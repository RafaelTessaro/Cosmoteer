"""Efeitos da railgun Tupa 2.0 (dono: WP09): tudo AZUL (palette.rail), so as brasas do ALVO quentes.

Modulo FX do registro do tools/build_mod.py (API = 2; BS_FX_EXT=0 desliga: o bsgen.railgun cai nos efeitos vanilla
do railgun, que ja sao ciano). Ganchos: write(out, header) (shots/bs_rail_fx/) e selfcheck(mod_dir, spec). Quem usa:
bsgen.railgun pelas listas media(<grupo>, frm) (MediaEffects prontos, '&<...>') e files(<grupo>).

Cores (SPEC.art_assets.effects.railgun.palette_map_addendum, tools/spec/bullet_strike_art2.json):
  claroes (boca, perfuracao, impacto, escudo)       nucleo core [205,228,255] -> borda glow [100,175,255]
  aneis EM, aneis do rastro, chiado, raios, arcos   glow [100,175,255], franja blue [45,115,255]
  particulas do rastro e faiscas                    core -> glow (branco-azuladas)
  anel de choque do tranco                          glow -> core
  luzes (blob light=True)                           palette.rail.hull [20,82,255] (regra do casco branco <= 0,5)
  UNICA cor quente                                  rail_embers [215,145,40] -> [120,45,10] (o alvo queimando)
Nada violeta ([150,105,255], [96,0,255], {0.38,0,1}), nada ouro-branco [255,225,150], nada cobre (selfcheck).

Arquivos gerados (shots/bs_rail_fx/), com orcamento de particulas (SPEC.art_assets.effects.railgun):
  rail_muzzle_flash / rail_muzzle_ring / rail_muzzle_light   boca (3 particulas; + o anel de choque)
  rail_shock_ring                                             TRANCO: anel de choque no espaco (shockwave.png vanilla)
  rail_trail_core / rail_trail_rings                          rastro que FICA no espaco (receita ion_trail do plasma)
  rail_puncture_flash / _sparks / _sizzle                     cada peca perfurada (5 + 1 vanilla = 6)
  rail_impact_light / _flash / _sparks / rail_embers          fim do caminho (com os raios e a fumaca: <= 45)
  rail_lightning                                              copia AZUL do missile_emp_lightning vanilla (4-6 raios)
  rail_emp_sizzle                                             copia AZUL do missile_emp_hit_sizzle vanilla (dreno final)
  rail_drain_sizzle                                           chiado azul do dreno por peca perfurada (1 particula)
  rail_shield_flash / rail_shield_ring                        acerto no escudo (+ missile_emp_hit_shockwave vanilla)
  rail_intercepted_flash / _sparks                            dardo abatido no ar (5)
  rail_charge_arcs                                            arcos de carga na coroa (copia AZUL do
                                                              disruptor_shoot_lightning, EmitPerSecond para o
                                                              ContinuousEffects dos ultimos 0,5 s da carga)
As copias de arquivos vanilla (rail_lightning, rail_emp_sizzle, rail_charge_arcs) sao INTEGRAIS (CONTRATOS R8):
tools/vanilla_fx/rail/*.rules lidos como estao e so recoloridos (rampas e cores do shader), com contagem trocada
e caminhos relativos -> ./Data/... (as copias moram em shots/bs_rail_fx/).

So importa rules_dsl e bsgen.fxkit / bsgen.fx_tex no nivel do modulo (nunca bs_data nem bsgen.railgun).
"""

import math
import os
import re

from rules_dsl import Q, VOID
from bsgen import fxkit as FXK
from bsgen import fx_tex as TEX

API = 2

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # tools/
VENDOR_DIR = os.path.join(HERE, "vanilla_fx", "rail")
DIR = "shots/bs_rail_fx"
D = "./Data"
SHOCKWAVE = FXK.SHOCKWAVE                                               # ./Data/common_effects/particles/shockwave.png
LIGHTNING_SHADER = f"{D}/shots/disruptor_bolt/particles/particle_lightning.shader"
DISCHARGE = f"{D}/shots/disruptor_bolt/particles/disruptor_bolt_discharge.png"

# cores proibidas em qualquer arquivo do rail (ADDENDUM WP09; selfcheck): violeta/ouro antigos
FORBIDDEN_RGB = ([150, 105, 255], [96, 0, 255], [255, 225, 150])
FORBIDDEN_FLOAT = ((0.38, 0.0, 1.0),)
WARM_FILES = ("rail_embers",)        # o unico arquivo com cor quente (o alvo queimando)


# ----------------------------------------------------------------------------- paleta
def pal():
    """palette.rail (blue, glow, core, hull, accent_orange_gold...) do spec de arte 2.0."""
    return FXK.pal("rail")


def f3(rgb):
    """[r, g, b] 0..255 -> (r, g, b) 0..1 com 4 casas."""
    return tuple(round(float(c) / 255.0, 4) for c in list(rgb)[:3])


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t, 4) for i in range(3))


def _k(c, k, a):
    """Chave de rampa (r, g, b, a) com o RGB multiplicado por k (HDR > 1 = centro mais branco)."""
    return tuple(round(v * k, 3) for v in c) + (round(a, 3),)


def colors():
    p = pal()
    core, glow, blue = f3(p["core"]), f3(p["glow"]), f3(p["blue"])
    hull = f3(p["hull"])
    hot = f3(p["accent_orange_gold"])
    return core, glow, blue, hull, hot


# ----------------------------------------------------------------------------- tijolos proprios
def _emitter_cont(pre, eps):
    """Emissor continuo (ContinuousEffects / MediaEffects de projetil): EmitPerSecond, sem disparo unico."""
    return {"EmitPerSecond": eps, "EmitPerOneShot": FXK.R(0, 0), "PreInitializers": pre, "PostInitializers": []}


def trail_core(note, eps, life, length, width, ramp, bucket="BulletTrailUpper"):
    """Rastro que FICA NO ESPACO atras do dardo (receita plasma_fx.ion_trail = bullet_trail_railgun.rules vanilla:
    LocationToWorldSpace + FpsCompensator sem InheritVelocity): riscos de blob alinhados ao voo que afinam e somem."""
    el, V, R = FXK.el, FXK.V, FXK.R
    pre = [el("SetValue", DataOut="location", ValueType="Vector2", Value=V(-FXK.r(length / 2 + 0.3), 0)),
           el("SetValue", DataOut="rot", ValueType="Angle", Value="0d"),
           el("SetValue", DataOut="base_color", ValueType="Color", Value=FXK.C(1, 1, 1, 1)),
           el("SetBulletBarrierID", BarrierIDOut="barrier")]
    init = [el("LocationToWorldSpace", LocationIn="location", LocationOut="location"),
            el("FpsCompensator", LocationInOut="location", VelocityIn=VOID, Mode="Uniform"),
            el("RotationToWorldSpace", RotationIn="rot", RotationOut="rot")]
    upd = [el("Lifetime", LifeInOut="life", Lifetime=FXK.r(life)),
           el("Lerp", True, LerpIn="life", DataOut="scale2", Invert=False, ValueType="Vector2",
              FromValue=V(1, 1), ToValue=V(0.85, 0.3)),
           FXK.ramp("color", ramp),
           FXK.mul("Color", "color", "base_color", "color"),
           el("Barrier", BarrierIDIn="barrier", LocationIn="location")]
    mat = {"Texture": FXK.tex(FXK.BLOB), "TargetBlendMode": dict(FXK.ADD)}
    return FXK.particles(note, init, upd, FXK.renderer(scale=VOID, scale2="scale2", base=(length, width)), mat,
                         _emitter_cont(pre, eps), bucket, True, "30", inflate=3)


def trail_rings(note, eps, life, size, scale, scale2, ramp, bucket="BulletTrailUpper"):
    """Aneis EM que ficam no caminho (bs_ring_thin tingido): nascem achatados perpendiculares ao voo e crescem."""
    el, V = FXK.el, FXK.V
    pre = [el("SetValue", DataOut="location", ValueType="Vector2", Value=V(0, 0)),
           el("SetValue", DataOut="rot", ValueType="Angle", Value="0d"),
           el("SetValue", DataOut="base_scale", ValueType="Float", Value=FXK.r(size)),
           el("SetBulletBarrierID", BarrierIDOut="barrier")]
    init = [el("LocationToWorldSpace", LocationIn="location", LocationOut="location"),
            el("FpsCompensator", LocationInOut="location", VelocityIn=VOID, Mode="Uniform"),
            el("RotationToWorldSpace", RotationIn="rot", RotationOut="rot"),
            el("ScaleToWorldSpace", ScaleIn="base_scale", ScaleOut="base_scale")]
    upd = [el("Lifetime", LifeInOut="life", Lifetime=FXK.r(life)),
           el("Lerp", True, LerpIn="life", DataOut="scale", Invert=False, ValueType="Float",
              FromValue=scale[0], ToValue=scale[1]),
           FXK.mul("Float", "scale", "base_scale", "scale"),
           el("Lerp", True, LerpIn="life", DataOut="scale2", Invert=False, ValueType="Vector2",
              FromValue=V(*scale2), ToValue=V(*scale2)),
           FXK.ramp("color", ramp),
           el("Barrier", BarrierIDIn="barrier", LocationIn="location")]
    mat = {"Texture": FXK.tex(TEX.ref("bs_ring_thin.png")), "TargetBlendMode": dict(FXK.ADD)}
    return FXK.particles(note, init, upd, FXK.renderer(scale2="scale2"), mat, _emitter_cont(pre, eps), bucket, True,
                         "30", inflate=3)


# ----------------------------------------------------------------------------- copias vanilla recoloridas
VENDORED = {
    # nome gerado: (arquivo em tools/vanilla_fx/rail, pasta vanilla de origem, contagem (Min, Max) | None,
    #               EmitPerSecond | None, nota)
    "rail_lightning": ("missile_emp_lightning.rules", "shots/missile_emp/particles", (4, 6), None,
                       "raios AZUIS do impacto e do dreno final (copia do missile_emp_lightning vanilla)"),
    "rail_emp_sizzle": ("missile_emp_hit_sizzle.rules", "shots/missile_emp/particles", None, None,
                        "chiado AZUL do dreno final (copia do missile_emp_hit_sizzle vanilla)"),
    "rail_charge_arcs": ("disruptor_shoot_lightning.rules", "ships/terran/disruptor/particles", (0, 0), 8,
                         "arcos AZUIS de carga na coroa da Ponta (copia do disruptor_shoot_lightning vanilla; "
                         "8/s x 0,3-0,4 s = ate ~3 vivos)"),
}
_NUM = r"-?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?"


def vendor_text(fname):
    """Texto vanilla sem o cabecalho // do vendor."""
    with open(os.path.join(VENDOR_DIR, fname), encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    i = 0
    while i < len(lines) and lines[i].startswith("//"):
        i += 1
    return "\n".join(lines[i:])


def _fmt(v):
    v = round(float(v), 6)
    return str(int(v)) if v == int(v) else f"{v:.6f}".rstrip("0").rstrip(".")


def _set_rgb(block, rgb):
    """Troca Rf/Gf/Bf (mantem Af) de um bloco { Rf .. Af }."""
    for ch, v in zip(("Rf", "Gf", "Bf"), rgb):
        block, n = re.subn(rf"(\t+{ch} = ){_NUM}", lambda m, v=v: m.group(1) + _fmt(v), block, count=1)
        if n != 1:
            raise ValueError(f"rail_fx: bloco de cor sem {ch}")
    return block


def recolor(text, src_dir, count=None, eps=None):
    """Copia vanilla INTEGRAL recolorida em azul: cores do shader (_centerColor -> core, _outerColor -> glow,
    _bloomColor -> blue), chaves de ColorRamp (brilho max(R,G,B) do vanilla x core -> glow ao longo da rampa, alfa
    igual), contagem (EmitPerOneShot Min/Max do EmitterDef) e EmitPerSecond trocados; File relativo -> ./Data/..."""
    core, glow, blue, _hull, _hot = colors()
    shader = {"_centerColor": core, "_outerColor": glow, "_bloomColor": blue}
    out = text
    for name, rgb in shader.items():
        def _sh(m, rgb=rgb):
            return m.group(1) + _set_rgb(m.group(2), rgb) + m.group(3)
        out, n = re.subn(rf"(\t+{name}\n\t+\{{\n)(.*?)(\n\t+\}})", _sh, out, flags=re.S)
        if n != 1:
            raise ValueError(f"rail_fx: {name} achado {n} vezes (esperado 1)")
    # rampas de cor: cada { Rf Gf Bf Af } dentro de 'Colors [ ... ]' de um ColorRamp

    def _ramp(m):
        body = m.group(2)
        keys = list(re.finditer(rf"\t+Rf = ({_NUM})\n\t+Gf = ({_NUM})\n\t+Bf = ({_NUM})\n", body))
        n = len(keys)
        if not n:
            raise ValueError("rail_fx: rampa sem chaves")
        parts, last = [], 0
        for i, k in enumerate(keys):
            r, g, b = (float(k.group(j)) for j in (1, 2, 3))
            bright = max(r, g, b)
            tgt = mix(core, glow, i / (n - 1) if n > 1 else 0)
            top = max(tgt)
            rgb = [bright * c / top for c in tgt]
            seg = body[k.start():k.end()]
            parts.append(body[last:k.start()])
            parts.append(_set_rgb(seg, rgb))
            last = k.end()
        parts.append(body[last:])
        return m.group(1) + "".join(parts) + m.group(3)
    out, nr = re.subn(r"(\t+Type = ColorRamp\n(?:.*?\n)*?\t+Colors\n\t+\[\n)(.*?)(\n\t+\])", _ramp, out, flags=re.S)
    if nr < 1:
        raise ValueError("rail_fx: nenhuma ColorRamp na copia vanilla")

    # sobras (ex.: SetValue color desligado do vanilla): toda cor quente/esverdeada que nao e branca vira core no
    # mesmo brilho, para nenhum numero fora da paleta ficar no arquivo
    def _left(m):
        r, g, b = (float(m.group(i)) for i in (2, 4, 6))
        if max(r, g, b) <= 0 or (b >= r and b >= g):
            return m.group(0)
        k = max(r, g, b)
        nr_, ng, nb = (k * c / max(core) for c in core)
        return f"{m.group(1)}{_fmt(nr_)}{m.group(3)}{_fmt(ng)}{m.group(5)}{_fmt(nb)}"
    out = re.sub(rf"(\t+Rf = )({_NUM})(\n\t+Gf = )({_NUM})(\n\t+Bf = )({_NUM})", _left, out)
    if count is not None:
        out, n = re.subn(rf"(EmitterDef\n\{{\n\tEmitPerSecond = {_NUM}\n\tEmitPerOneShot\n\t\{{\n\t\tMin = ){_NUM}"
                         rf"(\n\t\tMax = ){_NUM}", lambda m: f"{m.group(1)}{int(count[0])}{m.group(2)}{int(count[1])}",
                         out)
        if n != 1:
            raise ValueError("rail_fx: EmitPerOneShot do EmitterDef nao achado")
    if eps is not None:
        out, n = re.subn(rf"(EmitterDef\n\{{\n\tEmitPerSecond = ){_NUM}", lambda m: f"{m.group(1)}{_fmt(eps)}", out)
        if n != 1:
            raise ValueError("rail_fx: EmitPerSecond do EmitterDef nao achado")

    def _file(m):
        val = m.group(2)
        p = val.strip('"')
        if p.startswith("./Data/") or p.startswith("&"):
            return m.group(0)
        p = D + "/" + os.path.normpath(os.path.join(src_dir, p)).replace(os.sep, "/")
        return m.group(1) + f'"{p}"'
    out = re.sub(r"^(\t+File = )([^\n]+)$", _file, out, flags=re.M)
    return out


# ----------------------------------------------------------------------------- tabela dos efeitos
def specs():
    """{nome: (texto, nota)} de todos os arquivos de shots/bs_rail_fx/ (sem cabecalho)."""
    core, glow, blue, hull, hot = colors()
    ring_tex = TEX.ref("bs_ring_thin.png")
    flash_ramp = [_k(core, 1.6, 1), _k(core, 1.2, 0.85), _k(glow, 1.0, 0.4), _k(glow, 1.0, 0)]
    soft_ramp = [_k(glow, 1.3, 0.9), _k(glow, 1.0, 0.6), _k(blue, 1.0, 0.25), _k(blue, 1.0, 0)]
    ring_ramp = [_k(glow, 1.4, 0), _k(glow, 1.3, 0.95), _k(glow, 1.0, 0.55), _k(blue, 1.0, 0)]
    shock_ramp = [_k(glow, 1.4, 1), _k(mix(glow, core, 0.5), 1.2, 0.75), _k(core, 1.0, 0.35), _k(core, 1.0, 0)]
    light_ramp = [(1, 1, 1, 1), (1, 1, 1, 0.5), (1, 1, 1, 0)]
    # luz de casco (particle_light.shader): canal mais fraco x 24 x 1,1 x alfa <= 0,5 (fxkit.particle_light_white)
    light_col = hull + (0.22,)
    trail_ramp = [_k(core, 1.3, 1), _k(mix(core, glow, 0.5), 1.0, 0.55), _k(glow, 1.0, 0.2), _k(glow, 1.0, 0)]
    spark_cols = (core + (1,), glow + (1,))
    out = {}

    def put(name, text, note):
        out[name] = (text, note)
    # ---- boca (FireEffect da Ponta)
    put("rail_muzzle_flash", FXK.blob("Clarao branco-azulado da boca da Tupa", 6, 0.12, 0, (1, 1, 1, 1), flash_ramp,
                                      scale=(0.7, 1.1), bucket="Upper2"), "claro da boca: core -> glow")
    put("rail_muzzle_ring", FXK.textured_blob("Anel EM azul da boca da Tupa", ring_tex, 8, 0.35, (1, 1, 1, 1),
                                              ring_ramp, scale=(0.2, 1), bucket="Upper2"), "anel EM: glow")
    put("rail_muzzle_light", FXK.blob("Luz do disparo da Tupa no casco", 10, 0.2, 0, light_col, light_ramp,
                                      light=True, bucket="Upper2"), "luz: palette.rail.hull")
    # ---- TRANCO: anel de choque que fica no espaco (TriggeredEffects AnchorMediaEffects = false)
    put("rail_shock_ring", FXK.textured_blob("TRANCO da Tupa: anel de choque azul (shockwave.png vanilla)", SHOCKWAVE,
                                             6.5, 0.32, (1, 1, 1, 1), shock_ramp, scale=(round(1 / 6.5, 4), 1),
                                             bucket="Upper2"), "anel de choque: glow -> core, 1,0 -> 6,5 quadros")
    # ---- rastro
    put("rail_trail_core", trail_core("Rastro branco-azulado do dardo da Tupa (fica no espaco)", 40, 0.3, 8, 0.3,
                                      trail_ramp), "rastro: core -> glow, 40/s x 0,3 s")
    put("rail_trail_rings", trail_rings("Aneis EM azuis no caminho do dardo da Tupa", 10, 0.35, 1.0, (0.4, 1.6),
                                        (0.35, 1), ring_ramp), "aneis do rastro: glow, franja blue")
    # ---- cada peca perfurada (<= 6 com o vanilla bullet_penetrate_railgun)
    put("rail_puncture_flash", FXK.blob("Perfuracao da Tupa: clarao", 1.4, 0.08, 0, (1, 1, 1, 1), flash_ramp),
        "perfuracao: core -> glow")
    put("rail_puncture_sparks", FXK.streaks("Perfuracao da Tupa: faiscas branco-azuladas", (3, 3), (6, 12),
                                            (0.15, 0.3), (0.5, 0.8), 0, 0.2, -0.6, 0.6, spark_cols, "Upper2"),
        "faiscas: core -> glow")
    put("rail_puncture_sizzle", FXK.blob("Perfuracao da Tupa: chiado azul", 1.0, 0.25, 0, (1, 1, 1, 1), soft_ramp),
        "chiado: glow")
    # ---- dreno por peca perfurada (MediaEffectsOnDrain do ExplosiveResourceDrain)
    put("rail_drain_sizzle", FXK.blob("Dreno PEM da Tupa numa peca perfurada: chiado azul", 1.2, 0.3, 0, (1, 1, 1, 1),
                                      soft_ramp), "dreno por peca: glow")
    # ---- fim do caminho
    put("rail_impact_light", FXK.blob("Impacto da Tupa: luz no casco", 9, 0.25, 0, light_col, light_ramp,
                                      light=True), "luz: palette.rail.hull")
    put("rail_impact_flash", FXK.blob("Impacto da Tupa: clarao branco-azulado", 6, 0.15, 0, (1, 1, 1, 1), flash_ramp,
                                      scale=(0.8, 1.2)), "clarao: core -> glow")
    put("rail_impact_sparks", FXK.streaks("Impacto da Tupa: faiscas branco-azuladas", (10, 14), (8, 20), (0.25, 0.5),
                                          (0.6, 1.1), 0, 0.3, -0.8, 0.6, spark_cols, "Upper2"), "faiscas: core -> glow")
    put("rail_embers", FXK.embers("Impacto da Tupa: brasas do ALVO queimando (unica cor quente do rail)",
                                  n=(8, 12), speed=(2.5, 6), life=(1.2, 2.0),
                                  color_from=hot + (1,), color_to=f3([120, 45, 10]) + (1,)),
        "brasas: accent_orange_gold -> [120,45,10]")
    # ---- escudo
    put("rail_shield_flash", FXK.blob("Tupa no escudo: clarao branco-azulado", 5, 0.18, 0, (1, 1, 1, 1), flash_ramp),
        "escudo: core -> glow")
    put("rail_shield_ring", FXK.textured_blob("Tupa no escudo: anel azul", ring_tex, 6, 0.4, (1, 1, 1, 1), ring_ramp,
                                              scale=(0.3, 1)), "anel do escudo: glow")
    # ---- abatido no ar
    put("rail_intercepted_flash", FXK.blob("Dardo da Tupa abatido: estouro azul", 3, 0.2, 0, (1, 1, 1, 1), soft_ramp),
        "abatido: glow")
    put("rail_intercepted_sparks", FXK.streaks("Dardo da Tupa abatido: faiscas", (4, 4), (5, 10), (0.15, 0.3),
                                               (0.4, 0.7), 0, 0.2, -0.5, 0.5, spark_cols, "Upper2"),
        "faiscas: core -> glow")
    # ---- copias vanilla recoloridas
    for name, (fname, src_dir, count, eps, note) in VENDORED.items():
        put(name, recolor(vendor_text(fname), src_dir, count, eps), note)
    return out


# grupos de MediaEffects usados pelo bsgen.railgun (os vanilla incolores/azulados entram pelo chamador)
GROUPS = {
    "muzzle": ["rail_muzzle_flash", "rail_muzzle_ring", "rail_muzzle_light"],
    "shock": ["rail_shock_ring"],
    "trail": ["rail_trail_core", "rail_trail_rings"],
    "puncture": ["rail_puncture_flash", "rail_puncture_sparks", "rail_puncture_sizzle"],
    "drain_part": ["rail_drain_sizzle"],
    "impact": ["rail_impact_light", "rail_impact_flash", "rail_lightning", "rail_impact_sparks", "rail_embers"],
    "emp_burst": ["rail_emp_sizzle", "rail_lightning"],
    "shield_hit": ["rail_shield_flash", "rail_shield_ring"],
    "intercepted": ["rail_intercepted_flash", "rail_intercepted_sparks"],
    "charge_arcs": ["rail_charge_arcs"],
}
# orcamento de particulas por grupo (SPEC.art_assets.effects.railgun.*.budget_particles; o vanilla somado conta)
BUDGET = {"muzzle": 5, "puncture": 6, "impact": 45, "shield_hit": 4, "intercepted": 5}


def files(group):
    return list(GROUPS[group])


def media(group, frm="shot"):
    """['&<...>'] do grupo, visto de shots/<pasta>/x.rules (frm 'shot') ou de parts/<id>/x.rules ('part')."""
    return [FXK.ref_media(DIR, n, frm) for n in GROUPS[group]]


# ----------------------------------------------------------------------------- ganchos
def write(out, header):
    for name, (text, note) in sorted(specs().items()):
        head = "\n".join(f"// {ln}" for ln in (header + f"\nEfeito da Tupa (bsgen/rail_fx.py): {note}").split("\n"))
        out.text(f"{DIR}/{name}.rules", head + "\n\n" + text)


def _colors_in(text):
    """[(r, g, b)] 0..1 de todo bloco Rf/Gf/Bf e de todo VertexColor [r, g, b(, a)] 0..255 do texto."""
    found = []
    for m in re.finditer(rf"Rf = ({_NUM})\s+Gf = ({_NUM})\s+Bf = ({_NUM})", text):
        found.append(tuple(float(m.group(i)) for i in (1, 2, 3)))
    for m in re.finditer(rf"VertexColor = \[({_NUM}), ({_NUM}), ({_NUM})", text):
        found.append(tuple(float(m.group(i)) / 255.0 for i in (1, 2, 3)))
    return found


def color_problems(rel, text, warm_ok=False):
    """Cores fora da paleta do rail num arquivo: violeta/ouro-branco proibidos; quente (R > B) so em warm_ok."""
    probs = []
    for c in _colors_in(text):
        rgb255 = [round(v * 255) for v in c]
        for bad in FORBIDDEN_RGB:
            mx = max(c) or 1
            norm = [round(v / mx * 255) for v in c]
            if all(abs(a - b) <= 3 for a, b in zip(norm, bad)) and max(c) > 0:
                probs.append(f"{rel}: cor proibida {bad} (achado {rgb255})")
        for bad in FORBIDDEN_FLOAT:
            mx = max(c) or 1
            if all(abs(v / mx - b) <= 0.02 for v, b in zip(c, bad)):
                probs.append(f"{rel}: cor proibida {bad} (achado {tuple(round(v, 3) for v in c)})")
        r, g, b = c
        if max(c) > 0.02 and not warm_ok:
            if r > b + 0.02 * max(c):
                probs.append(f"{rel}: cor quente {tuple(round(v, 3) for v in c)} fora de rail_embers")
            elif r > g + 0.02 * max(c) and b > g:
                probs.append(f"{rel}: cor violeta {tuple(round(v, 3) for v in c)} (rail e AZUL)")
    return probs


def _count(text):
    """Max de particulas de um disparo (EmitPerOneShot Max do EmitterDef); 0 para emissor continuo."""
    m = re.search(rf"EmitterDef\n\{{\n\tEmitPerSecond = ({_NUM})\n\tEmitPerOneShot\n\t\{{\n\t\tMin = ({_NUM})\n\t\tMax = "
                  rf"({_NUM})", text)
    return int(float(m.group(3))) if m else 0


def selfcheck(mod_dir, spec=None):
    """Arquivos escritos, cores AZUIS (so rail_embers quente), luzes dentro da regra do casco branco e orcamento de
    particulas por grupo."""
    probs = []
    sp = specs()
    texts = {}
    for name in sp:
        p = os.path.join(mod_dir, DIR, f"{name}.rules")
        if not os.path.isfile(p):
            probs.append(f"{DIR}/{name}.rules nao foi escrito")
            continue
        with open(p, encoding="utf-8") as fh:
            texts[name] = fh.read()
        probs += color_problems(f"{DIR}/{name}.rules", texts[name], warm_ok=name in WARM_FILES)
    if "rail_embers" in texts and not any(c[0] > c[2] for c in _colors_in(texts["rail_embers"])):
        probs.append("rail_embers sem a cor quente do alvo queimando")
    # luzes particle_light: canal mais fraco no casco branco <= 0,5
    core, glow, blue, hull, hot = colors()
    for name in ("rail_muzzle_light", "rail_impact_light"):
        w = FXK.particle_light_white(hull + (0.22,), [(1, 1, 1, 1), (1, 1, 1, 0.5), (1, 1, 1, 0)])
        if w > 0.5 + 1e-9:
            probs.append(f"{name}: luz lava o casco branco ({w:.2f} > 0,5)")
    for grp, cap in BUDGET.items():
        n = sum(_count(texts.get(f, "")) for f in GROUPS[grp])
        extra = {"puncture": 1, "shield_hit": 1, "impact": 10, "muzzle": 1}.get(grp, 0)   # vanilla somado pelo railgun
        if n + extra > cap:
            probs.append(f"grupo {grp}: {n} + {extra} vanilla particulas > orcamento {cap}")
    return probs
