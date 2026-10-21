"""Carga de Missil HE (bs_msl_he, 2.0, NOVO) - municao dos lancadores (Jararaca/Muricoca); pilha de 10.

SPEC 2.0 ("small missile charge in a cradle, amber band, sleeve seams"): o missil HE 2.0 (Jararaca) em miniatura num
berco de prateleira (parts/_bs2_itens_helpers.charge): treno de NUCLEO ESCURO mais largo que o corpo com 2 trilhos
claros de bisel duplo por fora (fundo escuro tambem no casco branco); flecha FINA e longa (a Piranha e gorda e
curta): 3 luvas claras em divisa com frestas PRETAS, faixa AMBAR de ~3 px (Mo.band_mat("he"), a mesma tinta do
missil em voo e dos narizes nos lancadores), ogiva clara com o ANEL AMBAR do buscador e o domo escuro, 2 aletas em
flecha atras dos trilhos e o LED ambar num rebaixo da luva de tras.
Pilha (charge_part/MSL_LAYOUT): 1..5 centradas numa fileira (passo 0,14); 6..10 = fileira de 5 + a 2a camada
desencontrada meio passo e recuada (os 10 narizes aparecem). Desvio do stack_layout_7_10 do spec, que enchia da
esquerda (1 carga solta na beira do quadro) e empilhava no mesmo y (um pente).
"""

import bs3d as B  # noqa: F401  (contrato dos modelos)
import models as Mo  # noqa: F401
from parts import _bs2_itens_helpers as IT

KIND = "msl_he"
PART = IT.charge_part("rafaeltessaro.bs_msl_he", KIND, "amber")


def item(M, T="item"):
    IT.charge(M, IT.X(M), (T,), KIND)
