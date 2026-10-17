"""Gerador dos recursos (carregadores, celulas de plasma, projeteis nucleares).

Base: resources/bullet/bullet.rules e missile_part_nuke.rules (0.30.x). Sem HitResponse/StatusResponse
(mudou de nome entre 0.30.4 e 0.30.5; o SW:ACD tambem omite).
"""

from rules_dsl import Q


def build_resource(r):
    n = r["max_stack"]
    top = {
        "ID": r["id"],
        "NameKey": Q(f"Resource/{r['key']}"),
        "PluralNameKey": Q(f"Resource/{r['key']}Plural"),
        "DescriptionKey": Q(f"Resource/{r['key']}Desc"),
        "BuyPrice": r["price"],
        "SellPrice": "(&BuyPrice) / 2",
        "MaxPerNugget": 1,
        "MaxStackSize": n,
        "FlexGridPriorityKey": Q(f"flex_grid_{r['id']}"),
        "FlexGridDefaultPriority": 1,
        "DropRates": "&<./Data/resources/resources.rules>/AmmoDropRates",
        "Rarity": "Ammunition",
        "Icon": {"Texture": {"File": Q("icon.png"), "MipLevels": "max"}, "Size": [64, 64]},
        "Overlay": {"Texture": {"File": Q("overlay.png"), "SampleMode": "Linear", "MipLevels": "max"}, "Size": [1, 1]},
    }
    cook = r.get("cookoff")
    if cook:
        radius, dmg = cook
        top["DeathHitEffects"] = [{
            "Type": "ExplosiveDamage",
            "TotalDamage": {"BaseValue": dmg, "EffectScaleExponent": 1},
            "Radius": radius,
            "Delay": 0.05,
            "StatusType": "cosmoteer.fire",
            "StatusChancePerNDamage": "50%",
            "StatusValue": 1,
            "StatusValueType": "Interpolated",
            "NDamage": 1000,
            "CrewKillChance": "10%",
            "Filter": {"OperationalHealth": True, "StructuralHealth": False, "Friendlies": True},
        }]
        top["DeathMediaEffects"] = "&/COMMON_EFFECTS/" + r.get("death_fx", "MedPartDestroyed")
    top["NuggetSprites"] = [{"File": Q("nugget.png"), "NormalsFile": Q("nugget_normals.png"), "Size": [1, 1],
                             "Offset": [0.25, 0], "UVRotation": 1}]
    top["StackSprites"] = [{"File": Q(f"stack_{i}.png"), "Size": [1, 1]} for i in range(1, n + 1)]
    top["StackReceiveMediaEffects"] = "&/COMMON_EFFECTS/AmmoDeliver"
    top["StackPickupMediaEffects"] = "&/COMMON_EFFECTS/AmmoPickup"
    top["NuggetPickupMediaEffects"] = "&/COMMON_EFFECTS/NuggetPickup"
    return top
