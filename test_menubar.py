"""เทสว่าแอปรู้ตัวจริงมั้ยเมื่อ macOS กลืน event ทิ้ง (ไม่มีสิทธิ์ Accessibility)

บั๊กเดิม: CGEventPost เงียบสนิทตอนไม่มีสิทธิ์ แอปเลย log ว่า "Preventing AFK"
ทุก 5 วินาทีตลอดกาล ทั้งที่ตัวนับ idle ไม่เคยรีเซ็ตและ Discord ยังเห็นเราเป็น AFK

    PYTHONPATH=. ./venv/bin/python3 test_menubar.py
"""
import logging, sys, os
sys.argv = ["test"]

import menubar

TMP = os.path.join(os.environ.get("TMPDIR", "/tmp"), "test-anti-afk.log")
open(TMP, "w").close()
root = logging.getLogger()
for h in root.handlers[:]:
    root.removeHandler(h)
root.addHandler(logging.FileHandler(TMP))
root.setLevel(logging.INFO)

IDLE = [9999.0]
JIGGLE_OK = [False]
menubar.seconds_since_last_input = lambda: IDLE[0]
menubar.jiggle = lambda: JIGGLE_OK[0]

app = menubar.AntiAFKApp()
alerts = []
app.open_a11y = lambda _s: alerts.append(1)   # กัน modal เด้งตอนเทส

def loglines():
    return [l.strip() for l in open(TMP) if l.strip()]

fails = []
def check(cond, msg):
    print(("  ok  " if cond else "  FAIL") + "  " + msg)
    if not cond:
        fails.append(msg)

print("--- 1) self-check ตอนเปิดแอป เจอว่ายิง event ไม่ออก ---")
before = len(loglines())
app.tick(None)
new = loglines()[before:]
check(app.blocked is True, "blocked = True ตั้งแต่ tick แรก (ไม่ต้องรอ 10 นาที)")
check(len(alerts) == 1, "เด้ง dialog บอกวิธีเปิดสิทธิ์ 1 ครั้ง")
check(app.title == menubar.ICON_BLOCKED, "ไอคอนเป็น ⚠️ (ได้ %r)" % app.title)
check("Blocked" in app.status_item.title, "status บอกว่า Blocked")
check(app.perm_item.title.startswith("⚠️"), "เมนู Fix permission ติดธง")
check(app.spinning is False, "อนิเมชันหยุด ไม่กิน CPU ตอน blocked")
check(app.last_jiggle is None, "ไม่โกหกว่า jiggle สำเร็จ")
check(len(new) == 1 and "Jiggle failed" in new[0], "log error 1 บรรทัด (ได้ %d)" % len(new))

print("--- 2) ยัง blocked อยู่อีก 3 tick -> ห้าม spam log / ห้ามเด้งซ้ำ ---")
before = len(loglines())
for _ in range(3):
    app.tick(None)
check(len(loglines()) == before, "ไม่มี log เพิ่ม (ได้ +%d)" % (len(loglines()) - before))
check(len(alerts) == 1, "ไม่เด้ง dialog ซ้ำ")

print("--- 2.5) blocked อยู่ + ยังไม่ถึงเวลา idle -> ต้องยังลองใหม่ ---")
IDLE[0] = 1.0
JIGGLE_OK[0] = True
app.tick(None)
check(app.blocked is False, "หายเองภายใน 1 tick ไม่ต้องรอครบ idle")
check(app.title != menubar.ICON_BLOCKED, "ไอคอนกลับมาปกติ")
IDLE[0] = 9999.0
JIGGLE_OK[0] = False
app.tick(None)   # กลับไป blocked เพื่อเทสข้อ 3 ต่อ
check(app.blocked is True, "กลับไป blocked ได้เมื่อสิทธิ์หายอีก")

print("--- 3) Pan เปิดสิทธิ์แล้ว jiggle ผ่าน ---")
JIGGLE_OK[0] = True
before = len(loglines())
app.tick(None)   # tick แรก = หลุดจาก blocked
app.tick(None)   # tick ถัดมา = jiggle ตามปกติ (idle ยังเกิน threshold อยู่)
new = loglines()[before:]
check(app.blocked is False, "blocked = False")
check(app.title != menubar.ICON_BLOCKED, "ไอคอนกลับมาปกติ (ได้ %r)" % app.title)
check(any("working again" in l for l in new), "log ว่ากลับมาทำงาน")
check(any("Preventing AFK" in l for l in new), "log jiggle ปกติ")
check(app.last_jiggle is not None, "บันทึกเวลา jiggle ล่าสุด")

print("--- 4) ยังไม่ถึงเวลา idle -> ต้องไม่ jiggle ---")
IDLE[0] = 1.0
before = len(loglines())
app.tick(None)
check(len(loglines()) == before, "ไม่มี log เพิ่ม")

print("--- 5) pause แล้วต้องไม่แตะอะไรเลย ---")
IDLE[0] = 9999.0
app.cfg["paused"] = True
before = len(loglines())
app.tick(None)
check(len(loglines()) == before, "ไม่มี log เพิ่มตอน pause")

print()
print("FAILED: %d" % len(fails) if fails else "✅ ผ่านหมด")
sys.exit(1 if fails else 0)
