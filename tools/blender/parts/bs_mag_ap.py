"""Carregador Perfurante (Armor-Piercing Magazine) - AP e APHE usam o mesmo; pilha de 4.

Mesma construcao do Carregador Padrao (nucleo escuro, casca chanfrada com bisel duplo, contador de 4 LEDs
ambar numa fenda escura, tampa clara separada por vao escuro com fendas de pega), em pe (frente = +Y) para a
leitura de "perfurante":
  * nucleo escuro so um pouco maior que as cascas: moldura escura fina (1-2 px) em volta da peca;
  * frente: mandibulas de blindagem clara (pecas em U com bisel duplo) em volta da janela escura;
  * 3 pontas de tristeel prateadas e afiadas em pe na janela (a do meio mais longa, com brilho frio
    azul-branco pequeno) saindo alem do contorno, em ponta de flecha;
  * vao escuro estreito entre as mandibulas e o corpo (chanfros baixos: a unidade le como uma peca so);
  * corpo de aco canhoneado (cinza medio, mais escuro que a blindagem do Padrao) com o contador de 4 LEDs,
    faixa azul-branca atravessada na parte de baixo e linhas de painel largas;
  * tampa traseira de verdade (aco canhoneado claro, bisel duplo) separada por vao escuro, com 2 fendas
    escuras de pega cortadas no painel (como a tampa do Padrao): fecha o contorno da unidade em claro.
Unidade modelada centrada na origem (eixo longo em Y, ~0.67 x 1.07), cabendo em 1 x 1; o renderizador escala
para a pilha (stack_layout: lado a lado, piramide e 2 x 2, com giros pequenos como os tijolos do Padrao).
"""

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_mag_ap",
    "kind": "resource",
    "accent": "amber",
    "unit_scale": 0.41,
    "icon_scale": 0.80,
    # pilha organizada: 1 no centro, 2 lado a lado, 3 em piramide, 4 em 2 x 2 (sem sobrepor as pontas)
    "stack_layout": {
        1: [(0, 0, 0)],
        2: [(-0.17, 0, 0), (0.17, 0, 0)],
        3: [(-0.17, -0.222, 0), (0.17, -0.222, 0), (0, 0.222, 0)],
        4: [(-0.17, -0.222, 0), (0.17, -0.222, 0), (-0.17, 0.222, 0), (0.17, 0.222, 0)],
    },
    "stack_rot": [0, 1.5, -1.5, 1, -2, 2],
}

SHELL = (0.20, 0.22, 0.25)     # aco canhoneado do corpo (mais escuro que a blindagem clara, mais claro que o nucleo)
LID = (0.40, 0.42, 0.46)       # aco canhoneado claro da tampa (fecha o contorno da unidade sobre a base escura)


def _mats():
    return {
        "shell": B.mat_paint("ap_shell", SHELL, rough=0.36, metal=0.45, wear=0.18, grime=0.04, scale=5),
        "lid": B.mat_paint("ap_lid", LID, rough=0.34, metal=0.25, wear=0.18, grime=0.04, scale=5),
        "band": B.mat_paint("ap_band", (0.50, 0.68, 0.98), rough=0.25, metal=0.1, wear=0.05, grime=0.0, scale=5),
        "silver": B.mat_metal("silver", (0.80, 0.82, 0.86), rough=0.16, metal=1.0),
        "glint": B.mat_glow("glint", (0.70, 0.86, 1.0), 4.0),
    }


def item(M, T="item"):
    tags = (T,)
    X = _mats()
    A, K, S = M["armor"], M["core"], M["steel"]
    # nucleo escuro so um pouco maior que as cascas (~0.02-0.025): moldura escura fina que separa a unidade
    # da base sem pesar
    core = [(-0.335, -0.475), (-0.27, -0.54), (0.27, -0.54), (0.335, -0.475), (0.335, 0.28), (0.245, 0.393),
            (-0.245, 0.393), (-0.335, 0.28)]
    B.plate("ap_core", core, 0.0, 0.27, K, slope=0.012, tags=tags)

    # ---- frente: mandibulas claras em U em volta da janela das pontas (chanfro baixo para o vao ficar fino)
    front = [(-0.31, 0.0), (0.31, 0.0), (0.31, 0.27), (0.23, 0.37), (-0.23, 0.37), (-0.31, 0.27)]
    fa, fp = B.shard("ap_jaw", front, 0.04, 0.33, A, slope=0.03, groove=0.015, panel_h=0.025, tags=tags)
    win = [(-0.19, 0.12), (0.19, 0.12), (0.19, 0.60), (-0.19, 0.60)]
    for t, k in ((fa, "a"), (fp, "b")):
        B.cut(t, [B.loft(f"ap_win{k}", win, win, 0.26, 0.8, K, bevel=0.0)])
    B.box("ap_winbed", 0, 0.25, 0.38, 0.26, 0.255, 0.265, M["black"], bevel=0.0, tags=tags)
    # linha de painel diagonal em cada canto de baixo das mandibulas (larga o bastante para os 64 px)
    if fp is not None:
        B.cut(fp, [B.rbox(f"ap_jpl{sx}", sx * 0.24, 0.07, 0.022, 0.10, 0.29, 0.6, K, rot=sx * -45, bevel=0.0)
                   for sx in (-1, 1)])
    # 3 pontas de tristeel (cones facetados em pe; a do meio mais longa: frente em ponta de flecha)
    r = 0.055
    for i, (x, y0, y1) in enumerate(((-0.12, 0.15, 0.45), (0.0, 0.15, 0.52), (0.12, 0.15, 0.45))):
        B.cyl(f"ap_tip{i}", x, (y0 + y1) / 2, 0.315, r, y1 - y0, X["silver"], axis="Y", verts=6, bevel=0.0,
              r2=0.0, tags=tags)
        B.cyl(f"ap_col{i}", x, y0 - 0.012, 0.315, r + 0.008, 0.03, S, axis="Y", verts=6, bevel=0.004, tags=tags)
    # brilho frio pequeno na ponta do meio
    B.box("ap_glint", 0.0, 0.29, 0.018, 0.06, 0.375, 0.381, X["glint"], bevel=0.0, tags=tags)

    # ---- corpo de aco canhoneado (vao escuro de 0.04 ate as mandibulas e de 0.035 ate a tampa)
    body = B.rpoly(0, -0.1875, 0.62, 0.295, 0, chamfer=0.05)
    ba, bp = B.shard("ap_body", body, 0.04, 0.33, X["shell"], slope=0.03, groove=0.015, panel_h=0.025, tags=tags)
    # contador de 4 LEDs ambar numa fenda escura (metade de cima do corpo)
    Mo.slot_with_pips("ap_cnt", -0.14, -0.15, 0.15, 0.06, 0.355, 4, M, tags, target=[ba, bp], depth=0.075,
                      vertical=False)
    # linhas de painel diagonais nos cantos de cima do corpo (largura >= 0.02, fundo abaixo do painel)
    if bp is not None:
        B.cut(bp, [B.rbox(f"ap_bpl{sx}", sx * 0.225, -0.10, 0.022, 0.08, 0.29, 0.6, K, rot=sx * 45, bevel=0.0)
                   for sx in (-1, 1)])
    # faixa azul-branca atravessada na borda de baixo do corpo (anel pintado em volta dele; vao de 0.03 ate a tampa)
    B.box("ap_band", 0, -0.31, 0.66, 0.06, 0.04, 0.37, X["band"], bevel=0.008, tags=tags)

    # ---- tampa traseira clara (bisel duplo de verdade) com 2 fendas escuras de pega
    cap = B.rpoly(0, -0.4475, 0.60, 0.155, 0, chamfer=0.04)
    ca, cp = B.shard("ap_cap", cap, 0.04, 0.31, X["lid"], slope=0.02, groove=0.015, panel_h=0.015, tags=tags)
    for k, gy in enumerate((-0.43, -0.47)):
        for t, nm in ((ca, "a"), (cp, "b")):
            if t is not None:
                B.cut(t, [B.box(f"ap_grip{k}{nm}", 0, gy, 0.22, 0.022, 0.20, 0.6, K, bevel=0.0)])
        B.box(f"ap_gripbed{k}", 0, gy, 0.22, 0.022, 0.20, 0.21, M["black"], bevel=0.0, tags=tags)
    # parafusos de aco nas pontas da tampa (fora das fendas)
    B.bolts("ap_capb", [(-0.22, -0.45), (0.22, -0.45)], 0.33, 0.016, S, tags=tags)
