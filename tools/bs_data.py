"""Dados do Bullet Strike 2.0 (camada de dados do gerador; dono: WP01).

Os NUMEROS ficam em tools/spec/SPEC_2.0.json (fonte de verdade), dividido por tools/spec2_split.py em
tools/spec/bullet_strike_spec.json, bullet_strike_missiles.json e bullet_strike_art2.json. Este modulo:
  1) le os 3 JSON + o override opcional tools/spec/bullet_strike_switches.json (WP14a/WP14b);
  2) resolve os switches: switch('grupo.nome') na ordem CLI > env > bullet_strike_switches.json > padrao do spec;
  3) aplica as TRANSFORMACOES CENTRAIS (a0, a, b, c, d, d2, e; f = perfil vanilla nao existe na 2.0) num lugar so,
     para os modulos receberem os numeros prontos;
  4) monta GUNS, DEFENSES, SHOTS (canhoes e defesas), PEM, RESOURCES, FACTORIES, LIMITS e as techs (filtradas
     pelas pecas realmente escritas: career_techs(written) / buildbattle_techs(written) / bb_whitelist(written)).

Os modulos de conteudo (bsgen.guns, bsgen.ciws, bsgen.factory, bsgen.logistics, bsgen.intake, bsgen.pem,
bsgen.railgun, bs_data_missiles, ...) recebem este modulo como DATA nos ganchos do tools/build_mod.py.

CLI e variaveis: o build_mod passa a CLI por BS__CLI_SWITCHES (JSON) e a variante por BS__VARIANTE; quem importa
este modulo direto pode usar BS_SWITCHES='a.b=v,c.d=w', as env de SPEC.switches.*.env (BS_LOGISTICA, BS_RAIL...),
BS_ART_<NOME> para o grupo art, BS_SWITCHES_FILE (outro bullet_strike_switches.json) e BS_VARIANTE (fita|semfita).
"""

import copy
import importlib
import json
import math
import os
import re
import sys
import unicodedata

from rules_dsl import Q
import art3d as A3
from bsgen import common as C
from bsgen import plasma_fx as PFX

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_DIR = os.path.join(HERE, "spec")


def _load(name):
    with open(os.path.join(SPEC_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


SPEC = _load("bullet_strike_spec.json")
MSPEC = _load("bullet_strike_missiles.json")
ART2 = _load("bullet_strike_art2.json")["art_assets"]

VERSION = SPEC["version"]
AUTHOR = C.AUTHOR

# ============================================================================= avisos
WARNINGS = []


def warn(msg):
    """Aviso do gerador (impresso uma vez; o build_mod repete a lista no fim)."""
    if msg not in WARNINGS:
        WARNINGS.append(msg)
        print(f"(aviso) {msg}", file=sys.stderr)


# ============================================================================= variante (perfil do build)
# SPEC.build_2_0.variants: fita (BulletStrike/, rafaeltessaro.bullet_strike) e semfita (testes/BulletStrike_SemFita/,
# rafaeltessaro.bullet_strike_semfita, forca logistics.transport = tripulacao)
VARIANTS = SPEC["build_2_0"]["variants"]
VARIANT = (os.environ.get("BS__VARIANTE") or os.environ.get("BS_VARIANTE") or "fita").strip()
if VARIANT not in VARIANTS:
    raise SystemExit(f"variante desconhecida {VARIANT!r} (use: {', '.join(VARIANTS)})")
PROFILE = dict(VARIANTS[VARIANT])
PROFILE["variant"] = VARIANT
MOD_ID = PROFILE["mod_id"]
MOD_NAME = PROFILE["name"]
C.set_profile(MOD_ID, MOD_NAME)

# ============================================================================= switches
SWITCH_DEFS = {}
for _g, _d in SPEC["switches"].items():
    if isinstance(_d, dict):
        for _n, _e in _d.items():
            if isinstance(_e, dict) and "default" in _e:
                SWITCH_DEFS[f"{_g}.{_n}"] = _e

# apelidos de valor (nomes ingleses aceitos, SPEC.switches.where)
VALUE_ALIASES = {
    "logistics.transport": {"teleport": "teleporte", "network": "rede", "twin": "gemea", "network_twin": "gemea",
                            "crew": "tripulacao", "crew_only": "tripulacao"},
}
# variantes que NENHUM dos dois builds usa (ADDENDUM G11): o switch avisa e usa o 'safe'. Um modulo que implementar
# uma delas declara VARIANTS = {'chave': (valores, ...)} no topo (API >= 2) e o build_mod chama implement_variants().
DEFERRED_VARIANTS = {
    "logistics.paiol_seletor": {"nenhum"},
    "logistics.fita_embutida": {"botao"},
    "logistics.devolucao_arma": {"on", "auto"},
    "logistics.paiol_contador": {True},
    "rail.power_mode": {"A"},
    "rail.charge_wave": {"rede"},
}


def implement_variants(mapping, owner="?"):
    """Chamado pelo build_mod para cada modulo com API >= 2 que declara VARIANTS: tira os valores da lista de adiados."""
    for key, vals in (mapping or {}).items():
        if key not in SWITCH_DEFS:
            raise ValueError(f"{owner}: VARIANTS cita switch desconhecido {key}")
        for v in (vals if isinstance(vals, (list, tuple, set)) else [vals]):
            DEFERRED_VARIANTS.get(key, set()).discard(_parse_value(key, v, f"{owner}.VARIANTS"))


def _fold(s):
    """minusculas sem acento (para casar 'Mae-do-Ouro' com 'Mãe-do-Ouro')."""
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower().strip()


def _canon(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _parse_value(key, raw, source):
    """Converte o valor cru (texto da CLI/env ou valor do JSON) pelo tipo do padrao e confere contra 'values'."""
    e = SWITCH_DEFS[key]
    d = e["default"]
    v = raw
    if isinstance(raw, str):
        r = raw.strip()
        r = VALUE_ALIASES.get(key, {}).get(r.lower(), r)
        if isinstance(d, bool):
            if r.lower() in ("1", "true", "sim", "yes", "on", "verdadeiro"):
                v = True
            elif r.lower() in ("0", "false", "nao", "não", "no", "off", "falso"):
                v = False
            else:
                raise SystemExit(f"switch {key}: valor {raw!r} ({source}) nao e booleano (true/false)")
        elif isinstance(d, int):
            try:
                v = int(r)
            except ValueError:
                v = r
        elif isinstance(d, float):
            try:
                v = float(r)
            except ValueError:
                v = r
        else:
            v = r
    vals = e.get("values")
    if isinstance(vals, (dict, list)):
        allowed = [k for k in (vals.keys() if isinstance(vals, dict) else vals)]
        by_fold = {_fold(_canon(k)): k for k in allowed}
        hit = by_fold.get(_fold(_canon(v)))
        if hit is None:
            raise SystemExit(f"switch {key}: valor {raw!r} ({source}) invalido; validos: "
                             f"{', '.join(_canon(k) for k in allowed)}")
        if isinstance(v, str) and isinstance(hit, str) and not isinstance(d, (bool, int, float)):
            v = hit   # grafia canonica do spec (acentos)
    return v


def _switch_file():
    p = os.environ.get("BS_SWITCHES_FILE") or os.path.join(SPEC_DIR, "bullet_strike_switches.json")
    if not os.path.isfile(p):
        return p, {}
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    return p, {k: v for k, v in data.items() if not k.startswith("_")}


SWITCH_FILE, _FILE_DATA = _switch_file()
# chaves do arquivo que nao sao switches (ex.: guns.he_further_factor_medido, guns.ap_further_factor_medido)
SWITCH_EXTRA = {k: v for k, v in _FILE_DATA.items() if k not in SWITCH_DEFS}
_FILE_SW = {k: v for k, v in _FILE_DATA.items() if k in SWITCH_DEFS}


def _env_switches():
    out = {}
    for key, e in SWITCH_DEFS.items():
        names = []
        env = e.get("env")
        if isinstance(env, str) and re.fullmatch(r"BS_[A-Z0-9_]+", env.strip()):
            names.append(env.strip())
        grp, name = key.split(".", 1)
        if grp == "art":
            names.append("BS_ART_" + name.upper())
        for nm in names:
            if os.environ.get(nm, "") != "":
                out[key] = (os.environ[nm], f"env {nm}")
    if os.environ.get("BS_LOGISTICS", "") != "" and "logistics.transport" not in out:
        warn("BS_LOGISTICS e obsoleto: use BS_LOGISTICA (ou --logistica / --switch logistics.transport=...)")
        out["logistics.transport"] = (os.environ["BS_LOGISTICS"], "env BS_LOGISTICS (obsoleto)")
    for item in filter(None, (x.strip() for x in os.environ.get("BS_SWITCHES", "").split(","))):
        k, sep, v = item.partition("=")
        k = k.strip()
        if not sep or k not in SWITCH_DEFS:
            raise SystemExit(f"BS_SWITCHES: item invalido {item!r} (formato chave=valor; chave de SPEC.switches)")
        out[k] = (v.strip(), "env BS_SWITCHES")
    return out


def _cli_switches():
    raw = os.environ.get("BS__CLI_SWITCHES", "")
    if not raw:
        return {}
    data = json.loads(raw)
    for k in data:
        if k not in SWITCH_DEFS:
            raise SystemExit(f"--switch: chave desconhecida {k!r} (chaves de SPEC.switches)")
    return {k: (v, "cli") for k, v in data.items()}


_CLI = _cli_switches()
_ENV = _env_switches()


def _raw(key):
    """(valor, origem) sem as regras de transporte/adiamento."""
    forced = (PROFILE.get("forces") or {}).get(key)
    if forced is not None:
        for src in (_CLI, _ENV):
            if key in src and _parse_value(key, src[key][0], src[key][1]) != forced:
                warn(f"variante {VARIANT} forca {key}={forced} (ignorado {src[key][1]}={src[key][0]})")
        return forced, f"variante {VARIANT}"
    if key in _CLI:
        return _parse_value(key, *_CLI[key]), _CLI[key][1]
    if key in _ENV:
        return _parse_value(key, *_ENV[key]), _ENV[key][1]
    if key in _FILE_SW:
        return _parse_value(key, _FILE_SW[key], os.path.basename(SWITCH_FILE)), os.path.basename(SWITCH_FILE)
    return SWITCH_DEFS[key]["default"], "padrao"


def belt_net_ok():
    """A esteira fisica (rede/gemea) so existe com o bsgen.belt_net (WP15, reserva) com API >= 2."""
    return C.content_module("bsgen.belt_net") is not None


def switch(key):
    """Valor efetivo do switch 'grupo.nome' (CLI > env > bullet_strike_switches.json > SPEC.switches.*.default).

    Regras: rede/gemea sem o bsgen.belt_net -> 'tripulacao' com aviso (J2R3-19); switch com applies_to fora do
    transporte atual -> padrao do spec com aviso; variante adiada (ADDENDUM G11) -> 'safe' com aviso;
    balance.perfil = vanilla -> erro (perfil jogo base nao existe na 2.0)."""
    if key not in SWITCH_DEFS:
        raise KeyError(f"switch desconhecido: {key}")
    e = SWITCH_DEFS[key]
    v, src = _raw(key)
    if key == "logistics.transport" and v in ("rede", "gemea") and not belt_net_ok():
        warn(f"logistics.transport={v} ({src}) precisa do bsgen.belt_net (WP15, esteira fisica, pulado): usando "
             f"'tripulacao'")
        v = "tripulacao"
    if key == "balance.perfil" and v == "vanilla":
        raise SystemExit("perfil jogo base nao existe na 2.0 (resposta 3 = nao)")
    at = e.get("applies_to")
    if at and key != "logistics.transport":
        t = switch("logistics.transport")
        if t not in at:
            if src != "padrao" and v != e["default"]:
                warn(f"switch {key}={_canon(v)} ({src}) ignorado: so vale com logistics.transport em {at} (atual: {t})")
            return e["default"]
    if v in DEFERRED_VARIANTS.get(key, ()):
        safe = e.get("safe", e["default"])
        if src != "padrao" or v != safe:
            warn(f"variante {_canon(v)} de {key} nao implementada nesta versao; usando {_canon(safe)}")
        v = safe
    return v


def switch_source(key):
    return _raw(key)[1]


def switch_report():
    """[(chave, valor efetivo, origem)] para o log do build."""
    return [(k, switch(k), switch_source(k)) for k in sorted(SWITCH_DEFS)]


def switch_extra(key, default=None):
    """Dado extra do bullet_strike_switches.json que nao e switch (ex.: 'guns.he_further_factor_medido')."""
    return SWITCH_EXTRA.get(key, default)


def transport():
    return switch("logistics.transport")


def belt_skip_down(g):
    """Colunas da fileira de tras SEM porta termica (porta da esteira): so com transport em (rede, gemea);
    teleporte e tripulacao nao tem porta de esteira -> ()."""
    if transport() in ("rede", "gemea"):
        return tuple((g.get("belt") or {}).get("thermal_skip_down") or ())
    return ()


# ============================================================================= tabelas fixas (dado salvo)
AMMO_INDEX = {"he": 0, "ap": 1, "sap": 2, "ac": 3, "frag": 4}
CELL_INDEX = {"plasma": 0, "pem": 1}
MISSILE_INDEX = {"he": 0, "cluster": 1, "emp": 2, "nuclear": 3}
TOGGLES = SPEC["toggles"]


def _short(pid):
    return pid.split(".", 1)[1]


def _key(short):
    return "BS" + "".join(p.capitalize() for p in short.split("_")[1:])


def _rhu(x):
    """Inteiro pelo round() do Python (o mesmo do gerador do spec: 0,5 x 137 = 68, round half even)."""
    return int(round(x))


RAIL_ENABLED = bool(switch("rail.enabled"))
# perfil (f): 'vanilla' nao existe na 2.0 (resposta 3 = nao) -> para aqui com a mensagem
switch("balance.perfil")
# switches pedidos explicitamente (CLI/env/arquivo) sao conferidos ja na carga (valor, transporte, applies_to); os
# de variante adiavel so quando o modulo dono perguntar (ele pode declarar VARIANTS antes)
for _k in sorted(set(_CLI) | set(_ENV) | set(_FILE_SW)):
    if _k not in DEFERRED_VARIANTS:
        switch(_k)

# ============================================================================= dicas de arte e efeitos (Fase B)
# estilo da torre, cano, acento de cor, efeitos e geometria (arte procedural, so com BS_ARTE_PROCEDURAL=1, e
# os efeitos de boca/som de cada arma). Chave = parte do ID curto (primeira que bater).
ART_HINTS = [
    ("nuke", {"style": "nuke", "barrel": "howitzer", "accent": "aphe", "fx": "huge"}),
    ("naval_406", {"style": "heavy_naval", "barrel": "heavy", "accent": "aphe", "fx": "huge"}),
    ("naval_155", {"style": "heavy_naval", "barrel": "heavy", "accent": "aphe", "fx": "deck"}),
    ("naval", {"style": "naval", "barrel": "brake", "accent": "ammo", "fx": "large"}),
    ("plasma_heavy", {"style": "plasma", "barrel": "plasma", "accent": "plasma", "fx": "plasma_big"}),
    ("plasma", {"style": "plasma", "barrel": "plasma", "accent": "plasma", "fx": "plasma"}),
    ("ciws", {"style": "ciws", "barrel": "gatling", "accent": "defense", "fx": "flak"}),
    ("flak_heavy", {"style": "aa_heavy", "barrel": "plain", "accent": "flak", "fx": "flak"}),
    ("flak", {"style": "flak", "barrel": "plain", "accent": "flak", "fx": "flak"}),
    ("rotary", {"style": "minigun", "barrel": "gatling", "accent": "ammo", "fx": "mg_heavy"}),
    ("minigun", {"style": "minigun", "barrel": "gatling", "accent": "ammo", "fx": "mg"}),
    ("quad", {"style": "flak", "barrel": "fins", "accent": "ammo", "fx": "mg"}),
    ("autocannon", {"style": "autocannon", "barrel": "brake", "accent": "ammo", "fx": "med"}),
    ("hmg", {"style": "lmg", "barrel": "fins", "accent": "ammo", "fx": "mg"}),
    ("lmg", {"style": "lmg", "barrel": "fins", "accent": "ammo", "fx": "mg"}),
    ("pem", {"style": "plasma", "barrel": "fins", "accent": "emp", "fx": "med"}),
]


def art_hint(short):
    for key, h in ART_HINTS:
        if key in short:
            return dict(h)
    return {"style": "autocannon", "barrel": "brake", "accent": "ammo", "fx": "med"}


T = "./Data/ships/terran"
FX = {
    # particulas de boca (buckets "Upper" para nao ficarem sob o teto) + som de disparo
    "mg": {"particles": [f"{T}/chaingun/particles/chaingun_shoot.rules", f"{T}/chaingun/particles/chaingun_shoot_flash.rules"],
           "sound": [f"{T}/chaingun/sounds/chain_gun_shot_0{i}.wav" for i in (1, 2, 3, 4, 5)],
           "volume": 0.55, "max_concurrent": 40, "shake": 0, "offset": -0.3},
    "mg_heavy": {"particles": [f"{T}/chaingun/particles/chaingun_shoot.rules", f"{T}/chaingun/particles/chaingun_shoot_flash.rules",
                               f"{T}/chaingun/particles/chaingun_shoot_smoke.rules"],
                 "sound": [f"{T}/chaingun/sounds/chain_gun_shot_01.wav", f"{T}/chaingun/sounds/chain_gun_shot_02.wav"],
                 "volume": 0.8, "max_concurrent": 40, "shake": 0.02, "offset": -0.3},
    "med": {"particles": [f"{T}/cannon_deck/particles/cannon_shoot_deck_flash.rules", f"{T}/chaingun/particles/chaingun_shoot.rules"],
            "sound": f"{T}/cannon_med/sounds/cannon_med_shot.wav", "volume": 0.8, "max_concurrent": 20, "shake": 0.02,
            "offset": -0.2},
    "large": {"particles": [f"{T}/cannon_deck/particles/cannon_shoot_deck.rules", f"{T}/cannon_deck/particles/cannon_shoot_deck_flash.rules",
                            f"{T}/cannon_deck/particles/cannon_smoke_deck.rules"],
              "sound": f"{T}/cannon_large/sounds/cannon_large_shot.wav",
              "sound_oc": [f"{T}/cannon_large/sounds/large_cannon_overclocked_shot_0{i}.wav" for i in (1, 2, 3)],
              "volume": 1.0, "shake": 0.06, "offset": -0.9},
    "deck": {"particles": [f"{T}/cannon_deck/particles/cannon_shoot_deck.rules", f"{T}/cannon_deck/particles/cannon_shoot_deck_flash.rules",
                           f"{T}/cannon_deck/particles/cannon_shoot_deck_flare.rules", f"{T}/cannon_deck/particles/cannon_smoke_deck.rules"],
             "sound": f"{T}/cannon_deck/sounds/cannon_deck_shot.wav",
             "sound_oc": f"{T}/cannon_deck/sounds/deck_cannon_overclocked_shot.wav", "volume": 1.0, "shake": 0.1,
             "offset": -0.7},
    "huge": {"particles": [f"{T}/cannon_deck/particles/cannon_shoot_deck.rules", f"{T}/cannon_deck/particles/cannon_shoot_deck_flash.rules",
                           f"{T}/cannon_deck/particles/cannon_shoot_deck_flare.rules", f"{T}/cannon_deck/particles/cannon_smoke_deck.rules"],
             "sound": f"{T}/cannon_deck/sounds/deck_cannon_overclocked_shot.wav", "volume": 1.0, "shake": 0.16,
             "shake_time": 0.9, "offset": -0.5},
    # plasma: descarga ciano propria (bsgen/plasma_fx.py); particles_oc = descarga do overclock. Caminhos relativos a
    # parts/<id>/
    "plasma": {"particles": PFX.muzzle_paths("gatling", False), "particles_oc": PFX.muzzle_paths("gatling", True),
               "sound": [f"{T}/laser_blaster_small/sounds/laser_blaster_shot_0{i}.wav" for i in (1, 2, 3, 4)],
               "sound_oc": [f"{T}/laser_blaster_small/sounds/laser_overclocked_shot_0{i}.wav" for i in (1, 2, 3)],
               "volume": 0.7, "max_concurrent": 30, "shake": 0.01, "offset": 0},
    "plasma_big": {"particles": PFX.muzzle_paths("heavy", False), "particles_oc": PFX.muzzle_paths("heavy", True),
                   "sound": [f"{T}/laser_blaster_large/sounds/heavy_laser_shot_0{i}.wav" for i in (1, 2, 3, 4)],
                   "sound_oc": [f"{T}/laser_blaster_large/sounds/heavy_laser_overclocked_shot_0{i}.wav" for i in (1, 2, 3)],
                   "volume": 0.9, "max_concurrent": 12, "shake": 0.08, "offset": -0.05},
    "flak": {"particles": [f"{T}/flak_cannon_large/particles/flak_cannon_shoot_flash_large.rules"],
             "sound": [f"{T}/flak_cannon_large/sounds/flak_cannon_shot_0{i}.wav" for i in (1, 2, 3, 4)],
             "volume": 0.35, "max_concurrent": 30, "shake": 0, "offset": 0},
}
# lancadores (WP06 / bs_data_missiles le daqui)
FX["launch_s"] = {
    "flash": [f"{T}/missile_launcher/particles/missile_launcher_shoot_flash.rules"],
    "backblast": [f"{T}/chaingun/particles/chaingun_shoot_smoke.rules"],
    "sound": [f"{T}/missile_launcher/sounds/launcher_launch_0{i}.wav" for i in (1, 2, 3)],
    "volume": 0.5, "max_concurrent": 12, "shake": 0,
    "reload": [f"{T}/missile_launcher/sounds/launcher_reload_0{i}.wav" for i in (1, 2, 3)],
    "ready": [f"{T}/missile_launcher/sounds/launcher_ready_0{i}.wav" for i in (1, 2, 3)],
}
FX["launch_m"] = dict(FX["launch_s"], volume=0.6, max_concurrent=16, shake=0.01,
                      sound_heavy=[f"{T}/missile_launcher/nuke/sounds/launcher_launch_nuke.wav"])
FX["launch_l"] = dict(FX["launch_m"], volume=0.7, shake=0.02, thump=0.15,
                      backblast=[f"{T}/cannon_deck/particles/cannon_smoke_deck.rules"])

# cores por municao: paleta 2.0 (SPEC.art_assets.palette, AC em carmim) com o plasma da Fase B
PAL = ART2["palette"]
_PLASMA_COL = {"glow": [0, 255, 220], "tracer": [120, 255, 255], "core": [225, 255, 255]}


def ammo_color(key, part):
    """Cor 'glow' / 'tracer' / 'core' da municao (he, ap, sap, ac, frag, plasma)."""
    if key == "plasma":
        return list(_PLASMA_COL[part])
    p = PAL.get(key) or PAL["he"]
    return list(p.get(part) or PAL["he"][part])


# Visual do projetil por ARMA (calibre) da Fase B: trocar a municao so troca a cor (R1). O WP03 (caliber_fx.annotate)
# troca pelo visual 2.0; sem ele estas chaves continuam valendo (Boitata e Curupira dependem de plasma_fx/trail).
VIS = {
    "bs_lmg": {"look": "tracer", "wh": [3.0, 0.26], "core": [1.0, 0.12], "glow": [6, 2]},
    "bs_minigun": {"look": "tracer", "wh": [3.0, 0.26], "core": [1.0, 0.12], "glow": [6, 2]},
    "bs_hmg": {"look": "tracer", "wh": [3.5, 0.32], "core": [1.2, 0.15], "glow": [7, 2.5]},
    "bs_quad_hmg": {"look": "tracer", "wh": [3.5, 0.32], "core": [1.2, 0.15], "glow": [7, 2.5]},
    "bs_autocannon_20": {"look": "tracer", "wh": [4.0, 0.40], "core": [1.4, 0.18], "glow": [8, 3], "trail": "med"},
    "bs_rotary_30": {"look": "tracer", "wh": [5.0, 0.48], "core": [1.8, 0.22], "glow": [9, 3.5]},
    "bs_plasma_gatling": {"look": "energy", "wh": [2.0, 0.5], "core": [0.9, 0.22], "glow": [6, 3], "plasma": "gatling"},
    "bs_naval_76": {"look": "large", "size": 0.7, "glow": [12, 6], "glow_off": -1, "trail": "large"},
    "bs_naval_155": {"look": "large", "size": 1.1, "glow": [18, 9], "glow_off": -1.5, "z": 0.5, "trail": "deck"},
    "bs_naval_406": {"look": "large", "size": 1.35, "glow": [22, 11], "glow_off": -1.8, "z": 0.5, "trail": "deck"},
    "bs_nuke_howitzer": {"look": "large", "size": 1.35, "glow": [22, 11], "glow_off": -1.8, "z": 0.5, "trail": "deck"},
    "bs_plasma_heavy": {"look": "energy", "wh": [2.8, 1.12], "core": [1.4, 0.5], "glow": [12, 6], "glow_off": -1,
                        "plasma": "heavy"},
}
# a partir desta cadencia (tiros/s, ja com o overclock) o impacto usa efeitos leves
FAST_RATE = 5
# categorias de projetil do modo defesa da metralhadora hibrida (padrao pd_shot / point_defense)
PD_CATEGORIES = ["missile", "mine", "bullet"]


def _caliber(dmg):
    if dmg < 450:
        return "mg"
    if dmg < 2500:
        return "med"
    if dmg < 6000:
        return "large"
    return "deck"


# ============================================================================= arte 3D
PLACEHOLDERS = []   # pecas/recursos sem arte 3D (arte procedural); o spec2_check lista e o WP14b exige zero


def _meta(art_dir, size=None, pid=None, what=""):
    """Meta de art3d/<art_dir> se existir (e, com size, se o tamanho bater: J2R3-17); senao None e placeholder.
    Sem o meta e sem BS_ARTE_PROCEDURAL=1, A3.require para o build (regressao de arte nao passa despercebida)."""
    meta = A3.load_meta(art_dir)
    if meta is None:
        A3.require(art_dir, None)
        PLACEHOLDERS.append(f"{what or pid}: art3d/{art_dir} ausente (arte procedural)")
        return None
    if size is not None and meta.get("size") is not None and list(meta["size"]) != list(size):
        warn(f"{pid}: art3d/{art_dir} tem tamanho {meta['size']} e a peca {list(size)}: arte procedural")
        PLACEHOLDERS.append(f"{what or pid}: art3d/{art_dir} de outro tamanho (arte procedural)")
        return None
    if pid and meta.get("id") and meta["id"] != pid and not meta.get("shared"):
        raise ValueError(f"art3d/{art_dir}: meta.id {meta['id']} nao e {pid}")
    return meta


# ============================================================================= transformacoes centrais
TRANSFORMS = []   # registro do que foi aplicado (log do build e conferencia)
_AP_TABLE = SPEC["switches"]["guns"]["ap_further_factor"]["values"]


def _ap_class(pen):
    if pen <= 8:
        return "pen_le_8"
    if pen < 20:
        return "pen_8_20"
    return "pen_ge_20"


def _he_factor(short):
    """(a0) fator do HE/AC: numero (0.5 = o spec) ou 'medido' (guns.he_further_factor_medido do switches.json:
    {padrao, Mapinguari}; o Mapinguari usa o seu, as outras armas o 'padrao' - R4)."""
    v = switch("guns.he_further_factor")
    if v == "medido":
        med = switch_extra("guns.he_further_factor_medido")
        if not isinstance(med, dict) or "padrao" not in med:
            raise SystemExit("guns.he_further_factor = medido exige 'guns.he_further_factor_medido' = "
                             "{padrao, Mapinguari} em bullet_strike_switches.json")
        return float(med["Mapinguari"] if short == "bs_naval_406" and "Mapinguari" in med else med["padrao"])
    return float(v)


def _ap_factor(m, sap=False):
    """(a) fator por peca adicional do AP (pela faixa de penetracao) e do SAP."""
    mode = switch("guns.ap_further_factor")
    cls = "sap" if sap else _ap_class(m["penetration"])
    if mode == "linear":
        return m.get("further_factor") if m.get("further_factor") is not None else _AP_TABLE["linear"][cls]
    if mode == "sem_reducao":
        return _AP_TABLE["sem_reducao"][cls]
    med = switch_extra("guns.ap_further_factor_medido")
    if not isinstance(med, dict):
        raise SystemExit("guns.ap_further_factor = medido exige 'guns.ap_further_factor_medido' = "
                         "{pen_le_8, pen_8_20, pen_ge_20, sap} em bullet_strike_switches.json")
    f = med.get(cls)
    if f is None or cls == "pen_le_8":
        f = _AP_TABLE["sem_reducao"][cls]
    if f > _AP_TABLE["linear"][cls] + 1e-9:
        raise SystemExit(f"guns.ap_further_factor_medido[{cls}] = {f} acima do linear ({_AP_TABLE['linear'][cls]})")
    return f


def _transform_weapon(w):
    """(a0) e (a) num weapons[] (copia): pen_damage_per_further_part de HE/AC (pen > 0), AP e SAP."""
    short = _short(w["id"])
    for m in w["ammo_modes"]:
        k = m["key"]
        if k in ("he", "ac") and (m.get("penetration") or 0) > 0:
            f = _he_factor(short)
            m["pen_damage_per_further_part"] = _rhu(f * m["direct"])
            m["further_factor_applied"] = f
        elif k == "ap":
            f = _ap_factor(m)
            m["pen_damage_per_further_part"] = _rhu(m["direct"] * f)
            m["further_factor_applied"] = f
        elif k == "sap":
            f = _ap_factor(m, sap=True)
            m["pen_damage_per_further_part"] = _rhu(m["direct"] * f)
            m["further_factor_applied"] = f


def _transform_defense(w):
    """(e) guns.defesa_antilaser = banda: carga contra laser/ion 3200 r4 / 4300 r6 / 16900 r9."""
    if switch("guns.defesa_antilaser") != "banda":
        return
    banda = {"bs_flak_light": 3200, "bs_ciws": 4300, "bs_flak_heavy": 16900}
    tot = banda.get(_short(w["id"]))
    if tot is None:
        return
    for m in w["ammo_modes"]:
        m["blast_vs_lasers"]["total_damage"] = tot
        m["blast_vs_lasers"]["band_addendum"] = "guns.defesa_antilaser = banda"


def _transform_factories(facs):
    """(b) guns.ac_cost = 3x -> F2 AC 1,25 s; (c) econ.factory_adjacency = vanilla -> todo intervalo x1,5, DEPOIS
    do (b) (J2R3-25), com as taxas por segundo recalculadas (bateria e calor por ciclo nao mudam)."""
    ac3 = switch("guns.ac_cost") == "3x"
    adj = switch("econ.factory_adjacency") == "vanilla"
    for f in facs:
        oc = f.get("overclock") or {}
        speed = float(str(oc.get("SPEED_FACTOR", "300%")).rstrip("%")) / 100
        power = float(str(oc.get("POWER_USE_FACTOR", "150%")).rstrip("%")) / 100
        for r in f["recipes"]:
            r["interval_s_spec"] = r["interval_s_base"]
            iv = r["interval_s_base"]
            if ac3 and f["code"] == "F2" and r["recipe"] == "ac":
                iv = 1.25
            if adj:
                iv = round(iv * 1.5, 4)
            r["interval_s_base"] = iv
            r["interval_s"] = iv
            ups = r.get("units_per_cycle", 1) / iv
            r["units_per_s_base"] = round(ups, 4)
            r["units_per_s_overclock"] = round(ups * speed, 4)
            if r.get("battery_mb_per_cycle") is not None:
                r["battery_mb_per_s_base"] = round(r["battery_mb_per_cycle"] / iv, 3)
                r["battery_mb_per_s_overclock"] = round(r["battery_mb_per_cycle"] / iv * speed * power, 3)
            r["tile_seconds_per_unit"] = round(f["size"][0] * f["size"][1] * iv / r.get("units_per_cycle", 1), 4)
    if ac3:
        TRANSFORMS.append("(b) guns.ac_cost = 3x: F2 AC 1,25 s")
    if adj:
        TRANSFORMS.append("(c) econ.factory_adjacency = vanilla: intervalos x1,5")


def _transform_pem(pems):
    """(d) pem.tuvira_cp; (d2) pem.tuvira_mount (torre: numeros de 2026-10-21; fixa: historico); nome da pesada."""
    cp = int(switch("pem.tuvira_cp"))
    mount = switch("pem.tuvira_mount")
    heavy = switch("pem.heavy_name")
    for p in pems:
        s = _short(p["id"])
        if s == "bs_pem_light":
            p["command_points"] = cp
            if mount == "torre":
                tn = p["torre_numbers_2026-10-21"]
                p["mount"] = "torre"
                p["firing_arc_deg"] = int(str(tn["FiringArc"]).rstrip("d"))
                p["rotate_speed_deg_s"] = int(str(tn["RotateSpeed"]).rstrip("d"))
                p["trigger_interval_s"] = tn["trigger_interval_s"]
                p["shots_per_trigger"] = tn["shots_per_trigger"]
                p["fire_rate_shots_per_s"] = tn["fire_rate_shots_per_s"]
                p["internal_storage"]["MaxResources"] = tn["MagStorage_0"]
                p["internal_storage"]["ResupplyThreshold"] = tn["ResupplyThreshold"]
                p["computed"]["shp_per_s"] = tn["shp_per_s"]
            else:
                fx = p["mount_fixa_historico"]
                p["mount"] = "fixa"
                p["firing_arc_deg"] = fx["firing_arc_deg"]
                p["rotate_speed_deg_s"] = None
                p["trigger_interval_s"] = fx["trigger_interval_s"]
                p["fire_rate_shots_per_s"] = fx["fire_rate_shots_per_s"]
                p["internal_storage"]["MaxResources"] = fx["MaxResources"]
                p["internal_storage"]["ResupplyThreshold"] = fx["ResupplyThreshold"]
                p["computed"]["shp_per_s"] = fx["shp_per_s"]
                p["name_ptbr"], p["name_en"] = fx["name_ptbr"], fx["name_en"]
                if fx.get("vs_sw"):
                    p["vs_sw"] = fx["vs_sw"]
            p["computed"]["shots_per_s"] = p["fire_rate_shots_per_s"]
            p["computed"]["shp_per_s_per_cp"] = _rhu(p["computed"]["shp_per_s"] / max(1, cp))
        if s == "bs_pem_heavy":
            if heavy == "Corisco":
                p["codename"] = "Corisco"
            else:
                # nome historico (safe): pesada 'Mae-do-Ouro', overclock 'Corisco'
                p["codename"] = SPEC["switches"]["pem"]["heavy_name"]["safe"]
                if p.get("overclock"):
                    p["overclock"]["name_ptbr"] = "Corisco"
                    p["overclock"]["name_en"] = "Corisco"
    TRANSFORMS.append(f"(d) pem.tuvira_cp = {cp}; (d2) pem.tuvira_mount = {mount}; pem.heavy_name = {heavy}")


# ============================================================================= canhoes, defesas e tiros
SHOTS = []      # um dict por tiro (kind, file, dir, owner, id, ...); contrato SPEC.generator_mapping.shot_dispatch
GUNS = []
DEFENSES = []
SPEC_WEAPONS = copy.deepcopy(SPEC["weapons"])
SPEC_DEFENSES = copy.deepcopy(SPEC["defenses"])
for _w in SPEC_WEAPONS:
    _transform_weapon(_w)
for _w in SPEC_DEFENSES:
    _transform_defense(_w)
TRANSFORMS.append(f"(a0) guns.he_further_factor = {switch('guns.he_further_factor')}; "
                  f"(a) guns.ap_further_factor = {switch('guns.ap_further_factor')}")
if switch("guns.defesa_antilaser") == "banda":
    TRANSFORMS.append("(e) guns.defesa_antilaser = banda")


def _num_from(text, pat, default):
    m = re.search(pat, str(text or ""))
    return int(m.group(1)) if m else default


def _gun_shot(w, m, oc=None, oc_range=None):
    """Tiro de um modo (index da tabela) com os numeros ja transformados + as chaves visuais da Fase B.
    oc = overclock do spec (arquivo _oc proprio: troca de projetil); oc_range = alcance em overclock SEM troca de
    projetil (armas com seletor: Range com BuffRemap Overclock, padrao do pd_shot)."""
    short = _short(w["id"])
    key = m["key"]
    sid = _short(m["shot_id"]) + ("_oc" if oc else "")
    dmg = m["direct"]
    pen = m.get("penetration") or 0
    exp_r = m.get("explosive_radius_m") or 0
    exp_d = m.get("explosive") or 0
    shield = m.get("shield_damage")
    fire = m.get("fire_chance", 0.05)
    rng = w["range_m"]
    speed = w["shot_speed_mps"]
    impact = None
    if oc:
        df = oc.get("damage_factor", 1) or 1
        dmg = _rhu(dmg * df)
        exp_d = _rhu(exp_d * df)
        if shield is not None:
            shield = _rhu(shield * (oc.get("shield_damage_factor") or df))
        rf = oc.get("range_factor", 1) or 1
        rng = int(oc.get("range_overclock_m") or round(rng * rf))
        speed = _rhu(speed * (oc.get("speed_factor") or 1))
        if oc.get("explosive_damage"):
            impact = [oc["explosive_radius_m"], oc["explosive_damage"]]
    shot = w.get("shot") or {}
    targetable = bool(shot.get("targetable"))
    hp = shot.get("shot_hp")
    if not targetable and switch("guns.small_rounds_targetable"):
        targetable, hp = True, shot.get("fallback_shot_hp_if_targetable")
    cal = _caliber(dmg + exp_d)
    vis = VIS[short]
    oc_rate = max(1, ((w.get("overclock") or {}).get("fire_rate_factor") or 1))
    fast = w["fire_rate_shots_per_s"] * oc_rate >= FAST_RATE
    s = {
        "kind": "kinetic", "file": sid, "dir": sid, "id": f"{AUTHOR}.{sid}", "owner": "bsgen.guns",
        "title": f"{w['name_en']} - {key.upper()}{' (overclock)' if oc else ''}",
        "gun": short, "index": m["index"], "key": key, "ammo": key, "oc": bool(oc), "art_tier": w.get("art_tier"),
        "res": m["resource"],
        "range": rng, "speed": max(60, speed), "targetable": targetable, "health": hp,
        "target_category": shot.get("target_category") or "bullet",
        "direct": dmg, "damage": dmg, "explosive": exp_d, "explosive_radius": exp_r,
        "shield_damage": shield, "penetration": pen, "armor_factor": m.get("armor_factor"),
        "pen_damage": m.get("pen_damage_per_further_part"), "fire": fire,
        # visual (Fase B)
        "look": vis["look"], "glow_color": ammo_color(key, "glow"), "glow_size": list(vis["glow"]),
        "tracer_color": ammo_color(key, "tracer"), "core_color": ammo_color(key, "core"),
        "fx": {"mg": "mg", "med": "mg" if fast else "med", "large": "large", "deck": "deck"}[cal],
        "volume": {"mg": 0.5, "med": 0.6, "large": 0.8, "deck": 1.0}[cal],
        "max_conc": {"mg": 30, "med": 20, "large": 12, "deck": 8}[cal],
        "shake": {"mg": 0, "med": 0, "large": 0.04, "deck": 0.08}[cal],
        "radius": {"mg": 0.1, "med": 0.15, "large": 0.3, "deck": 0.45}[cal],
        "spec2": m,
    }
    if vis["look"] == "large":
        s["sprite_size"] = vis["size"]
    else:
        s["sprite_wh"] = list(vis["wh"])
        s["core_wh"] = list(vis["core"])
    if "glow_off" in vis:
        s["glow_offset"] = vis["glow_off"]
    if "z" in vis:
        s["glow_z"] = vis["z"]
    if vis.get("trail"):
        s["trail"] = vis["trail"]
        s["trail_color"] = key
    if fast:
        s["fast"] = True
    if vis.get("plasma"):
        s["plasma_fx"] = vis["plasma"]
        s["plasma_oc"] = bool(oc)
    if key == "plasma":
        s["fx"] = "plasma_fast" if fast else "plasma"
        s["category"] = "laser"
        s["heat"] = m.get("heat_status_per_hit") or _rhu(min(400, dmg * 0.08))
        s["bolt"] = True
    kind = str(m.get("kind") or "")
    if kind.startswith("contact"):
        # Boiuna: granada de contato (build_explosive): HitShield = shield_damage, explosao estrutural, fogo (bonus
        # fora do balanco), OnDeath detona no fim do alcance; AC guiada com boiuna.ac_guided
        s.update({"kind": "explosive", "explosion": [max(1.0, exp_r), exp_d],
                  "struct_explosion": [m.get("structural_radius_m") or max(2, exp_r * 0.8),
                                       m.get("structural_explosive") or _rhu(exp_d * 0.3)],
                  "explosion_fire": _num_from(m.get("explosion_fire"), r"StatusChancePerNDamage\s+(\d+)%", 50),
                  "friendly_fire": bool(m.get("friendly_fire", False)), "death_blast": True,
                  "category": "bullet", "shield_factor": (shield / max(1, dmg + exp_d)) if shield else 1})
        g = m.get("guided")
        if isinstance(g, dict) and switch("boiuna.ac_guided"):
            s["guided"] = {k: v for k, v in g.items() if k in ("Type", "TurnVelocity", "Delay",
                                                                "ModifiesLinearVelocity", "VelocityCompensation")}
        return s
    s["struct_damage"] = max(1, _rhu(dmg / 4))
    if exp_d:
        # carga explosiva onde o projetil para (HE/AC do 20 mm para cima; SAP com meia carga e raio 0,75x)
        s["finish_explosion"] = [max(1.0, exp_r), exp_d]
        if key == "sap":
            s["explosion_fire"] = 40
    if impact:
        s["impact_explosion"] = impact
        s["extra_particles"] = ["./Data/shots/missile_he/particles/missile_he_hit.rules"]
    if oc_range:
        s["oc_range"] = oc_range
    hyb = w.get("hybrid") or {}
    if hyb:
        s["anti_projectile"] = (hyb.get("anti_projectile_damage_per_hit") or {}).get(key, dmg)
        s["anti_categories"] = list(hyb.get("categories") or PD_CATEGORIES)
    return s


def _geom(w, hint):
    """Proporcao dos canos (arte procedural): comprimento pelo nivel, grossura pelo calibre."""
    W, _H = w["size"]
    m0 = w["ammo_modes"][0]
    dmg = m0["direct"] + (m0.get("explosive") or 0) * 0.5
    lf = {"early": 0.75, "mid": 0.85, "late": 1.0}[w["tier"]]
    bw = 0.11 if dmg < 450 else 0.17 if dmg < 2000 else 0.26 if dmg < 5000 else 0.36
    if "406" in w["id"]:
        bw, lf = 0.46, 1.05
    if hint["barrel"] in ("gatling", "plasma"):
        bw = max(bw, 0.28 if W <= 3 else 0.4)
    if hint["barrel"] == "howitzer":
        bw, lf = 0.46, 0.95
    return {"len_factor": lf, "barrel_w": bw}


def _attach_art3d(g, pid, size):
    meta = _meta(g["art3d_dir"], size, pid, f"{pid} (arma)")
    g["art3d"] = meta
    if meta and len(meta["barrel"]["ys"]) != g["barrels"]["count"]:
        raise ValueError(f"art3d/{g['art3d_dir']}: o render tem {len(meta['barrel']['ys'])} cano(s) visiveis, mas as "
                         f"regras esperam {g['barrels']['count']}")
    if meta and meta.get("crew_pos"):
        # lista inteira do meta; o modulo corta em [:crew] (J2R3-12: bs_naval_406 traz 10 postos para 7 tripulantes)
        g["crew_pos"] = [tuple(c) for c in meta["crew_pos"]]


def _gun(w):
    short = _short(w["id"])
    hint = art_hint(short)
    oc = w.get("overclock")
    spin = w.get("spinup")
    sel = list(w.get("ammo_selector") or [])
    oc_rf = (oc or {}).get("range_factor", 1) or 1
    oc_range = int(oc.get("range_overclock_m") or round(w["range_m"] * oc_rf)) if (oc and sel and oc_rf != 1) else None
    modes = []
    for m in sorted(w["ammo_modes"], key=lambda x: x["index"]):
        i = m["index"]   # indice do modo = o da tabela (nunca enumerate; R4 / bs_data 1.x:367-380)
        s = _gun_shot(w, m, oc_range=oc_range)
        SHOTS.append(s)
        storage = int(m["internal_storage_units"])
        md = {"index": i, "mode": i, "key": m["key"], "ammo": m["key"], "res": m["resource"],
              "internal_storage_units": storage, "storage": storage, "resupply_threshold": storage // 2,
              "splitter_to_quantity": int(m["splitter_to_quantity"]), "shots_per_unit": int(m["splitter_to_quantity"]),
              "resources_used_per_shot": int(m["resources_used_per_shot"]),
              "units_per_shot": int(m["resources_used_per_shot"]),
              "shot": s["file"], "show_pen": s["kind"] == "kinetic", "oc_range": bool(s.get("oc_range")),
              "names": C.index_names(i, m["key"]), "spec2": m}
        if oc and (sel or ((oc.get("damage_factor") or 1) == 1 and oc_rf == 1)):
            md["shot_oc"] = s["file"]
        elif oc:
            so = _gun_shot(w, m, oc)
            SHOTS.append(so)
            md["shot_oc"] = so["file"]
        modes.append(md)
    nb = int(w.get("barrels") or 1)
    burst = int(w.get("burst") or 1)
    visual_barrels = 1 if spin else nb
    fp = w.get("fire_pattern", "") or ""
    pattern = "alternate"
    if fp.startswith("salvo") or (burst > 1 and burst == nb):
        pattern = "volley"
    elif fp == "alternate_pairs":
        pattern = "pairs"
    spt = int(w.get("shots_per_trigger") or (visual_barrels if pattern == "volley" else 1))
    if w.get("fire_interval_s"):
        fire_interval = float(w["fire_interval_s"])
    elif spin:
        fire_interval = 1.0 / spin["min_rate"]
    else:
        fire_interval = spt / w["fire_rate_shots_per_s"]
    geo = _geom(w, hint)
    g = {
        "id": w["id"], "short": short, "key": _key(short), "kind": "gun",
        "name_en": w["name_en"], "name_pt": w["name_ptbr"], "codename": w.get("codename", ""),
        "tier": w["tier"], "size": list(w["size"]), "crew": int(w["crew"]), "cp": int(w["command_points"]),
        "hp": int(w["max_health"]), "cost": w["build_cost"], "ring": w.get("prohibit_ring_tiles", 1),
        "arc": w["firing_arc_deg"], "rotate": w["rotate_speed_deg_s"], "threshold": 2 if w["tier"] != "early" else 4,
        "fire_interval": round(fire_interval, 4), "spread": w.get("spread_deg_half", 1.5),
        "recoil": _rhu(min(400, (modes and (w["ammo_modes"][0]["direct"] + (w["ammo_modes"][0].get("explosive") or 0))
                                 or 0) / 40)),
        "modes": modes, "selector": len(modes) > 1, "available_choices": list(w.get("available_choices") or []),
        "barrels": {"count": visual_barrels,
                    "spacing": round(max({"early": 0.22, "mid": 0.3, "late": 0.5}[w["tier"]], geo["barrel_w"] * 2.15), 3),
                    "pattern": pattern, "width": geo["barrel_w"], "len_factor": geo["len_factor"]},
        "burst": None, "shots_per_trigger": spt,
        "fx": dict(FX[hint["fx"]]),
        "art": {"style": hint["style"], "barrel": hint["barrel"], "accent": hint["accent"]},
        "art_tier": w.get("art_tier"), "art3d_dir": w.get("art3d_dir") or short,
        "hybrid": bool(w.get("hybrid")), "desc": w.get("visual_concept", ""),
        "cookoff_cap": w.get("cookoff_cap"), "internal_stock": w.get("internal_stock"),
        "belt": w.get("belt"), "logistica": w.get("logistica"), "per_ship_limit": w.get("per_ship_limit"),
        "spec": w, "spec2": w, "extra_categories": [],
    }
    if g["hybrid"]:
        g["anti_categories"] = list((w.get("hybrid") or {}).get("categories") or PD_CATEGORIES)
        g["fire_pref_default"] = int((w.get("hybrid") or {}).get("fire_pref_default") or 2)
    if nb > 1 and not spin:
        g["barrels"]["count"] = min(nb, 4)
        if nb > 4:
            g["barrels"]["count"] = 3
    _attach_art3d(g, w["id"], w["size"])
    if spin:
        g["spin"] = {"max": round(spin["max_rate"] / spin["min_rate"], 3), "up": spin["seconds_to_max"],
                     "down": round(spin["seconds_to_max"] / 2, 2)}
    if w.get("crew_stun"):
        st = w["crew_stun"]
        ost = (oc or {}).get("crew_stun") or {}
        g["stun"] = {"radius": st["radius_m"], "duration": st["seconds"],
                     "oc_radius": ost.get("radius_m", round(st["radius_m"] * 1.3, 3)),
                     "oc_duration": ost.get("seconds", round(st["seconds"] * 1.5, 3))}
    if oc:
        fr = oc.get("fire_rate_factor", 1) or 1
        g["oc"] = {"fire_interval_factor": round(1 / fr, 4),
                   "half_spread": oc.get("half_spread_deg") or round(g["spread"] * 1.25, 3),
                   "recoil_factor": oc.get("recoil_factor") or 1.6, "heat_per_shot": oc["heat_per_shot"],
                   "heat_per_second": oc.get("heat_per_second", 0), "name_en": oc.get("name_en", ""),
                   "name_pt": oc.get("name_ptbr", ""), "spec2": oc}
        if spin:
            g["oc"]["max_spin"] = g["spin"]["max"]
            if oc.get("spin_up_s"):
                g["oc"]["spin_up"] = oc["spin_up_s"]
    return g


def _defense(w):
    short = _short(w["id"])
    hint = art_hint(short)
    oc = w.get("overclock")
    stock = int(w["internal_stock"]["internal_storage_units"])   # MagStorage_0/_4 (J2-LOW: nao existe por modo)
    frag = None
    cloud = None
    if oc and oc.get("cloud"):
        cl = oc["cloud"]
        cloud = {"kind": "cloud", "file": f"bs_cloud_{short[3:]}", "dir": short, "id": f"{AUTHOR}.bs_cloud_{short[3:]}",
                 "owner": "bsgen.ciws", "radius": cl["radius_m"], "lifetime": cl["lifetime_s"], "pool": cl["damage_pool"],
                 "defense": short}
        SHOTS.append(cloud)
    modes = []
    for m in sorted(w["ammo_modes"], key=lambda x: x["index"]):
        i = m["index"]
        bs, bl = m["blast_vs_shots"], m["blast_vs_lasers"]
        beam = {"kind": "flak", "file": _short(m["beam_file"]), "dir": short, "id": m["beam_file"], "owner": "bsgen.ciws",
                "title": f"{w['name_en']} - {m['key'].upper()}", "defense": short, "index": i, "key": m["key"],
                "res": m["resource"], "range": w["range_m"], "vs_shots": bs["total_damage"], "radius": bs["radius_m"],
                "categories": list(bs["categories"]), "crew": bool(bs.get("crew", True)),
                "laser_categories": list(bl["categories"]), "vs_lasers": bl["total_damage"],
                "laser_radius": bl["radius_m"],
                "offset": list(w.get("random_offset_radius_m") or [0.5, min(2.0, 0.67 * bs["radius_m"])]),
                "volume": 0.4, "max_conc": 12, "particles": 3, "spec2": m}
        if beam["offset"][1] >= min(beam["radius"], beam["laser_radius"]) and not m.get("fragments"):
            # FRAG fica de fora: a explosao central e menor de proposito e o cone de fragmentos cobre o resto
            raise ValueError(f"{short}/{m['key']}: o maximo do RandomOffsetRadius tem que ficar abaixo do raio da "
                             f"explosao ({beam['offset'][1]} >= {min(beam['radius'], beam['laser_radius'])})")
        fr = m.get("fragments")
        if fr:
            if frag is None:
                half = fr["cone_half_deg"]
                frag = {"kind": "frag_fragment", "file": f"bs_frag_{short[3:]}", "dir": short, "id": fr["fragment_id"],
                        "owner": "bsgen.ciws", "defense": short, "count": int(fr["count"]),
                        "damage": int(fr["damage_each_vs_bullets"]), "arc": [-half, 2 * half], "spread": [-3, 3],
                        "speed": fr["speed_mps"], "lifetime": fr["lifetime_s"], "reach": fr.get("reach_m"),
                        "radius": fr["collision_radius_m"], "categories": list(PD_CATEGORIES),
                        "variant": switch("guns.frag_fragment"), "spec2": fr}
                SHOTS.append(frag)
            beam["fragment"] = frag["file"]
            beam["frag_spawn"] = {"count": frag["count"], "arc": list(frag["arc"]), "spread": list(frag["spread"])}
        SHOTS.append(beam)
        md = {"index": i, "mode": i, "key": m["key"], "ammo": m["key"], "res": m["resource"],
              "internal_storage_units": stock, "storage": stock, "resupply_threshold": stock // 2,
              "splitter_to_quantity": int(m["splitter_to_quantity"]), "shots_per_unit": int(m["splitter_to_quantity"]),
              "resources_used_per_shot": int(m["resources_used_per_shot"]),
              "units_per_shot": int(m["resources_used_per_shot"]), "beam": beam["file"], "beam_oc": None,
              "fragment": beam.get("fragment"), "names": C.index_names(i, m["key"]), "spec2": m}
        if cloud:
            boc = {"kind": "flak_oc", "file": f"{beam['file']}_oc", "dir": short, "owner": "bsgen.ciws",
                   "base": beam["file"], "cloud": cloud["file"], "cloud_radius": cloud["radius"],
                   "cloud_pool": cloud["pool"], "cloud_lifetime": cloud["lifetime"], "defense": short, "index": i,
                   "key": m["key"]}
            SHOTS.append(boc)
            md["beam_oc"] = boc["file"]
        modes.append(md)
    thr = float(w.get("fire_threshold_deg") or 4)
    thr = int(thr) if thr.is_integer() else thr
    nb = int(w.get("barrels") or 1)
    burst = int(w.get("burst") or 1)
    rate = w.get("fire_rate_airbursts_per_s") or w.get("fire_rate_shots_per_s")
    d = {
        "id": w["id"], "short": short, "key": _key(short), "kind": "defense",
        "name_en": w["name_en"], "name_pt": w["name_ptbr"], "codename": w.get("codename", ""), "tier": w["tier"],
        "size": list(w["size"]), "crew": int(w["crew"]), "cp": int(w["command_points"]), "hp": int(w["max_health"]),
        "cost": w["build_cost"], "ring": w.get("prohibit_ring_tiles", 1), "arc": w.get("firing_arc_deg", 360),
        "rotate": w["rotate_speed_deg_s"], "threshold": thr, "fire_interval": round(burst / rate, 4),
        "burst": burst, "modes": modes, "selector": True, "available_choices": list(w.get("available_choices") or []),
        "barrels": {"count": 1 if hint["barrel"] == "gatling" else min(nb, 4), "spacing": 0.3 if w["size"][0] <= 3 else 0.5,
                    "length": {"early": 0.9, "mid": 1.4, "late": 1.9}[w["tier"]],
                    "width": 0.14 if hint["barrel"] != "gatling" else 0.3},
        "fx": dict(FX["flak"]), "art": {"style": hint["style"], "barrel": hint["barrel"], "accent": hint["accent"]},
        "art3d_dir": w.get("art3d_dir") or short, "desc": w.get("visual_concept", ""),
        "cookoff_cap": w.get("cookoff_cap"), "internal_stock": w.get("internal_stock"), "belt": w.get("belt"),
        "logistica": w.get("logistica"), "targets": w.get("targets"),
        "hold_after_cancel": 0.5, "checks_per_search": 4, "instant_searches": 3,
        "spec": w, "spec2": w, "extra_categories": [],
    }
    if w.get("burst_delay_s"):
        d["burst_delay"] = w["burst_delay_s"]
    _attach_art3d(d, w["id"], w["size"])
    if oc:
        fr = oc.get("fire_rate_factor", 1) or 1
        d["oc"] = {"fire_interval_factor": round(1 / fr, 4), "heat_per_shot": oc["heat_per_shot"],
                   "heat_per_second": oc.get("heat_per_second", 0), "name_en": oc.get("name_en", ""),
                   "name_pt": oc.get("name_ptbr", ""), "cloud": cloud["file"] if cloud else None, "spec2": oc}
    return d


for _w in SPEC_WEAPONS:
    GUNS.append(_gun(_w))
for _w in SPEC_DEFENSES:
    DEFENSES.append(_defense(_w))

# ciws_vs_own_missiles (Fase B): nuvem igual a vanilla; 'enemies_only' so se o modulo de misseis pedir
# (bs_data_missiles.MISSILE_VARIANTS), aplicado por quem constroi a nuvem.

# ============================================================================= linha PEM (dados; o WP08 constroi)
PEM = []
_PEM_SPEC = copy.deepcopy(SPEC["pem_weapons"]["weapons"])
_transform_pem(_PEM_SPEC)
for _p in _PEM_SPEC:
    _s = _short(_p["id"])
    _p["short"] = _s
    _p["key"] = _key(_s)
    _p["name_pt"] = _p["name_ptbr"]
    _p["art3d_dir"] = _p.get("art3d_dir") or _s
    _p["art3d"] = _meta(_p["art3d_dir"], _p["size"], _p["id"], f"{_p['id']} (PEM)")
    _p["extra_categories"] = []
    _p["art"] = {"style": "plasma", "barrel": "fins", "accent": "emp"}
    PEM.append(_p)

# ============================================================================= railgun (dados; o WP09 constroi)
RAIL = copy.deepcopy(SPEC["railgun"])
RAIL["enabled"] = RAIL_ENABLED
RAIL_PARTS = [f"{AUTHOR}.bs_rail_loader", f"{AUTHOR}.bs_rail_barrel", f"{AUTHOR}.bs_rail_muzzle"]

# ============================================================================= recursos
RESOURCES = []
RES_BY_KEY = {}
for _r in SPEC["resources"]:
    if _r["key"] == "slug" and not RAIL_ENABLED:
        continue    # rail.enabled = false tira bs_slug_rail dos recursos, das escolhas e do build battle
    _s = _short(_r["id"])
    _art = dict(_r.get("art") or {})
    _adir = _art.get("art3d_dir") or _s
    _rm = _meta(_adir, None, _r["id"], f"{_r['id']} (recurso)")
    if _rm is not None and int(_rm.get("stack", _r["max_stack_size"])) != int(_r["max_stack_size"]):
        warn(f"{_r['id']}: art3d/{_adir} tem pilha {_rm.get('stack')} e o recurso {_r['max_stack_size']}: arte procedural")
        PLACEHOLDERS.append(f"{_r['id']} (recurso): pilha do art3d diferente")
        _rm = None
    _rd = {
        "id": _r["id"], "dir": _s, "key": _key(_s), "spec_key": _r["key"], "family": _r["family"],
        "name_en": _r["name_en"], "name_pt": _r["name_ptbr"], "desc_pt": _r.get("description_ptbr", ""),
        "price": int(_r["buy_price"]), "sell_price": _r.get("sell_price") or "(&BuyPrice) / 2",
        "max_stack": int(_r["max_stack_size"]), "max_per_nugget": int(_r.get("max_per_nugget") or 1),
        "rarity": _r.get("rarity") or "Ammunition",
        "drop_rates": _r.get("drop_rates") or "&<./Data/resources/resources.rules>/AmmoDropRates",
        "selector_toggle": _r.get("selector_toggle"), "selector_index": _r.get("selector_index"),
        "art": {"kind": _art.get("kind", "mag"), "accent": _art.get("accent", "ammo")}, "art3d_dir": _adir,
        "art3d": _rm, "factory_id": _r.get("factory_id"), "spec2": _r,
    }
    if switch("logistics.recurso_cookoff") == "por_pilha":
        _rd["death_hit_effects"] = (_r.get("death_hit_effects") or {}).get("per_stack_mode")
    RESOURCES.append(_rd)
    RES_BY_KEY[_r["key"]] = _r["id"]
RES_BY_ID = {r["id"]: r for r in RESOURCES}

# ============================================================================= fabricas
FACTORIES = []
_FAC_SPEC = copy.deepcopy(SPEC["factories"])
_transform_factories(_FAC_SPEC)
for _f in _FAC_SPEC:
    if _f["code"] == "F6" and not RAIL_ENABLED:
        continue    # F6 so com rail.enabled
    _s = _short(_f["id"])
    _out0 = _f["recipes"][0]["output_resource"]
    _ra = (RES_BY_ID.get(_out0) or {}).get("art") or {"kind": "mag", "accent": "ammo"}
    _fd = {
        "id": _f["id"], "short": _s, "key": _key(_s), "code": _f["code"], "kind": "factory",
        "name_en": _f["name_en"], "name_pt": _f["name_ptbr"], "size": list(_f["size"]), "crew": int(_f.get("crew") or 0),
        "cp": int(_f.get("command_points") or 1), "hp": int(_f["max_health"]), "cost": _f["build_cost"],
        "recipes": _f["recipes"], "interval": _f["recipes"][0]["interval_s_base"],
        "output": [r["output_resource"] for r in _f["recipes"]], "selector": _f.get("selector"),
        "input_grids": _f.get("input_grids"), "oc": _f.get("overclock"), "base_part": _f.get("base_part"),
        "battery_max": _f.get("battery_max_resources"), "battery_threshold": _f.get("battery_resupply_threshold"),
        "art": dict(_ra), "art3d_dir": _f.get("art3d_dir") or _s,
        "logistica": _f.get("logistica"), "belt": _f.get("belt_block"), "type_categories": _f.get("type_categories"),
        "spec": _f, "spec2": _f, "extra_categories": [],
    }
    _fd["art3d"] = _meta(_fd["art3d_dir"], _f["size"], _f["id"], f"{_f['id']} (fabrica)")
    FACTORIES.append(_fd)

# ============================================================================= paiois, Fita e arte da logistica
PAIOL_ART = {"dir": SPEC["paiol"].get("art3d_dir") or "bs_paiol", "pub": SPEC["paiol"].get("published_dir") or "bs_paiol_comum"}
PAIOL_ART["meta"] = _meta(PAIOL_ART["dir"], None, None, "paiois (bs_paiol)")
FITA_ART = {d: _meta(d, None, None, f"logistica ({d})") for d in ("bs_fita", "bs_fita_fx", "bs_placas")}
PAIOL_PARTS = []
for _p in copy.deepcopy(SPEC["paiol"]["parts"]):
    _fam = _p["id"].split("_paiol_", 1)[1].rsplit("_", 1)[0]
    if _fam == "projeteis" and (not RAIL_ENABLED or (_p["size"][0] == 3 and not switch("logistics.projeteis_3x3"))):
        continue
    _p["family"] = _fam
    _p["short"] = _short(_p["id"])
    PAIOL_PARTS.append(_p)
FITA_PART = dict(SPEC["fita_teleporte"]["part"])

# ============================================================================= limites por nave
LIMIT_DEFS = []
EXTRA_CATEGORIES = {}
for _l in SPEC["category_limits"]:
    cat = _l["category"]
    if cat == "bs_limit_railgun" and not RAIL_ENABLED:
        continue
    if cat == "bs_limit_nuke" and switch("missiles.category_limits") == "off":
        continue
    _mx = int(switch("rail.per_ship_limit")) if cat == "bs_limit_railgun" else int(_l["max"])
    LIMIT_DEFS.append(dict(_l, max=_mx))
    for _pid in _l["parts"]:
        EXTRA_CATEGORIES.setdefault(_pid, []).append(cat)
LIMITS = [(_l["category"], _l["max"], _l["string_keys"][0], _l["string_keys"][1]) for _l in LIMIT_DEFS]
for _g in GUNS + DEFENSES + PEM + FACTORIES:
    _g["extra_categories"] = list(EXTRA_CATEGORIES.get(_g["id"], []))

# ============================================================================= lancadores (WP06)
# LAUNCHERS / MISSILES / MISSILE_CHOICES ficam vazios ate bs_data_missiles, bsgen.launchers E bsgen.missile_shots
# (os tres com API >= 2) existirem: o bs_data_missiles le este modulo e exporta as listas.
LAUNCHERS = []
MISSILES = []
MISSILE_CHOICES = []
MISSILE_STATUSES = []
MISSILE_TYPES = {}
MISSILE_VARIANTS = {}


def launchers_ready():
    return all(C.content_module(n) is not None for n in ("bs_data_missiles", "bsgen.launchers", "bsgen.missile_shots"))


def load_launchers():
    """Liga os dados do bs_data_missiles (WP06) quando bs_data_missiles, bsgen.launchers e bsgen.missile_shots tem
    API >= 2: copia LAUNCHERS, MISSILES, MISSILE_CHOICES, MISSILE_STATUSES (mutando as listas deste modulo, entao
    quem ja tem a referencia ve) e MISSILE_TYPES / MISSILE_VARIANTS. Chamado no fim da carga deste modulo (o
    bs_data_missiles pode importar bs_data: tudo ja esta definido nesse ponto). Devolve True se ligou."""
    if not launchers_ready():
        return False
    mm = C.content_module("bs_data_missiles")
    for name in ("LAUNCHERS", "MISSILES", "MISSILE_CHOICES", "MISSILE_STATUSES"):
        globals()[name][:] = list(getattr(mm, name, None) or [])
    MISSILE_TYPES.update(getattr(mm, "MISSILE_TYPES", None) or {})
    MISSILE_VARIANTS.update(getattr(mm, "MISSILE_VARIANTS", None) or {})
    # overclock do lancador: PART_INFO nasce do MSPEC (launcher_overclock); quando o bs_data_missiles traz a chave
    # 'oc' na entrada, ela manda (a peca escrita e as techs ficam iguais) e a diferenca vira aviso
    for L in LAUNCHERS:
        info = PART_INFO.get(L.get("id"))
        if info is None or "oc" not in L:
            continue
        if bool(L["oc"]) != bool(info.get("oc")):
            warn(f"lancador {L['id']}: oc do bs_data_missiles ({'sim' if L['oc'] else 'nao'}) difere do spec "
                 f"({'sim' if info.get('oc') else 'nao'}); usando o do modulo")
        if not L["oc"]:
            info["oc"] = None
        elif not info.get("oc"):
            o = L["oc"] if isinstance(L["oc"], dict) else {}
            info["oc"] = {"en": o.get("name_en", ""), "pt": o.get("name_ptbr", "")}
    return True


def launcher_overclock(L):
    """Overclock de um lancador do MSPEC. Na 2.0 a peca NAO tem chave 'overclock': o overclock e por modo
    (modes[].overclock / overclock_affects) mais a base_part *_overclock; os nomes ficam em
    MSPEC.missiles.overclock[<codinome>] (Fúria da Caipora, Estouro da Boiada). Devolve None (sem overclock, ex.
    Tocandira) ou {name_en, name_ptbr, tech, reload_factor (maior divisor de recarga), per_mode {tipo: divisor},
    excluded [tipos sem overclock]}. Uma chave 'overclock' na propria peca (formato 1.x) ainda manda."""
    own = L.get("overclock")
    if isinstance(own, dict):
        return own if own.get("enabled", True) else None
    base = str(L.get("base_part") or "").split(" ")[0].strip()
    modes = L.get("modes") or []
    per, excluded = {}, []
    for m in modes:
        key = m.get("missile_type") or m.get("type") or m.get("key")
        oc = m.get("overclock") if isinstance(m.get("overclock"), dict) else None
        if m.get("overclock_affects") or oc:
            per[key] = (oc or {}).get("reload_divide")
        else:
            excluded.append(key)
    if not (base.endswith("_overclock") or per):
        return None
    names = ((MSPEC.get("missiles") or {}).get("overclock") or {}).get(L.get("codename"))
    names = names if isinstance(names, dict) else {}
    factors = [f for f in per.values() if f]
    return {"name_en": names.get("name_en", ""), "name_ptbr": names.get("name_ptbr", ""), "tech": names.get("tech"),
            "reload_factor": max(factors) if factors else None, "per_mode": per,
            "excluded": excluded if per else []}


# ============================================================================= indice de pecas (nomes, techs)
def _part_info():
    """id -> {name_en, name_pt, tier, kind, oc (nome do overclock en/pt ou None), size}; de todos os blocos do spec."""
    out = {}

    def put(pid, en, pt, tier, kind, oc=None, size=None):
        out[pid] = {"name_en": en, "name_pt": pt, "tier": tier, "kind": kind, "size": size,
                    "oc": ({"en": oc.get("name_en", ""), "pt": oc.get("name_ptbr", "")} if oc else None)}
    for g in GUNS + DEFENSES:
        put(g["id"], g["name_en"], g["name_pt"], g["tier"], g["kind"], g["spec"].get("overclock"), g["size"])
    for p in PEM:
        put(p["id"], p["name_en"], p["name_ptbr"], p["tier"], "pem", p.get("overclock"), p["size"])
    for f in _FAC_SPEC:
        put(f["id"], f["name_en"], f["name_ptbr"], f.get("tier", "mid"), "factory", f.get("overclock") and
            {"name_en": f"Overclocked {f['name_en']}", "name_ptbr": f"{f['name_ptbr']} (Overclocking)"}, f["size"])
    for L in MSPEC.get("launchers", []):
        # overclock do lancador: base_part *_overclock ou modos com overclock (nao existe launchers[].overclock)
        put(L["id"], L["name_en"], L.get("name_ptbr", L["name_en"]), L.get("tier", "mid"), "launcher",
            launcher_overclock(L), L.get("size"))
    for p in SPEC["paiol"]["parts"]:
        put(p["id"], p["name_en"], p["name_ptbr"], "early", "paiol", None, p["size"])
    fp = SPEC["fita_teleporte"]["part"]
    put(fp["id"], fp["name_en"], fp["name_ptbr"], "early", "fita", None, fp.get("size"))
    for rp in (RAIL.get("parts") or {}).values() if isinstance(RAIL.get("parts"), dict) else (RAIL.get("parts") or []):
        if isinstance(rp, dict) and rp.get("id"):
            put(rp["id"], rp.get("name_en", rp["id"]), rp.get("name_ptbr", rp.get("name_en", rp["id"])), "late", "rail",
                None, rp.get("size"))
    return out


PART_INFO = _part_info()


# ============================================================================= techs (depois das pecas escritas)
def _part_ref(short, field):
    return f"&<../parts/{short}/{short}.rules>/Part/{field}"


def tech_string_key(tid):
    """Chave do texto proprio de uma tech (grupo BSTechs; texto em bs_strings)."""
    return "Tech_" + re.sub(r"[^A-Za-z0-9]", "_", _short(tid))


# techs com nome proprio (nao o da primeira peca): texto em bs_strings.TECH_NAMES
NAMED_TECHS = {f"{AUTHOR}.bs_logistica", f"{AUTHOR}.bs_paiol_pesado", f"{AUTHOR}.bs_rail"}

_TOKEN_TOGGLE = {"ammo": ("bs_ammo_type", AMMO_INDEX), "cell": ("bs_cell_type", CELL_INDEX),
                 "missile": ("bs_missile_type", MISSILE_INDEX)}


def choice_icon(kind, key):
    """gui/<icone>.png da escolha (SPEC.toggles)."""
    tid, idx = _TOKEN_TOGGLE[kind]
    ch = next(c for c in TOGGLES[tid]["choices"] if c["index"] == idx[key])
    return ch["icon"]


def _expand_paiol(pid):
    """paiol_seletor = nenhum: ficha de familia bs_paiol_<familia>_<n>x<n> -> as pecas por tipo dessa familia."""
    m = re.match(rf"{AUTHOR}\.bs_paiol_(cartuchos|celulas|misseis)_(\dx\d)$", pid)
    if not m or switch("logistics.paiol_seletor") != "nenhum":
        return [pid]
    fam, n = m.groups()
    keys = {"cartuchos": ["he", "ap", "sap", "ac", "frag"], "celulas": ["plasma", "pem"],
            "misseis": ["msl_he", "msl_cluster", "msl_emp", "msl_nuke"]}[fam]
    ids = SPEC["paiol"]["parts_when_selector_nenhum"]["ids"]
    return [i for k in keys for i in ids if i == f"{AUTHOR}.bs_paiol_{k}_{n}"]


def _expand_tokens(tokens):
    out = []
    for u in tokens:
        out.extend([u] if ":" in u else _expand_paiol(u))
    return out


def _choice_entry(tok):
    kind, key = tok.split(":", 1)
    tid, idx = _TOKEN_TOGGLE[kind]
    return idx[key], f"[{tid}, {idx[key]}]"


def career_techs(written=None, reserve=False):
    """Techs da Carreira a partir de SPEC.career_techs, filtradas pelas pecas ESCRITAS (written = set de IDs; None =
    todas as conhecidas, so para documentacao). Ficha valida: peca escrita, overclock de peca escrita, ammo:/cell:/
    missile: (indice 0 nunca listado). Tech sem ficha valida sai; pre-requisito que saiu e trocado pelos dele
    (transitivo); Icon = primeira peca, ou o icone da escolha (gui/<icone>.png) numa tech so de escolha.
    reserve = True: reserve_unlocks (esteira, WP15) entram se escritos."""
    known = written if written is not None else set(PART_INFO)
    specs = {t["id"]: t for t in SPEC["career_techs"]}
    kept, removed = {}, set()
    for t in SPEC["career_techs"]:
        tid = t["id"]
        toks = list(t["unlocks"]) + (list(t.get("reserve_unlocks") or []) if reserve else [])
        toks = _expand_tokens(toks)
        parts = [u for u in toks if ":" not in u and u in known]
        ocs = [u.split(":", 1)[1] for u in toks if u.startswith("overclock:")]
        ocs = [o for o in ocs if o in known and (PART_INFO.get(o) or {}).get("oc")]
        choices = []
        for u in toks:
            if u.startswith(("ammo:", "cell:", "missile:")):
                i, ent = _choice_entry(u)
                if i == 0:
                    continue   # indice 0 nunca bloqueado (R16)
                choices.append((u, ent))
        if not parts and not ocs and not choices:
            removed.add(tid)
            continue
        entry = {"ID": tid}
        if parts:
            p0 = _short(parts[0])
            if tid in NAMED_TECHS:
                entry.update({"NameKey": Q(f"BSTechs/{tech_string_key(tid)}"),
                              "DescriptionKey": Q(f"BSTechs/{tech_string_key(tid)}Desc")})
            else:
                entry.update({"NameKey": _part_ref(p0, "NameKey"), "DescriptionKey": _part_ref(p0, "DescriptionKey")})
            entry.update({"Icon": _part_ref(p0, "EditorIcon"), "EditorGroup": Q(C.EDITOR_GROUP),
                          "PartsUnlocked": [_part_ref(_short(p), "ID") for p in parts]})
        elif ocs:
            p0 = _short(ocs[0])
            entry.update({"Categories": ["overclock"], "NameKey": Q(f"BSTechs/{tech_string_key(tid)}"),
                          "DescriptionKey": Q(f"BSTechs/{tech_string_key(tid)}Desc"),
                          "Icon": _part_ref(p0, "EditorIcon"), "SecondaryIcon": "&~/OverclockIcon",
                          "EditorGroup": Q(C.EDITOR_GROUP)})
        else:
            kind, key = choices[0][0].split(":", 1)
            entry.update({"NameKey": Q(f"BSTechs/{tech_string_key(tid)}"),
                          "DescriptionKey": Q(f"BSTechs/{tech_string_key(tid)}Desc"),
                          "Icon": {"Texture": {"File": Q(f"../{choice_icon(kind, key)}"), "MipLevels": 2,
                                               "SampleMode": "Linear"}, "Size": [48, 48]},
                          "EditorGroup": Q(C.EDITOR_GROUP)})
        tcu = []
        if ocs:
            tcu += [f"{{ PartID={o}; ToggleID=thermal_overclock; Mode=1; }}" for o in ocs]
        tcu += [ent for _u, ent in choices]
        if tcu:
            entry["ToggleChoicesUnlocked"] = tcu
        entry["Cost"] = int(t["cost_credits"])
        entry["_pre"] = [p for p in t.get("prerequisites", []) if p]
        kept[tid] = entry

    def resolve(pre, seen=()):
        out = []
        for p in pre:
            if p in kept or not p.startswith(f"{AUTHOR}."):
                out.append(p)
            elif p in specs and p not in seen:
                out += resolve(specs[p].get("prerequisites", []), seen + (p,))
        return out
    res = []
    for tid, e in kept.items():
        pre = []
        for p in resolve(e.pop("_pre")):
            if p not in pre and p != tid:
                pre.append(p)
        if pre:
            e["Prerequisites"] = pre
        res.append(e)
    return res


def bb_whitelist(written=None, reserve=False):
    """PartsWhitelist do Build & Battle: SPEC.buildbattle.whitelist filtrada pelas pecas escritas (paiol_seletor =
    nenhum: familia -> pecas por tipo; reserve: + whitelist_reserve)."""
    known = written if written is not None else set(PART_INFO)
    ids = _expand_tokens(list(SPEC["buildbattle"]["whitelist"]) +
                         (list(SPEC["buildbattle"].get("whitelist_reserve") or []) if reserve else []))
    return [i for i in ids if i in known]


def _res_ref(rid):
    r = RES_BY_ID.get(rid)
    if r:
        return f"&<../resources/{r['dir']}/{r['dir']}.rules>/ID"
    return None


def buildbattle_techs(written=None):
    """Techs do Build & Battle (padrao 1.x): armas/defesas/PEM/lancadores de meio e fim por tech bs_bb_<id>
    (+ -overclock); lancadores (e a Tocandira, sempre oferecida) liberam os NOSSOS recursos de missil
    (SPEC.buildbattle.resources_unlocked, nunca missile_part_*); bs_bb_bs_rail libera as 3 pecas do Tupa + F6."""
    known = written if written is not None else set(PART_INFO)
    white = set(bb_whitelist(written))
    ru = SPEC["buildbattle"].get("resources_unlocked") or {}
    out = []

    def thr(tier):
        return 0 if tier in ("early", "mid") else 200000

    def add_part_tech(pid, cat, tier, oc, resources=None, tid=None):
        s = _short(pid)
        e = {"ID": tid or f"{AUTHOR}.bs_bb_{s}", "NameKey": _part_ref(s, "NameKey"),
             "DescriptionKey": _part_ref(s, "DescriptionKey"), "Icon": _part_ref(s, "EditorIcon"),
             "Category": [cat], "PartsUnlocked": [_part_ref(s, "ID")]}
        refs = [x for x in (_res_ref(r) for r in (resources or [])) if x]
        if refs:
            e["ResourcesUnlocked"] = refs
        e["Cost"] = 5000
        e["FundsThresholdBeforeOffered"] = thr(tier)
        out.append(e)
        if oc:
            out.append({"ID": f"{AUTHOR}.bs_bb_{s}-overclock", "NameKey": Q(f"BSTechs/{tech_string_key(pid)}_BBOC"),
                        "DescriptionKey": Q(f"BSTechs/{tech_string_key(pid)}_BBOCDesc"),
                        "Icon": _part_ref(s, "EditorIcon"), "SecondaryIcon": "&~/OverclockIcon",
                        "Category": ["overclocks"],
                        "PartsUnlocked": "&<./Data/modes/pvp/pvp_buildbattle/techs_buildbattle.rules>/ThermalParts",
                        "ToggleChoicesUnlocked": [f"{{ PartID={pid}; ToggleID=thermal_overclock; Mode=1; }}"],
                        "Cost": 5000, "FundsThresholdBeforeOffered": thr(tier),
                        "Prerequisites": [e["ID"]]})
    for g in GUNS + DEFENSES + PEM:
        if g["id"] not in known or g["id"] in white:
            continue
        cat = "defenses" if g in DEFENSES else "weapons"
        add_part_tech(g["id"], cat, g["tier"], bool((PART_INFO.get(g["id"]) or {}).get("oc")))
    for L in LAUNCHERS:
        pid = L["id"]
        if pid not in known:
            continue
        info = PART_INFO.get(pid) or {}
        if pid in white:
            # a peca vem da lista branca; esta tech sempre oferecida libera os recursos dela
            s = _short(pid)
            out.append({"ID": f"{AUTHOR}.bs_bb_{s}_ammo", "NameKey": Q(f"BSTechs/{tech_string_key(pid)}_BBAmmo"),
                        "DescriptionKey": Q(f"BSTechs/{tech_string_key(pid)}_BBAmmoDesc"),
                        "Icon": _part_ref(s, "EditorIcon"), "Category": ["weapons"],
                        "PartsUnlocked": [_part_ref(s, "ID")],
                        "ResourcesUnlocked": [x for x in (_res_ref(r) for r in ru.get(pid, [])) if x],
                        "Cost": 5000, "FundsThresholdBeforeOffered": 0})
            continue
        add_part_tech(pid, "weapons", info.get("tier", "mid"), bool(info.get("oc")), ru.get(pid, []))
    rail = [p for p in RAIL_PARTS if p in known]
    if rail:
        parts = rail + ([f"{AUTHOR}.bs_factory_slug"] if f"{AUTHOR}.bs_factory_slug" in known and
                        f"{AUTHOR}.bs_factory_slug" not in white else [])
        s0 = _short(rail[-1])
        out.append({"ID": f"{AUTHOR}.bs_bb_bs_rail", "NameKey": Q(f"BSTechs/{tech_string_key(AUTHOR + '.bs_rail')}"),
                    "DescriptionKey": Q(f"BSTechs/{tech_string_key(AUTHOR + '.bs_rail')}Desc"),
                    "Icon": _part_ref(s0, "EditorIcon"), "Category": ["weapons"],
                    "PartsUnlocked": [_part_ref(_short(p), "ID") for p in parts], "Cost": 5000,
                    "FundsThresholdBeforeOffered": 200000})
    return out


# ============================================================================= conferencia dos dados
def selfcheck_data():
    """Lista de problemas (vazia = OK): transformacoes contra o spec com os switches padrao, indices, IDs."""
    errs = []
    if len(RESOURCES) != (12 if RAIL_ENABLED else 11):
        errs.append(f"RESOURCES tem {len(RESOURCES)}")
    for g in GUNS + DEFENSES:
        for m in g["modes"]:
            if m["index"] not in g["available_choices"] and g["selector"]:
                errs.append(f"{g['short']}: modo {m['index']} fora de AvailableChoices {g['available_choices']}")
            if AMMO_INDEX.get(m["key"], m["index"]) != m["index"] and m["key"] != "plasma":
                errs.append(f"{g['short']}: modo {m['key']} com indice {m['index']} (tabela {AMMO_INDEX.get(m['key'])})")
    if switch("guns.he_further_factor") == 0.5 and switch("guns.ap_further_factor") == "linear":
        for w0, w in zip(SPEC["weapons"], SPEC_WEAPONS):
            for a, b in zip(w0["ammo_modes"], w["ammo_modes"]):
                if a.get("pen_damage_per_further_part") != b.get("pen_damage_per_further_part"):
                    errs.append(f"{w['id']}/{a['key']}: pen_damage {b.get('pen_damage_per_further_part')} != spec "
                                f"{a.get('pen_damage_per_further_part')}")
    # toda ficha overclock:<peca> do spec precisa de overclock no indice (senao a tech some sem aviso)
    for t in SPEC["career_techs"]:
        for u in t["unlocks"]:
            if u.startswith("overclock:"):
                pid = u.split(":", 1)[1]
                if pid in PART_INFO and not PART_INFO[pid].get("oc"):
                    errs.append(f"tech {t['id']}: {u} sem overclock em PART_INFO")
    for L in MSPEC.get("launchers", []):
        oc = launcher_overclock(L)
        if oc and oc.get("tech") and not any(t["id"] == oc["tech"] for t in SPEC["career_techs"]):
            errs.append(f"{L['id']}: tech de overclock {oc['tech']} fora de SPEC.career_techs")
    files = {}
    for s in SHOTS:
        for k in ("kind", "file", "dir", "owner"):
            if not s.get(k):
                errs.append(f"tiro sem '{k}': {s.get('file')}")
        if s["file"] in files:
            errs.append(f"tiro duplicado: {s['file']}")
        files[s["file"]] = s
    return errs


MOD = {"description": ""}   # montada pelo build_mod (infra.mod_description) depois das pecas

load_launchers()
