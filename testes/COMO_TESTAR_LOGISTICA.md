# Kit de testes do Bullet Strike 2.0: roteiro

**O que é este mod.** O **"[TESTE] Bullet Strike 2.0 - kit de testes"** é um mod pequeno, separado do Bullet Strike, que você pode apagar depois. Ele traz 20 peças de teste. Todas começam com **[TESTE]** e ficam na aba **BS Teste 2.0** do editor. Com elas você responde, no jogo de verdade, às dúvidas da 2.0: a munição anda sozinha por uma esteira (fábrica → paiol → arma, sem tripulação)? O contador de números funciona? O paiol explode mais quando está cheio? O railgun Tupã de 3 peças funciona? O kit usa só recursos do jogo base: **Munição**, **Peça de míssil A.E.**, **Bateria** e, nas 2 peças de controle, **calor**.

**Seu tempo:** a **Parte 1** (uns 15 minutos, 8 perguntas) é a que decide o projeto da 2.0. Se só der tempo para uma coisa, faça só a Parte 1 e me mande as 8 respostas. As Partes 2 e 3 são opcionais.

---

## Antes de começar

### Instalar (Windows)

1. Baixe o **`BulletStrike_Teste2.zip`** (o arquivo que te mandei na conversa, ou a pasta `testes` do repositório no GitHub) e extraia. Dentro há duas pastas:
   - **`BulletStrike_Teste2`**: use esta.
   - **`BulletStrike_Teste2_SemIcone`**: reserva. Só use se der o erro de ícone de rede (veja "Se der erro", no fim). As duas têm o mesmo ID: **nunca deixe as duas juntas** na pasta Mods.
2. Abra a pasta **Mods** do Cosmoteer:
   - O jeito mais fácil: no jogo, abra **Mods** (Gerenciador de mods) e clique em **Mostrar pasta**.
   - Ou cole `%USERPROFILE%\Saved Games\Cosmoteer` na barra de endereço do Explorador de Arquivos e aperte Enter. Entre na pasta com o número da sua conta Steam e depois em `Mods`. No Windows em português, "Saved Games" aparece como **"Jogos Salvos"**.
   - Se não achar ali, procure em `%APPDATA%\Cosmoteer\<número da Steam>\Mods` (instalações antigas).
3. Copie a pasta **`BulletStrike_Teste2`** inteira para dentro de `Mods`. Confira: tem que existir `...\Mods\BulletStrike_Teste2\mod.rules`. Não pode ficar uma pasta dentro da outra.
4. No jogo: **Mods** → ative **"[TESTE] Bullet Strike 2.0 - kit de testes"** → **Reiniciar agora**.
5. **Para a Parte 1, se puder, desative os outros mods** (Bullet Strike, Star Wars: A Cosmos Divided etc.) e reinicie. Assim, se algo der errado, sei que foi o kit. No item 35 você liga todos juntos.
6. O `--devmode` pode ficar como estava no teste anterior.

### Começar a partida Criativa

- No menu principal, comece um jogo **Criativo**. Construa como no teste anterior: no Criativo as peças saem prontas e não gastam nada (se o jogo pedir, ligue o **Modo Construção Livre**).
- **Recursos brutos: não precisa de nenhum.**
  - As Fábricas de teste criam munição do nada.
  - Os paióis têm botões para encher e esvaziar.
  - O Carregador do Tupã tem um botão para encher a bateria.
  - Se alguma peça do jogo base precisar de recurso, use **Gerenciar recursos → Reabastecer todos os recursos**. **Nunca use esse botão na Parte 1**: ele também enche a Arma de teste e estraga a leitura.
- **Salvar:** Esc → **Salvar jogo**. O roteiro avisa quando salvar.

### Se o jogo travar: o que mandar

- Tire um print da mensagem de erro, ou copie as ~20 primeiras linhas dela.
- Mande o **log**: na pasta do Cosmoteer (a mesma do passo 2, uma acima da pasta Mods ou duas acima), abra a pasta **Logs** e pegue o arquivo **`log <data> <hora>.txt` mais recente**. Caminho comum: `%USERPROFILE%\Saved Games\Cosmoteer\Logs\`. Se houver um arquivo com "crash" no nome, mande também.
- Diga em qual passo estava. Os casos conhecidos estão em "Se der erro", no fim.

### Regras do kit (leia uma vez)

- **Botões das peças:**
  - **Tipo**: Munição de canhão ou Peça de míssil A.E.
  - **Estoque**: `=` normal; `+1` = +1 por segundo; `▲▲` = encher rápido; `▼▼` = esvaziar rápido. Age só no tipo selecionado.
  - **Energia** (o botão de ligar/desligar do jogo, dica "Energia: ligada/desligada"): na **Arma de teste** ele quer dizer **ATIRAR** (gasta 4 por segundo).
  - **Detonar**: o mesmo botão da Carga explosiva.
- **REGRA DE OURO:** volte o Estoque para `=` **antes** de trocar o Tipo e antes de seguir para o próximo passo.
- **Peça nova pode vir com o último botão que você escolheu.** Ao colocar qualquer peça, confira Tipo, Estoque e Energia.
- **Barras:** aparecem embaixo da barra de vida quando você passa o mouse na peça ou a seleciona. Se não aparecerem, clique na peça para selecioná-la e confira Configurações → Jogabilidade → "Mostrar barras de status de peças selecionadas".
  - **Verde** = cheia de verdade (só fica verde a 100%). Amarela = no meio. Vermelha = quase vazia.
  - A Arma de teste tem duas barras: a de **Munição** e a **roxa** (Peça de míssil A.E.). A roxa nunca fica verde: cheia, ela fica quase branca.
- **Luzes:** ficam embaixo do teto. A verde da Arma fica acesa enquanto ela recebe pela esteira; a laranja, enquanto ela atira. A verde é um pontinho num canto da Arma; a laranja fica na ponta do cano desenhado; a da fábrica é um pontinho amarelo no meio dela (dê zoom).
- **Durante toda a Parte 1, deixe o interior da nave à mostra** (botão de interior, dica "Exibe o interior da nave", ou a tecla "Ligar/desligar interior da nave"; Configurações → Controles mostra qual é). Só assim você vê as luzes, a tripulação e a grade da fábrica. As barras aparecem do mesmo jeito. O jogo pode mostrar o interior sozinho ao abrir o editor de naves, e aí o botão o esconde: confira pelo que aparece (piso e paredes = à mostra; teto liso = escondido).
- **Contadores e medidores** (Partes 2 e 3) ficam no teto: para lê-los, **esconda o interior** com o mesmo botão.
- **Encostar liga direto.** Fábricas de teste, todos os paióis, Arma de teste, Tremonha, Fonte e Tanque de calor têm porta de esteira em **todas as bordas**. Duas dessas peças encostadas se ligam **sem esteira nenhuma**.
  - Por isso, **deixe 1 bloco vazio entre elas**, a não ser que o desenho mostre as duas encostadas.
  - O Carregador do Tupã só liga pelos **2 cantos de trás**. Cano e Ponta do Tupã não ligam.
- **Esteira de munição:** liga sozinha nos vizinhos. **Não deixa a tripulação passar** (o Corredor com esteira deixa). **Não liga** em Termoduto, Radiador, Corredor, Porta nem em peças do jogo base.
- **Sem paiol no caminho, nada passa** (de propósito): a fábrica só entrega para paiol, e a arma só puxa de paiol.
- **Portas:** a tripulação só entra numa sala (Fábrica, Arma, Tremonha, Carregador, alojamentos) por uma **Porta**. O jogo põe as Portas sozinho quando você coloca as peças (**Configurações → Editor de naves → Adicionar portas automaticamente**: vem ligado; deixe ligado). Esteira, paióis, Fonte, Tanque e Blindagem não aceitam porta. Onde o roteiro pede uma Porta, confira se ela apareceu; se faltar, ponha à mão.
- **Peça solta não dá:** o jogo recusa peça que não encosta na nave ("Não conectado"). Quando o roteiro pede uma peça separada, prenda-a na nave **só por Blindagem**.

---

# Parte 1 - Teste essencial (uns 15 min)

Esta parte decide a 2.0: **a munição anda pela esteira sem tripulação?** Junto vai uma peça de **controle** que faz o mesmo com **calor**, que o jogo já move por rede. Ela separa "defeito da esteira do kit" de "o jogo não deixa munição andar em rede".

Monte a Parte 1 num canto vazio da nave com **espaço livre de 11 blocos de largura por 6 de altura**: o 1A usa as 3 linhas de cima; o 1B e o 1C também usam as 3 de baixo. Prenda na nave com **Blindagem** (o jogo não aceita peça solta: "Não conectado"), só por cima do C ou do T (nunca só por cima do P: o P é desmontado no 1C.4) ou pelo lado de fora da F ou da A (à esquerda da F, à direita da A, na altura delas). **Nada da nave pode encostar nas 3 linhas de baixo.** Como só a Blindagem encosta na nave, o jogo não põe porta entre a nave e estas peças, e nenhum tripulante da nave chega até elas. A Parte 1 não precisa de energia nem de ponte.

## 1A. Fábrica → esteira → paiol → esteira → arma (uns 3 min)

1. **SALVE O JOGO** (Esc → Salvar jogo). É a primeira vez que munição entra na esteira. Se o jogo travar, volte a este save e veja "Se der erro".
2. Monte assim. Cada letra é 1 bloco, `=` é Esteira de munição e `.` é vazio:

   ```
   . . . C . P . T . . .
   F F = = = = = = = A A
   F F . . . . . . . A A
   ```

   - **F** = Fábrica de teste - Munição (2x2; no menu: "[TESTE] Fáb. munição"), **ligada**.
   - **P** = Paiol simples 1x1 (só munição), Estoque `=`.
   - **A** = Arma de teste (2x2): Tipo **Munição de canhão**, Atirar (botão **Energia**) **desligado**.
   - **C** = Controle - Fonte de calor, **ligada**.
   - **T** = Controle - Tanque de calor, Estoque `=`.
   - C, P e T encostam **só** na esteira, com 1 bloco vazio entre eles.
   - Ao colocar cada um (C, P e T), confira: embaixo dele a esteira desenha uma saída para cima (um T). Se não desenhar, a peça não está ligada: encoste-a direito na esteira.
   - Nas duas pontas, a esteira tem que entrar reta na F e na A. Se a ponta aparecer fechada/arredondada, a F ou a A não está encostada direito.

   **Coloque o P por último:** a munição só começa a andar quando ele encosta na esteira. Antes de colocá-lo, mostre o interior da nave e confira: você tem que ver o piso, as paredes e a grade da fábrica, não o teto liso. Se sair do editor de naves, confira de novo.
3. Assim que colocar o P, espere **40 s** olhando. Esperado:
   - A **Arma enche primeiro** (~6 s): barra de Munição verde (60). A luz verde fica acesa enquanto ela recebe.
   - Depois o **Paiol simples enche** (~20 s): barra verde (200).
   - O **Tanque de calor enche** (~20 s depois que você o coloca; pode já estar cheio): barra verde (200). A luz laranja da Fonte fica acesa enquanto ela manda calor e apaga quando o Tanque enche.
   - Os cartuchos andam na esteira enquanto P ou T enchem e param ~1 s depois.
   - Com o P cheio, a sobra vai para a **grade de saída** da fábrica (o quadrado de borda amarela no piso da fábrica; 1 pilha = 20). A luz "produzindo" da fábrica **apaga**.
   - Antes de você colocar o P, a grade já tem 1 pilha e a luz da fábrica já está apagada (normal: ainda não havia paiol). Ao colocar o P, a grade esvazia e a luz acende; com o P cheio, a grade enche de novo e a luz apaga.

   **Antes do passo 4:** se o Paiol simples NÃO encher em 40 s, use Estoque `▲▲` nele até ficar verde e volte para `=`. Veja se agora a Arma enche pela esteira (luz verde acesa). Isso responde o item 3 mesmo assim.
4. **Ligue o botão Energia (= Atirar) da Arma** e olhe 30 s. Ela gasta 4 por segundo e a esteira repõe: a barra fica quase cheia, com as luzes **verde e laranja** acesas. **Deixe Atirar ligado.**

| Item 1 (Paiol simples) | Item 2 (Tanque de calor) | Quer dizer |
|---|---|---|
| encheu | encheu | a munição anda pela esteira: ótimo |
| NÃO encheu | encheu | a esteira do kit funciona; o que falha é a munição **entrando** na esteira pela fábrica. O item 3 diz se a **saída** (paiol → arma) funciona |
| NÃO encheu | NÃO encheu | o defeito é da esteira do kit (portas, ligações), não da munição |
| encheu | NÃO encheu | estranho: só anote |

**Se o item 1 deu "não":** daqui em diante o `▲▲` faz o papel da fábrica.
- No item 4, responda só: a grade da fábrica ficou com 1 pilha (20) e a luz dela apagou? sim/não.
- No 1B, depois de pôr o I em Peça de míssil A.E., encha-o com `▲▲` e volte para `=`. No item 5, julgue só a, c e d (o b não vale, porque você encheu o I à mão).
- No 1C, ponha o P em `▲▲` no passo 2 e deixe assim até desmontá-lo no passo 4. No 1C.5, ponha o Paiol simples novo em `▲▲` e deixe assim durante o minuto em que você olha; depois volte para `=`.

**Se o item 3 deu "não":** responda o 5 e o 8 com "-". Nesse caso, no 1C a tripulação já começa a levar munição assim que o Q aparece: é normal. Faça o 1C.4 e responda só 6 e 7.

## 1B. Dois tipos na mesma esteira (uns 3 min)

Primeiro deixe a Arma pela metade. Assim os itens (c) e (d) abaixo podem mostrar uma falha.

1. **Desligue a Fábrica F.** Atirar continua ligado.
2. No **Paiol simples**: Estoque `▼▼` até a barra ficar vazia (toda preta). Volte para `=`.
3. Espere a barra de Munição da Arma cair até mais ou menos a **metade** (~8 s). **Desligue Atirar.**
4. Troque a **Arma** para **Peça de míssil A.E.**
5. No **Paiol simples**: Estoque `▲▲` até a barra ficar verde (200). Volte para `=`.
6. Coloque **G** e **I**, cada um encostado **só** na esteira:

   ```
   . . . C . P . T . . .
   F F = = = = = = = A A
   F F . G G . I . . A A
   . . . G G . . . . . .
   ```

   - **G** = Fábrica de teste - Peça de míssil A.E. (no menu: "[TESTE] Fáb. míssil A.E."), **ligada**.
   - **I** = **[TESTE] Paiol 1x1** novo (nome exato "[TESTE] Paiol 1x1"; não é o Paiol simples nem o "Paiol 1x1 B (mecanismo B)"): Tipo **Peça de míssil A.E.**, Estoque `=`.
7. Espere **45 s**. Esperado:
   - (a) a **barra roxa** da Arma enche (20; cheia = quase branca), com a luz verde acesa;
   - (b) o **Paiol 1x1** enche até 100 (barra verde);
   - (c) o **Paiol simples** continua **verde** (200);
   - (d) a barra de **Munição** da Arma continua **na metade**.

   Se (c) ou (d) mudaram, a Arma puxou munição de canhão estando no modo míssil.

## 1C. Tripulação só como reserva (uns 6 min)

1. **Desmonte G e I.**
2. **Ligue a Fábrica F.** Troque a Arma para **Munição de canhão** e **ligue Atirar**. A barra de Munição volta a encher pela esteira.
3. Agora monte o lado da tripulação: primeiro um corredor comum (`k`) na linha logo abaixo da F e da A, encostado nas duas (4ª linha do desenho), depois um **Beliche da tripulação** (`Q`) em pé, sem girar (a porta dele fica na ponta de cima, encostada no corredor). O jogo põe as Portas sozinho. **Confira se há pelo menos 1 Porta** entre o corredor e a F, 1 entre o corredor e a A e 1 entre o corredor e o Q; ponha à mão a que faltar.

   ```
   . . . C . P . T . . .
   F F = = = = = = = A A
   F F . . . . . . . A A
   k k k k k k k k k k k
   . . . . Q . . . . . .
   . . . . Q . . . . . .
   ```

   - Nada da nave principal encosta no k nem no Q, nem Blindagem (veja o começo da Parte 1).
   - No Criativo a tripulação aparece sozinha no beliche. Se ninguém aparecer, use o botão "Contratar N tripulantes" do editor da nave (dica: "Contrata tripulantes para preencher as camas vazias").
   - O botão **"Abastecer automaticamente"** em cima da grade da fábrica tem que estar **ligado** (é o normal).
   - Olhe uns 20 s: com o paiol no lugar, ninguém deve levar munição para a Arma.
4. **Desmonte o Paiol simples (P).**
   - A Arma para de receber pela esteira (**luz verde apaga**) e a barra desce, porque ela continua atirando.
   - A munição da fábrica fica na grade de saída.
   - Quando a barra da Arma chega **na metade**, um tripulante pega munição na grade da fábrica e leva para a Arma. A barra sobe com a **luz verde APAGADA**: foi a tripulação, não a esteira. A grade esvazia e a luz da fábrica volta a acender.
   - **Olhe mais 1 minuto.** Depois que a barra sobe, ninguém sai para buscar munição de novo até ela descer outra vez até a metade. Uma segunda entrega pequena logo depois da primeira é o resto do mesmo pedido (a grade só tem 20 por vez) e conta como a mesma entrega. Se a tripulação traz munição com a barra acima da metade sem ter havido entrega logo antes, a regra da metade não funcionou.
   - Se a Arma continuar recebendo pela esteira sem o paiol (luz verde acesa), anote no item 6: quer dizer que a fábrica manda direto para a arma.
5. **Coloque um Paiol simples NOVO** no lugar do P (Estoque `=`).
   - O paiol enche e a **luz verde da Arma volta a acender**.
   - **Olhe 1 minuto:** nenhum tripulante leva munição para a Arma. No máximo, chega uma entrega que já estava a caminho.

## Respostas da Parte 1

1. (1A) O **Paiol simples** encheu só com fábrica + esteira, sem tripulação? sim/não (ou "travou")
2. (1A) **Controle:** o Tanque de calor encheu pela esteira? sim/não
3. (1A) A Arma encheu pela esteira (luz verde) e, atirando, ficou quase cheia? sim/não
4. (1A) Ao colocar o P, a grade da fábrica esvaziou e, com o P cheio, encheu de novo e a luz dela apagou? sim/não
5. (1B) Dois tipos: aconteceram as 4 coisas (a, b, c, d)? sim/não (se não, diga quais letras falharam)
6. (1C) Sem o paiol, a tripulação levou munição da grade da fábrica para a Arma, com a luz verde apagada? sim/não
7. (1C) Sem o paiol, a tripulação só voltou a buscar munição depois que a barra desceu de novo até a metade (uma entrega extra logo em seguida não conta)? sim/não
8. (1C) Com o paiol de volta, a tripulação parou de levar munição para a Arma por 1 minuto? sim/não

**Se der tempo só para isto, pare aqui e mande as 8 respostas** (veja "O que me mandar").

---

# Parte 2 - Testes extras (opcionais)

Monte cada teste em outro lugar, com pelo menos 1 bloco vazio de qualquer peça da Parte 1 (ou desmonte a Parte 1). Faça só os que quiser.

**Interior:** para ler um contador ou medidor, **esconda o interior da nave** (o mesmo botão da Parte 1). Para ver luzes, tripulação ou cartuchos embaixo do piso, mostre o interior de novo.

## 2A. Contador (uns 4 min)

1. **SALVE O JOGO.** É a primeira vez que um contador muda de número. Se travar, veja "Se der erro".
2. Coloque um **Paiol 2x2 (com contador) novo**, encostado na nave só por Blindagem, sem esteira e sem nenhuma peça [TESTE] encostada. Tipo **Munição de canhão**. Esconda o interior da nave.
3. `▼▼` até **0000**. Depois `+1`: ele conta 0001, 0002... Preste atenção em **0007**, **0009 → 0010** e **0019 → 0020**. Volte para `=`.
4. `▲▲` → esperado **1839**, barra **verde**. Volte para `=`.
5. Troque o Tipo para **Peça de míssil A.E.** e use `▲▲` → **0459**, barra verde. Volte para `=`.
6. Coloque um **Paiol 3x3 (com contador) novo**, também encostado na nave só por Blindagem, sem esteira e sem nenhuma peça [TESTE] encostada, **longe do 2x2** (pelo menos 1 bloco vazio entre os dois). Se encostar, o 2x2 manda para ele a munição de canhão que ficou guardada.
   - Tipo **Munição de canhão**, `▲▲` → **4680**, barra verde. Volte para `=`.
   - Se ele vier no Tipo Peça de míssil, o `▲▲` mostra 1170. Isso não é erro do contador.
7. Confira se a **barra** e o **medidor do teto** acompanham o número.
8. **Painel de recursos:** em Configurações → Jogabilidade → **Contagem de recursos**, escolha **Todos**. No canto de cima à direita, embaixo dos créditos, aparece a Munição da nave. Ela conta a munição dos paióis? Quanto mostra?

Se algum número sair errado, **anote exatamente o que apareceu**. Exemplo: "no lugar de 0010 apareceu 0009" ou "a unidade ficou sempre em 0".

Respostas:

9. Contagem lenta: 0007, 0010 e 0020 apareceram certos? sim/não (se não, o que apareceu)
10. 2x2 = 1839, 2x2 em míssil = 0459 e 3x3 = 4680, com as três barras verdes? sim/não (se não, os números e "barra amarela")
11. A barra e o medidor do teto acompanharam o número? sim/não
12. O painel de recursos conta a munição dos paióis? sim/não. Quanto mostrou?

## 2B. Explosão (uns 6 min)

Faça numa **nave separada**, longe da principal (como no teste anterior):

```
B B B B B B
B k k k k B
B k E E k B
B k E E k B
B k k k k B
B B B B B B
```

- `B` = **Blindagem** (20 blocos; aguenta bastante).
- `k` = **corredor comum** (12 blocos; quebra fácil, então mostra até explosão pequena).
- `E` = o paiol testado (2x2), no meio.
- O botão Detonar funciona sem ponte. **Se ele estiver cinza**, ponha nessa nave uma Cabine, um Beliche da tripulação e um Núcleo de reator pequeno, com as Portas até o corredor.
- **Monte o anel SEM o paiol e SALVE O JOGO.** Antes de cada detonação, **carregue esse save**, coloque o paiol do teste no meio, encha e detone.

Seis detonações:

1. **Paiol de explosão 2x2 VAZIO** → Detonar. É a base: só a peça estoura.
2. **Paiol de explosão com 20** (1 pilha): `+1` por 20 s até o contador mostrar **0020**, volte para `=` → Detonar.
3. **Paiol de explosão CHEIO**: `▲▲` até **1839** (barra verde), volte para `=` → Detonar.
4. **Paiol de explosão (solta a munição) com ~20**: este não tem contador. Use `+1` por **20 s no relógio**, volte para `=` → Detonar.
5. **Paiol de explosão (solta a munição) CHEIO**: `▲▲` até a barra ficar verde, volte para `=` → Detonar.
6. **Paiol 2x2 (com contador)** normal, cheio de Munição (`▲▲` até 1839, `=`) → Detonar. Este tem a explosão própria do paiol (grande, raio ~4), para comparar.

Em cada detonação, anote três coisas:
- quantos **corredores** sumiram (de 12);
- quantas **blindagens** sumiram (de 20);
- se viu **fogo** nas peças em volta, ou a vida delas baixar (passe o mouse).

Por que o fogo importa: 1 pilha de 20 munições explode com pouco dano, espalhado num raio de 3. Pode não quebrar nada, mas a munição põe fogo.

Como ler:
- **Os dois Paióis de explosão iguais ao vazio** (nada quebrou, sem fogo) → a munição guardada não explode.
- **Só o que solta a munição** quebra ou pega fogo → a munição só explode quando a peça a solta (as armas do Bullet Strike soltam).
- **Com 20: fogo ou poucos corredores; cheio: muito mais** (blindagem some) → a explosão cresce com o estoque.
- **Fogo, mas 20 e cheio parecidos** → explode pouco e não cresce.

Respostas (em 14 a 19: corredores sumidos / blindagens sumidas / fogo sim ou não):

13. O botão Detonar funcionou na nave sem ponte? sim/não (precisou da Cabine?)
14. Paiol de explosão VAZIO:
15. Paiol de explosão com 0020:
16. Paiol de explosão CHEIO (1839):
17. Paiol de explosão (solta a munição) com ~20:
18. Paiol de explosão (solta a munição) CHEIO:
19. Paiol 2x2 cheio (com explosão própria):

## 2C. Esteiras, corredor com esteira e tremonha (uns 6 min)

**Antes de tudo:** os cartuchos só andam quando algum **paiol da esteira enche ou esvazia**. Num paiol cheio nada corre. Por isso, aqui, **use paiol vazio** (um novo, ou `▼▼` e depois `=`).

1. **Formas:** faça retas, curvas, um T e um cruzamento de Esteira de munição entre uma Fábrica de teste - Munição e um **paiol vazio**. A esteira deve mudar de desenho sozinha conforme os vizinhos.
2. **Cartuchos:** andam enquanto algum paiol da esteira enche ou esvazia (inclusive pelos botões `▲▲` e `▼▼`) e param ~1 s depois.
3. **Calor separado:** encoste um **Termoduto** e um **Radiador** do jogo na esteira.
   - Esperado: **não ligam** (o desenho da esteira não muda).
   - No editor, onde o jogo mostra as portas e linhas de calor (por exemplo, com o Termoduto selecionado para construir):
     - nas portas de esteira das peças do kit aparece um **quadradinho verde com um rasgo no meio**;
     - em cima da esteira aparece **só uma linha verde**, diferente da linha amarela do calor;
     - as duas linhas nunca se ligam.
   - Com a pasta `_SemIcone`, o ícone e a linha são os do calor. Aí responda o item 23 só com "não se liga no calor".
4. **Corredor com esteira:** coloque-o no caminho da tripulação (o melhor é ser a única passagem entre os alojamentos e o resto da nave) e, ao mesmo tempo, na linha da esteira, entre a fábrica e um **paiol vazio**:

   ```
   . . . Q Q . . .     Q = Alojamentos da tripulação
   . . . Q Q . . .
   F F = C = = P .     C = Corredor com esteira, no meio da esteira; P = paiol VAZIO
   F F . k . . . .     k = corredor comum, levando ao resto da nave
   . . . k . . . .
   ```

   - Gire os Alojamentos até o lado da porta ficar para baixo, virado para o C (eles só aceitam porta de um lado), e ponha uma **Porta** entre os Alojamentos e o C (confira se o jogo já não pôs).

   Esperado: (a) a tripulação passa por cima; (b) com o interior da nave à mostra, os cartuchos andam embaixo da grade do piso; (c) o paiol enche com o corredor no meio.
5. **Tremonha (H):**

   ```
   F F k k H = = P     F = Fábrica de teste - Munição SEM esteira encostada
   F F k . . . . .     H = Tremonha (Tipo Munição); P = paiol VAZIO no Tipo Munição
   . . k . . . . .     k = corredor comum até os alojamentos
   ```

   - A Tremonha é uma sala. Confira se há uma **Porta entre o corredor e a Tremonha** e outra **entre o corredor e a fábrica** (ponha à mão a que faltar). A esteira sai de **outro lado** da Tremonha.
   - A fábrica fica **sem esteira e sem encostar na Tremonha**, então a munição dela vai toda para a grade.
   - Esperado: a tripulação leva munição da grade da fábrica (ou de uma Baia de armazenamento) para a Tremonha. A Tremonha manda pela esteira e o paiol enche. A grade esvazia e a fábrica volta a produzir.

Respostas:

20. A esteira muda de forma sozinha (reta, curva, T, cruz)? sim/não
21. Os cartuchos andam enquanto algum paiol enche ou esvazia e param ~1 s depois? sim/não
22. O Termoduto e o Radiador encostados NÃO se ligam na esteira? sim/não
23. No editor: quadradinho verde nas portas e só a linha verde em cima da esteira, separada da amarela do calor? sim/não
24. Corredor com esteira: a tripulação passou por cima? sim/não
25. Corredor com esteira: com o interior à mostra, os cartuchos andam embaixo da grade? sim/não
26. Corredor com esteira: o paiol encheu com o corredor no meio? sim/não
27. Tremonha: a tripulação levou munição para ela e o paiol encheu pela esteira? sim/não

## 2D. Troca de tipo (uns 8 min)

### Seletor: o tipo desmarcado sai mesmo da esteira? (sem contador)

Monte numa **esteira separada**, sem fábrica e sem outro paiol, encostada na nave só por Blindagem e sem nenhuma outra peça [TESTE] encostada. Mostre o interior da nave (para ver a luz verde da Arma):

```
X = = . A A      . = lugar do ÚLTIMO bloco de esteira (coloque só no passo 4)
. . . . A A
```

1. **X = Paiol 1x1 novo** (mecanismo A). Tipo Munição → Estoque `▲▲` até a barra ficar verde (400) → **volte para `=`**.
2. Troque X para **Peça de míssil A.E.** A barra de X fica vazia, porque agora mostra peças de míssil e ele tem 0 delas. A munição de canhão continua guardada dentro dele.
3. Coloque uma **Arma de teste NOVA** (Tipo Munição, Atirar/Energia desligado) a 1 bloco da esteira, presa à nave por Blindagem, ainda sem encostar na esteira. A barra de Munição dela tem que estar vazia.
4. Coloque o **último bloco de esteira**, ligando X à Arma. Espere 15 s.
   - **Esperado: a Arma NÃO recebe nada** (barra vazia, luz verde apagada).
   - Se ela encher **com a luz verde acesa**, o tipo desmarcado continuou na esteira: o mecanismo falhou.
5. **Controle:** volte X para **Munição**. Agora a Arma **deve encher** (luz verde acesa). Isso prova que a esteira estava ligada.
6. **Desmonte X, a Arma e o último bloco de esteira.** Repita os passos 1 a 5 com **X = Paiol 1x1 B novo** (faixas azuis no teto; mecanismo B) e outra **Arma nova**.

### Expulsão: o tipo antigo vai para outro paiol? (usa o contador)

Estes números testam a **expulsão** (o tipo antigo saindo pela esteira para outro paiol). Quem decide se o seletor funciona é o teste de cima (itens 28 a 31).

Use **paióis NOVOS** (vazios), numa **esteira separada**, sem fábrica e sem arma, presa à nave só por Blindagem. Os paióis do 2A guardam o outro tipo, e ele seria expulso para cá. Esconda o interior da nave (para ler o contador).

```
1 = = 2 2 = = 3 3 3
. . . 2 2 . . 3 3 3
. . . . . . . 3 3 3
```

- 1 = Paiol 1x1; 2 = Paiol 2x2 (com contador); 3 = Paiol 3x3 (com contador; **coloque SÓ no passo 4**). Todos no Tipo Munição, Estoque `=`.

1. **Paiol 1x1**: Estoque `▲▲` até encher (400, barra verde). **Volte para `=`.**
2. **Paiol 2x2**: `▼▼` até **0000**. **Volte para `=`.**
3. Troque o **1x1 para Peça de míssil A.E.**
   - Esperado: o contador do **2x2 sobe para 0400** em ~4 s.
   - O 1x1 fica com a barra vazia (0 peças de míssil). Nada foi convertido.
4. **Agora coloque o Paiol 3x3** na ponta da esteira (confira: Tipo Munição, Estoque `=`) e faça, nesta ordem:
   1. 3x3: Estoque `▲▲` até **4680**.
   2. **VOLTE O ESTOQUE DO 3x3 PARA `=`.**
   3. Troque o **3x3 para Peça de míssil A.E.**
   4. Espere o 2x2 mostrar **1839**.
   5. Volte o 3x3 para **Munição**: ele deve mostrar **3241** (= 4680 − 1439 que couberam no 2x2).
   - Se aparecer **2841**, o 1x1 aceitou munição mesmo estando em Peça de míssil. Anote o número que aparecer.

Respostas:

28. Seletor A (Paiol 1x1 em Peça de míssil): a Arma ficou vazia? sim/não
29. Seletor A: ao voltar o 1x1 para Munição, a Arma encheu? sim/não
30. Seletor B (Paiol 1x1 B em Peça de míssil): a Arma ficou vazia? sim/não
31. Seletor B: ao voltar o 1x1 B para Munição, a Arma encheu? sim/não
32. Expulsão no 1x1: o 2x2 foi para 0400? sim/não (qual número?)
33. Depois da troca, o 1x1 ficou com a barra vazia (nada virou outro tipo)? sim/não
34. Expulsão no 3x3: o 2x2 chegou a 1839 e o 3x3 voltou mostrando 3241? sim/não (qual número?)

## 2E. Junto com os outros mods (1 min)

Ative **Bullet Strike + Star Wars: A Cosmos Divided + o kit** e reinicie.

35. O jogo abriu sem erro, e as abas e peças não se misturaram? sim/não

---

# Parte 3 - Railgun Tupã (opcional, uns 12 min)

**Use o "Tupã - Carregador (railgun)"**, que tem contador. O **"Tupã - Carregador sem contador (reserva)"** é só para o caso de "Se der erro".

**SALVE O JOGO antes de montar.** O contador da bateria do Carregador muda de número assim que ela começa a encher.

**Monte primeiro com Canos B** (faixa azul no teto). Todas as peças viradas para o mesmo lado (boca para cima), alinhadas pelas laterais:

```
      P P P   <- Ponta (3x4)
      P P P
      P P P
      P P P
      B B B   <- Cano B (3x3)
      B B B
      B B B
      B B B   <- Cano B (3x3)
      B B B
      B B B
      L L L   <- Carregador (3x4), 2 tripulantes
      L L L
      L L L
    = L L L =  <- esteira opcional, só nos 2 CANTOS de trás
```

Precisa de:
- Uma nave com **Sala de controle (ou Cabine), alojamentos e Núcleo de reator** funcionando. O Carregador e a Ponta usam pontos de comando.
- **2 tripulantes** chegando ao Carregador por Porta (as portas dele ficam nas laterais e no meio de trás).
- **Munição:** a tripulação pega na grade de uma **Fábrica de teste - Munição sem esteira**, ligada ao Carregador por corredor e Porta.
- **Energia:** no Carregador, deixe o botão **Bateria** em **"encher já"** nos passos 1 a 4. É energia infinita: o Tupã não precisa de reator para estes passos.
- **Um alvo:** uma nave inimiga, como no teste anterior. **O Tupã é fixo e só mira ±45° para a frente: deixe o alvo na frente da boca.** A Ponta atira sozinha no alvo a cada 6 s. Para parar, desligue a Ponta (botão Energia).
- **Interior escondido** para ler o contador da bateria (ele fica no teto).

O botão **Bateria** do Carregador tem 3 posições:
- **normal**: a tripulação recarrega com energia do reator;
- **encher já**: enche sozinho, 6000 em ~6 s, sem tripulação;
- **travada**: ninguém recarrega.

1. **Bônus no editor.** A Ponta mostra o bônus por número de canos:

   | Canos | Bônus |
   |---|---|
   | 1 | +25% |
   | 2 | +45% |
   | 3 | +64% |
   | 4 | +81% |
   | 5 | +98% |
   | 6 | +115% |

   Com 0 ou 7 canos aparece o ícone de **peça faltando** e ela não atira.
2. **Disparo** (com 2 Canos B, depois com 4). Mande a Ponta atacar o alvo. Esperado:
   - som de carga e **brilho correndo do carregador até a boca**: **~1,5 s com 2 canos e ~2 s com 4**;
   - depois o **projétil aparece deslizando** pelo canal aberto do cano;
   - por fim, o tiro sai.
3. **Isolamento** (de frente, que é como as peças se encadeiam):
   - (a) Monte **Carregador Tupã + Acelerador de canhão eletromagnético do jogo + Ponta Tupã** (o Acelerador no lugar dos canos; encoste a traseira da Ponta na frente do Acelerador, o mais centralizado possível). Esperado: a Ponta mostra **peça faltando** e nenhum bônus.
   - (b) Monte **Carregador Tupã + Cano B** e encoste um **Lançador de canhão eletromagnético do jogo** na frente do Cano. Esperado: o Lançador do jogo mostra **peça faltando** e não atira.
4. **Esteira no Carregador:**
   - Use um **Carregador recém-colocado** (grade de munição vazia). Pode ficar sem canos e sem ponta.
   - Logo depois de colocar, clique no botão **"Entregar automaticamente"** em cima da grade de munição dele para **DESLIGAR** a entrega da tripulação.
   - Ligue um **Paiol simples cheio** (`▲▲`, depois `=`) com esteira até um **canto de trás** do Carregador.
   - Esperado: a grade enche assim mesmo, só pela esteira, e a barra do Paiol simples desce um pouco.
5. **Recarga pela tripulação:** com um Núcleo de reator pequeno na nave, ponha o botão Bateria em **normal** e deixe a Ponta atirar uns 30 s. Esperado: depois dos tiros, um tripulante traz energia do reator para o Carregador e o contador sobe de novo (em saltos, não aos pouquinhos).
6. **Energia com 2 Canos B** (o teste que importa nesta parte):
   1. **Desligue a Ponta** (botão Energia). **SALVE O JOGO.** Volte para 2 Canos B.
   2. Bateria → **encher já**. Espere o contador mostrar **6000** (barra verde).
   3. Bateria → **travada**. Agora ninguém recarrega.
   4. Ligue a Ponta, com o alvo na frente. Anote o número **antes e logo depois de cada tiro** e **quantos tiros saem** até a Ponta parar (espere uns 15 s sem tiro para ter certeza).
   5. Desligue a Ponta.

   Leitura (vale sozinha, sem comparar com nada):

   | Com a bateria travada, começando em 6000 | Quer dizer |
   |---|---|
   | **6000 → 3000 → 0000, 2 tiros.** Cada tiro tira 3000 = 2000 da Ponta + 500 × 2 canos | os canos cobram a energia: **funciona** |
   | **6000 → 4000 → 2000 → 0000, 3 tiros.** Cada tiro tira só 2000 | os canos **não** cobram: **falha** |
   | outra coisa | anote os números |

   Regra geral, para qualquer número de canos: quando funciona, cada tiro tira **2000 + 500 × canos** (1 cano: 2500; 2: 3000; 4: 4000); quando falha, cada tiro tira **só 2000**. Começando em 6000, de 1 a 4 canos: funciona = **2 tiros**; falha = **3 tiros**.

7. **Energia com 2 Canos A:** **SALVE O JOGO.** Troque os dois Canos B por **2 Canos A** e repita o passo 6 (do 2 ao 5). Use a **mesma tabela**.
   - Julgue cada tipo de cano pela tabela, não pela comparação: se os dois falharem, os dois dão 3 tiros.
   - **Se o jogo travar ao colocar o Cano A**, carregue o save e responda o item 45 com "travou".
   - Os números do contador só valem se os itens 9 e 10 deram certo. Se não, use só a quantidade de tiros: 2 = funciona, 3 = falha.

Respostas:

36. O bônus da Ponta bateu com a tabela, e com 0 ou 7 canos apareceu "peça faltando"? sim/não
37. Brilho de carga correndo até a boca + som antes do tiro? sim/não
38. A carga demorou ~1,5 s com 2 canos e ~2 s com 4? sim/não
39. O projétil apareceu deslizando no cano? sim/não
40. Isolamento (a): com o Acelerador do jogo no lugar dos canos, a Ponta Tupã mostrou "peça faltando"? sim/não
41. Isolamento (b): o Lançador do jogo na frente do Cano Tupã não funcionou? sim/não
42. O Carregador recebeu munição pela esteira com "Entregar automaticamente" desligado? sim/não
43. Com a Bateria em normal, a tripulação trouxe energia do reator? sim/não
44. Energia com 2 Canos B: quais números apareceram e quantos tiros saíram?
45. Energia com 2 Canos A: quais números apareceram e quantos tiros saíram? (ou "travou ao colocar")
46. Qual Carregador você usou: o normal (com contador) ou o sem contador?

---

# Se der erro

- **O jogo não abre, ou mostra erro ao carregar:** mande o print e o log (veja "Se o jogo travar: o que mandar", no começo) e diga em qual passo estava.
- **A mensagem cita `part_networks`, `OverlayIcons`, `RouteLines`, `BS2TPortaEsteira` ou `BS2TEsteira`:** é o ícone e a linha próprios da esteira no editor.
  - Feche o jogo.
  - **Apague a pasta `BulletStrike_Teste2`** da pasta Mods.
  - **Copie a `BulletStrike_Teste2_SemIcone` no lugar.** Ela tem o mesmo ID, e o jogo continua vendo o mesmo mod.
  - A única diferença: no editor a esteira usa o ícone e a linha amarela do calor (ela continua sem se ligar no calor). O resto do roteiro vale igual; no item 23, responda só "não se liga no calor".
- **O jogo travou durante o 1A** (ao colocar as peças ou quando a munição começou a andar): carregue o save do passo 1A.1, responda o item 1 com "travou" e mande o log. Esse já é o resultado mais importante. Se der tempo, monte só C + 3 blocos de esteira + T (`C = = = T`, sem F, P e A, preso à nave por Blindagem) e responda o item 2: isso separa "munição" de "esteira".
- **O jogo travou quando o número de um CONTADOR mudou** (Paiol 2x2, Paiol 3x3, Paiol de explosão ou a bateria do Carregador normal): é o contador. Carregue o último save, me avise e siga só com peças **sem contador** (Paiol simples, Paiol 1x1, Paiol 1x1 B, Paiol de explosão que solta a munição, Tanque de calor):
  - **2A:** pule os itens **9 e 10**. Nos itens 11 e 12, use o Paiol 1x1.
  - **2B, explosão:** coloque o paiol 1x1 no **bloco de cima à esquerda** do buraco 2x2 do anel e deixe os outros 3 blocos do buraco vazios.
    - Itens 14 a 16: use o **Paiol simples** (ele também não tem explosão própria nem solta a munição): vazio, com ~20 (`+1` por 20 s no relógio) e cheio (200).
    - Itens 17 e 18: o Paiol de explosão que solta a munição, normal (ele não tem contador).
    - Item 19: use o **Paiol 1x1 cheio** de Munição (400; tem explosão própria).
  - **2D, expulsão sem contador (itens 32 a 34):** monte numa esteira um **Paiol 1x1 cheio** (Munição, `▲▲` até 400 e depois `=`) e um **Paiol simples VAZIO**. Troque o 1x1 para **Peça de míssil A.E.**:
    - o Paiol simples fica verde (200) e a barra do 1x1 fica vazia;
    - volte o 1x1 para **Munição**: a barra dele fica pela metade (200 de 400).
    - No item 32, responda "o Paiol simples ficou verde? sim/não". No 33, se a barra do 1x1 ficou vazia e depois pela metade. Pule o 34.
    - O seletor (itens 28 a 31) não usa contador: faça normal.
  - **Parte 3:** use o **"Tupã - Carregador sem contador (reserva)"** do começo ao fim. No passo 6, em vez dos números: Bateria em **encher já** até a barra ficar verde, depois **travada**, e **conte os tiros** até a Ponta parar. Itens 44 e 45 = número de tiros (2 = funciona; 3 = falha).
- **O jogo travou ao colocar um Cano A:** carregue o save e use só **Canos B**. No item 45, responda "travou". É justamente o ponto que eu não consegui comprovar.

---

# O que me mandar

1. **Uma linha com as respostas**, no formato número-resposta. A Parte 1 é a que importa:

   `1-sim 2-sim 3-sim 4-sim 5-sim 6-sim 7-sim 8-sim`

   Se fez as Partes 2 e 3, continue na mesma linha, com os números onde o item pede. Exemplo: `9-sim 10-não(1839/0459/4679, barra amarela no 3x3) 14-0/0/não ... 44-6000/3000/0000, 2 tiros`.
2. Qual pasta você usou (`BulletStrike_Teste2` ou `_SemIcone`) e se a Parte 1 foi feita **sem** outros mods.
3. Se algo travou: o print, o **log** e o passo em que estava.
4. Prints são bem-vindos, mas não são obrigatórios.
