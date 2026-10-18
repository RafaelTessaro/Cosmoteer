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

## Lança-mísseis de convés

> Projeto completo em `docs/MISSEIS_PROJETO.md` (spec `tools/spec/bullet_strike_missiles.json`). Ciclo = recarga do rack inteiro + salva.

| Lançador | Codinome | Fase | Tamanho | Tripulação | Míssil | Salva | Ciclo | Alcance | Recurso |
|---|---|---|---|---|---|---|---|---|---|
| **Caixa de Micromísseis de Convés** | Tocandira | Início | 2x2 | 1 | Micromíssil (Muriçoca) | 12 em 0,7 s | 9,1 s | 300 m | missile_part_he |
| **Caixa de Micromísseis de Convés** | Tocandira | Início | 2x2 | 1 | Micromíssil Incendiário (Taturana-mirim) | 12 em 0,7 s | 9,1 s | 300 m | missile_part_thermal |

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
