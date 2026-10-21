"""Carregador SAP (bs_mag_sap, 2.0, NOVO) - Semiperfurante; pilha de 5.

A mesma caixa da familia (parts/_bs2_itens_helpers.magazine) com a fenda de LED e as pastilhas LARANJA AVERMELHADAS
(matiz ~18, entre o tracer e o hull do palette.sap; o laranja 255,140,50 ficava a ~15 graus do ambar da HE) e 3
granadas SAP do nivel S passando da boca: faixa laranja-avermelhada FORA da caixa, ogiva curtissima, aro PRETO e a
TAMPA QUADRADA larga de aco claro (ponta chata). A 1x a SAP le como 3 blocos claros rombudos alinhados, a HE como 3
ogivas escuras pontudas em seta: forma E cor. Pilha de 5: 2 x 2 + uma cruzada (girada 90 graus) na camada de cima.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

AMMO = "sap"
PART = IT.mag_part("rafaeltessaro.bs_mag_sap", AMMO, 5)


def item(M, T="item"):
    IT.magazine(M, IT.X(M), (T,), AMMO)
