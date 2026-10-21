"""Kit da LOGISTICA 2.0 (Fita, FX dos cartuchos, placas de tipo, paiois): paleta, cassete neutro e utilitarios.

So o grupo da logistica usa este modulo (parts/bs_fita.py, bs_fita_fx.py, bs_placas.py, bs_paiol.py). Nada aqui muda
o kit comum (bs3d.py, models.py); os materiais novos tem nomes proprios (o cache do bs3d e por nome, STYLE.md 9).

Paleta (SPEC_2.0 art_assets.palette, sRGB 0-255): family_chip, gauge, cores por tipo das placas. Os verdes que vao
no TETO (luz da fita no teto, medidor cheio) mantem |r - b| >= 64: o shader de pintura do jogo pinta tudo que e
"verde com r ~ b" (STYLE.md 9); o verde do medidor cheio (110, 230, 90) do spec vira (104, 232, 30).
"""

import math

import bs3d as B

# ============================================================================ paleta (sRGB 0-255)
FAMILY_CHIP = {"cartuchos": (255, 190, 60), "celulas": (60, 220, 255), "misseis": (255, 120, 40),
               "projeteis": (150, 105, 255)}
GAUGE = {"low": (255, 70, 30), "high": (255, 200, 40), "full": (104, 232, 30)}   # full: |r - b| >= 64 (pintura)
# cor de cada tipo nas placas (palette[kind].band / chip; nunca o azul da interface)
KIND = {
    "he": {"body": (255, 190, 60), "acc": None},
    "ap": {"body": (215, 230, 255), "acc": None},
    "sap": {"body": (255, 140, 50), "acc": (255, 236, 200)},
    "ac": {"body": (230, 40, 80), "acc": (255, 200, 80)},
    "frag": {"body": (120, 210, 200), "acc": (225, 255, 250)},
    "plasma": {"body": (60, 220, 255), "acc": (220, 250, 255)},
    "pem": {"body": (60, 200, 255), "acc": (226, 140, 72)},          # bobinas de cobre na celula PEM
    "msl_he": {"body": (255, 170, 50), "acc": None},
    "msl_cluster": {"body": (255, 120, 40), "acc": (255, 214, 120)},
    "msl_emp": {"body": (80, 150, 255), "acc": (205, 236, 255)},
    "msl_nuke": {"body": (120, 236, 40), "acc": (20, 22, 26)},       # trevo escuro sobre o verde (sem amarelo)
    "slug": {"body": (150, 105, 255), "acc": (255, 214, 120)},       # aneis de armadura dourados
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
        "cass_cap": B.mat_metal("lg_cass_cap", (0.30, 0.31, 0.33), rough=0.30, metal=0.9),
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
