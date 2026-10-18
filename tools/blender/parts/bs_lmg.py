"""Metralhadora Leve de Conves ("Marimbondo") - a menor arma do mod (1x1), familia do 76 mm.

Vista de cima le como um marimbondo: duas mandibulas claras (ombro + lamina reta a 45 graus com ponta cortada)
que fecham sobre a raiz do cano, com o "olho" numa fenda de luz fraca; torax em ponta de flecha com espinha e
janela de sensor em seta, dividido por um sulco transversal; cintura fina (acoplamento de aco no vao escuro);
abdomen em pipa com ferrao para tras, listra transversal e fenda com 2 pips ambar. Do lado direito uma asa em
lamina reta varrida para tras (duas placas); do esquerdo a caixa de cinta listrada (corpo escuro, tampa clara
em 4 ripas) com a bandeja de cartuchos entrando na culatra. Atras, entre abdomen e caixa, uma baia de exaustao
mini (persianas) e, do outro lado, a porta de ejecao. Tudo dentro de r ~0.47 do pivo.
Cano fino: culatra escura, camisa clara perfurada (duas fileiras desencontradas de fendas, anel no meio),
tubo de aco exposto e quebra-chamas claro facetado em ponta de flecha com portas escuras.
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_lmg",
    "kind": "gun",
    "size": [1, 1],
    "pivot": [0.5, 0.5],           # centro do tile (x direita, y para baixo)
    "turret_box": 1.0,             # cabeca dentro de +-0.47
    "ring_r": 0.42,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "collider": 0.42,
    "barrels": {
        "ys": [0.0],
        "root": 0.28,              # pivo -> raiz do cano (culatra escura dentro do mantelete)
        "length": 0.90,            # raiz -> boca
        "width": 0.20,             # largura do sprite do cano (cabe o quebra-chamas)
        "pad": 0.07,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.05, 0.03, 0.012],
        "heat": [0.35, 0.18, 0.06],   # calor leve so no fundo das portas do quebra-chamas
        "interval": 0.04,
    },
    "lights": [                    # luz dinamica no ferrao (coordenadas da cabeca)
        {"at": [0.0, -0.30], "size": 0.5, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "single",
}

RING_R = PART["ring_r"]
ZB = 0.40                          # altura do eixo do cano


def side(poly, sx):
    return poly if sx > 0 else Mo.mirror(poly)


def brass():
    """Latao fosco dos cartuchos (mais escuro que um LED, nao compete com os pips)."""
    return B.mat_metal("bs_brass_lmg", (0.40, 0.25, 0.06), rough=0.40, metal=1.0)


def shard_hand(name, poly, pnl, z0, z1, mat, slope=0.025, panel_h=0.03, tags=()):
    """Placa com bisel duplo e painel interno desenhado a mao (evita ponta fina no deslocamento automatico)."""
    a = B.plate(name, poly, z0, z1, mat, slope=slope, tags=tags)
    b = B.plate(name + "_pnl", pnl, z1 - 0.004, z1 + panel_h, mat, slope=0.012, bevel=0.008, tags=tags)
    return a, b


# ============================================================================ planta (cabeca), lado direito
CORE = [(-0.24, -0.40), (0.24, -0.40), (0.38, -0.25), (0.38, 0.18), (0.22, 0.36), (-0.22, 0.36), (-0.38, 0.18),
        (-0.38, -0.25)]
MANT = [(-0.075, 0.16), (0.075, 0.16), (0.09, 0.24), (0.075, 0.40), (-0.075, 0.40), (-0.09, 0.24)]
# mandibula direita: ombro com degrau na aresta de fora, lamina reta a 45 graus, ponta cortada (>= 0.06)
MAND = [(0.245, 0.065), (0.365, 0.04), (0.40, 0.075), (0.40, 0.105), (0.43, 0.135), (0.43, 0.19), (0.40, 0.225),
        (0.195, 0.43), (0.125, 0.45), (0.115, 0.385), (0.185, 0.27), (0.215, 0.155)]
# painel interno da mandibula desenhado a mao: cobre o ombro e afina pela lamina ate uma ponta cega
MAND_PNL = [(0.27, 0.105), (0.345, 0.087), (0.36, 0.105), (0.36, 0.135), (0.385, 0.16), (0.385, 0.185),
            (0.36, 0.212), (0.19, 0.382), (0.165, 0.375), (0.225, 0.275), (0.255, 0.165)]
MAND_Z = (0.24, 0.44)
# torax (cupula central) em ponta de flecha para a frente
THX = [(-0.15, -0.11), (0.15, -0.11), (0.20, -0.06), (0.20, 0.08), (0.10, 0.235), (-0.10, 0.235), (-0.20, 0.08),
       (-0.20, -0.06)]
# espinha central sobre o torax (segundo degrau), com o sensor na frente
HOOD = [(-0.06, -0.08), (0.06, -0.08), (0.08, -0.055), (0.08, 0.095), (0.04, 0.17), (-0.04, 0.17), (-0.08, 0.095),
        (-0.08, -0.055)]
# janela do sensor em seta (eco da janela do 76 mm)
WIN = [(-0.035, 0.065), (0.035, 0.065), (0.035, 0.09), (0.012, 0.125), (-0.012, 0.125), (-0.035, 0.09)]
THX_Z = (0.24, 0.47)
# abdomen em pipa com flancos retos ate o ferrao
ABD = [(0.0, -0.47), (0.135, -0.325), (0.135, -0.235), (0.07, -0.17), (-0.07, -0.17), (-0.135, -0.235),
       (-0.135, -0.325)]
ABD_Z = (0.22, 0.42)
# asa direita: lamina reta varrida para tras (mesma linguagem da caixa da esquerda)
WING = [(0.25, 0.0), (0.37, 0.0), (0.43, -0.06), (0.43, -0.17), (0.31, -0.35), (0.27, -0.33), (0.25, -0.22)]
WING_PNL = [(0.29, -0.04), (0.353, -0.04), (0.39, -0.077), (0.39, -0.158), (0.31, -0.29), (0.295, -0.284),
            (0.29, -0.216)]
WING_Z = (0.24, 0.40)
# caixa de cinta (lado esquerdo; definida aqui do lado direito e espelhada)
CAN = [(0.235, 0.0), (0.385, 0.0), (0.425, -0.04), (0.425, -0.19), (0.35, -0.31), (0.235, -0.31)]
# tampa e painel da tampa desenhados a mao (o deslocamento automatico gera arestas degeneradas)
CAN_LID = [(0.27, -0.035), (0.371, -0.035), (0.39, -0.054), (0.39, -0.18), (0.331, -0.275), (0.27, -0.275)]
CAN_PNL = [(0.30, -0.065), (0.36, -0.065), (0.36, -0.171), (0.314, -0.245), (0.30, -0.245)]
CAN_Z = (0.20, 0.34)


# ============================================================================ cabeca
def head(M, T="head", phase=0.0):
    """Cabeca: mandibulas, torax com sensor, cintura, abdomen-ferrao, asa (dir.) e caixa de cinta (esq.)."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    BR = brass()

    # anel giratorio e nucleo escuro
    B.cyl("ring", 0, 0, 0.04, 0.44, 0.08, KM, axis="Z", verts=64, bevel=0.01, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(0, 0, 0.415, 20, math.pi / 20) if y < -0.05]
    B.bolts("ringbolt", pts, 0.09, 0.014, S, tags=tags)
    B.plate("core", CORE, 0.06, 0.24, K, slope=0.03, tags=tags)

    # ---------------------------------------------------------------- mantelete escuro (saida do cano)
    m = B.plate("mantlet", MANT, 0.22, 0.38, KM, slope=0.02, tags=tags)
    B.cut(m, [B.box("mant_cut", 0, 0.37, 0.06, 0.10, 0.30, 0.6, K, bevel=0.0)])
    B.cyl("mcollar", 0, 0.40, ZB, 0.056, 0.03, KM, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("mcring", 0, 0.418, ZB, 0.052, 0.01, S, axis="Y", verts=8, bevel=0.002, tags=tags)

    # ---------------------------------------------------------------- mandibulas
    mz0, mz1 = MAND_Z
    for sx in (-1, 1):
        ma, mpn = shard_hand(f"mand{sx}", side(MAND, sx), side(MAND_PNL, sx), mz0, mz1, A, slope=0.03,
                             panel_h=0.03, tags=tags)
        # olho: fenda escura no ombro, paralela a lamina, com luz fraca no fundo
        ex, ey, er = sx * 0.31, 0.18, sx * -50
        for t in (ma, mpn):
            B.cut(t, [B.rbox(f"eyec{sx}{t.name}", ex, ey, 0.06, 0.026, mz1 - 0.06, 0.9, K, rot=er, bevel=0.0)])
        B.rbox(f"eyebed{sx}", ex, ey, 0.06, 0.026, mz1 - 0.07, mz1 - 0.058, M["black"], rot=er, bevel=0.0,
               tags=tags)
        B.rbox(f"eyeled{sx}", ex, ey, 0.04, 0.009, mz1 - 0.06, mz1 - 0.052, M["glow_dim"], rot=er, bevel=0.0,
               tags=tags)
        # pino da articulacao no vao entre mandibula e asa/caixa
        B.cyl(f"hinge{sx}", sx * 0.33, 0.03, 0.28, 0.022, 0.08, S, axis="X", verts=10, bevel=0.003, tags=tags)

    # ---------------------------------------------------------------- torax (cupula) com capuz do sensor
    tz0, tz1 = THX_Z
    th, tpn = B.shard("thorax", THX, tz0, tz1, A, slope=0.035, groove=0.02, panel_h=0.03, tags=tags)
    zt = tz1 + 0.03
    # sulco transversal: torax em duas placas (alinhado com o sulco do capuz)
    B.cut(tpn, [B.box("thx_band", 0, -0.015, 0.34, 0.016, zt - 0.06, 0.9, K, bevel=0.0)])
    B.box("thx_bandbed", 0, -0.015, 0.32, 0.016, tz1 - 0.002, tz1 + 0.004, K, bevel=0.0, tags=tags)
    hd = B.plate("hood", HOOD, zt - 0.005, zt + 0.045, A, slope=0.018, tags=tags)
    zh = zt + 0.045
    B.cut(hd, [B.loft("win_c", WIN, WIN, zh - 0.035, 1.2, K, bevel=0.0),
               B.box("hood_g", 0, -0.015, 0.20, 0.016, zh - 0.02, 1.2, K, bevel=0.0)])
    B.box("hood_gbed", 0, -0.015, 0.124, 0.016, zh - 0.022, zh - 0.017, K, bevel=0.0, tags=tags)
    B.loft("sensor_bed", WIN, WIN, zh - 0.045, zh - 0.03, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, 0.082, 0.044, 0.010, zh - 0.035, zh - 0.026, M["lens"], bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- cintura (acoplamento) e pistoes
    B.cyl("waist", 0, -0.14, 0.30, 0.04, 0.10, S, axis="Y", verts=10, bevel=0.004, tags=tags)
    B.cyl("waistc", 0, -0.14, 0.30, 0.05, 0.03, KM, axis="Y", verts=10, bevel=0.004, tags=tags)
    for sx in (-1, 1):
        B.cyl(f"piston{sx}", sx * 0.20, -0.14, 0.30, 0.016, 0.12, S, axis="Y", verts=10, yaw=sx * 40, tags=tags)
        B.cyl(f"pistonb{sx}", sx * 0.23, -0.17, 0.30, 0.024, 0.05, KM, axis="Y", verts=10, yaw=sx * 40, tags=tags)

    # ---------------------------------------------------------------- abdomen (ferrao)
    az0, az1 = ABD_Z
    ab, apn = B.shard("abd", ABD, az0, az1, A, slope=0.025, groove=0.015, panel_h=0.03, tags=tags)
    # listra de vespa: sulco transversal atravessando o painel
    B.cut(apn, [B.box("abd_band", 0, -0.24, 0.30, 0.012, az1 - 0.03, 0.9, K, bevel=0.0)])
    B.box("abd_bandbed", 0, -0.24, 0.20, 0.012, az1 - 0.002, az1 + 0.004, K, bevel=0.0, tags=tags)
    # fenda do ferrao com 2 pips grandes (paredes ~0.03 dentro da face de cima do painel)
    sy0, sy1, sw = -0.333, -0.266, 0.028
    zf = az1 + 0.03 - 0.09
    for t in (ab, apn):
        B.cut(t, [B.box(f"sting_c{t.name}", 0, (sy0 + sy1) / 2, sw, sy1 - sy0, zf, 0.9, K, bevel=0.0)])
    B.box("sting_bed", 0, (sy0 + sy1) / 2, sw, sy1 - sy0, zf - 0.01, zf + 0.004, M["black"], bevel=0.0, tags=tags)
    for i in range(2):
        B.box(f"sting_pip{i}", 0, sy0 + (i + 0.5) * (sy1 - sy0) / 2, 0.018, 0.022, zf, zf + 0.012, M["glow"],
              bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- asa direita (duas placas)
    wz0, wz1 = WING_Z
    wa, wpn = shard_hand("wing", WING, WING_PNL, wz0, wz1, A, slope=0.025, panel_h=0.03, tags=tags)
    B.cut(wpn, [B.box("vein", 0.34, -0.13, 0.20, 0.016, wz1 - 0.01, 0.9, K, bevel=0.0)])
    B.box("veinbed", 0.34, -0.13, 0.12, 0.016, wz1 - 0.002, wz1 + 0.004, K, bevel=0.0, tags=tags)
    # porta de ejecao no vao entre asa e abdomen
    ej = B.rbox("eject", 0.20, -0.27, 0.05, 0.10, 0.22, 0.32, KM, rot=-6, bevel=0.006, tags=tags)
    B.cut(ej, [B.rbox("ejc", 0.20, -0.27, 0.022, 0.07, 0.29, 0.5, K, rot=-6, bevel=0.0)])

    # ---------------------------------------------------------------- baia de exaustao mini (vao esquerdo de tras)
    vx, vy, vr = -0.19, -0.27, 6
    B.rbox("vent_bay", vx, vy, 0.052, 0.096, 0.22, 0.27, M["black"], rot=vr, bevel=0.0, tags=tags)
    B.rbox("vent_rim", vx, vy, 0.066, 0.11, 0.20, 0.262, KM, rot=vr, bevel=0.004, tags=tags)
    ux, uy = -math.sin(math.radians(vr)), math.cos(math.radians(vr))
    for i in range(3):
        t = -0.03 + i * 0.03
        B.rbox(f"louver{i}", vx + ux * t, vy + uy * t, 0.046, 0.012, 0.24, 0.285, KM, rot=vr, bevel=0.003,
               tags=tags)

    # ---------------------------------------------------------------- caixa de cinta listrada (esquerda)
    cz0, cz1 = CAN_Z
    cpoly = side(CAN, -1)
    B.plate("can", cpoly, cz0, cz1, KM, slope=0.02, tags=tags)
    la, lpn = shard_hand("canlid", side(CAN_LID, -1), side(CAN_PNL, -1), cz1 - 0.004, cz1 + 0.05, A, slope=0.018,
                         panel_h=0.025, tags=tags)
    # listras transversais escuras (tampa em 4 ripas) ate o corpo escuro da caixa
    for t in (la, lpn):
        B.cut(t, [B.box(f"rib{i}{t.name}", -0.33, y, 0.26, 0.028, cz1 - 0.012, 0.9, K, bevel=0.0)
                  for i, y in enumerate((-0.088, -0.155, -0.222))])
    # trava de aco na frente da caixa
    B.box("latch", -0.31, -0.012, 0.07, 0.022, cz1, cz1 + 0.035, S, bevel=0.005, tags=tags)
    # bandeja de alimentacao: sai da caixa e entra na culatra pelo vao entre torax e mandibula esquerda
    tray_rot = -25
    tx0, ty0, tlen = -0.235, 0.03, 0.27
    ux, uy = -math.sin(math.radians(tray_rot)), math.cos(math.radians(tray_rot))
    tcx, tcy = tx0 + ux * tlen / 2, ty0 + uy * tlen / 2
    B.rbox("tray", tcx, tcy, 0.065, tlen, 0.22, 0.30, KM, rot=tray_rot, bevel=0.006, tags=tags)
    for i in range(5):
        t = 0.07 + i * 0.04
        B.cyl(f"cart{i}", tx0 + ux * t, ty0 + uy * t, 0.315, 0.012, 0.05, BR, axis="Y", verts=8, bevel=0.002,
              yaw=tray_rot + 90, tags=tags)
    # trilhos-guia escuros cobrindo as pontas dos cartuchos
    nx, ny = uy, -ux
    for k, sgn in enumerate((-1, 1)):
        B.rbox(f"trayrail{k}", tcx + nx * sgn * 0.026, tcy + ny * sgn * 0.026, 0.016, tlen, 0.30, 0.335, KM,
               rot=tray_rot, bevel=0.004, tags=tags)


# ============================================================================ cano
def barrel(M, L=0.90, T="barrel", phase=0.0):
    """Cano fino refrigerado a ar: raiz em y=0, boca em y=L, centrado em x=0."""
    tags = (T,)
    hot = (T, "hot")
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = ZB
    # culatra escura (fica dentro do mantelete mesmo no recuo)
    B.cyl("b_root", 0, 0.055, z, 0.048, 0.11, KM, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("b_rootring", 0, 0.112, z, 0.05, 0.016, S, axis="Y", verts=8, bevel=0.003, tags=tags)
    # camisa de refrigeracao clara, duas fileiras desencontradas de fendas (o nucleo escuro aparece)
    y0j, y1j = 0.12, 0.56
    ym = (y0j + y1j) / 2
    jk = B.cyl("b_jacket", 0, ym, z, 0.042, y1j - y0j, A, axis="Y", verts=8, bevel=0.005, tags=tags)
    holes = []
    for seg0 in (y0j + 0.03, ym + 0.022):
        for k in range(3):
            for sxh, dy in ((-1, 0.0), (1, 0.03)):
                yy = seg0 + 0.02 + k * 0.06 + dy
                if yy + 0.02 < (ym - 0.012 if seg0 < ym else y1j - 0.025):
                    holes.append(B.box(f"b_h{len(holes)}", sxh * 0.016, yy, 0.016, 0.04, z + 0.006, z + 0.2, K,
                                       bevel=0.0))
    B.cut(jk, holes)
    B.cyl("b_core", 0, ym, z, 0.028, y1j - y0j, K, axis="Y", verts=12, tags=tags)
    for i, yy in enumerate((y0j + 0.012, ym, y1j - 0.012)):
        B.cyl(f"b_collar{i}", 0, yy, z, 0.047, 0.022, AM, axis="Y", verts=8, bevel=0.004, tags=tags)
    # tubo de aco exposto
    yt1 = L - 0.19
    B.cyl("b_tube", 0, (y1j + yt1) / 2, z, 0.021, yt1 - y1j + 0.02, S, axis="Y", verts=8, bevel=0.003, tags=tags)
    B.cyl("b_tubering", 0, y1j + 0.07, z, 0.026, 0.016, AM, axis="Y", verts=8, bevel=0.003, tags=tags)
    # quebra-chamas claro facetado em ponta de flecha (afunila atras ate o tubo), portas transversais escuras
    y0f = L - 0.20
    fh = [(-0.024, y0f), (0.024, y0f), (0.048, y0f + 0.045), (0.048, L - 0.06), (0.016, L), (-0.016, L),
          (-0.048, L - 0.06), (-0.048, y0f + 0.045)]
    br = B.plate("b_fh", fh, z - 0.042, z + 0.042, A, slope=0.012, tags=tags)
    pc = [B.box(f"b_fhc{i}", 0, y0f + 0.07 + i * 0.036, 0.15, 0.015, z + 0.01, z + 0.2, K, bevel=0.0)
          for i in range(3)]
    pc.append(B.box("b_bore_c", 0, L - 0.005, 0.02, 0.04, z - 0.02, z + 0.2, K, bevel=0.0))
    B.cut(br, pc)
    # fundo escuro das portas: e ele que esquenta
    B.box("b_fh_core", 0, y0f + 0.106, 0.07, 0.11, z - 0.035, z + 0.012, K, bevel=0.0, tags=hot)


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto 1x1: placa verde (pintura), anel da torre no centro, chevrons de vespa em cada canto e 1 parafuso."""
    tags = (T,)
    green = B.mat_roof_green()
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    rr = RING_R
    B.box("deck_under", 0, 0, 1, 1, -0.05, 0.02, K, bevel=0.0, tags=tags)
    poly = B.rpoly(0, 0, 0.94, 0.94, 0, chamfer=0.06)
    dk, pnl = B.shard("deck", poly, 0.0, 0.06, green, slope=0.02, groove=0.03, panel_h=0.02, tags=tags)
    # chevrons de vespa: dois V aninhados por canto, vertice apontando para o anel, cortados ate o fundo escuro
    cuts = []
    beds = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for k, dd in enumerate((0.345, 0.385)):
                vx, vy = sx * dd, sy * dd
                for j, a in enumerate((45 + 58, 45 - 58)):
                    # braco: do vertice para fora, angulo a (graus) no quadrante (+,+), espelhado para os outros
                    dxa, dya = math.cos(math.radians(a)) * sx, math.sin(math.radians(a)) * sy
                    ln = 0.16
                    cx, cy = vx + dxa * ln / 2, vy + dya * ln / 2
                    rot = math.degrees(math.atan2(dya, dxa)) - 90
                    nm = f"chev{sx}{sy}{k}{j}"
                    cuts.append((nm, cx, cy, ln, rot))
                    beds.append((nm, cx, cy, ln, rot))
    for t in (dk, pnl):
        B.cut(t, [B.rbox(f"{nm}{t.name}", cx, cy, 0.026, ln + 0.026, 0.03, 0.2, K, rot=rot, bevel=0.0)
                  for nm, cx, cy, ln, rot in cuts])
    for nm, cx, cy, ln, rot in beds:
        B.rbox(nm + "_bed", cx, cy, 0.026, ln + 0.026, 0.024, 0.032, K, rot=rot, bevel=0.0, tags=tags)
    # anel da torre (sem pintura): colar escuro estreito, deixa o verde aparecer nas bordas
    B.torus("ringbear", 0, 0, 0.08, rr + 0.005, 0.035, KM, tags=tags)
    B.cyl("ringhole", 0, 0, 0.05, rr - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    # um parafuso de aco no sulco de cada canto
    B.bolts("cb", [(sx * 0.418, sy * 0.418) for sx in (-1, 1) for sy in (-1, 1)], 0.065, 0.016, S, tags=tags)


def floor(M, T="floor"):
    """Piso: anel no centro, assento do atirador, console a frente, caixa de cinta a esquerda e carregadores."""
    from bsgen.common import crew_positions
    tags = (T,)
    w, h = PART["size"]
    pv = PART["pivot"]
    rr = RING_R
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    BR = brass()
    B.box("fl_base", 0, 0, w, h, -0.05, 0.0, K, bevel=0.0, tags=tags)
    B.box("fl0", 0, 0, 0.92, 0.92, 0.0, 0.03, KM, bevel=0.01, tags=tags)
    B.torus("fl_ring", 0, 0, 0.05, rr * 0.88, 0.035, AM, tags=tags)
    # sapatas escuras parafusadas nas diagonais do anel
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        cx, cy = math.cos(a) * rr * 1.02, math.sin(a) * rr * 1.02
        B.rbox(f"fl_pad{k}", cx, cy, 0.07, 0.07, 0.03, 0.055, AM, rot=45, bevel=0.008, tags=tags)
        B.bolts(f"fl_padb{k}", [(cx, cy)], 0.06, 0.012, S, tags=tags)
    B.box("fl_led_t", 0, rr * 0.88, 0.16, 0.03, 0.06, 0.09, M["glow_dim"], bevel=0.0, tags=tags)
    for i, (cx, cy, _r) in enumerate(crew_positions(w, h, 1, pv)):
        x, y = cx - w / 2, h / 2 - cy
        B.box(f"seatb{i}", x, y + 0.02, 0.28, 0.26, 0.0, 0.05, S, bevel=0.012, tags=tags)
        B.box(f"seat{i}", x, y + 0.03, 0.22, 0.18, 0.05, 0.13, A, bevel=0.03, tags=tags)
        B.box(f"seatbk{i}", x, y - 0.10, 0.24, 0.06, 0.05, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"console{i}", x, y + 0.27, 0.30, 0.10, 0.0, 0.20, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.27, 0.14, 0.03, 0.20, 0.215, M["screen"], bevel=0.0, tags=tags)
    # caixa de cinta a esquerda com cartuchos a mostra
    B.box("can", -0.33, -0.02, 0.15, 0.34, 0.0, 0.16, KM, bevel=0.012, tags=tags)
    B.box("canlid", -0.33, -0.11, 0.12, 0.14, 0.16, 0.185, AM, bevel=0.008, tags=tags)
    for k in range(4):
        B.cyl(f"cancart{k}", -0.33, 0.02 + k * 0.03, 0.175, 0.011, 0.10, BR, axis="X", verts=8, bevel=0.002,
              tags=tags)
    # carregadores de reserva a direita
    for i in range(2):
        yy = -0.12 + i * 0.16
        B.box(f"mag{i}", 0.33, yy, 0.13, 0.12, 0.0, 0.14, KM, bevel=0.01, tags=tags)
        B.box(f"magled{i}", 0.33, yy, 0.07, 0.022, 0.14, 0.16, M["glow_dim"], bevel=0.0, tags=tags)
