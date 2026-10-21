"""Kit dos itens de municao 2.0 do Bullet Strike (recursos kind "resource": carregadores, celulas, cargas de missil,
ogiva nuclear e projetil da railgun).

Modulo do grupo "itens" (spec 2.0, art_assets.assets.resources + USER_NOTES "municoes futuristas"). Nao altera o kit
compartilhado (bs3d.py, models.py, render_part.py): so importa de la. Cada recurso continua sendo um modelo
kind "resource" (tools/blender/parts/<id_curto>.py, renderizado por render_part.py) que chama as funcoes daqui.

Linguagem (STYLE.md 1 e 7, a mesma das granadas e dos misseis 2.0): nucleo escuro por baixo de tudo (moldura escura
em volta das pecas), cascas claras de bisel duplo (B.shard), frestas pretas, LEDs so em recessos escuros e a COR DA
MUNICAO em duas camadas: tinta da faixa (emissao fraquinha, nao apaga na sombra, como Mo.band_mat) + uma fenda de LED
num recesso. As municoes dentro dos carregadores sao as granadas 2.0 do nivel S em miniatura (luva de composito
claro, faixa da cor, ogiva grafite, espoleta/penetrador/capuz/canards de cada tipo), os narizes das cargas de missil
sao os dos misseis 2.0 (Mo.band_mat = a mesma tinta do missil em voo e dos narizes nos lancadores) e o projetil da
Tupa segue a paleta AZUL nova da railgun (referencia do usuario: azul + detalhes laranja, parts/bs_rail.py).

Unidades: cada item e modelado centrado na origem, frente = +Y, cabendo em ~1 x 1 (o renderizador escala para a
pilha com unit_scale). Os nomes de material comecam com "it2_" (o cache do bs3d e por nome).
"""

import math

import bs3d as B
import models as Mo

A8 = math.pi / 8            # octogono de topo plano (Mo.lathe a0)
COS8 = math.cos(A8)


# ============================================================================ paleta 2.0 (sRGB -> linear)
def lin(c):
    out = []
    for v in c:
        v = v / 255.0
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return tuple(out)


# art_assets.palette (chip/band) do SPEC 2.0; PEM com o azul mais fundo do glow (o ciano do plasma e quase o mesmo
# matiz: a celula PEM le pelo cobre + azul), slug no azul da Tupa nova (USER_NOTES: referencia da railgun)
CHIP = {
    "he": (255, 190, 60), "ap": (215, 230, 255), "sap": (255, 140, 50), "ac": (230, 40, 80), "gold": (255, 200, 80),
    "frag": (120, 210, 200), "plasma": (60, 220, 255), "pem": (40, 150, 255), "slug": (45, 115, 255),
    "slug_hi": (110, 175, 255), "orange": (230, 135, 40), "nuke": (90, 255, 40),
}
# LEDs (forca ~1 na vista Standard sai ~ a cor; saturados para nao virar branco)
LED = {
    "he": (1.0, 0.42, 0.04), "ap": (0.50, 0.72, 1.0), "sap": (1.0, 0.20, 0.025), "ac": (1.0, 0.02, 0.08),
    "frag": (0.10, 0.90, 0.42), "plasma": (0.08, 0.72, 1.0), "pem": (0.03, 0.30, 1.0), "slug": (0.026, 0.171, 1.0),
    "slug_hi": (0.13, 0.43, 1.0), "nuke": (0.32, 1.0, 0.0), "msl_he": (1.0, 0.42, 0.04), "msl_cluster": (1.0, 0.78, 0.11),
    "msl_emp": (0.06, 0.45, 1.0), "white": (1.0, 0.92, 0.75), "nuke_core": (0.12, 1.0, 0.06),
}

COMP = (0.34, 0.352, 0.375)        # composito claro das luvas (= bs_shells2 COMP)
COMP_D = (0.17, 0.175, 0.185)      # composito medio (ogivas)
GRAPH = (0.085, 0.09, 0.10)        # grafite (capuzes, caudas)
STEEL = (0.50, 0.52, 0.55)         # aco claro (espoleta, penetrador, terminais)
TUNG = (0.40, 0.41, 0.43)          # tungstenio claro (haste do slug)
GOLD = (0.80, 0.47, 0.07)          # ouro da AC (= bs_shells2 GOLD)


def _spec(m, v):
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = v
    return m


def X(M):
    """Materiais extras (nomes unicos "it2_*")."""
    return {
        "comp": B.mat_paint("it2_comp", COMP, rough=0.40, metal=0.15, wear=0.0, grime=0.03, scale=5),
        "comp_d": _spec(B.mat_metal("it2_comp_d", COMP_D, rough=0.45, metal=0.3), 0.25),
        "ogive": _spec(B.mat_metal("it2_ogive", (0.095, 0.10, 0.11), rough=0.5, metal=0.1), 0.25),
        "graph": _spec(B.mat_metal("it2_graph", GRAPH, rough=0.45, metal=0.35), 0.25),
        "steel": _spec(B.mat_metal("it2_steel", STEEL, rough=0.34, metal=0.6), 0.35),
        "tung": _spec(B.mat_metal("it2_tung", TUNG, rough=0.30, metal=0.7), 0.35),
        "gold": _spec(B.mat_metal("it2_gold", GOLD, rough=0.30, metal=0.6), 0.35),
        "copper": Mo.copper_mat(),
        "nose": Mo.nose_paint("it2_nose", Mo.NOSE_LIGHT),
        "lens": _spec(B.mat_metal("it2_lens", (0.010, 0.012, 0.018), rough=0.12, metal=0.0), 0.7),
        # lente fosca (domos pequenos: a lente brilhante reflete o sol e some na ponta)
        "lensm": _spec(B.mat_metal("it2_lensm", (0.012, 0.014, 0.02), rough=0.5, metal=0.0), 0.2),
        "core": M["core"], "core_mid": M["core_mid"], "black": M["black"], "armor": M["armor"],
        "armor_mid": M["armor_mid"],
        # cascas escuras (grafite pintado sem desgaste: o desgaste de quina clareia malhas pequenas, STYLE 9)
        "dark": B.mat_paint("it2_dark", (0.055, 0.058, 0.066), rough=0.42, metal=0.45, wear=0.0, grime=0.03,
                            scale=6),
    }


PAINT_K = {"frag": 0.50, "ap": 0.70}   # tintas claras demais sob a luz de cima (a FRAG saia ciano como o plasma)


def paint(kind, emit=0.12, k=0.82):
    """Tinta da cor da municao (faixa/pastilha): nao e LED, mas tem uma emissao fraca na mesma cor para nao apagar na
    sombra (como Mo.band_mat)."""
    c = lin(CHIP[kind])
    k = min(k, PAINT_K.get(kind, k))
    m = B.mat_metal(f"it2_paint_{kind}", tuple(v * k for v in c), rough=0.55, metal=0.0)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.15
    b.inputs["Emission Color"].default_value = (*c, 1)
    b.inputs["Emission Strength"].default_value = emit
    m["bs_glow"] = emit
    return m


def led(kind, s=1.0):
    """LED emissivo na cor (lente escura com um toque da cor quando apagado)."""
    c = LED[kind]
    m = B.mat_glow(f"it2_led_{kind}_{int(round(s * 100)):03d}", c, s)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (c[0] * 0.03, c[1] * 0.03, c[2] * 0.03, 1)
    b.inputs["Roughness"].default_value = 0.4
    return m


# ============================================================================ geometria basica
def lathe_y(name, prof, mat, tags, x=0.0, zc=0.0, verts=8, a0=A8, smooth=False):
    """Solido de revolucao deitado ao longo de +Y (perfil [(raio, y)] da cauda para a frente), eixo em (x, zc).
    verts=8 + a0=pi/8 = octogono de topo plano (facetado como os canos e as granadas da familia)."""
    ob = Mo.lathe(name, prof, mat, tags, verts=verts, axis="X", zc=zc, a0=a0, smooth=smooth)
    ob.rotation_euler = (0.0, 0.0, math.pi / 2)      # eixo X -> +Y
    ob.location = (x, 0.0, 0.0)
    return ob


def ring_y(name, ya, yb, r, mat, tags, x=0.0, zc=0.0, ch=0.0, verts=8, a0=A8):
    """Anel/tubo curto (de ya a yb) com chanfro ch nas bordas."""
    if ch > 0:
        prof = [(r - ch, ya), (r, ya + ch), (r, yb - ch), (r - ch, yb)]
    else:
        prof = [(r, ya), (r, yb)]
    return lathe_y(name, prof, mat, tags, x=x, zc=zc, verts=verts, a0=a0)


def ogive_to(R, y0, y1, rf, n=8):
    """Ogiva tangente do raio R (em y0) ate o raio rf em y1 (truncada): [(raio, y)]."""
    L = y1 - y0
    rf = min(max(rf, 1e-4), R * 0.999)

    def at(Lo, s):
        rho = (R * R + Lo * Lo) / (2 * R)
        return math.sqrt(max(0.0, rho * rho - s * s)) + R - rho

    lo, hi = L, L * 20 + 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if at(mid, L) > rf:
            hi = mid
        else:
            lo = mid
    Lo = (lo + hi) / 2
    return [(at(Lo, L * k / n), y0 + L * k / n) for k in range(n + 1)]


def dome(y0, y1, r0, p=2.0, n=6):
    """Capuz/domo: raio r0 em y0 ate a ponta em y1 (expoente p: maior = mais rombudo)."""
    out = []
    for k in range(n + 1):
        t = k / n
        out.append((max(r0 * (1 - t ** p) ** (1 / p), 0.0), y0 + (y1 - y0) * t))
    out[-1] = (0.0, y1)
    return out


def fin_y(name, poly, z0, z1, mat, tags):
    """Aleta plana (prisma fino) no plano XY."""
    return B.loft(name, poly, poly, z0, z1, mat, bevel=0.0, tags=tags)


# ============================================================================ municoes do nivel S (miniatura)
# comprimentos do nariz em raios (ogiva, ponta) e raio final da ogiva, por municao
NOSE = {"he": (1.55, 0.62, 0.46), "ap": (2.5, 0.95, 0.24), "sap": (1.05, 0.55, 0.72), "ac": (2.1, 0.45, 0.44),
        "frag": (0.95, 0.30, 0.64)}


def round_s(pre, X, tags, ammo, x, zc, r, y0, y1, band=True, led_s=0.0):
    """UMA granada 2.0 do nivel S deitada ao longo de +Y (base em y0, ponta em y1), eixo em (x, zc), raio r.

    he  : luva de composito claro, faixa ambar, ogiva grafite media e espoleta de aco de ponta chata com o anel
          escuro do sensor;
    ap  : ogiva LONGA com capuz escuro e anel gelo, penetrador de triaco claro comprido;
    sap : ogiva curta com capuz ROMBUDO largo de grafite e colar de aco (crimp);
    ac  : guiada: faixa carmim entre dois aneis de ouro, canards de ouro no nariz e anel de ouro com o buscador
          escuro na ponta;
    frag: luva de fragmentos SEGMENTADA (aneis claros com sulcos pretos), faixa verde-agua e espoleta de
          proximidade chata (lente escura dentro de um aro de aco).
    led_s > 0: LED pequeno aceso no topo da faixa (num rebaixo). Devolve o y onde comeca a ogiva."""
    m = X
    lo, lt, rfk = NOSE[ammo]
    yt0 = y1 - lt * r                  # inicio da ponta (espoleta/capuz/penetrador/buscador)
    yo = yt0 - lo * r                  # inicio da ogiva
    bl = (1.25 if ammo != "ac" else 1.6) * r     # comprimento da faixa
    ybd = yo - bl
    # espinha escura por dentro (fecha as frestas entre os aneis) e obturador escuro na base
    ring_y(pre + "_spine", y0 + 0.01, yo + 0.01, r * 0.80, m["core"], tags, x=x, zc=zc)
    yb = y0 + 0.5 * r
    ring_y(pre + "_base", y0, yb, r * 0.92, m["graph"], tags, x=x, zc=zc, ch=0.004)
    if ammo == "frag":
        # luva de fragmentos: aneis claros com sulcos pretos (le como granada de fragmentacao a 1x)
        n = max(2, int(round((ybd - yb) / (0.95 * r))))
        seg = (ybd - yb) / n
        for i in range(n):
            ya = yb + i * seg
            ring_y(f"{pre}_fr{i}", ya + 0.007, ya + seg - 0.007, r * 1.02, m["comp"], tags, x=x, zc=zc, ch=0.007)
    else:
        # luva lisa de composito com UMA junta escura (a luva 2.0 partida em dois segmentos)
        yj = yb + 0.42 * (ybd - yb)
        ring_y(pre + "_sl0", yb + 0.005, yj - 0.006, r, m["comp"], tags, x=x, zc=zc, ch=0.006)
        ring_y(pre + "_sl1", yj + 0.006, ybd - 0.005, r, m["comp"], tags, x=x, zc=zc, ch=0.006)
    if ammo == "ac":
        g = 0.28 * r
        ring_y(pre + "_g0", ybd, ybd + g, r * 1.05, m["gold"], tags, x=x, zc=zc, ch=0.003)
        ring_y(pre + "_band", ybd + g, yo - g - 0.004, r * 1.03, paint("ac"), tags, x=x, zc=zc, ch=0.003)
        ring_y(pre + "_g1", yo - g - 0.004, yo - 0.002, r * 1.05, m["gold"], tags, x=x, zc=zc, ch=0.003)
    elif band:
        ring_y(pre + "_band", ybd, yo - 0.004, r * 1.035, paint(ammo), tags, x=x, zc=zc, ch=0.004)
    if led_s > 0:
        yl = (ybd + yo) / 2
        zt = zc + r * 1.035 * COS8
        B.box(pre + "_ledk", x, yl, r * 0.62, 0.30 * r, zt - 0.006, zt + 0.0015, m["black"], bevel=0.0, tags=tags)
        B.box(pre + "_led", x, yl, r * 0.44, 0.17 * r, zt - 0.004, zt + 0.003, led(ammo, led_s), bevel=0.0,
              tags=tags)
    rf = rfk * r
    og = ogive_to(r, yo, yt0, rf, n=8)
    if ammo == "ap":
        k = len(og) // 2
        lathe_y(pre + "_og", og[:k + 1], m["comp_d"], tags, x=x, zc=zc)
        ring_y(pre + "_ice", og[k][1] - 0.007, og[k][1] + 0.007, og[k][0] * 1.07, paint("ap", 0.10, 0.9), tags, x=x,
               zc=zc)
        lathe_y(pre + "_cap", og[k:], m["graph"], tags, x=x, zc=zc)
        rt = og[-1][0]
        lathe_y(pre + "_pen", [(rt * 0.95, yt0 - 0.004), (rt * 0.85, yt0 + 0.45 * lt * r), (rt * 0.40, y1 - 0.08 * r),
                               (0.0, y1)], m["steel"], tags, x=x, zc=zc)
        return yo
    lathe_y(pre + "_og", og, m["ogive"], tags, x=x, zc=zc)
    if ammo == "he":
        ring_y(pre + "_seat", yt0 - 0.006, yt0 + 0.012, rf * 1.12, m["steel"], tags, x=x, zc=zc)
        lathe_y(pre + "_fz", [(rf, yt0 + 0.012), (rf * 0.94, yt0 + 0.55 * lt * r), (rf * 0.72, y1)], m["steel"],
                tags, x=x, zc=zc)
        ring_y(pre + "_sens", yt0 + 0.45 * lt * r, yt0 + 0.70 * lt * r, rf * 0.97, m["black"], tags, x=x, zc=zc)
    elif ammo == "sap":
        ring_y(pre + "_crimp", yt0 - 0.012, yt0 + 0.010, rf * 1.08, m["steel"], tags, x=x, zc=zc, ch=0.003)
        lathe_y(pre + "_cap", dome(yt0 + 0.008, y1, rf, p=3.0, n=6), m["graph"], tags, x=x, zc=zc)
    elif ammo == "frag":
        ring_y(pre + "_fz", yt0 - 0.006, y1 - 0.012, rf * 1.04, m["steel"], tags, x=x, zc=zc, ch=0.004)
        lathe_y(pre + "_lens", dome(y1 - 0.016, y1, rf * 0.74, p=3.0, n=4), m["lens"], tags, x=x, zc=zc)
    elif ammo == "ac":
        ring_y(pre + "_skr", yt0 - 0.014, yt0 + 0.012, rf * 1.22, m["gold"], tags, x=x, zc=zc, ch=0.003)
        lathe_y(pre + "_sk", dome(yt0 + 0.008, y1, rf * 0.96, p=1.8, n=5), m["lens"], tags, x=x, zc=zc)
        # canards de ouro (2 laterais, vistos de cima) no ombro da ogiva
        yc0 = yo + 0.25 * r
        sp = r * 1.55
        for s in (-1, 1):
            poly = [(x + s * r * 0.55, yc0 + 1.15 * r), (x + s * sp, yc0 + 0.45 * r), (x + s * sp, yc0),
                    (x + s * r * 0.55, yc0 - 0.10 * r)]
            if s < 0:
                poly = list(reversed(poly))
            fin_y(f"{pre}_cn{s}", poly, zc - 0.006, zc + 0.012, m["gold"], tags)
    return yo


# ============================================================================ carregadores (familia cartuchos)
# Unidade: ~0.60 x 0.94, frente = +Y, altura maxima ~0.27. Exoesqueleto (STYLE 1.1): bandeja de nucleo escuro por
# baixo de tudo; placa traseira clara de bisel duplo (pega embutida + 2 pastilhas da cor); um VAO escuro transversal
# com a fenda de LED da cor da municao; duas bochechas claras em cunha nas laterais; e as granadas do nivel S deitadas
# na bandeja com os narizes passando da boca (a do meio adiantada: a ponta vira uma seta).
MAG_HW = 0.30                      # meia largura das cascas
MAG_Y0, MAG_Y1 = -0.445, 0.30      # costas / frente da bandeja
PLATE_Y1 = -0.245                  # fim da placa traseira nas laterais (a borda da frente e uma divisa)
CHEV = 0.065                       # avanco da divisa no meio (a fenda de LED vira uma seta "^" para a frente)
GAP = 0.072                        # largura do vao do LED (em y)
PLATE_Z = 0.245                    # altura da placa traseira (antes do painel)
TRAY_Z = 0.10                      # topo da bandeja (as granadas apoiam aqui)
MAG_ROUNDS = {   # n, raio, passo, base, ponta, avanco da do meio
    "he": (3, 0.064, 0.142, -0.13, 0.425, 0.035),
    "ap": (3, 0.058, 0.140, -0.13, 0.465, 0.0),
    "sap": (3, 0.066, 0.144, -0.13, 0.405, 0.03),
    "ac": (2, 0.068, 0.222, -0.13, 0.445, 0.0),
    "frag": (3, 0.070, 0.146, -0.13, 0.375, 0.0),
}
MAG_H = PLATE_Z + 0.022            # altura total (camada de cima da pilha apoia aqui)


def _chev_y(x, y_side):
    """y da divisa em x (y_side nas laterais, y_side + CHEV no meio)."""
    return y_side + CHEV * (1 - abs(x) / MAG_HW)


def magazine(M, Xm, tags, ammo, led_s=1.0, round_led=0.0):
    K, A, S = Xm["core"], Xm["armor"], Xm["steel"]
    hw = MAG_HW
    # ---- bandeja de nucleo escuro (moldura escura em volta das cascas; frente em cunha baixa)
    core = [(-hw + 0.04, MAG_Y0), (hw - 0.04, MAG_Y0), (hw + 0.012, MAG_Y0 + 0.05), (hw + 0.012, 0.21),
            (hw - 0.06, MAG_Y1), (-hw + 0.06, MAG_Y1), (-hw - 0.012, 0.21), (-hw - 0.012, MAG_Y0 + 0.05)]
    B.plate("mg_core", core, 0.0, TRAY_Z, K, slope=0.012, tags=tags)
    # ---- granadas do nivel S
    n, r, pitch, y0, y1, lead = MAG_ROUNDS[ammo]
    xs = [(i - (n - 1) / 2) * pitch for i in range(n)]
    zc = TRAY_Z + r * 0.92
    for i, x in enumerate(xs):
        dy = lead if abs(x) < 1e-6 else 0.0
        round_s(f"mg_r{i}", Xm, tags, ammo, x, zc, r, y0 + dy, y1 + dy, led_s=round_led)
    # ---- bochechas laterais em cunha (casca clara de bisel duplo)
    cx0 = max(xs) + r + 0.018
    zt = zc + r * COS8 + 0.016
    gy1 = PLATE_Y1 + GAP                                  # borda da frente do vao (nas laterais)
    cheek = [(cx0, _chev_y(cx0, gy1)), (hw, gy1), (hw, 0.19), (hw - 0.05, 0.265), (cx0, 0.265)]
    for s in (-1, 1):
        poly = cheek if s > 0 else Mo.mirror(cheek)
        ca, cp = B.shard(f"mg_cheek{s}", poly, TRAY_Z - 0.03, zt, A, slope=0.016, groove=0.008, panel_h=0.012,
                         tags=tags)
        # linha de painel transversal na bochecha (quebra a cada ~0.3, STYLE 1.8)
        for t in (ca, cp):
            if t is not None:
                B.cut(t, [B.box(f"mg_chl{s}{t.name}", s * (cx0 + hw) / 2, 0.06, hw - cx0 + 0.02, 0.016, zt - 0.03,
                                0.6, K, bevel=0.0)])
        # labio de aco na boca, sobre a granada de fora
        B.box(f"mg_lip{s}", s * (cx0 - 0.010), 0.232, 0.034, 0.05, zt - 0.014, zt + 0.010, S, bevel=0.004, tags=tags)
    # ---- vao escuro em divisa com a fenda de LED da cor da municao (entre a placa de tras e as bochechas)
    ang = math.degrees(math.atan2(CHEV, hw))
    for sd in (-1, 1):
        cx = sd * hw / 2
        cy = _chev_y(cx, PLATE_Y1 + GAP / 2)
        B.rbox(f"mg_ledbed{sd}", cx, cy, hw + 0.02, GAP - 0.01, TRAY_Z - 0.01, TRAY_Z + 0.03, Xm["black"],
               rot=-sd * ang, bevel=0.0, tags=tags)
        B.rbox(f"mg_led{sd}", sd * (hw / 2 - 0.005), _chev_y(sd * (hw / 2 - 0.005), PLATE_Y1 + GAP / 2),
               hw - 0.07, 0.030, TRAY_Z + 0.03, TRAY_Z + 0.042, led(ammo, led_s) if led_s > 0 else paint(ammo),
               rot=-sd * ang, bevel=0.0, tags=tags)
    # ---- placa traseira (casca clara de bisel duplo) com a borda da frente em divisa
    blk = [(-hw + 0.05, MAG_Y0 + 0.005), (hw - 0.05, MAG_Y0 + 0.005), (hw, MAG_Y0 + 0.055), (hw, PLATE_Y1),
           (0.0, PLATE_Y1 + CHEV), (-hw, PLATE_Y1), (-hw, MAG_Y0 + 0.055)]
    ba, bp = B.shard("mg_blk", blk, 0.0, PLATE_Z, A, slope=0.03, groove=0.015, panel_h=0.022, tags=tags)
    targets = [t for t in (ba, bp) if t is not None]
    # pega embutida nas costas (entalhe escuro com a barra de aco)
    for t in targets:
        B.cut(t, [B.box(f"mg_grip{t.name}", 0, MAG_Y0 - 0.02, 0.22, 0.13, TRAY_Z + 0.03, 0.6, K, bevel=0.0)])
    B.box("mg_gripbar", 0, MAG_Y0 + 0.02, 0.20, 0.026, PLATE_Z - 0.06, PLATE_Z - 0.03, S, bevel=0.006, tags=tags)
    # 2 pastilhas da cor nos cantos (rebaixo preto + tinta): a cor tambem le com a pilha em camadas
    for s in (-1, 1):
        cy = (MAG_Y0 + PLATE_Y1) / 2 + 0.02
        for t in targets:
            B.cut(t, [B.box(f"mg_chipc{s}{t.name}", s * 0.19, cy, 0.075, 0.075, PLATE_Z - 0.012, 0.6, K, bevel=0.0)])
        B.box(f"mg_chipb{s}", s * 0.19, cy, 0.075, 0.075, PLATE_Z - 0.022, PLATE_Z - 0.011, Xm["black"], bevel=0.0,
              tags=tags)
        B.box(f"mg_chip{s}", s * 0.19, cy, 0.05, 0.05, PLATE_Z - 0.012, PLATE_Z + 0.002, paint(ammo, 0.16),
              bevel=0.004, tags=tags)
    if ammo == "ac":
        # estojo premium: tampas de canto de OURO nos 4 cantos (le a 1x mesmo na pilha)
        for s in (-1, 1):
            c = [(s * (hw - 0.09), MAG_Y0 + 0.005), (s * (hw - 0.05), MAG_Y0 + 0.005), (s * hw, MAG_Y0 + 0.055),
                 (s * hw, MAG_Y0 + 0.115), (s * (hw - 0.09), MAG_Y0 + 0.115)]
            c = c if s < 0 else list(reversed(c))
            B.plate(f"mg_gcb{s}", c, 0.0, PLATE_Z + 0.035, Xm["gold"], slope=0.014, tags=tags)
            f = [(s * (hw - 0.075), 0.15), (s * hw, 0.15), (s * hw, 0.19), (s * (hw - 0.05), 0.265),
                 (s * (hw - 0.075), 0.265)]
            f = f if s < 0 else list(reversed(f))
            B.plate(f"mg_gcf{s}", f, TRAY_Z - 0.03, zt + 0.02, Xm["gold"], slope=0.012, tags=tags)


# pilha dos carregadores (unit_scale 0.5): 1 no centro, 2 lado a lado, 3 e 4 em duas fileiras de costas uma para a
# outra (as placas traseiras no meio, os narizes nas bordas), 5 e 6 com a camada de cima deitada sobre as placas
MAG_SCALE = 0.50
_CX, _RY = 0.168, 0.243
_HT = MAG_H * MAG_SCALE
MAG_LAYOUT = {
    1: [(0, 0, 0)],
    2: [(-_CX, 0, 0), (_CX, 0, 0)],
    3: [(-_CX, _RY, 0), (_CX, _RY, 0), (0, -_RY, 0)],
    4: [(-_CX, _RY, 0), (_CX, _RY, 0), (-_CX, -_RY, 0), (_CX, -_RY, 0)],
    5: [(-_CX, _RY, 0), (_CX, _RY, 0), (-_CX, -_RY, 0), (_CX, -_RY, 0), (0, 0, _HT)],
    6: [(-_CX, _RY, 0), (_CX, _RY, 0), (-_CX, -_RY, 0), (_CX, -_RY, 0), (-_CX, 0, _HT), (_CX, 0, _HT)],
}
# 0,1 = fileira da frente; 2,3 = fileira de tras girada 180 (placas no meio); 4,5 = camada de cima
MAG_ROT = [0, 1.5, 180, 181.5, -1.0, 1.0]
# a pilha de 3 tem so 1 unidade atras (indice 2: girada 180) e a de 5 tem 1 na camada de cima (indice 4)


def mag_part(pid, ammo, stack, accent="amber"):
    """PART de um carregador 2.0 (pilha = max_stack_size do SPEC 2.0)."""
    return {"id": pid, "kind": "resource", "accent": accent, "max_stack": stack, "unit_scale": MAG_SCALE,
            "icon_scale": 0.84, "stack_layout": {k: v for k, v in MAG_LAYOUT.items() if k <= stack},
            "stack_rot": MAG_ROT}


# ============================================================================ celulas (familia celulas)
# Unidade deitada ao longo de Y (~0.36 x 0.94, altura ~0.34): corpo SEXTAVADO de blindagem clara (topo plano) com
# juntas escuras, colares de reforco mais largos (nervuras na silhueta), tampas escuras sextavadas e bornes de aco.
#   plasma: janela longa recortada no topo com o nucleo de plasma CIANO segmentado num leito preto;
#   pem   : 3 aneis de bobina de COBRE (assinatura PEM) e duas janelas curtas com a faixa de LED AZUL baixa.
CELL_R = 0.155             # raio do corpo sextavado (meia largura nas quinas)
CELL_ZC = 0.165            # altura do eixo
CELL_Y = 0.30              # corpo em |y| <= CELL_Y
CELL_SCALE = 0.52
CELL_PITCH = 0.235
CELL_STAG = 0.026
CELL_LAYOUT = {
    1: [(0, 0, 0)],
    2: [(-CELL_PITCH / 2, CELL_STAG, 0), (CELL_PITCH / 2, -CELL_STAG, 0)],
    3: [(-CELL_PITCH, -CELL_STAG, 0), (0, CELL_STAG, 0), (CELL_PITCH, -CELL_STAG, 0)],
    4: [(-1.5 * CELL_PITCH, CELL_STAG, 0), (-CELL_PITCH / 2, -CELL_STAG, 0), (CELL_PITCH / 2, CELL_STAG, 0),
        (1.5 * CELL_PITCH, -CELL_STAG, 0)],
}


def hex_y(name, ya, yb, r, mat, tags, zc=CELL_ZC, ch=0.0):
    """Prisma sextavado de topo plano deitado em Y (de ya a yb), com chanfro ch nas bordas."""
    prof = [(r - ch, ya), (r, ya + ch), (r, yb - ch), (r - ch, yb)] if ch > 0 else [(r, ya), (r, yb)]
    return lathe_y(name, prof, mat, tags, zc=zc, verts=6, a0=0.0)


def cell(M, Xm, tags, kind, led_s=1.0):
    K, KM, A, S = Xm["core"], Xm["core_mid"], Xm["armor"], Xm["steel"]
    R, zc = CELL_R, CELL_ZC
    zt = zc + R * math.cos(math.radians(30))          # topo plano do sextavado
    # espinha escura (fecha as juntas) e tampas escuras sextavadas com o borne de aco
    hex_y("cl_spine", -CELL_Y - 0.02, CELL_Y + 0.02, R * 0.70, K, tags)
    for sy in (-1, 1):
        ya, yb = sorted((sy * CELL_Y, sy * (CELL_Y + 0.105)))
        hex_y(f"cl_cap{sy}", ya, yb, R * 0.88, Xm["dark"], tags, ch=0.014)
        ta, tb = sorted((sy * (CELL_Y + 0.10), sy * (CELL_Y + 0.15)))
        ring_y(f"cl_term{sy}", ta, tb, 0.052, S, tags, zc=zc, ch=0.008)
        ring_y(f"cl_termk{sy}", ta + 0.012, tb - 0.012, 0.056, K, tags, zc=zc)
        # LED de estado na tampa (fenda curta num rebaixo preto)
        yl = sy * (CELL_Y + 0.052)
        ztc = zc + R * 0.88 * math.cos(math.radians(30))
        B.box(f"cl_capk{sy}", 0, yl, 0.085, 0.036, ztc - 0.008, ztc + 0.002, Xm["black"], bevel=0.0, tags=tags)
        B.box(f"cl_capl{sy}", 0, yl, 0.06, 0.016, ztc - 0.004, ztc + 0.004,
              led("plasma" if kind == "plasma" else "pem", 0.9 * led_s), bevel=0.0, tags=tags)
    if kind == "plasma":
        # corpo em 3 segmentos de blindagem clara (juntas escuras) + 2 colares de reforco mais largos
        segs = [(-CELL_Y, -0.205), (-0.19, 0.19), (0.205, CELL_Y)]
        objs = []
        for i, (ya, yb) in enumerate(segs):
            objs.append(hex_y(f"cl_body{i}", ya, yb, R, A, tags, ch=0.012))
        for sy in (-1, 1):
            hex_y(f"cl_col{sy}", *sorted((sy * 0.235, sy * 0.275)), R * 1.10, A, tags, ch=0.010)
        # janela longa no topo do segmento do meio: leito preto + nucleo ciano segmentado
        win = B.box("cl_wcut", 0, 0, 0.10, 0.33, zt - 0.05, zt + 0.3, K, bevel=0.0)
        B.cut(objs[1], [win])
        B.box("cl_wbed", 0, 0, 0.10, 0.33, zt - 0.056, zt - 0.046, Xm["black"], bevel=0.0, tags=tags)
        ring_y("cl_core", -0.15, 0.15, 0.034, led("plasma", 1.0 * led_s), tags, zc=zt - 0.05, verts=8)
        for i, yy in enumerate((-0.075, 0.0, 0.075)):
            ring_y(f"cl_sep{i}", yy - 0.008, yy + 0.008, 0.040, KM, tags, zc=zt - 0.05, verts=8)
        # filete claro de aco nas bordas da janela (moldura de bisel)
        for sx in (-1, 1):
            B.box(f"cl_wrim{sx}", sx * 0.058, 0, 0.012, 0.31, zt - 0.006, zt + 0.004, S, bevel=0.0, tags=tags)
    else:
        # corpo de blindagem clara inteiro + 3 aneis de bobina de cobre (mais largos: costelas na silhueta)
        body = hex_y("cl_body", -CELL_Y, CELL_Y, R, A, tags, ch=0.012)
        cuts = []
        for i, yy in enumerate((-0.085, 0.085)):
            cuts.append(B.box(f"cl_wcut{i}", 0, yy, 0.09, 0.075, zt - 0.034, zt + 0.3, K, bevel=0.0))
        B.cut(body, cuts)
        for i, yy in enumerate((-0.085, 0.085)):
            B.box(f"cl_wbed{i}", 0, yy, 0.09, 0.075, zt - 0.040, zt - 0.029, Xm["black"], bevel=0.0, tags=tags)
            B.box(f"cl_wled{i}", 0, yy, 0.058, 0.040, zt - 0.034, zt - 0.024, led("pem", 0.85 * led_s), bevel=0.0,
                  tags=tags)
        for i, yy in enumerate((-0.19, 0.0, 0.19)):
            # bobina: nucleo escuro + 3 espiras de cobre redondas (le como fio enrolado, nao como faixa pintada)
            ring_y(f"cl_cuk{i}", yy - 0.048, yy + 0.048, R * 1.04, K, tags, zc=zc, verts=12, a0=0.0)
            for j, dy in enumerate((-0.03, 0.0, 0.03)):
                B.torus(f"cl_cu{i}{j}", 0, yy + dy, zc, R * 1.06, 0.016, Xm["copper"], tags=tags).rotation_euler = \
                    (math.pi / 2, 0, 0)


def cell_part(pid, kind, stack, accent):
    return {"id": pid, "kind": "resource", "accent": accent, "max_stack": stack, "unit_scale": CELL_SCALE,
            "icon_scale": 0.84, "stack_layout": {k: v for k, v in CELL_LAYOUT.items() if k <= stack},
            "stack_rot": [0, 0, 0, 0, 0, 0]}


# ============================================================================ cargas de missil (familia misseis)
# Unidade deitada ao longo de +Y (~0.26 x 0.92): o missil 2.0 do tipo em miniatura (a mesma tinta de faixa do missil em
# voo e dos narizes nos lancadores: Mo.band_mat) num BERCO (trenó escuro por baixo + 2 garras claras dos lados).
# Pilha de 10 (SPEC 2.0 render_kinds.resource.stack_layout_7_10.missile_charges): fileira de 5 com passo 0.14 e a
# 2a camada de 5 desencontrada por cima. O modelo e feito ao longo de Y, entao o giro da pilha e ~0 (o spec da 90
# para um modelo ao longo de X: o resultado e o mesmo).
MSL_SCALE = 0.50
MSL_LAYOUT = {int(k): [tuple(p) for p in v] for k, v in {
    1: [[-0.28, 0.0, 0.0]],
    2: [[-0.28, 0.0, 0.0], [-0.14, 0.0, 0.0]],
    3: [[-0.28, 0.0, 0.0], [-0.14, 0.0, 0.0], [0.0, 0.0, 0.0]],
    4: [[-0.28, 0.0, 0.0], [-0.14, 0.0, 0.0], [0.0, 0.0, 0.0], [0.14, 0.0, 0.0]],
    5: [[-0.28, 0.0, 0.0], [-0.14, 0.0, 0.0], [0.0, 0.0, 0.0], [0.14, 0.0, 0.0], [0.28, 0.0, 0.0]],
    6: [[-0.28, 0.0, 0.0], [-0.14, 0.0, 0.0], [0.0, 0.0, 0.0], [0.14, 0.0, 0.0], [0.28, 0.0, 0.0],
        [-0.21, 0.0, 0.14]],
    7: [[-0.28, 0.0, 0.0], [-0.14, 0.0, 0.0], [0.0, 0.0, 0.0], [0.14, 0.0, 0.0], [0.28, 0.0, 0.0],
        [-0.21, 0.0, 0.14], [-0.07, 0.0, 0.14]],
    8: [[-0.28, 0.0, 0.0], [-0.14, 0.0, 0.0], [0.0, 0.0, 0.0], [0.14, 0.0, 0.0], [0.28, 0.0, 0.0],
        [-0.21, 0.0, 0.14], [-0.07, 0.0, 0.14], [0.07, 0.0, 0.14]],
    9: [[-0.28, 0.0, 0.0], [-0.14, 0.0, 0.0], [0.0, 0.0, 0.0], [0.14, 0.0, 0.0], [0.28, 0.0, 0.0],
        [-0.21, 0.0, 0.14], [-0.07, 0.0, 0.14], [0.07, 0.0, 0.14], [0.21, 0.0, 0.14]],
    10: [[-0.28, 0.0, 0.0], [-0.14, 0.0, 0.0], [0.0, 0.0, 0.0], [0.14, 0.0, 0.0], [0.28, 0.0, 0.0],
         [-0.21, 0.0, 0.14], [-0.07, 0.0, 0.14], [0.07, 0.0, 0.14], [0.21, 0.0, 0.14], [0.35, 0.0, 0.14]],
}.items()}
MSL_ROT = [0, 2, -2, 1, -1, 0]       # spec stack_rot (90, 92, 88, 91, 89, ...) menos os 90 do modelo ao longo de X
MSL_ZC = 0.085                       # altura do eixo (o berco fica por baixo)
BAND = {"msl_he": "he", "msl_cluster": "cluster", "msl_emp": "emp"}


def rot_y(ob, x=0.0):
    """Gira um objeto feito ao longo de +X para +Y (giro em Z de 90 graus) e o desloca em x."""
    ob.rotation_euler = (0.0, 0.0, math.pi / 2)
    ob.location = (x, 0.0, 0.0)
    return ob


def sleeve_y(name, y0, y1, r, mat, tags, zc, dv=None, front=True, rear=True):
    """Luva em divisa (Mo.chevron_sleeve, "escamas") ao longo de +Y."""
    return rot_y(Mo.chevron_sleeve(name, y0, y1, r, mat, tags, dv=dv, front=front, rear=rear, zc=zc))


def _cradle(Xm, tags, y0, y1, hw, yokes, zc, r):
    """Berco: treno escuro por baixo do missil e garras claras dos dois lados (le como 'no berco' a 1x)."""
    B.box("cr_sled", 0, (y0 + y1) / 2, 0.075, y1 - y0, 0.0, zc - r * 0.55, Xm["core_mid"], bevel=0.006, tags=tags)
    for i, yy in enumerate(yokes):
        for s in (-1, 1):
            poly = [(s * (r * 0.70), yy - 0.032), (s * hw, yy - 0.022), (s * hw, yy + 0.022), (s * (r * 0.70), yy + 0.032)]
            if s < 0:
                poly = list(reversed(poly))
            B.plate(f"cr_y{i}{s}", poly, 0.0, zc + r * 0.25, Xm["armor"], slope=0.008, tags=tags)


def charge(M, Xm, tags, kind, led_s=1.0):
    K, KM, A = Xm["core"], Xm["core_mid"], Xm["armor"]
    zc = MSL_ZC
    nose = Xm["nose"]
    band = Mo.band_mat(BAND[kind])
    if kind == "msl_he":
        # Jararaca: flecha fina, luvas em divisa claras com frestas escuras, faixa ambar, ogiva clara e o domo escuro
        # do buscador com o anel ambar; 2 aletas em flecha na cauda
        r = 0.058
        _cradle(Xm, tags, -0.30, 0.20, 0.098, (-0.17, 0.10), zc, r)
        ring_y("ms_noz", -0.455, -0.415, r * 0.78, KM, tags, zc=zc, ch=0.006)
        ring_y("ms_tail", -0.42, -0.25, r * 0.96, A, tags, zc=zc, ch=0.006)
        # 3 luvas claras em divisa com as frestas largas mostrando o nucleo de GRAFITE (as "escamas" da Jararaca 2.0)
        for i, (ya, yb) in enumerate(((-0.25, -0.14), (-0.115, -0.005), (0.02, 0.105))):
            sleeve_y(f"ms_sl{i}", ya, yb, r, nose, tags, zc, dv=r * 0.9)
        ring_y("ms_core", -0.26, 0.12, r * 0.93, Xm["graph"], tags, zc=zc)
        ring_y("ms_band", 0.125, 0.17, r * 1.03, band, tags, zc=zc, ch=0.004)
        og = ogive_to(r, 0.17, 0.385, r * 0.44, n=8)
        lathe_y("ms_og", og, nose, tags, zc=zc)
        ring_y("ms_skr", 0.383, 0.392, r * 0.47, Xm["steel"], tags, zc=zc)
        lathe_y("ms_sk", dome(0.39, 0.445, r * 0.44, p=1.6, n=5), Xm["lensm"], tags, zc=zc)
        for s in (-1, 1):
            fin = [(s * r * 0.6, -0.30), (s * 0.125, -0.38), (s * 0.125, -0.425), (s * r * 0.6, -0.41)]
            if s < 0:
                fin = list(reversed(fin))
            fin_y(f"ms_fin{s}", fin, zc - 0.012, zc + 0.010, A, tags)
        # LED ambar num rebaixo da luva de tras
        zt = zc + r * COS8
        B.box("ms_ledk", 0, -0.205, 0.034, 0.05, zt - 0.006, zt + 0.004, Xm["black"], bevel=0.0, tags=tags)
        B.box("ms_led", 0, -0.205, 0.020, 0.034, zt - 0.003, zt + 0.006, led("msl_he", 1.0 * led_s), bevel=0.0,
              tags=tags)
    elif kind == "msl_cluster":
        # Piranha: portador GORDO com 2 baias escuras (narizes dos minimisseis a mostra), faixa amarela e o nariz em 4
        # PETALAS (fresta escura no eixo) com a ponta amarela
        r = 0.082
        _cradle(Xm, tags, -0.30, 0.16, 0.122, (-0.20, 0.08), zc + 0.01, r)
        zc = zc + 0.01
        ring_y("ms_noz", -0.455, -0.415, r * 0.66, KM, tags, zc=zc, ch=0.006)
        ring_y("ms_tail", -0.42, -0.31, r * 0.80, A, tags, zc=zc, ch=0.008)
        body = ring_y("ms_body", -0.31, 0.12, r, nose, tags, zc=zc, ch=0.008)
        zt = zc + r * COS8
        cuts = []
        for i, yy in enumerate((-0.19, -0.035)):
            cuts.append(B.box(f"ms_bay{i}", 0, yy, 0.09, 0.105, zt - 0.03, zt + 0.3, K, bevel=0.0))
        B.cut(body, cuts)
        for i, yy in enumerate((-0.19, -0.035)):
            B.box(f"ms_bayb{i}", 0, yy, 0.09, 0.105, zt - 0.036, zt - 0.026, Xm["black"], bevel=0.0, tags=tags)
            for j, xx in enumerate((-0.022, 0.022)):
                lathe_y(f"ms_mini{i}{j}", [(0.014, yy - 0.03), (0.014, yy + 0.01), (0.0, yy + 0.04)], nose, tags,
                        x=xx, zc=zt - 0.03 + 0.008, verts=6, a0=0.0)
        ring_y("ms_band", 0.12, 0.17, r * 1.03, band, tags, zc=zc, ch=0.004)
        ring_y("ms_hinge", 0.17, 0.19, r * 0.98, KM, tags, zc=zc)
        og = ogive_to(r * 0.97, 0.19, 0.40, r * 0.30, n=8)
        nob = lathe_y("ms_og", og, nose, tags, zc=zc)
        # fresta de cima das petalas (no eixo) + as frestas dos lados (entalhes no contorno)
        B.cut(nob, [B.box("ms_slit", 0, 0.30, 0.020, 0.24, zc + r * 0.35, zc + 0.5, K, bevel=0.0),
                    B.box("ms_slitl", -r, 0.30, 0.04, 0.22, zc - 0.012, zc + 0.012, K, bevel=0.0),
                    B.box("ms_slitr", r, 0.30, 0.04, 0.22, zc - 0.012, zc + 0.012, K, bevel=0.0)])
        B.box("ms_slitk", 0, 0.29, 0.020, 0.20, zc, zc + r * 0.4, Xm["black"], bevel=0.0, tags=tags)
        B.box("ms_slitled", 0, 0.29, 0.008, 0.16, zc + r * 0.38, zc + r * 0.45, led("msl_cluster", 0.6 * led_s),
              bevel=0.0, tags=tags)
        lathe_y("ms_tip", [(r * 0.30, 0.398), (r * 0.22, 0.42), (0.0, 0.445)], band, tags, zc=zc)
        for s in (-1, 1):
            fin = [(s * r * 0.7, -0.33), (s * 0.122, -0.39), (s * 0.122, -0.43), (s * r * 0.7, -0.42)]
            if s < 0:
                fin = list(reversed(fin))
            fin_y(f"ms_fin{s}", fin, zc - 0.012, zc + 0.010, A, tags)
    else:
        # Poraque (PEM): corpo ESCURO com 3 bobinas de COBRE e frestas azuis, 2 laminas longas e varridas claras dos
        # lados, faixa azul e o nariz escuro com o olho azul
        r = 0.060
        _cradle(Xm, tags, -0.30, 0.20, 0.098, (-0.24, 0.12), zc, r)
        ring_y("ms_noz", -0.455, -0.415, r * 0.80, KM, tags, zc=zc, ch=0.006)
        ring_y("ms_body", -0.42, 0.13, r, Xm["dark"], tags, zc=zc, ch=0.006)
        for i, yy in enumerate((-0.20, -0.07, 0.06)):
            for j, dy in enumerate((-0.016, 0.016)):
                B.torus(f"ms_cu{i}{j}", 0, yy + dy, zc, r * 1.02, 0.0135, Xm["copper"], tags=tags).rotation_euler = \
                    (math.pi / 2, 0, 0)
        zt = zc + r * COS8
        for i, yy in enumerate((-0.135, -0.005)):
            B.box(f"ms_ledk{i}", 0, yy, 0.034, 0.05, zt - 0.006, zt + 0.004, Xm["black"], bevel=0.0, tags=tags)
            B.box(f"ms_led{i}", 0, yy, 0.020, 0.032, zt - 0.003, zt + 0.006, led("msl_emp", 1.0 * led_s), bevel=0.0,
                  tags=tags)
        ring_y("ms_band", 0.13, 0.175, r * 1.04, band, tags, zc=zc, ch=0.004)
        og = ogive_to(r, 0.175, 0.40, r * 0.42, n=8)
        lathe_y("ms_og", og, Xm["dark"], tags, zc=zc)
        lathe_y("ms_eye", dome(0.395, 0.445, r * 0.42, p=1.8, n=5), led("msl_emp", 0.9 * led_s), tags, zc=zc)
        for s in (-1, 1):
            fin = [(s * r * 0.6, -0.05), (s * 0.12, -0.33), (s * 0.12, -0.41), (s * r * 0.6, -0.30)]
            if s < 0:
                fin = list(reversed(fin))
            fin_y(f"ms_fin{s}", fin, zc - 0.010, zc + 0.008, A, tags)


def charge_part(pid, kind, accent):
    return {"id": pid, "kind": "resource", "accent": accent, "max_stack": 10, "unit_scale": MSL_SCALE,
            "icon_scale": 0.92, "stack_layout": MSL_LAYOUT, "stack_rot": MSL_ROT}


# ============================================================================ ogiva nuclear (Iara)
# Unidade ao longo de +Y (~0.40 x 0.96): ogiva GORDA da Iara 2.0 (o unico missil de blindagem escura): base com colar
# claro de bisel, corpo de grafite com a faixa VERDE larga num sulco e a janela de contencao com o nucleo verde atras
# da grade de aco, colar claro no pescoco, ogiva clara com o TREVO de 3 cunhas escuras sobre disco verde (STYLE 7 / 11.6:
# permitido no recurso nuclear) e o sensor escuro na ponta. Sem divisas e sem amarelo.
NK_R = 0.175
NK_ZC = 0.185
NK_SCALE = 0.86
NK_LAYOUT = {1: [(0, 0, 0)], 2: [(-0.205, 0, 0), (0.205, 0, 0)]}


def warhead(M, Xm, tags, led_s=1.0):
    K, KM, A, S = Xm["core"], Xm["core_mid"], Xm["armor"], Xm["steel"]
    R, zc = NK_R, NK_ZC
    green = paint("nuke", 0.22, 0.75)
    # base: anel de aco escuro + colar claro de bisel (octogono)
    ring_y("nk_base", -0.475, -0.445, R * 0.82, KM, tags, zc=zc, ch=0.008)
    ring_y("nk_col0", -0.445, -0.36, R * 1.04, A, tags, zc=zc, ch=0.014)
    ring_y("nk_col0k", -0.405, -0.395, R * 1.06, K, tags, zc=zc)
    # corpo de grafite
    body = ring_y("nk_body", -0.36, 0.10, R, Xm["dark"], tags, zc=zc, ch=0.006)
    zt = zc + R * COS8
    # faixa verde larga num sulco (aros escuros) + uma fina perto do pescoco
    ring_y("nk_gk0", -0.315, -0.235, R * 1.015, K, tags, zc=zc)
    ring_y("nk_g0", -0.307, -0.243, R * 1.03, green, tags, zc=zc, ch=0.004)
    ring_y("nk_g1", 0.055, 0.075, R * 1.02, green, tags, zc=zc)
    # janela de contencao no topo: leito preto, nucleo verde aceso, grade de aco
    B.cut(body, [B.box("nk_wc", 0, -0.075, 0.14, 0.20, zt - 0.05, zt + 0.4, K, bevel=0.0)])
    B.box("nk_wb", 0, -0.075, 0.14, 0.20, zt - 0.056, zt - 0.046, Xm["black"], bevel=0.0, tags=tags)
    B.box("nk_core", 0, -0.075, 0.07, 0.16, zt - 0.05, zt - 0.036, led("nuke_core", 0.75 * led_s), bevel=0.0, tags=tags)
    for i, yy in enumerate((-0.135, -0.095, -0.055, -0.015)):
        B.box(f"nk_grid{i}", 0, yy, 0.14, 0.012, zt - 0.036, zt - 0.022, S, bevel=0.0, tags=tags)
    B.box("nk_gridv", 0, -0.075, 0.012, 0.20, zt - 0.036, zt - 0.024, S, bevel=0.0, tags=tags)
    # LEDs verdes de estado na base (fenda curta)
    ztc = zc + R * 1.04 * COS8
    B.box("nk_lk", 0, -0.415, 0.10, 0.03, ztc - 0.008, ztc + 0.002, Xm["black"], bevel=0.0, tags=tags)
    for i in range(3):
        B.box(f"nk_l{i}", -0.03 + i * 0.03, -0.415, 0.016, 0.016, ztc - 0.006, ztc + 0.004, led("nuke", 0.8 * led_s),
              bevel=0.0, tags=tags)
    # colar claro do pescoco
    ring_y("nk_col1", 0.10, 0.155, R * 1.05, A, tags, zc=zc, ch=0.012)
    ring_y("nk_col1k", 0.122, 0.132, R * 1.07, K, tags, zc=zc)
    # ogiva clara + trevo embutido (disco verde, cunhas escuras)
    og = ogive_to(R * 0.98, 0.155, 0.43, R * 0.26, n=10)
    ob = lathe_y("nk_og", og, Xm["nose"], tags, zc=zc)
    ty = 0.245
    rs = None
    for rr, yy in og:
        if yy >= ty + 0.075:
            rs = rr
            break
    Mo.trefoil_inlay("nk_tref", [ob], 0.0, ty, zc + (rs or R * 0.8) * COS8, 0.062, 0.016, M, tags, wedge_mat=K,
                     disc_mat=green, disc_r=0.078, hub_mat=K, a0=90, surface_r=rs or R * 0.8)
    # sensor escuro na ponta (lente) com aro de aco
    ring_y("nk_tipr", 0.425, 0.44, R * 0.30, S, tags, zc=zc)
    lathe_y("nk_tip", dome(0.438, 0.478, R * 0.25, p=1.8, n=5), Xm["lens"], tags, zc=zc)


# ============================================================================ projetil da railgun (Tupa)
# Unidade ao longo de +Y (~0.32 x 0.96): o dardo de tungstenio claro da Tupa num BERCO claro (2 trilhos de bisel duplo
# sobre um leito escuro, com travas LARANJA: os detalhes laranja da referencia do usuario), 4 colares EM AZUIS (a paleta
# nova da railgun: azul [45,115,255] / claro [110,175,255]) com a fenda acesa, ponta quente ouro-branca e 6 aletas
# curtas na cauda. Nunca cobre, nunca chama.
SLUG_SCALE = 0.86
SLUG_LAYOUT = {1: [(0, 0, 0)], 2: [(-0.16, 0, 0), (0.16, 0, 0)]}


def slug(M, Xm, tags, led_s=1.0):
    K, KM, A = Xm["core"], Xm["core_mid"], Xm["armor"]
    zc = 0.115
    r = 0.030
    blue = paint("slug", 0.14, 0.7)
    orange = paint("orange", 0.10, 0.85)
    # berco: leito escuro + 2 trilhos claros de bisel duplo com as pontas em cunha
    B.box("sg_bed", 0, -0.04, 0.12, 0.74, 0.0, zc - r * 0.4, KM, bevel=0.006, tags=tags)
    for s in (-1, 1):
        rail = [(s * 0.062, -0.40), (s * 0.118, -0.37), (s * 0.13, -0.33), (s * 0.13, 0.25), (s * 0.105, 0.31),
                (s * 0.062, 0.31)]
        if s < 0:
            rail = list(reversed(rail))
        ra, rp = B.shard(f"sg_rail{s}", rail, 0.0, zc + 0.012, A, slope=0.014, groove=0.007, panel_h=0.010,
                         tags=tags)
        # travas laranja atravessando o trilho (2 por lado) + LED azul de estado na ponta do trilho
        for i, yy in enumerate((-0.22, 0.13)):
            for t in (ra, rp):
                if t is not None:
                    B.cut(t, [B.box(f"sg_lc{s}{i}{t.name}", s * 0.096, yy, 0.09, 0.05, zc - 0.02, 0.6, K, bevel=0.0)])
            B.box(f"sg_latch{s}{i}", s * 0.094, yy, 0.064, 0.038, zc - 0.03, zc + 0.016, orange, bevel=0.004,
                  tags=tags)
        B.box(f"sg_lk{s}", s * 0.096, 0.235, 0.024, 0.05, zc + 0.012, zc + 0.026, Xm["black"], bevel=0.0, tags=tags)
        B.box(f"sg_led{s}", s * 0.096, 0.235, 0.012, 0.036, zc + 0.016, zc + 0.030, led("slug", 1.0 * led_s),
              bevel=0.0, tags=tags)
    # dardo: haste de tungstenio claro
    ring_y("sg_rod", -0.43, 0.40, r, Xm["tung"], tags, zc=zc)
    lathe_y("sg_pen", [(r, 0.40), (r * 0.80, 0.43), (r * 0.35, 0.462), (0.0, 0.478)], Xm["steel"], tags, zc=zc)
    ring_y("sg_hot", 0.455, 0.47, r * 0.42, led("white", 0.6 * led_s), tags, zc=zc)
    # 4 colares EM azuis (labios anodizados + fenda acesa)
    for i, yy in enumerate((-0.21, -0.07, 0.07, 0.21)):
        ring_y(f"sg_ca{i}", yy - 0.032, yy - 0.006, r * 1.75, blue, tags, zc=zc, ch=0.004)
        ring_y(f"sg_cb{i}", yy + 0.006, yy + 0.032, r * 1.75, blue, tags, zc=zc, ch=0.004)
        ring_y(f"sg_cl{i}", yy - 0.006, yy + 0.006, r * 1.55, led("slug_hi", 0.9 * led_s), tags, zc=zc)
    # 6 aletas curtas na cauda (2 laterais + dorsal), grafite
    for s in (-1, 1):
        fin = [(s * r * 0.7, -0.33), (s * 0.075, -0.39), (s * 0.075, -0.43), (s * r * 0.7, -0.43)]
        if s < 0:
            fin = list(reversed(fin))
        fin_y(f"sg_fin{s}", fin, zc - 0.008, zc + 0.008, Xm["graph"], tags)
    B.box("sg_dors", 0, -0.385, 0.012, 0.09, zc, zc + 0.05, Xm["graph"], bevel=0.0, tags=tags)
