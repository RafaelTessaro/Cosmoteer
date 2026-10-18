"""Kit compartilhado dos modelos 3D do Bullet Strike: paleta, materiais e pecas comuns (casco, piso).

Linguagem visual aprovada (canhao naval 76 mm, ver tools/blender/STYLE.md): nucleo mecanico escuro +
placas de blindagem claras e angulares por cima, com vaos onde o nucleo aparece; "garras" que envolvem
a raiz do cano; espinha central com sensor; baia de exaustao traseira com luzes; canos longos com canal
escuro, colares e freio de boca. Brilhos pequenos e poucos.

Coordenadas: origem no pivo da torre, +X = direita, +Y = frente (direcao do cano), +Z = para cima,
unidades = tiles. Cada arma fica em tools/blender/parts/<id>.py.
"""

import math

import bs3d as B

# paleta (valores lineares do Blender)
ARMOR = (0.52, 0.535, 0.55)        # cinza naval claro
ARMOR_MID = (0.20, 0.205, 0.215)
CORE = (0.016, 0.017, 0.02)
CORE_MID = (0.045, 0.046, 0.05)
STEEL = (0.30, 0.31, 0.33)
AMBER = (1.0, 0.42, 0.04)
CYAN = (0.15, 0.85, 1.0)           # plasma
GREEN = (0.40, 1.0, 0.18)          # nuclear
BLUE = (0.25, 0.50, 1.0)           # EMP / radar
RED = (1.0, 0.10, 0.06)            # alerta / radar
ACCENTS = {"amber": AMBER, "cyan": CYAN, "green": GREEN, "blue": BLUE, "red": RED}


def mats(accent=AMBER):
    """Materiais padrao. accent = cor das luzes (tupla RGB ou nome em ACCENTS)."""
    if isinstance(accent, str):
        accent = ACCENTS[accent]
    return {
        "armor": B.mat_paint("armor", ARMOR, rough=0.32, metal=0.25, wear=0.25, grime=0.06, scale=4),
        "armor_mid": B.mat_paint("armor_mid", ARMOR_MID, rough=0.38, metal=0.35, wear=0.3, grime=0.1),
        "core": B.mat_metal("core", CORE, rough=0.45, metal=0.7),
        "core_mid": B.mat_metal("core_mid", CORE_MID, rough=0.35, metal=0.85),
        "steel": B.mat_metal("steel", STEEL, rough=0.28, metal=0.95),
        "black": B.mat_metal("black", (0.004, 0.004, 0.005), rough=0.6, metal=0.2),
        "glow": B.mat_glow("glow", accent, 9.0),
        "glow_dim": B.mat_glow("glow_dim", accent, 3.0),
        "lens": B.mat_glow("lens", (1.0, 0.18, 0.05), 6.0),
        "ember": B.mat_glow("ember", (1.0, 0.16, 0.02), 0.35),
        "red": B.mat_glow("red_led", RED, 6.0),
        "screen": B.mat_glow("screen", (0.25, 0.65, 1.0), 6.0),
    }


def mirror(poly):
    return [(-x, y) for x, y in reversed(poly)]


# ============================================================================ 76 mm naval
def slot_with_pips(name, x, y0, y1, w, ztop, n, M, tags, target=None, depth=0.05, vertical=True):
    """Fenda escura (recortada no alvo, se houver) com uma fileira de n pips ambar no fundo."""
    cx, cy = (x, (y0 + y1) / 2) if vertical else ((y0 + y1) / 2, x)
    sx, sy = (w, abs(y1 - y0)) if vertical else (abs(y1 - y0), w)
    for t in (target if isinstance(target, (list, tuple)) else [target]):
        if t is not None:
            c = B.box(name + "_cut", cx, cy, sx, sy, ztop - depth, ztop + 0.2, M["black"], bevel=0.0)
            B.cut(t, [c])
    B.box(name + "_bed", cx, cy, sx, sy, ztop - depth - 0.01, ztop - depth + 0.004, M["black"], bevel=0.0, tags=tags)
    L = abs(y1 - y0)
    for i in range(n):
        t = (i + 0.5) / n
        px, py = (x, min(y0, y1) + t * L) if vertical else (min(y0, y1) + t * L, x)
        B.box(f"{name}_pip{i}", px, py, (w * 0.55) if vertical else L / n * 0.55, (L / n * 0.55) if vertical else w * 0.55,
              ztop - depth, ztop - depth + 0.012, M["glow"], bevel=0.0, tags=tags)


def hull_roof(M, w, h, pivot, ring_r, T="roof"):
    """Teto da peca (verde = pintura da nave) em coordenadas centradas na peca."""
    tags = (T,)
    green = B.mat_roof_green()
    px, py = pivot[0] - w / 2, h / 2 - pivot[1]
    gap = 0.03
    B.box("deck_under", 0, 0, w, h, -0.05, 0.02, M["core"], bevel=0.0, tags=tags)
    # placas do convés: uma por tile, cantos chanfrados e painel interno (bisel duplo)
    for tx in range(w):
        for ty in range(h):
            cx, cy = tx + 0.5 - w / 2, h / 2 - ty - 0.5
            poly = B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
            _, pnl = B.shard(f"deck{tx}_{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02,
                             tags=tags)
            # linha de painel diagonal em placas alternadas
            if (tx + ty) % 2 == 0 and pnl is not None:
                B.cut(pnl, [B.rbox(f"dl{tx}{ty}", cx + 0.18, cy - 0.18, 0.012, 0.5, 0.07, 0.2, M["core"], rot=45,
                                   bevel=0.0)])
    # anel da torre (sem pintura): colar escuro com parafusos
    B.torus("ringbear", px, py, 0.08, ring_r + 0.02, 0.055, M["core_mid"], tags=tags)
    B.cyl("ringhole", px, py, 0.05, ring_r - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    # parafusos do anel: so os que ficam dentro da peca (pecas estreitas)
    pts = [(x, y) for x, y in B.ring_points(px, py, ring_r + 0.11, 32)
           if abs(x) < w / 2 - 0.06 and abs(y) < h / 2 - 0.06]
    B.bolts("rb", pts, 0.1, 0.022, M["steel"], tags=tags)
    if h < 2:
        return  # peca de 1 fileira: nao sobra fileira de tras livre
    # fileira de tras: escotilha no meio (pecas com 3+ de largura) e respiros com luz nos tiles das pontas
    hy = -h / 2 + 0.5
    if w >= 3:
        hatch = B.rpoly(0, hy, 0.62, 0.62, 0, chamfer=0.12)
        B.plate("hatch", hatch, 0.06, 0.10, M["armor_mid"], slope=0.02, tags=tags)
        B.box("hatch_h", 0, hy - 0.16, 0.26, 0.05, 0.10, 0.13, M["steel"], bevel=0.01, tags=tags)
    vents = [0.0] if w == 1 else [sx * (w / 2 - 0.5) for sx in (-1, 1)]
    for k, cx in enumerate(vents):
        v = B.box(f"hvent{k}", cx, hy, 0.56, 0.34, 0.05, 0.11, M["core_mid"], bevel=0.01, slope=0.015, tags=tags)
        B.cut(v, [B.box(f"hvc{k}{i}", cx, hy - 0.11 + i * 0.075, 0.46, 0.03, 0.09, 0.2, M["core"], bevel=0.0)
                  for i in range(4)])
        B.box(f"hled{k}", cx, hy + 0.23, 0.14, 0.03, 0.06, 0.09, M["glow_dim"], bevel=0.0, tags=tags)


def hull_floor(M, w, h, pivot, ring_r, crew, T="floor"):
    tags = (T,)
    px, py = pivot[0] - w / 2, h / 2 - pivot[1]
    B.box("fl_base", 0, 0, w, h, -0.05, 0.0, M["core"], bevel=0.0, tags=tags)
    for tx in range(w):
        for ty in range(h):
            x0, y1 = tx - w / 2 + 0.04, h / 2 - ty - 0.04
            B.box(f"fl{tx}{ty}", x0 + 0.46, y1 - 0.46, 0.92, 0.92, 0.0, 0.03, M["core_mid"], bevel=0.01, tags=tags)
    # anel giratorio com setas
    B.torus("fl_ring", px, py, 0.05, ring_r * 0.85, 0.05, M["armor_mid"], tags=tags)
    B.cyl("fl_hub", px, py, 0.05, ring_r * 0.32, 0.08, M["armor"], axis="Z", verts=48, tags=tags)
    for k in range(4):
        a = k * math.pi / 2
        cx, cy = px + math.cos(a) * ring_r * 0.6, py + math.sin(a) * ring_r * 0.6
        B.box(f"fl_chev{k}", cx, cy, 0.16, 0.16, 0.05, 0.08, M["armor"], bevel=0.01, tags=tags)
    B.box("fl_led_t", px, py + ring_r * 0.95, 0.3, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    B.box("fl_led_b", px, py - ring_r * 0.95, 0.3, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # estantes de carregadores na fileira de tras + estacoes da tripulacao
    for tx in range(w):
        x = tx - w / 2 + 0.5
        B.box(f"rack{tx}", x, -h / 2 + 0.22, 0.78, 0.26, 0.0, 0.16, M["armor_mid"], bevel=0.01, tags=tags)
        for i in range(3):
            B.box(f"mag{tx}{i}", x - 0.24 + i * 0.24, -h / 2 + 0.22, 0.16, 0.18, 0.16, 0.24, M["core_mid"],
                  bevel=0.01, tags=tags)
            B.box(f"magled{tx}{i}", x - 0.24 + i * 0.24, -h / 2 + 0.22, 0.10, 0.03, 0.24, 0.26, M["glow_dim"],
                  bevel=0.0, tags=tags)
    for i, (cx, cy, _r) in enumerate(crew):
        x, y = cx - w / 2, h / 2 - cy
        B.box(f"seat{i}", x, y + 0.02, 0.32, 0.30, 0.0, 0.14, M["armor"], bevel=0.04, tags=tags)
        B.box(f"console{i}", x, y + 0.30, 0.42, 0.12, 0.0, 0.22, M["core_mid"], bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.30, 0.32, 0.06, 0.22, 0.24, M["screen"],
              bevel=0.0, tags=tags)
