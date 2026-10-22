# Bullet Strike 2.0: armas, munições, fábricas e logística

> Gerado por `tools/make_docs.py` a partir de `tools/spec/` (spec 2.0) e da camada de dados `tools/bs_data.py`, com os switches do build. Não edite à mão.

> **[2.0 de TESTE]** Números do build de teste (versão 2.0.0). A versão final só sai depois do [checklist](CHECKLIST_2_0.md).
>
> **Balanço:** Balanceado para jogar com o Star Wars: A Cosmos Divided; sem ele as armas do início e do meio do jogo ficam ~2-3x mais fortes por tile que as do jogo base.

**Convenções.** DPS no casco = tiros por segundo x (dano direto + metade da explosão). Escudo por segundo = dano no escudo + 2,5 x o dreno de bateria (o escudo do SW gasta 0,4 de bateria por ponto). Sem overclock, salvo quando dito. "Por tile" = dividido pelos quadrados da peça. Custos em créditos.

## Índice

- [Canhões](#canhões)
- [Munições](#munições)
- [Defesas](#defesas)
- [Linha PEM](#linha-pem)
- [Railgun Tupã](#railgun-tupã)
- [Lança-mísseis](#lança-mísseis)
- [Fábricas](#fábricas)
- [Paióis](#paióis)
- [Fita de Alimentação](#fita-de-alimentação)
- [Limites por nave](#limites-por-nave)
- [Techs da Carreira](#techs-da-carreira)
- [Balanço contra o SW:ACD](#balanço-contra-o-swacd)
- [Logística por tipo de munição](#logística-por-tipo-de-munição)
- [Efeitos visuais](#efeitos-visuais)

## Canhões

Só precisam de tripulação e munição: nenhum usa energia. Cada tipo de munição tem o seu estoque dentro da arma; trocar o tipo nunca joga fora o que já está lá. A tripulação reabastece a arma quando ela cai abaixo da metade (com a Fita, os paióis abastecem antes).

### Início de jogo

| Codinome | Arma | Calibre | Tamanho | Tripulação | Comando | Vida | Custo | Alcance | DPS HE (casco) | Munições | Overclock |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Marimbondo** | Metralhadora Leve de Convés | 7,62 mm | 1x1 | 1 | 1 | 4.000 | 2.000 | 360 m | 720 | HE/AP | - |
| **Mangangá** | Metralhadora Pesada de Convés | 12,7 mm | 1x2 | 1 | 2 | 6.000 | 3.600 | 380 m | 1.440 | HE/AP | - |
| **Carcará** | Canhão Automático de Convés 20 mm | 20 mm | 2x2 | 1 | 3 | 10.000 | 4.800 | 380 m | 1.650 | HE/AP/SAP | - |

### Meio de jogo

| Codinome | Arma | Calibre | Tamanho | Tripulação | Comando | Vida | Custo | Alcance | DPS HE (casco) | Munições | Overclock |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Saci** | Metralhadora Pesada Quádrupla | 12,7 mm x4 | 2x2 | 2 | 4 | 10.000 | 6.000 | 420 m | 2.100 | HE/AP | Redemoinho |
| **Cigarra** | Minigun de Convés | 7,62 mm rotativa | 2x3 | 2 | 5 | 14.000 | 10.000 | 420 m | 3.288 | HE/AP | Bafo de Dragão |
| **Tambor** | Canhão Naval Automático 76 mm | 76 mm | 3x4 | 3 | 7 | 24.000 | 15.000 | 450 m | 5.400 | HE/AP/SAP/AC | Salva Rápida |
| **Boitatá** | Gatling de Plasma | plasma (rotativa) | 2x3 | 2 | 5 | 13.000 | 13.050 | 420 m | 2.800 | Plasma | Sobrecarga |

### Fim de jogo

| Codinome | Arma | Calibre | Tamanho | Tripulação | Comando | Vida | Custo | Alcance | DPS HE (casco) | Munições | Overclock |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Furacão** | Canhão Rotativo Pesado 30 mm | 30 mm rotativo | 4x4 | 4 | 10 | 32.000 | 23.000 | 520 m | 6.804 | HE/AP/SAP | Vendaval |
| **Trovão** | Canhão Naval Duplo 155 mm | 155 mm | 4x5 | 5 | 12 | 40.000 | 28.000 | 560 m | 8.800 | HE/AP/SAP/AC | Supercarga |
| **Mapinguari** | Torre Naval Tripla 406 mm | 406 mm | 6x7 | 7 | 16 | 84.000 | 102.000 | 620 m | 12.000 | HE/AP/SAP/AC | Bordada Total |
| **Boiúna** | Obuseiro Pesado de Convés (AC) | obuseiro 380 mm | 5x6 | 5 | 10 | 54.000 | 48.500 | 600 m | 7.200 | HE/AC | Bote da Boiúna |
| **Curupira** | Canhão de Plasma Pesado | plasma (pesado) | 4x5 | 4 | 12 | 38.000 | 34.500 | 580 m | 7.485 | Plasma | Erupção Solar |

- **Aceleram enquanto atiram:** Cigarra, Furacão e Boitatá (começam devagar e chegam à cadência máxima em alguns segundos).
- **Atordoam a tripulação perto da torre ao disparar:** Tambor, Trovão, Mapinguari e Boiúna (mais forte com overclock).
- **Híbrida:** Saci também derruba mísseis, minas e projéteis no modo Defender.
- **Boiúna:** obuseiro pesado; a AC dele é guiada (ligada neste build) e cada disparo gasta 1,5 carregador.
- **Canhões de Encouraçado:** Mapinguari e Boiúna somados, no máximo 2 por nave.

## Munições

- **HE (Alto-Explosivo)** - Carregador HE: Munição padrão. Dano direto e, do 20 mm para cima, uma carga explosiva onde o projétil para. Barata (Prensa HE).
- **AP (Perfurante)** - Carregador AP: Menos dano, muito mais penetração: atravessa blindagem e os escudos-bolha pequenos (e médios a partir do 76 mm) do SW. Sem carga explosiva.
- **SAP (Semiperfurante)** - Carregador SAP: Meio-termo: penetra o dobro do HE e explode por dentro com meia carga. Só em armas com carga explosiva (20 mm para cima).
- **AC (Alta Capacidade)** - Carregador AC: Munição premium (não nuclear): +50% de dano direto, carga explosiva dobrada com raio 1,5x e +60% no escudo. Cara (cerca de 4x o HE). Só meio e fim de jogo, do 76 mm para cima.
- **FRAG (Nuvem de Fragmentos)** - Carregador FRAG: Só defesas. Espoleta programada (tipo AHEAD): explosão central menor e um cone de fragmentos de tungstênio que varre o corredor de chegada dos mísseis atrás do alvo. Melhor contra enxames e salvas; contra lasers vale o mesmo que a munição padrão.

"Peça seguinte" = dano em cada peça que a granada atravessa depois da primeira. HE e AC: 50 % do dano direto (como os turbolasers do SW). AP e SAP: fator do switch `guns.ap_further_factor` = sem_reducao.

| Arma | Tipo | Dano direto | Explosão (raio) | Penetração | Peça seguinte | Casco/s | Escudo/s | Por unidade | Estoque (tempo de tiro) |
|---|---|---|---|---|---|---|---|---|---|
| Marimbondo | HE | 90 | - | 2 | 45 | 720 | 720 | 75 disparos | 7 (66 s) |
| Marimbondo | AP | 63 | - | 6 | 9 | 504 | 432 | 75 disparos | 7 (66 s) |
| Mangangá | HE | 180 | - | 2 | 90 | 1.440 | 1.440 | 40 disparos | 12 (60 s) |
| Mangangá | AP | 126 | - | 7 | 19 | 1.008 | 864 | 40 disparos | 12 (60 s) |
| Carcará | HE | 600 | 120 (1 m) | 3 | 300 | 1.650 | 1.650 | 10 disparos | 15 (60 s) |
| Carcará | AP | 462 | - | 10 | 37 | 1.155 | 990 | 10 disparos | 15 (60 s) |
| Carcará | SAP | 531 | 60 (1 m) | 6 | 64 | 1.402 | 1.320 | 10 disparos | 15 (60 s) |
| Saci | HE | 150 | - | 2 | 75 | 2.100 | 2.100 | 45 disparos | 19 (61 s) |
| Saci | AP | 105 | - | 7 | 16 | 1.470 | 1.260 | 45 disparos | 19 (61 s) |
| Cigarra | HE | 137 | - | 2 | 68 | 3.288 | 3.288 | 50 disparos | 29 (60 s) |
| Cigarra | AP | 96 | - | 8 | 14 | 2.304 | 1.968 | 50 disparos | 29 (60 s) |
| Tambor | HE | 2.160 | 2.160 (2 m) | 3,5 | 1.080 | 5.400 | 5.400 | 2 disparos | 50 (60 s) |
| Tambor | AP | 2.268 | - | 20 | 113 | 3.780 | 3.240 | 2 disparos | 50 (60 s) |
| Tambor | SAP | 2.214 | 1.080 (1,5 m) | 7 | 266 | 4.590 | 4.320 | 2 disparos | 50 (60 s) |
| Tambor | AC | 3.240 | 4.320 (3 m) | 3,5 | 1.620 | 9.000 | 8.640 | 2 disparos | 50 (60 s) |
| Furacão | HE | 450 | 234 (1 m) | 3 | 225 | 6.804 | 6.804 | 18 disparos | 50 (75 s) |
| Furacão | AP | 397 | - | 12 | 32 | 4.764 | 4.080 | 18 disparos | 50 (75 s) |
| Furacão | SAP | 423 | 117 (1 m) | 6,5 | 51 | 5.778 | 5.448 | 18 disparos | 50 (75 s) |
| Trovão | HE | 7.000 | 8.000 (3 m) | 6 | 3.500 | 8.800 | 8.800 | 1 disparo | 60 (75 s) |
| Trovão | AP | 7.700 | - | 24 | 385 | 6.160 | 5.280 | 1 disparo | 60 (75 s) |
| Trovão | SAP | 7.350 | 4.000 (2,25 m) | 12 | 882 | 7.480 | 7.040 | 1 disparo | 60 (75 s) |
| Trovão | AC | 10.500 | 16.000 (4,5 m) | 6 | 5.250 | 14.800 | 14.080 | 1 disparo | 60 (75 s) |
| Mapinguari | HE | 7.200 | 9.600 (4,5 m) | 8 | 3.600 | 12.000 | 12.000 | 1 disparo | 75 (75 s) |
| Mapinguari | AP | 8.400 | - | 30 | 420 | 8.400 | 7.200 | 1 disparo | 75 (75 s) |
| Mapinguari | SAP | 7.800 | 4.800 (3,38 m) | 15 | 936 | 10.200 | 9.600 | 1 disparo | 75 (75 s) |
| Mapinguari | AC | 10.800 | 19.200 (6,75 m) | 8 | 5.400 | 20.400 | 19.200 | 1 disparo | 75 (75 s) |
| Boiúna | HE | 3.000 | 30.000 (5,5 m) | 0 | - | 7.200 | 7.200 | 1,5 carregador por disparo | 63 (105 s) |
| Boiúna | AC | 4.500 | 60.000 (8,25 m) | 0 | - | 13.800 | 11.520 | 1,5 carregador por disparo | 63 (105 s) |
| Boitatá | Plasma | 280 | - | 0 | - | 2.800 | 5.750 | 40 disparos | 15 (60 s) |
| Curupira | Plasma | 4.990 | - | 0 | - | 7.485 | 15.405 | 3 disparos | 38 (76 s) |

## Defesas

Tatu, Tamanduá e Pororoca só defendem: não atacam naves. Cada rajada leva duas cargas separadas: uma contra mísseis, minas e projéteis e outra, só contra os disparos laser e os tiros iônicos (os turbolasers e íons do SW:ACD). A munição FRAG (Nuvem de Fragmentos) estoura uma carga menor e solta fragmentos que varrem o caminho dos mísseis; contra lasers ela vale o mesmo que a HE.

| Codinome | Defesa | Tamanho | Tripulação | Alcance | Rajadas/s | HE: contra mísseis e projéteis | FRAG: central + fragmentos | Contra lasers e íons | Por segundo (anti-tiro / anti-laser) | Overclock |
|---|---|---|---|---|---|---|---|---|---|---|
| **Tatu** | Flak Leve de Convés | 2x2 | 1 | 180 m | 3 | 3.200 (3 m) | 1.600 (2 m) + 12 x 260 | 2.000 (4 m) | 9.600 / 6.000 | - |
| **Tamanduá** | CIWS de Convés | 3x3 | 2 | 250 m | 5 | 4.400 (4,5 m) | 2.200 (3 m) + 16 x 280 | 3.000 (6 m) | 22.000 / 15.000 | Barragem |
| **Pororoca** | Bateria Flak Pesada | 4x4 | 4 | 320 m | 3 | 16.900 (7 m) | 8.000 (5 m) + 24 x 420 | 8.000 (9 m) | 50.700 / 24.000 | Muralha de Flak |

**Contra o SW:ACD.** Contra mísseis, minas e balas: Tatu 1,15x, Tamanduá 1,17x e Pororoca 1,15x a defesa equivalente do SW. Contra os lasers e íons do SW: Tatu 0,72x, Tamanduá 0,80x e Pororoca 0,55x (decisão da Fase B; `guns.defesa_antilaser` = fase_b; a opção `banda` leva a 1,15x). As balas de até 30 mm não podem ser derrubadas por defesas (como o canhão de repetição do jogo base).

## Linha PEM

Canhões que disparam granadas PEM e drenam a bateria do escudo atingido, com pouco dano no casco. São o par dos canhões de íons do SW:ACD (Treme-Treme e Corisco: 1,17-1,19x os íons do SW). O overclock do escudo não corta esse dreno pela metade. Usam uma munição só, a Célula PEM, feita na F3 só com cobre.

| Codinome | Arma | Tamanho | Montagem | Tripulação | Comando | Alcance | Tiros/s | Escudo por acerto | Escudo/s | Escudo/s por comando | Casco/s | Células/s | Estoque | Overclock |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Tuvira** | Canhão PEM Leve | 1x2 | torre 270° (180°/s), 2 canos | 1 | 2 | 380 m | 1,44 | 3.000 | 4.320 | 2.160 | 216 | 0,36 | 22 células (61 s) | - |
| **Treme-Treme** | Canhão PEM Médio | 2x2 | torre 300° (45°/s) | 2 | 5 | 440 m | 0,52 | 12.000 | 6.250 | 1.250 | 130 | 0,52 | 32 células (61 s) | Choque Contínuo |
| **Corisco** | Canhão PEM Pesado | 4x4 | torre 270° (22°/s), 2 canos | 3 | 10 | 520 m | 0,97 | 18.000 | 17.476 | 1.748 | 388 | 0,97 | 73 células (75 s) | Relâmpago |

**Escada.** Por arma: Tuvira 4.320 < Treme-Treme 6.250 < Corisco 17.476 de escudo por segundo. Por ponto de comando: Tuvira 2.160, Treme-Treme 1.250, Corisco 1.748 (`pem.tuvira_cp` = 2).

**Corisco com overclock (Relâmpago).** O tiro atravessa peças com energia e drena por 10 s: 9.500 de escudo na hora + 34.000 ao longo do tempo (43.500 por acerto), alcance 650 m.

Tempo para derrubar uma bolha de escudo cheia, sem recarga:

| Arma | bolha pequena do SW (5.000) | bolha média do SW (20.000) | bolha grande do SW (80.000) | bolha gigante do SW (320.000) | bolha pequena do jogo base (15.000) | bolha grande do jogo base (45.000) |
|---|---|---|---|---|---|---|
| Tuvira | 1,2 s | 4,6 s | 18,5 s | 74,1 s | 3,5 s | 10,4 s |
| Treme-Treme | 0,8 s | 3,2 s | 12,8 s | 51,2 s | 2,4 s | 7,2 s |
| Corisco | 0,3 s | 1,1 s | 4,6 s | 18,3 s | 0,9 s | 2,6 s |

Contra os íons do SW:

| Arma | Âncora do SW | Escudo/s | Por comando | Na banda 1,10-1,25 |
|---|---|---|---|---|
| Tuvira | Dual Mounted Ion Cannon, Compact Edition | 0,67x | 0,67x | não (escolha) |
| Treme-Treme | Medium Ion Cannon | 1,19x | 1,43x | sim |
| Corisco | Heavy Ion Cannon | 1,17x | 1,40x | sim |

A Tuvira virou torre de 270° a pedido: o arco paga a cadência, e ela fica abaixo da âncora fixa do SW por arma.

## Railgun Tupã

Fixa e modular, como o canhão eletromagnético (railgun) do jogo base: **Carregador do Tupã** 5x5 + 1 a 6 **Canos do Tupã** 3x3 + **Ponta do Tupã** 3x4. Os canos encaixam no meio da borda de cima do carregador e a Ponta no último cano; com 0 ou mais de 6 canos a Ponta não atira.

- **Mais canos = mais dano, alcance, penetração, velocidade e energia por tiro:** m(N) = 1 + 0,25 x N^0,85; N = canos 1..6.
- **Comando:** 6 + 2 por cano. Tripulação: 2 no carregador.
- **Energia:** sai da bateria do carregador (15 de energia): 2,5 por tiro com 1 cano até 5 com 6 (os mesmos números das dicas do jogo). A tripulação leva bateria ao carregador.
- **Ritmo:** 1 tiro a cada 6 s. Estoque: 12 projéteis no carregador + 1 na câmara = 13 tiros (78 s).
- **Tranco:** um impulso por tiro na ponta (3.000 com 1 cano até 5.152 com 6), tremor de tela 0,2 por 0,7 s, anel de choque azul e recuo animado da ponta, dos canos e da culatra. Fora do centro da nave ela gira um pouco, como o canhão eletromagnético do jogo base.
- **Passa por cima da própria nave:** o dardo não acerta peças nossas.
- **Limite:** 2 por nave (a Ponta conta), à parte do limite do Mapinguari e da Boiúna.
- **Visual:** tudo azul elétrico (carregador, canos, dardo, rastro, impacto); só as brasas que ficam queimando no alvo são laranja.

| Canos | Tiles | Comando | Custo | Dano por tiro | DPS | DPS por tile | Penetração | Alcance | Velocidade | Energia por tiro | Tiros com a bateria cheia, sem recarga | Impulso do tranco | F6 por 1000 DPS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 46 | 8 | 54.750 | 50.000 | 8.333 | 181 | 32,5 | 500 m | 550 m/s | 2,5 | 6 | 3.000 | 0,72 |
| 2 | 55 | 10 | 66.250 | 58.025 | 9.671 | 176 | 37,7 | 580 m | 638 m/s | 3 | 5 | 3.482 | 0,62 |
| 3 | 64 | 12 | 77.750 | 65.442 | 10.907 | 170 | 42,5 | 654 m | 720 m/s | 3,5 | 4 | 3.927 | 0,55 |
| 4 | 73 | 14 | 89.250 | 72.490 | 12.082 | 166 | 47,1 | 700 m | 797 m/s | 4 | 4 | 4.349 | 0,50 |
| 5 | 82 | 16 | 100.750 | 79.276 | 13.213 | 161 | 51,5 | 700 m | 872 m/s | 4,5 | 3 | 4.757 | 0,45 |
| 6 | 91 | 18 | 112.250 | 85.859 | 14.310 | 157 | 55,8 | 700 m | 944 m/s | 5 | 3 | 5.152 | 0,42 |

Com 1 ou 2 canos a logística (0,72 / 0,62 tile de F6 por 1000 DPS) fica acima da banda do fim (0,4 a 0,6); de 3 canos em diante fica dentro.

**Contra o SW.** Por tiro: 1,67x (1 cano) a 2,86x (6) o Dual 70TT Superheavy Turbolaser do SW. Por tile: 0,51 a 0,45x a linha tardia do SW: o carregador 5x5 é o preço. Se ficar fraco, dá para atirar a cada 5,4 s em vez de 6 s (checklist 10.4).

## Lança-mísseis

Projeto completo em [MISSEIS_PROJETO.md](MISSEIS_PROJETO.md).

| Codinome | Lançador | Fase | Tamanho | Tripulação | Comando | Vida | Custo | Tipos | Alcance | Overclock | Limite |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Tocandira** | Caixa de Micromísseis de Convés | início | 2x2 | 1 | 2 | 9.000 | 5.200 | HE | 600 m | - | - |
| **Caipora** | Lançador Duplo de Mísseis de Convés | meio | 3x3 | 2 | 8 | 16.000 | 20.000 | HE / Submunição / PEM | 800 m | Fúria da Caipora | - |
| **Mula-sem-Cabeça** | Bateria Pesada de Mísseis Quádrupla | fim | 5x6 | 8 | 22 | 54.000 | 95.000 | HE / Submunição / PEM / Nuclear | 1.000 m | Estouro da Boiada | 2 por nave |

**Contra o SW.** Os lançadores do SW pagam em peças de míssil e tripulação carregando, então a conta é a densidade do sistema (lançador + fábrica + tripulação, por tile): 1,15-1,24x o lançador do SW com a Fita ou o paiol acoplado; só com a tripulação, sem acoplamento: 0,78-0,96x.

## Fábricas

Etapa única, sem tripulante (a tripulação só leva a matéria-prima e a energia), com overclock (3x mais rápido, esquentando).

**Vizinhança ligada, como no jogo base:** +25 % por fábrica vizinha (do Bullet Strike ou do jogo base). Os intervalos do Bullet Strike foram multiplicados por 1,5: sozinha a fábrica é mais lenta, e com 2 vizinhas ela volta ao ritmo do projeto.

| Código | Fábrica | Tamanho | Entra por ciclo | Sai por ciclo | Ritmo: sozinha / 1 vizinha / 2 vizinhas | Com overclock (sozinha) | Bateria por ciclo |
|---|---|---|---|---|---|---|---|
| F1 | Prensa HE | 2x2 | 0,25 enxofre | Carregador HE | 1,88 s / 1,5 s / 1,25 s | 0,62 s | 200 |
| F2 | Fábrica de Munição Especial | 4x3 | 0,25 enxofre + 0,05 triaço | Carregador AP | 0,94 s / 0,75 s / 0,62 s | 0,31 s | 300 |
| F2 | Fábrica de Munição Especial | 4x3 | 0,25 enxofre + 0,025 triaço | Carregador SAP | 0,78 s / 0,62 s / 0,52 s | 0,26 s | 250 |
| F2 | Fábrica de Munição Especial | 4x3 | 0,5 enxofre + 0,1 triaço | Carregador AC (Alta Capacidade) | 2,5 s / 2 s / 1,67 s | 0,83 s | 500 |
| F2 | Fábrica de Munição Especial | 4x3 | 0,3 enxofre + 0,025 triaço | Carregador FRAG (Nuvem de Fragmentos) | 0,78 s / 0,62 s / 0,52 s | 0,26 s | 250 |
| F3 | Fábrica de Células | 3x3 | 0,5 enxofre + 0,25 bobina | Célula de Plasma | 3 s / 2,4 s / 2 s | 1 s | 400 |
| F3 | Fábrica de Células | 3x3 | 0,125 cobre | Célula PEM | 1,35 s / 1,08 s / 0,9 s | 0,45 s | 500 |
| F4 | Fábrica de Mísseis | 3x3 | 0,1 ferro + 0,1 enxofre | 2 x Carga de Míssil HE | 0,45 s / 0,36 s / 0,3 s | 0,15 s | 120 |
| F4 | Fábrica de Mísseis | 3x3 | 0,2 ferro + 0,1 enxofre | 2 x Carga de Míssil de Submunição | 0,54 s / 0,43 s / 0,36 s | 0,18 s | 160 |
| F4 | Fábrica de Mísseis | 3x3 | 0,1 ferro + 0,05 enxofre | Carga de Míssil PEM | 0,54 s / 0,43 s / 0,36 s | 0,18 s | 200 |
| F5 | Fábrica de Ogivas Nucleares | 4x4 | 0,4 ferro + 0,16 urânio | Ogiva Nuclear | 4,5 s / 3,6 s / 3 s | 1,5 s | 2.700 |
| F6 | Forja de Projéteis | 3x4 | 0,25 triaço + 0,1 hiperbobina | Projétil de Railgun | 4,5 s / 3,6 s / 3 s | 1,5 s | 500 |

Modos (botão da fábrica): F2 (AP/SAP/AC/FRAG, começa em AP), F3 (Plasma/PEM) e F4 (HE/Submunição/PEM). A placa do teto mostra o modo; a F3 em PEM acende o banco PEM só produzindo. Entradas: F1 enxofre; F2 enxofre + triaço; F3 enxofre + bobina (Plasma) e cobre (PEM); F4 ferro + enxofre; F5 ferro + urânio; F6 triaço + hiperbobina.

## Paióis

Quatro famílias, de 1x1 a 3x3. O tipo é escolhido no botão do paiol; cada tipo tem o seu estoque (trocar o tipo não apaga nada, e o paiol continua empurrando o que já tinha para as armas daquele tipo). Barra sob a vida + medidor no teto (5 / 8 / 10 níveis) + placa do tipo; sem contador de números nesta versão. Cheio, explode; vazio, quase não.

No build com a Fita os paióis são selados (sem porta): só a Fita põe e tira munição. Na reserva sem Fita eles têm portas, a tripulação entra e um paiol encostado atrás da arma (ou embaixo da saída da fábrica) passa a munição sozinho.

| Paiol | Tamanho | Vida | Capacidade por tipo | Empurra por tipo | Custo |
|---|---|---|---|---|---|
| Paiol de Cartuchos 1x1 | 1x1 | 3.000 | HE 60, AP 40, SAP 50, AC 30, FRAG 60 | 10/s | 12 aço + 2 bobina |
| Paiol de Cartuchos 2x2 | 2x2 | 12.000 | HE 276, AP 184, SAP 230, AC 138, FRAG 276 | 20/s | 44 aço + 6 bobina + 2 triaço |
| Paiol de Cartuchos 3x3 | 3x3 | 27.000 | HE 702, AP 468, SAP 585, AC 351, FRAG 702 | 40/s | 96 aço + 12 bobina + 6 triaço |
| Paiol de Células 1x1 | 1x1 | 3.000 | Plasma 40, PEM 40 | 10/s | 12 aço + 2 bobina |
| Paiol de Células 2x2 | 2x2 | 12.000 | Plasma 184, PEM 184 | 20/s | 44 aço + 6 bobina + 2 triaço |
| Paiol de Células 3x3 | 3x3 | 27.000 | Plasma 468, PEM 468 | 40/s | 96 aço + 12 bobina + 6 triaço |
| Paiol de Mísseis 1x1 | 1x1 | 3.000 | HE 100, Submunição 100, PEM 100, Ogiva 20 | 20/s | 12 aço + 2 bobina |
| Paiol de Mísseis 2x2 | 2x2 | 12.000 | HE 460, Submunição 460, PEM 460, Ogiva 92 | 40/s | 44 aço + 6 bobina + 2 triaço |
| Paiol de Mísseis 3x3 | 3x3 | 27.000 | HE 1.170, Submunição 1.170, PEM 1.170, Ogiva 234 | 80/s | 96 aço + 12 bobina + 6 triaço |
| Paiol de Projéteis 1x1 | 1x1 | 3.000 | Projétil 20 | 10/s | 12 aço + 2 bobina |
| Paiol de Projéteis 2x2 | 2x2 | 12.000 | Projétil 92 | 10/s | 44 aço + 6 bobina + 2 triaço |
| Paiol de Projéteis 3x3 | 3x3 | 27.000 | Projétil 234 | 20/s | 96 aço + 12 bobina + 6 triaço |

## Fita de Alimentação

Grude do lado de uma fábrica, paiol ou arma do Bullet Strike: a máquina entra na rede da fita e a munição passa sozinha entre elas, de um canto ao outro da nave (teletransporte, sem caminho e sem tripulação). A luz verde acende quando está grudada. Uma fita encostada em duas máquinas liga as duas.

- **Peça:** 1x1, vida 1.500, custo 4 aço + 1 bobina. Grude de lado (não na quina) na máquina; uma Fita encostada em duas máquinas liga as duas.
- **Fábrica → paiol (jeito B):** a fábrica com Fita manda cada unidade pronta para os paióis com Fita que aceitam aquele tipo, em qualquer lugar da nave. Sem paiol com Fita ela não manda nada e a grade de saída fica para a tripulação, como no jogo base.
- **Paiol → arma (empurra):** o paiol com Fita empurra cada tipo que guarda para as armas com Fita naquele tipo (a vazão por tipo está na coluna "Empurra por tipo" dos paióis).
- **Um tipo nunca vira outro:** o paiol de HE só recebe HE e a arma só recebe o tipo escolhido no botão.
- **Reserva da tripulação (metade):** a tripulação continua levando munição para a arma que cair abaixo da metade (de uma Baia ou de munição comprada).
- **Alcance:** a nave inteira (`logistics.fita_alcance` = 1000); se o jogo ficar lento, dá para trocar para ~12 quadrados.
- **O que se vê:** a luz verde da Fita grudada, o ícone da Fita na máquina ligada, a barra do paiol e cartuchos saindo de uma peça e entrando na outra.
- **Não atravessa para outra nave:** se a nave se partir, cada pedaço fica com os seus paióis.

## Limites por nave

- **Canhões de Encouraçado** (Mapinguari e Boiúna somados): no máximo 2 por nave.
- **Baterias de Mísseis Nucleares** (Mula-sem-Cabeça): no máximo 2 por nave.
- **Railguns Tupã** (Ponta do Tupã): no máximo 2 por nave.

## Techs da Carreira

Pré-requisitos do jogo base aparecem pelo ID (`cosmoteer.*`). No modo Construir e Batalhar as peças vêm liberadas pela lista branca do mod.

| Tech | Nível | Custo | Pré-requisitos | Libera |
|---|---|---|---|---|
| Marimbondo | 1 | 2.000 | - | Marimbondo, Mangangá e Prensa HE |
| Logística de Munição | 1 | 3.000 | Marimbondo | Paiol de Cartuchos 1x1, Paiol de Cartuchos 2x2 e Fita de Alimentação |
| Carcará | 1 | 2.500 | Marimbondo | Carcará |
| Tatu | 1 | 3.000 | Marimbondo | Tatu |
| Tocandira | 1 | 3.500 | Carcará | Tocandira, Fábrica de Mísseis, Paiol de Mísseis 1x1 e Paiol de Mísseis 2x2 |
| Tuvira | 1 | 3.500 | Marimbondo | Tuvira, Fábrica de Células, Paiol de Células 1x1, Paiol de Células 2x2 e célula PEM |
| Saci | 2 | 6.000 | Logística de Munição e Tatu | Saci |
| Cigarra | 2 | 9.000 | Logística de Munição | Cigarra |
| Tambor | 2 | 12.000 | Logística de Munição e `cosmoteer.cannon_large` | Tambor |
| Tamanduá | 2 | 10.000 | Tatu e Logística de Munição | Tamanduá |
| Fábrica de Munição Especial | 2 | 8.000 | Logística de Munição | Fábrica de Munição Especial e munição AP |
| Munição Semiperfurante (SAP) | 2 | 12.000 | Fábrica de Munição Especial | munição SAP |
| Munição Nuvem de Fragmentos (FRAG) | 2 | 10.000 | Fábrica de Munição Especial e Tamanduá | munição FRAG |
| Boitatá | 2 | 16.000 | Cigarra | Boitatá, Fábrica de Células, Paiol de Células 1x1 e Paiol de Células 2x2 |
| Caipora | 2 | 14.000 | Tocandira | Caipora |
| Míssil de Submunição (Piranha) | 2 | 16.000 | Caipora | míssil Piranha |
| Míssil PEM | 2 | 12.000 | Caipora | míssil Poraquê |
| Paiol Pesado | 2 | 12.000 | Logística de Munição e Tambor | Paiol de Cartuchos 3x3, Paiol de Células 3x3 e Paiol de Mísseis 3x3 |
| Treme-Treme | 2 | 10.000 | Tuvira e Logística de Munição | Treme-Treme |
| Overclock: Saci | 3 | 30.000 | Saci e `cosmoteer.heat_management` | overclock: Saci |
| Overclock: Cigarra | 3 | 35.000 | Cigarra e `cosmoteer.heat_management` | overclock: Cigarra |
| Overclock: Tambor | 3 | 40.000 | Tambor e `cosmoteer.heat_management` | overclock: Tambor |
| Overclock: Boitatá | 3 | 40.000 | Boitatá e `cosmoteer.heat_management` | overclock: Boitatá |
| Overclock: Tamanduá | 3 | 45.000 | Tamanduá e `cosmoteer.heat_management` | overclock: Tamanduá |
| Trovão | 3 | 40.000 | Tambor e `cosmoteer.cannon_deck` | Trovão |
| Furacão | 3 | 35.000 | Cigarra e `cosmoteer.chaingun` | Furacão |
| Pororoca | 3 | 35.000 | Tamanduá e `cosmoteer.flak_cannon_large` | Pororoca |
| Curupira | 3 | 50.000 | Boitatá e Trovão | Curupira |
| Munição Alta Capacidade (AC) | 3 | 30.000 | Munição Semiperfurante (SAP) e Tambor | munição AC |
| Overclock: Prensa HE | 3 | 20.000 | Marimbondo e `cosmoteer.heat_management` | overclock: Prensa HE |
| Overclock: Fábrica de Munição Especial | 3 | 75.000 | Fábrica de Munição Especial e `cosmoteer.heat_management` | overclock: Fábrica de Munição Especial |
| Overclock: Fábrica de Células | 3 | 75.000 | Tuvira e `cosmoteer.heat_management` | overclock: Fábrica de Células |
| Overclock: Fábrica de Mísseis | 3 | 60.000 | Tocandira e `cosmoteer.heat_management` | overclock: Fábrica de Mísseis |
| Overclock: Caipora | 3 | 40.000 | Caipora e `cosmoteer.heat_management` | overclock: Caipora |
| Overclock: Treme-Treme | 3 | 30.000 | Treme-Treme e `cosmoteer.heat_management` | overclock: Treme-Treme |
| Corisco | 3 | 45.000 | Treme-Treme e Trovão | Corisco |
| Mapinguari | 4 | 150.000 | Trovão e `cosmoteer.control_room_large` | Mapinguari |
| Boiúna | 4 | 90.000 | Trovão e Munição Alta Capacidade (AC) | Boiúna |
| Railgun Tupã | 4 | 200.000 | Trovão e Munição Alta Capacidade (AC) | Carregador do Tupã, Cano do Tupã, Ponta do Tupã, Forja de Projéteis, Paiol de Projéteis 1x1, Paiol de Projéteis 2x2 e Paiol de Projéteis 3x3 |
| Mula-sem-Cabeça | 4 | 150.000 | Míssil de Submunição (Piranha) e `cosmoteer.control_room_large` | Mula-sem-Cabeça |
| Fábrica de Ogivas Nucleares | 4 | 110.000 | Mula-sem-Cabeça | Fábrica de Ogivas Nucleares e míssil Iara |
| Overclock: Furacão | 4 | 90.000 | Furacão e `cosmoteer.heat_management` | overclock: Furacão |
| Overclock: Trovão | 4 | 100.000 | Trovão e `cosmoteer.heat_management` | overclock: Trovão |
| Overclock: Curupira | 4 | 110.000 | Curupira e `cosmoteer.heat_management` | overclock: Curupira |
| Overclock: Pororoca | 4 | 90.000 | Pororoca e `cosmoteer.heat_management` | overclock: Pororoca |
| Overclock: Mapinguari | 4 | 160.000 | Mapinguari e `cosmoteer.heat_management` | overclock: Mapinguari |
| Overclock: Boiúna | 4 | 100.000 | Boiúna e `cosmoteer.heat_management` | overclock: Boiúna |
| Overclock: Mula-sem-Cabeça | 4 | 160.000 | Mula-sem-Cabeça e `cosmoteer.heat_management` | overclock: Mula-sem-Cabeça |
| Overclock: Corisco | 4 | 90.000 | Corisco e `cosmoteer.heat_management` | overclock: Corisco |
| Overclock: Fábrica de Ogivas Nucleares | 4 | 150.000 | Fábrica de Ogivas Nucleares e `cosmoteer.heat_management` | overclock: Fábrica de Ogivas Nucleares |
| Overclock: Forja de Projéteis | 4 | 120.000 | Railgun Tupã e `cosmoteer.heat_management` | overclock: Forja de Projéteis |

## Balanço contra o SW:ACD

Alvo: cada arma do Bullet Strike bate ~15 % mais que a equivalente do SW no mesmo nível (banda 1,10-1,25x), no casco e no escudo. Em troca, a arma custa logística: fábricas, paióis e estoque.

| Grupo | Arma | Bullet Strike | Âncora do SW | Razão |
|---|---|---|---|---|
| canhão | Marimbondo | 720 casco/s | Compact Roof-Mounted Laser Cannon | 1,15x |
| canhão | Mangangá | 1.440 casco/s | Compact Turbolaser - Burst | 1,15x |
| canhão | Carcará | 1.650 casco/s | média de Light Turbolaser (1.053) e Medium Turbolaser (1.818) | 1,15x |
| canhão | Saci | 2.100 casco/s | Medium Turbolaser | 1,16x |
| canhão | Cigarra | 3.288 casco/s | Medium Turbolaser por tile x 6 | 1,20x |
| canhão | Tambor | 5.400 casco/s | média de Medium Turbolaser (455 por tile) e Triple Turbolaser (333 por tile) x 12 | 1,14x |
| canhão | Furacão | 6.804 casco/s | média de CIS ZS Heavy Turbolaser (6.087) e Imperial Heavy Turbolaser (5.220) | 1,20x |
| canhão | Trovão | 8.800 casco/s | média dos turbolasers pesados de facção (5.650) x 20/16 | 1,25x |
| canhão | Mapinguari | 12.000 casco/s | Dual 70TT Superheavy Turbolaser (4.800) | 2,50x; por tile 0,81x |
| canhão | Boiúna | 7.200 casco/s | Dual 70TT Superheavy Turbolaser (4.800) | 1,50x |
| plasma | Boitatá | 2.800 casco / 5.750 escudo | Medium Turbolaser por tile x 6 / Medium Ion Cannon | 1,03x / 1,09x; por tile 0,73x |
| plasma | Curupira | 7.485 casco / 15.405 escudo | média dos turbolasers pesados de facção x 20/16 / Heavy Ion Cannon | 1,06x / 1,03x; por tile 0,82x |
| defesa | Tatu | 9.600 anti-tiro/s | Sentinel-Class Light Point Defense Turbolaser (8.333 anti-tiro/s) | 1,15x (lasers 0,72x) |
| defesa | Tamanduá | 22.000 anti-tiro/s | Sentinel-Class Light Point Defense Turbolaser por tile x 9 | 1,17x (lasers 0,80x) |
| defesa | Pororoca | 50.700 anti-tiro/s | Heavy Flak Deck Cannon (2.750 por tile) x 16 | 1,15x (lasers 0,55x) |
| PEM | Tuvira | 4.320 escudo/s | Dual Mounted Ion Cannon, Compact Edition | 0,67x |
| PEM | Treme-Treme | 6.250 escudo/s | Medium Ion Cannon | 1,19x |
| PEM | Corisco | 17.476 escudo/s | Heavy Ion Cannon | 1,17x |
| míssil | Caipora Poraquê | 14.207 escudo/s | íons do SW por tile | 1,20x |
| míssil | Mula-sem-Cabeça Poraquê | 32.876 escudo/s | íons do SW por tile | 1,17x |
| railgun | Tupã, 1 cano | 50.000 por tiro | Dual 70TT Superheavy Turbolaser (30.000 por tiro) | 1,67x por tiro; 0,51x por tile |
| railgun | Tupã, 4 canos | 72.490 por tiro | Dual 70TT Superheavy Turbolaser (30.000 por tiro) | 2,42x por tiro; 0,47x por tile |
| railgun | Tupã, 6 canos | 85.859 por tiro | Dual 70TT Superheavy Turbolaser (30.000 por tiro) | 2,86x por tiro; 0,45x por tile |

- **Fora da banda de propósito:** Mapinguari e Boiúna (sem par do SW desse tamanho; 2 somados por nave).
- **Plasma abaixo da banda por regra:** por tile, Boitatá 0,73x e Curupira 0,82x os íons do SW; e o overclock de escudo corta o plasma pela metade. O anti-escudo do Bullet Strike é a linha PEM.

### Fora do alvo do balanço

O alvo do balanço é o casco do SW (1 durasteel + interior), que o teste T3 mede. Fora dele ainda sobra:

- **AP das metralhadoras:** até 1,12x o HE (Cigarra) em blindagem do jogo base ou casco sem blindagem; não é medido (no casco do SW elas param na durasteel e ficam em 0,70x).
- **AP e SAP dos canhões grandes fora do casco do SW:** em blindagem do jogo base o HE perde a explosão ao atravessar, e o AP chega a 3,09x o HE (Mapinguari); o SAP, a 2,07x.
- **HE do Mapinguari:** no modelo, com o interior do jogo base, o que entra depois da primeira peça fica 1,70x o do turbolaser do SW (o Trovão, 1,49x; o limite é 1,5x). Vale até o teste T3 responder (checklist 10.1).

## Logística por tipo de munição

Tiles de fábrica do Bullet Strike para sustentar 1000 de dano (ou escudo) por segundo em fogo contínuo. Banda: 0,6 a 0,9 no início e no meio, 0,4 a 0,6 no fim. A banda conta só as fábricas do Bullet Strike no ritmo do projeto, que é o de uma fábrica com 2 vizinhas (a vizinhança está ligada e os intervalos foram multiplicados por 1,5; sozinha, multiplique por 1,5); refinados (triaço, bobina, hiperbobina) comprados ou feitos fora. A coluna "com refino" soma o refino do jogo base. Overclock: um terço.

| Arma | Tipo | Por segundo | Fábrica | Tiles por 1000 | Com refino | Banda | Situação |
|---|---|---|---|---|---|---|---|
| Marimbondo | HE | 720 casco | F1 | 0,74 | 0,74 | 0,6-0,9 | na banda |
| Marimbondo | AP | 504 casco | F2 | 1,59 | 2,10 | 0,6-0,9 | acima (munição cara) |
| Mangangá | HE | 1.440 casco | F1 | 0,69 | 0,69 | 0,6-0,9 | na banda |
| Mangangá | AP | 1.008 casco | F2 | 1,49 | 1,96 | 0,6-0,9 | acima (munição cara) |
| Carcará | HE | 1.650 casco | F1 | 0,76 | 0,76 | 0,6-0,9 | na banda |
| Carcará | AP | 1.155 casco | F2 | 1,62 | 2,14 | 0,6-0,9 | acima (munição cara) |
| Carcará | SAP | 1.402 casco | F2 | 1,11 | 1,33 | 0,6-0,9 | acima (munição cara) |
| Saci | HE | 2.100 casco | F1 | 0,74 | 0,74 | 0,6-0,9 | na banda |
| Saci | AP | 1.470 casco | F2 | 1,59 | 2,10 | 0,6-0,9 | acima (munição cara) |
| Cigarra | HE | 3.288 casco | F1 | 0,73 | 0,73 | 0,6-0,9 | na banda |
| Cigarra | AP | 2.304 casco | F2 | 1,56 | 2,06 | 0,6-0,9 | acima (munição cara) |
| Tambor | HE | 5.400 casco | F1 | 0,77 | 0,77 | 0,6-0,9 | na banda |
| Tambor | AP | 3.780 casco | F2 | 1,65 | 2,18 | 0,6-0,9 | acima (munição cara) |
| Tambor | SAP | 4.590 casco | F2 | 1,13 | 1,35 | 0,6-0,9 | acima (munição cara) |
| Tambor | AC | 9.000 casco | F2 | 1,85 | 2,30 | 0,6-0,9 | acima (munição cara) |
| Furacão | HE | 6.804 casco | F1 | 0,49 | 0,49 | 0,4-0,6 | na banda |
| Furacão | AP | 4.764 casco | F2 | 1,05 | 1,39 | 0,4-0,6 | acima (munição cara) |
| Furacão | SAP | 5.778 casco | F2 | 0,72 | 0,86 | 0,4-0,6 | acima (munição cara) |
| Trovão | HE | 8.800 casco | F1 | 0,46 | 0,46 | 0,4-0,6 | na banda |
| Trovão | AP | 6.160 casco | F2 | 0,97 | 1,29 | 0,4-0,6 | acima (munição cara) |
| Trovão | SAP | 7.480 casco | F2 | 0,67 | 0,80 | 0,4-0,6 | acima (munição cara) |
| Trovão | AC | 14.800 casco | F2 | 1,08 | 1,34 | 0,4-0,6 | acima (munição cara) |
| Mapinguari | HE | 12.000 casco | F1 | 0,42 | 0,42 | 0,4-0,6 | na banda |
| Mapinguari | AP | 8.400 casco | F2 | 0,89 | 1,18 | 0,4-0,6 | acima (munição cara) |
| Mapinguari | SAP | 10.200 casco | F2 | 0,61 | 0,73 | 0,4-0,6 | acima (munição cara) |
| Mapinguari | AC | 20.400 casco | F2 | 0,98 | 1,22 | 0,4-0,6 | acima (munição cara) |
| Boiúna | HE | 7.200 casco | F1 | 0,42 | 0,42 | 0,4-0,6 | na banda |
| Boiúna | AC | 13.800 casco | F2 | 0,87 | 1,08 | 0,4-0,6 | acima (munição cara) |
| Boitatá | Plasma | 5.750 escudo | F3 | 0,78 | 0,93 | 0,6-0,9 | na banda |
| Curupira | Plasma | 15.405 escudo | F3 | 0,58 | 0,69 | 0,4-0,6 | na banda |
| Tatu | HE | 9.600 anti-tiro | F1 | 0,20 | 0,20 | 0,6-0,9 | - |
| Tatu | FRAG | 14.160 anti-tiro | F2 | 0,17 | 0,20 | 0,6-0,9 | - |
| Tamanduá | HE | 22.000 anti-tiro | F1 | 0,19 | 0,19 | 0,6-0,9 | - |
| Tamanduá | FRAG | 33.400 anti-tiro | F2 | 0,16 | 0,19 | 0,6-0,9 | - |
| Pororoca | HE | 50.700 anti-tiro | F1 | 0,10 | 0,10 | 0,4-0,6 | - |
| Pororoca | FRAG | 54.240 anti-tiro | F2 | 0,12 | 0,14 | 0,4-0,6 | - |
| Tuvira | PEM | 4.320 escudo | F3 | 0,68 | 0,68 | 0,6-0,9 | na banda |
| Treme-Treme | PEM | 6.250 escudo | F3 | 0,68 | 0,68 | 0,6-0,9 | na banda |
| Corisco | PEM | 17.476 escudo | F3 | 0,45 | 0,45 | 0,4-0,6 | na banda |
| Tocandira | HE | 1.815 casco | F4 | 0,68 | 0,68 | 0,6-0,9 | na banda |
| Caipora | HE | 6.486 casco | F4 | 0,75 | 0,75 | 0,6-0,9 | na banda |
| Caipora | Submunição | 7.147 casco | F4 | 0,81 | 0,81 | 0,6-0,9 | na banda |
| Caipora | PEM | 14.207 escudo | F4 | 0,63 | 0,63 | 0,6-0,9 | na banda |
| Mula-sem-Cabeça | HE | 18.929 casco | F4 | 0,50 | 0,50 | 0,4-0,6 | na banda |
| Mula-sem-Cabeça | Submunição | 20.814 casco | F4 | 0,50 | 0,50 | 0,4-0,6 | na banda |
| Mula-sem-Cabeça | PEM | 32.876 escudo | F4 | 0,51 | 0,51 | 0,4-0,6 | na banda |
| Mula-sem-Cabeça | Nuclear | 11.496 casco | F5 | 0,42 | 0,42 | 0,4-0,6 | na banda |
| Tupã N=1 | Projétil, 1 cano | 8.333 casco | F6 | 0,72 | 1,06 | 0,4-0,6 | acima de propósito (canos curtos) |
| Tupã N=2 | Projétil, 2 canos | 9.671 casco | F6 | 0,62 | 0,92 | 0,4-0,6 | acima de propósito (canos curtos) |
| Tupã N=3 | Projétil, 3 canos | 10.907 casco | F6 | 0,55 | 0,81 | 0,4-0,6 | na banda |
| Tupã N=4 | Projétil, 4 canos | 12.082 casco | F6 | 0,50 | 0,73 | 0,4-0,6 | na banda |
| Tupã N=5 | Projétil, 5 canos | 13.213 casco | F6 | 0,45 | 0,67 | 0,4-0,6 | na banda |
| Tupã N=6 | Projétil, 6 canos | 14.310 casco | F6 | 0,42 | 0,62 | 0,4-0,6 | na banda |

AP pede ~2x mais fábrica por dano que o HE, SAP ~1,5x e AC ~2,4x: é o preço de trocar dano por penetração (AP e SAP) ou por alfa (AC).

## Efeitos visuais

Só visual: nada de dano, alcance ou cadência muda. O tamanho segue o calibre. As balas pequenas são traçantes na cor da munição; do 76 mm para cima são granadas 3D futuristas. O brilho grande dos projéteis aparece só no espaço (o casco branco não fica lavado). Escalas em relação ao efeito do jogo base (1 = tamanho do jogo).

Cores: HE âmbar; AP branco-azulado; SAP laranja; AC carmim com faixa dourada; FRAG verde-água.

| Arma | Calibre | Em voo | Clarão de boca | Tremor (disparo / impacto) |
|---|---|---|---|---|
| Marimbondo | 7,62 mm | traçante | x0,42 | 0 / 0 |
| Cigarra | 7,62 mm rotativa | traçante | x0,5 (OC x0,6) | 0 / 0 |
| Mangangá | 12,7 mm | traçante | x0,6 | 0 / 0 |
| Saci | 12,7 mm x4 | traçante | x0,6 (OC x0,75) | 0 / 0 |
| Carcará | 20 mm | traçante | x0,85 | 0,01 / 0 |
| Furacão | 30 mm rotativo | traçante | x1,15 (OC x1,45) | 0,015 / 0 |
| Tambor | 76 mm | granada 3D | x0,65 (OC x0,8) | 0,05 / 0,05 |
| Trovão | 155 mm | granada 3D | x1 (OC x1,25) | 0,12 / 0,15 |
| Mapinguari | 406 mm | granada 3D + fumaça | x1,6 (OC x2) | 0,12 / 0,25 |
| Boiúna | obuseiro 380 mm | granada 3D + fumaça | x1,65 | 0,3 / 0,3 |
| Tatu | 40 mm | explode no ar | x0,6 | 0 / 0 |
| Tamanduá | 35 mm | explode no ar | x0,7 (OC x0,85) | 0 / 0 |
| Pororoca | 57 mm | explode no ar | x1,1 (OC x1,3) | 0 / 0,03 |

Mísseis: cada tipo tem arte 3D própria, luzes e escapamento na cor do tipo: Jararaca (âmbar), Piranha (amarelo), Poraquê (azul) e Iara (verde). A Piranha solta as pétalas do nariz ao abrir; a Iara tem o trevo de radiação e a explosão nuclear verde.
