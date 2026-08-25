#!/bin/bash
# build .app แล้วห่อเป็น .dmg สำหรับลาก install
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="DiscordJiggler"
VOL="Discord Jiggler"
DMG="$DIR/$APP.dmg"
STAGE="$DIR/build/dmg"

cd "$DIR"

echo "==> 1/4 ตรวจ build environment"
[ -x "./venv/bin/python3" ] || { echo "❌ ยังไม่มี venv — รัน ./install.sh ก่อน" >&2; exit 1; }
./venv/bin/python3 -c "import py2app, rumps" 2>/dev/null || \
    ./venv/bin/pip install --quiet -r requirements-build.txt

echo "==> 2/4 build $APP.app"
rm -rf build dist "$DMG"
./venv/bin/python3 setup.py py2app > /dev/null 2>&1
[ -d "dist/$APP.app" ] || { echo "❌ build ไม่สำเร็จ" >&2; exit 1; }

echo "==> 3/4 เซ็นแบบ ad-hoc"
codesign --force --deep --sign - "dist/$APP.app" 2>/dev/null
codesign --verify "dist/$APP.app" && echo "    ✓ signature ผ่าน"

echo "==> 4/4 สร้าง $APP.dmg"
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -R "dist/$APP.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create -volname "$VOL" -srcfolder "$STAGE" -ov -format UDZO -quiet "$DMG"
rm -rf "$STAGE"

echo
echo "✅ เสร็จ: $DMG  ($(du -h "$DMG" | cut -f1))"
echo "   เปิดแล้วลาก DiscordJiggler ลง Applications ได้เลย"
