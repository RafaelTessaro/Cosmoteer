"""Prensa de Carregadores Perfurantes (AP Magazine Press) 3x3 - crava pontas de tristeel nos carregadores.

Layout vanilla factory_he (tools/bsgen/factory.py): fileira de cima + tile central = maquinario (bloqueado);
entradas no meio das laterais: tile (0,1) esquerda = Carregador Padrao, tile (2,1) direita = tristeel;
saida = fileira de baixo inteira. O jogo desenha as pilhas de recursos nesses 5 tiles, entao eles ficam
livres de maquinario e o piso mostra bases escuras marcadas (cantoneiras cinza, labio fino, setas ambar em
recesso). Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade = 1 tile.

Maquina (mesma familia das armas: cascas claras chanfradas com bisel duplo sobre nucleo escuro):
  * mesa rotativa indexadora no tile central, 4 paletes claros em cunha (estreitos no cubo, chanfros vivos)
    com berco escuro girando no sentido horario:
    W carga (vem da entrada esquerda) -> N prensa -> E inspecao -> S descarga (vai para a saida embaixo);
  * prensa de conformar no tile de cima do meio: duas bochechas em garra que agarram a borda da mesa,
    cilindro hidraulico e matriz em cunha que avanca sobre o ninho N (faiscas laranja e brilho quente no
    impacto, pontas em brasa na volta);
  * forja de pontas a direita (em cima da entrada de tristeel): placa traseira com janela de moldura em
    degrau onde as pontas prateadas deitadas atravessadas andam ate a bobina de inducao (um passo por ciclo,
    na batida), brilho frio azul-branco no tristeel e boca de entrada com setas ambar para cima;
  * central hidraulica a esquerda: placa traseira com janela em degrau e bomba de 2 pistoes alternados;
  * cada casca lateral = placa traseira com chanfro grande de 45 graus apontando para a prensa (a janela em
    degrau repete o chanfro) + cunha da frente que abraca esse chanfro (vao escuro reto e em diagonal, degrau
    na borda interna) + lamina embaixo apontando para a mesa.
Animacao (8 quadros): 0 repouso (mesa no esquadro, matriz recolhida = sprite desligado), 1 matriz desce e
os ninhos W/S deslizam (carga/descarga), 2 crava com faiscas, 3 segura, 4 volta com as pontas em brasa,
5-7 a mesa gira 22,5 graus por quadro (o quadro 0 seguinte fecha os 90 graus).
Teto: placas verdes (pintura) com a coroa blindada sem pintura sobre a prensa (espinha em cunha com olho
frio e 4 pips, garras que descem ate o colar da mesa, laminas diagonais nas placas de cima) e o colar
octogonal segmentado sobre a mesa; setas de entrada/saida pintadas nas outras placas (pips em fendas
vazadas, com leito escuro em volta) e respiros de persianas nas placas de baixo das pontas.
"""

import math
import random

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_factory_mag_ap",
    "kind": "factory",
    "size": [3, 3],
    "accent": "amber",
    "machine_frames": 8,
    "machine_interval": 0.1,
}

NF = PART["machine_frames"]
TCX, TCY = 0.0, -0.05      # centro da mesa indexadora (tile central)
NEST_R = 0.27              # raio dos ninhos (centro dos paletes) na mesa
# palete em cunha (u = radial, v = tangencial): estreito no cubo, largo na borda, chanfros de 0.04
PALLET = [(0.12, -0.10), (0.385, -0.135), (0.42, -0.10), (0.42, 0.10), (0.385, 0.135), (0.12, 0.10)]
DIE_OUT, DIE_IN = 0.56, 0.335   # frente da matriz recolhida / cravando (y)
SHELL = (0.20, 0.22, 0.25)     # aco canhoneado do Carregador Perfurante (igual a parts/bs_mag_ap.py)
LID = (0.40, 0.42, 0.46)       # tampa clara do Carregador Perfurante (igual a parts/bs_mag_ap.py)
FORGE_Y = 1.13             # altura (y) das janelas das cascas laterais


# ============================================================================ utilidades
def _extra():
    """Materiais proprios desta fabrica (prata das pontas, casca do carregador AP, brilhos)."""
    return {
        "silver": B.mat_metal("silver", (0.80, 0.82, 0.86), rough=0.16, metal=1.0),
        "silver_r": B.mat_metal("silver_r", (0.80, 0.82, 0.86), rough=0.34, metal=0.85),
        "ap_shell": B.mat_paint("ap_shell", SHELL, rough=0.36, metal=0.45, wear=0.18, grime=0.04, scale=5),
        "ap_lid": B.mat_paint("ap_lid", LID, rough=0.34, metal=0.25, wear=0.18, grime=0.04, scale=5),
        "band": B.mat_paint("ap_band", (0.50, 0.68, 0.98), rough=0.25, metal=0.1, wear=0.05, grime=0.0, scale=5),
        "brass": B.mat_metal("brass", (0.62, 0.42, 0.12), rough=0.3, metal=1.0),
        "glint": B.mat_glow("glint", (0.70, 0.86, 1.0), 4.0),
        # calor: laranja (nao satura em branco; o branco fica so no brilho frio do tristeel)
        "hot": B.mat_glow("hot", (1.0, 0.28, 0.035), 1.3),
        "spark": B.mat_glow("spark", (1.0, 0.40, 0.08), 1.9),
    }


def _rot(pts, ang, cx=0.0, cy=0.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def _octo(cx, cy, r, a0=22.5):
    return [(cx + r * math.cos(math.radians(a0 + 45 * i)), cy + r * math.sin(math.radians(a0 + 45 * i)))
            for i in range(8)]


def _rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def _flip(sx):
    """Poligono do lado esquerdo -> lado sx (espelho em x para o lado direito)."""
    return (lambda p: p) if sx < 0 else Mo.mirror


def _state(phase):
    """Estado do ciclo: (quadro, giro da mesa em graus, avanco da matriz 0..1, faiscas 0..1)."""
    i = int(round(phase * NF)) % NF
    rot = {5: 22.5, 6: 45.0, 7: 67.5}.get(i, 0.0)
    die = {1: 0.5, 2: 1.0, 3: 1.0, 4: 0.45}.get(i, 0.0)
    spark = {2: 1.0, 3: 0.45}.get(i, 0.0)
    return i, rot, die, spark


def _nests(i):
    """Conteudo de cada estacao (angulo da estacao em graus -> (tipo, deslize radial)).

    Estacoes: W 180 (carga), N 90 (prensa), E 0 (inspecao), S 270 (descarga). Depois do giro (quadro 0) o
    ninho que estava em W (padrao) chegou em N, N (ap) em E, E (ap) em S e S (vazio) em W."""
    if i == 0:
        return {90: ("std", 0.0), 0: ("ap", 0.0), 270: ("ap", 0.0), 180: (None, 0.0)}
    if i == 1:
        return {90: ("std", 0.0), 0: ("ap", 0.0), 270: ("ap", 0.04), 180: ("std", 0.05)}
    return {90: ("ap", 0.0), 0: ("ap", 0.0), 270: (None, 0.0), 180: ("std", 0.0)}


def _chevron(name, cx, cy, ang, M, tags, z=0.03, s=1.0, mat=None):
    """Seta de fluxo (chevron) apontando para ang (graus), em LED fraco sobre um leito escuro."""
    pts = [(-0.05, -0.07), (-0.01, -0.07), (0.05, 0.0), (-0.01, 0.07), (-0.05, 0.07), (0.01, 0.0)]
    pts = [(x * s, y * s) for x, y in pts]
    B.loft(name, _rot(pts, ang, cx, cy), _rot(pts, ang, cx, cy), z, z + 0.006, mat or M["glow_dim"], bevel=0.0,
           tags=tags)


# ============================================================================ piso
def floor(M, T="floor"):
    """Piso opaco: leito escuro do maquinario + bases escuras e discretas das entradas e da saida."""
    tags = (T,)
    K, KM, AM, S = M["core"], M["core_mid"], M["armor_mid"], M["steel"]
    X = _extra()
    B.box("fl_base", 0, 0, 3, 3, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for tx in range(3):
        for ty in range(3):
            cx, cy = tx - 1.0, 1.0 - ty
            p = B.plate(f"fl{tx}{ty}", B.rpoly(cx, cy, 0.94, 0.94, 0, chamfer=0.06), 0.0, 0.03, KM, slope=0.012,
                        tags=tags)
            if ty == 0 or (tx, ty) == (1, 1):
                # leito do maquinario: grade de fendas escuras
                B.cut(p, [B.box(f"flg{tx}{ty}{i}", cx, cy - 0.3 + i * 0.15, 0.7, 0.04, 0.015, 0.1, K, bevel=0.0)
                          for i in range(5)])
    # trilho da saida: moldura escura unica sob as 3 bases
    B.plate("out_rail", B.rpoly(0, -1.0, 2.86, 0.88, 0, chamfer=0.1), 0.03, 0.045, K, slope=0.01, tags=tags)
    # bases: (nome, centro, lado da seta, angulo da seta) - entrada esquerda -> mesa, tristeel -> forja (cima),
    # mesa -> saida do meio (para baixo)
    pads = (("in0", -1.0, 0.0, "e", 0), ("in1", 1.0, 0.0, "n", 90), ("out0", -1.0, -1.0, None, None),
            ("out1", 0.0, -1.0, "n", 270), ("out2", 1.0, -1.0, None, None))
    for name, cx, cy, side, ang in pads:
        # moldura escura (aco escuro) com poco no meio
        fr = B.plate(f"pad_{name}", B.rpoly(cx, cy, 0.86, 0.86, 0, chamfer=0.10), 0.03, 0.062, KM, slope=0.016,
                     tags=tags)
        hole = B.rpoly(cx, cy, 0.70, 0.70, 0, chamfer=0.07)
        cuts = [B.loft(f"pad_h{name}", hole, hole, 0.02, 0.3, K, bevel=0.0)]
        if side:
            # recesso escuro atravessando a moldura para a seta (LED fora da blindagem clara)
            ex, ey = (cx + 0.39, cy) if side == "e" else (cx, cy + 0.39)
            sx_, sy_ = (0.14, 0.30) if side == "e" else (0.30, 0.14)
            cuts.append(B.box(f"pad_n{name}", ex, ey, sx_, sy_, 0.042, 0.3, K, bevel=0.0))
            B.box(f"pad_nb{name}", ex, ey, sx_ - 0.02 if side == "n" else 0.10, sy_ - 0.02 if side == "e" else 0.10,
                  0.036, 0.043, M["black"], bevel=0.0, tags=tags)
            if name == "in1":
                # tristeel: seta para cima (forja) + tracinho frio azul-branco no mesmo recesso escuro
                _chevron("chv_" + name, ex - 0.05, ey, ang, M, tags, z=0.043, s=0.62)
                B.box("fl_glint", ex + 0.085, ey, 0.016, 0.06, 0.043, 0.049, X["glint"], bevel=0.0, tags=tags)
            else:
                _chevron("chv_" + name, ex, ey, ang, M, tags, z=0.043, s=0.62)
        B.cut(fr, cuts)
        # labio fino claro na borda do poco (marca a base sem pesar)
        lip = B.plate(f"padlip_{name}", B.rpoly(cx, cy, 0.73, 0.73, 0, chamfer=0.075), 0.035, 0.056, AM,
                      slope=0.005, bevel=0.004, tags=tags)
        inner = B.rpoly(cx, cy, 0.69, 0.69, 0, chamfer=0.066)
        B.cut(lip, [B.loft(f"padlip_h{name}", inner, inner, 0.02, 0.3, K, bevel=0.0)])
        # fundo do poco + cruz fina da grade da pilha
        B.loft(f"padwell_{name}", inner, inner, 0.03, 0.04, K, bevel=0.0, tags=tags)
        B.box(f"padgv_{name}", cx, cy, 0.012, 0.58, 0.04, 0.046, KM, bevel=0.0, tags=tags)
        B.box(f"padgh_{name}", cx, cy, 0.58, 0.012, 0.04, 0.046, KM, bevel=0.0, tags=tags)
        # cantoneiras em L cinza nos 4 cantos do poco (como a prensa padrao)
        for qx in (-1, 1):
            for qy in (-1, 1):
                ox, oy = cx + qx * 0.325, cy + qy * 0.325
                poly = [(ox, oy), (ox - qx * 0.16, oy), (ox - qx * 0.16, oy - qy * 0.045),
                        (ox - qx * 0.045, oy - qy * 0.045), (ox - qx * 0.045, oy - qy * 0.16), (ox, oy - qy * 0.16)]
                B.plate(f"padbr_{name}{qx}{qy}", poly, 0.04, 0.058, AM, slope=0.008, bevel=0.004, tags=tags)
        # parafusos nos lados da moldura sem seta
        pts = [(cx + 0.39 * dx, cy + 0.39 * dy) for dx, dy, sd in ((1, 0, "e"), (-1, 0, "w"), (0, 1, "n"),
                                                                    (0, -1, "s")) if sd != side]
        B.bolts(f"pbolt_{name}", pts, 0.066, 0.014, S, tags=tags)


# ============================================================================ maquina
def _mini_mag(name, M, X, ang, kind, slide, tags, z0=0.19):
    """Carregador no berco do palete; ang = direcao (graus) da frente, slide = deslize radial."""
    if kind is None:
        return
    u0 = TCX, TCY
    base = NEST_R + slide

    def P(poly):
        return _rot([(base + u, v) for u, v in poly], ang, *u0)

    body = B.rpoly(0, 0, 0.20, 0.145, 0, chamfer=0.03)
    if kind == "std":
        B.loft(name, P(body), P(B.offset_poly(body, 0.015)), z0, z0 + 0.09, M["armor"], bevel=0.008, tags=tags)
        B.loft(name + "_win", P(_rect(0.03, 0.075, -0.045, 0.045)), P(_rect(0.03, 0.075, -0.045, 0.045)), z0 + 0.09,
               z0 + 0.096, M["black"], bevel=0.0, tags=tags)
        for k, v in enumerate((-0.026, 0.0, 0.026)):
            cx, cy = _rot([(base + 0.052, v)], ang, *u0)[0]
            B.cyl(f"{name}_br{k}", cx, cy, z0 + 0.098, 0.011, 0.006, X["brass"], axis="Z", verts=8, bevel=0.0,
                  tags=tags)
        B.loft(name + "_led", P(_rect(-0.06, -0.035, -0.02, 0.02)), P(_rect(-0.06, -0.035, -0.02, 0.02)), z0 + 0.09,
               z0 + 0.097, M["glow_dim"], bevel=0.0, tags=tags)
    else:
        # carregador perfurante: nucleo escuro, tampa clara atras, corpo de aco canhoneado com faixa azul-branca,
        # mandibula clara na frente com janela escura e 3 pontas prateadas saindo
        B.loft(name + "_core", P(body), P(body), z0, z0 + 0.07, M["core"], bevel=0.0, tags=tags)
        bd = _rect(-0.058, 0.012, -0.0725, 0.0725)
        B.loft(name, P(bd), P(B.offset_poly(bd, 0.012)), z0, z0 + 0.09, X["ap_shell"], bevel=0.006, tags=tags)
        B.loft(name + "_band", P(_rect(-0.058, -0.036, -0.076, 0.076)), P(_rect(-0.058, -0.036, -0.076, 0.076)),
               z0 + 0.05, z0 + 0.096, X["band"], bevel=0.0, tags=tags)
        ld = _rect(-0.10, -0.07, -0.07, 0.07)
        B.loft(name + "_lid", P(ld), P(B.offset_poly(ld, 0.006)), z0, z0 + 0.088, X["ap_lid"], bevel=0.004,
               tags=tags)
        for k, (v0, v1) in enumerate(((-0.0725, -0.042), (0.042, 0.0725))):
            jw = _rect(0.032, 0.10, v0, v1)
            B.loft(f"{name}_jaw{k}", P(jw), P(B.offset_poly(jw, 0.006)), z0, z0 + 0.095, M["armor"], bevel=0.004,
                   tags=tags)
        jb = _rect(0.032, 0.05, -0.042, 0.042)
        B.loft(name + "_jawb", P(jb), P(jb), z0, z0 + 0.085, M["armor"], bevel=0.004, tags=tags)
        for k, v in enumerate((-0.025, 0.0, 0.025)):
            ln = 0.075 if k == 1 else 0.06
            cx, cy = _rot([(base + 0.05 + ln / 2, v)], ang, *u0)[0]
            B.cyl(f"{name}_tip{k}", cx, cy, z0 + 0.07, 0.014, ln, X["silver"], axis="Y", verts=6, bevel=0.0,
                  r2=0.0, yaw=ang - 90, tags=tags)


def _table(M, X, tags, i, rot):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    # base fixa do tile central (bloco de maquina) e anel octogonal com parafusos
    B.plate("tb_block", B.rpoly(0, 0, 0.94, 0.94, 0, chamfer=0.16), 0.0, 0.04, K, slope=0.015, tags=tags)
    B.plate("tb_base", _octo(TCX, TCY, 0.475), 0.03, 0.08, KM, slope=0.02, tags=tags)
    B.bolts("tb_bolt", _octo(TCX, TCY, 0.45, 22.5), 0.085, 0.014, S, tags=tags)
    # disco giratorio (nucleo escuro) com 4 paletes claros de bisel duplo (berco escuro em cima) e 4 dentes
    a0 = -rot
    B.plate("tb_disk", _octo(TCX, TCY, 0.43, 22.5 + a0), 0.08, 0.125, K, slope=0.015, tags=tags)
    for k in range(4):
        ang = 90 * k + a0
        pal = PALLET
        B.shard(f"tb_pal{k}", _rot(pal, ang, TCX, TCY), 0.12, 0.172, A, slope=0.02, groove=0.014, panel_h=0.014,
                tags=tags)
        # berco escuro sobre o painel (o carregador assenta nele; vazio = recesso preto no palete claro)
        cr = _rot(B.rpoly(NEST_R, 0.0, 0.212, 0.157, 0, chamfer=0.03), ang, TCX, TCY)
        B.loft(f"tb_cradle{k}", cr, cr, 0.183, 0.19, M["black"], bevel=0.0, tags=tags)
        # dente escuro na borda entre os paletes, com pip ambar
        tooth = [(0.31, -0.035), (0.39, -0.07), (0.425, -0.04), (0.425, 0.04), (0.39, 0.07), (0.31, 0.035)]
        B.plate(f"tb_tooth{k}", _rot(tooth, ang + 45, TCX, TCY), 0.12, 0.165, AM, slope=0.015, tags=tags)
        px, py = _rot([(0.375, 0.0)], ang + 45, TCX, TCY)[0]
        B.cyl(f"tb_pipbed{k}", px, py, 0.168, 0.02, 0.008, M["black"], axis="Z", verts=8, bevel=0.0, tags=tags)
        B.cyl(f"tb_pip{k}", px, py, 0.172, 0.012, 0.006, M["glow"], axis="Z", verts=8, bevel=0.0, tags=tags)
    # cubo central: octogono medio + recesso com LED de indice (forte so enquanto gira)
    B.plate("tb_hub", _octo(TCX, TCY, 0.115, 22.5 + a0), 0.12, 0.21, AM, slope=0.02, tags=tags)
    B.plate("tb_hub2", _octo(TCX, TCY, 0.065, a0), 0.21, 0.235, S, slope=0.01, tags=tags)
    B.cyl("tb_hubled", TCX, TCY, 0.236, 0.022, 0.006, M["glow"] if rot else M["glow_dim"], axis="Z", verts=8,
          bevel=0.0, tags=tags)
    # carregadores nos bercos (giram junto com a mesa)
    for st, (kind, slide) in _nests(i).items():
        _mini_mag(f"mm{st}", M, X, st + a0, kind, slide, tags)
    # estacoes fixas na borda do tile: carga (W), inspecao (E), descarga (S); postes por fora dos paletes
    for name, ang in (("w", 180), ("e", 0), ("s", 270)):
        for sv in (-1, 1):
            g = _rect(0.405, 0.435, sv * 0.14, sv * 0.175)
            B.loft(f"gate_{name}{sv}", _rot(g, ang, TCX, TCY), _rot(g, ang, TCX, TCY), 0.04, 0.17, S, bevel=0.005,
                   tags=tags)
        if name == "e":
            # scanner de inspecao: olho frio azul-branco num casulo escuro
            gx, gy = _rot([(0.445, 0.0)], ang, TCX, TCY)[0]
            sc = _rect(0.42, 0.47, -0.06, 0.06)
            B.loft("scan_body", _rot(sc, ang, TCX, TCY), _rot(sc, ang, TCX, TCY), 0.04, 0.2, KM, bevel=0.008,
                   tags=tags)
            B.box("scan_eye", gx - 0.012, gy, 0.012, 0.07, 0.2, 0.207, X["glint"], bevel=0.0, tags=tags)


def _sparks(M, X, tags, cx, cy, amount):
    """Leque de faiscas laranja saindo do ponto de contato da matriz (dos dois lados)."""
    if amount <= 0:
        return
    rnd = random.Random(7)
    n = 14 if amount > 0.7 else 7
    for k in range(n):
        side = -1 if k % 2 else 1
        a = (rnd.uniform(-35, 25) if side > 0 else 180 + rnd.uniform(-25, 35))
        r0 = 0.07 + rnd.uniform(0, 0.05) + (0.06 if amount < 0.7 else 0.0)
        ln = (0.05 + rnd.uniform(0, 0.06)) * (1.0 if amount > 0.7 else 0.7)
        dx, dy = math.cos(math.radians(a)), math.sin(math.radians(a))
        px, py = cx + dx * (r0 + ln / 2), cy + dy * (r0 + ln / 2)
        B.rbox(f"spark{k}", px, py, 0.012, ln, 0.50, 0.506, X["spark"], rot=a - 90, bevel=0.0, tags=tags)
    # brilho quente no ponto de contato
    B.rbox("hotspot", cx, cy + 0.01, 0.10 * amount + 0.04, 0.03, 0.31, 0.318, X["hot"], bevel=0.0, tags=tags)


def _press(M, X, tags, die, spark, ember=False):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    # leito escuro de toda a fileira de cima
    B.plate("mc_bed", B.rpoly(0, 0.98, 2.90, 0.92, 0, chamfer=0.08), 0.0, 0.05, K, slope=0.01, tags=tags)
    B.box("mc_chan", 0, 0.98, 0.40, 0.88, 0.04, 0.07, M["black"], bevel=0.0, tags=tags)
    # bochechas em garra que agarram a borda da mesa (ponta larga: sem triangulo preto no painel)
    cheek = [(-0.20, 1.40), (-0.40, 1.40), (-0.48, 1.32), (-0.48, 0.70), (-0.44, 0.50), (-0.34, 0.36),
             (-0.24, 0.40), (-0.21, 0.55), (-0.20, 0.62)]
    for side, sx in (("L", -1), ("R", 1)):
        ca, cp = B.shard(f"cheek_{side}", _flip(sx)(cheek), 0.0, 0.50, A, slope=0.07, groove=0.035, panel_h=0.03,
                         tags=tags)
        Mo.slot_with_pips(f"ck_slot{side}", sx * 0.37, 0.76, 1.04, 0.05, 0.53, 4, M, tags, target=[ca, cp],
                          depth=0.075)
        B.cut(cp, [B.rbox(f"ck_pl{side}", sx * 0.40, 0.62, 0.022, 0.22, 0.47, 0.8, K, rot=sx * -22, bevel=0.0)])
        # guia da matriz (trilho de aco no canal)
        B.box(f"die_rail{side}", sx * 0.185, 0.80, 0.022, 0.62, 0.05, 0.24, S, bevel=0.004, tags=tags)
    # cilindro hidraulico do martelo
    B.cyl("ram_cyl", 0, 1.06, 0.36, 0.125, 0.30, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
    for k, y in enumerate((0.93, 1.03, 1.13)):
        B.cyl(f"ram_ring{k}", 0, y, 0.36, 0.135, 0.025, S, axis="Y", verts=8, bevel=0.004, tags=tags)
    # matriz em cunha (bloco claro com bisel duplo) que avanca sobre o ninho N
    fy = DIE_OUT - (DIE_OUT - DIE_IN) * die
    top = fy + 0.27
    rod_len = 0.93 - top
    B.cyl("ram_rod", 0, top + rod_len / 2, 0.36, 0.048, rod_len + 0.02, X["silver"], axis="Y", verts=12,
          bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.cyl(f"guide{sx}", sx * 0.125, top + (1.2 - top) / 2, 0.32, 0.018, 1.2 - top, S, axis="Y", verts=8,
              bevel=0.0, tags=tags)
    head = [(-0.175, fy + 0.27), (0.175, fy + 0.27), (0.175, fy + 0.10), (0.09, fy + 0.0), (-0.09, fy + 0.0),
            (-0.175, fy + 0.10)]
    _, hp = B.shard("die_head", head, 0.22, 0.46, A, slope=0.05, groove=0.025, panel_h=0.025, tags=tags)
    B.cut(hp, [B.box("die_pl", 0, fy + 0.20, 0.30, 0.022, 0.42, 0.6, K, bevel=0.0)])
    for sx in (-1, 1):
        B.box(f"die_ear{sx}", sx * 0.175, fy + 0.18, 0.04, 0.12, 0.24, 0.40, AM, bevel=0.006, tags=tags)
    # inserto da matriz (aco) e cavidade escura na frente
    B.box("die_insert", 0, fy + 0.035, 0.15, 0.07, 0.14, 0.30, S, bevel=0.006, tags=tags)
    B.box("die_cav", 0, fy + 0.01, 0.09, 0.025, 0.28, 0.305, M["black"], bevel=0.0, tags=tags)
    # LED de ciclo no topo da matriz: forte cravando, fraco no resto
    B.box("die_ledbed", 0, fy + 0.13, 0.12, 0.035, 0.46, 0.488, M["black"], bevel=0.0, tags=tags)
    B.box("die_led", 0, fy + 0.13, 0.09, 0.016, 0.47, 0.49, M["glow"] if die >= 1.0 else M["glow_dim"], bevel=0.0,
          tags=tags)
    if die >= 1.0:
        B.box("die_hot", 0, fy + 0.012, 0.08, 0.012, 0.305, 0.31, X["hot"], bevel=0.0, tags=tags)
        # brilho frio na ponta de tristeel sendo cravada
        B.cyl("die_glint", 0.0, fy - 0.03, 0.30, 0.014, 0.006, X["glint"], axis="Z", verts=8, bevel=0.0,
              tags=tags)
    _sparks(M, X, tags, 0.0, fy - 0.01, spark)
    if ember:
        # pontas recem cravadas ainda em brasa enquanto a matriz volta
        B.box("tips_ember", 0.0, TCY + NEST_R + 0.115, 0.10, 0.03, 0.27, 0.276, M["ember"], bevel=0.0, tags=tags)
    # travessa superior (segundo degrau) com respiro e pips
    beam = [(-0.50, 1.18), (0.50, 1.18), (0.57, 1.25), (0.57, 1.36), (0.48, 1.44), (-0.48, 1.44), (-0.57, 1.36),
            (-0.57, 1.25)]
    ba, bp = B.shard("beam", beam, 0.50, 0.66, A, slope=0.05, groove=0.03, panel_h=0.025, tags=tags)
    B.cut(ba, [B.box("beam_vent", 0, 1.31, 0.50, 0.14, 0.60, 0.80, K, bevel=0.0)])
    B.cut(bp, [B.box("beam_vent2", 0, 1.31, 0.50, 0.14, 0.60, 0.80, K, bevel=0.0)])
    B.box("beam_vbed", 0, 1.31, 0.50, 0.14, 0.595, 0.605, M["black"], bevel=0.0, tags=tags)
    for k in range(3):
        B.box(f"beam_louv{k}", 0, 1.265 + k * 0.045, 0.48, 0.016, 0.60, 0.65, KM, bevel=0.003, tags=tags)
    for k, x in enumerate((-0.42, 0.42)):
        B.bolts(f"beam_bolt{k}", [(x, 1.24), (x, 1.38)], 0.69, 0.018, S, tags=tags)


# cascas laterais (lado esquerdo; o direito e o espelho): placa traseira com chanfro grande de 45 graus no canto
# de baixo de dentro (aponta para a prensa) + cunha da frente que abraca esse chanfro (vao escuro de 0.06 reto e
# em diagonal, degrau na borda interna, chanfro de baixo apontando para a mesa) + lamina embaixo
REAR = [(-1.42, 1.30), (-1.30, 1.42), (-0.94, 1.42), (-0.94, 1.06), (-1.155, 0.845), (-1.30, 0.845),
        (-1.42, 0.965)]
WEDGE = [(-0.88, 1.42), (-0.75, 1.42), (-0.64, 1.30), (-0.64, 1.18), (-0.68, 1.14), (-0.68, 1.06), (-0.64, 1.02),
         (-0.64, 0.97), (-0.765, 0.845), (-1.07, 0.845), (-0.88, 1.035)]
BLADE = [(-1.42, 0.785), (-0.88, 0.785), (-0.70, 0.70), (-0.585, 0.545), (-0.74, 0.555), (-1.30, 0.555),
         (-1.42, 0.65)]
WIN_X = 1.18               # centro (|x|) das janelas das placas traseiras
WIN_C = 0.10               # chanfro da janela no canto de baixo de dentro (paralelo ao chanfro da placa)


def _win(sx, d=0.0):
    """Janela da placa traseira do lado sx (encolhida d): retangulo com o canto de baixo de dentro chanfrado."""
    x0, x1, y0, y1 = WIN_X - 0.14 + d, WIN_X + 0.14 - d, FORGE_Y - 0.14 + d, FORGE_Y + 0.14 - d
    c = WIN_C - d * (2 - 2 ** 0.5)
    poly = [(x0 + c, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0 + c)]   # lado direito (dentro = x0)
    return poly if sx > 0 else Mo.mirror(poly)


def _housing(prefix, sx, M, tags, blade_slot=True):
    """Casca lateral: placa traseira (devolve-a para a janela), cunha da frente e lamina em garra."""
    f = _flip(sx)
    K, A, S = M["core"], M["armor"], M["steel"]
    ra, rp = B.shard(prefix + "_rear", f(REAR), 0.0, 0.46, A, slope=0.07, groove=0.035, panel_h=0.03, tags=tags)
    wa, wp = B.shard(prefix + "_wedge", f(WEDGE), 0.0, 0.50, A, slope=0.05, groove=0.025, panel_h=0.03, tags=tags)
    b, bp = B.shard(prefix + "_blade", f(BLADE), 0.0, 0.34, A, slope=0.07, groove=0.03, panel_h=0.025, tags=tags)
    # linhas de painel largas: horizontal sob a janela e diagonal no chanfro de baixo da placa traseira
    B.cut(rp, [B.rbox(prefix + "_pl2", sx * 1.02, 1.345, 0.022, 0.12, 0.42, 0.8, K, rot=sx * 45, bevel=0.0)])
    # cunha: fenda vertical com 3 pips fracos acima do degrau + linha de painel no chanfro
    Mo.slot_with_pips(prefix + "_wsl", sx * 0.76, 1.20, 1.36, 0.04, 0.53, 3, M, tags, target=[wa, wp], depth=0.075,
                      pip_mat=M["glow_dim"])
    B.cut(wp, [B.rbox(prefix + "_wpl", sx * 0.78, 0.96, 0.12, 0.022, 0.46, 0.8, K, rot=sx * 45, bevel=0.0)])
    B.cut(bp, [B.rbox(prefix + "_pl3", sx * 0.80, 0.66, 0.022, 0.14, 0.31, 0.8, K, rot=sx * 55, bevel=0.0)])
    if blade_slot:
        Mo.slot_with_pips(prefix + "_slot", 0.665, sx * 1.26, sx * 0.96, 0.05, 0.37, 4, M, tags, target=[b, bp],
                          depth=0.075, vertical=False)
    # parafusos nos cantos de cima da placa traseira
    B.bolts(prefix + "_bolt", [(sx * 1.33, 1.35), (sx * 1.33, 0.93)], 0.49, 0.018, S, tags=tags)
    return ra, rp, b, bp


def _bezel(prefix, poly_out, poly_in, z0, z1, M, tags, targets):
    """Janela com moldura em degrau: abre poly_out nas pecas e assenta um labio de aco (poly_out - poly_in)
    no meio da profundidade."""
    K, S = M["core"], M["steel"]
    for k, t in enumerate(targets):
        B.cut(t, [B.loft(f"{prefix}_c{k}", poly_out, poly_out, z0, 0.9, K, bevel=0.0)])
    lip = B.plate(prefix + "_lip", poly_out, z1 - 0.06, z1, S, slope=0.012, bevel=0.004, tags=tags)
    B.cut(lip, [B.loft(prefix + "_lc", poly_in, poly_in, z1 - 0.2, z1 + 0.2, K, bevel=0.0)])
    B.loft(prefix + "_bed", poly_out, poly_out, z0 - 0.02, z0, M["black"], bevel=0.0, tags=tags)


def _hydraulics(M, X, tags, phase):
    """Central hidraulica (tile de cima a esquerda): bomba de 2 pistoes alternados na janela em degrau."""
    KM, S = M["core_mid"], M["steel"]
    ra, rp, _, _ = _housing("hyd", -1, M, tags)
    x0, x1, y0, y1 = -WIN_X - 0.14, -WIN_X + 0.14, FORGE_Y - 0.14, FORGE_Y + 0.14
    _bezel("hyd_win", _win(-1), _win(-1, 0.024), 0.30, 0.46, M, tags, (ra, rp))
    # virabrequim no alto da janela e 2 pistoes em camisas escuras, defasados meio ciclo (1 curso por ciclo)
    B.box("hyd_crank", -WIN_X, y1 - 0.045, 0.24, 0.05, 0.30, 0.35, KM, bevel=0.008, tags=tags)
    for k, bx in enumerate((-WIN_X - 0.065, -WIN_X + 0.065)):
        B.box(f"hyd_bore{k}", bx, (y0 + y1) / 2 - 0.02, 0.085, 0.20, 0.30, 0.325, KM, bevel=0.006, tags=tags)
        d = 0.045 * math.cos(2 * math.pi * (phase + 0.5 * k))
        hy = FORGE_Y - 0.035 + d
        B.cyl(f"hyd_rod{k}", bx, (hy + y1 - 0.045) / 2, 0.355, 0.016, y1 - 0.045 - hy, X["silver"], axis="Y",
              verts=8, bevel=0.0, tags=tags)
        B.box(f"hyd_pst{k}", bx, hy, 0.078, 0.065, 0.325, 0.38, M["armor"], bevel=0.012, tags=tags)
        B.box(f"hyd_pstc{k}", bx, hy - 0.022, 0.05, 0.012, 0.38, 0.384, KM, bevel=0.0, tags=tags)
    # LED de pressao fraco entre as camisas
    B.box("hyd_ledbed", -WIN_X, y0 + 0.045, 0.04, 0.035, 0.30, 0.31, M["black"], bevel=0.0, tags=tags)
    B.box("hyd_led", -WIN_X, y0 + 0.045, 0.024, 0.02, 0.31, 0.316, M["glow_dim"], bevel=0.0, tags=tags)
    # mangueira hidraulica no vao ate a prensa + linha de pressao entrando na bochecha esquerda
    B.cyl("hyd_hose", -0.56, 0.86, 0.10, 0.04, 0.40, KM, axis="Y", verts=8, bevel=0.006, tags=tags)
    for k, y in enumerate((0.74, 0.98)):
        B.cyl(f"hyd_clamp{k}", -0.56, y, 0.10, 0.05, 0.03, S, axis="Y", verts=8, bevel=0.004, tags=tags)
    B.cyl("hyd_line", -0.56, FORGE_Y, 0.28, 0.045, 0.22, KM, axis="X", verts=8, bevel=0.006, tags=tags)
    B.cyl("hyd_linr", -0.56, FORGE_Y, 0.28, 0.053, 0.025, S, axis="X", verts=8, bevel=0.004, tags=tags)


def _forge(M, X, tags, phase):
    """Forja de pontas (tile de cima a direita): pontas prateadas deitadas atravessadas andam pela janela ate
    a bobina de inducao, um passo por ciclo (meio passo no quadro da batida)."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    ra, rp, b, bp = _housing("frg", 1, M, tags, blade_slot=False)
    x0, x1, y0, y1 = WIN_X - 0.14, WIN_X + 0.14, FORGE_Y - 0.14, FORGE_Y + 0.14
    _bezel("frg_win", _win(1), _win(1, 0.024), 0.30, 0.46, M, tags, (ra, rp))
    # pontas de tristeel (cones r 0.045 apontando para a mesa, -Y), andando para -X (para a prensa)
    pitch = 0.105
    i = int(round(phase * NF)) % NF
    off = {0: 0.0, 1: 0.0, 2: 0.5}.get(i, 1.0) * pitch
    lead = True
    for k in range(-1, 5):
        x = x0 + 0.10 + k * pitch - off
        if not (x0 + 0.02 < x < x1 - 0.005):
            continue
        ys = FORGE_Y + 0.005
        B.cyl(f"frg_tip{k}", x, ys - 0.015, 0.355, 0.045, 0.15, X["silver_r"], axis="Y", verts=8, bevel=0.0,
              r2=0.0, yaw=180, tags=tags)
        B.cyl(f"frg_tipb{k}", x, ys + 0.075, 0.355, 0.05, 0.03, S, axis="Y", verts=8, bevel=0.0, tags=tags)
        if lead:
            # brilho frio no tristeel (ponta da frente, a proxima a ir para a matriz)
            B.box("frg_glint", x - 0.012, ys + 0.02, 0.012, 0.03, 0.40, 0.406, X["glint"], bevel=0.0, tags=tags)
            lead = False
    # bobina de inducao em brasa na saida da janela (lado da prensa), por cima das pontas
    for k in range(3):
        B.box(f"frg_coil{k}", x0 + 0.04 + k * 0.022, FORGE_Y, 0.010, 0.22, 0.39, 0.42,
              X["hot"] if k == 1 else M["ember"], bevel=0.0, tags=tags)
    # alimentador entrando na bochecha direita pelo vao (sem cruzar a silhueta da prensa) + mangueira
    B.cyl("frg_chute", 0.56, FORGE_Y, 0.28, 0.045, 0.22, KM, axis="X", verts=8, bevel=0.006, tags=tags)
    B.cyl("frg_chr", 0.56, FORGE_Y, 0.28, 0.053, 0.025, S, axis="X", verts=8, bevel=0.004, tags=tags)
    B.cyl("frg_hose", 0.56, 0.86, 0.10, 0.04, 0.40, KM, axis="Y", verts=8, bevel=0.006, tags=tags)
    for k, y in enumerate((0.74, 0.98)):
        B.cyl(f"frg_clamp{k}", 0.56, y, 0.10, 0.05, 0.03, S, axis="Y", verts=8, bevel=0.004, tags=tags)
    # boca de entrada do tristeel na lamina (vem da base de baixo): recesso escuro com 3 setas para cima
    for t, nm in ((b, "a"), (bp, "b")):
        B.cut(t, [B.box(f"frg_in_c{nm}", 1.11, 0.665, 0.30, 0.07, 0.27, 0.8, K, bevel=0.0)])
    B.box("frg_in_bed", 1.11, 0.665, 0.30, 0.07, 0.26, 0.272, M["black"], bevel=0.0, tags=tags)
    for k in range(3):
        _chevron(f"frg_in_chv{k}", 1.01 + k * 0.10, 0.665, 90, M, tags, z=0.272, s=0.38)


def machine(M, T="machine", phase=0.0):
    """Maquinario (fileira de cima + tile central); transparente nos tiles de entrada e saida."""
    tags = (T,)
    X = _extra()
    i, rot, die, spark = _state(phase)
    _table(M, X, tags, i, rot)
    _press(M, X, tags, die, spark, ember=(i == 4))
    _hydraulics(M, X, tags, phase)
    _forge(M, X, tags, phase)


# ============================================================================ teto
def _ledslot(name, cx, cy, sx, sy, z_bed, n, M, tags, targets, vertical=True, pip_mat=None, pw=None):
    """Fenda de LEDs VAZADA nas pecas (sem fundo: o bisel reaplicado nao cria filete no canto de baixo, que
    tamparia as bordas do leito) com leito preto e n pips em cima de z_bed (topo da peca de baixo); pw = largura
    dos pips (padrao 55% da fenda)."""
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.box(f"{name}_c{k}", cx, cy, sx, sy, z_bed - 0.02, z_bed + 0.6, M["black"], bevel=0.0)])
    B.box(name + "_bed", cx, cy, sx, sy, z_bed, z_bed + 0.008, M["black"], bevel=0.0, tags=tags)
    L = sy if vertical else sx
    for i in range(n):
        t = (i + 0.5) / n - 0.5
        px, py = (cx, cy + t * L) if vertical else (cx + t * L, cy)
        a, b = ((pw or sx * 0.55, L / n * 0.55) if vertical else (L / n * 0.55, pw or sy * 0.55))
        B.box(f"{name}_pip{i}", px, py, a, b, z_bed + 0.008, z_bed + 0.02, pip_mat or M["glow"], bevel=0.0, tags=tags)


def _inlay(name, poly, targets, z1, green, tags, gap=0.03):
    """Placa em seta embutida: abre um furo (contorno + vao) nas placas de base e assenta a seta no fundo escuro."""
    hole = B.offset_poly(poly, -gap)
    for k, t in enumerate(targets):
        B.cut(t, [B.loft(f"{name}_h{k}", hole, hole, -0.01, 0.5, green, bevel=0.0)])
    return B.shard(name, poly, 0.0, z1, green, slope=0.05, groove=0.03, panel_h=0.018, tags=tags)


# coroa da prensa (lado esquerdo; o direito e o espelho)
CROWN = [(-0.69, 1.46), (0.69, 1.46), (0.69, 0.95), (0.40, 0.36), (-0.40, 0.36), (-0.69, 0.95)]
SPINE = [(-0.20, 1.43), (0.20, 1.43), (0.25, 1.37), (0.25, 0.86), (0.08, 0.47), (-0.08, 0.47), (-0.25, 0.86),
         (-0.25, 1.37)]
SPINE2 = [(-0.12, 1.32), (0.12, 1.32), (0.15, 1.28), (0.15, 0.92), (0.055, 0.70), (-0.055, 0.70), (-0.15, 0.92),
          (-0.15, 1.28)]
CLAW = [(-0.31, 1.43), (-0.57, 1.43), (-0.65, 1.35), (-0.65, 1.10), (-0.59, 1.04), (-0.59, 0.90), (-0.47, 0.62),
        (-0.37, 0.40), (-0.27, 0.43), (-0.24, 0.62), (-0.31, 0.83)]
RBLADE = [(-1.38, 1.00), (-1.38, 0.85), (-1.02, 0.66), (-0.65, 0.61), (-0.72, 0.71), (-1.20, 1.00)]


def roof(M, T="roof"):
    """Teto verde (pintura da nave) com a coroa blindada sem pintura sobre a prensa e o colar segmentado
    sobre a mesa; setas pintadas das entradas (meio) e da saida (embaixo)."""
    tags = (T,)
    green = B.mat_roof_green()
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    X = _extra()
    B.box("rf_under", 0, 0, 3, 3, -0.05, 0.02, K, bevel=0.0, tags=tags)

    # ---- fileira de cima, laterais: placas pintadas seguindo o chanfro da coroa (vao escuro de 0.06), respiro
    # no canto de fora e lamina clara em diagonal apontando para a mesa
    side = [(-1.45, 1.33), (-1.33, 1.45), (-0.75, 1.45), (-0.75, 0.936), (-0.563, 0.555), (-1.33, 0.555),
            (-1.45, 0.675)]
    for sx in (-1, 1):
        f = _flip(sx)
        B.shard(f"rf_ts{sx}", f(side), 0.0, 0.075, green, slope=0.03, groove=0.05, panel_h=0.022, tags=tags)
        rv = B.box(f"rf_sv{sx}", sx * 1.12, 1.24, 0.36, 0.24, 0.07, 0.125, KM, bevel=0.008, slope=0.012, tags=tags)
        B.cut(rv, [B.box(f"rf_svc{sx}{k}", sx * 1.12, 1.165 + k * 0.05, 0.28, 0.022, 0.105, 0.3, K, bevel=0.0)
                   for k in range(4)])
        B.bolts(f"rf_svb{sx}", [(sx * 0.88, 1.33), (sx * 0.88, 1.15)], 0.095, 0.017, S, tags=tags)
        # lamina com base escura (clara sobre escuro) e fenda de luz fraca num recesso
        bl = f(RBLADE)
        B.plate(f"rf_bl_core{sx}", B.offset_poly(bl, -0.03), 0.06, 0.10, K, slope=0.01, tags=tags)
        ba, bp = B.shard(f"rf_bl{sx}", bl, 0.09, 0.21, A, slope=0.045, groove=0.02, panel_h=0.02, tags=tags)
        cx_, cy_, ang = sx * 1.05, 0.79, sx * 25.0
        for t, nm in ((ba, "a"), (bp, "b")):
            B.cut(t, [B.rbox(f"rf_blc{sx}{nm}", cx_, cy_, 0.24, 0.03, 0.16, 0.6, K, rot=ang, bevel=0.0)])
        B.rbox(f"rf_blbed{sx}", cx_, cy_, 0.24, 0.03, 0.155, 0.165, M["black"], rot=ang, bevel=0.0, tags=tags)
        B.rbox(f"rf_blglow{sx}", cx_, cy_, 0.18, 0.011, 0.165, 0.171, M["glow_dim"], rot=ang, bevel=0.0, tags=tags)

    # ---- coroa blindada sem pintura (tile de cima do meio): nucleo escuro em seta, espinha em cunha com olho
    # frio e 4 pips, garras que descem ate o colar da mesa
    B.plate("cr_core", CROWN, 0.03, 0.12, K, slope=0.02, tags=tags)
    B.shard("cr_spine", SPINE, 0.10, 0.34, A, slope=0.08, groove=0.03, panel_h=0.03, tags=tags)
    s2 = B.plate("cr_spine2", SPINE2, 0.37, 0.45, A, slope=0.03, tags=tags)
    win = [(-0.06, 0.90), (0.06, 0.90), (0.06, 0.98), (0.035, 1.01), (-0.035, 1.01), (-0.06, 0.98)]
    B.cut(s2, [B.loft("cr_winc", win, win, 0.40, 0.7, K, bevel=0.0)])
    B.loft("cr_winbed", win, win, 0.395, 0.405, M["black"], bevel=0.0, tags=tags)
    B.box("cr_eye", 0, 0.945, 0.08, 0.018, 0.405, 0.412, X["glint"], bevel=0.0, tags=tags)
    _ledslot("cr_sl", 0.0, 1.14, 0.18, 0.055, 0.37, 4, M, tags, [s2], vertical=False, pip_mat=M["glow_dim"])
    B.cyl("cr_cap", 0, 1.25, 0.45, 0.06, 0.03, S, axis="Z", verts=8, bevel=0.008, tags=tags)
    B.cyl("cr_cap2", 0, 1.25, 0.47, 0.034, 0.02, KM, axis="Z", verts=8, bevel=0.005, tags=tags)
    for sx in (-1, 1):
        ca, cp = B.shard(f"cr_claw{sx}", _flip(sx)(CLAW), 0.10, 0.30, A, slope=0.06, groove=0.03, panel_h=0.025,
                         tags=tags)
        # baia de respiro no alto da garra (recesso escuro com persianas) + linhas de painel largas
        vx, vy = sx * 0.475, 1.22
        for t, nm in ((ca, "a"), (cp, "b")):
            B.cut(t, [B.box(f"cr_cv{sx}{nm}", vx, vy, 0.14, 0.16, 0.24, 0.6, K, bevel=0.0)])
        B.box(f"cr_cvbed{sx}", vx, vy, 0.14, 0.16, 0.235, 0.242, M["black"], bevel=0.0, tags=tags)
        for k in range(3):
            B.box(f"cr_cvl{sx}{k}", vx, vy - 0.05 + k * 0.05, 0.12, 0.018, 0.242, 0.29, KM, bevel=0.003, tags=tags)
        if cp is not None:
            B.cut(cp, [B.rbox(f"cr_clp{sx}a", sx * 0.47, 1.06, 0.16, 0.022, 0.26, 0.6, K, bevel=0.0),
                       B.rbox(f"cr_clp{sx}b", sx * 0.43, 0.70, 0.18, 0.022, 0.26, 0.6, K, rot=sx * 60, bevel=0.0)])
        B.bolts(f"cr_clb{sx}", [(sx * 0.44, 1.36)], 0.325, 0.017, S, tags=tags)
        # linha hidraulica no vao entre espinha e garra
        B.cyl(f"cr_line{sx}", sx * 0.28, 1.12, 0.17, 0.016, 0.42, S, axis="Y", verts=8, bevel=0.0, tags=tags)

    # ---- colar octogonal segmentado sobre a mesa (tile central): 4 segmentos claros nas diagonais, vaos nas
    # direcoes do fluxo (prensa em cima, entradas nos lados, saida embaixo) e escotilha no meio
    B.plate("cc_base", _octo(0, 0, 0.47), 0.03, 0.10, K, slope=0.02, tags=tags)
    seg = [(0.07, 0.283), (0.283, 0.07), (0.425, 0.07), (0.425, 0.176), (0.176, 0.425), (0.07, 0.425)]
    for qx in (-1, 1):
        for qy in (-1, 1):
            pts = [(x * qx, y * qy) for x, y in seg]
            if qx * qy < 0:
                pts = list(reversed(pts))
            B.shard(f"cc_seg{qx}{qy}", pts, 0.08, 0.19, A, slope=0.04, groove=0.02, panel_h=0.02, tags=tags)
            # parafuso no meio do segmento
            B.bolts(f"cc_b{qx}{qy}", [(qx * 0.245, qy * 0.245)], 0.215, 0.016, S, tags=tags)
    B.plate("cc_hatch", _octo(0, 0, 0.20), 0.08, 0.16, AM, slope=0.02, tags=tags)
    B.plate("cc_hatch2", _octo(0, 0, 0.12), 0.16, 0.18, KM, slope=0.012, tags=tags)
    B.bolts("cc_hb", B.ring_points(0, 0, 0.16, 8, math.radians(22.5)), 0.165, 0.014, S, tags=tags)
    B.box("cc_ledbed", 0, 0, 0.12, 0.045, 0.175, 0.185, K, bevel=0.0, tags=tags)
    B.box("cc_led", 0, 0, 0.09, 0.02, 0.18, 0.19, M["glow_dim"], bevel=0.0, tags=tags)
    # pino do martelo descendo da ponta da espinha (vao de cima) e travas de aco nos outros vaos
    B.cyl("cc_pin", 0, 0.36, 0.17, 0.05, 0.10, S, axis="Z", verts=8, bevel=0.008, tags=tags)
    B.cyl("cc_pin2", 0, 0.36, 0.225, 0.028, 0.02, KM, axis="Z", verts=8, bevel=0.004, tags=tags)
    for nm, (lx, ly, sx_, sy_) in (("w", (-0.34, 0, 0.12, 0.07)), ("e", (0.34, 0, 0.12, 0.07)),
                                   ("s", (0, -0.34, 0.07, 0.12))):
        B.box(f"cc_latch{nm}", lx, ly, sx_, sy_, 0.08, 0.14, S, bevel=0.01, tags=tags)

    # ---- meio: placas laterais (sobre as entradas) com placa em seta apontando para a mesa
    for sx in (-1, 1):
        ma, mp = B.shard(f"rf_mid{sx}", B.rpoly(sx * 1.0, 0.0, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.06, green,
                         slope=0.025, groove=0.05, panel_h=0.02, tags=tags)
        B.cut(mp, [B.rbox(f"rf_md{sx}{k}", sx * 1.0, dy, 0.62, 0.022, 0.03, 0.3, K, bevel=0.0)
                   for k, dy in enumerate((-0.34, 0.34))])
        arrow = [(sx * 1.32, 0.24), (sx * 0.98, 0.24), (sx * 0.74, 0.0), (sx * 0.98, -0.24), (sx * 1.32, -0.24)]
        aa, ap = _inlay(f"rf_arr{sx}", arrow, (ma, mp), 0.13, green, tags)
        _ledslot(f"rf_ap{sx}", sx * 1.165, 0.0, 0.075, 0.20, 0.02, 2, M, tags, [aa, ap], pw=0.034)
        B.bolts(f"rf_mb{sx}", [(sx * 1.0 + dx, dy) for dx in (-0.37, 0.37) for dy in (-0.37, 0.37)], 0.08, 0.016, S,
                tags=tags)

    # ---- fileira de baixo (saida): 3 placas; a do meio com seta para baixo, as laterais com painel em degrau
    for k, cx in enumerate((-1.0, 0.0, 1.0)):
        ba, bp = B.shard(f"rf_bot{k}", B.rpoly(cx, -1.0, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.07, green,
                         slope=0.03, groove=0.05, panel_h=0.022, tags=tags)
        if k == 1:
            arrow = [(-0.28, -0.66), (0.28, -0.66), (0.28, -1.02), (0.0, -1.28), (-0.28, -1.02)]
            aa, ap = _inlay("rf_barr", arrow, (ba, bp), 0.14, green, tags)
            _ledslot("rf_bpips", 0.0, -0.84, 0.27, 0.075, 0.02, 3, M, tags, [aa, ap], vertical=False, pw=0.034)
            B.cut(bp, [B.rbox(f"rf_bd{sx}", sx * 0.33, -1.30, 0.022, 0.16, 0.04, 0.3, K, rot=sx * 45, bevel=0.0)
                       for sx in (-1, 1)])
        else:
            sx = -1 if cx < 0 else 1
            # painel em degrau (L de linhas largas) + alca de aco num recesso + parafusos
            B.cut(bp, [B.rbox(f"rf_bl{k}a", cx, -0.80, 0.62, 0.022, 0.04, 0.3, K, bevel=0.0),
                       B.rbox(f"rf_bl{k}b", cx - sx * 0.20, -1.06, 0.022, 0.50, 0.04, 0.3, K, bevel=0.0),
                       B.rbox(f"rf_bl{k}c", cx + sx * 0.22, -1.30, 0.022, 0.16, 0.04, 0.3, K,
                              rot=sx * -45, bevel=0.0)])
            # respiro de persianas (sem pintura) no alto do painel em L + alca de aco num recesso embaixo dele
            vx = cx + sx * 0.06
            rv = B.box(f"rf_bv{k}", vx, -0.99, 0.34, 0.20, 0.07, 0.125, KM, bevel=0.008, slope=0.012, tags=tags)
            B.cut(rv, [B.box(f"rf_bvc{k}{i}", vx, -1.05 + i * 0.04, 0.26, 0.02, 0.105, 0.3, K, bevel=0.0)
                       for i in range(4)])
            B.box(f"rf_bgb{k}", vx, -1.19, 0.26, 0.07, 0.07, 0.085, K, bevel=0.0, tags=tags)
            B.box(f"rf_bg{k}", vx, -1.19, 0.20, 0.035, 0.085, 0.115, S, bevel=0.008, tags=tags)
            B.bolts(f"rf_bb{k}", [(cx - 0.36, -1.36), (cx + 0.36, -1.36), (cx + sx * 0.36, -0.66)], 0.095, 0.016,
                    S, tags=tags)

    # o verde do conves nao reflete nem rebate luz nas pecas sem pintura (senao a pintura vaza nas bordas claras)
    for o in B.bpy.context.scene.objects:
        if o.type == "MESH" and o.get(T) and any(m is green for m in o.data.materials):
            o.visible_glossy = False
            o.visible_diffuse = False
