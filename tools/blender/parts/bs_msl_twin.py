"""Lancador de Misseis de Conves de Casulo Duplo ("Caipora") - lancador 3x3 medio, familia do 76 mm.

Caipora = guardia da mata montada num porco-do-mato: "dois punhos" (casulos OCTOGONAIS 3-2-3, 8 tubos cada,
inclinados 35 graus) em bracos blindados ladeando uma cupula facetada de lascas claras com UM olho-sensor
(fenda ambar num visor inclinado), sobrancelha feroz em divisa e presas de queixada saindo do focinho;
laminas-garra avancam pelos lados de fora dos casulos, quatro pes abertos no anel, escotilha do carregador e
baia de exaustao de 5 pips atras. Overclock (turret_oc.png): o olho vira laranja e as baias de sopro/exaustao
ficam em brasa.
Casulos modelados no proprio referencial (face no plano local, como a Tocandira) e girados; as bocas projetadas
batem com launcher_layout (centros (+-0.85, 0.35), passo 0.24 x 0.24 na vista de cima, tube_r 0.085).
"""

import math
import os

import bmesh
import bpy

import bs3d as B
import models as Mo

DRAFT = os.environ.get("BS_DRAFT") == "1"     # rascunho: sem os 8 quadros do olho piscando

PART = {
    "id": "rafaeltessaro.bs_msl_twin",
    "kind": "launcher",
    "size": [3, 3],
    "pivot": [1.5, 1.4],           # = art.part_meta.pivot do spec
    "turret_box": 2.8,
    "ring_r": 1.15,
    "collider": 1.25,
    "accent": "amber",
    "looks": ["he", "cluster", "limpet", "napalm", "emp", "torpedo"],
    "oc_glow": True,
    "lights": [
        {"at": [0.0, -1.10], "size": 1.2, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "ripple",
}
if not DRAFT:
    PART["turret_anim"] = {"frames": 8, "interval": 0.12}   # olho da cupula pulsando

PITCH = 35.0
SIN, COS = math.sin(math.radians(PITCH)), math.cos(math.radians(PITCH))
TN = math.tan(math.radians(PITCH))
POD_X, POD_Y = 0.85, 0.35           # centro da face projetado (cells.pods[*].center)
Z0 = 0.95                           # altura do centro da face
TUBE_R = 0.085
PU = 0.24                           # passo lateral
RV = 0.24 / SIN                     # passo das fileiras no plano da face (0.24 na vista de cima)
# bocas no plano da face (u lateral, v descendo a face = frente na vista de cima); fileiras 3-2-3
TUBES = [(u, v) for v, n in ((-RV, 3), (0.0, 2), (RV, 3)) for u in [(c - (n - 1) / 2) * PU for c in range(n)]]
# octogono da face (plano da face): chanfro com 45 graus na vista de cima (CV = CU / SIN)
HW, HH, CU = 0.395, 0.66, 0.10
CV = CU / SIN
POD_L = 0.72                        # comprimento do casulo ao longo do eixo dos tubos

BAND = {"he": (0.80, 0.327, 0.0), "cluster": (0.80, 0.62, 0.086), "limpet": (0.80, 0.035, 0.024),
        "napalm": (0.80, 0.11, 0.0093), "emp": (0.062, 0.437, 0.80), "torpedo": (0.72, 0.74, 0.80)}
BAND_GLOW = {"he": (1.0, 0.473, 0.0), "cluster": (1.0, 0.78, 0.11), "limpet": (1.0, 0.044, 0.03),
             "napalm": (1.0, 0.186, 0.0155), "emp": (0.078, 0.546, 1.0), "torpedo": (0.9, 0.93, 1.0)}


# ============================================================================ utilidades
def _cena():
    return set(o.name for o in bpy.context.scene.objects)


def _novos(antes):
    """Objetos (e Empties de subgrupos) criados depois de 'antes' e ainda sem pai."""
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


def _sem_sombra(*objs):
    for o in objs:
        if isinstance(o, (tuple, list)):
            _sem_sombra(*o)
        elif o is not None:
            o.visible_shadow = False


def _octo(hw, hh, cu, cv, cx=0.0, cy=0.0):
    return [(cx - hw + cu, cy - hh), (cx + hw - cu, cy - hh), (cx + hw, cy - hh + cv), (cx + hw, cy + hh - cv),
            (cx + hw - cu, cy + hh), (cx - hw + cu, cy + hh), (cx - hw, cy + hh - cv), (cx - hw, cy - hh + cv)]


def _offset_edges(poly, ds):
    """Desloca cada aresta i (de poly[i] a poly[i+1]) para dentro por ds[i]; arestas continuam paralelas,
    entao as laterais de um loft (poly -> resultado) sao trapezios planos (facetas limpas)."""
    poly = list(poly)
    s = sum((poly[(i + 1) % len(poly)][0] - poly[i][0]) * (poly[(i + 1) % len(poly)][1] + poly[i][1])
            for i in range(len(poly)))
    if s > 0:
        raise ValueError("_offset_edges: poligono precisa ser anti-horario")
    n = len(poly)
    lines = []
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        lines.append(((x1 + nx * ds[i], y1 + ny * ds[i]), (dx / L, dy / L)))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


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


# ============================================================================ casulo: face (referencial da face)
def _pod_face(M, tags, sx):
    """Face do casulo no plano XY (x direita, y descendo a face = frente na vista de cima, z = para fora).
    Tudo que sai da face aparece deslocado para a FRENTE na vista de cima: a aba de cima da moldura e baixa e
    fica longe da fileira de tras, senao cobre as bocas vazias."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    blk = M["black"]
    outer = _octo(HW, HH, CU, CV)
    # corpo escuro (nucleo) ao longo do eixo e fundo preto atras das bocas
    B.plate("pbody", _octo(HW - 0.03, HH - 0.03, CU, CV), -POD_L, -0.03, KM, slope=0.0, bevel=0.01, tags=tags)
    B.plate("pback", _octo(HW - 0.05, HH - 0.06, CU, CV), -0.16, -0.06, blk, slope=0.0, bevel=0.0, tags=tags)
    # placa das bocas (colmeia escura) com 8 furos e aro de aco em cada boca
    plate = B.plate("pplate", _octo(HW - 0.045, HH - 0.065, CU * 0.8, CV * 0.8), -0.07, 0.0, KM, slope=0.012,
                    bevel=0.006, tags=tags)
    B.cut(plate, [B.cyl(f"pbore{i}", u, v, 0.0, TUBE_R, 0.4, K, axis="Z", verts=24, bevel=0.0)
                  for i, (u, v) in enumerate(TUBES)])
    for i, (u, v) in enumerate(TUBES):
        rim = B.cyl(f"prim{i}", u, v, 0.006, TUBE_R + 0.016, 0.026, S, axis="Z", verts=24, bevel=0.004, tags=tags)
        B.cut(rim, [B.cyl(f"primc{i}", u, v, 0.0, TUBE_R, 0.3, K, axis="Z", verts=24, bevel=0.0)])
    # nervuras entre as fileiras e parafusos nos cantos da placa
    for k, v in enumerate((-RV / 2, RV / 2)):
        B.box(f"prib{k}", 0, v, 2 * (HW - 0.10), 0.028, -0.01, 0.018, S, bevel=0.004, tags=tags)
    B.bolts("pfbolt", [(u, v) for u in (-0.27, 0.27) for v in (-0.05, 0.05)], 0.008, 0.014, S, tags=tags)
    # moldura octogonal clara baixa (bisel duplo) partida em 4 lascas por vaos escuros nas quinas
    fa, fp = B.shard("pframe", outer, -0.03, 0.03, A, slope=0.015, groove=0.018, panel_h=0.016, tags=tags)
    hole = _octo(HW - 0.055, HH - 0.085, CU * 0.75, CV * 0.75)
    for t in _pecas(fa, fp):
        cuts = [B.loft(f"phole_{t.name}", hole, hole, -0.3, 0.4, K, bevel=0.0)]
        for j, (gu, gv) in enumerate(((HW - 0.03, -HH + CV + 0.03), (HW - 0.03, HH - CV - 0.03),
                                      (-HW + 0.03, -HH + CV + 0.03), (-HW + 0.03, HH - CV - 0.03))):
            cuts.append(B.box(f"pgap_{t.name}{j}", gu, gv, 0.10, 0.032, -0.3, 0.4, K, bevel=0.0))
        B.cut(t, cuts)
    B.plate("pframe_bed", _octo(HW - 0.01, HH - 0.01, CU, CV), -0.05, -0.025, blk, slope=0.0, bevel=0.0, tags=tags)
    # queixo em lamina na aba de baixo (aponta para a frente), com fenda escura
    chin = [(-0.12, HH - 0.05), (0.12, HH - 0.05), (0.12, HH + 0.03), (0.035, HH + 0.16), (-0.035, HH + 0.16),
            (-0.12, HH + 0.03)]
    ca, cp = B.shard("pchin", chin, -0.05, 0.08, A, slope=0.022, groove=0.016, panel_h=0.02, tags=tags)
    slot = [(-0.02, HH - 0.01), (0.02, HH - 0.01), (0.02, HH + 0.05), (0.0, HH + 0.09), (-0.02, HH + 0.05)]
    for t in _pecas(ca, cp):
        B.cut(t, [B.loft(f"pcslot_{t.name}", slot, slot, 0.02, 0.4, K, bevel=0.0)])
    B.loft("pchin_bed", slot, slot, 0.012, 0.024, blk, bevel=0.0, tags=tags)


# ============================================================================ casulo: topo (referencial do eixo)
def _pod_top(M, tags, sx):
    """Blindagem do topo e dos chanfros de cima (x direita, y = eixo dos tubos, face em y = 0, z = cima)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    zt = HH - 0.03                                  # topo do corpo
    L = POD_L
    # topo em 2 lascas separadas por um vao em divisa apontando para a frente: a de tras tem a grelha de sopro
    # (tubos abertos atras), a da frente a fenda de 3 pips
    w = HW - CU - 0.02
    front = [(-w, -0.44), (0.0, -0.36), (w, -0.44), (w, -0.08), (w - 0.05, -0.04), (-w + 0.05, -0.04), (-w, -0.08)]
    rear = [(-w, -L + 0.10), (-0.10, -L + 0.04), (0.10, -L + 0.04), (w, -L + 0.10), (w, -0.48), (0.0, -0.40),
            (-w, -0.48)]
    fa, fp = B.shard("ptopf", front, zt - 0.02, zt + 0.05, A, slope=0.03, groove=0.022, panel_h=0.022, tags=tags)
    ra, rp = B.shard("ptopr", rear, zt - 0.02, zt + 0.05, A, slope=0.03, groove=0.022, panel_h=0.022, tags=tags)
    ztop = zt + 0.072
    for t in _pecas(ra, rp):
        B.cut(t, [B.box(f"pvcut_{t.name}", 0, -L + 0.15, 0.34, 0.10, ztop - 0.10, ztop + 0.4, K, bevel=0.0)])
    B.box("pvbed", 0, -L + 0.15, 0.34, 0.10, ztop - 0.11, ztop - 0.095, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"pvlouv{i}", 0, -L + 0.12 + i * 0.03, 0.32, 0.012, ztop - 0.10, ztop - 0.06, KM, bevel=0.0,
              tags=tags)
    Mo.slot_with_pips("ppip", 0.0, -0.30, -0.12, 0.045, ztop, 3, M, tags, target=_pecas(fa, fp), depth=0.07)
    # linhas de painel diagonais nas abas da lasca da frente
    _lines(fp, "ppl", [(s * 0.19, -0.22, 0.18, s * 28) for s in (-1, 1)], ztop)
    # lascas dos chanfros de cima (referencial girado em torno do eixo)
    ang = math.degrees(math.atan2(CV, CU))
    for k, s in enumerate((-1, 1)):
        antes = _cena()
        wc = math.hypot(CU, CV) - 0.06
        ch = B.rpoly(0, -L / 2 - 0.02, wc, L - 0.12, 0, chamfer=0.04)
        a, p = B.shard(f"pch{k}", ch, -0.01, 0.04, A, slope=0.02, groove=0.014, panel_h=0.016, tags=tags)
        if s == sx:
            # lado de fora: 2 entalhes escuros (respiros)
            for t in _pecas(a, p):
                B.cut(t, [B.box(f"pchc_{t.name}{i}", 0, -0.24 - i * 0.12, wc * 0.6, 0.035, 0.0, 0.4, K, bevel=0.0)
                          for i in range(2)])
        _grupo(antes, f"pchg{k}", (s * (HW - CU / 2 - 0.004), 0, zt - CV / 2 + 0.03), (0, s * ang, 0))


def _pod(M, tags, sx):
    """Um casulo inteiro, girado e posicionado (lado sx = -1 esquerda, 1 direita)."""
    cx = sx * POD_X
    antes = _cena()
    _pod_top(M, tags, sx)
    _grupo(antes, f"pod_top{sx}", (cx, POD_Y, Z0), (PITCH, 0, 0))
    antes = _cena()
    _pod_face(M, tags, sx)
    _grupo(antes, f"pod_face{sx}", (cx, POD_Y, Z0), (PITCH - 90.0, 0, 0))


# ============================================================================ cupula (cabeca da Caipora)
DOME = [(-0.20, -0.60), (0.20, -0.60), (0.35, -0.44), (0.37, 0.18), (0.25, 0.56), (-0.25, 0.56), (-0.37, 0.18),
        (-0.35, -0.44)]
DOME_Z = (0.40, 1.00)
# deslocamento de cada aresta ate o topo: traseira, chanfro tras, lado, chanfro frente, VISOR, chanfro, lado, chanfro
DOME_D = [0.14, 0.13, 0.10, 0.20, 0.36, 0.20, 0.10, 0.13]
EYE_Y = 0.385


def _visor_z(y):
    """Altura da superficie do visor (aresta da frente da cupula) em y."""
    y0 = DOME[4][1]
    z0, z1 = DOME_Z
    return z0 + (y0 - y) / DOME_D[4] * (z1 - z0)


def _eye_poly(ye, hw, hh, k=0.0):
    """Fenda do olho: hexagono alongado com as pontas de fora puxadas para tras (olhar bravo)."""
    return [(-hw, ye - k), (-hw * 0.45, ye - hh), (hw * 0.45, ye - hh), (hw, ye - k), (hw * 0.45, ye + hh),
            (-hw * 0.45, ye + hh)]


def _dome(M, tags, phase):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    top = _offset_edges(DOME, DOME_D)
    z0, z1 = DOME_Z
    # colar escuro embaixo
    B.plate("dcollar", B.offset_poly(DOME, -0.03), 0.28, z0 + 0.02, KM, slope=0.02, bevel=0.01, tags=tags)
    shell = B.loft("dshell", DOME, top, z0, z1, A, bevel=0.012, tags=tags)
    # vaos escuros nas juntas: casco vira visor (frente), 2 flancos e nuca
    cuts = []
    for i in (2, 3, 6, 7):
        (xa, ya), (xb, yb) = DOME[i], top[i]
        dx, dy = xb - xa, yb - ya
        ln = math.hypot(dx, dy)
        rot = math.degrees(math.atan2(-dx, dy))
        cuts.append(B.rbox(f"dgap{i}", (xa + xb) / 2, (ya + yb) / 2, 0.045, ln + 0.3, z0 - 0.01, 1.5, K, rot=rot,
                           bevel=0.0))
    # linhas de painel nos flancos
    cuts += [B.rbox(f"dfl{sx}", sx * 0.31, -0.14, 0.018, 0.30, 0.55, 1.5, K, bevel=0.0) for sx in (-1, 1)]
    # olho: fenda hexagonal alongada no visor, paredes verticais
    eye = _eye_poly(EYE_Y, 0.20, 0.042, k=0.012)
    zf = _visor_z(EYE_Y + 0.045) - 0.035
    cuts.append(B.loft("deye_cut", eye, eye, zf, 1.5, K, bevel=0.0))
    B.cut(shell, cuts)
    B.loft("deye_bed", eye, eye, zf - 0.012, zf + 0.002, M["black"], bevel=0.0, tags=tags)
    pulse = 0.5 + 0.5 * math.cos(phase * math.tau)
    eye_m = B.mat_glow("eye_slit", Mo.AMBER, 0.9 + 0.9 * pulse)
    B.loft("deye", _eye_poly(EYE_Y, 0.15, 0.016, k=0.008), _eye_poly(EYE_Y, 0.15, 0.016, k=0.008), zf, zf + 0.012,
           eye_m, bevel=0.0, tags=tags)
    for i in (2, 3, 6, 7):
        (xa, ya), (xb, yb) = DOME[i], top[i]
        rot = math.degrees(math.atan2(-(xb - xa), yb - ya))
        B.rbox(f"dgapbed{i}", (xa + xb) / 2, (ya + yb) / 2, 0.045, math.hypot(xb - xa, yb - ya), z0, z0 + 0.03,
               M["black"], rot=rot, bevel=0.0, tags=tags)
    # coroa (topo) com bisel duplo
    crown = B.offset_poly(top, 0.015)
    B.shard("dcrown", crown, z1 - 0.01, z1 + 0.06, A, slope=0.03, groove=0.022, panel_h=0.022, tags=tags)
    zc = z1 + 0.082
    # crina: quilha em seta sobre a coroa com fenda de 3 pips (eco da espinha do 76 mm)
    yb = top[4][1]
    mane = [(-0.06, -0.50), (0.06, -0.50), (0.09, -0.42), (0.09, yb - 0.20), (0.0, yb - 0.10), (-0.09, yb - 0.20),
            (-0.09, -0.42)]
    ma, mp = B.shard("dmane", mane, zc - 0.01, zc + 0.05, A, slope=0.02, groove=0.016, panel_h=0.018, tags=tags)
    Mo.slot_with_pips("dpip", 0.0, -0.42, -0.20, 0.042, zc + 0.068, 3, M, tags, target=_pecas(ma, mp), depth=0.06)
    # sobrancelha feroz: divisa clara e grossa apontando para a frente sobre o olho (borda da coroa)
    brow = [(-0.31, yb - 0.18), (-0.03, yb - 0.04), (0.03, yb - 0.04), (0.31, yb - 0.18), (0.34, yb - 0.07),
            (0.03, yb + 0.09), (-0.03, yb + 0.09), (-0.34, yb - 0.07)]
    B.shard("dbrow", brow, z1 + 0.01, z1 + 0.13, A, slope=0.02, groove=0.014, panel_h=0.02, tags=tags)
    # focinho: placa escura com grelha entre as presas
    snout = [(-0.17, 0.53), (0.17, 0.53), (0.15, 0.68), (0.07, 0.74), (-0.07, 0.74), (-0.15, 0.68)]
    sn = B.plate("dsnout", snout, 0.28, 0.46, KM, slope=0.025, bevel=0.008, tags=tags)
    B.cut(sn, [B.box(f"dsnc{i}", 0, 0.61 + i * 0.04, 0.20, 0.016, 0.42, 0.8, K, bevel=0.0) for i in range(3)])
    # presas de queixada: crescentes saindo do focinho para a frente e curvando para fora
    tusk = [(-0.13, 0.68), (-0.20, 0.57), (-0.27, 0.66), (-0.33, 0.76), (-0.40, 0.84), (-0.47, 0.88),
            (-0.42, 0.925), (-0.32, 0.90), (-0.24, 0.83), (-0.17, 0.74)]
    for side, f in (("L", lambda p: p), ("R", Mo.mirror)):
        B.plate(f"dtusk{side}", f(tusk), 0.36, 0.56, A, slope=0.025, bevel=0.01, tags=tags)


# ============================================================================ bracos, garras, pes, traseira
def _arms(M, tags):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    yc, zc = POD_Y - POD_L / 2 * COS, Z0 - POD_L / 2 * SIN      # centro do casulo (munhao)
    blade = [(-1.37, -0.35), (-1.37, 0.70), (-1.30, 0.88), (-1.12, 1.07), (-0.92, 1.23), (-0.78, 1.32),
             (-0.74, 1.26), (-0.84, 1.11), (-0.99, 0.96), (-1.14, 0.83), (-1.25, 0.70), (-1.27, -0.35)]
    blade_pnl = [(-1.335, 0.30), (-1.335, 0.695), (-1.268, 0.862), (-1.095, 1.04), (-0.905, 1.19), (-0.85, 1.215),
                 (-0.89, 1.13), (-1.02, 0.99), (-1.17, 0.86), (-1.29, 0.70), (-1.295, 0.30)]
    shoulder = [(-0.78, -0.66), (-1.30, -0.66), (-1.37, -0.76), (-1.24, -1.02), (-1.10, -1.10), (-1.02, -0.92),
                (-0.86, -0.80)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        # munhao entre a cupula e o casulo
        B.cyl(f"trun{side}", sx * 0.41, yc, zc, 0.07, 0.14, S, axis="X", verts=12, bevel=0.006, tags=tags)
        B.box(f"trunb{side}", sx * 0.41, yc, 0.08, 0.30, 0.30, zc, KM, bevel=0.01, tags=tags)
        # lamina-garra pelo lado de fora do casulo, ponta para a frente e para dentro (painel a mao)
        ba = B.plate(f"blade{side}", f(blade), 0.40, 0.78, A, slope=0.025, tags=tags)
        bp = B.plate(f"blade{side}_pnl", f(blade_pnl), 0.776, 0.80, A, slope=0.01, bevel=0.0, tags=tags)
        Mo.slot_with_pips(f"bslot{side}", sx * 1.32, -0.24, 0.12, 0.04, 0.78, 3, M, tags, target=[ba], depth=0.07)
        # fenda com luz ao longo da curva da lamina
        bx, by, br = sx * 1.055, 1.015, sx * 42
        for t in (ba, bp):
            B.cut(t, [B.rbox(f"bcut{side}{t.name}", bx, by, 0.05, 0.22, 0.74, 0.9, K, rot=br, bevel=0.0)])
        B.rbox(f"bbed{side}", bx, by, 0.05, 0.22, 0.72, 0.745, M["black"], rot=br, bevel=0.0, tags=tags)
        B.rbox(f"bglow{side}", bx, by, 0.016, 0.16, 0.745, 0.755, M["glow_dim"], rot=br, bevel=0.0, tags=tags)
        # ombreira traseira (braco que segura o casulo) em cunha com espora para tras
        sa, sp = B.shard(f"shoulder{side}", f(shoulder), 0.30, 0.72, A, slope=0.04, groove=0.022, panel_h=0.028,
                         tags=tags)
        Mo.slot_with_pips(f"sslot{side}", sx * 1.17, -0.92, -0.76, 0.045, 0.748, 2, M, tags, target=_pecas(sa, sp),
                          depth=0.07)
        _lines(sp, f"spl{side}", [(sx * 1.00, -0.75, 0.14, sx * -60)], 0.748)


def _feet(M, tags):
    """Quatro pes abertos no anel (base de 4 pernas da ref. 3): cunhas baixas com dedo escuro."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    foot = [(0.84, -0.09), (1.10, -0.09), (1.22, -0.13), (1.37, -0.05), (1.37, 0.05), (1.22, 0.13), (1.10, 0.09),
            (0.84, 0.09)]
    for k, a in enumerate((60, 148, 212, 300)):
        ar = math.radians(a)
        ux, uy = math.sin(ar), math.cos(ar)          # direcao do pe (a partir de +Y)
        vx, vy = uy, -ux

        def tr(p):
            return [(r * ux + t * vx, r * uy + t * vy) for r, t in p]
        fa, fp = B.shard(f"foot{k}", tr(foot), 0.22, 0.38, A, slope=0.025, groove=0.018, panel_h=0.02, tags=tags)
        toe = tr([(1.12, -0.03), (1.26, -0.03), (1.26, 0.03), (1.12, 0.03)])
        for t in _pecas(fa, fp):
            B.cut(t, [B.loft(f"ftoe_{t.name}", toe, toe, 0.34, 0.6, K, bevel=0.0)])
        B.loft(f"ftoebed{k}", toe, toe, 0.33, 0.342, M["black"], bevel=0.0, tags=tags)


def _rear(M, tags):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    # escotilha do carregador (magazine): placa clara com contorno de escotilha, alca e contador
    hatch = [(-0.28, -1.03), (0.28, -1.03), (0.34, -0.97), (0.34, -0.78), (0.26, -0.70), (-0.26, -0.70),
             (-0.34, -0.78), (-0.34, -0.97)]
    ha, hp = B.shard("hatch", hatch, 0.30, 0.60, A, slope=0.04, groove=0.025, panel_h=0.025, tags=tags)
    zh = 0.625
    inner = B.rpoly(0, -0.885, 0.42, 0.20, 0, chamfer=0.05)
    out = B.offset_poly(inner, -0.018)
    if hp is not None:
        B.cut(hp, [B.loft("hring_c", out, out, zh - 0.03, zh + 0.4, K, bevel=0.0)])
        B.plate("hlid", inner, zh - 0.05, zh + 0.005, A, slope=0.012, bevel=0.006, tags=tags)
        B.loft("hring_bed", out, out, zh - 0.045, zh - 0.03, M["black"], bevel=0.0, tags=tags)
    B.box("hhandle", 0, -0.93, 0.18, 0.035, zh, zh + 0.03, S, bevel=0.008, tags=tags)
    for i in range(4):
        B.box(f"hled{i}", -0.105 + i * 0.07, -0.84, 0.04, 0.022, zh, zh + 0.012,
              M["glow"] if i < 3 else M["black"], bevel=0.0, tags=tags)
    # baia de exaustao com 5 pips
    B.box("vent_bay", 0, -1.16, 0.62, 0.20, 0.20, 0.36, M["black"], bevel=0.0, tags=tags)
    for i in range(5):
        B.box(f"louver{i}", 0, -1.235 + i * 0.033, 0.60, 0.016, 0.30, 0.37, KM, bevel=0.003, tags=tags)
    for i in range(5):
        B.box(f"vent_pip{i}", -0.24 + i * 0.12, -1.085, 0.05, 0.024, 0.34, 0.39, M["glow"], bevel=0.0, tags=tags)
    B.bolts("rbolt", [(x, -1.24) for x in (-0.42, 0.42)], 0.33, 0.024, S, tags=tags)


def head(M, T="head", phase=0.0):
    """Casulos + cupula (camada roof_doodads): anel, pes, bracos, casulos inclinados com bocas VAZIAS."""
    tags = (T,)
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    rr = PART["ring_r"]
    B.cyl("ring", 0, 0, 0.04, rr + 0.02, 0.08, KM, axis="Z", verts=72, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, rr - 0.06, 24, 0.13), 0.09, 0.022, S, tags=tags)
    core = [(-0.50, -1.30), (0.50, -1.30), (1.08, -0.86), (1.10, 0.40), (0.80, 0.72), (-0.80, 0.72),
            (-1.10, 0.40), (-1.08, -0.86)]
    B.plate("core", core, 0.06, 0.30, K, slope=0.05, tags=tags)
    _feet(M, tags)
    _rear(M, tags)
    _arms(M, tags)
    _dome(M, tags, phase)
    for sx in (-1, 1):
        _pod(M, tags, sx)


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


def _nose_paint(name, color):
    return B.mat_paint(name, color, rough=0.3, metal=0.15, wear=0.08, grime=0.02, scale=6)


def cell(M, look, T="cell", form="tube", box=None):
    """UM nariz carregado (origem = centro da boca no plano da face), eixo inclinado como o casulo.
    tube: anel/tampa na cor do missil + ogiva clara; torpedo: tampa grande branca cobrindo a face do casulo."""
    tags = (T,)
    band = _band_mat(look)
    antes = _cena()
    if form == "torpedo":
        _torpedo(M, tags, band, box)
        _grupo(antes, "nose", (0, 0, 0), (PITCH - 90.0, 0, 0))
        return
    if form != "tube":
        raise NotImplementedError(f"bs_msl_twin: forma {form} nao existe neste lancador")
    nose = _nose_paint("nose", (0.64, 0.65, 0.66))
    R, L = 0.066, 0.16
    z0, zb = 0.03, 0.064
    if look == "limpet":
        # anel-presilha vermelho mais largo com 4 garras de aco
        B.cyl("n_band", 0, 0, (z0 + zb) / 2, 0.076, zb - z0, band, axis="Z", verts=24, bevel=0.0, tags=tags)
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            B.box(f"n_clamp{k}", 0.074 * math.cos(a), 0.074 * math.sin(a), 0.016, 0.016, z0, zb + 0.022, M["steel"],
                  bevel=0.0, tags=tags)
    elif look == "emp":
        # bobina: 2 aneis azuis separados por aco
        for k, (a, b_, m) in enumerate(((z0, z0 + 0.012, band), (z0 + 0.012, z0 + 0.022, M["steel"]),
                                        (z0 + 0.022, zb, band))):
            B.cyl(f"n_coil{k}", 0, 0, (a + b_) / 2, 0.074 if m is band else 0.069, b_ - a, m, axis="Z", verts=24,
                  bevel=0.0, tags=tags)
    else:
        B.cyl("n_band", 0, 0, (z0 + zb) / 2, 0.072, zb - z0, band if look == "he" else
              M["steel"] if look == "napalm" else M["core_mid"], axis="Z", verts=24, bevel=0.0, tags=tags)
    prof = _ogive(R, L, zb)
    rt, zt = prof[-1]
    if look == "cluster":
        # tampa de petalas amarela (4 petalas com costuras escuras)
        cap = _nose_paint("cap_cluster", BAND["cluster"])
        og = _lathe("n_ogive", prof + [(0.0, zt + 0.002)], cap, tags)
        _lathe("n_core", [(r * 0.75, z) for r, z in prof] + [(0.0, zt)], M["core"], tags)
        B.cut(og, [B.box(f"n_seam{k}", 0, 0, 0.012, 0.3, zb + 0.03, 0.5, M["core"], bevel=0.0) for k in range(1)] +
              [B.box("n_seam1", 0, 0, 0.3, 0.012, zb + 0.03, 0.5, M["core"], bevel=0.0)])
    elif look == "napalm":
        # tampa laranja queimada (ogiva inteira), anel de aco na base
        cap = _nose_paint("cap_napalm", (0.62, 0.075, 0.006))
        _lathe("n_ogive", prof + [(0.0, zt + 0.002)], cap, tags)
    else:
        _lathe("n_ogive", prof + [(0.0, zt + 0.002)], nose, tags)
    B.cyl("n_tip", 0, 0, (zt + zb + L) / 2, rt, zb + L - zt, M["core"], axis="Z", verts=12, bevel=0.0, tags=tags,
          r2=0.002)
    _grupo(antes, "nose", (0, 0, 0), (PITCH - 90.0, 0, 0))


def _torpedo(M, tags, band, box):
    """Torpedo Boto: cassete escuro com 4 travas, anel branco e ogiva branca grande (tampa) cobrindo a face do
    casulo, com costura escura e ponta de aco."""
    white = _nose_paint("torp_white", (0.74, 0.76, 0.80))
    # box = [largura, profundidade] na vista de cima; no plano da face a altura e profundidade / SIN
    bw, bd = (box or [0.65, 0.65])
    hw, hh = bw / 2, bd / 2 / SIN
    B.plate("t_collar", _octo(hw, hh - 0.02, CU * 0.8, CV * 0.8), 0.0, 0.05, M["core_mid"], slope=0.015,
            bevel=0.008, tags=tags)
    for k, (u, v) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        B.box(f"t_lug{k}", u * (hw - 0.06), v * (hh - 0.10), 0.05, 0.08, 0.04, 0.075, M["steel"], bevel=0.006,
              tags=tags)
    R, L = hw - 0.07, 0.30
    sy = 1.32
    B.plate("t_ring", [(x, y * sy) for x, y in B.rpoly(0, 0, 2 * (R + 0.03), 2 * (R + 0.03), 0, chamfer=0.09)],
            0.05, 0.08, band, slope=0.01, bevel=0.004, tags=tags)
    prof = _ogive(R, L, 0.08, tip_r=0.028)
    rt, zt = prof[-1]
    _lathe("t_nose", prof + [(0.0, zt + 0.002)], white, tags, verts=32, sy=sy)
    # costura escura a 35 % da ogiva
    r_s, z_s = prof[3]
    _lathe("t_seam", [(r_s + 0.004, z_s - 0.007), (r_s + 0.004, z_s + 0.007)], M["core"], tags, verts=32, sy=sy)
    B.cyl("t_tip", 0, 0, (zt + 0.08 + L) / 2, rt, 0.08 + L - zt, M["steel"], axis="Z", verts=16, bevel=0.0,
          tags=tags, r2=0.004)


# ============================================================================ overclock
def oc_glow(M, T="oc"):
    """So o que brilha no overclock: olho laranja, grelhas de sopro dos casulos e baia de exaustao em brasa.
    Forcas baixas: acima de ~1.5 o verde satura e o laranja vira amarelo."""
    tags = (T,)
    eye_oc = B.mat_glow("oc_eye", (1.0, 0.16, 0.012), 1.5)
    vent_oc = B.mat_glow("oc_vent", (1.0, 0.18, 0.02), 0.9)
    zf = _visor_z(EYE_Y + 0.045) - 0.035
    eye = _eye_poly(EYE_Y, 0.18, 0.030, k=0.010)
    B.loft("oc_eye", eye, eye, zf, zf + 0.02, eye_oc, bevel=0.0, tags=tags)
    # baia de exaustao traseira
    for i in range(4):
        B.box(f"oc_vent{i}", 0, -1.219 + i * 0.033, 0.56, 0.016, 0.34, 0.35, vent_oc, bevel=0.0, tags=tags)
    # grelhas de sopro dos casulos (mesmo referencial do topo)
    for sx in (-1, 1):
        antes = _cena()
        zt = HH - 0.03 + 0.072
        for i in range(3):
            B.box(f"oc_pv{sx}{i}", 0, -POD_L + 0.135 + i * 0.03, 0.30, 0.014, zt - 0.10, zt - 0.09, vent_oc,
                  bevel=0.0, tags=tags)
        _grupo(antes, f"oc_pod{sx}", (sx * POD_X, POD_Y, Z0), (PITCH, 0, 0))


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto 3x3: placas verdes (bisel duplo), anel da torre, escotilha estreita atras FORA do anel (o anel vai ate
    y = -1.07), respiros com luz nos cantos de tras e respiros em cunha nos cantos da frente."""
    tags = (T,)
    w, h = PART["size"]
    green = B.mat_roof_green()
    K, KM, AM, S = M["core"], M["core_mid"], M["armor_mid"], M["steel"]
    px, py = PART["pivot"][0] - w / 2, h / 2 - PART["pivot"][1]
    rr = PART["ring_r"]
    gap = 0.03
    B.box("deck_under", 0, 0, w, h, -0.05, 0.02, K, bevel=0.0, tags=tags)
    for tx in range(w):
        for ty in range(h):
            cx, cy = tx + 0.5 - w / 2, h / 2 - ty - 0.5
            poly = B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
            _, pnl = B.shard(f"deck{tx}_{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02,
                             tags=tags)
            if (tx + ty) % 2 == 0 and pnl is not None:
                B.cut(pnl, [B.rbox(f"dl{tx}{ty}", cx + 0.18, cy - 0.18, 0.012, 0.5, 0.07, 0.2, K, rot=45, bevel=0.0)])
    B.torus("ringbear", px, py, 0.08, rr + 0.02, 0.055, KM, tags=tags)
    B.cyl("ringhole", px, py, 0.05, rr - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(px, py, rr + 0.11, 32) if abs(x) < w / 2 - 0.06 and abs(y) < h / 2 - 0.06]
    B.bolts("rb", pts, 0.1, 0.022, S, tags=tags)
    # escotilha da tripulacao: estreita, entre o anel e a borda de tras
    hy = -1.30
    B.plate("hatch", B.rpoly(0, hy, 0.46, 0.22, 0, chamfer=0.06), 0.06, 0.10, AM, slope=0.02, tags=tags)
    B.box("hatch_h", 0, hy - 0.04, 0.22, 0.04, 0.10, 0.13, S, bevel=0.01, tags=tags)
    for sx in (-1, 1):
        # canto de tras: respiro com venezianas e luz
        cx, cy = sx * 1.0, -1.0
        v = B.box(f"hvent{sx}", cx, cy, 0.56, 0.34, 0.05, 0.11, KM, bevel=0.01, slope=0.015, tags=tags)
        B.cut(v, [B.box(f"hvc{sx}{i}", cx, cy - 0.11 + i * 0.075, 0.46, 0.03, 0.09, 0.2, K, bevel=0.0)
                  for i in range(4)])
        B.box(f"hled{sx}", cx, cy + 0.23, 0.14, 0.03, 0.06, 0.09, M["glow_dim"], bevel=0.0, tags=tags)
        # canto da frente: respiro escuro em cunha apontando para o canto
        hx, hy2 = sx * 1.16, 1.16
        wedge = [(-0.13, -0.08), (0.13, -0.08), (0.13, 0.01), (0.0, 0.13), (-0.13, 0.01)]
        a = math.radians(-sx * 45)
        wp = [(hx + x * math.cos(a) - y * math.sin(a), hy2 + x * math.sin(a) + y * math.cos(a)) for x, y in wedge]
        fv = B.plate(f"fvent{sx}", wp, 0.05, 0.10, KM, slope=0.015, bevel=0.008, tags=tags)
        B.cut(fv, [B.rbox(f"fvc{sx}{i}", hx + math.sin(a) * (i - 0.5) * 0.055, hy2 - math.cos(a) * (i - 0.5) * 0.055,
                          0.17, 0.02, 0.08, 0.2, K, rot=-sx * 45, bevel=0.0) for i in range(2)])


def floor(M, T="floor"):
    """Piso: anel, postos dos 2 atiradores atras e bercos com misseis nos cantos da frente."""
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
    # bercos de misseis (3 tubos com nariz claro e anel ambar fosco) nos cantos, em diagonal
    nose = _nose_paint("nose", (0.74, 0.75, 0.76))
    for i, (cx, cy) in enumerate(((-1.18, 1.18), (1.18, 1.18), (-1.20, -0.30), (1.20, -0.30))):
        rot = 45 if cx * cy < 0 else -45
        if i >= 2:
            rot = 0
        a = math.radians(rot)
        ux, uy = -math.sin(a), math.cos(a)
        vx, vy = math.cos(a), math.sin(a)
        B.rbox(f"cradle{i}", cx, cy, 0.42, 0.40, 0.0, 0.07, AM, rot=rot, chamfer=0.05, bevel=0.01, tags=tags)
        for k in (-1, 0, 1):
            tx, ty = cx + vx * k * 0.12, cy + vy * k * 0.12
            B.cyl(f"ctube{i}{k}", tx - ux * 0.03, ty - uy * 0.03, 0.13, 0.05, 0.28, KM, axis="Y", verts=12,
                  yaw=rot, tags=tags)
            B.cyl(f"cnose{i}{k}", tx + ux * 0.15, ty + uy * 0.15, 0.13, 0.045, 0.08, nose, axis="Y", verts=12,
                  yaw=rot, r2=0.01, tags=tags)
            B.cyl(f"cband{i}{k}", tx + ux * 0.10, ty + uy * 0.10, 0.13, 0.052, 0.02, M["ember"], axis="Y",
                  verts=12, yaw=rot, bevel=0.0, tags=tags)
    for i, (cx, cy, _r) in enumerate(crew_positions(w, h, 2, pv)):
        x, y = cx - w / 2, h / 2 - cy
        B.box(f"seat{i}", x, y + 0.02, 0.32, 0.30, 0.0, 0.14, A, bevel=0.04, tags=tags)
        side = 1 if x >= px else -1
        B.box(f"console{i}", x + side * 0.30, y + 0.04, 0.12, 0.36, 0.0, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x + side * 0.30, y + 0.04, 0.06, 0.26, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
    # estante do carregador no meio de tras
    B.box("rack", 0, -h / 2 + 0.16, 0.70, 0.22, 0.0, 0.16, AM, bevel=0.01, tags=tags)
    for i in range(3):
        B.box(f"mag{i}", -0.22 + i * 0.22, -h / 2 + 0.16, 0.16, 0.14, 0.16, 0.24, KM, bevel=0.01, tags=tags)
        B.box(f"magled{i}", -0.22 + i * 0.22, -h / 2 + 0.16, 0.10, 0.03, 0.24, 0.26, M["glow_dim"], bevel=0.0,
              tags=tags)
