import json
import os
import sys
import random
import copy

VERSION = "4.1.0"import json
import os
import sys
import random
import copy

VERSION = "4.1.0"
SAVE_FILE = "save_data.json"
name = " "
dan_patience = 0

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
    "combo": 0,
    "inventory": {"hp_potions": 2, "dp_potions": 2}
}

# DP System constants
COMBO_MAX = 100
COMBO_PER_ATTACK = 25
POWER_STRIKE_DP_COST = 10
POWER_STRIKE_MULTIPLIER = 2.5
VULNERABILITY_BONUS = 0.5
PARRY_DP_RESTORE = 5
PARRY_COUNTER_MULTIPLIER = 0.5
player_stats = copy.deepcopy(DEFAULT_PLAYER_STATS)

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

            # Recover from death: if HP is 0, restore to full
            if player_stats["hp"] <= 0:
                player_stats["hp"] = player_stats["max_hp"]
                player_stats["def"] = player_stats["max_def"]
                print(">> You were revived! HP and Armor fully restored.")

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

def open_loot_shop():
    while True:
        print(f"\n---  NABI TRADING POST  ---")
        print(f"Your Wallet: {player_stats['coins']} / 500 Coins")
        print(f"Your Stats: HP: {player_stats['hp']}/{player_stats['max_hp']} | Shield: {player_stats['def']}/{player_stats['max_def']} | ATK: {player_stats['atk']}")
        print("-" * 40)
        print("1. [RESTORE] Full HP (20c)")
        print("2. [REPAIR] Full Shield (20c)")
        print("3. [BUFF] Permanent ATK +5 (100c)")
        print("4. [BUFF] Permanent Max Shield +5 (100c)")
        print("5. [BUY] HP Potion (50c)")
        print("6. [BUY] Shield Potion (50c)")
        print("7. [UPGRADE] Max HP +20 (150c)")
        print("8. [UPGRADE] Max Shield +10 (120c)")
        print("9. [EXIT] Leave Shop")
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
                print(">> Success: Shield fully repaired!")
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
                print(f">> Success: Max Shield is now {player_stats['max_def']}.")
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
                print(f">> Success: Shield Potion added! Total: {player_stats['inventory']['dp_potions']}")
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
            if player_stats["coins"] >= 120:
                player_stats["max_def"] += 10
                player_stats["def"] = player_stats["max_def"]
                player_stats["coins"] -= 120
                print(f">> Success: Max Shield is now {player_stats['max_def']}.")
            else:
                print(">> Error: Not enough coins!")

        elif choice == "9":
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
            print(f"Shield Upgrade! Max Shield is now {player_stats['max_def']}.")
        elif roll == 4:
            if player_stats["cowardice"] > 0:
                player_stats["cowardice"] = 0
                print("Holy Relic! The weight of your cowardice has been lifted. The curse is gone!")
            else:
                bonus = 100
                player_stats["coins"] = min(500, player_stats["coins"] + bonus)
                print(f"Treasure! Gained {bonus} coins! Total: {player_stats['coins']}/500")


def apply_damage_to_player_cli(raw_damage, source_name="Enemy"):
    """Shield HP: DP absorbs first, overflow to HP. Vulnerability at 0 DP."""
    if player_stats["def"] <= 0:
        vuln_dmg = int(raw_damage * (1 + VULNERABILITY_BONUS))
        player_stats["hp"] -= vuln_dmg
        print(f">> VULNERABLE! {source_name} deals {vuln_dmg} ({raw_damage}+{vuln_dmg - raw_damage})!")
        return vuln_dmg
    if raw_damage <= player_stats["def"]:
        player_stats["def"] -= raw_damage
        print(f">> Shield absorbs {raw_damage}! (DP: {player_stats['def']}/{player_stats['max_def']})")
        return 0
    overflow = raw_damage - player_stats["def"]
    print(f">> Shield broken! {player_stats['def']} absorbed, {overflow} HP lost!")
    player_stats["def"] = 0
    player_stats["hp"] -= overflow
    return overflow

def apply_parry_cli(enemy_atk, enemy_max_atk, source_name="Enemy"):
    """Parry: restores DP, blocks through shield. Counter on strong attacks."""
    dp_restored = min(PARRY_DP_RESTORE, player_stats["max_def"] - player_stats["def"])
    player_stats["def"] += dp_restored
    reduced_dmg = max(0, enemy_atk - player_stats["def"])
    if reduced_dmg > 0:
        player_stats["def"] = 0
        player_stats["hp"] -= reduced_dmg
        print(f">> Parried! DP +{dp_restored}, but took {reduced_dmg} overflow!")
    else:
        player_stats["def"] -= enemy_atk
        print(f">> Parried! DP +{dp_restored}, shield holds! (DP: {player_stats['def']})")
    counter_dmg = 0
    if enemy_atk >= enemy_max_atk * 0.7:
        counter_dmg = int(player_stats["atk"] * PARRY_COUNTER_MULTIPLIER)
        print(f">> COUNTER-ATTACK! You strike back for {counter_dmg}!")
    return counter_dmg

def add_combo_cli(amount=COMBO_PER_ATTACK):
    player_stats["combo"] = min(COMBO_MAX, player_stats["combo"] + amount)

def get_input(prompt):
    user_input = input(prompt).strip()
    if user_input.lower() in ['quit', 'exit']:
        print("Thanks for playing Nabi! See you next time.")
        sys.exit()
    if user_input.lower() == "godmode":
        player_stats["hp"], player_stats["atk"], player_stats["def"] = 999, 999, 999
        player_stats["combo"] = COMBO_MAX
        print("** CHEAT ACTIVATED **")
        return get_input(prompt)
    return user_input

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
        player_stats["combo"] = 0
        
        print(f"\nLEVEL UP! You are now Level {player_stats['level']}!")
        print(f"Stats Increased: ATK +5 | Max HP +20 | Max Shield +5")
        print("Your Health and Shield have been fully restored!")

def start_combat(enemy_name):
    lvl_bonus = player_stats["level"] * 10
    c_mult = 1 + (player_stats.get("cowardice", 0) * 0.2)
    
    e_hp = int(random.randint(50 + lvl_bonus, 100 + lvl_bonus) * c_mult)
    e_atk = int(random.randint(15 + player_stats["level"], 25 + (player_stats["level"] * 2)) * c_mult)
    e_max_atk = e_atk
    e_dp = int(random.randint(5 + player_stats["level"], 15 + player_stats["level"]) * c_mult)

    print(f"\n--- BATTLE: {name} (Lv.{player_stats['level']}) vs {enemy_name} ---")
    if player_stats.get("cowardice", 0) > 0:
        print(f"CURSE: Your cowardice ({player_stats['cowardice']}) makes the enemy stronger!")
    print(f"Enemy Stats: HP: {e_hp} | ATK: {e_atk} | DEF: {e_dp}")

    while player_stats["hp"] > 0 and e_hp > 0:
        did_parry = False
        vuln_tag = " [VULNERABLE!]" if player_stats["def"] <= 0 else ""
        combo_tag = " [COMBO READY!]" if player_stats["combo"] >= COMBO_MAX else f" Combo: {player_stats['combo']}/{COMBO_MAX}"
        print(f"\n{name}: {player_stats['hp']}/{player_stats['max_hp']} HP | DP: {player_stats['def']}/{player_stats['max_def']}{vuln_tag}{combo_tag}")
        print(f"{enemy_name}: {e_hp} HP")

        actions = "1. Attack | 2. Parry | 3. Use Item | 4. Run | 5. Shop"
        if player_stats["combo"] >= COMBO_MAX:
            actions += " | 6. Special"
        actions += " | (Quit/Kill)"
        print(actions)
        
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
            add_combo_cli()
            print(f">> You strike! The {enemy_name} takes {player_stats['atk']} damage. Combo +{COMBO_PER_ATTACK}")
        
        elif action == "2":
            did_parry = True
            print(">> You raise your guard!")
        
        elif action == "3":
            print(f"Potions: HP({player_stats['inventory']['hp_potions']}) | Shield({player_stats['inventory']['dp_potions']})")
            item_choice = get_input("Use (HP/DP/Back): ").lower()
            
            if item_choice == "hp" and player_stats["inventory"]["hp_potions"] > 0:
                player_stats["hp"] = player_stats["max_hp"]
                player_stats["inventory"]["hp_potions"] -= 1
                print(">> Used HP Potion!")
                continue 
            elif item_choice == "dp" and player_stats["inventory"]["dp_potions"] > 0:
                player_stats["def"] = player_stats["max_def"]
                player_stats["inventory"]["dp_potions"] -= 1
                print(">> Shield restored!")
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

        elif action == "6" and player_stats["combo"] >= COMBO_MAX:
            print("COMBO SPECIAL:")
            print(f"  1. Power Strike (2.5x ATK, costs {POWER_STRIKE_DP_COST} DP)")
            print("  2. Shield Restore (full DP repair)")
            print("  3. Back")
            spec = get_input("Choose: ")
            if spec == "1":
                if player_stats["def"] >= POWER_STRIKE_DP_COST:
                    player_stats["combo"] = 0
                    player_stats["def"] -= POWER_STRIKE_DP_COST
                    dmg = int(player_stats["atk"] * POWER_STRIKE_MULTIPLIER)
                    e_hp -= dmg
                    print(f">> POWER STRIKE! -{POWER_STRIKE_DP_COST} DP, deals {dmg} damage!")
                else:
                    print(f">> Need {POWER_STRIKE_DP_COST} DP for Power Strike!")
                    continue
            elif spec == "2":
                player_stats["combo"] = 0
                old_dp = player_stats["def"]
                player_stats["def"] = player_stats["max_def"]
                print(f">> SHIELD RESTORE! DP fully repaired (+{player_stats['def'] - old_dp})!")
            else:
                continue

        else:
            print("Invalid action!")
            continue

        if e_hp > 0:
            if did_parry:
                counter_dmg = apply_parry_cli(e_atk, e_max_atk, enemy_name)
                if counter_dmg > 0:
                    e_hp -= counter_dmg
            else:
                apply_damage_to_player_cli(e_atk, enemy_name)

    if player_stats["hp"] > 0:
        print(f"\nVictory!")
        player_stats["cowardice"] = 0 
        drop_coins()
        gain_xp(50)
        save_game()
        return "victory"
    else:
        player_stats["hp"] = 0
        player_stats["cowardice"] = 0
        print(f"\n{name} has fallen in battle...")
        print("--- GAME OVER ---")
        save_game()
        return "defeat"

def get_yes_no(prompt):
    while True:
        choice = get_input(prompt).lower()
        if choice in ['yes', 'no']:
            return choice
        print("Please enter 'yes' or 'no'.")

def main_menu():
    global name
    print(f"--- NABI v{VERSION} ---")
    if os.path.exists(SAVE_FILE):
        choice = get_input("Save file found! Load previous game? (yes/no): ").lower()
        if choice == "yes":
            if load_game():
                name = get_input("Confirm your hero's name: ")

    if name.strip() == "":
        name = get_input("What should i call you, Oh great noble warrior? ")
    
    while True:
        print("\n--- MAIN MENU ---")
        print("1. Start Adventure")
        print("2. Quit Game")
        choice = get_input("Select: ")

        if choice == "1":
            player_stats["hp"] = player_stats["max_hp"]
            player_stats["def"] = player_stats["max_def"]
            save_game()
            play_game()
        elif choice == "2":
            sys.exit()

def play_game():
    global dan_patience
    print(f"\nWelcome {name}, to the world of NABI!")

    answer = get_yes_no("Would you like to know more about Nabi? (yes/no): ")
    if answer == "yes":
        print("\nNabi is a world full of mystery and adventure, even I know less about it than you would like to know.")
        print("But here in Nabi, you can be anything you want to be, from a simple farmer to a great warrior!")
        print(f"The choice is yours, Brave warrior {name}!")
    else:
        print("\nIt's not like I wanted to answer!")

    start_answer = get_yes_no("\nWould you like to start your adventure now? (yes/no): ")
    if start_answer == "no":
        print("Oh well, maybe next time!")
        return
    save_game()

    print("Great! Let's begin your adventure! Be warned, it's not going to be easy! Off you go!")

    # ─────────────────────── MAIN WORLD LOOP ───────────────────────
    while True:
        print("\n╔══════════════════════════════╗")
        print("║  You stand at the Crossroads  ║")
        print("╚══════════════════════════════╝")
        print("A dark forest stretches before you, split by three roads.")
        path_answer = get_input("Which path do you take? (Right/Left/Middle/Shop): ").lower()
        save_game()

        # ══════════════════════════════════════════════════════════════
        #  SHOP (Early)
        # ══════════════════════════════════════════════════════════════
        if path_answer == "shop":
            print("A travelling merchant pops out from behind a tree, grinning.")
            print("Merchant: 'Thought you'd sneak past without spending? How RUDE!'")
            open_loot_shop()
            continue

        # ══════════════════════════════════════════════════════════════
        #  RIGHT PATH — DAN'S FIELD  (original, extended)
        # ══════════════════════════════════════════════════════════════
        elif path_answer == "right":
            result = _path_right()
            if result in ("victory_end", "defeat", "menu"):
                return
            continue

        # ══════════════════════════════════════════════════════════════
        #  LEFT PATH — THE HAUNTED RUINS
        # ══════════════════════════════════════════════════════════════
        elif path_answer == "left":
            result = _path_left()
            if result in ("victory_end", "defeat", "menu"):
                return
            continue

        # ══════════════════════════════════════════════════════════════
        #  MIDDLE PATH — THE MOUNTAIN PASS
        # ══════════════════════════════════════════════════════════════
        elif path_answer == "middle":
            result = _path_middle()
            if result in ("victory_end", "defeat", "menu"):
                return
            continue

        else:
            print("Invalid choice. The paths are: Right, Left, Middle, or Shop.")
            continue


# ─────────────────────────────────────────────────────────────────────────────
#  RIGHT PATH  ─  DAN'S FIELD
# ─────────────────────────────────────────────────────────────────────────────
def _path_right():
    global dan_patience
    print("\nYou thread the path and arrive at the field of Dan.")
    print("A stocky man in overalls leans on a fence, chewing a piece of hay, eyeing you suspiciously.")

    dan_answer = get_input("Would you like to go back or speak to Dan? (Back/Speak): ").lower()
    if dan_answer == "back":
        print("Well, you have chosen to go back. Maybe next time you'll be more naive!")
        dan_patience = 0
        return "continue"

    if dan_answer == "speak":
        dan_patience += 1
    else:
        print("Invalid choice. Please enter Back or Speak.")
        return "continue"

    # ── Rage threshold ──
    if dan_patience >= 3:
        print(f"\nDan: THAT'S IT! I told you to leave!")
        print("Dan: You mortals NEVER know when to stop poking your noses in!")
        print("--- Dan's skin begins to tear as giant wings burst from his back! ---")
        print("Dan transforms into a fearsome demon!")
        print("HEHEHE! You're COOKED!")
        result = start_combat("Demon Dan")
        if result == "victory":
            print("\nThe demon crumbles to ash. A glowing orb floats up from the remains...")
            print("You absorb the orb. You feel its dark power reshape something inside you.")
            gain_xp(80)
            open_loot_box()
            # ── After Dan: secret cellar ──
            return _dan_cellar_secret()
        return result  # defeat / menu

    # ── Normal Dan conversation ──
    print("\nDan: And you are?")
    print(f"You: I am called {name}.")
    print(f"Dan: Hm, {name}. Interesting. I'm Dan, the owner of this fine field.")
    print("Dan: What brings you here?")
    print("1. I'm looking for adventure.")
    print("2. Just passing through.")
    print("3. None of your business.")
    print("4. I am lost and need help.")
    reason = get_input("Choose an option (1-4): ")

    if reason == "1":
        print("Dan: An adventure you say? Well I ain't got none now — SCRAM!")
        print("You: How rude!")
        print("Dan: Yeah well, maybe next time you'll think twice before bothering me!")
        print("You walk away, feeling a mix of anger and determination.")
    elif reason == "2":
        print("Dan: Just passing through, huh? Well, safe travels — but take ANOTHER path!")
        print("You nod and continue on your journey.")
    elif reason == "3":
        print("Dan: No need to be rude about it! Mind your own business then.")
        print("You feel a bit embarrassed but decide to leave Dan to his work.")
    elif reason == "4":
        print("Dan: Lost, are you? Well you're in luck — I know these parts well.")
        print("Dan: How about you rest for the night? Head out fresh tomorrow.")
        choice = get_input("1. Accept Dan's offer\n2. Decline and trust your gut\nChoose (1 or 2): ")
        if choice == "1":
            print("You accept. Dan leads you inside a cosy-looking farmhouse.")
            print("The soup smells wonderful. You eat. You sleep. You never wake up.")
            print("(The soup was laced with Nightshade Mushroom.)")
            print("--- GAME OVER ---")
            player_stats["hp"] = 0
            save_game()
            return "defeat"
        elif choice == "2":
            print("You decline. Something in Dan's smile is off — too wide, too still.")
            print("As you back away, Dan drops the facade.")
            print("'Perceptive little rat, aren't you?' he sneers, and begins to transform.")
            print("He is a demon worshipper. He BECOMES the demon.")
            fight_choice = get_yes_no("Do you stand and fight? (yes/no): ")
            if fight_choice == "no":
                player_stats["cowardice"] += 1
                print("You flee into the woods. The demon laughs behind you.")
                print(f"Cowardice increased to {player_stats['cowardice']}.")
                return "continue"
            else:
                print("You draw your weapon. Time to end this.")
                result = start_combat("Demon Dan")
                if result == "victory":
                    gain_xp(80)
                    open_loot_box()
                    return _dan_cellar_secret()
                return result

    if reason in ["1", "2", "3"]:
        if dan_patience == 1:
            print("\nDan: I don't have time for this. Leave before I lose my temper.")
        elif dan_patience == 2:
            print("\nDan: (Vein throbbing) I'm WARNING you… leave. NOW.")
            print("You walk away, but Dan is watching you closely…")

    return "continue"


def _dan_cellar_secret():
    """Secret area unlocked after defeating Demon Dan."""
    print("\n" + "═"*50)
    print("With Dan defeated, you notice the farmhouse door is ajar.")
    print("A strange blue light flickers from below — a cellar.")
    explore = get_yes_no("Do you explore the cellar? (yes/no): ")
    if explore == "no":
        print("You leave the farm behind. Some doors are best left unopened.")
        return "continue"

    print("\nYou descend crude stone steps. The air smells of sulphur and old paper.")
    print("The cellar is lined with ritual symbols, caged animals, and one very surprised imp.")
    print("\nImp: 'OI! Who killed my master?! That was MY master, you hear me?!'")
    print("The imp looks furious — then suddenly looks calculating.")
    print("Imp: '…Actually, if you're strong enough to kill a Greater Demon…'")
    print("Imp: 'How'd you like a guide? I know every secret in Nabi.'")

    imp_choice = get_input("1. Accept the imp as your guide\n2. Attack it\n3. Ignore it and loot the cellar\nChoose (1-3): ")

    if imp_choice == "1":
        print("\nThe imp — who introduces itself as GRUB — perches on your shoulder.")
        print("Grub: 'Call me Grub. Don't call me late for dinner. Let's GO.'")
        print("You gain a new companion. Grub whispers secrets of the land into your ear.")
        gain_xp(30)
        player_stats["atk"] += 3
        print("(Grub's tips improve your combat instincts! ATK permanently +3)")
        # Grub opens the hidden vault
        print("\nGrub: 'Oh, and the master kept his REAL loot behind the bookcase.'")
        print("Grub yanks a candlestick. A section of wall grinds open.")
        print("Inside: a chest full of gold and a peculiar glowing stone.")
        open_loot_box()
        drop_coins()
        return _enter_demon_tower()

    elif imp_choice == "2":
        print("\nThe imp SHRIEKS and transforms into a swirling shadow beast!")
        result = start_combat("Shadow Imp")
        if result == "victory":
            gain_xp(40)
            drop_coins()
            print("The imp dissolves into smoke. On the floor: a small key carved from bone.")
            print("(Bone Key obtained — it might open something later.)")
            player_stats.setdefault("bone_key", True)
        return result if result in ("defeat", "menu") else "continue"

    else:  # loot and ignore
        print("\nYou ignore the imp and rifle through the shelves.")
        print("Grub watches you with beady, offended eyes.")
        open_loot_box(is_cursed=random.random() < 0.4)
        drop_coins()
        print("\nGrub: 'Fine. Be that way. Good luck dying out there. Alone.'")
        print("The imp vanishes in a puff of sulphurous smoke.")
        return "continue"


def _enter_demon_tower():
    """Late-game area: The Demon Tower, accessed after Dan questline."""
    print("\n" + "═"*50)
    print("Grub leads you through the forest to a black iron tower that wasn't there before.")
    print("Grub: 'Dan answered to someone. Or something. Up there.'")
    print("Grub: 'I'd go in myself but… I have a prior engagement. With not dying.'")

    enter = get_yes_no("Do you enter the Demon Tower? (yes/no): ")
    if enter == "no":
        player_stats["cowardice"] += 1
        print(f"You back away. Cowardice +1 ({player_stats['cowardice']}).")
        print("Grub sighs dramatically. 'Bold choice. Incredibly bold.'")
        return "continue"

    print("\n--- FLOOR 1: THE GAUNTLET ---")
    print("Skeletal soldiers line the corridor. They turn their hollow eyes toward you.")
    result = start_combat("Skeleton Captain")
    if result in ("defeat", "menu"):
        return result
    gain_xp(50)
    open_loot_box()

    print("\n--- FLOOR 2: THE LIBRARY OF LIES ---")
    print("Books fly off the shelves and form a hulking golem of compressed paper and ink.")
    print("Words from a thousand stories tear loose and swirl around it like a hurricane.")
    result = start_combat("Lore Golem")
    if result in ("defeat", "menu"):
        return result
    gain_xp(60)
    drop_coins()

    print("\n--- FLOOR 3: THE THRONE ROOM ---")
    print("At the top sits a figure in armour so black it seems to eat the light.")
    print("It speaks without moving its mouth — the voice comes from everywhere at once.")
    print("???: 'So. The one who slew my herald arrives at last.'")
    print("???: 'I am MALACHAR. Archdemon of Nabi. And you… are VERY lost.'")
    print("\nMalachar rises. The tower shudders. This is it.")

    print("\n1. Fight Malachar")
    print("2. Try to negotiate")
    print("3. Run (you coward)")
    final_choice = get_input("Choose (1-3): ")

    if final_choice == "3":
        player_stats["cowardice"] += 3
        print("You bolt down the stairs. Malachar laughs, a sound like grinding continents.")
        print(f"Cowardice +3 ({player_stats['cowardice']}). The tower collapses behind you.")
        print("You survive. Barely. But Malachar is still out there.")
        return "continue"

    elif final_choice == "2":
        print("\nMalachar pauses. He was NOT expecting that.")
        print("Malachar: '…Negotiate. A mortal wishes to NEGOTIATE with me.'")
        roll = random.randint(1, 3)
        if roll == 1:
            print("Malachar: 'I admire the audacity. Very well. A game of riddles.'")
            result = _riddle_challenge()
            if result == "won":
                print("Malachar: '…Clever wretch. I'll let you leave. This time.'")
                print("He snaps his fingers. You find yourself outside the tower.")
                gain_xp(100)
                open_loot_box()
                print("\n--- YOU SURVIVED MALACHAR BY WIT ALONE ---")
                return "victory_end"
            else:
                print("Malachar: 'Wrong. I grow bored of you.'")
                result = start_combat("Malachar the Archdemon")
                if result == "victory":
                    return _malachar_victory()
                return result
        else:
            print("Malachar: 'Negotiate? There is nothing you have that I want.'")
            print("He raises one finger. You're blasted across the room.")
            apply_damage_to_player_cli(30, "Malachar")
            if player_stats["hp"] <= 0:
                print("--- GAME OVER ---")
                save_game()
                return "defeat"
            print("You scramble to your feet. Diplomacy has failed. Time for Plan B.")
            result = start_combat("Malachar the Archdemon")
            if result == "victory":
                return _malachar_victory()
            return result

    else:  # fight
        print("\nYou charge. Malachar smiles for the first time.")
        print("Malachar: 'Good. I was beginning to worry you'd bore me.'")
        result = start_combat("Malachar the Archdemon")
        if result == "victory":
            return _malachar_victory()
        return result


def _riddle_challenge():
    """Mini-game: answer 3 riddles to outsmart Malachar."""
    riddles = [
        ("I have cities but no houses live there, forests but no trees grow, and water but no fish swim. What am I?", "map"),
        ("The more you take, the more you leave behind. What am I?", "footsteps"),
        ("I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "echo"),
    ]
    random.shuffle(riddles)
    score = 0
    print("\nMalachar: 'Three riddles. Answer them all and I'll let you walk free.'")
    for i, (question, answer) in enumerate(riddles[:3], 1):
        print(f"\nRiddle {i}: {question}")
        guess = get_input("Your answer: ").lower().strip()
        if guess == answer:
            print("Malachar: '…Correct.' (He looks mildly annoyed.)")
            score += 1
        else:
            print(f"Malachar: 'WRONG. The answer was: {answer}.'")
    return "won" if score >= 2 else "lost"


def _malachar_victory():
    print("\n" + "═"*50)
    print("MALACHAR DEFEATED!")
    print("The tower shatters. The sky cracks open, revealing stars that were never there before.")
    print("Malachar dissolves, his voice fading: '…You… haven't seen… the last…'")
    print("Grub appears from nowhere. 'I totally helped. You're welcome.'")
    gain_xp(150)
    open_loot_box()
    drop_coins()
    print("\n══════════════════════════════════════")
    print(f"  {name} HAS SAVED NABI — FOR NOW.")
    print("══════════════════════════════════════")
    print("Epilogue: Grub opens a kebab stand. It becomes very popular.")
    save_game()
    return "victory_end"


# ─────────────────────────────────────────────────────────────────────────────
#  LEFT PATH  ─  THE HAUNTED RUINS
# ─────────────────────────────────────────────────────────────────────────────
def _path_left():
    print("\nYou push through thick undergrowth. The forest grows darker and colder.")
    print("After an hour of walking, the trees thin to reveal — ruins.")
    print("Stone arches, shattered columns, and a broken fountain filled with black water.")
    print("Something carved above the gate reads: ASHENVEIL — CITY OF THE FORGOTTEN.")

    enter = get_yes_no("Do you enter the ruins? (yes/no): ")
    if enter == "no":
        player_stats["cowardice"] += 1
        print("You step back. The ruins seem to exhale in disappointment.")
        print(f"Cowardice +1 ({player_stats['cowardice']}).")
        return "continue"

    print("\nYou step inside. Your footsteps echo strangely — as if someone is walking with you.")
    print("Three buildings are still partially standing:")
    print("  A — The Old Temple")
    print("  B — The Guard Barracks")
    print("  C — The Lord's Mansion")

    ruin_choice = get_input("Which do you explore first? (A/B/C): ").upper()

    if ruin_choice == "A":
        return _ruins_temple()
    elif ruin_choice == "B":
        return _ruins_barracks()
    elif ruin_choice == "C":
        return _ruins_mansion()
    else:
        print("The ruins offer only silence in response to your indecision.")
        return "continue"


def _ruins_temple():
    print("\n── THE OLD TEMPLE ──")
    print("Inside, rows of stone pews face an altar. On the altar sits a cracked mirror.")
    print("As you approach, your reflection MOVES ON ITS OWN.")
    print("Reflection: 'I've been waiting for you, original. I'm so tired of this place.'")

    mirror_choice = get_input("1. Speak to the reflection\n2. Smash the mirror\n3. Leave immediately\nChoose (1-3): ")

    if mirror_choice == "1":
        print("\nYou: 'Who are you?'")
        print(f"Reflection: 'I am you. A version that stepped left instead of right, ten years ago.'")
        print(f"Reflection: 'I know things you don't. About Nabi. About Malachar. About what's buried under this city.'")
        print("It presses its palm to the glass. 'Swap with me. Just for a moment.'")
        swap = get_yes_no("Do you press your palm to the mirror? (yes/no): ")
        if swap == "yes":
            print("\nThe cold glass pulls you in. For one terrifying second you ARE the reflection.")
            print("You see a memory — not yours. A child burying a box under the mansion's floor.")
            print("Then you snap back, gasping.")
            print("Reflection: 'Now you know. Go find it.'")
            print("(You received the VISION. Something is buried under the Lord's Mansion.)")
            player_stats.setdefault("mirror_vision", True)
            gain_xp(25)
        else:
            print("You step back. The reflection looks sad, then blank, then it's just you again.")
    elif mirror_choice == "2":
        print("\nYou grab a stone from the floor and HURL it at the mirror.")
        print("It shatters with a sound like a scream. The shards rise into the air…")
        print("And form a MIRROR WRAITH — your reflection, now furious and free.")
        result = start_combat("Mirror Wraith")
        if result == "victory":
            gain_xp(50)
            print("The wraith dissolves. Among the glass shards: a gemstone that glows faintly.")
            player_stats["atk"] += 5
            print("You pocket it. It sharpens your instincts. ATK +5.")
        elif result in ("defeat", "menu"):
            return result
    else:
        print("You back out of the temple. Some things are better left alone.")

    return "continue"


def _ruins_barracks():
    print("\n── THE GUARD BARRACKS ──")
    print("Rusted bunk beds. Rotted equipment. And one skeleton still seated at a table,")
    print("an unfinished game of cards laid out before it.")
    print("\nAs you enter, the skeleton's skull turns to face you. Its jaw opens.")
    print("Skeleton: 'Finally. I've been waiting CENTURIES for someone to finish this game.'")

    play = get_yes_no("Do you sit down and play cards with the skeleton? (yes/no): ")
    if play == "no":
        print("The skeleton slumps back. 'Story of my afterlife,' it mutters.")
        return "continue"

    print("\n--- BONE POKER ---")
    print("The rules are simple: highest draw wins. Best of three.")
    print("(The skeleton is unnerving but weirdly charming.)")

    player_wins = 0
    skeleton_wins = 0
    for round_num in range(1, 4):
        input(f"\nPress Enter to draw for Round {round_num}...")
        player_card = random.randint(1, 13)
        skeleton_card = random.randint(1, 13)
        print(f"You drew: {player_card} | Skeleton drew: {skeleton_card}")
        if player_card > skeleton_card:
            print("You win this round!")
            player_wins += 1
        elif skeleton_card > player_card:
            print("The skeleton rattles victoriously.")
            skeleton_wins += 1
        else:
            print("A tie! Nobody wins this round.")

    if player_wins > skeleton_wins:
        print("\nSkeleton: 'HAH! I lose again! But wait — I OWE you a prize.'")
        print("The skeleton reaches into its ribcage and produces a glowing potion.")
        print("Skeleton: 'This will serve you well, warrior. Now GET OUT, before I cry.'")
        player_stats["inventory"]["hp_potions"] += 2
        player_stats["inventory"]["dp_potions"] += 2
        gain_xp(30)
        print("You gained 2 HP Potions and 2 Shield Potions!")
    elif skeleton_wins > player_wins:
        print("\nSkeleton: 'HA! I WIN! After 400 years — I FINALLY WIN!'")
        print("The skeleton explodes into a harmless shower of confetti-like bone dust.")
        print("On the table: a coin purse it left behind in its excitement.")
        drop_coins()
    else:
        print("\nSkeleton: 'A draw. Well. That's... something.'")
        print("You both sit in companionable silence for a moment.")
        print("Skeleton: 'Come back sometime. I'll have snacks. Possibly.')") 
        gain_xp(15)

    # Hidden trap in the barracks
    print("\nAs you prepare to leave, you notice a trapdoor under one of the beds.")
    trap_choice = get_yes_no("Do you open the trapdoor? (yes/no): ")
    if trap_choice == "yes":
        roll = random.randint(1, 3)
        if roll == 1:
            print("A GHOUL lunges out at you!")
            result = start_combat("Barracks Ghoul")
            if result == "victory":
                gain_xp(40)
                open_loot_box(is_cursed=False)
            elif result in ("defeat", "menu"):
                return result
        elif roll == 2:
            print("Inside: a dusty chest full of old coins and a dented shield.")
            drop_coins()
            player_stats["max_def"] += 3
            player_stats["def"] = player_stats["max_def"]
            print(f"You equip the old shield. Max Shield +3 → {player_stats['max_def']}")
        else:
            print("Inside: absolute darkness and the smell of old biscuits. Nothing else.")
            print("You close the trapdoor respectfully.")

    return "continue"


def _ruins_mansion():
    print("\n── THE LORD'S MANSION ──")
    print("The grandest building in Ashenveil, now hollow and vine-choked.")
    print("Portraits on the wall show a nobleman and his family — but in every painting,")
    print("the nobleman's face has been scratched out.")

    print("\nYou explore the ground floor. A dining room. A study. A locked door.")
    print("The locked door is cold to the touch. Ice forms around the keyhole.")

    has_vision = player_stats.get("mirror_vision", False)
    if has_vision:
        print("\n(Your mirror vision PULSES. Something is below.)")
        print("You pry up the floorboards beneath the dining table. There it is — a box.")
        print("Inside the box: a LORDSHIP SIGNET RING and a letter.")
        print("\nLetter: 'To whoever finds this — the Lord made a pact with a demon named Dan.'")
        print("'He gave the city's souls in exchange for wealth. The demon collected. We all died.'")
        print("'The ring commands the mansion's guardian. Use it wisely — or don't. — E.A.'")
        player_stats.setdefault("signet_ring", True)
        player_stats["atk"] += 7
        print("\nYou pocket the ring. It hums with ancient authority. ATK +7.")
        gain_xp(40)

    action = get_input("\nWhat do you do?\n1. Try to open the cold locked door\n2. Leave the mansion\nChoose (1-2): ")
    if action == "2":
        print("You leave the mansion. The portraits seem to watch you go.")
        return "continue"

    # The locked door
    print("\nYou force the cold door open. Steps lead down to a crypt.")
    print("In the centre kneels a stone figure — a REVENANT KNIGHT, perfectly preserved.")
    print("Its armour is carved with the same signet pattern as the ring (if you have it).")

    if player_stats.get("signet_ring", False):
        print("\nYou hold up the signet ring. The Revenant Knight's eyes open — they glow gold.")
        print("Revenant: 'My lord's seal. The pact is broken. I am… free.'")
        print("Revenant: 'You have my gratitude, and my blade, warrior.'")
        print("The knight presses a massive sword into your hands and dissolves peacefully.")
        player_stats["atk"] = max(player_stats["atk"], 60)
        print(f"REVENANT'S BLADE equipped! ATK set to {player_stats['atk']} (if higher).")
        gain_xp(70)
        print("A chest behind the throne opens on its own. Final reward from a freed soul.")
        open_loot_box()
    else:
        print("\nThe Revenant's eyes snap open. Red. Furious.")
        print("Revenant: 'INTRUDER. YOU ARE NOT MY LORD.'")
        print("It rises, drawing a greatsword that trails shadow-fire.")
        result = start_combat("Revenant Knight")
        if result == "victory":
            gain_xp(80)
            print("The knight shatters. Its armour crumbles to dust — except one piece.")
            print("A pauldron inscribed with a crest. You add it to your own armour.")
            player_stats["max_def"] += 10
            player_stats["def"] = player_stats["max_def"]
            print(f"MAX SHIELD +10 → {player_stats['max_def']}")
            open_loot_box()
        elif result in ("defeat", "menu"):
            return result

    return "continue"


# ─────────────────────────────────────────────────────────────────────────────
#  MIDDLE PATH  ─  THE MOUNTAIN PASS
# ─────────────────────────────────────────────────────────────────────────────
def _path_middle():
    print("\nThe middle path climbs steeply. The trees thin to rocky scrub.")
    print("After an hour, you emerge onto a mountain pass swept by icy wind.")
    print("Below one side: the forest. Below the other: a vast, shimmering valley.")
    print("Above you: a cave mouth. Before it sits an old woman warming her hands over nothing.")
    print("Old Woman: 'Took you long enough. Sit.'")

    old_choice = get_input("1. Sit with the old woman\n2. Enter the cave directly\n3. Descend to the valley\nChoose (1-3): ")

    if old_choice == "1":
        return _mountain_oracle()
    elif old_choice == "2":
        return _mountain_cave()
    elif old_choice == "3":
        return _valley_descent()
    else:
        print("The wind swallows your indecision. The old woman doesn't look up.")
        return "continue"


def _mountain_oracle():
    print("\nYou sit across from the old woman. Up close, her eyes are solid silver.")
    print("Oracle: 'I am called Ysel. I see the threads of what will be.'")
    print(f"Oracle: 'I see you, {name}. You carry more questions than answers.'")
    print("Oracle: 'Ask. One question. I will answer truly.'")

    question = get_input("What do you ask?\n1. What is my destiny?\n2. How do I defeat Malachar?\n3. What is Dan hiding?\n4. Will I survive this?\nChoose (1-4): ")

    if question == "1":
        print(f"\nYsel: 'Your destiny, {name}, is not fixed. But I see a throne of ash.'")
        print("Ysel: 'Whether you sit upon it as ruler or sacrifice — that depends on your next choice.'")
        print("She gestures vaguely at everything.")
        gain_xp(20)
    elif question == "2":
        print("\nYsel: 'Malachar fears only one thing: being forgotten. He feeds on acknowledgement.'")
        print("Ysel: 'If you can make him feel small — truly small — his power wavers.'")
        print("Ysel: 'Also, a good sword helps.'")
        print("(ORACLE TIP acquired: In the fight with Malachar, consider negotiating!)")
        gain_xp(20)
    elif question == "3":
        print("\nYsel: 'Dan hides a tower. And in the tower, his master. And the master…'")
        print("She shivers, which is unsettling from someone who seems otherwise undauntable.")
        print("Ysel: '…The master hides everything.'")
        gain_xp(20)
    elif question == "4":
        print("\nYsel is quiet for a long time.")
        print("Ysel: 'Yes. But not without cost.'")
        print("She says nothing more on the subject.")
        gain_xp(20)
    else:
        print("Ysel: 'That was not one of the choices. I'll answer anyway.'")
        print("Ysel: 'Yes. Definitely yes. Now go.'")
        gain_xp(10)

    print("\nYsel reaches into her shawl and presses something cold into your hand.")
    print("It's a small carved stone in the shape of a flame.")
    print("Ysel: 'For when things get dark. And they will get dark.'")
    player_stats["inventory"]["hp_potions"] += 1
    player_stats["max_hp"] += 10
    player_stats["hp"] = min(player_stats["hp"] + 10, player_stats["max_hp"])
    print(f"(Stone of Ysel: +1 HP Potion, Max HP +10 → {player_stats['max_hp']})")

    print("\nYsel: 'The cave behind me — go. There is something there that was waiting before you were born.'")
    return _mountain_cave()


def _mountain_cave():
    print("\n── THE CAVE ──")
    print("Inside, the cave narrows to a tunnel that glows faintly blue.")
    print("The glow comes from CRYSTALS — enormous, humming shards growing from the walls.")
    print("And at the end of the tunnel: a dragon. Small, as dragons go, curled asleep.")
    print("It is the size of a large horse. Its scales shimmer between gold and black.")

    print("\n1. Try to sneak past the dragon")
    print("2. Wake the dragon and talk")
    print("3. Attack the sleeping dragon")
    print("4. Leave the cave")
    dragon_choice = get_input("Choose (1-4): ")

    if dragon_choice == "1":
        roll = random.randint(1, 3)
        if roll == 1:
            print("\nYou creep silently through the crystals. You almost make it.")
            print("Almost. Your boot catches a crystal shard. It rings like a bell.")
            print("The dragon's eye opens. It regards you without blinking.")
            print("Dragon: '...You have exactly three seconds to explain yourself.'")
            result = _dragon_conversation()
            return result
        else:
            print("\nYou move like a ghost. The dragon's breathing never changes.")
            print("Behind it: a ledge. On the ledge: a chest covered in crystal growth.")
            print("You prise it open. Inside: a magnificent gem that hums with stored power.")
            player_stats["atk"] += 10
            player_stats["max_hp"] += 15
            player_stats["hp"] = player_stats["max_hp"]
            gain_xp(50)
            print(f"CRYSTAL HEART obtained! ATK +10 → {player_stats['atk']}, Max HP +15 → {player_stats['max_hp']}")
            print("You sneak back out. The dragon never knew.")
            return "continue"

    elif dragon_choice == "2":
        print("\nYou clear your throat loudly. The dragon's eye snaps open.")
        print("Dragon: 'You DARE wake—' It stops. Tilts its head. 'Hm. You're not screaming.'")
        print("Dragon: 'They usually scream. You're either very brave or very stupid.'")
        return _dragon_conversation()

    elif dragon_choice == "3":
        print("\nYou raise your weapon and STRIKE — a solid hit on the dragon's flank!")
        print("The dragon wakes with a roar that shakes the entire mountain.")
        print("Dragon: 'YOU JUST— DO YOU KNOW HOW LONG I WAS ASLEEP?!'")
        print("Dragon: 'I JUST WANT TO REST AND MORTALS KEEP—'")
        print("It's not even fighting yet. It's just furious. But it will be fighting very soon.")
        result = start_combat("Furious Cave Dragon")
        if result == "victory":
            print("\nThe dragon slumps. Its final breath scorches the ceiling.")
            print("Dragon: '…Well. At least I'll sleep forever now. Finally.'")
            gain_xp(120)
            open_loot_box()
            drop_coins()
            print("\nThe dragon's hoard is beneath it — modest by dragon standards, spectacular by yours.")
            open_loot_box()
        return result if result in ("defeat", "menu") else "continue"

    else:
        print("You retreat from the cave. Some sleeping things should stay that way.")
        return "continue"


def _dragon_conversation():
    print("\nDragon: 'I am VETH. I have slept in this mountain for three hundred years.'")
    print("Veth: 'I am, frankly, very grumpy about being awake.'")
    print("Veth: 'State your purpose or I will eat you. It's not a threat — I'm just hungry.'")

    purpose = get_input("1. I seek power to fight a great evil\n2. I was just exploring\n3. I came to challenge you\n4. ...Are you okay?\nChoose (1-4): ")

    if purpose == "1":
        print("\nVeth stares at you for a long time.")
        print("Veth: 'Malachar. You're talking about Malachar.'")
        print("Veth: 'He's the reason I fled HERE to sleep. I wanted nothing to do with it.'")
        print("Veth: '...But if someone's finally going after him...'")
        print("Veth breathes a small plume of flame onto your weapon. It IGNITES with golden fire.")
        player_stats["atk"] += 15
        gain_xp(60)
        print(f"DRAGON'S BLESSING: Your weapon burns with dragonfire! ATK +15 → {player_stats['atk']}")
        print("Veth: 'Don't die. It would make my contribution pointless.'")
        print("Veth curls back up. 'Now. I am going back to sleep. Goodbye.'")
    elif purpose == "2":
        print("\nVeth: 'Just exploring. Right. In a DRAGON'S CAVE.'")
        print("Veth: '...You know what, I respect it. Most people have an agenda.'")
        print("Veth regards you, then nudges something toward you with one claw.")
        print("It's a scale — shed, gleaming, golden-black.")
        print("Veth: 'Dragon scale. Better than any armour you'll find down there.'")
        player_stats["max_def"] += 8
        player_stats["def"] = player_stats["max_def"]
        gain_xp(30)
        print(f"DRAGON SCALE equipped! Max Shield +8 → {player_stats['max_def']}")
    elif purpose == "3":
        print("\nVeth: 'Challenge me. CHALLENGE me. Delightful. Absolutely unhinged.'")
        print("Veth: 'Very well. But I warn you — I fight at half-power even when annoyed.'")
        result = start_combat("Veth the Cave Dragon (Holding Back)")
        if result == "victory":
            gain_xp(100)
            print("\nVeth: '...I am GENUINELY impressed. And humiliated. Mostly impressed.'")
            print("Veth bows its head and offers its hoard freely.")
            open_loot_box()
            open_loot_box()
            drop_coins()
            print("Veth: 'You've earned the right to bother me whenever you like. Which I will regret saying.'")
            player_stats["atk"] += 8
            print(f"WARRIOR'S RESPECT: ATK +8 → {player_stats['atk']}")
        return result if result in ("defeat", "menu") else "continue"
    elif purpose == "4":
        print("\nVeth goes very still.")
        print("Veth: '...'")
        print("Veth: 'Nobody has asked me that in three hundred years.'")
        print("There is a long silence. You think you see a single tear evaporate on the dragon's cheek.")
        print("Veth: 'I am... fine. I am just very tired. And the world is very loud.'")
        print("Veth: 'Here. Take this. I don't need it. I have the whole mountain.'")
        player_stats["inventory"]["hp_potions"] += 3
        player_stats["max_hp"] += 20
        player_stats["hp"] = player_stats["max_hp"]
        gain_xp(50)
        print(f"VETH'S GRATITUDE: +3 HP Potions, Max HP +20 → {player_stats['max_hp']}")
        print("Veth: 'You are strange, mortal. I hope the world doesn't grind that out of you.'")
    else:
        print("Veth: 'That was not a valid option. I'm eating you now.'")
        result = start_combat("Veth the Cave Dragon (Offended)")
        return result if result in ("defeat", "menu") else "continue"

    return "continue"


def _valley_descent():
    print("\n── THE SHIMMERING VALLEY ──")
    print("You descend the far side of the mountain into a valley unlike anything above.")
    print("The air is warm and sweet. Flowers you don't recognise bloom in spirals.")
    print("In the centre of the valley: a village. Small. Peaceful.")
    print("But the village is surrounded by a ring of STONE, and outside the stone:")
    print("hundreds of shambling undead, walking in slow circles. Waiting.")

    print("\nA child peeks over the stone wall at you.")
    print("Child: 'Are you a hero? We sent ravens for a hero three months ago.'")
    print("Child: 'You're late. But we're not picky.'")

    help_choice = get_yes_no("Do you help the village? (yes/no): ")
    if help_choice == "no":
        player_stats["cowardice"] += 2
        print(f"You turn away. The child's face falls. Cowardice +2 ({player_stats['cowardice']}).")
        print("You will remember that face.")
        return "continue"

    print("\nChild: 'The Elder will want to meet you!'")
    print("\n── THE VILLAGE OF EVENMERE ──")
    print("Inside the wall: a community doing its best. Gardens on rooftops. People looking tired but determined.")
    print("Elder Rho greets you — a broad-shouldered woman with a patchwork cloak and no-nonsense eyes.")
    print("Rho: 'The dead appeared eight days ago. They don't attack — just circle.'")
    print("Rho: 'They're waiting for something. Or someone. We found THIS nailed to the gate.'")
    print("She hands you a black iron plaque: 'DELIVER THE SOULSTONE OR THE SIEGE NEVER ENDS — M'")
    print("\nRho: 'We don't HAVE a soulstone. We don't know what it is.'")

    approach = get_input("1. Fight through the undead horde\n2. Search the village for clues\n3. Confront whoever left the message\nChoose (1-3): ")

    if approach == "1":
        print("\nYou vault the wall and charge into the undead.")
        print("They are slow but endless. Waves break against you.")
        result = start_combat("Undead Horde (First Wave)")
        if result in ("defeat", "menu"):
            return result
        gain_xp(60)
        result = start_combat("Undead Horde (Second Wave)")
        if result in ("defeat", "menu"):
            return result
        gain_xp(60)
        print("\nYou've fought them back — but more are rising from the treeline.")
        print("Rho: 'We can't win this way. We need to find the SOURCE.'")
        return _valley_find_necromancer()

    elif approach == "2":
        print("\nYou search the village. In the old chapel basement:")
        print("A glowing stone in a box. A SOULSTONE. It pulses with captured light.")
        print("Rho: 'We had it all along? Old Mayor Yenn must have hidden it before he died.'")
        print("\n1. Give the soulstone to whoever left the message")
        print("2. Destroy the soulstone")
        print("3. Use the soulstone yourself")
        stone_choice = get_input("Choose (1-3): ")
        if stone_choice == "1":
            return _valley_negotiate_necromancer()
        elif stone_choice == "2":
            print("\nYou smash the soulstone against the chapel floor.")
            print("The light SCREAMS outward. Outside: the undead collapse like puppets with cut strings.")
            print("The siege is over. But the stone's energy had to go somewhere.")
            print("It went into you.")
            player_stats["max_hp"] += 30
            player_stats["hp"] = player_stats["max_hp"]
            player_stats["atk"] += 10
            gain_xp(80)
            print(f"SOULSTONE ABSORBED: Max HP +30 → {player_stats['max_hp']}, ATK +10 → {player_stats['atk']}")
            print("\nRho: 'You absolute maniac. Thank you.'")
            print("The village throws a feast in your honour. It lasts until dawn.")
            drop_coins()
            drop_coins()
            return "continue"
        else:
            print("\nYou hold the soulstone. It hums and seems to — choose you.")
            player_stats["max_hp"] += 20
            player_stats["hp"] = player_stats["max_hp"]
            gain_xp(50)
            print(f"SOULSTONE BONDED: Max HP +20 → {player_stats['max_hp']}")
            print("The undead don't disperse. But now they ignore YOU.")
            print("The village is still trapped. You leave feeling complicated about this.")
            return "continue"

    else:
        return _valley_find_necromancer()


def _valley_find_necromancer():
    print("\nYou track the undead to their source — a hilltop altar at the valley's edge.")
    return _valley_negotiate_necromancer()


def _valley_negotiate_necromancer():
    print("\nAt the hilltop: a cloaked figure seated cross-legged in the dirt.")
    print("They look up. They are young — younger than expected. Exhausted.")
    print("Necromancer: 'You're here about the village.'")
    print("Necromancer: 'I'm not a villain. I'm… desperate. The soulstone holds my sister's soul.'")
    print("Necromancer: 'She died. I captured her soul before it passed. But the stone is FAILING.'")
    print("Necromancer: 'I need the original stone — the one hidden in the village — to stabilise it.'")

    print("\n1. Help them — find or give the soulstone")
    print("2. This is still wrong — fight the necromancer")
    print("3. Ask more questions")
    nec_choice = get_input("Choose (1-3): ")

    if nec_choice == "1":
        print("\nYou explain the situation. The necromancer listens. Nods.")
        print("Necromancer: 'The undead will disperse the moment I have what I need.'")
        print("Necromancer: 'I'll let her soul pass on properly. She deserves peace.'")
        print("They perform the ritual. The undead collapse. The sister's spirit rises —")
        print("— and smiles, once, before dissolving into golden light.")
        print("Necromancer: 'Thank you. I owe you a debt.'")
        print("They teach you one of their techniques.")
        gain_xp(80)
        player_stats["inventory"]["hp_potions"] += 2
        player_stats["max_def"] += 5
        player_stats["def"] = player_stats["max_def"]
        print(f"NECROMANCER'S THANKS: +2 HP Potions, Max Shield +5 → {player_stats['max_def']}")
        print("\nRho and the village celebrate. You have made two strangers' grief a little smaller.")
        drop_coins()

    elif nec_choice == "2":
        print("\nYou draw your weapon. The necromancer sighs.")
        print("Necromancer: 'Of course. Because nothing can ever be simple.'")
        print("They rise. The undead mass behind them.")
        result = start_combat("Desperate Necromancer")
        if result == "victory":
            gain_xp(70)
            print("\nThe necromancer falls. The undead collapse.")
            print("In the necromancer's bag: a cracked orb that still glows faintly.")
            print("A second soul, trying to hold itself together.")
            print("You don't know what to do with it. You carry it anyway.")
            open_loot_box(is_cursed=True)
        elif result in ("defeat", "menu"):
            return result

    else:
        print("\nYou ask about Malachar, about Nabi, about the soulstone's origin.")
        print("Necromancer: 'Malachar created the first soulstones as TRAPS. To collect souls.'")
        print("Necromancer: 'I repurposed the technique. It shouldn't have worked. But grief makes you creative.'")
        gain_xp(25)
        print("\nArmed with this knowledge, how do you proceed?")
        return _valley_negotiate_necromancer()

    save_game()
    return "continue"

SAVE_FILE = "save_data.json"
name = " "
dan_patience = 0

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
    "combo": 0,
    "inventory": {"hp_potions": 2, "dp_potions": 2}
}

# DP System constants
COMBO_MAX = 100
COMBO_PER_ATTACK = 25
POWER_STRIKE_DP_COST = 10
POWER_STRIKE_MULTIPLIER = 2.5
VULNERABILITY_BONUS = 0.5
PARRY_DP_RESTORE = 5
PARRY_COUNTER_MULTIPLIER = 0.5
player_stats = copy.deepcopy(DEFAULT_PLAYER_STATS)

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

            # Recover from death: if HP is 0, restore to full
            if player_stats["hp"] <= 0:
                player_stats["hp"] = player_stats["max_hp"]
                player_stats["def"] = player_stats["max_def"]
                print(">> You were revived! HP and Armor fully restored.")

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

def open_loot_shop():
    while True:
        print(f"\n---  NABI TRADING POST  ---")
        print(f"Your Wallet: {player_stats['coins']} / 500 Coins")
        print(f"Your Stats: HP: {player_stats['hp']}/{player_stats['max_hp']} | Shield: {player_stats['def']}/{player_stats['max_def']} | ATK: {player_stats['atk']}")
        print("-" * 40)
        print("1. [RESTORE] Full HP (20c)")
        print("2. [REPAIR] Full Shield (20c)")
        print("3. [BUFF] Permanent ATK +5 (100c)")
        print("4. [BUFF] Permanent Max Shield +5 (100c)")
        print("5. [BUY] HP Potion (50c)")
        print("6. [BUY] Shield Potion (50c)")
        print("7. [UPGRADE] Max HP +20 (150c)")
        print("8. [UPGRADE] Max Shield +10 (120c)")
        print("9. [EXIT] Leave Shop")
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
                print(">> Success: Shield fully repaired!")
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
                print(f">> Success: Max Shield is now {player_stats['max_def']}.")
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
                print(f">> Success: Shield Potion added! Total: {player_stats['inventory']['dp_potions']}")
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
            if player_stats["coins"] >= 120:
                player_stats["max_def"] += 10
                player_stats["def"] = player_stats["max_def"]
                player_stats["coins"] -= 120
                print(f">> Success: Max Shield is now {player_stats['max_def']}.")
            else:
                print(">> Error: Not enough coins!")

        elif choice == "9":
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
            print(f"Shield Upgrade! Max Shield is now {player_stats['max_def']}.")
        elif roll == 4:
            if player_stats["cowardice"] > 0:
                player_stats["cowardice"] = 0
                print("Holy Relic! The weight of your cowardice has been lifted. The curse is gone!")
            else:
                bonus = 100
                player_stats["coins"] = min(500, player_stats["coins"] + bonus)
                print(f"Treasure! Gained {bonus} coins! Total: {player_stats['coins']}/500")


def apply_damage_to_player_cli(raw_damage, source_name="Enemy"):
    """Shield HP: DP absorbs first, overflow to HP. Vulnerability at 0 DP."""
    if player_stats["def"] <= 0:
        vuln_dmg = int(raw_damage * (1 + VULNERABILITY_BONUS))
        player_stats["hp"] -= vuln_dmg
        print(f">> VULNERABLE! {source_name} deals {vuln_dmg} ({raw_damage}+{vuln_dmg - raw_damage})!")
        return vuln_dmg
    if raw_damage <= player_stats["def"]:
        player_stats["def"] -= raw_damage
        print(f">> Shield absorbs {raw_damage}! (DP: {player_stats['def']}/{player_stats['max_def']})")
        return 0
    overflow = raw_damage - player_stats["def"]
    print(f">> Shield broken! {player_stats['def']} absorbed, {overflow} HP lost!")
    player_stats["def"] = 0
    player_stats["hp"] -= overflow
    return overflow

def apply_parry_cli(enemy_atk, enemy_max_atk, source_name="Enemy"):
    """Parry: restores DP, blocks through shield. Counter on strong attacks."""
    dp_restored = min(PARRY_DP_RESTORE, player_stats["max_def"] - player_stats["def"])
    player_stats["def"] += dp_restored
    reduced_dmg = max(0, enemy_atk - player_stats["def"])
    if reduced_dmg > 0:
        player_stats["def"] = 0
        player_stats["hp"] -= reduced_dmg
        print(f">> Parried! DP +{dp_restored}, but took {reduced_dmg} overflow!")
    else:
        player_stats["def"] -= enemy_atk
        print(f">> Parried! DP +{dp_restored}, shield holds! (DP: {player_stats['def']})")
    counter_dmg = 0
    if enemy_atk >= enemy_max_atk * 0.7:
        counter_dmg = int(player_stats["atk"] * PARRY_COUNTER_MULTIPLIER)
        print(f">> COUNTER-ATTACK! You strike back for {counter_dmg}!")
    return counter_dmg

def add_combo_cli(amount=COMBO_PER_ATTACK):
    player_stats["combo"] = min(COMBO_MAX, player_stats["combo"] + amount)

def get_input(prompt):
    user_input = input(prompt).strip()
    if user_input.lower() in ['quit', 'exit']:
        print("Thanks for playing Nabi! See you next time.")
        sys.exit()
    if user_input.lower() == "godmode":
        player_stats["hp"], player_stats["atk"], player_stats["def"] = 999, 999, 999
        player_stats["combo"] = COMBO_MAX
        print("** CHEAT ACTIVATED **")
        return get_input(prompt)
    return user_input

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
        player_stats["combo"] = 0
        
        print(f"\nLEVEL UP! You are now Level {player_stats['level']}!")
        print(f"Stats Increased: ATK +5 | Max HP +20 | Max Shield +5")
        print("Your Health and Shield have been fully restored!")

def start_combat(enemy_name):
    lvl_bonus = player_stats["level"] * 10
    c_mult = 1 + (player_stats.get("cowardice", 0) * 0.2)
    
    e_hp = int(random.randint(50 + lvl_bonus, 100 + lvl_bonus) * c_mult)
    e_atk = int(random.randint(15 + player_stats["level"], 25 + (player_stats["level"] * 2)) * c_mult)
    e_max_atk = e_atk
    e_dp = int(random.randint(5 + player_stats["level"], 15 + player_stats["level"]) * c_mult)

    print(f"\n--- BATTLE: {name} (Lv.{player_stats['level']}) vs {enemy_name} ---")
    if player_stats.get("cowardice", 0) > 0:
        print(f"CURSE: Your cowardice ({player_stats['cowardice']}) makes the enemy stronger!")
    print(f"Enemy Stats: HP: {e_hp} | ATK: {e_atk} | DEF: {e_dp}")

    while player_stats["hp"] > 0 and e_hp > 0:
        did_parry = False
        vuln_tag = " [VULNERABLE!]" if player_stats["def"] <= 0 else ""
        combo_tag = " [COMBO READY!]" if player_stats["combo"] >= COMBO_MAX else f" Combo: {player_stats['combo']}/{COMBO_MAX}"
        print(f"\n{name}: {player_stats['hp']}/{player_stats['max_hp']} HP | DP: {player_stats['def']}/{player_stats['max_def']}{vuln_tag}{combo_tag}")
        print(f"{enemy_name}: {e_hp} HP")

        actions = "1. Attack | 2. Parry | 3. Use Item | 4. Run | 5. Shop"
        if player_stats["combo"] >= COMBO_MAX:
            actions += " | 6. Special"
        actions += " | (Quit/Kill)"
        print(actions)
        
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
            add_combo_cli()
            print(f">> You strike! The {enemy_name} takes {player_stats['atk']} damage. Combo +{COMBO_PER_ATTACK}")
        
        elif action == "2":
            did_parry = True
            print(">> You raise your guard!")
        
        elif action == "3":
            print(f"Potions: HP({player_stats['inventory']['hp_potions']}) | Shield({player_stats['inventory']['dp_potions']})")
            item_choice = get_input("Use (HP/DP/Back): ").lower()
            
            if item_choice == "hp" and player_stats["inventory"]["hp_potions"] > 0:
                player_stats["hp"] = player_stats["max_hp"]
                player_stats["inventory"]["hp_potions"] -= 1
                print(">> Used HP Potion!")
                continue 
            elif item_choice == "dp" and player_stats["inventory"]["dp_potions"] > 0:
                player_stats["def"] = player_stats["max_def"]
                player_stats["inventory"]["dp_potions"] -= 1
                print(">> Shield restored!")
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

        elif action == "6" and player_stats["combo"] >= COMBO_MAX:
            print("COMBO SPECIAL:")
            print(f"  1. Power Strike (2.5x ATK, costs {POWER_STRIKE_DP_COST} DP)")
            print("  2. Shield Restore (full DP repair)")
            print("  3. Back")
            spec = get_input("Choose: ")
            if spec == "1":
                if player_stats["def"] >= POWER_STRIKE_DP_COST:
                    player_stats["combo"] = 0
                    player_stats["def"] -= POWER_STRIKE_DP_COST
                    dmg = int(player_stats["atk"] * POWER_STRIKE_MULTIPLIER)
                    e_hp -= dmg
                    print(f">> POWER STRIKE! -{POWER_STRIKE_DP_COST} DP, deals {dmg} damage!")
                else:
                    print(f">> Need {POWER_STRIKE_DP_COST} DP for Power Strike!")
                    continue
            elif spec == "2":
                player_stats["combo"] = 0
                old_dp = player_stats["def"]
                player_stats["def"] = player_stats["max_def"]
                print(f">> SHIELD RESTORE! DP fully repaired (+{player_stats['def'] - old_dp})!")
            else:
                continue

        else:
            print("Invalid action!")
            continue

        if e_hp > 0:
            if did_parry:
                counter_dmg = apply_parry_cli(e_atk, e_max_atk, enemy_name)
                if counter_dmg > 0:
                    e_hp -= counter_dmg
            else:
                apply_damage_to_player_cli(e_atk, enemy_name)

    if player_stats["hp"] > 0:
        print(f"\nVictory!")
        player_stats["cowardice"] = 0 
        drop_coins()
        gain_xp(50)
        save_game()
        return "victory"
    else:
        player_stats["hp"] = 0
        player_stats["cowardice"] = 0
        print(f"\n{name} has fallen in battle...")
        print("--- GAME OVER ---")
        save_game()
        return "defeat"

def get_yes_no(prompt):
    while True:
        choice = get_input(prompt).lower()
        if choice in ['yes', 'no']:
            return choice
        print("Please enter 'yes' or 'no'.")

def main_menu():
    global name
    print(f"--- NABI v{VERSION} ---")
    if os.path.exists(SAVE_FILE):
        choice = get_input("Save file found! Load previous game? (yes/no): ").lower()
        if choice == "yes":
            if load_game():
                name = get_input("Confirm your hero's name: ")

    if name.strip() == "":
        name = get_input("What should i call you, Oh great noble warrior? ")
    
    while True:
        print("\n--- MAIN MENU ---")
        print("1. Start Adventure")
        print("2. Quit Game")
        choice = get_input("Select: ")

        if choice == "1":
            player_stats["hp"] = player_stats["max_hp"]
            player_stats["def"] = player_stats["max_def"]
            save_game()
            play_game()
        elif choice == "2":
            sys.exit()

def play_game():
    global dan_patience
    print(f"\nWelcome {name}, to the world of NABI!")

    answer = get_yes_no("Would you like to know more about Nabi? (yes/no): ")
    if answer == "yes":
        print("\nNabi is a world full of mystery and adventure, even i know less about it than you would like to know.")
        print("But here in Nabi, you can be anything you want to be, from a simple farmer to a great warrior!")
        print(f"The choice is yours, Brave warrior {name}!")
    else:
        print("\nit's not like i wanted to answer!")

    start_answer = get_yes_no("\nWould you like to start your adventure now? (yes/no): ")
    if start_answer == "no":
        print("Oh well, maybe next time! ")
        return
    save_game()

    print("Great! Let's begin your adventure!, Be warned, it's not going to be easy! Off you go!")
    while True:
        print("You find yourself in a dark forest, with two paths ahead of you. ", end='')
        path_answer = get_input("What path would you take? (Right/Left/Shop): ").lower()
        save_game()
        if path_answer == "shop":
            print("Isn't it a bit early to be shopping?")
            continue
        elif path_answer == "right":
            print("You thread the path and have arrived at the field of Dan. Would you like to go back or speak to Dan")
            dan_answer = get_input("(Back/Speak): ").lower()
            if dan_answer == "back":
                print("Well, you have chosen to go back. Maybe next time you'll be more naive!")
                dan_patience = 0
                continue
            if dan_answer == "speak":
                dan_patience += 1
            else:
                print("Invalid choice. Please enter Back or Speak.")
                continue

            if dan_patience >= 3:
                print(f"\nDan: THAT'S IT! I told you to leave!")
                print("Dan: You mortals never know when to stop poking your noses where they don't belong!")
                print("--- Dan's skin begins to tear as giant wings burst from his back! ---")
                print("Dan transforms into a fearsome demon!")
                print("HEHEHE! You're COOKED!")
                result = start_combat("Demon Dan")
                if result == "victory":
                    return
                elif result == "defeat":
                    return
                elif result == "menu":
                    return
                else:
                    continue
            else:
                print("\nDan: And you are?")
                print(f"You: I am called {name}.")
                print(f"Dan: Hm, {name}, that's an interesting name. I'm Dan, the owner of this fine field.")
                print("Dan: What brings you here?")
                print("1. I'm looking for adventure.")
                print("2. Just passing through.")
                print("3. None of your business.")
                print("4. I am lost and need help.")
                reason = get_input("Choose an option (1-4): ")
                if reason == "1":
                    print("Dan: An adventure you say? Well i ain't got none now scram!")
                    print("You: How rude!")
                    print("Dan: Yeah well, maybe next time you'll think twice before bothering me!")
                    print("You walk away, feeling a mix of anger and determination to find your own adventure.")
                elif reason == "2":
                    print("Dan: Just passing through, huh? Well, safe travels then, but please take go away and take another path!")
                    print("You nod and continue on your journey, grateful for the brief encounter.")
                elif reason == "3":
                    print("Dan: Well, no need to be rude about it! Mind your own business then.")
                    print("You feel a bit embarrassed but decide to leave Dan to his work.")
                elif reason == "4":
                    print("Dan: Lost, are you? Well, you're in luck! I know these parts well. How about you rest for the night first? Then you head out tomorrow.")
                    choice = get_input("1. Accept Dan's offer\n2. Decline and continue on your own\nChoose an option (1 or 2): ")
                    if choice == "1":
                        print("You decide to accept Dan's offer. You spend the night in his home.")
                        print("However, as he had poisoned your food, you died in your sleep.")
                        print("You naive fool! You should have been more careful.")
                        print("--- GAME OVER ---")
                        player_stats["hp"] = 0
                        save_game()
                        return
                    elif choice == "2":
                        print("You decide to decline Dan's offer, your instincts telling you to be cautious.")
                        print("Feeling a sense of danger, from the fields of Dan, you apprihend him but he escapes into his field, and turn outs he's a demon worshipper.")
                        print("He transforms into a demon.")
                        print("Do you wish to fight the demon?")
                        fight_choice = get_yes_no("(yes/no): ")
                        if fight_choice == "no":
                            print("You decide not to fight and flee from the demon. Thank the gods you're a COWARD!")
                            continue
                        elif fight_choice == "yes":
                            print("You didn't keep to yourself, and now you want to fight a demon? Just Great!")
                            result = start_combat("Demon Dan")
                            if result == "victory":
                                return
                            elif result == "defeat":
                                return
                            elif result == "menu":
                                return
                            else:
                                continue

                if reason in ["1", "2", "3"]:
                    if dan_patience == 1:
                        print("\nDan: I don't have time for this. Go away before I lose my temper.")
                    elif dan_patience == 2:
                        print("\nDan: (Vein throbbing) I'm warning you... leave. Now.")
                        print("You walk away, but Dan is watching you closely...")

        elif path_answer == "left":
            print("You head left into the forest, but there's nothing here yet.")
            continue
        else:
            print("Invalid choice. Please enter Right, Left, or Shop.")
            continue


if __name__ == "__main__":
    main_menu()
