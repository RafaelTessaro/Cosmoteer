"""Fundicao de Projeteis Nucleares (Nuclear Shell Foundry) 3x3 - celula quente blindada que monta o Projetil
Nuclear: uranio enriquecido + 2 Carregadores Padrao -> 1 Projetil Nuclear (800 de bateria por ciclo, fim de jogo).

Layout vanilla factory_he (tools/bsgen/factory.py): fileira de cima + tile central = maquinario (bloqueado);
entradas no meio das laterais: tile (0,1) esquerda = uranio enriquecido, tile (2,1) direita = Carregadores
Padrao; saida = fileira de baixo inteira. O jogo desenha as pilhas nesses 5 tiles, entao eles ficam livres de
maquinario e o piso mostra bases escuras marcadas (cantoneiras, labio fino, setas verdes em recesso).
Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade = 1 tile.

Maquina (mesma familia das armas: cascas claras chanfradas com bisel duplo sobre nucleo escuro, luz verde
so em recessos escuros):
  * camara de fundicao blindada no tile de cima do meio: parede grossa em cunha apontando para o berco,
    moldura de segundo degrau em volta de uma janela retangular de vidro de chumbo escuro (moldura de aco em
    degrau) por onde se ve o cadinho com o banho verde pulsando; fendas com pips verdes, respiro traseiro;
    portas de transferencia escuras nos dois chanfros de baixo;
  * dois manipuladores remotos articulados nos cantos de cima: tampao blindado de parede (torre do ombro),
    braco e antebraco de casca clara sobre viga escura com cilindros hidraulicos de aco, cotovelo de aco com
    LED, punho e garra de 2 dedos. O da esquerda leva o nucleo verde da porta ate o estojo aberto, o da
    direita leva a ogiva ate a ponta do projetil. Colunas blindadas nos cantos de fora, casco de chumbo
    (esquerda) e estante de ogivas (direita) no leito escuro por baixo do curso dos bracos;
  * berco de montagem blindado no tile central: calha escura com o estojo partido em 2 metades (as mesmas
    medidas do Projetil Nuclear, parts/bs_shell_nuke.py, em 0.72), 2 mordentes pesados de grampo (bloco
    escuro + casca clara) que correm em trilhos de aco, e capuz de saida embaixo (o projetil pronto desce por
    baixo dele para a saida).
Animacao (12 quadros, 0.11 s): 0 estojo aberto, garras nas portas (nucleo e ogiva presos); 1-3 o braco
esquerdo leva o nucleo (o banho pulsa forte quando o nucleo sai); 2-4 o braco direito leva a ogiva; 4-5 as
metades fecham; 6 o grampo bate com lampejo verde pelas costuras; 7-8 o lampejo apaga e o grampo solta;
9-10 o projetil desce para a saida; 11 berco vazio, novos nucleo e ogiva saindo das portas.
Teto: placas verdes (pintura) em blindagem extra pesada de 2 degraus, ombreiras dos manipuladores com tampa
de aco e laminas claras apontando para o centro, tampa da celula quente sem pintura em degraus com visor
verde, e o emblema do tile central: trevo de 3 laminas de blindagem clara sobre base escura com pips verdes
entre as laminas; setas das entradas e da saida com pips verdes em fendas vazadas.
"""

import math

import bs3d as B
import models as Mo
from parts import bs_shell_nuke as NK

PART = {
    "id": "rafaeltessaro.bs_factory_shell_nuke",
    "kind": "factory",
    "size": [3, 3],
    "accent": "green",
    "machine_frames": 12,
    "machine_interval": 0.11,
}

NF = PART["machine_frames"]
SC = 0.72                    # escala do Projetil Nuclear no berco
SY = 0.09                    # deslocamento em y do projetil no berco (y_berco = y_item * SC + SY)
SZ = 0.05                    # fundo do estojo (apoiado na calha)
# camara de fundicao: parede de baixo (cunha apontando para o berco), moldura do 2o degrau e janela
CH = [(-0.44, 1.43), (0.44, 1.43), (0.48, 1.39), (0.48, 1.00), (0.20, 0.59), (-0.20, 0.59), (-0.48, 1.00),
      (-0.48, 1.39)]
T2 = [(-0.36, 1.375), (0.36, 1.375), (0.405, 1.33), (0.405, 1.00), (0.16, 0.66), (-0.16, 0.66), (-0.405, 1.00),
      (-0.405, 1.33)]
WC = (0.0, 1.06)             # centro da janela / cadinho
WIN = (0.44, 0.32)           # janela (largura, altura)
CRU_R = 0.135                # raio do aro do cadinho (octogono)
# manipuladores (lado esquerdo; o direito e o espelho)
SH = (-1.0, 0.78)            # ombro
L1, L2, LC = 0.52, 0.62, 0.15  # braco, antebraco, garra
PORT = (-0.37, 0.83)         # ponta da garra na porta de transferencia (chanfro esquerdo da camara)
CORE_AT = (-0.03, 0.04)      # ponta da garra esquerda sobre a janela do estojo
CAP_AT = (0.05, 0.31)        # ponta da garra direita sobre a ponta do projetil


# ============================================================================ estados da animacao
def _state(phase):
    """Estado do ciclo (dicionario) para o quadro da fase."""
    i = int(round(phase * NF)) % NF
    return {
        "i": i,
        # trajeto das garras (0 = porta, 1 = estojo) e o que seguram
        "L": [0.0, 0.45, 0.85, 1.0, 0.6, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0][i],
        "R": [0.0, 0.0, 0.4, 0.8, 1.0, 0.55, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0][i],
        "Lhold": i in (0, 1, 2, 11),
        "Rhold": i in (0, 1, 2, 3, 11),
        "Lopen": i in (3, 4, 5, 6, 7, 8, 9, 10),
        "Ropen": i in (4, 5, 6, 7, 8, 9, 10),
        # nucleo / ogiva saindo das portas entre os dedos abertos
        "port_core": {8: 0.55, 9: 0.8, 10: 1.0}.get(i, 0.0),
        "port_cap": i in (9, 10),
        # estojo: abertura das metades (1 aberto), grampo (1 fechado), lampejo, conteudo, descida
        "gap": [1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.6][i],
        "clamp": [0.0, 0.0, 0.0, 0.0, 0.0, 0.55, 1.0, 1.0, 0.45, 0.0, 0.0, 0.0][i],
        "flash": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.4, 0.12, 0.0, 0.0, 0.0][i],
        "core_in": i in (3, 4, 5, 6, 7, 8, 9, 10),
        "cap_on": i in (4, 5, 6, 7, 8, 9, 10),
        "slide": {9: 0.10, 10: 0.36}.get(i, 0.0),
        "lit": i in (3, 4, 5, 6, 7, 8, 9, 10),     # faixas do estojo acendem quando o nucleo entra
        "ready": i == 11,                          # LED de pronto no fundo da calha (metades novas chegando)
        # banho do cadinho (forca da emissao)
        "melt": [1.0, 2.0, 1.5, 1.2, 0.95, 0.75, 0.7, 0.75, 0.8, 0.85, 0.95, 1.0][i],
    }


# ============================================================================ utilidades
def _extra(st=None):
    melt = st["melt"] if st else 1.0
    flash = st["flash"] if st else 0.0
    X = dict(NK.mats())   # mesmos materiais do Projetil Nuclear (corpo, ogiva, aco claro, nucleo, faixas)
    X.update({
        "cap": X["ogive"],
        # banho do cadinho: verde saturado (forca <= ~1.2 para nao estourar em branco), centro mais quente
        "melt": B.mat_glow("nk_melt", (0.30, 1.0, 0.14), 0.42 + 0.30 * melt),
        "melt_hot": B.mat_glow("nk_melt_hot", (0.36, 1.0, 0.18), 0.6 + 0.45 * melt),
        "flash": B.mat_glow("nk_flash", (0.35, 1.0, 0.16), 1.2 + 1.8 * flash),
        "lead": B.mat_metal("nk_lead", (0.075, 0.08, 0.085), rough=0.55, metal=0.5),
        # cinza medio fosco das cascas secundarias (sem desgaste: nao clareia nas quinas)
        "mid": B.mat_paint("nk_mid", (0.26, 0.268, 0.28), rough=0.5, metal=0.3, wear=0.0, grime=0.05, scale=4),
        # fundo do poco da janela: preto esverdeado (vidro de chumbo visto por dentro)
        "wbed": B.mat_metal("nk_wbed", (0.006, 0.016, 0.010), rough=0.5, metal=0.2),
        # reflexo claro no vidro (riscos diagonais no canto da janela)
        "glint": B.mat_paint("nk_glint", (0.72, 0.80, 0.78), rough=0.15, metal=0.0, wear=0.0, grime=0.0, scale=4),
    })
    return X


def _roof_led():
    """LED do teto: verde-lima com R alto e B zero. O shader do teto (swapAllegianceColor) troca pela pintura
    todo pixel com g - max(r, b) > .05 e |r - b| < .25; o verde puro das luzes cairia nesse teste. Com
    r/g >= ~0.9 (sRGB) e b = 0 nem o nucleo, nem as bordas misturadas com a blindagem, nem o halo sobre o leito
    escuro passam no teste (com r/g < 0.83 a mistura com cinza neutro ja cai no teste).
    Forca baixa: acima de ~1 o vermelho e o verde saturam juntos e a luz vira amarela."""
    return B.mat_glow("nk_roof_led", (0.80, 1.0, 0.0), 0.7)


def _holdout():
    """Material Holdout: tapa o que fica atras e sai transparente (o projetil que desce para a saida)."""
    m = B.bpy.data.materials.get("nk_holdout")
    if m is None:
        m = B.bpy.data.materials.new("nk_holdout")
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        nt.links.new(nt.nodes.new("ShaderNodeHoldout").outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs[0])
    return m


def _rot(pts, ang, cx=0.0, cy=0.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def _octo(cx, cy, r, a0=22.5):
    return [(cx + r * math.cos(math.radians(a0 + 45 * i)), cy + r * math.sin(math.radians(a0 + 45 * i)))
            for i in range(8)]


def _flip(sx):
    """Poligono do lado esquerdo -> lado sx (espelho em x para o lado direito)."""
    return (lambda p: p) if sx < 0 else Mo.mirror


def _chevron(name, cx, cy, ang, M, tags, z=0.03, s=1.0, mat=None):
    """Seta de fluxo (chevron) apontando para ang (graus), em LED fraco."""
    pts = [(-0.05, -0.07), (-0.01, -0.07), (0.05, 0.0), (-0.01, 0.07), (-0.05, 0.07), (0.01, 0.0)]
    pts = [(x * s, y * s) for x, y in pts]
    B.loft(name, _rot(pts, ang, cx, cy), _rot(pts, ang, cx, cy), z, z + 0.006, mat or M["glow_dim"], bevel=0.0,
           tags=tags)


def _link(p0, p1, w0, w1, c=0.03, ext0=0.0, ext1=0.0):
    """Elo afunilado de p0 a p1 (larguras w0 -> w1) com cantos chanfrados; ext estende/encurta as pontas."""
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
    """Braco de 2 elos (L1, L2 + garra LC rigida) do ombro S ate a ponta T; side = lado do cotovelo."""
    dx, dy = T[0] - S[0], T[1] - S[1]
    d = min(math.hypot(dx, dy), L1 + L2 + LC - 1e-4)
    a = math.atan2(dy, dx)
    c = (L1 * L1 + d * d - (L2 + LC) ** 2) / (2 * L1 * d)
    b = math.acos(max(-1.0, min(1.0, c)))
    ae = a + side * b
    E = (S[0] + L1 * math.cos(ae), S[1] + L1 * math.sin(ae))
    fa = math.atan2(T[1] - E[1], T[0] - E[0])
    W = (E[0] + L2 * math.cos(fa), E[1] + L2 * math.sin(fa))
    return E, W, fa


def _ledslot(name, cx, cy, sx, sy, z_bed, n, M, tags, targets, vertical=True, pip_mat=None, pw=None, rot=0.0):
    """Fenda de LEDs VAZADA nas pecas (sem fundo: o bisel reaplicado nao cria filete que tape o leito) com leito
    preto e n pips em cima de z_bed (topo da peca de baixo); rot gira a fenda em volta do centro."""
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.rbox(f"{name}_c{k}", cx, cy, sx, sy, z_bed - 0.02, z_bed + 0.6, M["black"], rot=rot,
                             bevel=0.0)])
    B.rbox(name + "_bed", cx, cy, sx, sy, z_bed, z_bed + 0.008, M["black"], rot=rot, bevel=0.0, tags=tags)
    L = sy if vertical else sx
    a = math.radians(rot)
    for i in range(n):
        t = (i + 0.5) / n - 0.5
        lx, ly = (0.0, t * L) if vertical else (t * L, 0.0)
        px, py = cx + lx * math.cos(a) - ly * math.sin(a), cy + lx * math.sin(a) + ly * math.cos(a)
        w_, h_ = ((pw or sx * 0.55, L / n * 0.55) if vertical else (L / n * 0.55, pw or sy * 0.55))
        B.rbox(f"{name}_pip{i}", px, py, w_, h_, z_bed + 0.008, z_bed + 0.02, pip_mat or M["glow"], rot=rot,
               bevel=0.0, tags=tags)


# ============================================================================ piso
def floor(M, T="floor"):
    """Piso opaco: leito escuro do maquinario + bases escuras marcadas das entradas e da saida."""
    tags = (T,)
    K, KM, AM, S = M["core"], M["core_mid"], M["armor_mid"], M["steel"]
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
    # bases: (nome, centro, lado da seta, angulo da seta): uranio -> berco, carregadores -> berco, berco -> saida
    pads = (("in0", -1.0, 0.0, "e", 0), ("in1", 1.0, 0.0, "w", 180), ("out0", -1.0, -1.0, None, None),
            ("out1", 0.0, -1.0, "n", 270), ("out2", 1.0, -1.0, None, None))
    for name, cx, cy, side, ang in pads:
        fr = B.plate(f"pad_{name}", B.rpoly(cx, cy, 0.86, 0.86, 0, chamfer=0.10), 0.03, 0.062, KM, slope=0.016,
                     tags=tags)
        hole = B.rpoly(cx, cy, 0.70, 0.70, 0, chamfer=0.07)
        cuts = [B.loft(f"pad_h{name}", hole, hole, 0.02, 0.3, K, bevel=0.0)]
        if side:
            ex, ey = {"e": (cx + 0.39, cy), "w": (cx - 0.39, cy), "n": (cx, cy + 0.39)}[side]
            sx_, sy_ = (0.14, 0.30) if side in ("e", "w") else (0.30, 0.14)
            cuts.append(B.box(f"pad_n{name}", ex, ey, sx_, sy_, 0.042, 0.3, K, bevel=0.0))
            B.box(f"pad_nb{name}", ex, ey, sx_ - 0.02 if side == "n" else 0.10, sy_ - 0.02 if side != "n" else 0.10,
                  0.036, 0.043, M["black"], bevel=0.0, tags=tags)
            _chevron("chv_" + name, ex, ey, ang, M, tags, z=0.043, s=0.62)
        B.cut(fr, cuts)
        # labio fino claro na borda do poco
        lip = B.plate(f"padlip_{name}", B.rpoly(cx, cy, 0.73, 0.73, 0, chamfer=0.075), 0.035, 0.056, AM,
                      slope=0.005, bevel=0.004, tags=tags)
        inner = B.rpoly(cx, cy, 0.69, 0.69, 0, chamfer=0.066)
        B.cut(lip, [B.loft(f"padlip_h{name}", inner, inner, 0.02, 0.3, K, bevel=0.0)])
        # fundo do poco (chapa de chumbo) + cruz fina da grade da pilha
        B.loft(f"padwell_{name}", inner, inner, 0.03, 0.04, K, bevel=0.0, tags=tags)
        B.box(f"padgv_{name}", cx, cy, 0.012, 0.58, 0.04, 0.046, KM, bevel=0.0, tags=tags)
        B.box(f"padgh_{name}", cx, cy, 0.58, 0.012, 0.04, 0.046, KM, bevel=0.0, tags=tags)
        # cantoneiras em L nos 4 cantos do poco
        for qx in (-1, 1):
            for qy in (-1, 1):
                ox, oy = cx + qx * 0.325, cy + qy * 0.325
                poly = [(ox, oy), (ox - qx * 0.16, oy), (ox - qx * 0.16, oy - qy * 0.045),
                        (ox - qx * 0.045, oy - qy * 0.045), (ox - qx * 0.045, oy - qy * 0.16), (ox, oy - qy * 0.16)]
                B.plate(f"padbr_{name}{qx}{qy}", poly, 0.04, 0.058, AM, slope=0.008, bevel=0.004, tags=tags)
        pts = [(cx + 0.39 * dx, cy + 0.39 * dy) for dx, dy, sd in ((1, 0, "e"), (-1, 0, "w"), (0, 1, "n"),
                                                                    (0, -1, "s")) if sd != side]
        B.bolts(f"pbolt_{name}", pts, 0.066, 0.014, S, tags=tags)


# ============================================================================ maquina: camara de fundicao
def _chamber(M, X, tags, st):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    wx, wy = WC
    # leito escuro de toda a fileira de cima
    B.plate("mc_bed", B.rpoly(0, 0.98, 2.90, 0.92, 0, chamfer=0.08), 0.0, 0.05, K, slope=0.01, tags=tags)
    # base escura um pouco maior que a blindagem (moldura escura em volta)
    B.plate("ch_core", B.offset_poly(CH, -0.03), 0.0, 0.16, K, slope=0.02, tags=tags)
    # parede grossa (1o degrau) e moldura (2o degrau), ambas com bisel duplo
    wa, wp = B.shard("ch_wall", CH, 0.0, 0.40, A, slope=0.08, groove=0.035, panel_h=0.03, tags=tags)
    fa, fp = B.shard("ch_frame", T2, 0.40, 0.52, A, slope=0.04, groove=0.018, panel_h=0.022, tags=tags)
    # janela: abertura em degrau (moldura mais larga que a abertura da parede); o poco e raso para o sol
    # entrar e iluminar o cadinho (sem vidro transmissivo: ele escurecia e sombreava tudo atras)
    w_out = B.rpoly(wx, wy, WIN[0] + 0.08, WIN[1] + 0.08, 0, chamfer=0.08)
    w_in = B.rpoly(wx, wy, WIN[0], WIN[1], 0, chamfer=0.065)
    for k, t in enumerate((fa, fp)):
        B.cut(t, [B.loft(f"ch_fh{k}", w_out, w_out, 0.36, 0.9, K, bevel=0.0)])
    for k, t in enumerate((wa, wp)):
        B.cut(t, [B.loft(f"ch_wh{k}", w_in, w_in, 0.24, 0.9, K, bevel=0.0)])
    B.loft("ch_wbed", w_in, w_in, 0.23, 0.245, X["wbed"], bevel=0.0, tags=tags)
    # trilhos de aco em cima e embaixo da janela (o cadinho corre neles)
    for k in (-1, 1):
        B.box(f"ch_irail{k}", wx, wy + k * (WIN[1] / 2 - 0.02), WIN[0] - 0.05, 0.028, 0.245, 0.29, KM, bevel=0.004,
              tags=tags)
    # cadinho: base escura, aro octogonal claro com chanfro, sulco escuro por dentro e o banho verde
    # (octogono cheio que pulsa), com o centro mais quente e 3 cascas de escoria girando devagar
    B.plate("cru_base", _octo(wx, wy, CRU_R + 0.012), 0.245, 0.33, K, slope=0.012, tags=tags)
    ring = B.plate("cru_ring", _octo(wx, wy, CRU_R), 0.30, 0.43, A, slope=0.014, bevel=0.005, tags=tags)
    ri = CRU_R - 0.037
    B.cut(ring, [B.loft("cru_in", _octo(wx, wy, ri), _octo(wx, wy, ri), 0.36, 0.6, K, bevel=0.0)])
    B.loft("cru_liner", _octo(wx, wy, ri), _octo(wx, wy, ri), 0.355, 0.385, K, bevel=0.0, tags=tags)
    rm = ri - 0.013
    B.loft("cru_melt", _octo(wx, wy, rm), _octo(wx, wy, rm), 0.385, 0.395, X["melt"], bevel=0.0, tags=tags)
    rh = 0.020 + 0.016 * max(0.0, st["melt"] - 0.7)      # centro quente cresce no pulso
    B.loft("cru_hot", _octo(wx, wy, rh, 0), _octo(wx, wy, rh, 0), 0.395, 0.40, X["melt_hot"], bevel=0.0,
           tags=tags)
    for k in range(3):
        a = math.radians(st["i"] * 22 + 120 * k + 15)
        B.loft(f"cru_slag{k}", _octo(wx + math.cos(a) * 0.052, wy + math.sin(a) * 0.052, 0.013, k * 10),
               _octo(wx + math.cos(a) * 0.052, wy + math.sin(a) * 0.052, 0.010, k * 10), 0.395, 0.403, KM,
               bevel=0.0, tags=tags)
    # pincas de aco dos dois lados: braco do lado da parede, pivo escuro e mordente que abraca o aro
    for k in (-1, 1):
        ap = CRU_R * math.cos(math.radians(22.5))         # face lateral do aro
        B.box(f"cru_tbar{k}", wx + k * (ap + 0.055), wy, 0.09, 0.036, 0.37, 0.41, S, bevel=0.005, tags=tags)
        B.box(f"cru_tjaw{k}", wx + k * (ap + 0.012), wy, 0.026, 0.11, 0.33, 0.445, S, bevel=0.005, tags=tags)
        B.cyl(f"cru_tpiv{k}", wx + k * (ap + 0.075), wy, 0.415, 0.022, 0.02, KM, axis="Z", verts=8, bevel=0.003,
              tags=tags)
        B.box(f"cru_tmount{k}", wx + k * (WIN[0] / 2 - 0.01), wy, 0.03, 0.09, 0.245, 0.40, KM, bevel=0.005,
              tags=tags)
    # reflexos do vidro de chumbo: 2 riscos claros em diagonal no canto de cima a esquerda
    for k, (d, ln) in enumerate(((0.0, 0.11), (0.032, 0.07))):
        gx, gy = wx - 0.170 + d * 0.707, wy + 0.105 - d * 0.707
        B.rbox(f"ch_glint{k}", gx, gy, ln, 0.011, 0.448, 0.452, X["glint"], rot=45, bevel=0.0, tags=tags)
    # labio de aco em degrau em volta da janela, com parafusos
    lip = B.plate("ch_wlip", B.rpoly(wx, wy, WIN[0] + 0.06, WIN[1] + 0.055, 0, chamfer=0.07), 0.42, 0.475, S,
                  slope=0.012, bevel=0.004, tags=tags)
    B.cut(lip, [B.loft("ch_wlc", w_in, w_in, 0.2, 0.6, K, bevel=0.0)])
    B.bolts("ch_wb", [(wx + dx * (WIN[0] / 2 + 0.005), wy + dy * (WIN[1] / 2 + 0.005)) for dx in (-1, 1)
                      for dy in (-1, 1)], 0.475, 0.014, KM, tags=tags)
    # moldura: linha de painel em cima (sem luzes), fendas verticais de 3 pips nos lados e fenda vertical de 2
    # pips na cunha de baixo apontando para o berco
    if fp is not None:
        B.cut(fp, [B.box("ch_tpl", wx, 1.305, 0.36, 0.022, 0.50, 0.9, K, bevel=0.0)])
    for sx in (-1, 1):
        _ledslot(f"ch_side{sx}", sx * 0.322, wy, 0.034, 0.22, 0.46, 3, M, tags, [fa, fp], pip_mat=M["glow_dim"])
        B.bolts(f"ch_fb{sx}", [(sx * 0.335, 1.31), (sx * 0.30, 0.86)], 0.545, 0.016, S, tags=tags)
    _ledslot("ch_tip", 0.0, 0.785, 0.036, 0.09, 0.46, 2, M, tags, [fa, fp])
    # portas de transferencia nos chanfros de baixo (recesso escuro com guias de aco)
    for sx in (-1, 1):
        px, py = sx * 0.372, 0.852                        # ponto do chanfro em frente a garra
        ang = math.degrees(math.atan2(-0.27, 0.42 * sx))  # normal do chanfro (para fora)
        port = _rot([(-0.06, -0.09), (0.13, -0.09), (0.13, 0.09), (-0.06, 0.09)], ang + 180, px, py)
        for k, t in enumerate((wa, wp, fa, fp)):
            B.cut(t, [B.loft(f"ch_port{sx}{k}", port, port, 0.20, 0.9, K, bevel=0.0)])
        B.loft(f"ch_pbed{sx}", port, port, 0.19, 0.20, M["black"], bevel=0.0, tags=tags)
        for j in (-1, 1):
            g = _rot([(-0.02, j * 0.09 - 0.012), (0.13, j * 0.09 - 0.012), (0.13, j * 0.09 + 0.012),
                      (-0.02, j * 0.09 + 0.012)], ang + 180, px, py)
            B.loft(f"ch_pg{sx}{j}", g, g, 0.20, 0.30, S, bevel=0.004, tags=tags)


def _core(name, x, y, z, ang, M, X, tags, s=1.0):
    """Nucleo verde (capsula octogonal brilhante) com colares escuros nas pontas."""
    ln, w = 0.11 * s, 0.05 * s
    p = _rot(B.rpoly(0, 0, ln, w, 0, chamfer=0.016 * s), ang, x, y)
    B.loft(name, p, p, z, z + 0.04, X["core_glow"], bevel=0.0, tags=tags)
    for k, e in enumerate((-1, 1)):
        q = _rot(B.rpoly(e * ln * 0.42, 0, 0.022 * s, w + 0.012, 0), ang, x, y)
        B.loft(f"{name}_cap{k}", q, q, z - 0.005, z + 0.048, M["core_mid"], bevel=0.003, tags=tags)


def _cap(name, x, y0, z, M, X, tags, sc=SC):
    """Ogiva do Projetil Nuclear (na escala sc, com o trevo), apontando para +Y a partir de y0, apoiada em z."""
    NK.ogive(name, x, y0, z + (NK.R - 0.012) * sc, sc, X, M, tags)


# ============================================================================ maquina: manipuladores
def _corner(prefix, sx, M, X, tags):
    """Canto de cima (lado sx): coluna blindada de fora, tampao de parede do ombro e greebles escuros no leito
    por baixo do curso do braco (casco de chumbo a esquerda, estante de ogivas a direita)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    f = _flip(sx)
    S0 = (sx * -SH[0], SH[1])
    # coluna de fora (casca cinza media de bisel duplo sobre base escura: recua para os bracos claros mandarem
    # na leitura), com fenda de 3 pips e parafusos
    col = [(-1.43, 1.31), (-1.31, 1.43), (-1.17, 1.43), (-1.17, 1.06), (-1.23, 1.00), (-1.23, 0.62),
           (-1.31, 0.55), (-1.43, 0.55)]
    B.plate(f"{prefix}_colk", B.offset_poly(f(col), -0.025), 0.0, 0.14, K, slope=0.015, tags=tags)
    ca, cp = B.shard(f"{prefix}_col", f(col), 0.0, 0.36, X["mid"], slope=0.05, groove=0.022, panel_h=0.024,
                     tags=tags)
    Mo.slot_with_pips(f"{prefix}_csl", sx * 1.30, 1.04, 1.30, 0.045, 0.384, 3, M, tags, target=[ca, cp],
                      depth=0.075, pip_mat=M["glow_dim"])
    if cp is not None:
        B.cut(cp, [B.rbox(f"{prefix}_cpl", sx * 1.335, 0.92, 0.10, 0.022, 0.34, 0.8, K, rot=sx * 35, bevel=0.0)])
    B.bolts(f"{prefix}_cb", [(sx * 1.30, 0.66), (sx * 1.24, 1.375)], 0.39, 0.016, S, tags=tags)
    # dutos escuros no leito: do pe da coluna ate a camara (passam por baixo do braco)
    for k, y in enumerate((1.355, 1.30)):
        B.cyl(f"{prefix}_duct{k}", sx * 0.83, y, 0.08, 0.026, 0.62, KM, axis="X", verts=8, bevel=0.004, tags=tags)
    for k, x in enumerate((0.66, 1.0)):
        B.box(f"{prefix}_dclamp{k}", sx * x, 1.327, 0.035, 0.12, 0.05, 0.12, S, bevel=0.005, tags=tags)
    if sx < 0:
        # casco de chumbo deitado (transporte do uranio) em berco escuro, com cintas de aco e LED verde fraco
        cx, cy = -0.80, 1.13
        B.box(f"{prefix}_caskcr", cx, cy, 0.40, 0.17, 0.03, 0.08, KM, bevel=0.008, tags=tags)
        B.cyl(f"{prefix}_cask", cx, cy, 0.15, 0.072, 0.34, X["lead"], axis="X", verts=8, bevel=0.008, tags=tags)
        for k, x in enumerate((-0.12, 0.12)):
            B.cyl(f"{prefix}_caskband{k}", cx + x, cy, 0.15, 0.078, 0.03, S, axis="X", verts=8, bevel=0.004,
                  tags=tags)
        B.box(f"{prefix}_caskled", cx, cy, 0.05, 0.016, 0.21, 0.22, M["glow_dim"], bevel=0.0, tags=tags)
    else:
        # estante de ogivas de reserva (em pe, vistas de cima) numa bandeja escura
        B.plate(f"{prefix}_rack", B.rpoly(0.80, 1.13, 0.46, 0.17, 0, chamfer=0.04), 0.03, 0.10, KM, slope=0.015,
                tags=tags)
        for k in range(3):
            cx = 0.65 + k * 0.15
            B.plate(f"{prefix}_ogb{k}", _octo(cx, 1.13, 0.06), 0.10, 0.17, X["cap"], slope=0.01, tags=tags)
            B.loft(f"{prefix}_ogt{k}", _octo(cx, 1.13, 0.05), _octo(cx, 1.13, 0.012), 0.17, 0.24, X["cap"],
                   bevel=0.0, tags=tags)
    # tampao blindado da parede (torre do ombro): base escura, anel claro de bisel duplo com entalhes
    B.plate(f"{prefix}_sbase", _octo(*S0, 0.25), 0.0, 0.32, K, slope=0.02, tags=tags)
    sa, sp = B.shard(f"{prefix}_sring", _octo(*S0, 0.235), 0.30, 0.40, A, slope=0.04, groove=0.02, panel_h=0.02,
                     tags=tags)
    for k in range(4):
        a = 45 + 90 * k
        cx, cy = S0[0] + math.cos(math.radians(a)) * 0.20, S0[1] + math.sin(math.radians(a)) * 0.20
        for t, nm in ((sa, "a"), (sp, "b")):
            if t is not None:
                B.cut(t, [B.rbox(f"{prefix}_sn{k}{nm}", cx, cy, 0.024, 0.09, 0.36, 0.8, K, rot=a + 90, bevel=0.0)])
    B.plate(f"{prefix}_sdisk", _octo(*S0, 0.13), 0.38, 0.43, KM, slope=0.012, tags=tags)


def _arm(prefix, sx, t, hold, opened, M, X, tags, wait=0.0):
    """Manipulador remoto do lado sx; t = 0 na porta, 1 no estojo; hold = 'core' | 'cap' | None;
    wait = nucleo / ogiva saindo da porta entre os dedos abertos (0..1)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    S0 = (sx * -SH[0], SH[1])
    p0 = (sx * -PORT[0], PORT[1])
    p1 = (CORE_AT if sx < 0 else CAP_AT)
    T = (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
    E, W, fa = _ik(S0, T, -sx)
    ua = math.degrees(math.atan2(E[1] - S0[1], E[0] - S0[0]))
    ur = math.radians(ua)
    # cubo de aco da torre (gira com o braco)
    B.plate(f"{prefix}_shub", _octo(*S0, 0.11, ua + 22.5), 0.42, 0.48, S, slope=0.015, bevel=0.005, tags=tags)
    # braco: viga escura + casca clara de bisel duplo + cilindro hidraulico de aco ao lado
    B.plate(f"{prefix}_ubeam", _link(S0, E, 0.21, 0.16, 0.035, 0.07, 0.07), 0.44, 0.50, KM, slope=0.012, tags=tags)
    ua_, up = B.shard(f"{prefix}_uarm", _link(S0, E, 0.175, 0.135, 0.04, -0.05, -0.085), 0.49, 0.58, A, slope=0.03,
                      groove=0.012, panel_h=0.018, tags=tags)
    nx, ny = -math.sin(ur) * sx, math.cos(ur) * sx
    hx0, hy0 = S0[0] + math.cos(ur) * 0.13 - nx * 0.115, S0[1] + math.sin(ur) * 0.13 - ny * 0.115
    hl = L1 - 0.22
    B.rbox(f"{prefix}_ucyl", hx0 + math.cos(ur) * hl * 0.3, hy0 + math.sin(ur) * hl * 0.3, hl * 0.6, 0.04, 0.44,
           0.50, KM, rot=ua, bevel=0.006, tags=tags)
    B.rbox(f"{prefix}_urod", hx0 + math.cos(ur) * hl * 0.75, hy0 + math.sin(ur) * hl * 0.75, hl * 0.5, 0.018, 0.455,
           0.485, S, rot=ua, bevel=0.003, tags=tags)
    # fenda com 2 pips verdes no braco (vazada no painel e na casca)
    mx, my = S0[0] + math.cos(ur) * L1 * 0.45, S0[1] + math.sin(ur) * L1 * 0.45
    _ledslot(f"{prefix}_usl", mx, my, 0.15, 0.036, 0.50, 2, M, tags, [ua_, up], vertical=False,
             pip_mat=M["glow_dim"], rot=ua)
    # pino do ombro por cima do braco
    B.plate(f"{prefix}_spin", _octo(*S0, 0.065, ua), 0.58, 0.62, S, slope=0.012, bevel=0.004, tags=tags)
    B.plate(f"{prefix}_spinc", _octo(*S0, 0.032, ua), 0.62, 0.635, KM, slope=0.006, bevel=0.002, tags=tags)
    # cotovelo de aco com tampa escura e LED
    B.plate(f"{prefix}_elb", _octo(*E, 0.088, ua), 0.42, 0.61, S, slope=0.016, bevel=0.005, tags=tags)
    B.plate(f"{prefix}_elbc", _octo(*E, 0.048, ua), 0.61, 0.63, KM, slope=0.008, bevel=0.003, tags=tags)
    B.cyl(f"{prefix}_elbled", E[0], E[1], 0.633, 0.016, 0.006, M["glow_dim"], axis="Z", verts=8, bevel=0.0,
          tags=tags)
    # antebraco (mais baixo que o braco): viga escura + casca clara, 2 tubos hidraulicos de aco
    fad = math.degrees(fa)
    ux, uy = math.cos(fa), math.sin(fa)
    nx, ny = -uy, ux
    B.plate(f"{prefix}_fbeam", _link(E, W, 0.15, 0.11, 0.03, 0.0, 0.035), 0.36, 0.42, KM, slope=0.01, tags=tags)
    fa_, fp_ = B.shard(f"{prefix}_farm", _link(E, W, 0.125, 0.09, 0.03, -0.10, -0.045), 0.41, 0.49, A,
                       slope=0.024, groove=0.012, panel_h=0.014, tags=tags)
    if fp_ is not None:
        mxx, myy = E[0] + ux * L2 * 0.62, E[1] + uy * L2 * 0.62
        B.cut(fp_, [B.rbox(f"{prefix}_fpl", mxx, myy, 0.022, 0.12, 0.47, 0.8, K, rot=fad, bevel=0.0)])
    for k in (-1, 1):
        mxx, myy = (E[0] + W[0]) / 2 + nx * k * 0.072, (E[1] + W[1]) / 2 + ny * k * 0.072
        B.rbox(f"{prefix}_fhyd{k}", mxx, myy, L2 * 0.66, 0.018, 0.39, 0.42, S, rot=fad, bevel=0.003, tags=tags)
    # punho e garra de 2 dedos (abre ao soltar)
    B.plate(f"{prefix}_wrist", _octo(*W, 0.058, fad), 0.33, 0.47, S, slope=0.014, bevel=0.004, tags=tags)
    B.plate(f"{prefix}_wristc", _octo(*W, 0.03, fad), 0.47, 0.485, KM, slope=0.006, bevel=0.002, tags=tags)
    B.rbox(f"{prefix}_palm", W[0] + ux * 0.045, W[1] + uy * 0.045, 0.04, 0.15, 0.33, 0.42, KM, rot=fad, bevel=0.005,
           tags=tags)
    g = 0.066 if opened else (0.050 if (hold or wait) else 0.036)
    for k in (-1, 1):
        # dedo de aco (mais largo) com ponta de blindagem clara dobrada para dentro: le como garra a 1x
        bx, by = W[0] + ux * 0.088 + nx * k * g, W[1] + uy * 0.088 + ny * k * g
        B.rbox(f"{prefix}_fing{k}", bx, by, 0.115, 0.038, 0.33, 0.41, S, rot=fad, bevel=0.006, tags=tags)
        tx_, ty_ = W[0] + ux * 0.158 + nx * k * (g - 0.016), W[1] + uy * 0.158 + ny * k * (g - 0.016)
        B.rbox(f"{prefix}_tip{k}", tx_, ty_, 0.06, 0.032, 0.33, 0.415, A, rot=fad - k * 32, bevel=0.005, tags=tags)
    item = hold or (("core" if sx < 0 else "cap") if wait > 0 else None)
    if item == "core":
        _core(f"{prefix}_core", W[0] + ux * 0.10, W[1] + uy * 0.10, 0.345, fad + 90, M, X, tags,
              s=1.0 if hold else wait)
    elif item == "cap":
        _cap(f"{prefix}_cap", W[0] + ux * 0.10, W[1] + uy * 0.10 - 0.08, 0.25, M, X, tags)


# ============================================================================ maquina: berco de montagem
def _half(prefix, sx, ox, oy, M, X, tags, lit=True):
    """Metade sx do estojo (sx = -1 esquerda): anel de base, colar claro com LED, corpo escuro com meia janela
    vazada e faixa verde (apagada ate o nucleo entrar: lit), colar do pescoco. ox/oy = deslocamento da metade."""
    K, A, S = M["core"], M["armor"], M["steel"]

    def Y(y):
        return y * SC + SY + oy

    def poly(x0, x1, y0, y1, c=0.0):
        if c > 0:
            pts = [(x0, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0, y1)]
        else:
            pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        pts = [(ox + sx * x, y) for x, y in pts]
        return pts if sx > 0 else list(reversed(pts))
    hw = NK.R * math.cos(math.radians(22.5)) * SC        # meia largura do corpo
    top = SZ + 2 * NK.R * SC * 0.93
    B.plate(f"{prefix}_ring", poly(0.004, (NK.R + 0.018) * SC * 0.97, Y(NK.Y_BASE0), Y(NK.Y_BASE1), 0.012),
            SZ, top - 0.01, X["ring"], slope=0.022, bevel=0.004, tags=tags)
    ca, cp = B.shard(f"{prefix}_col", poly(0.004, (NK.R + 0.02) * SC, Y(NK.Y_COL0), Y(NK.Y_COL1), 0.03), SZ,
                     top + 0.012, A, slope=0.022, groove=0.01, panel_h=0.014, tags=tags)
    # LED do contador (um por metade) numa fenda escura vazada no colar
    cyc = Y((NK.Y_COL0 + NK.Y_COL1) / 2)
    _ledslot(f"{prefix}_csl", ox + sx * 0.055, cyc, 0.05, 0.034, top - 0.03, 1, M, tags, [ca, cp], vertical=False,
             pip_mat=M["glow_dim"])
    body = B.plate(f"{prefix}_body", poly(0.004, hw, Y(NK.Y_COL1) - 0.004, Y(NK.Y_NECK0) + 0.004), SZ, top,
                   X["body"], slope=0.03, bevel=0.005, tags=tags)
    # meia janela vazada na borda interna (o nucleo aparece pela janela quando fecha)
    wy0, wy1 = Y(NK.WIN_Y[0]), Y(NK.WIN_Y[1])
    B.cut(body, [B.box(f"{prefix}_win", ox, (wy0 + wy1) / 2, 0.064, wy1 - wy0, SZ - 0.02, top + 0.3, K,
                       bevel=0.0)])
    # faixas verdes em sulcos escuros (as mesmas do Projetil Nuclear)
    for k, (yb, bw) in enumerate(NK.BANDS):
        by = Y(yb)
        B.box(f"{prefix}_bandk{k}", ox + sx * (hw / 2 + 0.002), by, hw - 0.004, (2 * bw + 0.03) * SC, top - 0.004,
              top + 0.004, M["black"], bevel=0.0, tags=tags)
        B.box(f"{prefix}_band{k}", ox + sx * (hw / 2 + 0.004), by, hw - 0.008, 2 * bw * SC, top + 0.004,
              top + 0.009, X["band"] if lit else X["band_off"], bevel=0.0, tags=tags)
    B.shard(f"{prefix}_neck", poly(0.004, (NK.R + 0.01) * SC, Y(NK.Y_NECK0), Y(NK.Y_NECK1), 0.02), SZ,
            top + 0.008, A, slope=0.018, groove=0.008, panel_h=0.01, tags=tags)


def _ycore(oy):
    """y do nucleo dentro do estojo (centro da janela)."""
    return (NK.WIN_Y[0] + NK.WIN_Y[1]) / 2 * SC + SY + oy


def _cradle(M, X, tags, st):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    # bloco de maquina do tile central e calha escura com trilhos de aco
    B.plate("cr_block", B.rpoly(0, 0, 0.94, 0.94, 0, chamfer=0.16), 0.0, 0.04, K, slope=0.015, tags=tags)
    B.plate("cr_trough", B.rpoly(0, -0.02, 0.38, 0.90, 0, chamfer=0.05), 0.03, 0.06, KM, slope=0.012, tags=tags)
    B.box("cr_well", 0, -0.02, 0.29, 0.84, 0.055, 0.064, M["black"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"cr_rail{sx}", sx * 0.165, -0.02, 0.022, 0.86, 0.04, 0.09, S, bevel=0.004, tags=tags)
    # selas de aco sob a base e sob a ogiva
    for k, y in enumerate((-0.25, 0.33)):
        B.box(f"cr_saddle{k}", 0, y, 0.31, 0.05, 0.05, 0.075, S, bevel=0.006, tags=tags)
    if st["ready"]:
        # LED de pronto no fundo da calha (entre as metades novas que chegam pelos lados)
        B.box("cr_ready", 0, 0.05, 0.03, 0.18, 0.064, 0.07, M["glow_dim"], bevel=0.0, tags=tags)

    # estojo (2 metades) + nucleo + ogiva
    oy = -st["slide"]
    if st["core_in"]:
        _core("sh_core", 0.0, _ycore(oy), SZ + 0.06, 90, M, X, tags)
    gap = 0.044 * st["gap"]
    for sx in (-1, 1):
        _half(f"sh{sx}", sx, sx * gap, oy, M, X, tags, lit=st["lit"])
    if st["cap_on"]:
        _cap("sh_cap", 0.0, NK.Y_NECK1 * SC + SY + oy - 0.004, SZ, M, X, tags)
    if st["flash"] > 0:
        # lampejo verde pelas costuras: linha fina no meio e nas juntas dos colares
        f = st["flash"]
        y0, y1 = (NK.Y_BASE1 * SC + SY + oy, NK.Y_NECK1 * SC + SY + oy)
        B.box("fx_seam", 0, (y0 + y1) / 2, 0.010 + 0.006 * f, y1 - y0, SZ + 0.05, SZ + 0.262, X["flash"],
              bevel=0.0, tags=tags)
        for k, yy in enumerate((NK.Y_COL1, NK.Y_NECK0)):
            B.box(f"fx_joint{k}", 0, yy * SC + SY + oy, 0.17, 0.007 + 0.004 * f, SZ + 0.23, SZ + 0.262,
                  X["flash"], bevel=0.0, tags=tags)
    if st["slide"] > 0:
        # o que desce alem do capuz fica escondido (holdout transparente); comeca em y -0.50 (abaixo da borda
        # de baixo do capuz e do bloco, y -0.47), senao recorta essa borda nos quadros da descida
        B.box("out_hold", 0, -0.66, 0.40, 0.32, -0.1, 1.2, _holdout(), bevel=0.0, tags=tags)

    # mordentes do grampo: bloco escuro + casca clara pesada (bisel duplo), correndo em trilhos de aco
    xin = 0.150 + (1.0 - st["clamp"]) * 0.11
    for sx in (-1, 1):
        f = _flip(sx)
        for k, y in enumerate((0.255, -0.305)):
            B.box(f"cl_rail{sx}{k}", sx * 0.33, y, 0.28, 0.03, 0.04, 0.12, S, bevel=0.005, tags=tags)
            B.box(f"cl_stop{sx}{k}", sx * 0.455, y, 0.035, 0.065, 0.04, 0.17, KM, bevel=0.006, tags=tags)
        jk = [(-xin, -0.225), (-xin - 0.045, -0.275), (-xin - 0.205, -0.275), (-xin - 0.205, 0.225),
              (-xin - 0.045, 0.225), (-xin, 0.18)]
        B.plate(f"cl_jk{sx}", f(jk), 0.0, 0.25, KM, slope=0.02, tags=tags)
        jaw = [(-xin - 0.03, -0.20), (-xin - 0.07, -0.25), (-xin - 0.17, -0.25), (-xin - 0.195, -0.225),
               (-xin - 0.195, 0.175), (-xin - 0.17, 0.20), (-xin - 0.07, 0.20), (-xin - 0.03, 0.16)]
        ja, jp = B.shard(f"cl_jaw{sx}", f(jaw), 0.22, 0.36, A, slope=0.04, groove=0.018, panel_h=0.022, tags=tags)
        # face interna: dentes escuros de aco que prendem as metades
        B.box(f"cl_face{sx}", sx * (xin + 0.014), -0.025, 0.028, 0.34, 0.06, 0.29, K, bevel=0.004, tags=tags)
        for k in range(3):
            B.box(f"cl_tooth{sx}{k}", sx * (xin + 0.004), -0.14 + k * 0.115, 0.012, 0.05, 0.08, 0.27, S, bevel=0.002,
                  tags=tags)
        jx = sx * (xin + 0.118)
        _ledslot(f"cl_sl{sx}", jx, -0.04, 0.045, 0.24, 0.30, 3, M, tags, [ja, jp],
                 pip_mat=M["glow"] if st["clamp"] >= 1.0 else M["glow_dim"])
        if jp is not None:
            B.cut(jp, [B.rbox(f"cl_pl{sx}", sx * (xin + 0.07), 0.15, 0.022, 0.08, 0.34, 0.8, K, rot=sx * 40,
                              bevel=0.0)])
        B.bolts(f"cl_b{sx}", [(jx, 0.155), (jx, -0.215)], 0.385, 0.016, S, tags=tags)

    # capuz de saida (sobre a ponta de baixo da calha): o projetil pronto desce por baixo dele
    hood = [(-0.22, -0.30), (0.22, -0.30), (0.26, -0.34), (0.26, -0.47), (-0.26, -0.47), (-0.26, -0.34)]
    B.plate("cr_hoodk", B.offset_poly(hood, -0.02), 0.20, 0.32, KM, slope=0.015, tags=tags)
    ha, hp = B.shard("cr_hood", hood, 0.30, 0.44, A, slope=0.045, groove=0.02, panel_h=0.02, tags=tags)
    _ledslot("cr_hsl", 0.0, -0.395, 0.22, 0.045, 0.40, 3, M, tags, [ha, hp], vertical=False,
             pip_mat=M["glow"] if st["slide"] > 0 else M["glow_dim"])
    B.bolts("cr_hb", [(-0.20, -0.44), (0.20, -0.44)], 0.465, 0.015, S, tags=tags)


def machine(M, T="machine", phase=0.0):
    """Maquinario (fileira de cima + tile central); transparente nos tiles de entrada e saida."""
    tags = (T,)
    st = _state(phase)
    X = _extra(st)
    _chamber(M, X, tags, st)
    _cradle(M, X, tags, st)
    for sx in (-1, 1):
        _corner("k" + ("L" if sx < 0 else "R"), sx, M, X, tags)
    _arm("aL", -1, st["L"], "core" if st["Lhold"] else None, st["Lopen"], M, X, tags, wait=st["port_core"])
    _arm("aR", 1, st["R"], "cap" if st["Rhold"] else None, st["Ropen"], M, X, tags,
         wait=1.0 if st["port_cap"] else 0.0)


# ============================================================================ teto
def _inlay(name, poly, targets, z1, green, tags, gap=0.03):
    """Placa em seta embutida: abre um furo (contorno + vao) nas placas de base e assenta a seta no fundo escuro."""
    hole = B.offset_poly(poly, -gap)
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.loft(f"{name}_h{k}", hole, hole, -0.01, 0.5, green, bevel=0.0)])
    return B.shard(name, poly, 0.0, z1, green, slope=0.05, groove=0.03, panel_h=0.018, tags=tags)


# placas verdes dos cantos de cima (lado esquerdo): seguem os chanfros da tampa da celula com vao escuro
RF_SIDE = [(-1.45, 1.33), (-1.33, 1.45), (-0.56, 1.45), (-0.56, 1.04), (-0.29, 0.585), (-1.33, 0.585),
           (-1.45, 0.705)]
# guarda de canto em L (2o degrau de blindagem clara sem pintura, sobre saia escura) em volta do ombro do
# manipulador: braco de cima com a ponta em cunha apontando para a tampa, braco de fora com ponta chanfrada
RF_GUARD = [(-1.38, 1.30), (-1.30, 1.38), (-0.64, 1.38), (-0.58, 1.33), (-0.76, 1.19), (-1.16, 1.19), (-1.16, 1.07),
            (-1.26, 1.00), (-1.38, 1.04)]
# lamina clara (sem pintura) em cunha de bisel duplo na base do canto, apontando para o berco
RF_BLADE = [(-1.40, 0.92), (-1.40, 0.77), (-1.20, 0.645), (-0.56, 0.645), (-0.72, 0.85), (-1.22, 0.85)]
# tampa da celula quente (sem pintura): cunha da camara (1o degrau) e bloco do visor (2o degrau)
LID = [(-0.46, 1.45), (0.46, 1.45), (0.50, 1.41), (0.50, 1.04), (0.22, 0.585), (-0.22, 0.585), (-0.50, 1.04),
       (-0.50, 1.41)]
LID2 = [(-0.25, 1.385), (0.25, 1.385), (0.29, 1.345), (0.29, 1.02), (0.11, 0.74), (-0.11, 0.74), (-0.29, 1.02),
        (-0.29, 1.345)]
# cinta blindada da fileira de baixo (porta de cofre): segmentos por tile, com vao no meio onde a seta da saida
# aponta para a trava central
STRAP_Y, STRAP_H = -1.30, 0.13
STRAP_SEGS = [(-1.08, -0.60), (-0.40, -0.11), (0.11, 0.40), (0.60, 1.08)]


def _vchev(name, cx, cy, ang, targets, z1, green, M, tags, s=1.0):
    """Chevron duplo em V (2o degrau verde embutido) apontando para ang."""
    v = [(0.20, 0.0), (-0.06, 0.26), (-0.20, 0.26), (0.05, 0.0), (-0.20, -0.26), (-0.06, -0.26)]
    out = []
    for k, dx in enumerate((-0.08, 0.13)):
        poly = _rot([((x + dx) * s, y * s) for x, y in v], ang, cx, cy)
        out.append(_inlay(f"{name}{k}", poly, targets, z1, green, tags, gap=0.025))
    return out


def roof(M, T="roof"):
    """Teto verde (pintura da nave) em blindagem extra pesada, tampa da celula quente sem pintura, ombreiras e
    laminas claras dos manipuladores, o trevo de 3 laminas sobre o berco e a cinta de cofre sobre a saida.
    Todas as luzes do teto usam o LED lima (_roof_led): o verde puro seria trocado pela pintura no jogo."""
    tags = (T,)
    green = B.mat_roof_green()
    LED = _roof_led()
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    X = _extra()
    B.box("rf_under", 0, 0, 3, 3, -0.05, 0.02, K, bevel=0.0, tags=tags)

    # ---- cantos de cima: placa verde + guarda clara em L (2o degrau) + lamina clara em cunha
    for sx in (-1, 1):
        f = _flip(sx)
        B.shard(f"rf_ts{sx}", f(RF_SIDE), 0.0, 0.08, green, slope=0.03, groove=0.05, panel_h=0.024,
                         tags=tags)
        # guarda em L: saia escura + casca clara de bisel duplo, linhas de painel (sem luzes: as luzes do canto
        # ficam so na lamina) e parafusos pesados na quina e na ponta
        B.plate(f"rf_gk{sx}", B.offset_poly(f(RF_GUARD), -0.03), 0.06, 0.15, K, slope=0.012, tags=tags)
        ga, gp = B.shard(f"rf_g{sx}", f(RF_GUARD), 0.12, 0.25, A, slope=0.045, groove=0.02, panel_h=0.022,
                         tags=tags)
        if gp is not None:
            B.cut(gp, [B.rbox(f"rf_gpl{sx}", sx * 1.27, 1.16, 0.12, 0.022, 0.2, 0.6, K, bevel=0.0),
                       B.rbox(f"rf_gpm{sx}", sx * 1.02, 1.285, 0.022, 0.12, 0.2, 0.6, K, bevel=0.0)])
        B.bolts(f"rf_gb{sx}", [(sx * 1.285, 1.285), (sx * 0.80, 1.285)], 0.272, 0.019, S, tags=tags)
        # no verde dentro do L: grade de respiro escura curta (sem pintura) com 2 parafusos
        vx, vy = sx * 0.90, 1.03
        rv = B.rbox(f"rf_gv{sx}", vx, vy, 0.26, 0.15, 0.07, 0.115, KM, bevel=0.006, tags=tags)
        B.cut(rv, [B.box(f"rf_gvc{sx}{k}", vx, vy - 0.04 + k * 0.04, 0.20, 0.018, 0.095, 0.3, K, bevel=0.0)
                   for k in range(3)])
        # lamina clara em cunha (bisel duplo) com base escura e fenda de 3 LEDs, apontando para o berco
        bl = f(RF_BLADE)
        B.plate(f"rf_blk{sx}", B.offset_poly(bl, -0.03), 0.06, 0.12, K, slope=0.012, tags=tags)
        ba, bp = B.shard(f"rf_bl{sx}", bl, 0.10, 0.21, A, slope=0.04, groove=0.02, panel_h=0.02, tags=tags)
        _ledslot(f"rf_bsl{sx}", sx * 0.94, 0.745, 0.32, 0.042, 0.12, 3, M, tags, [ba, bp], vertical=False,
                 pip_mat=LED, pw=0.022)
        if bp is not None:
            B.cut(bp, [B.rbox(f"rf_bpl{sx}", sx * 0.70, 0.735, 0.022, 0.12, 0.18, 0.6, K, rot=sx * 35, bevel=0.0)])
        B.bolts(f"rf_tb{sx}", [(sx * 0.63, 0.95)], 0.10, 0.015, S, tags=tags)

    # ---- tampa da celula quente (sem pintura): cunha pesada cinza (1o degrau, forro de chumbo) com fendas de
    # LEDs nos lados, bloco claro do visor (2o degrau) sobre plinto escuro, visor escuro com linha de luz e
    # reflexo, e parafusos pesados
    B.plate("lid_k", B.offset_poly(LID, -0.02), 0.02, 0.10, K, slope=0.015, tags=tags)
    la, lp = B.shard("lid", LID, 0.03, 0.17, X["mid"], slope=0.06, groove=0.03, panel_h=0.025, tags=tags)
    B.plate("lid2_k", B.offset_poly(LID2, -0.045), 0.17, 0.215, K, slope=0.008, tags=tags)
    l2a, l2p = B.shard("lid2", LID2, 0.19, 0.30, A, slope=0.04, groove=0.018, panel_h=0.022, tags=tags)
    for sx in (-1, 1):
        _ledslot(f"lid_sl{sx}", sx * 0.395, 1.20, 0.045, 0.24, 0.17, 3, M, tags, [la, lp], pip_mat=LED)
        B.bolts(f"lid_b{sx}", [(sx * 0.40, 1.385), (sx * 0.40, 1.0)], 0.195, 0.018, S, tags=tags)
        if lp is not None:
            B.cut(lp, [B.rbox(f"lid_pl{sx}", sx * 0.27, 0.80, 0.022, 0.14, 0.15, 0.6, K, rot=sx * 33, bevel=0.0)])
    # visor: fenda horizontal escura (vidro de chumbo neutro, sem verde: o verde seria pintado) com a linha de
    # luz lima do banho la embaixo e um reflexo claro na ponta
    vis = B.rpoly(0, 1.12, 0.36, 0.085, 0, chamfer=0.03)
    for k, t in enumerate((l2a, l2p)):
        B.cut(t, [B.loft(f"lid_vc{k}", vis, vis, 0.21, 0.7, K, bevel=0.0)])
    B.loft("lid_vbed", vis, vis, 0.20, 0.21, M["black"], bevel=0.0, tags=tags)
    B.box("lid_vglow", 0, 1.12, 0.20, 0.018, 0.21, 0.216, LED, bevel=0.0, tags=tags)
    B.rbox("lid_vglint", -0.135, 1.12, 0.05, 0.010, 0.25, 0.254, X["glint"], rot=60, bevel=0.0, tags=tags)
    _ledslot("lid_vent", 0.0, 1.29, 0.30, 0.045, 0.24, 4, M, tags, [l2a, l2p], vertical=False, pip_mat=LED)
    _ledslot("lid_tip", 0.0, 0.875, 0.10, 0.04, 0.24, 2, M, tags, [l2a, l2p], vertical=False, pip_mat=LED)
    if l2p is not None:
        B.cut(l2p, [B.box("lid2_pl", 0, 0.98, 0.30, 0.022, 0.28, 0.6, K, bevel=0.0)])

    # ---- tile central: trevo de 3 laminas claras sobre base escura, cubo de aco e LEDs entre as laminas
    B.plate("tf_base", _octo(0, 0, 0.47), 0.02, 0.10, K, slope=0.02, tags=tags)
    B.plate("tf_ring", _octo(0, 0, 0.44), 0.09, 0.115, KM, slope=0.01, tags=tags)
    blade = [(0.135, -0.075), (0.37, -0.20), (0.42, -0.15), (0.42, 0.15), (0.37, 0.20), (0.135, 0.075)]
    for k in range(3):
        a = 90 + 120 * k
        bk = _rot(B.offset_poly(blade, -0.02), a)
        B.plate(f"tf_bk{k}", bk, 0.10, 0.13, K, slope=0.01, tags=tags)
        ba, bp = B.shard(f"tf_bl{k}", _rot(blade, a), 0.11, 0.25, A, slope=0.045, groove=0.02, panel_h=0.022,
                         tags=tags)
        # linha de painel transversal na lamina
        if bp is not None:
            cx, cy = _rot([(0.33, 0.0)], a)[0]
            B.cut(bp, [B.rbox(f"tf_pl{k}", cx, cy, 0.022, 0.22, 0.23, 0.6, K, rot=a, bevel=0.0)])
        # LEDs no vao entre as laminas (fenda radial)
        pa_ = a + 60
        cx, cy = math.cos(math.radians(pa_)) * 0.33, math.sin(math.radians(pa_)) * 0.33
        B.rbox(f"tf_slot{k}", cx, cy, 0.13, 0.036, 0.115, 0.125, M["black"], rot=pa_, bevel=0.0, tags=tags)
        for j in range(2):
            px, py = (math.cos(math.radians(pa_)) * (0.29 + j * 0.075),
                      math.sin(math.radians(pa_)) * (0.29 + j * 0.075))
            B.rbox(f"tf_pip{k}{j}", px, py, 0.034, 0.02, 0.125, 0.133, LED, rot=pa_, bevel=0.0, tags=tags)
    B.plate("tf_hubk", _octo(0, 0, 0.13), 0.10, 0.20, K, slope=0.012, tags=tags)
    B.plate("tf_hub", _octo(0, 0, 0.105), 0.19, 0.27, S, slope=0.02, bevel=0.005, tags=tags)
    B.plate("tf_hubc", _octo(0, 0, 0.055, 0), 0.27, 0.285, KM, slope=0.008, tags=tags)
    B.cyl("tf_led", 0, 0, 0.287, 0.022, 0.006, LED, axis="Z", verts=8, bevel=0.0, tags=tags)
    B.bolts("tf_hb", _octo(0, 0, 0.08, 0), 0.27, 0.011, KM, tags=tags)

    # ---- meio: placas laterais (sobre as entradas) com chevron duplo em V embutido apontando para o berco e
    # cinta de aco chanfrada na borda de fora
    for sx in (-1, 1):
        ma, mp = B.shard(f"rf_mid{sx}", B.rpoly(sx * 1.0, 0.0, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.08, green,
                         slope=0.03, groove=0.05, panel_h=0.024, tags=tags)
        _vchev(f"rf_mv{sx}", sx * 0.98, 0.0, 0 if sx < 0 else 180, (ma, mp), 0.15, green, M, tags, s=0.95)
        _ledslot(f"rf_mp{sx}", sx * 0.72, 0.0, 0.05, 0.14, 0.02, 2, M, tags, [ma, mp], pw=0.026, pip_mat=LED)
        B.box(f"rf_strapk{sx}", sx * 1.36, 0.0, 0.10, 0.86, 0.02, 0.10, K, bevel=0.0, tags=tags)
        B.plate(f"rf_strap{sx}", B.rpoly(sx * 1.36, 0.0, 0.08, 0.84, 0, chamfer=0.03), 0.09, 0.14, S, slope=0.016,
                bevel=0.005, tags=tags)
        B.bolts(f"rf_stb{sx}", [(sx * 1.36, y) for y in (-0.33, -0.11, 0.11, 0.33)], 0.14, 0.014, KM, tags=tags)
        B.bolts(f"rf_mb{sx}", [(sx * 0.63, dy) for dy in (-0.37, 0.37)], 0.10, 0.016, S, tags=tags)

    # ---- fileira de baixo (saida): placas pesadas; a do meio com chevron duplo para baixo e 3 LEDs, as dos
    # cantos com lamina clara em cunha; cinta de cofre em segmentos claros de bisel duplo, dobradicas claras nas
    # pontas e trava de aco no meio (a seta aponta para ela)
    bots = []
    for k, cx in enumerate((-1.0, 0.0, 1.0)):
        bots.append(B.shard(f"rf_bot{k}", B.rpoly(cx, -1.0, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.08, green,
                            slope=0.03, groove=0.05, panel_h=0.024, tags=tags))
    ba, bp = bots[1]
    _vchev("rf_bv", 0.0, -0.905, 270, (ba, bp), 0.15, green, M, tags, s=0.95)
    _ledslot("rf_bpips", 0.0, -0.665, 0.22, 0.05, 0.02, 3, M, tags, [ba, bp], vertical=False, pw=0.026,
             pip_mat=LED)
    for k in (0, 2):
        cx = -1.0 if k == 0 else 1.0
        sx = -1 if cx < 0 else 1
        a_, p_ = bots[k]
        f = _flip(sx)
        # lamina clara em cunha espelhada (aponta para cima, para o berco): as 4 laminas dos cantos emolduram o
        # trevo; base escura, fenda de 3 LEDs e linha de painel na ponta
        bl = [(x, -y) for x, y in reversed(f(RF_BLADE))]
        B.plate(f"rf_bbk{k}", B.offset_poly(bl, -0.03), 0.06, 0.12, K, slope=0.012, tags=tags)
        la_, lp_ = B.shard(f"rf_bbl{k}", bl, 0.10, 0.21, A, slope=0.04, groove=0.02, panel_h=0.02, tags=tags)
        _ledslot(f"rf_bsl{k}", sx * 0.94, -0.745, 0.32, 0.042, 0.12, 3, M, tags, [la_, lp_], vertical=False,
                 pip_mat=LED, pw=0.022)
        if lp_ is not None:
            B.cut(lp_, [B.rbox(f"rf_bbp{k}", sx * 0.70, -0.735, 0.022, 0.12, 0.18, 0.6, K, rot=sx * -35,
                               bevel=0.0)])
        # faixa verde entre a lamina e a cinta: linha de painel e parafusos
        if p_ is not None:
            B.cut(p_, [B.rbox(f"rf_bgl{k}", cx - sx * 0.02, -1.06, 0.56, 0.022, 0.04, 0.3, K, bevel=0.0)])
        B.bolts(f"rf_bb{k}", [(cx + sx * 0.37, -0.62), (cx - sx * 0.37, -1.12)], 0.10, 0.016, S, tags=tags)
        # dobradica clara na ponta da cinta: bloco de bisel duplo sobre saia escura, com nervura escura (junta da
        # dobradica) e 2 parafusos
        hz = f([(-1.43, STRAP_Y - 0.11), (-1.15, STRAP_Y - 0.11), (-1.08, STRAP_Y - 0.04), (-1.08, STRAP_Y + 0.04),
                (-1.15, STRAP_Y + 0.11), (-1.43, STRAP_Y + 0.11)])
        B.plate(f"rf_hgk{k}", B.offset_poly(hz, -0.025), 0.02, 0.12, K, slope=0.01, tags=tags)
        ha_, hp_ = B.shard(f"rf_hg{k}", hz, 0.10, 0.22, A, slope=0.04, groove=0.018, panel_h=0.02, tags=tags)
        for t, nm in ((ha_, "a"), (hp_, "b")):
            if t is not None:
                B.cut(t, [B.box(f"rf_hgc{k}{nm}", cx + sx * 0.22, STRAP_Y, 0.03, 0.30, 0.16, 0.6, K, bevel=0.0)])
        B.box(f"rf_hgbed{k}", cx + sx * 0.22, STRAP_Y, 0.03, 0.22, 0.10, 0.165, K, bevel=0.0, tags=tags)
        B.bolts(f"rf_hgb{k}", [(cx + sx * 0.33, STRAP_Y + 0.05), (cx + sx * 0.33, STRAP_Y - 0.05)], 0.24, 0.016, S,
                tags=tags)
    # cinta: saia escura continua + segmentos claros de bisel duplo, travas escuras nas juntas dos tiles
    B.box("rf_bandk", 0, STRAP_Y, 2.30, STRAP_H + 0.03, 0.02, 0.10, K, bevel=0.0, tags=tags)
    for k, (x0, x1) in enumerate(STRAP_SEGS):
        B.shard(f"rf_band{k}", B.rpoly((x0 + x1) / 2, STRAP_Y, x1 - x0, STRAP_H, 0, chamfer=0.035), 0.08, 0.16, A,
                slope=0.025, groove=0.012, panel_h=0.015, tags=tags)
    for k, x in enumerate((-0.5, 0.5)):
        B.box(f"rf_lock{k}", x, STRAP_Y, 0.11, 0.20, 0.08, 0.19, KM, bevel=0.012, tags=tags)
        B.box(f"rf_lockb{k}", x, STRAP_Y, 0.04, 0.12, 0.185, 0.193, M["black"], bevel=0.0, tags=tags)
    # trava central: losango de aco num poco escuro, no vao da cinta (a seta da saida aponta para ela), com
    # fenda de LED
    B.plate("rf_ctk", B.rpoly(0, STRAP_Y, 0.17, 0.17, 45), 0.02, 0.14, K, slope=0.012, tags=tags)
    ct = B.plate("rf_ct", B.rpoly(0, STRAP_Y, 0.135, 0.135, 45), 0.12, 0.21, S, slope=0.02, bevel=0.005,
                 tags=tags)
    B.cut(ct, [B.box("rf_ctc", 0, STRAP_Y, 0.024, 0.075, 0.17, 0.6, K, bevel=0.0)])
    B.box("rf_ctbed", 0, STRAP_Y, 0.024, 0.075, 0.165, 0.175, M["black"], bevel=0.0, tags=tags)
    B.box("rf_ctl", 0, STRAP_Y, 0.012, 0.05, 0.175, 0.181, LED, bevel=0.0, tags=tags)
    B.bolts("rf_bandb", [(x, STRAP_Y) for x in (-0.84, -0.255, 0.255, 0.84)], 0.175, 0.015, KM, tags=tags)

    # o verde do conves nao reflete nem rebate luz nas pecas sem pintura (senao a pintura vaza nas bordas claras)
    for o in B.bpy.context.scene.objects:
        if o.type == "MESH" and o.get(T) and any(m is green for m in o.data.materials):
            o.visible_glossy = False
            o.visible_diffuse = False
