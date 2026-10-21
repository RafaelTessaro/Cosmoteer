"""Celula PEM (bs_cell_emp, 2.0, NOVO) - municao da linha de canhoes PEM (Tuvira, Treme-Treme, Corisco); pilha de 4.

SPEC 2.0 art_assets.assets.resources ("cell with 3 copper coil rings and a low blue LED band"): o mesmo chassi da
Celula de Plasma (parts/_bs2_itens_helpers.cell: corpo SEXTAVADO de blindagem clara, tampas escuras, bornes de aco),
mas com 3 BOBINAS DE COBRE (3 espiras redondas sobre um nucleo escuro, mais largas que o corpo: costelas de cobre na
silhueta, a assinatura da familia PEM) e duas janelas curtas com a faixa de LED AZUL de forca baixa (azul mais fundo
que o ciano do plasma, STYLE 9). Substitui o Carregador EMP da 1.x (bs_mag_emp, que sai).
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

PART = IT.cell_part("rafaeltessaro.bs_cell_emp", "pem", 4, "blue")


def item(M, T="item"):
    IT.cell(M, IT.X(M), (T,), "pem")
