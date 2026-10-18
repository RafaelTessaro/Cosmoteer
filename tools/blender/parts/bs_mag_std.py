"""Carregador Padrao (Standard Magazine) - municao empacotada pela Prensa de Carregadores e levada pela tripulacao.

Caixa de carregador blindada na linguagem da familia (a mesma do Carregador Perfurante): nucleo escuro MAIOR que
as cascas, de modo que uma moldura escura contorna a peca; casca clara chanfrada com bisel duplo partida em duas
metades (frente e tras) por um vao escuro com o contador de 4 LEDs ambar.
  * metade da frente em cunha com uma janela retangular longa e 3 balas de canhao grandes em fileira dupla
    desencontrada (como um carregador de duas colunas): a do meio na frente, entre os labios de aco da boca, e
    as duas de fora recuadas, de modo que as pontas formam uma seta (e nao uma fileira de pinos de conector).
    Cada bala mostra o perfil inteiro da bala do jogo que entra na prensa: corpo cinza-azulado, cinta escura e
    ogiva de latao pontuda, com vao escuro entre elas;
  * metade de tras com um entalhe aberto na ponta (o nucleo escuro aparece) e a alca de aco atravessando o
    entalhe sobre suportes escuros: le como a pega de uma caixa de municao, e nao como uma porta/fenda.
A cintura do nucleo no vao, a cunha da frente e o entalhe de tras quebram a silhueta.
Unidade modelada centrada na origem, frente = +Y (como o Perfurante), ~0.62 x 0.91, cabendo em 1 x 1, altura
maxima 0.445 (a prensa usa esta unidade em miniatura na esteira de saida e conta com essa altura); o
renderizador escala para a pilha (stack_layout: camada de baixo 2 x 2 com as alcas para fora e camada de cima
em tijolo, uma unidade sobre cada coluna).
"""

import bs3d as B
import models as Mo  # noqa: F401  (contrato dos modelos)

H_TOP = 0.188  # altura da camada de cima da pilha (ja na escala da unidade: apoiada nas cascas de baixo)
CX, RY = 0.185, 0.235   # colunas e fileiras da camada de baixo
PART = {
    "id": "rafaeltessaro.bs_mag_std",
    "kind": "resource",
    "accent": "amber",
    "unit_scale": 0.50,
    "icon_scale": 0.80,
    # pilha organizada que enche o tile como as pilhas do jogo: 1 no centro, 2 lado a lado, 3 em piramide, 4 em
    # 2 x 2 (fileira de cima girada 180 graus: as alcas ficam nas bordas e as janelas no meio). 5 e 6 ganham a
    # camada de cima em "tijolo": uma unidade deitada sobre cada coluna, cobrindo as duas metades da frente de
    # baixo e terminando exatamente no vao dos LEDs delas; de baixo so aparecem as pontas inteiras (alca + LEDs),
    # sem lascas de janela/LED nas bordas da unidade de cima (como acontecia com a camada cruzada a 90 graus)
    "stack_layout": {
        1: [(0, 0, 0)],
        2: [(-CX, 0, 0), (CX, 0, 0)],
        3: [(-CX, -RY, 0), (CX, -RY, 0), (0, RY, 0)],
        4: [(-CX, -RY, 0), (CX, -RY, 0), (-CX, RY, 0), (CX, RY, 0)],
        5: [(-CX, -RY, 0), (CX, -RY, 0), (-CX, RY, 0), (CX, RY, 0), (-CX, 0.0, H_TOP)],
        6: [(-CX, -RY, 0), (CX, -RY, 0), (-CX, RY, 0), (CX, RY, 0), (-CX, 0.0, H_TOP), (CX, 0.0, H_TOP)],
    },
    # indice 2 e 3 = fileira de cima (girada 180); 4 e 5 = camada de cima (janela para a frente, leve torcao)
    "stack_rot": [0, 1.5, 181, 178.5, -1.0, 1.0],
}

# geometria compartilhada (a prensa reaproveita esta unidade em miniatura na esteira de saida)
CORE_X, CORE_Y = 0.31, 0.455        # meia largura / meio comprimento do nucleo
SHELL_X = 0.25                      # meia largura das cascas (moldura escura de 0.06 dos lados)
GAP0, GAP1 = -0.075, 0.005          # vao entre as metades (contador de LEDs)
WIN_Y0, WIN_Y1 = 0.09, 0.30         # janela das balas (0.34 de largura)
LIP_Y = 0.303                       # labios de aco na boca da janela
# entalhe de tras (do fundo da casca ate NOTCH_Y) e sua largura: o topo fica 0.033 abaixo da face do painel
# interno (sem lasca fina de painel) e as orelhas da casca descem alem da alca, que fica solta no meio do entalhe
NOTCH_Y, NOTCH_W = -0.195, 0.27
HANDLE_Y = -0.285                   # eixo da alca


def _round_mats():
    """Materiais da bala de canhao (iguais aos da bala do jogo: corpo cinza-azulado escuro, ogiva de latao)."""
    return (B.mat_metal("round_body", (0.10, 0.11, 0.14), rough=0.34, metal=0.85),
            B.mat_metal("brass", (0.66, 0.44, 0.12), rough=0.28, metal=1.0))


def _case_mat():
    """Corpo cinza-azulado das balas na janela, um pouco mais claro que o da bala do jogo: precisa se destacar do
    fundo preto da janela sem se confundir com a moldura clara."""
    return B.mat_metal("mag_case", (0.16, 0.17, 0.21), rough=0.40, metal=0.85)


def _cartridge(name, x, tip, z, r, M, tags):
    """Bala de canhao deitada ao longo de +Y com a ponta em y = tip, como a bala do jogo que entra na prensa:
    corpo cinza-azulado (comprido, segue por baixo da casca), cinta escura e ogiva de latao grande em dois
    troncos (perfil arredondado que termina em ponta)."""
    _, brass = _round_mats()
    o1, o2 = 0.040, 0.050                       # troncos da ogiva (base larga + ponta)
    yb = tip - o1 - o2                          # base da ogiva
    band = 0.014
    yc = yb - band                              # fim do corpo
    lc = yc - (WIN_Y0 - 0.06)
    B.cyl(name + "_c", x, yc - lc / 2, z, r, lc, _case_mat(), axis="Y", verts=16, bevel=0.0, tags=tags)
    B.cyl(name + "_d", x, yc + band / 2, z, r * 1.02, band, M["core_mid"], axis="Y", verts=16, bevel=0.0, tags=tags)
    B.cyl(name + "_o", x, yb + o1 / 2, z, r * 0.98, o1, brass, axis="Y", verts=16, bevel=0.0, tags=tags, r2=r * 0.78)
    B.cyl(name + "_p", x, yb + o1 + o2 / 2, z, r * 0.78, o2, brass, axis="Y", verts=16, bevel=0.0, tags=tags,
          r2=r * 0.22)


def item(M, T="item"):
    tags = (T,)
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    # nucleo escuro com cintura no vao e frente em cunha (a moldura escura aparece em volta das cascas)
    cx, cy = CORE_X, CORE_Y
    core = [(-0.25, -cy), (0.25, -cy), (cx, -cy + 0.06), (cx, GAP0 - 0.035), (cx - 0.035, GAP0), (cx - 0.035, GAP1),
            (cx, GAP1 + 0.035), (cx, 0.32), (0.18, cy), (-0.18, cy), (-cx, 0.32), (-cx, GAP1 + 0.035),
            (-cx + 0.035, GAP1), (-cx + 0.035, GAP0), (-cx, GAP0 - 0.035), (-cx, -cy + 0.06)]
    B.plate("mag_core", core, 0.0, 0.30, K, slope=0.015, tags=tags)
    sx = SHELL_X
    # ---------------------------------------------------------------- metade da frente: cunha com a janela
    # a cunha comeca acima da janela, para a moldura clara em volta dela ter pelo menos 0.03 de face
    front = [(-sx, GAP1), (sx, GAP1), (sx, 0.32), (0.15, 0.405), (-0.15, 0.405), (-sx, 0.32)]
    fa, fp = B.shard("mag_front", front, 0.04, 0.34, A, slope=0.05, groove=0.025, panel_h=0.03, tags=tags)
    win = B.rpoly(0, (WIN_Y0 + WIN_Y1) / 2, 0.34, WIN_Y1 - WIN_Y0, 0, chamfer=0.02)
    for t, k in ((fa, "a"), (fp, "b")):
        B.cut(t, [B.loft(f"mag_win{k}", win, win, 0.30, 0.8, K, bevel=0.0)])
    B.loft("mag_winbed", win, win, 0.298, 0.304, M["black"], bevel=0.0, tags=tags)
    # 3 balas grandes (com vao escuro entre elas, para nao virarem um bloco): a do meio na frente, com a ponta
    # entre os labios; as de fora recuadas e um pouco mais baixas (a segunda coluna do carregador)
    for i in range(3):
        lead = i == 1
        _cartridge(f"mag_r{i}", (i - 1) * 0.11, LIP_Y + 0.004 if lead else LIP_Y - 0.036, 0.336 if lead else 0.326,
                   0.044, M, tags)
    # labios de aco na boca: duas pecas nas pontas (o meio fica livre e mostra a ponta da bala de cima)
    for s in (-1, 1):
        lip = [(s * 0.045, LIP_Y - 0.012), (s * 0.15, LIP_Y - 0.012), (s * 0.172, LIP_Y + 0.012),
               (s * 0.045, LIP_Y + 0.012)]
        B.loft(f"mag_lip{s}", lip, lip, 0.33, 0.385, S, bevel=0.006, tags=tags)
    # ---------------------------------------------------------------- vao central: contador de 4 LEDs ambar
    gy = (GAP0 + GAP1) / 2
    B.box("mag_gapbed", 0, gy, 0.44, GAP1 - GAP0 - 0.01, 0.296, 0.302, M["black"], bevel=0.0, tags=tags)
    for i in range(4):
        B.box(f"mag_led{i}", -0.15 + i * 0.10, gy, 0.056, 0.032, 0.302, 0.312, M["glow"], bevel=0.0, tags=tags)
    # ---------------------------------------------------------------- metade de tras: entalhe aberto com a alca
    back = [(-0.20, -0.405), (0.20, -0.405), (sx, -0.355), (sx, GAP0), (-sx, GAP0), (-sx, -0.355)]
    ba, bp = B.shard("mag_back", back, 0.04, 0.34, A, slope=0.05, groove=0.025, panel_h=0.03, tags=tags)
    notch = B.rpoly(0, (NOTCH_Y - 0.6) / 2, NOTCH_W, NOTCH_Y + 0.6, 0)
    for t, k in ((ba, "a"), (bp, "b")):
        B.cut(t, [B.loft(f"mag_notch{k}", notch, notch, 0.0, 0.8, K, bevel=0.0)])
    # alca: barra de aco sobre dois suportes escuros presos nas orelhas da casca; o nucleo escuro aparece em
    # volta dela (entalhe), de modo que ela le como peca elevada (altura maxima 0.445)
    hz, hr = 0.414, 0.031
    for s in (-1, 1):
        B.box(f"mag_hpost{s}", s * (NOTCH_W / 2 + 0.025), HANDLE_Y, 0.045, 0.075, 0.30, 0.43, KM, bevel=0.008,
              tags=tags)
    B.cyl("mag_handle", 0, HANDLE_Y, hz, hr, NOTCH_W + 0.07, S, axis="X", verts=16, bevel=0.004, tags=tags)
