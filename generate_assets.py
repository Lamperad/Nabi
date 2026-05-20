"""
Generate all pixel-art sprite sheets and background layers for Nabi.
Run once: python generate_assets.py
Outputs PNG files into assets/avatars/ and assets/backgrounds/
"""
import pygame
import os
import math

pygame.init()

AVATAR_SIZE = 64          # each frame is 64x64
BG_W, BG_H = 1280, 720     # matches game window

OUT_AVATAR = os.path.join(os.path.dirname(__file__), "assets", "avatars")
OUT_BG = os.path.join(os.path.dirname(__file__), "assets", "backgrounds")
os.makedirs(OUT_AVATAR, exist_ok=True)
os.makedirs(OUT_BG, exist_ok=True)

# ---- colour palette ----
SKIN = (220, 180, 140)
SKIN_DARK = (180, 140, 100)
ARMOR_SILVER = (160, 170, 185)
ARMOR_DARK = (100, 110, 125)
BLADE = (200, 210, 220)
CAPE_BLUE = (50, 70, 140)
CAPE_DARK = (30, 40, 90)
HAIR_BROWN = (80, 55, 30)
EYE = (40, 40, 40)
DAN_SHIRT = (80, 120, 60)
DAN_PANTS = (90, 70, 50)
DEMON_RED = (180, 30, 30)
DEMON_DARK = (100, 15, 15)
DEMON_WING = (140, 20, 20)
DEMON_EYE = (255, 200, 0)
HOOD_GREY = (50, 50, 60)
HOOD_DARK = (30, 30, 35)
CLOAK_PURPLE = (60, 30, 80)
CLOAK_DARK = (35, 18, 50)
TRANSPARENT = (0, 0, 0, 0)

def make_surf(w=AVATAR_SIZE, h=AVATAR_SIZE):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(TRANSPARENT)
    return s

def save_sheet(frames, name):
    """Save a list of surfaces as a horizontal sprite sheet."""
    n = len(frames)
    w = frames[0].get_width()
    h = frames[0].get_height()
    sheet = pygame.Surface((w * n, h), pygame.SRCALPHA)
    sheet.fill(TRANSPARENT)
    for i, f in enumerate(frames):
        sheet.blit(f, (i * w, 0))
    path = os.path.join(OUT_AVATAR, f"{name}.png")
    pygame.image.save(sheet, path)
    print(f"  Saved {path}  ({n} frames, {w}x{h})")

def save_bg(surf, name):
    path = os.path.join(OUT_BG, f"{name}.png")
    pygame.image.save(surf, path)
    print(f"  Saved {path}  ({surf.get_width()}x{surf.get_height()})")


# ======================================================================
#  PLAYER AVATAR — armored warrior
# ======================================================================
def draw_player_base(s, body_dy=0, arm_angle=0, sword_visible=True,
                     leg_spread=0, cape_sway=0, shield_up=False):
    """Draw the player character onto surface s with offsets for animation."""
    cx, cy = 32, 32  # centre reference
    by = cy + 6 + body_dy  # body y

    # Cape (behind body)
    cape_pts = [
        (cx - 8 + cape_sway, by - 12),
        (cx - 14 + cape_sway * 2, by + 18),
        (cx + 2 + cape_sway, by + 16),
    ]
    pygame.draw.polygon(s, CAPE_BLUE, cape_pts)
    pygame.draw.polygon(s, CAPE_DARK, cape_pts, 1)

    # Legs
    leg_y = by + 14
    pygame.draw.rect(s, ARMOR_DARK, (cx - 6 - leg_spread, leg_y, 5, 14))
    pygame.draw.rect(s, ARMOR_DARK, (cx + 1 + leg_spread, leg_y, 5, 14))
    # Boots
    pygame.draw.rect(s, (60, 50, 40), (cx - 7 - leg_spread, leg_y + 12, 7, 4))
    pygame.draw.rect(s, (60, 50, 40), (cx + 0 + leg_spread, leg_y + 12, 7, 4))

    # Body (torso armour)
    pygame.draw.rect(s, ARMOR_SILVER, (cx - 8, by - 2, 16, 16), border_radius=2)
    pygame.draw.rect(s, ARMOR_DARK, (cx - 8, by - 2, 16, 16), 1, border_radius=2)
    # Belt
    pygame.draw.rect(s, (120, 90, 40), (cx - 8, by + 11, 16, 3))

    # Arms
    # Left arm (shield side)
    la_x = cx - 12
    la_y = by + 1
    pygame.draw.rect(s, ARMOR_SILVER, (la_x, la_y, 5, 12))
    pygame.draw.rect(s, SKIN, (la_x, la_y + 10, 5, 4))
    if shield_up:
        pygame.draw.rect(s, (120, 80, 30), (la_x - 4, la_y - 2, 8, 16), border_radius=2)
        pygame.draw.rect(s, (80, 50, 20), (la_x - 4, la_y - 2, 8, 16), 1, border_radius=2)

    # Right arm (sword side)
    ra_x = cx + 7
    ra_y = by + 1 + int(arm_angle * 0.5)
    pygame.draw.rect(s, ARMOR_SILVER, (ra_x, ra_y, 5, 12))
    pygame.draw.rect(s, SKIN, (ra_x, ra_y + 10, 5, 4))
    if sword_visible:
        sw_y = ra_y - 8 - int(arm_angle * 2)
        pygame.draw.rect(s, (80, 60, 30), (ra_x + 1, ra_y + 2, 3, 8))  # hilt
        pygame.draw.rect(s, BLADE, (ra_x + 1, sw_y, 3, 12))  # blade
        pygame.draw.rect(s, (240, 240, 255), (ra_x + 2, sw_y, 1, 10))  # shine

    # Head
    head_y = by - 14
    pygame.draw.ellipse(s, SKIN, (cx - 6, head_y, 12, 12))
    # Helmet
    pygame.draw.arc(s, ARMOR_SILVER, (cx - 7, head_y - 2, 14, 10), 0, math.pi, 3)
    pygame.draw.rect(s, ARMOR_SILVER, (cx - 7, head_y, 14, 4))
    # Eyes
    pygame.draw.rect(s, EYE, (cx - 3, head_y + 5, 2, 2))
    pygame.draw.rect(s, EYE, (cx + 1, head_y + 5, 2, 2))


def gen_player():
    print("Generating player avatar...")
    # Idle (4 frames — breathing bob)
    idle_frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        cape = [0, 1, 0, -1][i]
        draw_player_base(s, body_dy=dy, cape_sway=cape)
        idle_frames.append(s)
    save_sheet(idle_frames, "player_idle")

    # Walk (6 frames — leg movement)
    walk_frames = []
    for i in range(6):
        s = make_surf()
        dy = [0, -1, -1, 0, 1, 1][i]
        leg = [-2, -1, 0, 2, 1, 0][i]
        cape = [0, 1, 2, 1, 0, -1][i]
        draw_player_base(s, body_dy=dy, leg_spread=leg, cape_sway=cape)
        walk_frames.append(s)
    save_sheet(walk_frames, "player_walk")

    # Attack (4 frames — sword swing)
    attack_frames = []
    for i in range(4):
        s = make_surf()
        arm = [0, 3, 6, 2][i]
        dy = [0, -2, 0, 1][i]
        draw_player_base(s, body_dy=dy, arm_angle=arm)
        attack_frames.append(s)
    save_sheet(attack_frames, "player_attack")

    # Hurt (3 frames — recoil)
    hurt_frames = []
    for i in range(3):
        s = make_surf()
        dx = [2, 4, 1][i]
        dy = [0, 1, 0][i]
        draw_player_base(s, body_dy=dy, cape_sway=dx)
        # Red tint overlay
        if i == 1:
            overlay = make_surf()
            overlay.fill((255, 0, 0, 60))
            s.blit(overlay, (0, 0))
        hurt_frames.append(s)
    save_sheet(hurt_frames, "player_hurt")

    # Defend (2 frames — shield up)
    def_frames = []
    for i in range(2):
        s = make_surf()
        draw_player_base(s, body_dy=0, shield_up=True, sword_visible=False, cape_sway=[0, -1][i])
        def_frames.append(s)
    save_sheet(def_frames, "player_defend")


# ======================================================================
#  DAN — farmer and demon form
# ======================================================================
def draw_dan_farmer(s, body_dy=0, arm_dy=0):
    cx, cy = 32, 32
    by = cy + 6 + body_dy

    # Legs
    pygame.draw.rect(s, DAN_PANTS, (cx - 5, by + 14, 4, 14))
    pygame.draw.rect(s, DAN_PANTS, (cx + 1, by + 14, 4, 14))
    pygame.draw.rect(s, (60, 45, 30), (cx - 6, by + 26, 6, 4))
    pygame.draw.rect(s, (60, 45, 30), (cx + 0, by + 26, 6, 4))

    # Body
    pygame.draw.rect(s, DAN_SHIRT, (cx - 7, by - 2, 14, 16), border_radius=2)

    # Arms
    pygame.draw.rect(s, DAN_SHIRT, (cx - 11, by + arm_dy, 5, 11))
    pygame.draw.rect(s, SKIN, (cx - 11, by + 10 + arm_dy, 5, 4))
    pygame.draw.rect(s, DAN_SHIRT, (cx + 6, by + arm_dy, 5, 11))
    pygame.draw.rect(s, SKIN, (cx + 6, by + 10 + arm_dy, 5, 4))

    # Head
    head_y = by - 14
    pygame.draw.ellipse(s, SKIN, (cx - 6, head_y, 12, 12))
    # Straw hat
    pygame.draw.ellipse(s, (180, 160, 80), (cx - 10, head_y - 2, 20, 8))
    pygame.draw.rect(s, (160, 140, 70), (cx - 5, head_y - 4, 10, 5))
    # Eyes
    pygame.draw.rect(s, EYE, (cx - 3, head_y + 5, 2, 2))
    pygame.draw.rect(s, EYE, (cx + 1, head_y + 5, 2, 2))


def draw_demon_dan(s, body_dy=0, wing_angle=0, mouth_open=False):
    cx, cy = 32, 32
    by = cy + 4 + body_dy

    # Wings (behind body)
    for side in [-1, 1]:
        wx = cx + side * 12
        w_spread = 14 + int(wing_angle * 3)
        pts = [
            (wx, by - 6),
            (wx + side * w_spread, by - 18 - wing_angle),
            (wx + side * (w_spread - 4), by - 4),
            (wx + side * 6, by + 4),
        ]
        pygame.draw.polygon(s, DEMON_WING, pts)
        pygame.draw.polygon(s, DEMON_DARK, pts, 1)

    # Legs
    pygame.draw.rect(s, DEMON_DARK, (cx - 5, by + 14, 5, 14))
    pygame.draw.rect(s, DEMON_DARK, (cx + 1, by + 14, 5, 14))
    # Clawed feet
    pygame.draw.polygon(s, DEMON_DARK, [(cx - 7, by + 28), (cx - 2, by + 28), (cx - 4, by + 32)])
    pygame.draw.polygon(s, DEMON_DARK, [(cx + 0, by + 28), (cx + 5, by + 28), (cx + 3, by + 32)])

    # Body
    pygame.draw.rect(s, DEMON_RED, (cx - 8, by - 2, 16, 16), border_radius=3)
    pygame.draw.rect(s, DEMON_DARK, (cx - 8, by - 2, 16, 16), 1, border_radius=3)

    # Arms
    pygame.draw.rect(s, DEMON_RED, (cx - 13, by, 6, 12))
    pygame.draw.rect(s, DEMON_RED, (cx + 7, by, 6, 12))
    # Claws
    for ax in [cx - 13, cx + 7]:
        for j in range(3):
            pygame.draw.line(s, DEMON_DARK, (ax + j * 2, by + 12), (ax + j * 2, by + 16), 1)

    # Head
    head_y = by - 16
    pygame.draw.ellipse(s, DEMON_RED, (cx - 7, head_y, 14, 14))
    # Horns
    pygame.draw.polygon(s, DEMON_DARK, [(cx - 6, head_y + 2), (cx - 10, head_y - 8), (cx - 3, head_y + 1)])
    pygame.draw.polygon(s, DEMON_DARK, [(cx + 6, head_y + 2), (cx + 10, head_y - 8), (cx + 3, head_y + 1)])
    # Eyes
    pygame.draw.rect(s, DEMON_EYE, (cx - 4, head_y + 5, 3, 3))
    pygame.draw.rect(s, DEMON_EYE, (cx + 1, head_y + 5, 3, 3))
    pygame.draw.rect(s, (0, 0, 0), (cx - 3, head_y + 6, 1, 1))
    pygame.draw.rect(s, (0, 0, 0), (cx + 2, head_y + 6, 1, 1))
    # Mouth
    if mouth_open:
        pygame.draw.rect(s, (40, 0, 0), (cx - 3, head_y + 10, 6, 3))
        pygame.draw.rect(s, (255, 255, 255), (cx - 2, head_y + 10, 1, 2))
        pygame.draw.rect(s, (255, 255, 255), (cx + 1, head_y + 10, 1, 2))


def gen_dan():
    print("Generating Dan (farmer) avatar...")
    # Farmer idle
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        draw_dan_farmer(s, body_dy=dy)
        frames.append(s)
    save_sheet(frames, "dan_farmer_idle")

    # Farmer angry (fists up)
    frames = []
    for i in range(3):
        s = make_surf()
        draw_dan_farmer(s, body_dy=[0, -2, 0][i], arm_dy=[-3, -5, -3][i])
        frames.append(s)
    save_sheet(frames, "dan_farmer_angry")

    print("Generating Dan (demon) avatar...")
    # Demon idle
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, -1, 0][i]
        wa = [0, 1, 2, 1][i]
        draw_demon_dan(s, body_dy=dy, wing_angle=wa)
        frames.append(s)
    save_sheet(frames, "demon_idle")

    # Demon attack
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -3, -1, 1][i]
        wa = [1, 3, 4, 2][i]
        mo = i >= 1
        draw_demon_dan(s, body_dy=dy, wing_angle=wa, mouth_open=mo)
        frames.append(s)
    save_sheet(frames, "demon_attack")

    # Transform sequence (6 frames: farmer -> glitch -> demon)
    transform_frames = []
    for i in range(6):
        s = make_surf()
        if i < 2:
            draw_dan_farmer(s, body_dy=-i * 2, arm_dy=-i * 3)
        elif i < 4:
            # Glitch: both overlaid with shake
            draw_dan_farmer(s, body_dy=-2)
            overlay = make_surf()
            draw_demon_dan(overlay, body_dy=0, wing_angle=i - 2)
            overlay.set_alpha(60 * (i - 1))
            s.blit(overlay, (0, 0))
        else:
            draw_demon_dan(s, body_dy=(5 - i), wing_angle=i - 3, mouth_open=True)
        transform_frames.append(s)
    save_sheet(transform_frames, "dan_transform")


# ======================================================================
#  NARRATOR — hooded figure
# ======================================================================
def draw_narrator(s, body_dy=0, cloak_sway=0, glow=0):
    cx, cy = 32, 32
    by = cy + 4 + body_dy

    # Cloak body (triangular silhouette)
    pts = [
        (cx, by - 18),
        (cx - 16 + cloak_sway, by + 22),
        (cx + 16 + cloak_sway, by + 22),
    ]
    pygame.draw.polygon(s, CLOAK_PURPLE, pts)
    pygame.draw.polygon(s, CLOAK_DARK, pts, 1)

    # Inner robe fold
    inner_pts = [
        (cx, by - 10),
        (cx - 5 + cloak_sway, by + 18),
        (cx + 5 + cloak_sway, by + 18),
    ]
    pygame.draw.polygon(s, CLOAK_DARK, inner_pts)

    # Hood
    pygame.draw.ellipse(s, HOOD_GREY, (cx - 9, by - 22, 18, 16))
    pygame.draw.ellipse(s, HOOD_DARK, (cx - 7, by - 18, 14, 10))
    # Shadow face — just hint of eyes
    if glow > 0:
        eye_col = (180 + glow, 160 + glow, 80 + glow)
        pygame.draw.rect(s, eye_col, (cx - 4, by - 13, 2, 2))
        pygame.draw.rect(s, eye_col, (cx + 2, by - 13, 2, 2))

    # Wispy bottom (ragged edge)
    for i in range(-14, 15, 4):
        rag_y = by + 22 + abs(i) % 3
        pygame.draw.line(s, CLOAK_DARK, (cx + i + cloak_sway, by + 20), (cx + i + cloak_sway, rag_y))


def gen_narrator():
    print("Generating narrator avatar...")
    # Floating idle (6 frames)
    frames = []
    for i in range(6):
        s = make_surf()
        dy = [0, -1, -2, -2, -1, 0][i]
        sway = [-1, 0, 1, 1, 0, -1][i]
        glow = [20, 40, 60, 60, 40, 20][i]
        draw_narrator(s, body_dy=dy, cloak_sway=sway, glow=glow)
        frames.append(s)
    save_sheet(frames, "narrator_idle")


# ======================================================================
#  BACKGROUNDS
# ======================================================================
def gen_bg_forest():
    print("Generating forest background layers...")
    # Layer 0: far sky/fog
    sky = pygame.Surface((BG_W, BG_H))
    for y in range(BG_H):
        t = y / BG_H
        r = int(5 + 15 * t)
        g = int(15 + 30 * t)
        b = int(10 + 15 * t)
        pygame.draw.line(sky, (r, g, b), (0, y), (BG_W, y))
    # Moon
    pygame.draw.circle(sky, (60, 65, 80), (BG_W - 120, 80), 30)
    pygame.draw.circle(sky, (5 + 15, 15 + 10, 10 + 5), (BG_W - 110, 75), 28)  # shadow
    save_bg(sky, "forest_sky")

    # Layer 1: far trees (silhouettes)
    far = pygame.Surface((BG_W * 2, BG_H), pygame.SRCALPHA)
    far.fill(TRANSPARENT)
    import random
    random.seed(42)
    for i in range(20):
        tx = random.randint(0, BG_W * 2 - 40)
        th = random.randint(200, 400)
        tw = random.randint(20, 50)
        # Trunk
        pygame.draw.rect(far, (15, 25, 12), (tx + tw // 2 - 4, BG_H - th, 8, th))
        # Canopy
        for j in range(3):
            cy = BG_H - th + j * 30
            cw = tw + 20 - j * 8
            pygame.draw.ellipse(far, (10 + j * 3, 20 + j * 3, 8 + j * 2),
                                (tx + tw // 2 - cw // 2, cy - 20, cw, 50))
    save_bg(far, "forest_far_trees")

    # Layer 2: near trees + path
    near = pygame.Surface((BG_W * 2, BG_H), pygame.SRCALPHA)
    near.fill(TRANSPARENT)
    random.seed(99)
    for i in range(12):
        tx = random.randint(0, BG_W * 2 - 60)
        th = random.randint(280, 500)
        tw = random.randint(30, 70)
        trunk_c = (20 + random.randint(0, 10), 12, 8)
        pygame.draw.rect(near, trunk_c, (tx + tw // 2 - 6, BG_H - th, 12, th))
        for j in range(4):
            cy = BG_H - th + j * 25
            cw = tw + 30 - j * 6
            leaf_c = (8 + j * 4, 30 + j * 5, 5 + j * 3)
            pygame.draw.ellipse(near, leaf_c, (tx + tw // 2 - cw // 2, cy - 15, cw, 40))
    # Ground/path
    pygame.draw.rect(near, (25, 18, 10), (0, BG_H - 40, BG_W * 2, 40))
    save_bg(near, "forest_near_trees")

    # Fog layer
    fog = pygame.Surface((BG_W * 2, BG_H), pygame.SRCALPHA)
    random.seed(77)
    for i in range(30):
        fx = random.randint(0, BG_W * 2)
        fy = random.randint(BG_H // 2, BG_H - 30)
        fw = random.randint(100, 300)
        fh = random.randint(20, 50)
        fog_s = pygame.Surface((fw, fh), pygame.SRCALPHA)
        fog_s.fill((80, 100, 80, 12))
        fog.blit(fog_s, (fx, fy))
    save_bg(fog, "forest_fog")


def gen_bg_field():
    print("Generating field background...")
    s = pygame.Surface((BG_W, BG_H))
    # Sky gradient
    for y in range(BG_H // 2):
        t = y / (BG_H // 2)
        r = int(30 + 60 * t)
        g = int(40 + 70 * t)
        b = int(20 + 30 * t)
        pygame.draw.line(s, (r, g, b), (0, y), (BG_W, y))
    # Ground
    for y in range(BG_H // 2, BG_H):
        t = (y - BG_H // 2) / (BG_H // 2)
        r = int(35 + 20 * t)
        g = int(55 + 25 * t)
        b = int(15 + 10 * t)
        pygame.draw.line(s, (r, g, b), (0, y), (BG_W, y))
    # Crop rows
    import random
    random.seed(55)
    for row in range(8):
        ry = BG_H // 2 + 20 + row * 35
        for x in range(0, BG_W, 15):
            ch = random.randint(12, 25)
            cg = (50 + random.randint(0, 40), 80 + random.randint(0, 50), 20)
            pygame.draw.line(s, cg, (x, ry), (x + random.randint(-3, 3), ry - ch), 2)
    # Sun
    pygame.draw.circle(s, (120, 100, 40), (BG_W - 100, 60), 35)
    pygame.draw.circle(s, (140, 120, 50), (BG_W - 100, 60), 28)
    save_bg(s, "field")


def gen_bg_combat():
    print("Generating combat background...")
    s = pygame.Surface((BG_W, BG_H))
    # Dark red/black gradient
    for y in range(BG_H):
        t = y / BG_H
        r = int(40 + 30 * (1 - t))
        g = int(8 + 8 * (1 - t))
        b = int(8 + 5 * (1 - t))
        pygame.draw.line(s, (r, g, b), (0, y), (BG_W, y))
    # Rocky ground
    import random
    random.seed(33)
    for y in range(BG_H - 80, BG_H):
        for x in range(0, BG_W, 4):
            c = 20 + random.randint(0, 15)
            pygame.draw.rect(s, (c + 10, c, c), (x, y, 4, 4))
    # Fire/torch pillars
    for px in [100, BG_W - 100]:
        pygame.draw.rect(s, (50, 30, 20), (px - 8, BG_H - 200, 16, 200))
        for fi in range(5):
            fy = BG_H - 210 - fi * 4
            fw = 12 - fi * 2
            fc = (200 - fi * 30, 100 - fi * 15, 20)
            pygame.draw.ellipse(s, fc, (px - fw // 2, fy, fw, 10))
    save_bg(s, "combat")


def gen_bg_shop():
    print("Generating shop background...")
    s = pygame.Surface((BG_W, BG_H))
    # Interior walls
    s.fill((30, 25, 40))
    # Wooden floor
    for y in range(BG_H - 120, BG_H):
        t = (y - (BG_H - 120)) / 120
        for x in range(0, BG_W, 40):
            c = int(45 + 15 * t) + (x // 40 % 2) * 8
            pygame.draw.rect(s, (c + 10, c, c - 5), (x, y, 40, 1))
    # Stone wall pattern
    import random
    random.seed(88)
    for y in range(0, BG_H - 120, 24):
        offset = 20 if (y // 24) % 2 else 0
        for x in range(-20 + offset, BG_W + 20, 48):
            c = 30 + random.randint(0, 15)
            pygame.draw.rect(s, (c + 5, c + 3, c + 10), (x, y, 46, 22))
            pygame.draw.rect(s, (20, 18, 25), (x, y, 46, 22), 1)
    # Counter
    pygame.draw.rect(s, (60, 40, 25), (BG_W // 2 - 200, BG_H - 180, 400, 30))
    pygame.draw.rect(s, (80, 55, 30), (BG_W // 2 - 200, BG_H - 185, 400, 8))
    # Torches on wall
    for tx in [150, BG_W - 150]:
        pygame.draw.rect(s, (70, 50, 30), (tx - 3, 100, 6, 30))
        for fi in range(4):
            fy = 95 - fi * 5
            fw = 10 - fi * 2
            fc = (220 - fi * 30, 120 - fi * 20, 30)
            pygame.draw.ellipse(s, fc, (tx - fw // 2, fy, fw, 8))
    # Shelves with items
    for sy in [80, 160]:
        pygame.draw.rect(s, (55, 35, 20), (BG_W // 2 - 150, sy, 300, 6))
        for i in range(6):
            ix = BG_W // 2 - 140 + i * 50
            c = [(180, 40, 40), (40, 120, 180), (180, 160, 40), (80, 180, 80), (180, 80, 180), (140, 100, 60)][i]
            pygame.draw.rect(s, c, (ix, sy - 16, 12, 16), border_radius=2)
    save_bg(s, "shop")


def gen_bg_menu():
    print("Generating menu background...")
    s = pygame.Surface((BG_W, BG_H))
    for y in range(BG_H):
        t = y / BG_H
        r = int(12 + 12 * t)
        g = int(12 + 12 * t)
        b = int(25 + 20 * t)
        pygame.draw.line(s, (r, g, b), (0, y), (BG_W, y))
    # Subtle pattern
    import random
    random.seed(11)
    for _ in range(60):
        x = random.randint(0, BG_W)
        y = random.randint(0, BG_H)
        r = random.randint(2, 6)
        a = random.randint(10, 30)
        cs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(cs, (100, 100, 140, a), (r, r), r)
        s.blit(cs, (x - r, y - r))
    save_bg(s, "menu")


def gen_bg_gameover():
    print("Generating gameover background...")
    s = pygame.Surface((BG_W, BG_H))
    for y in range(BG_H):
        t = y / BG_H
        r = int(15 * (1 - t))
        pygame.draw.line(s, (r + 5, r, r), (0, y), (BG_W, y))
    # Blood drip effect
    import random
    random.seed(66)
    for _ in range(20):
        x = random.randint(0, BG_W)
        h = random.randint(50, 200)
        w = random.randint(2, 5)
        pygame.draw.rect(s, (60 + random.randint(0, 30), 0, 0), (x, 0, w, h))
    save_bg(s, "gameover")


def gen_bg_loot():
    print("Generating loot background...")
    s = pygame.Surface((BG_W, BG_H))
    for y in range(BG_H):
        t = y / BG_H
        r = int(25 + 15 * t)
        g = int(15 + 10 * t)
        b = int(35 + 20 * t)
        pygame.draw.line(s, (r, g, b), (0, y), (BG_W, y))
    # Sparkle particles
    import random
    random.seed(44)
    for _ in range(40):
        x = random.randint(0, BG_W)
        y = random.randint(0, BG_H)
        sz = random.randint(1, 3)
        c = random.choice([(255, 215, 80), (200, 180, 255), (255, 255, 200)])
        pygame.draw.circle(s, c, (x, y), sz)
    save_bg(s, "loot")


# ======================================================================
#  ARCADE MONSTERS
# ======================================================================

# --- Skeleton Warrior ---
SKEL_BONE = (210, 200, 180)
SKEL_DARK = (140, 130, 110)
SKEL_EYE = (255, 60, 60)

def draw_skeleton(s, body_dy=0, arm_angle=0, jaw_open=False):
    cx, cy = 32, 32
    by = cy + 6 + body_dy
    # Legs (bones)
    for lx in [cx - 5, cx + 2]:
        pygame.draw.rect(s, SKEL_BONE, (lx, by + 14, 3, 12))
        pygame.draw.rect(s, SKEL_DARK, (lx - 1, by + 24, 5, 3))  # feet
    # Ribcage
    pygame.draw.rect(s, SKEL_BONE, (cx - 7, by - 2, 14, 14), border_radius=2)
    for rib in range(3):
        ry = by + rib * 4
        pygame.draw.line(s, SKEL_DARK, (cx - 6, ry), (cx + 6, ry), 1)
    # Spine
    pygame.draw.line(s, SKEL_DARK, (cx, by - 2), (cx, by + 14), 2)
    # Arms
    la_y = by + 1 + int(arm_angle * 0.3)
    pygame.draw.rect(s, SKEL_BONE, (cx - 11, la_y, 4, 10))
    pygame.draw.rect(s, SKEL_BONE, (cx + 7, la_y, 4, 10))
    # Sword in right hand
    sw_y = la_y - 6 - int(arm_angle * 2)
    pygame.draw.rect(s, (80, 80, 80), (cx + 8, la_y + 2, 2, 6))  # hilt
    pygame.draw.rect(s, (180, 180, 200), (cx + 8, sw_y, 2, 10))  # blade
    # Skull
    head_y = by - 16
    pygame.draw.ellipse(s, SKEL_BONE, (cx - 6, head_y, 12, 12))
    pygame.draw.rect(s, SKEL_EYE, (cx - 4, head_y + 4, 2, 2))
    pygame.draw.rect(s, SKEL_EYE, (cx + 2, head_y + 4, 2, 2))
    jaw_dy = 2 if jaw_open else 0
    pygame.draw.rect(s, SKEL_DARK, (cx - 3, head_y + 8 + jaw_dy, 6, 2))


def gen_skeleton():
    print("Generating skeleton warrior...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        draw_skeleton(s, body_dy=dy)
        frames.append(s)
    save_sheet(frames, "skeleton_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        arm = [0, 3, 6, 2][i]
        dy = [0, -2, 0, 1][i]
        draw_skeleton(s, body_dy=dy, arm_angle=arm, jaw_open=i >= 1)
        frames.append(s)
    save_sheet(frames, "skeleton_attack")


# --- Slime ---
SLIME_GREEN = (40, 180, 60)
SLIME_DARK = (25, 120, 35)
SLIME_LIGHT = (80, 220, 100)
SLIME_EYE = (255, 255, 255)

def draw_slime(s, body_dy=0, squash=0, mouth_open=False):
    cx, cy = 32, 36
    by = cy + body_dy
    w = 20 + squash * 2
    h = 16 - squash
    pygame.draw.ellipse(s, SLIME_GREEN, (cx - w // 2, by - h, w, h * 2))
    pygame.draw.ellipse(s, SLIME_DARK, (cx - w // 2, by - h, w, h * 2), 1)
    # Highlight
    pygame.draw.ellipse(s, SLIME_LIGHT, (cx - 4, by - h + 3, 6, 4))
    # Eyes
    pygame.draw.circle(s, SLIME_EYE, (cx - 4, by - 2), 3)
    pygame.draw.circle(s, SLIME_EYE, (cx + 4, by - 2), 3)
    pygame.draw.circle(s, (0, 0, 0), (cx - 3, by - 1), 1)
    pygame.draw.circle(s, (0, 0, 0), (cx + 5, by - 1), 1)
    if mouth_open:
        pygame.draw.ellipse(s, (20, 80, 30), (cx - 3, by + 3, 6, 4))


def gen_slime():
    print("Generating slime...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -2, 0, 2][i]
        sq = [0, -1, 0, 1][i]
        draw_slime(s, body_dy=dy, squash=sq)
        frames.append(s)
    save_sheet(frames, "slime_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -4, -2, 2][i]
        sq = [0, -2, 0, 2][i]
        draw_slime(s, body_dy=dy, squash=sq, mouth_open=i >= 1)
        frames.append(s)
    save_sheet(frames, "slime_attack")


# --- Shadow Wraith ---
WRAITH_DARK = (20, 10, 30)
WRAITH_PURPLE = (60, 20, 80)
WRAITH_EYE = (180, 60, 220)

def draw_wraith(s, body_dy=0, sway=0, glow=0):
    cx, cy = 32, 30
    by = cy + body_dy
    # Ghostly body (triangle tapering down)
    pts = [
        (cx, by - 16),
        (cx - 14 + sway, by + 20),
        (cx + 14 + sway, by + 20),
    ]
    pygame.draw.polygon(s, WRAITH_PURPLE, pts)
    pygame.draw.polygon(s, WRAITH_DARK, pts, 1)
    # Inner shadow
    inner = [
        (cx, by - 8),
        (cx - 6 + sway, by + 16),
        (cx + 6 + sway, by + 16),
    ]
    pygame.draw.polygon(s, WRAITH_DARK, inner)
    # Ragged bottom
    for i in range(-12, 13, 3):
        rag_y = by + 20 + abs(i) % 4
        pygame.draw.line(s, WRAITH_DARK, (cx + i + sway, by + 18), (cx + i + sway, rag_y))
    # Face - glowing eyes
    eye_c = (min(255, WRAITH_EYE[0] + glow), min(255, WRAITH_EYE[1] + glow), min(255, WRAITH_EYE[2] + glow))
    pygame.draw.rect(s, eye_c, (cx - 5, by - 8, 3, 2))
    pygame.draw.rect(s, eye_c, (cx + 2, by - 8, 3, 2))
    # Glow aura
    if glow > 0:
        aura = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.circle(aura, (WRAITH_EYE[0], WRAITH_EYE[1], WRAITH_EYE[2], min(40, glow * 2)), (14, 14), 14)
        s.blit(aura, (cx - 14, by - 20))


def gen_wraith():
    print("Generating shadow wraith...")
    frames = []
    for i in range(6):
        s = make_surf()
        dy = [0, -1, -2, -2, -1, 0][i]
        sw = [-1, 0, 1, 1, 0, -1][i]
        gl = [10, 20, 30, 30, 20, 10][i]
        draw_wraith(s, body_dy=dy, sway=sw, glow=gl)
        frames.append(s)
    save_sheet(frames, "wraith_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -3, -1, 1][i]
        sw = [0, -2, 2, 0][i]
        gl = [20, 50, 60, 30][i]
        draw_wraith(s, body_dy=dy, sway=sw, glow=gl)
        frames.append(s)
    save_sheet(frames, "wraith_attack")


# --- Fire Golem ---
GOLEM_ORANGE = (180, 80, 20)
GOLEM_DARK = (100, 40, 10)
GOLEM_FIRE = (230, 140, 30)
GOLEM_CORE = (255, 200, 50)

def draw_golem(s, body_dy=0, arm_raise=0, flame=0):
    cx, cy = 32, 30
    by = cy + 4 + body_dy
    # Legs (thick rock)
    pygame.draw.rect(s, GOLEM_DARK, (cx - 7, by + 12, 6, 14))
    pygame.draw.rect(s, GOLEM_DARK, (cx + 1, by + 12, 6, 14))
    pygame.draw.rect(s, GOLEM_DARK, (cx - 8, by + 24, 8, 4))
    pygame.draw.rect(s, GOLEM_DARK, (cx + 0, by + 24, 8, 4))
    # Body (large rocky torso)
    pygame.draw.rect(s, GOLEM_ORANGE, (cx - 10, by - 6, 20, 18), border_radius=4)
    pygame.draw.rect(s, GOLEM_DARK, (cx - 10, by - 6, 20, 18), 1, border_radius=4)
    # Core glow
    pygame.draw.circle(s, GOLEM_CORE, (cx, by + 4), 4)
    pygame.draw.circle(s, GOLEM_FIRE, (cx, by + 4), 2)
    # Cracks
    pygame.draw.line(s, GOLEM_FIRE, (cx - 6, by - 2), (cx - 2, by + 6), 1)
    pygame.draw.line(s, GOLEM_FIRE, (cx + 4, by - 3), (cx + 2, by + 4), 1)
    # Arms
    arm_y = by - 2 - arm_raise
    pygame.draw.rect(s, GOLEM_ORANGE, (cx - 16, arm_y, 7, 14))
    pygame.draw.rect(s, GOLEM_ORANGE, (cx + 9, arm_y, 7, 14))
    pygame.draw.rect(s, GOLEM_DARK, (cx - 16, arm_y, 7, 14), 1)
    pygame.draw.rect(s, GOLEM_DARK, (cx + 9, arm_y, 7, 14), 1)
    # Fists
    pygame.draw.rect(s, GOLEM_DARK, (cx - 17, arm_y + 12, 8, 6), border_radius=2)
    pygame.draw.rect(s, GOLEM_DARK, (cx + 9, arm_y + 12, 8, 6), border_radius=2)
    # Head (small rocky)
    head_y = by - 16
    pygame.draw.rect(s, GOLEM_ORANGE, (cx - 6, head_y, 12, 10), border_radius=3)
    pygame.draw.rect(s, GOLEM_DARK, (cx - 6, head_y, 12, 10), 1, border_radius=3)
    pygame.draw.rect(s, GOLEM_CORE, (cx - 4, head_y + 3, 2, 2))
    pygame.draw.rect(s, GOLEM_CORE, (cx + 2, head_y + 3, 2, 2))
    # Flame on head
    if flame > 0:
        for fi in range(flame):
            fy = head_y - 4 - fi * 3
            fw = 8 - fi * 2
            if fw > 0:
                fc = (min(255, 230 + fi * 10), max(0, 140 - fi * 30), 20)
                pygame.draw.ellipse(s, fc, (cx - fw // 2, fy, fw, 6))


def gen_golem():
    print("Generating fire golem...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        fl = [1, 2, 2, 1][i]
        draw_golem(s, body_dy=dy, flame=fl)
        frames.append(s)
    save_sheet(frames, "golem_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -3, -1, 1][i]
        ar = [0, 4, 6, 2][i]
        fl = [2, 3, 3, 2][i]
        draw_golem(s, body_dy=dy, arm_raise=ar, flame=fl)
        frames.append(s)
    save_sheet(frames, "golem_attack")


# --- Ice Spider ---
SPIDER_BLUE = (80, 140, 200)
SPIDER_DARK = (40, 70, 120)
SPIDER_ICE = (180, 220, 255)
SPIDER_EYE = (255, 40, 40)

def draw_spider(s, body_dy=0, leg_phase=0, fang_open=False):
    cx, cy = 32, 34
    by = cy + body_dy
    # Legs (4 per side)
    for side in [-1, 1]:
        for j in range(4):
            off = (j - 1.5) * 5
            ly = by - 2 + off
            phase = leg_phase * (1 if j % 2 == 0 else -1)
            knee_x = cx + side * 14
            knee_y = ly + phase
            foot_x = cx + side * 20
            foot_y = ly + 6 + abs(phase)
            pygame.draw.line(s, SPIDER_BLUE, (cx + side * 6, ly), (knee_x, knee_y), 2)
            pygame.draw.line(s, SPIDER_DARK, (knee_x, knee_y), (foot_x, foot_y), 2)
    # Abdomen (back)
    pygame.draw.ellipse(s, SPIDER_BLUE, (cx - 6, by + 2, 12, 10))
    pygame.draw.ellipse(s, SPIDER_DARK, (cx - 6, by + 2, 12, 10), 1)
    # Ice pattern on abdomen
    pygame.draw.line(s, SPIDER_ICE, (cx - 2, by + 4), (cx + 2, by + 8), 1)
    pygame.draw.line(s, SPIDER_ICE, (cx + 2, by + 4), (cx - 2, by + 8), 1)
    # Cephalothorax (head)
    pygame.draw.ellipse(s, SPIDER_BLUE, (cx - 5, by - 8, 10, 10))
    pygame.draw.ellipse(s, SPIDER_DARK, (cx - 5, by - 8, 10, 10), 1)
    # Eyes (cluster)
    for ex, ey in [(-3, -5), (-1, -6), (1, -6), (3, -5)]:
        pygame.draw.rect(s, SPIDER_EYE, (cx + ex, by + ey, 2, 2))
    # Fangs
    fang_dy = 2 if fang_open else 0
    pygame.draw.line(s, SPIDER_ICE, (cx - 2, by), (cx - 3, by + 4 + fang_dy), 2)
    pygame.draw.line(s, SPIDER_ICE, (cx + 2, by), (cx + 3, by + 4 + fang_dy), 2)


def gen_spider():
    print("Generating ice spider...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        lp = [-1, 0, 1, 0][i]
        draw_spider(s, body_dy=dy, leg_phase=lp)
        frames.append(s)
    save_sheet(frames, "spider_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -2, -1, 1][i]
        lp = [0, 2, -1, 0][i]
        draw_spider(s, body_dy=dy, leg_phase=lp, fang_open=i >= 1)
        frames.append(s)
    save_sheet(frames, "spider_attack")


# --- Dark Knight ---
DK_ARMOR = (30, 30, 40)
DK_TRIM = (80, 70, 100)
DK_VISOR = (160, 40, 40)
DK_BLADE = (120, 100, 140)
DK_CAPE = (40, 15, 50)

def draw_dark_knight(s, body_dy=0, arm_angle=0, cape_sway=0):
    cx, cy = 32, 32
    by = cy + 6 + body_dy
    # Cape
    cape_pts = [
        (cx - 8 + cape_sway, by - 12),
        (cx - 16 + cape_sway * 2, by + 20),
        (cx + 4 + cape_sway, by + 18),
    ]
    pygame.draw.polygon(s, DK_CAPE, cape_pts)
    pygame.draw.polygon(s, (20, 8, 30), cape_pts, 1)
    # Legs
    pygame.draw.rect(s, DK_ARMOR, (cx - 6, by + 14, 5, 14))
    pygame.draw.rect(s, DK_ARMOR, (cx + 1, by + 14, 5, 14))
    pygame.draw.rect(s, DK_TRIM, (cx - 7, by + 26, 7, 4))
    pygame.draw.rect(s, DK_TRIM, (cx + 0, by + 26, 7, 4))
    # Body
    pygame.draw.rect(s, DK_ARMOR, (cx - 8, by - 2, 16, 16), border_radius=2)
    pygame.draw.rect(s, DK_TRIM, (cx - 8, by - 2, 16, 16), 1, border_radius=2)
    # Cross emblem
    pygame.draw.line(s, DK_VISOR, (cx, by + 1), (cx, by + 9), 2)
    pygame.draw.line(s, DK_VISOR, (cx - 3, by + 5), (cx + 3, by + 5), 2)
    # Arms
    la_y = by + 1
    pygame.draw.rect(s, DK_ARMOR, (cx - 12, la_y, 5, 12))
    ra_y = by + 1 + int(arm_angle * 0.5)
    pygame.draw.rect(s, DK_ARMOR, (cx + 7, ra_y, 5, 12))
    # Dark sword
    sw_y = ra_y - 8 - int(arm_angle * 2)
    pygame.draw.rect(s, (50, 40, 60), (cx + 8, ra_y + 2, 3, 6))  # hilt
    pygame.draw.rect(s, DK_BLADE, (cx + 8, sw_y, 3, 12))  # blade
    pygame.draw.rect(s, DK_VISOR, (cx + 9, sw_y, 1, 10))  # edge glow
    # Helm
    head_y = by - 16
    pygame.draw.ellipse(s, DK_ARMOR, (cx - 7, head_y, 14, 14))
    pygame.draw.rect(s, DK_TRIM, (cx - 7, head_y + 4, 14, 2))
    # Visor slit
    pygame.draw.rect(s, DK_VISOR, (cx - 4, head_y + 5, 8, 2))
    # Horns on helm
    pygame.draw.polygon(s, DK_TRIM, [(cx - 6, head_y + 2), (cx - 8, head_y - 4), (cx - 4, head_y + 1)])
    pygame.draw.polygon(s, DK_TRIM, [(cx + 6, head_y + 2), (cx + 8, head_y - 4), (cx + 4, head_y + 1)])


def gen_dark_knight():
    print("Generating dark knight...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        cape = [0, 1, 0, -1][i]
        draw_dark_knight(s, body_dy=dy, cape_sway=cape)
        frames.append(s)
    save_sheet(frames, "dark_knight_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        arm = [0, 3, 6, 2][i]
        dy = [0, -2, 0, 1][i]
        draw_dark_knight(s, body_dy=dy, arm_angle=arm, cape_sway=[0, 1, 2, 1][i])
        frames.append(s)
    save_sheet(frames, "dark_knight_attack")


# ======================================================================
#  ARCADE BACKGROUND
# ======================================================================
def gen_bg_arcade():
    print("Generating arcade background...")
    s = pygame.Surface((BG_W, BG_H))
    # Dark purple/blue gradient
    for y in range(BG_H):
        t = y / BG_H
        r = int(20 + 25 * (1 - t))
        g = int(5 + 10 * (1 - t))
        b = int(40 + 30 * (1 - t))
        pygame.draw.line(s, (r, g, b), (0, y), (BG_W, y))
    # Arena floor
    import random
    random.seed(77)
    for y in range(BG_H - 100, BG_H):
        for x in range(0, BG_W, 4):
            c = 15 + random.randint(0, 12)
            pygame.draw.rect(s, (c + 5, c, c + 8), (x, y, 4, 4))
    # Pillars with blue flames
    for px in [80, BG_W // 3, BG_W * 2 // 3, BG_W - 80]:
        pygame.draw.rect(s, (35, 25, 50), (px - 8, BG_H - 220, 16, 220))
        for fi in range(5):
            fy = BG_H - 230 - fi * 4
            fw = 12 - fi * 2
            fc = (40 + fi * 10, 60 + fi * 20, 200 - fi * 20)
            pygame.draw.ellipse(s, fc, (px - fw // 2, fy, fw, 10))
    # Skull decorations at base of pillars
    for px in [80, BG_W - 80]:
        pygame.draw.circle(s, (180, 170, 150), (px, BG_H - 110), 8)
        pygame.draw.rect(s, (40, 0, 0), (px - 3, BG_H - 112, 2, 2))
        pygame.draw.rect(s, (40, 0, 0), (px + 1, BG_H - 112, 2, 2))
    save_bg(s, "arcade")


# ======================================================================
#  STORY EXPANSION — NEW SPRITES
# ======================================================================

# --- Imp (Grub) ---
IMP_GREY = (80, 70, 90)
IMP_DARK = (50, 40, 60)
IMP_EYE = (255, 180, 0)

def draw_imp(s, body_dy=0, wing_angle=0, grin=False):
    cx, cy = 32, 36
    by = cy + body_dy
    # Tiny wings
    for side in [-1, 1]:
        wx = cx + side * 8
        pts = [
            (wx, by - 6),
            (wx + side * (8 + wing_angle), by - 12 - wing_angle),
            (wx + side * 4, by - 2),
        ]
        pygame.draw.polygon(s, IMP_DARK, pts)
    # Body (small, hunched)
    pygame.draw.ellipse(s, IMP_GREY, (cx - 8, by - 4, 16, 14))
    pygame.draw.ellipse(s, IMP_DARK, (cx - 8, by - 4, 16, 14), 1)
    # Legs
    pygame.draw.rect(s, IMP_DARK, (cx - 5, by + 8, 3, 8))
    pygame.draw.rect(s, IMP_DARK, (cx + 2, by + 8, 3, 8))
    # Arms
    pygame.draw.rect(s, IMP_GREY, (cx - 12, by, 4, 8))
    pygame.draw.rect(s, IMP_GREY, (cx + 8, by, 4, 8))
    # Head
    head_y = by - 14
    pygame.draw.ellipse(s, IMP_GREY, (cx - 7, head_y, 14, 12))
    # Pointy ears
    pygame.draw.polygon(s, IMP_GREY, [(cx - 7, head_y + 3), (cx - 12, head_y - 4), (cx - 4, head_y + 1)])
    pygame.draw.polygon(s, IMP_GREY, [(cx + 7, head_y + 3), (cx + 12, head_y - 4), (cx + 4, head_y + 1)])
    # Eyes
    pygame.draw.rect(s, IMP_EYE, (cx - 4, head_y + 4, 3, 2))
    pygame.draw.rect(s, IMP_EYE, (cx + 1, head_y + 4, 3, 2))
    if grin:
        pygame.draw.arc(s, (200, 200, 200), (cx - 4, head_y + 7, 8, 4), 3.14, 6.28, 1)


def gen_imp():
    print("Generating imp (Grub)...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -2, 0, 2][i]
        wa = [0, 1, 2, 1][i]
        draw_imp(s, body_dy=dy, wing_angle=wa, grin=(i % 2 == 0))
        frames.append(s)
    save_sheet(frames, "imp_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -3, -1, 1][i]
        wa = [1, 3, 2, 0][i]
        draw_imp(s, body_dy=dy, wing_angle=wa, grin=True)
        frames.append(s)
    save_sheet(frames, "imp_attack")


# --- Oracle Ysel ---
ORACLE_ROBE = (60, 50, 80)
ORACLE_SHAWL = (100, 80, 120)
ORACLE_EYE = (200, 210, 220)

def draw_oracle(s, body_dy=0, sway=0):
    cx, cy = 32, 32
    by = cy + 6 + body_dy
    # Robe (full body flowing)
    pts = [
        (cx - 2, by - 14),
        (cx + 2, by - 14),
        (cx + 14 + sway, by + 24),
        (cx - 14 + sway, by + 24),
    ]
    pygame.draw.polygon(s, ORACLE_ROBE, pts)
    pygame.draw.polygon(s, (40, 30, 60), pts, 1)
    # Shawl
    pygame.draw.polygon(s, ORACLE_SHAWL, [
        (cx - 10, by - 4), (cx + 10, by - 4),
        (cx + 14 + sway, by + 8), (cx - 14 + sway, by + 8),
    ])
    # Hands
    pygame.draw.circle(s, (180, 150, 120), (cx - 10 + sway, by + 6), 3)
    pygame.draw.circle(s, (180, 150, 120), (cx + 10 + sway, by + 6), 3)
    # Head
    head_y = by - 22
    pygame.draw.ellipse(s, (180, 150, 120), (cx - 5, head_y, 10, 10))
    # Silver eyes
    pygame.draw.rect(s, ORACLE_EYE, (cx - 3, head_y + 4, 2, 2))
    pygame.draw.rect(s, ORACLE_EYE, (cx + 1, head_y + 4, 2, 2))
    # Hair (white, wispy)
    pygame.draw.arc(s, (200, 200, 210), (cx - 8, head_y - 3, 16, 10), 0, 3.14, 2)


def gen_oracle():
    print("Generating oracle Ysel...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        sw = [0, 1, 0, -1][i]
        draw_oracle(s, body_dy=dy, sway=sw)
        frames.append(s)
    save_sheet(frames, "oracle_idle")


# --- Cave Dragon Veth ---
DRAGON_GOLD = (180, 160, 60)
DRAGON_DARK = (100, 80, 30)
DRAGON_SCALE = (140, 120, 40)
DRAGON_EYE = (255, 100, 0)

def draw_dragon(s, body_dy=0, wing_angle=0, mouth_open=False):
    cx, cy = 32, 30
    by = cy + body_dy
    # Wings
    for side in [-1, 1]:
        wx = cx + side * 10
        w_spread = 16 + wing_angle * 2
        pts = [
            (wx, by - 4),
            (wx + side * w_spread, by - 16 - wing_angle),
            (wx + side * (w_spread - 6), by + 2),
            (wx + side * 4, by + 6),
        ]
        pygame.draw.polygon(s, DRAGON_DARK, pts)
        pygame.draw.polygon(s, DRAGON_SCALE, pts, 1)
    # Body (bulky)
    pygame.draw.ellipse(s, DRAGON_GOLD, (cx - 12, by - 6, 24, 20))
    pygame.draw.ellipse(s, DRAGON_DARK, (cx - 12, by - 6, 24, 20), 1)
    # Belly scales
    pygame.draw.ellipse(s, DRAGON_SCALE, (cx - 6, by - 2, 12, 14))
    # Legs
    pygame.draw.rect(s, DRAGON_GOLD, (cx - 10, by + 12, 5, 10))
    pygame.draw.rect(s, DRAGON_GOLD, (cx + 5, by + 12, 5, 10))
    # Claws
    for lx in [cx - 10, cx + 5]:
        for j in range(3):
            pygame.draw.line(s, DRAGON_DARK, (lx + j * 2, by + 22), (lx + j * 2, by + 25), 1)
    # Tail
    pygame.draw.arc(s, DRAGON_GOLD, (cx + 8, by + 4, 20, 16), 0, 2.5, 3)
    # Neck + Head
    head_y = by - 18
    pygame.draw.rect(s, DRAGON_GOLD, (cx - 3, by - 12, 6, 8))
    pygame.draw.ellipse(s, DRAGON_GOLD, (cx - 8, head_y, 16, 12))
    # Horns
    pygame.draw.polygon(s, DRAGON_DARK, [(cx - 6, head_y + 2), (cx - 9, head_y - 6), (cx - 3, head_y + 1)])
    pygame.draw.polygon(s, DRAGON_DARK, [(cx + 6, head_y + 2), (cx + 9, head_y - 6), (cx + 3, head_y + 1)])
    # Eyes
    pygame.draw.rect(s, DRAGON_EYE, (cx - 5, head_y + 5, 3, 2))
    pygame.draw.rect(s, DRAGON_EYE, (cx + 2, head_y + 5, 3, 2))
    if mouth_open:
        pygame.draw.rect(s, (200, 60, 0), (cx - 4, head_y + 9, 8, 3))
        # Fire breath
        pygame.draw.polygon(s, (255, 160, 0), [(cx, head_y + 12), (cx - 6, head_y + 18), (cx + 6, head_y + 18)])


def gen_dragon():
    print("Generating cave dragon Veth...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        wa = [0, 1, 2, 1][i]
        draw_dragon(s, body_dy=dy, wing_angle=wa)
        frames.append(s)
    save_sheet(frames, "dragon_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -2, 0, 1][i]
        wa = [1, 3, 2, 0][i]
        draw_dragon(s, body_dy=dy, wing_angle=wa, mouth_open=(i >= 1))
        frames.append(s)
    save_sheet(frames, "dragon_attack")


# --- Mirror Wraith ---
MIRROR_SILVER = (180, 190, 200)
MIRROR_DARK = (100, 110, 130)
MIRROR_GLOW = (200, 220, 255)

def draw_mirror_wraith(s, body_dy=0, sway=0, flicker=0):
    cx, cy = 32, 30
    by = cy + body_dy
    # Ghostly reflected player shape
    pts = [
        (cx, by - 16),
        (cx - 12 + sway, by + 18),
        (cx + 12 + sway, by + 18),
    ]
    pygame.draw.polygon(s, MIRROR_SILVER, pts)
    pygame.draw.polygon(s, MIRROR_DARK, pts, 1)
    # Glass shards floating around
    for sx, sy in [(-10, -5), (10, -8), (-8, 10), (12, 5)]:
        pygame.draw.rect(s, MIRROR_GLOW, (cx + sx + sway, by + sy, 3, 5), 1)
    # Face - glowing white eyes
    eye_c = (min(255, 200 + flicker), min(255, 220 + flicker), 255)
    pygame.draw.rect(s, eye_c, (cx - 5, by - 8, 3, 2))
    pygame.draw.rect(s, eye_c, (cx + 2, by - 8, 3, 2))
    # Mirror border outline
    pygame.draw.rect(s, MIRROR_GLOW, (cx - 14 + sway, by - 18, 28, 38), 1)


def gen_mirror_wraith():
    print("Generating mirror wraith...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        sw = [0, 2, 0, -2][i]
        fl = [0, 20, 40, 20][i]
        draw_mirror_wraith(s, body_dy=dy, sway=sw, flicker=fl)
        frames.append(s)
    save_sheet(frames, "mirror_wraith_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -3, -1, 1][i]
        sw = [0, 3, -3, 0][i]
        fl = [20, 50, 40, 10][i]
        draw_mirror_wraith(s, body_dy=dy, sway=sw, flicker=fl)
        frames.append(s)
    save_sheet(frames, "mirror_wraith_attack")


# --- Revenant Knight ---
REV_ARMOR = (60, 65, 75)
REV_DARK = (30, 32, 40)
REV_GLOW = (255, 200, 50)
REV_RED_GLOW = (255, 50, 30)

def draw_revenant(s, body_dy=0, arm_angle=0, eyes_gold=True):
    cx, cy = 32, 32
    by = cy + 6 + body_dy
    # Heavy armor legs
    pygame.draw.rect(s, REV_ARMOR, (cx - 6, by + 14, 5, 14))
    pygame.draw.rect(s, REV_ARMOR, (cx + 1, by + 14, 5, 14))
    pygame.draw.rect(s, REV_DARK, (cx - 7, by + 26, 7, 4))
    pygame.draw.rect(s, REV_DARK, (cx + 0, by + 26, 7, 4))
    # Body (heavy dark armor)
    pygame.draw.rect(s, REV_ARMOR, (cx - 9, by - 2, 18, 16), border_radius=2)
    pygame.draw.rect(s, REV_DARK, (cx - 9, by - 2, 18, 16), 1, border_radius=2)
    # Crest on chest
    pygame.draw.polygon(s, REV_GLOW if eyes_gold else REV_RED_GLOW, [
        (cx, by), (cx - 3, by + 5), (cx, by + 8), (cx + 3, by + 5)
    ])
    # Arms
    ra_y = by + 1 + int(arm_angle * 0.4)
    pygame.draw.rect(s, REV_ARMOR, (cx - 13, by + 1, 5, 12))
    pygame.draw.rect(s, REV_ARMOR, (cx + 8, ra_y, 5, 12))
    # Greatsword
    sw_y = ra_y - 10 - int(arm_angle * 2)
    pygame.draw.rect(s, (40, 40, 50), (cx + 9, ra_y + 2, 3, 8))  # hilt
    pygame.draw.rect(s, (120, 120, 140), (cx + 9, sw_y, 3, 14))  # blade
    # Shadow fire on sword
    if not eyes_gold:
        for fi in range(3):
            pygame.draw.ellipse(s, (60 + fi * 20, 10, 40 - fi * 10, 80),
                                (cx + 7, sw_y - fi * 3, 7, 5))
    # Head (helmet)
    head_y = by - 16
    pygame.draw.rect(s, REV_ARMOR, (cx - 7, head_y, 14, 14), border_radius=3)
    pygame.draw.rect(s, REV_DARK, (cx - 7, head_y, 14, 14), 1, border_radius=3)
    # Visor slit
    eye_c = REV_GLOW if eyes_gold else REV_RED_GLOW
    pygame.draw.rect(s, eye_c, (cx - 5, head_y + 5, 10, 2))
    # Plume
    pygame.draw.rect(s, REV_DARK, (cx - 1, head_y - 4, 2, 5))


def gen_revenant():
    print("Generating revenant knight...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        draw_revenant(s, body_dy=dy, eyes_gold=False)
        frames.append(s)
    save_sheet(frames, "revenant_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        arm = [0, 3, 6, 2][i]
        dy = [0, -2, 0, 1][i]
        draw_revenant(s, body_dy=dy, arm_angle=arm, eyes_gold=False)
        frames.append(s)
    save_sheet(frames, "revenant_attack")


# --- Malachar the Archdemon ---
MALACH_BLACK = (15, 10, 20)
MALACH_DARK = (40, 20, 50)
MALACH_PURPLE = (120, 40, 160)
MALACH_EYE = (255, 0, 100)

def draw_malachar(s, body_dy=0, wing_angle=0, aura=0):
    cx, cy = 32, 28
    by = cy + body_dy
    # Massive wings
    for side in [-1, 1]:
        wx = cx + side * 10
        w_spread = 20 + wing_angle * 2
        pts = [
            (wx, by - 6),
            (wx + side * w_spread, by - 22 - wing_angle),
            (wx + side * (w_spread - 4), by - 8),
            (wx + side * 8, by + 6),
        ]
        pygame.draw.polygon(s, MALACH_DARK, pts)
        pygame.draw.polygon(s, MALACH_PURPLE, pts, 1)
    # Body armor (absorbs light)
    pygame.draw.rect(s, MALACH_BLACK, (cx - 10, by - 4, 20, 18), border_radius=3)
    pygame.draw.rect(s, MALACH_DARK, (cx - 10, by - 4, 20, 18), 1, border_radius=3)
    # Purple runes on armor
    for ry in [by, by + 6]:
        pygame.draw.line(s, MALACH_PURPLE, (cx - 6, ry), (cx + 6, ry), 1)
    # Legs
    pygame.draw.rect(s, MALACH_BLACK, (cx - 6, by + 14, 5, 14))
    pygame.draw.rect(s, MALACH_BLACK, (cx + 1, by + 14, 5, 14))
    # Arms
    pygame.draw.rect(s, MALACH_BLACK, (cx - 15, by, 6, 14))
    pygame.draw.rect(s, MALACH_BLACK, (cx + 9, by, 6, 14))
    # Claws
    for ax in [cx - 15, cx + 9]:
        for j in range(3):
            pygame.draw.line(s, MALACH_PURPLE, (ax + j * 2, by + 14), (ax + j * 2, by + 18), 1)
    # Head
    head_y = by - 18
    pygame.draw.ellipse(s, MALACH_BLACK, (cx - 8, head_y, 16, 14))
    # Crown/horns
    for side in [-1, 1]:
        pygame.draw.polygon(s, MALACH_PURPLE, [
            (cx + side * 6, head_y + 2),
            (cx + side * 12, head_y - 10),
            (cx + side * 4, head_y),
        ])
    # Eyes
    pygame.draw.rect(s, MALACH_EYE, (cx - 5, head_y + 5, 3, 3))
    pygame.draw.rect(s, MALACH_EYE, (cx + 2, head_y + 5, 3, 3))
    # Aura effect
    if aura > 0:
        aura_s = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(aura_s, (MALACH_PURPLE[0], MALACH_PURPLE[1], MALACH_PURPLE[2], min(60, aura * 3)),
                           (24, 24), 24)
        s.blit(aura_s, (cx - 24, by - 20))


def gen_malachar():
    print("Generating Malachar the Archdemon...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        wa = [0, 1, 2, 1][i]
        au = [5, 10, 15, 10][i]
        draw_malachar(s, body_dy=dy, wing_angle=wa, aura=au)
        frames.append(s)
    save_sheet(frames, "malachar_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -3, -1, 1][i]
        wa = [2, 4, 3, 1][i]
        au = [10, 20, 15, 5][i]
        draw_malachar(s, body_dy=dy, wing_angle=wa, aura=au)
        frames.append(s)
    save_sheet(frames, "malachar_attack")


# --- Necromancer ---
NECRO_ROBE = (30, 25, 40)
NECRO_TRIM = (80, 60, 100)
NECRO_GREEN = (60, 200, 80)

def draw_necromancer(s, body_dy=0, cast=False):
    cx, cy = 32, 32
    by = cy + 6 + body_dy
    # Robe
    pts = [
        (cx - 4, by - 12),
        (cx + 4, by - 12),
        (cx + 14, by + 24),
        (cx - 14, by + 24),
    ]
    pygame.draw.polygon(s, NECRO_ROBE, pts)
    pygame.draw.polygon(s, NECRO_TRIM, pts, 1)
    # Arms
    pygame.draw.rect(s, NECRO_ROBE, (cx - 14, by, 6, 10))
    pygame.draw.rect(s, NECRO_ROBE, (cx + 8, by, 6, 10))
    # Hands
    pygame.draw.circle(s, (160, 130, 110), (cx - 12, by + 10), 3)
    pygame.draw.circle(s, (160, 130, 110), (cx + 12, by + 10), 3)
    if cast:
        # Green magic glow in hands
        glow_s = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (60, 200, 80, 100), (6, 6), 6)
        s.blit(glow_s, (cx - 18, by + 4))
        s.blit(glow_s, (cx + 6, by + 4))
    # Hood
    head_y = by - 20
    pygame.draw.polygon(s, NECRO_ROBE, [
        (cx, head_y - 4),
        (cx - 8, head_y + 10),
        (cx + 8, head_y + 10),
    ])
    # Face (partially hidden)
    pygame.draw.ellipse(s, (160, 130, 110), (cx - 4, head_y + 2, 8, 8))
    # Eyes
    pygame.draw.rect(s, NECRO_GREEN, (cx - 3, head_y + 5, 2, 2))
    pygame.draw.rect(s, NECRO_GREEN, (cx + 1, head_y + 5, 2, 2))


def gen_necromancer():
    print("Generating necromancer...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        draw_necromancer(s, body_dy=dy)
        frames.append(s)
    save_sheet(frames, "necromancer_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -2, 0, 1][i]
        draw_necromancer(s, body_dy=dy, cast=(i >= 1))
        frames.append(s)
    save_sheet(frames, "necromancer_attack")


# --- Lore Golem ---
GOLEM_PAPER = (200, 190, 170)
GOLEM_INK = (40, 30, 60)
GOLEM_TEXT = (80, 60, 100)

def draw_lore_golem(s, body_dy=0, arm_angle=0):
    cx, cy = 32, 30
    by = cy + body_dy
    # Swirling pages body
    pygame.draw.rect(s, GOLEM_PAPER, (cx - 10, by - 6, 20, 22), border_radius=4)
    pygame.draw.rect(s, GOLEM_INK, (cx - 10, by - 6, 20, 22), 1, border_radius=4)
    # Text lines on body
    for ty in range(by - 2, by + 14, 3):
        pygame.draw.line(s, GOLEM_TEXT, (cx - 7, ty), (cx + 7, ty), 1)
    # Floating pages around
    for px, py in [(-14, -8), (12, -10), (-12, 12), (14, 8)]:
        pygame.draw.rect(s, GOLEM_PAPER, (cx + px, by + py, 5, 6), 1)
    # Legs (paper stacks)
    pygame.draw.rect(s, GOLEM_PAPER, (cx - 7, by + 16, 5, 10))
    pygame.draw.rect(s, GOLEM_PAPER, (cx + 2, by + 16, 5, 10))
    # Arms
    ay = by + int(arm_angle * 0.5)
    pygame.draw.rect(s, GOLEM_PAPER, (cx - 15, ay, 6, 12))
    pygame.draw.rect(s, GOLEM_PAPER, (cx + 9, ay, 6, 12))
    # Head (book-shaped)
    head_y = by - 16
    pygame.draw.rect(s, GOLEM_PAPER, (cx - 7, head_y, 14, 10), border_radius=2)
    pygame.draw.rect(s, GOLEM_INK, (cx - 7, head_y, 14, 10), 1, border_radius=2)
    # Eyes (ink blots)
    pygame.draw.circle(s, GOLEM_INK, (cx - 3, head_y + 5), 2)
    pygame.draw.circle(s, GOLEM_INK, (cx + 3, head_y + 5), 2)


def gen_lore_golem():
    print("Generating lore golem...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, -1, 0, 1][i]
        draw_lore_golem(s, body_dy=dy)
        frames.append(s)
    save_sheet(frames, "lore_golem_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        arm = [0, 2, 4, 1][i]
        dy = [0, -2, 0, 1][i]
        draw_lore_golem(s, body_dy=dy, arm_angle=arm)
        frames.append(s)
    save_sheet(frames, "lore_golem_attack")


# --- Undead (generic zombie soldier) ---
UNDEAD_SKIN = (120, 140, 100)
UNDEAD_DARK = (70, 80, 55)
UNDEAD_ARMOR = (80, 75, 65)

def draw_undead(s, body_dy=0, arm_angle=0):
    cx, cy = 32, 32
    by = cy + 6 + body_dy
    # Legs (shambling)
    pygame.draw.rect(s, UNDEAD_DARK, (cx - 5, by + 14, 4, 14))
    pygame.draw.rect(s, UNDEAD_DARK, (cx + 2, by + 14, 4, 14))
    # Body (tattered armor)
    pygame.draw.rect(s, UNDEAD_ARMOR, (cx - 7, by - 2, 14, 16), border_radius=2)
    pygame.draw.rect(s, (50, 45, 35), (cx - 7, by - 2, 14, 16), 1, border_radius=2)
    # Tears in armor
    pygame.draw.line(s, UNDEAD_SKIN, (cx - 3, by + 2), (cx + 2, by + 8), 1)
    # Arms
    ay = by + 1 + int(arm_angle * 0.4)
    pygame.draw.rect(s, UNDEAD_SKIN, (cx - 11, ay, 4, 12))
    pygame.draw.rect(s, UNDEAD_SKIN, (cx + 7, ay, 4, 12))
    # Head
    head_y = by - 14
    pygame.draw.ellipse(s, UNDEAD_SKIN, (cx - 6, head_y, 12, 12))
    # Sunken eyes
    pygame.draw.rect(s, (40, 20, 20), (cx - 4, head_y + 4, 3, 3))
    pygame.draw.rect(s, (40, 20, 20), (cx + 1, head_y + 4, 3, 3))
    pygame.draw.rect(s, (200, 60, 60), (cx - 3, head_y + 5, 1, 1))
    pygame.draw.rect(s, (200, 60, 60), (cx + 2, head_y + 5, 1, 1))


def gen_undead():
    print("Generating undead...")
    frames = []
    for i in range(4):
        s = make_surf()
        dy = [0, 1, 0, -1][i]
        draw_undead(s, body_dy=dy)
        frames.append(s)
    save_sheet(frames, "undead_idle")
    frames = []
    for i in range(4):
        s = make_surf()
        arm = [0, 2, 5, 1][i]
        dy = [0, -1, 0, 1][i]
        draw_undead(s, body_dy=dy, arm_angle=arm)
        frames.append(s)
    save_sheet(frames, "undead_attack")


# ======================================================================
#  STORY EXPANSION — NEW BACKGROUNDS
# ======================================================================

def gen_bg_ruins():
    import random
    print("Generating ruins background...")
    s = pygame.Surface((BG_W, BG_H))
    # Dark grey sky
    for y in range(BG_H):
        t = y / BG_H
        r = int(30 + 20 * t)
        g = int(30 + 15 * t)
        b = int(35 + 18 * t)
        pygame.draw.line(s, (r, g, b), (0, y), (BG_W, y))
    # Stone floor
    random.seed(100)
    for y in range(BG_H - 120, BG_H):
        for x in range(0, BG_W, 6):
            c = 35 + random.randint(0, 15)
            pygame.draw.rect(s, (c + 3, c + 2, c + 5), (x, y, 6, 6))
    # Broken columns
    for px in [150, 400, 700, 1000]:
        h = random.randint(100, 250)
        pygame.draw.rect(s, (55, 50, 60), (px - 12, BG_H - 120 - h, 24, h))
        pygame.draw.rect(s, (40, 35, 45), (px - 12, BG_H - 120 - h, 24, h), 1)
        # Broken top
        for bx in range(-8, 9, 4):
            by = random.randint(-10, 5)
            pygame.draw.rect(s, (55, 50, 60), (px + bx, BG_H - 120 - h + by, 4, 8))
    # Archway
    pygame.draw.arc(s, (50, 45, 55), (BG_W // 2 - 80, BG_H - 320, 160, 200), 0, 3.14, 4)
    # Gate text
    for tx in range(BG_W // 2 - 50, BG_W // 2 + 50, 8):
        pygame.draw.rect(s, (70, 65, 75), (tx, BG_H - 290, 5, 3))
    # Fog patches
    for _ in range(8):
        fx = random.randint(0, BG_W)
        fy = random.randint(BG_H - 200, BG_H - 80)
        fog = pygame.Surface((120, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(fog, (60, 60, 70, 30), (0, 0, 120, 40))
        s.blit(fog, (fx, fy))
    save_bg(s, "ruins")


def gen_bg_temple():
    import random
    print("Generating temple background...")
    s = pygame.Surface((BG_W, BG_H))
    s.fill((25, 20, 35))
    # Stone walls
    random.seed(111)
    for y in range(0, BG_H - 100, 20):
        offset = 15 if (y // 20) % 2 else 0
        for x in range(-15 + offset, BG_W + 15, 40):
            c = 25 + random.randint(0, 10)
            pygame.draw.rect(s, (c + 3, c, c + 8), (x, y, 38, 18))
            pygame.draw.rect(s, (18, 15, 22), (x, y, 38, 18), 1)
    # Stone floor
    for y in range(BG_H - 100, BG_H):
        for x in range(0, BG_W, 8):
            c = 30 + random.randint(0, 12)
            pygame.draw.rect(s, (c + 5, c + 3, c + 8), (x, y, 8, 8))
    # Pews (rows of stone seats)
    for row in range(3):
        py = BG_H - 160 + row * 30
        for px in range(200, BG_W - 200, 60):
            pygame.draw.rect(s, (45, 35, 50), (px, py, 40, 12))
            pygame.draw.rect(s, (55, 45, 60), (px, py, 40, 4))
    # Altar at front
    pygame.draw.rect(s, (50, 40, 60), (BG_W // 2 - 40, BG_H - 200, 80, 40))
    pygame.draw.rect(s, (65, 55, 75), (BG_W // 2 - 40, BG_H - 200, 80, 8))
    # Mirror on altar (cracked)
    mx, my = BG_W // 2, BG_H - 240
    pygame.draw.ellipse(s, (120, 130, 150), (mx - 20, my, 40, 50))
    pygame.draw.ellipse(s, (80, 90, 110), (mx - 20, my, 40, 50), 2)
    # Crack lines
    pygame.draw.line(s, (60, 60, 80), (mx, my + 10), (mx + 12, my + 35), 1)
    pygame.draw.line(s, (60, 60, 80), (mx, my + 10), (mx - 8, my + 30), 1)
    save_bg(s, "temple")


def gen_bg_barracks():
    import random
    print("Generating barracks background...")
    s = pygame.Surface((BG_W, BG_H))
    s.fill((28, 22, 30))
    random.seed(122)
    # Stone walls
    for y in range(0, BG_H - 100, 20):
        for x in range(0, BG_W, 40):
            c = 28 + random.randint(0, 10)
            pygame.draw.rect(s, (c + 5, c + 2, c + 5), (x, y, 38, 18))
            pygame.draw.rect(s, (18, 15, 20), (x, y, 38, 18), 1)
    # Wood floor
    for y in range(BG_H - 100, BG_H):
        for x in range(0, BG_W, 30):
            c = 40 + random.randint(0, 10) + (x // 30 % 2) * 5
            pygame.draw.rect(s, (c + 8, c, c - 5), (x, y, 30, 1))
    # Bunk beds
    for bx in [100, 350, 600, 850]:
        # Frame
        pygame.draw.rect(s, (50, 35, 20), (bx, BG_H - 220, 80, 120))
        pygame.draw.rect(s, (60, 42, 25), (bx, BG_H - 220, 80, 120), 2)
        # Mattress (top)
        pygame.draw.rect(s, (70, 55, 40), (bx + 5, BG_H - 180, 70, 12))
        # Mattress (bottom)
        pygame.draw.rect(s, (70, 55, 40), (bx + 5, BG_H - 120, 70, 12))
    # Card table
    pygame.draw.rect(s, (60, 45, 25), (BG_W // 2 - 50, BG_H - 160, 100, 60))
    pygame.draw.rect(s, (75, 55, 30), (BG_W // 2 - 50, BG_H - 160, 100, 8))
    # Cards on table
    for cx_off in [-20, -5, 10, 25]:
        pygame.draw.rect(s, (220, 210, 190), (BG_W // 2 + cx_off, BG_H - 148, 10, 14), border_radius=1)
    save_bg(s, "barracks")


def gen_bg_mansion():
    import random
    print("Generating mansion background...")
    s = pygame.Surface((BG_W, BG_H))
    s.fill((22, 18, 28))
    random.seed(133)
    # Ornate wallpaper
    for y in range(0, BG_H - 100, 4):
        c = 22 + int(math.sin(y * 0.1) * 5)
        pygame.draw.line(s, (c + 5, c, c + 10), (0, y), (BG_W, y))
    # Marble floor
    for y in range(BG_H - 100, BG_H):
        for x in range(0, BG_W, 8):
            c = 35 + random.randint(0, 15)
            pygame.draw.rect(s, (c + 8, c + 6, c + 10), (x, y, 8, 8))
    # Portrait frames on wall
    for px in [200, 450, 750, 1000]:
        pygame.draw.rect(s, (80, 60, 30), (px - 25, 80, 50, 70), 3)
        pygame.draw.rect(s, (40, 30, 45), (px - 22, 83, 44, 64))
        # Scratched face
        pygame.draw.line(s, (60, 50, 40), (px - 10, 95), (px + 10, 120), 2)
        pygame.draw.line(s, (60, 50, 40), (px + 10, 95), (px - 10, 120), 2)
    # Vines
    for vx in [50, BG_W - 50]:
        for vy in range(0, BG_H - 100, 8):
            pygame.draw.rect(s, (20, 50 + random.randint(0, 20), 15), (vx + random.randint(-3, 3), vy, 3, 8))
    # Cold locked door
    dx = BG_W // 2
    pygame.draw.rect(s, (40, 50, 70), (dx - 30, BG_H - 250, 60, 150))
    pygame.draw.rect(s, (60, 70, 90), (dx - 30, BG_H - 250, 60, 150), 2)
    # Ice around keyhole
    pygame.draw.circle(s, (150, 180, 220), (dx, BG_H - 170), 8)
    pygame.draw.circle(s, (180, 210, 240), (dx, BG_H - 170), 4)
    save_bg(s, "mansion")


def gen_bg_mountain():
    import random
    print("Generating mountain background...")
    s = pygame.Surface((BG_W, BG_H))
    # Sky gradient (cold blue)
    for y in range(BG_H):
        t = y / BG_H
        r = int(40 + 30 * t)
        g = int(50 + 40 * t)
        b = int(80 + 40 * (1 - t))
        pygame.draw.line(s, (r, g, b), (0, y), (BG_W, y))
    random.seed(144)
    # Mountain peaks in background
    for mx, mh in [(200, 300), (500, 350), (900, 280), (1100, 320)]:
        pts = [(mx - 120, BG_H - 100), (mx, BG_H - 100 - mh), (mx + 120, BG_H - 100)]
        pygame.draw.polygon(s, (50, 55, 65), pts)
        # Snow caps
        snow_pts = [(mx - 20, BG_H - 100 - mh + 30), (mx, BG_H - 100 - mh), (mx + 20, BG_H - 100 - mh + 30)]
        pygame.draw.polygon(s, (200, 210, 220), snow_pts)
    # Rocky ground
    for y in range(BG_H - 100, BG_H):
        for x in range(0, BG_W, 6):
            c = 40 + random.randint(0, 15)
            pygame.draw.rect(s, (c + 5, c + 3, c), (x, y, 6, 6))
    # Cave mouth
    cx = BG_W // 2
    pygame.draw.ellipse(s, (15, 12, 20), (cx - 60, BG_H - 230, 120, 140))
    pygame.draw.ellipse(s, (25, 22, 30), (cx - 60, BG_H - 230, 120, 140), 2)
    # Old woman's fire spot (faint glow)
    glow = pygame.Surface((60, 40), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (180, 100, 30, 40), (0, 0, 60, 40))
    s.blit(glow, (cx - 130, BG_H - 140))
    save_bg(s, "mountain")


def gen_bg_cave():
    import random
    print("Generating cave background...")
    s = pygame.Surface((BG_W, BG_H))
    s.fill((12, 10, 18))
    random.seed(155)
    # Rocky walls
    for _ in range(200):
        x = random.randint(0, BG_W)
        y = random.randint(0, BG_H)
        c = 12 + random.randint(0, 10)
        pygame.draw.circle(s, (c + 3, c, c + 5), (x, y), random.randint(10, 40))
    # Crystal formations (blue glow)
    crystal_positions = [(200, 300), (400, 150), (700, 250), (900, 180), (1100, 350)]
    for cx, cy in crystal_positions:
        # Crystal shard
        pts = [(cx, cy - 30), (cx - 8, cy + 10), (cx + 8, cy + 10)]
        pygame.draw.polygon(s, (60, 100, 180), pts)
        pygame.draw.polygon(s, (100, 150, 220), pts, 1)
        # Glow
        glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (60, 100, 180, 30), (20, 20), 20)
        s.blit(glow, (cx - 20, cy - 20))
    # Stone floor
    for y in range(BG_H - 80, BG_H):
        for x in range(0, BG_W, 6):
            c = 18 + random.randint(0, 8)
            pygame.draw.rect(s, (c + 3, c, c + 4), (x, y, 6, 6))
    save_bg(s, "cave")


def gen_bg_valley():
    import random
    print("Generating valley background...")
    s = pygame.Surface((BG_W, BG_H))
    # Warm golden-green gradient
    for y in range(BG_H):
        t = y / BG_H
        r = int(60 + 40 * (1 - t))
        g = int(80 + 50 * (1 - t))
        b = int(30 + 20 * (1 - t))
        pygame.draw.line(s, (r, g, b), (0, y), (BG_W, y))
    random.seed(166)
    # Flowers
    for _ in range(50):
        fx = random.randint(0, BG_W)
        fy = random.randint(BG_H - 150, BG_H - 20)
        c = random.choice([(220, 80, 120), (80, 140, 220), (220, 200, 60), (200, 120, 220)])
        pygame.draw.circle(s, c, (fx, fy), random.randint(2, 4))
    # Stone ring wall
    for x in range(BG_W // 4, BG_W * 3 // 4, 8):
        wh = 40 + random.randint(0, 10)
        c = 60 + random.randint(0, 15)
        pygame.draw.rect(s, (c, c - 5, c - 10), (x, BG_H - 100 - wh, 6, wh))
    # Small houses inside wall
    for hx in [BG_W // 3, BG_W // 2, BG_W * 2 // 3]:
        pygame.draw.rect(s, (80, 60, 40), (hx - 15, BG_H - 160, 30, 30))
        pygame.draw.polygon(s, (120, 80, 40), [(hx - 18, BG_H - 160), (hx, BG_H - 180), (hx + 18, BG_H - 160)])
    # Shambling undead silhouettes outside wall
    for ux in range(80, BG_W // 4 - 20, 30):
        uy = BG_H - 110
        pygame.draw.ellipse(s, (50, 60, 40), (ux, uy - 10, 8, 10))
        pygame.draw.rect(s, (50, 60, 40), (ux + 1, uy, 6, 12))
    for ux in range(BG_W * 3 // 4 + 20, BG_W - 40, 30):
        uy = BG_H - 110
        pygame.draw.ellipse(s, (50, 60, 40), (ux, uy - 10, 8, 10))
        pygame.draw.rect(s, (50, 60, 40), (ux + 1, uy, 6, 12))
    save_bg(s, "valley")


def gen_bg_tower():
    import random
    print("Generating demon tower background...")
    s = pygame.Surface((BG_W, BG_H))
    # Very dark purple sky
    for y in range(BG_H):
        t = y / BG_H
        r = int(15 + 10 * t)
        g = int(5 + 5 * t)
        b = int(25 + 15 * t)
        pygame.draw.line(s, (r, g, b), (0, y), (BG_W, y))
    random.seed(177)
    # Tower interior walls (dark iron)
    for y in range(0, BG_H - 80, 20):
        for x in range(0, BG_W, 35):
            c = 18 + random.randint(0, 8)
            pygame.draw.rect(s, (c, c - 2, c + 5), (x, y, 33, 18))
            pygame.draw.rect(s, (10, 8, 15), (x, y, 33, 18), 1)
    # Iron floor
    for y in range(BG_H - 80, BG_H):
        for x in range(0, BG_W, 8):
            c = 22 + random.randint(0, 10)
            pygame.draw.rect(s, (c + 3, c, c + 6), (x, y, 8, 8))
    # Purple flame torches
    for tx in [100, 350, 650, BG_W - 100]:
        pygame.draw.rect(s, (30, 20, 40), (tx - 3, 100, 6, 30))
        for fi in range(4):
            fy = 95 - fi * 5
            fw = 10 - fi * 2
            fc = (80 + fi * 15, 20 + fi * 5, 120 - fi * 15)
            pygame.draw.ellipse(s, fc, (tx - fw // 2, fy, fw, 8))
    # Throne silhouette at back
    pygame.draw.rect(s, (10, 5, 15), (BG_W // 2 - 40, BG_H - 250, 80, 170))
    pygame.draw.polygon(s, (15, 8, 20), [
        (BG_W // 2 - 50, BG_H - 250),
        (BG_W // 2, BG_H - 320),
        (BG_W // 2 + 50, BG_H - 250),
    ])
    save_bg(s, "tower")


def gen_bg_cellar():
    import random
    print("Generating cellar background...")
    s = pygame.Surface((BG_W, BG_H))
    s.fill((15, 12, 20))
    random.seed(188)
    # Crude stone walls
    for y in range(0, BG_H - 80, 18):
        for x in range(0, BG_W, 32):
            c = 18 + random.randint(0, 10)
            pygame.draw.rect(s, (c + 3, c, c + 5), (x, y, 30, 16))
            pygame.draw.rect(s, (12, 10, 15), (x, y, 30, 16), 1)
    # Stone steps (left side)
    for step in range(5):
        sy = 50 + step * 40
        sw = 60 + step * 10
        pygame.draw.rect(s, (35, 30, 40), (10, sy, sw, 15))
    # Ritual symbols on floor
    cx, cy = BG_W // 2, BG_H - 120
    pygame.draw.circle(s, (80, 20, 20), (cx, cy), 60, 2)
    pygame.draw.circle(s, (60, 15, 15), (cx, cy), 40, 1)
    # Pentagram-ish lines
    for angle in range(0, 360, 72):
        rad = math.radians(angle)
        rad2 = math.radians(angle + 144)
        x1 = cx + int(55 * math.cos(rad))
        y1 = cy + int(55 * math.sin(rad))
        x2 = cx + int(55 * math.cos(rad2))
        y2 = cy + int(55 * math.sin(rad2))
        pygame.draw.line(s, (80, 20, 20), (x1, y1), (x2, y2), 1)
    # Blue light (from below)
    glow = pygame.Surface((200, 100), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (40, 60, 180, 30), (0, 0, 200, 100))
    s.blit(glow, (BG_W // 2 - 100, BG_H - 160))
    # Caged animals (small rectangles)
    for cage_x in [100, 250, BG_W - 250, BG_W - 100]:
        pygame.draw.rect(s, (50, 45, 55), (cage_x, BG_H - 160, 40, 30), 1)
    save_bg(s, "cellar")


# ======================================================================
#  MAIN
# ======================================================================
if __name__ == "__main__":
    gen_player()
    gen_dan()
    gen_narrator()
    gen_skeleton()
    gen_slime()
    gen_wraith()
    gen_golem()
    gen_spider()
    gen_dark_knight()
    gen_imp()
    gen_oracle()
    gen_dragon()
    gen_mirror_wraith()
    gen_revenant()
    gen_malachar()
    gen_necromancer()
    gen_lore_golem()
    gen_undead()
    gen_bg_forest()
    gen_bg_field()
    gen_bg_combat()
    gen_bg_shop()
    gen_bg_menu()
    gen_bg_gameover()
    gen_bg_loot()
    gen_bg_arcade()
    gen_bg_ruins()
    gen_bg_temple()
    gen_bg_barracks()
    gen_bg_mansion()
    gen_bg_mountain()
    gen_bg_cave()
    gen_bg_valley()
    gen_bg_tower()
    gen_bg_cellar()
    print("\nAll assets generated!")
    pygame.quit()
