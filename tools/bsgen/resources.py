"""Gerador dos 12 recursos do Bullet Strike 2.0 (carregadores HE/AP/SAP/AC/FRAG, celulas de plasma e PEM, cargas de
missil, ogiva nuclear e projetil do railgun; dono: WP01).

Base: resources/bullet/bullet.rules e missile_part_nuke.rules (0.30.x): MaxStackSize, BuyPrice, Rarity Ammunition,
AmmoDropRates. Sem HitResponse/StatusResponse (mudou de nome entre 0.30.4 e 0.30.5; o SW:ACD tambem omite).
Sem DeathHitEffects: o cook-off fica na peca, escalado pelo estoque (logistics.recurso_cookoff = off); so com
'por_pilha' volta o ExplosiveDamage por pilha de SPEC.resources[].death_hit_effects.per_stack_mode.
"""

from rules_dsl import Q


def build_resource(r):
    """r = um dict de bs_data.RESOURCES."""
    n = r["max_stack"]
    top = {
        "ID": r["id"],
        "NameKey": Q(f"Resource/{r['key']}"),
        "PluralNameKey": Q(f"Resource/{r['key']}Plural"),
        "DescriptionKey": Q(f"Resource/{r['key']}Desc"),
        "BuyPrice": int(r["price"]),
        "SellPrice": r.get("sell_price") or "(&BuyPrice) / 2",
        "MaxPerNugget": int(r.get("max_per_nugget") or 1),
        "MaxStackSize": int(n),
        "FlexGridPriorityKey": Q(f"flex_grid_{r['id']}"),
        "FlexGridDefaultPriority": 1,
        "DropRates": r.get("drop_rates") or "&<./Data/resources/resources.rules>/AmmoDropRates",
        "Rarity": r.get("rarity") or "Ammunition",
        "Icon": {"Texture": {"File": Q("icon.png"), "MipLevels": "max"}, "Size": [64, 64]},
        "Overlay": {"Texture": {"File": Q("overlay.png"), "SampleMode": "Linear", "MipLevels": "max"}, "Size": [1, 1]},
    }
    dhe = r.get("death_hit_effects")
    if dhe:
        # so com logistics.recurso_cookoff = por_pilha (bs_data poe a chave)
        e = dict(dhe)
        tot = e.get("TotalDamage")
        if isinstance(tot, dict):
            e["TotalDamage"] = dict(tot)
        if isinstance(e.get("Filter"), dict):
            e["Filter"] = dict(e["Filter"])
        top["DeathHitEffects"] = [e]
        top["DeathMediaEffects"] = "&/COMMON_EFFECTS/MedPartDestroyed"
    top["NuggetSprites"] = [{"File": Q("nugget.png"), "NormalsFile": Q("nugget_normals.png"), "Size": [1, 1],
                             "Offset": [0.25, 0], "UVRotation": 1}]
    top["StackSprites"] = [{"File": Q(f"stack_{i}.png"), "Size": [1, 1]} for i in range(1, n + 1)]
    top["StackReceiveMediaEffects"] = "&/COMMON_EFFECTS/AmmoDeliver"
    top["StackPickupMediaEffects"] = "&/COMMON_EFFECTS/AmmoPickup"
    top["NuggetPickupMediaEffects"] = "&/COMMON_EFFECTS/NuggetPickup"
    return top
