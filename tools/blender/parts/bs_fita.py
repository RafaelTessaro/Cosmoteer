"""Fita de Alimentacao (2.0, primario): a peca 1x1 que o jogador GRUDA do lado de uma fabrica, paiol ou arma.

    $PY tools/blender/render_layered.py bs_fita [--only roof,luz_grudada] [--quick] [--out DIR]

Pedido do usuario (USER_NOTES 2026-10-21): nada de esteira fisica; uma peca "fita" que gruda na maquina e a municao
TELETRANSPORTA de uma maquina para outra ("imagina que tem uma esteira por baixo da nave, mas nao tem"). Spec de
arte: assets.fita (TF/parts/bs2f_fita como molde: mesmos nomes de arquivo).

Linguagem visual (STYLE.md 1, adaptada a uma peca pequena e simetrica; a peca NAO gira, IsRotateable = false, e
gruda em qualquer um dos 4 lados, entao o desenho tem simetria de 4):
  * teto: placa do convés pintada (verde = pintura da nave) com bisel duplo; no meio a TAMPA BLINDADA octogonal
    clara de bisel duplo com o SIMBOLO DA FITA em baixo relevo: um cartucho estilizado (estojo de latao, ponta de
    aco) num rebaixo preto, e 4 setas cortadas apontando para os 4 lados (a fita "manda" para qualquer vizinho);
  * 4 GARRAS de aco nas bordas (uma por lado, dois dentes claros que vao ate a borda da peca e "mordem" a maquina
    vizinha) com a LENTE verde entre os dentes, num rebaixo escuro;
  * piso (interior): base escura, plataforma de teletransporte octogonal (anel de aco com 8 emissores e um anel
    ciano MUITO fraco), trilho curto em cruz ate as garras do piso, cada garra com o LED verde da ligacao.
Luzes da ligacao (acendem com o buff BulletStrike_FitaAck, componente LuzGrudada):
  * luz_grudada.png (lights_add, spec): os 4 LEDs verdes das garras do piso, aditivo (vista do interior);
  * luz_grudada_teto.png (roof_doodads, EXTRA desta arte): as 4 lentes das garras do teto acesas em verde, com
    alfa; com o teto ligado o lights_add fica embaixo do teto e o jogador nao veria a luz verde. Mesmo toggle.
"""

import math

import bs3d as B
import models as Mo
from parts import _bs2_logistica_helpers as LG

_NOTE_LUZ = ("luz_grudada.png (lights_add, rect [0,0,1,1]): os 4 LEDs verdes das garras do PISO (vista do interior). "
             "luz_grudada_teto.png (roof_doodads, rect [0,0,1,1], alfa): as 4 lentes das garras do TETO acesas; ligue "
             "as duas no mesmo OperationalToggle Grudada (com o teto ligado o lights_add fica embaixo do teto). O verde "
             "e (0.16, 1.0, 0.0) linear: |r - b| grande, o shader de pintura nunca o trata como tinta.")

PART = {
    "id": "rafaeltessaro.bs_fita", "kind": "layered", "size": [1, 1], "accent": "green",
    "walls": "none",                                  # peca fechada sem paredes (como o cano de calor vanilla)
    "layers": [
        {"name": "floor", "fn": "fita_floor", "game_layer": "floors", "opaque": True, "file": "floor.png"},
        {"name": "luz_grudada", "fn": "fita_floor_leds", "game_layer": "lights_add", "file": "luz_grudada.png",
         "emission_only": True, "blend": "add", "halo_px": 2.5, "gain": 1.0, "islands": True},
        {"name": "roof", "fn": "fita_roof", "game_layer": "roofs", "file": "roof.png", "normals": True,
         "despill": True, "samples": 64},
        {"name": "luz_teto", "fn": "fita_roof_leds", "game_layer": "roof_doodads", "file": "luz_grudada_teto.png",
         "emission_only": True, "blend": "alpha", "halo_px": 2.0, "gain": 1.0, "islands": True},
    ],
    "icon": {"size": [32, 32], "layers": ["floor", "roof", "luz_teto"]},
    "blueprint_layers": ["roof"],
    "notes": [_NOTE_LUZ,
              "Sem walls.png (walls 'none'): peca fechada como o cano de calor vanilla (heat_pipe_adaptive.rules:15-25).",
              "icon.png 32 x 32 (EditorIcon Size [32, 32]); blueprints.png 64 x 64."],
}

R_LID = 0.30                          # raio do octogono da tampa (vertice)
LENS_R = 0.428                        # distancia do centro ate a lente de cada garra (teto e piso: a mesma)
Z_DECK = 0.06


def _oct(r, a0=22.5):
    return [(r * math.cos(math.radians(a0 + 45 * k)), r * math.sin(math.radians(a0 + 45 * k))) for k in range(8)]


# ============================================================================ teto
def _cartridge(cx, cy, s=1.0):
    """Contornos do cartucho estilizado (ponta para cima): ponta (ogiva de aco) e estojo (latao com aro)."""
    w = 0.092 * s
    tip, yb, y0, yr = cy + 0.122 * s, cy + 0.035 * s, cy - 0.088 * s, cy - 0.118 * s
    right = [(cx + (w / 2) * math.sqrt(1 - (1 - t) ** 2), tip - (tip - yb) * t) for t in (0.2, 0.4, 0.6, 0.8, 1.0)]
    nose = [(cx, tip)] + right + [(2 * cx - x, y) for x, y in reversed(right)]
    case =[(cx - w / 2, yb - 0.012 * s), (cx + w / 2, yb - 0.012 * s), (cx + w / 2, y0), (cx + w / 2 + 0.012 * s, y0),
            (cx + w / 2 + 0.012 * s, yr), (cx - w / 2 - 0.012 * s, yr), (cx - w / 2 - 0.012 * s, y0), (cx - w / 2, y0)]
    return nose, case


def fita_roof(M, T="roof", **kw):
    """Teto: convés pintado, tampa blindada com o simbolo da fita, 4 garras com lentes (apagadas)."""
    tags = (T,)
    X = LG.mats(M)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    green = B.mat_roof_green()
    B.box("deck_under", 0, 0, 1, 1, -0.05, 0.02, K, bevel=0.0, tags=tags)
    deck = B.rpoly(0, 0, 0.94, 0.94, 0, chamfer=0.075)
    da, dp = B.shard("deck", deck, 0.0, Z_DECK, green, slope=0.025, groove=0.05, panel_h=0.02, tags=tags)
    if dp is not None:                # linhas de painel nos 4 cantos (entre as garras)
        B.cut(dp, [B.rbox(f"dpl{k}", sx * 0.34, sy * 0.34, 0.012, 0.15, 0.07, 0.3, K, rot=-sx * sy * 45, bevel=0.0)
                   for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1)))])
    for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        B.cyl(f"dbolt{k}", sx * 0.385, sy * 0.385, Z_DECK + 0.025, 0.018, 0.016, S, axis="Z", verts=10, bevel=0.004,
              tags=tags)

    # ---------------------------------------------------------------- 4 garras (dentes claros + ponte escura + lente)
    for k in range(4):
        base = LG.rot4([(-0.135, 0.235), (0.135, 0.235), (0.115, 0.345), (-0.115, 0.345)], k)
        B.plate(f"claw_base{k}", base, Z_DECK - 0.01, Z_DECK + 0.07, S, slope=0.015, tags=tags)
        for j, sx in enumerate((-1, 1)):
            tooth = [(sx * 0.050, 0.300), (sx * 0.112, 0.300), (sx * 0.112, 0.440), (sx * 0.088, 0.492),
                     (sx * 0.050, 0.492)]
            if sx > 0:
                tooth = list(reversed(tooth))
            B.plate(f"claw_t{k}{j}", LG.rot4(tooth, k), Z_DECK - 0.01, Z_DECK + 0.095, A, slope=0.014, bevel=0.006,
                    tags=tags)
        bridge = LG.rot4([(-0.052, 0.36), (0.052, 0.36), (0.052, 0.478), (-0.052, 0.478)], k)
        B.loft(f"claw_br{k}", bridge, bridge, Z_DECK - 0.01, Z_DECK + 0.045, KM, bevel=0.004, tags=tags)
        lx, ly = LG.rot4([(0.0, LENS_R)], k)[0]
        lens = B.rpoly(lx, ly, 0.066, 0.066, 0, chamfer=0.014)
        B.loft(f"lens_bed{k}", lens, lens, Z_DECK + 0.045, Z_DECK + 0.050, M["black"], bevel=0.0, tags=tags)
        inner = B.rpoly(lx, ly, 0.046, 0.046, 0, chamfer=0.010)
        B.loft(f"lens{k}", inner, inner, Z_DECK + 0.050, Z_DECK + 0.058, X["lens_off"], bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- tampa blindada com o simbolo da fita
    z0, z1 = Z_DECK, Z_DECK + 0.10
    la, lp = B.shard("lid", _oct(R_LID), z0, z1, A, slope=0.032, groove=0.018, panel_h=0.022, tags=tags)
    ztop = z1 + 0.022
    nose, case = _cartridge(0.0, 0.0)
    # rebaixo do simbolo: contorno do cartucho alargado (vao preto em volta), fundo escuro
    hole_n, hole_c = B.offset_poly(nose, -0.016), B.offset_poly(case, -0.016)
    for t in (la, lp):
        if t is not None:
            B.cut(t, [B.loft(f"emb_cn{t.name}", hole_n, hole_n, ztop - 0.045, 0.9, K, bevel=0.0),
                      B.loft(f"emb_cc{t.name}", hole_c, hole_c, ztop - 0.045, 0.9, K, bevel=0.0)])
    B.loft("emb_bed_n", hole_n, hole_n, ztop - 0.050, ztop - 0.044, M["black"], bevel=0.0, tags=tags)
    B.loft("emb_bed_c", hole_c, hole_c, ztop - 0.050, ztop - 0.044, M["black"], bevel=0.0, tags=tags)
    # o cartucho em baixo relevo (abaixo do topo da tampa): ponta de aco, estojo de latao com o sulco do aro
    B.plate("emb_nose", nose, ztop - 0.046, ztop - 0.012, S, slope=0.008, bevel=0.003, tags=tags)
    cs = B.plate("emb_case", case, ztop - 0.046, ztop - 0.014, X["brass"], slope=0.008, bevel=0.003, tags=tags)
    B.cut(cs, [B.box("emb_rim", 0, -0.094, 0.2, 0.010, ztop - 0.03, 0.9, K, bevel=0.0)])
    # 4 setas cortadas na tampa apontando para as garras (a fita manda para qualquer vizinho)
    for k in range(4):
        arrow = LG.rot4([(-0.042, 0.168), (0.042, 0.168), (0.0, 0.222)], k)
        for t in (la, lp):
            if t is not None:
                B.cut(t, [B.loft(f"arr_c{k}{t.name}", arrow, arrow, ztop - 0.05, 0.9, K, bevel=0.0)])
        B.loft(f"arr_bed{k}", arrow, arrow, ztop - 0.056, ztop - 0.050, M["black"], bevel=0.0, tags=tags)
        tri = LG.rot4([(-0.022, 0.176), (0.022, 0.176), (0.0, 0.204)], k)
        B.loft(f"arr_pip{k}", tri, tri, ztop - 0.050, ztop - 0.044, KM, bevel=0.0, tags=tags)


def fita_roof_leds(M, T="luz_teto", **kw):
    """So as 4 lentes das garras do teto, acesas em verde (luz_grudada_teto.png, roof_doodads com alfa)."""
    X = LG.mats(M)
    for k in range(4):
        lx, ly = LG.rot4([(0.0, LENS_R)], k)[0]
        inner = B.rpoly(lx, ly, 0.046, 0.046, 0, chamfer=0.010)
        B.loft(f"lens_on{k}", inner, inner, Z_DECK + 0.050, Z_DECK + 0.058, X["link"], bevel=0.0, tags=(T,))


# ============================================================================ piso (interior)
FLOOR_LED_Z = 0.075


def fita_floor(M, T="floor", **kw):
    """Piso: base escura, plataforma de teletransporte, trilho curto em cruz, 4 garras com LED (apagado)."""
    tags = (T,)
    X = LG.mats(M)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    B.box("fl_base", 0, 0, 1, 1, -0.05, 0.0, K, bevel=0.0, tags=tags)
    B.box("fl_plate", 0, 0, 0.92, 0.92, 0.0, 0.03, KM, bevel=0.01, tags=tags)
    # trilho curto em cruz: 2 trilhos de aco + dormentes, da plataforma ate as garras
    for k in range(4):
        for j, sx in enumerate((-1, 1)):
            rail = LG.rot4([(sx * 0.036 - 0.009, 0.20), (sx * 0.036 + 0.009, 0.20), (sx * 0.036 + 0.009, 0.37),
                            (sx * 0.036 - 0.009, 0.37)], k)
            B.loft(f"rail{k}{j}", rail, rail, 0.03, 0.052, S, bevel=0.003, tags=tags)
        for i in range(3):
            sl = LG.rot4([(-0.07, 0.235 + i * 0.05), (0.07, 0.235 + i * 0.05), (0.07, 0.255 + i * 0.05),
                          (-0.07, 0.255 + i * 0.05)], k)
            B.loft(f"sleeper{k}{i}", sl, sl, 0.03, 0.042, AM, bevel=0.002, tags=tags)
    # plataforma de teletransporte: anel de aco octogonal, 8 emissores, poco escuro e anel ciano muito fraco
    B.plate("pad", _oct(0.25), 0.03, 0.075, AM, slope=0.02, tags=tags)
    B.plate("pad_well", _oct(0.185), 0.074, 0.080, M["black"], slope=0.0, bevel=0.0, tags=tags)
    for i, (x, y) in enumerate(B.ring_points(0, 0, 0.215, 8, math.radians(22.5))):
        B.cyl(f"emit{i}", x, y, 0.088, 0.016, 0.02, AM, axis="Z", verts=8, bevel=0.003, tags=tags)
    B.torus("pad_ring", 0, 0, 0.082, 0.125, 0.008, X["tele_dim"], tags=tags)
    B.cyl("pad_core", 0, 0, 0.083, 0.035, 0.008, X["tele_dim"], axis="Z", verts=16, bevel=0.0, tags=tags)
    # garras do piso: base de aco com 2 dentes ate a borda e o LED verde (apagado) num rebaixo
    for k in range(4):
        base = LG.rot4([(-0.12, 0.375), (0.12, 0.375), (0.12, 0.40), (-0.12, 0.40)], k)
        B.loft(f"fclaw_b{k}", base, base, 0.03, 0.07, AM, bevel=0.004, tags=tags)
        for j, sx in enumerate((-1, 1)):
            tooth = LG.rot4([(sx * 0.058 - 0.026, 0.40), (sx * 0.058 + 0.026, 0.40), (sx * 0.058 + 0.026, 0.49),
                             (sx * 0.058 - 0.026, 0.49)], k)
            B.loft(f"fclaw_t{k}{j}", tooth, tooth, 0.03, 0.07, S, bevel=0.005, tags=tags)
        lx, ly = LG.rot4([(0.0, LENS_R)], k)[0]
        B.box(f"fled_bed{k}", lx, ly, 0.05, 0.05, 0.03, FLOOR_LED_Z - 0.005, M["black"], bevel=0.0, tags=tags)
        B.box(f"fled{k}", lx, ly, 0.032, 0.032, FLOOR_LED_Z - 0.005, FLOOR_LED_Z, X["lens_off"], bevel=0.0, tags=tags)
    for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        B.cyl(f"fbolt{k}", sx * 0.40, sy * 0.40, 0.035, 0.016, 0.012, S, axis="Z", verts=10, bevel=0.003, tags=tags)


def fita_floor_leds(M, T="luz_grudada", **kw):
    """So os 4 LEDs verdes das garras do piso (luz_grudada.png, lights_add aditivo)."""
    X = LG.mats(M)
    for k in range(4):
        lx, ly = LG.rot4([(0.0, LENS_R)], k)[0]
        B.box(f"fled_on{k}", lx, ly, 0.034, 0.034, FLOOR_LED_Z - 0.005, FLOOR_LED_Z + 0.002, X["link"], bevel=0.0,
              tags=(T,))
