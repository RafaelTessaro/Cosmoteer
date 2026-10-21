"""Efeitos dos misseis do Bullet Strike: arte propria por tipo, escapamento na cor do tipo, impacto do tamanho da
fase, clarao de lancamento por tipo, separacao do torpedo, contagem do Carrapato e a Iara que se reconhece de longe.

Modulo opcional (CONTRATOS secao 1 e 2.3): entra pelos seams de bs_data.py (D1 annotate), bsgen/shots.py (S2
visual_components, S4 decorate) e build_mod.py (B2 write, B3 copy_art). Ausente ou BS_FX_EXT=0 = misseis de hoje.
So importa rules_dsl e bsgen.fxkit no nivel do modulo (bsgen.shots so dentro de funcao: shots importa este).

Tabela: tools/spec/bullet_strike_missile_fx.json (copia da tabela de arte do design + configuracao por tipo + os sons
de hoje em SOUNDS, so como lugar marcado para os sons proprios de depois). Arte: art3d/bs_missiles/meta.json
(CONTRATOS secao 3; outra pasta com env BS_MISSILE_ART_DIR, para testar com folhas provisorias). Sem a arte, cada
missil usa o corpo vanilla de hoje (missile_he.png) com o escapamento novo.

So visual (CONTRATOS R4): nunca muda HitEffects, dano, raio, fisica, vida, alcance, velocidade nem gatilhos; so
MediaEffects, MediaEffectsScale, componentes de sprite/luz/midia e arquivos novos em shots/bs_missile_fx/. As
entradas de som que ja existem ficam como estao (R5).

Arquivos gerados (shots/bs_missile_fx/):
  plume_<chave>        feixe do propulsor: COPIA INTEGRAL do missile_he_thruster_plume.rules vanilla (Beam), Bucket
                       BulletUpper2 (acima dos tetos, abaixo do corpo BulletUpper3), cores e tamanho da tabela;
  plume_light_<tipo>   luz do propulsor no casco: copia integral do missile_he_thruster_plume_light.rules, recolorida;
                       nas linhas com fx_size < 1 (fases s e m, iscas) plume_light_<tipo>_s60 / _s80, Size x fx_size;
  smoke_<estilo>_<n>   fumaca: copia integral do missile_he_thruster_smoke.rules (nuke: missile_nuke_thruster_smoke),
                       Bucket BulletUpper1, n particulas/s, vida / valor / alfa / tamanho do estilo;
  fire_<estilo>_<n>    fogo do propulsor: copia integral do missile_thermal_thruster_fire.rules (nuke:
                       missile_nuke_thruster_fire), Bucket BulletUpper2, n/s, tamanho; o da Iara tingido de verde;
  backblast_heavy      sopro de lancamento do torpedo e da Iara: copia integral do cannon_smoke_deck.rules x1,4;
  launch_flash_<tipo>, burst_cluster, droplets_napalm, clank_limpet, separation_<tipo>, leak_iara, ring_torpedo,
  flash_torpedo        efeitos novos montados com os tijolos de bsgen/fxkit.py.
Copias integrais e nao heranca parcial (CONTRATOS R8): trails.py lembra que sobrescrever so um pedaco de uma Def
aninhada pode travar o jogo. O anel e o brilho residual nucleares sao os de shots/bs_nuke_fx (fxkit, os mesmos da
Boiuna).
Baldes: particulas em BulletUpper1 / BulletUpper2 tem precedente no SW:ACD (57 arquivos; ex.
sw_effects/glow/red_laser_shot_glow_med.rules l.139); feixe (Beam) em BulletUpper2 nao tem (o vanilla usa
BulletLower3, que fica sob o nosso teto): o nome do balde e valido (common_effects/effect_buckets.rules), so a ordem
de desenho sobre o casco fica para o teste no jogo T-M1.
"""

import json
import os
import posixpath
import re
import shutil

from rules_dsl import Q, fmt_num
from bsgen import fxkit as FX

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPEC_PATH = os.path.join(ROOT, "tools", "spec", "bullet_strike_missile_fx.json")
DIR = "shots/bs_missile_fx"
ART_OUT = "shots/bs_missile_art"
ART_PREFIX = "../bs_missile_art/"         # PNGs copiados, vistos de shots/<id>/<id>.rules
ART_ENV = "BS_MISSILE_ART_DIR"
VANILLA_BODY = "./Data/shots/missile_he"  # corpo de hoje (fallback sem arte): shots._missile_visuals

with open(SPEC_PATH, encoding="utf-8") as _fh:
    SPEC = json.load(_fh)
ITEMS = SPEC["items"]
TYPES = SPEC["types"]
SOUNDS = SPEC["SOUNDS"]     # sons de hoje por tipo [launch|impact|deploy|charge_beep] (lugar dos sons de depois)
TIER = SPEC["tier_letter"]

_UNSET = object()
META = _UNSET               # meta.json da arte (dict | None), lido no annotate (ou no copy_art)

HIT_BLOCKS = ("HitOperational", "HitStructural", "HitShield", "HitFriendly")

# Cor do GlowSprite do bocal (IsLight, fancy_light, _litReflectiveStrength 24) por tipo, no lugar da glow_color do
# bs_data: com [124, 255, 107] (Iara) ou [79, 195, 255] (P.E.M.) os tres canais saturam no casco e a luz sai BRANCA
# em casco branco, cinza e escuro (modelo de luz do WP2; a mesma falha que a granada da Boiuna ja corrigiu). Um canal
# so fica colorido: verde puro na Iara (fxkit.NUKE_GREEN_HULL, a mesma cor do trevo grande e da luz do propulsor) e
# azul quase puro no P.E.M. (no casco claro fica ciano, nunca branco). Os outros tipos ficam com a cor de hoje.
HULL_GLOW = {"nuclear": FX.NUKE_GREEN_HULL, "emp": [0, 90, 255]}

# Tremor do impacto da ogiva da Iara = o da granada da Boiuna (weapons.bs_nuke_howitzer.impact.shake na tabela de
# calibres): a Iara (r9) nao pode tremer menos que a Boiuna (r8). Lido do json, sem importar caliber_fx.
CAL_SPEC_PATH = os.path.join(ROOT, "tools", "spec", "bullet_strike_vfx.json")
SHAKE_BASE = "/BASE_SHAKE"


# ----------------------------------------------------------------------------- arte (meta.json)
def art_dir():
    """Pasta da arte dos misseis: env BS_MISSILE_ART_DIR (folhas de teste) ou art3d/bs_missiles."""
    return os.environ.get(ART_ENV) or os.path.join(ROOT, "art3d", "bs_missiles")


def load_meta():
    """meta.json da arte (kind "missiles", CONTRATOS secao 3) ou None quando a pasta / o meta nao existe. Arquivo
    citado e faltando aborta o build (como art3d.load_meta)."""
    d = art_dir()
    p = os.path.join(d, "meta.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        meta = json.load(fh)
    if meta.get("kind") != "missiles":
        raise ValueError(f"{p}: meta.json nao e de misseis (kind {meta.get('kind')!r})")
    missing = [n for n in meta.get("files", []) if not os.path.exists(os.path.join(d, n))]
    if missing:
        raise FileNotFoundError(f"{d}: meta.json cita arquivos que nao existem: {missing[:5]}")
    return meta


def _meta():
    global META
    if META is _UNSET:
        META = load_meta()
    return META


def copy_art(out):
    """Seam B3: copia os PNGs da arte para shots/bs_missile_art/ (com e sem --no-art, como as outras copias de
    art3d). Sem meta.json: nada (os misseis ficam no corpo vanilla)."""
    meta = _meta()
    if not meta:
        return
    src = art_dir()
    dst = os.path.join(out.root, ART_OUT)
    os.makedirs(dst, exist_ok=True)
    for name in meta["files"]:
        shutil.copyfile(os.path.join(src, name), os.path.join(dst, name))


# ----------------------------------------------------------------------------- annotate (seam D1)
def _art_key(role, typ, t):
    fmt = SPEC["art_key"][role]
    return fmt.format(type=typ, t=t)


def _hit_scale(role, typ, t):
    k = SPEC["hit_scale_key"][role]
    if isinstance(k, dict):
        k = k[typ]
    return SPEC["hit_media_scale"][k][t]


def _annotate_unit(u, role):
    if u.get("plasma_fx"):
        return
    typ = u["payload"]
    t = TIER[u["tier"]]
    key = _art_key(role, typ, t)
    if key not in ITEMS:
        raise KeyError(f"missile_fx: {u['file']}: chave de arte {key!r} fora da tabela {os.path.basename(SPEC_PATH)}")
    meta = _meta()
    u["art_key"] = key
    u["fx_key"] = key
    u["art"] = (meta or {}).get("items", {}).get(key)
    u["size_mul"] = SPEC["size_mul"].get(key, {}).get(t, 1.0)
    u["hit_scale"] = _hit_scale(role, typ, t)


def annotate(data):
    """Seam D1: chave de arte / item do meta / multiplicador de tamanho / escala do impacto / chave do escapamento
    em todo missil, filho e extra; clarao, sopro e tremor por tipo nos lancadores (caminhos vistos de
    parts/<id>/)."""
    global META
    META = load_meta()
    for s in data.MISSILES:
        _annotate_unit(s, "main")
        for c in s.get("children", []):
            _annotate_unit(c, c["role"])
        for x in s.get("extras", []):
            _annotate_unit(x, "main")
    for lch in data.LAUNCHERS:
        fx = lch["fx"]
        kinds = [m["type"] for m in lch["modes"]]
        # o clarao vanilla do lancador fica; o do tipo entra junto (cor do missil carregado)
        fx["flash_by_type"] = {k: list(fx["flash"]) + [FX.ref(DIR, f"launch_flash_{k}", "part")] for k in kinds}
        bb = {k: [_media_path(x, "part") for x in TYPES[k]["backblast"]] for k in kinds if TYPES[k].get("backblast")}
        if bb:
            fx["backblast_by_type"] = bb
        sh = {k: TYPES[k]["launch_shake"] for k in kinds if TYPES[k].get("launch_shake") is not None}
        if sh:
            fx["shake_by_type"] = sh


# ----------------------------------------------------------------------------- referencias
def _media_path(x, frm):
    """Caminho (sem &<>) de uma entrada da tabela: "./Data/..." (vanilla), "nuke:<nome>" (shots/bs_nuke_fx do fxkit)
    ou o nome de um arquivo deste modulo (shots/bs_missile_fx)."""
    if x.startswith("./Data/"):
        return x
    if x.startswith("nuke:"):
        return FX.nuke_ref(x[len("nuke:"):], frm)
    return FX.ref(DIR, x, frm)


def _media(x, frm="shot"):
    return f"&<{_media_path(x, frm)}>"


def smoke_name(ex):
    """Arquivo de fumaca de uma linha da tabela (None = sem fumaca)."""
    if not ex or not ex.get("smoke"):
        return None
    style, eps = ex["smoke"]
    return f"smoke_{style}_{_int(eps)}" + _size_tag(ex.get("fx_size", 1.0))


def fire_name(typ, ex):
    if not ex or not ex.get("fire_eps"):
        return None
    return f"fire_{typ}_{_int(ex['fire_eps'])}" + _size_tag(ex.get("fx_size", 1.0))


# filhotes da Piranha: shots.build_missile_part chama visual_components com plume=False (desempenho), entao nunca
# levam luz do propulsor; nao gerar o arquivo deles (ficaria sem uso)
NO_PLUME_LIGHT = {"cluster_child"}


def plume_light_name(typ, ex):
    """Luz do propulsor no casco por tipo e por tamanho da fase (fx_size: s 0,6 / m 0,8 / l 1), como o feixe e a
    fumaca: o mesmo 6x3 no micromissil da Tocandira (1 x 0,375) e no da Mula deixava a luz do micro do tamanho da do
    missil grande. fx_size 1 = o nome de antes (plume_light_<tipo>)."""
    return f"plume_light_{typ}" + _size_tag(ex.get("fx_size", 1.0))


def _size_tag(size):
    return "" if abs(size - 1.0) < 1e-9 else f"_s{_int(round(size * 100))}"


def _int(v):
    if isinstance(v, bool) or float(v) != int(v):
        raise ValueError(f"missile_fx: esperado inteiro, veio {v!r}")
    return int(v)


# ----------------------------------------------------------------------------- visual em voo (seam S2)
def _vanilla_body(s):
    """Corpo de hoje (fallback sem arte): o mesmo Sprite de shots._missile_visuals."""
    w, h = s["sprite_wh"]
    return {"Type": "Sprite", "RenderBucket": "BulletUpper3", "IsLit": True,
            "Sprite": {"Texture": {"File": Q(f"{VANILLA_BODY}/missile_he.png"), "MipLevels": "max"}, "Size": [w, h]},
            "NormalsTexture": {"File": Q(f"{VANILLA_BODY}/missile_he_normals.png"), "MipLevels": "max"}}


def _anchor(s, name, fallback):
    """Ancora da arte (meta "anchors") em tiles a partir do centro, ja no tamanho do jogo; sem arte, fallback."""
    art = s.get("art")
    if art and name in (art.get("anchors") or {}):
        x, y = art["anchors"][name]
        k = s.get("size_mul", 1.0)
        return [FX.r(x * k), FX.r(y * k)]
    return fallback


def visual_components(s, glow=True, plume=True):
    """Seam S2: componentes de voo do missil (substituem os de shots._missile_visuals).
      corpo: arte propria (fxkit.art_sprite_components: Sprite iluminado + normais, atlas de luzes aditivo) ou o
        corpo vanilla de hoje no tamanho de hoje;
      brilho: o GlowSprite de hoje (shots._glow_sprite), no bocal da arte quando ha arte; Iara e P.E.M. com a cor de
        um canal so (HULL_GLOW), para nao virar luz branca no casco;
      escapamento: MediaEffects no bocal, Rotation 180d (missile_he.rules l.96-108): fogo + fumaca + feixe + luz.
        plume=False (submunicao da Piranha, por desempenho): so o feixe pequeno, e nem ele com performance_strip;
      P.E.M.: o crepitar vanilla num segundo MediaEffects (MediaEffects3 do missile_emp.rules l.121-128);
      Iara (estagio 1 e ogiva, nao a isca): trevo de radiacao verde girando (fxkit.radiation_components).
    None so quando o missil nao tem fx_key (sem annotate)."""
    key = s.get("fx_key")
    if not key or s.get("plasma_fx"):
        return None
    from bsgen import shots as SH       # import tardio: shots importa este modulo
    typ = s["payload"]
    ex = ITEMS[key].get("exhaust") or {}
    art = s.get("art")
    mul = s.get("size_mul", 1.0)
    comps = {}
    if art:
        comps.update(FX.art_sprite_components(ART_PREFIX, art, mul))
        nozzle = FX.r(art["nozzle"][0] * mul)
        length = FX.art_size(art, mul)[0]
    else:
        comps["Sprite"] = _vanilla_body(s)
        nozzle = s["plume_offset"]
        length = s["sprite_wh"][0]
    if glow:
        g = SH._glow_sprite(s["sprite_wh"][0], HULL_GLOW.get(typ, s["glow_color"]), s["glow_size"])
        if art:
            g["Offset"] = [nozzle, 0]
        comps["GlowSprite"] = g
    media = []
    if plume:
        for name in (fire_name(typ, ex), smoke_name(ex)):
            if name:
                media.append(_media(name))
    if ex.get("beam_size") and (plume or glow):
        media.append(_media(f"plume_{key}"))
    if plume and ex.get("beam_size"):
        media.append(_media(plume_light_name(typ, ex)))
    if media:
        comps["MediaEffects"] = {"Type": "MediaEffects", "Offset": [nozzle, 0], "Rotation": "180d",
                                 "MediaEffects": media}
    T = TYPES[typ]
    if T.get("crackle"):
        comps["Crackle"] = {"Type": "MediaEffects", "MediaEffects": [_media(T["crackle"])]}
    rad = T.get("radiation")
    if rad and s.get("role", "main") in ("main", "warhead"):
        anchor = _anchor(s, "radiation", [FX.r(0.25 * length), 0])
        comps.update(FX.radiation_components(rad["big_size"], rad["big_spin"], rad["small_size"], rad["small_spin"],
                                             anchor, FX.NUKE_GREEN_HULL, big_offset=anchor,
                                             small_color=FX.NUKE_GREEN_LIGHT))
    return comps


# ----------------------------------------------------------------------------- impactos (seam S4)
def _base(k):
    return k.split(" : ")[0].strip() if isinstance(k, str) else k


def _set_scale(block, scale):
    """MediaEffectsScale = numero no bloco de impacto, logo antes do MediaEffects (SW:ACD proton_rocket.rules l.129
    e l.187, no HitShield/HitOperational de um SimpleHit; vanilla resonance_beam.rules l.111 com valor buffavel).
    Escala 1 = nada escrito."""
    if abs(scale - 1.0) < 1e-9:
        return block
    out = {}
    for k, v in block.items():
        if k == "MediaEffects":
            out["MediaEffectsScale"] = FX.r(scale, 3)
        out[k] = v
    return out


def _add_media(block, names):
    """Poe os efeitos novos depois das particulas que ja existem e antes dos sons/tremor (entradas Inh), sem mexer
    nas entradas de som (R5). MediaEffects por referencia ("&../HitOperational/MediaEffects") fica como esta."""
    lst = block.get("MediaEffects")
    if not isinstance(lst, list) or not names:
        return
    refs = [_media(n) for n in names]
    i = next((j for j, x in enumerate(lst) if not isinstance(x, str)), len(lst))
    lst[i:i] = [r for r in refs if r not in lst]


def _decorate_hit(hit, op_scale, shield_scale, friendly_scale, impact, shot_down):
    """Escala e extras nos blocos de impacto de um Hit; refs de texto ("&HitOperational") ficam como estao (herdam
    a escala do bloco apontado)."""
    for k in list(hit):
        b = _base(k)
        v = hit[k]
        if b not in HIT_BLOCKS or not isinstance(v, dict) or "MediaEffects" not in v:
            continue
        if b == "HitOperational":
            _add_media(v, impact)
            hit[k] = _set_scale(v, op_scale)
        elif b == "HitFriendly":
            _add_media(v, shot_down)
            hit[k] = _set_scale(v, friendly_scale)
        elif b == "HitShield":
            hit[k] = _set_scale(v, shield_scale)
        else:
            hit[k] = _set_scale(v, op_scale)


def _cal_nuke_shake():
    """(ShakeAmount, Duration) do impacto da Boiuna na tabela de calibres."""
    with open(CAL_SPEC_PATH, encoding="utf-8") as fh:
        amt, dur = json.load(fh)["weapons"]["bs_nuke_howitzer"]["impact"]["shake"][:2]
    return amt, dur


def _nuke_shake(hit):
    """Troca o /BASE_SHAKE do HitOperational da ogiva da Iara (0,35 / 0,5 s de shots._missile_media) pelo tremor da
    Boiuna. O HitShield usa &../HitOperational/MediaEffects e o HitStructural = &HitOperational: herdam a troca."""
    op = next((v for k, v in hit.items() if _base(k) == "HitOperational" and isinstance(v, dict)), None)
    lst = op.get("MediaEffects") if op else None
    if not isinstance(lst, list):
        raise ValueError("missile_fx: ogiva da Iara sem lista MediaEffects no HitOperational")
    idx = [i for i, e in enumerate(lst) if getattr(e, "base", None) == SHAKE_BASE]
    if len(idx) != 1:
        raise ValueError(f"missile_fx: ogiva da Iara com {len(idx)} tremor(es) {SHAKE_BASE} no HitOperational")
    amt, dur = _cal_nuke_shake()
    lst[idx[0]] = type(lst[idx[0]])(SHAKE_BASE, {"ShakeAmount": amt, "Duration": dur})


def _insert_after(d, after, items):
    """Copia de d com os pares de items logo depois da chave after (ordem do arquivo)."""
    out = {}
    for k, v in d.items():
        out[k] = v
        if k == after:
            out.update(items)
    for k, v in items.items():
        out.setdefault(k, v)
    return out


def decorate(s, top):
    """Seam S4 (no lugar): MediaEffectsScale da fase nos impactos, extras por tipo, midia da separacao do torpedo
    (Deploy.OnDeath, que ja leva HitEffects; DeathByLifetime.OnDeath com MediaEffects: mine_deployed.rules l.85-93),
    corpo e contagem da carga do Carrapato, vazamento verde da Iara abatida. Nao toca HitEffects nem numeros de jogo.
    MediaEffectsScale tambem no HitShield e no HitFriendly: o mesmo tipo de bloco do HitOperational (missile_he.rules
    l.125 "HitShield = &HitOperational", l.117 "OnDeath = &../Hit/HitFriendly"; SW:ACD proton_rocket.rules l.129 no
    HitShield de um PenetratingHit)."""
    key = s.get("fx_key")
    if not key or s.get("plasma_fx"):
        return
    typ = s["payload"]
    role = s.get("role", "main")
    T = TYPES[typ]
    comps = top.get("Components") or {}
    scale = s.get("hit_scale", 1.0)
    impact, shot_down, shield = [], [], scale
    if role == "main" and typ in ("he", "napalm", "limpet", "emp", "cluster"):
        impact = list(T.get("impact", []))
        shield = SPEC["shield_pop_scale"].get(typ, scale)
    elif role == "warhead":
        impact = list(T.get("impact", []))
        shot_down = list(T.get("shot_down", []))
    hit = comps.get("Hit")
    if isinstance(hit, dict):
        _decorate_hit(hit, scale, shield, min(1.0, scale), impact, shot_down)
        if typ == "nuclear" and role == "warhead":
            _nuke_shake(hit)
    # Piranha: abertura do cardume (BURST na raiz, usado pelos tres gatilhos)
    if role == "main" and isinstance(top.get("BURST"), dict):
        _add_media(top["BURST"], T.get("burst", []))
        top["BURST"] = _set_scale(top["BURST"], scale)
    # Carrapato: explosao da carga (BLAST na raiz) + corpo e contagem no casco
    if role == "charge":
        if isinstance(top.get("BLAST"), dict):
            _add_media(top["BLAST"], T.get("blast", []))
            top["BLAST"] = _set_scale(top["BLAST"], scale)
        art = s.get("art")
        if art and "Sprite" in comps:
            # corpo iluminado + anel de 8 LEDs, 10 quadros a 4 qps = a espoleta de 2,5 s, WrapMode Clamp (para no
            # ultimo quadro: ArmingSprite do mine_deployed.rules l.96-123). Sem arte: o pisca vanilla de hoje.
            new = FX.art_sprite_components(ART_PREFIX, art, s.get("size_mul", 1.0))
            comps["Sprite"] = new.pop("Sprite")
            top["Components"] = _insert_after(comps, "Sprite", new)
    # Boto / Iara: separacao do estagio de lancamento (o OnDeath do Deploy ja tem os SpawnBullets)
    dep = comps.get("Deploy")
    if role == "main" and isinstance(dep, dict) and isinstance(dep.get("OnDeath"), dict) and T.get("deploy"):
        od = dep["OnDeath"]
        if "MediaEffects" not in od:
            od["MediaEffects"] = [_media(n) for n in T["deploy"]]


# ----------------------------------------------------------------------------- texto vanilla -> arquivos
def _num(v):
    return fmt_num(round(float(v), 4))


def _col(c):
    return "[" + ", ".join(str(_int(x)) for x in c) + "]"


def _sub(text, old, new, what):
    n = text.count(old)
    if n != 1:
        raise ValueError(f"missile_fx: texto vanilla inesperado em {what}: {old!r} aparece {n} vez(es)")
    return text.replace(old, new)


def _range_sub(text, head, lo, hi, what, field="FromValue", field2="ToValue", old=None):
    """Troca FromValue/ToValue (ou Min/Max) logo depois de head (linha que identifica o bloco)."""
    m = re.search(re.escape(head) + r"(\n(?:\t[^\n]*\n)*?\t+)" + field + r" = ([^\n]+)\n(\t+)" + field2 +
                  r" = ([^\n]+)\n", text)
    if not m:
        raise ValueError(f"missile_fx: bloco {head!r} nao achado em {what}")
    if old is not None and (m.group(2), m.group(4)) != tuple(old):
        raise ValueError(f"missile_fx: {what}: {head!r} tem {m.group(2)}/{m.group(4)}, esperado {old}")
    new = f"{head}{m.group(1)}{field} = {_num(lo)}\n{m.group(3)}{field2} = {_num(hi)}\n"
    if text.count(m.group(0)) != 1:
        raise ValueError(f"missile_fx: bloco {head!r} repetido em {what}")
    return text.replace(m.group(0), new)


def _vendor(key):
    """(caminho vanilla, texto integral) com as curvas de volta no lugar."""
    rel, body = _VENDOR[key]
    for name, toks in _CURVES.items():
        pts = []
        for tok in toks.split():
            v, _, n = tok.partition("*")
            pts += [v] * (int(n) if n else 1)
        body = body.replace(f"\t\t\t\t@@{name}@@", "\n".join("\t\t\t\t" + p for p in pts))
    if "@@" in body:
        raise ValueError(f"missile_fx: curva sem dono em {rel}")
    return rel, body


_PATH_RE = re.compile(r"^(\t*)(File|Shader) = (\.\./[^\s\"]+)$", re.M)


def _abs_paths(text, rel):
    """Caminhos relativos do arquivo vanilla viram ./Data/... sem aspas, como no original (o arquivo sai de
    shots/bs_missile_fx/). Mesma mudanca que o SW:ACD fez ao copiar o feixe vanilla para outra pasta
    (shots/missiles/hex/particles/missile_hex_thruster_plume.rules l.6, 19, 24)."""
    base = posixpath.dirname(rel)

    def fix(m):
        p = posixpath.normpath(posixpath.join(base, m.group(3)))
        if p.startswith(".."):
            raise ValueError(f"missile_fx: caminho fora de Data em {rel}: {m.group(3)}")
        return f"{m.group(1)}{m.group(2)} = ./Data/{p}"

    out = _PATH_RE.sub(fix, text)
    left = [ln for ln in out.split("\n") if "../" in ln and "&<./Data/" not in ln]
    if left:
        raise ValueError(f"missile_fx: caminho relativo sobrando em {rel}: {left[:2]}")
    return out


def _vendored(key, note, edits):
    rel, t = _vendor(key)
    t = edits(t, rel)
    head = f"// Copia integral de ./Data/{rel} (vanilla; igual no 0.30.3 e no SW:ACD, 0.30.4).\n// {note}\n"
    return head + _abs_paths(t, rel) + "\n"


def plume_text(key):
    ex = ITEMS[key]["exhaust"]
    hot, cold, center = ex["beam_colors_hot_cold_center"]
    L, W = ex["beam_size"]

    def edits(t, rel):
        t = _sub(t, "_hotColor = [255, 209, 93, 255]", f"_hotColor = {_col(hot)}", rel)
        t = _sub(t, "_coldColor = [255, 80, 0, 255]", f"_coldColor = {_col(cold)}", rel)
        t = _sub(t, "_centerColor = [255, 233, 170, 255]", f"_centerColor = {_col(center)}", rel)
        t = _sub(t, "Size = [2.5/1.5, 0.6]", f"Size = [{_num(L)}, {_num(W)}]", rel)
        return _sub(t, "\nBucket = BulletLower3\n", "\nBucket = BulletUpper2\n", rel)
    return _vendored("plume", f"Feixe do propulsor de {ITEMS[key]['label']} ({key}): Bucket BulletUpper2 (acima dos "
                              f"tetos, abaixo do corpo BulletUpper3), cores e tamanho da tabela.", edits)


def plume_light_text(typ, size=1.0):
    """size = fx_size da fase: so o Size [6, 3] escala; _lightLength fica 1.25, como no jogo base (a luz do
    propulsor da tripulacao, Size [9/10, 6/10], e a do propulsor pequeno, [9, 6], usam os dois 1.25)."""
    hot, cold = TYPES[typ]["plume_light"]

    def edits(t, rel):
        t = _sub(t, "_hotColor = [255, 145, 28, 255]", f"_hotColor = {_col(hot)}", rel)
        t = _sub(t, "_coldColor =  [247, 29, 0, 255]", f"_coldColor =  {_col(cold)}", rel)
        if _size_tag(size):
            t = _sub(t, "\tSize = [6, 3]\n", f"\tSize = [{_num(6 * size)}, {_num(3 * size)}]\n", rel)
        return t
    if _size_tag(size):
        note = (f"Luz do propulsor no casco ({typ}, fase com fx_size {_num(size)}): cores do tipo (canal dominante, "
                f"para nao virar nevoa branca sobre casco claro) e Size x{_num(size)}.")
    else:
        note = (f"Luz do propulsor no casco ({typ}): so as cores mudam (canal dominante, para nao virar nevoa branca "
                f"sobre casco claro).")
    return _vendored("plume_light", note, edits)


def smoke_text(style, eps, size):
    st = SPEC["smoke_styles"][style]
    src = st["src"]

    def edits(t, rel):
        t = _sub(t, "EmitterDef\n{\n\tEmitPerSecond = " + ("60" if src == "he" else "800") + "\n",
                 f"EmitterDef\n{{\n\tEmitPerSecond = {_int(eps)}\n", rel)
        t = _sub(t, "\nBucket = Lower1\n", "\nBucket = BulletUpper1\n", rel)
        t = _range_sub(t, "DataOut = lifetime", *st["lifetime"], rel,
                       old=("0.9", "1.1") if src == "he" else ("0.2", "0.3"))
        t = _range_sub(t, "DataOut = base_scale", 4 * size, 5 * size, rel, old=("4", "5"))
        if st.get("value"):
            t = _range_sub(t, "ValueRange", *st["value"], rel, field="Min", field2="Max", old=("1.5", "1.5"))
        if st.get("alpha"):
            t = _range_sub(t, "AlphaRange", *st["alpha"], rel, field="Min", field2="Max", old=("0.05", "0.08"))
        warm = st.get("warm", 1.0)
        if abs(warm - 1.0) > 1e-9:
            # clarao quente aditivo do nascimento da fumaca (ColorRamp color_add): mais frio no rastro do torpedo
            a = t.index("ColorOut = color_add")
            b = t.index("\t\t\t]", a)
            seg = re.sub(r"(\t(?:Rf|Gf|Bf) = )([0-9.]+)", lambda m: m.group(1) + _num(float(m.group(2)) * warm),
                         t[a:b])
            t = t[:a] + seg + t[b:]
        return t
    return _vendored("smoke_" + src, f"Fumaca '{style}': {eps}/s, Bucket BulletUpper1, vida {st['lifetime']} s, "
                                     f"tamanho x{_num(size)}.", edits)


def fire_text(typ, eps, size):
    fs = SPEC["fire_styles"][typ]
    src = fs["src"]

    def edits(t, rel):
        t = _sub(t, "EmitterDef\n{\n\tEmitPerSecond = 800\n", f"EmitterDef\n{{\n\tEmitPerSecond = {_int(eps)}\n", rel)
        t = _sub(t, "\nBucket = Lower2\n", "\nBucket = BulletUpper2\n", rel)
        t = _range_sub(t, "DataOut = rand_scale", 0.7 * size, 0.9 * size, rel, old=("0.7", "0.9"))
        if fs.get("hsv"):
            # tinta do fogo (SetRandomHsvColor "hue" multiplicado pela textura fire.png laranja): matiz verde e valor
            # > 1 (o mesmo uso de valor > 1 do ValueRange 1,5 da fumaca vanilla) para o fogo da Iara sair verde
            h, sat, val = fs["hsv"]
            t = _range_sub(t, "HueRange", h, h, rel, field="Min", field2="Max", old=("90", "90"))
            t = _range_sub(t, "SaturationRange", sat, sat, rel, field="Min", field2="Max", old=("1", "1"))
            t = _range_sub(t, "ValueRange", val, val, rel, field="Min", field2="Max", old=("1", "1"))
        return t
    return _vendored("fire_" + src, f"Fogo do propulsor ({typ}): {eps}/s, Bucket BulletUpper2, tamanho x{_num(size)}"
                                    + (f", tinta HSV {fs['hsv']}" if fs.get("hsv") else "") + ".", edits)


def backblast_text(k=1.4):
    def edits(t, rel):
        t = _sub(t, '\t\t\tFromValue = 1\n\t\t\tToValue = 2\n\t\t\tName = "random scale"',
                 f'\t\t\tFromValue = {_num(k)}\n\t\t\tToValue = {_num(2 * k)}\n\t\t\tName = "random scale"', rel)
        t = _sub(t, "\t\t\t\t\tX = -0.6\n", f"\t\t\t\t\tX = {_num(-0.6 * k)}\n", rel)
        t = _sub(t, "\t\t\t\tRadius = 0.5\n", f"\t\t\t\tRadius = {_num(0.5 * k)}\n", rel)
        return _range_sub(t, "Speed", 4 * k, 8 * k, rel, field="Min", field2="Max", old=("4", "8"))
    return _vendored("roof_smoke", f"Sopro de lancamento do torpedo e da Iara: o leque do canhao de conves "
                                   f"(RoofCannonSmoke) x{_num(k)} (tamanho, espalhamento e velocidade).", edits)


# ----------------------------------------------------------------------------- efeitos novos (tijolos do fxkit)
HOT = [(1.6, 1.6, 1.6, 1), (1.15, 1.15, 1.15, 0.75), (1, 1, 1, 0.25), (1, 1, 1, 0)]
PUFF = [(1, 1, 1, 0), (1, 1, 1, 1), (1, 1, 1, 0.45), (1, 1, 1, 0)]


def launch_flash_text(typ):
    f = TYPES[typ]["flash"]
    return FX.blob(f"Clarao de lancamento ({typ}): blob aditivo na cor do tipo, por cima do clarao vanilla do lancador",
                   f["size"], f["life"], 0, tuple(f["color"]) + (1,), HOT, scale=(0.7, 1.25), bucket="Upper1")


def droplets_text():
    """Gotas de napalm: 8-14 bolhas de gel em brasa saindo em leque para a frente do impacto (o alvo), que perdem
    velocidade e apagam em 0,8-1,4 s: le "continua queimando". Mesmos tijolos de fxkit.streaks (provados no jogo
    pelo plasma), com blob.png aditivo no lugar da faisca."""
    pre = [FX.el("SetRandom", DataOut="location", ValueType="Vector2", FromValue=FX.V(-0.3, -0.6),
                 ToValue=FX.V(0.3, 0.6)),
           FX.el("SetRandomVelocityFromPoint", LocationIn="location", VelocityOut="base_velocity",
                 Speed=FX.R(2.5, 6), AwayFromPoint=FX.V(-0.6, 0)),
           FX.el("SetRandom", DataOut="base_color", ValueType="Color", FromValue=FX.C(1, 0.42, 0.06, 1),
                 ToValue=FX.C(1, 0.68, 0.2, 1)),
           FX.el("SetRandom", DataOut="base_scale", ValueType="Float", FromValue=0.35, ToValue=0.7),
           FX.el("SetRandom", DataOut="lifetime", ValueType="Float", FromValue=0.8, ToValue=1.4)]
    init = [FX.el("LocationToWorldSpace", LocationIn="location", LocationOut="location"),
            FX.el("VelocityToWorldSpace", VelocityIn="base_velocity", VelocityOut="base_velocity"),
            FX.el("AddFrameOfReference", VelocityInOut="inherited_velocity"),
            FX.el("ScaleToWorldSpace", ScaleIn="base_scale", ScaleOut="base_scale")]
    upd = [FX.el("VariableLifetime", LifeInOut="life", LifetimeIn="lifetime"),
           FX.el("Lerp", True, LerpIn="life", DataOut="velocity", Invert=False, ValueType="Vector2",
                 FromValue=FX.V(1, 1), ToValue=FX.V(0.1, 0.1)),
           FX.mul("Vector2", "velocity", "base_velocity", "velocity", upd=False),
           FX.addt("location", "velocity"),
           FX.addt("location", "inherited_velocity"),
           FX.ramp("color", [(1.6, 1.6, 1.6, 1), (1.2, 1.2, 1.2, 0.9), (1, 1, 1, 0.6), (0.7, 0.7, 0.7, 0)]),
           FX.mul("Color", "color", "base_color", "color"),
           FX.el("Lerp", True, LerpIn="life", DataOut="scale", Invert=False, ValueType="Float", FromValue=1,
                 ToValue=0.55),
           FX.mul("Float", "scale", "base_scale", "scale")]
    mat = {"Texture": FX.tex(FX.BLOB), "TargetBlendMode": dict(FX.ADD)}
    return FX.particles("Gotas de napalm em brasa no impacto da Taturana (8-14, 0,8-1,4 s)", init, upd,
                        FX.renderer(), mat, FX.emitter(pre, (8, 14)), "Upper1", True, "30", inflate=3)


def misc_texts():
    """{nome: texto} dos efeitos avulsos (todos com os tijolos do fxkit)."""
    return {
        "burst_cluster": FX.blob("Abertura do cardume da Piranha: clarao amarelo", 4.5, 0.3, 0, (1, 0.85, 0.3, 1), HOT,
                                 scale=(0.6, 1.3), bucket="Upper2"),
        "droplets_napalm": droplets_text(),
        "clank_limpet": FX.blob("Carrapato: estalo vermelho (gruda no casco; tambem na explosao da carga)", 2.2, 0.22,
                                0, (1, 0.18, 0.1, 1), HOT, scale=(0.6, 1.2), bucket="Upper2"),
        "separation_torpedo": FX.blob("Boto: baforada branca da separacao do estagio de lancamento", 3, 0.6, 0,
                                      (0.9, 0.95, 1, 0.6), PUFF, scale=(0.5, 1.4), bucket="Upper2"),
        "separation_nuclear": FX.blob("Iara: baforada verde-clara da separacao do estagio de lancamento", 3.5, 0.7, 0,
                                      (0.7, 1, 0.65, 0.6), PUFF, scale=(0.5, 1.4), bucket="Upper2"),
        "leak_iara": FX.blob("Iara abatida: vazamento verde (sem explosao nuclear)", 5, 1.4, 0, (0.35, 1, 0.25, 0.55),
                             PUFF, scale=(0.4, 1.5), bucket="Upper2", fancy=True, zoom="30"),
        # anel branco: shockwave.png como o anel nuclear do fxkit; 7,3 tiles x MediaEffectsScale 1,3 / 1,6 = borda
        # em ~4 / ~5 tiles (borda clara a ~0,85 do raio do quadro), o raio da ogiva do Boto
        "ring_torpedo": FX.blob("Boto: anel branco da explosao da ogiva", 7.3, 0.6, 0, (0.85, 0.92, 1, 1),
                                [(1.3, 1.3, 1.3, 1), (1.05, 1.05, 1.05, 0.85), (1, 1, 1, 0.4), (1, 1, 1, 0)],
                                scale=(0.15, 1), tex=FX.SHOCKWAVE, bucket="Upper2"),
        "flash_torpedo": FX.blob("Boto: clarao branco-azulado no casco (luz)", 8, 0.5, 0, (0.6, 0.8, 1, 0.22),
                                 [(1, 1, 1, 1), (1, 1, 1, 0.5), (1, 1, 1, 0)], light=True, bucket="Upper5"),
    }


def all_files():
    """{nome sem extensao: texto} de tudo o que vai para shots/bs_missile_fx/."""
    files = {}
    smokes, fires, kinds, lights = set(), set(), set(), set()
    for key, it in ITEMS.items():
        ex = it.get("exhaust")
        if not ex:
            continue
        kinds.add(it["type"])
        files[f"plume_{key}"] = plume_text(key)
        if ex.get("smoke"):
            smokes.add((smoke_name(ex), ex["smoke"][0], ex["smoke"][1], ex.get("fx_size", 1.0)))
        if ex.get("fire_eps"):
            fires.add((fire_name(it["type"], ex), it["type"], ex["fire_eps"], ex.get("fx_size", 1.0)))
        if ex.get("beam_size") and key not in NO_PLUME_LIGHT and _size_tag(ex.get("fx_size", 1.0)):
            lights.add((plume_light_name(it["type"], ex), it["type"], ex["fx_size"]))
    for typ in sorted(kinds | set(TYPES)):
        files[f"plume_light_{typ}"] = plume_light_text(typ)
        files[f"launch_flash_{typ}"] = launch_flash_text(typ)
    for name, typ, size in sorted(lights):
        files[name] = plume_light_text(typ, size)
    for name, style, eps, size in sorted(smokes):
        files[name] = smoke_text(style, eps, size)
    for name, typ, eps, size in sorted(fires):
        files[name] = fire_text(typ, eps, size)
    files["backblast_heavy"] = backblast_text()
    files.update(misc_texts())
    return files


def write(out, header):
    """Seam B2: grava shots/bs_missile_fx/ (sempre, inclusive com --no-art: so texto)."""
    head = "\n".join(f"// {ln}" for ln in header.split("\n")) + "\n"
    for name, txt in all_files().items():
        out.text(f"{DIR}/{name}.rules", head + txt)


# ============================================================================= texto vanilla copiado
# Gerado por SCR/vfx_impl/WP4/make_vendor.py a partir dos arquivos vanilla (git show do clone 0.30.5; os sete
# sao identicos no 0.30.3 e nas copias do SW:ACD, que mira o 0.30.4). Texto integral, com os caminhos relativos
# originais (o gerador os troca por ./Data/... em _abs_paths). As duas curvas de 1024 pontos (ValueCurve
# Points) se repetem em quatro arquivos: ficam uma vez so em _CURVES, em RLE ("valor*n" = n vezes), e entram de
# volta no lugar da linha @@Cn@@ (_vendor).
_CURVES = {
    "C0": (
        "0 0.003921569 0.011764706 0.015686275 0.023529412 0.03137255 0.03529412 0.043137256 0.050980393 "
        "0.05882353 0.06666667 0.078431375 0.08627451 0.09411765 0.101960786 0.11372549 0.12156863 0.13333334 "
        "0.14117648 0.15294118 0.16470589 0.1764706 0.18431373 0.19607843 0.20784314 0.21960784 0.23137255 "
        "0.24313726 0.25490198 0.26666668 0.2784314 0.2901961 0.3019608 0.3137255 0.3254902 0.3372549 0.3529412 "
        "0.3647059 0.3764706 0.38039216 0.3882353 0.39215687 0.4 0.40392157 0.4117647 0.41568628 0.41960785 "
        "0.42745098 0.43137255 0.4392157 0.44313726 0.4509804 0.45490196 0.45882353 0.46666667 0.47058824 "
        "0.47843137 0.48235294 0.4862745 0.49411765 0.49803922 0.5058824 0.50980395 0.5137255 0.52156866 "
        "0.5254902 0.53333336 0.5372549 0.5411765 0.54901963 0.5529412 0.5568628 0.5647059 0.5686275 0.57254905 "
        "0.5803922 0.58431375 0.5882353 0.59607846 0.6 0.6039216 0.60784316 0.6156863 0.61960787 0.62352943 "
        "0.627451 0.63529414 0.6392157 0.6431373 0.64705884 0.654902 0.65882355 0.6627451 0.6666667 0.67058825 "
        "0.6745098 0.68235296 0.6862745 0.6901961 0.69411767 0.69803923 0.7019608 0.7058824 0.70980394 0.7137255 "
        "0.7176471 0.72156864 0.7254902 0.7294118 0.73333335 0.7372549 0.7411765 0.74509805 0.7490196 0.7529412 "
        "0.75686276 0.7607843*2 0.7647059 0.76862746 0.77254903 0.7764706*2 0.78039217*4 0.78431374*7 "
        "0.7882353*7 0.7921569*8 0.79607844*7 0.8*8 0.8039216*8 0.80784315*7 0.8117647*8 0.8156863*9 "
        "0.81960785*8 0.8235294*8 0.827451*9 0.83137256*9 0.8352941*8 0.8392157*9 0.84313726*10 0.84705883*9 "
        "0.8509804*10 0.85490197*10 0.85882354*10 0.8627451*10 0.8666667*11 0.87058824*11 0.8745098*11 "
        "0.8784314*11 0.88235295*12 0.8862745*12 0.8901961*12 0.89411765*13 0.8980392*13 0.9019608*14 "
        "0.90588236*14 0.9098039*15 0.9137255*15 0.91764706*16 0.92156863*16 0.9254902*17 0.92941177*18 "
        "0.93333334*19 0.9372549*19 0.9411765*21 0.94509804*21 0.9490196*23 0.9529412*24 0.95686275*25 "
        "0.9607843*27 0.9647059*29 0.96862745*30 0.972549*31 0.9764706*33 0.98039216*33 0.9843137*34 "
        "0.9882353*35 0.99215686*34 0.99607843*33 1*16"),
    "C1": (
        "0*4 0.019607844*8 0.039215688*8 0.05882353*7 0.078431375*7 0.09803922*6 0.11372549*7 0.13333334*6 "
        "0.14901961*6 0.16862746*6 0.18431373*6 0.2*6 0.21568628*5 0.23137255*6 0.24313726*5 0.25882354*6 "
        "0.27450982*5 0.28627452*5 0.29803923*5 0.30980393*5 0.32156864*5 0.33333334*5 0.34509805*5 0.3529412*4 "
        "0.3647059*5 0.37254903*5 0.38039216*4 0.3882353*5 0.39607844*4 0.4*5 0.40784314*4 0.4117647*5 "
        "0.41960785*4 0.42352942*4 0.42745098*5 0.43529412*4 0.4392157*4 0.44313726*4 0.4509804*4 0.45490196*4 "
        "0.45882353*4 0.4627451*4 0.47058824*4 0.4745098*4 0.47843137*4 0.48235294*4 0.4862745*4 0.49019608*4 "
        "0.49411765*4 0.5019608*4 0.5058824*4 0.50980395*3 0.5137255*4 0.5176471*4 0.52156866*4 0.5254902*3 "
        "0.5294118*4 0.53333336*4 0.5372549*3 0.5411765*4 0.54509807*4 0.54901963*3 0.5529412*4 0.5568628*4 "
        "0.56078434*3 0.5647059*4 0.5686275*7 0.57254905*3 0.5764706*4 0.5803922*3 0.58431375*4 0.5882353*3 "
        "0.5921569*4 0.59607846*7 0.6*3 0.6039216*4 0.60784316*3 0.6117647*3 0.6156863*7 0.61960787*4 "
        "0.62352943*3 0.627451*3 0.6313726*4 0.63529414*6 0.6392157*4 0.6431373*3 0.64705884*7 0.6509804*3 "
        "0.654902*3 0.65882355*7 0.6627451*3 0.6666667*3 0.67058825*7 0.6745098*3 0.6784314*4 0.68235296*6 "
        "0.6862745*3 0.6901961*7 0.69411767*3 0.69803923*7 0.7019608*3 0.7058824*6 0.70980394*3 0.7137255*7 "
        "0.7176471*3 0.72156864*7 0.7254902*3 0.7294118*6 0.73333335*3 0.7372549*7 0.7411765*3 0.74509805*6 "
        "0.7490196*4 0.7529412*6 0.75686276*7 0.7607843*3 0.7647059*6 0.76862746*7 0.77254903*3 0.7764706*6 "
        "0.78039217*7 0.78431374*3 0.7882353*6 0.7921569*7 0.79607844*6 0.8*4 0.8039216*6 0.80784315*7 "
        "0.8117647*6 0.8156863*4 0.81960785*6 0.8235294*7 0.827451*6 0.83137256*7 0.8352941*7 0.8392157*3 "
        "0.84313726*7 0.84705883*6 0.8509804*7 0.85490197*7 0.85882354*7 0.8627451*7 0.8666667*7 0.87058824*7 "
        "0.8745098*7 0.8784314*7 0.88235295*7 0.8862745*7 0.8901961*7 0.89411765*8 0.8980392*7 0.9019608*7 "
        "0.90588236*8 0.9098039*7 0.9137255*8 0.91764706*8 0.92156863*12 0.9254902*8 0.92941177*8 0.93333334*8 "
        "0.9372549*8 0.9411765*9 0.94509804*13 0.9490196*9 0.9529412*9 0.95686275*9 0.9607843*9 0.9647059*15 "
        "0.96862745*10 0.972549*10 0.9764706*17 0.98039216*11 0.9843137*12 0.9882353*19 0.99215686*13 "
        "0.99607843*15 1*11"),
}

_VENDOR = {}

# shots/missile_he/particles/missile_he_thruster_plume.rules
_VENDOR["plume"] = ("shots/missile_he/particles/missile_he_thruster_plume.rules", """\
Type = Beam
Sprite
{
	Texture
	{
		File = ../../../ships/terran/thruster_small/particles/thruster_plume.png
		SampleMode = Linear
		MipLevels = max
		UVMode = Clamp
	}
	_hotColor = [255, 209, 93, 255]
	_coldColor = [255, 80, 0, 255]
	_centerColor = [255, 233, 170, 255]
	_thicknessOverIntensity = [0.5, 1]
	_additionalBuffedThickness = 0.25
	_additionalBuffedIntensity = (&<./Data/ships/terran/engine_room/engine_room.rules>/Part/Components/BuffProvider/BuffAmount)
	_noiseTexture
	{
		File = ../../../common_effects/particles/noise_gradient.png
		MipLevels = 1
		SampleMode = Linear
		UVMode = Wrap
	}
	Shader = ../../../ships/terran/thruster_small/particles/thruster_plume.shader
	Size = [2.5/1.5, 0.6]
	TargetBlendMode
	{
		SourceRgbFactor = SourceAlpha
		DestRgbFactor = One
		RgbOperator = Add
		SourceAlphaFactor = Zero
		DestAlphaFactor = One
		AlphaOperator = Add
	}
}
Bucket = BulletLower3
RandomTimeOffset = [0, 1]
IntensitySmoothSpeed = 10
RotationSmoothSpeed = 10
SpeedOverIntensity = 0
LengthOverIntensity = [0, 1]
MaxRotationSmoothDelta = 30d
RotationSmoothSkewMode = true""")

# shots/missile_he/particles/missile_he_thruster_plume_light.rules
_VENDOR["plume_light"] = ("shots/missile_he/particles/missile_he_thruster_plume_light.rules", """\
Type = Beam
Sprite
{
	Texture
	{
		File = ../../../ships/terran/thruster_small/particles/thruster_plume_light.png
		SampleMode = Linear
		MipLevels = max
		UVMode = Clamp
	}
	Shader = ../../../ships/terran/thruster_small/particles/thruster_plume_light.shader
	_z = 0.3
	_litReflectiveStrength = 24
	_litAdditiveStrength = 0 //0.8
	_unlitAdditiveStrength = 0 //1
	_nrmlStrengthLimit = 1
	_hotColor = [255, 145, 28, 255]
	_coldColor =  [247, 29, 0, 255]
	_pivot = 1/3
	Size = [6, 3]
	_lightLength = 1.25
	TargetBlendMode
	{
		SourceRgbFactor = InverseDestColor
		DestRgbFactor = One
		RgbOperator = Add
		SourceAlphaFactor = Zero
		DestAlphaFactor = One
		AlphaOperator = Add
	}
}
Bucket = Upper4
RandomTimeOffset = [0, 1]
IntensitySmoothSpeed = 10
RotationSmoothSpeed = 10
SpeedOverIntensity = 0
MaxRotationSmoothDelta = 30d
RotationSmoothSkewMode = true""")

# shots/missile_he/particles/missile_he_thruster_smoke.rules
_VENDOR["smoke_he"] = ("shots/missile_he/particles/missile_he_thruster_smoke.rules", """\
Type = Particles
Def
{
	EmitPerSecond = 0
	EmitPerOneShot = 0
	Initializers
	[
		{
			Type = InheritVelocity
			VelocityInOut = frame_velocity
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = FpsCompensator
			LocationInOut = location
			VelocityIn = frame_velocity
			Mode = Uniform
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = LocationToWorldSpace
			LocationIn = location
			LocationOut = location
			Name = "Convert location to world space."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = VelocityToWorldSpace
			VelocityIn = base_velocity
			VelocityOut = base_velocity
			Name = "Convert velocity to world space"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = AddFrameOfReference
			VelocityInOut = frame_velocity
			Name = "Add frame of reference"
			Enabled = false
			UpdateAfterInit = false
		}
		{
			Type = ScaleToWorldSpace
			ScaleIn = base_scale
			ScaleOut = base_scale
			Name = "Base scale to world space"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = sprite_index
			ValueType = Int
			FromValue = 0
			ToValue = 7
			Name = "Sprite Index"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = UvSprites
			SpriteIndexIn = sprite_index
			UvRectOut = uv_rect
			TextureSize
			{
				X = 256
				Y = 512
			}
			SpriteSize
			{
				X = 128
				Y = 128
			}
			SpriteCount = 8
			SpritesPerRow = 2
			PixelOffset
			{
				X = 0
				Y = 0
			}
			Looping = false
			Name = "Sprite UV Rect"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = rot
			ValueType = Angle
			FromValue = 0d
			ToValue = 360d
			Name = Rotation
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = rot_vel
			ValueType = Angle
			FromValue = -180d
			ToValue = 180d
			Name = "Rot Velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandomHsvColor
			ColorOut = base_color
			HueRange
			{
				Min = 0
				Max = 0
			}
			SaturationRange
			{
				Min = 0
				Max = 0
			}
			ValueRange
			{
				Min = 1.5
				Max = 1.5
			}
			AlphaRange
			{
				Min = 0.05
				Max = 0.08
			}
			Name = "Random base color"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = lifetime
			ValueType = Float
			FromValue = 0.9
			ToValue = 1.1
			Name = "Random Lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetBulletBarrierID
			BarrierIDOut = barrier
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
	]
	Updaters
	[
		{
			Type = VariableLifetime
			LifeInOut = life
			LifetimeIn = lifetime
			Name = "Variable Lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Angle
			AIn = rot
			BIn = rot_vel
			ResultOut = rot
			Operator = AddDt
			Name = "Apply rot velocity."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ColorRamp
			LerpIn = life
			ColorOut = color
			Invert = false
			Colors
			[
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 1
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.78431374
				}
				{
					Rf = 0.78431374
					Gf = 0.78431374
					Bf = 0.78431374
					Af = 0.39215687
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.19607843
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.11764706
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0
				}
			]
			Name = "Alpha ramp"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Color
			AIn = color
			BIn = base_color
			ResultOut = color
			Operator = Multiply
			Name = "Multiply base color with alpha"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Lerp
			LerpIn = life
			DataOut = scale
			Invert = false
			ValueType = Float
			FromValue = 0.4
			ToValue = 1
			Name = "Scale lerp"
			Enabled = true
			UpdateAfterInit = true
		}
		{
			Type = ParticleLightNormal
			LocationIn = location
			LightNormalOut = light_normal
			Name = "Light normal"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Float
			AIn = scale
			BIn = base_scale
			ResultOut = scale
			Operator = Multiply
			Name = "Apply base scale"
			Enabled = true
			UpdateAfterInit = true
		}
		{
			Type = ValueCurve
			MinValue = 0
			MaxValue = 1
			LerpIn = life
			CurveOut = curve
			Invert = false
			Points
			[
				@@C0@@
			]
			Name = "Velocity curve"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Lerp
			LerpIn = curve
			DataOut = life_velocity
			Invert = false
			ValueType = Vector2
			FromValue
			{
				X = 1
				Y = 1
			}
			ToValue
			{
				X = 0.1
				Y = 0.1
			}
			Name = "Velocity over life"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = base_velocity
			BIn = life_velocity
			ResultOut = base_vel2
			Operator = Multiply
			Name = "Apply life velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = base_vel2
			BIn = frame_velocity
			ResultOut = velocity
			Operator = Add
			Name = "add frame velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = location
			BIn = velocity
			ResultOut = location
			Operator = AddDt
			Name = "Apply velocity."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ColorRamp
			LerpIn = curve
			ColorOut = color_add
			Invert = false
			Colors
			[
				{
					Rf = 2
					Gf = 0.9411765
					Bf = 0.84705883
					Af = 0
				}
				{
					Rf = 2
					Gf = 0.9411765
					Bf = 0.84705883
					Af = 0
				}
				{
					Rf = 2
					Gf = 0.9411765
					Bf = 0.84705883
					Af = 0
				}
				{
					Rf = 2
					Gf = 0
					Bf = 0
					Af = 0
				}
				{
					Rf = 2
					Gf = 0
					Bf = 0
					Af = 0
				}
				{
					Rf = 2
					Gf = 0
					Bf = 0
					Af = 0
				}
				{
					Rf = 1.372549
					Gf = 0
					Bf = 0
					Af = 0
				}
				{
					Rf = 0
					Gf = 0
					Bf = 0
					Af = 0
				}
				{
					Rf = 0
					Gf = 0
					Bf = 0
					Af = 0
				}
			]
			Name = "Color shift ramp"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Color
			AIn = color
			BIn = color_add
			ResultOut = color
			Operator = Add
			Name = "Apply color shift"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Color
			AIn = color
			BIn = intensity_alpha
			ResultOut = color
			Operator = Multiply
			Name = "apply intensity alpha"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = OperatorConst
			AIn = scale
			ResultOut = scale
			Operator = Min
			ValueType = Float
			Value = 6
			Name = "Clamp scale"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Barrier
			BarrierIDIn = barrier
			LocationIn = location
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
	]
	Renderer
	{
		Type = LitQuadRenderer
		LightNormalIn = light_normal
		DiffuseShader
		NormalsShader
		{
			File = ../../../common_effects/particles/particle_normals_smoke.shader
		}
		LocationIn = location
		ScaleIn = scale
		Scale2In = scale2
		RotationIn = rot
		ColorIn = color
		UvRectIn = uv_rect
		BaseSize
		{
			X = 1
			Y = 1
		}
		Offset
		{
			X = 0
			Y = 0
		}
		Name = ""
	}
	Material
	{
		Shader
		{
			File = ../../../common_effects/particles/particle_lit_additive.shader
		}
		_normalsTexture
		{
			File = ../../../common_effects/particles/smoke_normals.png
			MipLevels = max
			SampleMode = Linear
		}
		Texture
		{
			File = ../../../common_effects/particles/smoke.png
			MipLevels = 8
			SampleMode = Linear
		}
	}
	DeleteMode = Fast
	EnableMultithreading = false
	InitCapacity = 256
}
EmitterDef
{
	EmitPerSecond = 60
	EmitPerOneShot
	{
		Min = 0
		Max = 0
	}
	PreInitializers
	[
		{
			Type = SetRandomCircle
			LocationOut = location
			Circle
			{
				Center
				{
					X = 0
					Y = 0
				}
				Radius = 0.005
			}
			Perimeter = false
			Name = "Random location in circle"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = base_scale
			ValueType = Float
			FromValue = 4
			ToValue = 5
			Name = "random base scale"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScaleFromIntensity
			ScaleOut = intensity_scale
			ScaleFactor = 1
			IntensityExponent = 0.6
			Name = "get intensity scale"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScaleFromIntensity
			ScaleOut = intensity_velocity
			ScaleFactor = 50
			IntensityExponent = 1
			Name = "get instensity velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandomVelocityFromPoint
			LocationIn = location
			VelocityOut = base_velocity
			Speed
			{
				Min = 1
				Max = 1
			}
			AwayFromPoint
			{
				X = -0.06
				Y = 0
			}
			ConvertPointToWorldSpace = false
			Name = "get base velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScalarOperator
			AIn = intensity_velocity
			DataType = Vector2
			BIn = base_velocity
			ResultOut = base_velocity
			Operator = Multiply
			Name = "apply intensity velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = scale2
			ValueType = Vector2
			FromValue
			{
				X = 0.7
				Y = 0.7
			}
			ToValue
			{
				X = 1.3
				Y = 1.3
			}
			Name = "random scale2"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Float
			AIn = base_scale
			BIn = intensity_scale
			ResultOut = base_scale
			Operator = Multiply
			Name = "apply intensity Scale"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Lerp
			LerpIn = intensity_scale
			DataOut = intensity_alpha
			Invert = false
			ValueType = Color
			FromValue
			{
				Rf = 1
				Gf = 1
				Bf = 1
				Af = 0
			}
			ToValue
			{
				Rf = 1
				Gf = 1
				Bf = 1
				Af = 1
			}
			Name = "apply intensity scale to alpha"
			Enabled = true
			UpdateAfterInit = false
		}
	]
	PostInitializers[]
}
Bucket = Lower1
UseRealTime = false
PenetratingBucket
MinIntensity = 0.2
IsFancy = true
IsFancyLight = false
IsSimple = false
Sharing = Global
UnsharedRenderInWorldSpace = false
DontEmitWhenOffScreen = true
DontEmitWhenOffScreenSizeInflate = 3
UseCustomShapeForOffScreenCheck = false
MaxEmissionZoom = 30
ScaleEmissionWithIntensity = false
ScaleEmissionWithBeamLength = false
ScaleEmissionWithWorldVelocity = false
ScaleEmissionWithPartSize = false
ScaleEmissionWithPartPhysicalSize = false
CaptureBackBuffer = false
Filter
{
	Ships = true
	OperationalHealth = true
	StructuralHealth = true
	OnlyPartCategories
	ExcludePartCategories
	Shields = true
	Bullets = true
	OnlyBulletCategories
	ExcludeBulletCategories
	Crew = true
	Nuggets = true
	IgnoreInvulnerability = true
	Self
	TargetedSelf
	Friendlies = true
	TargetedFriendlies
	Enemies = true
	TargetedEnemies
	Junk = true
	TargetedJunk
}
Delay = 0
IgnoreIntensity = false""")

# shots/missile_nuke/particles/missile_nuke_thruster_smoke.rules
_VENDOR["smoke_nuke"] = ("shots/missile_nuke/particles/missile_nuke_thruster_smoke.rules", """\
Type = Particles
Def
{
	EmitPerSecond = 0
	EmitPerOneShot = 0
	Initializers
	[
		{
			Type = InheritVelocity
			VelocityInOut = frame_velocity
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = base_velocity
			BIn = frame_velocity
			ResultOut = comp_vel
			Operator = Add
			Name = "calculate vel for compensator"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = LocationToWorldSpace
			LocationIn = location
			LocationOut = location
			Name = "Convert location to world space."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = VelocityToWorldSpace
			VelocityIn = base_velocity
			VelocityOut = base_velocity
			Name = "Convert velocity to world space"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = FpsCompensator
			LocationInOut = location
			VelocityIn = comp_vel
			Mode = Uniform
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = AddFrameOfReference
			VelocityInOut = frame_velocity
			Name = "Add frame of reference"
			Enabled = false
			UpdateAfterInit = false
		}
		{
			Type = ScaleToWorldSpace
			ScaleIn = base_scale
			ScaleOut = base_scale
			Name = "Base scale to world space"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = sprite_index
			ValueType = Int
			FromValue = 0
			ToValue = 7
			Name = "Sprite Index"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = UvSprites
			SpriteIndexIn = sprite_index
			UvRectOut = uv_rect
			TextureSize
			{
				X = 256
				Y = 512
			}
			SpriteSize
			{
				X = 128
				Y = 128
			}
			SpriteCount = 8
			SpritesPerRow = 2
			PixelOffset
			{
				X = 0
				Y = 0
			}
			Looping = false
			Name = "Sprite UV Rect"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = rot
			ValueType = Angle
			FromValue = 0d
			ToValue = 360d
			Name = Rotation
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = rot_vel
			ValueType = Angle
			FromValue = -180d
			ToValue = 180d
			Name = "Rot Velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandomHsvColor
			ColorOut = base_color
			HueRange
			{
				Min = 0
				Max = 0
			}
			SaturationRange
			{
				Min = 0
				Max = 0
			}
			ValueRange
			{
				Min = 1.5
				Max = 1.5
			}
			AlphaRange
			{
				Min = 0.05
				Max = 0.08
			}
			Name = "Random base color"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = lifetime
			ValueType = Float
			FromValue = 0.2
			ToValue = 0.3
			Name = "Random Lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetBulletBarrierID
			BarrierIDOut = barrier
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
	]
	Updaters
	[
		{
			Type = VariableLifetime
			LifeInOut = life
			LifetimeIn = lifetime
			Name = "Variable Lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Angle
			AIn = rot
			BIn = rot_vel
			ResultOut = rot
			Operator = AddDt
			Name = "Apply rot velocity."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ColorRamp
			LerpIn = life
			ColorOut = color
			Invert = false
			Colors
			[
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 1
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.78431374
				}
				{
					Rf = 0.78431374
					Gf = 0.78431374
					Bf = 0.78431374
					Af = 0.39215687
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.19607843
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.11764706
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0
				}
			]
			Name = "Alpha ramp"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Color
			AIn = color
			BIn = base_color
			ResultOut = color
			Operator = Multiply
			Name = "Multiply base color with alpha"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Lerp
			LerpIn = life
			DataOut = scale
			Invert = false
			ValueType = Float
			FromValue = 0.4
			ToValue = 1
			Name = "Scale lerp"
			Enabled = true
			UpdateAfterInit = true
		}
		{
			Type = ParticleLightNormal
			LocationIn = location
			LightNormalOut = light_normal
			Name = "Light normal"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Float
			AIn = scale
			BIn = base_scale
			ResultOut = scale
			Operator = Multiply
			Name = "Apply base scale"
			Enabled = true
			UpdateAfterInit = true
		}
		{
			Type = ValueCurve
			MinValue = 0
			MaxValue = 1
			LerpIn = life
			CurveOut = curve
			Invert = false
			Points
			[
				@@C0@@
			]
			Name = "Velocity curve"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Lerp
			LerpIn = curve
			DataOut = life_velocity
			Invert = false
			ValueType = Vector2
			FromValue
			{
				X = 1
				Y = 1
			}
			ToValue
			{
				X = 0.1
				Y = 0.1
			}
			Name = "Velocity over life"
			Enabled = false
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = base_velocity
			BIn = life_velocity
			ResultOut = base_vel2
			Operator = Multiply
			Name = "Apply life velocity"
			Enabled = false
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = base_velocity
			BIn = frame_velocity
			ResultOut = velocity
			Operator = Add
			Name = "add frame velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = location
			BIn = velocity
			ResultOut = location
			Operator = AddDt
			Name = "Apply velocity."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ColorRamp
			LerpIn = curve
			ColorOut = color_add
			Invert = false
			Colors
			[
				{
					Rf = 2
					Gf = 0.9411765
					Bf = 0.84705883
					Af = 0
				}
				{
					Rf = 2
					Gf = 0.9411765
					Bf = 0.84705883
					Af = 0
				}
				{
					Rf = 2
					Gf = 0.9411765
					Bf = 0.84705883
					Af = 0
				}
				{
					Rf = 2
					Gf = 0
					Bf = 0
					Af = 0
				}
				{
					Rf = 2
					Gf = 0
					Bf = 0
					Af = 0
				}
				{
					Rf = 2
					Gf = 0
					Bf = 0
					Af = 0
				}
				{
					Rf = 1.372549
					Gf = 0
					Bf = 0
					Af = 0
				}
				{
					Rf = 0
					Gf = 0
					Bf = 0
					Af = 0
				}
				{
					Rf = 0
					Gf = 0
					Bf = 0
					Af = 0
				}
			]
			Name = "Color shift ramp"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Color
			AIn = color
			BIn = color_add
			ResultOut = color
			Operator = Add
			Name = "Apply color shift"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Color
			AIn = color
			BIn = intensity_alpha
			ResultOut = color
			Operator = Multiply
			Name = "apply intensity alpha"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = OperatorConst
			AIn = scale
			ResultOut = scale
			Operator = Min
			ValueType = Float
			Value = 6
			Name = "Clamp scale"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Barrier
			BarrierIDIn = barrier
			LocationIn = location
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
	]
	Renderer
	{
		Type = LitQuadRenderer
		LightNormalIn = light_normal
		DiffuseShader
		NormalsShader
		{
			File = ../../../common_effects/particles/particle_normals_smoke.shader
		}
		LocationIn = location
		ScaleIn = scale
		Scale2In = scale2
		RotationIn = rot
		ColorIn = color
		UvRectIn = uv_rect
		BaseSize
		{
			X = 1
			Y = 1
		}
		Offset
		{
			X = 0
			Y = 0
		}
		Name = ""
	}
	Material
	{
		Shader
		{
			File = ../../../common_effects/particles/particle_lit_additive.shader
		}
		_normalsTexture
		{
			File = ../../../common_effects/particles/smoke_normals.png
			MipLevels = max
			SampleMode = Linear
		}
		Texture
		{
			File = ../../../common_effects/particles/smoke.png
			MipLevels = 8
			SampleMode = Linear
		}
	}
	DeleteMode = Fast
	EnableMultithreading = false
	InitCapacity = 256
}
EmitterDef
{
	EmitPerSecond = 800
	EmitPerOneShot
	{
		Min = 0
		Max = 0
	}
	PreInitializers
	[
		{
			Type = SetRandomCircle
			LocationOut = location
			Circle
			{
				Center
				{
					X = 0
					Y = 0
				}
				Radius = 0.005
			}
			Perimeter = false
			Name = "Random location in circle"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = base_scale
			ValueType = Float
			FromValue = 4
			ToValue = 5
			Name = "random base scale"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScaleFromIntensity
			ScaleOut = intensity_scale
			ScaleFactor = 1
			IntensityExponent = 0.6
			Name = "get intensity scale"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScaleFromIntensity
			ScaleOut = intensity_velocity
			ScaleFactor = 50
			IntensityExponent = 1
			Name = "get instensity velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandomVelocityFromPoint
			LocationIn = location
			VelocityOut = base_velocity
			Speed
			{
				Min = 1
				Max = 1
			}
			AwayFromPoint
			{
				X = -0.06
				Y = 0
			}
			ConvertPointToWorldSpace = false
			Name = "get base velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScalarOperator
			AIn = intensity_velocity
			DataType = Vector2
			BIn = base_velocity
			ResultOut = base_velocity
			Operator = Multiply
			Name = "apply intensity velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = scale2
			ValueType = Vector2
			FromValue
			{
				X = 0.7
				Y = 0.7
			}
			ToValue
			{
				X = 1.3
				Y = 1.3
			}
			Name = "random scale2"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Float
			AIn = base_scale
			BIn = intensity_scale
			ResultOut = base_scale
			Operator = Multiply
			Name = "apply intensity Scale"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Lerp
			LerpIn = intensity_scale
			DataOut = intensity_alpha
			Invert = false
			ValueType = Color
			FromValue
			{
				Rf = 1
				Gf = 1
				Bf = 1
				Af = 0
			}
			ToValue
			{
				Rf = 1
				Gf = 1
				Bf = 1
				Af = 1
			}
			Name = "apply intensity scale to alpha"
			Enabled = true
			UpdateAfterInit = false
		}
	]
	PostInitializers[]
}
Bucket = Lower1
UseRealTime = false
PenetratingBucket
MinIntensity = 0.2
IsFancy = true
IsFancyLight = false
IsSimple = false
Sharing = Global
UnsharedRenderInWorldSpace = false
DontEmitWhenOffScreen = true
DontEmitWhenOffScreenSizeInflate = 3
UseCustomShapeForOffScreenCheck = false
MaxEmissionZoom = 30
ScaleEmissionWithIntensity = false
ScaleEmissionWithBeamLength = false
ScaleEmissionWithWorldVelocity = false
ScaleEmissionWithPartSize = false
ScaleEmissionWithPartPhysicalSize = false
CaptureBackBuffer = false
Filter
{
	Ships = true
	OperationalHealth = true
	StructuralHealth = true
	OnlyPartCategories
	ExcludePartCategories
	Shields = true
	Bullets = true
	OnlyBulletCategories
	ExcludeBulletCategories
	Crew = true
	Nuggets = true
	IgnoreInvulnerability = true
	Self
	TargetedSelf
	Friendlies = true
	TargetedFriendlies
	Enemies = true
	TargetedEnemies
	Junk = true
	TargetedJunk
}
Delay = 0
IgnoreIntensity = false""")

# shots/missile_thermal/particles/missile_thermal_thruster_fire.rules
_VENDOR["fire_he"] = ("shots/missile_thermal/particles/missile_thermal_thruster_fire.rules", """\
Type = Particles
Def
{
	EmitPerSecond = 0
	EmitPerOneShot = 0
	Initializers
	[
		{
			Type = InheritVelocity
			VelocityInOut = frame_velocity
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = LocationToWorldSpace
			LocationIn = location
			LocationOut = location
			Name = "Convert location to world space."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = FpsCompensator
			LocationInOut = location
			VelocityIn = frame_velocity
			Mode = Uniform
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = VelocityToWorldSpace
			VelocityIn = base_velocity
			VelocityOut = base_velocity
			Name = "Convert velocity to world space"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = AlignToVelocity
			VelocityIn = base_velocity
			RotationInOut = rot
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScaleToWorldSpace
			ScaleIn = base_scale
			ScaleOut = base_scale
			Name = "Base scale to world space"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = sprite_index
			ValueType = Int
			FromValue = 0
			ToValue = 7
			Name = "Sprite Index"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = UvSprites
			SpriteIndexIn = sprite_index
			UvRectOut = uv_rect
			TextureSize
			{
				X = 256
				Y = 512
			}
			SpriteSize
			{
				X = 128
				Y = 128
			}
			SpriteCount = 8
			SpritesPerRow = 2
			PixelOffset
			{
				X = 0
				Y = 0
			}
			Looping = false
			Name = "Sprite UV Rect"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = lifetime
			ValueType = Float
			FromValue = 0.2
			ToValue = 0.3
			Name = "Random Lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandomHsvColor
			ColorOut = hue
			HueRange
			{
				Min = 90
				Max = 90
			}
			SaturationRange
			{
				Min = 1
				Max = 1
			}
			ValueRange
			{
				Min = 1
				Max = 1
			}
			AlphaRange
			{
				Min = 1
				Max = 1
			}
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
	]
	Updaters
	[
		{
			Type = VariableLifetime
			LifeInOut = life
			LifetimeIn = lifetime
			Name = "Variable Lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ValueCurve
			MinValue = 1
			MaxValue = 0.2
			LerpIn = life
			CurveOut = curve
			Invert = false
			Points
			[
				@@C0@@
			]
			Name = "Velocity curve"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ColorRamp
			LerpIn = curve
			ColorOut = color
			Invert = false
			Colors
			[
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.15686275
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.47058824
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.15686275
				}
			]
			Name = "Color ramp"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScalarOperator
			AIn = curve
			DataType = Vector2
			BIn = base_velocity
			ResultOut = base_vel2
			Operator = Multiply
			Name = "apply velocity curve to base velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = frame_velocity
			BIn = base_vel2
			ResultOut = velocity
			Operator = Add
			Name = "add frame and base velocity to velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = location
			BIn = velocity
			ResultOut = location
			Operator = AddDt
			Name = "Apply velocity."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Lerp
			LerpIn = life
			DataOut = life_scale
			Invert = false
			ValueType = Float
			FromValue = 1
			ToValue = 0
			Name = "Scale over lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ValueCurve
			MinValue = 2
			MaxValue = 0
			LerpIn = life
			CurveOut = x_curve
			Invert = false
			Points
			[
				@@C1@@
			]
			Name = "scale X curve"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ConstructVector2
			DataXIn = x_curve
			DataYIn = life_scale
			DataOut = xy_scale
			Name = "construct scale2"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScalarOperator
			AIn = base_scale
			DataType = Vector2
			BIn = xy_scale
			ResultOut = scale2
			Operator = Multiply
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Angle
			AIn = rot
			BIn = rot_vel
			ResultOut = rot
			Operator = AddDt
			Name = "Apply rot vel"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = OperatorConst
			AIn = scale2
			ResultOut = scale2
			Operator = Min
			ValueType = Vector2
			Value
			{
				X = 2
				Y = 1
			}
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Color
			AIn = hue
			BIn = color
			ResultOut = color
			Operator = Multiply
			Name = "combine color and alpha"
			Enabled = true
			UpdateAfterInit = false
		}
	]
	Renderer
	{
		Type = StandardQuadRenderer
		LocationIn = location
		ScaleIn
		Scale2In = scale2
		RotationIn = rot
		ColorIn = color
		UvRectIn = uv_rect
		BaseSize
		{
			X = 1
			Y = 1
		}
		Offset
		{
			X = 0
			Y = 0
		}
		Name = ""
	}
	Material
	{
		Texture
		{
			File = ../../../common_effects/particles/fire.png
			SampleMode = Linear
		}
		TargetBlendMode
		{
			SourceRgbFactor = SourceAlpha
			DestRgbFactor = One
			RgbOperator = Add
			SourceAlphaFactor = InverseDestAlpha
			DestAlphaFactor = One
			AlphaOperator = Add
		}
	}
	DeleteMode = Fast
	EnableMultithreading = false
	InitCapacity = 256
}
EmitterDef
{
	EmitPerSecond = 800
	EmitPerOneShot
	{
		Min = 0
		Max = 0
	}
	PreInitializers
	[
		{
			Type = SetRandomCircle
			LocationOut = location
			Circle
			{
				Center
				{
					X = 0
					Y = 0
				}
				Radius = 0.005
			}
			Perimeter = false
			Name = "Random location in circle"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandomVelocityFromPoint
			LocationIn = location
			VelocityOut = point_vel
			Speed
			{
				Min = 1
				Max = 1
			}
			AwayFromPoint
			{
				X = -0.015
				Y = 0
			}
			ConvertPointToWorldSpace = false
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScaleFromIntensity
			ScaleOut = initial_velocity
			ScaleFactor = 70
			IntensityExponent = 1
			Name = "initial velocity from intensity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScalarOperator
			AIn = initial_velocity
			DataType = Vector2
			BIn = point_vel
			ResultOut = base_velocity
			Operator = Multiply
			Name = "create base velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScaleFromIntensity
			ScaleOut = loc_intensity
			ScaleFactor = 1
			IntensityExponent = 2
			Name = "get location intensity"
			Enabled = false
			UpdateAfterInit = false
		}
		{
			Type = ScaleFromIntensity
			ScaleOut = intensity
			ScaleFactor = 1
			IntensityExponent = 1
			Name = "get scale intensity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = VelocityFromIntensity
			VelocityOut = loc_offset
			VelocityFactor
			{
				X = 0.35
				Y = 0
			}
			IntensityExponent = 2
			Name = "location offset from Intensity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = OperatorConst
			AIn = loc_offset
			ResultOut = loc_offset
			Operator = Min
			ValueType = Vector2
			Value
			{
				X = 0.35
				Y = 0
			}
			Name = "clamp location offset"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = loc_offset
			BIn = location
			ResultOut = location
			Operator = Add
			Name = "apply location offset"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = rand_scale
			ValueType = Float
			FromValue = 0.7
			ToValue = 0.9
			Name = "random scale"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Float
			AIn = intensity
			BIn = rand_scale
			ResultOut = base_scale
			Operator = Multiply
			Name = "apply random scale"
			Enabled = true
			UpdateAfterInit = false
		}
	]
	PostInitializers[]
}
Bucket = Lower2
UseRealTime = false
PenetratingBucket
MinIntensity = 0
IsFancy = true
IsFancyLight = false
IsSimple = false
Sharing = Global
UnsharedRenderInWorldSpace = false
DontEmitWhenOffScreen = true
DontEmitWhenOffScreenSizeInflate = 3
UseCustomShapeForOffScreenCheck = false
ScaleEmissionWithIntensity = true
ScaleEmissionWithBeamLength = false
ScaleEmissionWithWorldVelocity = false
ScaleEmissionWithPartSize = false
ScaleEmissionWithPartPhysicalSize = false
CaptureBackBuffer = false
Filter
{
	Ships = true
	OperationalHealth = true
	StructuralHealth = true
	OnlyPartCategories
	ExcludePartCategories
	Shields = true
	Bullets = true
	OnlyBulletCategories
	ExcludeBulletCategories
	Crew = true
	Nuggets = true
	IgnoreInvulnerability = true
	Self
	TargetedSelf
	Friendlies = true
	TargetedFriendlies
	Enemies = true
	TargetedEnemies
	Junk = true
	TargetedJunk
}
Delay = 0
IgnoreIntensity = false""")

# shots/missile_nuke/particles/missile_nuke_thruster_fire.rules
_VENDOR["fire_nuke"] = ("shots/missile_nuke/particles/missile_nuke_thruster_fire.rules", """\
Type = Particles
Def
{
	EmitPerSecond = 0
	EmitPerOneShot = 0
	Initializers
	[
		{
			Type = FpsCompensator
			LocationInOut = location
			VelocityIn = base_velocity
			Mode = Uniform
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = LocationToWorldSpace
			LocationIn = location
			LocationOut = location
			Name = "Convert location to world space."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = VelocityToWorldSpace
			VelocityIn = base_velocity
			VelocityOut = base_velocity
			Name = "Convert velocity to world space"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = AlignToVelocity
			VelocityIn = base_velocity
			RotationInOut = rot
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = AddFrameOfReference
			VelocityInOut = frame_velocity
			Name = "Add frame of reference"
			Enabled = false
			UpdateAfterInit = false
		}
		{
			Type = ScaleToWorldSpace
			ScaleIn = base_scale
			ScaleOut = base_scale
			Name = "Base scale to world space"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = sprite_index
			ValueType = Int
			FromValue = 0
			ToValue = 7
			Name = "Sprite Index"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = UvSprites
			SpriteIndexIn = sprite_index
			UvRectOut = uv_rect
			TextureSize
			{
				X = 256
				Y = 512
			}
			SpriteSize
			{
				X = 128
				Y = 128
			}
			SpriteCount = 8
			SpritesPerRow = 2
			PixelOffset
			{
				X = 0
				Y = 0
			}
			Looping = false
			Name = "Sprite UV Rect"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = lifetime
			ValueType = Float
			FromValue = 0.2
			ToValue = 0.3
			Name = "Random Lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandomHsvColor
			ColorOut = hue
			HueRange
			{
				Min = 90
				Max = 90
			}
			SaturationRange
			{
				Min = 1
				Max = 1
			}
			ValueRange
			{
				Min = 1
				Max = 1
			}
			AlphaRange
			{
				Min = 1
				Max = 1
			}
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = InheritVelocity
			VelocityInOut = frame_velocity
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
	]
	Updaters
	[
		{
			Type = VariableLifetime
			LifeInOut = life
			LifetimeIn = lifetime
			Name = "Variable Lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ValueCurve
			MinValue = 1
			MaxValue = 0.2
			LerpIn = life
			CurveOut = curve
			Invert = false
			Points
			[
				@@C0@@
			]
			Name = "Velocity curve"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ColorRamp
			LerpIn = curve
			ColorOut = color
			Invert = false
			Colors
			[
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.15686275
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.47058824
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.15686275
				}
			]
			Name = "Color ramp"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScalarOperator
			AIn = curve
			DataType = Vector2
			BIn = base_velocity
			ResultOut = base_vel2
			Operator = Multiply
			Name = "apply velocity curve to base velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = frame_velocity
			BIn = base_vel2
			ResultOut = velocity
			Operator = Add
			Name = "add frame and base velocity to velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = location
			BIn = velocity
			ResultOut = location
			Operator = AddDt
			Name = "Apply velocity."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Lerp
			LerpIn = life
			DataOut = life_scale
			Invert = false
			ValueType = Float
			FromValue = 1
			ToValue = 0
			Name = "Scale over lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ValueCurve
			MinValue = 2
			MaxValue = 0
			LerpIn = life
			CurveOut = x_curve
			Invert = false
			Points
			[
				@@C1@@
			]
			Name = "scale X curve"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ConstructVector2
			DataXIn = x_curve
			DataYIn = life_scale
			DataOut = xy_scale
			Name = "construct scale2"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Float
			AIn = life_scale
			BIn = base_scale
			ResultOut = scale
			Operator = Multiply
			Name = "Apply scale over lifetime"
			Enabled = false
			UpdateAfterInit = false
		}
		{
			Type = ScalarOperator
			AIn = base_scale
			DataType = Vector2
			BIn = xy_scale
			ResultOut = scale2
			Operator = Multiply
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Angle
			AIn = rot
			BIn = rot_vel
			ResultOut = rot
			Operator = AddDt
			Name = "Apply rot vel"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = OperatorConst
			AIn = scale2
			ResultOut = scale2
			Operator = Min
			ValueType = Vector2
			Value
			{
				X = 2
				Y = 1
			}
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Color
			AIn = hue
			BIn = color
			ResultOut = color
			Operator = Multiply
			Name = "combine color and alpha"
			Enabled = true
			UpdateAfterInit = false
		}
	]
	Renderer
	{
		Type = StandardQuadRenderer
		LocationIn = location
		ScaleIn
		Scale2In = scale2
		RotationIn = rot
		ColorIn = color
		UvRectIn = uv_rect
		BaseSize
		{
			X = 1
			Y = 1
		}
		Offset
		{
			X = 0
			Y = 0
		}
		Name = ""
	}
	Material
	{
		Texture
		{
			File = ../../../common_effects/particles/fire.png
			SampleMode = Linear
		}
		TargetBlendMode
		{
			SourceRgbFactor = SourceAlpha
			DestRgbFactor = One
			RgbOperator = Add
			SourceAlphaFactor = InverseDestAlpha
			DestAlphaFactor = One
			AlphaOperator = Add
		}
	}
	DeleteMode = Fast
	EnableMultithreading = false
	InitCapacity = 256
}
EmitterDef
{
	EmitPerSecond = 800
	EmitPerOneShot
	{
		Min = 0
		Max = 0
	}
	PreInitializers
	[
		{
			Type = SetRandomCircle
			LocationOut = location
			Circle
			{
				Center
				{
					X = 0
					Y = 0
				}
				Radius = 0.005
			}
			Perimeter = false
			Name = "Random location in circle"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandomVelocityFromPoint
			LocationIn = location
			VelocityOut = point_vel
			Speed
			{
				Min = 1
				Max = 1
			}
			AwayFromPoint
			{
				X = -0.015
				Y = 0
			}
			ConvertPointToWorldSpace = false
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScaleFromIntensity
			ScaleOut = initial_velocity
			ScaleFactor = 70
			IntensityExponent = 1
			Name = "initial velocity from intensity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScalarOperator
			AIn = initial_velocity
			DataType = Vector2
			BIn = point_vel
			ResultOut = base_velocity
			Operator = Multiply
			Name = "create base velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScaleFromIntensity
			ScaleOut = loc_intensity
			ScaleFactor = 1
			IntensityExponent = 2
			Name = "get location intensity"
			Enabled = false
			UpdateAfterInit = false
		}
		{
			Type = ScaleFromIntensity
			ScaleOut = intensity
			ScaleFactor = 1
			IntensityExponent = 1
			Name = "get scale intensity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Lerp
			LerpIn = loc_intensity
			DataOut = loc_offset
			Invert = false
			ValueType = Vector2
			FromValue
			{
				X = 0
				Y = 0
			}
			ToValue
			{
				X = 0.65
				Y = 0
			}
			Name = "create location offset from intensity"
			Enabled = false
			UpdateAfterInit = false
		}
		{
			Type = VelocityFromIntensity
			VelocityOut = loc_offset
			VelocityFactor
			{
				X = 0.35
				Y = 0
			}
			IntensityExponent = 2
			Name = "location offset from Intensity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = OperatorConst
			AIn = loc_offset
			ResultOut = loc_offset
			Operator = Min
			ValueType = Vector2
			Value
			{
				X = 0.35
				Y = 0
			}
			Name = "clamp location offset"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = loc_offset
			BIn = location
			ResultOut = location
			Operator = Add
			Name = "apply location offset"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = rand_scale
			ValueType = Float
			FromValue = 0.7
			ToValue = 0.9
			Name = "random scale"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Float
			AIn = intensity
			BIn = rand_scale
			ResultOut = base_scale
			Operator = Multiply
			Name = "apply random scale"
			Enabled = true
			UpdateAfterInit = false
		}
	]
	PostInitializers[]
}
Bucket = Lower2
UseRealTime = false
PenetratingBucket
MinIntensity = 0
IsFancy = true
IsFancyLight = false
IsSimple = false
Sharing = Global
UnsharedRenderInWorldSpace = false
DontEmitWhenOffScreen = true
DontEmitWhenOffScreenSizeInflate = 3
UseCustomShapeForOffScreenCheck = false
ScaleEmissionWithIntensity = true
ScaleEmissionWithBeamLength = false
ScaleEmissionWithWorldVelocity = false
ScaleEmissionWithPartSize = false
ScaleEmissionWithPartPhysicalSize = false
CaptureBackBuffer = false
Filter
{
	Ships = true
	OperationalHealth = true
	StructuralHealth = true
	OnlyPartCategories
	ExcludePartCategories
	Shields = true
	Bullets = true
	OnlyBulletCategories
	ExcludeBulletCategories
	Crew = true
	Nuggets = true
	IgnoreInvulnerability = true
	Self
	TargetedSelf
	Friendlies = true
	TargetedFriendlies
	Enemies = true
	TargetedEnemies
	Junk = true
	TargetedJunk
}
Delay = 0
IgnoreIntensity = false""")

# ships/terran/cannon_deck/particles/cannon_smoke_deck.rules
_VENDOR["roof_smoke"] = ("ships/terran/cannon_deck/particles/cannon_smoke_deck.rules", """\
Type = Particles
Def
{
	EmitPerSecond = 0
	EmitPerOneShot = 0
	Initializers
	[
		{
			Type = LocationToWorldSpace
			LocationIn = location
			LocationOut = location
			Name = "Convert location to world space."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = VelocityToWorldSpace
			VelocityIn = velocity
			VelocityOut = velocity
			Name = "Convert velocity to world space"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = AddFrameOfReference
			VelocityInOut = velocity
			Name = "Add frame of reference"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScaleToWorldSpace
			ScaleIn = base_scale
			ScaleOut = base_scale
			Name = "Base scale to world space"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = sprite_index
			ValueType = Int
			FromValue = 0
			ToValue = 7
			Name = "Sprite Index"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = UvSprites
			SpriteIndexIn = sprite_index
			UvRectOut = uv_rect
			TextureSize
			{
				X = 256
				Y = 512
			}
			SpriteSize
			{
				X = 128
				Y = 128
			}
			SpriteCount = 8
			SpritesPerRow = 2
			PixelOffset
			{
				X = 0
				Y = 0
			}
			Name = "Sprite UV Rect"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = rot
			ValueType = Angle
			FromValue = 0d
			ToValue = 360d
			Name = Rotation
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = rot_vel
			ValueType = Angle
			FromValue = -19.999998d
			ToValue = 19.999998d
			Name = "Rot Velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandomHsvColor
			ColorOut = base_color
			HueRange
			{
				Min = 0
				Max = 0
			}
			SaturationRange
			{
				Min = 0
				Max = 0
			}
			ValueRange
			{
				Min = 0.4
				Max = 0.8
			}
			AlphaRange
			{
				Min = 0.2
				Max = 0.2
			}
			Name = "Random base color"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = lifetime
			ValueType = Float
			FromValue = 0.5
			ToValue = 1
			Name = "Random Lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
	]
	Updaters
	[
		{
			Type = VariableLifetime
			LifeInOut = life
			LifetimeIn = lifetime
			Name = "Variable Lifetime"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Vector2
			AIn = location
			BIn = velocity
			ResultOut = location
			Operator = AddDt
			Name = "Apply velocity."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Angle
			AIn = rot
			BIn = rot_vel
			ResultOut = rot
			Operator = AddDt
			Name = "Apply rot velocity."
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ColorRamp
			LerpIn = life
			ColorOut = color
			Invert = false
			Colors
			[
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 1
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 1
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.39215687
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0
				}
			]
			Name = "Alpha ramp"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Color
			AIn = color
			BIn = base_color
			ResultOut = color
			Operator = Multiply
			Name = "Multiply base color with alpha"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Lerp
			LerpIn = life
			DataOut = scale
			Invert = false
			ValueType = Float
			FromValue = 1
			ToValue = 3
			Name = "Scale lerp"
			Enabled = true
			UpdateAfterInit = true
		}
		{
			Type = ParticleLightNormal
			LocationIn = location
			LightNormalOut = light_normal
			Name = "Light normal"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Float
			AIn = scale
			BIn = base_scale
			ResultOut = scale
			Operator = Multiply
			Name = "Apply base scale"
			Enabled = true
			UpdateAfterInit = true
		}
	]
	Renderer
	{
		Type = LitQuadRenderer
		LightNormalIn = light_normal
		DiffuseShader
		NormalsShader
		{
			File = ../../../../common_effects/particles/particle_normals_smoke.shader
		}
		LocationIn = location
		ScaleIn = scale
		Scale2In
		RotationIn = rot
		ColorIn = color
		UvRectIn = uv_rect
		BaseSize
		{
			X = 1.5
			Y = 1.5
		}
		Offset
		{
			X = 0
			Y = 0
		}
		Name = ""
	}
	Material
	{
		Shader
		{
			File = ../../../../common_effects/particles/particle_lit_additive.shader
		}
		_normalsTexture
		{
			File = ../../../../common_effects/particles/smoke_normals.png
			MipLevels = max
			SampleMode = Linear
		}
		Texture
		{
			File = ../../../../common_effects/particles/smoke.png
			MipLevels = 8
			SampleMode = Linear
		}
	}
	DeleteMode = Fast
	EnableMultithreading = false
	InitCapacity = 256
}
EmitterDef
{
	EmitPerSecond = 0
	EmitPerOneShot
	{
		Min = 10
		Max = 10
	}
	PreInitializers
	[
		{
			Type = SetRandomVelocity
			VelocityOut = velocity
			Speed
			{
				Min = 4
				Max = 8
			}
			Direction
			{
				Min = -9.999999d
				Max = 9.999999d
			}
			Name = "Initial velocity"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandomCircle
			LocationOut = location
			Circle
			{
				Center
				{
					X = -0.6
					Y = 0
				}
				Radius = 0.5
			}
			Perimeter = false
			Name = "Random location in circle"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetValue
			DataOut = base_scale
			ValueType = Float
			Value = 1
			Name = "Base scale"
			Enabled = false
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = base_scale
			ValueType = Float
			FromValue = 1
			ToValue = 2
			Name = "random scale"
			Enabled = true
			UpdateAfterInit = false
		}
	]
	PostInitializers[]
}
Bucket = RoofCannonSmoke
UseRealTime = false
PenetratingBucket
MinIntensity = 0
IsFancy = true
IsFancyLight = false
IsSimple = false
Sharing = Global
UnsharedRenderInWorldSpace = false
DontEmitWhenOffScreen = true
DontEmitWhenOffScreenSizeInflate = 3
UseCustomShapeForOffScreenCheck = false
MaxEmissionZoom = 15
ScaleEmissionWithIntensity = true
ScaleEmissionWithBeamLength = false
ScaleEmissionWithWorldVelocity = false
ScaleEmissionWithPartSize = false
ScaleEmissionWithPartPhysicalSize = false
CaptureBackBuffer = false
Filter
{
	Ships = true
	OperationalHealth = true
	StructuralHealth = true
	OnlyPartCategories
	ExcludePartCategories
	Shields = true
	Bullets = true
	OnlyBulletCategories
	ExcludeBulletCategories
	Crew = true
	Nuggets = true
	IgnoreInvulnerability = true
	Self
	TargetedSelf
	Friendlies = true
	TargetedFriendlies
	Enemies = true
	TargetedEnemies
	Junk = true
	TargetedJunk
}
Delay = 0
IgnoreIntensity = false""")
