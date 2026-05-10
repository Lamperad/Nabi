"""
Nabi v3.0.0 — Audiovisual RPG (Pygame)
Animated characters, parallax backgrounds, fluid movement, and sound.
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
VERSION = "3.0.0"
SAVE_FILE = "save_data.json"
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

# ---------------------------------------------------------------------------
#  GAME STATE
# ---------------------------------------------------------------------------
DEFAULT_PLAYER_STATS = {
    "hp": 100, "max_hp": 100, "atk": 20, "def": 15, "max_def": 15,
    "coins": 0, "level": 1, "xp": 0, "cowardice": 0,
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
        leveled = True
    return leveled


# ---------------------------------------------------------------------------
#  PYGAME INIT
# ---------------------------------------------------------------------------
os.environ["SDL_AUDIODRIVER"] = "dummy"

pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    AUDIO_OK = True
except Exception:
    AUDIO_OK = False

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
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
    w, h = 280, 170
    draw_panel((x, y, w, h), fill=C_PANEL)
    ny = y + 8
    draw_text(f"{player_name}  Lv.{player_stats['level']}", font_md, C_GOLD, x + 10, ny)
    ny += 28
    draw_bar(x + 10, ny, w - 20, 20, player_stats['hp'], player_stats['max_hp'], C_HP_BAR, C_HP_BG,
             f"HP {player_stats['hp']}/{player_stats['max_hp']}")
    ny += 26
    draw_bar(x + 10, ny, w - 20, 20, player_stats['def'], player_stats['max_def'], C_DP_BAR, C_DP_BG,
             f"DP {player_stats['def']}/{player_stats['max_def']}")
    ny += 26
    draw_bar(x + 10, ny, w - 20, 16, player_stats['xp'], 100, C_XP_BAR, C_XP_BG,
             f"XP {player_stats['xp']}/100")
    ny += 22
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
def pump_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            pygame.quit()
            sys.exit()

def get_text_input(prompt, max_len=20):
    text = ""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game(); pygame.quit(); sys.exit()
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
    """Typewriter with animated sprites and background."""
    if sprites is None:
        sprites = []
    displayed = []
    for line_text in lines:
        displayed.append("")
        skip = False
        for i, ch in enumerate(line_text):
            displayed[-1] += ch
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_game(); pygame.quit(); sys.exit()
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
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

    # Wait for click
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game(); pygame.quit(); sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
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
        draw_text("[ Click or press any key ]", font_sm, C_TEXT_DIM, SCREEN_W // 2, SCREEN_H - 30, "center")
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
            if duration == 0 and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
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
        ("[REPAIR] Full DP", 20, "dp_restore"),
        ("[BUFF] ATK +5", 100, "atk_buff"),
        ("[BUFF] Max DP +5", 100, "dp_buff"),
        ("[BUY] HP Potion", 50, "hp_pot"),
        ("[BUY] DP Potion", 50, "dp_pot"),
        ("[UPGRADE] Max HP +20", 150, "hp_upgrade"),
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
            player_stats["def"] = player_stats["max_def"]; msg = "Armor fully repaired!"
        elif action == "atk_buff":
            player_stats["atk"] += 5; msg = f"ATK is now {player_stats['atk']}!"
        elif action == "dp_buff":
            player_stats["max_def"] += 5; player_stats["def"] = player_stats["max_def"]
            msg = f"Max DP is now {player_stats['max_def']}!"
        elif action == "hp_pot":
            player_stats["inventory"]["hp_potions"] += 1
            msg = f"HP Potion added! ({player_stats['inventory']['hp_potions']})"
        elif action == "dp_pot":
            player_stats["inventory"]["dp_potions"] += 1
            msg = f"DP Potion added! ({player_stats['inventory']['dp_potions']})"
        elif action == "hp_upgrade":
            player_stats["max_hp"] += 20; player_stats["hp"] += 20
            msg = f"Max HP is now {player_stats['max_hp']}!"
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
            msg, color = f"Defense Upgrade! Max DP {player_stats['max_def']}", C_BLUE
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
    e_dp = int(random.randint(5 + player_stats["level"], 15 + player_stats["level"]) * c_mult)

    is_demon = "demon" in enemy_name.lower()
    enemy_sheet = spr_demon_idle if is_demon else spr_dan_idle
    enemy_attack_sheet = spr_demon_attack if is_demon else spr_dan_angry
    enemy_sprite = AnimatedSprite(enemy_sheet, 620, 280, fps=5)
    enemy_sprite.flip_h = True

    player_sprite.set_sheet(spr_player_idle)
    player_sprite.set_pos(150, 280)

    if is_demon:
        play_sound("demon_roar")

    log = [f"Battle: {player_name} vs {enemy_name}!"]
    if player_stats.get("cowardice", 0) > 0:
        log.append(f"CURSE: Cowardice ({player_stats['cowardice']}) empowers the enemy!")

    shake_timer = 0

    while player_stats["hp"] > 0 and e_hp > 0:
        actions = ["Attack", "Defend", "Use Item", "Run", "Shop", "Quit"]
        buttons = []
        for i, act in enumerate(actions):
            key_map = {0: pygame.K_1, 1: pygame.K_2, 2: pygame.K_3,
                       3: pygame.K_4, 4: pygame.K_5, 5: pygame.K_6}
            bw, bh = 140, 38
            col_i = i % 3; row_i = i // 3
            bx = 30 + col_i * (bw + 10)
            by = SCREEN_H - 100 + row_i * (bh + 8)
            buttons.append(Button((bx, by, bw, bh), f"{i+1}.{act}", font=font_sm, key=key_map.get(i)))

        action_idx = None
        while action_idx is None:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_game(); pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_k:
                        action_idx = -1; break
                    if event.key == pygame.K_g:
                        player_stats["hp"] = player_stats["atk"] = player_stats["def"] = 999
                        log.append("[CHEAT] GODMODE!"); action_idx = -2; break
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

            # Draw sprites with shake offset
            old_ex, old_ey = enemy_sprite.x, enemy_sprite.y
            enemy_sprite.x += sx; enemy_sprite.y += sy
            player_sprite.draw(screen)
            enemy_sprite.draw(screen)
            enemy_sprite.x, enemy_sprite.y = old_ex, old_ey

            # Enemy HP panel
            draw_panel((480, 40, 300, 100), fill=(50, 20, 20))
            draw_text(enemy_name, font_lg, C_RED, 630, 55, "center")
            draw_bar(500, 95, 260, 22, max(0, e_hp), e_max_hp, C_RED, C_HP_BG,
                     f"HP {max(0,e_hp)}/{e_max_hp}")
            draw_text(f"ATK: {e_atk}", font_sm, C_TEXT_DIM, 510, 125)
            draw_stat_panel(20, 40)

            # Log
            draw_panel((20, SCREEN_H - 250, SCREEN_W - 40, 130), fill=(20, 20, 30))
            ly = SCREEN_H - 242
            for entry in log[-6:]:
                draw_text(entry, font_sm, C_TEXT, 35, ly, max_width=SCREEN_W - 80)
                ly += 20

            for btn in buttons:
                btn.update(mouse_pos); btn.draw()
            pygame.display.flip()

        if action_idx == 5:
            return "menu"
        if action_idx == -1:
            log.append("[CHEAT] Forbidden spell!"); e_hp = 0; break
        if action_idx == -2:
            continue

        defend_bonus = 0

        if action_idx == 0:  # Attack
            play_sound("attack_hit")
            player_sprite.set_sheet(spr_player_attack)
            # Animate player lunging forward
            player_sprite.move_to(350, 280)
            wait_for_movement([player_sprite, enemy_sprite], 500)
            e_hp -= player_stats["atk"]
            log.append(f"You strike for {player_stats['atk']} damage!")
            player_sprite.move_to(150, 280)
            player_sprite.set_sheet(spr_player_idle)
            shake_timer = 0.3

        elif action_idx == 1:  # Defend
            defend_bonus = 10
            play_sound("defend")
            player_sprite.set_sheet(spr_player_defend)
            log.append("You brace yourself!")

        elif action_idx == 2:  # Items
            hp_c = player_stats["inventory"]["hp_potions"]
            dp_c = player_stats["inventory"]["dp_potions"]
            ch = show_menu("USE ITEM", [f"HP Potion ({hp_c})", f"DP Potion ({dp_c})", "Back"])
            if ch == 0 and hp_c > 0:
                play_sound("potion"); player_stats["hp"] = player_stats["max_hp"]
                player_stats["inventory"]["hp_potions"] -= 1; log.append("Used HP Potion!"); continue
            elif ch == 1 and dp_c > 0:
                play_sound("potion"); player_stats["def"] = player_stats["max_def"]
                player_stats["inventory"]["dp_potions"] -= 1; log.append("Used DP Potion!"); continue
            elif ch in (0, 1):
                play_sound("error"); show_message("No potions!", C_RED, 1000)
            continue

        elif action_idx == 3:  # Run
            if random.random() < 0.5:
                play_sound("flee")
                player_stats["cowardice"] = player_stats.get("cowardice", 0) + 1
                player_sprite.move_to(-150, 280)
                wait_for_movement([player_sprite], 800)
                show_message(f"Escaped! Cowardice: {player_stats['cowardice']}", C_ORANGE, 1500)
                return "escaped"
            else:
                log.append(f"Failed to escape! {enemy_name} blocks you!")

        elif action_idx == 4:  # Shop
            shop_screen(); bg.set_static(load_bg("combat")); continue

        # Enemy turn
        if e_hp > 0:
            enemy_sprite.set_sheet(enemy_attack_sheet)
            enemy_sprite.move_to(350, 280)
            wait_for_movement([player_sprite, enemy_sprite], 500)

            if action_idx == 1:
                defense_check = (player_stats["def"] + defend_bonus) - e_atk
                if defense_check >= 0:
                    log.append("Armor absorbs the hit!")
                else:
                    dmg = abs(defense_check); player_stats["hp"] -= dmg
                    play_sound("player_hurt"); log.append(f"Armor cracked! Took {dmg} damage!")
                    shake_timer = 0.3
                player_sprite.set_sheet(spr_player_idle)
            else:
                player_stats["hp"] -= e_atk
                play_sound("player_hurt")
                player_sprite.set_sheet(spr_player_hurt)
                log.append(f"{enemy_name} hits for {e_atk} damage!")
                shake_timer = 0.3

            enemy_sprite.move_to(620, 280)
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

    while True:
        choice = show_menu("THE DARK FOREST",
                           ["Go Right (Dan's Field)", "Go Left (Deep Forest)", "Shop"],
                           [player_sprite],
                           subtitle="Two paths stretch before you...")
        save_game()

        if choice == 2:
            typewriter(["Isn't it a bit early to be shopping?"], [player_sprite])
            continue
        elif choice == 1:
            player_sprite.set_sheet(spr_player_walk)
            player_sprite.move_to(-100, 380)
            wait_for_movement([player_sprite], 1500)
            typewriter(["You head left into the deep forest...", "But there's nothing here yet."], [], narrator_visible=True)
            player_sprite.set_pos(SCREEN_W + 100, 380)
            player_sprite.move_to(200, 380)
            player_sprite.set_sheet(spr_player_idle)
            wait_for_movement([player_sprite], 1500)
            continue
        elif choice == 0:
            player_sprite.set_sheet(spr_player_walk)
            player_sprite.move_to(SCREEN_W + 100, 380)
            wait_for_movement([player_sprite], 1500)
            result = scene_dan_field()
            if result in ("victory", "defeat", "gameover"):
                return result
            # Return to forest
            bg.layers = []
            bg.add_layer(load_bg("forest_sky"), 0)
            bg.add_layer(load_bg("forest_far_trees"), 8)
            bg.add_layer(load_bg("forest_fog"), 15)
            bg.add_layer(load_bg("forest_near_trees"), 25)
            player_sprite.set_sheet(spr_player_walk)
            player_sprite.set_pos(-100, 380)
            player_sprite.move_to(200, 380)
            wait_for_movement([player_sprite], 1500)
            player_sprite.set_sheet(spr_player_idle)


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

    choice = show_menu("DAN'S FIELD", ["Speak to Dan", "Go Back"], [player_sprite, dan_sprite])

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
        "I am lost and need help"
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
    return result


def scene_dan_option4():
    typewriter(["Dan: Lost, are you?",
                "Dan: How about you rest for the night first?"],
               [player_sprite, dan_sprite])

    choice = show_menu("DAN'S OFFER", ["Accept Dan's offer", "Decline and continue"], [player_sprite, dan_sprite])

    if choice == 0:
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

        fight = show_menu("FIGHT THE DEMON?", ["Yes, fight!", "No, flee!"], [player_sprite, dan_sprite])
        if fight == 1:
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
        return result


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


def main():
    global player_name

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

        choice = show_menu(f"NABI  v{VERSION}", ["Start Adventure", "Quit Game"],
                           [player_sprite, narrator_sprite],
                           subtitle=f"Hero: {player_name} | Lv.{player_stats['level']}")

        if choice == 0:
            player_stats["hp"] = player_stats["max_hp"]
            player_stats["def"] = player_stats["max_def"]
            save_game()
            scene_intro()
            want = show_menu("BEGIN YOUR ADVENTURE?", ["Yes!", "Not yet..."], [player_sprite])
            if want == 1:
                typewriter(["Oh well, maybe next time!"], [player_sprite]); continue
            save_game()
            scene_forest()
        elif choice == 1:
            save_game(); play_sound("save")
            show_message("Thanks for playing Nabi! Goodbye.", C_GOLD, 2000)
            pygame.quit(); sys.exit()


if __name__ == "__main__":
    main()
