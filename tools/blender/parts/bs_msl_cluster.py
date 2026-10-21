"""Carga de Missil de Submunicao (bs_msl_cluster, 2.0, NOVO) - Piranha; pilha de 10.

SPEC 2.0 ("charge with the 4-petal segmented nose"): o portador 2.0 (Piranha) em miniatura num berco
(parts/_bs2_itens_helpers.charge): corpo GORDO com 2 baias escuras mostrando os narizes dos minimisseis, faixa
AMARELA (Mo.band_mat("cluster") = a Piranha em voo e nos lancadores: o amarelo-limao aprovado nos misseis 2.0, em vez
do laranja do palette.cluster, que a 1x se confundia com a HE) e o nariz em 4 PETALAS com a fresta escura no eixo
(tira amarela fraca dentro) e a ponta amarela.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

KIND = "msl_cluster"
PART = IT.charge_part("rafaeltessaro.bs_msl_cluster", KIND, "amber")


def item(M, T="item"):
    IT.charge(M, IT.X(M), (T,), KIND)
