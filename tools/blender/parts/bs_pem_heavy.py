"""Canhao PEM Pesado ("PEM pesada", 155 mm; codinome ainda em aberto) - torre dupla blindada, familia do 76 mm +
assinatura PEM. So o ID entra nos nomes de arquivo (o codinome "Mae-do-Ouro" e provisorio).

Cabeca 4x4 larga e baixa: duas ombreiras claras de bisel duplo em cunha que avancam como garras ao lado dos canos
(com fendas de pips azuis), cada uma com uma BOBINA DE CAMPO deitada num rebaixo (espiras de cobre sobre um nucleo
azul fraco); bercos escuros dos canos; proa central em ponta de flecha entre os canos com a fileira de ELETRODOS de
cobre (de onde saltam os arcos antes do tiro); bancos de CAPACITORES em pe atras dos bercos (tampas de cobre com
anel azul); espinha de dois niveis com janela do sensor e o pulso PEM gravado; baia de exaustao traseira com 6 pips
azuis; placas traseiras em degrau.
Canos longos de 155 mm em PILHAS DE BOBINAS que brilham (espiras de cobre com frestas azuis acesas), luvas claras com
canal e o ANEL PARA-RAIOS na boca (aro claro largo com duas hastes de para-raios de ponta de cobre). Depois do tiro as
bobinas da frente e a boca brilham em azul (heat_color azul).
Brilho de carga (charge_glow1..4, opcao do render_part "charge_glow"): 0,5 s antes de cada tiro as bobinas de campo,
os capacitores e os eletrodos da proa acendem em rampa e arcos azuis saltam entre os canos (quadros 3 e 4).
Kit da familia PEM: parts/bs_pem_light.py (pem, coil, rslot, stroke).
"""

import math
import random

import bs3d as B
import models as Mo
from parts.bs_pem_light import coil, coil_layout, pem, rslot, side, stroke, turn

PART = {
    "id": "rafaeltessaro.bs_pem_heavy",
    "kind": "gun",
    "size": [4, 4],
    "pivot": [2.0, 1.70],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 3.92,            # lado do quadrado do sprite da torre (cabeca ate +-1.90)
    "ring_r": 1.50,                # raio do anel da torre no teto/piso
    "accent": "blue",
    "collider": 1.62,
    "crew": 3,                     # SPEC_2.0 pem_weapons[PEM pesada].crew
    "barrels": {
        "ys": [-0.50, 0.50],       # dois canos lado a lado (disparo alternado)
        "root": 0.95,              # pivo -> raiz do cano (a culatra fica no berco)
        "length": 2.95,            # raiz -> boca
        "width": 0.72,             # largura do sprite do cano (cabe o anel para-raios com folga)
        "pad": 0.34,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.30, 0.22, 0.14, 0.07, 0.025],          # 5 quadros de recuo + repouso (spec de arte)
        "heat": [0.80, 0.64, 0.48, 0.32, 0.16],             # bobinas e boca azuis depois do tiro
        "heat_color": (0.05, 0.35, 1.0),
        "interval": 0.08,
    },
    # brilho de carga antes do tiro (spec de arte render_kinds.gun.new_option.charge_glow): 4 quadros de 0,125 s
    "charge_glow": {"frames": 4, "interval": 0.125, "color": "pem"},
    "lights": [
        {"at": [0.0, -1.32], "size": 1.7, "color": [60, 150, 255], "z": 0.9},
        {"at": [0.0, 1.10], "size": 1.2, "color": [60, 150, 255], "z": 0.9},
    ],
    "preview_pattern": "alternate",
    "preview_fx": "plasma",
}

YS = PART["barrels"]["ys"]
ZB = 0.70                          # altura do eixo dos canos
ROOT = PART["barrels"]["root"]
PAD = PART["barrels"]["pad"]
BOX = PART["turret_box"] / 2
# bobina de campo deitada em cada ombreira (centro x, faixa y, raio, altura do eixo)
FCOIL_X, FCOIL_Y, FCOIL_R, FCOIL_Z = 1.10, (-0.30, 0.62), 0.17, 0.62
FCOIL_WIRE = 0.020
# capacitores em pe atras dos bercos: (x, y) do lado direito
CAPS = [(0.52, -0.20), (0.76, -0.20), (0.52, 0.12), (0.76, 0.12)]
CAP_R = 0.112
# eletrodos da proa (lado direito): pinos de cobre na borda da proa, de onde saltam os arcos
ELECTRODES = [(0.13, 1.30), (0.12, 1.50), (0.10, 1.68)]
# tambores de celulas PEM na traseira (lado direito)
DRUM_X, DRUM_Y = 0.66, (-1.30, -0.52)
# pilhas de bobinas do cano: (inicio, fim, raio, segmentos); fio e passo (frestas acesas entre as espiras)
STACKS = [(0.48, 1.22, 0.272, 3), (1.74, 2.30, 0.258, 2)]
WIRE, SPACING = 0.019, 2.4

# ombreira esquerda: cunha que avanca como garra ao lado do cano (fora do sprite do cano: x <= -0.86)
SHOULDER = [(-0.92, -0.62), (-1.30, -0.62), (-1.62, -0.30), (-1.70, 0.40), (-1.58, 1.00), (-1.26, 1.62),
            (-1.04, 1.86), (-0.95, 1.80), (-0.88, 1.30), (-0.88, 0.80)]
SHOULDER_Z = (0.40, 0.86)
# placa do flanco atras da ombreira (degrau, quina traseira chanfrada)
FLANK = [(-1.00, -0.70), (-1.62, -0.70), (-1.62, -0.98), (-1.24, -1.40), (-1.00, -1.40)]


def stack_segments():
    """Trechos (a, b, raio) das bobinas do cano, entre os colares (o cano e o brilho de carga usam os mesmos)."""
    out = []
    for a, b, R, n in STACKS:
        seg = (b - a) / n
        out += [(a + j * seg + 0.026, a + (j + 1) * seg - 0.026, R) for j in range(n)]
    return out


def head(M, T="head", phase=0.0):
    """Torre dupla blindada: ombreiras com bobinas de campo, proa com eletrodos, capacitores, tambores, espinha."""
    tags = (T,)
    X = pem(M)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]

    # ---------------------------------------------------------------- anel e nucleo escuro
    B.cyl("ring", 0, 0, 0.04, 1.56, 0.08, KM, axis="Z", verts=96, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, 1.50, 36, 0.09), 0.09, 0.022, S, tags=tags)
    core = [(-1.12, -1.62), (1.12, -1.62), (1.66, -1.08), (1.70, 0.86), (1.08, 1.66), (-1.08, 1.66),
            (-1.70, 0.86), (-1.66, -1.08)]
    B.plate("core", core, 0.06, 0.42, K, slope=0.05, tags=tags)

    # ---------------------------------------------------------------- bercos escuros dos canos
    y0c = ROOT - PAD - 0.03
    for i, y in enumerate(YS):
        crad = [(y - 0.30, y0c), (y + 0.30, y0c), (y + 0.34, y0c + 0.06), (y + 0.34, 1.64), (y + 0.26, 1.72),
                (y - 0.26, 1.72), (y - 0.34, 1.64), (y - 0.34, y0c + 0.06)]
        c = B.plate(f"cradle{i}", crad, 0.36, 0.54, KM, slope=0.04, tags=tags)
        B.cut(c, [B.box(f"crad_c{i}", y, (y0c + 1.66) / 2, 0.46, 1.66 - y0c - 0.14, 0.48, 1.0, K, bevel=0.0)])
        B.box(f"cradbed{i}", y, (y0c + 1.66) / 2, 0.46, 1.66 - y0c - 0.14, 0.475, 0.485, M["black"], bevel=0.0,
              tags=tags)
        for j in range(3):
            B.box(f"cradled{i}{j}", y, y0c + 0.14 + j * 0.08, 0.10, 0.026, 0.48, 0.49,
                  X["glow_dim"] if j < 2 else M["black"], bevel=0.0, tags=tags)
        B.cyl(f"mouth{i}", y, 1.66, ZB - 0.02, 0.30, 0.10, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
        B.cyl(f"mouthr{i}", y, 1.61, ZB - 0.02, 0.31, 0.03, S, axis="Y", verts=8, bevel=0.005, tags=tags)

    # ---------------------------------------------------------------- proa central com os eletrodos
    prow = [(-0.15, 0.30), (0.15, 0.30), (0.15, 1.40), (0.05, 1.84), (-0.05, 1.84), (-0.15, 1.40)]
    pa, pp = B.shard("prow", prow, 0.42, 0.92, A, slope=0.045, groove=0.02, panel_h=0.025, tags=tags)
    B.box("prow_slot_bed", 0, 0.98, 0.05, 0.60, 0.905, 0.915, M["black"], bevel=0.0, tags=tags)
    for t in (pa, pp):
        if t is not None:
            B.cut(t, [B.box(f"prow_slot{t.name}", 0, 0.98, 0.05, 0.60, 0.91, 1.3, K, bevel=0.0)])
    for i in range(4):
        B.box(f"prow_led{i}", 0, 0.76 + i * 0.15, 0.026, 0.06, 0.91, 0.918, X["glow"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        for k, (ex, ey) in enumerate(ELECTRODES):
            B.cyl(f"elec{sx}{k}", sx * (ex + 0.03), ey, 0.80, 0.024, 0.10, X["copper"], axis="X", verts=8,
                  bevel=0.0, tags=tags)
            B.cyl(f"elecb{sx}{k}", sx * ex, ey, 0.80, 0.036, 0.03, KM, axis="X", verts=8, bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- bancos de capacitores (atras dos bercos)
    for sx in (-1, 1):
        B.box(f"capbay{sx}", sx * 0.64, -0.04, 0.52, 0.60, 0.38, 0.44, M["black"], bevel=0.0, tags=tags)
        for k, (cx, cy) in enumerate(CAPS):
            x = sx * cx
            B.cyl(f"cap{sx}{k}", x, cy, 0.52, CAP_R, 0.18, X["navy"], axis="Z", verts=12, bevel=0.008, tags=tags)
            B.cyl(f"capcu{sx}{k}", x, cy, 0.615, CAP_R * 0.92, 0.02, X["copper"], axis="Z", verts=12, bevel=0.0,
                  tags=tags)
            B.cyl(f"caprim{sx}{k}", x, cy, 0.628, CAP_R * 0.53, 0.012, X["glow_dim"], axis="Z", verts=12,
                  bevel=0.0, tags=tags)
            B.cyl(f"capcap{sx}{k}", x, cy, 0.638, CAP_R * 0.40, 0.022, S, axis="Z", verts=8, bevel=0.003,
                  tags=tags)
        # barramento de cobre dos capacitores ate o berco
        B.box(f"busb{sx}", sx * 0.64, 0.37, 0.50, 0.07, 0.40, 0.445, KM, bevel=0.004, tags=tags)
        B.box(f"bus{sx}", sx * 0.64, 0.37, 0.46, 0.035, 0.445, 0.47, X["copper"], bevel=0.004, tags=tags)

    # ---------------------------------------------------------------- tambores de celulas PEM (traseira)
    ya, yb = DRUM_Y
    for sx in (-1, 1):
        x = sx * DRUM_X
        B.box(f"drum_bed{sx}", x, (ya + yb) / 2, 0.30, yb - ya + 0.08, 0.38, 0.43, M["black"], bevel=0.0, tags=tags)
        B.cyl(f"drum{sx}", x, (ya + yb) / 2, 0.54, 0.125, yb - ya, X["navy"], axis="Y", verts=10, bevel=0.008,
              tags=tags)
        for k, y in enumerate((ya + 0.03, ya + 0.27, yb - 0.27, yb - 0.03)):
            B.cyl(f"drumcu{sx}{k}", x, y, 0.54, 0.132, 0.035, X["copper"] if 0 < k < 3 else S, axis="Y", verts=10,
                  bevel=0.003, tags=tags)
        for k in range(3):
            B.box(f"drumwin{sx}{k}", x, ya + 0.34 + k * 0.05, 0.07, 0.024, 0.64, 0.67,
                  X["cell"] if k < 2 else M["black"], bevel=0.0, tags=tags)
        B.cyl(f"drumcap{sx}", x, yb + 0.03, 0.54, 0.07, 0.04, S, axis="Y", verts=10, bevel=0.004, tags=tags)
        # cabo do tambor ate o banco de capacitores
        B.cyl(f"dcable{sx}", x, yb + 0.12, 0.48, 0.035, 0.16, KM, axis="Y", verts=8, tags=tags)
        B.cyl(f"dcabler{sx}", x, yb + 0.12, 0.48, 0.043, 0.024, X["copper"], axis="Y", verts=8, tags=tags)

    # ---------------------------------------------------------------- ombreiras (garras) com bobinas de campo
    z0, z1 = SHOULDER_Z
    for sx in (-1, 1):
        sa, sp = B.shard(f"shoulder{sx}", side(SHOULDER, sx), z0, z1, A, slope=0.08, groove=0.035, panel_h=0.03,
                         tags=tags)
        fa_, fb_ = FCOIL_Y
        cut = B.rpoly(sx * FCOIL_X, (fa_ + fb_) / 2, 0.44, fb_ - fa_ + 0.10, 0, chamfer=0.06)
        for t in (sa, sp):
            if t is not None:
                B.cut(t, [B.loft(f"fc_cut{sx}{t.name}", cut, cut, 0.44, 1.3, K, bevel=0.0)])
        B.loft(f"fc_bed{sx}", cut, cut, 0.435, 0.445, M["black"], bevel=0.0, tags=tags)
        # em repouso o nucleo fica escuro (as frestas so acendem no brilho de carga, antes do tiro)
        coil(f"fcoil{sx}", fa_, fb_, FCOIL_Z, FCOIL_R, M, X, tags, wire=FCOIL_WIRE, x=sx * FCOIL_X, spacing=SPACING)
        for j, y in enumerate((fa_ - 0.015, (fa_ + fb_) / 2, fb_ + 0.015)):
            B.cyl(f"fcband{sx}{j}", sx * FCOIL_X, y, FCOIL_Z, FCOIL_R + 0.012, 0.03, S if j != 1 else KM, axis="Y",
                  verts=10, bevel=0.004, tags=tags)
        # fendas de pips (ponta da garra e lateral) e linhas de painel
        rslot(f"sslot{sx}", sx * 1.30, 1.18, 0.05, 0.40, sx * 31, z1 + 0.03, 0.08, 4, [sa, sp], M, tags)
        rslot(f"sslot2{sx}", sx * 1.48, -0.05, 0.05, 0.40, 0, z1 + 0.03, 0.08, 3, [sa, sp], M, tags)
        if sp is not None:
            B.cut(sp, [B.rbox(f"spl{sx}{k}", sx * x, y, 0.018, ln, z1 - 0.01, 1.3, K, rot=r, bevel=0.0)
                       for k, (x, y, ln, r) in enumerate(((1.45, 0.74, 0.20, sx * 12), (1.12, -0.48, 0.30, 90)))])
        # vao diagonal separando a ponta da garra do corpo da ombreira (le como placas sobrepostas, nao um bloco)
        for t in (sa, sp):
            if t is not None:
                B.cut(t, [B.rbox(f"sgap{sx}{t.name}", sx * 1.25, 0.90, 0.055, 0.95, 0.30, 1.4, K, rot=sx * 74,
                                 bevel=0.0)])
        B.bolts(f"sbolt{sx}", [(sx * 1.10, 0.76), (sx * 1.40, -0.44)], z1 + 0.035, 0.022, S, tags=tags)
        # placa do flanco (degrau) com fenda de pips bem dentro do painel
        fa, fp = B.shard(f"flank{sx}", side(FLANK, sx), 0.40, 0.72, A, slope=0.06, groove=0.03, panel_h=0.025,
                         tags=tags)
        rslot(f"fslot{sx}", sx * 1.27, -0.90, 0.05, 0.26, 90, 0.745, 0.075, 2, [fa, fp], M, tags)
        B.bolts(f"fbolt{sx}", [(sx * 1.12, -1.26)], 0.75, 0.02, S, tags=tags)
        # pistao hidraulico entre a ombreira e o berco
        B.cyl(f"piston{sx}", sx * 0.87, 1.10, 0.66, 0.032, 0.40, S, axis="Y", verts=10, yaw=sx * -5, tags=tags)
        B.cyl(f"pistonb{sx}", sx * 0.88, 0.90, 0.66, 0.052, 0.18, KM, axis="Y", verts=10, yaw=sx * -5, tags=tags)

    # ---------------------------------------------------------------- espinha de dois niveis (sensor + pulso PEM)
    spine = [(-0.24, -1.22), (0.24, -1.22), (0.30, -1.12), (0.30, -0.10), (0.14, 0.30), (-0.14, 0.30),
             (-0.30, -0.10), (-0.30, -1.12)]
    sa, sp = B.shard("spine", spine, 0.42, 1.04, A, slope=0.07, groove=0.03, panel_h=0.025, tags=tags)
    sp2 = [(-0.17, -1.02), (0.17, -1.02), (0.21, -0.94), (0.21, -0.22), (0.08, 0.04), (-0.08, 0.04),
           (-0.21, -0.22), (-0.21, -0.94)]
    s2 = B.plate("spine2", sp2, 1.06, 1.16, A, slope=0.035, tags=tags)
    win = [(-0.10, -0.20), (0.10, -0.20), (0.10, -0.12), (0.035, -0.03), (-0.035, -0.03), (-0.10, -0.12)]
    B.cut(s2, [B.loft("win_cut", win, win, 1.12, 1.5, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 1.115, 1.125, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, -0.12, 0.13, 0.024, 1.12, 1.131, X["lens"], bevel=0.0, tags=tags)
    # pulso PEM num rebaixo em losango (tracos azuis fracos)
    rim = [(-0.15, -0.62), (-0.09, -0.75), (0.09, -0.75), (0.15, -0.62), (0.09, -0.48), (0.0, -0.43),
           (-0.09, -0.48)]
    B.cut(s2, [B.loft("pul_cut", rim, rim, 1.13, 1.5, K, bevel=0.0)])
    B.loft("pul_bed", rim, rim, 1.125, 1.135, M["black"], bevel=0.0, tags=tags)
    pulse = [(-0.115, -0.61), (-0.055, -0.61), (-0.025, -0.51), (0.015, -0.72), (0.055, -0.61), (0.115, -0.61)]
    for i in range(len(pulse) - 1):
        stroke(f"pul{i}", pulse[i], pulse[i + 1], 0.028, 1.135, 1.141, X["glow_dim"], tags)
    B.cut(s2, [B.box("s2l0", 0, -0.90, 0.26, 0.018, 1.13, 1.5, K, bevel=0.0),
               B.box("s2l1", 0, -0.32, 0.26, 0.018, 1.13, 1.5, K, bevel=0.0)])
    if sp is not None:
        B.cut(sp, [B.box(f"spl{sx}", sx * 0.255, -0.62, 0.016, 0.56, 1.05, 1.5, K, bevel=0.0) for sx in (-1, 1)])
    Mo.slot_with_pips("spslot", -1.10, -0.10, 0.10, 0.045, 1.07, 3, M, tags, target=[sa, sp], depth=0.07,
                      vertical=False)

    # ---------------------------------------------------------------- baia de exaustao traseira
    B.box("vent_bay", 0, -1.48, 1.30, 0.30, 0.22, 0.42, M["black"], bevel=0.0, tags=tags)
    for i in range(6):
        B.box(f"louver{i}", 0, -1.60 + i * 0.045, 1.24, 0.02, 0.32, 0.43, KM, bevel=0.004, tags=tags)
    for i in range(6):
        B.box(f"vent_pip{i}", -0.50 + i * 0.20, -1.32, 0.07, 0.026, 0.38, 0.44, X["glow"], bevel=0.0, tags=tags)
    B.box("vent_lip", 0, -1.28, 1.26, 0.025, 0.38, 0.52, M["black"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.plate(f"rearplate{sx}", side([(-0.68, -1.36), (-0.98, -1.36), (-0.98, -1.58), (-0.82, -1.66),
                                        (-0.68, -1.66)], sx), 0.40, 0.60, A, slope=0.04, tags=tags)


# ============================================================================ brilho de carga (charge_glow)
def _arc(name, p, q, k, amp, z, w, mat, tags, rng):
    """Arco eletrico em zigue-zague de p ate q (k segmentos, desvio lateral amp)."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    pts = [p]
    for i in range(1, k):
        t = i / k
        o = rng.uniform(-amp, amp) * math.sin(math.pi * t) ** 0.5
        pts.append((p[0] + dx * t + nx * o, p[1] + dy * t + ny * o))
    pts.append(q)
    for i in range(len(pts) - 1):
        stroke(f"{name}{i}", pts[i], pts[i + 1], w, z, z + 0.01, mat, tags)


def charge_glow(M, T="charge", phase=1.0):
    """So as partes que acendem antes do tiro (emissivas, etiqueta T); no render a cabeca entra como Holdout.
    phase = k/4 (k = 1..4): bobinas de campo, frestas das bobinas da raiz dos canos (dentro do quadro da torre),
    capacitores e eletrodos sobem em rampa; arcos entre os canos nos quadros 3 e 4."""
    tags = (T,)
    X = pem(M)
    f = max(0.0, min(1.0, phase))
    # azul puxado para o anil: misturado ao reflexo do cobre o azul mais ciano saia esverdeado (verde = nuclear)
    gap = B.mat_glow(f"pem_charge_gap{int(f * 100)}", (0.05, 0.36, 1.0), 0.55 + 1.25 * f)
    hot = B.mat_glow(f"pem_charge_hot{int(f * 100)}", (0.25, 0.58, 1.0), 0.6 + 1.0 * f)
    arc = B.mat_glow("pem_charge_arc", (0.50, 0.80, 1.0), 2.4)
    fa_, fb_ = FCOIL_Y
    for sx in (-1, 1):
        # nucleo aceso da bobina de campo (aparece nas frestas; as espiras da cabeca tampam o resto)
        B.cyl(f"cg_fcoil{sx}", sx * FCOIL_X, (fa_ + fb_) / 2, FCOIL_Z, FCOIL_R - FCOIL_WIRE * 1.25, fb_ - fa_ - 0.01,
              gap, axis="Y", verts=12, bevel=0.0, tags=tags)
        for k, (cx, cy) in enumerate(CAPS):
            B.cyl(f"cg_cap{sx}{k}", sx * cx, cy, 0.629, CAP_R * 0.62, 0.012, hot, axis="Z", verts=12, bevel=0.0,
                  tags=tags)
        for k, (ex, ey) in enumerate(ELECTRODES):
            B.cyl(f"cg_el{sx}{k}", sx * (ex + 0.075), ey, 0.80, 0.028, 0.03, hot, axis="X", verts=8, bevel=0.0,
                  tags=tags)
        B.box(f"cg_bus{sx}", sx * 0.64, 0.37, 0.42, 0.018, 0.47, 0.475, gap, bevel=0.0, tags=tags)
    for i in range(4):
        B.box(f"cg_prow{i}", 0, 0.76 + i * 0.15, 0.026, 0.06, 0.918, 0.924, hot, bevel=0.0, tags=tags)
    # bobinas da raiz dos canos que caem dentro do quadro da torre (cano em repouso): nucleo aceso + espiras
    # copiadas como Holdout (etiqueta "head"), entao so as frestas acendem por cima do sprite do cano
    for x in YS:
        for a, b, R in stack_segments():
            ya, yb = ROOT + a, min(ROOT + b, BOX)
            if ya >= BOX - 0.02:
                continue
            B.cyl(f"cg_bc{x}{a}", x, (ya + yb) / 2, ZB, R - WIRE * 1.3, yb - ya, gap, axis="Y", verts=12, bevel=0.0,
                  tags=tags)
            for i, y in enumerate(coil_layout(a, b, WIRE, SPACING)):
                if ROOT + y < BOX + 0.05:
                    turn(f"cg_bt{x}{a}_{i}", x, ROOT + y, ZB, R - WIRE, WIRE, X["copper"], ("head",))
    # arcos entre os canos: dos eletrodos da proa ate as bobinas da raiz (e de cano a cano na frente da proa)
    rng = random.Random(int(round(f * 4)) * 7 + 3)
    if f > 0.6:
        for sx in (-1, 1):
            for k, (ex, ey) in enumerate(ELECTRODES):
                if f < 0.9 and k != 1:
                    continue
                _arc(f"cg_arc{sx}{k}_", (sx * (ex + 0.09), ey), (sx * 0.30, ey + rng.uniform(-0.08, 0.08)), 4, 0.05,
                     1.02, 0.03, arc, tags, rng)
        if f > 0.9:
            _arc("cg_arcX_", (-0.27, 1.88), (0.27, 1.88), 6, 0.07, 1.04, 0.032, arc, tags, rng)


# ============================================================================ cano
def barrel(M, L=2.95, T="barrel", phase=0.0):
    """Cano de 155 mm em pilhas de bobinas acesas, com anel para-raios na boca: raiz em y=0, boca em y=L."""
    tags = (T,)
    hot = (T, "hot")
    X = pem(M)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    gapb = B.mat_glow("pem_gap_stack", (0.08, 0.48, 1.0), 0.55)   # frestas acesas das pilhas de bobinas
    z = ZB
    # culatra escura (no berco) e nucleo escuro continuo
    B.cyl("b_root", 0, 0.21, z, 0.24, 0.42, KM, axis="Y", verts=8, bevel=0.012, tags=tags)
    B.cyl("b_rootring", 0, 0.43, z, 0.25, 0.035, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.box("b_rootslot", 0, 0.21, 0.06, 0.30, z + 0.20, z + 0.24, M["black"], bevel=0.0, tags=tags)
    B.cyl("b_core", 0, 1.50, z, 0.15, 2.10, K, axis="Y", verts=12, tags=tags)
    # pilhas de bobinas: espiras de cobre com frestas azuis acesas, colares claros nas pontas e escuros no meio
    for j, (a, b, R) in enumerate(stack_segments()):
        coil(f"b_coil{j}", a, b, z, R, M, X, hot, wire=WIRE, gap_mat=gapb, spacing=SPACING)
    for i, (a, b, R, n) in enumerate(STACKS):
        seg = (b - a) / n
        for j in range(n + 1):
            B.cyl(f"b_col{i}{j}", 0, a + j * seg, z, R + 0.022, 0.045, A if j in (0, n) else KM, axis="Y", verts=8,
                  bevel=0.006, tags=hot if i == 1 else tags)
    # luvas claras com canal escuro e LEDs azuis
    for i, (a, b, r0, r1) in enumerate(((1.25, 1.71, 0.19, 0.18), (2.33, 2.52, 0.18, 0.175))):
        sl = B.cyl(f"b_sleeve{i}", 0, (a + b) / 2, z, r0, b - a, A, axis="Y", verts=8, bevel=0.008, tags=tags,
                   r2=r1)
        B.cut(sl, [B.box(f"b_chc{i}", 0, (a + b) / 2, 0.05, b - a + 0.1, z + 0.12, z + 0.4, K, bevel=0.0)])
    B.box("b_chbed", 0, 1.48, 0.05, 0.46, z + 0.135, z + 0.15, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"b_chled{i}", 0, 1.34 + i * 0.12, 0.024, 0.05, z + 0.15, z + 0.156, X["glow"], bevel=0.0, tags=tags)
    # boca: cone claro facetado, ANEL PARA-RAIOS largo e duas hastes com ponta de cobre
    m0 = 2.52
    B.cyl("b_muz", 0, (m0 + L - 0.04) / 2, z, 0.19, L - 0.04 - m0, A, axis="Y", verts=8, bevel=0.008, tags=tags,
          r2=0.15)
    mz = B.cyl("b_muzc", 0, L - 0.02, z, 0.15, 0.04, KM, axis="Y", verts=8, bevel=0.004, tags=tags)
    B.cut(mz, [B.box("b_bore_c", 0, L, 0.10, 0.10, z - 0.06, z + 0.4, K, bevel=0.0)])
    ring = [(-0.24, 2.60), (0.24, 2.60), (0.315, 2.65), (0.315, 2.72), (0.24, 2.77), (-0.24, 2.77), (-0.315, 2.72),
            (-0.315, 2.65)]
    rg = B.plate("b_ring", ring, z - 0.05, z + 0.22, A, slope=0.035, tags=hot)
    B.cut(rg, [B.box("b_ringc", 0, 2.685, 0.46, 0.05, z + 0.12, z + 0.5, K, bevel=0.0)])
    B.box("b_ringbed", 0, 2.685, 0.46, 0.05, z + 0.11, z + 0.125, X["copper"], bevel=0.0, tags=hot)
    for sx in (-1, 1):
        # haste do para-raios: da frente do anel ate quase a boca, ponta de cobre afiada
        B.cyl(f"b_rod{sx}", sx * 0.24, 2.83, z + 0.10, 0.022, 0.14, S, axis="Y", verts=8, bevel=0.0, tags=tags)
        B.cyl(f"b_rodtip{sx}", sx * 0.24, 2.92, z + 0.10, 0.026, 0.06, X["copper"], axis="Y", verts=8, bevel=0.0,
              tags=hot, r2=0.006)
    for i in range(2):
        B.box(f"b_muzs{i}", 0, 2.84 + i * 0.05, 0.22, 0.018, z + 0.10, z + 0.20, K, bevel=0.0, tags=tags)


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto padrao do kit (placas verdes, anel, escotilhas e respiros na fileira de tras) com LEDs azuis."""
    pem(M)
    w, h = PART["size"]
    Mo.hull_roof(M, w, h, PART["pivot"], PART["ring_r"], T)


def floor(M, T="floor"):
    """Piso padrao do kit (anel, estantes, 3 postos) com as luzes azuis da familia."""
    from bsgen.common import crew_positions
    pem(M)
    w, h = PART["size"]
    pv = PART["pivot"]
    Mo.hull_floor(M, w, h, pv, PART["ring_r"], crew_positions(w, h, PART["crew"], pv), T)
