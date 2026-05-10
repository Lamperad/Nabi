#!/usr/bin/env python3
"""
Build Nabi into a standalone executable using PyInstaller.

Usage:
    python build.py           # Build for current platform
    python build.py --onedir  # Build as a folder (faster startup)

Requirements:
    pip install pyinstaller
"""
import subprocess
import sys
import os

def main():
    onedir = "--onedir" in sys.argv

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "Nabi",
        "--windowed",
        "--add-data", f"assets/avatars{os.pathsep}assets/avatars",
        "--add-data", f"assets/backgrounds{os.pathsep}assets/backgrounds",
        "--add-data", f"assets/sounds{os.pathsep}assets/sounds",
        "--add-data", f"assets/icon.png{os.pathsep}assets",
        "--clean",
        "-y",
    ]

    if os.path.exists(icon_path):
        cmd.extend(["--icon", icon_path])

    if onedir:
        cmd.append("--onedir")
    else:
        cmd.append("--onefile")

    cmd.append("nabi_gui.py")

    print(f"Building Nabi ({'onedir' if onedir else 'onefile'})...")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
