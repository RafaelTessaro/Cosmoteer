"""Bateria Flak Pesada ("Pororoca") - defesa 4x4 de canos duplos, mesma familia do 76 mm.

Montagem larga e baixa: nucleo escuro largo com escudos laterais em ondas (pororoca = a onda da
mare que sobe o Amazonas): tres niveis de placas curvas facetadas em cada flanco, empilhadas como a
crista de uma onda que quebra, cada uma terminando numa garra que avanca e se curva para dentro ate o
berco do cano. Espinha central com bloco de direcao de tiro (lente) e a onda gravada, tremonhas de
municao com contador nos vaos, bercos escuros dos canos e baia de exaustao traseira.
Canos: dois canos longos de 57 mm com luva de recuo escura, camisa de resfriamento perfurada, tubo com
canal escuro e abafador de chama multi-camara claro em ponta de flecha (janelas transversais escuras).
"""

import math

import bpy

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_flak_heavy",
    "kind": "gun",
    "size": [4, 4],
    "pivot": [2.0, 1.68],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 3.92,            # lado do quadrado do sprite da torre (cabeca larga: +-1.90)
    "ring_r": 1.36,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "collider": 1.55,
    "barrels": {
        "ys": [-0.45, 0.45],       # dois canos lado a lado
        "root": 0.62,              # pivo -> raiz do cano
        "length": 2.2,             # raiz -> boca
        "width": 0.50,             # largura do sprite do cano (cabe o abafador)
        "pad": 0.30,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.25, 0.21, 0.16, 0.11, 0.07, 0.04, 0.02],
        "heat": [0.72, 0.66, 0.59, 0.52, 0.45, 0.38, 0.31, 0.24, 0.16, 0.08],
        "interval": 0.06,
    },
    "lights": [
        {"at": [0.0, -1.12], "size": 1.7, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "alternate",
}

ZB = 0.50          # altura do eixo dos canos


# ============================================================================ utilidades
def check_meshes(T):
    """Falha alto se algum objeto com a tag T virar malha vazia (booleana ou deslocamento quebrado)."""
    dg = bpy.context.evaluated_depsgraph_get()
    empty = []
    for o in B.objects_with(T):
        if o.type != "MESH":
            continue
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        if len(me.vertices) == 0:
            empty.append(o.name)
        e.to_mesh_clear()
    if empty:
        raise RuntimeError(f"bs_flak_heavy: malhas vazias em '{T}': {empty}")


def _lines(target, name, specs, ztop, mat):
    """Linhas de painel recortadas no alvo: specs = [(x, y, comprimento, rotacao)]."""
    cuts = [B.rbox(f"{name}{i}", x, y, 0.016, ln, ztop - 0.045, ztop + 0.3, mat, rot=r, bevel=0.0)
            for i, (x, y, ln, r) in enumerate(specs)]
    B.cut(target, cuts)


def _stroke(name, p, q, w, z0, z1, mat, tags=()):
    """Traco fino (caixa girada) de p ate q; pontas estendidas w/2 para emendar com o proximo."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    rot = math.degrees(math.atan2(-dx, dy))
    return B.rbox(name, (p[0] + q[0]) / 2, (p[1] + q[1]) / 2, w, math.hypot(dx, dy) + w, z0, z1, mat, rot=rot,
                  bevel=0.0, tags=tags)


def _band(P, W):
    """Poligono de uma faixa ao longo da linha central P (larguras W por ponto)."""
    n = len(P)
    left, right = [], []
    for i in range(n):
        a, b = P[max(i - 1, 0)], P[min(i + 1, n - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        left.append((P[i][0] + nx * W[i] / 2, P[i][1] + ny * W[i] / 2))
        right.append((P[i][0] - nx * W[i] / 2, P[i][1] - ny * W[i] / 2))
    return left + right[::-1]


def _trim(P, d0, d1=None):
    """Encurta a linha central d0 no inicio e d1 no fim (ao longo da tangente)."""
    d1 = d0 if d1 is None else d1
    P = list(P)
    for i, j, d in ((0, 1, d0), (-1, -2, d1)):
        ax, ay = P[i]
        bx, by = P[j]
        ln = math.hypot(bx - ax, by - ay) or 1.0
        P[i] = (ax + (bx - ax) / ln * d, ay + (by - ay) / ln * d)
    return P


def _crest(name, P, W, z0, z1, mat, s=0.07, g=0.03, ph=0.03, tags=()):
    """Placa curva de onda com bisel duplo: faixa chanfrada + painel interno elevado (so onde cabe)."""
    bottom = _band(P, W)
    top = _band(_trim(P, s), [max(w - 2 * s, 0.02) for w in W])
    a = B.loft(name, bottom, top, z0, z1, mat, bevel=0.018, seg=1, tags=tags)
    d = s + g
    idx = [i for i, w in enumerate(W) if w - 2 * d >= 0.05]
    if len(idx) < 2:
        return a, None
    i0, i1 = idx[0], idx[-1]
    sub = _trim(P[i0:i1 + 1], d if i0 == 0 else 0.0, d if i1 == len(P) - 1 else 0.0)
    wsub = [w - 2 * d for w in W[i0:i1 + 1]]
    inner = _band(sub, wsub)
    b = B.plate(name + "_pnl", inner, z1 - 0.004, z1 + ph, mat, slope=0.012, bevel=0.008, tags=tags)
    return a, b


def _edge(P, W, side, off, width):
    """Faixa fina ao longo de uma borda da crista (side=+1 esquerda, -1 direita da linha central)."""
    n = len(P)
    Q = []
    for i in range(n):
        a, b = P[max(i - 1, 0)], P[min(i + 1, n - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        d = side * (W[i] / 2 + off)
        Q.append((P[i][0] + nx * d, P[i][1] + ny * d))
    return _band(Q, [width] * n)


def _mx(P):
    return [(-x, y) for x, y in P]


# ============================================================================ cabeca
# flanco esquerdo: corpo da onda (placa grande com gancho na frente) + duas cristas em faixa por cima,
# que correm pela borda externa e se enrolam para dentro ate o berco do cano
BODY = [(-1.00, -1.32), (-1.38, -1.32), (-1.64, -1.08), (-1.78, -0.80), (-1.72, -0.74), (-1.88, -0.46),
        (-1.90, 0.02), (-1.86, 0.36), (-1.84, 0.70), (-1.70, 0.58), (-1.62, 0.90), (-1.50, 1.16), (-1.36, 1.04),
        (-1.22, 1.30), (-1.00, 1.46), (-0.84, 1.53), (-0.74, 1.48), (-0.80, 1.30), (-0.94, 1.10), (-1.04, 0.86),
        (-1.08, 0.60), (-1.06, 0.30), (-1.00, -0.40)]
CREST2 = [(-1.66, -0.66), (-1.74, -0.30), (-1.73, 0.14), (-1.63, 0.54), (-1.45, 0.88), (-1.20, 1.16),
          (-0.96, 1.34)]
CW2 = [0.10, 0.22, 0.26, 0.28, 0.28, 0.24, 0.14]
CRESTM = [(-1.46, -1.00), (-1.51, -0.63), (-1.486, -0.278), (-1.437, 0.102), (-1.335, 0.429), (-1.199, 0.706),
          (-1.019, 0.967), (-0.855, 1.20)]
CWM = [0.08, 0.14, 0.18, 0.22, 0.24, 0.22, 0.18, 0.10]
CREST3 = [(-1.64, 0.16), (-1.60, 0.50), (-1.46, 0.84), (-1.24, 1.10), (-1.00, 1.28), (-0.82, 1.34)]
CW3 = [0.08, 0.16, 0.20, 0.20, 0.16, 0.08]


def head(M, T="head", phase=0.0):
    """Cabeca larga e baixa: nucleo escuro, escudos de onda nos flancos, espinha com direcao de tiro."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    # anel giratorio e nucleo escuro largo
    B.cyl("ring", 0, 0, 0.04, 1.40, 0.08, KM, axis="Z", verts=80, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, 1.33, 32, 0.1), 0.09, 0.022, S, tags=tags)
    core = [(-1.10, -1.32), (1.10, -1.32), (1.56, -0.92), (1.56, 0.50), (1.02, 1.08), (-1.02, 1.08),
            (-1.56, 0.50), (-1.56, -0.92)]
    B.plate("core", core, 0.06, 0.30, K, slope=0.05, tags=tags)

    # ---------------------------------------------------------------- escudos de onda (3 niveis por flanco)
    for side, sx in (("L", -1), ("R", 1)):
        f = (lambda p: p) if sx < 0 else _mx
        ba, bp = B.shard(f"wbody{side}", f(BODY), 0.26, 0.46, A, slope=0.09, groove=0.04, panel_h=0.03,
                         tags=tags)
        cma, cmp_ = _crest(f"crestm{side}", f(CRESTM), CWM, 0.38, 0.56, A, s=0.06, g=0.028, ph=0.022, tags=tags)
        c2a, c2p = _crest(f"crest2{side}", f(CREST2), CW2, 0.40, 0.66, A, s=0.07, g=0.03, ph=0.025, tags=tags)
        c3a, c3p = _crest(f"crest3{side}", f(CREST3), CW3, 0.62, 0.80, A, s=0.05, g=0.025, ph=0.02, tags=tags)
        # vaos escuros ao longo da borda interna de cada crista (separam os niveis da onda)
        for k, (P, W, tg, z) in enumerate(((CREST2, CW2, (ba, bp), 0.40), (CRESTM, CWM, (ba, bp), 0.40),
                                           (CREST3, CW3, (c2a, c2p), 0.60))):
            tr = _edge(f(P), W, sx, 0.025, 0.055)
            for j, t in enumerate(tg):
                if t is not None:
                    B.cut(t, [B.loft(f"tr{side}{k}{j}", tr, tr, z, 1.2, K, bevel=0.0)])
            B.loft(f"trbed{side}{k}", tr, tr, z - 0.004, z + 0.008, M["black"], bevel=0.0, tags=tags)
        # fenda com pips na parte traseira do corpo
        Mo.slot_with_pips(f"bslot{side}", sx * 1.22, -1.06, -0.62, 0.06, 0.49, 4, M, tags,
                          target=[ba, bp], depth=0.07)
        # fenda acesa ao longo da crista do meio (como a lamina do 76 mm)
        p, q = (sx * 1.495, -0.40), (sx * 1.45, 0.02)
        for k, t in enumerate((cma, cmp_)):
            if t is not None:
                B.cut(t, [_stroke(f"cmcut{side}{k}", p, q, 0.05, 0.50, 1.0, K)])
        _stroke(f"cmbed{side}", p, q, 0.05, 0.495, 0.51, M["black"], tags)
        _stroke(f"cmglow{side}", p, q, 0.016, 0.505, 0.515, M["glow_dim"], tags)
        # pistao ligando o gancho da onda ao berco
        B.cyl(f"piston{side}", sx * 0.86, 0.70, 0.42, 0.032, 0.36, S, axis="Y", verts=12, yaw=sx * 55, tags=tags)
        B.cyl(f"pistonb{side}", sx * 0.95, 0.64, 0.42, 0.048, 0.14, KM, axis="Y", verts=12, yaw=sx * 55, tags=tags)

    # ---------------------------------------------------------------- bercos dos canos (escuros)
    for sx in (-1, 1):
        cx = sx * 0.45
        crad = [(cx - 0.25, 0.36), (cx + 0.25, 0.36), (cx + 0.27, 0.50), (cx + 0.27, 1.20), (cx + 0.14, 1.42),
                (cx - 0.14, 1.42), (cx - 0.27, 1.20), (cx - 0.27, 0.50)]
        c = B.plate(f"cradle{sx}", crad, 0.26, 0.54, KM, slope=0.04, tags=tags)
        B.cut(c, [B.box(f"crad_c{sx}", cx, 1.10, 0.34, 0.66, 0.46, 0.9, K, bevel=0.0)])
        # toco da luva de recuo no berco: aparece com qualquer ordem de desenho
        B.cyl(f"stub{sx}", cx, 1.08, ZB, 0.15, 0.60, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
        for i in range(3):
            B.cyl(f"stubr{sx}{i}", cx, 0.86 + i * 0.18, ZB, 0.165, 0.035, K, axis="Y", verts=8, bevel=0.005,
                  tags=tags)
        for k in (-1, 1):
            B.cyl(f"recup{sx}{k}", cx + k * 0.215, 0.95, 0.55, 0.03, 0.60, S, axis="Y", verts=10, tags=tags)
        # culatra atras do berco
        B.box(f"breech{sx}", cx, 0.42, 0.34, 0.26, 0.40, 0.62, KM, bevel=0.012, tags=tags)
        B.box(f"breechr{sx}", cx, 0.50, 0.38, 0.045, 0.42, 0.64, S, bevel=0.008, tags=tags)
        B.box(f"breechs{sx}", cx, 0.38, 0.14, 0.09, 0.60, 0.625, M["black"], bevel=0.0, tags=tags)

    # regulador de espoleta entre os bercos (caixa escura com nervuras e luz fraca)
    B.plate("fuze", B.rpoly(0, 0.74, 0.26, 0.56, 0, chamfer=0.05), 0.28, 0.50, KM, slope=0.025, tags=tags)
    for i in range(3):
        B.box(f"fuzer{i}", 0, 0.56 + i * 0.09, 0.22, 0.03, 0.48, 0.53, S, bevel=0.006, tags=tags)
    B.box("fuzebed", 0, 0.92, 0.14, 0.05, 0.49, 0.505, M["black"], bevel=0.0, tags=tags)
    B.box("fuzeled", 0, 0.92, 0.09, 0.018, 0.50, 0.51, M["glow_dim"], bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- tremonhas de municao nos vaos
    for sx in (-1, 1):
        hx = sx * 0.70
        hop = B.plate(f"hopper{sx}", B.rpoly(hx, -0.36, 0.42, 1.06, 0, chamfer=0.06), 0.28, 0.56, KM, slope=0.03,
                      tags=tags)
        B.cut(hop, [B.box(f"hopc{sx}", hx, -0.34, 0.30, 0.86, 0.46, 0.9, K, bevel=0.0)])
        # granadas deitadas na bandeja (escada clara)
        for i in range(7):
            y = -0.72 + i * 0.12
            B.cyl(f"rnd{sx}{i}", hx, y, 0.47, 0.042, 0.24, S, axis="X", verts=8, bevel=0.004, tags=tags)
            B.cyl(f"rndt{sx}{i}", hx + sx * 0.13, y, 0.47, 0.034, 0.04, AM, axis="X", verts=8, bevel=0.003,
                  tags=tags)
        # trilhos guia
        for k in (-1, 1):
            B.box(f"hrail{sx}{k}", hx + k * 0.17, -0.34, 0.03, 0.90, 0.56, 0.60, S, bevel=0.006, tags=tags)
        # contador ambar num rebaixo atras da bandeja
        B.box(f"hcnt{sx}", hx, -0.84, 0.30, 0.07, 0.555, 0.57, M["black"], bevel=0.0, tags=tags)
        for i in range(4):
            B.box(f"hled{sx}{i}", hx - 0.105 + i * 0.07, -0.84, 0.04, 0.03, 0.565, 0.58,
                  M["glow"] if i < 3 else M["black"], bevel=0.0, tags=tags)
        # calha de alimentacao: tremonha -> culatra
        B.cyl(f"chute{sx}", sx * 0.58, 0.28, 0.46, 0.05, 0.30, KM, axis="Y", verts=8, yaw=sx * 20, tags=tags)
        for i in range(2):
            B.cyl(f"chuter{sx}{i}", sx * (0.60 - i * 0.04), 0.22 + i * 0.12, 0.46, 0.058, 0.025, S, axis="Y",
                  verts=8, yaw=sx * 20, tags=tags)

    # ---------------------------------------------------------------- espinha com direcao de tiro
    spine = [(-0.28, -1.02), (0.28, -1.02), (0.34, -0.92), (0.34, 0.06), (0.20, 0.40), (-0.20, 0.40),
             (-0.34, 0.06), (-0.34, -0.92)]
    sa, sp = B.shard("spine", spine, 0.30, 0.66, A, slope=0.08, groove=0.035, panel_h=0.025, tags=tags)
    sp2 = [(-0.19, -0.90), (0.19, -0.90), (0.22, -0.83), (0.22, -0.36), (0.15, -0.28), (-0.15, -0.28),
           (-0.22, -0.36), (-0.22, -0.83)]
    s2 = B.plate("spine2", sp2, 0.68, 0.76, A, slope=0.03, tags=tags)
    # onda gravada (emblema): rebaixo preto com canal fino aceso (fraco)
    wave_m = B.mat_glow("wave_glow", Mo.AMBER, 0.8)
    zig = [(-0.13, 0.0), (-0.065, 0.06), (0.0, 0.0), (0.065, 0.06), (0.13, 0.0)]
    k = 0
    for y0 in (-0.62, -0.76):
        pts = [(x, y + y0) for x, y in zig]
        B.cut(s2, [_stroke(f"emc{k}{i}", pts[i], pts[i + 1], 0.05, 0.73, 1.0, K) for i in range(4)])
        for i in range(4):
            _stroke(f"emb{k}{i}", pts[i], pts[i + 1], 0.05, 0.725, 0.735, M["black"], tags)
            _stroke(f"emg{k}{i}", pts[i], pts[i + 1], 0.016, 0.73, 0.736, wave_m, tags)
        k += 1
    # bloco de direcao de tiro: caixa facetada com lente redonda e fendas de telemetro
    dirb = [(-0.25, -0.20), (0.25, -0.20), (0.28, -0.12), (0.28, 0.14), (0.15, 0.34), (-0.15, 0.34),
            (-0.28, 0.14), (-0.28, -0.12)]
    da, dp = B.shard("director", dirb, 0.62, 0.84, A, slope=0.05, groove=0.025, panel_h=0.02, tags=tags)
    for k, t in enumerate((da, dp)):
        if t is not None:
            B.cut(t, [B.cyl(f"lens_c{k}", 0, 0.12, 0.95, 0.095, 0.30, K, axis="Z", verts=8, bevel=0.0)])
    B.cyl("lens_bed", 0, 0.12, 0.78, 0.095, 0.02, M["black"], axis="Z", verts=8, bevel=0.0, tags=tags)
    B.cyl("lens_ring", 0, 0.12, 0.80, 0.075, 0.03, S, axis="Z", verts=8, bevel=0.004, tags=tags)
    B.cyl("lens_eye", 0, 0.12, 0.81, 0.045, 0.03, M["lens"], axis="Z", verts=8, bevel=0.0, tags=tags)
    Mo.slot_with_pips("dslot", -0.10, -0.18, 0.18, 0.045, 0.86, 3, M, tags, target=[da, dp], depth=0.06,
                      vertical=False)

    # ---------------------------------------------------------------- baia de exaustao traseira
    B.box("vent_bay", 0, -1.21, 0.96, 0.18, 0.20, 0.34, M["black"], bevel=0.0, tags=tags)
    for i in range(4):
        B.box(f"louver{i}", 0, -1.28 + i * 0.045, 0.92, 0.02, 0.28, 0.35, KM, bevel=0.004, tags=tags)
    for i in range(6):
        B.box(f"vent_pip{i}", -0.375 + i * 0.15, -1.08, 0.06, 0.024, 0.30, 0.36, M["glow"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"module{sx}", sx * 0.80, -1.12, 0.22, 0.14, 0.28, 0.40, KM, bevel=0.01, tags=tags)
    B.bolts("bolt", [(x, -1.24) for x in (-0.86, -0.62, 0.62, 0.86)], 0.32, 0.024, S, tags=tags)
    check_meshes(T)


# ============================================================================ cano
def barrel(M, L=2.2, T="barrel", phase=0.0):
    """Cano de 57 mm com raiz (y=0) e boca (y=L), centrado em x=0, altura ZB."""
    tags = (T,)
    hot = (T, "hot")  # so abafador e colar da boca brilham de calor
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = ZB
    # luva de recuo escura com aros
    B.cyl("b_root", 0, 0.17, z, 0.17, 0.34, KM, axis="Y", verts=8, bevel=0.012, tags=tags)
    for i, y in enumerate((0.07, 0.25)):
        B.cyl(f"b_hoop{i}", 0, y, z, 0.182, 0.04, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("b_rootcap", 0, 0.355, z, 0.16, 0.04, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    # camisa de resfriamento clara, perfurada (duas colunas de furos escuros no topo)
    y0j, y1j = 0.37, 0.92
    jk = B.cyl("b_jacket", 0, (y0j + y1j) / 2, z, 0.145, y1j - y0j, A, axis="Y", verts=8, bevel=0.01, tags=tags)
    cuts = []
    for i in range(5):
        for k in (-1, 1):
            cuts.append(B.box(f"b_jh{i}{k}", k * 0.06, 0.45 + i * 0.10, 0.06, 0.045, z + 0.06, z + 0.3, K,
                              bevel=0.0))
    B.cut(jk, cuts)
    B.cyl("b_jcore", 0, (y0j + y1j) / 2, z, 0.10, y1j - y0j - 0.02, K, axis="Y", verts=8, bevel=0.0, tags=tags)
    B.cyl("b_collar0", 0, y1j, z, 0.155, 0.05, AM, axis="Y", verts=8, bevel=0.008, tags=tags)
    # tubo longo afunilado com canal escuro no topo
    y0, y1 = y1j, L - 0.50
    tb = B.cyl("b_tube", 0, (y0 + y1) / 2, z, 0.115, y1 - y0, A, axis="Y", verts=8, bevel=0.008, tags=tags,
               r2=0.098)
    B.cut(tb, [B.box("b_chc", 0, (y0 + y1) / 2, 0.04, y1 - y0 - 0.10, z + 0.07, z + 0.3, K, bevel=0.0)])
    B.box("b_chbed", 0, (y0 + y1) / 2, 0.04, y1 - y0 - 0.10, z + 0.05, z + 0.08, M["black"], bevel=0.0,
          tags=tags)
    B.cyl("b_collar1", 0, (y0 + y1) / 2, z, 0.122, 0.04, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("b_collar2", 0, y1 - 0.02, z, 0.13, 0.05, AM, axis="Y", verts=8, bevel=0.008, tags=hot)
    # abafador de chama multi-camara: cone claro facetado que abre para a frente, nariz em ponta de flecha,
    # 6 janelas transversais escuras (o nucleo escuro aparece no fundo de cada janela)
    ya, yb = L - 0.58, L
    B.cyl("b_hring", 0, ya - 0.01, z, 0.135, 0.04, S, axis="Y", verts=8, bevel=0.005, tags=hot)
    hid = [(-0.115, ya), (0.115, ya), (0.135, ya + 0.04), (0.19, yb - 0.17), (0.19, yb - 0.11), (0.10, yb),
           (-0.10, yb), (-0.19, yb - 0.11), (-0.19, yb - 0.17), (-0.135, ya + 0.04)]
    h = B.plate("b_hider", hid, z - 0.13, z + 0.13, A, slope=0.035, tags=hot)
    hc = [B.box(f"b_hp{i}", 0, ya + 0.075 + i * 0.065, 0.44, 0.03, z + 0.03, z + 0.3, K, bevel=0.0) for i in range(6)]
    hc.append(B.box("b_bore", 0, yb, 0.09, 0.08, z - 0.06, z + 0.3, K, bevel=0.0))
    B.cut(h, hc)
    core = B.offset_poly(hid, 0.035)
    B.loft("b_hider_core", core, core, z - 0.10, z + 0.034, K, bevel=0.0, tags=tags)
    check_meshes(T)


# ============================================================================ teto
def roof(M, T="roof"):
    """Teto 4x4: placas verdes, anel da torre; fileira de tras com 2 armarios de pentes nas pontas
    (janela com granadas e contador) e 2 escotilhas da tripulacao no meio."""
    tags = (T,)
    W, H = PART["size"]
    pv = PART["pivot"]
    rr = PART["ring_r"]
    green = B.mat_roof_green()
    AM, K, KM, S = M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    px, py = pv[0] - W / 2, H / 2 - pv[1]
    gap = 0.03
    B.box("deck_under", 0, 0, W, H, -0.05, 0.02, K, bevel=0.0, tags=tags)
    for tx in range(W):
        for ty in range(H):
            cx, cy = tx + 0.5 - W / 2, H / 2 - ty - 0.5
            poly = B.rpoly(cx, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
            _, pnl = B.shard(f"deck{tx}_{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02,
                             tags=tags)
            if (tx + ty) % 2 == 0 and pnl is not None and ty < H - 1:
                B.cut(pnl, [B.rbox(f"dl{tx}{ty}", cx + 0.18, cy - 0.18, 0.012, 0.5, 0.07, 0.2, K, rot=45,
                                   bevel=0.0)])
    # anel da torre (sem pintura)
    B.torus("ringbear", px, py, 0.08, rr + 0.02, 0.055, KM, tags=tags)
    B.cyl("ringhole", px, py, 0.05, rr - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(px, py, rr + 0.11, 36)
           if abs(x) < W / 2 - 0.08 and -H / 2 + 0.92 < y < H / 2 - 0.08]
    B.bolts("rb", pts, 0.1, 0.022, S, tags=tags)
    hy = -H / 2 + 0.5
    # armarios de pentes nas pontas
    for sx in (-1, 1):
        cx = sx * 1.5
        la, lp = B.shard(f"locker{sx}", B.rpoly(cx, hy, 0.76, 0.66, 0, chamfer=0.12), 0.05, 0.11, AM, slope=0.02,
                         groove=0.03, panel_h=0.015, tags=tags)
        win = B.rpoly(cx, hy + 0.05, 0.52, 0.34, 0, chamfer=0.05)
        for k, t in enumerate((la, lp)):
            if t is not None:
                B.cut(t, [B.loft(f"lwin{sx}{k}", win, win, 0.088, 0.4, K, bevel=0.0)])
        B.loft(f"lwinbed{sx}", win, win, 0.082, 0.092, M["black"], bevel=0.0, tags=tags)   # acima do conves verde
        for i in range(4):
            x = cx - 0.18 + i * 0.12
            B.cyl(f"lrnd{sx}{i}", x, hy + 0.03, 0.12, 0.045, 0.24, S, axis="Y", verts=8, bevel=0.004, tags=tags)
            B.cyl(f"lrndt{sx}{i}", x, hy + 0.18, 0.12, 0.045, 0.06, AM, axis="Y", verts=8, bevel=0.003, tags=tags,
                  r2=0.02)
        B.box(f"lcnt{sx}", cx, hy - 0.21, 0.26, 0.06, 0.10, 0.13, M["black"], bevel=0.0, tags=tags)
        for i in range(3):
            B.box(f"lled{sx}{i}", cx - 0.07 + i * 0.07, hy - 0.21, 0.04, 0.025, 0.12, 0.135, M["glow_dim"],
                  bevel=0.0, tags=tags)
        for k in (-1, 1):
            B.box(f"lhinge{sx}{k}", cx + k * 0.30, hy + 0.05, 0.035, 0.22, 0.10, 0.13, S, bevel=0.008, tags=tags)
    # escotilhas da tripulacao no meio
    for sx in (-1, 1):
        cx = sx * 0.5
        hatch = B.rpoly(cx, hy, 0.56, 0.56, 0, chamfer=0.12)
        B.plate(f"hatch{sx}", hatch, 0.06, 0.10, AM, slope=0.02, tags=tags)
        inner = B.offset_poly(hatch, 0.07)
        B.plate(f"hatchl{sx}", inner, 0.095, 0.12, AM, slope=0.012, bevel=0.006, tags=tags)
        B.box(f"hatch_h{sx}", cx, hy - 0.13, 0.22, 0.045, 0.12, 0.15, S, bevel=0.008, tags=tags)
        B.box(f"hatch_l{sx}", cx, hy + 0.20, 0.16, 0.024, 0.11, 0.125, M["glow_dim"], bevel=0.0, tags=tags)
    check_meshes(T)
