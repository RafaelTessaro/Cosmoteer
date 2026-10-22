"""Previas do grupo "itens" da 2.0 (so le PNGs; sem bpy), versionadas para poderem ser refeitas a partir do repo:

    python3 tools/blender/parts/_bs2_itens_previews.py [itens|icones|todas]

  itens  -> docs/preview/3d/v2/municoes_itens.png: os 12 recursos 2.0 (pilhas 1..N numa celula de deposito, icone,
            sobreposicao, unidade solta), a sala de carga, a familia ao lado dos projeteis 2.0, os pares que se
            confundiam (forma e cor a 1x) e a conferencia de leitura (piso escuro/claro, casco branco, espaco);
  icones -> docs/preview/3d/v2/icones_2_0.png: os icones 2.0 da interface (art3d/bs_ui_icons2, gerados por
            tools/bsgen/ui_icons.py) a 1x e 2x sobre o fundo dos botoes do jogo (imitacao), o icone do buff da Fita
            (gui/buff_fita.png) sobre uma maquina grudada na Fita e o antes/depois 1.x.
Modulo do grupo "itens" (regra dos arquivos compartilhados: nao edita compose_*.py, so importa compose_preview).
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))                 # tools/blender/parts
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))    # raiz do repo
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import compose_preview as CP  # noqa: E402
from bsgen import ui_icons as U  # noqa: E402

ART = os.path.join(ROOT, "art3d")
ICONS = os.path.join(ART, "bs_ui_icons2")
OUT_ITENS = os.path.join(ROOT, "docs", "preview", "3d", "v2", "municoes_itens.png")
OUT_ICONES = os.path.join(ROOT, "docs", "preview", "3d", "v2", "icones_2_0.png")
PX = 64
BG = (7, 9, 14)
PAINT = (46, 58, 74)
TEXT = (220, 226, 236)
DIM = (150, 160, 176)
GOLD = (255, 196, 70)
WHITE = (240, 242, 246)
UIBG = (31, 35, 43)
PANEL = (22, 25, 31)

FAMILIES = [
    ("Cartuchos · carregadores dos canhões (seletor de munição)", (255, 190, 60), [
        ("bs_mag_std", "Carregador HE", "Alto-Explosivo · pilha de 6", ("s", "he_s")),
        ("bs_mag_ap", "Carregador AP", "Perfurante · pilha de 4", ("s", "ap_s")),
        ("bs_mag_sap", "Carregador SAP", "Semiperfurante · pilha de 5", ("s", "sap_s")),
        ("bs_mag_ac", "Carregador AC", "Alta Capacidade · pilha de 3", ("s", "ac_s")),
        ("bs_mag_frag", "Carregador FRAG", "Nuvem de Fragmentos · pilha de 6", None),
    ]),
    ("Células · Plasma e PEM (seletor de célula)", (60, 220, 255), [
        ("bs_plasma_cell", "Célula de Plasma", "Boitatá e Curupira · pilha de 4", None),
        ("bs_cell_emp", "Célula PEM", "Tuvira, Treme-Treme e Corisco · pilha de 4", ("s", "pem_s")),
    ]),
    ("Mísseis · cargas e ogiva (seletor de míssil)", (255, 120, 40), [
        ("bs_msl_he", "Carga de Míssil HE", "Jararaca · pilha de 10", ("m", "he_m")),
        ("bs_msl_cluster", "Carga de Submunição", "Piranha · pilha de 10", ("m", "cluster_m")),
        ("bs_msl_emp", "Carga de Míssil PEM", "Poraquê · pilha de 10", ("m", "emp_m")),
        ("bs_msl_nuke", "Ogiva Nuclear", "Iara · pilha de 2", ("m", "nuclear_wh_l")),
    ]),
    ("Projéteis · railgun Tupã", (110, 175, 255), [
        ("bs_slug_rail", "Projétil de Railgun", "Tupã · pilha de 2", ("s", "slug")),
    ]),
]
MASK = {"he": (255, 190, 60), "ap": (215, 230, 255), "sap": (255, 140, 50), "ac": (230, 40, 80)}

_F = {}


def font(sz, bold=False):
    k = (sz, bold)
    if k not in _F:
        p = "/usr/share/fonts/opentype/inter/" + ("Inter-Bold.otf" if bold else "Inter-Medium.otf")
        _F[k] = ImageFont.truetype(p, sz)
    return _F[k]


def load(short, name):
    return Image.open(os.path.join(ART, short, name)).convert("RGBA")


def meta(short):
    return json.load(open(os.path.join(ART, short, "meta.json")))


def up(im, k):
    return im if k == 1 else im.resize((im.width * k, im.height * k), Image.NEAREST)


# ============================================================================ fundos
def storage_cell(light=False):
    """Celula de deposito (piso de carga, 64 x 64): chapa escura com bisel, cantoneiras e grade fina."""
    base = (150, 154, 160) if light else (50, 54, 61)
    im = Image.new("RGBA", (PX, PX), base + (255,))
    d = ImageDraw.Draw(im)
    lo = tuple(int(c * 0.55) for c in base)
    hi = tuple(min(255, int(c * 1.25) + 6) for c in base)
    d.rectangle([0, 0, 63, 63], outline=lo + (255,))
    d.line([1, 1, 62, 1], fill=hi + (255,))
    d.line([1, 1, 1, 62], fill=hi + (255,))
    mid = tuple(int(c * 0.86) for c in base)
    for k in (16, 32, 48):
        d.line([2, k, 61, k], fill=mid + (255,))
        d.line([k, 2, k, 61], fill=mid + (255,))
    br = tuple(min(255, int(c * 1.5) + 10) for c in base)
    for (x, y, sx, sy) in ((3, 3, 1, 1), (60, 3, -1, 1), (3, 60, 1, -1), (60, 60, -1, -1)):
        d.line([x, y, x + 6 * sx, y], fill=br + (255,))
        d.line([x, y, x, y + 6 * sy], fill=br + (255,))
    return im


def white_hull():
    return CP.hull_tiles(PX, PX, (222, 225, 230), tile=PX)


def space():
    im = Image.new("RGBA", (PX, PX), BG + (255,))
    rng = np.random.default_rng(3)
    d = ImageDraw.Draw(im)
    for _ in range(5):
        x, y = rng.integers(0, 64, 2)
        d.point((int(x), int(y)), fill=(120, 130, 150, 255))
    return im


def ui_box(w, h, sel=False):
    """Fundo de interface do jogo (painel escuro com borda fina)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=6, fill=UIBG + (255,),
                        outline=((0, 183, 255) if sel else (70, 78, 92)) + (255,))
    return im


def on(bg, spr, k=1):
    bg = bg.copy()
    bg.alpha_composite(spr)
    return up(bg, k)


def _wrap(d, text, f, w):
    """Quebra o texto em linhas que cabem em w px (primeiro nos " · ", depois nos espacos)."""
    if d.textlength(text, font=f) <= w:
        return [text]
    parts = text.split(" · ")
    if len(parts) > 1 and all(d.textlength(p, font=f) <= w for p in parts):
        return parts
    lines, cur = [], ""
    for word in text.split(" "):
        t = (cur + " " + word).strip()
        if cur and d.textlength(t, font=f) > w:
            lines.append(cur)
            cur = word
        else:
            cur = t
    return lines + [cur]


def label_block(w, h, name, sub, col):
    """Nome + subtitulo do item; o subtitulo quebra em linhas para nao passar por baixo das pilhas."""
    im = Image.new("RGBA", (w, h), BG + (255,))
    d = ImageDraw.Draw(im)
    lines = _wrap(d, sub, font(12), w - 16)
    d.rectangle([0, 4, 3, 40 + 16 * (len(lines) - 1)], fill=col + (255,))
    d.text((12, 2), name, font=font(17, True), fill=WHITE)
    for i, t in enumerate(lines):
        d.text((12, 26 + 16 * i), t, font=font(12), fill=DIM)
    return im


# ============================================================================ blocos
def item_row(short, name, sub, col):
    m = meta(short)
    n = m["stack"]
    cells = []
    floor = storage_cell()
    for k in range(1, n + 1):
        cells.append(on(floor, load(short, f"stack_{k}.png")))
    full3 = on(floor, load(short, f"stack_{n}.png"), 3)
    one3 = on(floor, load(short, "stack_1.png"), 3)
    icon = load(short, "icon.png")
    ov = load(short, "overlay.png")
    nug = load(short, "nugget.png")
    lw = 250
    parts = []
    # 1x: pilhas 1..N (2 fileiras quando N > 6)
    per = 6 if n > 6 else n
    gx = 70
    strip = Image.new("RGBA", (per * gx, 2 * gx if n > 6 else gx), BG + (255,))
    d = ImageDraw.Draw(strip)
    for i, c in enumerate(cells):
        strip.paste(c, ((i % per) * gx, (i // per) * gx))
    parts.append(("pilhas 1–%d (1×)" % n, strip))
    parts.append(("1 unidade (3×)", one3))
    parts.append(("pilha cheia (3×)", full3))
    ib = ui_box(76, 76)
    ib.alpha_composite(icon, (6, 6))
    ib3 = ui_box(204, 204)
    ib3.alpha_composite(up(icon, 3), (6, 6))
    icon_blk = Image.new("RGBA", (76 + 8 + 204, 204), BG + (255,))
    icon_blk.paste(ib, (0, 0))
    icon_blk.paste(ib3, (84, 0))
    parts.append(("ícone (1× e 3×)", icon_blk))
    ob = ui_box(140, 140)
    ob.alpha_composite(ov, (6, 6))
    parts.append(("sobreposição", ob))
    nb = Image.new("RGBA", (64 * 2 + 8, 64 * 2 + 8 + 70), BG + (255,))
    nb.paste(on(storage_cell(), nug, 2), (0, 0))
    nb.paste(on(storage_cell(), nug), (0, 64 * 2 + 8))
    nb.paste(on(white_hull(), nug), (72, 64 * 2 + 8))
    parts.append(("unidade solta (2× e 1×)", nb))
    W = lw + sum(p[1].width + 18 for p in parts)
    H = max(p[1].height for p in parts) + 22
    row = Image.new("RGBA", (W, H), BG + (255,))
    row.paste(label_block(lw - 10, 80, name, sub, col), (0, 18))
    d = ImageDraw.Draw(row)
    x = lw
    for cap, im in parts:
        d.text((x, 0), cap, font=font(11), fill=DIM)
        row.paste(im, (x, 18))
        x += im.width + 18
    return row


def storage_room(scale=2):
    """Sala de carga 8 x 4 (paredes, piso de carga) com a pilha CHEIA de cada item, cercada pelo casco pintado."""
    cols, rows = 6, 2
    W, H = cols + 2, rows + 2
    img = CP.hull_tiles(W * PX, H * PX, PAINT, tile=PX)
    inner = Image.new("RGBA", (cols * PX, rows * PX), (0, 0, 0, 255))
    shorts = [s for _, _, its in FAMILIES for s, *_ in its]
    for i, s in enumerate(shorts):
        cx, cy = i % cols, i // cols
        c = storage_cell()
        c.alpha_composite(load(s, f"stack_{meta(s)['stack']}.png"))
        inner.paste(c, (cx * PX, cy * PX))
    img.paste(inner, (PX, PX))
    d = ImageDraw.Draw(img)
    wc = (64, 67, 71, 255)
    d.rectangle([PX - 3, PX - 3, (cols + 1) * PX + 2, (rows + 1) * PX + 2], outline=wc, width=3)
    d.rectangle([PX - 4, PX - 4, (cols + 1) * PX + 3, (rows + 1) * PX + 3], outline=(20, 21, 24, 255), width=1)
    return up(img, scale), img


def family_pairs():
    """Cada item (icone 3x) ao lado do projetil 2.0 que ele vira (sprite do jogo, granadas 128 px/quadro a 1x nativo,
    misseis 64 px/quadro a 2x): mesmas luvas claras, frestas pretas, faixas e LEDs."""
    cells = []
    sm = json.load(open(os.path.join(ART, "bs_shells2", "meta.json")))
    mm = json.load(open(os.path.join(ART, "bs_missiles2", "meta.json")))
    for _, col, its in FAMILIES:
        for short, name, sub, pr in its:
            if pr is None:
                continue
            kind, key = pr
            if kind == "s":
                it = sm["items"][key]
                ammo = key.split("_")[0]
                body, lt = CP._proj_layers(os.path.join(ART, "bs_shells2"), it, 0, MASK.get(ammo))
                k = 1
            else:
                it = mm["items"][key]
                body, lt = CP._proj_layers(os.path.join(ART, "bs_missiles2"), it, 0, None)
                k = 2
            body = body.resize((body.width * k, body.height * k), Image.LANCZOS)
            if lt is not None:
                lt = lt.resize(body.size, Image.LANCZOS)
            pw = max(body.width, 150)
            cw = 204 + 24 + pw + 20
            cell = Image.new("RGBA", (cw, 236), BG + (255,))
            ib = ui_box(204, 204)
            ib.alpha_composite(up(load(short, "icon.png"), 3), (6, 6))
            cell.paste(ib, (0, 24))
            plate = CP.hull_tiles(pw + 20, 204, PAINT, tile=PX)
            CP.paste_center(plate, body, plate.width / 2, 102)
            if lt is not None:
                CP.add_center(plate, lt, plate.width / 2, 102, gain=1.0)
            cell.paste(plate, (228, 24))
            d = ImageDraw.Draw(cell)
            d.text((0, 2), name, font=font(13, True), fill=WHITE)
            d.text((228, 2), "→ em voo: %s" % key, font=font(11), fill=DIM)
            cells.append(cell)
    return cells


def pairs_block():
    """Os pares HE/SAP/AP (carregadores) e HE/Piranha (cargas): stack_1 e pilha cheia a 1x e 4x, piso e casco branco."""
    groups = [[("bs_mag_std", "HE"), ("bs_mag_sap", "SAP"), ("bs_mag_ap", "AP")],
              [("bs_msl_he", "Míssil HE"), ("bs_msl_cluster", "Submunição")]]
    k = 3
    cw = 64 * k * 2 + 8 + 2 * 72 + 30
    rows = []
    for g in groups:
        row = Image.new("RGBA", (len(g) * (cw + 20), 64 * k + 40), BG + (255,))
        d = ImageDraw.Draw(row)
        for i, (s, lab) in enumerate(g):
            x = i * (cw + 20)
            n = meta(s)["stack"]
            d.text((x, 0), lab, font=font(14, True), fill=WHITE)
            st1, stn = load(s, "stack_1.png"), load(s, f"stack_{n}.png")
            row.paste(on(storage_cell(), st1, k), (x, 22))
            row.paste(on(white_hull(), stn, k), (x + 64 * k + 8, 22))
            for j, (bg, im) in enumerate(((storage_cell(), st1), (white_hull(), st1), (storage_cell(), stn),
                                          (white_hull(), stn))):
                row.paste(on(bg, im), (x + 2 * 64 * k + 16 + (j % 2) * 72, 22 + (j // 2) * 72))
        rows.append(row)
    W = max(r.width for r in rows)
    out = Image.new("RGBA", (W, sum(r.height + 10 for r in rows)), BG + (255,))
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height + 10
    return out


def legibility():
    """Pilha cheia e icone de cada item a 1x sobre piso escuro, piso claro, casco branco e espaco."""
    shorts = [(s, n) for _, _, its in FAMILIES for s, n, *_ in its]
    bgs = [("piso de carga escuro", storage_cell()), ("piso claro", storage_cell(light=True)),
           ("casco branco", white_hull()), ("espaço", space())]
    gx = 76
    W = 190 + len(shorts) * gx
    H = len(bgs) * gx + 30
    im = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(im)
    short_lab = ["HE", "AP", "SAP", "AC", "FRAG", "Plasma", "PEM", "Míssil HE", "Submunição", "Míssil PEM", "Ogiva",
                 "Railgun"]
    for j, lab in enumerate(short_lab):
        d.text((190 + j * gx, 0), lab, font=font(11), fill=DIM)
    for i, (lab, bg) in enumerate(bgs):
        y = 18 + i * gx
        d.text((0, y + 24), lab, font=font(13), fill=TEXT)
        for j, (s, n) in enumerate(shorts):
            st = load(s, f"stack_{meta(s)['stack']}.png")
            im.paste(on(bg, st), (190 + j * gx, y))
    return im


# ============================================================================ folha
def build_itens(out=OUT_ITENS):
    blocks = []
    W = 1900
    head = Image.new("RGBA", (W, 150), BG + (255,))
    d = ImageDraw.Draw(head)
    d.text((14, 10), "Munições 2.0: os 12 itens no visual futurista", font=font(30, True), fill=WHITE)
    lines = [
        "Todos os recursos da 2.0 refeitos na linguagem das granadas e dos mísseis 2.0: núcleo escuro por baixo, "
        "cascas claras "
        "de bisel duplo, frestas pretas, LEDs só em recessos escuros",
        "e cada tipo se reconhece pela COR e pela FORMA a 1×: HE ogivas escuras em seta, AP agulhas, SAP tampas claras "
        "chatas, AC 2 guiadas com ouro, FRAG curtas; cargas num berço escuro de prateleira.",
        "Escala real = 64 px por quadro (como o jogo desenha a pilha de 1..N unidades num quadro de depósito); ao "
        "lado, "
        "ampliado 3× com os pixels do jogo. Ícone 64 px, sobreposição 128 px,",
        "unidade solta = o que o tripulante carrega (do tamanho de uma unidade da pilha). Desvios conscientes do spec: "
        "Tupã AZUL (referência do usuário), Piranha AMARELA (mísseis 2.0), SAP laranja-avermelhado.",
    ]
    for i, t in enumerate(lines):
        d.text((14, 54 + i * 21), t, font=font(14), fill=TEXT if i < 2 else DIM)
    blocks.append(head)
    # sala de carga montada (1x e 2x)
    big, small = storage_room(2)
    sec = Image.new("RGBA", (W, big.height + 50), BG + (255,))
    d = ImageDraw.Draw(sec)
    d.text((14, 4), "Sala de carga com a pilha cheia de cada item, cercada pelo casco pintado (2× e 1×)",
           font=font(18, True), fill=GOLD)
    sec.paste(big, (14, 36))
    sec.paste(small, (14 + big.width + 30, 36))
    d.text((14 + big.width + 30, 36 + small.height + 10),
           "1ª fileira: HE · AP · SAP · AC · FRAG · Plasma", font=font(12), fill=DIM)
    d.text((14 + big.width + 30, 36 + small.height + 28),
           "2ª fileira: PEM · Míssil HE · Submunição · Míssil PEM · Ogiva · Railgun", font=font(12), fill=DIM)
    blocks.append(sec)
    for title, col, its in FAMILIES:
        t = Image.new("RGBA", (W, 40), BG + (255,))
        ImageDraw.Draw(t).text((14, 10), title, font=font(19, True), fill=col)
        blocks.append(t)
        for short, name, sub, _ in its:
            r = item_row(short, name, sub, col)
            pad = Image.new("RGBA", (W, r.height + 14), BG + (255,))
            pad.paste(r, (14, 0))
            blocks.append(pad)
    # familia: item x projetil em voo
    t = Image.new("RGBA", (W, 64), BG + (255,))
    d = ImageDraw.Draw(t)
    d.text((14, 8), "Mesma família dos projéteis 2.0: o item (ícone 3×) ao lado do projétil em que ele vira",
           font=font(19, True), fill=GOLD)
    d.text((14, 36), "granadas = sprite do jogo (128 px por quadro) com a faixa tingida como o jogo faz; mísseis = "
           "sprite do jogo ampliado 2×; luzes do quadro 0 somadas", font=font(12), fill=DIM)
    blocks.append(t)
    cells = family_pairs()
    rows, row, w = [], [], 14
    for c in cells:
        if row and w + c.width > W - 14:
            rows.append(row)
            row, w = [], 14
        row.append(c)
        w += c.width + 26
    rows.append(row)
    for row in rows:
        r = Image.new("RGBA", (W, max(c.height for c in row) + 14), BG + (255,))
        x = 14
        for c in row:
            r.paste(c, (x, 0))
            x += c.width + 26
        blocks.append(r)
    # pares que precisam se distinguir a 1x (rodada 1 da revisao)
    t = Image.new("RGBA", (W, 64), BG + (255,))
    d = ImageDraw.Draw(t)
    d.text((14, 8), "Pares que se confundiam: forma E cor a 1× (piso escuro e casco branco) e 3×",
           font=font(19, True), fill=GOLD)
    d.text((14, 36), "HE × SAP × AP no mesmo seletor e na mesma fábrica; Jararaca × Piranha no seletor de míssil; "
           "1 unidade e a pilha cheia", font=font(12), fill=DIM)
    blocks.append(t)
    pr = pairs_block()
    r = Image.new("RGBA", (W, pr.height + 20), BG + (255,))
    r.paste(pr, (14, 0))
    blocks.append(r)
    # conferencia de leitura
    t = Image.new("RGBA", (W, 64), BG + (255,))
    d = ImageDraw.Draw(t)
    d.text((14, 8), "Conferência de leitura a 1×: pilha cheia sobre piso escuro, piso claro, casco branco e espaço",
           font=font(19, True), fill=GOLD)
    d.text((14, 36), "a cor de cada munição e a silhueta (narizes, bobinas, pétalas, trevo) precisam ler nos quatro "
           "fundos sem brilho estourado", font=font(12), fill=DIM)
    blocks.append(t)
    lg = legibility()
    r = Image.new("RGBA", (W, lg.height + 20), BG + (255,))
    r.paste(lg, (14, 0))
    blocks.append(r)
    H = sum(b.height for b in blocks) + 20
    sheet = Image.new("RGBA", (W, H), BG + (255,))
    y = 0
    for b in blocks:
        sheet.paste(b, (0, y))
        y += b.height
    sheet.convert("RGB").save(out, optimize=True)
    print(out, sheet.size)


# ============================================================================ icones 2.0
def button(size, sel=False, hover=False):
    """Botao de alternancia do painel da peca (imitacao do jogo): quadrado escuro azulado com bisel, borda fina; o
    selecionado ganha a borda azul da interface e um fundo um pouco mais claro."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = max(3, size // 16)
    fill = (44, 52, 64) if sel else (33, 38, 47)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=fill + (255,),
                        outline=((0, 183, 255) if sel else (74, 84, 99)) + (255,), width=max(1, size // 48))
    # bisel: luz em cima, sombra embaixo
    d.line([r, 2, size - r, 2], fill=tuple(min(255, c + 22) for c in fill) + (255,))
    d.line([r, size - 3, size - r, size - 3], fill=tuple(int(c * 0.7) for c in fill) + (255,))
    if sel:
        d.rounded_rectangle([3, 3, size - 4, size - 4], radius=max(2, r - 2), outline=(0, 110, 170, 255), width=1)
    return im


def icon_on_button(icon, size, sel=False, fill=0.92):
    b = button(size, sel)
    s = int(round(size * fill))
    ic = icon.resize((s, s), Image.LANCZOS) if s != icon.width else icon
    b.alpha_composite(ic, ((size - s) // 2, (size - s) // 2))
    return b


GROUPS = [
    ("Seletor de munição dos canhões (bs_ammo_type)", [
        ("ammo_he.png", "HE", "Alto-Explosivo"), ("ammo_ap.png", "AP", "Perfurante"),
        ("ammo_sap.png", "SAP", "Semiperfurante"), ("ammo_ac.png", "AC", "Alta Capacidade"),
        ("ammo_frag.png", "FRAG", "Nuvem de Fragmentos")]),
    ("Seletor de célula (bs_cell_type)", [
        ("cell_plasma.png", "Plasma", "Célula de Plasma"), ("cell_pem.png", "PEM", "Célula PEM")]),
    ("Seletor de míssil (bs_missile_type)", [
        ("missile_he.png", "Míssil HE", "Jararaca"), ("missile_cluster.png", "Submunição", "Piranha"),
        ("missile_emp.png", "Míssil PEM", "Poraquê"), ("missile_nuclear.png", "Nuclear", "Iara")]),
    ("Projétil da railgun e grupo do editor", [
        ("slug_rail.png", "Railgun", "Projétil da Tupã"), ("group_bullet_strike.png", "Bullet Strike",
                                                            "grupo do editor")]),
]
def _old_std():
    """Icone 1.x ammo_std (cartucho liso): apagado do ui_icons na 2.0 (SPEC ui_icons.drop); redesenhado aqui com as
    mesmas formas so para o antes/depois."""
    p = U.Pen()
    U.shell(p, 48, 12, 84, 24)
    return p.render()


BEFORE = [("ammo_he.png", "ammo_std (Padrão)", _old_std),
          ("ammo_ap.png", "ammo_ap", lambda: U.icon_ammo("ap")),
          ("missile_he.png", "missile_he", lambda: U.icon_missile("he")),
          ("missile_cluster.png", "missile_cluster", lambda: U.icon_missile("cluster")),
          ("missile_emp.png", "missile_emp", lambda: U.icon_missile("emp")),
          ("missile_nuclear.png", "missile_nuclear", lambda: U.icon_missile("nuclear")),
          ("group_bullet_strike.png", "group_bullet_strike", U.icon_group)]


def group_block(title, items, W):
    ic = {f: Image.open(os.path.join(ICONS, f)).convert("RGBA") for f, *_ in items}
    col_w = 340
    im = Image.new("RGBA", (W, 330), BG + (255,))
    d = ImageDraw.Draw(im)
    d.text((14, 6), title, font=font(19, True), fill=GOLD)
    # tira do seletor como no painel do jogo (o 1o selecionado), tamanho real de botao do painel (~48 px)
    x = 14
    d.text((x, 38), "no painel da peça (~48 px, o 1º selecionado)", font=font(11), fill=DIM)
    strip = Image.new("RGBA", (len(items) * 52 + 12, 60), PANEL + (255,))
    for i, (f, *_r) in enumerate(items):
        strip.alpha_composite(icon_on_button(ic[f], 48, sel=(i == 0)), (6 + i * 52, 6))
    im.paste(strip, (x, 56))
    x0 = 14 + max(strip.width, 280) + 24
    for i, (f, short, long_) in enumerate(items):
        cx = x0 + i * col_w
        if cx + col_w > W:
            break
        d.text((cx, 38), short, font=font(16, True), fill=WHITE)
        d.text((cx, 58), long_, font=font(12), fill=DIM)
        b1 = icon_on_button(ic[f], 104, sel=False, fill=96 / 104)
        im.paste(b1, (cx, 84))
        d.text((cx, 84 + 108), "1× (96 px)", font=font(10), fill=DIM)
        b2 = icon_on_button(ic[f].resize((192, 192), Image.LANCZOS), 206, sel=(i == 0), fill=192 / 206)
        im.paste(b2, (cx + 114, 84))
        d.text((cx + 114, 84 + 210), "2× (selecionado)" if i == 0 else "2×", font=font(10), fill=DIM)
    return im


def buff_block(W):
    """Icone do buff da Fita (gui/buff_fita.png, BulletStrike_FitaLink): 1x/2x no botao e no jogo, sobre um paiol 2x2
    grudado numa Fita, com o retangulo verde do buff e o icone no tamanho do jogo (Size 0,5 quadro = 32 px)."""
    ic = Image.open(os.path.join(ICONS, "buff_fita.png")).convert("RGBA")
    im = Image.new("RGBA", (W, 84 + 5 * PX + 16), BG + (255,))
    d = ImageDraw.Draw(im)
    d.text((14, 6), "Buff da Fita (gui/buff_fita.png)", font=font(19, True), fill=GOLD)
    d.text((14, 38), "a peça Fita vista de cima: cubo octogonal, 4 braços de elos e o cassete; cassete e luzes de "
           "ligação no verde do buff (110, 230, 120)", font=font(11), fill=DIM)
    b1 = icon_on_button(ic, 104, fill=96 / 104)
    im.paste(b1, (14, 84))
    d.text((14, 84 + 108), "1× (96 px)", font=font(10), fill=DIM)
    b2 = icon_on_button(ic.resize((192, 192), Image.LANCZOS), 206, fill=192 / 206)
    im.paste(b2, (128, 84))
    d.text((128, 84 + 210), "2×", font=font(10), fill=DIM)

    # no jogo: paiol 2x2 (teto de cartuchos) com a Fita grudada a esquerda; o paiol recebe o buff
    def scene():
        sc = CP.hull_tiles(4 * PX, 3 * PX, PAINT, tile=PX)
        paiol = Image.new("RGBA", (2 * PX, 2 * PX), (0, 0, 0, 0))
        paiol.alpha_composite(load("bs_paiol", "floor_2x2.png"))
        paiol.alpha_composite(CP.paint_roof(load("bs_paiol", "roof_cartuchos_2x2.png"), PAINT))
        sc.alpha_composite(paiol, (2 * PX - PX // 2, PX // 2))
        fita = CP.paint_roof(load("bs_fita", "roof.png"), PAINT)
        sc.alpha_composite(fita, (PX - PX // 2, PX // 2))
        sc.alpha_composite(load("bs_fita", "luz_grudada_teto.png"), (PX - PX // 2, PX // 2))
        ov = Image.new("RGBA", (2 * PX, 2 * PX), (110, 230, 120, 64))
        od = ImageDraw.Draw(ov)
        od.rectangle([0, 0, 2 * PX - 1, 2 * PX - 1], outline=(110, 230, 120, 160), width=2)
        sc.alpha_composite(ov, (2 * PX - PX // 2, PX // 2))
        sc.alpha_composite(ic.resize((PX // 2, PX // 2), Image.LANCZOS), (2 * PX - PX // 2 + PX - PX // 4,
                                                                         PX // 2 + PX - PX // 4))
        return sc
    sc = scene()
    x = 380
    d.text((x, 62), "no jogo (1×): paiol 2×2 grudado na Fita, retângulo verde do buff e o ícone a 32 px",
           font=font(11), fill=DIM)
    im.paste(sc, (x, 84))
    x2 = x + max(sc.width, int(d.textlength("no jogo (1×): paiol 2×2 grudado na Fita, retângulo verde do buff e "
                                            "o ícone a 32 px", font=font(11)))) + 30
    big = up(sc.crop((PX // 4, PX // 4, 4 * PX - PX // 4, 3 * PX - PX // 4)), 2)
    d.text((x2, 62), "recorte 2×", font=font(11), fill=DIM)
    im.paste(big, (x2, 84))
    return im


def build_icones(out=OUT_ICONES):
    W = 2080
    blocks = []
    head = Image.new("RGBA", (W, 130), BG + (255,))
    d = ImageDraw.Draw(head)
    d.text((14, 10), "Ícones 2.0 da interface", font=font(30, True), fill=WHITE)
    for i, t in enumerate([
        "Mesmo padrão dos ícones do jogo (gui/game/parts/missile_type_*): silhueta AZUL da interface (0, 183, 255) com "
        "brilho suave, 96 × 96 px, e um único destaque de cor por tipo.",
        "Linguagem 2.0 pela silhueta: luvas partidas por frestas finas (em divisa na Jararaca), ogiva pontuda com o "
        "anel do sensor, granada guiada com canards na AC, estilhaços na FRAG, cápsulas, anéis de armadura.",
        "Fundo = botão de alternância do painel da peça (imitação: os PNGs do jogo não estão no repositório). 1× = o "
        "arquivo de 96 px; 2× ampliado; à esquerda o tamanho real no painel (~48 px).",
    ]):
        d.text((14, 54 + i * 22), t, font=font(14), fill=TEXT if i < 2 else DIM)
    blocks.append(head)
    for title, items in GROUPS:
        blocks.append(group_block(title, items, W))
    blocks.append(buff_block(W))
    # antes / depois
    t = Image.new("RGBA", (W, 300), BG + (255,))
    d = ImageDraw.Draw(t)
    d.text((14, 6), "Antes (1.x) e depois (2.0)", font=font(19, True), fill=GOLD)
    d.text((14, 34), "saem na 2.0 (apagados do gerador e do build): ammo_std, ammo_aphe, ammo_emp, missile_limpet, "
           "missile_napalm, missile_torpedo; os 1.x abaixo são só a comparação", font=font(12), fill=DIM)
    x = 14
    for f, lab, fn in BEFORE:
        old = icon_on_button(fn(), 104, fill=96 / 104)
        new = icon_on_button(Image.open(os.path.join(ICONS, f)).convert("RGBA"), 104, fill=96 / 104, sel=True)
        t.paste(old, (x, 84))
        t.paste(new, (x + 112, 84))
        d.text((x, 62), lab, font=font(11), fill=TEXT)
        d.text((x + 36, 194), "1.x", font=font(11), fill=DIM)
        d.text((x + 112 + 34, 194), "2.0", font=font(11, True), fill=(0, 183, 255))
        x += 250
    blocks.append(t)
    H = sum(b.height for b in blocks) + 10
    sheet = Image.new("RGBA", (W, H), BG + (255,))
    y = 0
    for b in blocks:
        sheet.paste(b, (0, y))
        y += b.height
    sheet.convert("RGB").save(out, optimize=True)
    print(out, sheet.size)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "todas"
    if what not in ("itens", "icones", "todas"):
        sys.exit("uso: _bs2_itens_previews.py [itens|icones|todas]")
    if what in ("itens", "todas"):
        build_itens()
    if what in ("icones", "todas"):
        build_icones()
