# -*- coding: utf-8 -*-
"""Google Sheets: Subscriptions and Status sheets. Web App or API."""

import os
import json
import logging
import urllib.request
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _now_iso():
    """Current time in configured timezone (e.g. Europe/Moscow)."""
    tz_name = os.getenv("SHEETS_TIMEZONE", "Europe/Moscow").strip()
    if not tz_name:
        tz_name = "UTC"
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(tz_name)).isoformat()
    except Exception:
        try:
            import pytz
            return datetime.now(pytz.timezone(tz_name)).isoformat()
        except Exception:
            return datetime.now().isoformat()

SHEET_SUBS = "\u041f\u043e\u0434\u043f\u0438\u0441\u043a\u0438"  # ????????
SHEET_STATUS = "\u0421\u0442\u0430\u0442\u0443\u0441"  # ??????


def _load_sheets_env():
    """Load SHEETS_WEBAPP_URL from .env if not set."""
    if os.getenv("SHEETS_WEBAPP_URL"):
        return
    _dir = os.path.dirname(os.path.abspath(__file__))
    _env = os.path.join(_dir, ".env")
    if not os.path.isfile(_env):
        return
    for enc in ("utf-8", "latin-1", "cp1251"):
        try:
            with open(_env, "r", encoding=enc) as f:
                for line in f:
                    s = line.strip()
                    if s.startswith("SHEETS_WEBAPP_URL=") and "=" in s:
                        val = s.split("=", 1)[1].strip().strip('"\'')
                        if val and not val.startswith("#"):
                            os.environ["SHEETS_WEBAPP_URL"] = val
                            return
        except Exception:
            continue


_load_sheets_env()

SHEETS_WEBAPP_URL = os.getenv("SHEETS_WEBAPP_URL", "").strip()
SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_ID", "")
CREDENTIALS_PATH = os.getenv(
    "GOOGLE_CREDENTIALS",
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json"),
)

HEADERS_SUBSCRIPTIONS = [
    "timestamp", "user_id", "username", "first_name",
    "specialty_id", "specialty_name", "notify_days",
]
HEADERS_STATUS = ["timestamp", "user_id", "status", "value"]


def _send_to_webapp(action: str, data: dict) -> bool:
    if not SHEETS_WEBAPP_URL:
        return False
    try:
        payload = json.dumps({"action": action, "data": data}).encode("utf-8")
        req = urllib.request.Request(
            SHEETS_WEBAPP_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result.get("ok", False)
    except Exception as e:
        logger.warning("Web App error: %s", e)
        return False


def _get_client():
    if not SPREADSHEET_ID:
        return None
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return None
    if not os.path.isfile(CREDENTIALS_PATH):
        return None
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scopes)
        gc = gspread.authorize(creds)
        return gc.open_by_key(SPREADSHEET_ID)
    except Exception as e:
        logger.exception("Google Sheets API error: %s", e)
        return None


def _get_or_create_sheet(spreadsheet, title: str, headers: list):
    try:
        worksheet = spreadsheet.worksheet(title)
    except Exception:
        worksheet = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(headers))
        worksheet.append_row(headers)
    else:
        first_row = worksheet.row_values(1)
        if not first_row or first_row != headers:
            worksheet.clear()
            worksheet.append_row(headers)
    return worksheet


def append_subscription(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    specialty_id: Optional[str] = None,
    specialty_name: Optional[str] = None,
    notify_days: Optional[str] = None,
) -> bool:
    if SHEETS_WEBAPP_URL:
        data = {
            "timestamp": _now_iso(),
            "user_id": user_id,
            "username": username or "",
            "first_name": first_name or "",
            "specialty_id": specialty_id or "",
            "specialty_name": specialty_name or "",
            "notify_days": notify_days or "",
        }
        if _send_to_webapp("subscription", data):
            logger.info("Written to Subscriptions (Web App): user_id=%s", user_id)
            return True

    spreadsheet = _get_client()
    if not spreadsheet:
        return False
    try:
        ws = _get_or_create_sheet(spreadsheet, SHEET_SUBS, HEADERS_SUBSCRIPTIONS)
        row = [
            _now_iso(),
            str(user_id),
            username or "",
            first_name or "",
            specialty_id or "",
            specialty_name or "",
            notify_days or "",
        ]
        ws.append_row(row)
        logger.info("Written to Subscriptions (API): user_id=%s", user_id)
        return True
    except Exception as e:
        logger.exception("Error writing to Subscriptions: %s", e)
        return False


def append_status(user_id: int, status: str, value: str = "") -> bool:
    if SHEETS_WEBAPP_URL:
        data = {
            "timestamp": _now_iso(),
            "user_id": user_id,
            "status": status,
            "value": value or "",
        }
        if _send_to_webapp("status", data):
            logger.info("Written to Status (Web App): user_id=%s, status=%s", user_id, status)
            return True

    spreadsheet = _get_client()
    if not spreadsheet:
        return False
    try:
        ws = _get_or_create_sheet(spreadsheet, SHEET_STATUS, HEADERS_STATUS)
        row = [
            _now_iso(),
            str(user_id),
            status,
            value or "",
        ]
        ws.append_row(row)
        logger.info("Written to Status (API): user_id=%s, status=%s", user_id, status)
        return True
    except Exception as e:
        logger.exception("Error writing to Status: %s", e)
        return False
