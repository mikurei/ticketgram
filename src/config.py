import logging
import os
from datetime import datetime

from consts import WeekDay
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# load environment variables from .env file
load_dotenv()

#
# Required environment variables
#
# Get one from the @BotFather bot
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# Group in which the bot operates
AUTHORIZED_GROUP_ID = os.environ.get("AUTHORIZED_GROUP_ID")

#
# Optional environment variables
#
# bot language
BOT_LANGUAGE = os.environ.get("LANGUAGE", "ru")
# database connection URI
DB_URI = os.environ.get("DB_URI", "sqlite.db")
# maximum tickets per single user
USER_OPEN_TICKETS_MAX = int(os.environ.get("USER_OPEN_TICKETS_MAX", "3"))
# working time
BOT_TIME_ACTIVE = os.environ.get("BOT_TIME_ACTIVE", "09:00-17:00")
# timezone of the working time
BOT_TIME_ZONE = int(os.environ.get("BOT_TIME_ZONE", "+0"))
# working days
BOT_ACTIVE_DAYS = os.environ.get(
    "BOT_ACTIVE_DAYS",
    "monday tuesday wednesday thursday friday saturday sunday",
)

#
# validation
#
null_req_vars = []

if not TELEGRAM_TOKEN:
    null_req_vars.append("TELEGRAM_TOKEN")
if not AUTHORIZED_GROUP_ID:
    null_req_vars.append("AUTHORIZED_GROUP_ID")
else:
    AUTHORIZED_GROUP_ID = int(AUTHORIZED_GROUP_ID)

if null_req_vars:
    logger.error(
        "Required environment variables are not set: %s", null_req_vars
    )
    exit(1)

BOT_TIME_ACTIVE = [
    datetime.strptime(time, "%H:%M").time()
    for time in BOT_TIME_ACTIVE.split("-", 1)
]


BOT_ACTIVE_DAYS: WeekDay = [
    WeekDay._value2member_map_[day_str]
    for day_str in BOT_ACTIVE_DAYS.split(" ", 6)
]

assert BOT_TIME_ZONE in range(-12, 14)
