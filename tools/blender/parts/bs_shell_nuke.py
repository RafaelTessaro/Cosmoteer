"""Projetil Nuclear (Nuclear Shell) - municao do Obuseiro Nuclear Boiuna; pilha de 2; explode se a pilha cair.

Mesma familia dos carregadores (nucleo escuro + cascas claras chanfradas com bisel duplo, contador de LEDs numa
fenda escura), mas com outra silhueta e outra cor: uma granada de artilharia enorme deitada ao longo do tile
(frente = +Y, ogiva para cima), igual as granadas do rack da torre do Boiuna (corpo escuro, faixas verdes, nariz
cinza claro):
  * anel de base pesado de aco claro (octogonal, com sulco escuro) e colar de blindagem clara chanfrada na
    base, com o contador de 2 LEDs verdes numa fenda escura;
  * corpo de aco canhoneado quase preto, octogonal de topo plano (facetas chanfradas como os canos da
    familia), com 2 faixas verdes em sulcos escuros (larga embaixo, fina em cima) e janela longitudinal
    escura mostrando o nucleo verde (barra de luz com grade de aco atravessada);
  * colar claro chanfrado no pescoco e ogiva pontuda cinza clara em 3 troncos facetados, com o trevo de 3
    cunhas escuras (simbolo nuclear, mesmo motivo do teto da fundicao e do emblema do Boiuna) e cubo verde,
    anel escuro de painel perto da ponta e espoleta de aco.
Unidade modelada centrada na origem (eixo longo em Y, ~0.40 x 1.0); o renderizador escala para a pilha
(1 no centro, 2 lado a lado). O icone fica em pe (ogiva para cima), como os outros icones de municao.
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_shell_nuke",
    "kind": "resource",
    "accent": "green",
    "unit_scale": 0.90,
    "icon_scale": 0.84,
    "icon_rot": 0,
    "stack_layout": {
        1: [(0, 0, 0)],
        2: [(-0.20, 0, 0), (0.20, 0, 0)],
    },
    "stack_rot": [0, 0, 0, 0, 0, 0],
}

# geometria compartilhada (a fundicao reaproveita as medidas na casca do berco)
R = 0.18                     # raio do corpo (octogono de topo plano: meia largura R*cos(22.5))
ZC = 0.18                    # altura do eixo (granada deitada no chao)
Y_BASE0, Y_BASE1 = -0.50, -0.43   # anel de base
Y_COL0, Y_COL1 = -0.42, -0.27     # colar claro da base
Y_NECK0, Y_NECK1 = 0.07, 0.15     # colar claro do pescoco (o corpo escuro fica entre os colares)
Y_TIP = 0.50                      # ponta da espoleta
WIN_Y = (-0.175, 0.015)           # janela do nucleo no topo do corpo
BANDS = ((-0.225, 0.011), (0.045, 0.007))   # faixas verdes (centro, meia largura)
BODY = (0.040, 0.043, 0.048)      # aco canhoneado quase preto
OGIVE = (0.30, 0.31, 0.325)       # ogiva cinza clara (como os narizes das granadas do rack do Boiuna)
# perfil da ogiva (y, raio) e trevo (centro y, raio de fora, raio do cubo)
OG_PROF = [(Y_NECK1 - 0.01, R - 0.012), (0.25, R * 0.84), (0.35, R * 0.62), (0.44, R * 0.30)]
TREF = (0.245, 0.092, 0.030)


def mats():
    """Materiais proprios (sem desgaste nas pecas pequenas: o desgaste das quinas clareia a malha inteira)."""
    return {
        "body": B.mat_metal("nk_body", BODY, rough=0.48, metal=0.55),
        "ogive": B.mat_paint("nk_ogive", OGIVE, rough=0.36, metal=0.3, wear=0.0, grime=0.04, scale=5),
        # aco claro do anel de base e da espoleta (o aco padrao fica apagado nessa escala)
        "ring": B.mat_metal("nk_ring", (0.50, 0.52, 0.55), rough=0.3, metal=0.9),
        "core_glow": B.mat_glow("nk_core", Mo.GREEN, 1.6),
        "band": B.mat_glow("nk_band", Mo.GREEN, 1.3),
        # faixa apagada (estojo aberto no berco, ainda sem nucleo)
        "band_off": B.mat_metal("nk_band_off", (0.025, 0.075, 0.035), rough=0.4, metal=0.3),
    }


def octo_cyl(name, x, y0, y1, r, mat, tags, r2=None, z=ZC, bevel=0.006):
    """Cilindro octogonal deitado em Y, de y0 a y1, com uma face plana em cima (girado 22.5 graus no eixo)."""
    ob = B.cyl(name, x, (y0 + y1) / 2, z, r, y1 - y0, mat, axis="Y", verts=8, bevel=bevel, r2=r2, tags=tags)
    ob.rotation_euler = (math.radians(-90), math.radians(22.5), 0)
    return ob


def _trefoil(cx, cy, ro, ri):
    """3 cunhas do trevo (uma para cima, duas embaixo), cada uma com 60 graus, entre os raios ri e ro."""
    out = []
    for k in range(3):
        a = 90 + 120 * k
        inner = [(cx + ri * math.cos(math.radians(a + s)), cy + ri * math.sin(math.radians(a + s))) for s in (-24, 24)]
        arc = [(cx + ro * math.cos(math.radians(a + s)), cy + ro * math.sin(math.radians(a + s)))
               for s in (-30, -10, 10, 30)]
        out.append([inner[0]] + arc + [inner[1]])
    return out


def _og_r(y):
    """Raio da ogiva (perfil OG_PROF) na altura y."""
    for (ya, ra), (yb, rb) in zip(OG_PROF, OG_PROF[1:]):
        if ya <= y <= yb:
            return ra + (rb - ra) * (y - ya) / (yb - ya)
    return OG_PROF[-1][1]


def ogive(name, x, y0, zc, sc, X, M, tags, trefoil=True):
    """Ogiva na escala sc com a base em y0 e o eixo na altura zc: 3 troncos facetados cinza claros, anel escuro
    de painel perto da ponta, espoleta de aco claro com anel escuro e (opcional) o trevo de 3 cunhas escuras
    recortadas no nariz com o cubo verde."""
    base = OG_PROF[0][0]

    def Y(y):
        return y0 + (y - base) * sc
    segs = []
    for k in range(len(OG_PROF) - 1):
        (ya, ra), (yb, rb) = OG_PROF[k], OG_PROF[k + 1]
        segs.append(octo_cyl(f"{name}{k}", x, Y(ya), Y(yb), ra * sc, X["ogive"], tags, r2=rb * sc, z=zc,
                             bevel=0.004 * sc))
    octo_cyl(f"{name}_pl", x, Y(0.342), Y(0.360), R * 0.645 * sc, M["black"], tags, z=zc, bevel=0.0)
    octo_cyl(f"{name}_fz", x, Y(0.44), Y(Y_TIP), R * 0.30 * sc, X["ring"], tags, r2=0.01 * sc, z=zc, bevel=0.0)
    octo_cyl(f"{name}_fzr", x, Y(0.432), Y(0.452), R * 0.33 * sc, M["core_mid"], tags, z=zc, bevel=0.0)
    if not trefoil:
        return segs
    # trevo: cunhas recortadas (paredes verticais) ate um leito preto; cubo verde no meio
    ty, ro, ri = TREF
    cx, cy = x, Y(ty)
    zf = zc + 0.07 * sc                 # fundo do recorte (abaixo da face de cima do nariz)
    wedges = _trefoil(cx, cy, ro * sc, ri * sc)
    for j, seg in enumerate(segs[:2]):
        B.cut(seg, [B.loft(f"{name}_tc{j}{k}", w, w, zf, zc + 0.5 * sc, M["black"], bevel=0.0)
                    for k, w in enumerate(wedges)])
    for k, w in enumerate(wedges):
        B.loft(f"{name}_tb{k}", w, w, zf - 0.01 * sc, zf + 0.004 * sc, M["black"], bevel=0.0, tags=tags)
    zt = zc + _og_r(ty) * math.cos(math.radians(22.5)) * sc       # face de cima do nariz no centro do trevo
    B.cyl(f"{name}_thub", cx, cy, zt - 0.004 * sc, ri * 0.95 * sc, 0.012 * sc, M["black"], axis="Z", verts=8,
          bevel=0.0, tags=tags)
    B.cyl(f"{name}_tled", cx, cy, zt + 0.004 * sc, ri * 0.62 * sc, 0.006 * sc, X["core_glow"], axis="Z", verts=8,
          bevel=0.0, tags=tags)
    return segs


def item(M, T="item"):
    tags = (T,)
    X = mats()
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    top = ZC + R * math.cos(math.radians(22.5))      # face de cima do corpo

    # ---- anel de base pesado (aco claro) com sulco escuro e o fundo escuro do estojo
    octo_cyl("nk_base", 0, Y_BASE0, Y_BASE1, R + 0.018, X["ring"], tags, bevel=0.008)
    octo_cyl("nk_baseg", 0, Y_BASE1 - 0.002, Y_COL0 + 0.004, R - 0.01, K, tags, bevel=0.0)
    B.box("nk_basel", 0, (Y_BASE0 + Y_BASE1) / 2, 0.20, 0.018, top + 0.005, top + 0.03, K, bevel=0.0, tags=tags)

    # ---- corpo escuro (entre os colares; os colares claros cobrem as pontas)
    body = octo_cyl("nk_body", 0, Y_COL1 - 0.02, Y_NECK0 + 0.02, R, X["body"], tags)
    # janela longitudinal no topo do corpo: recesso escuro com o nucleo verde e grade de aco
    wy0, wy1 = WIN_Y
    B.cut(body, [B.box("nk_winc", 0, (wy0 + wy1) / 2, 0.09, wy1 - wy0, top - 0.05, top + 0.3, K, bevel=0.0)])
    B.box("nk_winbed", 0, (wy0 + wy1) / 2, 0.09, wy1 - wy0, top - 0.06, top - 0.045, M["black"], bevel=0.0,
          tags=tags)
    B.box("nk_core", 0, (wy0 + wy1) / 2, 0.034, wy1 - wy0 - 0.04, top - 0.045, top - 0.035, X["core_glow"],
          bevel=0.0, tags=tags)
    for k, gy in enumerate((-0.11, -0.04)):
        B.box(f"nk_bar{k}", 0, gy, 0.10, 0.018, top - 0.03, top - 0.005, S, bevel=0.003, tags=tags)
    # faixas verdes em sulcos escuros: larga logo acima do colar da base, fina logo abaixo do pescoco
    for k, (by, hw) in enumerate(BANDS):
        octo_cyl(f"nk_bandk{k}", 0, by - hw - 0.015, by + hw + 0.015, R + 0.006, M["black"], tags, bevel=0.0)
        octo_cyl(f"nk_band{k}", 0, by - hw, by + hw, R + 0.010, X["band"], tags, bevel=0.0)

    # ---- colar claro da base (bisel duplo) com o contador de 2 LEDs verdes numa fenda escura
    col = B.rpoly(0, (Y_COL0 + Y_COL1) / 2, 2 * (R + 0.02), Y_COL1 - Y_COL0, 0, chamfer=0.04)
    ca, cp = B.shard("nk_col", col, ZC - 0.06, top + 0.03, A, slope=0.035, groove=0.016, panel_h=0.02, tags=tags)
    Mo.slot_with_pips("nk_cnt", (Y_COL0 + Y_COL1) / 2, -0.085, 0.085, 0.05, top + 0.05, 2, M, tags, target=[ca, cp],
                      depth=0.075, vertical=False)

    # ---- colar claro do pescoco (bisel duplo) com linha de painel
    nk = B.rpoly(0, (Y_NECK0 + Y_NECK1) / 2, 2 * (R + 0.01), Y_NECK1 - Y_NECK0, 0, chamfer=0.022)
    na, npn = B.shard("nk_neck", nk, ZC - 0.06, top + 0.02, A, slope=0.012, groove=0.008, panel_h=0.018, tags=tags)
    if npn is not None:
        B.cut(npn, [B.box("nk_npl", 0, (Y_NECK0 + Y_NECK1) / 2, 0.24, 0.02, top - 0.02, top + 0.3, K, bevel=0.0)])

    # ---- ogiva pontuda cinza clara com o trevo, anel de painel e espoleta
    ogive("nk_og", 0, OG_PROF[0][0], ZC, 1.0, X, M, tags)
