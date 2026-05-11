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

    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "icon.ico")

    # Generate version_info.json for the updater
    import json
    version_file = os.path.join(base_dir, "version_info.json")
    try:
        # Read VERSION from nabi_gui.py
        with open(os.path.join(base_dir, "nabi_gui.py")) as f:
            for line in f:
                if line.startswith("VERSION"):
                    ver = line.split("=")[1].strip().strip('"').strip("'")
                    break
            else:
                ver = "0.0.0"
        with open(version_file, "w") as f:
            json.dump({"version": ver}, f)
        print(f"Generated version_info.json (v{ver})")
    except Exception as e:
        print(f"Warning: Could not generate version_info.json: {e}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "Nabi",
        "--windowed",
        "--add-data", f"assets/avatars{os.pathsep}assets/avatars",
        "--add-data", f"assets/backgrounds{os.pathsep}assets/backgrounds",
        "--add-data", f"assets/sounds{os.pathsep}assets/sounds",
        "--add-data", f"assets/icon.png{os.pathsep}assets",
        "--add-data", f"updater.py{os.pathsep}.",
        "--add-data", f"version_info.json{os.pathsep}.",
        "--hidden-import", "updater",
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
