"""F3 Fabrica de Celulas (Cell Factory) 3x3 - celula de plasma e Celula PEM (spec 2.0, factories F3).

Mesmo ID da 1.x (rafaeltessaro.bs_factory_plasma), arte REFEITA: agora com seletor bs_cell_type (0 plasma,
1 PEM). Grade (vanilla factory_he 3x3): maquina = fileira de cima + [1,1]; ENTRADAS enxofre [0,1] (esquerda),
bobina [2,1] (direita) e cobre [1,2] (no meio da fileira de baixo, sobre a grade de cobre do piso, caminhavel
pela porta [1,3]); SAIDAS celula de plasma [0,2] (esquerda, pastilha ciano) e Celula PEM [2,2] (direita, pastilha
de cobre). Placa de modo no teto em rect_centre [0.5, 0.5] (placa_plasma / placa_pem de bs_placas).
Coordenadas centradas na peca, +Y = frente (topo da imagem), 1 unidade = 1 quadro.

Maquinario (familia das armas; ciano so em fendas e recessos escuros, forca <= 1.25):
  * TANQUES DE PLASMA (canto de cima a esquerda, sobre a base de enxofre): 2 tanques claros em capsula num berco,
    com o visor vertical de nivel ciano subindo e descendo; coletor escuro e boca de entrada do enxofre;
  * ANEL DE CONFINAMENTO (meio de cima, o mesmo toro aprovado na 1.x): 6 blocos de bobina claros, o plasma ciano
    so nas fendas, pulso dando 2 voltas por ciclo; dutos dos tanques e do banco de bobinas ate o anel;
  * BANCO DE BOBINAS DE COBRE (canto de cima a direita, sobre a base de bobina): 3 bobinas de cobre deitadas entre
    placas claras, com o guia do fio indo e voltando na bobina de cima (assinatura de cobre da familia PEM);
  * BERCO DE ENCHIMENTO (celula central): capuzes claros com respiros, garras, bico injetor que desce do anel; a
    celula cheia cai no ALCAPAO de baixo (portas que abrem) e sai para a base da receita: setas ciano para a
    esquerda-baixo (plasma) e de cobre para a direita-baixo (PEM); boca do cobre no meio da borda de baixo.
Animacao: 12 quadros x 0,12 s: 0 celula vazia, bico recolhido (= sprite desligado) | 1 bico desce | 2 encaixa |
3-6 a celula enche | 6-8 respiros em rampa ciano, o bico sobe | 8 garras abrem | 9-10 a celula desce pelo alcapao
| 11 a proxima celula vazia entra pelo capuz esquerdo.
Camadas extras (EXTRA_LAYERS, render pelo _bs2_fabricas_helpers.py; spec factories F3.pem_bank):
  * banco_pem.png (+ normais) no rect [2.0, 0.1, 0.9, 1.0], roof_doodads: banco de bobinas de cobre aparafusado
    sobre o teto, so no modo PEM (ToggledComponents bs_cell_type = 1);
  * banco_pem_luz1..4.png, lights_add, 0,1 s por quadro: as frestas entre as espiras acendem em azul (baixo) numa
    onda de baixo para cima; precisa do modo PEM E da fabrica produzindo (AnimationToggle).
Teto: placas verdes; encaixe da placa de modo no canto de cima a esquerda; emblema do toro no meio de cima;
base do banco PEM (placa verde com 4 batentes) no canto de cima a direita; escotilha em capsula sobre o berco;
escotilhas em seta nas 3 entradas e nas 2 saidas (com a pastilha da celula).
"""

import math

import bs3d as B
import models as Mo
from parts import _bs2_fabricas_helpers as H

PART = {
    "id": "rafaeltessaro.bs_factory_plasma",
    "kind": "factory",
    "size": [3, 3],
    "accent": "cyan",
    "machine_frames": 12,
    "machine_interval": 0.12,
}

W, HH = PART["size"]
NF = PART["machine_frames"]
RC = (0.0, 0.975)          # centro do anel toroidal
RING_R = 0.295
SEG_R0, SEG_R1 = 0.19, 0.405
CR_Y = 0.13                # centro da celula no berco
CELL_S = 0.95              # escala da celula (0.13 x 0.36 quadro)
CELL_Z = 0.07
PLATE_C = (-1.0, 1.0)      # rect_centre [0.5, 0.5]
BANK_RECT = [2.0, 0.1, 0.9, 1.0]
BANK_C = (0.95, 0.90)      # centro do rect do banco em coordenadas do modelo
OUTS = {(0, 2): "plasma", (2, 2): "pem_cu"}

EXTRA_LAYERS = [
    {"name": "banco_pem", "fn": "banco_pem", "game_layer": "roof_doodads", "rect": BANK_RECT, "normals": True,
     "file": "banco_pem.png", "halo": False, "gate": "ModeToggle PEM (bs_cell_type = 1)"},
    {"name": "banco_pem_luz", "fn": "banco_pem_luz", "game_layer": "lights_add", "rect": BANK_RECT,
     "file": "banco_pem_luz{i}.png", "frames": 4, "interval": 0.1, "emission_only": True, "blend": "add",
     "halo_px": 2.5, "gain": 1.0,
     "gate": "ModeToggle PEM (bs_cell_type = 1) E AnimationToggle da fabrica (produzindo)"},
]

META_EXTRA = {
    "factory_code": "F3",
    "name_ptbr": "Fábrica de Células",
    "grid": {"blocked": [[0, 0], [1, 0], [2, 0], [1, 1]],
             "inputs": {"sulfur": [0, 1, 1, 1], "coil": [2, 1, 1, 1], "copper": [1, 2, 1, 1]},
             "outputs": {"plasma": [0, 2, 1, 1], "pem": [2, 2, 1, 1]}},
    "mode_plate": {"rect_centre": [0.5, 0.5], "size": 0.8, "modes": ["plasma", "pem"], "toggle": "bs_cell_type",
                   "values": [0, 1], "files": "placa_<modo>.png (art3d/bs_placas)", "game_layer": "roof_doodads"},
    "notes": ["grade de cobre no poco da base [1,2] (J2R3-9)",
              "banco_pem/banco_pem_luz: overlays do modo PEM (spec factories F3.pem_bank)"],
}


# ============================================================================ utilidades
def _extra():
    return {
        "pl_lo": B.mat_glow("pl_lo", Mo.CYAN, 0.16),
        "pl_tail": B.mat_glow("pl_tail", Mo.CYAN, 0.34),
        "pl_mid": B.mat_glow("pl_mid", Mo.CYAN, 0.70),
        "pl_hi": B.mat_glow("pl_hi", Mo.CYAN, 1.25),
        "em_ring": B.mat_glow("em_ring", Mo.CYAN, 0.90),
        "blue_lo": B.mat_glow("f3_blue_lo", (0.08, 0.48, 1.0), 0.45),
        "blue": B.mat_glow("f3_blue", (0.08, 0.48, 1.0), 0.9),
        "drum": B.mat_metal("f3_drum", (0.10, 0.11, 0.12), rough=0.35, metal=0.8),
    }


def _pol(cx, cy, r, a):
    return (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))


def _sector(cx, cy, r0, r1, ac, hs, c=0.0, n=3):
    """Setor de coroa (angulo central ac, meia abertura hs, graus) facetado, cantos chanfrados em c."""
    a0, a1 = ac - hs, ac + hs
    out = []
    if c > 0:
        out.append(_pol(cx, cy, r1 - c, a0))
        da = math.degrees(c / r1)
        for k in range(n + 1):
            out.append(_pol(cx, cy, r1, a0 + da + (a1 - a0 - 2 * da) * k / n))
        out.append(_pol(cx, cy, r1 - c, a1))
        db = math.degrees(c / r0)
        out.append(_pol(cx, cy, r0 + c, a1))
        out.append(_pol(cx, cy, r0, a1 - db))
        out.append(_pol(cx, cy, r0, a0 + db))
        out.append(_pol(cx, cy, r0 + c, a0))
    else:
        for k in range(n + 1):
            out.append(_pol(cx, cy, r1, a0 + (a1 - a0) * k / n))
        for k in range(n + 1):
            out.append(_pol(cx, cy, r0, a1 - (a1 - a0) * k / n))
    return out


def _state(phase):
    i = int(round(phase * NF)) % NF
    return {
        "i": i,
        "arm": {1: 0.5, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0, 7: 0.45}.get(i, 0.0),
        "level": {3: 0.25, 4: 0.5, 5: 0.75}.get(i, 1.0 if 6 <= i <= 10 else 0.0),
        "flow": 3 <= i <= 6,
        "contact": i == 2,
        "vent": {6: 1, 7: 3, 8: 2}.get(i, 0),
        "clamp": 1.0 if 8 <= i <= 10 else (0.5 if i == 11 else 0.0),
        "cell_y": {9: -0.02, 10: -0.17}.get(i, CR_Y if i <= 8 else None),
        "hatch": {9: 0.5, 10: 1.0, 11: 0.4}.get(i, 0.0),
        "in_x": {11: -0.10}.get(i),
    }


# ============================================================================ piso
def floor(M, T="floor"):
    machine = {(0, 0), (1, 0), (2, 0), (1, 1)}
    pads = {(0, 1): 90, (2, 1): 90, (1, 2): 90, (0, 2): (270, 90), (2, 2): (270, 90)}
    H.floor_grid(M, W, HH, machine, pads, T=T, chips=OUTS, copper={(1, 2)}, rail_rows=(2,))


# ============================================================================ maquina: anel toroidal
SEQ = [1, 0, 5, 4, 3, 2]


def _ring(M, X, tags, st):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    cx, cy = RC
    i = st["i"]
    B.plate("rg_base", H.octo(cx, cy, 0.47), 0.03, 0.10, K, slope=0.02, tags=tags)
    B.bolts("rg_bolt", [p for p in H.octo(cx, cy, 0.44) if abs(p[1] - cy) < 0.3], 0.105, 0.016, S, tags=tags)
    B.torus("rg_torus", cx, cy, 0.17, RING_R, 0.085, KM, tags=tags)
    lead = i % 6
    lv = ["pl_hi", "pl_mid", "pl_tail"] if i > 0 else ["pl_mid"]
    for k in range(6):
        a = 30 + 60 * k
        poly = _sector(cx, cy, SEG_R0, SEG_R1, a, 22.0, c=0.03, n=1)
        ba, bp = B.shard(f"rg_blk{k}", poly, 0.10, 0.32, A, slope=0.035, groove=0.018, panel_h=0.022, tags=tags)
        slit = _sector(cx, cy, RING_R - 0.021, RING_R + 0.021, a, 13.5, n=4)
        for q, t in enumerate((ba, bp)):
            if t is not None:
                B.cut(t, [B.loft(f"rg_sc{k}{q}", slit, slit, -0.1, 0.8, K, bevel=0.0)])
        B.loft(f"rg_bed{k}", slit, slit, 0.252, 0.258, M["black"], bevel=0.0, tags=tags)
        back = (lead - SEQ.index(k)) % 6
        mat = X[lv[back]] if back < len(lv) else X["pl_lo"]
        core = _sector(cx, cy, RING_R - 0.0125, RING_R + 0.0125, a, 12.0, n=4)
        B.loft(f"rg_pl{k}", core, core, 0.258, 0.264, mat, bevel=0.0, tags=tags)
        if bp is not None:
            cuts = []
            for j, da in enumerate((-16.0, 16.0)):
                p0 = _pol(cx, cy, (SEG_R0 + SEG_R1) / 2, a + da)
                cuts.append(B.rbox(f"rg_gr{k}{j}", p0[0], p0[1], 0.014, 0.12, 0.30, 0.6, K, rot=a + da - 90,
                                   bevel=0.0))
            B.cut(bp, cuts)
        ag = a + 30
        if ag % 180 != 0:
            p0 = _pol(cx, cy, RING_R, ag)
            B.rbox(f"rg_clamp{k}", p0[0], p0[1], 0.05, 0.20, 0.14, 0.27, KM, rot=ag - 90, bevel=0.008, tags=tags)
            B.bolts(f"rg_cb{k}", [p0], 0.275, 0.013, S, tags=tags)
    B.plate("rg_hub", H.octo(cx, cy, 0.125), 0.10, 0.22, AM, slope=0.025, tags=tags)
    hub2 = B.plate("rg_hub2", H.octo(cx, cy, 0.075, 0), 0.22, 0.26, S, slope=0.012, tags=tags)
    B.cut(hub2, [B.loft("rg_hubc", H.octo(cx, cy, 0.035, 0), H.octo(cx, cy, 0.035, 0), 0.20, 0.5, K, bevel=0.0)])
    B.loft("rg_hubbed", H.octo(cx, cy, 0.035, 0), H.octo(cx, cy, 0.035, 0), 0.215, 0.225, M["black"], bevel=0.0,
           tags=tags)
    B.cyl("rg_hubeye", cx, cy, 0.228, 0.017, 0.006, X["pl_hi"] if st["flow"] else X["pl_tail"], axis="Z",
          verts=8, bevel=0.0, tags=tags)


def _ducts(M, Xm, X, tags):
    """Dutos dos tanques (plasma ciano fraco) e do banco de bobinas (aneis de cobre) ate as fendas do anel."""
    KM, S = M["core_mid"], M["steel"]
    cx, cy = RC
    for sx in (-1, 1):
        x0, x1 = sx * 0.66, sx * (SEG_R1 - 0.02)
        xm, ln = (x0 + x1) / 2, abs(x1 - x0)
        B.cyl(f"dc{sx}", xm, cy, 0.20, 0.05, ln, KM, axis="X", verts=8, bevel=0.006, tags=tags)
        for j, f in enumerate((0.2, 0.75)):
            B.cyl(f"dc_r{sx}{j}", x0 + (x1 - x0) * f, cy, 0.20, 0.058, 0.026, Xm["copper"] if sx > 0 else S,
                  axis="X", verts=8, bevel=0.004, tags=tags)
        B.box(f"dc_bed{sx}", xm, cy, ln - 0.06, 0.03, 0.245, 0.252, M["black"], bevel=0.0, tags=tags)
        B.box(f"dc_flow{sx}", xm, cy, ln - 0.10, 0.012, 0.252, 0.256, X["pl_mid"] if sx < 0 else Xm["copper"],
              bevel=0.0, tags=tags)


# ============================================================================ maquina: tanques e banco de bobinas
FRAME = [(-1.40, 1.30), (-1.30, 1.40), (-0.76, 1.40), (-0.66, 1.30), (-0.66, 0.92), (-0.74, 0.84), (-1.32, 0.84),
         (-1.40, 0.92)]
BLADE = [(-1.40, 0.79), (-0.92, 0.79), (-0.60, 0.69), (-0.60, 0.545), (-1.30, 0.545), (-1.40, 0.645)]


def _frame(prefix, sx, M, tags, hole):
    """Berco claro (moldura chanfrada com o vao do conteudo) + lamina de baixo com a boca de entrada."""
    f = H.flip(sx)
    K, A, S, KM = M["core"], M["armor"], M["steel"], M["core_mid"]
    fa, fp = B.shard(prefix + "_fr", f(FRAME), 0.0, 0.40, A, slope=0.06, groove=0.03, panel_h=0.028, tags=tags)
    hole = f(hole)
    for q, t in enumerate((fa, fp)):
        if t is not None:
            B.cut(t, [B.loft(f"{prefix}_frh{q}", hole, hole, 0.06, 0.9, K, bevel=0.0)])
    B.loft(prefix + "_frbed", hole, hole, 0.04, 0.06, M["black"], bevel=0.0, tags=tags)
    ba, bp = B.shard(prefix + "_blade", f(BLADE), 0.0, 0.30, A, slope=0.045, groove=0.02, panel_h=0.025, tags=tags)
    H.ledslot(prefix + "_in", sx * 1.10, 0.67, 0.30, 0.075, 0.12, 0, M, tags, [ba, bp], vertical=False)
    for k in range(3):
        H.chevron(f"{prefix}_inchv{k}", sx * (1.00 + k * 0.10), 0.67, 90, M["glow_dim"], tags, z=0.128, s=0.40)
    if bp is not None:
        B.cut(bp, [B.rbox(prefix + "_pl3", sx * 0.80, 0.665, 0.022, 0.12, 0.26, 0.8, K, rot=sx * 58, bevel=0.0)])
    B.bolts(prefix + "_bolt", [(sx * 1.35, 1.35), (sx * 0.71, 1.35), (sx * 1.35, 0.89)], 0.43, 0.017, S, tags=tags)
    B.cyl(prefix + "_hose", sx * 1.05, 0.815, 0.10, 0.028, 0.46, KM, axis="X", verts=8, bevel=0.005, tags=tags)
    return fa, fp


TANK_HOLE = [(-1.30, 0.92), (-0.76, 0.92), (-0.76, 1.31), (-1.30, 1.31)]


def _tanks(M, Xm, X, tags, st):
    """2 tanques de plasma em capsula no berco da esquerda, visor vertical com o nivel ciano."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    fa, fp = _frame("tk", -1, M, tags, TANK_HOLE)
    H.ledslot("tk_sl", -1.355, 1.12, 0.032, 0.22, 0.34, 3, M, tags, [fa, fp], pw=0.016, pip_mat=M["glow_dim"])
    i = st["i"]
    for k, x in enumerate((-1.165, -0.895)):
        yc, L, r = 1.115, 0.38, 0.105
        tank = B.cyl(f"tk{k}", x, yc, 0.16, r, L, A, axis="Y", verts=8, bevel=0.01, tags=tags)
        for sy in (-1, 1):
            B.cyl(f"tk_cap{k}{sy}", x, yc + sy * (L / 2 + 0.012), 0.16, r * 0.82, 0.03, S, axis="Y", verts=8,
                  bevel=0.004, tags=tags)
            B.cyl(f"tk_band{k}{sy}", x, yc + sy * 0.12, 0.16, r * 1.04, 0.026, KM, axis="Y", verts=8, bevel=0.004,
                  tags=tags)
        # visor vertical: fenda escura no topo do tanque com o nivel ciano (oscila com a fase, os 2 defasados)
        B.cut(tank, [B.box(f"tk_vc{k}", x, yc, 0.045, 0.20, 0.16 + r * 0.80, 0.6, K, bevel=0.0)])
        B.box(f"tk_vb{k}", x, yc, 0.045, 0.20, 0.16 + r * 0.74, 0.16 + r * 0.80, M["black"], bevel=0.0, tags=tags)
        lvl = 2 + int(round(1.5 + 1.5 * math.sin(2 * math.pi * (i / NF) + k * 2.2)))
        for j in range(5):
            on = j < lvl
            B.box(f"tk_lv{k}{j}", x, yc - 0.08 + j * 0.04, 0.024, 0.028, 0.16 + r * 0.80, 0.16 + r * 0.82,
                  (X["pl_mid"] if j == lvl - 1 else X["pl_tail"]) if on else KM, bevel=0.0, tags=tags)
    # coletor escuro sob os tanques ate o duto do anel (o enxofre ionizado sobe da boca de baixo)
    B.box("tk_man", -1.03, 0.885, 0.50, 0.05, 0.04, 0.10, KM, bevel=0.008, tags=tags)
    for k, x in enumerate((-1.165, -0.895)):
        B.cyl(f"tk_pipe{k}", x, 0.90, 0.10, 0.02, 0.05, S, axis="Y", verts=8, bevel=0.0, tags=tags)


COIL_HOLE = [(-1.30, 0.92), (-0.76, 0.92), (-0.76, 1.31), (-1.30, 1.31)]


def _coils(M, Xm, X, tags, st):
    """Banco de bobinas de cobre no berco da direita: 3 bobinas deitadas (espiras = aneis escuros finos) entre
    placas, guia do fio indo e voltando na bobina de cima."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    fa, fp = _frame("cb", 1, M, tags, COIL_HOLE)
    H.ledslot("cb_sl", 1.355, 1.12, 0.032, 0.22, 0.34, 3, M, tags, [fa, fp], pw=0.016,
              pips=[X["blue_lo"], X["blue_lo"], None])
    i = st["i"]
    x0, x1 = 0.79, 1.27
    for k, y in enumerate((1.245, 1.115, 0.985)):
        B.cyl(f"cb_core{k}", (x0 + x1) / 2, y, 0.15, 0.052, x1 - x0 + 0.04, KM, axis="X", verts=8, bevel=0.0,
              tags=tags)
        B.cyl(f"cb_cu{k}", (x0 + x1) / 2, y, 0.15, 0.058, x1 - x0 - 0.06, Xm["copper"], axis="X", verts=12,
              bevel=0.004, tags=tags)
        for j in range(7):
            xx = x0 + 0.05 + j * (x1 - x0 - 0.10) / 6
            B.cyl(f"cb_w{k}{j}", xx, y, 0.15, 0.0595, 0.007, K, axis="X", verts=12, bevel=0.0, tags=tags)
        for sx in (-1, 1):
            B.cyl(f"cb_end{k}{sx}", (x0 + x1) / 2 + sx * (x1 - x0) / 2, y, 0.15, 0.064, 0.026, S, axis="X", verts=8,
                  bevel=0.004, tags=tags)
    # guia do fio (carro de aco) correndo sobre a bobina de cima
    t = 0.5 - 0.5 * math.cos(2 * math.pi * i / NF)
    gx = x0 + 0.06 + t * (x1 - x0 - 0.12)
    B.box("cb_guide", gx, 1.245, 0.05, 0.13, 0.20, 0.25, AM, bevel=0.008, tags=tags)
    B.box("cb_guidek", gx, 1.245, 0.02, 0.09, 0.25, 0.255, M["black"], bevel=0.0, tags=tags)
    B.box("cb_rail", (x0 + x1) / 2, 1.33, x1 - x0, 0.02, 0.18, 0.21, S, bevel=0.004, tags=tags)
    B.box("cb_wire", gx, 1.30, 0.008, 0.06, 0.21, 0.22, Xm["copper"], bevel=0.0, tags=tags)
    B.box("cb_man", 1.03, 0.885, 0.50, 0.05, 0.04, 0.10, KM, bevel=0.008, tags=tags)


# ============================================================================ maquina: berco
LHOOD = [(-0.47, 0.36), (-0.37, 0.46), (-0.215, 0.46), (-0.215, -0.035), (-0.29, -0.11), (-0.47, -0.11)]
NECK = [(-0.115, 0.64), (0.115, 0.64), (0.115, 0.535), (0.0, 0.445), (-0.115, 0.535)]
WEDGE = [(-0.47, -0.165), (-0.27, -0.165), (-0.17, -0.265), (-0.17, -0.31), (-0.33, -0.47), (-0.47, -0.47)]


def _cradle(M, Xm, X, tags, st):
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    B.plate("cr_block", B.rpoly(0, 0, 0.94, 0.94, 0, chamfer=0.16), 0.0, 0.035, K, slope=0.012, tags=tags)
    B.plate("cr_bed", B.rpoly(0, 0.10, 0.40, 0.62, 0, chamfer=0.07), 0.03, 0.06, KM, slope=0.012, tags=tags)
    B.box("cr_bedk", 0, 0.10, 0.15, 0.54, 0.06, 0.064, M["black"], bevel=0.0, tags=tags)
    for sx in (-1, 1):
        B.box(f"cr_rail{sx}", sx * 0.118, 0.10, 0.022, 0.60, 0.04, CELL_Z, S, bevel=0.003, tags=tags)
    vfl = st["vent"]
    vmat = (None, X["pl_tail"], X["pl_mid"], X["pl_hi"])[vfl]
    for sx in (-1, 1):
        f = H.flip(sx)
        ha, hp = B.shard(f"hood{sx}", f(LHOOD), 0.0, 0.30, A, slope=0.05, groove=0.025, panel_h=0.025, tags=tags)
        vx = sx * 0.345
        for q, t in enumerate((ha, hp)):
            if t is not None:
                B.cut(t, [B.box(f"hv_c{sx}{q}", vx, 0.18, 0.12, 0.34, 0.265, 0.8, K, bevel=0.0)])
        B.box(f"hv_bed{sx}", vx, 0.18, 0.12, 0.34, 0.26, 0.27, M["black"], bevel=0.0, tags=tags)
        for k in range(5):
            y = 0.05 + k * 0.065
            B.box(f"hv_l{sx}{k}", vx, y, 0.11, 0.024, 0.27, 0.30, KM, bevel=0.004, tags=tags)
            if vfl > 0 and k < 4:
                B.box(f"hv_f{sx}{k}", vx, y + 0.0325, (0.0, 0.06, 0.08, 0.09)[vfl], 0.016, 0.27, 0.278, vmat,
                      bevel=0.0, tags=tags)
        px, py = sx * 0.230, 0.15
        B.box(f"hport{sx}", px, py, 0.064, 0.36, 0.0, 0.272, KM, bevel=0.006, tags=tags)
        B.box(f"hport_k{sx}", px + sx * 0.004, py, 0.040, 0.32, 0.272, 0.276, M["black"], bevel=0.0, tags=tags)
        B.box(f"hport_l{sx}", sx * 0.2015, py, 0.008, 0.32, 0.0, 0.278, S, bevel=0.002, tags=tags)
        if hp is not None:
            B.cut(hp, [B.rbox(f"hd_pl{sx}", sx * 0.41, 0.405, 0.02, 0.09, 0.27, 0.8, K, rot=sx * 45, bevel=0.0)])
        B.bolts(f"hd_b{sx}", [(sx * 0.43, -0.065), (sx * 0.255, 0.40)], 0.325, 0.014, S, tags=tags)
        # cunha clara de baixo com a seta da saida da receita (plasma: ciano para baixo-esquerda; PEM: cobre/azul
        # para baixo-direita) num recesso escuro
        wa, wp = B.shard(f"bw{sx}", f(WEDGE), 0.0, 0.30, A, slope=0.045, groove=0.022, panel_h=0.022, tags=tags)
        ex, ey = sx * 0.375, -0.375
        for q, t in enumerate((wa, wp)):
            if t is not None:
                B.cut(t, [B.rbox(f"bw_c{sx}{q}", ex, ey, 0.10, 0.10, 0.24, 0.8, K, rot=45, bevel=0.0)])
        B.rbox(f"bw_bed{sx}", ex, ey, 0.10, 0.10, 0.235, 0.245, M["black"], rot=45, bevel=0.0, tags=tags)
        H.chevron(f"bw_ar{sx}", ex, ey, 225 if sx < 0 else 315,
                  X["pl_mid"] if sx < 0 else X["blue"], tags, z=0.245, s=0.55)
        if sx > 0:
            B.cyl("bw_cu", ex - 0.03, ey + 0.10, 0.31, 0.012, 0.10, Xm["copper"], axis="X", verts=8, bevel=0.0,
                  tags=tags)
    # alcapao de baixo: moldura escura com 2 portas que abrem para os lados
    B.plate("hatch_fr", B.rpoly(0, -0.25, 0.30, 0.28, 0, chamfer=0.04), 0.0, 0.07, KM, slope=0.01, tags=tags)
    B.box("hatch_pit", 0, -0.25, 0.22, 0.20, 0.07, 0.072, M["black"], bevel=0.0, tags=tags)
    o = 0.10 * st["hatch"]
    for sx in (-1, 1):
        B.box(f"hatch_d{sx}", sx * (0.055 + o), -0.25, 0.11, 0.20, 0.072, 0.10, AM, bevel=0.006, tags=tags)
        B.box(f"hatch_dl{sx}", sx * (0.012 + o), -0.25, 0.012, 0.16, 0.10, 0.104, M["black"], bevel=0.0, tags=tags)
    # boca do cobre (vem da base [1,2] embaixo) no meio da borda de baixo
    B.box("cu_mouth", 0, -0.445, 0.20, 0.07, 0.0, 0.05, M["black"], bevel=0.0, tags=tags)
    for g in (-1, 1):
        B.box(f"cu_g{g}", g * 0.115, -0.445, 0.022, 0.08, 0.0, 0.09, Xm["copper"], bevel=0.004, tags=tags)
    H.chevron("cu_ar", 0, -0.445, 90, M["glow_dim"], tags, z=0.05, s=0.55)
    # garras
    o = 0.07 * st["clamp"]
    for sx in (-1, 1):
        jaw = [(0.074 + o, CR_Y - 0.03), (0.20 + o, CR_Y - 0.06), (0.20 + o, CR_Y + 0.06), (0.074 + o, CR_Y + 0.03)]
        if sx < 0:
            jaw = Mo.mirror(jaw)
        B.plate(f"jaw{sx}", jaw, 0.06, 0.17, AM, slope=0.02, bevel=0.006, tags=tags)
        B.box(f"jawpad{sx}", sx * (0.084 + o), CR_Y, 0.02, 0.05, 0.06, 0.16, K, bevel=0.0, tags=tags)
    # celulas: a do berco (ou caindo pelo alcapao) e a vazia entrando pelo capuz esquerdo
    if st["cell_y"] is not None:
        H.mini_cell("cel", 0.0, st["cell_y"], CELL_Z, M, Xm, tags, "plasma", s=CELL_S, rz=0.0, level=st["level"])
    if st["in_x"] is not None:
        H.mini_cell("celi", st["in_x"], CR_Y, CELL_Z, M, Xm, tags, "plasma", s=CELL_S, rz=0.0, level=0.0)
    # pescoco do injetor e bico telescopico
    na, np_ = B.shard("neck", NECK, 0.06, 0.30, A, slope=0.04, groove=0.02, panel_h=0.02, tags=tags)
    H.ledslot("neck_sl", 0.0, 0.545, 0.04, 0.11, 0.12, 3, M, tags, [na, np_],
              pip_mat=X["pl_hi"] if st["flow"] else X["pl_tail"], pw=0.022)
    yb = 0.42 - 0.10 * st["arm"]
    rod = 0.50 - (yb + 0.075)
    B.cyl("noz_rod", 0, yb + 0.075 + rod / 2, 0.20, 0.024, rod, S, axis="Y", verts=10, bevel=0.0, tags=tags)
    B.rbox("noz_head", 0, yb + 0.04, 0.10, 0.08, 0.13, 0.27, KM, chamfer=0.022, bevel=0.006, tags=tags)
    B.box("noz_slot", 0, yb + 0.045, 0.03, 0.05, 0.27, 0.275, M["black"], bevel=0.0, tags=tags)
    B.box("noz_jet", 0, yb + 0.045, 0.012, 0.04, 0.275, 0.28, X["pl_hi"] if st["flow"] else X["pl_lo"], bevel=0.0,
          tags=tags)
    for sx in (-1, 1):
        B.box(f"noz_ear{sx}", sx * 0.058, yb + 0.05, 0.02, 0.05, 0.13, 0.25, S, bevel=0.004, tags=tags)
    if st["contact"] or st["flow"]:
        B.box("noz_tip", 0, yb - 0.006, 0.07, 0.012, 0.245, 0.253, X["pl_hi"] if st["contact"] else X["pl_mid"],
              bevel=0.0, tags=tags)


def machine(M, T="machine", phase=0.0):
    tags = (T,)
    Xm = H.X(M)
    X = _extra()
    st = _state(phase)
    B.plate("mc_bed", B.rpoly(0, 0.975, 2.90, 0.90, 0, chamfer=0.08), 0.0, 0.05, M["core"], slope=0.01, tags=tags)
    _ring(M, X, tags, st)
    _ducts(M, Xm, X, tags)
    _tanks(M, Xm, X, tags, st)
    _coils(M, Xm, X, tags, st)
    _cradle(M, Xm, X, tags, st)


# ============================================================================ teto
def roof(M, T="roof"):
    tags = (T,)
    green = H.roof_green()
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    X = _extra()
    deck = H.roof_deck(M, W, HH, skip={(1, 0), (0, 0)}, T=T)
    cx, cy = RC
    # entradas (enxofre, bobina, cobre) e saidas com a pastilha da celula
    H.roof_hatch("rf_in0", M, -1.0, 0.0, 90, deck[(0, 1)], T=T)
    H.roof_hatch("rf_in1", M, 1.0, 0.0, 90, deck[(2, 1)], T=T)
    H.roof_hatch("rf_in2", M, 0.0, -1.0, 90, deck[(1, 2)], T=T, s=0.85)
    for (i, j), kind in OUTS.items():
        px, py = H.cell_xy(W, HH, i, j)
        H.roof_hatch(f"rf_out{i}", M, px, py, 270, deck[(i, j)], T=T, chip=kind)
    # encaixe da placa de modo (canto de cima a esquerda)
    H.plate_slot("rf_plate", M, PLATE_C[0], PLATE_C[1], 0.8, [], T=T, z1=0.16)
    # base do banco PEM (canto de cima a direita): 4 batentes escuros com parafuso nos cantos do rect do banco e uma
    # regua de terminais (o banco_pem.png assenta por cima no modo PEM; no modo plasma a placa fica a mostra)
    bx, by = BANK_C
    pa, pp = deck[(2, 0)]
    for k, (dx, dy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        sx_, sy_ = bx + dx * 0.36, by + dy * 0.41
        B.box(f"rf_bk{k}", sx_, sy_, 0.10, 0.10, 0.06, 0.12, KM, bevel=0.012, tags=tags)
        B.bolts(f"rf_bkb{k}", [(sx_, sy_)], 0.12, 0.018, S, tags=tags)
    term = B.box("rf_term", bx, by, 0.12, 0.50, 0.06, 0.11, KM, bevel=0.01, tags=tags)
    for k in range(4):
        B.box(f"rf_termc{k}", bx, by - 0.18 + k * 0.12, 0.07, 0.05, 0.11, 0.125, Mo.copper_mat(), bevel=0.006,
              tags=tags)
    # emblema do toro (meio de cima, como na 1.x)
    ea, ep = B.shard("rf10", B.rpoly(0, 1.0, 0.92, 0.92, 0, chamfer=0.10), 0.0, 0.07, green, slope=0.03,
                     groove=0.05, panel_h=0.022, tags=tags)
    hole = H.octo(cx, cy, 0.47)
    for q, t in enumerate((ea, ep)):
        if t is not None:
            B.cut(t, [B.loft(f"rf_emb_h{q}", hole, hole, -0.01, 0.5, K, bevel=0.0)])
    B.plate("em_base", H.octo(cx, cy, 0.455), 0.02, 0.11, K, slope=0.02, tags=tags)
    for k in range(6):
        a = 30 + 60 * k
        sa, sp = B.shard(f"em_seg{k}", _sector(cx, cy, 0.215, 0.43, a, 24.0, c=0.035, n=1), 0.09, 0.22, A,
                         slope=0.035, groove=0.018, panel_h=0.02, tags=tags)
        if sp is not None:
            p0 = _pol(cx, cy, 0.40, a)
            B.cut(sp, [B.rbox(f"em_gr{k}", p0[0], p0[1], 0.02, 0.10, 0.20, 0.6, K, rot=a - 90, bevel=0.0)])
        B.bolts(f"em_b{k}", [_pol(cx, cy, 0.27, a + s_) for s_ in (-14, 14)], 0.245, 0.012, S, tags=tags)
    for k in range(6):
        a = 30 + 60 * k
        p0 = _pol(cx, cy, 0.182, a)
        B.rbox(f"em_glow{k}", p0[0], p0[1], 0.15, 0.014, 0.11, 0.116, X["em_ring"], rot=a + 90, bevel=0.0,
               tags=tags)
    B.plate("em_hub", H.octo(cx, cy, 0.15), 0.09, 0.19, AM, slope=0.025, tags=tags)
    B.plate("em_hub2", H.octo(cx, cy, 0.085, 0), 0.19, 0.23, S, slope=0.012, tags=tags)
    B.bolts("em_hb", B.ring_points(cx, cy, 0.118, 6, math.radians(30)), 0.195, 0.012, S, tags=tags)
    B.cyl("em_eye", cx, cy, 0.232, 0.025, 0.006, M["glow_dim"], axis="Z", verts=8, bevel=0.0, tags=tags)
    # espinha do injetor do anel ate a escotilha do berco
    spine = [(-0.12, 0.62), (0.12, 0.62), (0.12, 0.46), (0.07, 0.40), (-0.07, 0.40), (-0.12, 0.46)]
    sa, sp = B.shard("sp", spine, 0.06, 0.22, A, slope=0.035, groove=0.018, panel_h=0.02, tags=tags)
    H.ledslot("sp_sl", 0.0, 0.52, 0.05, 0.16, 0.10, 3, M, tags, [sa, sp], pw=0.024, pip_mat=M["glow_dim"])
    # escotilha em capsula sobre o berco
    pa, pp = deck[(1, 1)]
    cap = [(-0.10, -0.40), (0.10, -0.40), (0.20, -0.30), (0.20, 0.30), (0.10, 0.40), (-0.10, 0.40), (-0.20, 0.30),
           (-0.20, -0.30)]
    for sx in (-1, 1):
        clamp = [(0.23, -0.20), (0.36, -0.28), (0.40, -0.24), (0.40, 0.24), (0.36, 0.28), (0.23, 0.20)]
        cl = clamp if sx > 0 else Mo.mirror(clamp)
        B.plate(f"hc_cl{sx}", B.offset_poly(cl, -0.025), 0.06, 0.10, K, slope=0.01, tags=tags)
        B.shard(f"hc_clamp{sx}", cl, 0.09, 0.17, AM, slope=0.03, groove=0.015, panel_h=0.015, tags=tags)
        B.bolts(f"hc_cb{sx}", [(sx * 0.33, -0.16), (sx * 0.33, 0.16)], 0.19, 0.014, S, tags=tags)
    B.plate("hc_core", B.offset_poly(cap, -0.03), 0.06, 0.12, K, slope=0.012, tags=tags)
    ha, hp = B.shard("hc", cap, 0.10, 0.24, A, slope=0.045, groove=0.022, panel_h=0.025, tags=tags)
    H.ledslot("hc_win", 0.0, 0.0, 0.07, 0.30, 0.12, 4, M, tags, [ha, hp], pw=0.034, pip_mat=M["glow_dim"])
    for sy in (-1, 1):
        y = sy * 0.255
        B.box(f"hc_dr{sy}", 0, y, 0.43, 0.05, 0.10, 0.262, X["drum"], bevel=0.006, tags=tags)
        B.box(f"hc_sk{sy}", 0, y, 0.40, 0.018, 0.262, 0.265, M["black"], bevel=0.0, tags=tags)
        B.box(f"hc_seam{sy}", 0, y, 0.37, 0.009, 0.265, 0.268, X["pl_tail"], bevel=0.0, tags=tags)
        for j, dy in enumerate((-0.033, 0.033)):
            B.box(f"hc_band{sy}{j}", 0, y + dy, 0.45, 0.02, 0.10, 0.272, S, bevel=0.005, tags=tags)
    H.roof_unpaint(T)


# ============================================================================ camadas extras: banco PEM
def _bank(M, Xm, X, tags, phase=None):
    """Banco de bobinas de cobre do modo PEM (sobre o teto): base escura chanfrada, 3 colunas de bobinas de cobre
    em pe (espiras com frestas escuras), tampas claras em cima e embaixo com os bornes, regua de LEDs azuis.
    phase = None: frestas apagadas (lentes escuras, o difuso); k/4: a onda azul de baixo para cima (luz)."""
    K, KM, A, AM, S = M["core"], M["core_mid"], M["armor"], M["armor_mid"], M["steel"]
    bx, by = BANK_C
    base = B.rpoly(bx, by, 0.86, 0.96, 0, chamfer=0.10)
    B.plate("bk_base", base, 0.10, 0.18, K, slope=0.02, tags=tags)
    rim = B.plate("bk_rim", base, 0.18, 0.22, AM, slope=0.015, tags=tags)
    B.cut(rim, [B.loft("bk_rimc", B.offset_poly(base, 0.05), B.offset_poly(base, 0.05), 0.1, 0.5, K, bevel=0.0)])
    nrow = 8
    for c, x in enumerate((bx - 0.24, bx, bx + 0.24)):
        y0, y1 = by - 0.30, by + 0.30
        B.cyl(f"bk_core{c}", x, by, 0.30, 0.075, y1 - y0 + 0.04, KM, axis="Y", verts=8, bevel=0.0, tags=tags)
        for j in range(nrow):
            yy = y0 + (j + 0.5) * (y1 - y0) / nrow
            B.cyl(f"bk_cu{c}{j}", x, yy, 0.30, 0.092, (y1 - y0) / nrow - 0.016, Xm["copper"], axis="Y", verts=12,
                  bevel=0.003, tags=tags)
            if j < nrow - 1:
                yg = y0 + (j + 1) * (y1 - y0) / nrow
                lit = phase is not None and (j - int(round(phase * 4)) * 2) % 8 in (0, 1)
                mat = X["blue"] if lit else (X["blue_lo"] if phase is not None and j % 2 == 0 else K)
                B.box(f"bk_gap{c}{j}", x, yg, 0.11, 0.010, 0.30 + 0.088, 0.30 + 0.094, mat, bevel=0.0, tags=tags)
        for sy in (-1, 1):
            cap = B.rpoly(x, by + sy * 0.355, 0.20, 0.10, 0, chamfer=0.03)
            B.shard(f"bk_cap{c}{sy}", cap, 0.18, 0.40, A, slope=0.03, groove=0.012, panel_h=0.012, tags=tags)
            B.cyl(f"bk_post{c}{sy}", x, by + sy * 0.355, 0.42, 0.028, 0.03, Xm["copper"], axis="Z", verts=8,
                  bevel=0.004, tags=tags)
    # barramento de cobre ligando os bornes de cima
    B.box("bk_bus", bx, by + 0.355, 0.56, 0.026, 0.43, 0.45, Xm["copper"], bevel=0.005, tags=tags)
    for sx in (-1, 1):
        B.bolts(f"bk_b{sx}", [(bx + sx * 0.385, by - 0.43), (bx + sx * 0.385, by + 0.43)], 0.22, 0.016, S, tags=tags)


def banco_pem(M, T="banco_pem", **kw):
    _bank(M, H.X(M), _extra(), (T,), phase=None)


def banco_pem_luz(M, T="banco_pem_luz", phase=0.0, **kw):
    _bank(M, H.X(M), _extra(), (T,), phase=phase)
