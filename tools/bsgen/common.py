"""Blocos comuns reaproveitados por todas as pecas do Bullet Strike.

Tudo aqui segue padroes copiados dos arquivos vanilla 0.30.x (cannon_deck, cannon_large,
flak_cannon_large, chaingun, factory_ammo). Comentarios citam a origem quando util.
"""

from rules_dsl import Q, VOID, Inh, comment

AUTHOR = "rafaeltessaro"
MOD_ID = f"{AUTHOR}.bullet_strike"
EDITOR_GROUP = "BulletStrike"

# Categorias de projeteis que as defesas derrubam. "ion_shot" e a categoria dos tiros ionicos do
# SW:ACD; categorias sao texto livre, entao nao causa erro quando o SW:ACD nao esta instalado.
ANTI_SHOT_CATEGORIES = ["missile", "mine", "bullet", "laser", "ion_shot"]

HEAT_TO_RESOURCE = "&<./Data/statuses/heat/heat.rules>/STATUS_TO_RESOURCE_RATIO"


def pid(short):
    return f"{AUTHOR}.{short}"


def num(v):
    return v


def size_class(w, h):
    """Escolhe o arquivo base vanilla pelo tamanho (regra usada pelo jogo base)."""
    area = w * h
    if area <= 2:
        return "base_part_terran"
    if area <= 6:
        return "base_med_part_terran"
    return "base_large_part_terran"


BASE_PARTS = ("base_part_terran", "base_med_part_terran", "base_large_part_terran")


def base_part_path(w, h, overclock, base=None):
    """base: arquivo base pedido pelo spec (sem o sufixo _overclock); None = regra por area (size_class)."""
    base = base or size_class(w, h)
    if base not in BASE_PARTS:
        raise ValueError(f"arquivo base desconhecido: {base}")
    if overclock:
        base += "_overclock"
    return f"<./Data/ships/terran/{base}.rules>/Part"


def effect_size(w, h):
    area = w * h
    if area <= 2:
        return "Small", "MachinesOn", "MachinesOff"
    if area <= 6:
        return "Med", "MachinesOn", "MachinesOff"
    if area <= 16:
        return "Big", "MachinesOnLarge", "MachinesOffLarge"
    return "Huge", "MachinesOnLarge", "MachinesOffLarge"


def tall_ring(w, h, t):
    """Anel 'tall' (cima/esquerda/direita) igual ao do Deck Cannon (cannon_deck.rules l.36-41).

    t = espessura em tiles. Atras (embaixo) nao ha anel, entao duas armas podem ficar costas com costas.
    """
    if t <= 0:
        return []
    return [
        ["tall", [-t, -t, w + 2 * t, t]],
        ["tall", [-t, 0, t, h]],
        ["tall", [w, 0, t, h]],
    ]


def door_locations(w, h):
    doors = []
    for y in range(h):
        doors.append([-1, y])
    for y in range(h):
        doors.append([w, y])
    for x in range(w):
        doors.append([x, h])
    for x in range(w):
        doors.append([x, -1])
    return doors


def standard_toggles(overclock, command_points, defense=False, fire_pref_default=2):
    c = {}
    toggles = ["PowerToggle", "PartCrew", "ScorchedToggle"]
    if overclock:
        toggles.append("&~/Part/^/0/OVERCLOCK_OPERATIONAL")
    c["IsOperational"] = {"Type": "MultiToggle", "Toggles": toggles, "Mode": "All"}
    c["CommandConsumptionToggle"] = {"Type": "MultiToggle", "Toggles": ["PowerToggle", "ScorchedToggle"], "Mode": "All"}
    c["PowerToggle"] = {"Type": "UIToggle", "ToggleID": Q("on_off"), "Default": 1, "RequiresCommand": False}
    c["ScorchedToggle"] = {"Type": "StatusToggle", "StatusType": "cosmoteer.scorched", "MinStatusValue": 1, "Invert": True}
    c["CommandConsumer"] = {"Type": "CommandConsumer", "OperationalToggle": "CommandConsumptionToggle",
                            "CommandPoints": command_points}
    c["FireModeToggle"] = {"Type": "UIToggle", "ToggleID": Q("fire_mode"), "Default": 1, "ToggledOnChoices": [0, 1, 2]}
    c["AutoTargetToggle"] = {"Type": "ModeToggle", "Mode": "FireModeToggle", "OnModes": [1, 2]}
    c["AutoFireToggle"] = {"Type": "ModeToggle", "Mode": "FireModeToggle", "OnMode": 2}
    if defense:
        # Atacar / Defender / Ambos (flak_cannon_large.rules l.143-192)
        c["FirePrefToggle"] = {"Type": "UIToggle", "ToggleID": Q("fire_pref"), "Default": fire_pref_default}
        c["FirePrefAttack"] = {"Type": "ModeToggle", "Mode": "FirePrefToggle", "OnModes": [0, 2]}
        c["FirePrefDefend"] = {"Type": "ModeToggle", "Mode": "FirePrefToggle", "OnModes": [1, 2]}
        c["AttackToggle"] = {"Type": "MultiToggle", "Toggles": ["AutoTargetToggle", "FirePrefAttack"], "Mode": "All"}
        c["DefendToggle"] = {"Type": "MultiToggle", "Toggles": ["AutoTargetToggle", "FirePrefDefend"], "Mode": "All"}
    if overclock:
        c["IsOperationalNonOverclocked"] = {"Type": "MultiToggle",
                                            "Toggles": ["IsOperational", "{ Toggle=IsOverclocked; Invert=true }"],
                                            "Mode": "All"}
    return c


def overclock_machinery(center, w, h, heat_triggers, has_constant_heat=True, shot_heat=True):
    """Componentes de overclock (calor por tiro, calor constante, portas termicas).

    heat_triggers: lista de nomes de triggers que disparam somente em overclock.
    shot_heat=False: sem calor por tiro (lancadores cobram o calor por missil carregado no autoloader).
    """
    c = {}
    c["OverclockStateValue"] = {"Type": "ToggleValueSelector", "Toggle": "OverclockModeToggle",
                                "ToggleOffValue": "Zero", "ToggleOnValue": "One"}
    c["Zero"] = {"Type": "StaticValue", "Value": 0}
    c["One"] = {"Type": "StaticValue", "Value": 1}
    c["OverheatEffects : ^/0/OverheatEffects"] = {"Location": center}
    if shot_heat:
        # Mesmo padrao do Deck Cannon: MultiTrigger dos proxies, ativo somente em overclock.
        c["Overclock_EmissionTriggered"] = {"Type": "MultiTrigger", "OperationalToggle": "IsOverclocked",
                                            "Triggers": heat_triggers}
        trig = "Overclock_EmissionTriggered"
        c["Overclock_ShotHeatProducer"] = {
            "Type": "ResourceChange",
            "ResourceStorage": "&~/Part/^/0/HEAT_TARGET_STORAGE",
            "Trigger": trig,
            "Amount": "(&~/OVERCLOCK/HEAT_PER_SHOT) * (&~/HEAT_TO_RESOURCE)",
        }
    if has_constant_heat:
        c["Overclock_ConstantHeatProducer"] = {
            "Type": "ResourceConverter",
            "OperationalToggle": "IsOperationalOverclocked",
            "HEAT_PER_INTERVAL": "ceil((&~/OVERCLOCK/HEAT_PER_SECOND) * (&Interval))",
            "ToQuantity": "(&HEAT_PER_INTERVAL) * (&~/HEAT_TO_RESOURCE)",
            "ToStorage": "&~/Part/^/0/HEAT_TARGET_STORAGE",
            "Interval": 0.5,
        }
    # Portas termicas nas laterais e embaixo (como o Deck Cannon).
    first = None
    idx = 0
    for y in range(h):
        name = f"Port_Thermal_L{y}"
        if first is None:
            c[f"{name} : ~/Part/^/0/BASE_THERMAL_PORT"] = {"Location": [0, y], "Direction": "Left"}
            first = name
        else:
            c[f"{name} : {first}"] = {"Location": [0, y], "Direction": "Left"}
        idx += 1
    for y in range(h):
        c[f"Port_Thermal_R{y} : {first}"] = {"Location": [w - 1, y], "Direction": "Right"}
    for x in range(w):
        c[f"Port_Thermal_D{x} : {first}"] = {"Location": [x, h - 1], "Direction": "Down"}
    return c


def destroyed_effects(center, w, h):
    sz, on, off = effect_size(w, h)
    return {
        "OperationEffects": {"Type": "ToggleEffects", "Location": center, "Toggle": "IsOperational",
                             "ToggledOnMediaEffects": f"&/COMMON_EFFECTS/{on}",
                             "ToggledOffMediaEffects": f"&/COMMON_EFFECTS/{off}"},
        "ScorchedTrigger": {"Type": "ToggleTrigger", "Toggle": "ScorchedToggle", "TriggerWhenOn": False},
        "ScorchedEffects": {"Type": "TriggeredEffects", "Trigger": "ScorchedTrigger",
                            "Location": "&../DestroyedEffects/Location",
                            "MediaEffects": f"&/COMMON_EFFECTS/{sz}PartScorched"},
        "DestroyedEffects": {"Type": "DeathEffects", "MediaEffects": f"&/COMMON_EFFECTS/{sz}PartDestroyed",
                             "Location": center},
    }


def weapon_indicators(center, ammo_toggle, overclock, reload_delay, no_ammo_sprite="&/INDICATORS/NoAmmo"):
    """Indicadores (sem energia / sem municao / overclock resetando / sem tripulacao).

    Um indicador aparece enquanto o Toggle esta DESLIGADO (cannon_deck.rules l.1645-1699).
    no_ammo_sprite: lancadores usam &/INDICATORS/NoMissiles (missile_launcher_he.rules l.355).
    """
    inds = [
        {"Toggle": "ScorchedToggle", "AtlasSprite": "&/INDICATORS/Scorched",
         "HidesIndicators": [1, 2, 3, 4] if overclock else [1, 2, 3]},
        {"Toggle": "PowerToggle", "AtlasSprite": {"File": "&/INDICATORS/PowerOff", "Size": [1, 1]},
         "HidesIndicators": [2, 3, 4] if overclock else [2, 3]},
        {"Toggle": ammo_toggle, "Delay": reload_delay,
         "AtlasSprite": {"File": no_ammo_sprite, "Size": [1, 1]}},
    ]
    if overclock:
        inds.append({"Toggle": "&~/Part/^/0/OVERCLOCK_OPERATIONAL",
                     "AtlasSprite : /INDICATORS/OverclockReset": {"Size": [1, 1]},
                     "HidesIndicators": [4]})
    inds.append({"Toggle": "PartCrew", "AtlasSprite": {"File": "&/INDICATORS/NoCrew", "Size": [1, 1]}})
    return {"Type": "IndicatorSprites", "Location": center, "Indicators": inds}


def crew_block(positions, prereq):
    """Gera CrewLocationN + PartCrew (posicoes fixas no casco, como no Deck Cannon)."""
    c = {}
    names = []
    for i, (x, y, rot) in enumerate(positions, start=1):
        n = f"CrewLocation{i}"
        c[n] = {"Type": "CrewLocation", "Location": [x, y], "Rotation": f"{rot}d"}
        names.append(n)
    c["PartCrew"] = {
        "Type": "PartCrew",
        "Crew": len(positions),
        "DefaultPriority": "&/PRIORITIES/Weapon_Crew",
        "PrerequisitesBeforeCrewing": ["PowerToggle", "ScorchedToggle"],
        "HighPriorityPrerequisites": [prereq],
        "CrewDestinations": [f"&../../{n}/Location" for n in names],
        "CrewLocations": names,
    }
    return c


def crew_positions(w, h, n, pivot):
    """Distribui n tripulantes na parte de tras da peca, abaixo da torre."""
    y = h - 0.45
    if h == 1:
        y = 0.55
    if n == 1:
        return [(w / 2, y, 0)]
    pos = []
    for i in range(n):
        x = (i + 0.5) * w / n
        rot = 0
        pos.append((round(x, 3), round(y, 3), rot))
    return pos


def blueprint(w, h):
    return {"Type": "BlueprintSprite", "File": Q("blueprints.png"), "Size": [w, h]}


def editor_icon(w, h, overhang_top=0.0):
    """EditorIcon com a mesma proporcao do icon.png (64 px/tile incluindo o cano que passa da peca)."""
    # vanilla: 21.33 px de UI por tile (point_defense 64x128 -> [21.33, 42.66], cannon_med 128x192 ->
    # [42.66, 64]); altura maxima 92 (cannon_deck 256x448 -> [52.5, 92]).
    th = h + overhang_top
    per_tile = 64 / 3
    width, height = w * per_tile, th * per_tile
    scale = min(1.0, 92.0 / height, 92.0 / width)
    width, height = width * scale, height * scale
    return {"Texture": {"File": Q("icon.png"), "SampleMode": "Linear"},
            "Size": [round(width, 2), round(height, 2)]}
