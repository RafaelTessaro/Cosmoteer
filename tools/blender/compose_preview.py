"""Monta as previas de uma arma a partir dos sprites renderizados (so Pillow + numpy).

    python3 tools/blender/compose_preview.py <pasta_sprites> [--paint R,G,B]

Gera na mesma pasta:
    preview_ingame.png  -> peca montada na escala do jogo (64 px/tile) e ampliada 3x
    preview_fire.gif    -> torre girando, 3 disparos ("tum, tum, tum") com recuo, clarao e calor
"""

import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PX = 64


def load(d, name):
    return Image.open(os.path.join(d, name)).convert("RGBA")


def paint_roof(img, paint):
    """Simula a pintura da nave: o jogo troca o verde puro do teto pela cor escolhida."""
    a = np.asarray(img, dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mask = np.clip((g - np.maximum(r, b) - 8) / 40.0, 0, 1)
    lum = g / 217.0
    out = a.copy()
    for i in range(3):
        out[..., i] = a[..., i] * (1 - mask) + np.clip(paint[i] * lum * 1.05, 0, 255) * mask
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def paste_center(dst, src, cx, cy):
    dst.alpha_composite(src, (int(round(cx - src.width / 2)), int(round(cy - src.height / 2))))


def turret_layer(d, meta, frame, heat=0.0, size=None):
    """Torre + cano (quadro de recuo) num quadrado centrado no pivo, ainda sem girar."""
    ts = meta["turret_size"]
    root, L, pad = meta["barrel_root"], meta["barrel_len"], meta["recoil_pad"]
    reach = root + L + 0.2
    side = int(math.ceil(2 * max(reach, ts / 2) * PX)) + 4
    lay = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    c = side / 2
    paste_center(lay, load(d, "turret.png"), c, c)
    bar = load(d, f"barrel{frame}.png")
    by = c - (root + (L - pad) / 2) * PX
    paste_center(lay, bar, c, by)
    if heat > 0:
        h = load(d, "barrel_heat.png")
        ha = np.asarray(h, dtype=np.float32)
        ha[..., 3] *= min(1.0, heat * 1.3)
        h = Image.fromarray(ha.astype(np.uint8), "RGBA")
        hy = by + meta["recoil"][frame - 1] * PX  # o calor acompanha o recuo
        paste_center(lay, _fade(h, 0.8), c, hy)
        add_center(lay, h, c, hy, gain=0.6)
    return lay


def shadow_of(layer, off=6, blur=4, op=0.5):
    a = np.asarray(layer.split()[-1], dtype=np.float32) * op
    sh = Image.fromarray(a.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.putalpha(sh)
    shifted = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shifted.alpha_composite(out, (off, off))
    return shifted


def _flame(dr, cx, cy, L, W, ang_deg, col, steps=24):
    """Chama em gota: base arredondada em (cx,cy), ponta a L de distancia na direcao ang (0 = para cima)."""
    a = math.radians(ang_deg)
    ux, uy = math.sin(a), -math.cos(a)      # eixo da chama
    vx, vy = -uy, ux                         # perpendicular
    pts = []
    for i in range(steps + 1):
        t = i / steps
        hw = W * (1 - t) ** 0.9 * min(1.0, 0.45 + t * 5)
        pts.append((cx + ux * L * t + vx * hw, cy + uy * L * t + vy * hw))
    for i in range(steps, -1, -1):
        t = i / steps
        hw = W * (1 - t) ** 0.9 * min(1.0, 0.45 + t * 5)
        pts.append((cx + ux * L * t - vx * hw, cy + uy * L * t - vy * hw))
    dr.polygon(pts, fill=col)


def flash(scale, t, seed=0):
    """Clarao de boca: lingua de fogo para frente + jatos laterais saindo das fendas do freio de boca."""
    S = 4
    U = PX * scale * S
    w = h = int(3.0 * U)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx, cy = w / 2, h / 2
    k = (1 - t) ** 0.8
    rng = np.random.default_rng(seed)
    cols = [(255, 90, 10, 140), (255, 150, 40, 200), (255, 215, 120, 240), (255, 250, 225, 255)]
    for i, col in enumerate(cols):
        f = 1 - i * 0.2
        _flame(dr, cx, cy, U * (1.35 + 0.3 * rng.random()) * k * f, U * 0.27 * k * f, rng.uniform(-4, 4), col)
        for sx in (-1, 1):
            for j in range(3):  # tres fendas de cada lado
                _flame(dr, cx + sx * U * 0.12, cy + U * (0.10 - j * 0.09), U * (0.55 - j * 0.08) * k * f,
                       U * 0.08 * k * f, sx * (78 + j * 6), col)
    im = im.resize((w // S, h // S), Image.LANCZOS)
    glow = im.filter(ImageFilter.GaussianBlur(7 * scale))
    return Image.alpha_composite(glow, im)


def smoke(scale, t, seed=0):
    S = 2
    w = int(2.4 * PX * scale * S)
    im = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    U = PX * scale * S
    for _ in range(9):
        ang = rng.uniform(-1.9, 1.9)
        dist = U * (0.15 + 0.7 * t) * rng.uniform(0.6, 1.2)
        x = w / 2 + math.sin(ang) * dist
        y = w / 2 - math.cos(ang) * dist * 0.9
        r = U * (0.10 + 0.35 * t) * rng.uniform(0.7, 1.2)
        a = int(110 * (1 - t) ** 1.5)
        g = int(rng.uniform(95, 140))
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(g, g, g + 6, a))
    im = im.filter(ImageFilter.GaussianBlur(5 * scale * S / 2)).resize((w // S, w // S), Image.LANCZOS)
    return im


def add_center(dst, src, cx, cy, gain=1.0):
    """Mistura aditiva (luz): soma cor*alpha da imagem no destino."""
    x0, y0 = int(round(cx - src.width / 2)), int(round(cy - src.height / 2))
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(dst.width, x0 + src.width), min(dst.height, y0 + src.height)
    if X1 <= X0 or Y1 <= Y0:
        return
    d = np.asarray(dst, dtype=np.float32).copy()
    s_ = np.asarray(src, dtype=np.float32)[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    d[Y0:Y1, X0:X1, :3] += s_[..., :3] * (s_[..., 3:4] / 255.0) * gain
    d[Y0:Y1, X0:X1, 3] = np.maximum(d[Y0:Y1, X0:X1, 3], s_[..., 3])
    dst.paste(Image.fromarray(np.clip(d, 0, 255).astype(np.uint8), "RGBA"))


def rotate_about_center(img, deg):
    return img.rotate(deg, resample=Image.BICUBIC, expand=False)


def _fade(img, k):
    a = np.asarray(img, dtype=np.float32).copy()
    a[..., 3] *= k
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def crop_content(img, bg, pad=12):
    a = np.asarray(img.convert("RGB"), dtype=np.int16)
    diff = np.abs(a - np.array(bg, dtype=np.int16)).sum(axis=2) > 6
    ys, xs = np.where(diff)
    return img.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), min(img.width, xs.max() + pad),
                     min(img.height, ys.max() + pad)))


def assemble(d, meta, roof, frame=1, heat=0.0, angle=0.0, fx=None, scale=1, bg=(7, 9, 14)):
    """Monta a peca inteira (teto, sombra, torre, cano, efeitos) num quadro."""
    W, H = meta["part_size"]
    pvx, pvy = meta["pivot"]
    reach = meta["barrel_root"] + meta["barrel_len"] + 0.6
    top = max(0.0, reach - pvy) + 0.2
    side = max(0.0, reach - pvx, reach - (W - pvx)) + 0.2
    cw, ch = int((W + 2 * side) * PX), int((H + top + 0.4) * PX)
    canvas = Image.new("RGBA", (cw, ch), bg + (255,))
    ox, oy = int(side * PX), int(top * PX)
    canvas.alpha_composite(roof, (ox, oy))
    lay = turret_layer(d, meta, frame, heat)
    lay = rotate_about_center(lay, angle)
    px, py = ox + pvx * PX, oy + pvy * PX
    paste_center(canvas, shadow_of(lay), px, py)
    paste_center(canvas, lay, px, py)
    if fx:
        a = math.radians(angle)
        muzzle = meta["barrel_root"] + meta["barrel_len"] - meta["recoil"][frame - 1]
        for img, dist, additive in fx:
            mx = px - math.sin(a) * (muzzle + dist) * PX
            my = py - math.cos(a) * (muzzle + dist) * PX
            r = rotate_about_center(img, angle)
            if additive:
                add_center(canvas, r, mx, my, gain=1.2)
                paste_center(canvas, _fade(r, 0.35), mx, my)
            else:
                paste_center(canvas, r, mx, my)
    if scale != 1:
        canvas = canvas.resize((cw * scale, ch * scale), Image.LANCZOS)
    return canvas


def main():
    d = sys.argv[1]
    paint = (46, 58, 74)
    if "--paint" in sys.argv:
        paint = tuple(int(v) for v in sys.argv[sys.argv.index("--paint") + 1].split(","))
    meta = json.load(open(os.path.join(d, "meta.json")))
    roof = paint_roof(load(d, "roof.png"), paint)

    # vista do jogo: 1x e 3x lado a lado
    one = crop_content(assemble(d, meta, roof), (7, 9, 14))
    three = one.resize((one.width * 3, one.height * 3), Image.LANCZOS)
    sheet = Image.new("RGBA", (one.width + three.width + 48, three.height + 32), (7, 9, 14, 255))
    sheet.alpha_composite(one, (16, 16 + three.height - one.height))
    sheet.alpha_composite(three, (one.width + 32, 16))
    sheet.convert("RGB").save(os.path.join(d, "preview_ingame.png"))

    # GIF: gira para mirar, dispara 3 vezes (tum, tum, tum), esfria
    frames, durs = [], []
    SC = 2
    aim = -28.0
    for i in range(10):  # gira
        t = (i + 1) / 10
        ang = aim * (1 - math.cos(t * math.pi)) / 2
        frames.append(assemble(d, meta, roof, angle=ang, scale=SC))
        durs.append(40)
    heat = 0.0
    seq = [2, 3, 4, 5, 1, 1, 1, 1, 1, 1]  # quadros de recuo depois de cada tiro
    for shot in range(3):
        heat = min(1.0, heat + 0.45)
        for j, fr in enumerate(seq):
            fx = []
            if j < 3:
                fx.append((flash(1.0, j / 3, seed=shot * 7 + j), -0.14, True))
            if 0 < j < 9:
                fx.append((smoke(1.0, j / 9, seed=shot), 0.25 + j * 0.03, False))
            frames.append(assemble(d, meta, roof, frame=fr, heat=heat, angle=aim, fx=fx, scale=SC))
            durs.append(40)
            heat *= 0.97
    for i in range(14):  # esfriando
        heat *= 0.82
        frames.append(assemble(d, meta, roof, frame=1, heat=heat, angle=aim, scale=SC))
        durs.append(60)
    for i in range(10):  # volta
        t = (i + 1) / 10
        ang = aim * (1 + math.cos(t * math.pi)) / 2
        frames.append(assemble(d, meta, roof, angle=ang, scale=SC))
        durs.append(40)
    # recorta todos os quadros na mesma caixa (uniao do conteudo)
    boxes = []
    for f in frames:
        a = np.asarray(f.convert("RGB"), dtype=np.int16)
        ys, xs = np.where(np.abs(a - np.array((7, 9, 14), dtype=np.int16)).sum(axis=2) > 6)
        boxes.append((xs.min(), ys.min(), xs.max(), ys.max()))
    bx = (max(0, min(b[0] for b in boxes) - 16), max(0, min(b[1] for b in boxes) - 16),
          min(frames[0].width, max(b[2] for b in boxes) + 16), min(frames[0].height, max(b[3] for b in boxes) + 16))
    pal = [f.crop(bx).convert("RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
           for f in frames]
    pal[0].save(os.path.join(d, "preview_fire.gif"), save_all=True, append_images=pal[1:], duration=durs, loop=0,
                optimize=False, disposal=1)
    print("OK", len(frames), "quadros")


if __name__ == "__main__":
    main()
