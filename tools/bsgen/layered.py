"""Ligacao nas regras das pecas "layered" (spec 2.0 art_assets.render_kinds.layered.bsgen; dono WP10).

A arte vem de art3d/<pasta>/meta.json gravado por tools/blender/render_layered.py: cada camada tem a camada do jogo
(game_layer), o retangulo na peca (rect [x, y, w, h] em quadros, origem no canto de cima-esquerda, +y para baixo),
as copias (rects), os arquivos (files) e as normais, e um destes conjuntos: levels N | frames N | variants [..] |
situations [..] (ou nenhum = sprite unico). Este modulo transforma uma camada em componentes das regras (dicts do
tools/rules_dsl.py), com Location = centro do rect (coordenadas da peca) e Size = tamanho do rect:

    graphics(meta, nome, ...)         -> componente(s) Graphics / ValueSprites / ResourceSprites / ToggledBlendSprites
                                         (uma Graphics por copia quando a camada tem varios 'rects')
    components(meta, nome, cid, ...)  -> {cid: comp} ou {cid0: comp, cid1: comp, ...}
    base_graphics(meta, ...)          -> Graphics com Floor / Walls / Roof da peca (piso, moldura, teto + normais)
    editor_icon / blueprints          -> nomes do icone e da planta da peca
    stand_in(pid, size, camadas)      -> meta "de mentira" no MESMO formato (arte provisoria: make_art.layered_art
                                         desenha os PNGs; so com BS_ARTE_PROCEDURAL=1 ou quando a arte falta)

Qual componente sai (kind):
    frames                       -> "animation": Graphics com AnimationFiles (+ NormalsAnimationFiles na mesma ordem);
                                    a ordem padrao e a de meta['tranco'][nome]['AnimationFiles_order'] quando existe
                                    (quadros do tranco: o ultimo = repouso; AnimationStartTime MinValue +
                                    ClampAnimation, como o barrel dos canhoes de convés) e a dos arquivos nos outros
    levels                       -> "value": ValueSprites (ValueFrom=...) ou, com ResourceStorage=..., "resource":
                                    ResourceSprites; blank_first=True poe o quadro vazio na frente (vanilla
                                    railgun_accelerator.rules:597-610)
    variants                     -> "graphics" com variant=<v> (um sprite); kind="value"/"resource" usa as variantes
                                    como niveis (digitos 0..9 com Modulus)
    situations                   -> "blend": ToggledBlendSprites (so a reserva da esteira usa; SituationToggles=[...])
    sprite unico                 -> "graphics"

Os campos de cada "slot" da Graphics seguem o corpus do jogo (vanilla + SW:ACD, tools/schema_check.py): um campo que o
slot nao aceita (ex.: ClampAnimation no OperationalRoofDoodad, normais no OperationalLighting) levanta ValueError em
vez de ir para o arquivo. Campos de topo (OperationalToggle, AnimationToggle, ResetAnimationTrigger, ChainedTo,
Rotation, ValueFrom, ResourceStorage, Modulus, Round, HasZeroResourceSprite...) entram por **fields, crus (str =
identificador/referencia, Q(...) = texto entre aspas).

prefix: caminho relativo do arquivo das regras ate a pasta publicada da arte (ex.: "../bs_paiol_comum/" quando o
.rules do paiol fica em parts/bs_paiol_cartuchos_1x1/ e a arte compartilhada em parts/bs_paiol_comum/).
"""

import art3d as A3
from rules_dsl import Q

GAME_LAYERS = ["structure", "floors", "turrets", "doodads_low", "walls_stencil", "external_walls", "walls", "doors",
               "weapons", "doodads_high", "lights_add", "fire", "roofs", "roof_doodads", "roof_turrets",
               "roof_lights_fancy"]

# slot padrao da Graphics por camada do jogo (as outras, inclusive "walls": OperationalDoodad com Layer explicito;
# a moldura walls.png da peca vai no slot Walls pelo base_graphics)
SLOT_BY_LAYER = {"floors": "Floor", "roofs": "Roof", "lights_add": "OperationalLighting",
                 "roof_doodads": "OperationalRoofDoodad", "roof_lights_fancy": "OperationalRoofLighting"}

# campos aceitos em cada item de DamageLevels, por slot (corpus vanilla 0.30 + SW:ACD; schema_check)
_DOODAD = {"file", "normalsfile", "size", "offset", "animationfiles", "normalsanimationfiles", "animationinterval",
           "animationstarttime", "clampanimation", "vertexcolor", "z"}
SLOT_FIELDS = {
    "Floor": {"file", "normalsfile", "size", "offset", "animationfiles", "animationinterval"},
    "Walls": {"file", "normalsfile", "size", "offset"},
    "WallsStencil": {"file", "normalsfile", "size"},
    "Roof": {"file", "normalsfile", "size", "offset"},
    "OperationalDoodad": _DOODAD,
    "NonOperationalDoodad": {"file", "normalsfile", "size", "offset", "animationfiles", "animationinterval",
                             "clampanimation"},
    "ToggleOnDoodad": _DOODAD - {"normalsfile", "vertexcolor", "z"},
    "ToggleOffDoodad": _DOODAD - {"vertexcolor", "z"},
    "OperationalRoofDoodad": {"file", "normalsfile", "size", "offset", "animationfiles", "normalsanimationfiles",
                              "animationinterval", "animationstarttime"},
    "NonOperationalRoofDoodad": {"file", "normalsfile", "size"},
    "OperationalLighting": {"file", "size", "offset", "animationfiles", "animationinterval", "animationstarttime",
                            "vertexcolor"},
    "OperationalRoofLighting": {"file", "size", "animationfiles", "animationinterval", "vertexcolor", "z"},
}
# valores de AnimationStartTime aceitos por slot (corpus)
START_VALUES = {"OperationalDoodad": {"MinValue", "WhenSpawned", "Zero"}, "ToggleOnDoodad": {"WhenSpawned", "Zero"},
                "ToggleOffDoodad": {"WhenSpawned", "Zero"}, "OperationalLighting": {"WhenSpawned", "Zero"},
                "OperationalRoofDoodad": {"WhenSpawned", "Zero"}}
# situacoes das pecas que se emendam (vanilla heat_pipe_blend_sprites.rules:1-38)
SITUATION_CODES = {"hub": "0000", "stub": "0010", "straight": "1010", "corner": "0110", "3way": "1110",
                   "4way": "1111"}


# ============================================================================ leitura do meta
def part(meta, sub=None):
    """Meta de UMA peca (pasta compartilhada: meta['parts'][sub])."""
    return A3.sub_meta(meta, sub)


def layer(meta, name, sub=None):
    m = part(meta, sub)
    lay = m.get("layers") or {}
    if name not in lay:
        raise KeyError(f"{m.get('id')}: camada {name!r} nao existe (ha {sorted(lay)})")
    return lay[name]


def kind_of(ent):
    for k in ("frames", "levels", "variants", "situations"):
        if k in ent:
            return k
    return "single"


def rects(ent):
    return [list(r) for r in (ent.get("rects") or [ent["rect"]])]


def _n(v):
    v = round(float(v), 6)
    return int(v) if v == int(v) else v


def location(rect):
    """Centro do retangulo [x, y, w, h] (coordenadas da peca, +y para baixo) = Location das regras."""
    x, y, w, h = rect
    return [_n(x + w / 2), _n(y + h / 2)]


def size(rect):
    return [_n(rect[2]), _n(rect[3])]


def sprites(meta, name, sub=None, order="auto"):
    """[(arquivo, normais | None)] da camada na ordem pedida: "auto" (a do tranco quando o meta tem
    tranco.<camada>.AnimationFiles_order, senao a dos arquivos), "files" ou uma lista de arquivos."""
    ent = layer(meta, name, sub)
    files = list(ent["files"])
    nrm = list(ent.get("normals") or [])
    nmap = {}
    for f in files:
        nf = f[:-4] + "_normals.png"
        nmap[f] = nf if nf in nrm else None
    if order == "auto":
        tr = (part(meta, sub).get("tranco") or {}).get(name) or {}
        order = tr.get("AnimationFiles_order") or files
    elif order == "files":
        order = files
    bad = [f for f in order if f not in nmap]
    if bad:
        raise KeyError(f"{part(meta, sub).get('id')}/{name}: ordem cita arquivos fora da camada: {bad[:4]}")
    return [(f, nmap[f]) for f in order]


def has_tranco(meta, name, sub=None):
    return bool((part(meta, sub).get("tranco") or {}).get(name))


def editor_icon(meta, sub=None, variant=None):
    """Nome do icone do editor da peca (pasta compartilhada: o da variante pedida, ex.: a familia do paiol)."""
    m = part(meta, sub)
    ic = m.get("icon")
    if isinstance(ic, list):
        if variant is None:
            return ic[0]
        hit = [f for f in ic if f"_{variant}_" in f or f.endswith(f"_{variant}.png") or f == f"icon_{variant}.png"]
        if len(hit) != 1:
            raise KeyError(f"{m.get('id')}: icone da variante {variant!r} ambiguo/ausente em {ic}")
        return hit[0]
    return ic


def blueprints(meta, sub=None):
    return part(meta, sub).get("blueprints")


# ============================================================================ componentes
def _slot_for(gl, slot):
    if slot:
        return slot
    return SLOT_BY_LAYER.get(gl, "OperationalDoodad")


def _check(slot, item, what):
    allowed = SLOT_FIELDS.get(slot)
    if allowed is None:
        raise ValueError(f"{what}: slot {slot!r} desconhecido (use {sorted(SLOT_FIELDS)})")
    bad = sorted(k for k in item if k.lower() not in allowed)
    if bad:
        raise ValueError(f"{what}: o slot {slot} nao aceita {bad} (corpus do jogo; troque o slot, ex.: "
                         f"OperationalDoodad com Layer explicito)")
    st = item.get("AnimationStartTime")
    if st is not None and str(st) not in START_VALUES.get(slot, {str(st)}):
        raise ValueError(f"{what}: AnimationStartTime {st} nao vale no slot {slot} ({sorted(START_VALUES[slot])})")


def _level_items(pairs, sz, prefix, normals, blank_first, value):
    out = [{}] if blank_first else []
    for f, nf in pairs:
        it = {"File": Q(prefix + f)}
        if normals and nf and not value:
            it["NormalsFile"] = Q(prefix + nf)
        it["Size"] = sz
        out.append(it)
    return out


def graphics(meta, name, sub=None, *, prefix="", variant=None, kind=None, slot=None, copy=None, location_=None,
             size_=None, interval=None, start=None, clamp=None, order="auto", blank_first=False, off_slot=None,
             normals=True, layer_override=None, **fields):
    """Componente(s) das regras para a camada `name` (ver o cabecalho do modulo).

    variant: a variante (sprite unico) das camadas com variants; kind: "graphics" | "animation" | "value" |
    "resource" | "blend" (padrao pelo conjunto da camada); slot: slot da Graphics (padrao pela camada do jogo:
    SLOT_BY_LAYER, senao OperationalDoodad); off_slot: repete o sprite (1o quadro) num 2o slot, ex.
    "NonOperationalDoodad"; copy: indice de UMA copia (rects) - sem ele a camada com varias copias devolve uma
    lista; location_/size_: Location/Size no lugar do centro/tamanho do rect (ex.: FX da Fita no painel livre do
    paiol); interval/start/clamp: AnimationInterval / AnimationStartTime / ClampAnimation (quadros); order: ordem
    dos quadros ("auto" | "files" | lista); blank_first: quadro vazio antes do 1o nivel; normals=False omite as
    normais; layer_override: outra camada do jogo no lugar da do meta; **fields: campos de topo do componente."""
    ent = layer(meta, name, sub)
    pid = part(meta, sub).get("id")
    what = f"{pid}/{name}"
    gl = layer_override or ent["game_layer"]
    if gl not in GAME_LAYERS:
        raise ValueError(f"{what}: camada do jogo {gl!r} desconhecida")
    ks = kind_of(ent)
    if kind is None:
        kind = {"frames": "animation", "levels": "resource" if "ResourceStorage" in fields else "value",
                "situations": "blend"}.get(ks, "graphics")
    if kind == "value" and "ResourceStorage" in fields:
        kind = "resource"
    rs = rects(ent)
    if copy is not None:
        rs = [rs[copy]]
    comps = []
    for r in rs:
        loc = list(location_) if location_ is not None else location(r)
        sz = list(size_) if size_ is not None else size(r)
        comps.append(_one(meta, name, sub, ent, kind, ks, gl, loc, sz, what, prefix=prefix, variant=variant,
                          slot=slot, interval=interval, start=start, clamp=clamp, order=order,
                          blank_first=blank_first, off_slot=off_slot, normals=normals, fields=fields))
    return comps[0] if len(comps) == 1 else comps


def _one(meta, name, sub, ent, kind, ks, gl, loc, sz, what, *, prefix, variant, slot, interval, start, clamp,
         order, blank_first, off_slot, normals, fields):
    if kind in ("value", "resource"):
        if ks == "variants" and order == "auto":
            order = "files"
        pairs = sprites(meta, name, sub, order)
        key = "ValueFrom" if kind == "value" else "ResourceStorage"
        if key not in fields:
            raise ValueError(f"{what}: {kind} sem {key}= (de onde vem o nivel)")
        comp = {"Type": "ValueSprites" if kind == "value" else "ResourceSprites", "Location": loc,
                key: fields[key], "Layer": Q(gl)}
        comp.update({k: v for k, v in fields.items() if k != key})
        comp["ResourceLevels"] = _level_items(pairs, sz, prefix, normals, blank_first, kind == "value")
        return comp
    if kind == "blend":
        if "SituationToggles" not in fields:
            raise ValueError(f"{what}: ToggledBlendSprites sem SituationToggles=[cima, direita, baixo, esquerda]")
        sits = ent.get("situations") or []
        amb = []
        for s, f in zip(sits, ent["files"]):
            code = SITUATION_CODES.get(s, s)
            it = {"SituationCode": Q(code)}
            if code == "0000":
                it["AllowRotation"] = False
            it["DamageLevelSprites"] = [{"File": Q(prefix + f)}]
            amb.append(it)
        comp = {"Type": "ToggledBlendSprites", "Location": loc}
        comp.update(fields)
        comp["Layer"] = Q(gl)
        comp["AmbiguousSprites"] = amb
        return comp
    sl = _slot_for(gl, slot)
    if kind == "animation":
        pairs = sprites(meta, name, sub, order)
        tr = has_tranco(meta, name, sub) and order == "auto"
        item = {"AnimationFiles": [Q(prefix + f) for f, _ in pairs]}
        nfs = [nf for _f, nf in pairs]
        if normals and all(nfs) and nfs:
            item["NormalsAnimationFiles"] = [Q(prefix + nf) for nf in nfs]
        item["Size"] = sz
        iv = interval if interval is not None else ent.get("interval")
        if iv is not None:
            item["AnimationInterval"] = iv
        st = start if start is not None else ("MinValue" if tr else None)
        if st is not None:
            item["AnimationStartTime"] = st
        cl = clamp if clamp is not None else (True if tr else None)
        if cl is not None:
            item["ClampAnimation"] = bool(cl)
        _check(sl, item, what)
        comp = {"Type": "Graphics", "Location": loc}
        comp.update(fields)
        comp[sl] = {"Layer": Q(gl), "DamageLevels": [item]}
        if off_slot:
            f0, n0 = pairs[-1] if tr else pairs[0]       # repouso: o ultimo quadro do tranco / o 1o dos outros
            comp[off_slot] = _static_slot(off_slot, gl, f0, n0, sz, prefix, normals, what)
        return comp
    if kind != "graphics":
        raise ValueError(f"{what}: kind {kind!r} desconhecido")
    if ks in ("variants", "situations"):
        vals = list(ent.get("variants") or ent.get("situations"))
        if variant is None:
            raise ValueError(f"{what}: camada com variantes {vals}: passe variant=")
        if variant not in vals:
            raise KeyError(f"{what}: variante {variant!r} nao existe ({vals})")
        f = ent["files"][vals.index(variant)]
    elif ks in ("frames", "levels"):
        idx = 0 if variant is None else int(variant) - 1
        f = ent["files"][idx]
    else:
        f = ent["files"][0]
    nf = f[:-4] + "_normals.png"
    nf = nf if nf in (ent.get("normals") or []) else None
    comp = {"Type": "Graphics", "Location": loc}
    comp.update(fields)
    comp[sl] = _static_slot(sl, gl, f, nf, sz, prefix, normals, what)
    if off_slot:
        comp[off_slot] = _static_slot(off_slot, gl, f, nf, sz, prefix, normals, what)
    return comp


def _static_slot(sl, gl, f, nf, sz, prefix, normals, what):
    item = {"File": Q(prefix + f)}
    if normals and nf and "normalsfile" in SLOT_FIELDS.get(sl, ()):
        item["NormalsFile"] = Q(prefix + nf)
    item["Size"] = sz
    _check(sl, item, what)
    return {"Layer": Q(gl), "DamageLevels": [item]}


def components(meta, name, cid, sub=None, **kw):
    """{cid: componente} (ou {cid0: ..., cid1: ...} quando a camada tem varias copias)."""
    c = graphics(meta, name, sub, **kw)
    if isinstance(c, list):
        return {f"{cid}{i}": x for i, x in enumerate(c)}
    return {cid: c}


def base_graphics(meta, sub=None, *, prefix="", variant=None, floor="floor", roof="roof", walls=True,
                  walls_damage=None, location_=None, **fields):
    """Graphics da casca da peca: Floor (camada `floor`), Walls (meta['walls'] ou a lista walls_damage = niveis de
    dano, ex. [walls.png, walls_33.png, walls_66.png] quando o make_art.layered_art(wall_damage=True) os grava) e
    Roof (camada `roof`, com normais; variant = a variante do teto, ex. a familia do paiol). Location = centro."""
    m = part(meta, sub)
    W, H = m["size"]
    comp = {"Type": "Graphics", "Location": list(location_) if location_ is not None else [_n(W / 2), _n(H / 2)]}
    comp.update(fields)
    lay = m.get("layers") or {}
    if floor and floor in lay:
        fl = graphics(meta, floor, sub, prefix=prefix, slot="Floor", copy=0)
        comp["Floor"] = fl["Floor"]
    if walls and m.get("walls"):
        names = list(walls_damage) if walls_damage else [m["walls"]]
        comp["Walls"] = {"Layer": Q("walls"), "DamageLevels": [{"File": Q(prefix + n), "Size": [W, H]}
                                                                 for n in names]}
    if roof and roof in lay:
        rf = graphics(meta, roof, sub, prefix=prefix, slot="Roof", copy=0,
                      variant=variant if kind_of(lay[roof]) == "variants" else None)
        comp["Roof"] = rf["Roof"]
    return comp


def wall_damage_names(meta, sub=None):
    """[walls, walls_33, walls_66] da peca (os dois ultimos gravados por make_art.layered_art(wall_damage=True))."""
    w = part(meta, sub).get("walls")
    if not w:
        return []
    return [w, w[:-4] + "_33.png", w[:-4] + "_66.png"]


# ============================================================================ arte provisoria
def stand_in(pid, size_wh, layers, walls="closed", icon=True, blueprints_=True, sub=None):
    """Meta no formato do render_layered (version 1, kind layered) para uma peca SEM arte: os nomes dos arquivos
    seguem o mesmo esquema (file com {i} / {v}); make_art.layered_art(..., meta) desenha PNGs provisorios. layers:
    [{name, game_layer, rect?, levels|frames|variants|situations?, normals?, file?, interval?, blend?}]."""
    W, H = size_wh
    lay = {}
    files = []
    for L in layers:
        rect = list(L.get("rect") or [0, 0, W, H])
        f = L.get("file", L["name"] + ("{i}.png" if ("levels" in L or "frames" in L) else
                                       "_{v}.png" if ("variants" in L or "situations" in L) else ".png"))
        if "levels" in L or "frames" in L:
            n = int(L.get("levels") or L.get("frames"))
            names = [f.format(i=k) for k in range(1, n + 1)]
        elif "variants" in L or "situations" in L:
            names = [f.format(v=v) for v in (L.get("variants") or L.get("situations"))]
        else:
            names = [f]
        nrm = [n[:-4] + "_normals.png" for n in names] if L.get("normals") else None
        ent = {"game_layer": L["game_layer"], "rect": rect, "files": names, "normals": nrm}
        for k in ("levels", "frames", "variants", "situations", "interval", "blend", "rects"):
            if k in L:
                ent[k] = L[k]
        ent["opaque"] = L["game_layer"] == "floors"
        ent["emission_only"] = L["game_layer"] == "lights_add"
        ent["islands"] = True
        lay[L["name"]] = ent
        files += names + (nrm or [])
    meta = {"version": 1, "kind": "layered", "id": pid, "size": [W, H], "layers": lay,
            "walls": "walls.png" if walls not in (None, "none") else None, "stand_in": True}
    if meta["walls"]:
        files.append("walls.png")
    if icon:
        meta["icon"] = "icon.png"
        files.append("icon.png")
    if blueprints_:
        meta["blueprints"] = "blueprints.png"
        files.append("blueprints.png")
    if sub:
        meta["sub"] = sub
    meta["files"] = sorted(set(files))
    return meta
