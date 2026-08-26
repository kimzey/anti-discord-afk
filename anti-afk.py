"""Anti-AFK แบบ command line — สำหรับคนที่ไม่อยากใช้ menu bar app

    ./venv/bin/python3 anti-afk.py
    ANTI_AFK_MINUTES=3 ./venv/bin/python3 anti-afk.py
"""
import logging
import os
import sys
import time
from datetime import datetime

from jiggler import is_trusted, jiggle, seconds_since_last_input

# --- ตั้งค่าตรงนี้ (Configuration) ---
MINUTES = float(os.environ.get("ANTI_AFK_MINUTES", 10))        # นิ่งครบกี่นาทีถึงเริ่มขยับ
CHECK_INTERVAL = float(os.environ.get("ANTI_AFK_INTERVAL", 5)) # เช็คทุกกี่วินาที
LOG_FILE = os.environ.get("ANTI_AFK_LOG") or os.path.expanduser("~/Library/Logs/anti-afk.log")

os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    encoding="utf-8",   # .app ถูกเปิดโดยไม่มี LANG -> ไม่ใส่แล้วไทยกลายเป็น \uXXXX
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main():
    idle_threshold = MINUTES * 60

    start_msg = "Started Anti-AFK on %s. Mode: System Idle Check (%g mins, accessibility=%s)" % (
        sys.platform, MINUTES, "granted" if is_trusted() else "NOT granted"
    )
    print(start_msg, flush=True)
    logging.info(start_msg)

    blocked = False   # macOS กลืน event ทิ้งอยู่มั้ย

    try:
        while True:
            time.sleep(CHECK_INTERVAL)

            # ถามระบบตรง ๆ ว่าไม่มี input มากี่วินาทีแล้ว (นับทั้งเมาส์และคีย์บอร์ด)
            if seconds_since_last_input() < idle_threshold:
                continue

            if not jiggle():
                # CGEventPost เงียบสนิทตอนไม่มีสิทธิ์ -> ตัวนับ idle ไม่รีเซ็ต -> วนซ้ำ
                # ทุก CHECK_INTERVAL ตลอดกาล ทั้งที่ Discord ยังเห็นเราเป็น AFK
                # เตือนแค่ครั้งเดียวตอนเปลี่ยนสถานะ ไม่งั้น log ท่วม
                if not blocked:
                    blocked = True
                    err = ("Jiggle failed: macOS ทิ้ง event — เปิดสิทธิ์ Accessibility ให้ "
                           "python ตัวที่รันสคริปต์นี้ (System Settings > Privacy & Security "
                           "> Accessibility)")
                    print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), err), flush=True)
                    logging.error(err)
                continue

            if blocked:
                blocked = False
                logging.info("Jiggle working again (accessibility granted)")

            log_msg = "Activity Detected: Mouse Jiggled (Preventing AFK)"
            print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), log_msg), flush=True)
            logging.info(log_msg)

    except KeyboardInterrupt:
        stop_msg = "Script Stopped by User"
        print("\n%s" % stop_msg, flush=True)
        logging.info(stop_msg)


if __name__ == "__main__":
    main()
