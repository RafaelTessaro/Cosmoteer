"""Prensa de Carregadores (Magazine Press) 2x2 - empacota 5 balas de canhao em 1 Carregador Padrao.

Layout fixo das regras (tools/bsgen/factory.py): fileira de cima = maquinario (bloqueado para a tripulacao);
fileira de baixo = grade de ENTRADA no tile da esquerda e de SAIDA no tile da direita, onde o jogo desenha as
pilhas de recursos. Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade = 1 tile.

Maquinario (fileira de cima), na linguagem da familia (nucleo escuro + lascas claras com bisel duplo):
  * cilindro hidraulico facetado (como um cano curto e grosso, com canal escuro, LED e colar) no centro,
    apontado para a matriz; o martelo em ponta de seta avanca e bate na bigorna da matriz;
  * ombreiras em L (as "garras" da familia): a garra interna aponta para a matriz, a externa desce pela ponta
    ate o modulo do rotor; aleta com fenda de pips, baia de respiro e cacador ambar; tambores acumuladores
    com contador nos vaos escuros;
  * esteira de alimentacao: as balas de canhao (corpo cinza-azulado e ogiva de latao, como a bala do jogo que
    fica na grade de entrada) saem do alimentador esquerdo e entram na matriz; a janela da matriz mostra as
    balas sendo empacotadas (1..5) com o contador ambar abaixo;
  * esteira de saida: carregadores prontos (o proprio modelo do Carregador Padrao, parts/bs_mag_std.py, em
    miniatura e com a cunha apontando para a saida) saem por baixo da matriz e somem no ejetor direito;
  * rotores nos modulos das pontas, bicos de entrada/saida com setas ambar em calhas escuras;
  * LEDs das grades (na borda de cima de cada berco, fora da area das pilhas) ficam no quadro da maquina, para
    apagarem junto com ela.
A animacao (phase 0..1, 10 quadros = 1,25 s = intervalo da receita) e um ciclo da prensa: carrega 5 balas,
avanca o martelo, bate (lampejo e duas faiscas laranja), recua e ejeta um carregador.
Teto: placas verdes (pintura) e a cabeca blindada da prensa em seta (espinha = carcaca do martelo com trilhos-guia
de aco, tampa com fendas de respiro e visor de inspecao com o contador de 4 pips do carregador; ombreiras com
respiro, laminas diagonais com fenda de luz); escotilhas das grades com setas de entrada/saida.
"""

import math

import bs3d as B
import models as Mo
from parts import bs_mag_std as MAG

PART = {
    "id": "rafaeltessaro.bs_factory_mag_std",
    "kind": "factory",
    "size": [2, 2],
    "accent": "amber",
    "machine_frames": 10,
    "machine_interval": 0.125,
}

NFR = PART["machine_frames"]
# geometria compartilhada (fileira de cima: y em [0, 1]; as paredes cobrem 0.11 nas bordas da peca)
BELT_Y0, BELT_Y1 = 0.10, 0.37      # faixa da esteira
BELT_YC = (BELT_Y0 + BELT_Y1) / 2
DIE_X, DIE_Y1 = 0.235, 0.40        # meia largura e fundo da ponte da matriz
CAP_X = 0.59                       # borda interna dos modulos das pontas
LANE = 0.295                       # meia largura do corredor do martelo (entre as ombreiras)
RAM_IN, RAM_OUT = 0.548, 0.402     # frente do martelo recolhido / batendo
RAM_D = 0.14                       # profundidade do martelo
CYL_Y0, CYL_Y1 = 0.695, 0.885      # cilindro hidraulico
CYL_Z, CYL_R = 0.27, 0.20


def _mat_rough():
    """Cinza medio fosco (escotilhas e cantoneiras): sem o brilho frio da contraluz nos chanfros de baixo."""
    return B.mat_paint("armor_mid_rough", Mo.ARMOR_MID, rough=0.72, metal=0.12, wear=0.3, grime=0.1)


def _frame(phase):
    return int(round(phase * NFR)) % NFR


def _ram_ext(phase):
    """Extensao do martelo (0 = recolhido, 1 = batendo) ao longo do ciclo."""
    return [0.0, 0.0, 0.0, 0.0, 0.0, 0.55, 1.0, 0.94, 0.5, 0.15][_frame(phase)]


def _loaded(phase):
    """Balas dentro da matriz (janela de contagem): 1..5 carregando, 5 na batida, 0 depois da ejecao."""
    return [1, 2, 3, 4, 5, 5, 5, 5, 0, 0][_frame(phase)]


def _swap_mat(names, mat):
    for n in names:
        ob = B.bpy.data.objects.get(n)
        if ob is not None:
            ob.data.materials[0] = mat


def _round(name, x, y, z, r, L, M, tags):
    """Bala de canhao deitada ao longo de Y, como a bala do jogo: corpo cinza-azulado com cinta escura e ogiva de
    latao rombuda apontando para +Y (mesmos materiais das balas na janela do carregador)."""
    body, brass = MAG._round_mats()
    lc = L * 0.58
    B.cyl(name + "_case", x, y - L / 2 + lc / 2, z, r, lc, body, axis="Y", verts=10, bevel=0.0, tags=tags)
    B.cyl(name + "_band", x, y - L / 2 + lc * 0.72, z, r * 1.06, L * 0.07, M["core_mid"], axis="Y", verts=10,
          bevel=0.0, tags=tags)
    lt = L - lc
    B.cyl(name + "_tip", x, y - L / 2 + lc + lt / 2, z, r, lt, brass, axis="Y", verts=10, bevel=0.0, tags=tags,
          r2=r * 0.5)


MINI = 0.34   # escala do Carregador Padrao na esteira de saida (0.31 x 0.21 tile)


def _mini_mag(name, x, y, z, M, tags):
    """Carregador Padrao em miniatura na esteira de saida: o proprio modelo do recurso (bs_mag_std.item), deitado
    com a cunha apontando para a saida (+X). Altura total MINI * 0.445 + z (fica abaixo do fundo da janela da
    matriz e do recesso dos rotores, que o escondem enquanto passa por baixo)."""
    sc = B.bpy.context.scene
    before = set(o.name for o in sc.objects)
    MAG.item(M, tags[0])
    emp = B.bpy.data.objects.new(name, None)
    sc.collection.objects.link(emp)
    for o in [o for o in sc.objects if o.name not in before and o.parent is None and o is not emp]:
        o.parent = emp
    emp.location = (x, y, z)
    emp.scale = (MINI, MINI, MINI)
    emp.rotation_euler.z = math.radians(-90)
    return emp


# ============================================================================ piso
PAD_LED_Y = -0.06   # LED de cada berco: na borda de cima do tile de baixo, fora da area da pilha (inset de 6 px)


def floor(M, T="floor"):
    """Piso: poco escuro com grade sob a maquina; bercos de entrada/saida com cantoneiras e recesso para o LED
    (o LED em si fica no quadro da maquina, para apagar junto com ela)."""
    tags = (T,)
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    AR = _mat_rough()
    B.box("fl_base", 0, 0, 2, 2, -0.05, 0.0, K, bevel=0.0, tags=tags)
    # fileira de cima: poco da maquina (moldura escura e grade de aco)
    pit = B.plate("fl_pit", B.rpoly(0, 0.5, 1.92, 0.92, 0, chamfer=0.06), 0.0, 0.03, KM, slope=0.01, tags=tags)
    B.cut(pit, [B.box("fl_pitc", 0, 0.5, 1.80, 0.80, 0.0, 0.2, K, bevel=0.0)])
    B.box("fl_pitbed", 0, 0.5, 1.80, 0.80, -0.01, 0.002, M["black"], bevel=0.0, tags=tags)
    for i in range(11):
        B.box(f"fl_grate{i}", -0.85 + i * 0.17, 0.5, 0.025, 0.80, 0.0, 0.015, KM, bevel=0.0, tags=tags)
    # fileira de baixo: um berco por grade (entrada esquerda, saida direita)
    for side, cx in (("in", -0.5), ("out", 0.5)):
        cy = -0.5
        B.plate(f"fl_tray_{side}", B.rpoly(cx, cy, 0.92, 0.92, 0, chamfer=0.07), 0.0, 0.025, KM, slope=0.01,
                tags=tags)
        tin = B.rpoly(cx, cy, 0.76, 0.78, 0, chamfer=0.05)
        B.loft(f"fl_trayin_{side}", tin, tin, 0.025, 0.032, K, bevel=0.0, tags=tags)
        # grade da pilha (2 x 2) em relevo fino
        B.box(f"fl_tgv_{side}", cx, cy, 0.012, 0.70, 0.032, 0.038, KM, bevel=0.0, tags=tags)
        B.box(f"fl_tgh_{side}", cx, cy, 0.70, 0.012, 0.032, 0.038, KM, bevel=0.0, tags=tags)
        # cantoneiras em L nos quatro cantos (vaos escuros entre elas)
        for qx in (-1, 1):
            for qy in (-1, 1):
                ox, oy = cx + qx * 0.41, cy + qy * 0.41
                poly = [(ox, oy), (ox - qx * 0.24, oy), (ox - qx * 0.24, oy - qy * 0.07), (ox - qx * 0.07,
                        oy - qy * 0.07), (ox - qx * 0.07, oy - qy * 0.24), (ox, oy - qy * 0.24)]
                B.shard(f"fl_br_{side}{qx}{qy}", poly, 0.0, 0.06, AR, slope=0.012, groove=0.008, panel_h=0.012,
                        tags=tags)
        # recesso escuro do LED no vao de cima (o LED vem no quadro da maquina)
        B.box(f"fl_ledbed_{side}", cx, PAD_LED_Y, 0.20, 0.05, 0.02, 0.035, M["black"], bevel=0.0, tags=tags)
    # divisoria central entre as grades: barra de aco com parafusos
    B.box("fl_div", 0, -0.5, 0.06, 0.80, 0.0, 0.05, S, bevel=0.01, tags=tags)
    B.bolts("fl_divb", [(0, -0.22), (0, -0.78)], 0.05, 0.016, KM, tags=tags)


# ============================================================================ maquinario (animado)
def machine(M, T="machine", phase=0.0):
    tags = (T,)
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    fi = _frame(phase)

    # ---------------------------------------------------------------- esteira (base, trilhos, lona)
    B.box("bt_bed", 0, BELT_YC, 1.70, BELT_Y1 - BELT_Y0 + 0.04, 0.0, 0.08, KM, bevel=0.008, tags=tags)
    B.box("bt_lona", 0, BELT_YC, 1.70, BELT_Y1 - BELT_Y0 - 0.02, 0.08, 0.095, M["black"], bevel=0.0, tags=tags)
    for sy in (BELT_Y0, BELT_Y1):
        B.box(f"bt_rail{sy}", 0, sy, 1.70, 0.025, 0.06, 0.14, S, bevel=0.006, tags=tags)
    # esteira de entrada: taliscas + balas (anda 2 passos por ciclo)
    p_in = 0.095
    s_in = (phase * 2.0) % 1.0
    for k in range(-1, 6):
        x = -CAP_X - 0.08 + (k + s_in) * p_in
        if x > -DIE_X + 0.04:
            continue
        B.box(f"bt_cl{k}", x, BELT_YC, 0.012, BELT_Y1 - BELT_Y0 - 0.03, 0.095, 0.11, S, bevel=0.0, tags=tags)
        xr = x + p_in / 2
        if xr < -DIE_X + 0.02:
            _round(f"bt_rd{k}", xr, BELT_YC, 0.135, 0.033, 0.22, M, tags)
    # esteira de saida: taliscas + carregadores prontos (sai 1 carregador por ciclo; nascem escondidos sob a
    # matriz e passam por baixo do fundo da janela, que fica acima deles)
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
            _mini_mag(f"mm{k}", xm, BELT_YC, 0.095, M, tags)

    # ---------------------------------------------------------------- ponte da matriz (bigorna sobre a esteira)
    B.plate("die_jaw", B.rpoly(0, 0.225, 2 * DIE_X + 0.10, 0.34, 0, chamfer=0.06), 0.0, 0.20, KM, slope=0.02,
            tags=tags)
    for sx in (-1, 1):
        B.cyl(f"die_roll{sx}", sx * (DIE_X + 0.03), BELT_YC, 0.21, 0.02, 0.30, S, axis="Y", verts=10, bevel=0.0,
              tags=tags)
    # bigorna em hexagono alongado: pontas de seta apontando para as duas esteiras
    die = [(-0.31, 0.225), (-DIE_X, 0.075), (-0.18, 0.04), (0.18, 0.04), (DIE_X, 0.075), (0.31, 0.225),
           (DIE_X, 0.37), (0.19, DIE_Y1), (-0.19, DIE_Y1), (-DIE_X, 0.37)]
    da, dp = B.shard("die", die, 0.10, 0.30, A, slope=0.05, groove=0.022, panel_h=0.025, tags=tags)
    # janela de contagem: balas entrando no carregador (1..5); o fundo fica ACIMA do carregador pronto que passa
    # por baixo da matriz (topo da alca em 0.095 + 0.445 * MINI = 0.246), senao ele apareceria na janela
    wy0, wy1 = 0.19, 0.325
    for t in (da, dp):
        B.cut(t, [B.box(f"die_wc{id(t) % 7}", 0, (wy0 + wy1) / 2, 0.33, wy1 - wy0, 0.255, 0.6, K, bevel=0.0)])
    B.box("die_wbed", 0, (wy0 + wy1) / 2, 0.33, wy1 - wy0, 0.255, 0.26, M["black"], bevel=0.0, tags=tags)
    n = _loaded(phase)
    for i in range(n):
        _round(f"die_rd{i}", -0.128 + i * 0.064, (wy0 + wy1) / 2, 0.282, 0.024, 0.125, M, tags)
    # contador ambar (pips acesos = balas carregadas) numa fenda escura abaixo da janela
    Mo.slot_with_pips("die_sl", 0.13, -0.15, 0.15, 0.032, 0.325, 5, M, tags, target=[da, dp], depth=0.075,
                      vertical=False)
    _swap_mat([f"die_sl_pip{i}" for i in range(n, 5)], KM)

    # ---------------------------------------------------------------- modulos das pontas (alimentador/ejetor)
    capL = [(-0.885, 0.035), (-0.68, 0.035), (-0.59, 0.10), (-0.59, 0.20), (-0.655, 0.27), (-0.885, 0.27)]
    for sx, f in ((-1, lambda p: p), (1, Mo.mirror)):
        ca, cp = B.shard(f"cap{sx}", f(capL), 0.0, 0.30, A, slope=0.05, groove=0.025, panel_h=0.025, tags=tags)
        rx, ry = sx * 0.765, 0.152
        rec = B.rpoly(rx, ry, 0.16, 0.16, 0, chamfer=0.047)
        for t in (ca, cp):
            B.cut(t, [B.loft(f"cap_rc{sx}{id(t) % 7}", rec, rec, 0.25, 0.6, K, bevel=0.0)])
        # fundo do recesso acima do topo do carregador que passa por baixo do modulo (z 0.25)
        B.loft(f"cap_rbed{sx}", rec, rec, 0.25, 0.26, M["black"], bevel=0.0, tags=tags)
        # rotor de 3 pas: uma volta por ciclo (0,3 de passo por quadro, sem serrilhado de movimento)
        ang = -sx * phase * 360.0
        for b in range(3):
            a = ang + b * 120
            B.rbox(f"rot{sx}{b}", rx + math.cos(math.radians(a)) * 0.036, ry + math.sin(math.radians(a)) * 0.036,
                   0.064, 0.026, 0.26, 0.285, S, rot=a, bevel=0.004, tags=tags)
        B.cyl(f"rot_hub{sx}", rx, ry, 0.29, 0.026, 0.025, KM, axis="Z", verts=12, bevel=0.004, tags=tags)
        # capuz do tunel do alimentador/ejetor sobre a esteira, entre o modulo e a ombreira: as balas saem e os
        # carregadores entram por baixo dele (acima do topo do carregador, 0.246), com labio de aco na boca
        hood = [(0.595, 0.235), (0.885, 0.235), (0.885, 0.40), (0.66, 0.40), (0.595, 0.335)]
        B.plate(f"hood{sx}", hood if sx > 0 else Mo.mirror(hood), 0.25, 0.285, KM, slope=0.015, tags=tags)
        B.box(f"hood_lip{sx}", sx * 0.605, 0.30, 0.022, 0.11, 0.25, 0.30, S, bevel=0.005, tags=tags)
        # bico de entrada/saida na borda de baixo (calha escura com guias de aco e seta ambar)
        cx = sx * 0.70
        B.box(f"chute{sx}", cx, -0.005, 0.26, 0.11, 0.0, 0.06, K, bevel=0.006, tags=tags)
        for gx in (-1, 1):
            B.box(f"chute_g{sx}{gx}", cx + gx * 0.12, -0.005, 0.025, 0.12, 0.0, 0.09, S, bevel=0.004, tags=tags)
        d = 1 if sx < 0 else -1   # entrada aponta para dentro (+Y), saida aponta para fora (-Y)
        chev = [(cx - 0.06, -0.005 - d * 0.02), (cx, -0.005 + d * 0.025), (cx + 0.06, -0.005 - d * 0.02),
                (cx + 0.06, -0.005 - d * 0.04), (cx, -0.005 + d * 0.005), (cx - 0.06, -0.005 - d * 0.04)]
        B.loft(f"chute_ar{sx}", chev, chev, 0.06, 0.068, M["glow_dim"], bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- ombreiras em garra + tambores nos vaos
    # ombreira em L: cobre o canto de cima e desce pela ponta ate o modulo do rotor; garra interna aponta
    # para a matriz, garra externa aponta para o modulo
    paul = [(-0.875, 0.875), (-0.345, 0.875), (-LANE, 0.83), (-LANE, 0.64), (-0.335, 0.555), (-0.49, 0.555),
            (-0.585, 0.505), (-0.625, 0.39), (-0.69, 0.305), (-0.875, 0.305)]
    # aleta (segundo nivel) na parte externa, com fenda vertical de pips
    fin = [(-0.835, 0.80), (-0.70, 0.80), (-0.665, 0.765), (-0.665, 0.44), (-0.71, 0.375), (-0.835, 0.375)]
    # cacador descendo para a matriz: periodo de 5 quadros (divide os 10 do ciclo, sem tropeco na volta)
    lit = [2, 1, 0, None, None][fi % 5]
    for sx, f in ((-1, lambda p: p), (1, Mo.mirror)):
        pa, pp = B.shard(f"paul{sx}", f(paul), 0.0, 0.36, A, slope=0.085, groove=0.03, panel_h=0.03, tags=tags)
        # baia de respiro (persianas) no alto da ombreira
        vx = sx * 0.50
        for t in (pa, pp):
            B.cut(t, [B.box(f"pv_c{sx}{id(t) % 7}", vx, 0.735, 0.16, 0.08, 0.31, 0.6, K, bevel=0.0)])
        B.box(f"pv_bed{sx}", vx, 0.735, 0.16, 0.08, 0.30, 0.31, M["black"], bevel=0.0, tags=tags)
        for i in range(4):
            B.box(f"pv_lv{sx}{i}", vx - 0.06 + i * 0.04, 0.735, 0.016, 0.07, 0.31, 0.37, KM, bevel=0.003, tags=tags)
        # fenda vertical de 3 pips junto da garra interna (cacador descendo em direcao a matriz)
        Mo.slot_with_pips(f"paul_sl{sx}", sx * 0.405, 0.655, 0.785, 0.034, 0.39, 3, M, tags, target=[pa, pp],
                          depth=0.075)
        _swap_mat([f"paul_sl{sx}_pip{i}" for i in range(3) if i != lit], M["glow_dim"])
        # linhas de painel: corte no cotovelo de baixo e corte cruzado na perna que desce ao modulo do rotor
        for t in (pa, pp):
            B.cut(t, [B.rbox(f"paul_pl{sx}{id(t) % 7}a", sx * 0.43, 0.585, 0.014, 0.10, 0.30, 0.6, K, rot=0,
                             bevel=0.0),
                      B.rbox(f"paul_pl{sx}{id(t) % 7}b", sx * 0.60, 0.585, 0.11, 0.014, 0.30, 0.6, K, rot=-sx * 35,
                             bevel=0.0)])
        # aleta externa em cinza medio: as ombreiras recuam e a prensa (matriz + martelo) manda na leitura
        fa, fp = B.shard(f"fin{sx}", f(fin), 0.39, 0.47, AM, slope=0.035, groove=0.018, panel_h=0.02, tags=tags)
        Mo.slot_with_pips(f"fin_sl{sx}", sx * 0.75, 0.48, 0.70, 0.034, 0.49, 3, M, tags, target=[fa, fp],
                          depth=0.07, pip_mat=M["glow_dim"])
        # tambor acumulador no vao entre ombreira e esteira (contador ambar, aneis de aco)
        dx = sx * 0.45
        B.cyl(f"drum{sx}", dx, 0.475, 0.11, 0.06, 0.22, KM, axis="X", verts=8, bevel=0.008, tags=tags)
        for i, ox in enumerate((-0.09, 0.0, 0.09)):  # aneis
            B.cyl(f"drumr{sx}{i}", dx + ox, 0.475, 0.11, 0.066, 0.022, S, axis="X", verts=8, bevel=0.004, tags=tags)
        B.box(f"drumled{sx}", dx - sx * 0.05, 0.475, 0.022, 0.03, 0.165, 0.175, M["glow_dim"], bevel=0.0, tags=tags)
        # mangueira do tambor ate o cilindro
        B.cyl(f"hose{sx}", sx * 0.30, 0.50, 0.08, 0.016, 0.12, S, axis="Y", verts=8, bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- cilindro hidraulico facetado (o heroi)
    cl = CYL_Y1 - CYL_Y0
    yc = (CYL_Y0 + CYL_Y1) / 2
    cyl = B.cyl("cyl", 0, yc, CYL_Z, CYL_R, cl, A, axis="Y", verts=8, bevel=0.012, tags=tags)
    B.cut(cyl, [B.box("cyl_ch", 0, yc + 0.03, 0.07, cl - 0.05, CYL_Z + CYL_R - 0.06, CYL_Z + 0.5, K, bevel=0.0)])
    B.box("cyl_chbed", 0, yc + 0.03, 0.07, cl - 0.05, CYL_Z + CYL_R - 0.075, CYL_Z + CYL_R - 0.055, M["black"],
          bevel=0.0, tags=tags)
    B.box("cyl_chled", 0, yc + 0.03, 0.022, cl - 0.11, CYL_Z + CYL_R - 0.055, CYL_Z + CYL_R - 0.05,
          M["glow"] if _ram_ext(phase) > 0.9 else M["glow_dim"], bevel=0.0, tags=tags)
    B.cyl("cyl_col", 0, CYL_Y0 + 0.022, CYL_Z, CYL_R + 0.014, 0.04, AM, axis="Y", verts=8, bevel=0.006, tags=tags)
    for sx in (-1, 1):
        # conexoes hidraulicas nas faces laterais do cilindro
        B.cyl(f"cyl_port{sx}", sx * (CYL_R - 0.01), yc + 0.04, CYL_Z + 0.06, 0.022, 0.06, S, axis="Z", verts=8,
              bevel=0.004, tags=tags)
    B.cyl("cyl_gland", 0, CYL_Y0 - 0.008, CYL_Z - 0.02, 0.10, 0.03, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    # buchas das guias, presas nas ombreiras
    for sx in (-1, 1):
        B.box(f"gbush{sx}", sx * 0.245, CYL_Y0 + 0.02, 0.06, 0.06, 0.06, 0.20, KM, bevel=0.008, tags=tags)

    # ---------------------------------------------------------------- martelo (animado)
    e = _ram_ext(phase)
    yf = RAM_IN + (RAM_OUT - RAM_IN) * e
    yb = yf + RAM_D
    L = CYL_Y0 - yb
    if L > 0.01:
        B.cyl("ram_rod", 0, yb + L / 2, CYL_Z - 0.03, 0.06, L, S, axis="Y", verts=12, bevel=0.0, tags=tags)
    Lg = CYL_Y0 + 0.05 - yb
    for sx in (-1, 1):
        B.cyl(f"ram_gr{sx}", sx * 0.245, yb + Lg / 2, 0.13, 0.02, Lg, S, axis="Y", verts=10, bevel=0.0, tags=tags)
    ram = [(-0.17, yf), (0.17, yf), (0.26, yf + 0.06), (0.26, yb), (-0.26, yb), (-0.26, yf + 0.06)]
    B.box("ram_face", 0, yf + 0.014, 0.31, 0.03, 0.05, 0.22, K, bevel=0.004, tags=tags)
    ra, rp = B.shard("ram", ram, 0.06, 0.32, A, slope=0.04, groove=0.02, panel_h=0.025, tags=tags)
    Mo.slot_with_pips("ram_sl", yf + 0.085, -0.10, 0.10, 0.03, 0.345, 3, M, tags, target=[ra, rp], depth=0.07,
                      vertical=False, pip_mat=M["glow"] if e > 0.9 else M["glow_dim"])
    for sx in (-1, 1):
        B.bolts(f"ram_b{sx}", [(sx * 0.20, yb - 0.035)], 0.345, 0.014, S, tags=tags)
    # batida: linha ambar curta no encontro martelo/matriz e duas faiscas laranja curtas saindo pelos lados
    if e > 0.99:
        # linha curta e mais fraca que os LEDs: o halo nao lava a borda clara da matriz (bisel duplo continua lendo)
        hit = B.mat_glow("hit", Mo.ACCENTS["amber"], 4.5)
        B.box("hit", 0, DIE_Y1 + 0.004, 0.22, 0.01, 0.22, 0.235, hit, bevel=0.0, tags=tags)
        spark = B.mat_glow("spark", (1.0, 0.30, 0.03), 7.0)
        for i, sx in enumerate((-1, 1)):
            B.rbox(f"spark{i}", sx * 0.30, 0.418, 0.06, 0.011, 0.33, 0.34, spark, rot=sx * 22, bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- LEDs das grades (no recesso do piso)
    for side, cx in (("in", -0.5), ("out", 0.5)):
        B.box(f"pad_led_{side}", cx, PAD_LED_Y, 0.10, 0.018, 0.035, 0.042, M["glow_dim"], bevel=0.0, tags=tags)


# ============================================================================ teto
def roof(M, T="roof"):
    """Teto: placas verdes (pintura da nave) e, sobre a prensa, a cabeca blindada clara (espinha = carcaca do
    martelo + ombreiras)."""
    tags = (T,)
    green = B.mat_roof_green()
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    AR = _mat_rough()
    B.box("rf_under", 0, 0, 2, 2, -0.05, 0.02, K, bevel=0.0, tags=tags)
    for tx in range(2):
        for ty in range(2):
            cx, cy = tx - 0.5, 0.5 - ty
            _, pnl = B.shard(f"rf{tx}{ty}", B.rpoly(cx, cy, 0.94, 0.94, 0, chamfer=0.07), 0.0, 0.06, green,
                             slope=0.025, groove=0.05, panel_h=0.02, tags=tags)
            if ty == 1 and pnl is not None:
                # linha de painel diagonal (espelhada nos dois tiles de baixo): corta o painel inteiro e mostra um
                # filete escuro no fundo, senao a linha paralela a luz (tile da direita) some
                sgn = tx * 2 - 1
                lx, ly = cx + sgn * 0.22, cy - 0.22
                B.cut(pnl, [B.rbox(f"rf_dl{tx}", lx, ly, 0.016, 0.36, 0.045, 0.2, K, rot=sgn * 45, bevel=0.0)])
                B.rbox(f"rf_dlb{tx}", lx, ly, 0.014, 0.34, 0.058, 0.064, K, rot=sgn * 45, bevel=0.0, tags=tags)
    # escotilhas das grades: entrada (seta para dentro) e saida (seta para fora), com bisel duplo
    for sx in (-1, 1):
        cx, cy = sx * 0.5, -0.54
        ha, hp = B.shard(f"rf_hatch{sx}", B.rpoly(cx, cy, 0.48, 0.42, 0, chamfer=0.10), 0.07, 0.12, AR,
                         slope=0.025, groove=0.02, panel_h=0.015, tags=tags)
        d = 1 if sx < 0 else -1
        chev = [(cx - 0.10, cy - d * 0.04), (cx, cy + d * 0.06), (cx + 0.10, cy - d * 0.04),
                (cx + 0.10, cy - d * 0.09), (cx, cy + d * 0.01), (cx - 0.10, cy - d * 0.09)]
        for t in (ha, hp):
            B.cut(t, [B.loft(f"rf_chc{sx}{id(t) % 7}", chev, chev, 0.09, 0.3, K, bevel=0.0)])
        B.loft(f"rf_chb{sx}", chev, chev, 0.09, 0.095, M["black"], bevel=0.0, tags=tags)
        B.box(f"rf_hh{sx}", cx, cy - 0.145, 0.18, 0.035, 0.135, 0.16, S, bevel=0.008, tags=tags)
        B.bolts(f"rf_hb{sx}", [(cx - 0.17, cy + 0.13), (cx + 0.17, cy + 0.13)], 0.135, 0.015, S, tags=tags)
    # LEDs de sentido no vao entre as escotilhas
    B.box("rf_ledbed", 0, -0.54, 0.05, 0.24, 0.04, 0.07, M["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"rf_led{i}", 0, -0.62 + i * 0.08, 0.022, 0.03, 0.07, 0.078, M["glow_dim"], bevel=0.0, tags=tags)

    # cabeca da prensa sobre a fileira de cima, em seta apontando para as grades: nucleo escuro + espinha +
    # ombreiras + laminas diagonais que convergem para a ponta da espinha
    base = [(-0.30, 0.04), (0.30, 0.04), (0.74, 0.40), (0.74, 0.86), (0.66, 0.94), (-0.66, 0.94), (-0.74, 0.86),
            (-0.74, 0.40)]
    B.plate("cr_core", base, 0.05, 0.15, K, slope=0.02, tags=tags)
    spine = [(-0.17, 0.92), (0.17, 0.92), (0.22, 0.87), (0.22, 0.36), (0.08, 0.08), (-0.08, 0.08), (-0.22, 0.36),
             (-0.22, 0.87)]
    B.shard("cr_spine", spine, 0.12, 0.36, A, slope=0.085, groove=0.03, panel_h=0.03, tags=tags)
    spine2 = [(-0.115, 0.83), (0.115, 0.83), (0.135, 0.80), (0.135, 0.42), (0.055, 0.28), (-0.055, 0.28),
              (-0.135, 0.42), (-0.135, 0.80)]
    s2 = B.plate("cr_spine2", spine2, 0.39, 0.47, A, slope=0.03, tags=tags)
    # visor de inspecao sobre a matriz: fenda escura com o contador de 4 pips ambar do carregador
    win = B.rpoly(0, 0.405, 0.16, 0.042, 0, chamfer=0.012)
    B.cut(s2, [B.loft("cr_winc", win, win, 0.41, 0.7, K, bevel=0.0)])
    B.loft("cr_winbed", win, win, 0.405, 0.415, M["black"], bevel=0.0, tags=tags)
    for i in range(4):
        B.box(f"cr_cnt{i}", -0.054 + i * 0.036, 0.405, 0.02, 0.02, 0.415, 0.421, M["glow"], bevel=0.0, tags=tags)
    Mo.slot_with_pips("cr_sl", 0.555, -0.07, 0.07, 0.035, 0.47, 3, M, tags, target=s2, depth=0.06,
                      vertical=False, pip_mat=M["glow_dim"])
    # tampa da carcaca do martelo: fendas de respiro transversais (no lugar da tampa redonda, que lia como olho)
    for i in range(4):
        yv = 0.635 + i * 0.05
        B.cut(s2, [B.box(f"cr_slc{i}", 0, yv, 0.15, 0.022, 0.41, 0.7, K, bevel=0.0)])
        B.box(f"cr_slb{i}", 0, yv, 0.15, 0.022, 0.405, 0.415, M["black"], bevel=0.0, tags=tags)
    # trilhos-guia de aco do martelo dos dois lados da tampa, com batentes
    for sx in (-1, 1):
        B.box(f"cr_rail{sx}", sx * 0.152, 0.62, 0.028, 0.40, 0.36, 0.405, S, bevel=0.008, tags=tags)
        for yb in (0.43, 0.81):
            B.box(f"cr_stop{sx}{yb}", sx * 0.152, yb, 0.044, 0.03, 0.36, 0.42, KM, bevel=0.006, tags=tags)
    paul = [(-0.27, 0.92), (-0.27, 0.66), (-0.34, 0.585), (-0.62, 0.585), (-0.72, 0.66), (-0.72, 0.85),
            (-0.65, 0.92)]
    blade = [(-0.72, 0.53), (-0.58, 0.53), (-0.285, 0.25), (-0.25, 0.135), (-0.33, 0.11), (-0.72, 0.41)]
    for sx, f in ((-1, lambda p: p), (1, Mo.mirror)):
        pa, pp = B.shard(f"cr_paul{sx}", f(paul), 0.12, 0.32, A, slope=0.075, groove=0.03, panel_h=0.025, tags=tags)
        # baia de respiro (persianas escuras) e fenda de pips na ombreira
        vx = sx * 0.53
        for t in (pa, pp):
            B.cut(t, [B.box(f"cr_vc{sx}{id(t) % 7}", vx, 0.75, 0.17, 0.15, 0.25, 0.6, K, bevel=0.0)])
        B.box(f"cr_vbed{sx}", vx, 0.75, 0.17, 0.15, 0.25, 0.256, M["black"], bevel=0.0, tags=tags)
        for i in range(4):
            B.box(f"cr_lv{sx}{i}", vx, 0.693 + i * 0.038, 0.15, 0.016, 0.256, 0.30, KM, bevel=0.003, tags=tags)
        Mo.slot_with_pips(f"cr_psl{sx}", sx * 0.37, 0.68, 0.82, 0.034, 0.345, 3, M, tags, target=[pa, pp],
                          depth=0.07, pip_mat=M["glow_dim"])
        # lamina diagonal com fenda de luz fraca (como as laminas do 76 mm)
        ba, bp = B.shard(f"cr_blade{sx}", f(blade), 0.12, 0.27, A, slope=0.045, groove=0.02, panel_h=0.02,
                         tags=tags)
        ang = sx * 43
        for t in (ba, bp):
            B.cut(t, [B.rbox(f"cr_bc{sx}{id(t) % 7}", sx * 0.49, 0.342, 0.18, 0.03, 0.22, 0.6, K, rot=ang, bevel=0.0)])
        B.rbox(f"cr_bbed{sx}", sx * 0.49, 0.342, 0.18, 0.03, 0.215, 0.225, M["black"], rot=ang, bevel=0.0, tags=tags)
        B.rbox(f"cr_bglow{sx}", sx * 0.49, 0.342, 0.13, 0.011, 0.225, 0.231, M["glow_dim"], rot=ang, bevel=0.0,
               tags=tags)
        # linha hidraulica no vao entre espinha e ombreira
        B.cyl(f"cr_line{sx}", sx * 0.245, 0.69, 0.18, 0.016, 0.40, S, axis="Y", verts=8, bevel=0.0, tags=tags)
    B.bolts("cr_b", [(-0.68, 0.88), (0.68, 0.88), (-0.66, 0.46), (0.66, 0.46)], 0.15, 0.016, S, tags=tags)
    # o verde do conves nao reflete nem rebate luz nas pecas sem pintura (senao a pintura vaza nas bordas claras)
    for o in B.bpy.context.scene.objects:
        if o.type == "MESH" and o.get(T) and any(m is green for m in o.data.materials):
            o.visible_glossy = False
            o.visible_diffuse = False
