## Bullet Strike 2.0: resumo do projeto

**A ideia.** No Star Wars: A Cosmos Divided (SW) as armas custam energia. No Bullet Strike 2.0 elas custam logística: fábricas, paióis e um estoque grande dentro de cada arma. Em troca, cada arma bate cerca de 15 % mais que a equivalente do SW no mesmo nível (de 1,10 a 1,25x). O mod é balanceado para jogar com o SW: sem ele, as armas do início e do meio ficam 2 a 3x mais fortes por tile que as do jogo base (o README e a descrição do mod vão avisar).

**O que mudou desde a última versão**
- **HE e AC:** depois da primeira peça atingida, cada peça que a granada atravessa leva metade do dano, como nos turbolasers do SW. Antes ela levava o dano cheio.
- **Teste de balanço (T3):** agora mede também o Mapinguari, que nas minhas contas é a arma que mais passa do limite. Se uma arma passar, eu corrijo só a classe dela.
- **Visual futurista:** toda a munição ganha visual novo, inclusive os itens e os ícones (detalhes em "Munições").
- **Fábrica de Células:** a grade de cobre saiu de um lugar onde a tripulação não chegava.
- **TesteFita:** se o teletransporte falhar logo no A3 e no A3b, você não precisa fazer as Partes B e C.
- **Esteira:** se o teletransporte falhar, eu te pergunto antes de usar qualquer esteira física.

**Logística (sem esteira, como você pediu)**
- **Fita de Alimentação:** peça 1x1 que você gruda do lado da fábrica, do paiol ou da arma. A munição passa sozinha da fábrica para o paiol e do paiol para a arma, de qualquer canto da nave. Não tem caminho nem tripulação; só aparecem cartuchos saindo de uma peça e entrando na outra. A luz verde acende quando ela está grudada.
- **Paiol:** selado, em 4 famílias (cartuchos, células, mísseis e projéteis), de 1x1 a 3x3. Você escolhe o tipo no próprio paiol.
- **Alcance:** o navio inteiro. Se o jogo ficar lento, vira um "transmissor" de uns 12 blocos, como o Wi-Fi do MMCTR.
- **Sem fita:** a tripulação abastece a arma abaixo da metade, como hoje. No modo tripulação, fábrica encostada no paiol e paiol encostado na arma passam a munição sozinhos.

**Munições.** Numeração fixa: 0 HE, 1 AP, 2 SAP, 3 AC e 4 FRAG. Saem o APHE e o PEM dos canhões.
- **AP (Perfurante):** 70 % do dano do HE e 3 a 4x a penetração (5,7x no Tambor, para atravessar a bolha média do SW).
- **AP contra casco do SW:** nas minhas contas, o total fica entre 0,70 e 0,98x o do HE se o interior da nave resistir como eu supus. Com o interior do jogo base, que é mais fraco, o Tambor, o Trovão e o Mapinguari passam o HE (até 1,1, 1,2 e 1,4x). O teste T3 mede isso no casco do SW com o Furacão, o Trovão e o Mapinguari. Se alguma passar de 0,9x, eu corto o dano dela nas peças seguintes.
- **AP das metralhadoras:** param na blindagem do SW e ficam em 0,70x o HE, então o teste não consegue medir. Contra blindagem do jogo base ou casco sem blindagem, podem chegar a 1,1x o HE. Isso fica avisado no ARMAS.md.
- **SAP (Semiperfurante):** 85 % do dano, o dobro da penetração do HE e meia carga que explode por dentro.
- **AC (Alta Capacidade):** +50 % de dano direto, carga dobrada com raio 1,5x e +60 % no escudo.
- **FRAG (Nuvem de Fragmentos, só nas defesas):** estoura antes do alvo e solta 12, 16 ou 24 fragmentos que derrubam mísseis e minimísseis; no casco só faz faísca.
- **HE do Mapinguari:** com o interior do jogo base, ele ainda passa um pouco do limite nas minhas contas (1,7x o turbolaser do SW; o limite é 1,5x). O T3 mede ele e o Trovão; se passar, só o Mapinguari leva menos.
- **Visual futurista:** toda a munição é refeita no mesmo estilo: os 12 itens (carregadores HE, AP, SAP, AC e FRAG, células de plasma e PEM, cargas de míssil, ogiva da Iara e projétil do Tupã), as granadas de 76 mm para cima, os mísseis e os ícones dos botões. As balas pequenas (até 30 mm) continuam traçantes, com a cor de cada munição. O que já está sendo desenhado (granadas, mísseis, Tupã, Boiúna e armas PEM) entra como está. Só a AC dos canhões perde as aletas de guiagem, porque só a da Boiúna é guiada.

**Fábricas.** Etapa única, sem tripulante e com overclock (3x). Nenhuma fábrica do jogo base é necessária, e nada usa urânio enriquecido.

| Fábrica | Tamanho | Entradas | Faz | Ritmo base |
|---|---|---|---|---|
| F1 Prensa HE | 2x2 | enxofre | carregador HE | 1 a cada 1,25 s |
| F2 Munição Especial | 4x3 | enxofre + tristeel | AP / SAP / AC / FRAG | 0,625 / 0,52 / 1,67 / 0,52 s |
| F3 Células | 3x3 | enxofre + bobina; cobre | célula de plasma / Célula PEM | 2,0 / 0,9 s |
| F4 Mísseis | 3x3 | ferro + enxofre | cargas HE / submunição / PEM | 2 a cada 0,3 s / 2 a cada 0,36 s / 1 a cada 0,36 s |
| F5 Ogivas | 4x4 | ferro + urânio bruto | ogiva da Iara | 3,0 s |
| F6 Forja | 3x4 | tristeel + coil2 | projétil do Tupã | 3,0 s |

Cada 1000 de dano por segundo de HE pede 0,69 a 0,77 tile de fábrica no início e no meio, e 0,42 a 0,49 no fim (um terço com overclock). AP, SAP e AC pedem cerca de 2x, 1,5x e 2,4x isso.

**Armas.** O estoque interno dá 60 s de tiro no início e no meio, 75 s no fim, 45 s nas defesas e 5 salvas nos lançadores. Uma arma destruída com um tipo só no estoque explode como na 1.x. Com sobra de outros tipos, as explosões somam (até 4x no Mapinguari).

**Mísseis.** A Tocandira (início) atira só HE. A Caipora (meio) tem HE (Jararaca), Submunição (Piranha) e PEM (Poraquê). A Mula-sem-Cabeça (fim) tem esses três e a nuclear Iara (175.000 + 55.000 de dano), com no máximo 2 Mulas por nave. A Piranha abre a 300 m ou 400 m e solta 12 ou 20 minimísseis.

**Linha PEM** (drena escudo como os íons do SW, 12 a 19 % acima): Tuvira (1x2, fixa na proa), Treme-Treme (torre 2x2) e Mãe-do-Ouro (torre dupla 4x4). **Atenção:** uma Tuvira drena mais que um Treme-Treme (7.200 contra 6.250 de escudo por segundo). Ela é segurada por atirar só para a frente (30°) e ter alcance menor (380 m contra 440 m). Por ponto de comando, rende 3.600 contra 1.250 e 1.748 (pergunta 1).

**Railgun Tupã.** Carregador 3x4 + 1 a 6 Canos 3x3 + Ponta 3x4, no máximo 2 por nave, com 6 pontos de comando mais 2 por cano. Por tiro: 50.000 (1 cano), 72.490 (4) e 85.859 (6). Com 3 canos ou mais, é o projétil mais forte dos canhões. Com 1 ou 2, a AC da Boiúna (64.500) bate mais, e a logística passa da faixa do fim (0,72 e 0,62 tile por 1000 de dano/s). Por disparo, a salva AC do Mapinguari (90.000) bate qualquer Tupã.

**Boiúna.** Obuseiro pesado com HE e AC guiada (4.500 + 60.000 de explosão), âmbar e sem trevo. Mapinguari e Boiúna somados: no máximo 2 por nave.

**Balanço contra o SW**

| Arma | Bullet Strike | SW | Razão |
|---|---|---|---|
| Marimbondo (início) | 720 de dano/s | laser de teto compacto, 625 | 1,15x |
| Tambor (meio) | 5.400 | turbolasers médio + triplo, 4.730 | 1,14x |
| Trovão (fim) | 8.800 | turbolaser de facção, 7.060 | 1,25x |
| Mapinguari (fim) | 12.000 | Siege Turbolaser, 4.800 | 2,5x; 0,81x por tile |
| Boitatá (plasma) | 5.750 de escudo/s | íons médio, 5.250 | 1,10x; 0,73x por tile |
| Tupã, 4 canos | 72.490 por tiro | Siege Turbolaser, 30.000 | 2,4x; 0,57x por tile |

**Ruptura limpa.** Saem o APHE, o PEM dos canhões, a granada nuclear da Boiúna, duas fábricas antigas, os mísseis Carrapato, Taturana e Boto e as iscas da Iara. **Um save da 1.x pode fechar o jogo na 2.0: termine ou guarde a carreira antes. Naves da 1.x precisam ser refeitas.**

**Mande as respostas do TesteFita**
- **O que mandar:** sim ou não para A1, A2, A3 e A3b. Se o A3 ou o A3b deu sim, mande também A4 a A7, B1 a B3 e C1 a C3.
- **Se o A3 e o A3b derem não:** pare ali, como diz o roteiro. As Partes B e C não fazem falta nesse caso (o B1 ajuda, se quiser fazer). A convivência com o SW eu confiro pelo item 35 do kit antigo (Teste2).
- **Antes das respostas:** só monto builds de teste, no modo tripulação. A 2.0.0 sai depois delas: com a fita, o C3 (junto com o SW) precisa dar sim; sem a fita, o item 35 do Teste2.
- **Se o teletransporte falhar:** eu te pergunto se quer a esteira física do kit antigo ou só a tripulação.
- **Kit antigo (Teste2):** sem os itens 36 a 46, o Tupã fica fora da 2.0.0. Sem os itens 9 a 11, não entra o contador de 4 dígitos. Sem os itens 14 a 19, só a peça explode.

**Outras escolhas que já fiz (me diga se quiser diferente)**
- **Balas de até 30 mm:** a defesa de ponto não derruba, como a chaingun do jogo base.
- **Fita:** só existe a peça, sem botão de fita embutida nas máquinas.
- **Defesas contra lasers:** como na Fase B (0,55 a 0,80x o SW); posso subir para 1,15x.
- **Iara:** 12.000 de vida, como no SW. Ela chega escondida numa salva.
- **Custo da AC:** cerca de 4x o HE na fábrica; dá para baixar para 3x.

**Perguntas para você**
1. **PEM pesada e Tuvira:** a PEM pesada se chama Mãe-do-Ouro (overclock "Corisco") ou Corisco (overclock "Relâmpago")? E a Tuvira: fica como está, custa 4 pontos de comando (só muda a conta por ponto) ou vira torre (270°, 4.320 de escudo por segundo, abaixo do Treme-Treme)?
2. **Vizinhança das fábricas:** no jogo base, fábrica encostada em outra ganha +25 %. Deixei desligado no Bullet Strike para a conta de logística valer. Quer ligado? Aí as fábricas ficam 1,5x mais lentas, para o custo final ser o mesmo.
3. **Perfil jogo base:** quer um mod separado para jogar sem o SW, com dano e alcance ajustados ao jogo base? Os dois mods nunca podem ficar ativos juntos.
