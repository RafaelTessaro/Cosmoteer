"""Bateria Pesada de Misseis Quadrupla ("Mula-sem-Cabeca") - lancador 5x6 final, familia do 76 mm.

Mula-sem-Cabeca = a mula sem cabeca que cospe fogo pelo pescoco: corpo largo e blindado SEM cabeca; no lugar
dela um colar blindado aberto (gorjal em lascas que se abrem para a frente) com a garganta escura e uma brasa
MUITO fraca no fundo (pulsa devagar; no overclock vira fogo). O pescoco e uma fileira de vertebras em divisa
correndo entre os casulos ate o colar. Quatro casulos retangulares 3x4 (48 tubos, passo 0.26 x 0.22 na vista
de cima, inclinados 40 graus) em dois pares sobre bracos hidraulicos (pistoes visiveis nos vaos de cada par,
ref. 4 Cyberpunk); garras longas nascem nas ombreiras de tras, correm por fora dos casulos externos e curvam
para dentro na frente; saia blindada em segmentos sobre o anel; atras de cada casulo uma grelha de sopro
(defletor do backblast) e no rabo a baia de exaustao com 6 pips.
Casulos modelados no proprio referencial (face no plano local) e girados, como a Tocandira/Caipora: as bocas
projetadas batem com launcher_layout (centros (+-0.75, 0.9) e (+-1.75, 0.9), tube_r 0.09).
Overclock (turret_oc.png): a garganta do colar vira fogo e as grelhas de sopro dos casulos ficam em brasa.
"""

import math
import os

import bmesh
import bpy

import bs3d as B
import models as Mo

DRAFT = os.environ.get("BS_DRAFT") == "1"     # rascunho: sem os 8 quadros da brasa pulsando

PART = {
    "id": "rafaeltessaro.bs_msl_quad",
    "kind": "launcher",
    "size": [5, 6],
    "pivot": [2.5, 2.6],           # = art.part_meta.pivot do spec
    "turret_box": 4.8,
    "ring_r": 2.0,
    "collider": 2.1,
    "accent": "amber",
    "looks": ["he", "cluster", "limpet", "napalm", "emp", "torpedo", "nuclear"],
    "oc_glow": True,
    "oc_occlude": True,            # o brilho do overclock fica atras das pecas da cabeca (holdout)
    "lights": [
        {"at": [0.0, -2.02], "size": 1.8, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "ripple",
}
if not DRAFT:
    PART["turret_anim"] = {"frames": 8, "interval": 0.15}   # brasa da garganta respirando

PITCH = 40.0
SIN, COS = math.sin(math.radians(PITCH)), math.cos(math.radians(PITCH))
TN = math.tan(math.radians(PITCH))
POD_XS = (-1.75, -0.75, 0.75, 1.75)  # centros projetados das faces (cells.pods[*].center)
POD_Y = 0.9
Z0 = 1.0                             # altura do centro da face
TUBE_R = 0.09
PU = 0.26                            # passo lateral
RV = 0.22 / SIN                      # passo das fileiras no plano da face (0.22 na vista de cima)
# bocas no plano da face (u lateral, v descendo a face = frente na vista de cima): 4 fileiras x 3 colunas
TUBES = [(u, v) for v in (-1.5 * RV, -0.5 * RV, 0.5 * RV, 1.5 * RV) for u in (-PU, 0.0, PU)]
HWO = 0.43                           # meia largura externa do casulo
HW = 0.385                           # abertura da moldura (lados)
VT, VB = -0.80, 0.76                 # bordas de cima / de baixo da face (plano da face)
VTI, VBI = -0.70, 0.66               # abertura da moldura (a aba de cima fica longe da fileira de tras)
POD_L = 1.45                         # comprimento do casulo ao longo do eixo
VENT_Y = -POD_L + 0.30               # grelha de sopro no topo do casulo (referencial do eixo)
ZT = -VT - 0.025                     # topo do corpo do casulo (referencial do eixo)
CH = 0.10                            # chanfro das quinas de cima do casulo

BAND = {"he": (0.80, 0.327, 0.0), "cluster": (0.80, 0.62, 0.086), "limpet": (0.80, 0.035, 0.024),
        "napalm": (0.80, 0.11, 0.0093), "emp": (0.062, 0.437, 0.80), "torpedo": (0.62, 0.64, 0.70),
        "nuclear": (0.16, 0.80, 0.11)}
BAND_GLOW = {"he": (1.0, 0.473, 0.0), "cluster": (1.0, 0.78, 0.11), "limpet": (1.0, 0.044, 0.03),
             "napalm": (1.0, 0.186, 0.0155), "emp": (0.078, 0.546, 1.0), "torpedo": (0.9, 0.93, 1.0),
             "nuclear": (0.20, 1.0, 0.147)}
EMBER = (1.0, 0.16, 0.02)


# ============================================================================ utilidades
def _cena():
    return set(o.name for o in bpy.context.scene.objects)


def _novos(antes):
    return [o for o in bpy.context.scene.objects if o.name not in antes and o.parent is None]


def _grupo(antes, nome, at, rot):
    """Prende os objetos novos num Empty em 'at' girado por rot (graus XYZ): referencial local."""
    sc = bpy.context.scene
    objs = _novos(antes)
    emp = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(emp)
    for o in objs:
        o.parent = emp
    emp.location = at
    emp.rotation_euler = tuple(math.radians(a) for a in rot)
    return emp


def _pecas(*ts):
    return [t for t in ts if t is not None]


def _lines(target, name, specs, ztop, w=0.016, depth=0.035):
    """Linhas de painel recortadas: specs = [(x, y, comprimento, rotacao)]."""
    if target is None:
        return
    K = bpy.data.materials.get("core")
    B.cut(target, [B.rbox(f"{name}{i}", x, y, w, ln, ztop - depth, ztop + 0.4, K, rot=r, bevel=0.0)
                   for i, (x, y, ln, r) in enumerate(specs)])


def _pitched_cyl(name, x, y, z, r, length, mat, elev, yaw=0.0, verts=12, tags=(), bevel=0.0, r2=None):
    """Cilindro com eixo inclinado: elev graus acima do horizonte, yaw graus a partir de +Y."""
    ob = B.cyl(name, x, y, z, r, length, mat, axis="Y", verts=verts, bevel=bevel, tags=tags, r2=r2)
    ob.rotation_euler = (math.radians(-90 + elev), 0.0, math.radians(yaw))
    return ob


def _hshard(name, poly, pnl, z0, z1, mat, slope=0.02, panel_h=0.02, tags=()):
    """Lasca com painel desenhado a mao (pontas finas: o offset automatico se cruza)."""
    a = B.plate(name, poly, z0, z1, mat, slope=slope, tags=tags)
    b = B.plate(name + "_pnl", pnl, z1 - 0.004, z1 + panel_h, mat, slope=0.01, bevel=0.006, tags=tags)
    return a, b


def _washer(name, x, y, z0, z1, r0, r1, mat, verts=24, tags=()):
    """Arruela (aro) plana: anel entre r0 e r1, sem booleana."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for z in (z0, z1):
        for r in (r0, r1):
            rings.append([bm.verts.new((x + r * math.cos(a), y + r * math.sin(a), z))
                          for a in (i / verts * math.tau for i in range(verts))])
    ib, ob_, it, ot = rings
    for i in range(verts):
        j = (i + 1) % verts
        bm.faces.new((ot[i], ot[j], it[j], it[i]))        # topo
        bm.faces.new((ob_[j], ob_[i], ib[i], ib[j]))      # fundo
        bm.faces.new((ob_[i], ob_[j], ot[j], ot[i]))      # lado de fora
        bm.faces.new((ib[j], ib[i], it[i], it[j]))        # lado de dentro
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    md = o.modifiers.new("bevel", "BEVEL")
    md.width = 0.004
    md.segments = 1
    md.limit_method = "ANGLE"
    o.data.materials.append(mat)
    for t in tags:
        o[t] = True
    return o


def _vcut(name, poly, z0, z1, mat, tilt=TN):
    """Cortador com paredes VERTICAIS no mundo dentro de um referencial inclinado em X por PITCH (topo do
    casulo): o poligono de cima anda dz*tan(pitch) em y (STYLE.md 9, casulos inclinados)."""
    top = [(x, y + (z1 - z0) * tilt) for x, y in poly]
    return B.loft(name, poly, top, z0, z1, mat, bevel=0.0)


def _curve_poly(p0, p1, p2, w0, w1, n=8):
    """Contorno de uma garra curva: Bezier quadratica com meia-largura de w0 (base) a w1 (ponta)."""
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
        dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln, dx / ln
        w = w0 + (w1 - w0) * t
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


# ============================================================================ casulo: face (referencial da face)
def _pod_face(M, tags, i):
    """Face do casulo no plano XY (x direita, y descendo a face = frente na vista de cima, z = para fora).
    Placa escura com 12 bocas VAZIAS (aro de aco), nervuras entre as fileiras, moldura clara em 4 laminas
    (cantos com vao escuro) e 2 dentes para a frente na aba de baixo."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    blk = M["black"]
    vc = (VT + VB) / 2
    vci = (VTI + VBI) / 2
    # corpo escuro ao longo do eixo e fundo preto atras das bocas
    B.plate("pbody", B.rpoly(0, vc, 2 * (HWO - 0.025), (VB - VT) - 0.05, 0, chamfer=CH), -POD_L, -0.03, KM,
            slope=0.0, bevel=0.01, tags=tags)
    B.plate("pback", B.rpoly(0, vci, 2 * HW - 0.02, (VBI - VTI) - 0.02, 0, chamfer=0.03), -0.16, -0.06, blk,
            slope=0.0, bevel=0.0, tags=tags)
    plate = B.plate("pplate", B.rpoly(0, vci, 2 * HW, VBI - VTI, 0, chamfer=0.04), -0.07, 0.0, KM, slope=0.012,
                    bevel=0.006, tags=tags)
    B.cut(plate, [B.cyl(f"pbore{k}", u, v, 0.0, TUBE_R, 0.4, K, axis="Z", verts=24, bevel=0.0)
                  for k, (u, v) in enumerate(TUBES)])
    for k, (u, v) in enumerate(TUBES):
        _washer(f"prim{k}", u, v, -0.006, 0.02, TUBE_R, TUBE_R + 0.016, S, tags=tags)
    # nervuras de aco entre as fileiras
    for k, v in enumerate((-RV, 0.0, RV)):
        B.box(f"prib{k}", 0, v, 2 * (HW - 0.03), 0.024, -0.01, 0.014, S, bevel=0.004, tags=tags)
    # moldura clara em 4 laminas (bisel duplo), vao escuro nos cantos; aba de cima BAIXA (nao cobre as bocas
    # de tras na vista de cima)
    top = [(-HWO + 0.06, VT), (HWO - 0.06, VT), (HWO, VT + 0.05), (HWO, VTI), (-HWO, VTI), (-HWO, VT + 0.05)]
    bot = [(-HWO, VBI), (HWO, VBI), (HWO, VB - 0.05), (HWO - 0.06, VB), (-HWO + 0.06, VB), (-HWO, VB - 0.05)]
    B.shard("pf_top", top, -0.03, 0.022, A, slope=0.02, groove=0.016, panel_h=0.014, tags=tags)
    ba, bp = B.shard("pf_bot", bot, -0.03, 0.05, A, slope=0.02, groove=0.016, panel_h=0.018, tags=tags)
    for s in (-1, 1):
        side = B.rpoly(s * (HW + HWO) / 2, vci, HWO - HW, (VBI - VTI) - 0.07, 0, chamfer=0.0)
        B.plate(f"pf_side{s}", side, -0.03, 0.035, A, slope=0.01, bevel=0.006, tags=tags)
    B.plate("pf_bed", B.rpoly(0, vc, 2 * HWO - 0.02, (VB - VT) - 0.02, 0, chamfer=0.05), -0.05, -0.025, blk,
            slope=0.0, bevel=0.0, tags=tags)
    # entalhes escuros na aba de baixo (entre os dentes) e linha de painel
    _lines(bp, f"pfl{i}", [(s * 0.12, (VBI + VB) / 2, 0.06, 0) for s in (-1, 1)], 0.068, w=0.02, depth=0.03)
    # dois dentes curtos para a frente na aba de baixo
    tooth = [(-0.055, VB - 0.04), (0.055, VB - 0.04), (0.055, VB + 0.04), (0.018, VB + 0.13), (-0.018, VB + 0.13),
             (-0.055, VB + 0.04)]
    for j, s in enumerate((-1, 1)):
        B.shard(f"ptooth{j}", [(x + s * 0.27, y) for x, y in tooth], -0.04, 0.07, A, slope=0.016, groove=0.01,
                panel_h=0.016, tags=tags)


# ============================================================================ casulo: topo (referencial do eixo)
def _louvers(name, y0, n, step, w, th, z0, z1, mat, tags):
    """Venezianas com paredes VERTICAIS no mundo (cisalhadas por tan(pitch)): de cima os vaos entre elas ficam
    abertos (venezianas perpendiculares ao topo inclinado tampavam os proprios vaos na vista de cima)."""
    for k in range(n):
        y = y0 + k * step
        poly = [(-w / 2, y - th / 2), (w / 2, y - th / 2), (w / 2, y + th / 2), (-w / 2, y + th / 2)]
        top = [(x, yy + (z1 - z0) * TN) for x, yy in poly]
        B.loft(f"{name}{k}", poly, top, z0, z1, mat, bevel=0.0, tags=tags)


def _pod_top(M, tags, sx, outer):
    """Blindagem do topo (x direita, y = eixo dos tubos, face em y = 0, z = cima do casulo): 3 lascas em divisa
    (testa, meio com fenda de pips, traseira com grelha de sopro e cantos chanfrados), chanfros laterais."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    L = POD_L
    w = HWO - CH - 0.005
    tp = 0.08                                       # flecha das divisas (ponta para a frente)
    brow = [(-w, -0.30), (0.0, -0.30 + tp), (w, -0.30), (w, -0.08), (w - 0.05, -0.035), (-w + 0.05, -0.035),
            (-w, -0.08)]
    mid = [(-w, -0.66), (0.0, -0.66 + tp), (w, -0.66), (w, -0.34), (0.0, -0.34 + tp), (-w, -0.34)]
    rear = [(-w + 0.13, -L + 0.04), (w - 0.13, -L + 0.04), (w, -L + 0.17), (w, -0.70), (0.0, -0.70 + tp),
            (-w, -0.70), (-w, -L + 0.17)]
    ba, bp = B.shard("ptopb", brow, ZT - 0.02, ZT + 0.05, A, slope=0.03, groove=0.02, panel_h=0.022, tags=tags)
    ma, mp = B.shard("ptopm", mid, ZT - 0.02, ZT + 0.05, A, slope=0.03, groove=0.02, panel_h=0.022, tags=tags)
    ra, rp = B.shard("ptopr", rear, ZT - 0.02, ZT + 0.05, A, slope=0.03, groove=0.022, panel_h=0.022, tags=tags)
    ztop = ZT + 0.072
    # grelha de sopro (paredes verticais no mundo): 4 venezianas com 3 vaos (brasa no overclock)
    gv = [(-0.20, VENT_Y - 0.10), (0.20, VENT_Y - 0.10), (0.20, VENT_Y + 0.10), (-0.20, VENT_Y + 0.10)]
    for t in _pecas(ra, rp):
        B.cut(t, [_vcut(f"pvcut_{t.name}", gv, ztop - 0.11, ztop + 0.3, K)])
    B.box("pvbed", 0, VENT_Y, 0.42, 0.22, ztop - 0.125, ztop - 0.11, M["black"], bevel=0.0, tags=tags)
    _louvers("pvlouv", VENT_Y - 0.075, 4, 0.05, 0.40, 0.016, ztop - 0.115, ztop - 0.07, KM, tags)
    # fenda de 3 pips horizontal na lasca do meio (paredes verticais)
    sl = [(-0.13, -0.53), (0.13, -0.53), (0.13, -0.475), (-0.13, -0.475)]
    for t in _pecas(ma, mp):
        B.cut(t, [_vcut(f"pslot_{t.name}", sl, ztop - 0.07, ztop + 0.3, K)])
    B.box("pslot_bed", 0, -0.5025, 0.28, 0.07, ztop - 0.082, ztop - 0.068, M["black"], bevel=0.0, tags=tags)
    for k in range(3):
        B.box(f"pslot_pip{k}", -0.085 + k * 0.085, -0.5025, 0.045, 0.026, ztop - 0.07, ztop - 0.058, M["glow"],
              bevel=0.0, tags=tags)
    # linhas de painel: diagonais na testa, transversais na traseira
    _lines(bp, "ppl", [(s * 0.19, -0.17, 0.12, s * 35) for s in (-1, 1)], ztop)
    _lines(rp, "pplr", [(0.0, -0.87, 0.40, 90)] + [(s * 0.215, -1.28, 0.12, s * -45) for s in (-1, 1)], ztop)
    # lascas dos chanfros de cima (referencial girado em torno do eixo)
    for k, s in enumerate((-1, 1)):
        antes = _cena()
        wc = CH * math.sqrt(2) - 0.02
        ch = B.rpoly(0, -L / 2 + 0.02, wc, L - 0.16, 0, chamfer=0.03)
        a, p = B.shard(f"pch{k}", ch, -0.01, 0.035, A, slope=0.012, groove=0.012, panel_h=0.014, tags=tags)
        if s == sx and outer:
            # lado de fora dos casulos externos: 3 entalhes escuros (respiros)
            for t in _pecas(a, p):
                B.cut(t, [B.box(f"pchc_{t.name}{j}", 0, -0.36 - j * 0.14, wc * 0.7, 0.035, 0.0, 0.4, K,
                                bevel=0.0) for j in range(3)])
        _grupo(antes, f"pchg{k}", (s * (HWO - CH / 2 - 0.004), 0, ZT - CH / 2 + 0.035), (0, s * 45.0, 0))


def _pod(M, tags, i):
    cx = POD_XS[i]
    sx = -1 if cx < 0 else 1
    antes = _cena()
    _pod_top(M, tags, sx, abs(cx) > 1.0)
    _grupo(antes, f"pod_top{i}", (cx, POD_Y, Z0), (PITCH, 0, 0))
    antes = _cena()
    _pod_face(M, tags, i)
    _grupo(antes, f"pod_face{i}", (cx, POD_Y, Z0), (PITCH - 90.0, 0, 0))


# ============================================================================ corpo
def _arms(M, tags):
    """Bracos hidraulicos: pistao + haste nos vaos de cada par de casulos, munhoes e berco escuro."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    for sx in (-1, 1):
        x = sx * 1.25
        # berco escuro sob o par (aparece no vao)
        B.box(f"cradle{sx}", x, 0.25, 0.10, 1.9, 0.30, 0.42, KM, bevel=0.01, tags=tags)
        # pistao de elevacao: cilindro escuro atras, haste de aco subindo para a frente
        _pitched_cyl(f"pist{sx}", x, -0.30, 0.52, 0.048, 0.70, KM, 21.0, verts=12, bevel=0.006, tags=tags)
        _pitched_cyl(f"pistr{sx}", x, 0.42, 0.80, 0.027, 0.80, S, 21.0, verts=12, tags=tags)
        for k, (y, z) in enumerate(((-0.62, 0.40), (0.0, 0.64))):
            _pitched_cyl(f"pistc{sx}{k}", x, y, z, 0.056, 0.035, S, 21.0, verts=12, tags=tags)
        # munhao (eixo do par) e olhal da haste
        B.cyl(f"trun{sx}", x, -0.50, 0.62, 0.06, 0.13, S, axis="X", verts=12, bevel=0.006, tags=tags)
        B.cyl(f"eye{sx}", x, 0.80, 0.94, 0.045, 0.12, S, axis="X", verts=12, bevel=0.005, tags=tags)
    # pistoes de dentro (vale do pescoco, rentes aos casulos internos)
    for sx in (-1, 1):
        x = sx * 0.335
        _pitched_cyl(f"ipist{sx}", x, -0.40, 0.56, 0.022, 0.60, S, 18.0, verts=10, tags=tags)


def _neck(M, tags):
    """Pescoco: vertebras claras em divisa (ponta para a frente) subindo ate o colar, com cabos escuros."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.box("neck_core", 0, -0.62, 0.44, 2.40, 0.30, 0.50, KM, bevel=0.01, tags=tags)
    for sx in (-1, 1):
        B.cyl(f"cable{sx}", sx * 0.13, -0.60, 0.52, 0.03, 2.30, K, axis="Y", verts=8, tags=tags)
    ys = [-1.84, -1.49, -1.14, -0.79, -0.44, -0.09, 0.26]
    for k, y0 in enumerate(ys):
        w = 0.27 if k < len(ys) - 1 else 0.25
        d = 0.26
        tip = 0.09
        poly = [(-w, y0), (0.0, y0 + tip), (w, y0), (w, y0 + d), (0.0, y0 + d + tip), (-w, y0 + d)]
        z1 = 0.62 + 0.035 * k
        a, p = B.shard(f"vert{k}", poly, 0.40, z1, A, slope=0.03, groove=0.018, panel_h=0.02, tags=tags)
        if k in (1, 3, 5):
            # par de pips em recesso na lateral da vertebra
            for s in (-1, 1):
                Mo.slot_with_pips(f"vslot{k}{s}", s * 0.17, y0 + 0.08, y0 + 0.20, 0.04, z1 + 0.02, 1,
                                  dict(M, glow=M["glow_dim"]), tags, target=_pecas(a, p), depth=0.07)


THROAT = [(-0.16, 0.92), (0.16, 0.92), (0.22, 1.02), (0.22, 1.52), (0.14, 1.66), (-0.14, 1.66), (-0.22, 1.52),
          (-0.22, 1.02)]
NECK_C = (0.0, 1.29)                 # centro do toco do pescoco (aro)


def _collar(M, tags, phase):
    """Colar blindado aberto no lugar da cabeca: gorjal em lascas (2 laterais que se abrem em chifres para a
    frente, arco de tras ligado ao pescoco, labio em divisa na frente), garganta escura funda com o aro do toco,
    palhetas radiais e uma brasa MUITO fraca no fundo (respira devagar)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    blk = M["black"]
    cx, cy = NECK_C
    B.loft("throat_bed", THROAT, THROAT, 0.335, 0.36, blk, bevel=0.0, tags=tags)
    pulse = 0.5 + 0.5 * math.cos(phase * math.tau)
    ember = B.mat_glow("collar_ember", EMBER, 0.06 + 0.06 * pulse)
    B.cyl("throat_ember", cx, cy, 0.362, 0.10, 0.006, ember, axis="Z", verts=8, bevel=0.0, tags=tags)
    # aro do toco (octogono escuro) e palhetas radiais por cima da brasa
    _washer("neck_rim", cx, cy, 0.36, 0.50, 0.105, 0.155, KM, verts=8, tags=tags)
    _washer("neck_rim2", cx, cy, 0.50, 0.52, 0.112, 0.14, S, verts=8, tags=tags)
    for k in range(6):
        a = math.radians(30 + k * 60)
        B.rbox(f"vane{k}", cx + 0.07 * math.cos(a), cy + 0.07 * math.sin(a), 0.085, 0.014, 0.365, 0.44, KM,
               rot=math.degrees(a), bevel=0.0, tags=tags)
    # lascas laterais do gorjal: paralelas aos casulos (|x| <= 0.31) e abrindo em chifres na frente das faces
    side = [(-0.245, 0.80), (-0.31, 0.86), (-0.31, 1.46), (-0.40, 1.58), (-0.60, 1.78), (-0.73, 2.12),
            (-0.62, 2.08), (-0.46, 1.91), (-0.30, 1.77), (-0.245, 1.67)]
    side_pnl = [(-0.27, 0.90), (-0.285, 0.93), (-0.285, 1.45), (-0.38, 1.57), (-0.57, 1.77), (-0.645, 1.96),
                (-0.47, 1.82), (-0.31, 1.70), (-0.27, 1.62)]
    for s, f in ((-1, lambda p: p), (1, Mo.mirror)):
        a, p = _hshard(f"gorget{s}", f(side), f(side_pnl), 0.40, 0.90, A, slope=0.035, panel_h=0.026, tags=tags)
        # fenda de luz fraca no chifre
        bx, by, br = s * 0.52, 1.84, s * -38
        for t in (a, p):
            B.cut(t, [B.rbox(f"gcut{s}{t.name}", bx, by, 0.04, 0.17, 0.86, 1.3, K, rot=br, bevel=0.0)])
        B.rbox(f"gbed{s}", bx, by, 0.04, 0.17, 0.84, 0.86, blk, rot=br, bevel=0.0, tags=tags)
        B.rbox(f"gglow{s}", bx, by, 0.014, 0.12, 0.86, 0.87, M["glow_dim"], rot=br, bevel=0.0, tags=tags)
        _lines(p, f"gpl{s}", [(s * 0.285, 1.20, 0.10, 0)], 0.926, w=0.014)
    # arco de tras (liga o pescoco ao colar) e labio da frente em divisa
    arch = [(-0.22, 0.66), (0.0, 0.73), (0.22, 0.66), (0.235, 0.78), (0.16, 0.89), (-0.16, 0.89), (-0.235, 0.78)]
    B.shard("arch", arch, 0.40, 0.84, A, slope=0.03, groove=0.016, panel_h=0.02, tags=tags)
    lip = [(-0.20, 1.72), (0.20, 1.72), (0.28, 1.82), (0.08, 2.12), (-0.08, 2.12), (-0.28, 1.82)]
    la, lp = B.shard("lip", lip, 0.34, 0.70, A, slope=0.03, groove=0.018, panel_h=0.02, tags=tags)
    _lines(lp, "lpl", [(0.0, 1.93, 0.12, 0)], 0.72, w=0.016)


def _rear(M, tags):
    """Ombreiras de tras em 2 degraus (uma atras de cada casulo; o degrau de cima tem a grelha do defletor de
    sopro no ponto de backblast) e baia de exaustao com 6 pips no rabo."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    blk = M["black"]
    inner = [(-0.33, -0.80), (-0.75, -0.74), (-1.20, -0.80), (-1.20, -1.66), (-0.98, -1.92), (-0.33, -1.92)]
    inner2 = [(-0.41, -0.93), (-0.75, -0.86), (-1.12, -0.93), (-1.12, -1.60), (-0.95, -1.80), (-0.41, -1.80)]
    outer = [(-1.27, -0.80), (-1.75, -0.74), (-2.30, -0.82), (-2.37, -0.92), (-2.37, -1.24), (-1.86, -1.94),
             (-1.27, -1.94)]
    outer2 = [(-1.35, -0.93), (-1.75, -0.86), (-2.22, -0.93), (-2.24, -1.19), (-1.82, -1.80), (-1.35, -1.80)]
    for s, f in ((-1, lambda p: p), (1, Mo.mirror)):
        for nm, poly, poly2, z1, px in (("in", inner, inner2, 0.50, 0.75), ("out", outer, outer2, 0.52, 1.75)):
            B.shard(f"haunch_{nm}{s}", f(poly), 0.30, z1, A, slope=0.04, groove=0.02, panel_h=0.02, tags=tags)
            z2 = z1 + 0.15
            a, p = B.shard(f"haunch2_{nm}{s}", f(poly2), z1 - 0.02, z2, A, slope=0.035, groove=0.022,
                           panel_h=0.024, tags=tags)
            x = s * px
            ztop = z2 + 0.024
            # grelha do defletor de sopro (ponto de backblast em y = -1.3)
            gw, gh = 0.44, 0.34
            for t in _pecas(a, p):
                B.cut(t, [B.box(f"bgc_{t.name}", x, -1.30, gw, gh, ztop - 0.12, ztop + 0.3, K, bevel=0.0)])
            B.box(f"bgbed{nm}{s}", x, -1.30, gw, gh, ztop - 0.13, ztop - 0.115, blk, bevel=0.0, tags=tags)
            for k in range(5):
                B.box(f"bglouv{nm}{s}{k}", x, -1.42 + k * 0.06, gw - 0.02, 0.02, ztop - 0.12, ztop - 0.06, KM,
                      bevel=0.0, tags=tags)
            B.bolts(f"hb{nm}{s}", [(x - 0.30, -1.70), (x + 0.30, -1.70)] if nm == "in" else
                    [(x + s * 0.40, -0.98), (x - s * 0.30, -1.70)], z2 + 0.02, 0.02, S, tags=tags)
            if nm == "out":
                Mo.slot_with_pips(f"hslot{nm}{s}", s * 2.12, -1.12, -0.96, 0.05, ztop, 2, M, tags,
                                  target=_pecas(a, p), depth=0.07)
                _lines(p, f"hpl{nm}{s}", [(s * 1.58, -1.66, 0.16, s * 50), (s * 1.75, -1.02, 0.30, 90)], ztop)
            else:
                # fenda horizontal (vertical=False: x da funcao = y da fenda, y0..y1 = faixa em x)
                Mo.slot_with_pips(f"hslot{nm}{s}", -1.62, x - 0.11, x + 0.11, 0.045, ztop, 2, M, tags,
                                  target=_pecas(a, p), depth=0.07, vertical=False)
                _lines(p, f"hpl{nm}{s}", [(x, -1.02, 0.30, 90)], ztop)
    # baia de exaustao no rabo: venezianas + 6 pips ambar
    B.box("vent_bay", 0, -2.08, 0.62, 0.34, 0.20, 0.40, blk, bevel=0.0, tags=tags)
    for k in range(6):
        B.box(f"louver{k}", 0, -2.21 + k * 0.05, 0.60, 0.02, 0.34, 0.42, KM, bevel=0.004, tags=tags)
    for k in range(6):
        B.box(f"vent_pip{k}", -0.25 + k * 0.10, -1.93, 0.05, 0.026, 0.38, 0.44, M["glow"], bevel=0.0, tags=tags)
    tail = [(-0.31, -2.26), (0.31, -2.26), (0.24, -2.36), (-0.24, -2.36)]
    B.plate("tail", tail, 0.30, 0.46, AM, slope=0.02, bevel=0.008, tags=tags)
    B.bolts("tbolt", [(x, -2.31) for x in (-0.16, 0.16)], 0.47, 0.02, S, tags=tags)


def _claws(M, tags):
    """Garras longas: nascem nas ombreiras de tras, correm por fora dos casulos externos e curvam para dentro na
    frente em gancho (painel a mao, fenda de luz fraca perto da ponta)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    claw = [(-2.18, -0.72), (-2.30, -0.80), (-2.37, -0.66), (-2.37, 0.50), (-2.33, 1.15), (-2.22, 1.62),
            (-2.04, 2.00), (-1.80, 2.28), (-1.64, 2.31), (-1.71, 2.22), (-1.88, 1.98), (-2.02, 1.62),
            (-2.13, 1.18), (-2.20, 0.50)]
    pnl = [(-2.225, -0.56), (-2.335, -0.60), (-2.335, 0.50), (-2.295, 1.13), (-2.19, 1.59), (-2.02, 1.94),
           (-1.86, 2.13), (-1.91, 1.96), (-2.05, 1.60), (-2.16, 1.16), (-2.23, 0.50)]
    for s, f in ((-1, lambda p: p), (1, Mo.mirror)):
        a, p = _hshard(f"claw{s}", f(claw), f(pnl), 0.30, 0.60, A, slope=0.025, panel_h=0.024, tags=tags)
        bx, by, br = s * 2.11, 1.62, s * -22
        for t in (a, p):
            B.cut(t, [B.rbox(f"ccut{s}{t.name}", bx, by, 0.045, 0.26, 0.54, 0.9, K, rot=br, bevel=0.0)])
        B.rbox(f"cbed{s}", bx, by, 0.045, 0.26, 0.52, 0.545, M["black"], rot=br, bevel=0.0, tags=tags)
        B.rbox(f"cglow{s}", bx, by, 0.016, 0.19, 0.545, 0.555, M["glow_dim"], rot=br, bevel=0.0, tags=tags)
        _lines(p, f"cpl{s}", [(s * 2.285, y, 0.10, 0) for y in (-0.20, 0.30, 0.80)], 0.624, w=0.014)


def _skirt(M, tags):
    """Saia blindada sobre o anel: segmentos retos (sem circulo) com vaos escuros e um parafuso cada."""
    A, S = M["armor"], M["steel"]
    r0, r1 = 1.80, 2.22
    n = 24
    for k in range(n):
        a0 = (k + 0.5) / n * math.tau
        a1 = (k + 1.5) / n * math.tau
        g = 0.025 / r1
        pts = [(r0 * math.cos(a0 + g * 1.3), r0 * math.sin(a0 + g * 1.3)), (r1 * math.cos(a0 + g), r1 * math.sin(a0 + g)),
               (r1 * math.cos(a1 - g), r1 * math.sin(a1 - g)), (r0 * math.cos(a1 - g * 1.3), r0 * math.sin(a1 - g * 1.3))]
        # so os segmentos da frente aparecem (o resto fica sob os casulos e ombreiras)
        am = (a0 + a1) / 2
        if math.sin(am) < 0.55:
            continue
        B.shard(f"skirt{k}", pts, 0.10, 0.26, A, slope=0.03, groove=0.018, panel_h=0.016, tags=tags)
        B.bolts(f"skb{k}", [((r0 + r1) / 2 * math.cos(am), (r0 + r1) / 2 * math.sin(am))], 0.295, 0.018, S,
                tags=tags)


def head(M, T="head", phase=0.0):
    """Corpo da mula (camada roof_doodads): anel, saia, nucleo, ombreiras, pescoco, colar, garras, bracos e os
    4 casulos inclinados com as bocas VAZIAS."""
    tags = (T,)
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    rr = PART["ring_r"]
    B.cyl("ring", 0, 0, 0.04, rr + 0.02, 0.08, KM, axis="Z", verts=96, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, rr - 0.07, 36, 0.09), 0.09, 0.022, S, tags=tags)
    core = [(-1.0, -2.30), (1.0, -2.30), (2.30, -1.10), (2.30, 1.0), (1.3, 1.85), (-1.3, 1.85), (-2.30, 1.0),
            (-2.30, -1.10)]
    B.plate("core", core, 0.06, 0.34, K, slope=0.05, tags=tags)
    _skirt(M, tags)
    _rear(M, tags)
    _neck(M, tags)
    _collar(M, tags, phase)
    _claws(M, tags)
    _arms(M, tags)
    for i in range(4):
        _pod(M, tags, i)


# ============================================================================ narizes (sobreposicoes do rack)
def _band_mat(look):
    """Faixa do nariz: TINTA na cor do missil com uma emissao fraca (nao apaga na sombra)."""
    name = f"band_{look}"
    m = B.mat_metal(name, BAND[look], rough=0.65, metal=0.0)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.0
    b.inputs["Emission Color"].default_value = (*BAND_GLOW[look], 1)
    b.inputs["Emission Strength"].default_value = 0.12
    m["bs_glow"] = 0.12
    return m


def _nose_paint(name, color):
    return B.mat_paint(name, color, rough=0.3, metal=0.15, wear=0.08, grime=0.02, scale=6)


def _lathe(name, prof, mat, tags, verts=24, sy=1.0):
    """Solido de revolucao no eixo Z (perfil [(raio, z)], raio 0 = ponta); sy estica o eixo Y local."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r < 1e-5:
            rings.append([bm.verts.new((0.0, 0.0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a) * sy, z))
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


def _ogive(R, L, z0, tip_r=0.016):
    """Perfil de ogiva tangente (raio R, comprimento L) a partir de z0; para no raio da ponta de aco."""
    rho = (R * R + L * L) / (2 * R)
    prof = []
    for k in range(13):
        xt = L * (1 - k / 12)
        r = math.sqrt(max(0.0, rho * rho - (L - xt) ** 2)) + R - rho
        if r < tip_r:
            break
        prof.append((r, z0 + L - xt))
    return prof


def _capsule(name, a, b, h, mat, tags, z0=0.0, nx=28, na=14, p=3.0):
    """Meia capsula deitada no eixo x (comprimento 2a, meia-largura b em y, altura h em z) com base plana em z0:
    o nariz pesado de calibre duplo deitado sobre a fileira. Pontas em superelipse, secao em arco ogival."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    xs = [a * math.sin((-1 + 2 * i / nx) * math.pi / 2) for i in range(nx + 1)]
    rings = []
    for x in xs:
        f = max(0.0, 1 - (abs(x) / a) ** p) ** (1 / p)
        if f < 1e-4:
            rings.append([bm.verts.new((x, 0.0, z0))])
            continue
        ring = []
        for j in range(na + 1):
            t = math.pi * j / na
            yy, zz = math.cos(t), math.sin(t)
            zz = zz ** 0.8                      # arco levemente ogival (crista)
            ring.append(bm.verts.new((x, b * f * yy, z0 + h * f * zz)))
        rings.append(ring)
    for ra, rb in zip(rings, rings[1:]):
        if len(ra) == 1:
            for j in range(na):
                bm.faces.new((ra[0], rb[j + 1], rb[j]))
        elif len(rb) == 1:
            for j in range(na):
                bm.faces.new((ra[j], ra[j + 1], rb[0]))
        else:
            for j in range(na):
                bm.faces.new((ra[j], ra[j + 1], rb[j + 1], rb[j]))
    # base plana: lado y+ (j = 0) de tras para a frente e lado y- (j = na) de volta; pontas sao vertices unicos
    base = [r[0] for r in rings] + [r[-1] for r in reversed(rings[1:-1])]
    bf = bm.faces.new(base)
    bf.smooth = False
    for f in bm.faces:
        if f is not bf:
            f.smooth = True
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


def _stadium(cx, cy, a, b, n=10):
    """Contorno de estadio (retangulo com pontas em meio circulo) deitado em x."""
    pts = []
    r = b
    for k in range(n + 1):
        t = -math.pi / 2 + math.pi * k / n
        pts.append((cx + (a - r) + r * math.cos(t), cy + r * math.sin(t)))
    for k in range(n + 1):
        t = math.pi / 2 + math.pi * k / n
        pts.append((cx - (a - r) + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def cell(M, look, T="cell", form="tube", box=None):
    """UM nariz carregado (origem = centro da boca / da fileira / da face no plano da face), eixo inclinado
    como o casulo. tube: anel na cor do missil + ogiva clara; heavy: capsula de calibre duplo deitada sobre a
    fileira de 3 tubos; torpedo: ogiva grande tampando a face do casulo."""
    tags = (T,)
    band = _band_mat(look)
    antes = _cena()
    if form == "torpedo":
        _torpedo(M, tags, band, box, look)
    elif form == "heavy":
        _heavy(M, tags, band, box, look)
    elif form == "tube":
        _tube_nose(M, tags, band, look)
    else:
        raise NotImplementedError(f"bs_msl_quad: forma {form} nao existe")
    _grupo(antes, "nose", (0, 0, 0), (PITCH - 90.0, 0, 0))


def _tube_nose(M, tags, band, look):
    nose = _nose_paint("nose", (0.64, 0.65, 0.66))
    R, L = 0.068, 0.165
    z0, zb = 0.022, 0.058
    B.cyl("n_band", 0, 0, (z0 + zb) / 2, 0.075, zb - z0, band, axis="Z", verts=24, bevel=0.0, tags=tags)
    prof = _ogive(R, L, zb)
    rt, zt = prof[-1]
    _lathe("n_ogive", prof + [(0.0, zt + 0.002)], nose, tags)
    B.cyl("n_tip", 0, 0, (zt + zb + L) / 2, rt, zb + L - zt, M["core"], axis="Z", verts=12, bevel=0.0, tags=tags,
          r2=0.002)


def _heavy(M, tags, band, box, look):
    """Capsula pesada (Piranha / Carrapato / Taturana / Poraque): aro na cor do missil na base, corpo claro
    (ou pintado) deitado na fileira, detalhe por tipo."""
    bw, bd = (box or [0.70, 0.21])
    a = bw / 2 - 0.035                  # meio comprimento (lateral)
    b = min(0.105, bd / 2 / SIN * 0.62)  # meia largura no plano da face
    h = 0.085
    body_col = {"cluster": BAND["cluster"], "napalm": (0.87, 0.16, 0.012)}.get(look, (0.64, 0.65, 0.66))
    body = _nose_paint(f"heavy_{look}", body_col)
    # aro (faixa) na base, um pouco maior que a capsula
    rim = _stadium(0, 0, a + 0.022, b + 0.020)
    B.loft("h_rim", rim, rim, 0.0, 0.020, band if look != "napalm" else M["steel"], bevel=0.0, tags=tags)
    cap = _capsule("h_cap", a, b, h, body, tags, z0=0.016)
    if look == "cluster":
        # submunicoes: 2 costuras escuras dividem a capsula em 3 gomos (um por tubo)
        B.cut(cap, [B.box(f"h_seam{k}", s * PU / 2, 0, 0.014, 0.4, 0.03, 0.4, M["core"], bevel=0.0)
                    for k, s in enumerate((-1, 1))])
    elif look == "limpet":
        # presilhas de aco atravessando a capsula
        for k, s in enumerate((-1, 0, 1)):
            B.box(f"h_clamp{k}", s * 0.20, 0, 0.026, 2 * b + 0.05, 0.0, h * 0.85 + 0.02, M["steel"], bevel=0.004,
                  tags=tags)
    elif look == "emp":
        # bobinas: 2 aneis azuis perto das pontas
        for k, s in enumerate((-1, 1)):
            B.box(f"h_coil{k}", s * (a - 0.10), 0, 0.03, 2 * b + 0.03, 0.0, h * 0.8 + 0.02, band, bevel=0.003,
                  tags=tags)
            B.box(f"h_coil2{k}", s * (a - 0.15), 0, 0.016, 2 * b + 0.02, 0.0, h * 0.75 + 0.02, M["steel"],
                  bevel=0.002, tags=tags)
    # buscador escuro no meio da crista
    B.box("h_seek", 0, 0, 0.07, 0.022, 0.016 + h - 0.006, 0.016 + h + 0.006, M["core"], bevel=0.0, tags=tags)


def _torpedo(M, tags, band, box, look):
    """Torpedo (Boto) / Iara: cassete escuro tampando a face, ogiva grande clara com costuras, aro fino na cor
    (branco no Boto, verde na Iara) e buscador escuro com bico de aco."""
    white = _nose_paint("torp_white", (0.53, 0.555, 0.60))
    bw, bd = (box or [0.70, 0.84])
    hw, hh = bw / 2, bd / 2 / SIN
    B.plate("t_collar", B.rpoly(0, 0, 2 * hw + 0.02, 2 * hh - 0.02, 0, chamfer=0.07), 0.0, 0.045, M["core_mid"],
            slope=0.015, bevel=0.008, tags=tags)
    for k, (u, v) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        B.box(f"t_lug{k}", u * (hw - 0.05), v * (hh - 0.08), 0.05, 0.09, 0.04, 0.072, M["steel"], bevel=0.006,
              tags=tags)
    R, L, zb = hw - 0.08, 0.44, 0.04
    sy = min(1.75, (hh - 0.10) / R)
    rho = (R * R + L * L) / (2 * R)
    full = []
    for k in range(25):
        dz = L * k / 24
        full.append((max(0.0, math.sqrt(max(0.0, rho * rho - dz * dz)) + R - rho), zb + dz))
    cut_i = next(i for i, (r, z) in enumerate(full) if r < 0.07)
    prof, tip = full[:cut_i], full[cut_i - 1:]
    ring_m = band
    _lathe("t_ring", [(R + 0.025, 0.03), (R + 0.025, zb + 0.008), (0.0, zb + 0.008)], ring_m, tags, verts=32, sy=sy)
    rt, zt = prof[-1]
    og = _lathe("t_nose", prof + [(0.0, zt)], white, tags, verts=32, sy=sy)

    def r_at(z):
        for (ra, za), (rb, zb_) in zip(prof, prof[1:]):
            if za <= z <= zb_:
                return ra + (rb - ra) * (z - za) / (zb_ - za)
        return prof[-1][0]
    # 2 linhas de painel curtas no lado que olha para a camera (-y local)
    za, zc = zb + 0.05, zb + 0.15
    cuts = []
    for k, x in enumerate((-0.08, 0.08)):
        y_in = -sy * math.sqrt(max(r_at(zc) ** 2 - x * x, 0.0)) + 0.014
        cuts.append(B.box(f"t_pl{k}", x, (-1.0 + y_in) / 2, 0.016, 1.0 + y_in, za, zc, M["core"], bevel=0.0))
    B.cut(og, cuts)
    for k, f in enumerate((0.30, 0.60)):
        z_s = zb + L * f
        r_s = r_at(z_s)
        _lathe(f"t_seam{k}", [(r_s + 0.004, z_s - 0.006), (r_s + 0.004, z_s + 0.006), (0.0, z_s + 0.006)], M["core"],
               tags, verts=32, sy=sy)
    if look == "nuclear":
        # Iara: faixa verde fina a meia altura da ogiva
        z_s = zb + L * 0.45
        r_s = r_at(z_s)
        _lathe("t_nband", [(r_s + 0.006, z_s - 0.012), (r_s + 0.006, z_s + 0.012), (0.0, z_s + 0.012)], band, tags,
               verts=32, sy=sy)
    _lathe("t_seek", [(rt + 0.005, zt - 0.010), (rt + 0.005, zt + 0.002), (0.0, zt + 0.002)], M["core"], tags,
           verts=24, sy=sy)
    _lathe("t_tip", [(r, z + 0.002) for r, z in tip[:-1]] + [(0.0, tip[-1][1] + 0.002)], M["steel"], tags,
           verts=24, sy=sy)


def shutter(M, T="shutter", box=None):
    """Persiana blindada fechada sobre a face de um casulo externo (modo nuclear): 4 laminas claras com bisel
    duplo (uma por fileira), vaos escuros, emenda vertical das 2 portas e fecho de aco."""
    tags = (T,)
    A, KM, S, K = M["armor"], M["core_mid"], M["steel"], M["core"]
    bw, bd = (box or [0.70, 0.84])
    hw = HW + 0.005
    antes = _cena()
    v0, v1 = VTI + 0.01, VBI - 0.005
    B.plate("s_back", B.rpoly(0, (v0 + v1) / 2, 2 * hw, v1 - v0, 0, chamfer=0.03), 0.0, 0.02, KM, slope=0.0,
            bevel=0.004, tags=tags)
    n = 4
    step = (v1 - v0) / n
    for k in range(n):
        vc = v0 + step * (k + 0.5)
        for s in (-1, 1):
            poly = B.rpoly(s * (hw / 2 + 0.006), vc, hw - 0.022, step - 0.035, 0, chamfer=0.03)
            a, p = B.shard(f"s_slat{k}{s}", poly, 0.015, 0.045, A, slope=0.012, groove=0.012, panel_h=0.012,
                           tags=tags)
    # fecho central de aco e 2 parafusos por porta
    B.box("s_lock", 0, (v0 + v1) / 2, 0.05, 0.16, 0.04, 0.07, S, bevel=0.006, tags=tags)
    B.bolts("s_bolt", [(s * (hw - 0.05), v) for s in (-1, 1) for v in (v0 + 0.06, v1 - 0.06)], 0.06, 0.014, S,
            tags=tags)
    _grupo(antes, "shut", (0, 0, 0), (PITCH - 90.0, 0, 0))


# ============================================================================ overclock
def oc_glow(M, T="oc"):
    """So o que brilha no overclock: a garganta do colar em fogo e as grelhas de sopro dos 4 casulos em brasa.
    Forcas baixas (acima de ~1.5 o laranja vira amarelo)."""
    tags = (T,)
    fire = B.mat_glow("oc_fire", (1.0, 0.16, 0.012), 1.4)
    vent_oc = B.mat_glow("oc_vent", (1.0, 0.18, 0.02), 0.9)
    # garganta em fogo (a cabeca entra como holdout: palhetas e aro tampam o fogo onde ficam por cima)
    core_e = B.offset_poly(THROAT, 0.02)
    B.loft("oc_throat", core_e, core_e, 0.366, 0.372, fire, bevel=0.0, tags=tags)
    for i, cx in enumerate(POD_XS):
        antes = _cena()
        ztop = ZT + 0.072
        for k in range(3):
            y = VENT_Y - 0.05 + k * 0.05
            B.box(f"oc_pv{i}{k}", 0, y, 0.38, 0.026, ztop - 0.104, ztop - 0.094, vent_oc, bevel=0.0, tags=tags)
        _grupo(antes, f"oc_pod{i}", (cx, POD_Y, Z0), (PITCH, 0, 0))


# ============================================================================ casco
def floor(M, T="floor"):
    """Piso padrao (anel, 8 postos atras, estantes) + bercos com misseis pesados nos cantos e nas laterais."""
    from bsgen.common import crew_positions
    tags = (T,)
    w, h = PART["size"]
    pv = PART["pivot"]
    rr = PART["ring_r"]
    crew = crew_positions(w, h, 8, pv)
    Mo.hull_floor(M, w, h, pv, rr, crew, T)
    AM, KM = M["armor_mid"], M["core_mid"]
    nose = _nose_paint("nose", (0.74, 0.75, 0.76))
    for i, (cx, cy, rot) in enumerate(((-2.0, 2.45, -30), (2.0, 2.45, 30), (-2.12, -1.25, 0), (2.12, -1.25, 0))):
        a = math.radians(rot)
        ux, uy = -math.sin(a), math.cos(a)
        vx, vy = math.cos(a), math.sin(a)
        B.rbox(f"cradle{i}", cx, cy, 0.62, 0.50, 0.0, 0.07, AM, rot=rot, chamfer=0.06, bevel=0.01, tags=tags)
        for k in (-1, 0, 1):
            tx, ty = cx + vx * k * 0.18, cy + vy * k * 0.18
            B.cyl(f"ctube{i}{k}", tx - ux * 0.04, ty - uy * 0.04, 0.14, 0.07, 0.36, KM, axis="Y", verts=12,
                  yaw=rot, tags=tags)
            B.cyl(f"cnose{i}{k}", tx + ux * 0.19, ty + uy * 0.19, 0.14, 0.065, 0.10, nose, axis="Y", verts=12,
                  yaw=rot, r2=0.014, tags=tags)
            B.cyl(f"cband{i}{k}", tx + ux * 0.13, ty + uy * 0.13, 0.14, 0.074, 0.025, M["ember"], axis="Y",
                  verts=12, yaw=rot, bevel=0.0, tags=tags)
