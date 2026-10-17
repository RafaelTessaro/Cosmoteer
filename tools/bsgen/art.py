"""Motor de arte procedural do Bullet Strike (Pillow + numpy).

Cada sprite e desenhado em 4x (supersampling) num "Canvas" que guarda:
  - albedo RGBA (cores)
  - altura (float) -> vira sombreamento embutido + mapa de normais no formato do Cosmoteer
    (R = +x direita, G = +y PARA CIMA, B = +z, plano = (127,127,255))
Depois tudo e reduzido para 64 px por tile com LANCZOS.
"""

import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

SS = 4          # fator de supersampling
PX = 64         # pixels por tile no jogo


def clamp8(a):
    return np.clip(a, 0, 255).astype(np.uint8)


def mix(c1, c2, t):
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * t)) for i in range(3))


def shade(c, f):
    return tuple(max(0, min(255, int(round(v * f)))) for v in c[:3])


class Canvas:
    def __init__(self, w_px, h_px):
        """w_px/h_px = tamanho FINAL em pixels (o desenho interno e SS vezes maior)."""
        self.w, self.h = w_px, h_px
        self.W, self.H = w_px * SS, h_px * SS
        self.albedo = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        self.height = np.zeros((self.H, self.W), dtype=np.float32)
        self.emissive = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        self.seed = (w_px * 7919 + h_px * 104729) % 2**31

    # ---------------------------------------------------------------- coordenadas
    def s(self, v):
        return v * SS

    def box(self, x0, y0, x1, y1):
        return [x0 * SS, y0 * SS, x1 * SS - 1, y1 * SS - 1]

    # ---------------------------------------------------------------- mascaras
    def _mask(self):
        return Image.new("L", (self.W, self.H), 0)

    def mask_rect(self, x0, y0, x1, y1, r=0):
        m = self._mask()
        ImageDraw.Draw(m).rounded_rectangle(self.box(x0, y0, x1, y1), radius=r * SS, fill=255)
        return m

    def mask_ellipse(self, cx, cy, rx, ry=None):
        ry = rx if ry is None else ry
        m = self._mask()
        ImageDraw.Draw(m).ellipse(self.box(cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
        return m

    def mask_poly(self, pts):
        m = self._mask()
        ImageDraw.Draw(m).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
        return m

    # ---------------------------------------------------------------- pintura
    def fill(self, mask, color, alpha=255, height=None, bevel=2.0, mode="max", gradient=None):
        """Pinta uma forma. height: altura do topo (0..1); bevel: largura (px finais) da borda chanfrada.

        gradient: (cor_topo, cor_base) aplica um degrade vertical dentro da forma.
        """
        if gradient:
            top, bot = gradient
            grad = Image.linear_gradient("L").resize((self.W, self.H))
            col = Image.composite(Image.new("RGBA", (self.W, self.H), bot + (alpha,)),
                                  Image.new("RGBA", (self.W, self.H), top + (alpha,)), grad)
        else:
            col = Image.new("RGBA", (self.W, self.H), tuple(color[:3]) + (alpha,))
        self.albedo.paste(col, (0, 0), mask)
        if height is not None:
            m = np.asarray(mask, dtype=np.float32) / 255.0
            if bevel > 0:
                prof = np.asarray(mask.filter(ImageFilter.BoxBlur(bevel * SS)), dtype=np.float32) / 255.0
                prof = np.clip((prof - 0.5) * 2.0 + 0.5, 0, 1) * m
            else:
                prof = m
            hm = prof * height
            inside = m > 0.5
            if mode == "max":
                self.height = np.where(inside, np.maximum(self.height, hm), self.height)
            elif mode == "set":
                self.height = np.where(inside, hm, self.height)
            elif mode == "add":
                self.height = self.height + hm
            elif mode == "sub":
                self.height = self.height - prof * height

    def glow(self, mask, color, strength=1.0, blur=3.0):
        """Brilho (vai para o albedo de forma aditiva, com halo)."""
        g = Image.new("RGBA", (self.W, self.H), tuple(color[:3]) + (0,))
        a = mask.filter(ImageFilter.GaussianBlur(blur * SS)).point(lambda v: min(255, int(v * strength)))
        g.putalpha(a)
        self.emissive = Image.alpha_composite(self.emissive, g)
        core = Image.new("RGBA", (self.W, self.H), tuple(mix(color, (255, 255, 255), 0.45)) + (0,))
        core.putalpha(mask)
        self.emissive = Image.alpha_composite(self.emissive, core)

    def line(self, pts, color, width=1.0, height=None, alpha=255):
        m = self._mask()
        ImageDraw.Draw(m).line([(x * SS, y * SS) for x, y in pts], fill=255, width=max(1, int(width * SS)))
        self.fill(m, color, alpha=alpha, height=height, bevel=0.5 if height else 0, mode="max")
        return m

    def groove(self, pts, width=1.0, depth=0.08, color=None):
        """Linha de painel: escurece e afunda a altura."""
        m = self._mask()
        ImageDraw.Draw(m).line([(x * SS, y * SS) for x, y in pts], fill=255, width=max(1, int(width * SS)))
        arr = np.asarray(m, dtype=np.float32) / 255.0
        self.height -= arr * depth
        if color is not None:
            c = Image.new("RGBA", (self.W, self.H), tuple(color[:3]) + (255,))
            self.albedo.paste(c, (0, 0), m)

    def rivet(self, x, y, r, color, height=0.12):
        d = ImageDraw.Draw(self.albedo)
        d.ellipse(self.box(x - r, y - r, x + r, y + r), fill=tuple(color[:3]) + (255,))
        # domo calculado so na janela do rebite
        R = r * SS
        x0, x1 = int(max(0, x * SS - R - 1)), int(min(self.W, x * SS + R + 2))
        y0, y1 = int(max(0, y * SS - R - 1)), int(min(self.H, y * SS + R + 2))
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dd = np.sqrt((xx - x * SS) ** 2 + (yy - y * SS) ** 2) / max(R, 1e-3)
        dome = np.clip(1 - dd * dd, 0, 1) * height
        self.height[y0:y1, x0:x1] += dome

    def hazard(self, x0, y0, x1, y1, c1=(230, 180, 40), c2=(25, 25, 28), step=6.0, height=None):
        m = self.mask_rect(x0, y0, x1, y1)
        stripes = Image.new("RGBA", (self.W, self.H), c2 + (255,))
        d = ImageDraw.Draw(stripes)
        hgt = (y1 - y0) * SS
        st = step * SS
        k = x0 * SS - hgt
        while k < x1 * SS + hgt:
            d.polygon([(k, y0 * SS), (k + st / 2, y0 * SS), (k + st / 2 - hgt, y1 * SS), (k - hgt, y1 * SS)], fill=c1 + (255,))
            k += st
        self.albedo.paste(stripes, (0, 0), m)
        if height is not None:
            self.fill(m, (0, 0, 0), alpha=0, height=height, bevel=0.5)
            self.albedo.paste(stripes, (0, 0), m)

    # ---------------------------------------------------------------- saida
    def normals(self, strength=2.2):
        h = self.height
        gy, gx = np.gradient(h)
        gx = gx * SS * strength
        gy = gy * SS * strength
        nx, ny, nz = -gx, gy, np.ones_like(h)          # +y PARA CIMA (imagem y para baixo)
        ln = np.sqrt(nx * nx + ny * ny + nz * nz)
        nx, ny, nz = nx / ln, ny / ln, nz / ln
        a = np.asarray(self.albedo.getchannel("A"), dtype=np.float32)
        img = np.dstack([clamp8(127 + 128 * nx), clamp8(127 + 128 * ny), clamp8(127 + 128 * nz), clamp8(a)])
        return Image.fromarray(img, "RGBA")

    def render(self, light=(-0.55, -0.65, 0.52), ambient=0.62, ao=0.35, bake=True):
        """Albedo com iluminacao embutida (o jogo tambem ilumina via normais; aqui e leve)."""
        img = self.albedo
        if bake:
            h = self.height
            gy, gx = np.gradient(h)
            nx, ny = -gx * SS * 2.2, -gy * SS * 2.2
            nz = np.ones_like(h)
            ln = np.sqrt(nx * nx + ny * ny + nz * nz)
            lx, ly, lz = light
            ll = math.sqrt(lx * lx + ly * ly + lz * lz)
            dif = (nx * lx + ny * ly + nz * lz) / (ln * ll)
            dif = np.clip(dif, 0, 1)
            # oclusao: regioes abaixo da vizinhanca ficam mais escuras
            blur = np.asarray(Image.fromarray(np.clip(h * 255, 0, 255).astype(np.uint8)).filter(
                ImageFilter.GaussianBlur(3 * SS)), dtype=np.float32) / 255.0
            occl = np.clip((blur - h) * 2.5, 0, 1)
            k = ambient + (1 - ambient) * dif * 1.35 - occl * ao
            arr = np.asarray(img, dtype=np.float32)
            arr[..., :3] *= k[..., None]
            # brilho nas quinas voltadas para a luz e escurecimento nas opostas (le melhor em tamanho pequeno)
            edge = (-gx * lx - gy * ly) * SS * 3.0
            arr[..., :3] += np.clip(edge, -0.6, 0.6)[..., None] * 70
            # textura metalica sutil (ruido fixo pela semente)
            rng = np.random.default_rng(self.seed)
            noise = rng.normal(0, 1, (self.H // SS + 1, self.W // SS + 1)).astype(np.float32)
            noise = np.kron(noise, np.ones((SS, SS), np.float32))[: self.H, : self.W]
            arr[..., :3] += noise[..., None] * 4.0
            img = Image.fromarray(clamp8(arr), "RGBA")
        img = Image.alpha_composite(img, self.emissive) if self.emissive.getbbox() else img
        return img.resize((self.w, self.h), Image.LANCZOS)

    def final_normals(self, strength=2.2):
        return self.normals(strength).resize((self.w, self.h), Image.LANCZOS)


def drop_shadow(img, radius=2, alpha=40):
    """Sombra suave embutida em volta da silhueta (como os sprites de torre vanilla)."""
    a = img.getchannel("A").filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(alpha, v))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(a)
    return Image.alpha_composite(sh, img)


def silhouette_shadow(img, size_px, blur=5, alpha=110):
    a = img.getchannel("A").resize(size_px, Image.LANCZOS).filter(ImageFilter.GaussianBlur(blur))
    a = a.point(lambda v: min(alpha, int(v * 0.6)))
    out = Image.new("RGBA", size_px, (0, 0, 0, 0))
    out.putalpha(a)
    return out


def flat_normals(size, alpha_from=None):
    img = Image.new("RGBA", size, (127, 127, 255, 255))
    if alpha_from is not None:
        img.putalpha(alpha_from.getchannel("A"))
    return img
