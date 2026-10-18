"""Gerador das fabricas (prensas de carregadores / municao especial) do Bullet Strike.

Padroes vanilla: factory_ammo.rules (grades de entrada/saida, conversor, bateria, bonus de fabrica
adjacente) e factory_processor.rules (conversor tirando varias unidades direto da grade de entrada,
com ToggleOnResources = quantidade da receita).
Layout: fileira de cima = maquinario (bloqueado para a tripulacao); fileira de baixo = grades de
entrada (uma coluna por insumo) e, na ultima coluna, a grade de saida.
Overclock, animacao, luzes, sons e cook-off seguem factory_he.rules (3x3) e factory_ammo.rules (2x2).
"""

from rules_dsl import Q, Inh, comment
from bsgen import common as C

RES_STACK = {  # MaxStackSize dos recursos vanilla (resources/*.rules)
    "bullet": 20, "sulfur": 5, "steel": 40, "coil": 40, "coil2": 40, "tristeel": 40, "diamond": 5,
    "enriched_uranium": 10, "uranium": 5, "carbon": 5, "copper": 5, "gold": 5, "iron": 5, "tritanium": 5,
    "hyperium": 20, "processor": 5, "missile_part_he": 10, "missile_part_emp": 10, "missile_part_nuke": 10,
}

RES_FILE = {r: f"./Data/resources/{r}/{r}.rules" for r in RES_STACK}

# Categoria vanilla de cada insumo (factory_mine uses_ammo, factory_ammo uses_sulfur, factory_processor uses_coils,
# factory_emp uses_copper). Insumos sem categoria vanilla equivalente (tri-aco, uranio enriquecido, carregadores do
# mod) ficam sem categoria.
RES_CATEGORY = {"bullet": "uses_ammo", "sulfur": "uses_sulfur", "coil": "uses_coils", "copper": "uses_copper"}

# spec factories[].sounds -> (pasta vanilla, som do maquinario ligado, sons de cada item pronto)
SOUNDS = {
    "ammo": ("factory_ammo", "cannon_ammo_factory_idle.wav",
             [f"cannon_ammo_factory_putdown_0{i}.wav" for i in range(1, 8)]),
    "he": ("factory_he", "he_missile_factory_idle.wav", [f"missile_factory_putdown_0{i}.wav" for i in range(1, 6)]),
    "emp": ("factory_emp", "emp_missile_factory_idle.wav",
            [f"emp_missile_factory_putdown_0{i}.wav" for i in range(1, 6)]),
    "nuke": ("factory_nuke", "nuclear_missiles_factory_idle.wav",
             [f"nuclear_missiles_factory_putdown_0{i}.wav" for i in range(1, 6)]),
}

WALL_DAMAGE = ["walls.png", "walls_33.png", "walls_66.png"]  # niveis de dano das paredes (make_art.factory_art)


def pct(x):
    return f"{int(round(x * 100))}%"


def use_stat(res):
    """ID da linha 'uso de <insumo>' ([por item, por segundo]). Enxofre reaproveita a linha vanilla AmmoSulfurUsage
    (factory_ammo.rules); os demais insumos tem linha propria (registrada em infra.part_stats)."""
    if res == "sulfur":
        return "AmmoSulfurUsage"
    short = res.split(".")[-1]
    if short.startswith("bs_"):
        short = short[3:]
    return "BSAmmo" + "".join(p.capitalize() for p in short.split("_")) + "Usage"


def input_stat_ids(factories):
    """Linhas de estatistica proprias usadas pelas fabricas, na ordem em que aparecem (sem as vanilla)."""
    out = []
    for f in factories:
        for r, _q in f["inputs"]:
            sid = use_stat(r)
            if sid.startswith("BS") and sid not in out:
                out.append(sid)
    return out


def _layout(f):
    n = len(f["inputs"])
    size = f.get("size") or [n + 1, 2]
    he = list(size) == [3, 3] and n <= 2
    if he:
        # layout do factory_he vanilla: maquinario em cima e no centro, entradas nas laterais, saida embaixo
        return 3, 3, True, ([[0, 1], [2, 1]][:n] if n == 2 else [[0, 1]]), [0, 2, 3, 1]
    return n + 1, 2, False, [[i, 1] for i in range(n)], [n, 1, 1, 1]


def _cookoff_hits(ck):
    """Explosao da fabrica cheia (factory_he.rules l.1207-1256 / factory_ammo.rules l.780-829)."""
    return [
        {"Type": "ExplosiveDamage", "TotalDamage": {"BaseValue": ck["op_damage"], "EffectScaleExponent": 1},
         "Radius": ck["op_radius"], "Delay": 0.05, "StatusType": "cosmoteer.fire", "StatusChancePerNDamage": "100%",
         "StatusValue": 1, "StatusValueType": "Interpolated", "NDamage": 1000, "CrewKillChance": "50%",
         "Filter": {"OperationalHealth": True, "StructuralHealth": False, "Friendlies": True}},
        {"Type": "ExplosiveDamage", "TotalDamage": {"BaseValue": ck["st_damage"], "EffectScaleExponent": 1},
         "Radius": ck["st_radius"], "Delay": 0.05,
         "Filter": {"OperationalHealth": False, "StructuralHealth": True, "Friendlies": True, "Crew": False}},
    ]


def build_factory(f, own_stack):
    """own_stack: dict resource_id -> MaxStackSize dos recursos do proprio mod."""
    inputs = f["inputs"]
    out_res, out_qty = f["output"]
    n = len(inputs)
    w, h, he, in_cells, out_rect = _layout(f)
    center = [w / 2, h / 2]
    stack = dict(RES_STACK)
    stack.update(own_stack)
    power = f.get("power")  # bateria por ciclo (None = sem energia)
    oc = f.get("oc")  # overclock (spec factories[].overclock); None = sem overclock
    snd_dir, snd_idle, snd_put = SOUNDS[f.get("sounds") or "ammo"]
    snd_base = f"./Data/ships/terran/{snd_dir}/sounds"

    cats = ["provides_ammo"]
    for r, _q in inputs:
        if r in RES_CATEGORY and RES_CATEGORY[r] not in cats:
            cats.append(RES_CATEGORY[r])
    if power:
        cats.append("uses_power")
    part = {
        "NameKey": Q(f"Parts/{f['key']}"),
        "IconNameKey": Q(f"Parts/{f['key']}Icon"),
        "DescriptionKey": Q(f"Parts/{f['key']}Desc"),
        "ID": C.pid(f["short"]),
        "EditorGroups": [Q(C.EDITOR_GROUP), Q("Production")],
        "Resources": [[r, q] for r, q in f["cost"]],
        "Size": [w, h],
        "IsFlippable": True,
        "SelectionPriority": 1,
        "MaxHealth": f["hp"],
        "TypeCategories": cats,
        "ReceivableBuffs : ^/0/ReceivableBuffs": ["Factory"],
        "BlockedTravelCells": [[x, 0] for x in range(w)] + ([[1, 1]] if he else []),
        "ForceManhattanPathInPart": True,
        "AllowedDoorLocations": ([[-1, 1], [-1, 2], [0, 3], [1, 3], [2, 3], [3, 2], [3, 1]] if he else
                                 [[-1, 1], [w, 1]] + [[x, 2] for x in range(w)]),
        "EditorIcon": {"Texture": {"File": Q("icon.png"), "SampleMode": "Linear"},
                       "Size": [64, round(64 * h / w, 2)] if w >= h else [round(64 * w / h, 2), 64]},
    }

    comp = {}
    op_toggles = ["PowerToggle", "NonJunkToggle", "ScorchedToggle"] + [f"Input{i}" for i in range(n)]
    if power:
        op_toggles.append("BatteryStorage")
    if oc:
        # 3 s parada depois de desligar o overclock (base_part_overclock.rules OverclockReset)
        op_toggles.append("&~/Part/^/0/OVERCLOCK_OPERATIONAL")
    comp["IsOperational"] = {"Type": "MultiToggle", "Toggles": op_toggles, "Mode": "All"}
    comp["NonJunkToggle"] = {"Type": "JunkToggle", "OnWhenJunk": False}
    comp["CommandConsumptionToggle"] = {"Type": "MultiToggle", "Toggles": ["PowerToggle", "ScorchedToggle"],
                                        "Mode": "All"}
    comp["PowerToggle"] = {"Type": "UIToggle", "ToggleID": Q("on_off"), "Default": 1, "RequiresCommand": False}
    comp["ScorchedToggle"] = {"Type": "StatusToggle", "StatusType": "cosmoteer.scorched", "MinStatusValue": 1,
                              "Invert": True, "IncludeWhenUnderConstruction": True}
    comp["CommandConsumer"] = {"Type": "CommandConsumer", "OperationalToggle": "CommandConsumptionToggle",
                               "CommandPoints": f.get("cp", 1)}

    conv_from = []
    splitters = {}  # indice do insumo -> nome do InlineResourceConverter
    for i, (res, qty) in enumerate(inputs):
        cx, cy = in_cells[i]
        frac = qty < 1
        if frac:
            # entrada fracionaria: 1 unidade vira round(1/qty) pedacos (InlineResourceConverter, como no factory_he)
            parts = round(1 / qty)
            if abs(parts * qty - 1) > 0.01 or parts > 50:
                raise ValueError(f"{f['short']}: {qty} {res} nao vira um divisor inteiro (1:{1 / qty:.2f}).")
        else:
            qty = int(qty)
        cap_tiles = 1 if frac or qty <= stack[res] else 2
        if not frac and (qty > 2 * stack[res] or (he and cap_tiles == 2)):
            raise ValueError(f"{f['short']}: receita pede {qty} {res}, mas a grade de entrada so guarda "
                             f"{(1 if he else 2) * stack[res]} (pilha {stack[res]}). Reduza a receita.")
        rect = [cx, cy, 1, 1] if cap_tiles == 1 else [cx, 0, 1, 2]
        grid = {
            "Type": "TypedResourceGrid", "ResourceType": res, "GridRect": rect,
            "Layer": Q("doodads_low"), "SpriteInset": ["8/64", "6/64", "8/64", "9/64"],
            "AllowExternalPickupAndDelivery": True,
        }
        if not frac:
            grid.update({"ToggleOnResources": qty, "ToggleOffResources": qty - 1})
        comp[f"Input{i}"] = grid
        comp[f"Input{i}Consumer"] = {"Type": "TypedResourceGridConsumer", "ResourceType": res,
                                     "Storage": f"Input{i}", "DefaultPriority": "&/PRIORITIES/Factory_Supply",
                                     "OperationalToggle": "CommandConsumptionToggle",
                                     "ConsumptionToggleButtonOffset": [0, -0.4]}
        if frac:
            comp[f"Input{i}Splitter"] = {"Type": "InlineResourceConverter", "ResourceType": res,
                                         "FromStorage": f"Input{i}", "FromQuantity": 1, "ToQuantity": parts}
            splitters[i] = f"Input{i}Splitter"
            conv_from.append({"Storage": f"Input{i}Splitter", "Quantity": 1})
            op_toggles[op_toggles.index(f"Input{i}")] = f"Input{i}Splitter"
        else:
            conv_from.append({"Storage": f"Input{i}", "Quantity": qty})
        if cap_tiles == 2:
            part["BlockedTravelCells"] = [c for c in part["BlockedTravelCells"] if c != [cx, 0]]
    comp["Output"] = {"Type": "TypedResourceGrid", "ResourceType": out_res, "GridRect": out_rect,
                      "Layer": Q("doodads_low"), "SpriteInset": ["8/64", "6/64", "8/64", "9/64"],
                      "SuppliesResources": True, "SupplyToggleButtonOffset": [0, -0.4],
                      "InitToMaxResources": 0, "AllowExternalPickupAndDelivery": True}
    if power:
        # buffer vanilla: 2000 no 2x2 (factory_ammo l.133), 4000 no 3x3 (factory_he l.166)
        comp["BatteryStorage"] = {"Type": "ResourceStorage", "ResourceType": "battery",
                                  "MaxResources": max(4000 if he else 2000, power * 4),
                                  "ReceiveResourceMediaEffects": "&/COMMON_EFFECTS/PowerDeliver"}
        comp["BatteryConsumer"] = {"Type": "ResourceConsumer", "ResourceType": "battery", "Storage": "BatteryStorage",
                                   "DefaultPriority": "&/PRIORITIES/Factory_Supply",
                                   "ResupplyThreshold": max(500, power), "OperationalToggle": "CommandConsumptionToggle"}
        if oc:
            # em overclock cada ciclo gasta POWER_USE_FACTOR x a bateria (factory_he.rules l.193-208)
            pq = {"BaseValue": power, "Modifiers": [Inh("~/MODIFIERS/OVERCLOCK_LERP", {
                "MinValue": "&../../BaseValue", "MaxValue": "(&MinValue) * (&~/OVERCLOCK/POWER_USE_FACTOR)"})]}
        else:
            pq = power
        conv_from.append({"Storage": "BatteryStorage", "Quantity": pq, "MinQuantityForConversion": 1})
    interval_mods = [{"Type": "Buff", "BuffType": "Factory", "ModificationMode": "Divide"}]
    if oc:
        interval_mods.append({"Type": "BuffRemap", "BuffType": "Overclock", "RemapFrom": [0, 1],
                              "RemapTo": [1, "&~/OVERCLOCK/SPEED_FACTOR"], "ModificationMode": "Divide"})
    comp["ResourceConverter"] = {
        "Type": "ResourceConverter",
        "OperationalToggle": "IsOperational",
        "From": conv_from,
        "ToStorage": "Output",
        "ToQuantity": out_qty,
        "Interval": {"BaseValue": f["interval"], "Modifiers": interval_mods},
        "CheckResourceLimits": True,
    }
    comp["ConvertEffects"] = {
        "Type": "TriggeredEffects", "Trigger": "ResourceConverter", "Location": center,
        "MediaEffects": [Inh("/BASE_SOUNDS/AudioInteriorDetail", {
            "RandomSounds": [Q(f"{snd_base}/{s}") for s in snd_put],
            "Volume": 1, "Db": -2, "Speed": 1, "SpeedVariation": 0.05})],
    }
    # bonus para as vizinhas: vanilla liga pela bateria (factory_ammo l.217-224); a prensa nao tem bateria, entao
    # usa ligada e nao queimada (sem cair enquanto espera municao)
    comp["BuffProvider"] = {"Type": "GridBuffProvider", "BuffType": "Factory", "BuffAmount": "25%", "GridDistance": 1,
                            "OperationalToggle": "BatteryStorage" if power else "CommandConsumptionToggle"}

    # ------------------------------------------------------------------ overclock
    if oc:
        comp[comment("---- overclock (factory_he.rules l.261-318 e l.1332-1354) ----")] = None
        comp.update(C.overclock_machinery(center, w, h, [], has_constant_heat=False, shot_heat=False,
                                          port_rows=range(1, h)))
        comp["Overclock_ConversionHeatProducer"] = {
            "Type": "ResourceChange", "OperationalToggle": "IsOverclocked",
            "ResourceStorage": "&~/Part/^/0/HEAT_TARGET_STORAGE", "Trigger": "Overclock_ResourceConverterProxy",
            "Amount": "(&~/OVERCLOCK/HEAT_PER_CONVERSION) * (&~/HEAT_TO_RESOURCE)"}
        comp["Overclock_ResourceConverterProxy"] = {"Type": "TriggerProxy", "ProxyToggle": "IsOverclocked",
                                                    "ComponentID": "ResourceConverter"}
        # calor/s no painel termico do editor (stat HeatGeneration)
        comp["Overclock_HeatProductionInterval"] = {"Type": "BuffableValue",
                                                    "Value": "&~/Part/Components/ResourceConverter/Interval",
                                                    "IncludeInBlueprints": True}
        comp["Overclock_HeatPerConversion"] = {"Type": "StaticValue", "Value": "&~/OVERCLOCK/HEAT_PER_CONVERSION"}
        comp["HeatGenerationValue"] = {"Type": "ValueOperation", "Operator": "Divide",
                                       "ValueOne": "Overclock_HeatPerConversion",
                                       "ValueTwo": "Overclock_HeatProductionInterval", "NaNFallbackValue": 0,
                                       "IncludeInBlueprints": "Normal"}
        comp["HeatGenerationStatProvider"] = {"Type": "StatProvider", "Stat": "HeatGeneration",
                                              "OperationalToggle": "OverclockModeToggle",
                                              "ValueFrom": "HeatGenerationValue"}

    # ------------------------------------------------------------------ graficos
    comp[comment("---- graficos (factory_he.rules l.849-959) ----")] = None
    a3 = f.get("art3d")
    if a3:
        mm = a3["machine"]
        frames, off_png, msize, moff, mint = mm["frames"], mm["off"], mm["size"], mm["offset"], mm["interval"]
    else:
        frames = ["machine_on1.png", "machine_on2.png", "machine_on3.png", "machine_on4.png"]
        off_png, msize, moff, mint = "machine_off.png", [w, 1], [0, -0.5], 0.12
    # velocidade do maquinario acompanha o bonus de fabrica e o overclock
    belt = [{"Type": "Buff", "BuffType": "Factory", "ModificationMode": "Multiply"}]
    if oc:
        belt.append({"Type": "BuffRemap", "BuffType": "Overclock", "ModificationMode": "Multiply",
                     "RemapFrom": [0, 1], "RemapTo": [1, "&~/OVERCLOCK/SPEED_FACTOR"]})
    comp["BeltSpeedFactor"] = {"Type": "BuffableValue", "Value": {"BaseValue": 1, "Modifiers": belt}}
    comp["Graphics"] = {
        "Type": "Graphics", "Location": center, "OperationalToggle": "IsOperational",
        # a animacao so corre enquanto o conversor trabalha (para com a saida cheia ou sem insumo)
        "AnimationToggle": "ResourceConverter", "AnimationSpeedFactor": "BeltSpeedFactor",
        "Floor": {"Layer": Q("floors"), "DamageLevels": [{"File": Q("floor.png"), "Size": [w, h]}]},
        "OperationalDoodad": {"Layer": Q("doodads_low"), "Offset": moff, "DamageLevels": [{
            "AnimationFiles": [Q(x) for x in frames], "Size": msize, "AnimationInterval": mint,
            "AnimationStartTime": "WhenSpawned"}]},
        "NonOperationalDoodad": {"Layer": Q("doodads_low"), "Offset": moff,
                                 "DamageLevels": [{"File": Q(off_png), "Size": msize}]},
        "Walls": {"Layer": Q("walls"), "DamageLevels": [{"File": Q(x), "Size": [w, h]} for x in WALL_DAMAGE]},
        "Roof": {"Layer": Q("roofs"), "DamageLevels": [{"File": Q("roof.png"), "NormalsFile": Q("roof_normals.png"),
                                                          "Size": [w, h]}]},
    }
    if a3 and a3.get("hull", {}).get("lights"):
        comp["Graphics"]["OperationalLighting"] = {"Layer": Q("lights_add"), "DamageLevels": [
            {"File": Q(a3["hull"]["lights"]), "Size": [w, h]}]}
    # brilho vermelho no teto com iluminacao sofisticada (factory_he l.946-959 / factory_ammo l.529-542)
    comp["Graphics"]["OperationalRoofLighting"] = {
        "Layer": Q("roof_lights_fancy"), "Offset": [0, "-29/64" if h >= 3 else "-17/64"],
        "DamageLevels": [{"File": Q("./Data/ships/common/light_blob.png"), "Size": [4, 4] if h >= 3 else [3, 3],
                          "Z": 0.5, "VertexColor": ["255*1.5", 0, 0]}]}
    comp["Blueprints"] = C.blueprint(w, h)

    # ------------------------------------------------------------------ indicadores
    # queimada / desligada escondem os de baixo (factory_processor.rules l.1142-1147, factory_he l.1265-1313)
    inds = [{"Toggle": "ScorchedToggle", "AtlasSprite": "&/INDICATORS/Scorched", "HidesIndicators": None},
            {"Toggle": "PowerToggle", "AtlasSprite": {"File": "&/INDICATORS/PowerOff", "Size": [1, 1]},
             "HidesIndicators": None}]
    for i in range(n):
        tg = splitters.get(i, f"Input{i}")
        inds.append({"Toggle": tg, "AtlasSprite": {"File": "&/INDICATORS/NoResource", "Size": [1, 1]}})
    if power:
        inds.append({"Toggle": "BatteryStorage", "AtlasSprite": {"File": "&/INDICATORS/NoPower", "Size": [1, 1]}})
    if oc:
        inds.append({"Toggle": "&~/Part/^/0/OVERCLOCK_OPERATIONAL",
                     "AtlasSprite : /INDICATORS/OverclockReset": {"Size": [1, 1]}})
    inds[0]["HidesIndicators"] = list(range(1, len(inds)))
    inds[1]["HidesIndicators"] = list(range(2, len(inds)))
    comp["Indicators"] = {"Type": "IndicatorSprites", "Location": center, "Indicators": inds}

    # ------------------------------------------------------------------ efeitos
    sz, on, off = C.effect_size(w, h)
    comp["OperationEffects"] = {"Type": "ToggleEffects", "Location": center, "Toggle": "IsOperational",
                                "ToggledOnMediaEffects": f"&/COMMON_EFFECTS/{on}",
                                "ToggledOffMediaEffects": f"&/COMMON_EFFECTS/{off}"}
    comp["OperationSoundLoop"] = {
        "Type": "ContinuousEffects", "Location": center, "OperationalToggle": "IsOperational",
        "MaxMediaEffectsZoom": 4,
        "MediaEffects": [Inh("/BASE_SOUNDS/AudioInterior", {
            "Sound": Q(f"{snd_base}/{snd_idle}"), "Volume": 1, "MaxConcurrentVolume": 1, "Speed": 1,
            "MaxConcurrent": 1})]}
    comp["ScorchedTrigger"] = {"Type": "ToggleTrigger", "Toggle": "ScorchedToggle", "TriggerWhenOn": False,
                               "TriggerWhenOff": True}
    ck = f.get("cookoff")
    if ck:
        # cook-off da fabrica, escalado pelo enchimento da saida (factory_he.rules l.1182-1263); a explosao das
        # pilhas guardadas (DeathHitEffects do recurso) vem por cima, como no vanilla
        comp["ScorchedEffects"] = {"Type": "TriggeredEffects", "Trigger": "ScorchedTrigger",
                                   "Location": "&~/Part/Components/DestroyedEffects/Location",
                                   "MediaEffects": "&~/Part/Components/DestroyedEffects_UnderConstruction/MediaEffects",
                                   "HitEffects": "&~/Part/Components/DestroyedEffects/HitEffects",
                                   "FactorHitEffectsWith": "Output", "IncludeWhenUnderConstruction": False}
        comp["DestroyedEffects"] = {"Type": "DeathEffects", "OperationalToggle": "ScorchedToggle",
                                    "FactorHitEffectsWith": "Output", "Location": center,
                                    "IncludeWhenUnderConstruction": False, "HitEffects": _cookoff_hits(ck)}
        # sem escala pelo estoque: evita o crash durante a construcao (comentario vanilla)
        comp["DestroyedEffects_UnderConstruction"] = {"Type": "DeathEffects",
                                                      "Location": "&~/Part/Components/DestroyedEffects/Location",
                                                      "MediaEffects": f"&/COMMON_EFFECTS/{sz}PartDestroyed"}
    else:
        comp["ScorchedEffects"] = {"Type": "TriggeredEffects", "Trigger": "ScorchedTrigger",
                                   "Location": "&../DestroyedEffects/Location",
                                   "MediaEffects": f"&/COMMON_EFFECTS/{sz}PartScorched"}
        comp["DestroyedEffects"] = {"Type": "DeathEffects", "MediaEffects": f"&/COMMON_EFFECTS/{sz}PartDestroyed",
                                    "Location": center}
    part["Components : ^/0/Components"] = comp

    # ------------------------------------------------------------------ stats (factory_ammo.rules l.919-935)
    rc = "&~/Part/Components/ResourceConverter"
    stats = {"BSFactoryOutput": f"({rc}/ToQuantity) / ({rc}/Interval/BaseValue)"}
    if out_res in own_stack:
        rdir = out_res.split(".")[-1]
        stack_ref = f"&<../../resources/{rdir}/{rdir}.rules>/MaxStackSize"
    else:
        stack_ref = f"&<{RES_FILE[out_res]}>/MaxStackSize"
    stats["AmmoCapacity"] = (f"(&~/Part/Components/Output/GridRect/2) * (&~/Part/Components/Output/GridRect/3) * "
                             f"({stack_ref})")
    use_ids = []
    for i, (res, _q) in enumerate(inputs):
        sp = splitters.get(i)
        if sp:
            per_item = (f"(&~/Part/Components/{sp}/FromQuantity) / (&~/Part/Components/{sp}/ToQuantity) / "
                        f"({rc}/ToQuantity)")
            per_sec = (f"(&~/Part/Components/{sp}/FromQuantity) / (&~/Part/Components/{sp}/ToQuantity) / "
                       f"({rc}/Interval/BaseValue)")
        else:
            per_item = f"({rc}/From/{i}/Quantity) / ({rc}/ToQuantity)"
            per_sec = f"({rc}/From/{i}/Quantity) / ({rc}/Interval/BaseValue)"
        stats[f"Input{i}PerAmmo"] = per_item
        stats[f"Input{i}PerSecond"] = per_sec
        sid = use_stat(res)
        stats[sid] = [f"&../Input{i}PerAmmo", f"&../Input{i}PerSecond"]
        use_ids.append(sid)
    if power:
        pw = f"{rc}/From/{n}/Quantity" + ("/BaseValue" if oc else "")
        stats["PowerPerAmmo"] = f"({pw}) / ({rc}/ToQuantity) / 1000"
        stats["PowerPerSecond"] = f"({pw}) / ({rc}/Interval/BaseValue) / 1000"
        stats["AmmoPowerUsage"] = ["&../PowerPerAmmo", "&../PowerPerSecond"]
        stats["PowerCapacity"] = "(&~/Part/Components/BatteryStorage/MaxResources) / 1000"
    stats["FactoryBuff"] = "(&~/Part/Components/BuffProvider/BuffAmount) * 100"
    if power:
        # barras de energia/tripulacao recomendadas do editor (stat_widgets.rules l.16, l.44)
        stats["RecPower"] = "&PowerPerSecond"
        stats["RecCrew"] = "(&RecPower) * 4"
    part["Stats"] = stats

    top = {}
    if oc:
        o = {"HEAT_PER_CONVERSION": oc["heat_per_conversion"], "SPEED_FACTOR": pct(oc["speed_factor"])}
        if power:
            o["POWER_USE_FACTOR"] = pct(oc["power_use_factor"])
        top["OVERCLOCK"] = o
        top["HEAT_TO_RESOURCE"] = C.HEAT_TO_RESOURCE
        # tooltip "Overclocked" (factory_ammo.rules l.937-953)
        sec = {"BSFactoryOutput": "(&~/Part/Stats/BSFactoryOutput) * (&~/OVERCLOCK/SPEED_FACTOR)"}
        for sid in use_ids:
            sec[sid] = [f"(&~/Part/Stats/{sid}/0)", f"(&~/Part/Stats/{sid}/1) * (&~/OVERCLOCK/SPEED_FACTOR)"]
        if power:
            sec["POWER_PER_AMMO"] = "(&~/Part/Stats/AmmoPowerUsage/0) * (&~/OVERCLOCK/POWER_USE_FACTOR)"
            sec["POWER_PER_SECOND"] = ("(&~/Part/Stats/AmmoPowerUsage/1) * (&~/OVERCLOCK/POWER_USE_FACTOR) * "
                                       "(&~/OVERCLOCK/SPEED_FACTOR)")
            sec["AmmoPowerUsage"] = ["&../POWER_PER_AMMO", "&../POWER_PER_SECOND"]
        sec["AMMO_PER_CONVERSION"] = f"({rc}/ToQuantity)"
        sec["HEAT_PER_AMMO"] = "(&~/OVERCLOCK/HEAT_PER_CONVERSION) / (&AMMO_PER_CONVERSION)"
        sec["HEAT_PER_SECOND"] = (f"(&~/OVERCLOCK/HEAT_PER_CONVERSION) / ({rc}/Interval/BaseValue) * "
                                  f"(&~/OVERCLOCK/SPEED_FACTOR)")
        sec["AmmoHeatGeneration"] = ["&../HEAT_PER_AMMO", "&../HEAT_PER_SECOND"]
        part["SecondaryToolTip"] = {"TitleKey": Q("StatCategories/Overclocked"),
                                    "DescriptionKey": Q(f"Parts/{f['key']}OverclockDesc"), "Stats": sec}
    # arquivo base vanilla: 2x2 = base_part_terran (factory_ammo), 3x3 = base_med_part_terran (factory_he)
    base = f.get("base_part") or ("base_med_part_terran" if he else "base_part_terran")
    top["Part : " + C.base_part_path(w, h, bool(oc), base=base)] = part
    if oc and power:
        top["MODIFIERS"] = {"OVERCLOCK_LERP": {"Type": "Buff", "BuffType": "Overclock", "ModificationMode": "Lerp"}}
    return top, {"size": [w, h]}
