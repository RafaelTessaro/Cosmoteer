"""Flak Leve de Conves ("Tatu") - defesa antimissil 2x2, 1 tripulante, familia do 76 mm.

Tatu visto de cima: cupula segmentada em 3 faixas de blindagem em chevron bem marcado (apontam para a frente),
cada faixa clara com bisel duplo e perfil de cupula facetado (topo plano no meio, facetas caindo para os lados),
planta oval (faixas mais estreitas atras), vaos escuros entre as faixas com fendas de luz fraca e pinos de
articulacao. Escamas: um sulco inclinado por lado em cada faixa (inclina para o focinho, paralelo as garras), que
para dentro da face de cima (contorno e bisel inteiros). Focinho blindado em ponta com janela de sensor entre os
canos; quilha na faixa da frente com sensor ambar; garras curtas em lamina ate a raiz dos canos; radar de busca
(antena em crescente com alimentador e pip ambar numa ponta) num poco com colar de aco na faixa do meio, girando
360 graus em 8 quadros; baia de exaustao num entalhe da faixa de tras. Bercos escuros em cunha sob as culatras.
Canos: dois canos curtos e grossos estilo 40 mm: culatra escura, luva clara facetada com canal escuro e colares,
cone de chama claro facetado com portas escuras transversais e nariz chanfrado em ponta. Recuo alternado leve.
"""

import math

import bmesh
import bpy

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_flak_light",
    "kind": "gun",
    "size": [2, 2],
    "pivot": [1.0, 0.92],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 2.00,            # lado do quadrado do sprite da torre (focinho ate +0.96, cauda ate -0.95)
    "ring_r": 0.74,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "collider": 0.86,
    "barrels": {
        "ys": [-0.20, 0.20],       # dois canos curtos (sprites de 0.27 sem sobrepor)
        "root": 0.44,              # pivo -> raiz do cano (culatra escura no berco)
        "length": 0.90,            # raiz -> boca
        "width": 0.27,             # largura do sprite de cada cano (cabe o cone de chama)
        "pad": 0.16,               # espaco atras da raiz para o recuo (0.12 + folga)
        "anim": "recoil",
        "recoil": [0.12, 0.08, 0.045, 0.015],
        "heat": [0.55, 0.32, 0.15, 0.05],   # calor leve so no cone de chama
        "interval": 0.05,
    },
    "turret_anim": {"frames": 8, "interval": 0.18},   # radar de busca girando devagar (~1.4 s por volta)
    "lights": [                    # luzes dinamicas em coordenadas da cabeca
        {"at": [0.0, -0.78], "size": 0.9, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "alternate",
}

RING_R = PART["ring_r"]
YS = PART["barrels"]["ys"]
ZB = 0.42                          # altura do eixo dos canos
KCH = 0.325                        # recuo do chevron por unidade de x (igual nas 3 faixas: vaos uniformes)
SC_ANG = 25.0                      # inclinacao dos sulcos das escamas (graus, para o focinho)


# ============================================================================ utilidades
def sym(right):
    """Poligono simetrico a partir da metade direita (de tras para a frente)."""
    return list(right) + Mo.mirror(right)


def pw(xs, vs, x):
    """Interpolacao linear por partes (xs crescente)."""
    if x <= xs[0]:
        return vs[0]
    for i in range(len(xs) - 1):
        if x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return vs[i] + (vs[i + 1] - vs[i]) * t
    return vs[-1]


def solve(fn, lo, hi):
    """Raiz de fn em [lo, hi] por bissecao (fn(lo) e fn(hi) com sinais opostos)."""
    flo = fn(lo)
    for _ in range(50):
        mid = (lo + hi) / 2
        fm = fn(mid)
        if (flo <= 0) == (fm <= 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def strip(name, st, z0, mat, bevel=0.012, tags=()):
    """Solido em faixa ao longo de x. st = [(xb, xt, yf, yb, yft, ybt, zt)] em x crescente: base em z0 de yb a yf
    (em xb), topo em zt de ybt a yft (em xt). Topo plano por trechos (facetas), laterais chanfradas."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    V = []
    for xb, xt, yf, yb, yft, ybt, zt in st:
        V.append((bm.verts.new((xb, yf, z0)), bm.verts.new((xt, yft, zt)), bm.verts.new((xt, ybt, zt)),
                  bm.verts.new((xb, yb, z0))))
    F = bm.faces.new
    F(list(V[0]))
    F(list(reversed(V[-1])))
    for i in range(len(V) - 1):
        a, b = V[i], V[i + 1]
        F([a[0], b[0], b[1], a[1]])
        F([a[1], b[1], b[2], a[2]])
        F([a[2], b[2], b[3], a[3]])
        F([a[3], b[3], b[0], a[0]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = B._link(bpy.data.objects.new(name, me))
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


def mirror_st(half):
    """Estacoes da metade direita (x >= 0, comecando em x = 0) -> faixa inteira."""
    left = [(-xb, -xt, *r) for (xb, xt, *r) in reversed(half[1:])]
    return left + list(half)


class Band:
    """Faixa de blindagem do tatu: chevron em planta, perfil de cupula facetado e ponta em farpa para tras.

    F, Bk: borda da frente / de tras no meio (y); s: recuo do chevron nas pontas; W: meia largura (ponta da farpa);
    topo plano ate a, faceta ate m, faceta mais inclinada ate a ponta. cf/cb: chanfro da frente / de tras."""

    def __init__(self, F, Bk, W, zc, zm, ze, s=0.18, a=0.22, m=0.54, cf=0.06, cb=0.035, back=None):
        self.F, self.Bk, self.W, self.a, self.m = F, Bk, W, a, m
        self.back = back or (lambda x: 0.0)        # desvio extra da borda de tras (cauda arredondada)
        yf = lambda x: F - s * x / W
        yb = lambda x: Bk - s * x / W + self.back(x)
        self.yf, self.yb = yf, yb
        x4, xt5 = W - 0.11, W - 0.035
        self.zf = lambda x: pw([0.0, a, m, xt5], [zc, zc, zm, ze], x)
        half = [(x, x, yf(x), yb(x), yf(x) - cf, yb(x) + cb, self.zf(x)) for x in (0.0, a, m, x4)]
        # farpa: a quina da frente cai em diagonal e a ponta avanca um pouco para tras e para fora
        tf5, tb5 = yb(W) + 0.035, yb(W) - 0.045
        half.append((W, xt5, tf5, tb5, tf5 - 0.012, tb5 + 0.012, self.zf(xt5)))
        for h in half:
            assert h[2] - h[3] > 0.03 and h[4] - h[5] > 0.02, (h, "faixa fina demais")
        self.half = half
        xs = [h[1] for h in half]
        self.tf = lambda x: pw(xs, [h[4] for h in half], x)
        self.tb = lambda x: pw(xs, [h[5] for h in half], x)
        self.xp = x4 - 0.025                         # fim do painel interno (antes da farpa)
        self.ph = 0.028
        self.ztop = lambda x: self.zf(x) + self.ph

    def build(self, name, z0, mat, tags, groove=0.032):
        a = strip(name, mirror_st(self.half), z0, mat, tags=tags)
        # painel interno elevado (bisel duplo) seguindo as facetas do topo
        g, cp, xp, ph = groove, 0.012, self.xp, self.ph
        hp = []
        # estacoes em x crescente: a/m so entram se ficarem antes do chanfro da ponta (senao o painel dobra)
        for x in [v for v in (0.0, self.a, self.m) if v < xp - 0.08] + [xp - 0.05]:
            hp.append((x, x, self.tf(x) - g, self.tb(x) + g, self.tf(x) - g - cp, self.tb(x) + g + cp,
                       self.zf(x) + ph))
        xt = xp - 0.012
        e = max(0.0, min(0.035, (self.tf(xp) - self.tb(xp) - 2 * g - 2 * cp - 0.04) / 2))  # chanfro da ponta
        hp.append((xp, xt, self.tf(xp) - g - e, self.tb(xp) + g + e, self.tf(xt) - g - cp - e,
                   self.tb(xt) + g + cp + e, self.zf(xt) + ph))
        for h in hp:
            assert h[2] - h[3] > 0.03 and h[4] - h[5] > 0.02, (h, "painel fino demais")
        for h0, h1 in zip(hp, hp[1:]):
            assert h1[0] > h0[0] and h1[1] > h0[1], (h0, h1, "estacoes do painel fora de ordem")
        zmin = min(h[6] for h in self.half)
        p = strip(name + "_pnl", mirror_st(hp), zmin - 0.03, mat, bevel=0.008, tags=tags)
        return a, p

    def keel(self, name, hw, mat, tags, inset=0.05, h=0.035):
        """Quilha central mais alta (a espinha do tatu), em chevron como a faixa."""
        z = self.ztop(0.0)
        poly = [(0.0, self.tf(0.0) - inset), (hw, self.tf(hw) - inset), (hw, self.tb(hw) + inset),
                (0.0, self.tb(0.0) + inset)]
        poly = poly + [(-x, y) for x, y in reversed(poly[1:-1])]
        return B.plate(name, poly, z - 0.006, z + h, mat, slope=0.016, bevel=0.007, tags=tags), z + h

    def groove(self, name, x0, sx, band, panel, cmat, w=0.018, mb=0.045, mp=0.012):
        """Sulco inclinado entre escamas: corta o painel de lado a lado e a faixa so por dentro da face de cima
        (mb da borda), assim o contorno e o bisel da faixa ficam inteiros. Inclina SC_ANG graus para o focinho."""
        a = math.radians(SC_ANG)
        dx, dy = -math.sin(a), math.cos(a)           # direcao (lado direito): para a frente e para dentro
        ym = (self.tf(x0) + self.tb(x0)) / 2
        for tgt, m, sfx in ((band, mb, "b"), (panel, mp, "p")):
            t1 = solve(lambda t: (ym + t * dy) - (self.tf(x0 + t * dx) - m), 0.0, 0.5)
            t0 = solve(lambda t: (ym + t * dy) - (self.tb(x0 + t * dx) + m), -0.5, 0.0)
            tc, ln = (t0 + t1) / 2, t1 - t0
            zt = min(self.ztop(x0 + t0 * dx), self.ztop(x0 + t1 * dx))
            B.cut(tgt, [B.rbox(f"{name}{sfx}", sx * (x0 + tc * dx), ym + tc * dy, w, ln, zt - 0.08, 1.2,
                               cmat, rot=sx * SC_ANG, bevel=0.0)])


def rslot(name, cx, cy, ln, w, rot, ztop, n, M, tags, targets, depth):
    """Fenda escura girada (rot graus, comprimento ao longo do eixo y local) com n pips ambar no fundo."""
    for t in targets:
        B.cut(t, [B.rbox(f"{name}_cut{t.name}", cx, cy, w, ln, ztop - depth, ztop + 0.3, M["core"], rot=rot,
                         bevel=0.0)])
    B.rbox(name + "_bed", cx, cy, w, ln, ztop - depth - 0.01, ztop - depth + 0.004, M["black"], rot=rot, bevel=0.0,
           tags=tags)
    a = math.radians(rot)
    ux, uy = -math.sin(a), math.cos(a)
    for i in range(n):
        t = (-0.5 + (i + 0.5) / n) * ln
        B.rbox(f"{name}_pip{i}", cx + ux * t, cy + uy * t, w * 0.55, ln / n * 0.55, ztop - depth, ztop - depth + 0.012,
               M["glow"], rot=rot, bevel=0.0, tags=tags)


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
    emp.rotation_euler = tuple(math.radians(v) for v in rot_deg)
    bpy.context.view_layer.update()
    return emp


def piston(name, pf, pb, r, z, M, tags):
    """Pistao deitado de pb (corpo escuro, atras) ate pf (haste de aco, na frente), com anel de aco e olhais."""
    KM, S_ = M["core_mid"], M["steel"]
    dx, dy = pf[0] - pb[0], pf[1] - pb[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    yaw = math.degrees(math.atan2(-ux, uy))       # eixo Y girado: (-sin yaw, cos yaw) = (ux, uy)
    at = lambda t: (pb[0] + ux * t, pb[1] + uy * t)
    lb = ln * 0.58
    x, y = at(lb / 2)
    B.cyl(name + "_body", x, y, z, r, lb, KM, axis="Y", verts=8, yaw=yaw, bevel=0.005, tags=tags)
    x, y = at(lb - 0.012)
    B.cyl(name + "_ring", x, y, z, r * 1.15, 0.018, S_, axis="Y", verts=8, yaw=yaw, bevel=0.004, tags=tags)
    lr = ln - lb + 0.02
    x, y = at(lb + lr / 2 - 0.02)
    B.cyl(name + "_rod", x, y, z, r * 0.45, lr, S_, axis="Y", verts=8, yaw=yaw, bevel=0.003, tags=tags)
    for t, sfx in ((0.0, "_eb"), (ln, "_ef")):
        x, y = at(t)
        B.rbox(name + sfx, x, y, r * 2.2, r * 1.5, z - r, z + r * 0.6, KM, rot=yaw, bevel=0.004, tags=tags)


# ============================================================================ planta
BAND1 = Band(0.30, -0.03, 0.78, 0.62, 0.52, 0.32, s=KCH * 0.78, cf=0.08)
BAND2 = Band(-0.10, -0.43, 0.76, 0.68, 0.56, 0.33, s=KCH * 0.76, cf=0.08)
BAND3 = Band(-0.50, -0.85, 0.58, 0.60, 0.50, 0.32, s=KCH * 0.58, a=0.20, m=0.44, cf=0.08,
             back=lambda x: 0.25 * (x / 0.58) ** 3)
# nucleo escuro (oval chanfrado, aparece como borda escura em volta das faixas)
#   (borda lateral mais larga entre as pontas das faixas 1 e 2: mostra os pistoes de articulacao)
CORE = sym([(0.26, -0.96), (0.51, -0.925), (0.70, -0.81), (0.84, -0.62), (0.89, -0.38), (0.89, -0.10), (0.85, 0.16),
            (0.74, 0.36), (0.50, 0.64), (0.32, 0.76), (0.12, 0.80)])
# garra curta (lado direito): base paralela a frente da faixa 1 (0.065 a frente), ponta para a frente junto ao cano
CLAW = [(0.33, 0.258), (0.69, 0.141), (0.77, 0.21), (0.73, 0.40), (0.62, 0.46), (0.52, 0.66), (0.40, 0.85),
        (0.35, 0.84), (0.33, 0.74)]
CLAW_AX = 18.0                      # inclinacao do eixo da garra (graus, lado direito)
# focinho em ponta (estacoes ao longo de x): (xb, xt, y frente, y tras, y frente topo, y tras topo, z)
SNOUT = [(0.0, 0.0, 0.96, 0.34, 0.915, 0.375, 0.58), (0.05, 0.05, 0.79, 0.34, 0.755, 0.375, 0.535),
         (0.11, 0.098, 0.52, 0.36, 0.49, 0.385, 0.45)]
RY = (BAND2.tf(0.0) + BAND2.tb(0.0)) / 2   # centro do radar (meio da face de cima da faixa do meio)


def gap_mid(bf, bb, x):
    """Linha do meio do vao entre a faixa da frente (bf) e a de tras (bb) em x."""
    return (bf.yb(x) + bb.yf(x)) / 2


def gap_ang(bf, bb, x):
    """Inclinacao do vao em x (graus, positiva = desce para fora)."""
    return math.degrees(math.atan2(gap_mid(bf, bb, x - 0.1) - gap_mid(bf, bb, x + 0.1), 0.2))


# ============================================================================ cabeca
def radar(M, tags, phase):
    """Radar de busca: pedestal escuro fixo no poco e antena que gira phase*360 graus em torno de (0, RY).
    Antena = refletor claro em crescente (concavo para a frente) com linha recortada, alimentador escuro na frente
    e pip ambar recuado numa ponta so (mostra o sentido do giro)."""
    A, K, KM, S_ = M["armor"], M["core"], M["core_mid"], M["steel"]
    B.cyl("rad_base", 0, RY, 0.62, 0.055, 0.25, KM, axis="Z", verts=8, bevel=0.006, tags=tags)
    before = set(bpy.context.scene.objects)
    B.box("rad_yoke", 0, RY - 0.01, 0.09, 0.06, 0.735, 0.79, KM, bevel=0.01, tags=tags)
    # alimentador: braco escuro para a frente com corneta de aco
    B.box("rad_arm", 0, RY + 0.085, 0.022, 0.13, 0.765, 0.787, KM, bevel=0.004, tags=tags)
    B.box("rad_horn", 0, RY + 0.155, 0.046, 0.034, 0.755, 0.80, S_, bevel=0.006, tags=tags)
    zc0, zc1 = 0.78, 0.825
    us = [-0.20 + i * 0.05 for i in range(9)]
    vf = lambda u: 0.03 + 1.0 * u * u
    vb = lambda u: -0.05 + 1.5 * u * u
    dish = [(u, RY + vf(u)) for u in us] + [(u, RY + vb(u)) for u in reversed(us)]
    d = B.plate("rad_dish", dish, zc0, zc1, A, slope=0.010, bevel=0.005, tags=tags)
    # contorno escuro sob o refletor (destaca a antena clara sobre a faixa clara a 1x)
    B.loft("rad_under", B.offset_poly(dish, -0.016), B.offset_poly(dish, -0.016), zc0 - 0.014, zc0 + 0.002, KM,
           bevel=0.0, tags=tags)
    # linha fina recortada ao longo do refletor + recesso do pip numa ponta
    vc = lambda u: -0.01 + 1.25 * u * u
    uc = [-0.12 + i * 0.03 for i in range(9)]
    line = [(u, RY + vc(u) + 0.006) for u in uc] + [(u, RY + vc(u) - 0.006) for u in reversed(uc)]
    up = 0.168
    B.cut(d, [B.loft("rad_line", line, line, zc1 - 0.022, zc1 + 0.2, K, bevel=0.0),
              B.box("rad_pipc", up, RY + vc(up), 0.03, 0.03, zc1 - 0.026, zc1 + 0.2, K, bevel=0.0)])
    B.box("rad_pipbed", up, RY + vc(up), 0.03, 0.03, zc1 - 0.034, zc1 - 0.024, M["black"], bevel=0.0, tags=tags)
    B.box("rad_pip", up, RY + vc(up), 0.018, 0.018, zc1 - 0.026, zc1 - 0.016, M["glow"], bevel=0.0, tags=tags)
    group(new_roots(before), (0, RY, 0.0), (0.0, 0.0, phase * 360.0))


def head(M, T="head", phase=0.0):
    """Cupula do tatu: 3 faixas em chevron, focinho entre os canos, garras curtas, radar no topo."""
    tags = (T,)
    A, AM, K, KM, S_ = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]

    B.plate("core", CORE, 0.06, 0.28, K, slope=0.04, tags=tags)

    # bercos escuros em cunha sob as culatras, com anel de aco na boca
    for i, y in enumerate(YS):
        cpoly = [(y - 0.10, 0.24), (y + 0.10, 0.24), (y + 0.10, 0.68), (y + 0.065, 0.80), (y - 0.065, 0.80),
                 (y - 0.10, 0.68)]
        cr = B.plate(f"cradle{i}", cpoly, 0.24, 0.34, KM, slope=0.015, bevel=0.01, tags=tags)
        B.cut(cr, [B.box(f"cr_ch{i}", y, 0.51, 0.12, 0.42, 0.30, 0.9, K, bevel=0.0)])
        B.box(f"cr_bed{i}", y, 0.51, 0.12, 0.40, 0.29, 0.305, M["black"], bevel=0.0, tags=tags)
        B.cyl(f"cr_ring{i}", y, 0.768, ZB, 0.088, 0.03, S_, axis="Y", verts=8, bevel=0.005, tags=tags)

    # faixas do tatu
    b1, p1 = BAND1.build("band1", 0.26, A, tags)
    b2, p2 = BAND2.build("band2", 0.26, A, tags)
    b3, p3 = BAND3.build("band3", 0.26, A, tags)
    # escamas: um sulco inclinado por lado em cada faixa
    # (faixa 3: x0 0.28 para o sulco acabar antes do chanfro da ponta do painel em x 0.395)
    for bd, (bb, pp), x0, nm in ((BAND1, (b1, p1), 0.42, "b1"), (BAND2, (b2, p2), 0.36, "b2"),
                                 (BAND3, (b3, p3), 0.28, "b3")):
        for sx in (-1, 1):
            bd.groove(f"scg{nm}{sx}", x0, sx, bb, pp, K)

    # quilha (espinha) na faixa da frente com janela de sensor e fenda ambar
    kl, zk = BAND1.keel("keel1", 0.12, A, tags, inset=0.03, h=0.042)
    win = [(-0.06, 0.088), (0.06, 0.088), (0.06, 0.11), (0.028, 0.132), (-0.028, 0.132), (-0.06, 0.11)]
    zw = BAND1.zf(0.0) - 0.047                 # fundo 0.047 dentro da faixa (nada de tampa coplanar)
    for t in (kl, p1, b1):
        B.cut(t, [B.loft(f"kwin{t.name}", win, win, zw, 1.2, K, bevel=0.0)])
    B.loft("kwin_bed", win, win, zw - 0.01, zw + 0.004, M["black"], bevel=0.0, tags=tags)
    B.box("kwin_eye", 0, 0.104, 0.08, 0.012, zw + 0.004, zw + 0.012, M["glow"], bevel=0.0, tags=tags)

    # poco do radar na faixa do meio, com colar de aco na borda
    for t in (b2, p2):
        B.cut(t, [B.cyl(f"rad_well{t.name}", 0, RY, 0.75, 0.088, 0.5, K, axis="Z", verts=8, bevel=0.0)])
    B.cyl("rad_wellbed", 0, RY, 0.505, 0.09, 0.01, M["black"], axis="Z", verts=8, bevel=0.0, tags=tags)
    zr = BAND2.ztop(0.0)
    # colar escuro (o poco nao cresce: a borda da face de cima fica inteira) = disco escuro sob a antena
    col = B.cyl("rad_collar", 0, RY, zr + 0.006, 0.118, 0.024, KM, axis="Z", verts=8, bevel=0.004, tags=tags)
    B.cut(col, [B.cyl("rad_colc", 0, RY, zr, 0.084, 0.2, K, axis="Z", verts=8, bevel=0.0)])
    B.bolts("rad_bolt", [(0.10 * math.cos(math.radians(a)), RY + 0.10 * math.sin(math.radians(a)))
                         for a in (22.5, 157.5, 202.5, 337.5)], zr + 0.018, 0.009, S_, tags=tags)
    radar(M, tags, phase)

    # entalhe da baia de exaustao na faixa de tras
    for t in (b3, p3):
        B.cut(t, [B.box(f"vent_cut{t.name}", 0, -0.81, 0.34, 0.22, 0.30, 1.0, K, bevel=0.0)])
    B.box("vent_bay", 0, -0.80, 0.32, 0.18, 0.26, 0.34, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"louver{i}", 0, -0.85 + i * 0.045, 0.30, 0.016, 0.26, 0.35, KM, bevel=0.003, tags=tags)
    for i, x in enumerate((-0.09, 0.0, 0.09)):
        B.box(f"vent_pip{i}", x, -0.728, 0.03, 0.016, 0.34, 0.348, M["glow"], bevel=0.0, tags=tags)

    # focinho blindado com crista e janela de sensor
    sn = strip("snout", mirror_st(SNOUT), 0.26, A, tags=tags)
    B.cut(sn, [B.box("sn_win", 0, 0.50, 0.07, 0.12, 0.50, 1.0, K, bevel=0.0)])
    # escamas do focinho: 2 sulcos em V (mesmo chevron das faixas), param ~0.02 antes da borda da face de cima
    # (0.03 de largura e fundo preto: o bisel de 0.012 do focinho come sulcos mais finos)
    th = math.degrees(math.atan(KCH))
    sc = []
    for j, (ya, xe) in enumerate(((0.62, 0.057), (0.72, 0.040))):
        ln = xe / math.cos(math.radians(th)) + 0.008
        for sx in (-1, 1):
            cx = sx * (xe - 0.008) / 2
            sc.append(B.rbox(f"sn_sc{j}{sx}", cx, ya - KCH * abs(cx), ln, 0.03, 0.47, 1.0, K,
                             rot=-sx * th, bevel=0.0))
            B.rbox(f"sn_scb{j}{sx}", cx, ya - KCH * abs(cx), ln, 0.03, 0.462, 0.472, M["black"], rot=-sx * th,
                   bevel=0.0, tags=tags)
    B.cut(sn, sc)
    B.box("sn_bed", 0, 0.50, 0.07, 0.12, 0.49, 0.502, M["black"], bevel=0.0, tags=tags)
    B.box("sn_eye", 0, 0.52, 0.036, 0.014, 0.502, 0.51, M["glow"], bevel=0.0, tags=tags)

    for sx in (-1, 1):
        sd = "R" if sx > 0 else "L"
        poly = CLAW if sx > 0 else Mo.mirror(CLAW)
        ca, cp = B.shard(f"claw_{sd}", poly, 0.26, 0.50, A, slope=0.05, groove=0.028, panel_h=0.025, tags=tags)
        # fenda com luz fraca ao longo da garra
        cx, cy, rot = sx * 0.495, 0.49, sx * CLAW_AX
        for t in (ca, cp):
            if t is not None:
                B.cut(t, [B.rbox(f"csl{sd}{t.name}", cx, cy, 0.035, 0.22, 0.45, 0.9, K, rot=rot, bevel=0.0)])
        B.rbox(f"cslbed{sd}", cx, cy, 0.035, 0.22, 0.44, 0.452, M["black"], rot=rot, bevel=0.0, tags=tags)
        B.rbox(f"cslglow{sd}", cx, cy, 0.012, 0.10, 0.452, 0.46, M["glow_dim"], rot=rot, bevel=0.0, tags=tags)
        # fenda de 3 pips na faceta de fora da faixa do meio, perpendicular as bordas da faixa
        x = 0.57
        rslot(f"esl{sd}", sx * x, (BAND2.tf(x) + BAND2.tb(x)) / 2, 0.11, 0.04, -sx * math.degrees(math.atan(KCH)),
              BAND2.ztop(x), 3, M, tags, [b2, p2], depth=0.075)
        # pistoes de articulacao no nucleo escuro, na borda: faixa 1 -> faixa 2 e faixa 2 -> faixa 3
        for k, (pf, pb, r) in enumerate((((0.815, -0.33), (0.800, -0.585), 0.028),
                                         ((0.665, -0.655), (0.650, -0.800), 0.022))):
            piston(f"pst{sd}{k}", (sx * pf[0], pf[1]), (sx * pb[0], pb[1]), r, 0.282 + r, M, tags)
        # vaos entre as faixas: fenda de luz fraca e pino de articulacao (aco, com junta escura no meio)
        for k, (bf, bb, xl, xh) in enumerate(((BAND1, BAND2, 0.30, 0.56), (BAND2, BAND3, 0.30, 0.44))):
            ang = gap_ang(bf, bb, xl)
            B.rbox(f"gapled{sd}{k}", sx * xl, gap_mid(bf, bb, xl), 0.05, 0.009, 0.28, 0.287, M["glow_dim"],
                   rot=-sx * ang, bevel=0.0, tags=tags)
            ang = gap_ang(bf, bb, xh)
            gy = gap_mid(bf, bb, xh)
            yaw = sx * (90.0 - ang)
            B.cyl(f"hinge{sd}{k}", sx * xh, gy, 0.302, 0.026, 0.10, S_, axis="Y", verts=8, yaw=yaw, bevel=0.005,
                  tags=tags)
            B.cyl(f"hingek{sd}{k}", sx * xh, gy, 0.302, 0.031, 0.036, KM, axis="Y", verts=8, yaw=yaw, bevel=0.005,
                  tags=tags)


# ============================================================================ cano
def barrel(M, L=0.90, T="barrel", phase=0.0):
    """Cano curto e grosso estilo 40 mm: raiz em y=0, boca em y=L, centrado em x=0."""
    tags = (T,)
    hot = (T, "hot")
    A, AM, K, KM, S_ = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = ZB
    # culatra escura (fica no berco) com tampa e trava de aco
    rec = [(-0.075, 0.0), (0.075, 0.0), (0.088, 0.03), (0.088, 0.28), (0.075, 0.31), (-0.075, 0.31),
           (-0.088, 0.28), (-0.088, 0.03)]
    # (bisel fino e trava escura: a raiz le como bloco de mantelete escuro, como a culatra do 76 mm)
    B.plate("b_recv", rec, z - 0.09, z + 0.06, KM, slope=0.014, bevel=0.006, tags=tags)
    B.box("b_cover", 0, 0.15, 0.10, 0.18, z + 0.055, z + 0.075, KM, bevel=0.006, tags=tags)
    B.box("b_latch", 0, 0.05, 0.06, 0.03, z + 0.06, z + 0.085, KM, bevel=0.005, tags=tags)
    B.box("b_hinge", 0, 0.255, 0.08, 0.016, z + 0.06, z + 0.08, S_, bevel=0.004, tags=tags)
    # luva clara grossa facetada com canal escuro e colares
    y0, y1 = 0.31, 0.60
    sl = B.cyl("b_sleeve", 0, (y0 + y1) / 2, z, 0.080, y1 - y0, A, axis="Y", verts=8, bevel=0.006, tags=tags,
               r2=0.072)
    B.cut(sl, [B.box("b_chc", 0, (y0 + y1) / 2 + 0.01, 0.022, y1 - y0 - 0.08, z + 0.03, z + 0.2, K, bevel=0.0)])
    B.box("b_chbed", 0, (y0 + y1) / 2 + 0.01, 0.022, y1 - y0 - 0.08, z + 0.02, z + 0.034, M["black"], bevel=0.0,
          tags=tags)
    B.cyl("b_collar0", 0, y0 + 0.02, z, 0.088, 0.035, AM, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("b_collar1", 0, y1 - 0.01, z, 0.078, 0.03, AM, axis="Y", verts=8, bevel=0.006, tags=hot)
    # cone de chama claro facetado (alarga para a boca) com portas escuras transversais
    yc0, yc1 = y1, L - 0.07
    cone = B.cyl("b_cone", 0, (yc0 + yc1) / 2, z, 0.066, yc1 - yc0, A, axis="Y", verts=8, bevel=0.005, tags=hot,
                 r2=0.104)
    B.cut(cone, [B.box(f"b_port{i}", 0, yc0 + 0.06 + i * 0.06, 0.20, 0.026, z + 0.035, z + 0.2, K, bevel=0.0)
                 for i in range(3)])
    B.cyl("b_cone_core", 0, (yc0 + yc1) / 2, z, 0.05, yc1 - yc0, K, axis="Y", verts=8, bevel=0.0, tags=hot)
    # nariz chanfrado em ponta de flecha (como o freio do 76 mm) com a boca recortada
    lip = B.cyl("b_lip", 0, L - 0.035, z, 0.104, 0.07, A, axis="Y", verts=8, bevel=0.005, tags=hot, r2=0.058)
    B.cut(lip, [B.cyl("b_bore", 0, L, z, 0.045, 0.2, K, axis="Y", verts=8, bevel=0.0)])


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto 2x2: placas verdes, anel da torre, respiros nos cantos de tras e tampas com programador de espoleta."""
    tags = (T,)
    w, h = PART["size"]
    green = B.mat_roof_green()
    K, KM, AM, S_ = M["core"], M["core_mid"], M["armor_mid"], M["steel"]
    px, py = PART["pivot"][0] - w / 2, h / 2 - PART["pivot"][1]
    rr = RING_R
    gap = 0.03
    B.box("deck_under", 0, 0, w, h, -0.05, 0.02, K, bevel=0.0, tags=tags)
    for tx in range(w):
        for ty in range(h):
            cx, cy = tx + 0.5 - w / 2, h / 2 - ty - 0.5
            poly = B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
            B.shard(f"deck{tx}_{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02, tags=tags)
    B.torus("ringbear", px, py, 0.08, rr + 0.02, 0.055, KM, tags=tags)
    B.cyl("ringhole", px, py, 0.05, rr - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(px, py, rr + 0.11, 28) if abs(x) < w / 2 - 0.06 and abs(y) < h / 2 - 0.06]
    B.bolts("rb", pts, 0.1, 0.022, S_, tags=tags)
    # o painel verde do convés termina em z 0.08: tudo que deve ficar sem pintura fica acima disso
    for sx in (-1, 1):
        # canto de tras: respiro em diagonal com cantos em cunha, abertura funda (fundo preto em 0.10) com 3 aletas
        # de aco (as frestas pretas entre elas aparecem a 64 px/tile) e luz fraca na fresta de fora
        cx, cy, rot = sx * 0.76, -0.79, sx * 38
        a = math.radians(rot)
        ux, uy = -math.sin(a), math.cos(a)      # eixo curto do respiro (de fora para dentro)
        v = B.rbox(f"cvent{sx}", cx, cy, 0.36, 0.16, 0.07, 0.15, KM, rot=rot, chamfer=0.035, bevel=0.008, tags=tags)
        B.cut(v, [B.rbox(f"cvo{sx}", cx, cy, 0.27, 0.105, 0.10, 0.3, K, rot=rot, chamfer=0.02, bevel=0.0)])
        B.rbox(f"cvbed{sx}", cx, cy, 0.27, 0.105, 0.094, 0.101, M["black"], rot=rot, bevel=0.0, tags=tags)
        for i in range(3):
            t = (i - 1) * 0.029                  # 4 frestas iguais de 0.018 entre as aletas
            B.rbox(f"cvl{sx}{i}", cx + ux * t, cy + uy * t, 0.25, 0.011, 0.10, 0.138, S_, rot=rot, bevel=0.003,
                   tags=tags)
        B.rbox(f"cled{sx}", cx - ux * 0.0435, cy - uy * 0.0435, 0.16, 0.009, 0.101, 0.106, M["glow_dim"], rot=rot,
               bevel=0.0, tags=tags)
        # canto da frente: tampa triangular chanfrada com programador de espoleta (fenda escura e 2 pips)
        tri = [(sx * 0.93, 0.93), (sx * 0.58, 0.93), (sx * 0.93, 0.58)]
        hp = B.plate(f"chatch{sx}", tri if sx < 0 else list(reversed(tri)), 0.07, 0.15, AM, slope=0.02, tags=tags)
        sc, cy2, rot2 = sx * 0.81, 0.81, -sx * 45   # fenda paralela a hipotenusa, fundo 0.05 abaixo do topo
        B.cut(hp, [B.rbox(f"chc{sx}", sc, cy2, 0.12, 0.04, 0.10, 0.3, K, rot=rot2, bevel=0.0)])
        B.rbox(f"chbed{sx}", sc, cy2, 0.12, 0.04, 0.094, 0.101, M["black"], rot=rot2, bevel=0.0, tags=tags)
        a2 = math.radians(rot2)
        for i in (-1, 1):
            B.rbox(f"chpip{sx}{i}", sc + i * 0.03 * math.cos(a2), cy2 + i * 0.03 * math.sin(a2), 0.026, 0.02,
                   0.101, 0.108, M["glow_dim"], rot=rot2, bevel=0.0, tags=tags)
        B.bolts(f"chb{sx}", [(sx * 0.885, 0.885)], 0.155, 0.016, S_, tags=tags)


def floor(M, T="floor"):
    """Piso: anel, posto do atirador atras com consoles, pentes de granadas de 40 mm nos cantos da frente com calhas
    ate o anel, caixas de juncao com cabos nas laterais."""
    from bsgen.common import crew_positions
    tags = (T,)
    w, h = PART["size"]
    pv = PART["pivot"]
    rr = RING_R
    K, KM, A, AM, S_ = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    px, py = pv[0] - w / 2, h / 2 - pv[1]
    B.box("fl_base", 0, 0, w, h, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for tx in range(w):
        for ty in range(h):
            x0, y1 = tx - w / 2 + 0.04, h / 2 - ty - 0.04
            B.box(f"fl{tx}{ty}", x0 + 0.46, y1 - 0.46, 0.92, 0.92, 0.0, 0.03, KM, bevel=0.01, tags=tags)
    B.torus("fl_ring", px, py, 0.05, rr * 0.52, 0.045, AM, tags=tags)
    hub = B.cyl("fl_hub", px, py, 0.05, rr * 0.26, 0.08, A, axis="Z", verts=8, tags=tags)
    B.cut(hub, [B.rbox(f"fl_hubg{k}", px, py + (k - 1) * 0.06, rr * 0.40, 0.016, 0.07, 0.2, K, bevel=0.0)
                for k in range(3)])
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        B.rbox(f"fl_chev{k}", px + math.cos(a) * rr * 0.38, py + math.sin(a) * rr * 0.38, 0.10, 0.10, 0.05, 0.08,
               A, rot=45, bevel=0.01, tags=tags)
    B.box("fl_led_t", px, py + rr * 0.76, 0.24, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # pentes de 4 granadas de 40 mm nos cantos da frente (bandeja escura, estojos de aco, pontas claras)
    for sx in (-1, 1):
        cx, cy, rot = sx * 0.74, 0.72, -sx * 45
        B.rbox(f"fl_tray{sx}", cx, cy, 0.36, 0.30, 0.0, 0.10, KM, rot=rot, chamfer=0.03, bevel=0.01, tags=tags)
        a = math.radians(rot)
        ux, uy = math.cos(a), math.sin(a)        # eixo x local (ao longo do pente)
        vx, vy = -math.sin(a), math.cos(a)       # eixo y local (ao longo do estojo)
        for i in range(4):
            t = (i - 1.5) * 0.075
            x, y = cx + ux * t, cy + uy * t
            B.rbox(f"fl_case{sx}{i}", x - vx * 0.02, y - vy * 0.02, 0.06, 0.18, 0.10, 0.15, S_, rot=rot, bevel=0.01,
                   tags=tags)
            B.rbox(f"fl_tip{sx}{i}", x + vx * 0.095, y + vy * 0.095, 0.05, 0.06, 0.10, 0.145, A, rot=rot,
                   chamfer=0.018, bevel=0.008, tags=tags)
        B.rbox(f"fl_cnt{sx}", cx - vx * 0.13, cy - vy * 0.13, 0.12, 0.025, 0.10, 0.115, M["glow_dim"], rot=rot,
               bevel=0.0, tags=tags)
        # calha de alimentacao do pente ate o anel, com aneis de aco
        yaw = -sx * 47
        dx, dy = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        ccx, ccy = sx * 0.44, 0.43
        B.cyl(f"fl_chute{sx}", ccx, ccy, 0.09, 0.045, 0.30, KM, axis="Y", verts=8, yaw=yaw, bevel=0.008, tags=tags)
        for j in (-1, 1):
            B.cyl(f"fl_chr{sx}{j}", ccx + dx * j * 0.10, ccy + dy * j * 0.10, 0.09, 0.053, 0.025, S_, axis="Y",
                  verts=8, yaw=yaw, bevel=0.004, tags=tags)
        # caixa de juncao na lateral com luz fraca e cabos ate o pente
        jx = sx * 0.84
        B.box(f"fl_jbox{sx}", jx, -0.14, 0.14, 0.30, 0.0, 0.12, KM, bevel=0.015, tags=tags)
        B.box(f"fl_jlid{sx}", jx, -0.14, 0.09, 0.22, 0.12, 0.135, AM, bevel=0.008, tags=tags)
        B.box(f"fl_jled{sx}", jx, -0.235, 0.05, 0.02, 0.135, 0.142, M["glow_dim"], bevel=0.0, tags=tags)
        for j in (-1, 1):
            B.cyl(f"fl_cab{sx}{j}", jx + j * 0.03, 0.225, 0.035, 0.018, 0.45, S_, axis="Y", verts=8, bevel=0.0,
                  tags=tags)
    # estante de pentes ao longo da borda de tras
    for tx in range(w):
        x = tx - w / 2 + 0.5
        B.box(f"rack{tx}", x, -h / 2 + 0.13, 0.78, 0.18, 0.0, 0.16, AM, bevel=0.01, tags=tags)
        for i in range(3):
            B.box(f"mag{tx}{i}", x - 0.24 + i * 0.24, -h / 2 + 0.13, 0.16, 0.12, 0.16, 0.24, KM, bevel=0.01, tags=tags)
            B.box(f"magled{tx}{i}", x - 0.24 + i * 0.24, -h / 2 + 0.13, 0.10, 0.03, 0.24, 0.26, M["glow_dim"],
                  bevel=0.0, tags=tags)
    # posto do atirador: base de aco, assento claro, encosto escuro e consoles dos dois lados
    for i, (cx, cy, _r) in enumerate(crew_positions(w, h, 1, pv)):
        x, y = cx - w / 2, h / 2 - cy
        B.box(f"seatb{i}", x, y + 0.04, 0.34, 0.32, 0.0, 0.05, S_, bevel=0.012, tags=tags)
        B.box(f"seat{i}", x, y + 0.06, 0.28, 0.22, 0.05, 0.14, A, bevel=0.035, tags=tags)
        B.box(f"seatbk{i}", x, y - 0.09, 0.30, 0.07, 0.05, 0.24, KM, bevel=0.02, tags=tags)
        for sx in (-1, 1):
            B.box(f"console{i}{sx}", x + sx * 0.36, y + 0.06, 0.12, 0.34, 0.0, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x - 0.36, y + 0.06, 0.06, 0.24, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
        B.box(f"pad{i}", x + 0.36, y + 0.06, 0.06, 0.12, 0.22, 0.235, M["glow_dim"], bevel=0.0, tags=tags)
