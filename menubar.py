"""Discord Jiggler — menu bar app กัน AFK บน macOS"""
import json
import logging
import os
import subprocess
import sys
from datetime import datetime

import rumps

from jiggler import is_trusted, jiggle, seconds_since_last_input

APP_NAME = "Discord Jiggler"
LABEL = "com.pan.anti-afk.menubar"
SUPPORT_DIR = os.path.expanduser("~/Library/Application Support/AntiAFK")
CONFIG_FILE = os.path.join(SUPPORT_DIR, "config.json")
LOG_FILE = os.path.expanduser("~/Library/Logs/anti-afk.log")
PLIST = os.path.expanduser("~/Library/LaunchAgents/%s.plist" % LABEL)
A11Y_PANE = "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"

IDLE_CHOICES = [3, 5, 10, 15]   # ตัวเลือกในเมนู (นาที)
CHECK_INTERVAL = 5              # เช็คสถานะ idle ทุกกี่วินาที
FRAME_INTERVAL = 0.5            # เปลี่ยนเฟรมอนิเมชันทุกกี่วินาที (ยิ่งถี่ยิ่งกิน CPU)

# ใช้อีโมจิที่ความกว้างเท่ากันทุกเฟรม ไม่งั้นไอคอนบน menu bar จะกระตุกซ้าย-ขวา
ICON_IDLE = "🐭"                                    # ตอนปิดอนิเมชัน
ICON_PAUSED = "😴"                                  # ตอน pause
ICON_BLOCKED = "⚠️"                                 # ตอนยิง event ไม่ออก (ไม่มีสิทธิ์)
SPIN_FRAMES = "🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛"          # หมุนตอนกำลังเฝ้าดู
BURST_FRAMES = "🐭💨"                               # เด้งตอนเพิ่งขยับเมาส์
BURST_TICKS = 4                                     # เด้งนานกี่เฟรม (4 x 0.5 = 2 วิ)

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    encoding="utf-8",   # .app ถูกเปิดโดยไม่มี LANG -> ไม่ใส่แล้วไทยกลายเป็น \uXXXX
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
        self.blocked = False  # macOS กลืน event ทิ้งอยู่มั้ย (ไม่มีสิทธิ์ Accessibility)
        self.checked = False  # ลอง jiggle จริงตอนเปิดแอปแล้วรึยัง
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
        self.perm_item = rumps.MenuItem("Fix permission…", callback=self.open_a11y)

        self.menu = [
            self.status_item,
            self.last_item,
            None,
            self.pause_item,
            self.idle_menu,
            self.animate_item,
            rumps.MenuItem("Open log", callback=self.open_log),
            None,
            self.perm_item,
            self.login_item,
        ]

        self.refresh()
        logging.info("Menu bar app started (idle %d mins, accessibility=%s)",
                     self.cfg["minutes"], "granted" if is_trusted() else "NOT granted")
        rumps.Timer(self.tick, CHECK_INTERVAL).start()
        self.anim_timer = rumps.Timer(self.draw_icon, FRAME_INTERVAL)
        self.draw_icon()

    # --- วาดเมนูใหม่ให้ตรงกับ state ปัจจุบัน ---
    def refresh(self):
        paused = self.cfg["paused"]
        if self.blocked:
            self.status_item.title = "⚠️ Blocked — ยังไม่ได้สิทธิ์ Accessibility"
        elif paused:
            self.status_item.title = "⏸ Paused"
        else:
            self.status_item.title = "● Running (idle %d min)" % self.cfg["minutes"]
        self.last_item.title = "Last jiggle: %s" % (self.last_jiggle or "—")
        self.pause_item.title = "Resume" if paused else "Pause"
        for item in self.idle_menu.values():
            item.state = int(item.title == "%d min" % self.cfg["minutes"])
        self.animate_item.state = int(self.cfg["animate"])
        self.login_item.state = int(os.path.exists(PLIST))
        self.perm_item.title = "⚠️ Fix permission…" if self.blocked else "Fix permission…"

    # --- วาดไอคอนบน menu bar ---
    def draw_icon(self, _timer=None):
        if self.blocked:                   # ยิง event ไม่ออก -> ขึ้นเตือนค้างไว้
            icon = ICON_BLOCKED
        elif self.cfg["paused"]:
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
        need = not self.blocked and (
            self.burst_left > 0 or (self.cfg["animate"] and not self.cfg["paused"])
        )
        if need and not self.spinning:
            self.anim_timer.start()
            self.spinning = True
        elif not need and self.spinning:
            self.anim_timer.stop()
            self.spinning = False

    def do_jiggle(self, first_run=False):
        """ขยับเมาส์ + อัปเดตสถานะตามผลจริง คืนค่า True ถ้าตัวนับ idle รีเซ็ตจริง"""
        if jiggle():
            if self.blocked:
                self.blocked = False
                logging.info("Jiggle working again (accessibility granted)")
                self.refresh()
                self.draw_icon()
            return True

        # CGEventPost เงียบสนิทตอนไม่มีสิทธิ์ -> ตัวนับ idle ไม่รีเซ็ต -> เด้งซ้ำ
        # ทุก CHECK_INTERVAL ตลอดกาล ทั้งที่ Discord ยังเห็นเราเป็น AFK
        # เตือนแค่ครั้งเดียวตอนเปลี่ยนสถานะ ไม่งั้น log ท่วมทุก 5 วิ
        if not self.blocked:
            self.blocked = True
            logging.error(
                "Jiggle failed: macOS ทิ้ง event — เปิดสิทธิ์ Accessibility ให้ %s",
                APP_NAME,
            )
            self.refresh()
            self.draw_icon()
            if first_run:
                self.open_a11y(None)
        return False

    # --- หัวใจ: เช็คทุก CHECK_INTERVAL วินาที ---
    def tick(self, _timer):
        if self.cfg["paused"]:
            return

        # ลองของจริงหนึ่งครั้งตอนเปิดแอป จะได้รู้เลยว่าสิทธิ์ครบมั้ย
        # ไม่ต้องปล่อยเครื่องนิ่งครบ 10 นาทีก่อนถึงจะเจอว่าพัง
        if not self.checked:
            self.checked = True
            if self.do_jiggle(first_run=True):
                logging.info("Self-check passed: event ยิงออกและ idle รีเซ็ตจริง")
            return

        # ติดสิทธิ์อยู่ -> ลองใหม่ทุกรอบ (event ถูกกลืนทิ้ง ไม่กวนเมาส์อยู่แล้ว)
        # จะได้เด้งกลับมาเขียวเองภายใน 5 วิ ทันทีที่ Pan เปิดสิทธิ์ ไม่ต้องรอครบ idle
        if self.blocked:
            self.do_jiggle()
            return

        if seconds_since_last_input() < self.cfg["minutes"] * 60:
            return
        if not self.do_jiggle():
            return

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

    def open_a11y(self, _sender):
        subprocess.Popen(["open", A11Y_PANE])
        rumps.alert(
            title="เปิดสิทธิ์ Accessibility",
            message=(
                "%s ต้องได้สิทธิ์ Accessibility ถึงจะขยับเมาส์แทนเราได้\n\n"
                "1. หา %s ในหน้า System Settings ที่เพิ่งเปิดขึ้นมา\n"
                "2. เปิดสวิตช์ให้ %s (ถ้ายังไม่มีในลิสต์ กด + แล้วเลือกจาก /Applications)\n"
                "3. ถ้าเปิดสวิตช์แล้วยังไม่หาย ให้ลบออกจากลิสต์แล้วเพิ่มใหม่ "
                "หรือรัน: tccutil reset PostEvent com.pan.anti-afk\n"
                "4. เปิดแอปใหม่" % (APP_NAME, APP_NAME, APP_NAME)
            ),
        )

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
