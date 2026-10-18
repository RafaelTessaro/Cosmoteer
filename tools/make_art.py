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
        return
    a = S.ACCENTS[f["art"].get("accent", "ammo")]
    floor, walls, roof, roof_n, frames, off = S.render_factory(w, h, a, f["art"].get("kind", "mag"),
                                                                  seed=zlib.crc32(f["short"].encode()) % 991)
    out.image(f"{pdir}/floor.png", floor)
    out.image(f"{pdir}/walls.png", walls)
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


def launcher_art(out, pdir, lch, info):
    """Lancador de misseis: casulo (roof_doodads) + niveis do rack (roof_turrets) + casco + icone/blueprint.

    Com arte 3D (art3d/<id>/meta.json, kind 'launcher', STYLE.md secao 8) so copia os PNGs renderizados."""
    geo = info["geo"]
    w, h = lch["size"]
    if lch.get("art3d"):
        A3.copy_files(out.root, pdir, lch["short"], lch["art3d"])
        load = lambda n: Image.open(A3.path(lch["short"], n)).convert("RGBA")  # noqa: E731
        meta = lch["art3d"]
        roof, pod = load(meta["hull"]["roof"]), load(meta["turret"]["frames"][0])
        full = load(geo["modes"][lch["modes"][0]["type"]]["overlays"][0]["files"][-1])
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
                for j, (fname, nname) in enumerate(zip(ov["files"], ov["normals"])):
                    img, nimg = S.render_launcher_cells(ts, units0, pod_units[:j], tube_r, pitch, band)
                    out.image(f"{pdir}/{fname}", img)
                    out.image(f"{pdir}/{nname}", nimg)
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


def logo():
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
    out.image("gui/group_bullet_strike.png", S.render_group_icon())
    for kind in ("std", "ap", "aphe", "emp"):
        acc = {"std": "ammo", "ap": "ap", "aphe": "aphe", "emp": "emp"}[kind]
        out.image(f"gui/ammo_{kind}.png", S.render_toggle_icon(kind, S.ACCENTS[acc]))
    # seletor de missil (bs_missile_type): um icone por escolha, cor do brilho do tipo (spec missile_types[].glow)
    import bs_data as D
    if D.LAUNCHERS:
        for _idx, _cid, _key, icon, mt in D.MISSILE_CHOICES:
            out.image(f"gui/{icon}", S.render_missile_icon(mt, tuple(D._hex_rgb(D.MISSILE_TYPES[mt]["glow"]))))
    out.image("logo.png", logo())
