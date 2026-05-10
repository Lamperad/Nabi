#!/usr/bin/env python3
"""Generate Nabi app icon (narrator hooded figure on dark background)."""
import pygame
import os
import math

pygame.init()

SIZES = [256, 128, 64, 48, 32, 16]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)

# Colours
CLOAK_PURPLE = (70, 40, 100)
CLOAK_DARK = (35, 20, 55)
HOOD_GREY = (90, 80, 100)
HOOD_DARK = (30, 25, 40)
EYE_GLOW = (240, 220, 140)
BG_DARK = (18, 18, 30)
GOLD = (255, 215, 80)
GOLD_DIM = (180, 150, 50)
STAR = (200, 200, 220)


def draw_icon(size):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    # Dark circular background
    pygame.draw.circle(s, BG_DARK, (cx, cy), size // 2)
    pygame.draw.circle(s, (40, 40, 60), (cx, cy), size // 2, max(1, size // 64))

    # Particle sparkles
    import random
    random.seed(42)
    for _ in range(int(size * 0.15)):
        px = random.randint(4, size - 4)
        py = random.randint(4, size - 4)
        dist = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
        if dist < size // 2 - 4:
            r = max(1, size // 128)
            alpha = random.randint(40, 120)
            dot = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*STAR, alpha), (r, r), r)
            s.blit(dot, (px - r, py - r))

    # Scale factor relative to 256
    sc = size / 256

    # Cloak body (triangular silhouette) — centered, taking up good portion
    body_top = int(cy - 30 * sc)
    body_bot = int(cy + 80 * sc)
    body_w = int(60 * sc)
    pts = [
        (cx, body_top),
        (cx - body_w, body_bot),
        (cx + body_w, body_bot),
    ]
    pygame.draw.polygon(s, CLOAK_PURPLE, pts)
    pygame.draw.polygon(s, CLOAK_DARK, pts, max(1, int(2 * sc)))

    # Inner robe fold
    inner_w = int(22 * sc)
    inner_top = int(cy - 10 * sc)
    inner_bot = int(cy + 70 * sc)
    inner_pts = [
        (cx, inner_top),
        (cx - inner_w, inner_bot),
        (cx + inner_w, inner_bot),
    ]
    pygame.draw.polygon(s, CLOAK_DARK, inner_pts)

    # Hood
    hood_w = int(40 * sc)
    hood_h = int(34 * sc)
    hood_y = int(cy - 60 * sc)
    pygame.draw.ellipse(s, HOOD_GREY, (cx - hood_w // 2, hood_y, hood_w, hood_h))

    # Hood shadow (face area)
    face_w = int(30 * sc)
    face_h = int(22 * sc)
    face_y = int(cy - 48 * sc)
    pygame.draw.ellipse(s, HOOD_DARK, (cx - face_w // 2, face_y, face_w, face_h))

    # Glowing eyes
    eye_size = max(2, int(5 * sc))
    eye_y = int(cy - 40 * sc)
    eye_gap = int(8 * sc)

    # Eye glow halo
    glow_r = int(10 * sc)
    glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (*EYE_GLOW, 40), (glow_r, glow_r), glow_r)
    s.blit(glow_surf, (cx - eye_gap - glow_r, eye_y - glow_r + eye_size // 2))
    s.blit(glow_surf, (cx + eye_gap - glow_r, eye_y - glow_r + eye_size // 2))

    # Eye dots
    pygame.draw.rect(s, EYE_GLOW, (cx - eye_gap - eye_size // 2, eye_y, eye_size, eye_size))
    pygame.draw.rect(s, EYE_GLOW, (cx + eye_gap - eye_size // 2, eye_y, eye_size, eye_size))

    # Wispy bottom (ragged edge)
    for i in range(-int(55 * sc), int(56 * sc), max(2, int(6 * sc))):
        rag_y = body_bot + abs(i) % max(1, int(6 * sc))
        lw = max(1, int(1.5 * sc))
        pygame.draw.line(s, CLOAK_DARK, (cx + i, body_bot - int(4 * sc)), (cx + i, rag_y), lw)

    # "N" letter at bottom (gold, subtle)
    if size >= 48:
        font_size = max(12, int(22 * sc))
        font = pygame.font.SysFont("consolas", font_size, bold=True)
        n_surf = font.render("N", True, GOLD_DIM)
        n_rect = n_surf.get_rect(center=(cx, int(cy + 95 * sc)))
        if n_rect.bottom < size - 2:
            s.blit(n_surf, n_rect)

    return s


def main():
    # Generate the 256px master icon as PNG
    icon_256 = draw_icon(256)
    png_path = os.path.join(OUT, "icon.png")
    pygame.image.save(icon_256, png_path)
    print(f"Saved {png_path}")

    # Generate all sizes for ICO
    surfaces = [draw_icon(sz) for sz in SIZES]

    # Save individual PNGs for each size
    for surf, sz in zip(surfaces, SIZES):
        p = os.path.join(OUT, f"icon_{sz}.png")
        pygame.image.save(surf, p)

    # We'll use Pillow to create .ico if available, otherwise just keep PNGs
    try:
        from PIL import Image
        images = []
        for sz in SIZES:
            p = os.path.join(OUT, f"icon_{sz}.png")
            img = Image.open(p).convert("RGBA")
            images.append(img)

        ico_path = os.path.join(OUT, "icon.ico")
        images[0].save(ico_path, format="ICO", sizes=[(sz, sz) for sz in SIZES],
                       append_images=images[1:])
        print(f"Saved {ico_path}")

        # Clean up individual size PNGs
        for sz in SIZES:
            os.remove(os.path.join(OUT, f"icon_{sz}.png"))
    except ImportError:
        print("Pillow not installed — saved PNGs only. Install with: pip install Pillow")
        print("Then run again to generate .ico file.")

    pygame.quit()


if __name__ == "__main__":
    main()
