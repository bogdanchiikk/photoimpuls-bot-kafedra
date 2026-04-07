# -*- coding: utf-8 -*-
"""Test Google Sheets connection. Run: python3 test_sheets.py"""

import os

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_script_dir, ".env")

def _load_env_manual():
    """Read .env manually if dotenv fails."""
    if not os.path.isfile(_env_path):
        return
    for enc in ("utf-8", "latin-1", "cp1251"):
        try:
            with open(_env_path, "r", encoding=enc) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SHEETS_WEBAPP_URL=") and "=" in line:
                        val = line.split("=", 1)[1].strip().strip('"\'')
                        if val and not val.startswith("#"):
                            os.environ["SHEETS_WEBAPP_URL"] = val
                            return
        except Exception:
            continue

try:
    from dotenv import load_dotenv
    load_dotenv(_env_path, encoding="latin-1")
except ImportError:
    pass
_load_env_manual()

import sheets

def main():
    url = os.getenv("SHEETS_WEBAPP_URL", "").strip()
    if not url:
        print("ERROR: SHEETS_WEBAPP_URL not set in .env")
        print("Add: SHEETS_WEBAPP_URL=https://script.google.com/macros/s/xxx/exec")
        return

    print("Sending test data to Google Sheets...")

    ok1 = sheets.append_status(999999, "test", "connection check")
    ok2 = sheets.append_subscription(
        user_id=999999,
        username="test_user",
        first_name="Test",
        notify_days="",
    )

    if ok1 and ok2:
        print("OK! Open your Google Sheet - Status and Subscriptions tabs")
        print("should have new rows with user_id=999999.")
    else:
        print("ERROR. Check:")
        print("1. SHEETS_WEBAPP_URL in .env - copied fully?")
        print("2. Web App deployed with 'Anyone' access?")
        print("3. Apps Script saved and deployed?")

if __name__ == "__main__":
    main()
