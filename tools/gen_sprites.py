#!/usr/bin/env python3
"""Gera os sprites do mod Bullet Strike (bases, torres, icones e projeteis).

Tudo e desenhado proceduralmente com Pillow, entao o mod nao depende de
nenhuma arte copiada do jogo. Rode a partir da raiz do repositorio:

    python3 tools/gen_sprites.py

Os PNGs sao gravados em BulletStrike/ (dentro da pasta de cada peca).
Escala: 64 px por metro (tile) do Cosmoteer.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

PX = 64  # pixels por tile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "BulletStrike")

# Cores de destaque por tipo de municao.
ACCENTS = {
    "ammo": (232, 178, 48),      # latao / municao padrao
    "plasma": (64, 214, 255),    # ciano
    "nuclear": (120, 255, 90),   # verde radioativo
    "flak": (255, 120, 60),      # laranja
}

HULL_DARK = (46, 50, 58)
HULL_MID = (78, 84, 96)
HULL_LIGHT = (128, 136, 150)
STEEL = (150, 156, 166)
GUN_DARK = (34, 36, 42)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def _rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def vertical_gradient(w, h, top, bottom):
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=_rgba(_lerp(top, bottom, y / max(1, h - 1))))
    return img


def bevel_rect(d, box, base, width=3, radius=6):
    """Retangulo com borda clara em cima/esquerda e escura embaixo/direita."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=radius, fill=_rgba(base))
    for i in range(width):
        d.rounded_rectangle((x0 + i, y0 + i, x1 - i, y1 - i), radius=max(1, radius - i),
                            outline=_rgba(_shade(base, 1.35 - i * 0.1)))
    d.line([(x0 + radius, y1 - 1), (x1 - radius, y1 - 1)], fill=_rgba(_shade(base, 0.55)), width=2)
    d.line([(x1 - 1, y0 + radius), (x1 - 1, y1 - radius)], fill=_rgba(_shade(base, 0.55)), width=2)


def rivets(d, box, step, color):
    x0, y0, x1, y1 = box
    for x in range(int(x0) + step // 2, int(x1), step):
        for y in (y0 + 6, y1 - 7):
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=_rgba(_shade(color, 1.4)))
            d.point((x + 1, y + 1), fill=_rgba(_shade(color, 0.5)))


def hazard_stripes(img, box, accent):
    x0, y0, x1, y1 = [int(v) for v in box]
    stripe = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stripe)
    w, h = stripe.size
    for k in range(-h, w + h, 14):
        sd.polygon([(k, 0), (k + 7, 0), (k + 7 - h, h), (k - h, h)], fill=_rgba(accent, 230))
    for k in range(-h + 7, w + h, 14):
        sd.polygon([(k, 0), (k + 7, 0), (k + 7 - h, h), (k - h, h)], fill=(20, 20, 22, 230))
    img.alpha_composite(stripe, (x0, y0))


def noise_overlay(img, amount=10, seed=1):
    rnd = random.Random(seed)
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            n = rnd.randint(-amount, amount)
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)), a)


def draw_base(w_tiles, h_tiles, accent, ammo_strip_rows=1, seed=0):
    """Plataforma de montagem de conves.

    As `ammo_strip_rows` linhas de baixo sao a faixa de carregamento de
    municao (onde a tripulacao entrega a municao), igual ao Deck Cannon.
    """
    w, h = w_tiles * PX, h_tiles * PX
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bevel_rect(d, (1, 1, w - 2, h - 2), HULL_MID, width=4, radius=10)
    plate = vertical_gradient(w - 16, h - 16, _shade(HULL_MID, 1.1), _shade(HULL_DARK, 1.1))
    mask = Image.new("L", plate.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, plate.size[0] - 1, plate.size[1] - 1), radius=8, fill=255)
    img.paste(plate, (8, 8), mask)
    # linhas de painel
    for tx in range(1, w_tiles):
        d.line([(tx * PX, 10), (tx * PX, h - 10)], fill=_rgba(_shade(HULL_DARK, 0.7)), width=2)
    for ty in range(1, h_tiles):
        d.line([(10, ty * PX), (w - 10, ty * PX)], fill=_rgba(_shade(HULL_DARK, 0.7)), width=2)
    rivets(d, (8, 8, w - 8, h - 8), 22, HULL_MID)
    # faixa de municao
    if ammo_strip_rows > 0:
        sy = h - ammo_strip_rows * PX
        d.rectangle((10, sy + 6, w - 11, h - 11), fill=_rgba(HULL_DARK))
        hazard_stripes(img, (12, sy + 8, w - 12, sy + 18), accent)
        # caixas de municao
        n = max(2, w_tiles * 2)
        bw = (w - 30) / n
        for i in range(n):
            bx = 15 + i * bw
            d.rectangle((bx + 2, sy + 24, bx + bw - 3, h - 16), fill=_rgba(_shade(accent, 0.45)),
                        outline=_rgba(_shade(accent, 0.9)))
            d.line([(bx + 4, sy + 30), (bx + bw - 5, sy + 30)], fill=_rgba(_shade(accent, 1.1)), width=2)
    # anel da torre (centro da area acima da faixa)
    top_h = h - ammo_strip_rows * PX
    cx, cy = w / 2, top_h / 2
    r = min(w, top_h) * 0.44
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_rgba(_shade(HULL_DARK, 0.8)),
              outline=_rgba(_shade(accent, 0.8)), width=3)
    d.ellipse((cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8), outline=_rgba(HULL_LIGHT), width=2)
    for k in range(24):
        a = k / 24 * math.tau
        x = cx + math.cos(a) * (r - 4)
        y = cy + math.sin(a) * (r - 4)
        d.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=_rgba(STEEL))
    noise_overlay(img, 6, seed)
    return img


def _barrel(d, cx, y_top, y_bottom, width, accent, muzzle=True, cooling=0):
    half = width / 2
    d.rectangle((cx - half, y_top, cx + half, y_bottom), fill=_rgba(GUN_DARK))
    d.rectangle((cx - half + 1, y_top, cx - half + max(2, width * 0.3), y_bottom), fill=_rgba(_shade(STEEL, 0.85)))
    d.line([(cx + half - 1, y_top), (cx + half - 1, y_bottom)], fill=_rgba((15, 15, 18)), width=1)
    for i in range(cooling):
        yy = y_top + 10 + i * 7
        if yy > y_bottom - 6:
            break
        d.rectangle((cx - half - 2, yy, cx + half + 2, yy + 3), fill=_rgba(_shade(STEEL, 0.7)))
    if muzzle:
        d.rectangle((cx - half - 2, y_top, cx + half + 2, y_top + max(4, width * 0.6)), fill=_rgba(_shade(accent, 0.75)),
                    outline=_rgba((20, 20, 22)))


def draw_turret(style, size_px, accent, seed=0):
    """Desenha a cabeca da torre apontando para CIMA (direcao de disparo)."""
    w, h = size_px
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w / 2, h * 0.62  # pivo da rotacao fica no centro da imagem final (ver crop abaixo)
    body_r = min(w, h) * 0.26

    if style == "mg_light":
        _barrel(d, cx - 6, h * 0.06, cy, 6, accent, cooling=4)
        _barrel(d, cx + 6, h * 0.06, cy, 6, accent, cooling=4)
        bevel_rect(d, (cx - body_r, cy - body_r * 0.9, cx + body_r, cy + body_r * 1.1), HULL_LIGHT, 2, 6)
        d.rectangle((cx - body_r * 0.6, cy + body_r * 0.2, cx + body_r * 0.6, cy + body_r * 0.8), fill=_rgba(_shade(accent, 0.6)))
    elif style == "autocannon":
        _barrel(d, cx, h * 0.04, cy, 12, accent, cooling=3)
        d.rectangle((cx - 9, h * 0.30, cx + 9, h * 0.40), fill=_rgba(_shade(STEEL, 0.9)))  # freio de boca/recuo
        bevel_rect(d, (cx - body_r * 1.1, cy - body_r, cx + body_r * 1.1, cy + body_r * 1.15), HULL_LIGHT, 3, 8)
        d.rectangle((cx + body_r * 0.4, cy - body_r * 0.4, cx + body_r * 1.0, cy + body_r * 0.8), fill=_rgba(_shade(accent, 0.55)))
    elif style == "minigun":
        n = 6
        for i in range(n):
            ox = (i - (n - 1) / 2) * 5.5
            _barrel(d, cx + ox, h * 0.05 + abs(ox) * 0.4, cy, 5, accent, muzzle=False)
        d.rectangle((cx - 18, h * 0.04, cx + 18, h * 0.08), fill=_rgba(_shade(accent, 0.7)))
        d.rectangle((cx - 18, h * 0.26, cx + 18, h * 0.30), fill=_rgba(STEEL))
        d.ellipse((cx - body_r * 1.15, cy - body_r * 1.15, cx + body_r * 1.15, cy + body_r * 1.15), fill=_rgba(HULL_LIGHT),
                  outline=_rgba(_shade(HULL_LIGHT, 0.5)), width=3)
        d.ellipse((cx - body_r * 0.7, cy - body_r * 0.7, cx + body_r * 0.7, cy + body_r * 0.7), fill=_rgba(_shade(accent, 0.6)),
                  outline=_rgba(_shade(accent, 1.2)), width=2)
    elif style == "flak":
        for ox in (-14, 14):
            _barrel(d, cx + ox, h * 0.10, cy, 9, accent, cooling=2)
        bevel_rect(d, (cx - body_r * 1.25, cy - body_r, cx + body_r * 1.25, cy + body_r * 1.2), HULL_LIGHT, 3, 10)
        for ox in (-12, 12):
            d.ellipse((cx + ox - 6, cy - 6, cx + ox + 6, cy + 6), fill=_rgba(_shade(accent, 0.7)))
    elif style == "plasma_gatling":
        n = 4
        for i in range(n):
            ox = (i - (n - 1) / 2) * 8
            _barrel(d, cx + ox, h * 0.07, cy, 7, accent, muzzle=False)
        for k in range(4):
            yy = h * 0.12 + k * h * 0.08
            d.rectangle((cx - 19, yy, cx + 19, yy + 4), fill=_rgba(accent, 230))
        bevel_rect(d, (cx - body_r * 1.2, cy - body_r, cx + body_r * 1.2, cy + body_r * 1.2), HULL_LIGHT, 3, 10)
        d.ellipse((cx - 12, cy - 4, cx + 12, cy + 20), fill=_rgba(accent), outline=_rgba((255, 255, 255)), width=2)
    elif style == "heavy_cannon":
        for ox in (-13, 13):
            _barrel(d, cx + ox, h * 0.03, cy, 14, accent, cooling=4)
            d.rectangle((cx + ox - 10, h * 0.03, cx + ox + 10, h * 0.09), fill=_rgba(_shade(STEEL, 0.8)), outline=_rgba(GUN_DARK))
        bevel_rect(d, (cx - body_r * 1.3, cy - body_r * 1.05, cx + body_r * 1.3, cy + body_r * 1.25), HULL_LIGHT, 4, 12)
        d.rectangle((cx - body_r, cy + body_r * 0.35, cx + body_r, cy + body_r * 0.85), fill=_rgba(_shade(accent, 0.55)))
        hazard_stripes(img, (cx - body_r, cy + body_r * 0.9, cx + body_r, cy + body_r * 1.05), accent)
    elif style == "plasma_cannon":
        _barrel(d, cx, h * 0.03, cy, 20, accent, muzzle=False)
        for k in range(6):
            yy = h * 0.08 + k * h * 0.065
            d.rectangle((cx - 16, yy, cx + 16, yy + 5), fill=_rgba(accent, 235), outline=_rgba(_shade(accent, 0.5)))
        d.polygon([(cx - 14, h * 0.03), (cx + 14, h * 0.03), (cx + 9, h * 0.0), (cx - 9, h * 0.0)], fill=_rgba(_shade(accent, 0.7)))
        bevel_rect(d, (cx - body_r * 1.3, cy - body_r * 1.0, cx + body_r * 1.3, cy + body_r * 1.3), HULL_LIGHT, 4, 14)
        d.ellipse((cx - 18, cy - 8, cx + 18, cy + 28), fill=_rgba(accent), outline=_rgba((240, 255, 255)), width=3)
    elif style == "nuke_howitzer":
        _barrel(d, cx, h * 0.02, cy, 26, accent, cooling=6)
        d.rectangle((cx - 20, h * 0.02, cx + 20, h * 0.08), fill=_rgba(_shade(STEEL, 0.75)), outline=_rgba(GUN_DARK))
        bevel_rect(d, (cx - body_r * 1.35, cy - body_r * 1.05, cx + body_r * 1.35, cy + body_r * 1.35), HULL_LIGHT, 4, 14)
        # simbolo de radiacao
        rr = body_r * 0.55
        ry = cy + body_r * 0.35
        d.ellipse((cx - rr, ry - rr, cx + rr, ry + rr), fill=_rgba((26, 26, 26)))
        for k in range(3):
            a0 = -90 + k * 120 - 30
            d.pieslice((cx - rr * 0.9, ry - rr * 0.9, cx + rr * 0.9, ry + rr * 0.9), a0, a0 + 60, fill=_rgba(accent))
        d.ellipse((cx - rr * 0.22, ry - rr * 0.22, cx + rr * 0.22, ry + rr * 0.22), fill=_rgba(accent))
    else:
        raise ValueError(style)

    img = img.filter(ImageFilter.SMOOTH)
    noise_overlay(img, 5, seed)
    # Recentraliza de forma que o pivo (cx, cy) fique no centro da imagem.
    shift = int(h / 2 - cy)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(img, (0, shift))
    return out


def draw_bullet(length, width, accent, glow=True):
    w, h = width * 4, length + width * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w / 2
    if glow:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse((cx - width * 1.6, width * 0.3, cx + width * 1.6, h - width * 0.3), fill=_rgba(accent, 120))
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(width * 0.6)))
    d.ellipse((cx - width / 2, width, cx + width / 2, h - width), fill=_rgba(_lerp(accent, (255, 255, 255), 0.35)))
    d.ellipse((cx - width / 4, width * 1.2, cx + width / 4, h * 0.45), fill=(255, 255, 255, 255))
    return img


def draw_resource_icon(kind, accent, size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size
    if kind == "plasma":
        g = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse((s * 0.2, s * 0.1, s * 0.8, s * 0.9), fill=_rgba(accent, 150))
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(s * 0.08)))
        d.rounded_rectangle((s * 0.32, s * 0.12, s * 0.68, s * 0.88), radius=s * 0.1, fill=_rgba(_shade(accent, 0.6)),
                            outline=_rgba((230, 250, 255)), width=2)
        d.rectangle((s * 0.30, s * 0.10, s * 0.70, s * 0.22), fill=_rgba(STEEL))
        d.rectangle((s * 0.30, s * 0.78, s * 0.70, s * 0.90), fill=_rgba(STEEL))
        d.line([(s * 0.5, s * 0.25), (s * 0.44, s * 0.45), (s * 0.56, s * 0.55), (s * 0.5, s * 0.75)], fill=(255, 255, 255, 255), width=3)
    elif kind == "nuclear":
        d.rounded_rectangle((s * 0.34, s * 0.30, s * 0.66, s * 0.92), radius=4, fill=_rgba((70, 76, 70)),
                            outline=_rgba((20, 24, 20)), width=2)
        d.polygon([(s * 0.34, s * 0.32), (s * 0.66, s * 0.32), (s * 0.5, s * 0.04)], fill=_rgba(_shade(accent, 0.8)),
                  outline=_rgba((20, 30, 20)))
        d.rectangle((s * 0.34, s * 0.80, s * 0.66, s * 0.92), fill=_rgba((196, 150, 60)))
        rr = s * 0.11
        cx, cy = s * 0.5, s * 0.55
        d.ellipse((cx - rr * 1.3, cy - rr * 1.3, cx + rr * 1.3, cy + rr * 1.3), fill=_rgba(accent))
        for k in range(3):
            a0 = -90 + k * 120 - 30
            d.pieslice((cx - rr * 1.2, cy - rr * 1.2, cx + rr * 1.2, cy + rr * 1.2), a0, a0 + 60, fill=(20, 20, 20, 255))
        d.ellipse((cx - rr * 0.25, cy - rr * 0.25, cx + rr * 0.25, cy + rr * 0.25), fill=(20, 20, 20, 255))
    else:
        raise ValueError(kind)
    return img


def draw_factory(w_tiles, h_tiles, accent, kind, seed=0):
    w, h = w_tiles * PX, h_tiles * PX
    img = draw_base(w_tiles, h_tiles, accent, ammo_strip_rows=0, seed=seed)
    d = ImageDraw.Draw(img)
    # tanques / camaras
    n = w_tiles
    for i in range(n):
        x0 = 14 + i * (w - 28) / n
        x1 = x0 + (w - 28) / n - 8
        d.rounded_rectangle((x0, 16, x1, h * 0.62), radius=10, fill=_rgba(_shade(accent, 0.35)),
                            outline=_rgba(_shade(accent, 1.0)), width=2)
        d.rounded_rectangle((x0 + 6, 24, x0 + 12, h * 0.55), radius=3, fill=_rgba(_shade(accent, 1.15), 220))
    # esteira de saida
    d.rectangle((12, h * 0.70, w - 12, h - 14), fill=_rgba(GUN_DARK))
    for x in range(16, w - 14, 10):
        d.line([(x, h * 0.70 + 2), (x, h - 16)], fill=_rgba(HULL_MID), width=2)
    icon = draw_resource_icon(kind, accent, size=int(min(w, h) * 0.45)).resize((int(min(w, h) * 0.32),) * 2)
    img.alpha_composite(icon, (int(w / 2 - icon.size[0] / 2), int(h * 0.66 - icon.size[1] / 2)))
    return img


def make_icon(base, turret, out_size=128):
    comp = base.copy()
    bw, bh = base.size
    tw, th = turret.size
    # o pivo da torre fica no centro da regiao acima da faixa de municao
    comp.alpha_composite(turret, (int(bw / 2 - tw / 2), int(bh * 0.40 - th / 2) if bh > bw else int(bh / 2 - th / 2)))
    scale = out_size / max(bw, bh)
    small = comp.resize((max(1, int(bw * scale)), max(1, int(bh * scale))), Image.LANCZOS)
    icon = Image.new("RGBA", (out_size, out_size), (0, 0, 0, 0))
    icon.alpha_composite(small, ((out_size - small.size[0]) // 2, (out_size - small.size[1]) // 2))
    return icon


def save(img, *rel):
    path = os.path.join(ROOT, *rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path
