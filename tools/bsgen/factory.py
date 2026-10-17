"""Gerador das fabricas (prensas de carregadores / municao especial) do Bullet Strike.

Padroes vanilla: factory_ammo.rules (grades de entrada/saida, conversor, bateria, bonus de fabrica
adjacente) e factory_processor.rules (conversor tirando varias unidades direto da grade de entrada,
com ToggleOnResources = quantidade da receita).
Layout: fileira de cima = maquinario (bloqueado para a tripulacao); fileira de baixo = grades de
entrada (uma coluna por insumo) e, na ultima coluna, a grade de saida.
"""

from rules_dsl import Q, Inh
from bsgen import common as C

RES_STACK = {  # MaxStackSize dos recursos vanilla (resources/*.rules)
    "bullet": 20, "sulfur": 5, "steel": 40, "coil": 40, "coil2": 40, "tristeel": 40, "diamond": 5,
    "enriched_uranium": 10, "uranium": 5, "carbon": 5, "copper": 5, "gold": 5, "iron": 5, "tritanium": 5,
    "hyperium": 20, "processor": 5, "missile_part_he": 10, "missile_part_emp": 10, "missile_part_nuke": 10,
}

RES_FILE = {r: f"./Data/resources/{r}/{r}.rules" for r in RES_STACK}


def build_factory(f, own_stack):
    """own_stack: dict resource_id -> MaxStackSize dos recursos do proprio mod."""
    inputs = f["inputs"]
    out_res, out_qty = f["output"]
    n = len(inputs)
    w = n + 1
    h = 2
    stack = dict(RES_STACK)
    stack.update(own_stack)
    power = f.get("power")  # bateria por ciclo (None = sem energia)

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
        "TypeCategories": ["provides_ammo"] + [f"uses_{r}" for r, _ in inputs if r in ("sulfur", "coil", "coil2")] +
                          (["uses_power"] if power else []),
        "ReceivableBuffs : ^/0/ReceivableBuffs": ["Factory"],
        "BlockedTravelCells": [[x, 0] for x in range(w)],
        "ForceManhattanPathInPart": True,
        "AllowedDoorLocations": [[-1, 1], [w, 1]] + [[x, 2] for x in range(w)],
        "EditorIcon": {"Texture": {"File": Q("icon.png"), "SampleMode": "Linear"},
                       "Size": [64, round(64 * h / w, 2)] if w >= h else [round(64 * w / h, 2), 64]},
    }

    comp = {}
    op_toggles = ["PowerToggle", "NonJunkToggle", "ScorchedToggle"] + [f"Input{i}" for i in range(n)]
    if power:
        op_toggles.append("BatteryStorage")
    comp["IsOperational"] = {"Type": "MultiToggle", "Toggles": op_toggles, "Mode": "All"}
    comp["NonJunkToggle"] = {"Type": "JunkToggle", "OnWhenJunk": False}
    comp["CommandConsumptionToggle"] = {"Type": "MultiToggle", "Toggles": ["PowerToggle", "ScorchedToggle"],
                                        "Mode": "All"}
    comp["PowerToggle"] = {"Type": "UIToggle", "ToggleID": Q("on_off"), "Default": 1, "RequiresCommand": False}
    comp["ScorchedToggle"] = {"Type": "StatusToggle", "StatusType": "cosmoteer.scorched", "MinStatusValue": 1,
                              "Invert": True}
    comp["CommandConsumer"] = {"Type": "CommandConsumer", "OperationalToggle": "CommandConsumptionToggle",
                               "CommandPoints": f.get("cp", 1)}

    conv_from = []
    for i, (res, qty) in enumerate(inputs):
        cap_tiles = 1 if qty <= stack[res] else 2
        rect = [i, 1, 1, 1] if cap_tiles == 1 else [i, 0, 1, 2]
        comp[f"Input{i}"] = {
            "Type": "TypedResourceGrid", "ResourceType": res, "GridRect": rect,
            "Layer": Q("doodads_low"), "SpriteInset": ["8/64", "6/64", "8/64", "9/64"],
            "ToggleOnResources": qty, "ToggleOffResources": qty - 1,
            "AllowExternalPickupAndDelivery": True,
        }
        comp[f"Input{i}Consumer"] = {"Type": "TypedResourceGridConsumer", "ResourceType": res,
                                     "Storage": f"Input{i}", "DefaultPriority": "&/PRIORITIES/Factory_Supply",
                                     "OperationalToggle": "CommandConsumptionToggle",
                                     "ConsumptionToggleButtonOffset": [0, -0.4]}
        conv_from.append({"Storage": f"Input{i}", "Quantity": qty})
        if cap_tiles == 2:
            part["BlockedTravelCells"] = [c for c in part["BlockedTravelCells"] if c != [i, 0]]
    comp["Output"] = {"Type": "TypedResourceGrid", "ResourceType": out_res, "GridRect": [n, 1, 1, 1],
                      "Layer": Q("doodads_low"), "SpriteInset": ["8/64", "6/64", "8/64", "9/64"],
                      "SuppliesResources": True, "SupplyToggleButtonOffset": [0, -0.4],
                      "InitToMaxResources": 0, "AllowExternalPickupAndDelivery": True}
    if power:
        comp["BatteryStorage"] = {"Type": "ResourceStorage", "ResourceType": "battery",
                                  "MaxResources": max(2000, power * 4),
                                  "ReceiveResourceMediaEffects": "&/COMMON_EFFECTS/PowerDeliver"}
        comp["BatteryConsumer"] = {"Type": "ResourceConsumer", "ResourceType": "battery", "Storage": "BatteryStorage",
                                   "DefaultPriority": "&/PRIORITIES/Factory_Supply",
                                   "ResupplyThreshold": max(500, power), "OperationalToggle": "CommandConsumptionToggle"}
        conv_from.append({"Storage": "BatteryStorage", "Quantity": power, "MinQuantityForConversion": 1})
    comp["ResourceConverter"] = {
        "Type": "ResourceConverter",
        "OperationalToggle": "IsOperational",
        "From": conv_from,
        "ToStorage": "Output",
        "ToQuantity": out_qty,
        "Interval": {"BaseValue": f["interval"],
                     "Modifiers": [{"Type": "Buff", "BuffType": "Factory", "ModificationMode": "Divide"}]},
        "CheckResourceLimits": True,
    }
    comp["ConvertEffects"] = {
        "Type": "TriggeredEffects", "Trigger": "ResourceConverter", "Location": [w / 2, h / 2],
        "MediaEffects": [Inh("/BASE_SOUNDS/AudioInteriorDetail", {
            "RandomSounds": [Q(f"./Data/ships/terran/factory_ammo/sounds/cannon_ammo_factory_putdown_0{i}.wav")
                             for i in range(1, 8)],
            "Volume": 1, "Db": -2, "Speed": 1, "SpeedVariation": 0.05})],
    }
    comp["BuffProvider"] = {"Type": "GridBuffProvider", "BuffType": "Factory", "BuffAmount": "25%", "GridDistance": 1,
                            "OperationalToggle": "BatteryStorage" if power else "IsOperational"}
    comp["Graphics"] = {
        "Type": "Graphics", "Location": [w / 2, h / 2], "OperationalToggle": "IsOperational",
        "Floor": {"Layer": Q("floors"), "DamageLevels": [{"File": Q("floor.png"), "Size": [w, h]}]},
        "OperationalDoodad": {"Layer": Q("doodads_low"), "Offset": [0, -0.5], "DamageLevels": [{
            "AnimationFiles": [Q("machine_on1.png"), Q("machine_on2.png"), Q("machine_on3.png"), Q("machine_on4.png")],
            "Size": [w, 1], "AnimationInterval": 0.12}]},
        "NonOperationalDoodad": {"Layer": Q("doodads_low"), "Offset": [0, -0.5],
                                 "DamageLevels": [{"File": Q("machine_off.png"), "Size": [w, 1]}]},
        "Walls": {"Layer": Q("walls"), "DamageLevels": [{"File": Q("walls.png"), "Size": [w, h]}]},
        "Roof": {"Layer": Q("roofs"), "DamageLevels": [{"File": Q("roof.png"), "NormalsFile": Q("roof_normals.png"),
                                                          "Size": [w, h]}]},
    }
    comp["Blueprints"] = C.blueprint(w, h)
    inds = [{"Toggle": "PowerToggle", "AtlasSprite": {"File": "&/INDICATORS/PowerOff", "Size": [1, 1]},
             "HidesIndicators": list(range(1, n + 1 + (1 if power else 0)))}]
    for i in range(n):
        inds.append({"Toggle": f"Input{i}", "AtlasSprite": {"File": "&/INDICATORS/NoResource", "Size": [1, 1]}})
    if power:
        inds.append({"Toggle": "BatteryStorage", "AtlasSprite": {"File": "&/INDICATORS/NoPower", "Size": [1, 1]}})
    comp["Indicators"] = {"Type": "IndicatorSprites", "Location": [w / 2, h / 2], "Indicators": inds}
    sz, on, off = C.effect_size(w, h)
    comp["OperationEffects"] = {"Type": "ToggleEffects", "Location": [w / 2, h / 2], "Toggle": "IsOperational",
                                "ToggledOnMediaEffects": f"&/COMMON_EFFECTS/{on}",
                                "ToggledOffMediaEffects": f"&/COMMON_EFFECTS/{off}"}
    comp["DestroyedEffects"] = {"Type": "DeathEffects", "MediaEffects": f"&/COMMON_EFFECTS/{sz}PartDestroyed",
                                "Location": [w / 2, h / 2]}
    part["Components : ^/0/Components"] = comp

    stats = {"BSFactoryOutput": f"(&~/Part/Components/ResourceConverter/ToQuantity) / "
                                f"(&~/Part/Components/ResourceConverter/Interval/BaseValue)",
             "FactoryBuff": "(&~/Part/Components/BuffProvider/BuffAmount) * 100"}
    if power:
        stats["PowerPerSecond"] = (f"(&~/Part/Components/ResourceConverter/From/{n}/Quantity) / "
                                   f"(&~/Part/Components/ResourceConverter/Interval/BaseValue) / 1000")
        stats["PowerCapacity"] = "(&~/Part/Components/BatteryStorage/MaxResources) / 1000"
    part["Stats"] = stats
    top = {"Part : " + C.base_part_path(w, h, False): part}
    return top, {"size": [w, h]}
