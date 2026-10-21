"""F6 Forja de Projeteis (Slug Forge) 3x4 - o projetil da railgun Tupa (spec 2.0, factories F6).

ID novo rafaeltessaro.bs_factory_slug. Grade (vanilla factory_emp 3x4): maquina = fileiras 0-1 + [1,2];
ENTRADAS tristeel [0,2] (esquerda) e coil2 [2,2] (direita); SAIDA = a fileira de baixo inteira ([0,3,3,1]).
Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade = 1 quadro.

Cores: o spec pedia destaque violeta (palette.rail), mas o usuario mandou depois (USER_NOTES 2026-10-21, referencia
da Tupa) refazer a railgun em AZUL, com blindagem grafite, placas brancas grossas nas laterais, canal central azul
aceso e detalhes/molas LARANJA, e "o slug da Tupa acompanha a cor". A forja segue essa paleta nova com as MESMAS
cores da Tupa refeita (parts/bs_rail.py BLUE / ORANGE / ORANGE_P) e o slug novo de bs_shells2. Sem cobre (regra da
familia rail).

Maquinario (casca clara da familia + grafite e azul da Tupa; azul de forca baixa, so em fendas e frestas):
  * TREFILA DE HASTES (coluna esquerda, sobre a base de tristeel): janela alta com a haste de tungstenio subindo
    entre 3 pares de rolos (marcas correndo); no alto o braco de transferencia leva a haste cortada para o forno;
  * FORNO DE INDUCAO (meio de cima): tunel de 5 colares de bobina de grafite com frestas azuis, a haste dentro
    esquentando (laranja -> ouro-branco nas frestas), bochechas brancas dos lados;
  * PRENSA DE ARMADURA (meio): 2 mordentes brancos que fecham sobre a haste e cravam os colares EM (lampejo azul),
    MOLAS LARANJA atras de cada mordente (as molas da referencia);
  * BOBINADEIRA DE ARMADURAS (coluna direita, sobre a base de coil2): carretel de coil2 girando e o pente de
    colares de grafite com a linha azul, empurrados por uma mola laranja ate a prensa;
  * BERCO DE ACABAMENTO (celula [1,2]): o projetil pronto (haste clara, aletas, 4 colares azuis, ponta ouro-branca)
    esfria no berco e sai pela borda de baixo (3 setas azuis para a fileira de saida).
Animacao: 12 quadros x 0,25 s = 3,0 s = um projetil por volta (R07: F6 3,0 s): 0-3 a haste esquenta no forno
(o projetil anterior sai do berco em 1) | 4 desce para a prensa | 5 crava 2 colares (lampejo) | 6 avanca | 7 crava
os outros 2 | 8 abre | 9-10 desce ao berco de acabamento e esfria | 11 a haste nova entra no forno.
Teto: placas verdes; espinha central no estilo da Tupa (grafite com placas brancas grossas nas laterais, canal azul
fino aceso, aneis segmentados com pinos laranja); colunas com uma tampa por celula (capo com respiro em cima,
tampa octogonal do acionamento embaixo, travessa escura com fresta azul entre elas); celula [1,2] (maquina) com o
capuz do berco de acabamento (bochechas brancas + canal grafite com fresta azul, SEM seta); escotilhas em seta so
nas entradas e na saida.
"""

import math

import bs3d as B
import models as Mo
from parts import _bs2_fabricas_helpers as H

PART = {
    "id": "rafaeltessaro.bs_factory_slug",
    "kind": "factory",
    "size": [3, 4],
    "accent": "blue",
    "machine_frames": 12,
    "machine_interval": 0.25,
}

W, HH = PART["size"]
NF = PART["machine_frames"]
RAIL_BLUE = (0.026, 0.171, 1.0)          # azul eletrico da Tupa nova (parts/bs_rail.py BLUE, 45 115 255)
RAIL_ORANGE = (1.0, 0.42, 0.035)         # LED laranja de estado da Tupa nova (bs_rail.py ORANGE)
ORANGE_P = (0.60, 0.25, 0.020)           # tinta laranja-ouro das molas e pinos (bs_rail.py ORANGE_P refinado)
GRAPH = (0.055, 0.057, 0.063)            # grafite da blindagem (igual a parts/bs_rail.py)
FURN_Y0, FURN_Y1 = 1.12, 1.84            # tunel do forno
PRESS_Y = 0.76                           # linha dos mordentes
FIN_Y = -0.46                            # berco de acabamento
SLUG_S = 1.45                            # escala do projetil (0.65 x 0.10 quadro)

META_EXTRA = {
    "factory_code": "F6",
    "name_ptbr": "Forja de Projéteis",
    "grid": {"blocked": [[0, 0], [1, 0], [2, 0], [0, 1], [1, 1], [2, 1], [1, 2]],
             "inputs": {"tristeel": [0, 2, 1, 1], "coil2": [2, 2, 1, 1]}, "outputs": {"slug": [0, 3, 3, 1]}},
    "palette_note": "azul/laranja da Tupa nova (USER_NOTES: referencia da railgun) em vez do violeta do spec",
    "notes": ["12 quadros x 0,25 s = 3,0 s = um projetil por volta (R07)"],
}


def _state(phase):
    i = int(round(phase * NF)) % NF
    return {
        "i": i,
        "rod_y": {4: PRESS_Y + 0.05, 5: PRESS_Y + 0.05, 6: PRESS_Y - 0.06, 7: PRESS_Y - 0.06, 8: PRESS_Y - 0.06,
                  9: 0.05, 11: 1.70}.get(i, (FURN_Y0 + FURN_Y1) / 2 if i <= 3 else None),
        "heat": [0.25, 0.5, 0.8, 1.0, 0.85, 0.75, 0.65, 0.55, 0.45, 0.3, 0.1, 0.0][i],
        "collars": {5: 2, 6: 2, 7: 4, 8: 4, 9: 4}.get(i, 0),
        "jaws": {5: 1.0, 7: 1.0, 4: 0.3, 6: 0.3, 8: 0.2}.get(i, 0.0),
        "flash": i in (5, 7),
        "fin_y": {0: FIN_Y, 1: FIN_Y - 0.24, 10: FIN_Y, 11: FIN_Y}.get(i),
        "coil": 0.35 + 0.65 * [0.4, 0.6, 0.85, 1.0, 0.7, 0.5, 0.4, 0.35, 0.3, 0.3, 0.3, 0.35][i],
        "spin": i * 30.0,
        "xfer": {10: 0.0, 11: 1.0}.get(i),
    }


def _extra(st=None):
    k = st["coil"] if st else 0.5
    return {
        "blue_lo": B.mat_glow("f6_blue_lo", RAIL_BLUE, 0.45),
        "blue": B.mat_glow("f6_blue", RAIL_BLUE, 1.0),
        "blue_hi": B.mat_glow("f6_blue_hi", (0.13, 0.43, 1.0), 1.4),
        "coil": B.mat_glow("f6_coil", RAIL_BLUE, 0.35 + 0.9 * k),
        "orange": B.mat_paint("f6_orange", ORANGE_P, rough=0.36, metal=0.3, wear=0.0, grime=0.0, scale=6),
        "graph": B.mat_paint("f6_graph", GRAPH, rough=0.42, metal=0.45, wear=0.25, grime=0.05),
        "led_o": B.mat_glow("f6_led_o", RAIL_ORANGE, 0.8),
    }


def _M(M):
    """Os LEDs da familia (glow / glow_dim) viram o azul de forca baixa da forja (o azul do kit estoura)."""
    X = _extra()
    M = dict(M)
    M["glow"] = X["blue"]
    M["glow_dim"] = X["blue_lo"]
    return M


# ============================================================================ piso
def floor(M, T="floor"):
    M = _M(M)
    machine = {(i, j) for i in range(3) for j in range(2)} | {(1, 2)}
    pads = {(0, 2): 90, (2, 2): 90, (1, 3): (270, 90), (0, 3): None, (2, 3): None}
    H.floor_grid(M, W, HH, machine, pads, T=T, rail_rows=(3,))


# ============================================================================ maquina
COLW = [(-1.40, 1.80), (-1.30, 1.90), (-0.70, 1.90), (-0.62, 1.82), (-0.62, 0.40), (-0.70, 0.32), (-1.30, 0.32),
        (-1.40, 0.42)]
BLADE = [(-1.40, 0.06), (-0.70, 0.06), (-0.62, 0.14), (-0.62, 0.24), (-1.40, 0.24)]


def _column(prefix, sx, M, X, tags, hole):
    f = H.flip(sx)
    K, A, S, KM = M["core"], M["armor"], M["steel"], M["core_mid"]
    ca, cp = B.shard(prefix, f(COLW), 0.0, 0.40, A, slope=0.06, groove=0.028, panel_h=0.028, tags=tags)
    hole = f(hole)
    H.bezel(prefix + "_win", hole, B.offset_poly(hole, 0.022), 0.16, 0.40, M, tags, (ca, cp))
    ba, bp = B.shard(prefix + "_bl", f(BLADE), 0.0, 0.26, A, slope=0.035, groove=0.016, panel_h=0.02, tags=tags)
    H.ledslot(prefix + "_in", sx * 1.0, 0.15, 0.30, 0.06, 0.10, 0, M, tags, [ba, bp], vertical=False)
    for k in range(3):
        H.chevron(f"{prefix}_inchv{k}", sx * (0.90 + k * 0.10), 0.15, 90, X["blue_lo"], tags, z=0.108, s=0.38)
    H.ledslot(prefix + "_sl", sx * 1.335, 1.10, 0.034, 0.36, 0.34, 4, M, tags, [ca, cp], pw=0.016,
              pips=[X["blue_lo"], X["blue_lo"], None, X["led_o"]])
    B.bolts(prefix + "_b", [(sx * 1.33, 1.84), (sx * 0.69, 1.84), (sx * 1.33, 0.38)], 0.43, 0.017, S, tags=tags)
    return ca, cp


MILL_HOLE = [(-1.20, 0.44), (-0.82, 0.44), (-0.82, 1.76), (-1.20, 1.76)]


def _well(prefix, x, M, X, tags, rails, slits, y0=0.47, y1=1.73, dashes=None):
    """Fundo do gabinete (janela da coluna): piso grafite (core_mid) logo acima do leito preto do bezel, trilhos-guia
    de aco ao longo de y, travessas nas pontas e frestas azuis fracas num rebaixo (o poco deixa de ser um buraco
    preto com rolos flutuando). dashes = [(y, comprimento)]: a luz azul so em trechos curtos da fresta escura (a
    fresta inteira acesa passava do orcamento de area acesa, STYLE 1.6)."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    yc, L = (y0 + y1) / 2, y1 - y0
    B.box(prefix + "_floor", x, yc, 0.36, L + 0.02, 0.16, 0.172, KM, bevel=0.0, tags=tags)
    for k, dx in enumerate(rails):
        B.box(f"{prefix}_rail{k}", x + dx, yc, 0.022, L, 0.172, 0.198, S, bevel=0.004, tags=tags)
    for k, yy in enumerate((y0 + 0.03, y1 - 0.03)):
        B.box(f"{prefix}_tie{k}", x, yy, 0.34, 0.035, 0.172, 0.205, KM, bevel=0.005, tags=tags)
    for k, dx in enumerate(slits):
        B.box(f"{prefix}_sk{k}", x + dx, yc, 0.026, L - 0.12, 0.170, 0.176, K, bevel=0.0, tags=tags)
        for j, (yy, ll) in enumerate(dashes or [(yc, L - 0.16)]):
            B.box(f"{prefix}_sg{k}{j}", x + dx, yy, 0.010, ll, 0.176, 0.179, X["blue_lo"], bevel=0.0, tags=tags)


def _mill(M, Xm, X, tags, st):
    """Trefila de hastes: a haste sobe entre 3 pares de rolos de grafite (marcas correndo)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    _column("ml", -1, M, X, tags, MILL_HOLE)
    x = -1.01
    # luz so nos vaos entre os pares de rolos (y 0,64 / 1,10 / 1,56)
    _well("ml_w", x, M, X, tags, rails=(-0.165, 0.165), slits=(-0.048, 0.048),
          dashes=[(0.87, 0.20), (1.33, 0.20)])
    B.cyl("ml_rod", x, 1.10, 0.24, 0.024, 1.28, Xm["tungsten"], axis="Y", verts=8, bevel=0.0, tags=tags)
    for k, y in enumerate((0.64, 1.10, 1.56)):
        for sx in (-1, 1):
            B.cyl(f"ml_r{k}{sx}", x + sx * 0.09, y, 0.24, 0.055, 0.16, X["graph"], axis="Y", verts=12, bevel=0.004,
                  tags=tags)
            for j in range(2):
                yy = y - 0.06 + ((j * 0.06 + st["i"] * 0.025) % 0.12)
                B.cyl(f"ml_m{k}{sx}{j}", x + sx * 0.09, yy, 0.24, 0.057, 0.008, KM, axis="Y", verts=12, bevel=0.0,
                      tags=tags)
            B.box(f"ml_ax{k}{sx}", x + sx * 0.155, y, 0.03, 0.05, 0.20, 0.26, S, bevel=0.004, tags=tags)
    # barra de tristeel entrando por baixo
    B.box("ml_bar", x, 0.36, 0.07, 0.12, 0.16, 0.24, Xm["tristeel"], bevel=0.008, tags=tags)
    # braco de transferencia no alto (leva a haste cortada para o forno no quadro 11)
    B.box("ml_xrail", -0.55, 1.86, 0.92, 0.035, 0.40, 0.44, S, bevel=0.006, tags=tags)
    t = st["xfer"]
    ax = -1.01 + (0.0 - (-1.01)) * (t if t is not None else 0.0)
    B.box("ml_xcar", ax, 1.86, 0.12, 0.08, 0.44, 0.50, AM, bevel=0.008, tags=tags)
    B.box("ml_xled", ax, 1.86, 0.05, 0.014, 0.50, 0.505, X["blue_lo"], bevel=0.0, tags=tags)


ARM_HOLE = [(-1.20, 0.44), (-0.82, 0.44), (-0.82, 1.76), (-1.20, 1.76)]


def _winder(M, Xm, X, tags, st):
    """Bobinadeira de armaduras: carretel de coil2 girando no alto, pente de colares com a mola laranja."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    _column("wd", 1, M, X, tags, ARM_HOLE)
    x = 1.01
    # luz em 3 trechos: ao lado do pente de colares, da mola e do carretel
    _well("wd_w", x, M, X, tags, rails=(-0.115, 0.115), slits=(-0.158, 0.158),
          dashes=[(0.70, 0.16), (1.18, 0.14), (1.56, 0.14)])
    # carretel (disco escuro com fio azul-grafite) girando
    B.cyl("wd_spool", x, 1.52, 0.20, 0.15, 0.06, X["graph"], axis="Z", verts=16, bevel=0.004, tags=tags)
    B.torus("wd_wire", x, 1.52, 0.26, 0.11, 0.022, B.mat_metal("f6_wire", (0.16, 0.22, 0.32), rough=0.3, metal=0.9),
            tags=tags)
    H.rotor("wd_rot", x, 1.52, 0.27, 0.16, -st["spin"], M, tags, blades=3, w=0.02)
    # pente de colares (aneis de grafite com a linha azul) empilhados ao longo de y, empurrados pela mola laranja
    for k in range(5):
        y = 0.62 + k * 0.085
        B.cyl(f"wd_col{k}", x, y, 0.24, 0.07, 0.05, X["graph"], axis="Y", verts=8, bevel=0.004, tags=tags)
        B.box(f"wd_cl{k}", x, y, 0.05, 0.012, 0.31, 0.315, X["blue_lo"], bevel=0.0, tags=tags)
    spring_top = 1.32 - 0.03 * (st["i"] % 2)
    n = 6
    for k in range(n):
        y = 1.05 + (spring_top - 1.05) * (k + 0.5) / n
        B.cyl(f"wd_sp{k}", x, y, 0.24, 0.06, 0.022, X["orange"], axis="Y", verts=8, bevel=0.0, tags=tags)
    B.box("wd_spcore", x, (1.05 + spring_top) / 2, 0.03, spring_top - 1.05, 0.20, 0.26, KM, bevel=0.0, tags=tags)
    # empurrador ate a prensa (barra de aco saindo da coluna na altura dos mordentes)
    B.box("wd_push", 0.56, PRESS_Y, 0.20, 0.05, 0.18, 0.24, S, bevel=0.006, tags=tags)


def _furnace(M, Xm, X, tags, st):
    """Forno de inducao: tunel de 5 colares de grafite com frestas azuis; a haste dentro esquenta."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    y0, y1 = FURN_Y0, FURN_Y1
    yc = (y0 + y1) / 2
    B.box("fu_bed", 0, yc, 0.36, y1 - y0, 0.0, 0.10, K, bevel=0.01, tags=tags)
    # bochechas brancas grossas dos lados (as placas da referencia) com fendas de pips
    cheek = [(-0.47, y1), (-0.30, y1), (-0.25, y1 - 0.05), (-0.25, y0 + 0.05), (-0.30, y0), (-0.47, y0)]
    for sx in (-1, 1):
        ca, cp = B.shard(f"fu_ck{sx}", H.flip(sx)(cheek), 0.0, 0.44, A, slope=0.05, groove=0.022, panel_h=0.026,
                         tags=tags)
        H.ledslot(f"fu_sl{sx}", sx * 0.37, yc, 0.034, 0.40, 0.38, 4, M, tags, [ca, cp], pw=0.016,
                  pips=[X["blue"] if st["heat"] > 0.7 else X["blue_lo"]] * 3 + [X["led_o"]])
        B.bolts(f"fu_b{sx}", [(sx * 0.40, y1 - 0.06), (sx * 0.40, y0 + 0.06)], 0.45, 0.016, S, tags=tags)
    # haste dentro do tunel (a cor do calor e da propria haste; aparece nas frestas)
    if st["rod_y"] is not None and st["rod_y"] > 1.0:
        H.mini_slug("fu_rod", 0, st["rod_y"], 0.20, M, Xm, tags, s=SLUG_S, heat=st["heat"], rod_only=True)
    n = 5
    pitch = (y1 - y0) / n
    for k in range(n):
        y = y0 + (k + 0.5) * pitch
        B.cyl(f"fu_col{k}", 0, y, 0.22, 0.15, pitch * 0.66, X["graph"], axis="Y", verts=8, bevel=0.008, tags=tags)
        B.cyl(f"fu_colr{k}", 0, y, 0.22, 0.155, 0.02, S, axis="Y", verts=8, bevel=0.004, tags=tags)
        # fenda azul no topo de cada colar (a bobina de inducao)
        B.box(f"fu_slot{k}", 0, y, 0.20, 0.03, 0.22 + 0.148, 0.22 + 0.152, M["black"], bevel=0.0, tags=tags)
        B.box(f"fu_glow{k}", 0, y, 0.15, 0.012, 0.22 + 0.152, 0.22 + 0.156, X["coil"], bevel=0.0, tags=tags)
        if k < n - 1:
            # pino laranja na emenda de cada colar (os detalhes laranja da referencia)
            for sx in (-1, 1):
                B.box(f"fu_pin{k}{sx}", sx * 0.13, y + pitch / 2, 0.03, 0.02, 0.30, 0.33, X["orange"], bevel=0.004,
                      tags=tags)


def _press(M, Xm, X, tags, st):
    """Prensa de armadura: 2 mordentes brancos que fecham sobre a haste, molas laranja atras de cada um e os
    batentes brancos do quadro; lampejo azul ao cravar."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    y = PRESS_Y
    B.box("pr_bed", 0, y, 0.94, 0.40, 0.0, 0.08, KM, bevel=0.01, tags=tags)
    B.box("pr_chan", 0, y, 0.10, 0.40, 0.08, 0.085, K, bevel=0.0, tags=tags)
    B.box("pr_chang", 0, y, 0.012, 0.36, 0.085, 0.088, X["blue_lo"], bevel=0.0, tags=tags)
    g = 0.15 - 0.10 * st["jaws"]
    for sx in (-1, 1):
        jaw = [(0.0, -0.15), (0.10, -0.15), (0.16, -0.09), (0.16, 0.09), (0.10, 0.15), (0.0, 0.15), (-0.035, 0.07),
               (-0.035, -0.07)]
        jaw = [(sx * (g + x), y + yy) for x, yy in jaw]
        jaw = jaw if sx > 0 else list(reversed(jaw))
        ja, jp = B.shard(f"pr_jaw{sx}", jaw, 0.08, 0.38, A, slope=0.03, groove=0.012, panel_h=0.02, tags=tags)
        if jp is not None:
            B.cut(jp, [B.box(f"pr_jpl{sx}", sx * (g + 0.08), y, 0.02, 0.22, 0.36, 0.8, K, bevel=0.0)])
        # mola laranja atras do mordente (entre ele e o batente)
        x0, x1 = sx * (g + 0.16), sx * 0.39
        n = 5
        for k in range(n):
            xx = x0 + (x1 - x0) * (k + 0.5) / n
            B.cyl(f"pr_sp{sx}{k}", xx, y, 0.20, 0.06, abs(x1 - x0) / n * 0.55, X["orange"], axis="X", verts=8,
                  bevel=0.0, tags=tags)
        B.cyl(f"pr_spc{sx}", (x0 + x1) / 2, y, 0.20, 0.022, abs(x1 - x0), KM, axis="X", verts=8, bevel=0.0,
              tags=tags)
        # batente branco do quadro com fenda azul (pisca ao cravar)
        st_ = H.flip(-sx)([(0.39, y - 0.19), (0.47, y - 0.19), (0.47, y + 0.19), (0.39, y + 0.19)])
        sa, sp = B.shard(f"pr_stop{sx}", st_, 0.0, 0.40, A, slope=0.025, groove=0.012, panel_h=0.016, tags=tags)
        H.ledslot(f"pr_sl{sx}", sx * 0.43, y, 0.03, 0.22, 0.36, 3, M, tags, [sa, sp], pw=0.014,
                  pip_mat=X["blue"] if st["flash"] else X["blue_lo"])
    if st["rod_y"] is not None and 0.3 < st["rod_y"] < 1.0:
        H.mini_slug("pr_slug", 0, st["rod_y"], 0.13, M, Xm, tags, s=SLUG_S, collars=st["collars"],
                    heat=st["heat"] * 0.6)
    if st["flash"]:
        fl = B.mat_glow("f6_flash", RAIL_BLUE, 1.4)
        for k, dy in enumerate((-0.05, 0.05)):
            B.box(f"pr_fl{k}", 0, y + dy, 0.13, 0.012, 0.40, 0.41, fl, bevel=0.0, tags=tags)
    for k, yy in enumerate((y + 0.27, y - 0.32)):
        B.box(f"pr_g{k}", 0, yy, 0.20, 0.10, 0.0, 0.16, KM, bevel=0.01, tags=tags)
        B.box(f"pr_gk{k}", 0, yy, 0.06, 0.10, 0.16, 0.165, K, bevel=0.0, tags=tags)
        B.box(f"pr_gl{k}", 0, yy, 0.036, 0.012, 0.165, 0.168, X["blue_lo"], bevel=0.0, tags=tags)


FHOOD = [(-0.47, -0.08), (-0.30, -0.08), (-0.22, -0.16), (-0.22, -0.76), (-0.30, -0.84), (-0.47, -0.84)]


def _finish(M, Xm, X, tags, st):
    """Berco de acabamento (celula [1,2]): capuzes claros com respiros, trilho escuro com LEDs azuis."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.plate("fn_block", B.rpoly(0, -0.5, 0.94, 0.94, 0, chamfer=0.14), 0.0, 0.035, K, slope=0.012, tags=tags)
    B.box("fn_tr", 0, -0.48, 0.30, 0.86, 0.03, 0.07, KM, bevel=0.008, tags=tags)
    B.box("fn_well", 0, -0.48, 0.20, 0.82, 0.07, 0.074, KM, bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"fn_wk{sx}", sx * 0.075, -0.48, 0.024, 0.74, 0.072, 0.076, K, bevel=0.0, tags=tags)
        B.box(f"fn_wg{sx}", sx * 0.075, -0.30, 0.010, 0.30, 0.076, 0.079, X["blue_lo"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"fn_rail{sx}", sx * 0.13, -0.48, 0.02, 0.84, 0.04, 0.10, S, bevel=0.003, tags=tags)
        ha, hp = B.shard(f"fn_h{sx}", H.flip(sx)(FHOOD), 0.0, 0.30, A, slope=0.045, groove=0.02, panel_h=0.022,
                         tags=tags)
        H.vent(f"fn_v{sx}", sx * 0.345, -0.30, 0.12, 0.24, 0.25, 0.30, M, tags, n=4, targets=[ha, hp])
        H.ledslot(f"fn_sl{sx}", sx * 0.345, -0.64, 0.034, 0.20, 0.25, 3, M, tags, [ha, hp], pw=0.016,
                  pips=[X["blue_lo"], None, X["led_o"]])
    for k, (x, ang) in enumerate(((-0.10, 240), (0.0, 270), (0.10, 300))):
        H.chevron(f"fn_ar{k}", x, -0.94, ang, X["blue_lo"], tags, z=0.074, s=0.45)
    if st["fin_y"] is not None:
        H.mini_slug("fn_slug", 0, st["fin_y"], 0.08, M, Xm, tags, s=SLUG_S, collars=4,
                    heat=0.15 if st["i"] == 10 else 0.0)
    if st["rod_y"] is not None and st["rod_y"] < 0.3:
        H.mini_slug("fn_slug2", 0, st["rod_y"], 0.08, M, Xm, tags, s=SLUG_S, collars=4, heat=0.25)


def machine(M, T="machine", phase=0.0):
    tags = (T,)
    M = _M(M)
    Xm = H.X(M)
    st = _state(phase)
    X = _extra(st)
    B.plate("mc_bed", B.rpoly(0, 1.0, 2.90, 1.88, 0, chamfer=0.10), 0.0, 0.05, M["core"], slope=0.01, tags=tags)
    _finish(M, Xm, X, tags, st)
    _press(M, Xm, X, tags, st)
    _furnace(M, Xm, X, tags, st)
    _mill(M, Xm, X, tags, st)
    _winder(M, Xm, X, tags, st)


# ============================================================================ teto
def roof(M, T="roof"):
    tags = (T,)
    M = _M(M)
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    X = _extra()
    deck = H.roof_deck(M, W, HH, skip={(1, 0), (1, 1)}, T=T)
    H.roof_hatch("rf_in0", M, -1.0, -0.5, 90, deck[(0, 2)], T=T)
    H.roof_hatch("rf_in1", M, 1.0, -0.5, 90, deck[(2, 2)], T=T)
    for i in range(3):
        cx, cy = H.cell_xy(W, HH, i, 3)
        H.roof_hatch(f"rf_out{i}", M, cx, cy, 270, deck[(i, 3)], T=T, s=0.9)
    # espinha central estilo Tupa: base grafite, placas brancas grossas nas laterais, canal azul aceso no meio,
    # aneis segmentados com pinos laranja
    base = [(-0.48, 1.92), (0.48, 1.92), (0.50, 1.90), (0.50, 0.10), (0.48, 0.08), (-0.48, 0.08), (-0.50, 0.10),
            (-0.50, 1.90)]
    B.plate("sp_core", base, 0.0, 0.12, K, slope=0.02, tags=tags)
    spine = [(-0.24, 1.88), (0.24, 1.88), (0.28, 1.84), (0.28, 0.30), (0.12, 0.12), (-0.12, 0.12), (-0.28, 0.30),
             (-0.28, 1.84)]
    sa, sp = B.shard("sp_graph", spine, 0.10, 0.32, X["graph"], slope=0.04, groove=0.018, panel_h=0.02, tags=tags)
    ch = [(-0.045, 1.80), (0.045, 1.80), (0.045, 0.34), (0.0, 0.26), (-0.045, 0.34)]
    for q, t in enumerate((sa, sp)):
        if t is not None:
            B.cut(t, [B.loft(f"sp_chc{q}", ch, ch, 0.24, 0.8, K, bevel=0.0)])
    B.loft("sp_chbed", ch, ch, 0.235, 0.245, M["black"], bevel=0.0, tags=tags)
    inner = [(-0.022, 1.76), (0.022, 1.76), (0.022, 0.36), (0.0, 0.31), (-0.022, 0.36)]
    B.loft("sp_chglow", inner, inner, 0.245, 0.25, X["blue"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        plate = H.flip(sx)([(-0.47, 1.86), (-0.31, 1.86), (-0.29, 1.82), (-0.29, 0.40), (-0.35, 0.26),
                            (-0.47, 0.26)])
        pa, pp = B.shard(f"sp_wp{sx}", plate, 0.08, 0.40, A, slope=0.05, groove=0.022, panel_h=0.026, tags=tags)
        for k, y in enumerate((1.45, 0.75)):
            if pp is not None:
                B.cut(pp, [B.box(f"sp_wpl{sx}{k}", sx * 0.39, y, 0.20, 0.022, 0.38, 0.8, K, bevel=0.0)])
        H.ledslot(f"sp_wsl{sx}", sx * 0.39, 1.10, 0.034, 0.30, 0.36, 3, M, tags, [pa, pp], pw=0.016,
                  pip_mat=X["blue_lo"])
    for k, y in enumerate((1.62, 1.22, 0.82, 0.48)):
        ring = [(-0.27, y - 0.045), (0.27, y - 0.045), (0.29, y - 0.025), (0.29, y + 0.025), (0.27, y + 0.045),
                (-0.27, y + 0.045), (-0.29, y + 0.025), (-0.29, y - 0.025)]
        rg = B.plate(f"sp_ring{k}", ring, 0.30, 0.36, KM, slope=0.012, tags=tags)
        B.cut(rg, [B.box(f"sp_rgc{k}", 0, y, 0.10, 0.10, 0.2, 0.8, K, bevel=0.0)])
        for sx in (-1, 1):
            B.box(f"sp_pin{k}{sx}", sx * 0.20, y, 0.04, 0.03, 0.36, 0.38, X["orange"], bevel=0.004, tags=tags)
    # colunas (trefila / bobinadeira), uma tampa por celula sobre a placa verde (a cada ~0,3-0,5 quadro uma quebra,
    # STYLE 1.8): em cima o capo do motor com respiro, linha de painel e fenda de LEDs; embaixo a tampa octogonal do
    # acionamento (coroa clara de 6 segmentos sobre base escura, cubo grafite com LED azul e pinos laranja); entre
    # as duas, a travessa escura da coluna com a fresta azul
    for sx in (-1, 1):
        cx = sx * 1.0
        hood = B.rpoly(cx, 1.50, 0.66, 0.64, 0, chamfer=0.11)
        B.plate(f"rf_ck{sx}", B.offset_poly(hood, -0.03), 0.06, 0.10, K, slope=0.01, tags=tags)
        ca, cp = B.shard(f"rf_cov{sx}", hood, 0.09, 0.26, A, slope=0.05, groove=0.022, panel_h=0.024, tags=tags)
        H.vent(f"rf_cv{sx}", cx, 1.645, 0.40, 0.20, 0.21, 0.26, M, tags, n=4, targets=[ca, cp])
        H.groove(f"rf_cpl{sx}", cx, 1.475, 0.50, 0.026, 0.26, (ca, cp), M, tags, depth=0.06)
        H.ledslot(f"rf_cs{sx}", cx, 1.33, 0.34, 0.034, 0.21, 4, M, tags, [ca, cp], vertical=False, pw=0.016,
                  pips=[X["blue_lo"], None, X["blue_lo"], X["led_o"]])
        B.bolts(f"rf_cb{sx}", [(cx - 0.25, 1.235), (cx + 0.25, 1.235)], 0.26, 0.016, S, tags=tags)
        oc = (cx, 0.50)
        B.plate(f"rf_dk{sx}", H.octo(oc[0], oc[1], 0.31), 0.04, 0.13, K, slope=0.015, tags=tags)
        for k in range(6):
            a = 60 * k
            seg = [(oc[0] + math.cos(math.radians(a + d)) * r, oc[1] + math.sin(math.radians(a + d)) * r)
                   for r, d in ((0.17, -22), (0.285, -22), (0.285, 0), (0.285, 22), (0.17, 22), (0.17, 0))]
            B.shard(f"rf_dseg{sx}{k}", seg, 0.12, 0.22, A, slope=0.02, groove=0.01, panel_h=0.012, tags=tags)
        B.plate(f"rf_dhub{sx}", H.octo(oc[0], oc[1], 0.12), 0.12, 0.20, X["graph"], slope=0.015, tags=tags)
        B.cyl(f"rf_dled{sx}", oc[0], oc[1], 0.20, 0.032, 0.008, X["blue_lo"], axis="Z", verts=8, bevel=0.0,
              tags=tags)
        for k in range(3):
            a = 90 + 120 * k
            B.rbox(f"rf_dpin{sx}{k}", oc[0] + math.cos(math.radians(a)) * 0.085,
                   oc[1] + math.sin(math.radians(a)) * 0.085, 0.034, 0.026, 0.20, 0.215, X["orange"], rot=a,
                   bevel=0.004, tags=tags)
        B.box(f"rf_cr{sx}", cx, 0.995, 0.20, 0.40, 0.06, 0.14, KM, bevel=0.012, tags=tags)
        B.box(f"rf_crk{sx}", cx, 0.995, 0.05, 0.28, 0.14, 0.145, K, bevel=0.0, tags=tags)
        B.box(f"rf_crg{sx}", cx, 0.995, 0.016, 0.24, 0.145, 0.149, X["blue_lo"], bevel=0.0, tags=tags)
        B.bolts(f"rf_crb{sx}", [(cx - 0.065, 0.86), (cx + 0.065, 1.13)], 0.14, 0.014, S, tags=tags)
    # celula [1,2] (maquina, bloqueada): capuz do berco de acabamento, a continuacao da espinha da Tupa - bochechas
    # brancas com fendas de LED, canal grafite com a fresta azul do projetil esfriando e pinos laranja. Sem seta:
    # so as entradas e as saidas levam escotilha em seta.
    B.plate("rf_fb", B.rpoly(0, -0.5, 0.66, 0.86, 0, chamfer=0.12), 0.04, 0.13, K, slope=0.015, tags=tags)
    cheek = [(-0.31, -0.12), (-0.17, -0.12), (-0.13, -0.16), (-0.13, -0.84), (-0.17, -0.88), (-0.31, -0.88)]
    for sx in (-1, 1):
        ha, hp = B.shard(f"rf_fh{sx}", H.flip(sx)(cheek), 0.10, 0.27, A, slope=0.035, groove=0.016, panel_h=0.018,
                         tags=tags)
        H.groove(f"rf_fpl{sx}", sx * 0.22, -0.37, 0.12, 0.026, 0.27, (ha, hp), M, tags, depth=0.06)
        H.ledslot(f"rf_fs{sx}", sx * 0.22, -0.63, 0.034, 0.30, 0.20, 3, M, tags, [ha, hp], pw=0.016,
                  pips=[X["blue_lo"], X["blue_lo"], X["led_o"]])
    ch = B.plate("rf_fch", B.rpoly(0, -0.5, 0.22, 0.80, 0, chamfer=0.04), 0.10, 0.21, X["graph"], slope=0.02,
                 tags=tags)
    B.cut(ch, [B.box("rf_fchc", 0, -0.5, 0.05, 0.66, 0.18, 0.6, K, bevel=0.0)])
    B.box("rf_fchb", 0, -0.5, 0.05, 0.66, 0.175, 0.18, K, bevel=0.0, tags=tags)
    B.box("rf_fchg", 0, -0.5, 0.022, 0.62, 0.18, 0.185, X["blue"], bevel=0.0, tags=tags)
    for k, y in enumerate((-0.20, -0.80)):
        for sx in (-1, 1):
            B.box(f"rf_fpin{k}{sx}", sx * 0.07, y, 0.04, 0.03, 0.21, 0.225, X["orange"], bevel=0.004, tags=tags)
    H.roof_unpaint(T)
