"""Anti-AFK แบบ command line — สำหรับคนที่ไม่อยากใช้ menu bar app

    ./venv/bin/python3 anti-afk.py
    ANTI_AFK_MINUTES=3 ./venv/bin/python3 anti-afk.py
"""
import logging
import os
import sys
import time
from datetime import datetime

from jiggler import jiggle, seconds_since_last_input

# --- ตั้งค่าตรงนี้ (Configuration) ---
MINUTES = float(os.environ.get("ANTI_AFK_MINUTES", 10))        # นิ่งครบกี่นาทีถึงเริ่มขยับ
CHECK_INTERVAL = float(os.environ.get("ANTI_AFK_INTERVAL", 5)) # เช็คทุกกี่วินาที
LOG_FILE = os.environ.get("ANTI_AFK_LOG") or os.path.expanduser("~/Library/Logs/anti-afk.log")

os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main():
    idle_threshold = MINUTES * 60

    start_msg = "Started Anti-AFK on %s. Mode: System Idle Check (%g mins)" % (sys.platform, MINUTES)
    print(start_msg, flush=True)
    logging.info(start_msg)

    try:
        while True:
            time.sleep(CHECK_INTERVAL)

            # ถามระบบตรง ๆ ว่าไม่มี input มากี่วินาทีแล้ว (นับทั้งเมาส์และคีย์บอร์ด)
            if seconds_since_last_input() >= idle_threshold:
                jiggle()
                log_msg = "Activity Detected: Mouse Jiggled (Preventing AFK)"
                print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), log_msg), flush=True)
                logging.info(log_msg)

    except KeyboardInterrupt:
        stop_msg = "Script Stopped by User"
        print("\n%s" % stop_msg, flush=True)
        logging.info(stop_msg)


if __name__ == "__main__":
    main()
