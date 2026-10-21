"""Ogiva Nuclear (bs_msl_nuke, 2.0) - carga da Iara (missil nuclear da Mula); pilha de 2.

SPEC 2.0 ("fat warhead, green band, 3-wedge trefoil inlay, NO chevrons, NO yellow"; REWORK de bs_shell_nuke.py, que
sai com o Projetil Nuclear da 1.x): a ogiva gorda da Iara 2.0 (parts/_bs2_itens_helpers.warhead): base com colar claro
de bisel duplo e os 3 LEDs verdes de estado, corpo de GRAFITE (a Iara e o unico missil de blindagem escura) com a faixa
verde larga num sulco e a janela de contencao (nucleo verde aceso atras da grade de aco), colar claro no pescoco, ogiva
clara com o TREVO de 3 cunhas escuras sobre disco verde (STYLE 7: permitido no recurso nuclear) e o sensor escuro na
ponta. Sem divisas, sem amarelo. Pilha: 1 no centro, 2 lado a lado.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

PART = {
    "id": "rafaeltessaro.bs_msl_nuke",
    "kind": "resource",
    "accent": "green",
    "max_stack": 2,
    "unit_scale": IT.NK_SCALE,
    "icon_scale": 0.92,
    "stack_layout": IT.NK_LAYOUT,
    "stack_rot": [0, 0, 0, 0, 0, 0],
}


def item(M, T="item"):
    IT.warhead(M, IT.X(M), (T,))
