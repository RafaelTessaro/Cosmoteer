"""Previas da arte das armas 2.0 (PEM + Boiuna AC) para a aprovacao do usuario.

    python3 make_armas.py [pem|disparo|boiuna|galeria|todas]

Grava em docs/preview/3d/v2/:
  armas_pem.png          as 3 armas PEM como no jogo (teto pintado, torre em alguns angulos, 1x e 2x) + as granadas
  armas_pem_disparo.gif  recuo + brilho das bobinas (e o brilho de carga da PEM pesada) de cada uma
  armas_boiuna_ac.png    Boiuna antes (1.x) x depois (2.0), 1x e 2x, detalhes 3x e as granadas HE/AC
  armas_galeria_2_0.png  galeria como galeria_armas_3d.png com as armas novas nas fileiras da fase
  armas_casco_branco.png conferencia de leitura das 4 armas no casco branco, cinza, vermelho, azul-marinho e escuro
So le art3d/ e importa funcoes de tools/blender/compose_preview.py, tools/make_gallery.py e das previas das
granadas (make_sheets.py desta pasta); nao altera nada no repositorio fora das 4 imagens.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# copia no repositorio (ADDENDUM G13): caminhos relativos a esta pasta (tools/blender/previews/)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))
sys.path.insert(0, HERE)

import compose_preview as CP  # noqa: E402
import make_gallery as MG  # noqa: E402
import make_sheets as MS  # noqa: E402

ART = os.path.join(ROOT, "art3d")
OUT = os.path.join(ROOT, "docs", "preview", "3d", "v2")
SHELLS = os.path.join(ART, "bs_shells2")
BG = (7, 9, 14)
PAINT = (46, 58, 74)
GOLD = (255, 196, 70)
TEXT = (220, 226, 236)
DIM = (150, 160, 176)
NEWC = (120, 200, 255)

PEM = [
    {"short": "bs_pem_light", "name": "Tuvira", "full": "Canhão PEM Leve · agora uma TORRE de 270°", "shell": "pem_s",
     "facts": "1x2 · 1 tripulante · 40 mm · torre de 270° (gira ±135°; atrás fica o setor morto por onde a calha de "
              "células entra no anel, entre os 2 batentes) · 2 canos sincronizados",
     "angles": (0, 90, -135), "angle2x": -135, "arc": 270, "tier": "early"},
    {"short": "bs_pem_medium", "name": "Treme-Treme", "full": "Canhão PEM Médio", "shell": "pem_m",
     "facts": "2x2 · 2 tripulantes · 76 mm · torre de 300° · 1 cano grosso com 3 bobinas de cobre",
     "angles": (0, 40, -70), "tier": "mid"},
    {"short": "bs_pem_heavy", "name": "Corisco", "full": "Canhão PEM Pesado (overclock: Relâmpago)",
     "shell": "pem_l",
     "facts": "4x4 · 3 tripulantes · 155 mm · torre dupla de 270° · canos alternados em pilhas de bobinas acesas",
     "angles": (0, 30, -55), "tier": "late"},
]


def font(sz, bold=False):
    p = "/usr/share/fonts/opentype/inter/" + ("Inter-Bold.otf" if bold else "Inter-Medium.otf")
    return ImageFont.truetype(p, sz)


def meta(short):
    return json.load(open(os.path.join(ART, short, "meta.json")))


def roof(short, paint=PAINT):
    return CP.paint_roof(CP.load(os.path.join(ART, short), "roof.png"), paint)


def hull_field(w, h, paint):
    """Casco da nave em volta da peca: placas de 1 quadro na cor da pintura com juntas finas."""
    im = Image.new("RGBA", (w, h), tuple(paint) + (255,))
    dr = ImageDraw.Draw(im)
    dark = tuple(int(c * 0.80) for c in paint) + (255,)
    lite = tuple(min(255, int(c * 1.05 + 6)) for c in paint) + (255,)
    for x in range(0, w, 64):
        dr.line([(x, 0), (x, h)], fill=dark)
        dr.line([(x + 1, 0), (x + 1, h)], fill=lite)
    for y in range(0, h, 64):
        dr.line([(0, y), (w, y)], fill=dark)
        dr.line([(0, y + 1), (w, y + 1)], fill=lite)
    return im


def assemble(short, angle=0.0, bframes=None, overlays=(), fx=None, scale=1, paint=PAINT, crop=True, hull=False):
    """Peca montada como no jogo (teto pintado, sombra, torre + canos girados juntos). overlays = imagens do
    quadro da torre (brilho de carga) por cima da torre e dos canos (mistura alpha, como o meta registra), girando
    com ela. hull=True: casco da nave na mesma pintura em volta da peca (recorte fixo: peca + meio quadro)."""
    d = os.path.join(ART, short)
    m = meta(short)
    W, H = m["size"]
    pvx, pvy = m["pivot"]
    br = m["barrel"]
    bframes = bframes or [br["rest"]] * len(br["ys"])
    reach = br["root"] + br["length"] + 1.4
    top = max(0.0, reach - pvy) + 0.2
    side = max(0.0, reach - pvx, reach - (W - pvx)) + 0.2
    cw, ch = int((W + 2 * side) * 64), int((H + top + 0.4) * 64)
    ox, oy = int(side * 64), int(top * 64)
    canvas = hull_field(cw, ch, paint) if hull else Image.new("RGBA", (cw, ch), BG + (255,))
    if hull:   # juntas do casco alinhadas com a grade da peca
        canvas = hull_field(cw + 64, ch + 64, paint).crop((64 - ox % 64, 64 - oy % 64, 64 - ox % 64 + cw,
                                                           64 - oy % 64 + ch))
    canvas.alpha_composite(roof(short, paint), (ox, oy))
    base = CP.turret_layer(d, m, bframes, 0, None)
    lay = CP.turret_layer(d, m, bframes, 0, fx) if fx or overlays else base
    c = lay.width / 2
    for ov in overlays:
        CP.paste_center(lay, ov, c, c)
    base = CP.rotate_about_center(base, angle)
    lay = CP.rotate_about_center(lay, angle)
    px, py = ox + pvx * 64, oy + pvy * 64
    CP.paste_center(canvas, CP.shadow_of(base), px, py)
    CP.paste_center(canvas, lay, px, py)
    if hull:
        y0 = py - (br["root"] + br["length"] + 0.35) * 64
        canvas = canvas.crop((int(ox - 32), int(max(0, y0)), int(ox + W * 64 + 32),
                              int(min(canvas.height, oy + H * 64 + 24))))
    elif crop:
        canvas = CP.crop_content(canvas, BG, pad=6)
    if scale != 1:
        canvas = canvas.resize((canvas.width * scale, canvas.height * scale), Image.LANCZOS)
    return canvas


def sheet(header, rows, pad=22, cap_font=None, title_font=None):
    """header: [(texto, fonte, cor)]; rows: [(titulo, subtitulo, [(imagem, legenda, cor_legenda)])] -> folha com as
    figuras alinhadas pela base e legendas centradas embaixo."""
    cap_font = cap_font or font(15)
    title_font = title_font or font(22, True)
    sub_font = font(15)
    dr0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))

    def cap_lines(lab):
        return lab.split("\n")
    widths = []
    for _, _, items in rows:
        x = pad
        for im, lab, _ in items:
            tw = max(dr0.textlength(t, font=cap_font) for t in cap_lines(lab))
            x += max(im.width, int(tw)) + pad
        widths.append(x)
    hw = max(int(dr0.textlength(t, font=f)) + 2 * pad for t, f, _ in header)
    W = max(max(widths), hw)
    H = pad + sum(f.size + 8 for _, f, _ in header) + pad // 2
    for title, sub, items in rows:
        nl = max(len(cap_lines(lab)) for _, lab, _ in items)
        H += title_font.size + 10 + (sub_font.size + 8 if sub else 0) + max(im.height for im, _, _ in items) + \
            nl * (cap_font.size + 4) + 8 + pad
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    y = pad
    for t, f, col in header:
        dr.text((pad, y), t, font=f, fill=col)
        y += f.size + 8
    y += pad // 2
    for title, sub, items in rows:
        dr.text((pad, y), title, font=title_font, fill=GOLD)
        y += title_font.size + 10
        if sub:
            dr.text((pad, y), sub, font=sub_font, fill=DIM)
            y += sub_font.size + 8
        rh = max(im.height for im, _, _ in items)
        x = pad
        for im, lab, col in items:
            tw = int(max(dr.textlength(t, font=cap_font) for t in cap_lines(lab)))
            cw = max(im.width, tw)
            img.paste(im.convert("RGB"), (x + (cw - im.width) // 2, y + rh - im.height))
            for k, t in enumerate(cap_lines(lab)):
                lw = dr.textlength(t, font=cap_font)
                dr.text((x + (cw - lw) / 2, y + rh + 6 + k * (cap_font.size + 4)), t, font=cap_font,
                        fill=col or TEXT)
            x += cw + pad
        nl = max(len(cap_lines(lab)) for _, lab, _ in items)
        y += rh + nl * (cap_font.size + 4) + 8 + pad
    return img


def shell_cells(key, title):
    """Granada PEM da arma: no jogo a 1x e a 2x (com tracante e luzes, sobre casco escuro) e o sprite ampliado 3x."""
    m = json.load(open(os.path.join(SHELLS, "meta.json")))
    one = MS.cell_1x(SHELLS, m, key, lanes=("escuro",), label=False, width_t=3.2, lane_h=1.0)
    two = MS.cell_1x(SHELLS, m, key, lanes=("escuro",), label=False, width_t=3.2, lane_h=1.0, P=128)
    z = MS.cell_zoom(SHELLS, m, key, z=3, label=False)
    return [(one, f"granada {title}\nno jogo (1x)", None), (two, "granada (2x)", None), (z, "sprite da granada 3x", None)]


def arc_view(short, arc, scale=2, paint=PAINT):
    """Arco de tiro da torre: a peca em repouso, a torre "fantasma" (35 %) nos dois batentes (+-arc/2) e o setor do
    arco desenhado em ciano fraco com bordas tracejadas; o setor morto fica escuro."""
    d = os.path.join(ART, short)
    m = meta(short)
    W, H = m["size"]
    pvx, pvy = m["pivot"]
    br = m["barrel"]
    reach = br["root"] + br["length"] + 1.4
    top = max(0.0, reach - pvy) + 0.2
    side = max(0.0, reach - pvx, reach - (W - pvx)) + 0.2
    cw, ch = int((W + 2 * side) * 64), int((H + top + 0.4) * 64)
    ox, oy = int(side * 64), int(top * 64)
    S = 4
    canvas = Image.new("RGBA", (cw, ch), BG + (255,))
    canvas.alpha_composite(roof(short, paint), (ox, oy))
    px, py = ox + pvx * 64, oy + pvy * 64
    R = (br["root"] + br["length"] + 0.25) * 64
    sec = Image.new("RGBA", (cw * S, ch * S), (0, 0, 0, 0))
    dr = ImageDraw.Draw(sec)
    half = arc / 2
    box = [(px - R) * S, (py - R) * S, (px + R) * S, (py + R) * S]
    # PIL: angulo 0 = +x, sentido horario; a frente (cima) = -90
    dr.pieslice(box, -90 - half, -90 + half, fill=(90, 190, 255, 46))
    for k in range(0, int(arc), 6):
        a0 = -90 - half + k
        dr.arc(box, a0, a0 + 3, fill=(140, 215, 255, 210), width=2 * S)
    for sgn in (-1, 1):
        a = math.radians(-90 + sgn * half)
        for t in range(0, 20, 2):
            r0, r1 = R * t / 20, R * (t + 1) / 20
            dr.line([((px + math.cos(a) * r0) * S, (py + math.sin(a) * r0) * S),
                     ((px + math.cos(a) * r1) * S, (py + math.sin(a) * r1) * S)], fill=(140, 215, 255, 200), width=2 * S)
    sec = sec.resize((cw, ch), Image.LANCZOS)
    canvas.alpha_composite(sec)
    bf = [br["rest"]] * len(br["ys"])
    base = CP.turret_layer(d, m, bf, 0, None)
    for a in (half, -half):
        g = CP.rotate_about_center(base, a)
        ga = np.asarray(g).copy()
        ga[..., 3] = (ga[..., 3] * 0.38).astype(np.uint8)
        CP.paste_center(canvas, Image.fromarray(ga, "RGBA"), px, py)
    lay = base
    CP.paste_center(canvas, CP.shadow_of(lay), px, py)
    CP.paste_center(canvas, lay, px, py)
    canvas = CP.crop_content(canvas, BG, pad=6)
    if scale != 1:
        canvas = canvas.resize((canvas.width * scale, canvas.height * scale), Image.LANCZOS)
    return canvas



# ============================================================================ armas_pem.png
def make_pem():
    rows = []
    for w in PEM:
        s = w["short"]
        m = meta(s)
        items = []
        for a in w["angles"]:
            items.append((assemble(s, a), f"1x · {a:+d}°" if a else "1x · repouso", None))
        items.append((assemble(s, 0, scale=2), "2x · repouso", None))
        a2 = w.get("angle2x", w["angles"][1])
        items.append((assemble(s, a2, scale=2), f"2x · {a2:+d}°", None))
        if w.get("arc"):
            items.append((arc_view(s, w["arc"], scale=2), f"2x · arco de tiro de {w['arc']}°\n(fantasmas nos batentes)",
                          NEWC))
        cg = m["turret"].get("charge_glow")
        if cg:
            ov = [CP.load(os.path.join(ART, s), cg["frames"][-1])]
            items.append((assemble(s, 0, overlays=ov, scale=2), "2x · carregando o tiro\n(brilho de carga, quadro 4)",
                          NEWC))
        items += shell_cells(w["shell"], w["name"])
        rows.append((f"{w['name']} · {w['full']}", w["facts"], items))
    header = [("Armas PEM da 2.0: Tuvira · Treme-Treme · Corisco", font(30, True), TEXT),
              ("Como aparecem no jogo (64 px por quadro) com o teto pintado e a torre em alguns ângulos; 2x = ampliado "
               "2 vezes. Família PEM: bobinas de fio de cobre em todos os canos, luzes azuis fracas só em recessos "
               "(capacitores, células PEM, sensores).", font(15), DIM),
              ("Novo: a Tuvira virou torre de 270° (anel giratório no tile da frente, batentes a ±135°, tremonha de "
               "células atrás). A PEM pesada se chama Corisco (overclock Relâmpago).", font(15), NEWC),
              ("Depois de cada tiro as frestas entre as espiras acendem em azul (o cobre continua cobre); no Corisco, "
               "0,5 s antes do tiro, linhas azuis enchem as bobinas da raiz para a frente (brilho de carga).",
               font(15), DIM),
              ("À direita de cada arma, a granada PEM que ela dispara (arte dos projéteis 2.0 já aprovada): cápsula "
               "escura com bobinas de cobre e luz ciano — o mesmo cobre e o mesmo azul das armas.", font(15), DIM)]
    img = sheet(header, rows)
    p = os.path.join(OUT, "armas_pem.png")
    img.save(p, optimize=True)
    return p, img.size


# ============================================================================ armas_pem_disparo.gif
PEM_FLASH = [(255, 150, 60, 235), (70, 160, 255, 200), (170, 225, 255, 240), (240, 250, 255, 255)]


def pem_flash(scale, t, seed):
    """Clarao de boca PEM: lingua cobre-ambar por fora, nucleo azul-branco (spec: copper-amber flash + cyan arc).
    Como CP.flash, mas TODAS as camadas no mesmo eixo (CP.flash sorteia uma inclinacao por camada: a lingua
    cobre ficava torta e, fraca sobre o escuro, saia como uma cunha marrom de um lado so). A lingua cobre e
    forte (alpha ~235, somada) e um pouco mais longa que o nucleo azul: le como ponta laranja-quente."""
    S = 4
    U = 64 * scale * S
    w = h = int(3.0 * U)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx, cy = w / 2, h / 2
    k = (1 - t) ** 0.8
    rng = np.random.default_rng(seed)
    tilt = rng.uniform(-3, 3)
    reach = 1.35 + 0.3 * rng.random()
    for i, col in enumerate(PEM_FLASH):
        f = 1 - i * 0.2
        CP._flame(dr, cx, cy, U * reach * k * f * (1.10 if i == 0 else 1.0), U * 0.27 * k * f, tilt, col)
        for sx in (-1, 1):
            for j in range(3):  # fendas da boca emissora
                CP._flame(dr, cx + sx * U * 0.12, cy + U * (0.10 - j * 0.09), U * (0.55 - j * 0.08) * k * f,
                          U * 0.08 * k * f, sx * (78 + j * 6), col)
    im = im.resize((w // S, h // S), Image.LANCZOS)
    glow = im.filter(ImageFilter.GaussianBlur(7 * scale))
    return Image.alpha_composite(glow, im)


def muzzle_arcs(scale, t, seed):
    """2-3 arcos ciano curtos saltando em volta da boca."""
    S = 4
    U = 64 * scale * S
    w = int(1.6 * U)
    im = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    k = (1 - t)
    for j in range(3):
        a0 = rng.uniform(-2.4, 2.4)
        r0, r1 = U * 0.10, U * (0.35 + 0.25 * rng.random()) * (0.6 + 0.4 * k)
        pts = []
        for i in range(6):
            r = r0 + (r1 - r0) * i / 5
            a = a0 + rng.uniform(-0.35, 0.35)
            pts.append((w / 2 + math.sin(a) * r, w / 2 - math.cos(a) * r))
        dr.line(pts, fill=(150, 220, 255, int(255 * k)), width=max(2, int(S * scale * 0.9)))
        dr.line(pts, fill=(235, 250, 255, int(255 * k)), width=max(1, int(S * scale * 0.4)))
    im = im.resize((w // S, w // S), Image.LANCZOS)
    return Image.alpha_composite(im.filter(ImageFilter.GaussianBlur(2 * scale)), im)


def make_gif():
    """3 paineis lado a lado, mesma linha do tempo (40 ms por quadro): mira, disparos no padrao de cada arma (Tuvira
    sincronizada a cada ~0,84 s; Treme-Treme a cada 1,92 s; PEM pesada alternada, ~1,03 s entre tiros, com o brilho
    de carga de 0,5 s antes de cada tiro), recuo + bobinas azuis (quadros do cano) e clarao PEM; volta."""
    dt = 0.04
    scale = 2
    shots = {"bs_pem_light": [(0.50, [0, 1]), (1.34, [0, 1]), (2.18, [0, 1]), (3.02, [0, 1])],
             "bs_pem_medium": [(0.60, [0]), (2.52, [0])],
             "bs_pem_heavy": [(0.95, [0]), (1.98, [1]), (3.01, [0])]}
    aim = {"bs_pem_light": -70.0, "bs_pem_medium": -25.0, "bs_pem_heavy": -18.0}
    T_FIRE = 3.9
    n_aim = 10
    nf = n_aim + int(T_FIRE / dt) + n_aim
    panels = {}
    for w in PEM:
        s = w["short"]
        d = os.path.join(ART, s)
        m = meta(s)
        br = m["barrel"]
        seq = br["frames"]
        cg = m["turret"].get("charge_glow")
        cgi = [CP.load(d, f) for f in cg["frames"]] if cg else []
        cg_len = cg["interval"] * len(cg["frames"]) if cg else 0
        fsc = min(2.2, max(0.35, br["sprite_w"] / 0.46))
        frames = []
        for f in range(nf):
            if f < n_aim:
                ang = aim[s] * (1 - math.cos((f + 1) / n_aim * math.pi)) / 2
                t = -1.0
            elif f >= nf - n_aim:
                k = f - (nf - n_aim)
                ang = aim[s] * (1 + math.cos((k + 1) / n_aim * math.pi)) / 2
                t = 99.0
            else:
                ang = aim[s]
                t = (f - n_aim) * dt
            bnames = [seq[-1]] * len(br["ys"])
            fx, ovs = [], []
            for ts, bis in shots[s]:
                age = t - ts
                if 0 <= age:
                    idx = int(age / br["interval"])
                    for bi in bis:
                        if idx < len(seq) - 1:
                            bnames[bi] = seq[idx]
                    fa = int(age / dt)
                    if fa < 3:
                        for bi in bis:
                            fx.append((pem_flash(fsc, fa / 3, int(ts * 100) + bi * 7 + fa), br["muzzle"] - 0.14 * fsc,
                                       br["ys"][bi], True))
                    if fa < 4:
                        for bi in bis:
                            fx.append((muzzle_arcs(fsc, fa / 4, int(ts * 100) + bi * 13 + fa), br["muzzle"] + 0.05,
                                       br["ys"][bi], True))
                elif cgi and -cg_len <= age < 0:
                    k = min(len(cgi) - 1, int((age + cg_len) / cg["interval"]))
                    ovs = [cgi[k]]
            frames.append(assemble(s, ang, bframes=bnames, overlays=ovs, fx=fx, scale=1, crop=False))
        # recorte comum a todos os quadros do painel e ampliacao 2x
        boxes = []
        for im in frames:
            a = np.asarray(im.convert("RGB"), dtype=np.int16)
            ys, xs = np.where(np.abs(a - np.array(BG, dtype=np.int16)).sum(axis=2) > 6)
            boxes.append((xs.min(), ys.min(), xs.max(), ys.max()))
        bx = (max(0, min(b[0] for b in boxes) - 8), max(0, min(b[1] for b in boxes) - 8),
              max(b[2] for b in boxes) + 8, max(b[3] for b in boxes) + 8)
        panels[s] = [im.crop(bx).resize(((bx[2] - bx[0]) * scale, (bx[3] - bx[1]) * scale), Image.LANCZOS)
                     for im in frames]
    pad, top = 20, 72
    W = pad + sum(panels[w["short"]][0].width + pad for w in PEM)
    H = top + max(panels[w["short"]][0].height for w in PEM) + 52
    tf, lf, sf, sf2 = font(20, True), font(17, True), font(13), font(15)
    out = []
    for f in range(nf):
        img = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 10), "Disparo PEM (2x): recuo do cano + frestas das bobinas que acendem em azul", font=tf,
                fill=TEXT)
        dr.text((pad, 38), "o Corisco carrega 0,5 s antes de cada tiro (linhas azuis enchem as bobinas); 117 quadros "
                "de 40 ms", font=sf2, fill=DIM)
        x = pad
        for w in PEM:
            # paineis alinhados pela base (o recorte do painel termina 8 px abaixo da arma): o nome e a legenda
            # ficam logo embaixo de cada arma (em cima, o recorte inclui o alcance do clarao e o nome flutuava)
            p = panels[w["short"]][f]
            y = H - 52 - p.height
            img.paste(p.convert("RGB"), (x, y))
            dr.text((x + 4, y + p.height + 2), w["name"], font=lf, fill=GOLD)
            sub = {"bs_pem_light": "torre de 270°, 2 canos juntos", "bs_pem_medium": "1 tiro a cada 1,92 s",
                   "bs_pem_heavy": "alternado + brilho de carga"}[w["short"]]
            dr.text((x + 4, y + p.height + 24), sub, font=sf, fill=DIM)
            x += p.width + pad
        out.append(img)
    # paleta UNICA (montagem de quadros de mira, carga e disparo): o GIF guarda so o retangulo que muda entre
    # quadros (com uma paleta por quadro cada quadro inteiro era regravado: 17 MB)
    pick = [out[i] for i in (0, len(out) // 5, len(out) // 3, len(out) // 2, 2 * len(out) // 3, len(out) - 1)]
    mont = Image.new("RGB", (W, H * len(pick)))
    for i, im in enumerate(pick):
        mont.paste(im, (0, i * H))
    ref = mont.quantize(colors=250, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = [im.quantize(palette=ref, dither=Image.Dither.NONE) for im in out]
    p = os.path.join(OUT, "armas_pem_disparo.gif")
    pal[0].save(p, save_all=True, append_images=pal[1:], duration=40, loop=0, optimize=True, disposal=1)
    return p, out[0].size, len(out)


# ============================================================================ armas_casco_branco.png
HULLS = [("casco branco", (232, 234, 238)), ("cinza-claro", (176, 180, 186)), ("vermelho", (150, 40, 36)),
         ("azul-marinho", (46, 58, 74)), ("escuro", (30, 32, 36))]
CASCO = [("bs_pem_light", "Tuvira"), ("bs_pem_medium", "Treme-Treme"), ("bs_pem_heavy", "PEM pesada"),
         ("bs_boiuna_ac", "Boiúna AC")]


def make_casco():
    """Cada arma nova (uma linha) nas 5 pinturas do casco (teto pintado + casco da nave em volta), 1x; e a 2x no
    casco branco."""
    rows = []
    for s, name in CASCO:
        items = [(assemble(s, 0, paint=paint, hull=True), hname, None) for hname, paint in HULLS]
        rows.append((name, None, items))
    rows.append(("Casco branco a 2x", "as frestas escuras e os chanfros desenham a arma no casco claro",
                 [(assemble(s, 0, paint=HULLS[0][1], hull=True, scale=2), f"{name} · 2x", None)
                  for s, name in CASCO[:3]]))
    header = [("Armas 2.0 no casco branco e em outras pinturas", font(30, True), TEXT),
              ("Escala real (1x, 64 px por quadro): o teto da peça e o casco em volta recebem a mesma pintura da nave. "
               "Confere se a torre, os canos e as bobinas continuam legíveis em casco claro, médio e escuro.",
               font(15), DIM)]
    img = sheet(header, rows)
    p = os.path.join(OUT, "armas_casco_branco.png")
    img.save(p, optimize=True)
    return p, img.size


# ============================================================================ armas_boiuna_ac.png
def crop_zoom(short, name, box, z=3, bg=(40, 46, 56)):
    """Recorte de um sprite (box em px) ampliado z vezes sobre fundo de casco."""
    im = CP.load(os.path.join(ART, short), name).crop(box)
    im = im.resize((im.width * z, im.height * z), Image.LANCZOS)
    c = Image.new("RGBA", im.size, bg + (255,))
    c.alpha_composite(im)
    return c


def make_boiuna():
    old, new = "bs_nuke_howitzer", "bs_boiuna_ac"
    T = 314
    rows = [
        ("Antes × depois, como no jogo (teto pintado)", "à esquerda a Boiúna 1.x (obuseiro nuclear, destaque verde); à "
         "direita a Boiúna 2.0 (obuseiro pesado da munição AC, destaque âmbar)",
         [(assemble(old, 0), "antes · 1x", DIM), (assemble(new, 0), "depois · 1x", NEWC),
          (assemble(old, 0, scale=2), "antes · 2x", DIM), (assemble(new, 0, scale=2), "depois · 2x", NEWC)]),
        ("Girada e detalhes ampliados 3x", "a mesma arma girada no jogo; espinha (o trevo vira a serpente da Boiúna), "
         "freio de boca (portas com brilho âmbar) e camisa térmica (faixas de LED âmbar)",
         [(assemble(new, -35), "depois · 1x · −35°", NEWC), (assemble(new, 50, scale=2), "depois · 2x · +50°", NEWC),
          (crop_zoom(old, "turret.png", (119, 168, 195, 256)), "espinha antes · 3x", DIM),
          (crop_zoom(new, "turret.png", (119, 168, 195, 256)), "espinha depois · 3x", NEWC),
          (crop_zoom(old, "barrel1.png", (0, 0, 58, 120)), "freio antes · 3x", DIM),
          (crop_zoom(new, "barrel1.png", (0, 0, 58, 120)), "freio depois · 3x", NEWC),
          (crop_zoom(new, "barrel1.png", (0, 150, 58, 230)), "camisa depois · 3x", NEWC)]),
    ]
    m = json.load(open(os.path.join(SHELLS, "meta.json")))
    sh = []
    for key, lab in (("he_h", "granada HE (Alto-Explosivo)"), ("ac_h", "granada AC (Alta Capacidade)")):
        sh.append((MS.cell_1x(SHELLS, m, key, lanes=("escuro",), label=False, width_t=4.5, lane_h=1.4),
                   f"{lab}\nno jogo (1x)", None))
    for key, lab in (("he_h", "HE"), ("ac_h", "AC")):
        sh.append((MS.cell_zoom(SHELLS, m, key, z=2, label=False), f"{lab} · sprite 2x", None))
    rows.append(("As granadas da Boiúna 2.0", "o seletor tem só HE e AC; a AC é guiada (arte dos projéteis 2.0 já "
                 "aprovada)", sh))
    header = [("Boiúna 2.0: de obuseiro nuclear a obuseiro pesado da munição AC", font(30, True), TEXT),
              ("Mudou: destaque verde → âmbar (olhos, fendas, respiros, LEDs do teto e do piso, luz dinâmica); sem trevo "
               "nuclear e sem nenhum material verde; serpente da Boiúna gravada na espinha (corpo em S e cabeça em "
               "losango);", font(15), DIM),
              ("faixas de LED âmbar na camisa térmica e no canal do tubo; brilho âmbar fraco no fundo das portas do freio "
               "de boca; tampões do paiol com 4 travas (3 travas liam como trevo);", font(15), DIM),
              ("granadas dos vãos com cinta de latão; 5 postos no piso (tripulação 2.0). Ficou igual: escamas de "
               "serpente (correntes, presas, tubo em escamas), silhueta, recuo de 17 quadros.", font(15), DIM)]
    img = sheet(header, rows)
    p = os.path.join(OUT, "armas_boiuna_ac.png")
    img.save(p, optimize=True)
    return p, img.size


# ============================================================================ armas_galeria_2_0.png
def make_gallery():
    import bs_data as D
    new_by_tier = {"early": [("bs_pem_light", "Tuvira")], "mid": [("bs_pem_medium", "Treme-Treme")],
                   "late": [("bs_pem_heavy", "PEM pesada")]}
    rows = []
    for tier, title in MG.TIERS:
        items = []
        for g in D.GUNS + D.DEFENSES:
            if g["tier"] != tier:
                continue
            if g["short"] == "bs_nuke_howitzer":
                items.append(("bs_boiuna_ac", "Boiúna (AC)", 30, True))
            else:
                items.append((g["short"], g["codename"], g["size"][0] * g["size"][1], False))
        for s, name in new_by_tier[tier]:
            mm = meta(s)
            items.append((s, name, mm["size"][0] * mm["size"][1], True))
        items.sort(key=lambda t: t[2])
        items += [(x["short"], x["codename"], 0, False) for x in D.LAUNCHERS if x.get("tier") == tier]
        tiles = []
        for s, name, _, new in items:
            if not os.path.exists(os.path.join(ART, s, "meta.json")):
                continue
            tiles.append((MG.weapon_tile(s), name + (" · 2.0" if new else ""), NEWC if new else None))
        rows.append((title, None, tiles))
    header = [("Galeria de armas 2.0 (como no jogo, 2x)", font(34, True), TEXT),
              ("Em azul, as armas novas ou refeitas desta etapa: Tuvira, Treme-Treme e PEM pesada (linha PEM) e a Boiúna "
               "AC (sem visual nuclear). As outras armas continuam como na 1.x.", font(17), DIM)]
    img = sheet(header, rows, pad=20, cap_font=font(20, True), title_font=font(34, True))
    p = os.path.join(OUT, "armas_galeria_2_0.png")
    img.save(p, optimize=True)
    return p, img.size


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "todas"
    os.makedirs(OUT, exist_ok=True)
    for k, fn in (("pem", make_pem), ("boiuna", make_boiuna), ("galeria", make_gallery), ("casco", make_casco),
                  ("disparo", make_gif)):
        if what in (k, "todas"):
            print(k, fn())
