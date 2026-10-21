"""F1 Prensa HE (HE Press) 2x2 - funde e prensa o Carregador HE a partir de enxofre (spec 2.0, factories F1).

Mesmo ID da 1.x (rafaeltessaro.bs_factory_mag_std), arte REFEITA para a 2.0: o insumo agora e enxofre bruto.
Grade (vanilla factory_ammo 2x2): fileira de cima = maquinario (BlockedTravelCells [0,0],[1,0]); fileira de
baixo = ENTRADA de enxofre [0,1] (esquerda) e SAIDA do Carregador HE [1,1] (direita). As duas bases ficam livres
(o jogo desenha as pilhas ali e a tripulacao chega pelas portas [-1,1], [2,1], [0,2], [1,2]).
Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade = 1 quadro.

Maquinario (familia das armas: cascas claras com bisel duplo sobre nucleo escuro, LEDs ambar so em recessos):
  * TREMONHA DE ENXOFRE (esquerda, sobre a base de entrada): casca clara com janela octogonal em degrau que
    mostra o funil escuro em aneis com os graos amarelos girando e o agitador de 3 pas; a CALHA desce da
    tremonha ate a borda da base de entrada (graos subindo, seta ambar para cima na boca);
  * ROSCA ALIMENTADORA: calha aberta da tremonha ate a matriz, com a rosca (palhetas de aco inclinadas que
    andam) levando os graos;
  * MATRIZ DE FUNDICAO (meio-direita): bloco claro em U com a cavidade do carregador (janela escura) e o portao
    de baixo; enche de graos (3 quadros), o martelo prensa (lampejo e 2 faiscas), o carregador sai em brasa,
    o portao abre e o Carregador HE 2.0 (caixa blindada, 3 municoes, faixa ambar) desce para a saida;
  * MARTELO: cilindro hidraulico facetado no alto (canal escuro com LED que acende na batida) e cabeca em seta
    que desce sobre a matriz;
  * BOCA DE SAIDA embaixo da matriz (capuz escuro, guias de aco, seta ambar para baixo) e o modulo de bomba
    hidraulica na faixa da direita (fenda de pips, mangueiras ate o cilindro).
Animacao: 10 quadros x 0,125 s = 1,25 s = um carregador por volta (econ interval_s_base 1,25):
  0 repouso (= sprite desligado) | 1-3 a rosca enche a cavidade | 4 o martelo desce | 5 batida (lampejo, faiscas,
  o carregador aparece fundido, pontas em brasa) | 6 segura | 7 recua, o portao abre | 8-9 o carregador desce
  para a boca de saida.
Teto: placas verdes (pintura) nas bases com escotilhas em seta (entra / sai) e, sobre a fileira de cima, a coroa
blindada: tampa octogonal da tremonha (bocal de carga e respiros radiais), torre da prensa em seta apontando
para a saida (espinha com visor de contagem e trilhos-guia), lamina diagonal e ombreiras com respiros.
"""

import math

import bs3d as B
import models as Mo
from parts import _bs2_fabricas_helpers as H

PART = {
    "id": "rafaeltessaro.bs_factory_mag_std",
    "kind": "factory",
    "size": [2, 2],
    "accent": "amber",
    "machine_frames": 10,
    "machine_interval": 0.125,
}

W, HH = PART["size"]
NF = PART["machine_frames"]
HOP = (-0.55, 0.60)        # centro da janela da tremonha
HOP_R = 0.185              # raio da janela octogonal
CHUTE_X = -0.50            # calha de entrada (centro da base de entrada)
AUG_Y = 0.335              # rosca alimentadora
AUG_X0, AUG_X1 = -0.36, 0.25
DIE = (0.45, 0.375)        # centro da cavidade da matriz
CAV = (0.24, 0.17)         # cavidade (largura, altura)
RAM_X = DIE[0]
RAM_IN, RAM_OUT = 0.685, 0.545   # frente do martelo recolhido / batendo
CYL_Y0, CYL_Y1 = 0.70, 0.885
OUT_X = 0.50               # boca de saida (centro da base de saida)
MAG_S = 0.80               # escala do Carregador HE na matriz (0.24 x 0.17 quadro)

META_EXTRA = {
    "factory_code": "F1",
    "name_ptbr": "Prensa HE",
    "grid": {"blocked": [[0, 0], [1, 0]], "inputs": {"sulfur": [0, 1, 1, 1]},
             "outputs": {"he": [1, 1, 1, 1]}},
    "notes": ["10 quadros x 0,125 s = 1,25 s = um Carregador HE por volta (interval_s_base 1,25)",
              "lights.png vem do quadro 1 (repouso): so LEDs pequenos"],
}


def _state(phase):
    i = int(round(phase * NF)) % NF
    return {
        "i": i,
        "fill": {1: 1, 2: 2, 3: 3, 4: 3}.get(i, 0),
        "ram": {4: 0.5, 5: 1.0, 6: 0.88, 7: 0.35, 8: 0.08}.get(i, 0.0),
        "mag": i in (5, 6, 7, 8, 9),
        "cast": {5: 1.0, 6: 0.75, 7: 0.45, 8: 0.25, 9: 0.1}.get(i, 0.0),
        "drop": {8: 0.10, 9: 0.215}.get(i, 0.0),
        "gate": {7: 0.6, 8: 1.0, 9: 1.0}.get(i, 0.0),
        "flow": i in (1, 2, 3),
    }


# ============================================================================ piso
def floor(M, T="floor"):
    """Poco escuro da maquina + base de entrada (seta para cima, enxofre) e de saida (seta para baixo)."""
    H.floor_grid(M, W, HH, machine={(0, 0), (1, 0)}, pads={(0, 1): 90, (1, 1): (270, 90)}, T=T)
    tags = (T,)
    # divisoria central entre as bases: barra de aco com parafusos
    B.box("fl_div", 0, -0.5, 0.05, 0.80, 0.0, 0.05, M["steel"], bevel=0.01, tags=tags)
    B.bolts("fl_divb", [(0, -0.20), (0, -0.80)], 0.05, 0.015, M["core_mid"], tags=tags)


# ============================================================================ maquina
def _hopper(M, Xm, tags, st):
    """Tremonha de enxofre: casca clara com janela octogonal, funil em aneis, graos girando e agitador."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    hx, hy = HOP
    shell = [(-0.885, 0.31), (-0.36, 0.31), (-0.28, 0.39), (-0.28, 0.80), (-0.36, 0.885), (-0.80, 0.885),
             (-0.885, 0.80)]
    sa, sp = B.shard("hop", shell, 0.0, 0.30, A, slope=0.06, groove=0.026, panel_h=0.026, tags=tags)
    out = H.octo(hx, hy, HOP_R + 0.035)
    inn = H.octo(hx, hy, HOP_R)
    H.bezel("hop_win", out, inn, 0.02, 0.335, M, tags, [sa, sp], bed=False)
    # funil: fundo escuro e um anel de aco em degrau na borda (o monte de enxofre fica dentro)
    B.plate("hop_fb", H.octo(hx, hy, HOP_R), 0.02, 0.05, K, slope=0.01, tags=tags)
    ring = B.plate("hop_fr", H.octo(hx, hy, HOP_R), 0.05, 0.10, KM, slope=0.015, tags=tags)
    B.cut(ring, [B.loft("hop_frc", H.octo(hx, hy, HOP_R - 0.03), H.octo(hx, hy, HOP_R - 0.03), 0.0, 0.3, K,
                        bevel=0.0)])
    # enxofre: monte no funil + torroes girando com o agitador
    ang = -st["i"] * 36.0
    H.heap("hop_heap", hx, hy, 0.05, HOP_R * 0.88, HOP_R * 0.88, 0.07, Xm["sulfur"], tags, mat2=Xm["sulfur_dk"])
    pts = []
    for k, (r, n) in enumerate(((HOP_R * 0.80, 7), (HOP_R * 0.52, 4))):
        for j in range(n):
            a = math.radians(ang * (1.0 if k == 0 else 1.6) + j * 360.0 / n + k * 17)
            pts.append((hx + math.cos(a) * r, hy + math.sin(a) * r))
    H.grains("hop_g", pts, 0.085, 0.026, Xm["sulfur"], tags, seed=3, mat2=Xm["sulfur_dk"])
    # agitador de 3 pas (aco) e cubo
    for b in range(3):
        a = ang * 1.3 + b * 120
        ca, sa_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        B.rbox(f"hop_bl{b}", hx + ca * HOP_R * 0.42, hy + sa_ * HOP_R * 0.42, HOP_R * 0.78, 0.028, 0.12, 0.15, S,
               rot=a, bevel=0.004, tags=tags)
    B.cyl("hop_hub", hx, hy, 0.16, 0.038, 0.03, KM, axis="Z", verts=8, bevel=0.006, tags=tags)
    B.cyl("hop_hubc", hx, hy, 0.18, 0.018, 0.012, S, axis="Z", verts=8, bevel=0.0, tags=tags)
    # LEDs de nivel da tremonha (fenda vertical na borda direita da casca)
    H.ledslot("hop_lv", -0.325, 0.60, 0.032, 0.24, 0.25, 4, M, tags, [sa, sp], pw=0.016,
              pips=[M["glow_dim"], M["glow_dim"], None, None])
    # respiro no canto de cima-esquerda da casca
    H.vent("hop_v", -0.80, 0.80, 0.09, 0.13, 0.26, 0.31, M, tags, n=3, vertical=True, targets=[sa, sp])
    return sa, sp


def _chute_in(M, Xm, tags, st):
    """Calha da base de entrada ate a tremonha: graos subindo (2 passos por volta)."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    x = CHUTE_X
    # duto coberto (aco escuro com nervuras) e uma janelinha de inspecao onde passam os torroes
    B.box("ch_tr", x, 0.18, 0.15, 0.28, 0.0, 0.10, KM, bevel=0.01, tags=tags)
    for k, y in enumerate((0.075, 0.27)):
        B.box(f"ch_rib{k}", x, y, 0.17, 0.03, 0.0, 0.12, S, bevel=0.005, tags=tags)
    win = B.box("ch_wc", x, 0.17, 0.07, 0.11, 0.06, 0.3, K, bevel=0.0)
    B.cut(B.bpy.context.scene.objects["ch_tr"], [win])
    B.box("ch_wbed", x, 0.17, 0.07, 0.11, 0.055, 0.06, M["black"], bevel=0.0, tags=tags)
    s = (st["i"] * 0.3) % 1.0
    pts = [(x + (0.012 if k % 2 else -0.012), 0.12 + (k + s) * 0.05) for k in range(3)]
    H.grains("ch_gr", [p for p in pts if p[1] < 0.215], 0.06, 0.02, Xm["sulfur"], tags, seed=5,
             mat2=Xm["sulfur_dk"])
    B.box("ch_mouth", x, 0.02, 0.13, 0.04, 0.0, 0.05, M["black"], bevel=0.0, tags=tags)
    H.chevron("ch_ar", x, 0.025, 90, M["glow_dim"], tags, z=0.05, s=0.6)


def _auger(M, Xm, tags, st):
    """Rosca alimentadora: calha aberta, palhetas inclinadas andando para a matriz e graos."""
    K, KM, S, AM = M["core"], M["core_mid"], M["steel"], M["armor_mid"]
    L = AUG_X1 - AUG_X0
    xc = (AUG_X0 + AUG_X1) / 2
    B.box("au_tr", xc, AUG_Y, L, 0.15, 0.0, 0.07, KM, bevel=0.008, tags=tags)
    B.box("au_bed", xc, AUG_Y, L, 0.10, 0.07, 0.074, M["black"], bevel=0.0, tags=tags)
    for g in (-1, 1):
        B.box(f"au_rl{g}", xc, AUG_Y + g * 0.062, L, 0.022, 0.06, 0.115, S, bevel=0.004, tags=tags)
    B.cyl("au_shaft", xc, AUG_Y, 0.10, 0.014, L, S, axis="X", verts=8, bevel=0.0, tags=tags)
    p = 0.075
    s = (st["i"] * 0.25) % 1.0
    for k in range(-1, 10):
        x = AUG_X0 + (k + s) * p
        if AUG_X0 + 0.01 < x < AUG_X1 - 0.01:
            B.rbox(f"au_fl{k}", x, AUG_Y, 0.016, 0.10, 0.08, 0.125, S, rot=28, bevel=0.003, tags=tags)
            if st["flow"] or st["i"] == 0:
                H.grains(f"au_gr{k}", [(x + p / 2, AUG_Y + (0.018 if k % 2 else -0.018))], 0.074, 0.022,
                         Xm["sulfur"], tags, seed=k + 11, mat2=Xm["sulfur_dk"])
    # mancais nas pontas
    for k, x in enumerate((AUG_X0, AUG_X1)):
        B.box(f"au_brg{k}", x, AUG_Y, 0.05, 0.16, 0.0, 0.14, AM, bevel=0.01, tags=tags)


def _die(M, Xm, tags, st):
    """Matriz de fundicao em U com a cavidade do carregador, o portao de baixo e o carregador fundido."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    dx, dy = DIE
    cw, ch = CAV
    # bloco claro: duas bochechas (esquerda/direita) e a ponte de cima, em U aberto embaixo
    cheek = [(dx - 0.235, dy - 0.155), (dx - cw / 2 - 0.012, dy - 0.155), (dx - cw / 2 - 0.012, dy + ch / 2 + 0.01),
             (dx - 0.07, dy + ch / 2 + 0.01), (dx - 0.07, dy + 0.165), (dx - 0.20, dy + 0.165),
             (dx - 0.235, dy + 0.13)]
    parts = []
    for sx in (-1, 1):
        poly = cheek if sx < 0 else [(2 * dx - x, y) for x, y in reversed(cheek)]
        parts.append(B.shard(f"die{sx}", poly, 0.0, 0.27, A, slope=0.045, groove=0.02, panel_h=0.022, tags=tags))
    # ponte de cima (onde o martelo bate): escura, com a placa de impacto de aco
    B.box("die_br", dx, dy + ch / 2 + 0.06, 0.15, 0.10, 0.0, 0.22, KM, bevel=0.01, tags=tags)
    B.box("die_anvil", dx, dy + ch / 2 + 0.085, 0.13, 0.05, 0.22, 0.245, S, bevel=0.006, tags=tags)
    # cavidade: leito preto + molde do carregador (contorno de aco em degrau)
    B.box("die_cav", dx, dy, cw, ch, 0.0, 0.035, M["black"], bevel=0.0, tags=tags)
    B.box("die_mold", dx, dy, cw - 0.02, ch - 0.02, 0.035, 0.045, KM, bevel=0.004, tags=tags)
    # graos enchendo a cavidade (de baixo para cima)
    if st["fill"] and not st["mag"]:
        # leito de enxofre subindo na cavidade (de baixo para cima) com torroes na frente do enchimento
        f = st["fill"] / 3.0
        hy_ = (ch - 0.03) * f
        B.box("die_fillb", dx, dy - (ch - 0.03) / 2 + hy_ / 2, cw - 0.03, hy_, 0.045, 0.07, Xm["sulfur"],
              bevel=0.006, tags=tags)
        y_top = dy - (ch - 0.03) / 2 + hy_
        H.grains("die_gr", [(dx - 0.07 + c * 0.047, y_top - 0.005) for c in range(4)], 0.07, 0.022, Xm["sulfur"],
                 tags, seed=21, mat2=Xm["sulfur_dk"])
    # carregador fundido (na cavidade ou descendo pela boca)
    if st["mag"]:
        H.mini_mag("die_mag", dx, dy - st["drop"], 0.045, M, Xm, tags, kind="he", s=MAG_S, cast=st["cast"])
    # portao de baixo: barra escura que desliza para a direita quando abre
    g = st["gate"]
    B.box("die_gate", dx + g * 0.20, dy - 0.135, cw + 0.02, 0.04, 0.10, 0.17, KM, bevel=0.006, tags=tags)
    B.box("die_gled", dx + g * 0.20, dy - 0.135, 0.06, 0.012, 0.17, 0.176,
          M["glow_dim"] if g > 0.5 else M["core_mid"], bevel=0.0, tags=tags)
    # fendas de pips nas bochechas (contador de enchimento a esquerda, temperatura a direita)
    fill_pips = [M["glow_dim"] if k < st["fill"] or st["mag"] else None for k in range(3)]
    H.ledslot("die_fl", dx - 0.195, dy + 0.0, 0.03, 0.14, 0.20, 3, M, tags, list(parts[0]), pw=0.014,
              pips=list(reversed(fill_pips)))
    hot = st["cast"]
    H.ledslot("die_tp", dx + 0.195, dy + 0.0, 0.03, 0.14, 0.20, 3, M, tags, list(parts[1]), pw=0.014,
              pips=[(M["glow"] if hot > 0.7 else M["glow_dim"]) if hot > t else None for t in (0.6, 0.3, 0.05)])
    for sx in (-1, 1):
        B.bolts(f"die_b{sx}", [(dx + sx * 0.20, dy - 0.12), (dx + sx * 0.20, dy + 0.135)], 0.27, 0.014, S,
                tags=tags)


def _ram(M, tags, st):
    """Cilindro hidraulico facetado + cabeca do martelo em seta descendo sobre a matriz."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    e = st["ram"]
    H.hcyl("cyl", CYL_Y0, CYL_Y1, RAM_X, 0.27, 0.15, M, tags, axis="Y",
           led_mat=M["glow"] if e > 0.9 else M["glow_dim"], collars=2)
    B.cyl("cyl_gland", RAM_X, CYL_Y0 - 0.008, 0.25, 0.085, 0.03, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    yf = RAM_IN + (RAM_OUT - RAM_IN) * e
    yb = yf + 0.10
    L = CYL_Y0 - yb
    if L > 0.01:
        B.cyl("ram_rod", RAM_X, yb + L / 2, 0.24, 0.045, L, S, axis="Y", verts=12, bevel=0.0, tags=tags)
    head = [(RAM_X - 0.06, yf), (RAM_X + 0.06, yf), (RAM_X + 0.13, yf + 0.05), (RAM_X + 0.13, yb),
            (RAM_X - 0.13, yb), (RAM_X - 0.13, yf + 0.05)]
    ra, rp = B.shard("ram", head, 0.08, 0.31, A, slope=0.035, groove=0.016, panel_h=0.02, tags=tags)
    H.ledslot("ram_sl", RAM_X, yf + 0.065, 0.11, 0.024, 0.27, 2, M, tags, [ra, rp], vertical=False, pw=0.012,
              pip_mat=M["glow"] if e > 0.9 else M["glow_dim"])
    # guias do martelo (barras de aco dos dois lados)
    for sx in (-1, 1):
        B.box(f"ram_gd{sx}", RAM_X + sx * 0.175, (RAM_OUT + CYL_Y1) / 2 - 0.02, 0.024, CYL_Y1 - RAM_OUT, 0.0, 0.16, S,
              bevel=0.004, tags=tags)
    if e > 0.99:
        hit = H.glow(Mo.ACCENTS["amber"], 3.5, "hit")
        B.box("hit", RAM_X, RAM_OUT - 0.004, 0.13, 0.01, 0.24, 0.255, hit, bevel=0.0, tags=tags)
        spark = H.glow((1.0, 0.30, 0.03), 6.0, "spark")
        for k, sx in enumerate((-1, 1)):
            B.rbox(f"spark{k}", RAM_X + sx * 0.12, RAM_OUT - 0.02, 0.055, 0.011, 0.30, 0.31, spark, rot=-sx * 25,
                   bevel=0.0, tags=tags)


def _outlet(M, tags, st):
    """Boca de saida embaixo da matriz: capuz escuro com labio de aco, guias e seta para baixo."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    B.box("ot_tr", OUT_X, 0.11, 0.28, 0.22, 0.0, 0.05, K, bevel=0.006, tags=tags)
    for g in (-1, 1):
        B.box(f"ot_g{g}", OUT_X + g * 0.15, 0.11, 0.024, 0.22, 0.0, 0.10, S, bevel=0.004, tags=tags)
    # capuz por cima da ultima parte da boca (o carregador some debaixo dele)
    hood = [(OUT_X - 0.165, 0.005), (OUT_X + 0.165, 0.005), (OUT_X + 0.165, 0.10), (OUT_X + 0.12, 0.13),
            (OUT_X - 0.12, 0.13), (OUT_X - 0.165, 0.10)]
    B.plate("ot_hood", hood, 0.13, 0.17, KM, slope=0.015, tags=tags)
    B.box("ot_lip", OUT_X, 0.125, 0.24, 0.02, 0.13, 0.18, S, bevel=0.005, tags=tags)
    H.chevron("ot_ar", OUT_X, 0.055, 270, M["glow_dim"], tags, z=0.17, s=0.7)


def _pump(M, tags, st):
    """Modulo de bomba hidraulica na faixa da direita: casca clara estreita, fenda de pips e mangueiras."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    poly = [(0.715, 0.20), (0.885, 0.20), (0.885, 0.80), (0.80, 0.885), (0.715, 0.885), (0.715, 0.62),
            (0.69, 0.59), (0.69, 0.235)]
    pa, pp = B.shard("pump", poly, 0.0, 0.29, A, slope=0.05, groove=0.022, panel_h=0.022, tags=tags)
    lit = st["i"] % 5
    H.ledslot("pump_sl", 0.80, 0.42, 0.03, 0.22, 0.24, 3, M, tags, [pa, pp], pw=0.014,
              pips=[M["glow_dim"] if k == (2 - lit % 3) else None for k in range(3)])
    H.vent("pump_v", 0.80, 0.745, 0.10, 0.12, 0.25, 0.30, M, tags, n=3, targets=[pa, pp])
    for k, y in enumerate((0.74, 0.82)):
        B.cyl(f"pump_h{k}", 0.65, y, 0.12, 0.016, 0.10, S, axis="X", verts=8, bevel=0.0, tags=tags)


def _accum(M, tags, st):
    """Acumuladores hidraulicos no vao entre a tremonha e a prensa: 2 tambores escuros deitados com aneis de aco,
    janela de contagem e mangueiras ate o cilindro do martelo (os detalhes mecanicos ficam no nucleo escuro)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    for k, y in enumerate((0.585, 0.78)):
        B.cyl(f"acc{k}", -0.035, y, 0.10, 0.072, 0.40, KM, axis="X", verts=8, bevel=0.008, tags=tags)
        for j, ox in enumerate((-0.16, -0.05, 0.06, 0.17)):
            B.cyl(f"accr{k}{j}", -0.035 + ox, y, 0.10, 0.078, 0.02, S, axis="X", verts=8, bevel=0.004, tags=tags)
        B.cyl(f"accc{k}", -0.035 - 0.215, y, 0.10, 0.05, 0.03, S, axis="X", verts=8, bevel=0.004, tags=tags)
    # janela de pressao no tambor de cima (pip acende na batida)
    B.box("acc_w", 0.005, 0.78, 0.07, 0.03, 0.165, 0.175, M["black"], bevel=0.0, tags=tags)
    B.box("acc_led", 0.005, 0.78, 0.04, 0.014, 0.175, 0.18, M["glow"] if st["ram"] > 0.9 else M["glow_dim"],
          bevel=0.0, tags=tags)
    # mangueiras ate o cilindro do martelo e suportes
    for k, y in enumerate((0.585, 0.78)):
        B.cyl(f"acc_h{k}", 0.215, y, 0.09, 0.016, 0.07, S, axis="X", verts=8, bevel=0.0, tags=tags)
    for k, x in enumerate((-0.20, 0.13)):
        B.box(f"acc_st{k}", x, 0.68, 0.035, 0.32, 0.0, 0.07, AM, bevel=0.006, tags=tags)


def machine(M, T="machine", phase=0.0):
    tags = (T,)
    Xm = H.X(M)
    st = _state(phase)
    B.plate("mc_bed", B.rpoly(0, 0.47, 1.80, 0.88, 0, chamfer=0.08), 0.0, 0.03, M["core_mid"], slope=0.01, tags=tags)
    _chute_in(M, Xm, tags, st)
    _hopper(M, Xm, tags, st)
    _auger(M, Xm, tags, st)
    _die(M, Xm, tags, st)
    _ram(M, tags, st)
    _outlet(M, tags, st)
    _pump(M, tags, st)
    _accum(M, tags, st)


# ============================================================================ teto
def roof(M, T="roof"):
    """Teto: placas verdes com escotilhas em seta (entra / sai) e a coroa blindada da prensa."""
    tags = (T,)
    green = H.roof_green()
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    deck = H.roof_deck(M, W, HH, T=T)
    H.roof_hatch("rf_in", M, -0.5, -0.5, 90, deck[(0, 1)], T=T)
    H.roof_hatch("rf_out", M, 0.5, -0.5, 270, deck[(1, 1)], T=T)
    # LEDs de sentido no vao entre as escotilhas
    B.box("rf_ledbed", 0, -0.5, 0.05, 0.24, 0.04, 0.075, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"rf_led{i}", 0, -0.58 + i * 0.08, 0.022, 0.03, 0.075, 0.082, M["glow_dim"], bevel=0.0, tags=tags)

    # ---- coroa sobre a fileira de cima: nucleo escuro de base
    base = [(-0.90, 0.10), (0.90, 0.10), (0.90, 0.86), (0.84, 0.92), (-0.84, 0.92), (-0.90, 0.86)]
    B.plate("cr_core", base, 0.05, 0.15, K, slope=0.02, tags=tags)

    # tampa da tremonha (esquerda): casca octogonal clara com o bocal de carga e 6 respiros radiais
    hx, hy = -0.53, 0.53
    lid = H.octo(hx, hy, 0.335)
    la, lp = B.shard("cr_lid", lid, 0.12, 0.32, A, slope=0.07, groove=0.03, panel_h=0.03, tags=tags)
    for k in range(6):
        a = 30 + 60 * k
        if k in (4,):
            continue
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        for q, t in enumerate((la, lp)):
            if t is not None:
                B.cut(t, [B.rbox(f"cr_rv{k}{q}", hx + ca * 0.22, hy + sa * 0.22, 0.10, 0.030, 0.30, 0.8, K, rot=a,
                                 bevel=0.0)])
        B.rbox(f"cr_rvb{k}", hx + ca * 0.22, hy + sa * 0.22, 0.10, 0.030, 0.295, 0.30, M["black"], rot=a, bevel=0.0,
               tags=tags)
    cap = H.octo(hx, hy, 0.12)
    B.plate("cr_cap", cap, 0.33, 0.39, AM, slope=0.02, tags=tags)
    B.cyl("cr_capk", hx, hy, 0.40, 0.04, 0.03, S, axis="Z", verts=8, bevel=0.006, tags=tags)
    B.box("cr_caph", hx, hy, 0.16, 0.026, 0.39, 0.41, S, bevel=0.004, tags=tags)
    # fenda de nivel do enxofre (4 pips) no bisel de baixo-direita da tampa
    H.ledslot("cr_lvl", hx + 0.19, hy - 0.19, 0.16, 0.032, 0.28, 4, M, tags, [la, lp], vertical=False, pw=0.016,
              pip_mat=M["glow_dim"], ang=-45)

    # torre da prensa (direita): espinha em seta apontando para a saida
    sx0 = 0.45
    spine = [(sx0 - 0.20, 0.905), (sx0 + 0.20, 0.905), (sx0 + 0.25, 0.855), (sx0 + 0.25, 0.36), (sx0 + 0.10, 0.12),
             (sx0 - 0.10, 0.12), (sx0 - 0.25, 0.36), (sx0 - 0.25, 0.855)]
    B.shard("cr_spine", spine, 0.12, 0.36, A, slope=0.08, groove=0.03, panel_h=0.03, tags=tags)
    sp2 = [(sx0 - 0.13, 0.83), (sx0 + 0.13, 0.83), (sx0 + 0.15, 0.80), (sx0 + 0.15, 0.42), (sx0 + 0.06, 0.27),
           (sx0 - 0.06, 0.27), (sx0 - 0.15, 0.42), (sx0 - 0.15, 0.80)]
    s2 = B.plate("cr_sp2", sp2, 0.39, 0.47, A, slope=0.03, tags=tags)
    # visor de contagem sobre a matriz (4 pips ambar = municoes do carregador)
    win = B.rpoly(sx0, 0.405, 0.17, 0.045, 0, chamfer=0.012)
    B.cut(s2, [B.loft("cr_winc", win, win, 0.41, 0.7, K, bevel=0.0)])
    B.loft("cr_winbed", win, win, 0.405, 0.415, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"cr_cnt{i}", sx0 - 0.045 + i * 0.045, 0.405, 0.024, 0.02, 0.415, 0.421, M["glow"], bevel=0.0,
              tags=tags)
    # fendas de respiro transversais na tampa do martelo
    for i in range(4):
        yv = 0.62 + i * 0.05
        B.cut(s2, [B.box(f"cr_slc{i}", sx0, yv, 0.15, 0.022, 0.41, 0.7, K, bevel=0.0)])
        B.box(f"cr_slb{i}", sx0, yv, 0.15, 0.022, 0.405, 0.415, M["black"], bevel=0.0, tags=tags)
    for sxx in (-1, 1):
        B.box(f"cr_rail{sxx}", sx0 + sxx * 0.167, 0.62, 0.026, 0.40, 0.36, 0.405, S, bevel=0.008, tags=tags)
        for yb in (0.43, 0.81):
            B.box(f"cr_stop{sxx}{yb}", sx0 + sxx * 0.167, yb, 0.042, 0.03, 0.36, 0.42, KM, bevel=0.006, tags=tags)
    # ombreira da direita (respiro) e lamina diagonal ligando a tampa a torre
    paul = [(0.745, 0.905), (0.875, 0.905), (0.875, 0.30), (0.80, 0.22), (0.745, 0.30)]
    pa, pp = B.shard("cr_paul", paul, 0.12, 0.30, A, slope=0.05, groove=0.022, panel_h=0.022, tags=tags)
    H.vent("cr_pv", 0.81, 0.72, 0.075, 0.20, 0.25, 0.30, M, tags, n=4, targets=[pa, pp])
    H.ledslot("cr_psl", 0.81, 0.45, 0.034, 0.18, 0.25, 3, M, tags, [pa, pp], pw=0.018, pip_mat=M["glow_dim"])
    blade = [(-0.17, 0.30), (0.06, 0.30), (0.20, 0.17), (0.20, 0.12), (-0.04, 0.12), (-0.17, 0.24)]
    ba, bp = B.shard("cr_blade", blade, 0.12, 0.26, A, slope=0.04, groove=0.018, panel_h=0.018, tags=tags)
    for q, t in enumerate((ba, bp)):
        if t is not None:
            B.cut(t, [B.rbox(f"cr_bc{q}", 0.02, 0.21, 0.16, 0.03, 0.21, 0.6, K, rot=-25, bevel=0.0)])
    B.rbox("cr_bbed", 0.02, 0.21, 0.16, 0.03, 0.205, 0.215, M["black"], rot=-25, bevel=0.0, tags=tags)
    B.rbox("cr_bglow", 0.02, 0.21, 0.11, 0.011, 0.215, 0.221, M["glow_dim"], rot=-25, bevel=0.0, tags=tags)
    # duto da tremonha para a torre (a rosca por baixo)
    B.cyl("cr_duct", -0.08, 0.40, 0.17, 0.05, 0.22, KM, axis="X", verts=8, bevel=0.006, tags=tags)
    for k, x in enumerate((-0.15, -0.01)):
        B.cyl(f"cr_dr{k}", x, 0.40, 0.17, 0.056, 0.02, S, axis="X", verts=8, bevel=0.004, tags=tags)
    B.bolts("cr_b", [(-0.85, 0.87), (0.85, 0.15), (-0.85, 0.15)], 0.15, 0.016, S, tags=tags)
    H.roof_unpaint(T)
