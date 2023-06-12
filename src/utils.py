import logging
from datetime import datetime, timedelta
from typing import List, cast
from uuid import UUID

from config import AUTHORIZED_GROUP_ID
from consts import (
    LANGUAGE_CODE_TO_EMOJI,
    MAX_SUMMARY_LINE_LENGTH,
    TICKET_AGE_WARNING,
    TicketActions,
    TicketStatus,
    WeekDay,
)
from i18n import gt as _
from models import SupportTicket, User
from peewee import DoesNotExist
from telegram import Update

logger = logging.getLogger(__name__)


async def parse_command_target(update: Update, target: str) -> User:
    """Parse the target(ticket id, username or userid) and return the user"""
    message = update.message

    # check if target is a valid uuid
    try:
        ticket_id = UUID(target)
    except ValueError:
        ticket_id = None

    # check if target is an username
    if target.startswith("@"):
        username = target[1:]
    else:
        username = None

    # check if target is an userid
    try:
        user_id = int(target)
    except ValueError:
        user_id = None

    if ticket_id:
        try:
            ticket = SupportTicket.get_by_id(ticket_id)
            user = ticket.user
        except DoesNotExist:
            await message.reply_text(
                _("⚠️ Ticket with this id doesn't exist in the database")
            )
            return None
    elif username:
        try:
            user = User.get(User.username == username)
        except DoesNotExist:
            await message.reply_text(
                _("⚠️ User with this @username doesn't exist in the database")
            )
            return None
    elif user_id:
        try:
            user = User.get(User.id == user_id)
        except DoesNotExist:
            await message.reply_text(
                _("⚠️ User with this id doesn't exist in the database")
            )
            return None
    else:
        await message.reply_text(
            _("⚠️ Target must be a valid ticket id OR @username OR user id")
        )
        return None
    return user


def lang_code_to_emoji(lang_code: str | None) -> str:
    """Converts :obj:`str` containing language code to emoji"""
    if not lang_code:
        return "❓"
    return LANGUAGE_CODE_TO_EMOJI.get(lang_code, "🌐")


def validate_ticket_query(data: str) -> bool:
    ticket_id, *action = data.split("_", 1)

    if not action:
        return False

    try:
        ticket_id = UUID(ticket_id)
    except ValueError:
        logger.debug("Invalid ticket id: %s", ticket_id)
        return False

    if action[0] not in TicketActions.__members__.values():
        logger.debug("Invalid action: %s", action[0])
        return False
    
    return True


def humanize_td(td: timedelta) -> str:
    """
    Humanizes the timedelta, converting it into a readable, localized string
    """
    periods = [
        (_("month"), _("months"), 60 * 60 * 24 * 31),
        (_("day"), _("days"), 60 * 60 * 24),
        (_("hour"), _("hours"), 60 * 60),
        (_("minute"), _("minutes"), 60),
        (_("second"), _("seconds"), 1),
    ]

    seconds_bucket = int(td.total_seconds())

    if seconds_bucket >= 60 * 60 * 24 * 365:  # year
        return _("long time ago")

    if seconds_bucket < 1:
        return _("just now")

    chunks = []
    for label, label_plural, period_seconds in periods:
        if seconds_bucket >= period_seconds:
            value, seconds_bucket = divmod(seconds_bucket, period_seconds)
            str_format = label_plural if value > 1 else label
            chunks.append(f"{value} {str_format}")
        else:
            pass

    return " ".join(chunks)


def create_ticket_summary(tickets: List[SupportTicket]) -> str:
    status_dict = {TicketStatus.OPEN: "📄", TicketStatus.CLOSED: "✅"}

    now = datetime.utcnow()

    ticket_lines = []
    for ticket in tickets:
        status = status_dict.get(ticket.status, "❓")

        first_name = ticket.user.first_name

        prepared_name = ticket.message.replace("\n", "").strip()
        name = (
            (prepared_name[:MAX_SUMMARY_LINE_LENGTH] + "…")
            if len(prepared_name) > MAX_SUMMARY_LINE_LENGTH
            else prepared_name
        )

        chat_id = str(AUTHORIZED_GROUP_ID).replace(
            "-100", ""
        )  # links doesn't work with the supergroup prefix

        link = "https://t.me/c/{chat_id}/{message_id}".format(
            chat_id=chat_id, message_id=ticket.support_message_id
        )

        age = cast(timedelta, now - ticket.created_at)
        age_str = humanize_td(age)

        age_warn = (
            "⚠️ "
            if (age.total_seconds() > TICKET_AGE_WARNING)
            & (ticket.status == TicketStatus.OPEN)
            else ""
        )

        ticket_lines.append(
            f"  •  {status} <a href='{link}'>{first_name}: '{name}'</a>"
            f" — <i>{age_warn}{age_str}</i>\n\n"
        )

    if not ticket_lines:
        return _("<i>Nothing to show</i>")

    return "".join(ticket_lines)


def week_day_localized(day: WeekDay) -> str:
    week_day_map = {
        WeekDay.MONDAY: _("monday"),
        WeekDay.TUESDAY: _("tuesday"),
        WeekDay.WEDNESDAY: _("wednesday"),
        WeekDay.THURSDAY: _("thursday"),
        WeekDay.FRIDAY: _("friday"),
        WeekDay.SATURDAY: _("saturday"),
        WeekDay.SUNDAY: _("sunday"),
    }
    return week_day_map[day]
