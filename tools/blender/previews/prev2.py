"""Previas dos projeteis 2.0 (docs/preview/3d/v2/): desenho no jogo com as camadas da Fase B e as luzes 2.0.

Camadas (mesma ordem do jogo): luzes IsLight (2.0 = halo GlowSprite cor glow/4 refl 3 / unlit 0.5 + luz de casco
GlowSprite2 cor palette.hull refl 6 add 0.05; modelo fancy_light do spec de arte: no casco L = refl c D + add c, no
espaco unlit c), rastro de particulas, esteira de fumaca (406/Boiuna), tracante + nucleo + clarao da base nas
posicoes de bsgen/caliber_fx.shell_layout (BulletUpper2, por baixo do corpo), corpo renderizado (alfa), faixa da
mascara tingida com palette.band e o atlas de luzes somado (BulletUpper4).
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

# copia no repositorio (ADDENDUM G13): caminhos relativos a esta pasta (tools/blender/previews/)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import sheet as SH  # noqa: E402  (look da Fase B: o mesmo desenho da granadas_calibre.png)
import game_tex  # noqa: E402  (texturas do jogo pelo nome, nunca commitadas)
FX = SH.FX
CFX = SH.CFX
SH.DRAW_W = 1.0
TABLE = SH.TABLE
OLD_COL = TABLE["ammo_colors"]
# paleta 2.0 (AZUL do Tupa) do spec de arte do repositorio (tools/spec2_split.py); o spec_art.json do design era violeta
SPEC = json.load(open(os.path.join(REPO, "tools", "spec", "bullet_strike_art2.json"), encoding="utf-8"))["art_assets"]
PAL = SPEC["palette"]
OLD_DIR = os.path.join(REPO, "art3d", "bs_shells")
OLD_META = json.load(open(os.path.join(OLD_DIR, "meta.json")))

SPACE = (9, 11, 17)
HULLS = {"escuro": ((46, 58, 74), (30, 38, 50)), "cinza": ((128, 132, 140), (100, 104, 112)),
         "branco": ((214, 217, 222), (178, 182, 190))}
TIER_ROW = {"s": "bs_naval_76", "m": "bs_naval_155", "l": "bs_naval_406", "h": "bs_nuke_howitzer"}
BODY_L = {"s": 0.72, "m": 1.15, "l": 2.05, "h": 2.2, "pem_s": 0.5, "pem_m": 0.75, "pem_l": 1.15, "slug": 3.0}
AMMO_PT = {"he": "Alto-Explosivo (HE)", "ap": "Perfurante (AP)", "sap": "Semiperfurante (SAP)",
           "ac": "Alta Capacidade (AC)"}
BLOB = None


def blob_f(w, h):
    """Falloff 0..1 do blob.png do jogo no tamanho w x h px."""
    global BLOB
    if BLOB is None:
        BLOB = Image.open(game_tex.find("blob.png")).convert("RGBA")
    im = BLOB.resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32)[..., 3] / 255.0


def c01(c):
    return np.array(c, np.float32) / 255.0


# ============================================================================ cena com o modelo de luz
class Scene:
    def __init__(self, w, h, bg=SPACE, stars=True):
        self.w, self.h = w, h
        self.alb = np.zeros((h, w, 3), np.float32)
        self.alb[:] = bg
        if stars:
            rng = np.random.default_rng(3)
            for _ in range(w * h // 2500):
                x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
                self.alb[y, x] = np.maximum(self.alb[y, x], float(rng.uniform(40, 120)))
        self.hull = np.zeros((h, w), np.float32)
        self.lit = np.zeros((h, w, 3), np.float32)
        self.ladd = np.zeros((h, w, 3), np.float32)
        self.uadd = np.zeros((h, w, 3), np.float32)
        self.fx = FX.Canvas(w, h, bg=(0, 0, 0))
        self.mid = []          # (fn, args) alfa por cima do fundo (fumaca), antes dos aditivos
        self.top = []          # (fn, args) desenhados depois da composicao (corpo, faixa, luzes)
        self.out = None

    def plate(self, x0, y0, wt, ht, P, col, line):
        x0, y0 = int(x0), int(y0)
        w, h = int(round(wt * P)), int(round(ht * P))
        x1, y1 = min(self.w, x0 + w), min(self.h, y0 + h)
        self.alb[y0:y1, x0:x1] = col
        for i in range(int(wt) + 1):
            x = x0 + int(i * P)
            self.alb[y0:y1, max(0, x - 1):min(self.w, x + 1)] = line
        for j in range(int(ht) + 1):
            y = y0 + int(j * P)
            self.alb[max(0, y - 1):min(self.h, y + 1), x0:x1] = line
        self.hull[y0:y1, x0:x1] = 1.0

    def _acc(self, arr, f, cx, cy, val):
        h, w = f.shape
        x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
        X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(self.w, x0 + w), min(self.h, y0 + h)
        if X1 <= X0 or Y1 <= Y0:
            return
        arr[Y0:Y1, X0:X1] += f[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None] * val

    def light(self, cx, cy, wpx, hpx, col, refl, add, unlit):
        f = blob_f(wpx, hpx)
        c = c01(col)
        self._acc(self.lit, f, cx, cy, refl * c)
        self._acc(self.ladd, f, cx, cy, add * c * 255)
        self._acc(self.uadd, f, cx, cy, unlit * c * 255)

    def compose(self):
        hm = self.hull[..., None]
        base = self.alb * (1 + self.lit * hm) + self.ladd * hm + self.uadd * (1 - hm)
        self.out = FX.Canvas(self.w, self.h)
        self.out.a = base
        for fn, args in self.mid:
            fn(self.out, *args)
        self.out.a = self.out.a + self.fx.a
        for fn, args in self.top:
            fn(self.out, *args)
        return self.out


# ============================================================================ sprites
def new_body(meta, key):
    it = meta["items"][key]
    L = BODY_L[key] if key in BODY_L else BODY_L[key.split("_")[1]]
    cl, cw = it["size"]
    return L, L * cw / cl


def sprite_rgba(d, meta, key, band=None, frame=0):
    """Difuso com a faixa tingida (mascara lit, como sheet.shell_rgba) + quadro do atlas de luzes."""
    it = meta["items"][key]
    dif = np.asarray(Image.open(os.path.join(d, it["file"])).convert("RGBA"), dtype=np.float32)
    if it.get("mask") and band:
        mk = np.asarray(Image.open(os.path.join(d, it["mask"])).convert("RGBA"), dtype=np.float32)
        lum = dif[..., :3].mean(axis=2, keepdims=True) / 255.0
        tint = np.clip(np.array(band, np.float32) * (0.35 + lum * 0.75), 0, 255)
        a = mk[..., 3:4] / 255.0 * (dif[..., 3:4] / 255.0)
        dif[..., :3] = dif[..., :3] * (1 - a) + tint * a
    lt = None
    if it.get("lights"):
        pw, ph = it["px"]
        n = it["lights"]["frames"]
        at = Image.open(os.path.join(d, it["lights"]["file"])).convert("RGBA")
        f = frame % n
        lt = at.crop((f * pw, 0, (f + 1) * pw, ph))
    return Image.fromarray(dif.astype(np.uint8), "RGBA"), lt


def _resize(im, w, h):
    return im.convert("RGBa").resize((max(2, int(round(w))), max(2, int(round(h)))), Image.LANCZOS).convert("RGBA")


def _draw_sprite(cv, dif, lt, cx, cy, w, h):
    cv.over(_resize(dif, w, h), cx, cy)
    if lt is not None:
        cv.add(_resize(lt, w, h), cx, cy, 1.0)


def proj_info(key):
    """Tamanhos e cores do tiro no jogo (2.0) por chave."""
    if key.startswith("pem_"):
        p = PAL["pem"]
        L = BODY_L[key]
        halo = {"pem_s": [2.5, 1.25], "pem_m": [3.0, 1.5], "pem_l": [4.0, 2.0]}[key]
        return {"kind": "pem", "L": L, "halo": halo, "glow": p["glow"], "hull": p["hull"],
                "tracer": p["band"], "core": p["core"], "band": None,
                "hull_size": [1.2 * L, 0.6], "trail": {"pem_s": 2.0, "pem_m": 3.0, "pem_l": 4.5}[key]}
    if key == "slug":
        p = PAL["rail"]
        # paleta azul (ADDENDUM G13): as chaves 'violet'/'gold' nao existem mais
        return {"kind": "slug", "L": 3.0, "halo": [6, 3], "glow": p["glow"], "hull": p["hull"], "tracer": p["glow"],
                "core": p["core"], "gold": p["core"], "band": None, "hull_size": [3.6, 1.2]}
    ammo, tier = key.split("_")
    pr = TABLE["weapons"][TIER_ROW[tier]]["projectile"]
    p = PAL[ammo]
    return {"kind": "shell", "tier": tier, "ammo": ammo, "pr": pr, "L": BODY_L[tier], "halo": pr["glow"],
            "glow": p["glow"], "hull": p["hull"], "tracer": p["tracer"], "core": p["core"], "band": p["band"]}


def ring_img(wpx, hpx, rgb, lw=2.0):
    """Anel fino (contorno de elipse) RGBA, como bs_ring_thin.png tingido (achatado no eixo do voo)."""
    from PIL import ImageFilter
    W_, H_ = max(4, int(round(wpx)) + 6), max(4, int(round(hpx)) + 6)
    im = Image.new("L", (W_ * 4, H_ * 4), 0)
    ImageDraw.Draw(im).ellipse((12, 12, W_ * 4 - 12, H_ * 4 - 12), outline=255, width=max(2, int(lw * 4)))
    a = im.resize((W_, H_), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    out = Image.new("RGBA", (W_, H_), (*[int(v) for v in rgb], 0))
    out.putalpha(a)
    return out


def slug_fx(sc, cx, y, P, info, fx=1.0, zoom=False):
    """Voo do slug como o spec 2.0 (effects.railgun.in_flight): risco bs_rail_streak 4.2 x 1.6 no offset -0.6
    (nucleo branco-azulado FINO com franja azul: palette.rail core/glow), particulas branco-azuladas no mundo (~12
    vivas; info['gold'] = palette.rail core) e aneis azuis finos achatados que crescem para tras (~4 vivos). Sem
    'pluma': nada largo e branco colado na cauda."""
    xt = cx - 1.5 * P                                   # cauda do slug (corpo 3.0)
    g = 0.5 if zoom else 1.0
    sc.fx.add(FX.blob(4.2 * P, 0.42 * P, info["tracer"]), cx - 0.6 * P, y, 0.30 * g * fx)
    sc.fx.add(FX.blob(4.0 * P, max(1.0, 0.055 * P), info["gold"]), cx - 0.6 * P, y, 1.1 * fx)
    sc.fx.add(FX.blob(3.6 * P, max(1.0, 0.022 * P), info["core"]), cx - 0.6 * P, y, 0.8 * fx)
    rng = np.random.default_rng(7)
    for i in range(12):
        d = 0.35 + i * 0.40
        sc.fx.add(FX.blob(0.10 * P, 0.10 * P, info["gold"]), xt - d * P, y + rng.uniform(-0.05, 0.05) * P,
                  (0.95 - 0.06 * i) * g * fx)
    for j, (d, s_) in enumerate(((0.45, 0.45), (1.35, 0.85), (2.4, 1.25), (3.6, 1.6))):
        age = j / 4.0
        sc.fx.add(ring_img(0.35 * s_ * P, s_ * P, info["tracer"], lw=max(1.2, 0.03 * P)), xt - d * P, y,
                  (1.0 - age) * 0.85 * g * fx)


def draw_new(sc, d, meta, key, nose_x, y, P, frame=0, fx=1.0, lights=True, tracer_k=1.0, trail=True, head=True,
             halo_hull=True, zoom=False, head_k=1.0, head_dx=0.0, thin=None):
    """Um tiro 2.0 com o nariz em (nose_x, y) voando para +x. fx = 0 desenha so o sprite.
    zoom=True (ampliados): so o RISCO longo e fino do tracante do jogo (comprimento e largura reais, cortado pela
    borda do quadro), sem o nucleo branco e sem o clarao da base (nada de 'pluma' colada na granada).
    head_k / head_dx: proposta de clarao da base menor (diametro x head_k) e recuado (head_dx x diametro antigo).
    thin: proposta de tracante FINO para a Boiuna (o layout do bs_nuke_howitzer, sem clarao na cabeca, poe o nucleo
    branco-quente colado na base e o tracante largo vira 'chama de foguete'): dict {"tw": largura do tracante x,
    "tl": comprimento (quadros), "kw": largura do nucleo x, "kl": comprimento do nucleo, "kback": folga entre a base e
    a frente do nucleo (quadros), "puff": largura do rastro x, "gain": intensidade x}."""
    info = proj_info(key)
    L, W = new_body(meta, key)
    cx = nose_x - 0.5 * L * P
    if fx and lights:
        # 2.0: halo (glow/4, refl 3, unlit 0.5) + luz de casco (palette.hull, refl 6, add 0.05)
        g4 = [v / 4 for v in info["glow"]]
        sc.light(cx, y, info["halo"][0] * P, info["halo"][1] * P, g4, 3.0 if halo_hull else 0.0, 0.0, 0.5)
        hs = info.get("hull_size") or [1.2 * L, max(1.2 * W, 0.5)]
        sc.light(cx, y, hs[0] * P, hs[1] * P, info["hull"], 6.0, 0.05, 0.0)
    if fx:
        k = info["kind"]
        if k == "shell":
            pr = dict(info["pr"])
            pr["body"] = [L, W]
            if pr.get("smoke_trail") and trail:
                st = pr["smoke_trail"]
                sc.mid.append((FX.draw_smoke_wake, (cx - 0.5 * L * P, y, P, 14 if info["tier"] != "h" else 11,
                                                    (st["scale"][0] + st["scale"][1]) / 2 * 0.55)))
            th = thin or {}
            if trail:
                FX.draw_trail_puffs(sc.fx, cx - 0.6 * L * P, y, P, pr.get("trail_len", 4),
                                    max(0.25, W * 0.8) * th.get("puff", 1.0), info["tracer"], n=18,
                                    gain=0.6 * th.get("gain", 1.0))
            lay = CFX.shell_layout(dict(pr, tracer=[pr["tracer"][0] * tracer_k, pr["tracer"][1]]))
            tx, (tl, tw) = lay["tracer"]
            kx, (kl, kw) = lay["core"]
            if thin:
                # tracante fino comecando na base e nucleo curto recuado (frente a kback quadros da base)
                tl, tw = th.get("tl", tl), tw * th.get("tw", 1.0)
                tx = -0.5 * L - 0.5 * tl
                kl, kw = th.get("kl", kl), kw * th.get("kw", 1.0)
                kx = -0.5 * L - th.get("kback", 0.3) - 0.5 * kl
            g = th.get("gain", 1.0)
            if zoom:
                sc.fx.add(FX.blob(tl * P, max(1.0, tw * P), info["tracer"]), cx + tx * P, y, 0.9 * fx)
            else:
                sc.fx.add(FX.blob(tl * P, max(1.0, tw * P), info["tracer"]), cx + tx * P, y, 1.2 * g * fx)
                sc.fx.add(FX.blob(kl * P, max(1.0, kw * P), info["core"]), cx + kx * P, y, 1.2 * g * fx)
                if "head" in lay and head:
                    hx, (hd, _) = lay["head"]
                    hx = hx - head_dx * hd
                    sc.fx.add(FX.blob(hd * head_k * P, hd * head_k * P, (255, 250, 235)), cx + hx * P, y, 1.5 * fx)
        elif k == "pem":
            # bainha ciano aditiva em volta do corpo + rastro fino com nucleo branco-quente (bs_pem_sheath/trail)
            sc.fx.add(FX.blob(1.6 * L * P, 2.6 * W * P, info["tracer"]), cx, y, (0.2 if zoom else 0.55) * fx)
            tl = info["trail"] * (1.0 if zoom else tracer_k)
            sc.fx.add(FX.blob(tl * P, max(1.0, 0.35 * W * P), info["tracer"]), cx - (0.5 * L + 0.42 * tl) * P, y,
                      (0.8 if zoom else 1.1) * fx)
            if not zoom:
                sc.fx.add(FX.blob(0.45 * tl * P, max(1.0, 0.16 * W * P), info["core"]),
                          cx - (0.5 * L + 0.15 * tl) * P, y, 1.2 * fx)
        else:
            slug_fx(sc, cx, y, P, info, fx, zoom)
    dif, lt = sprite_rgba(d, meta, key, info["band"], frame)
    sc.top.append((_draw_sprite, (dif, lt, cx, y, L * P, W * P)))
    return L, W


def draw_old(sc, key, nose_x, y, P, frame=2, fx=1.0, spin=85.0, tracer_k=1.0):
    """Tiro da 1.x (arte art3d/bs_shells + camadas da Fase B, igual a granadas_calibre.png)."""
    tier = key
    short = TIER_ROW[tier]
    pr = TABLE["weapons"][short]["projectile"]
    nuke = pr["look"] == "nuke_shell"
    col = OLD_COL["nuclear" if nuke else "std"]
    if fx:
        tmp = FX.Canvas(sc.w, sc.h, bg=(0, 0, 0))
        # o draw_shell_game desenha camadas aditivas + o corpo; aqui so os aditivos vao para fx, o corpo por cima
        L, W = pr["body"]
        tcol = col["tracer"] if not nuke else (140, 255, 90)
        tmp.add(FX.blob(pr["glow"][0] * P, pr["glow"][1] * P, col["glow"]), nose_x - 0.5 * L * P, y,
                0.14 if not nuke else 0.2)
        FX.draw_trail_puffs(tmp, nose_x - 0.6 * L * P, y, P, pr.get("trail_len", 4), max(0.25, W * 0.8), tcol, n=18,
                            gain=0.6)
        if nuke:
            big = pr["spin_big"]
            r = FX.fit(FX.tex("radiation.png"), big["size"] * P, big["size"] * P, rot=spin)
            tmp.add(FX.tint(FX.additive_to_rgba(r), (110, 255, 70)), nose_x - 0.5 * L * P, y, 0.35)
        cx = nose_x - 0.5 * L * P
        if pr.get("smoke_trail"):
            st = pr["smoke_trail"]
            sc.mid.append((lambda cv, a=(nose_x - 0.5 * L * P, y, P, 14 if not nuke else 11,
                                         (st["scale"][0] + st["scale"][1]) / 2 * 0.55):
                           FX.draw_smoke_wake(cv, *a, grey=110 if not nuke else 95,
                                              tintg=(170, 220, 160) if nuke else None), ()))
        lay = CFX.shell_layout(dict(pr, tracer=[pr["tracer"][0] * tracer_k, pr["tracer"][1]]))
        tx, (tl, tw) = lay["tracer"]
        tmp.add(FX.blob(tl * P, max(1.0, tw * P), tcol), cx + tx * P, y, 1.2)
        kx, (kl, kw) = lay["core"]
        tmp.add(FX.blob(kl * P, max(1.0, kw * P), (255, 250, 230) if not nuke else (225, 255, 210)), cx + kx * P,
                y, 1.2)
        if "head" in lay:
            hx, (hd, _) = lay["head"]
            tmp.add(FX.blob(hd * P, hd * P, (255, 250, 235)), cx + hx * P, y, 1.5)
        sc.fx.a += tmp.a * fx
    L, W = pr["body"]
    it, dif, lt = SH.shell_rgba(OLD_DIR, OLD_META, "nuke" if nuke else "he", col.get("band"), frame if nuke else None)
    cx = nose_x - 0.5 * L * P

    def _old(cv, dif=dif, lt=lt):
        _draw_sprite(cv, dif, lt, cx, y, L * P, W * P)
        if nuke:
            sm = pr["spin_small"]
            ax = it["anchors"].get("radiation", [0, 0])[0]
            sx = cx + ax / it["size"][0] * L * P
            tre = FX.fit(FX.tex("radiation_small.png"), sm["size"] * P, sm["size"] * P, rot=spin * 2)
            cv.add(FX.tint(FX.additive_to_rgba(tre), (120, 255, 70)), sx, y, 0.9)
    sc.top.append((lambda cv: _old(cv), ()))
    return L, W


def label(im, x, y, text, sz=13, col=(220, 225, 235), bold=False):
    ImageDraw.Draw(im).text((x, y), text, fill=col, font=FX.font(sz, bold))
