"""Metralhadora Pesada Quadrupla ("Saci") - reparo aberto de 4 canos, 2x2, familia do 76 mm.

Berco escuro com 4 calhas (frente em chevron) onde entram os canos lado a lado; sela clara em proa de flecha
atras do berco (a crista mais alta, como a espinha do 76 mm) com cupula de mira facetada alongada para a frente
e o "gorro" vermelho do Saci num recesso escuro no topo; redemoinho (3 bracos em espiral) gravado na sela em
volta da cupula; fenda de pips atras da cupula; ombreiras laterais compactas (caixas de cinta) com laminas em
garra que avancam ate as raizes dos canos externos; calhas de alimentacao e munhoes nos vaos; baia de exaustao.
Cano: receptor escuro, camisa escura com fendas e brasa fraca, luva clara longa com canal e 3 colares, freio
leve em ponta com fendas transversais. Pares 1+3 / 2+4 recuam juntos.
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_quad_hmg",
    "kind": "gun",
    "size": [2, 2],
    "pivot": [1.0, 0.95],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 1.96,            # lado do quadrado do sprite da torre (cabeca +-0.93)
    "ring_r": 0.80,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "collider": 0.86,
    "barrels": {
        "ys": [-0.27, -0.09, 0.09, 0.27],   # 4 canos lado a lado (sprites de 0.17 sem sobrepor)
        "root": 0.40,              # pivo -> raiz do cano (dentro do berco escuro)
        "length": 1.2,             # raiz -> boca
        "width": 0.17,             # largura do sprite de cada cano
        "pad": 0.09,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.06, 0.035, 0.015],
        "heat": [0.5, 0.3, 0.14, 0.05],     # calor leve so nas fendas do freio e no colar da boca
        "interval": 0.035,         # 4 quadros ~ 0.14 s = intervalo de cada par (14 tiros/s no total)
    },
    "lights": [                    # luzes dinamicas em coordenadas da cabeca
        {"at": [0.0, -0.70], "size": 0.9, "color": [255, 120, 30], "z": 0.8},
        {"at": [0.0, -0.10], "size": 0.45, "color": [255, 40, 30], "z": 0.9},
    ],
    "preview_pattern": "pairs",
}

RING_R = PART["ring_r"]
YS = PART["barrels"]["ys"]

# ============================================================================ geometria (planta)
# sela em proa de flecha com degrau lateral; ponta em y<=0.33 (nunca sob o receptor, que comeca em 0.40-0.06)
SADDLE = [(-0.22, -0.665), (0.22, -0.665), (0.38, -0.545), (0.38, -0.30), (0.35, -0.26), (0.35, 0.02),
          (0.13, 0.33), (-0.13, 0.33), (-0.35, 0.02), (-0.35, -0.26), (-0.38, -0.30), (-0.38, -0.545)]
SADDLE_Z = (0.30, 0.58)
SADDLE_SLOPE, SADDLE_GROOVE, SADDLE_PH = 0.08, 0.03, 0.03
DY = -0.14                         # centro da cupula (parte larga da flecha)
SWIRL = dict(r0=0.18, r1=0.27, sweep=-110, w0=0.046, w1=0.024, ex=0.80, ey=1.10)   # eliptico (sela alongada)
SWIRL_A0 = (75, 195, 315)          # angulo de saida de cada braco (graus)
WELL_R, DOME_R = 0.19, (0.160, 0.130, 0.095)
CRADLE = [(-0.33, 0.12), (0.33, 0.12), (0.385, 0.18), (0.385, 0.58), (0.345, 0.625), (0.0, 0.70),
          (-0.345, 0.625), (-0.385, 0.58), (-0.385, 0.18)]
SLOT_Y = -0.485                    # fenda de pips atras da cupula
SBOLTS = [(-0.15, -0.57), (0.15, -0.57), (-0.163, 0.125), (0.163, 0.125)]


def octo(cx, cy, r, rot=22.5):
    """Octogono regular (rot=22.5: lados retos para frente/tras/lados)."""
    return [(cx + math.cos(math.radians(rot + 45 * k)) * r, cy + math.sin(math.radians(rot + 45 * k)) * r)
            for k in range(8)]


def dome_poly(cx, cy, r):
    """Octogono alongado em proa (eco da sela): ponta truncada na frente, chanfros atras."""
    pts = [(0.30, 1.30), (0.90, 0.42), (0.90, -0.55), (0.45, -1.0)]
    half = [(cx + x * r, cy + y * r) for x, y in pts]
    return half + [(2 * cx - x, y) for x, y in reversed(half)]


def swirl_band(cx, cy, r0, r1, a0, sweep, w0, w1, ex=1.0, ey=1.0, n=20):
    """Faixa curva em espiral eliptica (raio r0->r1, angulo a0->a0+sweep, largura w0->w1) como poligono."""
    def c(t):
        r = r0 + (r1 - r0) * t
        a = math.radians(a0 + sweep * t)
        return cx + r * math.cos(a) * ex, cy + r * math.sin(a) * ey
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        (x0, y0), (x1, y1) = c(max(t - 0.01, 0)), c(min(t + 0.01, 1))
        ln = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = -(y1 - y0) / ln, (x1 - x0) / ln
        px, py = c(t)
        w = (w0 + (w1 - w0) * t) / 2
        left.append((px + nx * w, py + ny * w))
        right.append((px - nx * w, py - ny * w))
    return left + list(reversed(right))


def swirl_arms():
    return [swirl_band(0, DY, a0=a, **{k: v for k, v in SWIRL.items() if k not in ("ex", "ey")},
                       ex=SWIRL["ex"], ey=SWIRL["ey"]) for a in SWIRL_A0]


def slot_rot(name, cx, cy, length, w, ztop, n, M, tags, rot, targets, depth=0.07, mat=None):
    """Fenda escura girada (eixo longo = y local girado por rot) com n pips, recortada nos alvos."""
    for t in targets:
        if t is not None:
            B.cut(t, [B.rbox(name + "_cut", cx, cy, w, length, ztop - depth, ztop + 0.2, M["black"], rot=rot,
                             bevel=0.0)])
    B.rbox(name + "_bed", cx, cy, w, length, ztop - depth - 0.01, ztop - depth + 0.004, M["black"], rot=rot,
           bevel=0.0, tags=tags)
    a = math.radians(rot)
    ux, uy = -math.sin(a), math.cos(a)
    for i in range(n):
        t = ((i + 0.5) / n - 0.5) * length
        B.rbox(f"{name}_pip{i}", cx + ux * t, cy + uy * t, w * 0.55, length / n * 0.55, ztop - depth,
               ztop - depth + 0.012, mat or M["glow"], rot=rot, bevel=0.0, tags=tags)


# ============================================================================ cabeca
def head(M, T="head", phase=0.0):
    """Cabeca: berco de 4 canos, sela em proa com cupula do Saci, ombreiras com garras, vaos com calhas."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]

    # anel giratorio (arco da frente recortado na boca do berco: nao cobre os canos) e nucleo escuro
    ring = B.cyl("ring", 0, 0, 0.04, RING_R + 0.02, 0.08, KM, axis="Z", verts=64, bevel=0.01, tags=tags)
    B.cut(ring, [B.box("ring_cut", 0, 0.82, 0.80, 0.34, -0.1, 0.3, K, bevel=0.0)])
    pts = [(x, y) for x, y in B.ring_points(0, 0, RING_R - 0.05, 20, 0.16) if not (abs(x) < 0.44 and y > 0.5)]
    B.bolts("ringbolt", pts, 0.09, 0.02, S, tags=tags)
    core = [(-0.36, -0.82), (0.36, -0.82), (0.64, -0.68), (0.80, -0.42), (0.80, 0.30), (0.58, 0.58),
            (-0.58, 0.58), (-0.80, 0.30), (-0.80, -0.42), (-0.64, -0.68)]
    B.plate("core", core, 0.06, 0.28, K, slope=0.04, tags=tags)

    # berco escuro: frente em chevron, 4 calhas abertas (raizes dos canos), cinta de aco e munhoes laterais
    cr = B.plate("cradle", CRADLE, 0.22, 0.44, KM, slope=0.025, tags=tags)
    B.cut(cr, [B.box(f"cr_ch{i}", y, 0.525, 0.125, 0.47, 0.35, 0.9, K, bevel=0.0) for i, y in enumerate(YS)])
    for i, y in enumerate(YS):
        yf = 0.70 - abs(y) * (0.075 / 0.345) - 0.03     # frente do chevron nesta calha
        B.box(f"cr_bed{i}", y, (0.30 + yf) / 2, 0.125, yf - 0.30, 0.34, 0.355, M["black"], bevel=0.0, tags=tags)
        # bandeja de alimentacao (aco) no fundo da calha, logo atras da raiz do cano
        B.box(f"cr_tray{i}", y, 0.355, 0.07, 0.05, 0.35, 0.39, S, bevel=0.006, tags=tags)
    B.box("cr_band", 0, 0.255, 0.70, 0.05, 0.42, 0.47, S, bevel=0.008, tags=tags)
    for sx in (-1, 1):
        B.cyl(f"trun{sx}", sx * 0.43, 0.40, 0.34, 0.075, 0.09, KM, axis="X", verts=8, bevel=0.008, tags=tags)
        B.cyl(f"trunc{sx}", sx * 0.475, 0.40, 0.34, 0.045, 0.03, S, axis="X", verts=8, bevel=0.004, tags=tags)
        # dentes escuros nas bochechas do berco: prendem os canos externos por fora
        tooth = [(0.352, 0.57), (0.395, 0.60), (0.402, 0.73), (0.378, 0.79), (0.352, 0.70)]
        B.plate(f"cr_tooth{sx}", tooth if sx > 0 else Mo.mirror(tooth), 0.26, 0.47, KM, slope=0.012,
                bevel=0.006, tags=tags)

    # ombreiras (caixas de cinta blindadas) + laminas em garra que avancam ate os canos externos
    paul = [(-0.53, -0.44), (-0.64, -0.70), (-0.76, -0.70), (-0.89, -0.42), (-0.89, -0.22), (-0.94, -0.14),
            (-0.94, 0.12), (-0.86, 0.24), (-0.55, 0.38), (-0.53, 0.30)]
    # aleta elevada (segundo andar) na borda de fora da ombreira, com a fenda de pips
    fin = [(-0.70, -0.58), (-0.78, -0.58), (-0.855, -0.41), (-0.855, -0.12), (-0.80, -0.04), (-0.70, -0.10)]
    # lamina em presa: borda de tras paralela a frente da ombreira (vao de 0.055), ponta fina perto do cano
    blade = [(-0.864, 0.29), (-0.574, 0.43), (-0.48, 0.54), (-0.43, 0.70), (-0.415, 0.93), (-0.47, 0.90),
             (-0.62, 0.70), (-0.80, 0.52), (-0.90, 0.40)]
    # painel interno da lamina desenhado a mao (a ponta fina nao comporta o deslocamento automatico)
    blade_pnl = [(-0.80, 0.385), (-0.60, 0.485), (-0.535, 0.565), (-0.505, 0.69), (-0.575, 0.665),
                 (-0.70, 0.555), (-0.83, 0.455)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        pa, ppn = B.shard(f"paul_{side}", f(paul), 0.26, 0.56, A, slope=0.07, groove=0.035, panel_h=0.03,
                          tags=tags)
        # linhas de painel: diagonal na frente e corte transversal na frente da aleta
        if ppn is not None:
            B.cut(ppn, [B.rbox(f"ppl{side}0", sx * 0.70, 0.13, 0.016, 0.30, 0.575, 0.8, K, rot=sx * 70, bevel=0.0),
                        B.rbox(f"ppl{side}1", sx * 0.71, 0.0, 0.016, 0.18, 0.575, 0.8, K, rot=90, bevel=0.0)])
        fa = B.plate(f"fin_{side}", f(fin), 0.585, 0.655, A, slope=0.03, tags=tags)
        Mo.slot_with_pips(f"pslot{side}", sx * 0.777, -0.40, -0.16, 0.055, 0.655, 3, M, tags,
                          target=[fa, ppn, pa], depth=0.13)
        # trava de aco da tampa da caixa de cinta
        B.box(f"plat{side}", sx * 0.672, -0.30, 0.04, 0.14, 0.58, 0.61, S, bevel=0.008, tags=tags)
        ba = B.plate(f"blade_{side}", f(blade), 0.26, 0.52, A, slope=0.05, tags=tags)
        bpn = B.plate(f"blade_{side}_pnl", f(blade_pnl), 0.516, 0.545, A, slope=0.012, bevel=0.008, tags=tags)
        # fenda com luz fraca ao longo da lamina
        slot_rot(f"bsl{side}", sx * 0.63, 0.55, 0.18, 0.04, 0.545, 1, M, tags, sx * 52, [ba, bpn], depth=0.07,
                 mat=M["glow_dim"])
        # pistao hidraulico entre ombreira e lamina
        B.cyl(f"piston{side}", sx * 0.53, 0.47, 0.36, 0.026, 0.20, S, axis="Y", verts=10, yaw=sx * 42, tags=tags)
        B.cyl(f"pistonb{side}", sx * 0.58, 0.41, 0.36, 0.038, 0.09, KM, axis="Y", verts=10, yaw=sx * 42,
              tags=tags)

    # vaos: calhas de alimentacao (das caixas de cinta ate o berco) e contadores ambar
    for sx in (-1, 1):
        x = sx * 0.455
        B.cyl(f"chute{sx}", x, -0.20, 0.36, 0.048, 0.62, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
        for i, y in enumerate((-0.42, -0.24, -0.06)):
            B.cyl(f"chuter{sx}{i}", x, y, 0.36, 0.056, 0.03, S, axis="Y", verts=8, bevel=0.004, tags=tags)
        B.box(f"feedport{sx}", sx * 0.43, 0.15, 0.10, 0.10, 0.28, 0.43, KM, bevel=0.012, tags=tags)
        B.box(f"feedlid{sx}", sx * 0.43, 0.15, 0.06, 0.06, 0.43, 0.45, S, bevel=0.006, tags=tags)
        m = B.box(f"cnt{sx}", x, -0.60, 0.10, 0.14, 0.26, 0.40, KM, bevel=0.01, tags=tags)
        Mo.slot_with_pips(f"cnts{sx}", x, -0.66, -0.54, 0.04, 0.40, 2, M, tags, target=m, depth=0.04)
        for o in [o for o in B.objects_with(T) if o.name.startswith(f"cnts{sx}_pip")]:
            o.data.materials[0] = M["glow_dim"]   # contador fraco (orcamento de brilho)

    # sela clara em proa (a crista mais alta da cabeca) com o redemoinho gravado em volta da cupula
    z0, z1 = SADDLE_Z
    sa, spn = B.shard("saddle", SADDLE, z0, z1, A, slope=SADDLE_SLOPE, groove=SADDLE_GROOVE, panel_h=SADDLE_PH,
                      tags=tags)
    zt = z1 + SADDLE_PH                          # topo do painel interno
    zg = z1 - 0.07                               # fundo dos sulcos (passa do painel: sem triangulos pretos)
    for k, band in enumerate(swirl_arms()):
        B.cut(spn, [B.loft(f"sw_c{k}", band, band, zg, 0.95, K, bevel=0.0)])
        B.cut(sa, [B.loft(f"sw_cb{k}", band, band, zg, 0.95, K, bevel=0.0)])
        # fundo do sulco em nucleo medio: le como gravacao, nao como rachadura
        B.loft(f"sw_bed{k}", band, band, zg - 0.01, zg + 0.004, KM, bevel=0.0, tags=tags)
    # poco escuro em volta da cupula (os bracos do redemoinho saem dele)
    well = dome_poly(0, DY, WELL_R)
    B.cut(spn, [B.loft("well_c", well, well, zg, 0.95, K, bevel=0.0)])
    B.cut(sa, [B.loft("well_cb", well, well, zg, 0.95, K, bevel=0.0)])
    B.loft("well_bed", well, well, zg - 0.01, zg + 0.004, M["black"], bevel=0.0, tags=tags)
    # cupula de mira facetada em proa (dois andares de facetas)
    zd0, zd1, zd2 = zg, z1 + 0.16, z1 + 0.225
    sk = B.loft("dome_sk", dome_poly(0, DY, DOME_R[0]), dome_poly(0, DY, DOME_R[1]), zd0, zd1, A, bevel=0.008, tags=tags)
    top = B.loft("dome_top", dome_poly(0, DY, DOME_R[1]), dome_poly(0, DY, DOME_R[2]), zd1, zd2, A, bevel=0.006,
                 tags=tags)
    # recesso escuro no topo com o gorro vermelho (gota apontando para a frente, como a proa)
    rec = dome_poly(0, DY, 0.072)
    B.cut(top, [B.loft("cap_cut", rec, rec, zd2 - 0.03, 1.2, K, bevel=0.0)])
    B.loft("cap_bed", rec, rec, zd2 - 0.04, zd2 - 0.028, M["black"], bevel=0.0, tags=tags)
    cap = [(0.0, DY + 0.072), (0.040, DY + 0.012), (0.032, DY - 0.030), (0.0, DY - 0.048), (-0.032, DY - 0.030),
           (-0.040, DY + 0.012)]
    # vermelho proprio do gorro: M["red"] (forca 6) estoura para branco neste tamanho; este fica saturado,
    # apaga no turret_off (mat_glow) e deve ser reaproveitado por outras pecas que precisem de vermelho pequeno
    red = B.mat_glow("saci_red", (1.0, 0.05, 0.03), 1.8)
    B.loft("cap", cap, B.offset_poly(cap, 0.007), zd2 - 0.03, zd2 - 0.004, red, bevel=0.0, tags=tags)
    # visor da mira na faceta da frente (janela escura com lente ambar)
    zv = zd0 + 0.11
    for t in (sk, top):
        B.cut(t, [B.box(f"vis_cut{t.name}", 0, DY + 0.168, 0.11, 0.05, zv, 1.2, K, bevel=0.0)])
    B.box("vis_bed", 0, DY + 0.168, 0.11, 0.05, zv - 0.006, zv + 0.004, M["black"], bevel=0.0, tags=tags)
    B.box("vis_lens", 0, DY + 0.166, 0.075, 0.016, zv, zv + 0.01, M["glow_dim"], bevel=0.0, tags=tags)
    # fenda com 3 pips atras da cupula (como a fenda da espinha do 76 mm)
    Mo.slot_with_pips("sp", SLOT_Y, -0.10, 0.10, 0.045, zt, 3, M, tags, target=[spn, sa], depth=0.08,
                      vertical=False)
    # linhas de painel no degrau lateral da sela
    if spn is not None:
        B.cut(spn, [B.rbox(f"sapl{sx}", sx * 0.255, -0.28, 0.016, 0.07, z1 - 0.02, 0.95, K, rot=90, bevel=0.0)
                    for sx in (-1, 1)])
    # parafusos da sela (no sulco entre chanfro e painel; os da frente nos chanfros da proa)
    B.bolts("sbolt", SBOLTS, z1 + 0.005, 0.014, S, tags=tags)

    # baia de exaustao traseira (persianas + pips)
    B.box("vent_bay", 0, -0.735, 0.46, 0.13, 0.20, 0.30, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"louver{i}", 0, -0.78 + i * 0.04, 0.44, 0.016, 0.20, 0.31, KM, bevel=0.003, tags=tags)
    for i, x in enumerate((-0.15, -0.05, 0.05, 0.15)):
        B.box(f"vent_pip{i}", x, -0.69, 0.045, 0.02, 0.30, 0.32, M["glow"], bevel=0.0, tags=tags)
    B.bolts("bolt", [(-0.66, -0.62), (0.66, -0.62)], 0.29, 0.02, S, tags=tags)


# ============================================================================ cano
def barrel(M, L=1.2, T="barrel", phase=0.0):
    """Um cano de metralhadora pesada: raiz em y=0, boca em y=L, centrado em x=0."""
    tags = (T,)
    hot = (T, "hot")
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = 0.50
    # receptor escuro (fica sobre o berco) com tampa de alimentacao escura e trava de aco
    rec = [(-0.056, 0.0), (0.056, 0.0), (0.064, 0.03), (0.064, 0.25), (0.05, 0.29), (-0.05, 0.29),
           (-0.064, 0.25), (-0.064, 0.03)]
    B.plate("b_recv", rec, z - 0.08, z + 0.05, KM, slope=0.012, tags=tags)
    B.box("b_cover", 0, 0.14, 0.074, 0.15, z + 0.045, z + 0.065, KM, bevel=0.006, tags=tags)
    B.box("b_hinge", 0, 0.222, 0.06, 0.014, z + 0.05, z + 0.07, S, bevel=0.004, tags=tags)
    B.box("b_latch", 0, 0.04, 0.05, 0.03, z + 0.05, z + 0.075, S, bevel=0.005, tags=tags)
    # camisa de resfriamento escura com fendas transversais (brasa fraca no fundo), como a do 76 mm
    y0j, y1j = 0.29, 0.60
    jk = B.cyl("b_jacket", 0, (y0j + y1j) / 2, z, 0.058, y1j - y0j, KM, axis="Y", verts=8, bevel=0.006,
               tags=tags)
    B.cut(jk, [B.box(f"b_jc{i}", 0, 0.37 + i * 0.065, 0.14, 0.03, z + 0.025, z + 0.2, K, bevel=0.0)
               for i in range(4)])
    B.box("b_heat", 0, (y0j + y1j) / 2, 0.075, y1j - y0j - 0.08, z + 0.018, z + 0.029, M["ember"], bevel=0.0,
          tags=tags)
    # aletas finas nas pontas da camisa
    for i, y in enumerate((y0j + 0.02, y1j - 0.02)):
        fn = B.cyl(f"b_fin{i}", 0, y, z, 0.063, 0.025, AM, axis="Y", verts=8, bevel=0.004, tags=tags)
        B.cut(fn, [B.box(f"b_finc{i}", 0, y, 0.016, 0.06, z + 0.036, z + 0.2, K, bevel=0.0)])
    # luva clara facetada longa com canal escuro no topo e 3 colares
    y0, y1 = y1j, L - 0.20
    sl = B.cyl("b_sleeve", 0, (y0 + y1) / 2, z, 0.049, y1 - y0, A, axis="Y", verts=8, bevel=0.006, tags=tags,
               r2=0.043)
    B.cut(sl, [B.box("b_chc", 0, (y0 + y1) / 2, 0.016, y1 - y0 - 0.06, z + 0.02, z + 0.2, K, bevel=0.0)])
    B.box("b_chbed", 0, (y0 + y1) / 2, 0.016, y1 - y0 - 0.06, z + 0.015, z + 0.025, M["black"], bevel=0.0,
          tags=tags)
    B.cyl("b_collar0", 0, y0 + 0.035, z, 0.057, 0.03, AM, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("b_collarm", 0, (y0 + y1) / 2, z, 0.054, 0.028, AM, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("b_collar1", 0, y1 - 0.01, z, 0.052, 0.03, AM, axis="Y", verts=8, bevel=0.006, tags=hot)
    # freio leve em ponta de flecha com fendas transversais escuras
    yb = L - 0.10
    brake = [(-0.056, yb - 0.10), (0.056, yb - 0.10), (0.066, yb - 0.07), (0.066, yb + 0.045),
             (0.036, yb + 0.10), (-0.036, yb + 0.10), (-0.066, yb + 0.045), (-0.066, yb - 0.07)]
    br = B.plate("b_brake", brake, z - 0.055, z + 0.055, A, slope=0.014, tags=tags)
    bc = [B.box(f"b_bc{i}", 0, yb - 0.055 + i * 0.048, 0.16, 0.02, z + 0.012, z + 0.2, K, bevel=0.0)
          for i in range(3)]
    bc.append(B.box("b_bore_c", 0, L, 0.032, 0.06, z - 0.03, z + 0.2, K, bevel=0.0))
    B.cut(br, bc)
    # fundo escuro das fendas: e ele que esquenta (laranja so dentro das fendas, a casca clara nao fica rosada)
    B.box("b_brake_core", 0, yb - 0.008, 0.11, 0.125, z - 0.04, z + 0.016, K, bevel=0.0, tags=hot)


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto 2x2: placas verdes, anel da torre, respiros em diagonal atras e tampas de cinta na frente."""
    tags = (T,)
    w, h = PART["size"]
    green = B.mat_roof_green()
    K, KM, S = M["core"], M["core_mid"], M["steel"]
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
    B.bolts("rb", pts, 0.1, 0.022, S, tags=tags)
    for sx in (-1, 1):
        # canto de tras: respiro em diagonal; a luz fica no fundo da persiana de fora (recesso escuro)
        cx, cy = sx * 0.79, -0.79
        v = B.rbox(f"cvent{sx}", cx, cy, 0.32, 0.18, 0.05, 0.11, KM, rot=sx * 45, chamfer=0.03, bevel=0.01,
                   tags=tags)
        a = math.radians(sx * 45)
        B.cut(v, [B.rbox(f"cvc{sx}{i}", cx - math.sin(a) * (i - 1) * 0.05, cy + math.cos(a) * (i - 1) * 0.05,
                         0.26, 0.022, 0.09, 0.2, K, rot=sx * 45, bevel=0.0) for i in range(3)])
        B.rbox(f"cled{sx}", sx * 0.825, -0.825, 0.20, 0.014, 0.090, 0.096, M["glow_dim"], rot=sx * 45, bevel=0.0,
               tags=tags)
        # canto da frente: tampa triangular chanfrada (acesso a cinta) com parafuso
        tri = [(sx * 0.92, 0.92), (sx * 0.62, 0.92), (sx * 0.92, 0.62)]
        B.plate(f"chatch{sx}", tri if sx < 0 else list(reversed(tri)), 0.06, 0.10, M["armor_mid"], slope=0.02,
                tags=tags)
        B.bolts(f"chb{sx}", [(sx * 0.83, 0.83)], 0.115, 0.018, S, tags=tags)


def floor(M, T="floor"):
    """Piso: anel, dois postos de atirador atras com console ao lado e caixas de cinta nos cantos."""
    from bsgen.common import crew_positions
    tags = (T,)
    w, h = PART["size"]
    pv = PART["pivot"]
    rr = RING_R
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    px, py = pv[0] - w / 2, h / 2 - pv[1]
    B.box("fl_base", 0, 0, w, h, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for tx in range(w):
        for ty in range(h):
            x0, y1 = tx - w / 2 + 0.04, h / 2 - ty - 0.04
            B.box(f"fl{tx}{ty}", x0 + 0.46, y1 - 0.46, 0.92, 0.92, 0.0, 0.03, KM, bevel=0.01, tags=tags)
    B.torus("fl_ring", px, py, 0.05, rr * 0.66, 0.045, AM, tags=tags)
    hub = B.cyl("fl_hub", px, py, 0.05, rr * 0.26, 0.08, A, axis="Z", verts=48, tags=tags)
    # sulcos radiais no cubo (6 raios) e furo central escuro
    B.cut(hub, [B.rbox(f"fl_hubg{k}", px + math.cos(math.radians(30 + 60 * k)) * rr * 0.16,
                       py + math.sin(math.radians(30 + 60 * k)) * rr * 0.16, 0.018, rr * 0.18, 0.07, 0.2, K,
                       rot=60 * k - 60, bevel=0.0) for k in range(6)])
    B.cyl("fl_hubc", px, py, 0.085, rr * 0.07, 0.012, KM, axis="Z", verts=16, bevel=0.0, tags=tags)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        B.rbox(f"fl_chev{k}", px + math.cos(a) * rr * 0.46, py + math.sin(a) * rr * 0.46, 0.12, 0.12, 0.05, 0.08,
               A, rot=45, bevel=0.01, tags=tags)
    B.box("fl_led_t", px, py + rr * 0.80, 0.24, 0.04, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # caixas de cinta nos cantos da frente (tampa clara e contador ambar)
    for sx in (-1, 1):
        cx, cy = sx * 0.76, 0.74
        B.rbox(f"fl_box{sx}", cx, cy, 0.34, 0.22, 0.0, 0.16, KM, rot=-sx * 45, chamfer=0.03, bevel=0.01, tags=tags)
        B.rbox(f"fl_lid{sx}", cx, cy, 0.26, 0.14, 0.16, 0.19, AM, rot=-sx * 45, chamfer=0.02, bevel=0.008,
               tags=tags)
        B.rbox(f"fl_cnt{sx}", cx, cy, 0.10, 0.03, 0.19, 0.205, M["glow_dim"], rot=-sx * 45, bevel=0.0, tags=tags)
    # estante de cintas ao longo da borda de tras
    for tx in range(w):
        x = tx - w / 2 + 0.5
        B.box(f"rack{tx}", x, -h / 2 + 0.13, 0.78, 0.18, 0.0, 0.16, AM, bevel=0.01, tags=tags)
        for i in range(3):
            B.box(f"mag{tx}{i}", x - 0.24 + i * 0.24, -h / 2 + 0.13, 0.16, 0.12, 0.16, 0.24, KM, bevel=0.01, tags=tags)
            B.box(f"magled{tx}{i}", x - 0.24 + i * 0.24, -h / 2 + 0.13, 0.10, 0.03, 0.24, 0.26, M["glow_dim"],
                  bevel=0.0, tags=tags)
    # postos dos atiradores: base de aco, assento claro, encosto escuro e console do lado de fora
    for i, (cx, cy, _r) in enumerate(crew_positions(w, h, 2, pv)):
        x, y = cx - w / 2, h / 2 - cy
        sx = -1 if x < 0 else 1
        B.box(f"seatb{i}", x, y + 0.04, 0.34, 0.32, 0.0, 0.05, S, bevel=0.012, tags=tags)
        B.box(f"seat{i}", x, y + 0.06, 0.28, 0.22, 0.05, 0.14, A, bevel=0.035, tags=tags)
        B.box(f"seatbk{i}", x, y - 0.09, 0.30, 0.07, 0.05, 0.24, KM, bevel=0.02, tags=tags)
        B.box(f"seatbs{i}", x, y - 0.09, 0.20, 0.025, 0.24, 0.255, S, bevel=0.006, tags=tags)
        B.box(f"console{i}", x + sx * 0.33, y + 0.06, 0.12, 0.36, 0.0, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x + sx * 0.33, y + 0.06, 0.06, 0.26, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
