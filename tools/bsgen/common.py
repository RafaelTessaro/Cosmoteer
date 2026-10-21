"""Blocos comuns reaproveitados por todas as pecas do Bullet Strike.

Tudo aqui segue padroes copiados dos arquivos vanilla 0.30.x (cannon_deck, cannon_large,
flak_cannon_large, chaingun, factory_ammo). Comentarios citam a origem quando util.
"""

import importlib

from rules_dsl import Q, VOID, Inh, comment

AUTHOR = "rafaeltessaro"
# ID e nome do mod vem do perfil do build (SPEC.build_2_0.variants: fita / semfita); bs_data chama set_profile()
MOD_ID = f"{AUTHOR}.bullet_strike"
MOD_NAME = "Bullet Strike"
EDITOR_GROUP = "BulletStrike"


def set_profile(mod_id, name):
    """Perfil do build (variante fita/semfita): ID e Name do mod.rules."""
    global MOD_ID, MOD_NAME
    MOD_ID, MOD_NAME = mod_id, name


def content_module(name, min_api=2):
    """Modulo de conteudo opcional (J2R3-15): importlib.import_module(name); devolve None so quando o PROPRIO modulo
    nao existe (ModuleNotFoundError com e.name == name) ou quando ele declara API < min_api (codigo 1.x ainda nao
    portado). Nunca olha BS_FX_EXT (esse so desliga o registro FX do build_mod). Um import quebrado DENTRO do
    modulo continua estourando. Use para INTAKE = content_module('bsgen.intake') e BELTNET = content_module(
    'bsgen.belt_net')."""
    try:
        mod = importlib.import_module(name)
    except ModuleNotFoundError as e:
        if e.name != name:
            raise
        return None
    if min_api and int(getattr(mod, "API", 0) or 0) < min_api:
        return None
    return mod


def call(mod, fn, *a, **k):
    """mod.fn(*a, **k) se o modulo e a funcao existirem; senao None (seam opcional)."""
    f = getattr(mod, fn, None) if mod is not None else None
    return f(*a, **k) if f is not None else None


def index_names(i, key=None):
    """Nomes dos componentes por modo (indice da tabela, nunca a posicao na lista; SPEC.ammo_index_rules):
    MagStorage_<i>, Splitter_<i>, MagConsumer_<i>, ModeToggle_<i>, FitaEntrada_<i>, Alimentador_<i>, Alimenta_<i>,
    PaiolAcoplado_<i>, AlimentadorAcoplado_<i>, NaoModo_<i>, Devolve_<i>, Devolucao_<i>; com key tambem
    FitaEntra_<key> (proxy da fita, por tipo) e Estoque_<key> (estoque do paiol do tipo)."""
    n = {"storage": f"MagStorage_{i}", "splitter": f"Splitter_{i}", "consumer": f"MagConsumer_{i}",
         "mode_toggle": f"ModeToggle_{i}", "fita_entrada": f"FitaEntrada_{i}", "alimentador": f"Alimentador_{i}",
         "alimenta": f"Alimenta_{i}", "paiol_acoplado": f"PaiolAcoplado_{i}",
         "alimentador_acoplado": f"AlimentadorAcoplado_{i}", "nao_modo": f"NaoModo_{i}", "devolve": f"Devolve_{i}",
         "devolucao": f"Devolucao_{i}", "reserva": f"ReservaTripulacao_{i}"}
    if key is not None:
        n["fita_entra"] = f"FitaEntra_{key}"
        n["estoque"] = f"Estoque_{key}"
    return n


def half(max_resources):
    """ResupplyThreshold da tripulacao = floor(MaxResources / 2) em todos os transportes (R04)."""
    return int(max_resources) // 2


def reserva_sem_fita():
    """True quando a reserva da tripulacao so vale com a maquina SEM fita: logistics.reserva_tripulacao = sem_fita
    SO com logistics.transport = teleporte E bsgen.intake carregado (J2R3-11: FitaLigada so existe ai)."""
    import bs_data as D
    return (D.switch("logistics.transport") == "teleporte" and content_module("bsgen.intake") is not None
            and D.switch("logistics.reserva_tripulacao") == "sem_fita")

# Categorias de projeteis que as defesas derrubam. "ion_shot" e a categoria dos tiros ionicos do
# SW:ACD; categorias sao texto livre, entao nao causa erro quando o SW:ACD nao esta instalado.
ANTI_SHOT_CATEGORIES = ["missile", "mine", "bullet", "laser", "ion_shot"]

# Duas listas de busca automatica nas defesas (defense_design C3/C4): misseis e minas primeiro (lentos e letais,
# sempre interceptados antes); granadas, raios laser e tiros ionicos numa segunda lista Overridable, que um missil
# novo pode tomar. ANTI_SHOT_CATEGORIES continua sendo a uniao das duas (docs e a logica do Saci usam).
PD_PRIORITY_TARGETS = ["missile", "mine"]
PD_SECONDARY_TARGETS = ["bullet", "laser", "ion_shot"]
if sorted(PD_PRIORITY_TARGETS + PD_SECONDARY_TARGETS) != sorted(ANTI_SHOT_CATEGORIES):
    raise ValueError("PD_PRIORITY_TARGETS + PD_SECONDARY_TARGETS tem que ser igual a ANTI_SHOT_CATEGORIES")

# Setor de cobertura da arma (o leque de alcance que aparece ao selecionar a arma ou mandar atacar). Na 0.30.3 /
# 0.30.4 cada TurretWeapon declara o seu: cannon_deck.rules 0.30.3 l.637, point_defense.rules 0.30.3 l.403,
# flak_cannon_large.rules 0.30.3 l.488; o SW:ACD (feito para a 0.30.4) declara em 120 de 125 torres
# (turbolaser_flak_cannon01.rules l.389). Sem ele a 0.30.4c nao mostra o alcance. A 0.30.5 tirou o campo das
# torres (passou para gui/game/sim_gui.rules) e ignora o que sobrar, entao manter e inofensivo. NAO usar
# CoverageLine / DefaultWeaponCoverage* / AllowCustomCoverageEditing (so existem na 0.30.5).
# Valor compartilhado: quem precisar mudar algum campo faz uma copia (dict(COVERAGE_SECTOR_ARC)).
COVERAGE_SECTOR_ARC = {"Texture": "&/INDICATORS/VerticalGradient", "VertexColor": [255, 255, 255, 51],
                       "QuadCount": 64}

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


def standard_toggles(overclock, command_points, defense=False, fire_pref_default=2, defend_only=False):
    """defense = Atacar/Defender/Ambos (flak vanilla, Saci); defend_only = so defesa (flak/CIWS do mod):
    sem fire_pref e sem "Atirar no alvo" no fire_mode, como o point_defense.rules l.97-116."""
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
    if defend_only:
        # -1 Suspender fogo, 1 Disparar a vontade, 2 Disparar automaticamente (sem 0 = alvo explicito),
        # AvailableChoices do point_defense.rules l.102
        c["FireModeToggle"] = {"Type": "UIToggle", "ToggleID": Q("fire_mode"), "Default": 1,
                               "AvailableChoices": [-1, 1, 2], "ToggledOnChoices": [0, 1, 2]}
    c["AutoTargetToggle"] = {"Type": "ModeToggle", "Mode": "FireModeToggle", "OnModes": [1, 2]}
    c["AutoFireToggle"] = {"Type": "ModeToggle", "Mode": "FireModeToggle", "OnMode": 2}
    if defense and not defend_only:
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


def mag_consumer(res, storage, toggle, no_min_priority=False, threshold=None, extra_toggle=None, comp=None,
                 toggle_name=None, fita_gate=True):
    """Consumidor de carregadores da tripulacao (prioridade de arma, botao de consumo no proprio tile).

    threshold: ResupplyThreshold (use half(MaxResources) = floor(Max/2), regra R04 de todos os transportes).
    Reserva sem fita (reserva_sem_fita(): logistics.reserva_tripulacao = sem_fita com teleporte + bsgen.intake) ou
    extra_toggle (nome de outro toggle a somar): o OperationalToggle vira um MultiToggle All [toggle, extra] gravado
    em comp[toggle_name] (padrao 'Reserva_<storage>'; vanilla engine_room.rules:95 {Toggle; Invert = true}); nesses
    casos comp e obrigatorio.
    fita_gate=False: nao soma o FitaLigada mesmo com sem_fita (consumidor que ja nunca recebe, ex. o bloco 'tipo
    fora de uso' do toggled_consumers); sem extra_toggle, comp deixa de ser obrigatorio."""
    extras = []
    if extra_toggle:
        extras.append(extra_toggle)
    if fita_gate and reserva_sem_fita():
        extras.append("{ Toggle=FitaLigada; Invert=true }")
    tog = toggle
    if extras:
        if comp is None:
            raise ValueError(f"mag_consumer({storage}): reserva sem_fita / extra_toggle exige comp= para o MultiToggle")
        tog = toggle_name or f"Reserva_{storage}"
        comp[tog] = {"Type": "MultiToggle", "Toggles": [toggle] + extras, "Mode": "All"}
    c = {"Type": "ResourceConsumer", "ResourceType": res, "Storage": storage,
         "DefaultPriority": "&/PRIORITIES/Weapon_Supply", "OperationalToggle": tog}
    if threshold is not None:
        c["ResupplyThreshold"] = int(threshold)
    if no_min_priority:
        c["AllowNonOperationalMinPriorityDelivery"] = False
    c["ConsumptionToggleButtonOffset"] = [0, -0.4]
    return c


def toggled_consumers(comp, cid, uses, res, storage, on_block, off_block, threshold=None):
    """Consumidor de um tipo de municao numa arma com seletor (chaingun.rules l.383-437).

    O mesmo ID (cid) em dois ToggledComponents ligados pelo toggle 'uses' (tipo escolhido):
      - tipo escolhido: OperationalToggle = CommandConsumptionToggle e entrega de prioridade minima padrao,
        como qualquer arma do jogo (missile_launcher_he.rules): desligada ou chamuscada, a arma continua sendo
        completada se sobrar tripulacao, e volta pronta;
      - tipo fora de uso: OperationalToggle = o proprio 'uses' (sempre desligado dentro deste bloco) e
        AllowNonOperationalMinPriorityDelivery = false: nenhuma entrega; o estoque que ja esta na arma fica.
    Manter o mesmo ID mantem viva a chave de prioridade e a reserva de recursos na troca de tipo (o comentario
    do chaingun: "If storage assignments thrash, then that causes resource AI issues")."""
    comp[on_block] = {"Type": "ToggledComponents", "Toggle": uses,
                      "Components": {cid: mag_consumer(res, storage, "CommandConsumptionToggle", threshold=threshold,
                                                       comp=comp, toggle_name=f"Reserva_{cid}")}}
    # bloco fora de uso: OperationalToggle = 'uses' (sempre desligado enquanto este bloco vale) e sem entrega de
    # prioridade minima, entao nunca recebe; o FitaLigada da reserva sem_fita nao muda nada aqui (fita_gate=False)
    comp[off_block] = {"Type": "ToggledComponents", "Toggle": uses, "Invert": True,
                       "Components": {cid: mag_consumer(res, storage, uses, no_min_priority=True,
                                                        threshold=threshold, fita_gate=False)}}


def overclock_machinery(center, w, h, heat_triggers, has_constant_heat=True, shot_heat=True, port_rows=None,
                        skip_down=()):
    """Componentes de overclock (calor por tiro, calor constante, portas termicas).

    heat_triggers: lista de nomes de triggers que disparam somente em overclock.
    shot_heat=False: sem calor por tiro (lancadores cobram o calor por missil carregado no autoloader).
    port_rows: fileiras com portas laterais (padrao: todas). As fabricas passam range(1, h): a fileira do
    maquinario fica sem porta (factory_he.rules l.288-318, factory_ammo.rules l.253-270).
    skip_down: colunas x da fileira de tras SEM Port_Thermal_D<x> (portas da esteira; D.belt_skip_down(g), que so
    devolve algo com logistics.transport em rede/gemea).
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
    rows = list(range(h)) if port_rows is None else list(port_rows)
    first = None
    for y in rows:
        name = f"Port_Thermal_L{y}"
        if first is None:
            c[f"{name} : ~/Part/^/0/BASE_THERMAL_PORT"] = {"Location": [0, y], "Direction": "Left"}
            first = name
        else:
            c[f"{name} : {first}"] = {"Location": [0, y], "Direction": "Left"}
    for y in rows:
        c[f"Port_Thermal_R{y} : {first}"] = {"Location": [w - 1, y], "Direction": "Right"}
    skip = set(skip_down or ())
    for x in range(w):
        if x in skip:
            continue
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
