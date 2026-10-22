# Lança-mísseis de convés do Bullet Strike 2.0

> Gerado por `tools/make_docs.py` a partir de `tools/spec/` (spec 2.0) e da camada de dados `tools/bs_data.py`, com os switches do build. Não edite à mão.

> **[2.0 de TESTE]** Números do build de teste. O que testar está nas seções 6 e 11 do [checklist](CHECKLIST_2_0.md).

## 1. Em um parágrafo

Três lançadores de convés, um por fase: **Tocandira, Caipora e Mula-sem-Cabeça**. Cada um carrega cargas de míssil feitas na Fábrica de Mísseis (e ogivas nucleares na Fábrica de Ogivas), guardadas num depósito por tipo dentro do lançador. Um autocarregador passa as cargas para as células visíveis, só com tripulação no posto; com todas as células cheias sai a salva em sequência e a recarga recomeça. O tipo é escolhido no botão do lançador. Sem energia: o custo é a logística (fábrica, paiol e Fita).

## 2. Os lançadores

| Codinome | Lançador | Fase | Tamanho | Tripulação | Comando | Vida | Custo | Overclock | Limite |
|---|---|---|---|---|---|---|---|---|---|
| **Tocandira** | Caixa de Micromísseis de Convés | início | 2x2 | 1 | 2 | 9.000 | 5.200 | sem overclock | - |
| **Caipora** | Lançador Duplo de Mísseis de Convés | meio | 3x3 | 2 | 8 | 16.000 | 20.000 | Fúria da Caipora | - |
| **Mula-sem-Cabeça** | Bateria Pesada de Mísseis Quádrupla | fim | 5x6 | 8 | 22 | 54.000 | 95.000 | Estouro da Boiada | 2 por nave |

### Modos

Estoque = 1 salva nas células + 4 salvas no depósito. Ciclo = recarga de todas as células + salva.

| Lançador | Míssil | Por salva | Cargas | Recarga por célula | Entre um míssil e outro | Dano | Alcance | Depósito (cargas) | Overclock na recarga |
|---|---|---|---|---|---|---|---|---|---|
| Tocandira | Muriçoca (HE) | 12 | 1 carga = 2 mísseis | 0,98 s | 0,13 s | 1.815 casco/s | 600 m | 24 | - |
| Caipora | Jararaca (HE) | 16 | 2 cargas por míssil | 0,43 s | 0,13 s | 6.486 casco/s | 800 m | 128 | ÷1,5 |
| Caipora | Piranha (Submunição) | 8 | 4 cargas por míssil | 1 s | 0,13 s | 7.147 casco/s | 800 m | 128 | ÷1,5 |
| Caipora | Poraquê (PEM) | 16 | 2 cargas por míssil | 0,6 s | 0,13 s | 14.207 escudo/s | 800 m | 128 | ÷1,2 |
| Mula-sem-Cabeça | Jararaca (HE) | 48 | 2 cargas por míssil | 0,22 s | 0,07 s | 18.929 casco/s | 1.000 m | 384 | ÷1,3 |
| Mula-sem-Cabeça | Piranha (Submunição) | 8 | 10 cargas por míssil | 1,44 s | 0,13 s | 20.814 casco/s | 1.000 m | 320 | ÷1,3 |
| Mula-sem-Cabeça | Poraquê (PEM) | 16 | 3 cargas por míssil | 0,52 s | 0,07 s | 32.876 escudo/s | 1.000 m | 192 | ÷1,15 |
| Mula-sem-Cabeça | Iara (Nuclear) | 2 | 1 carga por míssil | 9,97 s | 0,07 s | 11.496 casco/s | 1.000 m | 8 | - |

## 3. Os mísseis

### HE: Jararaca (e Muriçoca na Tocandira)

| Lançador | Míssil | Explosão | Raio | Vida do míssil | Alcance | Por salva |
|---|---|---|---|---|---|---|
| Tocandira | Muriçoca | 2.000 | 1,75 m | 1.300 | 600 m | 12 |
| Caipora | Jararaca | 7.200 | 3 m | 2.000 | 800 m | 16 |
| Mula-sem-Cabeça | Jararaca | 10.800 | 4 m | 2.600 | 1.000 m | 48 |

Míssil padrão: barato e bom para saturar a defesa de ponto. Não acende fogo.

### Submunição: Piranha

| Lançador | Abre a | Nunca antes de | Abre sozinha em | Minimísseis | Vida de cada | Explosão de cada | Raio | Vida do portador |
|---|---|---|---|---|---|---|---|---|
| Caipora | 300 m | 1 s | 4,6 s | 12 | 200 | 1.330 | 1,5 m | 2.000 |
| Mula-sem-Cabeça | 400 m | 1,2 s | 5,4 s | 20 | 250 | 3.240 | 2 m | 4.000 |

O portador abre antes do alvo e solta um cardume de minimísseis que se espalham pelas peças inimigas (cada um procura uma peça diferente); as pétalas do nariz caem e somem. Fora de alcance ele abre sozinho; um impacto antes da hora também solta o cardume. Nunca abre sobre o próprio convés. Neste build: alvo aleatório `on`, pétalas `bullets`, versão leve `false`.

### PEM: Poraquê

| Lançador | Dreno no escudo | Dano no escudo | Escudo por acerto | Escudo por salva | Pulso no casco (raio) |
|---|---|---|---|---|---|
| Caipora | 4.000 | 300 | 10.300 | 164.800 | 4.000 (10 m) |
| Mula-sem-Cabeça | 7.500 | 400 | 19.150 | 306.400 | 7.500 (12 m) |

Drena a bateria do escudo atingido (como os íons do SW): o overclock do escudo não corta esse dreno. No casco, um pulso de área apaga peças com energia. Nenhuma salva derruba sozinha uma bolha gigante do SW. Sobrecarga extra no escudo: desligada neste build (`missiles.poraque_overload`).

### Nuclear: Iara

Só na Mula-sem-Cabeça, 2 por salva, 1 Ogiva Nuclear por míssil. Dois estágios: o corpo voa 1,5 s e solta a ogiva, que segue o alvo. Uma ogiva só. Explosão: 175.000 (10 m) nas peças + 55.000 (8 m) na estrutura. Vida 12.000, alcance 1.000 m, recarga 9,97 s por míssil (o overclock não acelera a nuclear). No máximo 2 baterias de mísseis nucleares por nave.

## 4. Cargas e fábricas

| Carga | Pilha | Fábrica | Ritmo | Cargas por míssil |
|---|---|---|---|---|
| Carga de Míssil HE | 10 | F4 Fábrica de Mísseis | 2 a cada 0,45 s sozinha, 0,3 s com 2 vizinhas | Caipora 2, Mula-sem-Cabeça 2 |
| Carga de Míssil de Submunição | 10 | F4 Fábrica de Mísseis | 2 a cada 0,54 s sozinha, 0,36 s com 2 vizinhas | Caipora 4, Mula-sem-Cabeça 10 |
| Carga de Míssil PEM | 10 | F4 Fábrica de Mísseis | 1 a cada 0,54 s sozinha, 0,36 s com 2 vizinhas | Caipora 2, Mula-sem-Cabeça 3 |
| Ogiva Nuclear | 2 | F5 Fábrica de Ogivas Nucleares | 1 a cada 4,5 s sozinha, 3 s com 2 vizinhas | Mula-sem-Cabeça 1 |

Com a Fita, a Fábrica de Mísseis manda as cargas para os paióis de mísseis e os paióis empurram para os lançadores no tipo escolhido. Sem a Fita, a tripulação abastece abaixo da metade; na reserva sem Fita um paiol encostado no lançador também alimenta.

## 5. Balanço

| Lançador e modo | Dano | Comparado com | Razão |
|---|---|---|---|
| Tocandira (HE) | 1.815 casco/s | lançador do SW (densidade do sistema) | 1,15x |
| Caipora (HE) | 6.486 casco/s | lançador do SW (densidade do sistema) | 1,15x |
| Caipora (Submunição) | 7.147 casco/s | lançador do SW (densidade do sistema) | 1,19x |
| Mula-sem-Cabeça (HE) | 18.929 casco/s | lançador do SW (densidade do sistema) | 1,15x |
| Mula-sem-Cabeça (Submunição) | 20.814 casco/s | lançador do SW (densidade do sistema) | 1,24x |
| Caipora (Poraquê) | 14.207 escudo/s | íons do SW (por tile) | 1,20x |
| Mula-sem-Cabeça (Poraquê) | 32.876 escudo/s | íons do SW (por tile) | 1,17x |

A conta dos lançadores é a densidade do sistema (lançador + fábrica + tripulação, por tile), porque os lançadores do SW pagam em peças de míssil e tripulação. Só com a tripulação, sem a Fita e sem acoplamento: 0,78-0,96x.

### Estoque interno

| Lançador | Modo | Cargas (células + depósito) | Tempo de tiro |
|---|---|---|---|
| Tocandira | HE | 30 | 33,1 s |
| Caipora | HE | 160 | 44,4 s |
| Caipora | Submunição | 160 | 44,7 s |
| Caipora | PEM | 160 | 58 s |
| Mula-sem-Cabeça | HE | 480 | 68,5 s |
| Mula-sem-Cabeça | Submunição | 400 | 62,3 s |
| Mula-sem-Cabeça | PEM | 240 | 46,6 s |
| Mula-sem-Cabeça | Nuclear | 10 | 100 s |

O lançador carregado explode junto com o estoque quando é destruído (uma explosão por depósito, com o teto da 1.x).

## 6. Techs

| Tech | Custo | Pré-requisitos | Libera |
|---|---|---|---|
| Tocandira | 3.500 | Carcará | Tocandira, Fábrica de Mísseis, Paiol de Mísseis 1x1 e Paiol de Mísseis 2x2 |
| Caipora | 14.000 | Tocandira | Caipora |
| Míssil de Submunição (Piranha) | 16.000 | Caipora | míssil Piranha |
| Míssil PEM | 12.000 | Caipora | míssil Poraquê |
| Overclock: Caipora | 40.000 | Caipora e `cosmoteer.heat_management` | overclock: Caipora |
| Mula-sem-Cabeça | 150.000 | Míssil de Submunição (Piranha) e `cosmoteer.control_room_large` | Mula-sem-Cabeça |
| Fábrica de Ogivas Nucleares | 110.000 | Mula-sem-Cabeça | Fábrica de Ogivas Nucleares e míssil Iara |
| Overclock: Mula-sem-Cabeça | 160.000 | Mula-sem-Cabeça e `cosmoteer.heat_management` | overclock: Mula-sem-Cabeça |

## 7. Variantes (o que muda se um teste falhar)

| Switch | Neste build | Valores | Decidido por |
|---|---|---|---|
| `missiles.category_limits` | `on` | on, off | - |
| `missiles.cluster_lite` | `false` | true, false | teste T-MSL-PERF |
| `missiles.cluster_open` | `proximity` | proximity, timer | - |
| `missiles.cluster_petals` | `bullets` | particles, bullets | teste T-ART-8 |
| `missiles.cluster_randomize_target` | `on` | on, off_fan | teste T-MSL-CLUSTER |
| `missiles.iara_hp` | `12000` | 12000, 17500, 30000 | você (outras escolhas) |
| `missiles.poraque_overload` | `false` | true, false | teste T3 |
| `missiles.poraque_pulses` | `off` | off, repeating | - |
