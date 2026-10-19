"""Granadas de canhao em voo (kind "shells"): 3 texturas reaproveitadas em todos os calibres.

As regras (tools/bsgen/caliber_fx.py) escalam a MESMA imagem: 76 mm 0.72 x 0.26, 155 mm 1.15 x 0.40, 406 mm
2.05 x 0.72 e Boiuna 2.2 x 0.86 quadros (caliber_vfx_table.json). Por isso a tela das granadas comuns tem a
proporcao media desses tamanhos (2.0 x 0.70 = 256 x 90 px a 128 px/quadro; o sprite nao fica esticado) e cada
elemento tem pelo menos ~3 px no menor calibre (76 mm = 46 px de comprimento a 1x): cinta de cobre, faixa da
municao e espoleta sao largas, o resto e silhueta e sombreamento.

  * he (Padrao, P.E.M.): corpo de aco canhoneado escuro, cauda afinada, cinta de forcamento de cobre com sulco,
    linha de solda no meio do corpo, faixa da municao (mascara tingida pelo jogo) logo atras da ogiva, anel de
    centragem de aco claro e espoleta curta de aco claro de ponta chata com anel escuro de regulagem;
  * ap (Perfurante, Perfurante-Explosiva): corpo de aco usinado MEDIO (o inverso da he: da para separar as duas
    a 46 px), ogiva longa com capuz balistico de CHUMBO (cinza-grafite medio: ~40 niveis abaixo do corpo e ~33
    acima da tinta do casco, senao o nariz some sobre o casco e a ap le como um cilindro rombudo), ponta de aco
    claro e anel de cravacao claro na base do capuz;
  * nuke (Boiuna): mesma familia do recurso aprovado bs_shell_nuke e da Iara: anel de base de aco claro, colar
    claro com contador de 3 LEDs verdes em fila (ao longo do eixo) numa fenda escura, faixas verdes que RESPIRAM
    (atlas de 4 quadros a 6 fps), luva de divisas verde/preto, nucleo escuro com a janela do nucleo (recesso
    preto com grade de aco, SEM barra acesa: a ancora 'radiation' fica no meio dela e as regras poem o
    radiation_small.png verde girando por cima, que precisa de fundo escuro limpo), colar claro no pescoco e
    ogiva cinza clara facetada com o trevo de 3 cunhas pretas embutido e cubo verde; espoleta de aco.
    NUNCA listras amarelo/preto nem disco amarelo (regra do mod desde a Boiuna; STYLE.md 10.1 e 11.6).

Respiracao (STYLE.md 10.1, 0,55 / 0,8 / 1,0 / 0,8): a curva vale para o brilho que SAI no PNG (sRGB). A forca de
emissao no Blender e linear, entao cada quadro usa forca = pico * br ** 2.2 e o pico fica logo abaixo do estouro
(G ~245 no centro da faixa): com forca constante * br o quadro 0 ja estourava e os quadros 1-3 saiam iguais.

Todas as pecas sao octogonais de topo plano (lathe com verts=8, a0=pi/8, faces planas), como os canos da
familia e o recurso bs_shell_nuke: vistas de cima dao 3 faixas de tom (topo e duas facetas) que leem como volume
mesmo a 46 px; no jogo o sombreamento vem do mapa de normais (IsLit).

    $PY tools/blender/render_part.py bs_shells --quick --out <rascunho> [--only nuke] [--preview]
    $PY tools/blender/render_part.py bs_shells          # final em art3d/bs_shells/
"""

import math

import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_shells",
    "kind": "shells",
    "px_per_tile": 128,
    "accent": "green",
    "items": {
        # 256 x 90 px: proporcao 2.86 = media de 76/155/406 mm (2.77 / 2.88 / 2.85)
        "he": {"canvas_tiles": [2.0, 0.70], "frames": 1, "fps": 0, "wrap": None, "nozzle_x": -0.97,
               "mask": True, "anchors": {}},
        "ap": {"canvas_tiles": [2.0, 0.70], "frames": 1, "fps": 0, "wrap": None, "nozzle_x": -0.97,
               "mask": True, "anchors": {}},
        # 256 x 96 px (Boiuna 2.2 x 0.86 no jogo); ancora da radiacao no meio da janela do nucleo
        "nuke": {"canvas_tiles": [2.0, 0.75], "frames": 4, "fps": 6, "wrap": None, "nozzle_x": -0.97,
                 "mask": False, "anchors": {"radiation": [-0.10, 0.0]}},
    },
}

A0 = math.pi / 8                    # octogono de topo plano
COS8 = math.cos(math.pi / 8)        # meia largura vista de cima / raio do octogono
X0, X1 = -0.97, 0.97                # base e ponta (0.03 de folga na tela de 2.0)
BREATH = (0.55, 0.8, 1.0, 0.8)      # respiracao das faixas verdes (STYLE.md 10.1), no brilho de SAIDA (sRGB)
GAMMA = 2.2                         # forca linear = pico * br ** GAMMA (o sRGB comprime: linear 0.55 sai ~0.76)
# verde aceso: o verde das faixas nucleares da familia dos misseis (Mo.BAND_GLOW["nuclear"]); com o Mo.GREEN
# (R/G 0.40) o pico sai lima-claro (G/R ~1.5 no sRGB); com este (R/G 0.20) fica G/R ~2 no pico, verde de radiacao
NK_GLOW = Mo.BAND_GLOW["nuclear"]
PK_BAND, PK_HUB, PK_LED = 0.80, 0.66, 0.45   # forcas de pico (quadro 2): faixa, cubo do trevo, LEDs do contador

# ---- cores (nomes proprios "shl_*": o cache de materiais do bs3d e por nome)
DARK_STEEL = (0.085, 0.09, 0.10)    # aco canhoneado da he
MACHINED = (0.24, 0.245, 0.255)     # aco usinado medio da ap (mais claro que a he, mais escuro que o tracante)
LIGHT_STEEL = (0.50, 0.52, 0.55)    # espoleta / anel de base (mesmo valor do nk_ring do recurso)
AP_CAP = (0.12, 0.125, 0.14)        # chumbo do capuz da ap: sai L~90 (casco 46,58,74 = L57; corpo da ap L130)
HE_OGIVE = (0.115, 0.12, 0.13)      # ogiva da he um pouco mais clara que o corpo (separa o nariz no 155 / 406)
NK_BODY = (0.040, 0.043, 0.048)     # nucleo quase preto (recurso bs_shell_nuke BODY)
NK_GREY = (0.30, 0.31, 0.325)       # cinza claro da ogiva do recurso (OGIVE)


def _spec(m, v):
    """Reflexo especular baixo: os preenchimentos a +-70 graus refletem nas facetas de 45 graus e deixavam a face
    de cima mais escura que as facetas (corpo parecendo concavo)."""
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = v
    return m


def _lens(m, k=0.012):
    """Emissivo como LENTE ESCURA no difuso (STYLE 11.5): o mat_glow poe a cor base = cor * 0.08 e o sol axial
    deixava a faixa apagada verde-clara (53,100,51) no difuso; o jogo SOMA o atlas por cima, entao o composto
    estourava em 255 do quadro 1 em diante e a respiracao sumia. A cor base nao entra no passe de emissao."""
    b = m.node_tree.nodes["Principled BSDF"]
    c = b.inputs["Emission Color"].default_value
    b.inputs["Base Color"].default_value = (c[0] * k, c[1] * k, c[2] * k, 1)
    b.inputs["Roughness"].default_value = 0.45
    return m


def _mats(M):
    return {
        # metal baixo: com a luz axial (sol reto de cima sem reflexo) um metal puro deixa a face de cima MAIS
        # escura que as facetas (so os preenchimentos refletem) e o corpo parece concavo
        "he_body": _spec(B.mat_metal("shl_he_body", DARK_STEEL, rough=0.5, metal=0.3), 0.2),
        "ap_body": _spec(B.mat_metal("shl_ap_body", MACHINED, rough=0.45, metal=0.45), 0.2),
        "light": _spec(B.mat_metal("shl_light_steel", LIGHT_STEEL, rough=0.36, metal=0.55), 0.3),
        # capuz de chumbo: escuro o bastante para ler como capuz (abaixo do corpo usinado) e claro o bastante para
        # nao sumir sobre o casco (o valor antigo 0.05 saia 58,60,65 contra o casco 46,58,74: contraste 1.06)
        "cap": _spec(B.mat_metal("shl_ap_cap2", AP_CAP, rough=0.34, metal=0.5), 0.3),
        "he_ogive": _spec(B.mat_metal("shl_he_ogive", HE_OGIVE, rough=0.42, metal=0.35), 0.3),
        "groove": M["core_mid"],
        "black": M["black"],
        "band": Mo.nose_paint("shl_band_paint", Mo.NOSE_LIGHT),
        "copper": Mo.copper_mat(),
        "nk_body": B.mat_metal("shl_nk_body", NK_BODY, rough=0.48, metal=0.55),
        "nk_grey": B.mat_paint("shl_nk_grey", NK_GREY, rough=0.36, metal=0.3, wear=0.0, grime=0.04, scale=5),
        "nk_armor": B.mat_paint("shl_nk_armor", Mo.ARMOR, rough=0.32, metal=0.25, wear=0.0, grime=0.04, scale=4),
    }


def octo(name, prof, mat, tags):
    """Solido de revolucao octogonal de topo plano no eixo X (perfil [(raio, x)], faces planas)."""
    return Mo.lathe(name, prof, mat, tags, verts=8, axis="X", zc=0.0, a0=A0, smooth=False)


def ring(name, xa, xb, r, mat, tags, ch=0.0):
    """Anel octogonal de xa a xb no raio r; ch = chanfro (raio menor nas pontas)."""
    if ch > 0:
        return octo(name, [(r - ch, xa), (r, xa + ch), (r, xb - ch), (r - ch, xb)], mat, tags)
    return octo(name, [(r, xa), (r, xb)], mat, tags)


def _r_at(prof, x):
    """Raio do perfil [(r, x)] na posicao x (interpolado)."""
    for (ra, xa), (rb, xb) in zip(prof, prof[1:]):
        if xa <= x <= xb:
            return ra + (rb - ra) * (x - xa) / max(1e-9, xb - xa)
    return prof[-1][0] if x > prof[-1][1] else prof[0][0]


def _split(prof, x):
    """Corta o perfil [(r, x)] em x: devolve (antes, depois), os dois com o anel de corte em comum."""
    rc = _r_at(prof, x)
    a = [p for p in prof if p[1] < x - 1e-6] + [(rc, x)]
    b = [(rc, x)] + [p for p in prof if p[1] > x + 1e-6]
    return a, b


def _ogive_to(R, Lv, rf, x0, n=10):
    """Ogiva tangente do raio R (em x0) ao raio rf exatamente em x0 + Lv (truncada antes da ponta). Copia local de
    models._ogive_to (funcao privada do kit: uma refatoracao do kit nao quebra as granadas sem aviso)."""
    rf = min(max(rf, 1e-4), R * 0.999)

    def s_f(Lo):
        rho = (R * R + Lo * Lo) / (2 * R)
        return math.sqrt(max(0.0, rho * rho - (rf - R + rho) ** 2))
    lo, hi = Lv, Lv * 20 + 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if s_f(mid) < Lv:
            lo = mid
        else:
            hi = mid
    Lo = (lo + hi) / 2
    rho = (R * R + Lo * Lo) / (2 * R)
    return [(math.sqrt(max(0.0, rho * rho - s * s)) + R - rho, x0 + s) for s in (Lv * k / n for k in range(n + 1))]


# ============================================================================ granadas comuns
def _common(M, X, T, kind):
    """he / ap: perfil de Mo.shell_profile torneado em octogono, com cinta de cobre, solda, faixa da municao."""
    tags = (T,)
    R = 0.335                           # meia largura vista de cima = R * cos(22.5) = 0.31 (tela 0.35)
    L = X1 - X0
    if kind == "he":
        sp = Mo.shell_profile(L, R, "he", x0=X0, boat=0.09, tail_r=0.84, body_end=0.55, fuze=0.115, rf=0.42,
                              tip_r=0.55)
        body = X["he_body"]
    else:
        sp = Mo.shell_profile(L, R, "ap", x0=X0, boat=0.08, tail_r=0.86, body_end=0.43, cap=0.60, tip_r=0.05)
        body = X["ap_body"]
    S = sp["segs"]
    xb, xo = S["body"][0][1], S["body"][-1][1]
    # cauda afinada e corpo em 2 trechos com uma linha de solda escura no meio (quebra estrutural)
    octo(f"{kind}_tail", S["tail"], body, tags)
    xw = X0 + 0.43 * L if kind == "he" else X0 + 0.33 * L
    octo(f"{kind}_body0", [(R, xb), (R, xw - 0.012)], body, tags)
    octo(f"{kind}_weld", [(R * 0.965, xw - 0.013), (R * 0.965, xw + 0.013)], X["groove"], tags)
    octo(f"{kind}_body1", [(R, xw + 0.012), (R, xo)], body, tags)
    # cinta de forcamento de cobre (2 aneis com um sulco escuro): a unica excecao ao "cobre = P.E.M." (STYLE 10)
    ca = X0 + 0.135 * L
    cw = 0.135
    ring(f"{kind}_cu0", ca, ca + cw * 0.46, R * 1.045, X["copper"], tags, ch=0.008)
    ring(f"{kind}_cug", ca + cw * 0.44, ca + cw * 0.56, R * 1.01, X["groove"], tags)
    ring(f"{kind}_cu1", ca + cw * 0.54, ca + cw, R * 1.045, X["copper"], tags, ch=0.008)
    # faixa da municao logo atras da ogiva: tinta clara neutra no difuso + objeto (T, "mask")
    ring(f"{kind}_ammo", xo - 0.16, xo - 0.015, R * 1.025, X["band"], (T, "mask"), ch=0.006)
    if kind == "he":
        # anel de centragem de aco claro (bourrelet) entre a faixa e a ogiva
        ring("he_bour", xo - 0.018, xo + 0.022, R * 1.01, X["light"], tags, ch=0.004)
        # ogiva um tom acima do corpo: o bourrelet claro + a ogiva separam o nariz do corpo no 155 / 406 mm
        octo("he_ogive", S["ogive"], X["he_ogive"], tags)
        # espoleta: corpo de aco claro, anel escuro de regulagem, ponta chata
        fz = S["fuze"]
        xf, rf = fz[0][1], fz[0][0]
        octo("he_fuze", fz, X["light"], tags)
        ring("he_fzr", xf + 0.035, xf + 0.075, rf * 1.04, X["black"], tags)
        ring("he_fzb", xf - 0.004, xf + 0.012, rf * 1.10, X["groove"], tags)
    else:
        og, cap = S["ogive"], S["cap"]
        octo("ap_ogive", og, body, tags)
        # capuz de chumbo + ponta de aco claro (os ultimos 0.045: ~2 px a 76 mm, marca a ponta sobre o casco)
        cap_a, tip = _split(cap, X1 - 0.045)
        octo("ap_cap", cap_a, X["cap"], tags)
        octo("ap_tip", tip, X["light"], tags)
        # anel de cravacao claro na base do capuz (le como a borda do capuz balistico)
        xc, rc = cap[0][1], cap[0][0]
        ring("ap_crimp", xc - 0.012, xc + 0.016, rc * 1.03, X["light"], tags, ch=0.004)


# ============================================================================ granada nuclear
def _nuke(M, X, T, phase):
    tags = (T,)
    lt = (T, "lights")
    k = int(round(phase * 4)) % 4
    br = BREATH[k]
    R = 0.355                           # meia largura 0.328 (tela 0.375); pecas salientes ate 1.06 R
    top = R * COS8                      # face de cima do nucleo
    # forca linear = pico * br ** GAMMA: o brilho de saida segue 0.55 / 0.8 / 1.0 / 0.8 sem estourar no pico
    band_g = _lens(B.mat_glow(f"shl_nk_band_q{k}", NK_GLOW, PK_BAND * br ** GAMMA))
    # a faixa fina (2.6 px) sai ~8% mais quente que a larga no mesmo material (o denoiser realca linhas finas e a
    # coluna do meio estourava em 255 no pico): forca propria um pouco menor
    thin_g = _lens(B.mat_glow(f"shl_nk_bandf_q{k}", NK_GLOW, 0.92 * PK_BAND * br ** GAMMA))
    hub_g = _lens(B.mat_glow(f"shl_nk_hub_q{k}", NK_GLOW, PK_HUB * br ** GAMMA))
    led_g = _lens(B.mat_glow("shl_nk_led_q", NK_GLOW, PK_LED))  # contador fixo (nao respira)

    # ---- base: anel pesado de aco claro (chanfrado) + sulco escuro
    octo("nk_base", [(R * 0.94, X0), (R * 1.04, X0 + 0.02), (R * 1.04, X0 + 0.085), (R * 0.99, X0 + 0.095)],
         X["light"], tags)
    ring("nk_baseg", X0 + 0.09, X0 + 0.125, R * 0.95, X["groove"], tags)
    # nucleo escuro de ponta a ponta (as luvas e colares claros cobrem as pontas)
    xn0, xn1 = 0.18, 0.28               # colar do pescoco
    # (vai ate debaixo do pescoco: o entalhe de tras da luva do pescoco mostra o nucleo, nao um furo)
    core = ring("nk_core", X0 + 0.11, xn1 + 0.02, R, X["nk_body"], tags)

    # ---- colar claro da base em divisa (aponta para o nariz) com o contador de 3 LEDs verdes em fila ao longo do
    # eixo numa fenda (2 LEDs empilhados liam como um "8" a 1x; STYLE 11.3: nada de texto pintado)
    c0, c1 = X0 + 0.12, -0.70
    col = Mo.chevron_sleeve("nk_col", c0, c1, R * 1.035, X["nk_armor"], tags, dv=0.07, rear=False, verts=8)
    zt = R * 1.035 * COS8
    sx0, sx1 = c0 + 0.03, c1 - 0.01
    sw = 0.075                          # largura da fenda (em Y)
    # a fenda atravessa o colar e entra no nucleo (o colar tem so ~0.01 de espessura sobre o nucleo)
    for tgt, nm in ((col, "c"), (core, "k")):
        B.cut(tgt, [B.box(f"nk_cnt{nm}", (sx0 + sx1) / 2, 0, sx1 - sx0, sw, zt - 0.06, zt + 0.3, M["core"],
                          bevel=0.0)])
    B.box("nk_cntbed", (sx0 + sx1) / 2, 0, sx1 - sx0, sw, zt - 0.075, zt - 0.055, M["black"], bevel=0.0, tags=tags)
    pw = (sx1 - sx0) / 3
    for j in range(3):
        B.box(f"nk_cnt{j}", sx0 + (j + 0.5) * pw, 0, pw * 0.58, sw * 0.52, zt - 0.06, zt - 0.045, led_g, bevel=0.0,
              tags=lt)

    # ---- faixas verdes em sulcos pretos: larga atras da luva de divisas, fina na frente do nucleo (>= 0.02 =
    # 2.6 px a 128 px/quadro, STYLE 11.2). Raio 1.025 R: o halo de 5 px ainda cabe na tela de 0.75 (a 1.045 R ele
    # batia na borda de cima/baixo e saia cortado reto)
    for j, (bx, hw) in enumerate(((-0.60, 0.014), (0.135, 0.010))):
        ring(f"nk_bandk{j}", bx - hw - 0.02, bx + hw + 0.02, R * 1.012, X["black"], tags)
        ring(f"nk_band{j}", bx - hw, bx + hw, R * 1.025, thin_g if j else band_g, lt)

    # ---- luva de divisas verde/preto (excecao nuclear dos projeteis: NUNCA amarelo/preto)
    chev = Mo.chevron_mat("shl_nk_chev", scale=9.0)
    Mo.chevron_sleeve("nk_chev", -0.555, -0.38, R * 1.03, chev, tags, dv=0.08, verts=8)

    # ---- janela do nucleo no topo: recesso PRETO com 2 barras de grade de aco nas pontas. Sem barra acesa: o
    # radiation_small.png verde que as regras giram na ancora 'radiation' (-0.10) precisa de fundo escuro limpo
    # (a barra verde + o trevo girando liam como um rabisco "-*-" a 1x)
    wx0, wx1 = -0.26, 0.07
    B.cut(core, [B.box("nk_winc", (wx0 + wx1) / 2, 0, wx1 - wx0, 0.16, top - 0.06, top + 0.4, M["core"], bevel=0.0)])
    B.box("nk_winbed", (wx0 + wx1) / 2, 0, wx1 - wx0, 0.16, top - 0.075, top - 0.055, M["black"], bevel=0.0,
          tags=tags)
    for j, gx in enumerate((wx0 + 0.035, wx1 - 0.035)):
        B.box(f"nk_grate{j}", gx, 0, 0.03, 0.18, top - 0.04, top - 0.005, M["steel"], bevel=0.004, tags=tags)

    # ---- colar claro do pescoco (divisa) e ogiva cinza clara facetada
    Mo.chevron_sleeve("nk_neck", xn0, xn1, R * 1.03, X["nk_armor"], tags, dv=0.05, verts=8)
    og = _ogive_to(R * 0.99, 0.86 - xn1, R * 0.30, xn1, n=10)
    ogo = octo("nk_ogive", og, X["nk_grey"], tags)
    # anel escuro de painel perto da ponta e espoleta de aco claro com anel escuro
    xp = 0.74
    ring("nk_ogpl", xp - 0.012, xp + 0.012, _r_at(og, xp) * 1.02, X["black"], tags)
    xf = og[-1][1]
    rf = og[-1][0]
    octo("nk_fuze", [(rf * 1.02, xf - 0.005), (rf * 0.95, xf + 0.05), (rf * 0.45, X1 - 0.01), (rf * 0.30, X1)],
         X["light"], tags)
    ring("nk_fzr", xf + 0.012, xf + 0.032, rf * 1.04, X["black"], tags)

    # ---- trevo de 3 cunhas pretas embutido no topo da ogiva (1a cunha para o nariz) + cubo verde
    tx, ro, ri = 0.50, 0.17, 0.05
    r_c = _r_at(og, tx)
    r_f = _r_at(og, tx + ro)
    zc_top = r_c * COS8                 # face de cima no centro do trevo
    z_low = r_f * COS8 * math.sqrt(2) - ro   # faceta de 45 graus na frente, na borda do trevo
    depth = zc_top - min(z_low, r_f * COS8) + 0.015
    Mo.trefoil_inlay("nk_tref", [ogo], tx, 0.0, zc_top, ro, ri, M, tags, a0=0.0, depth=depth)
    B.cyl("nk_thub", tx, 0, zc_top - 0.006, ri * 0.98, 0.016, M["black"], axis="Z", verts=8, bevel=0.0, tags=tags)
    B.cyl("nk_tled", tx, 0, zc_top + 0.004, ri * 0.62, 0.008, hub_g, axis="Z", verts=8, bevel=0.0, tags=lt)


def model(M, key, T="body", phase=0.0):
    X = _mats(M)
    if key in ("he", "ap"):
        _common(M, X, T, key)
    elif key == "nuke":
        _nuke(M, X, T, phase)
    else:
        raise KeyError(key)
