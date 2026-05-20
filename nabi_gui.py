"""
Nabi v4.0.0 — Audiovisual RPG (Pygame)
Animated characters, parallax backgrounds, fluid movement, sound,
arcade mode with multiple monsters, cheat menu, and resizable window.
"""

import pygame
import json
import os
import sys
import random
import copy
import math

# ---------------------------------------------------------------------------
#  CONSTANTS
# ---------------------------------------------------------------------------
VERSION = "5.0.0"
SAVE_FILE = "save_data.json"
ARCADE_SAVE_FILE = "arcade_save.json"
SCREEN_W, SCREEN_H = 960, 640
FPS = 60
if getattr(sys, 'frozen', False):
    _BASE_DIR = sys._MEIPASS
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(_BASE_DIR, "assets")

# Colours
C_BG = (18, 18, 30)
C_PANEL = (30, 30, 50)
C_PANEL_LIGHT = (45, 45, 70)
C_BORDER = (80, 80, 120)
C_TEXT = (220, 220, 230)
C_TEXT_DIM = (140, 140, 160)
C_GOLD = (255, 215, 80)
C_RED = (220, 60, 60)
C_GREEN = (80, 200, 100)
C_BLUE = (80, 140, 220)
C_PURPLE = (160, 80, 200)
C_ORANGE = (230, 140, 50)
C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)
C_HP_BAR = (200, 50, 50)
C_HP_BG = (60, 20, 20)
C_DP_BAR = (50, 120, 200)
C_DP_BG = (20, 40, 60)
C_XP_BAR = (200, 180, 50)
C_XP_BG = (50, 45, 15)
C_COMBO_BAR = (220, 120, 220)
C_COMBO_BG = (50, 25, 50)
C_VULN = (255, 80, 80)

# ---------------------------------------------------------------------------
#  GAME STATE
# ---------------------------------------------------------------------------
DEFAULT_PLAYER_STATS = {
    "hp": 100, "max_hp": 100, "atk": 20, "def": 15, "max_def": 15,
    "coins": 0, "level": 1, "xp": 0, "cowardice": 0, "combo": 0,
    "bone_key": False, "mirror_vision": False, "signet_ring": False,
    "inventory": {"hp_potions": 2, "dp_potions": 2}
}
player_stats = copy.deepcopy(DEFAULT_PLAYER_STATS)
player_name = ""
dan_patience = 0

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
        p = player_stats.copy()
        p["version"] = VERSION
        p["name"] = player_name
        with open(SAVE_FILE, "w") as f:
            json.dump(p, f, indent=4)
        return True
    except Exception:
        return False

def load_game():
    global player_stats, player_name
    if not os.path.exists(SAVE_FILE):
        return False
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        data.pop("version", None)
        player_name = data.pop("name", "")
        player_stats = normalize_stats(data)
        if player_stats["hp"] <= 0:
            player_stats["hp"] = player_stats["max_hp"]
            player_stats["def"] = player_stats["max_def"]
        return True
    except Exception:
        return False

def drop_coins():
    loot = random.randint(10, 50)
    player_stats["coins"] = min(500, player_stats["coins"] + loot)
    return loot

def gain_xp(amount):
    player_stats["xp"] += amount
    leveled = False
    while player_stats["xp"] >= 100:
        player_stats["level"] += 1
        player_stats["xp"] -= 100
        player_stats["max_hp"] += 20
        player_stats["hp"] = player_stats["max_hp"]
        player_stats["atk"] += 5
        player_stats["max_def"] += 5
        player_stats["def"] = player_stats["max_def"]
        player_stats["combo"] = 0
        leveled = True
    return leveled


# ---------------------------------------------------------------------------
#  DP SYSTEM — Shield HP / Durability / Parry / Combo / Stamina
# ---------------------------------------------------------------------------
COMBO_MAX = 100
COMBO_PER_ATTACK = 25
POWER_STRIKE_DP_COST = 10
POWER_STRIKE_MULTIPLIER = 2.5
VULNERABILITY_BONUS = 0.5
PARRY_DP_RESTORE = 5
PARRY_COUNTER_MULTIPLIER = 0.5

def apply_damage_to_player(raw_damage, log, source_name="Enemy"):
    """Shield HP system: DP absorbs damage first, overflow hits HP.
    At 0 DP, player takes 50% bonus damage (vulnerability)."""
    if player_stats["def"] <= 0:
        vuln_dmg = int(raw_damage * (1 + VULNERABILITY_BONUS))
        player_stats["hp"] -= vuln_dmg
        log.append(f"VULNERABLE! {source_name} deals {vuln_dmg} ({raw_damage}+{vuln_dmg - raw_damage})!")
        return vuln_dmg
    if raw_damage <= player_stats["def"]:
        player_stats["def"] -= raw_damage
        log.append(f"Shield absorbs {raw_damage}! (DP: {player_stats['def']}/{player_stats['max_def']})")
        return 0
    overflow = raw_damage - player_stats["def"]
    log.append(f"Shield broken! {player_stats['def']} absorbed, {overflow} HP lost!")
    player_stats["def"] = 0
    player_stats["hp"] -= overflow
    return overflow

def apply_parry(enemy_atk, enemy_max_atk, log, source_name="Enemy"):
    """Defend = Parry. Restores some DP. If enemy attack is strong, counter-attacks."""
    dp_restored = min(PARRY_DP_RESTORE, player_stats["max_def"] - player_stats["def"])
    player_stats["def"] += dp_restored
    reduced_dmg = max(0, enemy_atk - player_stats["def"])
    if reduced_dmg > 0:
        player_stats["def"] = 0
        player_stats["hp"] -= reduced_dmg
        log.append(f"Parried! DP +{dp_restored}, but took {reduced_dmg} overflow!")
    else:
        player_stats["def"] -= enemy_atk
        log.append(f"Parried! DP +{dp_restored}, shield holds! (DP: {player_stats['def']})")
    counter_dmg = 0
    is_strong = enemy_atk >= enemy_max_atk * 0.7
    if is_strong:
        counter_dmg = int(player_stats["atk"] * PARRY_COUNTER_MULTIPLIER)
        log.append(f"COUNTER-ATTACK! You strike back for {counter_dmg}!")
    return counter_dmg

def add_combo(amount=COMBO_PER_ATTACK):
    player_stats["combo"] = min(COMBO_MAX, player_stats["combo"] + amount)

def can_power_strike():
    return player_stats["combo"] >= COMBO_MAX and player_stats["def"] >= POWER_STRIKE_DP_COST

def do_power_strike(log):
    """Spend combo + DP for massive damage."""
    player_stats["combo"] = 0
    player_stats["def"] -= POWER_STRIKE_DP_COST
    dmg = int(player_stats["atk"] * POWER_STRIKE_MULTIPLIER)
    log.append(f"POWER STRIKE! -{POWER_STRIKE_DP_COST} DP, deals {dmg} damage!")
    return dmg

def can_shield_restore():
    return player_stats["combo"] >= COMBO_MAX

def do_shield_restore(log):
    """Spend combo to fully restore DP."""
    player_stats["combo"] = 0
    old_dp = player_stats["def"]
    player_stats["def"] = player_stats["max_def"]
    restored = player_stats["def"] - old_dp
    log.append(f"SHIELD RESTORE! DP fully repaired (+{restored})!")


# ---------------------------------------------------------------------------
#  PYGAME INIT
# ---------------------------------------------------------------------------
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    AUDIO_OK = True
except Exception:
    AUDIO_OK = False

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
pygame.display.set_caption(f"Nabi v{VERSION}")
_icon_path = os.path.join(ASSET_DIR, "icon.png")
if os.path.exists(_icon_path):
    try:
        pygame.display.set_icon(pygame.image.load(_icon_path))
    except Exception:
        pass
clock = pygame.time.Clock()

font_sm = pygame.font.SysFont("consolas", 16)
font_md = pygame.font.SysFont("consolas", 20)
font_lg = pygame.font.SysFont("consolas", 28)
font_xl = pygame.font.SysFont("consolas", 42, bold=True)
font_title = pygame.font.SysFont("consolas", 56, bold=True)

# ---------------------------------------------------------------------------
#  SOUND
# ---------------------------------------------------------------------------
sounds = {}

def load_sounds():
    sdir = os.path.join(ASSET_DIR, "sounds")
    if not AUDIO_OK or not os.path.isdir(sdir):
        return
    for fname in os.listdir(sdir):
        if fname.endswith(".wav"):
            try:
                sounds[fname[:-4]] = pygame.mixer.Sound(os.path.join(sdir, fname))
            except Exception:
                pass

load_sounds()

def play_sound(name):
    if name in sounds:
        try:
            sounds[name].play()
        except Exception:
            pass


# ---------------------------------------------------------------------------
#  SPRITE / ANIMATION SYSTEM
# ---------------------------------------------------------------------------
class SpriteSheet:
    def __init__(self, path, frame_w=64, frame_h=64, scale=2):
        try:
            raw = pygame.image.load(path).convert_alpha()
            n = raw.get_width() // frame_w
            self.frames = []
            for i in range(n):
                sub = raw.subsurface((i * frame_w, 0, frame_w, frame_h))
                if scale != 1:
                    sub = pygame.transform.scale(sub, (frame_w * scale, frame_h * scale))
                self.frames.append(sub)
        except Exception:
            s = pygame.Surface((frame_w * scale, frame_h * scale), pygame.SRCALPHA)
            s.fill((255, 0, 255, 80))
            self.frames = [s]

    def __len__(self):
        return len(self.frames)

    def get(self, index):
        return self.frames[int(index) % len(self.frames)]


class AnimatedSprite:
    def __init__(self, sheet, x=0, y=0, fps=8):
        self.sheet = sheet
        self.x = float(x)
        self.y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)
        self.frame_idx = 0.0
        self.fps = fps
        self.flip_h = False
        self.visible = True
        self.alpha = 255
        self.scale_mult = 1.0

    def update(self, dt):
        self.frame_idx += self.fps * dt
        # Smooth movement toward target
        speed = 300 * dt
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 1:
            factor = min(1.0, speed / dist)
            self.x += dx * factor
            self.y += dy * factor
        else:
            self.x = self.target_x
            self.y = self.target_y

    def draw(self, surface):
        if not self.visible:
            return
        frame = self.sheet.get(self.frame_idx)
        if self.flip_h:
            frame = pygame.transform.flip(frame, True, False)
        if self.scale_mult != 1.0:
            w = int(frame.get_width() * self.scale_mult)
            h = int(frame.get_height() * self.scale_mult)
            frame = pygame.transform.scale(frame, (w, h))
        if self.alpha < 255:
            frame = frame.copy()
            frame.set_alpha(self.alpha)
        surface.blit(frame, (int(self.x), int(self.y)))

    def move_to(self, x, y):
        self.target_x = float(x)
        self.target_y = float(y)

    def set_pos(self, x, y):
        self.x = self.target_x = float(x)
        self.y = self.target_y = float(y)

    def is_moving(self):
        return abs(self.x - self.target_x) > 1 or abs(self.y - self.target_y) > 1

    def set_sheet(self, sheet):
        self.sheet = sheet
        self.frame_idx = 0


# ---------------------------------------------------------------------------
#  PARALLAX BACKGROUND
# ---------------------------------------------------------------------------
class ParallaxBG:
    def __init__(self):
        self.layers = []  # [(surface, scroll_speed, x_offset)]

    def add_layer(self, path, scroll_speed=0):
        try:
            img = pygame.image.load(path).convert_alpha()
        except Exception:
            img = pygame.Surface((SCREEN_W, SCREEN_H))
            img.fill(C_BG)
        self.layers.append([img, scroll_speed, 0.0])

    def set_static(self, path):
        self.layers = []
        self.add_layer(path, 0)

    def update(self, dt):
        for layer in self.layers:
            layer[2] -= layer[1] * dt
            if layer[0].get_width() > SCREEN_W:
                if layer[2] < -(layer[0].get_width() - SCREEN_W):
                    layer[2] = 0

    def draw(self, surface):
        for img, _, xoff in self.layers:
            surface.blit(img, (int(xoff), 0))


# ---------------------------------------------------------------------------
#  LOAD ALL SPRITE SHEETS
# ---------------------------------------------------------------------------
def load_sheet(name, frame_w=64, frame_h=64, scale=2):
    path = os.path.join(ASSET_DIR, "avatars", f"{name}.png")
    return SpriteSheet(path, frame_w, frame_h, scale)

# Load sprites
spr_player_idle = load_sheet("player_idle")
spr_player_walk = load_sheet("player_walk")
spr_player_attack = load_sheet("player_attack")
spr_player_hurt = load_sheet("player_hurt")
spr_player_defend = load_sheet("player_defend")
spr_dan_idle = load_sheet("dan_farmer_idle")
spr_dan_angry = load_sheet("dan_farmer_angry")
spr_demon_idle = load_sheet("demon_idle")
spr_demon_attack = load_sheet("demon_attack")
spr_dan_transform = load_sheet("dan_transform")
spr_narrator = load_sheet("narrator_idle")

# Arcade monster sprites
spr_skeleton_idle = load_sheet("skeleton_idle")
spr_skeleton_attack = load_sheet("skeleton_attack")
spr_slime_idle = load_sheet("slime_idle")
spr_slime_attack = load_sheet("slime_attack")
spr_wraith_idle = load_sheet("wraith_idle")
spr_wraith_attack = load_sheet("wraith_attack")
spr_golem_idle = load_sheet("golem_idle")
spr_golem_attack = load_sheet("golem_attack")
spr_spider_idle = load_sheet("spider_idle")
spr_spider_attack = load_sheet("spider_attack")
spr_dk_idle = load_sheet("dark_knight_idle")
spr_dk_attack = load_sheet("dark_knight_attack")

# Story expansion sprites
spr_imp_idle = load_sheet("imp_idle")
spr_imp_attack = load_sheet("imp_attack")
spr_oracle_idle = load_sheet("oracle_idle")
spr_dragon_idle = load_sheet("dragon_idle")
spr_dragon_attack = load_sheet("dragon_attack")
spr_mirror_wraith_idle = load_sheet("mirror_wraith_idle")
spr_mirror_wraith_attack = load_sheet("mirror_wraith_attack")
spr_revenant_idle = load_sheet("revenant_idle")
spr_revenant_attack = load_sheet("revenant_attack")
spr_malachar_idle = load_sheet("malachar_idle")
spr_malachar_attack = load_sheet("malachar_attack")
spr_necromancer_idle = load_sheet("necromancer_idle")
spr_necromancer_attack = load_sheet("necromancer_attack")
spr_lore_golem_idle = load_sheet("lore_golem_idle")
spr_lore_golem_attack = load_sheet("lore_golem_attack")
spr_undead_idle = load_sheet("undead_idle")
spr_undead_attack = load_sheet("undead_attack")

# Enemy sprite lookup for combat_screen
ENEMY_SPRITES = {
    "demon": (spr_demon_idle, spr_demon_attack),
    "malachar": (spr_malachar_idle, spr_malachar_attack),
    "dragon": (spr_dragon_idle, spr_dragon_attack),
    "veth": (spr_dragon_idle, spr_dragon_attack),
    "mirror wraith": (spr_mirror_wraith_idle, spr_mirror_wraith_attack),
    "revenant": (spr_revenant_idle, spr_revenant_attack),
    "skeleton": (spr_skeleton_idle, spr_skeleton_attack),
    "lore golem": (spr_lore_golem_idle, spr_lore_golem_attack),
    "golem": (spr_lore_golem_idle, spr_lore_golem_attack),
    "ghoul": (spr_undead_idle, spr_undead_attack),
    "undead": (spr_undead_idle, spr_undead_attack),
    "necromancer": (spr_necromancer_idle, spr_necromancer_attack),
    "imp": (spr_imp_idle, spr_imp_attack),
    "shadow imp": (spr_imp_idle, spr_imp_attack),
}

# Monster type definitions for arcade mode
MONSTER_TYPES = [
    {
        "name": "Skeleton Warrior",
        "idle": spr_skeleton_idle,
        "attack": spr_skeleton_attack,
        "pattern": "aggressive",
        "base_hp": 60, "base_atk": 18, "base_def": 8,
        "color": (210, 200, 180),
    },
    {
        "name": "Toxic Slime",
        "idle": spr_slime_idle,
        "attack": spr_slime_attack,
        "pattern": "poison",
        "base_hp": 45, "base_atk": 12, "base_def": 5,
        "color": (40, 180, 60),
    },
    {
        "name": "Shadow Wraith",
        "idle": spr_wraith_idle,
        "attack": spr_wraith_attack,
        "pattern": "evasive",
        "base_hp": 50, "base_atk": 22, "base_def": 4,
        "color": (160, 80, 200),
    },
    {
        "name": "Fire Golem",
        "idle": spr_golem_idle,
        "attack": spr_golem_attack,
        "pattern": "tank",
        "base_hp": 100, "base_atk": 15, "base_def": 18,
        "color": (230, 140, 50),
    },
    {
        "name": "Ice Spider",
        "idle": spr_spider_idle,
        "attack": spr_spider_attack,
        "pattern": "freeze",
        "base_hp": 55, "base_atk": 20, "base_def": 6,
        "color": (80, 140, 200),
    },
    {
        "name": "Dark Knight",
        "idle": spr_dk_idle,
        "attack": spr_dk_attack,
        "pattern": "berserker",
        "base_hp": 80, "base_atk": 20, "base_def": 15,
        "color": (120, 100, 140),
    },
]

# Create sprite instances
player_sprite = AnimatedSprite(spr_player_idle, 100, 350, fps=5)
dan_sprite = AnimatedSprite(spr_dan_idle, 650, 350, fps=5)
narrator_sprite = AnimatedSprite(spr_narrator, 50, 300, fps=4)
narrator_sprite.alpha = 200

# Background manager
bg = ParallaxBG()

def load_bg(name):
    return os.path.join(ASSET_DIR, "backgrounds", f"{name}.png")


# ---------------------------------------------------------------------------
#  DRAWING HELPERS
# ---------------------------------------------------------------------------
def draw_panel(rect, border_color=C_BORDER, fill=C_PANEL, border_width=2, alpha=220):
    surf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    surf.fill((*fill, alpha))
    screen.blit(surf, (rect[0], rect[1]))
    if border_width > 0:
        pygame.draw.rect(screen, border_color, rect, border_width, border_radius=6)

def draw_text(text, font, color, x, y, anchor="topleft", max_width=None):
    if max_width:
        words = text.split(' ')
        lines, current = [], ""
        for w in words:
            test = current + (" " if current else "") + w
            if font.size(test)[0] > max_width:
                if current:
                    lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)
        yy = y
        for line in lines:
            surf = font.render(line, True, color)
            screen.blit(surf, (x, yy))
            yy += font.get_height() + 2
        return yy - y
    else:
        surf = font.render(text, True, color)
        r = surf.get_rect(**{anchor: (x, y)})
        screen.blit(surf, r)
        return font.get_height()

def draw_bar(x, y, w, h, current, maximum, bar_color, bg_color, label=""):
    pygame.draw.rect(screen, bg_color, (x, y, w, h), border_radius=4)
    if maximum > 0:
        fill_w = max(0, int((current / maximum) * w))
        if fill_w > 0:
            pygame.draw.rect(screen, bar_color, (x, y, fill_w, h), border_radius=4)
    pygame.draw.rect(screen, C_BORDER, (x, y, w, h), 1, border_radius=4)
    if label:
        txt = font_sm.render(label, True, C_WHITE)
        screen.blit(txt, (x + 4, y + (h - txt.get_height()) // 2))

def draw_stat_panel(x, y):
    w, h = 280, 210
    draw_panel((x, y, w, h), fill=C_PANEL)
    ny = y + 8
    draw_text(f"{player_name}  Lv.{player_stats['level']}", font_md, C_GOLD, x + 10, ny)
    ny += 28
    draw_bar(x + 10, ny, w - 20, 20, max(0, player_stats['hp']), player_stats['max_hp'], C_HP_BAR, C_HP_BG,
             f"HP {max(0,player_stats['hp'])}/{player_stats['max_hp']}")
    ny += 26
    dp_color = C_VULN if player_stats['def'] <= 0 else C_DP_BAR
    dp_label = "DP VULNERABLE!" if player_stats['def'] <= 0 else f"DP {player_stats['def']}/{player_stats['max_def']}"
    draw_bar(x + 10, ny, w - 20, 20, max(0, player_stats['def']), player_stats['max_def'], dp_color, C_DP_BG,
             dp_label)
    ny += 26
    combo = player_stats.get('combo', 0)
    combo_label = "COMBO READY!" if combo >= COMBO_MAX else f"Combo {combo}/{COMBO_MAX}"
    combo_color = C_GOLD if combo >= COMBO_MAX else C_COMBO_BAR
    draw_bar(x + 10, ny, w - 20, 16, combo, COMBO_MAX, combo_color, C_COMBO_BG, combo_label)
    ny += 22
    draw_bar(x + 10, ny, w - 20, 14, player_stats['xp'], 100, C_XP_BAR, C_XP_BG,
             f"XP {player_stats['xp']}/100")
    ny += 20
    draw_text(f"ATK: {player_stats['atk']}  Coins: {player_stats['coins']}/500", font_sm, C_TEXT_DIM, x + 10, ny)
    ny += 18
    inv = player_stats['inventory']
    draw_text(f"HP Pots: {inv['hp_potions']}  DP Pots: {inv['dp_potions']}", font_sm, C_TEXT_DIM, x + 10, ny)
    if player_stats.get('cowardice', 0) > 0:
        ny += 18
        draw_text(f"Cowardice: {player_stats['cowardice']}", font_sm, C_RED, x + 10, ny)


# ---------------------------------------------------------------------------
#  BUTTON
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, rect, text, color=C_PANEL_LIGHT, hover_color=C_BLUE,
                 text_color=C_TEXT, font=None, key=None, enabled=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = font or font_md
        self.key = key
        self.hovered = False
        self.enabled = enabled

    def draw(self):
        col = self.hover_color if self.hovered else self.color
        if not self.enabled:
            col = (40, 40, 40)
        pygame.draw.rect(screen, col, self.rect, border_radius=6)
        pygame.draw.rect(screen, C_BORDER if self.enabled else (60, 60, 60),
                         self.rect, 2, border_radius=6)
        tc = self.text_color if self.enabled else C_TEXT_DIM
        txt = self.font.render(self.text, True, tc)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def update(self, mouse_pos):
        self.hovered = self.enabled and self.rect.collidepoint(mouse_pos)

    def clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered and self.enabled:
            return True
        if event.type == pygame.KEYDOWN and self.key and self.enabled and event.key == self.key:
            return True
        return False


# ---------------------------------------------------------------------------
#  CORE UI FUNCTIONS
# ---------------------------------------------------------------------------
def handle_resize(event):
    global screen, SCREEN_W, SCREEN_H
    SCREEN_W, SCREEN_H = max(640, event.w), max(480, event.h)
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)

class PauseMenuExit(Exception):
    """Raised when the player chooses to return to main menu from the pause menu."""
    pass

def pause_menu():
    """Esc pause overlay. Returns 'resume' or raises PauseMenuExit."""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    buttons = [
        Button((SCREEN_W // 2 - 150, SCREEN_H // 2 - 70, 300, 44), "1. Resume", key=pygame.K_1),
        Button((SCREEN_W // 2 - 150, SCREEN_H // 2 - 15, 300, 44), "2. Main Menu", key=pygame.K_2),
        Button((SCREEN_W // 2 - 150, SCREEN_H // 2 + 40, 300, 44), "3. Quit Game", key=pygame.K_3),
    ]
    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game(); pygame.quit(); sys.exit()
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "resume"
            for i, btn in enumerate(buttons):
                if btn.clicked(event):
                    play_sound("menu_click")
                    if i == 0:
                        return "resume"
                    elif i == 1:
                        raise PauseMenuExit()
                    elif i == 2:
                        save_game(); pygame.quit(); sys.exit()
        clock.tick(FPS)
        screen.blit(overlay, (0, 0))
        draw_text("PAUSED", font_xl, C_GOLD, SCREEN_W // 2, SCREEN_H // 2 - 120, "center")
        for btn in buttons:
            btn.update(mouse_pos)
            btn.draw()
        pygame.display.flip()

def pump_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            pygame.quit()
            sys.exit()
        if event.type == pygame.VIDEORESIZE:
            handle_resize(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pause_menu()

def get_text_input(prompt, max_len=20):
    text = ""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game(); pygame.quit(); sys.exit()
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and text.strip():
                    play_sound("menu_click")
                    return text.strip()
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                elif len(text) < max_len and event.unicode.isprintable():
                    text += event.unicode
        dt = clock.tick(FPS) / 1000
        bg.update(dt)
        bg.draw(screen)
        narrator_sprite.update(dt)
        narrator_sprite.draw(screen)
        draw_panel((SCREEN_W // 2 - 250, SCREEN_H // 2 - 60, 500, 120))
        draw_text(prompt, font_md, C_GOLD, SCREEN_W // 2, SCREEN_H // 2 - 35, "center")
        input_rect = pygame.Rect(SCREEN_W // 2 - 200, SCREEN_H // 2, 400, 36)
        pygame.draw.rect(screen, (20, 20, 35), input_rect, border_radius=4)
        pygame.draw.rect(screen, C_GOLD, input_rect, 2, border_radius=4)
        cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        draw_text(text + cursor, font_md, C_WHITE, input_rect.x + 8, input_rect.y + 6)
        pygame.display.flip()


def animate_frames(duration_ms, draw_fn, sprites=None):
    """Run an animation loop for `duration_ms`, calling draw_fn each frame."""
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration_ms:
        dt = clock.tick(FPS) / 1000
        pump_events()
        bg.update(dt)
        bg.draw(screen)
        if sprites:
            for sp in sprites:
                sp.update(dt)
                sp.draw(screen)
        t = (pygame.time.get_ticks() - start) / duration_ms
        draw_fn(t)
        pygame.display.flip()


def wait_for_movement(sprites, timeout=3000):
    """Animate until all sprites stop moving or timeout."""
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < timeout:
        dt = clock.tick(FPS) / 1000
        pump_events()
        bg.update(dt)
        bg.draw(screen)
        all_done = True
        for sp in sprites:
            sp.update(dt)
            sp.draw(screen)
            if sp.is_moving():
                all_done = False
        pygame.display.flip()
        if all_done:
            break


def typewriter(lines, sprites=None, narrator_visible=True):
    """Typewriter with animated sprites and background. Tab skips all dialogue."""
    if sprites is None:
        sprites = []
    displayed = []
    skip_all = False
    for line_text in lines:
        if skip_all:
            displayed.append(line_text)
            continue
        displayed.append("")
        skip = False
        for i, ch in enumerate(line_text):
            displayed[-1] += ch
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_game(); pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                    for j in range(len(displayed)):
                        displayed[j] = lines[j] if j < len(lines) else displayed[j]
                    displayed[-1] = line_text
                    skip_all = True
                    skip = True
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pause_menu()
                elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    displayed[-1] = line_text
                    skip = True
                    break
            if skip:
                break
            dt = clock.tick(FPS) / 1000
            bg.update(dt)
            bg.draw(screen)
            for sp in sprites:
                sp.update(dt)
                sp.draw(screen)
            if narrator_visible:
                narrator_sprite.update(dt)
                narrator_sprite.draw(screen)
            draw_stat_panel(SCREEN_W - 290, 10)
            _render_tw_lines(displayed)
            pygame.display.flip()
            if i % 2 == 0:
                play_sound("text_tick")
            pygame.time.delay(22)

    if skip_all:
        return

    # Wait for click
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game(); pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pause_menu()
            elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return
        dt = clock.tick(FPS) / 1000
        bg.update(dt)
        bg.draw(screen)
        for sp in sprites:
            sp.update(dt)
            sp.draw(screen)
        if narrator_visible:
            narrator_sprite.update(dt)
            narrator_sprite.draw(screen)
        draw_stat_panel(SCREEN_W - 290, 10)
        _render_tw_lines(displayed)
        draw_text("[ Click or press any key | Tab to skip ]", font_sm, C_TEXT_DIM, SCREEN_W // 2, SCREEN_H - 30, "center")
        pygame.display.flip()


def _render_tw_lines(lines):
    panel_w = SCREEN_W - 310
    draw_panel((20, SCREEN_H - 220, panel_w, 200), fill=C_PANEL)
    y = SCREEN_H - 210
    for line in lines[-8:]:
        h = draw_text(line, font_md, C_TEXT, 35, y, max_width=panel_w - 30)
        y += h + 4
        if y > SCREEN_H - 30:
            break


def show_menu(title, options, sprites=None, subtitle=""):
    if sprites is None:
        sprites = []
    buttons = []
    start_y = 240 if not subtitle else 280
    for i, opt in enumerate(options):
        key_map = {0: pygame.K_1, 1: pygame.K_2, 2: pygame.K_3, 3: pygame.K_4,
                   4: pygame.K_5, 5: pygame.K_6, 6: pygame.K_7, 7: pygame.K_8}
        bw, bh = 400, 44
        bx = SCREEN_W // 2 - bw // 2
        by = start_y + i * (bh + 10)
        buttons.append(Button((bx, by, bw, bh), f"{i+1}. {opt}", key=key_map.get(i)))

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game(); pygame.quit(); sys.exit()
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
                for bi in range(len(buttons)):
                    bw, bh = 400, 44
                    bx = SCREEN_W // 2 - bw // 2
                    by_pos = start_y + bi * (bh + 10)
                    buttons[bi].rect = pygame.Rect(bx, by_pos, bw, bh)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pause_menu()
            for i, btn in enumerate(buttons):
                if btn.clicked(event):
                    play_sound("menu_click")
                    return i
        dt = clock.tick(FPS) / 1000
        bg.update(dt)
        bg.draw(screen)
        for sp in sprites:
            sp.update(dt)
            sp.draw(screen)
        if player_name:
            draw_stat_panel(SCREEN_W - 290, 10)
        draw_text(title, font_xl, C_GOLD, SCREEN_W // 2, 160, "center")
        if subtitle:
            draw_text(subtitle, font_md, C_TEXT_DIM, SCREEN_W // 2, 210, "center")
        for btn in buttons:
            btn.update(mouse_pos)
            btn.draw()
        pygame.display.flip()


def show_message(text, color=C_TEXT, duration=0, sprites=None):
    if sprites is None:
        sprites = []
    start = pygame.time.get_ticks()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game(); pygame.quit(); sys.exit()
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pause_menu()
            elif duration == 0 and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return
        if duration > 0 and pygame.time.get_ticks() - start > duration:
            return
        dt = clock.tick(FPS) / 1000
        bg.update(dt)
        bg.draw(screen)
        for sp in sprites:
            sp.update(dt)
            sp.draw(screen)
        if player_name:
            draw_stat_panel(SCREEN_W - 290, 10)
        draw_panel((SCREEN_W // 2 - 300, SCREEN_H // 2 - 50, 600, 100))
        draw_text(text, font_md, color, SCREEN_W // 2, SCREEN_H // 2, "center")
        if duration == 0:
            draw_text("[ Click or press any key ]", font_sm, C_TEXT_DIM, SCREEN_W // 2, SCREEN_H // 2 + 30, "center")
        pygame.display.flip()


def fade_transition(duration_ms=400):
    fade_surf = pygame.Surface((SCREEN_W, SCREEN_H))
    fade_surf.fill(C_BLACK)
    half = duration_ms // 2
    for i in range(half // 16 + 1):
        alpha = min(255, int(255 * i / max(1, half // 16)))
        fade_surf.set_alpha(alpha)
        screen.blit(fade_surf, (0, 0))
        pygame.display.flip()
        pygame.time.delay(16)
    for i in range(half // 16 + 1):
        alpha = max(0, 255 - int(255 * i / max(1, half // 16)))
        fade_surf.set_alpha(alpha)
        screen.blit(fade_surf, (0, 0))
        pygame.display.flip()
        pygame.time.delay(16)


# ---------------------------------------------------------------------------
#  SHOP
# ---------------------------------------------------------------------------
def shop_screen():
    bg.set_static(load_bg("shop"))
    items = [
        ("[RESTORE] Full HP", 20, "hp_restore"),
        ("[REPAIR] Full Shield/DP", 20, "dp_restore"),
        ("[BUFF] ATK +5", 100, "atk_buff"),
        ("[BUFF] Max Shield +5", 100, "dp_buff"),
        ("[BUY] HP Potion", 50, "hp_pot"),
        ("[BUY] Shield Potion", 50, "dp_pot"),
        ("[UPGRADE] Max HP +20", 150, "hp_upgrade"),
        ("[UPGRADE] Max Shield +10", 120, "dp_upgrade"),
        ("[EXIT] Leave Shop", 0, "exit"),
    ]
    while True:
        opts = []
        for label, cost, _ in items:
            opts.append(f"{label} ({cost}c)" if cost > 0 else label)
        choice = show_menu("NABI TRADING POST", opts, subtitle=f"Coins: {player_stats['coins']}/500")
        label, cost, action = items[choice]
        if action == "exit":
            save_game(); return
        if cost > 0 and player_stats["coins"] < cost:
            play_sound("error"); show_message("Not enough coins!", C_RED, 1200); continue
        play_sound("shop_buy")
        player_stats["coins"] -= cost
        msg = ""
        if action == "hp_restore":
            player_stats["hp"] = player_stats["max_hp"]; msg = "Health fully restored!"
        elif action == "dp_restore":
            player_stats["def"] = player_stats["max_def"]; msg = "Shield fully repaired!"
        elif action == "atk_buff":
            player_stats["atk"] += 5; msg = f"ATK is now {player_stats['atk']}!"
        elif action == "dp_buff":
            player_stats["max_def"] += 5; player_stats["def"] = player_stats["max_def"]
            msg = f"Max Shield is now {player_stats['max_def']}!"
        elif action == "hp_pot":
            player_stats["inventory"]["hp_potions"] += 1
            msg = f"HP Potion added! ({player_stats['inventory']['hp_potions']})"
        elif action == "dp_pot":
            player_stats["inventory"]["dp_potions"] += 1
            msg = f"Shield Potion added! ({player_stats['inventory']['dp_potions']})"
        elif action == "hp_upgrade":
            player_stats["max_hp"] += 20; player_stats["hp"] += 20
            msg = f"Max HP is now {player_stats['max_hp']}!"
        elif action == "dp_upgrade":
            player_stats["max_def"] += 10; player_stats["def"] = player_stats["max_def"]
            msg = f"Max Shield is now {player_stats['max_def']}!"
        show_message(msg, C_GREEN, 1500)


# ---------------------------------------------------------------------------
#  LOOT BOX
# ---------------------------------------------------------------------------
def loot_box_screen(is_cursed=False):
    bg.set_static(load_bg("loot"))
    fade_transition(300)

    if is_cursed:
        play_sound("cursed_loot")
        roll = random.randint(1, 4)
        results = {
            1: ("DARK BLESSING: ATK +15!", C_PURPLE, lambda: player_stats.__setitem__("atk", player_stats["atk"] + 15)),
            2: (f"NEEDLE TRAP: Lost {int(player_stats['hp']*0.3)} HP!", C_RED, lambda: player_stats.__setitem__("hp", player_stats["hp"] - int(player_stats["hp"]*0.3))),
            3: ("OMEN: Cowardice +2!", C_PURPLE, lambda: player_stats.__setitem__("cowardice", player_stats["cowardice"] + 2)),
            4: ("MIMIC! Lost 20 HP!", C_RED, lambda: player_stats.__setitem__("hp", player_stats["hp"] - 20)),
        }
        msg, color, fn = results[roll]; fn()
        title = "CURSED LOOT BOX"
    else:
        play_sound("loot_open")
        roll = random.randint(1, 4)
        if roll == 1:
            up = random.randint(10, 30)
            player_stats["max_hp"] += up; player_stats["hp"] = player_stats["max_hp"]
            msg, color = f"Health Upgrade! Max HP {player_stats['max_hp']}", C_GREEN
        elif roll == 2:
            weapons = {"Iron Blade": 35, "Dragon Claw": 50, "Demon Slayer": 75}
            wn, wa = random.choice(list(weapons.items()))
            if wa > player_stats["atk"]:
                player_stats["atk"] = wa; msg = f"New Weapon: {wn} (ATK {wa})!"
            else:
                player_stats["atk"] += 5; msg = "Weapon sharpened! ATK +5"
            color = C_GOLD
        elif roll == 3:
            player_stats["max_def"] += 10; player_stats["def"] = player_stats["max_def"]
            msg, color = f"Shield Upgrade! Max DP {player_stats['max_def']}", C_BLUE
        else:
            if player_stats["cowardice"] > 0:
                player_stats["cowardice"] = 0; msg, color = "Holy Relic! Cowardice removed!", C_GOLD
            else:
                player_stats["coins"] = min(500, player_stats["coins"] + 100)
                msg, color = "Treasure! +100 coins!", C_GOLD
        title = "MYSTERY LOOT BOX"

    box_color = C_PURPLE if is_cursed else C_GOLD
    def draw_box(t):
        size = 80 + int(math.sin(t * math.pi * 4) * 20)
        cx, cy = SCREEN_W // 2, 250
        pygame.draw.rect(screen, box_color, (cx - size//2, cy - size//2, size, size), border_radius=8)
        pygame.draw.rect(screen, C_WHITE, (cx - size//2, cy - size//2, size, size), 3, border_radius=8)
        draw_text(title, font_lg, box_color, SCREEN_W // 2, 130, "center")
        draw_text("?", font_title, C_WHITE, cx, cy, "center")
    animate_frames(1200, draw_box)
    show_message(msg, color)


# ---------------------------------------------------------------------------
#  CHEAT MENU
# ---------------------------------------------------------------------------
def cheat_menu(log, enemies=None):
    """Show cheat submenu. Returns (action, log_entries).
    enemies is a list of dicts with 'hp' keys for arcade multi-enemy."""
    cheats = [
        "Kill All Enemies",
        "Godmode (999 HP/ATK/DEF)",
        "Full Heal + Shield",
        "Max Coins (500)",
        "Level Up",
        "Max Combo",
        "Back",
    ]
    ch = show_menu("CHEAT CODES", cheats)
    if ch == 0:
        if enemies:
            for e in enemies:
                e["hp"] = 0
        log.append("[CHEAT] Forbidden spell! All enemies slain!")
        return "kill"
    elif ch == 1:
        player_stats["hp"] = player_stats["max_hp"] = 999
        player_stats["atk"] = 999
        player_stats["def"] = player_stats["max_def"] = 999
        player_stats["combo"] = COMBO_MAX
        log.append("[CHEAT] GODMODE activated!")
        return "godmode"
    elif ch == 2:
        player_stats["hp"] = player_stats["max_hp"]
        player_stats["def"] = player_stats["max_def"]
        log.append("[CHEAT] Fully healed + shield restored!")
        return "heal"
    elif ch == 3:
        player_stats["coins"] = 500
        log.append("[CHEAT] Wallet maxed to 500 coins!")
        return "coins"
    elif ch == 4:
        player_stats["xp"] += 100
        gain_xp(0)
        log.append(f"[CHEAT] Level Up! Now Lv.{player_stats['level']}")
        return "levelup"
    elif ch == 5:
        player_stats["combo"] = COMBO_MAX
        log.append("[CHEAT] Combo meter maxed!")
        return "combo"
    return "back"


# ---------------------------------------------------------------------------
#  COMBAT
# ---------------------------------------------------------------------------
def combat_screen(enemy_name):
    bg.set_static(load_bg("combat"))
    fade_transition(300)

    lvl_bonus = player_stats["level"] * 10
    c_mult = 1 + (player_stats.get("cowardice", 0) * 0.2)
    e_hp = int(random.randint(50 + lvl_bonus, 100 + lvl_bonus) * c_mult)
    e_max_hp = e_hp
    e_atk = int(random.randint(15 + player_stats["level"], 25 + player_stats["level"] * 2) * c_mult)
    e_max_atk = e_atk
    e_dp = int(random.randint(5 + player_stats["level"], 15 + player_stats["level"]) * c_mult)

    en_lower = enemy_name.lower()
    enemy_sheet = spr_dan_idle
    enemy_attack_sheet = spr_dan_angry
    for key, (idle, attack) in ENEMY_SPRITES.items():
        if key in en_lower:
            enemy_sheet = idle
            enemy_attack_sheet = attack
            break
    enemy_sprite = AnimatedSprite(enemy_sheet, SCREEN_W - 300, 280, fps=5)
    enemy_sprite.flip_h = True

    player_sprite.set_sheet(spr_player_idle)
    player_sprite.set_pos(150, 280)

    if "demon" in en_lower or "malachar" in en_lower:
        play_sound("demon_roar")

    log = [f"Battle: {player_name} vs {enemy_name}!"]
    if player_stats.get("cowardice", 0) > 0:
        log.append(f"CURSE: Cowardice ({player_stats['cowardice']}) empowers the enemy!")

    shake_timer = 0

    while player_stats["hp"] > 0 and e_hp > 0:
        # Build action list — add Special when combo is ready
        actions = ["Attack", "Parry", "Use Item", "Run", "Shop", "Cheats"]
        if player_stats.get("combo", 0) >= COMBO_MAX:
            actions.insert(3, "Special")
        actions.append("Quit")

        buttons = []
        key_list = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                    pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
        for i, act in enumerate(actions):
            bw, bh = 120, 38
            col_i = i % 4; row_i = i // 4
            bx = 30 + col_i * (bw + 8)
            by = SCREEN_H - 100 + row_i * (bh + 8)
            btn_color = C_GOLD if act == "Special" else C_PANEL_LIGHT
            buttons.append(Button((bx, by, bw, bh), f"{i+1}.{act}", font=font_sm,
                                  color=btn_color, key=key_list[i] if i < len(key_list) else None))

        action_idx = None
        while action_idx is None:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_game(); pygame.quit(); sys.exit()
                if event.type == pygame.VIDEORESIZE:
                    handle_resize(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pause_menu()
                for i, btn in enumerate(buttons):
                    if btn.clicked(event):
                        play_sound("menu_click"); action_idx = i; break
                if action_idx is not None:
                    break

            dt = clock.tick(FPS) / 1000
            bg.update(dt)
            bg.draw(screen)

            sx = random.randint(-2, 2) if shake_timer > 0 else 0
            sy = random.randint(-2, 2) if shake_timer > 0 else 0
            shake_timer = max(0, shake_timer - dt)

            player_sprite.update(dt)
            enemy_sprite.update(dt)

            old_ex, old_ey = enemy_sprite.x, enemy_sprite.y
            enemy_sprite.x += sx; enemy_sprite.y += sy
            player_sprite.draw(screen)
            enemy_sprite.draw(screen)
            enemy_sprite.x, enemy_sprite.y = old_ex, old_ey

            draw_panel((SCREEN_W - 320, 40, 300, 100), fill=(50, 20, 20))
            draw_text(enemy_name, font_lg, C_RED, SCREEN_W - 170, 55, "center")
            draw_bar(SCREEN_W - 300, 95, 260, 22, max(0, e_hp), e_max_hp, C_RED, C_HP_BG,
                     f"HP {max(0,e_hp)}/{e_max_hp}")
            draw_text(f"ATK: {e_atk}", font_sm, C_TEXT_DIM, SCREEN_W - 300, 125)
            draw_stat_panel(20, 40)

            draw_panel((20, SCREEN_H - 250, SCREEN_W - 40, 130), fill=(20, 20, 30))
            ly = SCREEN_H - 242
            for entry in log[-6:]:
                draw_text(entry, font_sm, C_TEXT, 35, ly, max_width=SCREEN_W - 80)
                ly += 20

            for btn in buttons:
                btn.update(mouse_pos); btn.draw()
            pygame.display.flip()

        chosen_action = actions[action_idx]

        if chosen_action == "Quit":
            return "menu"

        if chosen_action == "Cheats":
            cheat_result = cheat_menu(log)
            if cheat_result == "kill":
                e_hp = 0; break
            bg.set_static(load_bg("combat"))
            continue

        did_parry = False

        if chosen_action == "Attack":
            play_sound("attack_hit")
            player_sprite.set_sheet(spr_player_attack)
            player_sprite.move_to(350, 280)
            wait_for_movement([player_sprite, enemy_sprite], 500)
            e_hp -= player_stats["atk"]
            add_combo()
            log.append(f"You strike for {player_stats['atk']}! Combo +{COMBO_PER_ATTACK}")
            player_sprite.move_to(150, 280)
            player_sprite.set_sheet(spr_player_idle)
            shake_timer = 0.3

        elif chosen_action == "Parry":
            did_parry = True
            play_sound("defend")
            player_sprite.set_sheet(spr_player_defend)
            log.append("You raise your guard!")

        elif chosen_action == "Special":
            spec_ch = show_menu("COMBO SPECIAL", [
                f"Power Strike (2.5x ATK, costs {POWER_STRIKE_DP_COST} DP)",
                "Shield Restore (full DP repair)",
                "Back",
            ])
            if spec_ch == 0:
                if can_power_strike():
                    play_sound("attack_hit")
                    player_sprite.set_sheet(spr_player_attack)
                    player_sprite.move_to(350, 280)
                    wait_for_movement([player_sprite, enemy_sprite], 500)
                    dmg = do_power_strike(log)
                    e_hp -= dmg
                    player_sprite.move_to(150, 280)
                    player_sprite.set_sheet(spr_player_idle)
                    shake_timer = 0.5
                else:
                    log.append(f"Need {POWER_STRIKE_DP_COST} DP for Power Strike!")
                    continue
            elif spec_ch == 1:
                if can_shield_restore():
                    do_shield_restore(log)
                    play_sound("potion")
                else:
                    log.append("Combo not ready!")
                    continue
            else:
                continue

        elif chosen_action == "Use Item":
            hp_c = player_stats["inventory"]["hp_potions"]
            dp_c = player_stats["inventory"]["dp_potions"]
            ch = show_menu("USE ITEM", [f"HP Potion ({hp_c})", f"Shield Potion ({dp_c})", "Back"])
            if ch == 0 and hp_c > 0:
                play_sound("potion"); player_stats["hp"] = player_stats["max_hp"]
                player_stats["inventory"]["hp_potions"] -= 1; log.append("Used HP Potion!"); continue
            elif ch == 1 and dp_c > 0:
                play_sound("potion"); player_stats["def"] = player_stats["max_def"]
                player_stats["inventory"]["dp_potions"] -= 1; log.append("Shield restored!"); continue
            elif ch in (0, 1):
                play_sound("error"); show_message("No potions!", C_RED, 1000)
            continue

        elif chosen_action == "Run":
            if random.random() < 0.5:
                play_sound("flee")
                player_stats["cowardice"] = player_stats.get("cowardice", 0) + 1
                player_sprite.move_to(-150, 280)
                wait_for_movement([player_sprite], 800)
                show_message(f"Escaped! Cowardice: {player_stats['cowardice']}", C_ORANGE, 1500)
                return "escaped"
            else:
                log.append(f"Failed to escape! {enemy_name} blocks you!")

        elif chosen_action == "Shop":
            shop_screen(); bg.set_static(load_bg("combat")); continue

        # Enemy turn
        if e_hp > 0:
            enemy_sprite.set_sheet(enemy_attack_sheet)
            enemy_sprite.move_to(350, 280)
            wait_for_movement([player_sprite, enemy_sprite], 500)

            if did_parry:
                counter_dmg = apply_parry(e_atk, e_max_atk, log, enemy_name)
                if counter_dmg > 0:
                    e_hp -= counter_dmg
                    shake_timer = 0.3
                if player_stats["hp"] < player_stats["max_hp"]:
                    play_sound("player_hurt")
                    shake_timer = 0.3
                player_sprite.set_sheet(spr_player_idle)
            else:
                play_sound("player_hurt")
                apply_damage_to_player(e_atk, log, enemy_name)
                player_sprite.set_sheet(spr_player_hurt)
                shake_timer = 0.3

            enemy_sprite.move_to(SCREEN_W - 300, 280)
            enemy_sprite.set_sheet(enemy_sheet)
            wait_for_movement([player_sprite, enemy_sprite], 500)
            player_sprite.set_sheet(spr_player_idle)

    # Result
    if player_stats["hp"] > 0:
        play_sound("victory")
        player_stats["cowardice"] = 0
        loot = drop_coins(); play_sound("coin")
        leveled = gain_xp(50); save_game()
        lines = ["VICTORY!", f"Gained {loot} coins!", "Gained 50 XP!"]
        if leveled:
            play_sound("level_up"); lines.append(f"LEVEL UP! Now Level {player_stats['level']}!")
        typewriter(lines, [player_sprite], narrator_visible=False)
        return "victory"
    else:
        player_stats["hp"] = 0; player_stats["cowardice"] = 0
        play_sound("defeat"); save_game()
        bg.set_static(load_bg("gameover"))
        typewriter([f"{player_name} has fallen...", "--- GAME OVER ---"], [], narrator_visible=False)
        return "defeat"


# ---------------------------------------------------------------------------
#  ARCADE MODE
# ---------------------------------------------------------------------------
def arcade_save_highscore(score, waves):
    """Save arcade high score."""
    data = {}
    if os.path.exists(ARCADE_SAVE_FILE):
        try:
            with open(ARCADE_SAVE_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            pass
    if score > data.get("high_score", 0):
        data["high_score"] = score
        data["high_wave"] = waves
        data["player"] = player_name
    try:
        with open(ARCADE_SAVE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass
    return data.get("high_score", score)


def arcade_get_highscore():
    if os.path.exists(ARCADE_SAVE_FILE):
        try:
            with open(ARCADE_SAVE_FILE, "r") as f:
                data = json.load(f)
            return data.get("high_score", 0), data.get("high_wave", 0)
        except Exception:
            pass
    return 0, 0


def spawn_arcade_wave(wave_num):
    """Create a list of enemy dicts for the given wave. Up to 3 enemies."""
    count = min(3, 1 + (wave_num - 1) // 2)
    scale = 1.0 + (wave_num - 1) * 0.15
    available = list(MONSTER_TYPES)
    enemies = []
    used_types = set()
    for i in range(count):
        candidates = [m for m in available if m["name"] not in used_types]
        if not candidates:
            candidates = available
        mtype = random.choice(candidates)
        used_types.add(mtype["name"])
        hp = int(mtype["base_hp"] * scale)
        atk = int(mtype["base_atk"] * scale)
        dp = int(mtype["base_def"] * scale)
        # Position enemies spread across right side of screen
        x_positions = {1: [SCREEN_W - 260], 2: [SCREEN_W - 320, SCREEN_W - 180],
                       3: [SCREEN_W - 380, SCREEN_W - 240, SCREEN_W - 100]}
        y_positions = {1: [260], 2: [230, 310], 3: [200, 280, 360]}
        ex = x_positions[count][i]
        ey = y_positions[count][i]
        sprite = AnimatedSprite(mtype["idle"], ex, ey, fps=5)
        sprite.flip_h = True
        enemies.append({
            "name": mtype["name"],
            "type": mtype,
            "hp": hp, "max_hp": hp, "atk": atk, "max_atk": atk, "def": dp,
            "sprite": sprite,
            "pattern": mtype["pattern"],
            "color": mtype["color"],
            "poison_turns": 0,
            "frozen": False,
        })
    return enemies


def arcade_combat(wave_num, enemies):
    """Multi-enemy combat for arcade mode. Returns 'victory' or 'defeat'."""
    bg.set_static(load_bg("arcade"))
    fade_transition(300)

    player_sprite.set_sheet(spr_player_idle)
    player_sprite.set_pos(120, 280)

    log = [f"--- WAVE {wave_num} ---"]
    names = ", ".join(e["name"] for e in enemies)
    log.append(f"Enemies: {names}")

    shake_timer = 0
    frozen_turn = False

    while player_stats["hp"] > 0 and any(e["hp"] > 0 for e in enemies):
        alive_enemies = [e for e in enemies if e["hp"] > 0]

        # Poison tick — damage goes through shield system
        for e in alive_enemies:
            if e.get("poison_turns", 0) > 0:
                poison_dmg = max(1, e["atk"] // 4)
                apply_damage_to_player(poison_dmg, log, f"Poison({e['name']})")
                e["poison_turns"] -= 1

        if player_stats["hp"] <= 0:
            break

        # Check frozen
        if frozen_turn:
            log.append("You are FROZEN and cannot act!")
            frozen_turn = False
        else:
            # Player selects target and action
            target_idx = 0
            if len(alive_enemies) > 1:
                target_names = [f"{e['name']} (HP:{e['hp']})" for e in alive_enemies]
                target_idx = show_menu("SELECT TARGET", target_names)

            actions = ["Attack", "Parry", "Use Item", "Shop", "Cheats"]
            if player_stats.get("combo", 0) >= COMBO_MAX:
                actions.insert(3, "Special")
            actions.append("Quit")

            buttons = []
            key_list = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                        pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]
            for i, act in enumerate(actions):
                bw, bh = 120, 38
                col_i = i % 4; row_i = i // 4
                bx = 30 + col_i * (bw + 8)
                by = SCREEN_H - 100 + row_i * (bh + 8)
                btn_color = C_GOLD if act == "Special" else C_PANEL_LIGHT
                buttons.append(Button((bx, by, bw, bh), f"{i+1}.{act}", font=font_sm,
                                      color=btn_color, key=key_list[i] if i < len(key_list) else None))

            action_idx = None
            while action_idx is None:
                mouse_pos = pygame.mouse.get_pos()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        save_game(); pygame.quit(); sys.exit()
                    if event.type == pygame.VIDEORESIZE:
                        handle_resize(event)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pause_menu()
                    for i, btn in enumerate(buttons):
                        if btn.clicked(event):
                            play_sound("menu_click"); action_idx = i; break
                    if action_idx is not None:
                        break

                dt = clock.tick(FPS) / 1000
                bg.update(dt)
                bg.draw(screen)

                sx = random.randint(-2, 2) if shake_timer > 0 else 0
                sy = random.randint(-2, 2) if shake_timer > 0 else 0
                shake_timer = max(0, shake_timer - dt)

                player_sprite.update(dt)
                player_sprite.draw(screen)

                for ei, e in enumerate(alive_enemies):
                    e["sprite"].update(dt)
                    old_x, old_y = e["sprite"].x, e["sprite"].y
                    e["sprite"].x += sx; e["sprite"].y += sy
                    e["sprite"].draw(screen)
                    e["sprite"].x, e["sprite"].y = old_x, old_y

                # Draw enemy HP bars
                for ei, e in enumerate(alive_enemies):
                    panel_x = SCREEN_W - 340
                    panel_y = 30 + ei * 80
                    draw_panel((panel_x, panel_y, 320, 70), fill=(50, 20, 20))
                    draw_text(e["name"], font_sm, e["color"], panel_x + 160, panel_y + 5, "center")
                    draw_bar(panel_x + 10, panel_y + 28, 200, 16, max(0, e["hp"]), e["max_hp"],
                             C_RED, C_HP_BG, f"HP {max(0,e['hp'])}/{e['max_hp']}")
                    draw_text(f"ATK:{e['atk']}", font_sm, C_TEXT_DIM, panel_x + 220, panel_y + 28)
                    pattern_label = e["pattern"].upper()
                    draw_text(pattern_label, font_sm, e["color"], panel_x + 220, panel_y + 48)
                    if ei == target_idx:
                        pygame.draw.rect(screen, C_GOLD, (panel_x - 2, panel_y - 2, 324, 74), 2, border_radius=6)

                draw_stat_panel(20, 40)
                draw_text(f"WAVE {wave_num}", font_lg, C_GOLD, SCREEN_W // 2, 8, "center")

                draw_panel((20, SCREEN_H - 250, SCREEN_W - 40, 130), fill=(20, 20, 30))
                ly = SCREEN_H - 242
                for entry in log[-5:]:
                    draw_text(entry, font_sm, C_TEXT, 35, ly, max_width=SCREEN_W - 80)
                    ly += 20

                for btn in buttons:
                    btn.update(mouse_pos); btn.draw()
                pygame.display.flip()

            chosen_action = actions[action_idx]

            if chosen_action == "Quit":
                return "menu"

            if chosen_action == "Cheats":
                cheat_result = cheat_menu(log, enemies=alive_enemies)
                if cheat_result == "kill":
                    for e in enemies:
                        e["hp"] = 0
                    break
                bg.set_static(load_bg("arcade"))
                continue

            target_enemy = alive_enemies[target_idx]
            did_parry = False

            if chosen_action == "Attack":
                play_sound("attack_hit")
                player_sprite.set_sheet(spr_player_attack)
                player_sprite.move_to(target_enemy["sprite"].x - 80, target_enemy["sprite"].y)
                wait_for_movement([player_sprite] + [e["sprite"] for e in alive_enemies], 500)
                target_enemy["hp"] -= player_stats["atk"]
                add_combo()
                log.append(f"You strike {target_enemy['name']} for {player_stats['atk']}! Combo +{COMBO_PER_ATTACK}")
                if target_enemy["hp"] <= 0:
                    log.append(f"{target_enemy['name']} defeated!")
                    target_enemy["sprite"].visible = False
                player_sprite.move_to(120, 280)
                player_sprite.set_sheet(spr_player_idle)
                shake_timer = 0.3

            elif chosen_action == "Parry":
                did_parry = True
                play_sound("defend")
                player_sprite.set_sheet(spr_player_defend)
                log.append("You raise your guard!")

            elif chosen_action == "Special":
                spec_ch = show_menu("COMBO SPECIAL", [
                    f"Power Strike (2.5x ATK, costs {POWER_STRIKE_DP_COST} DP)",
                    "Shield Restore (full DP repair)",
                    "Back",
                ])
                if spec_ch == 0:
                    if can_power_strike():
                        play_sound("attack_hit")
                        player_sprite.set_sheet(spr_player_attack)
                        player_sprite.move_to(target_enemy["sprite"].x - 80, target_enemy["sprite"].y)
                        wait_for_movement([player_sprite] + [e["sprite"] for e in alive_enemies], 500)
                        dmg = do_power_strike(log)
                        target_enemy["hp"] -= dmg
                        if target_enemy["hp"] <= 0:
                            log.append(f"{target_enemy['name']} defeated!")
                            target_enemy["sprite"].visible = False
                        player_sprite.move_to(120, 280)
                        player_sprite.set_sheet(spr_player_idle)
                        shake_timer = 0.5
                    else:
                        log.append(f"Need {POWER_STRIKE_DP_COST} DP for Power Strike!")
                        continue
                elif spec_ch == 1:
                    if can_shield_restore():
                        do_shield_restore(log)
                        play_sound("potion")
                    else:
                        log.append("Combo not ready!")
                        continue
                else:
                    continue

            elif chosen_action == "Use Item":
                hp_c = player_stats["inventory"]["hp_potions"]
                dp_c = player_stats["inventory"]["dp_potions"]
                ch = show_menu("USE ITEM", [f"HP Potion ({hp_c})", f"Shield Potion ({dp_c})", "Back"])
                if ch == 0 and hp_c > 0:
                    play_sound("potion"); player_stats["hp"] = player_stats["max_hp"]
                    player_stats["inventory"]["hp_potions"] -= 1; log.append("Used HP Potion!"); continue
                elif ch == 1 and dp_c > 0:
                    play_sound("potion"); player_stats["def"] = player_stats["max_def"]
                    player_stats["inventory"]["dp_potions"] -= 1; log.append("Shield restored!"); continue
                elif ch in (0, 1):
                    play_sound("error"); show_message("No potions!", C_RED, 1000)
                continue

            elif chosen_action == "Shop":
                shop_screen(); bg.set_static(load_bg("arcade")); continue

        # Enemy turns
        alive_after = [e for e in enemies if e["hp"] > 0]
        for e in alive_after:
            if player_stats["hp"] <= 0:
                break

            e["sprite"].set_sheet(e["type"]["attack"])

            # Apply attack pattern
            actual_atk = e["atk"]
            if e["pattern"] == "aggressive":
                actual_atk = int(e["atk"] * 1.2)
            elif e["pattern"] == "berserker":
                hp_ratio = e["hp"] / max(1, e["max_hp"])
                actual_atk = int(e["atk"] * (1.0 + (1.0 - hp_ratio) * 0.5))
            elif e["pattern"] == "tank":
                actual_atk = int(e["atk"] * 0.8)
            elif e["pattern"] == "evasive":
                if random.random() < 0.3:
                    log.append(f"{e['name']} phases through reality and dodges!")
                    e["sprite"].set_sheet(e["type"]["idle"])
                    continue

            # Special effects based on pattern
            if e["pattern"] == "poison" and random.random() < 0.4:
                e["poison_turns"] = 3
                log.append(f"{e['name']} inflicts POISON!")

            if e["pattern"] == "freeze" and random.random() < 0.25:
                frozen_turn = True
                log.append(f"{e['name']} FREEZES you!")

            e["sprite"].move_to(300, 280)
            wait_for_movement([player_sprite, e["sprite"]], 400)

            if did_parry and not frozen_turn:
                e_max_a = e.get("max_atk", e["atk"])
                counter_dmg = apply_parry(actual_atk, e_max_a, log, e["name"])
                if counter_dmg > 0:
                    e["hp"] -= counter_dmg
                    if e["hp"] <= 0:
                        log.append(f"{e['name']} defeated by counter!")
                        e["sprite"].visible = False
                    shake_timer = 0.2
                if player_stats["hp"] < player_stats["max_hp"]:
                    play_sound("player_hurt")
                    shake_timer = 0.2
            else:
                play_sound("player_hurt")
                apply_damage_to_player(actual_atk, log, e["name"])
                player_sprite.set_sheet(spr_player_hurt)
                shake_timer = 0.2

            # Move enemy back
            alive_list = [ae for ae in enemies if ae["hp"] > 0]
            idx_in_alive = alive_list.index(e) if e in alive_list else 0
            cnt = len(alive_list)
            x_positions = {1: [SCREEN_W - 260], 2: [SCREEN_W - 320, SCREEN_W - 180],
                           3: [SCREEN_W - 380, SCREEN_W - 240, SCREEN_W - 100]}
            y_positions = {1: [260], 2: [230, 310], 3: [200, 280, 360]}
            if cnt in x_positions and idx_in_alive < cnt:
                e["sprite"].move_to(x_positions[cnt][idx_in_alive], y_positions[cnt][idx_in_alive])
            else:
                e["sprite"].move_to(SCREEN_W - 260, 260)
            wait_for_movement([player_sprite, e["sprite"]], 400)
            e["sprite"].set_sheet(e["type"]["idle"])
            player_sprite.set_sheet(spr_player_idle)

    # Result
    if player_stats["hp"] > 0:
        return "victory"
    else:
        player_stats["hp"] = 0
        return "defeat"


def arcade_mode():
    """Main arcade mode loop."""
    global player_stats

    # Reset stats for arcade
    player_stats = copy.deepcopy(DEFAULT_PLAYER_STATS)
    player_stats["hp"] = player_stats["max_hp"]
    player_stats["def"] = player_stats["max_def"]
    player_stats["combo"] = 0

    high_score, high_wave = arcade_get_highscore()

    bg.set_static(load_bg("arcade"))
    fade_transition(400)

    typewriter([
        "Welcome to the ARCADE!",
        "Fight endless waves of monsters!",
        "How long can you survive?",
        f"High Score: {high_score} (Wave {high_wave})",
    ], [player_sprite], narrator_visible=True)

    wave = 0
    score = 0

    while player_stats["hp"] > 0:
        wave += 1
        enemies = spawn_arcade_wave(wave)

        bg.set_static(load_bg("arcade"))
        names = " + ".join(e["name"] for e in enemies)
        show_message(f"WAVE {wave}: {names}", C_GOLD, 2000)

        result = arcade_combat(wave, enemies)

        if result == "menu":
            arcade_save_highscore(score, wave - 1)
            return

        if result == "defeat":
            play_sound("defeat")
            bg.set_static(load_bg("gameover"))
            final_hs = arcade_save_highscore(score, wave - 1)
            typewriter([
                f"{player_name} has fallen at Wave {wave}!",
                f"Final Score: {score}",
                f"High Score: {final_hs}",
                "--- GAME OVER ---",
            ], [], narrator_visible=False)
            return

        # Victory rewards
        play_sound("victory")
        wave_score = wave * 100 + len(enemies) * 50
        score += wave_score
        loot = drop_coins()
        play_sound("coin")
        leveled = gain_xp(30 + wave * 10)

        lines = [
            f"Wave {wave} cleared!",
            f"+{wave_score} score (Total: {score})",
            f"+{loot} coins",
        ]
        if leveled:
            play_sound("level_up")
            lines.append(f"LEVEL UP! Now Level {player_stats['level']}!")

        bg.set_static(load_bg("arcade"))
        typewriter(lines, [player_sprite], narrator_visible=False)

        # Offer shop between waves
        if wave % 2 == 0:
            ch = show_menu(f"WAVE {wave} COMPLETE", ["Continue Fighting", "Visit Shop", "Quit Arcade"])
            if ch == 1:
                shop_screen()
            elif ch == 2:
                arcade_save_highscore(score, wave)
                return
        save_game()

    # If somehow we exit the loop
    arcade_save_highscore(score, wave)


# ---------------------------------------------------------------------------
#  STORY SCENES
# ---------------------------------------------------------------------------
def scene_intro():
    bg.layers = []
    bg.add_layer(load_bg("forest_sky"), 0)
    bg.add_layer(load_bg("forest_far_trees"), 8)
    bg.add_layer(load_bg("forest_fog"), 15)
    bg.add_layer(load_bg("forest_near_trees"), 25)
    fade_transition(400)

    narrator_sprite.set_pos(50, 300)
    narrator_sprite.visible = True
    player_sprite.set_sheet(spr_player_idle)
    player_sprite.set_pos(-150, 380)
    player_sprite.move_to(200, 380)
    wait_for_movement([player_sprite], 2000)

    typewriter([
        f"Welcome {player_name}, to the world of NABI!",
        "",
        "A world full of mystery and adventure.",
        f"The choice is yours, Brave warrior {player_name}!",
    ], [player_sprite])


def scene_forest():
    global dan_patience
    bg.layers = []
    bg.add_layer(load_bg("forest_sky"), 0)
    bg.add_layer(load_bg("forest_far_trees"), 8)
    bg.add_layer(load_bg("forest_fog"), 15)
    bg.add_layer(load_bg("forest_near_trees"), 25)

    player_sprite.set_sheet(spr_player_idle)
    player_sprite.set_pos(200, 380)

    def _reset_forest_bg():
        bg.layers = []
        bg.add_layer(load_bg("forest_sky"), 0)
        bg.add_layer(load_bg("forest_far_trees"), 8)
        bg.add_layer(load_bg("forest_fog"), 15)
        bg.add_layer(load_bg("forest_near_trees"), 25)

    def _walk_back_to_forest():
        _reset_forest_bg()
        player_sprite.set_sheet(spr_player_walk)
        player_sprite.set_pos(-100, 380)
        player_sprite.move_to(200, 380)
        wait_for_movement([player_sprite], 1500)
        player_sprite.set_sheet(spr_player_idle)

    while True:
        choice = show_menu("THE DARK FOREST",
                           ["Go Right (Dan's Field)", "Go Left (Haunted Ruins)",
                            "Go Straight (Mountain Pass)", "Shop", "Leave Forest"],
                           [player_sprite],
                           subtitle="Three paths stretch before you...")
        save_game()

        if choice == 4:
            typewriter(["You decide to head back..."], [player_sprite])
            return "menu"
        elif choice == 3:
            result = shop_screen()
            _reset_forest_bg()
            continue
        elif choice == 1:
            player_sprite.set_sheet(spr_player_walk)
            player_sprite.move_to(-100, 380)
            wait_for_movement([player_sprite], 1500)
            result = scene_ruins()
            if result in ("victory", "victory_end", "defeat", "gameover"):
                return result
            _walk_back_to_forest()
            continue
        elif choice == 2:
            player_sprite.set_sheet(spr_player_walk)
            player_sprite.move_to(SCREEN_W + 100, 380)
            wait_for_movement([player_sprite], 1500)
            result = scene_mountain()
            if result in ("victory", "victory_end", "defeat", "gameover"):
                return result
            _walk_back_to_forest()
            continue
        elif choice == 0:
            player_sprite.set_sheet(spr_player_walk)
            player_sprite.move_to(SCREEN_W + 100, 380)
            wait_for_movement([player_sprite], 1500)
            result = scene_dan_field()
            if result in ("victory", "victory_end", "defeat", "gameover"):
                return result
            _walk_back_to_forest()
            continue


def scene_dan_field():
    global dan_patience
    bg.set_static(load_bg("field"))
    fade_transition(300)

    player_sprite.set_sheet(spr_player_walk)
    player_sprite.set_pos(-100, 380)
    dan_sprite.set_sheet(spr_dan_idle)
    dan_sprite.set_pos(650, 380)

    player_sprite.move_to(200, 380)
    wait_for_movement([player_sprite, dan_sprite], 1500)
    player_sprite.set_sheet(spr_player_idle)

    typewriter(["You arrive at the field of Dan.",
                "A man tends to his crops, eyeing you suspiciously."],
               [player_sprite, dan_sprite])

    choice = show_menu("DAN'S FIELD", ["Speak to Dan", "Go Back to Forest"], [player_sprite, dan_sprite])

    if choice == 1:
        dan_patience = 0
        player_sprite.set_sheet(spr_player_walk)
        player_sprite.flip_h = True
        player_sprite.move_to(-100, 380)
        wait_for_movement([player_sprite], 1500)
        player_sprite.flip_h = False
        typewriter(["You turn back. Maybe next time."], [])
        return None

    dan_patience += 1

    if dan_patience >= 3:
        return scene_dan_transforms()

    # Walk toward Dan
    player_sprite.set_sheet(spr_player_walk)
    player_sprite.move_to(400, 380)
    wait_for_movement([player_sprite, dan_sprite], 1000)
    player_sprite.set_sheet(spr_player_idle)

    typewriter([
        "Dan: And you are?",
        f"You: I am called {player_name}.",
        f"Dan: Hm, {player_name}. Interesting name.",
        "Dan: What brings you here?",
    ], [player_sprite, dan_sprite])

    reason = show_menu("RESPOND TO DAN", [
        "I'm looking for adventure",
        "Just passing through",
        "None of your business",
        "I am lost and need help",
        "Leave"
    ], [player_sprite, dan_sprite])

    if reason == 0:
        dan_sprite.set_sheet(spr_dan_angry)
        typewriter(["Dan: An adventure? I ain't got none, now scram!",
                    "You: How rude!"], [player_sprite, dan_sprite])
        dan_sprite.set_sheet(spr_dan_idle)
    elif reason == 1:
        typewriter(["Dan: Just passing through? Safe travels, but go away!"], [player_sprite, dan_sprite])
    elif reason == 2:
        dan_sprite.set_sheet(spr_dan_angry)
        typewriter(["Dan: No need to be rude! Mind your business then."], [player_sprite, dan_sprite])
        dan_sprite.set_sheet(spr_dan_idle)
    elif reason == 3:
        return scene_dan_option4()
    elif reason == 4:
        typewriter(["You decide to leave Dan alone."], [player_sprite, dan_sprite])
        return None

    if dan_patience == 1:
        dan_sprite.set_sheet(spr_dan_angry)
        typewriter(["Dan: I don't have time for this. Go away!"], [player_sprite, dan_sprite])
        dan_sprite.set_sheet(spr_dan_idle)
    elif dan_patience == 2:
        dan_sprite.set_sheet(spr_dan_angry)
        typewriter(["Dan: (Vein throbbing) I'm warning you... leave. Now."], [player_sprite, dan_sprite])
        dan_sprite.set_sheet(spr_dan_idle)

    return None


def scene_dan_transforms():
    bg.set_static(load_bg("field"))
    fade_transition(300)
    play_sound("demon_roar")

    dan_sprite.set_sheet(spr_dan_angry)
    typewriter(["Dan: THAT'S IT! I told you to leave!",
                "Dan: You mortals never know when to stop!"],
               [player_sprite, dan_sprite])

    # Transform animation
    dan_sprite.set_sheet(spr_dan_transform)
    dan_sprite.fps = 3
    def draw_transform(t):
        # Screen shake + red flash
        if t > 0.3:
            flash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            flash.fill((180, 0, 0, max(0, int(40 * math.sin(t * 10)))))
            screen.blit(flash, (0, 0))
        draw_text("--- TRANSFORMATION ---", font_lg, C_RED, SCREEN_W // 2, 30, "center")
        player_sprite.draw(screen)
        dan_sprite.update(1/60)
        dan_sprite.draw(screen)
    animate_frames(2000, draw_transform)

    dan_sprite.set_sheet(spr_demon_idle)
    dan_sprite.fps = 5

    typewriter(["Giant wings burst from his back!",
                "Dan transforms into a fearsome DEMON!",
                "HEHEHE! You're COOKED!"],
               [player_sprite, dan_sprite])

    result = combat_screen("Demon Dan")
    if result == "victory":
        bg.set_static(load_bg("field"))
        typewriter(["The demon crumbles to dust.", "You have proven yourself, warrior!"], [player_sprite])
        cellar_result = scene_dan_cellar()
        if cellar_result in ("victory_end", "defeat", "gameover"):
            return cellar_result
        return "continue"
    return result


def scene_dan_option4():
    typewriter(["Dan: Lost, are you?",
                "Dan: How about you rest for the night first?"],
               [player_sprite, dan_sprite])

    choice = show_menu("DAN'S OFFER", ["Accept Dan's offer", "Decline and continue", "Leave"], [player_sprite, dan_sprite])

    if choice == 2:
        typewriter(["You decide to leave Dan alone."], [player_sprite, dan_sprite])
        return None
    elif choice == 0:
        fade_transition(600)
        bg.set_static(load_bg("gameover"))
        typewriter(["You accept Dan's offer and spend the night...",
                    "However, he had poisoned your food.",
                    "You died in your sleep.",
                    "You naive fool!",
                    "--- GAME OVER ---"], [], narrator_visible=False)
        player_stats["hp"] = 0; save_game()
        return "gameover"
    else:
        typewriter(["You decline, sensing danger...",
                    "You confront Dan, but he escapes!",
                    "He's a demon worshipper!",
                    "He transforms into a demon!"],
                   [player_sprite, dan_sprite])
        play_sound("demon_roar")

        dan_sprite.set_sheet(spr_dan_transform)
        def draw_t2(t):
            player_sprite.draw(screen)
            dan_sprite.update(1/60); dan_sprite.draw(screen)
        animate_frames(1500, draw_t2)
        dan_sprite.set_sheet(spr_demon_idle)

        fight = show_menu("FIGHT THE DEMON?", ["Yes, fight!", "No, flee!", "Run away"], [player_sprite, dan_sprite])
        if fight in (1, 2):
            player_sprite.set_sheet(spr_player_walk)
            player_sprite.flip_h = True
            player_sprite.move_to(-150, 380)
            wait_for_movement([player_sprite], 1000)
            player_sprite.flip_h = False
            typewriter(["You flee from the demon. Thank the gods you're a COWARD!"], [])
            return None

        typewriter(["You want to fight a demon? Just Great!"], [player_sprite, dan_sprite])
        result = combat_screen("Demon Dan")
        if result == "victory":
            bg.set_static(load_bg("field"))
            typewriter(["The demon crumbles to dust!"], [player_sprite])
            cellar_result = scene_dan_cellar()
            if cellar_result in ("victory_end", "defeat", "gameover"):
                return cellar_result
            return "continue"
        return result


# ---------------------------------------------------------------------------
#  STORY EXPANSION — DAN CELLAR + DEMON TOWER (RIGHT PATH CONT.)
# ---------------------------------------------------------------------------
def scene_dan_cellar():
    bg.set_static(load_bg("cellar"))
    fade_transition(400)
    imp_sprite = AnimatedSprite(spr_imp_idle, 600, 350, fps=5)

    typewriter([
        "With Dan defeated, you notice the farmhouse door is ajar.",
        "A strange blue light flickers from below — a cellar.",
    ], [player_sprite])

    ch = show_menu("EXPLORE?", ["Explore the cellar", "Leave"], [player_sprite])
    if ch == 1:
        typewriter(["You leave the farm behind."], [player_sprite])
        return "continue"

    player_sprite.set_sheet(spr_player_walk)
    player_sprite.set_pos(-100, 380)
    player_sprite.move_to(200, 380)
    wait_for_movement([player_sprite], 1500)
    player_sprite.set_sheet(spr_player_idle)

    typewriter([
        "You descend crude stone steps. Sulphur and old paper.",
        "Ritual symbols, caged animals, and one surprised imp.",
        "",
        "Imp: 'OI! Who killed my master?!'",
        "Imp: '…Actually, if you're strong enough…'",
        "Imp: 'How'd you like a guide? I know every secret in Nabi.'",
    ], [player_sprite, imp_sprite])

    ch = show_menu("THE IMP", [
        "Accept the imp as your guide",
        "Attack it",
        "Ignore it and loot the cellar",
    ], [player_sprite, imp_sprite])

    if ch == 0:
        typewriter([
            "The imp — GRUB — perches on your shoulder.",
            "Grub: 'Don't call me late for dinner. Let's GO.'",
            "Grub's tips improve your combat! ATK +3",
        ], [player_sprite, imp_sprite])
        gain_xp(30)
        player_stats["atk"] += 3
        show_message("ATK +3 | XP +30", C_GREEN, 1500)

        typewriter([
            "Grub: 'Master kept his REAL loot behind the bookcase.'",
            "A section of wall grinds open. Gold and a glowing stone!",
        ], [player_sprite, imp_sprite])
        loot_box_screen()
        coins = drop_coins()
        show_message(f"+{coins} coins!", C_GOLD, 1000)
        return scene_demon_tower(imp_sprite)

    elif ch == 1:
        typewriter([
            "The imp SHRIEKS and transforms into a shadow beast!",
        ], [player_sprite, imp_sprite])
        result = combat_screen("Shadow Imp")
        if result == "victory":
            gain_xp(40)
            coins = drop_coins()
            show_message(f"XP +40 | +{coins} coins", C_GREEN, 1500)
            typewriter(["On the floor: a small key carved from bone."], [player_sprite])
            player_stats.setdefault("bone_key", True)
        return result if result in ("defeat", "gameover") else "continue"

    else:
        loot_box_screen(is_cursed=random.random() < 0.4)
        coins = drop_coins()
        show_message(f"+{coins} coins!", C_GOLD, 1000)
        typewriter(["Grub: 'Fine. Good luck dying out there. Alone.'"], [player_sprite])
        return "continue"


def scene_demon_tower(imp_sprite=None):
    bg.set_static(load_bg("tower"))
    fade_transition(400)
    sprites = [player_sprite]
    if imp_sprite:
        imp_sprite.set_pos(280, 390)
        sprites.append(imp_sprite)

    typewriter([
        "Grub leads you to a black iron tower.",
        "Grub: 'Dan answered to someone. Up there.'",
        "Grub: 'I'd go in but… prior engagement. With not dying.'",
    ], sprites)

    ch = show_menu("DEMON TOWER", ["Enter the tower", "Back away"], sprites)
    if ch == 1:
        player_stats["cowardice"] = player_stats.get("cowardice", 0) + 1
        show_message(f"Cowardice +1 ({player_stats['cowardice']})", C_RED, 1200)
        return "continue"

    # Floor 1
    typewriter([
        "--- FLOOR 1: THE GAUNTLET ---",
        "Skeletal soldiers line the corridor.",
    ], sprites)
    result = combat_screen("Skeleton Captain")
    if result in ("defeat", "gameover"):
        return result
    gain_xp(50)
    loot_box_screen()

    # Floor 2
    bg.set_static(load_bg("tower"))
    typewriter([
        "--- FLOOR 2: THE LIBRARY OF LIES ---",
        "Books fly off shelves and form a hulking golem!",
    ], sprites)
    result = combat_screen("Lore Golem")
    if result in ("defeat", "gameover"):
        return result
    gain_xp(60)
    coins = drop_coins()
    show_message(f"XP +60 | +{coins} coins", C_GREEN, 1500)

    # Floor 3 — Malachar
    bg.set_static(load_bg("tower"))
    typewriter([
        "--- FLOOR 3: THE THRONE ROOM ---",
        "A figure in armour so black it eats the light.",
        "???: 'I am MALACHAR. Archdemon of Nabi.'",
        "???: 'And you… are VERY lost.'",
    ], sprites)

    ch = show_menu("MALACHAR", [
        "Fight Malachar",
        "Try to negotiate",
        "Run (coward)",
    ], sprites)

    if ch == 2:
        player_stats["cowardice"] = player_stats.get("cowardice", 0) + 3
        show_message(f"Cowardice +3 ({player_stats['cowardice']})", C_RED, 1200)
        typewriter(["You bolt. Malachar laughs. The tower collapses."], sprites)
        return "continue"

    if ch == 1:
        typewriter(["Malachar: '…Negotiate? A mortal?'"], sprites)
        roll = random.randint(1, 3)
        if roll == 1:
            won = scene_riddle_challenge()
            if won:
                typewriter([
                    "Malachar: 'Clever wretch. I'll let you leave.'",
                    "--- YOU SURVIVED MALACHAR BY WIT ALONE ---",
                ], sprites)
                gain_xp(100)
                loot_box_screen()
                return "victory_end"
            else:
                typewriter(["Malachar: 'Wrong. I grow bored.'"], sprites)
        else:
            dmg = 30
            player_stats["hp"] -= dmg
            show_message(f"Malachar blasts you! -{dmg} HP", C_RED, 1200)
            if player_stats["hp"] <= 0:
                typewriter(["--- GAME OVER ---"], sprites)
                save_game()
                return "gameover"
            typewriter(["Diplomacy failed. Time for Plan B."], sprites)

    typewriter(["You charge. Malachar smiles."], sprites)
    result = combat_screen("Malachar the Archdemon")
    if result == "victory":
        return scene_malachar_victory()
    return result


def scene_riddle_challenge():
    riddles = [
        ("I have cities but no houses, forests but no trees,\nand water but no fish. What am I?", "map"),
        ("The more you take, the more you leave behind.\nWhat am I?", "footsteps"),
        ("I speak without a mouth and hear without ears.\nI come alive with wind. What am I?", "echo"),
    ]
    random.shuffle(riddles)
    score = 0

    typewriter(["Malachar: 'Three riddles. Answer them all.'"], [player_sprite])

    for i, (question, answer) in enumerate(riddles[:3]):
        typewriter([f"Riddle {i+1}: {question}"], [player_sprite])
        options = [answer.capitalize(), "Shadow", "Time", "Nothing"]
        random.shuffle(options)
        correct_idx = options.index(answer.capitalize())
        ch = show_menu(f"RIDDLE {i+1}", options, [player_sprite])
        if ch == correct_idx:
            show_message("Correct!", C_GREEN, 800)
            score += 1
        else:
            show_message(f"Wrong! Answer: {answer}", C_RED, 1200)

    return score >= 2


def scene_malachar_victory():
    bg.set_static(load_bg("tower"))
    typewriter([
        "MALACHAR DEFEATED!",
        "The tower shatters. Stars never before seen.",
        "Malachar: '…You… haven't seen… the last…'",
        "Grub: 'I totally helped. You're welcome.'",
    ], [player_sprite])
    gain_xp(150)
    loot_box_screen()
    coins = drop_coins()
    show_message(f"XP +150 | +{coins} coins!", C_GOLD, 2000)
    typewriter([
        f"{player_name} HAS SAVED NABI — FOR NOW.",
        "Epilogue: Grub opens a kebab stand. Very popular.",
    ], [player_sprite])
    save_game()
    return "victory_end"


# ---------------------------------------------------------------------------
#  LEFT PATH — THE HAUNTED RUINS
# ---------------------------------------------------------------------------
def scene_ruins():
    bg.set_static(load_bg("ruins"))
    fade_transition(400)
    player_sprite.set_sheet(spr_player_walk)
    player_sprite.set_pos(-100, 380)
    player_sprite.move_to(200, 380)
    wait_for_movement([player_sprite], 1500)
    player_sprite.set_sheet(spr_player_idle)

    typewriter([
        "The forest grows darker and colder.",
        "Stone arches, shattered columns, black water.",
        "Carved above the gate: ASHENVEIL — CITY OF THE FORGOTTEN",
    ], [player_sprite])

    ch = show_menu("ASHENVEIL RUINS", ["Enter the ruins", "Turn back"], [player_sprite])
    if ch == 1:
        player_stats["cowardice"] = player_stats.get("cowardice", 0) + 1
        show_message(f"Cowardice +1 ({player_stats['cowardice']})", C_RED, 1200)
        return "continue"

    typewriter([
        "Your footsteps echo strangely.",
        "Three buildings still stand:",
    ], [player_sprite])

    ch = show_menu("EXPLORE RUINS", [
        "A — The Old Temple",
        "B — The Guard Barracks",
        "C — The Lord's Mansion",
        "Leave",
    ], [player_sprite])

    if ch == 0:
        return scene_ruins_temple()
    elif ch == 1:
        return scene_ruins_barracks()
    elif ch == 2:
        return scene_ruins_mansion()
    return "continue"


def scene_ruins_temple():
    bg.set_static(load_bg("temple"))
    fade_transition(300)

    typewriter([
        "── THE OLD TEMPLE ──",
        "Stone pews face an altar. A cracked mirror sits upon it.",
        "Your reflection MOVES ON ITS OWN.",
        "Reflection: 'I've been waiting, original.'",
    ], [player_sprite])

    ch = show_menu("THE MIRROR", [
        "Speak to the reflection",
        "Smash the mirror",
        "Leave immediately",
    ], [player_sprite])

    if ch == 0:
        typewriter([
            "Reflection: 'I am you. A version from a different path.'",
            "Reflection: 'I know things about Malachar. About what's buried.'",
            "It presses its palm to the glass. 'Swap with me. Just once.'",
        ], [player_sprite])
        swap = show_menu("TOUCH THE MIRROR?", ["Press your palm", "Step back"], [player_sprite])
        if swap == 0:
            typewriter([
                "The cold glass pulls you in!",
                "You see a memory — a child burying a box under the mansion.",
                "You snap back, gasping.",
                "(You received the VISION. Something is under the Mansion.)",
            ], [player_sprite])
            player_stats["mirror_vision"] = True
            gain_xp(25)
            show_message("Mirror Vision acquired! XP +25", C_BLUE, 1500)
        else:
            typewriter(["The reflection looks sad, then blank."], [player_sprite])

    elif ch == 1:
        typewriter([
            "You HURL a stone at the mirror!",
            "Shards rise and form a MIRROR WRAITH!",
        ], [player_sprite])
        result = combat_screen("Mirror Wraith")
        if result == "victory":
            gain_xp(50)
            player_stats["atk"] += 5
            show_message("ATK +5 | XP +50", C_GREEN, 1500)
            typewriter(["A gemstone from the shards. It sharpens your instincts."], [player_sprite])
        elif result in ("defeat", "gameover"):
            return result

    else:
        typewriter(["You back out. Some things are better left alone."], [player_sprite])

    return "continue"


def scene_ruins_barracks():
    bg.set_static(load_bg("barracks"))
    fade_transition(300)
    skel_sprite = AnimatedSprite(spr_skeleton_idle, 550, 340, fps=4)

    typewriter([
        "── THE GUARD BARRACKS ──",
        "Rusted bunks. One skeleton seated at a card table.",
        "Skeleton: 'Finally! Someone to finish this game!'",
    ], [player_sprite, skel_sprite])

    ch = show_menu("BONE POKER", ["Play cards", "Decline"], [player_sprite, skel_sprite])
    if ch == 1:
        typewriter(["Skeleton: 'Story of my afterlife.'"], [player_sprite, skel_sprite])
    else:
        typewriter(["--- BONE POKER --- Best of three!"], [player_sprite, skel_sprite])
        player_wins = 0
        skel_wins = 0
        for rd in range(1, 4):
            p_card = random.randint(1, 13)
            s_card = random.randint(1, 13)
            show_message(f"Round {rd}: You drew {p_card} | Skeleton drew {s_card}", C_GOLD, 1500)
            if p_card > s_card:
                player_wins += 1
                show_message("You win this round!", C_GREEN, 800)
            elif s_card > p_card:
                skel_wins += 1
                show_message("Skeleton wins!", C_RED, 800)
            else:
                show_message("Tie!", C_BLUE, 800)

        if player_wins > skel_wins:
            typewriter(["Skeleton: 'HAH! I lose again!'",
                        "It reaches into its ribcage and produces potions."], [player_sprite, skel_sprite])
            player_stats["inventory"]["hp_potions"] += 2
            player_stats["inventory"]["dp_potions"] += 2
            gain_xp(30)
            show_message("+2 HP Potions, +2 Shield Potions, XP +30", C_GREEN, 2000)
        elif skel_wins > player_wins:
            typewriter(["Skeleton: 'After 400 years — I WIN!'",
                        "It explodes into confetti-like bone dust!"], [player_sprite])
            coins = drop_coins()
            show_message(f"+{coins} coins!", C_GOLD, 1000)
        else:
            typewriter(["Skeleton: 'A draw. Come back sometime.'"], [player_sprite, skel_sprite])
            gain_xp(15)
            show_message("XP +15", C_GREEN, 800)

    # Trapdoor
    typewriter(["You notice a trapdoor under one of the beds."], [player_sprite])
    ch = show_menu("TRAPDOOR", ["Open it", "Leave it"], [player_sprite])
    if ch == 0:
        roll = random.randint(1, 3)
        if roll == 1:
            typewriter(["A GHOUL lunges out!"], [player_sprite])
            result = combat_screen("Barracks Ghoul")
            if result == "victory":
                gain_xp(40)
                loot_box_screen()
            elif result in ("defeat", "gameover"):
                return result
        elif roll == 2:
            coins = drop_coins()
            player_stats["max_def"] += 3
            player_stats["def"] = player_stats["max_def"]
            show_message(f"Old Shield! Max DP +3 | +{coins} coins", C_GREEN, 1500)
        else:
            typewriter(["Darkness and old biscuits. Nothing else."], [player_sprite])

    return "continue"


def scene_ruins_mansion():
    bg.set_static(load_bg("mansion"))
    fade_transition(300)

    typewriter([
        "── THE LORD'S MANSION ──",
        "Hollow and vine-choked. Portraits with scratched faces.",
        "A locked door. Ice forms around the keyhole.",
    ], [player_sprite])

    has_vision = player_stats.get("mirror_vision", False)
    if has_vision:
        typewriter([
            "(Your mirror vision PULSES. Something is below.)",
            "You pry up floorboards. A box! Inside: a signet ring.",
            "Letter: 'The Lord made a pact with Dan the demon.'",
            "'The ring commands the mansion's guardian.'",
        ], [player_sprite])
        player_stats["signet_ring"] = True
        player_stats["atk"] += 7
        gain_xp(40)
        show_message("Signet Ring! ATK +7, XP +40", C_GOLD, 2000)

    ch = show_menu("MANSION", ["Open the cold locked door", "Leave"], [player_sprite])
    if ch == 1:
        typewriter(["The portraits watch you go."], [player_sprite])
        return "continue"

    typewriter([
        "Steps lead to a crypt. A REVENANT KNIGHT kneels.",
    ], [player_sprite])

    if player_stats.get("signet_ring", False):
        typewriter([
            "You hold up the signet ring. Its eyes glow gold.",
            "Revenant: 'My lord's seal. The pact is broken.'",
            "Revenant: 'You have my blade, warrior.'",
        ], [player_sprite])
        player_stats["atk"] = max(player_stats["atk"], 60)
        gain_xp(70)
        show_message(f"REVENANT'S BLADE! ATK → {player_stats['atk']}", C_GOLD, 2000)
        loot_box_screen()
    else:
        typewriter([
            "Revenant: 'INTRUDER. YOU ARE NOT MY LORD.'",
            "It rises, drawing a shadow-fire greatsword!",
        ], [player_sprite])
        result = combat_screen("Revenant Knight")
        if result == "victory":
            gain_xp(80)
            player_stats["max_def"] += 10
            player_stats["def"] = player_stats["max_def"]
            show_message(f"Max Shield +10 → {player_stats['max_def']}", C_BLUE, 1500)
            loot_box_screen()
        elif result in ("defeat", "gameover"):
            return result

    return "continue"


# ---------------------------------------------------------------------------
#  MIDDLE PATH — THE MOUNTAIN PASS
# ---------------------------------------------------------------------------
def scene_mountain():
    bg.set_static(load_bg("mountain"))
    fade_transition(400)
    oracle_sprite = AnimatedSprite(spr_oracle_idle, 550, 340, fps=4)
    player_sprite.set_sheet(spr_player_walk)
    player_sprite.set_pos(-100, 380)
    player_sprite.move_to(200, 380)
    wait_for_movement([player_sprite], 1500)
    player_sprite.set_sheet(spr_player_idle)

    typewriter([
        "The middle path climbs steeply. Icy wind.",
        "A cave mouth above. An old woman warming her hands.",
        "Old Woman: 'Took you long enough. Sit.'",
    ], [player_sprite, oracle_sprite])

    ch = show_menu("THE MOUNTAIN PASS", [
        "Sit with the old woman",
        "Enter the cave directly",
        "Descend to the valley",
        "Go back",
    ], [player_sprite, oracle_sprite])

    if ch == 0:
        return scene_mountain_oracle(oracle_sprite)
    elif ch == 1:
        return scene_mountain_cave()
    elif ch == 2:
        return scene_valley()
    return "continue"


def scene_mountain_oracle(oracle_sprite):
    bg.set_static(load_bg("mountain"))

    typewriter([
        "Oracle: 'I am Ysel. I see the threads of what will be.'",
        f"Oracle: 'I see you, {player_name}. Ask one question.'",
    ], [player_sprite, oracle_sprite])

    ch = show_menu("ASK YSEL", [
        "What is my destiny?",
        "How do I defeat Malachar?",
        "What is Dan hiding?",
        "Will I survive this?",
    ], [player_sprite, oracle_sprite])

    responses = [
        "Ysel: 'Your destiny is not fixed. I see a throne of ash.'",
        "Ysel: 'Malachar fears being forgotten. Make him feel small.'",
        "Ysel: 'Dan hides a tower. And his master hides everything.'",
        "Ysel: 'Yes. But not without cost.'",
    ]
    typewriter([responses[ch]], [player_sprite, oracle_sprite])
    gain_xp(20)

    player_stats["inventory"]["hp_potions"] += 1
    player_stats["max_hp"] += 10
    player_stats["hp"] = min(player_stats["hp"] + 10, player_stats["max_hp"])
    show_message(f"Stone of Ysel: +1 Potion, Max HP +10 → {player_stats['max_hp']}", C_GREEN, 2000)

    typewriter(["Ysel: 'The cave behind me — go.'"], [player_sprite, oracle_sprite])
    return scene_mountain_cave()


def scene_mountain_cave():
    bg.set_static(load_bg("cave"))
    fade_transition(300)
    dragon_sprite = AnimatedSprite(spr_dragon_idle, 550, 300, fps=4)

    typewriter([
        "── THE CAVE ──",
        "Crystals hum and glow blue. A dragon sleeps curled up.",
        "Gold-black scales shimmer.",
    ], [player_sprite, dragon_sprite])

    ch = show_menu("THE DRAGON", [
        "Sneak past",
        "Wake it and talk",
        "Attack the sleeping dragon",
        "Leave the cave",
    ], [player_sprite, dragon_sprite])

    if ch == 0:
        roll = random.randint(1, 3)
        if roll == 1:
            typewriter([
                "Your boot catches a crystal shard. It rings!",
                "Dragon: '…Three seconds to explain yourself.'",
            ], [player_sprite, dragon_sprite])
            return scene_dragon_talk(dragon_sprite)
        else:
            typewriter([
                "You move like a ghost. Behind it: a crystal chest.",
                "CRYSTAL HEART obtained!",
            ], [player_sprite])
            player_stats["atk"] += 10
            player_stats["max_hp"] += 15
            player_stats["hp"] = player_stats["max_hp"]
            gain_xp(50)
            show_message(f"ATK +10, Max HP +15!", C_GOLD, 2000)
            return "continue"

    elif ch == 1:
        typewriter([
            "Dragon: 'You DARE—' It tilts its head.",
            "Dragon: 'You're not screaming. Interesting.'",
        ], [player_sprite, dragon_sprite])
        return scene_dragon_talk(dragon_sprite)

    elif ch == 2:
        typewriter([
            "You STRIKE the sleeping dragon!",
            "Dragon: 'DO YOU KNOW HOW LONG I WAS ASLEEP?!'",
        ], [player_sprite, dragon_sprite])
        result = combat_screen("Furious Cave Dragon")
        if result == "victory":
            gain_xp(120)
            loot_box_screen()
            coins = drop_coins()
            show_message(f"XP +120 | +{coins} coins!", C_GOLD, 1500)
            loot_box_screen()
        return result if result in ("defeat", "gameover") else "continue"

    return "continue"


def scene_dragon_talk(dragon_sprite):
    bg.set_static(load_bg("cave"))

    typewriter([
        "Dragon: 'I am VETH. Three hundred years asleep.'",
        "Veth: 'State your purpose or I will eat you.'",
    ], [player_sprite, dragon_sprite])

    ch = show_menu("SPEAK TO VETH", [
        "I seek power to fight a great evil",
        "I was just exploring",
        "I came to challenge you",
        "...Are you okay?",
    ], [player_sprite, dragon_sprite])

    if ch == 0:
        typewriter([
            "Veth: 'Malachar. If someone's finally going after him…'",
            "Veth breathes golden fire onto your weapon!",
        ], [player_sprite, dragon_sprite])
        player_stats["atk"] += 15
        gain_xp(60)
        show_message(f"DRAGON'S BLESSING! ATK +15 → {player_stats['atk']}", C_GOLD, 2000)

    elif ch == 1:
        typewriter([
            "Veth: 'Just exploring. In a DRAGON'S CAVE.'",
            "Veth: '…I respect it. Take this dragon scale.'",
        ], [player_sprite, dragon_sprite])
        player_stats["max_def"] += 8
        player_stats["def"] = player_stats["max_def"]
        gain_xp(30)
        show_message(f"DRAGON SCALE! Max Shield +8 → {player_stats['max_def']}", C_BLUE, 2000)

    elif ch == 2:
        typewriter([
            "Veth: 'Challenge me? Delightful. Unhinged.'",
        ], [player_sprite, dragon_sprite])
        result = combat_screen("Veth the Cave Dragon (Holding Back)")
        if result == "victory":
            gain_xp(100)
            typewriter(["Veth: 'Genuinely impressed.'"], [player_sprite, dragon_sprite])
            loot_box_screen()
            loot_box_screen()
            coins = drop_coins()
            player_stats["atk"] += 8
            show_message(f"WARRIOR'S RESPECT! ATK +8 | +{coins} coins", C_GOLD, 2000)
        return result if result in ("defeat", "gameover") else "continue"

    elif ch == 3:
        typewriter([
            "Veth: '…Nobody has asked me that in 300 years.'",
            "Veth: 'I am... fine. Just very tired.'",
            "Veth: 'Take this. I don't need it.'",
        ], [player_sprite, dragon_sprite])
        player_stats["inventory"]["hp_potions"] += 3
        player_stats["max_hp"] += 20
        player_stats["hp"] = player_stats["max_hp"]
        gain_xp(50)
        show_message(f"+3 Potions, Max HP +20 → {player_stats['max_hp']}", C_GREEN, 2000)

    return "continue"


def scene_valley():
    bg.set_static(load_bg("valley"))
    fade_transition(400)
    player_sprite.set_sheet(spr_player_walk)
    player_sprite.set_pos(-100, 380)
    player_sprite.move_to(200, 380)
    wait_for_movement([player_sprite], 1500)
    player_sprite.set_sheet(spr_player_idle)

    typewriter([
        "── THE SHIMMERING VALLEY ──",
        "Warm air, spiral flowers. A small peaceful village.",
        "But surrounded by stone, and outside: hundreds of undead.",
        "",
        "Child: 'Are you a hero? We sent ravens three months ago.'",
        "Child: 'You're late. But we're not picky.'",
    ], [player_sprite])

    ch = show_menu("HELP THE VILLAGE?", ["Yes, help them", "Turn away"], [player_sprite])
    if ch == 1:
        player_stats["cowardice"] = player_stats.get("cowardice", 0) + 2
        show_message(f"Cowardice +2 ({player_stats['cowardice']})", C_RED, 1200)
        typewriter(["The child's face falls. You will remember that."], [player_sprite])
        return "continue"

    typewriter([
        "── THE VILLAGE OF EVENMERE ──",
        "Elder Rho: 'The dead appeared eight days ago.'",
        "A plaque: 'DELIVER THE SOULSTONE OR THE SIEGE NEVER ENDS — M'",
    ], [player_sprite])

    ch = show_menu("APPROACH", [
        "Fight through the undead",
        "Search the village for clues",
        "Confront whoever left the message",
    ], [player_sprite])

    if ch == 0:
        typewriter(["You vault the wall and charge!"], [player_sprite])
        result = combat_screen("Undead Horde (First Wave)")
        if result in ("defeat", "gameover"):
            return result
        gain_xp(60)
        result = combat_screen("Undead Horde (Second Wave)")
        if result in ("defeat", "gameover"):
            return result
        gain_xp(60)
        show_message("XP +120 total!", C_GREEN, 1200)
        typewriter(["More are rising. Rho: 'We need the SOURCE.'"], [player_sprite])
        return scene_valley_necromancer()

    elif ch == 1:
        typewriter([
            "In the chapel basement: a SOULSTONE. It pulses with light.",
            "Rho: 'We had it all along?!'",
        ], [player_sprite])

        ch2 = show_menu("THE SOULSTONE", [
            "Give it to whoever left the message",
            "Destroy the soulstone",
            "Use the soulstone yourself",
        ], [player_sprite])

        if ch2 == 0:
            return scene_valley_necromancer()
        elif ch2 == 1:
            typewriter([
                "You SMASH the soulstone! Light screams outward!",
                "The undead collapse like puppets.",
                "The energy went into you.",
            ], [player_sprite])
            player_stats["max_hp"] += 30
            player_stats["hp"] = player_stats["max_hp"]
            player_stats["atk"] += 10
            gain_xp(80)
            show_message(f"SOULSTONE! Max HP +30, ATK +10!", C_GOLD, 2000)
            typewriter(["Rho: 'You absolute maniac. Thank you.'"], [player_sprite])
            coins = drop_coins()
            coins2 = drop_coins()
            show_message(f"+{coins + coins2} coins!", C_GOLD, 1000)
            return "continue"
        else:
            typewriter([
                "The soulstone bonds to you! Max HP +20.",
                "The undead ignore YOU now. But the village is still trapped.",
            ], [player_sprite])
            player_stats["max_hp"] += 20
            player_stats["hp"] = player_stats["max_hp"]
            gain_xp(50)
            show_message(f"Max HP +20 → {player_stats['max_hp']}", C_GREEN, 1500)
            return "continue"

    else:
        return scene_valley_necromancer()


def scene_valley_necromancer():
    bg.set_static(load_bg("valley"))
    necro_sprite = AnimatedSprite(spr_necromancer_idle, 600, 340, fps=4)

    typewriter([
        "At the hilltop: a cloaked figure. Young. Exhausted.",
        "Necromancer: 'I'm not a villain. I'm desperate.'",
        "Necromancer: 'The soulstone holds my sister's soul.'",
        "Necromancer: 'She died. I need the stone to save her.'",
    ], [player_sprite, necro_sprite])

    ch = show_menu("THE NECROMANCER", [
        "Help — give the soulstone",
        "Fight the necromancer",
        "Ask more questions",
    ], [player_sprite, necro_sprite])

    if ch == 0:
        typewriter([
            "The undead collapse. The sister's spirit rises —",
            "— and smiles, once, dissolving into golden light.",
            "Necromancer: 'Thank you. I owe you a debt.'",
        ], [player_sprite, necro_sprite])
        gain_xp(80)
        player_stats["inventory"]["hp_potions"] += 2
        player_stats["max_def"] += 5
        player_stats["def"] = player_stats["max_def"]
        coins = drop_coins()
        show_message(f"+2 Potions, Max Shield +5, +{coins} coins", C_GREEN, 2000)

    elif ch == 1:
        typewriter([
            "Necromancer: 'Of course. Nothing is ever simple.'",
        ], [player_sprite, necro_sprite])
        result = combat_screen("Desperate Necromancer")
        if result == "victory":
            gain_xp(70)
            typewriter(["A cracked orb still glows faintly."], [player_sprite])
            loot_box_screen(is_cursed=True)
        elif result in ("defeat", "gameover"):
            return result

    else:
        typewriter([
            "Necromancer: 'Malachar created soulstones as TRAPS.'",
            "Necromancer: 'I repurposed the technique.'",
        ], [player_sprite, necro_sprite])
        gain_xp(25)
        show_message("XP +25", C_GREEN, 800)
        return scene_valley_necromancer()

    save_game()
    return "continue"


# ---------------------------------------------------------------------------
#  MAIN MENU / GAME LOOP
# ---------------------------------------------------------------------------
def title_screen():
    bg.set_static(load_bg("menu"))
    narrator_sprite.set_pos(SCREEN_W // 2 - 64, 350)
    narrator_sprite.visible = True
    alpha = 0; growing = True

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.VIDEORESIZE:
                handle_resize(event)
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                play_sound("menu_click"); return

        dt = clock.tick(FPS) / 1000
        bg.update(dt)
        bg.draw(screen)
        narrator_sprite.update(dt)
        narrator_sprite.draw(screen)

        if growing:
            alpha = min(255, alpha + 3)
            if alpha >= 255: growing = False
        else:
            alpha = max(100, alpha - 2)
            if alpha <= 100: growing = True

        title_surf = font_title.render("NABI", True, C_GOLD)
        title_surf.set_alpha(alpha)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_W // 2, 200)))
        draw_text(f"v{VERSION}", font_md, C_TEXT_DIM, SCREEN_W // 2, 260, "center")
        draw_text("An Audiovisual RPG", font_md, C_TEXT_DIM, SCREEN_W // 2, 290, "center")

        pa = 128 + int(64 * math.sin(pygame.time.get_ticks() * 0.003))
        prompt = font_sm.render("Press any key to start", True, C_TEXT_DIM)
        prompt.set_alpha(pa)
        screen.blit(prompt, prompt.get_rect(center=(SCREEN_W // 2, 480)))
        pygame.display.flip()


def check_updates_gui():
    """Check for updates using the updater module, with GUI feedback."""
    try:
        from updater import check_for_updates, fetch_latest_release, parse_version
        show_message("Checking for updates...", C_BLUE, 1000)
        release = fetch_latest_release()
        if not release:
            show_message("Could not reach update server.", C_RED, 2000)
            return
        tag = release.get("tag_name", "")
        latest_ver = parse_version(tag)
        current_ver = parse_version(VERSION)
        if latest_ver <= current_ver:
            show_message(f"You're up to date! (v{VERSION})", C_GREEN, 2000)
            return
        release_name = release.get("name", tag)
        body = release.get("body", "")[:150]
        ch = show_menu(f"UPDATE AVAILABLE: {tag}",
                       ["Update Now", "Skip"],
                       subtitle=f"Current: v{VERSION} | {release_name}")
        if ch == 0:
            show_message("Updating... please wait", C_BLUE, 500)
            if check_for_updates(VERSION, headless=True):
                show_message("Update complete! Please restart Nabi.", C_GREEN, 3000)
            else:
                show_message("Update failed. Try again later.", C_RED, 2000)
    except ImportError:
        show_message("Updater module not found.", C_RED, 2000)
    except Exception as e:
        show_message(f"Update error: {str(e)[:50]}", C_RED, 2000)


def main():
    global player_name

    # Auto-check for updates on startup (non-blocking on failure)
    try:
        from updater import fetch_latest_release, parse_version
        release = fetch_latest_release()
        if release:
            tag = release.get("tag_name", "")
            if parse_version(tag) > parse_version(VERSION):
                pass  # Will show in menu as "Check for Updates (NEW!)"
    except Exception:
        pass

    title_screen()

    has_save = os.path.exists(SAVE_FILE)
    if has_save:
        bg.set_static(load_bg("menu"))
        choice = show_menu("SAVE FILE FOUND", ["Load Game", "New Game"])
        if choice == 0 and load_game():
            play_sound("save")
            show_message(f"Welcome back, {player_name}!", C_GREEN, 1500)
        else:
            has_save = False

    if not has_save or not player_name:
        bg.set_static(load_bg("menu"))
        player_name = get_text_input("What should I call you, warrior?")

    while True:
        bg.set_static(load_bg("menu"))
        narrator_sprite.set_pos(50, 350)
        player_sprite.set_sheet(spr_player_idle)
        player_sprite.set_pos(SCREEN_W - 200, 380)

        high_s, high_w = arcade_get_highscore()
        hs_txt = f" | Arcade Best: {high_s} (W{high_w})" if high_s > 0 else ""
        choice = show_menu(f"NABI  v{VERSION}",
                           ["Start Adventure", "Arcade Mode", "Check for Updates", "Quit Game"],
                           [player_sprite, narrator_sprite],
                           subtitle=f"Hero: {player_name} | Lv.{player_stats['level']}{hs_txt}")

        try:
            if choice == 0:
                player_stats["hp"] = player_stats["max_hp"]
                player_stats["def"] = player_stats["max_def"]
                player_stats["combo"] = 0
                save_game()
                scene_intro()
                want = show_menu("BEGIN YOUR ADVENTURE?", ["Yes!", "Not yet..."], [player_sprite])
                if want == 1:
                    typewriter(["Oh well, maybe next time!"], [player_sprite]); continue
                save_game()
                scene_forest()
            elif choice == 1:
                arcade_mode()
            elif choice == 2:
                check_updates_gui()
            elif choice == 3:
                save_game(); play_sound("save")
                show_message("Thanks for playing Nabi! Goodbye.", C_GOLD, 2000)
                pygame.quit(); sys.exit()
        except PauseMenuExit:
            save_game()
            continue


if __name__ == "__main__":
    main()
