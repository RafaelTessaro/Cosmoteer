# Lança-mísseis de convés do Bullet Strike: projeto final

- **Versão para máquina:** `tools/spec/bullet_strike_missiles.json` (o spec dos mísseis; os números de armas, munições e fábricas ficam em `tools/spec/bullet_strike_spec.json`).
- **Gerador:** `tools/bs_data.py` lê o spec e `tools/bsgen/launchers.py` e `tools/bsgen/shots.py` geram os lançadores e os mísseis (`python3 tools/build_mod.py`). Todos os números abaixo vêm do spec; o gerador confere salva, ciclo, alfa, cook-off e os limites rígidos dos mísseis e aborta se algo divergir (`_check_missile` e `_check_launcher` em `tools/bs_data.py`, `_check_cookoff` em `tools/bsgen/launchers.py`).
- **Limites rígidos:** 95 verificações em `balance_checks.hard_limits` do spec, todas aprovadas (seção 8.8).
- **Convenções deste documento:** A.E. = família alto-explosiva (`missile_part_he`), T. = térmica (`missile_part_thermal`), P.E.M. = pulso eletromagnético (`missile_part_emp`), como nos nomes das peças de míssil do jogo base. "Células" (ou "conjunto de células") são as células visíveis de um modo, que o autocarregador enche (o armazenamento `ReadyRack_k`); a "salva em sequência" dispara uma célula atrás da outra, e a "cadência da salva" é o intervalo entre duas células (a constante `RIPPLE`). Nomes de componentes, campos e arquivos ficam como no jogo (em inglês), entre crases.

## 1. O projeto em um parágrafo

Tiro, porrada e bomba, com o motor e os números do projeto A. Três lançadores de convés tripulados e sem energia - a caixa de micromísseis estilo RAM (início), os casulos octogonais gêmeos com cúpula sensora (meio) e a bateria quádrupla sem cabeça com 48 pontas (fim) - rodam o mesmo ciclo: a tripulação enche um paiol interno por família de recurso, um autocarregador tripulado enche as células visíveis, as células cheias soltam uma salva dramática em sequência e o lançador recarrega. O DPS sustentado fica exatamente nas faixas de cada fase do mod; o espetáculo está no alfa e nos mísseis: o cardume da Piranha, a contagem regressiva do Carrapato, o napalm que continua queimando, o P.E.M., o torpedo com iscas Boto e o nuclear Iara, que precisa ser mascarado. O overclock compra velocidade de recarga com calor, mísseis descartados e risco de cook-off; a bateria de fim de jogo é muito forte e muito cara (5x6, 8 tripulantes, 18 pontos de comando, 77.000 créditos, 2 por nave na vaga nuclear). No caminho padrão só há tipos de componente do jogo base e peças de míssil do jogo base; toda mecânica arriscada tem um plano B que não muda nenhum número.

**Base e enxertos.** BASE = o núcleo de lançador do projeto A (trava do modelo B, autocarregador tripulado, `ModeSwitchDelay`, `DryFlush`, napalm seguro, Carrapato que não pode ser alvo, calor por peça carregada) e a espinha numérica de A (faixas, overclock <= 550, 300/400/600 m, dreno de 1.500 por peça P.E.M.) - os dois juízes que pesam risco de motor e balanceamento escolheram esse projeto (8,5 / 8,0). ENXERTADO de B (fidelidade 8,5): a sequência de referências por fase (caixa RAM -> casulos octogonais gêmeos -> bateria quádrupla 3x4), a Mula-sem-Cabeça no fim de jogo, os parâmetros da Piranha (25 m, `InheritVelocity` false, mira fraca e tardia), o Iara em `bs_limit_nuke` sem overclock, um paiol por família de recurso, o cook-off por família, o esboço completo da torre e o `CrewKillChance` no Carrapato. ENXERTADO de C: o cassete de micromísseis (como `Burst` 2), o torpedo com iscas Boto, o custo de descarte do overclock (escalado por célula), os filhos com ímã + espaçamento, a carga do Carrapato no estilo buzz droid, os toggles de limiar com `MultiResourceStorage`, o padrão de variante isolada com `Repeating` e a matriz de contra-jogadas. NOVO aqui: `ModeSwitchDelay` por modo, cadência da salva alinhada aos ticks, o leiaute pesado de 16 unidades na Mula, o HP total dos filhos >= HP do portador e o tempo de mascaramento do Iara.

## 2. Restrições respeitadas

- Cosmoteer 0.30.4 + 0.30.5 RC4: só tipos de componente do jogo base presentes no 0.30.3 e no RC4; valores literais em toda parte; nada de `DefaultWeaponCoverage` / `MatchWeaponCoverage` / `CoverageSectorArc` / `UseContiguity` / `AllowVertexContiguity` / globais de retenção estrutural / `APPLIED_HEAT_PER_MISSILE`; `HealthFactor`, nunca `ScaleHealth`.
- Só torres de convés: `ProhibitedBy [tall]` + anel `tall`, sem `ProhibitAbove`, `TurretCollider { IsHigh = true; ChainedTo = Turret }`, casulo em `roof_doodads`, sobreposições das células em `roof_turrets`; todo `Hit` de míssil, filho, isca e carga tem `FriendlyShipLowCollisions = false`, `FriendlyShipHighCollisions = false` e `SourcePartCollisionDelay`.
- Só tripulação, sem energia: sem armazenamento de bateria, `TypeCategories` sem `uses_power`; `IsOperational` = [`PowerToggle` (liga/desliga), `PartCrew`, `ScorchedToggle` (+ reset do overclock)].
- Estoque interno reabastecido pela tripulação: um paiol por família de recurso + `ResourceConsumer` (`Weapon_Supply`), fora dos blocos alternados.
- Recarga automática só com tripulação: o `OperationalToggle` do autocarregador contém `IsOperational` (`PartCrew`).
- O overclock encurta a recarga com custos reais: `Interval` / 1,5; calor por peça carregada + calor constante; descarte; reset do overclock; paiol esvaziando mais rápido; cadeia de cook-off; nunca na recarga nuclear; overclock de início de jogo projetado, mas desligado (regra do mod).
- Compatível com o SW:ACD: `TargetCategory` 'missile' em todos, seletor próprio `bs_missile_type`, peças do jogo base compartilhadas com o SW, nenhum tipo, campo ou referência do SW, a não ser num arquivo de variante isolado atrás de uma opção de build.

## 3. Os três lançadores

|  | Tocandira (início) | Caipora (meio) | Mula-sem-Cabeça (fim) |
|---|---|---|---|
| ID | `rafaeltessaro.bs_msl_box` | `rafaeltessaro.bs_msl_twin` | `rafaeltessaro.bs_msl_quad` |
| Nome (en / pt-BR) | Deck Micro-Missile Box / Caixa de Micromísseis de Convés | Twin-Pod Deck Missile Launcher / Lançador Duplo de Mísseis de Convés | Quad-Pod Heavy Missile Battery / Bateria Pesada de Mísseis Quádrupla |
| Tamanho / tripulação / pontos de comando / vida | 2x2 / 1 / 2 / 8.000 | 3x3 / 2 / 5 / 12.000 | 5x6 / 8 / 18 / 42.000 |
| Custo | aço 60, bobina 16 (3.100 cr) | aço 100, hiperbobina 20, triaço 8, processador 1 (12.600 cr) | aço 400, hiperbobina 110, triaço 100, processador 4, urânio enriquecido 2 (77.000 cr) |
| Células visíveis | 12 tubos (6 cassetes de tubo duplo) | 16 (2 casulos x 8, 3-2-3) | 48 (4 casulos x 3x4) |
| Salva A.E. / cadência da salva | 12 em 0,733 s / `FireInterval` da torre = 4/30 (alinhado ao tick, como o 2/30 do ponto de defesa); o tubo B do cassete dispara `BurstDelay` = 2/30 depois do tubo A | 16 em 2,0 s / `FireInterval` da torre = 4/30 (alinhado ao tick, como o 2/30 do ponto de defesa) | 48 em 3,133 s / `FireInterval` da torre = 2/30 (alinhado ao tick, como o 2/30 do ponto de defesa) |
| Recarga / ciclo A.E. | 1,39 s por cassete / 9,073 s | 1,06 s por míssil / 18,96 s | 0,264 s por míssil / 15,805 s |
| Paióis (peças) | A.E. 12, T. 12 | A.E. 64, T. 64, P.E.M. 64 | A.E. 192, T. 192, P.E.M. 96, nuclear 32 |
| Seletor (`bs_missile_type`) | 0 Muriçoca, 3 Taturana-mirim | 0 Jararaca, 1 Piranha, 2 Carrapato, 3 Taturana, 4 Poraquê, 5 Boto | 0 Jararaca, 1 Piranha, 2 Carrapato, 3 Taturana, 4 Poraquê, 5 Boto, 6 Iara |
| Alcance | 300 m | 400 m (torpedo 400) | 600 m |
| Arco / giro / limiar de disparo | 360 / 120 graus/s / 30 graus | 360 / 75 graus/s / 25 graus | 360 / 40 graus/s / 20 graus |
| Anel / colisor | 1 / 0,85 | 1 / 1,25 | 2 / 2,1 |
| DPS efetivo A.E. por quadro (OC) | 264,5 (381,4, desligado) | 328,2 (467,6) | 379,6 (518,1) |
| Overclock | Furious Swarm / Enxame Furioso (desligado) | Caipora's Fury / Fúria da Caipora | Stampede / Estouro da Boiada |
| Limite por nave | nenhum | nenhum | 2 (`bs_limit_nuke`, junto com a Boiúna) |
| Cook-off (família A.E., cheia) | 11.500 + 3.800 estrutural | 61.200 + 20.400 estrutural | 183.600 + 61.200 estrutural |

### 3.1 Tocandira (início): Deck Micro-Missile Box / Caixa de Micromísseis de Convés

- **Conceito.** Caixa de micromísseis estilo RAM para o início de jogo: o atirador gira uma caixa 2x2 sobre o convés e 12 micromísseis saem chiando em 0,73 s, com seis cassetes de tubo duplo disparando de dois em dois ('tsk-tsk ... tsk-tsk'); cada cassete solta um clarão pequeno para a frente e uma baforada de sopro para trás, sobre o convés.
- **Peça base / categorias.** `base_med_part_terran` (sem overclock; a ligação do overclock fica nos dados, desligada); `TypeCategories` [weapon, is_crewed, uses_missiles, uses_launcher_parts].
- **Créditos por DPS efetivo:** 2,93. **Componentes emissores:** 12.

| Modo | Codinome | Leiaute | Mísseis/salva | Munição por míssil | Recarga s/unidade | Salva s | Ciclo s | Efetivo/quadro | x A.E. | Estoque (mísseis / s de fogo) | OC efetivo/quadro |
|---|---|---|---|---|---|---|---|---|---|---|---|
| he | Muriçoca | cassette | 12 | 1 `missile_part_he` por cassete = 2 micromísseis (0,5 peça cada) | 1,39 | 0,733 | 9,073 | 264,5 | 1,0 | 36,0 / 27,2 | 381,4 |
| napalm | Taturana-mirim | cassette | 12 | 1 `missile_part_thermal` por cassete = 2 micromísseis (0,5 peça cada) | 1,39 | 0,733 | 9,073 | 99,2 | 0,375 | 36,0 / 27,2 | 143,0 |

**Overclock - Furious Swarm / Enxame Furioso (projetado, DESLIGADO por padrão).** Projetado, mas DESLIGADO (regra do mod: overclock só nas armas de meio e fim de jogo). Para ligar, troque a peça base por `base_med_part_terran_overclock` e registre a tech `rafaeltessaro.bs_msl_box-overclock`; todos os números abaixo já estão nos dados.

- Efeito: `Interval` do `Autoloader_k` / 1,5 (P.E.M. / 1,2, para a taxa de escudo em overclock ficar <= 880); `Duration` do `ModeSwitchDelay_k` / o mesmo fator; a cadência da salva, o dano, o alcance e o míssil não mudam.
- Calor: 200 por peça carregada + 30/s -> A.E. 220,7 de média / 245,8 de pico de calor/s (0,2 / 0,22 radiador).
- Descarte por salva (peças): he 0, napalm 0.
- o calor sai quando o AUTOCARREGADOR põe um míssil nas células (padrão `Overclock_ConversionHeatProducer` da `factory_he` com `Trigger = Autoloader_k`): munição pesada paga pelo peso, e o calor acompanha o trabalho extra de carregar
- DESCARTE: cada vez que as células de um modo travam cheias em overclock, as peças de CELLS/16 mísseis saem do paiol da família (`ResourceChange` com `Amount` negativo, `Trigger = RackFullTrigger_k`; precedente do `thruster_boost`); torpedo e nuclear isentos; salvas com menos de 16 mísseis (Tocandira) não descartam nada
- `OverclockReset`: 3 s parado quando o overclock é desligado (`base_part_overclock`, herdado)
- o paiol esvazia mais rápido: viagens de tripulação A.E. 3,97 -> 5,72/min, fábricas A.E. 0,2 -> 0,29
- cadeia de cook-off: o calor que a rede não absorve transborda para os quadros do próprio lançador (`OverheatEffects`) -> com >= 350 de calor sorteia incêndio -> queimado -> o cook-off da família, proporcional ao estoque, dispara
- as portas térmicas têm de ficar alcançáveis (mesma geometria de portas da nossa CIWS 3x3 / Boiúna 5x6)
- Assinatura visual: a fenda da espinha pisca laranja, 2 baforadas de vapor por carga.

**Cook-off com o estoque cheio:** `missile_part_he`: um par `ScorchedEffects`/`DeathEffects` por armazenamento (paiol + as células de cada modo, `FactorHitEffectsWith` = esse armazenamento, `BaseValue` = valor x peças dele / `parts_full`); total com o estoque cheio: `ExplosiveDamage` 11.500 r3,5 (fogo 50%/1.000, `CrewKillChance` 30%) + 3.800 estrutural; 18 peças cheias = 850,0 por peça; `missile_part_thermal`: `GridStatusApplication` cosmoteer.heat com reserva de 4.500 nos próprios quadros (`Filter { Self = true }`, despejo do lançador térmico do jogo base).

**Arte.** Caixa compacta estilo RAM (referência 1) num garfo blindado curto: um casulo-caixa chanfrado inclinado 35 graus, uma grade escura e rebaixada de 4x3 tubos lida como 6 cassetes de tubo duplo; garras frontais abraçam os lados da caixa; espinha elevada com uma fenda de buscador infravermelho âmbar; tubos abertos atrás com venezianas (sopro); baia de ventilação traseira com 3 luzes âmbar. A 64 px lê-se como uma 'caixa de furos'.

- Casulos: 1 casulo-caixa (6 cassetes x 2 tubos). Grade de células: 4 colunas x 3 linhas = 12 tubos, passo 0,26 x 0,22 quadro (encurtado pela perspectiva), raio do tubo 0,09, face 1,1 x 0,7 quadro; cassetes = pares horizontais.
- Leiautes: `cassette` = 6 cassetes de tubo duplo (12 tubos visíveis); as células contam cassetes; níveis de sobreposição 0..6 (pares).
- Animações: giro da torre 120 graus/s (motor); os pares da sobreposição esvaziam em LIFO a cada lançamento (`ResourceSprites` em `ReadyRack_k`, camada `roof_turrets` sobre o casulo em `roof_doodads`); clarão de lançamento por tubo (`missile_launcher_shoot_flash`, Upper1, 60%) + baforada de sopro (`chaingun_shoot_smoke`, Upper) atrás da caixa; recarga: os pares de cassete enchem um a um (`launcher_reload_0x.wav` via `TriggeredEffects { Trigger = Autoloader_k }`); células cheias: som `launcher_ready` + as 3 luzes de ventilação acendem (`ToggleEffects` na trava); pulso da fenda da espinha em laço de 8 quadros x 0,12 s; sem recuo do casulo (mantém as sobreposições alinhadas).
- Meta da peça (`tools/blender/parts/bs_msl_box.py`, `kind: "launcher"`): `{"kind": "launcher", "size": [2, 2], "pivot": [1.0, 0.95], "turret_box": 1.9, "ring_r": 0.8, "collider": 0.85, "cell_style": "pitched", "pitch_deg": 35, "accent": "amber", "cells": {"pods": [{"center": [0.0, 0.32], "cols": 4, "rows": 3, "pitch": [0.26, 0.22]}], "tube_r": 0.09, "units": "pairs", "fill_order": "row_major_bottom_up"}, "looks": ["he", "napalm"], "backblast": [[0.0, -0.55]], "preview_pattern": "ripple"}`

### 3.2 Caipora (meio): Twin-Pod Deck Missile Launcher / Lançador Duplo de Mísseis de Convés

- **Conceito.** Lançador de casulos gêmeos para o meio de jogo: dois casulos octogonais com as ogivas à mostra ladeiam uma cúpula sensora blindada; uma salva é um rufar de 2 s com 16 mísseis, primeiro o casulo direito e depois o esquerdo, com as faixas no nariz mostrando a ogiva escolhida; no modo Boto cada face de casulo leva um torpedo gordo com tampa.
- **Peça base / categorias.** `base_med_part_terran_overclock`; `TypeCategories` [weapon, is_crewed, uses_missiles, uses_launcher_parts, uses_emps].
- **Créditos por DPS efetivo:** 4,27. **Componentes emissores:** 82.

| Modo | Codinome | Leiaute | Mísseis/salva | Munição por míssil | Recarga s/unidade | Salva s | Ciclo s | Efetivo/quadro | x A.E. | Estoque (mísseis / s de fogo) | OC efetivo/quadro |
|---|---|---|---|---|---|---|---|---|---|---|---|
| he | Jararaca | fine16 | 16 | 2 `missile_part_he` | 1,06 | 2,0 | 18,96 | 328,2 | 1,0 | 48,0 / 56,9 | 467,6 |
| cluster | Piranha | fine16 | 16 | 2 `missile_part_he` | 1,06 | 2,0 | 18,96 | 295,4 | 0,9 | 48,0 / 56,9 | 420,8 |
| limpet | Carrapato | fine16 | 16 | 2 `missile_part_he` | 1,06 | 2,0 | 18,96 | 328,2 | 1,0 | 48,0 / 56,9 | 467,6 |
| napalm | Taturana | fine16 | 16 | 2 `missile_part_thermal` | 1,06 | 2,0 | 18,96 | 140,6 | 0,429 | 48,0 / 56,9 | 200,4 |
| emp | Poraquê | fine16 | 16 | 2 `missile_part_emp` | 1,06 | 2,0 | 18,96 | 121,9 | 0,371 | 48,0 / 56,9 | 143,3 |
| torpedo | Boto | torpedo2 | 2 | 6 `missile_part_he` | 4,65 | 0,133 | 9,433 | 282,7 | 0,861 | 12,7 / 59,7 | 421,1 |

**Overclock - Caipora's Fury / Fúria da Caipora.** Os reguladores do carregador ficam abertos: os casulos recarregam em 2/3 do tempo enquanto o olho da cúpula arde em laranja.

- Efeito: `Interval` do `Autoloader_k` / 1,5 (P.E.M. / 1,2, para a taxa de escudo em overclock ficar <= 880); `Duration` do `ModeSwitchDelay_k` / o mesmo fator; a cadência da salva, o dano, o alcance e o míssil não mudam.
- Calor: 425 por peça carregada + 100/s -> A.E. 1.122,0 de média / 1.302,8 de pico de calor/s (1,02 / 1,18 radiador).
- Descarte por salva (peças): he 2, cluster 2, limpet 2, napalm 2, emp 2, torpedo 0.
- o calor sai quando o AUTOCARREGADOR põe um míssil nas células (padrão `Overclock_ConversionHeatProducer` da `factory_he` com `Trigger = Autoloader_k`): munição pesada paga pelo peso, e o calor acompanha o trabalho extra de carregar
- DESCARTE: cada vez que as células de um modo travam cheias em overclock, as peças de CELLS/16 mísseis saem do paiol da família (`ResourceChange` com `Amount` negativo, `Trigger = RackFullTrigger_k`; precedente do `thruster_boost`); torpedo e nuclear isentos; salvas com menos de 16 mísseis (Tocandira) não descartam nada
- `OverclockReset`: 3 s parado quando o overclock é desligado (`base_part_overclock`, herdado)
- o paiol esvazia mais rápido: viagens de tripulação A.E. 10,13 -> 15,33/min, fábricas A.E. 0,51 -> 0,77
- cadeia de cook-off: o calor que a rede não absorve transborda para os quadros do próprio lançador (`OverheatEffects`) -> com >= 350 de calor sorteia incêndio -> queimado -> o cook-off da família, proporcional ao estoque, dispara
- as portas térmicas têm de ficar alcançáveis (mesma geometria de portas da nossa CIWS 3x3 / Boiúna 5x6)
- Assinatura visual: o olho da cúpula fica laranja, brasa na ventilação, clarão de lançamento a 120%.

**Cook-off com o estoque cheio:** `missile_part_he`: um par `ScorchedEffects`/`DeathEffects` por armazenamento (paiol + as células de cada modo, `FactorHitEffectsWith` = esse armazenamento, `BaseValue` = valor x peças dele / `parts_full`); total com o estoque cheio: `ExplosiveDamage` 61.200 r5 (fogo 50%/1.000, `CrewKillChance` 30%) + 20.400 estrutural; 96 peças cheias = 850,0 por peça; `missile_part_thermal`: `GridStatusApplication` cosmoteer.heat com reserva de 24.000 nos próprios quadros (`Filter { Self = true }`, despejo do lançador térmico do jogo base); `missile_part_emp`: `ExplosiveResourceDrain` de bateria 57.600 r12 (padrão de morte do lançador P.E.M. do jogo base).

**Arte.** Cabeça larga de 'dois punhos' (referências 3 + 2): casulos OCTOGONAIS chanfrados gêmeos ladeando uma cúpula central blindada com uma fenda de olho sensor âmbar (o olho da referência 2, recolorido para a cor da família), lâminas em garra na frente segurando os casulos, quatro pés abertos desenhados no anel da torre (a base de quatro pernas da referência 3), escotilha traseira do paiol e baia de ventilação com 5 luzes âmbar.

- Casulos: 2 casulos octogonais, simétricos. Grade de células: 8 células por casulo no padrão 3-2-3, passo 0,24 quadro, raio do tubo 0,085, casulos inclinados 35 graus; visual de torpedo = um nariz de torpedo com tampa por face de casulo.
- Leiautes: `fine16` = 16 células: 2 casulos octogonais x 8 (3-2-3); `ResourceSprites` por casulo com `RangeLow`/`RangeHigh` 0-8 / 8-16, 9 níveis cada; `torpedo2` = 2 cassetes de torpedo, um nariz de torpedo com tampa cobrindo cada face de casulo; 2 níveis por casulo (0/1).
- Animações: giro da torre 75 graus/s; sobreposições por casulo (2 x `ResourceSprites` sobre o mesmo conjunto de células, `RangeLow`/`RangeHigh`), LIFO, o casulo direito esvazia primeiro; clarão de lançamento + sopro por célula (buckets Upper), tremor de tela 0,01 por lançamento; faixas no nariz por visual: A.E. âmbar, Piranha com tampa de pétalas amarela, Carrapato com anel de garra vermelho, Taturana com tampa laranja, Poraquê com faixa de bobina azul, Boto com tampa branca; laço de piscada do olho da cúpula (`turret_anim` 8 quadros x 0,12 s); o olho fica laranja e a brasa da ventilação acende em overclock (sprite ligado por `IsOverclocked`); sem recuo do casulo.
- Meta da peça (`tools/blender/parts/bs_msl_twin.py`, `kind: "launcher"`): `{"kind": "launcher", "size": [3, 3], "pivot": [1.5, 1.4], "turret_box": 2.8, "ring_r": 1.15, "collider": 1.25, "cell_style": "pitched", "pitch_deg": 35, "accent": "amber", "cells": {"pods": [{"center": [-0.85, 0.35], "pattern": "3-2-3", "pitch": [0.24, 0.24]}, {"center": [0.85, 0.35], "pattern": "3-2-3", "pitch": [0.24, 0.24]}], "tube_r": 0.085, "fill_order": "pod_sequential (L then R)"}, "looks": ["he", "cluster", "limpet", "napalm", "emp", "torpedo"], "backblast": [[-0.85, -0.6], [0.85, -0.6]], "preview_pattern": "ripple"}`

### 3.3 Mula-sem-Cabeça (fim): Quad-Pod Heavy Missile Battery / Bateria Pesada de Mísseis Quádrupla

- **Conceito.** Bateria de fim de jogo, de nau capitânia (Mula-sem-Cabeça): um corpo blindado sem cabeça com quatro casulos longos em braços hidráulicos; uma salva é um estouro em quatro tempos de 48 mísseis pesados em 3,1 s, que enterra o convés na fumaça do sopro. Carregada, é a peça mais perigosa da nave.
- **Peça base / categorias.** `base_large_part_terran_overclock`; `TypeCategories` [weapon, is_crewed, uses_missiles, uses_launcher_parts, uses_emps, uses_nukes, bs_limit_nuke].
- **Créditos por DPS efetivo:** 6,76. **Componentes emissores:** 118.

| Modo | Codinome | Leiaute | Mísseis/salva | Munição por míssil | Recarga s/unidade | Salva s | Ciclo s | Efetivo/quadro | x A.E. | Estoque (mísseis / s de fogo) | OC efetivo/quadro |
|---|---|---|---|---|---|---|---|---|---|---|---|
| he | Jararaca | fine48 | 48 | 2 `missile_part_he` | 0,264 | 3,133 | 15,805 | 379,6 | 1,0 | 144,0 / 47,4 | 518,1 |
| cluster | Piranha | heavy16 | 16 | 4 `missile_part_he` | 0,6 | 1,0 | 10,6 | 339,6 | 0,895 | 64,0 / 42,4 | 486,5 |
| limpet | Carrapato | heavy16 | 16 | 4 `missile_part_he` | 0,6 | 1,0 | 10,6 | 377,4 | 0,994 | 64,0 / 42,4 | 540,5 |
| napalm | Taturana | heavy16 | 16 | 4 `missile_part_thermal` | 0,6 | 1,0 | 10,6 | 150,9 | 0,398 | 64,0 / 42,4 | 216,2 |
| emp | Poraquê | heavy16 | 16 | 3 `missile_part_emp` | 0,6 | 1,0 | 10,6 | 95,6 | 0,252 | 48,0 / 31,8 | 112,6 |
| torpedo | Boto | torpedo4 | 4 | 12 `missile_part_he` | 2,37 | 0,2 | 9,68 | 330,6 | 0,871 | 20,0 / 48,4 | 490,8 |
| nuclear | Iara | torpedo2_inner | 2 | 8 `missile_part_nuke` | 9,97 | 0,067 | 20,007 | 266,6 | 0,702 | 6,0 / 60,0 | sem OC |

**Overclock - Stampede / Estouro da Boiada.** Os quatro carregadores dos casulos em ciclo de emergência: o colar da mula sem cabeça brilha e o estouro vem a cada ~11,6 s.

- Efeito: `Interval` do `Autoloader_k` / 1,5 (P.E.M. / 1,2, para a taxa de escudo em overclock ficar <= 880; nuclear excluído); `Duration` do `ModeSwitchDelay_k` / o mesmo fator; a cadência da salva, o dano, o alcance e o míssil não mudam.
- Calor: 400 por peça carregada + 150/s -> A.E. 3.465,7 de média / 4.695,5 de pico de calor/s (3,15 / 4,27 radiadores).
- Descarte por salva (peças): he 6, cluster 4, limpet 4, napalm 4, emp 3, torpedo 0.
- o calor sai quando o AUTOCARREGADOR põe um míssil nas células (padrão `Overclock_ConversionHeatProducer` da `factory_he` com `Trigger = Autoloader_k`): munição pesada paga pelo peso, e o calor acompanha o trabalho extra de carregar
- DESCARTE: cada vez que as células de um modo travam cheias em overclock, as peças de CELLS/16 mísseis saem do paiol da família (`ResourceChange` com `Amount` negativo, `Trigger = RackFullTrigger_k`; precedente do `thruster_boost`); torpedo e nuclear isentos; salvas com menos de 16 mísseis (Tocandira) não descartam nada
- `OverclockReset`: 3 s parado quando o overclock é desligado (`base_part_overclock`, herdado)
- o paiol esvazia mais rápido: viagens de tripulação A.E. 36,44 -> 52,84/min, fábricas A.E. 1,82 -> 2,64
- cadeia de cook-off: o calor que a rede não absorve transborda para os quadros do próprio lançador (`OverheatEffects`) -> com >= 350 de calor sorteia incêndio -> queimado -> o cook-off da família, proporcional ao estoque, dispara
- as portas térmicas têm de ficar alcançáveis (mesma geometria de portas da nossa CIWS 3x3 / Boiúna 5x6)
- Assinatura visual: o recesso do colar clareia (quadros de brasa), as ventilações dos casulos brilham, o som da salva em sequência fica 15% mais agudo.

**Cook-off com o estoque cheio:** `missile_part_he`: um par `ScorchedEffects`/`DeathEffects` por armazenamento (paiol + as células de cada modo, `FactorHitEffectsWith` = esse armazenamento, `BaseValue` = valor x peças dele / `parts_full`); total com o estoque cheio: `ExplosiveDamage` 183.600 r7 (fogo 50%/1.000, `CrewKillChance` 30%) + 61.200 estrutural; 288 peças cheias = 850,0 por peça; `missile_part_thermal`: `GridStatusApplication` cosmoteer.heat com reserva de 64.000 nos próprios quadros (`Filter { Self = true }`, despejo do lançador térmico do jogo base); `missile_part_emp`: `ExplosiveResourceDrain` de bateria 86.400 r12 (padrão de morte do lançador P.E.M. do jogo base); `missile_part_nuke`: um par `ScorchedEffects`/`DeathEffects` por armazenamento (paiol + as células de cada modo, `FactorHitEffectsWith` = esse armazenamento, `BaseValue` = valor x peças dele / `parts_full`); total com o estoque cheio: `ExplosiveDamage` 72.000 r8 (fogo 50%/1.000, `CrewKillChance` 30%) + 24.000 estrutural; 48 peças cheias = 2.000 por peça.

**Arte.** Bateria quádrupla cyberpunk (referência 4) no estilo da família: um corpo largo e achatado sem cabeça, com 4,8 quadros de largura - um colar blindado aberto ('pescoço') com um recesso de brasa bem fraco onde deveria estar a cabeça - carregando dois pares de casulos retangulares longos em braços de pistão hidráulico visíveis, cada face de casulo com uma grade de 3x4 células (48 pontas); lâminas em garra na raiz dos casulos, saia blindada sobre o anel, baia de ventilação traseira com 6 luzes âmbar. A 64 px lê-se como 'quatro caixas de munição em volta de um colar escuro'. CABEÇA ALTERNATIVA (escolha do usuário): o 'gigante de um olho só' do Gorjala - uma testa blindada com UM olho sensor num recesso escuro entre os pares de casulos (referência 2).

- Casulos: 4 casulos retangulares (2 de cada lado) em braços de pistão, os de fora abertos 6 graus. Grade de células: por casulo 3 colunas x 4 linhas = 12, passo 0,26 x 0,22 quadro, raio do tubo 0,09, inclinados 40 graus; visual pesado = um nariz longo por linha de 3 células; visual de torpedo = um nariz grande com tampa por face de casulo; visual nuclear = casulos internos tampados (faixa verde), os externos fechados por persianas.
- Leiautes: `fine48` = 48 células: 4 casulos x (3 colunas x 4 linhas); `ResourceSprites` por casulo com `RangeLow`/`RangeHigh` 0-12/12-24/24-36/36-48, 13 níveis cada; `heavy16` = 16 unidades pesadas: cada unidade = uma linha de 3 células de um casulo (4 por casulo), mostrada como um nariz longo de calibre duplo; 5 níveis por casulo; `torpedo2_inner` = 2 cassetes nucleares nos casulos internos; os externos mostram persianas fechadas (sprite fixo ligado por `ModeToggle_nuclear`); `torpedo4` = 4 cassetes de torpedo, um por face de casulo; 2 níveis por casulo.
- Animações: giro lento de 40 graus/s; 4 `ResourceSprites` por modo sobre o mesmo conjunto de células (`RangeLow`/`RangeHigh` por casulo; um conjunto de imagens reaproveitado pelos 4 casulos); salva em sequência em quatro tempos atravessando os casulos, clarão + leque de sopro por lançamento (`cannon_smoke_deck`, bucket `RoofCannonSmoke`), tremor de tela 0,02, pancada de 0,15 no último míssil (`TriggeredEffects` na trava desligando); laço dos braços de pistão (`turret_anim` 8 quadros, sutil); o recesso de brasa do colar usa `M['ember']` (bem fraco) e só clareia em overclock - a área emissiva total fica abaixo do orçamento de 1-2% (`STYLE.md` §1.6); SEM partícula de chama por padrão; modo nuclear: as persianas dos casulos externos fecham (sprite fixo ligado por `ModeToggle_nuclear`); o impacto reaproveita o cogumelo da Boiúna (já orçado); sem recuo dos casulos.
- Meta da peça (`tools/blender/parts/bs_msl_quad.py`, `kind: "launcher"`): `{"kind": "launcher", "size": [5, 6], "pivot": [2.5, 2.6], "turret_box": 4.8, "ring_r": 2.0, "collider": 2.1, "cell_style": "pitched", "pitch_deg": 40, "accent": "amber", "cells": {"pods": [{"center": [-1.75, 0.9], "cols": 3, "rows": 4, "pitch": [0.26, 0.22]}, {"center": [-0.75, 0.9], "cols": 3, "rows": 4, "pitch": [0.26, 0.22]}, {"center": [0.75, 0.9], "cols": 3, "rows": 4, "pitch": [0.26, 0.22]}, {"center": [1.75, 0.9], "cols": 3, "rows": 4, "pitch": [0.26, 0.22]}], "tube_r": 0.09, "fill_order": "pod_sequential (outer-L, inner-L, inner-R, outer-R)", "heavy_unit": "one 3-cell row"}, "looks": ["he", "cluster", "limpet", "napalm", "emp", "torpedo", "nuclear"], "backblast": [[-1.75, -1.3], [-0.75, -1.3], [0.75, -1.3], [1.75, -1.3]], "preview_pattern": "ripple", "alt_head": "one_eyed_giant"}`

## 4. Como um lançador funciona

1. A tripulação leva peças de míssil do jogo base para UM paiol por família de recurso (A.E. / T. / P.E.M. / nuclear) - o 'espaço interno para mísseis' que o usuário pediu. Os consumidores só pedem a família que o modo escolhido usa.
2. Enquanto (e só enquanto) o lançador está tripulado, o AUTOCARREGADOR do modo escolhido passa um míssil (PARTS peças -> 1 unidade das células) a cada RELOAD segundos para as CÉLULAS PRONTAS (`ReadyRack_k`). Os temporizadores de recarga do jogo base continuam contando sem tripulação; os nossos param (gaps §4.4 #2).
3. As células formam uma TRAVA (padrão de bateria do `thruster_boost`): ela só abre quando todas as células estão carregadas e fica aberta até a última célula disparar, então uma salva sempre termina e um carregador em overclock nunca a transforma em fogo sem fim.
4. A torre dispara uma célula a cada `RIPPLE` (a cadência da salva) por um `ModeCycle` por modo, em ordem LIFO, então as sobreposições `ResourceSprites` batem com as células reais em toda salva CHEIA (o ciclo recomeça alinhado ao LIFO sempre que as células enchem de novo). Limite cosmético conhecido (T21): uma salva parcial de `DryFlush`, ou o resto de uma salva interrompida depois de voltar ao modo, começa pela última célula, então um tubo parece vazio enquanto outro, que parecia carregado, dispara; todos os emissores puxam do mesmo `ReadyRack_k`, então contagem e dano não mudam.
5. Entrar num modo inicia o `ModeSwitchDelay` desse modo (= uma recarga completa do modo, dividida pelo overclock): as células já cheias de outro modo nunca dão duas salvas seguidas, também quando a troca acontece no meio da salva. Células que JÁ ESTÃO CHEIAS (travadas) na troca também esperam `PrefilledDelay_k` = uma recarga completa SEM a divisão do overclock (variante `prefilled_switch`), porque foram carregadas sem pagar o calor do overclock: células enchidas antes do combate não dão cadência de overclock de graça.
6. Quando o paiol da família não consegue carregar mais um míssil do modo por DRY_DELAY = CELLS x RELOAD segundos seguidos (nenhuma entrega da tripulação durante uma recarga inteira sem overclock), as células parcialmente carregadas disparam mesmo assim (`DryFlush`, com espera: rampa `ValueTween` + `ThresholdToggle` 100%, padrão `ShellChangingValueTween` do chaingun) - nada fica preso, e uma viagem atrasada da tripulação nunca transforma a salva em sequência travada num pinga-pinga de minissalvas (qualquer entrega recomeça a espera).
7. Salva interrompida: a trava continua ligada e as células restantes vão para o próximo alvo; depois o lançador recarrega.
8. Cook-off: um par `ScorchedEffects`/`DeathEffects` POR ARMAZENAMENTO (cada paiol de família e as células de cada modo), fora dos blocos alternados, cada um escalado pelo próprio enchimento e pesado pela capacidade em peças (`BaseValue` = valor da família com estoque cheio x peças do armazenamento / `cookoff.parts_full`; as células de um modo guardam CELLS x PARTS peças): cada peça guardada vale valor/`parts_full` onde estiver, e paiol + maior conjunto de células cheios dão exatamente o valor do spec; um lançador carregado queimado ou destruído explode.

Cortado da v1: o toggle Stream do projeto C (`bs_salvo_mode`): neutro em DPS, contradiz o ritmo 'recarga entre salvas' do usuário e acrescenta um segundo carregador por modo (D-C4); o `Unloader_k` de C, que descarregava na troca: vaza quando o paiol está cheio (D-C3); substituído por `ModeSwitchDelay_k`; o `ShootCycle` no nível da peça e o `SalvoCooldown` único de B (D-B2, D-B5).

Esboço dos componentes (só tipos do jogo base; Caipora como exemplo):

```
// ---- raiz da peça (Caipora como exemplo; gerada por lançador) ----
RIPPLE = 4/30                                   // alinhado ao tick (precedente: FireInterval 2/30 do point_defense)
OVERCLOCK { RELOAD_FACTOR = 1.5; HEAT_PER_PART = 425; HEAT_PER_SECOND = 100 }
HEAT_TO_RESOURCE = &<./Data/statuses/heat/heat.rules>/STATUS_TO_RESOURCE_RATIO
MODE_he      { CELLS = 16; PARTS = 2; RELOAD = 1.06; VENT = 2 }     // ... um bloco por modo (valores em launchers[].modes)
MODE_torpedo { CELLS = 2;  PARTS = 6; RELOAD = 4.65; VENT = 0 }

MissileTypeToggle { Type = UIToggle; ToggleID = "bs_missile_type"; Default = 0; AvailableChoices = [0, 1, 2, 3, 4, 5]; AlwaysAllowInBuildMode = true }
ModeToggle_he { Type = ModeToggle; Mode = MissileTypeToggle; OnMode = 0 }          // ... _cluster 1, _limpet 2, _napalm 3, _emp 4, _torpedo 5

// (1) UM PAIOL POR FAMÍLIA DE RECURSO (he / cluster / limpet / torpedo dividem MagStorage_HE), fora de qualquer ToggledComponents
UsesHE     { Type = MultiToggle; Toggles = [ModeToggle_he, ModeToggle_cluster, ModeToggle_limpet, ModeToggle_torpedo]; Mode = Any }
ConsumeHE  { Type = MultiToggle; Toggles = [CommandConsumptionToggle, UsesHE]; Mode = All }
MagStorage_HE  { Type = ResourceStorage; ResourceType = missile_part_he; MaxResources = 64; DelayBeforeReadyToUse = .5
                 DropResourcesWhenDestroyed = true; DropResourcesWhenRemoved = true; ReceiveResourceMediaEffects = &/COMMON_EFFECTS/AmmoDeliver; UITileRect = [...] }
MagConsumer_HE { Type = ResourceConsumer; ResourceType = missile_part_he; Storage = MagStorage_HE; DefaultPriority = &/PRIORITIES/Weapon_Supply
                 OperationalToggle = ConsumeHE; ConsumptionToggleButtonOffset = [0, -.4] }
// ... MagStorage_Thermal (napalm), MagStorage_EMP (emp), MagStorage_Nuke (nuclear, só na Mula)

// (2) POR MODO: trava das células, autocarregador tripulado, toggles de limiar (padrões de thruster_boost.rules:176-199)
ReadyRack_he   { Type = ResourceStorage; ResourceType = missile_part_he; MaxResources = &~/MODE_he/CELLS
                 ToggleOnResources = &~/MODE_he/CELLS; ToggleOffResources = 0; AnticipateMoreResourcesFrom = [MagStorage_HE]; DropResourcesWhenDestroyed = false }
RackAny_he     { Type = MultiResourceStorage; ResourceType = missile_part_he; ResourceStorages = [ReadyRack_he]; ToggleOnResources = 1; ToggleOffResources = 0 }
MagCanLoad_he  { Type = MultiResourceStorage; ResourceType = missile_part_he; ResourceStorages = [MagStorage_HE]
                 ToggleOnResources = &~/MODE_he/PARTS; ToggleOffResources = (&ToggleOnResources) - 1 }       // a família guarda >= 1 míssil DESTE modo
LoaderOn_he    { Type = MultiToggle; Toggles = [IsOperational, ModeToggle_he, { Toggle = ReadyRack_he; Invert = true }]; Mode = All }   // só tripulado
Autoloader_he  { Type = ResourceConverter; OperationalToggle = LoaderOn_he; CheckResourceLimits = true
                 FromStorage = MagStorage_HE; FromQuantity = &~/MODE_he/PARTS; ToStorage = ReadyRack_he; ToQuantity = 1
                 Interval { BaseValue = &~/MODE_he/RELOAD
                            Modifiers [ { Type = BuffRemap; BuffType = Overclock; RemapFrom = [0, 1]; RemapTo = [1, &~/OVERCLOCK/RELOAD_FACTOR]; ModificationMode = Divide } ] } }
                 // modos P.E.M.: RemapTo = [1, 1.2]; modo nuclear: o mesmo bloco SEM a lista Modifiers

// (3) EXPLORAÇÃO ENTRE MODOS: atraso de troca por modo = uma recarga completa do modo em que se ENTRA (vale também no meio da salva)
ModeOn_he         { Type = ToggleTrigger; Toggle = ModeToggle_he; TriggerWhenOn = true; TriggerWhenOff = false }
ModeSwitchDelay_he { Type = Timer; StartTrigger = ModeOn_he; StartExpired = true
                     Duration { BaseValue = (&~/MODE_he/CELLS) * (&~/MODE_he/RELOAD); Modifiers [ o mesmo BuffRemap Divide (nenhum no nuclear) ] } }

// (3b) CÉLULAS JÁ CHEIAS (variante prefilled_switch, lançadores com overclock, modos afetados pelo overclock): células cheias na troca esperam a recarga SEM overclock
PrefilledSwitch_he { Type = TriggerProxy; ComponentID = ModeOn_he; ProxyToggle = ReadyRack_he }        // padrão WasOperationalOverclockDisabled de base_part_overclock.rules
PrefilledDelay_he  { Type = Timer; StartTrigger = PrefilledSwitch_he; StartExpired = true; Duration = (&~/MODE_he/CELLS) * (&~/MODE_he/RELOAD) }   // sem Modifiers

// (4) SALVA PARCIAL quando o paiol da família fica seco por DRY_DELAY (DryFlush com espera; MODE_k { DRY_DELAY = (&CELLS) * (&RELOAD) })
DryPending_he { Type = MultiToggle; Toggles = [RackAny_he, { Toggle = MagCanLoad_he; Invert = true }]; Mode = All }
DryWait_he    { Type = ValueTween; IsOnToggle = DryPending_he; OnTweenDuration = &~/MODE_he/DRY_DELAY; OffTweenDuration = 0.1 }   // ShellChangingValueTween do chaingun
DryFlush_he   { Type = ThresholdToggle; ValueFrom = DryWait_he; MinAmount = 100% }                                                  // IsShellFullyOpen do chaingun
CanFire_he   { Type = MultiToggle; Toggles = [ReadyRack_he, DryFlush_he]; Mode = Any }
RackReady_he { Type = MultiToggle; Toggles = [ModeToggle_he, ModeSwitchDelay_he, PrefilledDelay_he, CanFire_he]; Mode = All }
HasMissiles_he { Type = MultiToggle; Toggles = [ModeToggle_he, { Type = MultiToggle; Toggles = [MagCanLoad_he, RackAny_he]; Mode = Any }]; Mode = All }
// ... repete (2)-(4) por modo
RackReady      { Type = MultiToggle; Toggles = [RackReady_he, RackReady_cluster, ...]; Mode = Any }
HasMissiles    { Type = MultiToggle; Toggles = [HasMissiles_he, ...]; Mode = Any }          // HighPriorityPrerequisites do PartCrew + indicador NoMissiles
FirePermission { Type = MultiToggle; Toggles = [RackReady, FireModeToggle]; Mode = All }

// (5) TORRE (completa: proxy de emissor para a mira, colisor IsHigh preso à torre)
Turret { Type = TurretWeapon; Location = [pivô]; OperationalToggle = IsOperational; AutoFireToggle = AutoFireToggle
         FireInterval = &~/RIPPLE; FirePermissionToggle = FirePermission
         FiringArc = 360d; RotateSpeed = 75d; FireThresholdAngle = 25d
         AllowFireWithBlockedLOS = true; IgnoreFriendlyShipLowLOSChecks = true
         Emitter = TargetEmitterProxy                           // cannon_deck.rules:617 "only used for targeting"
         AIFirepowerRating = &~/Part/StatsByCategory/0/Stats/DamagePerSecond
         AutoTargets [ { TargetType = ShipParts; Toggle = AutoTargetToggle; EnableInDirectControlMode = true } ] }
TurretCollider { Type = CircleCollider; ChainedTo = Turret; Radius = 1.25; IsHigh = true }
TargetEmitterProxy { Type = EmitterProxy; ComponentID = Emitter_0; ChainedTo = Turret }   // Emitter_0 do Fire_k ATIVO (cannon_deck.rules:895, T/bsgen/guns.py)

// (6) BLOCO DE DISPARO POR MODO (só um ativo): ShootCycle DENTRO do bloco, ModeRange por modo (corrige a salva em sequência do Iara/torpedo, D-B2)
Fire_he { Type = ToggledComponents; Toggle = ModeToggle_he; IncludeInBlueprints = true
  Components {
    ShootCycle     { Type = ModeCycle; ModeRange = [0, 15]; IncrementTrigger = Turret; StartingMode = 15 }
    ShootTrigger_0 { Type = ModeTrigger; Mode = ShootCycle; TriggerInModes = [0] }           // ... _15
    Emitter_0 { Type = BulletEmitter; ChainedTo = Turret; GetTargetFrom = Turret; FireTrigger = ShootTrigger_0; OperationalToggle = IsOperational
                Location = [célula 15 na ordem de enchimento]                               // LIFO: a última célula cheia dispara primeiro
                Bullet = &<../../shots/bs_msl_twin_he/bs_msl_twin_he.rules>; ResourceStorage = ReadyRack_he; ResourcesUsed = 1
                TargetLeadPrediction = false; Spread = [-4d, 4d]; Recoil = 0 }
    // Emitter_1..15 : Emitter_0 { Location = ...; FireTrigger = ShootTrigger_i }
    // os emissores de cassete da Tocandira acrescentam: Burst = 2; BurstDelay = 2/30 (UseResourcePerShotInBurst padrão false -> 1 unidade das células por par)
    EmitterAny     { Type = MultiTrigger; Triggers = [Emitter_0, ..., Emitter_15] }
    CellsPodL      { Type = ResourceSprites; ChainedTo = Turret; Rotation = 90d; Location = [...]; Layer = "roof_turrets"
                     ResourceStorage = ReadyRack_he; RangeLow = 0; RangeHigh = 8; HasZeroResourceSprite = true; ResourceLevels [ 9 entradas ] }
    CellsPodR : CellsPodL { Location = [...]; RangeLow = 8; RangeHigh = 16 }
    ReloadProgressBar { Type = ProgressBar; OperationalToggle = IsOperational; ShowProgressFor = ReadyRack_he }   // sem ValueRange: as células fornecem o enchimento 0..1 (shield_gen_small.rules)
    LaunchEffect_i { Type = TriggeredEffects; ChainedTo = Emitter_i; Trigger = Emitter_i; MediaEffects [ clarão (Upper1), sopro (Upper), som de lançamento ] }
  } }

// (7) CUSTOS DO OVERCLOCK (base_*_overclock dá IsOverclocked / HEAT_TARGET_STORAGE / OverclockReset)
Overclock_LoadHeat_he { Type = ResourceChange; OperationalToggle = IsOverclocked; Trigger = Autoloader_he
                        ResourceStorage = &~/Part/^/0/HEAT_TARGET_STORAGE; Amount = (&~/OVERCLOCK/HEAT_PER_PART) * (&~/MODE_he/PARTS) * (&~/HEAT_TO_RESOURCE) }
RackFullTrigger_he    { Type = ToggleTrigger; Toggle = ReadyRack_he; TriggerWhenOn = true; TriggerWhenOff = false }
Overclock_Vent_he     { Type = ResourceChange; OperationalToggle = IsOverclocked; Trigger = RackFullTrigger_he
                        ResourceStorage = MagStorage_HE; Amount = -(&~/MODE_he/VENT) }      // ResourceChange negativo de thruster_boost.rules:224
// calor constante: Overclock_ConstantHeatProducer (T/bsgen/common.py); o modo nuclear não tem LoadHeat nem Vent

// (8) COOK-OFF POR ARMAZENAMENTO, fora dos blocos alternados, ScorchedTrigger copiado AO PÉ DA LETRA (corrige D-C1)
// um par por armazenamento que guarda peças: o paiol da família (1 peça por recurso) e as células de cada modo da família (CELLS x PARTS peças);
// BaseValue = valor da família com estoque cheio x peças do armazenamento / cookoff.parts_full, então cada peça guardada vale valor/parts_full (Caipora A.E.: 637,5 op + 212,5 est)
ScorchedTrigger  { Type = ToggleTrigger; Toggle = ScorchedToggle; TriggerWhenOn = false; TriggerWhenOff = true }   // missile_launcher_he.rules:271-276
ScorchedEffects_Mag_HE  { Type = TriggeredEffects; Trigger = ScorchedTrigger; FactorHitEffectsWith = MagStorage_HE; HitEffects = &../DestroyedEffects_Mag_HE/HitEffects }
DestroyedEffects_Mag_HE { Type = DeathEffects; OperationalToggle = ScorchedToggle; FactorHitEffectsWith = MagStorage_HE     // armazenamento simples como fator: MissileStorage de missile_launcher_nuke.rules
                          HitEffects [ { Type = ExplosiveDamage; TotalDamage = { BaseValue = 40800; EffectScaleExponent = 1 }; Radius = 5; StatusType = cosmoteer.fire     // 61200 x 64 / 96
                                         StatusChancePerNDamage = 50%; StatusValue = 1; StatusValueType = Interpolated; NDamage = 1000; CrewKillChance = 30% }
                                       { Type = ExplosiveDamage; TotalDamage = { BaseValue = 13600; EffectScaleExponent = 1 }; Radius = 4; Filter { OperationalHealth = false; StructuralHealth = true } } ] }
ScorchedEffects_Rack_he / DestroyedEffects_Rack_he { ... FactorHitEffectsWith = ReadyRack_he; TotalDamage 20400 / 6800 }      // 61200 x (16 x 2) / 96
// ... o mesmo par para ReadyRack_cluster, ReadyRack_limpet, ReadyRack_torpedo (2 x 6 peças: 7650 / 2550); paiol cheio + células A.E. cheias = 61200 + 20400
// família térmica: despejo GridStatusApplication cosmoteer.heat (Filter { Self = true }); família P.E.M.: ExplosiveResourceDrain de bateria; família nuclear: explosão grande

// PLANO B se a trava se comportar como um limiar puro (teste T02), com os mesmos tempos (NGEN §14.1):
// IsSalvoActive { Type = Timer; StartTrigger = Turret; ResetTrigger = Turret; Duration = RIPPLE x 1.5; StartExpired = true }
// RackFull_k { Type = MultiResourceStorage; ResourceStorages = [ReadyRack_k]; ToggleOnResources = CELLS; ToggleOffResources = CELLS - 1 }
// CanFire_k = Any[RackFull_k, All[IsSalvoActive, RackAny_k], DryFlush_k]

```

## 5. Tipos de míssil

**Núcleo comum.** Núcleo de míssil seguro para o convés (todo míssil, filho, isca e carga): `Hit { Type = SimpleHit (carga: PenetratingHit); FriendlyShipLowCollisions = false; FriendlyShipHighCollisions = false; SourcePartCollisionDelay = 1.5 / (&/Simulation/PhysicsUpdatesPerSecond) }`; `TargetHoming { TurnVelocity; Delay; VelocityCompensation = 60% }` SEM `AvoidanceRaycastDistance` (`AvoidsFriendlies` no padrão, teste T07); `SameShipRetarget`; `Acceleration` + `NegativeAcceleration [-90, 0]` em [0, .75] com `Direction = FrameOfReferenceVelocity`; `DeathByLifetime`; `Targetable { TargetCategory = "missile"; OnDeath = &../Hit/HitFriendly }` (abatido = apaga, sem dano em área); explosões SEM `Friendlies = true`; todo número escalável escrito como `{ BaseValue = X; EffectScaleExponent = 1 }`; sprite `missile_he.png` do jogo base escalado (`RenderBucket` BulletUpper3) + brilho na cor do tipo (BulletUpper4) + `missile_he_thruster_plume_light` (Upper4); nunca as partículas de propulsor dos buckets Lower (ficariam escondidas sob o nosso teto).

| # | Codinome | Míssil (en / pt-BR) | Munição | Lançadores | Brilho |
|---|---|---|---|---|---|
| 0 | Jararaca | High-Explosive Missile / Míssil Alto-Explosivo | `missile_part_he` | Tocandira, Caipora, Mula-sem-Cabeça | #FFB000 âmbar |
| 1 | Piranha | Cluster Missile (Transformer) / Míssil de Submunições | `missile_part_he` | Caipora, Mula-sem-Cabeça | #FFE45C amarelo, nariz segmentado em pétalas |
| 2 | Carrapato | Limpet Missile / Míssil Grudento | `missile_part_he` | Caipora, Mula-sem-Cabeça | #FF3B30 vermelho, carga piscando |
| 3 | Taturana | Napalm Missile / Míssil de Napalm | `missile_part_thermal` | Tocandira, Caipora, Mula-sem-Cabeça | #FF6A1A laranja |
| 4 | Poraquê | EMP Missile / Míssil P.E.M. | `missile_part_emp` | Caipora, Mula-sem-Cabeça | #4FC3FF azul, anel de bobina |
| 5 | Boto | Decoy Torpedo / Torpedo com Iscas | `missile_part_he` | Caipora, Mula-sem-Cabeça | #F4F7FF nariz branco |
| 6 | Iara | Nuclear Torpedo / Torpedo Nuclear | `missile_part_nuke` | Mula-sem-Cabeça | #7CFF6B faixa verde fina |

### 0. Jararaca: High-Explosive Missile / Míssil Alto-Explosivo

*Por que o nome:* a víbora: rápida, direta, mordida letal.

- **Mecânica.** `SimpleHit`; `HitOperational` = [ `ExplosiveDamage { TotalDamage = { BaseValue = X; EffectScaleExponent = 1 }; Radius = r }` (sem incêndio, sem `Friendlies`), `Impulse` ]; `HitStructural = &HitOperational`; `HitShield = &HitOperational` (formato do `missile_he` do jogo base).
- **Especial.** O míssil de referência e o 'míssil normal' do SW:ACD. Uma corrente de ogivas de alvo único; a salva pesada de 48 mísseis da Mula é a melhor ferramenta de saturação de pontos de defesa no modelo de referência.
- **Contra-jogada.** Ponto de defesa e CIWS (triagem de alvo único); escudos absorvem a explosão na borda da bolha; blindagem segura explosões.
- **Plano B (sem mudar números).** Não precisa, além dos testes comuns de voo sobre o convés (T06/T07).
- **Risco.** BAIXO

| Lançador | ID do projétil | Munição/míssil | Velocidade / acel. / giro | Alcance | Atraso da mira | HP | Voo até o alcance máximo | Dano | Efetivo/míssil | Efetivo/quadro | Por equivalente de munição |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira (Muriçoca) | `rafaeltessaro.bs_msl_box_he` | 0,5 A.E. | 55 / 85 / 300 | 300 | 0,15 | 380 | 2,09 s | `ExplosiveDamage 1600; Radius 1.5; Impulse 15` | 800,0 | 264,5 | 800,0 |
| Caipora | `rafaeltessaro.bs_msl_twin_he` | 2,0 A.E. | 45 / 65 / 230 | 400 | 0,15 | 1.050 | 2,88 s | `ExplosiveDamage 7000; Radius 3.0; Impulse 60` | 3.500,0 | 328,2 | 875,0 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_he` | 2,0 A.E. | 45 / 60 / 200 | 600 | 0,15 | 2.200 | 3,78 s | `ExplosiveDamage 7500; Radius 3.5; Impulse 80` | 3.750,0 | 379,6 | 937,5 |

### 1. Piranha: Cluster Missile (Transformer) / Míssil de Submunições

*Por que o nome:* uma forma só na água, depois um cardume que arranca pedaços do alvo por todos os lados.

- **Mecânica.** Portador = o formato MIRV do Discord do SW em tipos do jogo base (SW `missile_discord.rules`:48-96, 170-172): grupo raiz `BURST { HitEffects [ { Type = SpawnBullets; Bullet = &~/CHILD; Count = K; Distance = [0, .8]; Arc = [-25d, 50d]; Spread = [-5d, 5d]; InheritVelocity = false; HealthFactor = { BaseValue = 1; EffectScaleExponent = 1 } } ] MediaEffects [clarão de pétalas] }`. Três gatilhos, nunca falha: `ProximityFuse { Type = DeathByEnemyProximity; Interval = .05; Range = 25; StartDelay = .4; DetectsShips = true; DetectsBullets = false; FactorEffectsWith = Targetable; OnDeath = &~/BURST }`; `TimedFuse { Type = DeathByLifetime; Lifetime = vida da classe; OnDeath = &~/BURST }`; `Hit { HitShield / HitOperational / HitStructural = &~/BURST }`. O portador NÃO tem ogiva. CHILD (mesma pasta, referência relativa como o nosso `flak_oc`): `Speed 40`; `Acceleration 100`; `TargetHoming { TurnVelocity = 120d/110d; Delay = .25 }` (mira fraca e tardia -> os filhos se abrem sobre várias peças); `SameShipRetarget`; `Magnet = ProximityAcceleration { Range = 30; Acceleration = 25; AccelerateTowardsShips = true; AccelerateTowardsEnemies = true; AccelerateTowardsFriendlies = false; AccelerateTowardsBullets = false }` (ímã do buzz droid, funciona até sem herdar o alvo); `Spacing = ProximityAcceleration { Range = 3; Acceleration = -10; AccelerateTowardsShips = false; AccelerateTowardsBullets = true; AccelerateTowardsBulletCategories = [missile]; AccelerateTowardsFriendlies = true; AccelerateTowardsEnemies = false }` (repulsão da mina do jogo base); `DeathByLifetime 2.5`; `Targetable { Health; "missile"; apaga }`; `SimpleHit` COM todas as opções de convés; `HitOperational` = `ExplosiveDamage` de raio pequeno + `Impulse 10`; um único sprite de brilho barato (desempenho).
- **Especial.** O míssil 'estilo Transformers' do usuário. Só abre a 25 m do casco (valor do Discord), então nunca 'se transforma' sobre o nosso próprio convés; os filhos saem a 40 m/s num cone de +-25 graus com mira fraca e tardia + ímã + espaçamento, então caem em várias peças. O HP total dos filhos >= HP do portador, então dividir nunca facilita a interceptação. Troca 10% do dano sustentado pelo espalhamento em várias peças e por gastar a munição do defensor; no modelo de referência LOCK passa quase tão bem quanto o A.E. contra um ponto de defesa ou CIWS (ver `balance_checks.interception`).
- **Contra-jogada.** Derrubar os portadores antes dos 25 m; flak de área de raio grande come os aglomerados de filhos (Pororoca r7, flak do jogo base); escudos pegam a ninhada inteira na bolha; blindagem segura as explosões pequenas.
- **Plano B (sem mudar números).** Q1 herança do alvo [INFERIDO, forte]: os filhos mantêm o ímã, então ainda chegam ao casco inimigo mais próximo - mesmo `Count`, dano e HP. Q2 nave de origem dos filhos desconhecida: opções de convés nos filhos de qualquer jeito; se um portador abrir sobre o nosso casco, `StartDelay` do `ProximityFuse` 0,4 -> 1,0 (não é número de balanceamento). Desempenho: tirar o brilho dos filhos e apagar o componente `Spacing` (só visual/espalhamento, o `Count` fica). `RandomizeTarget = true` continua num arquivo de experimento (nunca distribuído).
- **Risco.** MÉDIO (herança do alvo, nave de origem dos filhos, desempenho)

| Lançador | ID do projétil | Munição/míssil | Velocidade / acel. / giro | Alcance | Atraso da mira | HP | Voo até o alcance máximo | Dano | Efetivo/míssil | Efetivo/quadro | Por equivalente de munição |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Caipora | `rafaeltessaro.bs_msl_twin_cluster` | 2,0 A.E. | 45 / 65 / 230 | 400 | 0,15 | 1.050 | 2,88 s | `carrier_warhead 0; children 4; child_ExplosiveDamage 1575; child_radius 1.75; child_hp 300; child_total 6300; children_hp_pool 1200; proximity_range 25; child_turn_deg_s 120; child_speed 40; child_accel 100; child_homing_delay_s 0.25; child_lifetime_s 2.5` | 3.150,0 | 295,4 | 787,5 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_cluster` | 4,0 A.E. | 45 / 60 / 200 | 600 | 0,15 | 2.200 | 3,78 s | `carrier_warhead 0; children 6; child_ExplosiveDamage 2250; child_radius 2.0; child_hp 400; child_total 13500; children_hp_pool 2400; proximity_range 25; child_turn_deg_s 110; child_speed 40; child_accel 100; child_homing_delay_s 0.25; child_lifetime_s 2.5` | 6.750,0 | 339,6 | 843,8 |

### 2. Carrapato: Limpet Missile / Míssil Grudento

*Por que o nome:* o carrapato: morde, se agarra, e você só percebe tarde demais.

- **Mecânica.** Míssil `SimpleHit`: `HitOperational` / `HitStructural` = `{ Offset = [-0.4, 0]; HitEffects [ Damage d; SpawnBullets { Bullet = &~/CHARGE; Count = 1; Distance = 0; Spread = [0d, 0d]; InheritVelocity = false }; Impulse 20 ]; MediaEffects [clangor + clarão vermelho] }`; `HitShield` = só um `ExplosiveDamage` pequeno (não gruda numa bolha). CHARGE = a receita do buzz droid do SW em tipos do jogo base (SW `buzzdroid.rules`:37-44 ímã + :78-81 rastejar): `CirclePhysics .25 Density 1`; `Speed 12`; `Magnet ProximityAcceleration { Range = 8; Acceleration = 30; naves, inimigos }`; `Hit { Type = PenetratingHit; Penetration = 1000; PenetrationSpeed = 0.05; ShieldCollisions = { Shields = false; }; opções de convés; grupos Penetrating*/FinishedPenetrating* vazios }`; `Fuse = DeathByLifetime { Lifetime = 2.5; OnDeath = BLAST { ExplosiveDamage X r; CrewKillChance = 50% } }`; SEM `Targetable` (regra literal do usuário: abatido no voo = perdido; grudado = VAI explodir; também evita que o ponto de defesa da vítima atire no próprio casco, D-B4); `AnimatedSprite` vermelho piscando (BulletUpper3) + luz; numa salva, faróis vermelhos encadeados.
- **Especial.** Abatido no voo = perdido; acerta o casco = gruda e explode 2,5 s depois (`CrewKillChance` 50% castiga a tripulação que corre para consertar). O mesmo DPS sustentado do A.E., com outra sensação: uma contagem regressiva de faróis vermelhos.
- **Contra-jogada.** Derrubá-lo no voo (mesmo HP do A.E.); escudos (não gruda, só um estouro de 43%); blindagem de sacrifício come a carga; afastar a tripulação do farol.
- **Plano B (sem mudar números).** Mesma espoleta, explosão e raio em todos os passos: F1 tirar o ímã (broca pura); F2 status de peça próprio `rafaeltessaro.bs_limpet` (modelo `disruptor_drain`: `Layer = Part`; `ApplyNewInstance`; `TickInterval = 2.5`; `TickingEffects Damage`; `ParentMediaEffectsToShip`) aplicado por `StatusApplication { StatusDuration = 2.6 }` - só se o T14b provar o registro de status por mod + primeiro tick no `TickInterval` nas duas versões; F3 carga com `Speed` 0 e `Hit FrameOfReference = HitObject`; F4 último recurso: a mesma explosão no impacto. Variante isolada só do SW, `bs_msl_<l>_limpet_rep.rules`, com `Repeating { Count 1; InitialDelay 2.5; RequireHitPart true }` atrás de uma opção de build, conferida com `schema_check --extra SW` (nunca no caminho padrão). Variante opcional 'desarmável': `Targetable` 500/600 'missile' (desligada: o ponto de defesa travaria no próprio casco).
- **Risco.** MÉDIO-ALTO no comportamento (fixação), BAIXO na carga

| Lançador | ID do projétil | Munição/míssil | Velocidade / acel. / giro | Alcance | Atraso da mira | HP | Voo até o alcance máximo | Dano | Efetivo/míssil | Efetivo/quadro | Por equivalente de munição |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Caipora | `rafaeltessaro.bs_msl_twin_limpet` | 2,0 A.E. | 45 / 65 / 230 | 400 | 0,15 | 1.050 | 2,88 s | `impact_Damage 250; charge_ExplosiveDamage 6500; charge_radius 2.5; charge_CrewKillChance 50%; fuse_s 2.5; charge_targetable no (default); shield_pop_ExplosiveDamage 3000; shield_pop_radius 2.0` | 3.500,0 | 328,2 | 875,0 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_limpet` | 4,0 A.E. | 45 / 60 / 200 | 600 | 0,15 | 2.200 | 3,78 s | `impact_Damage 500; charge_ExplosiveDamage 14000; charge_radius 3.5; charge_CrewKillChance 50%; fuse_s 2.5; charge_targetable no (default); shield_pop_ExplosiveDamage 6500; shield_pop_radius 3.0` | 7.500,0 | 377,4 | 937,5 |

### 3. Taturana: Napalm Missile / Míssil de Napalm

*Por que o nome:* a lagarta de fogo: encostou, queima por muito tempo.

- **Mecânica.** `HitOperational` = [ `ExplosiveDamage` (explosão, SEM incêndio embutido: as chances interpoladas do `ExplosiveDamage` mudam entre 0.30.4 e 0.30.5, PN:19); `{ Type = StatusApplication; StatusType = cosmoteer.fire; StatusChance = { BaseValue = c; EffectScaleExponent = 1 }; StatusValue = v%; ValueType = Interpolated }` (padrão de `bullet_med.rules`:129-132 + `bullet_large_overclock_shrapnel.rules`:113-114); `{ Type = GridStatusApplication; StatusType = cosmoteer.heat; StatusValue = 0; StatusValuePool = H (literal, nunca APPLIED_HEAT_PER_MISSILE); ValueFalloff = 1; MaxCost = k; FalloffPadding = .5; EmptyTileCost = 1000; AllowDiagonals = true; Filter { Friendlies = false; TargetedFriendlies = true } }` (formato de `missile_thermal.rules`:128-139) ]; `HitStructural = &HitOperational`; `HitShield` = [ a explosão; `StatusApplication cosmoteer.heat` (valor bruto, `ApplyToAllHitPartTiles = true`; `DivideValueByPartArea = true`) ]. O 'respingo de gel' opcional (`GridStatusApplication cosmoteer.fire`) fica DESLIGADO até o teste T15 (valor bruto x interpolado num projétil não está provado). Nunca `UseContiguity` / `AllowVertexContiguity`.
- **Especial.** Incendiário de interior: fogo garantido na peça atingida + uma reserva de calor que continua acendendo incêndios (5-50% a cada 0,25 s acima de 350 de calor). Dano direto fraco; inútil em blindagem e estrutura (não inflamáveis).
- **Contra-jogada.** Extintores (-1 incêndio por unidade + `fire_foam` com 100% de resistência a fogo por 3-15 s), o reparo leve da tripulação esfria o calor, cintos de blindagem, escudos (só o calor do gerador).
- **Plano B (sem mudar números).** Se o `StatusApplication` de fogo se comportar mal: `ApplyToAllHitPartTiles = true` na mesma entrada. O fogo em gel por `GridStatusApplication` só depois do T15. A reserva de calor sozinha ainda reacende (mesmos números).
- **Risco.** BAIXO

| Lançador | ID do projétil | Munição/míssil | Velocidade / acel. / giro | Alcance | Atraso da mira | HP | Voo até o alcance máximo | Dano | Efetivo/míssil | Efetivo/quadro | Por equivalente de munição |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira (Taturana-mirim) | `rafaeltessaro.bs_msl_box_napalm` | 0,5 T. | 55 / 85 / 300 | 300 | 0,15 | 380 | 2,09 s | `blast_ExplosiveDamage 600; blast_radius 1.5; fire_StatusChance 0.6; fire_StatusValue_interpolated 40%; heat_StatusValuePool 500; heat_MaxCost 1; shield_heat 50; shield_blast 600` | 300,0 | 99,2 | 200,0 |
| Caipora | `rafaeltessaro.bs_msl_twin_napalm` | 2,0 T. | 45 / 65 / 230 | 400 | 0,15 | 1.050 | 2,88 s | `blast_ExplosiveDamage 3000; blast_radius 2.5; fire_StatusChance 1.0; fire_StatusValue_interpolated 60%; heat_StatusValuePool 1600; heat_MaxCost 3; shield_heat 160; shield_blast 3000` | 1.500,0 | 140,6 | 250,0 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_napalm` | 4,0 T. | 45 / 60 / 200 | 600 | 0,15 | 2.200 | 3,78 s | `blast_ExplosiveDamage 6000; blast_radius 3.5; fire_StatusChance 1.0; fire_StatusValue_interpolated 70%; heat_StatusValuePool 4800; heat_MaxCost 4; shield_heat 480; shield_blast 6000` | 3.000,0 | 150,9 | 250,0 |

### 4. Poraquê: EMP Missile / Míssil P.E.M.

*Por que o nome:* o peixe-elétrico da Amazônia: um choque e tudo apaga.

- **Mecânica.** `HitOperational` = [ `{ Type = ExplosiveResourceDrain; ResourceType = battery; TotalDrain = { BaseValue = D; EffectScaleExponent = 1 }; Radius = R; Slices = 1; Filter { Ships = true; Shields = true } (SEM Friendlies); MediaEffectsOnDrainFactor = .0005; MediaEffectsOnDrain [chiado/dreno do missile_emp do jogo base] }`; `{ Type = Damage; Damage = d }`; `{ Type = ExplosiveDamage; TotalDamage = s; Radius = rs; Filter { OperationalHealth = false; StructuralHealth = true } }`; carona opcional `StatusApplication cosmoteer.disruptor_drain` (`StatusDuration 3`, `StatusValue .1`, não conta) ]; `HitShield = HitStructural = &HitOperational` (formato de `missile_emp.rules`:151-196, escalado para 1.500 de dreno por peça P.E.M.).
- **Especial.** Apoio / quebra-escudo contra naves que dependem de bateria (jogo base, SW:ACD). As armas do Bullet Strike não têm bateria e são imunes de propósito.
- **Contra-jogada.** Blindagem absorve dreno em área (`ExplosiveResourceDrainSink` 2.000 por quadro), naves sem bateria nem sentem, derrubá-lo como qualquer míssil.
- **Plano B (sem mudar números).** Tirar a carona `disruptor_drain` se ela se comportar mal (nunca contou). Se o dreno na borda da bolha não chegar ao gerador: acrescentar um `ResourceDrain { TreatShieldAsPart = true }` de peça única com o mesmo total.
- **Risco.** BAIXO

| Lançador | ID do projétil | Munição/míssil | Velocidade / acel. / giro | Alcance | Atraso da mira | HP | Voo até o alcance máximo | Dano | Efetivo/míssil | Efetivo/quadro | Por equivalente de munição |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Caipora | `rafaeltessaro.bs_msl_twin_emp` | 2,0 P.E.M. | 45 / 65 / 230 | 400 | 0,15 | 1.500 | 2,88 s | `battery_TotalDrain 3000; drain_radius 8; direct_Damage 300; structural_ExplosiveDamage 2000; structural_radius 2.0; sw_shield_hp_per_missile 7500.0` | 1.300,0 | 121,9 | 130,0 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_emp` | 3,0 P.E.M. | 45 / 60 / 200 | 600 | 0,15 | 2.800 | 3,78 s | `battery_TotalDrain 4500; drain_radius 10; direct_Damage 400; structural_ExplosiveDamage 3000; structural_radius 2.5; sw_shield_hp_per_missile 11250.0` | 1.900,0 | 95,6 | 126,7 |

### 5. Boto: Decoy Torpedo / Torpedo com Iscas

*Por que o nome:* o boto do rio, que toma outras formas para enganar: uma ogiva se esconde entre iscas.

- **Mecânica.** Cadeia em dois estágios no padrão do nuclear do jogo base: ESTÁGIO DE LANÇAMENTO (1,5 s; `BoxPhysics [2.0, .65]`; `TargetHoming 90d Delay .3`; `Acceleration 12`, sem `LinearDamping`; `Targetable` HP "missile" que apaga; `Hit = &<arquivo da ogiva>/Components/Hit`, para um impacto precoce ainda detonar), cujo `Deploy = DeathByLifetime { Lifetime = 1.5; FactorEffectsWith = Targetable; OnDeath { HitEffects [ SpawnBullets { Bullet = &~/WARHEAD; Count = 1; InheritVelocity = true; HealthFactor {...} }; SpawnBullets { Bullet = &~/DECOY; Count = N; Distance = [0.5, 1.5]; Arc = [-60d, 120d]; Spread = [-10d, 10d]; InheritVelocity = true } ] } }`. WARHEAD (ogiva): `Speed 0` (herda), mira 90d, `Acceleration 12`, `SimpleHit`; `HitOperational` = [ `ExplosiveDamage` operacional (`ExpandDuration .5`; `ExpandStartRadius 1.5`; `ExpandLoss 100%`; filtro só operacional), `ExplosiveDamage` só estrutural ] (formato de `missile_nuke_stage1.rules`:141-160, literais, sem `Friendlies`); `HitShield` = só o bloco operacional. DECOY (isca): `Speed 0`, `Box [1.2, .4]`, mira 70d `Delay .4`, `Acceleration 12`, `Spacing ProximityAcceleration` (`Range 3.5`, -6, [missile], aliados), `Lifetime 9`, `Targetable` HP "missile", `SimpleHit` com as opções de convés e SEM `HitEffects` (só um estalo pequeno de mídia).
- **Especial.** O 'torpedo (maior, único)' do SW: lento, resistente (um gatilho do Tamanduá de 3 x 2.000 não mata uma ogiva de fim de jogo de 6.500 HP) e escondido entre iscas que gastam tiros de alvo único dos pontos de defesa e as reservas da flak.
- **Contra-jogada.** Flak de área (as iscas não enganam uma explosão grande); um Tamanduá precisa de dois gatilhos por ogiva de fim de jogo; naves rápidas fazem a curva por dentro dele (90 graus/s); escudos recebem a explosão operacional.
- **Plano B (sem mudar números).** Se dois `SpawnBullets` numa mesma lista `OnDeath` se comportarem mal (T17): torpedo de um estágio só + iscas disparadas por um segundo `BulletEmitter` por célula de torpedo (`Burst` N, `BurstDelay 0.1`, sem `ResourceStorage`) - mesmas contagens e HP.
- **Risco.** BAIXO-MÉDIO (dois `SpawnBullets` num `OnDeath`)

| Lançador | ID do projétil | Munição/míssil | Velocidade / acel. / giro | Alcance | Atraso da mira | HP | Voo até o alcance máximo | Dano | Efetivo/míssil | Efetivo/quadro | Por equivalente de munição |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Caipora | `rafaeltessaro.bs_msl_twin_torpedo` | 6,0 A.E. | 30 / 12 / 90 | 400 | 0,3 | 4.500 | 6,04 s | `warhead_operational 18000; op_radius 4.0; warhead_structural 6000; struct_radius 5.0; launch_stage_s 1.5; decoys 4; decoy_hp 600; decoy_damage 0` | 12.000,0 | 282,7 | 1.000,0 |
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_torpedo` | 12,0 A.E. | 30 / 12 / 90 | 600 | 0,3 | 6.500 | 7,81 s | `warhead_operational 36000; op_radius 5.0; warhead_structural 12000; struct_radius 6.0; launch_stage_s 1.5; decoys 6; decoy_hp 700; decoy_damage 0` | 24.000,0 | 330,6 | 1.000,0 |

### 6. Iara: Nuclear Torpedo / Torpedo Nuclear

*Por que o nome:* a sereia do rio: bonita, lenta, e quem a encontra não volta.

- **Mecânica.** A mesma cadeia e o mesmo arquivo de isca compartilhado do Boto de fim de jogo; `HitOperational` da ogiva = [ `ExplosiveDamage` 120.000 r9 (`ExpandDuration .8`; `ExpandStartRadius 2`; `ExpandLoss 100%`; `ImpulsePerNDamage 10`; `NDamage 1000`; filtro só operacional); `ExplosiveDamage` 40.000 r7 só estrutural ] (literais, SEM `Friendlies`); `MediaEffects` = o cogumelo da Boiúna (partículas de `BS/shots/bs_shot_nuke_howitzer_nuclear`). No lançador: o `Autoloader_nuclear` NÃO tem o `BuffRemap` de overclock, nem calor de overclock, nem descarte (o overclock nunca encurta uma recarga nuclear - regra da Boiúna).
- **Especial.** O 'nuclear' do SW: só na Mula, em `bs_limit_nuke` com a Boiúna, nunca acelerado pelo overclock. Sozinho morre para a flak de área, então precisa ser MASCARADO: lance o par de Iara primeiro e dispare uma salva pesada de mísseis A.E. 1-3 s depois, para os dois chegarem juntos.
- **Contra-jogada.** Qualquer flak de área sozinha (Tamanduá, Pororoca, flak do jogo base), dois pontos de defesa do jogo base; escudos comem a carga inteira na bolha; é lento (7,8 s até 600 m) e visível.
- **Plano B (sem mudar números).** O mesmo plano B das iscas do Boto. Se os `CategoryLimits` falharem no 0.30.5 RC: distribuir sem limites, como a Boiúna/Mapinguari (custo, 8 peças nucleares e a recarga de 20 s ainda seguram).
- **Risco.** BAIXO (mais o teste da vaga de limite)

| Lançador | ID do projétil | Munição/míssil | Velocidade / acel. / giro | Alcance | Atraso da mira | HP | Voo até o alcance máximo | Dano | Efetivo/míssil | Efetivo/quadro | Por equivalente de munição |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Mula-sem-Cabeça | `rafaeltessaro.bs_msl_quad_nuclear` | 8,0 nuclear | 30 / 12 / 90 | 600 | 0,3 | 6.500 | 7,81 s | `warhead_operational 120000; op_radius 9.0; warhead_structural 40000; struct_radius 7.0; launch_stage_s 1.5; decoys 6; decoy_hp 700; decoy_damage 0` | 80.000,0 | 266,6 | 1.111,1 |

## 6. Recursos e fábricas

NENHUM recurso novo e NENHUMA fábrica nova na v1. Todo míssil usa uma peça de míssil do jogo base, como o usuário pediu ('pega o padrão que já tem no jogo'). As fábricas do jogo base abastecem os lançadores; as peças podem ser compradas ou recuperadas; os lançadores do SW:ACD usam os mesmos IDs (`missile_part_he/emp/nuke`), então um jogo com os dois mods divide as fábricas e nada colide. O napalm usa `missile_part_thermal` (do jogo base desde o 0.30.0, nunca usado pelo SW) e tem a sua própria cadeia de cobre + enxofre. O Iara usa `missile_part_nuke`, nunca a cadeia do Projétil Nuclear da Boiúna.

| Peça | Compra | Pilha | Explode (cook-off) | Usada por | Fábrica |
|---|---|---|---|---|---|
| `missile_part_he` | 8 | 10 | sim | he, cluster, limpet, torpedo | `cosmoteer.factory_he` (3x3, ferro + enxofre + 125 de bateria/peça; 200 peças/min) |
| `missile_part_thermal` | 12 | 10 | sim | napalm | `cosmoteer.factory_thermal` (3x3, cobre + enxofre; 200 peças/min) |
| `missile_part_emp` | 20 | 10 | não | emp | `cosmoteer.factory_emp` (3x4, ferro + cobre; 120 peças/min) |
| `missile_part_nuke` | 36 | 10 | sim | nuclear | `cosmoteer.factory_nuke` (4x4, ferro + urânio; 120 peças/min) |

- Dica para o jogo: 1 Fábrica de mísseis A.E. alimenta 2 Caiporas ou 5 Tocandiras; uma Mula precisa de 1,8 Fábrica A.E. (2,6 com o Estouro da Boiada); uma Mula com Poraquê precisa de 2,3 Fábricas P.E.M.
- Os lançadores não usam energia (regra do mod para as armas); as fábricas do jogo base usam - é a economia de mísseis do jogo base.
- **Eficiência das fábricas.** DECIDIDO: aceitar a economia de mísseis do jogo base. Uma fábrica A.E. do jogo base alimenta ~5.300-6.300 de DPS efetivo dos nossos mísseis A.E., contra ~1.270 por fábrica na cadeia de carregadores das nossas armas (4-5x). Por crédito de munição e por viagem da tripulação, os mísseis ficam iguais ou mais famintos, e pagam com interceptação, tripulação, risco de cook-off e recargas tripuladas longas. O SW:ACD e o jogo base usam as mesmas peças com a mesma eficiência, então um míssil do Bullet Strike mais faminto de fábrica pareceria fraco ao lado deles. O dano NÃO é a alavanca. Alavanca guardada para depois (v2): um recurso `rafaeltessaro.bs_msl_canister` (peças do jogo base + 1 Carregador Padrão, prensa sem energia) aumentaria a carga das fábricas sem mexer em nenhum número de dano.
- Opção v2: `rafaeltessaro.bs_msl_canister` (pilha 4, empacotado a partir de 4 `missile_part_he` + 1 `rafaeltessaro.bs_mag_std` por uma peça no estilo da Prensa de Carregadores) - só `parts_per_missile` e o ID do recurso mudariam.

## 7. Techs da Carreira

| ID da tech | Nível | Custo | Pré-requisitos | Libera |
|---|---|---|---|---|
| `rafaeltessaro.bs_msl_box` | 1 | 3.500 | `rafaeltessaro.bs_autocannon_20` | `rafaeltessaro.bs_msl_box`, `missile:he` |
| `rafaeltessaro.bs_msl_napalm` | 2 | 9.000 | `rafaeltessaro.bs_msl_box`, `cosmoteer.factory_thermal` | `missile:napalm` |
| `rafaeltessaro.bs_msl_twin` | 2 | 14.000 | `rafaeltessaro.bs_msl_box`, `cosmoteer.factory_he` | `rafaeltessaro.bs_msl_twin` |
| `rafaeltessaro.bs_msl_cluster` | 2 | 16.000 | `rafaeltessaro.bs_msl_twin` | `missile:cluster` |
| `rafaeltessaro.bs_msl_emp` | 2 | 12.000 | `rafaeltessaro.bs_msl_twin`, `cosmoteer.factory_emp` | `missile:emp` |
| `rafaeltessaro.bs_msl_limpet` | 3 | 22.000 | `rafaeltessaro.bs_msl_cluster`, `rafaeltessaro.bs_ammo_aphe` | `missile:limpet` |
| `rafaeltessaro.bs_msl_torpedo` | 3 | 25.000 | `rafaeltessaro.bs_msl_cluster` | `missile:torpedo` |
| `rafaeltessaro.bs_msl_twin-overclock` | 3 | 40.000 | `rafaeltessaro.bs_msl_twin`, `cosmoteer.heat_management` | `overclock:rafaeltessaro.bs_msl_twin` |
| `rafaeltessaro.bs_msl_quad` | 4 | 150.000 | `rafaeltessaro.bs_msl_torpedo`, `cosmoteer.control_room_large` | `rafaeltessaro.bs_msl_quad` |
| `rafaeltessaro.bs_msl_nuclear` | 4 | 110.000 | `rafaeltessaro.bs_msl_quad`, `rafaeltessaro.bs_nuclear`, `cosmoteer.factory_nuke` | `missile:nuclear` |
| `rafaeltessaro.bs_msl_quad-overclock` | 4 | 160.000 | `rafaeltessaro.bs_msl_quad`, `cosmoteer.heat_management` | `overclock:rafaeltessaro.bs_msl_quad` |
| `rafaeltessaro.bs_msl_box-overclock` (desligada) | 3 | 30.000 | `rafaeltessaro.bs_msl_box`, `cosmoteer.heat_management` | `overclock:rafaeltessaro.bs_msl_box` |

- 'missile:<tipo>' é um prefixo novo em `bs_data.career_techs` -> `ToggleChoicesUnlocked = [[bs_missile_type, N]]` (formato de `techs.rules`:118 do jogo base; espelha o 'ammo:' de `T/bs_data.py`). Uma liberação vale para todo lançador que lista a escolha.
- Os custos seguem a escada do mod: nível 1 1.000-3.500, nível 2 4.000-16.000, nível 3 20.000-50.000, nível 4 60.000-170.000 (Mapinguari 150.000, o overclock dele 160.000).
- Âncoras do jogo base (`RJ/modes/career/techs.rules`): `factory_he` 7.500 exige `missile_launcher_he` (5.000, :112-119, :382-389); `factory_thermal` 9.000 exige `missile_launcher_thermal` (+ `heat_management`); `factory_emp` 10.000 exige `missile_launcher_emp`; `factory_nuke` 15.000 exige `missile_launcher_nuke` + `factory_uranium`; `control_room_large` 10.000; `heat_management` 5.000.
- Peças A.E. podem ser compradas nas estações antes de pesquisar a `factory_he`, então a Tocandira serve desde o nível 1.
- O Carrapato exige a nossa tech de munição Perfurante-Explosiva (granadas de espoleta retardada) - ligação temática; o torpedo nuclear exige a nossa tech `bs_nuclear` (Boiúna) e a fábrica de mísseis nucleares do jogo base.
- Construir e Batalhar: os três lançadores entram em `BB_WHITELIST` e em `buildbattle_techs` (percorre `GUNS + DEFENSES + LAUNCHERS`): a Tocandira, de início de jogo, entra na lista branca mais uma tech de munição sempre oferecida, `bs_bb_bs_msl_box_ammo` (custo 5.000, `FundsThresholdBeforeOffered 0`, `ResourcesUnlocked` = as suas `missile_part_he` / `missile_part_thermal`; `PartsUnlocked` repete a peça da lista branca, como a `cosmoteer.missile_launcher_he` do jogo base faz com a `factory_he` da lista branca), porque o modo Construir e Batalhar do jogo base só libera esses recursos com `cosmoteer.missile_launcher_he` / `_thermal` (`techs_buildbattle.rules`:54, :301); a Caipora e a Mula são techs de 5.000 cujo `ResourcesUnlocked` traz as suas famílias.

## 8. Verificações de balanceamento

Convenções: DPS efetivo = direto + 50% do explosivo, por célula de tamanho (quadro); equivalente de munição = créditos / 4; viagens de tripulação = peças/min / 10; fábricas sem bônus (A.E./térmica 200, P.E.M./nuclear 120 peças/min); 1 de dreno numa bolha do SW = 2,5 de HP de escudo; ciclo = unidades x recarga + duração da salva.

### 8.1 DPS por quadro contra as nossas armas de convés e o lançador do jogo base

Faixas das armas: início Marimbondo 260 / Mangangá 270 / Carcará 250 por quadro a 220-250 m; meio Saci 332,5 / Cigarra 340 / Tambor 312,5 / Boitatá 266,7 a 300-340 m; fim Furacão 375 / Trovão 380 / Curupira 270 / Boiúna 266,7 / Mapinguari 381 a 500-600 m. Lançador A.E. do jogo base: 938 de DPS explosivo por quadro (469 efetivo), 2 tripulantes, só na borda do casco.

| Lançador | Modo | Ciclo s | Alfa (expl.) | DPS efetivo | Efetivo/quadro | Expl./quadro | x 938 do jogo base | Efetivo/tripulante | Por equivalente de munição | x A.E. | OC efetivo/quadro |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira | he | 9,073 | 19.200 | 1.058,0 | 264,5 | 529,0 | 0,56 | 1.058,0 | 800,0 | 1,0 | 381,4 |
| Tocandira | napalm | 9,073 | 7.200 | 396,8 | 99,2 | 198,4 | 0,21 | 396,8 | 200,0 | 0,375 | 143,0 |
| Caipora | he | 18,96 | 112.000 | 2.953,6 | 328,2 | 656,4 | 0,7 | 1.476,8 | 875,0 | 1,0 | 467,6 |
| Caipora | cluster | 18,96 | 100.800 | 2.658,2 | 295,4 | 590,7 | 0,63 | 1.329,1 | 787,5 | 0,9 | 420,8 |
| Caipora | limpet | 18,96 | 104.000 | 2.953,6 | 328,2 | 609,5 | 0,65 | 1.476,8 | 875,0 | 1,0 | 467,6 |
| Caipora | napalm | 18,96 | 48.000 | 1.265,8 | 140,6 | 281,3 | 0,3 | 632,9 | 250,0 | 0,429 | 200,4 |
| Caipora | emp | 18,96 | 32.000 | 1.097,0 | 121,9 | 187,5 | 0,2 | 548,5 | 130,0 | 0,371 | 143,3 |
| Caipora | torpedo | 9,433 | 48.000 | 2.544,2 | 282,7 | 565,4 | 0,6 | 1.272,1 | 1.000,0 | 0,861 | 421,1 |
| Mula-sem-Cabeça | he | 15,805 | 360.000 | 11.388,6 | 379,6 | 759,2 | 0,81 | 1.423,6 | 937,5 | 1,0 | 518,1 |
| Mula-sem-Cabeça | cluster | 10,6 | 216.000 | 10.188,7 | 339,6 | 679,2 | 0,72 | 1.273,6 | 843,8 | 0,895 | 486,5 |
| Mula-sem-Cabeça | limpet | 10,6 | 224.000 | 11.320,8 | 377,4 | 704,4 | 0,75 | 1.415,1 | 937,5 | 0,994 | 540,5 |
| Mula-sem-Cabeça | napalm | 10,6 | 96.000 | 4.528,3 | 150,9 | 301,9 | 0,32 | 566,0 | 250,0 | 0,398 | 216,2 |
| Mula-sem-Cabeça | emp | 10,6 | 48.000 | 2.867,9 | 95,6 | 150,9 | 0,16 | 358,5 | 126,7 | 0,252 | 112,6 |
| Mula-sem-Cabeça | torpedo | 9,68 | 192.000 | 9.917,4 | 330,6 | 661,2 | 0,7 | 1.239,7 | 1.000,0 | 0,871 | 490,8 |
| Mula-sem-Cabeça | nuclear | 20,007 | 320.000 | 7.997,3 | 266,6 | 533,2 | 0,57 | 999,7 | 1.111,1 | 0,702 | - |

- A.E. por quadro: Tocandira 264,5 (faixa de início 250-280), Caipora 328,2 (meio 312,5-340), Mula 379,6 (fim 375-381, = Mapinguari 381). Progressão: todo modo de meio de jogo <= 328,2 < A.E. de fim de jogo 379,6.
- Especiais como fração do A.E.: Piranha 0,90 (meio) / 0,895 (fim); Carrapato 1,00 / 0,99; Boto 0,86 / 0,87; Taturana e Poraquê são apoio (só o direto; dano contínuo e dreno não contam); Iara 266,6 por quadro = Boiúna 266,7.
- Contra o lançador do jogo base (938 de DPS explosivo por quadro): os nossos fazem 529,0 / 656,4 / 759,2 explosivo por quadro (0,56 / 0,70 / 0,81 x). Por que menos, mesmo sendo de convés: atiramos por cima do próprio casco de qualquer lugar, não precisamos de borda do casco e soltamos salvas grandes em sequência (alfa) que saturam os pontos de defesa; o número por quadro do jogo base não compra nada disso.
- DPS por tripulante: 1.058,0 / 1.476,8 / 1.423,6 (teto 1.600; jogo base 670-1.500).
- Créditos por DPS efetivo: Tocandira 2,93, Caipora 4,27, Mula 6,76 (armas de início 2,6-3,1, de meio 3,1-4,0, Mapinguari 6,38, Boiúna 6,44).
- Alfa (espetáculo, não sustentado): Tocandira 19.200 em 0,73 s, Caipora 112.000 em 2,0 s (estoura uma bolha grande do SW), Mula 360.000 em 3,1 s a cada 15,8 s - o mesmo dano que um Mapinguari faz em ~16 s, concentrado na frente, interceptável e limitado a 2 por nave.

### 8.2 Valor do overclock contra o custo

| Lançador | Modo | Ligado | DPS x | OC efetivo/quadro | Calor/míssil | Calor/s médio (pico) | Radiadores | Calor por +1 de DPS | Peças descartadas (fração) | Viagens/min em OC |
|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira | he | não | 1,442 | 381,4 | 100,0 | 220,7 (245,8) | 0,2 | 0,472 | 0 (0%) | 5,72 |
| Tocandira | napalm | não | 1,442 | 143,0 | 100,0 | 220,7 (245,8) | 0,2 | 1,259 | 0 (0%) | 5,72 |
| Caipora | he | sim | 1,425 | 467,6 | 850,0 | 1.122,0 (1.302,8) | 1,02 | 0,894 | 2 (6%) | 15,33 |
| Caipora | cluster | sim | 1,425 | 420,8 | 850,0 | 1.122,0 (1.302,8) | 1,02 | 0,994 | 2 (6%) | 15,33 |
| Caipora | limpet | sim | 1,425 | 467,6 | 850,0 | 1.122,0 (1.302,8) | 1,02 | 0,894 | 2 (6%) | 15,33 |
| Caipora | napalm | sim | 1,425 | 200,4 | 850,0 | 1.122,0 (1.302,8) | 1,02 | 2,086 | 2 (6%) | 15,33 |
| Caipora | emp | sim | 1,175 | 143,3 | 850,0 | 943,0 (1.062,3) | 0,86 | 4,906 | 2 (6%) | 12,64 |
| Caipora | torpedo | sim | 1,489 | 421,1 | 2.550,0 | 905,3 (922,6) | 0,82 | 0,727 | 0 (0%) | 11,37 |
| Mula-sem-Cabeça | he | sim | 1,365 | 518,1 | 800,0 | 3.465,7 (4.695,5) | 3,15 | 0,834 | 6 (6%) | 52,84 |
| Mula-sem-Cabeça | cluster | sim | 1,432 | 486,5 | 1.600,0 | 3.609,5 (4.150,0) | 3,28 | 0,819 | 4 (6%) | 55,14 |
| Mula-sem-Cabeça | limpet | sim | 1,432 | 540,5 | 1.600,0 | 3.609,5 (4.150,0) | 3,28 | 0,737 | 4 (6%) | 55,14 |
| Mula-sem-Cabeça | napalm | sim | 1,432 | 216,2 | 1.600,0 | 3.609,5 (4.150,0) | 3,28 | 1,843 | 4 (6%) | 55,14 |
| Mula-sem-Cabeça | emp | sim | 1,178 | 112,6 | 1.200,0 | 2.283,3 (2.550,0) | 2,08 | 4,478 | 3 (6%) | 34,0 |
| Mula-sem-Cabeça | torpedo | sim | 1,485 | 490,8 | 4.800,0 | 3.094,8 (3.188,0) | 2,81 | 0,644 | 0 (0%) | 44,17 |

- Recarga / 1,5 em todos os modos, menos P.E.M. (/ 1,2) e nuclear (nenhum) -> DPS sustentado x1,43 (Caipora) / x1,37 (A.E. da Mula); a cadência da salva, o dano e o alcance não mudam, então as contas de interceptação também não.
- Caipora em overclock 467,6 por quadro, Mula em overclock 518,1 por quadro (máximo 540,5, teto 550). O overclock de início de jogo está projetado (daria 381,4 por quadro), mas desligado.
- Calor por +1 de DPS efetivo 0,83-0,89 no A.E. (Tambor 0,71, Furacão 0,88), cobrado por peça carregada, mais o descarte (6,25% das peças da salva) - dois custos reais além do reset do overclock e da cadeia de cook-off.
- Os modos de torpedo pagam calor por peça carregada (Boto: 12 peças = 4.800 de calor por torpedo na Mula), mas não descartam; o Iara não paga nada, porque o overclock não faz nada nele.

### 8.3 Saturação dos pontos de defesa (uma salva; fração das ogivas que chegam ao casco)

Modelo do juiz (`VERDICT_balance` §2.6), ampliado: lançamento no alcance máximo, aceleração constante; latência de tiro do ponto de defesa 0,3 s, o ponto de defesa mantém o alvo (o impacto mais próximo) até ele morrer ou acertar; defesas de explosão aérea na cadência real dos gatilhos; LOCK = todas as explosões aéreas de um gatilho caem num alvo e pegam até `lock_catch` membros do aglomerado dele (filhos / iscas); RETARGET = cada explosão aérea escolhe um alvo novo (limite pessimista para os mísseis); os filhos nascem a 25 m com `HealthFactor`; as iscas do torpedo nascem a 1,5 s, metade voando logo à frente da ogiva. Cenários com várias defesas rodam todos os reparos em paralelo contra a mesma salva. Mira ideal, sem desperdício de tiro -> enxames reais passam mais.

Defesas: ponto de defesa do jogo base 180/tiro 15/s 200 m; Saci 95/tiro 14/s 300 m; PD4 do SW 1.250/tiro 6,67/s 250 m; Tatu reserva de 1.000 3/s 180 m; flak do jogo base reserva de 3.000 4/s 150 m; Tamanduá 3 x 2.000 por gatilho 1,67/s 250 m; Pororoca 2 x 4.000 por gatilho 1,5/s 320 m.

| Lançador | Modo | Ogivas | 1 PD | 2 PD | Saci | PD4 do SW | Tatu | Flak do jogo | Taman. LOCK | Taman. RETARGET | Poro. LOCK | Poro. RETARGET | Taman. + PD | Defesa de fim em camadas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira | he | 12 | 58% | 0% | 33% | 0% | 50% | 50% | 67% | 17% | 58% | 25% | 42% | 0% |
| Caipora | he | 16 | 88% | 44% | 94% | 0% | 88% | 31% | 62% | 0% | 62% | 31% | 56% | 0% |
| Caipora | cluster | 64 | 88% | 31% | 94% | 0% | 92% | 28% | 56% | 3% | 56% | 27% | 56% | 0% |
| Caipora | emp | 16 | 94% | 81% | 94% | 56% | 88% | 31% | 62% | 0% | 62% | 31% | 62% | 0% |
| Caipora | torpedo | 2 | 100% | 50% | 100% | 0% | 100% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| Mula-sem-Cabeça | he | 48 | 100% | 98% | 100% | 92% | 98% | 69% | 85% | 85% | 85% | 73% | 85% | 56% |
| Mula-sem-Cabeça | cluster | 96 | 100% | 88% | 100% | 77% | 98% | 58% | 75% | 73% | 71% | 53% | 75% | 23% |
| Mula-sem-Cabeça | emp | 16 | 100% | 94% | 100% | 88% | 94% | 56% | 75% | 75% | 75% | 56% | 75% | 38% |
| Mula-sem-Cabeça | torpedo | 4 | 100% | 100% | 100% | 75% | 100% | 75% | 50% | 50% | 50% | 50% | 50% | 0% |
| Mula-sem-Cabeça | nuclear | 2 | 100% | 100% | 100% | 50% | 100% | 50% | 0% | 0% | 0% | 0% | 0% | 0% |

(PD = ponto de defesa do jogo base.)

- INÍCIO: uma salva da Tocandira passa 58% por UM ponto de defesa do jogo base (meta 40-60%), 0% por dois; 380 HP = 3 tiros do ponto de defesa; 12 micromísseis com 1/15 s entre eles.
- A.E. DE MEIO contra um Tamanduá: 62% com LOCK, 0% com RETARGET - o modelo da CIWS decide quase tudo (teste T10).
- PIRANHA (meio): 88% contra um ponto de defesa do jogo base, 92% contra o Tatu, 56% contra o Tamanduá em LOCK: mais ou menos a fração do A.E. (dentro de ~6 pontos) com 90% do dano do A.E., espalhado por muitas peças; flak de raio grande é o contra dela.
- A.E. DA MULA: 56% das 48 ogivas passam pela defesa de fim de jogo em camadas (Pororoca + 2 Tamanduá + 2 pontos de defesa do jogo base) - o estouro de 48 mísseis é a ferramenta de saturação mais forte do elenco.
- TORPEDOS: o Boto de fim de jogo passa 50% por um Tamanduá (6.500 HP pedem dois gatilhos, e as iscas gastam gatilhos) e 0% pela defesa em camadas; o Iara sozinho passa 0% por qualquer CIWS ou flak pesada - de propósito.
- O PD4 do SW (1.250 por tiro) apaga as salvas de meio de jogo; só a Mula o satura. Intencional: os mísseis do SW (7.000-9.800 HP) continuam os mais fortes no SW; os nossos ficam na escala do jogo base.

Armas combinadas (defesa de fim de jogo em camadas; o par de Iara sai em t = 0 e a salva que mascara sai em +atraso):

| Máscara | Atraso da máscara s | Iara que chegaram (de 2) | Ogivas da máscara que chegaram |
|---|---|---|---|
| he | 0 | 0 | 27 / 48 |
| he | 1 | 2 | 28 / 48 |
| he | 2 | 2 | 29 / 48 |
| he | 3 | 1 | 28 / 48 |
| he | 4 | 0 | 27 / 48 |
| cluster | 0 | 0 | 22 / 96 |
| cluster | 1 | 0 | 22 / 96 |
| cluster | 2 | 1 | 22 / 96 |
| cluster | 3 | 1 | 33 / 96 |
| cluster | 4 | 0 | 30 / 96 |
| 2 Caipora A.E. | 1 | 0 | 13 / 32 |
| 2 Caipora A.E. | 2 | 1 | 13 / 32 |
| 2 Caipora A.E. | 3 | 2 | 14 / 32 |

O par de Iara sai primeiro e a salva que mascara sai 1-3 s depois (mísseis pesados voam ~3,8 s até 600 m, torpedos ~7,8 s): as duas ogivas chegam pela defesa de fim em camadas com uma máscara de A.E. da Mula em +1 s / +2 s. Ao mesmo tempo ou mais tarde = as duas morrem. O tempo é a habilidade (o gancho 'tiro, porrada e bomba' do projeto B, com o tempo corrigido).

### 8.4 Logística de munição

| Lançador | Modo | Peça | Peças/min | Viagens/min | Fábricas | cr/s | Tripulação recomendada | Estoque (mísseis) | Estoque (s) | Viagens por 1.000 de DPS efetivo | DPS efetivo por fábrica | Viagens/min em OC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira | he | A.E. | 39,7 | 3,97 | 0,2 | 5,29 | 3,6 | 36,0 | 27,2 | 3,75 | 5.333,0 | 5,72 |
| Tocandira | napalm | T. | 39,7 | 3,97 | 0,2 | 7,94 | 3,6 | 36,0 | 27,2 | 10,0 | 2.000,0 | 5,72 |
| Caipora | he | A.E. | 101,3 | 10,13 | 0,51 | 13,5 | 8,8 | 48,0 | 56,9 | 3,43 | 5.833,0 | 15,33 |
| Caipora | cluster | A.E. | 101,3 | 10,13 | 0,51 | 13,5 | 8,8 | 48,0 | 56,9 | 3,81 | 5.250,0 | 15,33 |
| Caipora | limpet | A.E. | 101,3 | 10,13 | 0,51 | 13,5 | 8,8 | 48,0 | 56,9 | 3,43 | 5.833,0 | 15,33 |
| Caipora | napalm | T. | 101,3 | 10,13 | 0,51 | 20,25 | 8,8 | 48,0 | 56,9 | 8,0 | 2.500,0 | 15,33 |
| Caipora | emp | P.E.M. | 101,3 | 10,13 | 0,84 | 33,76 | 8,8 | 48,0 | 56,9 | 9,23 | 1.300,0 | 12,64 |
| Caipora | torpedo | A.E. | 76,3 | 7,63 | 0,38 | 10,18 | 7,1 | 12,7 | 59,7 | 3,0 | 6.667,0 | 11,37 |
| Mula-sem-Cabeça | he | A.E. | 364,4 | 36,44 | 1,82 | 48,59 | 32,3 | 144,0 | 47,4 | 3,2 | 6.250,0 | 52,84 |
| Mula-sem-Cabeça | cluster | A.E. | 362,3 | 36,23 | 1,81 | 48,3 | 32,2 | 64,0 | 42,4 | 3,56 | 5.625,0 | 55,14 |
| Mula-sem-Cabeça | limpet | A.E. | 362,3 | 36,23 | 1,81 | 48,3 | 32,2 | 64,0 | 42,4 | 3,2 | 6.250,0 | 55,14 |
| Mula-sem-Cabeça | napalm | T. | 362,3 | 36,23 | 1,81 | 72,45 | 32,2 | 64,0 | 42,4 | 8,0 | 2.500,0 | 55,14 |
| Mula-sem-Cabeça | emp | P.E.M. | 271,7 | 27,17 | 2,26 | 90,57 | 26,1 | 48,0 | 31,8 | 9,47 | 1.267,0 | 34,0 |
| Mula-sem-Cabeça | torpedo | A.E. | 297,5 | 29,75 | 1,49 | 39,67 | 27,8 | 20,0 | 48,4 | 3,0 | 6.667,0 | 44,17 |
| Mula-sem-Cabeça | nuclear | nuclear | 48,0 | 4,8 | 0,4 | 28,79 | 11,2 | 6,0 | 60,0 | 0,6 | 20.000,0 | - |

- Viagens de tripulação A.E. por minuto: Tocandira 3,97, Caipora 10,13, Mula 36,44 (nossas armas: Carcará 3,75, Tambor 8,33, Trovão 16, Mapinguari 30); o lançador A.E. do jogo base faz 12 viagens/min para 3.750 de DPS efetivo = 3,2 viagens por 1.000 de DPS efetivo; os nossos, 3,2-3,75.
- Fábricas A.E.: 0,2 / 0,51 / 1,82; tripulação recomendada (fórmula do jogo base) 3,6 / 8,8 / 32,3 - a Mula precisa de um convés de logística de verdade.
- Estoque interno = células + 2 salvas de peças por família = 3 salvas: 27 s (Tocandira), 57 s (Caipora), 47 s (A.E. da Mula) de fogo; as nossas armas guardam 12-32 s - os mísseis levam mais porque a recarga tripulada é o limite real e um estoque cheio é um risco de cook-off.

### 8.5 P.E.M. e escudos

| Lançador | Dreno/míssil | Dreno por peça P.E.M. | HP de escudo do SW por salva | por quadro por s | em OC por quadro por s | Teto |
|---|---|---|---|---|---|---|
| Caipora | 3.000 | 1.500,0 | 120.000,0 | 703,2 | 826,4 | 750 |
| Mula-sem-Cabeça | 4.500 | 1.500,0 | 180.000,0 | 566,0 | 666,7 | 750 |

1.500 de dreno por peça P.E.M. (jogo base: 2.000), <= 750 de HP de escudo do SW por quadro por segundo, e nenhuma salva apaga uma bolha gigante do SW (320.000): salva da Caipora 120.000 (estoura a bolha grande do SW de 80.000 - alfa registrado), salva da Mula 180.000. O autocarregador P.E.M. só acelera / 1,2 no overclock, então a taxa em overclock fica abaixo do teto de 880 do plasma em overclock do mod.

- Todo míssil é `SimpleHit` (penetração 0): estoura na borda da bolha, então contra as bolhas do SW as salvas A.E. quebram escudo primeiro (Caipora 112.000, Mula 360.000, Boto 4 x 36.000 operacional).
- Piranha: o portador abre na bolha e os filhos se gastam nela (não atravessam). Carrapato: não gruda em escudo, só o estouro (43% do A.E.). Taturana: calor no gerador + explosão.

### 8.6 Cook-off, limite do napalm, Carrapato e regra nuclear

| Lançador | Peças A.E. cheias | Explosão A.E. (op + est) | por peça A.E. | Despejo de calor térmico | Dreno P.E.M. | Explosão nuclear |
|---|---|---|---|---|---|---|
| Tocandira | 18 | 11.500 + 3.800 | 850,0 | 4.500 | - | - |
| Caipora | 96 | 61.200 + 20.400 | 850,0 | 24.000 | 57.600 | - |
| Mula-sem-Cabeça | 288 | 183.600 + 61.200 | 850,0 | 64.000 | 86.400 | 72.000 + 24.000 |

~850 de explosão por peça A.E. guardada (faixa 600-1.000; jogo base 3.333 em 12 peças): Tocandira 15.300 com 18 peças, Caipora 81.600 com 96, Mula 240.000 com 288 + mais 96.000 com peças nucleares a bordo. Uma Mula carregada é a peça mais perigosa da nave. Cada armazenamento (paiol da família e as células de cada modo; um míssil nas células = PARTS peças) tem o seu par de cook-off pesado pela capacidade em peças, então uma peça vale o mesmo no paiol ou nas células, e paiol + maior conjunto de células cheios dão exatamente esses números (estágio 4; a fração de enchimento única `Stock_<família>` sobre paiol + todas as células dos estágios 1-3 subestimava os valores, por exemplo A.E. da Caipora 0,70, Iara da Mula 2/34).

| Lançador | Napalm direto efetivo/quadro | Máximo de quadros em chamas por salva | Limite de DPS do dano contínuo | Limite contínuo por quadro | Limite total por quadro | A.E. efetivo/quadro |
|---|---|---|---|---|---|---|
| Tocandira | 99,2 | 12 | 336 | 84,0 | 183,2 | 264,5 |
| Caipora | 140,6 | 32 | 896 | 99,6 | 240,2 | 328,2 |
| Mula-sem-Cabeça | 150,9 | 64 | 1.792 | 59,7 | 210,6 | 379,6 |

O fogo faz no máximo 28 de dano/s por quadro em chamas (`DAMAGE_PER_TICK` 7 a cada 0,25 s com o valor cheio) até a peça queimar; mesmo que os quadros de uma salva inteira queimem sem ninguém apagar, o napalm fica abaixo do A.E. por quadro -> não é um modo de DPS escondido. Zero em blindagem e estrutura.

- **Carrapato.** A carga do Carrapato fica centrada dentro da primeira peça atingida (uma explosão na superfície desperdiça até metade do círculo no espaço), então 1,0x o A.E. sustentado já o favorece um pouco; a espoleta de 2,5 s, a fraqueza contra escudos (estouro de 43%) e a regra de só a primeira peça pagam por isso. O `CrewKillChance` é um bônus que não conta no DPS.
- **Regra nuclear.** Duas Mulas (máximo de `bs_limit_nuke`, junto com a Boiúna) no Iara = 4 torpedos a cada 20,007 s = 1 a cada 5,0 s = duas Boiúnas (1 a cada 10 s cada). 120.000 r9 + 40.000 r7 por torpedo (Boiúna 150.000 r8 + 40.000 r6); 8 peças nucleares (288 cr) por torpedo; HP 6.500 (Boiúna 7.500); o overclock nunca o encurta.

### 8.7 Conferência com o SW:ACD

- Categoria 'missile' em todo míssil, filho e isca (ponto de defesa e flak do jogo base, PD4 do SW, ponto de defesa de blaster do SW e flak do SW atacam todos); a carga do Carrapato não pode ser alvo, de propósito.
- Nenhum tipo ou campo do SW no caminho padrão (sem `Repeating`, `SourceShip*`, `TargetHomingComponent`, `&/SW_*`, camadas, categorias ou toggles do SW); o único tipo só do SW fica num arquivo de variante isolado atrás de uma opção de build.
- Peças de míssil do jogo base compartilhadas com os lançadores do SW; P.E.M. abaixo do jogo base por peça; HP <= 2.800, menos os torpedos (SW 7.000-9.800); alcance <= 600 (SW 1.250).
- Os nossos lançadores não guardam bateria e não são `uses_power`: íon e disruptor do SW (e o nosso próprio P.E.M.) não fazem nada neles.

### 8.8 Limites rígidos (conferidos pelo gerador)

| Verificação | Valor | Limite | OK |
|---|---|---|---|
| Tocandira he: A.E. efetivo/quadro na faixa da fase | 264,5 | 250,0-280,0 | sim |
| Tocandira he: efetivo/quadro em OC <= 550 | 381,4 | <= 550 | sim |
| Tocandira he: DPS efetivo/tripulante <= 1.600 | 1.058,0 | <= 1.600 | sim |
| Tocandira he: efetivo por equivalente de munição 700-1.050 | 800,0 | 700-1.050 | sim |
| Tocandira he: alcance <= teto da fase | 300 | <= 300 | sim |
| Tocandira napalm: efetivo/quadro <= teto da fase | 99,2 | <= 280,0 | sim |
| Tocandira napalm: efetivo/quadro em OC <= 550 | 143,0 | <= 550 | sim |
| Tocandira napalm: DPS efetivo/tripulante <= 1.600 | 396,8 | <= 1.600 | sim |
| Tocandira napalm: alcance <= teto da fase | 300 | <= 300 | sim |
| Caipora he: A.E. efetivo/quadro na faixa da fase | 328,2 | 312,5-340,0 | sim |
| Caipora he: efetivo/quadro em OC <= 550 | 467,6 | <= 550 | sim |
| Caipora he: DPS efetivo/tripulante <= 1.600 | 1.476,8 | <= 1.600 | sim |
| Caipora he: efetivo por equivalente de munição 700-1.050 | 875,0 | 700-1.050 | sim |
| Caipora he: alcance <= teto da fase | 400 | <= 450 | sim |
| Caipora cluster: efetivo/quadro <= teto da fase | 295,4 | <= 340,0 | sim |
| Caipora cluster: efetivo/quadro em OC <= 550 | 420,8 | <= 550 | sim |
| Caipora cluster: DPS efetivo/tripulante <= 1.600 | 1.329,1 | <= 1.600 | sim |
| Caipora cluster: efetivo por equivalente de munição 700-1.050 | 787,5 | 700-1.050 | sim |
| Caipora cluster: alcance <= teto da fase | 400 | <= 450 | sim |
| Caipora cluster: HP do portador <= HP do A.E. | 1.050 | <= 1.050 | sim |
| Caipora cluster: total dos filhos <= 90% do A.E. por peça | 0,9 | <= 0,9 | sim |
| Caipora cluster: filhos por portador <= 6 | 4 | <= 6 | sim |
| Caipora cluster: portadores por salva <= 16 | 16 | <= 16 | sim |
| Caipora cluster: filhos por salva <= 96 | 64 | <= 96 | sim |
| Caipora limpet: efetivo/quadro <= teto da fase | 328,2 | <= 340,0 | sim |
| Caipora limpet: efetivo/quadro em OC <= 550 | 467,6 | <= 550 | sim |
| Caipora limpet: DPS efetivo/tripulante <= 1.600 | 1.476,8 | <= 1.600 | sim |
| Caipora limpet: efetivo por equivalente de munição 700-1.050 | 875,0 | 700-1.050 | sim |
| Caipora limpet: alcance <= teto da fase | 400 | <= 450 | sim |
| Caipora napalm: efetivo/quadro <= teto da fase | 140,6 | <= 340,0 | sim |
| Caipora napalm: efetivo/quadro em OC <= 550 | 200,4 | <= 550 | sim |
| Caipora napalm: DPS efetivo/tripulante <= 1.600 | 632,9 | <= 1.600 | sim |
| Caipora napalm: alcance <= teto da fase | 400 | <= 450 | sim |
| Caipora emp: efetivo/quadro <= teto da fase | 121,9 | <= 340,0 | sim |
| Caipora emp: efetivo/quadro em OC <= 550 | 143,3 | <= 550 | sim |
| Caipora emp: DPS efetivo/tripulante <= 1.600 | 548,5 | <= 1.600 | sim |
| Caipora emp: alcance <= teto da fase | 400 | <= 450 | sim |
| Caipora emp: dreno por peça P.E.M. <= 1.500 | 1.500,0 | <= 1.500 | sim |
| Caipora emp: HP de escudo do SW/quadro/s <= 750 | 703,2 | <= 750 | sim |
| Caipora emp: salva P.E.M. < bolha gigante do SW 320.000 | 120.000,0 | < 320.000 | sim |
| Caipora emp: HP de escudo do SW/quadro/s em OC <= 880 (teto do plasma em OC) | 826,4 | <= 880 | sim |
| Caipora torpedo: efetivo/quadro <= teto da fase | 282,7 | <= 340,0 | sim |
| Caipora torpedo: efetivo/quadro em OC <= 550 | 421,1 | <= 550 | sim |
| Caipora torpedo: DPS efetivo/tripulante <= 1.600 | 1.272,1 | <= 1.600 | sim |
| Caipora torpedo: efetivo por equivalente de munição 700-1.050 | 1.000,0 | 700-1.050 | sim |
| Caipora torpedo: alcance <= teto da fase | 400 | <= 450 | sim |
| Caipora torpedo: torpedo >= 80.000/tiro precisa de limite por nave | 24.000 | >= 80.000 -> com limite | sim |
| Mula-sem-Cabeça he: A.E. efetivo/quadro na faixa da fase | 379,6 | 375,0-381,0 | sim |
| Mula-sem-Cabeça he: efetivo/quadro em OC <= 550 | 518,1 | <= 550 | sim |
| Mula-sem-Cabeça he: DPS efetivo/tripulante <= 1.600 | 1.423,6 | <= 1.600 | sim |
| Mula-sem-Cabeça he: efetivo por equivalente de munição 700-1.050 | 937,5 | 700-1.050 | sim |
| Mula-sem-Cabeça he: alcance <= teto da fase | 600 | <= 600 | sim |
| Mula-sem-Cabeça cluster: efetivo/quadro <= teto da fase | 339,6 | <= 381,0 | sim |
| Mula-sem-Cabeça cluster: efetivo/quadro em OC <= 550 | 486,5 | <= 550 | sim |
| Mula-sem-Cabeça cluster: DPS efetivo/tripulante <= 1.600 | 1.273,6 | <= 1.600 | sim |
| Mula-sem-Cabeça cluster: efetivo por equivalente de munição 700-1.050 | 843,8 | 700-1.050 | sim |
| Mula-sem-Cabeça cluster: alcance <= teto da fase | 600 | <= 600 | sim |
| Mula-sem-Cabeça cluster: HP do portador <= HP do A.E. | 2.200 | <= 2.200 | sim |
| Mula-sem-Cabeça cluster: total dos filhos <= 90% do A.E. por peça | 0,9 | <= 0,9 | sim |
| Mula-sem-Cabeça cluster: filhos por portador <= 6 | 6 | <= 6 | sim |
| Mula-sem-Cabeça cluster: portadores por salva <= 16 | 16 | <= 16 | sim |
| Mula-sem-Cabeça cluster: filhos por salva <= 96 | 96 | <= 96 | sim |
| Mula-sem-Cabeça limpet: efetivo/quadro <= teto da fase | 377,4 | <= 381,0 | sim |
| Mula-sem-Cabeça limpet: efetivo/quadro em OC <= 550 | 540,5 | <= 550 | sim |
| Mula-sem-Cabeça limpet: DPS efetivo/tripulante <= 1.600 | 1.415,1 | <= 1.600 | sim |
| Mula-sem-Cabeça limpet: efetivo por equivalente de munição 700-1.050 | 937,5 | 700-1.050 | sim |
| Mula-sem-Cabeça limpet: alcance <= teto da fase | 600 | <= 600 | sim |
| Mula-sem-Cabeça napalm: efetivo/quadro <= teto da fase | 150,9 | <= 381,0 | sim |
| Mula-sem-Cabeça napalm: efetivo/quadro em OC <= 550 | 216,2 | <= 550 | sim |
| Mula-sem-Cabeça napalm: DPS efetivo/tripulante <= 1.600 | 566,0 | <= 1.600 | sim |
| Mula-sem-Cabeça napalm: alcance <= teto da fase | 600 | <= 600 | sim |
| Mula-sem-Cabeça emp: efetivo/quadro <= teto da fase | 95,6 | <= 381,0 | sim |
| Mula-sem-Cabeça emp: efetivo/quadro em OC <= 550 | 112,6 | <= 550 | sim |
| Mula-sem-Cabeça emp: DPS efetivo/tripulante <= 1.600 | 358,5 | <= 1.600 | sim |
| Mula-sem-Cabeça emp: alcance <= teto da fase | 600 | <= 600 | sim |
| Mula-sem-Cabeça emp: dreno por peça P.E.M. <= 1.500 | 1.500,0 | <= 1.500 | sim |
| Mula-sem-Cabeça emp: HP de escudo do SW/quadro/s <= 750 | 566,0 | <= 750 | sim |
| Mula-sem-Cabeça emp: salva P.E.M. < bolha gigante do SW 320.000 | 180.000,0 | < 320.000 | sim |
| Mula-sem-Cabeça emp: HP de escudo do SW/quadro/s em OC <= 880 (teto do plasma em OC) | 666,7 | <= 880 | sim |
| Mula-sem-Cabeça torpedo: efetivo/quadro <= teto da fase | 330,6 | <= 381,0 | sim |
| Mula-sem-Cabeça torpedo: efetivo/quadro em OC <= 550 | 490,8 | <= 550 | sim |
| Mula-sem-Cabeça torpedo: DPS efetivo/tripulante <= 1.600 | 1.239,7 | <= 1.600 | sim |
| Mula-sem-Cabeça torpedo: efetivo por equivalente de munição 700-1.050 | 1.000,0 | 700-1.050 | sim |
| Mula-sem-Cabeça torpedo: alcance <= teto da fase | 600 | <= 600 | sim |
| Mula-sem-Cabeça torpedo: torpedo >= 80.000/tiro precisa de limite por nave | 48.000 | >= 80.000 -> com limite | sim |
| Mula-sem-Cabeça nuclear: DPS efetivo/tripulante <= 1.600 | 999,7 | <= 1.600 | sim |
| Mula-sem-Cabeça nuclear: alcance <= teto da fase | 600 | <= 600 | sim |
| Mula-sem-Cabeça nuclear: torpedo >= 80.000/tiro precisa de limite por nave | 160.000 | >= 80.000 -> com limite | sim |
| Progressão: todo modo de meio < A.E. de fim | 328,2 | < 379,6 | sim |
| Paridade nuclear: 2 Mulas (máximo da vaga) -> >= 5 s por torpedo nuclear | 5,002 | >= 5,0 | sim |
| Torpedo nuclear: sem OC na recarga | `no_oc` | `True` | sim |
| Salva de início passando por UM ponto de defesa do jogo base em 40-60% | 0,583 | 0,40-0,60 | sim |
| Tocandira: cook-off por peça A.E. guardada 600-1.000 | 850,0 | 600-1.000 | sim |
| Caipora: cook-off por peça A.E. guardada 600-1.000 | 850,0 | 600-1.000 | sim |
| Mula-sem-Cabeça: cook-off por peça A.E. guardada 600-1.000 | 850,0 | 600-1.000 | sim |

## 9. Plano de testes (modo desenvolvedor, 0.30.4 e 0.30.5 RC4, com e sem o SW:ACD)

| # | Pergunta | Como | Passa se | Plano B (sem mudar números) |
|---|---|---|---|---|
| T01 | Carregar e validar | `build_mod.py --no-art`, `rules_lint.py`, `schema_check.py --extra SW` no 0.30.4 e no 0.30.5 RC4, com e sem o SW:ACD. | 0 erros; nenhum global exclusivo do 0.30.5 referenciado | - |
| T02 | Histerese da trava das células (gap Q7) | Caipora A.E. contra um alvo de treino: observar as sobreposições + `ProgressBar`; matar o alvo no meio da salva. | as células enchem 0->16 e disparam 16 mísseis seguidos, o carregador fica parado enquanto travado; o resto de uma salva interrompida vai para o próximo alvo | `Timer` `IsSalvoActive` + trava `RackFull_k` (rodapé do esboço); mesmos tempos |
| T03 | Recarga só com tripulação | Tirar a tripulação com metade das células carregadas; devolver. | células congeladas, o paiol continua aceitando entregas, volta quando tripulado | acrescentar `PartCrew` explicitamente em `LoaderOn_k` |
| T04 | Exploração entre modos | Encher as células A.E., trocar para Piranha, disparar, voltar logo; trocar também no meio da salva; overclock ligado/desligado. Encher as células de todos os modos com o overclock desligado, ligar o overclock e passar por todos os modos. | as células A.E. esperam `ModeSwitchDelay_he` (uma recarga A.E., /1,5 em OC); nunca duas salvas seguidas; células que já estavam cheias na troca esperam a recarga SEM overclock (`PrefilledDelay_k`), então enchê-las antes não dá cadência de overclock de graça | um `ModeSwitchDelay` único no nível da peça com a maior duração (versão de A); `prefilled_switch=oc_delay` (atraso dividido pelo overclock em toda troca) |
| T05 | Salva parcial `DryFlush` | Dar 5 peças à família A.E., com as células vazias. Depois uma Mula A.E. sem abastecimento: paiol e células vazios, um tripulante entregando 10 peças a cada ~5 s (menos que as 6,1 peças/s que o carregador come). | carrega 2 mísseis, espera `DRY_DELAY` (uma recarga inteira sem overclock) sem entrega e dispara os 2, sem travar; Mula sem abastecimento: cada entrega recomeça a espera, a trava mantém as células fechadas e ela continua disparando salvas CHEIAS de 48 mísseis (nada de pinga-pinga de minissalvas de 1-5 mísseis); salva parcial só depois de uma recarga inteira sem nenhuma entrega | `dry_flush=instant` (sem espera; reabastecimento lento dispara em pinga-pinga) ou `dry_flush=off` (mísseis presos esperam o reabastecimento) |
| T06 | Lançamento por cima do próprio casco (gap Q4) | Lançadores cercados de blindagem e torres de convés; o míssil mais lento (torpedo) numa célula fora do centro; alvos atrás da nave. | nenhum `HitFriendly` apagando nas nossas peças, no casulo ou nas torres vizinhas | `SourcePartCollisionDelay` 0,05 -> 0,3 s nesse projétil |
| T07 | Desvio da mira sobre o próprio casco (gap Q5) | 3 variantes: `AvoidanceRaycastDistance` omitido (padrão) / 250 / `AvoidsFriendlies = false`. | sem frear nem desviar logo depois do lançamento | usar a melhor variante (não é número de balanceamento) |
| T08 | Cascos aliados (gap Q6) | Duas naves aliadas na linha de tiro. | documentado (as granadas de convés se comportam igual) | só uma linha na descrição |
| T09 | Nossa CIWS/flak contra os nossos mísseis (gap Q9) | Disparar salvas de Piranha e A.E. através das explosões aéreas do nosso Tamanduá e da nuvem da Muralha de Flak da Pororoca. | nenhuma perda própria | filtro explícito só de inimigos no `VolumeHit` da nuvem de estilhaços (`bs_cloud_flak_heavy`; arquivo da defesa, nenhum número de míssil) |
| T10 | CIWS LOCK x RETARGET (balanceamento §1) | Disparar 16 mísseis com cadência da salva de 4/30 s através de UM Tamanduá; contar mortes por gatilho; repetir com a Pororoca. | medir qual modelo vale; refazer as contas de interceptação (`balance_checks.interception` do spec) com ele | só ajuste de balanceamento: HP do míssil / cadência da salva, nunca mudança de mecânica |
| T11 | Piranha: herança, ímã, espalhamento (gap Q1/Q2) | 1 portador num alvo fora do eixo; registrar as peças diferentes atingidas; variante `RandomizeTarget = true`; abrir uma com um inimigo a 20 m do nosso casco grande. Danificar um portador até cerca de metade do HP com ponto de defesa e deixá-lo acertar um casco, esgotar o tempo (11 s) e abrir por proximidade. | os filhos miram depois de 0,25 s e acertam >= 3 peças; nenhum apagando em aliado; os filhos de um portador meio morto nascem com cerca de metade do HP nos três caminhos (`HealthFactor` ponderado pelo `Targetable` no `ProximityFuse`, no `TimedFuse` e no `Hit` de impacto) | filhos só com ímã; `StartDelay 1.0`; `RandomizeTarget` continua desligado |
| T12 | Piranha contra escudos | Bolhas do SW e do jogo base. | o portador abre na bolha; os filhos se gastam nela | - |
| T13 | Desempenho | 2 Mulas com Piranha (192 filhos) + 4 Caiporas com Piranha (256) + flak inimiga + a nossa CIWS, no 0.30.4 e no 0.30.5. | >= 30 fps na máquina de desenvolvimento | tirar o brilho dos filhos, apagar o componente `Spacing` dos filhos (`Count` igual) |
| T14 | Fixação do Carrapato (gap Q10) + sem trava do ponto de defesa | Alvo com empuxo máximo e girando; 16 Carrapatos; ponto de defesa inimigo presente. | as cargas seguem no casco por 2,5 s e explodem nele; o ponto de defesa inimigo não atira no próprio casco | F1 sem ímã -> F2 status (T14b) -> F3 `HitObject` com `Speed` 0 -> F4 explosão no impacto; mesmos números |
| T14b | Registro de status por mod (gap Q3) | `AddMany` de um status de peça de teste em `<statuses/statuses.rules>/Statuses`; aplicar `StatusDuration 3`, `TickInterval 2.5`; registrar o tempo dos ticks; `ExplosiveDamage` x `Damage` em `TickingEffects`. | carrega nas duas versões; primeiro tick no `TickInterval` | não usar o F2 |
| T15 | Napalm da Taturana | Acerto interno numa nave de teste sem blindagem, com e sem extintores; 0.30.4 x 0.30.5; arquivo da variante de respingo de gel. | fogo na peça atingida, calor >= 350 em 2-4 quadros, reignição em 6-10 s; a espuma apaga; blindagem nunca queima | `ApplyToAllHitPartTiles = true`; o gel continua desligado |
| T16 | P.E.M. do Poraquê | Nave do jogo base com escudo + reator; bolha média/grande do SW; nave com armas do Bullet Strike. | dreno em escudos/baterias na taxa calculada; nada nas armas do Bullet Strike; nenhum dreno em aliado | tirar a carona `disruptor_drain`; acrescentar `ResourceDrain TreatShieldAsPart` no `HitShield` |
| T17 | Estágio do torpedo + iscas | Observar o estágio de 1,5 s: ogiva + N iscas de dois `SpawnBullets` num `OnDeath`; danificar o estágio antes (`HealthFactor`). | 1 ogiva + N iscas; as iscas atraem tiros dos pontos de defesa e reservas da flak; um estágio danificado dá uma ogiva danificada | iscas por um segundo emissor (`Burst` N, `BurstDelay 0.1`, sem `ResourceStorage`) |
| T18 | Regras nucleares | Montar 2 Mulas + tentar uma Boiúna; 1 Mula + 1 Boiúna; impacto do Iara ao lado de um aliado; overclock ligado no modo Iara. | a 3ª plataforma é recusada; a mistura é aceita; nenhum dano no aliado; a recarga continua 9,97 s, sem calor de overclock | distribuir sem limites se os `CategoryLimits` falharem no 0.30.5 (como a Boiúna) |
| T19 | Custos do overclock + cadeia de cook-off (gap Q12) | Caipora em overclock com radiadores, depois sem tubulação, células cheias, fogo contínuo; depois consertar a queimadura. | o calor chega à rede; o descarte tira 2 peças por salva; sem tubulação -> calor nos próprios quadros -> fogo -> queimado -> cook-off da família; NENHUM cook-off ao consertar | se o descarte se comportar mal, apagá-lo (os custos de calor continuam) |
| T20 | Cook-off da família | Destruir lançadores cheios (A.E., depois térmica, P.E.M., nuclear a bordo). | explosão escalada pelo enchimento de cada família; um lançador queimado explode uma vez | - |
| T21 | Sobreposições | O casulo gira; sobreposições em `roof_turrets` sobre o casulo em `roof_doodads`; `RangeLow`/`RangeHigh` por casulo; visuais pesado/torpedo; vista do interior. Disparar uma salva parcial `DryFlush` e trocar de modo / voltar no meio da salva. | o LIFO bate com a contagem em todo leiaute em toda salva cheia; limite cosmético conhecido: uma salva parcial `DryFlush` e o resto de uma salva interrompida depois de voltar começam pela última célula (um tubo que parece vazio dispara enquanto some uma célula que parecia carregada; a contagem não muda) | um sprite de casulo combinado por nível |
| T22 | `Burst` do cassete + cadência da salva alinhada ao tick | Contar mísseis e peças da Tocandira por salva; medir a cadência real nos três (4/30, 2/30). | 12 mísseis por 6 peças; o tubo B sai 2/30 s depois do tubo A; cadências como especificado | emissor de tubo duplo de C (`FireDelay 2/30`, sem `ResourceStorage`) + `HoldTargetAfterCancel` |
| T23 | Comportamento da IA | Naves da IA com cada lançador contra alvos com muitos pontos de defesa. | dispara salvas cheias, usa o `AIFirepowerRating` | `AIFirepowerRating` x0,8 |
| T24 | Seletor e liberações | Carreira: cada tech libera só a sua escolha; `AvailableChoices` por lançador. | Tocandira 2 escolhas, Caipora 6, Mula 7 | `ToggleID`s separados por lançador (`bs_missile_type_s/_m/_l`) |

## 10. Notas de implementação (padrões do jogo base para copiar)

Apelidos de caminho: `R/` = as regras do jogo base 0.30.5 RC4 (a pasta `Data` do jogo); `RJ/` = uma segunda cópia dos dados do jogo base (o commit ae16922 = 0.30.3, usado como referência do 0.30.4); `SW/` = o mod Star Wars: A Cosmos Divided (feito para o 0.30.4); `BS/` = `BulletStrike/` (o nosso mod gerado); `T/` = `tools/` (o nosso gerador); `NVL/NSM/NSW/NGEN/GAPS` = notas de pesquisa do projeto (lançador do jogo base, mecânicas especiais, SW:ACD, nosso gerador, lacunas), que não estão no repositório. Os números de linha citados são da época do projeto e servem só para localizar o trecho.

| Assunto | Copiar de (arquivo:linha) | Nota |
|---|---|---|
| Casca de peça de convés | `R/ships/terran/cannon_deck/cannon_deck.rules`:35-36 (`ProhibitedBy [tall]` + anel `ProhibitRects`), :611 (`FireInterval = 0 // separate fire timer`), :617 (`Emitter = BaseEmitterProxy` 'only used for targeting'), :618 (`IgnoreFriendlyShipLowLOSChecks`), :817 (colisor `IsHigh`), :895 (`Type = EmitterProxy`); `T/bsgen/guns.py` (`Emitter = TargetEmitterProxy`, opção de linha de visada, `TurretCollider`, `ShootCycle`, `EmitterProxy ChainedTo = Turret`) | sem `ProhibitAbove`; anel de 1/1/2 quadros; `TypeCategories` sem `uses_power`; `base_med_part_terran(_overclock)` / `base_large_part_terran_overclock` |
| Seletor | `R/ships/terran/missile_launcher/missile_launcher.rules`:126-202 (`UIToggle` + `ModeToggle` + `ToggledComponents`, mesmos nomes por bloco), :281-291 (`TriggerProxy`/`ToggleProxy` para o bloco ativo); `RJ/ships/terran/point_defense/point_defense.rules`:102 (`AvailableChoices`, também no 0.30.3); `RJ/modes/career/techs.rules`:112-119 (`ToggleChoicesUnlocked = [[missile_type, 0]]`); `T/bsgen/guns.py` (`AmmoTypeToggle`, `ModeToggle_k`); `T/bsgen/infra.py` (`part_toggles` -> generalizado para uma lista) | `ToggleID` novo `bs_missile_type`, escolhas `bs_missile_<tipo>`, nunca o `missile_type` do jogo base nem o do SW |
| Paiol da família + consumidor | `T/bsgen/guns.py` (`MagStorage_k` / `MagConsumer_k`); `R/ships/terran/missile_launcher/he/missile_launcher_he.rules`:13-46 campos do armazenamento, :89-98 consumidor (NVL §3) | variante nova `magazine_block`: um armazenamento por família de recurso, toggle do consumidor `All[CommandConsumptionToggle, Any[ModeToggle_k da família]]` (D-B7) |
| Autocarregador tripulado + divisão do overclock | `SW/ships/terran/weapons/small/discordmissile/dm_launcher.rules`:109-176 (estoque + carregador temporizado de armazenamento para armazenamento, distribuído no 0.30.4); `RJ/ships/terran/factory_he/factory_he.rules`:212-227 (`Interval { BaseValue; Modifiers [ Buff Factory Divide, BuffRemap Overclock Divide ] }`, `CheckResourceLimits`) | `OperationalToggle = LoaderOn_k` (`IsOperational` contém `PartCrew`); o carregador nuclear não tem `Modifiers` |
| Trava das células, progresso, limiares, gatilhos, mudança negativa | `RJ/ships/terran/thruster_boost/thruster_boost.rules`:176-177 (`ToggleOnResources = (&MaxResources) - 999` / `ToggleOffResources = 0`), :186 (`ShowProgressFor` = armazenamento), :198-199 (`MultiResourceStorage` de limiar `FullAmmoToggle`), :213-214 e :237-238 (`ToggleTrigger TriggerWhenOn = false` / `TriggerWhenOff = true`), :224 (`ResourceChange Amount = -999999` num armazenamento) | trava, `RackAny_k` / `MagCanLoad_k`, `ModeOn_k`, descarte |
| `Timer` com `Duration` modificada pelo overclock, `StartExpired` | `Duration { BaseValue; Modifiers }` do `Overclock_ChargeTimer` do railgun (NVL §10; `RJ railgun_launcher.rules`:413-436); `Timer StartExpired` do chaingun (`chaingun.rules` 0.30.3:200-207, conferido pelo juiz de viabilidade) | `ModeSwitchDelay_k` |
| Cadência da salva alinhada ao tick | `RJ/ships/terran/point_defense/point_defense.rules`:365-367 (`FireInterval BaseValue = 2/30`); `R/cosmoteer.rules`:76 (`PhysicsUpdatesPerSecond = 30`) | `RIPPLE` = 4/30 (cassete da Tocandira, Caipora) e 2/30 (Mula); `BurstDelay` do cassete 2/30 |
| `Burst` do cassete | `BS/parts/bs_ciws/bs_ciws.rules` (`Burst = 3; BurstDelay = 0.08; UseResourcePerShotInBurst = true` -> o padrão false consome uma unidade por rajada); `RJ/ships/terran/cannon_med/cannon_med.rules`:512-526 (`Burst` / `BurstDelay`); `RJ/ships/terran/chaingun/chaingun.rules`:939 | emissores da Tocandira: `Burst = 2; BurstDelay = 2/30; ResourcesUsed = 1` |
| Sobreposições das células | `RJ/ships/terran/cannon_med/cannon_med.rules`:858-915 (`ResourceSprites ChainedTo = Turret`, `RangeLow`/`RangeHigh` 0-5 / 5-15); `missile_launcher_he.rules`:220-269 (`HasZeroResourceSprite`, um nível por contagem, NVL §4) | casulo em `roof_doodads` (1100), sobreposições em `roof_turrets` (1200); `RangeLow`/`RangeHigh` por casulo; ordem de disparo LIFO = inverso da ordem de enchimento |
| Cook-off | `RJ/ships/terran/missile_launcher/he/missile_launcher_he.rules`:271-276 (`ScorchedTrigger TriggerWhenOn = false; TriggerWhenOff = true`), :278-283 (`ScorchedEffects FactorHitEffectsWith`), :288-330 (`DeathEffects` 30.000 r5 + `CrewKillChance` 50% em :308 + 10.000 r4); despejo de calor térmico: `missile_launcher_thermal.rules`:536-619 (NVL §9) | um `DeathEffects` por família FORA dos blocos alternados; copiar o `ScorchedTrigger` ao pé da letra (D-C1) |
| Núcleo do míssil (seguro no convés) | `R/shots/missile_he/missile_he.rules`:16-48 (`TargetHoming` / `SameShipRetarget` / `Acceleration` / `NegativeAcceleration` / `DeathByLifetime`), :110-123 (`Targetable` que apaga + `SourcePartCollisionDelay`) (NVL §7); `R/shots/bullet_deck/bullet_deck.rules`:40-41 (`FriendlyShipLowCollisions = false`), :159/:188 (BulletUpper3/4); `T/bsgen/shots.py` (sprites Upper, opção de convés, `TargetHoming`) | sem `AvoidanceRaycastDistance`; sem `Friendlies = true`; só literais |
| Piranha | `SW/shots/missiles/discord/missile/missile_discord.rules`:48-72 (`DeathByEnemyProximity` -> `SpawnBullets`), :75-96 (reserva por tempo de vida), :170-172 (grupos do `Hit` = `OnDeath`); `RJ/shots/bullet_large/overclock/bullet_large_overclock.rules`:13-18 (cone `Arc`, `InheritVelocity` comentado = desligado); `RJ/shots/mine/mine.rules`:20-27 (repulsão); `SW/shots/missiles/discord/buzz-droids/buzzdroid.rules`:37-44 (ímã); `RJ/shots/missile_nuke/missile_nuke_stage1.rules`:46 (`HealthFactor`) | portador + filho na mesma pasta; `build_mod.shot_file` do tipo 'missile' grava os filhos primeiro (padrão do `flak_oc` em `T/build_mod.py`) |
| Carrapato | `SW/shots/missiles/discord/buzz-droids/buzzdroid.rules`:37-44 (ímã) + :78-81 (`PenetratingHit`, `PenetrationSpeed = 0.05`); status F2: `RJ/statuses/disruptor_drain/disruptor_drain.rules`:2-4, :25 (`Layer = Part; ApplyNewInstance; TickInterval; ParentMediaEffectsToShip`) + `RJ/statuses/statuses.rules`:5-12 (lista de registro); variante isolada: `SW/shots/missiles/intruder/missile_intruder.rules`:130-134 (`Repeating`, `InitialDelay`, `RequireHitPart`) | a carga NÃO tem `Targetable`; `CrewKillChance` no `BLAST` (campo do jogo base, `missile_launcher_he.rules`:308) |
| Taturana | `RJ/shots/bullet_med/bullet_med.rules`:129-132 (`StatusApplication cosmoteer.fire`, `StatusChance`, `ValueType = Interpolated`); `RJ/shots/bullet_large/overclock/bullet_large_overclock_shrapnel.rules`:14, :113-114 (`StatusValue = 30 %`, `Interpolated`); `RJ/shots/missile_thermal/missile_thermal.rules`:128-139 (reserva de calor `GridStatusApplication` - escrever uma reserva literal em vez do `APPLIED_HEAT_PER_MISSILE` exclusivo do RC em :131), :173-174 (calor no escudo com `ApplyToAllHitPartTiles`) | sem incêndio embutido no `ExplosiveDamage`; sem `UseContiguity`/`AllowVertexContiguity` |
| Poraquê | `RJ/shots/missile_emp/missile_emp.rules`:151-155 (`ExplosiveResourceDrain TotalDrain` / `Radius` / `Slices`), :182 (`Damage`), :192-196 (`ExplosiveDamage` só estrutural); `RJ/statuses/disruptor_drain` (carona) | `Filter` sem `Friendlies` |
| Boto / Iara | `RJ/shots/missile_nuke/missile_nuke_stage1.rules`:46 (`HealthFactor`), :141-160 (explosões operacional + estrutural com `ExpandDuration` / `ExpandStartRadius`); `BS/shots/bs_shot_nuke_howitzer_nuclear` (mídia do cogumelo) | literais; sem `LinearDamping` (aceleração constante de 12 - nada de que recuar, D-A4) |
| Maquinário de overclock | `T/bsgen/common.py` (`standard_toggles` + `OVERCLOCK_OPERATIONAL`, `overclock_machinery`; `Overclock_ShotHeatProducer`, `Overclock_ConstantHeatProducer`); `RJ/ships/base_part_overclock.rules`:122-125 (`OverclockReset Duration 3`), :172-189 (`OverflowHeatStorage`, `OverheatEffects`); `RJ/ships/terran/radiator/radiator.rules`:191 (1.100 de calor/s); `RJ/statuses/heat/heat.rules`:12 (`STATUS_TO_RESOURCE_RATIO = 1000`); `RJ/ships/terran/factory_he/factory_he.rules`:272 (`Overclock_ConversionHeatProducer`) | `Overclock_LoadHeat_k` por modo com `Trigger = Autoloader_k` em vez do calor por tiro do proxy do emissor |
| Limite por nave | `BS/mod.rules` (`CategoryLimits AddTo terran.rules`; `bs_limit_nuke Max = 2`; `CategoryNouns`) | `TypeCategories` da Mula += [`uses_nukes`, `bs_limit_nuke`]; nenhuma categoria nova |
| Buckets dos efeitos de lançamento | `ships/terran/missile_launcher/particles/missile_launcher_shoot_flash.rules` (Upper1, NGEN §2); evitar `missile_launcher_shoot.rules` (Middle3, sob o nosso teto); sopro `cannon_smoke_deck` / `chaingun_shoot_smoke` (Upper) | `check_vanilla_paths` confere cada caminho nos builds com `--vanilla` |
| Arquivos do gerador | lista NGEN §12: `T/bsgen/launchers.py` (novo), `shots.py` (`build_missile` / `build_missile_part` / `build_limpet_charge` / torpedo), `build_mod.py` (`shot_file` com tipos de vários arquivos), `bs_data.py` (`LAUNCHERS` / `MISSILE_CHOICES` / techs 'missile:' / `LIMITS`), `bs_strings.py`, `render_part.py` do tipo 'launcher' + `STYLE.md` §8 | chaves do spec `launchers` / `missile_types` como chaves novas de primeiro nível - nunca dentro de `weapons[]` (o `bs_data._convert` supõe campos de arma) |

- **Volume do gerador.** 212 componentes `BulletEmitter` no total (Tocandira 12, Caipora 82, Mula 118), gerados por um laço só; só um bloco `Fire_k` (<= 48 emissores) fica ativo por vez. Os modos pesados da Mula usam 16 unidades (uma linha de 3 células cada) para manter baixos o número de emissores, os projéteis de carga e a matriz de arte. Arquivos de projétil: A.E. x3, Piranha x2 (+2 filhos), Carrapato x2 (+2 cargas, +2 variantes isoladas `_rep`), Taturana x3, Poraquê x2, Boto x2 (+2 ogivas, +2 iscas), Iara x1 (+ogiva, +isca) = 28 arquivos no padrão.
- **Mapa de IDs.** início: `rafaeltessaro.bs_msl_box` (Tocandira); meio: `rafaeltessaro.bs_msl_twin` (Caipora); fim: `rafaeltessaro.bs_msl_quad` (Mula-sem-Cabeça); projéteis: `rafaeltessaro.bs_msl_<box|twin|quad>_<he|cluster|limpet|napalm|emp|torpedo|nuclear>[_child|_charge|_warhead|_decoy|_rep]`; nota: corrige a colisão de IDs entre A e B (S3): box = caixa RAM de início, twin = casulos gêmeos de meio, quad = bateria quádrupla de fim.

## 11. Riscos e planos B

| Risco | Nível | Plano B |
|---|---|---|
| Fixação do Carrapato numa nave que se move e gira | MÉDIO-ALTO no comportamento | cadeia F1-F4, mesma espoleta e explosão (T14) |
| Herança do alvo da Piranha + nave de origem dos filhos | MÉDIO [INFERIDO, forte] | filhos com ímã; `StartDelay 1.0` (T11) |
| Histerese da trava das células | BAIXO-MÉDIO [INFERIDO, forte] | trava `IsSalvoActive` + `RackFull`, mesmos tempos (T02) |
| CIWS LOCK x RETARGET | só balanceamento | refazer as contas de interceptação; ajustar HP/cadência da salva (T10) |
| Desvio da mira sobre o próprio casco | MÉDIO | `AvoidsFriendlies = false` (T07) |
| O próprio colisor `IsHigh` depois de 0,05 s | MÉDIO | `FriendlyShipHighCollisions = false` já está lá; `SourcePartCollisionDelay` 0,3 s (T06) |
| Dois `SpawnBullets` num `OnDeath` (iscas) | BAIXO-MÉDIO | iscas por emissor, mesmas contagens (T17) |
| Registro de status por mod (só para o F2 do Carrapato) | MÉDIO | pular o F2 (T14b) |
| Desempenho (<= 96 filhos por salva de lançador) | MÉDIO | tirar o visual + apagar o `Spacing` (T13) |
| A nuvem de estilhaços da nossa flak (Pororoca) contra os nossos mísseis | BAIXO [INFERIDO: só inimigos] | filtro só de inimigos na nuvem (T09) |
| Alinhamento de `FireInterval` / `BurstDelay` aos ticks | BAIXO | as cadências são múltiplas do tick; medir (T22) |
| `CategoryLimits` no 0.30.5 RC | BAIXO | distribuir sem limites (como a Boiúna/Mapinguari) |
| `DryFlush` com espera (a rampa `ValueTween` chegando a 100%) | BAIXO [padrão do chaingun do jogo base] | `dry_flush=instant`, mesmos números (T05) |
| Atraso de troca com células já cheias (`TriggerProxy` com `ProxyToggle` na trava das células) | BAIXO | `prefilled_switch=oc_delay`, mesmos números (T04) |

## 12. Cada defeito apontado pelos juízes e como foi resolvido

| Juiz | Projeto | Defeito | Solução |
|---|---|---|---|
| balanceamento | A | Cook-off pequeno demais (444/361 por peça A.E.) | ~850 por peça A.E. guardada em todos os lançadores (15.300 / 81.600 / 240.000 com o estoque cheio). |
| balanceamento | A | Estoque escondido: paióis por modo, cook-off dentro do `Fire_k` | Um paiol por família de recurso + cook-off FORA dos blocos alternados (estágio 4: um par por armazenamento - o paiol e as células de cada modo - pesado pela capacidade em peças; os estágios 1-3 usavam uma fração de enchimento `Stock_<família>`). |
| balanceamento | A | Torpedo Gorjala com 100.000 por tiro e sem limite | Os torpedos convencionais ficam < 80.000 (Boto 24.000 / 48.000 de explosivo); o único torpedo >= 80.000 (Iara) vai na Mula, limitado por `bs_limit_nuke`. |
| balanceamento | A | A promessa de espalhamento da submunição contradiz uma mira de 180 graus/s depois de 0,15 s | `InheritVelocity = false`, mira de 110-120 graus/s depois de 0,25 s, ímã + espaçamento; o espalhamento pelas peças é item de teste (T11). |
| balanceamento | A/B/C | CIWS LOCK x RETARGET sem teste | LOCK é o modelo principal e RETARGET o limite pessimista em todas as tabelas; o teste T10 calibra. |
| balanceamento | A | Observação sobre o alfa do P.E.M. | Salva P.E.M. da Caipora de 120.000 de HP de escudo do SW (estoura a bolha grande do SW) documentada; nenhuma salva chega a uma bolha gigante. |
| balanceamento | B | P.E.M. acima do teto (874/1.015, 3.500-4.000 por peça) | 1.500 por peça P.E.M.; 703 / 566 de HP de escudo do SW por quadro por s; salva da Mula 180.000 (< 320.000). |
| balanceamento | B | Tocandira morta na chegada contra um ponto de defesa do jogo base | Cassetes de micromísseis (12 em 0,73 s), 380 HP = 3 tiros do ponto de defesa: 58% passam por um ponto de defesa do jogo base. |
| balanceamento | B | Os ônibus de Piranha da Mula com 4.200 HP vencem a flak | HP do portador = HP do A.E. (2.200). |
| balanceamento | B | 240-480 filhos por salva | Piranha da Mula = 16 ônibus x 6 = 96 filhos por salva (192 com 2 Mulas); Caipora 16 x 4 = 64. |
| balanceamento | B | Conclusões sobre a CIWS montadas em RETARGET | Todas as tabelas de interceptação recalculadas com o modelo do juiz, LOCK como principal. |
| balanceamento | B | Cook-off de 271-306 por peça | ~850 por peça. |
| balanceamento | B | Buracos no `SalvoCooldown` (salva interrompida, duração global) | `ModeSwitchDelay_k` por modo, iniciado em QUALQUER entrada no modo, com duração = a recarga completa desse modo. |
| balanceamento | B | Concentração de alfa de 360.000 em 3,8 s | Mantido como espetáculo de fim de jogo, mas limitado: 48 células só no A.E., 2 por nave (vaga nuclear), igual a ~16 s de dano do Mapinguari concentrado na frente e totalmente interceptável; os modos pesados usam 16 unidades. |
| balanceamento | C | Faixas violadas (início 314, meio 418-447, OC 616-670, tripulação 1.879-2.011) | Início 264,5, meio 328,2, fim 379,6; OC no máximo 540,5; tripulação no máximo 1.556. |
| balanceamento | C | Alcances 400 / 520 / 720 | 300 / 400 / 600 m (torpedo 400 no de meio). |
| balanceamento | C | Dano por equivalente de munição: Boto 1.719, Sanguessuga 1.188 | Boto 1.000; Carrapato 875 / 937,5; nuclear 1.111 (o nuclear é exceção, Boiúna 1.103). |
| balanceamento | C | Pontos de corte de HP sem sentido com LOCK | O HP agora mira os pontos de corte dos pontos de defesa de alvo único (micro 380 = 3 tiros) e o gatilho LOCK (torpedo de fim 6.500 > 3 x 2.000). |
| balanceamento | C | Descarregar na troca falha com o paiol cheio | Não usado; `ModeSwitchDelay_k` é a correção principal. |
| balanceamento | C | Proximidade do Vespeiro a 280 m | 25 m (Discord), `StartDelay` 0,4. |
| balanceamento | C | O descarte do OC cobra 50% do Boto de 2 células | Descarte = CELLS/16 mísseis (6,25% de uma salva); torpedo e nuclear isentos. |
| balanceamento | C | Carga do Carrapato na categoria 'mine' | Sem `Targetable` no padrão; a variante opcional desarmável usa 'missile'. |
| balanceamento | todos | Eficiência das fábricas não decidida | Decidido: aceitar a economia de mísseis do jogo base; a alavanca do canister v2 está documentada (`resources_factories.factory_efficiency_decision`). |
| balanceamento | todos | Sem limite para o dano contínuo do napalm/Carrapato | Tabela `napalm_dot_upper_bound`: napalm <= A.E. por quadro mesmo se ninguém apagar nenhum quadro em chamas; Carrapato 1,0x o A.E. |
| fidelidade | A | Sem lançador de quatro casulos | Mula-sem-Cabeça: 4 casulos x 3x4 = 48 células (referência 4). |
| fidelidade | A | Fim de jogo entregou pouco | Mula: 5x6, 8 tripulantes, 18 pontos de comando, 77.000 cr + 2 urânio enriquecido, vaga nuclear, alfa de 360.000. |
| fidelidade | A | Sem míssil nuclear | Torpedo nuclear Iara (Mula, `bs_limit_nuke`). |
| fidelidade | A | Função principal da submunição fraca | Piranha que abre a 25 m, cone, mira fraca e tardia, ímã + espaçamento; números honestos em `balance_checks` (paridade com o A.E. contra ponto de defesa com 90% do dano, espalhamento por várias peças). |
| fidelidade | A | Salva de micromísseis modesta | 12 micromísseis em 0,73 s de 6 cassetes de tubo duplo. |
| fidelidade | A | Pouca empolgação | O esqueleto de B (caixa RAM -> casulos octogonais gêmeos -> bateria quádrupla), Piranha, iscas do Boto, mascaramento do Iara. |
| fidelidade | B | Sem torpedo convencional | Torpedo com iscas Boto na Caipora (2 por salva) e na Mula (4 por salva). |
| fidelidade | B | Lançador de início anulado com facilidade | Enxame de cassetes, 380 HP, ~58% passam por um ponto de defesa do jogo base. |
| fidelidade | B | Desempenho x espetáculo | <= 96 filhos por salva de lançador; o plano B de desempenho só tira visuais/espaçamento. |
| fidelidade | B | Salva parcial adiada | `DryFlush` na v1. |
| fidelidade | B | Desarmar o Carrapato vai além da regra do usuário | Padrão = a regra literal do usuário (carga que não pode ser alvo); desarmável é variante opcional. |
| fidelidade | B | Limite com duas vagas não provado, tira espaço do Mapinguari | Uma só vaga provada, `bs_limit_nuke`; a vaga da nau capitânia fica intocada; vaga dupla só como variante opcional depois do T18. |
| fidelidade | B | 'Pescoço em chamas' emissivo | O recesso do colar usa `M['ember']` (bem fraco), mais forte só em OC; sem partícula de chama por padrão; dentro do orçamento de 1-2%. |
| fidelidade | C | Alcance de 720 m / DPS acima das faixas / teto de OC 688 / divisão a 280 m / nuclear fora do limite / toggle Stream | Tudo rejeitado: teto de 600 m, faixas, teto de OC 550, divisão a 25 m, Iara em `bs_limit_nuke`, sem toggle Stream. |
| fidelidade | C | Seletores magros nas duas pontas | Início 2 tipos (micro A.E., micro napalm), meio 6, fim 7. |
| fidelidade | C | Menos espetáculo de salva | 12 / 16 / 48 pontas visíveis. |
| fidelidade | C | Custo moderado no fim de jogo | Mula 77.000 cr, 18 pontos de comando, 8 tripulantes, vaga nuclear. |
| fidelidade | C | Tubo do Arapuá sem armazenamento | `Burst = 2` num emissor por cassete (principal); o emissor de tubo duplo de C é o plano B. |
| viabilidade | A | D-A1 torre sem `Emitter` | `Emitter` da torre = `TargetEmitterProxy` -> `Emitter_0` do `Fire_k` ativo; colisor `ChainedTo = Turret`; `Location` informada. |
| viabilidade | A | D-A2 espoleta de 80-90 m sobre o próprio casco | 25 m, `StartDelay` 0,4 (plano B 1,0). |
| viabilidade | A | D-A3 cook-off só do modo escolhido | Cook-off por família contando todos os estoques. |
| viabilidade | A | D-A4 o plano B do torpedo muda um número | Nenhum `LinearDamping`: aceleração constante de 12, nada de que recuar. |
| viabilidade | A | D-A5 Carrapato sem ímã | Ímã + rastejar do buzz droid (combinação distribuída pelo SW). |
| viabilidade | B | D-B1 escala da Mula (242 emissores, 240 filhos) | 118 emissores (48 A.E. + 4 x 16 pesados + 4 + 2), 96 filhos por salva. |
| viabilidade | B | D-B2 salva em sequência do Iara sem mecanismo | `ShootCycle` por modo dentro do `Fire_k`; os torpedos usam a cadência da salva do lançador. |
| viabilidade | B | D-B3 napalm principal no valor bruto do gel | `StatusApplication` de fogo (`Interpolated`) + reserva de calor como principal; gel desligado até o T15. |
| viabilidade | B | D-B4 carga do Carrapato com `Targetable` 'missile' (trava do ponto de defesa no próprio casco) | Sem `Targetable`. |
| viabilidade | B | D-B5 o `SalvoCooldown` não pega a troca no meio da salva | `ModeSwitchDelay_k` em qualquer troca. |
| viabilidade | B | D-B6 duas vagas de `CategoryLimits` | Uma vaga (`bs_limit_nuke`). |
| viabilidade | B | D-B7 paióis por família = código novo | Orçado: variante nova `magazine_block` (`implementation_notes`). |
| viabilidade | C | D-C1 `ScorchedTrigger` dispara no conserto | Copiado ao pé da letra do jogo base (`TriggerWhenOn = false; TriggerWhenOff = true`), teste T19. |
| viabilidade | C | D-C2 divisão a 280 m sobre o nosso convés | 25 m. |
| viabilidade | C | D-C3 vazamento ao descarregar | Não usado. |
| viabilidade | C | D-C4 toggle Stream | Cortado. |
| viabilidade | C | D-C5 carga 'mine' | Sem `Targetable`. |
| viabilidade | C | D-C6 nuclear fora de `bs_limit_nuke` / 720 m | Dentro; 600 m. |
| viabilidade | C | D-C7 torre sem `Emitter` | Corrigido (ver D-A1). |
| viabilidade | C | D-C8 o plano B de desempenho muda `Count`/dano | O plano B de desempenho só tira visuais e o componente `Spacing`. |
| viabilidade | C | D-C9 leiautes de células por modo | Só três famílias de leiaute (fina / linha pesada / cassete de torpedo), todas por `RangeLow`/`RangeHigh` por casulo. |
| viabilidade | C | D-C10 tubo B do cassete sem armazenamento | `Burst 2` como principal. |
| viabilidade | comum | S1 testes das lacunas em aberto | Todos no plano de testes (T06-T11, T14, T14b). |
| viabilidade | comum | S2 peso das células no cook-off | Aproximação documentada (míssil nas células = 1 unidade); nunca duplica peças. |
| viabilidade | comum | S3 colisão de IDs entre A e B | Um mapa de IDs: box = início, twin = meio, quad = fim. |

## 13. Apresentação para o usuário

> Texto de `user_presentation_ptbr` no spec dos mísseis.

Três lançadores, um para cada fase. Todos são torres de convés (em cima do casco), operados só pela tripulação e **sem energia**.

### Como funciona (igual nos três)
- **Estoque interno:** cada lançador tem um paiol por tipo de peça (A.E., T., P.E.M., nuclear). A tripulação carrega as peças de míssil do jogo base até ele. O estoque cheio dá 3 salvas.
- **Recarga automática:** um autocarregador passa um míssil por vez do paiol para as células visíveis. **Só funciona com tripulação no posto.** Com todas as células cheias, sai a salva em sequência e a recarga recomeça. Se o paiol acabar, a salva parcial sai mesmo assim.
- **Trocar de míssil não dá salva grátis:** ao trocar o tipo, o lançador espera um ciclo completo de recarga do tipo novo.
- **Overclock (só meio e fim):** a recarga fica 1,5 vez mais rápida (P.E.M.: 1,2 vez). Custos: calor por peça carregada (precisa de radiador), cerca de 1 em cada 16 mísseis é descartado a cada salva, o paiol esvazia mais rápido, pausa de 3 s ao desligar e, sem radiador, o lançador esquenta, pega fogo e explode junto com o estoque. Nunca acelera o torpedo nuclear.
- **Lançador cheio é uma bomba:** destruído ou queimado, explode proporcional ao estoque (cerca de 850 de dano por peça A.E. guardada).

### Os lançadores
- **Início - Tocandira (Caixa de Micromísseis de Convés), 2x2, 1 tripulante.** Caixa estilo RAM com 6 cassetes de tubo duplo: 12 micromísseis em 0,73 s a cada 9,1 s, alcance 300 m. Mísseis: Muriçoca (alto-explosivo) e Taturana-mirim (incendiário). Contra um ponto de defesa do jogo base, cerca de 58% da salva passa.
- **Meio - Caipora (Lançador Duplo de Mísseis de Convés), 3x3, 2 tripulantes.** Dois casulos octogonais e uma cúpula com olho sensor: 16 mísseis em 2 s a cada 19,0 s, alcance 400 m. Mísseis: Jararaca, Piranha, Carrapato, Taturana, Poraquê e o torpedo Boto (2 por salva). Overclock: Fúria da Caipora.
- **Fim - Mula-sem-Cabeça (Bateria Pesada de Mísseis Quádrupla), 5x6, 8 tripulantes, 18 pontos de comando, 77.000 créditos.** Corpo sem cabeça com quatro casulos de 3x4 em braços hidráulicos: 48 mísseis pesados em 3,1 s a cada 15,8 s, alcance 600 m. Tem todos os mísseis, inclusive o nuclear Iara. Divide a vaga nuclear com a Boiúna (no máximo 2 por nave, em qualquer combinação). Overclock: Estouro da Boiada.

### Os mísseis
- **Jararaca (Alto-Explosivo):** explosão padrão; é o míssil comum, como o míssil normal do SW:ACD. Em salva grande, satura os pontos de defesa.
- **Piranha (Submunições, no estilo Transformers):** abre a 25 m do casco e solta 4 (meio) ou 6 (fim) minimísseis que se espalham e acertam várias peças. Faz 90% do dano do míssil A.E. O contra é flak de área de raio grande.
- **Carrapato (Grudento):** se for abatido no voo, perde-se; se acertar o casco, gruda, pisca e explode 2,5 s depois, com 50% de chance de matar a tripulação que vier consertar. Não gruda em escudo.
- **Taturana (Napalm):** explosão pequena, fogo garantido na peça atingida e calor em volta que continua acendendo incêndios. Extintor, espuma e blindagem são o contra.
- **Poraquê (P.E.M.):** drena bateria e escudos em área (1.500 por peça P.E.M., abaixo do míssil P.E.M. do jogo base). Não afeta as armas do Bullet Strike.
- **Boto (Torpedo com Iscas):** torpedo lento e resistente que solta 4 a 6 iscas para enganar os pontos de defesa. Faz 24.000 (meio) ou 48.000 (fim) de dano explosivo.
- **Iara (Torpedo Nuclear, só na Mula):** 120.000 + 40.000 de dano, 2 por salva a cada 20 s. Sozinho morre para qualquer flak; dispare o Iara primeiro e uma salva de mísseis A.E. 1 a 3 s depois para os dois chegarem juntos.

### O que é arriscado e precisa de teste no jogo
1. **Carrapato:** a carga grudar numa nave que gira e acelera. Há 4 planos B com os mesmos números.
2. **Piranha:** os minimísseis herdarem o alvo e não estourarem sobre o nosso casco. Plano B: ímã para o casco inimigo e atraso maior.
3. **Trava das células** (salva completa antes de recarregar). Plano B com temporizador.
4. **Mísseis sobre o próprio convés:** não podem bater na nossa torre nem desviar do nosso casco.
5. **Nossa CIWS contra os nossos mísseis**, e o modelo da CIWS (cada disparo mata 1 míssil ou vários). Isso muda os números de interceptação.
6. **Desempenho** com muitas submunições; **torpedo com iscas** (dois disparos no mesmo evento); **vaga nuclear** dividida com a Boiúna.

Todas as mecânicas usam componentes do jogo base, a categoria 'missile' (compatível com o SW:ACD) e funcionam no 0.30.4 e no 0.30.5. Cada risco tem um plano B que não muda nenhum número.

## Resumo

| Codinome | Lançador | Fase | Tamanho | Trip. | Salva A.E. | Ciclo | Alcance | Mísseis | DPS efetivo por quadro (OC) | Overclock | Limite |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tocandira | Caixa de Micromísseis de Convés | início | 2x2 | 1 | 12 em 0,73 s | 9,1 s | 300 m | Muriçoca, Taturana-mirim | 264,5 (381,4, desligado) | Enxame Furioso (desligado) | sem |
| Caipora | Lançador Duplo de Mísseis de Convés | meio | 3x3 | 2 | 16 em 2,00 s | 19,0 s | 400 m | Jararaca, Piranha, Carrapato, Taturana, Poraquê, Boto | 328,2 (467,6) | Fúria da Caipora | sem |
| Mula-sem-Cabeça | Bateria Pesada de Mísseis Quádrupla | fim | 5x6 | 8 | 48 em 3,13 s | 15,8 s | 600 m | Jararaca, Piranha, Carrapato, Taturana, Poraquê, Boto, Iara | 379,6 (518,1) | Estouro da Boiada | 2 por nave (vaga nuclear) |

## 14. Gerador: variantes de mecânica e estágios

Toda mecânica arriscada é uma **variante selecionável** no spec (`mechanic_variants`). O padrão é o projeto principal; cada outra opção é o plano B citado no plano de testes. Trocar uma variante muda só o mecanismo gerado - nenhum número de balanceamento (dano, HP, recarga, cadência da salva, células, peças, alcance, custo). Para gerar um plano B para um teste: `BS_MSL_VARIANTS="rack_gate=salvo_timer,cassette=twin_emitter" python3 tools/build_mod.py ...`.

| variante | teste | padrão | plano(s) B | estágio |
|---|---|---|---|---|
| `rack_gate` | T02 | `latch` | `salvo_timer` | 1 |
| `loader_crew_gate` | T03 | `is_operational` | `explicit_partcrew` | 1 |
| `mode_switch_delay` | T04 | `per_mode` | `single_longest` | 1 |
| `prefilled_switch` | T04 | `full_delay` | `oc_delay` (comportamento do estágio 3) | 4 |
| `dry_flush` | T05 | `debounced` | `instant` (comportamento dos estágios 1-3), `off` | 1 (`debounced`: 4) |
| `source_part_collision_delay` | T06 | `ticks_1_5` | `s_0_3` | 1 |
| `homing_avoidance` | T07 | `omit` | `raycast_250`, `no_avoid_friendlies` | 1 |
| `cassette` | T22 | `burst` | `twin_emitter` | 1 |
| `cell_sync` | T21 | `reset_each_reload` | `free_cycle` | 1 |
| `overlays` | T21 | `per_pod` | `combined` | 1 |
| `napalm_fire` | T15 | `status_application` | `all_hit_part_tiles` | 1 |
| `napalm_gel` | T15 | `off` | `on` | 2 |
| `ai_firepower` | T23 | `full` | `x0_8` | 1 |
| `selector_ids` | T24 | `shared` | `per_launcher` | 1 |
| `early_overclock` | - | `disabled` | `enabled` | 1 |
| `cluster_children` | T11 | `inherit_target_and_magnet` | `magnet_only` | 2 |
| `cluster_hp_inherit` | T11 | `all_paths` | `fuses_only` | 4 |
| `cluster_randomize_target` | T11 | `off` | `on` (só em build de experimento) | 2 |
| `limpet_anchor` | T14 / T14b | `F1` | `F1_drill`, `F2`, `F3`, `F4` | 2 |
| `limpet_repeating` | T14 / Q11 | `off` | `isolated_file` (`_rep.rules` só do SW, nenhum lançador o dispara) | 2 |
| `limpet_defusable` | T14 | `off` | `on` (carga com `Targetable` 500 / 600 'missile') | 2 |
| `emp_rider` | T16 | `on` | `off` | 2 |
| `emp_shield_drain` | T16 | `area` | `single_part` | 2 |
| `torpedo_decoys` | T17 | `spawn_on_stage` | `emitter` | 2 |
| `category_limits` | T18 | `on` | `off` | 2 |
| `ciws_vs_own_missiles` | T09 | `as_is` | `enemies_only` (filtro só de inimigos na nuvem de estilhaços da Pororoca) | 2 |
| `performance_strip` | T13 | `off` | `on` | 2 |

Estágios do gerador (`BUILD_LAUNCHERS` / `BUILD_PAYLOADS` em `tools/bs_data.py`):
- **Estágio 1 (pronto):** Tocandira (`rafaeltessaro.bs_msl_box`) com Muriçoca (micro A.E.) e Taturana-mirim (micro incendiário); toda a lógica de lançamento (paióis por família, autocarregador tripulado, trava das células, salva em sequência com células em LIFO, atraso de troca por modo, `DryFlush`, cook-off por família), o seletor `bs_missile_type` com as 7 escolhas, as techs `bs_msl_box` e `bs_msl_napalm`, a arte provisória da época (já substituída pelos renders 3D, ver o estágio 3) e o contrato de arte 3D (`tools/blender/STYLE.md` seção 8, `render_part.py` do tipo `launcher`). A ligação do overclock é gerada e testada atrás de `early_overclock=enabled`, mas fica desligada (regra do mod).
- **Estágio 2 (pronto): cargas.** Todo arquivo de míssil de `missile_types[].variants[].files`, em todo nível de lançador, é gerado (`tools/bsgen/shots.py`): Jararaca e Taturana na Caipora/Mula, Piranha (portador com `BURST` por proximidade / tempo / impacto + filho com mira tardia, ímã para o casco e espaçamento entre mísseis), Carrapato (míssil + carga lenta de `PenetratingHit` com ímã e farol piscando; planos B `F1_drill`, F2 com o status de peça `rafaeltessaro.bs_limpet_<twin|quad>` registrado em `statuses.rules`, F3 carga com `HitObject` e `Speed` 0, F4 explosão no impacto; arquivo isolado só do SW com `Repeating` atrás de `limpet_repeating`), Poraquê (dreno de bateria em área + acerto direto + explosão estrutural + carona `disruptor_drain`), Boto e Iara (estágio de lançamento de 1,5 s -> ogiva + iscas por dois `SpawnBullets`; o Iara com o cogumelo da Boiúna). Os números que cada carga precisa além das tabelas das variantes ficam em `missile_types[].payload_params` (uma cópia estruturada de `payload_mechanic`, nenhum número de balanceamento novo). `tools/bs_data.py` aborta se a lista de arquivos, o dano efetivo, o alfa da salva ou um limite rígido da carga (filhos por portador, HP total dos filhos, HP do portador, dreno por peça P.E.M., torpedo >= 80.000 precisa de limite por nave) divergir do spec. Arquivos de lançadores que ainda não são gerados existem, mas nenhuma peça os dispara. A categoria `bs_limit_nuke` da Mula vem do spec (`category_limits=off` a tira).
- **Estágio 3 (pronto): Caipora e Mula-sem-Cabeça.** `BUILD_LAUNCHERS` tem os três lançadores e todos os modos de míssil do spec.
  - Leiautes (`tools/launcher_layout.py`): `fine16` com casulos `pattern: "3-2-3"` e `torpedo2` (Caipora); `fine48`, `heavy16` (uma linha de 3 tubos = uma unidade pesada), `torpedo4` e `torpedo2_inner` (Mula; os casulos externos mostram persianas fechadas, um `Graphics` dentro do `Fire_nuclear`). Cada unidade tem uma `form` (`tube` / `heavy` / `torpedo`) e uma `box` de nariz para a arte.
  - Overclock na Caipora e na Mula (`overclock.enabled` do spec): `Interval` do `Autoloader_k` e `Duration` do `ModeSwitchDelay_k` divididos pelo fator do modo (1,5, P.E.M. 1,2, nuclear nenhum), calor por peça carregada (425 / 400) + calor constante (100 / 150 de calor/s), descarte das peças de CELLS/16 mísseis a cada vez que as células enchem (torpedo, nuclear e salvas abaixo de 16 isentos), reset do overclock herdado, portas térmicas, tooltip de overclock com o ciclo A.E. em OC, e um `OverclockGlowGraphics` (`turret_oc.png`, `IsOverclocked`) para o olho da cúpula / a brasa do colar.
  - A Mula em `bs_limit_nuke` (máximo 2, junto com a Boiúna; o nome do limite vira "Nuclear Weapon(s)" / "Arma(s) Nuclear(es)"); `category_limits=off` tira.
  - Efeitos por fase: Caipora com tremor de 0,01 por lançamento e torpedos com o som de lançamento nuclear do jogo base; Mula com o sopro `cannon_smoke_deck`, tremor de 0,02 e uma pancada de 0,15 quando as células esvaziam. Com mais de um casulo, a baforada sai atrás do casulo que disparou (`MultiTrigger` `PodFired_<casulo>` dentro de cada `Fire_k`).
  - `torpedo_decoys=emitter` (plano B do T17): um `DecoyEmitter_i` por célula de torpedo (`Burst` = iscas, `BurstDelay 0.1`, sem `ResourceStorage`) ao lado do torpedo de um estágio só.
  - Techs da Carreira (twin, cluster, emp, limpet, torpedo, twin-overclock, quad, nuclear, quad-overclock) e techs do Construir e Batalhar para a Caipora e a Mula (+ os overclocks delas; também liberam as peças de míssil das suas famílias, `ResourcesUnlocked`); a Tocandira continua na lista branca do Construir e Batalhar.
  - `tools/bs_data.py` também aborta se o ciclo em overclock, a regra do descarte, o número de emissores (`emitter_components`) ou o estoque de cook-off (paiol + maior conjunto de células da família, em peças = `cookoff[].parts_full`) divergirem do spec, ou se o overclock puder mexer na recarga nuclear.
  - Arte: os três lançadores têm renders 3D prontos em `art3d/bs_msl_box`, `art3d/bs_msl_twin` e `art3d/bs_msl_quad` (feitos com `tools/blender/render_part.py` do tipo `launcher`, com `cell(..., form, box)`, `shutter()` e `oc_glow()`, seguindo o contrato de arte de `tools/blender/STYLE.md` seção 8: formas, persianas, `turret_oc.png`); o build só copia esses renders. Os desenhos procedurais provisórios desta etapa (`tools/bsgen/sprites.py`) só voltam com `BS_ARTE_PROCEDURAL=1`.
- **Estágio 4 (pronto): correções da revisão** (`GENERATOR_STAGE = 4`; nenhum número de balanceamento mudou).
  - `DryFlush` com espera (`dry_flush=debounced`, T05): as células parcialmente carregadas só disparam depois de `DRY_DELAY` = CELLS x RELOAD (sem overclock) com o paiol da família sem conseguir carregar (rampa `ValueTween` + `ThresholdToggle` 100%, padrão do chaingun), então uma Caipora ou Mula com pouco abastecimento continua disparando salvas cheias em sequência em vez de pinga-pingas de 1-5 mísseis; `instant` mantém o comportamento antigo.
  - Células já cheias em overclock (`prefilled_switch=full_delay`, T04): trocar para um modo com as células já cheias também espera `PrefilledDelay_k` = uma recarga sem overclock (`TriggerProxy` em `ModeOn_k` com `ProxyToggle` = a trava das células), então células carregadas sem pagar o calor do overclock nunca disparam na cadência de overclock.
  - Cook-off por armazenamento: um par `ScorchedEffects`/`DeathEffects` para o paiol e para as células de cada modo, `BaseValue` = valor da família x peças do armazenamento / `parts_full`, então cada peça guardada vale valor/`parts_full` (A.E. da Caipora 61.200 + 20.400 e A.E. da Mula 183.600 + 61.200 com o estoque cheio, Iara 2.000 por peça); `_check_cookoff` em `bsgen/launchers.py` recalcula o que o motor vê a partir dos armazenamentos gerados e aborta se divergir.
  - `ReloadProgressBar` sem `ValueRange` (as células fornecem o enchimento 0..1; a faixa antiga [0, CELLS] limitava a barra a 1/CELLS).
  - Portador da Piranha: o `TimedFuse` e o `Hit` de impacto têm `FactorEffectsWith = Targetable` como o `ProximityFuse`, então os filhos herdam o HP restante do portador em todos os caminhos (`cluster_hp_inherit`, T11).
  - Sobreposições recortadas no retângulo de cada casulo (`overlay_rect` / `rect_placement` em `tools/launcher_layout.py`; `Location`/`Size` dos `ResourceSprites`): cerca de 8 MiB de texturas de sobreposição nos três lançadores em vez de 128 MiB; `render_part.py` grava `rect` no meta (STYLE.md 8.1).
  - Os lançadores usam a `base_part` do spec (Caipora em `base_med_part_terran_overclock`, como as 3x3 `factory_he` / `reactor_med` do jogo base).
  - Construir e Batalhar: a tech sempre oferecida `rafaeltessaro.bs_bb_bs_msl_box_ammo` (5.000) libera as `missile_part_he` / `missile_part_thermal` da Tocandira.
  - Limite cosmético documentado (T21, STYLE.md 8): uma salva parcial `DryFlush` ou o resto de uma salva interrompida depois de voltar ao modo começa pela última célula.
- `tools/bs_data.py` aborta o build se o tamanho da salva, a duração da salva, o ciclo, o alfa ou o estoque de cook-off gerados divergirem dos números `computed` deste spec.
