"""Autocanhao de Conves 20 mm ("Carcara") - torre baixa em cunha com cabeca de gaviao vista de cima, 2x2.

Mesma familia do 76 mm (nucleo escuro + placas claras com vaos), com identidade de carcara:
planta em losango (mais larga na linha dos olhos, afina para o bico e para a nuca); bico em proa entre os
canos (cera cinza com narinas escuras + bico claro facetado com crista central e dente tomial de cada lado),
bochechas claras com o olho do carcara (recesso escuro em gota, fenda de lente ambar ao longo da cauda e
viseira de aco), garras em lamina com fenda de luz fraca que avancam ate a raiz de cada cano (pistao no vao
bochecha/garra), coroa central com canal sensor escuro em seta, penas varridas para tras na nuca (lamina de
fora com degrau e fenda de pips, nivel de baixo por dentro), baia de exaustao entre as penas e calhas de
alimentacao nos vaos ate as culatras.
Canos: culatra escura, camisa escura com fendas e brasa fraca, luva clara facetada com canal, extrator de
gases facetado e colares, freio leve em ponta de flecha com fendas transversais escuras. Recuo alternado.
"""

import math

import bmesh
import bpy

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_autocannon_20",
    "kind": "gun",
    "size": [2, 2],
    "pivot": [1.0, 0.92],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 2.00,            # lado do quadrado do sprite da torre (bico ate +0.955, penas ate -0.86)
    "ring_r": 0.74,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "collider": 0.86,
    "barrels": {
        "ys": [-0.22, 0.22],       # dois canos finos saindo das bochechas (sprites de 0.24 sem sobrepor)
        "root": 0.30,              # pivo -> raiz do cano (culatra escura dentro do berco)
        "length": 1.50,            # raiz -> boca
        "width": 0.24,             # largura do sprite de cada cano (cabe o freio)
        "pad": 0.12,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.10, 0.065, 0.035, 0.012],
        "heat": [0.6, 0.35, 0.15, 0.05],    # calor leve so no fundo das fendas do freio e no colar da boca
        "interval": 0.045,
    },
    "lights": [                    # luzes dinamicas em coordenadas da cabeca
        {"at": [0.0, -0.72], "size": 0.9, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "alternate",
}

RING_R = PART["ring_r"]
YS = PART["barrels"]["ys"]
ZB = 0.46                          # altura do eixo dos canos


def sym(right):
    """Poligono simetrico a partir da metade direita (de tras para a frente)."""
    return list(right) + Mo.mirror(right)


# ============================================================================ planta (lado DIREITO, x > 0)
# nucleo escuro em losango: mais largo na linha dos olhos, afina para o bico e para a nuca
CORE = sym([(0.24, -0.85), (0.44, -0.82), (0.60, -0.62), (0.74, -0.36), (0.82, -0.12), (0.86, 0.10), (0.72, 0.36),
            (0.56, 0.58), (0.40, 0.82)])
# berco escuro dos dois canos (sob o bico, entre as garras)
CRADLE = [(-0.37, 0.16), (0.37, 0.16), (0.38, 0.22), (0.38, 0.74), (0.32, 0.84), (-0.32, 0.84), (-0.38, 0.74),
          (-0.38, 0.22)]
# bochecha (a parte mais larga da cabeca, com o olho): frente em diagonal rasa, vao de 0.08 ate a garra
CHEEK = [(0.39, 0.42), (0.39, -0.18), (0.46, -0.26), (0.78, -0.17), (0.89, 0.02), (0.89, 0.14), (0.79, 0.27)]
# garra em lamina: base paralela a frente da bochecha, borda de dentro paralela ao berco, ponta para a frente
# junto ao cano e borda de fora varrida para tras (continua a cunha da bochecha ate o bico)
TALON = [(0.74, 0.375), (0.43, 0.49), (0.36, 0.58), (0.345, 0.66), (0.345, 0.82), (0.365, 0.905), (0.395, 0.915),
         (0.43, 0.80), (0.52, 0.64), (0.66, 0.48)]
# coroa (espinha central): estreita atras (nuca), frente em ponta que entra na cera do bico
CROWN = [(-0.15, -0.62), (0.15, -0.62), (0.27, -0.44), (0.27, -0.10), (0.10, 0.22), (-0.10, 0.22), (-0.27, -0.10),
         (-0.27, -0.44)]
# canal sensor escuro em seta longa e estreita na coroa (aponta para o bico)
CAP = [(-0.07, -0.40), (0.07, -0.40), (0.07, -0.08), (0.0, 0.03), (-0.07, -0.08)]
# pena de fora: lamina varrida para tras com degrau na borda de tras (ponta dentro do raio 1.0)
FEATHER1 = [(0.45, -0.33), (0.77, -0.24), (0.80, -0.31), (0.68, -0.56), (0.58, -0.70), (0.52, -0.70),
            (0.47, -0.82), (0.43, -0.77)]
# pena de dentro: nivel mais baixo, enfiada sob a de fora (so o degrau de dentro aparece)
FEATHER2 = [(0.28, -0.50), (0.48, -0.44), (0.50, -0.66), (0.40, -0.78), (0.29, -0.75)]
# cera do bico (base e topo)
CERE_B = [(-0.125, 0.10), (0.125, 0.10), (0.13, 0.30), (-0.13, 0.30)]
CERE_T = [(-0.075, 0.12), (0.075, 0.12), (0.08, 0.29), (-0.08, 0.29)]
# bico: estacoes (y, meia largura embaixo, meia largura no topo, z da borda do topo, z da crista); dente tomial
# em 0.655-0.705; ponta (y embaixo, y em cima, z em cima)
BILL = [(0.315, 0.128, 0.060, 0.600, 0.632), (0.50, 0.127, 0.058, 0.595, 0.626), (0.64, 0.108, 0.046, 0.572, 0.604),
        (0.655, 0.082, 0.034, 0.566, 0.598), (0.705, 0.092, 0.038, 0.556, 0.588), (0.84, 0.058, 0.022, 0.512, 0.540)]
BILL_TIP = (0.955, 0.895, 0.478)
# olho (lado direito): centro do recesso, raio, cauda para tras e para fora (gota)
EYE = dict(c=(0.585, 0.11), r=0.068, tail=0.18, ang=-37.0)
TALON_AX = 22.8                    # inclinacao do eixo longo da garra (graus, lado direito)
GAP_YAW = 69.4                     # direcao do vao bochecha/garra (graus, lado direito)


def teardrop(cx, cy, r, tail, ang_deg, n=7):
    """Gota: frente redonda (arco) em volta de (cx, cy) e ponta a 'tail' na direcao ang_deg."""
    a0 = math.radians(ang_deg)
    pts = [(cx + r * math.cos(a0 + math.radians(48 + k * (264 / (n - 1)))),
            cy + r * math.sin(a0 + math.radians(48 + k * (264 / (n - 1))))) for k in range(n)]
    return pts + [(cx + tail * math.cos(a0), cy + tail * math.sin(a0))]


def side_poly(poly, sx):
    return poly if sx > 0 else Mo.mirror(poly)


# ============================================================================ utilidades
def beak(name, st, tip, z0, mat, bevel=0.01, tags=()):
    """Bico com crista central (duas facetas no topo). st = [(y, hb, ht, zs, zr)] de tras para a frente."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bl, br, tl, tr, rg = [], [], [], [], []
    for y, hb, ht, zs, zr in st:
        bl.append(bm.verts.new((-hb, y, z0)))
        br.append(bm.verts.new((hb, y, z0)))
        tl.append(bm.verts.new((-ht, y, zs)))
        tr.append(bm.verts.new((ht, y, zs)))
        rg.append(bm.verts.new((0.0, y, zr)))
    yb, yt, zt = tip
    pb = bm.verts.new((0.0, yb, z0))
    pt = bm.verts.new((0.0, yt, zt))
    F = bm.faces.new
    F(br + [pb] + list(reversed(bl)))
    F([bl[0], br[0], tr[0], rg[0], tl[0]])
    for i in range(len(st) - 1):
        F([br[i], br[i + 1], tr[i + 1], tr[i]])
        F([bl[i + 1], bl[i], tl[i], tl[i + 1]])
        F([rg[i], tr[i], tr[i + 1], rg[i + 1]])
        F([tl[i], rg[i], rg[i + 1], tl[i + 1]])
    F([br[-1], pb, pt, tr[-1]])
    F([pb, bl[-1], tl[-1], pt])
    F([rg[-1], tr[-1], pt])
    F([tl[-1], rg[-1], pt])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = B._link(bpy.data.objects.new(name, me))
    if bevel > 0:
        md = ob.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = 1
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(30)
    ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


def slot_rot(name, cx, cy, length, w, ztop, n, M, tags, rot, targets, depth=0.07, mat=None):
    """Fenda escura girada (eixo longo = y local girado por rot) com n pips, recortada nos alvos."""
    for t in targets:
        if t is not None:
            B.cut(t, [B.rbox(name + "_cut", cx, cy, w, length, ztop - depth, ztop + 0.3, M["black"], rot=rot,
                             bevel=0.0)])
    B.rbox(name + "_bed", cx, cy, w, length, ztop - depth - 0.01, ztop - depth + 0.004, M["black"], rot=rot,
           bevel=0.0, tags=tags)
    a = math.radians(rot)
    ux, uy = -math.sin(a), math.cos(a)
    for i in range(n):
        t = ((i + 0.5) / n - 0.5) * length
        B.rbox(f"{name}_pip{i}", cx + ux * t, cy + uy * t, w * 0.55, length / n * 0.55, ztop - depth,
               ztop - depth + 0.012, mat or M["glow"], rot=rot, bevel=0.0, tags=tags)


# ============================================================================ cabeca
def head(M, T="head", phase=0.0):
    """Cabeca de gaviao em cunha: bico entre os canos, bochechas com olhos, garras, coroa, penas na nuca."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]

    # nucleo escuro (o anel da torre fica todo sob o nucleo: so o teto o desenha)
    B.plate("core", CORE, 0.06, 0.28, K, slope=0.04, tags=tags)

    # berco escuro: duas calhas abertas onde assentam as culatras
    cr = B.plate("cradle", CRADLE, 0.20, 0.36, KM, slope=0.025, tags=tags)
    B.cut(cr, [B.box(f"cr_ch{i}", y, 0.53, 0.16, 0.74, 0.29, 0.9, K, bevel=0.0) for i, y in enumerate(YS)])
    for i, y in enumerate(YS):
        B.box(f"cr_bed{i}", y, 0.53, 0.16, 0.70, 0.28, 0.295, M["black"], bevel=0.0, tags=tags)

    for sx in (-1, 1):
        sd = "R" if sx > 0 else "L"
        # bochecha clara (a parte mais larga) com linha de painel atras do olho
        ca, cpn = B.shard(f"cheek_{sd}", side_poly(CHEEK, sx), 0.26, 0.56, A, slope=0.06, groove=0.03,
                          panel_h=0.03, tags=tags)
        if cpn is not None:
            B.cut(cpn, [B.rbox(f"cpl{sd}0", sx * 0.62, -0.075, 0.016, 0.22, 0.55, 0.9, K, rot=sx * 75, bevel=0.0)])
        # olho do carcara: recesso em gota com fenda de lente ambar ao longo da cauda e viseira de aco na frente
        ex, ey = EYE["c"]
        ang = EYE["ang"] if sx > 0 else 180.0 - EYE["ang"]
        drop = teardrop(sx * ex, ey, EYE["r"], EYE["tail"], ang)
        zt = 0.59
        for t in (ca, cpn):
            if t is not None:
                B.cut(t, [B.loft(f"eye_cut{sd}{t.name}", drop, drop, zt - 0.09, 1.0, K, bevel=0.0)])
        B.loft(f"eye_bed{sd}", drop, drop, zt - 0.10, zt - 0.088, M["black"], bevel=0.0, tags=tags)
        ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))   # eixo da cauda
        B.rbox(f"eye_lens{sd}", sx * ex + ux * 0.02, ey + uy * 0.02, 0.022, 0.11, zt - 0.072, zt - 0.06, M["glow"],
               rot=sx * 53, bevel=0.0, tags=tags)
        nx, ny = sx * 0.6, 0.8                                              # lado da frente do recesso
        B.rbox(f"visor{sd}", sx * ex + nx * 0.088, ey + ny * 0.088, 0.03, 0.17, 0.57, 0.615, S, rot=sx * 53,
               chamfer=0.012, slope=0.008, bevel=0.006, tags=tags)

        # garra em lamina com fenda de luz fraca ao longo do eixo
        ta, tpn = B.shard(f"talon_{sd}", side_poly(TALON, sx), 0.26, 0.53, A, slope=0.04, groove=0.02,
                          panel_h=0.025, tags=tags)
        tcx, tcy, trot = sx * 0.465, 0.635, sx * TALON_AX
        slot_rot(f"tsl{sd}", tcx, tcy, 0.18, 0.03, 0.555, 0, M, tags, trot, [ta, tpn], depth=0.07)
        B.rbox(f"tglow{sd}", tcx, tcy, 0.014, 0.14, 0.486, 0.498, M["glow_dim"], rot=trot, bevel=0.0, tags=tags)
        # pistao no vao bochecha/garra
        B.cyl(f"piston{sd}", sx * 0.60, 0.383, 0.32, 0.022, 0.24, S, axis="Y", verts=10, yaw=sx * GAP_YAW,
              tags=tags)
        B.cyl(f"pistonb{sd}", sx * 0.70, 0.345, 0.32, 0.032, 0.09, KM, axis="Y", verts=10, yaw=sx * GAP_YAW,
              tags=tags)

        # penas da nuca: a de fora com fenda de 2 pips ao longo da haste, a de dentro mais baixa e enfiada
        fa, fpn = B.shard(f"feather1_{sd}", side_poly(FEATHER1, sx), 0.24, 0.48, A, slope=0.05, groove=0.025,
                          panel_h=0.03, tags=tags)
        slot_rot(f"fsl{sd}", sx * 0.585, -0.48, 0.16, 0.04, 0.51, 2, M, tags, sx * -15, [fa, fpn], depth=0.08)
        B.shard(f"feather2_{sd}", side_poly(FEATHER2, sx), 0.20, 0.38, A, slope=0.045, groove=0.02, panel_h=0.025,
                tags=tags)

        # calha de alimentacao no vao coroa/bochecha: motor atras com contador, aneis de aco, boca na culatra
        x = sx * 0.34
        B.cyl(f"chute{sd}", x, -0.02, 0.34, 0.036, 0.56, KM, axis="Y", verts=8, bevel=0.006, tags=tags)
        for i, y in enumerate((-0.20, -0.02, 0.16)):
            B.cyl(f"chuter{sd}{i}", x, y, 0.34, 0.044, 0.026, S, axis="Y", verts=8, bevel=0.004, tags=tags)
        B.box(f"feedport{sd}", sx * 0.335, 0.30, 0.08, 0.13, 0.28, 0.44, KM, bevel=0.01, tags=tags)
        B.box(f"feedlid{sd}", sx * 0.335, 0.30, 0.05, 0.07, 0.44, 0.455, S, bevel=0.005, tags=tags)
        B.box(f"fmotor{sd}", sx * 0.385, -0.35, 0.12, 0.11, 0.26, 0.40, KM, bevel=0.012, tags=tags)
        B.box(f"fmotorc{sd}", sx * 0.385, -0.318, 0.08, 0.035, 0.40, 0.418, S, bevel=0.006, tags=tags)
        for i in range(2):
            B.box(f"fmled{sd}{i}", sx * (0.36 + i * 0.05), -0.378, 0.026, 0.024, 0.40, 0.409, M["glow_dim"],
                  bevel=0.0, tags=tags)

    # bico: cera cinza media com narinas escuras + bico claro com crista e dente tomial
    cere = B.loft("cere", CERE_B, CERE_T, 0.24, 0.60, AM, bevel=0.01, tags=tags)
    B.cut(cere, [B.box(f"nostril_c{sx}", sx * 0.036, 0.26, 0.022, 0.06, 0.55, 0.9, K, bevel=0.0) for sx in (-1, 1)])
    for sx in (-1, 1):
        B.box(f"nostril{sx}", sx * 0.036, 0.26, 0.022, 0.06, 0.545, 0.556, M["black"], bevel=0.0, tags=tags)
    bill = beak("bill", BILL, BILL_TIP, 0.26, A, bevel=0.01, tags=tags)
    B.cut(bill, [B.box("bill_pl", 0, 0.48, 0.30, 0.016, 0.55, 0.9, K, bevel=0.0)])

    # coroa clara com canal sensor escuro em seta (fenda de luz fraca na ponta, nervuras de aco atras)
    z0, z1, ph = 0.30, 0.62, 0.03
    cw, cpn = B.shard("crown", CROWN, z0, z1, A, slope=0.08, groove=0.035, panel_h=ph, tags=tags)
    zt = z1 + ph
    for t in (cw, cpn):
        if t is not None:
            B.cut(t, [B.loft(f"cap_cut{t.name}", CAP, CAP, zt - 0.08, 1.2, K, bevel=0.0)])
    B.loft("cap_bed", CAP, CAP, zt - 0.09, zt - 0.075, KM, bevel=0.0, tags=tags)
    B.box("cap_eye", 0, -0.06, 0.07, 0.016, zt - 0.076, zt - 0.068, M["glow_dim"], bevel=0.0, tags=tags)
    for i, y in enumerate((-0.33, -0.26)):
        B.box(f"cap_rib{i}", 0, y, 0.12, 0.022, zt - 0.076, zt - 0.06, S, bevel=0.004, tags=tags)

    # baia de exaustao traseira: persianas com fileira de 3 pips fracos entre duas delas
    B.box("vent_bay", 0, -0.73, 0.40, 0.18, 0.20, 0.30, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"louver{i}", 0, -0.79 + i * 0.05, 0.38, 0.018, 0.20, 0.31, KM, bevel=0.003, tags=tags)
    for i, x in enumerate((-0.10, 0.0, 0.10)):
        B.box(f"vent_pip{i}", x, -0.765, 0.03, 0.014, 0.300, 0.307, M["glow_dim"], bevel=0.0, tags=tags)


# ============================================================================ cano
def barrel(M, L=1.5, T="barrel", phase=0.0):
    """Um cano de 20 mm: raiz em y=0, boca em y=L, centrado em x=0."""
    tags = (T,)
    hot = (T, "hot")
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = ZB
    # culatra escura (fica no berco) com tampa, dobradica e trava de aco
    rec = [(-0.058, 0.0), (0.058, 0.0), (0.068, 0.03), (0.068, 0.30), (0.055, 0.34), (-0.055, 0.34),
           (-0.068, 0.30), (-0.068, 0.03)]
    B.plate("b_recv", rec, z - 0.08, z + 0.05, KM, slope=0.012, tags=tags)
    B.box("b_cover", 0, 0.17, 0.08, 0.20, z + 0.045, z + 0.065, KM, bevel=0.006, tags=tags)
    B.box("b_hinge", 0, 0.282, 0.064, 0.014, z + 0.05, z + 0.07, S, bevel=0.004, tags=tags)
    B.box("b_latch", 0, 0.05, 0.05, 0.03, z + 0.05, z + 0.075, S, bevel=0.005, tags=tags)
    # camisa escura com fendas transversais (brasa fraca e estreita no fundo)
    y0j, y1j = 0.34, 0.62
    jk = B.cyl("b_jacket", 0, (y0j + y1j) / 2, z, 0.052, y1j - y0j, KM, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cut(jk, [B.box(f"b_jc{i}", 0, 0.42 + i * 0.06, 0.13, 0.026, z + 0.022, z + 0.2, K, bevel=0.0)
               for i in range(3)])
    B.box("b_heat", 0, (y0j + y1j) / 2, 0.04, y1j - y0j - 0.10, z + 0.016, z + 0.026, M["ember"], bevel=0.0,
          tags=tags)
    for i, y in enumerate((y0j + 0.018, y1j - 0.018)):
        fn = B.cyl(f"b_fin{i}", 0, y, z, 0.058, 0.024, AM, axis="Y", verts=8, bevel=0.004, tags=tags)
        B.cut(fn, [B.box(f"b_finc{i}", 0, y, 0.016, 0.06, z + 0.034, z + 0.2, K, bevel=0.0)])
    # luva clara facetada afunilada com canal escuro
    y0, y1 = y1j, L - 0.25
    sl = B.cyl("b_sleeve", 0, (y0 + y1) / 2, z, 0.048, y1 - y0, A, axis="Y", verts=8, bevel=0.006, tags=tags,
               r2=0.040)
    B.cut(sl, [B.box("b_chc", 0, (y0 + y1) / 2, 0.014, y1 - y0 - 0.06, z + 0.02, z + 0.2, K, bevel=0.0)])
    B.box("b_chbed", 0, (y0 + y1) / 2, 0.014, y1 - y0 - 0.06, z + 0.012, z + 0.024, M["black"], bevel=0.0,
          tags=tags)
    # extrator de gases: bojo facetado com cones nas pontas e canal escuro no topo (a 40 % da luva)
    ye = y0 + (y1 - y0) * 0.40
    fume = B.cyl("b_fume", 0, ye, z, 0.06, 0.12, A, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cut(fume, [B.box("b_fumec", 0, ye, 0.014, 0.14, z + 0.032, z + 0.2, K, bevel=0.0)])
    for sx in (-1, 1):
        B.cyl(f"b_fumecone{sx}", 0, ye + sx * 0.08, z, 0.046 if sx < 0 else 0.06, 0.04, A, axis="Y", verts=8,
              bevel=0.0, tags=tags, r2=0.06 if sx < 0 else 0.046)
    B.cyl("b_collar0", 0, y0 + 0.03, z, 0.056, 0.03, AM, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("b_collar1", 0, y1 - 0.015, z, 0.054, 0.03, AM, axis="Y", verts=8, bevel=0.006, tags=hot)
    # freio leve em ponta de flecha (ombro atras, nariz em dardo) com 4 fendas transversais escuras
    yb = L - 0.13
    brake = [(-0.056, yb - 0.13), (0.056, yb - 0.13), (0.068, yb - 0.10), (0.068, yb + 0.02), (0.030, yb + 0.13),
             (-0.030, yb + 0.13), (-0.068, yb + 0.02), (-0.068, yb - 0.10)]
    br = B.plate("b_brake", brake, z - 0.058, z + 0.058, A, slope=0.010, tags=tags)
    bc = [B.box(f"b_bc{i}", 0, yb - 0.09 + i * 0.035, 0.18, 0.018, z + 0.012, z + 0.2, K, bevel=0.0)
          for i in range(4)]
    bc.append(B.box("b_bore_c", 0, L, 0.022, 0.07, z + 0.0, z + 0.2, K, bevel=0.0))
    B.cut(br, bc)
    # fundo escuro das fendas: e ele que esquenta (o laranja fica so dentro das fendas)
    B.box("b_brake_core", 0, yb - 0.035, 0.12, 0.13, z - 0.04, z + 0.014, K, bevel=0.0, tags=hot)


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto 2x2: placas verdes, anel da torre, respiros em chevron atras e tampas triangulares na frente."""
    tags = (T,)
    w, h = PART["size"]
    green = B.mat_roof_green()
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    px, py = PART["pivot"][0] - w / 2, h / 2 - PART["pivot"][1]
    rr = RING_R
    gap = 0.03
    B.box("deck_under", 0, 0, w, h, -0.05, 0.02, K, bevel=0.0, tags=tags)
    for tx in range(w):
        for ty in range(h):
            cx, cy = tx + 0.5 - w / 2, h / 2 - ty - 0.5
            poly = B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
            B.shard(f"deck{tx}_{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02, tags=tags)
    B.torus("ringbear", px, py, 0.08, rr + 0.02, 0.055, KM, tags=tags)
    B.cyl("ringhole", px, py, 0.05, rr - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(px, py, rr + 0.11, 28) if abs(x) < w / 2 - 0.06 and abs(y) < h / 2 - 0.06]
    B.bolts("rb", pts, 0.1, 0.022, S, tags=tags)
    for sx in (-1, 1):
        # canto de tras: respiro em diagonal com persianas fundas; luz fraca no fundo da persiana de fora
        cx, cy = sx * 0.78, -0.80
        v = B.rbox(f"cvent{sx}", cx, cy, 0.34, 0.17, 0.05, 0.11, KM, rot=sx * 40, chamfer=0.035, bevel=0.01,
                   tags=tags)
        a = math.radians(sx * 40)
        B.cut(v, [B.rbox(f"cvc{sx}{i}", cx - math.sin(a) * (i - 1) * 0.045, cy + math.cos(a) * (i - 1) * 0.045,
                         0.27, 0.025, 0.07, 0.2, K, rot=sx * 40, bevel=0.0) for i in range(3)])
        B.rbox(f"cled{sx}", cx + math.sin(a) * 0.045, cy - math.cos(a) * 0.045, 0.14, 0.018, 0.070, 0.078,
               M["glow_dim"], rot=sx * 40, bevel=0.0, tags=tags)
        # canto da frente: tampa triangular chanfrada com parafuso
        tri = [(sx * 0.92, 0.92), (sx * 0.64, 0.92), (sx * 0.92, 0.64)]
        B.plate(f"chatch{sx}", tri if sx < 0 else list(reversed(tri)), 0.06, 0.10, M["armor_mid"], slope=0.02,
                tags=tags)
        B.bolts(f"chb{sx}", [(sx * 0.84, 0.84)], 0.115, 0.018, S, tags=tags)


def floor(M, T="floor"):
    """Piso: anel, posto do atirador atras no meio com console ao lado, caixas de cinta nos cantos da frente."""
    from bsgen.common import crew_positions
    tags = (T,)
    w, h = PART["size"]
    pv = PART["pivot"]
    rr = RING_R
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    px, py = pv[0] - w / 2, h / 2 - pv[1]
    B.box("fl_base", 0, 0, w, h, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for tx in range(w):
        for ty in range(h):
            x0, y1 = tx - w / 2 + 0.04, h / 2 - ty - 0.04
            B.box(f"fl{tx}{ty}", x0 + 0.46, y1 - 0.46, 0.92, 0.92, 0.0, 0.03, KM, bevel=0.01, tags=tags)
    # anel menor (nao encosta na base do assento)
    B.torus("fl_ring", px, py, 0.05, rr * 0.52, 0.045, AM, tags=tags)
    hub = B.cyl("fl_hub", px, py, 0.05, rr * 0.26, 0.08, A, axis="Z", verts=48, tags=tags)
    B.cut(hub, [B.rbox(f"fl_hubg{k}", px + math.cos(math.radians(30 + 60 * k)) * rr * 0.16,
                       py + math.sin(math.radians(30 + 60 * k)) * rr * 0.16, 0.018, rr * 0.18, 0.07, 0.2, K,
                       rot=60 * k - 60, bevel=0.0) for k in range(6)])
    B.cyl("fl_hubc", px, py, 0.085, rr * 0.07, 0.012, KM, axis="Z", verts=16, bevel=0.0, tags=tags)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        B.rbox(f"fl_chev{k}", px + math.cos(a) * rr * 0.38, py + math.sin(a) * rr * 0.38, 0.10, 0.10, 0.05, 0.08,
               A, rot=45, bevel=0.01, tags=tags)
    B.box("fl_led_t", px, py + rr * 0.76, 0.24, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # caixas de cinta nos cantos da frente (tampa clara e contador ambar)
    for sx in (-1, 1):
        cx, cy = sx * 0.76, 0.74
        B.rbox(f"fl_box{sx}", cx, cy, 0.34, 0.22, 0.0, 0.16, KM, rot=-sx * 45, chamfer=0.03, bevel=0.01, tags=tags)
        B.rbox(f"fl_lid{sx}", cx, cy, 0.26, 0.14, 0.16, 0.19, AM, rot=-sx * 45, chamfer=0.02, bevel=0.008,
               tags=tags)
        B.rbox(f"fl_cnt{sx}", cx, cy, 0.10, 0.03, 0.19, 0.205, M["glow_dim"], rot=-sx * 45, bevel=0.0, tags=tags)
    # estante de cintas ao longo da borda de tras
    for tx in range(w):
        x = tx - w / 2 + 0.5
        B.box(f"rack{tx}", x, -h / 2 + 0.13, 0.78, 0.18, 0.0, 0.16, AM, bevel=0.01, tags=tags)
        for i in range(3):
            B.box(f"mag{tx}{i}", x - 0.24 + i * 0.24, -h / 2 + 0.13, 0.16, 0.12, 0.16, 0.24, KM, bevel=0.01, tags=tags)
            B.box(f"magled{tx}{i}", x - 0.24 + i * 0.24, -h / 2 + 0.13, 0.10, 0.03, 0.24, 0.26, M["glow_dim"],
                  bevel=0.0, tags=tags)
    # posto do atirador: base de aco, assento claro, encosto escuro e console a direita
    for i, (cx, cy, _r) in enumerate(crew_positions(w, h, 1, pv)):
        x, y = cx - w / 2, h / 2 - cy
        B.box(f"seatb{i}", x, y + 0.04, 0.34, 0.32, 0.0, 0.05, S, bevel=0.012, tags=tags)
        B.box(f"seat{i}", x, y + 0.06, 0.28, 0.22, 0.05, 0.14, A, bevel=0.035, tags=tags)
        B.box(f"seatbk{i}", x, y - 0.09, 0.30, 0.07, 0.05, 0.24, KM, bevel=0.02, tags=tags)
        B.box(f"seatbs{i}", x, y - 0.09, 0.20, 0.025, 0.24, 0.255, S, bevel=0.006, tags=tags)
        for sx in (-1, 1):
            B.box(f"console{i}{sx}", x + sx * 0.36, y + 0.06, 0.12, 0.34, 0.0, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x + 0.36, y + 0.06, 0.06, 0.24, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
        B.box(f"pad{i}", x - 0.36, y + 0.06, 0.06, 0.12, 0.22, 0.235, M["glow_dim"], bevel=0.0, tags=tags)
