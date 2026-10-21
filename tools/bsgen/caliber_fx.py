"""Efeitos por CALIBRE do Bullet Strike (modulo opcional, CONTRATOS secao 2.2): arma maior, tiro maior.

Fonte dos numeros: tools/spec/bullet_strike_vfx.json (copia da tabela aprovada do design de calibre + extensoes do
gerador + X2). So VISUAL (CONTRATOS R4): nunca muda HitEffects, dano, raio, Physics, Targetable, alcance,
velocidade, municao, toggles ou tempos; so MediaEffects, MediaEffectsScale, componentes de sprite/luz/midia e
arquivos de particula proprios. Plasma (s["plasma_fx"], linhas com mm = null) fica de fora (R3).

Entra pelos seams (CONTRATOS secao 1), sem editar bs_data / shots / build_mod / ciws:
  annotate(data)                    D1: chaves visuais nos projeteis (s["vfx"], look, tamanhos, rastro, tremor) e
                                        nos efeitos de boca das armas/defesas (g["fx"] / d["fx"]);
  projectile_components(s, trail)   S1: visual em voo (tracante, granada, granada nuclear);
  decorate(s, top)                  S3: midia de impacto por calibre (presets + MediaEffectsScale), HitShield
                                        explicito, carga final HE, nuclear (anel/brilho/abatido), rajada da flak;
  write(out, header)                B2: copias escaladas em shots/bs_cal_fx/;
  copy_art(out)                     B3: PNGs das granadas (art3d/bs_shells -> shots/bs_shell_art/).

Dois mecanismos (caliber_design 1.A / 1.B):
  * impactos: arquivos vanilla por referencia + MediaEffectsScale (numero puro) no bloco de acerto. Campo vanilla
    em bloco de acerto: shots/bullet_railgun/bullet_railgun.rules l.99/139/173 (0.30.3); numero puro no SW:ACD
    (alvo 0.30.4): shots/missiles/proton_rocket/proton_rocket.rules l.129/187 ("MediaEffectsScale = 1.5");
  * boca e rastros: COPIAS escaladas (scaled_copy) de 12 arquivos vanilla guardados em tools/vanilla_fx/ (texto
    identico no 0.30.3 e no 0.30.5 RC1). A copia multiplica so o Renderer.BaseSize (nunca tambem LocalScale/
    base_scale: daria s^2), mais posicoes/velocidades (s), quantidade (n), vida (life), Delay e Bucket, e cada botao
    confere quantos campos achou (texto vanilla diferente = build para, nunca tamanho errado em silencio). O Lerp do
    chaingun_shoot sobrescreve a escala de mundo, entao MediaEffectsScale nao serve para a boca.
Import: so rules_dsl, bsgen.fxkit, bsgen.trails e a biblioteca padrao (nunca bs_data / build_mod / bsgen.shots no
nivel do modulo: shots importa este arquivo).
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

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # tools/
ROOT = os.path.dirname(HERE)                                            # repositorio
SPEC_PATH = os.path.join(HERE, "spec", "bullet_strike_vfx.json")
VENDOR_DIR = os.path.join(HERE, "vanilla_fx")
OUT_DIR = "shots/bs_cal_fx"           # copias escaladas (irma de bs_trails / bs_plasma_fx / bs_nuke_fx)
ART_OUT = "shots/bs_shell_art"        # PNGs das granadas (CONTRATOS secao 3)
ART_SRC = os.path.join(ROOT, "art3d", "bs_shells")
ART_PREFIX = "../bs_shell_art/"       # visto de shots/<id>/<id>.rules
D = "./Data"

with open(SPEC_PATH, encoding="utf-8") as _fh:
    SPEC = json.load(_fh)
WEAPONS = SPEC["weapons"]
COLORS = SPEC["ammo_colors"]
PRESETS = SPEC["hit_presets"]

# ============================================================================= copias escaladas (1.B)
# fontes guardadas em tools/vanilla_fx/<nome do arquivo vanilla>.rules (caminho vanilla em SPEC["sources"])
VENDORED = ("CG", "CGF", "CGS", "CD", "CDF", "CDR", "CDS", "RGD", "FF", "FS", "SHR", "TSM")
# balde da copia quando o vanilla esta num balde de baixo (ficaria sob o nosso teto): FlakShootSmoke e Lower1
DEFAULT_BUCKET = {"FS": "RoofCannonSmoke", "TSM": "BulletTrailUpper"}
# fontes novas = fonte vanilla + trocas fixas (caliber_design 1.B "New sources")
#   RADF: clarao do deck com a textura do trevo (radiation.png) em verde; 0,25 s -> 0,6 s. Cor de UM canal (0, 1, 0):
#         luz particle_light com SCREEN; com o verde do design [.45, 1, .25] o R e o B tambem estouram no casco e o
#         trevo sairia branco (mesma conta do WP2, vfx_impl/WP2/light_model.py)
#   SHR_L / SHR_H: estilhacos da flak com 30..40 / 100..120 por rajada (o vanilla solta 150..200)
#   TSM_G: esteira de fumaca da Boiuna cinza-esverdeada (troca R por G na rampa color_add, quente perto da granada)
NEW_SOURCES = {
    "RADF": ("CDF", {"texture": f"{D}/shots/missile_nuke/radiation.png", "color": (0, 1, 0, 1), "life": 2.4}),
    "SHR_L": ("SHR", {"count": (30, 40)}),
    "SHR_H": ("SHR", {"count": (100, 120)}),
    "TSM_G": ("TSM", {"color": "swap_rg"}),
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


def vendor_path(src):
    return os.path.join(VENDOR_DIR, os.path.basename(SPEC["sources"][src]["file"]))


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
            elif typ == "SetValue" and out == "base_color" and isinstance(color, tuple):
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
        elif where == "upd" and typ == "ColorRamp" and _field(body, "ColorOut") == "color_add" and color == "swap_rg":
            # tinge de verde a parte quente da fumaca: cada chave (R, G, B) -> (G, R, B)
            def _swap(m):
                return f"{m.group(1)}{m.group(4)}{m.group(3)}{m.group(2)}{m.group(5)}"
            new, c = re.subn(rf"(\t+Rf = )({_NUM})(\n\t+Gf = )({_NUM})(\n)", _swap, new)
            if c < 1:
                raise ValueError(f"caliber_fx {src}: rampa color_add sem chaves")
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
    if isinstance(color, tuple) or color == "swap_rg":
        exp["color"] = 1
    if got != exp:
        raise ValueError(f"caliber_fx: a fonte {src} ({vendor_path(src)}) nao bate com o esperado: achou {got}, "
                         f"esperava {exp} (texto vanilla mudou?)")
    out = text
    for a, b, new in sorted(reps, reverse=True):
        out = out[:a] + new + out[b:]
    # textura do material (so RADF)
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
        name += "_c" + (color if isinstance(color, str) else "".join(f"{_iround(v * 255):02x}" for v in color))
    if count is not None:
        name += f"_k{int(count[0])}_{int(count[1])}"
    return name


def scaled_copy(src, s, n=1, life=1, speed=1, delay=0, bucket=None, texture=None, color=None, count=None):
    """(nome, texto) da copia escalada da fonte src (chave de SPEC["sources"] ou de NEW_SOURCES).
      s: tamanho (so Renderer.BaseSize x s); posicoes do EmitterDef x s; velocidades x s * speed;
      n: quantidade (EmitPerOneShot Min/Max e EmitPerSecond x n, arredondado, minimo 1 onde nao era 0);
      life: vida (Lifetime e SetRandom lifetime x life); delay: Delay do topo (s); bucket: Bucket do topo;
      texture / color / count: trocas avulsas (as fontes novas ja trazem as delas).
    O texto sai sem cabecalho (write() poe o de sempre)."""
    base, fixed = _src_parts(src)
    tex = texture or fixed.get("texture")
    col = color if color is not None else fixed.get("color")
    cnt = count if count is not None else fixed.get("count")
    lf = life * fixed.get("life", 1)
    name = copy_name(src, s, n, life, speed, delay, bucket, texture, color, count)
    return name, _patch(base, s, n, lf, speed, delay, bucket, tex, col, cnt)


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
    """smoke_trail da tabela {src TSM, eps, scale [a, b], life [a, b], tint} -> (fonte, kwargs). O tamanho vem do
    BaseSize (base_scale vanilla 4..5 -> scale / 4,5), a quantidade do EmitPerSecond (60) e a vida do lifetime
    vanilla 0,9..1,1 (media 1)."""
    src = st["src"] + ("_G" if st.get("tint") else "")
    s = (st["scale"][0] + st["scale"][1]) / 2 / 4.5
    life = (st["life"][0] + st["life"][1]) / 2 / 1.0
    return src, {"s": round(s, 4), "n": round(st["eps"] / 60, 4), "life": round(life, 4)}


def _needed():
    """{nome: (fonte, kwargs)} de TODAS as copias que a tabela usa (boca, culatra, esteira, estilhacos). write() grava
    todas; as referencias de annotate/decorate/projectile_components saem do mesmo copy_name."""
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
        burst = (row.get("impact") or {}).get("burst")
        if burst:
            for p in PRESETS[burst[0]]:
                if p.startswith("bs:"):
                    add(p[3:], {"s": 1.0})
    return need


def all_files():
    """{nome: texto} das copias (sem cabecalho)."""
    return {name: scaled_copy(src, **kw)[1] for name, (src, kw) in sorted(_needed().items())}


def write(out, header):
    """Seam B2: grava shots/bs_cal_fx/*.rules (inclusive com --no-art: so texto)."""
    head = "\n".join(f"// {ln}" for ln in header.split("\n"))
    for name, (src, kw) in sorted(_needed().items()):
        base, fixed = _src_parts(src)
        what = ", ".join(f"{k}={_num(v)}" for k, v in kw.items())
        # (caminhos seguidos de espaco: o conferidor de ./Data do build_mod tambem le os comentarios)
        extra = ("; trocas fixas: " + " ; ".join(f"{k} = {v}" for k, v in fixed.items()) + " ") if fixed else ""
        note = (f"// Copia escalada de ./Data/{SPEC['sources'][base]['file']} (fonte {src}: {what}{extra}).\n"
                f"// Texto vanilla em tools/vanilla_fx/{os.path.basename(vendor_path(base))}; so mudam BaseSize, "
                f"posicoes, velocidades, quantidade, vida, Delay, Bucket e caminhos ./Data.\n")
        out.text(f"{OUT_DIR}/{name}.rules", head + "\n" + note + scaled_copy(src, **kw)[1])


def cal_ref(name, frm):
    """Caminho (sem &<>) de uma copia de OUT_DIR; frm = "shot" | "part" (fxkit.ref)."""
    return FXK.ref(OUT_DIR, name, frm)


# ============================================================================= presets de impacto (1.A)
def _preset_paths(name):
    """Arquivos de um preset de SPEC["hit_presets"] como entradas de MediaEffects (vistas de um projetil)."""
    out = []
    for p in PRESETS[name]:
        if p.startswith("bs:"):
            out.append(f"&<{cal_ref(copy_name(p[3:], 1.0), 'shot')}>")
        else:
            out.append(f"&<{_data_shot(p)}>")
    return out


def _data_shot(p):
    """'chaingun_shot/particles/x' (relativo a Data/shots) -> './Data/shots/chaingun_shot/particles/x.rules'."""
    return D + "/" + os.path.normpath(os.path.join("shots", p)).replace(os.sep, "/") + ".rules"


DEBRIS = "../common_effects/particles/explosions/big_part_explode_debris"
NUKE_SHOT_DOWN = [f"&<{_data_shot('missile_nuke/particles/missile_nuke_flash')}>"]


# ============================================================================= arte das granadas (CONTRATOS 3)
_ART = {}


def _shell_art():
    """meta.json da arte das granadas ou None (sem arte = dardo vanilla no tamanho novo). BS_SHELL_ART_DIR troca a
    pasta (folhas de teste); pasta sem meta.json = sem arte (testa o caminho de reserva)."""
    d = os.environ.get("BS_SHELL_ART_DIR") or ART_SRC
    if d in _ART:
        return _ART[d]
    p = os.path.join(d, "meta.json")
    meta = None
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            meta = json.load(fh)
        if meta.get("kind") != "shells":
            raise ValueError(f"caliber_fx: {p} nao e de granadas (kind {meta.get('kind')!r})")
        missing = [f for f in meta.get("files", []) if not os.path.isfile(os.path.join(d, f))]
        if missing:
            raise FileNotFoundError(f"caliber_fx: {p} cita arquivos que nao existem: {missing[:5]}")
        for key in ("he", "ap", "nuke"):
            it = (meta.get("items") or {}).get(key)
            if not it or not it.get("file") or not it.get("size"):
                raise KeyError(f"caliber_fx: {p} sem o item {key!r} (file/size)")
            for f in [it.get("file"), it.get("normals"), it.get("mask")] + [(it.get("lights") or {}).get("file")]:
                if f and f not in meta.get("files", []):
                    raise KeyError(f"caliber_fx: {p}: {key} usa {f!r}, fora da lista files")
        meta = dict(meta, _dir=d)
    _ART[d] = meta
    return meta


def copy_art(out):
    """Seam B3: copia as PNGs da arte das granadas para shots/bs_shell_art/ (full e --no-art)."""
    meta = _shell_art()
    if not meta:
        return
    dst = os.path.join(out.root, ART_OUT)
    os.makedirs(dst, exist_ok=True)
    for f in meta["files"]:
        shutil.copyfile(os.path.join(meta["_dir"], f), os.path.join(dst, f))


# ============================================================================= anotacao (D1)
ART_KEY = {"std": "he", "emp": "he", "bullet": "he", "ap": "ap", "aphe": "ap", "nuclear": "nuke"}


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


def _annotate_shot(s, short, row, ammo, oc):
    pr = copy.deepcopy(row.get("projectile"))
    imp = copy.deepcopy(row.get("impact") or {})
    s["vfx"] = {"short": short, "ammo": ammo, "oc": bool(oc), "mm": row["mm"], "tier": row.get("tier"),
                "projectile": pr, "impact": imp}
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
            s["sprite_size"] = pr["body"][0]
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


def _annotate_burst(s, short, row):
    imp = copy.deepcopy(row.get("impact") or {})
    s["vfx"] = {"short": short, "ammo": None, "oc": False, "mm": row["mm"], "tier": row.get("tier"),
                "projectile": None, "impact": imp}
    sh = imp.get("shake") or [0, 0]
    s["vfx_shake_time"] = sh[1]


def annotate(data):
    """Seam D1: liga os projeteis as linhas da tabela pelos modos das armas (shot / shot_oc) e pelos feixes das
    defesas (beam), nunca pelo nome do arquivo. So chaves visuais; as de som, volume, raio, dano, tipo, categoria,
    vida, velocidade e alcance nao sao tocadas."""
    by_file = {s["file"]: s for s in data.SHOTS}
    for g in data.GUNS:
        row = _row(g["short"])
        if row is None:
            continue
        for m in g["modes"]:
            for f, oc in ((m["shot"], False), (m.get("shot_oc"), True)):
                if not f or (oc and f == m["shot"]):
                    continue
                s = by_file[f]
                if s.get("plasma_fx"):
                    continue
                _annotate_shot(s, g["short"], row, m["ammo"], oc)
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
        _annotate_burst(by_file[d["beam"]], d["short"], row)


# ============================================================================= visual em voo (S1)
GLOW = {"File": Q(f"{D}/common_effects/particles/blob.png"), "MipLevels": "max", "SampleMode": "Linear"}
FANCY = Q(f"{D}/common_effects/fancy_light.shader")
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


def _glow(wh, color, offset, z, unlit):
    """Brilho IsLight (fancy_light) do mesmo formato de shots._sprite_components."""
    return {"Type": "Sprite", "RenderBucket": "BulletUpper4", "Z": z, "IsLight": True,
            "Offset": [round(offset, 3), 0],
            "Sprite": {"Texture": dict(GLOW), "Size": list(wh), "VertexColor": [int(c) for c in color],
                       "TargetBlendMode": "Add", "Shader": FANCY, "_z": 1, "_nrmlStrengthLimit": 1,
                       "_litReflectiveStrength": 24, "_litAdditiveStrength": 0.05, "_unlitAdditiveStrength": unlit}}


def _ammo_colors(ammo):
    return COLORS.get(ammo) or COLORS["std"]


def _tracer_components(s, v, trail_ref):
    """Tracante (metralhadoras, 20/30 mm): risco + nucleo + cabeca + borrao + brilho (+ rastro no 20 mm).
    Molde do pd_shot.rules (Size [L, W], Offset -0.4375 L, LerpScaleFrom [.25, 1], LerpTime .05), igual ao caminho
    antigo de shots._sprite_components; so os tamanhos mudam com o calibre."""
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
    comps["GlowSprite"] = _glow(list(pr["glow"]), col["glow"], -0.4 * L, 0, 0.2)
    if trail_ref:
        comps["Trail"] = {"Type": "MediaEffects", "MediaEffects": [trail_ref]}
    return comps


def shell_layout(pr):
    """Camadas da granada no jogo (x do centro em tiles a partir do CENTRO do corpo, +x = nariz; [L, W] em tiles):
    corpo centrado (como o bullet_large vanilla e os misseis); tracante na base, por baixo do corpo, com o centro em
    -(0,55 L + 0,4375 tl) (caliber_design 3.5); nucleo branco-quente na frente do tracante; clarao da base (head, X2)
    em -0,5 L; brilho IsLight centrado. Usado tambem pela previa da escada (vfx_impl/WP3/ladder)."""
    L, W = pr["body"]
    tl, tw = pr["tracer"]
    lay = {"body": (0.0, [L, W]),
           "tracer": (-(0.55 * L + 0.4375 * tl), [tl, round(tw * 1.4 / MOCK_W, 4)]),
           "core": (-(0.55 * L + 0.1 * tl), [round(0.45 * tl, 4), round(tw * 0.8 / MOCK_W, 4)]),
           "glow": (0.0, list(pr["glow"]))}
    if pr.get("head"):
        lay["head"] = (-0.5 * L, [round(1.6 * pr["head"], 4)] * 2)
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
    """Granada (76/155/406) e granada nuclear (Boiuna): corpo iluminado da arte (art3d/bs_shells) com a faixa na cor
    da municao, tracante na base, clarao da base, brilho IsLight, rastro e esteira de fumaca; na Boiuna o atlas de
    luzes das faixas e o trevo de radiacao girando (fxkit.radiation_components, molde missile_nuke_stage1.rules
    l.72-116). Sem arte: o dardo vanilla no tamanho novo, com o resto igual."""
    pr = v["projectile"]
    ammo = v["ammo"]
    nuke = pr["look"] == "nuke_shell"
    col = _ammo_colors(ammo)
    lay = shell_layout(pr)
    L, W = pr["body"]
    comps = {}
    meta = _shell_art()
    item = (meta or {}).get("items", {}).get(ART_KEY.get(ammo, "he")) if meta else None
    if item:
        art = FXK.art_sprite_components(ART_PREFIX, item, [L, W],
                                        mask_color=(col["band"] if item.get("mask") else None))
        comps.update(art)
    else:
        comps["Sprite"] = _dart(L)
    x, wh = lay["tracer"]
    tr = _blob("BulletUpper2", wh, col["tracer"], x)
    tr["LerpScaleFrom"] = [0.25, 1]
    tr["LerpTime"] = 0.05
    comps["TailSprite"] = tr
    x, wh = lay["core"]
    core = _blob("BulletUpper2", wh, col["core"], x)
    core["LerpScaleFrom"] = [0.25, 1]
    core["LerpTime"] = 0.05
    comps["CoreSprite"] = core
    if "head" in lay:
        x, wh = lay["head"]
        comps["HeadSprite"] = _blob("BulletUpper2", wh, WHITE_HOT, x)
    x, wh = lay["glow"]
    # nuclear: ammo_colors.nuclear.glow = [0, 255, 0] no spec (= fxkit.NUKE_GREEN_HULL). O brilho de 30x15 fica em
    # cima do trevo; com o verde do design [120, 255, 60] e forca 24 os tres canais estouravam e o casco virava uma
    # mancha branca em volta do trevo (modelo WP2/light_model.py); com um canal so fica verde nos tres cascos
    comps["GlowSprite"] = _glow(wh, col["glow"], x, pr.get("glow_z", 0), 0.125)
    if nuke:
        big, small = pr["spin_big"], pr["spin_small"]
        anc = [0, 0]
        if item and item.get("anchors", {}).get("radiation"):
            ax, ay = item["anchors"]["radiation"]
            anc = [round(ax * L / item["size"][0], 4), round(ay * W / item["size"][1], 4)]
        # luz grande de UM canal (fxkit.NUKE_GREEN_HULL: o verde do design deixava o trevo branco no casco, WP2);
        # o trevo pequeno aditivo fica com a cor da tabela
        rad = FXK.radiation_components(big["size"], float(big["spin"].rstrip("d")), small["size"],
                                       float(small["spin"].rstrip("d")), anc, FXK.NUKE_GREEN_HULL,
                                       big_bucket=big.get("bucket", "BulletUpper2"),
                                       small_bucket=small.get("bucket", "BulletUpper4"),
                                       small_color=small.get("color", FXK.NUKE_GREEN_TINT))
        comps.update(rad)
    if trail_ref:
        comps["Trail"] = {"Type": "MediaEffects", "MediaEffects": [trail_ref]}
    if s.get("vfx_smoke"):
        # esteira de fumaca (missile_he_thruster_smoke copiado; como o propulsor vanilla: Rotation 180d na base,
        # missile_he.rules l.96-108)
        comps["SmokeTrail"] = {"Type": "MediaEffects", "Offset": [round(-0.5 * L, 3), 0], "Rotation": "180d",
                               "MediaEffects": [f"&<{cal_ref(s['vfx_smoke'], 'shot')}>"]}
    return comps


def projectile_components(s, trail_ref):
    """Seam S1: componentes visuais em voo por calibre, ou None (caminho antigo de shots._sprite_components)."""
    if s.get("plasma_fx"):
        return None
    v = s.get("vfx")
    if not v or not v.get("projectile"):
        return None
    look = v["projectile"]["look"]
    if look == "tracer":
        return _tracer_components(s, v, trail_ref)
    if look in ("shell", "nuke_shell"):
        return _shell_components(s, v, trail_ref)
    return None


# ============================================================================= impactos (S3)
SOUND_BASE = "/BASE_SOUNDS/AudioExterior"
SHAKE_BASE = "/BASE_SHAKE"
# MediaEffectsScale em dois blocos onde o corpus (vanilla 0.30.3/0.30.5 + SW:ACD) nunca o usa: a carga final HE
# (FinishedPenetratingOperational) e a rajada da flak (HitNothing do feixe). Sao o mesmo tipo de grupo dos blocos
# irmaos onde o campo e provado (PenetratingHit HitOperational/PenetratingOperational: bullet_railgun.rules 0.30.3
# l.99/139; HitOperational de raiz de feixe: ion_beam.rules 0.30.3 l.165), numero puro como no SW:ACD
# (proton_rocket.rules l.129). Campo desconhecido o jogo ignora (pior caso: o efeito sai x1). schema_check acusa
# duas categorias novas por isso; False aqui tira as duas e volta esses efeitos ao tamanho vanilla (a granada de
# 76 mm volta a desenhar a explosao inteira do missil HE). Teste no jogo: T-CAL-1.
MES_ON_FINISH = True
MES_ON_HITNOTHING = True


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
    ent = hull.get(ammo) or hull.get("std") or next(iter(hull.values()))
    return ent


def _decorate_kinetic(s, top, v):
    imp = v["impact"]
    ammo = v["ammo"]
    hit = top["Components"]["Hit"]
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
    # escudo: preset proprio (sem fumaca nem destrocos), HitEffects iguais aos de antes (R4)
    if imp.get("shield"):
        shp, shmes = imp["shield"]
        refs = _preset_paths(shp)
        he_ammo = (imp.get("he") or {}).get(ammo)
        if he_ammo and imp.get("shield_he") and isinstance(hit.get("FinishedPenetratingOperational"), dict):
            # granada HE no escudo: + clarao da carga; um MediaEffectsScale por bloco -> o menor dos dois (a bola de
            # fogo fica do tamanho da carga; o clarao do impacto encolhe junto)
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
    # pecas atravessadas: as particulas do primeiro acerto, menores (pen_mes; sem ele, a escala do casco), com o som
    # de antes (R5) e SEM tremor: antes o bloco apontava para a midia do HitOperational e cada peca atravessada
    # tremia de novo (406: ate 13 pecas x 0,25). O vanilla tambem nao treme aqui (bullet_deck.rules 0.30.3 l.119-145)
    pen = hit.get("PenetratingOperational")
    if isinstance(pen, dict):
        pmes = imp.get("pen_mes")
        refs = _preset_paths(hp)
        if imp.get("extra_ap") and ammo == "ap":
            # 406 Perfurante: destrocos grandes a cada peca atravessada (big_part_explode_debris ignora a escala)
            refs = refs + [f"&<{_data_shot(DEBRIS)}>"]
        pen["MediaEffects"] = refs + _sounds(op["MediaEffects"])
        pen["MediaEffectsScale"] = _mes(pmes if pmes is not None else hmes)
    # carga final HE (onde a granada para): preset por municao, escala = raio / 4 (missile_he desenhado para r4)
    fin = hit.get("FinishedPenetratingOperational")
    if isinstance(fin, dict):
        he = (imp.get("he") or {}).get(ammo)
        if not he:
            raise KeyError(f"caliber_fx: {s['file']} tem carga final mas a tabela nao tem impact.he[{ammo!r}]")
        fin["MediaEffects"] = _media(_preset_paths(he[0]), fin.get("MediaEffects"), shake)
        if MES_ON_FINISH:
            fin["MediaEffectsScale"] = _mes(he[1])


def _decorate_explosive(s, top, v):
    """Boiuna: cogumelo vanilla x MES + anel verde + brilho residual (fxkit, compartilhados com a Iara); abatida no
    ar: clarao do missil nuclear + anel pequeno (no lugar do clarao da flak)."""
    imp = v["impact"]
    ammo = v["ammo"]
    comps = top["Components"]
    hit = comps["Hit"]
    shake = (s.get("shake", 0), s.get("vfx_shake_time", 0.5))
    hp, hmes = _hull_entry(imp, ammo)
    if v.get("oc") and imp.get("oc_mes"):
        hmes = imp["oc_mes"]
    refs = _preset_paths(hp) + [FXK.nuke_media(n, "shot") for n in imp.get("extra") or []]
    op = hit["HitOperational"]
    op["MediaEffects"] = _media(refs, op.get("MediaEffects"), shake)
    op["MediaEffectsScale"] = _mes(hmes)
    # HitShield explicito da Boiuna (dano proprio) ja usa &../HitOperational/MediaEffects: mesma midia, e agora a
    # mesma escala (1,15; OC 1,4), senao o acerto no escudo tocava o cogumelo x1. HitShield e HitOperational de um
    # SimpleHit sao o mesmo tipo de bloco (missile_he.rules l.125 "HitShield = &HitOperational"; schema_check
    # SAME_TYPE), e o HitShield da ogiva da Iara (SimpleHit) ja leva MediaEffectsScale no mesmo build (missile_fx).
    sh = hit.get("HitShield")
    if isinstance(sh, dict):
        sh["MediaEffectsScale"] = _mes(hmes)
    if imp.get("shot_down"):
        tg = comps.get("Targetable")
        if isinstance(tg, dict) and isinstance(tg.get("OnDeath"), dict):
            # sem MediaEffectsScale no OnDeath (nao aparece no corpus): o clarao vanilla fica x1, como o missil
            # nuclear vanilla abatido (missile_nuke_stage1.rules HitFriendly); o anel pequeno ja e pequeno
            tg["OnDeath"]["MediaEffects"] = list(NUKE_SHOT_DOWN) + [FXK.nuke_media("bs_nuke_ring_small", "shot")]


def _decorate_flak(s, top, v):
    """Rajada da flak/CIWS (HitNothing; HitShield/HitOperational/HitStructural = &HitNothing herdam): clarao + fumaca
    vanilla + estilhacos SHR_L/SHR_H (copia leve), escala por defesa, tremor so na Pororoca."""
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


def decorate(s, top):
    """Seam S3: midia de impacto por calibre, no lugar (so visual; HitEffects e estatisticas intocados)."""
    if s.get("plasma_fx"):
        return None
    v = s.get("vfx")
    if not v:
        return None
    kind = s.get("kind")
    if kind == "kinetic" and isinstance(top.get("Components", {}).get("Hit"), dict):
        _decorate_kinetic(s, top, v)
    elif kind == "explosive" and isinstance(top.get("Components", {}).get("Hit"), dict):
        _decorate_explosive(s, top, v)
    elif kind == "flak":
        _decorate_flak(s, top, v)
    return None
