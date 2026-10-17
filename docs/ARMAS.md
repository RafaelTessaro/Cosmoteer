# Bullet Strike: armas, munições e fábricas

> Gerado automaticamente por `tools/make_docs.py` a partir de `tools/spec/bullet_strike_spec.json`.
> DPS = dano por segundo com munição padrão, sem overclock (explosões contam inteiras).

## Início de jogo

| Arma | Codinome | Tamanho | Tripulação | Alcance | DPS | Munição | Overclock |
|---|---|---|---|---|---|---|---|
| **Metralhadora Leve de Convés** | Wasp | 1x1 | 1 | 220 m | 260 | Munição avulsa (vanilla) | - |
| **Metralhadora Pesada de Convés** | Hornet | 1x2 | 1 | 240 m | 520 | Munição avulsa (vanilla) | - |
| **Canhão Automático de Convés 20 mm** | Stinger | 2x2 | 1 | 250 m | 1.050 | Munição avulsa (vanilla) | - |
| **Flak Leve de Convés** | Umbrella | 2x2 | 1 | 180 m | 3.000/s contra projéteis | Munição avulsa (vanilla) | - |

## Meio de jogo

| Arma | Codinome | Tamanho | Tripulação | Alcance | DPS | Munição | Overclock |
|---|---|---|---|---|---|---|---|
| **Metralhadora Pesada Quádrupla** | Quadra | 2x2 | 2 | 300 m | 1.520 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Minigun de Convés** | Buzzsaw | 2x3 | 2 | 310 m | 2.160 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Canhão Naval Automático 76 mm** | Thumper | 3x4 | 3 | 340 m | 3.900 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Gatling de Plasma** | Sunspray | 3x3 | 2 | 320 m | 2.250 | Células de plasma | sim |
| **CIWS de Convés** | Bastion | 3x3 | 2 | 240 m | 9.000/s contra projéteis | Carregador padrão | sim |

## Fim de jogo

| Arma | Codinome | Tamanho | Tripulação | Alcance | DPS | Munição | Overclock |
|---|---|---|---|---|---|---|---|
| **Canhão Rotativo Pesado 30 mm** | Thunderclap | 4x4 | 4 | 500 m | 5.120 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Canhão Naval Duplo 155 mm** | Hammerfall | 4x5 | 5 | 520 m | 6.400 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Canhão de Plasma Pesado** | Sunhammer | 4x5 | 4 | 550 m | 4.800 | Células de plasma | sim |
| **Obuseiro Nuclear** | Judgement | 5x6 | 5 | 600 m | 7.700 | Projéteis nucleares | sim |
| **Torre Naval Tripla 406 mm** | Leviathan | 6x7 | 8 | 600 m | 13.044 | Carregadores (Padrão/Perfurante/Perf.-Explosiva/EMP) | sim |
| **Bateria Flak Pesada** | Skywall | 4x4 | 4 | 320 m | 12.000/s contra projéteis | Carregador padrão | sim |

## Munições

| Recurso | Pilha por tile | Observação |
|---|---|---|
| **Carregador Padrão** | 4 | 1 magazine = 50 MG-round units (packed from 6 vanilla bullets). Minigun/Quad HMG: 50 shots; 30 mm rotary: 15 shots; 76 mm: 2 shells; 155 mm: 1 shell; 406 mm: 2 magazines per shell; Deck CIWS: 8 bursts; Heavy Flak: 3 bursts. Stack 4 = max 4 per crew trip, 16 per 2x2 storage bay. |
| **Carregador Perfurante** | 4 | Same shot count per magazine as the standard magazine for each gun (mode 1 of the bs_ammo_type toggle). Recipe value 8.5 bullet-eq. |
| **Carregador Perfurante-Explosivo** | 4 | Same shot count per magazine as standard (mode 2). Recipe value 11 bullet-eq. |
| **Carregador EMP** | 4 | Same shot count per magazine as standard (mode 3). Recipe value 12.67 bullet-eq + 200 battery of factory power. |
| **Célula de Plasma** | 6 | Plasma Gatling: 1 cell = 20 bolts; Heavy Plasma Cannon: 1 cell = 1 bolt. Recipe value 5 bullet-eq + 300 battery. 6 per crew trip. |
| **Projétil Nuclear** | 2 | Nuclear Howitzer: 1 shell = 1 shot. Recipe value 67.5 bullet-eq (1/8 enriched uranium + 5 bullets). 2 per crew trip; cooks off violently when the holder is destroyed. |

## Fábricas

| Fábrica | Entrada | Saída | Tempo | Energia |
|---|---|---|---|---|
| **Prensa de Carregadores** | 6 munição | 1 Carregador Padrão | 1 s | não usa |
| **Linha de Carregadores Perfurantes** | 12 munição + 1 ferro | 2 Carregador Perfurante | 2 s | 0.15 bateria/ciclo |
| **Linha de Carregadores Perfurante-Explosivos** | 12 munição + 1 ferro + 1 enxofre | 2 Carregador Perfurante-Explosivo | 2 s | 0.2 bateria/ciclo |
| **Linha de Carregadores EMP** | 18 munição + 1 cobre | 3 Carregador EMP | 3 s | 0.6 bateria/ciclo |
| **Condensador de Células de Plasma** | 1 enxofre + 1 cobre | 5 Célula de Plasma | 5 s | 1.5 bateria/ciclo |
| **Fundição de Projéteis Nucleares** | 1 urânio enriquecido + 40 munição | 8 Projétil Nuclear | 16 s | 2 bateria/ciclo |

## Tipos de munição (seletor das armas de meio/fim de jogo)

| Tipo | Para que serve |
|---|---|
| **Padrão** | Munição versátil. Os canhões disparam granadas explosivas que estouram no impacto. |
| **Perfurante** | Penetradores endurecidos que atravessam blindagem (a blindagem conta pela metade) e destroem o que está atrás. Fracos contra escudos. |
| **Perfurante-Explosiva** | Atravessa uma ou duas placas de blindagem e então detona DENTRO do casco inimigo. |
| **EMP** | Cada acerto drena bateria de escudos e partes energizadas. Menos dano ao casco, mas ótima contra naves que dependem de energia e escudos. |
