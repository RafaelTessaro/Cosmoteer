"""Modelos 3D das armas do Bullet Strike (gerados por codigo no Blender).

Linguagem visual (ver docs de estilo): nucleo mecanico escuro + placas de blindagem claras e
angulares por cima, com vaos onde o nucleo aparece; "garras" que envolvem a raiz do cano;
espinha central com sensor; baia de exaustao traseira com luzes ambar; canos longos com canal
escuro, colares e freio de boca. Brilhos pequenos e poucos.

Coordenadas: origem no pivo da torre, +Y = frente (direcao do cano), unidades = tiles.
Cada funcao build_* monta a cena e devolve a geometria usada pelas regras do jogo.
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


def mats(accent=AMBER):
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
    }


def mirror(poly):
    return [(-x, y) for x, y in reversed(poly)]


# ============================================================================ 76 mm naval
def _slot_with_pips(name, x, y0, y1, w, ztop, n, M, tags, target=None, depth=0.05, vertical=True):
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


def naval_76_head(M, T="head"):
    """Cabeca da torre: casco facetado em ponta de flecha, garras que avancam ate o cano."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    # anel giratorio e nucleo escuro (octogono chanfrado)
    B.cyl("ring", 0, 0, 0.04, 1.32, 0.08, KM, axis="Z", verts=72, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, 1.25, 24, 0.13), 0.09, 0.022, S, tags=tags)
    core = [(-1.10, -1.14), (1.10, -1.14), (1.26, -0.98), (1.26, 0.46), (0.70, 1.02), (-0.70, 1.02),
            (-1.26, 0.46), (-1.26, -0.98)]
    B.plate("core", core, 0.06, 0.34, K, slope=0.05, tags=tags)

    # garras: ombreira lateral + lamina que avanca em ponta ate o lado do cano (com vao entre as duas)
    pauldron = [(-0.62, -1.04), (-1.08, -1.04), (-1.30, -0.82), (-1.30, -0.34), (-1.42, -0.22), (-1.42, 0.24),
                (-1.26, 0.40), (-0.74, 0.56), (-0.70, -0.36), (-0.60, -0.48)]
    blade = [(-1.26, 0.53), (-0.80, 0.69), (-0.48, 0.95), (-0.34, 1.15), (-0.40, 1.29), (-0.64, 1.21), (-1.02, 0.90)]
    fin = [(-0.84, -0.94), (-1.10, -0.94), (-1.22, -0.80), (-1.22, -0.18), (-1.06, 0.00), (-0.86, -0.06)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, mirror)):
        _, pnl = B.shard(f"claw_{side}", f(pauldron), 0.30, 0.70, A, slope=0.11, groove=0.045, panel_h=0.035,
                         tags=tags)
        # linhas de painel recortadas na ombreira
        cuts = [B.rbox(f"pl{side}{i}", sx * x, y, 0.016, ln, 0.715, 0.9, K, rot=r, bevel=0.0)
                for i, (x, y, ln, r) in enumerate(((0.80, 0.20, 0.50, 0), (1.02, 0.36, 0.30, sx * 72)))]
        B.cut(pnl, cuts)
        ba, bpnl = B.shard(f"blade_{side}", f(blade), 0.30, 0.66, A, slope=0.08, groove=0.03, panel_h=0.03, tags=tags)
        # fenda com luz na lamina
        for t in (ba, bpnl):
            B.cut(t, [B.rbox(f"bcut{side}", sx * 0.80, 0.90, 0.30, 0.05, 0.62, 0.9, K, rot=sx * -38, bevel=0.0)])
        B.rbox(f"bbed{side}", sx * 0.80, 0.90, 0.30, 0.05, 0.60, 0.625, M["black"], rot=sx * -38, bevel=0.0,
               tags=tags)
        B.rbox(f"bglow{side}", sx * 0.80, 0.90, 0.22, 0.016, 0.62, 0.632, M["glow_dim"], rot=sx * -38, bevel=0.0,
               tags=tags)
        # aleta traseira em degrau, com fenda de pips recortada
        fa, fpnl = B.shard(f"fin_{side}", f(fin), 0.73, 0.84, A, slope=0.05, groove=0.03, panel_h=0.02, tags=tags)
        _slot_with_pips(f"fslot{side}", sx * 1.04, -0.78, -0.40, 0.065, 0.86, 4, M, tags, target=[fa, fpnl], depth=0.04)
        # pistao hidraulico ligando ombreira e lamina
        B.cyl(f"piston{side}", sx * 0.66, 0.66, 0.42, 0.035, 0.34, S, axis="Y", verts=12, yaw=sx * 50, tags=tags)
        B.cyl(f"pistonb{side}", sx * 0.74, 0.58, 0.42, 0.05, 0.14, KM, axis="Y", verts=12, yaw=sx * 50, tags=tags)

    # mantelete em cunha (de onde sai o cano)
    mant = [(-0.25, 0.56), (0.25, 0.56), (0.31, 0.72), (0.24, 1.20), (-0.24, 1.20), (-0.31, 0.72)]
    m = B.plate("mantlet", mant, 0.30, 0.66, KM, slope=0.06, tags=tags)
    B.cut(m, [B.box("mant_cut", 0, 1.05, 0.22, 0.40, 0.58, 0.9, K, bevel=0.0)])
    for sx in (-1, 1):
        B.cyl(f"recup{sx}", sx * 0.19, 0.90, 0.50, 0.045, 0.50, S, axis="Y", verts=12, tags=tags)
        # calhas de alimentacao: dos tambores ate a culatra
        B.cyl(f"chute{sx}", sx * 0.42, 0.36, 0.44, 0.05, 0.42, KM, axis="Y", verts=8, yaw=sx * -18, tags=tags)
        for i in range(3):
            B.cyl(f"chuter{sx}{i}", sx * (0.47 - i * 0.04), 0.22 + i * 0.12, 0.44, 0.058, 0.025, S, axis="Y",
                  verts=8, yaw=sx * -18, tags=tags)

    # espinha central em seta, com sensor
    spine = [(-0.30, -0.84), (0.30, -0.84), (0.36, -0.74), (0.36, 0.14), (0.15, 0.58), (-0.15, 0.58),
             (-0.36, 0.14), (-0.36, -0.74)]
    B.shard("spine", spine, 0.30, 0.86, A, slope=0.10, groove=0.04, panel_h=0.03, tags=tags)
    spine2 = [(-0.17, -0.50), (0.17, -0.50), (0.20, -0.42), (0.20, 0.10), (0.08, 0.34), (-0.08, 0.34),
              (-0.20, 0.10), (-0.20, -0.42)]
    s2 = B.plate("spine2", spine2, 0.88, 0.98, A, slope=0.035, tags=tags)
    win = [(-0.12, -0.05), (0.12, -0.05), (0.12, 0.07), (0.045, 0.21), (-0.045, 0.21), (-0.12, 0.07)]
    B.cut(s2, [B.loft("win_cut", win, win, 0.94, 1.2, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 0.935, 0.945, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, 0.06, 0.16, 0.03, 0.94, 0.952, M["lens"], bevel=0.0, tags=tags)
    _slot_with_pips("sp", -0.34, -0.12, 0.12, 0.05, 0.98, 3, M, tags, target=s2, depth=0.03, vertical=False)

    # baia de exaustao traseira (persianas + pips)
    B.box("vent_bay", 0, -0.98, 1.00, 0.30, 0.20, 0.36, M["black"], bevel=0.0, tags=tags)
    for i in range(6):
        B.box(f"louver{i}", 0, -1.10 + i * 0.048, 0.96, 0.02, 0.30, 0.37, KM, bevel=0.004, tags=tags)
    for i, x in enumerate((-0.36, -0.22, -0.08, 0.08, 0.22, 0.36)):
        B.box(f"vent_pip{i}", x, -0.86, 0.06, 0.024, 0.34, 0.39, M["glow"], bevel=0.0, tags=tags)

    # carregadores de alimentacao visiveis nos vaos (tambores com contador ambar)
    for sx in (-1, 1):
        x = sx * 0.53
        B.cyl(f"drum{sx}", x, -0.22, 0.44, 0.12, 0.70, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
        for i, y in enumerate((-0.48, -0.22, 0.04)):
            B.cyl(f"drumring{sx}{i}", x, y, 0.44, 0.13, 0.04, S, axis="Y", verts=8, bevel=0.005, tags=tags)
        for i in range(4):
            B.box(f"drumled{sx}{i}", x, -0.40 + i * 0.07, 0.035, 0.035, 0.55, 0.575,
                  M["glow"] if i < 3 else M["black"], bevel=0.0, tags=tags)
        B.box(f"module{sx}", sx * 0.95, -1.04, 0.22, 0.10, 0.30, 0.40, KM, bevel=0.01, tags=tags)
    B.bolts("bolt", [(x, -1.10) for x in (-1.0, -0.66, 0.66, 1.0)], 0.35, 0.026, S, tags=tags)


def naval_76_barrel(M, L=2.6, T="barrel"):
    """Cano com raiz (y=0) e boca (y=L), centrado em x=0, altura z=0.55."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = 0.55
    # luva de recuo (raiz) octogonal
    B.cyl("b_root", 0, 0.16, z, 0.185, 0.32, KM, axis="Y", verts=8, bevel=0.012, tags=tags)
    B.cyl("b_rootcap", 0, 0.33, z, 0.165, 0.04, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    # carenagem de resfriamento com fendas no topo (brilho de calor no fundo)
    y0j, y1j = 0.35, 0.97
    sh = B.cyl("b_shroud", 0, (y0j + y1j) / 2, z, 0.155, y1j - y0j, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
    cuts = [B.box(f"b_shc{i}", 0, 0.44 + i * 0.11, 0.17, 0.05, z + 0.07, z + 0.3, K, bevel=0.0) for i in range(5)]
    B.cut(sh, cuts)
    B.box("b_heat", 0, (y0j + y1j) / 2, 0.15, y1j - y0j - 0.06, z + 0.07, z + 0.08, M["ember"], bevel=0.0,
          tags=tags)
    B.cyl("b_jacket", 0, (y0j + y1j) / 2, z, 0.06, y1j - y0j, K, axis="Y", verts=16, tags=tags)
    # luva principal facetada e afunilada, com canal escuro recortado
    y0, y1 = 0.97, L - 0.40
    sl = B.cyl("b_sleeve", 0, (y0 + y1) / 2, z, 0.14, y1 - y0, A, axis="Y", verts=8, bevel=0.008, tags=tags,
               r2=0.118)
    B.cut(sl, [B.box("b_chc", 0, (y0 + y1) / 2, 0.05, y1 - y0 - 0.12, z + 0.08, z + 0.3, K, bevel=0.0)])
    B.box("b_chbed", 0, (y0 + y1) / 2, 0.05, y1 - y0 - 0.12, z + 0.06, z + 0.09, M["black"], bevel=0.0, tags=tags)
    # extrator de gases (bojo facetado)
    ye = y0 + (y1 - y0) * 0.40
    fume = B.cyl("b_fume", 0, ye, z, 0.165, 0.28, A, axis="Y", verts=8, bevel=0.015, tags=tags)
    B.cut(fume, [B.box("b_fumec", 0, ye, 0.05, 0.36, z + 0.08, z + 0.3, K, bevel=0.0)])
    for sx in (-1, 1):
        B.cyl(f"b_fumecone{sx}", 0, ye + sx * 0.18, z, 0.135 if sx < 0 else 0.165, 0.08, A, axis="Y", verts=8,
              bevel=0.0, tags=tags, r2=0.165 if sx < 0 else 0.13)
    for i, y in enumerate((y0 + 0.04, y1 - 0.04)):
        B.cyl(f"b_collar{i}", 0, y, z, 0.15 - i * 0.02, 0.05, AM, axis="Y", verts=8, bevel=0.008, tags=tags)
    # freio de boca em ponta de flecha com fendas transversais no topo
    yb = L - 0.21
    brake = [(-0.16, yb - 0.21), (0.16, yb - 0.21), (0.20, yb - 0.13), (0.20, yb + 0.08), (0.12, yb + 0.21),
             (-0.12, yb + 0.21), (-0.20, yb + 0.08), (-0.20, yb - 0.13)]
    br = B.plate("b_brake", brake, z - 0.14, z + 0.14, A, slope=0.05, tags=tags)
    bc = [B.box(f"b_bc{i}", 0, yb - 0.11 + i * 0.09, 0.44, 0.04, z + 0.03, z + 0.3, K, bevel=0.0) for i in range(3)]
    bc.append(B.box("b_bore_c", 0, L, 0.11, 0.12, z - 0.06, z + 0.3, K, bevel=0.0))
    B.cut(br, bc)
    B.box("b_brake_core", 0, yb - 0.02, 0.30, 0.30, z - 0.10, z + 0.03, K, bevel=0.0, tags=tags)


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
    B.bolts("rb", B.ring_points(px, py, ring_r + 0.11, 32), 0.1, 0.022, M["steel"], tags=tags)
    # fileira de tras: escotilha da tripulacao no meio, respiros com luz nos cantos
    hy = -h / 2 + 0.5
    hatch = B.rpoly(0, hy, 0.62, 0.62, 0, chamfer=0.12)
    B.plate("hatch", hatch, 0.06, 0.10, M["armor_mid"], slope=0.02, tags=tags)
    B.box("hatch_h", 0, hy - 0.16, 0.26, 0.05, 0.10, 0.13, M["steel"], bevel=0.01, tags=tags)
    for sx in (-1, 1):
        cx = sx * (w / 2 - 0.5)
        v = B.box(f"hvent{sx}", cx, hy, 0.56, 0.34, 0.05, 0.11, M["core_mid"], bevel=0.01, slope=0.015, tags=tags)
        B.cut(v, [B.box(f"hvc{sx}{i}", cx, hy - 0.11 + i * 0.075, 0.46, 0.03, 0.09, 0.2, M["core"], bevel=0.0)
                  for i in range(4)])
        B.box(f"hled{sx}", cx, hy + 0.23, 0.14, 0.03, 0.06, 0.09, M["glow_dim"], bevel=0.0, tags=tags)


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
        B.box(f"screen{i}", x, y + 0.30, 0.32, 0.06, 0.22, 0.24, B.mat_glow("screen", (0.25, 0.65, 1.0), 6),
              bevel=0.0, tags=tags)
