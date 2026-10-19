"""Misseis em voo do Bullet Strike: 22 sprites vistos de cima (kind "missiles", 64 px/tile).

Contrato: tools/blender/STYLE.md secoes 8.4 e 11 (CONTRATOS secao 3). Cada item e UM projetil com o nariz em +X,
centrado na origem, eixo = X (z = altura; o topo do corpo fica em z ~ raio). Os emissivos levam a etiqueta
(T, "lights") e vao para o atlas aditivo; no difuso eles saem apagados (lentes escuras). phase = k/frames escolhe o
quadro do atlas.

Mesma linguagem das torres: placas claras chanfradas sobre um nucleo escuro, divisas apontando para a frente, LEDs
no fundo de recessos escuros. As faixas usam Mo.band_mat(tipo) (o mesmo material dos narizes carregados nos
lancadores), entao o missil em voo bate com o do casulo. Identidade por tipo (o tipo se le pela SILHUETA):
  * Jararaca / Muricoca (HE, ambar): flecha fina com luvas em divisa ("escamas"), ogiva tangente com buscador
    escuro; he_l em 2 estagios (reforco com 4 aletas e anel de separacao com 3 pips que correm, sustentador com
    estrakes, faixa dupla).
  * Piranha (fragmentacao, amarela): cilindro gordo em baias com LEDs em sequencia, "boca" escura com anel de
    dentes (triangulos claros sobre preto) e nariz em petalas de fendas largas; fim com trilhos externos presos por
    presilhas e canards; filho = gota com olho amarelo e rabo de peixe bifurcado (estatico).
  * Carrapato (lapa, vermelha): luvas em divisa, 3 patas dobradas de cada lado, cabeca-ima hexagonal com anel
    vermelho e 2 pares de pincas; carga grudada = disco hexagonal com 6 patas, casca clara em 2 placas, cupula
    vermelha e anel de 8 LEDs (contagem de 10 quadros, Clamp).
  * Taturana (napalm, laranja): corrente de tanques redondos (12 lados) com costelas escuras e visores grandes de
    "fogo liquido" alternados, nariz em cupula com bico aspersor de 3 bicos em leque; fim com tanques laterais e
    aletas largas e baixas.
  * Poraque (P.E.M., azul): barbatanas-fita em corrente de escamas chanfradas, luva em divisa com pips azuis, pilha
    de bobinas de COBRE (Mo.copper_mat, o mesmo material do bs_mag_emp) com frestas azuis, buscador escuro com
    olho azul e aneis de aco; fim com 2 pontas de arco (>= 2 px).
  * Boto (torpedo isca, branco): cilindro branco grande de 16 lados (sombreamento plano, tinta fosca propria),
    nariz de golfinho liso (a tinta do nariz do casulo) com fenda escura embutida, estrobos em carcacas elevadas,
    anel de carenagem na cauda (2 barras + escora) e bomba-jato; estagio 1 com luva de reforco escura e 2
    propulsores laterais de nariz escuro; fim com bolha escura do sonar; isca cinza com colar de aco e nariz
    escuro, sem faixa, estrobo rapido.
  * Iara (torpedo nuclear, verde): o UNICO missil de blindagem escura, ogiva gorda em 3 camadas (placa de cima
    ESCURA com aro claro e o trevo grande de cunhas pretas sobre disco verde, placas dos ombros com divisas
    verde/preto, nucleo escuro), 2 faixas verdes LARGAS (tinta verde com a faixa acesa no meio) que respiram de
    verdade (G ~140/200/245/200, sem estourar), janela do nucleo com grade de aco, bocal triplo (3 sinos que
    aparecem atras das aletas, com aneis verdes e gargantas escuras), 4 aletas escuras solidas com bordo de ataque
    claro e anel de carenagem; estagio 1 com 2 propulsores laterais. Nunca amarelo/preto (regra do mod desde a
    Boiuna). Isca cinza sem divisas nem trevo.
Um missil do fim e mais comprido, mais gordo e ganha estrutura (estagio, mais aletas, baias, bobinas, garras).
"""

import math

import bs3d as B
import models as Mo


def _it(L, W, frames, fps, nozzle_x=None, anchors=None, wrap=None):
    d = {"canvas_tiles": [L, W], "frames": frames, "fps": fps, "wrap": wrap, "mask": False,
         "anchors": anchors or {}}
    if nozzle_x is not None:
        d["nozzle_x"] = nozzle_x
    return d


# chaves, telas, quadros e fps = tabela de arte dos misseis (missile_art_table.json / bullet_strike_missile_fx.json)
PART = {
    "id": "rafaeltessaro.bs_missiles",
    "kind": "missiles",
    "px_per_tile": 64,
    "accent": "amber",
    "items": {
        "he_s": _it(1.0, 0.375, 2, 4, -0.47, {"seeker": [0.46, 0.0]}),
        "napalm_s": _it(1.0, 0.4375, 2, 3, -0.47, {"seeker": [0.46, 0.0]}),
        "he_m": _it(1.75, 0.625, 2, 4, -0.86, {"seeker": [0.83, 0.0]}),
        "cluster_m": _it(1.75, 0.75, 3, 8, -0.86, {"seeker": [0.83, 0.0]}),
        "limpet_m": _it(1.75, 0.75, 2, 3, -0.86, {"seeker": [0.40, 0.0]}),
        "napalm_m": _it(1.75, 0.75, 2, 3, -0.86, {"seeker": [0.84, 0.0]}),
        "emp_m": _it(1.75, 0.75, 4, 12, -0.86, {"seeker": [0.60, 0.0]}),
        "torpedo_m": _it(2.75, 1.0, 2, 2, -1.38, {"seeker": [1.22, 0.0], "warhead": [0.10, 0.0]}),
        "he_l": _it(2.5, 0.875, 3, 6, -1.18, {"seeker": [1.20, 0.0]}),
        "cluster_l": _it(2.5, 1.0, 4, 8, -1.18, {"seeker": [1.20, 0.0]}),
        "limpet_l": _it(2.5, 1.0, 2, 3, -1.18, {"seeker": [0.53, 0.0]}),
        "napalm_l": _it(2.5, 1.0, 2, 3, -1.18, {"seeker": [1.21, 0.0]}),
        "emp_l": _it(2.5, 1.0, 4, 12, -1.18, {"seeker": [0.85, 0.0]}),
        "torpedo_l": _it(3.25, 1.25, 2, 2, -1.63, {"seeker": [1.43, 0.0], "warhead": [0.06, 0.0]}),
        "nuclear_l": _it(3.75, 1.5, 4, 6, -1.86, {"seeker": [1.83, 0.0], "warhead": [0.995, 0.0],
                                                  "radiation": [0.995, 0.0]}),
        "cluster_child": _it(0.75, 0.375, 1, 0, -0.3, {"seeker": [0.31, 0.0]}),
        "limpet_charge": _it(1.0, 1.0, 10, 4, None, {"warhead": [0.0, 0.0]}, wrap="Clamp"),
        "torpedo_wh_m": _it(2.25, 1.0, 2, 2, -1.13, {"seeker": [0.97, 0.0], "warhead": [-0.15, 0.0]}),
        "torpedo_wh_l": _it(2.75, 1.25, 2, 2, -1.35, {"seeker": [1.18, 0.0], "warhead": [-0.19, 0.0]}),
        "torpedo_decoy": _it(1.75, 0.625, 2, 6, -0.88, {"seeker": [0.82, 0.0]}),
        "nuclear_wh_l": _it(3.1, 1.5, 4, 6, -1.53, {"seeker": [1.50, 0.0], "warhead": [0.67, 0.0],
                                                    "radiation": [0.67, 0.0]}),
        "nuclear_decoy": _it(2.0, 0.75, 2, 6, -0.98, {"seeker": [0.95, 0.0]}),
    },
}

# ============================================================================ materiais e utilidades
LED_RGB = {"amber": Mo.AMBER, "yellow": (1.0, 0.78, 0.11), "red": (1.0, 0.10, 0.06), "orange": (1.0, 0.26, 0.02),
           "blue": (0.10, 0.42, 1.0), "white": (0.82, 0.88, 1.0), "green": Mo.GREEN,
           # verde da Iara: pouco vermelho e quase nada de azul (matiz ~99 graus, como o Mo.GREEN), para o pico da
           # respiracao ficar verde vivo sem virar lima/amarelo quando somado ao corpo e ao GlowSprite
           "iara": (0.15, 1.0, 0.01)}


def _lm(color, s):
    """Emissivo de LED/faixa com forca s (um material por forca: o cache do bs3d e por nome). Forcas baixas
    (<= ~1.5) para o laranja/verde/azul nao estourarem em branco/amarelo na vista Standard (STYLE secao 9)."""
    return B.mat_glow(f"msl_{color}_{int(round(s * 100)):03d}", LED_RGB[color], s)


def _mats(M):
    return {
        "nose": Mo.nose_paint("nose", Mo.NOSE_LIGHT),                 # mesma tinta dos narizes dos lancadores
        "white": Mo.nose_paint("torp_white", (0.53, 0.555, 0.60)),    # Boto (igual ao nariz do torpedo no casulo)
        # corpo do Boto: a MESMA cor do nariz do casulo, mas fosco (rough 0.6) e com um pouco de desgaste, para nao
        # ler como brinquedo de plastico; nome proprio, entao os narizes dos lancadores (torp_white) nao mudam
        "white_body": B.mat_paint("torp_white_body", (0.53, 0.555, 0.60), rough=0.6, metal=0.12, wear=0.12,
                                  grime=0.05, scale=6),
        "iara_cap": Mo.nose_paint("torp_iara", (0.40, 0.42, 0.45)),   # nariz da Iara (igual ao do casulo)
        "teeth": B.mat_paint("msl_teeth", (0.70, 0.71, 0.72), rough=0.3, metal=0.1, wear=0.0, grime=0.0, scale=6),
        # blindagem escura da Iara (sem desgaste: em malha pequena o desgaste clareia a peca inteira)
        "dark": B.mat_paint("iara_dark", (0.075, 0.078, 0.086), rough=0.40, metal=0.45, wear=0.0, grime=0.03,
                            scale=5),
        "grey": B.mat_paint("decoy_grey", (0.24, 0.245, 0.255), rough=0.42, metal=0.3, wear=0.0, grime=0.04,
                            scale=5),
        "eye": B.mat_metal("fry_eye", (0.95, 0.72, 0.06), rough=0.5, metal=0.0),
    }


def _a0(n):
    """Giro do anel do lathe que deixa uma FACE plana em cima (n lados)."""
    return (math.pi / 2 - math.pi / n) % (2 * math.pi / n)


def _ap(r, n=8):
    """Altura da face de cima de um prisma de n lados de raio r (apotema)."""
    return r * math.cos(math.pi / n)


def _tube(name, x0, x1, r, mat, tags, r1=None, verts=8, zc=0.0):
    """Tubo facetado (n lados, topo plano, sombreamento plano como os canos da familia) no eixo X."""
    return Mo.lathe(name, [(r, x0), (r if r1 is None else r1, x1)], mat, tags, verts=verts, axis="X", zc=zc,
                    a0=_a0(verts), smooth=False)


def _prof(name, prof, mat, tags, verts=8, smooth=False, zc=0.0):
    return Mo.lathe(name, prof, mat, tags, verts=verts, axis="X", zc=zc, a0=_a0(verts) if not smooth else 0.0,
                    smooth=smooth)


def _pill(name, x0, x1, r, mat, tags, ch=0.18, verts=8):
    """Segmento de tanque/baia: tubo com as pontas chanfradas (le como pecas separadas)."""
    c = min(r * ch, (x1 - x0) * 0.25)
    return _prof(name, [(r * 0.86, x0), (r, x0 + c), (r, x1 - c), (r * 0.86, x1)], mat, tags, verts=verts)


def _dome(x0, x1, r0, p=2.0, n=10, r_end=0.0):
    """Perfil eliptico de x0 (raio r0) ate x1 (raio r_end; 0 = ponta arredondada)."""
    out = []
    for k in range(n + 1):
        t = k / n
        r = r0 * max(0.0, 1 - t ** p) ** (1 / p)
        out.append((max(r, r_end) if k < n else r_end, x0 + (x1 - x0) * t))
    return out


def _nose(name, R, x0, x1, mat, tip_mat, tags, tip_r=0.016, verts=16):
    """Ogiva tangente clara de x0 a x1 com a ponta (buscador) escura a partir do raio tip_r."""
    prof = Mo.ogive(R, x1 - x0, x0, tip_r=tip_r)
    og = _prof(name, prof, mat, tags, verts=verts, smooth=True)
    rt, xt = prof[-1]
    _prof(name + "_tip", [(rt * 1.04, xt - 0.004), (0.0, x1)], tip_mat, tags, verts=verts, smooth=True)
    return og, prof


def _r_at(prof, x):
    for (ra, xa), (rb, xb) in zip(prof, prof[1:]):
        if xa <= x <= xb:
            return ra + (rb - ra) * (x - xa) / max(1e-9, xb - xa)
    return prof[-1][0] if x > prof[-1][1] else prof[0][0]


def _my(poly):
    return [(x, -y) for x, y in poly]


def _fins(name, poly, z, th, mat, tags, panel_mat=None, slope=0.012, groove=0.008, ph=0.008):
    """Par de aletas horizontais (as 2 visiveis de cima) em lasca com bisel duplo. poly no lado +y; a raiz entra
    no corpo (alfa conectado)."""
    out = []
    for s, nm in ((1, "l"), (-1, "r")):
        p = [(x, s * y) for x, y in poly]
        out.append(B.shard(f"{name}_{nm}", p, z - th / 2, z + th / 2, mat, slope=slope, groove=groove, panel_h=ph,
                           panel_mat=panel_mat, tags=tags))
    return out


def _strip(pts, w):
    """Poligono de uma tira de meia largura w (numero ou lista por ponto) em volta da polilinha pts."""
    n = len(pts)
    ws = list(w) if isinstance(w, (list, tuple)) else [w] * n
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        left.append((x + nx * ws[i], y + ny * ws[i]))
        right.append((x - nx * ws[i], y - ny * ws[i]))
    return left + right[::-1]


def _slot(targets, name, cx, cy, sx, sy, ztop, depth, M, tags):
    """Recesso escuro de paredes verticais (recorte nos alvos) com leito preto; devolve a altura do fundo.
    Os alvos sao tubos de lathe (sem bisel), entao o corte nao cai nas armadilhas de chanfro da secao 9."""
    zf = ztop - depth
    for j, t in enumerate(targets):
        if t is not None:
            B.cut(t, [B.box(f"{name}_c{j}", cx, cy, sx, sy, zf, ztop + 0.3, M["black"], bevel=0.0)])
    B.box(name + "_bed", cx, cy, sx, sy, zf - 0.008, zf + 0.001, M["black"], bevel=0.0, tags=tags)
    return zf


def _pip(name, x, y, zf, sx, sy, mat, LT, h=0.008):
    return B.box(name, x, y, sx, sy, zf + 0.0005, zf + h, mat, bevel=0.0, tags=LT)


def _facet(name, x0, x1, hw, ap, theta, th, mat, tags, panel_mat=None, ch=0.02, cf=0.03, slope=0.012,
           groove=0.008, ph=0.008):
    """Placa em lasca (bisel duplo) sobre uma face de um prisma de 8 lados: desenhada em cima (z = ap) e girada
    theta graus em torno do eixo X (0 = face de cima, +-45 = faces dos ombros). Cantos de tras chanfrados em ch e
    os da frente em cf (apontando para o nariz)."""
    poly = [(x0, -hw + ch), (x0 + ch, -hw), (x1 - cf, -hw), (x1, -hw + cf), (x1, hw - cf), (x1 - cf, hw),
            (x0 + ch, hw), (x0, hw - ch)]
    a, b = B.shard(name, poly, ap - 0.004, ap + th, mat, slope=slope, groove=groove, panel_h=ph, panel_mat=panel_mat,
                   tags=tags)
    for o in (a, b):
        if o is not None:
            o.rotation_euler = (math.radians(theta), 0.0, 0.0)
    return a, b


def _panels(name, x0, x1, ap, thetas, rim, panel, tags, hw=0.048, pitch=0.42, gap=0.035):
    """Placas de blindagem em lasca nas faces (thetas) de um trecho [x0, x1] de um prisma de 8 lados, quebradas em
    paineis de ~pitch com frestas (uma quebra estrutural a cada 0.3-0.5 tile, STYLE 1.8)."""
    n = max(1, int(round((x1 - x0) / pitch)))
    ln = (x1 - x0 - gap * (n - 1)) / n
    for i in range(n):
        a = x0 + i * (ln + gap)
        for th in thetas:
            _facet(f"{name}{i}_{th}", a, a + ln, hw, ap, th, 0.014, rim, tags, panel_mat=panel, ch=0.018, cf=0.03,
                   slope=0.010, groove=0.007, ph=0.008)


def _clamps(name, cx, lx, ys, ap, mat, tags, w=0.03):
    """Presilhas de aco atravessando uma faixa (anel) de um prisma de 8 lados de apotema ap, nas posicoes ys:
    seguem a superficie (topo plano e faces inclinadas) e ficam um pouco acima dela."""
    for i, y in enumerate(ys):
        zs = min(ap, ap * math.sqrt(2.0) - abs(y))
        B.box(f"{name}{i}", cx, y, lx, w, zs - 0.04, zs + 0.012, mat, bevel=0.004, tags=tags)


def _moved(ob, y=0.0, z=0.0):
    ob.location = (0.0, y, z)
    return ob


# ============================================================================ Jararaca / Muricoca (HE, ambar)
def _he(M, X, tags, LT, f, tier):
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    band = Mo.band_mat("he")
    if tier == "s":
        # Muricoca: 2 luvas, 1 LED, aletas pequenas
        R = 0.042
        Mo.lathe("h_noz", [(0.026, -0.48), (0.034, -0.445)], S, tags, verts=12, axis="X")
        _tube("h_core", -0.455, 0.20, 0.036, KM, tags)
        Mo.chevron_sleeve("h_sl0", -0.40, -0.16, R * 1.08, A, tags, dv=0.03, rear=False)
        s1 = Mo.chevron_sleeve("h_sl1", -0.13, 0.12, R * 1.08, A, tags, dv=0.03)
        _tube("h_band", 0.148, 0.195, R * 1.12, band, tags)
        _nose("h_og", R * 1.1, 0.195, 0.48, X["nose"], K, tags, tip_r=0.016, verts=16)
        _fins("h_fin", [(-0.30, 0.02), (-0.385, 0.15), (-0.44, 0.15), (-0.445, 0.02)], 0.0, 0.016, A, tags)
        zf = _slot([s1], "h_led", 0.0, 0.0, 0.048, 0.040, _ap(R * 1.08), 0.014, M, tags)
        _pip("h_pip", 0.0, 0.0, zf, 0.034, 0.030, _lm("amber", 1.6 if f == 0 else 0.15), LT)
        return
    if tier == "m":
        # Jararaca: 3 luvas, fenda com 3 pips, canards, aletas grandes com garras escuras na raiz
        R = 0.068
        Mo.lathe("h_noz", [(0.040, -0.855), (0.052, -0.80)], S, tags, verts=12, axis="X")
        _tube("h_core", -0.81, 0.30, 0.058, KM, tags)
        dv = 0.045
        xs = [(-0.70, -0.42), (-0.39, -0.11), (-0.08, 0.215)]
        sl = [Mo.chevron_sleeve(f"h_sl{i}", a, b, R * 1.06, A, tags, dv=dv, rear=i > 0) for i, (a, b) in enumerate(xs)]
        _tube("h_band", 0.245, 0.30, R * 1.10, band, tags)
        og, prof = _nose("h_og", R * 1.08, 0.30, 0.855, X["nose"], K, tags, tip_r=0.02)
        _fins("h_fin", [(-0.48, 0.04), (-0.70, 0.27), (-0.80, 0.27), (-0.80, 0.04)], 0.0, 0.022, A, tags)
        for s in (1, -1):
            B.box(f"h_clamp{s}", -0.63, s * 0.074, 0.26, 0.026, -0.03, 0.03, KM, bevel=0.004, tags=tags)
        _fins("h_can", [(0.44, 0.03), (0.37, 0.125), (0.34, 0.125), (0.345, 0.03)], 0.0, 0.014, A, tags)
        zf = _slot([sl[1]], "h_led", -0.25, 0.0, 0.17, 0.044, _ap(R * 1.06), 0.02, M, tags)
        for i in range(3):
            on = (i != 1) if f == 0 else (i == 1)
            _pip(f"h_pip{i}", -0.305 + i * 0.055, 0.0, zf, 0.036, 0.030, _lm("amber", 1.6 if on else 0.15), LT)
        return
    # he_l: DOIS ESTAGIOS (reforco + sustentador)
    Rb, R = 0.095, 0.085
    Mo.lathe("h_noz", [(0.064, -1.23), (0.080, -1.17), (0.072, -1.13)], S, tags, verts=12, axis="X")
    Mo.lathe("h_nozr", [(0.084, -1.155), (0.084, -1.135)], K, tags, verts=12, axis="X")
    _pill("h_boost", -1.14, -0.47, Rb, A, tags, ch=0.25)
    for k, x in enumerate((-0.92, -0.70)):
        _tube(f"h_bseam{k}", x - 0.01, x + 0.01, Rb * 1.01, K, tags)
    _fins("h_bfin", [(-0.78, 0.05), (-1.04, 0.405), (-1.17, 0.405), (-1.15, 0.05)], 0.0, 0.026, A, tags)
    for s in (1, -1):
        B.box(f"h_bclamp{s}", -0.98, s * 0.10, 0.30, 0.03, -0.035, 0.035, KM, bevel=0.004, tags=tags)
    # anel de separacao escuro com 3 pips que correm
    ring = _tube("h_sep", -0.48, -0.395, Rb * 1.06, KM, tags)
    zf = _slot([ring], "h_seps", -0.4375, 0.0, 0.056, 0.13, _ap(Rb * 1.06), 0.022, M, tags)
    for i in range(3):
        _pip(f"h_spip{i}", -0.4375, (i - 1) * 0.042, zf, 0.036, 0.030, _lm("amber", 1.6 if i == f else 0.12), LT)
    # sustentador: 3 luvas, estrakes longos, faixa dupla
    _tube("h_core", -0.40, 0.66, 0.075, KM, tags)
    xs = [(-0.38, -0.10), (-0.07, 0.21), (0.24, 0.52)]
    sl = [Mo.chevron_sleeve(f"h_sl{i}", a, b, R * 1.06, A, tags, dv=0.05, rear=i > 0) for i, (a, b) in enumerate(xs)]
    _fins("h_strake", [(0.42, 0.05), (0.30, 0.128), (-0.24, 0.128), (-0.33, 0.05)], -0.01, 0.014, M["armor_mid"],
          tags, slope=0.012, groove=0.008)
    zf2 = _slot([sl[1]], "h_led", 0.07, 0.0, 0.18, 0.044, _ap(R * 1.06), 0.022, M, tags)
    for i in range(3):
        _pip(f"h_pip{i}", 0.015 + i * 0.055, 0.0, zf2, 0.036, 0.030, _lm("amber", 1.6 if i == f else 0.12), LT)
    _tube("h_band0", 0.575, 0.615, R * 1.12, band, tags)
    _tube("h_band1", 0.645, 0.680, R * 1.12, band, tags)
    _tube("h_bandk", 0.60, 0.66, R * 1.02, K, tags)
    _nose("h_og", R * 1.10, 0.68, 1.23, X["nose"], K, tags, tip_r=0.022)


# ============================================================================ Piranha (fragmentacao, amarela)
def _petal_nose(name, R, x0, x1, thetas, sw, X, M, tags, mouth=0.0):
    """Nariz em petalas: ogiva clara cortada por fendas largas que passam pelo eixo (angulos thetas em torno de X)
    sobre uma ogiva interna preta (o escuro aparece nas fendas). mouth > 0: a casca clara comeca mouth tile depois
    da ogiva preta, abrindo uma "boca" escura onde ficam os dentes."""
    prof = Mo.ogive(R, x1 - x0, x0, tip_r=0.012)
    shell = [(r * 0.97, x) for r, x in prof if x >= x0 + mouth]
    og = _prof(name, [(shell[0][0], shell[0][1] - 0.004)] + shell + [(0.0, x1)], X["nose"], tags, verts=24,
               smooth=True)
    _prof(name + "_in", [(r * 0.84 if x >= x0 + mouth else r, x) for r, x in prof] + [(0.0, x1 - 0.01)], M["black"],
          tags, verts=16, smooth=True)
    cut = []
    for j, th in enumerate(thetas):
        c = B.box(f"{name}_seam{j}", (x0 + x1) / 2 + 0.03, 0.0, x1 - x0 + 0.1, sw, -0.6, 0.6, M["black"], bevel=0.0)
        c.rotation_euler = (math.radians(th), 0.0, 0.0)
        cut.append(c)
    B.cut(og, cut)
    return og, prof


def _teeth(name, x0, x1, R, n, X, tags):
    """Anel de dentes: triangulos claros apontando para o nariz numa fileira atravessando o topo."""
    tw = 2 * R * 0.82 / n
    for i in range(n):
        yc = (i - (n - 1) / 2) * tw
        zs = math.sqrt(max(0.0, R * R - yc * yc))
        tri = [(x0, yc - tw * 0.48), (x0, yc + tw * 0.48), (x1, yc)]
        B.loft(f"{name}{i}", tri, tri, zs - 0.035, zs + 0.012, X["teeth"], bevel=0.0, tags=tags)


def _cluster(M, X, tags, LT, f, tier):
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    band = Mo.band_mat("cluster")
    if tier == "m":
        R, n_bay, x_noz, x_tail, x_bays, x_nose = 0.145, 3, -0.855, -0.63, (-0.615, 0.28), 0.855
        fin = [(-0.64, 0.08), (-0.70, 0.27), (-0.80, 0.27), (-0.805, 0.08)]
        thetas, sw, n_teeth = (45, -45), 0.042, 5
    else:
        R, n_bay, x_noz, x_tail, x_bays, x_nose = 0.195, 4, -1.23, -0.93, (-0.915, 0.42), 1.23
        fin = [(-0.92, 0.10), (-1.0, 0.38), (-1.14, 0.38), (-1.15, 0.10)]
        thetas, sw, n_teeth = (0, 60, -60), 0.046, 7
    Mo.lathe("p_noz", [(R * 0.36, x_noz), (R * 0.45, x_noz + 0.06)], S, tags, verts=12, axis="X")
    _prof("p_tail", [(R * 0.50, x_noz + 0.045), (R * 0.92, x_tail)], KM, tags)
    _fins("p_fin", fin, 0.0, 0.024, A, tags)
    _tube("p_core", x_tail - 0.01, x_bays[1] + 0.02, R * 0.88, KM, tags)
    g = 0.03
    blen = (x_bays[1] - x_bays[0] - g * (n_bay - 1)) / n_bay
    for i in range(n_bay):
        a = x_bays[0] + i * (blen + g)
        bay = _pill(f"p_bay{i}", a, a + blen, R, A, tags, ch=0.12)
        cx = a + blen / 2
        zf = _slot([bay], f"p_led{i}", cx, 0.0, 0.056, 0.048, _ap(R), 0.022, M, tags)
        _pip(f"p_pip{i}", cx, 0.0, zf, 0.040, 0.034, _lm("yellow", 1.5 if i == f else 0.1), LT)
        # dobradicas das portas da baia (linhas escuras curtas nos ombros)
        for s in (1, -1):
            B.box(f"p_hinge{i}{s}", cx, s * R * 0.62, blen * 0.62, 0.016, _ap(R) * 0.55, _ap(R) * 0.86, K,
                  bevel=0.0, tags=tags)
    if tier == "l":
        # fim: trilhos escuros POR FORA da silhueta (y = +-(R+0.03), na meia altura) presos por uma presilha de aco
        # em cada baia, e um 2o jogo de aletas (canards) na frente: estrutura que se ve a 1x
        yr = R + 0.03
        xr0, xr1 = x_bays[0] + 0.03, x_bays[1] - 0.27
        for s in (1, -1):
            B.box(f"p_rail{s}", (xr0 + xr1) / 2, s * yr, xr1 - xr0, 0.04, R * 0.5 - 0.035, R * 0.5 + 0.02, KM,
                  bevel=0.006, tags=tags)
            for i in range(n_bay):
                cx = x_bays[0] + i * (blen + g) + blen * 0.5
                if cx < xr1 - 0.03:
                    B.box(f"p_rcl{i}{s}", cx, s * (R * 0.80 + yr) / 2, 0.042, yr - R * 0.80 + 0.04,
                          R * 0.5 - 0.02, R * 0.5 + 0.035, S, bevel=0.005, tags=tags)
        _fins("p_can", [(x_bays[1] - 0.03, 0.12), (x_bays[1] - 0.17, 0.33), (x_bays[1] - 0.24, 0.33),
                        (x_bays[1] - 0.25, 0.12)], 0.0, 0.02, A, tags)
    xb = x_bays[1]
    sc = R / 0.145
    _tube("p_band", xb, xb + 0.045 * sc, R * 1.03, band, tags)
    xr0 = xb + 0.045 * sc
    xr1 = xr0 + 0.04 * sc
    # boca: anel preto + dentes claros que avancam sobre o miolo preto exposto (a casca de petalas comeca depois)
    _tube("p_tring", xr0, xr1, R * 1.05, M["black"], tags, verts=16)
    _teeth("p_tooth", xr0 + 0.004, xr1 + 0.075 * sc, R * 1.0, n_teeth, X, tags)
    _petal_nose("p_og", R, xr1, x_nose, thetas, sw, X, M, tags, mouth=0.065 * sc)


def _fry(M, X, tags):
    """Filho da Piranha: gota clara, nariz rombudo escuro com olho amarelo pintado, rabo de peixe bifurcado.
    Estatico (sem atlas): o olho e tinta."""
    A, KM, S = M["armor"], M["core_mid"], M["steel"]
    _prof("c_body", [(0.022, -0.25), (0.046, -0.16), (0.068, -0.04), (0.076, 0.06), (0.074, 0.13)], X["nose"], tags,
          verts=16, smooth=True)
    _tube("c_band", 0.10, 0.135, 0.078, Mo.band_mat("cluster"), tags, verts=16)
    _prof("c_head", _dome(0.13, 0.335, 0.074, p=2.2, n=8), KM, tags, verts=16, smooth=True)
    B.cyl("c_eye", 0.215, 0.0, 0.066, 0.024, 0.014, X["eye"], axis="Z", verts=12, bevel=0.0, tags=tags)
    Mo.lathe("c_noz", [(0.018, -0.30), (0.026, -0.24)], S, tags, verts=10, axis="X")
    _fins("c_tail", [(-0.12, 0.02), (-0.335, 0.150), (-0.35, 0.115), (-0.25, 0.02)], 0.0, 0.016, A, tags,
          slope=0.008, groove=0.006, ph=0.006)


# ============================================================================ Carrapato (lapa, vermelha)
def _limpet(M, X, tags, LT, f, tier):
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    band = Mo.band_mat("limpet")
    late = tier == "l"
    s = 1.3 if late else 1.0
    R = 0.095 * s
    if not late:
        x_noz, x_core1 = -0.855, 0.22
        sleeves = [(-0.66, -0.25), (-0.22, 0.14)]
        legs_x = (-0.52, -0.30, -0.08)
        fin = [(-0.62, 0.05), (-0.70, 0.21), (-0.79, 0.21), (-0.79, 0.05)]
        xh0, xh1 = 0.215, 0.355
        outer = [(0.28, 0.07), (0.40, 0.20), (0.53, 0.27), (0.66, 0.255), (0.75, 0.19)]
        outer_tip = [(0.75, 0.19), (0.80, 0.13), (0.79, 0.075)]
        inner = [(0.36, 0.05), (0.44, 0.115), (0.53, 0.14), (0.61, 0.11)]
        inner_tip = [(0.61, 0.11), (0.645, 0.075), (0.635, 0.045)]
        w_out, w_in = 0.020, 0.015
    else:
        x_noz, x_core1 = -1.23, 0.30
        sleeves = [(-1.02, -0.66), (-0.625, -0.265), (-0.23, 0.205)]
        legs_x = (-0.78, -0.44, -0.10)
        fin = [(-0.92, 0.07), (-1.02, 0.29), (-1.15, 0.29), (-1.155, 0.07)]
        xh0, xh1 = 0.30, 0.49
        outer = [(0.38, 0.09), (0.55, 0.28), (0.74, 0.37), (0.93, 0.35), (1.06, 0.26)]
        outer_tip = [(1.06, 0.26), (1.14, 0.17), (1.135, 0.085)]
        inner = [(0.48, 0.07), (0.60, 0.16), (0.73, 0.195), (0.85, 0.15)]
        inner_tip = [(0.85, 0.15), (0.90, 0.10), (0.89, 0.055)]
        w_out, w_in = 0.026, 0.019
    Mo.lathe("l_noz", [(R * 0.46, x_noz), (R * 0.60, x_noz + 0.055 * s)], S, tags, verts=12, axis="X")
    _tube("l_core", x_noz + 0.04, x_core1, R * 0.9, KM, tags)
    _fins("l_fin", fin, 0.0, 0.02, A, tags)
    sl = [Mo.chevron_sleeve(f"l_sl{i}", a, b, R * 1.05, A, tags, dv=0.06 * s, rear=i > 0)
          for i, (a, b) in enumerate(sleeves)]
    # patas dobradas (3 de cada lado): quadril dentro do corpo, joelho para fora e para a frente, pe para tras
    for i, x in enumerate(legs_x):
        for sy in (1, -1):
            pts = [(x, sy * R * 0.5), (x + 0.085 * s, sy * (R + 0.075 * s)), (x - 0.07 * s, sy * (R + 0.115 * s))]
            B.loft(f"l_leg{i}{sy}", _strip(pts, 0.019 * s), _strip(pts, 0.019 * s), -0.02 * s, 0.02 * s,
                   M["armor_mid"], bevel=0.004, tags=tags)
            B.cyl(f"l_knee{i}{sy}", pts[1][0], pts[1][1], 0.012 * s, 0.02 * s, 0.03 * s, S, axis="Z", verts=8,
                  bevel=0.003, tags=tags)
            if late:
                B.box(f"l_foot{i}{sy}", pts[2][0] - 0.02, pts[2][1], 0.06, 0.035, -0.02, 0.025, S, bevel=0.006,
                      tags=tags)
    # estrobos vermelhos na espinha (1 no meio, 2 no fim)
    zt = _ap(R * 1.05)
    strobes = [1] if not late else [0, 1]
    for k in strobes:
        a, b = sleeves[k]
        cx = (a + b) / 2
        zf = _slot([sl[k]], f"l_strb{k}", cx, 0.0, 0.056, 0.046, zt, 0.022, M, tags)
        _pip(f"l_spip{k}", cx, 0.0, zf, 0.040, 0.032, _lm("red", 1.6 if f == 0 else 0.1), LT)
    _tube("l_band", sleeves[-1][1] + 0.02, xh0 + 0.005, R * 1.08, band, tags)
    # cabeca-ima hexagonal escura + anel vermelho na face + almofada do ima
    _tube("l_head", xh0, xh1, R * 1.16, KM, tags, verts=6)
    _tube("l_hrim", xh0 + 0.02, xh0 + 0.045, R * 1.20, S, tags, verts=6)
    _prof("l_ring", [(R * 1.02, xh1 - 0.004), (R * 1.02, xh1 + 0.026 * s)], _lm("red", 1.3 if f == 1 else 0.2), LT,
          verts=24, smooth=True)
    _prof("l_pad", [(R * 0.86, xh1 + 0.02 * s), (R * 0.86, xh1 + 0.045 * s)], K, tags, verts=24, smooth=True)
    # pincas: par grande de fora e par pequeno de dentro, arqueiam para fora e fecham para dentro, pontas escuras
    for nm, pts, tip, w in (("l_po", outer, outer_tip, w_out), ("l_pi", inner, inner_tip, w_in)):
        for sy in (1, -1):
            p = [(x, sy * y) for x, y in pts]
            t = [(x, sy * y) for x, y in tip]
            ws = [w * 1.25] + [w] * (len(p) - 1)
            B.loft(f"{nm}{sy}", _strip(p, ws), _strip(p, ws), -0.012, 0.03, A, bevel=0.005, tags=tags)
            B.loft(f"{nm}t{sy}", _strip(t, [w, w * 0.8, w * 0.45]), _strip(t, [w, w * 0.8, w * 0.45]), -0.008, 0.026,
                   K, bevel=0.003, tags=tags)


def _limpet_charge(M, X, tags, LT, f):
    """Carga grudada no casco (vista de cima): disco hexagonal escuro, casca clara em 2 placas, cupula vermelha,
    6 patas com pes de aco e o anel de 8 LEDs da contagem (o quadro k acende k+1 LEDs; os 2 ultimos, o anel
    inteiro)."""
    A, KM, S = M["armor"], M["core_mid"], M["steel"]
    # patas: quadril sob o disco, joelho de aco, pe de aco
    for k in range(6):
        a = math.radians(30 + 60 * k)
        ca, sa = math.cos(a), math.sin(a)
        b = a + math.radians(9)
        pts = [(0.14 * ca, 0.14 * sa), (0.31 * math.cos(b), 0.31 * math.sin(b)), (0.415 * ca, 0.415 * sa)]
        B.loft(f"ch_leg{k}", _strip(pts, [0.026, 0.022, 0.018]), _strip(pts, [0.026, 0.022, 0.018]), 0.0, 0.05, KM,
               bevel=0.006, tags=tags)
        B.cyl(f"ch_knee{k}", pts[1][0], pts[1][1], 0.05, 0.026, 0.03, S, axis="Z", verts=8, bevel=0.004, tags=tags)
        B.cyl(f"ch_foot{k}", pts[2][0], pts[2][1], 0.02, 0.038, 0.04, S, axis="Z", verts=10, bevel=0.006, tags=tags)
    # disco hexagonal escuro com aro de aco
    hexp = [(0.245 * math.cos(math.radians(60 * i)), 0.245 * math.sin(math.radians(60 * i))) for i in range(6)]
    B.plate("ch_rim", hexp, 0.0, 0.05, S, slope=0.016, bevel=0.005, tags=tags)
    hexi = [(0.228 * math.cos(math.radians(60 * i)), 0.228 * math.sin(math.radians(60 * i))) for i in range(6)]
    puck = B.loft("ch_puck", hexi, B.offset_poly(hexi, 0.014), 0.03, 0.085, KM, bevel=0.004, tags=tags)
    # anel de 8 LEDs de 3 px (o 1o em cima da imagem, sentido horario); raio 0.170 = dentro do apotema do disco
    zt = 0.085
    leds = []
    for i in range(8):
        a = math.radians(90 - 45 * i)
        leds.append((0.170 * math.cos(a), 0.170 * math.sin(a)))
    cut = [B.box(f"ch_lc{i}", x, y, 0.054, 0.054, zt - 0.02, zt + 0.3, M["black"], bevel=0.0)
           for i, (x, y) in enumerate(leds)]
    B.cut(puck, cut)
    # vermelho com forca ~1 (acima disso o R estoura e o halo puxa para salmao); o miolo da cupula acende forte nos
    # 2 ultimos quadros (o "vai explodir")
    if f <= 7:
        lit = [1.0 if i <= f else 0.0 for i in range(8)]
        dome = 0.0
    else:
        lit = [1.15 if f == 8 else 1.4] * 8
        dome = 1.6 if f == 8 else 2.2
    for i, (x, y) in enumerate(leds):
        B.box(f"ch_lb{i}", x, y, 0.054, 0.054, zt - 0.028, zt - 0.019, M["black"], bevel=0.0, tags=tags)
        _pip(f"ch_led{i}", x, y, zt - 0.02, 0.046, 0.046, _lm("red", lit[i]), LT)
    # casca clara em 2 placas (fresta escura no meio), menor que o anel de LEDs
    half = [(x * 0.85, y * 0.85 if y > 0.02 else y) for x, y in
            [(-0.13, 0.014), (0.13, 0.014), (0.142, 0.06), (0.09, 0.128), (-0.09, 0.128), (-0.142, 0.06)]]
    for s in (1, -1):
        B.shard(f"ch_shell{s}", [(x, s * y) for x, y in half], 0.07, 0.115, A, slope=0.016, groove=0.01, panel_h=0.012,
                tags=tags)
    # cupula vermelha (tinta da faixa do Carrapato) com aro preto; o miolo dela acende nos 2 ultimos quadros
    B.cyl("ch_bez", 0.0, 0.0, 0.122, 0.062, 0.02, M["black"], axis="Z", verts=24, bevel=0.0, tags=tags)
    Mo.lathe("ch_dome", [(0.048, 0.128), (0.044, 0.142), (0.032, 0.154), (0.0, 0.16)], Mo.band_mat("limpet"), tags,
             verts=24)
    B.cyl("ch_core", 0.0, 0.0, 0.161, 0.03, 0.004, _lm("red", dome), axis="Z", verts=16, bevel=0.0, tags=LT)


# ============================================================================ Taturana (napalm, laranja)
def _napalm(M, X, tags, LT, f, tier):
    A, KM, S = M["armor"], M["core_mid"], M["steel"]
    band = Mo.band_mat("napalm")
    if tier == "s":
        R, n, x_noz, xs0, xs1, x_nose = 0.055, 3, -0.48, -0.37, 0.20, 0.48
        fin = [(-0.36, 0.03), (-0.40, 0.155), (-0.455, 0.155), (-0.455, 0.03)]
    elif tier == "m":
        R, n, x_noz, xs0, xs1, x_nose = 0.105, 5, -0.855, -0.66, 0.48, 0.855
        fin = [(-0.66, 0.06), (-0.72, 0.25), (-0.80, 0.25), (-0.80, 0.06)]
    else:
        R, n, x_noz, xs0, xs1, x_nose = 0.125, 6, -1.23, -0.98, 0.78, 1.23
        fin = [(-0.70, 0.08), (-0.96, 0.445), (-1.10, 0.445), (-1.12, 0.08)]
    s = R / 0.105
    Mo.lathe("t_noz", [(R * 0.50, x_noz), (R * 0.66, x_noz + 0.06 * max(s, 0.6))], S, tags, verts=12, axis="X")
    _prof("t_tail", [(R * 0.62, x_noz + 0.03), (R * 0.9, xs0)], KM, tags)
    _fins("t_fin", fin, 0.0, 0.018 if tier != "l" else 0.016, A, tags)
    _tube("t_core", xs0 - 0.01, xs1 + 0.01, R * 0.80, KM, tags)
    g = 0.03 * max(s, 0.8)
    seg = (xs1 - xs0 - g * (n - 1)) / n
    liq = _lm("orange", 1.6 if tier == "s" else 1.35)
    for i in range(n):
        a = xs0 + i * (seg + g)
        # tanque redondo (12 lados, pontas bem chanfradas): le como lagarta, nao como as baias quadradas da Piranha
        c = min(R * 0.42, seg * 0.3)
        tank = _prof(f"t_seg{i}", [(R * 0.72, a), (R * 0.93, a + c * 0.45), (R, a + c), (R, a + seg - c),
                                   (R * 0.93, a + seg - c * 0.45), (R * 0.72, a + seg)], A, tags, verts=12)
        if tier != "s":
            # costelas escuras (aneis de reforco) nas pontas do tanque
            for j, xr in enumerate((a + c + 0.012 * s, a + seg - c - 0.012 * s)):
                _tube(f"t_rib{i}{j}", xr - 0.011 * s, xr + 0.011 * s, R * 1.035, KM, tags, verts=12)
        # visor de "fogo liquido" grande alternando de lado; o liquido balanca (2 quadros)
        side = 1 if i % 2 == 0 else -1
        cx, cy = a + seg / 2, side * R * 0.26
        sx, sy = (seg - 2 * c) * 0.92 if tier != "s" else seg * 0.5, R * 0.48
        zf = _slot([tank], f"t_gl{i}", cx, cy, sx, sy, _ap(R, 12), 0.02 * max(s, 0.7), M, tags)
        sh = (1 if (f + i) % 2 == 0 else -1) * sx * 0.16
        _pip(f"t_liq{i}", cx + sh, cy, zf, sx * 0.5, sy * 0.5, liq, LT)
    if tier == "l":
        # tanques laterais (selas) com visor proprio, presos por suportes escuros
        for sy in (1, -1):
            yy = sy * 0.23
            st = _moved(_pill(f"t_sad{sy}", -0.62, 0.30, 0.062, A, tags, ch=0.3), y=yy)
            for k, xb in enumerate((-0.44, 0.10)):
                B.box(f"t_sbr{sy}{k}", xb, sy * 0.17, 0.07, 0.12, -0.035, 0.035, KM, bevel=0.005, tags=tags)
            zf = _slot([st], f"t_sgl{sy}", -0.16, yy, 0.30, 0.036, _ap(0.062), 0.02, M, tags)
            sh = (1 if (f + (sy > 0)) % 2 == 0 else -1) * 0.05
            _pip(f"t_sliq{sy}", -0.16 + sh, yy, zf, 0.17, 0.024, liq, LT)
            _moved(Mo.lathe(f"t_scap{sy}", [(0.05, 0.296), (0.03, 0.34), (0.0, 0.355)], KM, tags, verts=12, axis="X"),
                   y=yy)
    _tube("t_band", xs1, xs1 + 0.045 * max(s, 0.8), R * 1.03, band, tags)
    xd = xs1 + 0.045 * max(s, 0.8)
    if tier == "s":
        lsp = 0.025 * 0.8
        _prof("t_dome", _dome(xd, x_nose - lsp, R * 1.0, p=2.3, n=10, r_end=R * 0.42), X["nose"], tags, verts=16,
              smooth=True)
        _prof("t_spray", [(R * 0.40, x_nose - lsp - 0.004), (R * 0.36, x_nose - 0.004)], KM, tags, verts=16,
              smooth=True)
        return
    # bico aspersor de 3 furos visivel de cima: coletor escuro na ponta da cupula e 3 bicos em leque (um reto e
    # dois a +-30 graus), pontas de aco; tudo antes da margem de 0.02 tile da tela
    xe = x_nose - 0.008                      # ponta do bico reto
    lb = 0.08 * s
    x0j = xe - lb                             # raiz dos bicos (no coletor)
    _prof("t_dome", _dome(xd, x0j + 0.004, R * 1.0, p=2.3, n=10, r_end=R * 0.50), X["nose"], tags, verts=16,
          smooth=True)
    _prof("t_man", [(R * 0.52, x0j - 0.012), (R * 0.44, x0j + 0.022 * s)], KM, tags, verts=12)
    tl = 0.022 * s
    for k, ang in enumerate((0.0, 40.0, -40.0)):
        a = math.radians(ang)
        ll = lb if ang == 0 else lb * 0.92
        ex, ey = x0j + ll * math.cos(a), ll * math.sin(a)
        B.rbox(f"t_jet{k}", (x0j + ex) / 2, ey / 2, ll, 0.03 * s, -0.02, 0.02 * s, KM, rot=ang, bevel=0.003,
               tags=tags)
        B.rbox(f"t_jtip{k}", ex - tl / 2 * math.cos(a), ey - tl / 2 * math.sin(a), tl, 0.042 * s, -0.018,
               0.024 * s, S, rot=ang, bevel=0.003, tags=tags)


# ============================================================================ Poraque (P.E.M., azul)
def _ribbon_scales(x0, x1, r0, h_front, h_rear, n):
    """Barbatana-fita em n escamas (dentes varridos) de x1 (frente) a x0 (cauda): cada escama tem a raiz no corpo,
    o bordo de ataque subindo ate o pico e o de fuga descendo ate a metade da altura; os picos baixam para a cauda
    e alternam um pouco (o ondulado da enguia). Poligonos no lado +y."""
    out = []
    L = (x1 - x0) / n
    for k in range(n):
        t = (k + 0.5) / n
        h = h_front + (h_rear - h_front) * t
        h *= 1.0 if k % 2 == 0 else 0.86
        xa = x1 - k * L                          # frente da escama
        xb = xa - L - 0.012                      # fuga (sobrepoe a proxima)
        out.append([(xa + 0.02, r0 * 0.55), (xa - L * 0.22, r0 + h), (xa - L * 0.40, r0 + h * 0.96),
                    (xb, r0 + h * 0.42), (xb, r0 * 0.55)])
    return out


def _emp(M, X, tags, LT, f, tier):
    A, K, KM, S = M["armor"], M["core"], M["core_mid"], M["steel"]
    copper = Mo.copper_mat()
    late = tier == "l"
    if not late:
        R, x_noz, x_sl, x_coil0, n_coil, lc, lg, x_nose = 0.08, -0.855, (-0.76, -0.12), 0.0, 3, 0.085, 0.04, 0.855
        fin = (-0.80, -0.06, 0.08, 0.115, 0.03, 5)
    else:
        R, x_noz, x_sl, x_coil0, n_coil, lc, lg, x_nose = 0.10, -1.23, (-1.10, -0.30), 0.05, 4, 0.11, 0.045, 1.10
        fin = (-1.16, -0.16, 0.10, 0.16, 0.035, 6)
    s = R / 0.08
    Mo.lathe("e_noz", [(R * 0.48, x_noz), (R * 0.64, x_noz + 0.055 * s)], S, tags, verts=12, axis="X")
    _tube("e_core", x_noz + 0.04, x_coil0 + n_coil * (lc + lg) + 0.06, R * 0.86, KM, tags)
    # barbatana-fita em corrente de escamas chanfradas (cada uma um dente varrido para tras, mais baixas para a
    # cauda): o ritmo ondulado da enguia com as quinas vivas da familia
    scales = _ribbon_scales(*fin)
    for k, poly in enumerate(scales):
        zt_k = 0.008 + 0.008 * (len(scales) - 1 - k)     # a escama da frente fica por cima da de tras
        for nm, pp in (("l", poly), ("r", _my(poly))):
            B.shard(f"e_rib{k}_{nm}", pp, -0.008, zt_k, A, slope=0.011, groove=0.007, panel_h=0.006,
                    panel_mat=M["armor_mid"], tags=tags)
    sl = Mo.chevron_sleeve("e_sl", x_sl[0], x_sl[1], R * 1.08, A, tags, dv=0.05 * s, rear=False)
    npip = 2 if not late else 3
    cx = (x_sl[0] + x_sl[1]) / 2
    zf = _slot([sl], "e_led", cx, 0.0, 0.05 * npip + 0.02, 0.034, _ap(R * 1.08), 0.022, M, tags)
    for i in range(npip):
        _pip(f"e_pip{i}", cx + (i - (npip - 1) / 2) * 0.05, 0.0, zf, 0.028, 0.02, _lm("blue", 0.7), LT)
    # pilha de bobinas de cobre; nas frestas o brilho azul (a fresta quente corre para o nariz)
    gaps = []
    x = x_coil0
    for i in range(n_coil):
        gaps.append((x, x + lg))
        x += lg
        _prof(f"e_coil{i}", [(R * 1.10, x), (R * 1.22, x + 0.012), (R * 1.22, x + lc - 0.012), (R * 1.10, x + lc)],
              copper, tags, verts=16, smooth=True)
        x += lc
    if not late:
        gaps.append((x, x + lg))
        x += lg
    x_coil1 = x
    for i, (a, b) in enumerate(gaps):
        st = 1.3 if i == f else 0.0
        m = (a + b) / 2
        _prof(f"e_gapk{i}", [(R * 1.0, a - 0.002), (R * 1.0, b + 0.002)], M["black"], tags, verts=16, smooth=True)
        _prof(f"e_gap{i}", [(R * 1.03, m - lg * 0.30), (R * 1.03, m + lg * 0.30)], _lm("blue", st), LT, verts=16,
              smooth=True)
    # buscador escuro com olho azul; colar e 2 aneis de aco claros (o contorno nao some sobre o espaco preto)
    og, prof = _nose("e_og", R * 1.0, x_coil1, x_nose, KM, K, tags, tip_r=0.02)
    _tube("e_scol", x_coil1 - 0.004, x_coil1 + 0.034, R * 1.06, S, tags)
    xe = x_coil1 + (x_nose - x_coil1) * 0.42
    re = _r_at(prof, xe)
    zf = _slot([og], "e_eye", xe, 0.0, 0.05 * s, 0.04 * s, re, 0.024 * s, M, tags)
    _pip("e_eyep", xe, 0.0, zf, 0.032 * s, 0.024 * s, _lm("blue", 1.0), LT)
    for k, t in enumerate((0.62, 0.80)):
        xx = x_coil1 + (x_nose - x_coil1) * t
        rr = _r_at(prof, xx + 0.016)
        _tube(f"e_sring{k}", xx, xx + 0.032, rr * 1.08 + 0.004, S, tags)
    if late:
        # 2 pontas de arco (>= 2 px de largura, STYLE 11.2) com as pontas azuis (estrutura do fim), presas num
        # colar de aco
        _tube("e_pcol", x_coil1 + 0.13, x_coil1 + 0.19, R * 1.02, S, tags)
        yp = 0.104
        for sy in (1, -1):
            B.box(f"e_prong{sy}", (x_coil1 + 0.15 + 1.19) / 2, sy * yp, 1.19 - (x_coil1 + 0.15), 0.036,
                  -0.014, 0.02, S, bevel=0.004, tags=tags)
            B.box(f"e_ptip{sy}", 1.205, sy * yp, 0.042, 0.036, -0.01, 0.024,
                  _lm("blue", 1.2 if f == 3 else 0.3), bevel=0.0, tags=LT)


# ============================================================================ Boto (torpedo isca, branco)
def _boto(M, X, tags, LT, f, xt, xn, R, Lb, late, decoy):
    """Torpedo: cauda escura com bomba-jato + anel de carenagem (2 barras + escora), [luva de reforco escura + 2
    propulsores laterais], corpo branco com costuras, faixa clara, nariz arredondado com fenda escura."""
    A, AM, K, KM, S = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"]
    s = R / 0.20
    body_m = X["grey"] if decoy else X["white_body"]
    # cauda (tudo facetado, sombreamento plano: lathe liso de 2 aneis puxa a normal das tampas e borra o mapa)
    Mo.lathe("b_pj", [(0.05 * s, xt), (0.10 * s, xt + 0.06 * s), (0.15 * s, xt + 0.175 * s)], KM, tags, verts=16,
             axis="X", smooth=False)
    _tube("b_stat", xt + 0.15 * s, xt + 0.19 * s, 0.158 * s, S, tags, verts=16)
    _prof("b_tc", [(0.15 * s, xt + 0.17 * s), (R, xt + 0.30 * s)], AM, tags, verts=16)
    bar = [(xt + 0.012 * s, R + 0.045 * s), (xt + 0.25 * s, R + 0.045 * s), (xt + 0.28 * s, R + 0.08 * s),
           (xt + 0.25 * s, R + 0.115 * s), (xt + 0.012 * s, R + 0.115 * s)]
    bar_m = X["grey"] if decoy else A
    _fins("b_bar", bar, 0.0, 0.09 * s, bar_m, tags, slope=0.014, groove=0.009, ph=0.009)
    strut = [(xt + 0.03 * s, 0.08 * s), (xt + 0.03 * s, R + 0.08 * s), (xt + 0.20 * s, R + 0.08 * s),
             (xt + 0.27 * s, 0.08 * s)]
    _fins("b_strut", strut, 0.0, 0.018 * s, KM, tags, slope=0.006, groove=0.005, ph=0.005)
    B.box("b_dors", xt + 0.135 * s, 0.0, 0.21 * s, 0.022 * s, 0.08 * s, R + 0.05 * s, bar_m, bevel=0.004, tags=tags)
    if late:
        # fim: par de aletas inclinadas para fora das barras
        _fins("b_xfin", [(xt + 0.04 * s, R + 0.10 * s), (xt + 0.04 * s, R + 0.20 * s), (xt + 0.11 * s, R + 0.20 * s),
                         (xt + 0.22 * s, R + 0.10 * s)], 0.0, 0.02 * s, bar_m, tags)
    xb0 = xt + 0.30 * s
    if Lb > 0:
        # estagio 1: luva de reforco escura (frente em divisa) e 2 propulsores laterais
        Mo.chevron_sleeve("b_bsl", xt + 0.27 * s, xb0 + Lb - 0.06 * s, R * 1.07, AM, tags, dv=0.10 * s, rear=False)
        for k, xx in enumerate((xb0 + Lb * 0.30, xb0 + Lb * 0.62)):
            _tube(f"b_bseam{k}", xx - 0.01, xx + 0.01, R * 1.075, K, tags)
        yb = R + 0.11 * s
        for sy in (1, -1):
            _moved(_tube(f"b_so{sy}", xt + 0.21 * s, xb0 + Lb - 0.16 * s, 0.065 * s, AM, tags), y=sy * yb)
            # nariz do propulsor escuro e facetado (o branco liso lia como brinquedo), com cinta de aco na emenda
            _moved(_prof(f"b_son{sy}", Mo.ogive(0.065 * s, 0.15 * s, xb0 + Lb - 0.16 * s, tip_r=0.01) +
                         [(0.0, xb0 + Lb - 0.005 * s)], KM, tags, verts=8), y=sy * yb)
            _moved(_tube(f"b_sob{sy}", xb0 + Lb - 0.175 * s, xb0 + Lb - 0.145 * s, 0.068 * s, S, tags), y=sy * yb)
            _moved(Mo.lathe(f"b_soz{sy}", [(0.04 * s, xt + 0.16 * s), (0.05 * s, xt + 0.22 * s)], S, tags, verts=12,
                            axis="X"), y=sy * yb)
            for k, xx in enumerate((xb0 + Lb * 0.15, xb0 + Lb * 0.75)):
                B.box(f"b_brk{sy}{k}", xx, sy * (R + 0.04 * s), 0.07 * s, 0.10 * s, -0.03 * s, 0.04 * s, KM,
                      bevel=0.005, tags=tags)
        xb0 += Lb
    Ln = 0.55 * s
    xband = xn - Ln - 0.06 * s
    # corpo de 16 lados com sombreamento plano, como os canos da familia (STYLE 1.5); so o nariz e liso
    _tube("b_body", xb0 - 0.02, xband + 0.002, R, body_m, tags, verts=16)
    zt = _ap(R, 16)
    nseam = 3 if late else 2
    for k in range(nseam):
        xx = xb0 + (xband - xb0) * (k + 1) / (nseam + 1)
        _tube(f"b_seam{k}", xx - 0.009, xx + 0.009, R * 1.012, K, tags, verts=16)
    # estrobos brancos (1 no meio, 2 no fim) no fundo de recessos em carcacas planas elevadas na espinha: o corte
    # pega SO a carcaca (nunca uma booleana no lathe do corpo)
    nstr = 2 if late else 1
    hm = KM if decoy else AM
    for k in range(nstr):
        xx = xb0 + (xband - xb0) * (0.62 if k == 0 else 0.20)
        hz = zt + 0.034 * s
        hs = B.box(f"b_strh{k}", xx, 0.0, 0.115 * s, 0.088 * s, zt - 0.01, hz, hm, bevel=0.006 * s, tags=tags)
        zf = _slot([hs], f"b_strb{k}", xx, 0.0, 0.064 * s, 0.054 * s, hz, 0.026 * s, M, tags)
        on = (f == 0) if (k == 0 or decoy) else (f == 1)
        _pip(f"b_spip{k}", xx, 0.0, zf, 0.050 * s, 0.042 * s, _lm("white", (1.7 if decoy else 1.4) if on else 0.08),
             LT)
    if decoy:
        # isca: colar de aco claro antes do nariz escuro (o contorno nao some sobre o espaco preto)
        _tube("b_bandk", xband, xn - Ln, R * 1.03, S, tags, verts=16)
    else:
        _tube("b_band", xband, xn - Ln, R * 1.02, Mo.band_mat("torpedo"), tags, verts=16)
    if late and not decoy:
        # colar do sonar (escuro) logo atras da faixa e bolha escura do sonar na espinha (o fim se le a 1x)
        _tube("b_sonar", xband - 0.10 * s, xband - 0.03 * s, R * 1.03, AM, tags, verts=16)
        bl = [(xband - 0.39 * s, 0.0), (xband - 0.33 * s, -0.062 * s), (xband - 0.17 * s, -0.062 * s),
              (xband - 0.12 * s, 0.0), (xband - 0.17 * s, 0.062 * s), (xband - 0.33 * s, 0.062 * s)]
        B.plate("b_blis", bl, zt - 0.01, zt + 0.045 * s, KM, slope=0.02 * s, bevel=0.004, tags=tags)
        B.box("b_blisw", xband - 0.25 * s, 0.0, 0.10 * s, 0.024 * s, zt + 0.03 * s, zt + 0.05 * s, S, bevel=0.003,
              tags=tags)
    # nariz de golfinho liso; o anel-guarda logo na base prende a media com a tampa num fio de 0.004 tile
    x0n = xn - Ln
    nprof = _dome(x0n, xn, R, p=2.2, n=12)
    nprof = [nprof[0], (R * 0.9995, x0n + 0.004)] + nprof[1:]
    _prof("b_nose", nprof, KM if decoy else X["white"], tags, verts=24, smooth=True)
    if not decoy:
        # fenda do buscador: caixa preta embutida (sem booleana na superficie lisa)
        xs = xn - 0.14 * s
        rs = _r_at(nprof, xs - 0.02 * s)
        B.box("b_slit", xs, 0.0, 0.035 * s, 0.13 * s, rs - 0.05 * s, rs + 0.004, M["black"], bevel=0.0, tags=tags)


# ============================================================================ Iara (torpedo nuclear, verde)
def _iara(M, X, tags, LT, f, xt, xn, boosters):
    A, AM, K, KM, S, BLK = M["armor"], M["armor_mid"], M["core"], M["core_mid"], M["steel"], M["black"]
    D = X["dark"]
    chev = Mo.chevron_mat("iara_chev", scale=6.0)
    paint = Mo.band_mat("nuclear")
    # respiracao das faixas, da janela e dos aneis do bocal: 0.55/0.8/1.0/0.8 de brilho PERCEBIDO. Na vista Standard
    # (sRGB) isso pede forcas lineares ~0.27/0.58/0.94/0.58 (G ~140/200/250/200), todas abaixo do ponto de estouro;
    # o verde proprio "iara" tem pouco vermelho (R/G ~0.42 no pico), entao somado ao corpo e ao GlowSprite nao
    # amarela (nunca amarelo na Iara)
    glow = _lm("iara", (0.22, 0.47, 0.72, 0.47)[f])
    R, RW = 0.20, 0.28
    ap, apw = _ap(R), _ap(RW)
    rb = RW + 0.008                            # raio da tinta das faixas (por cima da ogiva)

    def band(nm, x0, x1, xg0, xg1, ys):
        """Faixa LARGA: tinta verde da faixa nuclear (a mesma do nariz no casulo) de x0 a x1 com a faixa acesa
        (xg0..xg1, >= 2.5 px) no meio, sobre leito preto; presilhas de aco nas posicoes ys (so nos ombros)."""
        _tube(nm + "p", x0, x1, rb, paint, tags)
        _tube(nm + "k", xg0 - 0.004, xg1 + 0.004, rb + 0.003, BLK, tags)
        _tube(nm, xg0, xg1, rb + 0.006, glow, LT)
        _clamps(nm + "cl", (x0 + x1) / 2, x1 - x0 + 0.02, ys, _ap(rb + 0.006), S, tags)

    # ---- ogiva gorda (3 camadas): nucleo escuro, placas dos ombros com divisas, placa de cima ESCURA com o trevo
    xw0, xw1 = xn - 1.40, xn - 0.34
    _tube("i_wh", xw0, xw1, RW, D, tags)
    _prof("i_whcol", [(R, xn - 1.50), (RW, xw0)], D, tags)
    # faixa larga da base da ogiva (0.08 tile = 5 px; acesa 0.037 = 2.4 px), so 2 presilhas (nos ombros)
    band("i_band", xw0 + 0.002, xw0 + 0.082, xw0 + 0.0235, xw0 + 0.0605, (-0.20, 0.20))
    for th in (45, -45):
        _facet(f"i_sh{th}", xn - 1.22, xn - 0.50, 0.074, apw, th, 0.022, A, tags, panel_mat=chev, ch=0.02, cf=0.05,
               slope=0.012, groove=0.008, ph=0.01)
    # placa de cima: miolo escuro com aro claro chanfrado (2 px) e o trevo grande (cunhas pretas sobre disco verde,
    # como o icone nuclear do jogo e o recurso bs_shell_nuke)
    ta, tp = _facet("i_top", xn - 1.27, xn - 0.46, 0.14, apw, 0, 0.026, A, tags, panel_mat=D, ch=0.035, cf=0.075,
                    slope=0.022, groove=0.012, ph=0.014)
    cx = xn - 0.86
    ztp = apw + 0.026 + 0.014
    Mo.trefoil_inlay("i_tref", [ta, tp], cx, 0.0, ztp, 0.092, 0.026, M, tags, wedge_mat=BLK, disc_mat=paint,
                     disc_r=0.118, hub_mat=BLK, a0=0.0, depth=0.03)
    B.bolts("i_bolt", [(xn - 1.205, 0.095), (xn - 1.205, -0.095), (xn - 0.535, 0.075), (xn - 0.535, -0.075)],
            ztp + 0.002, 0.013, S, tags=tags)
    # faixa antes do nariz (0.09 tile; acesa 0.036 = 2.3 px) e nariz blindado rombudo (cinza do nariz da Iara no
    # casulo) com buscador escuro
    band("i_nband", xn - 0.44, xn - 0.35, xn - 0.413, xn - 0.377, (-0.20, 0.20))
    _prof("i_cap", [(RW * 0.985, xn - 0.34), (RW * 0.96, xn - 0.26), (RW * 0.86, xn - 0.17), (RW * 0.68, xn - 0.09),
                    (RW * 0.47, xn - 0.04)], X["iara_cap"], tags)
    _prof("i_seek", [(RW * 0.40, xn - 0.045), (RW * 0.33, xn - 0.02), (RW * 0.18, xn - 0.004), (0.0, xn)], K, tags,
          verts=16, smooth=True)
    # ---- corpo do meio: escuro, placas dos ombros (lascas cinza solidas com frestas escuras) e a janela do nucleo
    xm0, xm1 = xn - 2.30, xn - 1.50
    mid = _tube("i_mid", xm0, xm1 + 0.01, R, D, tags)
    _panels("i_msh", xm0 + 0.03, xm1 - 0.03, ap, (45, -45), AM, AM, tags)
    # janela do nucleo mais curta (0.36 tile): a area acesa vai para as faixas largas (orcamento de 4%)
    wc = (xm0 + xm1) / 2
    wx0, wx1 = wc - 0.18, wc + 0.18
    zf = _slot([mid], "i_win", wc, 0.0, wx1 - wx0, 0.076, ap, 0.036, M, tags)
    B.box("i_core", wc, 0.0, wx1 - wx0 - 0.03, 0.021, zf + 0.0005, zf + 0.007, glow, bevel=0.0, tags=LT)
    nbar = 3
    for k in range(nbar):
        xx = wx0 + (wx1 - wx0) * (k + 0.5) / nbar
        B.box(f"i_bar{k}", xx, 0.0, 0.018, 0.084, ap - 0.02, ap - 0.004, S, bevel=0.003, tags=tags)
    for sy in (1, -1):
        B.box(f"i_wrail{sy}", wc, sy * 0.044, wx1 - wx0 + 0.02, 0.012, ap - 0.012, ap + 0.004, S,
              bevel=0.002, tags=tags)
    # ---- secao do motor (escura, costuras) e cauda: carenagem, 4 aletas escuras, bocal triplo com aneis verdes.
    # Aletas, cone de cauda e carenagem ficam 0.12 tile a frente da saida: os 3 sinos aparecem atras deles (8 px),
    # separados por frestas escuras (centros em +-0.15, raio 0.055)
    xe0 = xt + 0.47
    _tube("i_eng", xe0, xm0 + 0.01, R, D, tags)
    nseam = max(1, int((xm0 - xe0) / 0.28))
    for k in range(nseam):
        xx = xe0 + (xm0 - xe0) * (k + 1) / (nseam + 1)
        _tube(f"i_eseam{k}", xx - 0.012, xx + 0.012, R * 1.012, BLK, tags)
    _panels("i_esh", xe0 + 0.03, xm0 - 0.03, ap, (45, 0, -45), AM, AM, tags)
    _prof("i_tc", [(0.125, xt + 0.13), (R, xe0 + 0.01)], D, tags)
    # aletas escuras solidas com o bordo de ataque claro chanfrado (2.5 px)
    fin = [(xt + 0.49, 0.12), (xt + 0.29, 0.64), (xt + 0.165, 0.64), (xt + 0.16, 0.12)]
    _fins("i_fin", fin, 0.0, 0.028, D, tags, slope=0.016, groove=0.010, ph=0.010)
    le = [(xt + 0.475, 0.15), (xt + 0.298, 0.615)]
    for sy in (1, -1):
        pts = [(x, sy * y) for x, y in le]
        B.plate(f"i_fle{sy}", _strip(pts, 0.019), 0.008, 0.026, A, slope=0.007, bevel=0.003, tags=tags)
    _fins("i_bar", [(xt + 0.15, 0.245), (xt + 0.39, 0.245), (xt + 0.415, 0.27), (xt + 0.39, 0.30), (xt + 0.15, 0.30)],
          0.0, 0.09, A, tags, slope=0.012, groove=0.008, ph=0.01)
    B.box("i_dors", xt + 0.33, 0.0, 0.30, 0.024, 0.10, R + 0.06, A, bevel=0.004, tags=tags)
    for k, yy in enumerate((-0.15, 0.0, 0.15)):
        # sino de aco (labio de saida 3.5 px) + anel verde (2 px) + garganta escura estreita ate o cone de cauda
        _moved(Mo.lathe(f"i_noz{k}", [(0.055, xt), (0.053, xt + 0.025), (0.047, xt + 0.055)], S, tags, verts=12,
                        axis="X"), y=yy)
        _moved(_tube(f"i_nring{k}", xt + 0.055, xt + 0.087, 0.049, glow, LT, verts=12), y=yy)
        _moved(_tube(f"i_nthr{k}", xt + 0.085, xt + 0.20, 0.036, KM, tags, verts=12), y=yy)
    if boosters:
        # estagio 1: 2 propulsores laterais escuros com nariz cinza, presos por suportes
        x0b, x1b = xt + 0.52, xn - 2.50
        for sy in (1, -1):
            yy = sy * 0.335
            _moved(_tube(f"i_so{sy}", x0b, x1b, 0.085, D, tags), y=yy)
            _moved(_prof(f"i_son{sy}", Mo.ogive(0.085, 0.16, x1b, tip_r=0.012) + [(0.0, x1b + 0.16)], X["iara_cap"],
                         tags, verts=12, smooth=True), y=yy)
            _moved(Mo.lathe(f"i_soz{sy}", [(0.05, x0b - 0.06), (0.062, x0b + 0.01)], S, tags, verts=12, axis="X"),
                   y=yy)
            _moved(_tube(f"i_sob{sy}", x1b - 0.06, x1b - 0.03, 0.088, BLK, tags), y=yy)
            for k, xx in enumerate((x0b + 0.18, x1b - 0.22)):
                B.box(f"i_sbr{sy}{k}", xx, sy * 0.25, 0.09, 0.14, -0.035, 0.05, KM, bevel=0.006, tags=tags)


def _iara_decoy(M, X, tags, LT, f):
    """Isca da Iara: cinza e pequena, cabeca gorda lisa com nariz cinza claro e faixa verde fina pintada; sem
    divisas, sem trevo; estrobo verde fraco."""
    K, KM, S = M["core"], M["core_mid"], M["steel"]
    G = X["grey"]
    R, RH = 0.11, 0.15
    xt, xn = -0.98, 0.98
    Mo.lathe("d_noz", [(0.045, xt), (0.055, xt + 0.07)], S, tags, verts=12, axis="X")
    _prof("d_tc", [(0.08, xt + 0.05), (R, xt + 0.22)], KM, tags)
    _fins("d_bar", [(xt + 0.02, 0.135), (xt + 0.17, 0.135), (xt + 0.19, 0.152), (xt + 0.17, 0.17), (xt + 0.02, 0.17)],
          0.0, 0.05, G, tags)
    _fins("d_fin", [(xt + 0.24, 0.06), (xt + 0.10, 0.30), (xt + 0.03, 0.30), (xt + 0.03, 0.06)], 0.0, 0.018, G, tags)
    body = _tube("d_body", xt + 0.21, 0.32, R, G, tags)
    zf = _slot([body], "d_strb", -0.25, 0.0, 0.054, 0.044, _ap(R), 0.022, M, tags)
    _pip("d_spip", -0.25, 0.0, zf, 0.038, 0.030, _lm("iara", 0.6 if f == 0 else 0.06), LT)
    _tube("d_seam", -0.02, 0.0, R * 1.02, K, tags)
    _prof("d_col", [(R, 0.32), (RH, 0.40)], G, tags)
    _tube("d_head", 0.40, 0.74, RH, G, tags)
    _tube("d_band", 0.74, 0.77, RH * 1.03, Mo.band_mat("nuclear"), tags)
    _prof("d_cap", [(RH * 0.98, 0.77), (RH * 0.9, 0.86), (RH * 0.66, 0.935), (RH * 0.40, 0.965)], X["iara_cap"], tags)
    _prof("d_seek", [(RH * 0.34, 0.96), (RH * 0.18, 0.975), (0.0, xn)], K, tags, verts=12, smooth=True)


# ============================================================================ entrada
def model(M, key, T="body", phase=0.0):
    tags = (T,)
    LT = (T, "lights")
    n = max(1, int(PART["items"][key].get("frames", 1)))
    f = int(round(phase * n)) % n
    X = _mats(M)
    if key in ("he_s", "he_m", "he_l"):
        _he(M, X, tags, LT, f, key[-1])
    elif key in ("cluster_m", "cluster_l"):
        _cluster(M, X, tags, LT, f, key[-1])
    elif key == "cluster_child":
        _fry(M, X, tags)
    elif key in ("limpet_m", "limpet_l"):
        _limpet(M, X, tags, LT, f, key[-1])
    elif key == "limpet_charge":
        _limpet_charge(M, X, tags, LT, f)
    elif key in ("napalm_s", "napalm_m", "napalm_l"):
        _napalm(M, X, tags, LT, f, key[-1])
    elif key in ("emp_m", "emp_l"):
        _emp(M, X, tags, LT, f, key[-1])
    elif key == "torpedo_m":
        _boto(M, X, tags, LT, f, -1.355, 1.355, 0.20, 0.5, False, False)
    elif key == "torpedo_wh_m":
        _boto(M, X, tags, LT, f, -1.105, 1.105, 0.20, 0.0, False, False)
    elif key == "torpedo_l":
        _boto(M, X, tags, LT, f, -1.605, 1.605, 0.25, 0.5, True, False)
    elif key == "torpedo_wh_l":
        _boto(M, X, tags, LT, f, -1.355, 1.355, 0.25, 0.0, True, False)
    elif key == "torpedo_decoy":
        _boto(M, X, tags, LT, f, -0.855, 0.855, 0.12, 0.0, False, True)
    elif key == "nuclear_l":
        _iara(M, X, tags, LT, f, -1.855, 1.855, True)
    elif key == "nuclear_wh_l":
        _iara(M, X, tags, LT, f, -1.53, 1.53, False)
    elif key == "nuclear_decoy":
        _iara_decoy(M, X, tags, LT, f)
    else:
        raise KeyError(f"bs_missiles: item desconhecido {key}")
