#!/bin/bash
# ถอน Anti-AFK: หยุดโปรแกรม + ลบ LaunchAgent (+ venv ถ้าใส่ --all)
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="com.pan.anti-afk"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$UID/$LABEL" 2>/dev/null || true
rm -f "$PLIST"
pkill -f anti-afk.py 2>/dev/null || true
echo "✅ หยุดและถอด auto-start แล้ว"

if [ "${1:-}" = "--all" ]; then
    rm -rf "$DIR/venv"
    rm -f "$HOME/Library/Logs/anti-afk.log" "$HOME/Library/Logs/anti-afk.out.log" "$HOME/Library/Logs/anti-afk.err.log"
    echo "✅ ลบ venv + log แล้ว"
fi

echo "อย่าลืมเอา python ออกจาก System Settings → Privacy & Security → Accessibility ด้วย"
