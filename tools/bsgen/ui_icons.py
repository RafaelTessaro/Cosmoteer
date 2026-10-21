"""Icones da interface no padrao visual do jogo (gui/game/parts/missile_type_*.png, gui/game/designer/group_*.png):
silhueta solida azul (0,183,255) com brilho suave em volta, 96 x 96, sem detalhes internos alem de vaos finos.

Cada icone e desenhado em coordenadas de 0 a 96 com superamostragem e depois reduzido. Uma segunda mascara
(destaque) recebe a cor do tipo (raio do EMP, chama do napalm, trevo nuclear, explosao do APHE).
"""

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = 96
SS = 8
FIT = 0.78  # escala global em volta do centro: as silhuetas do jogo ocupam ~60 de 96 px e o brilho precisa de margem
BLUE = (0, 183, 255)
BLUE_GLOW = (0, 148, 255)
ACC = {
    "fire": (255, 146, 40),
    "spark": (205, 236, 255),
    "nuke": (10, 212, 98),
}


class Pen:
    """Desenha poligonos em duas mascaras (corpo e destaque) com transformacao (translacao, rotacao, escala)."""

    def __init__(self):
        n = SIZE * SS
        self.m = {"body": Image.new("L", (n, n), 0), "acc": Image.new("L", (n, n), 0)}
        self.d = {k: ImageDraw.Draw(v) for k, v in self.m.items()}
        self.t = (0.0, 0.0, 0.0, 1.0)  # dx, dy, angulo (graus, horario), escala

    def at(self, dx=0.0, dy=0.0, ang=0.0, s=1.0):
        self.t = (dx, dy, ang, s)
        return self

    def _xf(self, pts):
        dx, dy, ang, s = self.t
        c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        h = SIZE / 2
        return [((h + ((x * c - y * sn) * s + dx - h) * FIT) * SS, (h + ((x * sn + y * c) * s + dy - h) * FIT) * SS)
                for x, y in pts]

    def poly(self, pts, layer="body", fill=255):
        self.d[layer].polygon(self._xf(pts), fill=fill)

    def circle(self, x, y, r, layer="body", fill=255, n=40):
        self.poly([(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)],
                  layer, fill)

    def rect(self, x0, y0, x1, y1, layer="body", fill=255):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer, fill)

    def gap(self, x0, y0, x1, y1):
        """Vao fino transparente (corta corpo e destaque)."""
        for k in self.m:
            self.rect(x0, y0, x1, y1, k, 0)

    def render(self, acc_color=None):
        out = np.zeros((SIZE, SIZE, 4), np.float32)
        layers = [("body", BLUE, BLUE_GLOW)]
        if acc_color:
            glow = tuple(int(c * 0.82) for c in acc_color)
            layers.append(("acc", acc_color, glow))
        for k, col, gcol in layers:
            a = np.asarray(self.m[k].resize((SIZE, SIZE), Image.LANCZOS), np.float32) / 255.0
            a = np.clip(a, 0, 1)
            im = Image.fromarray((a * 255).astype(np.uint8))
            g = (np.asarray(im.filter(ImageFilter.GaussianBlur(2.6)), np.float32) / 255.0 * 0.62 +
                 np.asarray(im.filter(ImageFilter.GaussianBlur(6.5)), np.float32) / 255.0 * 0.42)
            g = np.clip(g, 0, 0.62)
            lay = np.zeros_like(out)
            al = a + g * (1 - a)
            for i in range(3):
                lay[..., i] = np.where(al > 0, (a * col[i] + g * (1 - a) * gcol[i]) / np.maximum(al, 1e-6), 0)
            lay[..., 3] = al
            # composicao "por cima"
            oa = out[..., 3]
            na = lay[..., 3] + oa * (1 - lay[..., 3])
            for i in range(3):
                out[..., i] = np.where(na > 0, (lay[..., i] * lay[..., 3] + out[..., i] * oa * (1 - lay[..., 3])) /
                                       np.maximum(na, 1e-6), 0)
            out[..., 3] = na
        out[..., 3] *= 255
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


# ---------------------------------------------------------------------------------------------- formas basicas
def ogive(cx, y_tip, y_base, w, n=10, sharp=1.0):
    """Lado esquerdo -> direito de uma ogiva (ponta em y_tip, base de largura w em y_base)."""
    L = y_base - y_tip
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        r = (w / 2) * (1 - (1 - t) ** (1.0 + sharp)) ** 0.5 if t > 0 else 0.0
        y = y_tip + L * t
        left.append((cx - r, y))
        right.append((cx + r, y))
    return left, right


def shell(p, cx, top, bottom, w, tip=0.38, sharp=1.0, layer="body"):
    """Cartucho de canhao: ogiva + estojo, com vao na juncao e no sulco do aro."""
    L = bottom - top
    yb = top + L * tip
    left, right = ogive(cx, top, yb, w, sharp=sharp)
    p.poly(left + [(cx - w / 2, bottom - 4), (cx + w / 2, bottom - 4)] + right[::-1], layer)
    p.rect(cx - w / 2 - 1.5, bottom - 4, cx + w / 2 + 1.5, bottom, layer)
    p.gap(cx - w / 2 - 2, yb + 1.0, cx + w / 2 + 2, yb + 3.4)
    p.gap(cx - w / 2 - 2, bottom - 6.6, cx + w / 2 + 2, bottom - 5.0)


def missile(p, cx, top, bottom, w, fin=1.0, layer="body", nose=0.30):
    """Missil de pe (ponta para cima): ogiva, corpo, aletas na cauda e bocal."""
    L = bottom - top
    yb = top + L * nose
    left, right = ogive(cx, top, yb, w, sharp=0.8)
    tail = bottom - L * 0.08
    p.poly(left + [(cx - w / 2, tail), (cx + w / 2, tail)] + right[::-1], layer)
    fw = w * 0.55 * fin
    fy0 = bottom - L * 0.30
    for s in (-1, 1):
        p.poly([(cx + s * w / 2, fy0), (cx + s * (w / 2 + fw), fy0 + L * 0.16), (cx + s * (w / 2 + fw), tail),
                (cx + s * w / 2, tail)], layer)
    p.poly([(cx - w * 0.32, tail), (cx + w * 0.32, tail), (cx + w * 0.42, bottom), (cx - w * 0.42, bottom)], layer)
    p.gap(cx - w / 2 - fw - 1, tail - 0.4, cx + w / 2 + fw + 1, tail + 1.4)


def bolt(p, x, y, s, layer="acc"):
    """Raio (zigue-zague) com o canto de cima em (x, y)."""
    pts = [(10, 0), (24, 0), (16, 15), (25, 15), (6, 40), (11, 22), (2, 22)]
    p.poly([(x + px * s, y + py * s) for px, py in pts], layer)


def star(p, x, y, r0, r1, n=8, rot=0.0, layer="acc"):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r0
        a = math.radians(rot) + math.pi * i / n
        pts.append((x + r * math.sin(a), y - r * math.cos(a)))
    p.poly(pts, layer)


def flame(p, x, y, s, layer="acc"):
    """Chama de tres linguas com a base centrada em (x, y): uma gota alta no meio e duas menores inclinadas."""
    def tongue(cx, cy, h, w, lean):
        pts = []
        for i in range(25):
            t = i / 24
            yy = cy - h * t
            r = w * (math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7) * (1 - t) ** 0.35
            off = lean * h * t * t
            pts.append((cx + off - r, yy))
        right = []
        for i in range(25):
            t = i / 24
            yy = cy - h * t
            r = w * (math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7) * (1 - t) ** 0.35
            off = lean * h * t * t
            right.append((cx + off + r, yy))
        p.poly(pts + right[::-1], layer)
    tongue(x, y, 30 * s, 8.5 * s, 0.10)
    tongue(x - 6 * s, y - 1 * s, 19 * s, 5.5 * s, -0.35)
    tongue(x + 6 * s, y - 1 * s, 21 * s, 5.5 * s, 0.38)
    p.circle(x, y - 6 * s, 8.5 * s, layer)


def trefoil(p, x, y, r, layer="acc"):
    """Trevo de tres pas (simbolo nuclear simplificado, sem o amarelo e preto)."""
    for k in range(3):
        a0 = math.radians(-90 + k * 120 - 30)
        a1 = math.radians(-90 + k * 120 + 30)
        pts = [(x + r * 0.32 * math.cos(a0), y + r * 0.32 * math.sin(a0))]
        for i in range(13):
            a = a0 + (a1 - a0) * i / 12
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
        pts.append((x + r * 0.32 * math.cos(a1), y + r * 0.32 * math.sin(a1)))
        p.poly(pts, layer)
    p.circle(x, y, r * 0.2, layer)


# ---------------------------------------------------------------------------------------------- icones
def icon_ammo(kind):
    p = Pen()
    if kind == "std":
        shell(p, 48, 12, 84, 24)
        return p.render()
    if kind in ("ap", "aphe"):
        cx = 48 if kind == "ap" else 42
        # penetrador: dardo comprido e fino saindo do estojo, com colar de sabot
        p.poly([(cx, 10), (cx + 5, 30), (cx + 5, 50), (cx - 5, 50), (cx - 5, 30)])
        p.poly([(cx - 10, 47), (cx + 10, 47), (cx + 12, 53), (cx - 12, 53)])
        p.rect(cx - 12, 53, cx + 12, 80)
        p.rect(cx - 13.5, 80, cx + 13.5, 85)
        p.gap(cx - 14, 53, cx + 14, 55.2)
        p.gap(cx - 14, 77.6, cx + 14, 79.2)
        if kind == "aphe":
            star(p, 66, 22, 5.5, 13, n=7, rot=10)
            return p.render(ACC["fire"])
        return p.render()
    if kind == "emp":
        shell(p, 38, 14, 84, 22)
        bolt(p, 52, 16, 1.05)
        return p.render(ACC["spark"])
    raise ValueError(kind)


def icon_missile(kind):
    p = Pen()
    if kind == "he":
        missile(p, 48, 8, 88, 20)
        return p.render()
    if kind == "cluster":
        # portador embaixo com a ogiva aberta em petalas e um leque de micro-misseis (dardos) saindo dele
        missile(p, 48, 58, 92, 18, fin=0.8, nose=0.05)
        for sd in (-1, 1):
            p.poly([(48 + sd * 9, 60), (48 + sd * 4, 60), (48 + sd * 13, 51), (48 + sd * 16.5, 54)])
        for ang, r in ((-50, 26), (-17, 30), (17, 30), (50, 26), (-34, 46), (0, 48), (34, 46)):
            p.at(48 + r * math.sin(math.radians(ang)), 56 - r * math.cos(math.radians(ang)), ang)
            p.poly([(0, -9), (4.2, 5), (0, 2.2), (-4.2, 5)])
            p.at()
        return p.render()
    if kind == "limpet":
        # missil cravado em diagonal numa chapa de casco (ponta atravessando e duas garras mordendo) e o relogio
        # da espoleta retardada: gruda e explode depois
        p.at(46, 50, 38)
        p.rect(-26, -40, 26, -32)
        p.gap(-8.9, -40, -7.3, -32)
        p.gap(7.3, -40, 8.9, -32)
        missile(p, 0, -22, 36, 18, nose=0.10)
        p.rect(-2.3, -44, 2.3, -20)
        for sd in (-1, 1):
            p.poly([(sd * 5, -17), (sd * 13, -22), (sd * 15, -31.5), (sd * 11, -31.5), (sd * 10, -26), (sd * 3, -23)])
        p.gap(-12, -31.6, 12, -30.0)
        p.at()
        p.circle(72, 72, 13, "acc")
        p.circle(72, 72, 9.6, "acc", 0)
        p.rect(70.6, 63.5, 73.4, 73.2, "acc")
        p.poly([(71, 70.6), (79, 74.2), (78, 76.4), (70.2, 73.2)], "acc")
        return p.render(ACC["fire"])
    if kind == "napalm":
        missile(p, 40, 12, 88, 18)
        flame(p, 66, 50, 1.25)
        return p.render(ACC["fire"])
    if kind == "emp":
        missile(p, 40, 10, 88, 18)
        bolt(p, 54, 22, 1.05)
        return p.render(ACC["spark"])
    if kind == "torpedo":
        # torpedo: corpo grosso e comprido, nariz arredondado e anel de cauda (difusor)
        w = 22
        left, right = ogive(48, 8, 22, w, sharp=0.2)
        p.poly(left + [(48 - w / 2, 76), (48 + w / 2, 76)] + right[::-1])
        p.rect(48 - w / 2 - 5, 74, 48 + w / 2 + 5, 86)
        p.gap(48 - w / 2 - 0.5, 78, 48 + w / 2 + 0.5, 82)
        p.rect(44, 76, 52, 90)
        for y in (34, 54):
            p.gap(30, y, 66, y + 1.8)
        return p.render()
    if kind == "nuclear":
        # ogiva gorda (como o missil nuclear do jogo) e o trevo verde
        w = 26
        left, right = ogive(40, 10, 40, w, sharp=0.15)
        p.poly(left + [(40 - w / 2, 80), (40 + w / 2, 80)] + right[::-1])
        for s in (-1, 1):
            p.poly([(40 + s * w / 2, 62), (40 + s * (w / 2 + 7), 74), (40 + s * (w / 2 + 7), 86), (40 + s * w / 2, 82)])
        p.poly([(40 - 8, 80), (40 + 8, 80), (40 + 10, 88), (40 - 10, 88)])
        p.gap(26, 44, 54, 46.2)
        trefoil(p, 72, 26, 13)
        return p.render(ACC["nuke"])
    raise ValueError(kind)


def icon_group():
    """Grupo do editor: projetil inclinado com rastros de velocidade (Bullet Strike)."""
    p = Pen()
    p.at(56, 40, 45)
    shell(p, 0, -30, 30, 22)
    p.at()
    for i, (x, y, L) in enumerate(((16, 58, 18), (26, 70, 22), (38, 80, 16))):
        p.at(x, y, 45)
        p.rect(-2.2, -L / 2, 2.2, L / 2)
        p.at()
    return p.render()


# ============================================================================================== 2.0 (aditivo)
# Icones 2.0 (SPEC 2.0 art_assets.assets.ui_icons; USER_NOTES 2026-10-21 "icones de UI no mesmo estilo" futurista das
# municoes 2.0). Tudo daqui para baixo e NOVO: nada acima muda (os icones da 1.x continuam saindo iguais, bit a bit).
# Mesmo Pen (silhueta azul 96 x 96 com brilho + UMA mascara de destaque); a linguagem 2.0 entra pela silhueta: luvas
# partidas por frestas finas (retas ou em divisa), anel do sensor, espoleta de ponta chata, canards/aletas, capsulas
# com janela, aneis de armadura. Saida: art3d/bs_ui_icons2/ (python3 tools/bsgen/ui_icons.py [pasta]).
ACC.update({
    "gold": (255, 200, 80),
    "teal": (120, 230, 210),
    "cyan": (60, 225, 255),
    "violet": (170, 130, 255),
    # projetil da Tupa: a railgun virou AZUL (USER_NOTES: referencia do usuario); sobre a silhueta azul da interface os
    # aneis de armadura saem em azul-gelo eletrico (o violeta do spec ficou para tras com a Tupa antiga)
    "rail": (185, 225, 255),
})


def ogive_flat(cx, y_tip, y_base, w, r_tip, n=12, sharp=1.0):
    """Ogiva (lado esquerdo, lado direito) que termina CHATA no topo (raio r_tip em y_tip): espoleta/capuz 2.0."""
    L = y_base - y_tip
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        r = r_tip + (w / 2 - r_tip) * (1 - (1 - t) ** (1.0 + sharp)) ** 0.5
        y = y_tip + L * t
        left.append((cx - r, y))
        right.append((cx + r, y))
    return left, right


def sleeve_gaps(p, cx, y0, y1, n, w=30.0, th=2.4, chevron=0.0):
    """n frestas transparentes finas entre y0 e y1 (le como luvas de blindagem partidas). chevron > 0: fresta em
    DIVISA apontando para o nariz (para cima), a ponta chevron px acima das bordas (as 'escamas' da Jararaca)."""
    for i in range(n):
        y = y0 + (y1 - y0) * (i + 1) / (n + 1)
        h = w / 2 + 3
        if chevron:
            pts = [(cx - h, y + chevron), (cx, y), (cx + h, y + chevron), (cx + h, y + chevron + th), (cx, y + th),
                   (cx - h, y + chevron + th)]
            for k in p.m:
                p.poly(pts, k, 0)
        else:
            p.gap(cx - h, y, cx + h, y + th)


def fins(p, cx, y, w, h=18.0, span=9.0, layer="body"):
    """2 aletas de cauda em flecha presas nas bordas do corpo (largura w), da raiz em y ate y + h."""
    for s in (-1, 1):
        p.poly([(cx + s * w / 2, y), (cx + s * (w / 2 + span), y + h * 0.62), (cx + s * (w / 2 + span), y + h),
                (cx + s * w / 2, y + h * 0.82)], layer)


def canards(p, cx, y, w, span=6.0, h=8.0, layer="body"):
    """2 canards pequenos (triangulos para tras) nas bordas do corpo em y."""
    for s in (-1, 1):
        p.poly([(cx + s * w / 2, y), (cx + s * (w / 2 + span), y + h), (cx + s * (w / 2 + span), y + h + 2.2),
                (cx + s * w / 2, y + h * 0.75 + 2.2)], layer)


def capsule(p, cx, top, bottom, w, layer="body", cap=0.42):
    """Celula: capsula de pontas chanfradas (octogono alongado; 'cap' = chanfro em fracao da largura)."""
    c = w * cap
    h = w / 2
    p.poly([(cx - h + c, top), (cx + h - c, top), (cx + h, top + c), (cx + h, bottom - c), (cx + h - c, bottom),
            (cx - h + c, bottom), (cx - h, bottom - c), (cx - h, top + c)], layer)


def rod_armature(p, cx, top, bottom, w, rings, ring_w=None, ring_h=5.0, layer="body", ring_layer="acc"):
    """Haste fina com ponta de penetrador (topo) e 'rings' aneis de armadura mais largos (em ring_layer)."""
    rw = ring_w or w * 2.6
    tip = w * 2.2
    p.poly([(cx, top), (cx + w / 2, top + tip), (cx + w / 2, bottom), (cx - w / 2, bottom), (cx - w / 2, top + tip)],
           layer)
    y0, y1 = top + tip + 10, bottom - 22
    for i in range(rings):
        y = y0 + (y1 - y0) * i / max(1, rings - 1)
        p.poly([(cx - rw / 2 + 1.5, y), (cx + rw / 2 - 1.5, y), (cx + rw / 2, y + 1.5), (cx + rw / 2, y + ring_h - 1.5),
                (cx + rw / 2 - 1.5, y + ring_h), (cx - rw / 2 + 1.5, y + ring_h), (cx - rw / 2, y + ring_h - 1.5),
                (cx - rw / 2, y + 1.5)], ring_layer)


def fragment_fan(p, cx, cy, n, spread, r0=13.0, r1=30.0, th=2.6, layer="acc"):
    """Leque de n tracos para a frente (para cima) a partir de (cx, cy), abertura total 'spread' graus; tracos
    alternados mais curtos (a nuvem de fragmentos)."""
    for i in range(n):
        ang = -spread / 2 + spread * i / max(1, n - 1)
        a = math.radians(ang)
        rr1 = r1 if i % 2 == 0 else r1 * 0.80
        rr0 = r0 if i % 2 == 0 else r0 * 1.12
        x0, y0 = cx + math.sin(a) * rr0, cy - math.cos(a) * rr0
        x1, y1 = cx + math.sin(a) * rr1, cy - math.cos(a) * rr1
        nx, ny = math.cos(a) * th, math.sin(a) * th
        p.poly([(x0 - nx, y0 - ny), (x0 + nx, y0 + ny), (x1 + nx * 0.55, y1 + ny * 0.55), (x1 - nx * 0.55, y1 - ny * 0.55)],
               layer)


def _case(p, cx, y0, y1, w, rim=3.0):
    """Corpo do cartucho 2.0 (de y0 ate a base y1) com o aro da base mais largo e a fresta do sulco do aro."""
    p.rect(cx - w / 2, y0, cx + w / 2, y1 - 4)
    p.poly([(cx - w / 2 - rim + 1, y1 - 4), (cx + w / 2 + rim - 1, y1 - 4), (cx + w / 2 + rim, y1 - 2.5),
            (cx + w / 2 + rim, y1), (cx - w / 2 - rim, y1), (cx - w / 2 - rim, y1 - 2.5)])
    p.gap(cx - w / 2 - rim - 1, y1 - 6.4, cx + w / 2 + rim + 1, y1 - 4.4)


def icon_ammo2(kind):
    """Cartuchos 2.0 (seletor bs_ammo_type): he | ap | sap | ac | frag."""
    p = Pen()
    cx = 48
    if kind == "he":
        # granada 2.0: espoleta de ponta chata (corpo estreito + anel do sensor), ogiva longa, 2 frestas de luva e o aro
        w = 26
        p.poly([(cx - 4.2, 5), (cx + 4.2, 5), (cx + 5.6, 6.6), (cx + 5.6, 14), (cx - 5.6, 14), (cx - 5.6, 6.6)])
        p.gap(cx - 8, 8.8, cx + 8, 10.8)                   # anel do sensor na espoleta
        left, right = ogive_flat(cx, 14, 46, w, 6.0, sharp=0.9)
        p.poly(left + right[::-1])
        p.gap(cx - w / 2 - 2, 45.6, cx + w / 2 + 2, 47.8)   # juncao ogiva / luva
        _case(p, cx, 47.8, 89, w)
        sleeve_gaps(p, cx, 48, 83, 2, w)
        return p.render()
    if kind == "ap":
        # penetrador longo (dardo) com anel de sensor, colar do sabot em petalas, luva com 1 fresta e o aro
        w = 26
        p.poly([(cx, 4), (cx + 5.5, 22), (cx + 5.5, 48), (cx - 5.5, 48), (cx - 5.5, 22)])
        p.gap(cx - 7, 26, cx + 7, 28.2)
        for s in (-1, 1):                                  # petalas do sabot abrindo para fora
            p.poly([(cx + s * 6.5, 50), (cx + s * 13, 41), (cx + s * 16.5, 43), (cx + s * 13.5, 53)])
        p.rect(cx - 13.5, 50, cx + 13.5, 56)
        p.gap(cx - 15, 55.8, cx + 15, 58)
        _case(p, cx, 58, 88, w)
        sleeve_gaps(p, cx, 58, 84, 1, w)
        return p.render()
    if kind == "sap":
        # capuz ROMBUDO largo (chato), colar, luva com 1 fresta e a meia-estrela do estopim no meio do corpo
        w = 30
        cx = 44
        left, right = ogive_flat(cx, 12, 34, w, 9.5, sharp=0.35)
        p.poly(left + right[::-1])
        p.gap(cx - w / 2 - 2, 22.5, cx + w / 2 + 2, 24.7)   # divisa capuz / ogiva
        p.gap(cx - w / 2 - 2, 33.6, cx + w / 2 + 2, 35.8)
        _case(p, cx, 35.8, 88, w)
        sleeve_gaps(p, cx, 36, 82, 1, w)
        star(p, cx + w / 2 + 1, 56, 6.0, 14, n=7, rot=10)
        return p.render(ACC["fire"])
    if kind == "ac":
        # guiada: corpo fino, ogiva longa com o buscador (anel), canards no ombro, aletas na cauda e a faixa de OURO
        w = 22
        left, right = ogive(cx, 6, 38, w, sharp=1.1)
        p.poly(left + right[::-1])
        p.gap(cx - 6, 13.2, cx + 6, 15.2)                 # anel do buscador
        canards(p, cx, 30, w, span=7.5, h=7)
        p.rect(cx - w / 2, 38, cx + w / 2, 84)
        p.gap(cx - w / 2 - 3, 37.8, cx + w / 2 + 3, 40)
        p.rect(cx - w / 2 - 1, 46, cx + w / 2 + 1, 54, "acc")   # faixa de ouro
        p.gap(cx - w / 2 - 3, 44.2, cx + w / 2 + 3, 46.2)
        p.gap(cx - w / 2 - 3, 54, cx + w / 2 + 3, 56)
        fins(p, cx, 66, w, h=24, span=11)
        p.poly([(cx - 8, 84), (cx + 8, 84), (cx + 9.5, 91), (cx - 9.5, 91)])
        p.gap(cx - w / 2 - 12, 83.6, cx + w / 2 + 12, 85.4)
        return p.render(ACC["gold"])
    if kind == "frag":
        # granada curta e gorda (luva de fragmentos com 3 frestas) e o leque de 7 tracos para a frente (verde-agua)
        w = 32
        left, right = ogive_flat(cx, 48, 60, w, 8.0, sharp=0.5)
        p.poly(left + right[::-1])
        p.gap(cx - w / 2 - 2, 59.6, cx + w / 2 + 2, 61.8)
        _case(p, cx, 61.8, 92, w)
        sleeve_gaps(p, cx, 61.8, 87, 2, w, th=2.2)
        fragment_fan(p, cx, 50, 7, 124, r0=12, r1=34)
        return p.render(ACC["teal"])
    raise ValueError(kind)


def icon_cell(kind):
    """Celulas 2.0 (seletor bs_cell_type): plasma | pem."""
    p = Pen()
    if kind == "plasma":
        # capsula com tampas (frestas), bornes nas pontas e a janela do nucleo CIANO segmentada
        cx, w = 48, 34
        p.rect(cx - 6, 4, cx + 6, 10)
        p.rect(cx - 6, 86, cx + 6, 92)
        capsule(p, cx, 9, 87, w, cap=0.30)
        p.gap(cx - w / 2 - 2, 21, cx + w / 2 + 2, 23.2)
        p.gap(cx - w / 2 - 2, 72.8, cx + w / 2 + 2, 75)
        p.gap(cx - 10.5, 28.5, cx + 10.5, 67.5)            # moldura da janela (vao) ...
        p.rect(cx - 7.5, 31, cx + 7.5, 65, "acc")          # ... e o nucleo aceso dentro
        for y in (41.6, 53.2):
            p.gap(cx - 8, y, cx + 8, y + 2.2)
        return p.render(ACC["cyan"])
    if kind == "pem":
        # capsula com 3 bobinas mais largas (costelas na silhueta, espiras partidas) e o raio
        cx, w = 40, 28
        p.rect(cx - 5, 4, cx + 5, 10)
        p.rect(cx - 5, 86, cx + 5, 92)
        capsule(p, cx, 9, 87, w, cap=0.30)
        for y in (28, 45, 62):
            p.rect(cx - w / 2 - 4, y, cx + w / 2 + 4, y + 10)
            p.gap(cx - w / 2 - 5, y + 4, cx + w / 2 + 5, y + 5.8)
            p.gap(cx - w / 2 - 5, y - 2.4, cx + w / 2 + 5, y - 0.4)
        bolt(p, 58, 16, 1.0)
        return p.render(ACC["spark"])
    raise ValueError(kind)


def _missile2(p, cx, top, bottom, w, nose=0.30, fin=1.0, seeker=True):
    """Missil 2.0 de pe: ogiva com anel do buscador, corpo, aletas em flecha quebrada e bocal."""
    L = bottom - top
    yb = top + L * nose
    left, right = ogive(cx, top, yb, w, sharp=0.8)
    tail = bottom - L * 0.08
    p.poly(left + [(cx - w / 2, tail), (cx + w / 2, tail)] + right[::-1])
    if seeker:
        p.gap(cx - w / 2, top + L * 0.07, cx + w / 2, top + L * 0.07 + 2.0)
    fw = w * 0.62 * fin
    for s in (-1, 1):                                       # aleta em flecha quebrada (2 degraus)
        y0 = bottom - L * 0.34
        p.poly([(cx + s * w / 2, y0), (cx + s * (w / 2 + fw * 0.55), y0 + L * 0.10),
                (cx + s * (w / 2 + fw), y0 + L * 0.16), (cx + s * (w / 2 + fw), tail),
                (cx + s * w / 2, tail)])
    p.poly([(cx - w * 0.32, tail), (cx + w * 0.32, tail), (cx + w * 0.42, bottom), (cx - w * 0.42, bottom)])
    p.gap(cx - w / 2 - fw - 1, tail - 0.4, cx + w / 2 + fw + 1, tail + 1.6)
    return yb, tail


def icon_missile2(kind):
    """Misseis 2.0 (seletor bs_missile_type): he | cluster | emp | nuclear."""
    p = Pen()
    if kind == "he":
        # Jararaca: flecha fina com as luvas em DIVISA (escamas) e o anel do buscador
        yb, tail = _missile2(p, 48, 4, 92, 17, nose=0.27, fin=1.15)
        sleeve_gaps(p, 48, yb + 1, tail - 16, 3, 17, th=2.3, chevron=4.5)
        return p.render()
    if kind == "cluster":
        # Piranha: portador com as 4 petalas ABERTAS e um leque denso de 11 minimisseis saindo dele
        cx = 48
        _missile2(p, cx, 60, 93, 21, nose=0.04, fin=0.8, seeker=False)
        for sd in (-1, 1):                                  # petalas abertas (2 vistas de lado)
            p.poly([(cx + sd * 10, 64), (cx + sd * 4.5, 63), (cx + sd * 12, 52.5), (cx + sd * 17.5, 55.5)])
            p.poly([(cx + sd * 4, 63), (cx + sd * 1.2, 62.5), (cx + sd * 4.5, 52), (cx + sd * 8, 53)])
        # 11 minimisseis FINOS (dardo com 2 aletas), em 2 arcos: 6 mais perto e 5 mais longe, entre eles
        minis = [(-62, 25), (-37, 27), (-12, 28), (12, 28), (37, 27), (62, 25),
                 (-50, 44), (-25, 46.5), (0, 47.5), (25, 46.5), (50, 44)]
        for ang, r in minis:
            p.at(cx + r * math.sin(math.radians(ang)), 60 - r * math.cos(math.radians(ang)), ang, 0.80)
            p.poly([(0, -9.5), (2.0, -5.5), (2.0, 4), (-2.0, 4), (-2.0, -5.5)])
            for sd in (-1, 1):
                p.poly([(sd * 2.0, 1.5), (sd * 4.6, 5.2), (sd * 4.6, 7.4), (sd * 2.0, 5.4)])
            p.at()
        return p.render()
    if kind == "emp":
        # Poraque: missil com as bobinas (costelas largas partidas) e o raio
        cx = 38
        yb, tail = _missile2(p, cx, 8, 90, 18)
        for y in (40, 50, 60):
            p.rect(cx - 12.5, y, cx + 12.5, y + 6)
            p.gap(cx - 14, y + 6, cx + 14, y + 8)
        bolt(p, 54, 14, 1.05)
        return p.render(ACC["spark"])
    if kind == "nuclear":
        # Iara: ogiva GORDA em 3 camadas (frestas), janela de contencao, aletas e o trevo verde
        cx, w = 38, 28
        left, right = ogive(cx, 8, 38, w, sharp=0.12)
        p.poly(left + [(cx - w / 2, 80), (cx + w / 2, 80)] + right[::-1])
        p.gap(cx - w / 2 - 2, 24, cx + w / 2 + 2, 26)
        p.gap(cx - w / 2 - 2, 38, cx + w / 2 + 2, 40.2)
        p.gap(cx - 6, 47, cx + 6, 66)                       # janela de contencao
        p.rect(cx - 6, 52.5, cx + 6, 54.5)                  # grade
        p.rect(cx - 6, 58.5, cx + 6, 60.5)
        for s in (-1, 1):
            p.poly([(cx + s * w / 2, 62), (cx + s * (w / 2 + 8), 74), (cx + s * (w / 2 + 8), 88), (cx + s * w / 2, 82)])
        p.poly([(cx - 9, 80), (cx + 9, 80), (cx + 11, 89), (cx - 11, 89)])
        p.gap(cx - w / 2 - 9, 79.6, cx + w / 2 + 9, 81.4)
        trefoil(p, 71, 26, 14)
        return p.render(ACC["nuke"])
    raise ValueError(kind)


def icon_slug():
    """Projetil da Tupa: haste com ponta de penetrador, aneis de armadura (azul-gelo) e aletas curtas."""
    p = Pen()
    cx = 48
    rod_armature(p, cx, 3, 84, 9, 4, ring_w=25, ring_h=5.5)
    for s in (-1, 1):
        p.poly([(cx + s * 4.5, 70), (cx + s * 13, 82), (cx + s * 13, 91), (cx + s * 4.5, 87)])
    p.rect(cx - 4.5, 84, cx + 4.5, 91)
    return p.render(ACC["rail"])


def icon_group2():
    """Grupo do editor 2.0: granada futurista inclinada (espoleta chata, anel do sensor, luvas partidas) com rastros
    de velocidade."""
    p = Pen()
    p.at(57, 39, 45)
    w = 24
    left, right = ogive_flat(0, -33, -10, w, 4.0, sharp=0.9)
    p.poly(left + right[::-1])
    p.gap(-7, -27.4, 7, -25.6)
    p.gap(-w / 2 - 2, -10.4, w / 2 + 2, -8.4)
    _case(p, 0, -8.4, 31, w)
    sleeve_gaps(p, 0, -8, 25, 2, w, th=2.2)
    p.at()
    for x, y, L in ((15, 58, 18), (25, 70, 24), (37, 80, 16)):
        p.at(x, y, 45)
        p.rect(-2.2, -L / 2, 2.2, L / 2)
        p.at()
    return p.render()


# nome do arquivo no mod (gui/<nome>) -> funcao; ordem = a do spec (art_assets.assets.ui_icons.icons)
ICONS_2_0 = {
    "ammo_he.png": lambda: icon_ammo2("he"),
    "ammo_ap.png": lambda: icon_ammo2("ap"),
    "ammo_sap.png": lambda: icon_ammo2("sap"),
    "ammo_ac.png": lambda: icon_ammo2("ac"),
    "ammo_frag.png": lambda: icon_ammo2("frag"),
    "cell_plasma.png": lambda: icon_cell("plasma"),
    "cell_pem.png": lambda: icon_cell("pem"),
    "missile_he.png": lambda: icon_missile2("he"),
    "missile_cluster.png": lambda: icon_missile2("cluster"),
    "missile_emp.png": lambda: icon_missile2("emp"),
    "missile_nuclear.png": lambda: icon_missile2("nuclear"),
    "slug_rail.png": icon_slug,
    "group_bullet_strike.png": icon_group2,
}


def write_icons_2_0(out_dir):
    """Grava os icones 2.0 (96 x 96) em out_dir + icons.json (indice: arquivo do mod -> arquivo daqui). O indice NAO
    se chama meta.json de proposito: o check_art3d 'todos' so le pastas com meta.json de pecas."""
    import json
    import os
    os.makedirs(out_dir, exist_ok=True)
    files = {}
    for name, fn in ICONS_2_0.items():
        im = fn()
        im.save(os.path.join(out_dir, name))
        files[f"gui/{name}"] = name
    idx = {"version": 1, "kind": "ui_icons", "size": [SIZE, SIZE], "renderer": "tools/bsgen/ui_icons.py (2.0)",
           "files": files, "drop_1x": ["gui/ammo_std.png", "gui/ammo_aphe.png", "gui/ammo_emp.png",
                                       "gui/missile_limpet.png", "gui/missile_napalm.png", "gui/missile_torpedo.png"],
           "accents": {k: list(v) for k, v in ACC.items()}}
    with open(os.path.join(out_dir, "icons.json"), "w", encoding="utf-8") as fh:
        json.dump(idx, fh, indent=1, ensure_ascii=False)
    return files


if __name__ == "__main__":
    import os
    import sys
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "art3d", "bs_ui_icons2")
    for k in write_icons_2_0(out):
        print(k)
    print("OK", out)
