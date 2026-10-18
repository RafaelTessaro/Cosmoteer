"""Bateria Pesada de Misseis Quadrupla ("Mula-sem-Cabeca") - lancador 5x6 final, familia do 76 mm.

Mula-sem-Cabeca = a mula sem cabeca que cospe fogo pelo pescoco: corpo largo e blindado SEM cabeca; no lugar
dela o toco do pescoco aberto: aro blindado octogonal em segmentos que desce em degraus escuros ate um poco
preto com uma brasa MUITO fraca no fundo (respira devagar; no overclock vira fogo), abracado por um gorjal em
2 ferraduras facetadas abertas para a frente (chifre com crista em cada uma) e um queixo baixo. O pescoco e uma
espinha de 5 vertebras em divisa (tons alternados, janela de sensor, pips em recesso) que afina ate o colar.
Quatro casulos retangulares 3x4 (48 tubos, passo 0.26 x 0.22 na vista de cima, inclinados 40 graus) em dois
pares sobre bracos hidraulicos (arietes cromados no vao de cada par e na faixa escura da raiz, ref. 4
Cyberpunk); garras curtas saem de baixo das ombreiras e agarram a raiz de cada casulo (as de fora mais longas);
garras longas em foice com quebra de faceta correm por fora dos casulos externos; saia blindada em divisa
sobre o anel; ombreiras de tras em cunha (as de dentro chanfradas para a espinha, as de fora em barbatana
varrida para tras com entalhe), cada uma com a grelha do defletor de sopro no ponto de backblast; no rabo a
baia de exaustao com 6 pips.
Casulos modelados no proprio referencial (face no plano local) e girados, como a Tocandira/Caipora: as bocas
projetadas batem com launcher_layout (centros (+-0.75, 0.9) e (+-1.75, 0.9), tube_r 0.09).
Overclock (turret_oc.png): o fundo do poco do pescoco vira fogo (miolo quente, borda escura), as fendas da
raiz do gorjal acendem e as grelhas de sopro dos casulos ficam em brasa.
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
    PART["turret_anim"] = {"frames": 8, "interval": 0.15}   # brasa do poco respirando

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
VENT_Z = ZT + 0.004                  # fundo da grelha de sopro (acima do corpo escuro)

BAND = {"he": (0.80, 0.327, 0.0), "cluster": (0.80, 0.62, 0.086), "limpet": (0.80, 0.035, 0.024),
        "napalm": (0.80, 0.11, 0.0093), "emp": (0.062, 0.437, 0.80), "torpedo": (0.62, 0.64, 0.70),
        "nuclear": (0.16, 0.80, 0.11)}
BAND_GLOW = {"he": (1.0, 0.473, 0.0), "cluster": (1.0, 0.78, 0.11), "limpet": (1.0, 0.044, 0.03),
             "napalm": (1.0, 0.186, 0.0155), "emp": (0.078, 0.546, 1.0), "torpedo": (0.9, 0.93, 1.0),
             "nuclear": (0.20, 1.0, 0.147)}
EMBER = (1.0, 0.16, 0.02)
NOSE_LIGHT = (0.64, 0.65, 0.66)      # tinta clara dos narizes (todas as formas)

# ---------------------------------------------------------------------------- poligonos (cabeca)
# toco do pescoco (colar): centro, apotemas do aro e do poco
NECK_C = (0.0, 1.82)
R1_AP, R1_IN = 0.32, 0.25            # aro blindado (fora / furo)
# gorjal (lado direito): ferradura facetada que abraca o aro (vao de ~0.05), aberta para a frente, terminando num
# chifre que aponta para a frente; entalhe em degrau na lateral; a crista (3o degrau) cobre a metade da frente
GORGET = [(0.188, 1.467), (0.346, 1.620), (0.400, 1.820), (0.346, 2.020), (0.188, 2.173), (0.31, 2.30), (0.47, 2.37),
          (0.66, 2.15), (0.71, 1.97), (0.71, 1.86), (0.665, 1.80), (0.70, 1.74), (0.62, 1.56), (0.48, 1.45),
          (0.30, 1.405)]
GORGET_CREST = [(0.29, 2.17), (0.40, 2.06), (0.455, 1.87), (0.62, 1.87), (0.62, 1.98), (0.565, 2.14), (0.43, 2.27)]
GSLIT = (0.49, 1.59, -52)            # fenda de luz fraca na metade de tras (x, y, giro)
ARCH = [(-0.22, 1.00), (0.0, 1.08), (0.22, 1.00), (0.22, 1.40), (0.15, 1.45), (-0.15, 1.45), (-0.22, 1.40)]
CHIN = [(-0.10, 2.15), (0.10, 2.15), (0.10, 2.26), (0.0, 2.33), (-0.10, 2.26)]
# ombreiras de tras (lado esquerdo; o direito e o espelho)
IN_H = [(-0.355, -0.97), (-0.75, -0.90), (-1.18, -0.97), (-1.18, -1.50), (-1.06, -1.66), (-0.70, -1.80),
        (-0.355, -1.95)]
IN_H2 = [(-0.43, -1.075), (-0.75, -1.015), (-1.10, -1.075), (-1.10, -1.47), (-1.00, -1.58), (-0.43, -1.80)]
OUT_H = [(-1.31, -0.97), (-1.75, -0.90), (-2.20, -0.96), (-2.30, -1.06), (-2.30, -1.36), (-2.06, -1.80),
         (-1.92, -1.78), (-1.84, -1.66), (-1.62, -1.66), (-1.54, -1.74), (-1.31, -1.74)]
OUT_H2 = [(-1.39, -1.075), (-1.75, -1.015), (-2.12, -1.065), (-2.20, -1.14), (-2.20, -1.38), (-2.00, -1.70),
          (-1.92, -1.60), (-1.39, -1.58)]
# garra longa em foice (lado esquerdo): quebra de faceta (entalhe) a 1/3 e ponta em gancho
SICKLE = [(-2.20, -1.02), (-2.30, -1.10), (-2.365, -0.98), (-2.365, 0.40), (-2.335, 1.08), (-2.24, 1.60),
          (-2.04, 2.00), (-1.78, 2.27), (-1.50, 2.355), (-1.57, 2.27), (-1.70, 2.17), (-1.86, 2.00), (-1.98, 1.76),
          (-2.08, 1.46), (-2.15, 1.10), (-2.17, 0.62), (-2.235, 0.52), (-2.235, 0.22), (-2.20, 0.12)]
SICKLE_PNL = [(-2.228, -0.88), (-2.335, -0.93), (-2.335, 0.40), (-2.306, 1.07), (-2.214, 1.585), (-2.02, 1.97),
              (-1.79, 2.21), (-1.64, 2.265), (-1.722, 2.191), (-1.884, 2.018), (-2.007, 1.773), (-2.109, 1.466),
              (-2.179, 1.103), (-2.198, 0.67), (-2.262, 0.565), (-2.262, 0.195), (-2.228, 0.13)]
# saia blindada em divisa (lado esquerdo), a ponta de dentro passa por baixo do gorjal
SKIRT = [(-0.64, 1.74), (-1.34, 1.60), (-1.50, 1.62), (-1.56, 1.70), (-1.16, 1.98), (-0.98, 2.04), (-0.66, 1.98)]


def _root_claw(tip_y, hook=True):
    """Garra da raiz do casulo (referencial do topo, lado +x): nasce embaixo da ombreira, cruza a faixa escura
    da raiz e sobe pela quina do casulo; hook = ponta em gancho para dentro (agarra), senao reta (varrida).
    Devolve (contorno, painel)."""
    if hook:
        ox, tx, ix = 0.43, 0.31, 0.335
    else:
        ox, tx, ix = 0.446, 0.42, 0.37
    oy, iy = tip_y - 0.20, tip_y - 0.22
    poly = [(0.22, -1.80), (0.44, -1.80), (0.448, -1.38), (ox, oy), (tx, tip_y), (ix, iy), (0.295, -1.38),
            (0.22, -1.48)]
    yp = tip_y - 0.12
    xo = tx + (ox - tx) * (yp - tip_y) / (oy - tip_y)
    xi = tx + (ix - tx) * (yp - tip_y) / (iy - tip_y)
    pnl = [(0.25, -1.70), (0.418, -1.70), (0.424, -1.39), (ox - 0.024, oy - 0.02), ((xo + xi) / 2, yp),
           (ix + 0.024, iy - 0.04), (0.318, -1.39), (0.25, -1.50)]
    return poly, pnl


def _octagon(cx, cy, ap):
    """Octogono regular com lados retos para a frente, para tras e para os lados (ap = apotema)."""
    s = 2 * ap
    return B.rpoly(cx, cy, s, s, 0, chamfer=s / (2 + math.sqrt(2)))


THROAT = _octagon(NECK_C[0], NECK_C[1], 0.43)    # caixa escura do colar (embaixo do aro e do gorjal)


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


def _washer(name, x, y, z0, z1, r0, r1, mat, verts=24, tags=(), a0=0.0):
    """Arruela (aro) plana: anel entre r0 e r1 (raios dos vertices, a0 = giro), sem booleana."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for z in (z0, z1):
        for r in (r0, r1):
            rings.append([bm.verts.new((x + r * math.cos(a), y + r * math.sin(a), z))
                          for a in (a0 + i / verts * math.tau for i in range(verts))])
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
    # dois dentes curtos de aco para a frente na aba de baixo (claros pareciam narizes de missil)
    tooth = [(-0.05, VB - 0.04), (0.05, VB - 0.04), (0.05, VB + 0.03), (0.016, VB + 0.085), (-0.016, VB + 0.085),
             (-0.05, VB + 0.03)]
    for j, s in enumerate((-1, 1)):
        B.plate(f"ptooth{j}", [(x + s * 0.27, y) for x, y in tooth], -0.04, 0.06, S, slope=0.014, bevel=0.005,
                tags=tags)


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
    (testa, meio com fenda de pips, traseira com grelha de sopro e cantos chanfrados), chanfros laterais e as 2
    garras da raiz (saem de baixo da ombreira; nos casulos de fora sao mais longas e a de fora abre para fora)."""
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
    # o fundo fica logo acima do topo do corpo (ZT): mais fundo, o corpo escuro tampava a grelha e a brasa
    gv = [(-0.20, VENT_Y - 0.10), (0.20, VENT_Y - 0.10), (0.20, VENT_Y + 0.10), (-0.20, VENT_Y + 0.10)]
    for t in _pecas(ra, rp):
        B.cut(t, [_vcut(f"pvcut_{t.name}", gv, VENT_Z, ztop + 0.3, K)])
    B.box("pvbed", 0, VENT_Y, 0.42, 0.22, ZT - 0.004, VENT_Z, M["black"], bevel=0.0, tags=tags)
    _louvers("pvlouv", VENT_Y - 0.075, 4, 0.05, 0.40, 0.016, VENT_Z - 0.002, VENT_Z + 0.042, KM, tags)
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
    _lines(rp, "pplr", [(0.0, -0.87, 0.40, 90)], ztop)
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
    # garras da raiz: por cima das quinas de tras, a raiz some embaixo da ombreira
    for k, s in enumerate((-1, 1)):
        if outer:
            poly, pnl = _root_claw(-0.93, hook=(s != sx)) if s == sx else _root_claw(-0.96)
        else:
            poly, pnl = _root_claw(-1.04 if s == sx else -1.08)
        if s < 0:
            poly, pnl = Mo.mirror(poly), Mo.mirror(pnl)
        a, p = _hshard(f"pclaw{k}", poly, pnl, ZT + 0.03, ZT + 0.10, A, slope=0.018, panel_h=0.022, tags=tags)
        # entalhe escuro na base da garra (degrau)
        _lines(p, f"pclawl{k}", [(s * 0.335, -1.60, 0.10, s * 60)], ZT + 0.122, w=0.016, depth=0.04)


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
    """Bracos hidraulicos: berco escuro e um ariete (cilindro escuro + haste cromada) no vao de cada par de
    casulos, inclinado com eles e rente as quinas de cima (de cima o vao fundo fica na sombra)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    for sx in (-1, 1):
        x = sx * 1.25
        # berco escuro sob o par (aparece no vao)
        B.box(f"cradle{sx}", x, 0.25, 0.10, 1.9, 0.30, 0.42, KM, bevel=0.01, tags=tags)
        antes = _cena()
        z = ZT - 0.10
        B.cyl(f"gram{sx}", 0, -1.16, z, 0.052, 0.52, KM, axis="Y", verts=12, bevel=0.006, tags=tags)
        B.cyl(f"gramr{sx}", 0, -0.60, z + 0.004, 0.038, 0.66, S, axis="Y", verts=12, bevel=0.004, tags=tags)
        for k, y in enumerate((-1.36, -0.92)):
            B.cyl(f"gramc{sx}{k}", 0, y, z, 0.06, 0.035, S, axis="Y", verts=12, bevel=0.004, tags=tags)
        B.cyl(f"grame{sx}", 0, -0.26, z, 0.05, 0.13, S, axis="X", verts=12, bevel=0.005, tags=tags)
        _grupo(antes, f"gram_g{sx}", (x, POD_Y, Z0), (PITCH, 0, 0))


def _neck(M, tags):
    """Pescoco: 5 vertebras em divisa (ponta para a frente) que afinam e sobem ate o colar, tons alternados
    (claro / medio), janela de sensor nas claras de tras e par de pips em recesso nas medias, sobre um canal
    escuro com 2 cabos."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.box("neck_core", 0, -0.42, 0.46, 2.80, 0.30, 0.50, KM, bevel=0.01, tags=tags)
    for sx in (-1, 1):
        B.cyl(f"cable{sx}", sx * 0.13, -0.40, 0.52, 0.03, 2.70, K, axis="Y", verts=8, tags=tags)
    ds = (0.52, 0.50, 0.48, 0.46, 0.44)
    ws = (0.285, 0.27, 0.255, 0.24, 0.225)
    gap, tip = 0.07, 0.10
    y0 = -1.82
    dimM = dict(M, glow=M["glow_dim"])
    for k, (d, w) in enumerate(zip(ds, ws)):
        z1 = 0.62 + 0.04 * k
        mat = A if k % 2 == 0 else AM
        poly = [(-w, y0), (0.0, y0 + tip), (w, y0), (w, y0 + d - 0.06), (w - 0.06, y0 + d), (0.0, y0 + d + tip),
                (-w + 0.06, y0 + d), (-w, y0 + d - 0.06)]
        a, p = B.shard(f"vert{k}", poly, 0.40, z1, mat, slope=0.03, groove=0.018, panel_h=0.022, tags=tags)
        ztop = z1 + 0.022
        if k in (1, 3):
            # par de pips em recesso nas laterais
            for s in (-1, 1):
                Mo.slot_with_pips(f"vslot{k}{s}", s * (w - 0.11), y0 + 0.17, y0 + 0.31, 0.04, ztop, 1, dimM, tags,
                                  target=_pecas(a, p), depth=0.07)
            _lines(p, f"vpl{k}", [(0.0, y0 + d / 2 + 0.06, d - 0.26, 0)], ztop, w=0.014)
        elif k in (0, 2):
            # janela do sensor: recesso escuro com uma fenda de luz fraca
            Mo.slot_with_pips(f"vsens{k}", y0 + d / 2 + 0.05, -0.085, 0.085, 0.075, ztop, 1, dimM, tags,
                              target=_pecas(a, p), depth=0.07, vertical=False)
        else:
            _lines(p, f"vpl{k}", [(s * 0.10, y0 + d / 2 + 0.04, 0.16, s * 30) for s in (-1, 1)], ztop, w=0.014)
        y0 += d + gap


def _collar(M, tags, phase):
    """Toco do pescoco no lugar da cabeca: caixa escura, aro blindado octogonal em 4 segmentos (bisel duplo),
    2 degraus escuros (parafusos de aco, 3 tocos) descendo ate um poco preto com a brasa MUITO fraca no fundo
    (respira devagar); em volta o gorjal, uma ferradura por lado aberta para a frente (chifre com crista), o
    arco que liga o pescoco e o queixo baixo na frente."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    blk = M["black"]
    cx, cy = NECK_C
    B.plate("throat_bed", THROAT, 0.30, 0.355, K, slope=0.02, bevel=0.006, tags=tags)
    B.plate("throat_pit", _octagon(cx, cy, 0.16), 0.354, 0.358, blk, slope=0.0, bevel=0.0, tags=tags)
    pulse = 0.5 + 0.5 * math.cos(phase * math.tau)
    # brasa so de emissao (base preta: a luz da cena nao a acende): anel externo quase apagado + miolo
    for nm, r, z, st in (("throat_ember", 0.085, 0.359, 0.03 + 0.025 * pulse),
                         ("throat_core", 0.042, 0.362, 0.10 + 0.09 * pulse)):
        em = B.mat_glow(f"collar_{nm}", EMBER, st)
        em.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0, 0, 0, 1)
        B.cyl(nm, cx, cy, z + 0.002, r, 0.004, em, axis="Z", verts=8, bevel=0.0, tags=tags)
    # degraus escuros descendo para o poco: nucleo (com 3 tocos) e nucleo medio (com parafusos de aco)
    o8 = math.pi / 8
    _washer("neck_r3", cx, cy, 0.40, 0.43, 0.15, 0.20, K, verts=8, a0=o8, tags=tags)
    for k, a in enumerate((0.0, 120.0, 240.0)):
        ar = math.radians(a + 180.0)
        B.rbox(f"neck_stub{k}", cx + 0.13 * math.sin(ar), cy + 0.13 * math.cos(ar), 0.032, 0.09, 0.38, 0.425, KM,
               rot=-(a + 180.0), bevel=0.004, tags=tags)
    _washer("neck_r2", cx, cy, 0.46, 0.50, 0.19, 0.27, KM, verts=8, a0=o8, tags=tags)
    B.bolts("rimbolt", B.ring_points(cx, cy, 0.215, 8, 0.0), 0.505, 0.015, S, tags=tags)
    # aro blindado: lasca octogonal com furo, cortada em 4 segmentos nas diagonais
    ra, rp = B.shard("collar_ring", _octagon(cx, cy, R1_AP), 0.42, 0.58, A, slope=0.025, groove=0.014,
                     panel_h=0.02, tags=tags)
    hole = _octagon(cx, cy, R1_IN)
    for t in _pecas(ra, rp):
        cuts = [B.loft(f"chole_{t.name}", hole, hole, 0.30, 0.90, K, bevel=0.0)]
        for k, ang in enumerate((45, 135, 225, 315)):
            ar = math.radians(ang)
            cuts.append(B.rbox(f"cnotch_{t.name}{k}", cx + 0.29 * math.sin(ar), cy + 0.29 * math.cos(ar), 0.04,
                               0.16, 0.30, 0.90, K, rot=-ang, bevel=0.0))
        B.cut(t, cuts)
    # gorjal: uma ferradura por lado em volta do aro, aberta para a frente, com crista na metade da frente e a
    # fenda de luz fraca na metade de tras
    z0, z1 = 0.40, 0.80
    for s, f in ((-1, Mo.mirror), (1, lambda p: p)):
        a, p = B.shard(f"gorget{s}", f(GORGET), z0, z1, A, slope=0.03, groove=0.016, panel_h=0.022, tags=tags)
        gx, gy, gr = GSLIT
        bx, br = s * gx, s * gr
        for t in _pecas(a, p):
            B.cut(t, [B.rbox(f"gcut_{t.name}", bx, gy, 0.036, 0.13, z1 - 0.05, z1 + 0.4, K, rot=br, bevel=0.0)])
        B.rbox(f"gbed{s}", bx, gy, 0.036, 0.13, z1 - 0.062, z1 - 0.048, blk, rot=br, bevel=0.0, tags=tags)
        B.rbox(f"gglow{s}", bx, gy, 0.013, 0.09, z1 - 0.05, z1 - 0.042, M["glow_dim"], rot=br, bevel=0.0, tags=tags)
        B.bolts(f"gbolt{s}", [(s * 0.37, 1.51)], z1 + 0.026, 0.015, S, tags=tags)
        cr = B.plate(f"gorget_crest{s}", f(GORGET_CREST), z1 + 0.012, z1 + 0.08, A, slope=0.022, bevel=0.007,
                     tags=tags)
        _lines(cr, f"hpl{s}", [(s * 0.50, 2.04, 0.13, s * 35)], z1 + 0.08, w=0.014)
    # arco de tras (liga o pescoco ao colar, em divisa) e queixo baixo na frente
    aa, ap = B.shard("arch", ARCH, 0.40, 0.84, A, slope=0.03, groove=0.018, panel_h=0.022, tags=tags)
    Mo.slot_with_pips("aslot", 0.0, 1.15, 1.31, 0.045, 0.862, 2, dict(M, glow=M["glow_dim"]), tags,
                      target=_pecas(aa, ap), depth=0.07)
    B.plate("chin", CHIN, 0.30, 0.47, AM, slope=0.025, bevel=0.008, tags=tags)
    B.bolts("chinb", [(0.0, 2.22)], 0.475, 0.016, S, tags=tags)


def _rear(M, tags):
    """Ombreiras de tras em 2 degraus: as de dentro em cunha chanfrada para a espinha, as de fora em barbatana
    varrida para tras com entalhe; cada uma com a grelha do defletor de sopro no ponto de backblast. Na faixa
    escura entre os casulos e as ombreiras: dobradica e 2 arietes cromados por casulo. Baia de exaustao com 6
    pips no rabo."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    blk = M["black"]
    for s, f in ((-1, lambda p: p), (1, Mo.mirror)):
        for nm, poly, poly2, z1, px, gw in (("in", IN_H, IN_H2, 0.50, 0.75, 0.36), ("out", OUT_H, OUT_H2, 0.52, 1.75,
                                                                                     0.40)):
            B.shard(f"haunch_{nm}{s}", f(poly), 0.30, z1, A, slope=0.04, groove=0.02, panel_h=0.02, tags=tags)
            z2 = z1 + 0.15
            a, p = B.shard(f"haunch2_{nm}{s}", f(poly2), z1 - 0.02, z2, A, slope=0.035, groove=0.022,
                           panel_h=0.024, tags=tags)
            x = s * px
            ztop = z2 + 0.024
            # grelha do defletor de sopro (ponto de backblast em y = -1.3), longe das bordas chanfradas
            gh, gy = 0.28, -1.26
            for t in _pecas(a, p):
                B.cut(t, [B.box(f"bgc_{t.name}", x, gy, gw, gh, ztop - 0.12, ztop + 0.3, K, bevel=0.0)])
            B.box(f"bgbed{nm}{s}", x, gy, gw, gh, ztop - 0.13, ztop - 0.115, blk, bevel=0.0, tags=tags)
            for k in range(5):
                B.box(f"bglouv{nm}{s}{k}", x, gy - 0.112 + k * 0.056, gw - 0.02, 0.018, ztop - 0.12, ztop - 0.06, KM,
                      bevel=0.0, tags=tags)
            if nm == "out":
                Mo.slot_with_pips(f"hslot{nm}{s}", s * 2.08, -1.34, -1.16, 0.05, ztop, 2, M, tags,
                                  target=_pecas(a, p), depth=0.07)
                B.bolts(f"hb{nm}{s}", [(s * 1.46, -1.50)], z2 + 0.02, 0.02, S, tags=tags)
                _lines(p, f"hpl{nm}{s}", [(s * 1.75, -1.48, 0.30, 90), (s * 2.07, -1.55, 0.16, s * -30)], ztop,
                       depth=0.07)
            else:
                # fenda horizontal (vertical=False: x da funcao = y da fenda, y0..y1 = faixa em x)
                Mo.slot_with_pips(f"hslot{nm}{s}", -1.52, x - 0.11, x + 0.11, 0.045, ztop, 2, M, tags,
                                  target=_pecas(a, p), depth=0.07, vertical=False)
                B.bolts(f"hb{nm}{s}", [(s * 1.02, -1.42)], z2 + 0.02, 0.02, S, tags=tags)
                _lines(p, f"hpl{nm}{s}", [(s * 0.52, -1.48, 0.16, s * 25)], ztop, depth=0.07)
    # faixa da raiz: dobradica (aparece rente a traseira do casulo) e 2 arietes cromados por casulo
    for i, px in enumerate(POD_XS):
        B.cyl(f"hinge{i}", px, -0.70, 0.52, 0.045, 0.56, S, axis="X", verts=12, bevel=0.006, tags=tags)
        for k, s in enumerate((-1, 1)):
            x = px + s * 0.12
            _pitched_cyl(f"rram{i}{k}", x, -0.99, 0.44, 0.048, 0.34, KM, 24.0, verts=12, bevel=0.006, tags=tags)
            _pitched_cyl(f"rrod{i}{k}", x, -0.70, 0.565, 0.028, 0.36, S, 24.0, verts=12, tags=tags)
            _pitched_cyl(f"rcol{i}{k}", x, -0.855, 0.505, 0.056, 0.03, S, 24.0, verts=12, tags=tags)
    # baia de exaustao no rabo: venezianas + 6 pips ambar
    B.box("vent_bay", 0, -2.10, 0.62, 0.32, 0.20, 0.40, blk, bevel=0.0, tags=tags)
    for k in range(6):
        B.box(f"louver{k}", 0, -2.22 + k * 0.048, 0.60, 0.02, 0.34, 0.42, KM, bevel=0.004, tags=tags)
    for k in range(6):
        B.box(f"vent_pip{k}", -0.25 + k * 0.10, -1.955, 0.05, 0.026, 0.38, 0.44, M["glow"], bevel=0.0, tags=tags)
    tail = [(-0.31, -2.27), (0.31, -2.27), (0.24, -2.345), (-0.24, -2.345)]
    B.plate("tail", tail, 0.30, 0.46, AM, slope=0.02, bevel=0.008, tags=tags)
    B.bolts("tbolt", [(x, -2.315) for x in (-0.16, 0.16)], 0.47, 0.02, S, tags=tags)


def _claws(M, tags):
    """Garras longas em foice: nascem nas ombreiras de fora, correm por fora dos casulos externos e curvam para
    dentro na frente em gancho (entalhe a 1/3, painel a mao, fenda de luz fraca perto da ponta)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    for s, f in ((-1, lambda p: p), (1, Mo.mirror)):
        a, p = _hshard(f"claw{s}", f(SICKLE), f(SICKLE_PNL), 0.30, 0.64, A, slope=0.025, panel_h=0.024, tags=tags)
        bx, by, br = s * 2.11, 1.65, s * 19
        for t in (a, p):
            B.cut(t, [B.rbox(f"ccut{s}{t.name}", bx, by, 0.045, 0.24, 0.58, 0.95, K, rot=br, bevel=0.0)])
        B.rbox(f"cbed{s}", bx, by, 0.045, 0.24, 0.56, 0.585, M["black"], rot=br, bevel=0.0, tags=tags)
        B.rbox(f"cglow{s}", bx, by, 0.016, 0.17, 0.585, 0.595, M["glow_dim"], rot=br, bevel=0.0, tags=tags)
        _lines(p, f"cpl{s}", [(s * 2.29, y, 0.10, 0) for y in (-0.55, -0.05, 0.85)], 0.664, w=0.014, depth=0.07)
        B.bolts(f"cbolt{s}", [(s * 2.30, -0.80)], 0.67, 0.018, S, tags=tags)


def _skirt(M, tags):
    """Saia blindada sobre o anel na frente dos casulos (entre o gorjal e as garras): uma placa baixa em divisa
    por lado, tom medio (nao compete com o colar), linha de painel e parafusos."""
    A, AM, S = M["armor"], M["armor_mid"], M["steel"]
    for s, f in ((-1, lambda p: p), (1, Mo.mirror)):
        a, p = B.shard(f"skirt{s}", f(SKIRT), 0.33, 0.43, AM, slope=0.03, groove=0.016, panel_h=0.016, tags=tags)
        _lines(p, f"skl{s}", [(s * 1.16, 1.79, 0.20, s * 52)], 0.446, w=0.014)
        B.bolts(f"skb{s}", [(s * 0.92, 1.83), (s * 1.40, 1.68)], 0.45, 0.017, S, tags=tags)


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


def _wedge_nose(name, a, b, h, ch, c, mat, tags, z0=0.0, dv=0.0, nx=10, na=12, fend=0.22, chev=0.024):
    """Nariz pesado deitado no eixo x: secao em arco liso com a crista deslocada para a frente (+y, c = fracao de
    b), rampa de tras longa e frente curta; pontas em cinzel (largura e altura afinam em linha reta nos ultimos
    ch); a borda da frente faz uma divisa (chev no meio) apontando para a frente. Malha fechada (base plana em z0)
    para aceitar booleanas."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    xs = [-a + ch * k / 3 for k in range(3)] + [-a + ch + (2 * a - 2 * ch) * k / nx for k in range(nx + 1)] + \
        [a - ch + ch * k / 3 for k in range(1, 4)]
    rings = []
    for x in xs:
        f = 1.0 if abs(x) <= a - ch else fend + (1 - fend) * (a - abs(x)) / ch
        bb, hh, cc = b * f, h * (0.30 + 0.70 * f), c * b * f
        bf = bb + chev * f * (1 - abs(x) / a)
        ring = []
        for j in range(na + 1):
            t = math.pi * j / na
            ct = math.cos(t)
            yy = cc + (bf - cc) * ct if ct >= 0 else cc + (bb + cc) * ct
            ring.append(bm.verts.new((x, dv + yy, z0 + hh * max(0.0, math.sin(t)) ** 0.75)))
        rings.append(ring)
    for ra, rb in zip(rings, rings[1:]):
        for j in range(na):
            bm.faces.new((ra[j], rb[j], rb[j + 1], ra[j + 1]))
    caps = [bm.faces.new(list(rings[0])), bm.faces.new(list(reversed(rings[-1])))]
    base = bm.faces.new([r[0] for r in rings] + [r[-1] for r in reversed(rings)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for fc in bm.faces:
        fc.smooth = fc not in caps and fc is not base
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


def _heavy(M, tags, band, box, look):
    """Nariz pesado de calibre duplo (Piranha / Carrapato / Taturana / Poraque) deitado na fileira: corpo CLARO em
    cunha (arco liso com a crista inclinada para a frente, pontas em cinzel), aro fino na cor do missil por baixo
    (aparece atras e nas pontas), capuz escuro do buscador na crista e um detalhe por tipo: costuras escuras
    (submunicoes), presilhas de aco (lapa), sulco na crista + valvulas (napalm), bobinas na cor (EMP)."""
    bw, bd = (box or [0.70, 0.21])
    K, S = M["core"], M["steel"]
    a = bw / 2 - 0.025                  # meio comprimento (lateral)
    b = 0.094                           # meia largura no plano da face
    h = 0.078                           # altura da crista
    z0 = 0.014
    dv = -0.03                          # recua no plano da face: a crista projetada fica centrada na fileira
    ch = 0.085                          # cinzel das pontas
    cf = 0.40                           # crista deslocada para a frente (fracao de b)
    yc = dv + cf * b
    body = _nose_paint("heavy_body", NOSE_LIGHT)
    rim = [(-a - 0.016, dv), (-a + ch, dv - b - 0.018), (a - ch, dv - b - 0.018), (a + 0.016, dv),
           (a - ch, dv + b + 0.012), (-a + ch, dv + b + 0.012)]
    B.loft("h_rim", rim, rim, 0.0, 0.017, band, bevel=0.0, tags=tags)
    cap = _wedge_nose("h_body", a, b, h, ch, cf, body, tags, z0=z0, dv=dv)
    zt = z0 + h
    if look == "cluster":
        # submunicoes: 2 costuras escuras (~2 px) dividem o corpo e o aro em 3 gomos (um por tubo)
        B.cut(cap, [B.box(f"h_seam{k}", s * PU / 2, dv, 0.032, 0.4, z0 - 0.01, 0.4, K, bevel=0.0)
                    for k, s in enumerate((-1, 1))])
        for k, s in enumerate((-1, 1)):
            B.box(f"h_seamf{k}", s * PU / 2, dv, 0.034, 2 * b + 0.08, -0.002, z0 + 0.03, K, bevel=0.0, tags=tags)
    elif look == "limpet":
        # presilhas de aco atravessando o corpo
        for k, s in enumerate((-1, 0, 1)):
            B.box(f"h_clamp{k}", s * 0.20, dv + 0.01, 0.03, 2 * b + 0.05, 0.0, z0 + h * 0.86, S, bevel=0.005,
                  tags=tags)
    elif look == "napalm":
        # sulco escuro ao longo da crista e 2 valvulas de aco nas pontas dele
        B.cut(cap, [B.box("h_groove", 0, yc, 2 * (a - 0.13), 0.04, zt - 0.028, 0.4, K, bevel=0.0)])
        B.box("h_groovef", 0, yc, 2 * (a - 0.13), 0.04, zt - 0.04, zt - 0.024, K, bevel=0.0, tags=tags)
        for k, s in enumerate((-1, 1)):
            B.cyl(f"h_valve{k}", s * (a - 0.10), yc, zt - 0.014, 0.026, 0.04, S, axis="Z", verts=8, bevel=0.004,
                  tags=tags)
    elif look == "emp":
        # bobinas: 2 aneis finos na cor do missil perto das pontas, espacador de aco ao lado
        for k, s in enumerate((-1, 1)):
            B.box(f"h_coil{k}", s * (a - 0.13), dv + 0.01, 0.015, 2 * b + 0.03, 0.0, z0 + h * 0.84, band,
                  bevel=0.003, tags=tags)
            B.box(f"h_coil2{k}", s * (a - 0.17), dv + 0.01, 0.016, 2 * b + 0.024, 0.0, z0 + h * 0.80, S,
                  bevel=0.002, tags=tags)
    # capuz escuro do buscador no meio da crista (aro de aco)
    B.cyl("h_seekr", 0, yc, zt - 0.006, 0.042, 0.016, S, axis="Z", verts=8, bevel=0.003, tags=tags)
    B.cyl("h_seek", 0, yc, zt + 0.0, 0.030, 0.016, K, axis="Z", verts=8, bevel=0.003, tags=tags)


def _torpedo(M, tags, band, box, look):
    """Torpedo (Boto) / Iara: cassete escuro tampando a face, ogiva grande clara com costuras, aro fino na cor
    (branco no Boto, verde na Iara) e buscador escuro com bico de aco."""
    white = _nose_paint("torp_white", (0.53, 0.555, 0.60)) if look != "nuclear" else \
        _nose_paint("torp_iara", (0.40, 0.42, 0.45))
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
    ring_m = M["core_mid"] if look == "nuclear" else band
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
        _lathe("t_nband", [(r_s + 0.005, z_s - 0.009), (r_s + 0.005, z_s + 0.009), (0.0, z_s + 0.009)], band, tags,
               verts=32, sy=sy)
    _lathe("t_seek", [(rt + 0.005, zt - 0.010), (rt + 0.005, zt + 0.002), (0.0, zt + 0.002)], M["core"], tags,
           verts=24, sy=sy)
    _lathe("t_tip", [(r, z + 0.002) for r, z in tip[:-1]] + [(0.0, tip[-1][1] + 0.002)], M["steel"], tags,
           verts=24, sy=sy)


def shutter(M, T="shutter", box=None):
    """Porta blindada fechada sobre a face de um casulo externo (modo nuclear, Iara): 2 folhas em lasca com
    painel em degrau que se encontram numa emenda em divisa apontando para a frente; no bico da divisa a trava
    de aco com um recesso escuro e um pip verde fraco (intertravamento da Iara)."""
    tags = (T,)
    A, AM, KM, S, K = M["armor"], M["armor_mid"], M["core_mid"], M["steel"], M["core"]
    hw = HW + 0.005
    antes = _cena()
    v0, v1 = VTI + 0.01, VBI - 0.005
    B.plate("s_back", B.rpoly(0, (v0 + v1) / 2, 2 * hw, v1 - v0, 0, chamfer=0.03), 0.0, 0.02, KM, slope=0.0,
            bevel=0.004, tags=tags)
    vs, tip, g, c = -0.05, 0.13, 0.018, 0.05       # emenda: altura, flecha da divisa, meia folga, chanfro
    rear = [(-hw + c, v0), (hw - c, v0), (hw, v0 + c), (hw, vs - g), (0.0, vs + tip - g), (-hw, vs - g),
            (-hw, v0 + c)]
    front = [(-hw, vs + g), (0.0, vs + tip + g), (hw, vs + g), (hw, v1 - c), (hw - c, v1), (-hw + c, v1),
             (-hw, v1 - c)]
    ra, rp = B.shard("s_rear", rear, 0.015, 0.045, A, slope=0.016, groove=0.014, panel_h=0.014, tags=tags)
    fa, fp = B.shard("s_front", front, 0.015, 0.045, A, slope=0.016, groove=0.014, panel_h=0.014, tags=tags)
    # degrau: 2a placa elevada no meio de cada folha (bisel duplo em 3 niveis)
    step_r = [(-0.24, v0 + 0.09), (0.24, v0 + 0.09), (0.27, v0 + 0.13), (0.27, vs - 0.09), (0.0, vs + tip - 0.10),
              (-0.27, vs - 0.09), (-0.27, v0 + 0.13)]
    step_f = [(-0.27, vs + 0.10), (0.0, vs + tip + 0.10), (0.27, vs + 0.10), (0.27, v1 - 0.13), (0.24, v1 - 0.09),
              (-0.24, v1 - 0.09), (-0.27, v1 - 0.13)]
    B.plate("s_step_r", step_r, 0.058, 0.072, AM, slope=0.012, bevel=0.005, tags=tags)
    B.plate("s_step_f", step_f, 0.058, 0.072, AM, slope=0.012, bevel=0.005, tags=tags)
    # linhas de painel transversais nas folhas (fora do degrau)
    _lines(rp, "s_rl", [(s * 0.33, v0 + 0.16, 0.08, 0) for s in (-1, 1)], 0.059, w=0.012, depth=0.03)
    _lines(fp, "s_fl", [(s * 0.33, v1 - 0.16, 0.08, 0) for s in (-1, 1)], 0.059, w=0.012, depth=0.03)
    # trava no bico da divisa: placa de aco, recesso escuro e pip verde fraco
    lk = B.plate("s_lock", B.rpoly(0, vs + tip + 0.035, 0.15, 0.10, 0, chamfer=0.03), 0.05, 0.088, S, slope=0.012,
                 bevel=0.004, tags=tags)
    B.cut(lk, [B.box("s_lockc", 0, vs + tip + 0.035, 0.07, 0.04, 0.072, 0.3, K, bevel=0.0)])
    B.box("s_lockb", 0, vs + tip + 0.035, 0.07, 0.04, 0.068, 0.073, M["black"], bevel=0.0, tags=tags)
    pip = B.mat_glow("iara_pip", (0.20, 1.0, 0.15), 2.2)
    B.box("s_pip", 0, vs + tip + 0.035, 0.032, 0.016, 0.072, 0.077, pip, bevel=0.0, tags=tags)
    B.bolts("s_bolt", [(s * (hw - 0.06), v) for s in (-1, 1) for v in (v0 + 0.07, v1 - 0.07)], 0.058, 0.014, S,
            tags=tags)
    _grupo(antes, "shut", (0, 0, 0), (PITCH - 90.0, 0, 0))


# ============================================================================ overclock
def oc_glow(M, T="oc"):
    """So o que brilha no overclock: fogo no fundo do poco do pescoco (miolo quente, anel mais fraco ate a
    borda do degrau escuro; o aro e os degraus da cabeca entram como holdout e cortam o resto), as 2 fendas da
    raiz do gorjal e as grelhas de sopro dos 4 casulos em brasa. Forcas baixas (acima de ~1.5 o laranja vira
    amarelo)."""
    tags = (T,)
    cx, cy = NECK_C
    B.cyl("oc_ring", cx, cy, 0.3685, 0.15, 0.003, B.mat_glow("oc_fire_mid", (1.0, 0.13, 0.01), 0.7), axis="Z",
          verts=8, bevel=0.0, tags=tags)
    B.cyl("oc_core", cx, cy, 0.373, 0.075, 0.004, B.mat_glow("oc_fire", (1.0, 0.16, 0.012), 1.35), axis="Z",
          verts=8, bevel=0.0, tags=tags)
    slit = B.mat_glow("oc_slit", (1.0, 0.16, 0.012), 0.6)
    for s in (-1, 1):
        gx, gy, gr = GSLIT
        z1 = 0.80
        B.rbox(f"oc_gslit{s}", s * gx, gy, 0.02, 0.11, z1 - 0.040, z1 - 0.036, slit, rot=s * gr, bevel=0.0,
               tags=tags)
    vent_oc = B.mat_glow("oc_vent", (1.0, 0.18, 0.02), 0.9)
    for i, px in enumerate(POD_XS):
        antes = _cena()
        for k in range(3):
            y = VENT_Y - 0.05 + k * 0.05
            B.box(f"oc_pv{i}{k}", 0, y, 0.38, 0.028, VENT_Z + 0.001, VENT_Z + 0.007, vent_oc, bevel=0.0, tags=tags)
        _grupo(antes, f"oc_pod{i}", (px, POD_Y, Z0), (PITCH, 0, 0))


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto padrao (placas verdes, anel, escotilha e respiros na fileira de tras) + 2 escotilhas do carregador de
    misseis nos tiles laterais da fileira de tras (portas duplas, alca e contador de 3 pips fracos)."""
    tags = (T,)
    w, h = PART["size"]
    Mo.hull_roof(M, w, h, PART["pivot"], PART["ring_r"], T)
    K, AM, S, A = M["core"], M["armor_mid"], M["steel"], M["armor"]
    hy = -h / 2 + 0.5
    for s in (-1, 1):
        hx = s * 1.0
        base = B.rpoly(hx, hy, 0.72, 0.64, 0, chamfer=0.12)
        hp = B.plate(f"lhatch{s}", base, 0.06, 0.10, AM, slope=0.02, tags=tags)
        for k, dx in enumerate((-0.165, 0.165)):
            d = B.plate(f"ldoor{s}{k}", B.rpoly(hx + dx, hy - 0.01, 0.30, 0.40, 0, chamfer=0.05), 0.10, 0.125, A,
                        slope=0.012, bevel=0.006, tags=tags)
            B.cut(d, [B.rbox(f"ldl{s}{k}", hx + dx, hy - 0.01, 0.014, 0.24, 0.115, 0.3, K,
                             rot=30 * (1 if k else -1), bevel=0.0)])
        B.box(f"lhandle{s}", hx, hy - 0.265, 0.20, 0.035, 0.10, 0.13, S, bevel=0.008, tags=tags)
        Mo.slot_with_pips(f"lcnt{s}", hy + 0.25, hx - 0.10, hx + 0.10, 0.035, 0.10, 3, dict(M, glow=M["glow_dim"]),
                          tags, target=hp, depth=0.03, vertical=False)


def _floor_missile(name, cx, cy, rot, M, nose, tags, r=0.078, ln=0.46):
    """Missil deitado no berco do piso (corpo escuro, faixa em brasa fraca, nariz claro com ponta escura)."""
    a = math.radians(rot)
    ux, uy = -math.sin(a), math.cos(a)
    B.cyl(f"{name}b", cx - ux * 0.05, cy - uy * 0.05, 0.15, r, ln, M["core_mid"], axis="Y", verts=12, yaw=rot,
          bevel=0.006, tags=tags)
    B.cyl(f"{name}f", cx - ux * (0.05 + ln / 2 - 0.02), cy - uy * (0.05 + ln / 2 - 0.02), 0.15, r + 0.012, 0.04,
          M["steel"], axis="Y", verts=12, yaw=rot, bevel=0.0, tags=tags)
    B.cyl(f"{name}k", cx + ux * (ln / 2 - 0.08), cy + uy * (ln / 2 - 0.08), 0.15, r + 0.006, 0.03, M["ember"],
          axis="Y", verts=12, yaw=rot, bevel=0.0, tags=tags)
    B.cyl(f"{name}n", cx + ux * (ln / 2 + 0.01), cy + uy * (ln / 2 + 0.01), 0.15, r, 0.14, nose, axis="Y",
          verts=12, yaw=rot, r2=0.018, tags=tags)


def floor(M, T="floor"):
    """Piso do paiol: placas, anel com pedestal octogonal (cubo, setas em divisa, LEDs), elevador de misseis
    atras do cubo, 6 bercos com 3 misseis pesados cada (cantos da frente, laterais), estantes na parede de
    tras e os 8 postos."""
    from bsgen.common import crew_positions
    tags = (T,)
    W, H = PART["size"]
    pv = PART["pivot"]
    rr = PART["ring_r"]
    px, py = pv[0] - W / 2, H / 2 - pv[1]
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.box("fl_base", 0, 0, W, H, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for tx in range(W):
        for ty in range(H):
            x0, y1 = tx - W / 2 + 0.04, H / 2 - ty - 0.04
            B.box(f"fl{tx}{ty}", x0 + 0.46, y1 - 0.46, 0.92, 0.92, 0.0, 0.03, KM, bevel=0.01, tags=tags)
    # anel e pedestal octogonal (como o da Boiuna / Mapinguari)
    B.torus("fl_ring", px, py, 0.05, rr * 0.86, 0.06, AM, tags=tags)
    B.plate("fl_trunk", B.rpoly(px, py, 2.2, 2.2, 0, chamfer=0.62), 0.02, 0.07, KM, slope=0.03, tags=tags)
    wh = rr * 0.55
    B.plate("fl_hub", _octagon(px, py, wh / 2), 0.05, 0.12, AM, slope=0.03, tags=tags)
    B.plate("fl_hubc", _octagon(px, py, wh * 0.26), 0.10, 0.125, K, slope=0.015, tags=tags)
    B.plate("fl_hubs", _octagon(px, py, wh * 0.09), 0.12, 0.15, S, slope=0.01, bevel=0.006, tags=tags)
    B.bolts("fl_hubb", B.ring_points(px, py, wh * 0.38, 8, math.pi / 8), 0.125, 0.018, S, tags=tags)
    for k in range(4):
        a = k * math.pi / 2
        cx, cy = px + math.cos(a) * rr * 0.62, py + math.sin(a) * rr * 0.62
        arrow = [(0.13, 0.0), (-0.08, 0.13), (-0.02, 0.0), (-0.08, -0.13)]
        ca, sa = math.cos(a), math.sin(a)
        arrow = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in arrow]
        B.plate(f"fl_chev{k}", arrow, 0.05, 0.08, A, slope=0.01, bevel=0.006, tags=tags)
    B.box("fl_led_t", px, py + rr * 0.96, 0.4, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    B.box("fl_led_b", px, py - rr * 0.96, 0.4, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    nose = _nose_paint("nose", (0.74, 0.75, 0.76))
    # elevador de misseis atras do cubo (missil em pe: faixa em brasa, nariz claro)
    hy = py - 0.80
    B.plate("fl_hoist", _octagon(px, hy, 0.20), 0.05, 0.12, AM, slope=0.02, tags=tags)
    B.cyl("fl_hoistb", px, hy, 0.13, 0.11, 0.03, M["ember"], axis="Z", verts=16, bevel=0.0, tags=tags)
    B.cyl("fl_hoistn", px, hy, 0.20, 0.095, 0.12, nose, axis="Z", verts=16, r2=0.016, tags=tags)
    # 6 bercos de 3 misseis: cantos da frente (inclinados) e laterais (fora do anel)
    for i, (cx, cy, rot) in enumerate(((-2.0, 2.42, -30), (2.0, 2.42, 30), (-2.10, 0.55, 0), (2.10, 0.55, 0),
                                       (-2.10, -1.25, 0), (2.10, -1.25, 0))):
        a = math.radians(rot)
        vx, vy = math.cos(a), math.sin(a)
        B.rbox(f"cradle{i}", cx, cy, 0.68, 0.66, 0.0, 0.07, AM, rot=rot, chamfer=0.07, bevel=0.01, tags=tags)
        for k in (-1, 0, 1):
            B.rbox(f"csad{i}{k}", cx + vx * k * 0.19, cy + vy * k * 0.19, 0.17, 0.10, 0.07, 0.10, KM, rot=rot,
                   bevel=0.006, tags=tags)
            _floor_missile(f"cm{i}{k}", cx + vx * k * 0.19, cy + vy * k * 0.19, rot, M, nose, tags)
    # estantes na parede de tras + postos (assento, console e tela)
    for tx in range(W):
        x = tx - W / 2 + 0.5
        B.box(f"rack{tx}", x, -H / 2 + 0.13, 0.78, 0.18, 0.0, 0.16, AM, bevel=0.01, tags=tags)
        for i in range(3):
            B.box(f"mag{tx}{i}", x - 0.24 + i * 0.24, -H / 2 + 0.13, 0.16, 0.12, 0.16, 0.24, KM, bevel=0.01,
                  tags=tags)
            B.box(f"magled{tx}{i}", x - 0.24 + i * 0.24, -H / 2 + 0.13, 0.10, 0.03, 0.24, 0.26, M["glow_dim"],
                  bevel=0.0, tags=tags)
    for i, (cx, cy, _r) in enumerate(crew_positions(W, H, 8, pv)):
        x, y = cx - W / 2, H / 2 - cy
        B.box(f"seat{i}", x, y + 0.02, 0.30, 0.28, 0.0, 0.14, A, bevel=0.04, tags=tags)
        B.box(f"console{i}", x, y + 0.30, 0.38, 0.12, 0.0, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.30, 0.28, 0.06, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
