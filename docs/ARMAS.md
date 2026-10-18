# Bullet Strike: armas, munições e fábricas

> Gerado automaticamente por `tools/make_docs.py` a partir de `tools/spec/bullet_strike_spec.json`.
> DPS = dano por segundo com munição padrão, sem overclock (explosões contam inteiras).

## Início de jogo

| Arma | Codinome | Tamanho | Tripulação | Alcance | DPS | Munição | Overclock |
|---|---|---|---|---|---|---|---|
| **Metralhadora Leve de Convés** | Marimbondo | 1x1 | 1 | 220 m | 260 | Munição avulsa (vanilla) | - |
| **Metralhadora Pesada de Convés** | Mangangá | 1x2 | 1 | 240 m | 540 | Munição avulsa (vanilla) | - |
| **Canhão Automático de Convés 20 mm** | Carcará | 2x2 | 1 | 250 m | 1.000 | Munição avulsa (vanilla) | - |
| **Flak Leve de Convés** | Tatu | 2x2 | 1 | 180 m | 3.000/s contra projéteis | Munição avulsa (vanilla) | - |

## Meio de jogo

| Arma | Codinome | Tamanho | Tripulação | Alcance | DPS | Munição | Overclock |
|---|---|---|---|---|---|---|---|
| **Metralhadora Pesada Quádrupla** | Saci | 2x2 | 2 | 300 m | 1.330 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Minigun de Convés** | Cigarra | 2x3 | 2 | 300 m | 2.040 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Canhão Naval Automático 76 mm** | Tambor | 3x4 | 3 | 340 m | 3.750 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Gatling de Plasma** | Boitatá | 2x3 | 2 | 320 m | 1.600 | Células de plasma | sim |
| **CIWS de Convés** | Tamanduá | 3x3 | 2 | 250 m | 10.000/s contra projéteis | Carregador padrão | sim |

## Fim de jogo

| Arma | Codinome | Tamanho | Tripulação | Alcance | DPS | Munição | Overclock |
|---|---|---|---|---|---|---|---|
| **Canhão Rotativo Pesado 30 mm** | Furacão | 4x4 | 4 | 500 m | 6.000 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Canhão Naval Duplo 155 mm** | Trovão | 4x5 | 5 | 520 m | 7.600 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Canhão de Plasma Pesado** | Curupira | 4x5 | 4 | 550 m | 5.400 | Células de plasma | sim |
| **Obuseiro Nuclear de Convés** | Boiúna | 5x6 | 6 | 600 m | 8.000 | Projéteis nucleares | sim |
| **Torre Naval Tripla 406 mm** | Mapinguari | 6x7 | 10 | 600 m | 16.000 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Bateria Flak Pesada** | Pororoca | 4x4 | 4 | 320 m | 12.000/s contra projéteis | Carregador padrão | sim |

## Mísseis de convés

> Projeto completo em `docs/MISSEIS_PROJETO.md` (spec `tools/spec/bullet_strike_missiles.json`). Gerado por `tools/bsgen/launchers.py` e `tools/bsgen/shots.py`.

**Como funciona (igual nos três lançadores):** a tripulação leva as peças de míssil do jogo base até um paiol interno por família (A.E., térmica, PEM, nuclear). Um autocarregador passa um míssil por vez do paiol para as células visíveis, **só com tripulação no posto**. Com o rack cheio sai a salva em sequência (a última célula carregada dispara primeiro); depois a recarga recomeça. Trocar o tipo de míssil custa uma recarga completa do tipo novo; com o paiol vazio, o rack parcial dispara mesmo assim. Sem energia. Carregado, o lançador explode junto com o estoque quando pega fogo ou é destruído.

### Lançadores

| Lançador | Codinome | Fase | Tamanho | Trip. | CP | Vida | Custo | Salva HE | Ciclo HE | Alcance | DPS efetivo/tile (OC) | Overclock | Limite |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Caixa de Micromísseis de Convés** | Tocandira | Início | 2x2 | 1 | 2 | 8.000 | 3.100 cr | 12 em 0,733 s | 9,073 s | 300 m | 264,5 (381,4) | Enxame Furioso (desligado) | - |
| **Lançador de Mísseis de Convés de Casulo Duplo** | Caipora | Meio | 3x3 | 2 | 5 | 12.000 | 12.600 cr | 16 em 2 s | 18,96 s | 400 m | 328,2 (467,6) | Fúria da Caipora | - |
| **Bateria Pesada de Mísseis Quádrupla** | Mula-sem-Cabeça | Fim | 5x6 | 8 | 18 | 42.000 | 77.000 cr | 48 em 3,133 s | 15,805 s | 600 m | 379,6 (518,1) | Estouro da Boiada | 2 por nave (vaga nuclear, com a Boiúna) |

### Modos de cada lançador

> Ciclo = recarga do rack inteiro + salva. Paiol = capacidade da família, em peças. OC = ciclo com overclock (recarga ÷ 1,5; PEM ÷ 1,2; o nuclear nunca acelera).

| Lançador | Míssil | Células | Peças por míssil | Recarga por célula | Salva | Ciclo (OC) | DPS efetivo/tile | Paiol | Descarte em OC |
|---|---|---|---|---|---|---|---|---|---|
| Tocandira | Micromíssil (Muriçoca) | 6 cassetes | 0,5 peça de míssil A.E. | 1,39 s | 12 em 0,733 s | 9,073 s | 264,5 | 12 | - |
| Tocandira | Micromíssil Incendiário (Taturana-mirim) | 6 cassetes | 0,5 peça de míssil T.C. | 1,39 s | 12 em 0,733 s | 9,073 s | 99,2 | 12 | - |
| Caipora | Míssil Alto-Explosivo (Jararaca) | 16 | 2 peças de míssil A.E. | 1,06 s | 16 em 2 s | 18,96 s (13,307 s) | 328,2 | 64 | 2 peças/salva |
| Caipora | Míssil de Submunições (Transformer) (Piranha) | 16 | 2 peças de míssil A.E. | 1,06 s | 16 em 2 s | 18,96 s (13,307 s) | 295,4 | 64 | 2 peças/salva |
| Caipora | Míssil Grudento (Carrapato) | 16 | 2 peças de míssil A.E. | 1,06 s | 16 em 2 s | 18,96 s (13,307 s) | 328,2 | 64 | 2 peças/salva |
| Caipora | Míssil de Napalm (Taturana) | 16 | 2 peças de míssil T.C. | 1,06 s | 16 em 2 s | 18,96 s (13,307 s) | 140,6 | 64 | 2 peças/salva |
| Caipora | Míssil PEM (Poraquê) | 16 | 2 peças de míssil PEM | 1,06 s | 16 em 2 s | 18,96 s (16,133 s) | 121,9 | 64 | 2 peças/salva |
| Caipora | Torpedo com Iscas (Boto) | 2 | 6 peças de míssil A.E. | 4,65 s | 2 em 0,133 s | 9,433 s (6,333 s) | 282,7 | 64 | - |
| Mula-sem-Cabeça | Míssil Alto-Explosivo (Jararaca) | 48 | 2 peças de míssil A.E. | 0,264 s | 48 em 3,133 s | 15,805 s (11,581 s) | 379,6 | 192 | 6 peças/salva |
| Mula-sem-Cabeça | Míssil de Submunições (Transformer) (Piranha) | 16 | 4 peças de míssil A.E. | 0,6 s | 16 em 1 s | 10,6 s (7,4 s) | 339,6 | 192 | 4 peças/salva |
| Mula-sem-Cabeça | Míssil Grudento (Carrapato) | 16 | 4 peças de míssil A.E. | 0,6 s | 16 em 1 s | 10,6 s (7,4 s) | 377,4 | 192 | 4 peças/salva |
| Mula-sem-Cabeça | Míssil de Napalm (Taturana) | 16 | 4 peças de míssil T.C. | 0,6 s | 16 em 1 s | 10,6 s (7,4 s) | 150,9 | 192 | 4 peças/salva |
| Mula-sem-Cabeça | Míssil PEM (Poraquê) | 16 | 3 peças de míssil PEM | 0,6 s | 16 em 1 s | 10,6 s (9 s) | 95,6 | 96 | 3 peças/salva |
| Mula-sem-Cabeça | Torpedo com Iscas (Boto) | 4 | 12 peças de míssil A.E. | 2,37 s | 4 em 0,2 s | 9,68 s (6,52 s) | 330,6 | 192 | - |
| Mula-sem-Cabeça | Torpedo Nuclear (Iara) | 2 | 8 peças de míssil nuclear | 9,97 s | 2 em 0,067 s | 20,007 s (sem OC) | 266,6 | 32 | - |

### Tipos de míssil (seletor do lançador)

| # | Codinome | Míssil | Recurso | Lançadores | O que faz |
|---|---|---|---|---|---|
| 0 | **Jararaca** | Míssil Alto-Explosivo | peça de míssil A.E. | Tocandira, Caipora, Mula-sem-Cabeça | Ogiva alto-explosiva rápida e direta: o míssil de referência. Salvas grandes saturam a defesa de ponto. |
| 1 | **Piranha** | Míssil de Submunições (Transformer) | peça de míssil A.E. | Caipora, Mula-sem-Cabeça | Abre a 25 m do casco inimigo (ou no impacto, ou no fim do voo) e solta um cardume de minimísseis que se espalham por várias peças. Abatido antes de abrir, não solta nada. |
| 2 | **Carrapato** | Míssil Grudento | peça de míssil A.E. | Caipora, Mula-sem-Cabeça | Gruda no casco e explode 2,5 s depois, com alta chance de matar a tripulação que vier consertar. Abatido no voo, se perde; num escudo só estoura. |
| 3 | **Taturana** | Míssil de Napalm | peça de míssil T.C. | Tocandira, Caipora, Mula-sem-Cabeça | Explosão pequena, fogo garantido na peça atingida e calor em volta que continua acendendo incêndios. Inútil contra blindagem; extintor e espuma são o contra. |
| 4 | **Poraquê** | Míssil PEM | peça de míssil PEM | Caipora, Mula-sem-Cabeça | Drena baterias e escudos em área e continua drenando as peças com energia por alguns segundos. As armas do Bullet Strike não usam bateria e são imunes. |
| 5 | **Boto** | Torpedo com Iscas | peça de míssil A.E. | Caipora, Mula-sem-Cabeça | Torpedo lento e resistente: 1,5 s depois do lançamento a ogiva se separa no meio de iscas que gastam a defesa de ponto e a flak. |
| 6 | **Iara** | Torpedo Nuclear | peça de míssil nuclear | Mula-sem-Cabeça | Só na bateria pesada. Conta no limite nuclear (2 por nave, junto com a Boiúna) e o overclock nunca acelera a recarga. Sozinho morre para flak de área: esconda-o com uma salva pesada logo depois. |

### Arquivos de projétil

> Um arquivo por tipo de míssil e por lançador (`missile_types[].variants[].files`). Dano efetivo = direto + 50 % das explosões (convenção do spec).

| Míssil | Codinome | Lançador | HP | Velocidade / acel. / giro | Alcance | Dano explosivo | Efetivo | Arquivos |
|---|---|---|---|---|---|---|---|---|
| Micromíssil | Muriçoca | Tocandira | 380 | 55 / 85 / 300° | 300 m | 1.600 | 800,0 | `bs_msl_box_he` |
| Míssil Alto-Explosivo | Jararaca | Caipora | 1.050 | 45 / 65 / 230° | 400 m | 7.000 | 3.500,0 | `bs_msl_twin_he` |
| Míssil Alto-Explosivo | Jararaca | Mula-sem-Cabeça | 2.200 | 45 / 60 / 200° | 600 m | 7.500 | 3.750,0 | `bs_msl_quad_he` |
| Míssil de Submunições (Transformer) | Piranha | Caipora | 1.050 | 45 / 65 / 230° | 400 m | 6.300 | 3.150,0 | `bs_msl_twin_cluster`, `bs_msl_twin_cluster_child` |
| Míssil de Submunições (Transformer) | Piranha | Mula-sem-Cabeça | 2.200 | 45 / 60 / 200° | 600 m | 13.500 | 6.750,0 | `bs_msl_quad_cluster`, `bs_msl_quad_cluster_child` |
| Míssil Grudento | Carrapato | Caipora | 1.050 | 45 / 65 / 230° | 400 m | 6.500 | 3.500,0 | `bs_msl_twin_limpet`, `bs_msl_twin_limpet_charge` |
| Míssil Grudento | Carrapato | Mula-sem-Cabeça | 2.200 | 45 / 60 / 200° | 600 m | 14.000 | 7.500,0 | `bs_msl_quad_limpet`, `bs_msl_quad_limpet_charge` |
| Micromíssil Incendiário | Taturana-mirim | Tocandira | 380 | 55 / 85 / 300° | 300 m | 600 | 300,0 | `bs_msl_box_napalm` |
| Míssil de Napalm | Taturana | Caipora | 1.050 | 45 / 65 / 230° | 400 m | 3.000 | 1.500,0 | `bs_msl_twin_napalm` |
| Míssil de Napalm | Taturana | Mula-sem-Cabeça | 2.200 | 45 / 60 / 200° | 600 m | 6.000 | 3.000,0 | `bs_msl_quad_napalm` |
| Míssil PEM | Poraquê | Caipora | 1.500 | 45 / 65 / 230° | 400 m | 2.000 | 1.300,0 | `bs_msl_twin_emp` |
| Míssil PEM | Poraquê | Mula-sem-Cabeça | 2.800 | 45 / 60 / 200° | 600 m | 3.000 | 1.900,0 | `bs_msl_quad_emp` |
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
| `rafaeltessaro.bs_msl_emp` | 12.000 | `rafaeltessaro.bs_msl_twin`, `cosmoteer.factory_emp` | Míssil PEM (Poraquê) |
| `rafaeltessaro.bs_msl_limpet` | 22.000 | `rafaeltessaro.bs_msl_cluster`, `rafaeltessaro.bs_ammo_aphe` | Míssil Grudento (Carrapato) |
| `rafaeltessaro.bs_msl_torpedo` | 25.000 | `rafaeltessaro.bs_msl_cluster` | Torpedo com Iscas (Boto) |
| `rafaeltessaro.bs_msl_twin-overclock` | 40.000 | `rafaeltessaro.bs_msl_twin`, `cosmoteer.heat_management` | overclock da Caipora |
| `rafaeltessaro.bs_msl_quad` | 150.000 | `rafaeltessaro.bs_msl_torpedo`, `cosmoteer.control_room_large` | Mula-sem-Cabeça |
| `rafaeltessaro.bs_msl_nuclear` | 110.000 | `rafaeltessaro.bs_msl_quad`, `rafaeltessaro.bs_nuclear`, `cosmoteer.factory_nuke` | Torpedo Nuclear (Iara) |
| `rafaeltessaro.bs_msl_quad-overclock` | 160.000 | `rafaeltessaro.bs_msl_quad`, `cosmoteer.heat_management` | overclock da Mula-sem-Cabeça |

No **Build & Battle** a Tocandira já vem liberada (lista branca) e a Caipora e a Mula-sem-Cabeça são techs de 5000 (com o overclock à parte), que também liberam as peças de míssil das suas famílias.

## Munições

| Recurso | Pilha por tile | Observação |
|---|---|---|
| **Carregador Padrão** | 6 | 1 magazine = 50 MG-round equivalents (MGR) = 5 cannon ammo (Magazine Press, power-free). Quad HMG and minigun 50 rounds; 30 mm rotary 10; 76 mm 2 shells; CIWS 5 triple-airburst salvos' worth = 5 airbursts; heavy flak 3 airbursts; 155 mm 2 magazines per shell; 406 mm 3 magazines per shell; nuclear shell casing 2. Stack 6 => one crew trip = 300 MGR (1.5x a trip of loose ammo). Also the input of the AP/EMP presses and the nuclear foundry (chain bullet -> Standard -> special). |
| **Carregador Perfurante** | 4 | Same shot counts as the Standard Magazine; feeds selector modes AP (1) AND APHE (2). Pressed from 1 Standard Magazine + 0.05 tristeel (1.5x the cost). Stack 4 => special ammo needs 1.5x the crew trips of Standard. Stripe colour white/orange. |
| **Carregador EMP** | 4 | Same shot counts as the Standard Magazine; feeds selector mode EMP (3). Charged from 1 Standard Magazine + 0.125 copper + 200 battery. Stack 4. Stripe colour blue. |
| **Célula de Plasma** | 4 | Boitatá gatling: 40 bolts per cell (InlineResourceConverter 1:40). Curupira heavy cannon: 2 bolts per cell (1:2). Recipe 0.5 sulfur + 0.25 coil + 400 battery. Stack 4. |
| **Projétil Nuclear** | 2 | 1 shell = 1 Boiúna shot. Recipe 0.125 enriched uranium (1:8 splitter) + 2 Standard Magazines (casing/propellant). Stack 2 => every crew trip carries 2 shells. Cooks off when its storage is destroyed. |

## Fábricas

| Fábrica | Entrada | Saída | Tempo | Energia |
|---|---|---|---|---|
| **Prensa de Carregadores** | 5 munição | 1 Carregador Padrão | 1.25 s | não usa |
| **Prensa de Carregadores Perfurantes** | 2 Carregador Padrão + 0.1 tri-aço | 2 Carregador Perfurante | 4 s | 0.2 bateria/ciclo |
| **Carregadora de Carregadores EMP** | 2 Carregador Padrão + 0.25 cobre | 2 Carregador EMP | 4 s | 0.4 bateria/ciclo |
| **Fábrica de Células de Plasma** | 0.5 enxofre + 0.25 bobina | 1 Célula de Plasma | 2 s | 0.4 bateria/ciclo |
| **Fundição de Projéteis Nucleares** | 0.125 urânio enriquecido + 2 Carregador Padrão | 1 Projétil Nuclear | 8 s | 0.8 bateria/ciclo |

## Tipos de munição (seletor das armas de meio/fim de jogo)

| Tipo | Para que serve |
|---|---|
| **Padrão** | Munição versátil. Os canhões disparam granadas explosivas que estouram no impacto. |
| **Perfurante** | Penetradores endurecidos que atravessam blindagem (a blindagem conta pela metade) e destroem o que está atrás. Fracos contra escudos. |
| **Perfurante-Explosiva** | Atravessa uma ou duas placas de blindagem e então detona DENTRO do casco inimigo. |
| **EMP** | Cada acerto drena bateria de escudos e partes energizadas. Menos dano ao casco, mas ótima contra naves que dependem de energia e escudos. |
