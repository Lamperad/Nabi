import json
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
