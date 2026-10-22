"""Entrada (e saida) da municao nas maquinas do Bullet Strike 2.0 (dono: WP05; modulo de CONTEUDO, API 2).

Seam de logistica que TODOS os modulos de peca chamam por common.content_module('bsgen.intake') (nunca pelo _opt dos
efeitos; BS_FX_EXT nao desliga isto). Sem este modulo a maquina fica so com a tripulacao.

    part_fields(g, ctx)                -> {TypeCategories_add, ReceivableBuffs_add} do transporte
    weapon_intake(comp, g, ctx)        -> entrada da arma / defesa / PEM / lancador / Carregador do Tupa
    weapon_return(comp, g, ctx)        -> devolucao do modo nao escolhido (logistics.devolucao_arma = on)
    factory_output(comp, f, rc, ctx)   -> saida da fabrica por receita (rc = receita do factory.py: key, saida...)
    selfcheck(mod_dir, SPEC)           -> conferencia das pecas escritas

Transporte (logistics.transport, bs_data.transport()):
  * teleporte (Fita de Alimentacao grudavel, SPEC.fita_teleporte; molde testes/BulletStrike_TesteFita): a municao
    passa fabrica -> paiol -> arma pelo sistema de buffs (MultiResourceStorage ViaBuffs + GridBuffProvider
    GridDistance = logistics.fita_alcance), todas as pernas EMPURRANDO:
      - fabrica, jeito B (padrao; SW hypermatter_reactor_2x2.rules:256-292, kit bs2f_fab_bala_b.rules): RedeFab
        GridBuffProvider BulletStrike_FitaFab + ParaPaiois_<k> {ViaBuffs OutgoingBuffProviders [RedeFab];
        ComponentIDs [EntraPaiol_<k>]} + Envio_<k>; jeito A (kit bs2f_fab_bala.rules; vanilla thruster_small.rules:
        199-209): ParaPaiois_<k> {ViaBuffs IncomingBuffTypes [BulletStrike_FitaRede]};
      - paiol -> arma (fita_arma = empurra, vanilla engine_room.rules:99-127, kit bs2f_arma.rules): a arma so tem o
        proxy FitaEntra_<chave> -> MagStorage_<i> com ProxyToggle Alimenta_<i> = MultiToggle All [ModeToggle_<i>,
        FitaLigada] (o paiol empurra pelo Rede/ParaArmas_<k>, bsgen.logistics); fita_arma = puxa (kit
        bs2f_arma_puxa.rules): DosPaiois_<i> {ViaBuffs IncomingBuffTypes [BulletStrike_FitaRede]; ComponentIDs
        [Estoque_<chave>]} + Alimentador_<i>;
      - host: FitaLigada = BuffToggle BulletStrike_FitaLink (com logistics.fita_embutida = botao: FitaGrudada +
        UIToggle FitaEmbutida + FitaLigada = MultiToggle Any, vanilla factory_uranium.rules:150), AvisaFita* (luz verde
        da Fita, art.fita_luz = ack) e a animacao 'cartuchos entrando/saindo' (art3d/bs_fita_fx).
    A reserva da tripulacao continua no MagConsumer_<i> de quem constroi a arma (common.mag_consumer; com
    logistics.reserva_tripulacao = sem_fita o common soma {Toggle = FitaLigada; Invert = true}: por isso toda maquina
    de teleporte tem o FitaLigada).
  * tripulacao: nada de fita nem de buff; so o ACOPLAMENTO (logistics.acoplamento: auto = ligado so aqui; on = sempre):
    PaiolAcoplado_<i> = ResourceStorageProxy {PartLocation = celula de tras; ProxyableComponents [{PartCriteria
    {Category = bs_paiol_<chave>}; ComponentID = Estoque_<chave>}]} + AlimentadorAcoplado_<i> (molde SW:ACD 0.30.4
    chaingun_magazine.rules:163-200) e, nas fabricas, EntregaAcoplada_<k> + EmpurraAcoplado_<k>. A Category e a do
    TIPO (J2R2-MED), nunca a da familia.
  * rede / gemea (esteira fisica, WP15): tudo pelo modulo bsgen.belt_net (BELTNET); sem ele o bs_data ja devolveu
    'tripulacao' (J2R3-19).

Contrato com quem chama (WP02 guns/ciws, WP04 factory, WP06 launchers, WP08 pem, WP09 railgun):
  * g['modes'] (index, res/resource, opcional feed_q / fita_target) ou g['logistica'] (bloco do spec); o alvo de cada
    modo e o ComponentID do FitaEntra_<chave> do spec (MagStorage_<i>; Carregador do Tupa: SlugMagazine);
  * com seletor, os ModeToggle_<i> ja tem que estar em comp ANTES do weapon_intake (sem eles e erro);
  * g['size'] e g['id']; g['fita_fx_location'] opcional (padrao: centro da fileira de TRAS [w/2, h - 0.5], fora da
    torre; Carregador do Tupa: SPEC.railgun.parts.carregador.fita_fx_location).
"""

import os
import re

from rules_dsl import Q, comment
from bsgen import common as C

API = 2

# variantes adiadas (ADDENDUM G11) que este modulo implementa; 'auto' da devolucao continua adiado (cai no safe
# 'off') para o build sem bullet_strike_switches.json bater com o build_2_0 do spec (devolucao_arma = off)
VARIANTS = {"logistics.fita_embutida": ("botao",), "logistics.devolucao_arma": ("on",)}

BUFF_LINK = "BulletStrike_FitaLink"     # Fita -> maquina vizinha
BUFF_ACK = "BulletStrike_FitaAck"       # maquina -> Fita (luz verde)
BUFF_REDE = "BulletStrike_FitaRede"     # paiol com Fita -> navio
BUFF_FAB = "BulletStrike_FitaFab"       # fabrica com Fita -> navio (jeito B)
BUFFS = (BUFF_LINK, BUFF_ACK, BUFF_REDE, BUFF_FAB)
CAT_FITA = "bs_fita"
CAT_MAQUINA = "bs_fita_maquina"
TOGGLE_EMBUTIDA = "bs_fita_embutida"
FX_DIR = "bs_fita_fx"           # art3d/bs_fita_fx publicada em parts/bs_fita_fx
FX_FRAMES = 8
FX_INTERVAL = 0.075             # 8 x 0,075 s = 0,6 s = o Timer
ANIM_TIMER = 0.6
FEED_INTERVAL = 0.1             # todas as pernas: q a cada 0,1 s
DEVOLVE_Q = 10                  # devolucao: 10 por 0,1 s
RAIL_LOADER = f"{C.AUTHOR}.bs_rail_loader"

_READY = []


def _D():
    """bs_data (import tardio: evita ciclo) com as variantes deste modulo liberadas (tambem fora do build_mod, ex.
    spec2_check, que importa os modulos sem o Registry)."""
    import bs_data as D
    if not _READY:
        D.implement_variants(VARIANTS, "bsgen.intake")
        _READY.append(True)
    return D


def beltnet():
    """bsgen.belt_net (WP15, esteira fisica) ou None."""
    return C.content_module("bsgen.belt_net")


# ----------------------------------------------------------------------------- switches
def transport():
    return _D().transport()


def teleporte():
    return transport() == "teleporte"


def fita_fabrica():
    return _D().switch("logistics.fita_fabrica")


def fita_arma():
    return _D().switch("logistics.fita_arma")


def alcance():
    return int(_D().switch("logistics.fita_alcance"))


def luz_ack():
    return _D().switch("art.fita_luz") == "ack"


def embutida():
    return teleporte() and _D().switch("logistics.fita_embutida") == "botao"


def devolucao():
    return teleporte() and _D().switch("logistics.devolucao_arma") == "on"


def acoplamento_on():
    """logistics.acoplamento: on = sempre; auto = so com transport = tripulacao; off = nunca."""
    a = _D().switch("logistics.acoplamento")
    return a == "on" or (a == "auto" and transport() == "tripulacao")


# ----------------------------------------------------------------------------- dados
def res_key(res):
    """Chave do recurso no spec (he, ap, ..., msl_he, slug) = sufixo dos nomes Estoque_<k> / FitaEntra_<k>."""
    D = _D()
    r = D.RES_BY_ID.get(res)
    if r:
        return r["spec_key"]
    for s in D.SPEC["resources"]:
        if s["id"] == res:
            return s["key"]
    raise ValueError(f"recurso {res} fora do spec (sem chave de paiol)")


def _pick(d, prefix):
    """Valor da chave de d que comeca com prefix (o spec usa chaves com comentario: 'empurra (logistics...)')."""
    for k, v in (d or {}).items():
        if k == prefix or k.startswith(prefix + " "):
            return v
    return None


def spec_logistica(g):
    """Bloco 'logistica' do spec da maquina: g['logistica'] ou, sem ele, o do spec pelo ID (armas, defesas, PEM,
    lancadores, Carregador do Tupa, fabricas)."""
    if g.get("logistica"):
        return g["logistica"]
    D = _D()
    pid = g.get("id")
    if pid == RAIL_LOADER:
        return D.RAIL.get("logistica") or {}
    for w in list(D.SPEC.get("weapons") or []) + list(D.SPEC.get("defenses") or []) + \
            list((D.SPEC.get("pem_weapons") or {}).get("weapons") or []) + list(D.SPEC.get("factories") or []) + \
            list(D.MSPEC.get("launchers") or []):
        if w.get("id") == pid:
            return w.get("logistica") or {}
    return {}


def kind_of(g):
    """'factory' | 'paiol' | 'arma' (arma = canhao, defesa, PEM, lancador, Carregador do Tupa)."""
    k = g.get("kind")
    if k == "factory" or g.get("recipes"):
        return "factory"
    if k == "paiol" or "_paiol_" in str(g.get("id", "")):
        return "paiol"
    return "arma"


def feed_modes(g, comp=None):
    """Modos de entrada da maquina: [{index, key, res, target, q_puxa, q_acop, toggle}] (indice da tabela, nunca a
    posicao). Fonte: g['modes'] (cruzado com o spec) ou o bloco empurra do spec. toggle = ModeToggle_<i> se ja esta
    em comp (seletor) ou None (arma de um modo so)."""
    lg = spec_logistica(g)
    tp = _pick(lg, "teleporte") or {}
    push = _pick(tp, "empurra") or []
    pull = (_pick(tp, "puxa") or {}).get("per_mode") or []
    acop = _pick(lg, "acoplamento") or {}
    acop_pm = acop.get("per_mode") if isinstance(acop, dict) else None
    push_by = {e.get("index"): e for e in push if isinstance(e, dict)}
    pull_by = {e.get("index"): e for e in pull if isinstance(e, dict)}
    acop_by = {e.get("index"): e for e in (acop_pm or []) if isinstance(e, dict)}
    who = g.get("id") or g.get("short") or "?"
    src = []
    if g.get("modes"):
        for m in g["modes"]:
            i = m["index"] if "index" in m else m["mode"]
            res = m.get("res") or m.get("resource")
            src.append((i, res, m))
    else:
        for e in push:
            src.append((e["index"], e["resource"], {}))
    out = []
    for i, res, m in src:
        key = res_key(res)
        e = push_by.get(i) or {}
        if e and e.get("key") != key:
            raise ValueError(f"{who}: modo {i} usa {res} ({key}) e o spec da logistica diz {e.get('key')}")
        target = m.get("fita_target") or (e.get(f"FitaEntra_{key}") or {}).get("ComponentID") or f"MagStorage_{i}"
        pe = (pull_by.get(i) or {}).get(f"Alimentador_{i}") or {}
        ae = (acop_by.get(i) or {}).get(f"AlimentadorAcoplado_{i}") or {}
        q_puxa = int(m.get("feed_q") or pe.get("FromQuantity") or 1)
        q_acop = int(ae.get("FromQuantity") or m.get("feed_q") or 1)
        tog = f"ModeToggle_{i}"
        out.append({"index": i, "key": key, "res": res, "target": target, "q_puxa": q_puxa, "q_acop": q_acop,
                    "toggle": tog if (comp is not None and tog in comp) else None})
    keys = [m["key"] for m in out]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{who}: dois modos com o mesmo recurso {keys} (FitaEntra_<chave> seria duplicado)")
    if comp is not None and len(out) > 1 and any(m["toggle"] is None for m in out):
        raise ValueError(f"{who}: {len(out)} modos sem ModeToggle_<i> em comp: crie o seletor ANTES do weapon_intake")
    return out


def acoplamento_cell(g):
    """Celula logo atras da peca (PartLocation do paiol acoplado): spec acoplamento.cell ou g['acoplamento_cell']."""
    if g.get("acoplamento_cell"):
        return list(g["acoplamento_cell"])
    acop = _pick(spec_logistica(g), "acoplamento") or {}
    if isinstance(acop, dict) and acop.get("cell"):
        return list(acop["cell"])
    w, h = g["size"]
    return [0, h]


def fx_location(g):
    """Onde toca a animacao da Fita: g['fita_fx_location'] ou, no Carregador do Tupa, o do spec; nas armas com torre
    o centro da fileira de TRAS [w/2, h - 0.5] (roof_doodads fica sob roof_turrets; ADDENDUM WP05)."""
    if g.get("fita_fx_location"):
        return list(g["fita_fx_location"])
    if g.get("id") == RAIL_LOADER:
        loc = ((_D().RAIL.get("parts") or {}).get("carregador") or {}).get("fita_fx_location")
        if loc:
            return list(loc)
    w, h = g["size"]
    return [w / 2, h - 0.5]


def avisa_areas(w, h):
    """BuffArea do aviso para a Fita (luz verde) em cruz: as celulas vizinhas das 4 bordas, sem as quinas."""
    return [-1, 0, w + 2, h], [0, -1, w, h + 2]


# ----------------------------------------------------------------------------- blocos comuns
def has_comp(comp, name):
    """O componente existe na peca (no topo ou dentro de um ToggledComponents)?"""
    if name in comp:
        return True
    for v in comp.values():
        if isinstance(v, dict) and v.get("Type") == "ToggledComponents" and name in (v.get("Components") or {}):
            return True
    return False


def first_comp(comp, names, who, what):
    """Primeiro nome de names que existe na peca; nenhum = erro claro no build (no jogo, um ID de componente que nao
    existe derruba o carregamento)."""
    for n in names:
        if has_comp(comp, n):
            return n
    raise ValueError(f"{who}: {what}: a peca nao tem {' nem '.join(names)} (crie antes de chamar o intake)")


def _put(comp, name, value):
    """Poe um componente novo; nome repetido (de outro modulo) e erro, para nunca sobrescrever calado."""
    if name in comp:
        raise ValueError(f"componente {name} ja existe na peca (colisao com a logistica da Fita)")
    comp[name] = value


def fx_files(which, kind):
    """../bs_fita_fx/cartucho_<which>1..8.png (kind 'cartucho') ou brilho_<which>1..8.png ('brilho')."""
    return [Q(f"../{FX_DIR}/{kind}_{which}{n}.png") for n in range(1, FX_FRAMES + 1)]


def fx_graphics(which, toggle, location, size=(1, 1)):
    """Graphics da animacao da Fita (which = 'entra' | 'sai'): cartuchos em roof_doodads + brilho em lights_add,
    8 quadros de 0,075 s (kit TF/parts/bs2f_arma/bs2f_arma.rules:142-195)."""
    sz = [round(float(size[0]), 4), round(float(size[1]), 4)]
    return {
        "Type": "Graphics", "Location": [round(float(location[0]), 4), round(float(location[1]), 4)],
        "OperationalToggle": toggle,
        "OperationalRoofDoodad": {"Layer": Q("roof_doodads"), "DamageLevels": [
            {"AnimationFiles": fx_files(which, "cartucho"), "Size": sz, "AnimationInterval": FX_INTERVAL}]},
        "OperationalLighting": {"Layer": Q("lights_add"), "DamageLevels": [
            {"AnimationFiles": fx_files(which, "brilho"), "Size": sz, "AnimationInterval": FX_INTERVAL}]},
    }


def recent_timer(trigger):
    """Timer 'aconteceu ha pouco' (vanilla chaingun.rules:197-207; kit TesteFita): ligado 0,6 s apos o gatilho."""
    return {"Type": "Timer", "Duration": ANIM_TIMER, "StartTrigger": trigger, "ResetTrigger": trigger,
            "StartExpired": True, "InvertToggle": True}


def host(comp, w, h):
    """Componentes de toda maquina da Fita (teleporte): FitaLigada (+ FitaGrudada/FitaEmbutida com o botao) e o aviso
    para a Fita vizinha (luz verde, art.fita_luz = ack). Idempotente (fabrica de varias receitas)."""
    if "FitaLigada" in comp:
        return
    comp[comment("---- Fita de Alimentacao: maquina ligada na rede da Fita (kit TesteFita) ----")] = None
    if embutida():
        # botao 'Fita embutida' (naves sem espaco): FitaLigada = qualquer um dos dois (factory_uranium.rules:150)
        _put(comp, "FitaGrudada", {"Type": "BuffToggle", "BuffType": BUFF_LINK})
        _put(comp, "FitaEmbutida", {"Type": "UIToggle", "ToggleID": Q(TOGGLE_EMBUTIDA), "Default": 0,
                                    "AlwaysAllowInBuildMode": True, "RequiresCommand": False})
        _put(comp, "FitaLigada", {"Type": "MultiToggle", "Toggles": ["FitaGrudada", "FitaEmbutida"], "Mode": "Any"})
    else:
        # a propria BuffToggle (kit bs2f_*.rules: FitaLigada { Type = BuffToggle })
        _put(comp, "FitaLigada", {"Type": "BuffToggle", "BuffType": BUFF_LINK})
    if luz_ack():
        a_h, a_v = avisa_areas(w, h)
        _put(comp, "AvisaFitaHorizontal", {"Type": "AreaBuffProvider", "BuffType": BUFF_ACK, "BuffArea": a_h,
                                           "Criteria": {"Category": CAT_FITA}})
        _put(comp, "AvisaFitaVertical", {"Type": "AreaBuffProvider", "BuffType": BUFF_ACK, "BuffArea": a_v,
                                         "Criteria": {"Category": CAT_FITA}})


def desligado(comp):
    """StaticToggle sempre desligado: ancora dos MultiResourceStorage (estado vanilla engine_room.rules:113-125)."""
    if "Desligado" not in comp:
        comp["Desligado"] = {"Type": "StaticToggle", "ToggleOn": False}


def via_paiois(key, provider=None):
    """ViaBuffs que junta os EntraPaiol_<key> dos paiois: jeito B (OutgoingBuffProviders [provider]) ou A
    (IncomingBuffTypes [BulletStrike_FitaRede])."""
    if provider:
        return {"OutgoingBuffProviders": [provider], "ComponentIDs": [f"EntraPaiol_{key}"]}
    return {"IncomingBuffTypes": [BUFF_REDE], "ComponentIDs": [f"EntraPaiol_{key}"]}


def acoplado_proxy(res, key, cell):
    """ResourceStorageProxy para o Estoque_<key> do paiol encostado na celula (molde SW chaingun_magazine.rules:163-200;
    so a Category do TIPO, J2R3-22)."""
    return {"Type": "ResourceStorageProxy", "ResourceType": res, "PartLocation": list(cell),
            "ProxyableComponents": [{"PartCriteria": {"Category": f"bs_paiol_{key}"}, "ComponentID": f"Estoque_{key}"}]}


# ----------------------------------------------------------------------------- gancho: campos da peca
def part_fields(g, ctx=None):
    """{TypeCategories_add, ReceivableBuffs_add} que o transporte pede na peca g (arma, fabrica ou paiol)."""
    t = transport()
    if t in ("rede", "gemea"):
        return C.call(beltnet(), "part_fields", g, ctx) or {"TypeCategories_add": [], "ReceivableBuffs_add": []}
    if t != "teleporte":
        return {"TypeCategories_add": [], "ReceivableBuffs_add": []}
    k = kind_of(g)
    if k == "factory":
        # jeito B: a fabrica so precisa da Fita (ela da o FitaFab); jeito A: recebe o FitaRede dos paiois
        buffs = [BUFF_LINK] + ([BUFF_REDE] if fita_fabrica() == "A" else [])
    elif k == "paiol":
        # o paiol DA o FitaRede (nao recebe): Fita + empurrao das fabricas (jeito B)
        buffs = [BUFF_LINK, BUFF_FAB]
    else:
        # arma: Fita + FitaRede dos paiois (os dois sentidos do ViaBuffs; kit bs2f_arma*.rules)
        buffs = [BUFF_LINK, BUFF_REDE]
    return {"TypeCategories_add": [CAT_MAQUINA], "ReceivableBuffs_add": buffs}


# ----------------------------------------------------------------------------- gancho: entrada da arma
def weapon_intake(comp, g, ctx=None):
    """Entrada da municao na arma g (todos os modos): Fita (teleporte) e/ou paiol acoplado (acoplamento)."""
    t = transport()
    if t in ("rede", "gemea"):
        return C.call(beltnet(), "weapon_intake", comp, g, ctx)
    modes = feed_modes(g, comp)
    if not modes:
        return None
    w, h = g["size"]
    who = g.get("id") or g.get("short") or "?"
    for m in modes:
        first_comp(comp, [m["target"]], who, f"estoque do modo {m['index']} (alvo da Fita / do acoplamento)")
    if t == "teleporte":
        host(comp, w, h)
        if fita_arma() == "puxa":
            comp[comment("---- Fita: a arma PUXA dos paiois com Fita (kit bs2f_arma_puxa.rules) ----")] = None
            desligado(comp)
        else:
            comp[comment("---- Fita: os paiois com Fita EMPURRAM para ca (kit bs2f_arma.rules; vanilla "
                         "engine_room.rules:99-127) ----")] = None
        for m in modes:
            i, k = m["index"], m["key"]
            gate = "FitaLigada"
            if m["toggle"]:
                # so o tipo escolhido recebe pela Fita (TesteFita A7: um tipo nunca vira outro)
                gate = f"Alimenta_{i}"
                _put(comp, gate, {"Type": "MultiToggle", "Toggles": [m["toggle"], "FitaLigada"], "Mode": "All"})
            if fita_arma() == "puxa":
                _put(comp, f"AncoraPaiol_{i}", {"Type": "ResourceStorageProxy", "ResourceType": m["res"],
                                                "ComponentID": m["target"], "ProxyToggle": "Desligado"})
                _put(comp, f"DosPaiois_{i}", {
                    "Type": "MultiResourceStorage", "ResourceType": m["res"], "ResourceStorages": [f"AncoraPaiol_{i}"],
                    "ViaBuffs": {"IncomingBuffTypes": [BUFF_REDE], "ComponentIDs": [f"Estoque_{k}"]},
                    "RemoveMode": "PrioritizeMostResources"})
                _put(comp, f"Alimentador_{i}", {
                    "Type": "ResourceConverter", "OperationalToggle": gate, "FromStorage": f"DosPaiois_{i}",
                    "FromQuantity": m["q_puxa"], "MinFromQuantityForConversion": 1, "ToStorage": m["target"],
                    "ToQuantity": m["q_puxa"], "Interval": FEED_INTERVAL})
            else:
                _put(comp, f"FitaEntra_{k}", {"Type": "ResourceStorageProxy", "ResourceType": m["res"],
                                              "ComponentID": m["target"], "ProxyToggle": gate})
        # animacao 'cartuchos entrando' a cada aumento do estoque (kit: ValueChangeTrigger + Timer)
        comp[comment("---- Fita: cartuchos entrando (art3d/bs_fita_fx) ----")] = None
        trigs = []
        for m in modes:
            nm = f"Entrou_{m['index']}"
            _put(comp, nm, {"Type": "ValueChangeTrigger", "ValueSource": m["target"], "TriggerOnDecrease": False})
            trigs.append(nm)
        trig = trigs[0]
        if len(trigs) > 1:
            trig = "EntrouAlgum"
            _put(comp, trig, {"Type": "MultiTrigger", "Triggers": trigs})
        _put(comp, "EntrandoRecente", recent_timer(trig))
        _put(comp, "AnimEntrando", fx_graphics("entra", "EntrandoRecente", fx_location(g)))
    if acoplamento_on():
        cell = acoplamento_cell(g)
        comp[comment(f"---- paiol acoplado na celula {cell} (SW chaingun_magazine.rules:163-200; T-ACOPLA) ----")] = None
        for m in modes:
            i, k = m["index"], m["key"]
            # modo escolhido (seletor) ou, arma de um modo so, o consumo de comando (pronta para operar)
            gate = m["toggle"] or first_comp(comp, ["CommandConsumptionToggle", "PowerToggle"], who,
                                             "toggle do alimentador acoplado")
            _put(comp, f"PaiolAcoplado_{i}", acoplado_proxy(m["res"], k, cell))
            _put(comp, f"AlimentadorAcoplado_{i}", {
                "Type": "ResourceConverter", "OperationalToggle": gate,
                "FromStorage": f"PaiolAcoplado_{i}", "FromQuantity": m["q_acop"], "MinFromQuantityForConversion": 1,
                "ToStorage": m["target"], "ToQuantity": m["q_acop"], "Interval": FEED_INTERVAL})
    return None


def weapon_return(comp, g, ctx=None):
    """Devolucao (logistics.devolucao_arma = on, so teleporte e so arma com seletor): a sobra dos modos NAO escolhidos
    volta ao paiol do tipo pelo mesmo jeito da fabrica (logistics.fita_fabrica)."""
    t = transport()
    if t in ("rede", "gemea"):
        return C.call(beltnet(), "weapon_return", comp, g, ctx)
    if not devolucao():
        return None
    modes = feed_modes(g, comp)
    sel = [m for m in modes if m["toggle"]]
    if len(sel) < 2:
        return None
    w, h = g["size"]
    host(comp, w, h)
    desligado(comp)
    comp[comment("---- Fita: devolucao do modo nao escolhido ao paiol (logistics.devolucao_arma) ----")] = None
    provider = None
    if fita_fabrica() == "B":
        provider = "RedeDevolve"
        _put(comp, provider, {"Type": "GridBuffProvider", "BuffType": BUFF_FAB, "BuffAmount": 1,
                              "GridDistance": alcance(), "OperationalToggle": "FitaLigada"})
    for m in sel:
        i, k = m["index"], m["key"]
        mt = comp[m["toggle"]]
        others = [x["index"] for x in sel if x["index"] != i]
        _put(comp, f"NaoModo_{i}", {"Type": "ModeToggle", "Mode": mt["Mode"], "OnModes": others})
        _put(comp, f"Devolvendo_{i}", {"Type": "MultiToggle", "Toggles": [f"NaoModo_{i}", "FitaLigada"], "Mode": "All"})
        _put(comp, f"AncoraDevolve_{i}", {"Type": "ResourceStorageProxy", "ResourceType": m["res"],
                                          "ComponentID": m["target"], "ProxyToggle": "Desligado"})
        _put(comp, f"Devolucao_{i}", {"Type": "MultiResourceStorage", "ResourceType": m["res"],
                                      "ResourceStorages": [f"AncoraDevolve_{i}"], "ViaBuffs": via_paiois(k, provider),
                                      "AddMode": "PrioritizeLeastResources"})
        _put(comp, f"Devolve_{i}", {"Type": "ResourceConverter", "OperationalToggle": f"Devolvendo_{i}",
                                    "FromStorage": m["target"], "FromQuantity": DEVOLVE_Q,
                                    "MinFromQuantityForConversion": 1, "ToStorage": f"Devolucao_{i}",
                                    "ToQuantity": DEVOLVE_Q, "Interval": FEED_INTERVAL})
    return None


# ----------------------------------------------------------------------------- gancho: saida da fabrica
def envio_q(f, key):
    """q do Envio_<key> (por 0,1 s) de SPEC.factories[].logistica.teleporte.per_recipe."""
    tp = _pick(spec_logistica(f), "teleporte") or {}
    for e in tp.get("per_recipe") or []:
        if e.get("key") == key or e.get("recipe") == key:
            env = e.get(f"Envio_{key}") or {}
            return int(env.get("FromQuantity") or 1)
    return 1


def factory_acop_cell(f, key):
    acop = _pick(spec_logistica(f), "acoplamento") or []
    for e in acop if isinstance(acop, list) else []:
        if e.get("recipe") == key:
            return list(e["cell"])
    return None


def factory_output(comp, f, rc, ctx=None):
    """Saida da receita rc da fabrica f: teleporte (jeito B padrao / A) para os paiois com Fita, e/ou o paiol acoplado
    na saida. rc: dict do factory.py (key, saida, output_resource, first, last, center...)."""
    t = transport()
    if t in ("rede", "gemea"):
        return C.call(beltnet(), "factory_output", comp, f, rc, ctx)
    k = rc.get("key") or rc.get("recipe")
    res = rc.get("output_resource")
    saida = rc.get("saida") or f"Saida_{k}"
    w, h = f["size"]
    who = f.get("id") or "?"
    if res_key(res) != k:
        raise ValueError(f"{who}: receita {k} produz {res} ({res_key(res)}): o nome da saida precisa ser o tipo")
    first_comp(comp, [saida], who, f"grade de saida da receita {k}")
    q = envio_q(f, k)
    if t == "teleporte":
        host(comp, w, h)
        desligado(comp)
        provider = None
        if fita_fabrica() == "B" and "RedeFab" not in comp:
            # a fabrica com Fita da o FitaFab ao navio (SW hyperdrive_med.rules:80-87, GridDistance 1000)
            comp[comment("---- Fita, jeito B: a fabrica empurra para os paiois (SW hypermatter_reactor_2x2.rules:"
                         "256-292; kit bs2f_fab_bala_b.rules) ----")] = None
            _put(comp, "RedeFab", {"Type": "GridBuffProvider", "BuffType": BUFF_FAB, "BuffAmount": 1,
                                   "GridDistance": alcance(), "OperationalToggle": "FitaLigada"})
        if fita_fabrica() == "B":
            provider = "RedeFab"
        comp[comment(f"---- Fita: receita {k} -> paiois de {k} com Fita ----")] = None
        _put(comp, f"AncoraSaida_{k}", {"Type": "ResourceStorageProxy", "ResourceType": res, "ComponentID": saida,
                                        "ProxyToggle": "Desligado"})
        _put(comp, f"ParaPaiois_{k}", {"Type": "MultiResourceStorage", "ResourceType": res,
                                       "ResourceStorages": [f"AncoraSaida_{k}"], "ViaBuffs": via_paiois(k, provider),
                                       "AddMode": "PrioritizeLeastResources"})
        _put(comp, f"Envio_{k}", {"Type": "ResourceConverter", "OperationalToggle": "FitaLigada", "FromStorage": saida,
                                  "FromQuantity": q, "MinFromQuantityForConversion": 1,
                                  "ToStorage": f"ParaPaiois_{k}", "ToQuantity": q, "Interval": FEED_INTERVAL})
        if rc.get("last", True):
            envios = [n for n in comp if isinstance(n, str) and n.startswith("Envio_")]
            trig = envios[0]
            if len(envios) > 1:
                trig = "Enviou"
                _put(comp, trig, {"Type": "MultiTrigger", "Triggers": envios})
            comp[comment("---- Fita: cartuchos saindo (art3d/bs_fita_fx), uma vez por fabrica ----")] = None
            _put(comp, "SaindoRecente", recent_timer(trig))
            _put(comp, "AnimSaindo", fx_graphics("sai", "SaindoRecente", rc.get("center") or [w / 2, h / 2]))
    if acoplamento_on():
        cell = factory_acop_cell(f, k)
        if cell is None:
            raise ValueError(f"{f.get('id')}: receita {k} sem celula de acoplamento no spec")
        comp[comment(f"---- paiol acoplado na saida {k} (celula {cell}; T-ACOPLA) ----")] = None
        _put(comp, f"EntregaAcoplada_{k}", acoplado_proxy(res, k, cell))
        # mesma vazao do Envio_<k> (q por 0,1 s, SPEC.fita_teleporte.rates): a grade nao enche com o paiol encostado
        gate = first_comp(comp, ["PowerToggle"], who, "toggle do empurrao acoplado")
        _put(comp, f"EmpurraAcoplado_{k}", {"Type": "ResourceConverter", "OperationalToggle": gate,
                                            "FromStorage": saida, "FromQuantity": q, "MinFromQuantityForConversion": 1,
                                            "ToStorage": f"EntregaAcoplada_{k}", "ToQuantity": q,
                                            "Interval": FEED_INTERVAL})
    return None


# ----------------------------------------------------------------------------- conferencia (selfcheck)
def parse_rules(path):
    """Arvore do .rules (parser do tools/rules_lint.py) ou None."""
    import rules_lint as RL
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    root, errs, _w = RL.parse_text(text, RL.RFile("fs", path, path))
    return root if not errs else None


def child(node, name):
    if node is None:
        return None
    return next((c for c in node.children if c.name == name), None)


def plain(v):
    return (v or "").strip().strip('"')


def val(node, name):
    c = child(node, name)
    return plain(c.value) if c is not None and c.kind == "value" else None


def lst(node, name):
    c = child(node, name)
    if c is None or c.kind != "list":
        return None
    return [plain(x.value) for x in c.children if x.kind == "value"]


def part_info(path):
    """(ID, {componente: no}, no da Part, TypeCategories) de parts/<x>/<x>.rules (componentes de ToggledComponents
    tambem entram, com o nome proprio)."""
    root = parse_rules(path)
    if root is None:
        return None
    part = child(root, "Part")
    if part is None:
        return None
    comps = {}

    def walk(cn):
        for c in cn.children:
            if not c.name or c.kind not in ("group", "inherit"):
                continue
            comps[c.name] = c
            sub = child(c, "Components")
            if sub is not None:
                walk(sub)
    cn = child(part, "Components")
    if cn is not None:
        walk(cn)
    cats = lst(part, "TypeCategories") or []
    return val(part, "ID"), comps, part, cats


def mod_parts(mod_dir):
    """{ID: (arquivo, comps, part, cats)} de todas as pecas em <mod>/parts/*/*.rules."""
    out = {}
    pdir = os.path.join(mod_dir, "parts")
    if not os.path.isdir(pdir):
        return out
    for d in sorted(os.listdir(pdir)):
        p = os.path.join(pdir, d, f"{d}.rules")
        info = part_info(p)
        if info and info[0]:
            out[info[0]] = (p, info[1], info[2], info[3])
    return out


def machines():
    """{ID: g} das maquinas que entram na Fita (armas, defesas, PEM, lancadores, Carregador) pelos dados do build."""
    D = _D()
    out = {}
    for g in list(D.GUNS) + list(D.DEFENSES):
        out[g["id"]] = g
    for p in D.PEM:
        out[p["id"]] = p
    for lch in getattr(D, "LAUNCHERS", []) or []:
        out[lch["id"]] = lch
    # rail.loader_intake acoplamento/tripulacao (WP09): o bsgen.railgun liga o Carregador sozinho, fora da Fita
    if D.RAIL_ENABLED and D.switch("rail.loader_intake") == "auto":
        car = dict(((D.RAIL.get("parts") or {}).get("carregador") or {}))
        if car.get("id"):
            car["logistica"] = D.RAIL.get("logistica")
            out[car["id"]] = car
    return out


def selfcheck(mod_dir, SPEC=None):
    """Confere as maquinas ESCRITAS contra o transporte e o spec (lista de problemas; vazia = OK)."""
    D = _D()
    probs = []
    parts = mod_parts(mod_dir)
    t = transport()
    arma = fita_arma()
    fab = fita_fabrica()
    paiol_cats = set()
    estoques = set()
    all_comps = set()
    for pid, (path, comps, part, cats) in parts.items():
        all_comps |= set(comps)
        if "bs_paiol" in cats:
            paiol_cats |= {c for c in cats if c.startswith("bs_paiol_")}
            estoques |= {n for n in comps if n.startswith("Estoque_")}
    mach = machines()
    for pid, g in mach.items():
        if pid not in parts:
            continue
        path, comps, part, cats = parts[pid]
        who = pid.split(".", 1)[1]
        try:
            modes = feed_modes(g)
        except ValueError as e:
            probs.append(f"{who}: {e}")
            continue
        buffs = lst(part, "ReceivableBuffs") or []
        if t == "teleporte":
            if CAT_MAQUINA not in cats:
                probs.append(f"{who}: TypeCategories sem {CAT_MAQUINA}")
            for b in (BUFF_LINK, BUFF_REDE):
                if b not in buffs:
                    probs.append(f"{who}: ReceivableBuffs sem {b}")
            if "FitaLigada" not in comps:
                probs.append(f"{who}: sem FitaLigada")
            for m in modes:
                i, k = m["index"], m["key"]
                if arma == "puxa":
                    al = comps.get(f"Alimentador_{i}")
                    if comps.get(f"DosPaiois_{i}") is None or al is None:
                        probs.append(f"{who}: puxa sem DosPaiois_{i} / Alimentador_{i}")
                    elif val(al, "FromQuantity") != str(m["q_puxa"]):
                        probs.append(f"{who}: Alimentador_{i} FromQuantity {val(al, 'FromQuantity')}, spec {m['q_puxa']}")
                else:
                    fe = comps.get(f"FitaEntra_{k}")
                    if fe is None:
                        probs.append(f"{who}: teleporte sem FitaEntra_{k} (modo {i})")
                    elif val(fe, "ComponentID") != m["target"] or val(fe, "ResourceType") != m["res"]:
                        probs.append(f"{who}: FitaEntra_{k} -> {val(fe, 'ComponentID')} ({val(fe, 'ResourceType')}), "
                                     f"esperado {m['target']} ({m['res']})")
                    elif m["target"] not in comps:
                        probs.append(f"{who}: FitaEntra_{k} aponta para {m['target']}, que nao existe na peca")
            if luz_ack() and "AvisaFitaHorizontal" not in comps:
                probs.append(f"{who}: sem AvisaFitaHorizontal (art.fita_luz = ack)")
            if not luz_ack() and "AvisaFitaHorizontal" in comps:
                probs.append(f"{who}: AvisaFita* com art.fita_luz = sempre")
        else:
            bad = [n for n in comps if re.match(r"(FitaEntra_|FitaLigada$|FitaGrudada$|DosPaiois_|AvisaFita)", n)]
            if bad:
                probs.append(f"{who}: componentes da Fita fora do teleporte: {bad[:4]}")
            if any(b in buffs for b in BUFFS):
                probs.append(f"{who}: buff da Fita em ReceivableBuffs fora do teleporte")
        if acoplamento_on():
            for m in modes:
                i, k = m["index"], m["key"]
                pa = comps.get(f"PaiolAcoplado_{i}")
                if pa is None or comps.get(f"AlimentadorAcoplado_{i}") is None:
                    probs.append(f"{who}: acoplamento sem PaiolAcoplado_{i} / AlimentadorAcoplado_{i}")
        elif any(n.startswith("PaiolAcoplado_") for n in comps):
            probs.append(f"{who}: PaiolAcoplado_* com logistics.acoplamento desligado")
    # fabricas
    for f in D.FACTORIES:
        if f["id"] not in parts:
            continue
        path, comps, part, cats = parts[f["id"]]
        who = f["short"]
        buffs = lst(part, "ReceivableBuffs") or []
        for r in f["recipes"]:
            k = r["recipe"]
            if t == "teleporte":
                env = comps.get(f"Envio_{k}")
                q = envio_q(f, k)
                if env is None:
                    probs.append(f"{who}: teleporte sem Envio_{k}")
                elif val(env, "FromQuantity") != str(q) or val(env, "ToQuantity") != str(q):
                    probs.append(f"{who}: Envio_{k} q {val(env, 'FromQuantity')}/{val(env, 'ToQuantity')}, spec {q}")
                pp = comps.get(f"ParaPaiois_{k}")
                via = child(pp, "ViaBuffs") if pp is not None else None
                if via is None:
                    probs.append(f"{who}: sem ParaPaiois_{k} com ViaBuffs")
                elif fab == "B" and lst(via, "OutgoingBuffProviders") != ["RedeFab"]:
                    probs.append(f"{who}: ParaPaiois_{k} sem OutgoingBuffProviders [RedeFab] (jeito B)")
                elif fab == "A" and lst(via, "IncomingBuffTypes") != [BUFF_REDE]:
                    probs.append(f"{who}: ParaPaiois_{k} sem IncomingBuffTypes [{BUFF_REDE}] (jeito A)")
            if acoplamento_on() and comps.get(f"EntregaAcoplada_{k}") is None:
                probs.append(f"{who}: acoplamento sem EntregaAcoplada_{k}")
        if t == "teleporte":
            if fab == "B" and "RedeFab" not in comps:
                probs.append(f"{who}: jeito B sem RedeFab")
            if CAT_MAQUINA not in cats or BUFF_LINK not in buffs:
                probs.append(f"{who}: sem {CAT_MAQUINA} / {BUFF_LINK}")
            if fab == "A" and BUFF_REDE not in buffs:
                probs.append(f"{who}: jeito A sem {BUFF_REDE} em ReceivableBuffs")
        elif any(n.startswith(("Envio_", "ParaPaiois_")) or n == "RedeFab" for n in comps):
            probs.append(f"{who}: componentes da Fita fora do teleporte")
    # varredura geral: categorias, ViaBuffs e nada de esteira
    for pid, (path, comps, part, cats) in parts.items():
        who = pid.split(".", 1)[1]
        for name, node in comps.items():
            pcs = child(node, "ProxyableComponents")
            for el in (pcs.children if pcs is not None else []):
                crit = child(el, "PartCriteria")
                cat = val(crit, "Category")
                if cat and cat.startswith("bs_paiol"):
                    if not re.fullmatch(r"bs_paiol_[a-z]+(_[a-z]+)?", cat) or cat in (
                            "bs_paiol_cartuchos", "bs_paiol_celulas", "bs_paiol_misseis", "bs_paiol_projeteis"):
                        probs.append(f"{who}: {name} procura a categoria {cat} (tem que ser a do TIPO bs_paiol_<chave>)")
                    elif cat not in paiol_cats:
                        probs.append(f"{who}: {name} procura {cat}, que nenhum paiol escrito tem")
                    cid = val(el, "ComponentID")
                    if cid and cid not in estoques:
                        probs.append(f"{who}: {name} procura {cid}, que nenhum paiol escrito tem")
            via = child(node, "ViaBuffs")
            for cid in (lst(via, "ComponentIDs") or []) if via is not None else []:
                if cid not in all_comps:
                    probs.append(f"{who}: {name} ViaBuffs cita {cid}, que nao existe em nenhuma peca escrita")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        if t in ("teleporte", "tripulacao") and re.search(r"\bNetworkResource\w*", text):
            probs.append(f"{who}: NetworkResource* com logistics.transport = {t} (esteira so na reserva WP15)")
        if t in ("teleporte", "tripulacao") and re.search(rf"\b{C.AUTHOR}\.bs_belt", text):
            probs.append(f"{who}: porta de esteira (bs_belt) com logistics.transport = {t}")
    return probs
