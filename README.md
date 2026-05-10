# Nabi

A text-based RPG engine that converts screenplay/fade-in files into interactive tales.

## Quick Start

```bash
python nabi.py
```

## How It Works

Nabi is built around **tales** — screenplay-format text files that Nabi parses and plays back as interactive narratives. Your stats, inventory, and progression persist across all tales.

### Main Menu

- **Tales** — browse and play available tales
- **Manage Tales** — import, rename, or delete tales
- **Save Game** — save your current stats
- **Quit** — save and exit

### Writing Tales

Tales are plain text files in standard screenplay format:

```
INT. DARK FOREST - NIGHT

The wind howls through the trees. A shadowy figure blocks the path.

STRANGER

You shouldn't be here, traveler.

[COMBAT: Shadow Knight]

The figure crumbles to dust, leaving behind a glowing chest.

[LOOT_BOX]

[SAVE]
```

### Importing Tales

**From a file:**
1. Save your tale as a `.txt` or `.fadein` file
2. Open Nabi → **Manage Tales** → **Import Tale from File**
3. Enter the file path and give it a name
4. The tale appears in your **Tales** list

**By pasting:**
1. Open Nabi → **Manage Tales** → **Paste Tale Content**
2. Give the tale a name
3. Paste your screenplay text directly into the terminal
4. Type `END` on a new line and press Enter

**Supported formats:**
- `.txt` — plain text screenplay format
- `.fadein` — Fade In Professional Screenwriting files (ZIP/XML)
- Raw Open Screenplay Format XML

### System Triggers

Embed these tags in your screenplay files to fire core systems mid-tale:

| Tag | What it does |
|-----|-------------|
| `[COMBAT: Enemy Name]` | Starts a battle against the named enemy |
| `[SHOP]` | Opens the trading post |
| `[LOOT_BOX]` | Opens a mystery loot box |
| `[CURSED_LOOT_BOX]` | Opens a cursed loot box |
| `[GAIN_XP: 50]` | Awards XP (triggers level-up if enough) |
| `[GAIN_COINS: 100]` | Awards coins (capped at 500) |
| `[SAVE]` | Saves progress mid-tale |

If the player dies during combat, the tale ends early and returns to the menu.

### Screenplay Format Rules

**Plain text (`.txt`):**
- **Scene headings** start with `INT.` or `EXT.`
- **Character names** are written in ALL CAPS on their own line
- **Dialogue** follows the character name (blank line between is fine)
- **Action/description** is any other text within a scene
- **Triggers** are `[TAG]` on their own line

**Fade In (`.fadein`):**
- Standard Fade In files are auto-detected and parsed
- Scene Heading, Character, Dialogue, Parenthetical, Action, and Transition styles are all recognized
- You can embed `[TRIGGER]` tags in Action paragraphs within Fade In
- Supports OSF versions 1.2, 2.x, and 4.x

### Core Systems

All systems persist across tales through `save_data.json`:

- **Combat** — turn-based battles with attack, defend, items, flee, and mid-combat shop access
- **Shop** — buy HP/DP restores, permanent stat buffs, potions, and max HP upgrades
- **Loot Boxes** — random rewards (weapons, stat boosts, coins, or curses)
- **XP & Leveling** — 100 XP per level, each level boosts ATK/HP/DP
- **Cowardice** — fleeing combat increases cowardice, making future enemies stronger
- **Inventory** — HP and DP potions usable in combat

### Cheats

- Type `godmode` at any prompt to max out HP/ATK/DEF
- Type `kill` during combat to instantly win

## File Structure

```
nabi.py            # Main game engine
save_data.json     # Player save file (auto-generated)
tales/             # Parsed tale JSON files (auto-generated)
tales_index.json   # Tale registry (auto-generated)
```
