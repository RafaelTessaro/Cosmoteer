"""Gerador das armas de convés (ataque) do Bullet Strike.

Arquitetura (so padroes ja usados pelo jogo base 0.30.x):
  * Torre unica (TurretWeapon) com FireInterval modificavel:
      - divide pelo buff RateOfFire (spin-up da minigun, igual ao chaingun.rules l.765-790)
      - multiplica pelo fator de overclock (BuffRemap Overclock Multiply, idem)
  * Municao: para cada tipo de municao k ha um ResourceStorage (carregadores) + um
    InlineResourceConverter "Splitter_k" que abre 1 carregador em N tiros (chaingun.rules l.353-374).
    O consumidor (pedido de entrega para a tripulacao) so fica ativo para o tipo selecionado.
  * Seletor de municao: UIToggle "bs_ammo_type" + ModeToggle (missile_launcher.rules l.125-146).
  * Emissores: blocos ToggledComponents mutuamente exclusivos (tipo x overclock) que definem
    componentes com os MESMOS nomes (TargetEmitter, Emitter1..n); a torre e os efeitos usam
    EmitterProxy (cannon_deck.rules l.827-928).
  * Convés: anel 'tall', TurretCollider IsHigh, IgnoreFriendlyShipLowLOSChecks,
    AntiPhasingRaycastIgnoreLowCollisions e sprites em "roof_turrets" (cannon_deck).
"""

from rules_dsl import Q, VOID, comment
from bsgen import common as C


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
    """Calcula geometria (pivo, torre, canos, cano) a partir do tamanho; o gerador de sprites usa a mesma."""
    w, h = g["size"]
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


def build_gun(g, shot_paths):
    """Retorna (texto_rules, info) de uma arma de convés.

    shot_paths: dict (k, oc_state) -> caminho relativo do arquivo do tiro a partir da pasta da peca.
    """
    w, h = g["size"]
    oc = g.get("oc")
    spin = g.get("spin")
    sel = g.get("selector") and len(_modes(g)) > 1
    g["selector"] = bool(sel)
    geo = geometry(g)
    center = [w / 2, h / 2]
    modes = _modes(g)
    nb = g["barrels"]["count"]
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
        if g.get("stun"):
            o["CREW_STUN_DURATION"] = g["stun"].get("oc_duration", g["stun"]["duration"])
            o["CREW_STUN_RADIUS"] = g["stun"].get("oc_radius", g["stun"]["radius"])
        top["OVERCLOCK"] = o
        top["HEAT_TO_RESOURCE"] = C.HEAT_TO_RESOURCE
    top["FIRE_INTERVAL"] = g["fire_interval"]
    if spin:
        top["SPIN"] = {"MAX": spin["max"], "UP_TIME": spin["up"], "DOWN_TIME": spin["down"]}

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
    part["TypeCategories"] = ["weapon", "uses_ammo", "is_crewed"] + list(g.get("extra_categories", []))
    part["SignificanceToggle"] = "ScorchedToggle"
    if spin:
        part["ReceivableBuffs : ^/0/ReceivableBuffs"] = ["RateOfFire"]
    else:
        part["ReceivableBuffs : ^/0/ReceivableBuffs"] = []
    part["ProhibitedBy : ^/0/ProhibitedBy"] = ["tall"]
    ring = C.tall_ring(w, h, g.get("ring", 1))
    if ring:
        part["ProhibitRects"] = ring
    part["AllowedDoorLocations"] = C.door_locations(w, h)
    part["EditorIcon"] = C.editor_icon(w, h, geo["overhang"])

    comp = {}
    hybrid = bool(g.get("hybrid"))
    comp.update(C.standard_toggles(bool(oc), g["cp"], defense=hybrid, fire_pref_default=2))

    # ------------------------------------------------------------------ municao
    comp[C.comment("---- municao (carregadores abertos em N tiros) ----")] = None
    if sel:
        comp["AmmoTypeToggle"] = {"Type": "UIToggle", "ToggleID": Q("bs_ammo_type"), "Default": modes[0]["mode"],
                                  "AlwaysAllowInBuildMode": True}
    for i, m in enumerate(modes):
        k = m["mode"]
        if sel:
            comp[f"ModeToggle_{k}"] = {"Type": "ModeToggle", "Mode": "AmmoTypeToggle", "OnMode": k}
            comp[f"ConsumeToggle_{k}"] = {"Type": "MultiToggle", "Toggles": ["CommandConsumptionToggle", f"ModeToggle_{k}"],
                                          "Mode": "All"}
        tile_x = (i % w) + 7 / 64
        tile_y = (h - 1) + 7 / 64
        comp[f"MagStorage_{k}"] = {
            "Type": "ResourceStorage",
            "ResourceType": m["res"],
            "MaxResources": m["storage"],
            "UITileRect": [f"{i % w} + 7/64", f"{max(0, h - 1 - i // w)} + 7/64", "1 - 14/64", "1 - 14/64"],
            "ReceiveResourceMediaEffects": "&/COMMON_EFFECTS/AmmoDeliver",
            "DropResourcesWhenDestroyed": True,
        }
        comp[f"Splitter_{k}"] = {"Type": "InlineResourceConverter", "ResourceType": m["res"],
                                 "FromStorage": f"MagStorage_{k}", "FromQuantity": 1,
                                 "ToQuantity": m["shots_per_unit"]}
        comp[f"MagConsumer_{k}"] = {
            "Type": "ResourceConsumer",
            "ResourceType": m["res"],
            "Storage": f"MagStorage_{k}",
            "DefaultPriority": "&/PRIORITIES/Weapon_Supply",
            "OperationalToggle": f"ConsumeToggle_{k}" if sel else "CommandConsumptionToggle",
            "ConsumptionToggleButtonOffset": [0, -0.4 + 0.25 * i] if sel else [0, -0.4],
        }
        if sel:
            comp[f"HasAmmo_{k}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{k}", f"Splitter_{k}"], "Mode": "All"}
    if sel:
        comp["AmmoPrereq"] = {"Type": "MultiToggle", "Toggles": [f"HasAmmo_{m['mode']}" for m in modes], "Mode": "Any"}
    else:
        comp["AmmoPrereq"] = {"Type": "MultiToggle", "Toggles": [f"Splitter_{modes[0]['mode']}"], "Mode": "Any"}
    if sel and oc:
        for m in modes:
            k = m["mode"]
            comp[f"FireToggle_{k}_N"] = {"Type": "MultiToggle",
                                         "Toggles": [f"ModeToggle_{k}", "{ Toggle=IsOverclocked; Invert=true }"],
                                         "Mode": "All"}
            comp[f"FireToggle_{k}_OC"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{k}", "IsOverclocked"],
                                          "Mode": "All"}

    # ------------------------------------------------------------------ spin-up
    if spin:
        comp[C.comment("---- spin-up (chaingun.rules l.191-287) ----")] = None
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
        acc["DissipationRate"] = "((&~/SPIN/MAX) - 1) / (&~/SPIN/DOWN_TIME)"
        comp["SpinUp"] = acc
        comp["RateOfFireBuff"] = {"Type": "SelfBuffProvider", "BuffType": "RateOfFire", "BuffAmount": 1,
                                  "BuffMultiplier": "SpinUp"}

    # ------------------------------------------------------------------ torre
    comp[C.comment("---- torre ----")] = None
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
        "IgnoreFriendlyShipLowLOSChecks": True,
        "AutoTargets": [{"TargetType": "ShipParts", "Toggle": "AutoTargetToggle"}],
        "BlueprintArcSprite": {"Texture": "&/INDICATORS/WeaponArc", "Size": [0, 1.5], "Color": [255, 0, 0, 63]},
        "BlueprintArcRadius": 10,
        "BlueprintArcSpriteSegments": 64,
    }
    if g.get("searches"):
        turret["TargetSearchesPerSecond"] = g["searches"]
    if hybrid:
        # Atacar / Defender / Ambos, como a Flak vanilla (flak_cannon_large.rules l.444-477)
        turret["TargetSearchesPerSecond"] = g.get("searches", 6)
        turret["AllowShipWideExplicitTargetsToggle"] = "FirePrefAttack"
        turret["EstimateFirepowerToggle"] = "AttackToggle"
        turret["AllowDirectControlToggle"] = "FirePrefAttack"
        turret["AutoTargets"] = [
            {"TargetType": "Bullets", "BulletTargetCategories": C.ANTI_SHOT_CATEGORIES, "Toggle": "DefendToggle"},
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
    else:
        triggers = ["Turret"] * nb

    # ------------------------------------------------------------------ emissores (blocos por tipo x overclock)
    comp[C.comment("---- emissores: um bloco por tipo de municao (e por estado de overclock) ----")] = None
    oc_states = [False, True] if oc else [False]
    spread = g["spread"]
    for m in modes:
        k = m["mode"]
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
                "ResourceStorage": f"Splitter_{k}",
                "ResourcesUsed": m.get("units_per_shot", 1),
                "Recoil": g["recoil"] if not s else f"{g['recoil']} * (&~/OVERCLOCK/RECOIL_FACTOR)",
                "AntiPhasingRaycastDistance": 2,
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
    def fire_media(sound, shake):
        media = [f"&<{p}>" for p in fx["particles"]]
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
                                      "MediaEffects": fire_media(fx["sound"], fx.get("shake", 0))}
    for i, p in enumerate(proxies_oc):
        comp[f"Overclock_FireEffect{i + 1}"] = {"Type": "TriggeredEffects", "ChainedTo": p, "Trigger": p,
                                                "Location": [fx.get("offset", 0), 0],
                                                "MediaEffects": fire_media(fx.get("sound_oc", fx["sound"]),
                                                                           fx.get("shake_oc", fx.get("shake", 0)))}

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
    comp[C.comment("---- tripulacao ----")] = None
    comp.update(C.crew_block(g.get("crew_pos") or C.crew_positions(w, h, g["crew"], geo["pivot"]), "AmmoPrereq"))

    # ------------------------------------------------------------------ overclock
    if oc:
        comp[C.comment("---- overclock (base_part_overclock.rules + cannon_deck.rules l.323-413) ----")] = None
        comp.update(C.overclock_machinery(center, w, h, proxies_all, has_constant_heat=oc.get("heat_per_second", 0) > 0))
        comp["PeakHeatGenerationValue"] = {
            "Type": "StaticValue",
            "SHOT_HEAT_PER_SECOND": "(&~/OVERCLOCK/HEAT_PER_SHOT) * (&~/Part/SecondaryToolTip/StatsByCategory/0/Stats/ShotsPerSecond)",
            "Value": "(&~/OVERCLOCK/HEAT_PER_SECOND) + (&SHOT_HEAT_PER_SECOND)",
        }
        comp["HeatGenerationStatProvider"] = {"Type": "StatProvider", "Stat": "HeatGeneration",
                                              "OperationalToggle": "OverclockModeToggle",
                                              "ValueFrom": "PeakHeatGenerationValue"}

    # ------------------------------------------------------------------ graficos
    comp[C.comment("---- graficos ----")] = None
    comp["Graphics"] = {
        "Type": "Graphics", "Location": center, "OperationalToggle": "IsOperational",
        "Floor": {"Layer": Q("floors"), "DamageLevels": [{"File": Q("floor.png"), "Size": [w, h]}]},
        "Walls": {"Layer": Q("walls"), "DamageLevels": [{"File": Q("walls.png"), "Size": [w, h]}]},
        "Roof": {"Layer": Q("roofs"), "DamageLevels": [{"File": Q("roof.png"), "NormalsFile": Q("roof_normals.png"),
                                                          "Size": [w, h]}]},
    }
    ts = geo["turret_size"]
    comp["TurretGraphics"] = {
        "Type": "Graphics", "ChainedTo": "Turret", "Location": [0, 0], "Rotation": "90d",
        "OperationalToggle": "IsOperational",
        "Floor": {"Layer": Q("doodads_high"), "DamageLevels": [{"File": Q("turret_shadow.png"), "Size": [ts, ts]}]},
        "OperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [
            {"File": Q("turret.png"), "NormalsFile": Q("turret_normals.png"), "Size": [ts, ts]}]},
        "NonOperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [
            {"File": Q("turret_off.png"), "NormalsFile": Q("turret_normals.png"), "Size": [ts, ts]}]},
    }
    bl, bw = geo["barrel_len"], geo["barrel_sprite_w"] if "barrel_sprite_w" in geo else max(0.5, round(geo["barrel_w"] * 2, 3))
    geo["barrel_sprite_w"] = bw
    if spin:
        frames = ["barrel_spin1.png", "barrel_spin2.png", "barrel_spin3.png", "barrel1.png"]
        nframes = ["barrel_normals1.png"] * 4
        anim_interval = 0.05
    else:
        frames = ["barrel2.png", "barrel3.png", "barrel4.png", "barrel5.png", "barrel1.png"]
        nframes = ["barrel_normals1.png"] * 5
        anim_interval = g["barrels"].get("recoil_frame", 0.06)
    for i, y in enumerate(geo["ys"]):
        comp[f"Barrel{i + 1}Graphics"] = {
            "Type": "Graphics", "ChainedTo": "Turret", "Location": [geo["barrel_center"], y], "Rotation": "90d",
            "OperationalToggle": "IsOperational",
            "ResetAnimationTrigger": proxies_all[i],
            "OperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [{
                "AnimationFiles": [Q(f) for f in frames],
                "NormalsAnimationFiles": [Q(f) for f in nframes],
                "Size": [bw, bl], "AnimationInterval": anim_interval,
                "AnimationStartTime": "MinValue", "ClampAnimation": True}]},
            "NonOperationalDoodad": {"Layer": Q("roof_turrets"), "DamageLevels": [{
                "File": Q("barrel1.png"), "NormalsFile": Q("barrel_normals1.png"), "Size": [bw, bl]}]},
        }

    # ------------------------------------------------------------------ efeitos / UI
    comp.update(C.destroyed_effects(center, w, h))
    comp["Indicators"] = C.weapon_indicators(center, "AmmoPrereq", bool(oc), "&~/FIRE_INTERVAL")
    comp["Blueprints"] = C.blueprint(w, h)

    part["Components : ^/0/Components"] = comp

    # ------------------------------------------------------------------ stats
    m0 = modes[0]
    part["Stats"] = {
        "CrewRequired": "&~/Part/Components/PartCrew/Crew",
        "AmmoCapacity": f"&~/Part/Components/MagStorage_{m0['mode']}/MaxResources",
        "BSShotsPerMag": f"&~/Part/Components/Splitter_{m0['mode']}/ToQuantity",
    }
    if g.get("stun"):
        part["Stats"]["CrewStunDuration"] = [0, "&~/Part/Components/StunEffect/HitEffects/0/Duration/BaseValue"]
        part["Stats"]["CrewStunRadius"] = "&~/Part/Components/StunEffect/HitEffects/0/Radius/BaseValue"

    shots_per_trigger = (nb if pattern != "alternate" or nb == 1 else 1) * (burst["count"] if burst else 1)
    spin_max = spin["max"] if spin else 1
    cats = []
    def em_path(k, s):
        if _fire_block_toggle(g, k, s)[0] is None:
            return "&~/Part/Components/TargetEmitter"
        return f"&~/Part/Components/Fire_{k}_{'OC' if s else 'N'}/Components/TargetEmitter"

    for m in modes:
        k = m["mode"]
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
            "Range": f"{em}/Bullet/Range",
            "Arc": "deg(&~/Part/Components/Turret/FiringArc)",
            "Spread": f"deg({em}/Spread/1)",
            "TurretSpeed": "deg(&~/Part/Components/Turret/RotateSpeed)",
            "ShotSpeed": f"{em}/Bullet/Speed",
            "ShotHP": f"{em}/Bullet/Components/Targetable/Health",
            "AmmoPerShot": f"({em}/ResourcesUsed) / (&~/Part/Components/Splitter_{k}/ToQuantity)",
            "AmmoPerSecond": "(&AmmoPerShot) * (&ShotsPerSecond)",
            "ShotAmmoUsage": ["&../AmmoPerShot", "&../AmmoPerSecond"],
        })
        if burst:
            st["Burst"] = burst["count"]
        cats.append({"NameKey": Q(f"StatCategories/BSAmmo_{m['ammo']}"), "Stats": st})
    part["StatsByCategory"] = cats

    if oc:
        k = m0["mode"]
        em = em_path(k, True)
        oc_burst = oc.get("burst") or burst
        spt = (nb if pattern != "alternate" or nb == 1 else 1) * (oc_burst["count"] if oc_burst else 1)
        oc_spin = oc.get("max_spin", spin_max) if spin else 1
        oc_stats = {
            "DamagePerShot": f"{em}/Bullet/STAT_DAMAGE",
            "ShotsPerSecond": f"{spt} * {oc_spin} / (({fi_path}) * (&~/OVERCLOCK/FIRE_INTERVAL_FACTOR))",
            "DamagePerSecond": "(&DamagePerShot) * (&ShotsPerSecond)",
            "Damage": ["&../DamagePerShot", "&../DamagePerSecond"],
            "ROF": "&ShotsPerSecond",
            "Range": f"{em}/Bullet/Range",
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
