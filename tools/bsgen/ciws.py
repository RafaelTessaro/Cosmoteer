"""Gerador das defesas (flak / CIWS de conves) do Bullet Strike.

Padrao vanilla: flak_cannon_large.rules — BeamEmitter instantaneo ate o ponto mirado
(ClipRangeToTarget) + ExplosiveDamage filtrado por categorias de projetil (acerta VARIOS projeteis
de uma vez, os mais proximos do centro primeiro). Overclock: cadencia maior (FireInterval BuffRemap) e,
quando o spec pede (Pororoca), um feixe proprio que deixa uma nuvem de estilhacos no ar.

So defesa (sem modo Atacar): torre no molde do point_defense (fire_mode sem alvo explicito, sem fire_pref,
sem busca de pecas de nave, sem controle direto) e explosao so contra projeteis. O feixe passa por cima do
nosso casco e das nossas torres (FriendlyShipLow/HighCollisions = false) e a torre ignora as nossas pecas na
linha de tiro (IgnoreFriendlyShipLow/HighLOSChecks), como o manipulator_beam_emitter.

Contra os raios do SW:ACD (defense_design C4): tolerancia de mira de 3-4 graus, a torre nao volta ao centro entre
alvos, testa varios candidatos por busca, misseis/minas tem prioridade sobre granadas/laser/ion e o feixe leva uma
2a carga mais forte so contra laser/ion_shot (linha "Dano x lasers" no tooltip).
"""

import os

from rules_dsl import Q, VOID, Inh
from bsgen import common as C
from bsgen.guns import geometry, deck_graphics

# valores de ToggleOnMode aceitos no build de diagnostico (enum visto na 0.30.3: manipulator_beam_emitter l.451,
# chaingun l.833); qualquer outro valor para o build aqui, antes de virar arquivo que o jogo rejeita
_PD_DEBUG_MODES = {"1": "HasTarget", "HasTarget": "HasTarget", "WantsToFire": "WantsToFire"}


def _pd_debug_mode():
    """BS_PD_DEBUG=1 (ou HasTarget / WantsToFire): build de diagnostico das defesas (defense_design C9). Vazio ou
    0 = build normal, sem nada a mais. Nunca vai no mod publicado."""
    v = os.environ.get("BS_PD_DEBUG", "").strip()
    if v in ("", "0"):
        return None
    if v not in _PD_DEBUG_MODES:
        raise ValueError(f"BS_PD_DEBUG={v!r}: use 1 (HasTarget) ou WantsToFire")
    return _PD_DEBUG_MODES[v]


def _whole(v, name):
    """Campos int do TurretWeapon (TargetChecksPerSearch, InstantSearchesAfterTargetLost): um valor fracionario
    derruba o carregamento na 0.30.4c, entao o build para aqui."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != int(v) or v < 1:
        raise ValueError(f"{name} = {v!r}: tem que ser um inteiro >= 1")
    return int(v)


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
    comp.update(C.standard_toggles(bool(oc), c["cp"], defend_only=True))

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
        # tolerancia de mira do spec (bs_data._defense, 4/4/3 graus) para acompanhar os raios rapidos do SW:ACD;
        # flak_cannon_large.rules l.454 e a flak do SW:ACD (turbolaser_flak_cannon01.rules l.358) usam 30d
        "FireThresholdAngle": f"{c['threshold']}d",
        "TargetSearchesPerSecond": c.get("searches", 8),
        # aquisicao de alvo (defense_design C4). Todos os campos existem na 0.30.3 (ae16922) e no SW:ACD:
        # candidatos validados por busca (padrao do jogo = 1): manipulator_beam_emitter.rules 0.30.3 l.448 (10),
        # SW resource_collector_tiny.rules l.358 (10)
        "TargetChecksPerSearch": _whole(c.get("checks_per_search", 4), "checks_per_search"),
        # buscas imediatas quando o alvo some (padrao 1): chaingun.rules 0.30.3 l.742 (5)
        "InstantSearchesAfterTargetLost": _whole(c.get("instant_searches", 3), "instant_searches"),
        # segura o alvo depois de cancelar: point_defense.rules 0.30.3 l.372 (.5),
        # tractor_beam_emitter.rules 0.30.3 l.576 (0.5)
        "HoldTargetAfterCancel": c.get("hold_after_cancel", 0.5),
        # fica virada para o fluxo de disparos entre um alvo e outro (padrao true = volta ao centro):
        # manipulator_beam_emitter.rules 0.30.3 l.450, SW resource_collector_tiny.rules l.360
        "ReturnToCenter": False,
        # so defende: nunca mira pecas de nave nem aceita alvo do jogador (point_defense.rules l.383/390,
        # tractor_beam_emitter.rules l.574/577, manipulator_beam_emitter.rules l.441-445); a unica busca automatica
        # e a de projeteis (sem a de ShipParts que o point_defense vanilla ainda tem)
        "AIFirepowerRating": 0,
        "IncludeInFirepowerEstimation": False,
        "CanBeGivenExplicitTarget": False,
        "AllowShipWideExplicitTargets": False,
        "AllowDirectControl": False,
        "Emitter": "BaseFlakEmitter",
        # passa por cima das nossas torres (IsHigh): manipulator_beam_emitter.rules l.447-448
        "IgnoreFriendlyShipLowLOSChecks": True,
        "IgnoreFriendlyShipHighLOSChecks": True,
        # destrocos nao bloqueiam a mira: manipulator_beam_emitter.rules 0.30.3 l.446,
        # mining_laser_small.rules 0.30.3 l.331
        "IgnoreJunkLOSChecks": True,
        # dispara mesmo com a linha de visada bloqueada (a explosao so pega projeteis, nunca casco): flak do SW:ACD
        # (turbolaser_flak_cannon01.rules l.361) e lancadores vanilla (missile_launcher_he.rules 0.30.3 l.401)
        "AllowFireWithBlockedLOS": True,
        "AlwaysShowCoverage": True,
        "FirePermissionToggle": "FireModeToggle",
        "AutoTargetCrewSafetyDist": 8,
        # duas listas: misseis/minas primeiro; granadas/laser/ion numa lista Overridable (um missil novo toma o
        # lugar do raio seguido). Overridable = true na 2a lista: point_defense.rules 0.30.3 l.390,
        # flak_cannon_large.rules 0.30.3 l.475, SW turbolaser_flak_cannon01.rules l.376
        "AutoTargets": [
            {"TargetType": "Bullets", "BulletTargetCategories": list(C.PD_PRIORITY_TARGETS),
             "Toggle": "AutoTargetToggle"},
            {"TargetType": "Bullets", "BulletTargetCategories": list(C.PD_SECONDARY_TARGETS),
             "Toggle": "AutoTargetToggle", "Overridable": True},
        ],
        "BlueprintArcSprite": {"Texture": "&/INDICATORS/WeaponArc", "Size": [0, 1.5], "Color": [255, 0, 255, 63]},
        "BlueprintArcRadius": 10,
        "BlueprintArcSpriteSegments": 64,
        # setor de alcance na 0.30.4 (bsgen/common.py COVERAGE_SECTOR_ARC; a 0.30.5 ignora)
        "CoverageSectorArc": dict(C.COVERAGE_SECTOR_ARC),
    }
    dbg = _pd_debug_mode()
    if dbg:
        # SO no build de diagnostico (BS_PD_DEBUG): a torre vira "ligada" quando tem alvo (HasTarget) ou quando
        # quer atirar (WantsToFire) e acende a luz do teto (DebugTargetLight, abaixo). ToggleOnMode so muda como a
        # arma e lida como toggle: manipulator_beam_emitter.rules 0.30.3 l.451 (HasTarget, TurretWeapon),
        # SW resource_collector_tiny.rules l.361 (HasTarget), chaingun.rules 0.30.3 l.833 (WantsToFire, num
        # FixedWeapon: o campo e da classe base Weapon)
        comp["Turret"]["ToggleOnMode"] = dbg
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
    # clarao de boca proprio do overclock (fx["particles_oc"], preenchido pelo pacote de calibre). So em peca com
    # overclock: o gatilho de cada cano passa por um par de TriggerProxy com ProxyToggle = IsOverclocked (normal /
    # invertido), o padrao vanilla para separar efeito normal e de overclock (disruptor.rules 0.30.3 l.424-433;
    # cannon_deck.rules 0.30.3 l.912-934 com EmitterProxy; guns.py faz o mesmo). IsOverclocked vem da base vanilla
    # <ships/base_part_overclock.rules> (l.150), que so as pecas *_overclock herdam, e le o OverclockStateValue de
    # common.overclock_machinery. OperationalToggle num TriggeredEffects nao aparece no vanilla nem no SW:ACD, por
    # isso nao e usado. Sem particles_oc (ou sem overclock) o arquivo sai igual ao de antes.
    oc_fx = bool(oc) and bool(fx.get("particles_oc"))

    def _fire_media(particles, sounds):
        media = [f"&<{p}>" for p in particles]
        snd = {"RandomSounds": [Q(s) for s in sounds], "Volume": fx.get("volume", 0.35),
               "SpeedVariation": 0.08, "MaxConcurrent": fx.get("max_concurrent", 30)}
        media.append(Inh("/BASE_SOUNDS/AudioExterior", snd))
        return media

    def _fire_effect(y, trigger, particles, sounds):
        return {"Type": "TriggeredEffects", "ChainedTo": "Turret", "Trigger": trigger,
                "Location": [geo["muzzle"] + fx.get("offset", 0), y], "MediaEffects": _fire_media(particles, sounds)}

    for i, y in enumerate(geo["ys"]):
        trig = f"Emitter{i + 1}Trigger"
        if not oc_fx:
            comp[f"FireEffect{i + 1}"] = _fire_effect(y, trig, fx["particles"], fx["sound"])
            continue
        p_oc, p_n = f"FireTrigger{i + 1}_Overclocked", f"FireTrigger{i + 1}_NonOverclocked"
        comp[p_oc] = {"Type": "TriggerProxy", "ComponentID": trig, "ProxyToggle": "IsOverclocked"}
        comp[f"{p_n} : {p_oc}"] = {"InvertProxyToggle": True}
        comp[f"FireEffect{i + 1}"] = _fire_effect(y, p_n, fx["particles"], fx["sound"])
        # mesmo cano, posicao e som (gancho de som proprio depois: fx["sound_oc"]); so as particulas mudam
        comp[f"Overclock_FireEffect{i + 1}"] = _fire_effect(y, p_oc, fx["particles_oc"],
                                                            fx.get("sound_oc") or fx["sound"])

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
    if dbg:
        # build de diagnostico: luz extra do teto (lights.png, a mesma da peca) ligada pela propria torre. A arma
        # entra como toggle so dentro de um MultiToggle (Toggles = [Turret], Mode = Any), como no jogo base:
        # chaingun.rules 0.30.3 l.470-474 (EitherWeaponIsTargeting), manipulator_beam_emitter.rules 0.30.3 l.175.
        # Arma direto em OperationalToggle nao tem precedente no 0.30.3 nem no SW:ACD (0.30.4): nao usar.
        comp["DebugTargetToggle"] = {"Type": "MultiToggle", "Toggles": ["Turret"], "Mode": "Any"}
        comp["DebugTargetLight"] = {
            "Type": "Graphics", "Location": center, "OperationalToggle": "DebugTargetToggle",
            "OperationalLighting": {"Layer": Q("lights_add"),
                                    "DamageLevels": [{"File": Q("lights.png"), "Size": [w, h]}]}}

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
            "ROF": f"{burst} / ({fi_path})",
            "DamagePerSecondVsShots": "(&DamagePerShotVsShots) * (&ROF)",
            "ShotDamage": ["&../DamagePerShotVsShots", "&../DamagePerSecondVsShots"],
            # 2a carga, so contra laser/ion_shot (STAT_LASER_DAMAGE na raiz do feixe, shots.build_flak_beam); linha
            # propria BSShotDamageVsLasers (infra.part_stats + Stats/BSShotDamageVsLasersFmt), no formato de
            # ShotDamage: [por disparo, por segundo]
            "DamagePerShotVsLasers": f"{em}/STAT_LASER_DAMAGE",
            "DamagePerSecondVsLasers": "(&DamagePerShotVsLasers) * (&ROF)",
            "BSShotDamageVsLasers": ["&../DamagePerShotVsLasers", "&../DamagePerSecondVsLasers"],
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
