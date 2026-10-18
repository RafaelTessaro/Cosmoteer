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
    size = f.get("size") or [n + 1, 2]
    he = list(size) == [3, 3] and n <= 2
    if he:
        # layout do factory_he vanilla: maquinario em cima e no centro, entradas nas laterais, saida embaixo
        w, h = 3, 3
        in_cells = [[0, 1], [2, 1]][:n] if n == 2 else [[0, 1]]
        out_rect = [0, 2, 3, 1]
    else:
        w, h = n + 1, 2
        in_cells = [[i, 1] for i in range(n)]
        out_rect = [n, 1, 1, 1]
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
    a3 = f.get("art3d")
    if a3:
        mm = a3["machine"]
        frames, off_png, msize, moff, mint = mm["frames"], mm["off"], mm["size"], mm["offset"], mm["interval"]
    else:
        frames = ["machine_on1.png", "machine_on2.png", "machine_on3.png", "machine_on4.png"]
        off_png, msize, moff, mint = "machine_off.png", [w, 1], [0, -0.5], 0.12
    comp["Graphics"] = {
        "Type": "Graphics", "Location": [w / 2, h / 2], "OperationalToggle": "IsOperational",
        "Floor": {"Layer": Q("floors"), "DamageLevels": [{"File": Q("floor.png"), "Size": [w, h]}]},
        "OperationalDoodad": {"Layer": Q("doodads_low"), "Offset": moff, "DamageLevels": [{
            "AnimationFiles": [Q(x) for x in frames], "Size": msize, "AnimationInterval": mint}]},
        "NonOperationalDoodad": {"Layer": Q("doodads_low"), "Offset": moff,
                                 "DamageLevels": [{"File": Q(off_png), "Size": msize}]},
        "Walls": {"Layer": Q("walls"), "DamageLevels": [{"File": Q("walls.png"), "Size": [w, h]}]},
        "Roof": {"Layer": Q("roofs"), "DamageLevels": [{"File": Q("roof.png"), "NormalsFile": Q("roof_normals.png"),
                                                          "Size": [w, h]}]},
    }
    if a3 and a3.get("hull", {}).get("lights"):
        comp["Graphics"]["OperationalLighting"] = {"Layer": Q("lights_add"), "DamageLevels": [
            {"File": Q(a3["hull"]["lights"]), "Size": [w, h]}]}
    comp["Blueprints"] = C.blueprint(w, h)
    inds = [{"Toggle": "PowerToggle", "AtlasSprite": {"File": "&/INDICATORS/PowerOff", "Size": [1, 1]},
             "HidesIndicators": list(range(1, n + 1 + (1 if power else 0)))}]
    for i in range(n):
        tg = f"Input{i}Splitter" if f"Input{i}Splitter" in comp else f"Input{i}"
        inds.append({"Toggle": tg, "AtlasSprite": {"File": "&/INDICATORS/NoResource", "Size": [1, 1]}})
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
