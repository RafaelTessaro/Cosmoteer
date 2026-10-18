"""Canhao de Plasma Pesado ("Curupira") - guardiao da floresta, de pes virados e cabelo de fogo; mesma familia do 76 mm.

Cabeca em ponta de flecha: garras que avancam ate os canos, proa central bifurcada (repete as pontas dos
trilhos), espinha com sensor e a chama do Curupira gravada num rebaixo, ombreiras com fenda de pips e,
atras, uma crista de chamas angulares que varre PARA TRAS ate os cantos (os pes virados / o cabelo de
fogo): duas camadas por lado (3 linguas embaixo, 2 em cima, calco escuro entre elas). Tanques de celulas de plasma
com nivel ciano nos vaos, bobinas de carga pequenas atras deles, dutos ate os bercos, baia de exaustao
traseira com pips ciano. Teto com estante de celulas de plasma (4 baias com celula ciano e nivel).
Dois canos de trilho grossos: banco de capacitores escuro na raiz (copiado no berco da cabeca), dois
pacotes de bobinas claras cortadas por um canal escuro no topo (pips ciano nos vaos), trilhos expostos e pontas
abertas (duas pontas claras facetadas por cano com canal escuro no meio) - so as pontas esquentam.
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_plasma_heavy",
    "kind": "gun",
    "size": [4, 5],
    "pivot": [2.0, 2.1],           # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 3.9,             # lado do quadrado do sprite da torre (as laminas vao ate os cantos)
    "ring_r": 1.74,                # raio do anel da torre no teto/piso
    "accent": "cyan",
    "collider": 1.72,
    "barrels": {
        "ys": [-0.5, 0.5],         # dois canos de trilho lado a lado
        "root": 1.00,              # pivo -> raiz do cano
        "length": 2.8,             # raiz -> boca
        "width": 0.62,             # largura do sprite do cano (cabem as bobinas)
        "pad": 0.40,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.32, 0.28, 0.22, 0.16, 0.11, 0.06, 0.03, 0.01],
        "heat": [0.36, 0.29, 0.22, 0.15, 0.08],   # calor fraco so nas pontas (o plasma brilha em ciano)
        "interval": 0.065,
    },
    "lights": [
        {"at": [0.0, -1.40], "size": 1.7, "color": [70, 215, 255], "z": 0.9},
    ],
    "preview_pattern": "alternate",
}

BZ = 0.58                          # altura do eixo dos canos
ROOT = PART["barrels"]["root"]
BX = 0.5                           # deslocamento lateral dos canos (= ys)


# ============================================================================ utilidades locais
def _lines(target, name, specs, ztop, mat, w=0.016, depth=0.02):
    """Linhas de painel recortadas no alvo: specs = [(x, y, comprimento, rotacao)]."""
    if target is None:
        return
    cuts = [B.rbox(f"{name}{i}", x, y, w, ln, ztop - depth, ztop + 0.4, mat, rot=r, bevel=0.0)
            for i, (x, y, ln, r) in enumerate(specs)]
    B.cut(target, cuts)


def _stroke(name, p, q, w, z0, z1, mat, tags):
    """Traco fino (caixa girada) de p ate q; pontas estendidas w/2 para emendar com o proximo."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    rot = math.degrees(math.atan2(-dx, dy))
    return B.rbox(name, (p[0] + q[0]) / 2, (p[1] + q[1]) / 2, w, math.hypot(dx, dy) + w, z0, z1, mat, rot=rot,
                  bevel=0.0, tags=tags)


def _rslot(name, cx, cy, ln, w, rot, ztop, n, M, tags, targets, depth=0.035, lit=None):
    """Fenda de pips girada (eixo longo = y local girado por rot), recortada nos alvos."""
    for t in targets:
        if t is not None:
            B.cut(t, [B.rbox(name + "_c", cx, cy, w, ln, ztop - depth, ztop + 0.3, M["black"], rot=rot, bevel=0.0)])
    B.rbox(name + "_bed", cx, cy, w, ln, ztop - depth - 0.01, ztop - depth + 0.004, M["black"], rot=rot,
           bevel=0.0, tags=tags)
    a = math.radians(rot)
    ux, uy = -math.sin(a), math.cos(a)
    for i in range(n):
        s = ((i + 0.5) / n - 0.5) * ln
        on = lit is None or i < lit
        B.rbox(f"{name}_p{i}", cx + ux * s, cy + uy * s, w * 0.55, ln / n * 0.55, ztop - depth,
               ztop - depth + 0.012, M["glow"] if on else M["core_mid"], rot=rot, bevel=0.0, tags=tags)


# ============================================================================ cabeca
def head(M, T="head", phase=0.0):
    """Cabeca: casco em ponta de flecha, garras nos canos, crista de laminas de chama varrendo para tras."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    flame_m = B.mat_glow("flame_glow", Mo.CYAN, 1.6)

    # anel giratorio e nucleo escuro (octogono em ponta de flecha)
    B.cyl("ring", 0, 0, 0.04, 1.74, 0.08, KM, axis="Z", verts=80, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, 1.66, 32, 0.1), 0.09, 0.024, S, tags=tags)
    core = [(-0.98, -1.52), (0.98, -1.52), (1.36, -1.14), (1.42, 0.66), (0.96, 1.42), (-0.96, 1.42),
            (-1.42, 0.66), (-1.36, -1.14)]
    B.plate("core", core, 0.06, 0.36, K, slope=0.05, tags=tags)
    house = [(-0.90, -1.28), (0.90, -1.28), (1.00, -1.18), (1.00, 0.40), (0.82, 0.60), (-0.82, 0.60),
             (-1.00, 0.40), (-1.00, -1.18)]
    B.plate("house", house, 0.34, 0.54, KM, slope=0.05, tags=tags)

    # ---------------------------------------------------------------- crista de chamas (pes virados / cabelo de fogo)
    # duas camadas por lado varrendo para tras: chama baixa com 3 linguas (lateral, canto, traseira) e chama
    # alta com 2 linguas por cima; as raizes somem sob a ombreira
    low = [(-0.86, -0.58), (-1.50, -0.08), (-1.63, -0.36), (-1.80, -0.68), (-1.90, -1.01), (-1.71, -0.88),
           (-1.54, -0.86), (-1.66, -1.24), (-1.79, -1.57), (-1.85, -1.85), (-1.62, -1.66), (-1.40, -1.36),
           (-1.24, -1.26), (-1.22, -1.58), (-1.12, -1.90), (-0.98, -1.66), (-0.90, -1.30), (-0.84, -0.90)]
    up = [(-0.94, -0.52), (-1.40, -0.20), (-1.52, -0.52), (-1.64, -0.92), (-1.72, -1.40), (-1.50, -1.14),
          (-1.34, -1.10), (-1.32, -1.40), (-1.28, -1.70), (-1.12, -1.44), (-1.02, -1.10), (-0.96, -0.80)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        la, lp = B.shard(f"flameL{side}", f(low), 0.30, 0.56, A, slope=0.05, groove=0.03, panel_h=0.022,
                         tags=tags)
        _lines(lp, f"fll{side}", [(sx * 1.72, -0.64, 0.22, sx * 26), (sx * 1.00, -1.42, 0.22, sx * 8)], 0.582, K)
        # calco escuro sob a chama alta: vao escuro entre as duas camadas (le como placas sobrepostas)
        B.plate(f"flameS{side}", B.offset_poly(f(up), -0.045, max_miter=1.6), 0.46, 0.60, KM, slope=0.02,
                bevel=0.01, tags=tags)
        ua, un = B.shard(f"flameU{side}", f(up), 0.54, 0.80, A, slope=0.06, groove=0.032, panel_h=0.025,
                         tags=tags)
        _lines(un, f"ful{side}", [(sx * 1.13, -1.22, 0.26, sx * 18)], 0.825, K)
        # fenda com pips ciano ao longo da lingua de cima
        _rslot(f"fslot{side}", sx * 1.30, -0.70, 0.36, 0.055, sx * 28.6, 0.825, 3, M, tags, [ua, un], depth=0.035)

    # ---------------------------------------------------------------- ombreiras, garras
    paul = [(-0.86, -0.62), (-1.18, -0.62), (-1.44, -0.36), (-1.54, 0.06), (-1.54, 0.50), (-1.36, 0.80),
            (-0.90, 0.88), (-0.86, 0.74), (-0.86, 0.30), (-0.96, 0.20), (-0.96, -0.30), (-0.86, -0.40)]
    pcap = [(-1.10, -0.04), (-1.38, -0.04), (-1.46, 0.06), (-1.46, 0.48), (-1.32, 0.70), (-1.10, 0.72)]
    claw = [(-1.54, 0.92), (-1.22, 0.94), (-0.90, 1.10), (-0.85, 1.36), (-0.85, 1.74), (-0.93, 1.88),
            (-1.08, 1.80), (-1.58, 1.12)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        pa, pp = B.shard(f"paul_{side}", f(paul), 0.34, 0.84, A, slope=0.10, groove=0.045, panel_h=0.035,
                         tags=tags)
        _lines(pp, f"ppl{side}", [(sx * 1.02, 0.18, 0.40, 0), (sx * 1.20, -0.42, 0.22, sx * 45)], 0.875, K)
        ca_, cp_ = B.shard(f"pcap_{side}", f(pcap), 0.86, 0.96, A, slope=0.05, groove=0.025, panel_h=0.02,
                           tags=tags)
        Mo.slot_with_pips(f"pslot{side}", sx * 1.30, 0.06, 0.44, 0.06, 0.98, 3, M, tags, target=[ca_, cp_],
                          depth=0.035)
        # garra frontal (lamina) com fenda acesa
        ca, cp = B.shard(f"claw_{side}", f(claw), 0.34, 0.76, A, slope=0.09, groove=0.035, panel_h=0.03, tags=tags)
        for t in (ca, cp):
            B.cut(t, [B.rbox(f"ccut{side}", sx * 1.20, 1.30, 0.36, 0.05, 0.70, 1.0, K, rot=sx * -42, bevel=0.0)])
        B.rbox(f"cbed{side}", sx * 1.20, 1.30, 0.36, 0.05, 0.68, 0.705, M["black"], rot=sx * -42, bevel=0.0,
               tags=tags)
        B.rbox(f"cglow{side}", sx * 1.20, 1.30, 0.27, 0.016, 0.70, 0.712, M["glow_dim"], rot=sx * -42, bevel=0.0,
               tags=tags)
        _lines(cp, f"cpl{side}", [(sx * 0.93, 1.52, 0.24, 0)], 0.79, K)

    # ---------------------------------------------------------------- bercos escuros dos canos (raiz copiada)
    for sx in (-1, 1):
        cx = sx * BX
        crad = [(cx - 0.29, 0.50), (cx + 0.29, 0.50), (cx + 0.30, 0.70), (cx + 0.30, 1.46), (cx + 0.18, 1.60),
                (cx - 0.18, 1.60), (cx - 0.30, 1.46), (cx - 0.30, 0.70)]
        c = B.plate(f"cradle{sx}", crad, 0.28, 0.56, KM, slope=0.04, tags=tags)
        B.cut(c, [B.box(f"crad_c{sx}", cx, 1.08, 0.40, 0.86, 0.48, 0.9, K, bevel=0.0)])
        _breech(M, tags, f"hb{sx}", cx, ROOT)
        B.cyl(f"cradcol{sx}", cx, 1.56, BZ, 0.255, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=tags)
        # guias de recuo de aco nas bordas do berco e injetor de plasma atras da culatra
        for k in (-1, 1):
            B.cyl(f"crod{sx}{k}", cx + k * 0.258, 1.02, 0.56, 0.028, 0.92, S, axis="Y", verts=10, tags=tags)
        B.box(f"inj{sx}", cx, 0.72, 0.34, 0.16, 0.50, 0.66, KM, bevel=0.012, tags=tags)
        B.box(f"injr{sx}", cx, 0.79, 0.38, 0.04, 0.52, 0.68, S, bevel=0.006, tags=tags)
        B.box(f"injs{sx}", cx, 0.69, 0.20, 0.05, 0.655, 0.665, M["black"], bevel=0.0, tags=tags)
        B.box(f"injg{sx}", cx, 0.69, 0.14, 0.016, 0.66, 0.668, M["glow_dim"], bevel=0.0, tags=tags)
        # dutos de plasma: do tanque ate a traseira do berco
        yaw = sx * 21.8
        B.cyl(f"duct{sx}", sx * 0.56, 0.40, 0.58, 0.055, 0.36, KM, axis="Y", verts=8, yaw=yaw, tags=tags)
        ux, uy = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        for i in range(3):
            t = -0.11 + i * 0.11
            B.cyl(f"ductr{sx}{i}", sx * 0.56 + ux * t, 0.40 + uy * t, 0.58, 0.064, 0.025, S, axis="Y", verts=8,
                  yaw=yaw, tags=tags)

    # proa central bifurcada entre os canos (ecoa as pontas abertas dos trilhos)
    B.plate("prow_base", [(-0.16, 0.56), (0.16, 0.56), (0.16, 0.80), (-0.16, 0.80)], 0.30, 0.62, KM, slope=0.03,
            tags=tags)
    B.box("prow_fl", 0, 1.26, 0.10, 0.92, 0.30, 0.56, KM, bevel=0.0, tags=tags)
    for sx in (-1, 1):
        prong = [(sx * 0.035, 0.62), (sx * 0.16, 0.62), (sx * 0.16, 1.40), (sx * 0.09, 1.82), (sx * 0.035, 1.70)]
        B.shard(f"prow{sx}", prong, 0.40, 0.84, A, slope=0.035, groove=0.018, panel_h=0.015, tags=tags)
    B.box("prow_ch", 0, 1.26, 0.07, 0.92, 0.56, 0.60, M["black"], bevel=0.0, tags=tags)
    B.box("prow_glow", 0, 1.22, 0.02, 0.44, 0.60, 0.606, M["glow_dim"], bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- espinha com sensor e a chama gravada
    spine = [(-0.30, -1.24), (0.30, -1.24), (0.36, -1.12), (0.36, 0.16), (0.17, 0.56), (-0.17, 0.56),
             (-0.36, 0.16), (-0.36, -1.12)]
    sa, sp = B.shard("spine", spine, 0.56, 1.00, A, slope=0.08, groove=0.035, panel_h=0.03, tags=tags)
    sp2 = [(-0.20, -0.98), (0.20, -0.98), (0.23, -0.90), (0.23, 0.08), (0.09, 0.36), (-0.09, 0.36),
           (-0.23, 0.08), (-0.23, -0.90)]
    s2 = B.plate("spine2", sp2, 1.02, 1.12, A, slope=0.035, tags=tags)
    win = [(-0.12, -0.04), (0.12, -0.04), (0.12, 0.07), (0.045, 0.21), (-0.045, 0.21), (-0.12, 0.07)]
    B.cut(s2, [B.loft("win_cut", win, win, 1.08, 1.4, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 1.075, 1.085, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, 0.05, 0.16, 0.03, 1.08, 1.092, M["glow"], bevel=0.0, tags=tags)
    # chama do Curupira: rebaixo preto com contorno ciano fino (linguas apontando para tras)
    gl = [(0.0, 0.0), (0.10, 0.03), (0.145, 0.12), (0.14, 0.22), (0.11, 0.30), (0.14, 0.40), (0.06, 0.34),
          (0.04, 0.42), (0.0, 0.54), (-0.04, 0.42), (-0.06, 0.34), (-0.14, 0.40), (-0.11, 0.30), (-0.14, 0.22),
          (-0.145, 0.12), (-0.10, 0.03)]
    flame = [(x * 0.85, -0.79 + v * 0.95) for x, v in gl]
    dl = [(0.0, 0.08), (0.05, 0.13), (0.055, 0.21), (0.0, 0.32), (-0.055, 0.21), (-0.05, 0.13)]
    drop = [(x * 0.85, -0.79 + v * 0.95) for x, v in dl]
    shield = [(-0.13, -0.83), (0.13, -0.83), (0.16, -0.78), (0.16, -0.38), (0.0, -0.20), (-0.16, -0.38),
              (-0.16, -0.78)]
    B.cut(s2, [B.loft("flame_cut", shield, shield, 1.09, 1.4, K, bevel=0.0)])
    B.loft("flame_bed", shield, shield, 1.08, 1.095, M["black"], bevel=0.0, tags=tags)
    for nm, pts in (("fo", flame), ("fi", drop)):
        for i in range(len(pts)):
            _stroke(f"flame_{nm}{i}", pts[i], pts[(i + 1) % len(pts)], 0.017, 1.094, 1.102, flame_m, tags)
    Mo.slot_with_pips("sp", -1.055, -0.16, 0.16, 0.05, 1.03, 3, M, tags, target=sp, depth=0.03, vertical=False)

    # ---------------------------------------------------------------- tanques de celulas de plasma nos vaos
    for sx in (-1, 1):
        x = sx * 0.62
        B.cyl(f"tank{sx}", x, -0.225, 0.66, 0.15, 0.95, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
        for i, y in enumerate((-0.66, -0.225, 0.21)):
            B.cyl(f"tankring{sx}{i}", x, y, 0.66, 0.162, 0.045, S, axis="Y", verts=8, bevel=0.005, tags=tags)
        for k, (y0, y1) in enumerate(((-0.60, -0.27), (-0.18, 0.15))):
            B.box(f"tankwin{sx}{k}", x, (y0 + y1) / 2, 0.075, y1 - y0, 0.79, 0.815, M["black"], bevel=0.0,
                  tags=tags)
            for i in range(4):
                lit = (i < 3) if k == 0 else (i < 2)
                B.box(f"tankled{sx}{k}{i}", x, y0 + (i + 0.5) * (y1 - y0) / 4, 0.04, 0.045, 0.815, 0.825,
                      M["glow"] if lit else M["core_mid"], bevel=0.0, tags=tags)

    # bobinas de carga pequenas atras dos tanques (ecoam as bobinas dos canos)
    for sx in (-1, 1):
        x, cy0 = sx * 0.62, -0.98
        B.cyl(f"mcoil{sx}", x, cy0, 0.62, 0.075, 0.40, KM, axis="Y", verts=8, bevel=0.006, tags=tags)
        B.box(f"mcbed{sx}", x, cy0, 0.06, 0.30, 0.68, 0.70, M["black"], bevel=0.0, tags=tags)
        for i in range(4):
            B.cyl(f"mcr{sx}{i}", x, cy0 - 0.12 + i * 0.08, 0.62, 0.11, 0.04, A, axis="Y", verts=8, bevel=0.005,
                  tags=tags)
        for i in range(3):
            B.box(f"mcp{sx}{i}", x, cy0 - 0.08 + i * 0.08, 0.035, 0.016, 0.70, 0.708, M["glow_dim"], bevel=0.0,
                  tags=tags)

    # ---------------------------------------------------------------- baia de exaustao traseira
    B.box("vent_bay", 0, -1.40, 1.04, 0.24, 0.20, 0.38, M["black"], bevel=0.0, tags=tags)
    for i in range(5):
        B.box(f"louver{i}", 0, -1.49 + i * 0.045, 0.98, 0.02, 0.30, 0.39, KM, bevel=0.004, tags=tags)
    for i in range(6):
        B.box(f"vent_pip{i}", -0.40 + i * 0.16, -1.27, 0.065, 0.024, 0.34, 0.40, M["glow"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"module{sx}", sx * 0.72, -1.30, 0.18, 0.24, 0.30, 0.48, KM, bevel=0.01, tags=tags)
        B.box(f"modled{sx}", sx * 0.72, -1.22, 0.10, 0.026, 0.48, 0.49, M["glow_dim"], bevel=0.0, tags=tags)
    B.bolts("bolt", [(x, -1.44) for x in (-0.86, 0.86)], 0.37, 0.024, S, tags=tags)


# ============================================================================ cano
def _breech(M, tags, pre, x, y0):
    """Banco de capacitores escuro na raiz do cano (usado no cano e copiado no berco da cabeca)."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    B.cyl(f"{pre}_cap", x, y0 + 0.25, BZ, 0.235, 0.50, KM, axis="Y", verts=8, bevel=0.012, tags=tags)
    for i, y in enumerate((0.08, 0.20, 0.32)):
        B.cyl(f"{pre}_strap{i}", x, y0 + y, BZ, 0.25, 0.035, K, axis="Y", verts=8, bevel=0.005, tags=tags)
    B.cyl(f"{pre}_capr", x, y0 + 0.47, BZ, 0.245, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    for k in (-1, 1):  # barramentos de aco no topo
        B.box(f"{pre}_bus{k}", x + k * 0.10, y0 + 0.24, 0.04, 0.40, BZ + 0.18, BZ + 0.25, S, bevel=0.006, tags=tags)


def barrel(M, L=2.8, T="barrel", phase=0.0):
    """Cano de trilho com raiz (y=0) e boca (y=L), centrado em x=0, eixo na altura BZ."""
    tags = (T,)
    hot = (T, "hot")  # so as pontas dos trilhos esquentam
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = BZ
    _breech(M, tags, "b", 0.0, 0.0)

    def coils(pre, y0, n, r, pitch=0.11, th=0.066, ends=(True, True)):
        """Pacote de bobinas claras com pips ciano no fundo escuro entre elas (tubo escuro por dentro)."""
        yl = (n - 1) * pitch
        B.cyl(f"{pre}_core", 0, y0 + yl / 2, z, 0.17, yl + 0.16, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
        B.box(f"{pre}_bed", 0, y0 + yl / 2, 0.13, yl, z + 0.15, z + 0.178, M["black"], bevel=0.0, tags=tags)
        for i in range(n):
            ring = B.cyl(f"{pre}{i}", 0, y0 + i * pitch, z, r, th, A, axis="Y", verts=8, bevel=0.008, tags=tags)
            # canal escuro no topo das bobinas (continua o canal entre os trilhos)
            B.cut(ring, [B.box(f"{pre}_cc{i}", 0, y0 + i * pitch, 0.10, th + 0.04, z + 0.17, z + 0.4, K, bevel=0.0)])
        for i in range(n - 1):
            B.box(f"{pre}_pip{i}", 0, y0 + (i + 0.5) * pitch, 0.06, 0.022, z + 0.178, z + 0.19,
                  M["glow"] if i % 2 == 0 else M["glow_dim"], bevel=0.0, tags=tags)
        # aros de aco nas pontas do pacote
        for k, y in enumerate((y0 - 0.06, y0 + yl + 0.06)):
            if ends[k]:
                B.cyl(f"{pre}_end{k}", 0, y, z, r - 0.01, 0.035, S, axis="Y", verts=8, bevel=0.005, tags=tags)

    coils("b_coilA", 0.62, 7, 0.25)
    coils("b_coilB", 1.86, 5, 0.235, ends=(True, False))

    def rails(pre, y0, y1, ch_glow=False):
        """Trecho de trilhos expostos: duas barras claras facetadas com canal escuro no meio."""
        B.box(f"{pre}_fl", 0, (y0 + y1) / 2, 0.12, y1 - y0, z - 0.10, z + 0.06, KM, bevel=0.0, tags=tags)
        B.box(f"{pre}_ch", 0, (y0 + y1) / 2, 0.10, y1 - y0, z + 0.06, z + 0.09, M["black"], bevel=0.0, tags=tags)
        for sx in (-1, 1):
            poly = [(sx * 0.05, y0), (sx * 0.205, y0), (sx * 0.205, y1), (sx * 0.05, y1)]
            r = B.plate(f"{pre}{sx}", poly, z - 0.12, z + 0.165, A, slope=0.03, tags=tags)
            _lines(r, f"{pre}l{sx}", [(sx * 0.128, (y0 + y1) / 2, y1 - y0 - 0.12, 0)], z + 0.165, K)
        if ch_glow:
            B.box(f"{pre}_g", 0, (y0 + y1) / 2, 0.022, y1 - y0 - 0.14, z + 0.09, z + 0.096, M["glow_dim"],
                  bevel=0.0, tags=tags)

    rails("b_railA", 1.38, 1.76, ch_glow=True)
    B.cyl("b_collar", 0, 2.35, z, 0.225, 0.05, AM, axis="Y", verts=8, bevel=0.008, tags=tags)
    # pontas abertas: duas pontas claras facetadas (nariz em seta) com canal escuro e portas transversais
    y0 = 2.38
    B.box("b_tipbase", 0, (y0 + L - 0.20) / 2, 0.20, L - 0.20 - y0, z - 0.10, z + 0.03, KM, bevel=0.0, tags=tags)
    for sx in (-1, 1):
        prong = [(sx * 0.045, y0), (sx * 0.205, y0), (sx * 0.232, y0 + 0.04), (sx * 0.232, L - 0.17),
                 (sx * 0.115, L), (sx * 0.045, L - 0.04)]
        pr = B.plate(f"b_prong{sx}", prong, z - 0.13, z + 0.14, A, slope=0.035, tags=hot)
        B.cut(pr, [B.box(f"b_port{sx}{i}", sx * 0.14, y0 + 0.11 + i * 0.09, 0.22, 0.04, z + 0.04, z + 0.3, K,
                         bevel=0.0) for i in range(2)])
    B.box("b_tipch", 0, (y0 + L - 0.20) / 2, 0.09, L - 0.20 - y0, z - 0.02, z + 0.035, M["black"], bevel=0.0,
          tags=tags)
    B.box("b_bore", 0, L - 0.30, 0.025, 0.14, z + 0.035, z + 0.041, M["glow_dim"], bevel=0.0, tags=tags)


# ============================================================================ teto
def roof(M, T="roof"):
    """Teto: placas do conves (verde = pintura) + estante de celulas de plasma na fileira de tras."""
    tags = (T,)
    W, H = PART["size"]
    pv = PART["pivot"]
    ring_r = PART["ring_r"]
    green = B.mat_roof_green()
    px, py = pv[0] - W / 2, H / 2 - pv[1]
    gap = 0.03
    B.box("deck_under", 0, 0, W, H, -0.05, 0.02, M["core"], bevel=0.0, tags=tags)
    for tx in range(W):
        for ty in range(H):
            cx, cy = tx + 0.5 - W / 2, H / 2 - ty - 0.5
            poly = B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
            _, pnl = B.shard(f"deck{tx}_{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02,
                             tags=tags)
            if (tx + ty) % 2 == 0 and pnl is not None:
                B.cut(pnl, [B.rbox(f"dl{tx}{ty}", cx + 0.18, cy - 0.18, 0.012, 0.5, 0.07, 0.2, M["core"], rot=45,
                                   bevel=0.0)])
    # anel da torre (sem pintura)
    B.torus("ringbear", px, py, 0.08, ring_r + 0.02, 0.055, M["core_mid"], tags=tags)
    B.cyl("ringhole", px, py, 0.05, ring_r - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(px, py, ring_r + 0.11, 36)
           if abs(x) < W / 2 - 0.06 and abs(y) < H / 2 - 0.06]
    B.bolts("rb", pts, 0.1, 0.022, M["steel"], tags=tags)
    # estante de celulas na fileira de tras: faixa escura com 4 baias blindadas (celula ciano + nivel)
    sy = -H / 2 + 0.5
    strip = B.plate("cellstrip", B.rpoly(0, sy, W - 0.14, 0.84, 0, chamfer=0.12), 0.05, 0.11, M["core_mid"],
                    slope=0.025, tags=tags)
    rec = [B.box(f"vc{k}", k + 1 - W / 2, sy, 0.10, 0.50, 0.075, 0.3, M["core"], bevel=0.0) for k in range(W - 1)]
    B.cut(strip, rec)
    for k in range(W - 1):
        vx = k + 1 - W / 2
        B.box(f"vbed{k}", vx, sy, 0.10, 0.50, 0.07, 0.08, M["black"], bevel=0.0, tags=tags)
        for i in range(5):
            B.box(f"vlouver{k}{i}", vx, sy - 0.20 + i * 0.10, 0.085, 0.026, 0.08, 0.105, M["core_mid"], bevel=0.004,
                  tags=tags)
    for tx in range(W):
        cx = tx + 0.5 - W / 2
        # moldura blindada em seta (aponta para a frente)
        y0, y1 = sy - 0.32, sy + 0.34
        bay = [(cx - 0.30, y0), (cx + 0.30, y0), (cx + 0.36, y0 + 0.06), (cx + 0.36, y1 - 0.14), (cx + 0.20, y1),
               (cx - 0.20, y1), (cx - 0.36, y1 - 0.14), (cx - 0.36, y0 + 0.06)]
        ba, bp = B.shard(f"bay{tx}", bay, 0.10, 0.16, M["armor_mid"], slope=0.02, groove=0.03, panel_h=0.015,
                         tags=tags)
        # janela da celula (horizontal) com a celula de plasma dentro
        wy = sy + 0.02
        for t in (ba, bp):
            B.cut(t, [B.box(f"bwin{tx}", cx, wy, 0.56, 0.17, 0.12, 0.4, M["core"], bevel=0.0)])
        B.box(f"bwbed{tx}", cx, wy, 0.56, 0.17, 0.10, 0.125, M["black"], bevel=0.0, tags=tags)
        B.cyl(f"cell{tx}", cx, wy, 0.16, 0.06, 0.44, M["core_mid"], axis="X", verts=8, bevel=0.004, tags=tags)
        B.box(f"cellg{tx}", cx, wy, 0.34, 0.026, 0.215, 0.222, M["glow_dim"], bevel=0.0, tags=tags)
        for k in (-1, 1):
            B.cyl(f"cellcap{tx}{k}", cx + k * 0.24, wy, 0.16, 0.068, 0.04, M["steel"], axis="X", verts=8,
                  bevel=0.004, tags=tags)
        # nivel: 3 pips num rebaixo (dois acesos)
        for t in (ba, bp):
            B.cut(t, [B.box(f"lvlc{tx}", cx, sy - 0.20, 0.32, 0.06, 0.15, 0.4, M["core"], bevel=0.0)])
        for i in range(3):
            B.box(f"lvl{tx}{i}", cx - 0.10 + i * 0.10, sy - 0.20, 0.06, 0.03, 0.155, 0.165,
                  M["glow"] if i < 2 else M["core_mid"], bevel=0.0, tags=tags)
        B.box(f"lvlbed{tx}", cx, sy - 0.20, 0.32, 0.06, 0.14, 0.155, M["black"], bevel=0.0, tags=tags)
        B.box(f"bhandle{tx}", cx, y1 - 0.08, 0.16, 0.03, 0.17, 0.19, M["steel"], bevel=0.006, tags=tags)
