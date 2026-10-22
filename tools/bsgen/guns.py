"""Gerador das armas de conves (ataque) do Bullet Strike 2.0 (dono: WP02; modulo de CONTEUDO, API 2).

Gancho parts(out, DATA, ctx) do build_mod: os 12 canhoes de DATA.GUNS (numeros de SPEC.weapons ja transformados pelo
bs_data). build_gun(g, shot_paths, ctx=None) segue usavel por armas de recurso unico de outros modulos (PEM do WP08).

Arquitetura (so padroes ja usados pelo jogo base 0.30.x):
  * Torre unica (TurretWeapon) com FireInterval modificavel:
      - divide pelo buff RateOfFire (spin-up da minigun, igual ao chaingun.rules l.765-790)
      - multiplica pelo fator de overclock (BuffRemap Overclock Multiply, idem)
  * Municao, POR MODO i (indice da tabela SPEC.ammo_index_rules: 0 HE, 1 AP, 2 SAP, 3 AC; nunca a posicao na lista):
    ResourceStorage MagStorage_i (MaxResources = internal_storage_units), InlineResourceConverter Splitter_i que abre
    1 carregador em N cargas (ToQuantity = splitter_to_quantity; chaingun.rules l.353-374; Boiuna 1 -> 2 cargas) e o
    BulletEmitter puxa resources_used_per_shot do Splitter_i (Boiuna 3 = 1,5 carregador por granada); ModeToggle_i e
    o consumidor da tripulacao MagConsumer_i (common.mag_consumer: ResupplyThreshold = floor(Max/2) +
    logistics.reserva_tripulacao) em dois ToggledComponents com o mesmo ID (common.toggled_consumers, chaingun.rules
    l.383-437): so o modo escolhido recebe entregas e cada modo guarda o proprio estoque.
  * Seletor de municao: UIToggle "bs_ammo_type" (AvailableChoices do spec, Default 0) + ModeToggle
    (missile_launcher.rules l.125-146).
  * Emissores: blocos ToggledComponents mutuamente exclusivos (tipo x overclock) com os MESMOS nomes (TargetEmitter,
    Emitter1..n); a torre e os efeitos usam EmitterProxy (cannon_deck.rules l.827-928).
  * Logistica pelo seam do intake (WP05, bsgen.intake por common.content_module, nunca desligado pelo BS_FX_EXT):
    part_fields (TypeCategories/ReceivableBuffs a somar), weapon_intake (Fita: FitaEntra_<chave> por modo, ou
    acoplamento) e weapon_return (devolucao). Sem o modulo a arma fica so com a tripulacao.
  * Cook-off por modo: DeathEffects ExplosiveDamage = cookoff_cap x FactorHitEffectsWith MagStorage_i (fracao de
    enchimento, padrao thermal_battery.rules l.94-122, IncludeWhenUnderConstruction false).
  * Conves: anel 'tall', TurretCollider IsHigh, IgnoreFriendlyShipLowLOSChecks e IgnoreFriendlyShipHighLOSChecks (a
    torre atira por cima do casco e das nossas torres; os tiros tambem passam por cima delas: shots.OWN_SHIP_PASS),
    AntiPhasingRaycastIgnoreLowCollisions com o raio comecando no anel da propria torre e sprites em "roof_turrets".
"""

import os
import re

from rules_dsl import Q, VOID, comment, render
from bsgen import common as C

API = 2


def _intake():
    """bsgen.intake (WP05) com API >= 2, ou None (arma so com a tripulacao). Import tardio: evita ciclo com o intake."""
    return C.content_module("bsgen.intake")


def _ctx(ctx):
    """ctx do build_mod, ou um minimo (build_gun chamado de fora do gancho parts, ex. check_art3d)."""
    if ctx is not None:
        return ctx
    import bs_data as D
    import posixpath
    return {"D": D, "transport": D.transport(), "warn": D.warn, "header": "",
            "relpath": lambda a, b: posixpath.relpath(b, a)}


def _fi_value(g):
    """FireInterval da torre (grupo com modificadores, padrao do chaingun)."""
    mods = []
    if g.get("spin"):
        mods.append({"Type": "Buff", "BuffType": "RateOfFire", "ModificationMode": "Divide"})
    if g.get("oc"):
        mods.append({"Type": "BuffRemap", "BuffType": "Overclock", "ModificationMode": "Multiply",
                     "RemapFrom": [0, 1], "RemapTo": [1, "(&~/OVERCLOCK/FIRE_INTERVAL_FACTOR)"]})
    if not mods:
        return "&~/FIRE_INTERVAL", "&~/Part/Components/Turret/FireInterval"
    return {"BaseValue": "&~/FIRE_INTERVAL", "Modifiers": mods}, "&~/Part/Components/Turret/FireInterval/BaseValue"


def _barrel_ys(g):
    n = g["barrels"]["count"]
    sp = g["barrels"].get("spacing", 0.3)
    return [round((i - (n - 1) / 2) * sp, 4) for i in range(n)]


def geometry(g):
    """Calcula geometria (pivo, torre, canos, cano) a partir do tamanho; o gerador de sprites usa a mesma.

    Com arte 3D (g["art3d"] = meta.json do render), a geometria vem do proprio render (pasta g["art3d_dir"]; a
    Boiuna le art3d/bs_boiuna_ac, nao o art3d/<id curto>)."""
    w, h = g["size"]
    a3 = g.get("art3d")
    if a3:
        br = a3["barrel"]
        geo = {"pivot": list(a3["pivot"]), "turret_size": a3["turret_size"], "front": br["root"],
               "barrel_len": br["sprite_len"], "barrel_w": br["sprite_w"] / 2, "barrel_sprite_w": br["sprite_w"],
               "barrel_center": br["center"], "muzzle": br["muzzle"], "collider": a3.get("collider"),
               "ys": list(br["ys"])}
        # quanto o cano passa da borda de cima da peca (icone): ate o fim do desenho do cano em repouso, nao so
        # ate a boca (no Boitata as pontas passam da boca e ficariam cortadas na primeira linha do icone)
        top = geo["muzzle"]
        adir = g.get("art3d_dir") or g.get("short")
        if adir:
            import art3d as A3
            from PIL import Image
            bb = Image.open(A3.path(adir, br["rest"])).getchannel("A").getbbox()
            if bb:
                top = max(top, br["center"] + br["sprite_len"] / 2 - bb[1] / 64)
        overhang = top - geo["pivot"][1]
        geo["overhang"] = max(0, int(-(-overhang // 1)))
        return geo
    geo = dict(g.get("geom", {}))
    # area acima da fileira de tras (onde fica a tripulacao)
    top_h = h - 1 if h >= 2 else h
    geo.setdefault("pivot", [w / 2, round(max(0.5, top_h / 2 + (0.15 if h >= 3 else 0)), 3)])
    geo.setdefault("turret_size", round(min(w, top_h + 0.5) * 0.92, 3))
    ts = geo["turret_size"]
    geo.setdefault("front", round(ts * 0.36, 3))          # borda frontal da arte da torre (tiles a frente do pivo)
    if "length" in g["barrels"]:
        geo.setdefault("barrel_len", g["barrels"]["length"])
    else:
        geo.setdefault("barrel_len", round(min(4.6, max(0.7, ts * g["barrels"].get("len_factor", 0.8))), 3))
    geo.setdefault("barrel_w", g["barrels"].get("width", 0.25))
    geo["barrel_center"] = round(geo["front"] + geo["barrel_len"] / 2, 4)
    geo["muzzle"] = round(geo["front"] + geo["barrel_len"] - 0.08, 4)
    geo.setdefault("collider", round(ts * 0.5, 3))
    geo["ys"] = _barrel_ys(g)
    # quanto o cano passa da borda superior da peca (para o icone)
    overhang = geo["muzzle"] - geo["pivot"][1]
    geo["overhang"] = max(0, int(-(-overhang // 1)))
    return geo


def _modes(g):
    return g["modes"]


def _k(m):
    """Indice do modo (o da tabela; dicts 1.x usam 'mode')."""
    return m["index"] if "index" in m else m["mode"]


def _direct(m):
    """True = o emissor puxa direto do MagStorage (sem Splitter): so dicts sem splitter_to_quantity (1.x / modulos de
    fora) com mais de 1 carregador por disparo (cannon_deck.rules l.209-217 e l.845-846). Os modos 2.0 sempre tem o
    Splitter_i (mesmo com ToQuantity 1) e o emissor puxa resources_used_per_shot dele."""
    if m.get("direct_from_storage"):
        return True
    return "splitter_to_quantity" not in m and m.get("units_per_shot", 1) > 1


def shots_per_mag_stat(m):
    """True = a linha 'Disparos por carga' (BSShotsPerMag = Splitter_i/ToQuantity) vale para o modo: so com 1 carga
    do Splitter por disparo. Com ResourcesUsed > 1 (Boiuna: Splitter 2, ResourcesUsed 3 = 2/3 de disparo por
    carregador) o ToQuantity nao e o numero de disparos e o formato '{0:0}' arredondaria 0,67 para 1; a linha
    ShotAmmoUsage de cada modo ja mostra o consumo certo (1,5 por disparo)."""
    return not _direct(m) and int(m.get("units_per_shot", m.get("resources_used_per_shot", 1))) == 1


def _ammo_src(m):
    return f"MagStorage_{_k(m)}" if _direct(m) else f"Splitter_{_k(m)}"


def _fire_block_toggle(g, k, oc_state):
    """Nome do toggle que liga o bloco de emissores do tipo k no estado de overclock dado."""
    sel = g.get("selector")
    oc = bool(g.get("oc"))
    if sel and oc:
        return f"FireToggle_{k}_{'OC' if oc_state else 'N'}", False
    if sel:
        return f"ModeToggle_{k}", False
    if oc:
        return "IsOverclocked", (not oc_state)
    return None, False


def deck_hull_graphics(comp, g):
    """Casco (piso, paredes, teto e luzes internas lights_add da arte 3D)."""
    w, h = g["size"]
    center = [w / 2, h / 2]
    a3 = g.get("art3d")
    hull = {
        "Type": "Graphics", "Location": center, "OperationalToggle": "IsOperational",
        "Floor": {"Layer": Q("floors"), "DamageLevels": [{"File": Q("floor.png"), "Size": [w, h]}]},
        "Walls": {"Layer": Q("walls"), "DamageLevels": [{"File": Q("walls.png"), "Size": [w, h]}]},
        "Roof": {"Layer": Q("roofs"), "DamageLevels": [{"File": Q("roof.png"), "NormalsFile": Q("roof_normals.png"),
                                                          "Size": [w, h]}]},
    }
    if a3 and a3.get("hull", {}).get("lights"):
        hull["OperationalLighting"] = {"Layer": Q("lights_add"), "DamageLevels": [
            {"File": Q(a3["hull"]["lights"]), "Size": [w, h]}]}
    comp["Graphics"] = hull


def deck_turret_graphics(comp, g, geo, layer="roof_turrets"):
    """Torre/casulo girando (sombra em doodads_high). Lancadores usam layer="roof_doodads" para as
    sobreposicoes das celulas ficarem por cima em roof_turrets."""
    a3 = g.get("art3d")
    ts = geo["turret_size"]
    if a3:
        t = a3["turret"]
        if len(t["frames"]) > 1:
            on = {"AnimationFiles": [Q(f) for f in t["frames"]], "NormalsAnimationFiles": [Q(f) for f in t["normals"]],
                  "Size": [ts, ts], "AnimationInterval": t["interval"]}
        else:
            on = {"File": Q(t["frames"][0]), "NormalsFile": Q(t["normals"][0]), "Size": [ts, ts]}
        off = {"File": Q(t["off"]), "NormalsFile": Q(t["off_normals"]), "Size": [ts, ts]}
        shadow = t["shadow"]
        shadow_size = t.get("shadow_size", ts)
    else:
        on = {"File": Q("turret.png"), "NormalsFile": Q("turret_normals.png"), "Size": [ts, ts]}
        off = {"File": Q("turret_off.png"), "NormalsFile": Q("turret_normals.png"), "Size": [ts, ts]}
        shadow = "turret_shadow.png"
        shadow_size = ts
    comp["TurretGraphics"] = {
        "Type": "Graphics", "ChainedTo": "Turret", "Location": [0, 0], "Rotation": "90d",
        "OperationalToggle": "IsOperational",
        "Floor": {"Layer": Q("doodads_high"), "DamageLevels": [{"File": Q(shadow), "Size": [shadow_size, shadow_size]}]},
        "OperationalDoodad": {"Layer": Q(layer), "DamageLevels": [on]},
        "NonOperationalDoodad": {"Layer": Q(layer), "DamageLevels": [off]},
    }


def deck_light_graphics(comp, g):
    """Luzes dinamicas (iluminam o casco com normal map; so com "iluminacao sofisticada" ligada)."""
    for i, l in enumerate((g.get("art3d") or {}).get("lights", [])):
        comp[f"Light{i + 1}Graphics"] = {
            "Type": "Graphics", "ChainedTo": "Turret", "Location": [round(l["loc"][0], 4), round(l["loc"][1], 4)],
            "OperationalToggle": "IsOperational",
            "OperationalRoofLighting": {"Layer": Q("roof_lights_fancy"), "DamageLevels": [{
                "File": Q("./Data/ships/common/light_blob.png"), "Size": [l["size"], l["size"]], "Z": l["z"],
                "VertexColor": list(l["color"])}]},
        }


def deck_graphics(comp, g, geo, reset_triggers, spin=False, recoil_interval=0.06, spin_speed=None):
    """Componentes de grafico de uma torre de conves (casco, torre, canos, luzes).

    Com arte 3D usa os quadros/normais do meta.json (recuo com calor, giro, torre animada, luzes
    dinamicas roof_lights_fancy e brilho interno lights_add); sem ela, o formato da arte procedural."""
    a3 = g.get("art3d")
    deck_hull_graphics(comp, g)
    deck_turret_graphics(comp, g, geo)
    if a3:
        br = a3["barrel"]
        bl, bw = br["sprite_len"], br["sprite_w"]
        frames, nframes, interval = br["frames"], br["normals"], br["interval"]
        rest, rest_n = br["rest"], br["rest_normals"]
        spin = br["anim"] == "spin"
    else:
        bl = geo["barrel_len"]
        bw = geo["barrel_sprite_w"] if "barrel_sprite_w" in geo else max(0.5, round(geo["barrel_w"] * 2, 3))
        geo["barrel_sprite_w"] = bw
        if spin:
            frames = ["barrel_spin1.png", "barrel_spin2.png", "barrel_spin3.png", "barrel1.png"]
            nframes = ["barrel_normals1.png"] * 4
            interval = 0.05
        else:
            frames = ["barrel2.png", "barrel3.png", "barrel4.png", "barrel5.png", "barrel1.png"]
            nframes = ["barrel_normals1.png"] * 5
            interval = recoil_interval
        rest, rest_n = "barrel1.png", "barrel_normals1.png"
    if spin and spin_speed:
        # giro: os quadros borrados ocupam exatamente 1 intervalo de tiro (chaingun.rules l.1174-1212):
        # AnimationInterval = 1/n com AnimationSpeedFactor = 1/intervalo atual (acompanha o spin-up)
        interval = round(1 / max(1, len(frames) - 1), 4)
    for i, y in enumerate(geo["ys"]):
        anim = {"Size": [bw, bl]}
        if len(frames) > 1:
            anim.update({"AnimationFiles": [Q(f) for f in frames], "NormalsAnimationFiles": [Q(f) for f in nframes],
                         "AnimationInterval": interval, "AnimationStartTime": "MinValue", "ClampAnimation": True})
        else:
            anim.update({"File": Q(frames[0]), "NormalsFile": Q(nframes[0])})
        comp[f"Barrel{i + 1}Graphics"] = {
            "Type": "Graphics", "ChainedTo": "Turret", "Location": [geo["barrel_center"], y], "Rotation": "90d",
            "OperationalToggle": "IsOperational",
            "ResetAnimationTrigger": reset_triggers[i % len(reset_triggers)],
            "OperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [anim]},
            "NonOperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [
                {"File": Q(rest), "NormalsFile": Q(rest_n), "Size": [bw, bl]}]},
        }
        if spin and spin_speed:
            comp[f"Barrel{i + 1}Graphics"]["AnimationSpeedFactor"] = spin_speed
    deck_light_graphics(comp, g)


def _barrels_per_trigger(pattern, nb):
    if nb == 1:
        return 1
    return {"alternate": 1, "pairs": 2}.get(pattern, nb)


# ----------------------------------------------------------------------------- partes comuns (canhoes e defesas)
def crew_positions_for(g, geo):
    """Postos da tripulacao: os do meta da arte 3D (ou os procedurais) cortados em [:crew] (J2R3-12: o meta do
    bs_naval_406 traz 10 postos para 7 tripulantes; a Boiuna le art3d/bs_boiuna_ac, com 5)."""
    w, h = g["size"]
    pos = list(g.get("crew_pos") or C.crew_positions(w, h, g["crew"], geo["pivot"]))
    if len(pos) < g["crew"]:
        raise ValueError(f"{g.get('short')}: {len(pos)} postos de tripulacao para {g['crew']} tripulantes")
    return pos[:g["crew"]]


def ammo_selector(comp, g, modes):
    """UIToggle bs_ammo_type (AvailableChoices do spec, Default 0 = HE) + ModeToggle_i por modo."""
    choices = list(g.get("available_choices") or [_k(m) for m in modes])
    comp["AmmoTypeToggle"] = {"Type": "UIToggle", "ToggleID": Q("bs_ammo_type"),
                              "Default": 0 if 0 in choices else choices[0], "AvailableChoices": choices,
                              "AlwaysAllowInBuildMode": True}
    for m in modes:
        comp[f"ModeToggle_{_k(m)}"] = {"Type": "ModeToggle", "Mode": "AmmoTypeToggle", "OnMode": _k(m)}


def ui_tile_rect(pos, w, h, n):
    """UITileRect da barra do modo na posicao pos da lista (n modos): uma barra por bloco (da esquerda para a direita,
    de baixo para cima); se a peca tem menos blocos que modos (Marimbondo 1x1 com HE/AP), o bloco de baixo a esquerda
    e dividido em n barras lado a lado (fresta de 2/64), para as barras e os botoes de consumo nao se sobreporem."""
    if n > w * h:
        gap = 2
        bw = (50 - gap * (n - 1)) / n
        return [f"{pos * (bw + gap) + 7:g}/64", f"{max(0, h - 1)} + 7/64", f"{bw:g}/64", "1 - 14/64"]
    return [f"{pos % w} + 7/64", f"{max(0, h - 1 - pos // w)} + 7/64", "1 - 14/64", "1 - 14/64"]


def mag_storage(comp, g, m, pos, w, h, n=None):
    """MagStorage_i (+ Splitter_i) de um modo (pos = posicao na lista de n modos; n padrao = modos de g)."""
    k = _k(m)
    n = n or len(g.get("modes") or []) or 1
    st = {
        "Type": "ResourceStorage",
        "ResourceType": m["res"],
        "MaxResources": int(m["storage"]),
        "UITileRect": ui_tile_rect(pos, w, h, n),
        "ReceiveResourceMediaEffects": "&/COMMON_EFFECTS/AmmoDeliver",
        "DropResourcesWhenDestroyed": True,
    }
    if _direct(m):
        # liga so com carregadores para 1 disparo inteiro (cannon_deck.rules l.216-217 / l.259-260)
        st["ToggleOnResources"] = int(m["units_per_shot"])
        st["ToggleOffResources"] = int(m["units_per_shot"]) - 1
    comp[f"MagStorage_{k}"] = st
    if not _direct(m):
        comp[f"Splitter_{k}"] = {"Type": "InlineResourceConverter", "ResourceType": m["res"],
                                 "FromStorage": f"MagStorage_{k}", "FromQuantity": 1,
                                 "ToQuantity": int(m.get("splitter_to_quantity", m.get("shots_per_unit", 1)))}


def mag_consumers(comp, m, selector):
    """Consumidor da tripulacao do modo: ResupplyThreshold = floor(Max/2) e reserva da tripulacao
    (logistics.reserva_tripulacao) pelo common; arma sem seletor passa comp= (exigido com sem_fita, WP01)."""
    k = _k(m)
    thr = C.half(m["storage"])
    if selector:
        C.toggled_consumers(comp, f"MagConsumer_{k}", f"ModeToggle_{k}", m["res"], f"MagStorage_{k}",
                            f"AmmoConsumersOn_{k}", f"AmmoConsumersOff_{k}", threshold=thr)
    else:
        comp[f"MagConsumer_{k}"] = C.mag_consumer(m["res"], f"MagStorage_{k}", "CommandConsumptionToggle",
                                                  threshold=thr, comp=comp)


def intake_fields(g, ctx):
    """(TypeCategories, ReceivableBuffs) a somar na peca pelo transporte (intake.part_fields do WP05)."""
    res = C.call(_intake(), "part_fields", g, ctx) or {}
    cats = list(res.get("TypeCategories_add") or res.get("TypeCategories") or [])
    buffs = list(res.get("ReceivableBuffs_add") or res.get("ReceivableBuffs") or [])
    return cats, buffs


def intake_components(comp, g, ctx):
    """Entrada da arma pela logistica (Fita, acoplamento, esteira) e devolucao: seam do intake (WP05/WP15)."""
    mod = _intake()
    C.call(mod, "weapon_intake", comp, g, ctx)
    C.call(mod, "weapon_return", comp, g, ctx)


def cookoff_hits(g):
    """HitEffects do cook-off de UM modo cheio: g['cookoff_hits'] (lista pronta, ex. PEM do WP08) ou o teto
    g['cookoff_cap'] = {total_damage, radius_m} do spec (SPEC.cookoff.guns: teto 1.x por tipo guardado)."""
    if g.get("cookoff_hits"):
        return list(g["cookoff_hits"])
    cap = g.get("cookoff_cap") or {}
    if not cap.get("total_damage"):
        return None
    return [{"Type": "ExplosiveDamage", "TotalDamage": {"BaseValue": int(cap["total_damage"]), "EffectScaleExponent": 1},
             "Radius": cap["radius_m"], "Delay": 0.05, "Filter": {"Friendlies": True}}]


def cookoff_effects(comp, g, center, modes):
    """Um DeathEffects por modo, escalado pelo enchimento do MagStorage_i (FactorHitEffectsWith, padrao
    thermal_battery.rules l.94-122; IncludeWhenUnderConstruction = false como la). Modo cheio = o teto do spec."""
    hits = cookoff_hits(g)
    if not hits:
        return
    comp[comment("---- cook-off por modo (teto x enchimento do MagStorage_i) ----")] = None
    for m in modes:
        k = _k(m)
        comp[f"DestroyedEffects_{k}"] = {"Type": "DeathEffects", "Location": center,
                                         "FactorHitEffectsWith": f"MagStorage_{k}",
                                         "IncludeWhenUnderConstruction": False, "HitEffects": hits}


def skip_down_for(g):
    """Colunas da fileira de tras sem porta termica (so com esteira, WP15): D.belt_skip_down(g)."""
    if "skip_down" in g:
        return tuple(g["skip_down"] or ())
    try:
        import bs_data as D
        return D.belt_skip_down(g)
    except Exception:   # noqa: BLE001 (build_gun fora do build)
        return ()


def build_gun(g, shot_paths, ctx=None):
    """Retorna (top, info) de uma arma de conves.

    shot_paths: dict (indice do modo, oc_state) -> caminho relativo do arquivo do tiro a partir da pasta da peca.
    ctx: ctx do build_mod (logistica pelo intake); None = ctx minimo do bs_data.
    """
    ctx = _ctx(ctx)
    w, h = g["size"]
    oc = g.get("oc")
    spin = g.get("spin")
    sel = bool(g.get("selector") and len(_modes(g)) > 1)
    g["selector"] = sel
    geo = geometry(g)
    center = [w / 2, h / 2]
    modes = _modes(g)
    nb = len(geo["ys"]) if g.get("art3d") else g["barrels"]["count"]
    pattern = g["barrels"].get("pattern", "alternate" if nb > 1 else "single")
    burst = g.get("burst")
    fi_val, fi_path = _fi_value(g)

    top = {}
    if oc:
        o = {
            "FIRE_INTERVAL_FACTOR": oc["fire_interval_factor"],
            "HALF_SPREAD": f"{oc['half_spread']}d",
            "RECOIL_FACTOR": f"{int(round(oc.get('recoil_factor', 1.5) * 100))}%",
            "HEAT_PER_SHOT": oc["heat_per_shot"],
            "HEAT_PER_SECOND": oc.get("heat_per_second", 0),
        }
        if spin:
            o["MAX_SPIN"] = oc.get("max_spin", spin["max"])
            if oc.get("spin_up"):
                o["SPIN_UP_TIME"] = oc["spin_up"]
        if g.get("stun"):
            o["CREW_STUN_DURATION"] = g["stun"].get("oc_duration", g["stun"]["duration"])
            o["CREW_STUN_RADIUS"] = g["stun"].get("oc_radius", g["stun"]["radius"])
        top["OVERCLOCK"] = o
        top["HEAT_TO_RESOURCE"] = C.HEAT_TO_RESOURCE
    top["FIRE_INTERVAL"] = g["fire_interval"]
    if spin:
        top["SPIN"] = {"MAX": spin["max"], "UP_TIME": spin["up"], "DOWN_TIME": spin["down"]}

    add_cats, add_buffs = intake_fields(g, ctx)
    part = {}
    part["NameKey"] = Q(f"Parts/{g['key']}")
    part["IconNameKey"] = Q(f"Parts/{g['key']}Icon")
    part["DescriptionKey"] = Q(f"Parts/{g['key']}Desc")
    part["ID"] = C.pid(g["short"])
    part["EditorGroups"] = [Q(C.EDITOR_GROUP), Q("WeaponsProjectile")] if not g.get("defense") else \
        [Q(C.EDITOR_GROUP), Q("WeaponsProjectile"), Q("Defenses")]
    part["Resources"] = [[r, q] for r, q in g["cost"]]
    part["Size"] = [w, h]
    part["SelectionPriority"] = 1
    part["MaxHealth"] = g["hp"]
    cats = ["weapon", "uses_ammo", "is_crewed"]
    for c in list(g.get("extra_categories", [])) + add_cats:
        if c not in cats:
            cats.append(c)
    part["TypeCategories"] = cats
    part["SignificanceToggle"] = "ScorchedToggle"
    buffs = ["RateOfFire"] if spin else []
    buffs += [b for b in add_buffs if b not in buffs]
    part["ReceivableBuffs : ^/0/ReceivableBuffs"] = buffs
    part["ProhibitedBy : ^/0/ProhibitedBy"] = ["tall"]
    ring = C.tall_ring(w, h, g.get("ring", 1))
    if ring:
        part["ProhibitRects"] = ring
    part["AllowedDoorLocations"] = C.door_locations(w, h)
    part["EditorIcon"] = C.editor_icon(w, h, geo["overhang"])

    comp = {}
    hybrid = bool(g.get("hybrid"))
    comp.update(C.standard_toggles(bool(oc), g["cp"], defense=hybrid, fire_pref_default=g.get("fire_pref_default", 2)))

    # ------------------------------------------------------------------ municao
    comp[comment("---- municao: por modo i, MagStorage_i + Splitter_i + MagConsumer_i (indice da tabela) ----")] = None
    if sel:
        ammo_selector(comp, g, modes)
    for i, m in enumerate(modes):
        mag_storage(comp, g, m, i, w, h, len(modes))
        mag_consumers(comp, m, sel)
    if sel:
        for m in modes:
            k = _k(m)
            comp[f"HasAmmo_{k}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{k}", _ammo_src(m)], "Mode": "All"}
        comp["AmmoPrereq"] = {"Type": "MultiToggle", "Toggles": [f"HasAmmo_{_k(m)}" for m in modes], "Mode": "Any"}
    else:
        comp["AmmoPrereq"] = {"Type": "MultiToggle", "Toggles": [_ammo_src(modes[0])], "Mode": "Any"}
    if sel and oc:
        for m in modes:
            k = _k(m)
            comp[f"FireToggle_{k}_N"] = {"Type": "MultiToggle",
                                         "Toggles": [f"ModeToggle_{k}", "{ Toggle=IsOverclocked; Invert=true }"],
                                         "Mode": "All"}
            comp[f"FireToggle_{k}_OC"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{k}", "IsOverclocked"],
                                          "Mode": "All"}
    # logistica (Fita / acoplamento / esteira e devolucao) pelo seam do intake; sem o modulo, so a tripulacao
    intake_components(comp, g, ctx)

    # ------------------------------------------------------------------ spin-up
    if spin:
        comp[comment("---- spin-up (chaingun.rules l.191-287) ----")] = None
        max_interval = g["fire_interval"] * (oc["fire_interval_factor"] if oc else 1)
        comp["IsFiringTimer"] = {"Type": "Timer", "Duration": round(max(1.0, max_interval * 1.25), 3),
                                 "StartTrigger": "Turret", "ResetTrigger": "Turret",
                                 "StartExpired": True, "InvertToggle": True}
        comp["IsSpinning"] = {"Type": "MultiToggle", "Toggles": ["IsFiringTimer", "AmmoPrereq"], "Mode": "All"}
        acc = {
            "Type": "ValueAccumulator",
            "AccumulatingToggle": "IsSpinning",
            "MinValue": 1,
            "BaseValue": "&MinValue",
        }
        if oc:
            acc["MaxValue"] = {"BaseValue": "&~/SPIN/MAX",
                               "Modifiers": [{"Type": "Buff", "BuffType": "Overclock", "ModificationMode": "Replace",
                                              "MinValue": "&~/OVERCLOCK/MAX_SPIN", "MaxValue": "&MinValue"}]}
        else:
            acc["MaxValue"] = "&~/SPIN/MAX"
        acc["AccumulationRate"] = "((&~/SPIN/MAX) - 1) / (&~/SPIN/UP_TIME)"
        if oc and oc.get("spin_up"):
            # spin-up mais curto em overclock (chaingun.rules l.232-245: AccumulationRate BuffRemap Overclock;
            # RemapTo parte do BaseValue, como o Range do pd_shot.rules)
            acc["AccumulationRate"] = {
                "BaseValue": "((&~/SPIN/MAX) - 1) / (&~/SPIN/UP_TIME)",
                "Modifiers": [{"Type": "BuffRemap", "BuffType": "Overclock", "ModificationMode": "Replace",
                               "RemapFrom": [0, 1],
                               "RemapTo": ["&../../../BaseValue",
                                           "((&~/OVERCLOCK/MAX_SPIN) - 1) / (&~/OVERCLOCK/SPIN_UP_TIME)"]}]}
        acc["DissipationRate"] = "((&~/SPIN/MAX) - 1) / (&~/SPIN/DOWN_TIME)"
        comp["SpinUp"] = acc
        comp["RateOfFireBuff"] = {"Type": "SelfBuffProvider", "BuffType": "RateOfFire", "BuffAmount": 1,
                                  "BuffMultiplier": "SpinUp"}

    # ------------------------------------------------------------------ torre
    comp[comment("---- torre ----")] = None
    turret = {
        "Type": "TurretWeapon",
        "Location": geo["pivot"],
        "Rotation": "-90d",
        "OperationalToggle": "IsOperational",
        "AutoFireToggle": "AutoFireToggle",
        "FirePermissionToggle": "FireModeToggle",
        "FireInterval": fi_val,
        "FiringArc": f"{g['arc']}d",
        "RotateSpeed": f"{g['rotate']}d",
        "FireThresholdAngle": f"{g.get('threshold', 2)}d",
        "AIFirepowerRating": "&~/Part/StatsByCategory/0/Stats/DamagePerSecond",
        "Emitter": "TargetEmitterProxy",
        # atira por cima do casco (Low) e das nossas torres de conves (High), como o tiro, que tambem passa por
        # cima delas (shots.OWN_SHIP_PASS): manipulator_beam_emitter.rules l.447-448
        "IgnoreFriendlyShipLowLOSChecks": True,
        "IgnoreFriendlyShipHighLOSChecks": True,
        "AutoTargets": [{"TargetType": "ShipParts", "Toggle": "AutoTargetToggle"}],
        "BlueprintArcSprite": {"Texture": "&/INDICATORS/WeaponArc", "Size": [0, 1.5], "Color": [255, 0, 0, 63]},
        "BlueprintArcRadius": 10,
        "BlueprintArcSpriteSegments": 64,
        # setor de alcance ao atacar: no 0.30.3/0.30.4 cada TurretWeapon precisa do proprio (cannon_deck.rules 0.30.3
        # l.637; o SW:ACD declara em 120 de 125 torres); o 0.30.5 ignora. Sem ele o alcance nao aparecia no jogo (X1)
        "CoverageSectorArc": dict(C.COVERAGE_SECTOR_ARC),
    }
    if g.get("searches"):
        turret["TargetSearchesPerSecond"] = g["searches"]
    if hybrid:
        # Atacar / Defender / Ambos, como a Flak vanilla (flak_cannon_large.rules l.444-477)
        turret["TargetSearchesPerSecond"] = g.get("searches", 6)
        # setor de alcance sempre visivel na defesa, como point_defense.rules 0.30.3 l.375 e
        # flak_cannon_large.rules 0.30.3 l.460 (X1)
        turret["AlwaysShowCoverage"] = True
        turret["AllowShipWideExplicitTargetsToggle"] = "FirePrefAttack"
        turret["EstimateFirepowerToggle"] = "AttackToggle"
        turret["AllowDirectControlToggle"] = "FirePrefAttack"
        turret["AutoTargets"] = [
            {"TargetType": "Bullets", "BulletTargetCategories": g.get("anti_categories", C.ANTI_SHOT_CATEGORIES),
             "Toggle": "DefendToggle"},
            {"TargetType": "ShipParts", "Toggle": "AttackToggle", "Overridable": True},
        ]
    comp["Turret"] = turret
    comp["TurretCollider"] = {"Type": "CircleCollider", "Location": "&../Turret/Location",
                              "Radius": geo["collider"], "IsHigh": True}
    comp["ReloadProgressBar"] = {"Type": "ProgressBar", "OperationalToggle": "IsOperational", "ShowProgressFor": "Turret"}

    # ------------------------------------------------------------------ gatilhos dos canos
    triggers = []
    if pattern == "alternate" and nb > 1:
        comp["ShootCycle"] = {"Type": "ModeCycle", "ModeRange": [0, nb - 1], "IncrementTrigger": "Turret",
                              "StartingMode": nb - 1}
        for i in range(nb):
            comp[f"ShootTrigger{i + 1}"] = {"Type": "ModeTrigger", "Mode": "ShootCycle", "TriggerInModes": [i]}
            triggers.append(f"ShootTrigger{i + 1}")
    elif pattern == "pairs" and nb >= 4:
        # pares alternados: (1,3) e (2,4) se revezam a cada disparo
        half = nb // 2
        comp["ShootCycle"] = {"Type": "ModeCycle", "ModeRange": [0, half - 1], "IncrementTrigger": "Turret",
                              "StartingMode": half - 1}
        for j in range(half):
            comp[f"ShootTrigger{j + 1}"] = {"Type": "ModeTrigger", "Mode": "ShootCycle", "TriggerInModes": [j]}
        triggers = [f"ShootTrigger{i % half + 1}" for i in range(nb)]
    else:
        triggers = ["Turret"] * nb

    # ------------------------------------------------------------------ emissores (blocos por tipo x overclock)
    comp[comment("---- emissores: um bloco por tipo de municao (e por estado de overclock) ----")] = None
    oc_states = [False, True] if oc else [False]
    spread = g["spread"]
    # raio anti-phasing comeca no anel da propria torre, nunca atras do pivo nem dentro da peca vizinha
    # (cannon_deck: min(2, 3.75 - 1.5) = 2; cannon_med 2 - 1.5 = 0.5 a frente do pivo)
    anti_phasing = round(min(2.0, max(0.0, geo["muzzle"] - (geo["collider"] or 0))), 2)
    for m in modes:
        k = _k(m)
        for s in oc_states:
            shot = shot_paths[(k, s)]
            base = {
                "Type": "BulletEmitter",
                "ChainedTo": "Turret",
                "FireTrigger": VOID,
                "GetTargetFrom": "Turret",
                "Location": [geo["muzzle"], 0],
                "OperationalToggle": "IsOperational",
                "Bullet": f"&<{shot}>",
                "Spread": [f"-{spread}d", f"{spread}d"] if not s else
                ["-(&~/OVERCLOCK/HALF_SPREAD)", "(&~/OVERCLOCK/HALF_SPREAD)"],
                "ResourceStorage": _ammo_src(m),
                "ResourcesUsed": int(m.get("units_per_shot", 1)),
                "Recoil": g["recoil"] if not s else f"{g['recoil']} * (&~/OVERCLOCK/RECOIL_FACTOR)",
                "AntiPhasingRaycastDistance": anti_phasing,
                "AntiPhasingRaycastIgnoreLowCollisions": True,
            }
            burst_cfg = burst
            if s and oc and oc.get("burst"):
                burst_cfg = oc["burst"]
            inner = {"TargetEmitter": base}
            for i, y in enumerate(geo["ys"]):
                e = {"Location": [geo["muzzle"], y], "FireTrigger": triggers[i]}
                if burst_cfg:
                    e["Burst"] = burst_cfg["count"]
                    e["BurstDelay"] = burst_cfg["delay"]
                    e["UseResourcePerShotInBurst"] = True
                inner[f"Emitter{i + 1} : TargetEmitter"] = e
            tname, inv = _fire_block_toggle(g, k, s)
            if tname is None:
                # arma sem seletor e sem overclock: emissores direto na lista de componentes
                comp.update(inner)
                continue
            block = {"Type": "ToggledComponents", "Toggle": tname}
            if inv:
                block["Invert"] = True
            block["IncludeInBlueprints"] = (not s)
            block["Components"] = inner
            comp[f"Fire_{k}_{'OC' if s else 'N'}"] = block

    # proxies (a torre e os efeitos falam com o emissor ativo atraves deles)
    comp["TargetEmitterProxy"] = {"Type": "EmitterProxy", "ComponentID": "TargetEmitter", "ChainedTo": "Turret"}
    proxies_n, proxies_oc, proxies_all = [], [], []
    for i, y in enumerate(geo["ys"]):
        p = f"Emitter{i + 1}Proxy"
        comp[p] = {"Type": "EmitterProxy", "ComponentID": f"Emitter{i + 1}", "ChainedTo": "Turret",
                   "Location": [geo["muzzle"], y]}
        proxies_all.append(p)
        if oc:
            comp[f"{p}_OC : {p}"] = {"ProxyToggle": "IsOverclocked"}
            comp[f"{p}_N : {p}_OC"] = {"InvertProxyToggle": True}
            proxies_oc.append(f"{p}_OC")
            proxies_n.append(f"{p}_N")
        else:
            proxies_n.append(p)

    # ------------------------------------------------------------------ efeitos de disparo
    fx = g["fx"]

    def fire_media(sound, shake, particles):
        media = [f"&<{p}>" for p in particles]
        snd = {"Volume": fx.get("volume", 1.0), "SpeedVariation": fx.get("speed_var", 0.15)}
        if isinstance(sound, list):
            snd = {"RandomSounds": [Q(s) for s in sound], **snd}
        else:
            snd = {"Sound": Q(sound), **snd}
        if fx.get("max_concurrent"):
            snd["MaxConcurrent"] = fx["max_concurrent"]
        from rules_dsl import Inh
        media.append(Inh("/BASE_SOUNDS/AudioExterior", snd))
        if shake:
            media.append(Inh("/BASE_SHAKE", {"ShakeAmount": shake, "Duration": fx.get("shake_time", 0.5)}))
        return media

    for i, p in enumerate(proxies_n):
        comp[f"FireEffect{i + 1}"] = {"Type": "TriggeredEffects", "ChainedTo": p, "Trigger": p,
                                      "Location": [fx.get("offset", 0), 0],
                                      "MediaEffects": fire_media(fx["sound"], fx.get("shake", 0), fx["particles"])}
    for i, p in enumerate(proxies_oc):
        comp[f"Overclock_FireEffect{i + 1}"] = {"Type": "TriggeredEffects", "ChainedTo": p, "Trigger": p,
                                                "Location": [fx.get("offset", 0), 0],
                                                # particles_oc: clarao proprio do overclock (plasma: mais quente e maior)
                                                "MediaEffects": fire_media(fx.get("sound_oc", fx["sound"]),
                                                                           fx.get("shake_oc", fx.get("shake", 0)),
                                                                           fx.get("particles_oc", fx["particles"]))}
    # fumaca de recuo na culatra (fx["breech"] / fx["breech_oc"], copias escaladas do bsgen/caliber_fx.py; o atraso
    # vai no Delay da propria copia): outro TriggeredEffects nos MESMOS proxies do clarao, na raiz do cano
    # (Location relativa ao proxy da boca = raiz - boca). Sem "breech" (plasma, metralhadoras) nada muda.
    if fx.get("breech"):
        bx = round(geo["front"] - geo["muzzle"], 4)
        for i, p in enumerate(proxies_n):
            comp[f"RecoilSmoke{i + 1}"] = {"Type": "TriggeredEffects", "ChainedTo": p, "Trigger": p,
                                           "Location": [bx, 0], "MediaEffects": [f"&<{x}>" for x in fx["breech"]]}
        for i, p in enumerate(proxies_oc):
            comp[f"Overclock_RecoilSmoke{i + 1}"] = {
                "Type": "TriggeredEffects", "ChainedTo": p, "Trigger": p, "Location": [bx, 0],
                "MediaEffects": [f"&<{x}>" for x in fx.get("breech_oc", fx["breech"])]}

    # atordoamento da tripulacao pelo sopro (so armas grandes)
    if g.get("stun"):
        st = g["stun"]
        comp["StunTrigger"] = {"Type": "MultiTrigger", "Triggers": proxies_all}
        dur = {"BaseValue": st["duration"]}
        rad = {"BaseValue": st["radius"]}
        if oc:
            dur = {"BaseValue": st["duration"], "BuffType": "Overclock", "BuffMode": "Lerp", "MinValue": "&BaseValue",
                   "MaxValue": "&~/OVERCLOCK/CREW_STUN_DURATION"}
            rad = {"BaseValue": st["radius"], "BuffType": "Overclock", "BuffMode": "Lerp", "MinValue": "&BaseValue",
                   "MaxValue": "&~/OVERCLOCK/CREW_STUN_RADIUS"}
        comp["StunEffect"] = {"Type": "TriggeredEffects", "Location": geo["pivot"], "Trigger": "StunTrigger",
                              "HitEffects": [{"Type": "AreaCrewStun", "Duration": dur, "Falloff": 1, "Radius": rad,
                                              "Filter": {"Friendlies": True, "IgnoreInvulnerability": True},
                                              "Cumulative": True, "HitShipOnly": True}]}

    # ------------------------------------------------------------------ tripulacao
    comp[comment("---- tripulacao ----")] = None
    comp.update(C.crew_block(crew_positions_for(g, geo), "AmmoPrereq"))

    # ------------------------------------------------------------------ overclock
    if oc:
        comp[comment("---- overclock (base_part_overclock.rules + cannon_deck.rules l.323-413) ----")] = None
        comp.update(C.overclock_machinery(center, w, h, proxies_all, has_constant_heat=oc.get("heat_per_second", 0) > 0,
                                          skip_down=skip_down_for(g)))
        comp["PeakHeatGenerationValue"] = {
            "Type": "StaticValue",
            "SHOT_HEAT_PER_SECOND": "(&~/OVERCLOCK/HEAT_PER_SHOT) * (&~/Part/SecondaryToolTip/StatsByCategory/0/Stats/ShotsPerSecond)",
            "Value": "(&~/OVERCLOCK/HEAT_PER_SECOND) + (&SHOT_HEAT_PER_SECOND)",
        }
        comp["HeatGenerationStatProvider"] = {"Type": "StatProvider", "Stat": "HeatGeneration",
                                              "OperationalToggle": "OverclockModeToggle",
                                              "ValueFrom": "PeakHeatGenerationValue"}

    # ------------------------------------------------------------------ graficos
    comp[comment("---- graficos ----")] = None
    if spin:
        # intervalo de tiro atual (com spin-up e overclock) e seu inverso, para a velocidade do giro dos canos
        comp["FireIntervalValue"] = {"Type": "BuffableValue", "Value": fi_val}
        comp["InverseShotInterval"] = {"Type": "MultiValue", "Values": ["FireIntervalValue"], "OneOver": True,
                                       "Mode": "Add"}
    deck_graphics(comp, g, geo, proxies_all, spin=bool(spin),
                  recoil_interval=g["barrels"].get("recoil_frame", 0.06),
                  spin_speed="InverseShotInterval" if spin else None)

    # ------------------------------------------------------------------ efeitos / UI
    comp.update(C.destroyed_effects(center, w, h))
    cookoff_effects(comp, g, center, modes)
    comp["Indicators"] = C.weapon_indicators(center, "AmmoPrereq", bool(oc), "&~/FIRE_INTERVAL")
    comp["Blueprints"] = C.blueprint(w, h)

    part["Components : ^/0/Components"] = comp

    # ------------------------------------------------------------------ stats
    m0 = modes[0]
    part["Stats"] = {
        "CrewRequired": "&~/Part/Components/PartCrew/Crew",
        "AmmoCapacity": f"&~/Part/Components/MagStorage_{_k(m0)}/MaxResources",
    }
    if shots_per_mag_stat(m0):
        part["Stats"]["BSShotsPerMag"] = f"&~/Part/Components/Splitter_{_k(m0)}/ToQuantity"
    if g.get("stun"):
        part["Stats"]["CrewStunDuration"] = [0, "&~/Part/Components/StunEffect/HitEffects/0/Duration/BaseValue"]
        part["Stats"]["CrewStunRadius"] = "&~/Part/Components/StunEffect/HitEffects/0/Radius/BaseValue"

    shots_per_trigger = _barrels_per_trigger(pattern, nb) * (burst["count"] if burst else 1)
    spin_max = spin["max"] if spin else 1
    cats_stats = []

    def em_path(k, s):
        if _fire_block_toggle(g, k, s)[0] is None:
            return "&~/Part/Components/TargetEmitter"
        return f"&~/Part/Components/Fire_{k}_{'OC' if s else 'N'}/Components/TargetEmitter"

    for m in modes:
        k = _k(m)
        em = em_path(k, False)
        st = {
            "DamagePerShot": f"{em}/Bullet/STAT_DAMAGE",
            "ShotsPerSecond": f"{shots_per_trigger} * {spin_max} / ({fi_path})",
            "DamagePerSecond": "(&DamagePerShot) * (&ShotsPerSecond)",
            "Damage": ["&../DamagePerShot", "&../DamagePerSecond"],
        }
        if m.get("show_pen", True):
            st["Penetration"] = f"{em}/Bullet/STAT_PENETRATION"
        if spin:
            st["ROF"] = [f"{shots_per_trigger} / ({fi_path})", "&../ShotsPerSecond"]
        else:
            st["ROF"] = "&ShotsPerSecond"
        st.update({
            # Range com BuffRemap de overclock (pd_shot): o valor base fica em Range/BaseValue
            "Range": f"{em}/Bullet/Range" + ("/BaseValue" if m.get("oc_range") else ""),
            "Arc": "deg(&~/Part/Components/Turret/FiringArc)",
            "Spread": f"deg({em}/Spread/1)",
            "TurretSpeed": "deg(&~/Part/Components/Turret/RotateSpeed)",
            "ShotSpeed": f"{em}/Bullet/Speed",
        })
        if m.get("shot_targetable", True):
            # tiro <= 30 mm nao tem Targetable (a referencia nao existiria)
            st["ShotHP"] = f"{em}/Bullet/Components/Targetable/Health"
        st.update({
            "AmmoPerShot": f"{em}/ResourcesUsed" if _direct(m) else
            f"({em}/ResourcesUsed) / (&~/Part/Components/Splitter_{k}/ToQuantity)",
            "AmmoPerSecond": "(&AmmoPerShot) * (&ShotsPerSecond)",
            "ShotAmmoUsage": ["&../AmmoPerShot", "&../AmmoPerSecond"],
        })
        if burst:
            st["Burst"] = burst["count"]
        cats_stats.append({"NameKey": Q(f"StatCategories/BSAmmo_{m['ammo']}"), "Stats": st})
    part["StatsByCategory"] = cats_stats

    if oc:
        k = _k(m0)
        em = em_path(k, True)
        oc_burst = oc.get("burst") or burst
        spt = _barrels_per_trigger(pattern, nb) * (oc_burst["count"] if oc_burst else 1)
        oc_spin = oc.get("max_spin", spin_max) if spin else 1
        oc_stats = {
            "DamagePerShot": f"{em}/Bullet/STAT_DAMAGE",
            "ShotsPerSecond": f"{spt} * {oc_spin} / (({fi_path}) * (&~/OVERCLOCK/FIRE_INTERVAL_FACTOR))",
            "DamagePerSecond": "(&DamagePerShot) * (&ShotsPerSecond)",
            "Damage": ["&../DamagePerShot", "&../DamagePerSecond"],
            "ROF": "&ShotsPerSecond",
            "Range": f"{em}/Bullet/OVERCLOCK/RANGE" if m0.get("oc_range") else f"{em}/Bullet/Range",
            "Spread": "deg(&~/OVERCLOCK/HALF_SPREAD)",
            "ShotSpeed": f"{em}/Bullet/Speed",
            "HeatPerShot": "(&~/OVERCLOCK/HEAT_PER_SHOT)",
            "HeatGeneration": "(&~/OVERCLOCK/HEAT_PER_SECOND)",
        }
        if m0.get("show_pen", True):
            oc_stats["Penetration"] = f"{em}/Bullet/STAT_PENETRATION"
        if oc_burst:
            oc_stats["Burst"] = oc_burst["count"]
        part["SecondaryToolTip"] = {
            "TitleKey": Q("StatCategories/Overclocked"),
            "DescriptionKey": Q(f"Parts/{g['key']}OverclockDesc"),
            "StatsByCategory": [{"NameKey": Q(f"StatCategories/BSAmmo_{m0['ammo']}"), "Stats": oc_stats}],
        }

    top["Part : " + C.base_part_path(w, h, bool(oc))] = part
    info = {"geo": geo, "center": center}
    return top, info


# ----------------------------------------------------------------------------- gancho do build_mod
def write_art(out, pdir, g, info, ctx):
    """Arte da peca: make_art (arte 3D da pasta g['art3d_dir'] ou procedural) ou, com --no-art, a copia dos PNGs."""
    art = ctx.get("art")
    if art:
        # make_art.art_dir(g) ja le art3d/<art3d_dir> (Boiuna = bs_boiuna_ac); g vai inteiro, para a previa
        # docs/preview/<short>.png manter o nome do ID da peca (bs_nuke_howitzer.png)
        art.gun_art(out, pdir, g, info)
    elif g.get("art3d"):
        import art3d as A3
        A3.copy_files(out.root, pdir, g.get("art3d_dir") or g["short"], g["art3d"])


def parts(out, D, ctx):
    """Escreve os 12 canhoes (parts/<curto>/<curto>.rules) com os tiros ja escritos (ctx['shot_rel'])."""
    shots = {s["file"]: s for s in D.SHOTS}
    for g in D.GUNS:
        pdir = f"parts/{g['short']}"
        sp, missing = {}, []
        for m in g["modes"]:
            k = _k(m)
            states = [(False, m["shot"])] + ([(True, m.get("shot_oc") or m["shot"])] if g.get("oc") else [])
            for st, sid in states:
                rel = ctx["shot_rel"].get(sid)
                if rel is None:
                    missing.append(sid)
                    continue
                sp[(k, st)] = ctx["relpath"](pdir, rel)
            m["shot_targetable"] = bool((shots.get(m["shot"]) or {}).get("targetable", True))
        if missing:
            ctx["warn"](f"peca {g['id']} pulada: tiros nao escritos {sorted(set(missing))}")
            continue
        top, info = build_gun(g, sp, ctx)
        rel = f"{pdir}/{g['short']}.rules"
        code = f" \"{g['codename']}\"" if g.get("codename") else ""
        out.text(rel, render(top, ctx["header"] + f"\nArma: {g['name_en']} / {g['name_pt']}{code}"))
        write_art(out, pdir, g, info, ctx)
        ctx["add_part"](g["id"])


# ----------------------------------------------------------------------------- conferencia (selfcheck)
def rules_root(path):
    """Arvore do arquivo .rules (parser do tools/rules_lint.py) ou None."""
    import rules_lint as RL
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    root, errs, _w = RL.parse_text(text, RL.RFile("fs", path, path))
    return root if not errs else None


def node_at(node, path):
    """No pelo caminho 'A/B/0/C' (nomes sem a heranca; numeros = elemento de lista); None se nao existir."""
    for seg in [x for x in path.split("/") if x]:
        if node is None:
            return None
        if seg.isdigit() and node.kind == "list":
            i = int(seg)
            node = node.children[i] if i < len(node.children) else None
            continue
        node = next((c for c in node.children if c.name == seg), None)
    return node


def num_at(node, path=""):
    """Valor numerico do no (grupo {BaseValue}: o BaseValue; '45d' / '60%' sem o sufixo); None se nao for numero."""
    n = node_at(node, path) if path else node
    if n is None:
        return None
    if n.kind == "group":
        return num_at(n, "BaseValue")
    if n.kind != "value" or n.value is None:
        return None
    v = n.value.strip().strip('"').rstrip("d%")
    try:
        return float(v)
    except ValueError:
        return None


def list_at(node, path):
    n = node_at(node, path)
    if n is None or n.kind != "list":
        return None
    return [(c.value or "").strip() for c in n.children]


def _eq(a, b, tol=1e-6):
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))


def _rect_num(txt):
    """Valor de um termo de UITileRect ('1 + 7/64', '33/64'): so numeros e + - * / ( ); None se outra coisa."""
    t = (txt or "").strip().strip('"')
    if not t or any(ch not in "0123456789.+-*/() " for ch in t):
        return None
    try:
        return float(eval(t, {"__builtins__": {}}, {}))  # noqa: S307 - so aritmetica, conferida acima
    except Exception:  # noqa: BLE001
        return None


def check_ui_rects(short, comp, idxs):
    """Checklist 3.1: as barras MagStorage_i da peca nao se sobrepoem (cada tipo enche a sua barra)."""
    errs, rects = [], []
    for i in idxs:
        r = list_at(comp, f"MagStorage_{i}/UITileRect")
        v = [_rect_num(x) for x in (r or [])]
        if len(v) != 4 or None in v or v[2] <= 0 or v[3] <= 0:
            errs.append(f"{short}: MagStorage_{i} UITileRect ilegivel {r}")
            continue
        for j, o in rects:
            if min(v[0] + v[2], o[0] + o[2]) - max(v[0], o[0]) > 1e-6 and \
                    min(v[1] + v[3], o[1] + o[3]) - max(v[1], o[1]) > 1e-6:
                errs.append(f"{short}: barras MagStorage_{j} e MagStorage_{i} sobrepostas ({o} x {v})")
        rects.append((i, v))
    return errs


def check_shots_per_mag(short, part, m0):
    """Linha 'Disparos por carga' (Stats/BSShotsPerMag) so quando o 1o modo escrito gasta 1 carga do Splitter por
    disparo (shots_per_mag_stat); com ResourcesUsed > 1 (Boiuna) ela mostraria o ToQuantity (2) como disparos."""
    st = node_at(part, "Stats/BSShotsPerMag")
    want = int(m0.get("resources_used_per_shot", m0.get("units_per_shot", 1))) == 1
    ref = f"&~/Part/Components/Splitter_{_k(m0)}/ToQuantity"
    if want and (st is None or (st.value or "").strip().strip('"') != ref):
        return [f"{short}: Stats/BSShotsPerMag {st.value if st is not None else None} != {ref}"]
    if not want and st is not None:
        return [f"{short}: Stats/BSShotsPerMag presente com ResourcesUsed {m0.get('resources_used_per_shot')} por "
                f"disparo (mostraria o ToQuantity como disparos por carga)"]
    return []


def selfcheck(mod_dir, SPEC):
    """Confere os canhoes escritos contra o spec (numeros brutos de SPEC.weapons) e o bs_data (os transformados pelos
    switches: dano das pecas seguintes, alvejavel): MagStorage_i (e barras UITileRect sem sobreposicao), Splitter_i,
    ResourcesUsed, AvailableChoices, Crew/CommandPoints, FIRE_INTERVAL, a linha BSShotsPerMag (so com 1 carga por
    disparo) e, por tiro (sem overclock), dano direto, PenetratingOperational, explosao/raio, HitShield, Penetration,
    blindagem, Targetable, nenhum campo 0.30.5 e, na granada de contato da Boiuna, as duas cargas (explosao com fogo +
    so estrutural) no contato e no fim do alcance (Death/OnDeath)."""
    import bs_data as D
    errs = []
    weapons = {w["id"]: w for w in SPEC["weapons"]}
    trans = {w["id"]: w for w in D.SPEC_WEAPONS}
    shots = {s["file"]: s for s in D.SHOTS}
    for g in D.GUNS:
        w = weapons.get(g["id"])
        if w is None:
            errs.append(f"{g['id']} fora do spec")
            continue
        short = g["short"]
        root = rules_root(os.path.join(mod_dir, "parts", short, f"{short}.rules"))
        if root is None:
            errs.append(f"{short}: parts/{short}/{short}.rules ausente ou ilegivel")
            continue
        part = node_at(root, "Part")
        comp = node_at(part, "Components")
        if not _eq(num_at(comp, "PartCrew/Crew"), w["crew"]):
            errs.append(f"{short}: Crew {num_at(comp, 'PartCrew/Crew')} != {w['crew']}")
        if not _eq(num_at(comp, "CommandConsumer/CommandPoints"), w["command_points"]):
            errs.append(f"{short}: CommandPoints {num_at(comp, 'CommandConsumer/CommandPoints')} != {w['command_points']}")
        if w.get("fire_interval_s") and not _eq(num_at(root, "FIRE_INTERVAL"), w["fire_interval_s"], 1e-3):
            errs.append(f"{short}: FIRE_INTERVAL {num_at(root, 'FIRE_INTERVAL')} != {w['fire_interval_s']}")
        sel = len(w["ammo_modes"]) > 1
        if sel:
            ac = list_at(comp, "AmmoTypeToggle/AvailableChoices")
            if ac != [str(x) for x in (w.get("available_choices") or [])]:
                errs.append(f"{short}: AvailableChoices {ac} != {w.get('available_choices')}")
        for m in w["ammo_modes"]:
            i = m["index"]
            if not _eq(num_at(comp, f"MagStorage_{i}/MaxResources"), m["internal_storage_units"]):
                errs.append(f"{short}: MagStorage_{i} {num_at(comp, f'MagStorage_{i}/MaxResources')} != "
                            f"{m['internal_storage_units']}")
            if not _eq(num_at(comp, f"Splitter_{i}/ToQuantity"), m["splitter_to_quantity"]):
                errs.append(f"{short}: Splitter_{i} ToQuantity {num_at(comp, f'Splitter_{i}/ToQuantity')} != "
                            f"{m['splitter_to_quantity']}")
            if node_at(comp, f"MagConsumer_{i}") is None and node_at(comp, f"AmmoConsumersOn_{i}/Components/MagConsumer_{i}") is None:
                errs.append(f"{short}: sem MagConsumer_{i}")
            cand = [f"Fire_{i}_N/Components/TargetEmitter", "TargetEmitter"]
            em = next((node_at(comp, c) for c in cand if node_at(comp, c) is not None), None)
            if em is None or not _eq(num_at(em, "ResourcesUsed"), m["resources_used_per_shot"]):
                errs.append(f"{short}/{m['key']}: ResourcesUsed {num_at(em, 'ResourcesUsed') if em else None} != "
                            f"{m['resources_used_per_shot']}")
            if em is not None and (node_at(em, "ResourceStorage") is None
                                   or node_at(em, "ResourceStorage").value != f"Splitter_{i}"):
                errs.append(f"{short}/{m['key']}: o emissor nao puxa do Splitter_{i}")
            errs += _check_gun_shot(mod_dir, w, m, (trans.get(g["id"]) or w)["ammo_modes"], shots, D)
        errs += check_ui_rects(short, comp, [m["index"] for m in w["ammo_modes"]])
        k0 = _k(g["modes"][0])
        errs += check_shots_per_mag(short, part, next((m for m in w["ammo_modes"] if m["index"] == k0),
                                                      w["ammo_modes"][0]))
    return errs


def _check_blasts(where, exps, want, fire_pct=None):
    """Compara as ExplosiveDamage (na ordem) com want = [(nome, TotalDamage, Radius, so_estrutural)]: dano, raio, o
    filtro so estrutural (OperationalHealth false / StructuralHealth true) e a chance de fogo da explosao principal."""
    errs = []
    if len(exps) != len(want):
        errs.append(f"{where}: {len(exps)} ExplosiveDamage, esperado {len(want)}")
    for (name, total, radius, struct), e in zip(want, exps):
        if not _eq(num_at(e, "TotalDamage"), total) or not _eq(num_at(e, "Radius"), radius):
            errs.append(f"{where}: {name} {num_at(e, 'TotalDamage')} r{num_at(e, 'Radius')} != {total} r{radius}")
        op = (getattr(node_at(e, "Filter/OperationalHealth"), "value", None) or "").strip().lower()
        sh = (getattr(node_at(e, "Filter/StructuralHealth"), "value", None) or "").strip().lower()
        if struct and (op != "false" or sh != "true"):
            errs.append(f"{where}: {name} sem o filtro so estrutural (OperationalHealth {op or '-'}, "
                        f"StructuralHealth {sh or '-'})")
        if not struct and op == "false":
            errs.append(f"{where}: {name} com OperationalHealth false")
        if not struct and fire_pct is not None and not _eq(num_at(e, "StatusChancePerNDamage"), fire_pct):
            errs.append(f"{where}: {name} chance de fogo {num_at(e, 'StatusChancePerNDamage')} != {fire_pct}%")
    return errs


def _check_gun_shot(mod_dir, w, m, tmodes, shots, D):
    """Um tiro (sem overclock) de canhao contra o spec."""
    errs = []
    sid = m["shot_id"].split(".", 1)[1]
    s = shots.get(sid) or {}
    path = os.path.join(mod_dir, "shots", s.get("dir") or sid, f"{sid}.rules")
    root = rules_root(path)
    if root is None:
        return [f"{sid}: arquivo do tiro ausente ou ilegivel"]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    for f in D.SPEC["conventions"]["forbidden_fields_0305"]:
        if f in text:
            errs.append(f"{sid}: campo 0.30.5 proibido {f}")
    rng = num_at(root, "Range")
    if not _eq(rng, w["range_m"]):
        errs.append(f"{sid}: Range {rng} != {w['range_m']}")
    tm = next((x for x in tmodes if x["index"] == m["index"]), m)
    hit = node_at(root, "Components/Hit")
    targ = node_at(root, "Components/Targetable")
    want_t = bool(s.get("targetable"))
    if want_t != (targ is not None):
        errs.append(f"{sid}: Targetable {'ausente' if want_t else 'presente'} (esperado {'sim' if want_t else 'nao'})")
    if want_t and targ is not None and not _eq(num_at(targ, "Health"), s.get("health")):
        errs.append(f"{sid}: Targetable Health {num_at(targ, 'Health')} != {s.get('health')}")
    kind = str(m.get("kind") or "")
    shield = m.get("shield_damage")
    if kind.startswith("contact"):
        fx = node_at(hit, "HitOperational/HitEffects")
        vals = [(node_at(c, "Type").value if node_at(c, "Type") else None, c) for c in (fx.children if fx else [])]
        dmg = next((num_at(c, "Damage") for t, c in vals if t == "Damage"), None)
        if not _eq(dmg, m["direct"]):
            errs.append(f"{sid}: dano direto {dmg} != {m['direct']}")
        # cargas esperadas, na ordem do build_explosive: explosao (com fogo) + explosao so estrutural
        want = [("explosao", m["explosive"], m["explosive_radius_m"], False)]
        if m.get("structural_explosive"):
            want.append(("explosao estrutural", m["structural_explosive"], m["structural_radius_m"], True))
        fire = re.search(r"StatusChancePerNDamage\s+(\d+(?:\.\d+)?)%", str(m.get("explosion_fire") or ""))
        errs += _check_blasts(f"{sid} (contato)", [c for t, c in vals if t == "ExplosiveDamage"], want,
                              float(fire.group(1)) if fire else None)
        if shield is not None and not _eq(num_at(hit, "HitShield/HitEffects/0/Damage"), shield):
            errs.append(f"{sid}: HitShield {num_at(hit, 'HitShield/HitEffects/0/Damage')} != {shield}")
        guided = isinstance(m.get("guided"), dict) and D.switch("boiuna.ac_guided")
        if guided != (node_at(root, "Components/Homing") is not None):
            errs.append(f"{sid}: Homing {'ausente' if guided else 'presente'}")
        od = node_at(root, "Components/Death/OnDeath")
        if od is None:
            errs.append(f"{sid}: sem detonacao no fim do alcance (Death/OnDeath)")
        else:
            # fim do alcance: as mesmas cargas do contato (sem o dano direto nem o impulso)
            ofx = node_at(od, "HitEffects")
            items = ofx.children if ofx is not None and ofx.kind == "list" else []
            if len(items) != len(want):
                errs.append(f"{sid}: Death/OnDeath com {len(items)} efeito(s), esperado {len(want)}")
            errs += _check_blasts(f"{sid} (fim do alcance)",
                                  [c for c in items if node_at(c, "Type") and node_at(c, "Type").value == "ExplosiveDamage"],
                                  want, float(fire.group(1)) if fire else None)
        return errs
    if not _eq(num_at(hit, "HitOperational/HitEffects/0/Damage"), m["direct"]):
        errs.append(f"{sid}: dano direto {num_at(hit, 'HitOperational/HitEffects/0/Damage')} != {m['direct']}")
    hs = node_at(hit, "HitShield")
    want_sh = shield if shield is not None else m["direct"]
    if hs is None:
        errs.append(f"{sid}: sem HitShield")
    elif hs.kind == "group":
        # bloco proprio (shield_damage != direto; ou o decorate do WP03, que expande &HitOperational com os mesmos
        # HitEffects e a midia de escudo)
        if not _eq(num_at(hs, "HitEffects/0/Damage"), want_sh):
            errs.append(f"{sid}: HitShield {num_at(hs, 'HitEffects/0/Damage')} != {want_sh}")
    elif shield is not None and shield != m["direct"]:
        errs.append(f"{sid}: HitShield sem bloco proprio (escudo {shield} != direto {m['direct']})")
    elif (hs.value or "") != "&HitOperational":
        errs.append(f"{sid}: HitShield deveria ser &HitOperational")
    if m["key"] == "plasma":
        return errs
    if not _eq(num_at(hit, "Penetration"), m["penetration"]):
        errs.append(f"{sid}: Penetration {num_at(hit, 'Penetration')} != {m['penetration']}")
    pd = tm.get("pen_damage_per_further_part")
    got = num_at(hit, "PenetratingOperational/HitEffects/0/Damage")
    if pd is not None and not _eq(got, pd):
        errs.append(f"{sid}: PenetratingOperational {got} != {pd}")
    if got is not None and m["direct"] and got >= m["direct"] and m["key"] in ("he", "ac", "ap", "sap"):
        errs.append(f"{sid}: PenetratingOperational {got} >= dano direto {m['direct']}")
    af = m.get("armor_factor")
    if af is not None and abs(af - 1) > 1e-9:
        if not _eq(num_at(hit, "PartCategoryPenetrationFactors/armor"), af * 100):
            errs.append(f"{sid}: armor {num_at(hit, 'PartCategoryPenetrationFactors/armor')} != {af * 100}%")
    if (m.get("explosive") or 0) > 0:
        fin = node_at(hit, "FinishedPenetratingOperational/HitEffects/0")
        if fin is None or not _eq(num_at(fin, "TotalDamage"), m["explosive"]) or not _eq(num_at(fin, "Radius"),
                                                                                       m["explosive_radius_m"]):
            errs.append(f"{sid}: carga no fim != {m['explosive']} r{m['explosive_radius_m']}")
    return errs
