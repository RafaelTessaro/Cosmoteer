"""Paiois (2.0): 4 familias x 3 tamanhos = 12 pecas numa pasta so (art3d/bs_paiol -> parts/bs_paiol_comum/).

    $PY tools/blender/render_layered.py bs_paiol [--part bs_paiol_2x2] [--only roof,gauge] [--quick] [--out DIR]
    (renderize bs_placas antes: o icone de cada paiol cola a placa padrao da familia, lida de ../bs_placas/)

Spec de arte assets.paiol (+ SPEC_2.0 paiol): paiol SELADO como a bateria termica vanilla (sem escotilha de
tripulacao; IsRotateable = false, entao placa, digitos e medidor ficam sempre em pe). Familias: cartuchos (HE, AP,
SAP, AC, FRAG), celulas (plasma, PEM), misseis (HE, submunicao, PEM, ogiva nuclear) e projeteis (slug do Tupa).

Arquivos por tamanho <n> = 1x1 | 2x2 | 3x3 (nomes do spec):
  floor_<n>.png                  piso: estantes de cassetes neutros no perimetro + corredor central livre com a
                                 plataforma de teletransporte (tambem serve para o modo tripulacao: sala andavel)
  walls_<n>.png                  moldura fechada (vanilla)
  roof_<fam>_<n>.png (+ normals) tampa blindada SELADA pintada (verde = pintura), janela do medidor, encaixe da
                                 placa, janela dos digitos (2x2/3x3) e o chip da familia (faixa de 3 px na cor
                                 palette.family_chip, sem emissao) na borda de baixo da tampa; travas de vedacao,
                                 paineis de alivio (2x2/3x3) e costuras. Os segmentos APAGADOS do medidor e dos
                                 digitos ja vem pintados nas janelas (post roof_post): o medidor vazio e o teto.
  gauge_<n>_<k>.png              roof_doodads, ResourceSprites (Round Up, HasZeroResourceSprite false), k = 1..N
                                 (N = 5 / 8 / 10): segmentos de baixo para cima com 1 px de vao e 2 px de margem,
                                 cor do nivel f = k / N: f <= 0,5 low -> high, f > 0,5 high -> full
  icon_<fam>_<n>.png             EditorIcon (64 px por quadro): teto pintado de cinza + medidor cheio + a placa padrao
  blueprints_<n>.png             um por tamanho
  digito0..9.png                 EXTRA (switch paiol_counter): 24 x 40 px, segmentos ambar acesos so (os apagados
                                 estao no teto); a mesma geometria dos segmentos apagados (helpers.seg_poly)
A placa do tipo (placa_<tipo>.png, art3d/bs_placas) e desenhada pelas regras em cima do encaixe (meta "plate").
"""

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import bs3d as B
import models as Mo
from parts import _bs2_logistica_helpers as LG

FAMS = ["cartuchos", "celulas", "misseis", "projeteis"]
DEFAULT_KIND = {"cartuchos": "he", "celulas": "plasma", "misseis": "msl_he", "projeteis": "slug"}
# SPEC_2.0 art_assets.assets.paiol.layout_tiles (coordenadas da peca, +y para baixo)
LAYOUT = {
    "1x1": {"gauge_rect": [0.68, 0.12, 0.2, 0.76], "plate_centre": [0.32, 0.5], "plate_size": 0.42, "digits": None,
            "levels": 5},
    "2x2": {"gauge_rect": [1.58, 0.16, 0.26, 1.68], "plate_centre": [0.62, 0.62], "plate_size": 0.66,
            "digits": {"centres_x": [0.3, 0.55, 0.8, 1.05], "y": 1.55, "size": [0.22, 0.36]}, "levels": 8},
    "3x3": {"gauge_rect": [2.46, 0.2, 0.34, 2.6], "plate_centre": [0.85, 0.85], "plate_size": 0.92,
            "digits": {"centres_x": [0.4, 0.74, 1.08, 1.42], "y": 2.45, "size": [0.3, 0.5]}, "levels": 10},
}
SS_PIL = 4
DIGIT_PX = (24, 40)
AMBER_DIGIT = (255, 170, 40)          # palette.boiuna_amber.led (o ambar dos LEDs da familia)
UNLIT_SEG = (34, 38, 45)              # celula do medidor apagada (vidro escuro)
UNLIT_DIGIT = (50, 43, 34)            # segmento de digito apagado, fraco
FREE_PAD = {"1x1": 0.17, "2x2": 0.30, "3x3": 0.42}   # raio da plataforma de teletransporte no corredor
RACK = {"1x1": 0.19, "2x2": 0.25, "3x3": 0.30}       # profundidade das estantes do perimetro


def digit_rects(n):
    d = LAYOUT[n]["digits"]
    if not d:
        return []
    w, h = d["size"]
    return [[round(cx - w / 2, 4), round(d["y"] - h / 2, 4), w, h] for cx in d["centres_x"]]


def plate_rect(n):
    L = LAYOUT[n]
    s = L["plate_size"]
    cx, cy = L["plate_centre"]
    return [round(cx - s / 2, 4), round(cy - s / 2, 4), s, s]


def _part(n):
    W = int(n[0])
    L = LAYOUT[n]
    N = L["levels"]
    layers = [
        {"name": "floor", "fn": f"floor_{n}", "game_layer": "floors", "opaque": True, "file": f"floor_{n}.png"},
        {"name": "roof", "fn": f"roof_{n}", "game_layer": "roofs", "file": "roof_{v}_" + n + ".png",
         "variants": list(FAMS), "normals": True, "despill": True, "post": "roof_post", "samples": 64},
        {"name": "gauge", "fn": "pil:gauge", "game_layer": "roof_doodads", "rect": list(L["gauge_rect"]),
         "file": f"gauge_{n}_" + "{i}.png", "levels": N, "islands": True},
    ]
    dr = digit_rects(n)
    if dr:
        layers.append({"name": "digitos", "fn": "pil:digit", "game_layer": "roof_doodads", "rect": dr[0],
                       "at": [r[:2] for r in dr], "px": list(DIGIT_PX), "file": "digito{v}.png",
                       "variants": [str(i) for i in range(10)], "islands": True})
    plates = {f: [f"placa_{k}.png" for k in LG.FAMILY_KINDS[f]] for f in FAMS}
    return {
        "id": f"rafaeltessaro.bs_paiol_{n}", "kind": "layered", "size": [W, W], "accent": "amber",
        "folder": "bs_paiol", "sub": n, "folder_id": "rafaeltessaro.bs_paiol_comum",
        "walls": "closed", "walls_file": f"walls_{n}.png", "blueprints_file": f"blueprints_{n}.png",
        "layers": layers,
        "icon": {"file": "icon_{v}_" + n + ".png", "per_variant": "roof", "ppt": 64,
                 "layers": ["floor", "roof", "gauge"], "pick": {"gauge": N - 1}, "extra": "icon_extra"},
        "blueprint_layers": ["roof"],
        "meta_extra": {
            "ids": {f: f"rafaeltessaro.bs_paiol_{f}_{n}" for f in FAMS},
            "plate": {"rect": plate_rect(n), "game_layer": "roof_doodads", "source": "bs_placas",
                      "files": plates, "native_px": [48, 48]},
            "gauge_levels": N,
            "family_chip": {f: list(LG.FAMILY_CHIP[f]) for f in FAMS},
            "digits": {"rects": dr, "files": [f"digito{i}.png" for i in range(10)], "switch": "paiol_counter",
                       "publish_as": "gui/digitos/digito<i>.png"} if dr else None,
        },
        "notes": [
            f"Paiol {n}: as 4 familias usam o mesmo piso, paredes, medidor e blueprint; so o teto (chip da familia) e "
            f"o icone mudam: roof_<familia>_{n}.png / icon_<familia>_{n}.png.",
            f"gauge_{n}_1..{N}.png: ResourceSprites em roof_doodads no rect {L['gauge_rect']} (Round Up, "
            "HasZeroResourceSprite = false: o medidor vazio e o teto, que ja traz os segmentos apagados).",
            "placa: placa_<tipo>.png (art3d/bs_placas) no rect 'plate' (roof_doodads), ToggledComponents por modo do "
            "seletor (MostradorTipo_<k>); projeteis = placa fixa (placa_slug.png).",
            "digitos (opcional, switch paiol_counter): 4 ValueSprites com digito0..9.png (24 x 40) nos rects de "
            "'digits'; os segmentos apagados ja estao pintados na janela do teto.",
        ],
    }


PARTS = {f"bs_paiol_{n}": _part(n) for n in ("1x1", "2x2", "3x3")}


# ============================================================================ utilidades
def _c(n, x, y):
    """Coordenadas da peca (x direita, y para baixo) -> modelo (centrado, y para cima)."""
    W = int(n[0])
    return x - W / 2, W / 2 - y


def _rect_poly(n, rx, ry, rw, rh, chamfer=0.0, grow=0.0):
    cx, cy = _c(n, rx + rw / 2, ry + rh / 2)
    return B.rpoly(cx, cy, rw + 2 * grow, rh + 2 * grow, 0, chamfer=chamfer)


def _family_mat(fam):
    c = LG.lin(LG.FAMILY_CHIP[fam])
    m = B.mat_metal(f"lg_chip_{fam}", c, rough=0.55, metal=0.15)
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.25
    return m


# ============================================================================ teto
Z_RIM, Z_LID = 0.05, 0.075            # aro da tampa / topo do painel elevado (+panel_h)


def _roof(M, T, n, fam):
    tags = (T,)
    X = LG.mats(M)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    green = B.mat_roof_green()
    W = int(n[0])
    L = LAYOUT[n]
    B.box("deck_under", 0, 0, W, W, -0.05, 0.02, K, bevel=0.0, tags=tags)
    # tampa SELADA: uma placa so (aro chanfrado + painel elevado, bisel duplo), costuras nas emendas dos quadros
    lid = B.rpoly(0, 0, W - 0.05, W - 0.05, 0, chamfer=0.10 + 0.03 * W)
    la, lp = B.shard("lid", lid, 0.0, Z_RIM, green, slope=0.03, groove=0.065, panel_h=0.025, tags=tags)
    ztop = Z_RIM + 0.025
    seams = []
    for k in range(1, W):
        x, _ = _c(n, k, 0)
        seams.append(B.box(f"seamx{k}", x, 0, 0.016, W - 0.3, ztop - 0.016, 0.5, K, bevel=0.0))
        _, y = _c(n, 0, k)
        seams.append(B.box(f"seamy{k}", 0, y, W - 0.3, 0.016, ztop - 0.016, 0.5, K, bevel=0.0))
    if lp is not None and seams:
        B.cut(lp, seams)

    # ---------------------------------------------------------------- medidor: carcaca clara + janela escura
    gx, gy, gw, gh = L["gauge_rect"]
    house = _rect_poly(n, gx, gy, gw, gh, chamfer=0.035, grow=0.045)
    ha, hp = B.shard("g_house", house, ztop - 0.01, ztop + 0.05, A, slope=0.018, groove=0.012, panel_h=0.014,
                     tags=tags)
    win = _rect_poly(n, gx, gy, gw, gh)
    for t in (ha, hp, la, lp):
        if t is not None:
            B.cut(t, [B.loft(f"g_win{t.name}", win, win, Z_RIM - 0.02, 0.6, K, bevel=0.0)])
    B.loft("g_bed", win, win, Z_RIM - 0.02, Z_RIM - 0.012, X["glass"], bevel=0.0, tags=tags)
    # parafusos da carcaca (em cima e embaixo)
    for k, yy in enumerate((gy - 0.024, gy + gh + 0.024)):
        bx, by = _c(n, gx + gw / 2, yy)
        B.cyl(f"g_bolt{k}", bx, by, ztop + 0.068, 0.016, 0.014, S, axis="Z", verts=10, bevel=0.004, tags=tags)

    # ---------------------------------------------------------------- encaixe da placa (rebaixo escuro com labio)
    pr = plate_rect(n)
    sock = _rect_poly(n, *pr, chamfer=0.05, grow=0.05)
    sa, sp = B.shard("sock", sock, ztop - 0.01, ztop + 0.035, AM, slope=0.016, groove=0.010, panel_h=0.012,
                     tags=tags)
    hole = _rect_poly(n, *pr, chamfer=0.04, grow=0.006)
    for t in (sa, sp, la, lp):
        if t is not None:
            B.cut(t, [B.loft(f"s_hole{t.name}", hole, hole, Z_RIM - 0.015, 0.6, K, bevel=0.0)])
    B.loft("s_bed", hole, hole, Z_RIM - 0.015, Z_RIM - 0.008, M["black"], bevel=0.0, tags=tags)
    # 4 garras pequenas segurando a placa (cantos do encaixe)
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        cx, cy = _c(n, pr[0] + pr[2] / 2 + sx * (pr[2] / 2 + 0.03), pr[1] + pr[3] / 2 + sy * (pr[3] / 2 + 0.03))
        B.rbox(f"s_clip{k}", cx, cy, 0.05, 0.05, ztop + 0.03, ztop + 0.05, S, rot=45, bevel=0.004, tags=tags)

    # ---------------------------------------------------------------- janela dos digitos (2x2 / 3x3)
    dr = digit_rects(n)
    if dr:
        x0, x1 = dr[0][0] - 0.02, dr[-1][0] + dr[-1][2] + 0.02
        y0, y1 = dr[0][1] - 0.02, dr[0][1] + dr[0][3] + 0.02
        dh = _rect_poly(n, x0, y0, x1 - x0, y1 - y0, chamfer=0.03, grow=0.04)
        da, dp = B.shard("d_house", dh, ztop - 0.01, ztop + 0.04, A, slope=0.016, groove=0.010, panel_h=0.012,
                         tags=tags)
        dw = _rect_poly(n, x0, y0, x1 - x0, y1 - y0, chamfer=0.015)
        for t in (da, dp, la, lp):
            if t is not None:
                B.cut(t, [B.loft(f"d_win{t.name}", dw, dw, Z_RIM - 0.02, 0.6, K, bevel=0.0)])
        B.loft("d_bed", dw, dw, Z_RIM - 0.02, Z_RIM - 0.012, X["glass"], bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- chip da familia (faixa de 3 px, sem emissao)
    cx0 = 0.14
    cx1 = (gx - 0.10) if W == 1 else (gx - 0.12)
    cy = W - 0.12
    ch = 3.2 / 64
    chan = _rect_poly(n, cx0, cy - ch / 2, cx1 - cx0, ch, grow=0.012)
    for t in (la, lp):
        if t is not None:
            B.cut(t, [B.loft(f"chip_c{t.name}", chan, chan, Z_RIM - 0.03, 0.6, K, bevel=0.0)])
    B.loft("chip_bed", chan, chan, Z_RIM - 0.03, Z_RIM - 0.024, M["black"], bevel=0.0, tags=tags)
    strip = _rect_poly(n, cx0, cy - ch / 2, cx1 - cx0, ch)
    B.loft("chip", strip, strip, Z_RIM - 0.024, Z_RIM + 0.004, _family_mat(fam), bevel=0.003, tags=tags)

    # ---------------------------------------------------------------- travas de vedacao no aro (cima e esquerda)
    dogs = {"1x1": [(0.20, 0.035, 0), (0.45, 0.035, 0), (0.035, 0.80, 1)],
            "2x2": [(0.30, 0.035, 0), (0.95, 0.035, 0), (1.30, 0.035, 0), (0.035, 1.10, 1), (0.035, 0.30, 1)],
            "3x3": [(0.40, 0.035, 0), (1.30, 0.035, 0), (1.95, 0.035, 0), (0.035, 0.45, 1), (0.035, 1.50, 1),
                    (0.035, 2.30, 1)]}[n]
    for k, (x, y, vert) in enumerate(dogs):
        mx, my = _c(n, x, y)
        sx, sy = (0.06, 0.13) if vert else (0.13, 0.06)
        d = B.box(f"dog{k}", mx, my, sx, sy, Z_RIM - 0.01, Z_RIM + 0.035, S, bevel=0.008, tags=tags)
        B.cyl(f"dogb{k}", mx, my, Z_RIM + 0.04, 0.014, 0.012, AM, axis="Z", verts=8, bevel=0.003, tags=tags)

    # ---------------------------------------------------------------- paineis de alivio (2x2/3x3) e respiro
    if W >= 2:
        blow = {"2x2": [(1.06, 0.18, 0.40, 0.62), (1.06, 0.88, 0.40, 0.36)],
                "3x3": [(1.50, 0.16, 0.80, 0.80), (1.50, 1.04, 0.80, 0.80), (0.20, 1.44, 1.10, 0.56)]}[n]
        for k, (x, y, w, h) in enumerate(blow):
            poly = _rect_poly(n, x, y, w, h, chamfer=0.05)
            ba, bp = B.shard(f"blow{k}", poly, ztop - 0.012, ztop + 0.02, green, slope=0.016, groove=0.014,
                             panel_h=0.010, tags=tags)
            mx, my = _c(n, x + w / 2, y + h / 2)
            cuts = []
            if w > 0.6 and h > 0.6:          # linhas de ruptura em X (painel que estoura para fora no cook-off)
                ang = math.degrees(math.atan2(h, w))
                for s in (-1, 1):
                    cuts.append(B.rbox(f"blx{k}{s}", mx, my, 0.012, math.hypot(w, h) - 0.22, ztop + 0.005, 0.6, K,
                                       rot=s * (90 - ang), bevel=0.0))
            else:                            # respiro: 3 venezianas
                for i in range(3):
                    cuts.append(B.box(f"blv{k}{i}", mx, my + (i - 1) * h * 0.22, w - 0.12, 0.022, ztop + 0.0, 0.6,
                                      K, bevel=0.0))
            if bp is not None:
                B.cut(bp, cuts)
            for j, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
                B.cyl(f"blb{k}{j}", mx + sx * (w / 2 - 0.045), my + sy * (h / 2 - 0.045), ztop + 0.03, 0.014, 0.012,
                      S, axis="Z", verts=8, bevel=0.003, tags=tags)


def roof_post(P, layer, path, variant=None, **kw):
    """Pinta nas janelas os segmentos APAGADOS do medidor e dos digitos (mesma geometria dos sprites)."""
    n = P["sub"]
    W = int(n[0])
    im = Image.open(path).convert("RGBA")
    S4 = SS_PIL
    big = Image.new("RGBA", (W * 64 * S4, W * 64 * S4), (0, 0, 0, 0))
    dr = ImageDraw.Draw(big)
    gx, gy, gw, gh = LAYOUT[n]["gauge_rect"]
    N = LAYOUT[n]["levels"]
    for (x0, y0, x1, y1) in _segments(gw, gh, N):
        sx, sy = gw * 64 / round(gw * 64), gh * 64 / round(gh * 64)
        X0, Y0 = (gx * 64 + x0 * sx) * S4, (gy * 64 + y0 * sy) * S4
        X1, Y1 = (gx * 64 + x1 * sx) * S4, (gy * 64 + y1 * sy) * S4
        dr.rectangle([X0, Y0, X1 - 1, Y1 - 1], fill=UNLIT_SEG + (255,))
        dr.rectangle([X0, Y0, X1 - 1, Y0 + S4 - 1], fill=(52, 58, 68, 255))     # reflexo do vidro em cima
    for r in digit_rects(n):
        for sg in "abcdefg":
            pts = LG.seg_poly(sg, r[2] * 64 * S4, r[3] * 64 * S4, r[0] * 64 * S4, r[1] * 64 * S4)
            dr.polygon(pts, fill=UNLIT_DIGIT + (255,))
    small = big.resize((W * 64, W * 64), Image.LANCZOS)
    im.alpha_composite(small)
    im.save(path)


# ============================================================================ piso
def _floor(M, T, n):
    tags = (T,)
    X = LG.mats(M)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    W = int(n[0])
    B.box("fl_base", 0, 0, W, W, -0.05, 0.0, K, bevel=0.0, tags=tags)
    for tx in range(W):
        for ty in range(W):
            cx, cy = tx + 0.5 - W / 2, W / 2 - ty - 0.5
            B.box(f"fl{tx}{ty}", cx, cy, 0.94, 0.94, 0.0, 0.025, KM, bevel=0.008, tags=tags)
    d = RACK[n]
    e = 0.105                                         # parede (7 px) por cima da borda da peca
    lo, hi = -W / 2 + e, W / 2 - e
    # estantes do perimetro: trilhos de aco, prateleira escura e cassetes deitados ao longo da parede
    for side in range(4):
        # lado 0 = cima (y = hi), 1 = esquerda, 2 = baixo, 3 = direita (gira os pontos do lado de cima)
        span = (hi - lo) - 2 * d                  # trecho sem os cantos (cantos tem prateleira propria)
        shelf = LG.rot4([(lo + d, hi - d), (hi - d, hi - d), (hi - d, hi), (lo + d, hi)], side)
        B.loft(f"shelf{side}", shelf, shelf, 0.025, 0.045, AM, bevel=0.004, tags=tags)
        for j, off in enumerate((hi - d + 0.012, hi - 0.012)):
            rail = LG.rot4([(lo + d, off - 0.008), (hi - d, off - 0.008), (hi - d, off + 0.008),
                            (lo + d, off + 0.008)], side)
            B.loft(f"rail{side}{j}", rail, rail, 0.045, 0.11, S, bevel=0.003, tags=tags)
        nc = max(1, int(span / 0.33))
        step = span / nc
        for i in range(nc):
            cx = lo + d + step * (i + 0.5)
            cy = hi - d / 2
            (px, py), = LG.rot4([(cx, cy)], side)
            LG.cassette(f"cs{side}_{i}", px, py, 0.045, M, X, tags, rot=90 + 90 * side, s=min(1.0, (d - 0.03) / 0.15),
                        lit=(i % 3 == 1))
    # cantos: prateleira quadrada com um cassete em pe (visto de cima: a tampa)
    for k, (sx, sy) in enumerate(((-1, 1), (1, 1), (1, -1), (-1, -1))):
        cx, cy = sx * (hi - d / 2), sy * (hi - d / 2)
        B.box(f"corner{k}", cx, cy, d, d, 0.025, 0.05, AM, bevel=0.005, tags=tags)
        B.cyl(f"cornerc{k}", cx, cy, 0.09, d * 0.32, 0.08, X["cass"], axis="Z", verts=8, bevel=0.006, tags=tags)
        B.cyl(f"cornercap{k}", cx, cy, 0.135, d * 0.20, 0.012, X["brass"], axis="Z", verts=8, bevel=0.002, tags=tags)
    # corredor central livre: chapas antiderrapantes e a plataforma de teletransporte (onde os cassetes chegam)
    ai = hi - d - 0.04
    for i, (x, y) in enumerate([(x, y) for x in np.arange(-ai + 0.08, ai, 0.16) for y in np.arange(-ai + 0.08, ai, 0.16)]):
        if math.hypot(x, y) > FREE_PAD[n] + 0.06:
            B.cyl(f"grip{i}", x, y, 0.028, 0.012, 0.006, AM, axis="Z", verts=6, bevel=0.0, tags=tags)
    r = FREE_PAD[n]
    oct_ = [(r * math.cos(math.radians(22.5 + 45 * k)), r * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    B.plate("pad", oct_, 0.025, 0.065, AM, slope=0.018, tags=tags)
    ri = r * 0.74
    oct2 = [(ri * math.cos(math.radians(22.5 + 45 * k)), ri * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    B.plate("pad_well", oct2, 0.064, 0.070, M["black"], slope=0.0, bevel=0.0, tags=tags)
    for i, (x, y) in enumerate(B.ring_points(0, 0, r * 0.86, 8, math.radians(22.5))):
        B.cyl(f"emit{i}", x, y, 0.078, r * 0.065, 0.02, S, axis="Z", verts=8, bevel=0.003, tags=tags)
    B.torus("pad_ring", 0, 0, 0.072, r * 0.50, max(0.006, r * 0.04), X["tele_dim"], tags=tags)
    B.cyl("pad_core", 0, 0, 0.073, r * 0.14, 0.008, X["tele_dim"], axis="Z", verts=16, bevel=0.0, tags=tags)


for _n in LAYOUT:
    globals()[f"roof_{_n}"] = (lambda n: (lambda M, T="roof", variant="cartuchos", **kw: _roof(M, T, n, variant)))(_n)
    globals()[f"floor_{_n}"] = (lambda n: (lambda M, T="floor", **kw: _floor(M, T, n)))(_n)


# ============================================================================ medidor e digitos (PIL)
def _segments(gw, gh, N):
    """Retangulos (px, y para baixo, no sprite round(gw*64) x round(gh*64)) dos N segmentos, de BAIXO para cima:
    2 px de margem, 1 px de vao."""
    w, h = round(gw * 64), round(gh * 64)
    m, g = 2, 1
    inner = h - 2 * m - (N - 1) * g
    seg = inner / N
    out = []
    for i in range(N):                                # i = 0 e o de baixo
        y1 = h - m - i * (seg + g)
        y0 = y1 - seg
        out.append((m, y0, w - m, y1))
    return out


def _lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def gauge_color(f):
    G = LG.GAUGE
    if f <= 0.5:
        return _lerp(G["low"], G["high"], f / 0.5)
    return _lerp(G["high"], G["full"], (f - 0.5) / 0.5)


def gauge(P, layer, px, level=1, **kw):
    n = P["sub"]
    gx, gy, gw, gh = LAYOUT[n]["gauge_rect"]
    N = LAYOUT[n]["levels"]
    w, h = px
    S4 = SS_PIL
    col = gauge_color(level / N)
    big = Image.new("RGBA", (w * S4, h * S4), (0, 0, 0, 0))
    dr = ImageDraw.Draw(big)
    for i, (x0, y0, x1, y1) in enumerate(_segments(gw, gh, N)):
        if i >= level:
            break
        X0, Y0, X1, Y1 = x0 * S4, y0 * S4, x1 * S4, y1 * S4
        dr.rectangle([X0, Y0, X1 - 1, Y1 - 1], fill=tuple(int(c * 0.82) for c in col) + (255,))
        # nucleo mais claro (LED aceso) e reflexo em cima
        core = tuple(int(min(255, c * 1.0 + (255 - c) * 0.28)) for c in col)
        dr.rectangle([X0 + S4, Y0 + S4, X1 - 1 - S4, Y1 - 1 - S4], fill=core + (255,))
        dr.rectangle([X0 + S4, Y0 + S4, X1 - 1 - S4, Y0 + 2 * S4 - 1],
                     fill=tuple(int(min(255, c + (255 - c) * 0.6)) for c in col) + (255,))
    seg = big.resize((w, h), Image.LANCZOS)
    # brilho fraco nos vaos (luz dos LEDs no vidro), alfa baixo
    glow = seg.filter(ImageFilter.GaussianBlur(1.1))
    ga = np.asarray(glow, dtype=np.float32).copy()
    ga[..., 3] *= 0.45
    out = Image.fromarray(ga.astype(np.uint8), "RGBA")
    out.alpha_composite(seg)
    return out


def digit(P, layer, px, variant="0", **kw):
    """Digito de 7 segmentos aceso (so os segmentos acesos; os apagados estao no teto), 24 x 40, ambar."""
    w, h = px
    S4 = SS_PIL
    big = Image.new("RGBA", (w * S4, h * S4), (0, 0, 0, 0))
    dr = ImageDraw.Draw(big)
    for sg in LG.DIGIT_SEGS[variant]:
        dr.polygon(LG.seg_poly(sg, w * S4, h * S4), fill=AMBER_DIGIT + (255,))
    core = big.filter(ImageFilter.MinFilter(5))       # nucleo mais claro no meio de cada segmento
    ca = np.asarray(core, dtype=np.float32).copy()
    ca[..., :3] = np.clip(ca[..., :3] + (255 - ca[..., :3]) * 0.45, 0, 255)
    b = big.copy()
    b.alpha_composite(Image.fromarray(ca.astype(np.uint8), "RGBA"))
    seg = b.resize((w, h), Image.LANCZOS)
    glow = seg.filter(ImageFilter.GaussianBlur(1.2))
    ga = np.asarray(glow, dtype=np.float32).copy()
    ga[..., 3] *= 0.5
    out = Image.fromarray(ga.astype(np.uint8), "RGBA")
    out.alpha_composite(seg)
    return out


# ============================================================================ icone
def icon_extra(P, out, img, variant):
    """Cola a placa padrao da familia (de ../bs_placas) no encaixe do icone."""
    import os
    kind = DEFAULT_KIND[variant]
    for d in (os.path.join(os.path.dirname(out), "bs_placas"),
              os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "art3d", "bs_placas")):
        p = os.path.join(d, f"placa_{kind}.png")
        if os.path.exists(p):
            pl = Image.open(p).convert("RGBA")
            x, y, s, _ = plate_rect(P["sub"])
            pl = pl.resize((int(round(s * 64)), int(round(s * 64))), Image.LANCZOS)
            img.alpha_composite(pl, (int(round(x * 64)), int(round(y * 64))))
            return img
    print(f"  aviso: placa_{kind}.png nao encontrada (renderize bs_placas antes); icone sem placa")
    return img
