"""Efeitos por CALIBRE do Bullet Strike 2.0 (WP03; modulo FX do registro do build_mod, API 2): arma maior, tiro maior.

Fonte dos numeros: tools/spec/bullet_strike_vfx.json (tabela da Fase B re-chaveada pelas municoes 2.0 he/ap/sap/ac/
frag + os efeitos 2.0) e SPEC.art_assets (tools/spec/bullet_strike_art2.json: palette, shell_ladder, seam_tier_map,
phase_b_leftovers, effects.ac/.frag). So VISUAL (CONTRATOS R4): nunca muda HitEffects, dano, raio, Physics,
Targetable.Health, alcance, velocidade, municao, toggles ou tempos; so MediaEffects, MediaEffectsScale, componentes de
sprite/luz e arquivos de particula proprios. Plasma (s["plasma_fx"], linhas com mm = null) fica de fora.

Ganchos e seams (o build_mod chama annotate depois do shots(DATA) de TODOS os modulos, J2R3-13):
  annotate(DATA)                  D1: chaves visuais nos tiros de GUNS[].modes[] (por 'index'/'key'), nos feixes e
                                      fragmentos de DEFENSES por modo e, em DATA.SHOTS, a arte dos tiros com
                                      art_key/art_tier de outros modulos (PEM do WP08 'pem_s/m/l', slug do WP09);
                                      efeitos de boca das armas/defesas (g["fx"] / d["fx"]);
  write(out, header)              B2: copias escaladas em shots/bs_cal_fx/ + efeitos proprios em shots/bs_ac_fx/
                                      (AC_BLAST) e shots/bs_frag_fx/ (FRAG_BURST);
  copy_art(out)                   B3: PNGs de art3d/bs_shells2 -> shots/bs_shell_art/;
  projectile_components(s, trail) S1: visual em voo (tracante, granada 2.0 da escada, fragmento da FRAG);
  decorate(s, top)                S3: midia de impacto (presets + MediaEffectsScale), pecas atravessadas com PEN,
                                      fim da AP com o preset cheio uma vez, abatido = POP, rajada HE/FRAG das defesas,
                                      faisca do fragmento;
  pen_effect(art_tier) / pop_effect(art_tier)   seam do WP02 (SPEC.art_assets.seam_tier_map): lista de MediaEffects
                                      ('&<...>') ou None (tier fora da tabela / plasma: o chamador mantem o efeito antigo);
  art_key(ammo, tier, s) / art_item(key) / art_body(key) / art_components(...) / art_anchor(key, nome)
                                      arte de voo de art3d/bs_shells2 para quem escreve o proprio tiro (WP08, WP09).
Switches: art.light_split (fxkit.light_pair), art.pen_media (light | full = Fase B), art.frag_cone (cone | radial).

Dois mecanismos (caliber_design 1.A / 1.B):
  * impactos: arquivos vanilla por referencia + MediaEffectsScale (numero puro) no bloco de acerto. Campo vanilla
    em bloco de acerto: shots/bullet_railgun/bullet_railgun.rules l.99/139/173 (0.30.3); numero puro no SW:ACD
    (alvo 0.30.4): shots/missiles/proton_rocket/proton_rocket.rules l.129/187 ("MediaEffectsScale = 1.5");
  * boca, rastros e baforadas: COPIAS escaladas (scaled_copy) de arquivos vanilla guardados em tools/vanilla_fx/ (e
    tools/vanilla_fx/ammo2/ para as fontes 2.0). A copia multiplica so o Renderer.BaseSize (nunca tambem LocalScale/
    base_scale: daria s^2), mais posicoes/velocidades (s), quantidade (n), vida (life), Delay e Bucket, e cada botao
    confere quantos campos achou (texto vanilla diferente = build para, nunca tamanho errado em silencio).
Import: so rules_dsl, bsgen.fxkit, bsgen.trails e a biblioteca padrao (nunca bs_data / build_mod / bsgen.shots no
nivel do modulo: shots importa este arquivo). Os switches vem de fxkit.art_switch (bs_data ja carregado).
"""

import copy
import json
import math
import os
import re
import shutil

from rules_dsl import Q, Inh, fmt_num
from bsgen import fxkit as FXK
from bsgen import trails as TR

API = 2

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # tools/
ROOT = os.path.dirname(HERE)                                            # repositorio
SPEC_PATH = os.path.join(HERE, "spec", "bullet_strike_vfx.json")
VENDOR_DIR = os.path.join(HERE, "vanilla_fx")
OUT_DIR = "shots/bs_cal_fx"           # copias escaladas (irma de bs_trails / bs_plasma_fx / bs_nuke_fx)
FX_DIRS = {"ac": "shots/bs_ac_fx", "frag": "shots/bs_frag_fx"}     # efeitos proprios 2.0 (tijolos do fxkit)
TEX_PREFIX = "../bs_fx_tex/"          # texturas de bsgen/fx_tex.py vistas de shots/<pasta>/ (fx_tex.ref)
ART_OUT = "shots/bs_shell_art"        # PNGs das granadas (CONTRATOS secao 3)
ART_SRC = os.path.join(ROOT, "art3d", "bs_shells2")
ART_PREFIX = "../bs_shell_art/"       # visto de shots/<id>/<id>.rules
D = "./Data"

with open(SPEC_PATH, encoding="utf-8") as _fh:
    SPEC = json.load(_fh)
with open(FXK.ART2_PATH, encoding="utf-8") as _fh:
    ART2 = json.load(_fh)["art_assets"]
WEAPONS = SPEC["weapons"]
PRESETS = SPEC["hit_presets"]
OWN_FX = {k: v for k, v in SPEC["own_fx"].items() if not k.startswith("_")}
COUNTS = SPEC["particle_counts"]
LADDER = ART2["shell_ladder"]["items"]          # 18 chaves da escada (he_s ... slug): corpo no jogo
SEAM = ART2["seam_tier_map"]
AMMOS = ("he", "ap", "sap", "ac", "frag")
# cores: a paleta 2.0 do spec (SPEC.art_assets.palette); ammo_colors do json e copia (annotate avisa se divergir)
COLORS = {k: FXK.pal(k) for k in AMMOS}

# ============================================================================= copias escaladas (1.B)
# fontes guardadas em tools/vanilla_fx/[<vendor>/]<nome do arquivo vanilla>.rules (caminho vanilla em SPEC["sources"])
VENDORED = tuple(SPEC["sources"])
# balde da copia quando o vanilla esta num balde de baixo (ficaria sob o nosso teto): FlakShootSmoke e Lower1
DEFAULT_BUCKET = {"FS": "RoofCannonSmoke", "TSM": "BulletTrailUpper"}
# fontes novas = fonte vanilla + trocas fixas
#   SHR_L / SHR_H: estilhacos da flak com 30..40 / 100..120 por rajada (o vanilla solta 150..200)
#   FLS_L / FLS_H: baforada da FRAG (flak_large_smoke pequena, curta e cinza-azulada; sem coluna de fumaca)
TINT_FRAG = ("ramp", 0.8, 1.0, 0.95)
NEW_SOURCES = {
    "SHR_L": ("SHR", {"count": (30, 40)}),
    "SHR_H": ("SHR", {"count": (100, 120)}),
    "FLS_L": ("FLS", {"s": 0.25, "count": (4, 6), "life": 0.36, "color": TINT_FRAG}),
    "FLS_H": ("FLS", {"s": 0.35, "count": (8, 10), "life": 0.36, "color": TINT_FRAG}),
}
# quantos campos cada botao tem de achar em cada fonte (so elementos com Enabled = true). Conferido contra o texto
# vanilla; se o jogo mudar o arquivo, o build para aqui.
#   size: Renderer.BaseSize | loc: SetValue/SetRandom location ou SetRandomCircle no EmitterDef |
#   vel: SetValue/SetRandom velocity, SetRandomVelocity(FromPoint) no EmitterDef | life: Lifetime (updater) e
#   SetRandom lifetime | count: EmitPerOneShot do EmitterDef | eps: EmitPerSecond do EmitterDef
EXPECT = {
    "CG": {"size": 1, "loc": 1, "vel": 0, "life": 1, "count": 1, "eps": 1},
    "CGF": {"size": 1, "loc": 1, "vel": 0, "life": 1, "count": 1, "eps": 1},
    "CGS": {"size": 1, "loc": 1, "vel": 0, "life": 1, "count": 1, "eps": 1},
    "CD": {"size": 1, "loc": 1, "vel": 1, "life": 1, "count": 1, "eps": 1},
    "CDF": {"size": 1, "loc": 0, "vel": 0, "life": 1, "count": 1, "eps": 1},
    "CDR": {"size": 1, "loc": 1, "vel": 1, "life": 1, "count": 1, "eps": 1},
    "CDS": {"size": 1, "loc": 1, "vel": 1, "life": 1, "count": 1, "eps": 1},
    "RGD": {"size": 1, "loc": 1, "vel": 0, "life": 1, "count": 1, "eps": 1},
    "FF": {"size": 1, "loc": 1, "vel": 0, "life": 1, "count": 1, "eps": 1},
    "FS": {"size": 1, "loc": 0, "vel": 1, "life": 1, "count": 1, "eps": 1},
    "SHR": {"size": 1, "loc": 0, "vel": 0, "life": 1, "count": 1, "eps": 1},
    "TSM": {"size": 1, "loc": 1, "vel": 1, "life": 1, "count": 1, "eps": 1},
    "FLS": {"size": 1, "loc": 1, "vel": 1, "life": 1, "count": 1, "eps": 1},
}

_NUM = r"-?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?"
_VENDOR_CACHE = {}


def _num(v):
    """Numero no formato do jogo (inteiro sem ponto; ate 6 casas)."""
    return fmt_num(round(float(v), 6))


def _tag(v):
    return str(int(math.floor(float(v) * 100 + 0.5)))


def _iround(v):
    """Arredondamento comum (0,5 sobe), nunca o 'do banqueiro' do round()."""
    return int(math.floor(float(v) + 0.5))


def _is_ramp(color):
    return isinstance(color, tuple) and len(color) == 4 and color[0] == "ramp"


def vendor_path(src):
    e = SPEC["sources"][src]
    sub = e.get("vendor")
    return os.path.join(VENDOR_DIR, *([sub] if sub else []), os.path.basename(e["file"]))


def vendor_text(src):
    """Texto vanilla da fonte (sem as linhas // do cabecalho do vendor)."""
    if src not in _VENDOR_CACHE:
        with open(vendor_path(src), encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        i = 0
        while i < len(lines) and lines[i].startswith("//"):
            i += 1
        _VENDOR_CACHE[src] = "\n".join(lines[i:])
    return _VENDOR_CACHE[src]


def _sections(text):
    """Faixas do texto: (ini, fim) de Def.Initializers, Def.Updaters, Renderer, Material, EmitterDef, PreInitializers."""
    def idx(pat, start=0):
        m = re.compile(pat, re.M).search(text, start)
        if not m:
            raise ValueError(f"caliber_fx: secao {pat!r} nao achada no texto vanilla")
        return m.start()
    i_def = idx(r"^Def$")
    i_init = idx(r"^\tInitializers$", i_def)
    i_upd = idx(r"^\tUpdaters$", i_init)
    i_rend = idx(r"^\tRenderer$", i_upd)
    i_mat = idx(r"^\tMaterial$", i_rend)
    i_emit = idx(r"^EmitterDef$", i_mat)
    i_pre = idx(r"^\tPreInitializers\b", i_emit)
    i_end = idx(r"^Bucket = ", i_pre)
    return {"init": (i_init, i_upd), "upd": (i_upd, i_rend), "rend": (i_rend, i_mat), "mat": (i_mat, i_emit),
            "emit": (i_emit, i_end), "pre": (i_pre, i_end)}


def _elements(text, sec):
    """Elementos ({ Type = ... } com 2 tabs) de Initializers, Updaters e PreInitializers: (secao, ini, fim, corpo)."""
    out = []
    for m in re.finditer(r"\n\t\t\{\n(.*?)\n\t\t\}", text, re.S):
        a = m.start(1)
        where = next((k for k in ("init", "upd", "pre") if sec[k][0] <= a < sec[k][1]), None)
        if where:
            out.append((where, m.start(1), m.end(1), m.group(1)))
    return out


def _field(body, name):
    m = re.search(rf"^\t\t\t{name} = (\S+)$", body, re.M)
    return m.group(1) if m else None


def _scale_lines(body, names, k):
    """Multiplica por k os numeros das linhas 'Nome = n' (qualquer recuo) com Nome em names."""
    return re.subn(rf"^(\t+(?:{'|'.join(names)}) = )({_NUM})$", lambda m: m.group(1) + _num(float(m.group(2)) * k),
                   body, flags=re.M)


def _scale_block(body, block, names, k):
    """Multiplica os campos names dentro do primeiro sub-bloco 'block { ... }' do elemento."""
    m = re.search(rf"^(\t+){block}\n\1\{{\n(.*?)\n\1\}}", body, re.M | re.S)
    if not m:
        return body, 0
    inner, n = _scale_lines(m.group(2), names, k)
    return body[:m.start(2)] + inner + body[m.end(2):], n


def _rel_to_data(src, path):
    """Caminho relativo do arquivo vanilla -> ./Data/... (a copia mora em BulletStrike/shots/bs_cal_fx/)."""
    base = os.path.dirname(SPEC["sources"][src]["file"])
    return D + "/" + os.path.normpath(os.path.join(base, path)).replace(os.sep, "/")


def _patch(src, s, n, life, speed, delay, bucket, texture, color, count):
    """Texto da copia escalada da fonte vanilla src (ver scaled_copy). Confere as contagens de EXPECT[src]."""
    text = vendor_text(src)
    sec = _sections(text)
    got = {"size": 0, "loc": 0, "vel": 0, "life": 0, "count": 0, "eps": 0}
    reps = []   # (ini, fim, novo)
    dist = s * speed
    for where, a, b, body in _elements(text, sec):
        if _field(body, "Enabled") == "false":
            continue
        typ = _field(body, "Type")
        new = body
        if where == "pre":
            out = _field(body, "DataOut")
            if typ in ("SetValue", "SetRandom") and out in ("location", "velocity"):
                k = s if out == "location" else dist
                new, c = _scale_lines(new, ("X", "Y"), k)
                if not c:
                    raise ValueError(f"caliber_fx {src}: {typ} {out} sem X/Y")
                got["loc" if out == "location" else "vel"] += 1
            elif typ == "SetRandomCircle" and _field(body, "LocationOut") == "location":
                new, c1 = _scale_block(new, "Center", ("X", "Y"), s)
                new, c2 = _scale_lines(new, ("Radius",), s)
                if c1 != 2 or c2 != 1:
                    raise ValueError(f"caliber_fx {src}: SetRandomCircle inesperado ({c1}, {c2})")
                got["loc"] += 1
            elif typ in ("SetRandomVelocity", "SetRandomVelocityFromPoint"):
                new, c = _scale_block(new, "Speed", ("Min", "Max"), dist)
                if c != 2:
                    raise ValueError(f"caliber_fx {src}: {typ} sem Speed Min/Max")
                if typ == "SetRandomVelocityFromPoint":
                    new, c = _scale_block(new, "AwayFromPoint", ("X", "Y"), s)
                    if c != 2:
                        raise ValueError(f"caliber_fx {src}: AwayFromPoint sem X/Y")
                got["vel"] += 1
            elif typ == "SetValue" and out == "base_color" and isinstance(color, tuple) and not _is_ramp(color):
                for ch, v in zip(("Rf", "Gf", "Bf", "Af"), color):
                    new, c = re.subn(rf"^(\t+{ch} = ){_NUM}$", lambda m, v=v: m.group(1) + _num(v), new, flags=re.M)
                    if c != 1:
                        raise ValueError(f"caliber_fx {src}: base_color sem {ch}")
                got["color"] = got.get("color", 0) + 1
        elif where == "upd" and typ == "Lifetime":
            new, c = _scale_lines(new, ("Lifetime",), life)
            if c != 1:
                raise ValueError(f"caliber_fx {src}: Lifetime sem valor")
            got["life"] += 1
        elif where == "init" and typ == "SetRandom" and _field(body, "DataOut") == "lifetime":
            new, c = _scale_lines(new, ("FromValue", "ToValue"), life)
            if c != 2:
                raise ValueError(f"caliber_fx {src}: SetRandom lifetime sem FromValue/ToValue")
            got["life"] += 1
        elif where == "upd" and typ == "ColorRamp" and _field(body, "ColorOut") == "color" and _is_ramp(color):
            # tinge a rampa de cor (RGB de cada chave x tinta; o alfa fica): baforada cinza-azulada da FRAG
            _r, kr, kg, kb = color

            def _tint(m):
                return (f"{m.group(1)}{_num(float(m.group(2)) * kr)}{m.group(3)}{_num(float(m.group(4)) * kg)}"
                        f"{m.group(5)}{_num(float(m.group(6)) * kb)}")
            new, c = re.subn(rf"(\t+Rf = )({_NUM})(\n\t+Gf = )({_NUM})(\n\t+Bf = )({_NUM})", _tint, new)
            if c < 1:
                raise ValueError(f"caliber_fx {src}: rampa de cor sem chaves")
            got["color"] = got.get("color", 0) + 1
        if new != body:
            reps.append((a, b, new))
    # Renderer.BaseSize (o UNICO campo de tamanho; base_scale/LocalScale ficam como estao)
    r0, r1 = sec["rend"]
    rend = text[r0:r1]
    rend2, c = re.subn(rf"(\t\tBaseSize\n\t\t\{{\n\t\t\tX = )({_NUM})(\n\t\t\tY = )({_NUM})",
                       lambda m: m.group(1) + _num(float(m.group(2)) * s) + m.group(3) + _num(float(m.group(4)) * s),
                       rend)
    got["size"] = c
    reps.append((r0, r1, rend2))
    # quantidade por disparo e por segundo (so no EmitterDef; o Def tem os seus = 0)
    e0, e1 = sec["emit"]
    p0 = sec["pre"][0]
    head = text[e0:p0]

    def _count(v):
        return max(1, _iround(v * n)) if v > 0 else 0
    if count is not None:
        lo, hi = int(count[0]), int(count[1])
        head2, c = re.subn(rf"(\tEmitPerOneShot\n\t\{{\n\t\tMin = )({_NUM})(\n\t\tMax = )({_NUM})",
                           lambda m: f"{m.group(1)}{lo}{m.group(3)}{hi}", head)
    else:
        head2, c = re.subn(rf"(\tEmitPerOneShot\n\t\{{\n\t\tMin = )({_NUM})(\n\t\tMax = )({_NUM})",
                           lambda m: m.group(1) + str(_count(float(m.group(2)))) + m.group(3)
                           + str(_count(float(m.group(4)))), head)
        if not c:
            head2, c = re.subn(rf"^(\tEmitPerOneShot = )({_NUM})$",
                               lambda m: m.group(1) + str(_count(float(m.group(2)))), head, flags=re.M)
    got["count"] = c
    head3, c = re.subn(rf"^(\tEmitPerSecond = )({_NUM})$",
                       lambda m: m.group(1) + str(_iround(float(m.group(2)) * n)), head2, flags=re.M)
    got["eps"] = c
    reps.append((e0, p0, head3))
    exp = dict(EXPECT[src])
    if isinstance(color, tuple):
        exp["color"] = 1
    if got != exp:
        raise ValueError(f"caliber_fx: a fonte {src} ({vendor_path(src)}) nao bate com o esperado: achou {got}, "
                         f"esperava {exp} (texto vanilla mudou?)")
    out = text
    for a, b, new in sorted(reps, reverse=True):
        out = out[:a] + new + out[b:]
    # textura do material
    if texture:
        m0, m1 = _sections(out)["mat"]
        mat, c = re.subn(r"(\t\tTexture\n\t\t\{\n\t\t\tFile = )([^\n]+)", lambda m: m.group(1) + texture, out[m0:m1])
        if c != 1:
            raise ValueError(f"caliber_fx {src}: Material.Texture nao achada")
        out = out[:m0] + mat + out[m1:]
    # caminhos relativos do vanilla -> ./Data/... (a copia mora em outra pasta)

    def _file(m):
        val = m.group(2)
        q = val.startswith('"')
        p = val.strip('"')
        if p.startswith("./Data/") or p.startswith("&"):
            return m.group(0)
        p = _rel_to_data(src, p)
        return m.group(1) + (f'"{p}"' if q else p)
    out = re.sub(r"^(\t+File = )([^\n]+)$", _file, out, flags=re.M)
    # topo: Delay (campo vanilla do rabo, "Delay = 0") e Bucket
    if delay:
        out, c = re.subn(r"^Delay = 0$", f"Delay = {_num(delay)}", out, flags=re.M)
        if c != 1:
            raise ValueError(f"caliber_fx {src}: Delay = 0 nao achado")
    bk = bucket or DEFAULT_BUCKET.get(src)
    if bk:
        out, c = re.subn(r"^Bucket = \w+$", f"Bucket = {bk}", out, flags=re.M)
        if c != 1:
            raise ValueError(f"caliber_fx {src}: Bucket nao achado")
    return out


def _src_parts(src):
    """(fonte vanilla, trocas fixas) de uma fonte (vanilla ou nova)."""
    if src in NEW_SOURCES:
        base, fixed = NEW_SOURCES[src]
        return base, dict(fixed)
    if src not in VENDORED:
        raise KeyError(f"caliber_fx: fonte desconhecida {src!r}")
    return src, {}


def copy_name(src, s=1.0, n=1.0, life=1.0, speed=1.0, delay=0.0, bucket=None, texture=None, color=None, count=None):
    """Nome (sem extensao) da copia: bs_cal_<fonte>_<s*100>[_n..][_l..][_v..][_d..] (+ trocas avulsas)."""
    name = f"bs_cal_{src.lower()}_{_tag(s)}"
    if n != 1:
        name += f"_n{_tag(n)}"
    if life != 1:
        name += f"_l{_tag(life)}"
    if speed != 1:
        name += f"_v{_tag(speed)}"
    if delay:
        name += f"_d{_tag(delay)}"
    if bucket:
        name += f"_b{bucket.lower()}"
    if texture:
        name += "_t" + re.sub(r"\W", "", os.path.splitext(os.path.basename(texture))[0].lower())
    if color is not None:
        if _is_ramp(color):
            name += "_cr" + "".join(f"{_iround(v * 255):02x}" for v in color[1:])
        else:
            name += "_c" + (color if isinstance(color, str) else "".join(f"{_iround(v * 255):02x}" for v in color))
    if count is not None:
        name += f"_k{int(count[0])}_{int(count[1])}"
    return name


def scaled_copy(src, s, n=1, life=1, speed=1, delay=0, bucket=None, texture=None, color=None, count=None):
    """(nome, texto) da copia escalada da fonte src (chave de SPEC["sources"] ou de NEW_SOURCES).
      s: tamanho (so Renderer.BaseSize x s); posicoes do EmitterDef x s; velocidades x s * speed;
      n: quantidade (EmitPerOneShot Min/Max e EmitPerSecond x n, arredondado, minimo 1 onde nao era 0);
      life: vida (Lifetime e SetRandom lifetime x life); delay: Delay do topo (s); bucket: Bucket do topo;
      texture / color / count: trocas avulsas (as fontes novas ja trazem as delas; color ("ramp", r, g, b) tinge
      a rampa de cor).
    O texto sai sem cabecalho (write() poe o de sempre)."""
    base, fixed = _src_parts(src)
    tex = texture or fixed.get("texture")
    col = color if color is not None else fixed.get("color")
    cnt = count if count is not None else fixed.get("count")
    lf = life * fixed.get("life", 1)
    name = copy_name(src, s, n, life, speed, delay, bucket, texture, color, count)
    return name, _patch(base, s * fixed.get("s", 1), n, lf, speed, delay, bucket, tex, col, cnt)


def _item_params(item):
    """Item de boca da tabela ["CG", 0.42, {opcoes}] -> (fonte, kwargs de scaled_copy, onde)."""
    src, s = item[0], float(item[1])
    opt = dict(item[2]) if len(item) > 2 and item[2] else {}
    at = opt.pop("at", "muzzle")
    kw = {"s": s}
    for k in ("n", "life", "speed", "delay"):
        if k in opt:
            kw[k] = float(opt.pop(k))
    if opt:
        raise ValueError(f"caliber_fx: opcao desconhecida no item {item!r}: {sorted(opt)}")
    return src, kw, at


def _smoke_params(st):
    """smoke_trail da tabela {src TSM, eps, scale [a, b], life [a, b]} -> (fonte, kwargs). O tamanho vem do
    BaseSize (base_scale vanilla 4..5 -> scale / 4,5), a quantidade do EmitPerSecond (60) e a vida do lifetime
    vanilla 0,9..1,1 (media 1). Fumaca cinza (sem tinta: a Boiuna 2.0 nao e nuclear)."""
    if st.get("tint"):
        raise ValueError("caliber_fx: smoke_trail com tint nao existe na 2.0 (fumaca cinza)")
    s = (st["scale"][0] + st["scale"][1]) / 2 / 4.5
    life = (st["life"][0] + st["life"][1]) / 2 / 1.0
    return st["src"], {"s": round(s, 4), "n": round(st["eps"] / 60, 4), "life": round(life, 4)}


def _needed():
    """{nome: (fonte, kwargs)} de TODAS as copias que a tabela usa (boca, culatra, esteira, estilhacos, baforadas).
    write() grava todas; as referencias de annotate/decorate/projectile_components saem do mesmo copy_name."""
    need = {}

    def add(src, kw):
        need.setdefault(copy_name(src, **kw), (src, kw))
    for short, row in WEAPONS.items():
        if row.get("mm") is None:
            continue
        mz = row.get("muzzle") or {}
        for key in ("N", "OC"):
            for item in mz.get(key) or []:
                src, kw, _at = _item_params(item)
                add(src, kw)
        pr = row.get("projectile") or {}
        if pr.get("smoke_trail"):
            add(*_smoke_params(pr["smoke_trail"]))
    for lst in PRESETS.values():
        for p in lst:
            if p.startswith("bs:"):
                add(p[3:], {"s": 1.0})
    return need


def all_files():
    """{nome: texto} das copias (sem cabecalho)."""
    return {name: scaled_copy(src, **kw)[1] for name, (src, kw) in sorted(_needed().items())}


def cal_ref(name, frm):
    """Caminho (sem &<>) de uma copia de OUT_DIR; frm = "shot" | "part" (fxkit.ref)."""
    return FXK.ref(OUT_DIR, name, frm)


# ============================================================================= efeitos proprios 2.0 (AC, FRAG)
HOT = [(1.6, 1.6, 1.6, 1), (1.15, 1.15, 1.15, 0.75), (1, 1, 1, 0.25), (1, 1, 1, 0)]
RING_RAMP = [(1.4, 1.4, 1.4, 1), (1.1, 1.1, 1.1, 0.95), (1, 1, 1, 0.7), (1, 1, 1, 0)]
LIGHT_RAMP = [(1, 1, 1, 1), (1, 1, 1, 0.5), (1, 1, 1, 0)]
FRAG_CONES = ("cone", "radial")


def frag_shape_mode():
    v = FXK.art_switch("frag_cone")
    if v not in FRAG_CONES:
        raise ValueError(f"art.frag_cone invalido: {v!r} (use {', '.join(FRAG_CONES)})")
    return v


def own_fx_text(key):
    """Texto do efeito proprio 'pasta/nome' de SPEC["own_fx"] (tijolos do fxkit)."""
    c = OWN_FX[key]
    name = key.split("/", 1)[1]
    kind = c["kind"]
    note = f"Bullet Strike 2.0 ({name}): {c['what']}"
    col = tuple(c.get("color") or (1, 1, 1, 1))
    if kind == "light":
        # luz no casco (particle_light, SCREEN): alfa baixo para o casco tingir sem virar branco
        return FXK.blob(note, c["size"], c["life"], 0, col, LIGHT_RAMP, scale=(0.8, 1.15), light=True, bucket="Upper5")
    if kind == "flash":
        return FXK.blob(note, c["size"], c["life"], 0, col, HOT, scale=(0.6, 1.2), bucket="Upper2")
    if kind == "ring":
        return FXK.textured_blob(note, TEX_PREFIX + c["tex"], c["size"], c["life"], col, RING_RAMP,
                                 scale=tuple(c["scale"]), bucket="Upper2", delay=c.get("delay", 0))
    if kind == "embers":
        return FXK.embers(note, n=tuple(c["n"]), speed=tuple(c.get("speed") or (2.5, 6)), life=tuple(c["life"]),
                          color_from=tuple(c["from"]), color_to=tuple(c["to"]))
    if kind == "frag_shape":
        if frag_shape_mode() == "cone":
            # leque a frente: o vertice (borda esquerda do quadro) fica no ponto da rajada (Offset 0,5 do quadro)
            return FXK.textured_blob(note + " [art.frag_cone = cone]", TEX_PREFIX + c["cone_tex"], c["size"],
                                     c["life"], col, HOT, scale=tuple(c["scale"]), offset=(0.5, 0), bucket="Upper2")
        return FXK.textured_blob(note + " [art.frag_cone = radial]", TEX_PREFIX + c["ring_tex"], c["size"], c["life"],
                                 col, RING_RAMP, scale=(0.3, 1), bucket="Upper2")
    raise ValueError(f"caliber_fx: own_fx {key} com kind desconhecido {kind!r}")


def write(out, header):
    """Seam B2: grava shots/bs_cal_fx/*.rules e os efeitos proprios de shots/bs_ac_fx/ e shots/bs_frag_fx/
    (inclusive com --no-art: so texto)."""
    head = "\n".join(f"// {ln}" for ln in header.split("\n"))
    for name, (src, kw) in sorted(_needed().items()):
        base, fixed = _src_parts(src)
        what = ", ".join(f"{k}={_num(v)}" for k, v in kw.items())
        # (caminhos seguidos de espaco: o conferidor de ./Data do build_mod tambem le os comentarios)
        extra = ("; trocas fixas: " + " ; ".join(f"{k} = {v}" for k, v in fixed.items()) + " ") if fixed else ""
        rel_v = os.path.relpath(vendor_path(base), HERE).replace(os.sep, "/")
        note = (f"// Copia escalada de ./Data/{SPEC['sources'][base]['file']} (fonte {src}: {what}{extra}).\n"
                f"// Texto vanilla em tools/{rel_v}; so mudam BaseSize, posicoes, velocidades, quantidade, vida, "
                f"Delay, Bucket, tinta e caminhos ./Data.\n")
        out.text(f"{OUT_DIR}/{name}.rules", head + "\n" + note + scaled_copy(src, **kw)[1])
    for key in sorted(OWN_FX):
        sub, name = key.split("/", 1)
        out.text(f"{FX_DIRS[sub]}/{name}.rules", head + "\n" + own_fx_text(key))


# ============================================================================= presets de impacto (1.A)
def _data_shot(p):
    """'chaingun_shot/particles/x' (relativo a Data/shots) -> './Data/shots/chaingun_shot/particles/x.rules'."""
    return D + "/" + os.path.normpath(os.path.join("shots", p)).replace(os.sep, "/") + ".rules"


def _entry_path(p, frm="shot"):
    """Caminho (sem &<>) de uma entrada de preset: 'bs:<fonte>' (copia escalada s=1), 'fx:<pasta>/<nome>' (efeito
    proprio 2.0) ou caminho vanilla relativo a Data/shots."""
    if p.startswith("bs:"):
        return cal_ref(copy_name(p[3:], 1.0), frm)
    if p.startswith("fx:"):
        sub, name = p[3:].split("/", 1)
        return FXK.ref(FX_DIRS[sub], name, frm)
    return _data_shot(p)


def _preset_paths(name, frm="shot"):
    """Arquivos de um preset de SPEC["hit_presets"] como entradas de MediaEffects (vistas de um projetil)."""
    return [f"&<{_entry_path(p, frm)}>" for p in PRESETS[name]]


def preset_media(name, frm="shot"):
    """Lista de MediaEffects ('&<...>') de um preset (PEN_S, POP_L, AC_BLAST_M, FRAG_BURST_H, ...)."""
    if name not in PRESETS:
        raise KeyError(f"caliber_fx: preset desconhecido {name!r}")
    return _preset_paths(name, frm)


def preset_particles(name):
    """Particulas por disparo (soma dos maximos de particle_counts) de um preset."""
    return sum(int(COUNTS[p]) for p in PRESETS[name])


DEBRIS = "../common_effects/particles/explosions/big_part_explode_debris"


# ============================================================================= seam do WP02 (J2R3-18)
def _seam(table, art_tier):
    name = SEAM[table].get(art_tier) if isinstance(art_tier, str) else None
    return name or None


def pen_effect(art_tier, frm="shot"):
    """MediaEffects das pecas ATRAVESSADAS (PenetratingOperational) pelo art_tier (SPEC.art_assets.seam_tier_map:
    tracer -> PEN_S; s/m -> PEN_M; l/h -> PEN_L; pem -> PEN_S; slug -> PEN_L): lista de '&<...>' (<= 6 particulas,
    sem som e sem tremor; o chamador soma o som de antes). None para plasma, tier fora da tabela ou art.pen_media =
    full (o chamador mantem o efeito antigo; nunca KeyError)."""
    if FXK.art_switch("pen_media") == "full":
        return None
    name = _seam("pen_effect", art_tier)
    return _preset_paths(name, frm) if name else None


def pop_effect(art_tier, frm="shot"):
    """MediaEffects do projetil ABATIDO no ar (Targetable.OnDeath) pelo art_tier (tracer/s/pem -> POP_S;
    m/l/h/slug -> POP_L), sem MediaEffectsScale (o campo nao aparece no corpus em OnDeath). None como pen_effect."""
    if FXK.art_switch("pen_media") == "full":
        return None
    name = _seam("pop_effect", art_tier)
    return _preset_paths(name, frm) if name else None


# ============================================================================= arte das granadas (art3d/bs_shells2)
_ART = {}
_LEGACY_USED = {}            # chave -> (item, meta) da reserva 1.x usada neste build (copy_art copia os arquivos)


def _load_meta(d, kind="shells"):
    p = os.path.join(d, "meta.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        meta = json.load(fh)
    if meta.get("kind") != kind:
        raise ValueError(f"caliber_fx: {p} nao e de granadas (kind {meta.get('kind')!r})")
    missing = [f for f in meta.get("files", []) if not os.path.isfile(os.path.join(d, f))]
    if missing:
        raise FileNotFoundError(f"caliber_fx: {p} cita arquivos que nao existem: {missing[:5]}")
    for key, it in (meta.get("items") or {}).items():
        if not it.get("file") or not it.get("size"):
            raise KeyError(f"caliber_fx: {p}: item {key!r} sem file/size")
        for f in [it.get("file"), it.get("normals"), it.get("mask")] + [(it.get("lights") or {}).get("file")]:
            if f and f not in meta.get("files", []):
                raise KeyError(f"caliber_fx: {p}: {key} usa {f!r}, fora da lista files")
    return dict(meta, _dir=d)


def _shell_art():
    """meta.json da arte das granadas 2.0 (art3d/bs_shells2) ou None (sem arte = dardo vanilla no tamanho novo).
    BS_SHELL_ART_DIR troca a pasta (folhas de teste); pasta sem meta.json = sem arte (testa o caminho de reserva)."""
    d = os.environ.get("BS_SHELL_ART_DIR") or ART_SRC
    if d not in _ART:
        _ART[d] = _load_meta(d)
    return _ART[d]


def art_key(ammo, tier=None, s=None):
    """Chave da arte de voo: s['art_key'] quando o modulo dono pos uma (WP08 pem_s/pem_m/pem_l, WP09 'slug'); senao
    f'{ammo}_{tier}' (he_s, ap_m, ac_h, ...)."""
    if s is not None and s.get("art_key"):
        return s["art_key"]
    return f"{ammo}_{tier}"


def art_item(key):
    """(item do meta, meta) da chave em art3d/bs_shells2; (None, None) sem arte. Chave que falta na 2.0 cai na
    reserva 1.x do bloco LEGACY_1X_FALLBACK (aviso 'arte 1.x usada: <chave>')."""
    meta = _shell_art()
    if meta and key in meta["items"]:
        return meta["items"][key], meta
    if key in _LEGACY_USED:
        return _LEGACY_USED[key]
    # LEGACY_1X_FALLBACK inicio
    if not os.environ.get("BS_SHELL_ART_DIR"):
        old = _ART.get("__1x__")
        if "__1x__" not in _ART:
            old = _ART["__1x__"] = _load_meta(os.path.join(ROOT, "art3d", "bs_shells"))
        k1 = "ap" if key.split("_")[0] in ("ap", "sap") else "he"
        if old and k1 in old["items"]:
            FXK._warn(f"arte 1.x usada: {key} (sem a chave em art3d/bs_shells2; reserva art3d/bs_shells '{k1}')")
            _LEGACY_USED[key] = (old["items"][k1], old)
            return _LEGACY_USED[key]
    # LEGACY_1X_FALLBACK fim
    return None, None


def art_body(key, length=None):
    """Corpo no jogo [L, W] (tiles): L = SPEC.art_assets.shell_ladder.items[key].in_game_body[0] (ou length) e
    W = L x tela_h / tela_w da arte (meta items.<chave>.size: ex. he_s [2,0; 0,7] -> 0,72 x 0,252; slug [3,0; 0,8])."""
    item, _meta = art_item(key)
    if length is None:
        if key not in LADDER:
            raise KeyError(f"caliber_fx: chave {key!r} fora de SPEC.art_assets.shell_ladder.items")
        length = LADDER[key]["in_game_body"][0]
    L = float(length)
    if item:
        cw, ch = item["size"]
        return [round(L, 4), round(L * ch / cw, 4)]
    return [round(L, 4), round(float(LADDER.get(key, {}).get("in_game_body", [L, L * 0.35])[1]), 4)]


def art_anchor(key, name, length=None):
    """Ancora da arte (meta items.<chave>.anchors: 'tip' do slug, 'seeker' da ac_h) em tiles no jogo, a partir do
    centro do corpo; None quando a arte nao tem a ancora."""
    item, _meta = art_item(key)
    if not item or name not in (item.get("anchors") or {}):
        return None
    L, W = art_body(key, length)
    ax, ay = item["anchors"][name]
    cw, ch = item["size"]
    return [round(ax * L / cw, 4), round(ay * W / ch, 4)]


def art_components(key, length=None, mask_color=None, lights=True, bucket_body="BulletUpper3",
                   bucket_lights="BulletUpper4", offset=0, prefix=ART_PREFIX):
    """Componentes de sprite da arte de voo (corpo iluminado + faixa tingida + atlas de luzes, fxkit.
    art_sprite_components) para um tiro em shots/<pasta>/<arquivo>.rules; {} sem arte. mask_color: VertexColor da
    faixa (padrao: palette[municao].band quando o item tem mascara). Usado pelo WP08 (pem_s/m/l) e WP09 (slug)."""
    item, _meta = art_item(key)
    if not item:
        return {}
    if mask_color is None and item.get("mask"):
        ammo = key.split("_")[0]
        mask_color = (COLORS.get(ammo) or {}).get("band")
    return FXK.art_sprite_components(prefix, item, art_body(key, length), bucket_body=bucket_body,
                                     bucket_lights=bucket_lights, lights=lights,
                                     mask_color=mask_color if item.get("mask") else None, offset=offset)


def copy_art(out):
    """Seam B3: copia as PNGs da arte das granadas (art3d/bs_shells2 e, se usada, a reserva 1.x) para
    shots/bs_shell_art/ (full e --no-art)."""
    dst = os.path.join(out.root, ART_OUT)
    metas = []
    meta = _shell_art()
    if meta:
        metas.append((meta, meta["files"]))
    for item, m in _LEGACY_USED.values():
        files = [item.get("file"), item.get("normals"), item.get("mask"), (item.get("lights") or {}).get("file")]
        metas.append((m, [f for f in files if f]))
    for m, files in metas:
        os.makedirs(dst, exist_ok=True)
        for f in files:
            shutil.copyfile(os.path.join(m["_dir"], f), os.path.join(dst, f))


# ============================================================================= anotacao (D1)
def _row(short):
    row = WEAPONS.get(short)
    if not row or row.get("mm") is None:
        return None
    return row


def _muzzle_refs(items, frm):
    """Lista de boca da tabela -> (refs da boca, refs da culatra)."""
    mz, br = [], []
    for item in items or []:
        src, kw, at = _item_params(item)
        ref = cal_ref(copy_name(src, **kw), frm)
        (br if at == "breech" else mz).append(ref)
    return mz, br


def _turret_radius(g):
    """Raio da torre (tiles) para o StartTime das luzes: meta da arte (turret_size) ou a maior medida da peca / 2."""
    meta = g.get("art3d") or {}
    ts = meta.get("turret_size") if isinstance(meta, dict) else None
    if ts:
        return float(ts) / 2
    return max(g.get("size") or [1, 1]) / 2


def _annotate_shot(s, g, row, ammo, oc):
    pr = copy.deepcopy(row.get("projectile"))
    imp = copy.deepcopy(row.get("impact") or {})
    tier = s.get("art_tier") or (pr or {}).get("art_tier") or ("tracer" if (pr or {}).get("look") == "tracer" else None)
    v = {"short": g["short"], "ammo": ammo, "oc": bool(oc), "mm": row["mm"], "tier": tier, "projectile": pr,
         "impact": imp, "start": FXK.start_time(_turret_radius(g), s.get("speed") or 0)}
    s["vfx"] = v
    if pr:
        look = pr["look"]
        s["look"] = look
        if look == "tracer":
            s["sprite_wh"] = list(pr["streak"])
            s["core_wh"] = list(pr["core"])
            s["glow_size"] = list(pr["glow"])
            s["glow_offset"] = round(-0.4 * pr["streak"][0], 3)
            s.pop("glow_z", None)
        else:
            key = art_key(ammo, tier, s)
            v["art_key"] = key
            s["art_key"] = key
            v["body"] = art_body(key) if key in LADDER else list(pr["body"])
            s["sprite_size"] = v["body"][0]
            s["glow_size"] = list(pr["glow"])
            s["glow_offset"] = 0
            s["glow_z"] = pr.get("glow_z", 0)
        tr = pr.get("trail")
        if tr:
            s["trail"] = tr["shape"]
            s["trail_color"] = ammo
            # o nome do arquivo tem de existir em bsgen/trails.py (forma x cor da municao)
            TR.trail_name(tr["shape"], ammo)
        else:
            s.pop("trail", None)
            s.pop("trail_color", None)
        if pr.get("smoke_trail"):
            src, kw = _smoke_params(pr["smoke_trail"])
            s["vfx_smoke"] = copy_name(src, **kw)
    sh = imp.get("shake") or [0, 0]
    s["shake"] = sh[0]
    s["vfx_shake_time"] = sh[1]


def _annotate_burst(s, d, row, key):
    imp = copy.deepcopy(row.get("impact") or {})
    if key == "frag" and imp.get("burst_frag"):
        imp["burst"] = imp["burst_frag"]
    s["vfx"] = {"short": d["short"], "ammo": key, "oc": False, "mm": row["mm"], "tier": None, "projectile": None,
                "impact": imp}
    sh = imp.get("shake") or [0, 0]
    s["vfx_shake_time"] = sh[1]


def _annotate_fragment(s, d, row):
    fr = copy.deepcopy((row.get("impact") or {}).get("fragment") or {})
    s["vfx"] = {"short": d["short"], "ammo": "frag", "oc": False, "mm": row["mm"], "tier": None, "projectile": None,
                "impact": {}, "fragment": fr}


def _check_palette_copy():
    """ammo_colors do json e copia de SPEC.art_assets.palette: avisa se alguem mudou um e nao o outro."""
    for k, c in (SPEC.get("ammo_colors") or {}).items():
        p = COLORS.get(k)
        if not p:
            continue
        for ch, val in c.items():
            if isinstance(val, list) and ch in p and list(p[ch]) != list(val):
                FXK._warn(f"caliber_fx: bullet_strike_vfx.json ammo_colors.{k}.{ch} = {val} difere da paleta do spec "
                          f"{p[ch]} (vale a paleta)")


def annotate(data):
    """Seam D1: liga os projeteis as linhas da tabela pelos modos das armas (GUNS[].modes[] por index/key: shot /
    shot_oc) e das defesas (feixe por modo + fragmento da FRAG), nunca pelo nome do arquivo; e poe a arte de voo
    (art_key resolvida + art_body) nos tiros de outros modulos com art_key/art_tier (PEM, slug). So chaves visuais."""
    _check_palette_copy()
    by_file = {s["file"]: s for s in data.SHOTS}
    for g in data.GUNS:
        row = _row(g["short"])
        if row is None:
            continue
        for m in sorted(g["modes"], key=lambda x: x["index"]):
            ammo = m.get("key") or m.get("ammo")
            for f, oc in ((m.get("shot"), False), (m.get("shot_oc"), True)):
                if not f or (oc and f == m.get("shot")) or f not in by_file:
                    continue
                s = by_file[f]
                if s.get("plasma_fx"):
                    continue
                _annotate_shot(s, g, row, ammo, oc)
        mz = row["muzzle"]
        fx = g["fx"]
        p, b = _muzzle_refs(mz["N"], "part")
        fx["particles"] = p
        if b:
            fx["breech"] = b
        if mz.get("OC"):
            p, b = _muzzle_refs(mz["OC"], "part")
            fx["particles_oc"] = p
            if b:
                fx["breech_oc"] = b
        sh = mz.get("shake") or [0, 0]
        fx["shake"] = sh[0]
        fx["shake_time"] = sh[1] if sh[0] else fx.get("shake_time", 0.5)
        fx["shake_oc"] = mz.get("shake_oc", sh[0])
        if not fx["shake_oc"]:
            fx.pop("shake_oc")
    for d in data.DEFENSES:
        row = _row(d["short"])
        if row is None:
            continue
        mz = row["muzzle"]
        p, _b = _muzzle_refs(mz["N"], "part")
        d["fx"]["particles"] = p
        if mz.get("OC"):
            p, _b = _muzzle_refs(mz["OC"], "part")
            d["fx"]["particles_oc"] = p
        for m in sorted(d["modes"], key=lambda x: x["index"]):
            key = m.get("key") or m.get("ammo")
            beam = by_file.get(m.get("beam"))
            if beam is not None:
                _annotate_burst(beam, d, row, key)
            frag = by_file.get(m.get("fragment"))
            if frag is not None and "vfx" not in frag:
                _annotate_fragment(frag, d, row)
    # tiros de outros modulos (WP08 'pem', WP09 'slug_rail', ...): chave da arte de voo resolvida
    for s in data.SHOTS:
        if "vfx" in s or s.get("plasma_fx"):
            continue
        if s.get("art_key") or s.get("art_tier") in ("pem", "slug"):
            key = art_key(s.get("ammo") or s.get("key"), s.get("art_tier"), s)
            s["art_key"] = key
            if key in LADDER:
                s["art_body"] = art_body(key)


# ============================================================================= visual em voo (S1)
GLOW = {"File": Q(f"{D}/common_effects/particles/blob.png"), "MipLevels": "max", "SampleMode": "Linear"}
WHITE_HOT = [255, 250, 235]
# Os mocks aprovados (vfx_design/scripts/fxlib.draw_tracer) desenham o risco com 2,2x a largura do Size do jogo
# (shots._sprite_components: Size [L, W]); a granada desenha o tracante com 1,4 x largura e o nucleo com 0,8 x.
# Para a granada ficar na mesma proporcao das metralhadoras: largura no jogo = largura do mock / 2,2.
MOCK_W = 2.2


def _blob(bucket, wh, color, offset):
    """Sprite aditivo de blob.png (mesmo formato de shots._blob_sprite)."""
    return {"Type": "Sprite", "RenderBucket": bucket, "Offset": [round(offset, 3), 0],
            "Sprite": {"Texture": dict(GLOW), "Size": [round(wh[0], 4), round(wh[1], 4)],
                       "VertexColor": [int(c) for c in color], "TargetBlendMode": "Add"}}


def _ammo_colors(ammo):
    return COLORS.get(ammo) or COLORS["he"]


def _gain(color, g):
    return [_iround(c * g) for c in color]


def _tracer_components(s, v, trail_ref):
    """Tracante (metralhadoras, 20/30 mm): risco + nucleo + cabeca + borrao + halo de espaco (+ rastro no 20 mm).
    Molde do pd_shot.rules (Size [L, W], Offset -0.4375 L, LerpScaleFrom [.25, 1], LerpTime .05). A luz e SO o halo
    (fxkit.light_pair sem luz de casco: ate 36 tiros/s por arma, uma luz por tiro como na Fase B)."""
    pr = v["projectile"]
    col = _ammo_colors(v["ammo"])
    L, W = pr["streak"]
    cl, cw = pr["core"]
    comps = {}
    spr = _blob("BulletUpper3", [L, W], col["tracer"], -0.4375 * L)
    spr["LerpScaleFrom"] = [0.25, 1]
    spr["LerpTime"] = 0.05
    comps["Sprite"] = spr
    comps["CoreSprite"] = _blob("BulletUpper4", [cl, cw], col["core"], -0.35 * cl)
    if pr.get("head"):
        # cabeca branco-quente no nariz (mock fxlib.draw_tracer: blob 1,6 x head)
        h = 1.6 * pr["head"]
        comps["HeadSprite"] = _blob("BulletUpper4", [h, h], WHITE_HOT, 0)
    if pr.get("smear"):
        # borrao de calor do 30 mm: mais longo e fraco, por baixo (alfa aplicado na cor: aditivo)
        sl, sw = pr["smear"]["wh"]
        a = float(pr["smear"]["alpha"])
        comps["SmearSprite"] = _blob("BulletUpper2", [sl, sw], [_iround(c * a) for c in col["tracer"]], -0.55 * sl)
    comps.update(FXK.light_pair(list(pr["glow"]), col["glow"], None, None, v.get("start"), FXK.UNLIT_TRACER,
                                x_halo=-0.4 * L, legacy_unlit=0.2))
    if trail_ref:
        comps["Trail"] = {"Type": "MediaEffects", "MediaEffects": [trail_ref]}
    return comps


def shell_layout(pr):
    """Camadas da granada (Fase B) no jogo (x do centro em tiles a partir do CENTRO do corpo, +x = nariz; [L, W] em
    tiles): corpo centrado; tracante na base, por baixo do corpo, com o centro em -(0,55 L + 0,4375 tl); nucleo
    branco-quente na frente do tracante; clarao da base (head, X2) em -0,5 L; brilho centrado. Mantida igual para as
    previas (tools/blender/previews: sheet.py / prev2.py); o jogo usa shell_layout2."""
    L, W = pr["body"]
    tl, tw = pr["tracer"]
    lay = {"body": (0.0, [L, W]),
           "tracer": (-(0.55 * L + 0.4375 * tl), [tl, round(tw * 1.4 / MOCK_W, 4)]),
           "core": (-(0.55 * L + 0.1 * tl), [round(0.45 * tl, 4), round(tw * 0.8 / MOCK_W, 4)]),
           "glow": (0.0, list(pr["glow"]))}
    if pr.get("head"):
        lay["head"] = (-0.5 * L, [round(1.6 * pr["head"], 4)] * 2)
    return lay


def shell_layout2(pr):
    """shell_layout + as correcoes 2.0 (ADDENDUM G7): head_k / head_dx (Tambor e Trovao: clarao da base com metade do
    diametro e recuado head_dx x diametro antigo para tras da base) e thin (Boiuna, BOIUNA_THIN: tracante de tl tiles
    com tw x a largura comecando na base, nucleo de kl tiles com kw x a largura e a frente kback tile atras da base;
    'gain' fica para quem pinta). Mesma conta das folhas aprovadas (prev2.draw_new)."""
    lay = shell_layout(pr)
    L = pr["body"][0]
    if "head" in lay and (pr.get("head_k") or pr.get("head_dx")):
        hx, (hd, _hd) = lay["head"]
        k = float(pr.get("head_k") or 1.0)
        lay["head"] = (round(hx - float(pr.get("head_dx") or 0) * hd, 4), [round(hd * k, 4)] * 2)
    th = pr.get("thin")
    if th:
        _x, (tl, tw) = lay["tracer"]
        tl, tw = float(th.get("tl", tl)), tw * float(th.get("tw", 1))
        lay["tracer"] = (round(-0.5 * L - 0.5 * tl, 4), [round(tl, 4), round(tw, 4)])
        _x, (kl, kw) = lay["core"]
        kl, kw = float(th.get("kl", kl)), kw * float(th.get("kw", 1))
        lay["core"] = (round(-0.5 * L - float(th.get("kback", 0.3)) - 0.5 * kl, 4), [round(kl, 4), round(kw, 4)])
        lay.pop("head", None)
    return lay


def _dart(size):
    """Reserva sem arte: o dardo com sabot vanilla (bullet_large.png) no tamanho novo (shots._sprite_components)."""
    return {"Type": "AnimatedSprite", "RenderBucket": "BulletUpper3", "ReduceScaleWith": "Hit",
            "ReduceScaleExponent": 0.5,
            "Animation": {"AtlasSprite": {"Texture": {"File": Q(f"{D}/shots/bullet_large/bullet_large.png"),
                                                      "SampleMode": "Linear", "MipLevels": "max"},
                                          "Size": [size, size]},
                          "FrameCount": 16, "FrameSize": [256, 256], "FramesPerRow": 4, "FramesPerSecond": 120},
            "NormalsTexture": "&Animation/AtlasSprite/Texture",
            "DiffuseShader": Q(f"{D}/default.shader"),
            "NormalsShader": Q(f"{D}/no_normals.shader")}


def _shell_components(s, v, trail_ref):
    """Granada 2.0 (Tambor s, Trovao m, Mapinguari l, Boiuna h): arte de art3d/bs_shells2 (corpo iluminado + faixa na
    cor da municao + atlas de luzes; ac_h = a AC guiada da Boiuna com o sensor piscando no atlas), tracante/nucleo/
    clarao da base (shell_layout2), halo de espaco + luz de casco (fxkit.light_pair: palette[municao].hull, refl 6;
    AC 4), rastro e esteira de fumaca cinza (406 e Boiuna). Sem arte: o dardo vanilla no tamanho novo."""
    pr = dict(v["projectile"])
    ammo = v["ammo"]
    col = _ammo_colors(ammo)
    L, W = v.get("body") or pr["body"]
    pr["body"] = [L, W]
    lay = shell_layout2(pr)
    gain = float((pr.get("thin") or {}).get("gain", 1.0))
    comps = {}
    key = v.get("art_key")
    item = art_item(key)[0] if key else None
    if item:
        comps.update(FXK.art_sprite_components(ART_PREFIX, item, [L, W],
                                               mask_color=(col["band"] if item.get("mask") else None)))
    else:
        comps["Sprite"] = _dart(L)
    x, wh = lay["tracer"]
    tr = _blob("BulletUpper2", wh, _gain(col["tracer"], gain), x)
    tr["LerpScaleFrom"] = [0.25, 1]
    tr["LerpTime"] = 0.05
    comps["TailSprite"] = tr
    x, wh = lay["core"]
    core = _blob("BulletUpper2", wh, _gain(col["core"], gain), x)
    core["LerpScaleFrom"] = [0.25, 1]
    core["LerpTime"] = 0.05
    comps["CoreSprite"] = core
    if "head" in lay:
        x, wh = lay["head"]
        comps["HeadSprite"] = _blob("BulletUpper2", wh, WHITE_HOT, x)
    x, wh = lay["glow"]
    comps.update(FXK.light_pair(wh, col["glow"], [round(1.2 * L, 4), round(max(1.2 * W, 0.5), 4)], col["hull"],
                                v.get("start"), FXK.UNLIT_SHELL, x_halo=x, z=pr.get("glow_z", 0), key=ammo,
                                legacy_unlit=0.125))
    if trail_ref:
        comps["Trail"] = {"Type": "MediaEffects", "MediaEffects": [trail_ref]}
    if s.get("vfx_smoke"):
        # esteira de fumaca (missile_he_thruster_smoke copiado; como o propulsor vanilla: Rotation 180d na base,
        # missile_he.rules l.96-108)
        comps["SmokeTrail"] = {"Type": "MediaEffects", "Offset": [round(-0.5 * L, 3), 0], "Rotation": "180d",
                               "MediaEffects": [f"&<{cal_ref(s['vfx_smoke'], 'shot')}>"]}
    return comps


def fragment_components(s):
    """Fragmento da FRAG: UMA sprite aditiva (blob.png, palette.frag.tracer, [0,35, 0,06], BulletUpper3, LerpScaleFrom
    [0,3, 1], LerpTime 0,03); sem IsLight e sem emissor (SPEC.art_assets.effects.frag.fragments)."""
    fr = ((s.get("vfx") or {}).get("fragment")) or {}
    L, W = fr.get("wh") or [0.35, 0.06]
    spr = _blob(fr.get("bucket", "BulletUpper3"), [L, W], COLORS["frag"]["tracer"], -0.4375 * L)
    spr["LerpScaleFrom"] = list(fr.get("lerp_scale_from") or [0.3, 1])
    spr["LerpTime"] = fr.get("lerp_time", 0.03)
    return {"Sprite": spr}


def projectile_components(s, trail_ref):
    """Seam S1: componentes visuais em voo por calibre, ou None (caminho antigo de shots._sprite_components)."""
    if s.get("plasma_fx"):
        return None
    if s.get("kind") == "frag_fragment":
        return fragment_components(s)
    v = s.get("vfx")
    if not v or not v.get("projectile"):
        return None
    look = v["projectile"]["look"]
    if look == "tracer":
        return _tracer_components(s, v, trail_ref)
    if look == "shell":
        return _shell_components(s, v, trail_ref)
    return None


# ============================================================================= impactos (S3)
SOUND_BASE = "/BASE_SOUNDS/AudioExterior"
SHAKE_BASE = "/BASE_SHAKE"
# MediaEffectsScale em dois blocos onde o corpus (vanilla 0.30.3/0.30.5 + SW:ACD) nunca o usa: a carga final
# (FinishedPenetratingOperational) e a rajada da flak (HitNothing do feixe). Sao o mesmo tipo de grupo dos blocos
# irmaos onde o campo e provado (PenetratingHit HitOperational/PenetratingOperational: bullet_railgun.rules 0.30.3
# l.99/139; HitOperational de raiz de feixe: ion_beam.rules 0.30.3 l.165), numero puro como no SW:ACD
# (proton_rocket.rules l.129). Campo desconhecido o jogo ignora (pior caso: o efeito sai x1). False aqui tira os
# dois e volta esses efeitos ao tamanho vanilla. Teste no jogo: T-CAL-1.
MES_ON_FINISH = True
MES_ON_HITNOTHING = True
AP_FINISH_K = 0.8            # AP sem carga: o preset cheio do casco x0,8 UMA vez, onde a granada para


def _is(e, base):
    return isinstance(e, Inh) and e.base == base


def _media(refs, old, shake):
    """Nova lista de MediaEffects: refs de particula + os sons da lista antiga EXATAMENTE como estavam (R5) + tremor
    da tabela. Particulas e tremor antigos saem."""
    keep = []
    if isinstance(old, list):
        for e in old:
            if isinstance(e, str) and e.startswith("&<"):
                continue           # particula antiga
            if _is(e, SHAKE_BASE):
                continue           # tremor antigo
            keep.append(e)         # sons (e qualquer outra coisa) ficam
    out = list(refs) + keep
    amt, dur = shake
    if amt:
        out.append(Inh(SHAKE_BASE, {"ShakeAmount": amt, "Duration": dur}))
    return out


def _sounds(lst):
    return [copy.deepcopy(e) for e in (lst if isinstance(lst, list) else []) if _is(e, SOUND_BASE)]


def _mes(v):
    return round(float(v), 4)


def _hull_entry(imp, ammo):
    hull = imp.get("hull") or {}
    ent = hull.get(ammo) or hull.get("he") or next(iter(hull.values()))
    return ent


def _he_entry(imp, ammo, radius):
    """(preset, MediaEffectsScale) da carga de ammo: 'r/4' = raio da carga / 4 (lei he_mes)."""
    he = (imp.get("he") or {}).get(ammo)
    if not he:
        return None
    preset, mes = he
    if isinstance(mes, str):
        if mes.strip() != "r/4" or not radius:
            raise ValueError(f"caliber_fx: escala {mes!r} sem raio de carga")
        mes = float(radius) / 4.0
    return preset, mes


def _pop(s, comps, v, frm="shot"):
    """Abatido no ar: Targetable.OnDeath = POP pelo tier (pop_effect); so troca uma lista/referencia de midia."""
    tg = comps.get("Targetable")
    if not isinstance(tg, dict) or not isinstance(tg.get("OnDeath"), dict):
        return
    pop = pop_effect(v.get("tier") or s.get("art_tier"), frm)
    if pop:
        tg["OnDeath"]["MediaEffects"] = pop


def _decorate_kinetic(s, top, v):
    imp = v["impact"]
    ammo = v["ammo"]
    comps = top["Components"]
    hit = comps["Hit"]
    light = FXK.art_switch("pen_media") != "full"
    shake = (s.get("shake", 0), s.get("vfx_shake_time", 0.5))
    hp, hmes = _hull_entry(imp, ammo)
    op = hit["HitOperational"]
    op["MediaEffects"] = _media(_preset_paths(hp), op.get("MediaEffects"), shake)
    op["MediaEffectsScale"] = _mes(hmes)
    st = hit.get("HitStructural")
    if isinstance(st, dict) and imp.get("struct"):
        sp, smes = imp["struct"]
        st["MediaEffects"] = _media(_preset_paths(sp), st.get("MediaEffects"), (0, 0))
        st["MediaEffectsScale"] = _mes(smes)
    fin = hit.get("FinishedPenetratingOperational")
    burst_r = (s.get("finish_explosion") or [None])[0]
    he = _he_entry(imp, ammo, burst_r) if isinstance(fin, dict) else None
    # escudo: preset proprio (sem fumaca nem destrocos), HitEffects iguais aos de antes (R4)
    if imp.get("shield"):
        shp, shmes = imp["shield"]
        refs = _preset_paths(shp)
        if he and imp.get("shield_he"):
            # granada com carga no escudo: + clarao da carga; um MediaEffectsScale por bloco -> o menor dos dois
            refs = refs + [r for r in _preset_paths(imp["shield_he"][0]) if r not in refs]
            shmes = min(shmes, imp["shield_he"][1])
        sh = hit.get("HitShield")
        if sh == "&HitOperational":
            sh = {k: copy.deepcopy(x) for k, x in op.items() if k not in ("MediaEffects", "MediaEffectsScale")}
        if isinstance(sh, dict):
            sh["MediaEffects"] = refs + _sounds(op["MediaEffects"]) + (
                [Inh(SHAKE_BASE, {"ShakeAmount": shake[0], "Duration": shake[1]})] if shake[0] else [])
            sh["MediaEffectsScale"] = _mes(shmes)
            hit["HitShield"] = sh
    # pecas atravessadas (Fase B: o preset cheio do primeiro acerto em CADA peca = 559-793 particulas por granada 406
    # AP em 13 pecas). 2.0: PEN_S/M/L (<= 6 por peca) com o som de antes (R5) e SEM tremor
    pen = hit.get("PenetratingOperational")
    if isinstance(pen, dict):
        pmes = imp.get("pen_mes")
        if light:
            refs = _preset_paths(imp.get("pen") or _seam("pen_effect", v.get("tier")) or "PEN_S")
        else:
            refs = _preset_paths(hp)
            if imp.get("extra_ap") and ammo == "ap":
                refs = refs + [f"&<{_data_shot(DEBRIS)}>"]
        pen["MediaEffects"] = refs + _sounds(op["MediaEffects"])
        pen["MediaEffectsScale"] = _mes(pmes if pmes is not None else hmes)
    # onde a granada para: carga (HE/SAP/AC) com o preset por municao, escala = raio / 4
    if isinstance(fin, dict):
        if not he:
            raise KeyError(f"caliber_fx: {s['file']} tem carga final mas a tabela nao tem impact.he[{ammo!r}]")
        fin["MediaEffects"] = _media(_preset_paths(he[0]), fin.get("MediaEffects"), shake)
        if MES_ON_FINISH:
            fin["MediaEffectsScale"] = _mes(he[1])
    elif light and isinstance(pen, dict) and isinstance(fin, str) and fin.strip().endswith("PenetratingOperational"):
        # AP sem carga: o impacto cheio UMA vez onde a granada para (HitEffects copiados = R4; 406: + destrocos)
        new = {}
        if "ReduceEffectsByPenetration" in pen:
            new["ReduceEffectsByPenetration"] = pen["ReduceEffectsByPenetration"]
        new["HitEffects"] = copy.deepcopy(pen.get("HitEffects", []))
        refs = _preset_paths(hp)
        if imp.get("extra_ap") and ammo == "ap":
            refs = refs + [f"&<{_data_shot(DEBRIS)}>"]
        new["MediaEffects"] = refs + _sounds(op["MediaEffects"])
        new["MediaEffectsScale"] = _mes(hmes * AP_FINISH_K)
        hit["FinishedPenetratingOperational"] = new
    if light:
        _pop(s, comps, v)


def _decorate_explosive(s, top, v):
    """Boiuna 2.0 (obuseiro da AC, sem visual nuclear): HE = HE_BIG x1,375 (r 5,5 / 4), AC = AC_BLAST_L x2,25 +
    destrocos; HitShield com a mesma midia e a mesma escala; abatida no ar = POP_L."""
    imp = v["impact"]
    ammo = v["ammo"]
    comps = top["Components"]
    hit = comps["Hit"]
    shake = (s.get("shake", 0), s.get("vfx_shake_time", 0.5))
    hp, hmes = _hull_entry(imp, ammo)
    refs = _preset_paths(hp) + [f"&<{_data_shot(p)}>" for p in (imp.get("extra") or {}).get(ammo, [])]
    op = hit["HitOperational"]
    op["MediaEffects"] = _media(refs, op.get("MediaEffects"), shake)
    op["MediaEffectsScale"] = _mes(hmes)
    # HitShield explicito (dano proprio) com &../HitOperational/MediaEffects: mesma midia e a mesma escala, senao o
    # acerto no escudo tocava a explosao x1 (HitShield e HitOperational de um SimpleHit sao o mesmo tipo de bloco)
    sh = hit.get("HitShield")
    if isinstance(sh, dict):
        sh["MediaEffectsScale"] = _mes(hmes)
    if FXK.art_switch("pen_media") != "full":
        _pop(s, comps, v)


def _decorate_flak(s, top, v):
    """Rajada da flak/CIWS (HitNothing; HitShield/HitOperational/HitStructural = &HitNothing herdam): HE = clarao +
    fumaca vanilla + estilhacos SHR_L/SHR_H; FRAG = clarao branco-frio + leque (ou anel) + baforada cinza-azulada
    (FRAG_BURST_L/H, <= 8/12 particulas, sem coluna de fumaca). Escala por defesa, tremor so na Pororoca."""
    imp = v["impact"]
    burst = imp.get("burst")
    if not burst:
        return
    hn = top.get("HitNothing")
    if not isinstance(hn, dict):
        return
    shake = tuple((imp.get("shake") or [0, 0])[:2])
    hn["MediaEffects"] = _media(_preset_paths(burst[0]), hn.get("MediaEffects"), shake)
    if MES_ON_HITNOTHING:
        hn["MediaEffectsScale"] = _mes(burst[1])


HIT_TYPES = ("SimpleHit", "VolumeHit", "PenetratingHit")


def _decorate_fragment(s, top):
    """Fragmento da FRAG: so a faisca chaingun_sparks (2-4) no projetil inimigo atingido (HitBullet) e a sprite do
    fragmento quando o construtor nao pos nenhuma; casco/escudo sem efeito (o fragmento so defende)."""
    comps = top.get("Components")
    if not isinstance(comps, dict):
        return
    v = s.get("vfx") or {}
    fr = v.get("fragment") or {}
    sparks = [f"&<{_data_shot(p)}>" for p in (fr.get("hit_bullet") or ["chaingun_shot/particles/chaingun_sparks"])]
    for c in comps.values():
        if isinstance(c, dict) and c.get("Type") in HIT_TYPES and isinstance(c.get("HitBullet"), dict):
            c["HitBullet"]["MediaEffects"] = sparks + _sounds(c["HitBullet"].get("MediaEffects"))
    if not any(isinstance(c, dict) and c.get("Type") in ("Sprite", "AnimatedSprite") for c in comps.values()):
        comps.update(fragment_components(s))


def decorate(s, top):
    """Seam S3: midia de impacto por calibre, no lugar (so visual; HitEffects e estatisticas intocados)."""
    if s.get("plasma_fx"):
        return None
    kind = s.get("kind")
    if kind == "frag_fragment":
        _decorate_fragment(s, top)
        return None
    v = s.get("vfx")
    if not v:
        return None
    if kind == "kinetic" and isinstance(top.get("Components", {}).get("Hit"), dict):
        _decorate_kinetic(s, top, v)
    elif kind == "explosive" and isinstance(top.get("Components", {}).get("Hit"), dict):
        _decorate_explosive(s, top, v)
    elif kind == "flak":
        _decorate_flak(s, top, v)
    return None


# ============================================================================= conferencias (selfcheck)
_BLOCK = r"^(\t*){name}\n\1\{{\n(.*?)\n\1\}}"


def _blocks(text, name):
    return [m.group(2) for m in re.finditer(_BLOCK.format(name=name), text, re.M | re.S)]


def _val(block, field):
    m = re.search(rf"^\t*{field} = ({_NUM})$", block, re.M)
    return float(m.group(1)) if m else None


def _vc(block):
    m = re.search(r"^\t*VertexColor = \[(\d+), (\d+), (\d+)", block, re.M)
    return [int(m.group(i)) for i in (1, 2, 3)] if m else None


def _full_refs():
    """Arquivos dos presets cheios de casco (os que NAO podem tocar nas pecas atravessadas)."""
    pen = set()
    for k in ("PEN_S", "PEN_M", "PEN_L"):
        pen |= set(PRESETS[k])
    full = set()
    for k in ("MG", "MGH", "AC", "AC_FAST", "L", "D", "HE", "HE_BIG", "HE_POP"):
        full |= set(PRESETS.get(k, []))
    return {_data_shot(p) for p in full - pen}


def selfcheck(mod_dir, spec):
    """WP03: R4 da limpeza 1.x nos fontes; as 18 chaves da escada com arte; orcamentos (PEN <= 6, AC 17/17/37/49,
    FRAG 8/12); arquivos escritos; nos tiros do mod: halo (GlowSprite IsLight) com refl 0 e add 0, toda luz de casco
    (GlowSprite2) com o canal mais fraco <= c_min_limit(refl) e AC/slug a refl 4; nenhuma peca atravessada
    (PenetratingOperational) com o preset cheio ou com a midia do HitOperational; Boiuna sem visual nuclear."""
    probs = []
    for p in (os.path.abspath(__file__), os.path.join(os.path.dirname(os.path.abspath(__file__)), "fxkit.py")):
        probs += FXK.legacy_scan(p)
    meta = _shell_art()
    for key in LADDER:
        it, m = art_item(key)
        if not it:
            probs.append(f"chave da escada {key} sem arte (art3d/bs_shells2)")
    # orcamentos de particulas
    for name, cap in COUNTS["budgets"].items():
        base = name.split("+")[0]
        n = preset_particles(base) + (int(COUNTS[DEBRIS]) if name.endswith("+debris") else 0)
        if n > cap:
            probs.append(f"preset {name}: {n} particulas > {cap}")
    # arquivos
    for name in _needed():
        if not os.path.isfile(os.path.join(mod_dir, OUT_DIR, f"{name}.rules")):
            probs.append(f"{OUT_DIR}/{name}.rules nao foi escrito")
    for key in OWN_FX:
        sub, name = key.split("/", 1)
        if not os.path.isfile(os.path.join(mod_dir, FX_DIRS[sub], f"{name}.rules")):
            probs.append(f"{FX_DIRS[sub]}/{name}.rules nao foi escrito")
    if meta:
        for f in meta["files"]:
            if not os.path.isfile(os.path.join(mod_dir, ART_OUT, f)):
                probs.append(f"{ART_OUT}/{f} nao foi copiado")
                break
    # tiros do mod
    split = FXK.art_switch("light_split") != "legacy"
    light = FXK.art_switch("pen_media") != "full"
    refl4 = {tuple(FXK.pal(k)["hull"]): k for k in ("ac", "rail")}
    full = _full_refs()
    shots = os.path.join(mod_dir, "shots")
    for dp, _dn, fn in os.walk(shots):
        for f in fn:
            if not f.endswith(".rules"):
                continue
            rel = os.path.relpath(os.path.join(dp, f), mod_dir).replace(os.sep, "/")
            with open(os.path.join(dp, f), encoding="utf-8") as fh:
                text = fh.read()
            if "bs_plasma_fx" in text:
                continue           # plasma: Fase B sem mudanca (luz propria do plasma_fx)
            if split:
                for b in _blocks(text, "GlowSprite"):
                    if "IsLight = true" in b and (_val(b, "_litReflectiveStrength") or 0) != 0:
                        probs.append(f"{rel}: halo GlowSprite com _litReflectiveStrength != 0 (lava o casco branco)")
                    if "IsLight = true" in b and (_val(b, "_litAdditiveStrength") or 0) != 0:
                        probs.append(f"{rel}: halo GlowSprite com _litAdditiveStrength != 0")
            for b in _blocks(text, "GlowSprite2"):
                vc, refl = _vc(b), _val(b, "_litReflectiveStrength")
                if vc is None or refl is None:
                    continue
                if refl > 0 and min(vc) > FXK.c_min_limit(refl):
                    probs.append(f"{rel}: luz de casco {vc} refl {refl:g} lava o casco branco (c_min > "
                                 f"{FXK.c_min_limit(refl)})")
                if tuple(vc) in refl4 and refl != 4:
                    probs.append(f"{rel}: luz de casco de {refl4[tuple(vc)]} com refl {refl:g} (tem de ser 4)")
            if light:
                for b in _blocks(text, "PenetratingOperational"):
                    if "&../HitOperational/MediaEffects" in b or any(r in b for r in full):
                        probs.append(f"{rel}: PenetratingOperational com o preset cheio (usar PEN_*)")
            if "howitzer" in rel and ("bs_nuke_fx" in text or "radiation" in text):
                probs.append(f"{rel}: Boiuna com visual nuclear (trevo/anel verde)")
    return probs
