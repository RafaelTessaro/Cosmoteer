# Bullet Strike: armas de convés movidas a munição (mod para Cosmoteer)

![Bullet Strike](BulletStrike/logo.png)

**Bullet Strike** é um mod para **Cosmoteer: Starship Architect & Commander** focado em armas que usam
**munição** em vez de energia. Todas as armas são **de convés**: ficam por cima da nave, podem ser cercadas
de blindagem e atiram por cima do casco. Do começo ao fim do jogo, a sensação é de batalha naval no espaço:
traçantes, clarões de boca, granadas explodindo, flak enchendo o céu. É *tiro, porrada e bomba*.

- Versão do jogo: **0.30.4** (estável) e **0.30.5** (RC).
- Compatível com **Star Wars: A Cosmos Divided** (SW:ACD).
- Textos em **português (pt-BR)** e **inglês**.

> ⚠️ **Status: ainda não testado dentro do jogo.** Os arquivos foram gerados a partir dos arquivos de regras
> reais do Cosmoteer 0.30.5 e passaram por um validador que confere todas as referências, caminhos, imagens e
> textos (0 erros). Mesmo assim, só abrindo o jogo dá para ter certeza. Veja [Como testar](#como-testar).

## O que o mod traz

- **Só armas de convés, só munição, sem energia.** Cada arma precisa só de tripulação: quanto maior a
  arma, mais tripulantes.
- **Progressão por tamanho:**
  - **Início (1-2 blocos):** metralhadoras e autocanhões, alcance ~220-250 m.
  - **Meio:** minigun, metralhadora quádrupla, **canhão naval automático** ("tum, tum, tum"), gatling de
    plasma, CIWS. Alcance ~300-340 m.
  - **Fim:** canhão rotativo de 30 mm, torre naval dupla de 155 mm, canhão de plasma pesado, **obuseiro
    nuclear** e a **torre tripla de 406 mm** de encouraçado. Alcance 500-600 m.
- **Defesa multi-alvo:** flak/CIWS com explosão aérea que danifica **vários** mísseis, minas, granadas,
  disparos laser e tiros iônicos (inclusive os do SW:ACD) **de uma vez**. Em compensação, gasta muita munição.
  Feixes (como o do prisma iônico) não podem ser abatidos, igual ao jogo base.
- **Carregadores em vez de fitas de munição:** a fábrica produz munição, a **prensa** empacota em
  carregadores e a tripulação leva o carregador até a arma. Os carregadores especiais (Perfurante, EMP) e os
  projéteis nucleares são feitos a partir dos carregadores Padrão; Perfurante e Perfurante-Explosiva usam o
  mesmo carregador. Cada arma abre o carregador em N disparos
  (por exemplo, 50 tiros de metralhadora). Nada de fileiras de magazines ocupando a nave.
- **Seletor de munição** nas armas de meio e fim de jogo, igual ao do lança-mísseis:
  **Padrão**, **Perfurante** (atravessa blindagem), **Perfurante-Explosiva** (atravessa e explode dentro do
  casco) e **EMP** (drena um pouco de escudo e bateria a cada acerto).
- **Munições especiais:** **células de plasma** (ótimas contra escudos) e **projéteis nucleares**.
- **Lança-mísseis de convés:** três lançadores (início, meio e fim de jogo) que disparam salvas de mísseis por
  cima do casco, com 7 tipos de míssil. Veja [Mísseis](#mísseis) abaixo.
- **Overclock** nas armas de meio e fim de jogo: mais cadência, dano ou alcance em troca de calor.
- **Aba própria "Bullet Strike"** no menu de construção, techs no modo **Carreira** e no **Build & Battle**.
- **Limite por nave:** no máximo 2 armas nucleares (obuseiro nuclear Boiúna e bateria de mísseis
  Mula-sem-Cabeça, em qualquer combinação) e 2 torres de 406 mm (a arma do encouraçado), para não ficar roubado.
- **Arma de fim de jogo muito forte, mas muito cara:** a torre tripla de 406 mm causa ~16.000 de dano por
  segundo a 600 m, mas exige 10 tripulantes, 20 pontos de comando e uma linha de munição pesada
  (~30 viagens de carregadores por minuto).

## Mísseis

Três lança-mísseis de convés, todos operados só pela tripulação e **sem energia**. Os mísseis usam as **peças de
míssil do jogo base** (A.E., T.C./térmica, PEM e nuclear), então as fábricas de mísseis vanilla abastecem os
lançadores (e os do SW:ACD usam as mesmas peças).

**Como funciona (igual nos três):**
- **Paiol interno:** cada lançador tem um paiol por família de peça. A tripulação leva as peças até ele. Paiol
  cheio = 3 salvas.
- **Recarga automática só com tripulação:** um autocarregador passa um míssil por vez do paiol para as células
  visíveis (dá para ver as ogivas carregadas no casulo). Sem tripulação no posto, a recarga para.
- **Salva em sequência:** com todas as células cheias, sai a salva inteira em ripple (a última célula carregada
  dispara primeiro); depois a recarga recomeça. Se o paiol acabar de vez (uma recarga inteira sem chegar peça), a
  salva parcial sai mesmo assim; uma entrega só atrasada não quebra a salva cheia.
- **Trocar de míssil não dá salva grátis:** o tipo novo espera uma recarga completa (um rack que já estava cheio
  espera a recarga sem overclock, então encher os racks antes da luta não rende cadência de overclock de graça).
- **Overclock (meio e fim):** recarga 1,5 vez mais rápida (PEM 1,2 vez; o torpedo nuclear nunca acelera). Custa
  calor por peça carregada mais calor constante (precisa de radiador), descarta cerca de 1 em cada 16 mísseis por
  salva, dá uma pausa de 3 s ao desligar e esvazia o paiol mais rápido.
- **Lançador cheio é uma bomba:** destruído ou queimado, explode proporcional ao estoque de cada família.

| Lançador | Fase | Tamanho | Tripulação | Salva | Alcance | Mísseis | Overclock | Limite |
|---|---|---|---|---|---|---|---|---|
| **Tocandira** (Caixa de Micromísseis de Convés) | início | 2x2 | 1 | 12 micromísseis em 0,73 s a cada 9,1 s | 300 m | Muriçoca, Taturana-mirim | - | - |
| **Caipora** (Lançador de Mísseis de Convés de Casulo Duplo) | meio | 3x3 | 2 | 16 mísseis em 2 s a cada 19 s | 400 m | Jararaca, Piranha, Carrapato, Taturana, Poraquê, Boto | Fúria da Caipora | - |
| **Mula-sem-Cabeça** (Bateria Pesada de Mísseis Quádrupla) | fim | 5x6 | 8 | 48 mísseis em 3,1 s a cada 15,8 s | 600 m | os 6 da Caipora + Iara | Estouro da Boiada | 2 por nave (vaga nuclear, com a Boiúna) |

**Os mísseis** (seletor no lançador; cada tipo é liberado por uma tech na Carreira):
- **Jararaca / Muriçoca (alto-explosivo):** explosão direta; em salva grande, satura a defesa de ponto.
- **Piranha (submunições):** abre a 25 m do casco inimigo e solta 4 (meio) ou 6 (fim) minimísseis que se espalham
  por várias peças. O contra é flak de área.
- **Carrapato (grudento):** gruda no casco, pisca e explode 2,5 s depois, com 50 % de chance de matar a tripulação
  que vier consertar. Abatido no voo, se perde; num escudo só estoura.
- **Taturana / Taturana-mirim (napalm):** explosão pequena, fogo garantido na peça atingida e calor em volta que
  continua acendendo incêndios.
- **Poraquê (PEM):** drena bateria e escudos em área. As armas do Bullet Strike não usam bateria e são imunes.
- **Boto (torpedo com iscas):** torpedo lento e resistente que solta iscas para enganar a defesa de ponto.
- **Iara (torpedo nuclear, só na Mula):** 120.000 + 40.000 de dano. Sozinho morre para flak: dispare o Iara primeiro
  e uma salva pesada 1 a 3 s depois para os dois chegarem juntos.

Números completos (recarga, ciclo, DPS, paiol, techs) em [docs/ARMAS.md](docs/ARMAS.md#mísseis-de-convés) e o
projeto inteiro em [docs/MISSEIS_PROJETO.md](docs/MISSEIS_PROJETO.md). A arte dos lançadores ainda é provisória
(procedural); o contrato para os modelos 3D está em `tools/blender/STYLE.md`, seção 8.

A tabela completa de armas, munições e fábricas (com alcance, DPS, tripulação e receitas) está em
**[docs/ARMAS.md](docs/ARMAS.md)**. As imagens de cada peça ficam em [docs/preview](docs/preview).

## Como instalar

1. Baixe esta pasta do repositório: **`BulletStrike/`**.
2. Copie a pasta inteira para a pasta de mods do Cosmoteer:
   - Windows: `C:\Users\<seu usuário>\Saved Games\Cosmoteer\<seu SteamID>\Mods\`
   - O resultado deve ficar assim: `...\Mods\BulletStrike\mod.rules`
3. Abra o Cosmoteer, vá em **Mods**, ative o **Bullet Strike** e reinicie o jogo.
4. Para usar com o Star Wars: A Cosmos Divided, basta ativar os dois. Não importa a ordem.

## Como testar

1. Abra o jogo com o **modo desenvolvedor** (na Steam: botão direito no Cosmoteer → Propriedades →
   Opções de inicialização → `--devmode`). Assim os erros de carregamento aparecem com detalhes.
2. Se o jogo travar ao carregar, o motivo aparece nas primeiras ~20 linhas do log, acima de
   `--- End of inner exception stack trace ---`. Mande essas linhas que eu corrijo.
3. No **modo Criativo**, monte uma nave de teste e confira:
   - [ ] As peças aparecem na aba **Bullet Strike** e dá para colocá-las cercadas de blindagem.
   - [ ] A tripulação leva munição/carregadores até as armas, e a arma atira por cima do casco.
   - [ ] O botão de **seletor de munição** troca entre Padrão / Perfurante / Perfurante-Explosiva / EMP.
   - [ ] O **overclock** liga e gera calor (precisa de tubos de calor/radiadores, igual às armas do jogo).
   - [ ] A minigun e o canhão rotativo **aceleram** enquanto atiram.
   - [ ] A flak/CIWS derruba mísseis e projéteis (teste no modo Defender).
   - [ ] As fábricas (prensas) produzem carregadores, células de plasma e projéteis nucleares.
   - [ ] **Lança-mísseis:** a tripulação enche o paiol; as células do casulo enchem uma a uma só com tripulação
     no posto; a salva sai inteira e as ogivas somem do casulo na ordem certa; trocar o tipo de míssil espera uma
     recarga; os mísseis passam por cima do próprio casco sem explodir nele.
   - [ ] **Mula-sem-Cabeça:** não deixa ter mais de 2 junto com a Boiúna; no modo Iara os casulos externos
     fecham as persianas; o overclock não acelera o Iara.

## Compatibilidade com Star Wars: A Cosmos Divided

- O Bullet Strike **não substitui nenhum arquivo** do jogo nem do SW:ACD: só **adiciona** peças, recursos,
  techs e textos (ações `AddMany`/`Add`).
- Todos os IDs têm prefixo próprio (`rafaeltessaro.bs_*`, `BS*`), então não há colisão de nomes.
- As defesas miram também a categoria `ion_shot` (tiros iônicos do SW:ACD) e `laser` (turbolasers).
- O limite de armas nucleares usa o mesmo método em duas etapas do SW:ACD, então os dois mods convivem.
- Os mísseis usam a categoria de alvo `missile`, então as defesas de ponto e flak do jogo e do SW:ACD os
  derrubam; o seletor de míssil é próprio (`bs_missile_type`) e não mexe no do jogo nem no do SW:ACD.
- As armas do Bullet Strike não usam bateria, então os canhões iônicos do SW:ACD quase não as afetam. Em
  troca, a munição **EMP** é forte contra as naves do SW:ACD, que dependem de energia.

## Como mudar o balanceamento

Todos os números ficam em **`tools/spec/bullet_strike_spec.json`** (dano, alcance, cadência, tripulação,
custo, receitas das fábricas...). Depois de editar, gere o mod de novo:

```bash
python3 tools/build_mod.py --vanilla <pasta Data do Cosmoteer>   # gera BulletStrike/ (regras + arte + textos)
python3 tools/make_docs.py                                        # atualiza docs/ARMAS.md
python3 tools/rules_lint.py --mod BulletStrike --vanilla <pasta Data do Cosmoteer>   # valida
```

- Precisa de Python 3 com **Pillow** e **numpy** (`pip install pillow numpy`).
- A pasta `Data` fica em `steamapps\common\Cosmoteer\Data`.
- Estilo de arte, efeitos e textos ficam em `tools/bs_data.py` e `tools/bs_strings.py`.

### Estrutura do repositório

| Caminho | O que é |
|---|---|
| `BulletStrike/` | **O mod pronto** (copie esta pasta para o jogo) |
| `tools/spec/bullet_strike_spec.json` | Números de balanceamento |
| `tools/spec/bullet_strike_missiles.json` | Projeto e números dos lança-mísseis (com as variantes de mecânica) |
| `tools/bsgen/launchers.py`, `tools/launcher_layout.py` | Gerador dos lança-mísseis e posição das células |
| `tools/build_mod.py` | Gera o mod inteiro |
| `tools/bsgen/` | Geradores de peças, projéteis, fábricas, recursos e arte procedural |
| `tools/rules_lint.py` | Validador de arquivos `.rules` (referências, caminhos, imagens, textos) |
| `tools/schema_check.py` | Compara os campos usados pelo mod com os do jogo base |
| `docs/ARMAS.md` | Tabela de armas, mísseis, munições e fábricas |
| `docs/MISSEIS_PROJETO.md` | Projeto completo dos lança-mísseis (números, testes, planos B) |

## Créditos

- Ideia e direção: **Rafael Tessaro**.
- Arte procedural, regras e ferramentas geradas com ajuda do Claude (Anthropic).
- Efeitos sonoros e partículas reaproveitam os do Cosmoteer por referência (nada do jogo é copiado para o mod).
