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
  roof_<fam>_<n>.png (+ normals) tampa blindada SELADA: aro de blindagem media com um plato escuro por dentro e
                                 UMA PLACA PINTADA POR QUADRO (verde = pintura; vao escuro entre elas, o ritmo dos
                                 tetos das fabricas), carcaca clara do medidor, encaixe da placa, janela dos digitos
                                 (2x2/3x3), escotilhas de alivio de blindagem media sobre recesso escuro (disco de
                                 ruptura sextavado num poco preto / grelha de venezianas, cada uma com uma fenda de LED
                                 ambar) e, no 3x3, a baia de ventilacao com 4 luzes; o chip da familia (faixa de 3 px na
                                 cor palette.family_chip, sem emissao; projeteis = azul com pontas laranja) fica no
                                 plato escuro da borda de baixo; travas de vedacao no aro. Nenhum corte atravessa as
                                 placas pintadas (STYLE 9, "triangulo preto"). Os segmentos APAGADOS do medidor e dos
                                 digitos ja vem pintados nas janelas (post roof_post): o medidor vazio e o teto.
  gauge_<n>_<k>.png              roof_doodads, ResourceSprites (Round Up, HasZeroResourceSprite false), k = 1..N
                                 (N = 5 / 8 / 10): segmentos de baixo para cima com 1 px de vao e 2 px de margem,
                                 cor do nivel f = k / N: f <= 0,5 low -> high, f > 0,5 high -> full (mistura em HSV;
                                 todo pixel fora da chave de pintura, helpers.paint_safe)
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
UNLIT_DIGIT = (38, 34, 29)            # segmento de digito apagado, bem fraco (o "8888" fantasma nao poluir a 1x)
FREE_PAD = {"1x1": 0.17, "2x2": 0.30, "3x3": 0.42}   # raio da plataforma de teletransporte no corredor
# FX da Fita (bs_fita_fx, roof_doodads) no paiol: Location PADRAO = o painel pintado LIVRE (coordenadas da peca, +y para
# baixo) e Size em quadros. 1x1: centro da placa (o unico lugar fora do medidor); 2x2: a faixa livre entre o encaixe da
# placa (borda de baixo 1,005) e a janela dos digitos (borda de cima 1,305); 3x3: o painel livre embaixo da grelha, entre
# a janela dos digitos e o medidor. No centro da peca o FX passava por cima do encaixe e da grelha (2x2/3x3).
FITA_FX = {"1x1": {"location": [0.32, 0.5], "size": 0.8}, "2x2": {"location": [0.54, 1.16], "size": 0.7},
           "3x3": {"location": [2.03, 2.36], "size": 0.8}}
RACK = {"1x1": 0.19, "2x2": 0.25, "3x3": 0.30}       # profundidade das estantes do perimetro


FOLDER_NOTES = [
    "Pasta COMPARTILHADA (extensao da logistica ao esquema layered do spec): meta.json = {shared: true, id: "
    "rafaeltessaro.bs_paiol_comum, parts: {1x1|2x2|3x3: <meta layered normal>}, files: [uniao]}. O 'id' de cada "
    "sub-meta (rafaeltessaro.bs_paiol_<n>) e so o nome do conjunto: os ids REAIS das 12 pecas estao em "
    "parts.<n>.ids.<familia> (rafaeltessaro.bs_paiol_<familia>_<n>). Para o WP10 (check_art3d) e o bsgen/layered.py.",
    "Spec: art3d_owner_map chama a pasta de 'bs_paiol_comum'; a arte esta em art3d/bs_paiol (art_dir do spec) e "
    "e publicada em parts/bs_paiol_comum/ (regras: '../bs_paiol_comum/<arquivo>').",
    "PARA O WP05/WP10 (atualizar o spec ao ligar): SPEC_2.0 art_assets.palette.family_chip.projeteis ainda diz violeta "
    "(150, 105, 255), e palette.rail (violet/glow/chip) tambem. A arte segue a USER_NOTES (Tupa azul): o chip dos "
    "projeteis e AZUL (64, 128, 255) com pontas LARANJA (255, 140, 40) (meta parts.<n>.family_chip / family_chip_tip "
    "e helpers.FAMILY_CHIP / FAMILY_CHIP_TIP). Troque o spec, nao a arte.",
]


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
        "folder": "bs_paiol", "sub": n, "folder_id": "rafaeltessaro.bs_paiol_comum", "folder_notes": FOLDER_NOTES,
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
            "family_chip_tip": {f: list(c) for f, c in LG.FAMILY_CHIP_TIP.items()},
            "fita_fx": {"location": FITA_FX[n]["location"], "size": [FITA_FX[n]["size"]] * 2,
                        "files": "../bs_fita_fx/cartucho_sai|entra<1..8>.png (roof_doodads), brilho_* (lights_add)",
                        "default": True},
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
            f"FX da Fita (bs_fita_fx cartucho_sai/entra, roof_doodads; brilho_* em lights_add) no paiol {n}: PADRAO "
            f"Location {FITA_FX[n]['location']} com Size {FITA_FX[n]['size']} (meta 'fita_fx': o painel pintado livre; "
            "no centro da peca o FX passava por cima do encaixe da placa e da grelha). No 1x1 nao ha painel livre: o "
            "FX fica no centro da placa (cruza so a placa, nao o medidor). Tudo em roof_doodads, ordem indefinida na "
            "mesma camada; 0,6 s por envio.",
            f"gauge rect {L['gauge_rect']} = {L['gauge_rect'][2] * 64:.2f} x {L['gauge_rect'][3] * 64:.2f} px no jogo; "
            "a textura e o arredondamento disso (o jogo reamostra um pouco: os vaos de 1 px podem sair macios).",
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


def _family_mat(fam, tip=False):
    c = LG.lin(LG.FAMILY_CHIP_TIP[fam] if tip else LG.FAMILY_CHIP[fam])
    m = B.mat_metal(f"lg_chip_{fam}{'_tip' if tip else ''}", c, rough=0.55, metal=0.15)
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.25
    return m


# ============================================================================ teto
# alturas da tampa: aro de blindagem media (0 -> Z_RIM) com o PLATO escuro (K) por dentro (-> Z_PLAT), placas
# pintadas por quadro em cima do plato (-> ZT) e as carcacas (medidor, encaixe, digitos, escotilhas) por cima delas
Z_RIM = 0.05
Z_PLAT = Z_RIM + 0.012
Z_TILE = 0.085
ZT = Z_TILE + 0.014                   # topo do painel interno das placas pintadas
TILE_GAP = 0.044                      # vao escuro entre as placas pintadas de quadros vizinhos (~3 px)
# elementos de alivio da tampa (2x2/3x3), coordenadas da peca (x, y para baixo): (tipo, cx, cy, w, h)
#   "disco": escotilha blindada de bisel duplo sobre um recesso escuro, com o disco de ruptura SEXTAVADO afundado num
#            poco preto e uma fenda de LED ambar; "grelha": a mesma escotilha com a grelha de ventilacao (venezianas
#            num recesso preto) e a fenda de LED; "baia": baia de ventilacao (moldura, venezianas, 4 luzes ambar)
RELIEF = {
    "1x1": [],
    "2x2": [("disco", 1.26, 0.45, 0.42, 0.62), ("grelha", 1.26, 1.04, 0.42, 0.44)],
    "3x3": [("disco", 1.89, 0.57, 0.78, 0.78), ("grelha", 1.89, 1.43, 0.78, 0.78), ("baia", 0.75, 1.72, 1.10, 0.52)],
}


def _crect(n, x0, y0, x1, y1, c=0.0, **corners):
    """Retangulo da PECA (x0, y0) - (x1, y1) (y para baixo) -> poligono do modelo (CCW), chanfro c em todos os cantos
    ou por canto (tl, tr, br, bl = cima-esquerda, ...)."""
    W = int(n[0])
    cc = {k: corners.get(k, c) for k in ("tl", "tr", "br", "bl")}
    X0, X1, Y0, Y1 = x0 - W / 2, x1 - W / 2, W / 2 - y1, W / 2 - y0
    pts = [(X0 + cc["bl"], Y0), (X1 - cc["br"], Y0), (X1, Y0 + cc["br"]), (X1, Y1 - cc["tr"]), (X1 - cc["tr"], Y1),
           (X0 + cc["tl"], Y1), (X0, Y1 - cc["tl"]), (X0, Y0 + cc["bl"])]
    out = []
    for q in pts:
        if not out or abs(q[0] - out[-1][0]) > 1e-9 or abs(q[1] - out[-1][1]) > 1e-9:
            out.append(q)
    if abs(out[0][0] - out[-1][0]) < 1e-9 and abs(out[0][1] - out[-1][1]) < 1e-9:
        out.pop()
    return out


def _hexpoly(cx, cy, r, a0=90.0):
    return [(cx + r * math.cos(math.radians(a0 + 60 * k)), cy + r * math.sin(math.radians(a0 + 60 * k)))
            for k in range(6)]


def _tiles(n):
    """Placas pintadas: a area livre da tampa (fora do medidor e da faixa do chip) partida nos limites dos quadros com
    um vao escuro (o ritmo de uma placa por quadro dos tetos das fabricas). [(x0, y0, x1, y1, cantos)] da peca."""
    W = int(n[0])
    gx = LAYOUT[n]["gauge_rect"][0]
    lc = 0.10 + 0.03 * W                              # chanfro da tampa
    X0, X1, Y0, Y1 = 0.10, gx - 0.05 - 0.035, 0.10, W - 0.17
    xs = [X0] + [k for k in range(1, W) if X0 + 0.2 < k < X1 - 0.2] + [X1]
    ys = [Y0] + [k for k in range(1, W) if Y0 + 0.2 < k < Y1 - 0.2] + [Y1]
    out = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            a = xs[i] + (TILE_GAP / 2 if i > 0 else 0)
            b = xs[i + 1] - (TILE_GAP / 2 if i < len(xs) - 2 else 0)
            c = ys[j] + (TILE_GAP / 2 if j > 0 else 0)
            d = ys[j + 1] - (TILE_GAP / 2 if j < len(ys) - 2 else 0)
            corners = {"tl": 0.05, "tr": 0.05, "br": 0.05, "bl": 0.05}
            if i == 0 and j == 0:
                corners["tl"] = lc - 0.03
            if i == 0 and j == len(ys) - 2:
                corners["bl"] = lc - 0.06
            out.append((a, c, b, d, corners))
    return out


def _hatch(name, n, kind, cx, cy, w, h, M, X, tags):
    """Escotilha de alivio blindada (bisel duplo, blindagem MEDIA) sobre um recesso escuro, com o disco de ruptura
    sextavado afundado ("disco") ou a grelha de ventilacao ("grelha"), e uma fenda de LED ambar num rebaixo preto."""
    AM, K, KM, S = M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    m = min(w, h)
    c = 0.20 * m
    mx, my = _c(n, cx, cy)
    # recesso escuro em volta (le como o vao fundo onde a escotilha assenta)
    B.loft(f"{name}_rec", _crect(n, cx - w / 2 - 0.035, cy - h / 2 - 0.035, cx + w / 2 + 0.035, cy + h / 2 + 0.035,
                                 c + 0.02), _crect(n, cx - w / 2 - 0.035, cy - h / 2 - 0.035, cx + w / 2 + 0.035,
                                                   cy + h / 2 + 0.035, c + 0.02), ZT - 0.006, ZT + 0.008, K,
           bevel=0.0, tags=tags)
    ha, hp = B.shard(f"{name}_h", _crect(n, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, c), ZT + 0.004,
                     ZT + 0.040, AM, slope=0.02, groove=0.014, panel_h=0.014, tags=tags)
    zt = ZT + 0.054
    yo = 0.10 * h                                     # o miolo sobe um pouco; a fenda do LED fica embaixo
    if kind == "disco":
        r = 0.22 * m
        hole = _hexpoly(mx, my + yo, r)
        for t in (ha, hp):
            if t is not None:
                B.cut(t, [B.loft(f"{name}_hc{t.name}", hole, hole, ZT + 0.010, 0.6, K, bevel=0.0)])
        B.loft(f"{name}_hbed", hole, hole, ZT + 0.010, ZT + 0.014, M["black"], bevel=0.0, tags=tags)
        B.plate(f"{name}_disc", _hexpoly(mx, my + yo, r * 0.74), ZT + 0.014, ZT + 0.030, S, slope=0.008,
                bevel=0.003, tags=tags)
        for k in range(3):                            # riscos de ruptura em Y
            a = math.radians(90 + 120 * k)
            L = r * 0.56
            B.rbox(f"{name}_sc{k}", mx + math.cos(a) * L / 2, my + yo + math.sin(a) * L / 2, L, 0.012,
                   ZT + 0.029, ZT + 0.033, M["black"], rot=math.degrees(a), bevel=0.0, tags=tags)
        B.cyl(f"{name}_cap", mx, my + yo, ZT + 0.034, r * 0.17, 0.010, KM, axis="Z", verts=6, bevel=0.002, tags=tags)
    else:                                             # grelha: venezianas num recesso preto
        gw, gh = w * 0.56, h * 0.44
        hole = B.rpoly(mx, my + yo, gw, gh, 0, chamfer=0.02)
        for t in (ha, hp):
            if t is not None:
                B.cut(t, [B.loft(f"{name}_gc{t.name}", hole, hole, ZT + 0.010, 0.6, K, bevel=0.0)])
        B.loft(f"{name}_gbed", hole, hole, ZT + 0.010, ZT + 0.014, M["black"], bevel=0.0, tags=tags)
        nl = 4 if h > 0.6 else 3
        for k in range(nl):
            yy = my + yo + gh / 2 - gh * (k + 0.5) / nl
            B.box(f"{name}_lv{k}", mx, yy, gw - 0.03, gh / nl * 0.42, ZT + 0.014, ZT + 0.032, KM, bevel=0.004,
                  tags=tags)
    # fenda do LED (rebaixo preto vazado + lente ambar) embaixo do miolo
    LG.ledslot(f"{name}_led", mx, my - h * 0.36 + 0.02, w * 0.36, 0.044, ZT + 0.026, M, tags, [ha, hp],
               lens=M["glow_dim"], lens_frac=0.55)
    for k, (sx, sy) in enumerate(((-1, 1), (1, -1))):  # 2 parafusos nos chanfros
        d = c * 0.62
        B.cyl(f"{name}_b{k}", mx + sx * (w / 2 - d), my + sy * (h / 2 - d), zt + 0.002, 0.015, 0.012, S, axis="Z",
              verts=8, bevel=0.003, tags=tags)


def _bay(name, n, cx, cy, w, h, M, X, tags):
    """Baia de ventilacao (familia: recesso escuro, venezianas, fileira de luzes ambar) numa moldura media."""
    AM, K, KM, S = M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    mx, my = _c(n, cx, cy)
    fa, fp = B.shard(f"{name}_f", _crect(n, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 0.06), ZT - 0.006,
                     ZT + 0.030, AM, slope=0.018, groove=0.012, panel_h=0.012, tags=tags)
    gw, gh = w - 0.16, h - 0.22
    gy = my + 0.035
    hole = B.rpoly(mx, gy, gw, gh, 0, chamfer=0.025)
    for t in (fa, fp):
        if t is not None:
            B.cut(t, [B.loft(f"{name}_c{t.name}", hole, hole, ZT - 0.004, 0.6, K, bevel=0.0)])
    B.loft(f"{name}_bed", hole, hole, ZT - 0.004, ZT + 0.004, M["black"], bevel=0.0, tags=tags)
    nl = 5
    for k in range(nl):
        yy = gy + gh / 2 - gh * (k + 0.5) / nl
        B.box(f"{name}_lv{k}", mx, yy, gw - 0.03, gh / nl * 0.46, ZT + 0.004, ZT + 0.024, KM, bevel=0.004, tags=tags)
    # fileira de 4 luzes ambar num rebaixo preto embaixo da grelha
    ly = my - h / 2 + 0.065
    LG.ledslot(f"{name}_led", mx, ly, gw * 0.62, 0.042, ZT + 0.014, M, tags, [fa, fp], lens=None)
    for k in range(4):
        B.box(f"{name}_pip{k}", mx + (k - 1.5) * gw * 0.62 / 4, ly, gw * 0.62 / 4 * 0.5, 0.022, ZT + 0.022,
              ZT + 0.030, M["glow_dim"], bevel=0.0, tags=tags)
    for j, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        B.cyl(f"{name}_b{j}", mx + sx * (w / 2 - 0.045), my + sy * (h / 2 - 0.045), ZT + 0.044, 0.014, 0.012, S,
              axis="Z", verts=8, bevel=0.003, tags=tags)


def _roof(M, T, n, fam):
    """Tampa blindada SELADA: aro de blindagem media + plato escuro, uma placa PINTADA por quadro (vao escuro entre
    elas), carcaca clara do medidor, encaixe da placa, janela dos digitos (2x2/3x3), escotilhas de alivio e baia de
    ventilacao (2x2/3x3) e o chip da familia no plato da borda de baixo. Nenhum corte atravessa as placas pintadas
    (o 'triangulo preto' da STYLE 9): janelas e furos so cortam as proprias carcacas."""
    tags = (T,)
    X = LG.mats(M)
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    green = B.mat_roof_green()
    W = int(n[0])
    L = LAYOUT[n]
    B.box("deck_under", 0, 0, W, W, -0.05, 0.02, K, bevel=0.0, tags=tags)
    lc = 0.10 + 0.03 * W
    lid = B.rpoly(0, 0, W - 0.05, W - 0.05, 0, chamfer=lc)
    # aro de blindagem media (sem pintura) com o plato escuro por dentro: o vao das placas pintadas e escuro
    la, lp = B.shard("lid", lid, 0.0, Z_RIM, AM, slope=0.03, groove=0.03, panel_h=0.012, panel_mat=K, tags=tags)
    # parafusos do aro (a cada ~0,3 quadro) no topo do aro (cima e esquerda; os outros lados tem as travas)
    rim = W / 2 - 0.07
    nb = max(2, int(round((W - 0.4) / 0.3)))
    for k in range(nb):
        t = -W / 2 + 0.2 + (W - 0.4) * k / (nb - 1)
        for j, (bx, by) in enumerate(((t, -rim), (rim, t))):
            B.cyl(f"rimb{k}_{j}", bx, by, Z_RIM + 0.005, 0.012, 0.010, S, axis="Z", verts=8, bevel=0.003, tags=tags)
    # placas pintadas (uma por quadro), bisel duplo como o convés (Mo.hull_roof)
    for i, (x0, y0, x1, y1, cc) in enumerate(_tiles(n)):
        B.shard(f"tile{i}", _crect(n, x0, y0, x1, y1, **cc), Z_PLAT - 0.004, Z_TILE, green, slope=0.02,
                groove=0.04, panel_h=0.014, tags=tags)

    # ---------------------------------------------------------------- medidor: carcaca clara + janela escura
    gx, gy, gw, gh = L["gauge_rect"]
    house = _rect_poly(n, gx, gy, gw, gh, chamfer=0.035, grow=0.05)
    ha, hp = B.shard("g_house", house, Z_PLAT - 0.004, ZT + 0.02, A, slope=0.018, groove=0.012, panel_h=0.014,
                     tags=tags)
    win = _rect_poly(n, gx, gy, gw, gh)
    for t in (ha, hp):
        if t is not None:
            B.cut(t, [B.loft(f"g_win{t.name}", win, win, Z_PLAT - 0.002, 0.6, K, bevel=0.0)])
    B.loft("g_bed", win, win, Z_PLAT - 0.002, Z_PLAT + 0.006, X["glass"], bevel=0.0, tags=tags)
    for k, yy in enumerate((gy - 0.026, gy + gh + 0.026)):
        bx, by = _c(n, gx + gw / 2, yy)
        B.cyl(f"g_bolt{k}", bx, by, ZT + 0.036, 0.015, 0.012, S, axis="Z", verts=10, bevel=0.004, tags=tags)

    # ---------------------------------------------------------------- encaixe da placa (rebaixo preto com labio)
    pr = plate_rect(n)
    sock = _rect_poly(n, *pr, chamfer=0.05, grow=0.055)
    sa, sp = B.shard("sock", sock, ZT - 0.006, ZT + 0.03, AM, slope=0.016, groove=0.010, panel_h=0.012, tags=tags)
    hole = _rect_poly(n, *pr, chamfer=0.04, grow=0.006)
    for t in (sa, sp):
        if t is not None:
            B.cut(t, [B.loft(f"s_hole{t.name}", hole, hole, ZT - 0.004, 0.6, K, bevel=0.0)])
    B.loft("s_bed", hole, hole, ZT - 0.004, ZT + 0.002, M["black"], bevel=0.0, tags=tags)
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        cx, cy = _c(n, pr[0] + pr[2] / 2 + sx * (pr[2] / 2 + 0.03), pr[1] + pr[3] / 2 + sy * (pr[3] / 2 + 0.03))
        B.rbox(f"s_clip{k}", cx, cy, 0.05, 0.05, ZT + 0.03, ZT + 0.048, S, rot=45, bevel=0.004, tags=tags)

    # ---------------------------------------------------------------- janela dos digitos (2x2 / 3x3)
    dr = digit_rects(n)
    if dr:
        x0, x1 = dr[0][0] - 0.02, dr[-1][0] + dr[-1][2] + 0.02
        y0, y1 = dr[0][1] - 0.02, dr[0][1] + dr[0][3] + 0.02
        dh = _rect_poly(n, x0, y0, x1 - x0, y1 - y0, chamfer=0.03, grow=0.045)
        da, dp = B.shard("d_house", dh, ZT - 0.006, ZT + 0.026, A, slope=0.016, groove=0.010, panel_h=0.012,
                         tags=tags)
        dw = _rect_poly(n, x0, y0, x1 - x0, y1 - y0, chamfer=0.015)
        for t in (da, dp):
            if t is not None:
                B.cut(t, [B.loft(f"d_win{t.name}", dw, dw, ZT - 0.004, 0.6, K, bevel=0.0)])
        B.loft("d_bed", dw, dw, ZT - 0.004, ZT + 0.002, X["glass"], bevel=0.0, tags=tags)

    # ---------------------------------------------------------------- chip da familia (faixa de 3 px, sem emissao)
    # no plato escuro da borda de baixo, embaixo das placas pintadas (a faixa le sobre o escuro em qualquer pintura)
    cx0 = 0.14
    cx1 = gx - 0.10
    cy = W - 0.118
    ch = 3.2 / 64
    bed = _rect_poly(n, cx0, cy - ch / 2, cx1 - cx0, ch, grow=0.012)
    B.loft("chip_bed", bed, bed, Z_PLAT - 0.002, Z_PLAT + 0.003, M["black"], bevel=0.0, tags=tags)
    strip = _rect_poly(n, cx0, cy - ch / 2, cx1 - cx0, ch)
    B.loft("chip", strip, strip, Z_PLAT + 0.002, Z_PLAT + 0.016, _family_mat(fam), bevel=0.003, tags=tags)
    if fam in LG.FAMILY_CHIP_TIP:                     # projeteis: pontas laranja (azul + laranja do Tupa)
        tl = 0.075
        for k, xa in enumerate((cx0, cx1 - tl)):
            tip = _rect_poly(n, xa, cy - ch / 2, tl, ch, grow=0.002)
            B.loft(f"chip_tip{k}", tip, tip, Z_PLAT + 0.003, Z_PLAT + 0.018, _family_mat(fam, tip=True), bevel=0.003,
                   tags=tags)

    # ---------------------------------------------------------------- travas de vedacao no aro (cima e esquerda)
    dogs = {"1x1": [(0.20, 0.035, 0), (0.45, 0.035, 0), (0.035, 0.80, 1)],
            "2x2": [(0.30, 0.035, 0), (0.95, 0.035, 0), (1.30, 0.035, 0), (0.035, 1.10, 1), (0.035, 0.30, 1)],
            "3x3": [(0.40, 0.035, 0), (1.30, 0.035, 0), (1.95, 0.035, 0), (0.035, 0.45, 1), (0.035, 1.50, 1),
                    (0.035, 2.30, 1)]}[n]
    for k, (x, y, vert) in enumerate(dogs):
        mx, my = _c(n, x, y)
        sx, sy = (0.06, 0.13) if vert else (0.13, 0.06)
        B.box(f"dog{k}", mx, my, sx, sy, Z_RIM - 0.01, Z_RIM + 0.035, S, bevel=0.008, tags=tags)
        B.cyl(f"dogb{k}", mx, my, Z_RIM + 0.04, 0.014, 0.012, AM, axis="Z", verts=8, bevel=0.003, tags=tags)

    # ---------------------------------------------------------------- escotilhas de alivio e baia de ventilacao
    for k, (kind, cx, cy, w, h) in enumerate(RELIEF[n]):
        if kind == "baia":
            _bay(f"bay{k}", n, cx, cy, w, h, M, X, tags)
        else:
            _hatch(f"hatch{k}", n, kind, cx, cy, w, h, M, X, tags)
    _hatch_well(n, K, tags)


def _hatch_well(n, K, tags):
    """Poco escuro CONTINUO atras da coluna de escotilhas (2x2 / 3x3): os recessos chanfrados de cada escotilha
    deixavam cunhas de 1-2 px da placa pintada entre os cantos (branco no casco branco). Um retangulo escuro da borda
    de cima da escotilha de cima ate a de baixo (cantos de baixo com o chanfro do recesso) fecha o vao com o mesmo
    escuro dos outros vaos entre paineis da tampa. Cantos de cima retos: emendam no vao escuro do aro / entre placas."""
    hs = [r for r in RELIEF[n] if r[0] != "baia"]
    if len(hs) < 2:
        return
    hs = sorted(hs, key=lambda r: r[2])
    cx, w = hs[0][1], max(r[3] for r in hs)
    if any(abs(r[1] - cx) > 1e-6 for r in hs):
        return
    top = hs[0][2] - hs[0][4] / 2 - 0.035
    bot = hs[-1][2] + hs[-1][4] / 2 + 0.035
    cb = 0.20 * min(hs[-1][3], hs[-1][4]) + 0.02       # chanfro do recesso da escotilha de baixo
    poly = _crect(n, cx - w / 2 - 0.035, top, cx + w / 2 + 0.035, bot, 0.0, bl=cb, br=cb)
    B.loft("hatch_well", poly, poly, ZT - 0.006, ZT + 0.006, K, bevel=0.0, tags=tags)


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


def _lerp_hsv(a, b, t):
    """Mistura em HSV (matiz, saturacao e valor lineares): o meio do caminho ambar -> verde fica um lima saturado, nao
    o oliva/chartreuse lamacento da mistura em RGB."""
    import colorsys
    ha, sa, va = colorsys.rgb_to_hsv(*(c / 255.0 for c in a))
    hb, sb, vb = colorsys.rgb_to_hsv(*(c / 255.0 for c in b))
    r, g, bb = colorsys.hsv_to_rgb(ha + (hb - ha) * t, sa + (sb - sa) * t, va + (vb - va) * t)
    return (r * 255, g * 255, bb * 255)


GAUGE_VMAX = 0.90                     # teto do VALOR (HSV) do corpo dos segmentos: ~230 (le como vidro aceso, nao como
#                                       bloco de interface chapado; o reflexo de 1 px em cima pode passar disso)


def gauge_color(f):
    """Cor do nivel f = k / N (spec: f <= 0,5 low -> high, f > 0,5 high -> full), fora da chave de pintura, com o valor
    limitado a GAUGE_VMAX (o lima de f ~ 0,6 e o verde cheio deixam de ser blocos chapados no casco branco)."""
    import colorsys
    G = LG.GAUGE
    if f <= 0.5:
        c = _lerp_hsv(G["low"], G["high"], f / 0.5)
    else:
        c = _lerp_hsv(G["high"], G["full"], (f - 0.5) / 0.5)
    h, s, v = colorsys.rgb_to_hsv(*(x / 255.0 for x in c))
    c = tuple(x * 255 for x in colorsys.hsv_to_rgb(h, s, min(v, GAUGE_VMAX)))
    return LG.safe_rgb(c)


def zero_rgb_under_alpha0(img):
    """RGB = 0 onde alfa = 0 (sem franja de cor 'suja' no filtro bilinear do jogo)."""
    a = np.asarray(img.convert("RGBA")).copy()
    a[a[..., 3] == 0] = 0
    return Image.fromarray(a, "RGBA")


def _seg_shade(rw, rh, S4):
    """Fator de luz (rh x rw, 0..~1,05) de UM segmento aceso a S4x: vidro aceso por tras, nao bloco chapado. Queda
    vertical SUAVE (1,02 em cima -> 0,92 embaixo: mais forte o amarelo vira oliva), bisel interno de 1 px nas laterais
    (esquerda 0,92, direita 0,86) e 1 px mais escuro embaixo (0,78). O reflexo de cima e desenhado a parte."""
    t = (np.arange(rh, dtype=np.float32) + 0.5) / max(1, rh)
    f = (1.02 - 0.10 * t)[:, None] * np.ones((1, rw), np.float32)
    f[:, :S4] *= 0.92
    f[:, rw - S4:] *= 0.86
    f[rh - S4:, :] = np.minimum(f[rh - S4:, :], 0.78)
    return f


def gauge(P, layer, px, level=1, **kw):
    """Segmentos acesos 1..level (de baixo para cima) na cor do nivel (valor <= GAUGE_VMAX): cada segmento com queda
    vertical de luz, bisel interno nas laterais, 1 px mais escuro embaixo e o reflexo de 1 px em cima (vidro aceso),
    brilho fraco nos vaos (blur PRE-multiplicado: a cor do brilho e a dos LEDs) e paint_safe() no fim: nenhum pixel
    na chave de pintura; RGB = 0 sob alfa 0."""
    n = P["sub"]
    gx, gy, gw, gh = LAYOUT[n]["gauge_rect"]
    N = LAYOUT[n]["levels"]
    w, h = px
    S4 = SS_PIL
    col = np.array(gauge_color(level / N), np.float32)
    hi = np.array(LG.safe_rgb(tuple(c + (255 - c) * 0.40 for c in col)), np.float32)
    arr = np.zeros((h * S4, w * S4, 4), np.float32)
    for i, (x0, y0, x1, y1) in enumerate(_segments(gw, gh, N)):
        if i >= level:
            break
        X0, Y0, X1, Y1 = (int(round(v * S4)) for v in (x0, y0, x1, y1))
        f = _seg_shade(X1 - X0, Y1 - Y0, S4)
        arr[Y0:Y1, X0:X1, :3] = col[None, None, :] * f[..., None]
        arr[Y0:Y0 + S4, X0 + S4:X1 - S4, :3] = hi[None, None, :]          # reflexo do vidro (1 px)
        arr[Y0:Y1, X0:X1, 3] = 255
    big = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    seg = big.resize((w, h), Image.LANCZOS)
    glow = LG.premul_blur(seg, 1.1)
    ga = np.asarray(glow, dtype=np.float32).copy()
    ga[..., 3] *= 0.45
    out = Image.fromarray(ga.astype(np.uint8), "RGBA")
    out.alpha_composite(seg)
    out, _ = LG.paint_safe(out)
    return zero_rgb_under_alpha0(out)


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
    return zero_rgb_under_alpha0(out)


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
