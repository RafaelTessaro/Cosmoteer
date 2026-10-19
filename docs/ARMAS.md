# Bullet Strike: armas, munições e fábricas

> Gerado automaticamente por `tools/make_docs.py` a partir de `tools/spec/bullet_strike_spec.json` e `tools/spec/bullet_strike_missiles.json`. Não edite à mão.
> DPS = dano por segundo com munição padrão, sem overclock: dano direto + metade das explosões (convenção do spec). As defesas (Tatu, Tamanduá e Pororoca) só defendem: não causam dano em naves; a coluna mostra o dano por segundo contra projéteis.

## Início de jogo

| Arma | Codinome | Tamanho | Tripulação | Alcance | DPS | Munição | Overclock |
|---|---|---|---|---|---|---|---|
| **Metralhadora Leve de Convés** | Marimbondo | 1x1 | 1 | 220 m | 260 | Munição avulsa (jogo base) | - |
| **Metralhadora Pesada de Convés** | Mangangá | 1x2 | 1 | 240 m | 540 | Munição avulsa (jogo base) | - |
| **Canhão Automático de Convés 20 mm** | Carcará | 2x2 | 1 | 250 m | 1.000 | Munição avulsa (jogo base) | - |
| **Flak Leve de Convés** | Tatu | 2x2 | 1 | 180 m | só defesa: 3.000/s contra projéteis | Munição avulsa (jogo base) | - |

## Meio de jogo

| Arma | Codinome | Tamanho | Tripulação | Alcance | DPS | Munição | Overclock |
|---|---|---|---|---|---|---|---|
| **Metralhadora Pesada Quádrupla** | Saci | 2x2 | 2 | 300 m | 1.330 | Carregador Padrão (sem seletor) | Redemoinho |
| **Minigun de Convés** | Cigarra | 2x3 | 2 | 300 m | 2.040 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/P.E.M.) | Bafo de Dragão |
| **Canhão Naval Automático 76 mm** | Tambor | 3x4 | 3 | 340 m | 3.750 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/P.E.M.) | Salva Rápida |
| **Gatling de Plasma** | Boitatá | 2x3 | 2 | 320 m | 1.600 | Células de plasma | Sobrecarga |
| **CIWS de Convés** | Tamanduá | 3x3 | 2 | 250 m | só defesa: 10.000/s contra projéteis | Carregador Padrão | Barragem |

## Fim de jogo

| Arma | Codinome | Tamanho | Tripulação | Alcance | DPS | Munição | Overclock |
|---|---|---|---|---|---|---|---|
| **Canhão Rotativo Pesado 30 mm** | Furacão | 4x4 | 4 | 500 m | 6.000 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/P.E.M.) | Vendaval |
| **Canhão Naval Duplo 155 mm** | Trovão | 4x5 | 5 | 520 m | 7.600 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/P.E.M.) | Supercarga |
| **Canhão de Plasma Pesado** | Curupira | 4x5 | 4 | 550 m | 5.400 | Células de plasma | Erupção Solar |
| **Obuseiro Nuclear de Convés** | Boiúna | 5x6 | 6 | 600 m | 8.000 | Projéteis nucleares | Fat Boy (carga reforçada) |
| **Torre Naval Tripla 406 mm** | Mapinguari | 6x7 | 10 | 600 m | 16.000 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/P.E.M.) | Bordada Total |
| **Bateria Flak Pesada** | Pororoca | 4x4 | 4 | 320 m | só defesa: 12.000/s contra projéteis | Carregador Padrão | Muralha de Flak |

## Mísseis de convés

> Projeto completo em `docs/MISSEIS_PROJETO.md` (spec `tools/spec/bullet_strike_missiles.json`). Gerado por `tools/bsgen/launchers.py` e `tools/bsgen/shots.py`.

**Como funciona (igual nos três lançadores):** a tripulação leva as peças de míssil do jogo base até um paiol interno por família (A.E., T., P.E.M., nuclear). Um autocarregador passa um míssil por vez do paiol para as células visíveis, **só com tripulação no posto**. Com todas as células carregadas sai a salva em sequência (a última célula carregada dispara primeiro); depois a recarga recomeça. Trocar o tipo de míssil custa uma recarga completa do tipo novo (com overclock, se as células já estavam cheias na troca, a primeira salva espera a recarga normal, sem overclock); se o paiol ficar uma recarga inteira sem receber peças, as células já carregadas disparam mesmo assim (uma entrega atrasada não quebra a salva cheia). Sem energia. Carregado, o lançador explode junto com o estoque quando pega fogo ou é destruído: cada peça guardada (no paiol ou já nas células) soma a mesma força à explosão.

### Lançadores

| Lançador | Codinome | Fase | Tamanho | Trip. | Pontos de comando | Vida | Custo | Salva A.E. | Ciclo A.E. | Alcance | DPS efetivo por quadro (OC) | Overclock | Limite |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Caixa de Micromísseis de Convés** | Tocandira | Início | 2x2 | 1 | 2 | 8.000 | 3.100 cr | 12 em 0,733 s | 9,073 s | 300 m | 264,5 | Enxame Furioso (desligado) | - |
| **Lançador Duplo de Mísseis de Convés** | Caipora | Meio | 3x3 | 2 | 5 | 12.000 | 12.600 cr | 16 em 2 s | 18,96 s | 400 m | 328,2 (467,6) | Fúria da Caipora | - |
| **Bateria Pesada de Mísseis Quádrupla** | Mula-sem-Cabeça | Fim | 5x6 | 8 | 18 | 42.000 | 77.000 cr | 48 em 3,133 s | 15,805 s | 600 m | 379,6 (518,1) | Estouro da Boiada | 2 por nave (vaga nuclear, com a Boiúna) |

### Modos de cada lançador

> Ciclo = recarga de todas as células + salva. Paiol = capacidade da família, em peças. OC = ciclo com overclock (recarga ÷ 1,5; P.E.M. ÷ 1,2; o nuclear nunca acelera).

| Lançador | Míssil | Células | Peças por míssil | Recarga por célula | Salva | Ciclo (OC) | DPS efetivo por quadro | Paiol | Descarte em OC |
|---|---|---|---|---|---|---|---|---|---|
| Tocandira | Micromíssil (Muriçoca) | 6 cassetes | 0,5 peça de míssil A.E. | 1,39 s | 12 em 0,733 s | 9,073 s | 264,5 | 12 | - |
| Tocandira | Micromíssil Incendiário (Taturana-mirim) | 6 cassetes | 0,5 peça de míssil T. | 1,39 s | 12 em 0,733 s | 9,073 s | 99,2 | 12 | - |
| Caipora | Míssil Alto-Explosivo (Jararaca) | 16 | 2 peças de míssil A.E. | 1,06 s | 16 em 2 s | 18,96 s (13,307 s) | 328,2 | 64 | 2 peças/salva |
| Caipora | Míssil de Submunições (Piranha) | 16 | 2 peças de míssil A.E. | 1,06 s | 16 em 2 s | 18,96 s (13,307 s) | 295,4 | 64 | 2 peças/salva |
| Caipora | Míssil Grudento (Carrapato) | 16 | 2 peças de míssil A.E. | 1,06 s | 16 em 2 s | 18,96 s (13,307 s) | 328,2 | 64 | 2 peças/salva |
| Caipora | Míssil de Napalm (Taturana) | 16 | 2 peças de míssil T. | 1,06 s | 16 em 2 s | 18,96 s (13,307 s) | 140,6 | 64 | 2 peças/salva |
| Caipora | Míssil P.E.M. (Poraquê) | 16 | 2 peças de míssil P.E.M. | 1,06 s | 16 em 2 s | 18,96 s (16,133 s) | 121,9 | 64 | 2 peças/salva |
| Caipora | Torpedo com Iscas (Boto) | 2 | 6 peças de míssil A.E. | 4,65 s | 2 em 0,133 s | 9,433 s (6,333 s) | 282,7 | 64 | - |
| Mula-sem-Cabeça | Míssil Alto-Explosivo (Jararaca) | 48 | 2 peças de míssil A.E. | 0,264 s | 48 em 3,133 s | 15,805 s (11,581 s) | 379,6 | 192 | 6 peças/salva |
| Mula-sem-Cabeça | Míssil de Submunições (Piranha) | 16 | 4 peças de míssil A.E. | 0,6 s | 16 em 1 s | 10,6 s (7,4 s) | 339,6 | 192 | 4 peças/salva |
| Mula-sem-Cabeça | Míssil Grudento (Carrapato) | 16 | 4 peças de míssil A.E. | 0,6 s | 16 em 1 s | 10,6 s (7,4 s) | 377,4 | 192 | 4 peças/salva |
| Mula-sem-Cabeça | Míssil de Napalm (Taturana) | 16 | 4 peças de míssil T. | 0,6 s | 16 em 1 s | 10,6 s (7,4 s) | 150,9 | 192 | 4 peças/salva |
| Mula-sem-Cabeça | Míssil P.E.M. (Poraquê) | 16 | 3 peças de míssil P.E.M. | 0,6 s | 16 em 1 s | 10,6 s (9 s) | 95,6 | 96 | 3 peças/salva |
| Mula-sem-Cabeça | Torpedo com Iscas (Boto) | 4 | 12 peças de míssil A.E. | 2,37 s | 4 em 0,2 s | 9,68 s (6,52 s) | 330,6 | 192 | - |
| Mula-sem-Cabeça | Torpedo Nuclear (Iara) | 2 | 8 peças de míssil nuclear | 9,97 s | 2 em 0,067 s | 20,007 s (sem OC) | 266,6 | 32 | - |

### Tipos de míssil (seletor do lançador)

| # | Codinome | Míssil | Recurso | Lançadores | O que faz |
|---|---|---|---|---|---|
| 0 | **Jararaca** | Míssil Alto-Explosivo | peça de míssil A.E. | Tocandira, Caipora, Mula-sem-Cabeça | Ogiva alto-explosiva rápida e direta: o míssil de referência. Salvas grandes saturam os pontos de defesa. |
| 1 | **Piranha** | Míssil de Submunições | peça de míssil A.E. | Caipora, Mula-sem-Cabeça | Abre a 25 m do casco inimigo (ou no impacto, ou no fim do voo) e solta um cardume de minimísseis que se espalham por várias peças. Abatido antes de abrir, não solta nada. |
| 2 | **Carrapato** | Míssil Grudento | peça de míssil A.E. | Caipora, Mula-sem-Cabeça | Gruda no casco e explode 2,5 s depois, com alta chance de matar a tripulação que vier consertar. Abatido no voo, se perde; num escudo só estoura. |
| 3 | **Taturana** | Míssil de Napalm | peça de míssil T. | Tocandira, Caipora, Mula-sem-Cabeça | Explosão pequena, fogo garantido na peça atingida e calor em volta que continua acendendo incêndios. Inútil contra blindagem; extintor e espuma são o contra. |
| 4 | **Poraquê** | Míssil P.E.M. | peça de míssil P.E.M. | Caipora, Mula-sem-Cabeça | Drena baterias e escudos em área e continua drenando as peças com energia por alguns segundos. As armas do Bullet Strike não usam bateria e são imunes. |
| 5 | **Boto** | Torpedo com Iscas | peça de míssil A.E. | Caipora, Mula-sem-Cabeça | Torpedo lento e resistente: 1,5 s depois do lançamento a ogiva se separa no meio de iscas que gastam os pontos de defesa e a flak. |
| 6 | **Iara** | Torpedo Nuclear | peça de míssil nuclear | Mula-sem-Cabeça | Só na bateria pesada. Conta no limite nuclear (2 por nave, junto com a Boiúna) e o overclock nunca acelera a recarga. Sozinho morre para flak de área: esconda-o com uma salva pesada logo depois. |

### Arquivos de projétil

> Um arquivo por tipo de míssil e por lançador (`missile_types[].variants[].files`). Dano efetivo = direto + 50% das explosões (convenção do spec).

| Míssil | Codinome | Lançador | HP | Velocidade / acel. / giro | Alcance | Dano explosivo | Efetivo | Arquivos |
|---|---|---|---|---|---|---|---|---|
| Micromíssil | Muriçoca | Tocandira | 380 | 55 / 85 / 300° | 300 m | 1.600 | 800,0 | `bs_msl_box_he` |
| Míssil Alto-Explosivo | Jararaca | Caipora | 1.050 | 45 / 65 / 230° | 400 m | 7.000 | 3.500,0 | `bs_msl_twin_he` |
| Míssil Alto-Explosivo | Jararaca | Mula-sem-Cabeça | 2.200 | 45 / 60 / 200° | 600 m | 7.500 | 3.750,0 | `bs_msl_quad_he` |
| Míssil de Submunições | Piranha | Caipora | 1.050 | 45 / 65 / 230° | 400 m | 6.300 | 3.150,0 | `bs_msl_twin_cluster`, `bs_msl_twin_cluster_child` |
| Míssil de Submunições | Piranha | Mula-sem-Cabeça | 2.200 | 45 / 60 / 200° | 600 m | 13.500 | 6.750,0 | `bs_msl_quad_cluster`, `bs_msl_quad_cluster_child` |
| Míssil Grudento | Carrapato | Caipora | 1.050 | 45 / 65 / 230° | 400 m | 6.500 | 3.500,0 | `bs_msl_twin_limpet`, `bs_msl_twin_limpet_charge` |
| Míssil Grudento | Carrapato | Mula-sem-Cabeça | 2.200 | 45 / 60 / 200° | 600 m | 14.000 | 7.500,0 | `bs_msl_quad_limpet`, `bs_msl_quad_limpet_charge` |
| Micromíssil Incendiário | Taturana-mirim | Tocandira | 380 | 55 / 85 / 300° | 300 m | 600 | 300,0 | `bs_msl_box_napalm` |
| Míssil de Napalm | Taturana | Caipora | 1.050 | 45 / 65 / 230° | 400 m | 3.000 | 1.500,0 | `bs_msl_twin_napalm` |
| Míssil de Napalm | Taturana | Mula-sem-Cabeça | 2.200 | 45 / 60 / 200° | 600 m | 6.000 | 3.000,0 | `bs_msl_quad_napalm` |
| Míssil P.E.M. | Poraquê | Caipora | 1.500 | 45 / 65 / 230° | 400 m | 2.000 | 1.300,0 | `bs_msl_twin_emp` |
| Míssil P.E.M. | Poraquê | Mula-sem-Cabeça | 2.800 | 45 / 60 / 200° | 600 m | 3.000 | 1.900,0 | `bs_msl_quad_emp` |
| Torpedo com Iscas | Boto | Caipora | 4.500 | 30 / 12 / 90° | 400 m | 24.000 | 12.000,0 | `bs_msl_twin_torpedo`, `bs_msl_twin_torpedo_warhead`, `bs_msl_twin_torpedo_decoy` |
| Torpedo com Iscas | Boto | Mula-sem-Cabeça | 6.500 | 30 / 12 / 90° | 600 m | 48.000 | 24.000,0 | `bs_msl_quad_torpedo`, `bs_msl_quad_torpedo_warhead`, `bs_msl_quad_torpedo_decoy` |
| Torpedo Nuclear | Iara | Mula-sem-Cabeça | 6.500 | 30 / 12 / 90° | 600 m | 160.000 | 80.000,0 | `bs_msl_quad_nuclear`, `bs_msl_quad_nuclear_warhead`, `bs_msl_quad_nuclear_decoy` |

### Techs da Carreira

| Tech | Custo | Pré-requisitos | Libera |
|---|---|---|---|
| `rafaeltessaro.bs_msl_box` | 3.500 | `rafaeltessaro.bs_autocannon_20` | Tocandira, Míssil Alto-Explosivo (Muriçoca/Jararaca) |
| `rafaeltessaro.bs_msl_napalm` | 9.000 | `rafaeltessaro.bs_msl_box`, `cosmoteer.factory_thermal` | Míssil de Napalm (Taturana-mirim/Taturana) |
| `rafaeltessaro.bs_msl_twin` | 14.000 | `rafaeltessaro.bs_msl_box`, `cosmoteer.factory_he` | Caipora |
| `rafaeltessaro.bs_msl_cluster` | 16.000 | `rafaeltessaro.bs_msl_twin` | Míssil de Submunições (Piranha) |
| `rafaeltessaro.bs_msl_emp` | 12.000 | `rafaeltessaro.bs_msl_twin`, `cosmoteer.factory_emp` | Míssil P.E.M. (Poraquê) |
| `rafaeltessaro.bs_msl_limpet` | 22.000 | `rafaeltessaro.bs_msl_cluster`, `rafaeltessaro.bs_ammo_aphe` | Míssil Grudento (Carrapato) |
| `rafaeltessaro.bs_msl_torpedo` | 25.000 | `rafaeltessaro.bs_msl_cluster` | Torpedo com Iscas (Boto) |
| `rafaeltessaro.bs_msl_twin-overclock` | 40.000 | `rafaeltessaro.bs_msl_twin`, `cosmoteer.heat_management` | overclock da Caipora |
| `rafaeltessaro.bs_msl_quad` | 150.000 | `rafaeltessaro.bs_msl_torpedo`, `cosmoteer.control_room_large` | Mula-sem-Cabeça |
| `rafaeltessaro.bs_msl_nuclear` | 110.000 | `rafaeltessaro.bs_msl_quad`, `rafaeltessaro.bs_nuclear`, `cosmoteer.factory_nuke` | Torpedo Nuclear (Iara) |
| `rafaeltessaro.bs_msl_quad-overclock` | 160.000 | `rafaeltessaro.bs_msl_quad`, `cosmoteer.heat_management` | overclock da Mula-sem-Cabeça |

No modo **Construir e Batalhar** a Tocandira já vem liberada (lista branca), mas as peças de míssil A.E. e T. dela vêm da tech `rafaeltessaro.bs_bb_bs_msl_box_ammo` (5.000, sempre oferecida), porque o jogo base só libera esses recursos com as techs dos lançadores do jogo base; a Caipora e a Mula-sem-Cabeça são techs de 5.000 (com o overclock à parte), que também liberam as peças de míssil das suas famílias.

## Munições

> Pilha = quanto um tripulante leva por viagem (e cabe num quadro de depósito).

| Recurso | Pilha | Fábrica | Receita por unidade | Quem usa (por unidade) |
|---|---|---|---|---|
| **Munição** (jogo base) | 20 | Fábrica de munição para canhão (jogo base) | - | Marimbondo (20 disparos), Mangangá (10 disparos), Carcará (2 disparos), Tatu (2 explosões aéreas); também é a matéria-prima da Prensa de Carregadores |
| **Carregador Padrão** | 6 | Prensa de Carregadores | 5 munições | Saci (50 disparos), Cigarra (50 disparos), Tambor (2 disparos), Furacão (10 disparos), Trovão (2 carregadores por disparo), Mapinguari (3 carregadores por disparo), Tamanduá (5 explosões aéreas), Pororoca (3 explosões aéreas); matéria-prima de: Prensa de Carregadores Perfurantes, Energizador de Carregadores P.E.M., Fundição de Projéteis Nucleares |
| **Carregador Perfurante** | 4 | Prensa de Carregadores Perfurantes | 1 Carregador Padrão + 0,05 triaço + 0,1 de energia | Cigarra (50 disparos), Tambor (2 disparos), Furacão (10 disparos), Trovão (2 carregadores por disparo), Mapinguari (3 carregadores por disparo) |
| **Carregador P.E.M.** | 4 | Energizador de Carregadores P.E.M. | 1 Carregador Padrão + 0,125 cobre + 0,2 de energia | Cigarra (50 disparos), Tambor (2 disparos), Furacão (10 disparos), Trovão (2 carregadores por disparo), Mapinguari (3 carregadores por disparo) |
| **Célula de Plasma** | 4 | Fábrica de Células de Plasma | 0,5 enxofre + 0,25 bobina + 0,4 de energia | Boitatá (40 disparos), Curupira (2 disparos) |
| **Projétil Nuclear** | 2 | Fundição de Projéteis Nucleares | 0,125 urânio enriquecido + 2 Carregadores Padrão + 0,8 de energia | Boiúna (1 disparo) |

## Fábricas

> Produção sem bônus. Como no jogo base: +25% de velocidade para cada fábrica vizinha e overclock (liberado por tech na Carreira) que multiplica a velocidade em troca de calor.

| Fábrica | Tamanho | Entrada | Saída | Tempo | Produção | Energia | Overclock |
|---|---|---|---|---|---|---|---|
| **Prensa de Carregadores** | 2x2 | 5 munições | 1 Carregador Padrão | 1,25 s | 0,8/s | não usa | 3x mais rápida, 600 MJ/s de calor |
| **Prensa de Carregadores Perfurantes** | 3x3 | 2 Carregadores Padrão + 0,1 triaço | 2 Carregadores Perfurantes | 4 s | 0,5/s | 0,2 por ciclo | 3x mais rápida, 1.100 MJ/s de calor, 1,5x energia por ciclo |
| **Energizador de Carregadores P.E.M.** | 3x3 | 2 Carregadores Padrão + 0,25 cobre | 2 Carregadores P.E.M. | 4 s | 0,5/s | 0,4 por ciclo | 3x mais rápida, 1.100 MJ/s de calor, 1,5x energia por ciclo |
| **Fábrica de Células de Plasma** | 3x3 | 0,5 enxofre + 0,25 bobina | 1 Célula de Plasma | 2 s | 0,5/s | 0,4 por ciclo | 3x mais rápida, 1.100 MJ/s de calor, 1,5x energia por ciclo |
| **Fundição de Projéteis Nucleares** | 3x3 | 0,125 urânio enriquecido + 2 Carregadores Padrão | 1 Projétil Nuclear | 8 s | 0,125/s | 0,8 por ciclo | 3x mais rápida, 1.100 MJ/s de calor, 1,5x energia por ciclo |

**Proporções** (valem com os mesmos bônus dos dois lados: vizinhança e overclock):

- 2 Fábricas de munição para canhão alimentam 1 Prensa de Carregadores (4 munições/s).
- Prensa de Carregadores Perfurantes: consome 0,5 Carregador Padrão/s, ou seja, cada Prensa de Carregadores (0,8/s) abastece 1,6 dessas fábricas.
- Energizador de Carregadores P.E.M.: consome 0,5 Carregador Padrão/s, ou seja, cada Prensa de Carregadores (0,8/s) abastece 1,6 dessas fábricas.
- Fundição de Projéteis Nucleares: consome 0,25 Carregador Padrão/s, ou seja, cada Prensa de Carregadores (0,8/s) abastece 3,2 dessas fábricas.

## Logística por arma

> Fogo contínuo com munição Padrão (nas armas que aceleram, na rotação máxima), sem overclock e sem bônus de fábrica vizinha. Viagens = viagens de tripulação por minuto com a pilha cheia. As fábricas contam a cadeia inteira (munição -> Carregador Padrão -> munição especial); insumos do jogo base (triaço, cobre, enxofre, bobina, urânio enriquecido) ficam de fora.

| Arma | Codinome | Recurso | Disparos por unidade | Consumo | Viagens/min | Fábricas de munição para canhão | Fábricas do Bullet Strike |
|---|---|---|---|---|---|---|---|
| Metralhadora Leve de Convés | **Marimbondo** | Munição | 20 disparos | 0,33/s | 0,97 | 0,16 | - |
| Metralhadora Pesada de Convés | **Mangangá** | Munição | 10 disparos | 0,6/s | 1,8 | 0,3 | - |
| Canhão Automático de Convés 20 mm | **Carcará** | Munição | 2 disparos | 1,25/s | 3,75 | 0,62 | - |
| Flak Leve de Convés | **Tatu** | Munição | 2 explosões aéreas | 1,5/s | 4,5 | 0,75 | - |
| Metralhadora Pesada Quádrupla | **Saci** | Carregador Padrão | 50 disparos | 0,28/s | 2,8 | 0,7 | 0,35 Prensa de Carregadores |
| Minigun de Convés | **Cigarra** | Carregador Padrão | 50 disparos | 0,48/s | 4,8 | 1,2 | 0,6 Prensa de Carregadores |
| Canhão Naval Automático 76 mm | **Tambor** | Carregador Padrão | 2 disparos | 0,83/s | 8,33 | 2,08 | 1,04 Prensa de Carregadores |
| Gatling de Plasma | **Boitatá** | Célula de Plasma | 40 disparos | 0,25/s | 3,75 | - | 0,5 Fábrica de Células de Plasma |
| CIWS de Convés | **Tamanduá** | Carregador Padrão | 5 explosões aéreas | 1/s | 10 | 2,5 | 1,25 Prensa de Carregadores |
| Canhão Rotativo Pesado 30 mm | **Furacão** | Carregador Padrão | 10 disparos | 1,2/s | 12 | 3 | 1,5 Prensa de Carregadores |
| Canhão Naval Duplo 155 mm | **Trovão** | Carregador Padrão | 2 carregadores por disparo | 1,6/s | 16 | 4 | 2 Prensas de Carregadores |
| Canhão de Plasma Pesado | **Curupira** | Célula de Plasma | 2 disparos | 0,75/s | 11,25 | - | 1,5 Fábrica de Células de Plasma |
| Obuseiro Nuclear de Convés | **Boiúna** | Projétil Nuclear | 1 disparo | 0,1/s | 3 | 0,5 | 0,8 Fundição de Projéteis Nucleares, 0,25 Prensa de Carregadores |
| Torre Naval Tripla 406 mm | **Mapinguari** | Carregador Padrão | 3 carregadores por disparo | 3/s | 30 | 7,5 | 3,75 Prensas de Carregadores |
| Bateria Flak Pesada | **Pororoca** | Carregador Padrão | 3 explosões aéreas | 1/s | 10 | 2,5 | 1,25 Prensa de Carregadores |

## Tipos de munição (seletor das armas de meio/fim de jogo)

Armas com seletor: Cigarra, Tambor, Furacão, Trovão, Mapinguari. Perfurante e Perfurante-Explosiva usam o mesmo Carregador Perfurante.

Ao trocar de munição, cada modo continua com o próprio depósito na arma (Perfurante e Perfurante-Explosiva usam o mesmo Carregador Perfurante, mas cada um guarda o seu); a tripulação só reabastece o modo escolhido e nenhum carregador sai como outro tipo. Para testar, monte a nave sem "Reabastecer todos os recursos" e sem recursos cheios, porque os dois enchem os depósitos de **todos** os tipos na arma. Se o depósito P.E.M. já estiver cheio, o certo é a arma atirar P.E.M. desse depósito e os Carregadores Padrão continuarem no depósito deles.

| Tipo | Carregador | Para que serve |
|---|---|---|
| **Padrão** | Carregador Padrão | Munição versátil. Os canhões disparam granadas explosivas que estouram no impacto. |
| **Perfurante** | Carregador Perfurante | Penetradores endurecidos que atravessam blindagem (a blindagem resiste só 60% do normal) e destroem o que está atrás, com metade do dano em cada peça depois da primeira. Fracos contra escudos. |
| **Perfurante-Explosiva** | Carregador Perfurante | Atravessa uma ou duas placas de blindagem e então detona DENTRO do casco inimigo. |
| **P.E.M.** | Carregador P.E.M. | Cada acerto drena a energia de escudos e peças energizadas. Menos dano ao casco, mas ótima contra naves que dependem de energia e escudos. |
