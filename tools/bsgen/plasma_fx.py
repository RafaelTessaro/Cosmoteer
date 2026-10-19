"""Familia de efeitos de PLASMA da Boitata (bs_plasma_gatling) e do Curupira (bs_plasma_heavy).

Tudo vai em BulletStrike/shots/bs_plasma_fx/: as texturas de bsgen/plasma_tex.py e um .rules de particulas por
efeito. Os elementos (Initializers / Updaters / Renderer / Material) sao copias dos arquivos vanilla 0.30.x
abaixo, com SO os valores trocados (mesmos campos e tipos; nenhum campo exclusivo do 0.30.5):

  descarga de boca (flipbook)   ships/terran/laser_blaster_small/particles/laser_blaster_small_shoot.rules
  faiscas (riscos)              shots/laser_bolt_small/particles/laser_bolt_sparks_def.rules (+ emissor de
                                shots/bullet_railgun/particles/bullet_railgun_sparks.rules: SetRandomVelocityFromPoint)
  anel de choque                ships/terran/railgun_launcher/particles/railgun_shoot.rules (textura vanilla)
  luz no casco                  shots/laser_bolt_small/particles/laser_bolt_small_flash.rules (particle_light)
  brilho / clarao               o mesmo flash com StandardQuadRenderer e mistura aditiva (visivel sobre o espaco)
  arcos eletricos na boca       ships/terran/disruptor/particles/disruptor_shoot_lightning.rules
  crepitar em volta do raio     shots/disruptor_bolt/particles/disruptor_bolt_lightning.rules
  rastro ionizado (Curupira)    shots/bullet_railgun/particles/bullet_trail_railgun.rules (FpsCompensator SEM
                                InheritVelocity: a particula fica parada onde nasceu) + barreira do escudo do
                                mine_shrapnel_trail.rules, com blob esticado e mistura aditiva comum; Delay como o
                                missile_emp_thruster_lightning.rules (efeito preso ao projetil)
  rabo do resto do arquivo      bsgen/trails.TAIL_TEXT (carrega no 0.30.4c), so Bucket/IsFancy/zoom/Delay mudam

Orcamento (Boitata a 10 tiros/s por arma, 9 no overclock): boca <= 8 particulas por tiro no normal e <= 12 no
overclock, quase todas de <= 0,14 s (~10 vivas por arma; o anel e um pulso de 0,065 s, menor que o intervalo entre
tiros; a luz no casco fica a frente do cano e o brilho residual e fraco, para nao lavar a arte da torre a 10
tiros/s); raio 0 particulas no normal (so 5 sprites: sombra, corona, nucleo, cauda AnimatedSprite e luz) e ~2-3
vivas por raio no overclock (crepitar 28/s de 0,06-0,1 s); impacto <= 9 particulas no normal e <= 10 no overclock,
a maioria de <= 0,3 s (~20 vivas por arma). Curupira (~1,5 tiro/s, ~4 raios no ar): rastro ionizado de ~10-14
particulas vivas por raio (~40-60 por arma, no lugar do rastro deck de 300/s, ~250 por arma) e crepitar de ~4-7
vivas por raio. Todos os sistemas com InitCapacity 256, como no vanilla. Detalhes (faiscas, arcos, luzes, rastro)
com IsFancy = true; o essencial (descarga, respingo, clarao) com IsFancy = false. Luz IsLight so para iluminar o
casco: o que aparece sobre o espaco vazio vem de sprites/particulas aditivos comuns.
"""

from rules_dsl import Q, VOID, Inh, render
from bsgen import trails as TR

DIR = "shots/bs_plasma_fx"
D = "./Data"
MAXZ = "3.4028235E+38"
BLOB = f"{D}/common_effects/particles/blob.png"
SPARK = f"{D}/common_effects/particles/spark.png"
# anel fino proprio (bsgen/plasma_tex.shock_ring): o shockwave.png vanilla tem o miolo cheio e virava uma "bolha"
SHOCK = "bs_plasma_shock.png"
RING = f"{D}/ships/terran/railgun_launcher/particles/railgun_shoot.png"
LIGHT_SHADER = f"{D}/common_effects/particles/particle_light.shader"
LIGHTNING_SHADER = f"{D}/shots/disruptor_bolt/particles/particle_lightning.shader"
DISCHARGE = f"{D}/shots/disruptor_bolt/particles/disruptor_bolt_discharge.png"
CRACKLE = f"{D}/shots/disruptor_bolt/particles/disruptor_bolt_lightning.png"

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

# ----------------------------------------------------------------------------- configuracao por arma
# Tamanhos em tiles. "N" = normal, "OC" = overclock (mais quente/branco e maior). Cores float {R, G, B, A}.
CFG = {
    # Boitata: 2x3, 4 canos girando, 1 emissor no centro (boca em 1,93). Com o giro no maximo: 10 tiros/s
    # (intervalo 0,1 s) no normal e 9 tiros/s no overclock (o overclock MULTIPLICA o intervalo por 1,1111: 0,111 s)
    "gatling": {
        "N": {
            "burst": {"size": 2.0, "life": 0.085, "gain": 1.15},
            "streaks": {"n": (3, 4), "speed": (6, 13), "life": (0.08, 0.14), "scale": (0.6, 0.95), "spread": 0.28,
                        "white": 0.6},
            # anel = pulso curto (0,065 s, bem abaixo do intervalo de 0,1 s entre tiros): pico em ~16 ms e alfa
            # ~0 em ~40 ms, entao 40 ms depois de cada tiro a boca ja esta limpa (nada de "colar" parado). Pico de
            # alfa 0,7 no normal (le como tremor de choque, nao como um "O" de portal); o anel forte fica para o OC
            "ring": {"scale": 0.8, "life": 0.065, "x": 0.15, "pulse": True, "alpha": 0.74},
            # luz mais fraca e A FRENTE do cano (x): a 10 tiros/s nao pode lavar a arte da torre; vida 0,08 s
            # (menor que o intervalo) para piscar em vez de virar um serrote continuo. Brilho residual fraco em
            # todo tiro (n = (1, 1); o vanilla nunca usa {Min = 0  Max = 1}): ~2 vivos por vez = cano quente
            "light": {"scale": 2.0, "life": 0.08, "x": 0.7, "color": (0.25, 0.85, 1, 0.2)},
            "glow": {"scale": 0.85, "wh": (1, 1), "x": -0.1, "life": 0.2, "color": (0.2, 0.85, 1, 0.2),
                     "n": (1, 1)},
            "arcs": None,
            # serpente de fogo, nao girino: nucleo em lanca longa (bs_plasma_lance), corona afunilada que emenda
            # na cauda (bs_plasma_corona) e cauda = corpo grosso que afina por ~4,5 tiles (bs_plasma_tail). Sombra
            # escura por baixo (bs_plasma_shade) para ler sobre casco branco. Luz IsLight achatada (5,5 x 2): a
            # poca de luz acompanha a lanca em vez de virar um oval claro em volta dela sobre casco claro
            "bolt": {"core": (2.2, 0.36), "core_tex": "bs_plasma_lance.png", "corona": (2.9, 0.64),
                     "corona_tex": "bs_plasma_corona.png", "corona_color": [0, 185, 255],
                     "tail": (4.6, 0.8), "tail_tex": "bs_plasma_tail.png", "tail_start": 0.018, "glow": (5.5, 2),
                     "glow_x": -1.1, "glow_color": [0, 235, 255], "shade": (4.4, 0.7)},
            "crackle": None,
            # respingo um pouco maior (2,8) e faiscas mais longas e claras: "plasma derretido espirrando" na escala
            # de batalha, ainda <= 9 particulas por impacto
            "hit": {"splash": 2.8, "splash_life": 0.28, "sparks": (4, 6), "spark_speed": (2.5, 9),
                    "spark_life": (0.16, 0.32), "spark_scale": (0.6, 0.95), "flash": 1.4, "flash_life": 0.08,
                    "scorch": 2.6, "scorch_life": 0.6, "shield": 2.6, "shield_life": 0.22},
        },
        "OC": {
            # vida 0,08 s < intervalo de 0,111 s do overclock: a descarga pulsa em vez de ficar acesa direto
            "burst": {"size": 2.6, "life": 0.08, "gain": 1.4},
            "streaks": {"n": (5, 6), "speed": (7, 15), "life": (0.09, 0.16), "scale": (0.7, 1.1), "spread": 0.32,
                        "white": 0.85},
            "ring": {"scale": 0.95, "life": 0.065, "x": 0.18, "pulse": True, "alpha": 1.0},
            "light": {"scale": 2.8, "life": 0.09, "x": 0.6, "color": (0.45, 0.95, 1, 0.36)},
            "glow": {"scale": 1.0, "wh": (1, 1), "x": -0.1, "life": 0.22, "color": (0.45, 0.95, 1, 0.28),
                     "n": (1, 1)},
            "arcs": {"n": (1, 2), "scale": (0.22, 0.32), "life": (0.16, 0.22)},
            # o "mais quente" do overclock fica nas sprites aditivas (nucleo/corona/cauda maiores e mais brancos);
            # a luz IsLight continua ciano e quase do tamanho do normal, senao ela vira uma nevoa clara sobre o casco
            "bolt": {"core": (2.6, 0.42), "core_tex": "bs_plasma_lance.png", "corona": (3.3, 0.74),
                     "corona_tex": "bs_plasma_corona.png", "corona_color": [60, 215, 255],
                     "tail": (5.4, 0.92), "tail_tex": "bs_plasma_tail_oc.png", "tail_start": 0.018, "glow": (6, 2.2),
                     "glow_x": -1.2, "glow_color": [40, 220, 255], "shade": (5.2, 0.8)},
            # crepitar curto (0,06-0,1 s, mais vezes por segundo para manter a densidade): ele anda junto com o
            # raio (InheritVelocity) e continua voando depois do impacto ate morrer, entao vida curta = sobra pouco
            "crackle": {"eps": 28, "scale": (0.3, 0.45), "life": (0.06, 0.1)},
            "hit": {"splash": 3.2, "splash_life": 0.3, "sparks": (5, 7), "spark_speed": (2, 9),
                    "spark_life": (0.15, 0.32), "spark_scale": (0.5, 0.85), "flash": 1.6, "flash_life": 0.09,
                    "scorch": 3.2, "scorch_life": 0.65, "shield": 3.0, "shield_life": 0.24},
        },
    },
    "heavy": {     # Curupira: 4x5, 2 canos com pontas abertas (bocas em [3,75; +-0,5]), ~1,5 tiro/s alternado
        "N": {
            "burst": {"size": 3.4, "life": 0.13, "gain": 1.2},
            "streaks": {"n": (7, 9), "speed": (6, 14), "life": (0.12, 0.2), "scale": (0.8, 1.3), "spread": 0.45,
                        "white": 0.6},
            "ring": {"scale": 1.0, "life": 0.25, "x": 0.25},
            "light": {"scale": 4.2, "life": 0.16, "x": 0.5, "color": (0.25, 0.85, 1, 0.45)},
            # brilho residual entre as pontas (alongado no cano): nasce com o disparo, sobe ate ~25% da vida e
            # apaga. E um pos-brilho, nao uma carga antes do tiro (isso pediria FireDelay, que muda o jogo)
            "glow": {"scale": 1.0, "wh": (1.7, 0.65), "x": -0.25, "life": 0.35, "color": (0.35, 0.95, 1, 0.8),
                     "charge": True},
            "arcs": {"n": (3, 4), "scale": (0.4, 0.55), "life": (0.25, 0.35)},
            # cauda reta com aneis de pulso (esteira ionizada dos trilhos), nao a serpente da Boitata
            "bolt": {"core": (2.4, 0.75), "corona": (3.2, 1.3), "corona_color": [0, 160, 245],
                     "tail": (6.2, 1.2), "tail_tex": "bs_plasma_wake.png", "tail_start": 0.032, "glow": (12, 6),
                     "glow_color": [0, 235, 255], "shade": (6.4, 1.4)},
            "crackle": {"eps": 55, "scale": (0.45, 0.6), "life": (0.06, 0.1)},
            # rastro ionizado que FICA NO ESPACO atras do raio (sem InheritVelocity, padrao do rastro do railgun
            # vanilla; ver ion_trail): riscos finos e curtos a cada ~1,4 tile (200 m/s /
            # 140 por s; a parte visivel do blob esticado tem ~metade do comprimento, entao menos que isso abre
            # buracos). Vida 0,07 s = cauda de cometa de ~14 tiles que se solta da boca (com 0,14 s virava uma
            # linha continua da boca ao alvo, cara de tracante de laser/railgun), ~10 vivos por raio. Comeca 0,05 s
            # depois do disparo (200 m/s x 0,05 = 10 tiles; cada risco vai ate ~4,8 tiles atras do ponto onde
            # nasce, entao a ponta de tras fica a ~5 tiles da boca: nunca por cima da torre nem colada no cano)
            "trail": {"eps": 140, "life": 0.07, "len": 4.5, "wid": 0.3, "delay": 0.05,
                      "color": (0.1, 0.8, 1, 0.45)},
            "hit": {"splash": 4.2, "splash_life": 0.42, "sparks": (10, 14), "spark_speed": (3, 12),
                    "spark_life": (0.2, 0.5), "spark_scale": (0.7, 1.2), "flash": 3.0, "flash_life": 0.14,
                    "scorch": 5.0, "scorch_life": 1.0, "shield": 5.0, "shield_life": 0.35},
        },
        "OC": {
            "burst": {"size": 4.2, "life": 0.14, "gain": 1.5},
            "streaks": {"n": (9, 11), "speed": (7, 16), "life": (0.13, 0.22), "scale": (0.9, 1.5), "spread": 0.5,
                        "white": 0.9},
            "ring": {"scale": 1.25, "life": 0.28, "x": 0.3},
            "light": {"scale": 5.0, "life": 0.18, "x": 0.5, "color": (0.45, 0.95, 1, 0.5)},
            "glow": {"scale": 1.2, "wh": (1.7, 0.65), "x": -0.25, "life": 0.38, "color": (0.55, 1, 1, 0.9),
                     "charge": True},
            "arcs": {"n": (5, 6), "scale": (0.5, 0.65), "life": (0.28, 0.38)},
            "bolt": {"core": (2.9, 0.9), "corona": (3.8, 1.5), "corona_color": [40, 190, 255],
                     "tail": (7.4, 1.45), "tail_tex": "bs_plasma_wake_oc.png", "tail_start": 0.032, "glow": (12, 6),
                     "glow_color": [40, 220, 255], "shade": (7.6, 1.6)},
            "crackle": {"eps": 80, "scale": (0.55, 0.7), "life": (0.06, 0.1)},
            "trail": {"eps": 180, "life": 0.075, "len": 5.0, "wid": 0.36, "delay": 0.04,
                      "color": (0.3, 0.9, 1, 0.55)},
            # "Erupcao Solar" (explosao r3 no impacto): respingo grande + anel fino de pressao do tamanho da
            # explosao, rapido (0,24 s) e com o brilho concentrado no comeco, para nao cobrir o respingo
            "hit": {"splash": 6.0, "splash_life": 0.5, "sparks": (16, 20), "spark_speed": (4, 16),
                    "spark_life": (0.25, 0.6), "spark_scale": (0.8, 1.4), "flash": 4.5, "flash_life": 0.16,
                    "scorch": 6.5, "scorch_life": 1.2, "shield": 6.0, "shield_life": 0.4,
                    "shockwave": {"size": 6.0, "life": 0.24, "scale": (0.3, 1), "color": (0.4, 1, 1, 0.45),
                                  "ramp": [(1.2, 1.2, 1.2, 1), (0.5, 1, 1, 0.35), (0.2, 0.8, 1, 0.12),
                                           (0, 0.6, 1, 0)]}},
        },
    },
}

# sons (todos ./Data): impacto chiado de laser na Boitata, impacto pesado de laser no Curupira. O raio abatido no
# ar (pop) usa o chiado leve, baixo, nas duas armas
POP_SOUNDS = [f"{D}/shots/laser_bolt_small/sounds/laser_blaster_impact_0{i}.wav" for i in (1, 2, 3, 4)]
SOUNDS = {
    "gatling": {"N": [f"{D}/shots/laser_bolt_small/sounds/laser_blaster_impact_0{i}.wav" for i in (1, 2, 3, 4)],
                "OC": [f"{D}/shots/laser_bolt_small/sounds/laser_blaster_impact_0{i}.wav" for i in (1, 2, 3, 4)]},
    "heavy": {"N": [f"{D}/shots/laser_bolt_large/laser_bolt_large_hit.wav"],
              "OC": [f"{D}/shots/laser_bolt_large/overclock/sounds/heavy_laser_overclocked_impact_0{i}.wav"
                     for i in (1, 2, 3)]},
}

# centro do quadro das texturas proprias (pixel onde fica a boca / o ponto de impacto, quadros de 128 px)
BURST_CX = 40
SPLASH_CX = 76


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
    t = TR.TAIL_TEXT
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


def _lightning_material(tex):
    return {"Shader": {"File": Q(LIGHTNING_SHADER)},
            "_centerColor": C(0.85, 1, 1), "_outerColor": C(0, 0.85, 1), "_bloomColor": C(0, 0.55, 1),
            "Texture": _tex(tex, wrap=True, fix=True), "TargetBlendMode": dict(PURE_ADD)}


def arcs(note, n, scale, life, loc_x, bucket="DisruptorLightningUpper"):
    """Arcos eletricos radiais na boca (disruptor_shoot_lightning.rules, cores ciano no material; a rampa de cor
    do vertice e o controle da animacao do shader e fica como no vanilla)."""
    pre = [_el("SetRandom", DataOut="scale", ValueType="Float", FromValue=scale[0], ToValue=scale[1]),
           _el("SetRandom", DataOut="rot", ValueType="Angle", FromValue="0d", ToValue="360d"),
           _el("SetValue", DataOut="location", ValueType="Vector2", Value=V(_r(loc_x), 0))]
    init = [_el("LocationToWorldSpace", LocationIn="location", LocationOut="location"),
            _el("RotationToWorldSpace", RotationIn="rot", RotationOut="rot"),
            _el("ScaleToWorldSpace", ScaleIn="scale", ScaleOut="baseScale"),
            _el("AddFrameOfReference", VelocityInOut="velocity"),
            _el("SetRandom", DataOut="index", ValueType="Int", FromValue=0, ToValue=15),
            _el("SetRandom", DataOut="lifetime", ValueType="Float", FromValue=life[0], ToValue=life[1])]
    upd = [_el("VariableLifetime", LifeInOut="life", LifetimeIn="lifetime"),
           _ramp("color", [(0.486, 1, 1, 0.588), (0.486, 1, 0.392, 0.588), (1, 1, 0, 0.039)]),
           _el("Lerp", LerpIn="life", DataOut="scale", Invert=False, ValueType="Float", FromValue=1, ToValue=1),
           _mul("Float", "baseScale", "scale", "scale", upd=False),
           _el("Lerp", LerpIn="life", DataOut="frameAdd", Invert=False, ValueType="Int", FromValue=0, ToValue=15),
           _el("Operator", DataType="Int", AIn="index", BIn="frameAdd", ResultOut="newIndex", Operator="Add"),
           _el("UvSprites", True, SpriteIndexIn="newIndex", UvRectOut="uv_rect", TextureSize=V(1024, 1024),
               SpriteSize=V(256, 256), SpriteCount=16, SpritesPerRow=4, PixelOffset=V(0, 0), Looping=True),
           _addt()]
    return _particles(note, init, upd, _renderer(uv="uv_rect", offset=(0, 0.4)), _lightning_material(DISCHARGE),
                      _emitter(pre, n), bucket, True, MAXZ, inflate=3)


def crackle(note, eps, scale, life, bucket="DisruptorLightningUpper"):
    """Arcos curtos presos ao raio (disruptor_bolt_lightning.rules: InheritVelocity + barreira do escudo)."""
    pre = [_el("SetRandom", DataOut="rot", ValueType="Angle", FromValue="-15d", ToValue="15d"),
           _el("SetRandom", DataOut="baseScale", ValueType="Float", FromValue=scale[0], ToValue=scale[1])]
    init = [_el("LocationToWorldSpace", LocationIn="location", LocationOut="location"),
            _el("RotationToWorldSpace", RotationIn="rot", RotationOut="rot"),
            _el("ScaleToWorldSpace", ScaleIn="baseScale", ScaleOut="baseScale"),
            _el("SetRandom", DataOut="index", ValueType="Int", FromValue=0, ToValue=3),
            _el("UvSprites", SpriteIndexIn="index", UvRectOut="uv_rect", TextureSize=V(1024, 512),
                SpriteSize=V(512, 256), SpriteCount=4, SpritesPerRow=2, PixelOffset=V(0, 0), Looping=False),
            _el("SetRandom", DataOut="lifetime", ValueType="Float", FromValue=life[0], ToValue=life[1]),
            _el("InheritVelocity", VelocityInOut="velocity"),
            _el("SetBulletBarrierID", BarrierIDOut="barrier")]
    upd = [_el("VariableLifetime", LifeInOut="life", LifetimeIn="lifetime"),
           _ramp("color", [(0.486, 1, 1, 1), (0.862, 0, 0.196, 1), (1, 0, 0, 1)]),
           _el("Lerp", LerpIn="life", DataOut="scale", Invert=False, ValueType="Float", FromValue=2, ToValue=3),
           _mul("Float", "baseScale", "scale", "scale", upd=False),
           _addt(),
           _el("Barrier", BarrierIDIn="barrier", LocationIn="location")]
    em = {"EmitPerSecond": eps, "EmitPerOneShot": R(0, 0), "PreInitializers": pre, "PostInitializers": []}
    return _particles(note, init, upd, _renderer(uv="uv_rect", base=(1, 0.5)), _lightning_material(CRACKLE),
                      em, bucket, True, "30", inflate=1)


def ion_trail(note, eps, life, length, width, delay, color, bucket="BulletTrailUpper"):
    """Rastro ionizado que FICA NO ESPACO atras do raio. Padrao do bullet_trail_railgun.rules vanilla (o rastro do
    railgun fica parado onde nasceu): LocationToWorldSpace + FpsCompensator (VelocityIn vazio: espalha as
    particulas no caminho que o raio fez no quadro) e NENHUM InheritVelocity, entao nada move a particula depois
    que ela nasce. (Com InheritVelocity, como no crepitar e no disruptor_bolt_lightning.rules, as particulas
    andariam junto com o raio.) Barreira do escudo como no mine_shrapnel_trail.rules. Cada particula e um risco
    fino de blob alinhado ao raio (length x width tiles, centro meio risco atras da cabeca) que afina e some em
    `life` s; riscos de 4,5-5 tiles a 140-180/s (um a cada ~1,4 tile) emendam num canal continuo a 200-260 m/s.
    Delay: so comeca depois que o raio saiu da boca (o efeito preso ao missil EMP vanilla tambem usa Delay)."""
    pre = [_el("SetValue", DataOut="location", ValueType="Vector2", Value=V(-_r(length / 2 + 0.3), 0)),
           _el("SetValue", DataOut="rot", ValueType="Angle", Value="0d"),
           _el("SetValue", DataOut="base_color", ValueType="Color", Value=C(*color)),
           _el("SetBulletBarrierID", BarrierIDOut="barrier")]
    init = [_el("LocationToWorldSpace", LocationIn="location", LocationOut="location"),
            _el("FpsCompensator", LocationInOut="location", VelocityIn=VOID, Mode="Uniform"),
            _el("RotationToWorldSpace", RotationIn="rot", RotationOut="rot")]
    upd = [_el("Lifetime", LifeInOut="life", Lifetime=_r(life)),
           _el("Lerp", True, LerpIn="life", DataOut="scale2", Invert=False, ValueType="Vector2",
               FromValue=V(1, 1), ToValue=V(0.85, 0.35)),
           _ramp("color", [(1, 1, 1, 1), (1, 1, 1, 0.45), (1, 1, 1, 0.15), (1, 1, 1, 0)]),
           _mul("Color", "color", "base_color", "color"),
           _el("Barrier", BarrierIDIn="barrier", LocationIn="location")]
    em = {"EmitPerSecond": eps, "EmitPerOneShot": R(0, 0), "PreInitializers": pre, "PostInitializers": []}
    mat = {"Texture": _tex(BLOB), "TargetBlendMode": dict(ADD)}
    return _particles(note, init, upd, _renderer(scale=VOID, scale2="scale2", base=(length, width)), mat, em,
                      bucket, True, "30", inflate=3, delay=delay)


# ----------------------------------------------------------------------------- arquivos
def _name(w, mode, part):
    return f"bs_pfx_{w}{'_oc' if mode == 'OC' else ''}_{part}"


def _muzzle_files(w, mode, c):
    out = {}
    tag = f"{'Boitata' if w == 'gatling' else 'Curupira'} {'overclock' if mode == 'OC' else 'normal'}"
    b = c["burst"]
    g = b["gain"]
    out["muzzle_burst"] = flipbook(
        f"Descarga de plasma na boca ({tag}): flipbook bs_plasma_burst.png", "bs_plasma_burst.png", b["size"],
        b["life"], (64 - BURST_CX) / 128 * b["size"], scale=(0.9, 1.15),
        ramp=[_hot((1, 1, 1, 1), g), _hot((1, 1, 1, 1), 0.5 + 0.5 * g), (0.85, 1, 1, 0.85)])
    st = c["streaks"]
    out["muzzle_streaks"] = streaks(
        f"Riscos de plasma para frente na boca ({tag})", st["n"], st["speed"], st["life"], st["scale"], 0.02,
        st["spread"], -0.4 if w == "gatling" else -0.6, st["white"],
        [(0.55, 1, 1, 0.9), (0.15, 0.85, 1, 1)], "CannonFlare")
    r = c["ring"]
    out["muzzle_ring"] = ring(f"Anel de choque ciano na boca ({tag})", r["scale"], r["life"], r["x"],
                              gain=1.25 if mode == "OC" else 1.0, fancy=(w == "gatling"), pulse=r.get("pulse", False),
                              alpha=r.get("alpha", 1.0))
    li = c["light"]
    out["muzzle_light"] = blob(f"Luz ciano no casco ao disparar ({tag}; particle_light, centro a frente da boca)",
                               li["scale"], li["life"], li.get("x", 0), li["color"], [(1, 1, 1, 1), (1, 1, 1, 0)],
                               light=True, bucket="Upper1", fancy=True)
    gl = c["glow"]
    if gl.get("charge"):
        ramp = [(1, 1, 1, 0), (1, 1, 1, 1), (1, 1, 1, 0.55), (1, 1, 1, 0.2), (1, 1, 1, 0)]
        note = f"Brilho residual entre as pontas dos canos, depois do disparo ({tag})"
        wh = ((gl["wh"][0], gl["wh"][1]), (gl["wh"][0] * 0.8, gl["wh"][1] * 0.7))
    else:
        ramp = [(1, 1, 1, 0.9), (1, 1, 1, 0.5), (1, 1, 1, 0)]
        note = f"Brilho residual de cano quente ({tag})"
        wh = None
    out["muzzle_glow"] = blob(note, gl["scale"], gl["life"], gl["x"], gl["color"], ramp, scale=(0.8, 1.2), wh=wh,
                              n=gl.get("n", (1, 1)))
    if c.get("arcs"):
        a = c["arcs"]
        out["muzzle_arcs"] = arcs(f"Arcos eletricos ciano na boca ({tag})", a["n"], a["scale"], a["life"], 0.05)
    return out


def _bolt_files(w, mode, c):
    out = {}
    tag = f"{'Boitata' if w == 'gatling' else 'Curupira'} {'overclock' if mode == 'OC' else 'normal'}"
    if c.get("crackle"):
        k = c["crackle"]
        out["crackle"] = crackle(f"Crepitar eletrico em volta do raio de plasma ({tag})", k["eps"], k["scale"],
                                 k["life"])
    if c.get("trail"):
        t = c["trail"]
        out["trail"] = ion_trail(f"Rastro ionizado atras do raio de plasma ({tag})", t["eps"], t["life"], t["len"],
                                 t["wid"], t["delay"], t["color"])
    return out


def _hit_files(w, mode, c):
    out = {}
    tag = f"{'Boitata' if w == 'gatling' else 'Curupira'} {'overclock' if mode == 'OC' else 'normal'}"
    h = c["hit"]
    hot = 1.35 if mode == "OC" else 1.1
    sp = h["splash"]
    out["hit_splash"] = flipbook(
        f"Respingo de plasma no casco ({tag}): flipbook bs_plasma_splash.png", "bs_plasma_splash.png", sp,
        h["splash_life"], -(SPLASH_CX - 64) / 128 * sp, scale=(0.85, 1.1), rot=(-12, 12),
        ramp=[_hot((1, 1, 1, 1), hot), (1, 1, 1, 1), (0.8, 1, 1, 0.8)], bucket="Upper2")
    out["hit_sparks"] = streaks(
        f"Faiscas de plasma espirrando do casco ({tag})", h["sparks"], h["spark_speed"], h["spark_life"],
        h["spark_scale"], 0, 0.5 if w == "gatling" else 0.8, 0.4 if w == "gatling" else 0.6,
        0.7 if mode == "OC" else 0.45, [(0.45, 1, 1, 0.9), (0.1, 0.8, 1, 1)], "RailgunHitSparks",
        stretch=(2.6, 0.5))
    st = sp * 0.7
    out["hit_struct"] = flipbook(
        f"Respingo menor de plasma em peca ja destruida (HitStructural, {tag})", "bs_plasma_splash.png", st,
        h["splash_life"] * 0.85, -(SPLASH_CX - 64) / 128 * st, scale=(0.85, 1.1), rot=(-12, 12),
        ramp=[(1, 1, 1, 1), (0.9, 1, 1, 0.9), (0.7, 1, 1, 0.7)], bucket="Upper2")
    out["hit_flash"] = blob(f"Clarao branco-ciano do impacto ({tag})", h["flash"], h["flash_life"], 0,
                            (0.7, 1, 1, 1), [_hot((1, 1, 1, 1), hot), (0.4, 1, 1, 0.6), (0, 0.7, 1, 0)],
                            scale=(0.7, 1.15))
    out["hit_scorch"] = blob(f"Brasa ciano no casco atingido ({tag}; particle_light)", h["scorch"],
                             h["scorch_life"], 0, (0.3, 0.9, 1, 0.6),
                             [(1, 1, 1, 1), (0.6, 1, 1, 0.6), (0, 0.6, 0.9, 0)], scale=(0.8, 1.1), light=True,
                             bucket="Upper1", fancy=True)
    ss = h["shield"]
    sq = (0.45, 1.3)
    out["hit_shield"] = flipbook(
        f"Respingo de plasma espalhando na face do escudo ({tag})", "bs_plasma_splash.png", ss, h["shield_life"],
        -(SPLASH_CX - 64) / 128 * ss * sq[0], scale=(0.85, 1.1), rot=(-6, 6),
        scale2=(sq, (sq[0] * 0.8, sq[1] * 1.25)),
        ramp=[_hot((1, 1, 1, 1), hot), (0.8, 1, 1, 0.9), (0.4, 0.9, 1, 0.6)], bucket="Upper2")
    if h.get("shockwave"):
        sw = h["shockwave"]
        out["hit_shockwave"] = blob(
            f"Anel de pressao da Erupcao Solar ({tag}; raio da explosao, anel fino bs_plasma_shock.png)",
            sw["size"], sw["life"], 0, sw["color"], sw["ramp"], scale=sw["scale"], tex=SHOCK)
    return out


def all_files():
    """{nome sem extensao: texto do .rules} de todos os efeitos de plasma."""
    files = {}
    for w, modes in CFG.items():
        for mode, c in modes.items():
            for part, txt in {**_muzzle_files(w, mode, c), **_bolt_files(w, mode, c),
                              **_hit_files(w, mode, c)}.items():
                files[_name(w, mode, part)] = txt
    return files


def write(out, header):
    """Grava texturas e particulas na pasta do mod (sempre, inclusive com --no-art: PIL e rapido). plasma_tex
    (numpy + PIL) so e importado aqui: quem le bs_data (docs, textos) nao precisa dessas bibliotecas."""
    from bsgen import plasma_tex as PT
    for name, img in PT.all_textures().items():
        out.image(f"{DIR}/{name}", img)
    for name, txt in all_files().items():
        out.text(f"{DIR}/{name}.rules", "\n".join(f"// {ln}" for ln in header.split("\n")) + "\n" + txt)


# ----------------------------------------------------------------------------- referencias
def _ref(prefix, w, mode, part):
    return f"&<{prefix}{_name(w, mode, part)}.rules>"


PART_PREFIX = "../../shots/bs_plasma_fx/"     # de parts/<id>/<id>.rules
SHOT_PREFIX = "../bs_plasma_fx/"              # de shots/<id>/<id>.rules


def muzzle_paths(w, oc):
    """Caminhos (sem &<>) das particulas de boca, para FX[...]['particles'] / ['particles_oc'] em bs_data."""
    mode = "OC" if oc else "N"
    parts = ["muzzle_burst", "muzzle_streaks", "muzzle_ring", "muzzle_light", "muzzle_glow"]
    if CFG[w][mode].get("arcs"):
        parts.append("muzzle_arcs")
    return [f"{PART_PREFIX}{_name(w, mode, p)}.rules" for p in parts]


def _hit_sound(sounds, volume, max_conc):
    return Inh("/BASE_SOUNDS/AudioExterior", {"RandomSounds": [Q(s) for s in sounds], "Volume": _r(volume, 3),
                                              "SpeedVariation": 0.2, "MaxConcurrent": max_conc})


def hit_media(w, oc, kind, volume=0.6, max_conc=30, shake=0.0, shake_time=0.5):
    """Lista MediaEffects do impacto. kind:
      hull   (HitOperational): respingo, faiscas, clarao e brasa ciano (luz no casco) + som + tremor;
      struct (HitStructural, peca ja sem saude operacional): respingo menor, faiscas e clarao + som um pouco mais
             baixo, sem brasa (como o vanilla laser_bolt_small/large e bullet_railgun, que tambem tem particulas,
             faiscas e som no HitStructural);
      shield (HitShield): respingo achatado na face do escudo + clarao, sem brasa nem faiscas (o escudo ja desenha
             a propria ondulacao);
      pop    (Targetable.OnDeath, raio abatido no ar): o mesmo estouro do escudo + um chiado baixo."""
    mode = "OC" if oc else "N"
    P = SHOT_PREFIX
    if kind == "hull":
        parts = ["hit_splash", "hit_sparks", "hit_flash", "hit_scorch"]
        if CFG[w][mode]["hit"].get("shockwave"):
            parts.append("hit_shockwave")
    elif kind == "struct":
        parts = ["hit_struct", "hit_sparks", "hit_flash"]
    else:
        parts = ["hit_shield", "hit_flash"]
    media = [_ref(P, w, mode, p) for p in parts]
    if kind in ("hull", "shield"):
        media.append(_hit_sound(SOUNDS[w][mode], volume, max_conc))
    elif kind == "struct":
        media.append(_hit_sound(SOUNDS[w][mode], volume * 0.8, max_conc))
    else:
        media.append(_hit_sound(POP_SOUNDS, volume * 0.45, 8))
    if shake and kind == "hull":
        # mesma duracao do tremor dos outros impactos (shots._media)
        media.append(Inh("/BASE_SHAKE", {"ShakeAmount": shake, "Duration": shake_time}))
    return media


# a corona cresce nos primeiros 0,04 s (LerpScaleFrom / LerpTime, campos de Sprite do pd_shot.rules e do
# mine.rules): no quadro em que o raio nasce (cauda ainda escondida pelo StartTime) ela nao vira uma "pilula" gorda
CORONA_LERP_FROM = [0.45, 0.7]
CORONA_LERP_TIME = 0.04

# posicao do nariz (fracao da largura, a partir da esquerda) nas texturas do raio (plasma_tex usa as mesmas)
BOLT_NOSE = 0.8          # bs_plasma_bolt.png (gota do Curupira)
LANCE_NOSE = 0.9         # bs_plasma_lance.png (lanca da Boitata)
CORONA_NOSE = 0.95       # bs_plasma_corona.png
SHADE_NOSE = 0.97        # bs_plasma_shade.png


def _tex_sprite(bucket, wh, color, offset, tex=BLOB, lerp_from=None, lerp_time=None, start=None):
    c = {"Type": "Sprite", "RenderBucket": bucket}
    if start is not None:
        c["StartTime"] = start
    c["Offset"] = [round(offset, 3), 0]
    if lerp_from:
        c["LerpScaleFrom"] = list(lerp_from)
        c["LerpTime"] = lerp_time
    c["Sprite"] = {"Texture": {"File": Q(tex), "MipLevels": "max", "SampleMode": "Linear"},
                   "Size": [round(v, 3) for v in wh]}
    if color is not None:
        c["Sprite"]["VertexColor"] = list(color)
        c["Sprite"]["TargetBlendMode"] = "Add"
    return c


def bolt_components(w, oc):
    """Componentes visuais do raio: sombra escura por baixo (mistura alfa comum), corona ciano (afunilada na
    Boitata, blob no Curupira), nucleo branco-quente (lanca na Boitata, gota no Curupira), cauda animada
    (AnimatedSprite, 8 quadros a 30/s: corpo de serpente na Boitata, esteira reta com aneis no Curupira), luz
    IsLight para o casco e, no overclock e no Curupira, o crepitar eletrico; no Curupira ainda o rastro ionizado.
    Zero particulas no raio normal da Boitata."""
    mode = "OC" if oc else "N"
    b = CFG[w][mode]["bolt"]
    cl, cw = b["core"]
    tl, tw = b["tail"]
    comps = {}
    # cauda: borda direita (cabeca) logo atras da ponta do nucleo. StartTime (visivel so depois de N s,
    # como o ArmedSprite do mine_deployed.rules): no quadro em que o raio nasce na boca a cauda ainda nao aparece,
    # senao ela ficaria por cima da propria torre (Boitata 260 m/s x 0,018 s = 4,7 tiles >= cauda de 4,6 e
    # 312 x 0,018 = 5,6 >= 5,4 no overclock; Curupira 200 m/s x 0,032 s = 6,4 >= 6,2)
    head = 0.08 if w == "gatling" else 0.12
    comps["TailSprite"] = {
        "Type": "AnimatedSprite", "RenderBucket": "BulletUpper3", "StartTime": b["tail_start"],
        "Offset": [round(head - tl / 2, 3), 0],
        "Animation": {"AtlasSprite": {"Texture": {"File": Q(f"{SHOT_PREFIX}{b['tail_tex']}"), "MipLevels": "max",
                                                  "SampleMode": "Linear"},
                                      "Size": [tl, tw], "TargetBlendMode": "Add"},
                      "FrameCount": 8, "FrameSize": [512, 64], "FramesPerRow": 2, "FramesPerSecond": 30}}
    co_l, co_w = b["corona"]
    if b.get("corona_tex"):
        # corona afunilada: o nariz (CORONA_NOSE da textura) fica logo a frente da ponta do nucleo
        co_off, co_tex = head + 0.05 - (CORONA_NOSE - 0.5) * co_l, f"{SHOT_PREFIX}{b['corona_tex']}"
    else:
        co_off, co_tex = -0.22 * co_l, BLOB
    comps["Sprite"] = _tex_sprite("BulletUpper3", (co_l, co_w), b["corona_color"], co_off, co_tex,
                                  CORONA_LERP_FROM, CORONA_LERP_TIME)
    # nucleo: o nariz da textura (BOLT_NOSE / LANCE_NOSE) fica na posicao do projetil + head
    nose = LANCE_NOSE if b.get("core_tex") else BOLT_NOSE
    comps["CoreSprite"] = _tex_sprite("BulletUpper4", (cl, cw), [255, 255, 255], head + 0.02 - (nose - 0.5) * cl,
                                      f"{SHOT_PREFIX}{b.get('core_tex', 'bs_plasma_bolt.png')}")
    if b.get("shade"):
        # sombra por baixo (BulletUpper2, antes das sprites aditivas de BulletUpper3/4) SEM TargetBlendMode: mistura
        # alfa comum, como a Sprite do missile_he.rules / mine.rules. So escurece um pouco o casco claro em volta
        # do raio (o ciano aditivo sumia sobre casco branco). StartTime da cauda: nao escurece a torre no disparo
        sl, sw = b["shade"]
        comps["ShadeSprite"] = _tex_sprite("BulletUpper2", (sl, sw), None, head + 0.1 - (SHADE_NOSE - 0.5) * sl,
                                           f"{SHOT_PREFIX}bs_plasma_shade.png", start=b["tail_start"])
    gl = b["glow"]
    # a luz IsLight tambem so liga depois que o raio saiu da boca (StartTime em Sprite, como o ArmedSprite do
    # mine_deployed.rules): no quadro do disparo o brilho de 5,5x2 (12x6 no Curupira) parado na boca lavava a arte
    # da torre de ciano a cada tiro; a luz do disparo fica so com o muzzle_light (fraco e a frente do cano)
    comps["GlowSprite"] = {"Type": "Sprite", "RenderBucket": "BulletUpper4", "Z": 0, "IsLight": True,
                           "StartTime": b["tail_start"], "Offset": [round(b.get("glow_x", -0.12 * gl[0]), 3), 0],
                           "Sprite": {"Texture": {"File": Q(BLOB), "MipLevels": "max", "SampleMode": "Linear"},
                                      "Size": list(gl), "VertexColor": b["glow_color"], "TargetBlendMode": "Add",
                                      "Shader": Q(f"{D}/common_effects/fancy_light.shader"),
                                      "_z": 1, "_nrmlStrengthLimit": 1, "_litReflectiveStrength": 24,
                                      "_litAdditiveStrength": 0.05, "_unlitAdditiveStrength": 0.2}}
    if CFG[w][mode].get("crackle"):
        comps["Crackle"] = {"Type": "MediaEffects", "Offset": [round(-0.1 * tl, 3), 0],
                            "MediaEffects": [_ref(SHOT_PREFIX, w, mode, "crackle")]}
    if CFG[w][mode].get("trail"):
        comps["Trail"] = {"Type": "MediaEffects", "MediaEffects": [_ref(SHOT_PREFIX, w, mode, "trail")]}
    return comps
