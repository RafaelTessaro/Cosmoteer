"""Carregador FRAG - Nuvem de Fragmentos (bs_mag_frag, 2.0, NOVO; so defesas); pilha de 6.

A mesma caixa da familia (parts/_bs2_itens_helpers.magazine) com a fenda de LED e as pastilhas VERDE-AGUA
(palette.frag 120,210,200: faixa, pastilhas e LED no mesmo matiz ~170, longe do verde nuclear) e 3 granadas de flak
CURTAS e gordas (a ponta fica antes das outras): luva de fragmentos segmentada (aneis claros com sulcos pretos),
faixa verde-agua e espoleta de proximidade chata (aro de aco com a lente escura). Os narizes curtos e os aneis
listrados separam a FRAG das outras a 1x.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

AMMO = "frag"
PART = IT.mag_part("rafaeltessaro.bs_mag_frag", AMMO, 6)


def item(M, T="item"):
    IT.magazine(M, IT.X(M), (T,), AMMO)
