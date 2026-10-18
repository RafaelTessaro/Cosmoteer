"""Projetil Nuclear (Nuclear Shell) - municao do Obuseiro Nuclear Boiuna; pilha de 2; explode se a pilha cair.

Mesma familia dos carregadores (nucleo escuro + cascas claras chanfradas com bisel duplo, contador de LEDs numa
fenda escura), mas com outra silhueta e outra cor: uma granada de artilharia enorme deitada ao longo do tile
(frente = +Y, ogiva para cima), igual as granadas do rack da torre do Boiuna (corpo escuro, faixas verdes):
  * anel de base pesado de aco (octogonal, com sulco escuro) e colar de blindagem clara chanfrada na base,
    com o contador de 2 LEDs verdes numa fenda escura;
  * corpo de aco canhoneado quase preto, octogonal de topo plano (facetas chanfradas como os canos da
    familia), com faixa verde num sulco escuro e janela longitudinal escura mostrando o nucleo verde
    (barra de luz com grade de aco atravessada);
  * trevo de 3 cunhas verde fraco num rebaixo escuro (marca nuclear, como o trevo da espinha do Boiuna);
  * colar claro chanfrado no pescoco e ogiva pontuda em 2 troncos facetados com espoleta de aco.
Unidade modelada centrada na origem (eixo longo em Y, ~0.40 x 1.0); o renderizador escala para a pilha
(1 no centro, 2 lado a lado). O icone fica em diagonal (ogiva para cima-direita) para encher o quadro.
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_shell_nuke",
    "kind": "resource",
    "accent": "green",
    "unit_scale": 0.90,
    "icon_scale": 0.92,
    "icon_rot": -45,
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
BODY = (0.040, 0.043, 0.048)      # aco canhoneado quase preto
OGIVE = (0.13, 0.135, 0.145)      # ogiva cinza escura (mais clara que o corpo, como as granadas do Boiuna)


def mats():
    """Materiais proprios (sem desgaste nas pecas escuras pequenas: o desgaste das quinas clareia a malha)."""
    return {
        "body": B.mat_metal("nk_body", BODY, rough=0.48, metal=0.55),
        "ogive": B.mat_metal("nk_ogive", OGIVE, rough=0.42, metal=0.6),
        "core_glow": B.mat_glow("nk_core", Mo.GREEN, 2.2),
    }


def octo_cyl(name, x, y0, y1, r, mat, tags, r2=None, z=ZC, bevel=0.006):
    """Cilindro octogonal deitado em Y, de y0 a y1, com uma face plana em cima (girado 22.5 graus no eixo)."""
    ob = B.cyl(name, x, (y0 + y1) / 2, z, r, y1 - y0, mat, axis="Y", verts=8, bevel=bevel, r2=r2, tags=tags)
    ob.rotation_euler = (math.radians(-90), math.radians(22.5), 0)
    return ob


def trefoil(name, cx, cy, z, r0, r1, mat, tags, a0=90.0):
    """Trevo de 3 cunhas (setores de 60 graus, uma apontando para a0) + ponto central."""
    for k in range(3):
        a = math.radians(a0 + k * 120 - 30)
        pts = [(cx + math.cos(a + i / 4 * math.radians(60)) * r1, cy + math.sin(a + i / 4 * math.radians(60)) * r1)
               for i in range(5)]
        pts += [(cx + math.cos(a + math.radians(60)) * r0, cy + math.sin(a + math.radians(60)) * r0),
                (cx + math.cos(a) * r0, cy + math.sin(a) * r0)]
        B.loft(f"{name}{k}", pts, pts, z, z + 0.006, mat, bevel=0.0, tags=tags)
    B.cyl(f"{name}c", cx, cy, z + 0.003, r0 * 0.62, 0.006, mat, axis="Z", verts=10, bevel=0.0, tags=tags)


def item(M, T="item"):
    tags = (T,)
    X = mats()
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    top = ZC + R * math.cos(math.radians(22.5))      # face de cima do corpo

    # ---- anel de base pesado (aco) com sulco escuro e o fundo escuro do estojo
    octo_cyl("nk_base", 0, Y_BASE0, Y_BASE1, R + 0.018, S, tags, bevel=0.008)
    octo_cyl("nk_baseg", 0, Y_BASE1 - 0.002, Y_COL0 + 0.004, R - 0.01, K, tags, bevel=0.0)
    B.box("nk_basel", 0, (Y_BASE0 + Y_BASE1) / 2, 0.20, 0.016, top + 0.005, top + 0.03, KM, bevel=0.0, tags=tags)

    # ---- corpo escuro (entre os colares; os colares claros cobrem as pontas)
    body = octo_cyl("nk_body", 0, Y_COL1 - 0.02, Y_NECK0 + 0.02, R, X["body"], tags)
    # janela longitudinal no topo do corpo: recesso escuro com o nucleo verde e grade de aco
    wy0, wy1 = -0.165, 0.035
    B.cut(body, [B.box("nk_winc", 0, (wy0 + wy1) / 2, 0.09, wy1 - wy0, top - 0.05, top + 0.3, K, bevel=0.0)])
    B.box("nk_winbed", 0, (wy0 + wy1) / 2, 0.09, wy1 - wy0, top - 0.06, top - 0.045, M["black"], bevel=0.0,
          tags=tags)
    B.box("nk_core", 0, (wy0 + wy1) / 2, 0.034, wy1 - wy0 - 0.04, top - 0.045, top - 0.035, X["core_glow"],
          bevel=0.0, tags=tags)
    for k, gy in enumerate((-0.10, -0.03)):
        B.box(f"nk_bar{k}", 0, gy, 0.10, 0.018, top - 0.03, top - 0.005, S, bevel=0.003, tags=tags)
    # faixa verde num sulco escuro, logo acima do colar da base
    by = -0.225
    octo_cyl("nk_bandk", 0, by - 0.026, by + 0.026, R + 0.006, M["black"], tags, bevel=0.0)
    octo_cyl("nk_band", 0, by - 0.011, by + 0.011, R + 0.010, M["glow_dim"], tags, bevel=0.0)

    # ---- colar claro da base (bisel duplo) com o contador de 2 LEDs verdes numa fenda escura
    col = B.rpoly(0, (Y_COL0 + Y_COL1) / 2, 2 * (R + 0.02), Y_COL1 - Y_COL0, 0, chamfer=0.04)
    ca, cp = B.shard("nk_col", col, ZC - 0.06, top + 0.03, A, slope=0.035, groove=0.016, panel_h=0.02, tags=tags)
    Mo.slot_with_pips("nk_cnt", (Y_COL0 + Y_COL1) / 2, -0.085, 0.085, 0.05, top + 0.05, 2, M, tags, target=[ca, cp],
                      depth=0.075, vertical=False)

    # ---- colar claro do pescoco (bisel duplo) com linha de painel
    nk = B.rpoly(0, (Y_NECK0 + Y_NECK1) / 2, 2 * (R + 0.01), Y_NECK1 - Y_NECK0, 0, chamfer=0.035)
    na, npn = B.shard("nk_neck", nk, ZC - 0.06, top + 0.02, A, slope=0.03, groove=0.014, panel_h=0.018, tags=tags)
    if npn is not None:
        B.cut(npn, [B.box("nk_npl", 0, (Y_NECK0 + Y_NECK1) / 2, 0.24, 0.02, top - 0.02, top + 0.3, K, bevel=0.0)])

    # ---- ogiva pontuda em 3 troncos facetados + espoleta de aco
    prof = [(Y_NECK1 - 0.01, R - 0.012), (0.25, R * 0.84), (0.35, R * 0.62), (0.44, R * 0.30)]
    for k in range(len(prof) - 1):
        (y0, r0), (y1, r1) = prof[k], prof[k + 1]
        octo_cyl(f"nk_og{k}", 0, y0, y1, r0, X["ogive"], tags, r2=r1, bevel=0.004)
    octo_cyl("nk_fuze", 0, 0.44, Y_TIP, R * 0.30, S, tags, r2=0.01, bevel=0.0)
    octo_cyl("nk_fuzer", 0, 0.435, 0.455, R * 0.33, KM, tags, bevel=0.0)
