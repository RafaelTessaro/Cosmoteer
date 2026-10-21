"""Renderizador do tipo de peca "layered" (spec de arte 2.0, render_kinds.layered).

Uma peca "layered" e feita de CAMADAS independentes, cada uma com o seu sprite (ou a sua sequencia de sprites),
o seu retangulo dentro da peca e a sua camada do jogo. Serve para pecas que nao sao torre nem fabrica: o railgun
Tupa (carregador / cano / ponta), e depois os paiois, a fita, a tremonha e as placas de modo.

    <venv-com-bpy>/bin/python tools/blender/render_layered.py <modulo> [--part curto1,curto2] [--only camada1,camada2]
                                                              [--out DIR] [--quick]

    <modulo>  arquivo tools/blender/parts/<modulo>.py (ou o caminho de um .py). Ele define:
              PART  = {...}                    uma peca  -> art3d/<modulo>/ (ou --out)
              PARTS = {"curto": {...}, ...}    varias    -> art3d/<curto>/ (ou --out/<curto>/)
    --part    so essas pecas de PARTS; --only so essas camadas (o meta.json antigo e mesclado).

Esquema de PART (coordenadas da peca em quadros, origem no canto de cima-esquerda, +y para BAIXO, como as regras):

    {"id": "rafaeltessaro.bs_xxx", "kind": "layered", "size": [W, H], "accent": "violet" | (r, g, b) | "amber"...,
     "walls": "closed" | "none" | {"open": [["top" | "bottom" | "left" | "right", t0, t1], ...]},
     "layers": [
        {"name": "roof",            # chave no meta.json; tambem a etiqueta (tag) dos objetos do modelo
         "fn": "roof",              # funcao do modulo: fn(M, T, **kw); ou "pil:<funcao>" = fn(P, layer, px, **kw)
                                    # devolve uma imagem RGBA do tamanho px (camadas 2D: brilhos, digitos...)
         "game_layer": "roofs",     # camada do jogo (conventions.ship_layers_bottom_to_top)
         "rect": [x, y, w, h],      # retangulo na peca (quadros, +y para baixo); padrao = a peca inteira
         "at": [[x, y], ...],       # opcional: o MESMO sprite desenhado em varios lugares (canto de cima-esquerda
                                    # de cada copia, quadros); a 1a deve ser rect[0:2]. O modelo e renderizado
                                    # so no "rect"; o meta ganha "rects" (uma entrada por copia) e o composite()
                                    # desenha todas (consoles dos 2 postos, estantes dos paiois, a fita...)
         "file": "roof.png",        # nome; com niveis/quadros/variantes use {i} (1..N) ou {v} (variante)
         "levels": N | "frames": N | "variants": [..] | "situations": [..],   # opcional (um so = sprite unico)
         "interval": 0.1,           # segundos por quadro (meta; quem anima e a regra)
         "normals": True,           # grava <arquivo>_normals.png (alfa = alfa do difuso)
         "opaque": True,            # compoe sobre o piso escuro (18, 19, 21) com alfa 255 (pisos)
         "emission_only": True,     # so a luz emitida + halo (sem luzes da cena)
         "blend": "add" | "alpha",  # com emission_only: "add" = opaco sobre preto (lights_add, como os PNGs
                                    # vanilla); "alpha" = brilho com alfa (como turret_oc.png)
         "halo": True,              # halo de brilho dos emissivos no difuso (render_set glow_halo)
         "despill": True,           # tira o verde refletido das placas pintadas no metal vizinho (tetos)
         "fade": {"bottom": 0.12},  # o alfa cai a 0 ate a borda pedida (quadros; top/bottom/left/right): o que
                                    # passa da borda do rect "emerge" em vez de sair cortado reto
         "same_as": {"layer": "culatra_carrega", "index": 6},   # depois de tudo: os pixels deste sprite saem do
                                    # sprite <index> (1..N) da outra camada (mesmo rect), recortados pelo alfa deste
                                    # render (o mesmo objeto, pixel a pixel, sem o ruido de 2 renders)
         "samples": 48,             # amostras do Cycles
         "islands": False},         # meta: o sprite pode ter varias ilhas (o check_art3d aceita)
        ...],
     "icon": {"size": [69, 92], "layers": ["floor", "roof"], "paint": [120, 124, 132],    # EditorIcon (opcional)
              "pick": {"camada": indice}, "lights": {"carga": [indice, ganho]}},  # lights: aditivos no icone
     "blueprint_layers": ["weapon", "roof"]}                                                # silhueta (opcional)

Funcoes de modelo: fn(M, T, **kw) com kw = level (1..N) | phase ((k-1)/N) e frame (1..N) | variant | sit.
Coordenadas do modelo CENTRADAS NA PECA, 1 unidade = 1 quadro, +X = direita, +Y = frente da peca (topo da
imagem), +Z = para cima (igual ao tipo "factory"). A camera de cada camada e recortada no "rect" (sub-retangulo),
entao um sprite de 1x1 no canto da peca e modelado na posicao dele dentro da peca.

Saida em art3d/<curto>/: os PNGs de cada camada, walls.png (moldura vanilla de 7 px com as aberturas pedidas),
icon.png, blueprints.png e meta.json:

    {"version": 1, "kind": "layered", "id": ..., "size": [W, H],
     "layers": {nome: {"game_layer", "rect", "rects": [[x, y, w, h], ...] (todas as copias; rects[0] = rect),
                       "files": [...], "normals": [...] | null,
                       "levels" | "frames" | "variants" | "situations", "interval", "blend", "opaque", "islands"}},
     "walls": "walls.png" | null, "icon": "icon.png", "blueprints": "blueprints.png", "files": [...],
     "crew_pos": [...], "notes": [...]}      # crew_pos/notes: copiados de PART (as notas sao para quem liga as regras)

Este arquivo nao muda render_part.py: ele so importa de la os utilitarios (emission_pass, warn_empty,
_oc_glow_sprite). Contrato de estilo: tools/blender/STYLE.md.
"""

import importlib
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

import bs3d as B  # noqa: E402
import models as Mo  # noqa: E402
import render_part as RP  # noqa: E402  (so utilitarios; o main dele nao roda no import)

PX = B.PX
QUICK = False
FLOOR_BG = (18, 19, 21)
GAME_LAYERS = ["structure", "floors", "turrets", "doodads_low", "walls_stencil", "external_walls", "walls", "doors",
               "weapons", "doodads_high", "lights_add", "fire", "roofs", "roof_doodads", "roof_turrets",
               "roof_lights_fancy"]


# ============================================================================ utilidades
def samples(n):
    bpy.context.scene.cycles.samples = max(8, n // 4) if QUICK else n


_ACCENT_NOTED = set()


def fresh(accent):
    B.reset()
    if isinstance(accent, str) and accent not in Mo.ACCENTS:
        if accent not in _ACCENT_NOTED:
            _ACCENT_NOTED.add(accent)
            print(f"  nota: destaque '{accent}' nao existe em models.ACCENTS; M['glow'], M['glow_dim'] e M['lens'] "
                  f"saem AMBAR (o modelo deve definir os proprios materiais de luz para '{accent}')")
        accent = "amber"   # destaques novos (ex.: "violet") definem os proprios materiais no modelo
    return Mo.mats(accent)


def rect_of(P, layer):
    W, H = P["size"]
    return list(layer.get("rect", [0, 0, W, H]))


def rects_of(P, layer):
    """Todas as copias do sprite da camada: [[x, y, w, h], ...] (a 1a = o rect do render)."""
    r = rect_of(P, layer)
    at = layer.get("at")
    if not at:
        return [r]
    out = [[float(x), float(y), r[2], r[3]] for x, y in at]
    if abs(out[0][0] - r[0]) > 1e-6 or abs(out[0][1] - r[1]) > 1e-6:
        raise SystemExit(f"{P['id']}/{layer['name']}: at[0] {at[0]} deve ser o canto do rect {r[:2]}")
    return out


def ent_rects(ent):
    """Copias de uma entrada do meta.json (meta antigo sem "rects" = so o rect)."""
    return ent.get("rects") or [ent["rect"]]


def rect_center(P, rect):
    """Centro do retangulo (quadros, +y para baixo) em coordenadas do modelo (centradas, +y para cima)."""
    W, H = P["size"]
    x, y, w, h = rect
    return x + w / 2 - W / 2, H / 2 - (y + h / 2)


def rect_px(rect):
    return int(round(rect[2] * PX)), int(round(rect[3] * PX))


def instances(layer):
    """[(chave, kw, arquivo)] de uma camada: niveis 1..N, quadros 1..N, variantes, situacoes ou sprite unico."""
    f = layer.get("file", layer["name"] + ".png")
    if "levels" in layer:
        n = int(layer["levels"])
        return [(k, {"level": k}, f.format(i=k)) for k in range(1, n + 1)]
    if "frames" in layer:
        n = int(layer["frames"])
        return [(k, {"phase": (k - 1) / n, "frame": k}, f.format(i=k)) for k in range(1, n + 1)]
    if "variants" in layer:
        return [(v, {"variant": v}, f.format(v=v)) for v in layer["variants"]]
    if "situations" in layer:
        return [(s, {"sit": s}, f.format(v=s)) for s in layer["situations"]]
    return [(None, {}, f)]


def normals_name(fname):
    return fname[:-4] + "_normals.png"


def additive_sprite(em, blur_px=3.0, gain=1.0, halo=0.8):
    """Sprite ADITIVO (lights_add) a partir de um passe de emissao: cor premultiplicada + halo borrado, opaco
    sobre preto (como os PNGs de luz vanilla: preto = nada somado)."""
    a = np.asarray(em, dtype=np.float32) / 255.0
    pm = a[..., :3] * a[..., 3:4]
    im = Image.fromarray(np.clip(pm * 255, 0, 255).astype(np.uint8), "RGB")
    hb = np.asarray(im.filter(ImageFilter.GaussianBlur(blur_px)), dtype=np.float32) / 255.0
    rgb = np.clip((pm + hb * halo) * gain, 0, 1)
    return Image.fromarray(np.dstack([rgb * 255, np.full(rgb.shape[:2], 255.0)]).astype(np.uint8), "RGBA")


def despill_green(path, limit=70):
    """Tira o verde REFLETIDO (luz indireta das placas pintadas) do que nao e pintura: pixels com o verde so um pouco
    acima do vermelho/azul (0 < g - max(r, b) < limit) ficam neutros. O shader do jogo pinta por g - max(r, b)
    (mesmo teste de compose_preview.paint_roof); sem isto o bisel de metal ao lado do casco pintado sai meio
    pintado no jogo. A pintura de verdade (g - max(r, b) > 100) nao muda."""
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im).astype(np.int16).copy()
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = np.maximum(r, b)
    d = g - mx
    spill = (d > 0) & (d < limit)
    a[..., 1] = np.where(spill, mx + (d * 0.15).astype(np.int16), g)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").save(path)


def fade_edges(path, fade):
    """Multiplica o alfa por uma rampa suave (0 na borda -> 1 a 'd' quadros dela) nas bordas pedidas em fade =
    {"top" | "bottom" | "left" | "right": d}. Os normais (se houver) recebem o mesmo alfa depois."""
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im).astype(np.float32).copy()
    h, w = a.shape[:2]
    k = np.ones((h, w), np.float32)
    yy = (np.arange(h) + 0.5)[:, None] / PX
    xx = (np.arange(w) + 0.5)[None, :] / PX
    for side, d in (fade or {}).items():
        dist = {"top": yy, "bottom": h / PX - yy, "left": xx, "right": w / PX - xx}[side]
        r = np.clip(dist / max(1e-6, d), 0, 1)
        k = k * (r * r * (3 - 2 * r))
    a[..., 3] *= k
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").save(path)


def clean_alpha0(path):
    """RGB = 0 onde alfa = 0 (o LANCZOS da reducao deixa cor 'suja' em pixels transparentes perto das bordas)."""
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im).copy()
    z = a[..., 3] == 0
    if z.any() and a[z][:, :3].any():
        a[z] = 0
        Image.fromarray(a, "RGBA").save(path)


def walls_png(W, H, spec, color=(64, 67, 71)):
    """Moldura de parede vanilla de 7 px com sombra interna (igual a render_part.walls_png) e ABERTURAS.

    spec: "closed" | "none" | {"open": [[lado, t0, t1], ...]} (lado top/bottom/left/right; t em quadros ao longo
    do lado, a partir da esquerda (top/bottom) ou de cima (left/right)). Nas aberturas a moldura e a sombra somem e
    as pontas da parede ganham uma tampa escura de 2 px (a parede termina, nao e cortada)."""
    if spec in (None, "none"):
        return None
    im = RP.walls_png(W, H, color)
    if spec == "closed":
        return im
    Wp, Hp = W * PX, H * PX
    a = np.asarray(im).copy()
    depth = 15                                   # moldura (7 px) + sombra interna (7 px) + 1
    caps = []
    for side, t0, t1 in spec.get("open", []):
        p0, p1 = int(round(t0 * PX)), int(round(t1 * PX))
        if side == "top":
            a[0:depth, p0:p1] = 0
            caps += [(p0 - 2, 0, p0, 7), (p1, 0, p1 + 2, 7)]
        elif side == "bottom":
            a[Hp - depth:Hp, p0:p1] = 0
            caps += [(p0 - 2, Hp - 7, p0, Hp), (p1, Hp - 7, p1 + 2, Hp)]
        elif side == "left":
            a[p0:p1, 0:depth] = 0
            caps += [(0, p0 - 2, 7, p0), (0, p1, 7, p1 + 2)]
        elif side == "right":
            a[p0:p1, Wp - depth:Wp] = 0
            caps += [(Wp - 7, p0 - 2, Wp, p0), (Wp - 7, p1, Wp, p1 + 2)]
        else:
            raise SystemExit(f"walls: lado desconhecido {side}")
    out = Image.fromarray(a, "RGBA")
    d = ImageDraw.Draw(out)
    for x0, y0, x1, y1 in caps:
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=(26, 27, 29, 255))
    return out


def _load(path):
    return Image.open(path).convert("RGBA")


# ============================================================================ uma camada
def render_layer(mod, P, layer, out):
    """Renderiza todas as instancias de uma camada. Devolve a entrada do meta.json."""
    name = layer["name"]
    rect = rect_of(P, layer)
    px = rect_px(rect)
    cx, cy = rect_center(P, rect)
    fn = layer.get("fn", name)
    files, norms = [], []
    t0 = time.time()
    for key, kw, fname in instances(layer):
        stem = os.path.join(out, fname[:-4])
        if fn.startswith("pil:"):
            img = getattr(mod, fn[4:])(P, layer, px, **kw)
            if img.size != px:
                raise SystemExit(f"{P['id']}/{name}: a funcao PIL devolveu {img.size}, esperado {px}")
            img.save(stem + ".png")
            files.append(fname)
            continue
        M = fresh(P.get("accent", "amber"))
        B.camera(rect[2], rect[3], (cx, cy))
        samples(layer.get("samples", 48))
        getattr(mod, fn)(M, name, **kw)
        B.show_only([name])
        if key in (None, 1) or key == (layer.get("variants") or layer.get("situations") or [None])[0]:
            RP.warn_empty(name)
        if layer.get("emission_only"):
            em = RP.emission_pass(stem + "_emraw.png", px)
            if layer.get("blend", "add") == "add":
                img = additive_sprite(em, blur_px=layer.get("halo_px", 3.0), gain=layer.get("gain", 1.0))
            else:
                img = RP._oc_glow_sprite(em, blur_px=layer.get("halo_px", 3.0), gain=layer.get("gain", 1.1))
            img.save(stem + ".png")
            files.append(fname)
            continue
        want_n = bool(layer.get("normals"))
        res = B.render_set(stem, px, glow_halo=layer.get("halo", True), normals=want_n, off=False, glow=True)
        if layer.get("despill"):
            despill_green(stem + ".png")
        if layer.get("fade"):
            fade_edges(stem + ".png", layer["fade"])
            if want_n:
                n = np.asarray(_load(stem + "_normals.png")).copy()
                n[..., 3] = np.asarray(_load(stem + ".png"))[..., 3]
                Image.fromarray(n, "RGBA").save(stem + "_normals.png")
        if not layer.get("opaque"):
            clean_alpha0(stem + ".png")
        if layer.get("opaque"):
            base = Image.new("RGBA", px, FLOOR_BG + (255,))
            base.alpha_composite(res["on"])
            base.save(stem + ".png")
            if want_n:
                n = _load(stem + "_normals.png")
                arr = np.asarray(n).copy()
                arr[..., 3] = 255
                Image.fromarray(arr, "RGBA").save(stem + "_normals.png")
        files.append(fname)
        if want_n:
            norms.append(normals_name(fname))
    print(f"  camada {name}: {len(files)} sprite(s) {px[0]}x{px[1]} px, {time.time() - t0:.1f} s")
    ent = {"game_layer": layer["game_layer"], "rect": rect, "files": files, "normals": norms or None}
    if layer.get("at"):
        ent["rects"] = rects_of(P, layer)
    for k in ("levels", "frames", "variants", "situations", "interval", "blend"):
        if k in layer:
            ent[k] = layer[k]
    ent["opaque"] = bool(layer.get("opaque"))
    ent["emission_only"] = bool(layer.get("emission_only"))
    ent["islands"] = bool(layer.get("islands"))
    return ent


# ============================================================================ icone e blueprint
def _add_light(img, spr, xy, gain=1.0):
    """Soma aditiva de um sprite lights_add (RGB sobre preto) onde img ja tem alfa."""
    x, y = xy
    Wi, Hi = img.size
    x0, y0, x1, y1 = max(0, x), max(0, y), min(Wi, x + spr.width), min(Hi, y + spr.height)
    if x1 <= x0 or y1 <= y0:
        return img
    b = np.asarray(img, dtype=np.float32).copy()
    s = np.asarray(spr, dtype=np.float32)[y0 - y:y1 - y, x0 - x:x1 - x]
    add = s[..., :3] * (s[..., 3:4] / 255.0) * gain
    b[y0:y1, x0:x1, :3] = np.clip(b[y0:y1, x0:x1, :3] + add * (b[y0:y1, x0:x1, 3:4] / 255.0), 0, 255)
    return Image.fromarray(b.astype(np.uint8), "RGBA")


def composite(P, out, meta_layers, pick=None, paint=None, roof=True, lights=None):
    """Peca montada (camadas na ordem do jogo, walls.png na camada "walls") a partir dos PNGs gravados.
    pick = {camada: indice da instancia | None (esconde)} (padrao: a 1a); paint = cor que substitui o verde do teto;
    roof=False = vista do interior. As camadas aditivas (lights_add) ficam de fora (o jogo as soma por cima), a nao
    ser as pedidas em lights = {camada: (indice, ganho)}, somadas na posicao do jogo (abaixo dos tetos)."""
    from bsgen.sprites import paint_roof_preview
    W, H = P["size"]
    roofs = ("roofs", "roof_doodads", "roof_turrets", "roof_lights_fancy")
    stack = []
    wp = os.path.join(out, "walls.png")
    if os.path.exists(wp):
        stack.append((GAME_LAYERS.index("walls"), -1, _load(wp), (0, 0)))
    for k, (name, ent) in enumerate(meta_layers.items()):
        gl = ent["game_layer"]
        if gl == "lights_add" or (not roof and gl in roofs):
            continue
        idx = (pick or {}).get(name, 0)
        if idx is None:
            continue
        spr = _load(os.path.join(out, ent["files"][idx]))
        if gl == "roofs" and paint is not None:
            spr = paint_roof_preview(spr, tuple(paint))
        for r in ent_rects(ent):
            stack.append((GAME_LAYERS.index(gl), k, spr, (int(round(r[0] * PX)), int(round(r[1] * PX)))))
    add = []
    for name, (idx, gain) in (lights or {}).items():
        ent = meta_layers.get(name)
        if ent is None or ent["game_layer"] != "lights_add":
            continue
        spr = _load(os.path.join(out, ent["files"][idx]))
        for r in ent_rects(ent):
            add.append((spr, (int(round(r[0] * PX)), int(round(r[1] * PX))), gain))
    img = Image.new("RGBA", (W * PX, H * PX), (0, 0, 0, 0))
    gl_add = GAME_LAYERS.index("lights_add")
    done = False
    for gl, _k, spr, xy in sorted(stack, key=lambda s: (s[0], s[1])):
        if gl > gl_add and not done:
            for a in add:
                img = _add_light(img, *a)
            done = True
        img.alpha_composite(spr, xy)
    if not done:
        for a in add:
            img = _add_light(img, *a)
    return img


def make_icon(P, out, meta_layers):
    ic = P.get("icon")
    if not ic:
        return None
    W, H = P["size"]
    pick = {n: (0 if n in ic.get("layers", meta_layers) else None) for n in meta_layers}
    pick.update(ic.get("pick", {}))
    lights = {n: (v[0], v[1]) for n, v in ic.get("lights", {}).items()}
    img = composite(P, out, meta_layers, pick=pick, paint=ic.get("paint", [120, 124, 132]), lights=lights)
    img = img.resize(tuple(ic["size"]), Image.LANCZOS)
    img.save(os.path.join(out, "icon.png"))
    return "icon.png"


def make_blueprint(P, out, meta_layers):
    names = P.get("blueprint_layers")
    if not names:
        return None
    from bsgen.sprites import blueprint_from
    W, H = P["size"]
    sil = Image.new("RGBA", (W * PX, H * PX), (0, 0, 0, 0))
    for n in names:
        ent = meta_layers.get(n)
        if not ent:
            continue
        spr = _load(os.path.join(out, ent["files"][0]))
        if ent["game_layer"] == "roofs":
            # so a blindagem: o verde (pintura) sai da silhueta
            a = np.asarray(spr).astype(np.int16).copy()
            green = (a[..., 1] - np.maximum(a[..., 0], a[..., 2]) > 12) & (np.abs(a[..., 0] - a[..., 2]) < 64)
            a[..., 3] = np.where(green, 0, a[..., 3])
            spr = Image.fromarray(a.astype(np.uint8), "RGBA")
        for r in ent_rects(ent):
            sil.alpha_composite(spr, (int(round(r[0] * PX)), int(round(r[1] * PX))))
    blueprint_from(W, H, sil).save(os.path.join(out, "blueprints.png"))
    return "blueprints.png"


# ============================================================================ uma peca
def render_layered(mod, P, out, only):
    if P.get("kind") != "layered":
        raise SystemExit(f"{P.get('id')}: kind '{P.get('kind')}' (esperado 'layered')")
    W, H = P["size"]
    os.makedirs(out, exist_ok=True)
    print(f"{P['id']} ({W}x{H}) -> {out}")
    names = [l["name"] for l in P["layers"]]
    if len(set(names)) != len(names):
        raise SystemExit(f"{P['id']}: nomes de camada repetidos")
    for l in P["layers"]:
        if l["game_layer"] not in GAME_LAYERS:
            raise SystemExit(f"{P['id']}/{l['name']}: camada do jogo desconhecida {l['game_layer']}")
        for r in rects_of(P, l):
            if r[0] < -1e-6 or r[1] < -1e-6 or r[0] + r[2] > W + 1e-6 or r[1] + r[3] > H + 1e-6:
                raise SystemExit(f"{P['id']}/{l['name']}: rect {r} fora da peca {W}x{H}")
    layers = {}
    mp = os.path.join(out, "meta.json")
    old = json.load(open(mp)) if (only and os.path.exists(mp)) else {}
    for l in P["layers"]:
        if only and l["name"] not in only and "hull" not in only:
            if l["name"] in old.get("layers", {}):
                ent = dict(old["layers"][l["name"]])
                ent.pop("rects", None)
                if l.get("at"):
                    ent["rects"] = rects_of(P, l)     # as copias seguem o PART mesmo sem re-renderizar
                layers[l["name"]] = ent
            continue
        layers[l["name"]] = render_layer(mod, P, l, out)
    for l in P["layers"]:
        sa = l.get("same_as")
        if not sa or (only and l["name"] not in only and sa["layer"] not in only and "hull" not in only):
            continue
        src_ent = layers.get(sa["layer"])
        if src_ent is None or l["name"] not in layers:
            continue
        if rect_of(P, l) != list(src_ent["rect"]):
            raise SystemExit(f"{P['id']}/{l['name']}: same_as precisa do mesmo rect de {sa['layer']}")
        for f in layers[l["name"]]["files"]:
            me = np.asarray(_load(os.path.join(out, f))).astype(np.float32)
            src = np.asarray(_load(os.path.join(out, src_ent["files"][sa["index"] - 1]))).astype(np.float32)
            o = src.copy()
            o[..., 3] = np.minimum(src[..., 3], me[..., 3])
            o[o[..., 3] == 0] = 0
            Image.fromarray(o.astype(np.uint8), "RGBA").save(os.path.join(out, f))
        print(f"  camada {l['name']}: pixels de {sa['layer']}{sa['index']} (same_as)")
    files = []
    wimg = walls_png(W, H, P.get("walls", "closed"))
    if wimg is not None:
        wimg.save(os.path.join(out, "walls.png"))
        files.append("walls.png")
    for ent in layers.values():
        files += ent["files"] + (ent["normals"] or [])
    meta = {"version": 1, "kind": "layered", "id": P["id"], "size": [W, H], "layers": layers,
            "walls": "walls.png" if wimg is not None else None}
    if all(os.path.exists(os.path.join(out, f)) for e in layers.values() for f in e["files"]):
        ic = make_icon(P, out, layers)
        bp = make_blueprint(P, out, layers)
        if ic:
            meta["icon"] = ic
            files.append(ic)
        if bp:
            meta["blueprints"] = bp
            files.append(bp)
    for k in ("crew_pos", "notes"):
        if k in P:
            meta[k] = P[k]
    meta["files"] = sorted(set(files))
    json.dump(meta, open(mp, "w"), indent=1, ensure_ascii=False)
    return meta


def load_module(arg):
    if arg.endswith(".py") and os.path.isfile(arg):
        src = os.path.abspath(arg)
        short = os.path.splitext(os.path.basename(src))[0]
        spec = importlib.util.spec_from_file_location(f"bs_ext_layered_{short}", src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return short, mod
    return arg, importlib.import_module(f"parts.{arg}")


def main():
    global QUICK
    args = sys.argv[1:]
    short, mod = load_module(args[0])
    QUICK = "--quick" in args
    only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else set()
    want = set(args[args.index("--part") + 1].split(",")) if "--part" in args else set()
    base_out = args[args.index("--out") + 1] if "--out" in args else None
    if hasattr(mod, "PARTS"):
        parts = mod.PARTS
        bad = sorted(want - set(parts))
        if bad:
            raise SystemExit(f"--part desconhecida: {bad} (pecas: {', '.join(parts)})")
        for ps, P in parts.items():
            if want and ps not in want:
                continue
            out = os.path.join(base_out, ps) if base_out else os.path.join(ROOT, "art3d", ps)
            render_layered(mod, P, out, only)
    else:
        out = base_out or os.path.join(ROOT, "art3d", short)
        render_layered(mod, mod.PART, out, only)
    print("OK", short)


if __name__ == "__main__":
    main()
