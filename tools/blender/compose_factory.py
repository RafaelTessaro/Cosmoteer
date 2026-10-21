"""Previa de fabrica + municao (para mostrar a arte fora do jogo).

Uso: python3 tools/blender/compose_factory.py <fabrica> <recurso> <nome_saida>
(<fabrica> = pasta de art3d/, ex.: bs_factory_special para a F2 2.0; o teto leva a placa do 1o modo quando o meta
tem mode_plate.) Gera em docs/preview/3d/:
  <nome_saida>.png  - teto pintado, interior desligado, pilhas 1..N do recurso e o icone (ampliados, pixel a pixel)
  <nome_saida>.gif  - interior da fabrica trabalhando (chao + maquina + paredes + luzes), ampliado
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageChops, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ART = os.path.join(ROOT, "art3d")
OUT = os.path.join(ROOT, "docs", "preview", "3d")
BG = (24, 26, 32, 255)
TILE_BG = (48, 52, 62, 255)


def _load(short, name):
    return Image.open(os.path.join(ART, short, name)).convert("RGBA")


def _roof_tint(im):
    """Pinta o verde do teto (chave de cor do jogo) com a cor padrao das naves (mesma regra de compose_preview)."""
    from compose_preview import paint_roof
    return paint_roof(im, (46, 58, 74))


def plate_on_roof(roof, meta, mode=None):
    """Teto com a placa de modo (2.0: meta mode_plate + art3d/bs_placas/placa_<modo>.png, roof_doodads) no encaixe;
    mode = o modo (padrao: o primeiro). Sem mode_plate ou sem a placa, devolve o teto como veio."""
    mp = meta.get("mode_plate")
    if not mp or not mp.get("modes"):
        return roof
    m = mode or mp["modes"][0]
    p = os.path.join(ART, "bs_placas", f"placa_{m}.png")
    if not os.path.exists(p):
        return roof
    s = int(round(float(mp.get("size", 0.8)) * 64))
    cx, cy = mp["rect_centre"]
    out = roof.copy()
    out.alpha_composite(Image.open(p).convert("RGBA").resize((s, s), Image.LANCZOS),
                        (int(round(cx * 64 - s / 2)), int(round(cy * 64 - s / 2))))
    return out


def _interior(fac, meta, frame):
    hull = meta["hull"]
    base = Image.new("RGBA", _load(fac, hull["floor"]).size, BG)
    base.alpha_composite(_load(fac, hull["floor"]))
    base.alpha_composite(_load(fac, frame))
    if "walls" in hull:
        base.alpha_composite(_load(fac, hull["walls"]))
    if "lights" in hull:
        # camada lights_add do jogo: soma a luz (cor x alfa) por cima
        lights = _load(fac, hull["lights"])
        a = lights.getchannel("A")
        glow = Image.composite(lights, Image.new("RGBA", base.size, (0, 0, 0, 255)), a).convert("RGB")
        rgb = ImageChops.add(base.convert("RGB"), glow)
        base = rgb.convert("RGBA")
    return base


def _up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def main(fac, res, out):
    fm = json.load(open(os.path.join(ART, fac, "meta.json")))
    rm = json.load(open(os.path.join(ART, res, "meta.json")))
    os.makedirs(OUT, exist_ok=True)
    k = 3
    roof = plate_on_roof(_roof_tint(_load(fac, fm["hull"]["roof"])), fm)
    off = _interior(fac, fm, fm["machine"]["off"])
    stacks = [_load(res, f"stack_{i}.png") for i in range(1, rm.get("stack", 6) + 1)]
    icon = _load(res, "icon.png")
    pad = 12
    top_w = off.width * k * 2 + pad * 3
    sk = 3
    cell = 64 * sk
    n = len(stacks) + 1
    cols = min(n, max(1, (top_w - pad) // (cell + pad)))
    rows = (n + cols - 1) // cols
    W = max(top_w, cols * (cell + pad) + pad)
    H = off.height * k + pad * 2 + rows * (cell + pad) + pad
    sheet = Image.new("RGBA", (W, H), BG)
    sheet.alpha_composite(_up(off, k), (pad, pad))
    sheet.alpha_composite(_up(roof, k), (pad * 2 + off.width * k, pad))
    y0 = off.height * k + pad * 2
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(stacks + [icon]):
        cx, cy = pad + (i % cols) * (cell + pad), y0 + (i // cols) * (cell + pad)
        d.rectangle([cx, cy, cx + cell - 1, cy + cell - 1], fill=TILE_BG)
        sheet.alpha_composite(_up(im, sk), (cx, cy))
    sheet.save(os.path.join(OUT, out + ".png"))
    gk = 4
    frames = [_up(_interior(fac, fm, f), gk).convert("RGB") for f in fm["machine"]["frames"]]
    ms = int(round(fm["machine"].get("interval", 0.125) * 1000))
    frames[0].save(os.path.join(OUT, out + ".gif"), save_all=True, append_images=frames[1:], duration=ms, loop=0,
                   optimize=True)
    print(os.path.join(OUT, out + ".png"))
    print(os.path.join(OUT, out + ".gif"))


if __name__ == "__main__":
    main(*sys.argv[1:4])
