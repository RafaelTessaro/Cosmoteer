"""Gerador das defesas (flak / CIWS de convés) do Bullet Strike.

Padrao vanilla: flak_cannon_large.rules — BeamEmitter instantaneo ate o ponto mirado
(ClipRangeToTarget) + ExplosiveDamage filtrado por categorias de projetil (acerta VARIOS projeteis
de uma vez, os mais proximos do centro primeiro). Overclock: cadencia maior (FireInterval BuffRemap) e,
quando o spec pede (Pororoca), um feixe proprio que deixa uma nuvem de estilhacos no ar.
"""

from rules_dsl import Q, VOID, Inh
from bsgen import common as C
from bsgen.guns import geometry, deck_graphics


def build_ciws(c, beam_path, beam_oc_path):
    """beam_oc_path = None com overclock: so a cadencia muda, com o mesmo feixe (CIWS "Barragem")."""
    w, h = c["size"]
    oc = c.get("oc")
    oc_beam = bool(oc and beam_oc_path)
    geo = geometry(c)
    center = [w / 2, h / 2]
    nb = len(geo["ys"]) if c.get("art3d") else c["barrels"]["count"]
    m = c["ammo"]

    top = {}
    if oc:
        top["OVERCLOCK"] = {"FIRE_INTERVAL_FACTOR": oc.get("fire_interval_factor", 1),
                            "HEAT_PER_SHOT": oc["heat_per_shot"], "HEAT_PER_SECOND": oc.get("heat_per_second", 0)}
        top["HEAT_TO_RESOURCE"] = C.HEAT_TO_RESOURCE
    top["FIRE_INTERVAL"] = c["fire_interval"]

    part = {
        "NameKey": Q(f"Parts/{c['key']}"),
        "IconNameKey": Q(f"Parts/{c['key']}Icon"),
        "DescriptionKey": Q(f"Parts/{c['key']}Desc"),
        "ID": C.pid(c["short"]),
        "EditorGroups": [Q(C.EDITOR_GROUP), Q("Defenses"), Q("WeaponsProjectile")],
        "Resources": [[r, q] for r, q in c["cost"]],
        "Size": [w, h],
        "SelectionPriority": 1,
        "MaxHealth": c["hp"],
        "TypeCategories": ["defense", "uses_ammo", "is_crewed"],
        "SignificanceToggle": "ScorchedToggle",
        "ReceivableBuffs : ^/0/ReceivableBuffs": [],
        "ProhibitedBy : ^/0/ProhibitedBy": ["tall"],
    }
    ring = C.tall_ring(w, h, c.get("ring", 1))
    if ring:
        part["ProhibitRects"] = ring
    part["AllowedDoorLocations"] = C.door_locations(w, h)
    part["EditorIcon"] = C.editor_icon(w, h, geo["overhang"])

    comp = {}
    comp.update(C.standard_toggles(bool(oc), c["cp"], defense=True, fire_pref_default=c.get("fire_pref_default", 1)))

    comp[C.comment("---- municao ----")] = None
    comp["MagStorage"] = {"Type": "ResourceStorage", "ResourceType": m["res"], "MaxResources": m["storage"],
                          "UITileRect": [f"0 + 7/64", f"{h - 1} + 7/64", "1 - 14/64", "1 - 14/64"],
                          "ReceiveResourceMediaEffects": "&/COMMON_EFFECTS/AmmoDeliver",
                          "DropResourcesWhenDestroyed": True}
    comp["Splitter"] = {"Type": "InlineResourceConverter", "ResourceType": m["res"], "FromStorage": "MagStorage",
                        "FromQuantity": 1, "ToQuantity": m["shots_per_unit"]}
    comp["MagConsumer"] = {"Type": "ResourceConsumer", "ResourceType": m["res"], "Storage": "MagStorage",
                           "DefaultPriority": "&/PRIORITIES/Weapon_Supply",
                           "OperationalToggle": "CommandConsumptionToggle",
                           "ConsumptionToggleButtonOffset": [0, -0.4]}
    comp["AmmoPrereq"] = {"Type": "MultiToggle", "Toggles": ["Splitter"], "Mode": "Any"}

    fi = "&~/FIRE_INTERVAL"
    fi_path = "&~/Part/Components/Turret/FireInterval"
    if oc and oc.get("fire_interval_factor", 1) != 1:
        fi = {"BaseValue": "&~/FIRE_INTERVAL",
              "Modifiers": [{"Type": "BuffRemap", "BuffType": "Overclock", "ModificationMode": "Multiply",
                             "RemapFrom": [0, 1], "RemapTo": [1, "(&~/OVERCLOCK/FIRE_INTERVAL_FACTOR)"]}]}
        fi_path += "/BaseValue"

    cats = C.ANTI_SHOT_CATEGORIES
    comp[C.comment("---- torre ----")] = None
    comp["Turret"] = {
        "Type": "TurretWeapon",
        "Location": geo["pivot"],
        "Rotation": "-90d",
        "OperationalToggle": "IsOperational",
        "AutoFireToggle": "AutoFireToggle",
        "FireInterval": fi,
        "FiringArc": f"{c['arc']}d",
        "RotateSpeed": f"{c['rotate']}d",
        "FireThresholdAngle": f"{c.get('threshold', 10)}d",
        "TargetSearchesPerSecond": c.get("searches", 8),
        "AIFirepowerRating": "&~/Part/StatsByCategory/0/Stats/DamagePerSecond",
        "Emitter": "BaseFlakEmitter",
        "IgnoreFriendlyShipLowLOSChecks": True,
        "AllowShipWideExplicitTargetsToggle": "FirePrefAttack",
        "EstimateFirepowerToggle": "AttackToggle",
        "AlwaysShowCoverage": True,
        "AllowDirectControlToggle": "FirePrefAttack",
        "FirePermissionToggle": "FireModeToggle",
        "AutoTargetCrewSafetyDist": 8,
        "AutoTargets": [
            {"TargetType": "Bullets", "BulletTargetCategories": cats, "Toggle": "DefendToggle"},
            {"TargetType": "ShipParts", "Toggle": "AttackToggle", "Overridable": True},
        ],
        "BlueprintArcSprite": {"Texture": "&/INDICATORS/WeaponArc", "Size": [0, 1.5], "Color": [255, 0, 255, 63]},
        "BlueprintArcRadius": 10,
        "BlueprintArcSpriteSegments": 64,
    }
    comp["TurretCollider"] = {"Type": "CircleCollider", "Location": "&../Turret/Location",
                              "Radius": geo["collider"], "IsHigh": True}
    comp["ReloadProgressBar"] = {"Type": "ProgressBar", "OperationalToggle": "IsOperational",
                                 "ShowProgressFor": "Turret"}

    # gatilhos alternados entre canos (flak_cannon_large.rules l.497-515)
    if nb > 1:
        comp["ShootCycle"] = {"Type": "ModeCycle", "ModeRange": [0, nb - 1], "IncrementTrigger": "Turret",
                              "StartingMode": nb - 1}
        triggers = []
        for i in range(nb):
            comp[f"ShootTrigger{i + 1}"] = {"Type": "ModeTrigger", "Mode": "ShootCycle", "TriggerInModes": [i]}
            triggers.append(f"ShootTrigger{i + 1}")
    else:
        triggers = ["Turret"]

    comp[C.comment("---- emissores (feixe + explosao em area) ----")] = None
    base = {
        "Type": "BeamEmitter",
        "ChainedTo": "Turret",
        "GetTargetFrom": "Turret",
        "ResourceStorage": "Splitter",
        "FireTrigger": VOID,
        "Location": [geo["muzzle"], 0],
        "OperationalToggle": "IsOperationalNonOverclocked" if oc_beam else "IsOperational",
        "ResourcesUsed": m.get("units_per_shot", 1),
        "Recoil": c.get("recoil", 4),
        "Burst": c.get("burst", 1),
    }
    if c.get("burst", 1) > 1:
        base["BurstDelay"] = c.get("burst_delay", 0.03)
        base["UseResourcePerShotInBurst"] = True
    comp[f"BaseFlakEmitter : <{beam_path}>"] = base
    emitters = []
    for i, y in enumerate(geo["ys"]):
        n = f"FlakEmitter{i + 1}"
        comp[f"{n} : BaseFlakEmitter"] = {"Location": [geo["muzzle"], y], "FireTrigger": triggers[i]}
        emitters.append(n)
    oc_emitters = []
    if oc_beam:
        comp[f"Overclock_BaseFlakEmitter : <{beam_oc_path}>/Beam, BaseFlakEmitter"] = {
            "OperationalToggle": "IsOperationalOverclocked"}
        for i, y in enumerate(geo["ys"]):
            n = f"Overclock_FlakEmitter{i + 1}"
            comp[f"{n} : Overclock_BaseFlakEmitter, FlakEmitter{i + 1}"] = {
                "Location": "&^/1/Location", "FireTrigger": "&^/1/FireTrigger",
                "ResourceStorage": "&^/1/ResourceStorage"}
            oc_emitters.append(n)
    for i in range(nb):
        trig = [emitters[i]] + ([oc_emitters[i]] if oc_beam else [])
        comp[f"Emitter{i + 1}Trigger"] = {"Type": "MultiTrigger", "Triggers": trig}

    fx = c["fx"]
    for i, y in enumerate(geo["ys"]):
        media = [f"&<{p}>" for p in fx["particles"]]
        snd = {"RandomSounds": [Q(s) for s in fx["sound"]], "Volume": fx.get("volume", 0.35),
               "SpeedVariation": 0.08, "MaxConcurrent": fx.get("max_concurrent", 30)}
        media.append(Inh("/BASE_SOUNDS/AudioExterior", snd))
        comp[f"FireEffect{i + 1}"] = {"Type": "TriggeredEffects", "ChainedTo": "Turret",
                                      "Trigger": f"Emitter{i + 1}Trigger",
                                      "Location": [geo["muzzle"] + fx.get("offset", 0), y], "MediaEffects": media}

    comp[C.comment("---- tripulacao ----")] = None
    comp.update(C.crew_block(c.get("crew_pos") or C.crew_positions(w, h, c["crew"], geo["pivot"]), "AmmoPrereq"))

    if oc:
        comp.update(C.overclock_machinery(center, w, h, [f"Emitter{i + 1}Trigger" for i in range(nb)],
                                          has_constant_heat=oc.get("heat_per_second", 0) > 0))
        # o MultiTrigger de calor so e ativo em overclock, entao contar os dois emissores e seguro
        comp["PeakHeatGenerationValue"] = {
            "Type": "StaticValue",
            "SHOT_HEAT_PER_SECOND": "(&~/OVERCLOCK/HEAT_PER_SHOT) * (&~/Part/SecondaryToolTip/StatsByCategory/0/Stats/ROF)",
            "Value": "(&~/OVERCLOCK/HEAT_PER_SECOND) + (&SHOT_HEAT_PER_SECOND)"}
        comp["HeatGenerationStatProvider"] = {"Type": "StatProvider", "Stat": "HeatGeneration",
                                              "OperationalToggle": "OverclockModeToggle",
                                              "ValueFrom": "PeakHeatGenerationValue"}

    comp[C.comment("---- graficos ----")] = None
    deck_graphics(comp, c, geo, [f"Emitter{i + 1}Trigger" for i in range(nb)], recoil_interval=0.03)

    comp.update(C.destroyed_effects(center, w, h))
    comp["Indicators"] = C.weapon_indicators(center, "AmmoPrereq", bool(oc), "&~/FIRE_INTERVAL")
    comp["Blueprints"] = C.blueprint(w, h)
    part["Components : ^/0/Components"] = comp

    part["Stats"] = {"CrewRequired": "&~/Part/Components/PartCrew/Crew",
                     "AmmoCapacity": "&~/Part/Components/MagStorage/MaxResources",
                     "BSShotsPerMag": "&~/Part/Components/Splitter/ToQuantity"}
    burst = c.get("burst", 1)
    em = "&~/Part/Components/BaseFlakEmitter"
    part["StatsByCategory"] = [{
        "NameKey": Q("StatCategories/BSFlak"),
        "Stats": {
            "DamagePerShotVsShots": f"{em}/STAT_DAMAGE",
            "DamagePerShot": f"{em}/STAT_SHIP_DAMAGE",
            "ROF": f"{burst} / ({fi_path})",
            "DamagePerSecond": "(&DamagePerShot) * (&ROF)",
            "DamagePerSecondVsShots": "(&DamagePerShotVsShots) * (&ROF)",
            "MaxDamage": ["&../DamagePerShot", "&../DamagePerSecond"],
            "ShotDamage": ["&../DamagePerShotVsShots", "&../DamagePerSecondVsShots"],
            "DamageArea": f"{em}/STAT_RADIUS",
            "Range": f"{em}/Range",
            "Arc": "deg(&~/Part/Components/Turret/FiringArc)",
            "TurretSpeed": "deg(&~/Part/Components/Turret/RotateSpeed)",
            "ShotSpeed": "Infinity",
            "AmmoPerShot": f"({em}/ResourcesUsed) / (&~/Part/Components/Splitter/ToQuantity)",
            "AmmoPerSecond": "(&AmmoPerShot) * (&ROF)",
            "ShotAmmoUsage": ["&../AmmoPerShot", "&../AmmoPerSecond"],
        }}]
    if oc:
        oc_stats = {"ROF": f"{burst} / (({fi_path}) * (&~/OVERCLOCK/FIRE_INTERVAL_FACTOR))"}
        if oc_beam:
            oem = "&~/Part/Components/Overclock_BaseFlakEmitter"
            oc_stats.update({"ShrapnelFieldRadius": f"{oem}/STAT_CLOUD_RADIUS",
                             "ShrapnelFieldDamagePool": f"{oem}/STAT_CLOUD_POOL",
                             "ShrapnelFieldLifetime": f"{oem}/STAT_CLOUD_LIFETIME"})
        oc_stats.update({"HeatPerShot": "(&~/OVERCLOCK/HEAT_PER_SHOT)",
                         "HeatGeneration": "(&~/OVERCLOCK/HEAT_PER_SECOND)"})
        part["SecondaryToolTip"] = {
            "TitleKey": Q("StatCategories/Overclocked"),
            "DescriptionKey": Q(f"Parts/{c['key']}OverclockDesc"),
            "StatsByCategory": [{"NameKey": Q("StatCategories/BSFlak"), "Stats": oc_stats}]}
    top["Part : " + C.base_part_path(w, h, bool(oc))] = part
    return top, {"geo": geo, "center": center}
