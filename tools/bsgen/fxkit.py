"""Kit de efeitos compartilhado do Bullet Strike: usado por bsgen/caliber_fx.py (granadas por calibre) e
bsgen/missile_fx.py (misseis). Modulo opcional (CONTRATOS secao 1): build_mod / shots / bs_data o carregam com
_opt("bsgen.fxkit"); ausente ou BS_FX_EXT=0 = nada muda. So importa rules_dsl (nada de bs_data, build_mod,
bsgen.shots, bsgen.trails ou bsgen.plasma_fx): nao entra em ciclo de import com quem o chama.

1. Tijolos de particula: COPIA (nao import) dos construtores genericos de bsgen/plasma_fx.py (_el, V, C, R, _r,
   _tex, _renderer, _tail, _particles, _emitter, _ramp, _addt, _mul, _local_init, _hot, flipbook, streaks, blob,
   ring + constantes), com as mesmas assinaturas e o mesmo texto de saida byte a byte (o teste do WP2 confere,
   trocando os construtores do plasma_fx pelos daqui e regerando todos os efeitos de plasma). plasma_fx.py nao e
   editado; juntar os dois e tarefa futura. Nomes publicos sem o "_" (el, tex, renderer, tail, particles, emitter,
   ramp, addt, mul, local_init, hot, r); os nomes com "_" continuam valendo. O TAIL_TEXT (rabo dos arquivos de
   particula, ja carregado no 0.30.4c) e copia de bsgen/trails.TAIL_TEXT, conferida pelo mesmo teste.
2. Visual nuclear comum da Boiuna (granada) e da Iara (missil), em shots/bs_nuke_fx/ (NUKE_DIR): anel verde que
   cresce (bs_nuke_ring; bs_nuke_ring_small quando o projetil e abatido no ar) e brilho residual verde no casco
   (bs_nuke_afterglow). Referencias com nuke_ref(nome, "shot" | "part") / nuke_media(...).
3. radiation_components(): o trevo de radiacao girando do missil nuclear vanilla
   (shots/missile_nuke/missile_nuke_stage1.rules l.72-116: RadiationSpriteSmall + RadiationSpriteBig), recolorido
   e com tamanho, giro, posicao e baldes por projetil.
4. art_sprite_components(): corpo iluminado com mapa de normais + atlas de luzes aditivo + faixa tingida, a partir
   de um item do meta.json da arte de projeteis (art3d/bs_missiles2, art3d/bs_shells2; CONTRATOS secao 3).
5. (2.0, WP03) light_pair(): a luz do projetil em DUAS sprites IsLight (SPEC.art_assets.phase_b_leftovers.
   islight_white_hull + ADDENDUM G7): halo grande SO NO ESPACO (GlowSprite, cor glow/4, _litReflectiveStrength 0) +
   luz de casco pequena (GlowSprite2, palette[municao].hull, refl 6; AC e slug 4) com a regra do canal mais fraco
   (c_min <= floor(0,5 x 255 / (0,85 x refl)): 25 a refl 6, 37 a refl 4) para o casco branco nunca virar mancha
   branca. Switch art.light_split (split | legacy = a luz unica da Fase B). Ajudantes: palette(), hull_refl(),
   c_min_limit(), start_time() (StartTime das luzes, para o clarao do disparo nao lavar a propria torre).
6. (2.0, WP03) embers(): brasas que saem em leque, freiam e apagam (receita das gotas de brasa do missile_fx,
   generalizada: cor, quantidade, vida); AC (ac_embers) e o rail_fx (rail_embers) usam o mesmo tijolo.
7. (2.0, WP03) missile_art_dir() / missile_art_meta(): pasta da arte dos misseis = art3d/bs_missiles2 (ou env
   BS_MISSILE_ART_DIR); a reserva da arte 1.x fica so dentro do bloco LEGACY_1X_FALLBACK (apagado pelo WP14b).
8. (2.0, WP03) art_switch(nome): valor do switch art.<nome> (bs_data.switch quando o bs_data esta carregado; senao
   env BS_ART_<NOME> ou o padrao do spec).

Campos e tipos: so os do conjunto provado no 0.30.4c (CONTRATOS R9: TAIL_TEXT, regras ja geradas pelo mod e o
corpus do SW:ACD, que mira o 0.30.4). Inteiros onde o jogo so usa inteiros (VertexColor, FrameCount, FrameSize,
FramesPerRow, FramesPerSecond): valor fracionario estoura aqui, no build, e nao no carregamento do jogo.
"""

import json
import math
import os
import sys

from rules_dsl import Q, VOID, render, fmt_num

# registro de modulos do build_mod (WP01): so participa com API >= 2 (gancho write: arquivos de shots/bs_nuke_fx)
API = 2

# ----------------------------------------------------------------------------- constantes (copia de plasma_fx)
D = "./Data"
MAXZ = "3.4028235E+38"
BLOB = f"{D}/common_effects/particles/blob.png"
SPARK = f"{D}/common_effects/particles/spark.png"
# SHOCK = anel fino do plasma (bsgen/plasma_tex.shock_ring), caminho RELATIVO: so resolve dentro de
# shots/bs_plasma_fx/. Fica aqui para o texto sair igual ao do plasma_fx; fora daquela pasta use SHOCKWAVE.
SHOCK = "bs_plasma_shock.png"
RING = f"{D}/ships/terran/railgun_launcher/particles/railgun_shoot.png"
LIGHT_SHADER = f"{D}/common_effects/particles/particle_light.shader"

# misturas vistas no jogo base
ADD = {"SourceRgbFactor": "SourceAlpha", "DestRgbFactor": "One", "RgbOperator": "Add",
       "SourceAlphaFactor": "InverseDestAlpha", "DestAlphaFactor": "One", "AlphaOperator": "Add"}
ADD_SPARK = {"SourceRgbFactor": "SourceAlpha", "DestRgbFactor": "One", "RgbOperator": "Add",
             "SourceAlphaFactor": "Zero", "DestAlphaFactor": "One", "AlphaOperator": "Add"}
SCREEN = {"SourceRgbFactor": "InverseDestColor", "DestRgbFactor": "One", "RgbOperator": "Add",
          "SourceAlphaFactor": "Zero", "DestAlphaFactor": "One", "AlphaOperator": "Add"}
PURE_ADD = {"SourceRgbFactor": "One", "DestRgbFactor": "One", "RgbOperator": "Add",
            "SourceAlphaFactor": "InverseDestAlpha", "DestAlphaFactor": "One", "AlphaOperator": "Add"}

# curva "ease-out" de 11 pontos (mesma forma das curvas de 256/1024 pontos dos flashes vanilla)
EASE = [0, 0.33, 0.51, 0.64, 0.745, 0.835, 0.905, 0.95, 0.98, 0.995, 1]

# rabo dos arquivos de particula (depois do Bucket): COPIA de bsgen/trails.TAIL_TEXT (texto vanilla ja carregado
# no 0.30.4c; o teste do WP2 confere que e igual)
TAIL_TEXT = """UseRealTime = false
PenetratingBucket
MinIntensity = 0
IsFancy = true
IsFancyLight = false
IsSimple = false
Sharing = Global
UnsharedRenderInWorldSpace = false
DontEmitWhenOffScreen = true
DontEmitWhenOffScreenSizeInflate = 1
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
IgnoreIntensity = false"""


# ----------------------------------------------------------------------------- tijolos de sintaxe
def _el(type_, upd=False, **fields):
    d = {"Type": type_}
    d.update(fields)
    d["Name"] = Q("")
    d["Enabled"] = True
    d["UpdateAfterInit"] = upd
    return d


def V(x, y):
    return {"X": x, "Y": y}


def C(r, g, b, a=1):
    return {"Rf": r, "Gf": g, "Bf": b, "Af": a}


def R(a, b):
    return {"Min": a, "Max": b}


def _r(v, n=4):
    return round(float(v), n)


def _tex(path, wrap=False, fix=False):
    t = {"File": Q(path), "MipLevels": "max"}
    if fix:
        t["FixTransparentColors"] = True
    t["SampleMode"] = "Linear"
    if wrap:
        t["UMode"] = "Wrap"
        t["VMode"] = "Wrap"
    return t


def _renderer(kind="StandardQuadRenderer", scale="scale", scale2=VOID, rot="rot", color="color", uv=VOID,
              base=(1, 1), offset=(0, 0)):
    return {"Type": kind, "LocationIn": "location", "ScaleIn": scale, "Scale2In": scale2, "RotationIn": rot,
            "ColorIn": color, "UvRectIn": uv, "BaseSize": V(*base), "Offset": V(*offset), "Name": Q("")}


def _tail(bucket, fancy, zoom, inflate=1, delay=0):
    t = TAIL_TEXT
    for a, b in (("IsFancy = true", f"IsFancy = {'true' if fancy else 'false'}"),
                 ("MaxEmissionZoom = 30", f"MaxEmissionZoom = {zoom}"),
                 ("DontEmitWhenOffScreenSizeInflate = 1", f"DontEmitWhenOffScreenSizeInflate = {inflate}"),
                 ("Delay = 0\n", f"Delay = {_r(delay) if delay else 0}\n")):
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    return f"Bucket = {bucket}\n" + t + "\n"


def _particles(note, init, upd, renderer, material, emitter, bucket, fancy, zoom, inflate=1, capacity=256, delay=0):
    """InitCapacity 256 como em todos os efeitos de particula vanilla (Sharing = Global: um sistema por efeito para
    todas as armas; com muitas Boitatas a 10 tiros/s, 64 obrigava o jogo a realocar no meio da batalha)."""
    top = {"Type": "Particles",
           "Def": {"EmitPerSecond": 0, "EmitPerOneShot": 0, "Initializers": init, "Updaters": upd,
                   "Renderer": renderer, "Material": material, "DeleteMode": "Fast",
                   "EnableMultithreading": False, "InitCapacity": capacity},
           "EmitterDef": emitter}
    return render(top, note) + _tail(bucket, fancy, zoom, inflate, delay)


def _emitter(pre, n=(1, 1), eps=0):
    return {"EmitPerSecond": eps, "EmitPerOneShot": R(int(n[0]), int(n[1])), "PreInitializers": pre,
            "PostInitializers": []}


def _ramp(out, colors, lerp_in="life", upd=True):
    return _el("ColorRamp", upd, LerpIn=lerp_in, ColorOut=out, Invert=False, Colors=[C(*c) for c in colors])


def _addt(a="location", b="velocity"):
    return _el("Operator", DataType="Vector2", AIn=a, BIn=b, ResultOut=a, Operator="AddDt")


def _mul(dtype, a, b, out, upd=True):
    return _el("Operator", upd, DataType=dtype, AIn=a, BIn=b, ResultOut=out, Operator="Multiply")


def _local_init(scale_in="base_scale"):
    """Initializers de efeito local (boca/impacto): mundo + movimento da nave (AddFrameOfReference)."""
    return [_el("LocationToWorldSpace", LocationIn="location", LocationOut="location"),
            _el("RotationToWorldSpace", RotationIn="rot", RotationOut="rot"),
            _el("AddFrameOfReference", VelocityInOut="velocity"),
            _el("ScaleToWorldSpace", ScaleIn=scale_in, ScaleOut=scale_in)]


def _hot(c, k):
    """Cor da rampa multiplicada (HDR > 1 deixa o centro mais branco/quente)."""
    return tuple(_r(v * k, 3) for v in c[:3]) + (c[3],)

# ----------------------------------------------------------------------------- efeitos
def flipbook(note, tex, size, life, loc_x, scale=(0.9, 1.1), rot=(0, 0), scale2=None, ramp=None, frames=8,
             per_row=4, fpx=128, bucket="Upper2", fancy=False, zoom=MAXZ):
    """Uma particula com animacao de quadros (laser_blaster_small_shoot.rules): a animacao inteira cabe na vida
    (Framerate = numero de quadros, porque TimeIn = life vai de 0 a 1)."""
    rows = -(-frames // per_row)
    ramp = ramp or [(1, 1, 1, 1), (1, 1, 1, 1)]
    pre = [_el("SetValue", DataOut="location", ValueType="Vector2", Value=V(_r(loc_x), 0)),
           _el("SetRandom", DataOut="rot", ValueType="Angle", FromValue=f"{rot[0]}d", ToValue=f"{rot[1]}d"),
           _el("SetValue", DataOut="base_scale", ValueType="Float", Value=_r(size))]
    upd = [_el("Lifetime", LifeInOut="life", Lifetime=_r(life)),
           _addt(),
           _el("UvAnimation", True, TimeIn="life", UvRectOut="uv_rect", Framerate=frames,
               TextureSize=V(fpx * per_row, fpx * rows), FrameSize=V(fpx, fpx), FrameCount=frames,
               FramesPerRow=per_row, PixelOffset=V(0, 0), Looping=False),
           _el("Lerp", True, LerpIn="life", DataOut="scale", Invert=False, ValueType="Float",
               FromValue=scale[0], ToValue=scale[1]),
           _mul("Float", "scale", "base_scale", "scale"),
           _ramp("color", ramp)]
    s2 = VOID
    if scale2:
        upd.append(_el("Lerp", True, LerpIn="life", DataOut="scale2", Invert=False, ValueType="Vector2",
                       FromValue=V(*scale2[0]), ToValue=V(*scale2[1])))
        s2 = "scale2"
    mat = {"Texture": _tex(tex), "TargetBlendMode": dict(ADD)}
    return _particles(note, _local_init(), upd, _renderer(scale2=s2, uv="uv_rect"), mat, _emitter(pre),
                      bucket, fancy, zoom, inflate=3)


def streaks(note, n, speed, life, scale, loc_x, spread, away_x, white, base_colors, bucket, zoom="30",
            stretch=(3.2, 0.55)):
    """Riscos de faisca (laser_bolt_sparks_def.rules) saindo num cone: nascem numa faixa de +-spread em Y e
    correm para longe de (away_x, 0), como o bullet_railgun_sparks.rules."""
    pre = [_el("SetRandom", DataOut="location", ValueType="Vector2", FromValue=V(_r(loc_x), -_r(spread)),
               ToValue=V(_r(loc_x), _r(spread))),
           _el("SetRandomVelocityFromPoint", LocationIn="location", VelocityOut="base_velocity",
               Speed=R(speed[0], speed[1]), AwayFromPoint=V(_r(away_x), 0)),
           _el("SetRandom", DataOut="base_color", ValueType="Color", FromValue=C(*base_colors[0]),
               ToValue=C(*base_colors[1])),
           _el("SetRandom", DataOut="base_scale", ValueType="Float", FromValue=scale[0], ToValue=scale[1]),
           _el("SetRandom", DataOut="lifetime", ValueType="Float", FromValue=life[0], ToValue=life[1])]
    init = [_el("LocationToWorldSpace", LocationIn="location", LocationOut="location"),
            _el("VelocityToWorldSpace", VelocityIn="base_velocity", VelocityOut="base_velocity"),
            _el("AddFrameOfReference", VelocityInOut="inherited_velocity"),
            _el("AlignToVelocity", VelocityIn="base_velocity", RotationInOut="rot"),
            _el("ScaleToWorldSpace", ScaleIn="base_scale", ScaleOut="base_scale")]
    w = 1 + white
    upd = [_el("VariableLifetime", LifeInOut="life", LifetimeIn="lifetime"),
           _el("Lerp", True, LerpIn="life", DataOut="velocity", Invert=False, ValueType="Vector2",
               FromValue=V(1, 1), ToValue=V(0.15, 0.15)),
           _mul("Vector2", "velocity", "base_velocity", "velocity", upd=False),
           _addt("location", "velocity"),
           _addt("location", "inherited_velocity"),
           _el("ValueCurve", True, MinValue=0, MaxValue=1, LerpIn="life", CurveOut="curve", Invert=False,
               Points=list(EASE)),
           _el("Lerp", True, LerpIn="curve", DataOut="scale2", Invert=False, ValueType="Vector2",
               FromValue=V(*stretch), ToValue=V(0.2, 0.05)),
           _ramp("color", [(w, w, w, 1), (0.6, 1, 1, 0.85), (0.05, 0.7, 1, 0)], lerp_in="curve"),
           _mul("Color", "color", "base_color", "color"),
           _el("ScalarOperator", AIn="base_scale", DataType="Vector2", BIn="scale2", ResultOut="scale2",
               Operator="Multiply")]
    mat = {"Texture": _tex(SPARK), "TargetBlendMode": dict(ADD_SPARK)}
    return _particles(note, init, upd, _renderer(scale=VOID, scale2="scale2", base=(0.75, 0.75)), mat,
                      _emitter(pre, n), bucket, True, zoom, inflate=3)


def blob(note, size, life, loc_x, color, ramp, scale=(1, 1), wh=None, light=False, bucket="Upper2",
         fancy=False, zoom=MAXZ, tex=BLOB, unlit=0.1, n=(1, 1)):
    """Clarao/brilho de 1 particula (laser_bolt_small_flash.rules). light=True: LightQuadRenderer com
    particle_light.shader (ilumina o casco, quase nada sobre o espaco); senao aditivo comum (visivel no espaco).
    n = numero de particulas por disparo (EmitPerOneShot {Min  Max}); so faixas vistas no vanilla."""
    pre = [_el("SetValue", DataOut="location", ValueType="Vector2", Value=V(_r(loc_x), 0)),
           _el("SetValue", DataOut="base_color", ValueType="Color", Value=C(*color)),
           _el("SetValue", DataOut="base_scale", ValueType="Float", Value=_r(size))]
    upd = [_el("Lifetime", LifeInOut="life", Lifetime=_r(life)),
           _addt(),
           _ramp("color", ramp),
           _mul("Color", "color", "base_color", "color"),
           _el("Lerp", True, LerpIn="life", DataOut="scale", Invert=False, ValueType="Float",
               FromValue=scale[0], ToValue=scale[1]),
           _mul("Float", "scale", "base_scale", "scale")]
    s2 = VOID
    if wh:
        upd.append(_el("Lerp", True, LerpIn="life", DataOut="scale2", Invert=False, ValueType="Vector2",
                       FromValue=V(*wh[0]), ToValue=V(*wh[1])))
        s2 = "scale2"
    if light:
        mat = {"Shader": {"File": Q(LIGHT_SHADER)}, "_z": 0.1, "_litReflectiveStrength": 24,
               "_litAdditiveStrength": 0.05, "_unlitAdditiveStrength": unlit,
               "Texture": _tex(tex), "TargetBlendMode": dict(SCREEN)}
        rend = _renderer("LightQuadRenderer", scale2=s2)
    else:
        mat = {"Texture": _tex(tex), "TargetBlendMode": dict(ADD)}
        rend = _renderer(scale2=s2)
    return _particles(note, _local_init(), upd, rend, mat, _emitter(pre, n), bucket, fancy, zoom, inflate=3)


RING_RAMP = [(1, 1, 1, 0), (0.6, 1, 1, 0.9), (0.8, 1, 1, 0.3), (0.4, 1, 1, 0)]
# pulso da Boitata (9 chaves igualmente espacadas: 0; 0,125; 0,25 ...): pico em 25% da vida, ~0 em 62,5%, 0 em 75%
RING_PULSE = [(1, 1, 1, 0), (0.7, 1, 1, 0.6), (0.6, 1, 1, 0.95), (0.7, 1, 1, 0.55), (0.8, 1, 1, 0.22),
              (0.6, 1, 1, 0.04), (0.4, 1, 1, 0), (0.4, 1, 1, 0), (0.4, 1, 1, 0)]


def ring_ramp(gain=1.0, pulse=False, alpha=1.0):
    """Rampa de cor do anel: RGB (menos a ultima chave) multiplicado por gain (HDR no overclock) e alfa por
    alpha (pico menor no normal da Boitata)."""
    keys = RING_PULSE if pulse else RING_RAMP
    out = []
    for i, (r, g, b, a) in enumerate(keys):
        k = gain if (a > 0 and i < len(keys) - 1) else 1.0
        out.append((_r(r * k, 3), _r(g * k, 3), _r(b * k, 3), _r(a * alpha, 3)))
    return out


def ring(note, local_scale, life, loc_x, gain=1.0, bucket="Upper1", fancy=False, zoom=MAXZ, pulse=False,
         alpha=1.0):
    """Aneis de choque ciano para frente (railgun_shoot.rules: 16 quadros de 256 px), menores e mais curtos.
    pulse=True (Boitata): rampa que acende e apaga dentro de ~3/4 da vida, para o anel nunca durar ate o tiro
    seguinte."""
    pre = [_el("SetValue", DataOut="location", ValueType="Vector2", Value=V(_r(loc_x), 0))]
    init = [_el("LocationToWorldSpace", LocationIn="location", LocationOut="location"),
            _el("RotationToWorldSpace", RotationIn="rot", RotationOut="rot"),
            _el("AddFrameOfReference", VelocityInOut="velocity"),
            _el("SetWorldSpaceScale", ScaleOut="scale", LocalScale=_r(local_scale))]
    upd = [_el("Lifetime", LifeInOut="life", Lifetime=_r(life)),
           _addt(),
           _el("UvAnimation", True, TimeIn="life", UvRectOut="uv_rect", Framerate=16, TextureSize=V(1024, 1024),
               FrameSize=V(256, 256), FrameCount=16, FramesPerRow=4, PixelOffset=V(0, 0), Looping=False),
           _ramp("color", ring_ramp(gain, pulse, alpha)),
           _el("Lerp", True, LerpIn="life", DataOut="scale2", Invert=False, ValueType="Vector2",
               FromValue=V(2, 1), ToValue=V(1, 1))]
    mat = {"Texture": _tex(RING), "TargetBlendMode": dict(ADD)}
    return _particles(note, init, upd, _renderer(scale2="scale2", uv="uv_rect", base=(1.5, 1.5)), mat,
                      _emitter(pre), bucket, fancy, zoom, inflate=3)


# ----------------------------------------------------------------------------- nomes publicos (sem "_")
el = _el
r = _r
tex = _tex
renderer = _renderer
tail = _tail
particles = _particles
emitter = _emitter
ramp = _ramp
addt = _addt
mul = _mul
local_init = _local_init
hot = _hot


# ----------------------------------------------------------------------------- referencias
def ref(dir_rel, name, frm):
    """Caminho (sem &<>) do arquivo gerado <dir_rel>/<name>.rules visto de outro arquivo gerado.
      frm "shot": de shots/<id>/<id>.rules  -> "../<pasta>/<name>.rules" (dir_rel tem de ser shots/<pasta>);
      frm "part": de parts/<id>/<id>.rules  -> "../../<dir_rel>/<name>.rules".
    Caminho puro serve para as listas FX[...]["particles"] (guns.fire_media poe o &<>); para MediaEffects de
    projetil use ref_media()."""
    d = dir_rel.strip("/")
    if name.endswith(".rules"):
        name = name[:-len(".rules")]
    if frm == "shot":
        parts = d.split("/")
        if len(parts) != 2 or parts[0] != "shots":
            raise ValueError(f"ref(frm='shot') pede uma pasta shots/<pasta>, veio {dir_rel!r}")
        return f"../{parts[1]}/{name}.rules"
    if frm == "part":
        return f"../../{d}/{name}.rules"
    raise ValueError(f"frm deve ser 'shot' ou 'part', veio {frm!r}")


def ref_media(dir_rel, name, frm):
    """Elemento de lista MediaEffects: &<ref(...)>."""
    return f"&<{ref(dir_rel, name, frm)}>"


# ----------------------------------------------------------------------------- visual nuclear comum
# Boiuna (granada nuclear, caliber_fx) e Iara (missil nuclear, missile_fx) usam OS MESMOS arquivos.
NUKE_DIR = "shots/bs_nuke_fx"
NUKE_GREEN_LIGHT = [90, 255, 60]     # VertexColor da luz de radiacao IsLight da Iara (missiles_design 2, Iara)
NUKE_GREEN_TINT = [120, 255, 60]     # VertexColor dos trevos aditivos da Boiuna (caliber_design item 13)
# Verde de UM canal so para a luz IsLight grande do trevo (RadiationLight), o mesmo idioma do vermelho puro
# [255, 0, 0] do vanilla (missile_nuke_stage1.rules l.99). A luz de casco multiplica a cor pela forca do shader
# (fancy_light: _litReflectiveStrength 10) e pelo difuso do casco (base.shader multiplyAdditiveLightValue): com
# NUKE_GREEN_LIGHT / NUKE_GREEN_TINT o R e o B da lamina do trevo tambem estouram e o trevo sai BRANCO sobre casco
# branco, cinza ou escuro (conta em SCR/vfx_impl/WP2/light_model.py); com R = B = 0 so o verde satura.
NUKE_GREEN_HULL = [0, 255, 0]
NUKE_RING_COLOR = (0.45, 1, 0.25)    # cor float do anel (caliber_design 1.B: [.45, 1, .25])
SHOCKWAVE = f"{D}/common_effects/particles/shockwave.png"
RADIATION = f"{D}/shots/missile_nuke/radiation.png"
RADIATION_SMALL = f"{D}/shots/missile_nuke/radiation_small.png"
FANCY_LIGHT = f"{D}/common_effects/fancy_light.shader"

# Anel: shockwave.png vanilla (o mesmo do explosive_charge_shockwave.rules, que cresce 3 -> 8 com Lerp linear).
# A borda clara da textura fica a ~0,85 do raio do quadro (miolo quase transparente, alfa sobe ate a borda e cai a
# zero em ~0,92): quadro de 18 tiles = borda a ~7,7 tiles, o raio da explosao (Boiuna 8, Iara 9). Crescimento
# LINEAR (Lerp na vida, como o vanilla) de 2 a 18 tiles em 0,8 s = acompanha a frente de dano da Iara
# (ExplosiveDamage ExpandStartRadius 2 / ExpandDuration 0,8, tambem linear). O tamanho passa por
# ScaleToWorldSpace: o MediaEffectsScale do bloco de impacto multiplica o anel (Boiuna 1,15 = borda a ~8,8 tiles;
# Iara 1,3 = ~10 tiles, a mesma folga sobre o raio 9).
# Brilho residual: luz particle_light (LightQuadRenderer) de 14 tiles que acende em ~0,6 s e apaga em 3 s: o casco
# em volta do impacto fica verde depois que o clarao vanilla (missile_nuke_flash_light, 0,5 s) some.
# Intensidade (licao do plasma, X3: luz forte sobre casco branco vira nevoa clara): particle_light.shader devolve
# 24 * cor * (difuso do casco + 0,25) * alfa e o SCREEN soma isso por cima do casco ja desenhado. Com a cor
# [90, 255, 60] e alfa 0,6 o R e o B tambem estouram: o centro sai BRANCO puro ate ~1,8 s em casco branco, cinza
# ou escuro. Verde quase puro (0,12; 1; 0,08) com alfa 0,1 deixa so o verde saturar: le verde nos tres cascos de
# 0 a 1,8 s e some palido no fim (light_model.py do WP2 refaz a conta; no casco branco o maximo possivel e um
# verde-menta, a folga do SCREEN sobre branco e so ~0,15).
NUKE = {
    "bs_nuke_ring": {"size": 18, "start": 2, "life": 0.8, "bucket": "Upper2",
                     "ramp": [(1.4, 1.4, 1.4, 1), (1.1, 1.1, 1.1, 0.95), (1, 1, 1, 0.7), (1, 1, 1, 0)],
                     "note": "Anel verde da explosao nuclear (Boiuna e Iara): shockwave.png vanilla, 2 -> 18 tiles "
                             "em 0,8 s"},
    "bs_nuke_ring_small": {"size": 6, "start": 2, "life": 0.5, "bucket": "Upper2",
                           "ramp": [(1.3, 1.3, 1.3, 1), (1, 1, 1, 0.8), (1, 1, 1, 0.45), (1, 1, 1, 0)],
                           "note": "Anel verde pequeno do nuclear abatido no ar (Boiuna e Iara): 2 -> 6 tiles em "
                                   "0,5 s"},
    "bs_nuke_afterglow": {"size": 14, "life": 3, "bucket": "Upper5", "color": (0.12, 1, 0.08, 0.1),
                          "ramp": [(1, 1, 1, 0.35), (1, 1, 1, 1), (1, 1, 1, 0.65), (1, 1, 1, 0.38),
                                   (1, 1, 1, 0.16), (1, 1, 1, 0)],
                          "scale": (0.85, 1.1),
                          "note": "Brilho residual verde no casco depois da explosao nuclear (Boiuna e Iara; "
                                  "particle_light, 14 tiles, 3 s)"},
}
NUKE_FILES = tuple(NUKE)


def _nuke_text(name):
    c = NUKE[name]
    if name == "bs_nuke_afterglow":
        return blob(c["note"], c["size"], c["life"], 0, c["color"], c["ramp"], scale=c["scale"], light=True,
                    bucket=c["bucket"])
    return blob(c["note"], c["size"], c["life"], 0, NUKE_RING_COLOR + (1,), c["ramp"],
                scale=(_r(c["start"] / c["size"]), 1), tex=SHOCKWAVE, bucket=c["bucket"])


def all_files():
    """{nome sem extensao: texto do .rules} dos arquivos de NUKE_DIR."""
    return {name: _nuke_text(name) for name in NUKE}


def nuke_ref(name, frm):
    """Caminho (sem &<>) de um arquivo de NUKE_DIR; frm = "shot" | "part" (ver ref)."""
    if name.endswith(".rules"):
        name = name[:-len(".rules")]
    if name not in NUKE:
        raise KeyError(f"arquivo nuclear desconhecido: {name!r} (ha: {', '.join(NUKE_FILES)})")
    return ref(NUKE_DIR, name, frm)


def nuke_media(name, frm):
    """Elemento de lista MediaEffects: &<nuke_ref(...)>."""
    return f"&<{nuke_ref(name, frm)}>"


def write(out, header):
    """Grava os arquivos de NUKE_DIR (sempre, inclusive com --no-art: so texto). Cabecalho no estilo de
    plasma_fx.write. Sem copy_art: o kit nao tem arte propria (texturas vanilla em ./Data)."""
    for name, txt in all_files().items():
        out.text(f"{NUKE_DIR}/{name}.rules", "\n".join(f"// {ln}" for ln in header.split("\n")) + "\n" + txt)


# ----------------------------------------------------------------------------- conversores com checagem de tipo
def _int(v, what):
    """Inteiro para campos que o jogo so usa inteiros (fracionario estoura no build, nao no jogo)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or float(v) != int(v):
        raise ValueError(f"{what}: precisa ser inteiro, veio {v!r}")
    return int(v)


def _color(c, what="VertexColor"):
    """VertexColor [R, G, B] ou [R, G, B, A] inteiros 0-255 (como no vanilla e no SW:ACD)."""
    c = list(c)
    if len(c) not in (3, 4):
        raise ValueError(f"{what}: 3 ou 4 valores, veio {c!r}")
    out = [_int(v, what) for v in c]
    if any(v < 0 or v > 255 for v in out):
        raise ValueError(f"{what}: valores 0-255, veio {c!r}")
    return out


def _deg(v):
    """Angulo no formato do jogo ("120d")."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"angulo numerico, veio {v!r}")
    return f"{fmt_num(float(v))}d"


def _vec(v, what):
    """Offset [x, y] (numero = [x, 0])."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return [_r(v), 0]
    v = list(v)
    if len(v) != 2:
        raise ValueError(f"{what}: numero ou [x, y], veio {v!r}")
    return [_r(v[0]), _r(v[1])]


def _wh(v, what):
    v = list(v)
    if len(v) != 2 or any(isinstance(x, bool) or not isinstance(x, (int, float)) or x <= 0 for x in v):
        raise ValueError(f"{what}: [comprimento, largura] positivos, veio {v!r}")
    return [_r(v[0]), _r(v[1])]


# ----------------------------------------------------------------------------- trevo de radiacao
# Campos do vanilla shots/missile_nuke/missile_nuke_stage1.rules (0.30.x; o SW:ACD, que mira o 0.30.4, tem a mesma
# copia em shots/missiles/*/missile_nuke/missile_nuke_stage1.rules l.72-116):
#   RadiationSpriteSmall (l.72-89): Type Sprite, RenderBucket BulletUpper1, Spin 360d, Sprite { Texture
#     radiation_small.png (MipLevels max, SampleMode Linear), Size [1, 1], VertexColor, TargetBlendMode Add }
#   RadiationSpriteBig (l.91-116): Type Sprite, RenderBucket BulletUpper2, Spin 360d, Z .25, IsLight true, Sprite {
#     Texture radiation.png, Size [9, 9], VertexColor, TargetBlendMode Add, Shader fancy_light.shader, _z 1,
#     _nrmlStrengthLimit 1, _litReflectiveStrength 10, _litAdditiveStrength 0.25, _unlitAdditiveStrength .4 }
# Mudam so: tamanho, giro, cor, posicao (Offset, campo de Sprite que o mod ja usa no GlowSprite) e baldes. O trevo
# pequeno vai em BulletUpper4 por padrao (o vanilla usa BulletUpper1 porque o corpo dele nao tem balde; o nosso
# corpo fica em BulletUpper3 e cobriria o trevo).
RADIATION_LIGHT = {"_z": 1, "_nrmlStrengthLimit": 1, "_litReflectiveStrength": 10, "_litAdditiveStrength": 0.25,
                   "_unlitAdditiveStrength": 0.4}


def radiation_components(big_size, big_spin_deg, small_size, small_spin_deg, small_offset, color,
                         big_bucket="BulletUpper2", small_bucket="BulletUpper4", big_offset=0, small_color=None,
                         big_z=0.25, light=None):
    """{"RadiationLight": luz IsLight girando (radiation.png, fancy_light: um trevo de luz verde varrendo o casco
    embaixo), "RadiationSpin": trevo pequeno aditivo girando sobre o projetil (radiation_small.png)}.
      big_size / small_size: lado em tiles; *_spin_deg: graus por segundo (vanilla 360);
      small_offset / big_offset: numero (x) ou [x, y], em tiles a partir do centro do projetil (ancora "radiation"
        / "warhead" do meta da arte); color: VertexColor dos dois (small_color troca so o do trevo pequeno);
      big_z: Z da luz (vanilla .25); light: troca parametros do shader (padrao RADIATION_LIGHT, os do vanilla).
    Iara: radiation_components(7, 120, 0.7, <giro>, <ancora>, NUKE_GREEN_LIGHT, ...);
    Boiuna: radiation_components(8, 180, 0.75, 360, <ancora>, NUKE_GREEN_TINT).
    Para a luz grande ler VERDE sobre casco (e nao branca) passe color=NUKE_GREEN_HULL e a cor de desenho no trevo
    pequeno: radiation_components(..., NUKE_GREEN_HULL, small_color=NUKE_GREEN_LIGHT | NUKE_GREEN_TINT)."""
    big = {"Type": "Sprite", "RenderBucket": big_bucket, "Spin": _deg(big_spin_deg), "Z": _r(big_z),
           "IsLight": True}
    bo = _vec(big_offset, "big_offset")
    if bo != [0, 0]:
        big["Offset"] = bo
    params = dict(RADIATION_LIGHT)
    params.update(light or {})
    big["Sprite"] = {"Texture": {"File": Q(RADIATION), "MipLevels": "max", "SampleMode": "Linear"},
                     "Size": _wh((big_size, big_size), "big_size"), "VertexColor": _color(color),
                     "TargetBlendMode": "Add", "Shader": Q(FANCY_LIGHT)}
    for k, v in params.items():
        big["Sprite"][k] = _r(v)
    small = {"Type": "Sprite", "RenderBucket": small_bucket, "Spin": _deg(small_spin_deg)}
    so = _vec(small_offset, "small_offset")
    if so != [0, 0]:
        small["Offset"] = so
    small["Sprite"] = {"Texture": {"File": Q(RADIATION_SMALL), "MipLevels": "max", "SampleMode": "Linear"},
                       "Size": _wh((small_size, small_size), "small_size"),
                       "VertexColor": _color(small_color if small_color is not None else color),
                       "TargetBlendMode": "Add"}
    return {"RadiationLight": big, "RadiationSpin": small}


# ----------------------------------------------------------------------------- arte de projeteis (meta.json)
# Corpo: o padrao de shots._missile_visuals (Sprite IsLit + NormalsTexture; vanilla/SW:ACD missile_he.rules l.53-70
# "IsLit = true" + NormalsTexture). Luzes: AnimatedSprite aditivo como o HELightsSprite do missile_he.rules
# (l.72-92: AtlasSprite { Texture, Size, TargetBlendMode Add }, FrameCount, FrameSize, FramesPerRow,
# FramesPerSecond) e WrapMode Clamp como o ArmingSprite do mine_deployed.rules (l.96-123; no SW:ACD:
# buzzdroid.rules l.168): a animacao para no ultimo quadro (contagem do carrapato). Faixa: Sprite com VertexColor.
WRAP_MODES = ("Clamp",)     # unico valor de WrapMode provado no 0.30.4c (enum invalido derruba o carregamento)


def _art_tex(prefix, name, linear=False):
    t = {"File": Q(f"{prefix}{name}"), "MipLevels": "max"}
    if linear:
        t["SampleMode"] = "Linear"
    return t


def art_size(item, size):
    """Tamanho no jogo [comprimento, largura]: size numero = multiplica item["size"] (o tamanho da arte em tiles);
    size [L, W] = tamanho absoluto."""
    if isinstance(size, (int, float)) and not isinstance(size, bool):
        if size <= 0:
            raise ValueError(f"size: multiplicador positivo, veio {size!r}")
        base = _wh(item["size"], "item['size']")
        return [_r(base[0] * size), _r(base[1] * size)]
    return _wh(size, "size")


def art_sprite_components(img_prefix, item, size, bucket_body="BulletUpper3", bucket_lights="BulletUpper4",
                          lights=True, mask_color=None, mask_additive=False, bucket_mask=None, offset=0):
    """Componentes de sprite de um projetil com arte propria (um item de art3d/<pasta>/meta.json, CONTRATOS 3).
      img_prefix: pasta das PNGs copiadas, relativa ao arquivo do projetil (ex.: "../bs_missile_art/");
      size: multiplicador do tamanho da arte (numero) ou [L, W] absoluto em tiles (ver art_size);
      lights: inclui o atlas de luzes quando o item tem "lights";
      mask_color: VertexColor da faixa (so quando o item tem "mask"); None = sem faixa;
      mask_additive: False = faixa iluminada (IsLit + normais do corpo + VertexColor; VertexColor em sprite
        iluminado NAO foi testado no jogo); True = faixa aditiva sem luz (TargetBlendMode Add + VertexColor, a
        combinacao ja usada nos brilhos do mod; a faixa fica emissiva);
      bucket_mask: balde da faixa (padrao = bucket_lights, sempre acima do corpo);
      offset: numero (x) ou [x, y] aplicado a todos os componentes (padrao: centro da arte no projetil).
    Retorna {"Sprite": corpo, "MaskSprite": faixa (opcional), "LightsSprite": atlas (opcional)}."""
    for k in ("file", "size"):
        if not item.get(k):
            raise KeyError(f"item de arte sem {k!r}: {item!r}")
    prefix = img_prefix if (not img_prefix or img_prefix.endswith("/")) else img_prefix + "/"
    wh = art_size(item, size)
    off = _vec(offset, "offset")

    def base(kind, bucket):
        c = {"Type": kind, "RenderBucket": bucket}
        if off != [0, 0]:
            c["Offset"] = list(off)
        return c

    comps = {}
    body = base("Sprite", bucket_body)
    normals = item.get("normals")
    if normals:
        body["IsLit"] = True
    body["Sprite"] = {"Texture": _art_tex(prefix, item["file"]), "Size": list(wh)}
    if normals:
        body["NormalsTexture"] = _art_tex(prefix, normals)
    comps["Sprite"] = body

    if item.get("mask") and mask_color is not None:
        m = base("Sprite", bucket_mask or bucket_lights)
        if mask_additive or not normals:
            m["Sprite"] = {"Texture": _art_tex(prefix, item["mask"], linear=True), "Size": list(wh),
                           "VertexColor": _color(mask_color, "mask_color"), "TargetBlendMode": "Add"}
        else:
            m["IsLit"] = True
            m["Sprite"] = {"Texture": _art_tex(prefix, item["mask"]), "Size": list(wh),
                           "VertexColor": _color(mask_color, "mask_color")}
            m["NormalsTexture"] = _art_tex(prefix, normals)
        comps["MaskSprite"] = m

    lt = item.get("lights")
    if lights and lt and _int(lt["frames"], "lights.frames") == 1:
        # 2.0 (WP03): atlas de UM quadro (ex.: AC dos niveis s/m/l re-renderizada sem o sensor piscando, fps 0) =
        # sprite aditivo parado (FramesPerSecond 0 num AnimatedSprite nao aparece no corpus)
        ls = base("Sprite", bucket_lights)
        ls["Sprite"] = {"Texture": _art_tex(prefix, lt["file"], linear=True), "Size": list(wh),
                        "TargetBlendMode": "Add"}
        comps["LightsSprite"] = ls
        return comps
    if lights and lt:
        anim = {"AtlasSprite": {"Texture": _art_tex(prefix, lt["file"], linear=True), "Size": list(wh),
                                "TargetBlendMode": "Add"},
                "FrameCount": _int(lt["frames"], "lights.frames"),
                "FrameSize": [_int(v, "lights.frame_px") for v in lt["frame_px"]],
                "FramesPerRow": _int(lt["per_row"], "lights.per_row"),
                "FramesPerSecond": _int(lt["fps"], "lights.fps")}
        if anim["FrameCount"] < 1 or anim["FramesPerRow"] < 1 or len(anim["FrameSize"]) != 2:
            raise ValueError(f"atlas de luzes invalido: {lt!r}")
        wrap = lt.get("wrap")
        if wrap is not None:
            if wrap not in WRAP_MODES:
                raise ValueError(f"WrapMode {wrap!r} nao provado no 0.30.4c (so {WRAP_MODES})")
            anim["WrapMode"] = wrap
        ls = base("AnimatedSprite", bucket_lights)
        ls["Animation"] = anim
        comps["LightsSprite"] = ls
    return comps


# ============================================================================= 2.0 (WP03): paleta, luzes, brasas
TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))    # tools/
ROOT_DIR = os.path.dirname(TOOLS_DIR)                                       # repositorio
ART2_PATH = os.path.join(TOOLS_DIR, "spec", "bullet_strike_art2.json")     # split do SPEC_2.0 (art_assets)
SPEC_PATH = os.path.join(TOOLS_DIR, "spec", "bullet_strike_spec.json")
SWITCHES_PATH = os.path.join(TOOLS_DIR, "spec", "bullet_strike_switches.json")
_PAL = None
_SPEC_SW = None


def _warn(msg):
    """Aviso do build: bs_data.warn quando o bs_data esta carregado (entra na lista '(aviso)' do build_mod)."""
    D = sys.modules.get("bs_data")
    if D is not None and callable(getattr(D, "warn", None)):
        D.warn(msg)
    else:
        print(f"(aviso) {msg}", file=sys.stderr)


def palette():
    """SPEC.art_assets.palette (tools/spec/bullet_strike_art2.json): cores 2.0 por municao/familia."""
    global _PAL
    if _PAL is None:
        with open(ART2_PATH, encoding="utf-8") as fh:
            _PAL = json.load(fh)["art_assets"]["palette"]
    return _PAL


# chaves de tiro que nao sao chaves da paleta
PAL_ALIAS = {"slug": "rail", "nuke": "nuclear", "missile_he": "msl_he", "missile_emp": "msl_emp"}


def pal(key):
    """Entrada da paleta de uma municao/familia (he, ap, sap, ac, frag, pem, rail/slug, cluster, ...)."""
    p = palette()
    k = PAL_ALIAS.get(key, key)
    if k not in p:
        raise KeyError(f"paleta 2.0 sem a chave {key!r} (ha: {', '.join(sorted(p))})")
    return p[k]


def art_switch(name):
    """Valor do switch art.<name>: bs_data.switch quando o bs_data ja esta carregado (o build_mod carrega antes de
    tudo); senao env BS_ART_<NAME>, tools/spec/bullet_strike_switches.json (BS_SWITCHES_FILE) e o padrao do spec.
    Nunca importa o bs_data (montar os dados de dentro de um tijolo de efeito seria um ciclo)."""
    key = f"art.{name}"
    D = sys.modules.get("bs_data")
    if D is not None and callable(getattr(D, "switch", None)):
        return D.switch(key)
    env = os.environ.get(f"BS_ART_{name.upper()}", "").strip()
    if env:
        return env
    p = os.environ.get("BS_SWITCHES_FILE") or SWITCHES_PATH
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            v = json.load(fh).get(key)
        if v is not None:
            return v
    global _SPEC_SW
    if _SPEC_SW is None:
        with open(SPEC_PATH, encoding="utf-8") as fh:
            _SPEC_SW = json.load(fh)["switches"]
    return _SPEC_SW["art"][name]["default"]


# Luz de projetil em duas sprites (SPEC.art_assets.phase_b_leftovers.islight_white_hull, ADDENDUM G7). Modelo do
# fancy_light.shader sobre peca: L_c = refl x c/255 x D_c + add x c/255; sobre o espaco: unlit x c/255
# (plasma_fx.py, bolt_components). Casco branco (D ~ 0,85) vira mancha BRANCA quando os tres canais passam de 1.
HALO_DIV = 4                 # halo = round(glow / 4) (mesmo brilho no espaco da Fase B com unlit 0,8 / 0,5)
HULL_REFL_DEFAULT = 6        # luz de casco: refl 6 (AC e slug: palette.<k>.hull_refl = 4)
HULL_ADD = 0.05
WHITE_HULL_DIFFUSE = 0.85
UNLIT_TRACER = 0.8           # halo dos tracantes (Fase B: 0,2 x glow)
UNLIT_SHELL = 0.5            # halo de granadas e misseis (Fase B: 0,125 x glow)
LIGHT_SPLITS = ("split", "legacy")


def c_min_limit(refl):
    """Maior valor permitido para o canal mais fraco da luz de casco: floor(0,5 x 255 / (0,85 x refl))
    (25 a refl 6, 37 a refl 4, 15 a refl 10): pelo menos um canal nunca satura no casco branco."""
    return int(math.floor(0.5 * 255 / (WHITE_HULL_DIFFUSE * float(refl)) + 1e-9))


def hull_refl(key):
    """_litReflectiveStrength da luz de casco da municao key (palette.<k>.hull_refl ou 6)."""
    v = pal(key).get("hull_refl") or HULL_REFL_DEFAULT
    return int(v) if float(v) == int(v) else float(v)


def start_time(turret_radius_tiles, speed_tiles_s, lo=0.01, hi=0.05):
    """StartTime das luzes do projetil: clamp((raio da torre + 1) / velocidade, 0,01, 0,05) s, com 3 casas: no quadro
    do disparo o brilho parado na boca nao lava a arte da propria torre (plasma_fx: tail_start)."""
    sp = float(speed_tiles_s or 0)
    if sp <= 0:
        return hi
    return round(min(hi, max(lo, (float(turret_radius_tiles) + 1.0) / sp)), 3)


def halo_vertex_color(glow):
    """Cor do halo: round(glow / 4) por canal (0,5 sobe)."""
    return [int(math.floor(float(v) / HALO_DIV + 0.5)) for v in list(glow)[:3]]


def light_pair(halo_size, halo_color, hull_size=None, hull_color=None, start=None, unlit=UNLIT_SHELL,
               x_halo=0, x_hull=0, refl=None, key=None, z=0, bucket="BulletUpper4", split=None, legacy_unlit=None,
               ammo=None):
    """Luzes IsLight de um projetil: {"GlowSprite": halo, "GlowSprite2": luz de casco (so com hull_size)}.

    Ordem posicional (plano WP03): light_pair(halo_size, halo_color, hull_size, hull_color, start, unlit); o resto
    por nome.
      halo_size [L, W] (tiles): o tamanho do brilho da Fase B; halo_color: a cor 'glow' CHEIA da paleta (aqui
        vira round(glow / 4), _litReflectiveStrength 0 e _litAdditiveStrength 0: o halo so aparece no ESPACO);
      hull_size [L, W] ou None: None = so o halo (tracantes <= 30 mm: uma luz por tiro como na Fase B); granadas
        [1,2 L, max(1,2 W, 0,5)], misseis [1,2 L, 1,2 W] no bocal, slug [3,6, 1,2], PEM [1,2 L, 0,6];
      hull_color: VertexColor da luz de casco (padrao palette[key].hull); refl: _litReflectiveStrength dela
        (padrao hull_refl(key) = 6, AC e slug 4); o canal mais fraco tem de ficar <= c_min_limit(refl), senao
        ValueError no build;
      start: StartTime (s) das duas sprites (start_time(); None = sem StartTime);
      unlit: _unlitAdditiveStrength do halo (UNLIT_TRACER 0,8 / UNLIT_SHELL 0,5);
      x_halo / x_hull: Offset x (numero) ou [x, y]; z: Z das duas; bucket: balde (BulletUpper4 como na Fase B);
      key (ou ammo, apelido): chave da paleta (he, ap, sap, ac, pem, rail/slug, cluster, ...);
      split: None le o switch art.light_split; 'legacy' = UMA luz da Fase B (cor glow cheia, refl 24, add 0,05,
        unlit legacy_unlit: 0,2 sem hull_size / 0,125 com) para o teste A/B T-ART-5."""
    key = key or ammo
    split = split or art_switch("light_split")
    if split not in LIGHT_SPLITS:
        raise ValueError(f"art.light_split invalido: {split!r} (use {', '.join(LIGHT_SPLITS)})")

    def spr(size, x, color, r_, add, ul):
        c = {"Type": "Sprite", "RenderBucket": bucket, "Z": _r(z), "IsLight": True}
        if start:
            c["StartTime"] = _r(start, 3)
        c["Offset"] = _vec(x, "offset")
        c["Sprite"] = {"Texture": {"File": Q(BLOB), "MipLevels": "max", "SampleMode": "Linear"},
                       "Size": _wh(size, "size"), "VertexColor": _color(color), "TargetBlendMode": "Add",
                       "Shader": Q(FANCY_LIGHT), "_z": 1, "_nrmlStrengthLimit": 1,
                       "_litReflectiveStrength": r_, "_litAdditiveStrength": add, "_unlitAdditiveStrength": ul}
        return c
    glow = _color([int(round(float(v))) for v in list(halo_color)[:3]], "halo_color")
    if split == "legacy":
        lu = legacy_unlit if legacy_unlit is not None else (0.2 if hull_size is None else 0.125)
        return {"GlowSprite": spr(halo_size, x_halo, glow, 24, HULL_ADD, lu)}
    out = {"GlowSprite": spr(halo_size, x_halo, halo_vertex_color(glow), 0, 0, unlit)}
    if hull_size is not None:
        if hull_color is None:
            if key is None:
                raise ValueError("light_pair: hull_size sem hull_color nem key")
            hull_color = pal(key)["hull"]
        if refl is None:
            refl = hull_refl(key) if key else HULL_REFL_DEFAULT
        hc = _color(hull_color, "hull_color")
        lim = c_min_limit(refl)
        if min(hc[:3]) > lim:
            raise ValueError(f"light_pair: luz de casco {hc} com canal mais fraco {min(hc[:3])} > {lim} (refl {refl}): "
                             f"lavaria o casco branco (regra c_min, SPEC.art_assets.phase_b_leftovers)")
        out["GlowSprite2"] = spr(hull_size, x_hull, hc, refl, HULL_ADD, 0)
    return out


def embers(note, n=(8, 11), speed=(2.5, 6), life=(1.0, 1.5), color_from=(0.86, 0.12, 0.24, 1),
           color_to=(1, 0.78, 0.31, 1), scale=(0.35, 0.7), spread=(0.3, 0.6), away_x=-0.6, end_scale=0.55,
           ramp=None, bucket="Upper1", zoom="30", delay=0):
    """Brasas: n particulas aditivas (blob.png) que nascem numa faixa de +-spread em volta do ponto, saem para longe de
    (away_x, 0) com velocidade speed, freiam ate 10 % e apagam em life s (o alvo "continua queimando"). Receita das
    gotas de brasa do missile_fx (tijolos de fxkit.streaks provados pelo plasma), so com cor/quantidade/vida como
    parametro: AC (ac_embers, carmim -> ouro) e Tupa (rail_embers, laranja-ouro -> brasa escura)."""
    ramp = ramp or [(1.6, 1.6, 1.6, 1), (1.2, 1.2, 1.2, 0.9), (1, 1, 1, 0.6), (0.7, 0.7, 0.7, 0)]
    pre = [_el("SetRandom", DataOut="location", ValueType="Vector2", FromValue=V(-_r(spread[0]), -_r(spread[1])),
               ToValue=V(_r(spread[0]), _r(spread[1]))),
           _el("SetRandomVelocityFromPoint", LocationIn="location", VelocityOut="base_velocity",
               Speed=R(speed[0], speed[1]), AwayFromPoint=V(_r(away_x), 0)),
           _el("SetRandom", DataOut="base_color", ValueType="Color", FromValue=C(*color_from), ToValue=C(*color_to)),
           _el("SetRandom", DataOut="base_scale", ValueType="Float", FromValue=scale[0], ToValue=scale[1]),
           _el("SetRandom", DataOut="lifetime", ValueType="Float", FromValue=life[0], ToValue=life[1])]
    init = [_el("LocationToWorldSpace", LocationIn="location", LocationOut="location"),
            _el("VelocityToWorldSpace", VelocityIn="base_velocity", VelocityOut="base_velocity"),
            _el("AddFrameOfReference", VelocityInOut="inherited_velocity"),
            _el("ScaleToWorldSpace", ScaleIn="base_scale", ScaleOut="base_scale")]
    upd = [_el("VariableLifetime", LifeInOut="life", LifetimeIn="lifetime"),
           _el("Lerp", True, LerpIn="life", DataOut="velocity", Invert=False, ValueType="Vector2",
               FromValue=V(1, 1), ToValue=V(0.1, 0.1)),
           _mul("Vector2", "velocity", "base_velocity", "velocity", upd=False),
           _addt("location", "velocity"),
           _addt("location", "inherited_velocity"),
           _ramp("color", ramp),
           _mul("Color", "color", "base_color", "color"),
           _el("Lerp", True, LerpIn="life", DataOut="scale", Invert=False, ValueType="Float", FromValue=1,
               ToValue=end_scale),
           _mul("Float", "scale", "base_scale", "scale")]
    mat = {"Texture": _tex(BLOB), "TargetBlendMode": dict(ADD)}
    return _particles(note, init, upd, _renderer(), mat, _emitter(pre, n), bucket, True, zoom, inflate=3, delay=delay)


def textured_blob(note, tex_path, size, life, color, ramp, scale=(1, 1), loc_x=0, offset=(0, 0), bucket="Upper2",
                  fancy=False, zoom=MAXZ, delay=0, n=(1, 1)):
    """Uma particula aditiva com textura propria (anel bs_ring_thin, leque bs_frag_cone): o blob() com Offset no
    Renderer (fracao do quadro, como o Offset {X 0; Y 0.5} do bullet_trail_def.rules vanilla) e Delay no rabo.
    offset (0.5, 0) poe a borda esquerda do quadro (o vertice do leque) no ponto do efeito em qualquer escala."""
    pre = [_el("SetValue", DataOut="location", ValueType="Vector2", Value=V(_r(loc_x), 0)),
           _el("SetValue", DataOut="base_color", ValueType="Color", Value=C(*color)),
           _el("SetValue", DataOut="base_scale", ValueType="Float", Value=_r(size))]
    upd = [_el("Lifetime", LifeInOut="life", Lifetime=_r(life)),
           _addt(),
           _ramp("color", ramp),
           _mul("Color", "color", "base_color", "color"),
           _el("Lerp", True, LerpIn="life", DataOut="scale", Invert=False, ValueType="Float",
               FromValue=scale[0], ToValue=scale[1]),
           _mul("Float", "scale", "base_scale", "scale")]
    mat = {"Texture": _tex(tex_path), "TargetBlendMode": dict(ADD)}
    return _particles(note, _local_init(), upd, _renderer(offset=offset), mat, _emitter(pre, n), bucket, fancy, zoom,
                      inflate=3, delay=delay)


# ----------------------------------------------------------------------------- arte dos misseis (pasta)
MISSILE_ART_ENV = "BS_MISSILE_ART_DIR"
MISSILE_ART_DIR = os.path.join(ROOT_DIR, "art3d", "bs_missiles2")


def missile_art_dir():
    """Pasta da arte dos misseis: env BS_MISSILE_ART_DIR (folhas de teste) ou art3d/bs_missiles2 (ADOTADA, BASE).
    So se a 2.0 faltar entra a reserva 1.x do bloco LEGACY_1X_FALLBACK (aviso 'arte 1.x usada: misseis')."""
    d = os.environ.get(MISSILE_ART_ENV)
    if d:
        return d
    if os.path.isfile(os.path.join(MISSILE_ART_DIR, "meta.json")):
        return MISSILE_ART_DIR
    # LEGACY_1X_FALLBACK inicio
    old = os.path.join(ROOT_DIR, "art3d", "bs_missiles")
    if os.path.isfile(os.path.join(old, "meta.json")):
        _warn("arte 1.x usada: misseis (art3d/bs_missiles2/meta.json ausente; reserva art3d/bs_missiles)")
        return old
    # LEGACY_1X_FALLBACK fim
    return MISSILE_ART_DIR


def missile_art_meta():
    """meta.json (kind 'missiles') da pasta de missile_art_dir(), com '_dir'; None sem meta."""
    d = missile_art_dir()
    p = os.path.join(d, "meta.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        meta = json.load(fh)
    if meta.get("kind") != "missiles":
        raise ValueError(f"{p}: meta.json nao e de misseis (kind {meta.get('kind')!r})")
    return dict(meta, _dir=d)


def selfcheck(mod_dir, spec):
    """Arquivos de shots/bs_nuke_fx escritos (Iara) e a regra R4 da limpeza 1.x neste arquivo."""
    probs = []
    for name in NUKE:
        if not os.path.isfile(os.path.join(mod_dir, NUKE_DIR, f"{name}.rules")):
            probs.append(f"{NUKE_DIR}/{name}.rules nao foi escrito")
    probs += legacy_scan(os.path.abspath(__file__))
    return probs


_LEGACY_PAT = r"bs_shells([^2]|$)|bs_missiles([^2]|$)"


def legacy_scan(path):
    """R4 (SPEC.art_assets.legacy_1x_cleanup): nenhuma citacao das pastas de arte 1.x de granadas/misseis fora dos
    blocos '# LEGACY_1X_FALLBACK inicio' / 'fim' do arquivo path, e no maximo um bloco."""
    import re
    probs = []
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    inside, blocks = False, 0
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if s == "# LEGACY_1X_FALLBACK inicio":
            if inside:
                probs.append(f"{os.path.basename(path)}:{i}: bloco LEGACY_1X_FALLBACK aberto duas vezes")
            inside, blocks = True, blocks + 1
            continue
        if s == "# LEGACY_1X_FALLBACK fim":
            inside = False
            continue
        if not inside and re.search(_LEGACY_PAT, ln) and "_LEGACY_PAT" not in ln:
            probs.append(f"{os.path.basename(path)}:{i}: pasta de arte 1.x fora do bloco LEGACY_1X_FALLBACK")
    if inside:
        probs.append(f"{os.path.basename(path)}: bloco LEGACY_1X_FALLBACK sem fim")
    if blocks > 1:
        probs.append(f"{os.path.basename(path)}: {blocks} blocos LEGACY_1X_FALLBACK (esperado 1)")
    return probs
