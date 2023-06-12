import logging
from warnings import filterwarnings
from callbacks import (
    ban_user,
    cancel,
    error_handler,
    leave_chat,
    open_tickets,
    post_init,
    preprocess_update,
    process_user_ticket,
    set_staff_pseudonym,
    start,
    ticket,
    ticket_actions,
    ticket_response,
    unban_user,
)
from config import AUTHORIZED_GROUP_ID, TELEGRAM_TOKEN
from consts import LOG_FORMAT, ConversationState
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    TypeHandler,
    filters,
)
from telegram.warnings import PTBUserWarning
from utils import validate_ticket_query

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
# suppress the noisy httpx
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)
# suppress the PTB warning
filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )
    # runs checks before passing the update to other handlers
    application.add_handler(TypeHandler(Update, preprocess_update), -1)
    # leaves from unauthorized chats and channels
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS
            & ~filters.StatusUpdate.LEFT_CHAT_MEMBER
            & ~filters.Chat(chat_id=AUTHORIZED_GROUP_ID),
            leave_chat,
        )
    )
    # Client side of the bot
    application.add_handler(
        CommandHandler("start", start, filters.ChatType.PRIVATE)
    )
    client_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("ticket", ticket, filters.ChatType.PRIVATE)
        ],
        states={
            ConversationState.WAITING_FOR_MESSAGE: [
                MessageHandler(
                    filters.ChatType.PRIVATE & filters.TEXT,
                    process_user_ticket,
                )
            ]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^CANCEL$")],
    )
    application.add_handler(client_conversation)
    # Support side of the bot
    # handle the response to tickets
    application.add_handler(
        MessageHandler(
            filters.REPLY
            & filters.TEXT
            & filters.Chat(chat_id=AUTHORIZED_GROUP_ID),
            ticket_response,
        )
    )
    application.add_handler(
        CommandHandler(
            "ban", ban_user, filters.Chat(chat_id=AUTHORIZED_GROUP_ID)
        )
    )
    application.add_handler(
        CommandHandler(
            "unban", unban_user, filters.Chat(chat_id=AUTHORIZED_GROUP_ID)
        )
    )
    application.add_handler(
        CommandHandler(
            "pseudonym",
            set_staff_pseudonym,
            filters.Chat(chat_id=AUTHORIZED_GROUP_ID),
        )
    )
    application.add_handler(
        CommandHandler(
            "open", open_tickets, filters.Chat(chat_id=AUTHORIZED_GROUP_ID)
        )
    )
    # open tickets list's buttons
    application.add_handler(
        CallbackQueryHandler(open_tickets, pattern="^OPEN_TICKETS_")
    )
    # ticket's buttons
    application.add_handler(
        CallbackQueryHandler(ticket_actions, pattern=validate_ticket_query)
    )

    application.add_error_handler(error_handler)

    application.run_polling()
