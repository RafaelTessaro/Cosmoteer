"""Bateria Flak Pesada ("Pororoca") - defesa 4x4 de canos duplos, mesma familia do 76 mm.

Montagem larga e baixa: nucleo escuro largo com escudos laterais em ondas (pororoca = a onda da
mare que sobe o Amazonas): tres niveis de placas curvas facetadas em cada flanco, empilhadas como a
crista de uma onda que quebra, cada uma terminando num labio que avanca ate o berco do cano e se
enrola para tras. Espinha central em seta com bloco de direcao de tiro (lente escura) e a onda gravada,
quebra-ondas em V entre os bercos, tremonhas de granadas com contador nos vaos, bercos escuros dos
canos e baia de exaustao traseira.
Canos: dois canos longos de 57 mm com luva de recuo escura (cobre todo o berco, serve para as duas
ordens de desenho), camisa de resfriamento clara com fendas transversais, tubo com canal escuro e
abafador de chama multi-camara claro em ponta de flecha (janelas transversais escuras).
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
        "length": 2.4,             # raiz -> boca (raiz escura de 0.82 fica dentro do berco)
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
ROOT_D = 0.82      # trecho escuro da raiz do cano (pivo 0.62 -> 1.44, passa da boca do berco em 1.42)


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


def _lines(targets, name, specs, zfloor, mat):
    """Linhas de painel recortadas em cada alvo ate zfloor (um jogo de cortadores por alvo, pois B.cut
    prende o cortador ao alvo): specs = [(x, y, comprimento, rotacao)]."""
    for k, t in enumerate(targets):
        if t is None:
            continue
        cuts = [B.rbox(f"{name}{k}_{i}", x, y, 0.016, ln, zfloor, zfloor + 0.8, mat, rot=r, bevel=0.0)
                for i, (x, y, ln, r) in enumerate(specs)]
        B.cut(t, cuts)


def _across(P, W, i, t=0.5, extra=0.04):
    """Linha transversal a faixa P entre os pontos i e i+1 (fracao t): (x, y, comprimento, rotacao)."""
    (ax, ay), (bx, by) = P[i], P[i + 1]
    x, y = ax + (bx - ax) * t, ay + (by - ay) * t
    w = W[i] + (W[i + 1] - W[i]) * t
    return (x, y, w + extra, math.degrees(math.atan2(by - ay, bx - ax)))


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


def _mxs(specs):
    """Espelha specs de linha (x, y, comprimento, rotacao) para o flanco direito."""
    return [(-x, y, ln, -r) for x, y, ln, r in specs]


# ============================================================================ cabeca
# flanco esquerdo: corpo da onda (placa grande com gancho na frente e cauda chanfrada em seta) + tres
# cristas em faixa por cima, que correm pela borda externa e avancam ate o berco do cano; as duas de
# cima terminam num labio que se enrola para tras (onda quebrando)
BODY = [(-1.00, -1.32), (-1.24, -1.32), (-1.78, -0.80), (-1.72, -0.74), (-1.88, -0.46),
        (-1.90, 0.02), (-1.86, 0.36), (-1.84, 0.70), (-1.70, 0.58), (-1.62, 0.90), (-1.50, 1.16), (-1.36, 1.04),
        (-1.22, 1.30), (-1.00, 1.46), (-0.84, 1.53), (-0.74, 1.48), (-0.80, 1.30), (-0.94, 1.10), (-1.04, 0.86),
        (-1.08, 0.60), (-1.06, 0.30), (-1.00, -0.40)]
CREST2 = [(-1.66, -0.66), (-1.74, -0.30), (-1.73, 0.14), (-1.63, 0.54), (-1.45, 0.88), (-1.20, 1.16),
          (-0.96, 1.37), (-0.82, 1.44)]
CW2 = [0.10, 0.22, 0.26, 0.28, 0.28, 0.24, 0.16, 0.10]
CRESTM = [(-1.44, -0.96), (-1.51, -0.63), (-1.486, -0.278), (-1.437, 0.102), (-1.335, 0.429), (-1.199, 0.706),
          (-1.019, 0.967), (-0.855, 1.20)]
CWM = [0.08, 0.14, 0.18, 0.22, 0.24, 0.22, 0.18, 0.10]
CREST3 = [(-1.64, 0.16), (-1.60, 0.50), (-1.46, 0.84), (-1.24, 1.10), (-1.00, 1.28), (-0.85, 1.34),
          (-0.77, 1.28)]
CW3 = [0.08, 0.17, 0.24, 0.24, 0.18, 0.12, 0.09]


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
        g = (lambda s: s) if sx < 0 else _mxs
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
        Mo.slot_with_pips(f"bslot{side}", sx * 1.22, -1.04, -0.62, 0.06, 0.49, 4, M, tags,
                          target=[ba, bp], depth=0.07)
        # linhas de painel no corpo (fundo 0.42: atravessa o painel e entra 0.04 na placa de baixo)
        _lines((ba, bp), f"bl{side}", g([(-1.27, -0.44, 0.20, 90), (-1.26, -0.12, 0.13, 90)]), 0.42, K)
        # segmentos transversais nas cristas: cada nivel da onda le como placas sobrepostas
        _lines((c2a, c2p), f"c2l{side}", g([_across(CREST2, CW2, 0, 0.75), _across(CREST2, CW2, 1, 0.70)]),
               0.60, K)
        _lines((cma, cmp_), f"cml{side}", g([_across(CRESTM, CWM, 0, 0.75), _across(CRESTM, CWM, 3, 0.55),
                                             _across(CRESTM, CWM, 5, 0.25)]), 0.50, K)
        _lines((c3a, c3p), f"c3l{side}", g([_across(CREST3, CW3, 2, 0.30)]), 0.74, K)
        # fenda acesa ao longo da crista do meio (como a lamina do 76 mm)
        p, q = (sx * 1.495, -0.40), (sx * 1.45, 0.02)
        for k, t in enumerate((cma, cmp_)):
            if t is not None:
                B.cut(t, [_stroke(f"cmcut{side}{k}", p, q, 0.05, 0.50, 1.0, K)])
        _stroke(f"cmbed{side}", p, q, 0.05, 0.495, 0.51, M["black"], tags)
        _stroke(f"cmglow{side}", p, q, 0.016, 0.505, 0.515, M["glow_dim"], tags)
        # pistao ligando o berco ao corpo da onda (as duas pontas presas em garfos escuros)
        B.cyl(f"piston{side}", sx * 0.94, 0.65, 0.42, 0.032, 0.54, S, axis="Y", verts=12, yaw=sx * 55, tags=tags)
        B.cyl(f"pistonb{side}", sx * 1.10, 0.53, 0.42, 0.048, 0.16, KM, axis="Y", verts=12, yaw=sx * 55, tags=tags)
        B.rbox(f"clevis{side}", sx * 0.75, 0.79, 0.10, 0.08, 0.34, 0.47, KM, rot=sx * 55, bevel=0.008, tags=tags)
        B.rbox(f"clevisb{side}", sx * 1.17, 0.48, 0.12, 0.09, 0.34, 0.47, KM, rot=sx * 55, bevel=0.008, tags=tags)

    # ---------------------------------------------------------------- bercos dos canos (escuros)
    for sx in (-1, 1):
        cx = sx * 0.45
        crad = [(cx - 0.25, 0.36), (cx + 0.25, 0.36), (cx + 0.27, 0.50), (cx + 0.27, 1.16), (cx + 0.15, 1.42),
                (cx - 0.15, 1.42), (cx - 0.27, 1.16), (cx - 0.27, 0.50)]
        c = B.plate(f"cradle{sx}", crad, 0.26, 0.54, KM, slope=0.04, tags=tags)
        B.cut(c, [B.box(f"crad_c{sx}", cx, 1.10, 0.34, 0.66, 0.46, 0.9, K, bevel=0.0)])
        # toco da luva de recuo no berco (mesmos aneis da raiz do cano): aparece com qualquer ordem de desenho
        B.cyl(f"stub{sx}", cx, 1.08, ZB, 0.15, 0.60, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
        for i, y in enumerate((0.91, 1.13)):
            B.cyl(f"stubr{sx}{i}", cx, y, ZB, 0.165, 0.035, K, axis="Y", verts=8, bevel=0.005, tags=tags)
        # labio de aco na boca do berco (marca a saida do cano)
        B.cyl(f"lip{sx}", cx, 1.40, ZB, 0.19, 0.05, S, axis="Y", verts=8, bevel=0.006, tags=tags)
        for k in (-1, 1):
            B.cyl(f"recup{sx}{k}", cx + k * 0.215, 0.92, 0.55, 0.03, 0.56, S, axis="Y", verts=10, tags=tags)
        # culatra atras do berco
        B.box(f"breech{sx}", cx, 0.42, 0.34, 0.26, 0.40, 0.62, KM, bevel=0.012, tags=tags)
        B.box(f"breechr{sx}", cx, 0.50, 0.38, 0.045, 0.42, 0.64, S, bevel=0.008, tags=tags)
        B.box(f"breechs{sx}", cx, 0.38, 0.14, 0.09, 0.60, 0.625, M["black"], bevel=0.0, tags=tags)

    # regulador de espoleta entre os bercos (caixa escura com nervuras) + quebra-ondas em V por cima
    B.plate("fuze", B.rpoly(0, 0.78, 0.26, 0.64, 0, chamfer=0.05), 0.28, 0.50, KM, slope=0.025, tags=tags)
    for i in range(3):
        B.box(f"fuzer{i}", 0, 0.54 + i * 0.07, 0.22, 0.03, 0.48, 0.53, S, bevel=0.006, tags=tags)
    brk = [(0.0, 1.16), (0.15, 0.97), (0.15, 0.82), (0.07, 0.76), (-0.07, 0.76), (-0.15, 0.82), (-0.15, 0.97)]
    wa, wp = B.shard("breakwater", brk, 0.46, 0.56, A, slope=0.035, groove=0.02, panel_h=0.02, tags=tags)
    vee = [(-0.07, 0.86), (0.0, 0.96), (0.07, 0.86)]
    for k, t in enumerate((wa, wp)):
        if t is not None:
            B.cut(t, [_stroke(f"bwc{k}{i}", vee[i], vee[i + 1], 0.04, 0.515, 1.0, K) for i in range(2)])
    for i in range(2):
        _stroke(f"bwbed{i}", vee[i], vee[i + 1], 0.04, 0.51, 0.52, M["black"], tags)
        _stroke(f"bwglow{i}", vee[i], vee[i + 1], 0.014, 0.515, 0.525, M["glow_dim"], tags)

    # ---------------------------------------------------------------- tremonhas de granadas nos vaos
    for sx in (-1, 1):
        hx = sx * 0.70
        hop = B.plate(f"hopper{sx}", B.rpoly(hx, -0.36, 0.42, 1.06, 0, chamfer=0.06), 0.28, 0.56, KM, slope=0.03,
                      tags=tags)
        B.cut(hop, [B.box(f"hopc{sx}", hx, -0.34, 0.30, 0.86, 0.46, 0.9, K, bevel=0.0)])
        # granadas em 2 colunas, ogiva para a frente (sentido da alimentacao)
        for c in (-1, 1):
            for i in range(3):
                x, y = hx + c * 0.074, -0.66 + i * 0.28
                B.cyl(f"rndb{sx}{c}{i}", x, y - 0.075, 0.47, 0.06, 0.025, KM, axis="Y", verts=8, bevel=0.003,
                      tags=tags)
                B.cyl(f"rnd{sx}{c}{i}", x, y, 0.47, 0.056, 0.15, S, axis="Y", verts=8, bevel=0.004, tags=tags)
                B.cyl(f"rndt{sx}{c}{i}", x, y + 0.12, 0.47, 0.056, 0.09, AM, axis="Y", verts=8, bevel=0.003,
                      tags=tags, r2=0.016)
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

    # ---------------------------------------------------------------- espinha em seta com direcao de tiro
    spine = [(-0.28, -1.02), (0.28, -1.02), (0.34, -0.92), (0.34, 0.04), (0.12, 0.46), (-0.12, 0.46),
             (-0.34, 0.04), (-0.34, -0.92)]
    B.shard("spine", spine, 0.30, 0.66, A, slope=0.08, groove=0.035, panel_h=0.025, tags=tags)
    sp2 = [(-0.19, -0.90), (0.19, -0.90), (0.22, -0.83), (0.22, -0.40), (0.08, -0.28), (-0.08, -0.28),
           (-0.22, -0.40), (-0.22, -0.83)]
    s2 = B.plate("spine2", sp2, 0.68, 0.76, A, slope=0.03, tags=tags)
    # onda gravada (emblema): crista que sobe e quebra enrolando + linha d'agua; rebaixo preto com fio aceso
    wave_m = B.mat_glow("wave_glow", Mo.AMBER, 0.8)
    wave = [(-0.12, -0.745), (-0.055, -0.71), (-0.01, -0.64), (0.02, -0.565), (0.075, -0.52), (0.12, -0.555),
            (0.12, -0.62), (0.075, -0.645), (0.05, -0.605)]
    segs = [(wave[i], wave[i + 1]) for i in range(len(wave) - 1)] + [((-0.12, -0.81), (0.12, -0.81))]
    B.cut(s2, [_stroke(f"emc{i}", p, q, 0.044, 0.72, 1.0, K) for i, (p, q) in enumerate(segs)] +
          [B.rbox("s2l", 0, -0.44, 0.30, 0.016, 0.72, 1.0, K, bevel=0.0)])
    for i, (p, q) in enumerate(segs):
        _stroke(f"emb{i}", p, q, 0.044, 0.715, 0.725, M["black"], tags)
        _stroke(f"emg{i}", p, q, 0.016, 0.72, 0.728, wave_m, tags)
    # bloco de direcao de tiro em seta: janela em ponta (como o sensor do 76 mm) com lente de vidro escuro
    # e um ponto aceso pequeno; fenda de pips atras
    dirb = [(-0.25, -0.20), (0.25, -0.20), (0.28, -0.12), (0.28, 0.06), (0.06, 0.38), (-0.06, 0.38),
            (-0.28, 0.06), (-0.28, -0.12)]
    da, dp = B.shard("director", dirb, 0.62, 0.84, A, slope=0.05, groove=0.025, panel_h=0.02, tags=tags)
    win = [(-0.10, 0.03), (0.10, 0.03), (0.10, 0.13), (0.035, 0.23), (-0.035, 0.23), (-0.10, 0.13)]
    for k, t in enumerate((da, dp)):
        if t is not None:
            B.cut(t, [B.loft(f"lens_c{k}", win, win, 0.80, 1.1, K, bevel=0.0)])
    B.loft("lens_bed", win, win, 0.795, 0.805, M["black"], bevel=0.0, tags=tags)
    B.cyl("lens_ring", 0, 0.11, 0.815, 0.062, 0.03, KM, axis="Z", verts=8, bevel=0.004, tags=tags)
    B.cyl("lens_eye", 0, 0.11, 0.825, 0.046, 0.03, M["black"], axis="Z", verts=16, bevel=0.0, tags=tags)
    B.cyl("lens_dot", 0, 0.11, 0.838, 0.018, 0.006, M["lens"], axis="Z", verts=12, bevel=0.0, tags=tags)
    Mo.slot_with_pips("dslot", -0.07, -0.18, 0.18, 0.045, 0.86, 3, M, tags, target=[da, dp], depth=0.06,
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
def barrel(M, L=2.4, T="barrel", phase=0.0):
    """Cano de 57 mm com raiz (y=0) e boca (y=L), centrado em x=0, altura ZB."""
    tags = (T,)
    hot = (T, "hot")  # so abafador e colar da boca brilham de calor
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = ZB
    # luva de recuo escura com aros: cobre todo o trecho dentro do berco (escuro nas duas ordens de desenho)
    yr = ROOT_D - 0.02
    B.cyl("b_root", 0, yr / 2, z, 0.17, yr, KM, axis="Y", verts=8, bevel=0.012, tags=tags)
    for i, y in enumerate((0.07, 0.29, 0.51)):
        B.cyl(f"b_hoop{i}", 0, y, z, 0.182, 0.04, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("b_rootcap", 0, ROOT_D - 0.02, z, 0.165, 0.04, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    # camisa de resfriamento clara com fendas transversais (brasa fraca no fundo, como o 76 mm)
    y0j, y1j = ROOT_D + 0.02, 1.30
    # sem bisel: o bisel reaplicado depois das fendas gera uma rampa diagonal quebrada na faceta esquerda
    jk = B.cyl("b_jacket", 0, (y0j + y1j) / 2, z, 0.145, y1j - y0j, A, axis="Y", verts=8, bevel=0.0, tags=tags)
    ys = [0.93 + i * 0.10 for i in range(4)]
    B.cut(jk, [B.box(f"b_js{i}", 0, y, 0.17, 0.045, z + 0.08, z + 0.3, K, bevel=0.0) for i, y in enumerate(ys)])
    for i, y in enumerate(ys):
        B.box(f"b_heat{i}", 0, y, 0.165, 0.042, z + 0.072, z + 0.086, M["ember"], bevel=0.0, tags=tags)
    B.cyl("b_collar0", 0, y1j, z, 0.155, 0.05, AM, axis="Y", verts=8, bevel=0.008, tags=tags)
    # tubo longo afunilado com canal escuro no topo
    y0, y1 = y1j, L - 0.50
    tb = B.cyl("b_tube", 0, (y0 + y1) / 2, z, 0.115, y1 - y0, A, axis="Y", verts=8, bevel=0.008, tags=tags,
               r2=0.10)
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
    # escotilhas da tripulacao no meio (luz num rebaixo preto)
    for sx in (-1, 1):
        cx = sx * 0.5
        hatch = B.rpoly(cx, hy, 0.56, 0.56, 0, chamfer=0.12)
        B.plate(f"hatch{sx}", hatch, 0.06, 0.10, AM, slope=0.02, tags=tags)
        inner = B.offset_poly(hatch, 0.07)
        hl = B.plate(f"hatchl{sx}", inner, 0.095, 0.12, AM, slope=0.012, bevel=0.006, tags=tags)
        B.box(f"hatch_h{sx}", cx, hy - 0.13, 0.22, 0.045, 0.12, 0.15, S, bevel=0.008, tags=tags)
        B.cut(hl, [B.box(f"hatch_lc{sx}", cx, hy + 0.20, 0.20, 0.05, 0.105, 0.3, K, bevel=0.0)])
        B.box(f"hatch_lb{sx}", cx, hy + 0.20, 0.20, 0.05, 0.10, 0.108, M["black"], bevel=0.0, tags=tags)
        B.box(f"hatch_l{sx}", cx, hy + 0.20, 0.14, 0.022, 0.105, 0.114, M["glow_dim"], bevel=0.0, tags=tags)
    check_meshes(T)


# ============================================================================ piso
def floor(M, T="floor"):
    """Piso: o padrao (anel, estantes e postos da tripulacao) + estantes de granadas e trilhos de
    alimentacao nos 4 cantos fora do anel."""
    from bsgen.common import crew_positions
    tags = (T,)
    W, H = PART["size"]
    pv = PART["pivot"]
    crew = crew_positions(W, H, 4, pv)
    Mo.hull_floor(M, W, H, pv, PART["ring_r"], crew, T)
    AM, K, KM, S = M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    # cantos da frente: estante com 4 granadas (ogiva para a frente) e luz de estoque
    for sx in (-1, 1):
        cx, cy = sx * 1.50, 1.50
        B.box(f"fr_rack{sx}", cx, cy, 0.74, 0.70, 0.0, 0.08, AM, bevel=0.012, tags=tags)
        B.box(f"fr_tray{sx}", cx, cy + 0.02, 0.60, 0.48, 0.06, 0.10, K, bevel=0.0, tags=tags)
        for i in range(4):
            x = cx - 0.21 + i * 0.14
            B.cyl(f"fr_rnd{sx}{i}", x, cy - 0.04, 0.15, 0.055, 0.26, S, axis="Y", verts=8, bevel=0.004, tags=tags)
            B.cyl(f"fr_rndt{sx}{i}", x, cy + 0.14, 0.15, 0.055, 0.10, AM, axis="Y", verts=8, bevel=0.003,
                  tags=tags, r2=0.016)
        B.box(f"fr_led{sx}", cx, cy - 0.28, 0.30, 0.035, 0.08, 0.10, M["glow_dim"], bevel=0.0, tags=tags)
    # laterais do meio: caixas de espoletas com contador
    for sx in (-1, 1):
        cx, cy = sx * 1.72, -0.20
        B.box(f"fz_box{sx}", cx, cy, 0.40, 0.90, 0.0, 0.12, KM, bevel=0.012, tags=tags)
        for i in range(4):
            B.box(f"fz_cell{sx}{i}", cx, cy - 0.30 + i * 0.20, 0.30, 0.14, 0.10, 0.15, AM, bevel=0.01, tags=tags)
            B.box(f"fz_led{sx}{i}", cx, cy - 0.30 + i * 0.20, 0.14, 0.03, 0.15, 0.165,
                  M["glow_dim"] if i < 3 else K, bevel=0.0, tags=tags)
