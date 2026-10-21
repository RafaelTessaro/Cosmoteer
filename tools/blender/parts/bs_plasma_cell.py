"""Celula de Plasma (bs_plasma_cell, 2.0) - municao do Boitata e do Curupira; pilha de 4.

REWORK futurista (USER_NOTES 2026-10-21; SPEC 2.0 art_assets.assets.resources "hex-armoured cylinder with a cyan
core window in a recess"): celula deitada ao longo de Y (parts/_bs2_itens_helpers.cell): corpo SEXTAVADO de blindagem
clara em 3 segmentos com juntas escuras e 2 colares de reforco mais largos (nervuras na silhueta), janela longa no
topo com o NUCLEO DE PLASMA CIANO segmentado num leito preto (filetes de aco nas bordas), tampas escuras sextavadas com
o LED de estado ciano num rebaixo e os bornes de aco nas pontas. Sem cobre (cobre = celula PEM).
A ID e a da 1.x; so a arte muda. Pilha: fileira de celulas deitadas lado a lado (bandeja), com desencontro em y.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

PART = IT.cell_part("rafaeltessaro.bs_plasma_cell", "plasma", 4, "cyan")


def item(M, T="item"):
    IT.cell(M, IT.X(M), (T,), "plasma")
