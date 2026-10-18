"""Flak Leve de Conves ("Tatu") - defesa antimissil 2x2, 1 tripulante, familia do 76 mm.

Tatu visto de cima: cupula segmentada em 3 faixas de blindagem transversais em chevron (apontam para a
frente), cada faixa clara com bisel duplo e perfil facetado de cupula (topo plano no meio, duas facetas
caindo para cada lado), separadas por vaos escuros com fendas de luz fraca (as "linhas de faixa" do tatu).
Focinho blindado em ponta com crista central e janela de sensor entre os dois canos; garras curtas em
lamina na frente das pontas da primeira faixa, que avancam ate a raiz dos canos; radar de busca pequeno
num poco escuro no topo da faixa do meio (gira 360 graus em 8 quadros); baia de exaustao num entalhe da
faixa de tras. Bercos escuros sob as culatras.
Canos: dois canos curtos e grossos estilo 40 mm: culatra escura, luva clara facetada com canal escuro e
colares, cone de chama claro facetado alargando para a boca com portas escuras transversais. Recuo
alternado leve.
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
    "turret_box": 2.00,            # lado do quadrado do sprite da torre (focinho ate +0.96, cauda ate -0.88)
    "ring_r": 0.74,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "collider": 0.86,
    "barrels": {
        "ys": [-0.20, 0.20],       # dois canos curtos (sprites de 0.27 sem sobrepor)
        "root": 0.44,              # pivo -> raiz do cano (culatra escura no berco)
        "length": 0.90,            # raiz -> boca
        "width": 0.27,             # largura do sprite de cada cano (cabe o cone de chama)
        "pad": 0.13,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.12, 0.08, 0.045, 0.015],
        "heat": [0.55, 0.32, 0.15, 0.05],   # calor leve so no cone de chama
        "interval": 0.05,
    },
    "turret_anim": {"frames": 8, "interval": 0.1},   # radar de busca girando
    "lights": [                    # luzes dinamicas em coordenadas da cabeca
        {"at": [0.0, -0.74], "size": 0.9, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "alternate",
}

RING_R = PART["ring_r"]
YS = PART["barrels"]["ys"]
ZB = 0.42                          # altura do eixo dos canos
RY = -0.27                         # centro do radar (topo da faixa do meio)


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

    def build(self, name, z0, mat, tags, groove=0.032, ph=0.028):
        a = strip(name, mirror_st(self.half), z0, mat, tags=tags)
        # painel interno elevado (bisel duplo) seguindo as facetas do topo
        g, cp, xp = groove, 0.012, self.xp
        hp = []
        for x in (0.0, self.a, self.m, xp - 0.05):
            hp.append((x, x, self.tf(x) - g, self.tb(x) + g, self.tf(x) - g - cp, self.tb(x) + g + cp,
                       self.zf(x) + ph))
        xt = xp - 0.012
        e = min(0.035, (self.tf(xp) - self.tb(xp) - 2 * g - 2 * cp - 0.04) / 2)   # chanfro da ponta do painel
        hp.append((xp, xt, self.tf(xp) - g - e, self.tb(xp) + g + e, self.tf(xt) - g - cp - e,
                   self.tb(xt) + g + cp + e, self.zf(xt) + ph))
        for h in hp:
            assert h[2] - h[3] > 0.03 and h[4] - h[5] > 0.02, (h, "painel fino demais")
        zmin = min(h[6] for h in self.half)
        p = strip(name + "_pnl", mirror_st(hp), zmin - 0.03, mat, bevel=0.008, tags=tags)
        self.ztop = lambda x: self.zf(x) + ph
        return a, p

    def keel(self, name, hw, mat, tags, inset=0.05, h=0.035):
        """Quilha central mais alta (a espinha do tatu atravessa as faixas)."""
        z = self.zf(0.0) + 0.028
        poly = [(0.0, self.tf(0.0) - inset), (hw, self.tf(hw) - inset), (hw, self.tb(hw) + inset),
                (0.0, self.tb(0.0) + inset)]
        poly = poly + [(-x, y) for x, y in reversed(poly[1:-1])]
        return B.plate(name, poly, z - 0.006, z + h, mat, slope=0.016, bevel=0.007, tags=tags)


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


# ============================================================================ planta
BAND1 = Band(0.28, -0.04, 0.80, 0.62, 0.53, 0.34)
BAND2 = Band(-0.11, -0.43, 0.86, 0.68, 0.59, 0.36)
BAND3 = Band(-0.50, -0.87, 0.72, 0.60, 0.51, 0.34, a=0.20, m=0.46, back=lambda x: 0.23 * (x / 0.72) ** 2)
# nucleo escuro (oval chanfrado)
CORE = sym([(0.26, -0.90), (0.58, -0.84), (0.78, -0.64), (0.90, -0.36), (0.91, -0.12), (0.85, 0.16), (0.74, 0.36),
            (0.50, 0.64), (0.32, 0.76), (0.12, 0.80)])
# garra curta (lado direito): base paralela a frente da faixa 1, ponta para a frente junto ao cano
CLAW = [(0.33, 0.274), (0.70, 0.19), (0.785, 0.265), (0.72, 0.42), (0.62, 0.46), (0.52, 0.66), (0.40, 0.85),
        (0.35, 0.84), (0.33, 0.74)]
CLAW_AX = 18.0                      # inclinacao do eixo da garra (graus, lado direito)
# focinho em ponta (estacoes ao longo de x): (xb, xt, y frente, y tras, y frente topo, y tras topo, z)
SNOUT = [(0.0, 0.0, 0.96, 0.34, 0.915, 0.375, 0.58), (0.05, 0.05, 0.79, 0.34, 0.755, 0.375, 0.535),
         (0.11, 0.098, 0.52, 0.36, 0.49, 0.385, 0.45)]


def gap_mid(bf, bb, x):
    """Linha do meio do vao entre a faixa da frente (bf) e a de tras (bb) em x."""
    return (bf.yb(x) + bb.yf(x)) / 2


# ============================================================================ cabeca
def radar(M, tags, phase):
    """Radar de busca pequeno: poco escuro (recortado na faixa do meio), pedestal fixo e antena que gira
    phase*360 graus em torno de (0, RY), com pip ambar numa ponta (sentido do giro)."""
    A, K, KM, S_ = M["armor"], M["core"], M["core_mid"], M["steel"]
    B.cyl("rad_base", 0, RY, 0.62, 0.065, 0.24, KM, axis="Z", verts=8, bevel=0.008, tags=tags)
    B.cyl("rad_collar", 0, RY, 0.715, 0.075, 0.025, S_, axis="Z", verts=8, bevel=0.004, tags=tags)
    before = set(bpy.context.scene.objects)
    B.box("rad_yoke", 0, RY, 0.10, 0.07, 0.72, 0.79, KM, bevel=0.01, tags=tags)
    zc = 0.80
    hexa = [(-0.21, RY), (-0.16, RY - 0.058), (0.16, RY - 0.058), (0.21, RY), (0.16, RY + 0.058),
            (-0.16, RY + 0.058)]
    pa = B.plate("rad_panel", hexa, zc - 0.03, zc + 0.02, A, slope=0.014, bevel=0.006, tags=tags)
    B.cut(pa, [B.box("rad_face", 0, RY, 0.27, 0.054, zc, zc + 0.3, K, bevel=0.0)])
    B.box("rad_facebed", 0, RY, 0.27, 0.054, zc - 0.012, zc + 0.002, M["black"], bevel=0.0, tags=tags)
    for i in range(5):
        B.box(f"rad_el{i}", -0.10 + i * 0.05, RY, 0.036, 0.036, zc - 0.004, zc + 0.012, KM, bevel=0.004, tags=tags)
    B.box("rad_end", 0.185, RY, 0.022, 0.032, zc + 0.012, zc + 0.024, M["glow"], bevel=0.0, tags=tags)
    group(new_roots(before), (0, RY, 0.0), (0.0, 0.0, phase * 360.0))


def head(M, T="head", phase=0.0):
    """Cupula do tatu: 3 faixas em chevron, focinho entre os canos, garras curtas, radar no topo."""
    tags = (T,)
    A, AM, K, KM, S_ = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]

    B.plate("core", CORE, 0.06, 0.28, K, slope=0.04, tags=tags)

    # bercos escuros sob as culatras
    for i, y in enumerate(YS):
        cr = B.rbox(f"cradle{i}", y, 0.52, 0.20, 0.56, 0.24, 0.34, KM, chamfer=0.03, slope=0.015, bevel=0.01,
                    tags=tags)
        B.cut(cr, [B.box(f"cr_ch{i}", y, 0.54, 0.13, 0.54, 0.30, 0.9, K, bevel=0.0)])
        B.box(f"cr_bed{i}", y, 0.54, 0.13, 0.52, 0.29, 0.305, M["black"], bevel=0.0, tags=tags)

    # faixas do tatu
    b1, p1 = BAND1.build("band1", 0.26, A, tags)
    b2, p2 = BAND2.build("band2", 0.26, A, tags)
    b3, p3 = BAND3.build("band3", 0.26, A, tags)
    # sulcos entre as escamas de cada faixa (vincos do topo e meio da faceta de fora)
    for bd, tg, nm in ((BAND1, (b1, p1), "b1"), (BAND2, (b2, p2), "b2"), (BAND3, (b3, p3), "b3")):
        for sx in (-1, 1):
            for k, x in enumerate((bd.a, (bd.m + bd.xp) / 2 - 0.02)):
                if nm == "b3" and k == 0:
                    continue
                y0, y1 = bd.yb(x) - 0.05, bd.yf(x) + 0.05
                cuts = [B.box(f"scg{nm}{sx}{k}{t.name}", sx * x, (y0 + y1) / 2, 0.016, y1 - y0, bd.ztop(x) - 0.075,
                              1.2, K, bevel=0.0) for t in tg]
                for t, c in zip(tg, cuts):
                    B.cut(t, [c])
    # quilha central na faixa da frente com fenda de 3 pips
    kl = BAND1.keel("keel1", 0.10, A, tags)
    zk = BAND1.zf(0.0) + 0.028 + 0.035
    Mo.slot_with_pips("ksl", 0.12, -0.06, 0.06, 0.04, zk, 3, M, tags, target=[kl, p1], depth=0.075, vertical=False)

    # poco do radar na faixa do meio
    for t in (b2, p2):
        B.cut(t, [B.cyl(f"rad_well{t.name}", 0, RY, 0.75, 0.115, 0.5, K, axis="Z", verts=8, bevel=0.0)])
    B.cyl("rad_wellbed", 0, RY, 0.505, 0.115, 0.01, M["black"], axis="Z", verts=8, bevel=0.0, tags=tags)
    radar(M, tags, phase)

    # entalhe da baia de exaustao na faixa de tras
    for t in (b3, p3):
        B.cut(t, [B.box(f"vent_cut{t.name}", 0, -0.82, 0.34, 0.22, 0.30, 1.0, K, bevel=0.0)])
    B.box("vent_bay", 0, -0.81, 0.32, 0.18, 0.26, 0.34, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"louver{i}", 0, -0.86 + i * 0.045, 0.30, 0.016, 0.26, 0.35, KM, bevel=0.003, tags=tags)
    for i, x in enumerate((-0.09, 0.0, 0.09)):
        B.box(f"vent_pip{i}", x, -0.745, 0.03, 0.016, 0.34, 0.348, M["glow"], bevel=0.0, tags=tags)

    # focinho blindado com crista e janela de sensor
    sn = strip("snout", mirror_st(SNOUT), 0.26, A, tags=tags)
    B.cut(sn, [B.box("sn_win", 0, 0.50, 0.07, 0.12, 0.50, 1.0, K, bevel=0.0)])
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
        B.rbox(f"cslglow{sd}", cx, cy, 0.012, 0.13, 0.452, 0.46, M["glow_dim"], rot=rot, bevel=0.0, tags=tags)
        # fenda de 3 pips na ponta da faixa do meio (na faceta de fora)
        x = 0.66
        yc = (BAND2.tf(x) + BAND2.tb(x)) / 2
        Mo.slot_with_pips(f"esl{sd}", sx * x, yc - 0.06, yc + 0.06, 0.04, BAND2.ztop(x), 3, M, tags,
                          target=[b2, p2], depth=0.075)
        # fendas de luz fraca nos vaos entre as faixas (linhas de faixa do tatu)
        for k, (bf, bb) in enumerate(((BAND1, BAND2), (BAND2, BAND3))):
            x = 0.36
            yy = gap_mid(bf, bb, x)
            ang = math.degrees(math.atan2(gap_mid(bf, bb, x - 0.1) - gap_mid(bf, bb, x + 0.1), 0.2))
            B.rbox(f"gapled{sd}{k}", sx * x, yy, 0.09, 0.012, 0.28, 0.288, M["glow_dim"], rot=-sx * ang, bevel=0.0,
                   tags=tags)
        # pinos de articulacao das faixas (aco) no vao, perto das pontas
        for k, (bf, bb) in enumerate(((BAND1, BAND2), (BAND2, BAND3))):
            x = 0.56
            B.cyl(f"hinge{sd}{k}", sx * x, gap_mid(bf, bb, x), 0.30, 0.03, 0.10, S_, axis="Y", verts=8,
                  bevel=0.006, tags=tags)


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
    B.plate("b_recv", rec, z - 0.09, z + 0.06, KM, slope=0.014, tags=tags)
    B.box("b_cover", 0, 0.15, 0.10, 0.18, z + 0.055, z + 0.075, KM, bevel=0.006, tags=tags)
    B.box("b_latch", 0, 0.05, 0.06, 0.03, z + 0.06, z + 0.085, S_, bevel=0.005, tags=tags)
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
    # cone de chama claro facetado (alarga para a boca) com portas escuras transversais e labio
    yc0, yc1 = y1, L - 0.04
    cone = B.cyl("b_cone", 0, (yc0 + yc1) / 2, z, 0.066, yc1 - yc0, A, axis="Y", verts=8, bevel=0.005, tags=hot,
                 r2=0.104)
    B.cut(cone, [B.box(f"b_port{i}", 0, yc0 + 0.07 + i * 0.065, 0.20, 0.026, z + 0.035, z + 0.2, K, bevel=0.0)
                 for i in range(3)])
    lip = B.cyl("b_lip", 0, L - 0.02, z, 0.108, 0.04, A, axis="Y", verts=8, bevel=0.006, tags=hot, r2=0.094)
    B.cut(lip, [B.cyl("b_bore", 0, L, z, 0.045, 0.2, K, axis="Y", verts=8, bevel=0.0)])
    B.cyl("b_cone_core", 0, (yc0 + yc1) / 2, z, 0.05, yc1 - yc0, K, axis="Y", verts=8, bevel=0.0, tags=hot)


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto 2x2: placas verdes, anel da torre, respiros nos cantos de tras e faixas de tatu nos da frente."""
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
    for sx in (-1, 1):
        # canto de tras: respiro em diagonal com persianas fundas e luz fraca na borda de fora
        cx, cy, rot = sx * 0.76, -0.79, sx * 38
        v = B.rbox(f"cvent{sx}", cx, cy, 0.36, 0.18, 0.05, 0.11, KM, rot=rot, chamfer=0.04, bevel=0.01, tags=tags)
        a = math.radians(rot)
        B.cut(v, [B.rbox(f"cvc{sx}{i}", cx - math.sin(a) * (i - 1) * 0.045, cy + math.cos(a) * (i - 1) * 0.045,
                         0.28, 0.024, 0.07, 0.2, K, rot=rot, bevel=0.0) for i in range(3)])
        B.rbox(f"cled{sx}", cx - math.sin(a) * 0.115, cy + math.cos(a) * 0.115, 0.16, 0.02, 0.06, 0.075,
               M["glow_dim"], rot=rot, bevel=0.0, tags=tags)
        # canto da frente: tampa triangular chanfrada com programador de espoleta (fenda escura e 2 pips)
        tri = [(sx * 0.93, 0.93), (sx * 0.58, 0.93), (sx * 0.93, 0.58)]
        hp = B.plate(f"chatch{sx}", tri if sx < 0 else list(reversed(tri)), 0.06, 0.10, AM, slope=0.02, tags=tags)
        sc, rot2 = sx * 0.80, sx * 45
        B.cut(hp, [B.rbox(f"chc{sx}", sc, 0.80, 0.16, 0.04, 0.07, 0.2, K, rot=rot2, bevel=0.0)])
        B.rbox(f"chbed{sx}", sc, 0.80, 0.16, 0.04, 0.065, 0.072, M["black"], rot=rot2, bevel=0.0, tags=tags)
        for i in (-1, 1):
            B.rbox(f"chpip{sx}{i}", sc + i * 0.035 * 0.707, 0.80 - sx * i * 0.035 * 0.707, 0.03, 0.02, 0.072, 0.08,
                   M["glow_dim"], rot=rot2, bevel=0.0, tags=tags)
        B.bolts(f"chb{sx}", [(sx * 0.885, 0.885)], 0.105, 0.016, S_, tags=tags)


def floor(M, T="floor"):
    """Piso: anel, posto do atirador atras com consoles, pentes de granadas de 40 mm nos cantos da frente."""
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
