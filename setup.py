"""py2app config — build DiscordJiggler.app

    ./venv/bin/python3 setup.py py2app
"""
from setuptools import setup

setup(
    app=["menubar.py"],
    name="DiscordJiggler",
    options={
        "py2app": {
            "argv_emulation": False,
            "packages": ["rumps"],
            "includes": ["jiggler"],
            "iconfile": "assets/AppIcon.icns",
            "plist": {
                "CFBundleName": "DiscordJiggler",
                "CFBundleDisplayName": "Discord Jiggler",
                "CFBundleIdentifier": "com.pan.anti-afk",
                "CFBundleVersion": "1.0.0",
                "CFBundleShortVersionString": "1.0.0",
                "LSUIElement": True,   # อยู่แค่ menu bar ไม่โผล่ใน Dock / Cmd-Tab
                "LSMinimumSystemVersion": "11.0",
                "NSHumanReadableCopyright": "Anti-AFK",
            },
        }
    },
    setup_requires=["py2app"],
)
