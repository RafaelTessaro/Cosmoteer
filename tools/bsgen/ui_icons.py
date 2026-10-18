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
