"""Fileira de produtos das fabricas 2.0 (como aparecem DENTRO das maquinas), so para as previas do grupo "fabricas".

Nao e uma peca do jogo: e um modelo kind "factory" de 12 x 1 quadros so para usar o render_part.py; o
machine_on1.png e cortado em 12 quadros de 64 px (ordem = ITEMS) por _bs2_fabricas_previews.py. Render:

    <venv>/bin/python tools/blender/render_part.py tools/blender/parts/_bs2_fabricas_itens.py --out <pasta>

(o _bs2_fabricas_previews.py faz isso sozinho numa pasta temporaria quando recebe --blender <venv>/bin/python).
Os desenhos sao os mini_*() de _bs2_fabricas_helpers.py, os mesmos que as maquinas F1-F6 usam.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # tools/blender (render por caminho)

import bs3d as B  # noqa: E402
from parts import _bs2_fabricas_helpers as H  # noqa: E402

ITEMS = ["he", "ap", "sap", "ac", "frag", "plasma", "pem", "msl_he", "msl_cluster", "msl_emp", "nuke", "slug"]
PART = {"id": "rafaeltessaro.bs2_fabricas_itens_previa", "kind": "factory", "size": [len(ITEMS), 1],
        "accent": "amber", "machine_frames": 1, "machine_interval": 0.1}


def floor(M, T="floor"):
    B.box("fl", 0, 0, len(ITEMS), 1, -0.05, 0.0, M["core"], bevel=0.0, tags=(T,))


def roof(M, T="roof"):
    B.box("rf", 0, 0, len(ITEMS), 1, -0.05, 0.0, M["core"], bevel=0.0, tags=(T,))


def machine(M, T="machine", phase=0.0):
    tags = (T,)
    Xm = H.X(M)
    n = len(ITEMS)
    for k, it in enumerate(ITEMS):
        x = k + 0.5 - n / 2
        if it in ("he", "ap", "sap", "ac", "frag"):
            H.mini_mag(f"i{k}", x, 0.0, 0.0, M, Xm, tags, kind=it, s=2.6)
        elif it in ("plasma", "pem"):
            H.mini_cell(f"i{k}", x, 0.0, 0.0, M, Xm, tags, kind=it, s=2.2, rz=0.0)
        elif it.startswith("msl"):
            H.mini_missile(f"i{k}", x, 0.0, 0.0, M, Xm, tags, kind=it, s=2.15)
        elif it == "nuke":
            H.mini_warhead(f"i{k}", x, -0.02, 0.0, M, Xm, tags, s=2.3)
        else:
            H.mini_slug(f"i{k}", x, 0.0, 0.0, M, Xm, tags, s=1.85)
