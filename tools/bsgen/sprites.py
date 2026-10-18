"""Biblioteca de estilos de sprites do Bullet Strike (torres, canos, casco, fabricas, recursos, icones).

Convencoes do Cosmoteer (notas/08): 64 px/tile; torre e canos desenhados com o cano para CIMA;
teto (roof) em verde (0,G,0) para receber a pintura da nave; normais com G = +y para cima.
"""

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from bsgen.art import PX, SS, Canvas, drop_shadow, flat_normals, mix, shade, silhouette_shadow

METAL_DARK = (50, 54, 60)
METAL = (86, 92, 102)
METAL_LIGHT = (136, 144, 156)
GUNMETAL = (38, 40, 46)
STEEL = (118, 124, 134)
BRASS = (200, 154, 72)
WHITE = (214, 218, 222)
BLACK = (22, 22, 24)
UNPAINTED = (44, 47, 52)

ACCENTS = {
    "ammo": (226, 168, 48),
    "ap": (210, 210, 220),
    "aphe": (220, 70, 50),
    "emp": (80, 150, 255),
    "plasma": (60, 220, 255),
    "nuclear": (130, 255, 80),
    "flak": (255, 110, 50),
    "defense": (230, 60, 60),
}


# =====================================================================================  torres
def _base_ring(c, cx, cy, r, accent):
    c.fill(c.mask_ellipse(cx, cy, r), METAL_DARK, height=0.18, bevel=2)
    c.fill(c.mask_ellipse(cx, cy, r * 0.86), GUNMETAL, height=0.14, bevel=1, mode="set")
    n = max(10, int(r * 0.9))
    for k in range(n):
        a = k / n * math.tau
        c.rivet(cx + math.cos(a) * r * 0.93, cy + math.sin(a) * r * 0.93, max(0.8, r * 0.035), METAL_LIGHT, 0.06)


def _plate(c, mask, color, h=0.5, bevel=2.5, gradient=None):
    c.fill(mask, color, height=h, bevel=bevel, gradient=gradient)


def _panel_lines(c, x0, y0, x1, y1, nx=2, ny=2, depth=0.06):
    for i in range(1, nx):
        x = x0 + (x1 - x0) * i / nx
        c.groove([(x, y0 + 2), (x, y1 - 2)], 0.8, depth, shade(METAL, 0.6))
    for j in range(1, ny):
        y = y0 + (y1 - y0) * j / ny
        c.groove([(x0 + 2, y), (x1 - 2, y)], 0.8, depth, shade(METAL, 0.6))


def _rivet_row(c, x0, y0, x1, y1, n, r=0.9):
    for i in range(n):
        t = (i + 0.5) / n
        c.rivet(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, METAL_LIGHT, 0.05)


def _mantlets(c, cx, y_front, ys_px, bw_px, depth_px, color=GUNMETAL):
    for y in ys_px:
        x = cx + y
        c.fill(c.mask_rect(x - bw_px * 0.75, y_front, x + bw_px * 0.75, y_front + depth_px, r=bw_px * 0.3),
               color, height=0.62, bevel=1.2)
        c.fill(c.mask_rect(x - bw_px * 0.45, y_front - 1, x + bw_px * 0.45, y_front + depth_px * 0.45),
               BLACK, height=0.4, bevel=0.5, mode="set")


def _lamp(c, x, y, r, color):
    m = c.mask_ellipse(x, y, r)
    c.fill(m, shade(color, 0.6), height=0.55, bevel=0.5)
    c.glow(m, color, 0.9, blur=r * 0.8)


def turret_style(style, T, front_px, ys_px, bw_px, accent, seed=0, lamps_on=True):
    """Desenha a torre num canvas TxT (pivo no centro, cano para cima). Retorna Canvas."""
    rnd = random.Random(seed)
    c = Canvas(T, T)
    cx = cy = T / 2
    yf = cy - front_px                      # borda frontal da arte
    if style == "lmg":
        _base_ring(c, cx, cy, T * 0.40, accent)
        _plate(c, c.mask_rect(cx - T * 0.20, yf, cx + T * 0.20, cy + T * 0.26, r=T * 0.05), METAL, 0.5,
               gradient=(METAL_LIGHT, METAL_DARK))
        _panel_lines(c, cx - T * 0.2, yf, cx + T * 0.2, cy + T * 0.26, 2, 3)
        _plate(c, c.mask_rect(cx + T * 0.20, cy - T * 0.10, cx + T * 0.34, cy + T * 0.20, r=2), shade(accent, 0.75), 0.42)
        c.groove([(cx + T * 0.22, cy), (cx + T * 0.32, cy)], 0.8, 0.05, shade(accent, 0.4))
        _plate(c, c.mask_rect(cx - T * 0.33, cy - T * 0.02, cx - T * 0.20, cy + T * 0.16, r=2), METAL_DARK, 0.38)
        _mantlets(c, cx, yf, ys_px, bw_px, T * 0.10)
        if lamps_on:
            _lamp(c, cx - T * 0.27, cy + T * 0.07, T * 0.03, (255, 60, 40))
    elif style == "autocannon":
        _base_ring(c, cx, cy, T * 0.44, accent)
        w = T * 0.34
        pts = [(cx - w * 0.55, yf), (cx + w * 0.55, yf), (cx + w, yf + T * 0.16), (cx + w, cy + T * 0.30),
               (cx - w, cy + T * 0.30), (cx - w, yf + T * 0.16)]
        _plate(c, c.mask_poly(pts), METAL, 0.55, 2.5, gradient=(METAL_LIGHT, METAL_DARK))
        c.groove([(cx - w, yf + T * 0.16), (cx + w, yf + T * 0.16)], 1.0, 0.08, shade(METAL, 0.55))
        _panel_lines(c, cx - w, yf + T * 0.16, cx + w, cy + T * 0.30, 3, 2)
        _plate(c, c.mask_rect(cx - w * 0.95, cy - T * 0.02, cx - w * 0.55, cy + T * 0.16, r=2), METAL_DARK, 0.66)
        c.fill(c.mask_ellipse(cx + w * 0.5, cy + T * 0.16, T * 0.07), METAL_DARK, height=0.66, bevel=1)
        c.hazard(cx - w * 0.9, cy + T * 0.25, cx + w * 0.9, cy + T * 0.29, accent, BLACK, 5, height=0.58)
        _rivet_row(c, cx - w * 0.9, cy + T * 0.21, cx + w * 0.9, cy + T * 0.21, 8)
        _mantlets(c, cx, yf, ys_px, bw_px, T * 0.12)
        if lamps_on:
            _lamp(c, cx - w * 0.75, cy + T * 0.07, T * 0.025, (255, 70, 40))
    elif style in ("naval", "heavy_naval"):
        heavy = style == "heavy_naval"
        _base_ring(c, cx, cy, T * 0.46, accent)
        w = T * (0.40 if heavy else 0.36)
        rear = cy + T * (0.36 if heavy else 0.33)
        nose = yf + T * 0.03
        pts = [(cx - w * 0.62, nose), (cx + w * 0.62, nose), (cx + w, nose + T * 0.18), (cx + w, rear - T * 0.06),
               (cx + w * 0.8, rear), (cx - w * 0.8, rear), (cx - w, rear - T * 0.06), (cx - w, nose + T * 0.18)]
        _plate(c, c.mask_poly(pts), METAL, 0.6, 3.0, gradient=(STEEL, METAL_DARK))
        # face frontal inclinada
        face = [(cx - w * 0.62, nose), (cx + w * 0.62, nose), (cx + w * 0.86, nose + T * 0.14), (cx - w * 0.86, nose + T * 0.14)]
        _plate(c, c.mask_poly(face), shade(STEEL, 1.08), 0.68, 1.5, gradient=(METAL_LIGHT, METAL))
        c.groove([(cx - w * 0.86, nose + T * 0.14), (cx + w * 0.86, nose + T * 0.14)], 1.0, 0.09, shade(METAL, 0.5))
        _panel_lines(c, cx - w, nose + T * 0.14, cx + w, rear, 3 if heavy else 2, 3)
        # telemetro (orelhas laterais)
        for sgn in (-1, 1):
            ex = cx + sgn * (w + T * 0.05)
            _plate(c, c.mask_rect(ex - T * 0.05, cy + T * 0.02, ex + T * 0.05, cy + T * 0.10, r=T * 0.04), METAL_DARK, 0.55, 1)
            c.fill(c.mask_ellipse(ex + sgn * T * 0.035, cy + T * 0.06, T * 0.022), (90, 170, 220), height=0.6, bevel=0.5)
        # escotilhas e respiros
        c.fill(c.mask_ellipse(cx - w * 0.45, rear - T * 0.13, T * 0.06), METAL_DARK, height=0.7, bevel=1.2)
        c.fill(c.mask_ellipse(cx - w * 0.45, rear - T * 0.13, T * 0.035), METAL, height=0.74, bevel=0.6)
        for i in range(4 if heavy else 3):
            vy = cy + T * 0.04 + i * T * 0.045
            c.groove([(cx + w * 0.25, vy), (cx + w * 0.75, vy)], 1.4, 0.1, BLACK)
        c.hazard(cx - w * 0.7, rear - T * 0.045, cx + w * 0.7, rear - T * 0.012, accent, BLACK, 6, height=0.62)
        _rivet_row(c, cx - w * 0.95, nose + T * 0.2, cx - w * 0.95, rear - T * 0.08, 7 if heavy else 5)
        _rivet_row(c, cx + w * 0.95, nose + T * 0.2, cx + w * 0.95, rear - T * 0.08, 7 if heavy else 5)
        if heavy:
            c.fill(c.mask_rect(cx - w * 0.15, cy - T * 0.02, cx + w * 0.15, cy + T * 0.08, r=3), shade(accent, 0.55),
                   height=0.72, bevel=1)
        _mantlets(c, cx, nose - T * 0.01, ys_px, bw_px, T * 0.09)
        if lamps_on:
            _lamp(c, cx - w * 0.85, rear - T * 0.03, T * 0.018, (255, 60, 40))
            _lamp(c, cx + w * 0.85, rear - T * 0.03, T * 0.018, (255, 60, 40))
    elif style == "minigun":
        _base_ring(c, cx, cy, T * 0.43, accent)
        _plate(c, c.mask_ellipse(cx, cy + T * 0.02, T * 0.24), METAL, 0.55, 3, gradient=(METAL_LIGHT, METAL_DARK))
        c.groove([(cx - T * 0.24, cy + T * 0.02), (cx + T * 0.24, cy + T * 0.02)], 0.9, 0.07, shade(METAL, 0.55))
        # tambor de municao
        dx, dy, dr = cx + T * 0.27, cy + T * 0.12, T * 0.15
        _plate(c, c.mask_ellipse(dx, dy, dr), shade(accent, 0.7), 0.5, 2, gradient=(accent, shade(accent, 0.45)))
        for k in range(3):
            c.groove([(dx - dr * (0.85 - k * 0.25), dy), (dx + dr * (0.85 - k * 0.25), dy)], 0.7, 0.04, shade(accent, 0.35))
        c.fill(c.mask_ellipse(dx, dy, dr * 0.25), METAL_DARK, height=0.6, bevel=0.6)
        _plate(c, c.mask_rect(cx + T * 0.08, cy - T * 0.03, cx + T * 0.20, cy + T * 0.07), METAL_DARK, 0.48, 1)
        # alojamento dos canos
        _plate(c, c.mask_rect(cx - T * 0.13, yf, cx + T * 0.13, cy - T * 0.06, r=T * 0.05), METAL_DARK, 0.62, 1.5,
               gradient=(METAL, GUNMETAL))
        _rivet_row(c, cx - T * 0.1, yf + T * 0.05, cx + T * 0.1, yf + T * 0.05, 4)
        # motor traseiro
        _plate(c, c.mask_rect(cx - T * 0.10, cy + T * 0.20, cx + T * 0.10, cy + T * 0.33, r=T * 0.04), GUNMETAL, 0.5, 1)
        for i in range(3):
            c.groove([(cx - T * 0.08, cy + T * (0.23 + i * 0.03)), (cx + T * 0.08, cy + T * (0.23 + i * 0.03))], 0.8, 0.05, BLACK)
        if lamps_on:
            _lamp(c, cx - T * 0.18, cy + T * 0.16, T * 0.022, (255, 160, 40))
    elif style == "ciws":
        _base_ring(c, cx, cy, T * 0.43, accent)
        # radome branco estilo Phalanx atras dos canos
        _plate(c, c.mask_rect(cx - T * 0.19, cy - T * 0.10, cx + T * 0.19, cy + T * 0.34, r=T * 0.18), WHITE, 0.85, 4,
               gradient=((240, 242, 244), (170, 176, 182)))
        c.groove([(cx - T * 0.19, cy + T * 0.06), (cx + T * 0.19, cy + T * 0.06)], 0.8, 0.05, (150, 155, 160))
        c.groove([(cx - T * 0.17, cy + T * 0.20), (cx + T * 0.17, cy + T * 0.20)], 0.8, 0.05, (150, 155, 160))
        c.fill(c.mask_rect(cx - T * 0.16, cy + T * 0.26, cx + T * 0.16, cy + T * 0.29), shade(accent, 0.9),
               height=0.86, bevel=0.5)
        # suporte do canhao
        _plate(c, c.mask_rect(cx - T * 0.12, yf, cx + T * 0.12, cy - T * 0.08, r=T * 0.04), METAL_DARK, 0.6, 1.5,
               gradient=(METAL, GUNMETAL))
        # tambor lateral
        _plate(c, c.mask_rect(cx - T * 0.34, cy - T * 0.05, cx - T * 0.20, cy + T * 0.18, r=T * 0.05), METAL, 0.5, 2)
        _panel_lines(c, cx - T * 0.34, cy - T * 0.05, cx - T * 0.2, cy + T * 0.18, 1, 3)
        if lamps_on:
            _lamp(c, cx + T * 0.26, cy + T * 0.1, T * 0.025, accent)
    elif style == "plasma":
        _base_ring(c, cx, cy, T * 0.44, accent)
        w = T * 0.26
        pts = [(cx - w * 0.5, yf), (cx + w * 0.5, yf), (cx + w, yf + T * 0.2), (cx + w, cy + T * 0.26),
               (cx + w * 0.55, cy + T * 0.36), (cx - w * 0.55, cy + T * 0.36), (cx - w, cy + T * 0.26), (cx - w, yf + T * 0.2)]
        _plate(c, c.mask_poly(pts), (54, 60, 74), 0.62, 3, gradient=((96, 104, 124), (34, 38, 48)))
        # bobinas brilhantes
        for i in range(4):
            yy = yf + T * 0.12 + i * T * 0.09
            m = c.mask_rect(cx - w * 0.9, yy, cx + w * 0.9, yy + T * 0.025, r=2)
            c.fill(m, shade(accent, 0.5), height=0.7, bevel=0.5)
            c.glow(m, accent, 0.8, blur=2.5)
        # capacitores laterais
        for sgn in (-1, 1):
            ex = cx + sgn * (w + T * 0.09)
            _plate(c, c.mask_rect(ex - T * 0.06, cy - T * 0.12, ex + T * 0.06, cy + T * 0.22, r=T * 0.05),
                   (60, 66, 80), 0.5, 2, gradient=((110, 118, 136), (40, 44, 54)))
            m = c.mask_rect(ex - T * 0.02, cy - T * 0.08, ex + T * 0.02, cy + T * 0.18, r=2)
            c.fill(m, shade(accent, 0.6), height=0.56, bevel=0.4)
            c.glow(m, accent, 0.9, blur=2)
        core = c.mask_ellipse(cx, cy + T * 0.18, T * 0.07)
        c.fill(core, shade(accent, 0.7), height=0.75, bevel=1)
        c.glow(core, accent, 1.0, blur=4)
        _mantlets(c, cx, yf, ys_px, bw_px, T * 0.08, color=(44, 48, 60))
    elif style == "nuke":
        _base_ring(c, cx, cy, T * 0.47, accent)
        w = T * 0.40
        top = yf + T * 0.02
        rear = cy + T * 0.38
        ch = T * 0.10
        pts = [(cx - w + ch, top), (cx + w - ch, top), (cx + w, top + ch), (cx + w, rear - ch), (cx + w - ch, rear),
               (cx - w + ch, rear), (cx - w, rear - ch), (cx - w, top + ch)]
        _plate(c, c.mask_poly(pts), (74, 80, 72), 0.65, 4, gradient=((128, 136, 122), (48, 52, 46)))
        inner = [(x * 0.82 + cx * 0.18, y * 0.82 + cy * 0.18 + T * 0.02) for x, y in pts]
        _plate(c, c.mask_poly(inner), (84, 90, 80), 0.75, 2.5, gradient=((140, 148, 132), (60, 64, 56)))
        _panel_lines(c, cx - w * 0.8, top + T * 0.08, cx + w * 0.8, rear - T * 0.06, 2, 2, 0.08)
        # simbolo de radiacao
        rr = T * 0.11
        ey = cy + T * 0.08
        c.fill(c.mask_ellipse(cx, ey, rr * 1.15), (230, 200, 40), height=0.8, bevel=1)
        tre = Image.new("L", (c.W, c.H), 0)
        d = ImageDraw.Draw(tre)
        for k in range(3):
            a0 = -90 + k * 120 - 30
            d.pieslice(c.box(cx - rr, ey - rr, cx + rr, ey + rr), a0, a0 + 60, fill=255)
        d.ellipse(c.box(cx - rr * 0.2, ey - rr * 0.2, cx + rr * 0.2, ey + rr * 0.2), fill=255)
        c.fill(tre, BLACK, height=0.82, bevel=0.3)
        c.hazard(cx - w * 0.85, rear - T * 0.07, cx + w * 0.85, rear - T * 0.02, (230, 200, 40), BLACK, 7, height=0.7)
        c.hazard(cx - w * 0.85, top + T * 0.03, cx + w * 0.85, top + T * 0.07, (230, 200, 40), BLACK, 7, height=0.7)
        for sgn in (-1, 1):
            vx = cx + sgn * w * 0.62
            m = c.mask_rect(vx - T * 0.05, cy - T * 0.06, vx + T * 0.05, cy + T * 0.20, r=3)
            c.fill(m, BLACK, height=0.6, bevel=1, mode="set")
            for i in range(5):
                c.groove([(vx - T * 0.04, cy - T * 0.04 + i * T * 0.05), (vx + T * 0.04, cy - T * 0.04 + i * T * 0.05)],
                         1.0, 0.03, (70, 74, 70))
            g = c.mask_rect(vx - T * 0.03, cy - T * 0.03, vx + T * 0.03, cy + T * 0.17, r=2)
            c.glow(g, accent, 0.5, blur=3)
        _rivet_row(c, cx - w * 0.92, top + ch, cx - w * 0.92, rear - ch, 9)
        _rivet_row(c, cx + w * 0.92, top + ch, cx + w * 0.92, rear - ch, 9)
        _mantlets(c, cx, top - T * 0.01, ys_px, bw_px, T * 0.09)
        if lamps_on:
            _lamp(c, cx, rear - T * 0.12, T * 0.02, accent)
    elif style in ("flak", "aa_heavy"):
        heavy = style == "aa_heavy"
        _base_ring(c, cx, cy, T * 0.44, accent)
        w = T * (0.34 if heavy else 0.30)
        _plate(c, c.mask_rect(cx - w, yf + T * 0.06, cx + w, cy + T * 0.30, r=T * 0.10), METAL, 0.55, 3,
               gradient=(METAL_LIGHT, METAL_DARK))
        # escudos inclinados
        for sgn in (-1, 1):
            pts = [(cx + sgn * w * 0.15, yf), (cx + sgn * w * 1.05, yf + T * 0.08), (cx + sgn * w * 1.05, cy - T * 0.05),
                   (cx + sgn * w * 0.15, cy - T * 0.10)]
            _plate(c, c.mask_poly(pts), shade(STEEL, 1.05), 0.66, 1.5, gradient=(METAL_LIGHT, METAL))
        c.fill(c.mask_ellipse(cx, cy + T * 0.12, T * 0.10), shade(accent, 0.6), height=0.7, bevel=1)
        c.fill(c.mask_ellipse(cx, cy + T * 0.12, T * 0.05), METAL_DARK, height=0.74, bevel=0.6)
        _panel_lines(c, cx - w, cy - T * 0.05, cx + w, cy + T * 0.30, 2, 2)
        c.hazard(cx - w * 0.8, cy + T * 0.25, cx + w * 0.8, cy + T * 0.28, accent, BLACK, 5, height=0.6)
        _mantlets(c, cx, yf + T * 0.02, ys_px, bw_px, T * 0.08)
        if lamps_on:
            _lamp(c, cx + w * 0.8, cy + T * 0.2, T * 0.022, (255, 60, 40))
    else:
        raise ValueError(style)
    return c


def render_turret(style, ts_tiles, front_tiles, ys_tiles, bw_tiles, accent, seed=0):
    T = int(round(ts_tiles * PX))
    front = front_tiles * PX
    ys = [y * PX for y in ys_tiles]
    bw = bw_tiles * PX * 0.5
    on = turret_style(style, T, front, ys, bw, accent, seed, lamps_on=True)
    off = turret_style(style, T, front, ys, bw, accent, seed, lamps_on=False)
    img_on = drop_shadow(on.render(), 2, 45)
    img_off = drop_shadow(off.render(), 2, 45)
    off_arr = np.asarray(img_off, dtype=np.float32)
    off_arr[..., :3] *= 0.86
    img_off = Image.fromarray(np.clip(off_arr, 0, 255).astype(np.uint8), "RGBA")
    nrm = on.final_normals()
    shadow = silhouette_shadow(img_on, (T, T), blur=max(3, T // 40), alpha=120)
    return img_on, img_off, nrm, shadow


# =====================================================================================  canos
def _tube(c, x0, x1, y0, y1, color, h=0.5, rings=()):
    """Tubo vertical com sombreamento cilindrico (altura em meio-cilindro)."""
    w = x1 - x0
    m = c.mask_rect(x0, y0, x1, y1, r=min(w * 0.25, 3))
    grad = Image.linear_gradient("L").rotate(90, expand=True).resize((c.W, c.H))
    c.fill(m, color, height=None)
    # perfil cilindrico na altura
    X0, X1 = int(x0 * SS), int(x1 * SS)
    Y0, Y1 = int(max(0, y0 * SS)), int(min(c.H, y1 * SS))
    if X1 > X0 and Y1 > Y0:
        xs = np.linspace(-1, 1, X1 - X0, dtype=np.float32)
        prof = np.sqrt(np.clip(1 - xs * xs, 0, 1)) * h
        c.height[Y0:Y1, X0:X1] = np.maximum(c.height[Y0:Y1, X0:X1], prof[None, :])
        # brilho especular embutido
        arr = np.asarray(c.albedo, dtype=np.float32)
        hl = np.exp(-((xs + 0.35) ** 2) / 0.05) * 0.35 + 1.0 - np.clip(xs, 0, 1) * 0.35
        arr[Y0:Y1, X0:X1, :3] *= hl[None, :, None]
        c.albedo = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    for ry, rh, rc in rings:
        c.fill(c.mask_rect(x0 - 1, ry, x1 + 1, ry + rh, r=1), rc, height=h + 0.08, bevel=0.5)


def barrel_canvas(kind, bw_px, bl_px, accent, offset=0.0, phase=0):
    """Desenha um cano (cano para cima) num canvas bw x bl, deslocado 'offset' px para tras (recuo)."""
    c = Canvas(bw_px, bl_px)
    cx = bw_px / 2
    o = offset
    if kind in ("plain", "brake", "fins", "heavy", "howitzer"):
        tw = bw_px * (0.42 if kind != "howitzer" else 0.55)
        _tube(c, cx - tw / 2, cx + tw / 2, 2 + o, bl_px + 4, GUNMETAL if kind != "heavy" else METAL_DARK, 0.5,
              rings=[(bl_px * 0.55 + o, 3, METAL)])
        if kind in ("brake", "howitzer", "heavy"):
            bwid = tw * (1.55 if kind == "howitzer" else 1.35)
            c.fill(c.mask_rect(cx - bwid / 2, 1 + o, cx + bwid / 2, 1 + o + bl_px * 0.12, r=2), METAL_DARK, height=0.6, bevel=1)
            for k in range(3):
                yy = 3 + o + k * bl_px * 0.035
                c.groove([(cx - bwid / 2 + 1, yy), (cx + bwid / 2 - 1, yy)], 1.0, 0.1, BLACK)
        if kind == "howitzer":
            c.fill(c.mask_rect(cx - tw * 0.7, bl_px * 0.38 + o, cx + tw * 0.7, bl_px * 0.52 + o, r=tw * 0.3), METAL,
                   height=0.6, bevel=1.5)
        if kind == "fins":
            for k in range(6):
                yy = bl_px * 0.15 + o + k * bl_px * 0.07
                c.fill(c.mask_rect(cx - tw * 0.9, yy, cx + tw * 0.9, yy + 1.4), METAL, height=0.58, bevel=0.3)
        c.fill(c.mask_rect(cx - tw * 0.32, 0 + o, cx + tw * 0.32, 2.5 + o), BLACK, height=0.2, mode="set")
    elif kind == "gatling":
        n = 3
        tw = bw_px * 0.24
        span = bw_px * 0.78
        for i in range(n):
            x = cx - span / 2 + tw / 2 + i * (span - tw) / (n - 1)
            bright = 1.0 + 0.25 * math.cos((i + phase * 0.33) * math.pi * 0.66)
            _tube(c, x - tw / 2, x + tw / 2, 2 + o, bl_px + 2, shade(GUNMETAL, bright), 0.45)
        for ry in (bl_px * 0.05, bl_px * 0.38, bl_px * 0.72):
            c.fill(c.mask_rect(cx - span / 2 - 1, ry + o, cx + span / 2 + 1, ry + o + 3, r=1), METAL, height=0.6, bevel=0.5)
        c.fill(c.mask_rect(cx - span / 2, o + 1, cx + span / 2, o + 3), shade(accent, 0.6), height=0.62, bevel=0.3)
    elif kind == "plasma":
        tw = bw_px * 0.46
        _tube(c, cx - tw / 2, cx + tw / 2, 3 + o, bl_px + 4, (50, 56, 70), 0.5)
        for k in range(5):
            yy = bl_px * 0.12 + o + k * bl_px * 0.15
            m = c.mask_rect(cx - tw * 0.75, yy, cx + tw * 0.75, yy + bl_px * 0.045, r=1.5)
            c.fill(m, shade(accent, 0.55), height=0.6, bevel=0.4)
            c.glow(m, accent, 0.85, blur=1.5)
        crown = c.mask_rect(cx - tw * 0.8, 1 + o, cx + tw * 0.8, 1 + o + bl_px * 0.06, r=2)
        c.fill(crown, (70, 78, 96), height=0.62, bevel=0.8)
        c.glow(c.mask_rect(cx - tw * 0.25, o, cx + tw * 0.25, o + 2), accent, 1.0, 1.5)
    else:
        raise ValueError(kind)
    return c


RECOIL = [0.0, 0.55, 1.0, 0.66, 0.33]


def render_barrel_frames(kind, bw_tiles, bl_tiles, accent, recoil_px, spin=False):
    bw = max(8, int(round(bw_tiles * PX)))
    bl = max(16, int(round(bl_tiles * PX)))
    frames, normals = [], []
    if spin:
        seq = [(0, 1), (0, 2), (0, 3), (0, 0)]    # (recuo, fase): ultimo = repouso
        for off, ph in seq:
            cv = barrel_canvas(kind, bw, bl, accent, 0, ph)
            frames.append(cv.render())
            normals.append(cv.final_normals())
        return frames, normals
    for f in RECOIL:
        cv = barrel_canvas(kind, bw, bl, accent, f * recoil_px)
        frames.append(cv.render())
        normals.append(cv.final_normals())
    return frames, normals


# =====================================================================================  casco
def render_hull(w, h, accent, pivot, ring_r_tiles, crew_pos, seed=0, machinery=True):
    """floor.png, walls.png, roof.png (verde), roof_normals.png para uma peca w x h."""
    W, H = w * PX, h * PX
    rnd = random.Random(seed)
    # ---- teto
    r = Canvas(W, H)
    r.fill(r.mask_rect(0, 0, W, H), (0, 236, 0), height=0.5, bevel=2.5)
    r.fill(r.mask_rect(2, 2, W - 2, H - 2, r=3), (0, 250, 0), height=0.55, bevel=2)
    for tx in range(1, w):
        r.groove([(tx * PX, 4), (tx * PX, H - 4)], 1.2, 0.1, (0, 196, 0))
    for ty in range(1, h):
        r.groove([(4, ty * PX), (W - 4, ty * PX)], 1.2, 0.1, (0, 196, 0))
    # cantos com respiros sem pintura
    for (vx, vy) in [(6, H - 14), (W - 22, H - 14)]:
        r.fill(r.mask_rect(vx, vy, vx + 16, vy + 8, r=2), UNPAINTED, height=0.4, bevel=0.8, mode="set")
        for k in range(3):
            r.groove([(vx + 2, vy + 2 + k * 2.2), (vx + 14, vy + 2 + k * 2.2)], 0.8, 0.05, BLACK)
    # faixa de perigo na traseira
    r.hazard(W * 0.3, H - 7, W * 0.7, H - 3, (220, 170, 40), BLACK, 6, height=0.5)
    # anel da torre (sem pintura)
    px, py = pivot[0] * PX, pivot[1] * PX
    rr = ring_r_tiles * PX
    if rr > 4:
        r.fill(r.mask_ellipse(px, py, rr + 3), UNPAINTED, height=0.42, bevel=1.5, mode="set")
        r.fill(r.mask_ellipse(px, py, rr), (30, 32, 36), height=0.3, bevel=1, mode="set")
        n = max(12, int(rr / 3))
        for k in range(n):
            a = k / n * math.tau
            r.rivet(px + math.cos(a) * (rr + 1.5), py + math.sin(a) * (rr + 1.5), 0.9, (90, 94, 100), 0.05)
    roof = r.render(bake=False)
    roof_n = r.final_normals()
    roof = Image.fromarray(np.dstack([np.asarray(roof)[..., :3], np.full((H, W), 255, np.uint8)]), "RGBA")
    roof_n.putalpha(255)

    # ---- piso
    f = Canvas(W, H)
    f.fill(f.mask_rect(0, 0, W, H), (46, 44, 42), height=0.2, bevel=0)
    for tx in range(w):
        for ty in range(h):
            f.fill(f.mask_rect(tx * PX + 3, ty * PX + 3, tx * PX + PX - 3, ty * PX + PX - 3, r=2), (58, 56, 53),
                   height=0.25, bevel=1)
    if machinery and rr > 4:
        f.fill(f.mask_ellipse(px, py, rr * 0.95), (34, 34, 36), height=0.3, bevel=1)
        f.fill(f.mask_ellipse(px, py, rr * 0.55), (70, 72, 78), height=0.4, bevel=1)
        f.fill(f.mask_ellipse(px, py, rr * 0.2), shade(accent, 0.6), height=0.45, bevel=0.5)
        # suportes de carregadores na fileira de tras
        for tx in range(w):
            bx = tx * PX + PX * 0.18
            f.fill(f.mask_rect(bx, H - PX * 0.32, bx + PX * 0.64, H - PX * 0.08, r=2), shade(accent, 0.45),
                   height=0.4, bevel=1)
            f.groove([(bx + 2, H - PX * 0.2), (bx + PX * 0.62, H - PX * 0.2)], 0.8, 0.04, shade(accent, 0.25))
    for (cx, cy, _rot) in crew_pos:
        x, y = cx * PX, cy * PX
        f.fill(f.mask_rect(x - 9, y - 4, x + 9, y + 9, r=4), (90, 60, 50), height=0.4, bevel=1)
        f.fill(f.mask_rect(x - 10, y - 14, x + 10, y - 7, r=2), (40, 46, 56), height=0.45, bevel=0.8)
        f.glow(f.mask_rect(x - 6, y - 12, x + 6, y - 9), (90, 200, 255), 0.6, 1.2)
    floor = f.render()
    floor = Image.fromarray(np.dstack([np.asarray(floor)[..., :3], np.full((H, W), 255, np.uint8)]), "RGBA")

    # ---- paredes (moldura de 7 px + sombra interna)
    walls = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(walls)
    cols = [(22, 22, 22, 255), (33, 33, 33, 255), (82, 86, 90, 255), (92, 96, 100, 255), (86, 90, 94, 255),
            (78, 82, 86, 255), (48, 46, 44, 255)]
    for i, col in enumerate(cols):
        d.rectangle([i, i, W - 1 - i, H - 1 - i], outline=col)
    for i in range(7):
        a = int(115 * (1 - i / 7) ** 1.6)
        d.rectangle([7 + i, 7 + i, W - 8 - i, H - 8 - i], outline=(0, 0, 0, a))
    return floor, walls, roof, roof_n


# =====================================================================================  icones
def paint_roof_preview(roof, paint=(120, 124, 132)):
    """Simula a pintura da nave (verde -> cor) para os icones."""
    arr = np.asarray(roof, dtype=np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    green = (g - np.maximum(r, b) > 12) & (np.abs(r - b) < 64)
    k = g / 255.0
    for i, pc in enumerate(paint):
        arr[..., i] = np.where(green, pc * k, arr[..., i])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def compose_weapon(w, h, roof, turret, barrels, geo, overhang):
    """Monta a peca vista de cima (icone/preview) com o cano para cima, incluindo o cano que sai da peca."""
    W, H = w * PX, (h + overhang) * PX
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(paint_roof_preview(roof), (0, overhang * PX))
    px, py = geo["pivot"][0] * PX, (geo["pivot"][1] + overhang) * PX
    T = turret.size[0]
    img.alpha_composite(turret, (int(round(px - T / 2)), int(round(py - T / 2))))
    bw_px, bl_px = barrels[0].size
    for y in geo["ys"]:
        bx = px + y * PX - bw_px / 2
        by = py - geo["barrel_center"] * PX - bl_px / 2
        img.alpha_composite(barrels[0], (int(round(bx)), int(round(by))))
    return img


def blueprint_from(w, h, silhouette=None, sil_offset=(0, 0), color=(220, 40, 40)):
    W, H = w * PX, h * PX
    img = Image.new("RGBA", (W, H), (29, 139, 248, 80))
    d = ImageDraw.Draw(img)
    border = [(0, 0, 190), (0, 0, 201), (11, 11, 255), (25, 25, 255), (41, 41, 255), (0, 0, 231), (0, 0, 214)]
    for i, col in enumerate(border):
        d.rectangle([i, i, W - 1 - i, H - 1 - i], outline=col + (255,))
    if silhouette is not None:
        a = silhouette.getchannel("A")
        red = Image.new("RGBA", silhouette.size, color + (0,))
        red.putalpha(a.point(lambda v: int(v * 0.85)))
        sh = ImageOps.grayscale(silhouette).point(lambda v: v)
        tint = Image.merge("RGBA", (sh.point(lambda v: min(255, 120 + v)), sh.point(lambda v: v // 4),
                                    sh.point(lambda v: v // 4), a.point(lambda v: int(v * 0.85))))
        img.alpha_composite(tint, (int(sil_offset[0]), int(sil_offset[1])))
    return img


def fit_icon(img, max_side=None):
    return img


# =====================================================================================  fabricas
def render_factory(w, h, accent, out_kind, seed=0):
    W, H = w * PX, h * PX
    floor, walls, roof, roof_n = render_hull(w, h, accent, (w / 2, 0.5), 0.0001, [], seed, machinery=False)
    # piso com esteiras nas grades da fileira de baixo
    f = Canvas(W, H)
    f.fill(f.mask_rect(0, 0, W, H), (46, 44, 42), height=0.2, bevel=0)
    for tx in range(w):
        f.fill(f.mask_rect(tx * PX + 4, PX + 4, tx * PX + PX - 4, H - 4, r=3), (66, 64, 60), height=0.25, bevel=1)
        f.hazard(tx * PX + 4, H - 8, tx * PX + PX - 4, H - 4, (200, 160, 40), BLACK, 5, height=0.3)
    f.fill(f.mask_rect(2, 2, W - 2, PX - 2, r=3), (36, 36, 40), height=0.3, bevel=1)
    floor = Image.fromarray(np.dstack([np.asarray(f.render())[..., :3], np.full((H, W), 255, np.uint8)]), "RGBA")
    # maquinario animado (faixa de cima)
    frames = []
    for k in range(4):
        m = Canvas(W, PX)
        m.fill(m.mask_rect(4, 6, W - 4, PX - 6, r=6), METAL, height=0.5, bevel=2, gradient=(METAL_LIGHT, METAL_DARK))
        for i in range(w * 2):
            x = 10 + i * (W - 20) / (w * 2)
            m.fill(m.mask_rect(x, 14, x + (W - 20) / (w * 2) - 4, PX - 14, r=3), METAL_DARK, height=0.55, bevel=1)
        # pistao/prensa
        py = 18 + abs(2 - k) * 6
        m.fill(m.mask_rect(W / 2 - 10, py, W / 2 + 10, py + 14, r=2), shade(accent, 0.8), height=0.7, bevel=1)
        lamp = m.mask_ellipse(W - 14, 14, 3)
        m.fill(lamp, shade(accent, 0.5), height=0.6, bevel=0.3)
        if k % 2 == 0:
            m.glow(lamp, accent, 1.0, 2)
        frames.append(m.render())
    off = frames[0].copy()
    arr = np.asarray(off, dtype=np.float32)
    arr[..., :3] *= 0.7
    off = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    return floor, walls, roof, roof_n, frames, off


# =====================================================================================  recursos
def render_resource(kind, accent, n_stack):
    """icon 64, overlay 128 (silhueta branca), nugget 64 (+normais), stack_1..n 64."""
    def mag_item(c, x, y, s, horizontal=False):
        # carregador (caixa com janela de municao) / celula / projetil
        if kind == "mag":
            w_, h_ = (s * 0.9, s * 0.5) if horizontal else (s * 0.5, s * 0.9)
            c.fill(c.mask_rect(x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2, r=s * 0.08), (70, 74, 80),
                   height=0.6, bevel=1.5, gradient=((120, 126, 134), (50, 54, 60)))
            c.fill(c.mask_rect(x - w_ * 0.3, y - h_ * 0.3, x + w_ * 0.3, y + h_ * 0.3, r=2), shade(accent, 0.9),
                   height=0.66, bevel=0.6)
            c.groove([(x - w_ * 0.25, y), (x + w_ * 0.25, y)], 0.8, 0.04, shade(accent, 0.4))
        elif kind == "cell":
            w_, h_ = (s * 0.9, s * 0.45) if horizontal else (s * 0.45, s * 0.9)
            c.fill(c.mask_rect(x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2, r=s * 0.15), (60, 66, 80),
                   height=0.6, bevel=1.5)
            core = c.mask_rect(x - w_ * 0.32, y - h_ * 0.32, x + w_ * 0.32, y + h_ * 0.32, r=s * 0.1)
            c.fill(core, shade(accent, 0.6), height=0.66, bevel=0.6)
            c.glow(core, accent, 0.9, 2)
        elif kind == "shell":
            w_, h_ = (s * 0.95, s * 0.42) if horizontal else (s * 0.42, s * 0.95)
            if horizontal:
                body = c.mask_rect(x - w_ / 2, y - h_ / 2, x + w_ * 0.25, y + h_ / 2, r=2)
                nose = c.mask_poly([(x + w_ * 0.25, y - h_ / 2), (x + w_ / 2, y), (x + w_ * 0.25, y + h_ / 2)])
            else:
                body = c.mask_rect(x - w_ / 2, y - h_ * 0.25, x + w_ / 2, y + h_ / 2, r=2)
                nose = c.mask_poly([(x - w_ / 2, y - h_ * 0.25), (x, y - h_ / 2), (x + w_ / 2, y - h_ * 0.25)])
            c.fill(body, (90, 96, 86), height=0.6, bevel=1.2, gradient=((150, 158, 140), (60, 64, 56)))
            c.fill(nose, shade(accent, 0.85), height=0.62, bevel=1.0)
            band = c.mask_rect(x - w_ * 0.08, y - h_ / 2, x + w_ * 0.02, y + h_ / 2) if horizontal else \
                c.mask_rect(x - w_ / 2, y + h_ * 0.05, x + w_ / 2, y + h_ * 0.13)
            c.fill(band, (230, 200, 40), height=0.64, bevel=0.3)

    # icone
    ic = Canvas(64, 64)
    mag_item(ic, 32, 32, 52, horizontal=True)
    icon = ic.render()
    # nugget
    nc = Canvas(64, 64)
    mag_item(nc, 32, 32, 36, horizontal=True)
    nugget = nc.render()
    nugget_n = nc.final_normals()
    # silhueta branca 128
    oc = Canvas(128, 128)
    for i, xx in enumerate((40, 64, 88)):
        mag_item(oc, xx, 64, 56)
    a = oc.render().getchannel("A")
    overlay = Image.new("RGBA", (128, 128), (255, 255, 255, 0))
    overlay.putalpha(a)
    # pilhas
    stacks = []
    slots = []
    cols = 3 if n_stack > 4 else 2
    rows = int(math.ceil(n_stack / cols))
    for i in range(n_stack):
        r_, c_ = divmod(i, cols)
        slots.append((14 + c_ * (36 / max(1, cols - 1)), 16 + r_ * (32 / max(1, rows - 1)) if rows > 1 else 32))
    for k in range(1, n_stack + 1):
        sc = Canvas(64, 64)
        for (x, y) in slots[:k]:
            mag_item(sc, x, y, 26 if n_stack > 4 else 30)
        stacks.append(sc.render())
    return icon, overlay, nugget, nugget_n, stacks


def render_toggle_icon(kind, accent):
    c = Canvas(64, 64)
    c.fill(c.mask_ellipse(32, 32, 29), (34, 36, 42), height=0.4, bevel=2)
    c.fill(c.mask_ellipse(32, 32, 25), shade(accent, 0.35), height=0.45, bevel=1)
    if kind == "std":
        c.fill(c.mask_rect(26, 14, 38, 46, r=3), BRASS, height=0.7, bevel=1)
        c.fill(c.mask_poly([(26, 16), (32, 8), (38, 16)]), (170, 120, 60), height=0.7, bevel=1)
    elif kind == "ap":
        c.fill(c.mask_rect(26, 18, 38, 48, r=3), (160, 166, 176), height=0.7, bevel=1)
        c.fill(c.mask_poly([(26, 20), (32, 6), (38, 20)]), (40, 40, 44), height=0.75, bevel=1)
    elif kind == "aphe":
        c.fill(c.mask_rect(26, 18, 38, 48, r=3), (160, 166, 176), height=0.7, bevel=1)
        c.fill(c.mask_poly([(26, 20), (32, 6), (38, 20)]), (40, 40, 44), height=0.75, bevel=1)
        c.fill(c.mask_rect(26, 30, 38, 35), (230, 60, 40), height=0.72, bevel=0.5)
    elif kind == "emp":
        bolt = c.mask_poly([(35, 8), (22, 34), (31, 34), (27, 56), (42, 26), (33, 26)])
        c.fill(bolt, (150, 200, 255), height=0.75, bevel=0.8)
        c.glow(bolt, accent, 0.8, 3)
    img = c.render()
    return img


def render_group_icon():
    c = Canvas(96, 96)
    for i, x in enumerate((30, 48, 66)):
        y0 = 22 + abs(i - 1) * 6
        c.fill(c.mask_rect(x - 7, y0 + 14, x + 7, 80, r=3), BRASS, height=0.6, bevel=1.5,
               gradient=((240, 200, 110), (150, 105, 40)))
        c.fill(c.mask_poly([(x - 7, y0 + 16), (x, y0), (x + 7, y0 + 16)]), (180, 120, 60), height=0.65, bevel=1.2)
        c.fill(c.mask_rect(x - 7, 70, x + 7, 74), (120, 80, 30), height=0.62, bevel=0.5)
    return c.render()


# =====================================================================================  lancadores de misseis
# Arte provisoria (procedural) dos lancadores de convés ate o modelo 3D existir (contrato: STYLE.md secao 8).
# Casulo (turret.png) em roof_doodads; celulas carregadas (cells_<tipo>_p<casulo>_<n>.png) em roof_turrets,
# desenhadas no quadro da torre (lado = turret_box, pivo no centro, frente para cima) e recortadas por
# tools/make_art.py no retangulo do casulo (launcher_layout.overlay_rect), transparentes fora dos narizes.
def _tp(T, fwd, lat):
    """Coordenadas da torre (tiles, x frente / y direita) -> pixels do quadro da torre (frente para cima)."""
    return T / 2 + lat * PX, T / 2 - fwd * PX


def _tube_extent(T, units, tube_r, pitch_deg):
    tubes = [t for u in units for t in u["tubes"]]
    r = tube_r * PX
    ry = r * max(0.35, math.sin(math.radians(pitch_deg)))
    xs = [_tp(T, *t)[0] for t in tubes]
    ys = [_tp(T, *t)[1] for t in tubes]
    return tubes, r, ry, min(xs), max(xs), min(ys), max(ys)


def launcher_pod_canvas(T, units, tube_r, pitch_deg, accent, lamps_on=True):
    """Caixa de micromisseis estilo RAM (Tocandira): caixa chanfrada inclinada sobre um garfo blindado, grade
    escura de tubos (cassetes de 2), garras laterais, espinha com fenda ambar e baia de respiro traseira."""
    c = Canvas(T, T)
    cx = cy = T / 2
    tubes, r, ry, xmin, xmax, ymin, ymax = _tube_extent(T, units, tube_r, pitch_deg)
    pad_x, pad_y = r * 1.9, ry * 2.8
    fx0, fx1 = xmin - pad_x, xmax + pad_x                  # face com os tubos
    fy0, fy1 = ymin - pad_y, ymax + pad_y
    bx0, bx1 = fx0 - T * 0.04, fx1 + T * 0.04              # corpo da caixa
    rear = cy + T * 0.31
    _base_ring(c, cx, cy, T * 0.38, accent)
    # garfo (yoke) curto sob a caixa
    for sgn in (-1, 1):
        ex = cx + sgn * (bx1 - cx + T * 0.01)
        _plate(c, c.mask_rect(ex - T * 0.05, cy - T * 0.12, ex + T * 0.05, cy + T * 0.16, r=T * 0.02), GUNMETAL, 0.42, 1)
    ch = T * 0.06
    body = [(bx0 + ch, fy0), (bx1 - ch, fy0), (bx1, fy0 + ch), (bx1, rear - ch), (bx1 - ch, rear),
            (bx0 + ch, rear), (bx0, rear - ch), (bx0, fy0 + ch)]
    _plate(c, c.mask_poly(body), STEEL, 0.6, 3, gradient=(METAL_LIGHT, METAL_DARK))
    inner = [(x * 0.9 + cx * 0.1, y * 0.9 + (fy0 + rear) / 2 * 0.1) for x, y in body]
    _plate(c, c.mask_poly(inner), shade(STEEL, 1.06), 0.68, 2, gradient=(WHITE, METAL))
    # face inclinada com a grade de tubos (recesso escuro)
    c.fill(c.mask_rect(fx0, fy0 + T * 0.01, fx1, fy1, r=T * 0.025), GUNMETAL, height=0.5, bevel=1.2, mode="set")
    c.groove([(fx0, fy1), (fx1, fy1)], 1.2, 0.1, BLACK)
    for (fwd, lat) in tubes:
        x, y = _tp(T, fwd, lat)
        c.fill(c.mask_ellipse(x, y, r * 1.18, ry * 1.25), METAL_DARK, height=0.52, bevel=0.6, mode="set")
        c.fill(c.mask_ellipse(x, y, r, ry), BLACK, height=0.3, bevel=0.4, mode="set")
    # divisores de cassete (pares) e de fileira
    for u in units:
        if len(u["tubes"]) > 1:
            (f0, l0), (f1, l1) = u["tubes"][0], u["tubes"][-1]
            xa, ya = _tp(T, f0, l0)
            xb, _yb = _tp(T, f1, l1)
            c.groove([(xa - r * 1.25, ya + ry * 1.5), (xb + r * 1.25, ya + ry * 1.5)], 0.7, 0.05, shade(METAL, 0.55))
    # garras laterais que abracam a caixa
    for sgn in (-1, 1):
        x_out = cx + sgn * (bx1 - cx)
        pts = [(x_out, fy0 + T * 0.02), (x_out + sgn * T * 0.07, fy0 + T * 0.10), (x_out + sgn * T * 0.07, cy + T * 0.06),
               (x_out, cy + T * 0.12)]
        _plate(c, c.mask_poly(pts), shade(STEEL, 1.1), 0.7, 1.2, gradient=(METAL_LIGHT, METAL))
        c.groove([(x_out + sgn * T * 0.035, fy0 + T * 0.12), (x_out + sgn * T * 0.035, cy + T * 0.04)], 0.7, 0.05,
                 shade(METAL, 0.5))
    # espinha central com fenda do sensor IR
    sy0, sy1 = fy1 + T * 0.03, rear - T * 0.12
    _plate(c, c.mask_rect(cx - T * 0.06, sy0, cx + T * 0.06, sy1, r=T * 0.02), shade(STEEL, 1.12), 0.8, 1.2,
           gradient=(WHITE, METAL_LIGHT))
    slit = c.mask_rect(cx - T * 0.035, sy0 + T * 0.03, cx + T * 0.035, sy0 + T * 0.055, r=1)
    c.fill(slit, BLACK, height=0.7, bevel=0.3, mode="set")
    if lamps_on:
        c.glow(slit, accent, 0.8, blur=1.5)
    # baia de respiro traseira com 3 pips
    vy0, vy1 = rear - T * 0.10, rear - T * 0.03
    c.fill(c.mask_rect(bx0 + T * 0.08, vy0, bx1 - T * 0.08, vy1, r=2), BLACK, height=0.5, bevel=0.6, mode="set")
    for i in range(5):
        lx = bx0 + T * 0.1 + i * (bx1 - bx0 - T * 0.2) / 4
        c.groove([(lx, vy0 + 2), (lx, vy1 - 2)], 0.8, 0.04, (70, 74, 80))
    for i in range(3):
        px = cx + (i - 1) * T * 0.045
        pip = c.mask_ellipse(px, (vy0 + vy1) / 2, T * 0.012)
        c.fill(pip, shade(accent, 0.45), height=0.55, bevel=0.2)
        if lamps_on:
            c.glow(pip, accent, 0.9, blur=1.2)
    _rivet_row(c, bx0 + T * 0.03, fy1 + T * 0.04, bx0 + T * 0.03, rear - T * 0.04, 4)
    _rivet_row(c, bx1 - T * 0.03, fy1 + T * 0.04, bx1 - T * 0.03, rear - T * 0.04, 4)
    return c


def _pods_px(T, units):
    """Por casulo (ordem do indice): (x0, x1, y0, y1) dos tubos em pixels do quadro da torre."""
    pods = {}
    for u in units:
        pods.setdefault(u["pod"], []).extend(u["tubes"])
    out = []
    for _p, tubes in sorted(pods.items()):
        xs = [_tp(T, *t)[0] for t in tubes]
        ys = [_tp(T, *t)[1] for t in tubes]
        out.append((min(xs), max(xs), min(ys), max(ys)))
    return out


def _octagon(x0, y0, x1, y1, ch):
    return [(x0 + ch, y0), (x1 - ch, y0), (x1, y0 + ch), (x1, y1 - ch), (x1 - ch, y1), (x0 + ch, y1), (x0, y1 - ch),
            (x0, y0 + ch)]


def _rot_pts(pts, cx, cy, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def _tube_holes(c, T, units, r, ry):
    for u in units:
        for (fwd, lat) in u["tubes"]:
            x, y = _tp(T, fwd, lat)
            c.fill(c.mask_ellipse(x, y, r * 1.18, ry * 1.25), METAL_DARK, height=0.52, bevel=0.6, mode="set")
            c.fill(c.mask_ellipse(x, y, r, ry), BLACK, height=0.3, bevel=0.4, mode="set")


def _vent_bay(c, x0, x1, y0, y1, n_pips, accent, lamps_on, slats=6):
    c.fill(c.mask_rect(x0, y0, x1, y1, r=2), BLACK, height=0.5, bevel=0.6, mode="set")
    for i in range(slats):
        lx = x0 + (x1 - x0) * (i + 0.5) / slats
        c.groove([(lx, y0 + 2), (lx, y1 - 2)], 0.8, 0.04, (70, 74, 80))
    cx = (x0 + x1) / 2
    step = min((x1 - x0) / (n_pips + 1), (y1 - y0) * 1.4)
    for i in range(n_pips):
        px = cx + (i - (n_pips - 1) / 2) * step
        pip = c.mask_ellipse(px, (y0 + y1) / 2, max(1.2, (y1 - y0) * 0.17))
        c.fill(pip, shade(accent, 0.45), height=0.55, bevel=0.2)
        if lamps_on:
            c.glow(pip, accent, 0.9, blur=1.2)


def launcher_twin_canvas(T, units, tube_r, pitch_deg, accent, lamps_on=True, oc_glow=False):
    """Caipora: dois casulos OCTOGONAIS inclinados ladeando uma cupula blindada com um olho sensor ambar,
    garras na frente dos casulos, quatro pes abertos sobre o anel, escotilha de carregador e baia de respiro
    traseira com 5 pips. oc_glow=True devolve so o brilho de overclock (olho laranja + brasas do respiro)."""
    c = Canvas(T, T)
    cx = cy = T / 2
    _tubes, r, ry, *_ = _tube_extent(T, units, tube_r, pitch_deg)
    pods = _pods_px(T, units)
    pad_x, pad_y = r * 2.2, ry * 3.2
    dome_y, dome_r = cy + T * 0.02, T * 0.15
    eye = c.mask_rect(cx - dome_r * 0.55, dome_y - dome_r * 0.72, cx + dome_r * 0.55, dome_y - dome_r * 0.5, r=1.5)
    vy0, vy1 = cy + T * 0.27, cy + T * 0.33
    if oc_glow:
        c.glow(eye, (255, 110, 20), 1.6, blur=2.5)
        for i in range(5):                                  # brasas nas fendas do respiro
            ex = cx + (i - 2) * T * 0.05
            c.glow(c.mask_rect(ex - T * 0.008, vy0 + 2, ex + T * 0.008, vy1 - 2), (255, 90, 20), 0.8, blur=1.5)
        return c
    _base_ring(c, cx, cy, T * 0.41, accent)
    # quatro pes abertos (ref. 3) desenhados sobre o anel
    for k in range(4):
        a = math.radians(45 + 90 * k)
        fx, fy = cx + math.cos(a) * T * 0.33, cy + math.sin(a) * T * 0.33
        foot = [(fx - T * 0.035, fy - T * 0.08), (fx + T * 0.035, fy - T * 0.08), (fx + T * 0.05, fy + T * 0.07),
                (fx - T * 0.05, fy + T * 0.07)]
        _plate(c, c.mask_poly(_rot_pts(foot, fx, fy, a + math.pi / 2)), GUNMETAL, 0.4, 1)
    # corpo traseiro: escotilha do carregador e baia de respiro
    body = _octagon(cx - T * 0.2, cy - T * 0.02, cx + T * 0.2, cy + T * 0.36, T * 0.06)
    _plate(c, c.mask_poly(body), STEEL, 0.55, 2.5, gradient=(METAL_LIGHT, METAL_DARK))
    c.fill(c.mask_rect(cx - T * 0.1, cy + T * 0.17, cx + T * 0.1, cy + T * 0.25, r=2), shade(STEEL, 0.9), height=0.6,
           bevel=1)
    c.groove([(cx - T * 0.09, cy + T * 0.21), (cx + T * 0.09, cy + T * 0.21)], 0.8, 0.05, shade(METAL, 0.5))
    _vent_bay(c, cx - T * 0.13, cx + T * 0.13, vy0, vy1, 5, accent, lamps_on)
    # glacis frontal entre os casulos (protege a cupula)
    gl = _octagon(cx - T * 0.16, cy - T * 0.36, cx + T * 0.16, cy - T * 0.06, T * 0.07)
    _plate(c, c.mask_poly(gl), shade(STEEL, 0.95), 0.58, 2, gradient=(METAL_LIGHT, METAL))
    c.groove([(cx - T * 0.12, cy - T * 0.27), (cx + T * 0.12, cy - T * 0.27)], 0.8, 0.05, shade(METAL, 0.5))
    _rivet_row(c, cx - T * 0.12, cy - T * 0.32, cx + T * 0.12, cy - T * 0.32, 5)
    # bracos entre a cupula e os casulos
    for (x0, x1, y0, y1) in pods:
        side = -1 if (x0 + x1) / 2 < cx else 1
        ax0, ax1 = sorted([cx, (x0 + x1) / 2])
        ay = (y0 + y1) / 2 + pad_y * 0.6
        _plate(c, c.mask_rect(ax0, ay - T * 0.035, ax1, ay + T * 0.035, r=2), GUNMETAL, 0.5, 1)
        c.groove([(ax0 + 3, ay), (ax1 - 3, ay)], 0.7, 0.04, shade(METAL, 0.5))
        del side
    # casulos: corpo inclinado atras da face + face octogonal com os tubos
    for (x0, x1, y0, y1) in pods:
        fx0, fx1, fy0, fy1 = x0 - pad_x, x1 + pad_x, y0 - pad_y, y1 + pad_y
        ch = min(fx1 - fx0, fy1 - fy0) * 0.3
        tail = _octagon(fx0 + T * 0.012, fy0 + T * 0.06, fx1 - T * 0.012, fy1 + T * 0.13, ch)
        _plate(c, c.mask_poly(tail), shade(STEEL, 0.85), 0.55, 2, gradient=(METAL, METAL_DARK))
        face = _octagon(fx0, fy0, fx1, fy1, ch)
        _plate(c, c.mask_poly(face), STEEL, 0.66, 2, gradient=(METAL_LIGHT, METAL))
        inner = _octagon(fx0 + 2.5, fy0 + 2.5, fx1 - 2.5, fy1 - 2.5, ch * 0.85)
        c.fill(c.mask_poly(inner), GUNMETAL, height=0.5, bevel=1.0, mode="set")
        # garras na frente, do lado de fora
        out_x = fx0 if (fx0 + fx1) / 2 < cx else fx1
        sgn = -1 if out_x == fx0 else 1
        reach = max(1.5, min(T * 0.035, (out_x if sgn < 0 else T - out_x) - 2))   # nunca sai do quadro
        claw = [(out_x - sgn * 2, fy0 + ch * 0.2), (out_x + sgn * reach, fy0 - T * 0.01),
                (out_x + sgn * reach * 0.8, fy0 + ch * 1.4), (out_x - sgn * 2, fy1 - ch * 0.4)]
        _plate(c, c.mask_poly(claw), shade(STEEL, 1.1), 0.72, 1.2, gradient=(METAL_LIGHT, METAL))
    _tube_holes(c, T, units, r, ry)
    # cupula blindada com o olho sensor
    c.fill(c.mask_ellipse(cx, dome_y, dome_r * 1.08), METAL_DARK, height=0.6, bevel=1.5)
    c.fill(c.mask_ellipse(cx, dome_y, dome_r), STEEL, height=0.9, bevel=dome_r * 0.6,
           gradient=(WHITE, METAL))
    c.fill(c.mask_rect(cx - dome_r * 0.62, dome_y - dome_r * 0.78, cx + dome_r * 0.62, dome_y - dome_r * 0.44, r=2),
           BLACK, height=0.75, bevel=0.4, mode="set")
    c.fill(eye, shade(accent, 0.5), height=0.78, bevel=0.2)
    if lamps_on:
        c.glow(eye, accent, 0.9, blur=1.6)
    _rivet_row(c, cx - dome_r * 0.7, dome_y + dome_r * 0.55, cx + dome_r * 0.7, dome_y + dome_r * 0.55, 5)
    return c


def launcher_quad_canvas(T, units, tube_r, pitch_deg, accent, lamps_on=True, oc_glow=False):
    """Mula-sem-Cabeca: corpo largo e baixo SEM cabeca, um colar blindado aberto com um recesso de brasa muito
    fraca no lugar da cabeca, quatro casulos retangulares (face 3x4) em bracos hidraulicos, garras na raiz dos
    casulos, saia blindada sobre o anel e baia de respiro traseira com 6 pips. oc_glow=True devolve so o
    brilho de overclock (recesso do colar e respiros dos casulos em brasa)."""
    c = Canvas(T, T)
    cx = cy = T / 2
    _tubes, r, ry, *_ = _tube_extent(T, units, tube_r, pitch_deg)
    pods = _pods_px(T, units)
    pad_x, pad_y = r * 1.7, ry * 2.6
    col_y, col_r = cy + T * 0.05, T * 0.085
    recess = c.mask_ellipse(cx, col_y, col_r * 0.62, col_r * 0.55)
    pod_vents = []
    for (x0, x1, y0, y1) in pods:
        vy = y1 + pad_y + T * 0.07
        pod_vents.append(c.mask_rect((x0 + x1) / 2 - T * 0.035, vy, (x0 + x1) / 2 + T * 0.035, vy + T * 0.012, r=1))
    if oc_glow:
        c.glow(c.mask_ellipse(cx, col_y, col_r * 0.32, col_r * 0.28), (255, 100, 20), 1.6, blur=col_r * 0.25)
        for m in pod_vents:
            c.glow(m, (255, 110, 30), 1.0, blur=1.8)
        return c
    _base_ring(c, cx, cy, T * 0.415, accent)
    # saia blindada sobre o anel + corpo largo e baixo
    skirt = _octagon(cx - T * 0.44, cy - T * 0.06, cx + T * 0.44, cy + T * 0.36, T * 0.09)
    _plate(c, c.mask_poly(skirt), shade(STEEL, 0.8), 0.45, 2.5, gradient=(METAL, METAL_DARK))
    body = _octagon(cx - T * 0.40, cy - T * 0.02, cx + T * 0.40, cy + T * 0.30, T * 0.07)
    _plate(c, c.mask_poly(body), STEEL, 0.6, 3, gradient=(METAL_LIGHT, METAL_DARK))
    _panel_lines(c, cx - T * 0.38, cy, cx + T * 0.38, cy + T * 0.28, nx=4, ny=1)
    # escotilhas dos carregadores das familias e rebites do corpo
    for sx in (-1, 1):
        hx = cx + sx * T * 0.25
        c.fill(c.mask_rect(hx - T * 0.075, cy + T * 0.17, hx + T * 0.075, cy + T * 0.27, r=2.5), shade(STEEL, 0.92),
               height=0.66, bevel=1.2, gradient=(METAL_LIGHT, METAL))
        c.groove([(hx - T * 0.06, cy + T * 0.22), (hx + T * 0.06, cy + T * 0.22)], 0.8, 0.05, shade(METAL, 0.5))
        c.hazard(hx - T * 0.06, cy + T * 0.245, hx + T * 0.06, cy + T * 0.258, (220, 170, 40), BLACK, 5, height=0.68)
    _rivet_row(c, cx - T * 0.37, cy + T * 0.29, cx + T * 0.37, cy + T * 0.29, 12)
    _vent_bay(c, cx - T * 0.17, cx + T * 0.17, cy + T * 0.31, cy + T * 0.355, 6, accent, lamps_on, slats=8)
    # bracos hidraulicos (dois pistoes por casulo) e casulos
    for (x0, x1, y0, y1) in pods:
        fx0, fx1, fy0, fy1 = x0 - pad_x, x1 + pad_x, y0 - pad_y, y1 + pad_y
        mx = (fx0 + fx1) / 2
        for dx in (-0.25, 0.25):
            px = mx + dx * (fx1 - fx0)
            _plate(c, c.mask_rect(px - T * 0.011, fy1, px + T * 0.011, cy + T * 0.08, r=1), METAL_LIGHT, 0.62, 0.6)
            _plate(c, c.mask_rect(px - T * 0.017, fy1 + T * 0.09, px + T * 0.017, cy + T * 0.08, r=1.5), GUNMETAL,
                   0.64, 0.8)
        tail = [(fx0 + 2, fy0 + T * 0.04), (fx1 - 2, fy0 + T * 0.04), (fx1 - 3, fy1 + T * 0.09),
                (fx0 + 3, fy1 + T * 0.09)]
        _plate(c, c.mask_poly(tail), shade(STEEL, 0.85), 0.58, 2, gradient=(METAL, METAL_DARK))
        _plate(c, c.mask_rect(fx0, fy0, fx1, fy1, r=T * 0.012), STEEL, 0.7, 2, gradient=(METAL_LIGHT, METAL))
        c.fill(c.mask_rect(fx0 + 2.5, fy0 + 2.5, fx1 - 2.5, fy1 - 2.5, r=T * 0.008), GUNMETAL, height=0.55, bevel=1.0,
               mode="set")
        # garras na raiz do casulo
        for sgn, ex in ((-1, fx0), (1, fx1)):
            claw = [(ex, fy1 - T * 0.03), (ex + sgn * T * 0.022, fy1 + T * 0.01), (ex + sgn * T * 0.012, fy1 + T * 0.06),
                    (ex, fy1 + T * 0.04)]
            _plate(c, c.mask_poly(claw), shade(STEEL, 1.12), 0.74, 1, gradient=(METAL_LIGHT, METAL))
    for m in pod_vents:
        c.fill(m, BLACK, height=0.62, bevel=0.3, mode="set")
    _tube_holes(c, T, units, r, ry)
    # colar aberto (o "pescoco") com um recesso de brasa muito fraca: quase nada de area emissiva
    c.fill(c.mask_ellipse(cx, col_y, col_r * 1.15), METAL_DARK, height=0.66, bevel=1.5)
    c.fill(c.mask_ellipse(cx, col_y, col_r), shade(STEEL, 1.05), height=0.82, bevel=col_r * 0.35,
           gradient=(WHITE, METAL))
    c.fill(c.mask_ellipse(cx, col_y, col_r * 0.66, col_r * 0.6), BLACK, height=0.4, bevel=1.0, mode="set")
    # brasa muito fraca (STYLE.md 1.6: orcamento emissivo): so cor escura, sem halo
    c.fill(recess, (52, 24, 16) if lamps_on else (34, 22, 18), height=0.38, bevel=0.6)
    if lamps_on:
        c.fill(c.mask_ellipse(cx, col_y + col_r * 0.08, col_r * 0.3, col_r * 0.22), (96, 38, 18), height=0.36, bevel=0.6)
    n = 10
    for k in range(n):
        a = k / n * math.tau
        c.rivet(cx + math.cos(a) * col_r * 0.86, col_y + math.sin(a) * col_r * 0.86, 1.0, METAL_LIGHT, 0.06)
    return c


_POD_CANVAS = {"box": None, "twin": launcher_twin_canvas, "quad": launcher_quad_canvas}


def render_launcher_oc_glow(ts_tiles, units, tube_r, pitch_deg, accent, style):
    """turret_oc.png: so o brilho do overclock (camada roof_turrets, ligada por IsOverclocked)."""
    fn = _POD_CANVAS.get(style)
    if not fn:
        return None
    T = int(round(ts_tiles * PX))
    return fn(T, units, tube_r, pitch_deg, accent, oc_glow=True).render(bake=False)


def render_launcher_pod(ts_tiles, units, tube_r, pitch_deg, accent, style="box"):
    T = int(round(ts_tiles * PX))
    fn = _POD_CANVAS.get(style) or launcher_pod_canvas
    on = fn(T, units, tube_r, pitch_deg, accent, lamps_on=True)
    off = fn(T, units, tube_r, pitch_deg, accent, lamps_on=False)
    img_on = drop_shadow(on.render(), 2, 45)
    img_off = drop_shadow(off.render(), 2, 45)
    off_arr = np.asarray(img_off, dtype=np.float32)
    off_arr[..., :3] *= 0.86
    img_off = Image.fromarray(np.clip(off_arr, 0, 255).astype(np.uint8), "RGBA")
    nrm = on.final_normals()
    shadow = silhouette_shadow(img_on, (T, T), blur=max(3, T // 40), alpha=120)
    return img_on, img_off, nrm, shadow


def _nose_big(c, T, u, pitch_deg, band, form):
    """Nariz de uma unidade "heavy" (missil de calibre duplo deitado na fileira) ou "torpedo" (ogiva grande
    tampada cobrindo a face do casulo), no retangulo u["box"] (tiles) centrado na unidade."""
    x, y = _tp(T, *u["pos"])
    bw, bh = u["box"][0] * PX, u["box"][1] * PX
    k = max(0.35, math.sin(math.radians(pitch_deg)))
    if form == "heavy":
        w2, h2 = bw * 0.48, bh * 0.42
        c.fill(c.mask_rect(x - w2, y - h2, x + w2, y + h2, r=h2), shade(band, 0.95), height=0.62, bevel=0.5)
        c.fill(c.mask_rect(x - w2 * 0.86, y - h2 * 0.78, x + w2 * 0.5, y + h2 * 0.78, r=h2 * 0.78), (196, 200, 206),
               height=0.76, bevel=0.6, gradient=((236, 238, 240), (150, 154, 160)))
        c.fill(c.mask_ellipse(x - w2 * 0.86, y, h2 * 0.8, h2 * 0.78), (226, 228, 232), height=0.82, bevel=0.4)
        c.fill(c.mask_ellipse(x - w2 * 0.88, y - h2 * 0.25, h2 * 0.28, h2 * 0.22), (250, 250, 250), height=0.86,
               bevel=0.2)
        return
    rx, rr = bw * 0.44, bh * 0.44 * (0.75 + 0.25 * k)
    c.fill(c.mask_ellipse(x, y, rx * 1.06, rr * 1.06), METAL_DARK, height=0.55, bevel=0.6)
    c.fill(c.mask_ellipse(x, y, rx, rr), shade(band, 0.92), height=0.66, bevel=0.8)
    c.fill(c.mask_ellipse(x, y - rr * 0.08, rx * 0.8, rr * 0.8), (206, 210, 214), height=0.8, bevel=rx * 0.25,
           gradient=((240, 242, 244), (150, 154, 160)))
    c.fill(c.mask_ellipse(x, y - rr * 0.08, rx * 0.36, rr * 0.36), shade(band, 1.0), height=0.86, bevel=0.6)
    c.fill(c.mask_ellipse(x - rx * 0.22, y - rr * 0.38, rx * 0.16, rr * 0.13), (250, 250, 250), height=0.9, bevel=0.2)


def render_launcher_cells(ts_tiles, units, loaded, tube_r, pitch_deg, band):
    """Sobreposicao de um nivel do rack: narizes (cone claro + anel na cor do tipo) nas unidades `loaded`.
    Unidades "heavy"/"torpedo" (layout heavy16 / torpedo*) ganham um nariz unico do tamanho de u["box"]."""
    T = int(round(ts_tiles * PX))
    c = Canvas(T, T)
    _tubes, r, ry, *_ = _tube_extent(T, units, tube_r, pitch_deg)
    for u in loaded:
        if u.get("form") in ("heavy", "torpedo"):
            _nose_big(c, T, u, pitch_deg, band, u["form"])
            continue
        for (fwd, lat) in u["tubes"]:
            x, y = _tp(T, fwd, lat)
            c.fill(c.mask_ellipse(x, y, r * 0.98, ry * 1.02), shade(band, 0.95), height=0.62, bevel=0.4)
            c.fill(c.mask_ellipse(x, y - ry * 0.12, r * 0.72, ry * 0.74), (196, 200, 206), height=0.78, bevel=0.5,
                   gradient=((236, 238, 240), (150, 154, 160)))
            c.fill(c.mask_ellipse(x - r * 0.18, y - ry * 0.32, r * 0.24, ry * 0.26), (250, 250, 250), height=0.82,
                   bevel=0.2)
    return c.render(), c.final_normals()


def render_launcher_shutters(ts_tiles, shutters):
    """Persianas fechadas (casulos sem celula no modo, ex.: Iara nos casulos externos), no quadro da torre."""
    T = int(round(ts_tiles * PX))
    c = Canvas(T, T)
    for sh in shutters:
        x, y = _tp(T, *sh["center"])
        w2, h2 = sh["box"][0] * PX * 0.56, sh["box"][1] * PX * 0.56
        c.fill(c.mask_rect(x - w2, y - h2, x + w2, y + h2, r=2), GUNMETAL, height=0.72, bevel=1.2,
               gradient=((92, 96, 104), (40, 42, 48)))
        n = max(3, int(h2 * 2 / 5))
        for i in range(1, n):
            yy = y - h2 + 2 * h2 * i / n
            c.groove([(x - w2 + 2, yy), (x + w2 - 2, yy)], 0.9, 0.06, (24, 24, 26))
        c.hazard(x - w2 + 2, y + h2 - 4, x + w2 - 2, y + h2 - 1.5, (220, 170, 40), BLACK, 5, height=0.74)
    return c.render(), c.final_normals()


def compose_launcher(w, h, roof, pod, cells, pivot):
    """Icone: teto pintado + casulo + celulas cheias (frente para cima)."""
    img = Image.new("RGBA", (w * PX, h * PX), (0, 0, 0, 0))
    img.alpha_composite(paint_roof_preview(roof))
    T = pod.size[0]
    x, y = int(round(pivot[0] * PX - T / 2)), int(round(pivot[1] * PX - T / 2))
    for im in (pod, cells):
        if im is None:
            continue
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        layer.paste(im, (x, y), im)
        img = Image.alpha_composite(img, layer)
    return img


def render_missile_icon(kind, accent):
    """Icone do seletor bs_missile_type (64x64): missil na diagonal + sinal do tipo."""
    c = Canvas(64, 64)
    c.fill(c.mask_ellipse(32, 32, 29), (34, 36, 42), height=0.4, bevel=2)
    c.fill(c.mask_ellipse(32, 32, 25), shade(accent, 0.32), height=0.45, bevel=1)

    def missile(x0, y0, x1, y1, wid, body=(196, 200, 206), band=accent):
        ang = math.atan2(y1 - y0, x1 - x0)
        nx, ny = -math.sin(ang) * wid / 2, math.cos(ang) * wid / 2
        tip = (x1 + math.cos(ang) * wid * 0.9, y1 + math.sin(ang) * wid * 0.9)
        c.fill(c.mask_poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), tip, (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]), body,
               height=0.72, bevel=0.8, gradient=((236, 238, 240), (130, 134, 140)))
        bx, by = x0 + (x1 - x0) * 0.62, y0 + (y1 - y0) * 0.62
        bx2, by2 = x0 + (x1 - x0) * 0.74, y0 + (y1 - y0) * 0.74
        c.fill(c.mask_poly([(bx + nx * 1.05, by + ny * 1.05), (bx2 + nx * 1.05, by2 + ny * 1.05),
                            (bx2 - nx * 1.05, by2 - ny * 1.05), (bx - nx * 1.05, by - ny * 1.05)]), band, height=0.74,
               bevel=0.3)
        for s in (-1, 1):
            c.fill(c.mask_poly([(x0 + s * nx * 0.2, y0 + s * ny * 0.2), (x0 + s * nx * 2.2 - (x1 - x0) * 0.05,
                                 y0 + s * ny * 2.2 - (y1 - y0) * 0.05), (x0 + (x1 - x0) * 0.18 + s * nx,
                                                                         y0 + (y1 - y0) * 0.18 + s * ny)]),
                   (120, 124, 130), height=0.7, bevel=0.3)
        fl = c.mask_ellipse(x0 - (x1 - x0) * 0.08, y0 - (y1 - y0) * 0.08, wid * 0.45)
        c.glow(fl, (255, 160, 60), 0.8, blur=1.5)

    if kind == "he":
        missile(17, 47, 41, 23, 9)
    elif kind == "cluster":
        missile(14, 50, 30, 34, 8)
        for (x, y) in ((40, 18), (46, 28), (34, 14)):
            missile(x - 5, y + 5, x, y, 4)
    elif kind == "limpet":
        missile(15, 49, 36, 28, 9)
        b = c.mask_ellipse(44, 20, 5)
        c.fill(b, (200, 40, 30), height=0.8, bevel=0.5)
        c.glow(b, (255, 40, 30), 1.0, blur=2.5)
    elif kind == "napalm":
        missile(15, 49, 34, 30, 9)
        fl = c.mask_poly([(42, 14), (48, 26), (45, 34), (38, 36), (34, 28), (38, 22)])
        c.fill(fl, (255, 120, 30), height=0.75, bevel=0.6)
        c.glow(fl, (255, 90, 20), 0.9, blur=2.5)
    elif kind == "emp":
        missile(14, 50, 32, 32, 9)
        bolt = c.mask_poly([(45, 10), (36, 26), (42, 26), (37, 40), (50, 22), (44, 22)])
        c.fill(bolt, (150, 200, 255), height=0.78, bevel=0.6)
        c.glow(bolt, (80, 150, 255), 0.8, blur=2.5)
    elif kind == "torpedo":
        missile(14, 46, 40, 24, 14, body=(170, 176, 184))
        for (x, y) in ((46, 40), (50, 33)):
            d = c.mask_ellipse(x, y, 3)
            c.fill(d, (230, 230, 230), height=0.7, bevel=0.3)
            c.glow(d, accent, 0.6, blur=2)
    elif kind == "nuclear":
        missile(14, 50, 34, 30, 11, body=(170, 180, 160))
        rr = 8
        ex, ey = 43, 21
        c.fill(c.mask_ellipse(ex, ey, rr * 1.15), (230, 200, 40), height=0.8, bevel=0.6)
        tre = Image.new("L", (c.W, c.H), 0)
        d = ImageDraw.Draw(tre)
        for k in range(3):
            a0 = -90 + k * 120 - 30
            d.pieslice(c.box(ex - rr, ey - rr, ex + rr, ey + rr), a0, a0 + 60, fill=255)
        d.ellipse(c.box(ex - rr * 0.2, ey - rr * 0.2, ex + rr * 0.2, ey + rr * 0.2), fill=255)
        c.fill(tre, BLACK, height=0.82, bevel=0.2)
    else:
        raise ValueError(kind)
    return c.render()
