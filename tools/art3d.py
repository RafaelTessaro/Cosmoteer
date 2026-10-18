"""Sprites 3D (renderizados no Blender) do Bullet Strike: leitura do meta.json e copia para o mod.

Cada peca com arte 3D tem uma pasta art3d/<id_curto>/ com os PNGs no formato do jogo e um meta.json
gerado por tools/blender/render_part.py. Quando a pasta existe, o gerador do mod usa a geometria do
meta (pivo, tamanho da torre, canos, quadros de animacao) e copia os PNGs em vez de desenhar a arte
procedural antiga.
"""

import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART3D = os.path.join(ROOT, "art3d")


def load_meta(short):
    p = os.path.join(ART3D, short, "meta.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        meta = json.load(f)
    missing = [n for n in meta.get("files", []) if not os.path.exists(os.path.join(ART3D, short, n))]
    if missing:
        raise FileNotFoundError(f"art3d/{short}: meta.json cita arquivos que nao existem: {missing[:5]}")
    return meta


# Arte procedural antiga (desenhada em Python) so com BS_ARTE_PROCEDURAL=1; sem isso, falta de art3d/<id> ou do
# logo 3D para o build (uma regressao nao passa despercebida).
ALLOW_PROCEDURAL = os.environ.get("BS_ARTE_PROCEDURAL") == "1"


def require(short, meta):
    """Devolve o meta; sem ele (art3d/<id>/meta.json ausente) aborta, a menos que BS_ARTE_PROCEDURAL=1."""
    if meta is None and not ALLOW_PROCEDURAL:
        raise FileNotFoundError(f"art3d/{short}/meta.json nao existe: renderize a peca (tools/blender/render_part.py) "
                                f"ou use BS_ARTE_PROCEDURAL=1 para a arte procedural antiga")
    return meta


def part_scales(short):
    """(unit_scale, icon_scale) do modelo tools/blender/parts/<id>.py, lidos do dicionario PART com ast (sem
    importar o Blender). None quando o modelo nao existe ou nao define as escalas."""
    import ast
    p = os.path.join(ROOT, "tools", "blender", "parts", f"{short}.py")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PART" for t in node.targets) \
                and isinstance(node.value, ast.Dict):
            vals = {}
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(k, ast.Constant) and k.value in ("unit_scale", "icon_scale"):
                    vals[k.value] = ast.literal_eval(v)
            if "unit_scale" in vals and "icon_scale" in vals:
                return vals["unit_scale"], vals["icon_scale"]
    return None


def nugget_factor(short, meta):
    """Reducao da unidade solta (nugget) de renders antigos, feitos com icon_scale: o tripulante carregava um
    carregador do tamanho do icone, o dobro da unidade da pilha. render_part.py agora renderiza o nugget com
    unit_scale e grava meta["nugget_scale"]; ate re-renderizar, o build reduz a imagem (fator < 1) no centro."""
    if meta.get("kind") != "resource" or meta.get("nugget_scale"):
        return None
    sc = part_scales(short)
    if not sc:
        return None
    f = sc[0] / sc[1]
    return f if f < 0.95 else None


def scaled_center(img, f):
    """Imagem do mesmo tamanho com o conteudo reduzido pelo fator f em volta do centro (alfa pre-multiplicado,
    sem franja nas bordas transparentes)."""
    from PIL import Image
    im = img.convert("RGBA")
    w, h = im.size
    sw, sh = max(1, round(w * f)), max(1, round(h * f))
    small = im.convert("RGBa").resize((sw, sh), Image.LANCZOS).convert("RGBA")
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(small, ((w - sw) // 2, (h - sh) // 2))
    return out


def overlay_glow(alpha, radius=5.0, strength=0.7):
    """Silhueta branca com halo suave (como os overlay.png vanilla, ex. resources/bullet/overlay.png): o alfa
    borrado (radius px) a strength fica por baixo da silhueta solida."""
    from PIL import Image, ImageChops, ImageFilter
    a = alpha.convert("L")
    halo = a.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: int(v * strength))
    out = Image.new("RGBA", a.size, (255, 255, 255, 0))
    out.putalpha(ImageChops.lighter(a, halo))
    return out


def copy_files(out_root, pdir, short, meta):
    """Copia os PNGs listados no meta para <mod>/<pdir>/. Renders de recurso antigos (sem nugget_scale /
    overlay_glow no meta) saem ja no formato atual: nugget do tamanho de uma unidade da pilha e overlay com halo."""
    from PIL import Image
    dst = os.path.join(out_root, pdir)
    os.makedirs(dst, exist_ok=True)
    nf = nugget_factor(short, meta)
    for name in meta["files"]:
        src = os.path.join(ART3D, short, name)
        if nf and name in ("nugget.png", "nugget_normals.png"):
            scaled_center(Image.open(src), nf).save(os.path.join(dst, name), optimize=True)
        elif meta.get("kind") == "resource" and name == "overlay.png" and not meta.get("overlay_glow"):
            overlay_glow(Image.open(src).convert("RGBA").getchannel("A")).save(os.path.join(dst, name), optimize=True)
        else:
            shutil.copyfile(src, os.path.join(dst, name))


def path(short, name):
    return os.path.join(ART3D, short, name)
