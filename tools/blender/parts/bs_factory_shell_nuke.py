"""Fundicao de Projeteis Nucleares (Nuclear Shell Foundry) 3x3 - celula quente blindada que monta o Projetil
Nuclear: uranio enriquecido + 2 Carregadores Padrao -> 1 Projetil Nuclear (800 de bateria por ciclo, fim de jogo).

Layout vanilla factory_he (tools/bsgen/factory.py): fileira de cima + tile central = maquinario (bloqueado);
entradas no meio das laterais: tile (0,1) esquerda = uranio enriquecido, tile (2,1) direita = Carregadores
Padrao; saida = fileira de baixo inteira. O jogo desenha as pilhas nesses 5 tiles, entao eles ficam livres de
maquinario e o piso mostra bases escuras marcadas (cantoneiras, labio fino, setas verdes em recesso).
Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade = 1 tile.

Maquina (mesma familia das armas: cascas claras chanfradas com bisel duplo sobre nucleo escuro, luz verde
so em recessos escuros):
  * camara de fundicao blindada no tile de cima do meio: paredes grossas em 2 degraus de blindagem, visor de
    vidro de chumbo escuro (esverdeado, com reflexo) sobre o cadinho de aco com o banho verde pulsando;
    portas de transferencia nos dois chanfros de baixo (esquerda: nucleo verde; direita: ogiva);
  * dois manipuladores remotos articulados nos cantos de cima (torre de ombro, braco e antebraco de
    blindagem clara sobre viga escura, cotovelo de aco, garra de 2 dedos): o da esquerda leva o nucleo
    verde da porta ate o estojo aberto, o da direita leva a ogiva ate a ponta do projetil;
  * berco de montagem blindado no tile central: calha escura com o estojo partido em 2 metades (as mesmas
    medidas do Projetil Nuclear, parts/bs_shell_nuke.py, em 0.72), 2 mordentes pesados de grampo que correm
    em trilhos de aco e capuz de saida embaixo (o projetil pronto desce por baixo dele para a saida).
Animacao (12 quadros, 0.11 s): 0 estojo aberto, garras nas portas (nucleo e ogiva presos); 1-3 o braco
esquerdo leva o nucleo (o banho pulsa forte quando o nucleo sai); 2-4 o braco direito leva a ogiva; 4-5 as
metades fecham; 6 o grampo bate com lampejo verde pelas costuras; 7-8 o lampejo apaga e o grampo solta;
9-10 o projetil desce para a saida; 11 berco vazio, novos nucleo e ogiva nas portas.
Teto: placas verdes (pintura) em blindagem extra pesada de 2 degraus, tampa da celula quente sem pintura
(anel octogonal em degrau com fenda verde), ombreiras dos manipuladores e o emblema do tile central: trevo
de 3 laminas de blindagem clara sobre base escura com pips verdes entre as laminas; setas das entradas e da
saida com pips verdes em fendas vazadas.
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
# camara de fundicao (contorno da blindagem de baixo) e visor
CH = [(-0.44, 1.42), (0.44, 1.42), (0.48, 1.37), (0.48, 1.02), (0.21, 0.60), (-0.21, 0.60), (-0.48, 1.02),
      (-0.48, 1.37)]
VP = (0.0, 1.03)             # centro do visor / cadinho
# manipuladores (lado esquerdo; o direito e o espelho)
SH = (-1.0, 0.78)            # ombro
L1, L2, LC = 0.52, 0.62, 0.15  # braco, antebraco, garra
PORT = (-0.37, 0.83)         # ponta da garra na porta de transferencia (chanfro esquerdo da camara)
CORE_AT = (-0.03, 0.04)      # ponta da garra esquerda sobre a janela do estojo
CAP_AT = (0.05, 0.31)        # ponta da garra direita sobre a ponta do projetil (espelho: x positivo)


# ============================================================================ estados da animacao
def _state(phase):
    """Estado do ciclo (dicionario) para o quadro da fase."""
    i = int(round(phase * NF)) % NF
    st = {
        "i": i,
        # trajeto das garras (0 = porta, 1 = estojo) e o que seguram
        "L": [0.0, 0.45, 0.85, 1.0, 0.6, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0][i],
        "R": [0.0, 0.0, 0.4, 0.8, 1.0, 0.55, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0][i],
        "Lhold": i in (0, 1, 2, 11),
        "Rhold": i in (0, 1, 2, 3, 11),
        "Lopen": i in (3, 4, 5, 6, 7, 8, 9, 10),
        "Ropen": i in (4, 5, 6, 7, 8, 9, 10),
        # nucleo / ogiva esperando nas portas
        "port_core": {8: 0.5, 9: 1.0, 10: 1.0}.get(i, 0.0),
        "port_cap": i in (9, 10),
        # estojo: abertura das metades (1 aberto), grampo (1 fechado), lampejo, conteudo, descida
        "gap": [1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0][i],
        "clamp": [0.0, 0.0, 0.0, 0.0, 0.0, 0.55, 1.0, 1.0, 0.45, 0.0, 0.0, 0.0][i],
        "flash": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.5, 0.18, 0.0, 0.0, 0.0][i],
        "core_in": i in (3, 4, 5, 6, 7, 8, 9, 10),
        "cap_on": i in (4, 5, 6, 7, 8, 9, 10),
        "slide": {9: 0.10, 10: 0.36}.get(i, 0.0),
        "shell": i != 11,
        # banho do cadinho (forca da emissao)
        "melt": [1.0, 1.55, 1.3, 1.1, 1.0, 0.95, 1.05, 1.0, 0.95, 1.0, 1.1, 1.0][i],
    }
    return st


# ============================================================================ utilidades
def _extra(st=None):
    melt = st["melt"] if st else 1.0
    flash = st["flash"] if st else 0.0
    return {
        "glass": _glass(),
        "melt": B.mat_glow("nk_melt", (0.30, 1.0, 0.14), 1.05 * melt),
        "melt_hot": B.mat_glow("nk_melt_hot", (0.55, 1.0, 0.30), 2.0 * melt),
        "flash": B.mat_glow("nk_flash", (0.40, 1.0, 0.18), 1.0 + 5.0 * flash),
        "cap": B.mat_metal("nk_ogive", NK.OGIVE, rough=0.42, metal=0.6),
        "body": B.mat_metal("nk_body", NK.BODY, rough=0.48, metal=0.55),
        "core_glow": B.mat_glow("nk_core", Mo.GREEN, 2.2),
        "lead": B.mat_metal("nk_lead", (0.11, 0.115, 0.12), rough=0.55, metal=0.5),
    }


def _glass():
    """Vidro de chumbo: transmissivo, tom verde escuro, com reflexo das luzes (le como vidro grosso)."""
    if "nk_glass" in B._MATS:
        return B._MATS["nk_glass"]
    m = B.bpy.data.materials.new("nk_glass")
    b, nt = B._principled(m)
    b.inputs["Base Color"].default_value = (0.20, 0.42, 0.26, 1)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.06
    b.inputs["IOR"].default_value = 1.6
    b.inputs["Transmission Weight"].default_value = 1.0
    B._MATS["nk_glass"] = m
    return m


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
    return (lambda p: p) if sx < 0 else Mo.mirror


def _mx(sx, p):
    return (sx * -p[0], p[1]) if sx > 0 else p


def _chevron(name, cx, cy, ang, M, tags, z=0.03, s=1.0, mat=None):
    """Seta de fluxo (chevron) apontando para ang (graus), em LED fraco."""
    pts = [(-0.05, -0.07), (-0.01, -0.07), (0.05, 0.0), (-0.01, 0.07), (-0.05, 0.07), (0.01, 0.0)]
    pts = [(x * s, y * s) for x, y in pts]
    B.loft(name, _rot(pts, ang, cx, cy), _rot(pts, ang, cx, cy), z, z + 0.006, mat or M["glow_dim"], bevel=0.0,
           tags=tags)


def _link(p0, p1, w0, w1, c=0.03, ext0=0.0, ext1=0.0):
    """Elo afunilado de p0 a p1 (larguras w0 -> w1) com cantos chanfrados."""
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
    # bases: (nome, centro, lado da seta, angulo da seta)
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
        lip = B.plate(f"padlip_{name}", B.rpoly(cx, cy, 0.73, 0.73, 0, chamfer=0.075), 0.035, 0.056, AM,
                      slope=0.005, bevel=0.004, tags=tags)
        inner = B.rpoly(cx, cy, 0.69, 0.69, 0, chamfer=0.066)
        B.cut(lip, [B.loft(f"padlip_h{name}", inner, inner, 0.02, 0.3, K, bevel=0.0)])
        B.loft(f"padwell_{name}", inner, inner, 0.03, 0.04, K, bevel=0.0, tags=tags)
        B.box(f"padgv_{name}", cx, cy, 0.012, 0.58, 0.04, 0.046, KM, bevel=0.0, tags=tags)
        B.box(f"padgh_{name}", cx, cy, 0.58, 0.012, 0.04, 0.046, KM, bevel=0.0, tags=tags)
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
    vx, vy = VP
    # leito escuro de toda a fileira de cima
    B.plate("mc_bed", B.rpoly(0, 0.98, 2.90, 0.92, 0, chamfer=0.08), 0.0, 0.05, K, slope=0.01, tags=tags)
    # base escura um pouco maior que a blindagem (moldura escura em volta)
    B.plate("ch_core", B.offset_poly(CH, -0.03), 0.0, 0.16, K, slope=0.02, tags=tags)
    # blindagem de baixo (parede grossa): bisel duplo
    wa, wp = B.shard("ch_wall", CH, 0.0, 0.42, A, slope=0.085, groove=0.035, panel_h=0.03, tags=tags)
    # visor: furo octogonal ate o cadinho
    hole = _octo(vx, vy, 0.235)
    for k, t in enumerate((wa, wp)):
        B.cut(t, [B.loft(f"ch_vh{k}", hole, hole, 0.16, 0.9, K, bevel=0.0)])
    B.loft("ch_vbed", hole, hole, 0.14, 0.16, M["black"], bevel=0.0, tags=tags)
    # cadinho de aco: anel octogonal com bico, banho verde no meio (pulsa) e brilho mais forte no centro
    cru = B.plate("cru_ring", _octo(vx, vy, 0.16), 0.16, 0.25, S, slope=0.02, bevel=0.006, tags=tags)
    B.cut(cru, [B.loft("cru_in", _octo(vx, vy, 0.115), _octo(vx, vy, 0.115), 0.20, 0.5, K, bevel=0.0)])
    B.loft("cru_melt", _octo(vx, vy, 0.118), _octo(vx, vy, 0.118), 0.20, 0.215, X["melt"], bevel=0.0, tags=tags)
    B.loft("cru_hot", _octo(vx, vy, 0.045, 0), _octo(vx, vy, 0.045, 0), 0.215, 0.22, X["melt_hot"], bevel=0.0,
           tags=tags)
    for k in range(4):
        # garras do suporte do cadinho (aco escuro) nas diagonais
        a = 45 + 90 * k
        p = _rot([(0.15, -0.025), (0.225, -0.025), (0.225, 0.025), (0.15, 0.025)], a, vx, vy)
        B.loft(f"cru_hold{k}", p, p, 0.16, 0.235, KM, bevel=0.005, tags=tags)
    # vidro de chumbo (transmissivo, verde escuro) sobre o cadinho + moldura de aco em degrau
    B.loft("ch_glass", _octo(vx, vy, 0.225), _octo(vx, vy, 0.225), 0.30, 0.315, X["glass"], bevel=0.0,
           tags=tags)
    lip = B.plate("ch_vlip", _octo(vx, vy, 0.235), 0.30, 0.36, S, slope=0.012, bevel=0.004, tags=tags)
    B.cut(lip, [B.loft("ch_vlc", _octo(vx, vy, 0.205), _octo(vx, vy, 0.205), 0.2, 0.6, K, bevel=0.0)])
    # segundo degrau de blindagem: arco traseiro com baia de respiro (persianas + pips verdes) e duas
    # bochechas em cunha dos lados do visor
    arch = [(-0.38, 1.415), (0.38, 1.415), (0.43, 1.365), (0.43, 1.24), (0.27, 1.24), (0.22, 1.285), (-0.22, 1.285),
            (-0.27, 1.24), (-0.43, 1.24), (-0.43, 1.365)]
    aa, ap = B.shard("ch_arch", arch, 0.40, 0.54, A, slope=0.04, groove=0.02, panel_h=0.022, tags=tags)
    for k, t in enumerate((aa, ap)):
        B.cut(t, [B.box(f"ch_avc{k}", 0, 1.35, 0.30, 0.055, 0.44, 0.8, K, bevel=0.0)])
    B.box("ch_avbed", 0, 1.35, 0.30, 0.055, 0.435, 0.445, M["black"], bevel=0.0, tags=tags)
    for k in range(4):
        B.box(f"ch_avpip{k}", -0.105 + k * 0.07, 1.35, 0.032, 0.022, 0.445, 0.455, M["glow_dim"], bevel=0.0,
              tags=tags)
    cheek = [(-0.44, 1.20), (-0.30, 1.20), (-0.255, 1.155), (-0.255, 0.96), (-0.30, 0.88), (-0.44, 1.02)]
    for sx in (-1, 1):
        f = _flip(sx)
        ca, cp = B.shard(f"ch_cheek{sx}", f(cheek), 0.40, 0.52, A, slope=0.035, groove=0.018, panel_h=0.02,
                         tags=tags)
        Mo.slot_with_pips(f"ch_csl{sx}", sx * 0.365, 0.98, 1.14, 0.04, 0.54, 3, M, tags, target=[ca, cp],
                          depth=0.07, pip_mat=M["glow_dim"])
    # LED de estado na ponta da cunha (aponta para o berco)
    Mo.slot_with_pips("ch_tip", 0.755, -0.06, 0.06, 0.035, 0.45, 2, M, tags, target=[wa, wp], depth=0.08,
                      vertical=False)
    # portas de transferencia nos chanfros de baixo (recesso escuro; nucleo / ogiva esperando)
    for sx in (-1, 1):
        px, py = sx * 0.372, 0.852                        # ponto do chanfro em frente a garra
        ang = math.degrees(math.atan2(-0.27, 0.42 * sx))  # normal do chanfro (para fora)
        port = _rot([(-0.06, -0.09), (0.12, -0.09), (0.12, 0.09), (-0.06, 0.09)], ang + 180, px, py)
        for k, t in enumerate((wa, wp)):
            B.cut(t, [B.loft(f"ch_port{sx}{k}", port, port, 0.20, 0.9, K, bevel=0.0)])
        B.loft(f"ch_pbed{sx}", port, port, 0.19, 0.20, M["black"], bevel=0.0, tags=tags)
        # guias de aco na boca da porta
        for j in (-1, 1):
            g = _rot([(-0.02, j * 0.09 - 0.012), (0.12, j * 0.09 - 0.012), (0.12, j * 0.09 + 0.012),
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


def _cap(name, x, y0, z, M, X, tags):
    """Ogiva do Projetil Nuclear (na escala do berco), apontando para +Y a partir de y0."""
    prof = [(NK.Y_NECK1 - 0.01, NK.R - 0.012), (0.25, NK.R * 0.84), (0.35, NK.R * 0.62), (0.44, NK.R * 0.30)]
    zc = z + (NK.R - 0.012) * SC
    base = prof[0][0]
    for k in range(len(prof) - 1):
        (ya, ra), (yb, rb) = prof[k], prof[k + 1]
        NK.octo_cyl(f"{name}{k}", x, y0 + (ya - base) * SC, y0 + (yb - base) * SC, ra * SC, X["cap"], tags,
                    r2=rb * SC, z=zc, bevel=0.003)
    NK.octo_cyl(f"{name}_fz", x, y0 + (0.44 - base) * SC, y0 + (0.50 - base) * SC, NK.R * 0.30 * SC, M["steel"],
                tags, r2=0.006, z=zc, bevel=0.0)


# ============================================================================ maquina: manipuladores
def _arm(prefix, sx, t, hold, opened, M, X, tags, wait=0.0):
    """Manipulador remoto do lado sx; t = 0 na porta, 1 no estojo; hold = 'core' | 'cap' | None;
    wait = nucleo / ogiva saindo da porta entre os dedos abertos (0..1, tamanho do nucleo)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    S0 = (sx * -SH[0], SH[1])
    p0 = (sx * -PORT[0], PORT[1])
    p1 = (CORE_AT if sx < 0 else CAP_AT)
    T = (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
    E, W, fa = _ik(S0, T, -sx)
    # torre do ombro: base escura, anel claro de bisel duplo, cubo de aco
    B.plate(f"{prefix}_sbase", _octo(*S0, 0.215), 0.0, 0.30, K, slope=0.02, tags=tags)
    sa, sp = B.shard(f"{prefix}_sring", _octo(*S0, 0.20), 0.28, 0.40, A, slope=0.04, groove=0.02, panel_h=0.02,
                     tags=tags)
    for k in range(4):
        a = 22.5 + 90 * k + 45
        cx, cy = S0[0] + math.cos(math.radians(a)) * 0.17, S0[1] + math.sin(math.radians(a)) * 0.17
        for tt, nm in ((sa, "a"), (sp, "b")):
            if tt is not None:
                B.cut(tt, [B.rbox(f"{prefix}_sn{k}{nm}", cx, cy, 0.022, 0.08, 0.36, 0.8, K, rot=a + 90, bevel=0.0)])
    ua = math.degrees(math.atan2(E[1] - S0[1], E[0] - S0[0]))
    B.plate(f"{prefix}_shub", _octo(*S0, 0.10, ua + 22.5), 0.40, 0.47, S, slope=0.015, bevel=0.005, tags=tags)
    # braco: viga escura + casca clara de bisel duplo
    B.plate(f"{prefix}_ubeam", _link(S0, E, 0.17, 0.13, 0.03, 0.06, 0.06), 0.44, 0.50, KM, slope=0.012, tags=tags)
    ua_, up = B.shard(f"{prefix}_uarm", _link(S0, E, 0.15, 0.11, 0.035, -0.02, -0.06), 0.49, 0.58, A, slope=0.03,
                      groove=0.014, panel_h=0.016, tags=tags)
    # fenda com pip verde no braco
    mx, my = (S0[0] + E[0]) / 2, (S0[1] + E[1]) / 2
    for tt, nm in ((ua_, "a"), (up, "b")):
        if tt is not None:
            B.cut(tt, [B.rbox(f"{prefix}_usl{nm}", mx, my, 0.16, 0.034, 0.53, 0.9, K, rot=ua, bevel=0.0)])
    B.rbox(f"{prefix}_uslb", mx, my, 0.16, 0.034, 0.525, 0.535, M["black"], rot=ua, bevel=0.0, tags=tags)
    for k in (-1, 1):
        B.rbox(f"{prefix}_usp{k}", mx + math.cos(math.radians(ua)) * k * 0.04,
               my + math.sin(math.radians(ua)) * k * 0.04, 0.03, 0.016, 0.535, 0.542, M["glow_dim"], rot=ua,
               bevel=0.0, tags=tags)
    B.plate(f"{prefix}_spin", _octo(*S0, 0.06, ua), 0.58, 0.62, S, slope=0.012, bevel=0.004, tags=tags)
    B.plate(f"{prefix}_spinc", _octo(*S0, 0.03, ua), 0.62, 0.635, KM, slope=0.006, bevel=0.002, tags=tags)
    # cotovelo de aco com tampa escura
    B.plate(f"{prefix}_elb", _octo(*E, 0.075, ua), 0.42, 0.60, S, slope=0.015, bevel=0.005, tags=tags)
    B.plate(f"{prefix}_elbc", _octo(*E, 0.04, ua), 0.60, 0.62, KM, slope=0.008, bevel=0.003, tags=tags)
    # antebraco (mais baixo que o braco): viga escura + casca clara, 2 tubos hidraulicos de aco
    fad = math.degrees(fa)
    B.plate(f"{prefix}_fbeam", _link(E, W, 0.12, 0.09, 0.025, 0.0, 0.03), 0.36, 0.42, KM, slope=0.01, tags=tags)
    B.shard(f"{prefix}_farm", _link(E, W, 0.10, 0.075, 0.025, -0.08, -0.05), 0.41, 0.48, A, slope=0.022,
            groove=0.012, panel_h=0.012, tags=tags)
    for k in (-1, 1):
        nx, ny = -math.sin(fa) * k * 0.062, math.cos(fa) * k * 0.062
        mxx, myy = (E[0] + W[0]) / 2 + nx, (E[1] + W[1]) / 2 + ny
        B.rbox(f"{prefix}_fhyd{k}", mxx, myy, L2 * 0.62, 0.016, 0.40, 0.42, S, rot=fad, bevel=0.003, tags=tags)
    # punho e garra de 2 dedos (abre ao soltar)
    B.plate(f"{prefix}_wrist", _octo(*W, 0.05, fad), 0.34, 0.46, S, slope=0.012, bevel=0.004, tags=tags)
    B.plate(f"{prefix}_wristc", _octo(*W, 0.026, fad), 0.46, 0.475, KM, slope=0.006, bevel=0.002, tags=tags)
    ux, uy = math.cos(fa), math.sin(fa)
    nx, ny = -uy, ux
    g = 0.058 if opened else (0.042 if hold else 0.03)
    for k in (-1, 1):
        bx, by = W[0] + ux * 0.07 + nx * k * g, W[1] + uy * 0.07 + ny * k * g
        B.rbox(f"{prefix}_fing{k}", bx, by, 0.10, 0.026, 0.34, 0.40, S, rot=fad, bevel=0.004, tags=tags)
        tx_, ty_ = W[0] + ux * 0.13 + nx * k * (g - 0.012), W[1] + uy * 0.13 + ny * k * (g - 0.012)
        B.rbox(f"{prefix}_tip{k}", tx_, ty_, 0.05, 0.022, 0.34, 0.39, KM, rot=fad - k * 30, bevel=0.003, tags=tags)
    item = hold or (("core" if sx < 0 else "cap") if wait > 0 else None)
    if item == "core":
        _core(f"{prefix}_core", W[0] + ux * 0.095, W[1] + uy * 0.095, 0.35, fad + 90, M, X, tags,
              s=1.0 if hold else wait)
    elif item == "cap":
        _cap(f"{prefix}_cap", W[0] + ux * 0.10, W[1] + uy * 0.10 - 0.08, 0.255, M, X, tags)


# ============================================================================ maquina: berco de montagem
def _half(prefix, sx, ox, oy, M, X, tags, core_in):
    """Metade sx do estojo (sx = -1 esquerda): anel de base, colar claro, corpo escuro com meia janela e
    faixa verde, colar do pescoco. ox/oy = deslocamento da metade."""
    K, A, S = M["core"], M["armor"], M["steel"]

    def Y(y):
        return y * SC + SY + oy

    def poly(x0, x1, y0, y1, c=0.0):
        pts = [(x0, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0, y1)]
        pts = [(ox + sx * x, y) for x, y in pts]
        return pts if sx > 0 else list(reversed(pts))
    hw = NK.R * math.cos(math.radians(22.5)) * SC        # meia largura do corpo
    top = SZ + 2 * NK.R * SC * 0.93
    B.plate(f"{prefix}_ring", poly(0.004, (NK.R + 0.018) * SC * 0.97, Y(NK.Y_BASE0), Y(NK.Y_BASE1), 0.012),
            SZ, top - 0.01, S, slope=0.022, bevel=0.004, tags=tags)
    ca, cp = B.shard(f"{prefix}_col", poly(0.004, (NK.R + 0.02) * SC, Y(NK.Y_COL0), Y(NK.Y_COL1), 0.03), SZ,
                     top + 0.012, A, slope=0.022, groove=0.01, panel_h=0.014, tags=tags)
    # LED do contador (um por metade) numa fenda escura no colar
    cyc = Y((NK.Y_COL0 + NK.Y_COL1) / 2)
    for t, nm in ((ca, "a"), (cp, "b")):
        if t is not None:
            B.cut(t, [B.box(f"{prefix}_cslc{nm}", ox + sx * 0.05, cyc, 0.05, 0.032, top - 0.02, top + 0.4, K,
                            bevel=0.0)])
    B.box(f"{prefix}_cslb", ox + sx * 0.05, cyc, 0.05, 0.032, top - 0.025, top - 0.015, M["black"], bevel=0.0,
          tags=tags)
    B.box(f"{prefix}_cpip", ox + sx * 0.05, cyc, 0.028, 0.016, top - 0.015, top - 0.008, M["glow_dim"], bevel=0.0,
          tags=tags)
    body = B.plate(f"{prefix}_body", poly(0.004, hw, Y(NK.Y_COL1) - 0.004, Y(NK.Y_NECK0) + 0.004, 0.0), SZ, top,
                   X["body"], slope=0.03, bevel=0.005, tags=tags)
    # meia janela na borda interna (o nucleo aparece pela janela quando fecha)
    wy0, wy1 = Y(-0.165), Y(0.035)
    B.cut(body, [B.box(f"{prefix}_win", ox, (wy0 + wy1) / 2, 0.064, wy1 - wy0, SZ - 0.02, top + 0.3, K,
                       bevel=0.0)])
    # faixa verde num sulco escuro
    by = Y(-0.225)
    B.box(f"{prefix}_bandk", ox + sx * (hw / 2 + 0.002), by, hw - 0.004, 0.034, top - 0.004, top + 0.004,
          M["black"], bevel=0.0, tags=tags)
    B.box(f"{prefix}_band", ox + sx * (hw / 2 + 0.004), by, hw - 0.008, 0.014, top + 0.004, top + 0.009,
          M["glow_dim"], bevel=0.0, tags=tags)
    B.shard(f"{prefix}_neck", poly(0.004, (NK.R + 0.01) * SC, Y(NK.Y_NECK0), Y(NK.Y_NECK1), 0.02), SZ,
            top + 0.008, A, slope=0.018, groove=0.008, panel_h=0.01, tags=tags)


def _cradle(M, X, tags, st):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    # bloco de maquina do tile central e calha escura com trilhos de aco
    B.plate("cr_block", B.rpoly(0, 0, 0.94, 0.94, 0, chamfer=0.16), 0.0, 0.04, K, slope=0.015, tags=tags)
    B.plate("cr_trough", B.rpoly(0, -0.02, 0.36, 0.90, 0, chamfer=0.05), 0.03, 0.06, KM, slope=0.012, tags=tags)
    B.box("cr_well", 0, -0.02, 0.27, 0.84, 0.055, 0.064, M["black"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"cr_rail{sx}", sx * 0.155, -0.02, 0.022, 0.86, 0.04, 0.09, S, bevel=0.004, tags=tags)
    # selas de aco sob a base e sob a ogiva
    for k, y in enumerate((-0.25, 0.33)):
        B.box(f"cr_saddle{k}", 0, y, 0.30, 0.05, 0.05, 0.075, S, bevel=0.006, tags=tags)
    # LED de pronto no fundo da calha (aparece com o berco vazio)
    B.box("cr_ready", 0, 0.05, 0.03, 0.18, 0.064, 0.07, M["glow_dim"], bevel=0.0, tags=tags)

    # estojo (2 metades) + nucleo + ogiva
    if st["shell"]:
        oy = -st["slide"]
        if st["core_in"]:
            _core("sh_core", 0.0, Y_core(oy), SZ + 0.06, 90, M, X, tags)
        gap = 0.058 * st["gap"]
        for sx in (-1, 1):
            _half(f"sh{sx}", sx, sx * gap, oy, M, X, tags, st["core_in"])
        if st["cap_on"]:
            _cap("sh_cap", 0.0, NK.Y_NECK1 * SC + SY + oy - 0.004, SZ, M, X, tags)
        if st["flash"] > 0:
            # lampejo verde pelas costuras (linha no meio + juntas dos colares)
            f = st["flash"]
            y0, y1 = (NK.Y_BASE1 * SC + SY + oy, NK.Y_NECK1 * SC + SY + oy)
            B.box("fl_seam", 0, (y0 + y1) / 2, 0.012 + 0.008 * f, y1 - y0, SZ + 0.05, SZ + 0.29, X["flash"],
                  bevel=0.0, tags=tags)
            for k, yy in enumerate((NK.Y_COL1, NK.Y_NECK0)):
                B.box(f"fl_joint{k}", 0, yy * SC + SY + oy, 0.20, 0.008 + 0.006 * f, SZ + 0.24, SZ + 0.27,
                      X["flash"], bevel=0.0, tags=tags)
        if st["slide"] > 0:
            # o que desce alem do capuz fica escondido (holdout transparente)
            B.box("out_hold", 0, -0.62, 0.40, 0.30, -0.1, 1.2, _holdout(), bevel=0.0, tags=tags)

    # mordentes do grampo: blocos claros pesados que correm em trilhos de aco (bisel duplo, cunha interna)
    xin = 0.150 + (1.0 - st["clamp"]) * 0.075
    for sx in (-1, 1):
        f = _flip(sx)
        for k, y in enumerate((0.25, -0.30)):
            B.box(f"cl_rail{sx}{k}", sx * 0.345, y, 0.25, 0.03, 0.04, 0.12, S, bevel=0.005, tags=tags)
            B.box(f"cl_stop{sx}{k}", sx * 0.455, y, 0.035, 0.06, 0.04, 0.17, KM, bevel=0.006, tags=tags)
        jaw = [(-xin, -0.22), (-xin - 0.05, -0.27), (-xin - 0.20, -0.27), (-xin - 0.235, -0.235),
               (-xin - 0.235, 0.185), (-xin - 0.20, 0.22), (-xin - 0.05, 0.22), (-xin, 0.17)]
        ja, jp = B.shard(f"cl_jaw{sx}", f(jaw), 0.0, 0.34, A, slope=0.045, groove=0.02, panel_h=0.024, tags=tags)
        # dentes escuros da face interna (prendem as metades) + linha de painel
        B.box(f"cl_face{sx}", sx * (xin + 0.012), -0.025, 0.024, 0.34, 0.06, 0.30, K, bevel=0.004, tags=tags)
        jx = sx * (xin + 0.13)
        Mo.slot_with_pips(f"cl_sl{sx}", jx, -0.17, 0.10, 0.045, 0.364, 3, M, tags, target=[ja, jp], depth=0.075,
                          pip_mat=M["glow"] if st["clamp"] >= 1.0 else M["glow_dim"])
        if jp is not None:
            B.cut(jp, [B.rbox(f"cl_pl{sx}", sx * (xin + 0.06), 0.16, 0.022, 0.10, 0.32, 0.8, K, rot=sx * 40,
                              bevel=0.0)])
        B.bolts(f"cl_b{sx}", [(jx, 0.165), (jx, -0.215)], 0.37, 0.016, S, tags=tags)
        if st["flash"] > 0:
            B.box(f"fl_jaw{sx}", sx * (xin + 0.002), -0.025, 0.010, 0.30, 0.30, 0.31, X["flash"], bevel=0.0,
                  tags=tags)

    # capuz de saida (sobre a ponta de baixo da calha): o projetil pronto desce por baixo dele
    hood = [(-0.22, -0.30), (0.22, -0.30), (0.26, -0.34), (0.26, -0.47), (-0.26, -0.47), (-0.26, -0.34)]
    ha, hp = B.shard("cr_hood", hood, 0.30, 0.44, A, slope=0.045, groove=0.02, panel_h=0.02, tags=tags)
    Mo.slot_with_pips("cr_hsl", -0.395, -0.12, 0.12, 0.045, 0.46, 3, M, tags, target=[ha, hp], depth=0.075,
                      vertical=False, pip_mat=M["glow"] if st["slide"] > 0 else M["glow_dim"])
    B.bolts("cr_hb", [(-0.20, -0.44), (0.20, -0.44)], 0.465, 0.015, S, tags=tags)


def Y_core(oy):
    """y do nucleo dentro do estojo (centro da janela)."""
    return (-0.165 + 0.035) / 2 * SC + SY + oy


def machine(M, T="machine", phase=0.0):
    """Maquinario (fileira de cima + tile central); transparente nos tiles de entrada e saida."""
    tags = (T,)
    st = _state(phase)
    X = _extra(st)
    _chamber(M, X, tags, st)
    _cradle(M, X, tags, st)
    _arm("aL", -1, st["L"], "core" if st["Lhold"] else None, st["Lopen"], M, X, tags, wait=st["port_core"])
    _arm("aR", 1, st["R"], "cap" if st["Rhold"] else None, st["Ropen"], M, X, tags,
         wait=1.0 if st["port_cap"] else 0.0)


# ============================================================================ teto
def roof(M, T="roof"):
    """Teto provisorio (placas verdes)."""
    tags = (T,)
    green = B.mat_roof_green()
    K = M["core"]
    B.box("rf_under", 0, 0, 3, 3, -0.05, 0.02, K, bevel=0.0, tags=tags)
    for tx in range(3):
        for ty in range(3):
            cx, cy = tx - 1.0, 1.0 - ty
            B.shard(f"rf{tx}{ty}", B.rpoly(cx, cy, 0.92, 0.92, 0, chamfer=0.1), 0.0, 0.07, green, slope=0.03,
                    groove=0.05, panel_h=0.022, tags=tags)
