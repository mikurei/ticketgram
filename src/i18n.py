import gettext

from config import BOT_LANGUAGE

__translation = gettext.translation("base", "src/locales", [BOT_LANGUAGE], fallback=True)

gt = __translation.gettext