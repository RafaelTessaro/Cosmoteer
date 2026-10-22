"""Previas e conferencia de arte do grupo "fabricas" da 2.0 (F1-F6), versionadas no repo (so le PNGs; sem bpy):

    python3 tools/blender/parts/_bs2_fabricas_previews.py [folha|gif|check|todas] [--src DIR] [--out DIR]
            [--fac F1,F4] [--itens DIR] [--blender PY] [--spec SPEC_2.0.json] [--conf DIR]

  folha -> docs/preview/3d/v2/fabricas_2_0.png: as 6 fabricas a 1x nos dois cascos e, por fabrica, o interior
           trabalhando, o teto pintado (como no jogo), a fabrica a 1x no casco escuro/espaco e no branco, as placas
           de modo ao lado da saida do mesmo tipo, os produtos (icone do recurso 2.0 + o desenho de dentro da
           maquina) e a tira com todos os quadros da maquina a 1x;
  gif   -> docs/preview/3d/v2/fabricas_2_0.gif: as maquinas trabalhando (zoom 2x) num laco de 6 s em que cada uma
           fecha voltas inteiras. Os instantes de troca sao quantizados em 20 ms (GIF_STEP): Chrome, Firefox e
           Safari tratam atraso <= 10 ms como 100 ms, o que travava o laco. O GIF e conferido na volta (atraso
           minimo, laco total, voltas inteiras por painel, erro de cor da paleta por quadro);
  check -> conferencia de arte das pastas F1-F6 (meta e arquivos, tamanhos, alfa das normais, bases de
           entrada/saida livres de maquinario, area acesa, maior regiao plana clara, pintura do teto, camadas extras,
           encaixe da placa). Com --spec confere tambem id/tamanho/quadros/intervalo/grades contra o SPEC_2.0.json;
  todas -> as tres (padrao).

  --src DIR   pasta com as pastas das fabricas (padrao art3d/); aceita rascunhos com subpastas f1..f6.
  --itens DIR render de _bs2_fabricas_itens.py (os produtos "na maquina"). Sem ele, o modulo renderiza numa pasta
              temporaria se tiver o Python do Blender (--blender <venv>/bin/python ou a variavel BS_BLENDER_PY);
              sem Blender, a folha mostra so os icones dos recursos.
  --conf DIR  grava ali as imagens de conferencia (quadro 1 do GIF ao lado do RGB de origem).
Modulo do grupo "fabricas" (regra dos arquivos compartilhados: nao edita compose_*.py, so importa compose_preview).
"""
import bisect
import json
import os
import subprocess
import sys
import tempfile
from collections import deque

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))                 # tools/blender/parts
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))    # raiz do repo
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))
import compose_preview as CP  # noqa: E402

ART = os.path.join(ROOT, "art3d")
PLACAS = os.path.join(ART, "bs_placas")
OUT_DIR = os.path.join(ROOT, "docs", "preview", "3d", "v2")
PX = 64
BG = (7, 9, 14)
SPACE = (10, 12, 18)
PAINT = (46, 58, 74)
WHITE_HULL = (232, 234, 238)
GOLD = (255, 196, 70)
TEXT = (220, 226, 236)
DIM = (150, 160, 176)
GIF_STEP = 20          # ms: menor atraso do GIF (os navegadores tratam <= 10 ms como 100 ms)
GIF_LOOP_S = 6.0

# mesma ordem de _bs2_fabricas_itens.ITEMS (aquele modulo importa o bpy; este nao)
ITEMS = ["he", "ap", "sap", "ac", "frag", "plasma", "pem", "msl_he", "msl_cluster", "msl_emp", "nuke", "slug"]
ITEM_NAMES = {"he": "Carregador HE", "ap": "Carregador AP", "sap": "Carregador SAP", "ac": "Carregador AC",
              "frag": "Carregador FRAG", "plasma": "Célula de Plasma", "pem": "Célula PEM",
              "msl_he": "Carga de Míssil HE", "msl_cluster": "Carga de Submunição", "msl_emp": "Carga de Míssil PEM",
              "nuke": "Ogiva Nuclear", "slug": "Projétil da Tupã"}
ITEM_FOLDER = {"he": "bs_mag_std", "ap": "bs_mag_ap", "sap": "bs_mag_sap", "ac": "bs_mag_ac", "frag": "bs_mag_frag",
               "plasma": "bs_plasma_cell", "pem": "bs_cell_emp", "msl_he": "bs_msl_he",
               "msl_cluster": "bs_msl_cluster", "msl_emp": "bs_msl_emp", "nuke": "bs_msl_nuke",
               "slug": "bs_slug_rail"}

FACT = [
    {"code": "F1", "short": "bs_factory_mag_std", "draft": "f1", "name": "Prensa HE",
     "io": "enxofre → Carregador HE", "anim": "10 quadros × 0,125 s = 1,25 s = 1 carregador por volta",
     "items": ["he"], "plate": None,
     "what": "tremonha de enxofre (pás girando) → rosca alimentadora → matriz de fundição; o martelo prensa e o "
             "Carregador HE sai em brasa pela boca de saída; no teto, tudo no esquadro da família: tampa octogonal "
             "com a fenda reta de nível, torre da prensa e a placa de ligação chanfrada com a fenda de LEDs"},
    {"code": "F2", "short": "bs_factory_special", "draft": "f2", "name": "Fábrica de Munição Especial",
     "io": "enxofre + triaço → AP / SAP / AC / FRAG (uma base de saída por munição)",
     "anim": "10 quadros × 0,1 s", "items": ["ap", "sap", "ac", "frag"],
     "plate": {"modes": ["ap", "sap", "ac", "frag"], "c": [2.0, 0.5], "size": 0.8},
     "what": "mesa indexadora + prensa de conformar (da Prensa AP 1.x), misturador de enxofre, forja de pontas de "
             "triaço, porta-ferramentas com as 4 matrizes; a cor de cada saída fica numa pastilha com soquete escuro "
             "(teto e piso, lê nos dois cascos); teto com a coroa da prensa, a placa de modo e o colar octogonal de "
             "8 segmentos retos entre frestas escuras e respiros"},
    {"code": "F3", "short": "bs_factory_plasma", "draft": "f3", "name": "Fábrica de Células",
     "io": "enxofre + bobina → Célula de Plasma · cobre → Célula PEM",
     "anim": "12 quadros × 0,12 s", "items": ["plasma", "pem"],
     "plate": {"modes": ["plasma", "pem"], "c": [0.5, 0.5], "size": 0.8}, "bank": True,
     "what": "tanques de plasma, anel de confinamento (o toro da 1.x), banco de bobinas de cobre, berço com alçapão; "
             "grade de cobre na base do meio; saídas com pastilha ciano (plasma) e cobre (PEM, como a placa_pem) em "
             "soquete escuro; no modo plasma a tampa do banco fica fechada no teto, no modo PEM o banco de bobinas "
             "aparece por cima dela. * A luz do banco (lights_add) é CONDICIONAL: na ordem de camadas do spec ela "
             "fica sob o teto; se o jogo não a mostrar sobre o banco, a ligação a põe em roof_lights_fancy"},
    {"code": "F4", "short": "bs_factory_missile", "draft": "f4", "name": "Fábrica de Mísseis",
     "io": "ferro + enxofre → cargas HE / submunição / PEM", "anim": "12 quadros × 0,1 s",
     "items": ["msl_he", "msl_cluster", "msl_emp"],
     "plate": {"modes": ["msl_he", "msl_cluster", "msl_emp"], "c": [1.5, 0.5], "size": 0.8}, "hue_check": True,
     "what": "laminador de corpos, enchedora de ogivas, pórtico com lança que encaixa a ogiva no corpo, berço de "
             "acabamento; o código de cor das saídas é o MESMO das placas de modo: HE âmbar, submunição laranja, PEM "
             "azul, em 3 lugares por saída (pastilha no soquete escuro, os 3 LEDs da escotilha e a seta do piso); os "
             "LEDs amarelos genéricos ficam só nas entradas e no maquinário; a célula da máquina [1,1] tem tampa "
             "octogonal com fenda simétrica, sem seta"},
    {"code": "F5", "short": "bs_factory_warhead", "draft": "f5", "name": "Fábrica de Ogivas Nucleares",
     "io": "ferro + urânio → Ogiva Nuclear", "anim": "12 quadros × 0,125 s = 1,5 s (2 voltas por ogiva de 3,0 s)",
     "items": ["nuke"], "plate": None,
     "what": "célula quente com vidro de chumbo e 2 manipuladores, torno de carcaças (poço grafite com trilhos e "
             "frestas verdes), cascata de centrífugas, eclusa e berço de saída; a saída é a fileira de baixo inteira "
             "(seta nas 4 bases); teto: aba externa pintada com frestas, escudo claro com visor e o trevo grande "
             "embutido num recesso escuro"},
    {"code": "F6", "short": "bs_factory_slug", "draft": "f6", "name": "Forja de Projéteis",
     "io": "triaço + hiperbobina → Projétil da Tupã", "anim": "12 quadros × 0,25 s = 3,0 s = 1 projétil por volta",
     "items": ["slug"], "plate": None,
     "what": "trefila de hastes e bobinadeira em poços grafite com trilhos e frestas azuis, forno de indução "
             "(colares com frestas azuis), prensa de armadura com molas laranja-ouro; paleta azul + laranja da Tupã nova "
             "(referência do usuário); a saída é a fileira de baixo inteira (seta nas 3 bases); teto: tampas das "
             "colunas com a coroa sextavada do acionamento e o capuz do berço na célula [1,2] (máquina, sem seta)"},
]
_F = {}


def font(sz, bold=False):
    k = (sz, bold)
    if k not in _F:
        for p in ("/usr/share/fonts/opentype/inter/" + ("Inter-Bold.otf" if bold else "Inter-Medium.otf"),
                  "/usr/share/fonts/truetype/dejavu/" + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")):
            if os.path.exists(p):
                _F[k] = ImageFont.truetype(p, sz)
                break
        else:
            _F[k] = ImageFont.load_default()
    return _F[k]


def fdir(f, src):
    d = os.path.join(src, f["short"])
    return d if os.path.isdir(d) else os.path.join(src, f["draft"])


def load(d, n):
    return Image.open(os.path.join(d, n)).convert("RGBA")


def meta(d):
    return json.load(open(os.path.join(d, "meta.json")))


def up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def add_light(base, light):
    """lights_add: soma (cor x alfa) por cima."""
    a = light.getchannel("A")
    glow = Image.composite(light, Image.new("RGBA", base.size, (0, 0, 0, 255)), a).convert("RGB")
    return ImageChops.add(base.convert("RGB"), glow).convert("RGBA")


def interior(d, m, frame):
    base = Image.new("RGBA", load(d, m["hull"]["floor"]).size, (18, 19, 21, 255))
    base.alpha_composite(load(d, m["hull"]["floor"]))
    base.alpha_composite(load(d, frame))
    base.alpha_composite(load(d, m["hull"]["walls"]))
    return add_light(base, load(d, m["hull"]["lights"]))


def plate_img(mode, size_tiles):
    im = Image.open(os.path.join(PLACAS, f"placa_{mode}.png")).convert("RGBA")
    px = int(round(size_tiles * PX))
    return im.resize((px, px), Image.LANCZOS)


def roof(d, m, f, paint=PAINT, mode=None, pem=False, luz=None):
    """Teto como no jogo: verde trocado pela pintura, placa de modo (roof_doodads) e, na F3 em modo PEM, o banco de
    bobinas (roof_doodads) + a luz dele (lights_add, condicional: ver a nota da F3)."""
    im = CP.paint_roof(load(d, m["hull"]["roof"]), paint)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(im)
    pl = f.get("plate")
    if pl:
        pi = plate_img(mode or pl["modes"][0], pl["size"])
        cx, cy = pl["c"][0] * PX, pl["c"][1] * PX
        out.alpha_composite(pi, (int(round(cx - pi.width / 2)), int(round(cy - pi.height / 2))))
    if pem and "banco_pem" in m.get("overlays", {}):
        ov = m["overlays"]["banco_pem"]
        x, y = int(round(ov["rect"][0] * PX)), int(round(ov["rect"][1] * PX))
        out.alpha_composite(load(d, ov["files"][0]), (x, y))
        if luz is not None:
            li = load(d, m["overlays"]["banco_pem_luz"]["files"][luz % 4]).convert("RGB")
            sub = out.crop((x, y, x + li.width, y + li.height))
            a = sub.getchannel("A")
            sub2 = ImageChops.add(sub.convert("RGB"), li).convert("RGBA")
            sub2.putalpha(a)
            out.paste(sub2, (x, y))
    return out


def hull_field(w, h, paint):
    """Casco da nave em volta da peca: placas de 1 quadro na cor da pintura com juntas finas."""
    im = Image.new("RGBA", (w, h), tuple(paint) + (255,))
    dr = ImageDraw.Draw(im)
    dark = tuple(int(c * 0.80) for c in paint) + (255,)
    lite = tuple(min(255, int(c * 1.05 + 6)) for c in paint) + (255,)
    for x in range(0, w, PX):
        dr.line([(x, 0), (x, h)], fill=dark)
        dr.line([(x + 1, 0), (x + 1, h)], fill=lite)
    for y in range(0, h, PX):
        dr.line([(0, y), (w, y)], fill=dark)
        dr.line([(0, y + 1), (w, y + 1)], fill=lite)
    return im


def in_ship(d, m, f, paint, space=False, mode=None, pem=False):
    """A fabrica a 1x no meio de um casco pintado; space=True: a peca na borda da nave, com o espaco em volta."""
    W, H = m["size"]
    r = roof(d, m, f, paint, mode=mode, pem=pem)
    if space:
        cv = Image.new("RGBA", ((W + 2) * PX, (H + 2) * PX), SPACE + (255,))
        stars = np.random.RandomState(3).rand(cv.height, cv.width) > 0.996
        a = np.asarray(cv).copy()
        a[stars] = (150, 160, 180, 255)
        cv = Image.fromarray(a, "RGBA")
        cv.alpha_composite(hull_field((W + 2) * PX, (H + 1) * PX, paint), (0, PX))
    else:
        cv = hull_field((W + 2) * PX, (H + 2) * PX, paint)
    cv.alpha_composite(r, (PX, PX))
    return cv


# ============================================================================ produtos
def items_dir(itens=None, blender=None):
    """Pasta com o render de _bs2_fabricas_itens.py (machine_on1.png, 12 x 1 quadros); renderiza numa pasta
    temporaria se precisar e houver o Python do Blender. None = sem os desenhos "na maquina"."""
    if itens and os.path.exists(os.path.join(itens, "machine_on1.png")):
        return itens
    d = itens or os.path.join(tempfile.gettempdir(), "bs2_fabricas_itens")
    if os.path.exists(os.path.join(d, "machine_on1.png")) and not blender:
        return d
    py = blender or os.environ.get("BS_BLENDER_PY")
    if not py:
        print("AVISO: sem --itens nem --blender/BS_BLENDER_PY: a folha sai so com os icones dos recursos")
        return None
    os.makedirs(d, exist_ok=True)
    cmd = [py, os.path.join(ROOT, "tools", "blender", "render_part.py"), os.path.join(HERE, "_bs2_fabricas_itens.py"),
           "--out", d]
    print("render dos produtos:", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    return d


def items_strip(d):
    """Os produtos como aparecem dentro das maquinas, 1 por quadro de 64 px (ordem ITEMS)."""
    if d is None:
        return {}
    im = Image.open(os.path.join(d, "machine_on1.png")).convert("RGBA")
    if im.width != len(ITEMS) * PX:
        raise SystemExit(f"{d}/machine_on1.png tem {im.width} px; esperado {len(ITEMS)} x {PX}")
    return {k: im.crop((i * PX, 0, (i + 1) * PX, PX)) for i, k in enumerate(ITEMS)}


def resource_icon(kind):
    p = os.path.join(ART, ITEM_FOLDER[kind], "icon.png")
    return Image.open(p).convert("RGBA") if os.path.exists(p) else None


# ============================================================================ folha
def anim_strip(d, m, maxw=2250):
    """Tira com TODOS os quadros da maquina a 1x (recorte do maquinario), numerados, em ordem."""
    names = m["machine"]["frames"]
    al = None
    for n in names:
        a = np.asarray(load(d, n))[..., 3] > 8
        al = a if al is None else (al | a)
    ys, xs = np.nonzero(al)
    Wp, Hp = al.shape[1], al.shape[0]
    box = (max(0, xs.min() - 4), max(0, ys.min() - 4), min(Wp, xs.max() + 5), min(Hp, ys.max() + 5))
    crops = [interior(d, m, n).crop(box) for n in names]
    cw, ch = crops[0].size
    per = max(1, (maxw + 6) // (cw + 6))
    nr = (len(crops) + per - 1) // per
    img = Image.new("RGBA", (min(len(crops), per) * (cw + 6) - 6, nr * (ch + 18)), BG + (255,))
    dr = ImageDraw.Draw(img)
    for i, c in enumerate(crops):
        x, y = (i % per) * (cw + 6), (i // per) * (ch + 18)
        dr.text((x + 2, y), str(i + 1), font=font(12, True), fill=GOLD)
        img.alpha_composite(c, (x, y + 16))
    return img


def plate_vs_output(d, m, f):
    """Para cada modo: a placa de modo no teto e, ao lado, a escotilha da saida do MESMO tipo (zoom 2x). Mostra
    que a placa e a pastilha/LEDs da saida usam o mesmo codigo de cor."""
    outs = m.get("grid", {}).get("outputs", {})
    tiles = []
    for md in f["plate"]["modes"]:
        r = roof(d, m, f, mode=md)
        cx, cy = f["plate"]["c"][0] * PX, f["plate"]["c"][1] * PX
        pc = up(r.crop((int(cx - 40), int(cy - 40), int(cx + 40), int(cy + 40))), 2)
        tile = Image.new("RGBA", (pc.width + 8 + 2 * PX, pc.height), BG + (255,))
        tile.alpha_composite(pc, (0, 0))
        if md in outs:
            i, j = outs[md][:2]
            oc = up(r.crop((i * PX, j * PX, (i + 1) * PX, (j + 1) * PX)), 2)
            tile.alpha_composite(oc, (pc.width + 8, (pc.height - oc.height) // 2))
        tiles.append(tile)
    wsum = sum(t.width for t in tiles) + 14 * (len(tiles) - 1)
    strip = Image.new("RGBA", (wsum, tiles[0].height), BG + (255,))
    x = 0
    for t in tiles:
        strip.alpha_composite(t, (x, 0))
        x += t.width + 14
    return strip


def block(f, src, its):
    d = fdir(f, src)
    m = meta(d)
    W, H = m["size"]
    fr = m["machine"]["frames"]
    work = interior(d, m, fr[min(len(fr) - 1, len(fr) // 2 - 1)])
    k = 2
    f_t, f_s, f_c = font(26, True), font(16), font(15)
    pieces = [(up(work, k), "interior trabalhando · zoom 2x")]
    if f.get("bank"):
        pieces.append((up(roof(d, m, f), k), "teto, modo plasma · zoom 2x"))
        pieces.append((up(roof(d, m, f, mode="pem", pem=True, luz=1), k),
                       "teto, modo PEM (banco; luz condicional*) · zoom 2x"))
    else:
        pieces.append((up(roof(d, m, f), k), "teto pintado (como no jogo) · zoom 2x"))
    pieces.append((in_ship(d, m, f, PAINT, space=True), "1x · casco escuro / espaço"))
    pieces.append((in_ship(d, m, f, WHITE_HULL), "1x · casco branco"))
    if f.get("plate"):
        pieces.append((plate_vs_output(d, m, f), "placa de modo (bs_placas) e a saída do mesmo tipo, no teto · zoom 2x"))
    # produto: o icone do recurso 2.0 e, menor ao lado, o desenho que aparece dentro da maquina (o mesmo produto)
    cw, mw = 136, 72
    prod = Image.new("RGBA", (len(f["items"]) * (cw + mw + 18), cw + 40), BG + (255,))
    dp = ImageDraw.Draw(prod)
    for i, kd in enumerate(f["items"]):
        x = i * (cw + mw + 18)
        ic = resource_icon(kd)
        dp.rectangle([x, 0, x + cw - 1, cw - 1], fill=(40, 44, 52, 255))
        if ic is not None:
            im = up(ic, 2)
            prod.alpha_composite(im, (x + (cw - im.width) // 2, (cw - im.height) // 2))
        if kd in its:
            mi = its[kd].resize((mw, mw), Image.LANCZOS)
            dp.rectangle([x + cw + 4, cw - mw, x + cw + 4 + mw - 1, cw - 1], fill=(30, 33, 40, 255))
            prod.alpha_composite(mi, (x + cw + 4, cw - mw))
        dp.text((x, cw + 4), ITEM_NAMES[kd], font=f_c, fill=TEXT)
        dp.text((x, cw + 22), "recurso 2.0 · na máquina →" if kd in its else "recurso 2.0", font=font(12), fill=DIM)
    pieces.append((prod, "produto(s)"))
    iv = f"{m['machine']['interval']:.3g}".replace(".", ",")
    pieces.append((anim_strip(d, m), f"tira da animação: os {len(fr)} quadros da máquina a 1x (escala real), "
                                     f"{iv} s cada, em ordem"))
    MAXW = 2300
    rows, cur, w = [], [], 0
    for im, cap in pieces:
        if cur and w + im.width + 24 > MAXW:
            rows.append(cur)
            cur, w = [], 0
        cur.append((im, cap))
        w += im.width + 24
    rows.append(cur)
    f_w = font(13)
    meas = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    title, sub = f"{f['code']} · {f['name']} · {W}×{H}", f"{f['io']} · {f['anim']}"
    rh = [max(im.height for im, _ in r) + 30 for r in rows]
    # largura do bloco: a das figuras (e da legenda de cada uma) e a dos textos do cabecalho
    Wb = max(sum(max(im.width, int(meas.textlength(cap, font=f_c))) + 24 for im, cap in r) for r in rows) + 24
    Wb = max(Wb, int(meas.textlength(title, font=f_t)) + 48, int(meas.textlength(sub, font=f_s)) + 48)
    # descricao quebrada na largura REAL do bloco (com 1500 fixo a legenda da F1, bloco de ~1260 px, saia cortada)
    wrap = min(1500, Wb - 48)
    lines, cur_ = [], ""
    for w_ in f["what"].split():
        t_ = (cur_ + " " + w_).strip()
        if cur_ and meas.textlength(t_, font=f_w) > wrap:
            lines.append(cur_)
            cur_ = w_
        else:
            cur_ = t_
    lines.append(cur_)
    head_h = 66 + 17 * len(lines)
    img = Image.new("RGBA", (Wb, head_h + sum(rh) + 10), BG + (255,))
    dr = ImageDraw.Draw(img)
    dr.text((24, 6), title, font=f_t, fill=GOLD)
    dr.text((24, 38), sub, font=f_s, fill=TEXT)
    y = head_h
    for r, h_ in zip(rows, rh):
        x = 24
        base = y + h_ - 30
        for im, cap in r:
            img.alpha_composite(im, (x, base - im.height))
            dr.text((x, base + 6), cap, font=f_c, fill=DIM)
            x += im.width + 24
        y += h_
    for i_, ln in enumerate(lines):
        dr.text((24, 62 + 17 * i_), ln, font=f_w, fill=DIM)
    return img


def overview(src, facs, paint, k=1):
    """As fabricas lado a lado num casco a 1x (teto pintado), alinhadas pela base, com o codigo embaixo."""
    ims = []
    for f in FACT:
        if f["code"] in facs:
            d = fdir(f, src)
            # F3 com o banco PEM no teto: a placa tem de ser a PEM (sem mode caia em modes[0] = plasma: banco PEM com
            # placa de plasma, defeito da folha apontado na revisao das fabricas r2)
            bank = bool(f.get("bank"))
            ims.append((f, up(roof(d, meta(d), f, paint, mode="pem" if bank else None, pem=bank), k)))
    gap = PX * k
    W = sum(im.width for _, im in ims) + gap * (len(ims) + 1)
    H = max(im.height for _, im in ims) + 2 * gap
    cv = hull_field(W, H, paint)
    dr = ImageDraw.Draw(cv)
    x = gap
    fnt = font(13, True)
    for f, im in ims:
        cv.alpha_composite(im, (x, H - gap - im.height))
        tw = dr.textlength(f["code"], font=fnt)
        dr.text((x + (im.width - tw) / 2, H - gap + 18), f["code"], font=fnt,
                fill=(20, 22, 26) if sum(paint) > 450 else TEXT)
        x += im.width + gap
    return cv


def sheet(src, out, facs, its):
    blocks = [block(f, src, its) for f in FACT if f["code"] in facs]
    ov_d, ov_w = overview(src, facs, PAINT), overview(src, facs, WHITE_HULL)
    ovb = Image.new("RGBA", (24 + max(ov_d.width, ov_w.width) + 24, ov_d.height + ov_w.height + 70), BG + (255,))
    ovb.alpha_composite(ov_d, (24, 0))
    ovb.alpha_composite(ov_w, (24, ov_d.height + 34))
    d_ = ImageDraw.Draw(ovb)
    d_.text((24, ov_d.height + 6), "as 6 fábricas a 1x (escala real) no casco escuro — teto pintado, placa no modo "
            "padrão, F3 no modo PEM (placa PEM + banco de bobinas no teto)", font=font(15), fill=DIM)
    d_.text((24, ov_d.height + 34 + ov_w.height + 6), "as mesmas no casco branco", font=font(15), fill=DIM)
    blocks.insert(0, ovb)
    W = max(b.width for b in blocks)
    title_h = 130
    sh = Image.new("RGB", (W, title_h + sum(b.height + 16 for b in blocks)), BG)
    dr = ImageDraw.Draw(sh)
    dr.text((24, 14), "Fábricas 2.0 — F1 a F6", font=font(34, True), fill=TEXT)
    lines = ["Interior = a fábrica trabalhando com o teto escondido (modo interior do jogo); teto = como a nave mostra, "
             "o verde do teto vira a cor da pintura. As bases de entrada (seta para cima) e de saída (seta para baixo) "
             "ficam livres: o jogo desenha as pilhas ali e a tripulação chega em todas.",
             "Escala real = 64 px por quadro (1x); zoom 2x = cada pixel do jogo vira 2×2. Placas de modo = "
             "art3d/bs_placas (pacote logística), desenhadas por cima do encaixe do teto. Produtos: ícone do recurso 2.0 "
             "(pacote munições) e, ao lado, o mesmo produto como aparece dentro da máquina.",
             "Saídas com seletor: a cor de cada tipo fica numa pastilha com soquete escuro (teto e piso) e segue o "
             "código das placas de modo (F4: HE âmbar, submunição laranja, PEM azul)."]
    for i, s in enumerate(lines):
        dr.text((24, 58 + i * 20), s, font=font(14), fill=DIM)
    y = title_h
    for b in blocks:
        sh.paste(b.convert("RGB"), (0, y))
        y += b.height + 16
    sh.save(out)
    print(out, sh.size)


# ============================================================================ GIF
RESERVED = [(0, 0, 0), BG, GOLD, TEXT, DIM]


def _pack(a):
    a = a.astype(np.uint32)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


def _mediancut(px, n):
    if n <= 0 or len(px) == 0:
        return []
    im = Image.fromarray(np.ascontiguousarray(px.reshape(-1, 1, 3)), "RGB")
    q = im.quantize(colors=min(n, 256), method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:3 * n]
    used = sorted(set(np.asarray(q).ravel().tolist()))
    return [tuple(pal[3 * i:3 * i + 3]) for i in used]


def _hue(px):
    p = px.astype(np.float32)
    r, g, b = p[:, 0], p[:, 1], p[:, 2]
    mx, mn = p.max(1), p.min(1)
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4))
    return (h * 60.0) % 360.0


def _kmeans(u, w, P, fixed, it=3):
    """Lloyd ponderado (w = raiz da contagem) sobre as cores distintas u; as cores fixas nao se movem."""
    P = P.astype(np.float64)
    for _ in range(it):
        lab = np.empty(len(u), np.int32)
        for k in range(0, len(u), 8192):
            lab[k:k + 8192] = ((u[k:k + 8192, None, :] - P[None, :, :]) ** 2).sum(2).argmin(1)
        sw = np.bincount(lab, weights=w, minlength=len(P))
        for c in range(3):
            m = np.bincount(lab, weights=w * u[:, c], minlength=len(P))
            upd = (sw > 0) & ~fixed
            P[upd, c] = m[upd] / sw[upd]
    return np.clip(np.round(P), 0, 255).astype(int)


def build_palette(px, n=255):
    """Paleta de ate n cores: sem perda se houver <= n cores distintas; senao cores fixas + MEDIANCUT dos saturados
    por faixa de matiz de 30 graus (o verde dos LEDs, o azul, o ciano e o ambar nao somem) + MEDIANCUT dos neutros,
    e 3 passos de k-means ponderado."""
    pk = _pack(px)
    uq, cnt = np.unique(pk, return_counts=True)
    if len(uq) <= n:
        return [((int(c) >> 16) & 255, (int(c) >> 8) & 255, int(c) & 255) for c in uq]
    pres = set(uq.tolist())
    res = [c for c in RESERVED if ((c[0] << 16) | (c[1] << 8) | c[2]) in pres]
    sat = (px.max(1).astype(int) - px.min(1).astype(int)) >= 36
    left = n - len(res)
    pal = list(res)
    if sat.any():
        nsat = int(np.clip(round(left * max(sat.mean() * 3.0, 0.35)), 32, int(left * 0.6)))
        sp = px[sat]
        sec = (_hue(sp) // 30).astype(int)
        secs = [q for q in range(12) if (sec == q).any()]
        wq = np.array([np.sqrt((sec == q).sum()) for q in secs])
        uqn = [len(np.unique(_pack(sp[sec == q]))) for q in secs]
        alloc = [max(min(4, un), int(round(nsat * wv / wq.sum()))) for wv, un in zip(wq, uqn)]
        alloc = [min(a, un) for a, un in zip(alloc, uqn)]
        while sum(alloc) > nsat:
            alloc[int(np.argmax(alloc))] -= 1
        for q, a in zip(secs, alloc):
            pal += _mediancut(sp[sec == q], a)
    pal += _mediancut(px[~sat], n - len(pal))
    out, seen = [], set()
    for c in pal:
        if c not in seen:
            seen.add(c)
            out.append(c)
    out = out[:n]
    u = np.stack([(uq >> 16) & 255, (uq >> 8) & 255, uq & 255], 1).astype(np.float64)
    fixed = np.array([c in res for c in out])
    P = _kmeans(u, np.sqrt(cnt.astype(np.float64)), np.asarray(out, np.float64), fixed)
    final, seen = [], set()
    for c in map(tuple, P.tolist()):
        if c not in seen:
            seen.add(c)
            final.append(c)
    return final


def nearest(px, pal):
    u, inv = np.unique(_pack(px), return_inverse=True)
    uc = np.stack([(u >> 16) & 255, (u >> 8) & 255, u & 255], 1).astype(np.int32)
    P = np.asarray(pal, np.int32)
    idx = np.empty(len(uc), np.uint8)
    for k in range(0, len(uc), 8192):
        idx[k:k + 8192] = ((uc[k:k + 8192, None, :] - P[None, :, :]) ** 2).sum(2).argmin(1)
    return idx[inv.ravel()]


def save_gif_perframe(frames, durs, path, tol=6):
    """GIF com PALETA POR QUADRO e quadros delta: o quadro 1 tem paleta da imagem inteira; cada quadro seguinte so
    grava os pixels que diferem mais que tol do que o leitor ja mostra (o resto e o indice transparente 255,
    disposal 1) com 255 cores tiradas so desses pixels. O indice 255 nunca e uma cor."""
    out, palettes = [], []
    disp = None
    for f in frames:
        a = np.asarray(f.convert("RGB"))
        if disp is None:
            ch = np.ones(a.shape[:2], bool)
            disp = np.zeros(a.shape, np.int32)
        else:
            ch = np.abs(a.astype(np.int32) - disp).max(2) > tol
        if not ch.any():
            ch[0, 0] = True
        px = a[ch]
        pal = build_palette(px, 255)
        idx = nearest(px, pal)
        b = np.full(a.shape[:2], 255, np.uint8)
        b[ch] = idx
        disp[ch] = np.asarray(pal, np.int32)[idx]
        im = Image.fromarray(b, "P")
        flat = [v for c in pal for v in c] + [255, 0, 255] * (256 - len(pal))
        im.putpalette(flat[:768])
        im.info["transparency"] = 255
        out.append(im)
        palettes.append(pal)
    out[0].save(path, save_all=True, append_images=out[1:], duration=durs, loop=0, optimize=False, disposal=1,
                transparency=255)
    return palettes


def qms(ms):
    """Instante em ms -> grade de GIF_STEP ms (meio para cima)."""
    return int(ms / GIF_STEP + 0.5) * GIF_STEP


def timeline(panels, T=GIF_LOOP_S):
    """panels: [(n_quadros, intervalo_s)]. Cada painel da um numero INTEIRO de voltas c no laco de T s (intervalo
    efetivo T / (c x n)); o inicio de cada quadro de cada painel cai na grade de GIF_STEP ms, entao duas trocas
    nunca ficam a menos de GIF_STEP ms. Devolve (instantes de troca, duracoes, inicios por painel, (c, e) por
    painel)."""
    Tms = int(round(T * 1000))
    if Tms % GIF_STEP:
        raise SystemExit(f"laco de {Tms} ms nao e multiplo de {GIF_STEP} ms")
    starts, cyc = [], []
    for n, iv in panels:
        c = max(1, int(round(T / (n * iv))))
        e = Tms / (c * n)
        starts.append([qms(k * e) for k in range(c * n)])
        cyc.append((c, e))
    ts = sorted({t for st in starts for t in st if t < Tms})
    durs = [b - a for a, b in zip(ts, ts[1:] + [Tms])]
    return ts, durs, starts, cyc


def frame_at(starts, t, n):
    """Quadro do painel (de n quadros) que o GIF mostra no instante t (ms)."""
    return (bisect.bisect_right(starts, t) - 1) % n


def timeline_check(ts, durs, starts, cyc, panels, T=GIF_LOOP_S):
    """Conferencia do laco ANTES de gravar: atraso minimo >= GIF_STEP, soma = T, cada painel com c x n inicios
    distintos e crescentes dentro do laco (voltas inteiras)."""
    Tms = int(round(T * 1000))
    errs = []
    if min(durs) < GIF_STEP:
        errs.append(f"atraso minimo {min(durs)} ms < {GIF_STEP} ms")
    if sum(durs) != Tms:
        errs.append(f"laco {sum(durs)} ms != {Tms} ms")
    for p, (st, (c, e), (n, iv)) in enumerate(zip(starts, cyc, panels)):
        if len(st) != c * n or any(b <= a for a, b in zip(st, st[1:])) or st[-1] >= Tms:
            errs.append(f"painel {p}: inicios fora de ordem/fora do laco")
        if any(t not in set(ts) for t in st):
            errs.append(f"painel {p}: troca fora da linha do tempo")
    return errs


def gif_readback(path, frames, palettes):
    """Le o GIF de volta: atrasos (minimo, soma), quadros compostos x quadros RGB de origem, cores do quadro 1."""
    g = Image.open(path)
    durs, errs = [], []
    for k in range(g.n_frames):
        g.seek(k)
        durs.append(int(g.info.get("duration", 0)))
        f = frames[min(k, len(frames) - 1)]
        d = np.abs(np.asarray(g.convert("RGB")).astype(int) - np.asarray(f.convert("RGB")).astype(int)).max(2)
        errs.append((d.mean(), (d > 24).mean(), d.max()))
    P = np.asarray(palettes[0], int)
    r, gg, b = P[:, 0], P[:, 1], P[:, 2]
    hues = {"verde": int(((gg > r + 60) & (gg > b + 60)).sum()), "azul": int(((b > r + 80) & (b > gg + 30)).sum()),
            "ciano": int(((gg > 150) & (b > 150) & (r < 130)).sum()), "preto": int(((P.max(1)) == 0).sum()),
            "ambar/laranja": int(((r > 200) & (gg > 60) & (gg < 200) & (b < 90)).sum())}
    e = np.asarray(errs)
    return {"quadros_gif": g.n_frames, "quadros_origem": len(frames), "atraso_min_ms": min(durs),
            "atraso_max_ms": max(durs), "laco_ms": sum(durs), "atrasos_abaixo_de_20ms": sum(d < GIF_STEP for d in durs),
            "erro_medio": round(float(e[:, 0].mean()), 3), "px_erro_maior_24": f"{e[:, 1].max():.4%}",
            "erro_max": int(e[:, 2].max()), "paleta_quadro0": {"cores": len(P), **hues}}


def _fit_font(dr, text, maxw, size, bold=False, minsize=10):
    while size > minsize and dr.textlength(text, font=font(size, bold)) > maxw:
        size -= 1
    return font(size, bold)


def gif(src, out, facs, k=2, conf=None):
    fs = [f for f in FACT if f["code"] in facs]
    data = []
    for f in fs:
        d = fdir(f, src)
        m = meta(d)
        data.append((f, m, [up(interior(d, m, n), k) for n in m["machine"]["frames"]]))
    # painel extra: o teto da F3 no modo PEM com o banco de bobinas piscando (banco_pem_luz1..4, 0,1 s)
    f3 = [x for x in data if x[0]["code"] == "F3"]
    if f3:
        f, m, _ = f3[0]
        d = fdir(f, src)
        lz = [up(roof(d, m, f, mode="pem", pem=True, luz=j), k) for j in range(4)]
        data.insert(data.index(f3[0]) + 1, ({"code": "F3", "name": "teto no modo PEM",
                                             "sub": "banco de bobinas · luz condicional*"},
                                            {"machine": {"interval": 0.1}}, lz))
    panels = [(len(fr), m["machine"]["interval"]) for _, m, fr in data]
    ts, durs, starts, cyc = timeline(panels)
    bad = timeline_check(ts, durs, starts, cyc, panels)
    if bad:
        raise SystemExit("linha do tempo do GIF: " + "; ".join(bad))
    rows = [data[:4], data[4:]] if len(data) > 4 else [data]
    lab_h, gap, head = 44, 18, 112
    rw = [sum(fr[0].width for _, _, fr in r) + gap * (len(r) + 1) for r in rows]
    rh = [max(fr[0].height for _, _, fr in r) + lab_h for r in rows]
    W = max(rw)
    H = head + sum(rh) + gap * len(rows)
    base = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(base)
    dr.text((gap, 10), "Fábricas 2.0 trabalhando (interior com o teto escondido, zoom 2x, cada uma no seu ritmo)",
            font=font(24, True), fill=TEXT)
    for i, s in enumerate((
            f"Laço de {GIF_LOOP_S:.0f} s em que cada máquina fecha voltas inteiras; trocas de quadro em múltiplos de "
            f"{GIF_STEP} ms (os navegadores tratam atrasos de 10 ms ou menos como 100 ms).",
            "No GIF a F1 usa 0,12 s por quadro (no jogo 0,125 s) e a F3 0,125 s em média (no jogo 0,12 s); quadros de "
            "0,125 s e 0,25 s alternam ±10 ms.",
            "* Luz do banco PEM (lights_add) condicional: na ordem de camadas do spec ela fica sob o teto; se o jogo "
            "não a mostrar, a ligação a põe em roof_lights_fancy.")):
        dr.text((gap, 44 + 20 * i), s, font=_fit_font(dr, s, W - 2 * gap, 14), fill=DIM)
    pos = []
    y = head
    for r, h in zip(rows, rh):
        x = gap
        for f, m, fr in r:
            iv = f"{m['machine']['interval']:.3g}".replace(".", ",")
            pw = fr[0].width
            l1 = f"{f['code']} · {f['name']}"
            l2 = (f.get("sub", "") + " · " if f.get("sub") else "") + f"{len(fr)} quadros × {iv} s"
            dr.text((x, y + 2), l1, font=_fit_font(dr, l1, pw, 15, True), fill=GOLD)
            dr.text((x, y + 21), l2, font=_fit_font(dr, l2, pw, 13), fill=DIM)
            pos.append((x, y + lab_h))
            x += pw + gap
        y += h + gap
    frames = []
    for t in ts:
        im = base.copy()
        for (f, m, fr), (x, y), st in zip(data, pos, starts):
            im.paste(fr[frame_at(st, t, len(fr))].convert("RGB"), (x, y))
        frames.append(im)
    pals = save_gif_perframe(frames, durs, out)
    rep = gif_readback(out, frames, pals)
    rep["voltas_por_painel"] = {f"{f['code']} {f.get('sub', f['name'])}": f"{c} x {len(fr)} q, {e:.1f} ms/q"
                                for (f, m, fr), (c, e) in zip(data, cyc)}
    print(out, base.size, len(frames), "quadros", os.path.getsize(out) // 1024, "KiB")
    print(json.dumps(rep, ensure_ascii=False))
    if rep["atraso_min_ms"] < GIF_STEP or rep["laco_ms"] != int(round(GIF_LOOP_S * 1000)):
        raise SystemExit(f"GIF gravado com atraso minimo {rep['atraso_min_ms']} ms / laco {rep['laco_ms']} ms")
    if conf:
        os.makedirs(conf, exist_ok=True)
        g = Image.open(out)
        g.seek(0)
        chk = Image.new("RGB", (W * 2 + 10, H), (255, 0, 255))
        chk.paste(frames[0], (0, 0))
        chk.paste(g.convert("RGB"), (W + 10, 0))
        chk.save(os.path.join(conf, "gif_check_q0.png"))
    return rep


# ============================================================================ conferencia de arte
def flat_region(a):
    """Maior regiao plana clara (lum > 150, sat < 25, gradiente local < 5) em quadros^2 e a bbox dela (STYLE 1.8)."""
    rgb = a[..., :3]
    lum = rgb @ [0.299, 0.587, 0.114]
    sat = rgb.max(-1) - rgb.min(-1)
    gx = np.abs(np.diff(lum, axis=1, append=lum[:, -1:]))
    gy = np.abs(np.diff(lum, axis=0, append=lum[-1:, :]))
    gl = np.maximum(gx, gy)
    gl = np.maximum(gl, np.roll(gl, 1, 0))
    gl = np.maximum(gl, np.roll(gl, 1, 1))
    m = (lum > 150) & (sat < 25) & (gl < 5) & (a[..., 3] > 200)
    seen = np.zeros(m.shape, bool)
    best, bbb = 0, (0, 0)
    H, W = m.shape
    for y0, x0 in zip(*np.nonzero(m)):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)])
        seen[y0, x0] = True
        n, xa, xb, ya, yb = 0, x0, x0, y0, y0
        while q:
            y, x = q.popleft()
            n += 1
            xa, xb, ya, yb = min(xa, x), max(xb, x), min(ya, y), max(yb, y)
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    q.append((yy, xx))
        if n > best:
            best, bbb = n, ((xb - xa + 1) / PX, (yb - ya + 1) / PX)
    return best / float(PX * PX), bbb


def _sat_hues(px, smin, vmin):
    """Matizes (graus) dos pixels saturados (max - min >= smin e max >= vmin)."""
    px = px.reshape(-1, px.shape[-1])[:, :3].astype(int)
    m = ((px.max(1) - px.min(1)) >= smin) & (px.max(1) >= vmin)
    return _hue(px[m]) if m.any() else np.zeros(0)


def hue_code(d, m, f, tol=15.0):
    """Codigo de cor placa x saida (teto pintado como no jogo): [(modo, matiz dominante da placa, fracao dos pixels
    coloridos da escotilha da saida - pastilha + LEDs - a ate tol graus dele, n px)]."""
    out = []
    r = np.asarray(roof(d, m, f))
    for md, rect in m.get("grid", {}).get("outputs", {}).items():
        if md not in f["plate"]["modes"]:
            continue
        pl = np.asarray(Image.open(os.path.join(PLACAS, f"placa_{md}.png")).convert("RGBA"))
        hp = _sat_hues(pl[pl[..., 3] > 200], 50, 120)
        hist = np.histogram(hp, bins=36, range=(0, 360))[0]
        hdom = float(np.argmax(hist) * 10 + 5)
        i, j = rect[:2]
        ho = _sat_hues(r[j * PX + 4:(j + 1) * PX - 4, i * PX + 4:(i + 1) * PX - 4], 90, 150)
        near = float((np.abs((ho - hdom + 180) % 360 - 180) <= tol).mean()) if len(ho) else 0.0
        out.append((md, hdom, near, len(ho)))
    return out


def cells_of(rect):
    x, y, w, h = rect
    return [(x + i, y + j) for i in range(w) for j in range(h)]


def check_one(f, d, spec=None):
    errs, notes = [], []
    mp = os.path.join(d, "meta.json")
    if not os.path.exists(mp):
        return [f"sem meta.json em {d}"], notes
    m = json.load(open(mp))
    W, H = m["size"]
    if m.get("kind") != "factory":
        errs.append(f"kind {m.get('kind')}")
    if m.get("factory_code") != f["code"]:
        errs.append(f"factory_code {m.get('factory_code')} != {f['code']} (META_EXTRA nao entrou: rodou o helper?)")
    for k in ("grid", "lights_gain", "roof_led_safe_px"):
        if k not in m:
            errs.append(f"meta sem '{k}' (o 2o passo, _bs2_fabricas_helpers.py, nao rodou)")
    grid = m.get("grid", {})
    if spec:
        sf, sa = spec
        if m.get("id") != sf["id"]:
            errs.append(f"id {m.get('id')} != spec {sf['id']}")
        if [W, H] != list(sf["size"]):
            errs.append(f"size {[W, H]} != spec {sf['size']}")
        if len(m["machine"]["frames"]) != sa["machine_frames"]:
            errs.append(f"{len(m['machine']['frames'])} quadros != spec {sa['machine_frames']}")
        if abs(m["machine"]["interval"] - sa["machine_interval_s"]) > 1e-6:
            errs.append(f"intervalo {m['machine']['interval']} != spec {sa['machine_interval_s']}")
        sin = {c for r in sf["input_grids"].values() for c in cells_of(r)}
        sout = {c for r in sf["recipes"] for c in cells_of(r["output_grid_rect"])}
        min_ = {c for r in grid.get("inputs", {}).values() for c in cells_of(r)}
        mout = {c for r in grid.get("outputs", {}).values() for c in cells_of(r)}
        if sin != min_ or sout != mout:
            errs.append(f"grades do meta (entradas {sorted(min_)}, saidas {sorted(mout)}) != spec")
        if sa.get("mode_plate") and list(m.get("mode_plate", {}).get("rect_centre", [])) != \
                list(sa["mode_plate"]["rect_centre"]):
            errs.append("mode_plate.rect_centre != spec")
    for fn in m.get("files", []):
        if not os.path.exists(os.path.join(d, fn)):
            errs.append(f"meta.files cita {fn}, que nao existe")
    for key, fn in m["hull"].items():
        sz = load(d, fn).size
        if sz != (W * PX, H * PX):
            errs.append(f"{fn} ({key}) {sz} != {(W * PX, H * PX)}")
    roof_a = np.asarray(load(d, m["hull"]["roof"]))
    rn = np.asarray(load(d, m["hull"]["roof_normals"]))
    if (np.abs(roof_a[..., 3].astype(int) - rn[..., 3].astype(int)) > 8).mean() > 0.01:
        errs.append("alfa de roof_normals != alfa de roof")
    if (roof_a[1:-1, 1:-1, 3] < 250).mean() > 0.002:
        errs.append("teto com pixels transparentes (o teto cobre a peca)")
    if (np.asarray(load(d, m["hull"]["floor"]))[..., 3] < 250).any():
        errs.append("piso nao e opaco")
    mc = m["machine"]
    frames = [load(d, fn) for fn in mc["frames"]]
    if len({fr.size for fr in frames}) != 1 or frames[0].size != (W * PX, H * PX):
        errs.append(f"quadros da maquina com tamanhos {sorted({fr.size for fr in frames})}")
    pads = [(c, f"entrada {k}") for k, r in grid.get("inputs", {}).items() for c in cells_of(r)]
    pads += [(c, f"saida {k}") for k, r in grid.get("outputs", {}).items() for c in cells_of(r)]
    worst = 0.0
    for (cx, cy), what in pads:
        x0, y0 = cx * PX + 3, cy * PX + 3
        cov = max((np.asarray(fr)[y0:y0 + 58, x0:x0 + 58, 3] > 60).mean() for fr in frames)
        worst = max(worst, cov)
        if cov > 0.01:
            errs.append(f"maquina cobre {cov:.1%} da celula [{cx},{cy}] ({what})")
    blocked = {tuple(c) for c in grid.get("blocked", [])}
    if blocked & {c for c, _ in pads}:
        errs.append("celula de entrada/saida marcada como bloqueada")
    notes.append(f"bases livres: {len(pads)} celulas, cobertura maxima da maquina {worst:.2%}")
    on = np.asarray(frames[0]).astype(int)
    off = np.asarray(load(d, mc["off"])).astype(int)
    lit = (np.abs(on[..., :3] - off[..., :3]).max(axis=2) > 28) & (on[..., 3] > 128)
    frac = lit.sum() / float(W * H * PX * PX)
    notes.append(f"area acesa do quadro 1: {frac:.2%} do sprite (STYLE 1.6: <= 2%)")
    if frac > 0.02:
        errs.append(f"area acesa do quadro 1 {frac:.2%} do sprite (> 2%, STYLE 1.6)")
    li = np.asarray(load(d, m["hull"]["lights"]))
    notes.append(f"lights.png: pico {li[..., :3].max()}" + (f", ganho {m['lights_gain']}" if "lights_gain" in m else ""))
    fr_roof, bb = flat_region(roof_a.astype(float))
    fr_m, bbm = max((flat_region(np.asarray(fr).astype(float)) for fr in frames), key=lambda t: t[0])
    notes.append(f"maior regiao plana clara: teto {fr_roof:.2f} q2 ({bb[0]:.2f}x{bb[1]:.2f}), maquina {fr_m:.2f} q2")
    for what, v in (("teto", fr_roof), ("maquina", fr_m)):
        if v > 0.13:
            errs.append(f"{what}: regiao plana clara de {v:.2f} quadro^2 (> 0,13, STYLE 1.8)")
    blk = max(int(((np.asarray(fr)[..., :3].max(2) <= 2) & (np.asarray(fr)[..., 3] > 200)).sum()) for fr in frames)
    notes.append(f"preto puro opaco na maquina: {blk} px")
    if blk / float(W * H * PX * PX) > 0.01:
        errs.append(f"maquina com {blk} px de preto puro (> 1% do sprite: pocos vazios)")
    r_, g_, b_ = roof_a[..., 0].astype(int), roof_a[..., 1].astype(int), roof_a[..., 2].astype(int)
    paint = ((g_ - np.maximum(r_, b_)) > 13) & (np.abs(r_ - b_) < 64)
    notes.append(f"teto: {paint.mean():.0%} pintado (verde)")
    for name, ov in m.get("overlays", {}).items():
        want = (int(round(ov["rect"][2] * PX)), int(round(ov["rect"][3] * PX)))
        for fn in ov["files"]:
            sz = load(d, fn).size
            if abs(sz[0] - want[0]) > 1 or abs(sz[1] - want[1]) > 1:
                errs.append(f"{fn} {sz} != rect {want}")
        if "frames" in ov and len(ov["files"]) != ov["frames"]:
            errs.append(f"{name}: {len(ov['files'])} arquivos != {ov['frames']} quadros")
        notes.append(f"camada extra {name}: {len(ov['files'])} arquivo(s), {ov['game_layer']}"
                     + (" (nota: " + ov["notes"][:60] + "...)" if ov.get("notes") else ""))
    if f.get("hue_check"):
        for md, hdom, near, n in hue_code(d, m, f):
            notes.append(f"codigo de cor {md}: placa ~{hdom:.0f} graus; {near:.0%} dos {n} px coloridos da saida a "
                         f"ate 15 graus dela")
            if n < 8 or near < 0.7:
                errs.append(f"saida {md} fora do codigo de cor da placa_{md} ({near:.0%} dos px perto do matiz)")
    if f.get("plate"):
        mpm = m.get("mode_plate")
        if not mpm:
            errs.append("falta mode_plate no meta")
        elif [float(v) for v in mpm["rect_centre"]] != [float(v) for v in f["plate"]["c"]]:
            errs.append(f"mode_plate.rect_centre {mpm['rect_centre']} != previa {f['plate']['c']}")
        else:
            notes.append(f"placa de modo em {mpm['rect_centre']} ({', '.join(mpm['modes'])})")
    return errs, notes


def check(src, facs, spec_path=None):
    spec = None
    if spec_path:
        s = json.load(open(spec_path))
        spec = ({f["code"]: f for f in s["factories"]}, s["art_assets"]["assets"]["factories"])
    bad = 0
    for f in FACT:
        if f["code"] not in facs:
            continue
        d = fdir(f, src)
        errs, notes = check_one(f, d, (spec[0][f["code"]], spec[1][f["code"]]) if spec else None)
        print(f"== {f['code']} {os.path.relpath(d, ROOT) if d.startswith(ROOT) else d}")
        for n in notes:
            print("   ", n)
        for e in errs:
            print("  ERRO", e)
        if errs:
            bad += 1
        else:
            print("   OK")
    print("PROBLEMAS" if bad else "OK todas")
    return bad


def main():
    a = sys.argv[1:]
    what = a[0] if a and not a[0].startswith("--") else "todas"

    def opt(k, default=None):
        return a[a.index(k) + 1] if k in a else default
    src = os.path.abspath(opt("--src", ART))
    outd = os.path.abspath(opt("--out", OUT_DIR))
    facs = opt("--fac", ",".join(f["code"] for f in FACT)).split(",")
    os.makedirs(outd, exist_ok=True)
    bad = 0
    if what in ("check", "todas"):
        bad = check(src, facs, opt("--spec"))
    if what in ("folha", "todas"):
        sheet(src, os.path.join(outd, "fabricas_2_0.png"), facs, items_strip(items_dir(opt("--itens"), opt("--blender"))))
    if what in ("gif", "todas"):
        gif(src, os.path.join(outd, "fabricas_2_0.gif"), facs, conf=opt("--conf"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
