"""Obuseiro Nuclear de Conves ("Boiuna") - cobra gigante da Amazonia, mesma familia do 76 mm.

Cabeca baixa e larga em "celula quente" blindada: placas de blindagem anti-radiacao em degraus nos
flancos e na traseira, glacis em cabeca de serpente partido pelo berco escuro do cano (olhos verdes em
orbitas rebaixadas), correntes de escamas segmentadas que avancam pelos lados e terminam em presas longas
serrilhadas que se fecham sobre a raiz do cano (mandibula aberta), fileiras de escamas pequenas ao longo
do berco, espinha com janela da celula e trevo nuclear num rebaixo, granadas nucleares grandes (corpo escuro, aneis de aco,
faixa preta com luz verde pequena) nos vaos, respiros verdes, pistoes hidraulicos.
Cano unico de grosso calibre: treno de recuo escuro com recuperadores (copiado no berco da cabeca, para
qualquer ordem de desenho), camisa termica escura com fendas, tubo em escamas que crescem para a frente
(serrilha claro/escuro, entalhes em V na borda), extrator de gases facetado e freio de boca claro proprio:
camara traseira com presas laterais serrilhadas e camara dianteira em focinho de cunha, portas escuras de
lado a lado (so o freio e colares esquentam).
"""

import math

import bmesh
import bpy

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_nuke_howitzer",
    "kind": "gun",
    "size": [5, 6],
    "pivot": [2.5, 2.5],           # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 4.9,             # lado do quadrado do sprite da torre
    "ring_r": 2.20,                # raio do anel da torre no teto/piso
    "accent": "green",
    "collider": 2.2,
    "barrels": {
        "ys": [0.0],               # cano unico
        "root": 1.25,              # pivo -> raiz do cano (o treno fica no berco da cabeca)
        "length": 3.9,             # raiz -> boca (cano longo e grosso)
        "width": 0.90,             # largura do sprite do cano (cabe o freio de boca)
        "pad": 0.80,               # espaco atras da raiz para o recuo de 0.7
        "anim": "recoil",
        "recoil": [0.70, 0.69, 0.66, 0.62, 0.57, 0.51, 0.44, 0.37, 0.30, 0.23, 0.16, 0.10, 0.05, 0.02],
        "heat": [1.0, 0.98, 0.95, 0.91, 0.86, 0.8, 0.73, 0.66, 0.58, 0.5, 0.42, 0.34, 0.26, 0.19, 0.12, 0.06],
        "interval": 0.08,
    },
    "lights": [
        {"at": [0.0, -2.05], "size": 2.4, "color": [110, 255, 70], "z": 0.9},
    ],
    "preview_pattern": "single",
}

BZ = 0.66                          # altura do eixo do cano
ROOT = PART["barrels"]["root"]
PAD = PART["barrels"]["pad"]
SLED = 1.0                         # comprimento do treno de recuo (a partir da raiz)
CH = 0.47                          # meia largura do berco escuro (o cano recua por cima dele)


# ============================================================================ utilidades locais
def _lines(target, name, specs, ztop, mat, w=0.018, depth=0.022):
    """Linhas de painel recortadas num alvo de topo plano: specs = [(x, y, comprimento, rotacao)]."""
    cuts = [B.rbox(f"{name}{i}", x, y, w, ln, ztop - depth, ztop + 0.4, mat, rot=r, bevel=0.0)
            for i, (x, y, ln, r) in enumerate(specs)]
    B.cut(target, cuts)


def _zloft(name, bottom, top, zb, zt, mat, bevel=0.018, tags=()):
    """Prisma como B.loft, mas a altura de cada vertice vem de zb(x, y) (base) e zt(x, y) (topo)."""
    bottom = B._ccw(list(bottom))
    top = B._ccw(list(top))
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vb = [bm.verts.new((x, y, zb(x, y))) for x, y in bottom]
    vt = [bm.verts.new((x, y, zt(x, y))) for x, y in top]
    bm.faces.new(list(reversed(vb)))
    bm.faces.new(vt)
    n = len(bottom)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if bevel > 0:
        md = ob.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = 1
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(30)
    ob.data.materials.append(mat)
    for t in tags:
        ob[t] = True
    return ob


def _zlines(targets, name, specs, zf, top, depth, mat, w=0.021):
    """Linhas de painel em placa de topo inclinado zf: o corte segue a rampa (profundidade constante).
    top = altura do topo do painel acima de zf; specs = [(x, y, comprimento, rotacao)]."""
    for k, t in enumerate(targets):
        if t is None:
            continue
        cuts = []
        for i, (x, y, ln, r) in enumerate(specs):
            p = B.rpoly(x, y, w, ln, r)
            cuts.append(_zloft(f"{name}{k}_{i}", p, p, lambda a, b: zf(a, b) + top - depth,
                               lambda a, b: zf(a, b) + top + 0.4, mat, bevel=0.0))
        B.cut(t, cuts)


def _zslot(name, cx, cy, w, ln, rot, zf, top, depth, M, tags, targets, n=0, strip=0.0):
    """Fenda escura numa placa de topo inclinado (o corte, o fundo preto e as luzes seguem a rampa):
    n pips verdes ao longo da fenda, ou uma fenda de luz continua de largura strip."""
    poly = B.rpoly(cx, cy, w, ln, rot)
    zc = lambda a, b: zf(a, b) + top - depth  # noqa: E731  fundo da fenda
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [_zloft(f"{name}_c{k}", poly, poly, zc, lambda a, b: zf(a, b) + top + 0.4, M["core"],
                             bevel=0.0)])
    _zloft(f"{name}_bed", poly, poly, lambda a, b: zc(a, b) - 0.012, lambda a, b: zc(a, b) + 0.004, M["black"],
           bevel=0.0, tags=tags)
    a = math.radians(rot)
    ux, uy = -math.sin(a), math.cos(a)
    if strip:
        g = B.rpoly(cx, cy, strip, ln * 0.74, rot)
        _zloft(f"{name}_glow", g, g, zc, lambda a_, b_: zc(a_, b_) + 0.01, M["glow_dim"], bevel=0.0, tags=tags)
    for i in range(n):
        s = ((i + 0.5) / n - 0.5) * ln
        g = B.rpoly(cx + ux * s, cy + uy * s, w * 0.55, ln / n * 0.55, rot)
        _zloft(f"{name}_pip{i}", g, g, zc, lambda a_, b_: zc(a_, b_) + 0.012, M["glow"], bevel=0.0, tags=tags)


def _ramp(y0, z0, y1, z1):
    """Altura linear em y (topo inclinado): z0 em y0, z1 em y1."""
    k = (z1 - z0) / (y1 - y0)
    return lambda x, y: z0 + (y - y0) * k


def _sshard(name, poly, z0, zf, mat, slope=0.08, groove=0.035, panel_h=0.03, tags=()):
    """Placa com bisel duplo (como B.shard) e topo inclinado zf(x, y)."""
    s = B.safe_offset(poly, slope)
    a = _zloft(name, poly, B.offset_poly(poly, s), z0 if callable(z0) else (lambda x, y: z0), zf, mat, tags=tags)
    d = slope + groove
    inner = B.robust_offset(poly, d)
    if inner is None or B.robust_offset(poly, d + 0.012) is None:
        return a, None
    s2 = B.safe_offset(inner, 0.012)
    b = _zloft(name + "_pnl", inner, B.offset_poly(inner, s2), lambda x, y: zf(x, y) - 0.004,
               lambda x, y: zf(x, y) + panel_h, mat, bevel=0.008, tags=tags)
    return a, b


def _aramp(p0, p1, z0, z1):
    """Altura linear ao longo do eixo p0 -> p1: z0 em p0, z1 em p1."""
    ux, uy = p1[0] - p0[0], p1[1] - p0[1]
    L2 = (ux * ux + uy * uy) or 1e-9
    return lambda x, y: z0 + (z1 - z0) * ((x - p0[0]) * ux + (y - p0[1]) * uy) / L2


def _side(sx):
    return (lambda p: p) if sx < 0 else Mo.mirror


def _mx(sx):
    """Espelha um ponto (lado direito) ou devolve igual (lado esquerdo)."""
    return (lambda p: p) if sx < 0 else (lambda p: (-p[0], p[1]))


def _sled(M, tags, y0, z, pre):
    """Treno de recuo escuro com recuperadores (igual no cano e no berco da cabeca: qualquer ordem de
    desenho mostra a mesma coisa)."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    y1 = y0 + SLED
    body = [(-0.22, y0), (0.22, y0), (0.30, y0 + 0.10), (0.30, y1 - 0.08), (0.24, y1), (-0.24, y1),
            (-0.30, y1 - 0.08), (-0.30, y0 + 0.10)]
    B.plate(f"{pre}sled", body, z - 0.24, z + 0.18, KM, slope=0.08, tags=tags)
    # bloco deslizante central (dorso do treno) com sulco preto
    top = [(-0.12, y0 + 0.14), (0.12, y0 + 0.14), (0.15, y0 + 0.22), (0.15, y1 - 0.10), (0.10, y1 - 0.04),
           (-0.10, y1 - 0.04), (-0.15, y1 - 0.10), (-0.15, y0 + 0.22)]
    t = B.plate(f"{pre}slide", top, z + 0.16, z + 0.25, K, slope=0.03, tags=tags)
    B.cut(t, [B.box(f"{pre}slidec", 0, (y0 + y1) / 2 + 0.04, 0.035, SLED - 0.36, z + 0.23, z + 0.5, K,
                    bevel=0.0)])
    B.box(f"{pre}band", 0, y1 - 0.07, 0.56, 0.05, z - 0.20, z + 0.20, S, bevel=0.008, tags=tags)
    # culatra: bloco escalonado com aro de aco
    B.box(f"{pre}breech", 0, y0 + 0.07, 0.36, 0.12, z - 0.16, z + 0.22, K, bevel=0.012, tags=tags)
    B.box(f"{pre}breechr", 0, y0 + 0.15, 0.40, 0.035, z - 0.14, z + 0.215, S, bevel=0.006, tags=tags)
    for sx in (-1, 1):
        # recuperadores hidraulicos pesados (cilindro escuro + haste de aco)
        B.cyl(f"{pre}recup{sx}", sx * 0.35, y0 + 0.36, z - 0.02, 0.07, 0.56, KM, axis="Y", verts=10, bevel=0.008,
              tags=tags)
        B.cyl(f"{pre}recupr{sx}", sx * 0.35, y0 + 0.80, z - 0.02, 0.042, 0.34, S, axis="Y", verts=10, bevel=0.004,
              tags=tags)
        for j, y in enumerate((y0 + 0.10, y0 + 0.62, y1 - 0.03)):
            B.cyl(f"{pre}recupc{sx}{j}", sx * 0.35, y, z - 0.02, 0.078 if j < 2 else 0.06, 0.04, S if j else K,
                  axis="Y", verts=10, bevel=0.005, tags=tags)


def _trefoil(name, cx, cy, z, r0, r1, mat, tags):
    """Trevo nuclear: 3 setores de 60 graus (pontas para frente e para tras) + ponto central."""
    for k in range(3):
        a0 = math.radians(90 + k * 120 - 30)
        pts = [(cx + math.cos(a0 + i / 6 * math.radians(60)) * r1, cy + math.sin(a0 + i / 6 * math.radians(60)) * r1)
               for i in range(7)]
        pts += [(cx + math.cos(a0 + math.radians(60)) * r0, cy + math.sin(a0 + math.radians(60)) * r0),
                (cx + math.cos(a0) * r0, cy + math.sin(a0) * r0)]
        B.loft(f"{name}{k}", pts, pts, z, z + 0.008, mat, bevel=0.0, tags=tags)
    B.cyl(f"{name}c", cx, cy, z + 0.004, r0 * 0.6, 0.008, mat, axis="Z", verts=10, bevel=0.0, tags=tags)


# ============================================================================ cabeca
# glacis (metade esquerda): focinho recuado para a boca do berco e as presas ficarem a frente
GLACIS = [(-0.70, 0.22), (-1.12, 0.22), (-1.40, 0.50), (-1.40, 1.02), (-1.16, 1.58), (-0.92, 1.98),
          (-0.76, 2.06), (-0.70, 2.00)]
# borda externa do glacis em 3 trechos retos (a corrente de escamas corre colada nela, quinas vivas)
JAW = [(-1.40, 0.44), (-1.40, 1.02), (-1.16, 1.58), (-0.92, 1.98)]
# placa baixa do flanco: chifre frontal longo e agudo, um degrau grande na borda, quina traseira chanfrada
FLANK_A = [(-1.52, -1.50), (-1.52, 0.22), (-1.64, 0.36), (-1.98, 0.36), (-2.08, 0.50), (-2.14, 1.26),
           (-2.40, 0.84), (-2.40, -0.52), (-2.26, -0.72), (-2.26, -1.16), (-1.72, -1.70), (-1.64, -1.70)]
S_END = 1.32                       # comprimento das 3 escamas da corrente (depois vem a presa)


def _offset_open(pts, d):
    """Desloca uma polilinha aberta para a esquerda do avanco (para fora) por d, com esquadria."""
    nr = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        L = math.hypot(x2 - x1, y2 - y1) or 1e-9
        nr.append((-(y2 - y1) / L, (x2 - x1) / L))
    out = [(pts[0][0] + nr[0][0] * d, pts[0][1] + nr[0][1] * d)]
    for i in range(1, len(pts) - 1):
        n1, n2 = nr[i - 1], nr[i]
        k = d / (1 + n1[0] * n2[0] + n1[1] * n2[1])
        out.append((pts[i][0] + (n1[0] + n2[0]) * k, pts[i][1] + (n1[1] + n2[1]) * k))
    out.append((pts[-1][0] + nr[-1][0] * d, pts[-1][1] + nr[-1][1] * d))
    return out


def _band(cl, w):
    """Faixa de largura 2w em torno da linha central cl: pt(s, k) com k = -1 dentro, 0 centro, +1 fora."""
    acc = [0.0]
    for (x1, y1), (x2, y2) in zip(cl, cl[1:]):
        acc.append(acc[-1] + math.hypot(x2 - x1, y2 - y1))
    E = {-1: _offset_open(cl, -w), 0: cl, 1: _offset_open(cl, w)}

    def pt(s, k):
        s = max(0.0, min(acc[-1], s))
        i = min(len(cl) - 2, next((j for j in range(len(acc) - 1) if acc[j + 1] >= s), len(cl) - 2))
        t = (s - acc[i]) / ((acc[i + 1] - acc[i]) or 1e-9)
        (x1, y1), (x2, y2) = E[k][i], E[k][i + 1]
        return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

    def corners(sa, sb, k):
        return [E[k][i] for i in range(1, len(cl) - 1) if sa < acc[i] < sb]

    return pt, corners


def chain_polys(gap0=0.09, w=0.21, n=3, gap=0.06, chev=0.13, s_end=S_END):
    """Corrente de escamas (lado esquerdo) colada na borda do glacis, com juntas em V (a ponta de cada
    escama encaixa no entalhe da seguinte) e quinas vivas nos trechos retos; a ultima peca e a presa:
    lamina longa que dobra para dentro e termina em ponta ao lado da boca do berco."""
    cl = _offset_open(JAW, gap0 + w)
    pt, corners = _band(cl, w)
    seg = s_end / n
    out = []
    for i in range(n):
        sa, sb = i * seg + gap / 2, (i + 1) * seg - gap / 2
        poly = ([pt(sa, -1), pt(sa + chev, 0), pt(sa, 1)] + corners(sa, sb, 1) +
                [pt(sb, 1), pt(sb + chev, 0), pt(sb, -1)] + corners(sa, sb, -1)[::-1])
        mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)  # noqa: E731
        out.append((poly, mid(pt(sa, -1), pt(sa, 1)), mid(pt(sb, -1), pt(sb, 1))))
    sa = s_end + gap / 2
    # presa: entalhe em V atras, borda externa serrilhada (dente para a frente) ate a ponta, borda interna
    # rente ao focinho
    fang = [pt(sa, -1), pt(sa + chev, 0), pt(sa, 1), (-1.56, 2.06), (-1.32, 2.245), (-1.20, 2.29), (-1.175, 2.235),
            (-1.04, 2.345), (-0.84, 2.385), FANG_TIP, (-0.66, 2.27), (-0.82, 2.17), (-1.00, 2.08)]
    out.append((fang, ((fang[0][0] + fang[2][0]) / 2, (fang[0][1] + fang[2][1]) / 2), FANG_TIP))
    return out


FANG_TIP = (-0.545, 2.42)


def _eye(name, cx, cy, rot, zf, M, tags):
    """Olho da serpente: losango alongado preto (rebaixo) seguindo a rampa do glacis, fenda verde."""
    oval = B.rpoly(0, 0, 0.15, 0.42, 0, chamfer=0.07)
    lens = B.rpoly(0, 0, 0.04, 0.30, 0, chamfer=0.015)
    pupil = B.rpoly(0, 0.06, 0.05, 0.09, 0, chamfer=0.012)
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    tr = lambda poly: [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in poly]  # noqa: E731
    rim = _zloft(f"{name}_rim", tr(B.rpoly(0, 0, 0.21, 0.50, 0, chamfer=0.095)),
                 tr(B.rpoly(0, 0, 0.19, 0.48, 0, chamfer=0.09)), lambda x, y: zf(x, y) - 0.02,
                 lambda x, y: zf(x, y) + 0.045, M["core_mid"], bevel=0.006, tags=tags)
    # orbita rebaixada: o aro escuro fica acima da lente (luz so dentro do rebaixo)
    B.cut(rim, [_zloft(f"{name}_sock", tr(oval), tr(oval), lambda x, y: zf(x, y) + 0.015,
                       lambda x, y: zf(x, y) + 0.3, M["core"], bevel=0.0)])
    _zloft(f"{name}_bed", tr(oval), tr(oval), lambda x, y: zf(x, y) + 0.008, lambda x, y: zf(x, y) + 0.02,
           M["black"], bevel=0.0, tags=tags)
    _zloft(f"{name}_lens", tr(lens), tr(lens), lambda x, y: zf(x, y) + 0.02, lambda x, y: zf(x, y) + 0.026,
           M["glow_dim"], bevel=0.0, tags=tags)
    _zloft(f"{name}_pupil", tr(pupil), tr(pupil), lambda x, y: zf(x, y) + 0.02, lambda x, y: zf(x, y) + 0.03,
           M["glow"], bevel=0.0, tags=tags)


def _shell(name, x, y, r, M, tags, z=0.56):
    """Granada nuclear deitada (base em y, ponta para a frente): corpo escuro contornado por aneis de
    aco, faixa preta rebaixada com uma luz verde curta no topo, ogiva clara sobre base de aco larga."""
    K, KM, S, AM = M["core"], M["core_mid"], M["steel"], M["armor_mid"]
    body, tip = 0.34, 0.16
    B.cyl(f"{name}base", x, y + 0.018, z, r + 0.012, 0.036, S, axis="Y", verts=8, bevel=0.005, tags=tags)
    B.cyl(f"{name}body", x, y + 0.036 + body / 2, z, r, body, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
    yb = y + 0.036 + body * 0.40
    B.cyl(f"{name}band", x, yb, z, r + 0.002, 0.034, M["black"], axis="Y", verts=8, bevel=0.0, tags=tags)
    B.box(f"{name}led", x, yb, 0.07, 0.016, z + r - 0.03, z + r + 0.006, M["glow_dim"], bevel=0.0, tags=tags)
    B.cyl(f"{name}shoulder", x, y + 0.036 + body - 0.03, z, r + 0.008, 0.03, S, axis="Y", verts=8, bevel=0.004,
          tags=tags)
    B.cyl(f"{name}ogb", x, y + 0.036 + body + 0.012, z, r + 0.004, 0.024, S, axis="Y", verts=8, bevel=0.004,
          tags=tags)
    B.cyl(f"{name}tip", x, y + 0.036 + body + 0.024 + tip / 2, z, r - 0.004, tip, AM, axis="Y", verts=8, bevel=0.0,
          r2=0.035, tags=tags)
    return y + 0.036 + body + 0.024 + tip


def head(M, T="head", phase=0.0):
    """Cabeca: celula quente blindada com glacis em cabeca de serpente e correntes de escamas."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    BLK, G, GD = M["black"], M["glow"], M["glow_dim"]

    # ---------------------------------------------------------------- anel e nucleo escuro (caixao chanfrado)
    B.cyl("ring", 0, 0, 0.04, 2.24, 0.08, KM, axis="Z", verts=96, bevel=0.01, tags=tags)
    core = [(-1.10, -2.40), (1.10, -2.40), (2.36, -1.14), (2.36, 1.04), (1.30, 2.26), (-1.30, 2.26),
            (-2.36, 1.04), (-2.36, -1.14)]
    B.plate("core", core, 0.06, 0.38, K, slope=0.05, tags=tags)
    house = [(-0.92, -1.80), (0.92, -1.80), (1.04, -1.68), (1.04, 0.20), (0.88, 0.36), (-0.88, 0.36),
             (-1.04, 0.20), (-1.04, -1.68)]
    B.plate("house", house, 0.36, 0.84, KM, slope=0.06, tags=tags)

    # ---------------------------------------------------------------- berco escuro do cano + treno
    y0c = ROOT - PAD
    crad = [(-CH + 0.04, y0c), (CH - 0.04, y0c), (CH, y0c + 0.08), (CH, 2.24), (CH - 0.10, 2.36),
            (-CH + 0.10, 2.36), (-CH, 2.24), (-CH, y0c + 0.08)]
    c = B.plate("cradle", crad, 0.30, 0.46, KM, slope=0.04, tags=tags)
    B.cut(c, [B.box("crad_c", 0, (y0c + 2.30) / 2, 0.60, 2.30 - y0c - 0.16, 0.40, 0.9, K, bevel=0.0)])
    B.box("cradbed", 0, (y0c + 2.30) / 2, 0.60, 2.30 - y0c - 0.16, 0.395, 0.405, BLK, bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"cradled{i}", 0, y0c + 0.14 + i * 0.09, 0.10, 0.026, 0.40, 0.41, GD if i < 2 else BLK, bevel=0.0,
              tags=tags)
    _sled(M, tags, ROOT, BZ, "h_")
    # boca do berco (colar escuro de onde sai o tubo)
    B.cyl("mouth", 0, 2.30, BZ - 0.02, 0.33, 0.14, KM, axis="Y", verts=8, bevel=0.012, tags=tags)
    B.cyl("mouthr", 0, 2.24, BZ - 0.02, 0.338, 0.035, S, axis="Y", verts=8, bevel=0.006, tags=tags)

    # ---------------------------------------------------------------- flancos: placas anti-radiacao em degraus
    flank_b = [(-1.66, -0.48), (-1.66, 0.06), (-1.80, 0.26), (-1.96, 0.26), (-2.20, -0.02), (-2.20, -0.36),
               (-2.08, -0.48)]
    flank_c = [(-1.66, -1.48), (-1.66, -0.80), (-2.04, -0.80), (-2.14, -0.90), (-2.14, -1.14), (-1.80, -1.48)]
    rear = [(-0.86, -1.84), (-1.64, -1.84), (-1.12, -2.36), (-0.86, -2.36)]
    rear_b = [(-0.92, -1.92), (-1.40, -1.92), (-1.22, -2.10), (-0.92, -2.10)]
    for side, sx in (("L", -1), ("R", 1)):
        f = _side(sx)
        fa, fp = B.shard(f"flank_a{side}", f(FLANK_A), 0.36, 0.80, A, slope=0.08, groove=0.05, panel_h=0.03,
                         tags=tags)
        fb, fbp = B.shard(f"flank_b{side}", f(flank_b), 0.80, 1.04, A, slope=0.07, groove=0.04, panel_h=0.025,
                          tags=tags)
        # camadas da blindagem (sulcos transversais)
        _lines(fbp, f"fbl{side}", [(sx * 1.90, -0.18, 0.40, 90), (sx * 1.90, -0.30, 0.40, 90)], 1.065, K)
        # pistao hidraulico transversal no vao entre os dois blocos (empurra a blindagem)
        B.box(f"ramtr{side}", sx * 1.92, -0.64, 0.56, 0.16, 0.78, 0.80, BLK, bevel=0.0, tags=tags)
        B.cyl(f"ram{side}", sx * 2.04, -0.64, 0.86, 0.065, 0.30, KM, axis="X", verts=10, bevel=0.008, tags=tags)
        B.cyl(f"ramr{side}", sx * 1.78, -0.64, 0.86, 0.038, 0.26, S, axis="X", verts=10, bevel=0.004, tags=tags)
        for j, xx in enumerate((2.17, 1.90)):
            B.cyl(f"ramc{side}{j}", sx * xx, -0.64, 0.86, 0.072, 0.035, S, axis="X", verts=10, bevel=0.004,
                  tags=tags)
        fc, fcp = B.shard(f"flank_c{side}", f(flank_c), 0.80, 1.08, A, slope=0.07, groove=0.035, panel_h=0.025,
                          tags=tags)
        Mo.slot_with_pips(f"fslot{side}", sx * 1.90, -1.30, -0.96, 0.065, 1.105, 3, M, tags, target=[fc, fcp],
                          depth=0.04)
        B.bolts(f"fbolt{side}", [(sx * 2.24, 0.20), (sx * 2.24, 0.46)], 0.838, 0.022, S, tags=tags)
        # placas traseiras (duas camadas) em cunha, com fenda de pips horizontal
        ra, rp = B.shard(f"rear{side}", f(rear), 0.36, 0.72, A, slope=0.08, groove=0.035, panel_h=0.03, tags=tags)
        rb, rbp = B.shard(f"rearb{side}", f(rear_b), 0.75, 0.86, A, slope=0.04, groove=0.022, panel_h=0.018,
                          tags=tags)
        Mo.slot_with_pips(f"rslot{side}", -2.00, sx * 1.22, sx * 1.00, 0.06, 0.878, 2, M, tags, target=[rb, rbp],
                          depth=0.035, vertical=False)
        B.bolts(f"rbolt{side}", [(sx * 1.02, -2.22)], 0.758, 0.02, S, tags=tags)

    # ---------------------------------------------------------------- correntes de escamas + presas (mandibula)
    polys = chain_polys()
    for side, sx in (("L", -1), ("R", 1)):
        f = _side(sx)
        m = _mx(sx)
        for k, (poly, back, front) in enumerate(polys):
            fang = k == len(polys) - 1
            back, front = m(back), m(front)
            zb = 0.94 - k * 0.025
            # topo inclinado: cada escama desce para a frente (escamas sobrepostas); a presa desce mais
            drop = 0.22 if fang else 0.11
            zf = _aramp(back, front, zb, zb - drop)
            sa, sp = _sshard(f"scale{side}{k}", f(poly), 0.36, zf, A, slope=0.07, groove=0.03, panel_h=0.025,
                             tags=tags)
            ux, uy = front[0] - back[0], front[1] - back[1]
            if fang:
                # fenda verde ao longo da presa (como a lamina do 76 mm), seguindo a rampa
                p0, p1 = m((-1.36, 1.99)), m((-0.97, 2.225))
                gx, gy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
                rot = math.degrees(math.atan2(-(p1[0] - p0[0]), p1[1] - p0[1]))
                ln = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                _zslot(f"fang{side}", gx, gy, 0.07, ln, rot, zf, 0.025, 0.06, M, tags, [sa, sp], strip=0.022)
            else:
                # quilha: linha de painel ao longo da escama (corte segue a rampa)
                cx, cy = back[0] + ux * 0.5, back[1] + uy * 0.5
                rot = math.degrees(math.atan2(-ux, uy))
                _zlines([sa, sp], f"scl{side}{k}", [(cx, cy, 0.22, rot)], zf, 0.025, 0.07, K)
        # pistao hidraulico pesado entre o chifre do flanco e a corrente
        B.cyl(f"piston{side}", sx * 2.00, 0.84, 0.56, 0.042, 0.50, S, axis="Y", verts=10, yaw=sx * -4, tags=tags)
        B.cyl(f"pistonb{side}", sx * 1.99, 0.52, 0.56, 0.068, 0.24, KM, axis="Y", verts=10, yaw=sx * -4, tags=tags)
        B.cyl(f"pistonr{side}", sx * 1.995, 0.64, 0.56, 0.075, 0.03, S, axis="Y", verts=10, yaw=sx * -4, tags=tags)

    # ---------------------------------------------------------------- glacis em cabeca de serpente (partido)
    gz = _ramp(0.22, 1.20, 2.40, 0.80)
    # fileira de escamas pequenas ao longo do berco (garras que seguram a raiz do cano)
    rowc = [(-0.585, 0.32), (-0.585, 2.30)]
    pt, _ = _band(rowc, 0.065)
    nrow, rgap, rchev = 4, 0.05, 0.07
    rseg = 1.66 / nrow
    for k in range(nrow):
        sa_, sb_ = k * rseg + rgap / 2, (k + 1) * rseg - rgap / 2
        poly = [pt(sa_, -1), pt(sa_ + rchev, 0), pt(sa_, 1), pt(sb_, 1), pt(sb_ + rchev, 0), pt(sb_, -1)]
        yb_, yf_ = 0.32 + sa_, 0.32 + sb_ + rchev
        zr = _ramp(yb_, 0.86 - k * 0.02, yf_, 0.78 - k * 0.02)
        for side, sx in (("L", -1), ("R", 1)):
            _sshard(f"rowsc{side}{k}", _side(sx)(poly), 0.36, zr, A, slope=0.035, groove=0.02, panel_h=0.02,
                    tags=tags)
    for side, sx in (("L", -1), ("R", 1)):
        f = _side(sx)
        ga, gp = _sshard(f"glacis{side}", f(GLACIS), 0.36, gz, A, slope=0.08, groove=0.045, panel_h=0.03, tags=tags)
        # juntas entre as escamas da cabeca (vao escuro ate o nucleo)
        for t in (ga, gp):
            B.cut(t, [B.rbox(f"gj{side}{t.name[-3:]}{i}", sx * x, y, 0.065, ln, 0.30, 1.6, K, rot=90 + sx * -r,
                             bevel=0.0) for i, (x, y, ln, r) in enumerate(((1.05, 0.80, 0.9, 11),
                                                                            (0.98, 1.55, 0.8, 16)))])
        # linhas de painel (seguem a rampa) e fenda de pips no focinho
        _zlines([ga, gp], f"gpl{side}", [(sx * 1.17, 1.30, 0.22, sx * 23), (sx * 0.82, 1.90, 0.12, sx * 31)],
                gz, 0.03, 0.07, K)
        _zslot(f"gslot{side}", sx * 0.90, 1.74, 0.06, 0.24, sx * 31, gz, 0.03, 0.04, M, tags, [ga, gp], n=2)
        _eye(f"eye{side}", sx * 1.02, 1.17, sx * 30, lambda x, y: gz(x, y) + 0.03, M, tags)
        # escama de sobrancelha (tier de cima, atras do olho), apoiada na rampa do glacis
        brow = [(-0.76, 0.34), (-1.10, 0.34), (-1.28, 0.52), (-1.24, 0.64), (-0.76, 0.72)]
        _sshard(f"brow{side}", f(brow), lambda x, y: gz(x, y) - 0.01, lambda x, y: gz(x, y) + 0.10, A, slope=0.05,
                groove=0.026, panel_h=0.02, tags=tags)
        for i, (bx, by) in enumerate(((0.90, 1.06), (1.22, 0.96))):
            B.bolts(f"gbolt{side}{i}", [(sx * bx, by)], gz(bx, by) + 0.038, 0.02, S, tags=tags)

    # ---------------------------------------------------------------- vaos: granadas nucleares
    for side, sx in (("L", -1), ("R", 1)):
        x = sx * 1.28
        # bandeja de aco (as granadas escuras se destacam) com fendas entre elas
        tray = B.plate(f"tray{side}", B.rpoly(x, -0.69, 0.40, 1.90, 0, chamfer=0.05), 0.36, 0.41, S, slope=0.015,
                       bevel=0.006, tags=tags)
        B.cut(tray, [B.box(f"trayc{side}{i}", x, y, 0.30, 0.04, 0.39, 0.5, K, bevel=0.0)
                     for i, y in enumerate((-1.00, -0.40))])
        for j in (-1, 1):
            B.box(f"srail{side}{j}", x + j * 0.185, -0.69, 0.028, 1.84, 0.40, 0.53, S, bevel=0.006, tags=tags)
        for i, y in enumerate((-1.58, -0.98, -0.38)):
            _shell(f"shell{side}{i}", x, y, 0.15, M, tags)

    # ---------------------------------------------------------------- celula quente: paredes + espinha
    wall = [(-0.42, -1.66), (-0.80, -1.66), (-0.94, -1.52), (-0.94, -0.34), (-0.66, 0.12), (-0.46, 0.12),
            (-0.42, 0.06)]
    wcap = [(-0.50, -1.50), (-0.78, -1.50), (-0.86, -1.42), (-0.86, -0.80), (-0.70, -0.62), (-0.50, -0.62)]
    for side, sx in (("L", -1), ("R", 1)):
        f = _side(sx)
        wa, wp = B.shard(f"wall{side}", f(wall), 0.84, 1.10, A, slope=0.08, groove=0.035, panel_h=0.025, tags=tags)
        for t in (wa, wp):
            B.cut(t, [B.rbox(f"wgap{side}{t.name[-3:]}", sx * 0.68, -0.50, 0.07, 0.70, 0.80, 1.6, K, rot=90 + sx * 12,
                             bevel=0.0)])
        _lines(wp, f"wpl{side}", [(sx * 0.62, -0.20, 0.30, sx * -30)], 1.135, K, depth=0.03)
        ca, cp = B.shard(f"wcap{side}", f(wcap), 1.12, 1.22, A, slope=0.04, groove=0.022, panel_h=0.018,
                         tags=tags)
        Mo.slot_with_pips(f"wslot{side}", sx * 0.69, -1.36, -0.84, 0.06, 1.238, 3, M, tags, target=[ca, cp],
                          depth=0.035)
    spine = [(-0.30, -1.74), (0.30, -1.74), (0.36, -1.64), (0.36, 0.08), (0.16, 0.42), (-0.16, 0.42),
             (-0.36, 0.08), (-0.36, -1.64)]
    sa, sp = B.shard("spine", spine, 0.84, 1.32, A, slope=0.08, groove=0.03, panel_h=0.025, tags=tags)
    sp2 = [(-0.21, -1.42), (0.21, -1.42), (0.25, -1.32), (0.25, 0.04), (0.10, 0.28), (-0.10, 0.28),
           (-0.25, 0.04), (-0.25, -1.32)]
    s2 = B.plate("spine2", sp2, 1.34, 1.44, A, slope=0.035, tags=tags)
    # janela da celula (sensor) com fenda verde
    win = [(-0.13, -0.10), (0.13, -0.10), (0.13, 0.02), (0.045, 0.17), (-0.045, 0.17), (-0.13, 0.02)]
    B.cut(s2, [B.loft("win_cut", win, win, 1.40, 1.8, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 1.395, 1.405, BLK, bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, 0.01, 0.18, 0.03, 1.40, 1.412, G, bevel=0.0, tags=tags)
    # trevo nuclear num rebaixo octogonal escuro
    oc = B.rpoly(0, -0.88, 0.38, 0.38, 0, chamfer=0.11)
    B.cut(s2, [B.loft("tre_cut", oc, oc, 1.41, 1.8, K, bevel=0.0)])
    B.loft("tre_bed", oc, oc, 1.405, 1.415, BLK, bevel=0.0, tags=tags)
    _trefoil("tre", 0, -0.88, 1.415, 0.045, 0.15, GD, tags)
    _lines(s2, "s2l", [(0.0, -0.42, 0.24, 90), (0.0, -1.30, 0.24, 90)], 1.44, K)
    _lines(sp, "spl", [(-0.30, -0.80, 0.56, 0), (0.30, -0.80, 0.56, 0)], 1.345, K)

    # ---------------------------------------------------------------- baia de exaustao traseira (verde)
    B.box("vent_bay", 0, -2.10, 1.56, 0.56, 0.22, 0.40, BLK, bevel=0.0, tags=tags)
    for i in range(10):
        B.box(f"louver{i}", 0, -2.34 + i * 0.05, 1.50, 0.022, 0.32, 0.41, KM, bevel=0.004, tags=tags)
    for j, x in enumerate((-0.40, 0.40)):
        B.box(f"vrib{j}", x, -2.10, 0.05, 0.54, 0.30, 0.44, S, bevel=0.008, tags=tags)
    for i in range(5):
        B.box(f"vent_pip{i}", -0.56 + i * 0.28, -1.86, 0.08, 0.028, 0.38, 0.44, G, bevel=0.0, tags=tags)
    B.box("vent_lip", 0, -1.82, 1.54, 0.025, 0.38, 0.50, BLK, bevel=0.0, tags=tags)
    B.bolts("vbolt", [(-0.70, -2.34), (0.70, -2.34)], 0.42, 0.02, S, tags=tags)


# ============================================================================ cano
def _chamber(name, ya, yb, z, A, K, hot, tags, hw, tip, fw, ports, back=0.10, extra=()):
    """Camara do freio de boca (linguagem do 76 mm): corpo claro facetado que aponta para a frente,
    portas transversais escuras de lado a lado (serrilha limpa nas laterais) sobre um miolo escuro."""
    poly = [(-hw + back, ya), (hw - back, ya), (hw, ya + back), (hw, yb - tip), (fw, yb), (-fw, yb), (-hw, yb - tip),
            (-hw, ya + back)]
    ch = B.plate(name, poly, z - 0.20, z + 0.20, A, slope=0.05, tags=hot)
    cuts = [B.box(f"{name}_p{i}", 0, y, hw * 2 + 0.04, 0.06, z + 0.02, z + 0.4, K, bevel=0.0)
            for i, y in enumerate(ports)]
    B.cut(ch, cuts + list(extra))
    # miolo escuro (fundo das portas e do furo da boca)
    inner = B.offset_poly(poly, 0.04)
    B.loft(f"{name}_core", inner, inner, z - 0.16, z + 0.04, K, bevel=0.0, tags=tags)
    return ch


def barrel(M, L=3.9, T="barrel", phase=0.0):
    """Cano do obuseiro com raiz (y=0) e boca (y=L), centrado em x=0, altura BZ."""
    tags = (T,)
    hot = (T, "hot")  # so freio, presas do freio e colares da boca brilham de calor
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    BLK = M["black"]
    z = BZ
    _sled(M, tags, 0.0, z, "b_")
    ra = L - 0.88                          # inicio do freio de boca
    # nucleo escuro do tubo (aparece nos aneis entre as escamas)
    B.cyl("b_core", 0, (SLED - 0.05 + ra) / 2, z, 0.23, ra - SLED + 0.05, K, axis="Y", verts=16, tags=tags)
    # camisa termica escura que sai da boca do berco, com fendas transversais (sem brasa: o calor e so no freio)
    j0, j1 = SLED - 0.02, 1.40
    jk = B.cyl("b_jacket", 0, (j0 + j1) / 2, z, 0.31, j1 - j0, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
    B.cut(jk, [B.box(f"b_jc{i}", 0, 1.15 + i * 0.065, 0.46, 0.032, z + 0.17, z + 0.5, K, bevel=0.0)
               for i in range(4)])
    B.box("b_jbed", 0, 1.248, 0.46, 0.24, z + 0.15, z + 0.172, BLK, bevel=0.0, tags=tags)
    B.cyl("b_jcol", 0, 1.42, z, 0.322, 0.04, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    # tubo em escamas: cada segmento cresce para a frente e termina num degrau sobre um anel escuro
    segs = [(1.45, 1.80, 0.272, 0.335), (2.28, 2.60, 0.262, 0.325), (2.64, 2.93, 0.252, 0.315)]
    rings = [(1.82, 0.27), (2.62, 0.25), (2.95, 0.25)]
    fe0, fe1 = 1.92, 2.16                  # extrator de gases (bojo facetado) entre a 1a e a 2a escama
    tube = []
    for i, (a, b, r0, r1) in enumerate(segs):
        sg = B.cyl(f"b_seg{i}", 0, (a + b) / 2, z, r0, b - a, A, axis="Y", verts=8, bevel=0.008, tags=tags, r2=r1)
        # entalhes em V na borda da frente (pontas de escama sobrepostas; o nucleo escuro aparece no fundo)
        B.cut(sg, [B.rbox(f"b_segv{i}{sx}", sx * 0.165, b, 0.085, 0.085, z + 0.08, z + 0.6, K, rot=45, bevel=0.0)
                   for sx in (-1, 1)])
        tube.append(sg)
    for i, (y, r) in enumerate(rings):
        tube.append(B.cyl(f"b_ring{i}", 0, y, z, r, 0.04, KM, axis="Y", verts=8, bevel=0.004,
                          tags=hot if i == len(rings) - 1 else tags))
    tube.append(B.cyl("b_fume", 0, (fe0 + fe1) / 2, z, 0.37, fe1 - fe0, A, axis="Y", verts=8, bevel=0.014,
                      tags=tags))
    tube.append(B.cyl("b_fumecone0", 0, fe0 - 0.04, z, 0.29, 0.08, A, axis="Y", verts=8, bevel=0.0, tags=tags,
                      r2=0.37))
    tube.append(B.cyl("b_fumecone1", 0, fe1 + 0.04, z, 0.37, 0.08, A, axis="Y", verts=8, bevel=0.0, tags=tags,
                      r2=0.28))
    for i, y in enumerate((fe0 + 0.05, fe1 - 0.05)):
        tube.append(B.cyl(f"b_fumeband{i}", 0, y, z, 0.378, 0.03, AM, axis="Y", verts=8, bevel=0.004, tags=tags))
    tube.append(B.cyl("b_ring3", 0, 2.26, z, 0.25, 0.04, KM, axis="Y", verts=8, bevel=0.004, tags=tags))
    # canal escuro continuo no topo do tubo (do colar da camisa ate o freio)
    c0, c1 = 1.47, ra - 0.06
    for o in tube:
        B.cut(o, [B.box(f"{o.name}_c", 0, (c0 + c1) / 2, 0.09, c1 - c0, z + 0.15, z + 0.6, K, bevel=0.0)])
    B.box("b_chbed", 0, (c0 + c1) / 2, 0.09, c1 - c0, z + 0.13, z + 0.16, BLK, bevel=0.0, tags=tags)
    # freio de boca proprio (duplo defletor): camara traseira com presas laterais serrilhadas que apontam
    # para a frente, pescoco de aco e camara dianteira em focinho de cunha; portas escuras de lado a lado
    rb, fa, fb = ra + 0.36, ra + 0.41, L
    B.cyl("b_brakering", 0, ra - 0.02, z, 0.29, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=hot)
    ports1 = (ra + 0.14, ra + 0.25)
    _chamber("b_brake1", ra, rb, z, A, K, hot, tags, 0.34, 0.06, 0.28, ports1, back=0.10)
    for sx in (-1, 1):
        # ponta rombuda (~90 graus): o recuo do bisel nao cruza o poligono (malha vazia na booleana)
        fin = [(-0.30, ra + 0.04), (-0.37, ra + 0.09), (-0.41, ra + 0.18), (-0.41, rb - 0.02), (-0.36, rb + 0.06),
               (-0.30, rb + 0.02)]
        fin = fin if sx < 0 else Mo.mirror(fin)
        fn = B.plate(f"b_fang{sx}", fin, z - 0.14, z + 0.13, A, slope=0.035, bevel=0.01, tags=hot)
        # serrilha: as portas da camara continuam pela presa
        B.cut(fn, [B.box(f"b_fangn{sx}{i}", sx * 0.40, y, 0.12, 0.06, z - 0.3, z + 0.4, K, bevel=0.0)
                   for i, y in enumerate(ports1)])
    B.cyl("b_neck", 0, (rb + fa) / 2, z, 0.29, fa - rb + 0.04, S, axis="Y", verts=8, bevel=0.006, tags=hot)
    # 2 portas no trecho reto (antes do focinho), espacadas 0.11
    _chamber("b_brake2", fa, fb, z, A, K, hot, tags, 0.40, 0.22, 0.12, (fa + 0.11, fa + 0.22), back=0.08,
             extra=[B.box("b_bore_c", 0, fb, 0.16, 0.12, z - 0.10, z + 0.4, K, bevel=0.0)])
    # crista do nariz: para antes das portas e do furo da boca
    B.box("b_crest", 0, L - 0.12, 0.04, 0.12, z + 0.13, z + 0.215, AM, bevel=0.004, tags=hot)


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto: placas do conves (verde = pintura) + paiol blindado de granadas nucleares na fileira de tras."""
    tags = (T,)
    W, H = PART["size"]
    pv = PART["pivot"]
    ring_r = PART["ring_r"]
    green = B.mat_roof_green()
    px, py = pv[0] - W / 2, H / 2 - pv[1]
    gap = 0.03
    B.box("deck_under", 0, 0, W, H, -0.05, 0.02, M["core"], bevel=0.0, tags=tags)
    for tx in range(W):
        for ty in range(H - 1):
            cx, cy = tx + 0.5 - W / 2, H / 2 - ty - 0.5
            poly = B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
            _, pnl = B.shard(f"deck{tx}_{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02,
                             tags=tags)
            if (tx + ty) % 2 == 0 and pnl is not None:
                B.cut(pnl, [B.rbox(f"dl{tx}{ty}", cx + 0.18, cy - 0.18, 0.012, 0.5, 0.07, 0.2, M["core"], rot=45,
                                   bevel=0.0)])
    B.torus("ringbear", px, py, 0.08, ring_r + 0.02, 0.055, M["core_mid"], tags=tags)
    B.cyl("ringhole", px, py, 0.05, ring_r - 0.01, 0.1, M["black"], axis="Z", verts=96, bevel=0.0, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(px, py, ring_r + 0.11, 40) if abs(x) < W / 2 - 0.06 and
           abs(y) < H / 2 - 0.06]
    B.bolts("rb", pts, 0.1, 0.022, M["steel"], tags=tags)
    # paiol: faixa escura com 5 tampoes blindados octogonais (um por tile) e respiros entre eles
    sy = -H / 2 + 0.5
    strip = B.plate("magstrip", B.rpoly(0, sy, W - 0.10, 0.88, 0, chamfer=0.12), 0.0, 0.11, M["core_mid"],
                    slope=0.025, tags=tags)
    rec = []
    for tx in range(W):
        cx = tx + 0.5 - W / 2
        rec.append(B.box(f"ledc{tx}", cx, sy - 0.35, 0.34, 0.06, 0.08, 0.3, M["core"], bevel=0.0))
    for k in range(W - 1):
        rec.append(B.box(f"ventc{k}", k + 1 - W / 2, sy + 0.02, 0.10, 0.50, 0.075, 0.3, M["core"], bevel=0.0))
    B.cut(strip, rec)
    for tx in range(W):
        cx = tx + 0.5 - W / 2
        cyy = sy + 0.04
        lid = B.rpoly(cx, cyy, 0.70, 0.62, 0, chamfer=0.17)
        la, lp = B.shard(f"lid{tx}", lid, 0.10, 0.16, M["armor_mid"], slope=0.025, groove=0.03, panel_h=0.015,
                         tags=tags)
        # tampao central (bisel duplo) com 3 travas a 120 graus
        plug = B.rpoly(cx, cyy, 0.36, 0.36, 0, chamfer=0.105)
        B.cut(lp, [B.loft(f"plugc{tx}", B.offset_poly(plug, -0.03), B.offset_poly(plug, -0.03), 0.15, 0.3,
                          M["core"], bevel=0.0)])
        B.loft(f"plugbed{tx}", B.offset_poly(plug, -0.03), B.offset_poly(plug, -0.03), 0.145, 0.155, M["black"],
               bevel=0.0, tags=tags)
        B.plate(f"plug{tx}", plug, 0.14, 0.19, M["armor_mid"], slope=0.015, bevel=0.006, tags=tags)
        for k in range(3):
            a = math.radians(90 + k * 120)
            B.rbox(f"lock{tx}{k}", cx + math.cos(a) * 0.11, cyy + math.sin(a) * 0.11, 0.04, 0.09, 0.19, 0.21,
                   M["steel"], rot=math.degrees(a) - 90, bevel=0.006, tags=tags)
        B.cyl(f"plugh{tx}", cx, cyy, 0.20, 0.035, 0.02, M["steel"], axis="Z", verts=8, bevel=0.004, tags=tags)
        B.box(f"dslot{tx}", cx, sy - 0.35, 0.34, 0.06, 0.075, 0.085, M["black"], bevel=0.0, tags=tags)
        B.box(f"dled{tx}", cx, sy - 0.35, 0.24, 0.022, 0.085, 0.092, M["glow_dim"], bevel=0.0, tags=tags)
    for k in range(W - 1):
        vx = k + 1 - W / 2
        B.box(f"vbed{k}", vx, sy + 0.02, 0.10, 0.50, 0.07, 0.08, M["black"], bevel=0.0, tags=tags)
        for i in range(5):
            B.box(f"vlouver{k}{i}", vx, sy - 0.18 + i * 0.09, 0.08, 0.024, 0.08, 0.105, M["core_mid"],
                  bevel=0.004, tags=tags)


def _nuke_shell(name, x, y, M, tags, r=0.12):
    """Granada nuclear em pe (vista de cima): base octogonal escura, faixa verde e ogiva de aco."""
    B.cyl(f"{name}b", x, y, 0.10, r, 0.16, M["core_mid"], axis="Z", verts=8, bevel=0.01, tags=tags)
    B.cyl(f"{name}g", x, y, 0.185, r * 0.92, 0.02, M["glow_dim"], axis="Z", verts=8, bevel=0.0, tags=tags)
    B.cyl(f"{name}n", x, y, 0.23, r * 0.85, 0.08, M["armor_mid"], axis="Z", verts=8, bevel=0.0, r2=r * 0.3,
          tags=tags)


def floor(M, T="floor"):
    """Piso: placas, anel com elevador central, estantes de granadas nucleares nos cantos, 6 postos."""
    from bsgen.common import crew_positions
    tags = (T,)
    W, H = PART["size"]
    pv = PART["pivot"]
    ring_r = PART["ring_r"]
    px, py = pv[0] - W / 2, H / 2 - pv[1]
    B.box("fl_base", 0, 0, W, H, -0.05, 0.0, M["core"], bevel=0.0, tags=tags)
    for tx in range(W):
        for ty in range(H):
            x0, y1 = tx - W / 2 + 0.04, H / 2 - ty - 0.04
            B.box(f"fl{tx}{ty}", x0 + 0.46, y1 - 0.46, 0.92, 0.92, 0.0, 0.03, M["core_mid"], bevel=0.01, tags=tags)
    B.torus("fl_ring", px, py, 0.05, ring_r * 0.86, 0.06, M["armor_mid"], tags=tags)
    B.plate("fl_trunk", B.rpoly(px, py, 2.1, 2.1, 0, chamfer=0.6), 0.02, 0.07, M["core_mid"], slope=0.03,
            tags=tags)
    w = ring_r * 0.55
    oct_ = lambda s: B.rpoly(px, py, s, s, 0, chamfer=s / (2 + math.sqrt(2)))  # noqa: E731
    B.plate("fl_hub", oct_(w), 0.05, 0.12, M["armor_mid"], slope=0.03, tags=tags)
    B.plate("fl_hubc", oct_(w * 0.52), 0.10, 0.125, M["core"], slope=0.015, tags=tags)
    B.plate("fl_hubs", oct_(w * 0.18), 0.12, 0.15, M["steel"], slope=0.01, bevel=0.006, tags=tags)
    B.bolts("fl_hubb", B.ring_points(px, py, w * 0.38, 8, math.pi / 8), 0.125, 0.018, M["steel"], tags=tags)
    for k in range(4):
        a = k * math.pi / 2
        cx, cy = px + math.cos(a) * ring_r * 0.62, py + math.sin(a) * ring_r * 0.62
        arrow = [(0.12, 0.0), (-0.07, 0.12), (-0.02, 0.0), (-0.07, -0.12)]
        ca, sa = math.cos(a), math.sin(a)
        arrow = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in arrow]
        B.plate(f"fl_chev{k}", arrow, 0.05, 0.08, M["armor"], slope=0.01, bevel=0.006, tags=tags)
    # elevador de granadas atras do cubo
    B.cyl("fl_hoist", px, py - 1.05, 0.10, 0.20, 0.12, M["armor_mid"], axis="Z", verts=8, bevel=0.01, tags=tags)
    _nuke_shell("fl_hs", px, py - 1.05, M, tags, r=0.12)
    B.box("fl_led_t", px, py + ring_r * 0.96, 0.4, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    B.box("fl_led_b", px, py - ring_r * 0.96, 0.4, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # estantes de granadas nucleares nos 4 cantos (fora do anel)
    for sx in (-1, 1):
        for k, (ys) in enumerate(((2.70, 2.36, 2.02), (-0.86, -1.20, -1.54))):
            bx = sx * 2.12
            B.box(f"fl_rack{sx}{k}", bx, sum(ys) / 3, 0.62, 1.04, 0.0, 0.08, M["armor_mid"], bevel=0.01, tags=tags)
            for i, y in enumerate(ys):
                for j, dx in enumerate((-0.15, 0.15)):
                    _nuke_shell(f"fl_s{sx}{k}{i}{j}", bx + dx, y, M, tags, r=0.12)
    # esteira de granadas na parede de tras
    ey = -H / 2 + 0.19
    B.box("fl_conv", 0, ey, W - 0.30, 0.12, 0.0, 0.10, M["armor_mid"], bevel=0.01, tags=tags)
    for tx in range(W):
        cx = tx + 0.5 - W / 2
        B.box(f"fl_shell{tx}", cx, ey, 0.30, 0.10, 0.10, 0.17, M["core_mid"], bevel=0.01, tags=tags)
        B.box(f"fl_shled{tx}", cx, ey, 0.03, 0.10, 0.17, 0.185, M["glow_dim"], bevel=0.0, tags=tags)
    for i, (cx, cy, _r) in enumerate(crew_positions(W, H, 6, pv)):
        x, y = cx - W / 2, H / 2 - cy
        B.box(f"seat{i}", x, y + 0.02, 0.30, 0.28, 0.0, 0.14, M["armor"], bevel=0.04, tags=tags)
        B.box(f"console{i}", x, y + 0.30, 0.38, 0.12, 0.0, 0.22, M["core_mid"], bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.30, 0.28, 0.06, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
