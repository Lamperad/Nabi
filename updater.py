"""
Nabi Auto-Updater
Checks GitHub releases for newer versions and offers to update.
Works for both PyInstaller .exe builds and source installs.
"""

import os
import sys
import json
import platform
import subprocess

VERSION_FILE = "version_info.json"
GITHUB_REPO = "Lamperad/Nabi"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_current_version():
    """Import version from nabi_gui or fall back to reading the file."""
    try:
        # When running as .exe, read from bundled version
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        vf = os.path.join(base, VERSION_FILE)
        if os.path.exists(vf):
            with open(vf) as f:
                return json.load(f).get("version", "0.0.0")
    except Exception:
        pass
    return "0.0.0"


def parse_version(v):
    """Parse 'x.y.z' into tuple for comparison."""
    try:
        parts = v.lstrip("vV").split(".")
        return tuple(int(p) for p in parts)
    except Exception:
        return (0, 0, 0)


def fetch_latest_release():
    """Fetch latest release info from GitHub API. Returns dict or None."""
    try:
        import urllib.request
        req = urllib.request.Request(GITHUB_API, headers={"User-Agent": "Nabi-Updater"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def get_platform_asset(assets):
    """Find the right download asset for this platform."""
    system = platform.system().lower()
    if system == "windows":
        suffix = "Windows.exe"
    elif system == "darwin":
        suffix = "macOS"
    else:
        suffix = "Linux"

    for asset in assets:
        name = asset.get("name", "")
        if suffix.lower() in name.lower():
            return asset
    return None


def download_update(url, dest_path):
    """Download the update file with progress indication."""
    try:
        import urllib.request
        print(f"Downloading update...")
        req = urllib.request.Request(url, headers={"User-Agent": "Nabi-Updater"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            data = b""
            chunk_size = 65536
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                data += chunk
                if total > 0:
                    pct = len(data) * 100 // total
                    print(f"\r  Progress: {pct}%  ({len(data) // 1024}KB / {total // 1024}KB)", end="", flush=True)
            print()

        with open(dest_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def apply_update_exe(download_path):
    """Replace the running .exe with the downloaded one."""
    current_exe = sys.executable
    backup = current_exe + ".old"

    try:
        # Rename current exe as backup
        if os.path.exists(backup):
            os.remove(backup)
        os.rename(current_exe, backup)
        os.rename(download_path, current_exe)

        print("Update applied! Restarting...")
        # Launch the new exe and exit
        if platform.system().lower() == "windows":
            subprocess.Popen([current_exe], creationflags=subprocess.DETACHED_PROCESS)
        else:
            os.execv(current_exe, [current_exe])
        sys.exit(0)
    except Exception as e:
        print(f"Failed to apply update: {e}")
        # Try to restore backup
        if os.path.exists(backup) and not os.path.exists(current_exe):
            os.rename(backup, current_exe)
        return False


def apply_update_source(download_path):
    """For source installs, save the downloaded file and inform the user."""
    print(f"Update downloaded to: {download_path}")
    print("Since you're running from source, please replace your files manually,")
    print("or run 'git pull' to get the latest version.")
    return True


def check_for_updates(current_version, headless=False):
    """Main update check. Returns True if update was applied.
    If headless=True, skip user prompt and just report availability."""
    release = fetch_latest_release()
    if not release:
        return False

    tag = release.get("tag_name", "")
    latest_ver = parse_version(tag)
    current_ver = parse_version(current_version)

    if latest_ver <= current_ver:
        return False

    release_name = release.get("name", tag)
    body = release.get("body", "")
    body_preview = body[:200] + "..." if len(body) > 200 else body

    print(f"\n{'='*50}")
    print(f"  NEW VERSION AVAILABLE: {tag}")
    print(f"  Current: v{current_version}")
    print(f"  {release_name}")
    if body_preview:
        print(f"\n  {body_preview}")
    print(f"{'='*50}")

    if headless:
        return True

    # Ask user
    while True:
        choice = input("\nWould you like to update now? (yes/no): ").strip().lower()
        if choice in ("yes", "y"):
            break
        elif choice in ("no", "n"):
            print("Skipping update. You can update later from the main menu.")
            return False
        else:
            print("Please enter 'yes' or 'no'.")

    assets = release.get("assets", [])
    is_frozen = getattr(sys, 'frozen', False)

    if is_frozen:
        asset = get_platform_asset(assets)
        if not asset:
            print("No compatible download found for your platform.")
            print(f"Visit: https://github.com/{GITHUB_REPO}/releases/latest")
            return False

        download_url = asset["browser_download_url"]
        temp_path = sys.executable + ".new"
        if download_update(download_url, temp_path):
            return apply_update_exe(temp_path)
        return False
    else:
        # Source install — try git pull
        repo_dir = os.path.dirname(os.path.abspath(__file__))
        git_dir = os.path.join(repo_dir, ".git")
        if os.path.isdir(git_dir):
            print("Pulling latest changes from GitHub...")
            try:
                result = subprocess.run(
                    ["git", "pull", "origin", "base"],
                    cwd=repo_dir, capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    print(f"Updated successfully!\n{result.stdout}")
                    print("Please restart Nabi to use the new version.")
                    return True
                else:
                    print(f"Git pull failed: {result.stderr}")
            except Exception as e:
                print(f"Git pull error: {e}")

        print(f"Visit https://github.com/{GITHUB_REPO}/releases/latest to download manually.")
        return False


if __name__ == "__main__":
    ver = get_current_version()
    print(f"Current version: {ver}")
    check_for_updates(ver)
