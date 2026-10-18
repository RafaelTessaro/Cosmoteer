"""Torre Naval Tripla 406 mm ("Mapinguari") - arma-capitania do mod, mesma familia do 76 mm.

Casa de canhoes em fortaleza com 3 niveis de placas: cinturao baixo (ombreiras com degrau, maos de
duas garras - lamina principal + garra externa - e saias traseiras com turbinas), glacis inclinado
de verdade (topo em rampa) + ombros, e no topo a espinha com sensor e a ponte do telemetro que cruza
a traseira inteira (casulos oticos saindo dos flancos: silhueta "cabeca de martelo", luzes de alerta
vermelhas). Nucleo escuro com maquinaria nos vaos: elevadores de granadas, tambores com contador,
calhas, turbinas. Bocarra do Mapinguari: presas interligadas entre os tres bercos dos canos.
Tres canos enormes: bolsa de culatra pregueada, luva de recuo grossa, tubo afunilado com extrator
de gases e freio de boca claro em ponta de flecha com varias portas (brilha de calor).
"""

import math

import bmesh
import bpy

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_naval_406",
    "kind": "gun",
    "size": [6, 7],
    "pivot": [3.0, 3.05],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 5.9,             # lado do quadrado do sprite da torre
    "ring_r": 2.65,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "collider": 2.6,
    "barrels": {
        "ys": [-0.9, 0.0, 0.9],    # tres canos lado a lado (largura 0.8: nao se sobrepoem)
        "root": 1.50,              # pivo -> raiz do cano
        "length": 4.0,             # raiz -> boca
        "width": 0.80,             # largura do sprite do cano (cabe o freio de boca)
        "pad": 0.66,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.60, 0.58, 0.54, 0.49, 0.43, 0.37, 0.31, 0.25, 0.19, 0.14, 0.09, 0.05, 0.02],
        "heat": [1.0, 0.97, 0.93, 0.88, 0.82, 0.75, 0.68, 0.6, 0.52, 0.44, 0.36, 0.28, 0.2, 0.13, 0.07],
        "interval": 0.075,
    },
    "lights": [
        {"at": [0.0, -2.35], "size": 2.6, "color": [255, 120, 30], "z": 0.9},
    ],
    "preview_pattern": "volley",
}

BZ = 0.70          # altura do eixo dos canos
YS = PART["barrels"]["ys"]
ROOT = PART["barrels"]["root"]


# ============================================================================ utilidades locais
def _lines(target, name, specs, ztop, mat):
    """Linhas de painel recortadas no alvo: specs = [(x, y, comprimento, rotacao)]."""
    cuts = [B.rbox(f"{name}{i}", x, y, 0.016, ln, ztop - 0.02, ztop + 0.4, mat, rot=r, bevel=0.0)
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


def _ramp(y0, z0, y1, z1):
    """Altura linear em y (topo inclinado): z0 em y0, z1 em y1."""
    k = (z1 - z0) / (y1 - y0)
    return lambda x, y: z0 + (y - y0) * k


def _sshard(name, poly, z0, zf, mat, slope=0.08, groove=0.035, panel_h=0.03, tags=()):
    """Placa com bisel duplo (como B.shard) e topo inclinado zf(x, y)."""
    s = B.safe_offset(poly, slope)
    a = _zloft(name, poly, B.offset_poly(poly, s), lambda x, y: z0, zf, mat, tags=tags)
    d = slope + groove
    inner = B.robust_offset(poly, d)
    if inner is None or B.robust_offset(poly, d + 0.012) is None:
        return a, None
    s2 = B.safe_offset(inner, 0.012)
    b = _zloft(name + "_pnl", inner, B.offset_poly(inner, s2), lambda x, y: zf(x, y) - 0.004,
               lambda x, y: zf(x, y) + panel_h, mat, bevel=0.008, tags=tags)
    return a, b


def _side(sx):
    return (lambda p: p) if sx < 0 else Mo.mirror


# ============================================================================ cabeca
K_RF = 0.24 / 1.56   # enflechamento da ponte do telemetro (y recua com |x|)


def _rf_front(x):
    return -1.34 - (abs(x) - 0.74) * K_RF


def _rf_back(x):
    return -1.80 - (abs(x) - 0.74) * K_RF


def _glass():
    """Vidro escuro das janelas oticas (nao emite: so a pip ambar acende)."""
    return B.mat_metal("rf_glass", (0.025, 0.04, 0.065), rough=0.08, metal=0.15)


def head(M, T="head", phase=0.0):
    """Cabeca: fortaleza de 3 niveis, garras duplas, ponte de telemetro, bocarra entre os bercos."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    BLK = M["black"]

    # ---------------------------------------------------------------- anel, nucleo e bloco escuro
    # anel giratorio: o arco da frente e cortado na altura das bocas dos bercos (com a cabeca por cima
    # dos canos, nada escuro pode passar da boca do berco nas colunas dos canos)
    ring = B.cyl("ring", 0, 0, 0.04, 2.68, 0.08, KM, axis="Z", verts=96, bevel=0.01, tags=tags)
    B.cut(ring, [B.box("ring_c", 0, 2.75, 4.0, 0.78, -0.2, 0.4, K, bevel=0.0)])
    B.bolts("ringbolt", [p for p in B.ring_points(0, 0, 2.60, 40, 0.05) if p[1] < 2.25], 0.09, 0.026, S,
            tags=tags)
    # nucleo largo: cobre os vaos entre ombreiras, casulos e garras (nenhuma pintura do casco aparece)
    core = [(-1.55, -2.88), (1.55, -2.88), (2.46, -2.16), (2.74, -1.90), (2.84, -1.40), (2.84, 1.04), (2.62, 1.12),
            (1.92, 2.12), (-1.92, 2.12), (-2.62, 1.12), (-2.84, 1.04), (-2.84, -1.40), (-2.74, -1.90), (-2.46, -2.16)]
    B.plate("core", core, 0.06, 0.38, K, slope=0.05, tags=tags)
    house = [(-1.40, -1.30), (1.40, -1.30), (1.50, -1.20), (1.50, 0.70), (1.30, 0.92), (-1.30, 0.92),
             (-1.50, 0.70), (-1.50, -1.20)]
    B.plate("house", house, 0.36, 0.84, KM, slope=0.06, tags=tags)

    # ---------------------------------------------------------------- nivel 1: ombreiras, garras, saias
    # ombreira dividida em chevron (continua a linha glacis/ombro): placa traseira baixa + dianteira alta
    paul_r = [(-1.82, -1.38), (-2.34, -1.42), (-2.60, -1.16), (-2.70, -0.50), (-1.92, -0.20), (-1.92, -0.55),
              (-1.82, -0.66)]
    paul = [(-1.92, -0.08), (-2.86, -0.44), (-2.86, 0.42), (-2.64, 0.98), (-1.98, 0.98), (-1.82, 0.82),
            (-1.82, 0.30), (-1.92, 0.18)]
    pcap = [(-2.12, -0.06), (-2.60, -0.24), (-2.74, -0.14), (-2.74, 0.34), (-2.46, 0.76), (-2.12, 0.58)]
    # lamina principal: larga na raiz, varre para dentro ate a ponta ao lado do cano externo
    blade = [(-2.36, 1.08), (-1.60, 1.08), (-1.29, 1.42), (-1.27, 2.50), (-1.34, 2.86), (-1.50, 2.80),
             (-1.70, 2.44), (-1.86, 2.40), (-2.10, 1.98), (-2.36, 1.66)]
    # garra externa (mais curta, ponta recolhida para girar sem varrer tanto os vizinhos)
    talon = [(-2.44, 1.06), (-2.80, 1.06), (-2.86, 1.14), (-2.86, 1.54), (-2.68, 2.02), (-2.46, 2.30),
             (-2.38, 2.12), (-2.42, 1.70)]
    # junta escura sob o par de garras (fundo da forquilha lamina/garra)
    knuckle = [(-1.72, 0.98), (-2.80, 0.98), (-2.80, 1.52), (-2.62, 2.00), (-2.44, 2.22), (-2.14, 2.22),
               (-1.92, 2.06)]
    # saia traseira em cunha (a traseira afunila), recuada atras da ponte enflechada
    apron = [(-1.36, -1.97), (-2.26, -2.11), (-2.44, -2.21), (-2.44, -2.33), (-1.70, -2.86), (-1.22, -2.86)]
    for side, sx in (("L", -1), ("R", 1)):
        f = _side(sx)
        pa, pp = B.shard(f"paulr_{side}", f(paul_r), 0.36, 0.84, A, slope=0.10, groove=0.04, panel_h=0.03,
                         tags=tags)
        _lines(pp, f"pprl{side}", [(sx * 2.40, -0.78, 0.26, 0)], 0.87, K)
        # grelha de respiro (sem luz: quebra a fileira de fendas acesas)
        vx, vy = sx * 2.22, -1.12
        for t in (pa, pp):
            B.cut(t, [B.box(f"pv_c{side}", vx, vy, 0.44, 0.14, 0.80, 1.2, K, bevel=0.0)])
        B.box(f"pv_bed{side}", vx, vy, 0.44, 0.14, 0.785, 0.80, BLK, bevel=0.0, tags=tags)
        for i in range(6):
            B.box(f"pv_l{side}{i}", vx - 0.175 + i * 0.07, vy, 0.026, 0.12, 0.79, 0.835, KM, bevel=0.004,
                  tags=tags)
        _, pp = B.shard(f"paul_{side}", f(paul), 0.36, 0.94, A, slope=0.11, groove=0.045, panel_h=0.035,
                        tags=tags)
        _lines(pp, f"ppl{side}", [(sx * 2.20, 0.74, 0.20, 90), (sx * 2.05, 0.10, 0.24, 0)], 0.975, K)
        ca, cp = B.shard(f"pcap_{side}", f(pcap), 0.96, 1.08, A, slope=0.05, groove=0.026, panel_h=0.022,
                         tags=tags)
        _lines(cp, f"pcl{side}", [(sx * 2.40, 0.16, 0.32, 0)], 1.10, K)
        # periscopio do chefe de peca (lente num rebaixo preto)
        B.box(f"peri{sx}", sx * 2.34, 0.52, 0.18, 0.12, 1.08, 1.16, KM, bevel=0.01, tags=tags)
        B.box(f"peribed{sx}", sx * 2.34, 0.555, 0.13, 0.04, 1.155, 1.165, BLK, bevel=0.0, tags=tags)
        B.box(f"perig{sx}", sx * 2.34, 0.555, 0.10, 0.014, 1.163, 1.168, M["glow_dim"], bevel=0.0, tags=tags)

        # junta escura + lamina principal com topo em rampa (desce para a ponta) e fenda acesa
        B.plate(f"knuckle_{side}", f(knuckle), 0.06, 0.36, KM, slope=0.04, tags=tags)
        ba, bp = _sshard(f"blade_{side}", f(blade), 0.36, _ramp(1.08, 0.92, 2.86, 0.62), A, slope=0.10,
                         groove=0.04, panel_h=0.03, tags=tags)
        for t in (ba, bp):
            B.cut(t, [B.rbox(f"bcut{side}", sx * 1.74, 1.86, 0.46, 0.06, 0.70, 1.2, K, rot=sx * -52, bevel=0.0)])
        B.rbox(f"bbed{side}", sx * 1.74, 1.86, 0.46, 0.06, 0.66, 0.705, BLK, rot=sx * -52, bevel=0.0, tags=tags)
        B.rbox(f"bglow{side}", sx * 1.74, 1.86, 0.34, 0.018, 0.70, 0.712, M["glow_dim"], rot=sx * -52,
               bevel=0.0, tags=tags)
        _lines(bp, f"bpl{side}", [(sx * 1.46, 2.20, 0.40, 0), (sx * 1.98, 1.30, 0.26, 90)], 0.86, K)
        ta, tp = _sshard(f"talon_{side}", f(talon), 0.36, _ramp(1.08, 0.86, 2.28, 0.62), A, slope=0.08,
                         groove=0.03, panel_h=0.025, tags=tags)
        _lines(tp, f"tpl{side}", [(sx * 2.66, 1.40, 0.22, 0)], 0.84, K)
        # pistao hidraulico cruzando a forquilha em diagonal: cilindro na garra, haste entra na lamina
        p0, p1 = (sx * 2.50, 1.88), (sx * 1.96, 2.20)
        ux, uy = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(ux, uy)
        ux, uy = ux / ln, uy / ln
        yaw = math.degrees(math.atan2(-ux, uy))
        B.cyl(f"piston{sx}", (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 0.55, 0.038, ln, S, axis="Y", verts=10,
              yaw=yaw, tags=tags)
        B.cyl(f"pistonb{sx}", p0[0] + ux * 0.16, p0[1] + uy * 0.16, 0.55, 0.062, 0.20, KM, axis="Y", verts=10,
              yaw=yaw, tags=tags)
        B.cyl(f"pistonr{sx}", p0[0] + ux * 0.27, p0[1] + uy * 0.27, 0.55, 0.068, 0.025, S, axis="Y", verts=10,
              yaw=yaw, tags=tags)

        # saia traseira com turbina embutida (rotor visto por um furo na placa)
        aa, ap = B.shard(f"apron_{side}", f(apron), 0.36, 0.74, A, slope=0.08, groove=0.035, panel_h=0.028,
                         tags=tags)
        tx, ty, tr = sx * 1.75, -2.40, 0.21
        for t in (aa, ap):
            B.cut(t, [B.cyl(f"tb_cut{side}", tx, ty, 0.8, tr, 1.2, K, axis="Z", verts=8, bevel=0.0)])
        if ap is not None and ap.modifiers.get("bevel"):
            ap.modifiers.remove(ap.modifiers["bevel"])   # bisel pos-recorte dobra o painel (ver glacis)
        _turbine(M, tags, f"tb{side}", tx, ty, sx, tr)
        B.bolts(f"apb{side}", [(sx * 1.47, -2.74), (sx * 1.50, -2.14)], 0.77, 0.018, S, tags=tags)

    # ---------------------------------------------------------------- bercos escuros dos tres canos
    for k, cx in enumerate(YS):
        crad = [(cx - 0.27, 0.80), (cx + 0.27, 0.80), (cx + 0.30, 0.92), (cx + 0.30, 2.16), (cx + 0.20, 2.36),
                (cx - 0.20, 2.36), (cx - 0.30, 2.16), (cx - 0.30, 0.92)]
        c = B.plate(f"cradle{k}", crad, 0.30, 0.62, KM, slope=0.04, tags=tags)
        B.cut(c, [B.box(f"crad_c{k}", cx, 1.50, 0.44, 1.10, 0.52, 0.9, K, bevel=0.0)])
        # toco da bolsa de culatra (igual ao do cano): aparece com qualquer ordem de desenho
        B.cyl(f"bagcore{k}", cx, ROOT + 0.27, BZ, 0.255, 0.54, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
        for i in range(5):
            B.cyl(f"bagstub{k}{i}", cx, ROOT + 0.06 + i * 0.105, BZ, 0.272, 0.035, K, axis="Y", verts=8,
                  bevel=0.005, tags=tags)
        B.cyl(f"bagscap{k}", cx, ROOT + 0.56, BZ, 0.265, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=tags)
        # boca do berco (colar escuro de onde sai a luva de recuo)
        B.cyl(f"mouth{k}", cx, 2.22, BZ - 0.04, 0.30, 0.26, KM, axis="Y", verts=8, bevel=0.012, tags=tags)
        B.cyl(f"mouthr{k}", cx, 2.33, BZ - 0.04, 0.305, 0.04, S, axis="Y", verts=8, bevel=0.006, tags=tags)
        for j in (-1, 1):
            B.cyl(f"recup{k}{j}", cx + j * 0.272, 1.55, 0.66, 0.03, 1.00, S, axis="Y", verts=10, tags=tags)
        # culatra: bloco escuro com aro de aco e soquete, soquete do refulgador atras
        B.box(f"breech{k}", cx, 0.98, 0.40, 0.30, 0.66, 0.80, KM, bevel=0.012, tags=tags)
        B.box(f"breechr{k}", cx, 1.10, 0.44, 0.05, 0.68, 0.82, S, bevel=0.008, tags=tags)
        B.box(f"breechs{k}", cx, 0.92, 0.18, 0.10, 0.79, 0.805, BLK, bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- bocarra: dentes entre os bercos
    # dente de cima sai de baixo do glacis e aponta para a frente (inclinado para dentro); dente de baixo
    # nasce na boca dos bercos e aponta para tras (inclinado para fora): mandibulas desencontradas
    fang_up = [(-0.57, 0.78), (-0.33, 0.78), (-0.33, 1.04), (-0.38, 1.40), (-0.42, 1.40), (-0.57, 1.02)]
    fang_lo = [(-0.57, 2.36), (-0.57, 2.04), (-0.52, 1.70), (-0.48, 1.70), (-0.33, 2.02), (-0.33, 2.36)]
    for side, sx in (("L", -1), ("R", 1)):
        f = _side(sx)
        cx = sx * 0.45
        # garganta preta entre os bercos (fundo da boca)
        B.box(f"throat{sx}", cx, 1.62, 0.26, 1.50, 0.38, 0.40, BLK, bevel=0.0, tags=tags)
        _sshard(f"fang_up_{side}", f(fang_up), 0.40, _ramp(0.78, 0.90, 1.40, 0.66), A, slope=0.035,
                groove=0.015, panel_h=0.015, tags=tags)
        _sshard(f"fang_lo_{side}", f(fang_lo), 0.40, _ramp(2.36, 0.74, 1.70, 0.60), A, slope=0.035,
                groove=0.015, panel_h=0.015, tags=tags)
        # brasa no fundo da garganta: 3 pips entre as pontas dos dentes
        B.box(f"maw_bed{sx}", cx, 1.55, 0.12, 0.26, 0.40, 0.41, BLK, bevel=0.0, tags=tags)
        for i in range(3):
            B.box(f"maw_glow{sx}{i}", cx, 1.47 + i * 0.08, 0.075, 0.024, 0.41, 0.418, M["glow_dim"], bevel=0.0,
                  tags=tags)

    # ---------------------------------------------------------------- nivel 2: glacis inclinado + ombros
    # glacis sem a presa (a presa virou peca propria): borda interna acompanha o nariz da espinha
    glacis = [(-0.57, -0.16), (-1.42, -0.48), (-1.42, 0.40), (-1.10, 0.86), (-0.36, 0.86), (-0.57, 0.30)]
    shoulder = [(-0.57, -0.29), (-1.42, -0.61), (-1.42, -1.08), (-1.24, -1.26), (-0.57, -1.26)]
    fin = [(-0.72, -0.50), (-0.72, -1.14), (-1.04, -1.14), (-1.16, -1.00), (-1.16, -0.66)]
    gz = _ramp(-0.48, 1.20, 1.40, 0.80)
    seam = math.degrees(math.atan2(0.32, 0.85))   # angulo da emenda glacis/ombro (chevron)
    diag = math.degrees(math.atan2(0.21, 0.56))   # angulo da borda interna dianteira do glacis
    for side, sx in (("L", -1), ("R", 1)):
        f = _side(sx)
        ga, gp = _sshard(f"glacis_{side}", f(glacis), 0.80, gz, A, slope=0.10, groove=0.04, panel_h=0.03,
                         tags=tags)
        # linha transversal (segue a rampa) e par de linhas paralelas a borda interna (perto dos dentes)
        _lines(gp, f"gpl{side}", [(sx * 0.98, 0.40, 0.46, 90)], gz(0, 0.40) + 0.03, K)
        _lines(gp, f"gpd{side}", [(sx * 0.66, 0.62, 0.22, sx * diag), (sx * 0.76, 0.66, 0.16, sx * diag)],
               gz(0, 0.74) + 0.03, K)
        # escotilha do municiador: retangulo alinhado a emenda chevron, recuado para fora do eixo do sensor;
        # recorte e tampa inclinados junto com a rampa do glacis (profundidade constante)
        hx, hy, hr = sx * 1.095, -0.07, -sx * seam
        hcut = B.rpoly(hx, hy, 0.30, 0.17, hr)
        for t in (ga, gp):
            B.cut(t, [_zloft(f"hatchc{side}", hcut, hcut, lambda x, y: gz(0, y) - 0.02,
                             lambda x, y: gz(0, y) + 0.4, K, bevel=0.0)])
        _zloft(f"hatchbed{side}", hcut, hcut, lambda x, y: gz(0, y) - 0.035, lambda x, y: gz(0, y) - 0.018, BLK,
               bevel=0.0, tags=tags)
        hlid = B.rpoly(hx, hy, 0.25, 0.125, hr, chamfer=0.025)
        _zloft(f"hatch{side}", hlid, B.offset_poly(hlid, 0.012), lambda x, y: gz(0, y) - 0.03,
               lambda x, y: gz(0, y) + 0.008, A, bevel=0.006, tags=tags)
        a = math.radians(hr)
        hh = B.rpoly(hx - math.sin(a) * 0.035, hy + math.cos(a) * 0.035, 0.12, 0.022, hr)
        _zloft(f"hatchh{side}", hh, hh, lambda x, y: gz(0, y) + 0.004, lambda x, y: gz(0, y) + 0.026, S, bevel=0.004,
               tags=tags)
        # o bisel reaplicado depois dos recortes dobra o painel inclinado (faces nao planas): o painel ja
        # tem chanfro proprio (topo recuado 0.012), entao fica sem o modificador
        if gp is not None and gp.modifiers.get("bevel"):
            gp.modifiers.remove(gp.modifiers["bevel"])
        B.shard(f"shoulder_{side}", f(shoulder), 0.84, 1.20, A, slope=0.10, groove=0.04, panel_h=0.03, tags=tags)
        fa, fp = B.shard(f"fin_{side}", f(fin), 1.20, 1.34, A, slope=0.05, groove=0.03, panel_h=0.02, tags=tags)
        Mo.slot_with_pips(f"fslot{side}", sx * 0.94, -1.00, -0.70, 0.065, 1.36, 4, M, tags, target=[fa, fp],
                          depth=0.07)

    # ---------------------------------------------------------------- maquinaria nos vaos laterais
    for sx in (-1, 1):
        x = sx * 1.62
        # elevador de granadas: trilhos de aco com 3 granadas subindo
        for j in (-1, 1):
            B.box(f"hrail{sx}{j}", x + j * 0.13, -0.50, 0.03, 1.40, 0.40, 0.50, S, bevel=0.006, tags=tags)
        for i, y in enumerate((-1.02, -0.62, -0.22)):
            B.cyl(f"shell{sx}{i}", x, y, 0.47, 0.075, 0.24, KM, axis="Y", verts=8, bevel=0.006, tags=tags)
            B.cyl(f"shelltip{sx}{i}", x, y + 0.17, 0.47, 0.075, 0.10, S, axis="Y", verts=8, bevel=0.0,
                  r2=0.02, tags=tags)
            B.cyl(f"shellband{sx}{i}", x, y - 0.06, 0.47, 0.08, 0.025, AM, axis="Y", verts=8, bevel=0.0,
                  tags=tags)
        # tambor de carregador com contador ambar
        B.cyl(f"drum{sx}", x, 0.42, 0.50, 0.15, 0.62, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
        for i, y in enumerate((0.16, 0.42, 0.68)):
            B.cyl(f"drumring{sx}{i}", x, y, 0.50, 0.162, 0.04, S, axis="Y", verts=8, bevel=0.005, tags=tags)
        for i in range(4):
            B.box(f"drumled{sx}{i}", x, 0.22 + i * 0.06, 0.035, 0.03, 0.64, 0.66,
                  M["glow"] if i < 3 else BLK, bevel=0.0, tags=tags)
        # calha: da ponta do tambor ate o flanco do berco externo (ao lado da culatra)
        c0, c1 = (sx * 1.64, 0.74), (sx * 1.18, 0.98)
        ux, uy = c1[0] - c0[0], c1[1] - c0[1]
        ln = math.hypot(ux, uy)
        ux, uy = ux / ln, uy / ln
        yaw = math.degrees(math.atan2(-ux, uy))
        mx, my = (c0[0] + c1[0]) / 2, (c0[1] + c1[1]) / 2
        B.cyl(f"chute{sx}", mx, my, 0.50, 0.085, ln, KM, axis="Y", verts=8, yaw=yaw, tags=tags)
        for i in range(3):
            t = -0.16 + i * 0.16
            B.cyl(f"chuter{sx}{i}", mx + ux * t, my + uy * t, 0.50, 0.097, 0.03, S, axis="Y", verts=8, yaw=yaw,
                  tags=tags)
        # hastes/cabos no vao entre espinha e glacis
        B.cyl(f"rod{sx}", sx * 0.52, -0.42, 0.90, 0.022, 1.26, S, axis="Y", verts=8, tags=tags)
        B.box(f"gapmod{sx}", sx * 0.52, -1.10, 0.06, 0.18, 0.86, 0.94, KM, bevel=0.01, tags=tags)
        B.box(f"gapled{sx}", sx * 0.52, -1.10, 0.026, 0.09, 0.94, 0.95, M["glow"], bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- nivel 3: espinha com sensor
    # espinha maior (seta central dominante) com o nariz avancando ate a linha dos bercos
    spine = [(-0.40, -1.12), (0.40, -1.12), (0.47, -1.00), (0.47, 0.22), (0.19, 0.86), (-0.19, 0.86),
             (-0.47, 0.22), (-0.47, -1.00)]
    sa, sp = B.shard("spine", spine, 0.90, 1.38, A, slope=0.08, groove=0.03, panel_h=0.025, tags=tags)
    sp2 = [(-0.25, -0.84), (0.25, -0.84), (0.30, -0.74), (0.30, 0.18), (0.11, 0.60), (-0.11, 0.60),
           (-0.30, 0.18), (-0.30, -0.74)]
    s2 = B.plate("spine2", sp2, 1.40, 1.50, A, slope=0.035, tags=tags)
    win = [(-0.16, 0.04), (0.16, 0.04), (0.16, 0.17), (0.06, 0.37), (-0.06, 0.37), (-0.16, 0.17)]
    B.cut(s2, [B.loft("win_cut", win, win, 1.46, 1.8, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 1.455, 1.465, BLK, bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, 0.11, 0.22, 0.036, 1.46, 1.472, M["lens"], bevel=0.0, tags=tags)
    Mo.slot_with_pips("sp", -0.40, -0.15, 0.15, 0.05, 1.50, 3, M, tags, target=s2, depth=0.03, vertical=False)
    _lines(s2, "s2l", [(0.0, -0.66, 0.30, 90)], 1.50, K)
    _lines(sp, "spl", [(0.0, -0.95, 0.40, 90)], 1.405, K)
    # quinas do nariz: linhas que reforcam a ponta de flecha
    _lines(sp, "spn", [(-0.24, 0.52, 0.22, -24), (0.24, 0.52, 0.22, 24)], 1.405, K)

    # ---------------------------------------------------------------- ponte do telemetro (traseira)
    # bracos enflechados em dois degraus: capuz interno alto + braco externo baixo, com vao escuro;
    # a casa central fica na ponta do chevron
    rot0 = math.degrees(math.atan(K_RF))
    for side, sx in (("L", -1), ("R", 1)):
        f = _side(sx)
        rot = -sx * rot0
        hood = [(-0.74, _rf_front(0.74)), (-1.56, _rf_front(1.56)), (-1.44, _rf_back(1.44)),
                (-0.74, _rf_back(0.74))]
        arm = [(-1.62, _rf_front(1.62)), (-2.30, _rf_front(2.30)), (-2.40, _rf_front(2.40) - 0.08),
               (-2.40, _rf_back(2.40) + 0.08), (-2.30, _rf_back(2.30)), (-1.50, _rf_back(1.50))]
        ha_, hp_ = B.shard(f"rf_hood{side}", f(hood), 0.84, 1.30, A, slope=0.08, groove=0.03, panel_h=0.025,
                           tags=tags)
        ra, rp = B.shard(f"rf_arm{side}", f(arm), 0.84, 1.16, A, slope=0.07, groove=0.03, panel_h=0.022,
                         tags=tags)
        # janelas oticas segmentadas (vidro escuro + uma pip curta cada), alinhadas do capuz ao braco
        for i, (wxa, objs, zt) in enumerate(((1.16, (ha_, hp_), 1.30), (1.90, (ra, rp), 1.16),
                                             (2.18, (ra, rp), 1.16))):
            wx = sx * wxa
            wy = (_rf_front(wxa) + _rf_back(wxa)) / 2
            for t in objs:
                B.cut(t, [B.rbox(f"rf_wc{side}{i}", wx, wy, 0.26, 0.08, zt - 0.03, zt + 0.4, K, rot=rot,
                                 bevel=0.0)])
            B.rbox(f"rf_wbed{side}{i}", wx, wy, 0.26, 0.08, zt - 0.045, zt - 0.03, BLK, rot=rot, bevel=0.0,
                   tags=tags)
            B.rbox(f"rf_glass{side}{i}", wx, wy, 0.22, 0.05, zt - 0.03, zt - 0.022, _glass(), rot=rot, bevel=0.0,
                   tags=tags)
            B.rbox(f"rf_pip{side}{i}", wx, wy, 0.07, 0.016, zt - 0.022, zt - 0.016, M["glow_dim"], rot=rot,
                   bevel=0.0, tags=tags)
        # linhas de painel transversais no capuz e no braco
        _lines(hp_, f"rf_hl{side}", [(sx * 0.92, _rf_back(0.92) + 0.10, 0.12, 0)], 1.325, K)
        _lines(rp, f"rf_al{side}", [(sx * 1.70, (_rf_front(1.70) + _rf_back(1.70)) / 2, 0.20, rot)], 1.18, K)
    rhouse = [(-0.66, -1.86), (0.66, -1.86), (0.80, -1.72), (0.80, -1.46), (0.30, -1.24), (-0.30, -1.24),
              (-0.80, -1.46), (-0.80, -1.72)]
    ha, hp = B.shard("rf_house", rhouse, 1.20, 1.44, A, slope=0.07, groove=0.03, panel_h=0.022, tags=tags)
    Mo.slot_with_pips("rfh", -1.62, -0.40, 0.40, 0.06, 1.465, 5, M, tags, target=[ha, hp], depth=0.05,
                      vertical=False)
    _lines(hp, "rfhl", [(-0.30, -1.44, 0.16, 70), (0.30, -1.44, 0.16, -70)], 1.465, K)
    # casulos oticos nas pontas (o ponto mais largo da torre) com objetiva e luz de alerta vermelha
    pod = [(-2.38, -1.50), (-2.66, -1.50), (-2.80, -1.64), (-2.80, -1.86), (-2.60, -2.12), (-2.38, -2.12)]
    py_ = -1.80
    for side, sx in (("L", -1), ("R", 1)):
        f = _side(sx)
        pa, pp = B.shard(f"rf_pod{side}", f(pod), 0.80, 1.32, A, slope=0.07, groove=0.026, panel_h=0.022,
                         tags=tags)
        for t in (pa, pp):
            B.cut(t, [B.box(f"rf_oc{side}", sx * 2.80, py_ + 0.02, 0.16, 0.18, 0.86, 1.6, K, bevel=0.0)])
        B.box(f"rf_obed{side}", sx * 2.755, py_ + 0.02, 0.07, 0.18, 0.84, 0.87, BLK, bevel=0.0, tags=tags)
        B.cyl(f"rf_obj{side}", sx * 2.76, py_ + 0.02, 1.02, 0.06, 0.06, KM, axis="X", verts=8, bevel=0.006,
              tags=tags)
        B.cyl(f"rf_objr{side}", sx * 2.775, py_ + 0.02, 1.02, 0.068, 0.016, S, axis="X", verts=8, bevel=0.004,
              tags=tags)
        # luz de alerta: rebaixo preto com led vermelho e um branco
        for t in (pa, pp):
            B.cut(t, [B.box(f"rf_lc{side}", sx * 2.56, py_, 0.10, 0.22, 1.28, 1.6, K, bevel=0.0)])
        B.box(f"rf_lbed{side}", sx * 2.56, py_, 0.10, 0.22, 1.27, 1.285, BLK, bevel=0.0, tags=tags)
        B.box(f"rf_red{side}", sx * 2.56, py_ + 0.06, 0.05, 0.05, 1.285, 1.295, M["red"], bevel=0.0, tags=tags)
        B.box(f"rf_wht{side}", sx * 2.56, py_ - 0.06, 0.05, 0.05, 1.285, 1.295, _white(), bevel=0.0, tags=tags)
        _lines(pp, f"rf_pl{side}", [(sx * 2.52, py_ + 0.20, 0.14, 90), (sx * 2.52, py_ - 0.20, 0.14, 90)], 1.345, K)

    # ---------------------------------------------------------------- baia de exaustao traseira (trapezio)
    yf, yr, wf, wr = -1.96, -2.80, 1.28, 1.14
    hw = lambda y: wr + (wf - wr) * (y - yr) / (yf - yr)  # noqa: E731
    bay = [(-wf, yf), (wf, yf), (wr, yr), (-wr, yr)]
    B.loft("vent_bay", bay, bay, 0.22, 0.42, BLK, bevel=0.0, tags=tags)
    for i in range(12):
        y = -2.72 + i * 0.05
        B.box(f"louver{i}", 0, y, 2 * (hw(y) - 0.04), 0.022, 0.32, 0.43, KM, bevel=0.004, tags=tags)
    for j, x in enumerate((-0.82, 0.0, 0.82)):
        B.box(f"vrib{j}", x, -2.40, 0.05, 0.76, 0.30, 0.46, S, bevel=0.008, tags=tags)
    for i in range(9):
        B.box(f"vent_pip{i}", -1.12 + i * 0.28, -2.04, 0.08, 0.028, 0.38, 0.44, M["glow"], bevel=0.0, tags=tags)
    B.box("vent_lip", 0, -1.97, 2.52, 0.025, 0.38, 0.52, BLK, bevel=0.0, tags=tags)
    B.bolts("bolt", [(x, -2.84) for x in (-1.0, -0.35, 0.35, 1.0)], 0.40, 0.024, S, tags=tags)


def _white():
    return B.mat_glow("white_led", (1.0, 0.92, 0.85), 5.0)


def _turbine(M, tags, name, cx, cy, sx, R=0.3):
    """Turbina de exaustao vista de cima: poco preto, brasa no fundo, rotor de 9 pas, cubo e aro."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    B.cyl(f"{name}_well", cx, cy, 0.30, R - 0.01, 0.06, M["black"], axis="Z", verts=24, bevel=0.0, tags=tags)
    B.cyl(f"{name}_ember", cx, cy, 0.335, R * 0.66, 0.01, M["ember"], axis="Z", verts=24, bevel=0.0, tags=tags)
    for i in range(9):
        a = math.radians(i * 40 + 10)
        B.rbox(f"{name}_bl{i}", cx + math.cos(a) * R * 0.5, cy + math.sin(a) * R * 0.5, R * 0.2, R * 0.66,
               0.42, 0.46, KM, rot=math.degrees(a) - 90 + sx * 28, bevel=0.004, tags=tags)
    B.cyl(f"{name}_hub", cx, cy, 0.47, R * 0.25, 0.06, S, axis="Z", verts=12, bevel=0.01, tags=tags)
    B.cyl(f"{name}_hubc", cx, cy, 0.505, R * 0.1, 0.02, K, axis="Z", verts=12, bevel=0.0, tags=tags)
    B.torus(f"{name}_rim", cx, cy, 0.48, R - 0.025, 0.022, S, tags=tags)


# ============================================================================ cano
def barrel(M, L=4.0, T="barrel", phase=0.0):
    """Cano de 406 mm com raiz (y=0) e boca (y=L), centrado em x=0, altura BZ."""
    tags = (T,)
    hot = (T, "hot")  # partes que brilham de calor depois do tiro
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = BZ
    # bolsa de culatra (lona) escura com pregas - igual ao toco do berco na cabeca
    B.cyl("b_bag", 0, 0.27, z, 0.255, 0.54, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
    for i in range(5):
        B.cyl(f"b_pleat{i}", 0, 0.06 + i * 0.105, z, 0.272, 0.035, K, axis="Y", verts=8, bevel=0.005, tags=tags)
    B.cyl("b_bagcap", 0, 0.56, z, 0.265, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    # luva de recuo grossa (clara), canal escuro com trilho de aco e dois aros
    y0, y1 = 0.585, 1.47
    sl = B.cyl("b_sleeve", 0, (y0 + y1) / 2, z, 0.29, y1 - y0, A, axis="Y", verts=8, bevel=0.012, tags=tags,
               r2=0.28)
    B.cut(sl, [B.box("b_slc", 0, (y0 + y1) / 2, 0.11, y1 - y0 - 0.14, z + 0.13, z + 0.5, K, bevel=0.0)])
    B.box("b_slbed", 0, (y0 + y1) / 2, 0.11, y1 - y0 - 0.14, z + 0.11, z + 0.14, M["black"], bevel=0.0,
          tags=tags)
    B.box("b_slrail", 0, (y0 + y1) / 2, 0.03, y1 - y0 - 0.20, z + 0.13, z + 0.16, S, bevel=0.004, tags=tags)
    for i, y in enumerate((0.74, 1.32)):
        B.cyl(f"b_hoop{i}", 0, y, z, 0.302, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    # degrau de aco entre a luva e o tubo
    B.cyl("b_step", 0, 1.50, z, 0.272, 0.06, S, axis="Y", verts=8, bevel=0.008, tags=tags)
    # tubo afunilado com canal escuro; o trecho final e 'hot' (o calor do freio escorre um pouco)
    yt0, yh, yt1 = 1.53, 2.78, 3.16
    rt0, rt1 = 0.25, 0.212
    rh = rt0 + (rt1 - rt0) * (yh - yt0) / (yt1 - yt0)
    t1 = B.cyl("b_tube", 0, (yt0 + yh) / 2, z, rt0, yh - yt0, A, axis="Y", verts=8, bevel=0.008, tags=tags, r2=rh)
    t2 = B.cyl("b_tubeh", 0, (yh + yt1) / 2, z, rh, yt1 - yh, A, axis="Y", verts=8, bevel=0.008, tags=hot, r2=rt1)
    for t in (t1, t2):
        B.cut(t, [B.box("b_tc", 0, (yt0 + yt1) / 2, 0.075, yt1 - yt0 - 0.10, z + 0.10, z + 0.5, K, bevel=0.0)])
    B.box("b_tbed", 0, (yt0 + yt1) / 2, 0.075, yt1 - yt0 - 0.10, z + 0.08, z + 0.11, M["black"], bevel=0.0,
          tags=tags)
    # extrator de gases (bojo facetado)
    ye = 2.22
    fume = B.cyl("b_fume", 0, ye, z, 0.295, 0.34, A, axis="Y", verts=8, bevel=0.015, tags=tags)
    B.cut(fume, [B.box("b_fumec", 0, ye, 0.075, 0.42, z + 0.12, z + 0.5, K, bevel=0.0)])
    B.cyl("b_fumecone0", 0, ye - 0.215, z, 0.24, 0.09, A, axis="Y", verts=8, bevel=0.0, tags=tags, r2=0.295)
    B.cyl("b_fumecone1", 0, ye + 0.215, z, 0.295, 0.09, A, axis="Y", verts=8, bevel=0.0, tags=tags, r2=0.23)
    for i, y in enumerate((ye - 0.10, ye + 0.10)):
        B.cyl(f"b_fumeband{i}", 0, y, z, 0.302, 0.03, AM, axis="Y", verts=8, bevel=0.004, tags=tags)
    B.cyl("b_collar0", 0, 1.60, z, 0.265, 0.05, AM, axis="Y", verts=8, bevel=0.008, tags=tags)
    B.cyl("b_collar1", 0, 2.78, z, 0.238, 0.05, AM, axis="Y", verts=8, bevel=0.008, tags=hot)
    B.cyl("b_collar2", 0, 3.13, z, 0.228, 0.05, AM, axis="Y", verts=8, bevel=0.008, tags=hot)
    # freio de boca da capitania: estagio traseiro estreito + estagio dianteiro mais largo em "cabeca de
    # martelo" (ecoa a ponte do telemetro), nariz em ponta de flecha; portas transversais escuras e
    # entalhes laterais, ranhura funda no degrau entre os estagios
    yb0 = 3.18
    B.cyl("b_brakering", 0, yb0 + 0.015, z, 0.25, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=hot)
    ys0, ys1, yf0, yn = yb0 + 0.03, 3.44, 3.54, 3.80
    hw0, hw1 = 0.30, 0.355
    brake = [(-0.26, ys0), (0.26, ys0), (hw0, ys0 + 0.05), (hw0, ys1), (hw1, yf0), (hw1, yn), (0.21, L), (-0.21, L),
             (-hw1, yn), (-hw1, yf0), (-hw0, ys1), (-hw0, ys0 + 0.05)]
    br = B.plate("b_brake", brake, z - 0.17, z + 0.17, A, slope=0.05, tags=hot)
    cuts = []
    for i, y in enumerate((3.33,)):
        cuts.append(B.box(f"b_bc{i}", 0, y, 0.70, 0.05, z + 0.03, z + 0.4, K, bevel=0.0))
        for sx in (-1, 1):
            cuts.append(B.box(f"b_bn{i}{sx}", sx * hw0, y, 0.08, 0.05, z - 0.3, z + 0.4, K, bevel=0.0))
    cuts.append(B.box("b_bstep", 0, 3.49, 0.80, 0.05, z - 0.02, z + 0.4, K, bevel=0.0))
    for i, y in enumerate((3.63, 3.75)):
        cuts.append(B.box(f"b_bf{i}", 0, y, 0.80, 0.05, z + 0.03, z + 0.4, K, bevel=0.0))
        for sx in (-1, 1):
            cuts.append(B.box(f"b_bfn{i}{sx}", sx * hw1, y, 0.10, 0.05, z - 0.3, z + 0.4, K, bevel=0.0))
    cuts.append(B.box("b_bore_c", 0, L, 0.14, 0.14, z - 0.07, z + 0.4, K, bevel=0.0))
    B.cut(br, cuts)
    # nucleo escuro (aparece no fundo das portas), dentro do contorno dos dois estagios
    B.box("b_brake_core", 0, 3.37, 0.50, 0.22, z - 0.13, z + 0.04, K, bevel=0.0, tags=tags)
    B.box("b_brake_core2", 0, 3.67, 0.60, 0.40, z - 0.13, z + 0.04, K, bevel=0.0, tags=tags)
    # aresta central do nariz (crista) para reforcar a ponta de flecha
    B.box("b_crest", 0, L - 0.11, 0.03, 0.14, z + 0.10, z + 0.175, AM, bevel=0.004, tags=hot)


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto: placas do conves (verde = pintura) + faixa de 6 tiles com 3 conjuntos de portas duplas."""
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
    # anel da torre (sem pintura)
    B.torus("ringbear", px, py, 0.08, ring_r + 0.02, 0.055, M["core_mid"], tags=tags)
    B.cyl("ringhole", px, py, 0.05, ring_r - 0.01, 0.1, M["black"], axis="Z", verts=96, bevel=0.0, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(px, py, ring_r + 0.11, 44) if abs(x) < W / 2 - 0.06 and
           abs(y) < H / 2 - 0.06]
    B.bolts("rb", pts, 0.1, 0.022, M["steel"], tags=tags)
    # faixa de carregadores na fileira de tras: 3 conjuntos de portas duplas em chevron + respiros
    sy = -H / 2 + 0.5
    strip = B.plate("magstrip", B.rpoly(0, sy, W - 0.10, 0.88, 0, chamfer=0.12), 0.0, 0.11, M["core_mid"],
                    slope=0.025, tags=tags)
    rec = []
    for k in range(3):
        cx = -2.0 + 2.0 * k
        rec.append(B.box(f"ledc{k}", cx, sy - 0.33, 0.60, 0.06, 0.08, 0.3, M["core"], bevel=0.0))
    for k in range(2):
        rec.append(B.box(f"ventc{k}", -1.0 + 2.0 * k, sy + 0.04, 0.16, 0.50, 0.075, 0.3, M["core"], bevel=0.0))
    for sx in (-1, 1):
        rec.append(B.box(f"ventce{sx}", sx * 2.90, sy + 0.04, 0.06, 0.40, 0.075, 0.3, M["core"], bevel=0.0))
    B.cut(strip, rec)
    for k in range(3):
        cx = -2.0 + 2.0 * k
        y0, y1 = sy - 0.24, sy + 0.36
        for j, sx in enumerate((-1, 1)):
            # folha da porta: chevron que aponta para a frente, encontra a outra no meio
            leaf = [(cx + sx * 0.04, y0), (cx + sx * 0.66, y0), (cx + sx * 0.78, y0 + 0.12),
                    (cx + sx * 0.78, y1 - 0.20), (cx + sx * 0.58, y1), (cx + sx * 0.04, y1)]
            da, dp = B.shard(f"door{k}{j}", leaf, 0.10, 0.15, M["armor_mid"], slope=0.02, groove=0.03,
                             panel_h=0.015, tags=tags)
            B.cut(dp, [B.box(f"dgr{k}{j}", cx + sx * 0.42, sy + 0.06, 0.016, 0.40, 0.15, 0.3, M["core"],
                             bevel=0.0)])
            B.box(f"dhinge{k}{j}", cx + sx * 0.745, sy + 0.04, 0.04, 0.26, 0.15, 0.178, M["steel"], bevel=0.008,
                  tags=tags)
            B.box(f"dpad{k}{j}", cx + sx * 0.22, y0 + 0.14, 0.16, 0.035, 0.165, 0.185, M["steel"], bevel=0.006,
                  tags=tags)
        # trava central (barra de aco na emenda das folhas)
        B.box(f"dlatch{k}", cx, sy + 0.04, 0.05, 0.50, 0.15, 0.19, M["steel"], bevel=0.01, tags=tags)
        B.box(f"dslot{k}", cx, sy - 0.33, 0.60, 0.06, 0.075, 0.085, M["black"], bevel=0.0, tags=tags)
        for i in range(3):
            B.box(f"dled{k}{i}", cx - 0.18 + i * 0.18, sy - 0.33, 0.11, 0.022, 0.085, 0.092, M["glow_dim"],
                  bevel=0.0, tags=tags)
    for k in range(2):
        vx = -1.0 + 2.0 * k
        B.box(f"vbed{k}", vx, sy + 0.04, 0.16, 0.50, 0.07, 0.08, M["black"], bevel=0.0, tags=tags)
        for i in range(5):
            B.box(f"vlouver{k}{i}", vx, sy - 0.16 + i * 0.10, 0.14, 0.026, 0.08, 0.105, M["core_mid"],
                  bevel=0.004, tags=tags)
    for sx in (-1, 1):
        B.box(f"vbede{sx}", sx * 2.90, sy + 0.04, 0.06, 0.40, 0.07, 0.08, M["black"], bevel=0.0, tags=tags)


def floor(M, T="floor"):
    """Piso: placas, anel com tronco de 3 elevadores, 10 postos, esteira e estantes de granadas."""
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
    B.plate("fl_trunk", B.rpoly(px, py, 2.6, 2.6, 0, chamfer=0.74), 0.02, 0.07, M["core_mid"], slope=0.03,
            tags=tags)
    w = ring_r * 0.5
    oct_ = lambda s: B.rpoly(px, py, s, s, 0, chamfer=s / (2 + math.sqrt(2)))  # noqa: E731
    B.plate("fl_hub", oct_(w), 0.05, 0.12, M["armor_mid"], slope=0.03, tags=tags)
    B.plate("fl_hubc", oct_(w * 0.52), 0.10, 0.125, M["core"], slope=0.015, tags=tags)
    B.plate("fl_hubs", oct_(w * 0.18), 0.12, 0.15, M["steel"], slope=0.01, bevel=0.006, tags=tags)
    B.bolts("fl_hubb", B.ring_points(px, py, w * 0.38, 8, math.pi / 8), 0.125, 0.018, M["steel"], tags=tags)
    for k in range(4):
        a = k * math.pi / 2
        cx, cy = px + math.cos(a) * ring_r * 0.62, py + math.sin(a) * ring_r * 0.62
        arrow = [(0.14, 0.0), (-0.08, 0.14), (-0.03, 0.0), (-0.08, -0.14)]
        ca, sa = math.cos(a), math.sin(a)
        arrow = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in arrow]
        B.plate(f"fl_chev{k}", arrow, 0.05, 0.08, M["armor"], slope=0.01, bevel=0.006, tags=tags)
    # tres elevadores de granadas (um por cano)
    for k, dx in enumerate((-0.9, 0.0, 0.9)):
        hx, hy = px + dx, py - 1.15
        B.cyl(f"fl_hoist{k}", hx, hy, 0.10, 0.17, 0.12, M["armor_mid"], axis="Z", verts=8, bevel=0.01, tags=tags)
        B.cyl(f"fl_hoistc{k}", hx, hy, 0.17, 0.10, 0.04, M["steel"], axis="Z", verts=8, bevel=0.005, tags=tags)
        B.box(f"fl_hoistl{k}", hx, hy + 0.21, 0.12, 0.025, 0.04, 0.07, M["glow_dim"], bevel=0.0, tags=tags)
    B.box("fl_led_t", px, py + ring_r * 0.96, 0.4, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    B.box("fl_led_b", px, py - ring_r * 0.96, 0.4, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # esteira de granadas ao longo da parede de tras (sob as 3 portas duplas do teto)
    ey = -H / 2 + 0.19
    B.box("fl_conv", 0, ey, W - 0.30, 0.12, 0.0, 0.10, M["armor_mid"], bevel=0.01, tags=tags)
    for k in range(3):
        cx = -2.0 + 2.0 * k
        for j in range(4):
            _shell_x(M, tags, f"fl_sh{k}{j}", cx - 0.54 + j * 0.36, ey, 0.15)
    # estantes de granadas nos cantos fora do anel (3 granadas deitadas apontando para a frente)
    for k, (rx, ry) in enumerate(((-2.50, 2.98), (2.50, 2.98), (-2.50, -2.16), (2.50, -2.16))):
        B.plate(f"fl_rack{k}", B.rpoly(rx, ry, 0.66, 0.56, 0, chamfer=0.08), 0.0, 0.06, M["armor_mid"], slope=0.02,
                tags=tags)
        for j in (-1, 1):
            B.box(f"fl_rackb{k}{j}", rx, ry + j * 0.16, 0.62, 0.04, 0.06, 0.12, M["steel"], bevel=0.006, tags=tags)
        for i in range(3):
            x = rx - 0.19 + i * 0.19
            B.cyl(f"fl_rs{k}{i}", x, ry - 0.04, 0.14, 0.075, 0.30, M["core_mid"], axis="Y", verts=8, bevel=0.006,
                  tags=tags)
            B.cyl(f"fl_rst{k}{i}", x, ry + 0.17, 0.14, 0.075, 0.12, M["steel"], axis="Y", verts=8, bevel=0.0,
                  r2=0.02, tags=tags)
            B.cyl(f"fl_rsb{k}{i}", x, ry - 0.12, 0.14, 0.08, 0.025, M["armor_mid"], axis="Y", verts=8, bevel=0.0,
                  tags=tags)
        B.box(f"fl_rled{k}", rx, ry - 0.25, 0.20, 0.03, 0.06, 0.075, M["glow_dim"], bevel=0.0, tags=tags)
    for i, (cx, cy, _r) in enumerate(crew_positions(W, H, 10, pv)):
        x, y = cx - W / 2, H / 2 - cy
        B.box(f"seat{i}", x, y + 0.02, 0.30, 0.28, 0.0, 0.14, M["armor"], bevel=0.04, tags=tags)
        B.box(f"console{i}", x, y + 0.30, 0.40, 0.12, 0.0, 0.22, M["core_mid"], bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.30, 0.30, 0.06, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)


def _shell_x(M, tags, name, x, y, z):
    """Granada deitada no eixo X (ponta para +x): corpo escuro, cinta e ogiva de aco."""
    B.cyl(name, x - 0.03, y, z, 0.045, 0.20, M["core_mid"], axis="X", verts=8, bevel=0.004, tags=tags)
    B.cyl(name + "t", x + 0.11, y, z, 0.045, 0.08, M["steel"], axis="X", verts=8, bevel=0.0, r2=0.012, tags=tags)
    B.cyl(name + "b", x - 0.09, y, z, 0.05, 0.02, M["armor_mid"], axis="X", verts=8, bevel=0.0, tags=tags)
