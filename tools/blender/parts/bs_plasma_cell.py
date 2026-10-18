"""Celula de Plasma (Plasma Cell) - municao do Canhao de Plasma Pesado Curupira e da Gatling de Plasma Boitata.

Mesma familia dos carregadores (nucleo escuro, cascas claras chanfradas com bisel duplo, contador de 4 LEDs numa
fenda escura), mas NAO e uma caixa: e uma capsula (canister) estreita e comprida, igual as celulas dos tanques
das torres de plasma (cilindro escuro facetado com tampas e coluna de nivel ciano), em pe (eixo longo = Y):
  * nucleo escuro em capsula (octogono alongado) por baixo de tudo: moldura escura fina em volta das pecas;
  * corpo cilindrico de 8 faces escuro (aco azulado) com uma janela longa recortada no topo, mostrando o nucleo
    de plasma ciano brilhando (tubo ciano saturado + barra de nivel clara no meio);
  * duas bobinas magneticas (aneis de aco facetados com enrolamento de cobre aparecendo nas ranhuras) mais
    largas que o corpo: a silhueta fica em "carretel" com nervuras, bem diferente das caixas dos carregadores;
  * tampas blindadas claras nas duas pontas (lascas com bisel duplo e cantos chanfrados): a de cima com o
    terminal de contato de aco num recesso escuro, a de baixo com o contador de 4 LEDs ciano numa fenda vazada.
Unidade centrada na origem, ~0.40 x 0.96, altura maxima ~0.40. A fabrica (parts/bs_factory_plasma.py) usa
cell() em miniatura no berco de enchimento, com o nivel do plasma subindo (level) e os LEDs acendendo.
Pilha: as celulas ficam em pe lado a lado numa fileira (como as bandejas de celulas das torres de plasma),
1 no centro ate 4 em fileira.
"""

import bs3d as B
import models as Mo

PITCH = 0.228   # distancia entre as celulas na fileira da pilha (tiles)
PART = {
    "id": "rafaeltessaro.bs_plasma_cell",
    "kind": "resource",
    "accent": "cyan",
    "unit_scale": 0.46,
    "icon_scale": 0.84,
    # fileira de celulas em pe (bandeja de celulas das torres), centrada
    "stack_layout": {
        1: [(0, 0, 0)],
        2: [(-PITCH / 2, 0, 0), (PITCH / 2, 0, 0)],
        3: [(-PITCH, 0, 0), (0, 0, 0), (PITCH, 0, 0)],
        4: [(-1.5 * PITCH, 0, 0), (-PITCH / 2, 0, 0), (PITCH / 2, 0, 0), (1.5 * PITCH, 0, 0)],
    },
    "stack_rot": [0, 0, 0, 0, 0, 0],
}

# geometria (unidade)
BODY_R = 0.150          # raio do corpo cilindrico (8 faces)
BODY_Z = 0.175          # altura do eixo do corpo
CAP_Y0, CAP_Y1 = 0.285, 0.48   # tampas: de |y| = CAP_Y0 ate CAP_Y1
CAP_X = 0.19            # meia largura das tampas
RING_Y = 0.212          # centro das bobinas (|y|)
RING_R = 0.232          # raio das bobinas (mais largas que tudo: nervuras na silhueta)
WIN_Y = 0.150           # janela: y em [-WIN_Y, WIN_Y]
WIN_W = 0.10            # largura da janela


def _mats():
    """Materiais proprios (aco azulado escuro do corpo, cobre das bobinas, plasma ciano saturado)."""
    return {
        # metal (sem desgaste de pintura: pecas escuras pequenas nao clareiam, STYLE.md 9 / armadilha a)
        "body": B.mat_metal("pc_body", (0.035, 0.048, 0.060), rough=0.32, metal=0.85),
        "copper": B.mat_metal("pc_copper", (0.62, 0.30, 0.12), rough=0.30, metal=1.0),
        "glass": B.mat_metal("pc_glass", (0.010, 0.030, 0.036), rough=0.12, metal=0.3),
        # plasma: ciano saturado (forca baixa para nao estourar em branco) + barra de nivel clara
        "plasma": B.mat_glow("pc_plasma", Mo.CYAN, 1.25),
        "level": B.mat_glow("pc_level", (0.55, 0.95, 1.0), 2.6),
        # LEDs do contador: ciano (forca media: le como LED ciano, nao como borrao branco)
        "led": B.mat_glow("pc_led", Mo.CYAN, 2.0),
    }


def _cap(name, sy, M, X, tags, leds):
    """Tampa blindada clara de uma ponta (sy = +1 em cima, -1 embaixo)."""
    A, K, S = M["armor"], M["core"], M["steel"]
    y0, y1 = CAP_Y0, CAP_Y1
    pts = [(-CAP_X, y0), (CAP_X, y0), (CAP_X, y1 - 0.095), (CAP_X - 0.095, y1), (-CAP_X + 0.095, y1),
           (-CAP_X, y1 - 0.095)]
    poly = [(x, sy * y) for x, y in pts]
    ca, cp = B.shard(name, poly, 0.04, 0.33, A, slope=0.035, groove=0.016, panel_h=0.025, tags=tags)
    yc = sy * (y0 + y1) / 2
    if sy > 0:
        # terminal de contato: pino octogonal de aco baixo sobre um colar escuro, furo escuro no meio
        B.cyl(name + "_tcol", 0, yc + 0.01, 0.37, 0.068, 0.02, K, axis="Z", verts=8, bevel=0.0, tags=tags)
        B.cyl(name + "_pin", 0, yc + 0.01, 0.385, 0.048, 0.03, S, axis="Z", verts=8, bevel=0.008, tags=tags)
        B.cyl(name + "_pin2", 0, yc + 0.01, 0.40, 0.018, 0.008, K, axis="Z", verts=8, bevel=0.0, tags=tags)
        # linhas de painel nos ombros chanfrados
        if cp is not None:
            B.cut(cp, [B.rbox(f"{name}_pl{sx}", sx * 0.115, sy * 0.425, 0.016, 0.07, 0.30, 0.6, K, rot=sx * sy * 45,
                              bevel=0.0) for sx in (-1, 1)])
    else:
        # contador de 4 LEDs ciano numa fenda VAZADA (sem filete do bisel tampando o leito, armadilha b)
        sx_, sy_ = 0.27, 0.06
        for k, t in enumerate((ca, cp)):
            if t is not None:
                B.cut(t, [B.box(f"{name}_lc{k}", 0, yc, sx_, sy_, 0.05, 0.8, K, bevel=0.0)])
        B.box(name + "_lbed", 0, yc, sx_, sy_, 0.06, 0.07, M["black"], bevel=0.0, tags=tags)
        for i in range(4):
            on = i < leds
            B.box(f"{name}_led{i}", -0.0975 + i * 0.065, yc, 0.040, 0.032, 0.07, 0.30,
                  X["led"] if on else M["core_mid"], bevel=0.0, tags=tags)
    return ca, cp


def cell(M, tags, level=1.0, leds=4, name="pc"):
    """Uma celula na origem. level = fracao do nucleo de plasma acesa (de baixo para cima); leds = LEDs acesos."""
    X = _mats()
    K, KM, S, A = M["core"], M["core_mid"], M["steel"], M["armor"]
    # nucleo escuro em capsula (moldura escura em volta das tampas e das bobinas)
    core = [(-0.15, -0.50), (0.15, -0.50), (0.215, -0.435), (0.215, 0.435), (0.15, 0.50), (-0.15, 0.50),
            (-0.215, 0.435), (-0.215, -0.435)]
    B.plate(name + "_core", core, 0.0, 0.07, K, slope=0.015, tags=tags)
    # corpo cilindrico facetado (8 faces, como as celulas dos tanques das torres)
    bl = 2 * CAP_Y0 + 0.04
    body = B.cyl(name + "_body", 0, 0, BODY_Z, BODY_R, bl, X["body"], axis="Y", verts=8, bevel=0.0, tags=tags)
    # janela longa no topo do corpo (recorte com leito escuro) mostrando o tubo de plasma
    zt = BODY_Z + BODY_R
    B.cut(body, [B.box(name + "_wc", 0, 0, WIN_W, 2 * WIN_Y, zt - 0.075, zt + 0.3, K, bevel=0.0)])
    B.box(name + "_wbed", 0, 0, WIN_W, 2 * WIN_Y, zt - 0.085, zt - 0.072, M["black"], bevel=0.0, tags=tags)
    # tubo de plasma: aceso de baixo ate o nivel, vidro escuro acima; barra de nivel clara no meio
    tz, tr = zt - 0.072 + 0.026, 0.030
    L = 2 * WIN_Y - 0.02
    y0 = -L / 2
    lit = max(0.0, min(1.0, level)) * L
    if lit > 0.004:
        B.cyl(name + "_pl", 0, y0 + lit / 2, tz, tr, lit, X["plasma"], axis="Y", verts=12, bevel=0.0, tags=tags)
        B.box(name + "_lvl", 0, y0 + lit / 2, 0.012, max(0.004, lit - 0.03), tz + tr - 0.004, tz + tr + 0.004,
              X["level"], bevel=0.0, tags=tags)
    if lit < L - 0.004:
        B.cyl(name + "_gl", 0, y0 + lit + (L - lit) / 2, tz, tr, L - lit, X["glass"], axis="Y", verts=12,
              bevel=0.0, tags=tags)
    # marcas de escala (aco) nas bordas da janela, a cada quarto
    for i in range(1, 4):
        yy = -WIN_Y + i * (2 * WIN_Y) / 4
        for sx in (-1, 1):
            B.box(f"{name}_tick{i}{sx}", sx * (WIN_W / 2 + 0.012), yy, 0.022, 0.012, zt - 0.03, zt + 0.004, S,
                  bevel=0.0, tags=tags)
    # bobinas magneticas: enrolamento de cobre entre dois colares de aco facetados (mais largos que as tampas)
    for k, sy in enumerate((-1, 1)):
        y = sy * RING_Y
        B.cyl(f"{name}_cu{k}", 0, y, BODY_Z, RING_R - 0.018, 0.088, X["copper"], axis="Y", verts=8, bevel=0.0,
              tags=tags)
        for j, dy in enumerate((-0.036, 0.036)):
            B.cyl(f"{name}_ring{k}{j}", 0, y + dy, BODY_Z, RING_R, 0.026, S, axis="Y", verts=8, bevel=0.004,
                  tags=tags)
    # tampas blindadas
    _cap(name + "_capT", 1, M, X, tags, leds)
    _cap(name + "_capB", -1, M, X, tags, leds)
    return body


def item(M, T="item"):
    cell(M, (T,), level=1.0, leds=4)
