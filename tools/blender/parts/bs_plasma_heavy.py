"""Canhao de Plasma Pesado ("Curupira") - guardiao da floresta, de pes virados e cabelo de fogo; mesma familia do 76 mm.

Cabeca em ponta de flecha: garras de ponta bifurcada que avancam ate os canos, proa central bifurcada (repete
as pontas dos trilhos), espinha com sensor e a chama do Curupira gravada num rebaixo, ombreiras com tampa em
lingua virada para tras e, atras, uma crista de chamas angulares que varre PARA TRAS (os pes virados / o
cabelo de fogo): duas camadas por lado (3 linguas embaixo, 2 em cima, calco escuro entre elas), todas dentro
de r 2.3 do pivo. Tanques de celulas de plasma com nivel ciano nos vaos, bobinas de carga pequenas atras
deles, dutos ate os bercos em cunha, baia de exaustao traseira com pips ciano. Teto com estante de celulas em
favo (4 baias hexagonais, 2 celulas com coluna de nivel cada). Piso proprio com estante e condutos ate o anel.
Dois canos de trilho grossos: banco de capacitores escuro afunilado na raiz (copiado no berco da cabeca),
pescoco escuro, dois pacotes de bobinas claras com colares cinza a cada 3 aneis (batida de 0.36 tile) e canal
escuro estreito no topo (pips ciano nos vaos), trilhos expostos e pontas abertas (duas pontas claras facetadas
por cano com canal escuro no meio) - so as pontas esquentam.
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
        "heat_color": (0.25, 0.85, 1.0),  # calor de plasma: brilho ciano nas pontas dos trilhos
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
    # contorno da chama: cor do acento, fraco (o sensor continua sendo o foco, como no 76 mm)
    flame_m = B.mat_glow("flame_glow", Mo.ACCENTS[PART["accent"]], 1.1)

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
    # alta com 2 linguas por cima; as raizes somem sob a ombreira. Todas as pontas ficam em r <= 2.3 do pivo
    # (a cabeca gira sem varrer as pecas vizinhas nem a estante de celulas do teto)
    low = [(-0.86, -0.58), (-1.50, -0.08), (-1.63, -0.36), (-1.80, -0.68), (-1.90, -1.00), (-1.71, -0.88),
           (-1.55, -0.87), (-1.66, -1.18), (-1.73, -1.40), (-1.64, -1.60), (-1.46, -1.46), (-1.32, -1.32),
           (-1.22, -1.28), (-1.20, -1.58), (-1.11, -1.88), (-0.98, -1.66), (-0.90, -1.30), (-0.84, -0.90)]
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
    # tampa da ombreira em lingua de chama: borda externa termina numa ponta virada PARA TRAS (pes virados)
    pcap = [(-1.08, -0.02), (-1.22, -0.06), (-1.34, -0.25), (-1.45, 0.02), (-1.46, 0.48), (-1.32, 0.70),
            (-1.08, 0.72)]
    # garra com ponta bifurcada (duas pontas + entalhe em V, ecoa as pontas abertas dos trilhos)
    claw = [(-1.54, 0.92), (-1.22, 0.94), (-0.90, 1.10), (-0.85, 1.36), (-0.85, 1.74), (-0.89, 1.90),
            (-0.97, 1.74), (-1.06, 1.86), (-1.14, 1.76), (-1.58, 1.12)]
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
        # berco em cunha (frente afunilada, cantos de tras chanfrados), dentro da faixa x do sprite do cano
        crad = [(cx - 0.21, 0.50), (cx + 0.21, 0.50), (cx + 0.30, 0.62), (cx + 0.30, 1.20), (cx + 0.15, 1.60),
                (cx - 0.15, 1.60), (cx - 0.30, 1.20), (cx - 0.30, 0.62)]
        c = B.plate(f"cradle{sx}", crad, 0.28, 0.56, KM, slope=0.04, tags=tags)
        B.cut(c, [B.box(f"crad_c{sx}", cx, 0.985, 0.40, 0.67, 0.48, 0.9, K, bevel=0.0)])
        _breech(M, tags, f"hb{sx}", cx, ROOT)
        # guias de recuo escuras (ponteira de aco) nas bordas do berco e injetor de plasma atras da culatra
        for k in (-1, 1):
            B.cyl(f"crod{sx}{k}", cx + k * 0.258, 0.88, 0.56, 0.028, 0.56, KM, axis="Y", verts=10, tags=tags)
            B.cyl(f"crodt{sx}{k}", cx + k * 0.258, 1.17, 0.56, 0.034, 0.05, S, axis="Y", verts=8, bevel=0.004,
                  tags=tags)
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
    # corpo afunilado para a frente (le como cunha, nao como gaiola)
    B.cyl(f"{pre}_cap", x, y0 + 0.25, BZ, 0.24, 0.50, KM, axis="Y", verts=8, bevel=0.012, tags=tags, r2=0.20)
    for i, (y, r) in enumerate(((0.08, 0.25), (0.20, 0.24), (0.32, 0.23))):
        B.cyl(f"{pre}_strap{i}", x, y0 + y, BZ, r, 0.035, K, axis="Y", verts=8, bevel=0.005, tags=tags)
    B.cyl(f"{pre}_capr", x, y0 + 0.47, BZ, 0.215, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    # espinha de barramento no topo: rebaixo preto com fenda ciano fraca
    B.box(f"{pre}_bus", x, y0 + 0.23, 0.12, 0.40, BZ + 0.16, BZ + 0.255, KM, bevel=0.008, tags=tags)
    B.box(f"{pre}_busb", x, y0 + 0.23, 0.06, 0.30, BZ + 0.255, BZ + 0.262, M["black"], bevel=0.0, tags=tags)
    B.box(f"{pre}_busg", x, y0 + 0.23, 0.018, 0.22, BZ + 0.262, BZ + 0.267, M["glow_dim"], bevel=0.0, tags=tags)


def barrel(M, L=2.8, T="barrel", phase=0.0):
    """Cano de trilho com raiz (y=0) e boca (y=L), centrado em x=0, eixo na altura BZ."""
    tags = (T,)
    hot = (T, "hot")  # so as pontas dos trilhos esquentam
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = BZ
    _breech(M, tags, "b", 0.0, 0.0)
    # pescoco escuro: emenda a culatra (termina em 0.495) no tubo do primeiro pacote (sem fresta no sprite)
    B.cyl("b_neck", 0, 0.56, z, 0.19, 0.15, KM, axis="Y", verts=8, bevel=0.006, tags=tags)

    def coils(pre, y0, kinds, r, pitch=0.12, th=0.07):
        """Pacote de bobinas com pips ciano no canal escuro do topo. kinds: 'c' = bobina clara,
        'k' = colar cinza medio um pouco maior (marca uma batida de ~0.36 tile, como os colares do 76 mm)."""
        n = len(kinds)
        yl = (n - 1) * pitch
        B.cyl(f"{pre}_core", 0, y0 + yl / 2, z, 0.17, yl + 0.12, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
        B.box(f"{pre}_bed", 0, y0 + yl / 2, 0.075, yl, z + 0.15, z + 0.178, M["black"], bevel=0.0, tags=tags)
        for i, k in enumerate(kinds):
            y = y0 + i * pitch
            if k == "c":
                ring = B.cyl(f"{pre}{i}", 0, y, z, r, th, A, axis="Y", verts=8, bevel=0.008, tags=tags)
            else:
                ring = B.cyl(f"{pre}{i}", 0, y, z, r + 0.025, 0.06, AM, axis="Y", verts=8, bevel=0.008, tags=tags)
            # canal escuro estreito no topo (continua o canal entre os trilhos)
            B.cut(ring, [B.box(f"{pre}_cc{i}", 0, y, 0.07, th + 0.04, z + 0.17, z + 0.4, K, bevel=0.0)])
        for i in range(n - 1):
            both = kinds[i] == "c" and kinds[i + 1] == "c"
            B.box(f"{pre}_pip{i}", 0, y0 + (i + 0.5) * pitch, 0.045, 0.024, z + 0.178, z + 0.19,
                  M["glow"] if both else M["glow_dim"], bevel=0.0, tags=tags)

    coils("b_coilA", 0.66, "kcckcck", 0.25)      # 0.66 .. 1.38
    coils("b_coilB", 1.86, "kccck", 0.235)       # 1.86 .. 2.34 (o ultimo colar segura as pontas)

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

    # trilhos entram 0.03 sob os colares das pontas (sem fresta)
    rails("b_railA", 1.35, 1.89, ch_glow=True)
    # pontas abertas: duas pontas claras facetadas (nariz em seta) com canal escuro e portas transversais
    y0 = 2.36
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
    # estante de celulas na fileira de tras: 4 baias hexagonais em favo (ponta para a frente), cada uma com
    # 2 celulas de plasma deitadas e uma coluna de nivel ciano; coletor escuro liga as baias
    sy = -H / 2 + 0.5
    lit = (3, 4, 2, 3, 4, 3, 3, 2)
    for tx in range(W):
        cx = tx + 0.5 - W / 2
        hexp = [(cx, sy - 0.44), (cx + 0.40, sy - 0.23), (cx + 0.40, sy + 0.23), (cx, sy + 0.44),
                (cx - 0.40, sy + 0.23), (cx - 0.40, sy - 0.23)]
        ba, bp = B.shard(f"bay{tx}", hexp, 0.05, 0.13, M["armor_mid"], slope=0.025, groove=0.03, panel_h=0.015,
                         tags=tags)
        inner = B.offset_poly(hexp, 0.10)
        for t in (ba, bp):
            if t is not None:
                B.cut(t, [B.loft(f"bayc{tx}_{t.name}", inner, inner, 0.09, 0.4, M["core"], bevel=0.0)])
        B.loft(f"baybed{tx}", inner, inner, 0.08, 0.095, M["black"], bevel=0.0, tags=tags)
        for k, sxk in enumerate((-1, 1)):
            x = cx + sxk * 0.13
            n = lit[tx * 2 + k]
            B.cyl(f"cell{tx}{k}", x, sy, 0.16, 0.085, 0.42, M["core_mid"], axis="Y", verts=8, bevel=0.006,
                  tags=tags)
            for e in (-1, 1):
                B.cyl(f"cellcap{tx}{k}{e}", x, sy + e * 0.20, 0.16, 0.094, 0.04, M["steel"], axis="Y", verts=8,
                      bevel=0.004, tags=tags)
            # coluna de nivel: fenda preta no topo da celula com 4 pips (de tras para a frente)
            B.box(f"lvlbed{tx}{k}", x, sy, 0.045, 0.30, 0.236, 0.246, M["black"], bevel=0.0, tags=tags)
            for i in range(4):
                B.box(f"lvl{tx}{k}{i}", x, sy - 0.105 + i * 0.07, 0.028, 0.045, 0.246, 0.252,
                      M["glow"] if i < n else M["core_mid"], bevel=0.0, tags=tags)
        # alca de aco na ponta da frente e luz de estado na ponta de tras (em rebaixo)
        B.box(f"bhandle{tx}", cx, sy + 0.33, 0.14, 0.03, 0.13, 0.155, M["steel"], bevel=0.006, tags=tags)
        B.box(f"bstat{tx}", cx, sy - 0.33, 0.10, 0.03, 0.10, 0.112, M["glow_dim"], bevel=0.0, tags=tags)
    # coletor: tocos de tubo escuro com abracadeiras de aco ligando as baias vizinhas
    for k in range(W - 1):
        vx = k + 1 - W / 2
        B.cyl(f"mani{k}", vx, sy, 0.10, 0.05, 0.30, M["core_mid"], axis="X", verts=8, bevel=0.005, tags=tags)
        for e in (-1, 1):
            B.cyl(f"manir{k}{e}", vx + e * 0.06, sy, 0.10, 0.058, 0.025, M["steel"], axis="X", verts=8,
                  bevel=0.004, tags=tags)


# ============================================================================ piso
def floor(M, T="floor"):
    """Piso: placas, anel com cubo injetor ciano, 4 postos, estante de celulas e condutos ate o anel."""
    from bsgen.common import crew_positions
    tags = (T,)
    W, H = PART["size"]
    pv = PART["pivot"]
    ring_r = PART["ring_r"]
    KM, S = M["core_mid"], M["steel"]
    px, py = pv[0] - W / 2, H / 2 - pv[1]
    B.box("fl_base", 0, 0, W, H, -0.05, 0.0, M["core"], bevel=0.0, tags=tags)
    for tx in range(W):
        for ty in range(H):
            x0, y1 = tx - W / 2 + 0.04, H / 2 - ty - 0.04
            B.box(f"fl{tx}{ty}", x0 + 0.46, y1 - 0.46, 0.92, 0.92, 0.0, 0.03, KM, bevel=0.01, tags=tags)
    # anel giratorio + cubo octogonal com o injetor de plasma (nucleo escuro, pips ciano em volta)
    rr = ring_r * 0.85
    B.torus("fl_ring", px, py, 0.05, rr, 0.05, M["armor_mid"], tags=tags)
    w = ring_r * 0.62
    oct_ = lambda s: B.rpoly(px, py, s, s, 0, chamfer=s / (2 + math.sqrt(2)))  # noqa: E731
    B.plate("fl_hub", oct_(w), 0.05, 0.12, M["armor_mid"], slope=0.03, tags=tags)
    B.plate("fl_hubc", oct_(w * 0.56), 0.10, 0.125, M["core"], slope=0.015, tags=tags)
    B.plate("fl_hubs", oct_(w * 0.22), 0.12, 0.16, S, slope=0.01, bevel=0.006, tags=tags)
    for i, (x, y) in enumerate(B.ring_points(px, py, w * 0.38, 8, math.pi / 8)):
        B.box(f"fl_hubp{i}", x, y, 0.035, 0.035, 0.125, 0.132, M["glow_dim"], bevel=0.0, tags=tags)
    for k in range(4):
        a = k * math.pi / 2
        cx, cy = px + math.cos(a) * ring_r * 0.6, py + math.sin(a) * ring_r * 0.6
        arrow = [(0.10, 0.0), (-0.06, 0.10), (-0.02, 0.0), (-0.06, -0.10)]
        ca, sa = math.cos(a), math.sin(a)
        arrow = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in arrow]
        B.plate(f"fl_chev{k}", arrow, 0.05, 0.08, M["armor"], slope=0.01, bevel=0.006, tags=tags)
    B.box("fl_led_t", px, py + rr * 1.1, 0.3, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # estante de celulas na parede de tras: 4 bercos com 3 celulas deitadas (faixa ciano no topo)
    ey = -H / 2 + 0.14
    for tx in range(W):
        cx = tx + 0.5 - W / 2
        B.box(f"fl_rack{tx}", cx, ey, 0.82, 0.20, 0.0, 0.10, M["armor_mid"], bevel=0.01, tags=tags)
        for i in range(3):
            x = cx - 0.26 + i * 0.26
            B.cyl(f"fl_cell{tx}{i}", x, ey, 0.16, 0.065, 0.20, KM, axis="X", verts=8, bevel=0.005, tags=tags)
            for e in (-1, 1):
                B.cyl(f"fl_cc{tx}{i}{e}", x + e * 0.09, ey, 0.16, 0.072, 0.025, S, axis="X", verts=8, bevel=0.004,
                      tags=tags)
            B.box(f"fl_cg{tx}{i}", x, ey, 0.11, 0.022, 0.222, 0.23, M["glow_dim"], bevel=0.0, tags=tags)
    # condutos de plasma: da estante ate o anel, passando entre os postos
    for j, x in enumerate((-1.0, 0.0, 1.0)):
        y0, y1 = ey + 0.10, py - math.sqrt(rr * rr - x * x)
        B.cyl(f"fl_duct{j}", x, (y0 + y1) / 2, 0.07, 0.05, y1 - y0, KM, axis="Y", verts=8, bevel=0.005, tags=tags)
        n = int((y1 - y0) / 0.30)
        for i in range(n + 1):
            B.cyl(f"fl_ductr{j}{i}", x, y0 + 0.06 + i * (y1 - y0 - 0.12) / max(n, 1), 0.07, 0.058, 0.025, S,
                  axis="Y", verts=8, bevel=0.004, tags=tags)
        B.box(f"fl_ductg{j}", x, (y0 + y1) / 2, 0.016, min(0.24, (y1 - y0) * 0.3), 0.12, 0.126, M["glow_dim"],
              bevel=0.0, tags=tags)
    # postos da tripulacao (mesmas posicoes que o gerador usa)
    for i, (cx, cy, _r) in enumerate(crew_positions(W, H, 4, pv)):
        x, y = cx - W / 2, H / 2 - cy
        B.box(f"seat{i}", x, y + 0.02, 0.32, 0.30, 0.0, 0.14, M["armor"], bevel=0.04, tags=tags)
        B.box(f"console{i}", x, y + 0.30, 0.42, 0.12, 0.0, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.30, 0.32, 0.06, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
