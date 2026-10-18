"""Gera os PNGs de cada peca/recurso do Bullet Strike usando a biblioteca bsgen.sprites."""

import math
import zlib
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from bsgen import sprites as S
from bsgen.art import PX, Canvas, flat_normals
import art3d as A3

HERE = os.path.dirname(os.path.abspath(__file__))


def _accent(g):
    return S.ACCENTS[g["art"].get("accent", "ammo")]


def gun_art3d(out, pdir, g, info):
    """Arma com arte 3D: copia os PNGs renderizados e monta icone/blueprint com eles."""
    geo = info["geo"]
    w, h = g["size"]
    meta = g["art3d"]
    A3.copy_files(out.root, pdir, g["short"], meta)
    load = lambda n: Image.open(A3.path(g["short"], n)).convert("RGBA")  # noqa: E731
    roof = load(meta["hull"]["roof"])
    turret = load(meta["turret"]["frames"][0])
    rest = load(meta["barrel"]["rest"])
    icon = S.compose_weapon(w, h, roof, turret, [rest], geo, geo["overhang"])
    out.image(f"{pdir}/icon.png", icon)
    sil = S.compose_weapon(w, h, Image.new("RGBA", roof.size, (0, 0, 0, 0)), turret, [rest], geo, 0)
    sil = sil.crop((0, 0, w * PX, h * PX))
    out.image(f"{pdir}/blueprints.png", S.blueprint_from(w, h, sil))
    out.image(f"../docs/preview/{g['short']}.png", icon)


def gun_art(out, pdir, g, info):
    if g.get("art3d"):
        return gun_art3d(out, pdir, g, info)
    geo = info["geo"]
    w, h = g["size"]
    a = _accent(g)
    style = g["art"]["style"]
    bw = geo.get("barrel_sprite_w", max(0.5, geo["barrel_w"] * 2))
    on, off, nrm, shadow = S.render_turret(style, geo["turret_size"], geo["front"], geo["ys"], geo["barrel_w"], a,
                                           seed=zlib.crc32(g["short"].encode()) % 1000)
    out.image(f"{pdir}/turret.png", on)
    out.image(f"{pdir}/turret_off.png", off)
    out.image(f"{pdir}/turret_normals.png", nrm)
    out.image(f"{pdir}/turret_shadow.png", shadow)
    kind = g["art"].get("barrel", "plain")
    spin = bool(g.get("spin"))
    recoil_px = g["art"].get("recoil_px", max(4, int(geo["barrel_len"] * PX * 0.18)))
    frames, normals = S.render_barrel_frames(kind, bw, geo["barrel_len"], a, recoil_px, spin=spin)
    if spin:
        names = ["barrel_spin1.png", "barrel_spin2.png", "barrel_spin3.png", "barrel1.png"]
    else:
        names = ["barrel1.png", "barrel2.png", "barrel3.png", "barrel4.png", "barrel5.png"]
    for name, fr in zip(names, frames):
        out.image(f"{pdir}/{name}", fr)
    out.image(f"{pdir}/barrel_normals1.png", normals[-1] if spin else normals[0])
    crew = g.get("crew_pos")
    if not crew:
        from bsgen.common import crew_positions
        crew = crew_positions(w, h, g["crew"], geo["pivot"])
    floor, walls, roof, roof_n = S.render_hull(w, h, a, geo["pivot"], geo["turret_size"] * 0.46, crew,
                                               seed=zlib.crc32(g["short"].encode()) % 997)
    out.image(f"{pdir}/floor.png", floor)
    out.image(f"{pdir}/walls.png", walls)
    out.image(f"{pdir}/roof.png", roof)
    out.image(f"{pdir}/roof_normals.png", roof_n)
    rest = frames[-1] if spin else frames[0]
    icon = S.compose_weapon(w, h, roof, on, [rest], geo, geo["overhang"])
    out.image(f"{pdir}/icon.png", icon)
    # blueprint: casco azul + silhueta vermelha da torre/canos dentro da peca
    sil = S.compose_weapon(w, h, Image.new("RGBA", roof.size, (0, 0, 0, 0)), on, [rest], geo, 0)
    sil = sil.crop((0, 0, w * PX, h * PX))
    out.image(f"{pdir}/blueprints.png", S.blueprint_from(w, h, sil))
    # preview grande para o README
    out.image(f"../docs/preview/{g['short']}.png", icon)


def wall_damage_levels(walls, seed, fractions=(0.05, 0.10)):
    """Paredes danificadas (walls_33 / walls_66) feitas a partir de walls.png, no jeito das vanilla
    (factory_he/walls_33.png e walls_66.png): rachaduras escuras com a borda clara e lascas, so nos pixels
    opacos do contorno, alfa intocado e o contorno um pouco mais escuro. Cada nivel contem o dano do anterior;
    fractions = fracao do contorno alterada em cada nivel (vanilla: ~5% e ~10%)."""
    import random
    import numpy as np
    a = np.asarray(walls.convert("RGBA")).astype(np.float32)
    H, W = a.shape[:2]
    rim = a[..., 3] >= 250
    ys, xs = np.nonzero(rim)
    total = len(ys)
    rng = random.Random(seed)
    hit = np.zeros((H, W), bool)
    out = []
    for frac, dim in zip(fractions, (0.99, 0.98)):
        target = int(total * frac)
        while hit.sum() < target and total:
            j = rng.randrange(total)
            y, x = int(ys[j]), int(xs[j])
            # rachadura corre ao longo do contorno: vertical nas laterais, horizontal em cima/embaixo
            vert = min(x, W - 1 - x) < min(y, H - 1 - y)
            dy, dx = (rng.choice((-1, 1)), 0) if vert else (0, rng.choice((-1, 1)))
            for _ in range(rng.randint(4, 14)):
                if not (0 <= y < H and 0 <= x < W) or not rim[y, x]:
                    break
                if not hit[y, x]:
                    a[y, x, :3] *= 0.45
                    hit[y, x] = True
                    # borda clara do lado de baixo/direita (luz vinda de cima/esquerda)
                    hy, hx = (y, x + 1) if vert else (y + 1, x)
                    if 0 <= hy < H and 0 <= hx < W and rim[hy, hx] and not hit[hy, hx]:
                        a[hy, hx, :3] = np.minimum(255, a[hy, hx, :3] * 1.25 + 12)
                        hit[hy, hx] = True
                y, x = y + dy, x + dx
                if rng.random() < 0.35:  # zigue-zague
                    if vert:
                        x += rng.choice((-1, 1))
                    else:
                        y += rng.choice((-1, 1))
            # lasca solta perto da rachadura
            if rng.random() < 0.5:
                j = rng.randrange(total)
                cy, cx = int(ys[j]), int(xs[j])
                if not hit[cy, cx]:
                    a[cy, cx, :3] = np.clip(a[cy, cx, :3] + rng.choice((-28, 24)), 0, 255)
                    hit[cy, cx] = True
        lvl = a.copy()
        lvl[rim, :3] *= dim
        out.append(Image.fromarray(np.clip(lvl, 0, 255).round().astype(np.uint8), "RGBA"))
    return out


def _wall_damage_files(out, pdir, walls, short):
    for name, img in zip(("walls_33.png", "walls_66.png"), wall_damage_levels(walls, zlib.crc32(short.encode()))):
        out.image(f"{pdir}/{name}", img)


def factory_art(out, pdir, f, info):
    w, h = info["size"]
    if f.get("art3d"):
        meta = f["art3d"]
        A3.copy_files(out.root, pdir, f["short"], meta)
        load = lambda n: Image.open(A3.path(f["short"], n)).convert("RGBA")  # noqa: E731
        icon = Image.new("RGBA", (w * PX, h * PX), (0, 0, 0, 0))
        icon.alpha_composite(load("floor.png"))
        icon.alpha_composite(load(meta["machine"]["frames"][0]))
        icon.alpha_composite(load("walls.png"))
        out.image(f"{pdir}/icon.png", icon)
        out.image(f"{pdir}/blueprints.png", S.blueprint_from(w, h))
        # niveis de dano das paredes (bsgen/factory.py WALL_DAMAGE)
        _wall_damage_files(out, pdir, load("walls.png"), f["short"])
        return
    a = S.ACCENTS[f["art"].get("accent", "ammo")]
    floor, walls, roof, roof_n, frames, off = S.render_factory(w, h, a, f["art"].get("kind", "mag"),
                                                                  seed=zlib.crc32(f["short"].encode()) % 991)
    out.image(f"{pdir}/floor.png", floor)
    out.image(f"{pdir}/walls.png", walls)
    _wall_damage_files(out, pdir, walls, f["short"])
    out.image(f"{pdir}/roof.png", roof)
    out.image(f"{pdir}/roof_normals.png", roof_n)
    for i, fr in enumerate(frames, start=1):
        out.image(f"{pdir}/machine_on{i}.png", fr)
    out.image(f"{pdir}/machine_off.png", off)
    icon = Image.new("RGBA", (w * PX, h * PX), (0, 0, 0, 0))
    icon.alpha_composite(floor)
    icon.alpha_composite(frames[0], (0, 0))
    icon.alpha_composite(walls)
    out.image(f"{pdir}/icon.png", icon)
    out.image(f"{pdir}/blueprints.png", S.blueprint_from(w, h, frames[0]))
    out.image(f"../docs/preview/{f['short']}.png", icon)


def _inside(bb, box):
    return bb[0] >= box[0] and bb[1] >= box[1] and bb[2] <= box[2] and bb[3] <= box[3]


def launcher_art(out, pdir, lch, info):
    """Lancador de misseis: casulo (roof_doodads) + niveis do rack (roof_turrets) + casco + icone/blueprint.

    Com arte 3D (art3d/<id>/meta.json, kind 'launcher', STYLE.md secao 8) so copia os PNGs renderizados."""
    geo = info["geo"]
    w, h = lch["size"]
    T = int(round(geo["turret_size"] * PX))

    def uncrop(img, rect):
        """Sobreposicao recortada (retangulo do casulo, STYLE.md 8.1) de volta no quadro inteiro da torre."""
        cv = Image.new("RGBA", (T, T), (0, 0, 0, 0))
        cv.alpha_composite(img, (rect[0], rect[1]))
        return cv

    if lch.get("art3d"):
        A3.copy_files(out.root, pdir, lch["short"], lch["art3d"])
        load = lambda n: Image.open(A3.path(lch["short"], n)).convert("RGBA")  # noqa: E731
        meta = lch["art3d"]
        roof, pod = load(meta["hull"]["roof"]), load(meta["turret"]["frames"][0])
        full = None
        for ov in geo["modes"][lch["modes"][0]["type"]]["overlays"]:
            im = uncrop(load(ov["files"][-1]), ov["rect"])
            full = im if full is None else Image.alpha_composite(full, im)
    else:
        a = S.ACCENTS["ammo"]
        ts = geo["turret_size"]
        pitch = lch["geo"].get("pitch_deg", 35)
        m0 = lch["modes"][0]
        units0 = geo["modes"][m0["type"]]["units"]
        tube_r = m0["geo"]["tube_r"]
        style = lch["art"]["style"].split("_", 1)[1]          # box / twin / quad
        on, off, nrm, shadow = S.render_launcher_pod(ts, units0, tube_r, pitch, a, style)
        out.image(f"{pdir}/turret.png", on)
        out.image(f"{pdir}/turret_off.png", off)
        out.image(f"{pdir}/turret_normals.png", nrm)
        out.image(f"{pdir}/turret_shadow.png", shadow)
        if geo.get("oc_glow"):
            out.image(f"{pdir}/{geo['oc_glow']}", S.render_launcher_oc_glow(ts, units0, tube_r, pitch, a, style))
        full = None
        for m in lch["modes"]:
            gm = geo["modes"][m["type"]]
            band = tuple(m["glow"])
            if gm.get("shutters"):
                img, nimg = S.render_launcher_shutters(ts, m["geo"]["shutters"])
                out.image(f"{pdir}/{gm['shutters']['file']}", img)
                out.image(f"{pdir}/{gm['shutters']['normals']}", nimg)
            for ov in gm["overlays"]:
                lo, hi = ov["range"]
                pod_units = gm["units"][lo:hi]
                box = tuple(ov["rect"])                         # recorte do casulo (launcher_layout.overlay_rect)
                for j, (fname, nname) in enumerate(zip(ov["files"], ov["normals"])):
                    img, nimg = S.render_launcher_cells(ts, units0, pod_units[:j], tube_r, pitch, band)
                    if img.getbbox() and not _inside(img.getbbox(), box):
                        raise ValueError(f"{lch['short']}/{fname}: nariz fora do retangulo do casulo {box} "
                                         f"(bbox {img.getbbox()})")
                    out.image(f"{pdir}/{fname}", img.crop(box))
                    out.image(f"{pdir}/{nname}", nimg.crop(box))
                    if m is m0 and j == len(ov["files"]) - 1:
                        full = img if full is None else Image.alpha_composite(full, img)
        crew = lch.get("crew_pos")
        if not crew:
            from bsgen.common import crew_positions
            crew = crew_positions(w, h, lch["crew"], geo["pivot"])
        floor, walls, roof, roof_n = S.render_hull(w, h, a, geo["pivot"], lch["geo"]["ring_r"], crew,
                                                   seed=zlib.crc32(lch["short"].encode()) % 997)
        out.image(f"{pdir}/floor.png", floor)
        out.image(f"{pdir}/walls.png", walls)
        out.image(f"{pdir}/roof.png", roof)
        out.image(f"{pdir}/roof_normals.png", roof_n)
        pod = on
    icon = S.compose_launcher(w, h, roof, pod, full, geo["pivot"])
    out.image(f"{pdir}/icon.png", icon)
    sil = S.compose_launcher(w, h, Image.new("RGBA", roof.size, (0, 0, 0, 0)), pod, full, geo["pivot"])
    out.image(f"{pdir}/blueprints.png", S.blueprint_from(w, h, sil))
    out.image(f"../docs/preview/{lch['short']}.png", icon)


def resource_art(out, r):
    d = f"resources/{r['dir']}"
    if r.get("art3d"):
        A3.copy_files(out.root, d, r["dir"], r["art3d"])
        out.image(f"../docs/preview/res_{r['dir']}.png", Image.open(A3.path(r["dir"], "icon.png")).convert("RGBA"))
        return
    icon, overlay, nugget, nugget_n, stacks = S.render_resource(r["art"]["kind"], S.ACCENTS[r["art"]["accent"]],
                                                               r["max_stack"])
    out.image(f"{d}/icon.png", icon)
    out.image(f"{d}/overlay.png", overlay)
    out.image(f"{d}/nugget.png", nugget)
    out.image(f"{d}/nugget_normals.png", nugget_n)
    for i, st in enumerate(stacks, start=1):
        out.image(f"{d}/stack_{i}.png", st)
    out.image(f"../docs/preview/res_{r['dir']}.png", icon)


def _font(size):
    for p in ["/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


LOGO_HERO = os.path.join(HERE, "blender", "logo_hero.png")   # render 3D (tools/blender/render_logo.py)
LOGO_TITLE = "BULLET STRIKE"
LOGO_SUB = "ARMAS DE CONVÉS · MUNIÇÃO · OVERCLOCK"


def logo():
    """Logo da Workshop / lista de mods (512 x 512 RGB): imagem heroi 3D + titulo e subtitulo.
    Sem a imagem 3D, cai no desenho procedural antigo."""
    if os.path.exists(LOGO_HERO):
        try:
            return _logo_hero(LOGO_HERO)
        except Exception as e:  # imagem corrompida: nao derruba o build
            print(f"AVISO: logo 3D falhou ({e}); usando o logo procedural")
    return _logo_procedural()


def _gradient(h, stops):
    """Coluna de cores (h x 3) interpolando stops [(t, (r, g, b))]."""
    import numpy as np
    ts = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32)
    t = np.linspace(0, 1, h, dtype=np.float32)
    return np.stack([np.interp(t, ts, cs[:, k]) for k in range(3)], axis=-1)


def _metal_title(W, text, size, slant=0.12, ss=3):
    """Titulo em ambar metalico: degrade com 'horizonte' escuro no meio, brilho no topo das letras,
    contorno escuro, sombra e brilho ambar por tras. Desenhado em ss x e reduzido (bordas limpas).
    Devolve (camada RGBA de largura W, altura das letras, margem acima das letras na camada). A margem cobre a
    cauda do desfoque do brilho (3 sigmas): a camada chega a alfa 0 nas bordas e nao deixa emenda no fundo."""
    import numpy as np
    f = _font(size * ss)
    sw = 3 * ss                                # contorno
    glow_r = 9 * ss                            # sigma do brilho difuso
    pad = 3 * glow_r + 3 * ss                  # cabe a cauda inteira do desfoque (sem corte reto em cima/baixo)
    x0, y0, x1, y1 = f.getbbox(text)
    tw, th = x1 - x0, y1 - y0
    Wb, Hb = W * ss, th + 2 * pad
    ox, oy = (Wb - tw) / 2 - x0, pad - y0

    def mask(stroke=0, dy=0):
        m = Image.new("L", (Wb, Hb), 0)
        ImageDraw.Draw(m).text((ox, oy + dy), text, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
        return m

    fill, outline = mask(), mask(sw)
    # degrade metalico (de cima para baixo dentro da altura das letras)
    col = _gradient(th, [(0.0, (255, 242, 196)), (0.30, (255, 205, 92)), (0.49, (246, 158, 34)),
                         (0.51, (176, 82, 10)), (0.70, (236, 132, 24)), (1.0, (255, 196, 96))])
    grad = np.zeros((Hb, Wb, 3), np.float32)
    grad[:] = col[0]
    grad[pad:pad + th] = col[:, None, :]
    grad[pad + th:] = col[-1]
    # brilho no topo de cada traco (mascara menos ela mesma deslocada para baixo)
    a = np.asarray(fill, np.float32) / 255
    below = np.asarray(mask(dy=2 * ss), np.float32) / 255
    hi = np.clip(a - below, 0, 1)[..., None]
    grad = grad * (1 - hi * 0.7) + np.array([255, 250, 228], np.float32) * hi * 0.7
    letters = Image.fromarray(np.dstack([np.clip(grad, 0, 255), a * 255]).astype(np.uint8), "RGBA")
    layer = Image.new("RGBA", (Wb, Hb), (0, 0, 0, 0))
    # brilho ambar difuso atras, sombra deslocada, contorno escuro e as letras
    glow = outline.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: int(v * 0.55))
    layer.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (Wb, Hb), (255, 120, 16)).split(), glow)))
    shadow = Image.new("L", (Wb, Hb), 0)
    shadow.paste(outline.filter(ImageFilter.GaussianBlur(2 * ss)), (0, 3 * ss))
    layer.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (Wb, Hb), (0, 0, 0)).split(),
                                                shadow.point(lambda v: int(v * 0.85)))))
    layer.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (Wb, Hb), (22, 13, 6)).split(), outline)))
    layer.alpha_composite(letters)
    if slant:
        # italico "de ataque": o topo das letras avanca para a direita
        cy = Hb / 2
        layer = layer.transform((Wb, Hb), Image.AFFINE, (1, slant, -slant * cy, 0, 1, 0), Image.BICUBIC)
    return layer.resize((W, Hb // ss), Image.LANCZOS), th // ss, pad // ss


def _logo_hero(path):
    import numpy as np
    W = 512
    bg = Image.open(path).convert("RGB")
    w, h = bg.size
    if w != h:
        # imagem nao quadrada: recorte central (nao deforma a cena)
        print(f"AVISO: {path} nao e quadrada ({w}x{h}); usando o recorte central")
        c = min(w, h)
        bg = bg.crop(((w - c) // 2, (h - c) // 2, (w - c) // 2 + c, (h - c) // 2 + c))
    if min(w, h) < W:
        print(f"AVISO: {path} tem {min(w, h)} px (menos que {W}): o logo vai sair borrado; "
              "renderize de novo com tools/blender/render_logo.py (sem --quick)")
    if bg.size != (W, W):
        bg = bg.resize((W, W), Image.LANCZOS)
    img = bg.convert("RGBA")
    # faixa de baixo escurecida (o titulo fica legivel sobre o conves)
    t = np.clip((np.arange(W, dtype=np.float32) - 318) / 150, 0, 1)
    ramp = (t * t * (3 - 2 * t) * 228).astype(np.uint8)
    shade = Image.fromarray(np.repeat(ramp[:, None], W, axis=1), "L")
    img.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (W, W), (2, 3, 6)).split(), shade)))
    # titulo: o maior que cabe em ~90 % da largura
    size = 72
    while size > 40 and _font(size).getbbox(LOGO_TITLE)[2] > W * 0.90:
        size -= 1
    title, th, pad = _metal_title(W, LOGO_TITLE, size)
    ty = 372
    img.alpha_composite(title, (0, ty - pad))
    # subtitulo em duas linhas centradas (legivel na miniatura de 128 px da lista de mods): claro com contorno
    # escuro e separador ambar; o maior tamanho em que a linha mais larga cabe em ~84 % da largura
    parts = LOGO_SUB.split(" · ")
    lines = [parts[:1], parts[1:]] if len(parts) > 2 else [parts]
    sep = "  ·  "
    sw = 3
    for sz in range(30, 15, -1):
        f2 = _font(sz)
        widths = [sum(f2.getlength(p) for p in ln) + f2.getlength(sep) * (len(ln) - 1) for ln in lines]
        if max(widths) <= W * 0.84:
            break
    hb = f2.getbbox("H")
    lh = (hb[3] - hb[1]) + 12                 # altura de maiuscula + entrelinha
    y = ty + th + 22 - hb[1]
    txt = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    for ln, lw in zip(lines, widths):
        x = (W - lw) / 2
        for i, p in enumerate(ln):
            d.text((x, y), p, font=f2, fill=(228, 233, 242, 255), stroke_width=sw, stroke_fill=(4, 5, 8, 255))
            x += f2.getlength(p)
            if i < len(ln) - 1:
                d.text((x, y), sep, font=f2, fill=(255, 170, 40, 255), stroke_width=sw, stroke_fill=(4, 5, 8, 255))
                x += f2.getlength(sep)
        y += lh
    img.alpha_composite(txt)
    return img.convert("RGB")


def _logo_procedural():
    """Logo antigo em 2D procedural (reserva quando tools/blender/logo_hero.png nao existe)."""
    W = 512
    img = Image.new("RGBA", (W, W), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    for y in range(W):
        t = y / W
        d.line([(0, y), (W, y)], fill=(int(8 + 14 * t), int(10 + 12 * t), int(26 + 20 * (1 - t)), 255))
    import random
    rnd = random.Random(7)
    for _ in range(260):
        x, y = rnd.randrange(W), rnd.randrange(W)
        b = rnd.randrange(90, 255)
        d.point((x, y), fill=(b, b, min(255, b + 20), 255))
    # tracantes
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(9):
        x0 = 256 + rnd.randrange(-30, 30)
        y0 = 300
        ang = math.radians(-90 + rnd.uniform(-14, 14))
        L = rnd.randrange(220, 330)
        gd.line([(x0, y0), (x0 + math.cos(ang) * L, y0 + math.sin(ang) * L)], fill=(255, 190, 80, 200), width=3)
    glow = glow.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, glow)
    # torre pesada no centro
    on, _off, _n, _sh = S.render_turret("heavy_naval", 4.2, 4.2 * 0.36, [-0.62, 0, 0.62], 0.36, S.ACCENTS["aphe"], 3)
    frames, _nn = S.render_barrel_frames("heavy", 0.7, 2.6, S.ACCENTS["aphe"], 10)
    tur = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    T = on.size[0]
    cx, cy = W // 2, 330
    for y in (-0.62, 0, 0.62):
        tur.alpha_composite(frames[0], (int(cx + y * 64 - frames[0].size[0] / 2),
                                        int(cy - 4.2 * 0.36 * 64 - frames[0].size[1])))
    tur.alpha_composite(on, (cx - T // 2, cy - T // 2))
    # clarao das bocas
    fl = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl)
    for y in (-0.62, 0, 0.62):
        mx, my = cx + y * 64, cy - 4.2 * 0.36 * 64 - frames[0].size[1] + 4
        fd.ellipse([mx - 26, my - 46, mx + 26, my + 10], fill=(255, 170, 60, 210))
        fd.ellipse([mx - 12, my - 26, mx + 12, my + 4], fill=(255, 245, 210, 255))
    fl = fl.filter(ImageFilter.GaussianBlur(9))
    img = Image.alpha_composite(img, fl)
    img = Image.alpha_composite(img, tur)
    # titulo
    txt = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)
    f1 = _font(64)
    f2 = _font(20)
    title = "BULLET STRIKE"
    tw = td.textlength(title, font=f1)
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            td.text(((W - tw) / 2 + dx, 404 + dy), title, font=f1, fill=(0, 0, 0, 255))
    td.text(((W - tw) / 2, 404), title, font=f1, fill=(255, 196, 70, 255))
    sub = "ARMAS DE CONVÉS · MUNIÇÃO · OVERCLOCK"
    sw = td.textlength(sub, font=f2)
    td.text(((W - sw) / 2 + 1, 478 + 1), sub, font=f2, fill=(0, 0, 0, 255))
    td.text(((W - sw) / 2, 478), sub, font=f2, fill=(220, 226, 236, 255))
    img = Image.alpha_composite(img, txt)
    return img.convert("RGB")


def misc_art(out):
    # icones da interface no padrao do jogo (silhueta azul com brilho, 96 px; ver bsgen/ui_icons.py)
    from bsgen import ui_icons as U
    out.image("gui/group_bullet_strike.png", U.icon_group())
    for kind in ("std", "ap", "aphe", "emp"):
        out.image(f"gui/ammo_{kind}.png", U.icon_ammo(kind))
    # seletor de missil (bs_missile_type): um icone por escolha
    import bs_data as D
    if D.LAUNCHERS:
        for _idx, _cid, _key, icon, mt in D.MISSILE_CHOICES:
            out.image(f"gui/{icon}", U.icon_missile(mt))
    out.image("logo.png", logo())
