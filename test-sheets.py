
# -*- coding: utf-8 -*-
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import sheets

def main():
    url = os.getenv("SHEETS_WEBAPP_URL", "").strip()
    if not url:
        print("SHEETS_WEBAPP_URL ne zadan v .env")
        return
    print("Otpravlyayu testovyye dannye...")
    ok1 = sheets.append_status(999999, "test", "proverka svyazi")
    ok2 = sheets.append_subscription(user_id=999999, username="test_user", first_name="Test", notify_days="")
    if ok1 and ok2:
        print("Vse ok! Otkroyte tablicu.")
    else:
        print("Oshibka. Proverite SHEETS_WEBAPP_URL v .env")

if __name__ == "__main__":
    main()
