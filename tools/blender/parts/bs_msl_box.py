"""Caixa de Micromisseis de Convés ("Tocandira") - lancador 2x2 inicial, familia do 76 mm.

Tocandira = formiga-bala (a ferroada mais dolorida): a caixa de tubos e a cabeca, mandibulas em foice (com
dente) se fecham sobre os cantos de baixo da face, bochechas (garfo curto com esporao traseiro) seguram os
munhoes nas laterais e o abdomen de tergitos em divisa afunila ate a cauda com a baia de exaustao de 3 pips.
Caixa estilo RAM inclinada 35 graus: face preta com 6 cassetes de 2 tubos (grade 4x3, bocas VAZIAS),
moldura clara em aba com esporao no meio, carapaca no topo com entalhes de sopro traseiros e crista dorsal
com cabeca de sensor IR (fenda ambar pulsando, 8 quadros); a crista continua no abdomen.
A caixa e modelada no proprio referencial (face no plano local) e girada; as posicoes projetadas das bocas
batem com launcher_layout (centro da face (0, 0.32), passo 0.26 x 0.22 na vista de cima).
"""

import math

import bpy

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_msl_box",
    "kind": "launcher",
    "size": [2, 2],
    "pivot": [1.0, 0.95],          # = art.part_meta.pivot do spec
    "turret_box": 1.9,
    "ring_r": 0.80,
    "collider": 0.85,
    "accent": "amber",
    "looks": ["he", "napalm"],
    "turret_anim": {"frames": 8, "interval": 0.12},   # fenda IR da espinha pulsando
    "lights": [
        {"at": [0.0, -0.80], "size": 1.0, "color": [255, 120, 30], "z": 0.6},
    ],
    "preview_pattern": "ripple",
}

PITCH = 35.0                        # elevacao da caixa (graus)
SIN, COS = math.sin(math.radians(PITCH)), math.cos(math.radians(PITCH))
FACE_Y = 0.32                       # centro da face projetado (cells.pods[0].center)
Z0 = 1.15                           # altura do centro da face
TUBE_R = 0.09
COLS = (-0.39, -0.13, 0.13, 0.39)
ROW_V = 0.22 / SIN                  # passo das fileiras no plano da face (0.22 na vista de cima)
ROWS = (-ROW_V, 0.0, ROW_V)         # v > 0 = parte de baixo da face = frente na vista de cima
LP = 0.40                           # comprimento da caixa atras da face

BAND = {"he": (1.0, 0.43, 0.0), "napalm": (1.0, 0.145, 0.01)}   # #FFB000 / #FF6A1A (lineares)


# ============================================================================ utilidades
def _novos(antes):
    sc = bpy.context.scene
    return [o for o in sc.objects if o.name not in antes and o.parent is None and o.type != "EMPTY"]


def _agrupar(antes, nome, rot_x, at):
    """Prende os objetos novos (sem pai) num Empty girado em X e posicionado (referencial da caixa)."""
    sc = bpy.context.scene
    emp = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(emp)
    for o in _novos(antes):
        o.parent = emp
    emp.location = at
    emp.rotation_euler = (math.radians(rot_x), 0.0, 0.0)
    return emp


def _cena():
    return set(o.name for o in bpy.context.scene.objects)


# ============================================================================ caixa: face (referencial da face)
def _face(M, tags):
    """Face da caixa no plano XY (x direita, y = descendo a face = frente na projecao, z = para fora)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.box("f_back", 0, 0, 1.10, 1.20, -0.26, -0.12, M["black"], bevel=0.0, tags=tags)
    fp = B.box("f_plate", 0, 0, 1.10, 1.20, -0.12, -0.03, M["black"], bevel=0.008, tags=tags)
    # moldura clara em aba em volta da grade
    outer = B.rpoly(0, 0, 1.24, 1.34, 0, chamfer=0.11)
    fr = B.plate("f_frame", outer, -0.10, 0.07, A, slope=0.035, tags=tags)
    opening = B.rpoly(0, 0, 1.08, 1.18, 0, chamfer=0.05)
    B.cut(fr, [B.loft("f_open", opening, opening, -0.3, 0.3, K, bevel=0.0)])
    B.bolts("f_bolt", [(sx * 0.575, sy * 0.625) for sx in (-1, 1) for sy in (-1, 1)], 0.075, 0.018, S, tags=tags)
    # esporao no meio da aba de baixo (ponta para a frente entre as mandibulas)
    chin = [(-0.12, 0.585), (0.12, 0.585), (0.05, 0.735), (-0.05, 0.735)]
    ch = B.plate("f_chin", chin, 0.0, 0.12, A, slope=0.03, tags=tags)
    B.cut(ch, [B.box("f_chin_c", 0, 0.64, 0.016, 0.07, 0.10, 0.3, K, bevel=0.0)])
    # 6 cassetes de 2 tubos (pares horizontais), bocas vazias
    plate_cuts = []
    for r, v in enumerate(ROWS):
        for c, xc in enumerate((-0.26, 0.26)):
            cas = B.plate(f"cas{r}{c}", B.rpoly(xc, v, 0.49, 0.27, 0, chamfer=0.07), -0.05, 0.03, AM, slope=0.018,
                          tags=tags)
            B.cut(cas, [B.cyl(f"bore{r}{c}{k}", xc + dx, v, 0.0, TUBE_R, 0.6, K, axis="Z", verts=24, bevel=0.0)
                        for k, dx in enumerate((-0.13, 0.13))])
            for k, dx in enumerate((-0.13, 0.13)):
                plate_cuts.append(B.cyl(f"pbore{r}{c}{k}", xc + dx, v, 0.0, TUBE_R, 0.6, K, axis="Z", verts=24,
                                        bevel=0.0))
            # nervura de aco entre os dois tubos do cassete
            B.box(f"cas_rib{r}{c}", xc, v, 0.028, 0.17, 0.02, 0.045, S, bevel=0.004, tags=tags)
    B.cut(fp, plate_cuts)


# ============================================================================ caixa: topo (referencial do eixo)
def _top(M, tags, phase):
    """Corpo e topo da caixa (x direita, y = eixo dos tubos, z = cima da caixa); face em y = 0."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.box("p_body", 0, -(LP + 0.08) / 2, 1.14, LP - 0.08, -0.58, 0.58, KM, bevel=0.012, tags=tags)
    # carapaca do topo numa peca so (borda de tras em divisa, como o abdomen)
    shell = [(-0.60, -0.31), (-0.16, -0.39), (0.16, -0.39), (0.60, -0.31), (0.60, -0.18), (0.55, -0.13),
             (-0.55, -0.13), (-0.60, -0.18)]
    sa, sp = B.shard("shell", shell, 0.55, 0.64, A, slope=0.045, groove=0.025, panel_h=0.022, tags=tags)
    tg = [t for t in (sa, sp) if t is not None]
    ang = math.degrees(math.atan2(0.08, 0.44))
    for sname, sx in (("L", -1), ("R", 1)):
        # entalhe de sopro na borda de tras (tubos abertos atras): venezianas escuras
        gx, gy, gr = sx * 0.40, -0.335, sx * ang
        ux, uy = -math.sin(math.radians(gr)), math.cos(math.radians(gr))
        for t in tg:
            B.cut(t, [B.rbox(f"gcut_{t.name}{sname}", gx, gy, 0.26, 0.065, 0.58, 0.9, K, rot=gr, bevel=0.0)])
        B.rbox(f"gbed{sname}", gx, gy, 0.26, 0.065, 0.565, 0.58, M["black"], rot=gr, bevel=0.0, tags=tags)
        for i in range(3):
            o = (i - 1) * 0.019
            B.rbox(f"glouv{sname}{i}", gx + ux * o, gy + uy * o, 0.24, 0.008, 0.57, 0.615, KM, rot=gr, bevel=0.0,
                   tags=tags)
        # sulcos diagonais varrendo para a frente
        if sp is not None:
            B.cut(sp, [B.rbox(f"tpl{sname}{i}", sx * (0.30 + i * 0.12), -0.215 + i * 0.005, 0.014, 0.13, 0.64,
                              0.9, K, rot=sx * -38, bevel=0.0) for i in range(2)])
    B.bolts("tbolt", [(sx * 0.535, -0.175) for sx in (-1, 1)], 0.665, 0.016, S, tags=tags)
    # crista dorsal em seta com cabeca do sensor IR (fenda ambar que pulsa)
    zs = 0.74
    ridge = [(-0.08, -0.40), (0.08, -0.40), (0.10, -0.36), (0.10, -0.26), (0.13, -0.225), (0.13, -0.15),
             (0.05, -0.05), (-0.05, -0.05), (-0.13, -0.15), (-0.13, -0.225), (-0.10, -0.26), (-0.10, -0.36)]
    ra, rp = B.shard("ridge", ridge, 0.60, zs, A, slope=0.035, groove=0.02, panel_h=0.022, tags=tags)
    win = [(-0.065, -0.215), (0.065, -0.215), (0.065, -0.19), (0.028, -0.158), (-0.028, -0.158), (-0.065, -0.19)]
    for t in (ra, rp):
        if t is not None:
            B.cut(t, [B.loft(f"wcut_{t.name}", win, win, zs - 0.06, zs + 0.5, K, bevel=0.0)])
    B.loft("ir_bed", win, win, zs - 0.066, zs - 0.056, M["black"], bevel=0.0, tags=tags)
    pulse = 0.5 + 0.5 * math.cos(phase * math.tau)
    ir = B.mat_glow("ir_slit", Mo.AMBER, 1.5 + 5.0 * pulse)
    B.box("ir_slit", 0, -0.198, 0.10, 0.016, zs - 0.058, zs - 0.048, ir, bevel=0.0, tags=tags)
    # aletas finas na traseira da crista
    if rp is not None:
        B.cut(rp, [B.box(f"rfin{i}", 0, -0.335 + i * 0.03, 0.16, 0.014, zs, zs + 0.3, K, bevel=0.0) for i in range(2)])


# ============================================================================ cabeca
def _claws(M, tags):
    """Bochechas (garfo com munhao e esporao traseiro) + mandibulas longas que se fecham na frente da caixa."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    cheek = [(-0.665, -0.34), (-0.72, -0.60), (-0.80, -0.56), (-0.89, -0.34), (-0.89, 0.08), (-0.84, 0.20),
             (-0.665, 0.24)]
    # mandibula em foice: bordo externo em facetas retas, gancho que passa sobre o canto de baixo da face
    # (sem cobrir os narizes da fileira da frente) e um dente no bordo interno
    mand = [(-0.70, 0.26), (-0.88, 0.26), (-0.91, 0.38), (-0.89, 0.60), (-0.79, 0.78), (-0.62, 0.885),
            (-0.40, 0.92), (-0.25, 0.915), (-0.17, 0.875), (-0.24, 0.835), (-0.35, 0.80), (-0.40, 0.74),
            (-0.47, 0.785), (-0.56, 0.75), (-0.62, 0.70), (-0.665, 0.60), (-0.68, 0.40)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        ca, cp = B.shard(f"cheek_{side}", f(cheek), 0.30, 1.02, A, slope=0.045, groove=0.025, panel_h=0.03,
                         tags=tags)
        # fenda de pips na bochecha + linha de painel em diagonal
        Mo.slot_with_pips(f"cslot{side}", sx * 0.775, -0.22, 0.02, 0.058, 1.05, 3, M, tags,
                          target=[t for t in (ca, cp) if t is not None], depth=0.075)
        if cp is not None:
            B.cut(cp, [B.rbox(f"cpl{side}", sx * 0.77, 0.12, 0.016, 0.16, 1.04, 1.3, K, rot=sx * 55, bevel=0.0),
                       B.rbox(f"cpl2{side}", sx * 0.77, -0.42, 0.016, 0.16, 1.04, 1.3, K, rot=sx * -40, bevel=0.0)])
        # mancal do munhao no vao entre bochecha e caixa
        B.box(f"bear{side}", sx * 0.64, 0.06, 0.07, 0.24, 0.6, 0.98, KM, bevel=0.01, tags=tags)
        B.cyl(f"trun{side}", sx * 0.64, 0.06, 0.99, 0.06, 0.10, S, axis="X", verts=12, bevel=0.005, tags=tags)
        # mandibula: lamina curva em degrau com fenda de luz ao longo do bordo externo
        ma, mp = B.shard(f"mand_{side}", f(mand), 0.55, 0.84, A, slope=0.045, groove=0.022, panel_h=0.03,
                         tags=tags)
        mx, my, mr = sx * 0.79, 0.48, sx * 10
        for t in (ma, mp):
            if t is not None:
                B.cut(t, [B.rbox(f"mcut_{t.name}", mx, my, 0.045, 0.22, 0.80, 1.1, K, rot=mr, bevel=0.0)])
        B.rbox(f"mbed{side}", mx, my, 0.045, 0.22, 0.78, 0.805, M["black"], rot=mr, bevel=0.0, tags=tags)
        B.rbox(f"mglow{side}", mx, my, 0.016, 0.16, 0.805, 0.813, M["glow_dim"], rot=mr, bevel=0.0, tags=tags)
        if mp is not None:
            B.cut(mp, [B.rbox(f"mpl{side}", sx * 0.69, 0.80, 0.016, 0.12, 0.86, 1.1, K, rot=sx * 50, bevel=0.0)])
        # pistao da mandibula (no vao entre mandibula e caixa) e pistao de elevacao atras
        B.cyl(f"mpist{side}", sx * 0.655, 0.42, 0.60, 0.028, 0.24, S, axis="Y", verts=12, yaw=sx * 6, tags=tags)
        B.cyl(f"epist{side}", sx * 0.585, -0.50, 0.40, 0.03, 0.26, S, axis="Y", verts=12, yaw=sx * -10, tags=tags)
        B.cyl(f"epistb{side}", sx * 0.58, -0.58, 0.40, 0.046, 0.12, KM, axis="Y", verts=12, yaw=sx * -10,
              tags=tags)


CHEV = 0.28   # inclinacao das divisas do abdomen (dy por dx)


def _band(w, yf, yb):
    """Tergito em divisa (ponta para tras): frente e fundo em V, laterais retas."""
    k = CHEV
    return [(-w, yb + k * w), (0.0, yb), (w, yb + k * w), (w, yf + k * w), (0.0, yf), (-w, yf + k * w)]


def _abdomen(M, tags):
    """Abdomen segmentado (tergitos em divisa) afunilando ate a cauda, com a baia de exaustao de 3 pips."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    sa = B.shard("segA", _band(0.50, -0.36, -0.56), 0.28, 0.60, A, slope=0.04, groove=0.022, panel_h=0.02,
                 tags=tags)
    sb = B.shard("segB", _band(0.42, -0.585, -0.72), 0.28, 0.54, A, slope=0.04, groove=0.022, panel_h=0.02,
                 tags=tags)
    tail = [(-0.08, -0.90), (0.08, -0.90), (0.30, -0.74), (0.30, -0.661), (0.0, -0.745), (-0.30, -0.661),
            (-0.30, -0.74)]
    sc = B.shard("segC", tail, 0.28, 0.46, A, slope=0.04, groove=0.022, panel_h=0.02, tags=tags)
    # grelhas de sopro (venezianas) no tergito do meio, alinhadas com a divisa
    for sx in (-1, 1):
        gx, gy, gr = sx * 0.20, -0.597, sx * math.degrees(math.atan(CHEV))
        for t in sb:
            if t is not None:
                B.cut(t, [B.rbox(f"bcut_{t.name}{sx}", gx, gy, 0.20, 0.065, 0.48, 0.9, K, rot=gr, bevel=0.0)])
        B.rbox(f"bbed{sx}", gx, gy, 0.20, 0.065, 0.47, 0.485, M["black"], rot=gr, bevel=0.0, tags=tags)
        for k in range(3):
            o = (k - 1) * 0.02
            B.rbox(f"blv{sx}{k}", gx - math.sin(math.radians(gr)) * o, gy + math.cos(math.radians(gr)) * o, 0.18,
                   0.008, 0.47, 0.53, KM, rot=gr, bevel=0.0, tags=tags)
    # baia de exaustao na cauda: 3 pips ambar em V, cada um num rebaixo escuro
    zt = 0.48
    for i, (x, y) in enumerate(((-0.13, -0.786), (0.0, -0.822), (0.13, -0.786))):
        r = math.degrees(math.atan(CHEV)) * (1 if x > 0 else -1 if x < 0 else 0)
        for t in sc:
            if t is not None:
                B.cut(t, [B.rbox(f"vcut_{t.name}{i}", x, y, 0.085, 0.05, zt - 0.07, zt + 0.3, K, rot=r, bevel=0.0)])
        B.rbox(f"vbed{i}", x, y, 0.085, 0.05, zt - 0.08, zt - 0.066, M["black"], rot=r, bevel=0.0, tags=tags)
        B.rbox(f"vpip{i}", x, y, 0.05, 0.026, zt - 0.07, zt - 0.058, M["glow"], rot=r, bevel=0.0, tags=tags)
    # crista dorsal: continua a crista da caixa e divide os tergitos (corpo de inseto)
    dor = [(-0.075, -0.38), (0.075, -0.38), (0.075, -0.70), (0.0, -0.765), (-0.075, -0.70)]
    B.plate("dorsal_gap", B.offset_poly(dor, -0.025), 0.40, 0.605, M["black"], slope=0.0, bevel=0.0, tags=tags)
    d = B.plate("dorsal", dor, 0.40, 0.68, A, slope=0.03, tags=tags)
    B.cut(d, [B.box(f"dfin{i}", 0, -0.50 - i * 0.07, 0.20, 0.014, 0.66, 0.9, K, bevel=0.0) for i in range(3)])


def head(M, T="head", phase=0.0):
    """Casulo inteiro (camada roof_doodads): anel, garfo, caixa inclinada com bocas vazias, abdomen."""
    tags = (T,)
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    # anel giratorio e nucleo escuro
    B.cyl("ring", 0, 0, 0.04, PART["ring_r"], 0.08, KM, axis="Z", verts=64, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, PART["ring_r"] - 0.05, 20, 0.16), 0.09, 0.02, S, tags=tags)
    core = [(-0.40, -0.80), (0.40, -0.80), (0.70, -0.52), (0.70, 0.44), (0.46, 0.66), (-0.46, 0.66),
            (-0.70, 0.44), (-0.70, -0.52)]
    B.plate("core", core, 0.06, 0.30, K, slope=0.05, tags=tags)
    _claws(M, tags)
    _abdomen(M, tags)
    # caixa inclinada: topo/corpo (eixo) e face, no mesmo centro
    antes = _cena()
    _top(M, tags, phase)
    _agrupar(antes, "pod_top", PITCH, (0.0, FACE_Y, Z0))
    antes = _cena()
    _face(M, tags)
    _agrupar(antes, "pod_face", PITCH - 90.0, (0.0, FACE_Y, Z0))


def cell(M, look, T="cell", form="tube", box=None):
    """UM nariz carregado na boca do tubo (origem = centro da boca no plano da face), eixo inclinado como a
    caixa: anel na cor do missil + ogiva clara."""
    if form != "tube":
        raise NotImplementedError(f"bs_msl_box: forma {form} nao existe neste lancador")
    tags = (T,)
    nose = B.mat_paint("nose", (0.74, 0.75, 0.76), rough=0.3, metal=0.15, wear=0.08, grime=0.02, scale=6)
    band = B.mat_glow(f"band_{look}", BAND.get(look, Mo.AMBER), 1.3)
    antes = _cena()
    w = 0.03
    # (raio de tras, raio da frente, comprimento, material): anel colorido + ogiva rombuda + janela do sensor
    for i, (r1, r2, ln, mat) in enumerate(((0.074, 0.074, 0.042, band), (0.071, 0.064, 0.035, nose),
                                           (0.064, 0.046, 0.035, nose), (0.046, 0.020, 0.028, nose),
                                           (0.020, 0.004, 0.010, M["core_mid"]))):
        B.cyl(f"n{i}", 0, 0, w + ln / 2, r1, ln, mat, axis="Z", verts=24, bevel=0.0, tags=tags, r2=r2)
        w += ln
    _agrupar(antes, "nose", PITCH - 90.0, (0.0, 0.0, 0.0))


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto 2x2: placas verdes, anel da torre, respiros nos cantos de tras e tampas nos cantos da frente."""
    tags = (T,)
    w, h = PART["size"]
    green = B.mat_roof_green()
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    px, py = PART["pivot"][0] - w / 2, h / 2 - PART["pivot"][1]
    rr = PART["ring_r"]
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
        # canto de tras: respiro em diagonal com luz
        cx, cy = sx * 0.80, -0.80
        v = B.rbox(f"cvent{sx}", cx, cy, 0.30, 0.18, 0.05, 0.11, KM, rot=sx * 45, chamfer=0.03, bevel=0.01,
                   tags=tags)
        a = math.radians(sx * 45)
        B.cut(v, [B.rbox(f"cvc{sx}{i}", cx - math.sin(a) * (i - 1) * 0.05, cy + math.cos(a) * (i - 1) * 0.05,
                         0.24, 0.022, 0.09, 0.2, K, rot=sx * 45, bevel=0.0) for i in range(3)])
        B.rbox(f"cled{sx}", sx * 0.90, -0.90, 0.10, 0.025, 0.06, 0.085, M["glow_dim"], rot=sx * 45, bevel=0.0,
               tags=tags)
        # canto da frente: tampa de inspecao chanfrada
        hx, hy = sx * 0.82, 0.83
        B.shard(f"chatch{sx}", B.rpoly(hx, hy, 0.22, 0.22, sx * 45, chamfer=0.05), 0.06, 0.10, M["armor_mid"],
                slope=0.015, groove=0.02, panel_h=0.012, tags=tags)
        B.bolts(f"chb{sx}", [(hx, hy)], 0.115, 0.018, S, tags=tags)


def floor(M, T="floor"):
    """Piso: anel, posto do atirador atras e berços com cassetes de micromisseis nos cantos."""
    from bsgen.common import crew_positions
    tags = (T,)
    w, h = PART["size"]
    pv = PART["pivot"]
    rr = PART["ring_r"]
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    px, py = pv[0] - w / 2, h / 2 - pv[1]
    B.box("fl_base", 0, 0, w, h, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for tx in range(w):
        for ty in range(h):
            x0, y1 = tx - w / 2 + 0.04, h / 2 - ty - 0.04
            B.box(f"fl{tx}{ty}", x0 + 0.46, y1 - 0.46, 0.92, 0.92, 0.0, 0.03, KM, bevel=0.01, tags=tags)
    B.torus("fl_ring", px, py, 0.05, rr * 0.85, 0.05, AM, tags=tags)
    B.cyl("fl_hub", px, py, 0.05, rr * 0.30, 0.08, A, axis="Z", verts=48, tags=tags)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        B.rbox(f"fl_chev{k}", px + math.cos(a) * rr * 0.58, py + math.sin(a) * rr * 0.58, 0.14, 0.14, 0.05, 0.08,
               A, rot=45, bevel=0.01, tags=tags)
    B.box("fl_led_t", px, py + rr * 0.95, 0.26, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # bercos de cassetes (2 tubos com nariz claro e anel ambar) nos 4 cantos, em diagonal
    nose = B.mat_paint("nose", (0.74, 0.75, 0.76), rough=0.3, metal=0.15, wear=0.08, grime=0.02, scale=6)
    for i, (cx, cy) in enumerate(((-0.74, 0.74), (0.74, 0.74), (-0.76, -0.80), (0.76, -0.80))):
        rot = 45 if cx * cy < 0 else -45
        a = math.radians(rot)
        ux, uy = -math.sin(a), math.cos(a)       # eixo do cassete
        vx, vy = math.cos(a), math.sin(a)
        B.rbox(f"cradle{i}", cx, cy, 0.30, 0.36, 0.0, 0.07, AM, rot=rot, chamfer=0.04, bevel=0.01, tags=tags)
        for k in (-1, 1):
            tx, ty = cx + vx * k * 0.07, cy + vy * k * 0.07
            B.cyl(f"ctube{i}{k}", tx - ux * 0.03, ty - uy * 0.03, 0.13, 0.055, 0.24, KM, axis="Y", verts=12,
                  yaw=rot, tags=tags)
            B.cyl(f"cnose{i}{k}", tx + ux * 0.13, ty + uy * 0.13, 0.13, 0.05, 0.08, nose, axis="Y", verts=12,
                  yaw=rot, r2=0.012, tags=tags)
            B.cyl(f"cband{i}{k}", tx + ux * 0.085, ty + uy * 0.085, 0.13, 0.057, 0.02, M["glow_dim"], axis="Y",
                  verts=12, yaw=rot, bevel=0.0, tags=tags)
    for i, (cx, cy, _r) in enumerate(crew_positions(w, h, 1, pv)):
        x, y = cx - w / 2, h / 2 - cy
        B.box(f"seat{i}", x, y + 0.02, 0.32, 0.30, 0.0, 0.14, A, bevel=0.04, tags=tags)
        B.box(f"console{i}", x, y + 0.30, 0.42, 0.12, 0.0, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.30, 0.32, 0.06, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
