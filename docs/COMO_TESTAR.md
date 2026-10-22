# Bullet Strike 2.0: como testar

> Gerado por `tools/make_docs.py` a partir de `tools/spec/` (spec 2.0) e da camada de dados `tools/bs_data.py`, com os switches do build. Não edite à mão.

O roteiro de testes da 2.0 é o **[CHECKLIST_2_0.md](CHECKLIST_2_0.md)**. Ele começa pela instalação, pelo carregamento e pela Fita de Alimentação, e segue família por família. Este arquivo só junta as dicas e o que está valendo enquanto os testes não voltam.

## 1. O que instalar

| Pasta no repositório | Nome na lista de mods | Zip | Descrição |
|---|---|---|---|
| `BulletStrike` | Bullet Strike | `testes/BulletStrike_2_0.zip` | [2.0 de TESTE] Versão com a Fita de Alimentação (teletransporte). Se não carregar, use a reserva 'Bullet Strike (reserva sem Fita)'. Nunca ative as duas juntas. |
| `testes/BulletStrike_SemFita` | Bullet Strike (reserva sem Fita) | `testes/BulletStrike_SemFita.zip` | [2.0 de TESTE - RESERVA SEM FITA] Mesmas armas, paióis e fábricas; sem a peça Fita (tripulação + paiol acoplado). Nunca ative junto com o 'Bullet Strike'. |

Nunca ative as duas juntas: as peças têm os mesmos IDs. Cada zip traz também o `CHECKLIST_2_0_CURTO.txt` (os itens essenciais).

## 2. Como seguir o checklist

- Faça as seções na ordem. A seção 2 (Fita) vem antes das armas porque decide o transporte da munição.
- Os itens com ★ liberam a versão final 2.0.0: 1.1, 1.2, 1.3, 1.7, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15 e 11.1.
- Os itens **(com SW)** são com o Star Wars: A Cosmos Divided ativo junto: 1.7, 2.15, 6.5, 7.3, 7.4, 8.11, 8.12, 9.2, 9.3, 9.5, 10.1, 10.2, 10.3, 10.4, 11.3 e 11.5. Todos os outros: só o Bullet Strike.
- Abra o jogo com o modo desenvolvedor (na Steam: botão direito no Cosmoteer > Propriedades > Opções de inicialização > `--devmode`): os erros de carregamento aparecem com detalhes.
- Se travar, o motivo fica nas primeiras linhas do log mais recente da pasta Logs, acima de `--- End of inner exception stack trace ---`.

## 3. Como me mandar o resultado

1. Mande uma linha por item: número + sim/não + o que viu (ex.: '2.3 sim', '8.6 não: andou para a frente'). Pode pular o que não deu para testar (diga 'não testei').
2. Se travou: mande o log mais recente da pasta Logs e, se puder, um print.
3. Se você já tinha respostas do TesteFita (A1-A7, A3b, B1-B3, C1-C3), mande também. Não é mais obrigatório: a seção 2 refaz o kit com as peças de verdade.

## 4. O que está valendo enquanto os testes não voltam

Cada escolha que depende de um teste usa o valor seguro ("safe") até a resposta, a não ser que você já tenha respondido ou que o build precise de outro valor. Quando você mandar as respostas, eu troco o que falhou.

| Escolha | Valor neste build | Por quê | Item do checklist |
|---|---|---|---|
| `art.fita_luz` | `ack` | decisão (sua resposta / do build) | 2.1 |
| `art.frag_cone` | `radial` | safe (sem resposta) | - |
| `art.light_split` | `split` | safe (sem resposta) | 3.2 |
| `art.pen_media` | `light` | safe (sem resposta) | 11.4 |
| `balance.perfil` | `sw` | safe (sem resposta) | - |
| `balance.perfil_extra` | `false` | sua resposta / pedido | - |
| `boiuna.ac_guided` | `true` | safe (sem resposta) | 3.7 |
| `econ.factory_adjacency` | `vanilla` | sua resposta / pedido | 4.4 |
| `guns.ac_cost` | `4x` | safe (sem resposta) | - |
| `guns.ap_further_factor` | `sem_reducao` | safe (sem resposta) | 10.2 |
| `guns.defesa_antilaser` | `fase_b` | safe (sem resposta) | 9.3 |
| `guns.frag_fragment` | `volumehit` | safe (sem resposta) | 9.4 |
| `guns.he_further_factor` | `0.5` | safe (sem resposta) | 10.1 |
| `guns.small_rounds_targetable` | `false` | safe (sem resposta) | - |
| `logistics.acoplamento` | `auto` | safe (sem resposta) | 12.3 |
| `logistics.devolucao_arma` | `off` | safe (sem resposta) | - |
| `logistics.fita_alcance` | `1000` | safe (sem resposta) | 11.1 |
| `logistics.fita_arma` | `empurra` | safe (sem resposta) | 2.5 |
| `logistics.fita_embutida` | `off` | safe (sem resposta) | - |
| `logistics.fita_fabrica` | `B` | decisão (sua resposta / do build) | 2.3 |
| `logistics.paiol_contador` | `false` | decisão (sua resposta / do build) | 5.3 |
| `logistics.paiol_seletor` | `botao` | safe (sem resposta) | - |
| `logistics.recurso_cookoff` | `off` | safe (sem resposta) | - |
| `logistics.reserva_tripulacao` | `metade` | safe (sem resposta) | 2.11 |
| `logistics.transport` | `teleporte` | decisão do build de teste | 2.3/2.5/2.7 |
| `missiles.cluster_lite` | `false` | safe (sem resposta) | 6.4-6.7/11.2 |
| `missiles.cluster_petals` | `bullets` | safe (sem resposta) | - |
| `missiles.cluster_randomize_target` | `on` | safe (sem resposta) | 6.4 |
| `missiles.iara_hp` | `12000` | safe (sem resposta) | - |
| `missiles.poraque_overload` | `false` | safe (sem resposta) | - |
| `pem.heavy_name` | `Corisco` | sua resposta / pedido | 7.2 |
| `pem.overload_rider` | `false` | safe (sem resposta) | - |
| `pem.tuvira_cp` | `2` | safe (sem resposta) | - |
| `pem.tuvira_mount` | `torre` | sua resposta / pedido | 7.1 |
| `rail.buffed_riders` | `false` | safe (sem resposta) | 8.1/8.3/8.11-8.13 |
| `rail.charge_wave` | `atraso` | safe (sem resposta) | - |
| `rail.enabled` | `true` | sua resposta / pedido | 8.1 |
| `rail.loader_intake` | `auto` | decisão do build de teste | - |
| `rail.overload_rider` | `false` | safe (sem resposta) | - |
| `rail.power_mode` | `B` | decisão (sua resposta / do build) | - |
| `rail.r2_fallback` | `true` | safe (sem resposta) | 8.1/8.3/8.11-8.13 |
| `rail.recoil_com` | `false` | safe (sem resposta) | 8.7 |
| `rail.tranco_gatilho` | `relay` | safe (sem resposta) | 8.8 |
| `rail.tranco_impulso` | `impulso` | safe (sem resposta) | 8.6 |

## 5. Testes do projeto x itens do checklist

- **Kit TesteFita:** A1->1.1/1.3, A2->2.1/2.2, A3/A3b->2.3/2.4, A4->2.5, A6->2.6, A7->2.7, B1->2.11, B2->2.12, B3->2.13, C1->2.14, C2->11.1, C3->1.7/2.15
- **Testes do 1º build 2.0:** T-FITA-1->2.7-2.9, T-F2-SPLIT->4.6, T-FRAG->9.4, T11->3.10/5.5, T3->10.1/10.2, R-1..R-4->8.1/8.3/8.11-8.13, T-MSL-*->6.4-6.7/11.2, T-ART-5->3.2, T-ART-6->11.4, T-TR-1..6->8.2/8.6-8.10/8.15, B-1->3.7, T-ACOPLA->12.3/12.4

Se você ainda tiver respostas do kit TesteFita, elas valem no lugar dos itens correspondentes.
