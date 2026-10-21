"""Canhao PEM Medio ("Treme-Treme", 76 mm) - a raia-eletrica do litoral brasileiro, familia do 76 mm + assinatura PEM.

Torre redonda e achatada (o disco da raia visto de cima), 2x2:
  * nadadeiras peitorais = placas claras em crescente de bisel duplo seguindo a borda do disco, partidas em duas
    (frente e tras) com fendas de pips azuis; as pontas da frente fecham ao lado do berco do cano (garras);
  * orgaos eletricos = os 2 TAMBORES DE CELULAS PEM nos lados, entre as nadadeiras e o corpo (cilindros azul-marinho
    com aneis de cobre e 3 janelas azuis de contagem, num rebaixo preto), ligados a culatra por cabos com aneis de
    cobre;
  * corpo central em ponta de flecha com os dois "olhos" (lentes azuis em orbitas escuras) e os espiraculos atras,
    pulso PEM gravado num rebaixo preto (traco azul fraco, como o raio do Trovao);
  * cauda: quilha estreita para tras, ladeada pelas baias de exaustao com pips azuis.
Cano unico grosso de 76 mm: culatra escura no berco, luva clara com canal, TRES BOBINAS de fio de cobre separadas
por colares de aco e luvas curtas, boca emissora facetada com fendas escuras e anel de contato de cobre. Depois do
tiro as bobinas da frente brilham em azul (heat_color azul; o calor sobe para a boca).
Kit da familia PEM: parts/bs_pem_light.py (pem, coil, cell, stroke).
"""

import math

import bs3d as B
import models as Mo
from parts.bs_pem_light import coil, pem, rslot, side, stroke

PART = {
    "id": "rafaeltessaro.bs_pem_medium",
    "kind": "gun",
    "size": [2, 2],
    "pivot": [1.0, 0.95],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 1.96,            # lado do quadrado do sprite da torre (disco ate +-0.95)
    "ring_r": 0.78,                # raio do anel da torre no teto/piso
    "accent": "blue",
    "collider": 0.88,
    "crew": 2,                     # SPEC_2.0 pem_weapons[Treme-Treme].crew
    "barrels": {
        "ys": [0.0],               # cano unico grosso
        "root": 0.42,              # pivo -> raiz do cano (culatra no berco escuro)
        "length": 1.45,            # raiz -> boca
        "width": 0.42,             # largura do sprite do cano (cabem as bobinas e a boca)
        "pad": 0.16,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.14, 0.10, 0.055, 0.02],     # 4 quadros de recuo + repouso (spec de arte)
        "heat": [0.72, 0.52, 0.32, 0.14],        # bobinas azuis depois do tiro
        "heat_color": (0.05, 0.35, 1.0),
        "interval": 0.07,
    },
    "lights": [
        {"at": [0.0, -0.70], "size": 0.9, "color": [60, 150, 255], "z": 0.8},
    ],
    "preview_pattern": "single",
    "preview_fx": "plasma",
}

ZB = 0.50                          # altura do eixo do cano
ROOT = PART["barrels"]["root"]
PAD = PART["barrels"]["pad"]
DRUM_X = 0.465                     # tambores de celulas (orgaos eletricos)
DRUM_Y = (-0.40, 0.28)


def _arc(R, a0, a1, n):
    """Pontos do lado esquerdo do disco: angulo a partir de +Y (frente) girando para -X, em graus."""
    return [(-R * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))),
             R * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]


# nadadeira da frente (esquerda): borda externa no disco, ponta fechando ao lado do berco
FIN_F = [(-0.27, 0.62), (-0.33, 0.86)] + _arc(0.94, 26, 92, 4) + [(-0.64, 0.02), (-0.64, 0.30), (-0.50, 0.50)]
# nadadeira de tras: crescente ate a cauda
FIN_R = _arc(0.94, 99, 157, 4) + [(-0.30, -0.70), (-0.46, -0.50), (-0.64, -0.24), (-0.65, -0.06)]
FIN_Z = (0.30, 0.62)


def head(M, T="head", phase=0.0):
    """Disco da raia: nadadeiras claras, tambores de celulas nos lados, corpo com olhos azuis, cauda."""
    tags = (T,)
    X = pem(M)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]

    # anel e nucleo escuro (disco facetado de 16 lados)
    B.cyl("ring", 0, 0, 0.04, 0.86, 0.08, KM, axis="Z", verts=64, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, 0.82, 24, 0.13), 0.09, 0.018, S, tags=tags)
    disc = [(0.83 * math.cos(math.radians(11.25 + 22.5 * i)), 0.83 * math.sin(math.radians(11.25 + 22.5 * i)))
            for i in range(16)]
    B.plate("core", disc, 0.06, 0.30, K, slope=0.04, tags=tags)

    # berco escuro do cano + colar da boca do berco
    y0c = ROOT - PAD - 0.02
    crad = [(-0.17, y0c), (0.17, y0c), (0.21, y0c + 0.05), (0.21, 0.86), (0.16, 0.93), (-0.16, 0.93),
            (-0.21, 0.86), (-0.21, y0c + 0.05)]
    c = B.plate("cradle", crad, 0.26, 0.40, KM, slope=0.03, tags=tags)
    B.cut(c, [B.box("crad_c", 0, (y0c + 0.88) / 2, 0.26, 0.88 - y0c - 0.1, 0.34, 0.9, K, bevel=0.0)])
    B.box("cradbed", 0, (y0c + 0.88) / 2, 0.26, 0.88 - y0c - 0.1, 0.335, 0.345, M["black"], bevel=0.0, tags=tags)
    B.cyl("mouth", 0, 0.88, ZB - 0.02, 0.17, 0.08, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
    B.cyl("mouthr", 0, 0.845, ZB - 0.02, 0.176, 0.022, S, axis="Y", verts=8, bevel=0.004, tags=tags)

    # ---------------------------------------------------------------- tambores de celulas (orgaos eletricos)
    ya, yb = DRUM_Y
    for sx in (-1, 1):
        x = sx * DRUM_X
        B.box(f"drum_bed{sx}", x, (ya + yb) / 2, 0.30, yb - ya + 0.08, 0.26, 0.31, M["black"], bevel=0.0, tags=tags)
        B.cyl(f"drum{sx}", x, (ya + yb) / 2, 0.40, 0.125, yb - ya, X["navy"], axis="Y", verts=10, bevel=0.008,
              tags=tags)
        for k, y in enumerate((ya + 0.03, ya + 0.23, yb - 0.23, yb - 0.03)):
            B.cyl(f"drumcu{sx}{k}", x, y, 0.40, 0.132, 0.035, X["copper"] if 0 < k < 3 else S, axis="Y", verts=10,
                  bevel=0.003, tags=tags)
        # 3 janelas de contagem acesas (as celulas dentro do tambor), so na faixa de cima
        for k in range(3):
            y = ya + 0.29 + k * 0.05
            B.box(f"drumwin{sx}{k}", x, y, 0.07, 0.024, 0.50, 0.53, X["cell"] if k < 2 else M["black"], bevel=0.0,
                  tags=tags)
        # tampa de aco do eixo do tambor (frente) e cabo de alimentacao ate a culatra
        B.cyl(f"drumcap{sx}", x, yb + 0.03, 0.40, 0.07, 0.04, S, axis="Y", verts=10, bevel=0.004, tags=tags)
        cx0, cy0, cx1, cy1 = x * 0.92, yb + 0.05, sx * 0.20, 0.40
        ang = math.degrees(math.atan2(-(cx1 - cx0), cy1 - cy0))
        L = math.hypot(cx1 - cx0, cy1 - cy0)
        B.cyl(f"cable{sx}", (cx0 + cx1) / 2, (cy0 + cy1) / 2, 0.38, 0.03, L, KM, axis="Y", verts=8, yaw=ang,
              tags=tags)
        for j in range(3):
            t = (j + 1) / 4
            B.cyl(f"cabler{sx}{j}", cx0 + (cx1 - cx0) * t, cy0 + (cy1 - cy0) * t, 0.38, 0.037, 0.02, X["copper"],
                  axis="Y", verts=8, yaw=ang, tags=tags)

    # ---------------------------------------------------------------- nadadeiras peitorais (frente e tras)
    z0, z1 = FIN_Z
    for sx in (-1, 1):
        fa, fp = B.shard(f"finF{sx}", side(FIN_F, sx), z0, z1, A, slope=0.05, groove=0.025, panel_h=0.03,
                         tags=tags)
        ra, rp = B.shard(f"finR{sx}", side(FIN_R, sx), z0, z1 - 0.04, A, slope=0.05, groove=0.025, panel_h=0.03,
                         tags=tags)
        # fendas de pips seguindo a curva do disco (tangentes no meio do painel) e linhas de painel radiais
        for k, (th, n, t2, zt) in enumerate(((60, 3, (fa, fp), z1 + 0.03), (126, 2, (ra, rp), z1 - 0.01))):
            cx, cy = sx * 0.79 * math.sin(math.radians(th)), 0.79 * math.cos(math.radians(th))
            rslot(f"fslot{sx}{k}", cx, cy, 0.045, 0.26, -sx * (th + 90), zt, 0.08, n, list(t2), M, tags)
        for k, (th, t) in enumerate(((36, fp), (147, rp))):
            if t is not None:
                cx, cy = sx * 0.80 * math.sin(math.radians(th)), 0.80 * math.cos(math.radians(th))
                B.cut(t, [B.rbox(f"fpl{sx}{k}", cx, cy, 0.016, 0.17, 0.5, 0.9, K, rot=-sx * th, bevel=0.0)])
        # pistao entre a nadadeira da frente e o berco
        B.cyl(f"piston{sx}", sx * 0.30, 0.47, 0.42, 0.026, 0.22, S, axis="Y", verts=10, yaw=sx * 28, tags=tags)
        B.cyl(f"pistonb{sx}", sx * 0.35, 0.39, 0.42, 0.038, 0.10, KM, axis="Y", verts=10, yaw=sx * 28, tags=tags)

    # ---------------------------------------------------------------- corpo central (cabeca da raia) + olhos
    body = [(-0.17, -0.62), (0.17, -0.62), (0.25, -0.50), (0.27, 0.02), (0.20, 0.20), (0.08, 0.30), (-0.08, 0.30),
            (-0.20, 0.20), (-0.27, 0.02), (-0.25, -0.50)]
    ba, bp = B.shard("body", body, 0.30, 0.62, A, slope=0.06, groove=0.025, panel_h=0.03, tags=tags)
    for sx in (-1, 1):
        # olhos da raia: fendas inclinadas em orbitas escuras nos cantos da frente do corpo
        ex, ey, er = sx * 0.165, 0.115, sx * -32
        sock = B.rpoly(ex, ey, 0.05, 0.13, er, chamfer=0.016)
        for t in (ba, bp):
            if t is not None:
                B.cut(t, [B.loft(f"eyec{sx}{t.name}", sock, sock, 0.56, 1.2, K, bevel=0.0)])
        B.loft(f"eyebed{sx}", sock, sock, 0.555, 0.565, M["black"], bevel=0.0, tags=tags)
        B.rbox(f"eye{sx}", ex, ey, 0.016, 0.09, 0.56, 0.567, X["lens"], rot=er, bevel=0.0, tags=tags)
        # espiraculo (respiro escuro com 2 aletas) atras do olho
        sp = B.rpoly(sx * 0.20, -0.10, 0.06, 0.10, 0, chamfer=0.015)
        for t in (ba, bp):
            if t is not None:
                B.cut(t, [B.loft(f"spir{sx}{t.name}", sp, sp, 0.58, 1.2, K, bevel=0.0)])
        B.loft(f"spirbed{sx}", sp, sp, 0.575, 0.585, M["black"], bevel=0.0, tags=tags)
        for j in range(2):
            B.box(f"spirf{sx}{j}", sx * 0.20, -0.125 + j * 0.05, 0.05, 0.012, 0.58, 0.60, KM, bevel=0.002, tags=tags)
    # espinha elevada em ponta de flecha com o pulso PEM gravado num rebaixo em losango
    sp2 = [(-0.10, -0.56), (0.10, -0.56), (0.14, -0.48), (0.14, -0.08), (0.04, 0.06), (-0.04, 0.06), (-0.14, -0.08),
           (-0.14, -0.48)]
    s2a, s2p = B.shard("spine2", sp2, 0.60, 0.72, A, slope=0.035, groove=0.016, panel_h=0.02, tags=tags)
    rim = [(-0.115, -0.31), (-0.07, -0.40), (0.07, -0.40), (0.115, -0.31), (0.07, -0.20), (0.0, -0.15),
           (-0.07, -0.20)]
    for t in (s2a, s2p):
        if t is not None:
            B.cut(t, [B.loft(f"pul_cut{t.name}", rim, rim, 0.69, 1.2, K, bevel=0.0)])
    B.loft("pul_bed", rim, rim, 0.685, 0.695, M["black"], bevel=0.0, tags=tags)
    pulse = [(-0.085, -0.30), (-0.04, -0.30), (-0.015, -0.225), (0.015, -0.37), (0.04, -0.30), (0.085, -0.30)]
    for i in range(len(pulse) - 1):
        stroke(f"pul{i}", pulse[i], pulse[i + 1], 0.02, 0.695, 0.701, X["glow_dim"], tags)
    if s2p is not None:
        B.cut(s2p, [B.box("s2l", 0, -0.48, 0.20, 0.014, 0.72, 1.2, K, bevel=0.0),
                    B.box("s2l2", 0, -0.06, 0.12, 0.014, 0.72, 1.2, K, bevel=0.0)])
    B.bolts("bbolt", [(-0.19, -0.52), (0.19, -0.52)], 0.628, 0.016, S, tags=tags)

    # ---------------------------------------------------------------- cauda + baias de exaustao
    tail = [(-0.11, -0.60), (0.11, -0.60), (0.07, -0.86), (0.0, -0.955), (-0.07, -0.86)]
    B.shard("tail", tail, 0.30, 0.54, A, slope=0.03, groove=0.012, panel_h=0.02, tags=tags)
    for sx in (-1, 1):
        bay = side([(-0.12, -0.63), (-0.27, -0.63), (-0.30, -0.72), (-0.24, -0.84), (-0.12, -0.80)], sx)
        B.loft(f"vbay{sx}", bay, bay, 0.24, 0.36, M["black"], bevel=0.0, tags=tags)
        for i in range(3):
            B.rbox(f"vlouv{sx}{i}", sx * 0.20, -0.70 - i * 0.045, 0.14, 0.014, 0.30, 0.37, KM, rot=sx * -14,
                   bevel=0.003, tags=tags)
        for i in range(2):
            B.box(f"vpip{sx}{i}", sx * (0.165 + i * 0.065), -0.655, 0.038, 0.016, 0.34, 0.375, X["glow"], bevel=0.0,
                  tags=tags)


# ============================================================================ cano
def barrel(M, L=1.45, T="barrel", phase=0.0):
    """Cano grosso de 76 mm com tres bobinas de cobre: raiz em y=0, boca em y=L, centrado em x=0."""
    tags = (T,)
    hot = (T, "hot")
    X = pem(M)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = ZB
    # culatra escura (no berco)
    B.cyl("b_root", 0, 0.11, z, 0.13, 0.22, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
    B.cyl("b_rootring", 0, 0.225, z, 0.135, 0.03, S, axis="Y", verts=8, bevel=0.005, tags=tags)
    # nucleo escuro continuo (aparece entre luvas e colares)
    B.cyl("b_core", 0, 0.80, z, 0.09, 1.10, K, axis="Y", verts=12, tags=tags)
    # luvas claras com canal escuro entre as bobinas
    packs = [(0.40, 0.60), (0.70, 0.90), (1.00, 1.17)]
    sleeves = [(0.24, 0.39), (0.61, 0.69), (0.91, 0.99)]
    for i, (a, b) in enumerate(sleeves):
        sl = B.cyl(f"b_sleeve{i}", 0, (a + b) / 2, z, 0.118 - 0.006 * i, b - a, A, axis="Y", verts=8, bevel=0.006,
                   tags=tags)
        B.cut(sl, [B.box(f"b_chc{i}", 0, (a + b) / 2, 0.032, b - a + 0.1, z + 0.05, z + 0.3, K, bevel=0.0)])
    B.box("b_chbed", 0, 0.62, 0.032, 0.74, z + 0.04, z + 0.052, M["black"], bevel=0.0, tags=tags)
    # tres bobinas de fio de cobre, cada uma entre dois colares
    for i, (a, b) in enumerate(packs):
        coil(f"b_coil{i}", a + 0.012, b - 0.012, z, 0.172 - 0.006 * i, M, X, hot, wire=0.0155)
        for j, y in enumerate((a + 0.006, b - 0.006)):
            B.cyl(f"b_col{i}{j}", 0, y, z, 0.178 - 0.006 * i, 0.014, S, axis="Y", verts=8, bevel=0.003,
                  tags=hot if i == 2 else tags)
    # boca emissora facetada com fendas escuras e anel de contato de cobre no fundo
    yb = L - 0.13
    muz = [(-0.12, yb - 0.12), (0.12, yb - 0.12), (0.17, yb - 0.07), (0.17, yb + 0.04), (0.07, yb + 0.13),
           (-0.07, yb + 0.13), (-0.17, yb + 0.04), (-0.17, yb - 0.07)]
    mz = B.plate("b_muzzle", muz, z - 0.12, z + 0.12, A, slope=0.03, tags=tags)
    cuts = [B.box(f"b_mc{i}", 0, yb - 0.07 + i * 0.065, 0.40, 0.03, z + 0.02, z + 0.3, K, bevel=0.0)
            for i in range(3)]
    cuts.append(B.box("b_bore_c", 0, L, 0.06, 0.09, z - 0.06, z + 0.3, K, bevel=0.0))
    B.cut(mz, cuts)
    B.box("b_mcore", 0, yb - 0.01, 0.27, 0.20, z - 0.09, z + 0.025, X["copper"], bevel=0.0, tags=hot)
    B.box("b_crest", 0, yb + 0.105, 0.03, 0.03, z + 0.09, z + 0.13, AM, bevel=0.004, tags=tags)


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto 2x2: placas verdes (pintura), anel da torre e, nos cantos de tras, baias de celulas com LED azul."""
    tags = (T,)
    X = pem(M)
    w, h = PART["size"]
    pv = PART["pivot"]
    Mo.hull_roof(M, w, h, pv, PART["ring_r"], T)
    K, KM, AM, S = M["core"], M["core_mid"], M["armor_mid"], M["steel"]
    # cantos de tras (fora do anel): tampas triangulares de celulas com janela e LED azul
    for sx in (-1, 1):
        tri = side([(-0.94, -0.94), (-0.52, -0.94), (-0.94, -0.52)], sx)
        tp = B.plate(f"ctri{sx}", tri, 0.06, 0.11, AM, slope=0.02, tags=tags)
        cx, cy = sx * 0.80, -0.80
        B.cut(tp, [B.rbox(f"ctric{sx}", cx, cy, 0.18, 0.05, 0.09, 0.3, K, rot=sx * -45, bevel=0.0)])
        B.rbox(f"ctribed{sx}", cx, cy, 0.18, 0.05, 0.085, 0.095, M["black"], rot=sx * -45, bevel=0.0, tags=tags)
        B.rbox(f"ctriled{sx}", cx, cy, 0.12, 0.016, 0.095, 0.10, X["glow_dim"], rot=sx * -45, bevel=0.0, tags=tags)
        # calco claro no canto da frente
        ftri = side([(-0.94, 0.94), (-0.70, 0.94), (-0.94, 0.70)], sx)
        B.plate(f"ftri{sx}", ftri, 0.06, 0.10, AM, slope=0.015, tags=tags)


def floor(M, T="floor"):
    """Piso padrao do kit (anel, estantes, 2 postos) com as luzes azuis da familia."""
    from bsgen.common import crew_positions
    pem(M)
    w, h = PART["size"]
    pv = PART["pivot"]
    Mo.hull_floor(M, w, h, pv, PART["ring_r"], crew_positions(w, h, PART["crew"], pv), T)
