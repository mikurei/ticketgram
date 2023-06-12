from i18n import gt as _

ticket_response_message = _(
    "<b>ℹ️ Support response:</b>\n\n"
    "Hi, {client_name}!\n\n"
    "{staff_response}\n\n"
    "Kind regards,\n"
    "{staff_pseudonym}"
)

start_message = _(
    "Hi! I'm a bot that manages the support system."
    " If you need assistance with anything,"
    " feel free to contact us using the `/ticket` command!\n\n"
    "Local time is <code>{local_time} (UTC{time_zone})</code>\n"
    "Work time is <code>{work_start} - {work_end}</code>\n"
    "Work days are <code>{work_calendar}</code>"
)