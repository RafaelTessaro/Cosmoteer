# Bullet Strike 2.0 - o que testar

> Gerado por `tools/make_docs.py` a partir de `tools/spec/` (spec 2.0) e da camada de dados `tools/bs_data.py`, com os switches do build. Não edite à mão: o texto fica em `tools/spec/checklist_2_0.json`.

Este é o build de **teste** da 2.0 com a Fita de Alimentação (pasta `BulletStrike`, versão 2.0.0, descrição começando com "[2.0 de TESTE]"). Se ele não carregar, use a reserva "Bullet Strike (reserva sem Fita)" (seção 12). Os itens marcados **(com SW)** são feitos com o Star Wars: A Cosmos Divided ativo junto; **todos os outros, só com o Bullet Strike**. Sugestão: faça primeiro todos os itens sem a marca e depois, com o SW ativo, todos os (com SW) de uma vez: 1.7, 2.15, 6.5, 7.3, 7.4, 8.11, 8.12, 9.2, 9.3, 9.5, 10.1, 10.2, 10.3, 10.4, 11.3 e 11.5.

Os itens com ★ liberam a versão final 2.0.0; se tiver pouco tempo, faça pelo menos esses. Em cada item: faça o que está em "O que fazer", confira "O que olhar" e marque sim ou não. Se for não, siga o "Se não". No fim (seção 13) está como me mandar as respostas.

## 0. Antes de começar (instalação)

**0.1**

- **O que fazer:** Guarde uma cópia da sua pasta Mods/BulletStrike da 1.x e da sua carreira da 1.x. Depois apague a pasta BulletStrike da 1.x de Mods e copie a nova do zip (arquivos que mudaram de nome ficariam sobrando).
- **O que olhar:** Abrir um save da 1.x com a 2.0 pode fechar o jogo; naves da 1.x precisam ser refeitas.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Se apagou algo sem querer, me avise antes de testar.

**0.2**

- **O que fazer:** Copie também a pasta BulletStrike_SemFita (do outro zip) para Mods, mas deixe DESATIVADA. Nunca ative as duas juntas: as peças são as mesmas.
- **O que olhar:** Na lista de mods aparecem 'Bullet Strike' e 'Bullet Strike (reserva sem Fita)'.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Me diga o que aparece na lista.

**0.3**

- **O que fazer:** Jogo 0.30.4c: Novo jogo > Criativo, com 'Modo Construção Livre' MARCADO. Itens marcados '(com SW)': Star Wars: A Cosmos Divided ativo JUNTO com o Bullet Strike. Todos os outros: SÓ o Bullet Strike ativo. Dica: faça primeiro todos os itens sem a marca, seção por seção; depois ative o SW e faça todos os '(com SW)' de uma vez (estão nas seções 1, 2, 6, 7, 8, 9, 10 e 11).
- **O que olhar:** Você sabe onde fica a pasta Logs do Cosmoteer (a mesma de onde já tirou logs antes; normalmente em Jogos Salvos/Saved Games > Cosmoteer).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Me avise que eu explico onde achar o log.

## 1. Carregamento e log de erro

**1.1** ★

- **O que fazer:** Abra o jogo com o 'Bullet Strike' ativo.
- **O que olhar:** Chega ao menu sem tela de erro e sem fechar.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Mande o log mais recente da pasta Logs e passe para a seção 12 (reserva sem Fita).

**1.2** ★

- **O que fazer:** Veja a descrição do mod na lista de mods.
- **O que olhar:** Versão 2.0.0 e a 1ª linha começando com '[2.0 de TESTE]'.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Me diga a versão e a descrição que aparecem.

**1.3** ★

- **O que fazer:** Novo jogo Criativo > construir nave > aba do Bullet Strike.
- **O que olhar:** 41 botões na aba, todos com ícone (nenhum quadrado branco ou rosa): 12 canhões, 3 defesas, 3 PEM (Tuvira, Treme-Treme e Corisco), 3 lança-mísseis, o Tupã, 6 fábricas, 12 paióis e a Fita. O Tupã é um botão só, 'Railgun Tupã' (a Ponta): selecione-o e aparecem 'Carregador Tupã' e 'Cano Tupã'.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga quais faltam ou estão sem ícone.

**1.4**

- **O que fazer:** Ponha uma de cada peça na nave (pode ser numa nave grande de Estrutura).
- **O que olhar:** Nada trava; nenhuma textura xadrez ou roxa (isso seria arquivo faltando).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Print da peça + log.

**1.5**

- **O que fazer:** Em 'Gerenciar recursos' (ou numa Baia de armazenamento), procure os itens novos.
- **O que olhar:** 12 itens com visual futurista: Carregadores HE, AP, SAP, AC e FRAG, Células de Plasma e PEM, Cargas de Míssil HE, de Submunição e PEM, Ogiva Nuclear e Projétil de Railgun.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga quais estão com visual antigo ou sem ícone.

**1.6**

- **O que fazer:** Salve a nave e o jogo, saia e carregue de novo.
- **O que olhar:** Tudo volta igual, sem erro.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Mande o log.

**1.7** ★

- **O que fazer:** (com SW) Feche o jogo, ative o SW:ACD junto com o Bullet Strike e abra (Criativo).
- **O que olhar:** Carrega; as peças do SW e as do Bullet Strike aparecem.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Mande o log (isto trava a liberação da 2.0.0).

## 2. Fita de Alimentação e teletransporte (faça PRIMEIRO)

**Preparo:**

- Monte como no TesteFita: Criativo, Construção Livre, uma linha reta de Estrutura com uns 50 quadrados.
- Cada máquina fica encostada na Estrutura e longe das outras (5 quadrados ou mais).
- Cada Fita encosta de lado (não na quina) só na sua máquina e também na Estrutura.
- Fábricas: as de verdade precisam de energia e de matéria-prima. Ponha um reator e, ligados SÓ às fábricas por corredor e porta, um Beliche e uma Baia de armazenamento com Enxofre, Triaço e Hiperbobina (em 'Gerenciar recursos').
- Aperte 'Reabastecer todos os recursos' uma vez só, antes de pôr paióis e armas, e não aperte de novo até o item 2.11: ele enche tudo, e um paiol ou uma arma já cheios estragam o teste.
- Comando: as armas só atiram se a nave tiver uma sala de comando (Cabine, Sala de controle ou Ponte) funcionando. Se ainda não tiver, ponha uma Cabine no corredor das fábricas, com mais 1 Beliche.
- Armas: elas precisam de tripulação para atirar. Ponha camas só para elas: cada Tambor usa 3 tripulantes (no 2.9 são 2 Tambores) e a reserva do 2.11 precisa de 1 tripulante livre; por exemplo, 1 'Alojamentos da tripulação' (6 camas) + 1 Beliche. Ligue essas camas por corredor SÓ às armas (nada de Baia nem de fábrica nesse corredor). Assim a tripulação opera a arma, mas não tem de onde trazer munição: só a Fita abastece (até o item 2.11).
- Paióis: sem corredor nenhum (nesta versão eles são selados).
- Para as armas atirarem, crie uma nave inimiga no menu do Criativo.
- Luz verde da Fita e grade de saída das fábricas: veja com o interior ligado. Cartuchos andando: veja com o interior desligado.

**2.1** ★

- **O que fazer:** Ponha um 'Paiol de Cartuchos 1x1' (em HE) e grude uma Fita nele.
- **O que olhar:** A luz verde da Fita acende (interior ligado: 4 LEDs no piso; interior desligado: 4 lentes no teto). A barra do paiol continua vazia (ainda não tem fábrica).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** A Fita não está ligando: mande print e log.
- _(decide: art.fita_luz)_

**2.2** ★

- **O que fazer:** No modo construção, passe o mouse sobre o paiol.
- **O que olhar:** O paiol mostra o ícone da Fita (buff).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (é só um aviso visual).

**2.3** ★

- **O que fazer:** No meio da linha, ponha uma 'Prensa HE' (F1) com Fita, ligada ao reator e à Baia (preparo acima).
- **O que olhar:** Em ~20 s a barra do paiol começa a subir (sozinha, a Prensa HE faz 1 carregador a cada ~1,9 s); aparecem cartuchos saindo da Prensa HE e entrando no paiol; a pilha na grade de saída da Prensa HE sobe e desce (não fica parada cheia).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** O teletransporte fábrica -> paiol não funciona: me mande o resultado e teste a reserva (seção 12).
- _(decide: logistics.transport / fita_fabrica)_

**2.4** ★

- **O que fazer:** Tire a Fita da Prensa HE.
- **O que olhar:** A grade de saída da Prensa HE enche e para; com a Fita de volta ela volta a mandar.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**2.5** ★

- **O que fazer:** Na outra ponta, um 'Tambor' (Canhão Naval Automático 76 mm) com Fita, em HE, só com o corredor dos atiradores (preparo), atirando na nave inimiga.
- **O que olhar:** Aparecem cartuchos entrando no Tambor e a barra de HE dele sobe sem ninguém levar munição. Atirando sem parar ela pode baixar devagar: uma Prensa HE sozinha faz ~32 carregadores por minuto e o Tambor gasta ~50 carregadores por minuto. O que vale aqui é a barra receber.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** O paiol não está empurrando para a arma: me mande o resultado.
- _(decide: logistics.transport / fita_arma)_

**2.6** ★

- **O que fazer:** Tire a Fita do Tambor (ele continua atirando).
- **O que olhar:** A barra para de receber e vai esvaziando.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**2.7** ★

- **O que fazer:** Com o Tambor sem Fita e a barra de HE vazia, mude o Tambor para AP e SÓ DEPOIS grude a Fita de volta.
- **O que olhar:** A barra de AP continua vazia (o paiol só tem HE: um tipo nunca vira outro). Depois ponha uma 'Fábrica de Munição Especial' (F2) em AP e outro 'Paiol de Cartuchos 1x1' trocado para AP, os dois com Fita: a barra de AP do Tambor sobe e o paiol de HE nunca recebe AP.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Mistura de tipos: me avise (isso trava a Fita).
- _(decide: logistics.transport (A7))_

**2.8** ★

- **O que fazer:** Troque o paiol de HE (cheio) para AP no botão do paiol. Depois volte o Tambor para HE.
- **O que olhar:** A Prensa HE para de mandar para ele. O Tambor, de volta em HE, recebe o HE que ficou no paiol.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**2.9** ★

- **O que fazer:** Um para muitos: 2 Prensas HE + 2 paióis de cartuchos em HE + 2 Tambores em HE, todos com Fita e longe uns dos outros.
- **O que olhar:** Os 2 paióis e os 2 Tambores recebem munição (cartuchos entrando em todos); nenhum fica de fora.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote qual não recebeu.

**2.10** ★

- **O que fazer:** Monte o Carregador do Tupã + 1 Cano + Ponta e ponha um 'Paiol de Projéteis 1x1' e uma 'Forja de Projéteis' (F6), cada máquina com Fita (no carregador, de lado). A F6 precisa de Triaço e Hiperbobina na Baia.
- **O que olhar:** Primeiro as cápsulas azuis aparecem na janela do carregador (até 12); depois o paiol de projéteis enche (até 20). Sozinha, a Forja de Projéteis faz 1 projétil a cada ~4,5 s: leva alguns minutos.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (a reserva pela tripulação continua valendo).

**2.11** ★

- **O que fazer:** Reserva da tripulação: ligue ao corredor das armas uma Baia de armazenamento com Carregadores HE (em 'Gerenciar recursos'; agora pode apertar 'Reabastecer todos os recursos'). Tire TODAS as Fitas e deixe o Tambor atirando 1 minuto.
- **O que olhar:** Quando a barra do Tambor passa da metade para baixo (~30 s atirando), um tripulante traz Carregadores HE.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** A reserva por tripulação quebrou: me avise.
- _(decide: logistics.reserva_tripulacao (B1))_

**2.12** ★

- **O que fazer:** Ponha as Fitas de volta (com as Prensas HE ligadas).
- **O que olhar:** O Tambor recebe pela Fita e a tripulação quase nunca leva munição a ele (só se ele cair abaixo da metade).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote o que a tripulação fez (B2).

**2.13** ★

- **O que fazer:** Com as Fitas no lugar, desligue TODAS as Prensas HE (ou tire a Fita delas) e espere os paióis esvaziarem: todos têm HE desde o 'Reabastecer' do 2.11, até os que estão em AP. Para ir mais rápido, tire a Fita só dos paióis (a do Tambor fica).
- **O que olhar:** Quando o Tambor passa da metade, a tripulação volta a abastecer.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (B3: com a Fita a arma dependeria só do paiol).

**2.14** ★

- **O que fazer:** Monte uma nave em duas metades ligadas por uma fileira de Estrutura. Numa metade, o paiol de cartuchos com Fita e cheio de HE. Na outra, o Tambor com Fita, uma Cabine (sem sala de comando a metade dele não atira) e camas para 4 tripulantes (2 Beliches: 3 para o Tambor e 1 para a Cabine), com o corredor só até os postos (sem Baia). Com o Tambor atirando, selecione as Estruturas do meio e use Autodestruição.
- **O que olhar:** Depois de separar, o Tambor não recebe mais nada: a barra só desce até esvaziar (~60 s atirando com ela cheia). A Fita não atravessa para outra nave.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (C1).

**2.15** ★

- **O que fazer:** (com SW) Monte um 'Heavy Reinforced Reactor' ou 'WIP! Light Hypermatter Reactor' do SW com Overclock perto das peças com Fita.
- **O que olhar:** As peças do SW continuam com energia e as barras das peças com Fita não mudam.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Isto trava a liberação: mande o resultado e o log.
- _(decide: portao (C3))_

## 3. Famílias de armas

**3.1**

- **O que fazer:** Metralhadoras e canhões leves (Marimbondo, Mangangá, Carcará, Saci, Cigarra e Furacão): troque o tipo no botão de munição.
- **O que olhar:** Só aparecem os tipos de cada arma (Marimbondo, Mangangá, Saci e Cigarra: HE/AP; Carcará e Furacão: HE/AP/SAP); trocar o tipo troca a barra que enche. No Marimbondo (1 quadrado) aparecem duas barras finas lado a lado (HE à esquerda, AP à direita), cada uma com o seu botão de consumo.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga qual arma ou tipo falhou.

**3.2**

- **O que fazer:** Atire com elas perto de um casco branco e no espaço.
- **O que olhar:** Traçantes com a cor da munição (HE âmbar, AP branco-azulado, SAP laranja); o brilho grande aparece só no espaço, sem mancha branca no casco.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Print do casco lavado.

**3.3**

- **O que fazer:** Canhões navais (Tambor 76 mm, Trovão 155 mm e Mapinguari 406 mm) em HE, AP, SAP e AC.
- **O que olhar:** 4 tipos no botão; granadas futuristas: HE âmbar, AP branco-azulado, SAP laranja, AC carmim com faixa dourada e SEM aletas de guiagem (voa reta).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga qual granada está errada.

**3.4**

- **O que fazer:** Olhe a traseira das granadas do Tambor e do Trovão em voo.
- **O que olhar:** O clarão branco da base é pequeno e fica atrás da granada (não cobre a granada).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Print.

**3.5**

- **O que fazer:** AP contra uma pilha de blindagem (várias peças).
- **O que olhar:** Em cada peça atravessada só faísca; a explosão cheia só onde a granada para.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote se cada peça faz a explosão inteira.

**3.6**

- **O que fazer:** AC contra o casco.
- **O que olhar:** Explosão dourada grande com anel de pressão (nunca verde).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Print.

**3.7**

- **O que fazer:** Boiúna (obuseiro 5x6) em HE e em AC.
- **O que olhar:** Torre âmbar, com cara de obuseiro comum (nada nuclear); traçante FINO (parece granada, não foguete); atira nos dois tipos, gastando 1,5 carregador por disparo; a AC faz curva atrás de um alvo que anda, a ~600 m.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga o que falhou.
- _(decide: boiuna.ac_guided (B-1))_

**3.8**

- **O que fazer:** Ponha 3 armas entre Mapinguari e Boiúna na mesma nave.
- **O que olhar:** A 3ª é recusada (no máximo 2 somadas).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**3.9**

- **O que fazer:** Boitatá e Curupira (plasma) com Células de Plasma (F3 em Plasma + paiol de células, com Fita).
- **O que olhar:** Recebem as células e atiram com os efeitos de plasma de sempre.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**3.10**

- **O que fazer:** Destrua um Tambor cheio de HE e outro vazio.
- **O que olhar:** O cheio explode como na 1.x; o vazio quase não explode.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T11).

## 4. Fábricas

**4.1**

- **O que fazer:** Ponha as 6 fábricas.
- **O que olhar:** Arte nova: F1 Prensa HE 2x2, F2 Fábrica de Munição Especial 4x3, F3 Fábrica de Células 3x3, F4 Fábrica de Mísseis 3x3, F5 Fábrica de Ogivas Nucleares 4x4 e F6 Forja de Projéteis 3x4; a animação só roda produzindo.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga qual está errada.

**4.2**

- **O que fazer:** Abasteça as entradas (com tripulação; sem Construção Livre, se precisar).
- **O que olhar:** F1 enxofre; F2 enxofre + triaço; F3 enxofre + bobina (Plasma) e cobre (PEM); F4 ferro + enxofre; F5 ferro + urânio; F6 triaço + hiperbobina. A tripulação alcança todas as grades.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga qual grade não recebe.

**4.3**

- **O que fazer:** Troque o modo: F2 (AP/SAP/AC/FRAG, começa em AP), F3 (Plasma/PEM) e F4 (HE/Submunição/PEM).
- **O que olhar:** A placa do teto troca e a saída certa produz; a F3 em PEM mostra o banco PEM aceso só produzindo.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**4.4**

- **O que fazer:** Vizinhança: uma Prensa HE sozinha e outra encostada em 2 fábricas (do Bullet Strike ou do jogo base).
- **O que olhar:** A estatística mostra o bônus de fábrica (+25 % por vizinha); sozinha ela faz 1 carregador a cada ~1,9 s; com 2 vizinhas, a cada ~1,25 s.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote os tempos.
- _(decide: econ.factory_adjacency)_

**4.5**

- **O que fazer:** Overclock nas fábricas.
- **O que olhar:** Produz ~3x mais rápido e esquenta.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**4.6**

- **O que fazer:** F2 em AC por 2 minutos seguidos.
- **O que olhar:** Não trava (a saída de AC continua andando).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T-F2-SPLIT).

**4.7**

- **O que fazer:** Destrua uma fábrica com estoque na grade de saída.
- **O que olhar:** Explosão moderada (por saída), não maior que a da fábrica equivalente do jogo base.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**4.8**

- **O que fazer:** Sem Fita: a tripulação recolhe da grade de saída.
- **O que olhar:** Igual a uma fábrica do jogo base.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

## 5. Paióis

**5.1**

- **O que fazer:** Ponha os 12 paióis (cartuchos, células, mísseis e projéteis; 1x1, 2x2 e 3x3).
- **O que olhar:** Teto com a cor da família, placa do tipo, medidor lateral; selados (sem porta) nesta versão com Fita.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga qual está errado.

**5.2**

- **O que fazer:** Troque o tipo no botão do paiol.
- **O que olhar:** A placa troca e ele passa a aceitar só o tipo escolhido.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**5.3**

- **O que fazer:** Encha um paiol pela Fita.
- **O que olhar:** A barra sob a vida e o medidor do teto sobem juntos (5 / 8 / 10 níveis). Não há contador de números (desligado nesta versão).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.
- _(decide: logistics.paiol_contador)_

**5.4**

- **O que fazer:** Encha até parar.
- **O que olhar:** Capacidade em cartuchos HE: 60 no 1x1, 276 no 2x2 e 702 no 3x3; em projéteis: 20 / 92 / 234.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote o número.

**5.5**

- **O que fazer:** Destrua um paiol 1x1 de HE cheio e outro vazio.
- **O que olhar:** O cheio explode bem mais que o vazio.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (itens 14-16 do kit antigo).

**5.6**

- **O que fazer:** Abra o painel de recursos da nave.
- **O que olhar:** Ele conta o estoque dos paióis.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote se conta ou não (só para eu saber).

## 6. Mísseis

**6.1**

- **O que fazer:** Tocandira, Caipora e Mula-sem-Cabeça: botão de tipo.
- **O que olhar:** Tocandira só HE; Caipora HE / Submunição / PEM; Mula-sem-Cabeça HE / Submunição / PEM / Nuclear.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**6.2**

- **O que fazer:** Alimente pela Fita (F4 + paiol de mísseis) e, sem Fita, pela tripulação abaixo da metade.
- **O que olhar:** O lançador enche (células e depósito) nos dois casos.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**6.3**

- **O que fazer:** Atire cada tipo.
- **O que olhar:** Mísseis com visual novo; a Iara inconfundível (verde, com o trevo de radiação).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Print.

**6.4**

- **O que fazer:** Submunição (Piranha) contra uma nave.
- **O que olhar:** O portador abre a ~300 m (Caipora) / ~400 m (Mula) do alvo e solta 12 / 20 minimísseis que acertam peças DIFERENTES; as pétalas do nariz caem e somem; nunca acertam o próprio convés.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.
- _(decide: missiles.cluster_randomize_target (T-MSL-CLUSTER))_

**6.5**

- **O que fazer:** (com SW) Poraquê contra uma bolha do SW, com e sem overclock do escudo.
- **O que olhar:** Tira ~10.300 (Caipora) / ~19.150 (Mula) de escudo por acerto, igual com e sem overclock.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote os números (T-MSL-EMP).

**6.6**

- **O que fazer:** Iara (Mula em Nuclear).
- **O que olhar:** 2 estágios (o corpo solta a ogiva ~1,5 s depois do lançamento), uma ogiva só, explosão nuclear grande; a 3ª Mula é recusada; o overclock não acelera a recarga da nuclear.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T-MSL-NUKE).

**6.7**

- **O que fazer:** Destrua uma Mula cheia de HE e de Submunição.
- **O que olhar:** Explosão grande, mas não maior que na 1.x.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T-MSL-COOK).

## 7. Linha PEM

**7.1**

- **O que fazer:** Tuvira (1x2) com Células PEM (F3 em PEM + paiol de células em PEM, com Fita).
- **O que olhar:** É uma TORRE que gira 270° (não só para a frente), com 2 canos; atira ~1,4 tiro/s.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.
- _(decide: pem.tuvira_mount)_

**7.2**

- **O que fazer:** Treme-Treme e a PEM pesada.
- **O que olhar:** A pesada se chama 'Corisco' e o overclock dela 'Relâmpago'; arcos e brilho azul antes do tiro.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote o nome que aparece.
- _(decide: pem.heavy_name)_

**7.3**

- **O que fazer:** (com SW) Contra uma bolha média do SW (20.000 de escudo).
- **O que olhar:** Ela quebra em ~4,6 s (Tuvira), ~3,2 s (Treme-Treme), ~1,1 s (Corisco); igual com overclock do escudo.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote os tempos (T1).

**7.4**

- **O que fazer:** (com SW) Acertos no casco e nas torres do SW.
- **O que olhar:** Quase não fazem dano; peças do SW drenadas apagam. Já as armas do Bullet Strike quase não sentem os íons do SW (menos o Tupã, que gasta a bateria do carregador).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T5).

**7.5**

- **O que fazer:** Corisco com overclock (Relâmpago).
- **O que olhar:** O tiro atravessa peças e drena por ~10 s.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

## 8. Tupã com tranco

**8.1**

- **O que fazer:** Monte o Carregador do Tupã (5x5) + 1 Cano + Ponta em linha (os canos encaixam no MEIO da borda de cima do carregador).
- **O que olhar:** A Ponta fica operacional; com 0 canos (Ponta direto no carregador) ou 7 canos ela mostra peça faltando e não atira.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Print do montado.
- _(decide: rail.enabled (R-1))_

**8.2**

- **O que fazer:** Desloque o carregador 1 quadrado para o lado.
- **O que olhar:** Nada conecta (ícone de peça faltando).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T-TR-5).

**8.3**

- **O que fazer:** Leia a dica (tooltip) da Ponta do Tupã e passe o mouse também sobre um Cano. Depois monte o Tupã com 4 Canos (Carregador + 4 Canos + Ponta) e veja quanto sobem os pontos de comando usados pela nave.
- **O que olhar:** A dica da Ponta mostra bônus de +25 a +115 % e uma linha por número de canos (1 a 6); a dica do Cano abre sem erro. O Tupã com 4 canos gasta 14 pontos de comando ao todo.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**8.4**

- **O que fazer:** Energia: monte o Tupã com camas para os 2 tripulantes do carregador no corredor dele e sem nenhum reator ligado a esse corredor. Aperte 'Reabastecer todos os recursos' (enche a bateria do carregador) e deixe o Tupã atirar na nave inimiga até parar; conte os tiros. Faça com 1, 4 e 6 Canos.
- **O que olhar:** Sem recarga ele para depois de 6 tiros com 1 Cano, 4 com 4 e 3 com 6. A dica do Carregador do Tupã mostra a bateria cheia (15 de energia) e a dica da Ponta, o gasto por tiro (2,5 com 1 Cano, 4 com 4, 5 com 6). Depois ligue um reator ao corredor: a tripulação traz bateria ao carregador e ele volta a atirar.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote quantos tiros saíram com cada número de Canos.

**8.5**

- **O que fazer:** Antes do tiro, olhe os canos.
- **O que olhar:** A carga azul acende do carregador para a ponta; o dardo azul desliza pelo canal; nada reacende depois do tiro.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**8.6**

- **O que fazer:** TRANCO: nave pequena parada, Tupã no centro, 1 tiro.
- **O que olhar:** A nave dá um tranco PARA TRÁS; com 6 canos empurra mais que com 1.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Se for para a frente ou não mexer, anote.
- _(decide: rail.tranco_impulso (T-TR-1))_

**8.7**

- **O que fazer:** Tupã fora do centro da nave.
- **O que olhar:** A nave gira um pouco (normal, como o canhão eletromagnético do jogo base).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote se gira demais (T-TR-2).
- _(decide: rail.recoil_com)_

**8.8**

- **O que fazer:** Olhe de perto vários tiros, com o teto e com o interior ligado.
- **O que olhar:** A cada tiro, UMA vez só (nunca um segundo coice meio segundo depois): a frente da ponta (com as bochechas brancas), os tambores de CADA cano e, logo depois, o bloco da culatra com as molas recuam e voltam. Parados, tudo em repouso (nada faltando nem desenhado em dobro); com o interior ligado o bloco da culatra não cobre os tripulantes.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga qual peça não mexe, se mexe duas vezes ou o que cobre o interior (T-TR-3, T-TR-A2).
- _(decide: rail.tranco_gatilho / camada do tranco)_

**8.9**

- **O que fazer:** Tremor e anel.
- **O que olhar:** A tela treme a cada tiro (some com 'Tremor de tela' desligado nas opções); um anel azul na boca fica no lugar enquanto a nave recua.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T-TR-4).

**8.10**

- **O que fazer:** Ponha peças da própria nave na frente do Tupã e mande atirar num inimigo.
- **O que olhar:** A IA atira e o dardo passa POR CIMA da própria nave, sem dano.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote o dano na própria nave.

**8.11**

- **O que fazer:** (com SW) Números: 1, 4 e 6 canos contra bolhas de escudo do SW (média e grande).
- **O que olhar:** Alcance ~500 / 700 / 700 m; com 1 cano o dardo fura a bolha média do SW e continua; com 4 a bolha grande cai em 2 tiros.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (R-1/R-3).

**8.12**

- **O que fazer:** (com SW) 4 canos contra 3 fileiras de durasteel do SW + interior.
- **O que olhar:** Tira 60.000 de HP ou mais; fogo e calor onde o dardo para; peças com energia atravessadas chiam ~4 s.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (R-2).

**8.13**

- **O que fazer:** Limite.
- **O que olhar:** A 3ª Ponta é recusada; 2 Mapinguari + 2 Tupã são aceitos.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (R-4).

**8.14**

- **O que fazer:** Cores.
- **O que olhar:** Tudo AZUL (carregador, canos, ponta, dardo, rastro, faíscas, raios e clarões do impacto, escudo atingido): nada violeta e nada dourado na energia. Só as brasas laranja que ficam queimando no alvo depois do impacto são quentes (de propósito).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Print (e diga se prefere as brasas azuis também).

**8.15**

- **O que fazer:** (opcional) Multijogador ou replay com muitos tiros.
- **O que olhar:** Sem dessincronizar.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T-TR-6).

## 9. Defesas contra os lasers do SW

**9.1**

- **O que fazer:** Tatu, Tamanduá e Pororoca: botão HE / FRAG, alimentados pela Fita (cartuchos HE e FRAG).
- **O que olhar:** Recebem e atiram nos dois modos.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**9.2**

- **O que fazer:** (com SW) Contra mísseis do SW.
- **O que olhar:** Derrubam vários de uma vez.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**9.3**

- **O que fazer:** (com SW) Contra tiros de laser e de íon do SW.
- **O que olhar:** Derrubam parte dos tiros: úteis, mas mais fracas que a defesa do SW contra lasers (como na Fase B: 0,55-0,80x).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Se achar fraco demais, diga: dá para subir para 1,15x.
- _(decide: guns.defesa_antilaser)_

**9.4**

- **O que fazer:** Tamanduá em FRAG contra uma salva de Piranhas de uma nave inimiga (Caipora em Submunição) e contra um casco a 30 m.
- **O que olhar:** Os fragmentos destroem os minimísseis inimigos e não derrubam os nossos mísseis que passam por perto; no casco só faísca, sem dano e sem travar.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T-FRAG).
- _(decide: guns.frag_fragment)_

**9.5**

- **O que fazer:** (com SW) Defesas do SW contra as nossas balas pequenas (até 30 mm).
- **O que olhar:** Não derrubam as balas pequenas (como o canhão de repetição do jogo base).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

## 10. Balanço contra o SW

**10.1**

- **O que fazer:** (com SW) T3 etapa 1: Trovão HE e Mapinguari HE contra o 'Imperial Heavy Turbolaser' do SW, num bloco interior 2x2 sem blindagem (10 tiros cada).
- **O que olhar:** O que entra depois do primeiro contato fica no máximo ~1,5x o do turbolaser.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote o HP tirado por cada um.
- _(decide: guns.he_further_factor)_

**10.2**

- **O que fazer:** (com SW) T3 etapa 2: 10 tiros AP e 10 HE de Furacão, Trovão e Mapinguari (e SAP x HE de Trovão e Mapinguari) contra 1 durasteel do SW + interior 2x2 + corredores.
- **O que olhar:** O AP tira no máximo 0,90x o HP que o HE tira; o SAP, no máximo 0,95x.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote os HPs.
- _(decide: guns.ap_further_factor)_

**10.3**

- **O que fazer:** (com SW) Combate geral.
- **O que olhar:** Por nível, as armas do Bullet Strike ficam ~15 % acima das do SW (Marimbondo x laser de teto, Tambor x turbolaser médio, Trovão x turbolaser de facção; Boitatá e PEM x íons).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga quais parecem fortes ou fracas demais.

**10.4**

- **O que fazer:** (com SW) Tupã contra o 'Dual 70TT Superheavy Turbolaser' do SW.
- **O que olhar:** O Tupã bate mais por tiro (2,4x com 4 canos), mas rende menos por espaço (o carregador 5x5 é o preço).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga se ficou forte ou fraco demais (se fraco: dá para atirar a cada 5,4 s em vez de 6 s).

**10.5**

- **O que fazer:** Logística.
- **O que olhar:** Com fábricas encostadas umas nas outras, o custo em fábricas parece razoável para manter as armas atirando.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Diga se as fábricas parecem lentas demais.

## 11. Desempenho

**11.1** ★

- **O que fazer:** 10 paióis, 20 armas e 5 fábricas, todos com Fita.
- **O que olhar:** O jogo não fica lento; ao selecionar um paiol aparece só uma cruzinha verde, nenhum retângulo do tamanho da nave.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Descreva (se ficar lento, eu troco a Fita para um alcance de ~12 quadrados).
- _(decide: logistics.fita_alcance (C2))_

**11.2**

- **O que fazer:** 2 Mulas + 2 Caiporas em Submunição, juntas, contra um alvo de ~150 peças.
- **O que olhar:** Fica jogável.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote o FPS (T-MSL-PERF).

**11.3**

- **O que fazer:** (com SW) 2 Tupã de 6 canos atirando 30 s contra uma nave do SW de ~40 peças.
- **O que olhar:** Fica jogável.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (P-1).

**11.4**

- **O que fazer:** Mapinguari em AP numa pilha de 13 blindagens.
- **O que olhar:** Sem engasgo a cada tiro.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T-ART-6).

**11.5**

- **O que fazer:** (com SW) Uma batalha grande de 10 minutos.
- **O que olhar:** O jogo não fecha.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Mande o log se fechar.

## 12. Reserva sem Fita (só se a seção 1 ou 2 falhar, ou para comparar)

**12.1**

- **O que fazer:** Desative 'Bullet Strike', ative 'Bullet Strike (reserva sem Fita)' (nunca os dois) e abra o jogo.
- **O que olhar:** Carrega; a Fita não existe; o resto é igual.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Mande o log.

**12.2**

- **O que fazer:** Ponha paióis.
- **O que olhar:** Eles têm portas e a tripulação entra (sala de munição caminhável).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**12.3**

- **O que fazer:** Ponha um paiol de cartuchos 1x1 sozinho e aperte 'Reabastecer todos os recursos' (ele enche o paiol). Só depois encoste um Marimbondo novo (vazio) com o paiol logo atrás dele, com o atirador no posto e sem Baia de munição.
- **O que olhar:** A arma enche e atira sem ninguém levar munição (paiol acoplado).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T-ACOPLA arma).
- _(decide: logistics.acoplamento)_

**12.4**

- **O que fazer:** Prensa HE com um paiol 1x1 encostado embaixo da saída.
- **O que olhar:** O paiol enche sozinho (a tripulação só leva o enxofre para a Prensa HE).
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote (T-ACOPLA fábrica).

**12.5**

- **O que fazer:** Tripulação e corredor ligando paióis e armas (sem Fita nesta versão).
- **O que olhar:** A tripulação leva munição dos paióis para as armas abaixo da metade.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

**12.6**

- **O que fazer:** Ponha um paiol de projéteis 1x1 sozinho e aperte 'Reabastecer todos os recursos'. Só depois monte o Tupã (Carregador + 1 Cano + Ponta) com o paiol encostado atrás do canto de trás esquerdo do carregador (um 2x2 ou 3x3 também serve, crescendo para a esquerda, para não tampar a porta de trás).
- **O que olhar:** Ele alimenta o carregador sem ninguém carregando projéteis; a tripulação ainda entra pelas portas de trás.
- **Deu certo?** [ ] sim  [ ] não
- **Se não:** Anote.

## 13. Como me mandar as respostas

1. Mande uma linha por item: número + sim/não + o que viu (ex.: '2.3 sim', '8.6 não: andou para a frente'). Pode pular o que não deu para testar (diga 'não testei').
2. Se travou: mande o log mais recente da pasta Logs e, se puder, um print.
3. Se você já tinha respostas do TesteFita (A1-A7, A3b, B1-B3, C1-C3), mande também. Não é mais obrigatório: a seção 2 refaz o kit com as peças de verdade.
