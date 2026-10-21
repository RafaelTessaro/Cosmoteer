"""Projetil de Railgun (bs_slug_rail, 2.0, NOVO) - municao da Tupa; pilha de 2.

SPEC 2.0 ("tungsten rod with armature rings and a gold tip, in a light cradle") com a paleta AZUL nova da Tupa
(USER_NOTES: referencia do usuario, "slug da Tupa acompanha a cor"; parts/bs_rail.py): o dardo de tungstenio claro
num BERCO claro (parts/_bs2_itens_helpers.slug): 2 trilhos de bisel duplo com pontas em cunha sobre um leito escuro,
travas LARANJA (os detalhes laranja da referencia) e o LED azul de estado na ponta de cada trilho; 4 colares EM AZUIS
(labios anodizados + fenda acesa), ponta de penetrador clara com o ponto quente ouro-branco e 3 aletas curtas de
grafite na cauda (2 laterais + 1 dorsal). Nunca cobre, nunca chama.
Cor: AZUL em vez do violeta do palette.rail/look do spec, por decisao do usuario (USER_NOTES); desvio consciente,
nao "corrigir" de volta na ligacao (ver as NOTAS PARA A LIGACAO em parts/_bs2_itens_helpers.py).
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

PART = {
    "id": "rafaeltessaro.bs_slug_rail",
    "kind": "resource",
    "accent": "blue",
    "max_stack": 2,
    "unit_scale": IT.SLUG_SCALE,
    "icon_scale": 0.88,                 # o halo do overlay (borrao de 5 px) cabe inteiro nos 128 px
    "stack_layout": IT.SLUG_LAYOUT,
    "stack_rot": [0, 0, 0, 0, 0, 0],
}


def item(M, T="item"):
    IT.slug(M, IT.X(M), (T,))
