"""Gatling de Plasma ("Boitata") - a serpente de fogo do folclore; torre rotativa de 4 canos, 2x3, familia do 76 mm.

Cabeca de vibora alongada em ponta de flecha que afunila num pescoco atras: escamas finas empilhadas nos flancos
(a da dobradica por cima, com segundo nivel e fenda de pips; o labio sai de baixo dela; a presa sai de baixo do
labio), cada uma terminando num dente para a frente; pistoes ligando labio e presa; escudo frontal com sensor
entre dois olhos ciano em fenda (orbitas escuras com aro de aco), dois parietais por cima com a costura dorsal
acesa (a linha de fogo do Boitata), celulas de plasma com nivel ciano nos vaos e dutos ate o focinho, focinho
escuro em ponta com o mesmo emblema de chevrons do tambor (aparece com o cano por cima ou por baixo) e baia de
exaustao no pescoco.
Teto com estante de 4 celulas de plasma na fileira de tras e duto com nervuras em chevron.
Cano: grupo de 4 canos (gira phase*90 graus) com 3 bobinas ciano por cano (anel aceso afundado entre dois labios
escuros, luva limpa entre elas), caixa do motor escura com o emblema (chevrons acesos no topo, escamas de aco
em chevron nas facetas), abracadeira do meio escura, bloco da frente claro em ponta de flecha com portas escuras
e pontas que aquecem em ciano nos quadros de giro (alma escura na boca de cada uma).
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_plasma_gatling",
    "kind": "gun",
    "size": [2, 3],
    "pivot": [1.0, 1.0],           # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 2.24,
    "ring_r": 0.86,
    "accent": "cyan",
    "collider": 0.98,
    "barrels": {
        "ys": [0.0],               # um sprite = o grupo de 4 canos
        "root": 0.50,
        "length": 1.48,
        "width": 0.52,
        "pad": 0.10,
        "anim": "spin",
        "spin_frames": 3,
        "spin_recoil": 0.02,
        "heat_color": (0.25, 0.85, 1.0),   # calor de plasma (ciano)
        "heat": [0.55, 0.45, 0.55, 0.45],  # um valor por quadro de giro (spin_frames + 1), pulsando
        "interval": 0.05,
    },
    "lights": [
        {"at": [0.0, -0.84], "size": 1.0, "color": [70, 215, 255], "z": 0.8},
    ],
    "preview_pattern": "rotary",
}

RING_R = PART["ring_r"]
ZB = 0.55                          # altura do eixo do grupo de canos


# ============================================================================ utilidades locais
def ycyl(name, x, y, z, r, length, mat, verts=8, roll=0.0, bevel=0.01, tags=(), r2=None):
    """Cilindro no eixo Y com giro (roll, graus) em torno do proprio eixo; r atras, r2 na frente."""
    ob = B.cyl(name, x, y, z, r, length, mat, axis="Y", verts=verts, bevel=bevel, tags=tags, r2=r2)
    ob.rotation_euler = (math.radians(-90), math.radians(roll), 0.0)
    return ob


def _lines(target, name, specs, ztop, mat, w=0.016, depth=0.02):
    """Linhas de painel recortadas no alvo: specs = [(x, y, comprimento, rotacao)]."""
    if target is None:
        return
    B.cut(target, [B.rbox(f"{name}{i}", x, y, w, ln, ztop - depth, ztop + 0.4, mat, rot=r, bevel=0.0)
                   for i, (x, y, ln, r) in enumerate(specs)])


def _rslot(name, cx, cy, ln, w, rot, ztop, n, M, tags, targets, depth=0.04, lit=None, pw=0.45, pl=0.45):
    """Fenda de pips girada (eixo longo = y local girado por rot), recortada nos alvos.
    pw/pl = fracao da largura/passo ocupada por cada pip (o resto fica como moldura escura)."""
    for t in targets:
        if t is not None:
            B.cut(t, [B.rbox(name + "_c", cx, cy, w, ln, ztop - depth, ztop + 0.3, M["black"], rot=rot, bevel=0.0)])
    B.rbox(name + "_bed", cx, cy, w, ln, ztop - depth - 0.01, ztop - depth + 0.004, M["black"], rot=rot,
           bevel=0.0, tags=tags)
    a = math.radians(rot)
    ux, uy = -math.sin(a), math.cos(a)
    for i in range(n):
        s = ((i + 0.5) / n - 0.5) * ln
        on = lit is None or i < lit
        B.rbox(f"{name}_p{i}", cx + ux * s, cy + uy * s, w * pw, ln / n * pl, ztop - depth,
               ztop - depth + 0.012, M["glow"] if on else M["core_mid"], rot=rot, bevel=0.0, tags=tags)


def _scale(name, poly, z0, z1, M, tags, shim=True, slope=0.05, groove=0.028, panel_h=0.022):
    """Escama fina empilhada: pedestal escuro escondido, contorno preto fino na base (sombra de sobreposicao)
    e placa com bisel duplo por cima."""
    ped = B.robust_offset(poly, 0.10)
    if ped is not None and z0 > 0.34:
        B.plate(name + "_ped", ped, 0.30, z0 + 0.004, M["core_mid"], slope=0.0, bevel=0.0, tags=tags)
    if shim:
        B.plate(name + "_shim", B.offset_poly(poly, -0.016, max_miter=1.6), z0 - 0.03, z0 + 0.006, M["black"],
                slope=0.0, bevel=0.0, tags=tags)
    return B.shard(name, poly, z0, z1, M["armor"], slope=slope, groove=groove, panel_h=panel_h, tags=tags)


def _chevron(yc, hw, d, th):
    """Chevron em ponta para a frente (+y): faixa de espessura th entre duas linhas em V (abas em yc, ponta yc+d)."""
    return [(-hw, yc - th), (0.0, yc + d - th), (hw, yc - th), (hw, yc), (0.0, yc + d), (-hw, yc)]


def _on_facet(ob, ang, z):
    """Leva uma peca modelada em cima do eixo (z local = distancia ao eixo) para a faceta girada ang graus."""
    ob.rotation_euler = (0.0, math.radians(ang), 0.0)
    ob.location = (0.0, 0.0, z)
    return ob


# ============================================================================ cabeca
def head(M, T="head", phase=0.0):
    """Cabeca de vibora em ponta de flecha: escamas empilhadas nos flancos, escudos do cranio, olhos ciano."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]

    # anel giratorio e nucleo escuro (seta alongada que afunila no pescoco)
    B.cyl("ring", 0, 0, 0.04, RING_R + 0.04, 0.08, KM, axis="Z", verts=64, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, RING_R - 0.03, 20, 0.16), 0.09, 0.02, S, tags=tags)
    core = [(-0.28, 0.86), (0.28, 0.86), (0.62, 0.50), (0.86, -0.36), (0.46, -0.90), (0.28, -1.04),
            (-0.28, -1.04), (-0.46, -0.90), (-0.86, -0.36), (-0.62, 0.50)]
    B.plate("core", core, 0.06, 0.32, K, slope=0.05, tags=tags)

    # focinho escuro (mantelete) em ponta de chevron, de onde sai o grupo de canos (tudo escuro em |x| < 0.28)
    mant = [(-0.22, 0.30), (0.22, 0.30), (0.28, 0.40), (0.28, 0.70), (0.20, 0.86), (0.0, 0.94), (-0.20, 0.86),
            (-0.28, 0.70), (-0.28, 0.40)]
    m = B.plate("mantlet", mant, 0.30, 0.62, KM, slope=0.05, tags=tags)
    # emblema da serpente no mesmo lugar do da caixa do motor (raiz do cano em y=0.50): com a cabeca por cima
    # do cano os 3 chevrons acesos continuam no mesmo ponto; linha de painel transversal na frente
    B.cut(m, [B.loft(f"m_chev{i}", _chevron(0.565 + i * 0.062, 0.068, 0.040, 0.030),
                     _chevron(0.565 + i * 0.062, 0.068, 0.040, 0.030), 0.58, 0.9, K, bevel=0.0) for i in range(3)]
          + [B.box("m_line", 0, 0.80, 0.28, 0.016, 0.60, 0.9, K, bevel=0.0),
             B.box("m_line2", 0, 0.48, 0.36, 0.016, 0.60, 0.9, K, bevel=0.0)])
    B.box("m_chevbed", 0, 0.63, 0.15, 0.22, 0.574, 0.584, B.mat_glow("emblem_h", Mo.CYAN, 0.7), bevel=0.0,
          tags=tags)
    # escamas de aco em chevron dos dois lados do emblema (eco das escamas das facetas do tambor)
    for sx in (-1, 1):
        for j, y0 in enumerate((0.545, 0.617, 0.689) if sx > 0 else (0.525, 0.597, 0.669)):
            B.plate(f"m_scale{sx}{j}", [(x + sx * 0.15, y) for x, y in _chevron(y0, 0.036, 0.022, 0.024)],
                    0.615, 0.634, S, slope=0.0, bevel=0.003, tags=tags)

    # flanco em seta (lado esquerdo): escama da dobradica por cima, labio do meio, presa em lamina na frente;
    # cada escama sai de baixo da de tras e termina num dente que aponta para a frente
    hinge = [(-0.32, -0.94), (-0.46, -0.94), (-0.90, -0.42), (-0.80, 0.08), (-0.50, -0.06), (-0.46, -0.30),
             (-0.46, -0.62), (-0.32, -0.76)]
    lip = [(-0.48, -0.22), (-0.70, -0.08), (-0.596, 0.508), (-0.42, 0.40), (-0.46, 0.10)]
    jaw = [(-0.30, 0.30), (-0.44, 0.30), (-0.50, 0.37), (-0.36, 1.04), (-0.30, 1.00)]
    # painel interno da presa desenhado a mao (o deslocamento automatico some numa lamina tao fina)
    jaw_pnl = [(-0.366, 0.40), (-0.425, 0.40), (-0.386, 0.60), (-0.366, 0.64)]
    # bordo externo da dobradica: O -> F; P(t, d) anda t ao longo dele e d para dentro (perpendicular)
    ox, oy, fx, fy = 0.90, -0.42, 0.80, 0.08
    el = math.hypot(fx - ox, fy - oy)
    ex_, ey_ = (fx - ox) / el, (fy - oy) / el          # direcao do bordo (lado direito: x diminui)
    edge_rot = math.degrees(math.atan2(-ex_, ey_))     # giro do eixo y local para alinhar com o bordo (lado direito)
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        B.shard(f"jaw_{side}", f(jaw), 0.30, 0.56, A, slope=0.05, groove=0.025, panel_h=0.022, tags=tags)
        B.plate(f"jaw_pnl_{side}", f(jaw_pnl), 0.556, 0.578, A, slope=0.0, bevel=0.005, tags=tags)
        _scale(f"lip_{side}", f(lip), 0.60, 0.70, M, tags)
        ha, hp = _scale(f"hinge_{side}", f(hinge), 0.74, 0.84, M, tags)

        def P(t, d):
            return (sx * (ox + t * el * ex_ - d * ey_), oy + t * el * ey_ + d * ex_)
        # segundo nivel em degrau ao longo do bordo externo (escama sobre escama) com fenda de pips
        tier = [P(0.04, 0.08), P(0.84, 0.08), P(0.64, 0.30), P(0.0, 0.30)]
        ta, tp = _scale(f"tier_{side}", tier, 0.855, 0.93, M, tags, slope=0.03, groove=0.018, panel_h=0.018)
        cx, cy = P(0.40, 0.19)
        _rslot(f"hslot{side}", cx, cy, 0.27, 0.065, sx * edge_rot, 0.93, 3, M, tags, [ta, tp], depth=0.05, lit=2)
        # linha de painel paralela ao bordo diagonal de tras da dobradica
        _lines(hp, f"hl{side}", [(sx * 0.581, -0.596, 0.30, sx * -40.3)], 0.862, K)
        # olho: orbita escura facetada entre o escudo frontal e o labio, aro de aco, pupila ciano em fenda
        ex, ey, er = sx * 0.355, 0.20, sx * 30.0
        B.rbox(f"eyepod{side}", ex, ey, 0.13, 0.27, 0.40, 0.66, KM, rot=er, chamfer=0.05, slope=0.03, bevel=0.01,
               tags=tags)
        rim = B.rbox(f"eyerim{side}", ex, ey, 0.10, 0.22, 0.655, 0.685, S, rot=er, chamfer=0.04, slope=0.01,
                     bevel=0.004, tags=tags)
        B.cut(rim, [B.rbox(f"eyecut{side}", ex, ey, 0.07, 0.17, 0.668, 0.9, K, rot=er, chamfer=0.028, bevel=0.0)])
        B.rbox(f"eyebed{side}", ex, ey, 0.07, 0.17, 0.66, 0.67, M["black"], rot=er, chamfer=0.028, bevel=0.0,
               tags=tags)
        B.rbox(f"eyeglow{side}", ex, ey, 0.022, 0.13, 0.67, 0.678, M["glow"], rot=er, chamfer=0.008, bevel=0.0,
               tags=tags)
        # pistao hidraulico: sai de baixo do dente do labio e segura a presa (preenche o canto do anel)
        B.cyl(f"piston{side}", sx * 0.535, 0.67, 0.44, 0.028, 0.30, S, axis="Y", verts=12, yaw=sx * 30, tags=tags)
        B.cyl(f"pistonb{side}", sx * 0.60, 0.555, 0.44, 0.045, 0.16, KM, axis="Y", verts=12, yaw=sx * 30, tags=tags)
        B.cyl(f"pistonr{side}", sx * 0.578, 0.594, 0.44, 0.05, 0.022, S, axis="Y", verts=12, yaw=sx * 30, tags=tags)

    # cranio: escudo frontal (com sensor) e dois parietais por cima, com a costura dorsal acesa entre eles
    frontal = [(-0.20, -0.24), (0.20, -0.24), (0.26, -0.14), (0.26, 0.14), (0.10, 0.38), (-0.10, 0.38),
               (-0.26, 0.14), (-0.26, -0.14)]
    fa, fp = B.shard("frontal", frontal, 0.30, 0.80, A, slope=0.07, groove=0.03, panel_h=0.025, tags=tags)
    win = [(-0.09, 0.02), (0.09, 0.02), (0.09, 0.08), (0.035, 0.17), (-0.035, 0.17), (-0.09, 0.08)]
    for t in (fa, fp):
        if t is not None:
            B.cut(t, [B.loft(f"win_cut{t.name}", win, win, 0.76, 1.2, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 0.755, 0.765, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, 0.07, 0.12, 0.02, 0.76, 0.768, M["glow_dim"], bevel=0.0, tags=tags)
    par = [(-0.05, -0.80), (-0.20, -0.80), (-0.28, -0.66), (-0.28, -0.20), (-0.20, -0.04), (-0.05, -0.12)]
    for side, f in (("L", lambda p: p), ("R", Mo.mirror)):
        pa, pp = _scale(f"par_{side}", f(par), 0.83, 0.93, M, tags)
        sx = -1 if side == "L" else 1
        _lines(pp, f"pl{side}", [(sx * 0.17, -0.56, 0.20, 0), (sx * 0.15, -0.22, 0.12, sx * -40)], 0.952, K)
    # costura dorsal: leito escuro com a linha de fogo (pips ciano) da serpente
    B.box("seam", 0, -0.45, 0.10, 0.70, 0.70, 0.84, KM, bevel=0.0, tags=tags)
    B.box("seam_bed", 0, -0.45, 0.07, 0.62, 0.84, 0.846, M["black"], bevel=0.0, tags=tags)
    for i in range(5):
        B.box(f"seam_pip{i}", 0, -0.70 + i * 0.12, 0.024, 0.04, 0.846, 0.852,
              M["glow_dim"] if i < 4 else M["core_mid"], bevel=0.0, tags=tags)

    # celulas de plasma nos vaos entre os parietais e as escamas (nivel ciano) e dutos ate o focinho
    for sx in (-1, 1):
        x = sx * 0.37
        B.cyl(f"cell{sx}", x, -0.36, 0.44, 0.068, 0.56, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
        for i, y in enumerate((-0.62, -0.10)):
            B.cyl(f"cellcap{sx}{i}", x, y, 0.44, 0.076, 0.045, S, axis="Y", verts=8, bevel=0.005, tags=tags)
        B.box(f"cellwin{sx}", x, -0.36, 0.044, 0.40, 0.50, 0.51, M["black"], bevel=0.0, tags=tags)
        for i in range(4):
            B.box(f"cellled{sx}{i}", x, -0.51 + i * 0.10, 0.026, 0.05, 0.51, 0.517,
                  M["glow"] if i < 3 else M["core_mid"], bevel=0.0, tags=tags)
        # duto de plasma octogonal da tampa da celula para a frente (some debaixo da orbita do olho)
        yaw = sx * 10.0
        ux, uy = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        B.cyl(f"feed{sx}", x + ux * 0.10, -0.08 + uy * 0.10, 0.43, 0.046, 0.24, KM, axis="Y", verts=8, yaw=yaw,
              bevel=0.006, tags=tags)
        for i, t in enumerate((0.05, 0.13)):
            B.cyl(f"feedr{sx}{i}", x + ux * t, -0.08 + uy * t, 0.43, 0.056, 0.022, S, axis="Y", verts=8, yaw=yaw,
                  bevel=0.004, tags=tags)

    # baia de exaustao no pescoco (persianas + pips ciano)
    B.box("vent_bay", 0, -0.92, 0.50, 0.18, 0.26, 0.36, M["black"], bevel=0.0, tags=tags)
    for i in range(4):
        B.box(f"louver{i}", 0, -0.985 + i * 0.042, 0.46, 0.02, 0.30, 0.37, KM, bevel=0.004, tags=tags)
    for i, x in enumerate((-0.18, -0.06, 0.06, 0.18)):
        B.box(f"vent_pip{i}", x, -0.842, 0.045, 0.02, 0.34, 0.38, M["glow"], bevel=0.0, tags=tags)
    B.bolts("bolt", [(x, -0.99) for x in (-0.31, 0.31)], 0.34, 0.02, S, tags=tags)


# ============================================================================ cano
def barrel(M, L=1.48, T="barrel", phase=0.0):
    """Grupo de 4 canos: raiz (y=0) na caixa do motor, boca em y=L. phase gira o grupo phase*90 graus."""
    tags = (T,)
    hot = (T, "hot")
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = ZB
    rot = phase * 90.0
    spinning = phase > 1e-6
    # onda de carga: em cada quadro de giro uma bobina fica mais forte (corre da raiz para a boca)
    nsp = PART["barrels"].get("spin_frames", 3) + 1
    k = int(round(phase * nsp))                       # 1..nsp nos quadros de giro, 0 em repouso
    hi = B.mat_glow("coil_hi", Mo.CYAN, 2.0)          # mais forte, mas ainda ciano (branco fica para o overclock)
    lo = B.mat_glow("coil_lo", Mo.CYAN, 1.1 if spinning else 0.4)
    emb = B.mat_glow("emblem", Mo.CYAN, 1.2 if spinning else 0.5)
    tipm = B.mat_glow("tip_plasma", Mo.CYAN, 0.30) if spinning else S

    # caixa do motor (fixa): octogono escuro de topo plano com o emblema de escamas da serpente
    hb = ycyl("b_motor", 0, 0.13, z, 0.225, 0.26, KM, verts=8, roll=22.5, bevel=0.012, tags=tags)
    # 3 chevrons em ponta para a frente recortados no topo, com leito ciano no fundo
    B.cut(hb, [B.loft(f"b_chev{i}", _chevron(0.065 + i * 0.062, 0.068, 0.040, 0.030),
                      _chevron(0.065 + i * 0.062, 0.068, 0.040, 0.030), z + 0.17, z + 0.4, K, bevel=0.0)
               for i in range(3)])
    B.box("b_chevbed", 0, 0.13, 0.15, 0.22, z + 0.166, z + 0.176, emb, bevel=0.0, tags=tags)
    # escamas de aco nas facetas de 45 graus, intercaladas com os chevrons (a espiral em volta do tambor)
    apo = 0.225 * math.cos(math.radians(22.5))
    for sx in (-1, 1):
        for j, y0 in enumerate((0.045, 0.117, 0.189) if sx > 0 else (0.025, 0.097, 0.169)):
            _on_facet(B.plate(f"b_scale{sx}{j}", _chevron(y0, 0.036, 0.022, 0.024), apo - 0.006, apo + 0.016, S,
                              slope=0.0, bevel=0.003, tags=tags), sx * 45.0, z)
    ycyl("b_motorcap", 0, -0.015, z, 0.20, 0.03, S, verts=8, roll=22.5, bevel=0.005, tags=tags)
    ycyl("b_motorring", 0, 0.255, z, 0.235, 0.025, S, verts=8, roll=22.5, bevel=0.004, tags=tags)
    ycyl("b_nose", 0, 0.32, z, 0.215, 0.10, KM, verts=8, roll=22.5, bevel=0.008, tags=tags, r2=0.18)
    # cubo do rotor (gira) e eixo central
    ycyl("b_hub", 0, 0.405, z, 0.185, 0.07, S, verts=8, roll=rot + 22.5, bevel=0.008, tags=tags)
    y0, yf0, yf1 = 0.44, L - 0.34, L - 0.19
    ycyl("b_axle", 0, (y0 + yf0) / 2, z, 0.05, yf0 - y0, KM, verts=8, roll=rot, bevel=0.0, tags=tags)
    # 4 canos nervurados em volta do eixo (fase 0 = um cano no topo)
    Rc, rb = 0.12, 0.048
    coils = (0.599, 0.755, 0.912)     # alinhadas aos pixels nos quadros de giro (recuo 0.02): anel nao se divide
    for i in range(4):
        a = math.radians(i * 90 + rot)
        bx, bz = Rc * math.sin(a), z + Rc * math.cos(a)
        ycyl(f"b_bar{i}", bx, (y0 + yf0) / 2, bz, rb, yf0 - y0, A, verts=8, roll=rot, bevel=0.004, tags=tags)
        # nervuras so nas pontas da luva (entre as bobinas a luva fica limpa)
        for j, y in enumerate((0.49, 1.10)):
            ycyl(f"b_rib{i}{j}", bx, y, bz, rb + 0.009, 0.026, AM, verts=8, roll=rot, bevel=0.0, tags=tags)
        # bobinas: anel aceso afundado entre dois labios escuros; o anel e estreito e girado 22.5 graus para
        # deixar um vao escuro entre canos vizinhos (o grupo de 4 se le mesmo parado)
        for j, y in enumerate(coils):
            for e in (-1, 1):
                ycyl(f"b_cl{i}{j}{e}", bx, y + e * 0.022, bz, rb + 0.022, 0.02, K, verts=8, roll=rot, bevel=0.0,
                     tags=tags)
            gm = hi if (spinning and j == k - 1) else lo
            ycyl(f"b_cg{i}{j}", bx, y, bz, rb + 0.008, 0.022, gm, verts=8, roll=rot + 22.5, bevel=0.0, tags=tags)
        # ponta (so ela aquece): sai do bloco da frente; nos quadros de giro brilha fraco em ciano
        ycyl(f"b_tip{i}", bx, (yf1 + L - 0.04) / 2, bz, rb * 0.98, L - 0.04 - yf1, tipm, verts=8, roll=rot,
             bevel=0.004, tags=hot)
        # aro escuro na boca de cada ponta (frio): separa os 4 emissores no brilho; alma escura saindo da boca
        ycyl(f"b_tipend{i}", bx, L - 0.025, bz, rb * 1.06, 0.03, KM, verts=8, roll=rot, bevel=0.004, tags=tags)
        ycyl(f"b_bore{i}", bx, L - 0.01, bz, 0.022, 0.04, K, verts=8, roll=rot, bevel=0.0, tags=tags)
    # abracadeira do meio (escura, gira)
    ycyl("b_clamp_mid", 0, 1.04, z, 0.20, 0.05, KM, verts=8, roll=rot + 22.5, bevel=0.006, tags=tags)
    # bloco da frente claro facetado em ponta de flecha, 3 portas escuras transversais espacadas
    blk = [(-0.19, yf0), (0.19, yf0), (0.225, yf0 + 0.04), (0.225, yf1 - 0.06), (0.12, yf1 + 0.05),
           (-0.12, yf1 + 0.05), (-0.225, yf1 - 0.06), (-0.225, yf0 + 0.04)]
    br = B.plate("b_clamp", blk, z - 0.17, z + 0.17, A, slope=0.045, tags=tags)
    B.cut(br, [B.box(f"b_port{i}", 0, yf0 + 0.045 + i * 0.058, 0.50, 0.026, z + 0.10, z + 0.4, K, bevel=0.0)
               for i in range(3)])
    B.box("b_clamp_core", 0, yf0 + 0.09, 0.18, 0.14, z - 0.10, z + 0.11, K, bevel=0.0, tags=tags)
    # coroa escura logo depois do bico (separa o bloco claro das pontas quentes)
    ycyl("b_crown", 0, yf1 + 0.062, z, 0.165, 0.025, KM, verts=8, roll=rot + 22.5, bevel=0.004, tags=tags)


# ============================================================================ teto
def roof(M, T="roof"):
    """Teto 2x3: placas verdes, anel da torre e estante de celulas de plasma na fileira de tras."""
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
    # anel da torre (sem pintura); parafusos defasados para nao cair nos vaos entre placas
    B.torus("ringbear", px, py, 0.08, RING_R + 0.02, 0.05, KM, tags=tags)
    B.cyl("ringhole", px, py, 0.05, RING_R - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    B.bolts("rb", B.ring_points(px, py, RING_R + 0.09, 28, math.pi / 28), 0.1, 0.02, S, tags=tags)
    # estante de celulas (fileira de tras): bandeja escura com 4 celulas deitadas e coluna de nivel ciano
    hy = -h / 2 + 0.5
    tray = B.rpoly(0, hy - 0.04, 1.80, 0.60, 0, chamfer=0.12)
    t = B.plate("tray", tray, 0.04, 0.12, KM, slope=0.03, tags=tags)
    B.cut(t, [B.box("tray_cut", 0, hy - 0.04, 1.66, 0.46, 0.09, 0.3, K, bevel=0.0)])
    B.box("tray_bed", 0, hy - 0.04, 1.66, 0.46, 0.07, 0.095, M["black"], bevel=0.0, tags=tags)
    lit = (4, 3, 4, 2)
    for i in range(4):
        x = -0.63 + i * 0.42
        cy = hy - 0.05
        B.cyl(f"rcell{i}", x, cy, 0.17, 0.12, 0.40, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
        for e in (-1, 1):
            B.cyl(f"rcap{i}{e}", x, cy + e * 0.19, 0.17, 0.13, 0.05, S, axis="Y", verts=8, bevel=0.005, tags=tags)
        B.box(f"rlvlbed{i}", x, cy, 0.06, 0.30, 0.282, 0.292, M["black"], bevel=0.0, tags=tags)
        for k in range(4):
            B.box(f"rlvl{i}{k}", x, cy - 0.105 + k * 0.07, 0.028, 0.038, 0.292, 0.298,
                  M["glow"] if k < lit[i] else M["core_mid"], bevel=0.0, tags=tags)
    # duto de plasma entre a estante e o anel, com nervuras de aco em chevron (as escamas do Boitata)
    cy0, cy1 = hy + 0.26, py - RING_R - 0.03
    B.box("feed", 0, (cy0 + cy1) / 2, 0.14, cy1 - cy0, 0.05, 0.12, KM, bevel=0.012, slope=0.01, tags=tags)
    B.box("feedbed", 0, (cy0 + cy1) / 2, 0.07, cy1 - cy0 - 0.04, 0.12, 0.125, M["black"], bevel=0.0, tags=tags)
    B.box("feedg", 0, (cy0 + cy1) / 2, 0.02, cy1 - cy0 - 0.08, 0.125, 0.13, M["glow_dim"], bevel=0.0, tags=tags)
    for i in range(3):
        ch = _chevron(cy0 + (i + 0.5) * (cy1 - cy0) / 3 - 0.02, 0.09, 0.04, 0.03)
        B.loft(f"feedrib{i}", ch, ch, 0.05, 0.14, S, bevel=0.004, tags=tags)


# ============================================================================ piso
def floor(M, T="floor"):
    """Piso padrao (bancos, consoles, estantes) + duto de plasma da estante ate o anel."""
    tags = (T,)
    w, h = PART["size"]
    pv = PART["pivot"]
    from bsgen.common import crew_positions
    Mo.hull_floor(M, w, h, pv, RING_R, crew_positions(w, h, 2, pv), T)
    py = h / 2 - pv[1]
    y0, y1 = -h / 2 + 0.36, py - RING_R * 0.95 - 0.05
    B.box("fl_feed", 0, (y0 + y1) / 2, 0.16, y1 - y0, 0.0, 0.07, M["core_mid"], bevel=0.01, tags=tags)
    B.box("fl_feedbed", 0, (y0 + y1) / 2, 0.08, y1 - y0 - 0.04, 0.07, 0.075, M["black"], bevel=0.0, tags=tags)
    B.box("fl_feedg", 0, (y0 + y1) / 2, 0.02, y1 - y0 - 0.10, 0.075, 0.08, M["glow_dim"], bevel=0.0, tags=tags)
    n = 4
    for i in range(n):
        y = y0 + (i + 0.5) * (y1 - y0) / n
        B.box(f"fl_feedrib{i}", 0, y, 0.18, 0.025, 0.0, 0.085, M["steel"], bevel=0.004, tags=tags)
