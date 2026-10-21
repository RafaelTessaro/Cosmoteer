"""Canhao PEM Leve de Proa ("Tuvira", 40 mm) - peixe-eletrico-faca dos rios, familia do 76 mm + assinatura PEM.

Peca 1x2 de PROA FIXA: a arma nao e uma torre que gira 360 graus, e um cardan (gimbal) baixo que mira so 30 graus
(FiringArc 30d). Por isso o teto mostra a montagem fixa: o poco do cardan no tile da frente, calcos de proa nos
cantos e, no tile de tras, a TREMONHA de celulas PEM (caixa blindada sem pintura com janela mostrando 3 celulas
PEM deitadas, contador azul e calha de alimentacao ate o cardan).
Cabeca (o cardan, gira +-15 graus): corpo em lamina de faca alongado (o peixe-faca visto de cima): duas bochechas
claras de bisel duplo que afinam em ponta para a frente ao lado dos canos, munhoes de aco nas laterais (o cardan),
recesso da culatra entre as raizes dos canos com o CAPACITOR azul aceso (cilindro deitado preso por cintas de aco),
espinha curta com janela do sensor (lente azul) e baia de exaustao traseira com 3 pips azuis.
Canos gemeos curtos (disparo sincronizado): culatra escura, BOBINA de fio de cobre (espiras redondas sobre nucleo
escuro, a assinatura da familia PEM), colar de aco, luva clara curta com canal e boca emissora facetada com fendas
escuras. Depois do tiro as espiras brilham em azul (heat_color azul, fraco).

Este arquivo tambem guarda o KIT DA FAMILIA PEM (pem(), turn(), coil(), cell()), importado por bs_pem_medium.py e
bs_pem_heavy.py: brilhos azuis em intensidade BAIXA (Mo.mats("blue") estoura, STYLE.md 9), cobre = Mo.copper_mat()
(o mesmo das bobinas do Carregador P.E.M. e do Poraque), corpo azul-marinho das celulas = o de parts/bs_mag_emp.py.
"""

import math

import bpy

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_pem_light",
    "kind": "gun",
    "size": [1, 2],
    "pivot": [0.5, 0.55],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 1.0,             # lado do quadrado do sprite da cabeca (cardan: +-0.47)
    "ring_r": 0.40,                # raio do poco do cardan no teto/piso
    "accent": "blue",
    "collider": 0.45,
    "crew": 1,                     # SPEC_2.0 pem_weapons[Tuvira].crew (o spec 1.x nao tem a peca)
    "barrels": {
        "ys": [-0.15, 0.15],       # canos gemeos sincronizados (sprites de 0.26 sem sobrepor)
        "root": 0.22,              # pivo -> raiz do cano (a culatra fica no berco escuro do cardan)
        "length": 0.84,            # raiz -> boca (cano curto de 40 mm)
        "width": 0.26,             # largura do sprite de cada cano (cabe a boca emissora)
        "pad": 0.08,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.06, 0.035, 0.012],          # 3 quadros de recuo + repouso (spec de arte)
        "heat": [0.62, 0.38, 0.16],              # espiras azuis depois do tiro (fraco)
        "heat_color": (0.05, 0.35, 1.0),         # azul PEM (spec de arte: Tuvira heat_color)
        "interval": 0.06,
    },
    "lights": [                    # luzes dinamicas (coordenadas da cabeca): o capacitor azul
        {"at": [0.0, 0.06], "size": 0.55, "color": [60, 150, 255], "z": 0.8},
    ],
    "preview_pattern": "volley",   # fire_pattern synchronized_2: os dois canos juntos
    "preview_fx": "plasma",        # previa automatica: clarao azul sem fumaca (o clarao real e das regras)
}

YS = PART["barrels"]["ys"]
ZB = 0.40                          # altura do eixo dos canos

# ============================================================================ kit da familia PEM
PEM_BLUE = (0.06, 0.50, 1.0)       # azul eletrico da familia (entre o ciano das granadas e o azul do carregador)
NAVY = (0.055, 0.095, 0.21)        # casca azul-marinho das celulas (= parts/bs_mag_emp.py NAVY)


def pem(M):
    """Materiais da familia PEM e troca, em M, dos brilhos padrao (azul a 9/3 estoura em branco/ciano na vista
    Standard) por azuis fracos: M["glow"], M["glow_dim"], M["lens"] e M["ember"] passam a ser os da familia, entao
    as funcoes do kit (Mo.slot_with_pips, Mo.hull_roof/hull_floor) acendem em azul sem estourar."""
    X = {
        "copper": Mo.copper_mat(),
        # mesmos nomes e valores de parts/bs_mag_emp.py (o cache do bs3d e por nome)
        "navy": B.mat_paint("emp_navy", NAVY, rough=0.40, metal=0.35, wear=0.0, grime=0.03, scale=5),
        "cell": B.mat_glow("emp_cell", (0.15, 0.38, 1.0), 0.8),
        "silver": B.mat_metal("silver", (0.80, 0.82, 0.86), rough=0.16, metal=1.0),
        "glow": B.mat_glow("pem_led", PEM_BLUE, 1.5),
        "glow_dim": B.mat_glow("pem_led_dim", PEM_BLUE, 0.6),
        "cap": B.mat_glow("pem_cap", (0.10, 0.46, 1.0), 0.9),        # capacitores / celulas acesas
        "gap": B.mat_glow("pem_gap", (0.05, 0.36, 1.0), 0.32),       # brilho fraco entre as espiras (repouso)
        "lens": B.mat_glow("pem_lens", (0.40, 0.78, 1.0), 1.3),
    }
    M["glow"], M["glow_dim"], M["lens"], M["ember"] = X["glow"], X["glow_dim"], X["lens"], X["gap"]
    return X


def turn(name, x, y, z, R, r, mat, tags, seg=20):
    """Uma espira de fio (toro) em volta de um eixo paralelo a Y: vista de cima e uma faixa com brilho de fio
    redondo (le como bobina, nao como anel liso)."""
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg, minor_segments=8,
                                     location=(x, y, z), rotation=(math.pi / 2, 0, 0))
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    for t in tags:
        ob[t] = True
    return ob


def coil_layout(y0, y1, wire, spacing=2.05):
    """Centros (y) das espiras de uma bobina de y0 a y1: passo ~ spacing x diametro do fio (2.05 = espiras
    encostadas; maior = frestas entre as espiras mostrando o nucleo)."""
    n = max(2, int(round((y1 - y0) / (spacing * wire))))
    step = (y1 - y0) / n
    return [y0 + (i + 0.5) * step for i in range(n)]


def coil(name, y0, y1, z, R, M, X, tags, wire=None, x=0.0, gap_mat=None, core_r=None, spacing=2.05, turn_tags=None):
    """Bobina de fio de cobre em volta de um eixo paralelo a Y (de y0 a y1): espiras redondas sobre um nucleo escuro
    (ou aceso, gap_mat: as bobinas brilhantes da PEM pesada; com spacing > 2.05 o nucleo aparece entre as espiras).
    R = raio externo da bobina. turn_tags: etiquetas so das espiras (padrao = tags)."""
    wire = wire or max(0.010, R * 0.13)
    ys = coil_layout(y0, y1, wire, spacing)
    B.cyl(f"{name}_core", x, (y0 + y1) / 2, z, core_r or (R - wire * 1.6), y1 - y0, gap_mat or M["core"], axis="Y",
          verts=12, bevel=0.0, tags=tags)
    for i, y in enumerate(ys):
        turn(f"{name}_t{i}", x, y, z, R - wire, wire, X["copper"], turn_tags or tags)
    return len(ys)


def cell(name, x, y, z, r, L, M, X, tags, axis="X", lit=True):
    """Celula PEM deitada (eixo X ou Y): casca azul-marinho, 2 bobinas de cobre, tampas de aco e uma janela acesa
    azul no meio (a celula que a tremonha e os tambores mostram)."""
    S = M["steel"]
    ax = axis
    off = (lambda d: (x + d, y)) if ax == "X" else (lambda d: (x, y + d))
    B.cyl(f"{name}_body", x, y, z, r, L * 0.86, X["navy"], axis=ax, verts=10, bevel=0.004, tags=tags)
    for k, d in enumerate((-L * 0.47, L * 0.47)):
        cx, cy = off(d)
        B.cyl(f"{name}_cap{k}", cx, cy, z, r * 0.92, L * 0.07, S, axis=ax, verts=10, bevel=0.003, tags=tags)
    for k, d in enumerate((-L * 0.25, L * 0.25)):
        cx, cy = off(d)
        B.cyl(f"{name}_cu{k}", cx, cy, z, r * 1.06, L * 0.08, X["copper"], axis=ax, verts=10, bevel=0.0, tags=tags)
    if lit:
        B.cyl(f"{name}_win", x, y, z, r * 1.02, L * 0.11, X["cell"], axis=ax, verts=10, bevel=0.0, tags=tags)


def stroke(name, p, q, w, z0, z1, mat, tags):
    """Traco fino (caixa girada) de p ate q; pontas estendidas w/2 para emendar com o proximo."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    rot = math.degrees(math.atan2(-dx, dy))
    return B.rbox(name, (p[0] + q[0]) / 2, (p[1] + q[1]) / 2, w, math.hypot(dx, dy) + w, z0, z1, mat, rot=rot,
                  bevel=0.0, tags=tags)


def rslot(name, cx, cy, w, ln, rot, ztop, depth, n, targets, M, tags, pip_mat=None):
    """Fenda escura GIRADA (rot em graus; ln ao longo do eixo girado) recortada nos alvos, com leito preto e n pips
    acesos no fundo (Mo.slot_with_pips so faz fendas alinhadas aos eixos; nas placas em crescente a fenda segue a
    curva). Use depth >= panel_h + 0.04 (STYLE.md 9)."""
    for t in targets:
        if t is not None:
            B.cut(t, [B.rbox(f"{name}_c{t.name}", cx, cy, w, ln, ztop - depth, ztop + 0.3, M["core"], rot=rot,
                             bevel=0.0)])
    B.rbox(f"{name}_bed", cx, cy, w, ln, ztop - depth - 0.01, ztop - depth + 0.004, M["black"], rot=rot, bevel=0.0,
           tags=tags)
    a = math.radians(rot)
    ux, uy = -math.sin(a), math.cos(a)
    for i in range(n):
        s = ((i + 0.5) / n - 0.5) * ln
        B.rbox(f"{name}_pip{i}", cx + ux * s, cy + uy * s, w * 0.55, ln / n * 0.55, ztop - depth,
               ztop - depth + 0.012, pip_mat or M["glow"], rot=rot, bevel=0.0, tags=tags)


def side(poly, sx):
    """Poligono desenhado do lado esquerdo (x < 0) -> lado sx."""
    return poly if sx < 0 else Mo.mirror(poly)


# ============================================================================ cabeca (cardan)
CORE = [(-0.20, -0.44), (0.20, -0.44), (0.35, -0.30), (0.38, 0.12), (0.30, 0.34), (-0.30, 0.34), (-0.38, 0.12),
        (-0.35, -0.30)]
# bochecha esquerda: lamina de faca que corre pela lateral e afina em ponta ao lado do cano (fora do sprite dele)
CHEEK = [(-0.22, -0.42), (-0.33, -0.33), (-0.44, -0.06), (-0.445, 0.14), (-0.40, 0.33), (-0.31, 0.468),
         (-0.285, 0.43), (-0.29, 0.20), (-0.27, 0.02), (-0.20, -0.20)]
CHEEK_Z = (0.24, 0.50)


def head(M, T="head", phase=0.0):
    """Cardan da proa: corpo em lamina de faca, bochechas claras, capacitor azul no recesso da culatra."""
    tags = (T,)
    X = pem(M)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]

    # base do cardan (disco escuro) e corpo escuro
    B.cyl("gimbal", 0, 0, 0.04, 0.40, 0.08, KM, axis="Z", verts=48, bevel=0.01, tags=tags)
    B.bolts("gbolt", [(x, y) for x, y in B.ring_points(0, 0, 0.37, 16, math.pi / 16) if y < -0.05], 0.09, 0.014,
            S, tags=tags)
    B.plate("core", CORE, 0.06, 0.26, K, slope=0.035, tags=tags)

    # berco escuro dos canos (o cano recua por cima dele; nada claro sob a raiz)
    for i, y in enumerate(YS):
        B.box(f"cradle{i}", y, 0.31, 0.15, 0.30, 0.20, 0.34, KM, bevel=0.01, tags=tags)
        B.cyl(f"cradring{i}", y, 0.44, ZB, 0.066, 0.03, S, axis="Y", verts=8, bevel=0.004, tags=tags)
    B.box("cradle_mid", 0, 0.32, 0.05, 0.26, 0.24, 0.36, S, bevel=0.008, tags=tags)

    # recesso da culatra com o capacitor azul: cilindro deitado fino, 4 cintas de aco por cima (3 trechos acesos
    # pequenos) e tampas de cobre nas pontas
    B.box("cap_bay", 0, 0.085, 0.40, 0.15, 0.20, 0.27, M["black"], bevel=0.0, tags=tags)
    B.cyl("capacitor", 0, 0.085, 0.262, 0.027, 0.32, X["cap"], axis="X", verts=12, bevel=0.0, tags=tags)
    for k, x in enumerate((-0.135, -0.045, 0.045, 0.135)):
        B.box(f"cap_strap{k}", x, 0.085, 0.036, 0.11, 0.25, 0.31, S, bevel=0.004, tags=tags)
    for sx in (-1, 1):
        B.cyl(f"cap_end{sx}", sx * 0.185, 0.085, 0.262, 0.046, 0.04, X["copper"], axis="X", verts=12, bevel=0.0,
              tags=tags)

    # bochechas (laminas de faca) com fenda de pips azuis e munhao do cardan
    z0, z1 = CHEEK_Z
    for sx in (-1, 1):
        ca, cp = B.shard(f"cheek{sx}", side(CHEEK, sx), z0, z1, A, slope=0.035, groove=0.018, panel_h=0.025,
                         tags=tags)
        Mo.slot_with_pips(f"cslot{sx}", sx * 0.375, -0.12, 0.06, 0.030, z1 + 0.025, 2, M, tags, target=[ca, cp],
                          depth=0.075)
        # linha de painel diagonal na ponta da bochecha
        if cp is not None:
            B.cut(cp, [B.rbox(f"cpl{sx}", sx * 0.36, 0.30, 0.014, 0.12, z1 - 0.02, 0.9, K, rot=sx * 24, bevel=0.0)])
        # munhao (pino do cardan) saindo da lateral
        B.cyl(f"trun{sx}", sx * 0.43, -0.20, 0.30, 0.045, 0.06, S, axis="X", verts=10, bevel=0.005, tags=tags)
        B.cyl(f"trunc{sx}", sx * 0.405, -0.20, 0.30, 0.058, 0.02, KM, axis="X", verts=10, bevel=0.003, tags=tags)

    # espinha curta em ponta de flecha com fenda do sensor (lente azul) e linha de painel
    spine = [(-0.10, -0.29), (0.10, -0.29), (0.14, -0.23), (0.14, -0.09), (0.035, 0.03), (-0.035, 0.03),
             (-0.14, -0.09), (-0.14, -0.23)]
    sa, sp = B.shard("spine", spine, 0.24, 0.47, A, slope=0.04, groove=0.016, panel_h=0.022, tags=tags)
    win = B.rpoly(0, -0.115, 0.13, 0.034, 0)
    for t in (sa, sp):
        if t is not None:
            B.cut(t, [B.loft(f"win_cut{t.name}", win, win, 0.43, 0.9, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 0.425, 0.435, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, -0.115, 0.07, 0.010, 0.43, 0.437, X["lens"], bevel=0.0, tags=tags)
    if sp is not None:
        B.cut(sp, [B.box("spl", 0, -0.215, 0.16, 0.014, 0.47, 0.9, K, bevel=0.0),
                   B.rbox("spd0", -0.06, -0.03, 0.012, 0.10, 0.47, 0.9, K, rot=-42, bevel=0.0),
                   B.rbox("spd1", 0.06, -0.03, 0.012, 0.10, 0.47, 0.9, K, rot=42, bevel=0.0)])

    # baia de exaustao traseira (persianas + 3 pips azuis), atras da espinha
    B.box("vent_bay", 0, -0.37, 0.28, 0.10, 0.20, 0.30, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"louver{i}", 0, -0.405 + i * 0.028, 0.26, 0.012, 0.26, 0.31, KM, bevel=0.003, tags=tags)
    for i, x in enumerate((-0.075, 0.0, 0.075)):
        B.box(f"vent_pip{i}", x, -0.335, 0.03, 0.012, 0.29, 0.32, X["glow_dim"], bevel=0.0, tags=tags)
    # cabos de alimentacao (do capacitor para as bobinas) nos vaos entre espinha e bochechas
    for sx in (-1, 1):
        B.cyl(f"cable{sx}", sx * 0.215, -0.10, 0.29, 0.022, 0.30, KM, axis="Y", verts=8, yaw=sx * -10, tags=tags)
        for j in range(3):
            B.cyl(f"cabler{sx}{j}", sx * (0.215 + 0.017 * (j - 1) * 0.6), -0.20 + j * 0.10, 0.29, 0.027, 0.014,
                  X["copper"], axis="Y", verts=8, yaw=sx * -10, tags=tags)


# ============================================================================ cano
def barrel(M, L=0.84, T="barrel", phase=0.0):
    """Cano curto de 40 mm envolto em bobina de cobre: raiz em y=0, boca em y=L, centrado em x=0."""
    tags = (T,)
    hot = (T, "hot")                  # as espiras e o colar da boca brilham em azul depois do tiro
    X = pem(M)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = ZB
    # culatra escura (dentro do berco do cardan)
    B.cyl("b_root", 0, 0.07, z, 0.068, 0.12, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
    B.cyl("b_rootring", 0, 0.135, z, 0.07, 0.022, S, axis="Y", verts=8, bevel=0.004, tags=tags)
    # luva clara curta com canal escuro (saindo do berco)
    y0, y1 = 0.145, 0.31
    sl = B.cyl("b_sleeve", 0, (y0 + y1) / 2, z, 0.064, y1 - y0, A, axis="Y", verts=8, bevel=0.006, tags=tags,
               r2=0.060)
    B.cut(sl, [B.box("b_chc", 0, (y0 + y1) / 2, 0.018, y1 - y0 - 0.04, z + 0.024, z + 0.2, K, bevel=0.0)])
    B.box("b_chbed", 0, (y0 + y1) / 2, 0.018, y1 - y0 - 0.04, z + 0.018, z + 0.028, M["black"], bevel=0.0,
          tags=tags)
    # bobina de fio de cobre (assinatura PEM), na frente: o calor azul do tiro sobe por ela ate a boca
    c0, c1 = 0.325, L - 0.19
    coil("b_coil", c0, c1, z, 0.088, M, X, hot, wire=0.0115)
    for i, y in enumerate((c0 - 0.006, (c0 + c1) / 2, c1 + 0.006)):
        B.cyl(f"b_cband{i}", 0, y, z, 0.092, 0.018, KM if i == 1 else S, axis="Y", verts=8, bevel=0.003,
              tags=hot if i == 2 else tags)
    # boca emissora facetada em ponta de flecha com fendas escuras e anel de contato de cobre no fundo
    yb = L - 0.085
    muz = [(-0.07, yb - 0.085), (0.07, yb - 0.085), (0.098, yb - 0.05), (0.098, yb + 0.03), (0.04, yb + 0.085),
           (-0.04, yb + 0.085), (-0.098, yb + 0.03), (-0.098, yb - 0.05)]
    mz = B.plate("b_muzzle", muz, z - 0.07, z + 0.07, A, slope=0.018, tags=tags)
    cuts = [B.box(f"b_mc{i}", 0, yb - 0.045 + i * 0.05, 0.24, 0.022, z + 0.012, z + 0.2, K, bevel=0.0)
            for i in range(2)]
    cuts.append(B.box("b_bore_c", 0, L, 0.034, 0.06, z - 0.035, z + 0.2, K, bevel=0.0))
    B.cut(mz, cuts)
    B.box("b_mcore", 0, yb - 0.02, 0.16, 0.12, z - 0.05, z + 0.016, X["copper"], bevel=0.0, tags=hot)


# ============================================================================ casco (montagem fixa de proa)
def roof(M, T="roof"):
    """Teto 1x2: poco do cardan no tile da frente, calcos de proa, tremonha de celulas PEM no tile de tras."""
    tags = (T,)
    X = pem(M)
    w, h = PART["size"]
    green = B.mat_roof_green()
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    px, py = PART["pivot"][0] - w / 2, h / 2 - PART["pivot"][1]
    rr = PART["ring_r"]
    gap = 0.03
    B.box("deck_under", 0, 0, w, h, -0.05, 0.02, K, bevel=0.0, tags=tags)
    for ty in range(h):
        cy = h / 2 - ty - 0.5
        poly = B.rpoly(0, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
        B.shard(f"deck{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02, tags=tags)
    # poco do cardan (colar escuro, sem pintura) com parafusos
    B.torus("ringbear", px, py, 0.08, rr + 0.02, 0.045, KM, tags=tags)
    B.cyl("ringhole", px, py, 0.05, rr - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(px, py, rr + 0.075, 24, math.pi / 24)
           if abs(x) < w / 2 - 0.05 and y < h / 2 - 0.05]
    B.bolts("rb", pts, 0.1, 0.016, S, tags=tags)
    # calcos de proa nos cantos da frente (montagem fixa)
    for sx in (-1, 1):
        tri = [(sx * 0.44, 0.94), (sx * 0.30, 0.94), (sx * 0.44, 0.80)]
        B.plate(f"chock{sx}", tri if sx < 0 else list(reversed(tri)), 0.06, 0.11, AM, slope=0.015, tags=tags)
    # tremonha de celulas PEM (tile de tras): caixa blindada sem pintura, janela com 3 celulas, calha ate o cardan
    hy = -0.50
    hop = [(-0.30, -0.93), (0.30, -0.93), (0.40, -0.83), (0.40, -0.20), (0.26, -0.08), (-0.26, -0.08),
           (-0.40, -0.20), (-0.40, -0.83)]
    ha, hp = B.shard("hopper", hop, 0.04, 0.16, AM, slope=0.03, groove=0.02, panel_h=0.02, tags=tags)
    win = B.rpoly(0, hy - 0.02, 0.50, 0.46, 0, chamfer=0.05)
    for t in (ha, hp):
        if t is not None:
            B.cut(t, [B.loft(f"hwin{t.name}", win, win, 0.10, 0.5, K, bevel=0.0)])
    B.loft("hwin_bed", win, win, 0.095, 0.105, M["black"], bevel=0.0, tags=tags)
    for i, y in enumerate((hy - 0.17, hy - 0.02, hy + 0.13)):
        cell(f"hcell{i}", 0, y, 0.15, 0.052, 0.44, M, X, tags, axis="X")
    # grade de aco sobre a janela (2 barras ao longo de y): quebra o brilho e segura as celulas
    for sx in (-1, 1):
        B.box(f"hgrille{sx}", sx * 0.11, hy - 0.02, 0.022, 0.46, 0.20, 0.225, S, bevel=0.004, tags=tags)
    # linhas de painel e parafusos na tampa da tremonha
    if hp is not None:
        B.cut(hp, [B.box(f"hpl{sx}", sx * 0.295, -0.52, 0.014, 0.30, 0.16, 0.5, K, bevel=0.0) for sx in (-1, 1)])
    B.bolts("hbolt", [(sx * 0.29, y) for sx in (-1, 1) for y in (-0.82, -0.20)], 0.185, 0.016, S, tags=tags)
    # contador da tremonha (4 LEDs azuis num rebaixo) e calha de alimentacao ate o poco do cardan
    Mo.slot_with_pips("hcnt", -0.815, -0.16, 0.16, 0.04, 0.18, 4, M, tags, target=[ha, hp], depth=0.07,
                      vertical=False)
    B.box("chute", 0, -0.05, 0.14, 0.14, 0.06, 0.13, KM, bevel=0.01, tags=tags)
    B.box("chuter", 0, -0.05, 0.16, 0.025, 0.06, 0.14, S, bevel=0.004, tags=tags)


def floor(M, T="floor"):
    """Piso: base do cardan no tile da frente, posto do atirador atras com console e prateleira de celulas."""
    from bsgen.common import crew_positions
    tags = (T,)
    X = pem(M)
    w, h = PART["size"]
    pv = PART["pivot"]
    rr = PART["ring_r"]
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    px, py = pv[0] - w / 2, h / 2 - pv[1]
    B.box("fl_base", 0, 0, w, h, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for ty in range(h):
        B.box(f"fl{ty}", 0, h / 2 - ty - 0.5, 0.92, 0.92, 0.0, 0.03, KM, bevel=0.01, tags=tags)
    B.torus("fl_ring", px, py, 0.05, rr * 0.78, 0.04, AM, tags=tags)
    B.cyl("fl_hub", px, py, 0.05, rr * 0.32, 0.08, A, axis="Z", verts=8, tags=tags)
    B.cyl("fl_hubc", px, py, 0.09, rr * 0.14, 0.012, X["copper"], axis="Z", verts=8, bevel=0.0, tags=tags)
    B.box("fl_led_t", px, py + rr * 0.95, 0.20, 0.035, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    for i, (cx, cy, _r) in enumerate(crew_positions(w, h, PART["crew"], pv)):
        x, y = cx - w / 2, h / 2 - cy
        B.box(f"seatb{i}", x, y + 0.04, 0.32, 0.30, 0.0, 0.05, S, bevel=0.012, tags=tags)
        B.box(f"seat{i}", x, y + 0.06, 0.26, 0.20, 0.05, 0.14, A, bevel=0.035, tags=tags)
        B.box(f"seatbk{i}", x, y - 0.09, 0.28, 0.07, 0.05, 0.24, KM, bevel=0.02, tags=tags)
        B.box(f"console{i}", x, y + 0.31, 0.36, 0.11, 0.0, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.31, 0.24, 0.05, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
        for sx in (-1, 1):
            # celulas de reserva em pe dos lados do assento
            B.cyl(f"fcell{sx}", x + sx * 0.36, y - 0.02, 0.10, 0.07, 0.20, X["navy"], axis="Z", verts=10,
                  bevel=0.006, tags=tags)
            B.cyl(f"fcellc{sx}", x + sx * 0.36, y - 0.02, 0.205, 0.05, 0.012, X["cap"], axis="Z", verts=10,
                  bevel=0.0, tags=tags)
    B.box("rack", 0, -h / 2 + 0.11, 0.80, 0.14, 0.0, 0.14, AM, bevel=0.01, tags=tags)
    for i in range(3):
        B.cyl(f"rcell{i}", -0.25 + i * 0.25, -h / 2 + 0.11, 0.18, 0.05, 0.12, X["navy"], axis="X", verts=10,
              bevel=0.004, tags=tags)
        B.box(f"rled{i}", -0.25 + i * 0.25, -h / 2 + 0.11, 0.05, 0.025, 0.23, 0.245, M["glow_dim"], bevel=0.0,
              tags=tags)
