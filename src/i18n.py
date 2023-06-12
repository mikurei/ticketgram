import gettext

from config import BOT_LANGUAGE

translation = gettext.translation("base", "src/locales", [BOT_LANGUAGE], fallback=True)

gt = translation.gettext