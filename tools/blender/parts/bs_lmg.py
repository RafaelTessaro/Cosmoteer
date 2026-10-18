"""Metralhadora Leve de Conves ("Marimbondo") - a menor arma do mod (1x1), familia do 76 mm.

Vista de cima le como um marimbondo: duas mandibulas claras em gancho que avancam e fecham sobre a raiz do cano
(com o "olho" numa fenda de luz fraca), cupula central facetada (o torax) com janela de sensor, cintura fina
(acoplamento de aco no vao escuro), abdomen em ponta para tras (o ferrao) com fenda longitudinal e 2 pips ambar.
Do lado direito uma asa curta varrida para tras; do esquerdo a caixa de cinta (corpo escuro, tampa clara com
nervuras) com a bandeja de cartuchos de latao correndo pelo vao ate a culatra. Tudo dentro de um raio de ~0.47
do pivo (a cabeca nao sai do tile quando gira). Cano fino: culatra escura, camisa clara perfurada, tubo de aco
exposto e quebra-chamas claro facetado em ponta com portas escuras.
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
        "heat": [0.35, 0.18, 0.06],   # calor leve so no quebra-chamas
        "interval": 0.04,
    },
    "lights": [                    # luz dinamica no ferrao (coordenadas da cabeca)
        {"at": [0.0, -0.33], "size": 0.5, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "single",
}

RING_R = PART["ring_r"]
ZB = 0.40                          # altura do eixo do cano


def side(poly, sx):
    return poly if sx > 0 else Mo.mirror(poly)


def brass():
    """Latao dos cartuchos (so na bandeja de alimentacao)."""
    return B.mat_metal("bs_brass", (0.56, 0.33, 0.075), rough=0.30, metal=1.0)


def dim_pips(T, prefix, M):
    """Troca os pips de uma fenda para a luz fraca (orcamento de brilho)."""
    for o in [o for o in B.objects_with(T) if o.name.startswith(prefix)]:
        o.data.materials[0] = M["glow_dim"]


# ============================================================================ planta (cabeca), lado direito
CORE = [(-0.24, -0.40), (0.24, -0.40), (0.38, -0.25), (0.38, 0.18), (0.22, 0.36), (-0.22, 0.36), (-0.38, 0.18),
        (-0.38, -0.25)]
MANT = [(-0.075, 0.16), (0.075, 0.16), (0.09, 0.24), (0.075, 0.40), (-0.075, 0.40), (-0.09, 0.24)]
# mandibula direita: ombro atras, aresta externa convexa, ponta em gancho para dentro na raiz do cano
MAND = [(0.25, 0.08), (0.36, 0.05), (0.43, 0.13), (0.40, 0.23), (0.32, 0.32), (0.20, 0.41), (0.12, 0.45),
        (0.11, 0.40), (0.15, 0.33), (0.20, 0.26), (0.23, 0.17)]
MAND_Z = (0.26, 0.44)
# torax (cupula central) em ponta de flecha para a frente
THX = [(-0.15, -0.11), (0.15, -0.11), (0.20, -0.06), (0.20, 0.08), (0.10, 0.235), (-0.10, 0.235), (-0.20, 0.08),
       (-0.20, -0.06)]
# espinha central sobre o torax (segundo degrau), com o sensor na frente
HOOD = [(-0.055, -0.075), (0.055, -0.075), (0.07, -0.05), (0.07, 0.10), (0.035, 0.168), (-0.035, 0.168),
        (-0.07, 0.10), (-0.07, -0.05)]
THX_Z = (0.24, 0.47)
# abdomen em gota com ferrao para tras
ABD = [(0.0, -0.468), (0.11, -0.35), (0.13, -0.285), (0.105, -0.21), (0.055, -0.172), (-0.055, -0.172),
       (-0.105, -0.21), (-0.13, -0.285), (-0.11, -0.35)]
ABD_Z = (0.22, 0.42)
# asa direita varrida para tras (ponta atras)
WING = [(0.25, 0.0), (0.36, 0.0), (0.435, -0.07), (0.415, -0.19), (0.30, -0.365), (0.255, -0.31), (0.265, -0.19),
        (0.24, -0.10)]
# painel interno da asa desenhado a mao (o deslocamento automatico perde a ponta)
WING_PNL = [(0.286, -0.04), (0.344, -0.04), (0.392, -0.085), (0.377, -0.175), (0.343, -0.225), (0.302, -0.225),
            (0.305, -0.186), (0.281, -0.097)]
WING_Z = (0.24, 0.42)
# caixa de cinta (lado esquerdo; definida aqui do lado direito e espelhada)
CAN = [(0.25, 0.0), (0.38, 0.0), (0.42, -0.05), (0.42, -0.19), (0.33, -0.32), (0.26, -0.32), (0.24, -0.27),
       (0.24, -0.04)]
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
        ma, mpn = B.shard(f"mand{sx}", side(MAND, sx), mz0, mz1, A, slope=0.03, groove=0.02, panel_h=0.03,
                          tags=tags)
        # olho: fenda escura inclinada com luz fraca
        ex, ey, er = sx * 0.335, 0.19, sx * -52
        for t in (ma, mpn):
            if t is not None:
                B.cut(t, [B.rbox(f"eyec{sx}{t.name}", ex, ey, 0.10, 0.026, mz1 - 0.06, 0.9, K, rot=er, bevel=0.0)])
        B.rbox(f"eyebed{sx}", ex, ey, 0.10, 0.026, mz1 - 0.07, mz1 - 0.058, M["black"], rot=er, bevel=0.0,
               tags=tags)
        B.rbox(f"eyeled{sx}", ex, ey, 0.055, 0.009, mz1 - 0.06, mz1 - 0.052, M["glow_dim"], rot=er, bevel=0.0,
               tags=tags)
        # pino da articulacao no vao entre mandibula e asa/caixa
        B.cyl(f"hinge{sx}", sx * 0.33, 0.035, 0.28, 0.022, 0.08, S, axis="X", verts=10, bevel=0.003, tags=tags)

    # ---------------------------------------------------------------- torax (cupula) com capuz do sensor
    tz0, tz1 = THX_Z
    th, tpn = B.shard("thorax", THX, tz0, tz1, A, slope=0.035, groove=0.02, panel_h=0.03, tags=tags)
    zt = tz1 + 0.03
    hd = B.plate("hood", HOOD, zt - 0.005, zt + 0.045, A, slope=0.018, tags=tags)
    win = [(-0.03, 0.07), (0.03, 0.07), (0.03, 0.095), (0.015, 0.118), (-0.015, 0.118), (-0.03, 0.095)]
    zh = zt + 0.045
    B.cut(hd, [B.loft("win_c", win, win, zh - 0.035, 1.2, K, bevel=0.0),
               B.box("hood_g", 0, -0.015, 0.20, 0.014, zh - 0.02, 1.2, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, zh - 0.045, zh - 0.03, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, 0.084, 0.04, 0.010, zh - 0.035, zh - 0.026, M["lens"], bevel=0.0, tags=tags)
    # linhas de painel nas laterais do torax (dos dois lados da espinha)
    if tpn is not None:
        B.cut(tpn, [B.rbox(f"thx_pl{sx}", sx * 0.115, 0.115, 0.012, 0.09, zt - 0.06, 0.9, K, rot=sx * 34, bevel=0.0)
                    for sx in (-1, 1)])

    # ---------------------------------------------------------------- cintura (acoplamento) e pistoes
    B.cyl("waist", 0, -0.135, 0.30, 0.04, 0.10, S, axis="Y", verts=10, bevel=0.004, tags=tags)
    B.cyl("waistc", 0, -0.135, 0.30, 0.05, 0.03, KM, axis="Y", verts=10, bevel=0.004, tags=tags)
    for sx in (-1, 1):
        B.cyl(f"piston{sx}", sx * 0.20, -0.15, 0.30, 0.016, 0.12, S, axis="Y", verts=10, yaw=sx * 40, tags=tags)
        B.cyl(f"pistonb{sx}", sx * 0.23, -0.18, 0.30, 0.024, 0.05, KM, axis="Y", verts=10, yaw=sx * 40, tags=tags)

    # ---------------------------------------------------------------- abdomen (ferrao)
    az0, az1 = ABD_Z
    ab, apn = B.shard("abd", ABD, az0, az1, A, slope=0.03, groove=0.018, panel_h=0.03, tags=tags)
    # listra de vespa: sulco transversal atravessando o painel
    if apn is not None:
        B.cut(apn, [B.box("abd_band", 0, -0.252, 0.30, 0.016, az1 - 0.03, 0.9, K, bevel=0.0)])
    # fenda do ferrao com 2 pips
    Mo.slot_with_pips("sting", 0, -0.36, -0.278, 0.03, az1 + 0.03, 2, M, tags, target=[ab, apn], depth=0.09)

    # ---------------------------------------------------------------- asa direita
    wz0, wz1 = WING_Z
    B.plate("wing", WING, wz0, wz1, A, slope=0.025, tags=tags)
    wpn = B.plate("wing_pnl", WING_PNL, wz1 - 0.004, wz1 + 0.03, A, slope=0.012, bevel=0.008, tags=tags)
    # sulco transversal: asa em dois segmentos
    B.cut(wpn, [B.rbox("vein", 0.34, -0.128, 0.16, 0.014, wz1 + 0.005, 0.9, K, rot=-8, bevel=0.0)])
    # porta de ejecao no vao entre asa e abdomen
    ej = B.rbox("eject", 0.215, -0.27, 0.05, 0.10, 0.22, 0.32, KM, rot=-15, bevel=0.006, tags=tags)
    B.cut(ej, [B.rbox("ejc", 0.215, -0.27, 0.022, 0.07, 0.29, 0.5, K, rot=-15, bevel=0.0)])

    # ---------------------------------------------------------------- caixa de cinta (esquerda)
    cz0, cz1 = CAN_Z
    cpoly = side(CAN, -1)
    B.plate("can", cpoly, cz0, cz1, KM, slope=0.02, tags=tags)
    lid_poly = B.offset_poly(cpoly, 0.03)
    la, lpn = B.shard("canlid", lid_poly, cz1 - 0.004, cz1 + 0.05, A, slope=0.025, groove=0.018, panel_h=0.025,
                      tags=tags)
    # nervuras transversais da tampa
    for t in (la, lpn):
        if t is not None:
            B.cut(t, [B.box(f"rib{i}{t.name}", -0.33, y, 0.22, 0.018, cz1 + 0.02, 0.9, K, bevel=0.0)
                      for i, y in enumerate((-0.10, -0.19))])
    # contador de municao na borda de fora
    Mo.slot_with_pips("cnt", -0.385, -0.17, -0.07, 0.026, cz1 + 0.075, 2, M, tags, target=[la, lpn], depth=0.07)
    dim_pips(T, "cnt_pip", M)
    # alca de aco dobrada sobre a tampa (le como caixa de municao)
    zl = cz1 + 0.075
    B.box("handle", -0.31, -0.145, 0.012, 0.13, zl + 0.012, zl + 0.03, S, bevel=0.004, tags=tags)
    for i, y in enumerate((-0.21, -0.08)):
        B.box(f"handle_f{i}", -0.31, y, 0.03, 0.02, zl - 0.01, zl + 0.03, KM, bevel=0.004, tags=tags)
    B.box("latch", -0.30, -0.012, 0.07, 0.022, cz1, cz1 + 0.04, S, bevel=0.005, tags=tags)
    # bandeja de alimentacao com cartuchos no vao entre torax e mandibula esquerda
    ty0, ty1 = 0.02, 0.27
    tx = -0.215
    tray_rot = -14
    B.rbox("tray", tx + 0.02, (ty0 + ty1) / 2, 0.06, ty1 - ty0, 0.22, 0.30, KM, rot=tray_rot, bevel=0.006,
           tags=tags)
    n = 0
    y = ty0 + 0.02
    while y < ty1 - 0.01:
        t = (y - (ty0 + ty1) / 2)
        cx = tx + 0.02 - math.sin(math.radians(tray_rot)) * t
        B.cyl(f"cart{n}", cx, y, 0.32, 0.012, 0.05, BR, axis="X", verts=8, bevel=0.002, tags=tags)
        n += 1
        y += 0.03


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
    # camisa de refrigeracao clara, perfurada em duas fileiras desencontradas
    y0j, y1j = 0.12, 0.56
    jk = B.cyl("b_jacket", 0, (y0j + y1j) / 2, z, 0.042, y1j - y0j, A, axis="Y", verts=8, bevel=0.005,
               tags=tags)
    holes = []
    for i in range(6):
        yy = y0j + 0.055 + i * 0.062
        holes.append(B.box(f"b_h{i}", 0, yy, 0.024, 0.03, z + 0.02, z + 0.2, K, bevel=0.0))
    B.cut(jk, holes)
    B.cyl("b_core", 0, (y0j + y1j) / 2, z, 0.028, y1j - y0j, K, axis="Y", verts=12, tags=tags)
    for i, yy in enumerate((y0j + 0.012, y1j - 0.012)):
        B.cyl(f"b_collar{i}", 0, yy, z, 0.047, 0.022, AM, axis="Y", verts=8, bevel=0.004, tags=tags)
    # tubo de aco exposto
    yt1 = L - 0.13
    B.cyl("b_tube", 0, (y1j + yt1) / 2, z, 0.021, yt1 - y1j, S, axis="Y", verts=8, bevel=0.003, tags=tags)
    B.cyl("b_tubering", 0, y1j + 0.10, z, 0.026, 0.016, AM, axis="Y", verts=8, bevel=0.003, tags=tags)
    # quebra-chamas claro facetado em ponta, com portas transversais escuras
    yb = L - 0.07
    fh = [(-0.028, yb - 0.09), (0.028, yb - 0.09), (0.052, yb - 0.03), (0.052, yb + 0.035), (0.024, yb + 0.07),
          (-0.024, yb + 0.07), (-0.052, yb + 0.035), (-0.052, yb - 0.03)]
    br = B.plate("b_fh", fh, z - 0.042, z + 0.042, A, slope=0.012, tags=tags)
    pc = [B.box(f"b_fhc{i}", 0, yb - 0.03 + i * 0.038, 0.15, 0.015, z + 0.01, z + 0.2, K, bevel=0.0)
          for i in range(2)]
    pc.append(B.box("b_bore_c", 0, L - 0.005, 0.022, 0.04, z - 0.02, z + 0.2, K, bevel=0.0))
    B.cut(br, pc)
    # fundo escuro das portas: e ele que esquenta
    B.box("b_fh_core", 0, yb - 0.01, 0.085, 0.10, z - 0.035, z + 0.012, K, bevel=0.0, tags=hot)


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto 1x1: placa verde, anel da torre no centro, tampas de canto com chevron e parafusos."""
    tags = (T,)
    green = B.mat_roof_green()
    K, KM, AM, S = M["core"], M["core_mid"], M["armor_mid"], M["steel"]
    rr = RING_R
    B.box("deck_under", 0, 0, 1, 1, -0.05, 0.02, K, bevel=0.0, tags=tags)
    poly = B.rpoly(0, 0, 0.94, 0.94, 0, chamfer=0.07)
    B.shard("deck", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02, tags=tags)
    B.torus("ringbear", 0, 0, 0.08, rr + 0.02, 0.045, KM, tags=tags)
    B.cyl("ringhole", 0, 0, 0.05, rr - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tri = [(sx * 0.425, sy * 0.425), (sx * 0.27, sy * 0.425), (sx * 0.425, sy * 0.27)]
            if sx * sy < 0:
                tri = list(reversed(tri))
            cp = B.plate(f"corner{sx}{sy}", tri, 0.06, 0.10, AM, slope=0.015, tags=tags)
            # chevron (emblema da vespa) apontando para o anel
            B.cut(cp, [B.rbox(f"cchev{sx}{sy}{k}", sx * 0.37 + dx, sy * 0.37 + dy, 0.012, 0.07, 0.09, 0.2, K,
                              rot=r, bevel=0.0)
                       for k, (dx, dy, r) in enumerate(((sx * -0.018, sy * 0.012, sx * sy * 0),
                                                        (sx * 0.012, sy * -0.018, 90)))])
            B.bolts(f"cb{sx}{sy}", [(sx * 0.40, sy * 0.40)], 0.10, 0.016, S, tags=tags)
    # parafusos do anel nos cantos
    pts = [(x, y) for x, y in B.ring_points(0, 0, rr + 0.09, 24, math.pi / 24)
           if abs(x) < 0.44 and abs(y) < 0.44 and abs(abs(x) - abs(y)) > 0.05]
    B.bolts("rb", pts, 0.1, 0.016, S, tags=tags)


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
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        B.rbox(f"fl_chev{k}", math.cos(a) * rr * 1.02, math.sin(a) * rr * 1.02, 0.07, 0.07, 0.03, 0.06, A, rot=45,
               bevel=0.008, tags=tags)
    B.box("fl_led_t", 0, rr * 0.88, 0.16, 0.03, 0.06, 0.09, M["glow"], bevel=0.0, tags=tags)
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
