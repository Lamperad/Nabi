# Nabi

An audiovisual RPG built with Pygame. Explore the dark forest, confront Dan, and battle demons — all with graphics, sound effects, and animated UI. Releases are built automatically on every version update.

## Quick Start

```bash
pip install -r requirements.txt
python nabi_gui.py
```

Or run the original text-based version:
```bash
python nabi.py
```

## Requirements

- Python 3.8+
- Pygame 2.5+

## Features

### Visual UI
- Rendered game window (960x640) with styled panels, menus, and stat bars
- HP/DP/XP bars with real-time updates
- Typewriter text effect for story narration
- Animated loot box opening sequence
- Screen shake and flash effects in combat
- Fade transitions between scenes
- Pulsing animated title screen

### Sound Effects
- Combat: attack hits, defend, player damage, demon roar
- Systems: shop purchase, loot box open, cursed loot, coin drops
- UI: menu clicks, text ticks, save confirmation
- Events: victory fanfare, defeat, level up, flee, potion use

### Core Systems
- **Combat** — turn-based battles with attack, defend, items, flee, and mid-combat shop
- **Shop** — buy HP/DP restores, permanent stat buffs, potions, and max HP upgrades
- **Loot Boxes** — random rewards (weapons, stat boosts, coins, or curses)
- **XP & Leveling** — 100 XP per level, each level boosts ATK/HP/DP
- **Cowardice** — fleeing combat makes future enemies stronger
- **Save/Load** — persistent progress via save_data.json with death recovery

### The Story
- Dark forest with branching paths
- Dan's field — visit too many times and he transforms into a demon
- Multiple dialogue choices with consequences
- Trap path (Dan's offer) with proper GAME OVER and recovery

### Controls
- **Mouse** — click buttons and menus
- **Keyboard** — press 1-8 to select menu options
- **Cheats** — press K in combat to instant-kill, G for godmode

## Build Standalone App

Build a single executable that runs without Python installed:

```bash
pip install pyinstaller
python build.py
```

This creates `dist/Nabi` (or `dist/Nabi.exe` on Windows). Double-click to play.

For a folder build (faster startup, larger size):
```bash
python build.py --onedir
```

### Automated Builds

Every GitHub release automatically builds executables for **Windows**, **macOS**, and **Linux**. Go to [Releases](../../releases) to download the latest build for your platform.

To create a release:
1. Go to your repo → Releases → "Draft a new release"
2. Create a tag (e.g. `v3.0.0`)
3. Publish — the GitHub Action will build and attach executables automatically

You can also trigger a build manually from the Actions tab → "Build Nabi" → "Run workflow".

## File Structure

```
nabi_gui.py        # Audiovisual game (Pygame)
nabi.py            # Original text-based game
build.py           # PyInstaller build script
nabi.spec          # PyInstaller spec file
requirements.txt   # Python dependencies
.github/workflows/ # Auto-build on release
assets/
  avatars/         # Character sprite sheets
  backgrounds/     # Scene background images
  sounds/          # Generated WAV sound effects
save_data.json     # Player save file (auto-generated)
```

## Versions

- **v3.0.0** — Audiovisual Pygame edition (current)
- **v2.1.0** — Text-based with bug fixes (nabi.py)
