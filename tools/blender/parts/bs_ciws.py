"""CIWS de Conves ("Tamandua") - defesa de ponto 3x3, 2 tripulantes, familia do 76 mm.

Tamandua: focinho longo (grupo de 4 canos rotativos numa luva octogonal afunilada), cabeca/corcunda
formada por um radome facetado alto em octogono chanfrado (nivel de baixo partido em lascas por vaos
escuros, degrau escuro, nivel de cima com janela de sensor, perfil facetado do tamandua e fenda de pips),
flancos corcundas partidos em duas escamas e garras em foice (facetas retas, joelho na quina da caixa e
presa para a frente, com entalhe no dorso) que avancam ate a raiz do focinho.
Atras do radome fica a "cauda": antena plana de busca (hexagono em ponta de flecha) que gira 360 graus
em 8 quadros, com farol vermelho piscando. Tambores de carregador nos vaos, calhas ate a culatra,
baias de exaustao traseiras.
Cano: um sprite com o grupo de 4 canos (gira phase*90 graus), caixa do motor escura, luva octogonal
clara afunilada com duas janelas no topo (os canos aparecem girando la dentro), bloco da abracadeira
claro facetado com portas escuras, nariz em ponta de flecha e pontas escuras que aquecem.
"""

import math

import bpy

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_ciws",
    "kind": "gun",
    "size": [3, 3],
    "pivot": [1.5, 1.28],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 2.62,            # lado do quadrado do sprite da torre
    "ring_r": 1.18,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "collider": 1.15,
    "barrels": {
        "ys": [0.0],               # um sprite = o grupo de 4 canos
        "root": 0.62,              # pivo -> raiz (traseira da caixa do motor)
        "length": 1.85,            # raiz -> boca (focinho longo)
        "width": 0.42,
        "pad": 0.10,
        "anim": "spin",
        "spin_frames": 3,
        "spin_recoil": 0.02,       # o grupo treme para tras enquanto atira
        "heat": [0.25, 0.20, 0.15],  # pontas mornas durante o giro (arma leve: pouco calor)
        "interval": 0.05,
    },
    "turret_anim": {"frames": 8, "interval": 0.1},   # antena de busca girando + farol vermelho piscando
    "lights": [
        {"at": [0.0, -0.95], "size": 1.2, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "rotary",
}

RING_R = PART["ring_r"]
ZB = 0.55          # altura do eixo do grupo de canos
RY = -0.86         # centro de giro da antena de busca (y da cabeca)


# ============================================================================ utilidades
def ycyl(name, x, y, z, r, length, mat, verts=8, roll=0.0, bevel=0.01, tags=(), r2=None):
    """Cilindro no eixo Y com giro (roll, graus) em torno do proprio eixo; r atras, r2 na frente."""
    ob = B.cyl(name, x, y, z, r, length, mat, axis="Y", verts=verts, bevel=bevel, tags=tags, r2=r2)
    ob.rotation_euler = (math.radians(-90), math.radians(roll), 0.0)
    return ob


def lines(target, name, specs, ztop, mat, w=0.016):
    """Linhas de painel recortadas no alvo: specs = [(x, y, comprimento, rotacao)]."""
    if target is None:
        return
    cuts = [B.rbox(f"{name}{i}", x, y, w, ln, ztop - 0.03, ztop + 0.3, mat, rot=r, bevel=0.0)
            for i, (x, y, ln, r) in enumerate(specs)]
    B.cut(target, cuts)


def new_roots(before):
    """Objetos criados depois de 'before' que nao tem pai (cortadores ficam presos ao alvo)."""
    return [o for o in bpy.context.scene.objects if o not in before and o.parent is None]


def group(objs, loc, rot_deg):
    """Prende os objetos a um Empty em loc e gira o conjunto (graus XYZ) em torno desse ponto."""
    emp = bpy.data.objects.new("grp", None)
    bpy.context.scene.collection.objects.link(emp)
    emp.location = loc
    bpy.context.view_layer.update()
    for o in objs:
        o.parent = emp
        o.matrix_parent_inverse = emp.matrix_world.inverted()
    emp.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    bpy.context.view_layer.update()
    return emp


def radar(M, tags, phase):
    """Antena plana de busca ("cauda" do tamandua): pedestal fixo, garfo + painel inclinado que giram
    phase*360 graus em torno de (0, RY); farol vermelho atras do painel pisca (metade dos quadros)."""
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    # pedestal fixo (octogono escuro) com colar de aco
    B.cyl("rad_base", 0, RY, 0.50, 0.17, 0.40, KM, axis="Z", verts=8, bevel=0.01, tags=tags)
    B.cyl("rad_collar", 0, RY, 0.715, 0.15, 0.03, S, axis="Z", verts=8, bevel=0.005, tags=tags)
    before = set(bpy.context.scene.objects)
    # garfo giratorio e modulo traseiro (contrapeso) com o farol num rebaixo escuro
    B.box("rad_yoke", 0, RY, 0.22, 0.12, 0.72, 0.85, KM, bevel=0.012, tags=tags)
    for sx in (-1, 1):
        B.box(f"rad_arm{sx}", sx * 0.13, RY + 0.02, 0.04, 0.10, 0.76, 0.90, S, bevel=0.006, tags=tags)
    ym = RY + 0.16
    mod = B.rbox("rad_mod", 0, ym, 0.30, 0.13, 0.78, 0.90, KM, chamfer=0.03, slope=0.01, bevel=0.008, tags=tags)
    B.cut(mod, [B.box("rad_modc", 0, ym, 0.09, 0.075, 0.86, 1.2, K, bevel=0.0)])
    B.box("rad_modbed", 0, ym, 0.09, 0.075, 0.85, 0.862, M["black"], bevel=0.0, tags=tags)
    k = int(round(phase * 8)) % 8
    lit = k in (0, 1, 4, 5)
    red_off = B.mat_metal("red_off", (0.10, 0.012, 0.01), rough=0.35, metal=0.2)
    B.box("rad_beacon", 0, ym, 0.07, 0.05, 0.855, 0.874, M["red"] if lit else red_off, bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"rad_modfin{sx}", sx * 0.115, ym, 0.02, 0.10, 0.90, 0.915, S, bevel=0.0, tags=tags)
    # painel da antena (inclinado para tras e para cima): hexagono em ponta de flecha com bisel duplo,
    # moldura clara, face escura com grade de emissores e pip ambar numa ponta (sentido do giro)
    tb = set(bpy.context.scene.objects)
    zc = 0.93
    hexa = [(-0.38, RY), (-0.31, RY - 0.105), (0.31, RY - 0.105), (0.38, RY), (0.31, RY + 0.105),
            (-0.31, RY + 0.105)]
    pa, pp = B.shard("rad_panel", hexa, zc - 0.035, zc + 0.02, A, slope=0.016, groove=0.016, panel_h=0.012,
                     tags=tags)
    ztop = zc + 0.032
    for t in (pa, pp):
        if t is not None:
            B.cut(t, [B.box(f"rad_face{t.name}", 0, RY, 0.50, 0.10, zc, zc + 0.3, K, bevel=0.0)])
    B.box("rad_facebed", 0, RY, 0.50, 0.10, zc - 0.012, zc + 0.002, M["black"], bevel=0.0, tags=tags)
    for row, dy in enumerate((-0.024, 0.024)):
        for i in range(6):
            x = -0.20 + i * 0.08
            B.box(f"rad_el{row}{i}", x, RY + dy, 0.064, 0.038, zc - 0.004, zc + 0.026, KM, bevel=0.005,
                  tags=tags)
    B.box("rad_rib", 0, RY, 0.48, 0.008, zc - 0.004, zc + 0.016, S, bevel=0.0, tags=tags)
    # fendas nas duas pontas: a da direita tem pip ambar (mostra o sentido do giro)
    for sx in (-1, 1):
        for t in (pa, pp):
            if t is not None:
                B.cut(t, [B.box(f"rad_sl{sx}{t.name}", sx * 0.29, RY, 0.026, 0.07, ztop - 0.06, ztop + 0.3, K,
                                bevel=0.0)])
        B.box(f"rad_slbed{sx}", sx * 0.29, RY, 0.026, 0.07, ztop - 0.07, ztop - 0.058, M["black"], bevel=0.0,
              tags=tags)
        if sx > 0:
            B.box("rad_end", sx * 0.29, RY, 0.016, 0.05, ztop - 0.06, ztop - 0.048, M["glow"], bevel=0.0, tags=tags)
    # alimentador: braco de aco saindo da face com corneta escura na ponta
    B.box("rad_feedarm", 0, RY - 0.13, 0.03, 0.14, zc + 0.02, zc + 0.045, S, bevel=0.005, tags=tags)
    B.box("rad_horn", 0, RY - 0.205, 0.10, 0.045, zc + 0.005, zc + 0.06, KM, bevel=0.008, slope=0.008, tags=tags)
    tilt = group(new_roots(tb), (0, RY, zc), (24.0, 0.0, 0.0))
    group(new_roots(before) + [tilt], (0, RY, 0.0), (0.0, 0.0, phase * 360.0))


# ============================================================================ cabeca
def head(M, T="head", phase=0.0):
    """Cabeca: radome facetado no centro, flancos corcundas, garras em foice, antena atras."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    # anel giratorio (arco da frente recortado na boca do focinho) e nucleo escuro
    ring = B.cyl("ring", 0, 0, 0.04, RING_R + 0.02, 0.08, KM, axis="Z", verts=72, bevel=0.01, tags=tags)
    B.cut(ring, [B.box("ring_notch", 0, 1.10, 0.46, 0.44, 0.0, 0.3, K, bevel=0.0)])
    rbolts = [p for p in B.ring_points(0, 0, RING_R - 0.06, 24, 0.13) if not (abs(p[0]) < 0.26 and p[1] > 0)]
    B.bolts("ringbolt", rbolts, 0.09, 0.022, S, tags=tags)
    core = [(-0.62, -1.10), (0.62, -1.10), (1.02, -0.80), (1.10, -0.20), (1.00, 0.40), (0.50, 0.84),
            (-0.50, 0.84), (-1.00, 0.40), (-1.10, -0.20), (-1.02, -0.80)]
    B.plate("core", core, 0.06, 0.32, K, slope=0.05, tags=tags)

    # ---------------------------------------------------------------- flancos corcundas + garras em foice
    # flanco: ombreira com a quina da frente em ponta (para dentro/frente), partida por um vao inclinado
    flank = [(-0.80, -1.00), (-1.00, -1.00), (-1.16, -0.84), (-1.16, -0.58), (-1.26, -0.46), (-1.26, 0.02),
             (-0.80, 0.28)]
    fin = [(-0.88, -0.92), (-1.02, -0.92), (-1.09, -0.84), (-1.10, -0.58), (-0.88, -0.43)]
    # garra em foice: facetas retas, joelho na quina da caixa e presa apontando para a frente
    sick = [(-1.27, 0.06), (-1.27, 0.62), (-0.94, 1.06), (-0.52, 1.27), (-0.36, 1.27), (-0.34, 1.17),
            (-0.48, 1.02), (-0.66, 0.80), (-0.82, 0.54), (-0.88, 0.30)]
    # painel desenhado a mao (recuo ~0.09; a presa e fina demais para o painel automatico)
    sick_pnl = [(-1.18, 0.20), (-1.18, 0.59), (-0.885, 0.985), (-0.505, 1.18), (-0.45, 1.18), (-0.55, 1.05),
                (-0.725, 0.835), (-0.895, 0.56), (-0.955, 0.34)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        fa, fp = B.shard(f"flank_{side}", f(flank), 0.30, 0.72, A, slope=0.09, groove=0.04, panel_h=0.03,
                         tags=tags)
        # vao inclinado (paralelo a quina da frente): o flanco vira duas escamas
        gap = [B.rbox(f"fgap{side}{k}", sx * 1.03, -0.23, 0.05, 0.70, 0.2, 1.0, K, rot=sx * 60.5, bevel=0.0)
               for k in range(2)]
        B.cut(fa, gap[:1])
        B.cut(fp, gap[1:])
        B.rbox(f"fgapbed{side}", sx * 1.03, -0.23, 0.05, 0.50, 0.30, 0.33, K, rot=sx * 60.5, bevel=0.0, tags=tags)
        lines(fp, f"fpl{side}", [(sx * 1.03, -0.09, 0.16, sx * 60.5)], 0.75, K, w=0.022)
        ta, tp = B.shard(f"fin_{side}", f(fin), 0.73, 0.84, A, slope=0.05, groove=0.03, panel_h=0.02, tags=tags)
        Mo.slot_with_pips(f"fslot{side}", sx * 0.985, -0.80, -0.60, 0.055, 0.86, 3, M, tags, target=[ta, tp],
                          depth=0.04)
        ca = B.plate(f"sick_{side}", f(sick), 0.30, 0.64, A, slope=0.055, tags=tags)
        cp = B.plate(f"sick_{side}_pnl", f(sick_pnl), 0.636, 0.67, A, slope=0.012, bevel=0.0, tags=tags)
        # entalhe em gancho no dorso, perto da presa (parede da frente reta: a ponta vira garra dupla)
        notch = f([(-0.86, 1.22), (-0.665, 1.07), (-0.63, 1.32)])
        for t in (ca, cp):
            B.cut(t, [B.loft(f"snotch{side}{t.name}", notch, notch, 0.2, 1.0, K, bevel=0.0)])
        # fenda com luz paralela a faceta do joelho
        cx, cy, cr = sx * 0.969, 0.738, sx * 36.9
        for t in (ca, cp):
            B.cut(t, [B.rbox(f"scut{side}{t.name}", cx, cy, 0.05, 0.26, 0.58, 0.9, K, rot=cr, bevel=0.0)])
        B.rbox(f"sbed{side}", cx, cy, 0.05, 0.26, 0.56, 0.585, M["black"], rot=cr, bevel=0.0, tags=tags)
        B.rbox(f"sglow{side}", cx, cy, 0.016, 0.19, 0.585, 0.595, M["glow_dim"], rot=cr, bevel=0.0, tags=tags)
        # linha de painel atravessando a base da foice
        lines(cp, f"spl{side}", [(sx * 1.07, 0.36, 0.20, 90)], 0.67, K)
        # pistao hidraulico: foice -> mantelete
        B.cyl(f"piston{side}", sx * 0.51, 0.70, 0.44, 0.03, 0.40, S, axis="Y", verts=12, yaw=sx * 79, tags=tags)
        B.cyl(f"pistonb{side}", sx * 0.63, 0.678, 0.44, 0.045, 0.14, KM, axis="Y", verts=12, yaw=sx * 79,
              tags=tags)

    # ---------------------------------------------------------------- mantelete (de onde sai o focinho)
    mant = [(-0.24, 0.46), (0.24, 0.46), (0.30, 0.60), (0.26, 0.90), (-0.26, 0.90), (-0.30, 0.60)]
    m = B.plate("mantlet", mant, 0.30, 0.62, KM, slope=0.05, tags=tags)
    B.cut(m, [B.box("mant_cut", 0, 0.80, 0.36, 0.24, 0.54, 0.9, K, bevel=0.0)])

    # ---------------------------------------------------------------- tambores + calhas nos vaos
    for sx in (-1, 1):
        x = sx * 0.68
        B.cyl(f"drum{sx}", x, -0.30, 0.44, 0.10, 0.62, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
        for i, y in enumerate((-0.54, -0.30, -0.06)):
            B.cyl(f"drumring{sx}{i}", x, y, 0.44, 0.11, 0.035, S, axis="Y", verts=8, bevel=0.005, tags=tags)
        for i in range(3):
            B.box(f"drumled{sx}{i}", x, -0.47 + i * 0.065, 0.03, 0.03, 0.53, 0.55,
                  M["glow"] if i < 2 else M["black"], bevel=0.0, tags=tags)
        # calha do tambor ate a culatra
        yaw = sx * 32.0
        ux, uy = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        cx, cy = sx * 0.51, 0.32
        B.cyl(f"chute{sx}", cx, cy, 0.42, 0.045, 0.58, KM, axis="Y", verts=8, yaw=yaw, tags=tags)
        for i, t in enumerate((-0.16, 0.0, 0.16)):
            B.cyl(f"chuter{sx}{i}", cx + ux * t, cy + uy * t, 0.42, 0.053, 0.022, S, axis="Y", verts=8, yaw=yaw,
                  tags=tags)

    # ---------------------------------------------------------------- radome facetado (corcunda)
    R1 = [(-0.32, -0.66), (0.32, -0.66), (0.58, -0.40), (0.58, 0.10), (0.24, 0.58), (-0.24, 0.58),
          (-0.58, 0.10), (-0.58, -0.40)]
    R2 = B.offset_poly(R1, 0.23)    # mesma ordem de vertices (R1 ja e anti-horario)
    d1 = B.plate("dome1", R1, 0.30, 0.78, A, slope=0.20, tags=tags)
    # vaos escuros nas 4 juntas lado/chanfro: o nivel de baixo vira proa em chevron, 2 lascas laterais
    # e lasca traseira; cada vao vai da quina de R1 ate a quina do nivel de cima
    cuts = []
    for i in (2, 3, 6, 7):
        (x0, y0), (x1, y1) = R1[i], R2[i]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln
        gx, gy, rot = x0 + ux * 0.125, y0 + uy * 0.125, math.degrees(math.atan2(-ux, uy))
        cuts.append(B.rbox(f"dgap{i}", gx, gy, 0.05, 0.35, 0.31, 1.0, K, rot=rot, bevel=0.0))
        B.rbox(f"dgapbed{i}", gx, gy, 0.05, 0.35, 0.31, 0.33, M["black"], rot=rot, bevel=0.0, tags=tags)
    # uma linha de painel por lasca lateral, paralela a aresta da base (sem cruzamentos)
    cuts += [B.rbox(f"dline{sx}", sx * 0.49, -0.15, 0.02, 0.26, 0.40, 1.0, K, bevel=0.0) for sx in (-1, 1)]
    B.cut(d1, cuts)
    # degrau escuro entre os niveis (separa bem o nivel de cima)
    B.plate("dome_step", B.offset_poly(R1, 0.20), 0.775, 0.825, KM, slope=0.012, bevel=0.006, tags=tags)
    d2a, d2p = B.shard("dome2", R2, 0.82, 1.08, A, slope=0.11, groove=0.035, panel_h=0.03, tags=tags)
    ztop = 1.11
    # janela do sensor de tiro (rebaixo escuro com fenda acesa) na proa do topo
    win = [(-0.11, 0.0), (0.11, 0.0), (0.11, 0.06), (0.045, 0.15), (-0.045, 0.15), (-0.11, 0.06)]
    for t in (d2a, d2p):
        if t is not None:
            B.cut(t, [B.loft(f"win_cut{t.name}", win, win, ztop - 0.07, ztop + 0.3, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, ztop - 0.075, ztop - 0.065, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, 0.05, 0.15, 0.028, ztop - 0.07, ztop - 0.058, M["lens"], bevel=0.0, tags=tags)
    # emblema: perfil facetado do tamandua (focinho longo e fino, corcunda, cauda em vassoura caida),
    # incrustacao cinza escura rebaixada no topo do radome
    ant = [(0.150, -0.004), (0.060, 0.016), (0.035, 0.030), (0.010, 0.046), (-0.020, 0.054), (-0.075, 0.040),
           (-0.120, 0.034), (-0.170, 0.022), (-0.190, -0.008), (-0.170, -0.046), (-0.120, -0.040),
           (-0.092, -0.026), (-0.090, -0.056), (-0.064, -0.056), (-0.058, -0.026), (-0.004, -0.026),
           (0.000, -0.056), (0.030, -0.058), (0.030, -0.020), (0.060, -0.006), (0.150, -0.014)]
    ant = [(x * 0.85 + 0.017, y * 0.85 - 0.106) for x, y in ant]
    for t in (d2a, d2p):
        if t is not None:
            B.cut(t, [B.loft(f"ant_cut{t.name}", ant, ant, ztop - 0.07, ztop + 0.3, K, bevel=0.0)])
    B.loft("ant_inlay", ant, ant, ztop - 0.08, ztop - 0.02, AM, bevel=0.0, tags=tags)
    # fenda de pips atras do emblema (eco da espinha do 76 mm)
    Mo.slot_with_pips("dslot", -0.222, -0.10, 0.10, 0.045, ztop, 3, M, tags, target=[d2a, d2p], depth=0.075,
                      vertical=False)

    # ---------------------------------------------------------------- baias de exaustao traseiras
    for sx in (-1, 1):
        x = sx * 0.48
        B.box(f"vent_bay{sx}", x, -0.93, 0.30, 0.24, 0.24, 0.36, M["black"], bevel=0.0, tags=tags)
        for i in range(5):
            B.box(f"louver{sx}{i}", x, -1.02 + i * 0.045, 0.28, 0.018, 0.30, 0.37, KM, bevel=0.003, tags=tags)
        for i in range(4):
            B.box(f"vent_pip{sx}{i}", x + (i - 1.5) * 0.068, -0.785, 0.04, 0.022, 0.34, 0.38, M["glow"],
                  bevel=0.0, tags=tags)
    B.bolts("bolt", [(x, -0.96) for x in (-0.70, 0.70)], 0.33, 0.024, S, tags=tags)

    # ---------------------------------------------------------------- antena de busca (anima)
    radar(M, tags, phase)


# ============================================================================ cano (grupo de 4)
def barrel(M, L=1.85, T="barrel", phase=0.0):
    """Focinho: grupo de 4 canos numa luva octogonal; raiz (y=0), boca (y=L). phase gira o grupo phase*90."""
    tags = (T,)
    hot = (T, "hot")
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = ZB
    rot = phase * 90.0
    # caixa do motor (fixa): octogono escuro com 2 canais no topo
    hb = ycyl("b_motor", 0, 0.13, z, 0.195, 0.26, KM, verts=8, roll=22.5, bevel=0.012, tags=tags)
    B.cut(hb, [B.box(f"b_ch{sx}", sx * 0.065, 0.14, 0.03, 0.18, z + 0.145, z + 0.4, K, bevel=0.0)
               for sx in (-1, 1)])
    ycyl("b_motorcap", 0, 0.015, z, 0.17, 0.03, S, verts=8, roll=22.5, bevel=0.005, tags=tags)
    ycyl("b_motorring", 0, 0.24, z, 0.20, 0.025, S, verts=8, roll=22.5, bevel=0.004, tags=tags)
    # cubo do rotor (gira)
    ycyl("b_hub", 0, 0.30, z, 0.17, 0.09, S, verts=8, roll=rot + 22.5, bevel=0.008, tags=tags)
    # trechos ao longo do focinho
    y0s, y1s = 0.34, L - 0.56         # luva
    yb0, yb1 = L - 0.40, L - 0.24     # bloco da abracadeira da frente
    yn1 = L - 0.13                    # fim do nariz
    yc1 = L - 0.10                    # fim da coroa
    yt0 = L - 0.15                    # inicio das pontas
    # 4 canos em volta do eixo: correm dentro da luva ate o bloco da frente; as pontas saem da coroa
    Rc, rb = 0.07, 0.034
    yb_end = yb0 + 0.03
    for i in range(4):
        a = math.radians(i * 90 + rot)
        bx, bz = Rc * math.sin(a), z + Rc * math.cos(a)
        ycyl(f"b_bar{i}", bx, (y0s + yb_end) / 2, bz, rb, yb_end - y0s, S, verts=8, roll=rot, bevel=0.004,
             tags=tags)
        # ponta escura (so ela aquece)
        ycyl(f"b_tip{i}", bx, (yt0 + L - 0.012) / 2, bz, rb * 1.12, L - 0.012 - yt0, KM, verts=8, roll=rot,
             bevel=0.004, tags=hot)
    ycyl("b_axle", 0, (y0s + yb_end) / 2, z, 0.035, yb_end - y0s, KM, verts=8, roll=rot, bevel=0.0, tags=tags)
    # luva octogonal (fixa) afunilada como focinho de tamandua, com 2 janelas no topo (canos girando dentro)
    sh = ycyl("b_shroud", 0, (y0s + y1s) / 2, z, 0.17, y1s - y0s, A, verts=8, roll=22.5, bevel=0.008, tags=tags,
              r2=0.12)
    yw = (y0s + y1s) / 2 + 0.07     # colar do meio separa as duas janelas
    wins = [(y0s + 0.12, yw - 0.05), (yw + 0.05, y1s - 0.08)]
    B.cut(sh, [B.box(f"b_win{i}", 0, (u + v) / 2, 0.12, v - u, z + 0.03, z + 0.4, K, bevel=0.0)
               for i, (u, v) in enumerate(wins)])
    for i, (u, v) in enumerate(wins):
        B.box(f"b_winbed{i}", 0, (u + v) / 2, 0.12, v - u, z + 0.02, z + 0.03, M["black"], bevel=0.0, tags=tags)
    rs = lambda y: 0.17 + (0.12 - 0.17) * (y - y0s) / (y1s - y0s)  # noqa: E731  raio da luva em y
    for i, y in enumerate((y0s + 0.06, yw)):
        ycyl(f"b_collar{i}", 0, y, z, rs(y) + 0.013, 0.05, AM, verts=8, roll=22.5, bevel=0.006, tags=tags)
    ycyl("b_lip", 0, y1s - 0.01, z, 0.128, 0.03, KM, verts=8, roll=22.5, bevel=0.004, tags=tags)
    # abracadeira do meio (gira) no trecho exposto
    ym = (y1s + yb0) / 2
    ycyl("b_clamp_mid", 0, ym, z, 0.112, 0.04, KM, verts=8, roll=rot + 22.5, bevel=0.006, tags=tags)
    ycyl("b_clamp_midr", 0, ym, z, 0.118, 0.012, S, verts=8, roll=rot + 22.5, bevel=0.0, tags=tags)
    # bloco da abracadeira da frente (fixo, portas sempre limpas): claro, facetado, 2 portas escuras
    # transversais no topo
    yc = (yb0 + yb1) / 2
    blk = ycyl("b_clamp", 0, yc, z, 0.135, yb1 - yb0, A, verts=8, roll=22.5, bevel=0.008, tags=tags)
    B.cut(blk, [B.box(f"b_port{i}", 0, yc + d, 0.18, 0.035, z + 0.06, z + 0.4, K, bevel=0.0)
                for i, d in enumerate((-0.035, 0.035))])
    B.box("b_clamp_core", 0, yc, 0.18, yb1 - yb0 - 0.03, z - 0.06, z + 0.07, K, bevel=0.0, tags=tags)
    # nariz em ponta de flecha (fixo) ate a coroa quente (gira com o grupo)
    ycyl("b_nose", 0, (yb1 + yn1) / 2, z, 0.135, yn1 - yb1, A, verts=8, roll=22.5, bevel=0.006, tags=tags,
         r2=0.095)
    ycyl("b_crown", 0, (yn1 + yc1) / 2, z, 0.095, yc1 - yn1, KM, verts=8, roll=rot + 22.5, bevel=0.004, tags=hot,
         r2=0.085)


# ============================================================================ teto
def roof(M, T="roof"):
    """Teto 3x3: placas verdes, anel da torre, respiros nos cantos de tras e escotilha baixa no meio."""
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
    B.torus("ringbear", px, py, 0.08, RING_R + 0.02, 0.055, KM, tags=tags)
    B.cyl("ringhole", px, py, 0.05, RING_R - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(px, py, RING_R + 0.11, 32) if abs(x) < w / 2 - 0.06 and abs(y) < h / 2 - 0.06]
    B.bolts("rb", pts, 0.1, 0.022, S, tags=tags)
    # fileira de tras: respiros com luz nos cantos e escotilha baixa e larga no meio (abaixo do anel)
    hy = -h / 2 + 0.5
    for k, cx in enumerate((-1.0, 1.0)):
        v = B.box(f"hvent{k}", cx, hy, 0.56, 0.34, 0.05, 0.11, KM, bevel=0.01, slope=0.015, tags=tags)
        B.cut(v, [B.box(f"hvc{k}{i}", cx, hy - 0.11 + i * 0.075, 0.46, 0.03, 0.09, 0.2, K, bevel=0.0)
                  for i in range(4)])
        # luz abaixo do respiro (fica visivel: a cabeca cobre ate y ~ -0.78)
        B.box(f"hled{k}", cx, hy - 0.23, 0.14, 0.03, 0.06, 0.09, M["glow_dim"], bevel=0.0, tags=tags)
    # escotilha octogonal com bisel duplo
    hyh = -1.24
    hatch = B.rpoly(0, hyh, 0.62, 0.30, 0, chamfer=0.10)
    B.shard("hatch", hatch, 0.06, 0.10, M["armor_mid"], slope=0.02, groove=0.025, panel_h=0.015, tags=tags)
    B.box("hatch_h", 0, hyh - 0.055, 0.22, 0.04, 0.11, 0.135, S, bevel=0.008, tags=tags)
    B.bolts("hb", [(sx * 0.20, hyh + 0.07) for sx in (-1, 1)], 0.12, 0.016, S, tags=tags)
