"""แกนหลักของ Anti-AFK — คุยกับ macOS ผ่าน Quartz โดยตรง

ทำไมไม่เช็คจากตำแหน่งเมาส์: เพราะถ้านั่งพิมพ์คีย์บอร์ดอยู่โดยไม่แตะเมาส์
วิธีเดิมจะนับว่า "idle" แล้วเด้งขยับเมาส์กวนเรา ส่วน macOS มีตัวนับ idle จริง
ที่รวมทั้งเมาส์และคีย์บอร์ด ซึ่งเป็นตัวเดียวกับที่ Discord ใช้ตัดสินว่า AFK
"""
import ctypes
import ctypes.util
import time

import Quartz

# ถือว่า jiggle สำเร็จถ้าตัวนับ idle ตกลงมาต่ำกว่านี้ (วินาที)
# ตัว jiggle เองใช้เวลา ~0.1 วิ เลยเผื่อไว้ที่ 1 วิ
RESET_THRESHOLD = 1.0


def seconds_since_last_input():
    """วินาทีที่ผ่านไปตั้งแต่ผู้ใช้แตะเมาส์หรือคีย์บอร์ดครั้งล่าสุด"""
    return Quartz.CGEventSourceSecondsSinceLastEventType(
        Quartz.kCGEventSourceStateHIDSystemState,
        Quartz.kCGAnyInputEventType,
    )


def jiggle():
    """ขยับเมาส์ 1px แล้วดึงกลับที่เดิม — ทำให้ตัวนับ idle ของระบบรีเซ็ต

    ต้องยิงเป็น event เข้า HID tap (ไม่ใช่ CGWarpMouseCursorPosition)
    ไม่งั้นเคอร์เซอร์ขยับก็จริงแต่ตัวนับ idle ไม่รีเซ็ต = กัน AFK ไม่ได้

    คืนค่า True ถ้าตัวนับ idle รีเซ็ตจริง / False ถ้า macOS กลืน event ทิ้ง
    ซึ่งเกิดตอนแอปยังไม่ได้สิทธิ์ Accessibility — CGEventPost จะเงียบสนิท
    ไม่ error ไม่ throw ทำให้ดูเหมือนทำงานอยู่ทั้งที่ Discord ยังเห็นเราเป็น AFK
    """
    x, y = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    for pos in ((x + 1, y), (x, y)):   # ไปแล้วกลับ ไม่งั้นเคอร์เซอร์ไหลไปทางซ้ายเรื่อย ๆ
        event = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventMouseMoved, pos, 0
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        time.sleep(0.05)
    return seconds_since_last_input() < RESET_THRESHOLD


def is_trusted():
    """แอปอยู่ในลิสต์ Accessibility มั้ย — ใช้บอกใบ้ตอน start เท่านั้น

    ห้ามใช้ตัดสินว่า jiggle จะสำเร็จมั้ย เพราะสิทธิ์ยิง event มีสองช่อง
    (Accessibility กับ PostEvent) ตัวนี้เห็นแค่ช่องแรก — ตัวตัดสินจริงคือ
    ค่าที่ jiggle() คืนมา
    """
    try:
        lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library("ApplicationServices"))
        lib.AXIsProcessTrusted.restype = ctypes.c_bool
        return bool(lib.AXIsProcessTrusted())
    except (OSError, AttributeError, TypeError):
        return False
