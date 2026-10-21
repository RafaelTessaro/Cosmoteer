"""Previas da logistica 2.0 (paiois, Fita, FX dos cartuchos) para a aprovacao do usuario.

    python3 make_logistica.py [paiois|fita|gif|todas] [--root ART] [--out DIR]

Grava em docs/preview/3d/v2/ (ou --out):
  logistica_paiois.png  todos os paiois a 1x e 2x, medidor vazio/metade/cheio, placas de cada tipo, interior,
                        leitura em 5 pinturas, icones e blueprints
  logistica_fita.png    a Fita (teto solto/grudado, interior), as 4 posicoes em volta de maquinas (teto e interior,
                        2x e 1x) e os quadros do FX dos cartuchos
  logistica_fita.gif    ilustracao: Fita numa fabrica, num paiol e numa arma longe uma da outra na mesma nave; os
                        cartuchos saem da fabrica, entram no paiol, saem do paiol e entram na arma; a luz verde
So le art3d/ (PNGs); nao altera nada no repositorio fora destas 3 imagens.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))
import compose_logistica as C  # noqa: E402

ROOT = C.ART
OUT = os.path.join(C.REPO, "docs", "preview", "3d", "v2")
FAMS = ["cartuchos", "celulas", "misseis", "projeteis"]
KINDS = {"cartuchos": ["he", "ap", "sap", "ac", "frag"], "celulas": ["plasma", "pem"],
         "misseis": ["msl_he", "msl_cluster", "msl_emp", "msl_nuke"], "projeteis": ["slug"]}
KIND_NAME = {"he": "HE", "ap": "AP", "sap": "SAP", "ac": "AC", "frag": "FRAG", "plasma": "Plasma", "pem": "PEM",
             "msl_he": "Míssil HE", "msl_cluster": "Submunição", "msl_emp": "Míssil PEM",
             "msl_nuke": "Ogiva Nuclear", "slug": "Projétil de Railgun"}
KIND_LONG = {"he": "Alto-Explosivo", "ap": "Perfurante", "sap": "Semiperfurante", "ac": "Alta Capacidade",
             "frag": "Nuvem de Fragmentos", "plasma": "Célula de Plasma", "pem": "Célula PEM",
             "msl_he": "carga de míssil", "msl_cluster": "carga de submunição", "msl_emp": "carga PEM",
             "msl_nuke": "ogiva nuclear", "slug": "slug do Tupã"}
FAM_TITLE = {"cartuchos": "Paiol de Cartuchos · HE, AP, SAP, AC e FRAG (seletor de munição)",
             "celulas": "Paiol de Células · Plasma e PEM (seletor de célula)",
             "misseis": "Paiol de Mísseis · HE, Submunição, PEM e Ogiva Nuclear (seletor de míssil)",
             "projeteis": "Paiol de Projéteis · Projétil de Railgun (tipo único: placa fixa)"}
FAM_CHIP = {"cartuchos": "chip âmbar", "celulas": "chip ciano", "misseis": "chip laranja",
            "projeteis": "chip azul com pontas laranja (paleta nova do Tupã)"}
LEVELS = {"1x1": 5, "2x2": 8, "3x3": 10}
ICON2 = {"he": "ammo_he", "ap": "ammo_ap", "sap": "ammo_sap", "ac": "ammo_ac", "frag": "ammo_frag",
         "plasma": "cell_plasma", "pem": "cell_pem", "msl_he": "missile_he", "msl_cluster": "missile_cluster",
         "msl_emp": "missile_emp", "msl_nuke": "missile_nuclear", "slug": "slug_rail"}
HULLS = [("casco branco", (232, 234, 238)), ("cinza-claro", (176, 180, 186)), ("vermelho", (150, 40, 36)),
         ("azul-marinho", (46, 58, 74)), ("escuro", (30, 32, 36))]
NX = "×"


def z(img, k):
    return img.resize((img.width * k, img.height * k), Image.LANCZOS)


def zn(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


# ============================================================================ logistica_paiois.png
def make_paiois():
    rows = []
    for fam in FAMS:
        ks = KINDS[fam]
        items, i = [], 0
        for n in ("1x1", "2x2", "3x3"):
            N = LEVELS[n]
            for lv, lab in ((0, "vazio"), ((N + 1) // 2, "metade"), (N, "cheio")):
                k = ks[i % len(ks)]
                i += 1
                img = C.on_hull(C.paiol(n, fam, lv, k, root=ROOT), C.PAINT, 0.25)
                items.append((img, f"{n.replace('x', NX)} · {lab}\n{KIND_NAME[k]}", None))
        big = {"cartuchos": ("2x2", 4, "sap", "0138"), "celulas": ("2x2", 8, "pem", "0276"),
               "misseis": ("3x3", 5, "msl_nuke", "0021"), "projeteis": ("3x3", 10, "slug", "0234")}[fam]
        n, lv, k, dg = big
        img = C.on_hull(C.paiol(n, fam, lv, k, digits=dg, root=ROOT), C.PAINT, 0.25, scale=2)
        items.append((img, f"{n.replace('x', NX)} · 2x · {KIND_NAME[k]}\ncontador ligado ({dg})", C.NEWC))
        rows.append((FAM_TITLE[fam], f"1x (escala do jogo) e 2x · {FAM_CHIP[fam]} na borda de baixo da tampa · "
                     f"medidor de {LEVELS['1x1']} / {LEVELS['2x2']} / {LEVELS['3x3']} segmentos", items))

    # os 3 tamanhos a 2x (toda familia aparece em todo tamanho a 2x somando com as linhas de cima)
    items = []
    for n, fam, lv, k in (("1x1", "cartuchos", 3, "ap"), ("1x1", "celulas", 5, "plasma"), ("1x1", "misseis", 1, "msl_emp"),
                          ("1x1", "projeteis", 4, "slug"), ("2x2", "misseis", 6, "msl_he"),
                          ("2x2", "projeteis", 3, "slug"), ("3x3", "cartuchos", 9, "frag"),
                          ("3x3", "celulas", 4, "pem")):
        N = LEVELS[n]
        img = C.on_hull(C.paiol(n, fam, lv, k, root=ROOT), C.PAINT, 0.25, scale=2)
        items.append((img, f"{n.replace('x', NX)} · 2x · {fam}\n{KIND_NAME[k]} · {lv}/{N}", None))
    rows.append(("Os 3 tamanhos ampliados 2x (teto pintado)", "com as linhas de cima, toda família aparece em todo "
                 "tamanho a 2x; o 1×1 tem só a placa e o medidor (sem dígitos nem escotilhas)", items))

    # placas de tipo
    pd = os.path.join(ROOT, "bs_placas")
    items = []
    for fam in FAMS:
        for k in KINDS[fam]:
            pl = C.load(pd, f"placa_{k}.png")
            cell = Image.new("RGBA", (144 + 6 + 72, 144 + 8 + 59), C.BG + (255,))
            back = C.hull_field(144, 144, C.PAINT)
            back.alpha_composite(zn(pl, 3))
            cell.alpha_composite(back, (0, 0))
            ic = C.load(os.path.join(ROOT, "bs_ui_icons2"), ICON2[k] + ".png").resize((72, 72), Image.LANCZOS)
            ib = Image.new("RGBA", (72, 72), (24, 27, 33, 255))
            ib.alpha_composite(ic)
            cell.alpha_composite(ib, (150, 36))
            x = 0
            for s in (27, 42, 59):
                hb = C.hull_field(s + 6, s + 6, C.PAINT)
                hb.alpha_composite(pl.resize((s, s), Image.LANCZOS), (3, 3))
                cell.alpha_composite(hb, (x, 144 + 8 + 59 - (s + 6)))
                x += s + 6 + 4
            items.append((cell, f"{KIND_NAME[k]}\n{KIND_LONG[k]}", None))
    rows.append(("Placas de tipo (placa_<tipo>.png, 48 px)", "3x em cima (com o botão do seletor 2.0 ao lado); "
                 "embaixo no tamanho do encaixe no jogo: paiol 1×1 (0,42 quadro), 2×2 (0,66) e 3×3 (0,92). A MESMA "
                 "silhueta do botão do seletor, na cor do tipo, em baixo relevo, numa moldura escura com 2 parafusos "
                 "(sem emissão)", items))

    # interior
    items = []
    for n in ("1x1", "2x2", "3x3"):
        items.append((C.on_hull(C.paiol(n, "cartuchos", root=ROOT, roof=False), C.PAINT, 0.25),
                      f"{n.replace('x', NX)} · 1x", None))
    for n in ("1x1", "2x2", "3x3"):
        items.append((C.on_hull(C.paiol(n, "cartuchos", root=ROOT, roof=False), C.PAINT, 0.25, scale=2),
                      f"{n.replace('x', NX)} · 2x", None))
    rows.append(("Interior (teto escondido)", "estantes de cassetes neutros no perímetro, corredor central livre com "
                 "a plataforma de teletransporte (onde a munição chega); serve também no modo tripulação (sala andável)",
                 items))

    # leitura em pinturas
    items = []
    for hname, paint in HULLS:
        items.append((C.on_hull(C.paiol("2x2", "misseis", 4, "msl_cluster", paint=paint, root=ROOT), paint, 0.3),
                      f"{hname} · 1x", None))
    items.append((C.on_hull(C.paiol("3x3", "cartuchos", 7, "ac", paint=HULLS[0][1], digits="0157", root=ROOT),
                            HULLS[0][1], 0.25, scale=2), "casco branco · 2x", None))
    items.append((C.on_space(C.paiol("3x3", "celulas", 2, "plasma", root=ROOT), pad=16, scale=2),
                  "no espaço escuro · 2x\n(medidor baixo, vermelho)", None))
    rows.append(("Conferência de leitura: 5 pinturas do casco e o espaço", "o teto da peça e o casco em volta recebem a "
                 "mesma pintura; o aro de blindagem escura, as janelas pretas e a placa desenham o paiol em qualquer cor",
                 items))

    # icones e blueprints
    d = os.path.join(ROOT, "bs_paiol")
    items = []
    for n in ("1x1", "2x2", "3x3"):
        for fam in FAMS:
            items.append((C.on_space(C.load(d, f"icon_{fam}_{n}.png"), pad=4), f"icon_{fam}_{n}", None))
    for n in ("1x1", "2x2", "3x3"):
        items.append((C.on_space(C.load(d, f"blueprints_{n}.png"), pad=4), f"blueprints_{n}", None))
    rows.append(("Ícones do editor (64 px por quadro) e blueprints", None, items))

    header = [("Paióis da 2.0: cartuchos · células · mísseis · projéteis", C.font(30, True), C.TEXT),
              ("Como aparecem no jogo (64 px por quadro) com o teto pintado; 2x = ampliado 2 vezes. Tampa blindada "
               "SELADA, sem escotilha de tripulação (como a bateria térmica do jogo base): aro de blindagem, uma placa "
               "pintada por quadro com vão escuro entre elas (o ritmo dos tetos das fábricas), travas de vedação e, "
               "nos maiores, escotilhas de alívio blindadas (disco de ruptura sextavado / grelha) com fenda de LED.",
               C.font(15), C.DIM),
              ("Medidor no vidro à direita (5 / 8 / 10 segmentos): vermelho-laranja quando baixo, âmbar na metade, "
               "verde cheio; vazio = só os segmentos apagados do teto. Placa = o tipo escolhido no seletor (fixa nos "
               "projéteis). Contador de 4 dígitos âmbar: opcional (switch paiol_counter).", C.font(15), C.DIM),
              ("Chip da família na borda de baixo da tampa (3 px, sem emissão): âmbar = cartuchos, ciano = células, "
               "laranja = mísseis, azul com pontas laranja = projéteis. Não gira (IsRotateable = false): placa, "
               "dígitos e medidor ficam sempre em pé.", C.font(15), C.DIM)]
    img = C.sheet(header, rows)
    p = os.path.join(OUT, "logistica_paiois.png")
    img.save(p, optimize=True)
    return p, img.size



# ============================================================================ logistica_fita.png
FACTORY = "bs_factory_mag_std"        # Prensa de Carregadores (F1), arte aprovada da 1.x so como exemplo de maquina
GUN = "bs_autocannon_20"              # Carcara 2x2 (usa cartuchos)


def _scenes():
    """As 5 cenas das posicoes: (titulo, Scene, [(x, y) das fitas])."""
    out = []
    S = C.Scene(4, 5, root=ROOT)                     # fita EM CIMA de um paiol 2x2
    S.add_paiol("2x2", "cartuchos", 1, 2, level=5, kind="he")
    S.add_fita(1, 1)
    out.append(("em cima de um paiol 2×2", S))
    S = C.Scene(5, 4, root=ROOT)                     # fita A DIREITA de uma fabrica
    S.add_factory(FACTORY, 1, 1, working=False)
    S.add_fita(3, 2)
    out.append(("à direita de uma fábrica", S))
    S = C.Scene(4, 5, root=ROOT)                     # fita EMBAIXO de uma arma
    S.add_gun(GUN, 1, 1, angle=0)
    S.add_fita(2, 3)
    out.append(("embaixo de uma arma (Carcará)", S))
    S = C.Scene(4, 3, root=ROOT)                     # fita A ESQUERDA de um paiol 1x1
    S.add_paiol("1x1", "celulas", 2, 1, level=3, kind="pem")
    S.add_fita(1, 1)
    out.append(("à esquerda de um paiol 1×1", S))
    S = C.Scene(7, 4, root=ROOT)                     # fita ENTRE duas maquinas: liga as duas
    S.add_factory(FACTORY, 1, 1, working=False)
    S.add_fita(3, 1)
    S.add_paiol("2x2", "cartuchos", 4, 1, level=2, kind="he")
    out.append(("entre duas máquinas: liga as duas", S))
    return out


def fx_place(n):
    """Location (centro, quadros da peca) e Size (quadros) PADRAO do FX da Fita no paiol <n> (meta fita_fx)."""
    m = C.paiol_meta(ROOT)["parts"][n].get("fita_fx") or {"location": [int(n[0]) / 2] * 2, "size": [1, 1]}
    return tuple(m["location"]), float(m["size"][0])


def put_fx(S, layer, spr, cx, cy, size, mode="alpha"):
    """Sprite do FX (64 px = 1 quadro) com Size em quadros e centro (cx, cy) da cena, como o Graphics do jogo."""
    if abs(size - 1.0) > 1e-6:
        spr = spr.resize((int(round(spr.width * size)), int(round(spr.height * size))), Image.LANCZOS)
    S.put_center(layer, spr, cx, cy, mode)


def _fx_strip(kind, roof=True, k=3):
    """Os 8 quadros do FX no painel livre de um paiol 2x2 (Location / Size padrao do meta), recorte de 1,3 quadro,
    ampliados k."""
    d = os.path.join(ROOT, "bs_fita_fx")
    (lx, ly), size = fx_place("2x2")
    cells = []
    for i in range(1, 9):
        S = C.Scene(4, 4, root=ROOT)
        S.add_paiol("2x2", "cartuchos", 1, 1, level=4, kind="he")
        if roof:
            put_fx(S, "roof_doodads", C.load(d, f"cartucho_{kind}{i}.png"), 1 + lx, 1 + ly, size)
        else:
            put_fx(S, "lights_add", C.load(d, f"brilho_{kind}{i}.png"), 1 + lx, 1 + ly, size, "add")
        img = S.render(roof=roof)
        cx, cy, h = (1 + lx) * C.PX, (1 + ly) * C.PX, 0.65 * C.PX
        img = img.crop((int(cx - h), int(cy - h), int(cx + h), int(cy + h)))
        cells.append((z(img, k), f"quadro {i}", None))
    return cells


def make_fita():
    d = os.path.join(ROOT, "bs_fita")
    rows = []
    # ---------------------------------------------------------------- a peca
    items = [
        (C.on_hull(C.fita(linked=True, root=ROOT), C.PAINT, 0.5), "1x · grudada", None),
        (C.on_hull(C.fita(linked=False, root=ROOT), C.PAINT, 0.25, scale=3), "3x · solta\n(luz apagada)", None),
        (C.on_hull(C.fita(linked=True, root=ROOT), C.PAINT, 0.25, scale=3), "3x · grudada\n(luz verde nas garras)",
         C.GREENC),
        (C.on_hull(C.fita(linked=False, roof=False, root=ROOT), C.PAINT, 0.25, scale=3), "3x · interior · solta", None),
        (C.on_hull(C.fita(linked=True, roof=False, root=ROOT), C.PAINT, 0.25, scale=3), "3x · interior · grudada",
         C.GREENC),
        (C.on_hull(C.fita(linked=True, paint=HULLS[0][1], root=ROOT), HULLS[0][1], 0.25, scale=3),
         "3x · casco branco", None),
        (C.on_hull(C.fita(linked=True, paint=HULLS[4][1], root=ROOT), HULLS[4][1], 0.25, scale=3),
         "3x · casco escuro", None),
        (C.on_space(zn(C.load(d, "icon.png"), 4), pad=6), "ícone do editor\n32 px (4x)", None),
        (C.on_space(zn(C.load(d, "blueprints.png"), 3), pad=6), "blueprint (3x)", None),
    ]
    rows.append(("A peça (1×1, não gira, gruda em qualquer lado)", "tampa blindada sobre um anel escuro com o "
                 "símbolo da fita (o mesmo cassete neutro que some e aparece nas máquinas) e 4 setas; 4 garras de aço "
                 "que mordem a máquina vizinha, com a lente verde entre os dentes; no interior, a plataforma de "
                 "teletransporte e o trilho curto em cruz", items))
    sc = _scenes()
    rows.append(("As 4 posições em volta das máquinas · com teto (2x)", "a luz verde acende quando a máquina responde "
                 "(buff BulletStrike_FitaAck); a fábrica e a arma aqui são só exemplos de máquina",
                 [(z(S.render(True, margin=0.15), 2), lab, None) for lab, S in sc]))
    rows.append(("As mesmas posições · interior, teto escondido (2x)", "os 4 LEDs verdes do piso (luz_grudada.png, "
                 "lights_add) e a plataforma de teletransporte",
                 [(z(S.render(False, margin=0.15), 2), lab, None) for lab, S in sc]))
    rows.append(("Escala do jogo (1x)", None, [(S.render(True, margin=0.15), lab, None) for lab, S in sc]))
    (lx, ly), fs = fx_place("2x2")
    br = lambda v, k: f"{v:.{k}f}".replace(".", ",")                   # noqa: E731  (decimal com virgula)
    rows.append((f"Cartuchos SAINDO (cartucho_sai1..8, 0,075 s por quadro) · no painel livre de um paiol 2×2 "
                 f"(Location padrão {br(lx, 2)}; {br(ly, 2)}, Size {br(fs, 1)}), 3x",
                 "2 cassetes neutros (cápsula escura, faixa de latão, pip âmbar) sobem do centro, deslizam para a borda e "
                 "somem no teletransporte (linhas de varredura, tom ciano, linha de luz)", _fx_strip("sai")))
    rows.append(("Cartuchos ENTRANDO (cartucho_entra1..8) · o inverso: aparecem na borda e descem para o centro", None,
                 _fx_strip("entra")))
    rows.append(("Rastro do teletransporte no interior (brilho_sai1..8, lights_add, ciano baixo)", None,
                 _fx_strip("sai", roof=False)))
    header = [("Fita de Alimentação (2.0): grude do lado da máquina e a munição se teletransporta", C.font(30, True),
               C.TEXT),
              ("Peça 1×1 que você gruda do lado de uma fábrica, paiol ou arma do Bullet Strike. A munição passa sozinha "
               "de uma máquina para a outra, de um canto ao outro da nave — sem esteira, sem caminho e sem tripulação "
               "(\"imagina que tem uma esteira por baixo da nave, mas não tem\").", C.font(15), C.DIM),
              ("Mesmo desenho dos 4 lados (a peça não gira). Com o teto ligado a luz verde aparece nas lentes das garras "
               "(luz_grudada_teto.png, roof_doodads); na vista do interior, nos LEDs do piso (luz_grudada.png).",
               C.font(15), C.DIM),
              ("Embaixo, o efeito que toda máquina mostra a cada envio/recebimento: um conjunto só para todas as máquinas "
               "e todos os tipos (o cassete é neutro), 1 quadro no centro da máquina; nos paióis, no painel pintado livre "
               "da tampa (fora da placa, dos dígitos e das escotilhas).", C.font(15), C.DIM)]
    img = C.sheet(header, rows)
    p = os.path.join(OUT, "logistica_fita.png")
    img.save(p, optimize=True)
    return p, img.size



# ============================================================================ logistica_fita.gif
GIF_GUN = "bs_naval_76"               # Tambor 3x4 (cartuchos); a fileira de tras fica livre da cabeca da torre
DT = 0.075                            # 1 quadro do GIF = 1 quadro do FX (0,075 s)
SHIP_W, SHIP_H = 18, 9
POS = {"fab": (1, 4), "fita_fab": (3, 4), "paiol": (7, 2), "fita_paiol": (8, 4), "gun": (13, 4), "fita_gun": (12, 6)}
FX_AT = {"fab": (2.0, 5.0), "paiol": (8.0, 3.0), "gun": (14.5, 7.5)}     # centro do FX (quadros da cena); o do paiol
#                                                                         vem do meta (fita_fx) em _fx_at()
FX_SIZE = {"fab": 1.0, "paiol": 1.0, "gun": 1.0}


def _fx_at():
    (lx, ly), size = fx_place("2x2")
    FX_AT["paiol"] = (POS["paiol"][0] + lx, POS["paiol"][1] + ly)
    FX_SIZE["paiol"] = size
PHASES = [  # (quadro inicial, texto)
    (0, "1 · Grude a Fita do lado de cada máquina: a luz verde acende quando a máquina responde."),
    (12, "2 · A fábrica produz e envia: os cartuchos SOMEM da fábrica e APARECEM no paiol (teletransporte)."),
    (44, "3 · O paiol empurra para a arma: os cartuchos saem do paiol e entram na arma, que atira."),
    (76, "4 · Tudo ao mesmo tempo, de um canto ao outro da nave — sem esteira, sem caminho, sem tripulação."),
]
NF = 108


def _bezier(p0, p1, sag):
    """Curva da 'esteira imaginaria' (so ilustracao): quadratica que passa por baixo da reta (desce sag quadros)."""
    mx, my = (p0[0] + p1[0]) / 2, max(p0[1], p1[1]) + sag
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * mx + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * my + t * t * p1[1]) for t in np.linspace(0, 1, 60)]


def _dots(img, pts, phase, alpha):
    """Pontos ciano andando ao longo da curva (fase 0..1); alfa baixo: e so a ilustracao do 'por baixo da nave'."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(lay)
    n = len(pts)
    for k in range(0, n, 3):
        q = (k / n - phase) % 1.0
        a = int(alpha * (0.35 + 0.65 * (1 - q) ** 2))
        x, y = pts[k][0] * C.PX, pts[k][1] * C.PX
        dr.ellipse([x - 2.2, y - 2.2, x + 2.2, y + 2.2], fill=(90, 220, 255, a))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.6)))
    return img


def _state(f):
    """Estado da animacao no quadro f."""
    st = {"fitas": [f >= 2, f >= 5, f >= 8], "fab": None, "p_in": None, "p_out": None, "g_in": None, "shots": [],
          "lvl": 2, "link1": False, "link2": False}
    # fabrica -> paiol: fase 2 (12..43) e fase 4 (76..107), ciclos de 8 quadros
    for a, b in ((12, 44), (76, NF)):
        if a <= f < b:
            k = (f - a) % 8
            st["fab"], st["p_in"] = k + 1, k + 1
            st["link1"] = True
    # paiol -> arma: fase 3 (44..75) e fase 4 com 4 quadros de defasagem
    for a, b in ((44, 76), (80, NF)):
        if a <= f < b:
            k = (f - a) % 8
            st["p_out"], st["g_in"] = k + 1, k + 1
            st["link2"] = True
    # nivel do paiol: sobe 1 por ciclo na fase 2 (2 -> 6), desce na fase 3 (6 -> 2), fica na fase 4
    if f >= 12:
        st["lvl"] = 2 + min(4, (min(f, 44) - 12) // 8 + (1 if f >= 20 else 0))
    if f >= 44:
        st["lvl"] = max(2, 6 - ((min(f, 76) - 44) // 8 + (1 if f >= 52 else 0)))
    if f >= 76:
        st["lvl"] = 3 + ((f - 76) // 8) % 2
    # tiros da arma (Tambor, um cano): fase 3 e 4
    st["shots"] = [s for s in (50, 62, 74, 86, 98) if s <= f]
    return st


def _frame(f, CP):
    st = _state(f)
    hull = {(x, y) for x in range(SHIP_W) for y in range(1, SHIP_H)}
    S = C.Scene(SHIP_W, SHIP_H + 1, hull=hull, root=ROOT)
    fx = os.path.join(ROOT, "bs_fita_fx")
    S.add_factory(FACTORY, *POS["fab"], working=st["fab"] is not None)
    S.add_paiol("2x2", "cartuchos", *POS["paiol"], level=st["lvl"], kind="he")
    # arma: recuo + clarao + fumaca do ultimo tiro
    m = json.load(open(os.path.join(ROOT, GIF_GUN, "meta.json")))
    br = m["barrel"]
    seq = br["frames"]
    bname, gfx = br["rest"], []
    if st["shots"]:
        age = (f - st["shots"][-1]) * DT
        idx = int(age / br["interval"])
        if idx < len(seq) - 1:
            bname = seq[idx]
        fa = f - st["shots"][-1]
        if fa < 3:
            gfx.append((CP.flash(1.0, fa / 3, seed=st["shots"][-1]), br["muzzle"], 0.0, True))
        if fa < 10:
            gfx.append((CP.smoke(1.0, fa / 10, seed=st["shots"][-1]), br["muzzle"] + 0.2, 0.0, False))
    S.add_gun(GIF_GUN, *POS["gun"], angle=-18, bframes=[bname], fx=gfx)
    for i, key in enumerate(("fita_fab", "fita_paiol", "fita_gun")):
        S.add_fita(*POS[key], linked=st["fitas"][i])
    # FX dos cartuchos (roof_doodads, centro da maquina; na arma, a fileira de tras)
    for key, name, at in (("fab", "cartucho_sai", "fab"), ("p_in", "cartucho_entra", "paiol"),
                          ("p_out", "cartucho_sai", "paiol"), ("g_in", "cartucho_entra", "gun")):
        if st[key]:
            cx, cy = FX_AT[at]
            put_fx(S, "roof_doodads", C.load(fx, f"{name}{st[key]}.png"), cx, cy, FX_SIZE[at])
    img = S.render(roof=True)
    # 'esteira imaginaria' (so ilustracao): pontos ciano fracos por baixo da nave entre as maquinas ligadas
    if st["link1"]:
        img = _dots(img, _bezier(FX_AT["fab"], FX_AT["paiol"], 2.2), (f % 16) / 16, 120)
    if st["link2"]:
        img = _dots(img, _bezier(FX_AT["paiol"], FX_AT["gun"], 1.6), (f % 16) / 16, 120)
    return img, st


# cores que o GIF precisa ter exatas (a paleta da 1a versao, feita so com a MEDIANCUT de 6 quadros, perdia o verde da
# ligacao: as lentes saiam ambar): o verde aceso da Fita, as cores do texto e as do medidor
RESERVED = [C.BG, C.TEXT, C.DIM, C.GOLD, C.NEWC, C.GREENC, (111, 255, 0), (150, 255, 60), (60, 200, 0),
            (255, 70, 30), (255, 200, 40), (88, 240, 14)]


def gif_palette(frames, n_sat=104, n_all=255):
    """UMA paleta para o GIF inteiro (os quadros ficam com a mesma tabela e o GIF so grava o que muda: ~2 MB em vez de
    ~20 MB com paleta por quadro), montada para NAO perder as cores pequenas: as reservadas (verde aceso da Fita,
    texto, medidor) + uma paleta so dos pixels SATURADOS de todos os quadros (verde da ligacao, ciano do
    teletransporte, ambar dos pips, cores do medidor e das placas: poucos pixels que a MEDIANCUT do quadro inteiro
    trocaria pelo ambar, o defeito da 1a versao) + a paleta do resto (amostras de varios quadros)."""
    pal = [tuple(c) for c in RESERVED]
    sat_px, all_px = [], []
    for k, im in enumerate(frames):
        a = np.asarray(im.convert("RGB")).astype(np.int16)
        mx, mn = a.max(axis=2), a.min(axis=2)
        sat = ((mx - mn) > 45) & (mx > 60)
        sat_px.append(a[sat][::2])
        if k % 6 == 0:
            all_px.append(a.reshape(-1, 3)[::7])
    sp = np.concatenate(sat_px).astype(np.uint8)
    sq = Image.fromarray(sp[None, :, :], "RGB").quantize(colors=n_sat, method=Image.Quantize.MEDIANCUT,
                                                         dither=Image.Dither.NONE)
    used = sorted(set(np.asarray(sq).ravel().tolist()))
    p = sq.getpalette()
    pal += [tuple(p[3 * i:3 * i + 3]) for i in used]
    ap = np.concatenate(all_px).astype(np.uint8)
    fq = Image.fromarray(ap[None, :, :], "RGB").quantize(colors=n_all - len(pal), method=Image.Quantize.MEDIANCUT,
                                                         dither=Image.Dither.NONE)
    used = sorted(set(np.asarray(fq).ravel().tolist()))
    p = fq.getpalette()
    pal += [tuple(p[3 * i:3 * i + 3]) for i in used]
    pal = pal[:256]
    flat = [v for c in pal for v in c] + [0, 0, 0] * (256 - len(pal))
    pimg = Image.new("P", (1, 1))
    pimg.putpalette(flat)
    return pimg


def make_gif():
    import compose_preview as CP
    _fx_at()
    frames = []
    crops = {"fab": (0.5, 3.0, 3.5, 3.0), "paiol": (6.5, 1.5, 3.0, 3.5), "gun": (11.5, 4.5, 4.6, 3.6)}
    labels = {"fab": "fábrica + Fita (2x)", "paiol": "paiol de cartuchos + Fita (2x)", "gun": "Tambor (fileira de trás) + Fita (2x)"}
    tf, sf, lf, cf = C.font(22, True), C.font(15), C.font(16, True), C.font(17, True)
    pad = 18
    for f in range(NF):
        scene, st = _frame(f, CP)
        panels = []
        for key in ("fab", "paiol", "gun"):
            x, y, w, h = crops[key]
            c = scene.crop((int(x * C.PX), int(y * C.PX), int((x + w) * C.PX), int((y + h) * C.PX)))
            panels.append((z(c, 2), labels[key]))
        pw = sum(p.width for p, _ in panels) + pad * (len(panels) - 1)
        W = max(scene.width, pw) + 2 * pad
        ph = max(p.height for p, _ in panels)
        H = 92 + scene.height + 34 + ph + 34 + 60
        img = Image.new("RGB", (W, H), C.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), "Fita de Alimentação: fábrica → paiol → arma, longe uma da outra na mesma nave", font=tf,
                fill=C.TEXT)
        dr.text((pad, 44), "Em cima: a nave na escala do jogo (64 px por quadro), teto ligado. Embaixo: as 3 máquinas "
                "ampliadas 2x. 1 quadro = 0,075 s em média (70/80 ms alternados; o mesmo dos 8 quadros do efeito).",
                font=sf, fill=C.DIM)
        dr.text((pad, 64), "Os pontos ciano mostram o caminho imaginário \"por baixo da nave\" — só ilustração: no jogo "
                "não aparece linha nenhuma, só os cartuchos sumindo e aparecendo.", font=sf, fill=C.DIM)
        y0 = 92
        sx0 = (W - scene.width) // 2
        img.paste(scene.convert("RGB"), (sx0, y0))
        for key, nm in (("fab", "fábrica"), ("paiol", "paiol"), ("gun", "arma (Tambor)")):
            cx = FX_AT[key][0] if key != "paiol" else POS["paiol"][0] + 1.0
            dr.text((sx0 + cx * C.PX - dr.textlength(nm, font=lf) / 2, y0 + (1.2 if key != "gun" else 8.2) * C.PX - 6),
                    nm, font=lf, fill=C.GOLD)
        y1 = y0 + scene.height + 34
        x = (W - pw) // 2
        for p, lab in panels:
            img.paste(p.convert("RGB"), (x, y1 + ph - p.height))
            dr.text((x + 4, y1 + ph + 6), lab, font=sf, fill=C.DIM)
            x += p.width + pad
        txt = [t for a, t in PHASES if f >= a][-1]
        dr.text((pad, H - 46), txt, font=cf, fill=C.GREENC if f < 12 else C.NEWC)
        frames.append(img)
    gp = gif_palette(frames)
    pal = [im.convert("RGB").quantize(palette=gp, dither=Image.Dither.NONE) for im in frames]
    p = os.path.join(OUT, "logistica_fita.gif")
    # o GIF guarda centesimos de segundo: 75 ms nao existe; 70/80 alternados = 0,075 s em media (o mesmo do FX)
    dur = [70 if i % 2 == 0 else 80 for i in range(len(pal))]
    pal[0].save(p, save_all=True, append_images=pal[1:], duration=dur, loop=0, optimize=True, disposal=1)
    return p, frames[0].size, len(frames)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--root" in args:
        ROOT = args[args.index("--root") + 1]
        C.ART = ROOT
    if "--out" in args:
        OUT = args[args.index("--out") + 1]
    what = args[0] if args and not args[0].startswith("--") else "todas"
    os.makedirs(OUT, exist_ok=True)
    for k in ("paiois", "fita", "gif"):
        fn = {"paiois": "make_paiois", "fita": "make_fita", "gif": "make_gif"}[k]
        if what in (k, "todas") and fn in globals():
            print(k, globals()[fn]())
