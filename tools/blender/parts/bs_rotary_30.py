"""Canhao Rotativo Pesado 30 mm ("Furacao") - torre 4x4 de 7 canos estilo GAU-8, familia do 76 mm.

Mantelete macico em U (quadrado, chanfrado) em volta do grupo de canos, garras que avancam por fora
do mantelete e abracam os canos, casulos de turbina nos flancos (rotor de pas curvas num rebaixo
escuro), espinha central com sensor e a espiral do "Furacao" gravada, tambores de municao grandes nos
vaos com contador ambar e calhas de alimentacao ate o mantelete, saias traseiras e baia de exaustao.
Cano: um sprite com o grupo de 7 canos (gira phase*360/7 graus), caixa do motor octogonal atras,
cubo do rotor, luva traseira cinza com janelas, abracadeira do meio escura, abracadeira da frente clara
facetada (7 lados) com janelas transversais escuras e nariz em ponta (o nucleo visto pelas janelas
aquece), coroa escura e pontas de aco escuro que viram brasa nos quadros de giro.
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_rotary_30",
    "kind": "gun",
    "size": [4, 4],
    "pivot": [2.0, 1.55],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 3.36,            # lado do quadrado do sprite da torre
    "ring_r": 1.40,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "collider": 1.45,
    "barrels": {
        "ys": [0.0],               # um sprite = o grupo de 7 canos
        "root": 0.62,              # pivo -> raiz (traseira da caixa do motor)
        "length": 2.2,             # raiz -> boca
        "width": 0.80,             # largura do sprite (cabe a abracadeira da frente)
        "pad": 0.12,
        "anim": "spin",
        "spin_frames": 3,
        "spin_recoil": 0.03,       # o grupo treme para tras enquanto atira
        "heat": [0.5, 0.4, 0.3],   # pontas mornas durante o giro
        "interval": 0.05,
    },
    "lights": [
        {"at": [0.0, -1.30], "size": 1.6, "color": [255, 120, 30], "z": 0.9},
    ],
    "preview_pattern": "rotary",
}

RING_R = PART["ring_r"]
ROOT = PART["barrels"]["root"]
ZB = 0.60          # altura do eixo do grupo de canos (cabeca e cano usam a mesma)
NB = 7             # canos no grupo


def ycyl(name, x, y, z, r, length, mat, verts=8, roll=0.0, bevel=0.01, tags=(), r2=None):
    """Cilindro no eixo Y com giro (roll, graus) em torno do proprio eixo; r atras, r2 na frente."""
    ob = B.cyl(name, x, y, z, r, length, mat, axis="Y", verts=verts, bevel=bevel, tags=tags, r2=r2)
    ob.rotation_euler = (math.radians(-90), math.radians(roll), 0.0)
    return ob


def lines(target, name, specs, ztop, mat):
    """Linhas de painel recortadas no alvo: specs = [(x, y, comprimento, rotacao)]."""
    if target is None:
        return
    cuts = [B.rbox(f"{name}{i}", x, y, 0.016, ln, ztop - 0.02, ztop + 0.3, mat, rot=r, bevel=0.0)
            for i, (x, y, ln, r) in enumerate(specs)]
    B.cut(target, cuts)


def stroke(name, p, q, w, z0, z1, mat, tags=()):
    """Traco fino (caixa girada) de p ate q; pontas estendidas w/2 para emendar com o proximo."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    rot = math.degrees(math.atan2(-dx, dy))
    return B.rbox(name, (p[0] + q[0]) / 2, (p[1] + q[1]) / 2, w, math.hypot(dx, dy) + w, z0, z1, mat, rot=rot,
                  bevel=0.0, tags=tags)


def ngon(cx, cy, r, n, a0=0.0):
    return [(cx + r * math.cos(a0 + i * math.tau / n), cy + r * math.sin(a0 + i * math.tau / n)) for i in range(n)]


def motor_block(M, tags, y0, pre):
    """Caixa do motor do grupo (fixa): octogono escuro com 2 canais no topo, tampa e cintas de aco.
    Usada no cano e repetida na cabeca (berco), para ficar igual com qualquer ordem de desenho."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    mb = ycyl(pre + "motor", 0, y0 + 0.25, ZB, 0.35, 0.50, KM, verts=8, roll=22.5, bevel=0.014, tags=tags)
    B.cut(mb, [B.box(f"{pre}mch{sx}", sx * 0.12, y0 + 0.26, 0.045, 0.40, ZB + 0.28, ZB + 0.6, K, bevel=0.0)
               for sx in (-1, 1)])
    ycyl(pre + "mcap", 0, y0 + 0.015, ZB, 0.30, 0.03, S, verts=8, roll=22.5, bevel=0.005, tags=tags)
    B.box(pre + "mhatch", 0, y0 + 0.27, 0.15, 0.26, ZB + 0.30, ZB + 0.345, M["armor_mid"], bevel=0.01, tags=tags)
    B.box(pre + "mhatchb", 0, y0 + 0.17, 0.09, 0.03, ZB + 0.34, ZB + 0.355, S, bevel=0.004, tags=tags)
    for i, d in enumerate((0.10, 0.42)):
        ycyl(f"{pre}mband{i}", 0, y0 + d, ZB, 0.36, 0.035, S, verts=8, roll=22.5, bevel=0.005, tags=tags)
    # nariz afunilado ate o cubo do rotor
    ycyl(pre + "mnose", 0, y0 + 0.55, ZB, 0.35, 0.10, KM, verts=8, roll=22.5, bevel=0.008, tags=tags, r2=0.30)


def turbine(M, tags, cx, cy, mir, targets, name):
    """Disco de turbina: alojamento claro facetado (12 lados) com rebaixo escuro, rotor de pas curvas
    (redemoinho) e cubo com pip ambar. mir = funcao de espelho do lado."""
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    R0, R1 = 0.34, 0.25
    a0 = math.pi / 12
    ha, hp = B.shard(name + "_hous", mir(ngon(cx, cy, R0, 12, a0)), 0.70, 0.86, A, slope=0.035, groove=0.02,
                     panel_h=0.018, tags=tags)
    hole = mir(ngon(cx, cy, R1, 12, a0))
    for k, t in enumerate([ha, hp] + list(targets)):
        if t is not None:
            B.cut(t, [B.loft(f"{name}_hc{k}", hole, hole, 0.50, 1.3, K, bevel=0.0)])
    B.loft(name + "_bed", hole, hole, 0.48, 0.505, M["black"], bevel=0.0, tags=tags)
    # respiros radiais no aro (6 fendas curtas)
    if hp is not None:
        cuts = []
        for i in range(6):
            a = a0 + math.pi / 6 + i * math.tau / 6
            px, py = cx + math.cos(a) * 0.295, cy + math.sin(a) * 0.295
            cuts.append(B.rbox(f"{name}_v{i}", *mir([(px, py)])[0], 0.022, 0.06, 0.85, 1.2, K,
                               rot=math.degrees(a) - 90 if mir([(1, 0)])[0][0] > 0 else 90 - math.degrees(a),
                               bevel=0.0))
        B.cut(hp, cuts)
    # rotor: 9 pas curvas (varridas 55 graus), aco escuro sobre o fundo preto
    nbl, ri, ro, sw = 9, 0.085, 0.235, math.radians(55)
    for i in range(nbl):
        th = i * math.tau / nbl
        lead, trail = [], []
        for j in range(5):
            t = j / 4
            r = ri + (ro - ri) * t
            a = th + sw * t
            hw = math.radians(11 - 4 * t)
            lead.append((cx + r * math.cos(a + hw), cy + r * math.sin(a + hw)))
            trail.append((cx + r * math.cos(a - hw), cy + r * math.sin(a - hw)))
        B.plate(f"{name}_bl{i}", mir(lead + trail[::-1]), 0.52, 0.60, S, slope=0.008, bevel=0.0, tags=tags)
    B.plate(name + "_hub", mir(ngon(cx, cy, 0.095, 8, math.pi / 8)), 0.52, 0.68, KM, slope=0.015, bevel=0.008,
            tags=tags)
    B.plate(name + "_hubc", mir(ngon(cx, cy, 0.06, 8, math.pi / 8)), 0.66, 0.70, S, slope=0.01, bevel=0.004,
            tags=tags)
    B.plate(name + "_hubb", mir(ngon(cx, cy, 0.034, 8, math.pi / 8)), 0.695, 0.705, M["black"], slope=0.0,
            bevel=0.0, tags=tags)
    B.plate(name + "_hubg", mir(ngon(cx, cy, 0.018, 8, math.pi / 8)), 0.70, 0.71, M["glow_dim"], slope=0.0,
            bevel=0.0, tags=tags)
    return ha, hp


def head(M, T="head", phase=0.0):
    """Cabeca: mantelete em U em volta do grupo, garras externas, turbinas nos flancos, espinha."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    # anel giratorio e nucleo escuro
    B.cyl("ring", 0, 0, 0.04, RING_R + 0.02, 0.08, KM, axis="Z", verts=80, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, RING_R - 0.06, 28, 0.11), 0.09, 0.024, S, tags=tags)
    core = [(-1.02, -1.44), (1.02, -1.44), (1.52, -0.94), (1.52, 0.50), (1.02, 1.32), (-1.02, 1.32),
            (-1.52, 0.50), (-1.52, -0.94)]
    B.plate("core", core, 0.06, 0.36, K, slope=0.05, tags=tags)

    # ---------------------------------------------------------------- mantelete em U e berco do grupo
    mant = [(-0.96, 0.32), (0.96, 0.32), (1.04, 0.40), (1.04, 0.80), (0.72, 1.30), (0.46, 1.30), (0.46, 0.56),
            (-0.46, 0.56), (-0.46, 1.30), (-0.72, 1.30), (-1.04, 0.80), (-1.04, 0.40)]
    ma, mp = B.shard("mant", mant, 0.36, 0.90, A, slope=0.06, groove=0.03, panel_h=0.03, tags=tags)
    # berco escuro entre as bochechas, recuperadores e o motor (igual ao do sprite do cano)
    cr = B.plate("cradle", [(-0.46, 0.50), (0.46, 0.50), (0.46, 1.32), (-0.46, 1.32)], 0.28, 0.46, KM, slope=0.03,
                 tags=tags)
    B.cut(cr, [B.box("crad_c", 0, 0.92, 0.80, 0.70, 0.42, 0.9, K, bevel=0.0)])
    for sx in (-1, 1):
        B.cyl(f"recup{sx}", sx * 0.405, 0.92, 0.50, 0.032, 0.74, S, axis="Y", verts=10, tags=tags)
        B.cyl(f"recupb{sx}", sx * 0.405, 0.62, 0.50, 0.045, 0.12, KM, axis="Y", verts=10, tags=tags)
    motor_block(M, tags, ROOT, "h_")
    # sobrancelha (nivel 2) de cada bochecha, com fenda de pips; linha de painel na ponte do U
    brow = [(-0.60, 0.52), (-0.88, 0.52), (-0.92, 0.58), (-0.92, 0.76), (-0.70, 1.10), (-0.60, 1.10)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        ba, bp = B.shard(f"brow_{side}", f(brow), 0.90, 1.00, A, slope=0.05, groove=0.025, panel_h=0.02, tags=tags)
        Mo.slot_with_pips(f"bslot{side}", sx * 0.73, 0.60, 0.84, 0.06, 1.02, 4, M, tags, target=[ba, bp],
                          depth=0.035)
        lines(mp, f"mpl{side}", [(sx * 0.27, 0.44, 0.30, 90)], 0.93, K)

    # ---------------------------------------------------------------- garras externas que abracam os canos
    # largura minima ~0.2 em todo o comprimento: com o chanfro de 0.064 o topo nao pode estrangular
    claw = [(-1.10, 0.36), (-1.60, 0.36), (-1.60, 0.62), (-1.34, 1.06), (-1.04, 1.44), (-0.70, 1.62),
            (-0.50, 1.645), (-0.455, 1.575), (-0.455, 1.48), (-0.53, 1.41), (-0.78, 1.35), (-1.10, 0.80)]
    # painel desenhado a mao: a ponta e fina demais para o painel automatico (gerava uma lasca cruzada)
    claw_pnl = [(-1.20, 0.46), (-1.50, 0.46), (-1.50, 0.59), (-1.25, 1.00), (-0.99, 1.33), (-0.88, 1.40),
                (-0.886, 1.37), (-1.20, 0.83)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        ca = B.plate(f"claw_{side}", f(claw), 0.32, 0.72, A, slope=0.064, tags=tags)
        cp = B.plate(f"claw_{side}_pnl", f(claw_pnl), 0.716, 0.75, A, slope=0.012, bevel=0.0, tags=tags)
        # fenda acesa ao longo da garra (vocabulario do 76 mm)
        sxc, syc, rr = sx * 1.175, 0.98, sx * 36.5
        for t in (ca, cp):
            B.cut(t, [B.rbox(f"ccut{side}", sxc, syc, 0.05, 0.32, 0.66, 1.0, K, rot=rr, bevel=0.0)])
        B.rbox(f"cbed{side}", sxc, syc, 0.05, 0.32, 0.64, 0.665, M["black"], rot=rr, bevel=0.0, tags=tags)
        B.rbox(f"cglow{side}", sxc, syc, 0.016, 0.25, 0.665, 0.675, M["glow_dim"], rot=rr, bevel=0.0, tags=tags)
        lines(cp, f"cpl{side}", [(sx * 1.36, 0.50, 0.18, 90)], 0.75, K)

    # ---------------------------------------------------------------- casulos de turbina nos flancos
    pod = [(-0.92, -1.00), (-1.38, -1.00), (-1.60, -0.78), (-1.60, 0.10), (-1.44, 0.26), (-1.00, 0.26),
           (-0.92, 0.18)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        pa, pp = B.shard(f"pod_{side}", f(pod), 0.30, 0.74, A, slope=0.08, groove=0.035, panel_h=0.03, tags=tags)
        turbine(M, tags, -1.26, -0.30, f, (pa, pp), f"turb{side}")
        Mo.slot_with_pips(f"pslot{side}", -0.84, sx * 1.08, sx * 1.42, 0.055, 0.77, 3, M, tags, target=[pa, pp],
                          depth=0.045, vertical=False)
        lines(pp, f"ppl{side}", [(sx * 1.43, 0.10, 0.14, sx * 45)], 0.77, K)

    # ---------------------------------------------------------------- espinha com sensor e espiral
    spine = [(-0.30, -1.14), (0.30, -1.14), (0.38, -1.04), (0.38, -0.02), (0.22, 0.26), (-0.22, 0.26),
             (-0.38, -0.02), (-0.38, -1.04)]
    sa, sp = B.shard("spine", spine, 0.32, 0.84, A, slope=0.08, groove=0.035, panel_h=0.03, tags=tags)
    sp2 = [(-0.21, -0.94), (0.21, -0.94), (0.25, -0.86), (0.25, -0.08), (0.11, 0.14), (-0.11, 0.14),
           (-0.25, -0.08), (-0.25, -0.86)]
    s2 = B.plate("spine2", sp2, 0.86, 0.96, A, slope=0.03, tags=tags)
    win = [(-0.12, -0.09), (0.12, -0.09), (0.12, 0.02), (0.045, 0.10), (-0.045, 0.10), (-0.12, 0.02)]
    B.cut(s2, [B.loft("win_cut", win, win, 0.92, 1.2, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 0.915, 0.925, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, -0.02, 0.16, 0.026, 0.92, 0.932, M["lens"], bevel=0.0, tags=tags)
    # espiral do "Furacao": 2 bracos curvos (sulcos escuros) em volta de um olho com pip ambar
    c = (0.0, -0.46)
    cuts = []
    for k in range(2):
        pts = []
        for j in range(9):
            t = j / 8
            a = math.radians(80 + 180 * k + 190 * t)
            r = 0.06 + 0.115 * t
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a) * 1.12))
        for j in range(8):
            w = 0.036 - 0.012 * j / 7       # braco afina para a ponta
            cuts.append(stroke(f"sw_c{k}{j}", pts[j], pts[j + 1], w, 0.93, 1.2, K))
            stroke(f"sw_b{k}{j}", pts[j], pts[j + 1], w, 0.92, 0.932, M["black"], tags)
    eye = ngon(c[0], c[1], 0.045, 8, math.pi / 8)
    cuts.append(B.loft("sw_eye_c", eye, eye, 0.93, 1.2, K, bevel=0.0))
    B.cut(s2, cuts)
    Mo.slot_with_pips("sp", -0.80, -0.12, 0.12, 0.05, 0.96, 3, M, tags, target=s2, depth=0.03, vertical=False)
    B.loft("sw_eye_bed", eye, eye, 0.92, 0.932, M["black"], bevel=0.0, tags=tags)
    pip = ngon(c[0], c[1], 0.02, 8, math.pi / 8)
    B.loft("sw_eye_pip", pip, pip, 0.93, 0.94, M["glow_dim"], bevel=0.0, tags=tags)
    lines(sp, "spl", [(0.0, -1.02, 0.18, 90)], 0.87, K)

    # ---------------------------------------------------------------- tambores de municao e calhas
    for sx in (-1, 1):
        x = sx * 0.645
        B.cyl(f"drum{sx}", x, -0.52, 0.46, 0.15, 0.92, KM, axis="Y", verts=8, bevel=0.012, tags=tags)
        for i, y in enumerate((-0.90, -0.56, -0.14)):
            B.cyl(f"drumring{sx}{i}", x, y, 0.46, 0.162, 0.04, S, axis="Y", verts=8, bevel=0.005, tags=tags)
        B.box(f"drumslot{sx}", x, -0.35, 0.05, 0.30, 0.595, 0.605, M["black"], bevel=0.0, tags=tags)
        for i in range(4):
            B.box(f"drumled{sx}{i}", x, -0.465 + i * 0.075, 0.03, 0.04, 0.60, 0.615,
                  M["glow"] if i < 3 else M["black"], bevel=0.0, tags=tags)
        B.cyl(f"drumcap{sx}", x, -0.995, 0.46, 0.12, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=tags)
        # calha de alimentacao: tambor -> traseira do mantelete
        yaw = sx * 6.0
        B.cyl(f"chute{sx}", sx * 0.625, 0.16, 0.48, 0.065, 0.42, KM, axis="Y", verts=8, yaw=yaw, tags=tags)
        ux, uy = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        for i in range(3):
            t = -0.13 + i * 0.13
            B.cyl(f"chuter{sx}{i}", sx * 0.625 + ux * t, 0.16 + uy * t, 0.48, 0.074, 0.03, S, axis="Y", verts=8,
                  yaw=yaw, tags=tags)

    # ---------------------------------------------------------------- saias traseiras e baia de exaustao
    apron = [(-0.56, -1.08), (-1.36, -1.08), (-1.00, -1.42), (-0.56, -1.42)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        aa, ap = B.shard(f"apron_{side}", f(apron), 0.30, 0.58, A, slope=0.06, groove=0.03, panel_h=0.025,
                         tags=tags)
        Mo.slot_with_pips(f"aslot{side}", -1.25, sx * 0.66, sx * 0.94, 0.05, 0.605, 3, M, tags, target=[aa, ap],
                          depth=0.03, vertical=False)
        lines(ap, f"apl{side}", [(sx * 1.08, -1.20, 0.16, sx * 45)], 0.605, K)
        B.box(f"module{sx}", sx * 0.70, -1.02, 0.18, 0.05, 0.36, 0.42, KM, bevel=0.008, tags=tags)
    B.box("vent_bay", 0, -1.30, 0.86, 0.22, 0.20, 0.38, M["black"], bevel=0.0, tags=tags)
    for i in range(6):
        B.box(f"louver{i}", 0, -1.395 + i * 0.038, 0.82, 0.018, 0.30, 0.39, KM, bevel=0.004, tags=tags)
    for i in range(6):
        B.box(f"vent_pip{i}", -0.35 + i * 0.14, -1.19, 0.06, 0.024, 0.34, 0.40, M["glow"], bevel=0.0, tags=tags)


def ported_block(name, ya, yb, nose, r, rn, ports, M, rot, tags, hot_core, mat=None):
    """Bloco facetado de 7 lados (gira com o grupo) com nariz chanfrado e janelas transversais escuras
    no topo (como o freio do 76 mm); o nucleo escuro aparece no fundo das janelas (e aquece se hot_core)."""
    A, K = mat or M["armor"], M["core"]
    z = ZB
    body = ycyl(name, 0, (ya + yb - nose) / 2, z, r, yb - nose - ya, A, verts=NB, roll=rot, bevel=0.012,
                tags=tags)
    tip = None
    if nose > 0:
        tip = ycyl(name + "_nose", 0, yb - nose / 2, z, r, nose, A, verts=NB, roll=rot, bevel=0.008, tags=tags,
                   r2=rn)
    cuts = [B.box(f"{name}_p{i}", 0, y, 0.80, 0.045, z + r - 0.11, z + 0.6, K, bevel=0.0)
            for i, y in enumerate(ports)]
    B.cut(body, cuts)
    ycyl(name + "_core", 0, (ya + yb - nose) / 2, z, r - 0.07, yb - nose - ya - 0.02, K, verts=NB, roll=rot,
         bevel=0.0, tags=hot_core)
    return body, tip


def barrel(M, L=2.2, T="barrel", phase=0.0):
    """Grupo de 7 canos: raiz (y=0) na caixa do motor, boca em y=L. phase gira o grupo phase*360/7 graus."""
    tags = (T,)
    hot = (T, "hot")
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = ZB
    rot = phase * 360.0 / NB
    spinning = phase > 1e-6       # fase 0 = repouso; as outras = quadros de giro (atirando)
    # caixa do motor (fixa)
    motor_block(M, tags, 0.0, "b_")
    # cubo do rotor (gira) e eixo central de aco
    ycyl("b_hub", 0, 0.665, z, 0.33, 0.13, S, verts=NB, roll=rot, bevel=0.012, tags=tags)
    ycyl("b_axle", 0, 1.35, z, 0.09, 1.20, S, verts=NB, roll=rot, bevel=0.0, tags=tags)
    # luva traseira cinza escura (parte do motor/tambor): a peca clara do grupo e a abracadeira da frente
    ported_block("b_jacket", 0.74, 0.99, 0.0, 0.335, None, (0.825, 0.905), M, rot, tags, tags, mat=AM)
    ycyl("b_jacketr", 0, 1.005, z, 0.31, 0.03, K, verts=NB, roll=rot, bevel=0.0, tags=tags)
    # 7 canos grossos em volta do eixo (fase 0 = um cano no topo)
    Rc, rb = 0.222, 0.074
    y0, ym, yt = 0.98, L - 0.26, L - 0.12
    for i in range(NB):
        a = math.radians(i * 360.0 / NB + rot)
        bx, bz = Rc * math.sin(a), z + Rc * math.cos(a)
        ycyl(f"b_bar{i}", bx, (y0 + ym) / 2, bz, rb, ym - y0, A, verts=8, roll=rot + 22.5, bevel=0.005, tags=tags,
             r2=rb * 0.92)
        ycyl(f"b_barf{i}", bx, (ym + yt) / 2, bz, rb * 0.84, yt - ym, S, verts=8, roll=rot + 22.5, bevel=0.004,
             tags=tags)
        # ponta (so ela aquece); nos quadros de giro vira brasa, para o calor ler laranja e nao dourado
        ycyl(f"b_tip{i}", bx, (yt + L - 0.012) / 2, bz, rb * 0.98, L - 0.012 - yt, M["ember"] if spinning else KM,
             verts=8, roll=rot + 22.5, bevel=0.005, tags=hot)
    # abracadeira do meio: anel escuro de 7 lados com aro de aco
    ycyl("b_clamp_mid", 0, 1.27, z, 0.325, 0.08, KM, verts=NB, roll=rot, bevel=0.008, tags=tags)
    ycyl("b_clamp_midr", 0, 1.32, z, 0.31, 0.02, S, verts=NB, roll=rot, bevel=0.0, tags=tags)
    # abracadeira da frente: bloco claro facetado com 3 janelas e nariz em ponta (nucleo aquece)
    yc0, yc1 = L - 0.66, L - 0.26
    ported_block("b_clampf", yc0, yc1, 0.13, 0.368, 0.25, (yc0 + 0.065, yc0 + 0.135, yc0 + 0.205), M, rot, tags,
                 hot)
    ycyl("b_clampf_r", 0, yc0 - 0.012, z, 0.34, 0.024, K, verts=NB, roll=rot, bevel=0.0, tags=tags)
    # coroa escura logo atras das pontas
    ycyl("b_crown", 0, yt - 0.025, z, 0.29, 0.04, KM, verts=NB, roll=rot, bevel=0.006, tags=tags)


def roof(M, T="roof"):
    """Teto 4x4: placas verdes, anel da torre e faixa de 2 tambores grandes na fileira de tras."""
    tags = (T,)
    W, H = PART["size"]
    pv = PART["pivot"]
    green = B.mat_roof_green()
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    px, py = pv[0] - W / 2, H / 2 - pv[1]
    gap = 0.03
    B.box("deck_under", 0, 0, W, H, -0.05, 0.02, K, bevel=0.0, tags=tags)
    for tx in range(W):
        for ty in range(H):
            cx, cy = tx + 0.5 - W / 2, H / 2 - ty - 0.5
            poly = B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
            _, pnl = B.shard(f"deck{tx}_{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02,
                             tags=tags)
            if (tx + ty) % 2 == 0 and pnl is not None and ty < H - 1:
                B.cut(pnl, [B.rbox(f"dl{tx}{ty}", cx + 0.18, cy - 0.18, 0.012, 0.5, 0.07, 0.2, K, rot=45,
                                   bevel=0.0)])
    # anel da torre (sem pintura)
    B.torus("ringbear", px, py, 0.08, RING_R + 0.02, 0.055, KM, tags=tags)
    B.cyl("ringhole", px, py, 0.05, RING_R - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(px, py, RING_R + 0.11, 36)
           if abs(x) < W / 2 - 0.08 and -H / 2 + 0.9 < y < H / 2 - 0.08]
    B.bolts("rb", pts, 0.1, 0.022, S, tags=tags)
    # fileira de tras: bandeja escura com 2 tambores grandes deitados (contador ambar) e juncao de alimentacao
    sy = -H / 2 + 0.48
    B.plate("tray", B.rpoly(0, sy, W - 0.14, 0.80, 0, chamfer=0.12), 0.04, 0.10, KM, slope=0.025, tags=tags)
    B.plate("trayb", B.rpoly(0, sy, W - 0.40, 0.58, 0, chamfer=0.08), 0.09, 0.105, M["black"], slope=0.0,
            bevel=0.0, tags=tags)
    for sx in (-1, 1):
        dx = sx * 1.00
        B.cyl(f"rdrum{sx}", dx, sy, 0.27, 0.21, 1.36, KM, axis="X", verts=8, bevel=0.012, tags=tags)
        for i, d in enumerate((-0.58, -0.20, 0.20, 0.58)):
            B.cyl(f"rdring{sx}{i}", dx + d, sy, 0.27, 0.225, 0.045, S, axis="X", verts=8, bevel=0.005, tags=tags)
        B.cyl(f"rdcap{sx}", dx + sx * 0.70, sy, 0.27, 0.17, 0.05, S, axis="X", verts=8, bevel=0.006, tags=tags)
        # contador: fenda escura no topo entre os aneis do meio, 4 pips (3 acesos)
        B.box(f"rdslot{sx}", dx, sy, 0.30, 0.06, 0.47, 0.485, M["black"], bevel=0.0, tags=tags)
        for i in range(4):
            B.box(f"rdled{sx}{i}", dx - 0.105 + i * 0.07, sy, 0.04, 0.03, 0.48, 0.495,
                  M["glow_dim"] if i < 3 else M["black"], bevel=0.0, tags=tags)
        # calha que sai da ponta interna do tambor ate a juncao central
        B.cyl(f"rfeed{sx}", sx * 0.24, sy + 0.12, 0.30, 0.07, 0.30, KM, axis="X", verts=8, bevel=0.008, tags=tags)
        B.cyl(f"rfeedr{sx}", sx * 0.24, sy + 0.12, 0.30, 0.08, 0.03, S, axis="X", verts=8, bevel=0.004, tags=tags)
    # juncao central: bloco facetado com respiro e calha nervurada ate o anel
    j = B.plate("junction", B.rpoly(0, sy + 0.04, 0.26, 0.40, 0, chamfer=0.07), 0.08, 0.36, M["armor_mid"],
                slope=0.025, tags=tags)
    B.cut(j, [B.box(f"jv{i}", 0, sy - 0.06 + i * 0.06, 0.16, 0.025, 0.33, 0.5, K, bevel=0.0) for i in range(3)])
    cy0, cy1 = sy + 0.24, py - RING_R - 0.04
    if cy1 > cy0 + 0.04:
        B.box("feed", 0, (cy0 + cy1) / 2, 0.16, cy1 - cy0, 0.05, 0.14, KM, bevel=0.012, slope=0.01, tags=tags)
        B.box("feedrib", 0, (cy0 + cy1) / 2, 0.18, 0.03, 0.05, 0.155, S, bevel=0.004, tags=tags)


def floor(M, T="floor"):
    """Piso padrao (bancos, consoles, estantes de carregadores) com os 4 postos da tripulacao."""
    from bsgen.common import crew_positions
    W, H = PART["size"]
    pv = PART["pivot"]
    Mo.hull_floor(M, W, H, pv, RING_R, crew_positions(W, H, 4, pv), T)
