#!/usr/bin/env python3
"""News Front Page 24 November 2026.

Copies the pre-composed front-page image (entry.png, 1024x1024 PNG)
byte-for-byte to the output directory. No network, no randomness:
running this program twice always produces identical output bytes.
"""
import os
import shutil
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)
    print("wrote", dst)


if __name__ == "__main__":
    sys.exit(main())
