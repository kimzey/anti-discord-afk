#!/bin/bash
# ติดตั้ง Anti-AFK แบบคำสั่งเดียว: สร้าง venv + ลง library + ตั้งให้รันอัตโนมัติตอน login
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="com.pan.anti-afk"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PY="$DIR/venv/bin/python3"
MINUTES="${1:-10}"

# arg แรกคือจำนวนนาที (ตัวเลขเท่านั้น)
case "$MINUTES" in
    ''|*[!0-9.]*)
        echo "ใช้: ./install.sh [นาที]   เช่น ./install.sh 5   (default 10)" >&2
        exit 1
        ;;
esac

# หา python ที่สร้าง venv ได้จริง (บางเครื่อง brew python พังเรื่อง pyexpat)
pick_python() {
    local probe
    probe="$(mktemp -d)"
    for c in python3 python3.13 python3.12 /opt/homebrew/bin/python3.13 /usr/bin/python3; do
        command -v "$c" >/dev/null 2>&1 || continue
        if "$c" -m venv "$probe/v" >/dev/null 2>&1; then
            rm -rf "$probe"
            echo "$c"
            return 0
        fi
        rm -rf "$probe/v"
    done
    rm -rf "$probe"
    return 1
}

echo "==> 1/3 สร้าง virtual environment"
if [ ! -x "$PY" ]; then
    BASE_PY="$(pick_python)" || {
        echo "❌ หา Python ที่ใช้งานได้ไม่เจอ — ลอง: brew reinstall python@3.13" >&2
        exit 1
    }
    echo "    ใช้ $BASE_PY ($("$BASE_PY" -V 2>&1))"
    "$BASE_PY" -m venv "$DIR/venv"
fi

echo "==> 2/3 ติดตั้ง dependencies"
"$DIR/venv/bin/pip" install --quiet --upgrade pip
"$DIR/venv/bin/pip" install --quiet -r "$DIR/requirements.txt"

echo "==> 3/3 ตั้ง LaunchAgent (auto-start ตอน login)"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cat > "$PLIST" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PY</string>
        <string>$DIR/anti-afk.py</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>ANTI_AFK_MINUTES</key>
        <string>$MINUTES</string>
    </dict>
    <key>WorkingDirectory</key>
    <string>$DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/anti-afk.out.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/anti-afk.err.log</string>
</dict>
</plist>
PLIST_EOF

launchctl bootout "gui/$UID/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID" "$PLIST"

echo
echo "✅ ติดตั้งเสร็จ — ทำงานอยู่เบื้องหลังแล้ว (idle $MINUTES นาที)"
echo
echo "🔐 เหลืออีกขั้นเดียว: เปิดสิทธิ์ Accessibility ให้ python ตัวนี้"
echo "   System Settings → Privacy & Security → Accessibility → กด +"
echo "   ในหน้าต่างเลือกไฟล์ กด Cmd+Shift+G แล้ววาง path นี้:"
echo "   $PY"
echo
echo "   (ถ้าไม่เปิด เมาส์จะไม่ขยับ — log จะขึ้นว่า jiggled แต่เมาส์นิ่ง)"
echo
echo "ดู log:      tail -f ~/Library/Logs/anti-afk.log"
echo "เช็คสถานะ:   launchctl list | grep anti-afk"
echo "ถอนออก:      ./uninstall.sh"
