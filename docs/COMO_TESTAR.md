# Bullet Strike: instalação e roteiro de testes

Guia passo a passo para instalar o mod e conferir tudo dentro do jogo. Vá marcando os itens; quando algo falhar,
anote o número do item (por exemplo **H5**) e veja no fim [como me mandar o resultado](#5-como-me-mandar-o-resultado).

---

## 1. Instalar

1. **Baixe o mod.** No GitHub, abra o repositório **RafaelTessaro/Cosmoteer**, troque o branch para
   **`claude/laughing-babbage-0pswjv`** e clique em **Code → Download ZIP**.
2. **Extraia o ZIP.** Dentro dele há uma pasta **`BulletStrike`** (é ela que interessa; o resto é o gerador e a
   documentação).
3. **Abra a pasta de mods do Cosmoteer:**
   `C:\Users\<seu usuário>\Saved Games\Cosmoteer\<número do seu SteamID>\Mods\`
   (se a pasta `Mods` não existir, crie).
4. **Se já tinha uma versão antiga do Bullet Strike, apague a pasta antiga primeiro.** Arquivos que mudaram de nome
   ficariam sobrando e podem dar erro.
5. **Copie a pasta `BulletStrike` inteira** para dentro de `Mods`. O resultado tem que ficar assim:
   `...\Mods\BulletStrike\mod.rules` (e não `...\Mods\BulletStrike\BulletStrike\mod.rules`).
6. **Ative o modo desenvolvedor** (mostra os erros com detalhes): na Steam, botão direito no Cosmoteer →
   **Propriedades → Opções de inicialização** → escreva `--devmode`.
7. **Abra o jogo → Mods → ative o Bullet Strike** e reinicie o jogo quando ele pedir.
8. **Star Wars: A Cosmos Divided (opcional):** para testar junto, ative os dois mods. A ordem não importa.
   Faça primeiro os testes só com o Bullet Strike e depois repita a parte [K](#k-junto-com-o-star-wars-a-cosmos-divided).

**Se o jogo travar ao carregar:** a mensagem de erro mostra o motivo nas primeiras ~20 linhas, acima de
`--- End of inner exception stack trace ---`. Copie essas linhas (ou tire um print) e me mande. O arquivo de log
completo costuma ficar na mesma pasta `Saved Games\Cosmoteer`.

---

## 2. Preparar a nave de teste

- Use o **modo Criativo** (tudo liberado, sem custo). Monte uma nave com tripulação suficiente (alojamentos),
  corredores até as armas, depósitos e, para o overclock, **termodutos e radiadores** ligados às peças.
- Coloque os insumos: **munição** (da Fábrica de munição para canhão do jogo), **enxofre, bobina, triaço, cobre,
  urânio enriquecido** e **peças de míssil** (A.E., T., P.E.M. e nuclear).
- Monte também uma **nave inimiga** simples (com escudo e com blindagem) para servir de alvo, e uma que dispare
  mísseis, para testar as defesas.
- **Pinte uma nave-alvo de branco** e deixe outra cinza ou escura: vários efeitos novos precisam ser vistos sobre
  casco claro (B20, T-M5, T-CAL-3).
- Para o teste das defesas contra os raios do Star Wars (G1) você vai precisar do SW:ACD ativo junto.
- As peças do mod ficam na aba **Bullet Strike** do editor.

---

## 3. Roteiro de testes

**O que mais importa nesta versão:** [G1](#g1-teste-contra-os-raios-do-star-wars-precisa-dos-dois-mods) (defesas
contra os raios do SW), **B21** (setor de alcance ao atacar), a parte nova de **B20** (plasma sobre casco branco),
[M](#m-efeitos-dos-mísseis-t-m1-a-t-m8) (efeitos dos mísseis), [N](#n-efeitos-por-calibre-t-cal-1-a-t-cal-6)
(efeitos por calibre) e [O](#o-aprovar-o-visual-decisões-de-gosto) (aprovar o visual). Para comparar com o visual
antigo, veja [Comparar com o visual antigo (A/B)](#comparar-com-o-visual-antigo-ab).

### A. Carregamento e editor

- [ ] **A1** O jogo abre sem erro com o mod ativo.
- [ ] **A2** O Bullet Strike aparece no menu Mods com o logo novo (torre tripla disparando).
- [ ] **A3** A aba **Bullet Strike** aparece no editor com o ícone azul (projétil com rastros).
- [ ] **A4** Todas as peças aparecem com ícone 3D: 15 armas, 3 lança-mísseis e 5 fábricas.
- [ ] **A5** Nomes e descrições estão em português (com o jogo em pt-BR), sem texto faltando nem em inglês.
- [ ] **A6** As armas podem ser colocadas no convés e cercadas de blindagem.
- [ ] **A7** O tooltip de cada peça mostra os números (dano, alcance, consumo, tripulação).

### B. Cada arma (atirando num alvo)

Para cada arma confira: a tripulação chega no posto, a munição chega, a torre gira e mira, o cano recua (ou gira),
sai clarão e som, e o tiro chega no alvo dentro do alcance.

| Item | Arma | Fase | O que observar em especial |
|---|---|---|---|
| [ ] **B1** | Marimbondo (metralhadora leve, 1x1) | início | usa munição avulsa do jogo |
| [ ] **B2** | Mangangá (metralhadora pesada, 1x2) | início | fluxo constante de traçantes |
| [ ] **B3** | Carcará (autocanhão 20 mm, 2x2) | início | os dois canos alternando; o tiro tem pequena explosão |
| [ ] **B4** | Tatu (flak leve, 2x2) | início | veja a parte G |
| [ ] **B5** | Saci (metralhadora quádrupla, 2x2) | meio | ataca naves **e** derruba mísseis (híbrida) |
| [ ] **B6** | Cigarra (minigun, 2x3) | meio | **começa devagar e acelera** os canos girando |
| [ ] **B7** | Tambor (canhão naval 76 mm, 3x4) | meio | "tum, tum, tum"; tripulante perto da torre leva um tranco |
| [ ] **B8** | Boitatá (gatling de plasma, 2x3) | meio | acelera; disparos ciano; derruba escudo rápido |
| [ ] **B9** | Tamanduá (CIWS, 3x3) | meio | radar girando; veja a parte G |
| [ ] **B10** | Furacão (rotativo 30 mm, 4x4) | fim | demora ~6 s para acelerar |
| [ ] **B11** | Trovão (naval duplo 155 mm, 4x5) | fim | canos alternados, longo alcance (520 m) |
| [ ] **B12** | Curupira (plasma pesado, 4x5) | fim | 2 canos de plasma, quebra escudos de longe |
| [ ] **B13** | Pororoca (flak pesada, 4x4) | fim | veja a parte G |
| [ ] **B14** | Boiúna (obuseiro nuclear, 5x6) | fim | 1 projétil a cada 10 s; explosão nuclear **não** destrói a própria nave; o projétil pode ser abatido |
| [ ] **B15** | Mapinguari (torre tripla 406 mm, 6x7) | fim | salva de 3 granadas; tranco forte na tripulação |

- [ ] **B16** O tranco (Tambor, Trovão, Boiúna, Mapinguari) atordoa só por um instante quem está perto da torre.
- [ ] **B17** Sem tripulante no posto, a arma para de atirar.
- [ ] **B18** **Todo disparo aparece em voo**, de perto e de longe: metralhadoras, Carcará, Cigarra, Saci e Furacão
  soltam traçantes (risco brilhante com ponta branca) na cor da munição: âmbar no Padrão, vermelho-alaranjado na
  Perfurante-Explosiva, branco-azulado na Perfurante, azul no P.E.M.; o plasma é ciano. Tambor, Trovão, Mapinguari
  e Boiúna disparam granadas com rastro de fogo na cor da munição (verde na Boiúna). O jogo não fica lento com
  várias Cigarras atirando (as armas rápidas não têm rastro de partículas). O tamanho de cada tiro agora segue o
  calibre: confira na parte [N](#n-efeitos-por-calibre-t-cal-1-a-t-cal-6). O traçante do 7,62 mm (Marimbondo e
  Cigarra) é o mais fino de todos, mas ainda tem que dar para ver de longe; se sumir, anote: aí eu engrosso o
  risco.
- [ ] **B19** **Fogo amigo:** duas Marimbondo/Mangangá/Curupira e uma Tamanduá lado a lado, alvo ao longo da
  fileira: nenhum acerto nem clarão de flak nas torres vizinhas, e as torres atiram mesmo com outra torre nossa na
  frente. Se uma torre logo embaixo do cano de outra ainda levar dano, anote qual arma atirou. A Tamanduá só
  defende e não aceita alvo, então ela só atira aqui se vierem projéteis inimigos ao longo da fileira (ponha uma
  nave inimiga com lança-mísseis disparando nessa direção) ou se você passar ela para **Disparar
  automaticamente** ("disparar continuamente, mesmo se não houver nada em que disparar"), com o arco de tiro
  virado para o lado da fileira.

- [ ] **B20** **Efeitos de plasma (Boitatá e Curupira):** nenhum clarão laranja de pólvora na boca. A cada tiro sai
  uma descarga ciano com centro branco (ponta de lança para frente, faíscas curtas e um anel pequeno que pisca e
  some antes do tiro seguinte: com a Boitatá atirando sem parar, a ponta dos canos **não** pode ficar com um anel
  parado em volta). A luz no casco é fraca e fica mais à frente do cano, e a boca da Boitatá tem só um brilho fraco
  de cano quente: a arte da torre não pode sumir no clarão. No Curupira, logo depois de cada tiro, aparece um brilho
  entre as pontas dos canos (é um brilho que fica depois do disparo, não uma carga antes dele) e arcos elétricos. As
  duas armas atiram a mesma "lança" de plasma: ponta branca comprida, **sem cabeça redonda**, dentro de um corpo
  ciano que afina para trás; no instante do disparo a lança não pode aparecer deitada por cima dos canos ou da
  torre. Na Boitatá o raio é uma **serpente de fogo / lança de plasma** fina: o corpo sai reto da lança, num traço
  só, e afina devagar até a ponta, uns 4,5 tiles, com uma ondulação suave em S que **não** aumenta na ponta. No
  Curupira o raio é um **cometa / torpedo de plasma pesado**: a mesma lança, mais grossa, num corpo ciano largo que
  é mais largo cerca de 1 tile atrás da ponta e dali para trás só afina, sem "pescoço", seguido de uma esteira
  **reta** (anéis de pulso discretos só na metade de trás) e de um rastro curto que continua a esteira e some a uns
  10 tiles do raio. Na escala normal de batalha **nenhum** dos dois pode lembrar um girino/espermatozoide (cabeça
  oval clara + pescoço fino + fio atrás); se lembrar, anote a arma e o zoom. Sobre casco branco ou bem claro o raio
  tem que ler como uma lança: ponta branca, corpo ciano e um contorno azul-petróleo fino em volta (é a sombra por
  baixo do raio, um pouco mais larga que ele de propósito); **não** pode virar uma folha ou névoa clara em volta do
  raio, nem no overclock. A luz que o raio joga no casco é estreita e acompanha a lança; o halo ciano largo em volta
  do raio só aparece sobre o espaço. A cauda só aparece depois que o raio sai da boca (não pode ficar por cima da
  torre), e o rastro do Curupira também começa longe da torre. Confira também que o rastro do Curupira **fica parado
  no espaço** atrás do raio (não anda junto com ele; depois do impacto o que sobrou dele some ali mesmo em menos de
  0,06 s) e que as faíscas elétricas em volta do raio **acompanham** o raio, coladas nele. Depois de um impacto no
  casco as poucas faíscas que ainda estavam vivas seguem em linha reta por alguns tiles além do ponto de impacto (no
  pior caso uns 20) e somem em menos de 0,07 s; no escudo elas param na face dele. É normal. O raio do Curupira
  solta essas faíscas em voo no normal e no overclock; o da Boitatá, só no overclock. No casco: borrifo ciano,
  faíscas e uma brasa ciano que some. Em peça já destruída: um respingo menor, com som. No escudo: respingo achatado
  na face do escudo, sem brasa. Raio abatido no ar: estouro pequeno com um chiado baixo. Em overclock tudo fica
  maior e mais branco sobre o espaço (sobre casco branco continua a mesma lança, sem névoa branca), e o impacto do
  Curupira ganha um anel fino de pressão (Erupção Solar) que abre rápido e some sem cobrir o respingo. A luz da boca
  no overclock é ciano e não pode deixar uma mancha branca no casco claro a cada tiro. O som do tiro da Boitatá muda
  ao ligar o overclock (estalo leve no normal, mais forte no overclock). Com várias Boitatás atirando o jogo não pode
  ficar lento; se ficar, anote quantas. Faça esta parte sobre os três cascos (branco, cinza e escuro): se sobre casco
  cinza o raio parecer apagado demais (sem luz no casco) ou sobre casco branco aparecer névoa, anote; o ajuste é a
  força da luz estreita (um número só no gerador). Se o jogo acusar arquivo não encontrado ao carregar (sons
  `heavy_laser_*`, `laser_blaster_shot_*`, `laser_blaster_impact_*`, `laser_bolt_large_hit` ou a textura
  `railgun_shoot.png`), anote o nome do arquivo.
- [ ] **B21** **Setor de alcance ao atacar.** Selecione a nave, clique com o botão direito na nave inimiga e
  **segure** enquanto arrasta para longe dela (é o comando que escolhe a distância e a direção do ataque). Enquanto
  você arrasta, cada arma mostra o seu setor de alcance: uma fatia clara e transparente, em degradê, na direção em
  que a arma pode atirar e até onde ela alcança. Depois de dar o ataque, segure **Shift** (a tecla *Adicionar
  seleção*) e arraste uma das alças que aparecem: os setores aparecem de novo. **Todas** as armas do Bullet Strike
  têm que mostrar o setor: as 15 armas da tabela acima e os 3 lança-mísseis (Tocandira, Caipora e Mula-sem-Cabeça).
  As defesas (Tatu, Tamanduá, Pororoca) e o Saci mostram o setor mesmo sem atacar naves, como o ponto de defesa e a
  Matriz flak do jogo. Ponha uma arma do jogo na mesma nave para comparar: o setor das nossas tem que parecer igual
  ao dela. Se alguma não mostrar, anote qual.

### C. Munição e logística

- [ ] **C1** A **Prensa de Carregadores** transforma munição do jogo em **Carregadores Padrão** (5 → 1).
- [ ] **C2** A tripulação leva os carregadores até as armas de meio e fim de jogo (6 por viagem).
- [ ] **C3** O carregador na mão do tripulante tem o tamanho de um carregador da pilha (não aparece gigante).
- [ ] **C4** As pilhas aparecem certinhas nos depósitos: Carregador Padrão até 6, Perfurante 4, P.E.M. 4,
  Célula de Plasma 4, Projétil Nuclear 2.
- [ ] **C5** **Prensa de Carregadores Perfurantes:** 2 Carregadores Padrão + triaço → 2 Carregadores Perfurantes.
- [ ] **C6** **Energizador de Carregadores P.E.M.:** 2 Carregadores Padrão + cobre → 2 Carregadores P.E.M.
- [ ] **C7** **Fábrica de Células de Plasma:** enxofre + bobina → Célula de Plasma; Boitatá e Curupira usam.
- [ ] **C8** **Fundição de Projéteis Nucleares:** urânio enriquecido + 2 Carregadores Padrão → Projétil Nuclear; a Boiúna usa.
- [ ] **C9** A dica "2 Fábricas de munição para canhão alimentam 1 Prensa de Carregadores" aparece na descrição e
  bate na prática (a prensa não fica parada esperando munição).

### D. Seletor de munição (Cigarra, Tambor, Furacão, Trovão, Mapinguari)

- [ ] **D1** O botão de munição aparece e troca entre **Padrão / Perfurante / Perfurante-Explosiva / P.E.M.**
- [ ] **D2** Cada modo pede o carregador certo (Perfurante e Perfurante-Explosiva usam o mesmo Carregador
  Perfurante, mas cada modo tem o próprio quadrinho na arma: 4 quadrinhos nas armas com seletor).
- [ ] **D3** **Perfurante** atravessa blindagem e danifica as peças de trás.
- [ ] **D4** **Perfurante-Explosiva** atravessa uma ou duas placas e explode dentro do casco.
- [ ] **D5** **P.E.M.** drena escudos e bateria (as armas do Bullet Strike não são afetadas).
- [ ] **D6** Trocar de modo não gera tiros grátis nem trava a arma.
- [ ] **D7** **Estoque por tipo:** Cigarra em Padrão, com um depósito de Carregadores Padrão e um Energizador
  P.E.M. na nave. Monte a nave **sem** "Reabastecer todos os recursos" e sem recursos cheios, porque os dois
  enchem os depósitos de todos os tipos na arma. Assim, o quadrinho do P.E.M. na arma fica **vazio** enquanto o Padrão está
  escolhido. Gaste até sobrar 3 Carregadores Padrão, troque para P.E.M.: a arma espera a tripulação trazer
  Carregadores P.E.M. e os 3 Padrão continuam no quadrinho deles; volte para Padrão e ela atira com eles na hora.
  Se o depósito P.E.M. já estiver cheio (nave reabastecida), o certo é a arma atirar P.E.M. desse depósito e os
  3 Padrão continuarem no depósito deles.
- [ ] **D7b** Desligue a Cigarra (botão liga/desliga) com o depósito do tipo escolhido pela metade e espere um
  pouco (com tripulação sobrando): a tripulação continua completando o tipo escolhido, com a prioridade mínima,
  como nas armas do jogo, e o quadrinho dos outros tipos não recebe nada. Ligue de novo: ela atira na hora.
- [ ] **D7c** O mesmo entre os dois perfurantes: em Perfurante, gaste até sobrar 3 Carregadores Perfurantes e troque
  para Perfurante-Explosiva. A arma espera a tripulação trazer Carregadores Perfurantes para o quadrinho da
  Perfurante-Explosiva, e os 3 (e o carregador já aberto) continuam com a Perfurante para quando você voltar.
- [ ] **D8** Trovão e Mapinguari atiram normalmente (gastam 2 e 3 carregadores por disparo direto do depósito) e
  o aviso de "sem munição" aparece quando sobra menos que um disparo.

### E. Overclock das armas (meio e fim de jogo)

- [ ] **E1** O botão de overclock aparece nas armas de meio e fim (não aparece nas de início).
- [ ] **E2** Ligado, a arma atira mais rápido (veja a tabela de overclock no README) e **gera calor** nos termodutos.
- [ ] **E3** Sem radiador suficiente, a arma esquenta, pega fogo e pode explodir.
- [ ] **E4** Efeitos especiais: Trovão alcança 598 m; Curupira estoura no impacto; Boiúna "Fat Boy" com explosão
  maior; Pororoca deixa nuvem de estilhaços por 4 s.
- [ ] **E5** Desligar o overclock dá uma pausa de 3 s antes de voltar ao normal.

### F. Fábricas

- [ ] **F1** A máquina **só anima enquanto produz**: para quando falta insumo ou quando a saída enche.
- [ ] **F2** Fábricas vizinhas ganham +25% de velocidade e a animação fica mais rápida junto.
- [ ] **F3** **Overclock** das fábricas: produz 3 vezes mais rápido, gera calor (portas térmicas nas laterais e
  embaixo, não na fileira das máquinas) e, nas que usam energia, gasta 1,5 vez mais bateria.
- [ ] **F4** A **luz vermelha no teto** aparece num lugar que faz sentido em cima da arte.
- [ ] **F5** Ao levar dano, as **paredes rachadas** aparecem (dois níveis de dano).
- [ ] **F6** Som da fábrica parada não está alto demais.
- [ ] **F7** Destruída com produto guardado, a fábrica explode (mais forte quanto mais estoque).
- [ ] **F8** Com o teto ligado, o teto da fábrica fica com a cor da nave (o verde vira a pintura).

### G. Defesas (Tatu, Tamanduá, Pororoca e o Saci)

**O que mudou nesta versão:** as três defesas miram com tolerância de 4° (Tatu e Tamanduá) e 3° (Pororoca) em vez de
~1°, não voltam ao centro entre um alvo e outro, testam vários alvos possíveis a cada busca e dão prioridade a
mísseis e minas (um míssil novo tira a defesa de um raio). A explosão ganhou uma **segunda carga só contra raios
laser e iônicos**: Tatu 2.000 de dano em 4 m, Tamanduá 3.000 em 6 m, Pororoca 8.000 em 9 m. O dano contra mísseis
não mudou. A Pororoca gira mais rápido (120°/s em vez de 90°/s) e as rajadas de flak ficaram mais juntas.

#### G1. Teste contra os raios do Star Wars (precisa dos dois mods)

Modo Criativo, com o Star Wars: A Cosmos Divided e o Bullet Strike ativos e o jogo aberto com `--devmode` (passo 6
da instalação). Os nomes das armas do SW aparecem em inglês no editor.

**Montagem**

- 5 barcaças-alvo iguais (mesma placa de blindagem, reator, tripulação e munição cheia com **Reabastecer todos os
  recursos**), uma defesa em cada:
  - **Alvo 1:** 1 Tatu · **Alvo 2:** 1 Tamanduá · **Alvo 3:** 1 Pororoca
  - **Alvo 4:** 1 Matriz flak do jogo (controle: **tem** que atirar nos raios)
  - **Alvo 5:** 1 Sistema de ponto de defesa do jogo (controle: **não** pode atirar nos raios)
- **Naves salvas com a versão do primeiro teste (antes da 9874a40):** antes de começar, ponha o modo de tiro de cada
  Tatu, Tamanduá e Pororoca em **Disparar à vontade** (veja G3). Se ficou gravado "Disparar no alvo", a defesa nunca
  atira, e o teste não vale.
- Nave inimiga do SW a uns 300 m, **um tipo de arma por rodada**:
  - **Ataque 1:** 2× *Medium Turbolaser* (raio vermelho por padrão; a cor muda no botão da peça; 140 m/s, 2.000 de
    vida)
  - **Ataque 2:** 1× *Heavy Turbolaser* (80 m/s, 4.000 de vida)
  - **Ataque 3:** *Dual Laser Cannon* (repetidor, 350 m/s, 210 de vida)
  - **Ataque 4:** *Lançador de míssil e mina* do jogo com mísseis A.E. (para ver se nada piorou)
  - **Ataque 5** (só contra Tamanduá e Pororoca): *Dual 70TT Superheavy Turbolaser* (o Siege 12×12, que dispara
    raios de concussão pesados de 20.000 de vida)
- Use armas que disparam **raios** (tiros soltos). Os **feixes contínuos** do SW (Estrela da Morte, os "Super"
  lasers, os feixes *Siege*/*Artillery Turbolaser Beam*, SPHA-T) **nunca** podem ser abatidos, por nenhuma defesa: é
  limite do jogo, não é falha.
- Deixe só uma barcaça por vez na frente do atacante (as outras longe, fora do alcance), para os raios não serem
  divididos entre elas.

**Em cada rodada** (60 s por par defesa × atacante, em **Disparar à vontade**), anote:

- (a) A torre gira na direção dos raios?
- (b) Ela atira (explosões de flak no caminho do raio)?
- (c) Quantos raios foram destruídos e quantos acertaram o casco (pode ser por alto: "quase todos", "metade",
  "quase nenhum"; um vídeo curto ajuda).
- Com raios chegando, abra o **Part Debugger** do modo desenvolvedor e clique na torre: anote o que ele mostra no
  componente da torre (se ela tem alvo e se quer atirar). Um print basta.
- Anote também se aparecem explosões de flak encostadas no casco inimigo (a torre mirando um raio atrás do casco:
  gasta munição à toa).
- Depois, 10 s em **Disparar automaticamente**: prova que munição, tripulação e canhão funcionam.
- No fim: uma salva dos **nossos** mísseis passando pela nossa flak **não** pode ser destruída (é o H8).
- Se não achar o Part Debugger, use a [versão de diagnóstico](#4-dicas) no lugar da normal: a luz do teto da defesa
  fica mais forte enquanto ela tem um alvo.

**Passa se**

- Começa a atirar até ~1 s depois que o primeiro raio entra no alcance.
- Raios destruídos:

  | Defesa | Ataque 1 (médio) | Ataque 2 (pesado) | Ataque 3 (repetidor) | Ataque 5 (concussão) | Ataque 4 (mísseis A.E.) |
  |---|---|---|---|---|---|
  | Tatu | ≥ 80 % | ≥ 80 % (2 rajadas por raio) | derruba alguns | não testa | ≥ 95 % |
  | Tamanduá | ≥ 95 % | ≥ 95 % | anote | ≥ 80 % | ≥ 95 % |
  | Pororoca | ≥ 70 % | ≥ 95 % | anote | ≥ 90 % | ≥ 95 % |

- Alvo 4 (Matriz flak) atira no Ataque 1; Alvo 5 (ponto de defesa) ignora o Ataque 1.
- O Tatu gasta no máximo 1 unidade de munição do jogo por raio médio destruído.

**Se ainda falhar**

| O que você vê | Causa provável | O que eu faço |
|---|---|---|
| Gira para os raios e o Part Debugger mostra alvo, mas não atira | condição de disparo (ângulo) | te mando uma versão de teste com tolerância de 10°, depois de 30° (o valor da Matriz flak), sem mudar mais nada |
| Não gira para os raios, mas gira para os mísseis do Ataque 4, e a Matriz flak (Alvo 4) atira nos raios | escolha de alvo da nossa torre | aproximo a torre da Matriz flak, um passo por vez: (1) volta a nota de poder de fogo; (2) uma lista de alvos só; (3) aceita alvo do jogador; (4) tira "atirar com a visada bloqueada" |
| Nem a Matriz flak (Alvo 4) atira nos raios do SW | limite do jogo ou do SW | troco por um projeto que não depende de alvo: granada com espoleta de proximidade contra laser/íon, ou um campo de estilhaços como a nuvem do overclock da Pororoca |
| Não atira nem em Disparar automaticamente | montagem | confira munição, tripulação e se a peça está danificada ou queimada |
| Não dá para saber se a torre tem alvo (sem Part Debugger) | falta informação | rode a rodada de novo com a [versão de diagnóstico](#4-dicas); se a luz acende e ela não atira, é a 1ª linha; se não acende, é a 2ª |

- [ ] **G1** O teste acima passou (anote os resultados de cada rodada mesmo se passou).

#### Outros itens das defesas

- [ ] **G2** **Só defendem:** não aparece o botão Atacar/Defender, não dá para dar alvo nem controle direto, e a
  explosão nunca causa dano em naves ou escudos.
- [ ] **G3** O modo de tiro só tem Suspender fogo / Disparar à vontade / Disparar automaticamente (como o ponto de
  defesa do jogo) e já vem em Disparar à vontade; o Saci continua com Atacar / Defender / Atacar + Defender.
  **Naves salvas com a versão do primeiro teste (antes da 9874a40):** confira o botão de modo de tiro de cada Tatu,
  Tamanduá e Pororoca. Se aparecer "Disparar no alvo" ou nenhum modo marcado, escolha **Disparar à vontade**:
  "Disparar no alvo" não existe mais nelas e, se tiver ficado gravado assim, a defesa nunca atira.
- [ ] **G4** Feixes contínuos (como o prisma iônico) **não** são abatidos (igual ao jogo); os feixes contínuos do
  SW:ACD também não.
- [ ] **G5** O consumo de munição das defesas é alto, mas a tripulação consegue manter o abastecimento.
- [ ] **G6** O tooltip das três defesas mostra a linha nova **Dano x lasers** (por disparo e por segundo), depois
  das linhas do jogo: Tatu 2.000, Tamanduá 3.000 e Pororoca 8.000 por disparo.
- [ ] **G7** Tatu, Tamanduá e Pororoca continuam derrubando mísseis, minas e granadas inimigos (vários de uma vez
  na mesma explosão), mesmo com outra torre nossa na frente, e a explosão sai no ar, perto do projétil, não em cima
  das nossas torres.

### H. Lança-mísseis (Tocandira, Caipora, Mula-sem-Cabeça)

Estes são os testes mais importantes: são mecânicas que só dá para confirmar no jogo.

- [ ] **H1** A tripulação leva **peças de míssil** do jogo (A.E., T., P.E.M., nuclear) até o paiol do lançador.
- [ ] **H2** As ogivas aparecem carregadas no casulo, uma a uma, enquanto ele recarrega.
- [ ] **H3** **Trava das células:** só dispara com todas as células cheias, sai a **salva inteira em sequência**,
  e só então volta a recarregar.
- [ ] **H4** **Recarga só com tripulação:** sem tripulante no posto, as células param de encher (o paiol continua
  recebendo peças).
- [ ] **H5** **Troca de míssil:** trocar o tipo nunca dispara uma salva logo depois da outra, nem com overclock.
- [ ] **H6** **Salva parcial:** com o paiol vazio, as células já carregadas disparam depois de uma recarga inteira;
  com abastecimento só lento, continua saindo a salva cheia.
- [ ] **H7** Os mísseis passam **por cima do próprio convés**: não explodem nas nossas torres nem freiam ou desviam
  logo depois de sair.
- [ ] **H8** A nossa CIWS e flak **não** devem derrubar os nossos próprios mísseis: dispare salvas nossas através
  das explosões do Tamanduá e da nuvem de estilhaços da Pororoca em overclock (a nuvem é igual à do jogo e é a que
  mais pode pegar algum). Anote qualquer míssil nosso perdido e onde (é o teste T09).
- [ ] **H9** **Piranha (submunições):** abre perto do inimigo, os minimísseis seguem o alvo, se espalham por várias
  peças e não estouram em cima do nosso casco; o jogo aguenta muitas submunições ao mesmo tempo sem travar.
- [ ] **H10** **Carrapato (grudento):** gruda numa nave que está girando e acelerando e explode 2,5 s depois;
  abatido no voo, se perde.
- [ ] **H11** **Taturana (napalm):** acende fogo na peça atingida e em volta.
- [ ] **H12** **Poraquê (P.E.M.):** drena bateria e escudo na área.
- [ ] **H13** **Boto (torpedo com iscas):** a ogiva se separa junto com as iscas 1,5 s depois do lançamento.
- [ ] **H14** **Iara (torpedo nuclear, só na Mula):** só os 2 casulos de dentro disparam (os de fora ficam com
  persianas fechadas) e o overclock **não** acelera o Iara.
- [ ] **H15** **Overclock (Caipora e Mula):** recarga 1,5 vez mais rápida, calor chega aos termodutos, cerca de 1 em
  16 mísseis é descartado por salva; sem refrigeração o lançador pega fogo e explode.
- [ ] **H16** Lançador destruído **cheio** explode proporcional ao estoque; consertar um lançador queimado não o faz
  explodir de novo.
- [ ] **H17** Na Mula, o colar sem cabeça mostra a brasa fraca, que acende forte no overclock.

### I. Limites por nave

- [ ] **I1** **Limite nuclear (2):** aceita 2 Boiúnas, 2 Mulas ou 1 de cada; recusa a 3ª.
- [ ] **I2** **Torres de Encouraçado (2):** recusa o 3º Mapinguari.
- [ ] **I3** O editor mostra o limite na peça.

### J. Carreira e Construir e Batalhar

- [ ] **J1** Na **Carreira**, as techs do Bullet Strike aparecem na árvore e liberam as peças, os tipos de munição,
  os tipos de míssil e o overclock de cada arma e fábrica.
- [ ] **J2** Nenhuma arma é liberada sem dar para fazer a munição dela.
- [ ] **J3** No **Construir e Batalhar**, as peças aparecem e dá para montar e lutar.

### K. Junto com o Star Wars: A Cosmos Divided

- [ ] **K1** Os dois mods carregam juntos sem erro.
- [ ] **K2** A flak e a CIWS derrubam mísseis e disparos do SW:ACD (o teste completo é o
  [G1](#g1-teste-contra-os-raios-do-star-wars-precisa-dos-dois-mods)).
- [ ] **K3** As fábricas de mísseis do SW:ACD abastecem os nossos lançadores (usam as mesmas peças de míssil).
- [ ] **K4** As abas do editor e os textos dos dois mods não se misturam nem somem.

### L. Visual geral

- [ ] **L1** As torres ficam por cima do casco, com sombra, e giram suaves.
- [ ] **L2** Os canos ficam alinhados com a torre durante o giro e o recuo.
- [ ] **L3** Com o teto ligado, a parte de baixo das armas pega a cor da nave.
- [ ] **L4** Luzes âmbar/ciano/verde acendem quando a arma está funcionando e apagam quando está desligada ou
  destruída.
- [ ] **L5** Nada aparece cortado, deslocado ou com quadrado preto.

### M. Efeitos dos mísseis (T-M1 a T-M8)

Cada tipo de míssil agora tem arte própria, maior a cada fase (Muriçoca ~1 tile, Jararaca 1,75 tile na Caipora e
2,5 na Mula, Boto 2,75 / 3,25, Iara 3,75), jato do propulsor na cor do tipo, explosão do tamanho da fase e um
clarão de lançamento na cor do tipo. Se os mísseis aparecerem todos com o corpo do míssil A.E. do jogo, a arte não
carregou (o resto dos efeitos continua): anote.

| Tipo | Jato e fumaça em voo | Impacto (tamanho da explosão do jogo) |
|---|---|---|
| Jararaca e Muriçoca (A.E.) | jato âmbar, fumaça cinza (a Muriçoca não solta fumaça) | Muriçoca 0,45×; Jararaca 0,85× na Caipora e 1× na Mula |
| Taturana (napalm) | jato laranja, fogo e fumaça escura e oleosa | 0,5× (Taturana-mirim) / 0,8× / 1,1×, com estilhaços térmicos e gotas de napalm |
| Piranha (submunições) | jato amarelo, fumaça cinza; os minimísseis só têm um jato pequeno | ao abrir: clarão amarelo e estilhaços |
| Carrapato (grudento) | jato vermelho, fumaça cinza | clarão vermelho ao grudar; carga com contagem de LEDs; clarão vermelho ao explodir |
| Poraquê (P.E.M.) | jato azul, fumaça fraca e faíscas elétricas azuis | 0,8× / 1× |
| Boto (torpedo) | jato branco-azulado e esteira de fumaça branca | 1,3× / 1,6×, com anel branco e clarão branco |
| Iara (nuclear) | jato verde, fogo verde, fumaça nuclear | explosão nuclear do jogo 1,3× (maior que a da Boiúna), anel verde até ~10 tiles, tremor forte como o da Boiúna e brilho verde que fica uns 3 s |

- [ ] **T-M1** **Jato por cima do convés e por baixo do corpo.** Dispare salvas de cada lançador por cima do nosso
  convés (com o teto ligado) e olhe o míssil saindo.
  - **Passa se:** o jato colorido aparece por cima dos nossos tetos e torres logo na saída da célula, por baixo do
    corpo do míssil (não cobre o míssil), e a fumaça fica por baixo do jato.
  - **Se falhar:** jato escondido embaixo do teto ou desenhado por cima do corpo: anote; eu troco a camada de
    desenho do jato e da fumaça.
- [ ] **T-M2** **Explosão do tamanho da fase.** Veja o impacto de cada míssil num casco sem escudo e num escudo, e
  um míssil nosso abatido.
  - **Passa se:** a explosão da Muriçoca é bem menor que a da Jararaca da Caipora, e esta menor que a da Mula
    (tabela acima); o mesmo na Taturana; o Boto bem maior, com anel e clarão brancos. Um micromíssil nosso abatido
    mostra uma bola de fogo pequena, não a de um míssil grande. Anote também se o som do impacto dos micromísseis
    fica mais baixo.
  - **Se falhar:** tudo do mesmo tamanho de antes quer dizer que o jogo ignorou a escala (MediaEffectsScale); o
    plano B é escrever cópias da explosão já no tamanho de cada fase.
- [ ] **T-M3** **Fumaça e fogo de cada tipo.** Olhe cada tipo em voo, de perto e de longe.
  - **Passa se:** cores e quantidade leem bem (tabela acima) e a fumaça fica parada no espaço, atrás e por baixo do
    míssil.
  - **Se falhar:** o plano B (cópias completas dos arquivos de fumaça e fogo do jogo, em vez de herança parcial, que
    pode travar o jogo) já está aplicado. Se faltar fumaça, ela sair no lugar errado ou o jogo travar ao disparar um
    tipo, anote o tipo; se a fumaça estiver demais ou de menos, diga qual, eu ajusto a quantidade.
- [ ] **T-M4** **Contagem do Carrapato.** Dispare Carrapatos numa nave parada e olhe a carga grudada no casco.
  - **Passa se:** a carga tem corpo próprio com um anel de 8 LEDs que acendem um a um em 2,5 s, começando do zero
    quando ela gruda e parando no último quadro quando explode (a explosão bate com o fim da contagem).
  - **Se falhar:** contagem começando no meio, repetindo ou fora de sincronia com a explosão: o plano B é voltar ao
    pisca rápido em loop de hoje.
- [ ] **T-M5** **Luzes dos mísseis e o trevo verde do Iara.** Olhe os mísseis em voo sobre casco branco, cinza e
  escuro.
  - **Passa se:** os LEDs e as faixas acesas brilham por cima do corpo iluminado (sem quadrados escuros). No Iara, o
    trevo pequeno gira por cima da ogiva e a luz grande em forma de trevo gira no casco por baixo dele, **verde**
    (não branca) inclusive sobre casco branco. A luz do bocal do Iara (e das iscas dele) também é verde, e a do
    Poraquê é azul: nenhuma pode virar uma mancha branca no casco. As iscas do Iara não têm trevo (de propósito,
    veja O8).
  - **Se falhar:** luzes sumindo ou quadrados escuros: anote o tipo. Trevo branco sobre casco branco: eu baixo a
    força da luz.
- [ ] **T-M6** **Desempenho com salva grande.** Uma Mula com 48 Jararacas e uma Caipora com 16 Taturanas disparando
  ao mesmo tempo; depois uma salva de Piranhas (até 96 minimísseis). Veja o FPS (por exemplo, com o contador de FPS
  da Steam) e compare com a [versão A/B](#comparar-com-o-visual-antigo-ab).
  - **Passa se:** o jogo não fica bem mais lento que na versão antiga (a conta dá ~800 partículas para a salva de
    Jararacas e ~1.000 para a de Taturanas; os minimísseis da Piranha não têm partículas).
  - **Se falhar:** o plano B é a fumaça pela metade. Teste também com **Partículas abstratas e efeitos especiais**
    desligado nas opções de vídeo (a fumaça e as gotas de napalm são dessa parte "extra") e me diga a diferença.
- [ ] **T-M7** **Tamanho ao lado dos mísseis do SW.** Nossos mísseis e torpedos voando junto com mísseis e torpedos
  do SW:ACD.
  - **Passa se:** o tamanho parece coerente: nenhum dos nossos parece de brinquedo ou gigante ao lado dos do SW, e
    os grandes não ficam feios passando por cima das nossas torres na saída.
  - **Se falhar:** diga qual parece grande ou pequeno demais; eu mudo o tamanho daquela fase (só visual).
- [ ] **T-M8** **Detalhes de cada tipo.**
  - Lançamento: além do clarão do jogo, um clarão na cor do tipo; o Iara treme a tela de leve; Boto e Iara soltam
    uma nuvem de fumaça maior no lançamento.
  - Boto e Iara: aos 1,5 s, a separação mostra uma baforada (branca no Boto, verde no Iara) e 1 a 3 pedaços
    girando.
  - Taturana: 8 a 14 gotas laranja voando para dentro do alvo no impacto.
  - Carrapato: clarão vermelho quando gruda e quando a carga explode.
  - Piranha: os minimísseis são uma figura parada com um jato pequeno, sem fumaça.
  - Iara abatido: vazamento verde e um anel verde pequeno. Iara no alvo: o brilho que fica depois é, no máximo, um
    verde-menta fraco sobre casco branco (nunca branco); o anel fica quase branco sobre casco branco, isso é normal.
  - Iscas (Boto e Iara): estouro pequeno e fumaça fraca.

### N. Efeitos por calibre (T-CAL-1 a T-CAL-6)

Arma maior, tiro maior: o clarão da boca, o tiro em voo, o impacto e o tremor de tela agora seguem o calibre. As
granadas (Tambor, Trovão, Mapinguari e Boiúna) têm arte própria: corpo de metal iluminado, uma faixa perto do nariz
na cor da munição e o traçante na base. O plasma (Boitatá e Curupira) fica de fora: é o B20.

| Arma | Calibre | Em voo |
|---|---|---|
| Marimbondo / Cigarra | 7,62 mm | traçante fino (2,2 / 2,6 tiles) |
| Mangangá / Saci | 12,7 mm | traçante 3,0 / 3,4 tiles |
| Carcará | 20 mm | traçante 3,6 tiles com cabeça branca e rastro âmbar |
| Furacão | 30 mm | traçante 4,0 tiles com cabeça branca e um borrão de calor |
| Tambor | 76 mm | granada de 0,72 tile, traçante 5,5 tiles e clarão na base |
| Trovão | 155 mm | granada de 1,15 tile, traçante 6,0 tiles e rastro de fogo |
| Mapinguari | 406 mm | granada de 2,05 tiles, traçante 6,5 tiles, rastro de fogo grande e esteira de fumaça |
| Boiúna | nuclear (420 mm visual) | granada nuclear de 2,2 tiles, faixas verdes piscando, trevo girando e esteira de fumaça cinza-esverdeada |

As defesas também: clarão da boca e rajada pequenos no Tatu, médios no Tamanduá e grandes na Pororoca (que treme
a tela de leve).

- [ ] **T-CAL-1** **Impacto do tamanho do calibre.** Atire cada arma no casco, no escudo e, com Perfurante, através
  da blindagem; com Padrão e Perfurante-Explosiva, veja também a explosão onde a granada para.
  - **Passa se:** o impacto cresce com o calibre (Marimbondo só faíscas pequenas; Mapinguari 1,5× o impacto do
    canhão de convés do jogo). A explosão do Carcará é um estouro pequeno, não a de um míssil; a do Tambor é bem
    menor que a de uma Jararaca, e a do Mapinguari maior que a do Trovão. Cada peça atravessada solta faíscas
    menores, sem tremer a tela de novo. Rajadas da flak: Tatu < Tamanduá < Pororoca. Anote também se o som do
    impacto fica mais baixo nas armas pequenas.
  - **Se falhar:** se algum impacto sai do tamanho de antes, o jogo ignorou a escala (MediaEffectsScale) naquele
    lugar. Se for só na explosão onde a granada para ou na rajada da flak (os dois lugares onde o jogo base não usa
    esse campo), eu desligo o campo ali (voltam ao tamanho do jogo) ou faço cópias já no tamanho certo; se for em
    todos os impactos, faço cópias escaladas para todos, como já faço com o clarão da boca.
- [ ] **T-CAL-2** **Escada de tamanhos.** Ao carregar, nenhum erro de arquivo não encontrado (`shots/bs_cal_fx/...`).
  Ponha as armas lado a lado atirando no mesmo alvo.
  - **Passa se:** o clarão da boca e o tiro em voo crescem na ordem 7,62 < 12,7 < 20 < 30 < 76 < 155 < 406 <
    Boiúna. O tiro do Tambor (76 mm) parece mais forte que os traçantes do Carcará (20 mm) e do Furacão (30 mm), e o
    Trovão (155 mm) fica claramente acima do Furacão. O Mapinguari mostra 3 chamas (uma por cano) e, logo depois, 3
    baforadas de fumaça atrás da torre (na culatra); Tambor, Trovão e Boiúna também soltam essa fumaça. Trovão,
    Mapinguari e Boiúna soltam uma onda de pressão (distorção) na boca. Tamanduá e Pororoca em overclock: clarão de
    boca maior.
  - **Se falhar:** erro de arquivo: mande o nome. Dois calibres parecendo iguais: diga quais; eu ajusto os tamanhos.
- [ ] **T-CAL-3** **Granada iluminada, faixa colorida, trevo girando e esteira de fumaça.** Aproxime o zoom nos
  tiros do Tambor, Trovão, Mapinguari e Boiúna passando sobre casco branco e escuro.
  - **Passa se:** a granada tem corpo de metal com sombra (iluminado pelas luzes da nave) e a faixa perto do nariz
    tem a cor da munição (âmbar no Padrão, branco-azulado na Perfurante, vermelho-alaranjado na
    Perfurante-Explosiva, azul no P.E.M.). Padrão e P.E.M. usam a granada explosiva (nariz com espoleta, cinta de
    cobre); Perfurante e Perfurante-Explosiva, a perfurante (ogiva longa com capuz escuro). Na Boiúna: granada cinza
    com 2 faixas verdes piscando, um trevo pequeno girando por cima e, no casco, uma luz verde grande em forma de
    trevo girando por baixo (verde, não branca, inclusive sobre casco branco). O brilho em volta da granada também
    é verde: o trevo não pode sumir dentro de uma mancha branca no casco. No impacto: o cogumelo nuclear do
    jogo, um anel verde que abre até ~9 tiles e um brilho verde fraco que fica uns 3 s (sobre casco branco, no
    máximo um verde-menta fraco; o anel fica quase branco sobre casco branco, isso é normal). Abatida no ar: clarão
    nuclear e um anel verde pequeno. Mapinguari e Boiúna deixam uma esteira de fumaça que **fica parada no espaço**
    (não anda junto com a granada).
  - **Se falhar:** faixa branca em vez de colorida: troco a faixa por uma versão aditiva (sempre colorida).
    Granada preta, quadrada ou invisível: anote a arma. Se aparecer o dardo com sabot do jogo no lugar da granada,
    a arte das granadas não carregou: anote. Trevo parado ou esteira andando junto: anote a arma.
- [ ] **T-CAL-4** **Desempenho (FPS).** 4 Cigarras, 2 Furacões e 2 Tamanduás, todos em overclock, atirando por 60 s.
  Veja o FPS (por exemplo, com o contador de FPS da Steam) e repita com a
  [versão A/B](#comparar-com-o-visual-antigo-ab).
  - **Passa se:** o FPS não cai mais que na versão antiga (a conta indica que melhora: o Tamanduá em overclock caiu
    de ~2.700 para ~800 partículas vivas).
  - **Se falhar:** mande o FPS das duas versões e qual arma pesa; o plano B é cortar partículas daquela arma (menos
    estilhaços, fumaça pela metade). Teste também com **Partículas abstratas e efeitos especiais** desligado.
- [ ] **T-CAL-5** *(opcional)* **Escala nos efeitos de disparo.** Nada a testar nesta versão: o clarão da boca usa
  cópias já no tamanho certo. Só vale se eu te mandar uma versão de teste para isso.
- [ ] **T-CAL-6** **Conforto do tremor de tela.** 2 Mapinguaris e 2 Trovões atirando juntos; depois uma Boiúna
  acertando perto da câmera.
  - Os números: Mapinguari 0,12 por cano, com os 3 canos no mesmo instante (0,16 no overclock), e 0,25 por 1 s no
    impacto; Trovão 0,12 por tiro (0,18 no overclock) e 0,15 no impacto; Boiúna 0,3 no disparo e 0,5 por 1,5 s no
    impacto; Pororoca 0,03 por rajada.
  - **Passa se:** dá para sentir o peso, mas a tela continua legível e não incomoda.
  - **Se falhar:** diga qual arma e em que momento (disparo ou impacto); eu baixo o tremor dela. No Mapinguari,
    outra saída é disparar os 3 canos um depois do outro (veja O5).

### O. Aprovar o visual (decisões de gosto)

Aqui não tem certo ou errado: para cada item, diga **aprovo** ou o que prefere. Tudo isso é só visual (não muda
dano nem nada do jogo), exceto a opção dos canos em sequência do O5.

- [ ] **O1** **Acerto no escudo sem fumaça.** O tiro que bate no escudo agora mostra só clarão e faíscas, sem
  fumaça nem destroços, que só fazem sentido no casco. Antes era igual ao acerto no casco.
- [ ] **O2** **Menos estilhaços na flak.** Tatu e Tamanduá soltam 30 a 40 estilhaços por rajada (antes 150 a 200) e
  a Pororoca 100 a 120; as rajadas também ficaram mais juntas. Pesa muito menos no jogo, mas fica mais "leve".
  Aprova ou quer mais?
- [ ] **O3** **Formato da granada perfurante.** Perfurante e Perfurante-Explosiva agora são uma granada de ogiva
  longa com capuz escuro, no lugar do dardo com sabot do jogo. Aprova ou prefere o dardo?
- [ ] **O4** **Calibre visual da Boiúna: 420 mm.** A granada nuclear tem 2,2 tiles, um pouco maior que a do
  Mapinguari (2,05). Outras opções: 280 mm (como o canhão atômico "Atomic Annie", menor que o 406) ou 406 mm (igual
  ao Mapinguari). Só os tamanhos mudam.
- [ ] **O5** **Chama e tremor do Mapinguari (406 mm).** A chama da boca é 1,6× a do canhão de convés do jogo (2× no
  overclock): chamas longas, de ~14 a 18 tiles, que podem esconder a própria nave ou o alvo. Os 3 canos atiram e
  tremem juntos. Aprova, quer a chama mais curta, menos tremor, ou os canos um depois do outro (0 / 0,12 / 0,24 s;
  isso muda o tempo de disparo, então só com o seu ok)?
- [ ] **O6** **Iara com blindagem escura e chevrons verdes.** O Iara é o único míssil de blindagem escura, com
  chevrons verde e preto, trevo, faixas verdes pulsando, bocal triplo e fogo verde (no jogo o fogo é laranja). Os
  chevrons quebram de propósito a regra "sem faixas de alerta" das torres, só nos mísseis. Aprova?
- [ ] **O7** **Esteira de fumaça longa do 406 e da Boiúna.** A esteira atrás da granada do Mapinguari chega a uns
  80 tiles. Aprova ou quer mais curta? (O Trovão não tem esteira de propósito, para as fases ficarem diferentes.)
- [ ] **O8** **Iscas do Iara sem trevo.** Dá para distinguir a ogiva das iscas de longe (de propósito; a mira das
  defesas não usa o visual, então a isca continua enganando as defesas). Aprova ou prefere iscas iguais à ogiva?

---

## 4. Dicas

- Teste uma parte por vez (por exemplo, só a logística com a Prensa e a Cigarra) para achar o problema mais rápido.
- Para os testes de míssil, deixe uma nave inimiga **parada** primeiro e depois uma **girando e acelerando**.
- Para o overclock, coloque radiadores **de sobra** primeiro (para ver o efeito) e depois **de menos** (para ver o
  aquecimento e o fogo).

### Comparar com o visual antigo (A/B)

Para saber se algo mudou por causa dos efeitos novos (visual, FPS ou erro ao carregar), compare com uma versão
gerada com **`BS_FX_EXT=0`**. Nela continuam as mudanças das defesas (parte G), o setor de alcance (B21) e o plasma
atual (B20); os efeitos por calibre (N), a arte e os efeitos dos mísseis (M) e o anel e o brilho nucleares voltam a
ser os de antes.

- **Jeito fácil:** me peça a versão A/B e eu te mando o ZIP.
- **Gerando você mesmo** (precisa de Python 3 e de `pip install pillow numpy`): no PowerShell, dentro da pasta
  extraída do ZIP (a que tem `tools` e `BulletStrike`):

  ```
  $env:BS_FX_EXT = "0"
  python tools\build_mod.py --out comparar\BulletStrike
  ```

  A pasta nova `comparar\BulletStrike` é a versão A/B. Feche o PowerShell depois (a variável some junto). Use
  sempre uma pasta nova ou vazia em `--out`: o gerador se recusa a apagar uma pasta que não seja de um build do mod.
  O logo do menu Mods pode sair com outra fonte; não importa.
- **Trocar de versão:** com o jogo fechado, deixe só **uma** das duas pastas dentro de `Mods` (as duas são o mesmo
  mod) e abra o jogo de novo.
- Se o jogo travar ao carregar só na versão nova e não na A/B, o problema está nos efeitos novos: mande as linhas do
  erro.

### Versão de diagnóstico das defesas

Para o G1, se o Part Debugger não ajudar: nesta versão a luz do teto de cada defesa fica mais forte enquanto ela
**tem um alvo** (ou, numa segunda versão, enquanto ela **quer atirar**). Ela usa a mesma pasta `BulletStrike` e
substitui a normal; é só para o teste.

- **Jeito fácil:** me peça (versão "tem alvo" e/ou "quer atirar").
- **Gerando você mesmo:** como na A/B, mas com `$env:BS_PD_DEBUG = "1"` (luz = tem alvo) ou
  `$env:BS_PD_DEBUG = "WantsToFire"` (luz = quer atirar), e `--out diagnostico\BulletStrike`.

## 5. Como me mandar o resultado

Para cada item que falhou, me mande:

1. O **número do item** (por exemplo **H5**).
2. **O que aconteceu** e o que você esperava.
3. Um **print** ou vídeo curto, se der.
4. Se o jogo travou: as primeiras linhas do erro (acima de `--- End of inner exception stack trace ---`).

Para o **G1**, mande as anotações de cada rodada (a, b, c), o que o Part Debugger mostrou e o resultado das
barcaças de controle (Alvo 4 e Alvo 5). Para a parte **O**, basta dizer "aprovo" ou o que prefere em cada item.

Vários itens dos mísseis têm um **plano B** pronto no gerador, que muda o mecanismo sem mudar os números; então,
se algo de H falhar, eu já tenho por onde corrigir rápido. O mesmo vale para as partes M e N: cada teste já diz
qual é o plano B.
