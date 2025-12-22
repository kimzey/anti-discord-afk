import pyautogui
import time
import sys
import logging
from datetime import datetime

# --- ตั้งค่าตรงนี้ (Configuration) ---
MINUTES = 10         # โปรแกรมจะรอให้เมาส์นิ่งครบตามเวลานี้ (นาที) ก่อนจึงจะเริ่มขยับ
CHECK_INTERVAL = 5   # เช็คการขยับของเมาส์ทุกๆ กี่วินาที (ไม่ต้องแก้ก็ได้)
LOG_FILE = "anti-afk.log" # ชื่อไฟล์ Log

# --- ตั้งค่าระบบ Log ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    # แปลงนาทีเป็นวินาที
    idle_threshold = MINUTES * 60
    
    current_idle_time = 0
    last_mouse_pos = pyautogui.position()

    start_msg = f"Started Anti-AFK on {sys.platform}. Mode: Smart Idle Check ({MINUTES} mins)"
    print(start_msg)
    logging.info(start_msg)

    try:
        while True:
            # รอเวลาเช็ครรอบถัดไป
            time.sleep(CHECK_INTERVAL)
            
            # เก็บตำแหน่งเมาส์ปัจจุบัน
            current_mouse_pos = pyautogui.position()

            # เช็คว่าเมาส์ขยับไหม?
            if current_mouse_pos != last_mouse_pos:
                # ถ้าตำแหน่งเปลี่ยน (เราขยับเมาส์เอง) -> รีเซ็ตเวลานับถอยหลัง
                current_idle_time = 0
                last_mouse_pos = current_mouse_pos
                # print("User is active. Timer reset.") # Uncomment ถ้าอยากเห็นตอนเทส
            else:
                # ถ้าตำแหน่งเดิม (ไม่ได้แตะเมาส์) -> เพิ่มเวลาสะสม
                current_idle_time += CHECK_INTERVAL

            # ถ้าเมาส์นิ่งเกินเวลาที่กำหนดแล้ว -> สั่งขยับ!
            if current_idle_time >= idle_threshold:
                pyautogui.moveRel(1, 0)
                pyautogui.moveRel(-1, 0)
                
                log_msg = "Activity Detected: Mouse Jiggled (Preventing AFK)"
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
                logging.info(log_msg)

                # รีเซ็ตเวลา และอัปเดตตำแหน่งเมาส์ล่าสุด
                current_idle_time = 0
                last_mouse_pos = pyautogui.position()

    except KeyboardInterrupt:
        stop_msg = "Script Stopped by User"
        print(f"\n{stop_msg}")
        logging.info(stop_msg)

if __name__ == "__main__":
    main()