"""Discord Jiggler — menu bar app กัน AFK บน macOS"""
import json
import logging
import os
import subprocess
import sys
from datetime import datetime

import rumps

from jiggler import jiggle, seconds_since_last_input

APP_NAME = "Discord Jiggler"
LABEL = "com.pan.anti-afk.menubar"
SUPPORT_DIR = os.path.expanduser("~/Library/Application Support/AntiAFK")
CONFIG_FILE = os.path.join(SUPPORT_DIR, "config.json")
LOG_FILE = os.path.expanduser("~/Library/Logs/anti-afk.log")
PLIST = os.path.expanduser("~/Library/LaunchAgents/%s.plist" % LABEL)

IDLE_CHOICES = [3, 5, 10, 15]   # ตัวเลือกในเมนู (นาที)
CHECK_INTERVAL = 5              # เช็คสถานะ idle ทุกกี่วินาที
FRAME_INTERVAL = 0.5            # เปลี่ยนเฟรมอนิเมชันทุกกี่วินาที (ยิ่งถี่ยิ่งกิน CPU)

# ใช้อีโมจิที่ความกว้างเท่ากันทุกเฟรม ไม่งั้นไอคอนบน menu bar จะกระตุกซ้าย-ขวา
ICON_IDLE = "🐭"                                    # ตอนปิดอนิเมชัน
ICON_PAUSED = "😴"                                  # ตอน pause
SPIN_FRAMES = "🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛"          # หมุนตอนกำลังเฝ้าดู
BURST_FRAMES = "🐭💨"                               # เด้งตอนเพิ่งขยับเมาส์
BURST_TICKS = 4                                     # เด้งนานกี่เฟรม (4 x 0.5 = 2 วิ)

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def load_config():
    cfg = {"minutes": 10, "paused": False, "animate": True}
    try:
        with open(CONFIG_FILE) as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass  # ไฟล์ยังไม่มีหรือพัง -> ใช้ค่า default
    if cfg["minutes"] not in IDLE_CHOICES:
        cfg["minutes"] = 10
    return cfg


def save_config(cfg):
    os.makedirs(SUPPORT_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)


def launch_target():
    """คำสั่งที่ LaunchAgent จะใช้เรียกแอปตอน login"""
    if getattr(sys, "frozen", False):        # รันจาก .app ที่ build แล้ว
        return [os.path.realpath(sys.executable)]
    return [sys.executable, os.path.abspath(__file__)]   # รันจาก source


class AntiAFKApp(rumps.App):
    def __init__(self):
        super().__init__(APP_NAME, title=ICON_IDLE, quit_button="Quit")
        self.cfg = load_config()
        self.last_jiggle = None
        self.frame = 0        # เฟรมปัจจุบันของอนิเมชันหมุน
        self.burst_left = 0   # เหลืออีกกี่เฟรมของอนิเมชันตอน jiggle
        self.drawn = None     # ไอคอนที่วาดไว้ล่าสุด กันเขียนทับด้วยค่าเดิม
        self.spinning = False # timer อนิเมชันเดินอยู่มั้ย

        # ระวัง: rumps ใช้ title เป็น key ของเมนู -> ห้ามตั้งชื่อเริ่มต้นซ้ำกัน ไม่งั้นทับกันหาย
        self.status_item = rumps.MenuItem("Status")
        self.last_item = rumps.MenuItem("Last jiggle")
        self.pause_item = rumps.MenuItem("Pause", callback=self.toggle_pause)
        self.idle_menu = rumps.MenuItem("Idle time")
        for minutes in IDLE_CHOICES:
            self.idle_menu.add(rumps.MenuItem("%d min" % minutes, callback=self.set_idle))
        self.animate_item = rumps.MenuItem("Animate icon", callback=self.toggle_animate)
        self.login_item = rumps.MenuItem("Start at login", callback=self.toggle_login)

        self.menu = [
            self.status_item,
            self.last_item,
            None,
            self.pause_item,
            self.idle_menu,
            self.animate_item,
            rumps.MenuItem("Open log", callback=self.open_log),
            None,
            self.login_item,
        ]

        self.refresh()
        logging.info("Menu bar app started (idle %d mins)", self.cfg["minutes"])
        rumps.Timer(self.tick, CHECK_INTERVAL).start()
        self.anim_timer = rumps.Timer(self.draw_icon, FRAME_INTERVAL)
        self.draw_icon()

    # --- วาดเมนูใหม่ให้ตรงกับ state ปัจจุบัน ---
    def refresh(self):
        paused = self.cfg["paused"]
        self.status_item.title = (
            "⏸ Paused" if paused else "● Running (idle %d min)" % self.cfg["minutes"]
        )
        self.last_item.title = "Last jiggle: %s" % (self.last_jiggle or "—")
        self.pause_item.title = "Resume" if paused else "Pause"
        for item in self.idle_menu.values():
            item.state = int(item.title == "%d min" % self.cfg["minutes"])
        self.animate_item.state = int(self.cfg["animate"])
        self.login_item.state = int(os.path.exists(PLIST))

    # --- วาดไอคอนบน menu bar ---
    def draw_icon(self, _timer=None):
        if self.cfg["paused"]:
            icon = ICON_PAUSED
        elif self.burst_left > 0:          # เพิ่งขยับเมาส์ไป -> เด้งให้เห็น
            self.burst_left -= 1
            icon = BURST_FRAMES[self.burst_left % len(BURST_FRAMES)]
        elif not self.cfg["animate"]:
            icon = ICON_IDLE
        else:                              # กำลังเฝ้าดูอยู่ -> หมุนไปเรื่อย ๆ
            self.frame = (self.frame + 1) % len(SPIN_FRAMES)
            icon = SPIN_FRAMES[self.frame]

        # แตะ self.title ทีไร Cocoa วาด status item ใหม่ทุกครั้ง แม้ค่าเดิม -> เขียนเฉพาะตอนเปลี่ยนจริง
        if icon != self.drawn:
            self.drawn = icon
            self.title = icon
        self.sync_anim()

    def sync_anim(self):
        """เดิน timer เฉพาะตอนมีเฟรมต้องขยับจริง ๆ นอกนั้นหยุดให้ CPU ว่าง"""
        need = self.burst_left > 0 or (self.cfg["animate"] and not self.cfg["paused"])
        if need and not self.spinning:
            self.anim_timer.start()
            self.spinning = True
        elif not need and self.spinning:
            self.anim_timer.stop()
            self.spinning = False

    # --- หัวใจ: เช็คทุก CHECK_INTERVAL วินาที ---
    def tick(self, _timer):
        if self.cfg["paused"]:
            return
        if seconds_since_last_input() >= self.cfg["minutes"] * 60:
            jiggle()
            self.burst_left = BURST_TICKS
            self.last_jiggle = datetime.now().strftime("%H:%M:%S")
            logging.info("Activity Detected: Mouse Jiggled (Preventing AFK)")
            self.refresh()
            self.draw_icon()   # ปลุก timer ให้กลับมาเดินเพื่อเล่นอนิเมชันเด้ง

    # --- callbacks ---
    def toggle_pause(self, _sender):
        self.cfg["paused"] = not self.cfg["paused"]
        save_config(self.cfg)
        logging.info("Paused" if self.cfg["paused"] else "Resumed")
        self.refresh()
        self.draw_icon()

    def set_idle(self, sender):
        self.cfg["minutes"] = int(sender.title.split()[0])
        save_config(self.cfg)
        logging.info("Idle threshold set to %d mins", self.cfg["minutes"])
        self.refresh()

    def toggle_animate(self, _sender):
        self.cfg["animate"] = not self.cfg["animate"]
        save_config(self.cfg)
        self.refresh()
        self.draw_icon()

    def open_log(self, _sender):
        open(LOG_FILE, "a").close()
        subprocess.Popen(["open", LOG_FILE])

    def toggle_login(self, _sender):
        if os.path.exists(PLIST):
            subprocess.run(["launchctl", "bootout", "gui/%d/%s" % (os.getuid(), LABEL)],
                           capture_output=True)
            os.remove(PLIST)
        else:
            os.makedirs(os.path.dirname(PLIST), exist_ok=True)
            args = "".join("        <string>%s</string>\n" % a for a in launch_target())
            with open(PLIST, "w") as f:
                f.write(
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                    '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                    '<plist version="1.0">\n<dict>\n'
                    "    <key>Label</key>\n    <string>%s</string>\n"
                    "    <key>ProgramArguments</key>\n    <array>\n%s    </array>\n"
                    "    <key>RunAtLoad</key>\n    <true/>\n"
                    "</dict>\n</plist>\n" % (LABEL, args)
                )
            subprocess.run(["launchctl", "bootstrap", "gui/%d" % os.getuid(), PLIST],
                           capture_output=True)
        self.refresh()


if __name__ == "__main__":
    AntiAFKApp().run()
