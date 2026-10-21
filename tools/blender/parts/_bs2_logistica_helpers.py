"""Kit da LOGISTICA 2.0 (Fita, FX dos cartuchos, placas de tipo, paiois): paleta, cassete neutro e utilitarios.

So o grupo da logistica usa este modulo (parts/bs_fita.py, bs_fita_fx.py, bs_placas.py, bs_paiol.py). Nada aqui muda
o kit comum (bs3d.py, models.py); os materiais novos tem nomes proprios (o cache do bs3d e por nome, STYLE.md 9).

Paleta (SPEC_2.0 art_assets.palette, sRGB 0-255): family_chip, gauge, cores por tipo das placas.

Verdes e pintura: so a camada "roofs" usa o shader de teto com pintura por chave de cor (ENABLE_ROOF_PAINT_COLOR_KEYED);
"roof_doodads" (medidor, placas, digitos, FX, luz da fita no teto) usa ../common/roof_uncolored_lit.shader (vanilla
terran.rules), que NAO pinta nada. Mesmo assim todo verde desta arte fica fora da chave de pintura (STYLE.md 9:
verde dominante com |r - b| < 64): se alguem mudar a camada, ou copiar a arte para um teto, nada vira pintura. O
paint_safe() abaixo garante isso PIXEL A PIXEL depois de cada sprite (bordas, halos e relevos incluidos), e o
check_logistica.py confere. Por isso o verde do medidor cheio nao e o (110, 230, 90) do ProgressBar (|r - b| = 20) e
sim GAUGE["full"] = (88, 240, 14): o mesmo papel (cheio = verde), um pouco mais amarelado.
"""

import math

import bs3d as B

# ============================================================================ paleta (sRGB 0-255)
# projeteis: AZUL eletrico + pontas LARANJA (paleta nova do Tupa, referencia do usuario; USER_NOTES: "paleta azul em
# vez de violeta; slug da Tupa acompanha a cor"). Diferente do ciano das celulas (hue 225 contra 191 graus) e com as
# pontas laranja (FAMILY_CHIP_TIP) que nenhuma outra familia tem.
FAMILY_CHIP = {"cartuchos": (255, 190, 60), "celulas": (60, 220, 255), "misseis": (255, 120, 40),
               "projeteis": (64, 128, 255)}
FAMILY_CHIP_TIP = {"projeteis": (255, 140, 40)}
# medidor: low -> high -> full interpolados em HSV (a saturacao se mantem no meio; sem o oliva da mistura RGB).
# full: verde fora da chave de pintura (r - b = 74 >= 64), todas as cores derivadas passam por safe_rgb()
GAUGE = {"low": (255, 70, 30), "high": (255, 200, 40), "full": (88, 240, 14)}
# cor de cada tipo nas placas (palette[kind] band/chip; nunca o azul da interface). As silhuetas sao as dos icones
# 2.0 do seletor (tools/bsgen/ui_icons.py, art3d/bs_ui_icons2): "body" = corpo do icone, "acc" = a mascara de destaque
# do icone, "parts" = regioes do corpo com outra cor (bobinas de cobre, minimisseis, cauda), em coordenadas do icone
# (0..96, y para baixo), recortadas pela mascara do corpo
COPPER = (214, 122, 58)               # bobinas da familia P.E.M. (palette.pem.copper clareado: le no campo escuro)
SPARK = (205, 236, 255)               # raio do P.E.M. (o "spark" dos icones)
KIND = {
    "he": {"body": (255, 190, 60), "acc": None},
    "ap": {"body": (215, 230, 255), "acc": None},
    "sap": {"body": (255, 128, 44), "acc": (255, 238, 190)},       # laranja mais vermelho que o HE + estrela clara
    "ac": {"body": (230, 40, 80), "acc": (255, 200, 80)},          # carmim + faixa de ouro
    "frag": {"body": (120, 210, 200), "acc": (215, 250, 244)},
    "plasma": {"body": (60, 220, 255), "acc": (225, 250, 255)},
    "pem": {"body": (50, 175, 255), "acc": SPARK,                  # capsula azul, 3 bobinas de COBRE, raio claro
            "parts": [("rects", [(0, 26, 96, 39.5), (0, 43, 96, 56.5), (0, 60, 96, 73.5)], COPPER)]},
    "msl_he": {"body": (255, 170, 50), "acc": None},
    "msl_cluster": {"body": (255, 120, 40), "acc": None,           # portador laranja, minimisseis ouro claro
                    "parts": [("rects", [(0, 0, 96, 51.5), (0, 0, 29.5, 57), (66.5, 0, 96, 57)], (255, 214, 120))]},
    "msl_emp": {"body": (80, 150, 255), "acc": SPARK,              # Poraque: bobinas de cobre (STYLE 8.4)
                "parts": [("rects", [(0, 39.5, 96, 46.5), (0, 49.5, 96, 56.5), (0, 59.5, 96, 66.5)], COPPER)]},
    "msl_nuke": {"body": (110, 232, 30), "acc": (200, 255, 120)},  # corpo verde + trevo verde-claro AO LADO (icone)
    "slug": {"body": (205, 228, 255), "acc": (64, 128, 255),       # haste branco-azulada, aneis EM AZUIS e a cauda
             "parts": [("rects", [(0, 69.5, 96, 96)], (255, 140, 40))]},   # LARANJA (paleta nova do Tupa)
}
KIND_ORDER = ["he", "ap", "sap", "ac", "frag", "plasma", "pem", "msl_he", "msl_cluster", "msl_emp", "msl_nuke",
              "slug"]
FAMILY_KINDS = {"cartuchos": ["he", "ap", "sap", "ac", "frag"], "celulas": ["plasma", "pem"],
                "misseis": ["msl_he", "msl_cluster", "msl_emp", "msl_nuke"], "projeteis": ["slug"]}
LINK_GREEN = (0.16, 1.0, 0.0)        # luz da fita grudada (linear; sRGB ~(111, 255, 0): |r - b| > 64, nunca vira pintura)
TELE_CYAN = (0.0, 0.62, 0.80)        # rastro do teletransporte (canal mais fraco ~0: ciano puro, baixo)


def lin(c):
    """sRGB 0-255 -> linear 0-1 (cores do spec nos materiais do Blender)."""
    def f(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(f(v) for v in c)


# ============================================================================ materiais proprios
def mats(M):
    """Materiais da logistica (nomes unicos). Devolve um dict; M (Mo.mats) continua valendo para o resto."""
    return {
        "brass": B.mat_metal("brass", (0.66, 0.44, 0.12), rough=0.28, metal=1.0),     # = parts/bs_mag_std.py
        "cass": B.mat_metal("lg_cass", (0.050, 0.053, 0.062), rough=0.36, metal=0.8),  # capsula escura do cassete
        "cass_cap": B.mat_metal("lg_cass_cap", (0.50, 0.51, 0.54), rough=0.34, metal=0.55),   # tampas claras: le no teto escuro
        "amber": B.mat_glow("lg_amber", (1.0, 0.42, 0.04), 2.2),
        "amber_off": B.mat_metal("lg_amber_off", (0.09, 0.035, 0.004), rough=0.2, metal=0.0),
        "lens_off": B.mat_metal("lg_lens_off", (0.012, 0.030, 0.012), rough=0.12, metal=0.0),   # lente verde apagada
        "glass": B.mat_metal("lg_glass", (0.010, 0.013, 0.018), rough=0.10, metal=0.0),         # janela escura
        "link": B.mat_glow("lg_link", LINK_GREEN, 1.6),
        "tele": B.mat_glow("lg_tele", TELE_CYAN, 0.7),
        "tele_dim": B.mat_glow("lg_tele_dim", TELE_CYAN, 0.22),
    }


# ============================================================================ cassete neutro
CASS_L, CASS_W, CASS_H = 0.30, 0.15, 0.10


def cassette(name, x, y, z0, M, X, tags, rot=0.0, s=1.0, lit=True):
    """Cassete selado NEUTRO (o mesmo para todo tipo de municao): capsula escura chanfrada, tampas de aco nas
    pontas, faixa de latao e 1 pip ambar num rebaixo preto. Eixo longo em Y (girado por rot graus), base em z0.
    s = escala. lit=False: pip apagado (lente ambar escura)."""
    L, W, H = CASS_L * s, CASS_W * s, CASS_H * s
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)

    def P(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca)

    def poly(pts):
        return [P(px, py) for px, py in pts]
    c = 0.035 * s
    body = [(-W / 2 + c, -L / 2), (W / 2 - c, -L / 2), (W / 2, -L / 2 + c), (W / 2, L / 2 - c), (W / 2 - c, L / 2),
            (-W / 2 + c, L / 2), (-W / 2, L / 2 - c), (-W / 2, -L / 2 + c)]
    B.plate(f"{name}_body", poly(body), z0, z0 + H, X["cass"], slope=0.018 * s, bevel=0.006 * s, tags=tags)
    for k, (ya, yb2) in enumerate(((-L / 2 + 0.004 * s, -L / 2 + 0.05 * s), (L / 2 - 0.05 * s, L / 2 - 0.004 * s))):
        cap = [(-W / 2 + c * 0.7, ya), (W / 2 - c * 0.7, ya), (W / 2 - c * 0.7, yb2), (-W / 2 + c * 0.7, yb2)]
        B.plate(f"{name}_cap{k}", poly(cap), z0 + H * 0.15, z0 + H + 0.008 * s, X["cass_cap"], slope=0.008 * s,
                bevel=0.003 * s, tags=tags)
    yb = -L * 0.12
    band = [(-W / 2 - 0.004 * s, yb - 0.022 * s), (W / 2 + 0.004 * s, yb - 0.022 * s),
            (W / 2 + 0.004 * s, yb + 0.022 * s), (-W / 2 - 0.004 * s, yb + 0.022 * s)]
    B.loft(f"{name}_band", poly(band), poly(band), z0 + H * 0.10, z0 + H + 0.006 * s, X["brass"], bevel=0.003 * s,
           tags=tags)
    yp = L * 0.22
    bed = [(-0.030 * s, yp - 0.024 * s), (0.030 * s, yp - 0.024 * s), (0.030 * s, yp + 0.024 * s),
           (-0.030 * s, yp + 0.024 * s)]
    B.loft(f"{name}_pbed", poly(bed), poly(bed), z0 + H - 0.004 * s, z0 + H + 0.003 * s, M["black"], bevel=0.0,
           tags=tags)
    pip = [(-0.017 * s, yp - 0.013 * s), (0.017 * s, yp - 0.013 * s), (0.017 * s, yp + 0.013 * s),
           (-0.017 * s, yp + 0.013 * s)]
    B.loft(f"{name}_pip", poly(pip), poly(pip), z0 + H, z0 + H + 0.006 * s, X["amber"] if lit else X["amber_off"],
           bevel=0.0, tags=tags)


# ============================================================================ utilitarios
def ledslot(name, cx, cy, sx, sy, z_bed, M, tags, targets, lens=None, lens_frac=0.6):
    """Rebaixo VAZADO nas pecas (sem fundo: o bisel reaplicado nao cobre o leito, STYLE.md 9 'fendas cegas
    estreitas') com leito preto em z_bed e uma lente no meio (lens = material; None = so o leito)."""
    for k, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.box(f"{name}_c{k}", cx, cy, sx, sy, z_bed - 0.02, z_bed + 0.6, M["black"], bevel=0.0)])
    B.box(name + "_bed", cx, cy, sx, sy, z_bed, z_bed + 0.008, M["black"], bevel=0.0, tags=tags)
    if lens is not None:
        B.box(name + "_lens", cx, cy, sx * lens_frac, sy * lens_frac, z_bed + 0.008, z_bed + 0.018, lens, bevel=0.0,
              tags=tags)


def safe_rgb(c):
    """Cor (r, g, b) 0-255 fora da chave de pintura (STYLE.md 9): se o verde passa do vermelho e do azul com
    |r - b| < 64, afasta r de b (verdes claros de verdade: b desce, r sobe), puxa o azul (menta -> ciano) ou tira o
    excesso de verde (cinzas esverdeados e verdes escuros ficam neutros). Cores nao verdes passam iguais."""
    r, g, b = (float(v) for v in c[:3])
    if g <= max(r, b) or abs(r - b) >= 64:
        return tuple(int(round(v)) for v in (r, g, b))
    if b >= r:                                        # menta/ciano: vira ciano (o azul alcanca o verde)
        b = g
    elif g >= 96 and g - max(r, b) > 8:               # verde claro de verdade: r - b >= 64
        b = max(0.0, min(b, r - 64))
        r = max(r, b + 64)
    else:                                             # cinza esverdeado / verde escuro (sombra, borda): neutro
        g = max(r, b)
    return tuple(int(round(min(255.0, max(0.0, v)))) for v in (r, g, b))


def paint_safe(img):
    """safe_rgb() por pixel (Image RGBA -> Image RGBA, mesma alfa): nenhum pixel com alfa > 0 fica com o verde acima
    do vermelho e do azul e |r - b| < 64 (a chave de pintura do jogo e o 'verde' das conferencias). Devolve (imagem,
    pixels mudados)."""
    import numpy as np
    from PIL import Image
    a = np.asarray(img.convert("RGBA")).astype(np.float32).copy()
    r, g, b, al = a[..., 0].copy(), a[..., 1].copy(), a[..., 2].copy(), a[..., 3]
    mx = np.maximum(r, b)
    bad = (al > 0) & (g > mx) & (np.abs(r - b) < 64)
    n = int(bad.sum())
    if n:
        cyan = bad & (b >= r)
        a[..., 2] = np.where(cyan, g, a[..., 2])
        lite = bad & (b < r) & (g >= 96) & (g - mx > 8)
        nb = np.clip(np.minimum(b, r - 64), 0, 255)
        a[..., 2] = np.where(lite, nb, a[..., 2])
        a[..., 0] = np.where(lite, np.maximum(r, nb + 64), a[..., 0])
        flat = bad & (b < r) & ~lite
        a[..., 1] = np.where(flat, mx, a[..., 1])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), n


def paint_safe_file(path):
    """paint_safe() num PNG gravado (pos-processo das camadas roof_doodads). Devolve os pixels mudados."""
    from PIL import Image
    img, n = paint_safe(Image.open(path))
    if n:
        img.save(path)
    return n


def premul_blur(img, radius):
    """GaussianBlur com alfa PRE-multiplicado (o blur comum do PIL mistura o RGB com o preto dos pixels
    transparentes e escurece/desvia a cor das bordas): a cor do halo e a media das cores de verdade."""
    import numpy as np
    from PIL import Image, ImageFilter
    a = np.asarray(img.convert("RGBA")).astype(np.float32) / 255.0
    pm = np.dstack([a[..., :3] * a[..., 3:4], a[..., 3:4]])
    chans = [np.asarray(Image.fromarray((pm[..., i] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius)),
                        np.float32) / 255.0 for i in range(4)]
    al = chans[3]
    rgb = np.dstack(chans[:3]) / np.maximum(al[..., None], 1e-6)
    out = np.dstack([np.clip(rgb, 0, 1), al[..., None]])
    out[al < 1e-6] = 0
    return Image.fromarray((out * 255).astype(np.uint8), "RGBA")


def rot4(pts, k):
    """Gira pontos (x, y) por k x 90 graus (anti-horario) em torno da origem."""
    out = []
    for x, y in pts:
        for _ in range(k % 4):
            x, y = -y, x
        out.append((x, y))
    return out


# ============================================================================ digitos de 7 segmentos
# geometria em unidades da celula do digito (0..1 em x, 0..1 em y para BAIXO); a mesma para os digitos acesos
# (digito0..9.png) e para os segmentos apagados pintados na janela dos digitos do teto do paiol: sempre casam
SEG_T = 0.17                          # espessura do segmento (fracao da largura)
SEG = {                               # a, b, c, d, e, f, g
    "a": (0.20, 0.08, 0.80, 0.08 + SEG_T * 0.6),
    "b": (0.80 - SEG_T * 0.6 * 0.6, 0.12, 0.80 + SEG_T * 0.6 * 0.4, 0.47),
    "c": (0.80 - SEG_T * 0.6 * 0.6, 0.53, 0.80 + SEG_T * 0.6 * 0.4, 0.88),
    "d": (0.20, 0.92 - SEG_T * 0.6, 0.80, 0.92),
    "e": (0.20 - SEG_T * 0.6 * 0.4, 0.53, 0.20 + SEG_T * 0.6 * 0.6, 0.88),
    "f": (0.20 - SEG_T * 0.6 * 0.4, 0.12, 0.20 + SEG_T * 0.6 * 0.6, 0.47),
    "g": (0.20, 0.50 - SEG_T * 0.3, 0.80, 0.50 + SEG_T * 0.3),
}
DIGIT_SEGS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
              "7": "abc", "8": "abcdefg", "9": "abcdfg"}
SLANT = 0.10                          # inclinacao italica (fracao da largura por altura)


def seg_poly(seg, w, h, x0=0.0, y0=0.0):
    """Poligono (hexagono de pontas chanfradas) do segmento num retangulo w x h com canto em (x0, y0) (px, y para
    baixo), inclinado em italico."""
    ax0, ay0, ax1, ay1 = SEG[seg]
    X0, X1, Y0, Y1 = ax0 * w, ax1 * w, ay0 * h, ay1 * h
    if X1 - X0 >= Y1 - Y0:            # horizontal
        m = (Y1 - Y0) / 2
        pts = [(X0, (Y0 + Y1) / 2), (X0 + m, Y0), (X1 - m, Y0), (X1, (Y0 + Y1) / 2), (X1 - m, Y1), (X0 + m, Y1)]
    else:
        m = (X1 - X0) / 2
        pts = [((X0 + X1) / 2, Y0), (X1, Y0 + m), (X1, Y1 - m), ((X0 + X1) / 2, Y1), (X0, Y1 - m), (X0, Y0 + m)]
    return [(x0 + px + SLANT * (h / 2 - py), y0 + py) for px, py in pts]
