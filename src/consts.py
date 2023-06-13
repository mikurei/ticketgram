from enum import IntEnum, StrEnum

APPLICATION_NAME = "ticketgram"

MAX_SUMMARY_LINE_LENGTH = 48

TICKET_AGE_WARNING = 60 * 60 * 24  # day

TICKETS_PER_PAGE = 10

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | "
    "%(name)s::%(funcName)s (line %(lineno)s) | %(message)s"
)

LANGUAGE_CODE_TO_EMOJI = {
    "en": "🇺🇸",
    "ru": "🇷🇺",
    "ua": "🇺🇦",
    "de": "🇩🇪",
    "fr": "🇫🇷",
    "es": "🇪🇸",
    "it": "🇮🇹",
    "pl": "🇵🇱",
    "nl": "🇳🇱",
    "tr": "🇹🇷",
    "pt": "🇵🇹",
    "sv": "🇸🇪",
    "no": "🇳🇴",
    "da": "🇩🇰",
    "cs": "🇨🇿",
    "hu": "🇭🇺",
    "th": "🇹🇭",
    "id": "🇮🇩",
    "ro": "🇷🇴",
    "au": "🇦🇺",
    "vi": "🇻🇳",
    "el": "🇬🇷",
    "bg": "🇧🇬",
    "he": "🇮🇱",
    "ar": "🇦🇪",
    "hi": "🇮🇳",
    "ko": "🇰🇷",
    "mx": "🇲🇽",
    "cn": "🇨🇳",
    "jp": "🇯🇵",
    "hk": "🇭🇰",
    "cr": "🇨🇷",
    "tw": "🇹🇼",
    "my": "🇲🇾",
}


class WeekDay(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ConversationState(IntEnum):
    WAITING_FOR_MESSAGE = 0
    WAITING_FOR_ADDITIONAL_MESSAGE = 1


class TicketStatus(IntEnum):
    OPEN = 0
    CLOSED = 1


class TicketActions(StrEnum):
    SPAM = "MARK_AS_SPAM"
    CLOSE = "CLOSE_TICKET"


class PaginationActions(StrEnum):
    PREVIOUS = "PREV_PAGE"
    REFRESH = "UPD_PAGE"
    NEXT = "NEXT_PAGE"


class TicketCreationActions(StrEnum):
    CANCEL = "CANCEL"