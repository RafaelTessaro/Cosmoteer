"""F4 Fabrica de Misseis (Missile Factory) 3x3 - cargas de missil HE / submunicao / PEM (spec 2.0, factories F4).

ID novo rafaeltessaro.bs_factory_missile. Grade (vanilla factory_he 3x3): maquina = fileira de cima + [1,1];
ENTRADAS ferro [0,1] (esquerda) e enxofre [2,1] (direita); SAIDAS uma por receita (seletor bs_missile_type
0/1/2): HE [0,2], submunicao [1,2], PEM [2,2], cada base com a pastilha da cor do missil (Jararaca ambar, Piranha
amarelo-limao, Poraque azul: as cores dos misseis 2.0 aprovados). Placa de modo no teto em rect_centre [1.5, 0.5]
(placa_msl_he / placa_msl_cluster / placa_msl_emp de bs_placas).
Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade = 1 quadro.

Maquinario (familia das armas; LEDs ambar so em recessos):
  * LAMINADOR DE CORPOS (canto de cima a esquerda, sobre a base de ferro): casca clara com a janela do torno: o
    corpo do missil girando entre a placa e o contraponto, a ferramenta correndo ao longo dele; calha do ferro;
  * ENCHEDORA DE OGIVAS (canto de cima a direita, sobre a base de enxofre): carrossel de 3 ogivas numa janela, a
    da frente enchendo de explosivo (nivel ambar); calha do enxofre;
  * PORTICO (meio de cima): trilho de aco no alto, carro claro que corre no trilho e lanca telescopica com a garra:
    pega a ogiva na enchedora e a ENCAIXA no corpo deitado no berco em V (lampejo no encaixe);
  * BERCO DE ACABAMENTO (celula central): o missil pronto desce do berco de cima para o berco de baixo, onde as
    travas fecham as aletas, e sai pela borda de baixo: 3 setas de LED (ambar, amarelo, azul) para as 3 saidas.
Animacao: 12 quadros x 0,1 s: 0 carro na enchedora com a ogiva | 1-2 o carro leva a ogiva ate o corpo | 3 encaixe
(lampejo) | 4-5 o carro volta e pega a proxima ogiva | 6-7 o missil pronto desce ao berco de acabamento | 8-9 o
proximo corpo sai do laminador para o berco | 10-11 o missil acabado sai para a fileira de baixo.
O modo (HE / submunicao / PEM) nao muda a maquina: o missil e mostrado com a faixa da Jararaca (HE) no ninho e a
cor de cada modo fica na placa do teto e nas pastilhas das saidas.
"""

import math

import bs3d as B
import models as Mo
from parts import _bs2_fabricas_helpers as H

PART = {
    "id": "rafaeltessaro.bs_factory_missile",
    "kind": "factory",
    "size": [3, 3],
    "accent": "amber",
    "machine_frames": 12,
    "machine_interval": 0.1,
}

W, HH = PART["size"]
NF = PART["machine_frames"]
MATE_Y = 0.97              # linha do berco de encaixe (fileira de cima)
RAIL_Y = 1.24              # trilho do portico
MS = 1.55                  # escala da carga de missil (0.57 x 0.14 quadro)
BODY_X = -0.08             # centro do corpo no berco de encaixe (nariz para +X)
LOW_Y = 0.02               # berco de acabamento (celula central)
OUTS = {(0, 2): "msl_he", (1, 2): "msl_cluster", (2, 2): "msl_emp"}
PLATE_C = (0.0, 1.0)       # rect_centre [1.5, 0.5]

META_EXTRA = {
    "factory_code": "F4",
    "name_ptbr": "Fábrica de Mísseis",
    "grid": {"blocked": [[0, 0], [1, 0], [2, 0], [1, 1]],
             "inputs": {"iron": [0, 1, 1, 1], "sulfur": [2, 1, 1, 1]},
             "outputs": {"msl_he": [0, 2, 1, 1], "msl_cluster": [1, 2, 1, 1], "msl_emp": [2, 2, 1, 1]}},
    "mode_plate": {"rect_centre": [1.5, 0.5], "size": 0.8, "modes": ["msl_he", "msl_cluster", "msl_emp"],
                   "toggle": "bs_missile_type", "values": [0, 1, 2], "files": "placa_<modo>.png (art3d/bs_placas)",
                   "game_layer": "roof_doodads"},
    "notes": ["o maquinario e o mesmo nos 3 modos; pastilhas pintadas nas saidas e placa de modo no teto"],
}


def _state(phase):
    i = int(round(phase * NF)) % NF
    return {
        "i": i,
        # carro do portico (x) e lanca (0 recolhida .. 1 estendida ate a linha do berco)
        "cart": {0: 1.0, 1: 0.70, 2: 0.42, 3: 0.42, 4: 0.72, 5: 1.0}.get(i, 1.0),
        "boom": {0: 0.0, 1: 0.0, 2: 0.6, 3: 1.0, 4: 0.3, 5: 0.0}.get(i, 0.0),
        "carry": i in (0, 1, 2, 5, 6, 7, 8, 9, 10, 11),
        "flash": i == 3,
        # corpo no berco de cima (x do centro, None = vazio) e com ogiva?
        "body_x": {7: None, 8: -0.52, 9: BODY_X}.get(i, BODY_X),
        "body_nose": i in (4, 5, 6),
        "body_y": {6: 0.55}.get(i, MATE_Y),
        # missil acabado no berco de baixo (y do centro, None = vazio)
        "low_y": {7: LOW_Y, 8: LOW_Y, 9: LOW_Y, 10: -0.17, 11: -0.36}.get(i),
        "jig": {2: 0.6, 3: 1.0, 4: 1.0, 5: 0.4}.get(i, 0.0),
        "lock": i in (8, 9),
        # torno do laminador (0..1) e carrossel da enchedora (graus)
        "lathe": (i / NF),
        "fill": {0: 0.0, 1: 0.2, 2: 0.4, 3: 0.6, 4: 0.8, 5: 1.0}.get(i, 1.0 if i < 6 else (i - 6) / 6.0),
    }


# ============================================================================ piso
def floor(M, T="floor"):
    machine = {(0, 0), (1, 0), (2, 0), (1, 1)}
    pads = {(0, 1): 90, (2, 1): 90, (0, 2): (270, 90), (1, 2): (270, 90), (2, 2): (270, 90)}
    H.floor_grid(M, W, HH, machine, pads, T=T, chips=OUTS, rail_rows=(2,))


# ============================================================================ maquina
HOUSE = [(-1.40, 1.30), (-1.30, 1.40), (-0.70, 1.40), (-0.60, 1.30), (-0.60, 1.20), (-0.66, 1.14), (-0.66, 0.80),
         (-0.74, 0.72), (-1.32, 0.72), (-1.40, 0.80)]
BLADE = [(-1.40, 0.67), (-0.92, 0.67), (-0.70, 0.60), (-0.70, 0.545), (-1.30, 0.545), (-1.40, 0.60)]


def _housing(prefix, sx, M, tags, hole):
    """Casca clara de canto (lado sx) com o vao do conteudo e a lamina de baixo com a boca de entrada."""
    f = H.flip(sx)
    K, A, S, KM = M["core"], M["armor"], M["steel"], M["core_mid"]
    ha, hp = B.shard(prefix, f(HOUSE), 0.0, 0.40, A, slope=0.06, groove=0.03, panel_h=0.028, tags=tags)
    hole = f(hole)
    H.bezel(prefix + "_win", hole, B.offset_poly(hole, 0.022), 0.20, 0.40, M, tags, (ha, hp))
    ba, bp = B.shard(prefix + "_blade", f(BLADE), 0.0, 0.26, A, slope=0.04, groove=0.018, panel_h=0.022, tags=tags)
    H.ledslot(prefix + "_in", sx * 1.10, 0.61, 0.30, 0.07, 0.10, 0, M, tags, [ba, bp], vertical=False)
    for k in range(3):
        H.chevron(f"{prefix}_inchv{k}", sx * (1.00 + k * 0.10), 0.61, 90, M["glow_dim"], tags, z=0.108, s=0.40)
    H.ledslot(prefix + "_sl", sx * 1.355, 1.06, 0.032, 0.20, 0.34, 3, M, tags, [ha, hp], pw=0.016,
              pip_mat=M["glow_dim"])
    B.bolts(prefix + "_bolt", [(sx * 1.35, 1.35), (sx * 0.66, 1.35)], 0.43, 0.017, S, tags=tags)
    return ha, hp


LATHE_HOLE = [(-1.26, 0.86), (-0.80, 0.86), (-0.80, 1.12), (-0.86, 1.18), (-1.26, 1.18)]


def _lathe(M, Xm, tags, st):
    """Laminador de corpos: o corpo gira no torno (marcas das luvas correndo) e a ferramenta anda ao longo dele."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    _housing("la", -1, M, tags, LATHE_HOLE)
    y = 1.04
    B.box("la_head", -1.21, y, 0.07, 0.18, 0.20, 0.32, KM, bevel=0.01, tags=tags)
    B.box("la_tail", -0.84, y, 0.05, 0.12, 0.20, 0.30, KM, bevel=0.01, tags=tags)
    B.cyl("la_body", -1.025, y, 0.26, 0.06, 0.30, A, axis="X", verts=8, bevel=0.004, tags=tags)
    t = st["lathe"]
    for k in range(4):
        xx = -1.16 + ((k * 0.075 + t * 0.075 * 4) % 0.30)
        B.cyl(f"la_seam{k}", xx, y, 0.26, 0.062, 0.008, K, axis="X", verts=8, bevel=0.0, tags=tags)
    # ferramenta: carro de aco com ponta, andando ao longo do corpo
    tx = -1.13 + 0.21 * (0.5 - 0.5 * math.cos(2 * math.pi * t))
    B.box("la_tool", tx, y - 0.115, 0.06, 0.07, 0.22, 0.30, S, bevel=0.008, tags=tags)
    B.box("la_tip", tx, y - 0.07, 0.016, 0.03, 0.26, 0.28, Xm["silver"], bevel=0.0, tags=tags)
    B.box("la_rail", -1.03, y - 0.13, 0.40, 0.02, 0.20, 0.22, KM, bevel=0.0, tags=tags)
    B.box("la_billet", -1.03, 0.90, 0.22, 0.05, 0.20, 0.25, Xm["iron"], bevel=0.008, tags=tags)


FILL_HOLE = [(-1.24, 0.84), (-0.80, 0.84), (-0.80, 1.20), (-1.24, 1.20)]


def _filler(M, Xm, tags, st):
    """Enchedora de ogivas: carrossel de 3 ogivas (cones claros) girando; a da frente enche de explosivo."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    _housing("fi", 1, M, tags, FILL_HOLE)
    cx, cy = 1.02, 1.04
    B.cyl("fi_disk", cx, cy, 0.22, 0.17, 0.03, KM, axis="Z", verts=16, bevel=0.004, tags=tags)
    rot = -st["i"] * 10.0
    for k in range(3):
        a = 210 + rot + k * 120
        px, py = cx + math.cos(math.radians(a)) * 0.10, cy + math.sin(math.radians(a)) * 0.10
        B.cyl(f"fi_cup{k}", px, py, 0.25, 0.058, 0.02, S, axis="Z", verts=8, bevel=0.0, tags=tags)
        B.cyl(f"fi_cone{k}", px, py, 0.29, 0.05, 0.07, Xm["nose"], axis="Z", verts=8, bevel=0.0, tags=tags,
              r2=0.012)
    # bico de enchimento sobre a ogiva da frente + nivel ambar numa fenda
    B.box("fi_noz", cx - 0.13, cy - 0.11, 0.09, 0.05, 0.30, 0.34, KM, bevel=0.008, tags=tags)
    n = int(round(st["fill"] * 3))
    for k in range(3):
        B.box(f"fi_lv{k}", cx + 0.17, cy - 0.10 + k * 0.06, 0.026, 0.035, 0.30, 0.31,
              M["glow_dim"] if k < n else M["core_mid"], bevel=0.0, tags=tags)
    B.box("fi_lvbed", cx + 0.17, cy - 0.04, 0.045, 0.18, 0.29, 0.30, M["black"], bevel=0.0, tags=tags)


def _gantry(M, Xm, tags, st):
    """Portico: trilho no alto da fileira de cima, carro claro e lanca telescopica com a garra (e a ogiva)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    # viga do portico: perfil claro com canal escuro no meio, apoiada em 2 montantes claros nas pontas
    beam = [(-1.20, RAIL_Y - 0.06), (1.20, RAIL_Y - 0.06), (1.24, RAIL_Y - 0.02), (1.24, RAIL_Y + 0.06),
            (1.20, RAIL_Y + 0.10), (-1.20, RAIL_Y + 0.10), (-1.24, RAIL_Y + 0.06), (-1.24, RAIL_Y - 0.02)]
    bm, bp = B.shard("gt_beam", beam, 0.44, 0.52, AM, slope=0.02, groove=0.01, panel_h=0.01, tags=tags)
    for q, t in enumerate((bm, bp)):
        if t is not None:
            B.cut(t, [B.box(f"gt_bc{q}", 0, RAIL_Y + 0.02, 2.30, 0.035, 0.49, 0.8, K, bevel=0.0)])
    B.box("gt_bbed", 0, RAIL_Y + 0.02, 2.30, 0.035, 0.485, 0.49, M["black"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        post = [(sx * 1.10, RAIL_Y - 0.12), (sx * 1.34, RAIL_Y - 0.12), (sx * 1.38, RAIL_Y - 0.08),
                (sx * 1.38, RAIL_Y + 0.12), (sx * 1.34, RAIL_Y + 0.16), (sx * 1.10, RAIL_Y + 0.16)]
        post = post if sx < 0 else list(reversed(post))
        B.shard(f"gt_post{sx}", post, 0.0, 0.56, M["armor"], slope=0.03, groove=0.014, panel_h=0.014, tags=tags)
        B.bolts(f"gt_pb{sx}", [(sx * 1.24, RAIL_Y + 0.02)], 0.57, 0.018, S, tags=tags)
    cx = st["cart"]
    cart = [(cx - 0.17, RAIL_Y + 0.13), (cx + 0.17, RAIL_Y + 0.13), (cx + 0.20, RAIL_Y + 0.09),
            (cx + 0.20, RAIL_Y - 0.08), (cx + 0.08, RAIL_Y - 0.15), (cx - 0.08, RAIL_Y - 0.15),
            (cx - 0.20, RAIL_Y - 0.08), (cx - 0.20, RAIL_Y + 0.09)]
    ca, cp = B.shard("gt_cart", cart, 0.48, 0.62, A, slope=0.035, groove=0.016, panel_h=0.018, tags=tags)
    H.ledslot("gt_cl", cx, RAIL_Y + 0.04, 0.18, 0.032, 0.58, 3, M, tags, [ca, cp], vertical=False, pw=0.014,
              pips=[M["glow"] if st["flash"] else M["glow_dim"], None, M["glow_dim"]])
    for sx in (-1, 1):
        B.box(f"gt_wheel{sx}", cx + sx * 0.13, RAIL_Y + 0.02, 0.05, 0.16, 0.50, 0.56, KM, bevel=0.008, tags=tags)
    # lanca: tubo escuro telescopico descendo (-y) ate a garra
    yt = RAIL_Y - 0.15
    yg = yt - 0.12 - (yt - 0.12 - (MATE_Y + 0.12)) * st["boom"]
    L = yt - yg
    B.box("gt_boom", cx, (yt + yg) / 2, 0.08, L, 0.40, 0.47, KM, bevel=0.01, tags=tags)
    B.box("gt_boomr", cx, (yt + yg) / 2, 0.025, L - 0.04, 0.47, 0.48, S, bevel=0.0, tags=tags)
    B.box("gt_boom2", cx, yg + 0.03, 0.10, 0.06, 0.40, 0.48, AM, bevel=0.008, tags=tags)
    # garra (2 dedos) segurando a ogiva deitada com o nariz para +X
    for sy in (-1, 1):
        B.box(f"gt_fing{sy}", cx, yg - 0.035 + sy * 0.045, 0.10, 0.022, 0.30, 0.42, AM, bevel=0.006, tags=tags)
    if st["carry"]:
        H.mini_missile("gt_wh", cx - 0.03, yg - 0.035, 0.24, M, Xm, tags, kind="msl_he", s=MS, rz=-90,
                       part="nose", lit=False)


def _mate(M, Xm, tags, st):
    """Berco de encaixe em V (meio de cima) com o corpo deitado e, no encaixe, o lampejo."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.box("mt_bed", 0.0, MATE_Y, 1.02, 0.24, 0.0, 0.08, KM, bevel=0.01, tags=tags)
    for k, x in enumerate((-0.30, 0.0, 0.26)):
        for sy in (-1, 1):
            B.rbox(f"mt_v{k}{sy}", x, MATE_Y + sy * 0.075, 0.06, 0.06, 0.08, 0.17, AM, rot=0, bevel=0.008, tags=tags)
    # trilho de transferencia do laminador ate o berco
    B.box("mt_tr", -0.55, MATE_Y, 0.30, 0.10, 0.0, 0.06, K, bevel=0.006, tags=tags)
    for sy in (-1, 1):
        B.box(f"mt_trr{sy}", -0.55, MATE_Y + sy * 0.055, 0.30, 0.016, 0.06, 0.10, S, bevel=0.003, tags=tags)
    # gabarito de encaixe: 2 garras claras acima e abaixo do corpo que fecham no encaixe
    j = 0.035 * st["jig"]
    for sy in (-1, 1):
        claw = [(-0.40, 0.0), (0.18, 0.0), (0.24, 0.05), (0.24, 0.10), (-0.36, 0.10), (-0.40, 0.06)]
        claw = [(x, MATE_Y + sy * (0.155 - j + yy)) for x, yy in claw]
        claw = claw if sy > 0 else list(reversed(claw))
        ca, cp = B.shard(f"mt_jig{sy}", claw, 0.06, 0.30, A, slope=0.03, groove=0.012, panel_h=0.016, tags=tags)
        H.ledslot(f"mt_jl{sy}", -0.10, MATE_Y + sy * (0.205 - j), 0.30, 0.03, 0.26, 3, M, tags, [ca, cp],
                  vertical=False, pw=0.012, pips=[M["glow"] if st["jig"] >= 1 else M["glow_dim"], None, None])
    if st["body_x"] is not None:
        part = "all" if st["body_nose"] else "body"
        H.mini_missile("mt_body", st["body_x"], st["body_y"], 0.10, M, Xm, tags, kind="msl_he", s=MS, rz=-90,
                       part=part)
    if st["flash"]:
        fl = H.glow(Mo.ACCENTS["amber"], 3.0, "mflash")
        jx = BODY_X + 0.14 * MS / 1.55 + 0.005
        B.box("mt_flash", jx, MATE_Y, 0.012, 0.16, 0.30, 0.31, fl, bevel=0.0, tags=tags)
        sp = H.glow((1.0, 0.30, 0.03), 5.0, "mspark")
        for k, sy in enumerate((-1, 1)):
            B.rbox(f"mt_sp{k}", jx + 0.02, MATE_Y + sy * 0.10, 0.05, 0.010, 0.32, 0.33, sp, rot=sy * 50, bevel=0.0,
                   tags=tags)


LOWH = [(-0.47, 0.42), (-0.38, 0.47), (-0.30, 0.47), (-0.30, 0.20), (-0.36, 0.14), (-0.36, -0.20), (-0.30, -0.26),
        (-0.30, -0.33), (-0.47, -0.33)]


def _finish(M, Xm, tags, st):
    """Berco de acabamento (celula central): capuzes claros dos lados com as travas e a boca de saida embaixo."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.plate("lo_block", B.rpoly(0, 0, 0.94, 0.94, 0, chamfer=0.16), 0.0, 0.035, K, slope=0.012, tags=tags)
    # rampa de descida do berco de cima (canal escuro com guias)
    B.box("lo_ramp", 0, 0.34, 0.24, 0.30, 0.0, 0.05, M["black"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"lo_rg{sx}", sx * 0.13, 0.30, 0.022, 0.36, 0.0, 0.10, S, bevel=0.004, tags=tags)
    B.plate("lo_bed", B.rpoly(0, LOW_Y, 0.66, 0.24, 0, chamfer=0.05), 0.03, 0.07, KM, slope=0.01, tags=tags)
    for k, x in enumerate((-0.2, 0.18)):
        for sy in (-1, 1):
            B.box(f"lo_v{k}{sy}", x, LOW_Y + sy * 0.075, 0.05, 0.05, 0.07, 0.15, AM, bevel=0.008, tags=tags)
    for sx in (-1, 1):
        ha, hp = B.shard(f"lo_h{sx}", H.flip(sx)(LOWH), 0.0, 0.30, A, slope=0.045, groove=0.022, panel_h=0.022,
                         tags=tags)
        H.vent(f"lo_v{sx}", sx * 0.405, 0.27, 0.09, 0.22, 0.25, 0.30, M, tags, n=4, targets=[ha, hp])
        H.ledslot(f"lo_sl{sx}", sx * 0.405, -0.13, 0.032, 0.20, 0.25, 3, M, tags, [ha, hp], pw=0.016,
                  pips=[M["glow"] if st["lock"] else M["glow_dim"], None, None])
        # trava das aletas (fecha nos quadros 8-9)
        o = 0.0 if st["lock"] else 0.05
        B.box(f"lo_lock{sx}", sx * (0.30 + o), LOW_Y, 0.06, 0.10, 0.10, 0.22, S, bevel=0.008, tags=tags)
    # portal de vedacao claro sobre a saida (o missil acabado passa por baixo dele)
    gate = [(-0.30, -0.27), (0.30, -0.27), (0.34, -0.30), (0.34, -0.36), (0.30, -0.39), (-0.30, -0.39),
            (-0.34, -0.36), (-0.34, -0.30)]
    ga, gp = B.shard("lo_gate", gate, 0.14, 0.30, A, slope=0.025, groove=0.012, panel_h=0.014, tags=tags)
    H.ledslot("lo_gsl", 0, -0.33, 0.30, 0.03, 0.27, 4, M, tags, [ga, gp], vertical=False, pw=0.012,
              pips=[M["glow_dim"] if (st["low_y"] is not None and st["low_y"] < 0) else None, None, None, None])
    # boca de saida e as 3 setas (cor de cada missil) para as 3 bases de baixo
    B.box("lo_out", 0, -0.44, 0.62, 0.09, 0.0, 0.05, M["black"], bevel=0.0, tags=tags)
    for k, (x, ang, kind) in enumerate(((-0.24, 225, "msl_he"), (0.0, 270, "msl_cluster"), (0.24, 315, "msl_emp"))):
        H.chevron(f"lo_ar{k}", x, -0.445, ang, H.led(kind, 0.9), tags, z=0.05, s=0.55)
    if st["low_y"] is not None:
        H.mini_missile("lo_msl", 0.0, st["low_y"], 0.08, M, Xm, tags, kind="msl_he", s=MS, rz=-90)


def machine(M, T="machine", phase=0.0):
    tags = (T,)
    Xm = H.X(M)
    st = _state(phase)
    B.plate("mc_bed", B.rpoly(0, 0.975, 2.90, 0.90, 0, chamfer=0.08), 0.0, 0.05, M["core"], slope=0.01, tags=tags)
    _lathe(M, Xm, tags, st)
    _filler(M, Xm, tags, st)
    _mate(M, Xm, tags, st)
    _finish(M, Xm, tags, st)
    _gantry(M, Xm, tags, st)


# ============================================================================ teto
def roof(M, T="roof"):
    tags = (T,)
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    deck = H.roof_deck(M, W, HH, skip={(1, 0)}, T=T)
    H.roof_hatch("rf_in0", M, -1.0, 0.0, 90, deck[(0, 1)], T=T)
    H.roof_hatch("rf_in1", M, 1.0, 0.0, 90, deck[(2, 1)], T=T)
    for (i, j), kind in OUTS.items():
        px, py = H.cell_xy(W, HH, i, j)
        H.roof_hatch(f"rf_out{i}", M, px, py, 270, deck[(i, j)], T=T, chip=kind)
    # coroa do portico (meio de cima): encaixe da placa de modo entre dois montantes do trilho
    H.plate_slot("rf_plate", M, PLATE_C[0], PLATE_C[1], 0.8, [], T=T, z1=0.18)
    for sx in (-1, 1):
        post = H.flip(sx)([(-0.62, 1.44), (-0.50, 1.44), (-0.50, 0.58), (-0.56, 0.52), (-0.62, 0.52)])
        pa, pp = B.shard(f"rf_post{sx}", post, 0.0, 0.26, A, slope=0.03, groove=0.012, panel_h=0.014, tags=tags)
        H.ledslot(f"rf_psl{sx}", sx * 0.56, 1.0, 0.03, 0.24, 0.22, 3, M, tags, [pa, pp], pw=0.014,
                  pip_mat=M["glow_dim"])
    # cantos de cima: tampas blindadas das estacoes (respiro + fenda) com o trilho do portico passando por cima
    for sx in (-1, 1):
        pa, pp = deck[(0 if sx < 0 else 2, 0)]
        cover = H.flip(sx)([(-1.36, 1.30), (-1.26, 1.40), (-0.78, 1.40), (-0.70, 1.32), (-0.70, 0.84), (-0.78, 0.76),
                            (-1.26, 0.76), (-1.36, 0.86)])
        B.plate(f"rf_ck{sx}", B.offset_poly(cover, -0.03), 0.06, 0.10, K, slope=0.01, tags=tags)
        ca, cp = B.shard(f"rf_cov{sx}", cover, 0.09, 0.24, A, slope=0.05, groove=0.022, panel_h=0.022, tags=tags)
        H.vent(f"rf_cv{sx}", sx * 1.03, 1.16, 0.40, 0.20, 0.20, 0.25, M, tags, n=4, targets=[ca, cp])
        H.ledslot(f"rf_cs{sx}", sx * 1.03, 0.90, 0.30, 0.034, 0.20, 3, M, tags, [ca, cp], vertical=False, pw=0.016,
                  pip_mat=M["glow_dim"])
        B.box(f"rf_rail{sx}", sx * 0.95, 1.40, 0.90, 0.05, 0.24, 0.30, S, bevel=0.01, tags=tags)
    # celula central: escotilha em seta (o missil desce) com o perfil de missil gravado
    pa, pp = deck[(1, 1)]
    arrow = [(-0.30, 0.34), (0.30, 0.34), (0.30, -0.10), (0.0, -0.36), (-0.30, -0.10)]
    aa, ap = H.inlay("rf_carr", arrow, (pa, pp), 0.14, tags)
    msl = [(-0.035, 0.24), (0.035, 0.24), (0.035, -0.08), (0.0, -0.17), (-0.035, -0.08)]
    for q, t in enumerate((aa, ap)):
        if t is not None:
            B.cut(t, [B.loft(f"rf_mc{q}", msl, msl, 0.06, 0.5, K, bevel=0.0)])
    B.loft("rf_mbed", msl, msl, 0.055, 0.065, M["black"], bevel=0.0, tags=tags)
    for k in range(3):
        B.box(f"rf_mled{k}", 0, 0.16 - k * 0.09, 0.024, 0.03, 0.065, 0.072, M["glow_dim"], bevel=0.0, tags=tags)
    H.roof_unpaint(T)
