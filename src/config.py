import logging
import os
from datetime import datetime

from consts import WeekDay
from dotenv import load_dotenv

__logger = logging.getLogger(__name__)

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
# defines if the Prometheus client is enabled
PROMETHEUS_ENABLED = bool(os.environ.get("PROMETHEUS_ENABLED", False))
# Prometheus port for exposing the application's metrics
PROMETHEUS_PORT = int(os.environ.get("PROMETHEUS_PORT", "8000"))


#
# validation
#
__null_req_vars = []

if not TELEGRAM_TOKEN:
    __null_req_vars.append("TELEGRAM_TOKEN")
if not AUTHORIZED_GROUP_ID:
    __null_req_vars.append("AUTHORIZED_GROUP_ID")
else:
    AUTHORIZED_GROUP_ID = int(AUTHORIZED_GROUP_ID)

if __null_req_vars:
    __logger.error(
        "Required environment variables are not set: %s", __null_req_vars
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

if BOT_TIME_ZONE not in range(-12, 14 + 1):
    __logger.error("BOT_TIME_ZONE must be a valid timezone (-12, 14)")
    exit(1)

if PROMETHEUS_PORT not in range(1024, 65535 + 1):
    __logger.error("PROMETHEUS_PORT must be a valid port (1024-65535)")