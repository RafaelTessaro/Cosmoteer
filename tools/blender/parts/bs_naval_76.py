"""Canhao Naval Automatico 76 mm ("Tambor") - modelo de referencia do estilo aprovado pelo usuario.

Casco facetado em ponta de flecha, garras (ombreira + lamina) que avancam ate o cano, espinha central
com sensor, tambores de carregador nos vaos, baia de exaustao traseira. Cano unico longo com carenagem
de resfriamento, extrator de gases e freio de boca em ponta.
"""

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_naval_76",
    "kind": "gun",
    "size": [3, 4],
    "pivot": [1.5, 1.65],          # coordenadas da peca (x direita, y para baixo), em tiles
    "turret_box": 2.9,             # lado do quadrado do sprite da torre
    "ring_r": 1.30,                # raio do anel da torre no teto/piso
    "accent": "amber",
    "barrels": {
        "ys": [0.0],               # deslocamento lateral de cada cano (tiles, + = direita)
        "root": 0.88,              # pivo -> raiz do cano
        "length": 2.6,             # raiz -> boca
        "width": 0.46,             # largura do sprite do cano
        "pad": 0.30,               # espaco atras da raiz para o recuo
        "anim": "recoil",
        "recoil": [0.26, 0.18, 0.10, 0.04],          # quadros de recuo (tiles)
        "heat": [1.0, 0.9, 0.78, 0.64, 0.5, 0.36, 0.22, 0.1],   # calor do freio por quadro (depois esfria)
        "interval": 0.06,
    },
    "lights": [                    # luzes dinamicas (roof_lights_fancy) em coordenadas da cabeca
        {"at": [0.0, -0.86], "size": 1.4, "color": [255, 120, 30], "z": 0.8},
    ],
    "preview_pattern": "single",
}


def head(M, T="head", phase=0.0):
    """Cabeca da torre: casco facetado em ponta de flecha, garras que avancam ate o cano."""
    tags = (T,)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    # anel giratorio e nucleo escuro (octogono chanfrado)
    B.cyl("ring", 0, 0, 0.04, 1.32, 0.08, KM, axis="Z", verts=72, bevel=0.01, tags=tags)
    B.bolts("ringbolt", B.ring_points(0, 0, 1.25, 24, 0.13), 0.09, 0.022, S, tags=tags)
    core = [(-1.10, -1.14), (1.10, -1.14), (1.26, -0.98), (1.26, 0.46), (0.70, 1.02), (-0.70, 1.02),
            (-1.26, 0.46), (-1.26, -0.98)]
    B.plate("core", core, 0.06, 0.34, K, slope=0.05, tags=tags)

    # garras: ombreira lateral + lamina que avanca em ponta ate o lado do cano (com vao entre as duas)
    pauldron = [(-0.62, -1.04), (-1.08, -1.04), (-1.30, -0.82), (-1.30, -0.34), (-1.42, -0.22), (-1.42, 0.24),
                (-1.26, 0.40), (-0.74, 0.56), (-0.70, -0.36), (-0.60, -0.48)]
    blade = [(-1.26, 0.53), (-0.80, 0.69), (-0.48, 0.95), (-0.34, 1.15), (-0.40, 1.29), (-0.64, 1.21), (-1.02, 0.90)]
    fin = [(-0.84, -0.94), (-1.10, -0.94), (-1.22, -0.80), (-1.22, -0.18), (-1.06, 0.00), (-0.86, -0.06)]
    for side, sx, f in (("L", -1, lambda p: p), ("R", 1, Mo.mirror)):
        _, pnl = B.shard(f"claw_{side}", f(pauldron), 0.30, 0.70, A, slope=0.11, groove=0.045, panel_h=0.035,
                         tags=tags)
        # linhas de painel recortadas na ombreira
        cuts = [B.rbox(f"pl{side}{i}", sx * x, y, 0.016, ln, 0.715, 0.9, K, rot=r, bevel=0.0)
                for i, (x, y, ln, r) in enumerate(((0.80, 0.20, 0.50, 0), (1.02, 0.36, 0.30, sx * 72)))]
        B.cut(pnl, cuts)
        ba, bpnl = B.shard(f"blade_{side}", f(blade), 0.30, 0.66, A, slope=0.08, groove=0.03, panel_h=0.03, tags=tags)
        # fenda com luz na lamina
        for t in (ba, bpnl):
            B.cut(t, [B.rbox(f"bcut{side}", sx * 0.80, 0.90, 0.30, 0.05, 0.62, 0.9, K, rot=sx * -38, bevel=0.0)])
        B.rbox(f"bbed{side}", sx * 0.80, 0.90, 0.30, 0.05, 0.60, 0.625, M["black"], rot=sx * -38, bevel=0.0,
               tags=tags)
        B.rbox(f"bglow{side}", sx * 0.80, 0.90, 0.22, 0.016, 0.62, 0.632, M["glow_dim"], rot=sx * -38, bevel=0.0,
               tags=tags)
        # aleta traseira em degrau, com fenda de pips recortada
        fa, fpnl = B.shard(f"fin_{side}", f(fin), 0.73, 0.84, A, slope=0.05, groove=0.03, panel_h=0.02, tags=tags)
        Mo.slot_with_pips(f"fslot{side}", sx * 1.04, -0.78, -0.40, 0.065, 0.86, 4, M, tags, target=[fa, fpnl], depth=0.04)
        # pistao hidraulico ligando ombreira e lamina
        B.cyl(f"piston{side}", sx * 0.66, 0.66, 0.42, 0.035, 0.34, S, axis="Y", verts=12, yaw=sx * 50, tags=tags)
        B.cyl(f"pistonb{side}", sx * 0.74, 0.58, 0.42, 0.05, 0.14, KM, axis="Y", verts=12, yaw=sx * 50, tags=tags)

    # mantelete em cunha (de onde sai o cano)
    mant = [(-0.25, 0.56), (0.25, 0.56), (0.31, 0.72), (0.24, 1.20), (-0.24, 1.20), (-0.31, 0.72)]
    m = B.plate("mantlet", mant, 0.30, 0.66, KM, slope=0.06, tags=tags)
    B.cut(m, [B.box("mant_cut", 0, 1.05, 0.22, 0.40, 0.58, 0.9, K, bevel=0.0)])
    for sx in (-1, 1):
        B.cyl(f"recup{sx}", sx * 0.19, 0.90, 0.50, 0.045, 0.50, S, axis="Y", verts=12, tags=tags)
        # calhas de alimentacao: dos tambores ate a culatra
        B.cyl(f"chute{sx}", sx * 0.42, 0.36, 0.44, 0.05, 0.42, KM, axis="Y", verts=8, yaw=sx * -18, tags=tags)
        for i in range(3):
            B.cyl(f"chuter{sx}{i}", sx * (0.47 - i * 0.04), 0.22 + i * 0.12, 0.44, 0.058, 0.025, S, axis="Y",
                  verts=8, yaw=sx * -18, tags=tags)

    # espinha central em seta, com sensor
    spine = [(-0.30, -0.84), (0.30, -0.84), (0.36, -0.74), (0.36, 0.14), (0.15, 0.58), (-0.15, 0.58),
             (-0.36, 0.14), (-0.36, -0.74)]
    B.shard("spine", spine, 0.30, 0.86, A, slope=0.10, groove=0.04, panel_h=0.03, tags=tags)
    spine2 = [(-0.17, -0.50), (0.17, -0.50), (0.20, -0.42), (0.20, 0.10), (0.08, 0.34), (-0.08, 0.34),
              (-0.20, 0.10), (-0.20, -0.42)]
    s2 = B.plate("spine2", spine2, 0.88, 0.98, A, slope=0.035, tags=tags)
    win = [(-0.12, -0.05), (0.12, -0.05), (0.12, 0.07), (0.045, 0.21), (-0.045, 0.21), (-0.12, 0.07)]
    B.cut(s2, [B.loft("win_cut", win, win, 0.94, 1.2, K, bevel=0.0)])
    B.loft("sensor_bed", win, win, 0.935, 0.945, M["black"], bevel=0.0, tags=tags)
    B.box("sensor_eye", 0, 0.06, 0.16, 0.03, 0.94, 0.952, M["lens"], bevel=0.0, tags=tags)
    Mo.slot_with_pips("sp", -0.34, -0.12, 0.12, 0.05, 0.98, 3, M, tags, target=s2, depth=0.03, vertical=False)

    # baia de exaustao traseira (persianas + pips)
    B.box("vent_bay", 0, -0.98, 1.00, 0.30, 0.20, 0.36, M["black"], bevel=0.0, tags=tags)
    for i in range(6):
        B.box(f"louver{i}", 0, -1.10 + i * 0.048, 0.96, 0.02, 0.30, 0.37, KM, bevel=0.004, tags=tags)
    for i, x in enumerate((-0.36, -0.22, -0.08, 0.08, 0.22, 0.36)):
        B.box(f"vent_pip{i}", x, -0.86, 0.06, 0.024, 0.34, 0.39, M["glow"], bevel=0.0, tags=tags)

    # carregadores de alimentacao visiveis nos vaos (tambores com contador ambar)
    for sx in (-1, 1):
        x = sx * 0.53
        B.cyl(f"drum{sx}", x, -0.22, 0.44, 0.12, 0.70, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
        for i, y in enumerate((-0.48, -0.22, 0.04)):
            B.cyl(f"drumring{sx}{i}", x, y, 0.44, 0.13, 0.04, S, axis="Y", verts=8, bevel=0.005, tags=tags)
        for i in range(4):
            B.box(f"drumled{sx}{i}", x, -0.40 + i * 0.07, 0.035, 0.035, 0.55, 0.575,
                  M["glow"] if i < 3 else M["black"], bevel=0.0, tags=tags)
        B.box(f"module{sx}", sx * 0.95, -1.04, 0.22, 0.10, 0.30, 0.40, KM, bevel=0.01, tags=tags)
    B.bolts("bolt", [(x, -1.10) for x in (-1.0, -0.66, 0.66, 1.0)], 0.35, 0.026, S, tags=tags)


def barrel(M, L=2.6, T="barrel", phase=0.0):
    """Cano com raiz (y=0) e boca (y=L), centrado em x=0, altura z=0.55."""
    tags = (T,)
    hot = (T, "hot")  # partes que brilham de calor depois do tiro
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    z = 0.55
    # luva de recuo (raiz) octogonal
    B.cyl("b_root", 0, 0.16, z, 0.185, 0.32, KM, axis="Y", verts=8, bevel=0.012, tags=tags)
    B.cyl("b_rootcap", 0, 0.33, z, 0.165, 0.04, S, axis="Y", verts=8, bevel=0.006, tags=tags)
    # carenagem de resfriamento com fendas no topo (brilho de calor no fundo)
    y0j, y1j = 0.35, 0.97
    sh = B.cyl("b_shroud", 0, (y0j + y1j) / 2, z, 0.155, y1j - y0j, KM, axis="Y", verts=8, bevel=0.01, tags=tags)
    cuts = [B.box(f"b_shc{i}", 0, 0.44 + i * 0.11, 0.17, 0.05, z + 0.07, z + 0.3, K, bevel=0.0) for i in range(5)]
    B.cut(sh, cuts)
    B.box("b_heat", 0, (y0j + y1j) / 2, 0.15, y1j - y0j - 0.06, z + 0.07, z + 0.08, M["ember"], bevel=0.0,
          tags=tags)
    B.cyl("b_jacket", 0, (y0j + y1j) / 2, z, 0.06, y1j - y0j, K, axis="Y", verts=16, tags=tags)
    # luva principal facetada e afunilada, com canal escuro recortado
    y0, y1 = 0.97, L - 0.40
    sl = B.cyl("b_sleeve", 0, (y0 + y1) / 2, z, 0.14, y1 - y0, A, axis="Y", verts=8, bevel=0.008, tags=hot,
               r2=0.118)
    B.cut(sl, [B.box("b_chc", 0, (y0 + y1) / 2, 0.05, y1 - y0 - 0.12, z + 0.08, z + 0.3, K, bevel=0.0)])
    B.box("b_chbed", 0, (y0 + y1) / 2, 0.05, y1 - y0 - 0.12, z + 0.06, z + 0.09, M["black"], bevel=0.0, tags=tags)
    # extrator de gases (bojo facetado)
    ye = y0 + (y1 - y0) * 0.40
    fume = B.cyl("b_fume", 0, ye, z, 0.165, 0.28, A, axis="Y", verts=8, bevel=0.015, tags=hot)
    B.cut(fume, [B.box("b_fumec", 0, ye, 0.05, 0.36, z + 0.08, z + 0.3, K, bevel=0.0)])
    for sx in (-1, 1):
        B.cyl(f"b_fumecone{sx}", 0, ye + sx * 0.18, z, 0.135 if sx < 0 else 0.165, 0.08, A, axis="Y", verts=8,
              bevel=0.0, tags=hot, r2=0.165 if sx < 0 else 0.13)
    for i, y in enumerate((y0 + 0.04, y1 - 0.04)):
        B.cyl(f"b_collar{i}", 0, y, z, 0.15 - i * 0.02, 0.05, AM, axis="Y", verts=8, bevel=0.008, tags=hot)
    # freio de boca em ponta de flecha com fendas transversais no topo
    yb = L - 0.21
    brake = [(-0.16, yb - 0.21), (0.16, yb - 0.21), (0.20, yb - 0.13), (0.20, yb + 0.08), (0.12, yb + 0.21),
             (-0.12, yb + 0.21), (-0.20, yb + 0.08), (-0.20, yb - 0.13)]
    br = B.plate("b_brake", brake, z - 0.14, z + 0.14, A, slope=0.05, tags=hot)
    bc = [B.box(f"b_bc{i}", 0, yb - 0.11 + i * 0.09, 0.44, 0.04, z + 0.03, z + 0.3, K, bevel=0.0) for i in range(3)]
    bc.append(B.box("b_bore_c", 0, L, 0.11, 0.12, z - 0.06, z + 0.3, K, bevel=0.0))
    B.cut(br, bc)
    B.box("b_brake_core", 0, yb - 0.02, 0.30, 0.30, z - 0.10, z + 0.03, K, bevel=0.0, tags=tags)


