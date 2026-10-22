"""Logistica principal do Bullet Strike 2.0 (dono: WP05; modulo de CONTEUDO, API 2): a Fita de Alimentacao, os paiois,
os buffs da Fita e a arte publicada (parts/bs_fita, parts/bs_fita_fx, parts/bs_paiol_comum, parts/bs_placas).

Ganchos do build_mod: write (buffs/bs_fita_buffs.rules), parts (Fita + paiois), toggles (bs_fita_embutida), strings,
mod_actions (Overrides dos buffs em <./Data/buffs/buffs.rules>) e selfcheck. A entrada/saida das OUTRAS maquinas
(armas, fabricas) e do bsgen.intake (seam), que este modulo reaproveita (host, animacao, nomes).

logistics.transport (SPEC.fita_teleporte; ADDENDUM_2_0 G1):
  * teleporte (build BulletStrike/): a peca Fita rafaeltessaro.bs_fita (1x1, nao giratoria, sem paredes; AreaBuffProvider
    BulletStrike_FitaLink em cruz para Category bs_fita_maquina; luz verde pelo BuffToggle BulletStrike_FitaAck) e os
    paiois SELADOS (thermal_battery.rules:22-25): Estoque_<k> por tipo (fora de qualquer bloco alternado: trocar o tipo
    nunca apaga estoque), EntraPaiol_<k> (proxy com ProxyToggle Aceita_<k> = EhTipo_<k> E FitaLigada; alvo do
    Envio_<k> das fabricas), Rede (GridBuffProvider BulletStrike_FitaRede GridDistance = logistics.fita_alcance) e,
    com fita_arma = empurra, AncoraArmas_<k> + ParaArmas_<k> {ViaBuffs OutgoingBuffProviders [Rede]; ComponentIDs
    [FitaEntra_<k>]} + Empurra_<k> (q de SPEC.paiol.parts[].teleporte.push_q_per_0_1s) para TODO tipo guardado
    (escolhido ou nao) que alguma arma deste build usa (kit testes/BulletStrike_TesteFita bs2f_paiol_bala.rules;
    vanilla engine_room.rules:99-127);
  * tripulacao (build testes/BulletStrike_SemFita): sala de municao blindada caminhavel (SPEC.paiol.components_crew_mode;
    vanilla power_storage.rules:86-162): Estoque_<k> SuppliesResources + pickup de uma pilha + IsIntermediateStorage,
    Consumidor_<k> Storage_Supply com limiar floor(Max/2); seletor = SuppliesResourcesToggle/OperationalToggle EhTipo_<k>
    + AllowNonOperationalMinPriorityDelivery false no consumidor (sem ele a tripulacao ociosa enche o tipo fora do
    botao, que nunca mais sai; SW chaingun_magazine.rules:123) (com paiol_seletor = nenhum esses campos sao OMITIDOS,
    J2R2-MED);
  * rede / gemea (WP15, esteira fisica): so com o bsgen.belt_net (paiol_net); sem ele o bs_data ja devolveu
    'tripulacao' (J2R3-19) e aqui fica so a conferencia.
Comum: seletor UIToggle da familia (paiol_seletor = botao) ou uma peca por tipo (nenhum: SPEC.paiol.
parts_when_selector_nenhum), barra sob a vida (ProgressBar), medidor do teto (ResourceSprites, 5/8/10 niveis), placa do
tipo, contador de 4 digitos (logistics.paiol_contador; padrao desligado), cook-off proprio por tipo escalado pelo
estoque (thermal_battery.rules:94-122) e indicadores.
"""

import os
import shutil

from rules_dsl import Q, comment, render
from bsgen import common as C
from bsgen import intake as I

API = 2

# variantes adiadas (ADDENDUM G11) implementadas aqui (o intake declara as dele)
VARIANTS = {"logistics.paiol_seletor": ("nenhum",), "logistics.paiol_contador": (True,)}

FITA_DIR = "bs_fita"
PLACAS_DIR = "bs_placas"
BUFFS_FILE = "buffs/bs_fita_buffs.rules"
FAMILY_TOGGLE_COMP = "TipoMunicao"
GREEN = [110, 230, 120]

# rotulos curtos por tipo (pt, en) e as unidades por familia (pt, en)
KIND_LABEL = {
    "he": ("HE", "HE"), "ap": ("AP", "AP"), "sap": ("SAP", "SAP"), "ac": ("AC", "AC"), "frag": ("FRAG", "FRAG"),
    "plasma": ("Plasma", "Plasma"), "pem": ("PEM", "EMP"),
    "msl_he": ("HE", "HE"), "msl_cluster": ("Submunição", "Cluster"), "msl_emp": ("PEM", "EMP"),
    "msl_nuke": ("Nuclear", "Nuclear"), "slug": ("Projétil", "Slug"),
}
# nome das pecas por tipo (paiol_seletor = nenhum): "Paiol de <x>" / "<x> Magazine"
KIND_NAME = {
    "he": ("Cartuchos HE", "HE Shell"), "ap": ("Cartuchos AP", "AP Shell"), "sap": ("Cartuchos SAP", "SAP Shell"),
    "ac": ("Cartuchos AC", "AC Shell"), "frag": ("Cartuchos FRAG", "FRAG Shell"),
    "plasma": ("Células de Plasma", "Plasma Cell"), "pem": ("Células PEM", "EMP Cell"),
    "msl_he": ("Mísseis HE", "HE Missile"), "msl_cluster": ("Mísseis de Submunição", "Cluster Missile"),
    "msl_emp": ("Mísseis PEM", "EMP Missile"), "msl_nuke": ("Ogivas Nucleares", "Nuclear Warhead"),
    "slug": ("Projéteis", "Slug"),
}
# o que a peca de um tipo so guarda (texto da descricao)
KIND_DESC = {
    "he": ("cartuchos HE", "HE shells"), "ap": ("cartuchos AP", "AP shells"), "sap": ("cartuchos SAP", "SAP shells"),
    "ac": ("cartuchos AC", "AC shells"), "frag": ("cartuchos FRAG", "FRAG shells"),
    "plasma": ("células de plasma", "plasma cells"), "pem": ("células PEM", "EMP cells"),
    "msl_he": ("mísseis HE", "HE missiles"), "msl_cluster": ("mísseis de submunição", "cluster missiles"),
    "msl_emp": ("mísseis PEM", "EMP missiles"), "msl_nuke": ("ogivas nucleares", "nuclear warheads"),
    "slug": ("projéteis de railgun", "railgun slugs"),
}
FAMILY_UNIT = {"cartuchos": ("carregadores", "magazines"), "celulas": ("células", "cells"),
               "misseis": ("cargas", "charges"), "projeteis": ("projéteis", "slugs")}
FAMILY_SHORT = {"cartuchos": ("Cartuchos", "Shells"), "celulas": ("Células", "Cells"),
                "misseis": ("Mísseis", "Missiles"), "projeteis": ("Projéteis", "Slugs")}
ICON_SIZE = {1: 32, 2: 48, 3: 64}

_READY = []


def _D():
    import bs_data as D
    if not _READY:
        D.implement_variants(VARIANTS, "bsgen.logistics")
        _READY.append(True)
    I._D()
    return D


def seletor():
    return _D().switch("logistics.paiol_seletor")


def contador():
    return bool(_D().switch("logistics.paiol_contador"))


# ----------------------------------------------------------------------------- dados dos paiois
def paiol_entries():
    """[(peca do spec, [tipos], id, curto, chave)] das pecas de paiol deste build: as 4 familias (seletor = botao) ou,
    com paiol_seletor = nenhum, uma peca por tipo (SPEC.paiol.parts_when_selector_nenhum) + os projeteis."""
    D = _D()
    out = []
    ids = set(D.SPEC["paiol"]["parts_when_selector_nenhum"]["ids"])
    for p in D.PAIOL_PARTS:
        kinds = list(p["kinds"])
        if seletor() == "nenhum" and len(kinds) > 1:
            n = f"{p['size'][0]}x{p['size'][1]}"
            for k in kinds:
                pid = f"{C.AUTHOR}.bs_paiol_{k['key']}_{n}"
                if pid not in ids:
                    raise ValueError(f"{pid} fora de SPEC.paiol.parts_when_selector_nenhum")
                short = pid.split(".", 1)[1]
                out.append((p, [k], pid, short, D._key(short)))
        else:
            out.append((p, kinds, p["id"], p["short"], D._key(p["short"])))
    return out


def sub_meta(n):
    """Sub-meta do tamanho n ('1x1'...) de art3d/bs_paiol (meta compartilhada) ou None (arte procedural)."""
    meta = _D().PAIOL_ART.get("meta")
    return ((meta or {}).get("parts") or {}).get(n)


def rect_loc(rect):
    """[x, y, w, h] do meta (origem no canto de cima-esquerda) -> (Location do centro, Size)."""
    x, y, w, h = [float(v) for v in rect]
    return [round(x + w / 2, 4), round(y + h / 2, 4)], [round(w, 4), round(h, 4)]


def consumed_keys(ctx):
    """Tipos (chave do recurso) que alguma maquina DESTE build usa (para o paiol so empurrar para FitaEntra_<k> que
    existe: ViaBuffs com ComponentIDs de ninguem reprova o rules_lint). Sem ctx (fora do build): todos."""
    D = _D()
    if ctx is None or ctx.get("registry") is None:
        return None
    names = ctx["registry"].names
    keys = set()

    def add(g):
        try:
            keys.update(m["key"] for m in I.feed_modes(g))
        except ValueError:
            pass
    if "bsgen.guns" in names:
        for g in D.GUNS:
            add(g)
    if "bsgen.ciws" in names:
        for g in D.DEFENSES:
            add(g)
    if "bsgen.pem" in names:
        for g in D.PEM:
            add(g)
    if "bsgen.launchers" in names:
        for g in getattr(D, "LAUNCHERS", []) or []:
            add(g)
    if "bsgen.railgun" in names and D.RAIL_ENABLED:
        add({"id": I.RAIL_LOADER, "size": [5, 5], "logistica": D.RAIL.get("logistica")})
    return keys


# ----------------------------------------------------------------------------- cook-off
def cookoff_hits(ck):
    """HitEffects do tipo CHEIO (SPEC.paiol.parts[].kinds[].cookoff_when_full), escalados pelo FactorHitEffectsWith:
    op = ExplosiveDamage com fogo (factory_ammo.rules:788-807), struct = so estrutura, drain = dreno de bateria
    (factory_emp.rules:1005-1030)."""
    hits = []
    op = ck.get("op")
    if op:
        e = {"Type": "ExplosiveDamage", "TotalDamage": {"BaseValue": int(op["TotalDamage"]), "EffectScaleExponent": 1},
             "Radius": op["Radius"], "Delay": 0.05}
        if op.get("RadiusEffectScaleExponent") is not None:
            e["RadiusEffectScaleExponent"] = op["RadiusEffectScaleExponent"]
        if op.get("StatusType"):
            e.update({"StatusType": op["StatusType"], "StatusChancePerNDamage": op.get("StatusChancePerNDamage", "50%"),
                      "StatusValue": op.get("StatusValue", 1), "NDamage": int(op.get("NDamage", 1000))})
        e["Filter"] = {"OperationalHealth": True, "StructuralHealth": False, "Friendlies": True}
        hits.append(e)
    st = ck.get("struct")
    if st:
        hits.append({"Type": "ExplosiveDamage",
                     "TotalDamage": {"BaseValue": int(st["TotalDamage"]), "EffectScaleExponent": 1},
                     "Radius": st["Radius"], "Delay": 0.05,
                     "Filter": {"OperationalHealth": False, "StructuralHealth": True, "Friendlies": True,
                                "Crew": False}})
    dr = ck.get("drain")
    if dr:
        e = {"Type": "ExplosiveResourceDrain", "ResourceType": dr.get("ResourceType", "battery"),
             "TotalDrain": {"BaseValue": int(dr["TotalDrain"]), "EffectScaleExponent": 1}, "Radius": dr["Radius"],
             "Slices": 1, "Delay": 0.05}
        if dr.get("RadiusEffectScaleExponent") is not None:
            e["RadiusEffectScaleExponent"] = dr["RadiusEffectScaleExponent"]
        e["Filter"] = {"Ships": True, "Shields": True, "Friendlies": True}
        hits.append(e)
    return hits


DRAIN_MEDIA = ["&<./Data/shots/missile_emp/particles/missile_emp_hit_orb.rules>",
               "&<./Data/shots/missile_emp/particles/missile_emp_hit_bolts.rules>",
               "&<./Data/shots/missile_emp/particles/missile_emp_hit_shockwave.rules>"]


# ----------------------------------------------------------------------------- Fita
def build_fita():
    """Peca Fita de Alimentacao (SPEC.fita_teleporte.part; kit TF/parts/bs2f_fita/bs2f_fita.rules)."""
    D = _D()
    fp = D.FITA_PART
    meta = D.FITA_ART.get(FITA_DIR)
    ack = I.luz_ack()
    key = D._key(fp["id"].split(".", 1)[1])
    fields = fp.get("fields") or {}
    part = {
        "NameKey": Q(f"Parts/{key}"), "IconNameKey": Q(f"Parts/{key}Icon"), "DescriptionKey": Q(f"Parts/{key}Desc"),
        "ID": fp["id"], "EditorGroups": [Q(C.EDITOR_GROUP), Q("Utilities")],
        "Resources": [[r, int(q)] for r, q in fp["build_cost"]], "Size": list(fp["size"]),
        "IsRotateable": bool(fields.get("IsRotateable", False)), "IsFlippable": bool(fields.get("IsFlippable", False)),
        "SelectionPriority": int(fields.get("SelectionPriority", 0)), "MaxHealth": int(fp["max_health"]),
        "TypeCategories": [I.CAT_FITA],
    }
    if ack:
        part["ReceivableBuffs : ^/0/ReceivableBuffs"] = [I.BUFF_ACK]
    part.update({"AllowedDoorLocations": [], "GeneratorRequiresDoor": False, "CrewSpeedFactor": 0,
                 "EditorIcon": {"Texture": {"File": Q("icon.png"), "SampleMode": "Linear"}, "Size": [32, 32]}})
    layers = (meta or {}).get("layers") or {}

    def loc_size(name):
        lay = layers.get(name)
        return rect_loc(lay["rect"]) if lay else ([0.5, 0.5], [1, 1])
    comp = {}
    comp[comment("---- gruda na maquina vizinha (em cruz, sem as quinas): buff BulletStrike_FitaLink ----")] = None
    comp["GrudaHorizontal"] = {"Type": "AreaBuffProvider", "BuffType": I.BUFF_LINK, "BuffArea": [-1, 0, 3, 1],
                               "Criteria": {"Category": I.CAT_MAQUINA}}
    comp["GrudaVertical"] = {"Type": "AreaBuffProvider", "BuffType": I.BUFF_LINK, "BuffArea": [0, -1, 1, 3],
                             "Criteria": {"Category": I.CAT_MAQUINA}}
    comp[comment("---- luz verde (art.fita_luz): piso (lights_add) + lentes do teto (roof_doodads) ----")] = None
    lz_loc, lz_sz = loc_size("luz_grudada")
    lt_loc, lt_sz = loc_size("luz_teto")
    luz = {"Type": "Graphics", "Location": lz_loc}
    teto = {"Type": "Graphics", "Location": lt_loc}
    if ack:
        # a maquina responde BulletStrike_FitaAck (AvisaFita*): luz so quando grudada em algo
        comp["Grudada"] = {"Type": "BuffToggle", "BuffType": I.BUFF_ACK}
        luz["OperationalToggle"] = "Grudada"
        teto["OperationalToggle"] = "Grudada"
    luz["OperationalLighting"] = {"Layer": Q("lights_add"),
                                  "DamageLevels": [{"File": Q("luz_grudada.png"), "Size": lz_sz}]}
    teto["OperationalRoofDoodad"] = {"Layer": Q("roof_doodads"),
                                     "DamageLevels": [{"File": Q("luz_grudada_teto.png"), "Size": lt_sz}]}
    comp["LuzGrudada"] = luz
    comp["LuzGrudadaTeto"] = teto
    fl_loc, fl_sz = loc_size("floor")
    rf_loc, rf_sz = loc_size("roof")
    comp["Graficos"] = {"Type": "Graphics", "Location": fl_loc,
                        "Floor": {"Layer": Q("floors"), "DamageLevels": [{"File": Q("floor.png"), "Size": fl_sz}]},
                        "Roof": {"Layer": Q("roofs"), "DamageLevels": [{"File": Q("roof.png"),
                                                                        "NormalsFile": Q("roof_normals.png"),
                                                                        "Size": rf_sz}]}}
    comp["Blueprints"] = {"Type": "BlueprintSprite", "File": Q("blueprints.png"), "Size": list(fp["size"])}
    comp["DestroyedEffects"] = {"Type": "DeathEffects", "MediaEffects": "&/COMMON_EFFECTS/SmallPartDestroyed",
                                "Location": [0.5, 0.5]}
    part["Components : ^/0/Components"] = comp
    return {"Part : " + C.base_part_path(1, 1, False, base="base_part_terran"): part}


# ----------------------------------------------------------------------------- paiol
def build_paiol(p, kinds, pid, short, key, ctx=None):
    """Regras de um paiol (familia com seletor, familia de um tipo, ou peca por tipo com paiol_seletor = nenhum)."""
    D = _D()
    t = D.transport()
    tele = t == "teleporte"
    w, h = p["size"]
    n = f"{w}x{h}"
    fam = p["family"]
    sel = len(kinds) > 1
    center = [w / 2, h / 2]
    sub = sub_meta(n) or {}
    pub = f"../{D.PAIOL_ART['pub']}/"
    consumed = consumed_keys(ctx)
    push_q = int((p.get("teleporte") or {}).get("push_q_per_0_1s") or D.SPEC["paiol"]["teleporte_push_table"][fam][n] // 10)

    cats = ["bs_paiol", f"bs_paiol_{fam}"] + [f"bs_paiol_{k['key']}" for k in kinds]
    cats += [I.CAT_MAQUINA] if tele else ["storage"]
    part = {
        "NameKey": Q(f"Parts/{key}"), "IconNameKey": Q(f"Parts/{key}Icon"), "DescriptionKey": Q(f"Parts/{key}Desc"),
        "ID": pid, "EditorGroups": [Q(C.EDITOR_GROUP), Q("Storage")],
        "Resources": [[r, int(q)] for r, q in p["build_cost"]], "Size": [w, h],
        "IsRotateable": False, "IsFlippable": False, "SelectionPriority": 0, "MaxHealth": int(p["max_health"]),
        "TypeCategories": cats,
    }
    if tele:
        # selado: a tripulacao nao entra (thermal_battery.rules:22-25); o paiol DA o FitaRede, nao recebe
        part["ReceivableBuffs : ^/0/ReceivableBuffs"] = [I.BUFF_LINK, I.BUFF_FAB]
        part.update({"AllowedDoorLocations": [], "GeneratorRequiresDoor": False, "CrewSpeedFactor": 0})
    else:
        # sala de municao caminhavel (SPEC.paiol.components_crew_mode.part_fields): portas em todas as bordas
        part.update({"AllowedDoorLocations": C.door_locations(w, h), "GeneratorRequiresDoor": True,
                     "CrewSpeedFactor": 0.7})
    cf = D.SPEC["paiol"]["common_fields"]
    part.update({"IsWalled": True, "InitialPenetrationResistance": cf["InitialPenetrationResistance"],
                 "ContinuingPenetrationResistance": cf["ContinuingPenetrationResistance"],
                 "DamageResistances": dict(cf["DamageResistances"])})
    icons = sub.get("icon") or []
    icon = next((x for x in icons if f"_{fam}_" in x), f"icon_{fam}_{n}.png")
    isz = ICON_SIZE.get(max(w, h), 64)
    part["EditorIcon"] = {"Texture": {"File": Q(pub + icon), "SampleMode": "Linear"}, "Size": [isz, isz]}

    comp = {}
    if t in ("rede", "gemea"):
        # reserva fisica (WP15): o resto do paiol vem do bsgen.belt_net
        C.call(I.beltnet(), "paiol_net", comp, p, ctx)
    # ------------------------------------------------------------------ seletor do tipo
    if sel:
        comp[comment(f"---- seletor do tipo ({p['selector_toggle']}; PartToggle do WP01) ----")] = None
        comp[FAMILY_TOGGLE_COMP] = {"Type": "UIToggle", "ToggleID": Q(p["selector_toggle"]),
                                    "Default": int(kinds[0]["selector_index"]),
                                    "AvailableChoices": [int(k["selector_index"]) for k in kinds],
                                    "AlwaysAllowInBuildMode": True, "RequiresCommand": False}
        for k in kinds:
            comp[f"EhTipo_{k['key']}"] = {"Type": "ModeToggle", "Mode": FAMILY_TOGGLE_COMP,
                                          "OnMode": int(k["selector_index"])}
    # ------------------------------------------------------------------ estoque por tipo
    comp[comment("---- estoque por tipo (fora de bloco alternado: trocar o tipo nunca apaga o estoque) ----")] = None
    for k in kinds:
        kk = k["key"]
        st = {"Type": "ResourceStorage", "ResourceType": k["resource"], "MaxResources": int(k["MaxResources"]),
              "InitToMaxResources": 0, "DropResourcesWhenDestroyed": False}
        if not tele:
            stack = int((D.RES_BY_ID.get(k["resource"]) or {}).get("max_stack") or 1)
            st["SuppliesResources"] = True
            if sel:
                st["SuppliesResourcesToggle"] = f"EhTipo_{kk}"
            st.update({"MinResourcesPickUp": stack, "MaxResourcesPickUp": stack, "IsIntermediateStorage": True})
        comp[f"Estoque_{kk}"] = st
        if not tele:
            cons = {"Type": "ResourceConsumer", "ResourceType": k["resource"], "Storage": f"Estoque_{kk}",
                    "DefaultPriority": "&/PRIORITIES/Storage_Supply", "ResupplyThreshold": C.half(k["MaxResources"])}
            if sel:
                # tipo fora do botao: sem entrega nenhuma. So o OperationalToggle desligado ainda deixa a tripulacao
                # ociosa entregar na prioridade minima (common.toggled_consumers; SW chaingun_magazine.rules:123),
                # e o que entrasse ficaria preso (SuppliesResourcesToggle = EhTipo_<k> desligado), ate 5x o estoque
                cons["OperationalToggle"] = f"EhTipo_{kk}"
                cons["AllowNonOperationalMinPriorityDelivery"] = False
            comp[f"Consumidor_{kk}"] = cons
    # ------------------------------------------------------------------ Fita (teleporte)
    if tele:
        I.host(comp, w, h)
        areas = (p.get("teleporte") or {}).get("AvisaFita_BuffArea")
        if areas and "AvisaFitaHorizontal" in comp:
            comp["AvisaFitaHorizontal"]["BuffArea"] = list(areas[0])
            comp["AvisaFitaVertical"]["BuffArea"] = list(areas[1])
        comp[comment("---- com Fita: o paiol da o BulletStrike_FitaRede ao navio (kit bs2f_paiol_bala.rules:60-70) ----")] = None
        comp["Rede"] = {"Type": "GridBuffProvider", "BuffType": I.BUFF_REDE, "BuffAmount": 1,
                        "GridDistance": I.alcance(), "OperationalToggle": "FitaLigada"}
        push = [k for k in kinds if consumed is None or k["key"] in consumed] if I.fita_arma() == "empurra" else []
        if push:
            I.desligado(comp)
        for k in kinds:
            kk = k["key"]
            comp[comment(f"---- {kk}: entra das fabricas (EntraPaiol_{kk}) e sai para as armas (Empurra_{kk}) ----")] = None
            gate = "FitaLigada"
            if sel:
                gate = f"Aceita_{kk}"
                comp[gate] = {"Type": "MultiToggle", "Toggles": [f"EhTipo_{kk}", "FitaLigada"], "Mode": "All"}
            comp[f"EntraPaiol_{kk}"] = {"Type": "ResourceStorageProxy", "ResourceType": k["resource"],
                                        "ComponentID": f"Estoque_{kk}", "ProxyToggle": gate}
            if k in push:
                comp[f"AncoraArmas_{kk}"] = {"Type": "ResourceStorageProxy", "ResourceType": k["resource"],
                                             "ComponentID": f"Estoque_{kk}", "ProxyToggle": "Desligado"}
                comp[f"ParaArmas_{kk}"] = {"Type": "MultiResourceStorage", "ResourceType": k["resource"],
                                           "ResourceStorages": [f"AncoraArmas_{kk}"],
                                           "ViaBuffs": {"OutgoingBuffProviders": ["Rede"],
                                                        "ComponentIDs": [f"FitaEntra_{kk}"]},
                                           "AddMode": "PrioritizeLeastResources"}
                comp[f"Empurra_{kk}"] = {"Type": "ResourceConverter", "OperationalToggle": "FitaLigada",
                                         "FromStorage": f"Estoque_{kk}", "FromQuantity": push_q,
                                         "MinFromQuantityForConversion": 1, "ToStorage": f"ParaArmas_{kk}",
                                         "ToQuantity": push_q, "Interval": I.FEED_INTERVAL}
        # animacao: cartuchos entrando (estoque sobe) / saindo (estoque desce)
        comp[comment("---- Fita: cartuchos entrando / saindo (art3d/bs_fita_fx no painel livre do teto) ----")] = None
        fx = sub.get("fita_fx") or {}
        floc = fx.get("location") or center
        fsz = fx.get("size") or [1, 1]
        for which, nm, flag in (("entra", "Entrou", "TriggerOnDecrease"), ("sai", "Saiu", "TriggerOnIncrease")):
            trigs = []
            for k in kinds:
                tn = f"{nm}_{k['key']}"
                comp[tn] = {"Type": "ValueChangeTrigger", "ValueSource": f"Estoque_{k['key']}", flag: False}
                trigs.append(tn)
            trig = trigs[0]
            if len(trigs) > 1:
                trig = f"{nm}Algum"
                comp[trig] = {"Type": "MultiTrigger", "Triggers": trigs}
            rec = "EntrandoRecente" if which == "entra" else "SaindoRecente"
            comp[rec] = I.recent_timer(trig)
            comp["AnimEntrando" if which == "entra" else "AnimSaindo"] = I.fx_graphics(which, rec, floc, fsz)
    # ------------------------------------------------------------------ mostrador
    comp[comment("---- mostrador: barra sob a vida + medidor do teto + placa do tipo ----")] = None
    gauge = (sub.get("layers") or {}).get("gauge") or {}
    gfiles = gauge.get("files") or [f"gauge_{n}_{i}.png" for i in range(1, int(p.get("roof_gauge_levels") or 5) + 1)]
    g_loc, g_sz = rect_loc(gauge.get("rect") or D.SPEC["paiol"]["gauge_rect"][n])
    plate = sub.get("plate") or {}
    p_loc, p_sz = rect_loc(plate.get("rect") or D.SPEC["paiol"]["plate_rect"][n])
    for k in kinds:
        kk = k["key"]
        bar = {"Type": "ProgressBar"}
        if sel:
            bar["OperationalToggle"] = f"EhTipo_{kk}"
        bar.update({"ShowProgressFor": f"Estoque_{kk}", "LowColor": [255, 70, 30], "HighColor": [255, 200, 40],
                    "FullColor": [110, 230, 90], "Height": 8})
        comp[f"BarraEstoque_{kk}"] = bar
        shown = {
            f"Medidor_{kk}": {"Type": "ResourceSprites", "Location": g_loc, "ResourceStorage": f"Estoque_{kk}",
                              "Layer": Q("roof_doodads"), "HasZeroResourceSprite": False, "Round": "Up",
                              "ResourceLevels": [{"File": Q(pub + f), "Size": g_sz} for f in gfiles]},
            f"Placa_{kk}": {"Type": "Graphics", "Location": p_loc,
                            "OperationalRoofDoodad": {"Layer": Q("roof_doodads"), "DamageLevels": [
                                {"File": Q(f"../{PLACAS_DIR}/placa_{kk}.png"), "Size": p_sz}]}},
        }
        if sel:
            comp[f"MostradorTipo_{kk}"] = {"Type": "ToggledComponents", "Toggle": f"EhTipo_{kk}", "Components": shown}
        else:
            comp.update(shown)
    if contador():
        counter_components(comp, kinds, sub, sel)
    # ------------------------------------------------------------------ indicadores
    inds = []
    if tele:
        # fora da Fita (sem Fita grudada nem botao): nada entra nem sai
        inds.append({"Toggle": "FitaLigada", "AtlasSprite": {"File": "&/INDICATORS/NoResource", "Size": [1, 1]},
                     "HidesIndicators": [1]})
    if sel:
        for k in kinds:
            comp[f"TemMunicao_{k['key']}"] = {"Type": "MultiToggle", "Toggles": [f"EhTipo_{k['key']}",
                                                                                 f"Estoque_{k['key']}"], "Mode": "All"}
        comp["TemMunicao"] = {"Type": "MultiToggle", "Toggles": [f"TemMunicao_{k['key']}" for k in kinds],
                              "Mode": "Any"}
    else:
        comp["TemMunicao"] = {"Type": "MultiToggle", "Toggles": [f"Estoque_{kinds[0]['key']}"], "Mode": "Any"}
    inds.append({"Toggle": "TemMunicao", "Delay": 1,
                 "AtlasSprite": {"File": "&/INDICATORS/NoAmmo", "Size": [1, 1]}})
    comp["Indicadores"] = {"Type": "IndicatorSprites", "Location": center, "Indicators": inds}
    # ------------------------------------------------------------------ cook-off por tipo
    comp[comment("---- explosao propria por tipo, escalada pelo estoque (thermal_battery.rules:94-122) ----")] = None
    for k in kinds:
        ck = k.get("cookoff_when_full")
        if not ck:
            continue
        hits = cookoff_hits(ck)
        if not hits:
            continue
        de = {"Type": "DeathEffects", "Location": center, "FactorHitEffectsWith": f"Estoque_{k['key']}",
              "IncludeWhenUnderConstruction": False, "HitEffects": hits}
        if ck.get("drain"):
            de["FactorMediaEffectsWith"] = "&FactorHitEffectsWith"
            de["MediaEffects"] = list(DRAIN_MEDIA)
        comp[f"ExplosaoPropria_{k['key']}"] = de
    sz, _on, _off = C.effect_size(w, h)
    comp["DestroyedEffects"] = {"Type": "DeathEffects", "Location": center,
                                "MediaEffects": f"&/COMMON_EFFECTS/{sz}PartDestroyed"}
    # ------------------------------------------------------------------ graficos
    lay = sub.get("layers") or {}
    floor = (lay.get("floor") or {}).get("files") or [f"floor_{n}.png"]
    roof = next((f for f in ((lay.get("roof") or {}).get("files") or []) if f"_{fam}_" in f), f"roof_{fam}_{n}.png")
    roof_n = roof.replace(".png", "_normals.png")
    walls = sub.get("walls") or f"walls_{n}.png"
    comp["Graficos"] = {
        "Type": "Graphics", "Location": center,
        "Floor": {"Layer": Q("floors"), "DamageLevels": [{"File": Q(pub + floor[0]), "Size": [w, h]}]},
        "Walls": {"Layer": Q("walls"), "DamageLevels": [{"File": Q(pub + walls), "Size": [w, h]}]},
        "Roof": {"Layer": Q("roofs"), "DamageLevels": [{"File": Q(pub + roof), "NormalsFile": Q(pub + roof_n),
                                                        "Size": [w, h]}]},
    }
    comp["Blueprints"] = {"Type": "BlueprintSprite", "File": Q(pub + (sub.get("blueprints") or f"blueprints_{n}.png")),
                          "Size": [w, h]}
    part["Components : ^/0/Components"] = comp
    return {"Part : " + C.base_part_path(w, h, False): part}


def counter_components(comp, kinds, sub, sel):
    """Contador de 4 digitos do tipo escolhido (logistics.paiol_contador; molde testes/BulletStrike_Teste2
    bs2t_paiol_2x2.rules:489-614). So nos tamanhos com 'digits' no meta (2x2 e 3x3)."""
    dg = sub.get("digits")
    if not dg:
        return
    rects = dg["rects"]
    files = [Q(f"../../gui/digitos/digito{i}.png") for i in range(10)]
    comp[comment("---- contador de 4 digitos (estoque do tipo escolhido) ----")] = None
    comp["Dez"] = {"Type": "StaticValue", "Value": 10}
    comp["Cem"] = {"Type": "StaticValue", "Value": 100}
    comp["Mil"] = {"Type": "StaticValue", "Value": 1000}
    for k in kinds:
        kk = k["key"]
        # contagem absoluta (ProvidedValueRange = 0; vanilla missile_launcher_thermal.rules:81-89)
        comp[f"Contagem_{kk}"] = {"Type": "MultiResourceStorage", "ResourceType": k["resource"],
                                  "ResourceStorages": [f"Estoque_{kk}"], "ProvidedValueRange": 0,
                                  "ProvidedValuePerResource": 1}
        inner = {}
        for div, nm in ((10, "Dez"), (100, "Cem"), (1000, "Mil")):
            inner[f"Dividido{div}_{kk}"] = {"Type": "ValueOperation", "Operator": "Divide",
                                            "ValueOne": f"Contagem_{kk}", "ValueTwo": nm}
        # rects da esquerda para a direita: milhar, centena, dezena, unidade
        names = ["Milhar", "Centena", "Dezena", "Unidade"]
        for idx, (rect, nm) in enumerate(zip(rects, names)):
            loc, sz = rect_loc(rect)
            levels = [{"File": f, "Size": sz} for f in files]
            if nm == "Unidade":
                inner[f"Digito{nm}_{kk}"] = {"Type": "ResourceSprites", "Location": loc,
                                             "ResourceStorage": f"Estoque_{kk}", "Layer": Q("roof_doodads"),
                                             "Modulus": 10, "Round": "Up", "HasZeroResourceSprite": True,
                                             "ResourceLevels": levels}
            else:
                div = {"Milhar": 1000, "Centena": 100, "Dezena": 10}[nm]
                inner[f"Digito{nm}_{kk}"] = {"Type": "ValueSprites", "Location": loc,
                                             "ValueFrom": f"Dividido{div}_{kk}", "Layer": Q("roof_doodads"),
                                             "Modulus": 10, "Round": "Down", "HasZeroResourceSprite": True,
                                             "ResourceLevels": levels}
        if sel:
            comp[f"Contador_{kk}"] = {"Type": "ToggledComponents", "Toggle": f"EhTipo_{kk}", "Components": inner}
        else:
            comp.update(inner)


# ----------------------------------------------------------------------------- arte publicada
def _copy(out, src_dir, names, dst_rel, renames=None):
    """Copia os PNGs do art3d para <mod>/<dst_rel>/ (so os que ainda nao foram copiados)."""
    import art3d as A3
    dst = os.path.join(out.root, dst_rel)
    os.makedirs(dst, exist_ok=True)
    for nm in names:
        target = (renames or {}).get(nm, nm)
        p = os.path.join(dst, target)
        if os.path.exists(p):
            continue
        shutil.copyfile(A3.path(src_dir, nm), p)


def _ph_image(size, rgba, label=None, ring=None):
    """Arte provisoria (PIL; so com BS_ARTE_PROCEDURAL=1 e o art3d ausente)."""
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w, h = size
    d.rectangle([1, 1, w - 2, h - 2], fill=tuple(rgba), outline=tuple(ring or (40, 44, 52, 255)), width=max(1, w // 32))
    if label:
        d.text((max(2, w // 8), max(2, h // 3)), label, fill=(240, 240, 240, 255))
    return im


def _ph_frames(out, rel_dir):
    """Quadros provisorios da animacao da Fita: cartucho_<sai|entra><1..8> (alfa) e brilho_* (aditivo)."""
    from PIL import Image, ImageDraw
    for which, dy in (("sai", -1), ("entra", 1)):
        for i in range(1, I.FX_FRAMES + 1):
            c = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            b = Image.new("RGBA", (64, 64), (0, 0, 0, 255))
            y = 32 + dy * (i * 3 - 12)
            ImageDraw.Draw(c).rectangle([26, y - 6, 38, y + 6], fill=(200, 160, 60, 220))
            ImageDraw.Draw(b).ellipse([20, y - 12, 44, y + 12], fill=(0, 90, 110, 255))
            out.image(f"{rel_dir}/cartucho_{which}{i}.png", c)
            out.image(f"{rel_dir}/brilho_{which}{i}.png", b)


def publish_art(out, entries, ctx):
    """Arte usada pelas regras: Fita e FX (teleporte), arte compartilhada dos paiois e placas dos tipos."""
    D = _D()
    tele = D.transport() == "teleporte"
    if tele:
        meta = D.FITA_ART.get(FITA_DIR)
        if meta:
            _copy(out, FITA_DIR, meta["files"], f"parts/{FITA_DIR}")
        else:
            for nm, sz, col in (("floor.png", (64, 64), (60, 64, 72, 255)), ("roof.png", (64, 64), (150, 156, 166, 255)),
                                ("roof_normals.png", (64, 64), (128, 128, 255, 255)),
                                ("luz_grudada.png", (64, 64), (20, 120, 30, 255)),
                                ("luz_grudada_teto.png", (64, 64), (110, 230, 120, 160)),
                                ("icon.png", (32, 32), (150, 156, 166, 255)),
                                ("blueprints.png", (64, 64), (60, 120, 200, 160))):
                out.image(f"parts/{FITA_DIR}/{nm}", _ph_image(sz, col, "F" if nm == "icon.png" else None))
        fx = D.FITA_ART.get(I.FX_DIR)
        if fx:
            _copy(out, I.FX_DIR, fx["files"], f"parts/{I.FX_DIR}")
        else:
            _ph_frames(out, f"parts/{I.FX_DIR}")
    # placas dos tipos (art3d/bs_placas; a fabrica F2/F3/F4 tambem publica se ainda nao existir)
    plates = D.FITA_ART.get(PLACAS_DIR)
    keys = sorted({k["key"] for _p, kinds, *_r in entries for k in kinds})
    if plates:
        _copy(out, PLACAS_DIR, plates["files"], f"parts/{PLACAS_DIR}")
    else:
        for kk in keys:
            out.image(f"parts/{PLACAS_DIR}/placa_{kk}.png", _ph_image((48, 48), (30, 34, 40, 255), kk[:4].upper()))
    # arte compartilhada dos paiois -> parts/bs_paiol_comum/
    pub = f"parts/{D.PAIOL_ART['pub']}"
    names = set()
    digits = False
    for p, kinds, *_r in entries:
        w, h = p["size"]
        n = f"{w}x{h}"
        fam = p["family"]
        sub = sub_meta(n)
        if sub:
            lay = sub.get("layers") or {}
            names.update((lay.get("floor") or {}).get("files") or [])
            names.add(sub["walls"])
            names.add(sub["blueprints"])
            names.update((lay.get("gauge") or {}).get("files") or [])
            names.update(f for f in sub.get("icon") or [] if f"_{fam}_" in f)
            for f in (lay.get("roof") or {}).get("files") or []:
                if f"_{fam}_" in f:
                    names.update([f, f.replace(".png", "_normals.png")])
            if contador() and sub.get("digits"):
                digits = True
        else:
            levels = int(p.get("roof_gauge_levels") or 5)
            ph = {f"floor_{n}.png": (60, 64, 72, 255), f"walls_{n}.png": (40, 44, 52, 255),
                  f"roof_{fam}_{n}.png": (140, 146, 156, 255), f"roof_{fam}_{n}_normals.png": (128, 128, 255, 255),
                  f"icon_{fam}_{n}.png": (140, 146, 156, 255), f"blueprints_{n}.png": (60, 120, 200, 160)}
            for nm, col in ph.items():
                if not out.exists(f"{pub}/{nm}"):
                    out.image(f"{pub}/{nm}", _ph_image((64 * w, 64 * h), col, fam[:3].upper() if "icon" in nm else None))
            for i in range(1, levels + 1):
                nm = f"gauge_{n}_{i}.png"
                if not out.exists(f"{pub}/{nm}"):
                    out.image(f"{pub}/{nm}", _ph_image((16, 64), (110, 230, 90, 40 + 200 * i // levels)))
    if names:
        _copy(out, D.PAIOL_ART["dir"], sorted(names), pub)
    if digits:
        files = [f"digito{i}.png" for i in range(10)]
        _copy(out, D.PAIOL_ART["dir"], files, "gui/digitos")


# ----------------------------------------------------------------------------- ganchos do build_mod
def write(out, header):
    """buffs/bs_fita_buffs.rules (so teleporte): os 4 buffs da Fita, registrados pelo Overrides do mod_actions()
    (padrao do kit mod.rules e do SW mod.rules:39-43). Nenhum muda numero de nada: sao o 'fio invisivel' do ViaBuffs,
    como o EnginePowerDistribution vanilla (buffs.rules:25-28)."""
    if _D().transport() != "teleporte":
        return
    none = {"CombineMode": "Max", "RectBorderColor": [0, 0, 0, 0], "RectFillColor": [0, 0, 0, 0]}
    top = {
        I.BUFF_LINK: {"CombineMode": "Max",
                      "Icon": {"Texture": {"File": Q("../gui/buff_fita.png"), "MipLevels": 2, "SampleMode": "Linear"},
                               "Size": [0.5, 0.5]},
                      "RectBorderColor": GREEN + [160], "RectFillColor": GREEN + [64]},
        I.BUFF_ACK: {"CombineMode": "Max", "RectBorderColor": GREEN + [160], "RectFillColor": GREEN + [32]},
        I.BUFF_REDE: dict(none),
        I.BUFF_FAB: dict(none),
    }
    out.text(BUFFS_FILE, render(top, header + "\nBuffs da Fita de Alimentacao (teletransporte da municao; SPEC.fita_teleporte.buffs)."))


def mod_actions():
    """Overrides dos buffs da Fita em <./Data/buffs/buffs.rules> (so teleporte)."""
    if _D().transport() != "teleporte":
        return []
    return [{"Action": "Overrides", "OverrideIn": Q("<./Data/buffs/buffs.rules>"), "Overrides": f"&<{BUFFS_FILE}>"}]


def parts(out, D, ctx):
    """Fita (teleporte) e paiois deste build."""
    D = _D()
    t = D.transport()
    if t in ("rede", "gemea"):
        # o bs_data so devolve rede/gemea com o bsgen.belt_net (J2R3-19)
        assert I.beltnet() is not None, "logistics.transport rede/gemea sem o bsgen.belt_net"
    entries = paiol_entries()
    if t == "teleporte":
        fp = D.FITA_PART
        short = fp["id"].split(".", 1)[1]
        rel = f"parts/{short}/{short}.rules"
        out.text(rel, render(build_fita(), ctx["header"] + f"\nPeca: {fp['name_en']} / {fp['name_ptbr']}"))
        ctx["add_part"](fp["id"])
    for p, kinds, pid, short, key in entries:
        if pid not in D.PART_INFO:
            # peca por tipo (paiol_seletor = nenhum): entra no indice para a descricao do mod contar 'paiois'
            D.PART_INFO[pid] = {"name_en": name_of(p, kinds)[1], "name_pt": name_of(p, kinds)[0], "tier": "early",
                                "kind": "paiol", "size": list(p["size"]), "oc": None}
        rel = f"parts/{short}/{short}.rules"
        nm_pt, nm_en = name_of(p, kinds)
        out.text(rel, render(build_paiol(p, kinds, pid, short, key, ctx),
                             ctx["header"] + f"\nPaiol: {nm_en} / {nm_pt}"))
        ctx["add_part"](pid)
    publish_art(out, entries, ctx)
    if I.embutida():
        _toggle_icons(out)


def _toggle_icons(out):
    """Icones do botao 'Fita embutida' (gui/fita_embutida_0/1.png, PIL; variante adiada logistics.fita_embutida)."""
    from PIL import Image, ImageDraw
    for mode, col in ((0, (90, 96, 104, 255)), (1, tuple(GREEN) + (255,))):
        rel = f"gui/fita_embutida_{mode}.png"
        if out.exists(rel):
            continue
        im = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([10, 30, 86, 66], radius=10, fill=(24, 36, 56, 230), outline=col, width=5)
        for x in (24, 40, 56, 72):
            d.rectangle([x - 4, 40, x + 4, 56], fill=col)
        out.image(rel, im)
        _D().PLACEHOLDERS.append(f"icone provisorio {rel} (logistics.fita_embutida = botao)")


def toggles():
    """PartToggle do botao 'Fita embutida' (so com logistics.fita_embutida = botao); os seletores de tipo (municao,
    celula, missil) sao do nucleo (WP01, R4)."""
    if not I.embutida():
        return []
    return [(I.TOGGLE_EMBUTIDA, [(0, "bs_fita_embutida_off", "PartToggles/BSFitaEmbutida_Off", "fita_embutida_0.png"),
                                 (1, "bs_fita_embutida_on", "PartToggles/BSFitaEmbutida_On", "fita_embutida_1.png")])]


# ----------------------------------------------------------------------------- textos
def name_of(p, kinds):
    """(pt, en) do paiol: o do spec (familia) ou, peca por tipo, 'Paiol de <tipo> <n>x<n>'."""
    if len(kinds) == 1 and len(p["kinds"]) > 1:
        n = f"{p['size'][0]}x{p['size'][1]}"
        pt, en = KIND_NAME[kinds[0]["key"]]
        return f"Paiol de {pt} {n}", f"{en} Magazine {n}"
    return p["name_ptbr"], p["name_en"]


ALCANCE_NAVE = 1000   # logistics.fita_alcance: 1000 = o navio inteiro (SPEC.switches.logistics.fita_alcance)


def _perto():
    """Alcance da Fita em blocos quando ele NAO cobre o navio inteiro (fita_alcance = 12, C2); None com 1000."""
    a = I.alcance()
    return a if a < ALCANCE_NAVE else None


def celula_acoplada(key, w, h):
    """Celula do paiol acoplado que os textos prometem (= spec acoplamento.cell de toda maquina): lancador (msl_*) no
    meio da borda da FRENTE [(w-1)//2, -1] (a torre aponta para cima: launchers.py TurretWeapon Rotation -90d);
    Carregador do Tupa (slug) no canto de tras-esquerdo [0, h]; as outras armas no meio da traseira [(w-1)//2, h]
    (largura par: logo a esquerda do meio)."""
    if key.startswith("msl_"):
        return [(w - 1) // 2, -1]
    if key == "slug":
        return [0, h]
    return [(w - 1) // 2, h]


def _onde_acoplar(fam, pt):
    """Onde encostar o paiol acoplado, por familia (celula_acoplada); a saida da fabrica e a celula do spec."""
    if fam == "misseis":
        return ("Encostado no meio da borda da frente (de cima) de um lançador (largura par: logo à esquerda do meio), "
                "ou na saída de uma fábrica" if pt else
                "Placed against the middle of a launcher's front (top) edge (even width: just left of the middle), "
                "or at a factory output")
    if fam == "projeteis":
        return ("Encostado atrás do Carregador do Tupã, no canto esquerdo da traseira, ou na saída de uma fábrica"
                if pt else
                "Placed behind the Tupã Railgun Loader, at the left corner of its back edge, or at a factory output")
    return ("Encostado no meio da traseira de uma arma (largura par: logo à esquerda do meio), ou na saída de uma "
            "fábrica" if pt else
            "Placed against the middle of a gun's back edge (even width: just left of the middle), or at a factory "
            "output")


def _fita_desc(fp, pt):
    """Texto da Fita (spec) acertado as variantes: fita_alcance < 1000 troca 'de um canto ao outro da nave' pelo
    alcance em blocos; art.fita_luz = sempre tira a frase da luz verde (a luz fica sempre acesa e nao avisa nada)."""
    txt = fp["description_ptbr" if pt else "description_en"]
    trocas = []
    a = _perto()
    if a is not None:
        trocas.append(("de um canto ao outro da nave", f"a até {a} blocos de distância") if pt else
                      ("anywhere on the ship", f"within {a} tiles"))
    if not I.luz_ack():
        trocas.append((" A luz verde acende quando está grudada.", "") if pt else
                      (" The green light shows it is attached.", ""))
    for old, new in trocas:
        if old not in txt:
            raise ValueError(f"logistics: a descricao da Fita no spec mudou (sem '{old}'): acerte _fita_desc")
        txt = txt.replace(old, new)
    return txt


def _desc(p, kinds, lang):
    D = _D()
    t = D.transport()
    fam = p["family"]
    sel = len(kinds) > 1
    pt = lang == "pt"
    unit = FAMILY_UNIT[fam][0 if pt else 1]
    caps = " · ".join(f"{KIND_LABEL[k['key']][0 if pt else 1]} {int(k['MaxResources'])}" for k in kinds)
    acop = I.acoplamento_on()
    if t == "teleporte":
        a = _perto()
        if a is None:
            onde = ", de qualquer lugar da nave." if pt else ", anywhere on the ship."
        else:
            onde = (f", desde que estejam a até {a} blocos de distância." if pt else
                    f", as long as they are within {a} tiles.")
        head = ("Paiol blindado e selado: a tripulação não entra. Grude uma Fita de Alimentação do lado: a munição chega "
                "sozinha das fábricas com Fita e vai sozinha para as armas com Fita" + onde
                if pt else
                "Armored, sealed magazine: crew cannot enter. Stick an Ammo Feed Link next to it: ammo arrives by itself "
                "from factories with a Link and goes by itself to guns with a Link" + onde)
        if sel:
            how = ("No botão do paiol escolha o tipo que ele ACEITA (a placa no teto mostra qual). O que já está guardado, "
                   "de qualquer tipo, continua indo para as armas que usam aquele tipo."
                   if pt else
                   "Use the magazine's button to pick the type it ACCEPTS (the roof plate shows which). Whatever is "
                   "already stored, of any type, keeps going to the guns that use that type.")
        else:
            lbl = KIND_DESC[kinds[0]["key"]][0 if pt else 1]
            how = (f"Só guarda {lbl}." if pt else f"Stores {lbl} only.")
        if acop:
            how += (f" {_onde_acoplar(fam, pt)}, do mesmo tipo, também troca munição com ela sem a Fita (paiol "
                    "acoplado)." if pt else
                    f" {_onde_acoplar(fam, pt)}, of the same type, it also trades ammo with it without a Link (docked "
                    "magazine).")
    else:
        head = ("Sala de munição blindada: a tripulação guarda aqui a munição e leva dela para as armas que ficam abaixo "
                "da metade." if pt else
                "Armored ammo room: the crew store ammo here and carry it to guns that drop below half.")
        if sel:
            how = ("No botão escolha o tipo que a tripulação guarda e retira (a placa no teto mostra qual)."
                   if pt else "Use the button to pick the type the crew store and take (the roof plate shows which).")
        else:
            lbl = KIND_DESC[kinds[0]["key"]][0 if pt else 1]
            how = (f"Só guarda {lbl}." if pt else f"Stores {lbl} only.")
        if acop:
            how += (f" {_onde_acoplar(fam, pt)}, do mesmo tipo, abastece sozinho, sem tripulação (paiol acoplado)."
                    if pt else
                    f" {_onde_acoplar(fam, pt)}, of the same type, it feeds by itself, with no crew (docked magazine).")
    if len(kinds) == 1:
        cap = (f"Capacidade: {int(kinds[0]['MaxResources'])} {unit}." if pt else
               f"Capacity: {int(kinds[0]['MaxResources'])} {unit}.")
    else:
        cap = (f"Capacidade ({unit}): {caps}." if pt else f"Capacity ({unit}): {caps}.")
    boom = ("Explode quando destruído: quanto mais cheio, maior a explosão." if pt else
            "Explodes when destroyed: the fuller it is, the bigger the blast.")
    if any((k.get("cookoff_when_full") or {}).get("drain") for k in kinds):
        boom += (" Células e mísseis PEM guardados também drenam as baterias por perto." if pt else
                 " Stored EMP cells and missiles also drain nearby batteries.")
    if not any(k.get("cookoff_when_full") for k in kinds):
        boom = ""
    return "\n\n".join(x for x in (head, how, cap, boom) if x) + "<string id='BSModTag'/>"


def strings(DATA=None):
    """(en, pt): Fita, paiois e o botao 'Fita embutida'."""
    D = _D()
    en = {"Parts": {}, "PartToggles": {}}
    pt = {"Parts": {}, "PartToggles": {}}
    if D.transport() == "teleporte":
        fp = D.FITA_PART
        key = D._key(fp["id"].split(".", 1)[1])
        pt["Parts"][key] = fp["name_ptbr"]
        en["Parts"][key] = fp["name_en"]
        pt["Parts"][key + "Icon"] = "Fita"
        en["Parts"][key + "Icon"] = "Feed Link"
        pt["Parts"][key + "Desc"] = _fita_desc(fp, True) + "<string id='BSModTag'/>"
        en["Parts"][key + "Desc"] = _fita_desc(fp, False) + "<string id='BSModTag'/>"
    for p, kinds, pid, short, key in paiol_entries():
        n = f"{p['size'][0]}x{p['size'][1]}"
        nm_pt, nm_en = name_of(p, kinds)
        pt["Parts"][key] = nm_pt
        en["Parts"][key] = nm_en
        if len(kinds) == 1 and len(p["kinds"]) > 1:
            pt["Parts"][key + "Icon"] = f"{KIND_LABEL[kinds[0]['key']][0]} {n}"
            en["Parts"][key + "Icon"] = f"{KIND_LABEL[kinds[0]['key']][1]} {n}"
        else:
            pt["Parts"][key + "Icon"] = f"{FAMILY_SHORT[p['family']][0]} {n}"
            en["Parts"][key + "Icon"] = f"{FAMILY_SHORT[p['family']][1]} {n}"
        pt["Parts"][key + "Desc"] = _desc(p, kinds, "pt")
        en["Parts"][key + "Desc"] = _desc(p, kinds, "en")
    if I.embutida():
        pt["PartToggles"]["BSFitaEmbutida_Off"] = ("<b>Fita embutida: desligada</b>\n\nSó a peça Fita de Alimentação "
                                                   "grudada do lado liga esta máquina na rede da Fita.")
        en["PartToggles"]["BSFitaEmbutida_Off"] = ("<b>Built-in Feed Link: off</b>\n\nOnly an Ammo Feed Link part "
                                                   "stuck next to it links this machine.")
        pt["PartToggles"]["BSFitaEmbutida_On"] = ("<b>Fita embutida: ligada</b>\n\nA máquina entra na rede da Fita "
                                                  "mesmo sem a peça Fita (para naves sem espaço).")
        en["PartToggles"]["BSFitaEmbutida_On"] = ("<b>Built-in Feed Link: on</b>\n\nThe machine joins the feed network "
                                                  "even without a Feed Link part (for cramped ships).")
    return en, pt


# ----------------------------------------------------------------------------- conferencia (selfcheck)
def selfcheck(mod_dir, SPEC=None):
    """Confere a Fita, os paiois e os buffs escritos contra o transporte e o spec (lista de problemas)."""
    import re
    D = _D()
    probs = []
    t = D.transport()
    tele = t == "teleporte"
    parts = I.mod_parts(mod_dir)
    fita_id = D.FITA_PART["id"]
    buffs_path = os.path.join(mod_dir, BUFFS_FILE)
    mod_rules = os.path.join(mod_dir, "mod.rules")
    mr = open(mod_rules, encoding="utf-8").read() if os.path.isfile(mod_rules) else ""
    if tele:
        if fita_id not in parts:
            probs.append("teleporte sem a peca Fita (bs_fita)")
        if not os.path.isfile(buffs_path):
            probs.append(f"teleporte sem {BUFFS_FILE}")
        else:
            txt = open(buffs_path, encoding="utf-8").read()
            for b in I.BUFFS:
                if not re.search(rf"^{b}\s*$", txt, re.M):
                    probs.append(f"{BUFFS_FILE} sem o buff {b}")
        if "<./Data/buffs/buffs.rules>" not in mr or BUFFS_FILE not in mr:
            probs.append("mod.rules sem o Overrides dos buffs da Fita")
    else:
        if fita_id in parts:
            probs.append(f"peca Fita escrita com logistics.transport = {t}")
        if os.path.isfile(buffs_path) or "bs_fita_buffs" in mr:
            probs.append(f"buffs da Fita com logistics.transport = {t}")
    if fita_id in parts:
        path, comps, part, cats = parts[fita_id]
        for g in ("GrudaHorizontal", "GrudaVertical"):
            c = comps.get(g)
            if c is None or I.val(I.child(c, "Criteria"), "Category") != I.CAT_MAQUINA:
                probs.append(f"Fita: {g} sem Criteria Category {I.CAT_MAQUINA}")
        if I.luz_ack() != ("Grudada" in comps):
            probs.append("Fita: BuffToggle Grudada nao bate com art.fita_luz")
        if I.val(part, "IsRotateable") != "false":
            probs.append("Fita: tem que ser nao giratoria")
    # tipos que alguma arma ESCRITA recebe pela Fita (FitaEntra_<k>): so esses precisam do Empurra_<k> no paiol
    consumed = set()
    for pid in parts:
        if pid in I.machines():
            consumed |= {n.split("_", 1)[1] for n in parts[pid][1] if n.startswith("FitaEntra_")}
    want = paiol_entries()
    for p, kinds, pid, short, key in want:
        who = short
        if pid not in parts:
            probs.append(f"{who}: paiol nao escrito")
            continue
        path, comps, part, cats = parts[pid]
        text = open(path, encoding="utf-8").read()
        n = f"{p['size'][0]}x{p['size'][1]}"
        sel = len(kinds) > 1
        q = int((p.get("teleporte") or {}).get("push_q_per_0_1s") or 0)
        for k in kinds:
            kk = k["key"]
            st = comps.get(f"Estoque_{kk}")
            if st is None:
                probs.append(f"{who}: sem Estoque_{kk}")
                continue
            if I.val(st, "MaxResources") != str(int(k["MaxResources"])):
                probs.append(f"{who}: Estoque_{kk} MaxResources {I.val(st, 'MaxResources')}, spec {k['MaxResources']}")
            if f"bs_paiol_{kk}" not in cats:
                probs.append(f"{who}: TypeCategories sem bs_paiol_{kk} (o acoplamento procura o TIPO)")
            if tele:
                if comps.get(f"EntraPaiol_{kk}") is None:
                    probs.append(f"{who}: sem EntraPaiol_{kk}")
                emp = comps.get(f"Empurra_{kk}")
                if I.fita_arma() == "empurra" and kk in consumed:
                    if emp is None:
                        probs.append(f"{who}: sem Empurra_{kk} (alguma arma escrita tem FitaEntra_{kk})")
                    elif I.val(emp, "FromQuantity") != str(q):
                        probs.append(f"{who}: Empurra_{kk} q {I.val(emp, 'FromQuantity')}, spec {q}")
                elif emp is not None and I.fita_arma() == "puxa":
                    probs.append(f"{who}: Empurra_{kk} com logistics.fita_arma = puxa")
            else:
                cons = comps.get(f"Consumidor_{kk}")
                if cons is None:
                    probs.append(f"{who}: tripulacao sem Consumidor_{kk}")
                elif I.val(cons, "ResupplyThreshold") != str(C.half(k["MaxResources"])):
                    probs.append(f"{who}: Consumidor_{kk} limiar {I.val(cons, 'ResupplyThreshold')}, "
                                 f"esperado {C.half(k['MaxResources'])}")
                has_tog = I.val(st, "SuppliesResourcesToggle") is not None or I.val(cons, "OperationalToggle") is not None
                if has_tog != sel:
                    probs.append(f"{who}: SuppliesResourcesToggle/OperationalToggle {'ausente' if sel else 'presente'} "
                                 f"(seletor {'botao' if sel else 'nenhum'})")
                if sel and cons is not None and I.val(cons, "AllowNonOperationalMinPriorityDelivery") != "false":
                    probs.append(f"{who}: Consumidor_{kk} sem AllowNonOperationalMinPriorityDelivery = false (a "
                                 f"tripulacao encheria o tipo fora do botao, que nunca mais sai)")
                if I.val(st, "IsIntermediateStorage") != "true":
                    probs.append(f"{who}: Estoque_{kk} sem IsIntermediateStorage")
        if tele:
            rede = comps.get("Rede")
            if rede is None or I.val(rede, "GridDistance") != str(I.alcance()):
                probs.append(f"{who}: Rede ausente ou GridDistance diferente de {I.alcance()}")
            if I.lst(part, "AllowedDoorLocations") != []:
                probs.append(f"{who}: paiol de teleporte tem que ser selado (AllowedDoorLocations [])")
            if I.CAT_MAQUINA not in cats:
                probs.append(f"{who}: TypeCategories sem {I.CAT_MAQUINA}")
            rb = I.lst(part, "ReceivableBuffs") or []
            if I.BUFF_LINK not in rb or I.BUFF_FAB not in rb or I.BUFF_REDE in rb:
                probs.append(f"{who}: ReceivableBuffs {rb} (esperado {I.BUFF_LINK} + {I.BUFF_FAB}; o paiol DA o "
                             f"{I.BUFF_REDE})")
        else:
            doors = I.child(part, "AllowedDoorLocations")
            if doors is None or len(doors.children) != 2 * (p["size"][0] + p["size"][1]):
                probs.append(f"{who}: tripulacao sem as portas em todas as bordas")
            if any(nm.startswith(("EntraPaiol_", "Empurra_", "ParaArmas_")) or nm == "Rede" for nm in comps):
                probs.append(f"{who}: componentes da Fita com logistics.transport = {t}")
        if sel != (FAMILY_TOGGLE_COMP in comps):
            probs.append(f"{who}: seletor {'ausente' if sel else 'presente'}")
        if contador() != bool(re.search(r"\bContagem_", text)) and (sub_meta(n) or {}).get("digits"):
            probs.append(f"{who}: contador de digitos nao bate com logistics.paiol_contador")
        if re.search(r"\bNetworkResource\w*", text):
            probs.append(f"{who}: NetworkResource* num paiol")
    # pecas de paiol escritas que nao deviam existir (ex.: familia com paiol_seletor = nenhum)
    want_ids = {e[2] for e in want}
    for pid in parts:
        if "_paiol_" in pid and pid not in want_ids:
            probs.append(f"{pid.split('.', 1)[1]}: paiol escrito fora do conjunto deste build")
    # o texto do paiol diz onde encostar (celula_acoplada): toda maquina escrita tem que bater com ele
    maq = I.machines()
    for pid in parts:
        if pid not in maq:
            continue
        path, comps, part, cats = parts[pid]
        size = I.lst(part, "Size") or []
        for nm, c in comps.items():
            if not nm.startswith("PaiolAcoplado_") or len(size) != 2:
                continue
            res, loc = I.val(c, "ResourceType"), I.lst(c, "PartLocation") or []
            try:
                want_cell = celula_acoplada(I.res_key(res), int(size[0]), int(size[1]))
                ok = [int(float(x)) for x in loc] == want_cell
            except (KeyError, ValueError, TypeError):
                want_cell, ok = "?", False
            if not ok:
                probs.append(f"{pid.split('.', 1)[1]}: {nm} PartLocation {loc}, o texto do paiol promete {want_cell}")
    # textos x variantes: alcance da Fita (fita_alcance < 1000) e luz (art.fita_luz = sempre)
    en_s, pt_s = strings()
    for tab in (en_s, pt_s):
        for k, v in tab["Parts"].items():
            low = v.lower()
            if _perto() is not None and any(x in low for x in ("qualquer lugar", "canto ao outro", "anywhere")):
                probs.append(f"texto {k}: diz 'a nave toda' com logistics.fita_alcance = {I.alcance()}")
            if not I.luz_ack() and any(x in low for x in ("luz verde", "green light")):
                probs.append(f"texto {k}: fala da luz verde com art.fita_luz = sempre")
    return probs
