"""Monta as previas de uma arma a partir dos sprites renderizados (so Pillow + numpy).

    python3 tools/blender/compose_preview.py <pasta_sprites> [--paint R,G,B]

Gera na mesma pasta:
    preview_ingame.png  -> peca montada na escala do jogo (64 px/tile) e ampliada 3x
    preview_fire.gif    -> torre girando, 3 disparos ("tum, tum, tum") com recuo, clarao e calor
Lancadores (meta kind "launcher"): o casulo com o rack cheio (1x e 3x) e um GIF com a salva em LIFO tubo a tubo
(o nivel do rack cai uma unidade por lancamento, clarao no tubo e baforada de sopro) e a recarga unidade a unidade.
Pecas "layered" (meta kind "layered", make_layered; render_layered.py: Tupa, paiois, Fita, placas):

    python3 tools/blender/compose_preview.py <pasta> [--sub 1x1] [--sheet PNG] [--gif GIF]

    folha com a peca montada como no jogo (interior e teto pintado, 1x e 3x; placa de tipo do meta no teto; digitos
    do paiol so com o switch paiol_counter, desligado nos builds) e uma tira por camada com mais de um sprite (so os
    quadros levam tempo no rotulo; niveis seguem o estoque/valor); GIF com as camadas de quadros/niveis rodando
    juntas (variantes = escolha fixa: so tira; pasta shared: --sub escolhe a peca; sem quadros nem niveis, ex.
    placas, nao ha GIF). Grupos alternativos (*_sai / *_entra do FX da Fita, toggles separados no jogo) saem um por
    linha, nunca juntos; peca so de FX: o interior leva um fundo escuro para a luz aditiva aparecer.
Projeteis (meta kind "missiles" / "shells", make_projectiles):

    python3 tools/blender/compose_preview.py <pasta_sprites> [--sheet PNG] [--gif GIF]

    folha com cada item a 1x e 3x (64 px/tile no jogo) sobre placas de casco, com uma chama/tracante simples na cor
    do tipo atras do bocal, as luzes (quadro 0) somadas e a faixa da granada tingida; GIF com os atlas de luzes
    animados (fps de cada item, WrapMode Clamp segura o ultimo quadro). Padrao: preview_projectiles.png e
    preview_lights.gif na pasta.
"""

import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PX = 64


def load(d, name):
    return Image.open(os.path.join(d, name)).convert("RGBA")


def paint_roof(img, paint):
    """Simula a pintura da nave: o jogo troca o verde puro do teto pela cor escolhida."""
    a = np.asarray(img, dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # mesmo teste do shader do jogo: verde acima de vermelho e azul E vermelho ~ azul (|r - b| < 0.25); sem a segunda
    # condicao os LEDs verdes do teto (ex.: fundicao nuclear) seriam pintados na previa, mas nao no jogo
    mask = np.clip((g - np.maximum(r, b) - 8) / 40.0, 0, 1) * (np.abs(r - b) < 64)
    lum = g / 217.0
    out = a.copy()
    for i in range(3):
        out[..., i] = a[..., i] * (1 - mask) + np.clip(paint[i] * lum * 1.05, 0, 255) * mask
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def paste_center(dst, src, cx, cy):
    dst.alpha_composite(src, (int(round(cx - src.width / 2)), int(round(cy - src.height / 2))))


def turret_layer(d, meta, bframes, tframe=0, fx=None):
    """Torre + canos num quadrado centrado no pivo, ainda sem girar.

    bframes: um nome de PNG por cano (quadro atual de cada cano). fx: [(img, x_frente, y_lado, aditivo)]."""
    ts = meta["turret_size"]
    br = meta["barrel"]
    reach = br["root"] + br["length"] + 1.4
    side = int(math.ceil(2 * max(reach, ts / 2) * PX)) + 4
    lay = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    c = side / 2
    tf = meta["turret"]["frames"]
    paste_center(lay, load(d, tf[tframe % len(tf)]), c, c)
    for y, name in zip(br["ys"], bframes):
        paste_center(lay, load(d, name), c + y * PX, c - br["center"] * PX)
    for img, fwd, lat, additive in (fx or []):
        if additive:
            add_center(lay, img, c + lat * PX, c - fwd * PX, gain=1.2)
            paste_center(lay, _fade(img, 0.35), c + lat * PX, c - fwd * PX)
        else:
            paste_center(lay, img, c + lat * PX, c - fwd * PX)
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


FIRE_COLS = [(255, 90, 10, 140), (255, 150, 40, 200), (255, 215, 120, 240), (255, 250, 225, 255)]
PLASMA_COLS = [(20, 140, 255, 140), (40, 200, 255, 200), (150, 240, 255, 240), (240, 255, 255, 255)]


def flash(scale, t, seed=0, cols=None):
    """Clarao de boca: lingua de fogo para frente + jatos laterais saindo das fendas do freio de boca."""
    S = 4
    U = PX * scale * S
    w = h = int(3.0 * U)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx, cy = w / 2, h / 2
    k = (1 - t) ** 0.8
    rng = np.random.default_rng(seed)
    cols = cols or FIRE_COLS
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


def assemble(d, meta, roof, bframes=None, tframe=0, angle=0.0, fx=None, scale=1, bg=(7, 9, 14)):
    """Monta a peca inteira (teto, sombra, torre, canos, efeitos) num quadro."""
    W, H = meta["size"]
    pvx, pvy = meta["pivot"]
    br = meta["barrel"]
    bframes = bframes or [br["rest"]] * len(br["ys"])
    reach = br["root"] + br["length"] + 1.4
    top = max(0.0, reach - pvy) + 0.2
    side = max(0.0, reach - pvx, reach - (W - pvx)) + 0.2
    cw, ch = int((W + 2 * side) * PX), int((H + top + 0.4) * PX)
    canvas = Image.new("RGBA", (cw, ch), bg + (255,))
    ox, oy = int(side * PX), int(top * PX)
    canvas.alpha_composite(roof, (ox, oy))
    lay = turret_layer(d, meta, bframes, tframe, fx)
    lay = rotate_about_center(lay, angle)
    px, py = ox + pvx * PX, oy + pvy * PX
    paste_center(canvas, shadow_of(lay), px, py)
    paste_center(canvas, lay, px, py)
    if scale != 1:
        canvas = canvas.resize((cw * scale, ch * scale), Image.LANCZOS)
    return canvas


def _crop_frames(frames, bg=(7, 9, 14)):
    boxes = []
    for f in frames:
        a = np.asarray(f.convert("RGB"), dtype=np.int16)
        ys, xs = np.where(np.abs(a - np.array(bg, dtype=np.int16)).sum(axis=2) > 6)
        boxes.append((xs.min(), ys.min(), xs.max(), ys.max()))
    bx = (max(0, min(b[0] for b in boxes) - 16), max(0, min(b[1] for b in boxes) - 16),
          min(frames[0].width, max(b[2] for b in boxes) + 16), min(frames[0].height, max(b[3] for b in boxes) + 16))
    return [f.crop(bx) for f in frames]


def make_all(d, paint=(46, 58, 74), scale=2):
    meta = json.load(open(os.path.join(d, "meta.json")))
    if meta.get("kind") == "launcher":
        return make_all_launcher(d, meta, paint, scale)
    if meta.get("kind") in PROJ_KINDS:
        return make_projectiles(d, paint=paint)
    roof = paint_roof(load(d, "roof.png"), paint)
    br = meta["barrel"]
    nb = len(br["ys"])

    # vista do jogo: 1x e 3x lado a lado
    one = crop_content(assemble(d, meta, roof), (7, 9, 14))
    three = one.resize((one.width * 3, one.height * 3), Image.LANCZOS)
    sheet = Image.new("RGBA", (one.width + three.width + 48, three.height + 32), (7, 9, 14, 255))
    sheet.alpha_composite(one, (16, 16 + three.height - one.height))
    sheet.alpha_composite(three, (one.width + 32, 16))
    sheet.convert("RGB").save(os.path.join(d, "preview_ingame.png"))

    # GIF: gira para mirar, dispara, esfria e volta
    pattern = meta.get("preview_pattern", "single")
    seq = br["frames"]                      # ordem do jogo: quadros de tiro ... repouso
    spin = br["anim"] == "spin"
    frames, durs = [], []
    aim = -28.0
    tf = 0
    ntf = len(meta["turret"]["frames"])
    for i in range(10):
        t = (i + 1) / 10
        frames.append(assemble(d, meta, roof, tframe=tf, angle=aim * (1 - math.cos(t * math.pi)) / 2, scale=scale))
        durs.append(40)
        tf += 1 if ntf > 1 else 0
    if pattern in ("single", "volley"):
        groups = [list(range(nb))] * 3
    elif pattern == "pairs":
        half = max(1, nb // 2)
        groups = [[i for i in range(nb) if i % half == k % half] for k in range(6)]
    elif pattern == "rotary":
        groups = [[0]] * 24
    else:  # alternate
        groups = [[k % nb] for k in range(max(4, nb * 2))]
    # canhoes lentos: espera o calor esfriar entre os tiros; rotativos/metralhadoras: rajada rapida
    small = br["sprite_w"] < 0.3 and not spin   # metralhadoras: tiro rapido ("tatata"), nao cadencia de canhao
    gap = max(10, len(seq) + 2) if pattern in ("single", "volley") and not small else (2 if pattern == "rotary" else (3 if small else 4))
    if small and pattern in ("single", "volley"):
        groups = [list(range(nb))] * 10
    # tamanho do clarao/fumaca pelo calibre (largura do sprite do cano; 0.46 = 76 mm)
    fsc = 0.55 if spin else min(2.2, max(0.3, br["sprite_w"] / 0.46))
    plasma = meta.get("preview_fx") == "plasma" or meta.get("accent") == "cyan"
    state = [len(seq) - 1] * nb             # indice do quadro atual de cada cano (comeca em repouso)
    shot_fx = []                            # (barril, idade)
    smokes = []
    step = 0
    total = len(groups) * gap + 16
    for t in range(total):
        if t % gap == 0 and t // gap < len(groups):
            for bi in groups[t // gap]:
                state[bi] = 0
                shot_fx.append([bi, 0])
                smokes.append([bi, 0, step])
                step += 1
        fx = []
        for item in shot_fx:
            bi, age = item
            if age < 3:
                fx.append((flash(fsc, age / 3, seed=step * 7 + age, cols=PLASMA_COLS if plasma else None),
                           br["muzzle"] - 0.14 * fsc, br["ys"][bi], True))
            item[1] += 1
        for item in smokes:
            bi, age, sd = item
            if 0 < age < 9 and not plasma:   # plasma nao solta fumaca
                fx.append((smoke(max(0.6, fsc * 0.9), age / 9, seed=sd), br["muzzle"] + 0.25 * fsc + age * 0.03,
                           br["ys"][bi], False))
            item[1] += 1
        shot_fx = [x for x in shot_fx if x[1] < 3]
        smokes = [x for x in smokes if x[1] < 9]
        if spin and t < len(groups) * gap:
            bnames = [seq[t % len(seq)]] * nb   # giro uniforme: quadros borrados + repouso, como no jogo
        else:
            bnames = [seq[min(st, len(seq) - 1)] for st in state]
        frames.append(assemble(d, meta, roof, bframes=bnames, tframe=tf, angle=aim, fx=fx, scale=scale))
        durs.append(40)
        state = [min(st + 1, len(seq) - 1) for st in state]
        tf += 1 if ntf > 1 else 0
    for i in range(10):
        t = (i + 1) / 10
        frames.append(assemble(d, meta, roof, tframe=tf, angle=aim * (1 + math.cos(t * math.pi)) / 2, scale=scale))
        durs.append(40)
        tf += 1 if ntf > 1 else 0
    frames = _crop_frames(frames)
    # pecas grandes: limita o tamanho do GIF (envio maximo ~30 MB)
    k = min(1.0, 760 / max(frames[0].size))
    if k < 1:
        frames = [f.resize((int(f.width * k), int(f.height * k)), Image.LANCZOS) for f in frames]
    pal = [f.convert("RGB").quantize(colors=200, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
           for f in frames]
    pal[0].save(os.path.join(d, "preview_fire.gif"), save_all=True, append_images=pal[1:], duration=durs, loop=0,
                optimize=True, disposal=1)
    return len(frames)



# ============================================================================ lancadores de misseis
LAUNCH_REACH = 1.9      # tiles a frente do pivo mostrados no GIF (voo dos misseis), no minimo


def _reach(meta):
    return max(LAUNCH_REACH, meta["turret_size"] / 2 + 1.0)


_TFRAMES = {}


def _turret_frame(d, meta, i, thr=8):
    """Quadro i da animacao da torre para a previa: pixels que so diferem do 1o quadro pelo ruido do render
    (<= thr niveis) ficam iguais aos do 1o quadro, entao o GIF guarda so o que anima de verdade (brasa, olho)."""
    tf = meta["turret"]["frames"]
    key = (d, i % len(tf))
    if key not in _TFRAMES:
        im = load(d, tf[key[1]])
        if key[1]:
            a0 = np.asarray(_turret_frame(d, meta, 0), dtype=np.int16)
            a = np.asarray(im, dtype=np.int16).copy()
            if a.shape == a0.shape:
                keep = np.abs(a - a0).max(axis=2) <= thr
                a[keep] = a0[keep]
                im = Image.fromarray(a.astype(np.uint8), "RGBA")
        _TFRAMES[key] = im
    return _TFRAMES[key]


def _launcher_layer(d, meta, look, level, tframe=0, fx=None, side=None, oc=False):
    """Casulo + nivel do rack (ResourceSprites) num quadrado centrado no pivo, ainda sem girar.

    level: unidades carregadas (0..N). fx: [(img, frente, lado, aditivo)] em coordenadas da torre.
    oc: soma o brilho do overclock (turret_oc.png, OverclockGlowGraphics) por cima."""
    ts = meta["turret_size"]
    T = int(round(ts * PX))
    side = side or int(math.ceil(2 * _reach(meta) * PX)) + 4
    lay = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    c = side / 2
    x0, y0 = int(round(c - T / 2)), int(round(c - T / 2))
    lay.alpha_composite(_turret_frame(d, meta, tframe), (x0, y0))
    for ov in meta["modes"][look]["overlays"]:
        a, b = ov["range"]
        n = max(0, min(b - a, level - a))
        r = ov.get("rect") or [0, 0, T, T]
        lay.alpha_composite(load(d, ov["files"][n]), (x0 + r[0], y0 + r[1]))
    sh = meta["modes"][look].get("shutters")
    if sh:                      # persianas fechadas dos casulos sem unidade neste modo (quadro da torre)
        lay.alpha_composite(load(d, sh["file"]), (x0, y0))
    if oc and meta["turret"].get("oc_glow"):
        lay.alpha_composite(load(d, meta["turret"]["oc_glow"]), (x0, y0))
    for img, fwd, lat, additive in (fx or []):
        if additive:
            add_center(lay, img, c + lat * PX, c - fwd * PX, gain=1.2)
            paste_center(lay, _fade(img, 0.35), c + lat * PX, c - fwd * PX)
        else:
            paste_center(lay, img, c + lat * PX, c - fwd * PX)
    return lay


def _launcher_frame(d, meta, roof, look, level, tframe=0, angle=0.0, fx=None, scale=1, bg=(7, 9, 14), oc=False):
    """Peca inteira: teto, sombra do casulo, casulo + rack + efeitos girados juntos (ChainedTo Turret)."""
    W, H = meta["size"]
    pvx, pvy = meta["pivot"]
    reach = _reach(meta)
    top = max(0.0, reach - pvy) + 0.2
    side = max(0.0, reach - pvx, reach - (W - pvx)) + 0.2
    cw, ch = int((W + 2 * side) * PX), int((H + top + 0.4) * PX)
    canvas = Image.new("RGBA", (cw, ch), bg + (255,))
    ox, oy = int(side * PX), int(top * PX)
    canvas.alpha_composite(roof, (ox, oy))
    px, py = ox + pvx * PX, oy + pvy * PX
    base = rotate_about_center(_launcher_layer(d, meta, look, level, tframe), angle)
    paste_center(canvas, shadow_of(base), px, py)
    lay = rotate_about_center(_launcher_layer(d, meta, look, level, tframe, fx, oc=oc), angle) if (fx or oc) \
        else base
    paste_center(canvas, lay, px, py)
    if scale != 1:
        canvas = canvas.resize((cw * scale, ch * scale), Image.LANCZOS)
    return canvas


def tube_flash(scale, t, seed=0):
    """Clarao pequeno na boca do tubo (missile_launcher_shoot_flash): nucleo claro + lingua curta para frente."""
    S = 4
    U = PX * scale * S
    w = int(1.2 * U)
    im = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    k = (1 - t) ** 0.8
    rng = np.random.default_rng(seed)
    for i, col in enumerate(FIRE_COLS):
        f = 1 - i * 0.22
        _flame(dr, w / 2, w / 2 + U * 0.04, U * (0.42 + 0.1 * rng.random()) * k * f, U * 0.10 * k * f,
               rng.uniform(-6, 6), col)
        r = U * 0.11 * k * f
        dr.ellipse([w / 2 - r, w / 2 - r, w / 2 + r, w / 2 + r], fill=col)
    im = im.resize((w // S, w // S), Image.LANCZOS)
    return Image.alpha_composite(im.filter(ImageFilter.GaussianBlur(3 * scale)), im)


def micro_missile(scale, age):
    """Micromissil em voo (frente para cima): corpo claro, nariz e pluma ambar que cresce."""
    S = 4
    U = PX * scale * S
    w, h = int(0.5 * U), int(1.3 * U)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx, cy = w / 2, h * 0.30
    L, R = U * 0.24, U * 0.035
    pl = U * (0.18 + 0.12 * min(age, 3))
    for i, col in enumerate(FIRE_COLS):
        f = 1 - i * 0.2
        _flame(dr, cx, cy + L / 2, pl * f, R * 1.6 * f, 180, col)
    dr.rounded_rectangle([cx - R, cy - L / 2, cx + R, cy + L / 2], radius=R, fill=(205, 208, 214, 255))
    dr.polygon([(cx - R, cy - L / 2 + R), (cx + R, cy - L / 2 + R), (cx, cy - L / 2 - R * 1.6)], fill=(232, 234, 238, 255))
    dr.rectangle([cx - R, cy - L / 2 + R * 1.2, cx + R, cy - L / 2 + R * 2.0], fill=(255, 176, 0, 255))
    im = im.resize((w // S, h // S), Image.LANCZOS)
    return Image.alpha_composite(im.filter(ImageFilter.GaussianBlur(2 * scale)), im)


def backblast_puff(scale, t, seed=0):
    """Baforada de sopro atras do casulo (chaingun_shoot_smoke): leque de fumaca clara indo para tras (baixo)."""
    S = 2
    w = int(1.8 * PX * scale * S)
    im = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    U = PX * scale * S
    for _ in range(10):
        ang = rng.uniform(-1.2, 1.2)
        dist = U * (0.05 + 0.55 * t) * rng.uniform(0.5, 1.1)
        x = w / 2 + math.sin(ang) * dist
        y = w / 2 + math.cos(ang) * dist * 0.8
        r = U * (0.08 + 0.26 * t) * rng.uniform(0.7, 1.2)
        a = int(165 * (1 - t) ** 1.3)
        g = int(rng.uniform(150, 190))
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(g, g, g + 6, a))
    return im.filter(ImageFilter.GaussianBlur(4 * scale)).resize((w // S, w // S), Image.LANCZOS)


def make_all_launcher(d, meta, paint=(46, 58, 74), scale=2):
    """Previas do lancador: casulo com o rack cheio (1x e 3x) e GIF girando, salva em LIFO tubo a tubo (o nivel
    do rack cai uma unidade por lancamento, clarao em cada tubo + baforada de sopro atras), recarga unidade
    a unidade e, no fim, o rack cheio dos outros modos com unidade diferente (pesado, torpedo, persianas)."""
    roof = paint_roof(load(d, "roof.png"), paint)
    looks = list(meta["modes"])
    look = looks[0]
    units = len(meta["modes"][look]["units"])
    bg = (7, 9, 14)

    # vista do jogo: 3x com o rack cheio do 1o modo + grade 1x com todos os modos (rack cheio) e, se houver,
    # o 1o modo em overclock (turret_oc.png por cima); a grade cresce em colunas e nunca sai da folha
    def still(lk, oc=False):
        c = _launcher_frame(d, meta, roof, lk, len(meta["modes"][lk]["units"]), oc=oc)
        return crop_content(c, bg)
    one = still(look)
    smalls = [one] + [still(lk) for lk in looks[1:]]
    if meta["turret"].get("oc_glow"):
        smalls.append(still(look, oc=True))
    three = one.resize((one.width * 3, one.height * 3), Image.LANCZOS)
    cw_, ch_ = max(s.width for s in smalls), max(s.height for s in smalls)
    rows = max(1, (three.height + 12) // (ch_ + 12))
    cols = -(-len(smalls) // rows)
    left_w = cols * (cw_ + 12) - 12
    sheet = Image.new("RGBA", (left_w + three.width + 48, max(three.height, rows * (ch_ + 12) - 12) + 32),
                      bg + (255,))
    for i, im in enumerate(smalls):
        sheet.alpha_composite(im, (16 + (i // rows) * (cw_ + 12), 16 + (i % rows) * (ch_ + 12)))
    sheet.alpha_composite(three, (left_w + 32, 16))
    sheet.convert("RGB").save(os.path.join(d, "preview_ingame.png"))

    # GIF (40 ms por quadro): mira, salva em ripple (4/30 s ~ 3 quadros; 2o tubo do cassete 2/30 s ~ 2 quadros
    # depois do 1o), recarga unidade a unidade, volta
    ntf = len(meta["turret"]["frames"])
    tf_every = max(1, int(round(meta["turret"].get("interval", 0.12) / 0.04))) if ntf > 1 else 0
    tubes = meta["modes"][look]["tubes"]
    upods = meta["modes"][look].get("unit_pods") or [0] * units
    bb = (meta.get("backblast") or [[-0.5, 0.0]])
    reach = _reach(meta)
    frames, durs = [], []
    aim = -28.0
    clock = [0]

    def tfr():
        return (clock[0] // tf_every) % ntf if tf_every else 0

    def push(img):
        frames.append(img)
        durs.append(40)
        clock[0] += 1

    for i in range(10):
        t = (i + 1) / 10
        push(_launcher_frame(d, meta, roof, look, units, tfr(), aim * (1 - math.cos(t * math.pi)) / 2, scale=scale))
    for _ in range(3):
        push(_launcher_frame(d, meta, roof, look, units, tfr(), aim, scale=scale))
    # racks grandes (Mula: 48): ripple de 2 quadros (~2/30 s do jogo) e recarga mais curta por unidade, senao o
    # GIF passa de ~15 MB
    big = units > 24
    ripple, burst = (2 if big else 3), 2
    events = []                 # (quadro, unidade, tubo)
    for k in range(units):
        u = units - 1 - k       # LIFO: a ultima unidade carregada sai primeiro
        for j in range(len(tubes[u])):
            events.append((k * ripple + j * burst, u, j))
    fsc = max(0.5, min(1.4, meta["turret_size"] / 2.0))
    last = max(e[0] for e in events)
    level = units
    for f in range(last + 12):
        fx = []
        for (f0, u, j) in events:
            age = f - f0
            if age == 0 and j == 0:
                level = u       # o rack perde a unidade no 1o tiro do cassete
            if age < 0:
                continue
            fwd, lat = tubes[u][j]
            if age < 8:         # missil saindo do tubo e acelerando para frente
                s = 0.10 + 0.22 * age + 0.06 * age * age
                if fwd + s < reach - 0.2:
                    fx.append((micro_missile(scale=1, age=age), fwd + s + 0.12, lat, False))
            if age < 3:
                fx.append((tube_flash(fsc, age / 3, seed=f0 * 5 + j), fwd + 0.08, lat, True))
            if age < 9 and j == 0:
                # uma baforada no ponto de sopro do casulo que disparou (so fumaca: as regras nao poem chama ali)
                b = bb[upods[u]] if upods[u] < len(bb) else bb[0]
                fx.append((backblast_puff(fsc, age / 9, seed=f0 + 3), b[0] - 0.08 - age * 0.03, b[1], False))
        push(_launcher_frame(d, meta, roof, look, level, tfr(), aim, fx=fx, scale=scale))
    for lv in range(units + 1):       # recarga: uma unidade por vez
        for _ in range(2 if big else 4):
            push(_launcher_frame(d, meta, roof, look, lv, tfr(), aim, scale=scale))
    for _ in range(4):
        push(_launcher_frame(d, meta, roof, look, units, tfr(), aim, scale=scale))
    for i in range(10):
        t = (i + 1) / 10
        push(_launcher_frame(d, meta, roof, look, units, tfr(), aim * (1 + math.cos(t * math.pi)) / 2, scale=scale))
    # fecho: rack cheio dos outros modos com unidade diferente (pesado, torpedo, persianas), ~0.5 s cada
    seen = {units}
    for lk in looks[1:]:
        n = len(meta["modes"][lk]["units"])
        if n in seen:
            continue
        seen.add(n)
        for _ in range(13):
            push(_launcher_frame(d, meta, roof, lk, n, tfr(), 0.0, scale=scale))
    frames = _crop_frames(frames)
    k = min(1.0, (640 if big else 760) / max(frames[0].size))
    if k < 1:
        frames = [f.resize((int(f.width * k), int(f.height * k)), Image.LANCZOS) for f in frames]
    _save_gif_shared(frames, durs, os.path.join(d, "preview_fire.gif"))
    return len(frames)


def _save_gif_shared(frames, durs, path, colors=255):
    """GIF com UMA paleta para todos os quadros (amostrada de varios quadros, inclusive os de clarao): as areas
    paradas ficam identicas entre quadros e o Pillow grava so o retangulo que mudou (paleta por quadro mudava
    a imagem inteira e o GIF do lancador de 48 tubos passava de 30 MB)."""
    step = max(1, len(frames) // 32)
    samples = [f.convert("RGB").resize((max(1, f.width // 2), max(1, f.height // 2)), Image.BILINEAR)
               for f in frames[::step]]
    sheet = Image.new("RGB", (samples[0].width, sum(s.height for s in samples)))
    y = 0
    for s_ in samples:
        sheet.paste(s_, (0, y))
        y += s_.height
    pal = sheet.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=False, disposal=1)


# ============================================================================ projeteis (misseis e granadas)
PROJ_KINDS = ("missiles", "shells")
# cor da chama (misseis, pelo tipo = 1o pedaco da chave) / do tracante (granadas, pela municao), so para a previa
MOCK_COLORS = {"he": (255, 170, 60), "cluster": (255, 214, 90), "limpet": (255, 70, 50), "napalm": (255, 120, 30),
               "emp": (110, 170, 255), "torpedo": (215, 232, 255), "nuclear": (120, 255, 80), "nuke": (120, 255, 60),
               "ap": (190, 215, 255), "aphe": (255, 95, 45)}
# cor da faixa das granadas (VertexColor da mascara no jogo; ammo_colors.band da tabela de calibre)
MASK_COLORS = {"he": (255, 190, 60), "ap": (215, 230, 255), "aphe": (255, 80, 40), "emp": (80, 150, 255)}


def palette_2_0():
    """SPEC.art_assets.palette (tools/spec/bullet_strike_art2.json): a paleta 2.0 (AC carmim, Tupa AZUL eletrico).
    {} sem o arquivo (rascunhos fora do repositorio)."""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spec", "bullet_strike_art2.json")
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)["art_assets"]["palette"]
    except (OSError, KeyError, ValueError):
        return {}


def _palette_colors():
    """Cores 2.0 das previas: tracante (MOCK_COLORS) e faixa (MASK_COLORS) por municao; slug/rail no azul da Tupa
    (palette.rail glow/core, nunca violeta)."""
    pal = palette_2_0()
    for k in ("he", "ap", "sap", "ac", "frag", "pem"):
        c = pal.get(k) or {}
        if c.get("tracer") or c.get("glow"):
            MOCK_COLORS[k] = tuple(c.get("tracer") or c.get("glow"))
        if c.get("band"):
            MASK_COLORS[k] = tuple(c["band"])
    rail = pal.get("rail") or {}
    if rail.get("glow"):
        MOCK_COLORS["slug"] = MOCK_COLORS["rail"] = tuple(rail["glow"])
    if rail.get("core"):
        MASK_COLORS["slug"] = tuple(rail["core"])


_palette_colors()


def _font():
    try:
        return ImageFont.load_default(12)
    except TypeError:
        return ImageFont.load_default()


def _font_ui(size=13):
    """Fonte com acentos para as legendas em pt-BR das previas layered (a fonte padrao do Pillow nao tem 'í')."""
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
              "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return _font()


def hull_tiles(w, h, paint=(46, 58, 74), tile=PX):
    """Fundo de placas de casco pintadas (tile px por placa): fresta escura, chanfro claro em cima/esquerda."""
    base = tuple(int(c * 0.85) for c in paint)
    im = Image.new("RGBA", (w, h), base + (255,))
    dr = ImageDraw.Draw(im)
    g = max(1, tile // 32)
    hi = tuple(min(255, int(c * 1.18) + 6) for c in paint)
    lo = tuple(int(c * 0.55) for c in paint)
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            dr.rectangle([x0, y0, x0 + tile - 1, y0 + tile - 1], fill=(14, 15, 17, 255))
            dr.rectangle([x0 + g, y0 + g, x0 + tile - 1 - g, y0 + tile - 1 - g], fill=paint + (255,))
            dr.line([x0 + g, y0 + g, x0 + tile - 1 - g, y0 + g], fill=hi + (255,), width=g)
            dr.line([x0 + g, y0 + g, x0 + g, y0 + tile - 1 - g], fill=hi + (255,), width=g)
            dr.line([x0 + g, y0 + tile - 1 - g, x0 + tile - 1 - g, y0 + tile - 1 - g], fill=lo + (255,), width=g)
            m = tile // 4
            dr.rectangle([x0 + m, y0 + m, x0 + tile - 1 - m, y0 + tile - 1 - m], outline=base + (255,), width=g)
    return im


def _mix(c, k):
    return tuple(int(c[i] + (255 - c[i]) * k) for i in range(3))


def exhaust_mock(length_px, width_px, rgb):
    """Chama/tracante simples apontando para tras (-X). Devolve (imagem, x da base na imagem); a base fica na
    altura do meio da imagem."""
    S = 4
    L, W = max(4, length_px) * S, max(2, width_px) * S
    im = Image.new("RGBA", (int(L + W), int(2 * W + 4)), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cols = [rgb + (140,), _mix(rgb, 0.35) + (200,), _mix(rgb, 0.65) + (240,), _mix(rgb, 0.92) + (255,)]
    bx = L + W * 0.2
    for i, col in enumerate(cols):
        f = 1 - i * 0.2
        _flame(dr, bx, im.height / 2, L * f, W * 0.5 * f, -90, col)
    im = im.resize((max(1, im.width // S), max(1, im.height // S)), Image.LANCZOS)
    return Image.alpha_composite(im.filter(ImageFilter.GaussianBlur(1.5)), im), bx / S


def _proj_layers(d, it, frame=0, mask_rgb=None):
    """(corpo RGBA com a faixa tingida, luzes do quadro 'frame' ou None) na resolucao nativa do sprite."""
    body = load(d, it["file"])
    if it.get("mask") and mask_rgb:
        mk = np.asarray(load(d, it["mask"]), dtype=np.float32)
        b = np.asarray(body, dtype=np.float32)
        lum = b[..., :3].mean(axis=2, keepdims=True) / 255.0
        tint = np.clip(np.array(mask_rgb, np.float32) * (0.35 + lum * 1.3), 0, 255)
        a = mk[..., 3:4] / 255.0 * (b[..., 3:4] / 255.0)
        rgb = b[..., :3] * (1 - a) + tint * a
        body = Image.fromarray(np.dstack([rgb, b[..., 3]]).astype(np.uint8), "RGBA")
    lt = None
    if it.get("lights"):
        L_ = it["lights"]
        fw, fh = L_["frame_px"]
        per = max(1, L_.get("per_row") or L_["frames"])
        k = frame % L_["frames"]
        x0, y0 = (k % per) * fw, (k // per) * fh
        lt = load(d, L_["file"]).crop((x0, y0, x0 + fw, y0 + fh))
    return body, lt


def _proj_cell(d, key, it, length, s, paint, mock_rgb, mask_rgb, frame=0, label=None, font=None):
    """Um item desenhado no comprimento 'length' (tiles do jogo) a s x 64 px/tile sobre o casco."""
    L0, W0 = it["size"]
    k = length / L0
    pw, ph = max(2, int(round(L0 * k * PX * s))), max(2, int(round(W0 * k * PX * s)))
    exh = int(round(pw * (0.9 if mock_rgb else 0.0)))
    pad = 10 + 4 * s
    lab = 16 if label else 0
    cw, ch = pw + exh + 2 * pad, max(ph, int(ph * 1.6)) + 2 * pad + lab
    if label:
        tw = int(ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(label, font=font or _font()))
        cw = max(cw, tw + 2 * pad)
    cell = hull_tiles(cw, ch, paint, tile=PX * s)
    cx, cy = cw - pad - pw / 2, pad + (ch - 2 * pad - lab) / 2
    body, lt = _proj_layers(d, it, frame, mask_rgb)
    body = body.resize((pw, ph), Image.LANCZOS)
    if mock_rgb:
        # chama/tracante embaixo do corpo (Beam em BulletUpper2, corpo em BulletUpper3), base no bocal
        nx = cx + it["nozzle"][0] * k * PX * s
        ex, bx = exhaust_mock(exh, ph * 0.55, mock_rgb)
        add_center(cell, ex, nx - bx + ex.width / 2, cy, gain=1.0)
    paste_center(cell, body, cx, cy)
    if lt is not None:
        add_center(cell, lt.resize((pw, ph), Image.LANCZOS), cx, cy, gain=1.0)
    if label:
        ImageDraw.Draw(cell).text((pad, ch - lab - 2), label, fill=(225, 228, 235, 255), font=font or _font())
    return cell


def _grid(cells, max_w, bg=(7, 9, 14), gap=6, title=None, font=None):
    rows, row, w = [], [], 0
    for c in cells:
        if row and w + c.width > max_w:
            rows.append(row)
            row, w = [], 0
        row.append(c)
        w += c.width + gap
    if row:
        rows.append(row)
    th = 20 if title else 0
    W = max(sum(c.width for c in r) + gap * (len(r) - 1) for r in rows) + 2 * gap
    if title:
        tw = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(title, font=font or _font())
        W = max(W, int(tw) + 2 * gap)
    H = sum(max(c.height for c in r) for r in rows) + gap * (len(rows) + 1) + th
    out = Image.new("RGBA", (W, H), bg + (255,))
    if title:
        ImageDraw.Draw(out).text((gap, 4), title, fill=(235, 238, 245, 255), font=font or _font())
    y = gap + th
    for r in rows:
        x = gap
        for c in r:
            out.alpha_composite(c, (x, y))
            x += c.width + gap
        y += max(c.height for c in r) + gap
    return out


def _mock_for(key, kind, mock_colors):
    if key in mock_colors:
        return mock_colors[key]
    if "charge" in key:
        return None                     # carga grudada no casco: sem chama
    head = key.split("_")[0]
    return MOCK_COLORS.get(head, MOCK_COLORS["he"])


def make_projectiles(d, sheet_path=None, gif_path=None, paint=(46, 58, 74), keys=None, lengths=None,
                     mock_colors=None, mask_colors=None, max_w=1800, gif_scale=2):
    """Previas de uma folha de projeteis (meta kind "missiles"/"shells", CONTRATOS secao 3).

    sheet_path / gif_path: saidas (padrao <d>/preview_projectiles.png e <d>/preview_lights.gif; WP de arte grava
    as previas finais em docs/preview/3d/ passando o caminho). keys: itens e ordem (padrao: todos).
    lengths: {chave: [comprimentos no jogo em tiles]} (padrao: o "size" do item; as granadas reaproveitam a mesma
    textura em varios calibres). mock_colors: {chave: (r, g, b) | None} cor da chama/tracante (None = sem).
    mask_colors: {chave: (r, g, b)} tinta da faixa (mascara). Devolve (folha, gif ou None)."""
    meta = json.load(open(os.path.join(d, "meta.json")))
    kind = meta["kind"]
    items = meta["items"]
    keys = [k for k in (keys or list(items)) if k in items]
    lengths = lengths or {}
    mock_colors = mock_colors or {}
    mask_colors = mask_colors or {}
    font = _font()
    sheet_path = sheet_path or os.path.join(d, "preview_projectiles.png")
    gif_path = gif_path or os.path.join(d, "preview_lights.gif")

    def mask_for(k):
        return mask_colors.get(k, MASK_COLORS.get(k, MASK_COLORS["he"]))
    parts = []
    for s in (1, 3):
        cells = []
        for k in keys:
            it = items[k]
            for ln in lengths.get(k, [it["size"][0]]):
                lab = f"{k} {ln:g}t" if k in lengths else f"{k} {it['px'][0]}x{it['px'][1]}"
                cells.append(_proj_cell(d, k, it, ln, s, paint, _mock_for(k, kind, mock_colors), mask_for(k),
                                        label=lab, font=font))
        parts.append(_grid(cells, max_w, title=f"{meta.get('id', '')} ({kind}, {meta['px_per_tile']} px/tile) - "
                                               f"{s}x (64 px/tile no jogo = 1x)", font=font))
    W = max(p.width for p in parts)
    sheet = Image.new("RGBA", (W, sum(p.height for p in parts)), (7, 9, 14, 255))
    y = 0
    for p in parts:
        sheet.alpha_composite(p, (0, y))
        y += p.height
    os.makedirs(os.path.dirname(os.path.abspath(sheet_path)), exist_ok=True)
    sheet.convert("RGB").save(sheet_path)

    # GIF dos atlas de luzes (40 ms por quadro)
    lit = [k for k in keys if items[k].get("lights")]
    if not lit:
        return sheet_path, None
    T = 2.0
    for k in lit:
        L_ = items[k]["lights"]
        cyc = L_["frames"] / max(0.1, L_.get("fps") or 1)
        T = max(T, cyc + 0.6 if L_.get("wrap") == "Clamp" else cyc * math.ceil(2.0 / cyc))
    T = min(T, 6.0)
    nf = int(round(T / 0.04))
    frames = []
    for f in range(nf):
        t = f * 0.04
        cells = []
        for k in lit:
            it = items[k]
            L_ = it["lights"]
            idx = int(t * (L_.get("fps") or 1))
            idx = min(idx, L_["frames"] - 1) if L_.get("wrap") == "Clamp" else idx % L_["frames"]
            cells.append(_proj_cell(d, k, it, it["size"][0], gif_scale, paint, _mock_for(k, kind, mock_colors),
                                    mask_for(k), frame=idx, label=f"{k} {idx + 1}/{L_['frames']}", font=font))
        frames.append(_grid(cells, 1200, font=font))
    os.makedirs(os.path.dirname(os.path.abspath(gif_path)), exist_ok=True)
    _save_gif_shared(frames, [40] * len(frames), gif_path)
    return sheet_path, gif_path


# ============================================================================ pecas "layered" (render_layered.py)
GAME_LAYERS = ["structure", "floors", "turrets", "doodads_low", "walls_stencil", "external_walls", "walls", "doors",
               "weapons", "doodads_high", "lights_add", "fire", "roofs", "roof_doodads", "roof_turrets",
               "roof_lights_fancy"]
ROOF_LAYERS = ("roofs", "roof_doodads", "roof_turrets", "roof_lights_fancy")


def layered_part(meta, sub=None):
    """Meta de UMA peca layered (pasta shared: parts[sub]; sem sub, a primeira)."""
    if meta.get("shared"):
        parts = meta.get("parts") or {}
        return parts[sub] if sub else parts[sorted(parts)[0]]
    return meta


def _ent_rects(ent):
    return ent.get("rects") or [ent["rect"]]


def _add_light(img, spr, xy, gain=1.0):
    """Soma aditiva (lights_add: RGB sobre preto) onde img ja tem alfa."""
    x, y = xy
    Wi, Hi = img.size
    x0, y0, x1, y1 = max(0, x), max(0, y), min(Wi, x + spr.width), min(Hi, y + spr.height)
    if x1 <= x0 or y1 <= y0:
        return img
    b = np.asarray(img, dtype=np.float32).copy()
    sp = np.asarray(spr, dtype=np.float32)[y0 - y:y1 - y, x0 - x:x1 - x]
    add = sp[..., :3] * (sp[..., 3:4] / 255.0) * gain
    b[y0:y1, x0:x1, :3] = np.clip(b[y0:y1, x0:x1, :3] + add * (b[y0:y1, x0:x1, 3:4] / 255.0), 0, 255)
    return Image.fromarray(b.astype(np.uint8), "RGBA")


def _sprite_for(d, ent, idx, size_px):
    """Sprite idx da camada no tamanho do rect (as camadas com 'px' proprio, ex. digitos, sao reduzidas)."""
    spr = load(d, ent["files"][idx % len(ent["files"])])
    if spr.size != size_px:
        spr = spr.resize(size_px, Image.LANCZOS)
    return spr


def _optional_layers(m):
    """Camadas que so existem com um switch ligado (escondidas por padrao; so entram com pick explicito): os
    digitos do paiol (meta digits.switch = paiol_counter, DESLIGADO nos dois builds: ADDENDUM G1/G9)."""
    dg = m.get("digits") or {}
    if not dg.get("switch"):
        return set()
    fs = set(dg.get("files") or [])
    return {n for n, e in (m.get("layers") or {}).items() if n == "digitos" or (fs and set(e["files"]) <= fs)}


def _plate_sprite(d, m, pick):
    """(sprite, rect) da placa de tipo do meta (parts.<n>.plate: rect + files[familia] em art3d/<source>) ou None.
    Familia = a variante escolhida do teto (pick['roof']); tipo = pick['placa'] (indice na lista da familia,
    padrao 0 = o 1o tipo, como no logistica_paiois.png aprovado; None esconde)."""
    pl = m.get("plate")
    if not (isinstance(pl, dict) and pl.get("rect") and isinstance(pl.get("files"), dict)):
        return None
    k = (pick or {}).get("placa", 0)
    if k is None:
        return None
    roof = (m.get("layers") or {}).get("roof") or {}
    fams = roof.get("variants") or list(pl["files"])
    fam = fams[((pick or {}).get("roof", 0) or 0) % len(fams)]
    files = pl["files"].get(fam) or []
    if not files:
        return None
    src = os.path.join(os.path.dirname(os.path.abspath(d)), pl.get("source") or "bs_placas")
    if not os.path.exists(os.path.join(src, files[k % len(files)])):
        return None
    x, y, w, h = pl["rect"]
    spr = load(src, files[k % len(files)])
    size = (int(round(w * PX)), int(round(h * PX)))
    if spr.size != size:
        spr = spr.resize(size, Image.LANCZOS)
    return spr, (int(round(x * PX)), int(round(y * PX)))


# Grupos alternativos: camadas <base>_<sufixo> que no jogo sao toggles SEPARADOS (o FX da Fita: cartucho_sai +
# brilho_sai no Timer SaindoRecente, cartucho_entra + brilho_entra no EntrandoRecente; meta bs_fita_fx notes). A
# previa nunca desenha dois grupos na mesma imagem: um ladrilho (e uma linha do GIF) por grupo.
ALT_GROUPS = {"sai": "saindo (SaindoRecente)", "entra": "entrando (EntrandoRecente)"}
LIGHT_BASE = (24, 28, 36)          # fundo escuro do interior de uma peca so de FX (o piso da peca hospedeira)


def _alt_groups(m):
    """{sufixo: [camadas]} dos grupos alternativos da peca, na ordem de ALT_GROUPS; vazio quando ha menos de dois
    grupos (nada a separar)."""
    lay = m.get("layers") or {}
    g = {s: [n for n in lay if n.endswith("_" + s)] for s in ALT_GROUPS}
    g = {s: v for s, v in g.items() if v}
    return g if len(g) > 1 else {}


def _alt_hidden(m, group=None):
    """Camadas dos OUTROS grupos alternativos (group None = o 1o grupo: uma imagem mostra um grupo so)."""
    g = _alt_groups(m)
    if not g:
        return set()
    group = group if group in g else next(iter(g))
    return {n for s, v in g.items() if s != group for n in v}


def _light_base(m):
    """True para uma peca sem piso proprio e com camada lights_add (o FX da Fita): no jogo a luz soma no piso da peca
    hospedeira; na previa o interior leva o fundo LIGHT_BASE para o brilho aparecer (_add_light so soma onde ja ha
    alfa)."""
    lay = list((m.get("layers") or {}).values())
    return (not any(e["game_layer"] == "floors" for e in lay)) and any(e["game_layer"] == "lights_add" for e in lay)


def layered_composite(d, m, pick=None, roof=True, paint=(46, 58, 74), lights=True, walls=True, hide=(), group=None,
                      base=None):
    """Peca layered montada a 1x (64 px/quadro) na ordem das camadas do jogo, como o render_layered.composite mas
    so com PIL: pick = {camada: indice do sprite | None (esconde)} (padrao 0); roof=False = interior; as camadas
    lights_add sao SOMADAS na posicao do jogo (abaixo dos tetos, como no jogo) quando lights=True; os tetos levam
    a pintura `paint`. hide: camadas que nao entram (ex.: layer_flags exclusive_with).
    Como no jogo: as camadas de switch desligado (digitos do paiol, _optional_layers) so entram com pick explicito
    ({'digitos': i}); a placa de tipo do meta (plate.rect, art3d/bs_placas) entra no roof_doodads com o teto
    (pick['placa'] = indice do tipo da familia, None esconde); dos grupos alternativos (_alt_groups: *_sai /
    *_entra do FX da Fita) so entra `group` (None = o 1o). base = cor (r, g, b) de fundo opaco da peca antes das
    camadas (o piso da peca hospedeira de um FX: _light_base), para a luz aditiva aparecer."""
    W, H = m["size"]
    stack, adds = [], []
    opt = _optional_layers(m)
    hide = set(hide) | _alt_hidden(m, group)
    if walls and m.get("walls") and os.path.exists(os.path.join(d, m["walls"])):
        stack.append((GAME_LAYERS.index("walls"), -1, load(d, m["walls"]), (0, 0)))
    nl = len(m.get("layers") or {})
    if roof:
        ps = _plate_sprite(d, m, pick)
        if ps is not None:
            # depois do medidor e antes dos digitos (ordem do compose_logistica aprovado; nao se cruzam)
            stack.append((GAME_LAYERS.index("roof_doodads"), nl - 0.5, ps[0], ps[1]))
    for k, (name, ent) in enumerate((m.get("layers") or {}).items()):
        gl = ent["game_layer"]
        if name in hide or (not roof and gl in ROOF_LAYERS):
            continue
        idx = (pick or {}).get(name, None if name in opt else 0)
        if idx is None:
            continue
        x, y, w, h = ent["rect"]
        spr = _sprite_for(d, ent, idx, (int(round(w * PX)), int(round(h * PX))))
        if gl == "roofs" and paint is not None:
            spr = paint_roof(spr, paint)
        for r in _ent_rects(ent):
            xy = (int(round(r[0] * PX)), int(round(r[1] * PX)))
            if gl == "lights_add":
                if lights:
                    adds.append((spr, xy))
            else:
                stack.append((GAME_LAYERS.index(gl), k, spr, xy))
    img = Image.new("RGBA", (W * PX, H * PX), tuple(base[:3]) + (255,) if base else (0, 0, 0, 0))
    gl_add = GAME_LAYERS.index("lights_add")
    done = False
    for gl, _k, spr, xy in sorted(stack, key=lambda t: (t[0], t[1])):
        if gl > gl_add and not done:
            for a in adds:
                img = _add_light(img, *a)
            done = True
        img.alpha_composite(spr, xy)
    if not done:
        for a in adds:
            img = _add_light(img, *a)
    return img


def _exclusive_hidden(m):
    """Camadas escondidas por padrao: layer_flags rest_only (ex.: weapon da ponta do Tupa, que nunca vai junto com
    weapon_tranco)."""
    return {n for n, fl in (m.get("layer_flags") or {}).items() if fl.get("rest_only")}


def _strip_layers(m):
    """[(camada, n, passo s)] das camadas com mais de um sprite (quadros, niveis ou variantes): uma tira cada na
    folha. O passo e o intervalo do meta (quadros) ou so o passo do GIF da previa (0,18 s nos niveis, 0,12 s em
    quadros sem intervalo): niveis nao tem tempo no jogo (seguem o estoque/valor)."""
    out = []
    for name, ent in (m.get("layers") or {}).items():
        n = len(ent["files"])
        if n > 1:
            iv = ent.get("interval") or (0.12 if "frames" in ent else 0.18)
            out.append((name, n, float(iv)))
    return out


def _animated(m):
    """[(camada, n, passo s)] das camadas que MUDAM no jogo (quadros e niveis; o GIF passa por todos). As
    variantes (teto por familia, placas, digitos) sao escolhas fixas de cada peca/estado: so tiras, sem GIF; as
    camadas de switch desligado (digitos) tambem ficam fora."""
    opt = _optional_layers(m)
    return [(n, k, iv) for n, k, iv in _strip_layers(m)
            if n not in opt and "variants" not in m["layers"][n]]


def _segundos(v):
    """Intervalo em pt-BR (virgula decimal): 0.075 -> '0,075 s'."""
    return f"{float(v):g}".replace(".", ",") + " s"


def _strip_info(m, name, ent, opt, groups):
    """Texto entre parenteses do rotulo de uma tira: camada do jogo e o tempo SO dos quadros (AnimationInterval do
    meta); niveis seguem o estoque/valor (sem tempo no jogo); variantes sao escolha fixa."""
    gl = ent["game_layer"]
    if "frames" in ent:
        info = f"{gl}, {_segundos(ent['interval'])} por quadro" if ent.get("interval") else \
            f"{gl}, intervalo fora do meta"
    elif "levels" in ent:
        info = f"{gl}; o nível segue o estoque/valor, sem tempo no jogo"
    else:
        info = f"{gl}, escolha fixa, fora do GIF"
    for s, v in groups.items():
        if name in v:
            info += f"; grupo {ALT_GROUPS[s]}"
    if name in opt:
        info += f"; só com o switch {(m.get('digits') or {}).get('switch')}, desligado nos builds"
    return info


def _on_hull(img, paint=(46, 58, 74), pad=1):
    w, h = img.size
    bg = hull_tiles(w + 2 * pad * PX, h + 2 * pad * PX, paint)
    bg.alpha_composite(img, (pad * PX, pad * PX))
    return bg


def make_layered(d, sub=None, sheet_path=None, gif_path=None, paint=(46, 58, 74), scale=3, title=None):
    """Previas de uma peca layered (spec render_kinds.layered.preview): folha com a peca montada a 1x e a `scale`
    (interior e com teto pintado), uma tira por camada com mais de um sprite (todos os quadros/niveis/variantes,
    ampliados; so os quadros levam tempo no rotulo) e um GIF com as camadas de quadros/niveis (_animated) rodando
    juntas (intervalo do meta nos quadros; os niveis sobem e descem no passo da previa), interior e teto lado a lado
    sobre placas de casco. Grupos alternativos (_alt_groups: *_sai / *_entra do FX da Fita, toggles separados no
    jogo) saem em linhas separadas, um grupo por linha, na folha e no GIF. Peca so de FX (_light_base): o interior
    leva um fundo escuro (o piso da peca hospedeira) para a luz aditiva aparecer. Padrao: preview_layered[_sub].png /
    .gif na pasta. Devolve (folha, gif); gif None quando nada anima (ex.: placas)."""
    meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
    m = layered_part(meta, sub)
    tag = f"_{sub}" if sub else ""
    sheet_path = sheet_path or os.path.join(d, f"preview_layered{tag}.png")
    gif_path = gif_path or os.path.join(d, f"preview_layered{tag}.gif")
    font = _font_ui()
    hide = _exclusive_hidden(m)
    groups = _alt_groups(m)
    gnames = list(groups) or [None]
    base = LIGHT_BASE if _light_base(m) else None
    in_lab = "interior (sem teto)" + (", luz sobre fundo escuro" if base else "")
    rows = []                                        # [(titulo da linha | None, [celulas])]
    for g in gnames:
        inner = layered_composite(d, m, roof=False, paint=paint, hide=hide, group=g, base=base)
        full = layered_composite(d, m, roof=True, paint=paint, hide=hide, group=g)
        tiles = []
        for im, lab in ((inner, in_lab), (full, "com teto pintado")):
            big = _on_hull(im, paint).resize(((im.width + 2 * PX) * scale, (im.height + 2 * PX) * scale),
                                             Image.NEAREST)
            tiles.append((big, f"{lab} - {scale}x"))
            tiles.append((_on_hull(im, paint), f"{lab.split(',')[0]} - 1x"))
        cells = []
        for im, lab in tiles:
            cv = Image.new("RGBA", (max(im.width, int(font.getlength(lab)) + 8), im.height + 18), (7, 9, 14, 255))
            cv.alpha_composite(im, (0, 18))
            ImageDraw.Draw(cv).text((4, 3), lab, font=font, fill=(220, 226, 236, 255))
            cells.append(cv)
        rows.append((f"{ALT_GROUPS[g]}: {' + '.join(groups[g])} (toggle separado no jogo)" if g else None, cells))
    strips = []
    opt = _optional_layers(m)
    for name, n, iv in _strip_layers(m):
        ent = m["layers"][name]
        x, y, w, h = ent["rect"]
        k = max(1, min(4, int(256 // max(1, max(w, h) * PX))))
        fr = [_sprite_for(d, ent, i, (int(round(w * PX)), int(round(h * PX)))) for i in range(n)]
        if ent["game_layer"] == "roofs" and paint is not None:
            fr = [paint_roof(f, paint) for f in fr]          # teto como no jogo (sem a chave de pintura verde)
        cw, ch = fr[0].width * k, fr[0].height * k
        kind = "quadros" if "frames" in ent else "níveis" if "levels" in ent else "variantes"
        lab = f"{name}: {n} {kind} ({_strip_info(m, name, ent, opt, groups)})"
        st = Image.new("RGBA", (max(n * (cw + 4) + 4, int(font.getlength(lab)) + 12), ch + 22), (7, 9, 14, 255))
        for i, f in enumerate(fr):
            bg = Image.new("RGBA", f.size, (0, 0, 0, 255) if ent["game_layer"] == "lights_add" else (48, 52, 62, 255))
            bg.alpha_composite(f)
            st.alpha_composite(bg.resize((cw, ch), Image.NEAREST), (4 + i * (cw + 4), 20))
        ImageDraw.Draw(st).text((4, 4), lab, font=font, fill=(255, 196, 70, 255))
        strips.append(st)
    head = title or f"{m.get('id', meta.get('id', ''))} ({m['size'][0]}x{m['size'][1]}, layered)"
    row_h = [(20 if rt else 0) + max(c.height for c in cs) + 8 for rt, cs in rows]
    Wd = max([sum(c.width + 8 for c in cs) + 8 for _rt, cs in rows] + [s.width + 16 for s in strips] +
             [int(font.getlength(rt)) + 16 for rt, _cs in rows if rt])
    Hd = 26 + sum(row_h) + sum(s.height + 8 for s in strips) + 8
    sheet = Image.new("RGBA", (Wd, Hd), (7, 9, 14, 255))
    dr = ImageDraw.Draw(sheet)
    dr.text((8, 6), head, font=font, fill=(255, 196, 70, 255))
    y = 26
    for (rt, cs), rh in zip(rows, row_h):
        if rt:
            dr.text((8, y + 2), rt, font=font, fill=(120, 220, 235, 255))
        x = 8
        for c in cs:
            sheet.alpha_composite(c, (x, y + (20 if rt else 0)))
            x += c.width + 8
        y += rh
    for s_ in strips:
        sheet.alpha_composite(s_, (8, y))
        y += s_.height + 8
    os.makedirs(os.path.dirname(os.path.abspath(sheet_path)), exist_ok=True)
    sheet.convert("RGB").save(sheet_path)
    anim = _animated(m)
    if not anim:
        return sheet_path, None
    step = 0.04
    T = min(6.0, max(2.0, max(n * iv * (2 if "levels" in m["layers"][nm] else 1) for nm, n, iv in anim)))
    frames = []
    for f in range(int(round(T / step))):
        t = f * step
        pick = {}
        for nm, n, iv in anim:
            i = int(t / iv)
            if "levels" in m["layers"][nm]:
                i = i % (2 * n - 2) if n > 1 else 0          # niveis sobem e descem
                i = i if i < n else 2 * n - 2 - i
            else:
                i = i % n
            pick[nm] = i
        lines = []
        for g in gnames:                                     # uma linha por grupo alternativo
            a = _on_hull(layered_composite(d, m, pick=pick, roof=False, paint=paint, hide=hide, group=g, base=base),
                         paint)
            b = _on_hull(layered_composite(d, m, pick=pick, roof=True, paint=paint, hide=hide, group=g), paint)
            fr = Image.new("RGBA", (a.width + b.width + 8, a.height), (7, 9, 14, 255))
            fr.alpha_composite(a, (0, 0))
            fr.alpha_composite(b, (a.width + 8, 0))
            lines.append((g, fr))
        k = max(1, min(4, int(900 // lines[0][1].width)))    # pecas pequenas (FX 1x1) saem ampliadas
        if not groups:
            fr = lines[0][1]
            frames.append(fr.resize((fr.width * k, fr.height * k), Image.NEAREST))
            continue
        lw, lh = lines[0][1].width * k, lines[0][1].height * k
        out = Image.new("RGBA", (lw, len(lines) * (lh + 20)), (7, 9, 14, 255))
        dro = ImageDraw.Draw(out)
        for j, (g, fr) in enumerate(lines):
            y0 = j * (lh + 20)
            dro.text((4, y0 + 3), f"{ALT_GROUPS[g]}: interior | com teto", font=font, fill=(120, 220, 235, 255))
            out.alpha_composite(fr.resize((lw, lh), Image.NEAREST), (0, y0 + 20))
        frames.append(out)
    os.makedirs(os.path.dirname(os.path.abspath(gif_path)), exist_ok=True)
    _save_gif_shared(frames, [int(step * 1000)] * len(frames), gif_path)
    return sheet_path, gif_path


def main():
    d = sys.argv[1]
    paint = (46, 58, 74)
    if "--paint" in sys.argv:
        paint = tuple(int(v) for v in sys.argv[sys.argv.index("--paint") + 1].split(","))
    meta = json.load(open(os.path.join(d, "meta.json")))
    opt = {a: sys.argv[sys.argv.index(f"--{a}") + 1] for a in ("sheet", "gif", "sub") if f"--{a}" in sys.argv}
    if meta.get("kind") in PROJ_KINDS:
        print("OK", make_projectiles(d, sheet_path=opt.get("sheet"), gif_path=opt.get("gif"), paint=paint))
        return
    if meta.get("kind") == "layered":
        print("OK", make_layered(d, sub=opt.get("sub"), sheet_path=opt.get("sheet"), gif_path=opt.get("gif"),
                                 paint=paint))
        return
    print("OK", make_all(d, paint), "quadros")


if __name__ == "__main__":
    main()
