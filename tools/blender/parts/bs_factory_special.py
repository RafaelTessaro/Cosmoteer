"""F2 Fabrica de Municao Especial (Special Ammunition Factory) 4x3 - carregadores AP / SAP / AC / FRAG.

Spec 2.0 factories F2: o ID continua rafaeltessaro.bs_factory_mag_ap (a 1.x Prensa AP vira a F2), mas a arte nova
fica nesta pasta (art3d/bs_factory_special); a arte 3x3 da 1.x (parts/bs_factory_mag_ap.py) fica intacta ate o
gerador 2.0 apontar a F2 para ca (como a Boiuna AC: pasta bs_boiuna_ac, id bs_nuke_howitzer).
Grade (vanilla factory_mine 4x3): maquina = fileira de cima + [1,1], [2,1]; ENTRADAS enxofre [0,1] (esquerda) e
tristeel [3,1] (direita); SAIDAS na fileira de baixo, uma por receita: AP [0,2], SAP [1,2], AC [2,2], FRAG [3,2]
(seletor bs_ammo_type 1..4). Cada base de saida leva no piso a pastilha pintada da sua municao e o teto leva o
encaixe da placa de modo (rect_centre [2.0, 0.5], 0.8 quadro: placa_ap/sap/ac/frag.png de bs_placas).
Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade = 1 quadro.

Maquinario (familia das armas, modelo herdado da Prensa AP 1.x):
  * MESA INDEXADORA no centro das 2 celulas do meio: 4 paletes claros em cunha girando no sentido horario:
    W carga (bandeja vazia + dose de enxofre) -> N prensa -> E inspecao -> S descarga (para o distribuidor);
  * PRENSA DE CONFORMAR em cima da mesa: bochechas em garra, cilindro hidraulico e matriz em cunha que crava as
    municoes/pontas no ninho N (faiscas laranja e brilho quente; pontas em brasa na volta);
  * MISTURADOR DE ENXOFRE no canto de cima a esquerda (sobre a base de enxofre): janela em degrau com o tambor,
    as pas girando e o monte de enxofre; calha da base de entrada (seta para cima);
  * FORJA DE PONTAS no canto de cima a direita (sobre a base de tristeel): pontas de tristeel andando ate a
    bobina de inducao (brilho frio no tristeel); calha da base de entrada;
  * CENTRAL HIDRAULICA (2 pistoes alternados) entre o misturador e a prensa; PORTA-FERRAMENTAS entre a prensa e a
    forja: 4 matrizes com a faixa de cada municao (AP branco-azulado, SAP laranja, AC carmim + ouro, FRAG
    verde-agua) - o maquinario e o mesmo nos 4 modos, quem diz o modo e a placa do teto;
  * DOSADOR de bandejas a esquerda da mesa (pilha de bandejas vazias numa janela, bico de enxofre no ninho W) e
    SCANNER de inspecao a direita (olho frio); DISTRIBUIDOR embaixo da mesa: trilho escuro com 4 setas de LED na
    cor de cada municao apontando para as 4 bases de saida.
Animacao: 10 quadros x 0,1 s: 0 repouso (= sprite desligado) | 1 a bandeja entra em W, a matriz desce |
2 crava (faiscas) | 3 segura, o enxofre cai na bandeja | 4 volta (pontas em brasa) | 5 o carregador pronto sai de
S para o distribuidor | 6-9 a mesa gira 18 graus por quadro (o quadro 0 fecha os 90 graus).
Teto: placas verdes com escotilhas em seta (entradas para cima, saidas para baixo com a pastilha da municao),
coroa blindada sem pintura sobre a prensa (espinha em cunha com o encaixe da placa de modo, garras, laminas) e
o colar octogonal sobre a mesa; respiros e caixas de juncao nos cantos.
"""

import math
import random

import bs3d as B
import models as Mo
from parts import _bs2_fabricas_helpers as H

PART = {
    "id": "rafaeltessaro.bs_factory_mag_ap",
    "kind": "factory",
    "size": [4, 3],
    "accent": "amber",
    "machine_frames": 10,
    "machine_interval": 0.1,
}

W, HH = PART["size"]
NF = PART["machine_frames"]
TCX, TCY = 0.0, 0.0        # centro da mesa indexadora
NEST_R = 0.27
PALLET = [(0.12, -0.10), (0.385, -0.135), (0.42, -0.10), (0.42, 0.10), (0.385, 0.135), (0.12, 0.10)]
DIE_OUT, DIE_IN = 0.60, 0.395   # frente da matriz recolhida / cravando (y)
MAG_S = 0.68                    # carregador no palete (0.20 x 0.16)
WIN_X = 1.68                    # centro (|x|) das janelas das cascas dos cantos
WIN_Y = 1.13
OUTS = {(0, 2): "ap", (1, 2): "sap", (2, 2): "ac", (3, 2): "frag"}
PLATE_C = (0.0, 1.0)            # rect_centre [2.0, 0.5] em coordenadas do modelo

META_EXTRA = {
    "factory_code": "F2",
    "name_ptbr": "Fábrica de Munição Especial",
    "art3d_dir": "bs_factory_special",
    "grid": {"blocked": [[0, 0], [1, 0], [2, 0], [3, 0], [1, 1], [2, 1]],
             "inputs": {"sulfur": [0, 1, 1, 1], "tristeel": [3, 1, 1, 1]},
             "outputs": {"ap": [0, 2, 1, 1], "sap": [1, 2, 1, 1], "ac": [2, 2, 1, 1], "frag": [3, 2, 1, 1]}},
    "mode_plate": {"rect_centre": [2.0, 0.5], "size": 0.8, "modes": ["ap", "sap", "ac", "frag"],
                   "toggle": "bs_ammo_type", "values": [1, 2, 3, 4], "files": "placa_<modo>.png (art3d/bs_placas)",
                   "game_layer": "roof_doodads"},
    "notes": ["id da peca = rafaeltessaro.bs_factory_mag_ap (ID mantido); arte 2.0 nesta pasta",
              "o maquinario e o mesmo nos 4 modos; pastilhas pintadas nas bases de saida e placa de modo no teto",
              "LIGACAO: a pasta antiga art3d/bs_factory_mag_ap (3x3, 1.x) tem o mesmo id; o bsgen deve ler esta pasta "
              "(meta.art3d_dir) e o art3d_owner_map do spec deve trocar F2 'bs_factory_mag_ap' por "
              "'bs_factory_special' (ou aposentar a pasta antiga), senao duas pastas reivindicam o mesmo id"],
}


# ============================================================================ utilidades
def _extra():
    return {
        "silver_r": B.mat_metal("silver_r", (0.80, 0.82, 0.86), rough=0.34, metal=0.85),
        "glint": B.mat_glow("glint", (0.70, 0.86, 1.0), 4.0),
        "hot": B.mat_glow("hot", (1.0, 0.28, 0.035), 1.3),
        "spark": B.mat_glow("spark", (1.0, 0.40, 0.08), 1.9),
    }


def _state(phase):
    i = int(round(phase * NF)) % NF
    return {
        "i": i,
        "die": {1: 0.5, 2: 1.0, 3: 1.0, 4: 0.45}.get(i, 0.0),
        "spark": {2: 1.0, 3: 0.45}.get(i, 0.0),
        "ember": i == 4,
    }


def _rotation(i):
    """Giro da mesa (graus) nos quadros 6-9: 4 passos que fecham 90 graus no quadro 0 seguinte."""
    return {6: 18.0, 7: 36.0, 8: 54.0, 9: 72.0}.get(i, 0.0)


def _nests(i):
    """Conteudo de cada estacao (angulo em graus -> (tipo, deslize radial, enxofre)).
    tipos: "tray" bandeja vazia | "fill" bandeja com enxofre | "mag" carregador pronto (faixa neutra de aco: a cor
    da municao depende do modo e fica na placa/pastilhas) | None."""
    if i == 0:
        return {180: (None, 0.0), 90: ("fill", 0.0), 0: ("mag", 0.0), 270: ("mag", 0.0)}
    if i == 1:
        return {180: ("tray", 0.05), 90: ("fill", 0.0), 0: ("mag", 0.0), 270: ("mag", 0.0)}
    if i in (2, 3, 4):
        return {180: ("tray" if i == 2 else "fill", 0.0), 90: ("mag" if i >= 3 else "fill", 0.0), 0: ("mag", 0.0),
                270: ("mag", 0.0)}
    if i == 5:
        return {180: ("fill", 0.0), 90: ("mag", 0.0), 0: ("mag", 0.0), 270: ("mag", 0.10)}
    return {180: ("fill", 0.0), 90: ("mag", 0.0), 0: ("mag", 0.0), 270: (None, 0.0)}


# ============================================================================ piso
def floor(M, T="floor"):
    machine = {(0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (2, 1)}
    pads = {(0, 1): 90, (3, 1): 90, (0, 2): (270, 90), (1, 2): (270, 90), (2, 2): (270, 90), (3, 2): (270, 90)}
    H.floor_grid(M, W, HH, machine, pads, T=T, chips=OUTS, rail_rows=(2,))


# ============================================================================ maquina
def _tray(name, M, Xm, tags, kind, x, y, rz, s, z=0.0):
    """Bandeja de carregador vazia (so a bandeja escura e as laterais claras) com ou sem a dose de enxofre."""
    before = H.snapshot()
    K, A = M["core"], M["armor"]
    B.box(name + "_t", 0, -0.01, 0.27, 0.19, 0.0, 0.045, K, bevel=0.006, tags=tags)
    side = [(0.098, -0.105), (0.15, -0.105), (0.15, 0.045), (0.12, 0.085), (0.098, 0.085)]
    for sx in (-1, 1):
        B.shard(f"{name}_s{sx}", side if sx > 0 else Mo.mirror(side), 0.0, 0.105, A, slope=0.016, groove=0.008,
                panel_h=0.01, tags=tags)
    B.box(name + "_b", 0, -0.0825, 0.30, 0.065, 0.0, 0.10, A, bevel=0.008, tags=tags)
    if kind == "fill":
        H.heap(name + "_h", 0, 0.0, 0.045, 0.085, 0.07, 0.05, Xm["sulfur"], tags, mat2=Xm["sulfur_dk"], n=9)
    return H.parent_new(name, before, (x, y, z), s, rz)


def _table(M, Xm, X, tags, i):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    rot = _rotation(i)
    B.plate("tb_base", H.octo(TCX, TCY, 0.475), 0.03, 0.08, KM, slope=0.02, tags=tags)
    B.bolts("tb_bolt", H.octo(TCX, TCY, 0.45, 22.5), 0.085, 0.014, S, tags=tags)
    a0 = -rot
    B.plate("tb_disk", H.octo(TCX, TCY, 0.43, 22.5 + a0), 0.08, 0.125, K, slope=0.015, tags=tags)
    for k in range(4):
        ang = 90 * k + a0
        B.shard(f"tb_pal{k}", H.rot(PALLET, ang, TCX, TCY), 0.12, 0.172, A, slope=0.02, groove=0.014,
                panel_h=0.014, tags=tags)
        cr = H.rot(B.rpoly(NEST_R, 0.0, 0.212, 0.157, 0, chamfer=0.03), ang, TCX, TCY)
        B.loft(f"tb_cradle{k}", cr, cr, 0.183, 0.19, M["black"], bevel=0.0, tags=tags)
        tooth = [(0.31, -0.035), (0.39, -0.07), (0.425, -0.04), (0.425, 0.04), (0.39, 0.07), (0.31, 0.035)]
        B.plate(f"tb_tooth{k}", H.rot(tooth, ang + 45, TCX, TCY), 0.12, 0.165, AM, slope=0.015, tags=tags)
        px, py = H.rot([(0.375, 0.0)], ang + 45, TCX, TCY)[0]
        B.cyl(f"tb_pipbed{k}", px, py, 0.168, 0.02, 0.008, M["black"], axis="Z", verts=8, bevel=0.0, tags=tags)
        B.cyl(f"tb_pip{k}", px, py, 0.172, 0.011, 0.006, M["glow_dim"], axis="Z", verts=8, bevel=0.0, tags=tags)
    B.plate("tb_hub", H.octo(TCX, TCY, 0.115, 22.5 + a0), 0.12, 0.21, AM, slope=0.02, tags=tags)
    B.plate("tb_hub2", H.octo(TCX, TCY, 0.065, a0), 0.21, 0.235, S, slope=0.01, tags=tags)
    B.cyl("tb_hubled", TCX, TCY, 0.236, 0.02, 0.006, M["glow"] if rot else M["glow_dim"], axis="Z", verts=8,
          bevel=0.0, tags=tags)
    for st, (kind, slide) in _nests(i).items():
        if kind is None:
            continue
        ang = st + a0
        r = NEST_R + slide
        x, y = TCX + math.cos(math.radians(ang)) * r, TCY + math.sin(math.radians(ang)) * r
        if kind == "mag":
            H.mini_mag(f"nm{st}", x, y, 0.19, M, Xm, tags, kind="blank", s=MAG_S, rz=ang - 90)
        else:
            _tray(f"nt{st}", M, Xm, tags, kind, x, y, ang - 90, MAG_S, z=0.19)
    # estacoes fixas: postes de aco nas bordas W, E e S
    for name, ang in (("w", 180), ("e", 0), ("s", 270)):
        for sv in (-1, 1):
            g = [(0.405, sv * 0.14), (0.435, sv * 0.14), (0.435, sv * 0.175), (0.405, sv * 0.175)]
            g = g if sv > 0 else list(reversed(g))
            B.loft(f"gate_{name}{sv}", H.rot(g, ang, TCX, TCY), H.rot(g, ang, TCX, TCY), 0.04, 0.17, S, bevel=0.005,
                   tags=tags)


def _sparks(M, X, tags, cx, cy, amount):
    if amount <= 0:
        return
    rnd = random.Random(7)
    n = 12 if amount > 0.7 else 6
    for k in range(n):
        side = -1 if k % 2 else 1
        a = (rnd.uniform(-35, 25) if side > 0 else 180 + rnd.uniform(-25, 35))
        r0 = 0.07 + rnd.uniform(0, 0.05) + (0.06 if amount < 0.7 else 0.0)
        ln = (0.05 + rnd.uniform(0, 0.06)) * (1.0 if amount > 0.7 else 0.7)
        dx, dy = math.cos(math.radians(a)), math.sin(math.radians(a))
        B.rbox(f"spark{k}", cx + dx * (r0 + ln / 2), cy + dy * (r0 + ln / 2), 0.012, ln, 0.50, 0.506, X["spark"],
               rot=a - 90, bevel=0.0, tags=tags)
    B.rbox("hotspot", cx, cy + 0.01, 0.10 * amount + 0.04, 0.03, 0.31, 0.318, X["hot"], bevel=0.0, tags=tags)


def _press(M, X, tags, st):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    die = st["die"]
    B.box("mc_chan", 0, 0.98, 0.40, 0.84, 0.04, 0.07, M["black"], bevel=0.0, tags=tags)
    cheek = [(-0.20, 1.40), (-0.40, 1.40), (-0.48, 1.32), (-0.48, 0.74), (-0.44, 0.56), (-0.34, 0.44),
             (-0.24, 0.48), (-0.21, 0.62), (-0.20, 0.68)]
    for side, sx in (("L", -1), ("R", 1)):
        ca, cp = B.shard(f"cheek_{side}", H.flip(sx)(cheek), 0.0, 0.50, A, slope=0.07, groove=0.035, panel_h=0.03,
                         tags=tags)
        H.ledslot(f"ck_slot{side}", sx * 0.37, 0.92, 0.04, 0.22, 0.45, 3, M, tags, [ca, cp], pw=0.02,
                  pip_mat=M["glow_dim"])
        if cp is not None:
            B.cut(cp, [B.rbox(f"ck_pl{side}", sx * 0.40, 0.66, 0.022, 0.22, 0.47, 0.8, K, rot=sx * -22, bevel=0.0)])
        B.box(f"die_rail{side}", sx * 0.185, 0.86, 0.022, 0.56, 0.05, 0.24, S, bevel=0.004, tags=tags)
    B.cyl("ram_cyl", 0, 1.10, 0.36, 0.125, 0.30, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
    for k, y in enumerate((0.97, 1.07, 1.17)):
        B.cyl(f"ram_ring{k}", 0, y, 0.36, 0.135, 0.025, S, axis="Y", verts=8, bevel=0.004, tags=tags)
    fy = DIE_OUT - (DIE_OUT - DIE_IN) * die
    top = fy + 0.25
    rod_len = 0.97 - top
    B.cyl("ram_rod", 0, top + rod_len / 2, 0.36, 0.048, rod_len + 0.02, X["silver_r"], axis="Y", verts=12,
          bevel=0.0, tags=tags)
    head = [(-0.175, fy + 0.25), (0.175, fy + 0.25), (0.175, fy + 0.10), (0.09, fy + 0.0), (-0.09, fy + 0.0),
            (-0.175, fy + 0.10)]
    ha, hp = B.shard("die_head", head, 0.22, 0.46, A, slope=0.05, groove=0.025, panel_h=0.025, tags=tags)
    if hp is not None:
        B.cut(hp, [B.box("die_pl", 0, fy + 0.19, 0.30, 0.022, 0.42, 0.6, K, bevel=0.0)])
    for sx in (-1, 1):
        B.box(f"die_ear{sx}", sx * 0.175, fy + 0.17, 0.04, 0.11, 0.24, 0.40, AM, bevel=0.006, tags=tags)
    B.box("die_insert", 0, fy + 0.035, 0.15, 0.07, 0.14, 0.30, S, bevel=0.006, tags=tags)
    B.box("die_cav", 0, fy + 0.01, 0.09, 0.025, 0.28, 0.305, M["black"], bevel=0.0, tags=tags)
    H.ledslot("die_led", 0, fy + 0.12, 0.12, 0.032, 0.42, 2, M, tags, [ha, hp], vertical=False, pw=0.014,
              pip_mat=M["glow"] if die >= 1.0 else M["glow_dim"])
    if die >= 1.0:
        B.box("die_hot", 0, fy + 0.012, 0.08, 0.012, 0.305, 0.31, X["hot"], bevel=0.0, tags=tags)
        B.cyl("die_glint", 0.0, fy - 0.03, 0.30, 0.014, 0.006, X["glint"], axis="Z", verts=8, bevel=0.0, tags=tags)
    _sparks(M, X, tags, 0.0, fy - 0.01, st["spark"])
    if st["ember"]:
        B.box("tips_ember", 0.0, TCY + NEST_R + 0.10, 0.10, 0.03, 0.27, 0.276, M["ember"], bevel=0.0, tags=tags)
    beam = [(-0.50, 1.20), (0.50, 1.20), (0.57, 1.26), (0.57, 1.33), (0.50, 1.40), (-0.50, 1.40), (-0.57, 1.33),
            (-0.57, 1.26)]
    ba, bp = B.shard("beam", beam, 0.50, 0.64, A, slope=0.045, groove=0.025, panel_h=0.022, tags=tags)
    H.vent("beam_v", 0, 1.30, 0.50, 0.11, 0.59, 0.64, M, tags, n=3, targets=[ba, bp])
    for k, x in enumerate((-0.44, 0.44)):
        B.bolts(f"beam_bolt{k}", [(x, 1.30)], 0.665, 0.018, S, tags=tags)


# cascas dos cantos de cima (lado esquerdo; o direito e o espelho), as da Prensa AP 1.x deslocadas 0.5 para fora
REAR = H.shift([(-1.42, 1.30), (-1.30, 1.42), (-0.94, 1.42), (-0.94, 1.06), (-1.155, 0.845), (-1.30, 0.845),
                (-1.42, 0.965)], -0.5, 0.0)
WEDGE = H.shift([(-0.88, 1.42), (-0.75, 1.42), (-0.64, 1.30), (-0.64, 1.18), (-0.68, 1.14), (-0.68, 1.06),
                 (-0.64, 1.02), (-0.64, 0.97), (-0.765, 0.845), (-1.07, 0.845), (-0.88, 1.035)], -0.5, 0.0)
BLADE = H.shift([(-1.42, 0.785), (-0.88, 0.785), (-0.70, 0.70), (-0.64, 0.60), (-0.74, 0.555), (-1.30, 0.555),
                 (-1.42, 0.65)], -0.5, 0.0)


def _win(sx, d=0.0):
    x0, x1, y0, y1 = WIN_X - 0.14 + d, WIN_X + 0.14 - d, WIN_Y - 0.14 + d, WIN_Y + 0.14 - d
    c = 0.10 - d * (2 - 2 ** 0.5)
    poly = [(x0 + c, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0 + c)]
    return poly if sx > 0 else Mo.mirror(poly)


def _housing(prefix, sx, M, tags):
    f = H.flip(sx)
    K, A, S = M["core"], M["armor"], M["steel"]
    ra, rp = B.shard(prefix + "_rear", f(REAR), 0.0, 0.46, A, slope=0.07, groove=0.035, panel_h=0.03, tags=tags)
    wa, wp = B.shard(prefix + "_wedge", f(WEDGE), 0.0, 0.50, A, slope=0.05, groove=0.025, panel_h=0.03, tags=tags)
    b, bp = B.shard(prefix + "_blade", f(BLADE), 0.0, 0.34, A, slope=0.07, groove=0.03, panel_h=0.025, tags=tags)
    if rp is not None:
        B.cut(rp, [B.rbox(prefix + "_pl2", sx * 1.52, 1.345, 0.022, 0.12, 0.42, 0.8, K, rot=sx * 45, bevel=0.0)])
    H.ledslot(prefix + "_wsl", sx * 1.26, 1.28, 0.04, 0.14, 0.45, 3, M, tags, [wa, wp], pw=0.02,
              pip_mat=M["glow_dim"])
    if wp is not None:
        B.cut(wp, [B.rbox(prefix + "_wpl", sx * 1.28, 0.96, 0.12, 0.022, 0.46, 0.8, K, rot=sx * 45, bevel=0.0)])
    if bp is not None:
        B.cut(bp, [B.rbox(prefix + "_pl3", sx * 1.30, 0.66, 0.022, 0.14, 0.31, 0.8, K, rot=sx * 55, bevel=0.0)])
    B.bolts(prefix + "_bolt", [(sx * 1.83, 1.35), (sx * 1.83, 0.93)], 0.49, 0.018, S, tags=tags)
    return ra, rp, b, bp


def _mixer(M, Xm, tags, st):
    """Misturador de enxofre (canto de cima a esquerda): tambor com monte de enxofre e pas girando; calha da base."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    ra, rp, b, bp = _housing("mix", -1, M, tags)
    H.bezel("mix_win", _win(-1), _win(-1, 0.024), 0.24, 0.46, M, tags, (ra, rp))
    cx, cy = -WIN_X + 0.01, WIN_Y + 0.01
    B.plate("mix_drum", H.octo(cx, cy, 0.125), 0.20, 0.24, KM, slope=0.01, tags=tags)
    H.heap("mix_heap", cx, cy, 0.24, 0.10, 0.10, 0.05, Xm["sulfur"], tags, mat2=Xm["sulfur_dk"], n=10, seed=4)
    H.rotor("mix_rot", cx, cy, 0.30, 0.22, -st["i"] * 36.0, M, tags, blades=3, w=0.024)
    # calha da base de enxofre ate a lamina (boca com seta para cima) e duto ate o dosador
    for t, nm in ((b, "a"), (bp, "b")):
        if t is not None:
            B.cut(t, [B.box(f"mix_in_c{nm}", -1.60, 0.665, 0.30, 0.07, 0.27, 0.8, K, bevel=0.0)])
    B.box("mix_in_bed", -1.60, 0.665, 0.30, 0.07, 0.26, 0.272, M["black"], bevel=0.0, tags=tags)
    for k in range(3):
        H.chevron(f"mix_in_ar{k}", -1.70 + k * 0.10, 0.665, 90, M["glow_dim"], tags, z=0.272, s=0.42)
    B.cyl("mix_duct", -1.05, 0.70, 0.12, 0.045, 0.22, KM, axis="X", verts=8, bevel=0.006, tags=tags)
    B.cyl("mix_ductr", -1.05, 0.70, 0.12, 0.053, 0.025, S, axis="X", verts=8, bevel=0.004, tags=tags)


def _forge(M, Xm, X, tags, st):
    """Forja de pontas (canto de cima a direita): pontas de tristeel andando ate a bobina de inducao."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    ra, rp, b, bp = _housing("frg", 1, M, tags)
    x0, x1 = WIN_X - 0.14, WIN_X + 0.14
    H.bezel("frg_win", _win(1), _win(1, 0.024), 0.30, 0.46, M, tags, (ra, rp))
    pitch = 0.105
    i = st["i"]
    off = {0: 0.0, 1: 0.0, 2: 0.5}.get(i, 1.0) * pitch if i < 6 else 0.0
    lead = True
    for k in range(-1, 5):
        x = x0 + 0.10 + k * pitch - off
        if not (x0 + 0.02 < x < x1 - 0.005):
            continue
        ys = WIN_Y + 0.005
        B.cyl(f"frg_tip{k}", x, ys - 0.015, 0.355, 0.045, 0.15, X["silver_r"], axis="Y", verts=8, bevel=0.0, r2=0.0,
              yaw=180, tags=tags)
        B.cyl(f"frg_tipb{k}", x, ys + 0.075, 0.355, 0.05, 0.03, S, axis="Y", verts=8, bevel=0.0, tags=tags)
        if lead:
            B.box("frg_glint", x - 0.012, ys + 0.02, 0.012, 0.03, 0.40, 0.406, X["glint"], bevel=0.0, tags=tags)
            lead = False
    for k in range(3):
        B.box(f"frg_coil{k}", x0 + 0.04 + k * 0.022, WIN_Y, 0.010, 0.22, 0.39, 0.42,
              X["hot"] if k == 1 else M["ember"], bevel=0.0, tags=tags)
    for t, nm in ((b, "a"), (bp, "b")):
        if t is not None:
            B.cut(t, [B.box(f"frg_in_c{nm}", 1.60, 0.665, 0.30, 0.07, 0.27, 0.8, K, bevel=0.0)])
    B.box("frg_in_bed", 1.60, 0.665, 0.30, 0.07, 0.26, 0.272, M["black"], bevel=0.0, tags=tags)
    for k in range(3):
        H.chevron(f"frg_in_ar{k}", 1.50 + k * 0.10, 0.665, 90, M["glow_dim"], tags, z=0.272, s=0.42)


def _hydraulics(M, Xm, X, tags, st):
    """Central hidraulica entre o misturador e a prensa: bomba de 2 pistoes alternados numa casca clara."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    shell = [(-1.08, 0.86), (-0.60, 0.86), (-0.55, 0.91), (-0.55, 1.36), (-0.60, 1.41), (-1.08, 1.41)]
    sa, sp = B.shard("hyd", shell, 0.0, 0.40, A, slope=0.05, groove=0.022, panel_h=0.024, tags=tags)
    win = B.rpoly(-0.815, 1.155, 0.34, 0.36, 0, chamfer=0.05)
    H.bezel("hyd_win", win, B.rpoly(-0.815, 1.155, 0.30, 0.32, 0, chamfer=0.04), 0.22, 0.40, M, tags, (sa, sp))
    phase = st["i"] / NF
    for k, bx in enumerate((-0.885, -0.745)):
        B.box(f"hyd_bore{k}", bx, 1.14, 0.09, 0.26, 0.22, 0.25, KM, bevel=0.006, tags=tags)
        d = 0.05 * math.cos(2 * math.pi * (phase + 0.5 * k))
        hy = 1.13 + d
        B.cyl(f"hyd_rod{k}", bx, (hy + 1.29) / 2, 0.28, 0.016, 1.29 - hy, X["silver_r"], axis="Y", verts=8,
              bevel=0.0, tags=tags)
        B.box(f"hyd_pst{k}", bx, hy, 0.08, 0.07, 0.25, 0.31, A, bevel=0.012, tags=tags)
    B.box("hyd_crank", -0.815, 1.29, 0.26, 0.05, 0.25, 0.30, KM, bevel=0.008, tags=tags)
    H.ledslot("hyd_led", -0.815, 0.94, 0.20, 0.034, 0.36, 3, M, tags, [sa, sp], vertical=False, pw=0.016,
              pips=[M["glow_dim"], None, None])
    for k, y in enumerate((0.98, 1.22)):
        B.cyl(f"hyd_hose{k}", -0.515, y, 0.20, 0.022, 0.07, S, axis="X", verts=8, bevel=0.0, tags=tags)


def _tools(M, Xm, tags, st):
    """Porta-ferramentas entre a prensa e a forja: 4 matrizes (uma por municao) com a faixa da cor dela."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    shell = Mo.mirror([(-1.08, 0.86), (-0.60, 0.86), (-0.55, 0.91), (-0.55, 1.36), (-0.60, 1.41), (-1.08, 1.41)])
    sa, sp = B.shard("tool", shell, 0.0, 0.40, A, slope=0.05, groove=0.022, panel_h=0.024, tags=tags)
    win = B.rpoly(0.815, 1.155, 0.34, 0.40, 0, chamfer=0.05)
    H.bezel("tool_win", win, B.rpoly(0.815, 1.155, 0.30, 0.36, 0, chamfer=0.04), 0.22, 0.40, M, tags, (sa, sp))
    for k, kind in enumerate(("ap", "sap", "ac", "frag")):
        x = 0.74 + (k % 2) * 0.15
        y = 1.235 - (k // 2) * 0.165
        B.box(f"tool{k}", x, y, 0.12, 0.13, 0.22, 0.29, S, bevel=0.012, tags=tags)
        B.box(f"tool_c{k}", x, y + 0.02, 0.07, 0.05, 0.29, 0.30, M["black"], bevel=0.0, tags=tags)
        B.box(f"tool_b{k}", x, y - 0.04, 0.10, 0.022, 0.29, 0.305, H.chip_mat(kind, 0.3), bevel=0.0, tags=tags)
    H.ledslot("tool_led", 0.815, 0.94, 0.20, 0.034, 0.36, 3, M, tags, [sa, sp], vertical=False, pw=0.016,
              pips=[None, M["glow_dim"], None])


def _doser(M, Xm, tags, st):
    """Dosador a esquerda da mesa: pilha de bandejas vazias numa janela e bico de enxofre sobre o ninho W."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    shell = [(-0.96, -0.42), (-0.62, -0.42), (-0.52, -0.32), (-0.52, 0.30), (-0.62, 0.40), (-0.96, 0.40)]
    sa, sp = B.shard("dos", shell, 0.0, 0.36, A, slope=0.05, groove=0.022, panel_h=0.022, tags=tags)
    win = B.rpoly(-0.76, -0.08, 0.24, 0.34, 0, chamfer=0.04)
    H.bezel("dos_win", win, B.rpoly(-0.76, -0.08, 0.20, 0.30, 0, chamfer=0.03), 0.10, 0.36, M, tags, (sa, sp))
    for k in range(3):
        _tray(f"dos_t{k}", M, Xm, tags, "tray", -0.76, -0.17 + k * 0.095, 0, 0.62, z=0.10)
    # bico de enxofre: braco escuro saindo da casca para o ninho W
    B.box("dos_noz", -0.48, 0.18, 0.12, 0.05, 0.28, 0.33, KM, bevel=0.008, tags=tags)
    B.box("dos_nozt", -0.40, 0.18, 0.05, 0.05, 0.24, 0.30, S, bevel=0.006, tags=tags)
    if st["i"] in (2, 3):
        H.grains("dos_fall", [(-0.40, 0.14), (-0.39, 0.10)], 0.22, 0.016, Xm["sulfur"], tags, seed=8)
    H.ledslot("dos_led", -0.76, 0.27, 0.18, 0.032, 0.32, 3, M, tags, [sa, sp], vertical=False, pw=0.014,
              pips=[M["glow_dim"] if st["i"] in (1, 2, 3) else None, None, None])


def _scanner(M, X, tags, st):
    """Scanner de inspecao a direita da mesa (olho frio sobre o ninho E) e painel de pips."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    shell = Mo.mirror([(-0.96, -0.42), (-0.62, -0.42), (-0.52, -0.32), (-0.52, 0.30), (-0.62, 0.40), (-0.96, 0.40)])
    sa, sp = B.shard("scn", shell, 0.0, 0.36, A, slope=0.05, groove=0.022, panel_h=0.022, tags=tags)
    H.vent("scn_v", 0.76, -0.16, 0.24, 0.24, 0.30, 0.36, M, tags, n=4, targets=[sa, sp])
    B.box("scn_arm", 0.48, 0.0, 0.12, 0.10, 0.26, 0.33, KM, bevel=0.01, tags=tags)
    B.box("scn_eyebed", 0.43, 0.0, 0.03, 0.08, 0.30, 0.335, M["black"], bevel=0.0, tags=tags)
    B.box("scn_eye", 0.43, 0.0, 0.014, 0.06, 0.335, 0.34, X["glint"] if st["i"] in (1, 2, 3, 4) else M["core_mid"],
          bevel=0.0, tags=tags)
    H.ledslot("scn_led", 0.76, 0.22, 0.18, 0.032, 0.32, 3, M, tags, [sa, sp], vertical=False, pw=0.014,
              pips=[None, None, M["glow_dim"]])


def _distributor(M, Xm, tags, st):
    """Trilho do distribuidor embaixo da mesa: 4 setas na cor de cada municao apontando para as 4 saidas."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    B.box("ds_rail", 0, -0.455, 1.86, 0.07, 0.0, 0.06, KM, bevel=0.008, tags=tags)
    B.box("ds_bed", 0, -0.455, 1.80, 0.035, 0.06, 0.064, M["black"], bevel=0.0, tags=tags)
    for k, (x, ang, kind) in enumerate(((-0.86, 225, "ap"), (-0.50, 270, "sap"), (0.50, 270, "ac"),
                                        (0.86, 315, "frag"))):
        H.chevron(f"ds_ar{k}", x, -0.455, ang, H.led(kind, 0.9 if kind != "ap" else 0.7), tags, z=0.064, s=0.5)
    # garganta da descarga sob o ninho S
    B.box("ds_mouth", 0, -0.44, 0.24, 0.10, 0.0, 0.07, K, bevel=0.006, tags=tags)
    for g in (-1, 1):
        B.box(f"ds_g{g}", g * 0.135, -0.44, 0.022, 0.11, 0.0, 0.11, S, bevel=0.004, tags=tags)


def machine(M, T="machine", phase=0.0):
    tags = (T,)
    Xm = H.X(M)
    X = _extra()
    st = _state(phase)
    B.plate("mc_bed", B.rpoly(0, 0.98, 3.84, 0.86, 0, chamfer=0.08), 0.0, 0.05, M["core"], slope=0.01, tags=tags)
    B.plate("mc_bed2", B.rpoly(0, 0.0, 1.90, 0.94, 0, chamfer=0.10), 0.0, 0.04, M["core"], slope=0.01, tags=tags)
    _distributor(M, Xm, tags, st)
    _table(M, Xm, X, tags, st["i"])
    _press(M, X, tags, st)
    _mixer(M, Xm, tags, st)
    _forge(M, Xm, X, tags, st)
    _hydraulics(M, Xm, X, tags, st)
    _tools(M, Xm, tags, st)
    _doser(M, Xm, tags, st)
    _scanner(M, X, tags, st)


# ============================================================================ teto
def roof(M, T="roof"):
    tags = (T,)
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    deck = H.roof_deck(M, W, HH, skip={(1, 0), (2, 0), (1, 1), (2, 1)}, T=T)
    H.roof_hatch("rf_in0", M, -1.5, 0.0, 90, deck[(0, 1)], T=T)
    H.roof_hatch("rf_in1", M, 1.5, 0.0, 90, deck[(3, 1)], T=T)
    for (i, j), kind in OUTS.items():
        cx, cy = H.cell_xy(W, HH, i, j)
        H.roof_hatch(f"rf_out{i}", M, cx, cy, 270, deck[(i, j)], T=T, chip=kind)
    # coroa sobre a prensa (2 celulas de cima do meio): nucleo escuro + espinha em cunha com o encaixe da placa
    base = [(-0.96, 0.56), (0.96, 0.56), (0.96, 1.40), (0.90, 1.46), (-0.90, 1.46), (-0.96, 1.40)]
    B.plate("cr_core", base, 0.0, 0.10, K, slope=0.02, tags=tags)
    spine = [(-0.50, 1.44), (0.50, 1.44), (0.56, 1.38), (0.56, 0.72), (0.18, 0.50), (-0.18, 0.50), (-0.56, 0.72),
             (-0.56, 1.38)]
    # a espinha e so a moldura em volta do encaixe da placa (o encaixe tira o miolo inteiro): placa chanfrada simples
    # (com B.shard o painel interno sumia nas booleanas)
    sa = B.plate("cr_spine", spine, 0.08, 0.30, A, slope=0.06, tags=tags)
    H.plate_slot("cr_plate", M, PLATE_C[0], PLATE_C[1], 0.8, [sa], T=T, z1=0.36)
    # garras laterais da coroa (descem ate a borda da celula do meio) com fenda de pips e respiro
    claw = [(-0.94, 1.42), (-0.62, 1.42), (-0.62, 0.70), (-0.70, 0.56), (-0.94, 0.56)]
    for sx in (-1, 1):
        ca, cp = B.shard(f"cr_claw{sx}", H.flip(sx)(claw), 0.08, 0.26, A, slope=0.05, groove=0.022, panel_h=0.022,
                         tags=tags)
        H.vent(f"cr_cv{sx}", sx * 0.78, 1.20, 0.18, 0.26, 0.22, 0.27, M, tags, n=4, targets=[ca, cp])
        H.ledslot(f"cr_csl{sx}", sx * 0.78, 0.82, 0.034, 0.20, 0.22, 3, M, tags, [ca, cp], pw=0.016,
                  pip_mat=M["glow_dim"])
    # celulas do meio (sobre a mesa): UMA placa verde de 2 quadros com o furo octogonal do colar segmentado
    green = H.roof_green()
    mid = B.rpoly(0, 0, 1.92, 0.92, 0, chamfer=0.10)
    ma, mp = B.shard("rf_mid", mid, 0.0, 0.07, green, slope=0.03, groove=0.05, panel_h=0.022, tags=tags)
    hole = H.octo(0, 0, 0.43)
    for q, t in enumerate((ma, mp)):
        if t is not None:
            B.cut(t, [B.loft(f"rf_midh{q}", hole, hole, -0.01, 0.5, K, bevel=0.0)])
    # linhas de painel ESCURAS e respiros nas duas pontas da placa (a placa e longa: quebra a cada ~0,3 quadro, e no
    # casco branco a placa verde vira branca - so as frestas escuras a separam)
    for k, sx_ in enumerate((-1, 1)):
        H.groove(f"rf_midpl{k}", sx_ * 0.56, 0, 0.026, 0.66, 0.07, (ma, mp), M, tags, depth=0.05)
        H.vent(f"rf_midv{k}", sx_ * 0.76, 0.12, 0.20, 0.36, 0.03, 0.06, M, tags, n=4, targets=[ma, mp])
        H.ledslot(f"rf_mids{k}", sx_ * 0.76, -0.24, 0.20, 0.034, 0.03, 3, M, tags, [ma, mp], vertical=False,
                  pw=0.016, pip_mat=M["glow_dim"])
    B.plate("cr_colbase", H.octo(0, 0, 0.42), 0.0, 0.05, K, slope=0.01, tags=tags)
    for k in range(8):
        a0 = 22.5 + 45 * k
        seg = [(math.cos(math.radians(a0 + d)) * r, math.sin(math.radians(a0 + d)) * r)
               for r, d in ((0.29, -19), (0.40, -19), (0.40, 19), (0.29, 19))]
        B.shard(f"cr_col{k}", seg, 0.0, 0.13, AM, slope=0.02, groove=0.012, panel_h=0.012, tags=tags)
    B.cyl("cr_hub", 0, 0, 0.10, 0.12, 0.08, KM, axis="Z", verts=8, bevel=0.01, tags=tags)
    B.cyl("cr_hubc", 0, 0, 0.15, 0.06, 0.03, S, axis="Z", verts=8, bevel=0.006, tags=tags)
    B.cyl("cr_hubl", 0, 0, 0.168, 0.022, 0.006, M["glow_dim"], axis="Z", verts=8, bevel=0.0, tags=tags)
    # cantos de cima: respiro de persianas + caixa de juncao (insumo sobe para a maquina)
    for sx in (-1, 1):
        pa, pp = deck[(0 if sx < 0 else 3, 0)]
        cx = sx * 1.5
        jb = H.flip(sx)([(-1.86, 0.62), (-1.20, 0.62), (-1.12, 0.70), (-1.12, 1.02), (-1.20, 1.10), (-1.86, 1.10)])
        B.plate(f"rf_jbk{sx}", B.offset_poly(jb, -0.03), 0.06, 0.10, K, slope=0.01, tags=tags)
        ja, jp = B.shard(f"rf_jb{sx}", jb, 0.09, 0.22, A, slope=0.04, groove=0.02, panel_h=0.02, tags=tags)
        H.ledslot(f"rf_jbs{sx}", cx, 0.86, 0.30, 0.04, 0.10, 3, M, tags, [ja, jp], vertical=False, pw=0.018,
                  pip_mat=M["glow_dim"])
        rv = B.box(f"rf_sv{sx}", cx + sx * 0.14, 1.28, 0.30, 0.20, 0.07, 0.125, KM, bevel=0.008, slope=0.012,
                   tags=tags)
        B.cut(rv, [B.box(f"rf_svc{sx}{k}", cx + sx * 0.14, 1.215 + k * 0.045, 0.22, 0.02, 0.105, 0.3, K,
                         bevel=0.0) for k in range(3)])
        B.cyl(f"rf_cd{sx}", sx * 1.04, 0.86, 0.13, 0.04, 0.16, KM, axis="X", verts=8, bevel=0.006, tags=tags)
        B.bolts(f"rf_cb{sx}", [(sx * 1.86, 1.36), (sx * 1.14, 1.36)], 0.095, 0.016, S, tags=tags)
    H.roof_unpaint(T)
