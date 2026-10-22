"""Previas finais: python3 make_sheets.py <pasta_arte> <pasta_saida> [futuristas|antes_depois|casco|luzes|todas]"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prev2 as PV  # noqa: E402

FX = PV.FX
BG = PV.SPACE
GROUPS = [
    ("Tambor 76 mm", "calibre leve", "luva de compósito lisa e 1 faixa de LED", ["he_s", "ap_s", "sap_s", "ac_s"]),
    ("Trovão 155 mm", "calibre médio", "luvas em divisa, anel de LED, fendas de trilho em V acesas no ombro do nariz",
     ["he_m", "ap_m", "sap_m", "ac_m"]),
    ("Mapinguari 406 mm", "calibre pesado", "blindagem segmentada, nariz sensor de lente escura, anel aceso na base",
     ["he_l", "ap_l", "sap_l", "ac_l"]),
    ("Boiúna", "obuseiro", "a 406 gorda: segmentada, nariz sensor, base-bleed âmbar com respiros acesos "
     "(sem trevo, sem verde); a única AC guiada; traçante fino da 2.0 em projeteis_antes_depois.png",
     ["he_h", "ac_h"]),
    ("PEM", "Tuvira · Treme-Treme · Corisco", "cápsula escura, bobinas de fio de cobre, luz ciano que pula entre "
     "as bobinas", ["pem_s", "pem_m", "pem_l"]),
    ("Tupã (railgun)", "slug", "dardo fino de tungstênio claro, 6 aletas curtas, colares EM AZUIS, ponta quente "
     "branco-azulada com o colar laranja (paleta azul da Tupã; sem cobre, sem chama)", ["slug"]),
]
NAME = {"pem_s": "Tuvira 40 mm", "pem_m": "Treme-Treme 76 mm", "pem_l": "Corisco 155 mm", "slug": "slug da Tupã"}


def item_name(k):
    if k in NAME:
        return NAME[k]
    return PV.AMMO_PT[k.split("_")[0]]


def zoom_name(k):
    """Rótulo curto dos ampliados (as células de 76 mm a 3x têm só ~190 px de largura)."""
    if k in NAME:
        return {"pem_s": "Tuvira", "pem_m": "Treme-Treme", "pem_l": "Corisco", "slug": "slug"}[k]
    return k.split("_")[0].upper()


def cell_1x(d, meta, key, lanes=("escuro",), frame=0, label=True, width_t=None, lane_h=None, halo_hull=True,
            title=None, P=64, head_k=1.0, head_dx=0.0, thin=None, stats=None):
    """Tiro a 1x (64 px/quadro; P=128 = zoom 2x do jogo) com todas as camadas, uma faixa por fundo (espaço /
    cascos). head_k / head_dx: proposta de clarão da base menor e recuado; thin: proposta de traçante fino (Boiúna).
    stats = lista: recebe, por faixa de casco, a fração da placa com os 3 canais >= 250 (estourada em branco)."""
    L, W = PV.new_body(meta, key)
    wt = width_t or (6 if L < 1.5 else (7 if L < 2.5 else 10))
    lh = lane_h or (1.5 if W < 0.5 else 2.0)
    top = 18 if label else 0
    w, h = int(wt * P), int(lh * P * len(lanes)) + top
    sc = PV.Scene(w, h)
    for i, ln in enumerate(lanes):
        y0 = top + int(i * lh * P)
        if ln != "espaço":
            col, line = PV.HULLS[ln]
            sc.plate(0, y0, wt, lh, P, col, line)
        PV.draw_new(sc, d, meta, key, w - int(0.45 * P), y0 + lh * P / 2, P, frame=frame, halo_hull=halo_hull,
                    head_k=head_k, head_dx=head_dx, thin=thin)
    im = sc.compose().image()
    if stats is not None:
        a = np.asarray(im)
        for i, ln in enumerate(lanes):
            if ln != "espaço":
                y0 = top + int(i * lh * P)
                stats.append((ln, float((a[y0:y0 + int(lh * P)] >= 250).all(2).mean())))
    if label:
        im.paste(BG, (0, 0, w, top))
        PV.label(im, 2, 2, title or item_name(key), 12, (235, 238, 245), True)
    return im


def cell_zoom(d, meta, key, z=3, frame=0, hull="escuro", label=True, stub=0.18, title=None):
    """SÓ o sprite (corpo + faixa + luzes do atlas) a z vezes a escala do jogo sobre placa de casco, sem traçante,
    sem núcleo e sem clarão: ampliado, qualquer pedaço do traçante vira uma 'pluma' colada na granada (crítica r1);
    o traçante do jogo está nas células de escala real."""
    P = 64 * z
    L, W = PV.new_body(meta, key)
    top = 18 if label else 0
    w = int((L + stub) * P) + 16
    h = int(max(W * 1.35, W + 0.12) * P) + top
    sc = PV.Scene(w, h, stars=False)
    col, line = PV.HULLS[hull]
    sc.plate(0, top, w / P + 1, (h - top) / P + 1, P, col, line)
    sc.hull[:top] = 0
    sc.alb[:top] = BG
    PV.draw_new(sc, d, meta, key, w - 8, top + (h - top) / 2, P, frame=frame, fx=0, lights=False, zoom=True)
    im = sc.compose().image()
    if label:
        im.paste(BG, (0, 0, w, top))
        PV.label(im, 2, 2, f"{title or zoom_name(key)}  {z}x", 12, (235, 238, 245), True)
    return im


def old_1x(tier, lanes=("espaço", "escuro"), width_t=7, lane_h=None, title="", P=64):
    pr = PV.TABLE["weapons"][PV.TIER_ROW[tier]]["projectile"]
    L, W = pr["body"]
    lh = lane_h or (1.5 if W < 0.5 else 2.0)
    top = 18
    w, h = int(width_t * P), int(lh * P * len(lanes)) + top
    sc = PV.Scene(w, h)
    for i, ln in enumerate(lanes):
        y0 = top + int(i * lh * P)
        if ln != "espaço":
            col, line = PV.HULLS[ln]
            sc.plate(0, y0, width_t, lh, P, col, line)
        PV.draw_old(sc, tier, w - int(0.45 * P), y0 + lh * P / 2, P)
    im = sc.compose().image()
    im.paste(BG, (0, 0, w, top))
    PV.label(im, 2, 2, title, 12, (235, 238, 245), True)
    return im


def old_zoom(tier, z=3, stub=0.18, title=""):
    P = 64 * z
    pr = PV.TABLE["weapons"][PV.TIER_ROW[tier]]["projectile"]
    nuke = pr["look"] == "nuke_shell"
    L, W = pr["body"]
    top = 18
    w = int((L + stub) * P) + 16
    h = int(max(W * 1.35, W + 0.12) * P) + top
    sc = PV.Scene(w, h, stars=False)
    col, line = PV.HULLS["escuro"]
    sc.plate(0, top, w / P + 1, (h - top) / P + 1, P, col, line)
    sc.hull[:top] = 0
    sc.alb[:top] = BG
    c = PV.OLD_COL["nuclear" if nuke else "std"]
    nose = w - 8
    cx = nose - 0.5 * L * P
    yc = top + (h - top) / 2
    it, dif, lt = PV.SH.shell_rgba(PV.OLD_DIR, PV.OLD_META, "nuke" if nuke else "he", c.get("band"),
                                   2 if nuke else None)
    sc.top.append((PV._draw_sprite, (dif, lt, cx, yc, L * P, W * P)))
    im = sc.compose().image()
    im.paste(BG, (0, 0, w, top))
    PV.label(im, 2, 2, f"{title}  {z}x", 12, (235, 238, 245), True)
    return im


def side_by_side(a, b, gap=10):
    out = Image.new("RGB", (a.width + gap + b.width, max(a.height, b.height)), BG)
    out.paste(a, (0, 0))
    out.paste(b, (a.width + gap, 0))
    return out


def sheet_antes_depois(d, outp):
    meta = json.load(open(os.path.join(d, "meta.json")))
    MAXW = 1840
    parts = [text_block([
        ("Escada de calibres: antes (1.x) e depois (2.0)", 22, (245, 246, 250), True),
        ("Antes: a MESMA granada de aço escuro com cinta de cobre em todos os calibres, só mudando o tamanho; "
         "a Boiúna disparava a granada nuclear. Depois: cada calibre tem a sua granada, e quanto maior, "
         "mais futurista.", 13, (205, 210, 220), False),
        ("Munição Alto-Explosivo. Por calibre: escala real (64 px por quadro) no espaço e sobre casco escuro; "
         "o mesmo tiro com o zoom 2x do jogo; e só o sprite ampliado 3x. "
         "Antes = efeitos da 1.x; depois = luzes da 2.0 (halo fraco + luz de casco tingida).", 12,
         (170, 176, 190), False),
    ], MAXW)]
    rows = [("s", "Tambor 76 mm", "he_s", "calibre leve: luva de compósito + faixa de LED"),
            ("m", "Trovão 155 mm", "he_m", "calibre médio: luvas em divisa + anel de LED + fendas de trilho em V"),
            ("l", "Mapinguari 406 mm", "he_l", "calibre pesado: blindagem segmentada + nariz sensor + anel aceso "
             "na base"),
            ("h", "Boiúna", "he_h", "obuseiro: granada âmbar com base-bleed aceso (a granada nuclear sai; sem trevo, "
             "sem verde)")]
    for tier, name, key, cue in rows:
        parts.append(text_block([(f"{name} — {cue}", 15, (255, 205, 120), True)], MAXW))
        a = old_1x(tier, title="ANTES (1.x)" + (": granada nuclear" if tier == "h" else ""))
        b = cell_1x(d, meta, key, lanes=("espaço", "escuro"), width_t=7, title="DEPOIS (2.0)")
        parts.append(side_by_side(a, b, 24))
        wt2 = 5 if tier in ("s", "m") else 6
        a2 = old_1x(tier, lanes=("escuro",), width_t=wt2, title="ANTES com zoom 2x do jogo", P=128)
        b2 = cell_1x(d, meta, key, lanes=("escuro",), width_t=wt2, title="DEPOIS com zoom 2x do jogo", P=128)
        parts.append(side_by_side(a2, b2, 24))
        za = old_zoom(tier, 3, title="ANTES")
        zb = cell_zoom(d, meta, key, 3, title="DEPOIS")
        parts.append(pack([za, zb], MAXW, gap=24))
    # proposta para o integrador: clarao da base menor e recuado (76 e 155 mm)
    parts.append(text_block([
        ("Adotado na 2.0 (ADDENDUM G7 f): clarão da base menor e recuado (Tambor e Trovão)", 15, (255, 205, 120),
         True),
        ("O clarão branco da base (cabeça do traçante, 1,6 x 'head' da 1.x) é maior que a granada de 76 mm e "
         "lava a traseira das luvas claras. Na 2.0: metade do diâmetro, recuado para trás da base (encostando nela). "
         "Escala real "
         "e zoom 2x.", 12, (170, 176, 190), False)], MAXW))
    for key, nm in (("he_s", "Tambor"), ("he_m", "Trovão")):
        cells = [cell_1x(d, meta, key, lanes=("espaço", "escuro"), width_t=5, title=f"{nm}: clarão da Fase B"),
                 cell_1x(d, meta, key, lanes=("espaço", "escuro"), width_t=5, title=f"{nm}: clarão da 2.0",
                         head_k=0.5, head_dx=0.15),
                 cell_1x(d, meta, key, lanes=("escuro",), width_t=3, title="Fase B (2x)", P=128),
                 cell_1x(d, meta, key, lanes=("escuro",), width_t=3, title="2.0 (2x)", P=128, head_k=0.5,
                         head_dx=0.15)]
        parts.append(pack(cells, MAXW, gap=16))
    # proposta para o integrador: tracante fino da Boiuna (sem 'chama de foguete' atras da granada)
    parts.append(text_block([
        ("Adotado na 2.0 (ADDENDUM G7 d): traçante fino na Boiúna (granada, não foguete)", 15, (255, 205, 120),
         True),
        ("O layout da Fase B do obuseiro (bs_nuke_howitzer: traçante 5 x 0,9 quadro, sem clarão na cabeça) põe o "
         "núcleo "
         "branco-quente colado na base e o traçante largo abre em pluma: com os respiros acesos e as aletas da AC, "
         "lê como míssil com chama.", 12, (170, 176, 190), False),
        ("Na 2.0: traçante 6,5 quadros com 45% da largura, núcleo curto (1,6 quadro, metade da largura) começando "
         "0,35 quadro atrás da base, rastro com metade da largura; traçante, núcleo e rastro com 75% da intensidade. "
         "Escala real e zoom 2x.", 12,
         (170, 176, 190), False)], MAXW))
    for key, nm in (("he_h", "Boiúna HE"), ("ac_h", "Boiúna AC")):
        cells = [cell_1x(d, meta, key, lanes=("espaço", "escuro"), width_t=6, title=f"{nm}: traçante da Fase B"),
                 cell_1x(d, meta, key, lanes=("espaço", "escuro"), width_t=6, title=f"{nm}: traçante da 2.0",
                         thin=BOIUNA_THIN),
                 cell_1x(d, meta, key, lanes=("escuro",), width_t=4, title="Fase B (2x)", P=128),
                 cell_1x(d, meta, key, lanes=("escuro",), width_t=4, title="2.0 (2x)", P=128,
                         thin=BOIUNA_THIN)]
        parts.append(pack(cells, MAXW, gap=16))
    im = stack(parts)
    im.save(outp)
    print(outp, im.size)


BOIUNA_THIN = {"tw": 0.45, "tl": 6.5, "kw": 0.5, "kl": 1.6, "kback": 0.35, "puff": 0.5, "gain": 0.75}


def pack(cells, max_w, gap=10, bg=BG):
    rows, cur, cw = [], [], 0
    for c in cells:
        if cur and cw + c.width + gap > max_w:
            rows.append(cur)
            cur, cw = [], 0
        cur.append(c)
        cw += c.width + gap
    if cur:
        rows.append(cur)
    W = max(sum(c.width for c in r) + gap * (len(r) - 1) for r in rows)
    H = sum(max(c.height for c in r) for r in rows) + gap * (len(rows) - 1)
    out = Image.new("RGB", (W, H), bg)
    y = 0
    for r in rows:
        x = 0
        for c in r:
            out.paste(c, (x, y))
            x += c.width + gap
        y += max(c.height for c in r) + gap
    return out


def stack(parts, gap=14, bg=BG, pad=16):
    W = max(p.width for p in parts) + 2 * pad
    H = sum(p.height for p in parts) + gap * (len(parts) - 1) + 2 * pad
    out = Image.new("RGB", (W, H), bg)
    y = pad
    for p in parts:
        out.paste(p, (pad, y))
        y += p.height + gap
    return out


def text_block(lines, w):
    """lines = [(texto, tamanho, cor, negrito)]"""
    h = sum(sz + 8 for _, sz, _, _ in lines) + 4
    im = Image.new("RGB", (w, h), BG)
    y = 2
    for t, sz, col, b in lines:
        PV.label(im, 0, y, t, sz, col, b)
        y += sz + 8
    return im


def sheet_futuristas(d, outp):
    meta = json.load(open(os.path.join(d, "meta.json")))
    MAXW = 1840
    parts = [text_block([
        ("Projéteis 2.0: quanto maior o calibre, mais futurista", 22, (245, 246, 250), True),
        ("Cada calibre tem a sua própria granada. Munição pela COR (faixa + LED + traçante) e pela SILHUETA: "
         "HE espoleta de ponta chata (no 406 e na Boiúna, nariz sensor fino e escalonado) ·", 13, (205, 210, 220),
         False),
        ("AP ogiva longa com capuz escuro de filete claro e ponta de penetrador · SAP capuz rombudo e largo · "
         "AC carmim e ouro com aletas de cauda (voa reta; só a AC da Boiúna é guiada: canards e buscador que "
         "pisca).",
         13, (205, 210, 220), False),
        ("Escala real = 64 px por quadro, com traçante, clarão da base, rastro e luzes como no jogo; cada tiro sobre o "
         "espaço e sobre um casco escuro. Abaixo de cada grupo, só o sprite ampliado 3x (sem traçante: ele está na "
         "escala real acima).", 12, (170, 176, 190), False),
    ], MAXW)]
    for name, tier, cue, keys in GROUPS:
        parts.append(text_block([(f"{name} — {tier}: {cue}", 15, (255, 205, 120), True)], MAXW))
        parts.append(pack([cell_1x(d, meta, k, lanes=("espaço", "escuro")) for k in keys], MAXW))
        parts.append(pack([cell_zoom(d, meta, k, 3) for k in keys], MAXW))
    im = stack(parts)
    im.save(outp)
    print(outp, im.size)


casco_branco_stats = {}


def sheet_casco(d, outp):
    meta = json.load(open(os.path.join(d, "meta.json")))
    MAXW = 1840
    parts = [text_block([
        ("Casco branco e cinza: os projéteis 2.0 continuam legíveis", 22, (245, 246, 250), True),
        ("Escala real (64 px por quadro) sobre casco branco e cinza claro, com traçante, clarão da base, rastro e a "
         "luz de casco pequena da 2.0 na cor da munição.", 13, (205, 210, 220), False),
        ("No casco BRANCO quase não há tinta: perto do tiro a luz, o núcleo do traçante e o clarão estouram em "
         "branco, e a cor da munição só aparece na borda da luz.", 13, (205, 210, 220), False),
        ("Nas fileiras por calibre o brilho grande fica de fora, para conferir só o desenho; no fim, o tiro como "
         "está hoje no jogo (o casco branco estoura) e a correção que entra na 2.0.", 12, (170, 176, 190), False),
        ("O contorno vem das frestas escuras entre as luvas claras, da cauda e do nariz escuros e da faixa colorida; "
         "o slug tem os colares azuis e a PEM é uma cápsula escura.", 12, (170, 176, 190), False),
    ], MAXW)]
    for name, tier, cue, keys in GROUPS:
        parts.append(text_block([(f"{name} — {tier}", 15, (255, 205, 120), True)], MAXW))
        parts.append(pack([cell_1x(d, meta, k, lanes=("branco", "cinza"), halo_hull=False) for k in keys], MAXW))
    sel = [("he_s", "Tambor HE"), ("ap_m", "Trovão AP"), ("sap_l", "Mapinguari SAP"), ("ac_h", "Boiúna AC"),
           ("pem_m", "Treme-Treme"), ("slug", "slug da Tupã")]

    def halo_row(halo_hull):
        cells = []
        for k, t in sel:
            st = []
            cell_1x(d, meta, k, lanes=("branco", "cinza"), halo_hull=halo_hull, stats=st)
            pct = round(100 * dict(st)["branco"])
            cells.append(cell_1x(d, meta, k, lanes=("branco", "cinza"), halo_hull=halo_hull,
                                 title=f"{t}: {pct}% branco estourado"))
            casco_branco_stats[(k, halo_hull)] = pct
        return pack(cells, MAXW)
    row = halo_row(True)
    S = casco_branco_stats
    parts.append(text_block([
        ("Como está hoje: perto do tiro, o casco branco fica todo branco (estoura)", 15,
         (255, 205, 120), True),
        (f"Quanto da placa branca estoura: Trovão AP {S[('ap_m', True)]}%, Boiúna AC {S[('ac_h', True)]}%, "
         f"Mapinguari SAP {S[('sap_l', True)]}%, Tambor HE {S[('he_s', True)]}%. A cor da munição só aparece na "
         "borda da luz.", 12, (170, 176, 190), False)], MAXW))
    parts.append(row)
    parts.append(text_block([
        ("Correção que entra na 2.0: o brilho grande fica só no espaço", 15, (255, 205, 120), True),
        ("No espaço o brilho continua igual. Sobre o casco fica só uma luz pequena na cor da munição, e a cor "
         "volta a aparecer.", 12, (170, 176, 190), False)], MAXW))
    parts.append(halo_row(False))
    parts.append(text_block([("Recorte ampliado 2x no casco branco", 15, (255, 205, 120), True)], MAXW))
    sel = [("he_s", "Tambor HE"), ("ap_m", "Trovão AP"), ("sap_l", "Mapinguari SAP"), ("ac_l", "Mapinguari AC"),
           ("he_h", "Boiúna HE"), ("pem_m", "Treme-Treme"), ("slug", "slug da Tupã")]
    parts.append(pack([cell_zoom(d, meta, k, 2, hull="branco", title=t) for k, t in sel], MAXW))
    im = stack(parts)
    im.save(outp)
    print(outp, im.size, "estourado (chave, halo no casco): %", casco_branco_stats)


SHORT = {"s": "Tambor 76", "m": "Trovão 155", "l": "Mapinguari 406", "h": "Boiúna"}
ANIM = {"s": "faixa de LED pisca", "m": "anel de LED / fendas em V alternam",
        "l": "scanner do visor + anel da base", "h": "scanner do visor + base-bleed âmbar",
        "ac": "luz parada (voa reta, sem buscador)", "pem_s": "faixa ciano pisca",
        "pem_m": "carga pula: vão 1 › vão 2 › nariz",
        "pem_l": "onda nas frestas entre as bobinas", "slug": "onda nos colares EM + ponta quente"}


def gif_label(k):
    """(linha 1 em negrito, linha 2)"""
    if k.startswith("pem_") or k == "slug":
        return NAME[k], ANIM[k]
    ammo, tier = k.split("_")
    an = ANIM["ac"] if ammo == "ac" and tier in ("s", "m", "l") else ANIM[tier]
    if ammo == "ac" and tier == "h":
        # so a AC da Boiuna e guiada (as AC dos canhoes tem 1 quadro de luz parado)
        an = "guiada: buscador + " + an.replace("scanner do visor", "scanner").replace(" âmbar", "")
    return f"{SHORT[tier]} · {ammo.upper()}", an


def gif_palette(rgb, n=255, iters=12, wsat=3.0):
    """Paleta global do GIF por k-means ponderado sobre as cores UNICAS de TODOS os quadros compostos (luzes sobre o
    corpo, cada quadro de cada celula). Peso = raiz da contagem, x wsat nas cores saturadas (max - min > 40): os
    tons raros e saturados (azul do slug, carmim da AC, ambar/ciano dos LEDs) ganham entradas proprias em vez de
    cair no cinza-azulado do corpo. Semente = median-cut das cores unicas. (A r1 usava median-cut de uma amostra:
    o violeta virava azul-claro.)"""
    allpx = np.concatenate([a.reshape(-1, 3) for a in rgb])
    u, c = np.unique(allpx, axis=0, return_counts=True)
    sat = u.max(1).astype(np.int16) - u.min(1)
    w = np.sqrt(c) * np.where(sat > 40, wsat, 1.0)
    X = u.astype(np.float32)
    seed = Image.fromarray(u.reshape(1, -1, 3).astype(np.uint8)).quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    C = np.array(seed.getpalette()[:n * 3], np.float32).reshape(-1, 3)
    for _ in range(iters):
        lab = np.empty(len(X), np.int32)
        for i in range(0, len(X), 20000):
            lab[i:i + 20000] = ((X[i:i + 20000, None, :] - C[None]) ** 2).sum(2).argmin(1)
        for j in range(n):
            m = lab == j
            if m.any():
                C[j] = (X[m] * w[m, None]).sum(0) / w[m].sum()
    pal = Image.new("P", (1, 1))
    pal.putpalette([int(round(v)) for v in C.clip(0, 255).ravel()] + [0, 0, 0] * (256 - n))
    return pal


def save_gif(frames, durs, path):
    """GIF com UMA paleta global (gif_palette) para todos os quadros (sem tremido no fundo); vizinho mais proximo,
    sem pontilhado. Do 2o quadro em diante, o pixel igual ao do quadro anterior vira o indice transparente 255
    (disposal 1 = o quadro anterior fica): so as luzes que mudam vao no arquivo (r2: ~2 MB -> menos da metade,
    sem perder resolucao). Confere a decodificacao contra os quadros quantizados."""
    rgb = [np.asarray(f.convert("RGB")) for f in frames]
    pal = gif_palette(rgb)
    q = [Image.fromarray(a).quantize(palette=pal, dither=Image.Dither.NONE) for a in rgb]
    idx = [np.asarray(f) for f in q]
    assert max(int(a.max()) for a in idx) < 255
    out = [q[0]]
    for prev, cur in zip(idx, idx[1:]):
        d = cur.copy()
        d[cur == prev] = 255
        im = Image.fromarray(d, "P")
        im.putpalette(q[0].getpalette())
        out.append(im)
    out[0].save(path, save_all=True, append_images=out[1:], duration=durs, loop=0, optimize=False, disposal=1,
                transparency=255)
    # conferencia: cada quadro decodificado = o quadro quantizado
    pal_rgb = np.array(q[0].getpalette()[:768], np.uint8).reshape(-1, 3)
    g = Image.open(path)
    n = 0
    try:
        while True:
            want = pal_rgb[idx[n]]
            got = np.asarray(g.convert("RGB"))
            bad = int((got != want).any(2).sum())
            if bad:
                raise SystemExit(f"GIF: quadro {n} decodificado difere em {bad} px")
            n += 1
            g.seek(g.tell() + 1)
    except EOFError:
        pass
    print("GIF conferido:", n, "quadros iguais aos quantizados")


def sheet_luzes(d, outp):
    from fractions import Fraction
    meta = json.load(open(os.path.join(d, "meta.json")))
    keys = list(meta["items"])
    fps = {k: meta["items"][k]["lights"]["fps"] for k in keys}
    nfr = {k: meta["items"][k]["lights"]["frames"] for k in keys}
    period = Fraction(2)
    times = sorted({Fraction(i, f) for f in set(fps.values()) for i in range(int(period * f))})
    times_ms = [int(round(float(t) * 1000 / 10)) * 10 for t in times]
    durs = [b - a for a, b in zip(times_ms, times_ms[1:] + [int(period * 1000)])]
    # celulas: sprite na resolucao da textura (128 px por quadro) sobre casco escuro
    P = 128
    lay = []
    for k in keys:
        it = meta["items"][k]
        pw, ph = it["px"]
        lay.append((k, pw + 16, ph + 40))
    MAXW = 1150
    rows, cur, cw = [], [], 0
    for c in lay:
        if cur and cw + c[1] + 8 > MAXW:
            rows.append(cur)
            cur, cw = [], 0
        cur.append(c)
        cw += c[1] + 8
    rows.append(cur)
    head = 58
    W = max(sum(c[1] for c in r) + 8 * (len(r) - 1) for r in rows) + 24
    H = head + sum(max(c[2] for c in r) for r in rows) + 8 * len(rows) + 12
    pos = {}
    y = head
    for r in rows:
        x = 12
        for k, cw_, ch in r:
            pos[k] = (x, y, cw_, ch)
            x += cw_ + 8
        y += max(c[2] for c in r) + 8
    # fundo fixo (placas + rotulos) e sprites/luzes por quadro
    base = PV.Scene(W, H, stars=True)
    col, line = PV.HULLS["escuro"]
    for k, (x, y, cw_, ch) in pos.items():
        base.plate(x, y + 32, (cw_) / P, (ch - 32) / P, P, col, line)
    bimg = base.compose().image()
    for k, (x, y, cw_, ch) in pos.items():
        l1, l2 = gif_label(k)
        PV.label(bimg, x, y + 1, l1, 12, (235, 238, 245), True)
        PV.label(bimg, x, y + 16, l2, 11, (175, 182, 195), False)
    PV.label(bimg, 12, 8, "Luzes dos projéteis 2.0 — ampliado (a textura tem 128 px por quadro; no jogo a 76 mm "
             "tem 46 px)", 16, (245, 246, 250), True)
    PV.label(bimg, 12, 32, "Cada atlas no fps do jogo: 76/155 mm 4 qps (AC dos canhões: luz parada), 406 mm e Boiúna "
             "6 qps, PEM 6/10/12 qps, slug 12 qps. LEDs em recessos escuros.", 12, (175, 182, 195), False)
    sprites = {}
    for k in keys:
        it = meta["items"][k]
        info = PV.proj_info(k)
        sprites[k] = [PV.sprite_rgba(d, meta, k, info["band"], f) for f in range(nfr[k])]
    frames = []
    for t in times:
        cv = FX.Canvas(W, H)
        cv.a = np.asarray(bimg, dtype=np.float32).copy()
        for k, (x, y, cw_, ch) in pos.items():
            f = int(t * fps[k]) % nfr[k]
            dif, lt = sprites[k][f]
            pw, ph = meta["items"][k]["px"]
            PV._draw_sprite(cv, dif, lt, x + cw_ / 2, y + 32 + (ch - 32) / 2, pw, ph)
        frames.append(cv.image())
    save_gif(frames, durs, outp)
    sheet_luzes.last = (frames, pos)
    print(outp, (W, H), len(frames), "quadros", sum(durs), "ms", "min dur", min(durs))


if __name__ == "__main__":
    d, od = sys.argv[1], sys.argv[2]
    what = sys.argv[3] if len(sys.argv) > 3 else "todas"
    os.makedirs(od, exist_ok=True)
    if what in ("futuristas", "todas"):
        sheet_futuristas(d, os.path.join(od, "projeteis_futuristas.png"))
    if what in ("casco", "todas"):
        sheet_casco(d, os.path.join(od, "projeteis_casco_branco.png"))
    if what in ("luzes", "todas"):
        sheet_luzes(d, os.path.join(od, "projeteis_luzes.gif"))
    if what in ("antes_depois", "todas"):
        sheet_antes_depois(d, os.path.join(od, "projeteis_antes_depois.png"))
