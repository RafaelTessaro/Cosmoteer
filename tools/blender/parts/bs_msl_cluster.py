"""Carga de Missil de Submunicao (bs_msl_cluster, 2.0, NOVO) - Piranha; pilha de 10.

SPEC 2.0 ("charge with the 4-petal segmented nose"): o portador 2.0 (Piranha) em miniatura no mesmo berco de
prateleira das cargas (parts/_bs2_itens_helpers.charge: treno escuro + trilhos claros, aqui so ao lado da cauda
estreita): corpo GORDO (~6 px) e CURTO com 2 baias escuras mostrando os narizes AMARELOS dos minimisseis e o nariz
GRANDE em 4 PETALAS AMARELAS (Mo.band_mat("cluster") = a Piranha em voo e nos lancadores) com a fresta PRETA no eixo e
os entalhes dos lados; LED amarelo so no aro da articulacao. A 1x: bloco gordo com a ponta amarela de varios px
(a HE e uma flecha fina com faixa ambar).
Cor: amarelo-limao dos misseis 2.0 (USER_NOTES/STYLE 8.3: "Piranha amarela") em vez do laranja-ouro do
palette.cluster/look do spec, que a 1x se confundia com a HE. Desvio consciente: nao "corrigir" de volta na ligacao.
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

KIND = "msl_cluster"
PART = IT.charge_part("rafaeltessaro.bs_msl_cluster", KIND, "amber")


def item(M, T="item"):
    IT.charge(M, IT.X(M), (T,), KIND)
