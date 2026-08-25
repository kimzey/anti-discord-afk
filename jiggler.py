"""แกนหลักของ Anti-AFK — คุยกับ macOS ผ่าน Quartz โดยตรง

ทำไมไม่เช็คจากตำแหน่งเมาส์: เพราะถ้านั่งพิมพ์คีย์บอร์ดอยู่โดยไม่แตะเมาส์
วิธีเดิมจะนับว่า "idle" แล้วเด้งขยับเมาส์กวนเรา ส่วน macOS มีตัวนับ idle จริง
ที่รวมทั้งเมาส์และคีย์บอร์ด ซึ่งเป็นตัวเดียวกับที่ Discord ใช้ตัดสินว่า AFK
"""
import time

import Quartz


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
    """
    x, y = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    for dx in (1, -1):
        event = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventMouseMoved, (x + dx, y), 0
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        time.sleep(0.05)
    return x, y
