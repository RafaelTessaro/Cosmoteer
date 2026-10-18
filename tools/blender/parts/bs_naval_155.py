"""Canhao Naval Duplo 155 mm ("Trovao") - torre dupla de encouracado, mesma familia do 76 mm.

Bloco escuro da casa de canhoes coberto por placas claras em varios niveis (ombreiras macicas,
ombros divididos em chevron, aletas com pips, espinha com sensor e o raio do "Trovao" gravado num
rebaixo escuro), cunha frontal larga (garras laterais + bercos em cunha + proa central entre os canos),
orelhas de telemetro: casulos blindados que saem dos flancos e giram (animacao da torre), tambores de
municao nos vaos, baia de exaustao traseira e faixa de carregadores com 4 escotilhas emolduradas no teto.
Dois canos pesados: bolsa de culatra escura, luva de recuo com aros, tubo em dois estagios (tubo A +
cano fino) com extrator de gases e freio de boca em dois estagios na linguagem do 76 mm: camaras claras
facetadas apontando para a frente (a da frente em ponta de flecha) com janelas transversais escuras, que
brilham de calor (o calor escorre um pouco para o fim do cano fino).
"""

import math

import bpy

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_naval_155",
    "kind": "gun",
    "size": [4, 5],
    "pivot": [2.0, 2.1],           # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 3.9,             # lado do quadrado do sprite da torre
    "ring_r": 1.78,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "collider": 1.75,
    "barrels": {
        "ys": [-0.45, 0.45],       # dois canos lado a lado
        "root": 1.00,              # pivo -> raiz do cano
        "length": 3.0,             # raiz -> boca
        "width": 0.62,             # largura do sprite do cano (cabe o freio de boca)
        "pad": 0.45,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.40, 0.36, 0.30, 0.23, 0.16, 0.10, 0.05, 0.02],   # recuo rapido, retorno lento
        "heat": [1.0, 0.96, 0.9, 0.82, 0.73, 0.64, 0.55, 0.46, 0.37, 0.28, 0.19, 0.1],
        "interval": 0.07,
    },
    "turret_anim": {"frames": 8, "interval": 0.15},   # tubos de telemetro girando + varredura otica
    "lights": [
        {"at": [0.0, -1.56], "size": 1.8, "color": [255, 120, 30], "z": 0.9},
    ],
    "preview_pattern": "alternate",
}

EAR_Y = -0.96     # centro das orelhas de telemetro (y da cabeca)


def _lines(target, name, specs, ztop, mat):
    """Linhas de painel recortadas no alvo: specs = [(x, y, comprimento, rotacao)]."""
    cuts = [B.rbox(f"{name}{i}", x, y, 0.016, ln, ztop - 0.02, ztop + 0.3, mat, rot=r, bevel=0.0)
            for i, (x, y, ln, r) in enumerate(specs)]
    B.cut(target, cuts)


def _stroke(name, p, q, w, z0, z1, mat, tags):
    """Traco fino (caixa girada) de p ate q; pontas estendidas w/2 para emendar com o proximo."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    rot = math.degrees(math.atan2(-dx, dy))
    return B.rbox(name, (p[0] + q[0]) / 2, (p[1] + q[1]) / 2, w, math.hypot(dx, dy) + w, z0, z1, mat, rot=rot,
                  bevel=0.0, tags=tags)


def _swivel(objs, px, py, deg):
    """Gira um grupo de objetos em torno do eixo Z que passa por (px, py)."""
    emp = bpy.data.objects.new("swivel", None)
    bpy.context.scene.collection.objects.link(emp)
    emp.location = (px, py, 0.0)
    bpy.context.view_layer.update()
    for o in objs:
        o.parent = emp
        o.matrix_parent_inverse = emp.matrix_world.inverted()
    emp.rotation_euler.z = math.radians(deg)
    bpy.context.view_layer.update()


def _ear(M, tags, sx, phase, paul):
    """Orelha de telemetro: casulo blindado que sai do flanco da ombreira (silhueta classica de torre de
    encouracado) e gira +-11 graus num soquete escuro; janela otica no topo com ponto de varredura e
    objetiva num rebaixo da face externa."""
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    y0 = EAR_Y
    f = (lambda p: p) if sx < 0 else Mo.mirror
    # soquete escuro na ombreira: a folga em volta do casulo mostra o giro
    for i, t in enumerate(paul):
        B.cut(t, [B.box(f"ear_sock{sx}{i}", sx * 1.51, y0, 0.38, 0.58, 0.72, 1.3, K, bevel=0.0)])
    B.box(f"ear_bed{sx}", sx * 1.49, y0, 0.34, 0.58, 0.70, 0.725, KM, bevel=0.0, tags=tags)
    before = set(bpy.context.scene.objects)
    # casulo em cunha: canto externo dianteiro bem chanfrado (aponta para a frente/fora)
    pod = [(-1.40, y0 - 0.18), (-1.46, y0 - 0.24), (-1.80, y0 - 0.24), (-1.89, y0 - 0.14), (-1.89, y0 + 0.02),
           (-1.74, y0 + 0.22), (-1.44, y0 + 0.26), (-1.40, y0 + 0.21)]
    ha, hp = B.shard(f"ear_pod{sx}", f(pod), 0.62, 0.98, A, slope=0.06, groove=0.026, panel_h=0.024, tags=tags)
    # janela otica ao longo do topo (fenda escura, lente fina e ponto que varre)
    wx, wy = sx * 1.625, y0 + 0.06
    for t in (ha, hp):
        B.cut(t, [B.box(f"ear_wc{sx}", wx, wy, 0.30, 0.075, 0.965, 1.3, K, bevel=0.0)])
    B.box(f"ear_wbed{sx}", wx, wy, 0.30, 0.075, 0.95, 0.97, M["black"], bevel=0.0, tags=tags)
    B.box(f"ear_lens{sx}", wx, wy, 0.22, 0.014, 0.965, 0.972, M["glow_dim"], bevel=0.0, tags=tags)
    s = 0.5 + 0.5 * math.sin(2 * math.pi * phase)
    B.box(f"ear_scan{sx}", wx + sx * (-0.09 + 0.18 * s), wy, 0.04, 0.04, 0.965, 0.977, M["lens"], bevel=0.0,
          tags=tags)
    # objetiva num rebaixo da face externa (mordida escura com tubo e aro de aco)
    oy = y0 - 0.06
    for t in (ha, hp):
        B.cut(t, [B.box(f"ear_oc{sx}", sx * 1.90, oy, 0.16, 0.14, 0.72, 1.3, K, bevel=0.0)])
    B.box(f"ear_obed{sx}", sx * 1.855, oy, 0.07, 0.14, 0.70, 0.725, M["black"], bevel=0.0, tags=tags)
    B.cyl(f"ear_obj{sx}", sx * 1.85, oy, 0.80, 0.05, 0.08, KM, axis="X", verts=8, bevel=0.006, tags=tags)
    B.cyl(f"ear_objr{sx}", sx * 1.885, oy, 0.80, 0.058, 0.02, S, axis="X", verts=8, bevel=0.004, tags=tags)
    _lines(hp, f"ear_l{sx}", [(sx * 1.62, y0 - 0.075, 0.24, 90)], 1.004, K)
    B.bolts(f"ear_b{sx}", [(sx * 1.50, y0 - 0.14), (sx * 1.76, y0 - 0.14)], 1.006, 0.016, S, tags=tags)
    new = [o for o in bpy.context.scene.objects if o not in before and o.parent is None]
    _swivel(new, sx * 1.50, y0, 11.0 * math.sin(2 * math.pi * phase))


def head(M, T="head", phase=0.0):
    """Cabeca: bloco escuro da casa de canhoes com placas claras em 3-4 niveis, cunha frontal, orelhas."""
    tags = (T,)
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    bolt_m = B.mat_glow("bolt_glow", Mo.AMBER, 0.6)
    # anel giratorio e nucleo escuro (cantos traseiros bem chanfrados: gira sem invadir o teto)
    B.cyl("ring", 0, 0, 0.04, 1.80, 0.08, KM, axis="Z", verts=80, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, 1.72, 32, 0.1), 0.09, 0.024, S, tags=tags)
    core = [(-1.20, -1.76), (1.20, -1.76), (1.66, -1.30), (1.66, 0.86), (1.02, 1.58), (-1.02, 1.58),
            (-1.66, 0.86), (-1.66, -1.30)]
    B.plate("core", core, 0.06, 0.36, K, slope=0.05, tags=tags)
    # bloco escuro da casa de canhoes (nivel 2): aparece nos vaos entre as placas
    house = [(-0.98, -1.36), (0.98, -1.36), (1.08, -1.26), (1.08, 0.34), (0.78, 0.86), (-0.78, 0.86),
             (-1.08, 0.34), (-1.08, -1.26)]
    B.plate("house", house, 0.34, 0.80, KM, slope=0.06, tags=tags)

    # ---------------------------------------------------------------- ombreiras, garras e saia traseira
    # ombreira macica: cresce para fora, borda interna fica em 1.20 (tambores continuam visiveis)
    paul = [(-1.20, -1.38), (-1.48, -1.38), (-1.66, -1.20), (-1.66, -0.20), (-1.80, -0.06), (-1.80, 0.44),
            (-1.56, 0.80), (-1.24, 0.84), (-1.20, 0.70), (-1.20, 0.22), (-1.30, 0.10), (-1.30, -0.40),
            (-1.20, -0.52)]
    # tampa da ombreira com borda traseira diagonal (~31 graus): continua o chevron do glacis
    pcap = [(-1.34, 0.02), (-1.62, -0.15), (-1.72, -0.07), (-1.72, 0.38), (-1.54, 0.64), (-1.34, 0.62)]
    claw = [(-1.60, 0.88), (-1.26, 0.86), (-0.94, 1.04), (-0.79, 1.30), (-0.79, 1.70), (-0.86, 1.84),
            (-0.98, 1.76), (-1.66, 1.06)]
    apron = [(-0.62, -1.88), (-1.04, -1.88), (-1.50, -1.46), (-0.62, -1.46)]
    # ombro da casa dividido em chevron: placa traseira (alta) + cunha frontal (mais baixa)
    shoulder = [(-0.40, -1.24), (-0.74, -1.24), (-1.02, -0.96), (-1.02, -0.30), (-0.40, -0.06)]
    glacis = [(-0.40, 0.02), (-1.02, -0.22), (-1.02, 0.30), (-0.80, 0.72), (-0.70, 0.62), (-0.70, 0.36),
              (-0.40, 0.10)]
    fin = [(-0.56, -1.06), (-0.74, -1.06), (-0.88, -0.92), (-0.88, -0.52), (-0.70, -0.38), (-0.56, -0.44)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        pa, pp = B.shard(f"paul_{side}", f(paul), 0.34, 0.84, A, slope=0.10, groove=0.045, panel_h=0.035,
                         tags=tags)
        ca_, cp_ = B.shard(f"pcap_{side}", f(pcap), 0.86, 0.96, A, slope=0.05, groove=0.025, panel_h=0.02,
                           tags=tags)
        _lines(cp_, f"pcl{side}", [(sx * 1.53, 0.24, 0.26, 0)], 0.98, K)
        Mo.slot_with_pips(f"pslot{side}", sx * 1.48, -0.60, -0.22, 0.06, 0.875, 3, M, tags, target=[pa, pp],
                          depth=0.035)
        # garra frontal (lamina) com fenda acesa
        ca, cp = B.shard(f"claw_{side}", f(claw), 0.34, 0.76, A, slope=0.09, groove=0.035, panel_h=0.03, tags=tags)
        for t in (ca, cp):
            B.cut(t, [B.rbox(f"ccut{side}", sx * 1.22, 1.26, 0.40, 0.05, 0.70, 1.0, K, rot=sx * -40, bevel=0.0)])
        B.rbox(f"cbed{side}", sx * 1.22, 1.26, 0.40, 0.05, 0.68, 0.705, M["black"], rot=sx * -40, bevel=0.0,
               tags=tags)
        B.rbox(f"cglow{side}", sx * 1.22, 1.26, 0.30, 0.016, 0.70, 0.712, M["glow_dim"], rot=sx * -40, bevel=0.0,
               tags=tags)
        _lines(cp, f"cpl{side}", [(sx * 0.90, 1.50, 0.22, 0)], 0.79, K)
        # saia traseira baixa: linha paralela ao chanfro + fenda com 3 pips
        aa, ap = B.shard(f"apron_{side}", f(apron), 0.30, 0.58, A, slope=0.07, groove=0.03, panel_h=0.025,
                         tags=tags)
        _lines(ap, f"apl{side}", [(sx * 1.13, -1.63, 0.17, -sx * 45)], 0.605, K)
        Mo.slot_with_pips(f"aslot{side}", -1.67, sx * 0.74, sx * 0.98, 0.05, 0.605, 3, M, tags,
                          target=[aa, ap], depth=0.03, vertical=False)
        # placa do ombro da casa (nivel 3) e aleta com pips (nivel 4)
        sa, sp = B.shard(f"shoulder_{side}", f(shoulder), 0.78, 1.02, A, slope=0.10, groove=0.04, panel_h=0.03,
                         tags=tags)
        _lines(sp, f"spl{side}", [(sx * 0.50, -0.70, 0.30, 0)], 1.05, K)
        fa, fp = B.shard(f"fin_{side}", f(fin), 1.02, 1.12, A, slope=0.05, groove=0.03, panel_h=0.02, tags=tags)
        Mo.slot_with_pips(f"fslot{side}", sx * 0.73, -0.90, -0.50, 0.06, 1.14, 4, M, tags, target=[fa, fp],
                          depth=0.035)
        ga, gp = B.shard(f"glacis_{side}", f(glacis), 0.76, 0.94, A, slope=0.09, groove=0.035, panel_h=0.025,
                         tags=tags)
        _lines(gp, f"gpl{side}", [(sx * 0.80, 0.50, 0.18, sx * 35)], 0.965, K)
        # periscopio: lente no topo, dentro de um rebaixo preto (nao vaza brilho na blindagem)
        B.box(f"peri{sx}", sx * 0.84, 0.14, 0.16, 0.12, 0.94, 1.02, KM, bevel=0.01, tags=tags)
        B.box(f"perit{sx}", sx * 0.84, 0.10, 0.12, 0.04, 1.02, 1.035, S, bevel=0.004, tags=tags)
        B.box(f"peribed{sx}", sx * 0.84, 0.165, 0.12, 0.04, 1.015, 1.024, M["black"], bevel=0.0, tags=tags)
        B.box(f"perig{sx}", sx * 0.84, 0.165, 0.09, 0.014, 1.022, 1.027, M["glow_dim"], bevel=0.0, tags=tags)
        _ear(M, tags, sx, phase, (pa, pp))

    # ---------------------------------------------------------------- bercos em cunha e culatras (escuros)
    for sx in (-1, 1):
        cx = sx * 0.45
        crad = [(cx - 0.25, 0.60), (cx + 0.25, 0.60), (cx + 0.27, 0.80), (cx + 0.27, 1.52), (cx + 0.14, 1.76),
                (cx - 0.14, 1.76), (cx - 0.27, 1.52), (cx - 0.27, 0.80)]
        c = B.plate(f"cradle{sx}", crad, 0.28, 0.58, KM, slope=0.04, tags=tags)
        B.cut(c, [B.box(f"crad_c{sx}", cx, 1.275, 0.36, 0.61, 0.50, 0.9, K, bevel=0.0)])
        # toco da bolsa de culatra no berco: a bolsa aparece com qualquer ordem de desenho
        B.cyl(f"bagcore{sx}", cx, 1.26, 0.52, 0.165, 0.52, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
        for i in range(5):
            B.cyl(f"bagstub{sx}{i}", cx, 1.06 + i * 0.10, 0.52, 0.19, 0.035, K, axis="Y", verts=8, bevel=0.005,
                  tags=tags)
        B.cyl(f"bagscap{sx}", cx, 1.54, 0.52, 0.18, 0.04, S, axis="Y", verts=8, bevel=0.005, tags=tags)
        for k in (-1, 1):
            B.cyl(f"recup{sx}{k}", cx + k * 0.235, 1.15, 0.57, 0.035, 0.70, S, axis="Y", verts=10, tags=tags)
        # culatra sobre o bloco: anel de aco + soquete
        B.box(f"breech{sx}", cx, 0.62, 0.36, 0.30, 0.78, 0.90, KM, bevel=0.012, tags=tags)
        B.box(f"breechr{sx}", cx, 0.72, 0.40, 0.05, 0.80, 0.92, S, bevel=0.008, tags=tags)
        B.box(f"breechs{sx}", cx, 0.56, 0.16, 0.10, 0.88, 0.905, M["black"], bevel=0.0, tags=tags)
        B.cyl(f"rammer{sx}", cx, 0.30, 0.86, 0.04, 0.40, S, axis="Y", verts=10, tags=tags)
        # calha de alimentacao: do tambor ate a culatra
        B.cyl(f"chute{sx}", sx * 0.98, 0.70, 0.46, 0.055, 0.46, KM, axis="Y", verts=8, yaw=sx * 30, tags=tags)
        for i in range(3):
            B.cyl(f"chuter{sx}{i}", sx * (1.06 - i * 0.07), 0.58 + i * 0.11, 0.46, 0.064, 0.025, S, axis="Y",
                  verts=8, yaw=sx * 30, tags=tags)
        # cabos/hastes no vao entre espinha e ombro
        B.cyl(f"rod{sx}", sx * 0.36, -0.55, 0.83, 0.022, 0.90, S, axis="Y", verts=8, tags=tags)
        B.box(f"gapmod{sx}", sx * 0.36, -1.12, 0.065, 0.16, 0.80, 0.88, KM, bevel=0.01, tags=tags)
        B.box(f"gapled{sx}", sx * 0.36, -1.12, 0.028, 0.08, 0.88, 0.89, M["glow"], bevel=0.0, tags=tags)

    # proa central em cunha entre os canos
    B.shard("prow", [(-0.16, 0.56), (0.16, 0.56), (0.16, 1.34), (0.0, 1.86), (-0.16, 1.34)], 0.40, 0.90,
            A, slope=0.05, groove=0.02, panel_h=0.02, tags=tags)
    B.box("prow_slot", 0, 1.10, 0.05, 0.36, 0.89, 0.93, M["black"], bevel=0.0, tags=tags)

    # espinha (nivel 4, mais larga) com sensor na ponta e o raio (trovao) gravado atras
    spine = [(-0.27, -1.14), (0.27, -1.14), (0.32, -1.04), (0.32, 0.18), (0.14, 0.60), (-0.14, 0.60),
             (-0.32, 0.18), (-0.32, -1.04)]
    sa, sp = B.shard("spine", spine, 0.80, 1.14, A, slope=0.07, groove=0.03, panel_h=0.025, tags=tags)
    sp2 = [(-0.18, -0.90), (0.18, -0.90), (0.21, -0.82), (0.21, 0.10), (0.08, 0.40), (-0.08, 0.40),
           (-0.21, 0.10), (-0.21, -0.82)]
    s2 = B.plate("spine2", sp2, 1.16, 1.26, A, slope=0.035, tags=tags)
    win = [(-0.12, -0.03), (0.12, -0.03), (0.12, 0.08), (0.04, 0.22), (-0.04, 0.22), (-0.12, 0.08)]
    B.cut(s2, [B.loft("win_cut", win, win, 1.22, 1.5, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 1.215, 1.225, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, 0.06, 0.17, 0.03, 1.22, 1.232, M["lens"], bevel=0.0, tags=tags)
    # raio do "Trovao": rebaixo preto largo (~2 px em volta) com canal de energia fino dentro,
    # mesma lingua das fendas acesas (nada de brilho direto na blindagem branca)
    dx = -0.012
    bolt = [(x + dx, y) for x, y in ((0.04, -0.16), (0.10, -0.16), (0.03, -0.35), (0.11, -0.35), (-0.10, -0.76),
                                     (-0.025, -0.44), (-0.08, -0.44))]
    rim = B.offset_poly(bolt, -0.03)          # d negativo = para fora
    B.cut(s2, [B.loft("bolt_cut", rim, rim, 1.23, 1.5, K, bevel=0.0)])
    B.loft("bolt_bed", rim, rim, 1.22, 1.235, M["black"], bevel=0.0, tags=tags)
    path = [(0.07 + dx, -0.18), (-0.04 + dx, -0.40), (0.07 + dx, -0.39), (-0.075 + dx, -0.69)]
    for i in range(3):
        _stroke(f"bolt_glow{i}", path[i], path[i + 1], 0.022, 1.23, 1.236, bolt_m, tags)
    _lines(sp, "spl", [(0.0, -1.00, 0.16, 90)], 1.165, K)

    # ---------------------------------------------------------------- baia de exaustao traseira
    B.box("vent_bay", 0, -1.60, 1.16, 0.44, 0.20, 0.40, M["black"], bevel=0.0, tags=tags)
    for i in range(6):
        B.box(f"louver{i}", 0, -1.78 + i * 0.045, 1.10, 0.02, 0.30, 0.41, KM, bevel=0.004, tags=tags)
    # pips longe da parede da casa: a face inclinada nao reflete uma segunda fileira
    for i in range(6):
        B.box(f"vent_pip{i}", -0.45 + i * 0.18, -1.49, 0.07, 0.026, 0.36, 0.42, M["glow"], bevel=0.0, tags=tags)
    B.box("vent_lip", 0, -1.43, 1.12, 0.025, 0.36, 0.50, M["black"], bevel=0.0, tags=tags)

    # tambores de municao nos vaos laterais (contador ambar) e pistoes do elevador
    for sx in (-1, 1):
        x = sx * 1.14
        B.cyl(f"drum{sx}", x, -0.15, 0.46, 0.10, 0.52, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
        for i, y in enumerate((-0.38, -0.15, 0.08)):
            B.cyl(f"drumring{sx}{i}", x, y, 0.46, 0.112, 0.04, S, axis="Y", verts=8, bevel=0.005, tags=tags)
        for i in range(4):
            B.box(f"drumled{sx}{i}", x, -0.32 + i * 0.055, 0.03, 0.028, 0.55, 0.57,
                  M["glow"] if i < 3 else M["black"], bevel=0.0, tags=tags)
        B.cyl(f"hoist{sx}", sx * 1.14, -0.92, 0.44, 0.035, 0.70, S, axis="Y", verts=10, tags=tags)
        B.cyl(f"hoistb{sx}", sx * 1.14, -1.16, 0.44, 0.055, 0.26, KM, axis="Y", verts=10, tags=tags)


def _chamber(name, ya, yb, z, A, K, hot, tip, fw, ports, extra=()):
    """Camara do freio de boca (como o freio do 76 mm): corpo claro facetado que aponta para a frente
    (chanfro frontal 'tip' ate a meia largura 'fw'), brilha de calor, com janelas transversais escuras
    recortadas no topo (o nucleo escuro b_brake_core aparece no fundo de cada janela)."""
    poly = [(-0.23, ya), (0.23, ya), (0.265, ya + 0.05), (0.265, yb - tip), (fw, yb), (-fw, yb), (-0.265, yb - tip),
            (-0.265, ya + 0.05)]
    ch = B.plate(name, poly, z - 0.145, z + 0.145, A, slope=0.035, tags=hot)
    cuts = [B.box(f"{name}_p{i}", 0, y, 0.60, 0.045, z + 0.03, z + 0.3, K, bevel=0.0) for i, y in enumerate(ports)]
    B.cut(ch, cuts + list(extra))
    return ch


def barrel(M, L=3.0, T="barrel", phase=0.0):
    """Cano pesado com raiz (y=0) e boca (y=L), centrado em x=0, altura z=0.6."""
    tags = (T,)
    hot = (T, "hot")  # partes que brilham de calor depois do tiro
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = 0.6
    # bolsa de culatra (lona) escura com pregas
    B.cyl("b_bag", 0, 0.26, z, 0.22, 0.52, KM, axis="Y", verts=8, bevel=0.012, tags=tags)
    for i in range(5):
        B.cyl(f"b_pleat{i}", 0, 0.06 + i * 0.10, z, 0.235, 0.035, K, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("b_bagcap", 0, 0.54, z, 0.21, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    # luva de recuo escura com aros de aco e nervuras laterais (sem fendas: nao repete o 76 mm)
    y0j, y1j = 0.57, 1.06
    B.cyl("b_jacket", 0, (y0j + y1j) / 2, z, 0.20, y1j - y0j, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
    for i, y in enumerate((0.70, 0.96)):
        B.cyl(f"b_hoop{i}", 0, y, z, 0.215, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    for sx in (-1, 1):
        B.box(f"b_rib{sx}", sx * 0.185, (y0j + y1j) / 2, 0.04, y1j - y0j - 0.04, z + 0.02, z + 0.10, S,
              bevel=0.006, tags=tags)
    # estagio 1: tubo A grosso, com canal escuro no topo
    y0, y1 = y0j, 1.50
    ta = B.cyl("b_atube", 0, (y0 + y1) / 2, z, 0.195, y1 - y0, A, axis="Y", verts=8, bevel=0.008, tags=tags,
               r2=0.19)
    B.cut(ta, [B.box("b_chca", 0, (1.06 + y1) / 2 + 0.02, 0.065, y1 - 1.06 - 0.04, z + 0.10, z + 0.3, K,
                     bevel=0.0)])
    B.box("b_chbeda", 0, (1.06 + y1) / 2 + 0.02, 0.065, y1 - 1.06 - 0.04, z + 0.08, z + 0.11, M["black"],
          bevel=0.0, tags=tags)
    B.cyl("b_collar0", 0, 1.09, z, 0.21, 0.05, AM, axis="Y", verts=8, bevel=0.008, tags=tags)
    # ombro de aco escalonado entre os dois estagios
    B.cyl("b_shoulder", 0, y1, z, 0.205, 0.06, S, axis="Y", verts=8, bevel=0.008, tags=tags)
    # estagio 2: cano fino afunilado ate o freio, com canal escuro
    yc0, yc1 = y1, L - 0.71
    # trecho final do cano fino separado e marcado 'hot': o calor do freio "escorre" um pouco para tras
    yh = 2.10
    rh = 0.168 - 0.018 * (yh - yc0) / (yc1 - yc0)
    ch = B.cyl("b_chase", 0, (yc0 + yh) / 2, z, 0.168, yh - yc0, A, axis="Y", verts=8, bevel=0.008, tags=tags,
               r2=rh)
    chh = B.cyl("b_chaseh", 0, (yh + yc1) / 2, z, rh, yc1 - yh, A, axis="Y", verts=8, bevel=0.008, tags=hot,
                r2=0.15)
    for t in (ch, chh):
        B.cut(t, [B.box("b_chcc", 0, (yc0 + yc1) / 2, 0.065, yc1 - yc0 - 0.10, z + 0.085, z + 0.3, K, bevel=0.0)])
    B.box("b_chbedc", 0, (yc0 + yc1) / 2, 0.065, yc1 - yc0 - 0.10, z + 0.065, z + 0.095, M["black"], bevel=0.0,
          tags=tags)
    # extrator de gases (bojo facetado) no meio do cano fino
    ye = 1.86
    fume = B.cyl("b_fume", 0, ye, z, 0.225, 0.30, A, axis="Y", verts=8, bevel=0.015, tags=tags)
    B.cut(fume, [B.box("b_fumec", 0, ye, 0.065, 0.38, z + 0.10, z + 0.3, K, bevel=0.0)])
    B.cyl("b_fumecone0", 0, ye - 0.19, z, 0.165, 0.08, A, axis="Y", verts=8, bevel=0.0, tags=tags, r2=0.225)
    B.cyl("b_fumecone1", 0, ye + 0.19, z, 0.225, 0.08, A, axis="Y", verts=8, bevel=0.0, tags=tags, r2=0.16)
    B.cyl("b_collar1", 0, L - 0.77, z, 0.178, 0.05, AM, axis="Y", verts=8, bevel=0.008, tags=hot)
    # freio de boca em dois estagios (linguagem do 76 mm): camaras claras apontando para a frente, com
    # janelas transversais escuras (ritmo 0.09, barras claras de 0.045)
    B.cyl("b_brakering", 0, L - 0.71, z, 0.20, 0.04, S, axis="Y", verts=8, bevel=0.006, tags=hot)
    ra, rb = L - 0.69, L - 0.41
    fa, fb = L - 0.345, L
    _chamber("b_brake1", ra, rb, z, A, K, hot, 0.07, 0.20, (ra + 0.09, ra + 0.18))
    B.cyl("b_neck", 0, (rb + fa) / 2, z, 0.17, fa - rb + 0.02, S, axis="Y", verts=8, bevel=0.006, tags=hot)
    # camara frontal em ponta de flecha (como (+-0.12, yb+0.21) do 76 mm), com a boca recortada na ponta
    _chamber("b_brake2", fa, fb, z, A, K, hot, 0.13, 0.12, (fa + 0.08, fa + 0.17),
             extra=[B.box("b_bore_c2", 0, fb, 0.12, 0.10, z - 0.07, z + 0.3, K, bevel=0.0)])
    # nucleo escuro: topo logo acima do fundo das janelas (aparece nelas); termina antes da ponta de flecha
    # para nao alargar a silhueta do nariz
    B.box("b_brake_core", 0, (ra + fb - 0.08) / 2, 0.40, fb - ra - 0.12, z - 0.12, z + 0.035, K, bevel=0.0,
          tags=tags)


def roof(M, T="roof"):
    """Teto: placas do conves (verde = pintura) + faixa de carregadores de 4 tiles com portas facetadas."""
    tags = (T,)
    W, H = PART["size"]
    pv = PART["pivot"]
    ring_r = PART["ring_r"]
    green = B.mat_roof_green()
    px, py = pv[0] - W / 2, H / 2 - pv[1]
    gap = 0.03
    B.box("deck_under", 0, 0, W, H, -0.05, 0.02, M["core"], bevel=0.0, tags=tags)
    for tx in range(W):
        for ty in range(H):
            cx, cy = tx + 0.5 - W / 2, H / 2 - ty - 0.5
            poly = B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
            _, pnl = B.shard(f"deck{tx}_{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02,
                             tags=tags)
            if (tx + ty) % 2 == 0 and pnl is not None:
                B.cut(pnl, [B.rbox(f"dl{tx}{ty}", cx + 0.18, cy - 0.18, 0.012, 0.5, 0.07, 0.2, M["core"], rot=45,
                                   bevel=0.0)])
    # anel da torre (sem pintura)
    B.torus("ringbear", px, py, 0.08, ring_r + 0.02, 0.055, M["core_mid"], tags=tags)
    B.cyl("ringhole", px, py, 0.05, ring_r - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    B.bolts("rb", B.ring_points(px, py, ring_r + 0.11, 36), 0.1, 0.022, M["steel"], tags=tags)
    # faixa de carregadores na fileira de tras: 4 portas em seta (folhas em chevron), respiros entre elas
    sy = -H / 2 + 0.5
    strip = B.plate("magstrip", B.rpoly(0, sy, W - 0.14, 0.84, 0, chamfer=0.12), 0.05, 0.11, M["core_mid"],
                    slope=0.025, tags=tags)
    rec = []
    for tx in range(W):
        cx = tx + 0.5 - W / 2
        rec.append(B.box(f"ledc{tx}", cx, sy - 0.31, 0.30, 0.06, 0.08, 0.3, M["core"], bevel=0.0))
    for k in range(W - 1):
        rec.append(B.box(f"ventc{k}", k + 1 - W / 2, sy + 0.06, 0.12, 0.40, 0.075, 0.3, M["core"], bevel=0.0))
    B.cut(strip, rec)
    for tx in range(W):
        cx = tx + 0.5 - W / 2
        y0, y1 = sy - 0.20, sy + 0.34
        door = [(cx - 0.25, y0), (cx + 0.25, y0), (cx + 0.33, y0 + 0.08), (cx + 0.33, y1 - 0.17), (cx + 0.14, y1),
                (cx - 0.14, y1), (cx - 0.33, y1 - 0.17), (cx - 0.33, y0 + 0.08)]
        da, dp = B.shard(f"door{tx}", door, 0.10, 0.15, M["armor_mid"], slope=0.02, groove=0.03, panel_h=0.015,
                         tags=tags)
        # escotilha emoldurada (como a do 76 mm): sulco escuro seguindo o contorno em ponta + tampa interna
        outer, inner = B.offset_poly(door, 0.10), B.offset_poly(door, 0.128)
        B.cut(dp, [B.loft(f"dring{tx}", outer, outer, 0.145, 0.3, M["core"], bevel=0.0)])
        B.loft(f"dringbed{tx}", outer, outer, 0.14, 0.153, M["black"], bevel=0.0, tags=tags)
        B.plate(f"dlid{tx}", inner, 0.13, 0.166, M["armor_mid"], slope=0.012, bevel=0.006, tags=tags)
        for k in (-1, 1):
            B.box(f"dhinge{tx}{k}", cx + k * 0.295, sy + 0.02, 0.035, 0.22, 0.15, 0.175, M["steel"], bevel=0.008,
                  tags=tags)
        B.box(f"dpad{tx}", cx, y0 + 0.19, 0.12, 0.032, 0.166, 0.186, M["steel"], bevel=0.006, tags=tags)
        # luz de estado num rebaixo da faixa
        B.box(f"dslot{tx}", cx, sy - 0.31, 0.30, 0.06, 0.075, 0.085, M["black"], bevel=0.0, tags=tags)
        B.box(f"dled{tx}", cx, sy - 0.31, 0.22, 0.022, 0.085, 0.092, M["glow_dim"], bevel=0.0, tags=tags)
    # respiros com persianas entre as portas (repete a baia de exaustao da cabeca)
    for k in range(W - 1):
        vx = k + 1 - W / 2
        B.box(f"vbed{k}", vx, sy + 0.06, 0.12, 0.40, 0.07, 0.08, M["black"], bevel=0.0, tags=tags)
        for i in range(4):
            B.box(f"vlouver{k}{i}", vx, sy - 0.08 + i * 0.093, 0.10, 0.024, 0.08, 0.105, M["core_mid"],
                  bevel=0.004, tags=tags)


def floor(M, T="floor"):
    """Piso: placas, anel com elevador de granadas, 5 postos da tripulacao e esteira de municao no fundo."""
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
    # anel giratorio com setas + tronco do elevador de granadas (anel escuro com 2 guinchos)
    B.torus("fl_ring", px, py, 0.05, ring_r * 0.85, 0.05, M["armor_mid"], tags=tags)
    B.plate("fl_trunk", B.rpoly(px, py, 1.62, 1.62, 0, chamfer=0.46), 0.02, 0.07, M["core_mid"], slope=0.03,
            tags=tags)
    # cubo octogonal (cinza medio) com centro escuro e eixo de aco
    w = ring_r * 0.62
    oct_ = lambda s: B.rpoly(px, py, s, s, 0, chamfer=s / (2 + math.sqrt(2)))  # noqa: E731
    B.plate("fl_hub", oct_(w), 0.05, 0.12, M["armor_mid"], slope=0.03, tags=tags)
    B.plate("fl_hubc", oct_(w * 0.52), 0.10, 0.125, M["core"], slope=0.015, tags=tags)
    B.plate("fl_hubs", oct_(w * 0.18), 0.12, 0.15, M["steel"], slope=0.01, bevel=0.006, tags=tags)
    B.bolts("fl_hubb", B.ring_points(px, py, w * 0.38, 8, math.pi / 8), 0.125, 0.018, M["steel"], tags=tags)
    # setas apontando para fora (sentido do giro do anel)
    for k in range(4):
        a = k * math.pi / 2
        cx, cy = px + math.cos(a) * ring_r * 0.6, py + math.sin(a) * ring_r * 0.6
        arrow = [(0.10, 0.0), (-0.06, 0.10), (-0.02, 0.0), (-0.06, -0.10)]
        ca, sa = math.cos(a), math.sin(a)
        arrow = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in arrow]
        B.plate(f"fl_chev{k}", arrow, 0.05, 0.08, M["armor"], slope=0.01, bevel=0.006, tags=tags)
    for k in (-1, 1):
        hx, hy = px + k * 0.74, py - 0.74
        B.cyl(f"fl_hoist{k}", hx, hy, 0.10, 0.14, 0.12, M["armor_mid"], axis="Z", verts=8, bevel=0.01, tags=tags)
        B.cyl(f"fl_hoistc{k}", hx, hy, 0.17, 0.08, 0.04, M["steel"], axis="Z", verts=8, bevel=0.005, tags=tags)
        B.box(f"fl_hoistl{k}", hx, hy + 0.17, 0.10, 0.025, 0.04, 0.07, M["glow_dim"], bevel=0.0, tags=tags)
    B.box("fl_led_t", px, py + ring_r * 0.95, 0.3, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    B.box("fl_led_b", px, py - ring_r * 0.95, 0.3, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # esteira continua de municao ao longo da parede de tras, com granadas sob as 4 portas do teto
    ey = -H / 2 + 0.19
    B.box("fl_conv", 0, ey, W - 0.30, 0.12, 0.0, 0.10, M["armor_mid"], bevel=0.01, tags=tags)
    for tx in range(W):
        cx = tx + 0.5 - W / 2
        for k in (-1, 1):
            x = cx + k * 0.17
            B.box(f"fl_shell{tx}{k}", x, ey, 0.16, 0.10, 0.10, 0.17, M["core_mid"], bevel=0.01, tags=tags)
            B.box(f"fl_shled{tx}{k}", x, ey, 0.09, 0.024, 0.17, 0.185, M["glow_dim"], bevel=0.0, tags=tags)
    # postos da tripulacao (mesmas posicoes que o gerador usa)
    for i, (cx, cy, _r) in enumerate(crew_positions(W, H, 5, pv)):
        x, y = cx - W / 2, H / 2 - cy
        B.box(f"seat{i}", x, y + 0.02, 0.32, 0.30, 0.0, 0.14, M["armor"], bevel=0.04, tags=tags)
        B.box(f"console{i}", x, y + 0.30, 0.42, 0.12, 0.0, 0.22, M["core_mid"], bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.30, 0.32, 0.06, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
