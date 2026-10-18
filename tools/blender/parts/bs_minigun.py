"""Minigun de Convés ("Cigarra") - torre rotativa de 6 canos, 2x3, familia do 76 mm.

Cabeca de cigarra: mandibulas em lamina (com fenda de luz) que prendem o cubo do rotor, olhos compostos
facetados na raiz das asas, asas em tenda que varrem para tras ate pontas traseiras (sulcos paralelos ao
bordo de ataque + fenda de pips), tambor central com sensor e chevrons rebaixados, cinta de elos ate a
culatra, carregadores de 50 tiros e baia de exaustao entre as pontas das asas.
Cano: 6 canos em volta de um eixo de aco, cubo do rotor, abracadeira do meio escura, abracadeira da
frente larga com fendas, coroa da boca e pontas escuras que aquecem; caixa do motor afunilada atras.
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_minigun",
    "kind": "gun",
    "size": [2, 3],
    "pivot": [1.0, 1.0],           # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 2.2,
    "ring_r": 0.86,
    "accent": "amber",
    "barrels": {
        "ys": [0.0],               # um sprite = o grupo de 6 canos
        "root": 0.50,
        "length": 1.45,
        "width": 0.56,
        "pad": 0.12,
        "anim": "spin",
        "spin_frames": 3,
        "spin_recoil": 0.02,       # o grupo recua um pouco enquanto atira
        "heat": [0.4, 0.4, 0.4],    # pontas mornas constantes durante o giro (sem piscar)
        "interval": 0.05,
    },
    "lights": [
        {"at": [0.0, -0.80], "size": 1.0, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "rotary",
}

RING_R = PART["ring_r"]


def ycyl(name, x, y, z, r, length, mat, verts=8, roll=0.0, bevel=0.01, tags=(), r2=None):
    """Cilindro no eixo Y com giro (roll, graus) em torno do proprio eixo; r atras, r2 na frente."""
    ob = B.cyl(name, x, y, z, r, length, mat, axis="Y", verts=verts, bevel=bevel, tags=tags, r2=r2)
    ob.rotation_euler = (math.radians(-90), math.radians(roll), 0.0)
    return ob


def slot_rot(name, cx, cy, length, w, ztop, n, M, tags, rot, targets, depth=0.035):
    """Fenda de pips girada (eixo longo = y local girado por rot), recortada nos alvos."""
    for t in targets:
        B.cut(t, [B.rbox(name + "_cut", cx, cy, w, length, ztop - depth, ztop + 0.2, M["black"], rot=rot,
                         bevel=0.0)])
    B.rbox(name + "_bed", cx, cy, w, length, ztop - depth - 0.01, ztop - depth + 0.004, M["black"], rot=rot,
           bevel=0.0, tags=tags)
    a = math.radians(rot)
    ux, uy = -math.sin(a), math.cos(a)
    for i in range(n):
        s = ((i + 0.5) / n - 0.5) * length
        B.rbox(f"{name}_pip{i}", cx + ux * s, cy + uy * s, w * 0.55, length / n * 0.55, ztop - depth,
               ztop - depth + 0.012, M["glow"], rot=rot, bevel=0.0, tags=tags)


def line_clip(poly, cx, cy, ux, uy):
    """Trecho (t0, t1) da reta (cx, cy) + t*(ux, uy) que fica dentro do poligono, em volta de t=0."""
    ts = []
    n = len(poly)
    for i in range(n):
        (px, py), (qx, qy) = poly[i], poly[(i + 1) % n]
        ex, ey = qx - px, qy - py
        det = ex * uy - ux * ey
        if abs(det) < 1e-9:
            continue
        t = ((px - cx) * (-ey) + ex * (py - cy)) / det
        sp = (ux * (py - cy) - uy * (px - cx)) / det
        if -1e-9 <= sp <= 1 + 1e-9:
            ts.append(t)
    neg = [t for t in ts if t < 0]
    pos = [t for t in ts if t > 0]
    return (max(neg) if neg else 0.0), (min(pos) if pos else 0.0)


def head(M, T="head", phase=0.0):
    """Cabeca em ponta de flecha: mandibulas + asas em tenda formam uma linha continua ate a traseira."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    # anel giratorio e nucleo escuro em delta
    B.cyl("ring", 0, 0, 0.04, RING_R + 0.04, 0.08, KM, axis="Z", verts=64, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, RING_R - 0.03, 20, 0.16), 0.09, 0.02, S, tags=tags)
    core = [(-0.40, 0.72), (0.40, 0.72), (0.90, 0.02), (0.90, -0.62), (0.66, -0.96), (-0.66, -0.96),
            (-0.90, -0.62), (-0.90, 0.02)]
    B.plate("core", core, 0.06, 0.32, K, slope=0.05, tags=tags)

    # asa (bordo de ataque varrido ~35 graus, bordo de fuga em diagonal ate a ponta traseira)
    hind = [(-0.50, 0.50), (-0.60, 0.54), (-0.97, 0.02), (-0.97, -0.22), (-0.92, -0.28), (-0.92, -0.40),
            (-0.97, -0.46), (-0.97, -0.60), (-0.82, -1.00), (-0.74, -1.00), (-0.56, -0.76), (-0.54, -0.30)]
    fore = [(-0.58, 0.30), (-0.66, 0.36), (-0.90, 0.02), (-0.90, -0.20), (-0.84, -0.28), (-0.70, -0.22),
            (-0.58, -0.04)]
    # mandibula em lamina que afunila e curva para dentro ate o cubo do rotor
    mand = [(-0.66, 0.54), (-0.50, 0.57), (-0.34, 0.78), (-0.25, 0.98), (-0.29, 1.06), (-0.40, 1.03),
            (-0.60, 0.84), (-0.72, 0.66)]
    mand_pnl = [(-0.618, 0.624), (-0.542, 0.638), (-0.408, 0.814), (-0.385, 0.905), (-0.43, 0.885),
                (-0.542, 0.791), (-0.633, 0.655)]
    sweep = 35.4  # angulo do bordo de ataque (graus a partir do eixo y)
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        wa, wp = B.shard(f"hind_{side}", f(hind), 0.30, 0.58, A, slope=0.08, groove=0.035, panel_h=0.03, tags=tags)
        # nervuras: 2 sulcos retos paralelos ao bordo de ataque, de borda a borda do painel (so no painel),
        # com fundo preto recortado na forma do painel para a linha ler limpa vista de cima
        a = math.radians(sx * sweep)
        ux, uy = -math.sin(a), math.cos(a)
        inner = B.robust_offset(f(hind), 0.08 + 0.035 + 0.008)
        veins = ((0.74, -0.33), (0.755, -0.645))
        if wp is not None:
            B.cut(wp, [B.rbox(f"vein{side}{i}", sx * x, y, 0.022, 0.70, 0.585, 0.8, K, rot=sx * sweep, bevel=0.0)
                       for i, (x, y) in enumerate(veins)])
            for i, (x, y) in enumerate(veins):
                t0, t1 = line_clip(inner, sx * x, y, ux, uy)
                tm = (t0 + t1) / 2
                B.rbox(f"veinbed{side}{i}", sx * x + ux * tm, y + uy * tm, 0.022, t1 - t0, 0.579, 0.587, M["black"],
                       rot=sx * sweep, bevel=0.0, tags=tags)
        # fenda de pips entre as nervuras, na mesma direcao
        slot_rot(f"wslot{side}", sx * 0.765, -0.485, 0.20, 0.05, 0.61, 3, M, tags, sx * sweep,
                 [t for t in (wa, wp) if t is not None])
        # lamina superior em degrau, com vao escuro em volta (sombra de separacao)
        B.plate(f"foregap_{side}", B.offset_poly(f(fore), -0.03), 0.56, 0.625, M["black"], slope=0.0, bevel=0.0,
                tags=tags)
        B.shard(f"fore_{side}", f(fore), 0.56, 0.82, A, slope=0.08, groove=0.03, panel_h=0.025, tags=tags)
        # mandibula: base chanfrada + painel desenhado a mao (o automatico gera uma ponta degenerada)
        ma = B.plate(f"mand_{side}", f(mand), 0.30, 0.68, A, slope=0.055, tags=tags)
        # sem bisel no painel: as tiras finas ao lado da fenda inverteriam o bisel depois do recorte
        mp = B.plate(f"mand_{side}_pnl", f(mand_pnl), 0.676, 0.705, A, slope=0.014, bevel=0.0, tags=tags)
        # fenda com luz ao longo da mandibula (vocabulario do 76 mm)
        mx, my, mr = sx * 0.497, 0.77, sx * 35.2
        for t in (ma, mp):
            B.cut(t, [B.rbox(f"mcut{side}", mx, my, 0.045, 0.20, 0.64, 0.9, K, rot=mr, bevel=0.0)])
        B.rbox(f"mbed{side}", mx, my, 0.045, 0.20, 0.62, 0.645, M["black"], rot=mr, bevel=0.0, tags=tags)
        B.rbox(f"mglow{side}", mx, my, 0.016, 0.145, 0.645, 0.655, M["glow_dim"], rot=mr, bevel=0.0, tags=tags)
        # pistao hidraulico: flanco do mantelete -> borda interna da mandibula
        pyaw = -sx * 50.5
        pux, puy = -math.sin(math.radians(pyaw)), math.cos(math.radians(pyaw))
        B.cyl(f"piston{side}", sx * 0.335, 0.67, 0.45, 0.028, 0.24, S, axis="Y", verts=12, yaw=pyaw, tags=tags)
        B.cyl(f"pistonb{side}", sx * 0.335 - pux * 0.06, 0.67 - puy * 0.06, 0.45, 0.045, 0.11, KM, axis="Y",
              verts=12, yaw=pyaw, tags=tags)
        # olho composto: casulo facetado em losango na raiz da asa, aro de aco e 3 pips em triangulo
        ex, ey, er = sx * 0.62, 0.47, sx * sweep
        B.rbox(f"eye{side}", ex, ey, 0.18, 0.27, 0.50, 0.74, KM, rot=er, chamfer=0.07, slope=0.025, bevel=0.01,
               tags=tags)
        rim = B.rbox(f"eyerim{side}", ex, ey, 0.13, 0.21, 0.735, 0.765, S, rot=er, chamfer=0.05, slope=0.01,
                     bevel=0.005, tags=tags)
        B.cut(rim, [B.rbox(f"eyecut{side}", ex, ey, 0.085, 0.15, 0.748, 0.9, K, rot=er, chamfer=0.03, bevel=0.0)])
        B.rbox(f"eyebed{side}", ex, ey, 0.085, 0.15, 0.742, 0.75, M["black"], rot=er, chamfer=0.03, bevel=0.0,
               tags=tags)
        a = math.radians(er)
        ux, uy = -math.sin(a), math.cos(a)        # eixo longo do olho
        vx, vy = math.cos(a), math.sin(a)         # eixo curto
        for i, (s, t) in enumerate(((0.035, 0.0), (-0.025, -0.019), (-0.025, 0.019))):
            B.rbox(f"eyepip{side}{i}", ex + ux * s + vx * t, ey + uy * s + vy * t, 0.026, 0.026, 0.75, 0.758,
                   M["glow_dim"], rot=er, bevel=0.0, tags=tags)

    # mantelete escuro (de onde sai o grupo de canos)
    mant = [(-0.22, 0.36), (0.22, 0.36), (0.28, 0.48), (0.24, 0.80), (-0.24, 0.80), (-0.28, 0.48)]
    m = B.plate("mantlet", mant, 0.30, 0.62, KM, slope=0.05, tags=tags)
    B.cut(m, [B.box("mant_cut", 0, 0.70, 0.30, 0.20, 0.54, 0.9, K, bevel=0.0)])

    # tambor central gordo com proa em ponta, sensor e carapaca de chevrons rebaixados
    drum = [(-0.22, -0.70), (0.22, -0.70), (0.42, -0.50), (0.42, 0.04), (0.18, 0.40), (-0.18, 0.40),
            (-0.42, 0.04), (-0.42, -0.50)]
    da, dp = B.shard("drum", drum, 0.30, 0.82, A, slope=0.10, groove=0.035, panel_h=0.03, tags=tags)
    for k, tgt in enumerate((da, dp)):
        B.cut(tgt, [B.box(f"dl{k}{sx}", sx * 0.27, -0.32, 0.022, 0.72, 0.72, 0.95, K, bevel=0.0) for sx in (-1, 1)])
    c0 = [(-0.24, -0.06), (0.24, -0.06), (0.24, 0.04), (0.08, 0.28), (-0.08, 0.28), (-0.24, 0.04)]
    s0 = B.plate("cara0", c0, 0.84, 1.00, A, slope=0.03, tags=tags)
    win = [(-0.13, -0.01), (0.13, -0.01), (0.13, 0.04), (0.04, 0.17), (-0.04, 0.17), (-0.13, 0.04)]
    B.cut(s0, [B.loft("win_cut", win, win, 0.95, 1.2, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 0.945, 0.955, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, 0.05, 0.16, 0.026, 0.95, 0.962, M["lens"], bevel=0.0, tags=tags)
    chevs = []
    for i, (dy, hw, zt) in enumerate(((0.0, 0.27, 0.97), (-0.15, 0.23, 0.92))):
        chevs.append(([(-hw, -0.21 + dy), (0.0, -0.09 + dy), (hw, -0.21 + dy), (hw, -0.31 + dy),
                       (0.0, -0.19 + dy), (-hw, -0.31 + dy)], zt))
    if dp is not None:  # rebaixo em volta de cada chevron (o chevron nasce de dentro do rebaixo)
        B.cut(dp, [B.loft(f"chevcut{i}", B.offset_poly(c, -0.022), B.offset_poly(c, -0.022), 0.83, 1.2, K,
                          bevel=0.0) for i, (c, _) in enumerate(chevs)])
    for i, (c, zt) in enumerate(chevs):
        B.plate(f"chevbed{i}", B.offset_poly(c, -0.022), 0.824, 0.832, M["black"], slope=0.0, bevel=0.0, tags=tags)
        B.plate(f"chev{i}", c, 0.828, zt, A, slope=0.025, tags=tags)
    # fenda de 3 pips no fim do tambor (quebra entre chevrons e baia)
    Mo.slot_with_pips("dslot", -0.515, -0.12, 0.12, 0.045, 0.85, 3, M, tags, target=dp, depth=0.03, vertical=False)

    # baia de exaustao traseira entre as pontas das asas
    B.box("vent_bay", 0, -0.84, 0.40, 0.20, 0.30, 0.36, M["black"], bevel=0.0, tags=tags)
    for i in range(5):
        B.box(f"louver{i}", 0, -0.92 + i * 0.04, 0.36, 0.016, 0.30, 0.37, KM, bevel=0.003, tags=tags)
    for i, x in enumerate((-0.135, -0.045, 0.045, 0.135)):
        B.box(f"vent_pip{i}", x, -0.73, 0.035, 0.02, 0.34, 0.38, M["glow"], bevel=0.0, tags=tags)
    B.bolts("bolt", [(x, -0.90) for x in (-0.62, 0.62)], 0.35, 0.024, S, tags=tags)

    # carregadores de 50 tiros atras das asas (contador ambar) + cinta de elos ate a culatra
    for sx in (-1, 1):
        x = sx * 0.41
        B.box(f"mag{sx}", x, -0.82, 0.28, 0.30, 0.30, 0.52, KM, bevel=0.012, tags=tags)
        for i, y in enumerate((-0.92, -0.72)):
            B.box(f"magband{sx}{i}", x, y, 0.16, 0.025, 0.30, 0.53, S, bevel=0.004, tags=tags)
        for i in range(3):
            B.box(f"magled{sx}{i}", x, -0.87 + i * 0.05, 0.04, 0.025, 0.52, 0.54,
                  M["glow_dim"] if i < 2 else M["black"], bevel=0.0, tags=tags)
        # calha continua (leito escuro) com elos quase encostados
        B.rbox(f"beltbed{sx}", sx * 0.475, -0.18, 0.12, 0.88, 0.30, 0.39, KM, rot=sx * 1.5, bevel=0.008, tags=tags)
        for i in range(9):
            y = -0.58 + i * 0.10
            bx = sx * (0.477 - 0.0262 * (y + 0.18))
            B.rbox(f"link{sx}{i}", bx, y, 0.08, 0.08, 0.38, 0.44, KM, rot=sx * 1.5, bevel=0.008, tags=tags)
            B.cyl(f"round{sx}{i}", bx, y, 0.445, 0.021, 0.074, S, axis="X", verts=8, bevel=0.0, tags=tags)
        # calha angulada que entra pelo flanco do mantelete (como as calhas do 76 mm)
        cx, cy, yaw = sx * 0.38, 0.35, sx * 43.0
        B.cyl(f"chute{sx}", cx, cy, 0.42, 0.05, 0.27, KM, axis="Y", verts=8, yaw=yaw, tags=tags)
        ux, uy = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        for i, t in enumerate((-0.075, 0.065)):
            B.cyl(f"chuter{sx}{i}", cx + ux * t, cy + uy * t, 0.42, 0.058, 0.025, S, axis="Y", verts=8, yaw=yaw,
                  tags=tags)


def barrel(M, L=1.45, T="barrel", phase=0.0):
    """Grupo de 6 canos: raiz (y=0) na caixa do motor, boca em y=L. phase gira o grupo phase*60 graus."""
    tags = (T,)
    hot = (T, "hot")
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = 0.55
    rot = phase * 60.0
    spinning = phase > 1e-6       # fase 0 = quadro de repouso; as outras = quadros de giro (atirando)
    # caixa do motor (fixa): bloco octogonal escuro com 2 canais longitudinais e nariz afunilado
    hb = ycyl("b_motor", 0, 0.11, z, 0.24, 0.22, KM, verts=8, roll=22.5, bevel=0.012, tags=tags)
    B.cut(hb, [B.box(f"b_ch{sx}", sx * 0.075, 0.12, 0.035, 0.16, z + 0.19, z + 0.4, K, bevel=0.0) for sx in (-1, 1)])
    ycyl("b_motorcap", 0, 0.015, z, 0.20, 0.03, S, verts=8, roll=22.5, bevel=0.005, tags=tags)
    ycyl("b_nose", 0, 0.275, z, 0.235, 0.11, KM, verts=8, roll=22.5, bevel=0.008, tags=tags, r2=0.19)
    ycyl("b_motorring", 0, 0.225, z, 0.235, 0.02, S, verts=8, roll=22.5, bevel=0.004, tags=tags)
    # cubo do rotor (gira) e eixo central de aco (aparece nas frestas entre os canos)
    ycyl("b_hub", 0, 0.385, z, 0.215, 0.11, S, verts=6, roll=rot, bevel=0.01, tags=tags)
    ycyl("b_axle", 0, 0.88, z, 0.09, 0.96, S, verts=8, roll=rot, bevel=0.0, tags=tags)
    # 6 canos em volta do eixo (fase 0 = um cano no topo, grupo impar e centrado)
    Rc, rb = 0.14, 0.05
    y0, ym, yt = 0.44, L - 0.46, L - 0.095
    for i in range(6):
        a = math.radians(i * 60 + rot)
        bx, bz = Rc * math.sin(a), z + Rc * math.cos(a)
        ycyl(f"b_bar{i}", bx, (y0 + ym) / 2, bz, rb, ym - y0, A, verts=8, roll=rot, bevel=0.004, tags=tags)
        ycyl(f"b_barf{i}", bx, (ym + yt) / 2, bz, rb * 0.9, yt - ym, S, verts=8, roll=rot, bevel=0.004, tags=tags)
        # ponta escura (so ela aquece); nos quadros de giro vira brasa, para o calor ler laranja e nao dourado
        ycyl(f"b_tip{i}", bx, (yt + L - 0.012) / 2, bz, rb * 1.12, L - 0.012 - yt, M["ember"] if spinning else KM,
             verts=8, roll=rot, bevel=0.004, tags=hot)
    # abracadeira do meio: quebra escura
    ycyl("b_clamp_mid", 0, 0.80, z, 0.205, 0.06, KM, verts=6, roll=rot, bevel=0.008, tags=tags)
    ycyl("b_clamp_midr", 0, 0.835, z, 0.19, 0.012, S, verts=6, roll=rot, bevel=0.0, tags=tags)
    # abracadeira da frente: 3 aneis largos claros sobre um corpo escuro (2 fendas transversais) e aros
    # escuros nas faces
    yc = L - 0.29
    ycyl("b_clamp_f", 0, yc, z, 0.215, 0.10, K, verts=6, roll=rot, bevel=0.0, tags=tags)
    for i, d in enumerate((-0.036, 0.0, 0.036)):
        ycyl(f"b_clamp_fb{i}", 0, yc + d, z, 0.235, 0.022, A, verts=6, roll=rot, bevel=0.006, tags=tags)
    for i, d in enumerate((-0.0625, 0.0625)):
        ycyl(f"b_clamp_fr{i}", 0, yc + d, z, 0.20, 0.025, K, verts=6, roll=rot, bevel=0.0, tags=tags)
    # coroa da boca logo atras das pontas
    ycyl("b_crown", 0, yt - 0.02, z, 0.21, 0.035, KM, verts=6, roll=rot, bevel=0.006, tags=tags)


def roof(M, T="roof"):
    """Teto 2x3: placas verdes, anel da torre e faixa de carregadores na fileira de tras."""
    tags = (T,)
    w, h = PART["size"]
    green = B.mat_roof_green()
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    px, py = PART["pivot"][0] - w / 2, h / 2 - PART["pivot"][1]
    gap = 0.03
    B.box("deck_under", 0, 0, w, h, -0.05, 0.02, K, bevel=0.0, tags=tags)
    for tx in range(w):
        for ty in range(h):
            cx, cy = tx + 0.5 - w / 2, h / 2 - ty - 0.5
            poly = B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
            _, pnl = B.shard(f"deck{tx}_{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02,
                             tags=tags)
            if (tx + ty) % 2 == 0 and pnl is not None and ty < h - 1:
                B.cut(pnl, [B.rbox(f"dl{tx}{ty}", cx + 0.18, cy - 0.18, 0.012, 0.5, 0.07, 0.2, K, rot=45,
                                   bevel=0.0)])
    # anel da torre (sem pintura)
    B.torus("ringbear", px, py, 0.08, RING_R + 0.02, 0.05, KM, tags=tags)
    B.cyl("ringhole", px, py, 0.05, RING_R - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    B.bolts("rb", B.ring_points(px, py, RING_R + 0.09, 28), 0.1, 0.02, S, tags=tags)
    # faixa de carregadores (fileira de tras): bandeja escura com 6 pentes de 50 tiros
    hy = -h / 2 + 0.5
    tray = B.rpoly(0, hy - 0.04, 1.80, 0.56, 0, chamfer=0.10)
    t = B.plate("tray", tray, 0.04, 0.12, KM, slope=0.03, tags=tags)
    B.cut(t, [B.box("tray_cut", 0, hy - 0.04, 1.66, 0.42, 0.09, 0.3, K, bevel=0.0)])
    B.box("tray_bed", 0, hy - 0.04, 1.66, 0.42, 0.07, 0.095, M["black"], bevel=0.0, tags=tags)
    for i in range(6):
        x = -0.70 + i * 0.28
        my = hy - 0.06
        mg = B.box(f"rmag{i}", x, my, 0.22, 0.34, 0.09, 0.18, KM, bevel=0.015, slope=0.01, tags=tags)
        # contador: fenda escura com 2 pips no meio do pente
        Mo.slot_with_pips(f"rmc{i}", x, my - 0.11, my + 0.03, 0.05, 0.18, 2, M, tags, target=mg, depth=0.025)
        # trava clara fina na traseira e pontas dos cartuchos saindo na frente
        B.box(f"rmaglatch{i}", x, my - 0.15, 0.18, 0.035, 0.17, 0.19, M["armor_mid"], bevel=0.006, tags=tags)
        for k, (dx, dy) in enumerate(((-0.05, 0.12), (0.0, 0.135), (0.05, 0.12))):
            B.cyl(f"rround{i}{k}", x + dx, my + dy, 0.18, 0.02, 0.04, S, axis="Z", verts=10, bevel=0.005, tags=tags)
    # calha de alimentacao nervurada entre a faixa e o anel
    cy0, cy1 = hy + 0.24, py - RING_R - 0.03
    B.box("feed", 0, (cy0 + cy1) / 2, 0.14, cy1 - cy0, 0.05, 0.12, KM, bevel=0.012, slope=0.01, tags=tags)
    B.box("feedbed", 0, (cy0 + cy1) / 2, 0.07, cy1 - cy0 - 0.04, 0.12, 0.125, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"feedrib{i}", 0, cy0 + (i + 0.5) * (cy1 - cy0) / 3, 0.16, 0.025, 0.05, 0.135, S, bevel=0.004,
              tags=tags)


def floor(M, T="floor"):
    """Piso padrao (bancos, consoles, estantes de pentes) + canal de alimentacao da estante ate o anel."""
    tags = (T,)
    w, h = PART["size"]
    pv = PART["pivot"]
    from bsgen.common import crew_positions
    Mo.hull_floor(M, w, h, pv, RING_R, crew_positions(w, h, 2, pv), T)
    py = h / 2 - pv[1]
    y0, y1 = -h / 2 + 0.36, py - RING_R * 0.95 - 0.05
    B.box("fl_feed", 0, (y0 + y1) / 2, 0.16, y1 - y0, 0.0, 0.07, M["core_mid"], bevel=0.01, tags=tags)
    B.box("fl_feedbed", 0, (y0 + y1) / 2, 0.08, y1 - y0 - 0.04, 0.07, 0.075, M["black"], bevel=0.0, tags=tags)
    n = 4
    for i in range(n):
        y = y0 + (i + 0.5) * (y1 - y0) / n
        B.box(f"fl_feedrib{i}", 0, y, 0.18, 0.025, 0.0, 0.085, M["steel"], bevel=0.004, tags=tags)
