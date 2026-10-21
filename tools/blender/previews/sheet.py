"""Folha de contato das granadas (copia do WP7 no WP3: tabela do gerador, camadas do jogo): os 4 tamanhos do jogo (76 / 155 / 406 mm e Boiuna) sobre placas de casco,
com o tracante e o brilho das regras simulados (fxlib dos mocks de calibre) e a faixa tingida na cor da municao.

    python3 sheet.py <pasta_art> <saida.png>

Painel 1x = escala real do jogo (64 px/quadro); painel 3x = a mesma coisa ampliada (tracante encurtado).
O sprite e desenhado EXATAMENTE no tamanho 'body' da tabela (como fxkit.art_sprite_components vai usar), entao
qualquer diferenca de proporcao entre a tela e o tamanho no jogo aparece aqui."""
import json
import os
import sys

import numpy as np
from PIL import Image

# copia no repositorio (ADDENDUM G13): caminhos relativos a esta pasta (tools/blender/previews/)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fxlib as FX  # noqa: E402

# tabela: a do gerador (tools/spec/bullet_strike_vfx.json, WP3/X2)
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
TABLE_PATH = os.path.join(REPO, "tools", "spec", "bullet_strike_vfx.json")
TABLE = json.load(open(TABLE_PATH, encoding="utf-8"))
# 2.0 (WP03): a tabela re-chaveada (he/ap/sap/ac) guarda a da Fase B em historico_1x; as previas leem a vista da Fase B
# (cores std/aphe/emp/nuclear e os projeteis 1.x), como quando as folhas aprovadas foram feitas
if "historico_1x" in TABLE:
    _H = TABLE["historico_1x"]
    TABLE = dict(TABLE, ammo_colors=_H["ammo_colors"], weapons={
        k: (dict(r, **_H["weapons"][k]) if k in _H["weapons"] else r) for k, r in TABLE["weapons"].items()})
# posicoes e larguras das camadas da granada = as do jogo (bsgen/caliber_fx.shell_layout)
sys.path.insert(0, os.path.join(REPO, "tools"))
from bsgen import caliber_fx as CFX  # noqa: E402
COL = TABLE["ammo_colors"]
# largura de desenho dos riscos (tracante e nucleo) em relacao ao Size do jogo. CFX.MOCK_W (2,2) = convencao dos
# mocks aprovados (fxlib.draw_tracer), que desenha os riscos 2,2x mais largos que no jogo. As previas publicadas em
# docs/preview (ladder.py, WP9/make_vfx_antes_depois.py) poem 1.0: larguras iguais as do jogo (a legenda diz
# "escala real"). O resto (comprimentos, brilho, corpo) ja e 1:1 nos dois casos.
DRAW_W = CFX.MOCK_W
AMMO = [("std", "Padrao", "he"), ("ap", "Perfurante", "ap"), ("aphe", "Perf.-Explosiva", "ap"), ("emp", "P.E.M.", "he")]
SHELLS = [("bs_naval_76", "Tambor 76 mm"), ("bs_naval_155", "Trovao 155 mm"), ("bs_naval_406", "Mapinguari 406 mm")]
HULL = (46, 58, 74)


def shell_rgba(d, meta, key, band=None, frame=None):
    """Sprite composto na resolucao nativa: difuso + faixa tingida (lit aproximado) ; luzes a parte (aditivo)."""
    it = meta["items"][key]
    dif = Image.open(os.path.join(d, it["file"])).convert("RGBA")
    if it.get("mask") and band:
        mk = np.asarray(Image.open(os.path.join(d, it["mask"])).convert("RGBA"), dtype=np.float32)
        b = np.asarray(dif, dtype=np.float32)
        lum = b[..., :3].mean(axis=2, keepdims=True) / 255.0
        tint = np.clip(np.array(band, np.float32) * (0.35 + lum * 0.75), 0, 255)
        a = mk[..., 3:4] / 255.0 * (b[..., 3:4] / 255.0)
        b[..., :3] = b[..., :3] * (1 - a) + tint * a
        dif = Image.fromarray(b.astype(np.uint8), "RGBA")
    lt = None
    if it.get("lights") and frame is not None:
        pw, ph = it["px"]
        at = Image.open(os.path.join(d, it["lights"]["file"])).convert("RGBA")
        lt = at.crop((frame * pw, 0, (frame + 1) * pw, ph))
    return it, dif, lt


def draw_shell(cv, d, meta, key, x, y, P, pr, colors, nuke=False, frame=0, spin=0.0, tracer_k=1.0, glow=0.05):
    """Granada com o nariz em (x, y), voando para +x. WP3: as camadas saem de bsgen/caliber_fx.shell_layout (as
    MESMAS posicoes e tamanhos das regras geradas): corpo centrado; tracante, nucleo e clarao da base (head) por
    baixo do corpo (BulletUpper2 < corpo BulletUpper3); faixa e luzes por cima. Larguras de risco do jogo x DRAW_W
    (2,2 = MOCK_W, a convencao dos mocks aprovados; 1 = largura do jogo). Ganhos de desenho do WP7 mantidos."""
    L, W = pr["body"]
    gl, gw = pr["glow"]
    tcol = colors["tracer"] if not nuke else (140, 255, 90)
    cx = x - 0.5 * L * P
    lay = CFX.shell_layout(dict(pr, tracer=[pr["tracer"][0] * tracer_k, pr["tracer"][1]]))
    if glow:
        gx, (gl2, gw2) = lay["glow"]
        cv.add(FX.blob(gl2 * P, gw2 * P, colors["glow"]), cx + gx * P, y, glow)
    if nuke and glow:
        big = pr["spin_big"]
        r = FX.fit(FX.tex("radiation.png"), big["size"] * P, big["size"] * P, rot=spin)
        cv.add(FX.tint(FX.additive_to_rgba(r), (110, 255, 70)), cx, y, 0.12)
    tx, (tl2, tw2) = lay["tracer"]
    cv.add(FX.blob(tl2 * P, max(1.0, tw2 * DRAW_W * P), tcol), cx + tx * P, y, 1.2)
    kx, (kl, kw) = lay["core"]
    cv.add(FX.blob(kl * P, max(1.0, kw * DRAW_W * P), (255, 250, 230) if not nuke else (225, 255, 210)),
           cx + kx * P, y, 1.2)
    if "head" in lay:
        hx, (hd, _) = lay["head"]
        cv.add(FX.blob(hd * P, hd * P, (255, 250, 235)), cx + hx * P, y, 1.5)
    it, dif, lt = shell_rgba(d, meta, key, colors.get("band"), frame if nuke else None)
    pw, ph = max(2, int(round(L * P))), max(2, int(round(W * P)))
    cv.over(dif.resize((pw, ph), Image.LANCZOS), cx, y)
    if lt is not None:
        cv.add(lt.resize((pw, ph), Image.LANCZOS), cx, y, 1.0)
    if nuke:
        sm = pr["spin_small"]
        ax, ay = it["anchors"].get("radiation", [0, 0])
        sx = cx + ax / it["size"][0] * L * P
        tre = FX.fit(FX.tex("radiation_small.png"), sm["size"] * P, sm["size"] * P, rot=spin * 2)
        cv.add(FX.tint(FX.additive_to_rgba(tre), (120, 255, 70)), sx, y, 0.9)


def draw_shell_game(cv, d, meta, key, x, y, P, pr, colors, nuke=False, frame=0, spin=0.0):
    """TODAS as camadas que o jogo desenha numa granada em voo, na mesma ordem e com os mesmos ganhos do mock
    aprovado (fxlib.draw_shell): brilho IsLight (0.14; nuclear 0.2), esteira de fumaca (linhas com smoke_trail:
    406 e Boiuna), puffs do rastro de particulas ao longo de trail_len na cor do tracante, luz grande
    radiation.png da Boiuna (0.35), tracante na base, sprite renderizado (difuso + faixa tingida + atlas de luzes)
    e o radiation_small.png girando. Quem chama deve recortar a fileira (o brilho tem 12-30 quadros)."""
    L, W = pr["body"]
    gl, gw = pr["glow"]
    tcol = colors["tracer"] if not nuke else (140, 255, 90)
    cv.add(FX.blob(gl * P, gw * P, colors["glow"]), x - 0.5 * L * P, y, 0.14 if not nuke else 0.2)
    if pr.get("smoke_trail"):
        st = pr["smoke_trail"]
        FX.draw_smoke_wake(cv, x - 0.5 * L * P, y, P, 14 if not nuke else 11,
                           (st["scale"][0] + st["scale"][1]) / 2 * 0.55, grey=110 if not nuke else 95,
                           tintg=(170, 220, 160) if nuke else None)
    FX.draw_trail_puffs(cv, x - 0.6 * L * P, y, P, pr.get("trail_len", 4), max(0.25, W * 0.8), tcol, n=18, gain=0.6)
    if nuke:
        big = pr["spin_big"]
        r = FX.fit(FX.tex("radiation.png"), big["size"] * P, big["size"] * P, rot=spin)
        cv.add(FX.tint(FX.additive_to_rgba(r), (110, 255, 70)), x - 0.5 * L * P, y, 0.35)
    draw_shell(cv, d, meta, key, x, y, P, pr, colors, nuke=nuke, frame=frame, spin=spin, tracer_k=1.0, glow=0.0)


def draw_tracer(cv, x, y, P, pr, colors, gain=1.0):
    """Igual a fxlib.draw_tracer (mesmas camadas, posicoes e ganhos), mas com a largura dos riscos x DRAW_W em vez
    do 2,2 fixo do fxlib. Com DRAW_W = 2,2 o desenho e identico ao do fxlib."""
    L, W = pr["streak"]
    cl, cw = pr["core"]
    gl, gw = pr["glow"]
    cv.add(FX.blob(gl * P, gw * P, colors["glow"]), x - 0.4 * L * P, y, 0.22 * gain)
    if pr.get("smear"):
        sl, sw = pr["smear"]["wh"]
        cv.add(FX.blob(sl * P, max(2, sw * P * DRAW_W), colors["tracer"]), x - 0.55 * sl * P, y,
               pr["smear"]["alpha"] * gain)
    cv.add(FX.blob(L * P, max(2.0, W * P * DRAW_W), colors["tracer"]), x - 0.4375 * L * P, y, 1.25 * gain)
    cv.add(FX.blob(cl * P, max(1.5, cw * P * DRAW_W), colors["core"]), x - 0.35 * cl * P, y, 1.6 * gain)
    if pr.get("head"):
        h = pr["head"] * P
        cv.add(FX.blob(h * 1.6, h * 1.6, (255, 250, 235)), x, y, 1.5 * gain)


def draw_tracer_game(cv, x, y, P, pr, colors):
    """Tracante com as camadas do mock aprovado (mock_progressao): risco/nucleo/cabeca/borrao/brilho e, nas linhas
    com rastro de particulas (20 mm), os puffs do rastro. Larguras dos riscos x DRAW_W (draw_tracer acima)."""
    draw_tracer(cv, x, y, P, pr, colors)
    if pr.get("trail"):
        FX.draw_trail_puffs(cv, x - 0.5 * P, y, P, 3.0, 0.22, colors["tracer"], gain=0.5)


def panel(d, meta, P, tracer_k, title, glow=0.05):
    rows = []
    for short, name in SHELLS:
        pr = TABLE["weapons"][short]["projectile"]
        rows.append((name, short, pr, False))
    rows.append(("Boiuna (nuclear)", "bs_nuke_howitzer", TABLE["weapons"]["bs_nuke_howitzer"]["projectile"], True))
    lab_w = 150
    cell_w = []
    for _, _, pr, nk in rows:
        L = pr["body"][0]
        cell_w.append(int((L + 0.55 * L + pr["tracer"][0] * tracer_k + 0.6) * P))
    cw = max(cell_w)
    ncol = 4
    heights = [int(max(1.6, pr["body"][1] * 3.2 + 0.4) * P) + 18 for _, _, pr, _ in rows]
    Wt = lab_w + ncol * (cw + 8) + 16
    Ht = 34 + sum(heights) + 8 * len(rows)
    cv = FX.Canvas(Wt, Ht, bg=(9, 11, 17))
    FX.stars(cv, n=Wt * Ht // 2500)
    y0 = 34
    labels = []
    for (name, short, pr, nk), hh in zip(rows, heights):
        # cada fileira num quadro proprio: o brilho e a luz da radiacao (8 quadros) nao vazam para a fileira de
        # baixo (antes a Boiuna esverdeava o 406)
        rc = FX.Canvas(Wt, hh, bg=(9, 11, 17))
        rc.a[:] = cv.a[y0:y0 + hh]
        hpx = hh - 16
        for c in range(ncol):
            x0 = lab_w + c * (cw + 8)
            # casco OPACO na celula inteira (o tracante e o corpo inteiro sobre o casco: contraste honesto)
            FX.hull(rc, x0, 16, cw / P, hpx / P, P, col=HULL, line=(30, 38, 50))
            nose_x = x0 + cw - int(0.5 * P)
            yc = 16 + hpx / 2
            if nk:
                draw_shell(rc, d, meta, "nuke", nose_x, yc, P, pr, COL["nuclear"], nuke=True, frame=c,
                           spin=c * 37.0, tracer_k=tracer_k, glow=glow)
                labels.append((x0, y0, f"quadro de luz {c} (6 qps)"))
            else:
                ammo, an, key = AMMO[c]
                draw_shell(rc, d, meta, key, nose_x, yc, P, pr, COL[ammo], tracer_k=tracer_k, glow=glow)
                labels.append((x0, y0, f"{an} ({key})"))
        cv.a[y0:y0 + hh] = rc.a
        labels.append((8, y0 + 18, name))
        labels.append((8, y0 + 34, f"corpo {pr['body'][0]:g} x {pr['body'][1]:g}"))
        y0 += hh + 8
    im = cv.image()
    FX.label(im, 8, 8, title, sz=15, bold=True)
    for x, y, t in labels:
        FX.label(im, x, y, t, sz=12)
    return im


def main():
    d, outp = sys.argv[1], sys.argv[2]
    meta = json.load(open(os.path.join(d, "meta.json")))
    p1 = panel(d, meta, 64, 1.0, "Granadas no jogo, escala real (64 px por quadro) - nariz para a direita")
    p3 = panel(d, meta, 192, 0.25, "Ampliado 3x (tracante encurtado, sem o brilho grande)", glow=0.0)
    W = max(p1.width, p3.width)
    out = Image.new("RGB", (W, p1.height + p3.height), (9, 11, 17))
    out.paste(p1, (0, 0))
    out.paste(p3, (0, p1.height))
    out.save(outp)
    print(outp, out.size)


if __name__ == "__main__":
    main()
