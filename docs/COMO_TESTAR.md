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
- As peças do mod ficam na aba **Bullet Strike** do editor.

---

## 3. Roteiro de testes

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
  várias Cigarras atirando (as armas rápidas não têm rastro de partículas).
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
  oval clara + pescoço fino + fio atrás); se lembrar, anote a arma e o zoom. Sobre casco branco o raio tem que
  continuar visível (há uma sombra azul-petróleo por baixo dele, mais estreita que o raio; ela não pode aparecer
  como mancha escura fora do raio). A cauda só aparece depois que o raio sai da boca (não pode ficar por cima da
  torre), e o rastro do Curupira também começa longe da torre. Confira também que o rastro do Curupira **fica parado
  no espaço** atrás do raio (não anda junto com ele; depois do impacto o que sobrou dele some ali mesmo em menos de
  0,06 s) e que as faíscas elétricas em volta do raio **acompanham** o raio, coladas nele. Depois de um impacto no
  casco as poucas faíscas que ainda estavam vivas seguem em linha reta por alguns tiles além do ponto de impacto (no
  pior caso uns 20) e somem em menos de 0,07 s; no escudo elas param na face dele. É normal. O raio do Curupira
  solta essas faíscas em voo no normal e no overclock; o da Boitatá, só no overclock. No casco: borrifo ciano,
  faíscas e uma brasa ciano que some. Em peça já destruída: um respingo menor, com som. No escudo: respingo achatado
  na face do escudo, sem brasa. Raio abatido no ar: estouro pequeno com um chiado baixo. Em overclock tudo fica
  maior e mais branco, e o impacto do Curupira ganha um anel fino de pressão (Erupção Solar) que abre rápido e some
  sem cobrir o respingo. O som do tiro da Boitatá muda ao ligar o overclock (estalo leve no normal, mais forte no
  overclock). Com várias Boitatás atirando o jogo não pode ficar lento; se ficar, anote quantas. Se o jogo acusar
  arquivo não encontrado ao carregar (sons `heavy_laser_*`, `laser_blaster_shot_*`, `laser_blaster_impact_*`,
  `laser_bolt_large_hit` ou a textura `railgun_shoot.png`), anote o nome do arquivo.

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

- [ ] **G1** Tatu, Tamanduá e Pororoca derrubam mísseis, minas, granadas e disparos laser inimigos (vários de uma
  vez na mesma explosão), mesmo com outra torre nossa na frente, e a explosão sai no ar, perto do projétil, não em
  cima das nossas torres.
- [ ] **G2** **Só defendem:** não aparece o botão Atacar/Defender, não dá para dar alvo nem controle direto, e a
  explosão nunca causa dano em naves ou escudos.
- [ ] **G3** O modo de tiro só tem Suspender fogo / Disparar à vontade / Disparar automaticamente (como o ponto de
  defesa do jogo) e já vem em Disparar à vontade; o Saci continua com Atacar / Defender / Atacar + Defender.
  **Naves salvas antes desta versão:** confira o botão de modo de tiro de cada Tatu, Tamanduá e Pororoca. Se
  aparecer "Disparar no alvo" ou nenhum modo marcado, escolha **Disparar à vontade**: "Disparar no alvo" não
  existe mais nelas e, se tiver ficado gravado assim, a defesa nunca atira.
- [ ] **G4** Feixes contínuos (como o prisma iônico) **não** são abatidos (igual ao jogo).
- [ ] **G5** O consumo de munição das defesas é alto, mas a tripulação consegue manter o abastecimento.

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
- [ ] **K2** A flak e a CIWS derrubam mísseis e disparos do SW:ACD.
- [ ] **K3** As fábricas de mísseis do SW:ACD abastecem os nossos lançadores (usam as mesmas peças de míssil).
- [ ] **K4** As abas do editor e os textos dos dois mods não se misturam nem somem.

### L. Visual geral

- [ ] **L1** As torres ficam por cima do casco, com sombra, e giram suaves.
- [ ] **L2** Os canos ficam alinhados com a torre durante o giro e o recuo.
- [ ] **L3** Com o teto ligado, a parte de baixo das armas pega a cor da nave.
- [ ] **L4** Luzes âmbar/ciano/verde acendem quando a arma está funcionando e apagam quando está desligada ou
  destruída.
- [ ] **L5** Nada aparece cortado, deslocado ou com quadrado preto.

---

## 4. Dicas

- Teste uma parte por vez (por exemplo, só a logística com a Prensa e a Cigarra) para achar o problema mais rápido.
- Para os testes de míssil, deixe uma nave inimiga **parada** primeiro e depois uma **girando e acelerando**.
- Para o overclock, coloque radiadores **de sobra** primeiro (para ver o efeito) e depois **de menos** (para ver o
  aquecimento e o fogo).

## 5. Como me mandar o resultado

Para cada item que falhou, me mande:

1. O **número do item** (por exemplo **H5**).
2. **O que aconteceu** e o que você esperava.
3. Um **print** ou vídeo curto, se der.
4. Se o jogo travou: as primeiras linhas do erro (acima de `--- End of inner exception stack trace ---`).

Vários itens dos mísseis têm um **plano B** pronto no gerador, que muda o mecanismo sem mudar os números; então,
se algo de H falhar, eu já tenho por onde corrigir rápido.
