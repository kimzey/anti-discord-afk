"""สร้าง AppIcon.icns จากอีโมจิ 🐭 ด้วย Cocoa

รันเมื่ออยากเปลี่ยนไอคอนแอป (แก้ EMOJI ข้างล่างแล้วรัน):
    ./venv/bin/python3 assets/make-icon.py
"""
import os
import subprocess

from AppKit import (NSAttributedString, NSBitmapImageRep, NSColor, NSFont,
                    NSFontAttributeName, NSGraphicsContext)

EMOJI = "🐭"
HERE = os.path.dirname(os.path.abspath(__file__))
ICONSET = os.path.join(HERE, "AppIcon.iconset")
PNG_TYPE = 4


def render(size, path):
    rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, size, size, 8, 4, True, False, "NSCalibratedRGBColorSpace", 0, 0)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.setCurrentContext_(
        NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep))
    NSColor.clearColor().set()
    font = NSFont.fontWithName_size_("Apple Color Emoji", size * 0.72)
    text = NSAttributedString.alloc().initWithString_attributes_(
        EMOJI, {NSFontAttributeName: font})
    width, height = text.size().width, text.size().height
    text.drawAtPoint_(((size - width) / 2, (size - height) / 2))
    NSGraphicsContext.restoreGraphicsState()
    rep.representationUsingType_properties_(PNG_TYPE, {}).writeToFile_atomically_(path, True)


def main():
    os.makedirs(ICONSET, exist_ok=True)
    for size in (16, 32, 64, 128, 256, 512, 1024):
        render(size, "%s/icon_%dx%d.png" % (ICONSET, size, size))
        if size > 16:
            render(size, "%s/icon_%dx%d@2x.png" % (ICONSET, size // 2, size // 2))
    icns = os.path.join(HERE, "AppIcon.icns")
    subprocess.run(["iconutil", "-c", "icns", ICONSET, "-o", icns], check=True)
    print("wrote %s (%d bytes)" % (icns, os.path.getsize(icns)))


if __name__ == "__main__":
    main()
