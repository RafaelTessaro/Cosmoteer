"""F5 Fabrica de Ogivas Nucleares (Nuclear Warhead Factory) 4x4 - a Ogiva Nuclear da Iara (spec 2.0, factories F5).

ID novo rafaeltessaro.bs_factory_warhead; modelo derivado da Fundicao de Projeteis Nucleares 1.x
(parts/bs_factory_shell_nuke.py: celula quente com vidro de chumbo e 2 manipuladores). Grade (vanilla factory_nuke
4x4): maquina = fileiras 0-1 + [1,2], [2,2]; ENTRADAS ferro [0,2] (esquerda) e uranio [3,2] (direita); SAIDA = a
fileira de baixo inteira ([0,3,4,1]). Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade =
1 quadro. Destaque verde: LEDs e o nucleo em verde saturado de forca baixa (STYLE 9); sem faixas de perigo e sem
amarelo (o trevo so aparece embutido na propria ogiva, recurso nuclear, STYLE 7).

Maquinario:
  * CELULA QUENTE (meio, fileiras 0-1): parede grossa clara em degraus com a JANELA de vidro de chumbo (poco
    escuro esverdeado, reflexos em diagonal, labio de aco), dentro dela a mesa giratoria com a ogiva aberta e o
    poco do nucleo; portas de transferencia nos dois lados da janela;
  * 2 MANIPULADORES (os da 1.x, maiores): torre do ombro blindada na parede, braco e antebraco de casca clara
    sobre viga escura, cotovelo com LED, garra de 2 dedos. O da direita traz o NUCLEO verde das centrifugas, o da
    esquerda traz a TAMPA da ogiva do torno;
  * TORNO DE CARCACAS (coluna esquerda, sobre a base de ferro): janela com a carcaca girando e a ferramenta;
    calha do ferro;
  * CASCATA DE CENTRIFUGAS (coluna direita, sobre a base de uranio): 3 centrifugas octogonais (rotor girando,
    LED verde de rotacao); calha do uranio;
  * ECLUSA + BERCO DE SAIDA (celulas [1,2], [2,2]): a ogiva pronta desce da celula quente pela eclusa (porta que
    abre), assenta no berco com grampos e sai para a fileira de saida (setas verdes).
Animacao: 12 quadros x 0,125 s = 1,5 s = metade do ciclo de 3,0 s (2 voltas por ogiva): 0 ogiva aberta na mesa,
garras nas portas | 1-3 o braco direito poe o nucleo (o poco pulsa) | 3-5 o braco esquerdo poe a tampa | 5 solda
(lampejo verde nas costuras) | 6 os bracos voltam | 7-8 a eclusa abre e a ogiva desce | 9-10 a ogiva no berco
desce para a saida | 11 carcaca nova na mesa, nucleo e tampa novos nas portas.
Teto: placas verdes; tampa da celula quente sem pintura em degraus com visor e fendas de LED verde; tampas das
colunas (centrifugas = 3 calotas octogonais; torno = capo com respiro); cinta de cofre sobre o berco de saida;
escotilhas em seta nas entradas e na saida.
"""

import math

import bs3d as B
import models as Mo
from parts import _bs2_fabricas_helpers as H

PART = {
    "id": "rafaeltessaro.bs_factory_warhead",
    "kind": "factory",
    "size": [4, 4],
    "accent": "green",
    "machine_frames": 12,
    "machine_interval": 0.125,
}

W, HH = PART["size"]
NF = PART["machine_frames"]
WC = (0.0, 1.12)               # centro da janela / mesa giratoria
WIN = (1.08, 0.80)             # janela de vidro de chumbo (largura, altura)
WH_S = 1.15                    # escala da ogiva (0.25 x 0.36 quadro)
SH = (-1.18, 1.36)             # ombro do manipulador esquerdo (o direito e o espelho)
L1, L2, LC = 0.50, 0.52, 0.15
PORT = (-0.66, 1.12)           # ponta da garra esquerda na porta de transferencia
CAP_AT = (-0.03, 1.27)         # ponta da garra esquerda sobre o nariz da ogiva
CORE_AT = (0.06, 1.12)         # ponta da garra direita sobre o poco do nucleo
CRADLE_Y = -0.52               # berco de saida

META_EXTRA = {
    "factory_code": "F5",
    "name_ptbr": "Fábrica de Ogivas Nucleares",
    "grid": {"blocked": [[0, 0], [1, 0], [2, 0], [3, 0], [0, 1], [1, 1], [2, 1], [3, 1], [1, 2], [2, 2]],
             "inputs": {"iron": [0, 2, 1, 1], "uranium": [3, 2, 1, 1]}, "outputs": {"msl_nuke": [0, 3, 4, 1]}},
    "notes": ["12 quadros x 0,125 s = 1,5 s = metade do ciclo de 3,0 s (2 voltas por ogiva)"],
}


# ============================================================================ estado
def _state(phase):
    i = int(round(phase * NF)) % NF
    return {
        "i": i,
        "R": [0.0, 0.45, 0.85, 1.0, 0.55, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0][i],   # braco direito: porta -> poco
        "L": [0.0, 0.0, 0.35, 0.75, 1.0, 0.6, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0][i],   # braco esquerdo: porta -> nariz
        "Rhold": i in (0, 1, 2, 11),
        "Lhold": i in (0, 1, 2, 3, 11),
        "Ropen": i in (3, 4, 5, 6, 7, 8, 9, 10),
        "Lopen": i in (4, 5, 6, 7, 8, 9, 10),
        "stage": [1, 1, 1, 2, 2, 3, 3, 3, None, None, None, 1][i],                 # ogiva na mesa
        "drop": {7: 0.0, 8: 0.0}.get(i),
        "lock": {7: 0.5, 8: 1.0, 9: 0.5}.get(i, 0.0),                              # porta da eclusa
        "low_y": {8: 0.08, 9: CRADLE_Y, 10: CRADLE_Y - 0.26}.get(i),              # ogiva descendo / no berco
        "clamp": i == 9,
        "flash": {5: 1.0, 6: 0.35}.get(i, 0.0),
        "pit": [0.8, 1.0, 1.4, 1.7, 1.1, 0.8, 0.7, 0.6, 0.6, 0.7, 0.8, 0.8][i],
        "spin": i * 30.0,
    }


def _extra(st=None):
    pit = st["pit"] if st else 0.8
    fl = st["flash"] if st else 0.0
    return {
        "led": B.mat_glow("f5_led", (0.32, 1.0, 0.0), 0.75),
        "led_lo": B.mat_glow("f5_led_lo", (0.32, 1.0, 0.0), 0.35),
        "pit": B.mat_glow("f5_pit", (0.30, 1.0, 0.14), 0.18 + 0.30 * min(pit, 1.6)),
        "core": B.mat_glow("f5_core", (0.30, 1.0, 0.12), 1.1),
        "flash": B.mat_glow("f5_flash", (0.35, 1.0, 0.16), 0.4 + 1.6 * fl),
        "wbed": B.mat_metal("f5_wbed", (0.006, 0.020, 0.012), rough=0.45, metal=0.2),
        "glint": B.mat_paint("f5_glint", (0.42, 0.50, 0.47), rough=0.15, metal=0.0, wear=0.0, grime=0.0, scale=4),
        "lead": B.mat_metal("f5_lead", (0.075, 0.08, 0.085), rough=0.55, metal=0.5),
        "mid": B.mat_paint("f5_mid", (0.26, 0.268, 0.28), rough=0.5, metal=0.3, wear=0.0, grime=0.05, scale=4),
        "wfloor": B.mat_metal("f5_wfloor", (0.030, 0.052, 0.040), rough=0.38, metal=0.8),
    }


def _link(p0, p1, w0, w1, c=0.03, ext0=0.0, ext1=0.0):
    """Elo afunilado de p0 a p1 (larguras w0 -> w1) com cantos chanfrados (copia da 1.x)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1e-9
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    a = (p0[0] - ux * ext0, p0[1] - uy * ext0)
    b = (p1[0] + ux * ext1, p1[1] + uy * ext1)

    def P(o, u, n):
        return (o[0] + ux * u + nx * n, o[1] + uy * u + ny * n)
    return [P(a, c, w0 / 2), P(b, -c, w1 / 2), P(b, 0, w1 / 2 - c), P(b, 0, -w1 / 2 + c), P(b, -c, -w1 / 2),
            P(a, c, -w0 / 2), P(a, 0, -w0 / 2 + c), P(a, 0, w0 / 2 - c)]


def _ik(S, T, side):
    dx, dy = T[0] - S[0], T[1] - S[1]
    d = min(math.hypot(dx, dy), L1 + L2 + LC - 1e-4)
    a = math.atan2(dy, dx)
    c = (L1 * L1 + d * d - (L2 + LC) ** 2) / (2 * L1 * d)
    b = math.acos(max(-1.0, min(1.0, c)))
    ae = a + side * b
    E = (S[0] + L1 * math.cos(ae), S[1] + L1 * math.sin(ae))
    fa = math.atan2(T[1] - E[1], T[0] - E[0])
    Wp = (E[0] + L2 * math.cos(fa), E[1] + L2 * math.sin(fa))
    return E, Wp, fa


# ============================================================================ piso
def floor(M, T="floor"):
    machine = {(i, j) for i in range(4) for j in range(2)} | {(1, 2), (2, 2)}
    pads = {(0, 2): 90, (3, 2): 90, (1, 3): (270, 90), (2, 3): (270, 90), (0, 3): None, (3, 3): None}
    H.floor_grid(M, W, HH, machine, pads, T=T, rail_rows=(3,))


# ============================================================================ maquina: celula quente
WALL = [(-0.92, 1.88), (0.92, 1.88), (0.98, 1.82), (0.98, 0.72), (0.62, 0.30), (-0.62, 0.30), (-0.98, 0.72),
        (-0.98, 1.82)]
STEP = [(-0.80, 1.80), (0.80, 1.80), (0.86, 1.74), (0.86, 0.78), (0.56, 0.42), (-0.56, 0.42), (-0.86, 0.78),
        (-0.86, 1.74)]


def _hotcell(M, Xm, X, tags, st):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    wx, wy = WC
    B.plate("hc_core", B.offset_poly(WALL, -0.03), 0.0, 0.18, K, slope=0.02, tags=tags)
    wa, wp = B.shard("hc_wall", WALL, 0.0, 0.40, A, slope=0.08, groove=0.035, panel_h=0.03, tags=tags)
    fa, fp = B.shard("hc_step", STEP, 0.40, 0.50, A, slope=0.04, groove=0.018, panel_h=0.022, tags=tags)
    w_out = B.rpoly(wx, wy, WIN[0] + 0.08, WIN[1] + 0.08, 0, chamfer=0.12)
    w_in = B.rpoly(wx, wy, WIN[0], WIN[1], 0, chamfer=0.10)
    for k, t in enumerate((fa, fp)):
        if t is not None:
            B.cut(t, [B.loft(f"hc_fh{k}", w_out, w_out, 0.36, 0.9, K, bevel=0.0)])
    for k, t in enumerate((wa, wp)):
        if t is not None:
            B.cut(t, [B.loft(f"hc_wh{k}", w_in, w_in, 0.14, 0.9, K, bevel=0.0)])
    B.loft("hc_wbed", w_in, w_in, 0.13, 0.145, X["wbed"], bevel=0.0, tags=tags)
    # mesa giratoria: base escura, anel claro segmentado, poco do nucleo (verde que pulsa)
    B.plate("tt_base", H.octo(wx, wy, 0.30), 0.145, 0.19, KM, slope=0.012, tags=tags)
    for k in range(8):
        a = 22.5 + 45 * k + st["i"] * 3.0
        seg = [(wx + math.cos(math.radians(a + d)) * r, wy + math.sin(math.radians(a + d)) * r)
               for r, d in ((0.22, -18), (0.29, -18), (0.29, 18), (0.22, 18))]
        B.shard(f"tt_seg{k}", seg, 0.19, 0.24, AM, slope=0.012, groove=0.006, panel_h=0.008, tags=tags)
    B.plate("tt_pit", H.octo(wx, wy, 0.20), 0.19, 0.205, K, slope=0.006, tags=tags)
    # sulco do poco em volta da mesa: fio verde que pulsa com o nucleo (forca baixa, so a linha)
    groove = B.plate("tt_groove", H.octo(wx, wy, 0.335), 0.145, 0.165, M["black"], slope=0.004, tags=tags)
    B.cut(groove, [B.loft("tt_groovec", H.octo(wx, wy, 0.305), H.octo(wx, wy, 0.305), 0.1, 0.3, K, bevel=0.0)])
    ring = B.plate("tt_ring", H.octo(wx, wy, 0.325), 0.165, 0.17, X["pit"], slope=0.002, tags=tags)
    B.cut(ring, [B.loft("tt_ringc", H.octo(wx, wy, 0.315), H.octo(wx, wy, 0.315), 0.1, 0.3, K, bevel=0.0)])
    # trilhos da janela e pincas laterais (a mesa corre neles)
    for k in (-1, 1):
        B.box(f"hc_irail{k}", wx, wy + k * (WIN[1] / 2 - 0.03), WIN[0] - 0.10, 0.03, 0.145, 0.19, KM, bevel=0.004,
              tags=tags)
    # ogiva na mesa (aberta / com nucleo / fechada), nariz para +Y
    if st["stage"] is not None:
        H.mini_warhead("tt_wh", wx, wy - 0.02, 0.205, M, Xm, tags, s=WH_S, stage=st["stage"],
                       glow_k=0.9 if st["stage"] == 2 else 1.0)
    if st["flash"] > 0:
        for k, dy in enumerate((0.04, -0.07)):
            B.box(f"hc_weld{k}", wx, wy - 0.02 + dy * WH_S, 0.24 * WH_S, 0.010, 0.45, 0.455, X["flash"], bevel=0.0,
                  tags=tags)
    # reflexos do vidro (riscos em diagonal no canto de cima a esquerda)
    for k, (d, ln) in enumerate(((0.0, 0.22), (0.05, 0.11))):
        gx, gy = wx - 0.40 + d * 0.707, wy + 0.27 - d * 0.707
        B.rbox(f"hc_glint{k}", gx, gy, ln, 0.010, 0.47, 0.475, X["glint"], rot=45, bevel=0.0, tags=tags)
    lip = B.plate("hc_wlip", B.rpoly(wx, wy, WIN[0] + 0.06, WIN[1] + 0.055, 0, chamfer=0.11), 0.44, 0.50, S,
                  slope=0.012, bevel=0.004, tags=tags)
    B.cut(lip, [B.loft("hc_wlc", w_in, w_in, 0.2, 0.7, K, bevel=0.0)])
    B.bolts("hc_wb", [(wx + dx * (WIN[0] / 2 + 0.005), wy + dy * (WIN[1] / 2 + 0.005)) for dx in (-1, 1)
                      for dy in (-1, 1)], 0.50, 0.016, KM, tags=tags)
    # moldura: fendas de pips verdes nos lados, linha de painel em cima, fenda na cunha de baixo
    if fp is not None:
        # linhas de painel na moldura (STYLE 1.8: uma quebra a cada 0,3-0,5 quadro): faixa de cima, lados e cunha de
        # baixo partidas em placas menores
        cuts = [B.box("hc_tpl", wx, 1.71, 0.90, 0.024, 0.48, 0.9, K, bevel=0.0)]
        for sx in (-1, 1):
            cuts.append(B.box(f"hc_tv{sx}", sx * 0.30, 1.69, 0.022, 0.24, 0.48, 0.9, K, bevel=0.0))
            cuts.append(B.box(f"hc_sh{sx}", sx * 0.735, 1.24, 0.30, 0.022, 0.48, 0.9, K, bevel=0.0))
            cuts.append(B.box(f"hc_sl{sx}", sx * 0.735, 0.86, 0.30, 0.022, 0.48, 0.9, K, bevel=0.0))
            cuts.append(B.box(f"hc_bv{sx}", sx * 0.30, 0.55, 0.022, 0.24, 0.48, 0.9, K, bevel=0.0))
            cuts.append(B.rbox(f"hc_bd{sx}", sx * 0.67, 0.62, 0.20, 0.022, 0.48, 0.9, K, rot=-sx * 50, bevel=0.0))
        B.cut(fp, cuts)
    for sx in (-1, 1):
        H.vent(f"hc_sv{sx}", sx * 0.725, 1.05, 0.14, 0.24, 0.44, 0.50, M, tags, n=3, targets=[fa, fp])
    for sx in (-1, 1):
        H.ledslot(f"hc_side{sx}", sx * 0.78, 1.42, 0.034, 0.24, 0.46, 3, M, tags, [fa, fp], pip_mat=X["led_lo"],
                  pw=0.016)
        B.bolts(f"hc_fb{sx}", [(sx * 0.80, 1.75), (sx * 0.78, 0.86)], 0.53, 0.017, S, tags=tags)
    H.ledslot("hc_tip", 0.0, 0.55, 0.30, 0.036, 0.46, 4, M, tags, [fa, fp], vertical=False, pw=0.016,
              pips=[X["led"] if st["lock"] > 0 else X["led_lo"], None, None, X["led_lo"]])
    # portas de transferencia nos lados da janela (recesso escuro com guias de aco)
    for sx in (-1, 1):
        port = B.rpoly(sx * 0.66, wy, 0.16, 0.20, 0, chamfer=0.03)
        for k, t in enumerate((wa, wp)):
            if t is not None:
                B.cut(t, [B.loft(f"hc_port{sx}{k}", port, port, 0.20, 0.9, K, bevel=0.0)])
        B.loft(f"hc_pbed{sx}", port, port, 0.19, 0.20, M["black"], bevel=0.0, tags=tags)
        for j in (-1, 1):
            B.box(f"hc_pg{sx}{j}", sx * 0.66, wy + j * 0.10, 0.17, 0.022, 0.20, 0.34, S, bevel=0.004, tags=tags)


def _core(name, x, y, z, ang, M, X, tags, s=1.0):
    """Nucleo verde (capsula octogonal brilhante) com colares escuros (copia da 1.x)."""
    ln, w = 0.11 * s, 0.05 * s
    p = H.rot(B.rpoly(0, 0, ln, w, 0, chamfer=0.016 * s), ang, x, y)
    B.loft(name, p, p, z, z + 0.04, X["core"], bevel=0.0, tags=tags)
    for k, e in enumerate((-1, 1)):
        q = H.rot(B.rpoly(e * ln * 0.42, 0, 0.022 * s, w + 0.012, 0), ang, x, y)
        B.loft(f"{name}_cap{k}", q, q, z - 0.005, z + 0.048, M["core_mid"], bevel=0.003, tags=tags)


def _nosecap(name, x, y, z, ang, M, Xm, tags):
    """Tampa (nariz) da ogiva carregada pela garra: cone claro com ponta escura."""
    a = math.radians(ang)
    B.cyl(name, x, y, z, 0.075, 0.12, M["armor"], axis="Y", verts=12, bevel=0.004, tags=tags, r2=0.028,
          yaw=ang - 90)
    B.cyl(name + "_t", x + math.cos(a) * 0.07, y + math.sin(a) * 0.07, z, 0.03, 0.02, M["core_mid"], axis="Y",
          verts=12, bevel=0.0, tags=tags, r2=0.015, yaw=ang - 90)


def _arm(prefix, sx, t, hold, opened, M, Xm, X, tags):
    """Manipulador remoto (da 1.x); t = 0 na porta, 1 no alvo; hold = 'core' | 'cap' | None."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    S0 = (sx * -SH[0], SH[1])
    p0 = (sx * -PORT[0], PORT[1])
    p1 = CAP_AT if sx < 0 else CORE_AT
    T = (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
    E, Wp, fa = _ik(S0, T, -sx)
    ua = math.degrees(math.atan2(E[1] - S0[1], E[0] - S0[0]))
    ur = math.radians(ua)
    B.plate(f"{prefix}_shub", H.octo(*S0, 0.12, ua + 22.5), 0.52, 0.58, S, slope=0.015, bevel=0.005, tags=tags)
    B.plate(f"{prefix}_ubeam", _link(S0, E, 0.20, 0.15, 0.035, 0.07, 0.07), 0.54, 0.60, KM, slope=0.012, tags=tags)
    ua_, up = B.shard(f"{prefix}_uarm", _link(S0, E, 0.165, 0.125, 0.04, -0.05, -0.085), 0.59, 0.68, A,
                      slope=0.03, groove=0.012, panel_h=0.018, tags=tags)
    mx, my = S0[0] + math.cos(ur) * L1 * 0.45, S0[1] + math.sin(ur) * L1 * 0.45
    H.ledslot(f"{prefix}_usl", mx, my, 0.14, 0.034, 0.60, 2, M, tags, [ua_, up], vertical=False,
              pip_mat=X["led_lo"], ang=ua)
    B.plate(f"{prefix}_spin", H.octo(*S0, 0.065, ua), 0.68, 0.72, S, slope=0.012, bevel=0.004, tags=tags)
    B.plate(f"{prefix}_elb", H.octo(*E, 0.085, ua), 0.52, 0.71, S, slope=0.016, bevel=0.005, tags=tags)
    B.plate(f"{prefix}_elbc", H.octo(*E, 0.046, ua), 0.71, 0.73, KM, slope=0.008, bevel=0.003, tags=tags)
    B.cyl(f"{prefix}_elbled", E[0], E[1], 0.733, 0.016, 0.006, X["led_lo"], axis="Z", verts=8, bevel=0.0, tags=tags)
    fad = math.degrees(fa)
    ux, uy = math.cos(fa), math.sin(fa)
    nx, ny = -uy, ux
    B.plate(f"{prefix}_fbeam", _link(E, Wp, 0.14, 0.10, 0.03, 0.0, 0.035), 0.46, 0.52, KM, slope=0.01, tags=tags)
    B.shard(f"{prefix}_farm", _link(E, Wp, 0.115, 0.085, 0.03, -0.10, -0.045), 0.51, 0.59, A, slope=0.024,
            groove=0.012, panel_h=0.014, tags=tags)
    for k in (-1, 1):
        mxx, myy = (E[0] + Wp[0]) / 2 + nx * k * 0.066, (E[1] + Wp[1]) / 2 + ny * k * 0.066
        B.rbox(f"{prefix}_fhyd{k}", mxx, myy, L2 * 0.66, 0.018, 0.49, 0.52, S, rot=fad, bevel=0.003, tags=tags)
    B.plate(f"{prefix}_wrist", H.octo(*Wp, 0.055, fad), 0.43, 0.57, S, slope=0.014, bevel=0.004, tags=tags)
    B.rbox(f"{prefix}_palm", Wp[0] + ux * 0.045, Wp[1] + uy * 0.045, 0.04, 0.14, 0.43, 0.52, KM, rot=fad,
           bevel=0.005, tags=tags)
    g = 0.064 if opened else (0.048 if hold else 0.036)
    for k in (-1, 1):
        bx, by = Wp[0] + ux * 0.085 + nx * k * g, Wp[1] + uy * 0.085 + ny * k * g
        B.rbox(f"{prefix}_fing{k}", bx, by, 0.11, 0.036, 0.43, 0.51, S, rot=fad, bevel=0.006, tags=tags)
        tx_, ty_ = Wp[0] + ux * 0.15 + nx * k * (g - 0.016), Wp[1] + uy * 0.15 + ny * k * (g - 0.016)
        B.rbox(f"{prefix}_tip{k}", tx_, ty_, 0.058, 0.030, 0.43, 0.515, A, rot=fad - k * 32, bevel=0.005, tags=tags)
    if hold == "core":
        _core(f"{prefix}_core", Wp[0] + ux * 0.10, Wp[1] + uy * 0.10, 0.445, fad + 90, M, X, tags)
    elif hold == "cap":
        _nosecap(f"{prefix}_cap", Wp[0] + ux * 0.10, Wp[1] + uy * 0.10, 0.44, fad, M, Xm, tags)


def _shoulder(prefix, sx, M, X, tags):
    """Torre do ombro na parede (tampao blindado com entalhes), como na 1.x."""
    K, KM, A, S = M["core"], M["core_mid"], M["armor"], M["steel"]
    S0 = (sx * -SH[0], SH[1])
    B.plate(f"{prefix}_sbase", H.octo(*S0, 0.25), 0.0, 0.42, K, slope=0.02, tags=tags)
    sa, sp = B.shard(f"{prefix}_sring", H.octo(*S0, 0.235), 0.40, 0.50, A, slope=0.04, groove=0.02, panel_h=0.02,
                     tags=tags)
    for k in range(4):
        a = 45 + 90 * k
        cx, cy = S0[0] + math.cos(math.radians(a)) * 0.20, S0[1] + math.sin(math.radians(a)) * 0.20
        for q, t in enumerate((sa, sp)):
            if t is not None:
                B.cut(t, [B.rbox(f"{prefix}_sn{k}{q}", cx, cy, 0.024, 0.09, 0.46, 0.8, K, rot=a + 90, bevel=0.0)])
    B.plate(f"{prefix}_sdisk", H.octo(*S0, 0.13), 0.48, 0.53, KM, slope=0.012, tags=tags)


# ============================================================================ maquina: colunas laterais
COL = [(-1.92, 1.82), (-1.82, 1.92), (-1.47, 1.92), (-1.41, 1.86), (-1.41, 0.32), (-1.47, 0.26), (-1.92, 0.26)]
BLADE = [(-1.92, 0.06), (-1.10, 0.06), (-1.04, 0.12), (-1.04, 0.22), (-1.92, 0.22)]


def _column(prefix, sx, M, Xm, X, tags):
    """Casca clara da coluna lateral (lado sx) e lamina de baixo com a boca de entrada (setas verdes)."""
    f = H.flip(sx)
    K, A, S, KM = M["core"], M["armor"], M["steel"], M["core_mid"]
    ca, cp = B.shard(prefix, f(COL), 0.0, 0.40, X["mid"], slope=0.05, groove=0.022, panel_h=0.024, tags=tags)
    ba, bp = B.shard(prefix + "_bl", f(BLADE), 0.0, 0.28, A, slope=0.035, groove=0.016, panel_h=0.02, tags=tags)
    H.ledslot(prefix + "_in", sx * 1.50, 0.14, 0.30, 0.06, 0.12, 0, M, tags, [ba, bp], vertical=False)
    for k in range(3):
        H.chevron(f"{prefix}_inchv{k}", sx * (1.40 + k * 0.10), 0.14, 90, X["led_lo"], tags, z=0.128, s=0.38)
    B.bolts(prefix + "_b", [(sx * 1.86, 1.86), (sx * 1.47, 1.86)], 0.43, 0.017, S, tags=tags)
    # entre a coluna e a parede da celula quente: dutos verticais de refrigeracao, caixa de valvulas com LED e o
    # conduite que entra na parede por cima do ombro
    for k, x in enumerate((1.25, 1.33)):
        B.cyl(f"{prefix}_pipe{k}", sx * x, 0.62, 0.10, 0.026, 0.70, KM, axis="Y", verts=8, bevel=0.004, tags=tags)
        for j, y in enumerate((0.36, 0.84)):
            B.cyl(f"{prefix}_pclamp{k}{j}", sx * x, y, 0.10, 0.032, 0.025, S, axis="Y", verts=8, bevel=0.004,
                  tags=tags)
    vb = B.rpoly(sx * 1.20, 0.60, 0.20, 0.22, 0, chamfer=0.04)
    va, vp = B.shard(prefix + "_vb", vb, 0.0, 0.26, A, slope=0.03, groove=0.014, panel_h=0.016, tags=tags)
    H.ledslot(prefix + "_vbl", sx * 1.20, 0.60, 0.10, 0.032, 0.22, 2, M, tags, [va, vp], vertical=False, pw=0.014,
              pips=[X["led_lo"], None])
    B.cyl(prefix + "_cond", sx * 1.18, 1.75, 0.22, 0.045, 0.40, KM, axis="X", verts=8, bevel=0.006, tags=tags)
    for j, x in enumerate((1.04, 1.30)):
        B.cyl(f"{prefix}_condr{j}", sx * x, 1.75, 0.22, 0.052, 0.025, S, axis="X", verts=8, bevel=0.004, tags=tags)
    return ca, cp


def _lathe(M, Xm, X, tags, st):
    """Torno de carcacas (coluna esquerda): janela com a carcaca girando e a ferramenta."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    ca, cp = _column("la", -1, M, Xm, X, tags)
    hole = [(-1.84, 0.42), (-1.50, 0.42), (-1.50, 1.62), (-1.84, 1.62)]
    H.bezel("la_win", hole, B.offset_poly(hole, 0.02), 0.20, 0.40, M, tags, (ca, cp))
    x = -1.67
    # fundo do poco: piso grafite esverdeado (nao um buraco preto), trilhos-guia do carro da ferramenta, travessas e
    # frestas verdes fracas num rebaixo
    B.box("la_floor", x, 1.02, 0.32, 1.18, 0.20, 0.212, X["wfloor"], bevel=0.0, tags=tags)
    for k, sx in enumerate((-1, 1)):
        B.box(f"la_rail{k}", x + sx * 0.14, 1.02, 0.022, 1.14, 0.212, 0.24, S, bevel=0.004, tags=tags)
        B.box(f"la_sk{k}", x + sx * 0.115, 1.02, 0.024, 0.98, 0.210, 0.215, K, bevel=0.0, tags=tags)
        B.box(f"la_sg{k}", x + sx * 0.115, 1.02, 0.010, 0.94, 0.215, 0.218, X["led_lo"], bevel=0.0, tags=tags)
    for k, yy in enumerate((0.47, 1.57)):
        B.box(f"la_tie{k}", x, yy, 0.30, 0.04, 0.212, 0.245, KM, bevel=0.005, tags=tags)
    B.box("la_head", x, 1.52, 0.22, 0.10, 0.20, 0.32, KM, bevel=0.01, tags=tags)
    B.box("la_tail", x, 0.52, 0.14, 0.06, 0.20, 0.30, KM, bevel=0.01, tags=tags)
    B.cyl("la_body", x, 1.0, 0.30, 0.10, 0.84, A, axis="Y", verts=12, bevel=0.006, tags=tags)
    for k in range(5):
        yy = 0.62 + ((k * 0.155 + st["i"] / NF * 0.155 * 4) % 0.78)
        B.cyl(f"la_seam{k}", x, yy, 0.30, 0.102, 0.01, K, axis="Y", verts=12, bevel=0.0, tags=tags)
    ty = 0.66 + 0.70 * (0.5 - 0.5 * math.cos(2 * math.pi * st["i"] / NF))
    B.box("la_tool", x + 0.12, ty, 0.08, 0.06, 0.25, 0.34, S, bevel=0.008, tags=tags)
    B.box("la_tip", x + 0.09, ty, 0.03, 0.014, 0.30, 0.33, Xm["silver"], bevel=0.0, tags=tags)


def _centrifuges(M, Xm, X, tags, st):
    """Cascata de 3 centrifugas (coluna direita): calotas octogonais claras, rotor girando, LED verde."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    ca, cp = _column("cf", 1, M, Xm, X, tags)
    for k, y in enumerate((0.58, 1.02, 1.46)):
        cx = 1.665
        hole = H.octo(cx, y, 0.165)
        for q, t in enumerate((ca, cp)):
            if t is not None:
                B.cut(t, [B.loft(f"cf_h{k}{q}", hole, hole, 0.10, 0.9, K, bevel=0.0)])
        B.plate(f"cf_base{k}", H.octo(cx, y, 0.16), 0.08, 0.14, K, slope=0.01, tags=tags)
        B.plate(f"cf_cup{k}", H.octo(cx, y, 0.135), 0.14, 0.30, A, slope=0.025, tags=tags)
        B.plate(f"cf_top{k}", H.octo(cx, y, 0.09), 0.30, 0.33, KM, slope=0.01, tags=tags)
        H.rotor(f"cf_rot{k}", cx, y, 0.33, 0.15, st["spin"] + k * 40, M, tags, blades=3, w=0.022)
        B.cyl(f"cf_led{k}", cx + 0.10, y - 0.10, 0.30, 0.016, 0.01,
              X["led"] if (st["i"] + k * 4) % 12 < 6 else X["led_lo"], axis="Z", verts=8, bevel=0.0, tags=tags)
    # duto da cascata ate a porta direita da celula quente (o nucleo enriquecido)
    B.cyl("cf_duct", 1.12, 1.12, 0.22, 0.05, 0.28, KM, axis="X", verts=8, bevel=0.006, tags=tags)
    B.cyl("cf_ductr", 1.12, 1.12, 0.22, 0.058, 0.03, S, axis="X", verts=8, bevel=0.004, tags=tags)


# ============================================================================ maquina: eclusa e berco
def _output(M, Xm, X, tags, st):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.plate("ot_block", B.rpoly(0, -0.5, 1.90, 0.94, 0, chamfer=0.14), 0.0, 0.04, K, slope=0.012, tags=tags)
    # eclusa: moldura escura na borda de baixo da celula quente com a porta de 2 folhas
    B.plate("lk_fr", B.rpoly(0, 0.16, 0.46, 0.30, 0, chamfer=0.05), 0.0, 0.14, KM, slope=0.012, tags=tags)
    o = 0.11 * st["lock"]
    for sx in (-1, 1):
        B.box(f"lk_d{sx}", sx * (0.085 + o), 0.16, 0.17, 0.26, 0.14, 0.20, AM, bevel=0.008, tags=tags)
    B.box("lk_pit", 0, 0.16, 0.30, 0.24, 0.13, 0.14, M["black"], bevel=0.0, tags=tags)
    # calha e berco de saida
    B.plate("ot_tr", B.rpoly(0, -0.42, 0.46, 0.92, 0, chamfer=0.05), 0.03, 0.07, KM, slope=0.012, tags=tags)
    B.box("ot_well", 0, -0.42, 0.36, 0.86, 0.065, 0.072, M["black"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"ot_rail{sx}", sx * 0.19, -0.42, 0.024, 0.88, 0.04, 0.10, S, bevel=0.004, tags=tags)
        # capuzes claros dos lados com respiro e fenda de LED; grampos que fecham com a ogiva no berco
        hood = H.flip(sx)([(-0.92, -0.08), (-0.40, -0.08), (-0.30, -0.18), (-0.30, -0.80), (-0.40, -0.90),
                           (-0.92, -0.90)])
        ha, hp = B.shard(f"ot_h{sx}", hood, 0.0, 0.32, A, slope=0.05, groove=0.022, panel_h=0.024, tags=tags)
        H.vent(f"ot_v{sx}", sx * 0.66, -0.30, 0.30, 0.22, 0.27, 0.32, M, tags, n=4, targets=[ha, hp])
        H.ledslot(f"ot_sl{sx}", sx * 0.66, -0.66, 0.30, 0.034, 0.28, 4, M, tags, [ha, hp], vertical=False, pw=0.016,
                  pips=[X["led"] if st["clamp"] else X["led_lo"], None, None, X["led_lo"]])
        cg = 0.0 if st["clamp"] else 0.04
        B.box(f"ot_clamp{sx}", sx * (0.235 + cg), CRADLE_Y, 0.07, 0.14, 0.06, 0.24, S, bevel=0.01, tags=tags)
    for k, x in enumerate((-0.10, 0.10)):
        H.chevron(f"ot_ar{k}", x, -0.94, 270, X["led_lo"], tags, z=0.072, s=0.55)
    if st["low_y"] is not None:
        H.mini_warhead("ot_wh", 0, st["low_y"], 0.07, M, Xm, tags, s=WH_S, stage=3)


def machine(M, T="machine", phase=0.0):
    tags = (T,)
    Xm = H.X(M)
    st = _state(phase)
    X = _extra(st)
    B.plate("mc_bed", B.rpoly(0, 1.0, 3.84, 1.86, 0, chamfer=0.10), 0.0, 0.05, M["core"], slope=0.01, tags=tags)
    _output(M, Xm, X, tags, st)
    _hotcell(M, Xm, X, tags, st)
    _lathe(M, Xm, X, tags, st)
    _centrifuges(M, Xm, X, tags, st)
    for sx in (-1, 1):
        _shoulder(f"sh{sx}", sx, M, X, tags)
    _arm("aL", -1, st["L"], "cap" if st["Lhold"] else None, st["Lopen"], M, Xm, X, tags)
    _arm("aR", 1, st["R"], "core" if st["Rhold"] else None, st["Ropen"], M, Xm, X, tags)


# ============================================================================ teto
def roof(M, T="roof"):
    tags = (T,)
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    X = _extra()
    led = X["led"]
    deck = H.roof_deck(M, W, HH, skip={(1, 0), (2, 0), (1, 1), (2, 1)}, T=T)
    H.roof_hatch("rf_in0", M, -1.5, -0.5, 90, deck[(0, 2)], T=T, led_mat=led)
    H.roof_hatch("rf_in1", M, 1.5, -0.5, 90, deck[(3, 2)], T=T, led_mat=led)
    for i in range(4):
        cx, cy = H.cell_xy(W, HH, i, 3)
        H.roof_hatch(f"rf_out{i}", M, cx, cy, 270, deck[(i, 3)], T=T, led_mat=led, s=0.9)
    # tampa da celula quente (4 celulas do meio de cima): base escura, 2 degraus claros, visor com fenda verde
    base = [(-0.96, 1.92), (0.96, 1.92), (0.98, 1.90), (0.98, 0.10), (0.96, 0.08), (-0.96, 0.08), (-0.98, 0.10),
            (-0.98, 1.90)]
    B.plate("lid_core", base, 0.0, 0.10, K, slope=0.02, tags=tags)
    lid = [(-0.88, 1.86), (0.88, 1.86), (0.94, 1.80), (0.94, 0.62), (0.56, 0.16), (-0.56, 0.16), (-0.94, 0.62),
           (-0.94, 1.80)]
    la, lp = B.shard("lid", lid, 0.08, 0.30, A, slope=0.08, groove=0.035, panel_h=0.03, tags=tags)
    lid2 = [(-0.62, 1.70), (0.62, 1.70), (0.70, 1.62), (0.70, 0.86), (0.36, 0.46), (-0.36, 0.46), (-0.70, 0.86),
            (-0.70, 1.62)]
    l2a, l2p = B.shard("lid2", lid2, 0.32, 0.44, A, slope=0.04, groove=0.02, panel_h=0.022, tags=tags)
    vis = B.rpoly(0, 1.30, 0.70, 0.16, 0, chamfer=0.05)
    for q, t in enumerate((l2a, l2p)):
        if t is not None:
            B.cut(t, [B.loft(f"lid_vc{q}", vis, vis, 0.36, 0.9, K, bevel=0.0)])
    B.loft("lid_vbed", vis, vis, 0.35, 0.36, X["wbed"], bevel=0.0, tags=tags)
    for k in range(5):
        B.box(f"lid_vl{k}", -0.24 + k * 0.12, 1.30, 0.06, 0.03, 0.36, 0.366, led if k == 2 else X["led_lo"],
              bevel=0.0, tags=tags)
    for sx in (-1, 1):
        H.ledslot(f"lid_sl{sx}", sx * 0.52, 0.98, 0.034, 0.30, 0.40, 3, M, tags, [l2a, l2p], pw=0.016, pip_mat=led)
        H.vent(f"lid_v{sx}", sx * 0.80, 1.40, 0.14, 0.40, 0.25, 0.30, M, tags, n=5, targets=[la, lp])
        B.bolts(f"lid_b{sx}", [(sx * 0.84, 1.78), (sx * 0.84, 0.70), (sx * 0.30, 0.24)], 0.30, 0.018, S, tags=tags)
    # trevo de 3 cunhas claras no degrau de baixo (emblema nuclear sem amarelo e sem faixa de perigo)
    tc = (0.0, 0.90)
    B.plate("lid_tbase", H.octo(tc[0], tc[1], 0.22), 0.43, 0.46, K, slope=0.01, tags=tags)
    for k in range(3):
        a = 90 + 120 * k
        pts = [(tc[0] + math.cos(math.radians(a + d)) * r, tc[1] + math.sin(math.radians(a + d)) * r)
               for r, d in ((0.055, -24), (0.19, -27), (0.19, 27), (0.055, 24))]
        B.shard(f"lid_tw{k}", pts, 0.45, 0.52, AM, slope=0.012, groove=0.006, panel_h=0.008, tags=tags)
    B.cyl("lid_th", tc[0], tc[1], 0.50, 0.035, 0.05, KM, axis="Z", verts=8, bevel=0.006, tags=tags)
    B.cyl("lid_tl", tc[0], tc[1], 0.527, 0.016, 0.006, led, axis="Z", verts=8, bevel=0.0, tags=tags)
    # colunas: capo do torno (esquerda) e 3 calotas das centrifugas (direita) sobre as placas verdes
    for sx in (-1, 1):
        for j in (0, 1):
            pa, pp = deck[(0 if sx < 0 else 3, j)]
        cap = H.flip(sx)([(-1.86, 1.84), (-1.10, 1.84), (-1.10, 0.18), (-1.86, 0.18)])
        if sx < 0:
            ha, hp = B.shard("rf_lathe", B.rpoly(-1.48, 1.0, 0.70, 1.60, 0, chamfer=0.12), 0.06, 0.24, A,
                             slope=0.05, groove=0.022, panel_h=0.022, tags=tags)
            H.vent("rf_lv", -1.48, 1.30, 0.40, 0.40, 0.19, 0.24, M, tags, n=5, targets=[ha, hp])
            H.ledslot("rf_ll", -1.48, 0.62, 0.34, 0.036, 0.19, 3, M, tags, [ha, hp], vertical=False, pw=0.016,
                      pip_mat=led)
        else:
            ra, rp = B.shard("rf_cfrack", B.rpoly(1.50, 1.02, 0.74, 1.66, 0, chamfer=0.12), 0.04, 0.14,
                             M["armor_mid"], slope=0.03, groove=0.016, panel_h=0.016, tags=tags)
            for k, y in enumerate((0.55, 1.02, 1.49)):
                cx = 1.48
                hole = H.octo(cx, y, 0.215)
                for q, t in enumerate((ra, rp)):
                    if t is not None:
                        B.cut(t, [B.loft(f"rf_cfh{k}{q}", hole, hole, 0.08, 0.6, K, bevel=0.0)])
                B.plate(f"rf_cfk{k}", H.octo(cx, y, 0.21), 0.04, 0.10, K, slope=0.01, tags=tags)
                ca, cp = B.shard(f"rf_cf{k}", H.octo(cx, y, 0.19), 0.08, 0.26, A, slope=0.04, groove=0.018,
                                 panel_h=0.02, tags=tags)
                for j in range(4):
                    a = 45 + 90 * j
                    px_, py_ = cx + math.cos(math.radians(a)) * 0.13, y + math.sin(math.radians(a)) * 0.13
                    for q, t in enumerate((ca, cp)):
                        if t is not None:
                            B.cut(t, [B.rbox(f"rf_cfn{k}{j}{q}", px_, py_, 0.02, 0.07, 0.22, 0.6, K, rot=a + 90,
                                             bevel=0.0)])
                B.cyl(f"rf_cfc{k}", cx, y, 0.29, 0.06, 0.05, KM, axis="Z", verts=8, bevel=0.006, tags=tags)
                B.cyl(f"rf_cfl{k}", cx, y, 0.318, 0.02, 0.006, led, axis="Z", verts=8, bevel=0.0, tags=tags)
            B.box("rf_cfbar", 1.80, 1.02, 0.05, 1.30, 0.14, 0.20, S, bevel=0.01, tags=tags)
    # cinta de cofre sobre o berco de saida (celulas [1,2], [2,2]): segmentos claros com dobradicas
    for k, (x0, x1) in enumerate(((-0.92, -0.10), (0.10, 0.92))):
        st_ = B.rpoly((x0 + x1) / 2, -0.50, x1 - x0, 0.30, 0, chamfer=0.06)
        sa, sp = B.shard(f"rf_strap{k}", st_, 0.06, 0.20, A, slope=0.035, groove=0.016, panel_h=0.018, tags=tags)
        H.ledslot(f"rf_ss{k}", (x0 + x1) / 2, -0.50, 0.40, 0.034, 0.16, 4, M, tags, [sa, sp], vertical=False,
                  pw=0.016, pip_mat=X["led_lo"])
    B.plate("rf_lock", H.octo(0, -0.50, 0.12), 0.06, 0.26, AM, slope=0.02, tags=tags)
    B.cyl("rf_lockl", 0, -0.50, 0.265, 0.03, 0.008, led, axis="Z", verts=8, bevel=0.0, tags=tags)
    for k, y in enumerate((-0.16, -0.84)):
        B.box(f"rf_hinge{k}", 0, y, 0.16, 0.06, 0.06, 0.16, S, bevel=0.01, tags=tags)
    H.roof_unpaint(T)
