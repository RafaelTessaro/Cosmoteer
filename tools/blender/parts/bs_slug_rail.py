"""Projetil de Railgun (bs_slug_rail, 2.0, NOVO) - municao da Tupa; pilha de 2.

SPEC 2.0 ("tungsten rod with armature rings and a gold tip, in a light cradle") com a paleta AZUL nova da Tupa
(USER_NOTES: referencia do usuario, "slug da Tupa acompanha a cor"; parts/bs_rail.py): o dardo de tungstenio claro
num BERCO claro (parts/_bs2_itens_helpers.slug): 2 trilhos de bisel duplo com pontas em cunha sobre um leito escuro,
travas LARANJA (os detalhes laranja da referencia) e o LED azul de estado na ponta de cada trilho; 4 colares EM AZUIS
(labios anodizados + fenda acesa), ponta de penetrador clara com o ponto quente ouro-branco e 6 aletas curtas de
grafite na cauda. Nunca cobre, nunca chama.
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
    "icon_scale": 0.92,
    "stack_layout": IT.SLUG_LAYOUT,
    "stack_rot": [0, 0, 0, 0, 0, 0],
}


def item(M, T="item"):
    IT.slug(M, IT.X(M), (T,))
