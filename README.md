# Discord Jiggler 🐭

แอป macOS กันสถานะ **"Away" (AFK)** บน Discord — อยู่บน menu bar เงียบ ๆ ขยับเมาส์ให้อัตโนมัติเมื่อคุณไม่ได้แตะเครื่องนานเกินกำหนด

## ✨ คุณสมบัติ
- **ไอคอนมีอนิเมชัน:** 🕐 หมุนตอนกำลังเฝ้าดู → 🐭💨 เด้งตอนเพิ่งขยับเมาส์ → 😴 ตอน pause เหลือบตาดูก็รู้ว่ามันยังทำงานอยู่
- **Smart Idle Check:** อ่าน **system idle time จริง** ของ macOS ซึ่งนับทั้งเมาส์และคีย์บอร์ด — นั่งพิมพ์งานอยู่มันจะไม่มากวน ต่างจาก jiggler ทั่วไปที่ดูแค่ตำแหน่งเมาส์
- **ตั้งเวลาได้จากเมนู:** 3 / 5 / 10 / 15 นาที
- **Start at login:** ติ๊กในเมนูได้เลย
- **เบามาก:** ไม่มีหน้าต่าง ไม่กิน Dock ไม่โผล่ Cmd-Tab

---

## 🚀 ติดตั้ง

เปิด **`DiscordJiggler.dmg`** → ลาก **DiscordJiggler** ลงโฟลเดอร์ **Applications** → เปิดจาก Launchpad

จบ ไม่ต้องแตะ Terminal เลย

> **ครั้งแรกถ้า macOS ขึ้นว่า "ไม่สามารถเปิดได้ เพราะไม่ทราบผู้พัฒนา"**
> คลิกขวาที่แอป → **Open** → กด **Open** ยืนยัน (แค่ครั้งเดียว)
> เกิดเพราะแอปเซ็นแบบ ad-hoc ไม่ได้ผ่าน Apple notarization — ปกติสำหรับแอปที่ build ใช้เอง

### หน้าตาเมนู
```
🕐 (หมุนอยู่)
├─ ● Running (idle 10 min)
├─ Last jiggle: 13:15:28
├─ ──────────────
├─ Pause
├─ Idle time  ▸  3 / 5 / 10 / 15 min
├─ Animate icon        ✓
├─ Open log
├─ ──────────────
├─ Start at login
└─ Quit
```

### ไอคอนบอกอะไรบ้าง
| ไอคอน | แปลว่า |
|---|---|
| 🕐 หมุน | กำลังทำงาน เฝ้านับเวลา idle อยู่ |
| 🐭💨 เด้ง 2 วิ | เพิ่งขยับเมาส์ให้ไปเมื่อกี้ |
| 😴 นิ่ง | pause อยู่ |
| 🐭 นิ่ง | ทำงานอยู่ แต่ปิด `Animate icon` ไว้ |

ไม่ชอบไอคอนขยับไปมา ติ๊ก **Animate icon** ออกได้ (อนิเมชันกิน CPU เพิ่มราว 0.5%)

ค่าที่ตั้งไว้เก็บที่ `~/Library/Application Support/AntiAFK/config.json`
Log อยู่ที่ `~/Library/Logs/anti-afk.log`

---

## 🔨 Build .dmg เอง

```bash
./install.sh        # เตรียม venv + dependencies
./build-dmg.sh      # ได้ DiscordJiggler.dmg
```

ใช้ py2app ห่อ Python runtime ไว้ในแอปทั้งก้อน — เครื่องปลายทางไม่ต้องมี Python

---

## 💻 ทางเลือก: รันแบบ command line

ไม่อยากได้ไอคอนบน menu bar ก็รันเป็น background service ได้:

```bash
./install.sh 10     # ติดตั้ง + ตั้งให้รันตอน login (10 = จำนวนนาที)
./uninstall.sh      # ถอดออก
```

หรือรันสด ๆ ดูเฉย ๆ:
```bash
./venv/bin/python3 anti-afk.py              # Ctrl+C เพื่อหยุด
ANTI_AFK_MINUTES=3 ./venv/bin/python3 anti-afk.py
```

จัดการ service:
```bash
tail -f ~/Library/Logs/anti-afk.log            # ดู log สด
launchctl list | grep anti-afk                 # เช็คว่ารันอยู่มั้ย (มี PID = รันอยู่)
launchctl kickstart -k gui/$UID/com.pan.anti-afk   # restart
```

> ⚠️ **อย่าใช้พร้อมกับ menu bar app** — จะมีสองตัวขยับเมาส์ชนกัน เลือกอย่างใดอย่างหนึ่ง

---

## 📁 ไฟล์ในโปรเจกต์

| ไฟล์ | หน้าที่ |
|---|---|
| `jiggler.py` | แกนหลัก — อ่าน idle time + ขยับเมาส์ผ่าน Quartz |
| `menubar.py` | menu bar app (rumps) |
| `anti-afk.py` | เวอร์ชัน command line |
| `install.sh` / `uninstall.sh` | ติดตั้ง/ถอดแบบ command line |
| `build-dmg.sh` / `setup.py` | build `.app` → `.dmg` |

---

## 🩺 Troubleshooting

**เปิดแอปแล้วไม่เห็นอะไรเลย** — ดูที่ menu bar มุมขวาบน (ข้าง ๆ นาฬิกา) ไม่มีหน้าต่างและไม่มีไอคอนใน Dock ถ้า menu bar เต็มจนไอคอนถูกซ่อน ลองปิดแอปอื่นหรือใช้ Bartender

**ไม่เห็นมันขยับเมาส์** — ปกติครับ ตั้งไว้ 10 นาที ต้องปล่อยเครื่องนิ่งครบ 10 นาทีก่อน อยากลองเร็ว ๆ ให้ตั้ง `Idle time → 3 min` แล้วเปิด `Open log` ดู

**Discord ยังขึ้น Away** — ลดเวลาลงเหลือ 3 นาที (Discord ตัดที่ราว ๆ 10 นาที)

**เมาส์ไม่ขยับจริง ๆ** — เปิดสิทธิ์ให้แอป: `System Settings` → `Privacy & Security` → `Accessibility` → เพิ่ม **DiscordJiggler**

**`build-dmg.sh` หา Python ไม่เจอ / venv สร้างไม่ได้** — brew python บางเวอร์ชันพัง (`ensurepip` ล้มที่ `pyexpat`) `install.sh` จะข้ามไปหาตัวที่ใช้ได้ให้เอง ถ้าไม่เหลือเลย: `brew reinstall python@3.13`

---

## 🗑 ถอนการติดตั้ง

ลาก **DiscordJiggler** จาก Applications ลงถังขยะ แล้วเก็บกวาดที่เหลือ:
```bash
launchctl bootout gui/$UID/com.pan.anti-afk.menubar 2>/dev/null
rm -f ~/Library/LaunchAgents/com.pan.anti-afk.menubar.plist
rm -rf ~/Library/Application\ Support/AntiAFK ~/Library/Logs/anti-afk*.log
```
