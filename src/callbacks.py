import html
import logging
import traceback
from datetime import datetime, timedelta

import services
from config import (
    AUTHORIZED_GROUP_ID,
    BOT_ACTIVE_DAYS,
    BOT_TIME_ACTIVE,
    BOT_TIME_ZONE,
    USER_OPEN_TICKETS_MAX,
)
from consts import (
    TICKETS_PER_PAGE,
    ConversationState,
    PaginationActions,
    TicketActions,
    TicketCreationActions,
    TicketStatus,
)
from i18n import gt as _
from models import Employee, SupportTicket, User
from peewee import DoesNotExist
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    ContextTypes,
    ConversationHandler,
)
from templates import start_message, ticket_response_message
from utils import (
    create_ticket_summary,
    lang_code_to_emoji,
    parse_command_target,
    week_day_localized,
)

logger = logging.getLogger(__name__)


async def error_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )

    bot_data_dump = html.escape(str(context.bot_data))
    chat_data_dump = html.escape(str(context.chat_data))
    user_data_dump = html.escape(str(context.user_data))
    tb_dump = html.escape("".join(tb_list))

    message = _(
        "⚠️ Unexpected Error has occurred:\n\n"
        "<pre>context.bot_data = {}</pre>\n"
        "<pre>context.chat_data = {}</pre>\n"
        "<pre>context.user_data = {}</pre>\n\n"
        "<pre>{}</pre>\n"
    ).format(bot_data_dump, chat_data_dump, user_data_dump, tb_dump)

    await context.bot.send_message(
        AUTHORIZED_GROUP_ID,
        message,
        parse_mode="HTML",
    )


async def post_init(application: Application) -> None:
    """Called after the initialization and before polling for updates"""
    await services.bot.check_prerequisites(application)

    services.db.init_db()

    await services.bot.add_commands(application)


async def leave_chat(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Leaves from the chat
    """
    logger.info("Chat is not authorized: '%s'", update.effective_chat.id)
    context.application.create_task(
        update.effective_chat.leave(), update=update
    )
    raise ApplicationHandlerStop


async def ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initializes the ticket creation conversation"""
    message = update.effective_message
    user = update.effective_user

    db_user = User.get(User.id == user.id)

    open_tickets = services.user.get_open_tickets(db_user)

    if len(open_tickets) >= USER_OPEN_TICKETS_MAX:
        await message.reply_text(
            _(
                f"You have <code>{len(open_tickets)}</code> open tickets."
                " Please, wait until they are resolved."
            ),
            parse_mode="HTML",
        )
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton(
                _("Cancel ❌"), callback_data=TicketCreationActions.CANCEL
            )
        ]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    status_message = await message.reply_text(
        _("Send your question and we'll do our best to assist you! 😉"),
        reply_markup=markup,
    )
    context.user_data["process_ticket_message_id"] = status_message.id

    return ConversationState.WAITING_FOR_MESSAGE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stops the conversation"""
    await update.effective_message.edit_text(
        _("<i>❌ Ticket has been cancelled by user.</i>"), parse_mode="HTML"
    )
    return ConversationHandler.END


async def process_user_ticket(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Creates a new ticket and forwards the user's message to the support group"""
    bot = context.bot
    user = update.effective_user
    message = update.effective_message
    chat = update.effective_chat
    ticket = SupportTicket(
        user_id=user.id, message=message.text, private_message_id=message.id
    )

    buttons = [
        [
            InlineKeyboardButton(
                _("SPAM 🗑️"), callback_data=f"{ticket.id}_{TicketActions.SPAM}"
            ),
            InlineKeyboardButton(
                _("CLOSE ✅"),
                callback_data=f"{ticket.id}_{TicketActions.CLOSE}",
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(buttons)

    group_message = await bot.send_message(
        AUTHORIZED_GROUP_ID,
        (
            f"<a href='tg://user?id={user.id}'>{user.first_name}</a> | "
            f"{lang_code_to_emoji(user.language_code)} | "
            f"<code>{ticket.id}</code>\n\n{message.text}"
        ),
        parse_mode="HTML",
        reply_markup=reply_markup,
    )
    # remove 'cancel' button
    await bot.edit_message_reply_markup(
        chat.id,
        context.user_data["process_ticket_message_id"],
        reply_markup=None,
    )

    await message.reply_text(_("✅ Ticket has been successfully created"))

    ticket.support_message_id = group_message.id
    ticket.save(force_insert=True)

    return ConversationHandler.END


async def ticket_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forwards the staff reply to the client"""
    message = update.effective_message
    user = update.effective_user
    reply_message = message.reply_to_message
    reply_user = reply_message.from_user
    bot = context.bot
    # check if reply mentions the bot
    if reply_user.id != context.bot.id:
        return

    try:
        ticket = SupportTicket.get(
            SupportTicket.support_message_id == reply_message.id
        )
    except DoesNotExist:
        logger.debug(
            "Reply message with id '%s' is not associated with a support ticket",
            reply_message.id,
        )
        return

    if ticket.status == TicketStatus.CLOSED:
        logger.debug(
            "SupportTicket with id '%s' is closed",
            SupportTicket.id
        )
        return

    db_user = User.get(User.id == user.id)

    try:
        pseudonym = Employee.get(Employee.user_id == user.id).pseudonym
    except DoesNotExist:
        logger.debug("Fallback pseudonym to default value")
        pseudonym = _("Support Staff")
    # send response
    await bot.send_message(
        ticket.user.id,
        ticket_response_message.format(
            client_name=ticket.user.first_name,
            staff_response=message.text_html,
            staff_pseudonym=pseudonym,
        ),  # TODO
        parse_mode="HTML",
        reply_to_message_id=ticket.private_message_id,
    )
    # mark as resolved
    services.ticket.close_ticket(ticket, db_user)
    await bot.edit_message_reply_markup(
        AUTHORIZED_GROUP_ID, ticket.support_message_id, reply_markup=None
    )


async def ticket_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    query_user = query.from_user
    message = update.effective_message
    bot = context.bot

    if update.effective_chat.id != AUTHORIZED_GROUP_ID:
        logger.info("Callback query tampering attempt by %s", query_user)
        return

    raw_ticket_id, action = query.data.split("_", 1)

    try:
        ticket = SupportTicket.get_by_id(raw_ticket_id)
    except DoesNotExist:
        return

    edit_header = (
        f"{message.text_html}\n\n"
        f"<a href='tg://user?id={query_user.id}'>{query_user.first_name}</a> "
    )

    if action == TicketActions.SPAM:
        reason = _("Spam")

        services.user.ban(ticket.user, reason)

        edit_body = _(
            "🛑 <b>has issued a ban</b>, <i>reason: {reason}</i>"
        ).format(reason=reason)
        # notify the user about action
        await bot.send_message(
            ticket.user.id,
            _("<b>System</b> {body}").format(body=edit_body),
            parse_mode="HTML",
        )
        # get all open tickets created by user
        deleted_count = 0
        for ticket in SupportTicket.select().where(
            (
                (SupportTicket.user_id == ticket.user_id)
                & (SupportTicket.status == TicketStatus.OPEN)
            )
        ):
            ticket.delete_instance()
            await bot.delete_message(
                chat_id=AUTHORIZED_GROUP_ID,
                message_id=ticket.support_message_id,
            )
            deleted_count += 1

        # notify the staff about the action
        await bot.send_message(
            chat_id=AUTHORIZED_GROUP_ID,
            text=_(
                "{header}{body}\n\n<i>Deleted {count} open tickets</i>"
            ).format(header=edit_header, body=edit_body, count=deleted_count),
            parse_mode="HTML",
            reply_markup=None,
        )
    elif action == TicketActions.CLOSE:
        services.ticket.close_ticket(ticket, query_user)

        await message.edit_text(
            _("{header}✅ <b>marked this ticket as resolved</b>").format(
                header=edit_header
            ),
            parse_mode="HTML",
            reply_markup=None,
        )
    else:
        return

    await query.answer()


async def preprocess_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Called before every update"""
    user = update.effective_user

    if user.is_bot:
        return

    try:
        db_user = User.get(User.id == user.id)

        if services.user.is_banned(db_user):
            raise ApplicationHandlerStop
    except DoesNotExist:
        db_user = User.create(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            language_code=user.language_code,
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows welcome message"""
    work_time = [time.strftime("%H:%M") for time in BOT_TIME_ACTIVE]
    work_days = [week_day_localized(day) for day in BOT_ACTIVE_DAYS]
    work_days_str = ", ".join(work_days)
    local_time = (datetime.utcnow() + timedelta(hours=BOT_TIME_ZONE)).strftime(
        "%H:%M"
    )
    tz_sign = "+" if BOT_TIME_ZONE >= 0 else "-"

    await update.message.reply_text(
        start_message.format(
            local_time=local_time,
            time_zone=tz_sign + str(BOT_TIME_ZONE),
            work_start=work_time[0],
            work_end=work_time[1],
            work_calendar=work_days_str,
        ),
        parse_mode="HTML",
    )


async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Blocks the user in the system"""
    message = update.effective_message

    async def usage(message: Message):
        await message.reply_text(
            _(
                "ℹ️ Usage: {} <ticket_id OR username OR user_id> <reason>"
            ).format(command)
        )

    command, *args = message.text.split(" ", 1)
    if not args:
        return context.application.create_task(usage(message))

    target, *reason = args[0].split(" ", 1)
    if not reason:
        return context.application.create_task(usage(message))

    user = await parse_command_target(update, target)

    if not user:
        return

    if services.user.is_banned(user):
        await message.reply_text(_("⚠️ User is already banned"))
    else:
        services.user.ban(user, reason=reason[0])
        await message.reply_text(_("✅ User has been banned"))


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unblocks the user in the system"""
    message = update.effective_message

    async def usage(message: Message):
        await message.reply_text(
            _("ℹ️ Usage: {} <ticket_id OR username OR user_id>").format(
                command
            )
        )

    command, *target = message.text.split(" ", 1)
    if not target:
        return context.application.create_task(usage(message))

    user = await parse_command_target(update, target[0])

    if not user:
        return

    if services.user.unban(user):
        await message.reply_text(_("✅ User has been unbanned"))
    else:
        await message.reply_text(_("⚠️ User is not banned"))


async def set_staff_pseudonym(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Set pseudonym of the staff member"""
    message = update.effective_message
    user = update.effective_user

    async def usage(message: Message):
        await message.reply_text(_("ℹ️ Usage: {} <pseudonym>").format(command))

    command, *pseudonym = message.text.split(" ", 1)
    if not pseudonym:
        return context.application.create_task(usage(message))

    user_db = User.get_by_id(user.id)
    employee, __ = Employee.get_or_create(user=user_db)

    services.employee.set_pseudonym(employee, pseudonym[0])

    await message.reply_text(
        _("✅ Pseudonym has been set to '{}'").format(pseudonym[0])
    )


async def open_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists open tickets for the staff member"""
    query_prefix = "OPEN_TICKETS_"

    message = update.effective_message
    query = update.callback_query

    page = context.user_data.get("open_tickets_page", 0)

    if query:
        if update.effective_chat.id != AUTHORIZED_GROUP_ID:
            logger.info(
                "Callback query tampering attempt by %s", update.effective_user
            )
            return

        command = query.data.replace(query_prefix, "")
        if command == PaginationActions.PREVIOUS:
            page -= 1
        elif command == PaginationActions.REFRESH:
            pass
        elif command == PaginationActions.NEXT:
            page += 1
        else:
            return
        await query.answer()

    tickets_count = (
        SupportTicket.select()
        .where(SupportTicket.status == TicketStatus.OPEN)
        .count()
    )

    pages_count, remainder = divmod(tickets_count, TICKETS_PER_PAGE)
    if remainder:
        pages_count += 1

    # bounds check
    if page >= pages_count:
        page = 0
    elif page < 0:
        page = pages_count - 1

    limit = TICKETS_PER_PAGE
    offset = TICKETS_PER_PAGE * page

    open_tickets = (
        SupportTicket.select()
        .where(SupportTicket.status == TicketStatus.OPEN)
        .order_by(SupportTicket.created_at)
        .offset(offset)
        .limit(limit)
    )
    if not open_tickets:
        summary = _("🥳 Hooray, all tickets are resolved!")
    else:
        summary = create_ticket_summary(open_tickets)

    keyboard = [
        [
            InlineKeyboardButton(
                "⏮️", callback_data=(query_prefix + PaginationActions.PREVIOUS)
            ),
            InlineKeyboardButton(
                "🔄", callback_data=(query_prefix + PaginationActions.REFRESH)
            ),
            InlineKeyboardButton(
                "⏭️", callback_data=(query_prefix + PaginationActions.NEXT)
            ),
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    pages_str = (
        _("<b>(page {}/{})</b>").format(page + 1, pages_count)
        if pages_count
        else ""
    )

    msg_text = _("📂 Open tickets {}\n{}").format(pages_str, summary)

    if query:
        try:
            await message.edit_text(
                msg_text, parse_mode="HTML", reply_markup=markup
            )
        except BadRequest as e:
            if "Message is not modified: " in str(
                e
            ):  # no error type for that, yuck
                pass
            else:
                raise

    else:
        await message.reply_text(
            msg_text,
            parse_mode="HTML",
            reply_markup=markup,
        )

    context.user_data["open_tickets_page"] = page
