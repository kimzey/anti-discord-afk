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
CHECK_INTERVAL = 5              # เช็คทุกกี่วินาที
ICON_ACTIVE = "🐭"
ICON_PAUSED = "😴"

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def load_config():
    cfg = {"minutes": 10, "paused": False}
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
        super().__init__(APP_NAME, title=ICON_ACTIVE, quit_button="Quit")
        self.cfg = load_config()
        self.last_jiggle = None

        # ระวัง: rumps ใช้ title เป็น key ของเมนู -> ห้ามตั้งชื่อเริ่มต้นซ้ำกัน ไม่งั้นทับกันหาย
        self.status_item = rumps.MenuItem("Status")
        self.last_item = rumps.MenuItem("Last jiggle")
        self.pause_item = rumps.MenuItem("Pause", callback=self.toggle_pause)
        self.idle_menu = rumps.MenuItem("Idle time")
        for minutes in IDLE_CHOICES:
            self.idle_menu.add(rumps.MenuItem("%d min" % minutes, callback=self.set_idle))
        self.login_item = rumps.MenuItem("Start at login", callback=self.toggle_login)

        self.menu = [
            self.status_item,
            self.last_item,
            None,
            self.pause_item,
            self.idle_menu,
            rumps.MenuItem("Open log", callback=self.open_log),
            None,
            self.login_item,
        ]

        self.refresh()
        logging.info("Menu bar app started (idle %d mins)", self.cfg["minutes"])
        rumps.Timer(self.tick, CHECK_INTERVAL).start()

    # --- วาดเมนูใหม่ให้ตรงกับ state ปัจจุบัน ---
    def refresh(self):
        paused = self.cfg["paused"]
        self.title = ICON_PAUSED if paused else ICON_ACTIVE
        self.status_item.title = (
            "⏸ Paused" if paused else "● Running (idle %d min)" % self.cfg["minutes"]
        )
        self.last_item.title = "Last jiggle: %s" % (self.last_jiggle or "—")
        self.pause_item.title = "Resume" if paused else "Pause"
        for item in self.idle_menu.values():
            item.state = int(item.title == "%d min" % self.cfg["minutes"])
        self.login_item.state = int(os.path.exists(PLIST))

    # --- หัวใจ: เช็คทุก CHECK_INTERVAL วินาที ---
    def tick(self, _timer):
        if self.cfg["paused"]:
            return
        if seconds_since_last_input() >= self.cfg["minutes"] * 60:
            jiggle()
            self.last_jiggle = datetime.now().strftime("%H:%M:%S")
            logging.info("Activity Detected: Mouse Jiggled (Preventing AFK)")
            self.refresh()

    # --- callbacks ---
    def toggle_pause(self, _sender):
        self.cfg["paused"] = not self.cfg["paused"]
        save_config(self.cfg)
        logging.info("Paused" if self.cfg["paused"] else "Resumed")
        self.refresh()

    def set_idle(self, sender):
        self.cfg["minutes"] = int(sender.title.split()[0])
        save_config(self.cfg)
        logging.info("Idle threshold set to %d mins", self.cfg["minutes"])
        self.refresh()

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
