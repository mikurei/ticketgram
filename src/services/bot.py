import logging
from typing import cast

from config import AUTHORIZED_GROUP_ID
from exc import InitializationError
from i18n import gt as _
from telegram import (
    Bot,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    Chat,
)
from telegram.error import BadRequest, Forbidden
from telegram.ext import Application

logger = logging.getLogger(__name__)


async def add_commands(application: Application):
    """Add commands to the bot"""
    bot = cast(Bot, application.bot)
    await bot.set_my_commands(
        commands=[
            ("start", _("Start command")),
            ("ticket", _("Create a new support ticket")),
        ],
        scope=BotCommandScopeAllPrivateChats(),
    )

    await bot.set_my_commands(
        commands=[
            ("open", _("List of open tickets")),
            ("pseudonym", _("Update your pseudonym")),
            ("ban", _("Ban the user")),
            ("unban", _("Unban the user")),
        ],
        scope=BotCommandScopeAllGroupChats(),
    )


async def check_prerequisites(application: Application):
    """Checks that bot can operate in the authorized chat"""
    bot = cast(Bot, application.bot)
    try:
        chat = cast(Chat, await bot.get_chat(AUTHORIZED_GROUP_ID))
    except BadRequest:
        logger.error(
            "Bot is not a member of the authorized group",
            AUTHORIZED_GROUP_ID,
        )

    try:
        await chat.get_member(bot.id)
    except BadRequest:
        logger.error(
            "Bot is not a member of the authorized group",
            AUTHORIZED_GROUP_ID,
        )
        raise InitializationError
    except Forbidden:
        logger.error("Bot is restricted from the authorized group")
        raise InitializationError

    if chat.type != Chat.SUPERGROUP:
        logging.error("Chat must be a supergroup")
        raise InitializationError
