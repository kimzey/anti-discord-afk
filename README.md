# Discord Anti-AFK Script (macOS) 🐭

สคริปต์ Python สำหรับขยับเมาส์อัตโนมัติ (Mouse Jiggler) เพื่อป้องกันสถานะ "Away" (AFK) บน Discord หรือแอปพลิเคชันอื่นๆ ทำงานเบื้องหลังอย่างเงียบๆ และสามารถตั้งค่าให้เริ่มทำงานทันทีที่เปิดเครื่องได้

## ✨ คุณสมบัติ
- **ทำงานเบื้องหลัง:** ไม่รบกวนการใช้งานทั่วไป
- **Smart Idle Check:** ตรวจสอบการใช้งานเมาส์จริง โปรแกรมจะขยับเมาส์ให้เฉพาะเมื่อคุณ **ไม่ได้ขยับเมาส์เอง** ตามเวลาที่กำหนดเท่านั้น (ไม่กวนการทำงานปกติ)
- **ประหยัดทรัพยากร:** ใช้ทรัพยากรเครื่องน้อยมาก
- **Auto-start:** รองรับการทำงานอัตโนมัติเมื่อเปิดเครื่อง (macOS)

---

## 📋 สิ่งที่ต้องเตรียม
1. เครื่องคอมพิวเตอร์ระบบปฏิบัติการ **macOS**
2. **Python 3** (ติดตั้งผ่าน Homebrew หรือมาพร้อมเครื่อง)
3. โฟลเดอร์สำหรับเก็บไฟล์โปรเจกต์

---

## 🛠 วิธีการติดตั้งและใช้งาน (Installation)

แนะนำให้ติดตั้งผ่าน **Virtual Environment (venv)** เพื่อความสะอาดและป้องกันปัญหา Library ตีกัน

### 1. ติดตั้ง
เปิด **Terminal** และรันคำสั่งทีละบรรทัด:

```bash
# 1. เข้าไปที่โฟลเดอร์โปรเจกต์ (แก้ path ตามที่คุณเก็บไฟล์)
cd ~/Desktop/project/anti-afk

# 2. สร้าง Virtual Environment ชื่อ 'venv'
python3 -m venv venv

# 3. ติดตั้ง Library ที่จำเป็น (pyautogui)
./venv/bin/pip install pyautogui
```

### 2. ทดลองรัน (Manual Run)
```bash
./venv/bin/python anti-afk.py
```
*หากต้องการหยุดการทำงาน ให้กด `Ctrl + C`*

### 3. การตั้งค่าเวลา (Configuration)
หากต้องการเปลี่ยนระยะเวลาที่ต้องรอให้เมาส์นิ่งก่อนเริ่มขยับ ให้เปิดไฟล์ `anti-afk.py` และแก้ไขตัวเลขในบรรทัด:
```python
MINUTES = 10  # โปรแกรมจะรอให้เมาส์นิ่งครบ 10 นาทีก่อนจึงจะเริ่มขยับ
```

### 4. การกลับมาใช้งานครั้งถัดไป (Re-entry)
เมื่อคุณปิด Terminal ไปแล้วและต้องการกลับมารันสคริปต์ใหม่ ให้ทำดังนี้:
```bash
# 1. เข้าไปที่โฟลเดอร์โปรเจกต์
cd ~/Desktop/project/anti-afk

# 2. เปิดใช้งาน Environment (สังเกตจะมีวงเล็บ (venv) นำหน้า)
source venv/bin/activate

# 3. รันสคริปต์
python anti-afk.py
```
*หมายเหตุ: หากต้องการออกจาก Environment ให้พิมพ์คำสั่ง `deactivate`*

---

## ⚙️ ตั้งค่าให้รันตอนเปิดเครื่อง (Auto-start)

เราจะใช้ **Automator** ของ macOS เพื่อสร้างแอปพลิเคชันสำหรับรันสคริปต์นี้

1. เปิดโปรแกรม **Automator** → เลือก **Application**
2. ค้นหาคำสั่ง **"Run Shell Script"** แล้วลากมาไว้ที่หน้าต่างด้านขวา
3. เปลี่ยนตัวเลือก **Pass input** เป็น **"to stdin"**
4. คัดลอกโค้ดด้านล่างไปใส่ (🔴 **อย่าลืมแก้ `YOUR_USER` เป็นชื่อ User ของคุณ**):
   ```bash
   # เรียกใช้ Python จากใน venv โดยตรง
   /Users/YOUR_USER/Desktop/project/anti-afk/venv/bin/python /Users/YOUR_USER/Desktop/project/anti-afk/anti-afk.py
   ```
5. กด `Cmd + S` บันทึกชื่อแอปว่า **"DiscordJiggler"** ไว้ในโฟลเดอร์ `Applications`

---

## 🔐 การตั้งค่าสิทธิ์ (Permissions)

เพื่อให้สคริปต์สามารถควบคุมเมาส์และรันตอนเปิดเครื่องได้:

1. **Login Items:**
   - ไปที่ `System Settings` → `General` → `Login Items`
   - กดปุ่ม `+` แล้วเลือกแอป **DiscordJiggler** ที่เราสร้างไว้

2. **Accessibility (สำคัญ):**
   - ไปที่ `System Settings` → `Privacy & Security` → `Accessibility`
   - กดเปิดสวิตช์ให้ **DiscordJiggler** (เพื่อให้สคริปต์ขยับเมาส์ได้)

---

## 🔍 การจัดการและตรวจสอบ (Management)

เนื่องจากแอปทำงานเบื้องหลัง (Background Process) จะไม่มีหน้าต่างแสดง

**เช็คสถานะการทำงาน:**
```bash
ps -ef | grep anti-afk.py
```

**สั่งหยุดการทำงาน (Kill Process):**
```bash
pkill -f anti-afk.py
```

---

## 🗑 การถอนการติดตั้ง (Uninstallation)
1. สั่งหยุดโปรแกรม: `pkill -f anti-afk.py`
2. ลบออกจาก Login Items ใน System Settings
3. ลบไฟล์แอป **DiscordJiggler** ใน Applications
4. ลบโฟลเดอร์โปรเจกต์ทิ้งได้เลย