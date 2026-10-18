"""Canhao Rotativo Pesado 30 mm ("Furacao") - torre 4x4 de 7 canos estilo GAU-8, familia do 76 mm.

Mantelete em U em volta do grupo de canos: duas bochechas macicas chanfradas (borda traseira em chevron)
e uma travessa baixa cinza escura atras do motor; garras facetadas que avancam por fora do mantelete e
terminam em presa junto aos canos (com pistoes no vao), casulos de turbina nos flancos (rotor de pas
curvas escuras com escora diagonal num rebaixo sob um capuz blindado, cortes em diagonal no sentido do
giro), espinha central com sensor e a espiral do "Furacao" gravada em linhas finas, tambores de
municao nos vaos com contador ambar e calhas ate o mantelete, saias traseiras em V e baia de exaustao.
O anel da torre aparece atras e nas diagonais traseiras.
Cano: um sprite com o grupo de 7 canos (gira phase*360/7 graus): caixa do motor curta atras, cubo escuro
do rotor com aro de aco, luva cinza curta, ~1 tile de canos nus com abracadeira escura no meio e colares
de aco, abracadeira da frente clara facetada (7 lados) com 3 janelas transversais e nariz em ponta,
coroa escura, anel de aco e pontas escuras (so as pontas e o nucleo da abracadeira aquecem).
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
        {"at": [0.0, -1.03], "size": 1.6, "color": [255, 120, 30], "z": 0.9},
    ],
    "preview_pattern": "rotary",
}

RING_R = PART["ring_r"]
ROOT = PART["barrels"]["root"]
ZB = 0.60          # altura do eixo do grupo de canos (cabeca e cano usam a mesma)
NB = 7             # canos no grupo
MOTOR_L = 0.40     # caixa do motor + nariz (a partir da raiz); o cubo do rotor comeca aqui
MOUTH_X = 0.34     # meia largura da boca aberta na cabeca na frente do motor (o cubo/luva aparecem)
TURB = (-1.23, -0.27)                                   # centro do disco de turbina (lado esquerdo)
SLASHES = [(-1.25, -0.655), (-1.15, -0.655), (-1.05, -0.655)]   # cortes diagonais atras do disco


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


def mouth(name, K):
    """Cortador da boca: tira anel/nucleo/berco da cabeca na frente do motor (cubo e luva do cano aparecem
    com qualquer ordem de desenho)."""
    y0 = ROOT + MOTOR_L
    return B.box(name, 0, y0 + 0.45, 2 * MOUTH_X, 0.90, -0.1, 0.50, K, bevel=0.0)


def check_meshes(T):
    """Falha alto se algum objeto com a tag T avaliar para malha vazia (booleana ou offset quebrado)."""
    import bpy
    dg = bpy.context.evaluated_depsgraph_get()
    empty = []
    for o in B.objects_with(T):
        if o.type != "MESH":
            continue
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        if len(me.vertices) == 0:
            empty.append(o.name)
        e.to_mesh_clear()
    if empty:
        raise RuntimeError(f"bs_rotary_30: malhas vazias em '{T}': {empty}")


def cut_each(targets, make):
    """Recorta cada alvo com cortadores proprios (make(sufixo) -> lista de cortadores)."""
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, make(str(k)))


def motor_block(M, tags, y0, pre):
    """Caixa do motor do grupo (fixa, curta): octogono escuro com 2 canais e respiro de aletas de aco no
    topo, tampa e cintas de aco, nariz afunilado. Usada no cano e repetida na cabeca (berco)."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    mb = ycyl(pre + "motor", 0, y0 + 0.16, ZB, 0.35, 0.32, KM, verts=8, roll=22.5, bevel=0.014, tags=tags)
    cuts = [B.box(f"{pre}mch{sx}", sx * 0.12, y0 + 0.16, 0.045, 0.24, ZB + 0.27, ZB + 0.6, K, bevel=0.0)
            for sx in (-1, 1)]
    cuts.append(B.box(pre + "mvc", 0, y0 + 0.16, 0.12, 0.15, ZB + 0.25, ZB + 0.6, K, bevel=0.0))
    B.cut(mb, cuts)
    # respiro: fundo preto com 3 aletas de aco atravessadas
    B.box(pre + "mvbed", 0, y0 + 0.16, 0.12, 0.15, ZB + 0.245, ZB + 0.255, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"{pre}mrib{i}", 0, y0 + 0.115 + i * 0.045, 0.13, 0.016, ZB + 0.25, ZB + 0.305, S, bevel=0.003,
              tags=tags)
    ycyl(pre + "mcap", 0, y0 + 0.015, ZB, 0.30, 0.03, S, verts=8, roll=22.5, bevel=0.005, tags=tags)
    for i, d in enumerate((0.05, 0.27)):
        ycyl(f"{pre}mband{i}", 0, y0 + d, ZB, 0.36, 0.035, S, verts=8, roll=22.5, bevel=0.005, tags=tags)
    ycyl(pre + "mnose", 0, y0 + 0.36, ZB, 0.35, 0.08, KM, verts=8, roll=22.5, bevel=0.008, tags=tags, r2=0.30)


def turbine(M, tags, cx, cy, mir, targets, name, sx):
    """Disco de turbina: alojamento claro octogonal com rebaixo escuro, rotor de pas curvas (redemoinho),
    escora diagonal, cubo escuro e capuz blindado com entalhe em V cobrindo a frente do disco."""
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    R0, R1 = 0.29, 0.21
    a0 = math.pi / 8
    ha, hp = B.shard(name + "_hous", mir(ngon(cx, cy, R0, 8, a0)), 0.70, 0.84, A, slope=0.03, groove=0.018,
                     panel_h=0.016, tags=tags)
    hole = mir(ngon(cx, cy, R1, 8, a0))
    for k, t in enumerate([ha, hp] + list(targets)):
        if t is not None:
            B.cut(t, [B.loft(f"{name}_hc{k}", hole, hole, 0.50, 1.3, K, bevel=0.0)])
    B.loft(name + "_bed", hole, hole, 0.48, 0.505, M["black"], bevel=0.0, tags=tags)
    # rotor: 9 pas curvas (varridas 55 graus), aco escuro fosco sobre o fundo preto (fundo no rebaixo)
    DS = B.mat_metal("turb_blade", (0.10, 0.104, 0.112), rough=0.42, metal=0.9)
    nbl, ri, ro, sw = 9, 0.075, 0.192, math.radians(55)
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
        B.plate(f"{name}_bl{i}", mir(lead + trail[::-1]), 0.52, 0.58, DS, slope=0.008, bevel=0.0, tags=tags)
    # escora diagonal escura atravessando a tomada (le como entrada de ar, nao ventoinha)
    ex, ey = mir([(cx, cy)])[0]
    B.rbox(name + "_strut", ex, ey, 0.034, 2 * R1 * 0.98, 0.58, 0.64, KM, rot=sx * 45, bevel=0.006, tags=tags)
    B.rbox(name + "_struts", ex, ey, 0.010, 2 * R1 * 0.90, 0.64, 0.646, S, rot=sx * 45, bevel=0.0, tags=tags)
    B.plate(name + "_hub", mir(ngon(cx, cy, 0.075, 8, math.pi / 8)), 0.52, 0.68, KM, slope=0.015, bevel=0.008,
            tags=tags)
    B.plate(name + "_hubc", mir(ngon(cx, cy, 0.045, 8, math.pi / 8)), 0.66, 0.70, DS, slope=0.01, bevel=0.004,
            tags=tags)
    # capuz: borda da frente paralela ao topo do casulo, traseira com entalhe em V (expoe o cubo)
    hood = [(cx + 0.27, cy + 0.435), (cx - 0.27, cy + 0.30), (cx - 0.27, cy + 0.20), (cx - 0.17, cy + 0.11),
            (cx, cy + 0.20), (cx + 0.17, cy + 0.11), (cx + 0.27, cy + 0.19)]
    ka, kp = B.shard(name + "_hood", mir(hood), 0.80, 0.90, A, slope=0.035, groove=0.018, panel_h=0.018,
                     tags=tags)
    # dois cortes em diagonal no capuz, no sentido de varredura do rotor
    hs = [mir([(cx + dx, cy + 0.27 + dx * 0.25)])[0] for dx in (-0.135, 0.135)]
    cut_each((ka, kp), lambda k: [B.rbox(f"{name}_hs{k}{i}", x, y, 0.024, 0.13, 0.84, 1.2, K, rot=sx * 38,
                                         bevel=0.0) for i, (x, y) in enumerate(hs)])
    for i, (x, y) in enumerate(hs):
        B.rbox(f"{name}_hsb{i}", x, y, 0.024, 0.13, 0.82, 0.835, M["black"], rot=sx * 38, bevel=0.0, tags=tags)
    return ha, hp


def head(M, T="head", phase=0.0):
    """Cabeca: bochechas + travessa em U em volta do grupo, garras externas, turbinas nos flancos, espinha."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    # anel giratorio (boca aberta na frente do motor) e nucleo escuro de traseira recolhida
    rg = B.cyl("ring", 0, 0, 0.04, RING_R + 0.02, 0.08, KM, axis="Z", verts=80, bevel=0.01, tags=tags)
    B.cut(rg, [mouth("rmouth", K)])
    pts = [p for p in B.ring_points(0, 0, RING_R - 0.03, 28, 0.11) if not (abs(p[0]) < 0.5 and p[1] > 0.9)]
    B.bolts("ringbolt", pts, 0.09, 0.024, S, tags=tags)
    core = [(-0.56, -1.20), (0.56, -1.20), (1.00, -0.96), (1.48, -0.40), (1.48, 0.50), (1.02, 1.32),
            (-1.02, 1.32), (-1.48, 0.50), (-1.48, -0.40), (-1.00, -0.96)]
    cp = B.plate("core", core, 0.06, 0.36, K, slope=0.05, tags=tags)
    B.cut(cp, [mouth("cmouth", K)])

    # ---------------------------------------------------------------- mantelete em U e berco do grupo
    # duas bochechas macicas (borda traseira a 14 graus, mesmo chevron dos casulos e das garras) e uma
    # travessa baixa cinza escura atras do motor: o fundo do U fica em outro nivel (quebra a faixa)
    cheek = [(-0.96, 0.28), (-0.46, 0.405), (-0.46, 1.30), (-0.72, 1.30), (-1.02, 0.80), (-1.02, 0.34)]
    for side, f in (("L", lambda p: p), ("R", Mo.mirror)):
        B.shard(f"mant_{side}", f(cheek), 0.36, 0.90, A, slope=0.055, groove=0.03, panel_h=0.03, tags=tags)
    yoke = [(-0.30, 0.40), (0.30, 0.40), (0.36, 0.46), (0.36, 0.63), (-0.36, 0.63), (-0.36, 0.46)]
    yk = B.plate("yoke", yoke, 0.36, 0.64, AM, slope=0.035, tags=tags)
    lines(yk, "ykl", [(0.0, 0.50, 0.50, 90)], 0.64, K)
    B.bolts("ykbolt", [(-0.25, 0.555), (0.25, 0.555)], 0.64, 0.022, S, tags=tags)
    # berco escuro em cunha entre as bochechas, recuperadores e o motor (igual ao do sprite do cano)
    crad = [(-0.46, 0.52), (0.46, 0.52), (0.46, 1.16), (0.34, 1.32), (-0.34, 1.32), (-0.46, 1.16)]
    cr = B.plate("cradle", crad, 0.28, 0.46, KM, slope=0.03, tags=tags)
    B.cut(cr, [B.box("crad_c", 0, 0.86, 0.80, 0.56, 0.42, 0.9, K, bevel=0.0), mouth("crmouth", K)])
    for sx in (-1, 1):
        B.cyl(f"recup{sx}", sx * 0.405, 0.89, 0.50, 0.032, 0.66, S, axis="Y", verts=10, tags=tags)
        B.cyl(f"recupb{sx}", sx * 0.405, 0.62, 0.50, 0.045, 0.12, KM, axis="Y", verts=10, tags=tags)
    motor_block(M, tags, ROOT, "h_")
    # sobrancelha (nivel 2) de cada bochecha, com fenda de pips
    brow = [(-0.60, 0.52), (-0.88, 0.50), (-0.92, 0.56), (-0.92, 0.76), (-0.70, 1.10), (-0.60, 1.10)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        ba, bp = B.shard(f"brow_{side}", f(brow), 0.90, 1.00, A, slope=0.05, groove=0.025, panel_h=0.02, tags=tags)
        Mo.slot_with_pips(f"bslot{side}", sx * 0.73, 0.60, 0.84, 0.06, 1.02, 4, M, tags, target=[ba, bp],
                          depth=0.065)

    # ---------------------------------------------------------------- garras externas em presa
    # base inclinada (paralela ao topo do casulo), faceta externa com degrau, presa em ponta junto aos canos
    claw = [(-1.12, 0.2675), (-1.60, 0.1475), (-1.60, 0.62), (-1.42, 0.91), (-1.35, 0.89), (-1.14, 1.24),
            (-0.64, 1.65), (-0.455, 1.60), (-0.50, 1.52), (-0.80, 1.30), (-1.12, 0.82)]
    # painel desenhado a mao, rombo antes da lamina estreita (ponta fina invertia no bisel e a malha sumia)
    claw_pnl = [(-1.22, 0.37), (-1.50, 0.30), (-1.50, 0.60), (-1.345, 0.85), (-1.29, 0.835), (-1.09, 1.17),
                (-0.98, 1.19), (-1.04, 1.06), (-1.22, 0.79)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        ca = B.plate(f"claw_{side}", f(claw), 0.32, 0.72, A, slope=0.064, tags=tags)
        cp_ = B.plate(f"claw_{side}_pnl", f(claw_pnl), 0.716, 0.75, A, slope=0.012, bevel=0.0, tags=tags)
        # fenda acesa ao longo da garra (vocabulario do 76 mm)
        sxc, syc, rr = sx * 1.17, 1.00, sx * 31.0
        for t in (ca, cp_):
            B.cut(t, [B.rbox(f"ccut{side}", sxc, syc, 0.05, 0.30, 0.66, 1.0, K, rot=rr, bevel=0.0)])
        B.rbox(f"cbed{side}", sxc, syc, 0.05, 0.30, 0.64, 0.665, M["black"], rot=rr, bevel=0.0, tags=tags)
        B.rbox(f"cglow{side}", sxc, syc, 0.016, 0.23, 0.665, 0.675, M["glow_dim"], rot=rr, bevel=0.0, tags=tags)
        lines(cp_, f"cpl{side}", [(sx * 1.36, 0.42, 0.20, sx * 76)], 0.75, K)
        # pistao hidraulico no vao garra/bochecha (a garra le como articulada)
        B.cyl(f"piston{side}", sx * 0.90, 1.07, 0.56, 0.026, 0.34, S, axis="Y", verts=12, yaw=sx * 32.3, tags=tags)
        B.cyl(f"pistonb{side}", sx * 1.00, 0.91, 0.56, 0.042, 0.14, KM, axis="Y", verts=12, yaw=sx * 32.3,
              tags=tags)

    # ---------------------------------------------------------------- casulos de turbina nos flancos
    # canto traseiro externo cortado, degrau no flanco, topo inclinado (converge para a frente)
    pod = [(-0.90, -0.86), (-1.20, -0.86), (-1.50, -0.58), (-1.50, -0.36), (-1.60, -0.26), (-1.60, 0.03),
           (-1.53, 0.0825), (-1.00, 0.215), (-0.90, 0.14)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        pa, pp = B.shard(f"pod_{side}", f(pod), 0.30, 0.74, A, slope=0.08, groove=0.035, panel_h=0.03, tags=tags)
        turbine(M, tags, *TURB, f, (pa, pp), f"turb{side}", sx)
        # 3 cortes em diagonal atras do disco, no sentido do giro (redemoinho)
        sl = [f([p])[0] for p in SLASHES]
        cut_each((pa, pp), lambda k: [B.rbox(f"psl{side}{k}{i}", x, y, 0.026, 0.14, 0.68, 1.2, K, rot=sx * -40,
                                             bevel=0.0) for i, (x, y) in enumerate(sl)])
        for i, (x, y) in enumerate(sl):
            B.rbox(f"pslbed{side}{i}", x, y, 0.026, 0.14, 0.66, 0.675, M["black"], rot=sx * -40, bevel=0.0,
                   tags=tags)
        lines(pp, f"ppl{side}", [(sx * 1.47, -0.30, 0.20, 0)], 0.77, K)

    # ---------------------------------------------------------------- espinha com sensor e espiral
    spine = [(-0.30, -0.90), (0.30, -0.90), (0.38, -0.80), (0.38, -0.04), (0.20, 0.30), (-0.20, 0.30),
             (-0.38, -0.04), (-0.38, -0.80)]
    sa, sp = B.shard("spine", spine, 0.32, 0.84, A, slope=0.08, groove=0.035, panel_h=0.03, tags=tags)
    sp2 = [(-0.21, -0.76), (0.21, -0.76), (0.25, -0.68), (0.25, -0.10), (0.11, 0.17), (-0.11, 0.17),
           (-0.25, -0.10), (-0.25, -0.68)]
    s2 = B.plate("spine2", sp2, 0.86, 0.96, A, slope=0.03, tags=tags)
    win = [(-0.12, -0.10), (0.12, -0.10), (0.12, 0.01), (0.045, 0.09), (-0.045, 0.09), (-0.12, 0.01)]
    B.cut(s2, [B.loft("win_cut", win, win, 0.92, 1.2, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 0.915, 0.925, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, -0.02, 0.16, 0.026, 0.92, 0.932, M["lens"], bevel=0.0, tags=tags)
    # espiral do "Furacao": 3 bracos curvos (sulcos escuros) em volta de um olho com pip ambar
    c = (0.0, -0.40)
    cuts = []
    for k in range(3):
        pts = []
        for j in range(9):
            t = j / 8
            a = math.radians(90 + 120 * k + 165 * t)
            r = 0.055 + 0.135 * t
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
        for j in range(8):
            w = 0.032 - 0.012 * j / 7       # braco afina para a ponta (linha de painel, nao decalque)
            cuts.append(stroke(f"sw_c{k}{j}", pts[j], pts[j + 1], w, 0.93, 1.2, K))
            stroke(f"sw_b{k}{j}", pts[j], pts[j + 1], w, 0.92, 0.932, M["black"], tags)
    eye = ngon(c[0], c[1], 0.05, 8, math.pi / 8)
    cuts.append(B.loft("sw_eye_c", eye, eye, 0.93, 1.2, K, bevel=0.0))
    B.cut(s2, cuts)
    Mo.slot_with_pips("sp", -0.68, -0.12, 0.12, 0.05, 0.96, 3, M, tags, target=s2, depth=0.03, vertical=False)
    B.loft("sw_eye_bed", eye, eye, 0.92, 0.932, M["black"], bevel=0.0, tags=tags)
    pip = ngon(c[0], c[1], 0.022, 8, math.pi / 8)
    B.loft("sw_eye_pip", pip, pip, 0.93, 0.94, M["glow_dim"], bevel=0.0, tags=tags)
    lines(sp, "spl", [(0.0, -0.81, 0.16, 90)], 0.87, K)

    # ---------------------------------------------------------------- tambores de municao e calhas
    for sx in (-1, 1):
        x = sx * 0.645
        B.cyl(f"drum{sx}", x, -0.45, 0.46, 0.15, 0.78, KM, axis="Y", verts=8, bevel=0.012, tags=tags)
        for i, y in enumerate((-0.76, -0.45, -0.14)):
            B.cyl(f"drumring{sx}{i}", x, y, 0.46, 0.162, 0.04, S, axis="Y", verts=8, bevel=0.005, tags=tags)
        B.box(f"drumslot{sx}", x, -0.295, 0.05, 0.26, 0.595, 0.605, M["black"], bevel=0.0, tags=tags)
        for i in range(4):
            B.box(f"drumled{sx}{i}", x, -0.385 + i * 0.06, 0.03, 0.036, 0.60, 0.615,
                  M["glow"] if i < 3 else M["black"], bevel=0.0, tags=tags)
        B.cyl(f"drumcap{sx}", x, -0.855, 0.46, 0.12, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=tags)
        # calha de alimentacao: tambor -> traseira do mantelete
        yaw = sx * 6.0
        B.cyl(f"chute{sx}", sx * 0.625, 0.18, 0.48, 0.065, 0.48, KM, axis="Y", verts=8, yaw=yaw, tags=tags)
        ux, uy = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        for i in range(3):
            t = -0.15 + i * 0.15
            B.cyl(f"chuter{sx}{i}", sx * 0.625 + ux * t, 0.18 + uy * t, 0.48, 0.074, 0.03, S, axis="Y", verts=8,
                  yaw=yaw, tags=tags)

    # ---------------------------------------------------------------- saias traseiras em V e baia de exaustao
    apron = [(-0.50, -0.93), (-0.98, -0.93), (-0.74, -1.13), (-0.50, -1.18)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        aa, ap = B.shard(f"apron_{side}", f(apron), 0.30, 0.58, A, slope=0.05, groove=0.025, panel_h=0.025,
                         tags=tags)
        Mo.slot_with_pips(f"aslot{side}", -1.025, sx * 0.60, sx * 0.80, 0.045, 0.605, 3, M, tags,
                          target=[aa, ap], depth=0.07, vertical=False)
    B.box("vent_bay", 0, -1.035, 0.86, 0.21, 0.20, 0.38, M["black"], bevel=0.0, tags=tags)
    for i in range(6):
        B.box(f"louver{i}", 0, -1.125 + i * 0.036, 0.82, 0.018, 0.30, 0.39, KM, bevel=0.004, tags=tags)
    for i in range(6):
        B.box(f"vent_pip{i}", -0.35 + i * 0.14, -0.91, 0.06, 0.024, 0.34, 0.40, M["glow"], bevel=0.0, tags=tags)
    check_meshes(T)


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
    # caixa do motor (fixa, curta)
    motor_block(M, tags, 0.0, "b_")
    # cubo do rotor (gira) escuro; aro fino de aco com 14 lados (brilho constante, nao pisca no giro)
    ycyl("b_hub", 0, MOTOR_L + 0.05, z, 0.33, 0.10, KM, verts=NB, roll=rot, bevel=0.012, tags=tags)
    ycyl("b_hubr", 0, MOTOR_L + 0.075, z, 0.335, 0.02, S, verts=14, roll=rot, bevel=0.0, tags=tags)
    ycyl("b_axle", 0, 1.20, z, 0.09, 1.10, S, verts=NB, roll=rot, bevel=0.0, tags=tags)
    # luva traseira cinza escura curta (2 janelas) e aro escuro
    ported_block("b_jacket", 0.50, 0.65, 0.0, 0.335, None, (0.545, 0.605), M, rot, tags, tags, mat=AM)
    ycyl("b_jacketr", 0, 0.66, z, 0.31, 0.03, K, verts=NB, roll=rot, bevel=0.0, tags=tags)
    # 7 canos grossos em volta do eixo (fase 0 = um cano no topo): ~1 tile de canos nus a mostra
    Rc, rb = 0.235, 0.080
    y0, ym = 0.64, L - 0.16
    ys0, yt = L - 0.13, L - 0.06      # anel de aco (frio) e coroa escura da boca (so ela aquece)
    for i in range(NB):
        a = math.radians(i * 360.0 / NB + rot)
        bx, bz = Rc * math.sin(a), z + Rc * math.cos(a)
        ycyl(f"b_bar{i}", bx, (y0 + ym) / 2, bz, rb, ym - y0, A, verts=8, roll=rot + 22.5, bevel=0.005, tags=tags,
             r2=rb * 0.92)
        # colar de aco no meio do vao nu entre as abracadeiras
        ycyl(f"b_col{i}", bx, 1.45, bz, rb * 1.08, 0.03, S, verts=8, roll=rot + 22.5, bevel=0.004, tags=tags)
        ycyl(f"b_barf{i}", bx, (ys0 + yt) / 2, bz, rb * 0.86, yt - ys0, S, verts=8, roll=rot + 22.5, bevel=0.004,
             tags=tags)
        # ponta: aco escuro em todos os quadros (o calor do renderizador a deixa laranja queimado)
        ycyl(f"b_tip{i}", bx, (yt + L - 0.012) / 2, bz, rb * 0.96, L - 0.012 - yt, KM, verts=8,
             roll=rot + 22.5, bevel=0.005, tags=hot, r2=rb * 0.86)
    # abracadeira do meio: anel escuro de 7 lados com aro de aco (logo a frente das presas)
    ycm = 1.14
    ycyl("b_clamp_mid", 0, ycm, z, 0.345, 0.08, KM, verts=NB, roll=rot, bevel=0.008, tags=tags)
    ycyl("b_clamp_midr", 0, ycm + 0.05, z, 0.33, 0.02, S, verts=NB, roll=rot, bevel=0.0, tags=tags)
    # abracadeira da frente: bloco claro facetado com 3 janelas e nariz em ponta (nucleo aquece)
    yc0, yc1 = L - 0.46, L - 0.16
    ported_block("b_clampf", yc0, yc1, 0.09, 0.368, 0.25, (yc0 + 0.05, yc0 + 0.11, yc0 + 0.17), M, rot, tags,
                 hot)
    ycyl("b_clampf_r", 0, yc0 - 0.012, z, 0.34, 0.024, K, verts=NB, roll=rot, bevel=0.0, tags=tags)
    # coroa escura logo atras dos aneis de aco
    ycyl("b_crown", 0, L - 0.145, z, 0.30, 0.03, KM, verts=NB, roll=rot, bevel=0.006, tags=tags)
    check_meshes(T)


def roof(M, T="roof"):
    """Teto 4x4: placas verdes, anel da torre, 2 bercos de tambor separados na fileira de tras, escotilha
    no meio e calhas em V dos tambores ate o anel."""
    tags = (T,)
    W, H = PART["size"]
    pv = PART["pivot"]
    green = B.mat_roof_green()
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    drum_m = B.mat_metal("drum_matte", (0.04, 0.041, 0.045), rough=0.92, metal=0.0)   # fosco: nao reflete o verde
    ring_m = B.mat_metal("ring_matte", (0.20, 0.205, 0.215), rough=0.85, metal=0.0)    # aneis claros foscos
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
    # fileira de tras: dois bercos de tambor separados (convés verde em volta)
    sy = -H / 2 + 0.50
    for sx in (-1, 1):
        dx = sx * 1.10
        B.plate(f"tray{sx}", B.rpoly(dx, sy, 1.30, 0.60, 0, chamfer=0.10), 0.04, 0.10, drum_m, slope=0.025,
                tags=tags)
        B.plate(f"trayb{sx}", B.rpoly(dx, sy, 1.12, 0.44, 0, chamfer=0.07), 0.09, 0.105, M["black"], slope=0.0,
                bevel=0.0, tags=tags)
        B.cyl(f"rdrum{sx}", dx, sy, 0.27, 0.20, 1.06, drum_m, axis="X", verts=8, bevel=0.012, tags=tags)
        for i, d in enumerate((-0.40, -0.13, 0.13, 0.40)):
            B.cyl(f"rdring{sx}{i}", dx + d, sy, 0.27, 0.215, 0.04, ring_m, axis="X", verts=8, bevel=0.005, tags=tags)
        B.cyl(f"rdcap{sx}", dx + sx * 0.55, sy, 0.27, 0.16, 0.05, ring_m, axis="X", verts=8, bevel=0.006, tags=tags)
        # contador: fenda escura no topo entre os aneis do meio, 4 pips (3 acesos)
        B.box(f"rdslot{sx}", dx, sy, 0.20, 0.06, 0.455, 0.47, M["black"], bevel=0.0, tags=tags)
        for i in range(4):
            B.box(f"rdled{sx}{i}", dx - 0.075 + i * 0.05, sy, 0.03, 0.03, 0.465, 0.48,
                  M["glow_dim"] if i < 3 else M["black"], bevel=0.0, tags=tags)
        # calha nervurada em diagonal: ponta interna do tambor -> anel
        p0, p1 = (sx * 0.56, sy + 0.02), (sx * 0.30, py - RING_R + 0.02)
        ln = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        yaw = math.degrees(math.atan2(-(p1[0] - p0[0]), p1[1] - p0[1]))
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        B.cyl(f"rfeed{sx}", mx, my, 0.20, 0.07, ln, KM, axis="Y", verts=8, bevel=0.008, yaw=yaw, tags=tags)
        ux, uy = (p1[0] - p0[0]) / ln, (p1[1] - p0[1]) / ln
        for i in range(3):
            t = (i - 1) * ln * 0.30
            B.cyl(f"rfeedr{sx}{i}", mx + ux * t, my + uy * t, 0.20, 0.08, 0.03, S, axis="Y", verts=8, bevel=0.004,
                  yaw=yaw, tags=tags)
    # escotilha da tripulacao no meio (cinza, sem pintura) com alca e respiro
    hy = sy - 0.06
    B.plate("hatch", B.rpoly(0, hy, 0.46, 0.46, 0, chamfer=0.10), 0.06, 0.11, M["armor_mid"], slope=0.02,
            tags=tags)
    B.box("hatch_h", 0, hy - 0.12, 0.20, 0.045, 0.11, 0.14, S, bevel=0.008, tags=tags)
    hv = B.box("hatch_v", 0, hy + 0.07, 0.26, 0.14, 0.10, 0.125, KM, bevel=0.006, tags=tags)
    B.cut(hv, [B.box(f"hvc{i}", 0, hy + 0.035 + i * 0.035, 0.22, 0.016, 0.115, 0.2, K, bevel=0.0) for i in range(3)])
    check_meshes(T)


def floor(M, T="floor"):
    """Piso: placas, anel com placa octogonal de acionamento do rotor, 4 postos da tripulacao, estantes de
    carregadores na fileira de tras e 2 canais de alimentacao ate o anel (ecoam os 2 tambores do teto)."""
    from bsgen.common import crew_positions
    tags = (T,)
    W, H = PART["size"]
    pv = PART["pivot"]
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    px, py = pv[0] - W / 2, H / 2 - pv[1]
    B.box("fl_base", 0, 0, W, H, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for tx in range(W):
        for ty in range(H):
            x0, y1 = tx - W / 2 + 0.04, H / 2 - ty - 0.04
            B.box(f"fl{tx}{ty}", x0 + 0.46, y1 - 0.46, 0.92, 0.92, 0.0, 0.03, KM, bevel=0.01, tags=tags)
    # anel giratorio e placa octogonal de acionamento (cinza medio, centro escuro, eixo de aco)
    B.torus("fl_ring", px, py, 0.05, RING_R * 0.85, 0.05, AM, tags=tags)
    oct_ = lambda s: B.rpoly(px, py, s, s, 0, chamfer=s / (2 + math.sqrt(2)))  # noqa: E731
    w = RING_R * 0.66
    B.plate("fl_hub", oct_(w), 0.03, 0.11, AM, slope=0.03, tags=tags)
    B.plate("fl_hubc", oct_(w * 0.56), 0.09, 0.115, K, slope=0.015, tags=tags)
    B.plate("fl_hubs", ngon(px, py, w * 0.14, 7, math.pi / 2), 0.11, 0.15, S, slope=0.01, bevel=0.006, tags=tags)
    B.bolts("fl_hubb", B.ring_points(px, py, w * 0.40, 8, math.pi / 8), 0.115, 0.018, S, tags=tags)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        cx, cy = px + math.cos(a) * RING_R * 0.62, py + math.sin(a) * RING_R * 0.62
        arrow = [(0.10, 0.0), (-0.06, 0.10), (-0.02, 0.0), (-0.06, -0.10)]
        ca, sa = math.cos(a), math.sin(a)
        arrow = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in arrow]
        B.plate(f"fl_chev{k}", arrow, 0.03, 0.07, A, slope=0.01, bevel=0.006, tags=tags)
    B.box("fl_led_t", px, py + RING_R * 0.95, 0.3, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # estantes de carregadores na fileira de tras
    for tx in range(W):
        x = tx - W / 2 + 0.5
        B.box(f"rack{tx}", x, -H / 2 + 0.13, 0.78, 0.18, 0.0, 0.16, AM, bevel=0.01, tags=tags)
        for i in range(3):
            B.box(f"mag{tx}{i}", x - 0.24 + i * 0.24, -H / 2 + 0.13, 0.16, 0.12, 0.16, 0.24, KM, bevel=0.01,
                  tags=tags)
            B.box(f"magled{tx}{i}", x - 0.24 + i * 0.24, -H / 2 + 0.13, 0.10, 0.03, 0.24, 0.26, M["glow_dim"],
                  bevel=0.0, tags=tags)
    # 2 canais de alimentacao (x = +-0.14) das estantes ate o anel
    y0, y1 = -H / 2 + 0.24, py - RING_R * 0.85 - 0.06
    for sx in (-1, 1):
        x = sx * 0.14
        B.box(f"fl_feed{sx}", x, (y0 + y1) / 2, 0.13, y1 - y0, 0.0, 0.07, KM, bevel=0.01, tags=tags)
        B.box(f"fl_feedbed{sx}", x, (y0 + y1) / 2, 0.07, y1 - y0 - 0.04, 0.07, 0.075, M["black"], bevel=0.0,
              tags=tags)
        n = 4
        for i in range(n):
            y = y0 + (i + 0.5) * (y1 - y0) / n
            B.box(f"fl_feedrib{sx}{i}", x, y, 0.15, 0.022, 0.0, 0.085, S, bevel=0.004, tags=tags)
    B.box("fl_led_b", px, py - RING_R * 0.95, 0.12, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # postos da tripulacao (banco, console e tela)
    for i, (cx, cy, _r) in enumerate(crew_positions(W, H, 4, pv)):
        x, y = cx - W / 2, H / 2 - cy
        B.box(f"seat{i}", x, y + 0.02, 0.32, 0.30, 0.0, 0.14, A, bevel=0.04, tags=tags)
        B.box(f"console{i}", x, y + 0.30, 0.42, 0.12, 0.0, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.30, 0.32, 0.06, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
