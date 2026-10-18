"""Prensa de Carregadores (Magazine Press) 2x2 - empacota 5 balas de canhao em 1 Carregador Padrao.

Layout fixo das regras (tools/bsgen/factory.py): fileira de cima = maquinario (bloqueado para a tripulacao);
fileira de baixo = grade de ENTRADA no tile da esquerda e de SAIDA no tile da direita, onde o jogo desenha as
pilhas de recursos. Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade = 1 tile.

Maquinario (fileira de cima), na linguagem da familia (nucleo escuro + lascas claras com bisel duplo):
  * esteira de alimentacao: as balas de canhao saem da tampa esquerda e andam ate a ponte da matriz;
  * prensa hidraulica: ombreiras claras em garra flanqueiam o corredor do martelo; o martelo (bloco claro com
    face escura) avanca e bate na ponte da matriz; a janela da matriz mostra as balas entrando (1..5);
  * esteira de saida: carregadores prontos saem da matriz e somem sob a tampa direita, rumo a grade de saida;
  * rotores nas tampas das pontas, luzes ambar de estado em fendas escuras.
A animacao (phase 0..1) e um ciclo da prensa: carrega 5 balas, avanca o martelo, bate, recua e ejeta.
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_factory_mag_std",
    "kind": "factory",
    "size": [2, 2],
    "accent": "amber",
    "machine_frames": 10,
    "machine_interval": 0.125,     # 10 x 0.125 s = 1.25 s = intervalo da receita
}

# geometria compartilhada (fileira de cima: y em [0, 1])
BELT_Y0, BELT_Y1 = 0.10, 0.37      # faixa da esteira
BELT_YC = (BELT_Y0 + BELT_Y1) / 2
DIE_X = 0.25                       # meia largura da ponte da matriz
CAP_X = 0.62                       # inicio das tampas das pontas
RAM_FRONT_IN, RAM_FRONT_OUT = 0.61, 0.437   # frente do martelo recolhido / batendo
RAM_D = 0.17                       # profundidade do martelo
HOUSING_Y = 0.785                  # face da carcaca do cilindro


def _brass():
    return B.mat_metal("brass", (0.66, 0.44, 0.12), rough=0.28, metal=1.0)


def _ram_ext(phase):
    """Extensao do martelo (0 = recolhido, 1 = batendo) ao longo do ciclo de 10 quadros."""
    tab = [0.0, 0.0, 0.0, 0.0, 0.0, 0.55, 1.0, 0.92, 0.5, 0.16]
    return tab[int(round(phase * 10)) % 10]


def _loaded(phase):
    """Balas dentro da matriz (janela de contagem): 1..5 carregando, 5 na batida, 0 depois da ejecao."""
    tab = [1, 2, 3, 4, 5, 5, 5, 5, 0, 0]
    return tab[int(round(phase * 10)) % 10]


def _round(name, x, y, z, r, L, M, brass, tags, yaw=0.0):
    """Bala de canhao deitada ao longo de Y (estojo de latao + ogiva de aco escuro apontando para +Y)."""
    lc = L * 0.62
    B.cyl(name + "_case", x, y - L / 2 + lc / 2, z, r, lc, brass, axis="Y", verts=10, bevel=0.0, tags=tags)
    B.cyl(name + "_rim", x, y - L / 2 + 0.008, z, r * 1.08, 0.016, M["steel"], axis="Y", verts=10, bevel=0.0,
          tags=tags)
    lt = L - lc
    B.cyl(name + "_tip", x, y - L / 2 + lc + lt / 2, z, r * 0.92, lt, M["armor_mid"], axis="Y", verts=10,
          bevel=0.0, tags=tags, r2=r * 0.32)


def _mini_mag(name, x, y, M, tags):
    """Carregador Padrao em miniatura na esteira de saida (casco claro, janela de latao, LED ambar, alca)."""
    A, K, S = M["armor"], M["core"], M["steel"]
    z0 = 0.10
    B.plate(name + "_core", B.rpoly(x, y, 0.27, 0.205, 0, chamfer=0.035), z0, z0 + 0.08, K, slope=0.012,
            tags=tags)
    sh = B.plate(name + "_sh", B.rpoly(x - 0.025, y, 0.20, 0.215, 0, chamfer=0.04), z0 + 0.02, z0 + 0.13, A,
                 slope=0.022, tags=tags)
    B.cut(sh, [B.box(name + "_w", x - 0.035, y + 0.035, 0.12, 0.05, z0 + 0.10, z0 + 0.3, K, bevel=0.0)])
    B.box(name + "_wb", x - 0.035, y + 0.035, 0.12, 0.05, z0 + 0.095, z0 + 0.10, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.cyl(f"{name}_br{i}", x - 0.07 + i * 0.035, y + 0.035, z0 + 0.105, 0.012, 0.045, _brass(), axis="Y",
              verts=8, bevel=0.0, tags=tags)
    B.box(name + "_led", x - 0.06, y - 0.055, 0.05, 0.016, z0 + 0.125, z0 + 0.135, M["glow"], bevel=0.0, tags=tags)
    B.plate(name + "_cap", B.rpoly(x + 0.105, y, 0.05, 0.19, 0, chamfer=0.015), z0 + 0.02, z0 + 0.12, A,
            slope=0.012, tags=tags)
    B.box(name + "_hdl", x + 0.105, y, 0.022, 0.13, z0 + 0.13, z0 + 0.15, S, bevel=0.004, tags=tags)


# ============================================================================ piso
def floor(M, T="floor"):
    """Piso: poco escuro com grade sob a maquina; berços de entrada/saida com cantoneiras claras e LEDs."""
    tags = (T,)
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.box("fl_base", 0, 0, 2, 2, -0.05, 0.0, K, bevel=0.0, tags=tags)
    # fileira de cima: poco da maquina (moldura escura e grade de aco)
    pit = B.plate("fl_pit", B.rpoly(0, 0.5, 1.92, 0.92, 0, chamfer=0.06), 0.0, 0.03, KM, slope=0.01, tags=tags)
    B.cut(pit, [B.box("fl_pitc", 0, 0.5, 1.80, 0.80, 0.0, 0.2, K, bevel=0.0)])
    B.box("fl_pitbed", 0, 0.5, 1.80, 0.80, -0.01, 0.002, M["black"], bevel=0.0, tags=tags)
    for i in range(11):
        B.box(f"fl_grate{i}", -0.85 + i * 0.17, 0.5, 0.025, 0.80, 0.0, 0.015, KM, bevel=0.0, tags=tags)
    # fileira de baixo: um berço por grade (entrada esquerda, saida direita)
    for side, cx in (("in", -0.5), ("out", 0.5)):
        cy = -0.5
        B.plate(f"fl_tray_{side}", B.rpoly(cx, cy, 0.92, 0.92, 0, chamfer=0.07), 0.0, 0.025, KM, slope=0.01,
                tags=tags)
        B.loft(f"fl_trayin_{side}", B.rpoly(cx, cy, 0.76, 0.78, 0, chamfer=0.05),
               B.rpoly(cx, cy, 0.76, 0.78, 0, chamfer=0.05), 0.025, 0.032, K, bevel=0.0, tags=tags)
        # grade da pilha (2 x 2) em relevo fino
        B.box(f"fl_tgv_{side}", cx, cy, 0.012, 0.70, 0.032, 0.038, KM, bevel=0.0, tags=tags)
        B.box(f"fl_tgh_{side}", cx, cy, 0.70, 0.012, 0.032, 0.038, KM, bevel=0.0, tags=tags)
        # cantoneiras claras em L nos quatro cantos (vaos escuros entre elas)
        for qx in (-1, 1):
            for qy in (-1, 1):
                ox, oy = cx + qx * 0.41, cy + qy * 0.41
                poly = [(ox, oy), (ox - qx * 0.24, oy), (ox - qx * 0.24, oy - qy * 0.07), (ox - qx * 0.07,
                        oy - qy * 0.07), (ox - qx * 0.07, oy - qy * 0.24), (ox, oy - qy * 0.24)]
                B.shard(f"fl_br_{side}{qx}{qy}", poly, 0.0, 0.06, AM, slope=0.012, groove=0.008, panel_h=0.012,
                        tags=tags)
        # LEDs nos vaos de cima e de baixo (recesso escuro)
        for qy in (-1, 1):
            B.box(f"fl_ledbed_{side}{qy}", cx, cy + qy * 0.42, 0.22, 0.05, 0.02, 0.035, M["black"], bevel=0.0,
                  tags=tags)
            B.box(f"fl_led_{side}{qy}", cx, cy + qy * 0.42, 0.10, 0.018, 0.035, 0.042, M["glow_dim"], bevel=0.0,
                  tags=tags)
    # divisoria central entre as grades: barra de aco com parafusos
    B.box("fl_div", 0, -0.5, 0.06, 0.80, 0.0, 0.05, S, bevel=0.01, tags=tags)
    B.bolts("fl_divb", [(0, -0.22), (0, -0.78)], 0.05, 0.016, KM, tags=tags)


# ============================================================================ maquinario (animado)
def machine(M, T="machine", phase=0.0):
    tags = (T,)
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    brass = _brass()
    fi = int(round(phase * 10)) % 10

    # ---------------------------------------------------------------- esteira (base, trilhos, lona)
    B.box("bt_bed", 0, BELT_YC, 1.70, BELT_Y1 - BELT_Y0 + 0.04, 0.0, 0.08, KM, bevel=0.008, tags=tags)
    B.box("bt_lona", 0, BELT_YC, 1.70, BELT_Y1 - BELT_Y0 - 0.02, 0.08, 0.095, M["black"], bevel=0.0, tags=tags)
    for sy in (BELT_Y0, BELT_Y1):
        B.box(f"bt_rail{sy}", 0, sy, 1.70, 0.025, 0.06, 0.14, S, bevel=0.006, tags=tags)
    # esteira de entrada: taliscas + balas (anda 2 passos por ciclo)
    p_in = 0.095
    s_in = (phase * 2.0) % 1.0
    for k in range(-1, 6):
        x = -CAP_X - 0.05 + (k + s_in) * p_in
        if x > -DIE_X + 0.04:
            continue
        B.box(f"bt_cl{k}", x, BELT_YC, 0.012, BELT_Y1 - BELT_Y0 - 0.03, 0.095, 0.11, S, bevel=0.0, tags=tags)
        xr = x + p_in / 2
        if xr < -DIE_X + 0.02:
            _round(f"bt_rd{k}", xr, BELT_YC, 0.135, 0.033, 0.22, M, brass, tags)
    # esteira de saida: taliscas + carregadores prontos (anda 1 carregador por ciclo)
    p_out = 0.38
    s_out = (phase - 0.75) % 1.0
    p_c = p_out / 3
    for j in range(-1, 6):
        xc = DIE_X + (j + (s_out * 3) % 1.0) * p_c
        if DIE_X - 0.03 < xc < CAP_X + 0.03:
            B.box(f"bt_co{j}", xc, BELT_YC, 0.012, BELT_Y1 - BELT_Y0 - 0.03, 0.095, 0.11, S, bevel=0.0, tags=tags)
    for k in range(-1, 2):
        xm = 0.12 + (k + s_out) * p_out
        if DIE_X - 0.16 < xm < CAP_X + 0.16:
            _mini_mag(f"mm{k}", xm, BELT_YC, M, tags)

    # ---------------------------------------------------------------- ponte da matriz (tunel sobre a esteira)
    die = [(-DIE_X, 0.08), (-DIE_X + 0.05, 0.035), (DIE_X - 0.05, 0.035), (DIE_X, 0.08), (DIE_X, 0.40),
           (DIE_X - 0.04, 0.435), (-DIE_X + 0.04, 0.435), (-DIE_X, 0.40)]
    B.plate("die_core", B.rpoly(0, 0.235, 2 * DIE_X + 0.05, 0.36, 0, chamfer=0.04), 0.0, 0.18, KM, slope=0.02,
            tags=tags)
    da, dp = B.shard("die", die, 0.10, 0.30, A, slope=0.045, groove=0.025, panel_h=0.025, tags=tags)
    # janela de contagem: balas entrando no carregador (1..5)
    wx0, wx1, wy0, wy1 = -0.165, 0.165, 0.19, 0.33
    for t in (da, dp):
        B.cut(t, [B.box(f"die_wc{id(t) % 7}", 0, (wy0 + wy1) / 2, wx1 - wx0, wy1 - wy0, 0.20, 0.6, K, bevel=0.0)])
    B.box("die_wbed", 0, (wy0 + wy1) / 2, wx1 - wx0, wy1 - wy0, 0.20, 0.205, M["black"], bevel=0.0, tags=tags)
    n = _loaded(phase)
    for i in range(min(n, 5)):
        _round(f"die_rd{i}", -0.128 + i * 0.064, (wy0 + wy1) / 2, 0.229, 0.024, 0.13, M, brass, tags)
    # contador ambar (pips acesos = balas carregadas) numa fenda escura abaixo da janela
    Mo.slot_with_pips("die_sl", 0.125, -0.16, 0.16, 0.035, 0.325, 5, M, tags, target=[da, dp], depth=0.075,
                      vertical=False)
    for i in range(5):
        ob = B.bpy.data.objects.get(f"die_sl_pip{i}")
        if ob is not None and i >= n:
            ob.data.materials[0] = M["core_mid"]

    # ---------------------------------------------------------------- tampas das pontas (rotores)
    for sx in (-1, 1):
        cap = [(sx * CAP_X, 0.06), (sx * (CAP_X + 0.06), 0.03), (sx * 0.86, 0.03), (sx * 0.89, 0.07),
               (sx * 0.89, 0.40), (sx * 0.85, 0.44), (sx * (CAP_X + 0.05), 0.44), (sx * CAP_X, 0.39)]
        ca, cp = B.shard(f"cap{sx}", cap if sx < 0 else Mo.mirror(cap), 0.0, 0.30, A, slope=0.045, groove=0.025,
                         panel_h=0.025, tags=tags)
        rx, ry = sx * 0.755, 0.29
        rec = B.rpoly(rx, ry, 0.17, 0.17, 0, chamfer=0.05)
        for t in (ca, cp):
            B.cut(t, [B.loft(f"cap_rc{sx}{id(t) % 7}", rec, rec, 0.19, 0.6, K, bevel=0.0)])
        B.loft(f"cap_rbed{sx}", rec, rec, 0.19, 0.20, M["black"], bevel=0.0, tags=tags)
        # rotor de 3 pas (gira 1/3 de volta por ciclo... x3 = uma volta)
        ang = sx * phase * 360.0
        for b in range(3):
            a = ang + b * 120
            ca_, sa_ = math.cos(math.radians(a)), math.sin(math.radians(a))
            B.rbox(f"rot{sx}{b}", rx + ca_ * 0.038, ry + sa_ * 0.038, 0.068, 0.028, 0.20, 0.23, S, rot=a,
                   bevel=0.004, tags=tags)
        B.cyl(f"rot_hub{sx}", rx, ry, 0.235, 0.026, 0.03, KM, axis="Z", verts=12, bevel=0.004, tags=tags)
        # fenda de estado vertical na tampa
        Mo.slot_with_pips(f"cap_sl{sx}", 0.125, sx * 0.69, sx * 0.82, 0.035, 0.325, 3, M, tags, target=[ca, cp],
                          depth=0.07, vertical=False, pip_mat=M["glow_dim"])
        # bico de entrada/saida na borda de baixo (calha escura com guias de aco e seta ambar)
        B.box(f"chute{sx}", sx * 0.70, -0.005, 0.26, 0.11, 0.0, 0.06, K, bevel=0.006, tags=tags)
        for gx in (-1, 1):
            B.box(f"chute_g{sx}{gx}", sx * 0.70 + gx * 0.12, -0.005, 0.025, 0.12, 0.0, 0.09, S, bevel=0.004,
                  tags=tags)
        d = 1 if sx < 0 else -1   # entrada aponta para dentro (+Y), saida aponta para fora (-Y)
        chev = [(sx * 0.70 - 0.06, -0.005 - d * 0.02), (sx * 0.70, -0.005 + d * 0.025),
                (sx * 0.70 + 0.06, -0.005 - d * 0.02), (sx * 0.70 + 0.06, -0.005 - d * 0.04),
                (sx * 0.70, -0.005 + d * 0.005), (sx * 0.70 - 0.06, -0.005 - d * 0.04)]
        B.loft(f"chute_ar{sx}", chev, chev, 0.06, 0.068, M["glow_dim"], bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- carcaca da prensa: ombreiras em garra
    sh = [(-0.88, 0.875), (-0.31, 0.875), (-0.275, 0.84), (-0.275, 0.53), (-0.31, 0.465), (-0.47, 0.465),
          (-0.56, 0.52), (-0.84, 0.52), (-0.88, 0.56)]
    for sx, f in ((-1, lambda p: p), (1, Mo.mirror)):
        sa, sp = B.shard(f"shl{sx}", f(sh), 0.0, 0.40, A, slope=0.07, groove=0.035, panel_h=0.03, tags=tags)
        Mo.slot_with_pips(f"shl_sl{sx}", 0.745, sx * 0.72, sx * 0.46, 0.045, 0.43, 4, M, tags, target=[sa, sp],
                          depth=0.075, vertical=False)
        # pips do cacador: um aceso forte por quadro, os outros fracos
        # (o slot_with_pips ja criou pips "glow"; troca o material dos que nao estao no passo atual)
        for i in range(4):
            ob = B.bpy.data.objects.get(f"shl_sl{sx}_pip{i}")
            if ob is not None and i != (fi % 4 if sx < 0 else 3 - fi % 4):
                ob.data.materials[0] = M["glow_dim"]
        # linhas de painel
        if sp is not None:
            B.cut(sp, [B.rbox(f"shl_pl{sx}{i}", sx * x, y, ln, 0.014, 0.38, 0.6, K, rot=r, bevel=0.0)
                       for i, (x, y, ln, r) in enumerate(((0.58, 0.665, 0.30, 0), (0.43, 0.62, 0.12, sx * -55)))])
        # mangueiras hidraulicas no vao entre ombreira e esteira
        B.cyl(f"hose{sx}", sx * 0.45, 0.44, 0.07, 0.022, 0.30, S, axis="X", verts=8, bevel=0.0, tags=tags)
        B.cyl(f"hosec{sx}", sx * 0.31, 0.44, 0.07, 0.03, 0.04, KM, axis="X", verts=8, bevel=0.0, tags=tags)

    # carcaca do cilindro (nucleo escuro) no fundo do corredor do martelo
    B.box("hsg", 0, (HOUSING_Y + 0.88) / 2, 0.55, 0.88 - HOUSING_Y + 0.02, 0.0, 0.30, KM, bevel=0.012, tags=tags)
    B.cyl("hsg_cyl", 0, (HOUSING_Y + 0.88) / 2, 0.30, 0.085, 0.09, S, axis="Y", verts=8, bevel=0.01, tags=tags)
    for sx in (-1, 1):
        B.cyl(f"hsg_g{sx}", sx * 0.16, HOUSING_Y + 0.02, 0.18, 0.04, 0.05, S, axis="Y", verts=8, bevel=0.006,
              tags=tags)
    B.bolts("hsg_b", [(-0.23, 0.85), (0.23, 0.85)], 0.30, 0.018, S, tags=tags)
    # trilhos do corredor do martelo (piso do corredor)
    B.box("lane", 0, (RAM_FRONT_OUT + HOUSING_Y) / 2, 0.50, HOUSING_Y - RAM_FRONT_OUT, 0.0, 0.05, K, bevel=0.0,
          tags=tags)
    for sx in (-1, 1):
        B.box(f"lane_r{sx}", sx * 0.20, (RAM_FRONT_OUT + HOUSING_Y) / 2, 0.03, HOUSING_Y - RAM_FRONT_OUT, 0.05,
              0.07, S, bevel=0.004, tags=tags)

    # ---------------------------------------------------------------- martelo (animado)
    e = _ram_ext(phase)
    yf = RAM_FRONT_IN + (RAM_FRONT_OUT - RAM_FRONT_IN) * e
    yb = yf + RAM_D
    ram = [(-0.165, yf), (0.165, yf), (0.215, yf + 0.04), (0.215, yb), (-0.215, yb), (-0.215, yf + 0.04)]
    B.box("ram_face", 0, yf + 0.012, 0.32, 0.03, 0.06, 0.24, K, bevel=0.004, tags=tags)
    ra, rp = B.shard("ram", ram, 0.07, 0.30, A, slope=0.04, groove=0.02, panel_h=0.025, tags=tags)
    Mo.slot_with_pips("ram_sl", yf + 0.085, -0.10, 0.10, 0.04, 0.325, 3, M, tags, target=[ra, rp], depth=0.07,
                      vertical=False, pip_mat=M["glow"] if e > 0.9 else M["glow_dim"])
    # hastes: principal + guias (aparecem quando o martelo avanca)
    L = HOUSING_Y - yb
    if L > 0.01:
        B.cyl("ram_rod", 0, yb + L / 2, 0.18, 0.045, L, S, axis="Y", verts=12, bevel=0.0, tags=tags)
        for sx in (-1, 1):
            B.cyl(f"ram_gr{sx}", sx * 0.16, yb + L / 2, 0.15, 0.022, L, S, axis="Y", verts=10, bevel=0.0, tags=tags)
    # batida: faisca ambar curta no encontro martelo/matriz
    if e > 0.99:
        B.box("hit", 0, 0.437, 0.40, 0.012, 0.20, 0.22, M["glow"], bevel=0.0, tags=tags)
        for i, (x, a) in enumerate(((-0.26, 25), (0.27, -30), (-0.30, -15), (0.31, 18))):
            B.rbox(f"spark{i}", x, 0.44 + (i % 2) * 0.02, 0.05, 0.008, 0.25, 0.26, M["glow_dim"], rot=a, bevel=0.0,
                   tags=tags)


# ============================================================================ teto
def roof(M, T="roof"):
    """Teto: placas verdes (pintura da nave) e, sobre a prensa, uma coroa blindada clara sem pintura."""
    tags = (T,)
    green = B.mat_roof_green()
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.box("rf_under", 0, 0, 2, 2, -0.05, 0.02, K, bevel=0.0, tags=tags)
    for tx in range(2):
        for ty in range(2):
            cx, cy = tx - 0.5, 0.5 - ty
            _, pnl = B.shard(f"rf{tx}{ty}", B.rpoly(cx, cy, 0.94, 0.94, 0, chamfer=0.07), 0.0, 0.06, green,
                             slope=0.025, groove=0.05, panel_h=0.02, tags=tags)
            if ty == 1 and pnl is not None:
                B.cut(pnl, [B.rbox(f"rf_dl{tx}", cx - (tx * 2 - 1) * 0.2, cy - 0.2, 0.012, 0.42, 0.07, 0.2, K,
                                   rot=(tx * 2 - 1) * 45, bevel=0.0)])
    # escotilhas das grades: entrada (seta para dentro) e saida (seta para fora)
    for sx in (-1, 1):
        cx, cy = sx * 0.5, -0.56
        h = B.plate(f"rf_hatch{sx}", B.rpoly(cx, cy, 0.46, 0.40, 0, chamfer=0.09), 0.06, 0.11, AM, slope=0.02,
                    tags=tags)
        d = 1 if sx < 0 else -1
        chev = [(cx - 0.11, cy - d * 0.03), (cx, cy + d * 0.07), (cx + 0.11, cy - d * 0.03),
                (cx + 0.11, cy - d * 0.085), (cx, cy + d * 0.015), (cx - 0.11, cy - d * 0.085)]
        B.cut(h, [B.loft(f"rf_chc{sx}", chev, chev, 0.08, 0.3, K, bevel=0.0)])
        B.loft(f"rf_chb{sx}", chev, chev, 0.075, 0.082, M["black"], bevel=0.0, tags=tags)
        B.box(f"rf_hh{sx}", cx, cy - 0.15, 0.20, 0.04, 0.11, 0.135, S, bevel=0.008, tags=tags)
        B.bolts(f"rf_hb{sx}", [(cx - 0.18, cy + 0.14), (cx + 0.18, cy + 0.14)], 0.11, 0.016, S, tags=tags)
    # LED de sentido no vao entre as escotilhas
    B.box("rf_ledbed", 0, -0.56, 0.05, 0.22, 0.04, 0.07, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"rf_led{i}", 0, -0.63 + i * 0.07, 0.022, 0.03, 0.07, 0.078, M["glow_dim"], bevel=0.0, tags=tags)

    # coroa da prensa sobre a fileira de cima: nucleo escuro + espinha + garras laterais
    crown = [(-0.62, 0.10), (-0.52, 0.04), (0.52, 0.04), (0.62, 0.10), (0.66, 0.80), (0.56, 0.93), (-0.56, 0.93),
             (-0.66, 0.80)]
    B.plate("cr_core", crown, 0.05, 0.16, K, slope=0.03, tags=tags)
    spine = [(-0.19, 0.91), (0.19, 0.91), (0.23, 0.87), (0.23, 0.30), (0.09, 0.10), (-0.09, 0.10), (-0.23, 0.30),
             (-0.23, 0.87)]
    sa, sp = B.shard("cr_spine", spine, 0.14, 0.36, A, slope=0.07, groove=0.03, panel_h=0.03, tags=tags)
    # olho da prensa (janela escura com fenda ambar) perto da ponta
    win = [(-0.08, 0.24), (0.08, 0.24), (0.08, 0.32), (0.04, 0.36), (-0.04, 0.36), (-0.08, 0.32)]
    for t in (sa, sp):
        B.cut(t, [B.loft(f"cr_winc{id(t) % 7}", win, win, 0.31, 0.6, K, bevel=0.0)])
    B.loft("cr_winbed", win, win, 0.30, 0.31, M["black"], bevel=0.0, tags=tags)
    B.box("cr_eye", 0, 0.29, 0.10, 0.02, 0.31, 0.318, M["lens"], bevel=0.0, tags=tags)
    # tampa do cilindro hidraulico no alto da espinha
    B.cyl("cr_cylcap", 0, 0.72, 0.40, 0.10, 0.04, S, axis="Z", verts=8, bevel=0.01, tags=tags)
    B.cyl("cr_cylcap2", 0, 0.72, 0.42, 0.06, 0.03, KM, axis="Z", verts=8, bevel=0.006, tags=tags)
    Mo.slot_with_pips("cr_sl", 0.50, -0.09, 0.09, 0.04, 0.39, 3, M, tags, target=[sa, sp], depth=0.075,
                      vertical=False)
    claw = [(-0.28, 0.90), (-0.28, 0.34), (-0.36, 0.17), (-0.48, 0.08), (-0.58, 0.12), (-0.62, 0.20),
            (-0.62, 0.78), (-0.52, 0.90)]
    for sx, f in ((-1, lambda p: p), (1, Mo.mirror)):
        ca, cp = B.shard(f"cr_claw{sx}", f(claw), 0.12, 0.30, A, slope=0.06, groove=0.03, panel_h=0.025, tags=tags)
        # baia de respiro com persianas e pips
        vx = sx * 0.45
        for t in (ca, cp):
            B.cut(t, [B.box(f"cr_vc{sx}{id(t) % 7}", vx, 0.62, 0.16, 0.30, 0.25, 0.6, K, bevel=0.0)])
        B.box(f"cr_vbed{sx}", vx, 0.62, 0.16, 0.30, 0.25, 0.256, M["black"], bevel=0.0, tags=tags)
        for i in range(5):
            B.box(f"cr_lv{sx}{i}", vx, 0.50 + i * 0.06, 0.14, 0.022, 0.256, 0.30, KM, bevel=0.004, tags=tags)
        Mo.slot_with_pips(f"cr_csl{sx}", vx, 0.22, 0.40, 0.04, 0.325, 3, M, tags, target=[ca, cp], depth=0.07,
                          pip_mat=M["glow_dim"])
        # linha hidraulica no vao entre espinha e garra
        B.cyl(f"cr_line{sx}", sx * 0.255, 0.55, 0.20, 0.018, 0.62, S, axis="Y", verts=8, bevel=0.0, tags=tags)
    B.bolts("cr_b", [(-0.58, 0.86), (0.58, 0.86), (-0.56, 0.14), (0.56, 0.14)], 0.16, 0.018, S, tags=tags)
