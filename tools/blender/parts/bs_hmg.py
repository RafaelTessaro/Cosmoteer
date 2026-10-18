"""Metralhadora Pesada de Conves ("Manganga") - torre compacta de 1x2 com canos gemeos, familia do 76 mm.

Vista de cima le como a mamangava (abelha carpinteira): escudo de canhao chanfrado de frente reta (a "cabeca"),
com duas canhoneiras escuras onde entram os canos gemeos e uma alca de mira em ponta de flecha no nariz central;
duas mandibulas (laminas) nos cantos da frente que passam da frente do escudo e fecham em ponta sobre as raizes dos
canos, com o "olho" (fenda de luz fraca num modulo escuro) no vao entre o escudo e a mandibula; caixa de cinta clara
(o "torax") com duas janelas por onde a cinta de cartuchos de latao corre ate as culatras sob o escudo (contador
ambar na espinha da caixa); duas asas curtas facetadas com degrau, varridas para tras, com fenda de pips e nervura;
abdomen curto em faixas em chevron separadas por sulcos escuros (as listras) e ferrao em ponta, com a baia de
exaustao (persiana e 3 pips) no sulco antes do ferrao. Em repouso nada passa da largura da peca de 1 tile (so as
pontas das mandibulas, raio ~0.6, sobram um pouco quando a torre gira). Canos: culatra escura, camisa escura com fendas e brasa fraca, luva clara com canal e colares,
freio leve facetado em ponta de flecha com fendas transversais escuras. Recuo alternado.
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_hmg",
    "kind": "gun",
    "size": [1, 2],
    "pivot": [0.5, 0.58],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 1.16,            # lado do quadrado do sprite da torre (cabeca de +0.50 a -0.55)
    "ring_r": 0.40,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "collider": 0.48,
    "barrels": {
        "ys": [-0.14, 0.14],       # canos gemeos lado a lado (sprites de 0.26 sem sobrepor)
        "root": 0.30,              # pivo -> raiz do cano (a culatra escura comeca 0.035 a frente, na canhoneira)
        "length": 1.10,            # raiz -> boca
        "width": 0.26,             # largura do sprite de cada cano (cabe o freio; espacamento 0.28 sem sobrepor)
        "pad": 0.06,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.06, 0.04, 0.02, 0.008],
        "heat": [0.45, 0.28, 0.14, 0.05],   # calor leve so no fundo das fendas do freio e no colar da boca
        "interval": 0.05,
    },
    "lights": [                    # luzes dinamicas em coordenadas da cabeca
        {"at": [0.0, -0.46], "size": 0.6, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "alternate",
}

RING_R = PART["ring_r"]
YS = PART["barrels"]["ys"]
ZB = 0.44                          # altura do eixo dos canos


def side(poly, sx):
    return poly if sx > 0 else Mo.mirror(poly)


def brass():
    """Latao dos cartuchos (so na cinta de municao)."""
    return B.mat_metal("bs_brass", (0.56, 0.33, 0.075), rough=0.30, metal=1.0)


# ============================================================================ planta (cabeca)
# nucleo escuro (octogono chanfrado; a frente vai ate as raizes dos canos)
CORE = [(-0.30, -0.45), (0.30, -0.45), (0.45, -0.30), (0.47, 0.28), (0.29, 0.46), (-0.29, 0.46), (-0.47, 0.28),
        (-0.45, -0.30)]
# escudo: frente reta entre os canos, bochechas em chanfro de 45 graus recuadas (o vao e das mandibulas)
SHIELD = [(-0.32, 0.18), (0.32, 0.18), (0.355, 0.205), (0.205, 0.355), (0.19, 0.455), (-0.19, 0.455),
          (-0.205, 0.355), (-0.355, 0.205)]
SHIELD_Z = (0.26, 0.56)
SHIELD_SLOPE = 0.025              # maior que isso as arestas curtas do canto de tras se invertem (safe_offset cortava)
NOTCH_W, NOTCH_Y0 = 0.16, 0.27     # canhoneiras (largura, fundo)
# mandibula direita: ombro no canto do escudo (x <= 0.495, dentro da peca de 1 tile), aresta externa facetada e
# ponta afiada que avanca alem do escudo e fecha sobre a raiz do cano
BLADE = [(0.42, 0.21), (0.49, 0.19), (0.495, 0.25), (0.44, 0.35), (0.35, 0.44), (0.30, 0.525), (0.27, 0.515),
         (0.25, 0.47), (0.255, 0.375)]
BLADE_Z = (0.30, 0.50)
# caixa de cinta (torax)
BOX = [(-0.19, -0.23), (0.19, -0.23), (0.23, -0.19), (0.23, 0.03), (0.19, 0.07), (-0.19, 0.07), (-0.23, 0.03),
       (-0.23, -0.19)]
BOX_Z = (0.24, 0.46)
WIN_X, WIN_W, WIN_Y0 = 0.11, 0.12, -0.15    # janelas da cinta
# asa direita: facetas retas, degrau na aresta externa e na borda de fuga interna, traseira chanfrada
WING = [(0.29, 0.13), (0.40, 0.13), (0.49, 0.04), (0.49, -0.12), (0.455, -0.155), (0.455, -0.30), (0.39, -0.39),
        (0.335, -0.39), (0.32, -0.30), (0.285, -0.24), (0.285, -0.04)]
WING_Z = (0.22, 0.44)
WING_SLOPE = 0.035
# abdomen: meia largura por y (de frente para tras) e segmentos telescopicos (fundos o bastante para o chanfro
# de ~0.02 sobreviver ao safe_offset)
ABD_W = [(-0.25, 0.20), (-0.30, 0.215), (-0.38, 0.19), (-0.46, 0.13), (-0.53, 0.05)]
ABD_SEG = [(-0.245, -0.32, 0.44, 0.025), (-0.345, -0.405, 0.41, 0.02)]   # (frente, tras, topo, chanfro)
# ferrao: frente reta (o sulco antes dele vira cunha, com a baia de exaustao) e ponta de flecha para tras
YTF = -0.48                        # frente do ferrao
TAIL = [(0.0, -0.552), (0.06, -0.537), (0.135, YTF), (-0.135, YTF), (-0.06, -0.537)]
TAIL_Z = 0.38
ABD_V = 0.03                       # flecha do chevron de cada segmento (centro mais atras)


def abd_w(y):
    """Meia largura do abdomen em y (interpolacao linear)."""
    for (y0, w0), (y1, w1) in zip(ABD_W, ABD_W[1:]):
        if y1 <= y <= y0:
            t = (y0 - y) / (y0 - y1)
            return w0 + (w1 - w0) * t
    return ABD_W[0][1] if y > ABD_W[0][0] else ABD_W[-1][1]


def abd_seg(ya, yb, ch=0.02, v=ABD_V):
    """Segmento do abdomen entre ya (frente) e yb (tras): faixa em chevron rasa apontando para tras, com a ponta
    lateral facetada (sem chanfros curtos, que limitavam o chanfro da placa a ~0.015)."""
    wa, wb = abd_w(ya), abd_w(yb)
    right = [(wb - ch, yb), (max(wa, wb), (ya + yb) / 2), (wa - ch, ya)]
    return [(0.0, yb - v)] + right + [(0.0, ya - v)] + [(-x, y) for x, y in reversed(right)]


def dim_pips(T, prefix, M):
    """Troca os pips de uma fenda para a luz fraca (orcamento de brilho)."""
    for o in [o for o in B.objects_with(T) if o.name.startswith(prefix)]:
        o.data.materials[0] = M["glow_dim"]


# ============================================================================ cabeca
def head(M, T="head", phase=0.0):
    """Cabeca: escudo com canhoneiras, mandibulas, caixa de cinta com cinta de latao, asas e abdomen listrado."""
    tags = (T,)
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    BR = brass()

    # anel giratorio e nucleo escuro
    B.cyl("ring", 0, 0, 0.04, 0.47, 0.08, KM, axis="Z", verts=64, bevel=0.01, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(0, 0, 0.455, 16, math.pi / 16) if y < 0.1]
    B.bolts("ringbolt", pts, 0.09, 0.016, S, tags=tags)
    B.plate("core", CORE, 0.06, 0.26, K, slope=0.04, tags=tags)

    # ---------------------------------------------------------------- escudo (cabeca da abelha)
    z0, z1 = SHIELD_Z
    # placa do escudo sem painel automatico: as canhoneiras comiam todo o painel interno e a travessa (y 0.18..0.27)
    # ficava lisa; o painel da travessa e desenhado a mao (bisel duplo, STYLE 9)
    sh = B.plate("shield", SHIELD, z0, z1, A, slope=SHIELD_SLOPE, tags=tags)
    for i, y in enumerate(YS):
        B.cut(sh, [B.box(f"notch{i}", y, (NOTCH_Y0 + 0.62) / 2, NOTCH_W, 0.62 - NOTCH_Y0, 0.20, 0.95, K,
                         bevel=0.0)])
        # mantelete escuro dentro da canhoneira, com colar de aco na boca
        B.box(f"mant{i}", y, (NOTCH_Y0 + 0.47) / 2, NOTCH_W - 0.03, 0.47 - NOTCH_Y0, 0.24, 0.40, KM, bevel=0.01,
              tags=tags)
        B.cyl(f"mcollar{i}", y, 0.455, ZB, 0.078, 0.04, KM, axis="Y", verts=8, bevel=0.006, tags=tags)
        B.cyl(f"mcring{i}", y, 0.478, ZB, 0.074, 0.012, S, axis="Y", verts=8, bevel=0.003, tags=tags)
    # painel elevado em cada metade da travessa (margem ~0.015 da borda de tras do topo, da canhoneira e do
    # chanfro da bochecha; ~0.02 da base da alca de mira)
    for sx in (-1, 1):
        B.plate(f"shpnl{sx}", side([(0.075, 0.219), (0.272, 0.219), (0.237, 0.255), (0.075, 0.255)], sx),
                z1 - 0.004, z1 + 0.04, A, slope=0.011, bevel=0.006, tags=tags)
    zt = z1 + 0.035                                   # altura de referencia da alca de mira (topo dos paineis)
    # alca de mira: aleta em ponta de flecha no nariz central, desce pelo chanfro ate a borda da frente
    hb = [(-0.05, 0.215), (0.05, 0.215), (0.056, 0.30), (0.046, 0.42), (0.0, 0.478), (-0.046, 0.42), (-0.056, 0.30)]
    ht = [(-0.042, 0.222), (0.042, 0.222), (0.047, 0.30), (0.036, 0.375), (0.0, 0.412), (-0.036, 0.375),
          (-0.047, 0.30)]
    hd = B.loft("hood", hb, ht, 0.30, zt + 0.06, A, bevel=0.006, tags=tags)
    # sensor: fenda horizontal num recesso escuro (como o sensor do 76 mm), lente fraca
    B.cut(hd, [B.box("hood_cut", 0, 0.335, 0.056, 0.026, zt + 0.02, 1.2, K, bevel=0.0)])
    B.box("hood_bed", 0, 0.335, 0.056, 0.026, zt + 0.012, zt + 0.022, M["black"], bevel=0.0, tags=tags)
    B.box("hood_lens", 0, 0.335, 0.040, 0.009, zt + 0.02, zt + 0.028, M["glow_dim"], bevel=0.0, tags=tags)
    B.box("hood_rib", 0, 0.262, 0.012, 0.05, zt + 0.055, zt + 0.07, K, bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- mandibulas (laminas que fecham nos canos)
    bz0, bz1 = BLADE_Z
    for sx in (-1, 1):
        # chanfro e sulco estreitos: a lamina tem ~0.11 de largura (raio maximo 0.56) e ainda ganha painel
        B.shard(f"blade{sx}", side(BLADE, sx), bz0, bz1, A, slope=0.02, groove=0.012, panel_h=0.025, tags=tags)
        # olho: modulo escuro no vao entre o escudo e a mandibula, com fenda de luz fraca
        ex, ey = sx * 0.325, 0.27
        pod = B.rbox(f"eye{sx}", ex, ey, 0.115, 0.042, 0.24, 0.40, KM, rot=sx * -45, bevel=0.008, tags=tags)
        B.cut(pod, [B.rbox(f"eyec{sx}", ex, ey, 0.085, 0.018, 0.37, 0.6, K, rot=sx * -45, bevel=0.0)])
        B.rbox(f"eyebed{sx}", ex, ey, 0.085, 0.018, 0.36, 0.371, M["black"], rot=sx * -45, bevel=0.0, tags=tags)
        B.rbox(f"eyeled{sx}", ex, ey, 0.062, 0.008, 0.37, 0.378, M["glow_dim"], rot=sx * -45, bevel=0.0, tags=tags)
        # pistao no vao entre a raiz da asa e o ombro da mandibula
        B.cyl(f"piston{sx}", sx * 0.432, 0.16, 0.33, 0.018, 0.11, S, axis="Y", verts=10, yaw=sx * -8, tags=tags)
        B.cyl(f"pistonb{sx}", sx * 0.427, 0.118, 0.33, 0.026, 0.05, KM, axis="Y", verts=10, yaw=sx * -8, tags=tags)

    # ---------------------------------------------------------------- caixa de cinta (torax) com a cinta de latao
    cz0, cz1 = BOX_Z
    bx, bpn = B.shard("box", BOX, cz0, cz1, A, slope=0.05, groove=0.025, panel_h=0.03, tags=tags)
    zf = 0.37                                  # fundo das janelas
    for sx in (-1, 1):
        # no painel a janela vai ate atras da borda dele (sem tira fina atras da janela, que estraga o bisel)
        for t, yw in ((bx, WIN_Y0), (bpn, WIN_Y0 - 0.03)):
            if t is not None:
                B.cut(t, [B.box(f"win{sx}{t.name}", sx * WIN_X, (yw + 0.14) / 2, WIN_W, 0.14 - yw, zf,
                                0.95, K, bevel=0.0)])
        B.box(f"win_bed{sx}", sx * WIN_X, (WIN_Y0 + 0.07) / 2, WIN_W, 0.07 - WIN_Y0, zf - 0.012, zf, M["black"],
              bevel=0.0, tags=tags)
        # bandeja de alimentacao no vao entre a caixa e o escudo
        B.box(f"tray{sx}", sx * WIN_X, 0.13, WIN_W - 0.01, 0.13, 0.24, zf, KM, bevel=0.008, tags=tags)
        B.box(f"trayr{sx}", sx * (WIN_X + WIN_W / 2 - 0.004), 0.13, 0.012, 0.13, zf, zf + 0.035, S, bevel=0.003,
              tags=tags)
        # cinta: cartuchos deitados (eixo x) com ponta de aco para fora, passo 0.032
        n = 0
        y = WIN_Y0 + 0.022
        while y < 0.20:
            cx = sx * WIN_X
            B.cyl(f"cart{sx}_{n}", cx - sx * 0.008, y, zf + 0.022, 0.0135, 0.074, BR, axis="X", verts=8, bevel=0.003,
                  tags=tags)
            # ponta afinando para fora (o cone do eixo X vai de -x para +x)
            r_in, r_out = (0.011, 0.004) if sx > 0 else (0.004, 0.011)
            B.cyl(f"tip{sx}_{n}", cx + sx * 0.040, y, zf + 0.022, r_in, 0.022, S, axis="X", verts=8, bevel=0.0,
                  tags=tags, r2=r_out)
            n += 1
            y += 0.032
    # espinha da caixa entre as janelas: o painel recua (degrau) e o contador de municao (3 pips) fica na base
    if bpn is not None:
        B.cut(bpn, [B.box("spine_c", 0, -0.0525, 0.12, 0.125, 0.40, 0.95, K, bevel=0.0)])
    Mo.slot_with_pips("cnt", 0, -0.108, -0.022, 0.03, cz1 + 0.03, 3, M, tags, target=[bx], depth=0.08)
    dim_pips(T, "cnt_pip", M)
    # dobradica da tampa apoiada na face de cima da caixa (quebra transversal atras das janelas)
    B.box("lidhinge", 0, -0.165, 0.26, 0.022, cz1 - 0.005, cz1 + 0.03, S, bevel=0.006, tags=tags)

    # ---------------------------------------------------------------- asas curtas
    wz0, wz1 = WING_Z
    for sx in (-1, 1):
        wa, wpn = B.shard(f"wing{sx}", side(WING, sx), wz0, wz1, A, slope=WING_SLOPE, groove=0.02, panel_h=0.03,
                          tags=tags)
        # nervura e fenda de pips
        if wpn is not None:
            B.cut(wpn, [B.rbox(f"vein{sx}", sx * 0.375, 0.005, 0.016, 0.17, wz1 - 0.05, 0.95, K, rot=sx * 12,
                               bevel=0.0)])
        Mo.slot_with_pips(f"wslot{sx}", sx * 0.375, -0.20, -0.09, 0.026, wz1 + 0.03, 2, M, tags, target=[wa, wpn],
                          depth=0.09)
        dim_pips(T, f"wslot{sx}_pip", M)

    # ---------------------------------------------------------------- abdomen listrado (segmentos + sulcos)
    for k, (ya, yb, zz, sl) in enumerate(ABD_SEG):
        B.plate(f"abd{k}", abd_seg(ya, yb), 0.22, zz, A, slope=sl, tags=tags)
    B.plate("tail", TAIL, 0.22, TAIL_Z, A, slope=0.02, tags=tags)
    # baia de exaustao no sulco em cunha antes do ferrao: fundo preto, 3 pips e uma persiana de aco atras deles
    yb2, ch = ABD_SEG[1][1], 0.02
    bed = [(0.0, yb2 - ABD_V - 0.004), (abd_w(yb2) - 0.01, yb2 - 0.004), (0.13, YTF - 0.004), (-0.13, YTF - 0.004),
           (-(abd_w(yb2) - 0.01), yb2 - 0.004)]
    B.loft("vent_bed", bed, bed, 0.24, 0.265, M["black"], bevel=0.0, tags=tags)
    for i, x in enumerate((-0.07, 0.0, 0.07)):
        yback = yb2 - ABD_V * (1 - abs(x) / (abd_w(yb2) - ch))   # borda de tras do 2o segmento em x
        B.rbox(f"vent_pip{i}", x, yback - 0.011, 0.034, 0.012, 0.265, 0.277, M["glow"],
               rot=math.copysign(6, x) if x else 0, bevel=0.0, tags=tags)
    B.box("louver", 0, YTF + 0.012, 0.22, 0.008, 0.255, 0.29, S, bevel=0.002, tags=tags)


# ============================================================================ cano
def barrel(M, L=1.10, T="barrel", phase=0.0):
    """Um cano de metralhadora pesada: raiz em y=0, boca em y=L, centrado em x=0."""
    tags = (T,)
    hot = (T, "hot")
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = ZB
    # culatra escura (comeca 0.035 a frente da raiz: no recuo maximo ainda fica dentro da canhoneira escura)
    B.cyl("b_root", 0, 0.08, z, 0.068, 0.09, KM, axis="Y", verts=8, bevel=0.008, tags=tags)
    B.cyl("b_rootring", 0, 0.125, z, 0.066, 0.02, S, axis="Y", verts=8, bevel=0.004, tags=tags)
    # camisa escura com fendas transversais e brasa fraca
    y0j, y1j = 0.135, 0.40
    jk = B.cyl("b_jacket", 0, (y0j + y1j) / 2, z, 0.062, y1j - y0j, KM, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cut(jk, [B.box(f"b_jc{i}", 0, 0.20 + i * 0.07, 0.14, 0.03, z + 0.025, z + 0.2, K, bevel=0.0) for i in range(3)])
    B.box("b_heat", 0, (y0j + y1j) / 2, 0.022, y1j - y0j - 0.08, z + 0.018, z + 0.026, M["ember"], bevel=0.0,
          tags=tags)
    for i, y in enumerate((y0j + 0.015, y1j - 0.015)):
        fn = B.cyl(f"b_fin{i}", 0, y, z, 0.068, 0.025, AM, axis="Y", verts=8, bevel=0.004, tags=tags)
        B.cut(fn, [B.box(f"b_finc{i}", 0, y, 0.018, 0.06, z + 0.04, z + 0.2, K, bevel=0.0)])
    # luva clara facetada com canal escuro e colares
    y0, y1 = y1j, L - 0.24
    sl = B.cyl("b_sleeve", 0, (y0 + y1) / 2, z, 0.058, y1 - y0, A, axis="Y", verts=8, bevel=0.006, tags=tags,
               r2=0.052)
    B.cut(sl, [B.box("b_chc", 0, (y0 + y1) / 2, 0.018, y1 - y0 - 0.06, z + 0.022, z + 0.2, K, bevel=0.0)])
    B.box("b_chbed", 0, (y0 + y1) / 2, 0.018, y1 - y0 - 0.06, z + 0.016, z + 0.026, M["black"], bevel=0.0, tags=tags)
    B.cyl("b_collar0", 0, y0 + 0.035, z, 0.062, 0.03, AM, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("b_collarm", 0, (y0 + y1) / 2 + 0.02, z, 0.058, 0.028, AM, axis="Y", verts=8, bevel=0.006, tags=tags)
    B.cyl("b_collar1", 0, y1 - 0.01, z, 0.058, 0.032, AM, axis="Y", verts=8, bevel=0.006, tags=hot)
    # freio leve facetado em ponta de flecha com fendas transversais escuras
    yb = L - 0.12
    brake = [(-0.074, yb - 0.12), (0.074, yb - 0.12), (0.094, yb - 0.09), (0.094, yb + 0.025), (0.032, yb + 0.12),
             (-0.032, yb + 0.12), (-0.094, yb + 0.025), (-0.094, yb - 0.09)]
    br = B.plate("b_brake", brake, z - 0.07, z + 0.07, A, slope=0.018, tags=tags)
    bc = [B.box(f"b_bc{i}", 0, yb - 0.068 + i * 0.054, 0.22, 0.024, z + 0.014, z + 0.2, K, bevel=0.0)
          for i in range(3)]
    bc.append(B.box("b_bore_c", 0, L, 0.03, 0.06, z - 0.035, z + 0.2, K, bevel=0.0))
    B.cut(br, bc)
    # fundo escuro das fendas: e ele que esquenta
    B.box("b_brake_core", 0, yb - 0.014, 0.155, 0.165, z - 0.05, z + 0.018, K, bevel=0.0, tags=hot)


# ============================================================================ casco
def roof(M, T="roof"):
    """Teto 1x2: placas verdes, anel da torre no tile da frente, escotilha do atirador e respiro atras."""
    tags = (T,)
    w, h = PART["size"]
    green = B.mat_roof_green()
    K, KM, AM, S = M["core"], M["core_mid"], M["armor_mid"], M["steel"]
    px, py = PART["pivot"][0] - w / 2, h / 2 - PART["pivot"][1]
    rr = RING_R
    gap = 0.03
    B.box("deck_under", 0, 0, w, h, -0.05, 0.02, K, bevel=0.0, tags=tags)
    for ty in range(h):
        cy = h / 2 - ty - 0.5
        poly = B.rpoly(0, cy, 1 - 2 * gap, 1 - 2 * gap, 0, chamfer=0.07)
        dk, pnl = B.shard(f"deck{ty}", poly, 0.0, 0.06, green, slope=0.025, groove=0.05, panel_h=0.02, tags=tags)
        if ty == 1:
            # linhas de painel dos dois lados da escotilha: sulco ate o meio da placa com fundo escuro
            for t in (dk, pnl):
                if t is not None:
                    B.cut(t, [B.rbox(f"dl{sx}{t.name}", sx * 0.355, -0.40, 0.016, 0.26, 0.03, 0.2, K, bevel=0.0)
                              for sx in (-1, 1)])
            for sx in (-1, 1):
                B.rbox(f"dlbed{sx}", sx * 0.355, -0.40, 0.016, 0.26, 0.025, 0.035, K, bevel=0.0, tags=tags)
    B.torus("ringbear", px, py, 0.08, rr + 0.02, 0.05, KM, tags=tags)
    B.cyl("ringhole", px, py, 0.05, rr - 0.01, 0.1, M["black"], axis="Z", verts=64, bevel=0.0, tags=tags)
    pts = [(x, y) for x, y in B.ring_points(px, py, rr + 0.10, 28, math.pi / 28)
           if abs(x) < w / 2 - 0.06 and 0.04 < y < h / 2 - 0.06]
    B.bolts("rb", pts, 0.1, 0.02, S, tags=tags)
    # cantos da frente: tampas triangulares chanfradas
    for sx in (-1, 1):
        # pequenas e encostadas no canto: ficam ~0.04 fora da aresta da mandibula (vao pintado visivel a 1x)
        tri = [(sx * 0.43, 0.93), (sx * 0.34, 0.93), (sx * 0.43, 0.84)]
        B.plate(f"chatch{sx}", tri if sx < 0 else list(reversed(tri)), 0.06, 0.10, AM, slope=0.015, tags=tags)
    # tile de tras: escotilha do atirador (moldura escura + tampa octogonal com alca e dobradica) e respiro
    hy = -0.40
    B.plate("hatchf", B.rpoly(0, hy, 0.52, 0.48, 0, chamfer=0.13), 0.05, 0.085, KM, slope=0.012, tags=tags)
    hp = B.plate("hatch", B.rpoly(0, hy, 0.44, 0.40, 0, chamfer=0.10), 0.06, 0.11, AM, slope=0.025, tags=tags)
    B.cut(hp, [B.box("hatch_g", 0, hy, 0.30, 0.012, 0.10, 0.2, K, bevel=0.0)])
    B.box("hatch_h", 0, hy - 0.11, 0.18, 0.04, 0.11, 0.14, S, bevel=0.01, tags=tags)
    for sx in (-1, 1):
        B.box(f"hinge{sx}", sx * 0.13, hy + 0.215, 0.07, 0.035, 0.06, 0.11, KM, bevel=0.008, tags=tags)
    vy = -0.81
    v = B.box("hvent", 0, vy, 0.66, 0.20, 0.05, 0.12, KM, bevel=0.01, slope=0.015, tags=tags)
    B.cut(v, [B.box(f"hvc{i}", 0, vy - 0.05 + i * 0.05, 0.56, 0.026, 0.09, 0.2, K, bevel=0.0) for i in range(3)])
    B.box("hvbed", 0, vy, 0.56, 0.14, 0.085, 0.09, M["black"], bevel=0.0, tags=tags)
    B.box("hled", 0, vy - 0.05, 0.16, 0.012, 0.09, 0.097, M["glow_dim"], bevel=0.0, tags=tags)


def floor(M, T="floor"):
    """Piso: anel no tile da frente, posto do atirador atras com console e caixas de cinta dos lados."""
    from bsgen.common import crew_positions
    tags = (T,)
    w, h = PART["size"]
    pv = PART["pivot"]
    rr = RING_R
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    BR = brass()
    px, py = pv[0] - w / 2, h / 2 - pv[1]
    B.box("fl_base", 0, 0, w, h, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for ty in range(h):
        B.box(f"fl{ty}", 0, h / 2 - ty - 0.5, 0.92, 0.92, 0.0, 0.03, KM, bevel=0.01, tags=tags)
    B.torus("fl_ring", px, py, 0.05, rr * 0.78, 0.04, AM, tags=tags)
    hub = B.cyl("fl_hub", px, py, 0.05, rr * 0.30, 0.08, A, axis="Z", verts=48, tags=tags)
    B.cut(hub, [B.rbox(f"fl_hubg{k}", px + math.cos(math.radians(30 + 60 * k)) * rr * 0.18,
                       py + math.sin(math.radians(30 + 60 * k)) * rr * 0.18, 0.016, rr * 0.20, 0.07, 0.2, K,
                       rot=60 * k - 60, bevel=0.0) for k in range(6)])
    B.cyl("fl_hubc", px, py, 0.085, rr * 0.08, 0.012, KM, axis="Z", verts=16, bevel=0.0, tags=tags)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        B.rbox(f"fl_chev{k}", px + math.cos(a) * rr * 0.55, py + math.sin(a) * rr * 0.55, 0.08, 0.08, 0.05, 0.08,
               A, rot=45, bevel=0.008, tags=tags)
    B.box("fl_led_t", px, py + rr * 0.95, 0.20, 0.035, 0.04, 0.07, M["glow"], bevel=0.0, tags=tags)
    # posto do atirador
    for i, (cx, cy, _r) in enumerate(crew_positions(w, h, 1, pv)):
        x, y = cx - w / 2, h / 2 - cy
        B.box(f"seatb{i}", x, y + 0.04, 0.32, 0.30, 0.0, 0.05, S, bevel=0.012, tags=tags)
        B.box(f"seat{i}", x, y + 0.06, 0.26, 0.20, 0.05, 0.14, A, bevel=0.035, tags=tags)
        B.box(f"seatbk{i}", x, y - 0.09, 0.28, 0.07, 0.05, 0.24, KM, bevel=0.02, tags=tags)
        B.box(f"seatbs{i}", x, y - 0.09, 0.18, 0.025, 0.24, 0.255, S, bevel=0.006, tags=tags)
        B.box(f"console{i}", x, y + 0.31, 0.36, 0.11, 0.0, 0.22, KM, bevel=0.02, tags=tags)
        B.box(f"screen{i}", x, y + 0.31, 0.24, 0.05, 0.22, 0.24, M["screen"], bevel=0.0, tags=tags)
        # caixas de cinta dos lados do assento (tampa clara, cinta de latao a mostra)
        for sx in (-1, 1):
            bx = x + sx * 0.355
            B.box(f"can{sx}", bx, y - 0.02, 0.17, 0.36, 0.0, 0.17, KM, bevel=0.012, tags=tags)
            B.box(f"canlid{sx}", bx, y - 0.10, 0.13, 0.17, 0.17, 0.195, AM, bevel=0.008, tags=tags)
            for k in range(4):
                B.cyl(f"cancart{sx}{k}", bx, y + 0.04 + k * 0.03, 0.185, 0.012, 0.11, BR, axis="X", verts=8,
                      bevel=0.002, tags=tags)
    # estante de cintas na borda de tras
    B.box("rack", 0, -h / 2 + 0.11, 0.80, 0.14, 0.0, 0.14, AM, bevel=0.01, tags=tags)
    for i in range(3):
        B.box(f"mag{i}", -0.25 + i * 0.25, -h / 2 + 0.11, 0.17, 0.10, 0.14, 0.22, KM, bevel=0.01, tags=tags)
        B.box(f"magled{i}", -0.25 + i * 0.25, -h / 2 + 0.11, 0.10, 0.025, 0.22, 0.24, M["glow_dim"], bevel=0.0,
              tags=tags)
