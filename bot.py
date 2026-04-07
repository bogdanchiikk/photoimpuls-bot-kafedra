# -*- coding: utf-8 -*-
"""
Telegram-    @photoimpulsbot       -                 .
                          ,          ,                                        .     .
"""

import os
import re
import logging
import asyncio

#           .env                  (                                    )
_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_script_dir, ".env")
try:
    from dotenv import load_dotenv
    load_dotenv(_env_path, encoding="latin-1")
except ImportError:
    pass

def _ensure_env():
    """Load env vars from .env if not set (handles encoding on server)."""
    if not os.path.isfile(_env_path):
        return
    for enc in ("utf-8", "latin-1", "cp1251"):
        try:
            with open(_env_path, "r", encoding=enc) as f:
                for line in f:
                    s = line.strip()
                    if "=" not in s or s.startswith("#"):
                        continue
                    key, _, val = s.partition("=")
                    key = key.strip()
                    val = val.strip().strip('"\'')
                    if not val or val.startswith("#"):
                        continue
                    if key == "SHEETS_WEBAPP_URL" and not os.getenv(key):
                        os.environ[key] = val
                    elif key == "ADMIN_IDS" and not os.getenv(key):
                        os.environ[key] = val
                    elif key in ("WELCOME_IMAGE", "IMAGE_SUBSCRIBE", "IMAGE_SPECIALTY", "IMAGE_PHOTO_CENTER", "PROGRAM_SCHEDULE_URL"):
                        os.environ[key] = val
        except Exception:
            continue
_ensure_env()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands, BotCommand
try:
    from telegram import BotCommandScopeChat, BotCommandScopeDefault
except ImportError:
    try:
        from telegram.helpers import BotCommandScopeChat, BotCommandScopeDefault
    except ImportError:
        # Fallback ??? ?????? ??????
        BotCommandScopeChat = None
        BotCommandScopeDefault = None
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatMemberStatus, ParseMode

import database
import sheets
try:
    from texts import TEXT_HELP, TEXT_ABOUT
except ImportError:
    TEXT_HELP = "\u2139\ufe0f <b>\u041f\u043e\u043c\u043e\u0449\u044c</b>\n\n\u2022 /start \u2014 \u043d\u0430\u0447\u0430\u0442\u044c\n\u2022 /check \u2014 \u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0443"
    TEXT_ABOUT = "\u2b50\ufe0f <b>\u041e \u0431\u043e\u0442\u0435</b>\n\n\u0424\u043e\u0442\u043e-\u0426\u0435\u043d\u0442\u0440 \u041a\u043e\u043d\u0444\u0435\u0440\u0435\u043d\u0446\u0438\u0438."

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

if sheets.SHEETS_WEBAPP_URL:
    logger.info("Google Sheets: URL set, table writes enabled")
else:
    logger.warning("Google Sheets: SHEETS_WEBAPP_URL not set, table writes disabled")

#             
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN must be set in .env file")
_channel_id = os.getenv("CHANNEL_ID", "")
CHANNEL_ID = int(_channel_id) if _channel_id.lstrip("-").isdigit() else _channel_id
CHANNEL_INVITE_LINK = os.getenv(
    "CHANNEL_INVITE_LINK",
    "https://t.me/+bgUJi9zfTKliY2Ey",
)
YANDEX_DAY1_LINK = os.getenv("YANDEX_DAY1_LINK", "https://disk.yandex.ru/DAY1")
YANDEX_DAY2_LINK = os.getenv("YANDEX_DAY2_LINK", "https://disk.yandex.ru/DAY2")
YANDEX_DAY3_LINK = os.getenv("YANDEX_DAY3_LINK", "https://disk.yandex.ru/DAY3")
# ?????? ??? ????????? (???????? ??????)
YANDEX_DAY1_UPLOAD_LINK = os.getenv("YANDEX_DAY1_UPLOAD_LINK", "").strip()
YANDEX_DAY2_UPLOAD_LINK = os.getenv("YANDEX_DAY2_UPLOAD_LINK", "").strip()
YANDEX_DAY3_UPLOAD_LINK = os.getenv("YANDEX_DAY3_UPLOAD_LINK", "").strip()
WELCOME_IMAGE = os.getenv("WELCOME_IMAGE", "").strip()
IMAGE_SUBSCRIBE = os.getenv("IMAGE_SUBSCRIBE", "").strip()
IMAGE_SPECIALTY = os.getenv("IMAGE_SPECIALTY", "").strip()
IMAGE_PHOTO_CENTER = os.getenv("IMAGE_PHOTO_CENTER", "").strip()
# ?????? ?? ?????????? ?? ????? (???? 8080)
PROGRAM_SCHEDULE_URL = os.getenv("PROGRAM_SCHEDULE_URL", "http://185.198.152.146:8080/").strip()
# ID                               (           /notify_day1, /notify_day2, /notify_day3)
_admin_ids = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = set(int(x.strip()) for x in _admin_ids.split(",") if x.strip().isdigit())

DAY_LABELS = {
    1: "\u0412\u0435\u0439\u043d\u043e\u0432\u0441\u043a\u0438\u0435 \u0447\u0442\u0435\u043d\u0438\u044f. 9 \u0444\u0435\u0432\u0440\u0430\u043b\u044f. \u0414\u0435\u043d\u044c 1",
    2: "\u0412\u0435\u0439\u043d\u043e\u0432\u0441\u043a\u0438\u0435 \u0447\u0442\u0435\u043d\u0438\u044f. 10 \u0444\u0435\u0432\u0440\u0430\u043b\u044f. \u0414\u0435\u043d\u044c 2",
    3: "\u0412\u0435\u0439\u043d\u043e\u0432\u0441\u043a\u0438\u0435 \u0447\u0442\u0435\u043d\u0438\u044f. 11 \u0444\u0435\u0432\u0440\u0430\u043b\u044f. \u0414\u0435\u043d\u044c 3",
}
DAY_BUTTON_LABELS = {
    1: "\U0001f4c1 \u0412\u0435\u0439\u043d\u043e\u0432\u0441\u043a\u0438\u0435 \u0447\u0442\u0435\u043d\u0438\u044f. 9 \u0444\u0435\u0432. \u0414\u0435\u043d\u044c 1",
    2: "\U0001f4c1 \u0412\u0435\u0439\u043d\u043e\u0432\u0441\u043a\u0438\u0435 \u0447\u0442\u0435\u043d\u0438\u044f. 10 \u0444\u0435\u0432. \u0414\u0435\u043d\u044c 2",
    3: "\U0001f4c1 \u0412\u0435\u0439\u043d\u043e\u0432\u0441\u043a\u0438\u0435 \u0447\u0442\u0435\u043d\u0438\u044f. 11 \u0444\u0435\u0432. \u0414\u0435\u043d\u044c 3",
}
YANDEX_LINKS = {1: YANDEX_DAY1_LINK, 2: YANDEX_DAY2_LINK, 3: YANDEX_DAY3_LINK}
YANDEX_UPLOAD_LINKS = {1: YANDEX_DAY1_UPLOAD_LINK, 2: YANDEX_DAY2_UPLOAD_LINK, 3: YANDEX_DAY3_UPLOAD_LINK}

SPECIALTIES = {
    1: "\u041d\u0435\u0432\u0440\u043e\u043b\u043e\u0433",
    2: "\u041f\u0441\u0438\u0445\u0438\u0430\u0442\u0440",
    3: "\u0420\u0435\u0430\u0431\u0438\u043b\u0438\u0442\u043e\u043b\u043e\u0433",
    4: "\u041f\u0441\u0438\u0445\u043e\u0442\u0435\u0440\u0430\u043f\u0435\u0432\u0442",
    5: "\u0414\u0440\u0443\u0433\u043e\u0435",
}


# ----------                   ----------
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not CHANNEL_ID:
        logger.error("CHANNEL_ID         .")
        return False
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.OWNER,
        )
    except Exception as e:
        logger.exception("                            : %s", e)
        return False


# ----------            ----------
def get_specialty_keyboard():
    rows = []
    for spec_id, spec_name in sorted(SPECIALTIES.items()):
        rows.append([InlineKeyboardButton(str(spec_name), callback_data="spec_%d" % spec_id)])
    if PROGRAM_SCHEDULE_URL:
        rows.append([InlineKeyboardButton("\U0001f4c5 \u0420\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435", url=PROGRAM_SCHEDULE_URL)])
    return InlineKeyboardMarkup(rows)


def get_subscribe_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f4fa \u041f\u043e\u0434\u043f\u0438\u0441\u0430\u0442\u044c\u0441\u044f \u043d\u0430 \u043a\u0430\u043d\u0430\u043b", url=CHANNEL_INVITE_LINK)],
        [InlineKeyboardButton("\u2705 \u042f \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043b\u0441\u044f", callback_data="check_sub")],
    ])


def get_notify_days_string(user_id: int) -> str:
    """Get comma-separated string of selected days (e.g., '1,2,3')."""
    u = database.get_user(user_id)
    if not u:
        return ""
    selected = []
    if u.get("notify_day1"):
        selected.append("1")
    if u.get("notify_day2"):
        selected.append("2")
    if u.get("notify_day3"):
        selected.append("3")
    result = ",".join(selected) if selected else ""
    # Log for debugging
    logger.debug("get_notify_days_string: user_id=%s, result='%s', user_data=%s", user_id, result, u)
    return result


def get_days_keyboard(user_id=None):
    u = database.get_user(user_id) if user_id and user_id > 0 else None
    def label(d):
        base = DAY_BUTTON_LABELS[d]
        if u and u.get("notify_day%d" % d):
            return base + " \u2713"
        return base
    rows = [
        [InlineKeyboardButton(label(1), callback_data="day_1"), InlineKeyboardButton(label(2), callback_data="day_2")],
        [InlineKeyboardButton(label(3), callback_data="day_3")],
    ]
    return InlineKeyboardMarkup(rows)


def get_change_day_keyboard():
    rows = [[InlineKeyboardButton("\u2795 \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0435\u0449\u0451 \u0434\u0435\u043d\u044c", callback_data="change_day")]]
    return InlineKeyboardMarkup(rows)


def get_photos_keyboard():
    """Inline keyboard with direct links to all photo days."""
    rows = []
    if YANDEX_DAY1_LINK:
        rows.append([InlineKeyboardButton(DAY_BUTTON_LABELS[1], url=YANDEX_DAY1_LINK)])
    if YANDEX_DAY2_LINK:
        rows.append([InlineKeyboardButton(DAY_BUTTON_LABELS[2], url=YANDEX_DAY2_LINK)])
    if YANDEX_DAY3_LINK:
        rows.append([InlineKeyboardButton(DAY_BUTTON_LABELS[3], url=YANDEX_DAY3_LINK)])
    if PROGRAM_SCHEDULE_URL:
        rows.append([InlineKeyboardButton("\U0001f4c5 \u0420\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435", url=PROGRAM_SCHEDULE_URL)])
    return InlineKeyboardMarkup(rows) if rows else None


def get_day_notify_keyboard(day: int):
    link = YANDEX_LINKS.get(day, "#")
    t = "\U0001f4c1 \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0430\u043b\u044c\u0431\u043e\u043c \u0414\u043d\u044f " + str(day) + " \u043d\u0430 \u042f\u043d\u0434\u0435\u043a\u0441.\u0414\u0438\u0441\u043a"
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, url=link)]])


def get_multi_day_notify_keyboard(user_data: dict, ready_days: list[int]):
    """Keyboard with buttons for days user selected AND that are in ready_days."""
    rows = []
    for d in sorted(ready_days):
        if d not in (1, 2, 3):
            continue
        if not user_data.get("notify_day%d" % d):
            continue
        link = YANDEX_LINKS.get(d, "#")
        if not link or link == "#":
            continue
        label = "\U0001f4c1 " + DAY_BUTTON_LABELS[d]
        rows.append([InlineKeyboardButton(label, url=link)])
    if not rows:
        return None
    return InlineKeyboardMarkup(rows)


TEXT_WELCOME = (
    "\U0001f44b \u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c!\n\n"
    "\u2705 \u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0443\u043a\u0430\u0436\u0438\u0442\u0435 \u0432\u0430\u0448\u0443 \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u044c, \u0437\u0430\u0442\u0435\u043c \u043f\u043e\u0434\u043f\u0438\u0448\u0438\u0442\u0435\u0441\u044c \u043d\u0430 \u043a\u0430\u043d\u0430\u043b \u2014 \u0438 \u0432\u044b \u0441\u043c\u043e\u0436\u0435\u0442\u0435 \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0444\u043e\u0442\u043e \u0441 \u043c\u0435\u0440\u043e\u043f\u0440\u0438\u044f\u0442\u0438\u044f."
)
TEXT_NOW_SUBSCRIBE = (
    "\u041f\u043e\u0434\u043f\u0438\u0448\u0438\u0442\u0435\u0441\u044c \u043d\u0430 \u043a\u0430\u043d\u0430\u043b \u043a\u043e\u043d\u0444\u0435\u0440\u0435\u043d\u0446\u0438\u0438 \u043f\u043e \u0441\u0441\u044b\u043b\u043a\u0435 \u043d\u0438\u0436\u0435 \u0438 \u043d\u0430\u0436\u043c\u0438\u0442\u0435 \u00ab\u042f \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043b\u0441\u044f\u00bb."
)
TEXT_NOT_SUBSCRIBED = (
    "\u0412\u044b \u0435\u0449\u0451 \u043d\u0435 \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043d\u044b \u043d\u0430 \u043a\u0430\u043d\u0430\u043b.\n\n"
    "\u041f\u043e\u0434\u043f\u0438\u0448\u0438\u0442\u0435\u0441\u044c \u043f\u043e \u0441\u0441\u044b\u043b\u043a\u0435 \u0438 \u043d\u0430\u0436\u043c\u0438\u0442\u0435 \u00ab\u042f \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043b\u0441\u044f\u00bb."
)
TEXT_SUBSCRIBE = (
    "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u0435 \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0443 \u043d\u0430 \u043a\u0430\u043d\u0430\u043b \u0438 \u043d\u0430\u0436\u043c\u0438\u0442\u0435 \u00ab\u042f \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043b\u0441\u044f\u00bb."
)
TEXT_SUB_OK = "\u2705 \u041e\u0442\u043b\u0438\u0447\u043d\u043e! \u0421\u043f\u0430\u0441\u0438\u0431\u043e, \u0447\u0442\u043e \u0432\u044b \u0441 \u043d\u0430\u043c\u0438!"
TEXT_SPECIALTY_OTHER = "\u270f\ufe0f \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0432\u0430\u0448\u0443 \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u044c:"
TEXT_SPECIALTY = "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0432\u0430\u0448\u0443 \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u044c:"
TEXT_ALREADY_SPECIALTY = (
    "\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c \u0441\u043d\u043e\u0432\u0430!\n\n"
    "\u0412\u044b \u0443\u0436\u0435 \u0443\u043a\u0430\u0437\u044b\u0432\u0430\u043b\u0438 \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u044c: <b>{specialty_name}</b>."
)
TEXT_SUB_OK_AND_SPECIALTY = TEXT_SUB_OK + "\n\n" + TEXT_SPECIALTY
TEXT_PHOTO_CENTER = (
    "\U0001f4f8 <b>\u0424\u043e\u0442\u043e\u0433\u0440\u0430\u0444\u0438\u0438 \u043a\u043e\u043d\u0444\u0435\u0440\u0435\u043d\u0446\u0438\u0438</b>\n\n"
    "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043d\u0443\u0436\u043d\u044b\u0439 \u0434\u0435\u043d\u044c \u043d\u0438\u0436\u0435 \u2014 \u043c\u044b \u043e\u0442\u043a\u0440\u043e\u0435\u043c \u0430\u043b\u044c\u0431\u043e\u043c \u0441 \u0444\u043e\u0442\u043e\u0433\u0440\u0430\u0444\u0438\u044f\u043c\u0438 \u043d\u0430 \u042f\u043d\u0434\u0435\u043a\u0441.\u0414\u0438\u0441\u043a\u0435."
)
TEXT_DAY_CONFIRM = (
    "\u2705 \u0413\u043e\u0442\u043e\u0432\u043e!\n\n"
    "\u0412\u044b \u0431\u0443\u0434\u0435\u0442\u0435 \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u044c \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u044f \u0437\u0430: <b>{days_list}</b>\n\n"
    "\u041a\u043e\u0433\u0434\u0430 \u0430\u043b\u044c\u0431\u043e\u043c\u044b \u0431\u0443\u0434\u0443\u0442 \u0433\u043e\u0442\u043e\u0432\u044b \u2014 \u043c\u044b \u0432\u0430\u043c \u043d\u0430\u043f\u0438\u0448\u0435\u043c!"
)
TEXT_NOTIFY_READY = (
    "\U0001f514 \u0424\u043e\u0442\u043e \u0433\u043e\u0442\u043e\u0432\u044b!\n\n"
    "\u0410\u043b\u044c\u0431\u043e\u043c\u044b <b>{day_label}</b> \u0433\u043e\u0442\u043e\u0432\u044b \u2014 \u0437\u0430\u0431\u0438\u0440\u0430\u0439\u0442\u0435 \u043f\u043e \u0441\u0441\u044b\u043b\u043a\u0435 \u043d\u0438\u0436\u0435! \U0001f4c1"
)
TEXT_NOTIFY_READY_MULTI = (
    "\U0001f514 \u0424\u043e\u0442\u043e \u0433\u043e\u0442\u043e\u0432\u044b!\n\n"
    "\U0001f4c1 \u0417\u0430\u0431\u0438\u0440\u0430\u0439\u0442\u0435 \u0430\u043b\u044c\u0431\u043e\u043c\u044b \u043f\u043e \u0441\u0441\u044b\u043b\u043a\u0430\u043c:"
)
TEXT_ERROR = "\u26a0\ufe0f \u041f\u0440\u043e\u0438\u0437\u043e\u0448\u043b\u0430 \u043e\u0448\u0438\u0431\u043a\u0430. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u043f\u043e\u0437\u0436\u0435 \u0438\u043b\u0438 \u043e\u0431\u0440\u0430\u0442\u0438\u0442\u0435\u0441\u044c \u043a \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0443."
TEXT_MENU = (
    "\U0001f3e0 <b>\u041c\u0435\u043d\u044e</b>\n\n"
    "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u043d\u0438 \u043a\u043e\u043d\u0444\u0435\u0440\u0435\u043d\u0446\u0438\u0438 \u0438\u043b\u0438 \u043f\u043e\u0441\u043c\u043e\u0442\u0440\u0438\u0442\u0435 \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u0443."
)
TEXT_MY_DAYS_EMPTY = (
    "\U0001f4c5 \u041c\u043e\u0438 \u0434\u043d\u0438\n\n"
    "\u0412\u044b \u043f\u043e\u043a\u0430 \u043d\u0435 \u0432\u044b\u0431\u0440\u0430\u043b\u0438 \u0434\u043d\u0438 \u043a\u043e\u043d\u0444\u0435\u0440\u0435\u043d\u0446\u0438\u0438.\n\n"
    "\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u00ab\u0412\u044b\u0431\u0440\u0430\u0442\u044c \u0434\u043d\u0438\u00bb \u2014 \u043c\u044b \u043f\u0440\u0438\u0448\u043b\u0451\u043c, \u043a\u043e\u0433\u0434\u0430 \u0430\u043b\u044c\u0431\u043e\u043c\u044b \u0431\u0443\u0434\u0443\u0442 \u0433\u043e\u0442\u043e\u0432\u044b."
)
TEXT_MY_DAYS = (
    "\U0001f4c5 \u041c\u043e\u0438 \u0434\u043d\u0438\n\n"
    "\u0412\u044b \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043d\u044b \u043d\u0430 \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u044f: <b>{days_list}</b>\n\n"
    "\u041a\u043e\u0433\u0434\u0430 \u0430\u043b\u044c\u0431\u043e\u043c\u044b \u0431\u0443\u0434\u0443\u0442 \u0433\u043e\u0442\u043e\u0432\u044b \u2014 \u043c\u044b \u0432\u0430\u043c \u043d\u0430\u043f\u0438\u0448\u0435\u043c!"
)
# TEXT_HELP from texts.py or fallback above (block below removed to avoid SyntaxError on server)
# TEXT_HELP = (
#     "\u2139\ufe0f <b>\u041f\u043e\u043c\u043e\u0449\u044c</b>\n\n"
#     "\u2022 <b>/start</b> \u2014 \u043d\u0430\u0447\u0430\u0442\u044c\n"
#     "\u2022 <b>/check</b> \u2014 \u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0443\n\n"
#     "\u0412 \u043a\u0430\u043d\u0430\u043b \u2014 \u0442\u043e\u043b\u044c\u043a\u043e \u0432\u0440\u0430\u0447\u0438. \u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u044c, \u043f\u043e\u0442\u043e\u043c \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0430, \u0437\u0430\u0442\u0435\u043c \u0432\u044b\u0431\u043e\u0440 \u0434\u043d\u0435\u0439. \u041a\u043e\u0433\u0434\u0430 \u0444\u043e\u0442\u043o \u0433\u043e\u0442\u043e\u0432\u044b \u2014 \u043f\u0440\u0438\u0448\u043b\u0451\u043c \u0441\u0441\u044b\u043b\u043a\u0443" + "!"
# )
# TEXT_HELP and TEXT_ABOUT from texts.py (or fallback at top)
TEXT_MENU_SUBSCRIBE = (
    "\u26a0\ufe0f \u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u043f\u043e\u0434\u043f\u0438\u0448\u0438\u0442\u0435\u0441\u044c \u043d\u0430 \u043a\u0430\u043d\u0430\u043b!"
)


def get_menu_keyboard():
    """Main menu inline keyboard - simple version."""
    rows = [
        [InlineKeyboardButton("\U0001f4f8 \u0424\u043e\u0442\u043e-\u0446\u0435\u043d\u0442\u0440", callback_data="photo_center")],
    ]
    if PROGRAM_SCHEDULE_URL:
        rows.append([InlineKeyboardButton("\U0001f4c5 \u0420\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435", url=PROGRAM_SCHEDULE_URL)])
    return InlineKeyboardMarkup(rows)


def get_back_to_menu_keyboard():
    """Back to menu button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2b05 \u0412 \u043c\u0435\u043d\u044e", callback_data="back_to_menu")],
    ])


def escape_html(s: str) -> str:
    """Escape for Telegram HTML."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ----------                                  (           ) ----------
def _resolve_image_path(path: str) -> str:
    """Resolve relative path to script dir; URLs unchanged."""
    if not path or path.startswith(("http://", "https://")):
        return path
    if not os.path.isabs(path):
        path = os.path.join(_script_dir, path)
    return path


def _get_photo_arg(image: str):
    """Return (photo_arg, ok). photo_arg for send_photo, ok=True if valid."""
    if not image:
        return None, False
    
    # URLs are always OK
    is_url = image.startswith(("http://", "https://"))
    if is_url:
        return image, True
    
    # Resolve file path
    path = _resolve_image_path(image)
    
    # Check if file exists
    if os.path.isfile(path):
        logger.debug("Image found: %s -> %s", image, path)
        return path, True
    
    # File not found - log detailed info
    logger.warning("Image not found: %s (resolved: %s)", image, path)
    
    # Try to list images directory to help debug
    images_dir = os.path.join(_script_dir, "images")
    if os.path.isdir(images_dir):
        try:
            files = os.listdir(images_dir)
            logger.info("Available files in images/: %s", ", ".join(files[:10]))  # Show first 10 files
        except Exception as e:
            logger.debug("Could not list images directory: %s", e)
    
    return None, False


async def _send_photo(chat_id: int, image: str, context: ContextTypes.DEFAULT_TYPE, caption: str = None, reply_markup=None) -> bool:
    """Send photo by URL or file path. Optional caption and keyboard."""
    if not chat_id or not image:
        return False
    photo_arg, ok = _get_photo_arg(image)
    if not ok:
        return False
    try:
        kwargs = {"chat_id": chat_id, "photo": photo_arg}
        if caption:
            kwargs["caption"] = caption
            kwargs["parse_mode"] = ParseMode.HTML
        if reply_markup:
            kwargs["reply_markup"] = reply_markup
        await context.bot.send_photo(**kwargs)
        return True
    except Exception as e:
        logger.warning("send_photo failed: %s", e)
        return False


# ----------             ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.effective_user
        if not user:
            logger.warning("start(): No user in update")
            return
        user_id = user.id
        database.init_db()
        database.ensure_user(user_id, user.username)
        logger.info("User %s (%s) called /start", user_id, user.username)

        # Send response to user FIRST (before slow Google Sheets operations)
        chat_id = update.effective_chat.id if update.effective_chat else None
        logger.info("start(): chat_id=%s, WELCOME_IMAGE=%s", chat_id, bool(WELCOME_IMAGE))

        u = database.get_user(user_id)
        has_specialty = u and (u.get("specialty_id") or (u.get("specialty_name") or "").strip())

        message_sent = False
        try:
            if has_specialty:
                # ??? ??????? ????????????? ? ?? ?????????? ????? ?????
                spec_name = (u.get("specialty_name") or "").strip() or "\u2014"
                text = TEXT_ALREADY_SPECIALTY.format(specialty_name=spec_name)
                if await check_subscription(user_id, context):
                    database.set_subscribed(user_id, True)
                    kb = get_photos_keyboard()
                    if not kb:
                        kb = get_menu_keyboard()
                    # ?????  ??????? ????  (IMAGE_PHOTO_CENTER), ??? ? ????-??????
                    if chat_id and IMAGE_PHOTO_CENTER and _get_photo_arg(IMAGE_PHOTO_CENTER)[1]:
                        sent = await _send_photo(chat_id, IMAGE_PHOTO_CENTER, context, text, kb)
                        if sent:
                            message_sent = True
                    if not message_sent and chat_id:
                        await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
                        message_sent = True
                else:
                    text += "\n\n" + TEXT_NOW_SUBSCRIBE
                    kb = get_subscribe_keyboard()
                    if chat_id:
                        await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
                        message_sent = True
            else:
                # ?????? ??? ? ?????????? ??????????? ? ????? ?????????????
                if WELCOME_IMAGE and chat_id:
                    logger.info("start(): Attempting to send photo")
                    photo_arg, ok = _get_photo_arg(WELCOME_IMAGE)
                    if ok:
                        sent = await _send_photo(chat_id, WELCOME_IMAGE, context, TEXT_WELCOME, get_specialty_keyboard())
                        if sent:
                            message_sent = True
                            logger.info("start(): Photo sent successfully")
                        else:
                            logger.warning("start(): Photo send failed, will try text message")
                    else:
                        logger.warning("start(): Photo file not found, will send text message")
                if not message_sent:
                    logger.info("start(): Sending text message")
                    await update.message.reply_text(TEXT_WELCOME, reply_markup=get_specialty_keyboard(), parse_mode=ParseMode.HTML)
                    message_sent = True
                    logger.info("start(): Text message sent successfully")
        except Exception as send_err:
            logger.exception("start(): Error sending message: %s", send_err)
            if not message_sent and chat_id:
                try:
                    if has_specialty:
                        text_fb = TEXT_ALREADY_SPECIALTY.format(specialty_name=(u.get("specialty_name") or "").strip() or "\u2014")
                        kb_fb = get_photos_keyboard() or get_menu_keyboard()
                    else:
                        text_fb = TEXT_WELCOME
                        kb_fb = get_specialty_keyboard()
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=text_fb,
                        reply_markup=kb_fb,
                        parse_mode=ParseMode.HTML,
                    )
                    message_sent = True
                except Exception as alt_err:
                    logger.exception("start(): Alternative send also failed: %s", alt_err)
        
        # ?????????? ?????? ?????? ??? ????? ????: ?????? ????? ???, ????????? ? ?????? start/check
        if update.effective_chat and chat_id:
            try:
                chat_type = update.effective_chat.type
                logger.info("start(): chat_type=%s, user_id=%s, is_admin=%s", chat_type, user_id, is_admin(user_id))
                if chat_type == "private":
                    await _set_commands_for_chat(context, chat_id, user_id)
                    logger.info("start(): Commands set for chat %s", chat_id)
            except Exception as cmd_err:
                logger.warning("start(): Failed to set commands: %s", cmd_err)

        # Write to Google Sheets AFTER sending response (non-blocking)
        try:
            ok_status = sheets.append_status(user_id, "\u0437\u0430\u0448\u0451\u043b")
            ok_subs = sheets.append_subscription(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                notify_days=get_notify_days_string(user_id),
            )
            if not ok_status or not ok_subs:
                logger.warning("Sheets write failed for user_id=%s (status=%s subs=%s)", user_id, ok_status, ok_subs)
        except Exception as e:
            logger.exception("Error writing to Sheets in start(): %s", e)
    except Exception as e:
        logger.exception("start(): Unexpected error: %s", e)


async def button_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    if not user:
        await query.edit_message_text(TEXT_ERROR, parse_mode=ParseMode.HTML)
        return
    user_id = user.id
    database.ensure_user(user_id, user.username)

    chat_id = query.message.chat_id if query.message else None
    if not await check_subscription(user_id, context):
        kb_sub = get_subscribe_keyboard()
        if IMAGE_SUBSCRIBE and chat_id and _get_photo_arg(IMAGE_SUBSCRIBE)[1]:
            try:
                await query.delete_message()
            except Exception:
                pass
            await _send_photo(chat_id, IMAGE_SUBSCRIBE, context, TEXT_NOT_SUBSCRIBED, kb_sub)
        else:
            try:
                await query.edit_message_text(
                    TEXT_NOT_SUBSCRIBED,
                    reply_markup=kb_sub,
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                if chat_id:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=TEXT_NOT_SUBSCRIBED,
                        reply_markup=kb_sub,
                        parse_mode=ParseMode.HTML,
                    )
        return

    database.set_subscribed(user_id, True)
    
    # After subscribe: show simple message with links to all photo days
    text = TEXT_PHOTO_CENTER
    kb_photos = get_photos_keyboard()
    if IMAGE_PHOTO_CENTER and chat_id and _get_photo_arg(IMAGE_PHOTO_CENTER)[1]:
        try:
            await query.delete_message()
        except Exception:
            pass
        await _send_photo(chat_id, IMAGE_PHOTO_CENTER, context, text, kb_photos)
    else:
        try:
            await query.edit_message_text(
                text,
                reply_markup=kb_photos,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.exception("button_check edit failed: %s", e)
            await context.bot.send_message(
                chat_id=chat_id or update.effective_chat.id,
                text=text,
                reply_markup=kb_photos,
                parse_mode=ParseMode.HTML,
            )
    
    # Write to Google Sheets AFTER sending response (non-blocking)
    try:
        sheets.append_status(user_id, "\u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043b\u0441\u044f")
        sheets.append_subscription(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            notify_days=get_notify_days_string(user_id),
        )
    except Exception as e:
        logger.exception("Error writing to Sheets in button_check(): %s", e)


async def specialty_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    if not data or not data.startswith("spec_"):
        return
    try:
        spec_id = int(data.split("_")[1])
    except (IndexError, ValueError):
        return
    if spec_id not in SPECIALTIES:
        return
    user = query.from_user
    if not user:
        return
    user_id = user.id
    database.ensure_user(user_id, user.username)
    chat_id = query.message.chat_id if query.message else None

    # If "??????" (spec_id == 5), ask user to type their specialty
    if spec_id == 5:
        try:
            await query.edit_message_text(
                TEXT_SPECIALTY_OTHER,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.exception("specialty_selected edit failed: %s", e)
            if chat_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=TEXT_SPECIALTY_OTHER,
                    parse_mode=ParseMode.HTML,
                )
        # Store that user is waiting for specialty input
        context.user_data["waiting_specialty"] = True
        return

    # Regular specialty selected ? ????????? ? ?????????? ????????
    spec_name = SPECIALTIES[spec_id]
    database.set_specialty(user_id, spec_id, spec_name)

    kb = get_subscribe_keyboard()
    if IMAGE_SUBSCRIBE and chat_id and _get_photo_arg(IMAGE_SUBSCRIBE)[1]:
        try:
            await query.delete_message()
        except Exception:
            pass
        await _send_photo(chat_id, IMAGE_SUBSCRIBE, context, TEXT_NOW_SUBSCRIBE, kb)
    else:
        try:
            if query.message.photo:
                await query.edit_message_caption(caption=TEXT_NOW_SUBSCRIBE, reply_markup=kb, parse_mode=ParseMode.HTML)
            else:
                await query.edit_message_text(TEXT_NOW_SUBSCRIBE, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.exception("specialty_selected edit failed: %s", e)
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text=TEXT_NOW_SUBSCRIBE, reply_markup=kb, parse_mode=ParseMode.HTML)
    
    # Write to Google Sheets AFTER sending response (non-blocking)
    try:
        sheets.append_status(user_id, "\u0441\u043a\u0430\u0437\u0430\u043b \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u044c", spec_name)
        sheets.append_subscription(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            specialty_id=str(spec_id),
            specialty_name=spec_name,
            notify_days=get_notify_days_string(user_id),
        )
    except Exception as e:
        logger.exception("Error writing to Sheets in specialty_selected(): %s", e)


async def day_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data not in ("day_1", "day_2", "day_3"):
        return
    day = int(data.split("_")[1])
    user = query.from_user
    if not user:
        return
    user_id = user.id
    database.ensure_user(user_id, user.username)
    database.set_subscribed(user_id, True)
    database.set_notify_day(user_id, day, True)

    u = database.get_user(user_id)
    selected = []
    if u:
        if u.get("notify_day1"):
            selected.append(DAY_LABELS[1])
        if u.get("notify_day2"):
            selected.append(DAY_LABELS[2])
        if u.get("notify_day3"):
            selected.append(DAY_LABELS[3])
    days_list = ", ".join(selected) if selected else DAY_LABELS[day]
    days_list = escape_html(days_list)
    text = TEXT_DAY_CONFIRM.format(days_list=days_list)
    kb = get_change_day_keyboard()
    
    # Send response to user FIRST (before slow Google Sheets operations)
    chat_id = query.message.chat_id if query.message else None
    try:
        if query.message.photo:
            await query.edit_message_caption(caption=text, reply_markup=kb, parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception("day_selected edit failed: %s", e)
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=kb, parse_mode=ParseMode.HTML)
    
    # Write to Google Sheets AFTER sending response (non-blocking)
    try:
        sheets.append_status(user_id, "\u0432\u044b\u0431\u0440\u0430\u043b \u0434\u0435\u043d\u044c", DAY_LABELS[day])
        # Update subscription in Google Sheets with notify_days
        # Note: specialty_id and specialty_name may be empty if not selected yet
        notify_days_str = get_notify_days_string(user_id)
        sheets.append_subscription(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            specialty_id="",
            specialty_name="",
            notify_days=notify_days_str,
        )
    except Exception as e:
        logger.exception("Error writing to Sheets in day_selected(): %s", e)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages - check if user is entering custom specialty."""
    if not update.message or not update.message.text:
        return
    user = update.effective_user
    if not user:
        return
    user_id = user.id
    
    # Check if user is waiting for specialty input
    if context.user_data.get("waiting_specialty"):
        custom_specialty = update.message.text.strip()
        if not custom_specialty or len(custom_specialty) > 100:
            await update.message.reply_text(
                "\u26a0\ufe0f \u041f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, \u0432\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u0440\u043e\u0442\u043a\u0443\u044e \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u044c (\u0434\u043e 100 \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432).",
                parse_mode=ParseMode.HTML,
            )
            return
        
        database.ensure_user(user_id, user.username)
        database.set_specialty(user_id, 5, custom_specialty)

        # Clear waiting flag
        context.user_data.pop("waiting_specialty", None)

        # Now ask to subscribe (do not set subscribed yet)
        kb = get_subscribe_keyboard()
        chat_id = update.effective_chat.id if update.effective_chat else None
        if IMAGE_SUBSCRIBE and chat_id and _get_photo_arg(IMAGE_SUBSCRIBE)[1]:
            await _send_photo(chat_id, IMAGE_SUBSCRIBE, context, TEXT_NOW_SUBSCRIBE, kb)
        else:
            await update.message.reply_text(TEXT_NOW_SUBSCRIBE, reply_markup=kb, parse_mode=ParseMode.HTML)
        
        # Save custom specialty to Google Sheets AFTER sending response (non-blocking)
        try:
            spec_name = "\u270f\ufe0f \u0414\u0440\u0443\u0433\u043e\u0435: " + custom_specialty
            sheets.append_status(user_id, "\u0441\u043a\u0430\u0437\u0430\u043b \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u044c", spec_name)
            sheets.append_subscription(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                specialty_id="5",
                specialty_name=custom_specialty,
                notify_days=get_notify_days_string(user_id),
            )
        except Exception as e:
            logger.exception("Error writing to Sheets in handle_text_message(): %s", e)
        return


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """                                                    ."""
    user = update.effective_user
    if not user:
        return
    user_id = user.id
    database.ensure_user(user_id, user.username)
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not await check_subscription(user_id, context):
        if IMAGE_SUBSCRIBE and chat_id:
            await _send_photo(chat_id, IMAGE_SUBSCRIBE, context, TEXT_NOT_SUBSCRIBED, get_subscribe_keyboard())
        else:
            await update.message.reply_text(
                TEXT_NOT_SUBSCRIBED,
                reply_markup=get_subscribe_keyboard(),
                parse_mode=ParseMode.HTML,
            )
        return
    database.set_subscribed(user_id, True)
    
    # Subscribed ? show simple message with links to all photo days
    text = TEXT_PHOTO_CENTER
    kb_photos = get_photos_keyboard()
    if IMAGE_PHOTO_CENTER and chat_id and _get_photo_arg(IMAGE_PHOTO_CENTER)[1]:
        await _send_photo(chat_id, IMAGE_PHOTO_CENTER, context, text, kb_photos)
    else:
        await update.message.reply_text(
            text,
            reply_markup=kb_photos,
            parse_mode=ParseMode.HTML,
        )
    
    # Write to Google Sheets AFTER sending response (non-blocking)
    try:
        sheets.append_status(user_id, "\u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043b\u0441\u044f")
        sheets.append_subscription(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            notify_days=get_notify_days_string(user_id),
        )
    except Exception as e:
        logger.exception("Error writing to Sheets in check_command(): %s", e)


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """??????? ?????????? ????????? (????)."""
    if not PROGRAM_SCHEDULE_URL:
        await update.message.reply_text(
            "\u0420\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u0441\u0435\u0439\u0447\u0430\u0441 \u043d\u0435 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e.",
            parse_mode=ParseMode.HTML,
        )
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f4c5 \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0440\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435", url=PROGRAM_SCHEDULE_URL)],
    ])
    await update.message.reply_text(
        "\u0420\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u043a\u043e\u043d\u0433\u0440\u0435\u0441\u0441\u0430:\n" + PROGRAM_SCHEDULE_URL,
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle menu callback buttons: my_days, change_specialty, photo_center, program_info, help, about, back_to_menu."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    if not user:
        return
    user_id = user.id
    chat_id = query.message.chat_id if query.message else None
    database.ensure_user(user_id, user.username)

    if data == "back_to_menu":
        try:
            if query.message and query.message.photo:
                await query.delete_message()
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=TEXT_MENU,
                    reply_markup=get_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
            else:
                await query.edit_message_text(
                    TEXT_MENU,
                    reply_markup=get_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
        except Exception as e:
            logger.warning("menu_callback back_to_menu edit failed: %s", e)
            if chat_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=TEXT_MENU,
                    reply_markup=get_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
        return

    if data == "my_days":
        u = database.get_user(user_id)
        selected = []
        if u:
            if u.get("notify_day1"):
                selected.append(DAY_LABELS[1])
            if u.get("notify_day2"):
                selected.append(DAY_LABELS[2])
            if u.get("notify_day3"):
                selected.append(DAY_LABELS[3])
        if not selected:
            text = TEXT_MY_DAYS_EMPTY
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("\U0001f4c5 \u0412\u044b\u0431\u0440\u0430\u0442\u044c \u0434\u043d\u0438", callback_data="photo_center")],
                [InlineKeyboardButton("\u2b05 \u0412 \u043c\u0435\u043d\u044e", callback_data="back_to_menu")],
            ])
        else:
            days_list = escape_html(", ".join(selected))
            text = TEXT_MY_DAYS.format(days_list=days_list)
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2795 \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0438\u043b\u0438 \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0434\u043d\u0438", callback_data="photo_center")],
                [InlineKeyboardButton("\u2b05 \u0412 \u043c\u0435\u043d\u044e", callback_data="back_to_menu")],
            ])
        try:
            if query.message and query.message.photo:
                await query.delete_message()
                await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=kb, parse_mode=ParseMode.HTML)
            else:
                await query.edit_message_text(text=text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning("menu_callback my_days edit failed: %s", e)
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    if data == "change_specialty":
        kb = get_specialty_keyboard()
        back_row = [InlineKeyboardButton("\u2b05 \u0412 \u043c\u0435\u043d\u044e", callback_data="back_to_menu")]
        kb = InlineKeyboardMarkup(kb.inline_keyboard + [back_row])
        try:
            if query.message and query.message.photo:
                await query.delete_message()
                await context.bot.send_message(chat_id=chat_id, text=TEXT_SPECIALTY, reply_markup=kb, parse_mode=ParseMode.HTML)
            else:
                await query.edit_message_text(
                    TEXT_SPECIALTY,
                    reply_markup=kb,
                    parse_mode=ParseMode.HTML,
                )
        except Exception as e:
            logger.warning("menu_callback change_specialty edit failed: %s", e)
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text=TEXT_SPECIALTY, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    if data == "photo_center":
        text = TEXT_PHOTO_CENTER
        kb_photos = get_photos_keyboard()
        if IMAGE_PHOTO_CENTER and chat_id and _get_photo_arg(IMAGE_PHOTO_CENTER)[1]:
            try:
                await query.delete_message()
            except Exception:
                pass
            await _send_photo(chat_id, IMAGE_PHOTO_CENTER, context, text, kb_photos)
        else:
            try:
                if query.message.photo:
                    await query.edit_message_caption(caption=text, reply_markup=kb_photos, parse_mode=ParseMode.HTML)
                else:
                    await query.edit_message_text(text, reply_markup=kb_photos, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.warning("menu_callback photo_center edit failed: %s", e)
                if chat_id:
                    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=kb_photos, parse_mode=ParseMode.HTML)
        return

    if data == "help":
        kb = get_back_to_menu_keyboard()
        try:
            if query.message and query.message.photo:
                await query.delete_message()
                await context.bot.send_message(chat_id=chat_id, text=TEXT_HELP, reply_markup=kb, parse_mode=ParseMode.HTML)
            else:
                await query.edit_message_text(text=TEXT_HELP, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning("menu_callback help edit failed: %s", e)
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text=TEXT_HELP, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    if data == "about":
        kb = get_back_to_menu_keyboard()
        try:
            if query.message and query.message.photo:
                await query.delete_message()
                await context.bot.send_message(chat_id=chat_id, text=TEXT_ABOUT, reply_markup=kb, parse_mode=ParseMode.HTML)
            else:
                await query.edit_message_text(text=TEXT_ABOUT, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning("menu_callback about edit failed: %s", e)
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text=TEXT_ABOUT, reply_markup=kb, parse_mode=ParseMode.HTML)
        return


async def change_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id if query.message else None
    text = TEXT_PHOTO_CENTER
    kb_photos = get_photos_keyboard()
    if IMAGE_PHOTO_CENTER and chat_id and _get_photo_arg(IMAGE_PHOTO_CENTER)[1]:
        try:
            await query.delete_message()
        except Exception:
            pass
        await _send_photo(chat_id, IMAGE_PHOTO_CENTER, context, text, kb_photos)
    else:
        try:
            if query.message.photo:
                await query.edit_message_caption(caption=text, reply_markup=kb_photos, parse_mode=ParseMode.HTML)
            else:
                await query.edit_message_text(text, reply_markup=kb_photos, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.exception("change_day edit failed: %s", e)
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=kb_photos, parse_mode=ParseMode.HTML)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ?????? ?????? ??? ????: ??????? ???????????? ????? ?????? start/check, ?????? ? ???
COMMANDS_USER = [
    BotCommand("start", "\u041d\u0430\u0447\u0430\u0442\u044c \u0440\u0430\u0431\u043e\u0442\u0443 \u0441 \u0431\u043e\u0442\u043e\u043c"),
    BotCommand("check", "\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0443 \u043d\u0430 \u043a\u0430\u043d\u0430\u043b"),
    BotCommand("schedule", "\u0420\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u043a\u043e\u043d\u0433\u0440\u0435\u0441\u0441\u0430"),
]
COMMANDS_ADMIN = COMMANDS_USER + [
    BotCommand("notify_day1", "\u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435 \u043e \u0433\u043e\u0442\u043e\u0432\u043d\u043e\u0441\u0442\u0438 \u0444\u043e\u0442\u043e \u0414\u0435\u043d\u044c 1"),
    BotCommand("notify_day2", "\u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435 \u043e \u0433\u043e\u0442\u043e\u0432\u043d\u043e\u0441\u0442\u0438 \u0444\u043e\u0442\u043e \u0414\u0435\u043d\u044c 2"),
    BotCommand("notify_day3", "\u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435 \u043e \u0433\u043e\u0442\u043e\u0432\u043d\u043e\u0441\u0442\u0438 \u0444\u043e\u0442\u043e \u0414\u0435\u043d\u044c 3"),
    BotCommand("notify_ready", "\u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435 \u0434\u043b\u044f \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u0438\u0445 \u0434\u043d\u0435\u0439: /notify_ready 1 2 3"),
    BotCommand("broadcast_feb2026", "\u0420\u0430\u0441\u0441\u044b\u043b\u043a\u0430 \u0441\u0441\u044b\u043b\u043e\u043a \u043d\u0430 \u0444\u043e\u0442\u043e 9\u201310 \u0444\u0435\u0432\u0440\u0430\u043b\u044f 2026"),
]


async def _set_commands_for_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> None:
    """?????????? ?????? ?????? ??? ????: ?????? ????? ???, ????????? ? ?????? start/check."""
    if BotCommandScopeChat is None:
        logger.warning("BotCommandScopeChat not available, skipping command setup")
        return
    try:
        commands = COMMANDS_ADMIN if is_admin(user_id) else COMMANDS_USER
        await context.bot.set_my_commands(commands=commands, scope=BotCommandScopeChat(chat_id=chat_id))
        logger.info("Commands set successfully for chat %s (user %s, admin: %s)", chat_id, user_id, is_admin(user_id))
    except Exception as e:
        logger.warning("set_my_commands for chat %s failed: %s", chat_id, e)


async def notify_day(update: Update, context: ContextTypes.DEFAULT_TYPE, day: int) -> None:
    """                                                                           ."""
    user_id = update.effective_user.id if update.effective_user else 0
    if not is_admin(user_id):
        await update.message.reply_text("\u041a\u043e\u043c\u0430\u043d\u0434\u0430 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0430 \u0442\u043e\u043b\u044c\u043a\u043e \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0443.")
        return
    user_ids = database.get_users_for_day(day)
    day_label = escape_html(DAY_LABELS[day])
    text = TEXT_NOTIFY_READY.format(day_label=day_label)
    keyboard = get_day_notify_keyboard(day)
    sent = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
            sent += 1
        except Exception as e:
            logger.warning("                                              %s: %s", uid, e)
    await update.message.reply_text(
        f"\u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435 \u0437\u0430 \u0414\u0435\u043d\u044c {day} \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u043b\u0435\u043d\u043e: {sent} \u0438\u0437 {len(user_ids)}."
    )


async def notify_day1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await notify_day(update, context, 1)


async def notify_day2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await notify_day(update, context, 2)


async def notify_day3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await notify_day(update, context, 3)


async def notify_ready(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send one message per user with buttons for all their selected days that are ready."""
    try:
        msg = update.message
        if not msg:
            return
        user_id = update.effective_user.id if update.effective_user else 0
        if not is_admin(user_id):
            await msg.reply_text(
                "\u041a\u043e\u043c\u0430\u043d\u0434\u0430 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0430 \u0442\u043e\u043b\u044c\u043a\u043e \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0443."
            )
            return
        args = list(getattr(context, "args", None) or [])
        if not args and msg.text:
            raw = re.sub(r"/notify_ready(@\w+)?\s*", "", (msg.text or ""), count=1).strip()
            if raw:
                args = raw.replace(",", " ").split()
        ready_days = []
        for p in args:
            try:
                d = int(str(p).strip())
                if d in (1, 2, 3) and d not in ready_days:
                    ready_days.append(d)
            except (ValueError, TypeError):
                pass
        if not ready_days:
            await msg.reply_text(
                "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435: /notify_ready 1 2 3\n"
                "\u041f\u0440\u0438\u043c\u0435\u0440: /notify_ready 1 2 \u2014 \u0444\u043e\u0442\u043e \u0414\u043d\u044f 1 \u0438 2 \u0433\u043e\u0442\u043e\u0432\u044b."
            )
            return
        seen = set()
        user_ids = []
        for d in ready_days:
            for uid in database.get_users_for_day(d):
                if uid not in seen:
                    seen.add(uid)
                    user_ids.append(uid)
        text = TEXT_NOTIFY_READY_MULTI
        sent = 0
        for uid in user_ids:
            u = database.get_user(uid)
            if not u:
                continue
            keyboard = get_multi_day_notify_keyboard(u, ready_days)
            if not keyboard:
                continue
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
                sent += 1
            except Exception as e:
                logger.warning("notify_ready to %s: %s", uid, e)
        days_str = ", ".join(str(d) for d in sorted(ready_days))
        await msg.reply_text(
            "\u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435 \u0437\u0430 \u0414\u043d\u0438 "
            + days_str + " \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u043b\u0435\u043d\u043e: "
            + str(sent) + " \u0438\u0437 " + str(len(user_ids)) + "."
        )
    except Exception as e:
        logger.exception("notify_ready error: %s", e)
        if update.message:
            await update.message.reply_text("\u041e\u0448\u0438\u0431\u043a\u0430: " + str(e))


async def broadcast_feb2026(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast photos message."""
    msg = update.message
    if not msg or not update.effective_user:
        return

    admin_id = update.effective_user.id
    if not is_admin(admin_id):
        await msg.reply_text(
            "\u041a\u043e\u043c\u0430\u043d\u0434\u0430 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0430 \u0442\u043e\u043b\u044c\u043a\u043e \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0443."
        )
        return

    # ????? ?????????????: /broadcast_feb2026 test
    args = list(getattr(context, "args", None) or [])
    is_preview = any(str(a).lower() in ("test", "preview") for a in args)

    if is_preview:
        # ?????? ??????, ????? ??????????, ??? ???????? ?????????
        user_ids = [admin_id]
    else:
        # ???? ??????????? ?????????????
        user_ids = database.get_all_subscribed_users()

    # ????? ???????? (????? \u-??????????????????, ????? ?? ???????? ?????????)
    # ????? ???????? (????? \u-??????????????????, ????? ?? ???????? ?????????)
    text = (
        "\u041a\u043e\u043b\u043b\u0435\u0433\u0438, \u0434\u043e\u0431\u0440\u044b\u0439 \u0434\u0435\u043d\u044c!\n\n"
        "\u0424\u043e\u0442\u043e\u0433\u0440\u0430\u0444\u0438\u0438 \u0441 \u041a\u043e\u043d\u0433\u0440\u0435\u0441\u0441\u0430 <b>\u00ab\u0412\u0435\u0439\u043d\u043e\u0432\u0441\u043a\u0438\u0435 \u0447\u0442\u0435\u043d\u0438\u044f 2026\u00bb</b> \u0437\u0430 9\u201110 \u0444\u0435\u0432\u0440\u0430\u043b\u044f \u0443\u0436\u0435 \u0440\u0430\u0437\u043c\u0435\u0449\u0435\u043d\u044b \u043f\u043e \u0441\u0441\u044b\u043b\u043a\u0435 \u043d\u0438\u0436\u0435.\n\n"
        "\u0417\u0430\u0445\u043e\u0434\u0438\u0442\u0435 \u043f\u043e \u043a\u043d\u043e\u043f\u043a\u0435 \u043d\u0438\u0436\u0435, \u043d\u0430\u0445\u043e\u0434\u0438\u0442\u0435 \u0441\u0432\u043e\u0438 \u043b\u0443\u0447\u0448\u0438\u0435 \u0440\u0430\u043a\u0443\u0440\u0441\u044b \u0438 \u0441\u043a\u0430\u0447\u0438\u0432\u0430\u0439\u0442\u0435!\n\n"
        "\u0414\u043e \u0432\u0441\u0442\u0440\u0435\u0447\u0438 \u043d\u0430 \u0431\u0443\u0434\u0443\u0449\u0438\u0445 \u043a\u043e\u043d\u0433\u0440\u0435\u0441\u0441\u0430\u0445 \U0001F49B"
    )
    # ?????? ?? ??????? 9 ? 10 ??????? (?????? ??? ? ???????? ??????? ????)
    buttons = []
    if YANDEX_DAY1_LINK:
        buttons.append([InlineKeyboardButton(DAY_BUTTON_LABELS[1], url=YANDEX_DAY1_LINK)])
    if YANDEX_DAY2_LINK:
        buttons.append([InlineKeyboardButton(DAY_BUTTON_LABELS[2], url=YANDEX_DAY2_LINK)])
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    sent = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
            )
            sent += 1
        except Exception as e:
            logger.warning("broadcast_feb2026 to %s failed: %s", uid, e)

    if is_preview:
        await msg.reply_text(
            "\u0422\u0435\u0441\u0442\u043e\u0432\u043e\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e \u0442\u043e\u043b\u044c\u043a\u043e \u0430\u0434\u043c\u0438\u043d\u0443."
        )
    else:
        await msg.reply_text(
            "\u0420\u0430\u0441\u0441\u044b\u043b\u043a\u0430 \u0437\u0430 9\u201110 \u0444\u0435\u0432\u0440\u0430\u043b\u044f \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0430: "
            f"{sent} \u0438\u0437 {len(user_ids)} \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439."
        )

def main() -> None:
    if not CHANNEL_ID:
        print("        : CHANNEL_ID         .   . README.md.")

    database.init_db()

    async def post_init(app):
        try:
            await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        except Exception as e:
            logger.warning("set_chat_menu_button failed: %s", e)
        # ?? ????????? ??? ????? ?????? start/check; ??? ?????? ????? ?????? ??????????? ? /start
        if BotCommandScopeDefault is not None:
            try:
                await app.bot.set_my_commands(commands=COMMANDS_USER, scope=BotCommandScopeDefault())
                logger.info("Default commands set successfully")
            except Exception as e:
                logger.warning("set_my_commands default failed: %s", e)
        else:
            logger.warning("BotCommandScopeDefault not available, skipping default command setup")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^(my_days|change_specialty|photo_center|help|about|back_to_menu)$"))
    application.add_handler(CallbackQueryHandler(button_check, pattern="^check_sub$"))
    application.add_handler(CallbackQueryHandler(specialty_selected, pattern="^spec_\\d+$"))
    application.add_handler(CallbackQueryHandler(day_selected, pattern="^day_[123]$"))
    application.add_handler(CallbackQueryHandler(change_day, pattern="^change_day$"))
    application.add_handler(CommandHandler("notify_day1", notify_day1))
    application.add_handler(CommandHandler("notify_day2", notify_day2))
    application.add_handler(CommandHandler("notify_day3", notify_day3))
    application.add_handler(CommandHandler("notify_ready", notify_ready))
    application.add_handler(CommandHandler("broadcast_feb2026", broadcast_feb2026))

    logger.info("Bot starting (run_polling)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
