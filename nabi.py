import json
import os
import sys
import random
import copy
import re
import textwrap
import zipfile
import xml.etree.ElementTree as ET

VERSION = "3.0.0"
SAVE_FILE = "save_data.json"
TALES_DIR = "tales"
TALES_INDEX = "tales_index.json"

name = " "

DEFAULT_PLAYER_STATS = {
    "hp": 100,
    "max_hp": 100,
    "atk": 20,
    "def": 15,
    "max_def": 15,
    "coins": 0,
    "level": 1,
    "xp": 0,
    "cowardice": 0,
    "inventory": {"hp_potions": 2, "dp_potions": 2}
}
player_stats = copy.deepcopy(DEFAULT_PLAYER_STATS)

# Regex for system trigger tags inside tale files
TRIGGER_RE = re.compile(
    r"^\[("
    r"COMBAT:\s*.+"
    r"|SHOP"
    r"|LOOT_BOX"
    r"|CURSED_LOOT_BOX"
    r"|GAIN_XP:\s*\d+"
    r"|GAIN_COINS:\s*\d+"
    r"|SAVE"
    r")\]$"
)


# ============================================================
#  CORE SYSTEMS
# ============================================================

def get_input(prompt):
    user_input = input(prompt).strip()
    if user_input.lower() in ['quit', 'exit']:
        print("Thanks for playing Nabi! See you next time.")
        sys.exit()
    if user_input.lower() == "godmode":
        player_stats["hp"], player_stats["atk"], player_stats["def"] = 999, 999, 999
        print("** CHEAT ACTIVATED **")
        return get_input(prompt)
    return user_input


def get_yes_no(prompt):
    while True:
        choice = get_input(prompt).lower()
        if choice in ['yes', 'no']:
            return choice
        print("Please enter 'yes' or 'no'.")


def normalize_stats(data):
    normalized = copy.deepcopy(DEFAULT_PLAYER_STATS)
    for key, value in data.items():
        if key == "inventory" and isinstance(value, dict):
            normalized["inventory"].update(value)
        else:
            normalized[key] = value
    return normalized


def save_game():
    try:
        save_payload = player_stats.copy()
        save_payload["version"] = VERSION
        with open(SAVE_FILE, "w") as f:
            json.dump(save_payload, f, indent=4)
        print(f"\n[ SYSTEM ] Progress saved (v{VERSION}).")
    except Exception as e:
        print(f"\n[ ERROR ] Save failed: {e}")


def load_game():
    global player_stats
    if not os.path.exists(SAVE_FILE):
        return False
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            if data.get("version") != VERSION:
                print(f">> Updating save file from {data.get('version')} to {VERSION}...")
            data.pop("version", None)
            player_stats = normalize_stats(data)
            return True
    except Exception as e:
        print(f"[ ERROR ] Failed to load save file: {e}")
        return False


def drop_coins():
    loot = random.randint(10, 50)
    player_stats["coins"] = min(500, player_stats["coins"] + loot)
    if player_stats["coins"] >= 500:
        print(f"You found {loot} coins, but your wallet is full at 500!")
    else:
        print(f"The enemy dropped {loot} coins. Total: {player_stats['coins']}/500")


def gain_xp(amount):
    player_stats["xp"] += amount
    print(f"Gained {amount} XP!")
    while player_stats["xp"] >= 100:
        player_stats["level"] += 1
        player_stats["xp"] -= 100
        player_stats["max_hp"] += 20
        player_stats["hp"] = player_stats["max_hp"]
        player_stats["atk"] += 5
        player_stats["max_def"] += 5
        player_stats["def"] = player_stats["max_def"]
        print(f"\nLEVEL UP! You are now Level {player_stats['level']}!")
        print(f"Stats Increased: ATK +5 | Max HP +20 | Max DP +5")
        print("Your Health and Armor have been fully restored!")


def open_loot_shop():
    while True:
        print(f"\n---  NABI TRADING POST  ---")
        print(f"Your Wallet: {player_stats['coins']} / 500 Coins")
        print(f"Your Stats: HP: {player_stats['hp']}/{player_stats['max_hp']} | DP: {player_stats['def']}/{player_stats['max_def']} | ATK: {player_stats['atk']}")
        print("-" * 35)
        print("1. [RESTORE] Full HP (20c)")
        print("2. [REPAIR] Full Armor/DP (20c)")
        print("3. [BUFF] Permanent ATK +5 (100c)")
        print("4. [BUFF] Permanent Max DP +5 (100c)")
        print("5. [BUY] HP Potion (50c)")
        print("6. [BUY] DP Potion (50c)")
        print("7. [UPGRADE] Max HP +20 (150c)")
        print("8. [EXIT] Leave Shop")
        print("-" * 35)

        choice = get_input("What would you like to buy? ")

        if choice == "1":
            if player_stats["coins"] >= 20:
                player_stats["hp"] = player_stats["max_hp"]
                player_stats["coins"] -= 20
                print(">> Success: You feel rejuvenated! Health is full.")
            else:
                print(">> Error: Not enough coins!")
        elif choice == "2":
            if player_stats["coins"] >= 20:
                player_stats["def"] = player_stats["max_def"]
                player_stats["coins"] -= 20
                print(">> Success: Your armor is shiny and new! DP is full.")
            else:
                print(">> Error: Not enough coins!")
        elif choice == "3":
            if player_stats["coins"] >= 100:
                player_stats["atk"] += 5
                player_stats["coins"] -= 100
                print(f">> Success: Your muscles grow stronger! ATK is now {player_stats['atk']}.")
            else:
                print(">> Error: Not enough coins!")
        elif choice == "4":
            if player_stats["coins"] >= 100:
                player_stats["max_def"] += 5
                player_stats["def"] = player_stats["max_def"]
                player_stats["coins"] -= 100
                print(f">> Success: Your Max DP is now {player_stats['max_def']}.")
            else:
                print(">> Error: Not enough coins!")
        elif choice == "5":
            if player_stats["coins"] >= 50:
                player_stats["inventory"]["hp_potions"] += 1
                player_stats["coins"] -= 50
                print(f">> Success: HP Potion added! Total: {player_stats['inventory']['hp_potions']}")
            else:
                print(">> Error: Not enough coins!")
        elif choice == "6":
            if player_stats["coins"] >= 50:
                player_stats["inventory"]["dp_potions"] += 1
                player_stats["coins"] -= 50
                print(f">> Success: DP Potion added! Total: {player_stats['inventory']['dp_potions']}")
            else:
                print(">> Error: Not enough coins!")
        elif choice == "7":
            if player_stats["coins"] >= 150:
                player_stats["max_hp"] += 20
                player_stats["hp"] += 20
                player_stats["coins"] -= 150
                print(f">> Success: Max HP is now {player_stats['max_hp']}.")
            else:
                print(">> Error: Not enough coins!")
        elif choice == "8":
            print(">> Shopkeeper: Safe travels!")
            save_game()
            return
        else:
            print(">> Invalid choice. Please try again.")


def open_loot_box(is_cursed=False):
    if is_cursed:
        print("\n--- YOU FOUND A CURSED LOOT BOX! ---")
        print("It vibrates with a dark, hungry energy...")
        roll = random.randint(1, 4)
        if roll == 1:
            player_stats["atk"] += 15
            print(">> DARK BLESSING: A shadow essence coats your blade! ATK +15.")
        elif roll == 2:
            damage = int(player_stats["hp"] * 0.3)
            player_stats["hp"] -= damage
            print(f">> NEEDLE TRAP: The box was rigged! You lost {damage} HP.")
        elif roll == 3:
            player_stats["cowardice"] += 2
            print(">> OMEN: A ghostly chill enters your soul. Cowardice +2!")
        else:
            print(">> IT'S A MIMIC! The box grows teeth and snaps at you!")
            player_stats["hp"] -= 20
            print("You managed to escape but lost 20 HP in the struggle.")
    else:
        print("\n--- YOU FOUND A MYSTERY LOOT BOX! ---")
        roll = random.randint(1, 4)
        if roll == 1:
            upgrade = random.randint(10, 30)
            player_stats["max_hp"] += upgrade
            player_stats["hp"] = player_stats["max_hp"]
            print(f"Health Upgrade! Max HP is now {player_stats['max_hp']}.")
        elif roll == 2:
            weapons = {"Iron Blade": 35, "Dragon Claw": 50, "Demon Slayer": 75}
            w_name, w_atk = random.choice(list(weapons.items()))
            if w_atk > player_stats["atk"]:
                player_stats["atk"] = w_atk
                print(f"New Weapon! You equipped the {w_name} (Atk: {w_atk}).")
            else:
                player_stats["atk"] += 5
                print("Your weapon was already stronger, so you sharpened it! ATK +5.")
        elif roll == 3:
            player_stats["max_def"] += 10
            player_stats["def"] = player_stats["max_def"]
            print(f"Defense Upgrade! Your Max DP is now {player_stats['max_def']}.")
        elif roll == 4:
            if player_stats["cowardice"] > 0:
                player_stats["cowardice"] = 0
                print("Holy Relic! The weight of your cowardice has been lifted. The curse is gone!")
            else:
                bonus = 100
                player_stats["coins"] = min(500, player_stats["coins"] + bonus)
                print(f"Treasure! Gained {bonus} coins! Total: {player_stats['coins']}/500")


def start_combat(enemy_name):
    lvl_bonus = player_stats["level"] * 10
    c_mult = 1 + (player_stats.get("cowardice", 0) * 0.2)

    e_hp = int(random.randint(50 + lvl_bonus, 100 + lvl_bonus) * c_mult)
    e_atk = int(random.randint(15 + player_stats["level"], 25 + (player_stats["level"] * 2)) * c_mult)
    e_dp = int(random.randint(5 + player_stats["level"], 15 + player_stats["level"]) * c_mult)

    print(f"\n--- BATTLE: {name} (Lv.{player_stats['level']}) vs {enemy_name} ---")
    if player_stats.get("cowardice", 0) > 0:
        print(f"CURSE: Your cowardice ({player_stats['cowardice']}) makes the enemy stronger!")
    print(f"Enemy Stats: HP: {e_hp} | ATK: {e_atk} | DEF: {e_dp}")

    while player_stats["hp"] > 0 and e_hp > 0:
        defend_bonus = 0
        print(f"\n{name}: {player_stats['hp']}/{player_stats['max_hp']} HP | DP: {player_stats['def']}")
        print(f"{enemy_name}: {e_hp} HP")
        print("1. Attack | 2. Defend | 3. Use Item | 4. Run | 5. Shop | (Quit to Menu)")

        action = get_input("What is your move? ").lower()

        if action == "quit":
            print("\nReturning to the Main Menu...")
            return "menu"

        if action == "kill":
            print(f"\n** [CHEAT] You unleashed a forbidden spell! **")
            e_hp = 0
            break

        if action == "1":
            e_hp -= player_stats["atk"]
            print(f">> You strike! The {enemy_name} takes {player_stats['atk']} damage.")
        elif action == "2":
            defend_bonus = 10
            print(">> You brace yourself! Your armor will absorb more damage this turn.")
        elif action == "3":
            print(f"Potions: HP({player_stats['inventory']['hp_potions']}) | DP({player_stats['inventory']['dp_potions']})")
            item_choice = get_input("Use (HP/DP/Back): ").lower()
            if item_choice == "hp" and player_stats["inventory"]["hp_potions"] > 0:
                player_stats["hp"] = player_stats["max_hp"]
                player_stats["inventory"]["hp_potions"] -= 1
                print(">> Used HP Potion!")
                continue
            elif item_choice == "dp" and player_stats["inventory"]["dp_potions"] > 0:
                player_stats["def"] = player_stats["max_def"]
                player_stats["inventory"]["dp_potions"] -= 1
                print(">> Used DP Potion!")
                continue
            else:
                print(">> No item used.")
                continue
        elif action == "4":
            if random.random() < 0.5:
                player_stats["cowardice"] = player_stats.get("cowardice", 0) + 1
                print(f">> You escaped! Cowardice increased to {player_stats['cowardice']}!")
                return "escaped"
            else:
                print(f">> You failed to escape! {enemy_name} blocks your path!")
        elif action == "5":
            open_loot_shop()
            continue
        else:
            print("Invalid action! Choose 1, 2, 3, 4, 5, or type 'Quit'.")
            continue

        if e_hp > 0:
            if action == "2":
                defense_check = (player_stats["def"] + defend_bonus) - e_atk
                if defense_check >= 0:
                    print(f">> Your armor absorbs the hit! 0 HP lost.")
                else:
                    damage_taken = abs(defense_check)
                    player_stats["hp"] -= damage_taken
                    print(f">> Your armor cracked! You took {damage_taken} damage.")
            else:
                player_stats["hp"] -= e_atk
                print(f">> {enemy_name} hits you for {e_atk} damage!")

    if player_stats["hp"] > 0:
        print(f"\nVictory!")
        player_stats["cowardice"] = 0
        drop_coins()
        gain_xp(50)
        save_game()
        return True
    else:
        player_stats["hp"] = 0
        player_stats["cowardice"] = 0
        print(f"\n{name} has fallen in battle...")
        print("--- GAME OVER ---")
        save_game()
        return False


# ============================================================
#  TALE SYSTEM
# ============================================================

def ensure_tales_dir():
    if not os.path.exists(TALES_DIR):
        os.makedirs(TALES_DIR)


def load_tales_index():
    if not os.path.exists(TALES_INDEX):
        return {}
    try:
        with open(TALES_INDEX, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_tales_index(index):
    with open(TALES_INDEX, "w") as f:
        json.dump(index, f, indent=4)


def parse_fadein_xml(xml_content):
    """
    Parse Open Screenplay Format XML (from a .fadein ZIP or raw XML)
    into the same tale data structure used by the text parser.

    Handles OSF versions 1.2 (basestylename), 2.x (baseStyleName),
    and 4.x (basestyle).
    """
    root = ET.fromstring(xml_content)
    paragraphs = root.find("paragraphs")
    if paragraphs is None:
        return {"raw": xml_content, "scenes": []}

    tale_data = {"raw": xml_content, "scenes": []}
    current_scene = None
    current_speaker = None

    for para in paragraphs.findall("para"):
        style_el = para.find("style")
        if style_el is None:
            continue

        # Handle all OSF version attribute names
        style_name = (
            style_el.get("basestyle")
            or style_el.get("basestylename")
            or style_el.get("baseStyleName")
            or ""
        ).lower()

        # Collect all <text> elements into one string
        text_parts = [t.text or "" for t in para.findall("text")]
        text = "".join(text_parts).strip()
        if not text:
            continue

        if style_name == "scene heading":
            current_scene = {"heading": text, "beats": []}
            tale_data["scenes"].append(current_scene)
            current_speaker = None

        elif style_name == "character":
            current_speaker = text

        elif style_name in ("dialogue", "parenthetical"):
            if current_speaker and current_scene is not None:
                line = f"({text})" if style_name == "parenthetical" else text
                current_scene["beats"].append({
                    "type": "dialogue",
                    "speaker": current_speaker,
                    "line": line
                })
                current_speaker = None

        elif style_name == "transition":
            if current_scene is not None:
                current_scene["beats"].append({"type": "action", "text": text})
            current_speaker = None

        else:
            # Action, Shot, or any other style
            if TRIGGER_RE.match(text):
                if current_scene is not None:
                    current_scene["beats"].append({
                        "type": "trigger",
                        "tag": text[1:-1].strip()
                    })
            elif current_scene is not None:
                current_scene["beats"].append({"type": "action", "text": text})
            else:
                if not tale_data.get("header"):
                    tale_data["header"] = []
                tale_data["header"].append(text)
            current_speaker = None

    return tale_data


def parse_fadein_file(filepath):
    """
    Read a .fadein file (ZIP containing document.xml) and parse it.
    Falls back to reading it as raw XML if it isn't a valid ZIP.
    """
    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            xml_bytes = zf.read("document.xml")
            return parse_fadein_xml(xml_bytes.decode("utf-8"))
    except (zipfile.BadZipFile, KeyError):
        with open(filepath, "r") as f:
            return parse_fadein_xml(f.read())


def parse_screenplay_text(content):
    """
    Parse plain-text screenplay content into structured tale data.

    Supports embedded system trigger tags that fire core systems
    during tale playback:

        [COMBAT: Enemy Name]     - starts combat against Enemy Name
        [SHOP]                   - opens the trading post
        [LOOT_BOX]              - opens a mystery loot box
        [CURSED_LOOT_BOX]       - opens a cursed loot box
        [GAIN_XP: 50]           - awards XP
        [GAIN_COINS: 100]       - awards coins
        [SAVE]                  - saves progress mid-tale
    """
    lines = content.strip().split("\n")
    tale_data = {"raw": content, "scenes": []}

    current_scene = None
    current_speaker = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Scene headings (INT. / EXT.)
        if stripped.startswith("INT.") or stripped.startswith("EXT."):
            current_scene = {"heading": stripped, "beats": []}
            tale_data["scenes"].append(current_scene)
            current_speaker = None

        # System trigger tags
        elif TRIGGER_RE.match(stripped):
            if current_scene is not None:
                current_scene["beats"].append({
                    "type": "trigger",
                    "tag": stripped[1:-1].strip()
                })
            current_speaker = None

        # Character name: all-caps, short, not a heading or stage direction
        elif (stripped.isupper()
              and len(stripped.split()) <= 4
              and not stripped.startswith(("INT.", "EXT.", "THE ", "---"))
              and stripped not in ("SILENCE", "SILENCE.")):
            current_speaker = stripped

        # Dialogue line (follows a character name)
        elif current_speaker and current_scene is not None:
            current_scene["beats"].append({
                "type": "dialogue",
                "speaker": current_speaker,
                "line": stripped
            })
            current_speaker = None

        # Action / description line
        elif current_scene is not None:
            current_scene["beats"].append({
                "type": "action",
                "text": stripped
            })
        else:
            if not tale_data.get("header"):
                tale_data["header"] = []
            tale_data["header"].append(stripped)

    return tale_data


def parse_screenplay(filepath):
    """
    Auto-detect file type and parse accordingly:
    - .fadein files -> ZIP/XML parser
    - anything else -> plain-text screenplay parser
    """
    if filepath.lower().endswith(".fadein"):
        return parse_fadein_file(filepath)

    with open(filepath, "r") as f:
        content = f.read()

    # If it looks like XML, try the XML parser
    if content.strip().startswith("<?xml") or "<document" in content[:200]:
        return parse_fadein_xml(content)

    return parse_screenplay_text(content)


def execute_trigger(tag):
    """
    Run a core system based on a trigger tag embedded in a tale.

    Returns False if the player died (tale should stop), True otherwise.
    """
    if tag.startswith("COMBAT:"):
        enemy_name = tag.split(":", 1)[1].strip()
        result = start_combat(enemy_name)
        if result is False:
            return False
        return True

    elif tag == "SHOP":
        open_loot_shop()
        return True

    elif tag == "LOOT_BOX":
        open_loot_box(is_cursed=False)
        return True

    elif tag == "CURSED_LOOT_BOX":
        open_loot_box(is_cursed=True)
        return True

    elif tag.startswith("GAIN_XP:"):
        amount = int(tag.split(":", 1)[1].strip())
        gain_xp(amount)
        return True

    elif tag.startswith("GAIN_COINS:"):
        amount = int(tag.split(":", 1)[1].strip())
        player_stats["coins"] = min(500, player_stats["coins"] + amount)
        print(f"Gained {amount} coins! Total: {player_stats['coins']}/500")
        return True

    elif tag == "SAVE":
        save_game()
        return True

    else:
        print(f">> [Unknown trigger: {tag}]")
        return True


def import_tale(filepath, tale_name=None):
    """Import a tale from a screenplay / fade-in file."""
    ensure_tales_dir()

    # Strip surrounding quotes from the path (common on Windows copy-paste)
    filepath = filepath.strip('"').strip("'")

    if not os.path.exists(filepath):
        print(f">> Error: File '{filepath}' not found.")
        return False

    if not tale_name:
        tale_name = os.path.splitext(os.path.basename(filepath))[0]

    tale_data = parse_screenplay(filepath)
    tale_id = f"tale_{random.randint(10000, 99999)}"

    tale_file = os.path.join(TALES_DIR, f"{tale_id}.json")
    with open(tale_file, "w") as f:
        json.dump(tale_data, f, indent=4)

    index = load_tales_index()
    index[tale_id] = {"name": tale_name, "file": tale_file}
    save_tales_index(index)

    print(f">> Tale '{tale_name}' imported successfully! (ID: {tale_id})")
    return True


def import_tale_from_text(content, tale_name):
    """Import a tale from pasted screenplay text."""
    ensure_tales_dir()

    # If it looks like XML, use the XML parser
    if content.strip().startswith("<?xml") or "<document" in content[:200]:
        tale_data = parse_fadein_xml(content)
    else:
        tale_data = parse_screenplay_text(content)

    tale_id = f"tale_{random.randint(10000, 99999)}"

    tale_file = os.path.join(TALES_DIR, f"{tale_id}.json")
    with open(tale_file, "w") as f:
        json.dump(tale_data, f, indent=4)

    index = load_tales_index()
    index[tale_id] = {"name": tale_name, "file": tale_file}
    save_tales_index(index)

    print(f">> Tale '{tale_name}' imported successfully! (ID: {tale_id})")
    return True


def rename_tale():
    """Rename an existing tale."""
    index = load_tales_index()
    if not index:
        print(">> No tales to rename.")
        return

    tales_list = list(index.items())
    print("\n--- RENAME TALE ---")
    for i, (tid, info) in enumerate(tales_list, 1):
        print(f"  {i}. {info['name']}")

    sel = get_input("Select tale number (or 'back'): ").strip()
    if sel.lower() == "back":
        return

    try:
        sel_num = int(sel)
        if 1 <= sel_num <= len(tales_list):
            tale_id = tales_list[sel_num - 1][0]
            old_name = index[tale_id]["name"]
            new_name = get_input(f"New name for '{old_name}': ").strip()
            if new_name:
                index[tale_id]["name"] = new_name
                save_tales_index(index)
                print(f">> Renamed: '{old_name}' -> '{new_name}'")
            else:
                print(">> Name cannot be empty.")
        else:
            print(">> Invalid selection.")
    except ValueError:
        print(">> Please enter a number.")


def delete_tale():
    """Delete a tale."""
    index = load_tales_index()
    if not index:
        print(">> No tales to delete.")
        return

    tales_list = list(index.items())
    print("\n--- DELETE TALE ---")
    for i, (tid, info) in enumerate(tales_list, 1):
        print(f"  {i}. {info['name']}")

    sel = get_input("Select tale number (or 'back'): ").strip()
    if sel.lower() == "back":
        return

    try:
        sel_num = int(sel)
        if 1 <= sel_num <= len(tales_list):
            tale_id = tales_list[sel_num - 1][0]
            tale_name = index[tale_id]["name"]
            confirm = get_yes_no(f"Delete '{tale_name}'? (yes/no): ")
            if confirm == "yes":
                tale_file = index[tale_id]["file"]
                if os.path.exists(tale_file):
                    os.remove(tale_file)
                del index[tale_id]
                save_tales_index(index)
                print(f">> Tale '{tale_name}' deleted.")
        else:
            print(">> Invalid selection.")
    except ValueError:
        print(">> Please enter a number.")


def play_tale(tale_id):
    """
    Play a tale by walking through its parsed scenes and beats.

    Narrative beats (action/dialogue) are printed to the screen.
    Trigger beats fire the corresponding core system:

        [COMBAT: Enemy Name]  -> start_combat("Enemy Name")
        [SHOP]                -> open_loot_shop()
        [LOOT_BOX]           -> open_loot_box()
        [CURSED_LOOT_BOX]    -> open_loot_box(is_cursed=True)
        [GAIN_XP: 50]        -> gain_xp(50)
        [GAIN_COINS: 100]    -> awards coins
        [SAVE]               -> save_game()

    If the player dies during a trigger (e.g. lost combat), the tale
    ends early and returns to the menu.
    """
    index = load_tales_index()
    if tale_id not in index:
        print(">> Error: Tale not found.")
        return

    tale_file = index[tale_id]["file"]
    if not os.path.exists(tale_file):
        print(">> Error: Tale file missing.")
        return

    with open(tale_file, "r") as f:
        tale_data = json.load(f)

    tale_name = index[tale_id]["name"]
    print(f"\n{'=' * 40}")
    print(f"  {tale_name.upper()}")
    print(f"{'=' * 40}")

    for scene in tale_data.get("scenes", []):
        print(f"\n{scene['heading']}")
        print()
        for beat in scene.get("beats", []):
            if beat["type"] == "action":
                wrapped = textwrap.fill(beat["text"], width=70)
                print(wrapped)
                print()

            elif beat["type"] == "dialogue":
                print(f"  {beat['speaker']}")
                wrapped = textwrap.fill(
                    beat["line"], width=60,
                    initial_indent="    ", subsequent_indent="    "
                )
                print(wrapped)
                print()

            elif beat["type"] == "trigger":
                alive = execute_trigger(beat["tag"])
                if not alive:
                    print(f"\n--- Your journey through '{tale_name}' ends here. ---")
                    input("\nPress Enter to return to the menu...")
                    return

    print(f"\n{'=' * 40}")
    print("  THE END")
    print(f"{'=' * 40}")
    save_game()
    input("\nPress Enter to return to the menu...")


# ============================================================
#  TALE BROWSING & MANAGEMENT
# ============================================================

def browse_tales():
    """Show available tales and let the player select one to play."""
    while True:
        index = load_tales_index()

        print(f"\n--- TALES ---")
        if not index:
            print("  No tales available.")
            print("  Use 'Manage Tales' from the menu to import tale files.")
            input("\nPress Enter to return...")
            return

        tales_list = list(index.items())
        for i, (tid, info) in enumerate(tales_list, 1):
            print(f"  {i}. {info['name']}")
        print(f"  {len(tales_list) + 1}. Back")

        choice = get_input("\nSelect a tale: ").strip()
        try:
            choice_num = int(choice)
            if choice_num == len(tales_list) + 1:
                return
            if 1 <= choice_num <= len(tales_list):
                tale_id = tales_list[choice_num - 1][0]
                play_tale(tale_id)
            else:
                print(">> Invalid choice.")
        except ValueError:
            print(">> Please enter a number.")


def manage_tales():
    """Tale management menu: import from file, paste, rename, delete."""
    while True:
        print(f"\n--- MANAGE TALES ---")
        print("1. Import Tale from File (.txt, .fadein)")
        print("2. Paste Tale Content")
        print("3. Rename Tale")
        print("4. Delete Tale")
        print("5. Back")

        choice = get_input("Select: ").strip()

        if choice == "1":
            filepath = get_input("Enter file path: ").strip()
            tale_name = get_input("Name this tale (or press Enter to use filename): ").strip()
            import_tale(filepath, tale_name if tale_name else None)

        elif choice == "2":
            tale_name = get_input("Name this tale: ").strip()
            if not tale_name:
                print(">> Name cannot be empty.")
                continue
            print("Paste your screenplay below. When done, type END on a new line and press Enter.")
            print("-" * 35)
            lines = []
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            content = "\n".join(lines)
            if content.strip():
                import_tale_from_text(content, tale_name)
            else:
                print(">> No content pasted.")

        elif choice == "3":
            rename_tale()
        elif choice == "4":
            delete_tale()
        elif choice == "5":
            return
        else:
            print(">> Invalid choice.")


# ============================================================
#  MAIN MENU
# ============================================================

def main_menu():
    global name
    print(f"\n{'=' * 35}")
    print(f"       NABI  v{VERSION}")
    print(f"{'=' * 35}")

    if os.path.exists(SAVE_FILE):
        choice = get_yes_no("Save file found! Load previous game? (yes/no): ")
        if choice == "yes":
            if load_game():
                print(">> Save loaded!")

    if name.strip() == "":
        name = get_input("What should I call you, warrior? ")

    while True:
        print(f"\n--- MAIN MENU ---")
        print(f"  Hero: {name} | Lv.{player_stats['level']} | HP: {player_stats['hp']}/{player_stats['max_hp']}")
        print("-" * 35)
        print("1. Tales")
        print("2. Manage Tales")
        print("3. Save Game")
        print("4. Quit")
        print("-" * 35)

        choice = get_input("Select: ").strip()

        if choice == "1":
            browse_tales()
        elif choice == "2":
            manage_tales()
        elif choice == "3":
            save_game()
        elif choice == "4":
            save_game()
            print("Thanks for playing Nabi! Goodbye.")
            sys.exit()
        else:
            print(">> Invalid choice.")


if __name__ == "__main__":
    main_menu()
