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


def copy_files(out_root, pdir, short, meta):
    """Copia os PNGs listados no meta para <mod>/<pdir>/."""
    dst = os.path.join(out_root, pdir)
    os.makedirs(dst, exist_ok=True)
    for name in meta["files"]:
        shutil.copyfile(os.path.join(ART3D, short, name), os.path.join(dst, name))


def path(short, name):
    return os.path.join(ART3D, short, name)
