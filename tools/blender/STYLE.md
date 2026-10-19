# Bullet Strike: estilo da arte 3D e contrato dos modelos

Este guia vale para todo sprite 3D do mod. O modelo de referência é o **Canhão Naval Automático 76 mm**
(`tools/blender/parts/bs_naval_76.py`), que o usuário aprovou com as palavras "exatamente o estilo que eu quero para
as armas do mod". Toda arma nova precisa parecer da mesma família.

Referências renderizadas (abra antes de começar):
- `docs/preview/3d/naval76_ampliado.png` (vista de cima, 4x)
- `docs/preview/3d/naval76_no_jogo.png` (escala do jogo, 1x e 3x)
- `docs/preview/3d/naval76_disparo.gif` (animação de disparo)
- `docs/preview/3d/naval76_perspectiva.png` (vista 3/4 do modelo)

Leitura de apoio: o estudo de estilo do mod "Redline Orbital Heavy Industries", que o usuário pediu para seguir, e as
notas sobre as convenções gráficas do jogo foram feitos na fase de pesquisa e **não estão no repositório**. O que
importa deles está resumido nas seções 1 e 2 abaixo.

---

## 1. Linguagem visual (obrigatória)

1. **Núcleo escuro e blindagem clara.** Cada cabeça de torre é um núcleo mecânico quase preto (`M["core"]`,
   `M["core_mid"]`) envolto em placas de blindagem cinza-claras separadas (`M["armor"]`). Entre as placas correm
   frestas escuras de 0,05 a 0,15 quadro. A cabeça deve parecer um exoesqueleto, não uma caixa.
2. **Angular, facetada, agressiva.** As silhuetas são octógonos chanfrados e cunhas apontando para a frente, com
   recortes em degrau. Evite círculos perfeitos na camada do teto; o anel da torre é a única exceção. Use
   `B.shard()` (placa chanfrada com um painel interno elevado, o chanfro duplo) em toda peça de blindagem.
3. **Simetria espelhada** ao longo do eixo do cano. A assimetria só pode vir de detalhes pequenos (por exemplo uma
   caixa de munição de um lado, se a direção de arte pedir).
4. **Elementos recorrentes** que dão identidade à família. Adapte-os ao tamanho de cada arma:
   - "garras" ou "lâminas" inclinadas para a frente que seguram a raiz dos canos;
   - uma espinha central elevada com uma janela de sensor (recesso escuro com uma fenda pequena acesa);
   - um compartimento de ventilação traseiro (recesso escuro, venezianas, uma fileira de 3 a 6 luzes âmbar);
   - detalhes mecânicos **só nas frestas escuras do núcleo**: tambores de munição com contadores acesos, calhas de
     alimentação, pistões, cabos e módulos;
   - linhas de painel cortadas na blindagem (`B.cut` com caixas finas) e fendas de LED cortadas na blindagem
     (`Mo.slot_with_pips`).
5. **Canos** são luvas longas e facetadas (cilindros de 8 lados, sombreamento plano) com um canal escuro cortado
   por cima, 2 a 3 colares e um freio de boca ou supressor de clarão. A raiz fica num berço ou mantelete escuro. Uma
   arma rotativa tem um feixe de canos com um anel de fixação na frente.
6. **Emissivos pequenos e raros.** A área acesa deve ficar abaixo de 1 a 2% do sprite. Os LEDs ficam em
   **recessos escuros**, nunca direto sobre a blindagem branca. Use `M["glow"]` (forte), `M["glow_dim"]` (suave) e
   `M["ember"]` (calor, bem fraco). Nada de logotipos, textos grandes ou faixas de perigo na torre (só os projéteis
   nucleares têm uma exceção, seção 11.6).
7. **Acabamento limpo de fábrica.** Sem ferrugem e sem sujeira visível. Desgaste e sujeira vêm só dos materiais de
   `Mo.mats()`.
8. **Densidade de detalhes.** A 64 px/quadro deve haver uma quebra estrutural (fresta, degrau, ranhura ou fenda) a
   cada 0,3 a 0,5 quadro. Nenhuma área plana maior que cerca de 1x1 quadro sem ranhura ou rebaixo.
9. **Escala com o tamanho.** Armas pequenas (1x1, 1x2, 2x2) são compactas, com 1 ou 2 camadas de placas e formas
   grandes e legíveis, porque o detalhe some a 64 px. Armas grandes (4x5 para cima) ganham mais camadas de placas,
   mais módulos no núcleo e mais LEDs, mas mantêm os mesmos tipos de forma.

### Cores e destaques
- Use **só** a paleta de `Mo.mats(accent)`: blindagem cinza-naval clara, núcleo escuro, aço. Ignore as cores
  listadas no `art_direction` do spec (oliva, vermelho-ferrugem, areia etc.). O usuário aprovou um visual único
  para a família. Do `art_direction` tire só **a silhueta, a quantidade e o estilo dos canos e as animações**.
- Cor de destaque (cor das luzes) por arma: `"amber"` por padrão; `"cyan"` nas armas de plasma (Boitatá, Curupira);
  `"green"` no obuseiro nuclear (Boiúna). Uma luz pequena de radar vermelha (`M["red"]`) é permitida na CIWS.
- O teto do casco é **verde puro** (`B.mat_roof_green()`); o jogo troca o verde pela pintura da nave. O que não deve
  ser pintado (ventilações, escotilhas, metal) usa materiais que não são verdes.

## 2. Coordenadas e convenções

- 1 unidade do Blender = 1 quadro = 64 px. A câmera olha direto para baixo.
- **Cabeça e cano:** origem no pivô da torre, **+X = direita, +Y = frente (direção do cano), +Z = para cima**.
  O cano é modelado com a **raiz em y = 0** e a boca em y = L, centrado em x = 0 (altura z ≈ 0,4 a 0,6).
- **Teto e chão:** coordenadas centradas na peça (x em [-w/2, w/2], y em [-h/2, h/2], +Y = frente da peça). O pivô
  em coordenadas da peça (x para a direita, y **para baixo**) é convertido com `px = pivot[0] - w/2`,
  `py = h/2 - pivot[1]`.
- O sprite da torre é um quadrado de lado `turret_box` centrado no pivô. **A cabeça inteira precisa caber nesse
  quadrado** (deixe uma margem de uns 0,03).
- O sprite do cano vai de `-pad` até `L` (pad = espaço do recuo) e tem largura `width`. O cano inteiro, inclusive o
  freio de boca, precisa caber nessa largura.
- **Sobreposição torre/cano:** dentro da mesma camada o jogo não garante a ordem de desenho. Onde a raiz do cano
  cobre a cabeça (o berço/mantelete), faça ficar certo **tanto com o cano por cima da cabeça quanto por baixo**.
  Deixe essa região escura (core_mid/core) e não deixe o cano cobrir blindagem branca.

## 3. Contrato do modelo (`tools/blender/parts/<id_curto>.py`)

```python
import bs3d as B
import models as Mo

PART = {
    "id": "rafaeltessaro.bs_xxx",
    "kind": "gun",                     # torres de convés (armas e defesas)
    "size": [w, h],                    # PRECISA bater com o spec (tools/spec/bullet_strike_spec.json)
    "pivot": [x, y],                   # coordenadas da peça (x para a direita, y para baixo), em quadros
    "turret_box": 2.9,                 # lado do sprite da torre
    "ring_r": 1.3,                     # raio do anel da torre desenhado no teto/chão
    "accent": "amber",
    "collider": 1.3,                   # opcional: raio de colisão da torre (padrão 0,45 * box)
    "barrels": {
        "ys": [0.0],                   # deslocamento lateral de cada cano VISÍVEL (+ = direita). A QUANTIDADE é fixa por arma (tabela abaixo)
        "root": 0.88,                  # distância pivô -> raiz do cano
        "length": 2.6,                 # raiz -> boca
        "width": 0.46,                 # largura do sprite do cano (quadros)
        "pad": 0.30,                   # espaço do recuo atrás da raiz
        "anim": "recoil",              # "recoil" | "spin" | "static"
        "recoil": [0.26, 0.18, 0.10, 0.04],   # recuo por quadro de animação (quadros), o primeiro = disparo
        "heat": [1.0, 0.9, 0.78, 0.64, 0.5, 0.36, 0.22, 0.1],  # brilho de calor por quadro (esfria depois)
        "interval": 0.06,              # segundos por quadro de animação
        "heat_color": (1.0, 0.13, 0.015),  # opcional: cor do calor (plasma: (0.25, 0.85, 1.0) ciano)
        # com anim == "spin": "spin_frames": 3 (barrel(M, L, T, phase) com phase em [0,1) = fração do
        # ângulo entre dois canos; o renderizador pede as fases 1/4, 2/4, 3/4 e 0 para o repouso)
    },
    "turret_anim": {"frames": 8, "interval": 0.1},   # opcional: animação em laço da cabeça (radar, luzes)
    "lights": [{"at": [x, y], "size": 1.4, "color": [255, 120, 30], "z": 0.8}],  # luzes dinâmicas (coordenadas da cabeça)
    "preview_pattern": "single",       # prévia em GIF: single | alternate | pairs | volley | rotary
    "preview_fx": "fire",              # opcional: "plasma" = clarão ciano e sem fumaça (padrão pela cor de destaque)
}

def head(M, T="head", phase=0.0): ...        # cabeça da torre; phase em [0,1) quando existe turret_anim
def barrel(M, L, T="barrel", phase=0.0): ... # UM cano (ou o feixe rotativo); raiz em y=0
def roof(M, T="roof"): ...                   # opcional (padrão: Mo.hull_roof)
def floor(M, T="floor"): ...                 # opcional (padrão: Mo.hull_floor, com assentos da tripulação)
```

Regras:
- Todo objeto renderizado recebe a etiqueta passada em `T` (`tags=(T,)`). As partes do cano que devem brilhar quando
  quentes (luva, freio, colares) recebem `tags=(T, "hot")`.
- **Nunca** dê etiquetas aos cortadores booleanos (o `B.cut` cuida deles).
- A quantidade de canos em `ys` precisa ser igual à da tabela (senão o build falha):

| arma | tamanho | tripulação | canos visíveis (`ys`) | anim | padrão | destaque |
|---|---|---|---|---|---|---|
| bs_lmg (Marimbondo) | 1x1 | 1 | 1 | recoil | single | amber |
| bs_hmg (Mangangá) | 1x2 | 1 | 2 | recoil | alternate | amber |
| bs_autocannon_20 (Carcará) | 2x2 | 1 | 2 | recoil | alternate | amber |
| bs_flak_light (Tatu) | 2x2 | 1 | 2 | recoil | alternate | amber |
| bs_quad_hmg (Saci) | 2x2 | 2 | 4 | recoil | pairs (1+3 / 2+4) | amber |
| bs_minigun (Cigarra) | 2x3 | 2 | 1 (feixe de 6 canos) | spin | rotary | amber |
| bs_naval_76 (Tambor) | 3x4 | 3 | 1 | recoil | single | amber |
| bs_plasma_gatling (Boitatá) | 2x3 | 2 | 1 (feixe de 4 canos) | spin | rotary | cyan |
| bs_ciws (Tamanduá) | 3x3 | 2 | 1 (feixe de 4 canos) | spin | rotary | amber (+ radar vermelho) |
| bs_rotary_30 (Furacão) | 4x4 | 4 | 1 (feixe de 7 canos) | spin | rotary | amber |
| bs_naval_155 (Trovão) | 4x5 | 5 | 2 | recoil | alternate | amber |
| bs_plasma_heavy (Curupira) | 4x5 | 4 | 2 | recoil | alternate | cyan |
| bs_flak_heavy (Pororoca) | 4x4 | 4 | 2 | recoil | alternate | amber |
| bs_nuke_howitzer (Boiúna) | 5x6 | 6 | 1 | recoil | single | green |
| bs_naval_406 (Mapinguari) | 6x7 | 10 | 3 | recoil | volley | amber |

- Posicionamento: a cabeça costuma cobrir as fileiras da frente; a **fileira de trás** da peça (onde fica a
  tripulação) costuma continuar visível no teto (escotilha, ventilações). A tripulação é posicionada
  automaticamente na fileira de trás; não defina `crew_pos`.
- O recuo deve ser proporcional ao calibre: metralhadora pequena 0,04 a 0,08 quadro, autocanhão 0,1 a 0,15,
  76 mm 0,26, 155 mm 0,4, 406 mm 0,6, obuseiro 0,7. O brilho de calor combina com canhões (76 mm para cima) e com o
  plasma (brilho ciano pelos materiais `ember`/`glow_dim`). Metralhadoras leves devem usar pouco ou nenhum calor.

## 4. Comandos

Rode da raiz do repositório. `<python-com-bpy>` é um Python com o módulo `bpy` do Blender instalado (por exemplo
um venv próprio) e `<pasta Data do Cosmoteer>` é a pasta `Data` do jogo base (veja o README).

```bash
PY=<python-com-bpy>
# iteração rápida (qualidade baixa), saída numa pasta de rascunho fora de art3d/:
$PY tools/blender/render_part.py bs_xxx --quick --preview --out <pasta de rascunho>/draft_bs_xxx
#   (--only turret | barrel | hull renderiza só uma parte)
# versão final (vai para art3d/bs_xxx/, que o mod usa):
$PY tools/blender/render_part.py bs_xxx --preview
# confere se o mod gera e valida:
python3 tools/build_mod.py --no-art && python3 tools/rules_lint.py --mod BulletStrike --vanilla <pasta Data do Cosmoteer>
```

A opção `--preview` grava `preview_ingame.png` (1x e 3x) e `preview_fire.gif` na pasta de saída. **Olhe as
imagens** a cada iteração. A máquina usada tinha só 4 CPUs, então renderize a versão final uma vez só.

## 5. Lista de conferência de qualidade (critique o próprio trabalho antes de terminar)

- [ ] A 1x (64 px/quadro) a silhueta se lê bem e é diferente das outras armas (veja `art_direction`).
- [ ] Parece da família do 76 mm: núcleo escuro com placas claras e frestas, garras, espinha, compartimento de
      ventilação, LEDs em recessos.
- [ ] Parece agressiva: formas e chanfros apontando para a frente. Nada parece "caixote" ou "de brinquedo".
- [ ] Toda peça de blindagem tem chanfro duplo; há linhas de painel; nenhuma área plana grande e vazia.
- [ ] Os emissivos são pequenos; o calor é laranja (não branco); o plasma é ciano; o nuclear é verde.
- [ ] A cabeça cabe no `turret_box`; o cano cabe em `width`; nada é cortado nas bordas do sprite.
- [ ] A raiz/berço do cano fica certa nas duas ordens de desenho.
- [ ] O teto é verde com detalhes não verdes; o chão tem assentos/consoles nas posições da tripulação e
      porta-munições visíveis.
- [ ] `python3 tools/build_mod.py --no-art` e o `rules_lint` dão 0 erros.

## 6. Fábricas (`kind: "factory"`)

Referência (primeira versão, simples): `tools/blender/parts/bs_factory_mag_std.py`.

```python
PART = {"id": "rafaeltessaro.bs_factory_xxx", "kind": "factory", "size": [w, h], "accent": "amber",
        "machine_frames": 4, "machine_interval": 0.12}
def floor(M, T="floor"): ...                  # chão interno opaco (a peça inteira)
def machine(M, T="machine", phase=0.0): ...   # maquinário (quadro animado; phase em [0,1)); transparente onde vazio
def roof(M, T="roof"): ...                    # teto verde + detalhes sem pintura
```
- Coordenadas centradas na peça, +Y = frente da peça (topo da imagem), 1 unidade = 1 quadro.
- **Leiaute da grade (fixado pelas regras, `tools/bsgen/factory.py`):**
  - 2x2 (Prensa de Carregadores): fileira de cima = maquinário (bloqueado para a tripulação). Fileira de baixo:
    ENTRADA no quadro da esquerda, SAÍDA no quadro da direita.
  - 3x3 (as outras fábricas, leiaute da `factory_he` do jogo base): fileira de cima + quadro central (1,1) =
    maquinário. Quadros (0,1) à esquerda e (2,1) à direita = ENTRADAS (a 2ª entrada à direita). A fileira de baixo
    inteira (y = 2) = SAÍDA.
  - O jogo desenha as pilhas de recurso por cima dos quadros de entrada e saída (camada `doodads_low`). O chão
    deve mostrar "plataformas" marcadas ali. Deixe esses quadros livres de maquinário.
- O maquinário precisa parecer da mesma família: carcaças claras chanfradas com chanfro duplo, núcleo escuro, LEDs
  em recessos, linhas de painel. A animação precisa mostrar trabalho (pilão da prensa, esteira, rotor girando, luz
  pulsando...). Tema por fábrica: Prensa de Carregadores (empacota balas), Prensa de Carregadores Perfurantes
  (pontas de triaço), Energizador de Carregadores P.E.M. (bobinas de cobre e brilho elétrico), Fábrica de Células
  de Plasma (ciano, tanques de células), Fundição de Projéteis Nucleares (verde, célula quente com blindagem contra
  radiação).
- Destaque: âmbar (prensa padrão/perfurante), azul (P.E.M.), ciano (plasma), verde (nuclear).

## 7. Munição (`kind: "resource"`)

Referência: `tools/blender/parts/bs_mag_std.py`.

```python
PART = {"id": "rafaeltessaro.bs_xxx", "kind": "resource", "accent": "amber", "unit_scale": 0.44,
        # opcional: "stack_layout": {k: [(x, y, z), ...]}, "stack_rot": [...], "icon_scale": 0.8}
def item(M, T="item"): ...   # UMA unidade centrada na origem, cabendo em ~1x1 (z até ~0,5)
```
- O renderizador produz `stack_1..N` (N = `max_stack_size` do spec) em 64x64, o `nugget` (item solto, com
  normais), `icon.png` 64x64 e `overlay.png` (silhueta branca 128x128).
- O item precisa ser reconhecível a 64 px e a meio quadro: silhueta clara, carcaça clara + núcleo escuro e um
  detalhe próprio de cada tipo: Padrão (LEDs âmbar, latão à mostra), Perfurante/Perfurante-Explosiva (pontas de
  triaço, faixa branco-azulada), P.E.M. (bobinas/brilho azul), célula de plasma (cilindro ciano aceso), projétil
  nuclear (projétil grande, faixa verde, símbolo de radiação feito de 3 cunhas).
- Pilhas de 5 ou 6 não podem parecer um amontoado: use um arranjo organizado em 2 camadas (`stack_layout`).

## 8. Lança-mísseis (`kind: "launcher"`)

Os lança-mísseis de convés (Tocandira 2x2 no início, Caipora 3x3 no meio, Mula-sem-Cabeça 5x6 no fim) são torres
de convés como as armas, mas **não têm canos**. Um casulo giratório leva uma grade de tubos, e o jogo mostra
quantos mísseis estão carregados desenhando **imagens de sobreposição por cima do casulo** (uma imagem por nível de
carga das células, um componente `ResourceSprites` no armazenamento das células). O projeto e todos os números
ficam em `tools/spec/bullet_strike_missiles.json` (versão para ler: `docs/MISSEIS_PROJETO.md`); as regras são
escritas por `tools/bsgen/launchers.py`.

Enquanto um modelo não existe, `tools/bsgen/sprites.py` desenha substitutos procedurais com **os mesmos arquivos e
a mesma geometria**, então um modelo pronto os substitui sem mudar as regras.

### 8.1 O que as regras referenciam (o contrato da arte)

| imagem(ns) | camada | componente | observações |
|---|---|---|---|
| `turret.png`, `turret_normals.png`, `turret_off.png`, `turret_shadow.png` (+ quadros `turret<n>.png` se houver `turret_anim`) | casulo: `roof_doodads`; sombra: `doodads_high` | `TurretGraphics` (ChainedTo Turret, Rotation 90d) | quadrado de lado `turret_box` centrado no pivô, frente = topo da imagem, exatamente como a cabeça de uma arma. **As bocas dos tubos são desenhadas VAZIAS** (buracos escuros) |
| `cells_<tipo>_p<casulo>_<n>.png` + `cells_<tipo>_p<casulo>_<n>_normals.png`, n = 0..unidades daquele casulo | `roof_turrets` (por cima do casulo) | um `ResourceSprites` por casulo e por modo de míssil (`RangeLow`/`RangeHigh` = as unidades das células daquele casulo, `HasZeroResourceSprite = true`, `Location` = centro do retângulo do casulo, `Size` = o tamanho dele) | **tela = o retângulo de sobreposição do casulo**, um recorte da tela de `turret.png` (pixels `[x0, y0, x1, y1]` na tela da torre, frente = topo da imagem) calculado por `overlay_rect()` em `tools/launcher_layout.py`: a caixa que envolve todos os narizes daquele casulo naquele modo (quadrado de 5 x `tube_r` por tubo; `box` x 1,15 nas unidades pesadas/torpedo) + 2 px. O nível n mostra os narizes carregados das n primeiras unidades das células daquele casulo **na ordem de enchimento**; todo o resto é transparente. O nível 0 é todo transparente. Só os casulos que têm unidades naquele modo ganham arquivos (Iara: `p1`, `p2`). O recorte mantém as texturas pequenas (Mula: 50 a 70 px por casulo em vez de 307 x 307, cerca de 8 MiB de sobreposições para os três lançadores em vez de 128 MiB) |
| `shutters_<tipo>.png` + `_normals.png` | `roof_turrets` | `Shutters` (`Graphics` dentro do bloco `Fire_<tipo>` daquele modo, então só aparece naquele modo) | só nos leiautes `*_inner` (Iara da Mula): persianas fechadas sobre os casulos que não têm unidade naquele modo (os casulos externos), mesma tela de `turret.png` |
| `turret_oc.png` (sem normais) | `roof_turrets` | `OverclockGlowGraphics` (`OperationalToggle = IsOverclocked`) | lançadores com overclock (Caipora, Mula): SÓ o brilho do overclock numa tela transparente do tamanho de `turret.png` (Caipora: o olho da cúpula fica laranja + brasas nas ventilações; Mula: o recesso do colar e as ventilações dos casulos brilham). Opcional num modelo 3D: sem ele as regras pulam o componente |
| `floor.png`, `walls.png`, `roof.png`, `roof_normals.png`, `lights.png` | camadas do casco | `Graphics` | igual às armas (teto verde, assentos da tripulação; os lançadores devem mostrar suportes/berços de mísseis no chão) |
| `icon.png`, `blueprints.png` | – | editor | montados por `tools/make_art.py` a partir do teto + casulo + células cheias |

Os efeitos de lançamento são partículas do jogo base, não imagens: o clarão de cada tubo é
`ships/terran/missile_launcher/particles/missile_launcher_shoot_flash.rules` (bucket `Upper1`) em cada emissor, e a
baforada de sopro é `ships/terran/chaingun/particles/chaingun_shoot_smoke.rules` (Tocandira, Caipora) ou
`ships/terran/cannon_deck/particles/cannon_smoke_deck.rules` (Mula, bucket `RoofCannonSmoke`) no ponto `backblast`
do casulo que disparou (um ponto por casulo; o ponto único da Tocandira solta a baforada em todo lançamento). Não use
`missile_launcher_shoot.rules` (bucket `Middle3`, ficaria escondido sob o nosso teto). **Sem recuo do casulo**: o
recuo moveria o casulo, mas não as sobreposições.

A ordem de disparo é **LIFO**: a última unidade carregada nas células dispara primeiro, então em toda salva cheia a
sobreposição que some é a do tubo que acabou de disparar. Limite cosmético conhecido (teste T21 do spec): uma salva
parcial (o paiol ficou sem peças, `DryFlush`) ou o resto de uma salva interrompida depois de voltar ao tipo de
míssil começa pela ÚLTIMA célula, então um tubo que parece vazio dispara enquanto some uma célula que parecia
carregada (as sobreposições desenham o nível de carga das células, e o ciclo de células recomeça do topo). Contagem
e dano não mudam; não tente corrigir isso na arte. A unidade das células de cada modo é definida pelo spec
(`launchers[].modes[].layout`, calculado por `tools/launcher_layout.py`); cada unidade tem uma **forma** que diz à
arte o que desenhar:

| leiaute | lançador / modos | unidades das células | forma | como fica uma unidade carregada |
|---|---|---|---|---|
| `cassette` | Tocandira (todos) | 6 cassetes de tubo duplo (12 tubos) | `tube` | um nariz em cada um dos 2 tubos |
| `fine16` (casulos `pattern: "3-2-3"`) | Caipora he, cluster, limpet, napalm, emp | 16 (2 casulos x 8) | `tube` | um nariz no tubo |
| `torpedo2` | Caipora Boto | 2 (um por casulo) | `torpedo` | um nariz grande de torpedo com tampa cobrindo a face inteira do casulo |
| `fine48` | Mula he | 48 (4 casulos x 3x4) | `tube` | um nariz no tubo |
| `heavy16` | Mula cluster, limpet, napalm, emp | 16 (4 fileiras x 4 casulos) | `heavy` | um nariz longo de calibre duplo deitado sobre a fileira inteira de 3 tubos |
| `torpedo4` | Mula Boto | 4 (um por casulo) | `torpedo` | nariz grande com tampa sobre a face do casulo |
| `torpedo2_inner` | Mula Iara | 2 (os 2 casulos internos) | `torpedo` | nariz grande com tampa e uma faixa verde fina; os casulos externos mostram `shutters_nuclear.png` |

Ordem de enchimento: um casulo depois do outro, na ordem da lista `cells.pods` do spec (Caipora: E e depois D, então
o casulo direito esvazia primeiro; Mula: externo E, interno E, interno D, externo D), fileiras de trás para a frente,
da esquerda para a direita dentro de uma fileira. Uma unidade `heavy`/`torpedo` tem um `box` = [largura lateral,
profundidade] em quadros (heavy: a fileira; torpedo: a face do casulo), escrito pelo leiaute e passado para
`cell()`.

### 8.2 Arquivo do modelo (`tools/blender/parts/bs_msl_<box|twin|quad>.py`)

```python
PART = {
    "id": "rafaeltessaro.bs_msl_twin", "kind": "launcher",
    "size": [3, 3], "pivot": [1.5, 1.4],      # PRECISA bater com launchers[].size e art.part_meta.pivot do spec
    "turret_box": 2.8, "ring_r": 1.15, "collider": 1.25, "accent": "amber",
    "looks": ["he", "cluster", "limpet", "napalm", "emp", "torpedo"],   # todos os modos de míssil do lançador
    "oc_glow": True,                           # Caipora / Mula: renderiza turret_oc.png com oc_glow()
    # opcional: "cells": {...} substitui art.part_meta.cells (casulos: centro + cols/rows ou pattern "3-2-3", pitch,
    #           em coordenadas da CABEÇA; tube_r; units "pairs" | single); o padrão lê o spec, então as células
    #           sempre batem com as regras
    # opcional: "backblast": [[x, y], ...] (coordenadas da cabeça, um por casulo), "lights": [...], "turret_anim": {...}
}
def head(M, T="head", phase=0.0): ...   # suporte + casulo(s); bocas dos tubos VAZIAS (escuras), nas posições de célula do spec
def cell(M, look, T="cell", form="tube", box=None): ...
    # forma "tube": UM nariz carregado na origem (eixo do tubo inclinado como o casulo), com uma faixa fina na cor
    #               do tipo; precisa caber num quadrado de 5 x tube_r
    # forma "heavy": um nariz longo de calibre duplo deitado ao longo de x, centrado, cabendo em box[0] x box[1] (quadros)
    # forma "torpedo": um nariz grande de torpedo com tampa, centrado, cabendo em box[0] x box[1] (a face do casulo)
def shutter(M, T="shutter", box=None): ...   # só na Mula: UMA placa de persiana fechada, centrada, cabendo em box (face do casulo)
def oc_glow(M, T="oc"): ...                   # Caipora/Mula: SÓ as partes emissivas do overclock, em coordenadas da cabeça
                                              # (olho da cúpula / recesso do colar / ventilações, por exemplo M["ember"]
                                              # reforçado); o renderizador guarda só a emissão delas + um halo suave
def roof(M, T="roof"): ...              # opcional (padrão Mo.hull_roof)
def floor(M, T="floor"): ...            # opcional (padrão Mo.hull_floor)
```

As posições das células vêm de `tools/launcher_layout.py` (compartilhado com o gerador das regras): coordenadas da
cabeça (x para a direita, y para a frente a partir do pivô). O renderizador renderiza `cell()` uma vez por visual e
forma e cola o resultado em cada tubo (`tube`) ou no centro da unidade (`heavy`, `torpedo`) das n primeiras unidades
para montar cada nível, e cola `shutter()` em cada casulo com persiana, então os narizes sempre ficam exatamente sobre
as bocas que `head()` desenha nas mesmas coordenadas. Um leiaute com persianas e um modelo sem `shutter()` param o
render com erro.

`render_part.py <id_curto> [--quick] [--out DIR] [--only turret,hull,cells]` grava as imagens e um `meta.json` com
`kind: "launcher"`, `turret` (como nas armas, mais `oc_glow`), `modes.<tipo>.units` / `tubes` / `unit_pods`
(coordenadas da torre, ordem de enchimento), `modes.<tipo>.overlays[{range, files, normals, rect}]` (`rect` = o
retângulo do casulo em que as imagens dos níveis são recortadas, vindo de `overlay_rect()`; as regras posicionam o
`ResourceSprites` com ele) e `modes.<tipo>.shutters{file, normals, pods}`, mais `backblast`, `crew_pos`, `hull` e
`lights`. O renderizador monta cada nível direto na tela do retângulo do casulo e para com erro se um nariz não
couber nela. `tools/bs_data.py` confere se cada modo tem tantas unidades quanto as células do spec e se os modos
`*_inner` têm persianas; `tools/check_art3d.py <id_curto>` confere os tamanhos das telas (tela da torre para
`turret*.png` e persianas, retângulo do casulo para os níveis das células).

### 8.3 Estilo por lançador (o mesmo visual de família das armas: núcleo escuro + placas claras, LEDs em recessos)

| lançador | tamanho | tripulação | casulos / tubos | unidade das células | estilo | destaque |
|---|---|---|---|---|---|---|
| bs_msl_box (Tocandira) | 2x2 | 1 | 1 casulo-caixa, 4x3 = 12 tubos, inclinados 35 graus | cassete de tubo duplo (6) | caixa estilo RAM num garfo curto, garras laterais, espinha com fenda infravermelha âmbar, compartimento de ventilação traseiro com 3 luzes | amber |
| bs_msl_twin (Caipora) | 3x3 | 2 | 2 casulos octogonais (3-2-3, passo 0,24) = 16 tubos, inclinados 35 graus, + cúpula sensora | 1 tubo (16); torpedo 2 | "dois punhos": casulos octogonais em braços ladeando uma cúpula blindada com uma fenda de olho sensor, lâminas-garra à frente, quatro pés abertos sobre o anel, escotilha de paiol traseira + compartimento de ventilação com 5 luzes; overclock: o olho fica laranja e as ventilações brilham | amber |
| bs_msl_quad (Mula-sem-Cabeça) | 5x6 | 8 | 4 casulos retangulares 3x4 (passo 0,26 x 0,22) = 48 tubos, inclinados 40 graus, em braços hidráulicos | 1 tubo (48); fileira pesada (16); torpedo 4; nuclear 2 + persianas | corpo largo sem cabeça: um colar blindado aberto com um recesso de brasa MUITO fraco onde deveria estar a cabeça, braços de pistão, lâminas-garra na raiz dos casulos, saia blindada sobre o anel, compartimento de ventilação traseiro com 6 luzes; overclock: o recesso do colar e as ventilações dos casulos brilham (cabeça alternativa: sobrancelha de gigante de um olho só) | amber |

Narizes das sobreposições: cone do nariz claro + uma faixa de 2 a 3 px na cor do míssil (`missile_types[].glow` do
spec): Jararaca âmbar, Piranha amarela, Carrapato vermelha, Taturana laranja, Poraquê azul, Boto branca, Iara verde.
Mantenha o orçamento de 1 a 2% de emissivo (o brilho do overclock fica em `turret_oc.png`, mostrado só com o
overclock ligado).

Os substitutos procedurais (`tools/bsgen/sprites.py`: `launcher_pod_canvas` (caixa), `launcher_twin_canvas`,
`launcher_quad_canvas`, `_nose_big`, `render_launcher_shutters`, `render_launcher_oc_glow`) seguem esta tabela e o
mesmo contrato de arquivos; um modelo pronto os substitui quando se acrescenta `art3d/<id_curto>/meta.json`.

### 8.4 Mísseis em voo (`kind: "missiles"`)

Cada míssil tem o seu próprio sprite 3D visto de cima, na mesma linguagem das torres (placas claras chanfradas sobre
um núcleo escuro, divisas apontando para a frente, LEDs em recessos), e **cada tipo precisa ser reconhecível a 1x**.
São 22 sprites: os 15 mísseis (tipo x nível), os filhos (submunição da Piranha, ogivas e iscas do Boto e da Iara) e a
carga grudada do Carrapato. As chaves, telas, quadros e fps são os da tabela de arte dos mísseis
(`tools/spec/bullet_strike_missile_fx.json`, cópia de `missile_art_table.json`); o `check_art3d` confere contra ela.

O modelo fica em `tools/blender/parts/bs_missiles.py` e a saída em `art3d/bs_missiles/`. O build copia os PNGs para
`shots/bs_missile_art/` e as regras (`tools/bsgen/missile_fx.py`) os referenciam como `../bs_missile_art/<arquivo>`.
Sem `art3d/bs_missiles/meta.json` as regras voltam ao corpo do jogo base (`missile_he.png`), então o build nunca
quebra por falta de arte.

```python
PART = {
    "id": "rafaeltessaro.bs_missiles", "kind": "missiles", "px_per_tile": 64, "accent": "amber",
    "items": {   # uma entrada por chave da tabela de arte
        "he_m": {"canvas_tiles": [1.75, 0.625],   # tela [comprimento, largura] em quadros (nariz em +x)
                 "frames": 2, "fps": 4,           # quadros do atlas de luzes (1 = sem atlas)
                 "wrap": None,                    # None = laço; "Clamp" = toca uma vez e para (carga do Carrapato)
                 "nozzle_x": -0.86,               # bocal (x em quadros): onde as regras põem a chama
                 "mask": False,                   # mísseis não têm máscara
                 "anchors": {"seeker": [0.84, 0.0]}},   # opcional: seeker | warhead | radiation, [x, y] em quadros
        ...
    },
}

def model(M, key, T="body", phase=0.0): ...
    # UM projétil, nariz em +X, centrado na origem, eixo = X (z = altura; o topo do corpo fica em z ~ raio).
    # Tudo com a etiqueta T; os emissivos com (T, "lights"). phase = k/frames escolhe o quadro do atlas de luzes.
```

O renderizador (`render_part.py`, função `render_projectiles`) faz, para cada item:

| arquivo | conteúdo |
|---|---|
| `msl_<chave>.png` | difuso com a luz axial (seção 11.1) e **os emissivos apagados** (os LEDs saem como lentes escuras), 48 amostras (`--quick`: 12) |
| `msl_<chave>_normals.png` | normais (R = +x, G = +y para cima, B = para fora), alfa igual ao do difuso |
| `msl_<chave>_lights.png` | atlas de luzes ADITIVO, só quando `frames > 1`: um quadro por fase k/n (a cena é refeita com `phase = k/n`), só a emissão dos objetos `(T, "lights")`, com o resto do míssil em Holdout (tapa o brilho que fica atrás) e um halo suave; n quadros numa fileira (`n*w x h`) |

O `meta.json` segue o esquema combinado com as regras:

```json
{"version": 1, "kind": "missiles", "id": "rafaeltessaro.bs_missiles", "px_per_tile": 64,
 "items": {"he_m": {"size": [1.75, 0.625], "px": [112, 40], "file": "msl_he_m.png", "normals": "msl_he_m_normals.png",
                    "lights": {"file": "msl_he_m_lights.png", "frames": 2, "frame_px": [112, 40], "per_row": 2,
                               "fps": 4, "wrap": null},
                    "mask": null, "nozzle": [-0.86, 0], "anchors": {"seeker": [0.84, 0.0]}}},
 "files": ["msl_he_m.png", "msl_he_m_lights.png", "msl_he_m_normals.png"]}
```

No jogo: corpo `Sprite` em `BulletUpper3` com `IsLit` e `NormalsTexture`; luzes num `AnimatedSprite` aditivo em
`BulletUpper4` (`FrameCount`, `FrameSize`, `FramesPerRow`, `FramesPerSecond` e `WrapMode = Clamp` na carga); chama
(`Beam`) em `BulletUpper2`, embaixo do corpo, a partir de `nozzle`. **Nunca** use um bucket Lower/Middle: fica
escondido sob o nosso teto. O tamanho no jogo é o `size` vezes o `Size` da regra (filhos compartilhados: Piranha
x1,0 / x1,15, isca do Boto x1,0 / x1,1, carga 0,9 / 1,25).

Escada de tamanhos (64 px/quadro; a caixa de física não muda, só o visual):

| nível | chaves | tela (quadros) |
|---|---|---|
| início (Tocandira) | `he_s`, `napalm_s` | 1,0 x 0,375 / 1,0 x 0,4375 |
| meio (Caipora) | `he_m`; `cluster_m`, `limpet_m`, `napalm_m`, `emp_m` | 1,75 x 0,625; 1,75 x 0,75 |
| fim (Mula) | `he_l`; `cluster_l`, `limpet_l`, `napalm_l`, `emp_l` | 2,5 x 0,875; 2,5 x 1,0 |
| torpedos (Boto) | `torpedo_m` / `torpedo_wh_m`, `torpedo_l` / `torpedo_wh_l` | 2,75 x 1,0 / 2,25 x 1,0; 3,25 x 1,25 / 2,75 x 1,25 |
| nuclear (Iara) | `nuclear_l` / `nuclear_wh_l` | 3,75 x 1,5 (o maior projétil do mod) / 3,1 x 1,5 |
| filhos | `cluster_child`, `torpedo_decoy`, `nuclear_decoy`, `limpet_charge` | 0,75 x 0,375; 1,75 x 0,625; 2,0 x 0,75; 1,0 x 1,0 |

Um míssil do fim é mais comprido **e** mais gordo **e** ganha estrutura (estágio de reforço, mais aletas, mais
segmentos, bobinas, garras); nunca é só o do meio ampliado.

Identidade de cada tipo (a faixa usa `Mo.band_mat(tipo)`, o mesmo material dos narizes carregados nos lançadores,
então o míssil em voo bate com o do casulo):

| tipo | apelido | silhueta / assinatura | luzes |
|---|---|---|---|
| Jararaca / Muriçoca (HE, âmbar) | víbora | flecha fina, luvas em divisa encaixadas ("escamas"), ogiva tangente com buscador escuro; `he_l` em 2 estágios | pisca (2 quadros) / corre (3 quadros, `he_l`) |
| Piranha (fragmentação, amarela) | cardume | cilindro gordo em 3 ou 4 baias, nariz em pétalas com anel de dentes (triângulos brancos sobre preto); filho = gota com rabo bifurcado, sem animação | LEDs das baias em sequência |
| Carrapato (lapa, vermelha) | carrapato | patas dobradas ao longo do corpo, 2 pares de pinças, cabeça-ímã hexagonal escura; carga = disco hexagonal com 6 patas e anel de 8 LEDs (10 quadros, `Clamp`, os 2 últimos com o anel inteiro) | estrobo + anel do ímã |
| Taturana (napalm, laranja) | lagarta de fogo | segmentos de tanque com visores de "fogo líquido" alternados, nariz em cúpula com bico de 3 furos; fim com tanques laterais | visores balançam (2 quadros) |
| Poraquê (P.E.M., azul) | poraquê | barbatanas-fita longas e baixas, pilha de bobinas de COBRE (`Mo.copper_mat()`) com frestas azuis, buscador com olho azul; fim com 2 pontas de arco | a fresta quente corre para o nariz (4 quadros) |
| Boto (torpedo isca, branco) | boto | cilindro branco grande, nariz arredondado com fenda escura, anel de carenagem na cauda; estágio 1 com luva de reforço e 2 propulsores laterais; iscas cinza sem faixa, estrobo rápido | estrobos brancos |
| Iara (torpedo nuclear, verde) | "tem que SABER que é nuclear" | o ÚNICO míssil de blindagem escura; ogiva gorda em 3 camadas com o trevo (cunhas pretas sobre disco verde), divisas verde/preto nos ombros, faixas verdes largas, janela do núcleo com grade de aço, bocal triplo; isca cinza sem divisas nem trevo | faixas, janela e anéis do bocal respiram (4 quadros, 0,55 / 0,8 / 1,0 / 0,8) |

Comandos (da raiz do repositório):

```bash
$PY tools/blender/render_part.py bs_missiles --quick --out <rascunho>/draft_missiles [--only he_m,nuclear_l] [--preview]
$PY tools/blender/render_part.py bs_missiles             # final, art3d/bs_missiles/ (as 22 telas são pequenas: renderize uma vez)
python3 tools/check_art3d.py bs_missiles                 # ou: python3 tools/check_art3d.py <rascunho>/draft_missiles
python3 tools/blender/compose_preview.py art3d/bs_missiles --sheet docs/preview/3d/misseis_em_voo.png \
    --gif docs/preview/3d/misseis_luzes.gif
```

As regras comuns a todos os projéteis (luz axial, telas pequenas, rotação, orçamento de emissivo, a exceção
nuclear e as armadilhas) estão na seção 11.

## 9. Armadilhas conhecidas (dos agentes que já modelaram armas)

- **Cortes rasos quebram o chanfro:** `Mo.slot_with_pips`/`B.cut` que entram só uns 0,02 numa placa chanfrada criam
  triângulos pretos (o chanfro é reaplicado depois da booleana). Use profundidade >= panel_h + 0,04 e mantenha as
  paredes do cortador pelo menos 0,03 para dentro da borda da face de cima.
- **Contornos deslocados que se cruzam:** `offset_ok` só detecta arestas que invertem de direção. Polígonos com
  vértices agudos perto de outras arestas (presas, entalhes) podem se cruzar sem aviso, e a booleana devolve uma
  malha VAZIA. Se uma parte sumir do render, simplifique o polígono ou reduza a inclinação.
- **Anel da cabeça sobre os canos:** em torres grandes o disco da torre (anel) pode cobrir a raiz dos canos quando
  a cabeça é desenhada por cima. Corte o arco da frente do disco nas bocas do berço.
- **Calor na blindagem clara:** marque como 'hot' só freios/pontas/colares. Nas armas de plasma use um `heat_color`
  ciano com valores de calor baixos.
- **Fundo do corte sobre outra face:** se a profundidade do `slot_with_pips` for igual à altura do painel, o fundo do
  cortador cai exatamente na face da placa de baixo, e a booleana coplanar pode deixar uma "tampa" sobre os recessos
  vizinhos. Use profundidade > panel_h.
- **Pontas finas depois do chanfro:** contornos côncavos cuja face de cima (depois do `slope`) afina abaixo de
  ~0,02 quadro criam triângulos sobrepostos que saem pretos (muitas vezes só no lado espelhado). Alargue a ponta ou
  desenhe o painel interno à mão (como fazem a Cigarra e o Tamanduá).
- O renderizador imprime `AVISO: '<obj>' ficou vazio depois das booleanas` quando uma peça some: confira sempre o
  log.
- **Casulos inclinados dos lançadores:** um recesso cortado perpendicular a uma superfície inclinada em torno de X
  mostra a parede do fundo iluminada por cima, preenchendo metade da janela escura. Corte com paredes verticais no
  mundo (desloque o polígono do cortador em dz*tan(pitch) no y local).
- **oc_glow() (lançadores com overclock):** desenhe SÓ objetos emissivos com a etiqueta 'oc'; qualquer coisa não
  emissiva marcada com 'oc' sai preta sobre a torre.
- **Casulos inclinados (projeção):** tudo o que se projeta de uma face inclinada desloca-se para a FRENTE na vista de
  cima em altura*cos(pitch); uma moldura alta pode cobrir as bocas vazias da fileira de trás. Mantenha a moldura
  baixa (~0,045) e deixe ~0,1 de espaço entre a abertura e as bordas da fileira de trás.
- **Saturação da emissão:** com a vista Standard, brilhos acima de ~1,5 de intensidade saturam (o laranja vira
  amarelo). Um "olho laranja" de overclock usa intensidade 1,0 a 1,5 com a cor (1, 0.16, 0.01).
- **Recesso mais fundo que a placa de cima num casulo inclinado:** um recesso cortado no topo de um casulo a 40
  graus mais fundo que a placa de blindagem de cima (~0,07 a 0,09 de espessura) chega ao corpo escuro do casulo,
  cuja face de cima vira o "fundo da ventilação" (e, com `oc_occlude`, esconde qualquer brilho de overclock abaixo
  dela). Mantenha o fundo dos recessos logo acima do topo do corpo.
- **Venezianas em topos inclinados:** lâminas montadas em esquadro com um topo inclinado escondem as próprias
  frestas na vista de cima (a grade parece uma fenda escura sólida). Incline-as para paredes verticais no mundo
  (topo deslocado em dz*tan(pitch)), como os cortadores.
- **`Mo.slot_with_pips(vertical=False)`:** `x` vira a posição y da fenda e `y0/y1` a faixa em x. Use argumentos
  nomeados e confira duas vezes.
- **`Mo.slot_with_pips` numa placa:** mire em `[shard, panel]`, nunca só no painel (o leito do recesso acaba
  enterrado dentro do corpo da placa e as luzes somem).
- **Fendas cegas estreitas em placas chanfradas:** o `B.cut` reaplica o chanfro, que também arredonda a aresta
  côncava do fundo de uma fenda cega e cobre as bordas do leito preto (em incrustações no teto verde a fenda sai
  verde). Em fendas mais estreitas que ~0,06, corte um furo passante e ponha o leito preto na peça de baixo (função
  auxiliar `_ledslot` em `parts/bs_factory_mag_ap.py`).
- **Desgaste da pintura em malhas pequenas:** a máscara de desgaste de borda do `mat_paint` vaza por faces inteiras
  de malhas pequenas, chanfradas e com poucos polígonos, e faz a pintura escura sair clara. Use `wear=0.0` em itens
  pequenos e escuros (munição).
- **`B.rpoly` com `sy` negativo** devolve um polígono em sentido horário: o corte não faz nada. Mantenha os tamanhos
  positivos.
- **Mapa de luz das fábricas:** `render_factory` monta `lights.png` só a partir do quadro 1 da máquina; mantenha os
  brilhos grandes estáticos ou aceite um mapa de luz estático.
- **Ilhas flutuantes:** confira se o sprite da torre é UM componente conectado (alfa > 100). Uma placa cujo polígono
  começa depois do fim da peça de baixo fica flutuando sobre o casco.
- **Brilho do overclock:** nunca cubra uma carcaça inteira com uma placa emissiva (parece um adesivo laranja chapado).
  Ponha emissores pequenos e concêntricos no fundo do recesso e deixe o `oc_occlude` (holdout) recortá-los com as
  bordas e aletas da frente.
- **`B.shard` em arestas curtas:** uma aresta de polígono mais curta que cerca de 2*(slope+groove) (pontas de
  lâmina, chanfros pequenos ao lado de arestas longas) pode deixar o painel interno VAZIO depois das booleanas, sem
  aviso, às vezes só no lado espelhado. O aviso "chanfro reduzido" é a pista; `render_factory`/`render_resource`
  agora também imprimem "ficou vazio".
- **Brilho ciano em repouso:** `M["glow_dim"]` é o destaque x 3,0, que no ciano sai quase branco (mais claro que um
  ciano saturado a 1,25-1,4). Nas partes cianas, monte níveis explícitos a partir de `Mo.CYAN` (por exemplo 0,16 /
  0,34 / 0,70 / 1,25) para o repouso ficar mais fraco que o ativo.
- **Iteração rápida de fábricas:** `render_part.py <fábrica> --quick --only f1,f8` renderiza só esses quadros da
  máquina; `--only hull` renderiza só teto/chão/paredes.
- **Brilhos de destaque azul:** `Mo.mats("blue")` põe glow/glow_dim com intensidade 9/3, que estoura para branco/
  ciano na vista Standard. As partes azuis definem materiais de brilho próprios de baixa intensidade (~0,5 a 1,5),
  como faz `parts/bs_mag_emp.py`.
- **O cache de materiais é por nome:** o `bs3d` guarda os materiais pelo nome, então dois arquivos de peça que
  definem "silver" ou "brass" com valores diferentes na mesma cena compartilham o primeiro. Reaproveite os valores
  existentes ou escolha um nome único.
- **Faixas de cobre** são a assinatura da família P.E.M. (o Carregador P.E.M. e o Energizador de Carregadores P.E.M.);
  as outras linhas de munição não devem usá-las.
- **Brilhos verdes:** acima de ~1,5 de intensidade, faixas emissivas verdes maiores ficam lima/amarelas na vista
  Standard (faixas ficam certas a ~1,3, núcleos a ~1,6). LEDs verdes no teto precisam manter o vermelho bem abaixo do
  verde e |r - b| >= 64 (0,25), senão o shader de pintura do jogo os trata como pintura: use uma cor como
  (0.32, 1, 0) a ~0,75.

## 10. Granadas de canhão (`kind: "shells"`)

Os canhões (Tambor 76 mm, Trovão 155 mm, Mapinguari 406 mm) e o obuseiro nuclear (Boiúna) disparam granadas 3D em
vez do dardo do jogo base. São 3 texturas reaproveitadas em todos os calibres; as regras (`tools/bsgen/caliber_fx.py`)
escalam a mesma imagem: 76 mm 0,72 x 0,26, 155 mm 1,15 x 0,40, 406 mm 2,05 x 0,72 e Boiúna 2,2 x 0,86 quadros. Por
isso elas são renderizadas a **128 px/quadro** e precisam ler bem tanto pequenas quanto grandes.

O modelo fica em `tools/blender/parts/bs_shells.py` e a saída em `art3d/bs_shells/`. O build copia os PNGs para
`shots/bs_shell_art/` e as regras os referenciam como `../bs_shell_art/<arquivo>`. Sem `art3d/bs_shells/meta.json` as
regras voltam ao dardo do jogo base no tamanho novo.

```python
PART = {
    "id": "rafaeltessaro.bs_shells", "kind": "shells", "px_per_tile": 128, "accent": "green",
    "items": {
        "he":   {"canvas_tiles": [2.0, 0.5], "frames": 1, "fps": 0, "wrap": None, "nozzle_x": -0.98,
                 "mask": True, "anchors": {}},
        "ap":   {"canvas_tiles": [2.0, 0.5], "frames": 1, "fps": 0, "wrap": None, "nozzle_x": -0.98,
                 "mask": True, "anchors": {}},
        "nuke": {"canvas_tiles": [2.0, 0.75], "frames": 4, "fps": 6, "wrap": None, "nozzle_x": -0.98,
                 "mask": False, "anchors": {"radiation": [0.4, 0.0]}},
    },
}

def model(M, key, T="body", phase=0.0): ...
    # igual aos mísseis (nariz +X, centrado, eixo X); a faixa da munição leva (T, "mask")
```

| arquivo | conteúdo |
|---|---|
| `bs_shell_he.png` + `_normals.png` | granada de espoleta (Padrão, P.E.M.): espoleta curta no nariz, corpo de aço escuro, cinta de forçamento de cobre, cauda afinada (boat tail) |
| `bs_shell_ap.png` + `_normals.png` | perfurante (Perfurante, Perfurante-Explosiva): ogiva longa e pontuda com capuz balístico escuro |
| `bs_shell_band_he.png`, `bs_shell_band_ap.png` | máscara da faixa da munição: os objetos `(T, "mask")` em **branco puro sobre transparente** (alfa = cobertura; o resto da granada tapa a faixa onde ela fica atrás). O jogo tinge com `VertexColor` = cor da munição: padrão [255, 190, 60], perfurante [215, 230, 255], perfurante-explosiva [255, 80, 40], P.E.M. [80, 150, 255]. No difuso, pinte a faixa de cinza claro neutro (`Mo.NOSE_LIGHT`) para o tom não sujar a cor |
| `bs_shell_nuke.png` + `_normals.png` | granada nuclear (seção 10.1) |
| `bs_shell_nuke_lights.png` | atlas de 4 quadros a 6 fps (uma fileira): as faixas verdes acesas, respirando |

O `meta.json` é o mesmo esquema dos mísseis (seção 8.4) com `"kind": "shells"`, `"px_per_tile": 128` e `"mask":
"bs_shell_band_<chave>.png"` nos itens com máscara. O tracante atrás da base é desenhado pelas regras (cor da
munição), não pinte tracante nem chama no sprite.

Formas: `Mo.shell_profile(L, R, "he" | "ap")` devolve os perfis de torno (cauda, corpo, ogiva, espoleta ou capuz, e a
cinta de forçamento) e `Mo.shell_parts(...)` torneia cada segmento com o seu material (a cinta pode receber
`mask_tags`). A cinta de forçamento de **cobre** (`Mo.copper_mat()`, o mesmo material das bobinas do P.E.M.) é a
única exceção à regra "cobre = família P.E.M." da seção 9: é um anel fino e real de artilharia, não uma bobina.

### 10.1 Granada nuclear (Boiúna)

Mesma família do recurso aprovado `bs_shell_nuke` (`tools/blender/parts/bs_shell_nuke.py`) e da Iara: corpo escuro
ou cinza-claro como pede o desenho, **faixas verdes que respiram** (atlas de 4 quadros, intensidades 0,55 / 0,8 / 1,0
/ 0,8), divisas verde/preto (`Mo.chevron_mat`) e o trevo embutido com cunhas pretas ou escuras (`Mo.trefoil_inlay`;
disco verde opcional). **Nunca** listras amarelo/preto nem disco amarelo (regra do mod desde a Boiúna). Por cima dela
as regras põem o `radiation_small.png` girando e a luz grande `radiation.png` verde (âncora `radiation`).

Comandos:

```bash
$PY tools/blender/render_part.py bs_shells --quick --out <rascunho>/draft_shells [--only nuke] [--preview]
$PY tools/blender/render_part.py bs_shells               # final, art3d/bs_shells/
python3 tools/check_art3d.py bs_shells
```

## 11. Regras comuns dos projéteis (mísseis e granadas)

### 11.1 Luz axial

Projéteis giram em voo: um míssil que vai para a esquerda mostraria a luz "de cima-esquerda" das torres do lado
errado. Por isso `render_projectiles` usa `B.reset("axial")` (ou `B.lights_axial()` depois de um `reset()`):

- sol principal reto de cima (2,6), **sem reflexo especular** (`key_glossy=False`): com a câmera ortográfica olhando
  reto para baixo, o reflexo desse sol volta direto para a câmera em toda face plana virada para cima e a blindagem
  clara estoura em branco puro (testado: mediana 254 contra 208 sem o reflexo, que é a faixa das torres aprovadas);
- dois preenchimentos iguais (0,7) a +-70 graus em torno do eixo X, um de cada lado do míssil;
- nada iluminado de um lado só. A sombra no jogo vem do mapa de normais (`IsLit`).

Metal polido mostra 2 brilhos simétricos (os preenchimentos), um de cada lado do eixo; isso é esperado. A luz padrão
das torres (`B.reset()`) não muda.

### 11.2 Telas pequenas: formas grandes

Um micromíssil tem 64 x 24 px; um filho da Piranha, 48 x 24. Vale a regra 1.9 com mais força:

- 3 a 4 elementos legíveis por míssil pequeno (corpo, nariz, faixa, aletas); detalhe nenhum menor que 2 px
  (0,03 quadro a 64 px/quadro, 0,016 a 128 px/quadro); faixa com 2 a 3 px no mínimo;
- o tipo se reconhece pela **silhueta** (pétalas, pinças, segmentos, bobinas, anel de carenagem, ogiva gorda), não por
  pintura miúda;
- confira sempre a 1x na prévia (`compose_preview`), não só ampliado.

### 11.3 Rotação e simetria

O sprite gira com o projétil: nada de sombra projetada, luz lateral ou texto pintado. Modele simétrico no eixo X
(espelho em Y); só detalhes pequenos podem ser assimétricos (os visores alternados da Taturana, por exemplo).

### 11.4 Orçamento de emissivo

A área acesa do quadro 0 do atlas fica em **até 3% da área do corpo** (Iara e granada nuclear: até 4%, pelas faixas
largas que respiram). O `check_art3d` mede: pixels do quadro 0 com alfa >= 128 (o halo forte conta) sobre os pixels
do difuso com alfa >= 128. A respiração/piscada vem dos quadros, não de áreas grandes acesas.

### 11.5 LEDs só em recessos

O atlas é somado por cima do corpo iluminado; um LED sobre blindagem branca some. Ponha cada luz no fundo de um
recesso escuro (leito preto, como `Mo.slot_with_pips` ou uma caixa rebaixada). O difuso sai com os emissivos
apagados (lentes escuras). Todo objeto emissivo que deve acender leva `(T, "lights")`; um emissivo sem essa etiqueta
não entra no atlas, e um objeto com a etiqueta que não é emissivo sai preto (o renderizador avisa).

### 11.6 Exceção nuclear (só projéteis)

A Iara e a granada nuclear podem usar **divisas verde/preto** (`Mo.chevron_mat`, verde `Mo.BAND["nuclear"]`) e o
**trevo** (`Mo.trefoil_inlay`, cunhas pretas ou escuras, disco verde opcional), que a regra 1.6 proíbe nas torres:
"quando você vê o míssil nuclear, você SABE que é nuclear". A exceção vale só para projéteis; torres, fábricas e
recursos continuam sem faixas de perigo. Nunca amarelo/preto em lugar nenhum. As iscas da Iara não levam divisas,
trevo nem a luz de radiação (a Iara de verdade é a que tem a luz verde girando).

### 11.7 Funções do kit (`tools/blender/models.py`)

| função | uso |
|---|---|
| `BAND`, `BAND_GLOW`, `NOSE_LIGHT`, `band_mat(tipo)`, `nose_paint(nome, cor)` | cópias exatas de `parts/bs_msl_quad.py` (o cache de materiais é por nome: `band_<tipo>` sai igual no lançador e no míssil) |
| `COPPER`, `copper_mat()` | o cobre de `parts/bs_mag_emp.py` (nome "copper", mesmos valores) |
| `lathe(nome, perfil, mat, tags, verts, axis="X", zc, a0, smooth)` | sólido de revolução; `axis="X"` = eixo do projétil (perfil `[(raio, x)]` da cauda para o nariz, tampa no fim); `verts=8, a0=pi/8, smooth=False` = tubo octogonal de topo plano como os canos |
| `ogive(R, L, x0, tip_r)` | perfil de ogiva tangente (cópia de `bs_msl_quad._ogive`) |
| `shell_profile(L, R, "he" \| "ap", **ajustes)`, `shell_parts(...)` | perfis e peças torneadas das granadas (seção 10) |
| `trefoil_polys(...)`, `trefoil_inlay(nome, alvos, cx, cy, ztop, ro, ri, M, tags, disc_mat, surface_r, a0)` | trevo nuclear embutido: recesso de paredes verticais até um fundo plano abaixo da curva (`surface_r`), cunhas e disco planos dentro; a 1a cunha aponta para o nariz (`a0 = 0`) |
| `chevron_sleeve(nome, x0, x1, r, mat, tags, dv, ...)` | luva de blindagem com a frente em divisa e o entalhe atrás ("escamas"), feita na malha (sem booleana) |
| `chevron_mat(nome, c1, c2, escala)` | tinta em divisas apontando para o nariz (padrão verde/preto) |

### 11.8 Armadilhas dos projéteis

- **Um componente só:** aletas, pinças e faixas precisam encostar no corpo (alfa > 100); o `check_art3d` reprova
  ilhas soltas (a mesma armadilha das torres, seção 9).
- **Divisas por booleana:** cortar uma divisa num tubo chanfrado cai em todas as armadilhas da seção 9 (corte raso,
  fundo coplanar, ponta fina depois do chanfro, malha vazia). Use `Mo.chevron_sleeve`, que desloca os vértices de
  cada anel em X conforme |y|: as faces continuam planas e as tampas viram paredes verticais em V, invisíveis de
  cima. Se for cortar fendas/LEDs numa luva, use profundidade >= 0,04 (o `B.cut` reaplica o bisel).
- **Recorte em superfície curva:** um recesso no topo de um corpo torneado precisa de fundo abaixo da superfície em
  toda a área do desenho (a curva desce para os lados e, na ogiva, para a frente). Passe ao `trefoil_inlay` o raio no
  ponto mais baixo do desenho (`surface_r`) e o `ztop` desse ponto.
- **Tela justa:** o nariz e o bocal não podem encostar na borda da tela (o `check_art3d` avisa); deixe ~0,02 quadro.
- **Brilhos verdes e azuis:** valem as intensidades da seção 9 (faixas verdes ~1,3; azul próprio de 0,5 a 1,5).
- **Quadros do atlas:** a cena inteira é refeita a cada fase; não use aleatoriedade sem semente no modelo, senão o
  corpo "treme" entre os quadros.

### 11.9 Conferência e prévias

- `python3 tools/check_art3d.py bs_missiles | bs_shells | todos | <pasta de rascunho>`: arquivos e nomes do contrato,
  `px = size x px_per_tile` (+-1 px), atlas `n x w` numa fileira, um componente de alfa por sprite, orçamento de
  emissivo do quadro 0, máscaras brancas sobre transparente (e dentro do corpo), normais com o alfa do difuso;
  nas pastas oficiais, também as chaves do contrato (granadas `he`, `ap`, `nuke`; mísseis = tabela de arte).
- `python3 tools/blender/compose_preview.py <pasta> [--sheet PNG] [--gif GIF]` (ou `--preview` no render): folha com
  cada item a 1x e 3x sobre placas de casco, com uma chama/tracante simples na cor do tipo atrás do bocal, as luzes do
  quadro 0 somadas e a faixa tingida; GIF com os atlas de luzes animados (fps de cada item; `Clamp` segura o último
  quadro). Em Python, `compose_preview.make_projectiles(pasta, sheet_path, gif_path, lengths={chave: [comprimentos
  no jogo]}, mock_colors=..., mask_colors=...)` monta, por exemplo, a escada de calibres das granadas.
