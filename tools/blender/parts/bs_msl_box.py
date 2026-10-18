"""Caixa de Micromisseis de Convés ("Tocandira") - lancador 2x2 inicial, familia do 76 mm.

Tocandira = formiga-bala (a ferroada mais dolorida): a caixa de tubos e a cabeca, mandibulas em foice (facetas
retas, cotovelo e ponta a 45 graus para dentro, dente interno) fecham os cantos da frente; bochechas (garfo curto
com esporao traseiro) seguram os munhoes nas laterais e o abdomen sobe em rampa de 3 tergitos em divisa (vaos
escuros entre eles) ate a carapaca, afunilando na cauda com a baia de exaustao de 3 pips.
Caixa estilo RAM inclinada 35 graus: face preta com 6 cassetes de 2 tubos (grade 4x3, bocas VAZIAS), moldura de 4
laminas com bisel duplo (cantos em degrau, vaos escuros nos cantos, entalhes na aba de tras, dentes e queixo em
lamina na frente), carapaca no topo com entalhes de sopro e crista dorsal com o sensor IR (fenda ambar pulsando,
8 quadros); a crista continua em quilhas sobre os tergitos.
A caixa e modelada no proprio referencial (face no plano local) e girada; as posicoes projetadas das bocas
batem com launcher_layout (centro da face (0, 0.32), passo 0.26 x 0.22 na vista de cima).
"""

import math

import bmesh
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
Z0 = 0.88                           # altura do centro da face (baixa: a caixa nao sombreia o abdomen)
TUBE_R = 0.09
ROW_V = 0.22 / SIN                  # passo das fileiras no plano da face (0.22 na vista de cima)
ROWS = (-ROW_V, 0.0, ROW_V)         # v > 0 = parte de baixo da face = frente na vista de cima

# cor da faixa do nariz (tinta, linear): #FFB000 Jararaca / #FF6A1A Taturana, compensada pela luz da cena
BAND = {"he": (0.80, 0.30, 0.0), "napalm": (0.80, 0.085, 0.006)}
BAND_GLOW = {"he": (1.0, 0.434, 0.0), "napalm": (1.0, 0.144, 0.010)}

# divisas do abdomen e da borda de tras da carapaca (vista de cima): centro reto +-FLAT, laterais subindo CHEV
FLAT = 0.10
CHEV = 0.24


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


def _pecas(*ts):
    return [t for t in ts if t is not None]


# ============================================================================ caixa: face (referencial da face)
def _face(M, tags):
    """Face da caixa no plano XY (x direita, y = descendo a face = frente na projecao, z = para fora)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    blk = M["black"]
    # fundo preto (aparece nos vaos dos cantos da moldura) e placa das bocas
    B.box("f_back", 0, 0.06, 1.34, 1.36, -0.26, -0.12, blk, bevel=0.0, tags=tags)
    fp = B.box("f_plate", 0, 0, 1.10, 1.20, -0.12, -0.03, blk, bevel=0.008, tags=tags)
    # moldura em 4 laminas com bisel duplo e vao escuro nos cantos (abertura 1.08 x 1.18 como antes)
    rb = [(-0.66, -0.59), (-0.66, -0.64), (-0.62, -0.68), (-0.57, -0.68), (-0.53, -0.74), (0.53, -0.74),
          (0.57, -0.68), (0.62, -0.68), (0.66, -0.64), (0.66, -0.59)]
    fb = [(-0.66, 0.59), (0.66, 0.59), (0.66, 0.635), (0.62, 0.675), (0.57, 0.675), (0.53, 0.72), (-0.53, 0.72),
          (-0.57, 0.675), (-0.62, 0.675), (-0.66, 0.635)]
    ra, rp = B.shard("f_rear", rb, -0.04, 0.05, A, slope=0.03, groove=0.02, panel_h=0.025, tags=tags)
    B.shard("f_front", fb, -0.04, 0.05, A, slope=0.025, groove=0.018, panel_h=0.025, tags=tags)
    for side, sx in (("L", -1), ("R", 1)):
        B.shard(f"f_side{side}", B.rpoly(sx * 0.60, 0.0, 0.13, 1.12, 0, chamfer=0.035), -0.04, 0.05, A,
                slope=0.025, groove=0.018, panel_h=0.025, tags=tags)
    # aba de tras: entalhe trapezoidal no meio (encaixe da crista) + 2 linhas nos vaos dos cassetes,
    # atravessando a parede e o topo; fundo preto embaixo
    notch = [(-0.065, -0.82), (0.065, -0.82), (0.028, -0.655), (-0.028, -0.655)]
    for t in _pecas(ra, rp):
        B.cut(t, [B.loft(f"rnotch_{t.name}", notch, notch, -0.4, 0.4, K, bevel=0.0)] +
              [B.box(f"rslot_{t.name}{i}", sx * 0.26, -0.73, 0.03, 0.17, -0.4, 0.4, K, bevel=0.0)
               for i, sx in enumerate((-1, 1))])
    B.plate("f_rear_bed", B.offset_poly(rb, 0.02), -0.06, -0.03, blk, slope=0.0, bevel=0.0, tags=tags)
    B.bolts("f_bolt", [(sx * 0.42, -0.665) for sx in (-1, 1)], 0.083, 0.016, S, tags=tags)
    # dois dentes curtos para a frente na aba de baixo, ladeando o queixo
    tooth = [(-0.06, 0.66), (0.06, 0.66), (0.06, 0.75), (0.022, 0.85), (-0.022, 0.85), (-0.06, 0.75)]
    for side, sx in (("L", -1), ("R", 1)):
        B.shard(f"f_tooth{side}", [(x + sx * 0.33, y) for x, y in tooth], -0.03, 0.10, A, slope=0.02, groove=0.012,
                panel_h=0.02, tags=tags)
    # queixo em lamina para a frente (entre os dentes da aba), com fenda escura do nucleo
    chin = [(-0.15, 0.635), (0.15, 0.635), (0.15, 0.72), (0.05, 0.93), (-0.05, 0.93), (-0.15, 0.72)]
    ca, cp = B.shard("f_chin", chin, -0.06, 0.12, A, slope=0.03, groove=0.02, panel_h=0.025, tags=tags)
    slot = [(-0.024, 0.68), (0.024, 0.68), (0.024, 0.80), (0.0, 0.85), (-0.024, 0.80)]
    for t in _pecas(ca, cp):
        B.cut(t, [B.loft(f"cslot_{t.name}", slot, slot, 0.02, 0.4, K, bevel=0.0)])
    B.loft("f_chin_bed", slot, slot, 0.012, 0.024, blk, bevel=0.0, tags=tags)
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
    B.box("p_body", 0, -0.19, 1.14, 0.22, -0.58, 0.58, KM, bevel=0.012, tags=tags)
    # carapaca: borda de tras em divisa com a mesma inclinacao do abdomen (vao escuro constante ate o tergito)
    k = CHEV / COS
    yr = -0.31
    ys = yr + k * 0.40
    shell = [(-0.60, ys + 0.04), (-0.56, ys), (-0.50, ys), (-FLAT, yr), (FLAT, yr), (0.50, ys), (0.56, ys),
             (0.60, ys + 0.04), (0.60, -0.08), (0.56, -0.04), (-0.56, -0.04), (-0.60, -0.08)]
    sa, sp = B.shard("shell", shell, 0.55, 0.64, A, slope=0.035, groove=0.018, panel_h=0.022, tags=tags)
    gr_deg = math.degrees(math.atan(k))
    for sname, sx in (("L", -1), ("R", 1)):
        # entalhe de sopro na borda de tras (tubos abertos atras): venezianas escuras
        gx = sx * 0.34
        gy = yr + k * (0.34 - FLAT) + 0.012
        gr = sx * gr_deg
        ux, uy = -math.sin(math.radians(gr)), math.cos(math.radians(gr))
        for t in _pecas(sa, sp):
            B.cut(t, [B.rbox(f"gcut_{t.name}{sname}", gx, gy, 0.22, 0.06, 0.58, 0.9, K, rot=gr, bevel=0.0)])
        B.rbox(f"gbed{sname}", gx, gy, 0.22, 0.06, 0.565, 0.58, M["black"], rot=gr, bevel=0.0, tags=tags)
        for i in range(3):
            o = (i - 1) * 0.018
            B.rbox(f"glouv{sname}{i}", gx + ux * o, gy + uy * o, 0.20, 0.008, 0.57, 0.615, KM, rot=gr, bevel=0.0,
                   tags=tags)
        # sulco longo paralelo a divisa (le como linha de painel a 1x)
        if sp is not None:
            B.cut(sp, [B.rbox(f"tpl{sname}", sx * 0.30, yr + k * 0.20 + 0.095, 0.30, 0.016, 0.64, 0.9, K,
                              rot=gr, bevel=0.0)])
    B.bolts("tbolt", [(sx * 0.54, -0.15) for sx in (-1, 1)], 0.665, 0.016, S, tags=tags)
    # crista dorsal em seta (mais longa e um degrau mais alta) com a cabeca do sensor IR (fenda ambar que pulsa)
    zs = 0.80
    # a ponta da frente entra no entalhe da aba de tras da moldura (a espinha atravessa a caixa)
    ridge = [(-0.08, -0.42), (0.08, -0.42), (0.10, -0.38), (0.10, -0.28), (0.13, -0.245), (0.13, -0.15),
             (0.055, -0.02), (0.035, 0.05), (-0.035, 0.05), (-0.055, -0.02), (-0.13, -0.15), (-0.13, -0.245),
             (-0.10, -0.28), (-0.10, -0.38)]
    ra, rp = B.shard("ridge", ridge, 0.60, zs, A, slope=0.035, groove=0.02, panel_h=0.022, tags=tags)
    win = [(-0.065, -0.215), (0.065, -0.215), (0.065, -0.19), (0.028, -0.158), (-0.028, -0.158), (-0.065, -0.19)]
    for t in _pecas(ra, rp):
        B.cut(t, [B.loft(f"wcut_{t.name}", win, win, zs - 0.06, zs + 0.5, K, bevel=0.0)])
    B.loft("ir_bed", win, win, zs - 0.066, zs - 0.056, M["black"], bevel=0.0, tags=tags)
    pulse = 0.5 + 0.5 * math.cos(phase * math.tau)
    ir = B.mat_glow("ir_slit", Mo.AMBER, 1.5 + 5.0 * pulse)
    B.box("ir_slit", 0, -0.198, 0.10, 0.016, zs - 0.058, zs - 0.048, ir, bevel=0.0, tags=tags)
    # aletas finas na traseira da crista
    if rp is not None:
        B.cut(rp, [B.box(f"rfin{i}", 0, -0.36 + i * 0.035, 0.16, 0.014, zs, zs + 0.3, K, bevel=0.0) for i in range(2)])


# ============================================================================ cabeca
def _claws(M, tags):
    """Bochechas (garfo com munhao e esporao traseiro) + mandibulas em foice que fecham os cantos da frente."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    cheek = [(-0.71, -0.34), (-0.745, -0.60), (-0.815, -0.56), (-0.90, -0.34), (-0.90, 0.08), (-0.85, 0.20),
             (-0.71, 0.24)]
    # mandibula: bordo externo em 3 facetas retas + cotovelo duro, ponta a 45 graus para a frente e para dentro,
    # dente interno grande; painel interno desenhado a mao (sem ponta degenerada)
    mand = [(-0.71, 0.27), (-0.87, 0.27), (-0.925, 0.40), (-0.925, 0.60), (-0.835, 0.755), (-0.665, 0.925),
            (-0.575, 0.855), (-0.655, 0.775), (-0.595, 0.705), (-0.67, 0.645), (-0.71, 0.52)]
    mand_pnl = [(-0.75, 0.33), (-0.845, 0.33), (-0.88, 0.41), (-0.88, 0.59), (-0.80, 0.73), (-0.735, 0.70),
                (-0.725, 0.62), (-0.75, 0.52)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        ca, cp = B.shard(f"cheek_{side}", f(cheek), 0.30, 0.80, A, slope=0.045, groove=0.025, panel_h=0.03,
                         tags=tags)
        # fenda de pips na bochecha + linhas de painel em diagonal
        Mo.slot_with_pips(f"cslot{side}", sx * 0.805, -0.22, 0.02, 0.058, 0.83, 3, M, tags,
                          target=_pecas(ca, cp), depth=0.075)
        if cp is not None:
            B.cut(cp, [B.rbox(f"cpl{side}", sx * 0.80, 0.12, 0.016, 0.16, 0.82, 1.1, K, rot=sx * 55, bevel=0.0),
                       B.rbox(f"cpl2{side}", sx * 0.80, -0.42, 0.016, 0.16, 0.82, 1.1, K, rot=sx * -40, bevel=0.0)])
        # munhao no vao entre bochecha e moldura
        B.box(f"bear{side}", sx * 0.685, 0.06, 0.05, 0.22, 0.50, 0.78, KM, bevel=0.01, tags=tags)
        B.cyl(f"trun{side}", sx * 0.685, 0.06, 0.79, 0.055, 0.07, S, axis="X", verts=12, bevel=0.005, tags=tags)
        # mandibula: base chanfrada + painel elevado a mao + fenda de 2 pips na lamina
        ma = B.plate(f"mand_{side}", f(mand), 0.40, 0.64, A, slope=0.035, tags=tags)
        mp = B.plate(f"mand_{side}_pnl", f(mand_pnl), 0.636, 0.665, A, slope=0.012, bevel=0.0, tags=tags)
        sl = [(sx * 0.80, 0.40), (sx * 0.80, 0.56)]
        for t in _pecas(ma, mp):
            B.cut(t, [B.box(f"mcut_{t.name}", sl[0][0], 0.48, 0.05, 0.17, 0.57, 0.9, K, bevel=0.0)])
        B.box(f"mbed{side}", sx * 0.80, 0.48, 0.05, 0.17, 0.555, 0.572, M["black"], bevel=0.0, tags=tags)
        for i, y in enumerate((0.44, 0.52)):
            B.box(f"mpip{side}{i}", sx * 0.80, y, 0.026, 0.04, 0.565, 0.578, M["glow"], bevel=0.0, tags=tags)
        # pistao da mandibula (no vao entre mandibula e caixa) e pistao de elevacao atras
        B.cyl(f"mpist{side}", sx * 0.685, 0.40, 0.50, 0.026, 0.22, S, axis="Y", verts=12, yaw=sx * 4, tags=tags)
        B.cyl(f"epist{side}", sx * 0.60, -0.48, 0.58, 0.03, 0.24, S, axis="Y", verts=12, yaw=sx * -8, tags=tags)
        B.cyl(f"epistb{side}", sx * 0.605, -0.57, 0.58, 0.045, 0.11, KM, axis="Y", verts=12, yaw=sx * -8,
              tags=tags)


def _chev(w, yf, d, cut=0.04):
    """Tergito em divisa (ponta para tras), espessura d na vista de cima, canto externo de tras chanfrado."""
    s = CHEV * (w - FLAT)
    yb = yf - d
    return [(-w, yb + s + cut), (-w + cut, yb + s - CHEV * cut), (-FLAT, yb), (FLAT, yb),
            (w - cut, yb + s - CHEV * cut), (w, yb + s + cut), (w, yf + s), (FLAT, yf), (-FLAT, yf), (-w, yf + s)]


def _abdomen(M, tags):
    """Abdomen: 3 tergitos claros em divisa subindo em rampa ate a carapaca (vaos escuros de 0.05), quilhas
    centrais continuando a crista, espiraculos no 1o e a cauda com a baia de exaustao de 3 pips."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    za, zb, zc = 1.16, 1.00, 0.84
    a = B.shard("segA", _chev(0.50, -0.312, 0.175), 0.30, za, A, slope=0.022, groove=0.014, panel_h=0.022,
                tags=tags)
    B.shard("segB", _chev(0.42, -0.527, 0.155), 0.30, zb, A, slope=0.022, groove=0.014, panel_h=0.022, tags=tags)
    sf = -0.722 + CHEV * (0.30 - FLAT)
    tail = [(-0.07, -0.92), (0.07, -0.92), (0.30, -0.76), (0.30, sf), (FLAT, -0.722), (-FLAT, -0.722),
            (-0.30, sf), (-0.30, -0.76)]
    sc = B.shard("segC", tail, 0.30, zc, A, slope=0.022, groove=0.014, panel_h=0.022, tags=tags)
    # quilhas centrais (a crista da caixa continua sobre os tergitos)
    B.plate("keelA", [(-0.05, -0.32), (0.05, -0.32), (0.05, -0.465), (0.0, -0.495), (-0.05, -0.465)], za - 0.05,
            za + 0.075, A, slope=0.02, tags=tags)
    B.plate("keelB", [(-0.045, -0.535), (0.045, -0.535), (0.045, -0.65), (0.0, -0.675), (-0.045, -0.65)], zb - 0.05,
            zb + 0.07, A, slope=0.02, tags=tags)
    # espiraculos: fenda escura curta em cada lado do 1o tergito, ao longo da divisa
    ra = math.degrees(math.atan(CHEV))
    for sx in (-1, 1):
        x = sx * 0.30
        y = -0.312 + CHEV * (0.30 - FLAT) - 0.088
        for t in _pecas(*a):
            B.cut(t, [B.rbox(f"spc_{t.name}{sx}", x, y, 0.13, 0.034, za - 0.075, za + 0.3, K, rot=sx * ra,
                             bevel=0.0)])
        B.rbox(f"spbed{sx}", x, y, 0.13, 0.034, za - 0.085, za - 0.07, M["black"], rot=sx * ra, bevel=0.0, tags=tags)
    # baia de exaustao na cauda: 3 pips ambar em V, cada um num rebaixo escuro
    for i, (x, y) in enumerate(((-0.12, -0.79), (0.0, -0.825), (0.12, -0.79))):
        r = ra * (1 if x > 0 else -1 if x < 0 else 0)
        for t in _pecas(*sc):
            B.cut(t, [B.rbox(f"vcut_{t.name}{i}", x, y, 0.075, 0.042, zc - 0.07, zc + 0.3, K, rot=r, bevel=0.0)])
        B.rbox(f"vbed{i}", x, y, 0.075, 0.042, zc - 0.08, zc - 0.066, M["black"], rot=r, bevel=0.0, tags=tags)
        B.rbox(f"vpip{i}", x, y, 0.046, 0.022, zc - 0.07, zc - 0.058, M["glow"], rot=r, bevel=0.0, tags=tags)


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


def _band_mat(look):
    """Faixa do nariz: TINTA na cor do missil (nao e luz) com uma emissao fraca para nao apagar na sombra."""
    name = f"band_{look}"
    m = B.mat_metal(name, BAND.get(look, BAND["he"]), rough=0.65, metal=0.0)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.0     # tinta fosca: sem reflexo branco na faixa
    b.inputs["Emission Color"].default_value = (*BAND_GLOW.get(look, BAND_GLOW["he"]), 1)
    b.inputs["Emission Strength"].default_value = 0.25
    m["bs_glow"] = 0.25
    return m


def _lathe(name, prof, mat, tags, verts=24):
    """Solido de revolucao no eixo Z (perfil [(raio, z)], raio 0 = ponta), lateral suave numa malha so."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r < 1e-5:
            rings.append([bm.verts.new((0.0, 0.0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z))
                          for a in (i / verts * math.tau for i in range(verts))])
    for ra, rb in zip(rings, rings[1:]):
        for i in range(verts):
            j = (i + 1) % verts
            if len(rb) == 1:
                bm.faces.new((ra[i], ra[j], rb[0]))
            else:
                bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = len(p.vertices) != verts
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


def cell(M, look, T="cell", form="tube", box=None):
    """UM nariz carregado na boca do tubo (origem = centro da boca no plano da face), eixo inclinado como a
    caixa: anel fino na cor do missil + cone afilado claro com ponta de aco."""
    if form != "tube":
        raise NotImplementedError(f"bs_msl_box: forma {form} nao existe neste lancador")
    tags = (T,)
    nose = B.mat_paint("nose", (0.74, 0.75, 0.76), rough=0.3, metal=0.15, wear=0.08, grime=0.02, scale=6)
    band = _band_mat(look)
    antes = _cena()
    # anel colorido fino na boca do tubo
    z0, zb = 0.03, 0.062
    B.cyl("n_band", 0, 0, (z0 + zb) / 2, 0.074, zb - z0, band, axis="Z", verts=24, bevel=0.0, tags=tags)
    # ogiva tangente (comprimento 0.17 >= 1.2 x diametro), lisa, com ponta de aco
    R, L = 0.071, 0.17
    rho = (R * R + L * L) / (2 * R)
    prof = []
    for k in range(13):
        xt = L * (1 - k / 12)                       # distancia ate a ponta
        r = math.sqrt(max(0.0, rho * rho - (L - xt) ** 2)) + R - rho
        if r < 0.008:
            break
        prof.append((r, zb + L - xt))
    rt, zt = prof[-1]
    _lathe("n_ogive", prof + [(0.0, zt + 0.002)], nose, tags)
    B.cyl("n_tip", 0, 0, (zt + zb + L) / 2, rt, zb + L - zt, M["steel"], axis="Z", verts=12, bevel=0.0, tags=tags,
          r2=0.001)
    _agrupar(antes, "nose", PITCH - 90.0, (0.0, 0.0, 0.0))


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto 2x2: placas verdes, anel da torre, respiros nos cantos de tras e respiros em cunha nos da frente."""
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
        # canto da frente: respiro escuro em cunha apontando para o canto (sem circulos no teto)
        hx, hy = sx * 0.80, 0.81
        wedge = [(-0.11, -0.07), (0.11, -0.07), (0.11, 0.01), (0.0, 0.11), (-0.11, 0.01)]
        a = math.radians(-sx * 45)
        wp = [(hx + x * math.cos(a) - y * math.sin(a), hy + x * math.sin(a) + y * math.cos(a)) for x, y in wedge]
        fv = B.plate(f"fvent{sx}", wp, 0.05, 0.10, KM, slope=0.015, bevel=0.008, tags=tags)
        B.cut(fv, [B.rbox(f"fvc{sx}{i}", hx + math.sin(a) * (i - 0.5) * 0.05, hy - math.cos(a) * (i - 0.5) * 0.05,
                          0.15, 0.02, 0.08, 0.2, K, rot=-sx * 45, bevel=0.0) for i in range(2)])


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
    # bercos de cassetes (2 tubos com nariz claro e anel ambar fosco) nos 4 cantos, em diagonal
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
            B.cyl(f"cband{i}{k}", tx + ux * 0.085, ty + uy * 0.085, 0.13, 0.057, 0.02, M["ember"], axis="Y",
                  verts=12, yaw=rot, bevel=0.0, tags=tags)
    for i, (cx, cy, _r) in enumerate(crew_positions(w, h, 1, pv)):
        x, y = cx - w / 2, h / 2 - cy
        B.box(f"seat{i}", x, y + 0.02, 0.32, 0.30, 0.0, 0.14, A, bevel=0.04, tags=tags)
        B.box(f"console{i}", x, y + 0.30, 0.42, 0.12, 0.0, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.30, 0.32, 0.06, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
