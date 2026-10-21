"""Gerador das defesas (flak / CIWS de conves) do Bullet Strike 2.0 (dono: WP02; modulo de CONTEUDO, API 2).

Padrao vanilla: flak_cannon_large.rules — BeamEmitter instantaneo ate o ponto mirado (ClipRangeToTarget) +
ExplosiveDamage filtrado por categorias de projetil (acerta VARIOS projeteis de uma vez). Overclock: cadencia maior
(FireInterval BuffRemap) e, quando o spec pede (Pororoca), um feixe proprio por modo que deixa uma nuvem de
estilhacos no ar (o Tamandua so muda a cadencia, com os mesmos feixes).

2.0 (plano WP02): dois modos no seletor bs_ammo_type (AvailableChoices [0, 4]): HE "AE-PF (espoleta de proximidade)"
e FRAG "Nuvem de Fragmentos" (explosao central menor + SpawnBullets do cone de fragmentos no HitNothing do feixe). Por
modo i: MagStorage_i (MaxResources = SPEC.defenses[].internal_stock: Tatu 17, Tamandua 38, Pororoca 45),
Splitter_i (8 / 6 / 3 rajadas por carregador), ModeToggle_i, MagConsumer_i (floor(Max/2), reserva da tripulacao) e
o cook-off do modo; emissores num bloco ToggledComponents por modo (e por estado de overclock quando ha feixe OC),
com BeamEmitterProxy para a torre e os efeitos (tractor_beam_emitter.rules l.656-700, chaingun.rules l.967-981).
Logistica pelo seam do intake (como os canhoes). Contra laser/ion: a carga da Fase B (guns.defesa_antilaser).

So defesa (sem modo Atacar): torre no molde do point_defense (fire_mode sem alvo explicito, sem fire_pref, sem
busca de pecas de nave, sem controle direto) e explosao so contra projeteis. O feixe passa por cima do nosso casco e
das nossas torres (FriendlyShipLow/HighCollisions = false) e a torre ignora as nossas pecas na linha de tiro
(IgnoreFriendlyShipLow/HighLOSChecks), como o manipulator_beam_emitter.

Contra os raios do SW:ACD (defense_design C4, Fase B): tolerancia de mira de 3-4 graus, a torre nao volta ao centro
entre alvos, testa varios candidatos por busca e misseis/minas tem prioridade sobre granadas/laser/ion.

O fragmento da FRAG (kind 'frag_fragment', um por defesa) e escrito aqui pelo build_shot (SHOT_KINDS), em
shots/<defesa>/<arquivo>.rules ao lado do feixe que o referencia; o construtor e o shots.build_frag_fragment.
"""

import os

from rules_dsl import Q, VOID, Inh, comment, render
from bsgen import common as C
from bsgen.guns import (geometry, deck_graphics, crew_positions_for, ammo_selector, mag_storage, mag_consumers,
                        intake_fields, intake_components, cookoff_effects, skip_down_for, write_art, rules_root,
                        node_at, num_at, list_at, _eq, _k, _ctx)

API = 2
SHOT_KINDS = ("frag_fragment",)

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


def build_ciws(c, beam_paths, beam_oc_paths=None, ctx=None):
    """Retorna (top, info) de uma defesa. beam_paths: indice do modo -> caminho relativo do feixe; beam_oc_paths:
    indice -> feixe de overclock (so a Pororoca; None/vazio com overclock = so a cadencia muda, como a 'Barragem' do
    Tamandua). Compatibilidade 1.x: beam_paths como texto = um feixe so para todos os modos."""
    ctx = _ctx(ctx)
    w, h = c["size"]
    oc = c.get("oc")
    modes = c["modes"]
    if isinstance(beam_paths, str):
        beam_paths = {_k(m): beam_paths for m in modes}
    if isinstance(beam_oc_paths, str):
        beam_oc_paths = {_k(m): beam_oc_paths for m in modes}
    beam_oc_paths = beam_oc_paths or {}
    oc_beam = bool(oc and beam_oc_paths)
    sel = len(modes) > 1
    c["selector"] = sel
    geo = geometry(c)
    center = [w / 2, h / 2]
    nb = len(geo["ys"]) if c.get("art3d") else c["barrels"]["count"]

    top = {}
    if oc:
        top["OVERCLOCK"] = {"FIRE_INTERVAL_FACTOR": oc.get("fire_interval_factor", 1),
                            "HEAT_PER_SHOT": oc["heat_per_shot"], "HEAT_PER_SECOND": oc.get("heat_per_second", 0)}
        top["HEAT_TO_RESOURCE"] = C.HEAT_TO_RESOURCE
    top["FIRE_INTERVAL"] = c["fire_interval"]

    add_cats, add_buffs = intake_fields(c, ctx)
    cats = ["defense", "uses_ammo", "is_crewed"]
    for x in list(c.get("extra_categories", [])) + add_cats:
        if x not in cats:
            cats.append(x)
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
        "TypeCategories": cats,
        "SignificanceToggle": "ScorchedToggle",
        "ReceivableBuffs : ^/0/ReceivableBuffs": list(add_buffs),
        "ProhibitedBy : ^/0/ProhibitedBy": ["tall"],
    }
    ring = C.tall_ring(w, h, c.get("ring", 1))
    if ring:
        part["ProhibitRects"] = ring
    part["AllowedDoorLocations"] = C.door_locations(w, h)
    part["EditorIcon"] = C.editor_icon(w, h, geo["overhang"])

    comp = {}
    comp.update(C.standard_toggles(bool(oc), c["cp"], defend_only=True))

    comp[comment("---- municao: por modo i (0 HE, 4 FRAG), MagStorage_i + Splitter_i + MagConsumer_i ----")] = None
    if sel:
        ammo_selector(comp, c, modes)
    for i, m in enumerate(modes):
        mag_storage(comp, c, m, i, w, h)
        mag_consumers(comp, m, sel)
    if sel:
        for m in modes:
            k = _k(m)
            comp[f"HasAmmo_{k}"] = {"Type": "MultiToggle", "Toggles": [f"ModeToggle_{k}", f"Splitter_{k}"],
                                    "Mode": "All"}
        comp["AmmoPrereq"] = {"Type": "MultiToggle", "Toggles": [f"HasAmmo_{_k(m)}" for m in modes], "Mode": "Any"}
    else:
        comp["AmmoPrereq"] = {"Type": "MultiToggle", "Toggles": [f"Splitter_{_k(modes[0])}"], "Mode": "Any"}
    if oc_beam:
        for m in modes:
            k = _k(m)
            comp[f"FireToggle_{k}_N"] = {"Type": "MultiToggle",
                                         "Toggles": [f"ModeToggle_{k}" if sel else "IsOperational",
                                                     "{ Toggle=IsOverclocked; Invert=true }"], "Mode": "All"}
            comp[f"FireToggle_{k}_OC"] = {"Type": "MultiToggle",
                                          "Toggles": [f"ModeToggle_{k}" if sel else "IsOperational", "IsOverclocked"],
                                          "Mode": "All"}
    # logistica (Fita / acoplamento / esteira e devolucao) pelo seam do intake; sem o modulo, so a tripulacao
    intake_components(comp, c, ctx)

    fi = "&~/FIRE_INTERVAL"
    fi_path = "&~/Part/Components/Turret/FireInterval"
    if oc and oc.get("fire_interval_factor", 1) != 1:
        fi = {"BaseValue": "&~/FIRE_INTERVAL",
              "Modifiers": [{"Type": "BuffRemap", "BuffType": "Overclock", "ModificationMode": "Multiply",
                             "RemapFrom": [0, 1], "RemapTo": [1, "(&~/OVERCLOCK/FIRE_INTERVAL_FACTOR)"]}]}
        fi_path += "/BaseValue"

    comp[comment("---- torre ----")] = None
    comp["Turret"] = {
        "Type": "TurretWeapon",
        "Location": geo["pivot"],
        "Rotation": "-90d",
        "OperationalToggle": "IsOperational",
        "AutoFireToggle": "AutoFireToggle",
        "FireInterval": fi,
        "FiringArc": f"{c['arc']}d",
        "RotateSpeed": f"{c['rotate']}d",
        # tolerancia de mira do spec (4/4/3 graus) para acompanhar os raios rapidos do SW:ACD;
        # flak_cannon_large.rules l.454 e a flak do SW:ACD (turbolaser_flak_cannon01.rules l.358) usam 30d
        "FireThresholdAngle": f"{c['threshold']}d",
        "TargetSearchesPerSecond": c.get("searches", 8),
        # aquisicao de alvo (defense_design C4). Todos os campos existem na 0.30.3 (ae16922) e no SW:ACD:
        # candidatos validados por busca (padrao do jogo = 1): manipulator_beam_emitter.rules 0.30.3 l.448 (10),
        # SW resource_collector_tiny.rules l.358 (10)
        "TargetChecksPerSearch": _whole(c.get("checks_per_search", 4), "checks_per_search"),
        # buscas imediatas quando o alvo some (padrao 1): chaingun.rules 0.30.3 l.742 (5)
        "InstantSearchesAfterTargetLost": _whole(c.get("instant_searches", 3), "instant_searches"),
        # segura o alvo depois de cancelar: point_defense.rules 0.30.3 l.372 (.5)
        "HoldTargetAfterCancel": c.get("hold_after_cancel", 0.5),
        # fica virada para o fluxo de disparos entre um alvo e outro (padrao true = volta ao centro)
        "ReturnToCenter": False,
        # so defende: nunca mira pecas de nave nem aceita alvo do jogador (point_defense.rules l.383/390)
        "AIFirepowerRating": 0,
        "IncludeInFirepowerEstimation": False,
        "CanBeGivenExplicitTarget": False,
        "AllowShipWideExplicitTargets": False,
        "AllowDirectControl": False,
        # o feixe do modo ativo (BeamEmitterProxy: tractor_beam_emitter.rules l.656-660)
        "Emitter": "BaseFlakEmitterProxy",
        # passa por cima das nossas torres (IsHigh): manipulator_beam_emitter.rules l.447-448
        "IgnoreFriendlyShipLowLOSChecks": True,
        "IgnoreFriendlyShipHighLOSChecks": True,
        # destrocos nao bloqueiam a mira: manipulator_beam_emitter.rules 0.30.3 l.446
        "IgnoreJunkLOSChecks": True,
        # dispara mesmo com a linha de visada bloqueada (a explosao so pega projeteis, nunca casco): flak do SW:ACD
        # (turbolaser_flak_cannon01.rules l.361) e lancadores vanilla (missile_launcher_he.rules 0.30.3 l.401)
        "AllowFireWithBlockedLOS": True,
        "AlwaysShowCoverage": True,
        "FirePermissionToggle": "FireModeToggle",
        "AutoTargetCrewSafetyDist": 8,
        # duas listas: misseis/minas primeiro; granadas/laser/ion numa lista Overridable (point_defense.rules 0.30.3
        # l.390, flak_cannon_large.rules 0.30.3 l.475, SW turbolaser_flak_cannon01.rules l.376)
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
        # SO no build de diagnostico (BS_PD_DEBUG): manipulator_beam_emitter.rules 0.30.3 l.451 (HasTarget)
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

    comp[comment("---- emissores: um bloco por modo (e por estado de overclock com feixe OC) ----")] = None
    burst = c.get("burst", 1) or 1
    oc_states = [False, True] if oc_beam else [False]
    for m in modes:
        k = _k(m)
        for s in oc_states:
            base = {
                "Type": "BeamEmitter",
                "ChainedTo": "Turret",
                "GetTargetFrom": "Turret",
                "ResourceStorage": f"Splitter_{k}",
                "FireTrigger": VOID,
                "Location": [geo["muzzle"], 0],
                "OperationalToggle": "IsOperational",
                "ResourcesUsed": int(m.get("units_per_shot", 1)),
                "Recoil": c.get("recoil", 4),
                "Burst": burst,
            }
            if burst > 1:
                base["BurstDelay"] = c.get("burst_delay", 0.03)
                base["UseResourcePerShotInBurst"] = True
            src = f"<{beam_oc_paths[k]}>/Beam" if s else f"<{beam_paths[k]}>"
            inner = {f"BaseFlakEmitter : {src}": base}
            for i, y in enumerate(geo["ys"]):
                inner[f"Emitter{i + 1} : BaseFlakEmitter"] = {"Location": [geo["muzzle"], y],
                                                                  "FireTrigger": triggers[i]}
            if oc_beam:
                tname = f"FireToggle_{k}_{'OC' if s else 'N'}"
            elif sel:
                tname = f"ModeToggle_{k}"
            else:
                tname = None
            if tname is None:
                comp.update(inner)
                continue
            comp[f"Fire_{k}_{'OC' if s else 'N'}"] = {"Type": "ToggledComponents", "Toggle": tname,
                                                      "IncludeInBlueprints": (not s), "Components": inner}

    # proxies: a torre fala com o feixe do modo ativo e os efeitos com o cano ativo (mesmos IDs em cada bloco)
    comp["BaseFlakEmitterProxy"] = {"Type": "BeamEmitterProxy", "ComponentID": "BaseFlakEmitter", "ChainedTo": "Turret"}
    proxies_n, proxies_oc, proxies_all = [], [], []
    fx = c["fx"]
    # clarao de boca proprio do overclock (fx["particles_oc"], do pacote de calibre): par de proxies normal /
    # overclock (ProxyToggle = IsOverclocked), como os canhoes (guns.py) e o cannon_deck.rules 0.30.3 l.912-934
    oc_fx = bool(oc) and bool(fx.get("particles_oc"))
    for i, y in enumerate(geo["ys"]):
        p = f"Emitter{i + 1}Proxy"
        comp[p] = {"Type": "BeamEmitterProxy", "ComponentID": f"Emitter{i + 1}", "ChainedTo": "Turret",
                   "Location": [geo["muzzle"], y]}
        proxies_all.append(p)
        if oc_fx:
            comp[f"{p}_OC : {p}"] = {"ProxyToggle": "IsOverclocked"}
            comp[f"{p}_N : {p}_OC"] = {"InvertProxyToggle": True}
            proxies_oc.append(f"{p}_OC")
            proxies_n.append(f"{p}_N")
        else:
            proxies_n.append(p)

    def _fire_media(particles, sounds):
        media = [f"&<{p}>" for p in particles]
        snd = {"RandomSounds": [Q(s) for s in sounds], "Volume": fx.get("volume", 0.35),
               "SpeedVariation": 0.08, "MaxConcurrent": fx.get("max_concurrent", 30)}
        media.append(Inh("/BASE_SOUNDS/AudioExterior", snd))
        return media

    for i, p in enumerate(proxies_n):
        comp[f"FireEffect{i + 1}"] = {"Type": "TriggeredEffects", "ChainedTo": p, "Trigger": p,
                                      "Location": [fx.get("offset", 0), 0],
                                      "MediaEffects": _fire_media(fx["particles"], fx["sound"])}
    for i, p in enumerate(proxies_oc):
        comp[f"Overclock_FireEffect{i + 1}"] = {"Type": "TriggeredEffects", "ChainedTo": p, "Trigger": p,
                                                "Location": [fx.get("offset", 0), 0],
                                                "MediaEffects": _fire_media(fx["particles_oc"],
                                                                            fx.get("sound_oc") or fx["sound"])}

    comp[comment("---- tripulacao ----")] = None
    comp.update(C.crew_block(crew_positions_for(c, geo), "AmmoPrereq"))

    if oc:
        comp.update(C.overclock_machinery(center, w, h, proxies_all, has_constant_heat=oc.get("heat_per_second", 0) > 0,
                                          skip_down=skip_down_for(c)))
        # o MultiTrigger de calor so e ativo em overclock, entao contar os proxies de todos os canos e seguro
        comp["PeakHeatGenerationValue"] = {
            "Type": "StaticValue",
            "SHOT_HEAT_PER_SECOND": "(&~/OVERCLOCK/HEAT_PER_SHOT) * (&~/Part/SecondaryToolTip/StatsByCategory/0/Stats/ROF)",
            "Value": "(&~/OVERCLOCK/HEAT_PER_SECOND) + (&SHOT_HEAT_PER_SECOND)"}
        comp["HeatGenerationStatProvider"] = {"Type": "StatProvider", "Stat": "HeatGeneration",
                                              "OperationalToggle": "OverclockModeToggle",
                                              "ValueFrom": "PeakHeatGenerationValue"}

    comp[comment("---- graficos ----")] = None
    deck_graphics(comp, c, geo, proxies_all, recoil_interval=0.03)
    if dbg:
        # build de diagnostico: luz extra do teto ligada pela propria torre (chaingun.rules 0.30.3 l.470-474)
        comp["DebugTargetToggle"] = {"Type": "MultiToggle", "Toggles": ["Turret"], "Mode": "Any"}
        comp["DebugTargetLight"] = {
            "Type": "Graphics", "Location": center, "OperationalToggle": "DebugTargetToggle",
            "OperationalLighting": {"Layer": Q("lights_add"),
                                    "DamageLevels": [{"File": Q("lights.png"), "Size": [w, h]}]}}

    comp.update(C.destroyed_effects(center, w, h))
    cookoff_effects(comp, c, center, modes)
    comp["Indicators"] = C.weapon_indicators(center, "AmmoPrereq", bool(oc), "&~/FIRE_INTERVAL")
    comp["Blueprints"] = C.blueprint(w, h)
    part["Components : ^/0/Components"] = comp

    m0 = modes[0]
    part["Stats"] = {"CrewRequired": "&~/Part/Components/PartCrew/Crew",
                     "AmmoCapacity": f"&~/Part/Components/MagStorage_{_k(m0)}/MaxResources",
                     "BSShotsPerMag": f"&~/Part/Components/Splitter_{_k(m0)}/ToQuantity"}

    def em_path(k, s):
        if not oc_beam and not sel:
            return "&~/Part/Components/BaseFlakEmitter"
        return f"&~/Part/Components/Fire_{k}_{'OC' if s else 'N'}/Components/BaseFlakEmitter"

    cats_stats = []
    for m in modes:
        k = _k(m)
        em = em_path(k, False)
        cats_stats.append({
            "NameKey": Q(f"StatCategories/BSAmmo_{m['ammo']}"),
            "Stats": {
                "DamagePerShotVsShots": f"{em}/STAT_DAMAGE",
                "ROF": f"{burst} / ({fi_path})",
                "DamagePerSecondVsShots": "(&DamagePerShotVsShots) * (&ROF)",
                "ShotDamage": ["&../DamagePerShotVsShots", "&../DamagePerSecondVsShots"],
                # 2a carga, so contra laser/ion_shot (STAT_LASER_DAMAGE na raiz do feixe); linha propria
                # BSShotDamageVsLasers (infra.part_stats + Stats/BSShotDamageVsLasersFmt): [por disparo, por segundo]
                "DamagePerShotVsLasers": f"{em}/STAT_LASER_DAMAGE",
                "DamagePerSecondVsLasers": "(&DamagePerShotVsLasers) * (&ROF)",
                "BSShotDamageVsLasers": ["&../DamagePerShotVsLasers", "&../DamagePerSecondVsLasers"],
                "DamageArea": f"{em}/STAT_RADIUS",
                "Range": f"{em}/Range",
                "Arc": "deg(&~/Part/Components/Turret/FiringArc)",
                "TurretSpeed": "deg(&~/Part/Components/Turret/RotateSpeed)",
                "ShotSpeed": "Infinity",
                "AmmoPerShot": f"({em}/ResourcesUsed) / (&~/Part/Components/Splitter_{k}/ToQuantity)",
                "AmmoPerSecond": "(&AmmoPerShot) * (&ROF)",
                "ShotAmmoUsage": ["&../AmmoPerShot", "&../AmmoPerSecond"],
            }})
    part["StatsByCategory"] = cats_stats
    if oc:
        oc_stats = {"ROF": f"{burst} / (({fi_path}) * (&~/OVERCLOCK/FIRE_INTERVAL_FACTOR))"}
        if oc_beam:
            oem = em_path(_k(m0), True)
            oc_stats.update({"ShrapnelFieldRadius": f"{oem}/STAT_CLOUD_RADIUS",
                             "ShrapnelFieldDamagePool": f"{oem}/STAT_CLOUD_POOL",
                             "ShrapnelFieldLifetime": f"{oem}/STAT_CLOUD_LIFETIME"})
        oc_stats.update({"HeatPerShot": "(&~/OVERCLOCK/HEAT_PER_SHOT)",
                         "HeatGeneration": "(&~/OVERCLOCK/HEAT_PER_SECOND)"})
        part["SecondaryToolTip"] = {
            "TitleKey": Q("StatCategories/Overclocked"),
            "DescriptionKey": Q(f"Parts/{c['key']}OverclockDesc"),
            "StatsByCategory": [{"NameKey": Q(f"StatCategories/BSAmmo_{m0['ammo']}"), "Stats": oc_stats}]}
    top["Part : " + C.base_part_path(w, h, bool(oc))] = part
    return top, {"geo": geo, "center": center}


# ----------------------------------------------------------------------------- ganchos do build_mod
def build_shot(out, s, header):
    """Kind 'frag_fragment' (SPEC.generator_mapping.shot_dispatch): fragmento da Nuvem de Fragmentos, escrito em
    shots/<pasta da defesa>/<arquivo>.rules ao lado do feixe FRAG que o referencia (&<arquivo.rules>)."""
    if s.get("kind") != "frag_fragment":
        return None
    from bsgen import shots
    import bs_data as D
    s = dict(s)
    s.setdefault("tracer_color", D.ammo_color("frag", "tracer"))
    rel = f"shots/{s.get('dir') or s['file']}/{s['file']}.rules"
    out.text(rel, render(shots.build_frag_fragment(s), header + f"\nFragmento da Nuvem de Fragmentos: {s['file']} "
                                                                f"({s.get('variant')})"))
    return rel


def parts(out, D, ctx):
    """Escreve as 3 defesas (parts/<curto>/<curto>.rules) com os feixes ja escritos (ctx['shot_rel'])."""
    for c in D.DEFENSES:
        pdir = f"parts/{c['short']}"
        beams, beams_oc, missing = {}, {}, []
        for m in c["modes"]:
            k = _k(m)
            rel = ctx["shot_rel"].get(m["beam"])
            if rel is None:
                missing.append(m["beam"])
            else:
                beams[k] = ctx["relpath"](pdir, rel)
            if m.get("fragment") and m["fragment"] not in ctx["shot_rel"]:
                missing.append(m["fragment"])
            if m.get("beam_oc"):
                rel = ctx["shot_rel"].get(m["beam_oc"])
                if rel is None:
                    missing.append(m["beam_oc"])
                else:
                    beams_oc[k] = ctx["relpath"](pdir, rel)
        if missing:
            ctx["warn"](f"peca {c['id']} pulada: tiros nao escritos {sorted(set(missing))}")
            continue
        top, info = build_ciws(c, beams, beams_oc, ctx)
        rel = f"{pdir}/{c['short']}.rules"
        code = f" \"{c['codename']}\"" if c.get("codename") else ""
        out.text(rel, render(top, ctx["header"] + f"\nDefesa: {c['name_en']} / {c['name_pt']}{code}"))
        write_art(out, pdir, c, info, ctx)
        ctx["add_part"](c["id"])


# ----------------------------------------------------------------------------- conferencia (selfcheck)
def selfcheck(mod_dir, SPEC):
    """Confere as defesas escritas: MagStorage_0/_4 (internal_stock), Splitter_i, ResourcesUsed, AvailableChoices,
    Crew/CommandPoints, FIRE_INTERVAL e, por feixe, carga contra tiros e contra laser (guns.defesa_antilaser),
    raios, alcance, SpawnBullets dos fragmentos (Count/Arc/Spread/InheritVelocity) e o fragmento (dano, sem
    Targetable, variante de guns.frag_fragment)."""
    import bs_data as D
    errs = []
    defs = {d["id"]: d for d in SPEC["defenses"]}
    trans = {d["id"]: d for d in D.SPEC_DEFENSES}
    shots = {s["file"]: s for s in D.SHOTS}
    for c in D.DEFENSES:
        d = defs.get(c["id"])
        short = c["short"]
        root = rules_root(os.path.join(mod_dir, "parts", short, f"{short}.rules"))
        if root is None or d is None:
            errs.append(f"{short}: parts/{short}/{short}.rules ausente/ilegivel ou fora do spec")
            continue
        comp = node_at(root, "Part/Components")
        if not _eq(num_at(comp, "PartCrew/Crew"), d["crew"]):
            errs.append(f"{short}: Crew {num_at(comp, 'PartCrew/Crew')} != {d['crew']}")
        if not _eq(num_at(comp, "CommandConsumer/CommandPoints"), d["command_points"]):
            errs.append(f"{short}: CommandPoints != {d['command_points']}")
        rate = d.get("fire_rate_airbursts_per_s") or d.get("fire_rate_shots_per_s")
        want_fi = round((d.get("burst") or 1) / rate, 4)
        if not _eq(num_at(root, "FIRE_INTERVAL"), want_fi, 1e-3):
            errs.append(f"{short}: FIRE_INTERVAL {num_at(root, 'FIRE_INTERVAL')} != {want_fi}")
        ac = list_at(comp, "AmmoTypeToggle/AvailableChoices")
        if ac != [str(x) for x in d["available_choices"]]:
            errs.append(f"{short}: AvailableChoices {ac} != {d['available_choices']}")
        stock = d["internal_stock"]["internal_storage_units"]
        tmodes = {m["index"]: m for m in (trans.get(c["id"]) or d)["ammo_modes"]}
        for m in d["ammo_modes"]:
            i = m["index"]
            if not _eq(num_at(comp, f"MagStorage_{i}/MaxResources"), stock):
                errs.append(f"{short}: MagStorage_{i} {num_at(comp, f'MagStorage_{i}/MaxResources')} != {stock}")
            if not _eq(num_at(comp, f"Splitter_{i}/ToQuantity"), m["splitter_to_quantity"]):
                errs.append(f"{short}: Splitter_{i} ToQuantity != {m['splitter_to_quantity']}")
            em = node_at(comp, f"Fire_{i}_N/Components")
            base = next((x for x in (em.children if em else []) if x.name == "BaseFlakEmitter"), None)
            if base is None or not _eq(num_at(base, "ResourcesUsed"), m["resources_used_per_shot"]):
                errs.append(f"{short}/{m['key']}: ResourcesUsed != {m['resources_used_per_shot']}")
            if base is not None and (node_at(base, "ResourceStorage") is None
                                     or node_at(base, "ResourceStorage").value != f"Splitter_{i}"):
                errs.append(f"{short}/{m['key']}: o feixe nao puxa do Splitter_{i}")
            errs += _check_beam(mod_dir, c, m, tmodes.get(i, m), shots, D)
    return errs


def _check_beam(mod_dir, c, m, tm, shots, D):
    errs = []
    bid = m["beam_file"].split(".", 1)[1]
    s = shots.get(bid) or {}
    root = rules_root(os.path.join(mod_dir, "shots", s.get("dir") or c["short"], f"{bid}.rules"))
    if root is None:
        return [f"{bid}: feixe ausente ou ilegivel"]
    if not _eq(num_at(root, "Range"), c["spec"]["range_m"]):
        errs.append(f"{bid}: Range {num_at(root, 'Range')} != {c['spec']['range_m']}")
    fx = node_at(root, "HitNothing/HitEffects")
    items = fx.children if fx else []
    exp = [x for x in items if node_at(x, "Type") and node_at(x, "Type").value == "ExplosiveDamage"]
    bs, bl = m["blast_vs_shots"], tm["blast_vs_lasers"]
    if len(exp) < 2:
        return errs + [f"{bid}: HitNothing sem as duas cargas"]
    if not (_eq(num_at(exp[0], "TotalDamage"), bs["total_damage"]) and _eq(num_at(exp[0], "Radius"), bs["radius_m"])):
        errs.append(f"{bid}: carga contra tiros {num_at(exp[0], 'TotalDamage')} r{num_at(exp[0], 'Radius')} != "
                    f"{bs['total_damage']} r{bs['radius_m']}")
    if not (_eq(num_at(exp[1], "TotalDamage"), bl["total_damage"]) and _eq(num_at(exp[1], "Radius"), bl["radius_m"])):
        errs.append(f"{bid}: carga contra laser {num_at(exp[1], 'TotalDamage')} r{num_at(exp[1], 'Radius')} != "
                    f"{bl['total_damage']} r{bl['radius_m']}")
    fr = m.get("fragments")
    sp = [x for x in items if node_at(x, "Type") and node_at(x, "Type").value == "SpawnBullets"
          and (node_at(x, "Bullet").value or "") == "&~/FRAGMENT"]
    if fr:
        half = fr["cone_half_deg"]
        if len(sp) != 1:
            return errs + [f"{bid}: FRAG sem o SpawnBullets dos fragmentos"]
        x = sp[0]
        if not _eq(num_at(x, "Count"), fr["count"]):
            errs.append(f"{bid}: fragmentos Count {num_at(x, 'Count')} != {fr['count']}")
        arc = [num_at(n) for n in node_at(x, "Arc").children] if node_at(x, "Arc") else []
        spr = [num_at(n) for n in node_at(x, "Spread").children] if node_at(x, "Spread") else []
        if arc != [-half, 2 * half]:
            errs.append(f"{bid}: Arc {arc} != [{-half}, {2 * half}]")
        if spr != [-3, 3]:
            errs.append(f"{bid}: Spread {spr} != [-3, 3] (faixa simetrica)")
        if (node_at(x, "InheritVelocity").value if node_at(x, "InheritVelocity") else "") != "false":
            errs.append(f"{bid}: InheritVelocity deveria ser false")
        fid = fr["fragment_id"].split(".", 1)[1]
        froot = rules_root(os.path.join(mod_dir, "shots", c["short"], f"{fid}.rules"))
        if froot is None:
            errs.append(f"{fid}: fragmento ausente (shots/{c['short']}/{fid}.rules)")
        else:
            if node_at(froot, "Components/Targetable") is not None:
                errs.append(f"{fid}: fragmento com Targetable")
            variant = D.switch("guns.frag_fragment")
            if variant == "simplehit":
                dmg = num_at(froot, "Components/Hit/HitBullet/HitEffects/0/Damage")
                if (node_at(froot, "Components/Hit/Type").value if node_at(froot, "Components/Hit/Type") else "") \
                        != "SimpleHit" or node_at(froot, "Components/Hit/HitOperational/HitEffects") is not None:
                    errs.append(f"{fid}: simplehit sem SimpleHit ou com HitEffects no casco")
            else:
                dmg = num_at(froot, "Components/DamagePool/Damage")
                if node_at(froot, "Components/VolHit") is None:
                    errs.append(f"{fid}: volumehit sem VolumeHit")
            if not _eq(dmg, fr["damage_each_vs_bullets"]):
                errs.append(f"{fid}: dano {dmg} != {fr['damage_each_vs_bullets']}")
    elif sp:
        errs.append(f"{bid}: feixe HE com fragmentos")
    return errs
