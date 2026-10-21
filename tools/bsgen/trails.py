"""Rastros de particulas proprios dos projeteis do Bullet Strike (R1: projeteis visiveis em voo; 2.0: WP03).

Copias do texto vanilla 0.30.x de shots/bullet_med/particles/bullet_trail_med.rules, bullet_trail_large.rules,
bullet_trail_def.rules e shots/bullet_deck/particles/bullet_trail_deck.rules, com SO estas mudancas:
  * Bucket = BulletTrailUpper (o do bullet_trail_deck): o rastro fica por cima dos tetos, visivel sobre o
    nosso casco e sobre o casco inimigo (BulletTrail esta nos MiddleBuckets, sob o teto);
  * EmitPerSecond menor nos rastros de canhao rapido (orcamento de particulas, ver bs_data.VIS);
  * nos coloridos (AP, SAP, AC) a Def vai inteira no arquivo e muda so _color1/_color2:
    no particle_distort.shader a cor vem do material (col = lerp(_color1, _color2, tex.r)), a cor da particula
    nao tinge o rastro. Caminhos relativos da Def viram ./Data/... (os tres existem no jogo).
Nada de heranca parcial da Def ("Def : <...> { Material : ... }"): nao ha exemplo vanilla e o
bullet_deck_overclock.rules avisa que heranca parcial aninhada pode travar o jogo.

2.0 (WP03): chaves por forma x municao 2.0: med_{he,ap,sap}, large_{he,ap,sap,ac}, deck_{he,ap,sap,ac},
deckL_{he,ap,sap,ac} e deckH_{he,ac} (Boiuna: rastro fino, metade da largura do deck e cores x0,75). HE = ambar
vanilla (med/large pela Def vanilla por referencia; deck = o proprio bullet_trail_deck.rules vanilla, trail_name
devolve None). all_trails() continua chamado sem condicao pelo build_mod (Boitata/Curupira e o caminho sem o
caliber_fx tambem usam estes arquivos).
"""

# Def de shots/bullet_med/particles/bullet_trail_def.rules (@@BS@@ = BaseSize; @@C1@@/@@C2@@ = cores)
DEF_TEXT = """	EmitPerSecond = 0
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
			Enabled = false
			UpdateAfterInit = false
		}
		{
			Type = FpsCompensator
			LocationInOut = location
			VelocityIn
			Mode = Uniform
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ScaleToWorldSpace
			ScaleIn = base_scale
			ScaleOut = base_scale
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = rot
			ValueType = Angle
			FromValue = 84.999985d
			ToValue = 95d
			Name = Rotation
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = RotationToWorldSpace
			RotationIn = rot
			RotationOut = rot
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = SetRandom
			DataOut = rand_color
			ValueType = Color
			FromValue
			{
				Rf = 0
				Gf = 0
				Bf = 0
				Af = 0
			}
			ToValue
			{
				Rf = 0
				Gf = 0
				Bf = 1
				Af = 0
			}
			Name = "random blue (offset)"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = InheritVelocity
			VelocityInOut = velocity
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
	]
	Updaters
	[
		{
			Type = Lifetime
			LifeInOut = life
			Lifetime = 0.2
			Name = Lifetime
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
			DataOut = scale
			Invert = false
			ValueType = Float
			FromValue = 0.3
			ToValue = 0.8
			Name = "scale over life"
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
			Name = "apply base scale"
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
					Rf = 0
					Gf = 0
					Bf = 1
					Af = 1
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 1
				}
			]
			Name = ""
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = ColorRamp
			LerpIn = life
			ColorOut = alpha
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
					Af = 0.5882353
				}
				{
					Rf = 1
					Gf = 1
					Bf = 1
					Af = 0.3137255
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
					Af = 0
				}
			]
			Name = "alpha ramp"
			Enabled = true
			UpdateAfterInit = false
		}
		{
			Type = Operator
			DataType = Color
			AIn = color
			BIn = alpha
			ResultOut = color
			Operator = Multiply
			Name = "apply alpha ramp"
			Enabled = true
			UpdateAfterInit = true
		}
		{
			Type = Operator
			DataType = Color
			AIn = color
			BIn = rand_color
			ResultOut = color
			Operator = Add
			Name = "apply random color"
			Enabled = true
			UpdateAfterInit = true
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
		Type = StandardQuadRenderer
		LocationIn = location
		ScaleIn = scale
		Scale2In
		RotationIn = rot
		ColorIn = color
		UvRectIn
		BaseSize
		{
			X = @@BS@@
			Y = @@BS@@
		}
		Offset
		{
			X = 0
			Y = 0.5
		}
		Name = ""
	}
	Material
	{
		Shader
		{
			File = "./Data/common_effects/particles/particle_distort.shader"
		}
		_distortMultiplier = -0.5
		_erodeMultiplier = 3
		_noiseScale
		{
			X = 0.69
			Y = 0.19
		}
		_scrollSpeed
		{
			X = 0
			Y = -0.7
		}
		_color1
		{
@@C1@@
		}
		_color2
		{
@@C2@@
		}
		_noiseTexture
		{
			File = "./Data/common_effects/particles/noise_voronoi2.png"
			MipLevels = 8
			SampleMode = Linear
			UMode = Wrap
			VMode = Wrap
		}
		Texture
		{
			File = "./Data/shots/bullet_med/particles/bullet_trail_med.png"
			MipLevels = 8
			SampleMode = Linear
		}
		TargetBlendMode = Add
	}
	DeleteMode = Fast
	EnableMultithreading = false
	InitCapacity = 256"""

# EmitterDef de bullet_trail_med.rules / bullet_trail_large.rules / bullet_trail_deck.rules
EMITTER_TEXT = """EmitterDef
{
\tEmitPerSecond = @@EPS@@
\tEmitPerOneShot
\t{
\t\tMin = 0
\t\tMax = 0
\t}
\tPreInitializers
\t[
\t\t{
\t\t\tType = SetRandom
\t\t\tDataOut = base_scale
\t\t\tValueType = Float
\t\t\tFromValue = @@S0@@
\t\t\tToValue = @@S1@@
\t\t\tName = "random scale"
\t\t\tEnabled = true
\t\t\tUpdateAfterInit = false
\t\t}
\t\t{
\t\t\tType = SetValue
\t\t\tDataOut = location
\t\t\tValueType = Vector2
\t\t\tValue
\t\t\t{
\t\t\t\tX = @@LX@@
\t\t\t\tY = 0
\t\t\t}
\t\t\tName = "set location"
\t\t\tEnabled = true
\t\t\tUpdateAfterInit = false
\t\t}
\t\t{
\t\t\tType = SetBulletBarrierID
\t\t\tBarrierIDOut = barrier
\t\t\tName = ""
\t\t\tEnabled = true
\t\t\tUpdateAfterInit = false
\t\t}
\t]
\tPostInitializers[]
}
"""

# resto do arquivo (igual nos tres rastros vanilla, depois do Bucket)
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

# forma de cada rastro vanilla: escala base (min, max), ponto de emissao X, BaseSize da Def
SHAPES = {
    "med": {"scale": (2, 4), "loc_x": 0.5, "base_size": 1},     # bullet_trail_med.rules
    "large": {"scale": (4, 8), "loc_x": 1, "base_size": 1},     # bullet_trail_large.rules
    "deck": {"scale": (4, 8), "loc_x": 1, "base_size": 1.5},    # bullet_trail_deck.rules (Def com BaseSize 1.5)
    # 406 mm (caliber_design item 12): o deck vanilla com escala base 6..12 e emissao 1,5 a frente (rastro maior que
    # o do 155 mm, mesma Def de BaseSize 1,5)
    "deckL": {"scale": (6, 12), "loc_x": 1.5, "base_size": 1.5},
    # Boiuna 2.0 (ADDENDUM G7d, BOIUNA_THIN: puff 0,5 / gain 0,75): o deck com metade da escala (rastro fino de granada,
    # nao 'chama de foguete') e as duas cores do material x0,75
    "deckH": {"scale": (2, 4), "loc_x": 1, "base_size": 1.5, "gain": 0.75},
}

# _color1 / _color2 (X, Y, Z, W) do material. Vanilla (ambar): (1, 0.0745, 0, 1) e (1, 0.727, 0.259, 1)
COLORS = {
    # HE = ambar vanilla escrito por extenso: so para formas sem rastro vanilla pronto (deckL, deckH); med/large HE
    # continuam pela Def vanilla por referencia e o deck HE e o proprio bullet_trail_deck.rules
    "he": ((1, 0.0745, 0, 1), (1, 0.727, 0.259, 1)),
    "ap": ((0.35, 0.5, 1, 1), (0.85, 0.92, 1, 1)),         # branco-azulado do Perfurante (palette.ap)
    "sap": ((1, 0.22, 0.02, 1), (1, 0.6, 0.26, 1)),        # laranja do Semiperfurante (palette.sap)
    "ac": ((0.78, 0.03, 0.12, 1), (1, 0.45, 0.36, 1)),     # carmim profundo da Alta Capacidade (palette.ac, nunca rosa)
}
# nomes antigos e municoes sem cor propria de rastro -> ambar (HE)
COLOR_ALIAS = {"amber": "he", "std": "he", "bullet": "he", "frag": "he"}
# (o plasma do Curupira tem rastro proprio em bsgen/plasma_fx.py)

EPS = {"med": 150, "large": 200, "deck": 300, "deckL": 300, "deckH": 300}
# formas x municoes usadas pelos projeteis 2.0 (Carcara med; Tambor large; Trovao deck; Mapinguari deckL; Boiuna
# deckH) mais as combinacoes do caminho sem o caliber_fx (bs_data.VIS: Mapinguari e Boiuna com 'deck')
USED = {"med": ("he", "ap", "sap"), "large": ("he", "ap", "sap", "ac"), "deck": ("ap", "sap", "ac"),
        "deckL": ("he", "ap", "sap", "ac"), "deckH": ("he", "ac")}
# (forma, cor ou None = Def vanilla por referencia (ambar), particulas/s): um arquivo por combinacao
TRAILS = {}
for _shape, _keys in USED.items():
    for _k in _keys:
        _ref = _k == "he" and _shape in ("med", "large")
        TRAILS[f"bs_trail_{_shape}_{_k}"] = (_shape, None if _ref else _k, EPS[_shape])

# rastro vanilla ja no bucket de cima (sem copia): canhoes de conves com HE
VANILLA_DECK = "./Data/shots/bullet_deck/particles/bullet_trail_deck.rules"
DIR = "shots/bs_trails"


def _num(v):
    return str(int(v)) if float(v) == int(v) else f"{v:g}"


def _color_lines(c):
    return "\n".join(f"\t\t\t{k} = {_num(v)}" for k, v in zip("XYZW", c))


def color_key(color):
    """Municao -> chave de cor de rastro (he/ap/sap/ac; o resto vira ambar = he)."""
    key = COLOR_ALIAS.get(color, color)
    return key if key in COLORS else "he"


def trail_name(shape, color):
    """Nome do arquivo do rastro de uma forma (med/large/deck/deckL/deckH) e municao (he/ap/sap/ac; outra = ambar).
    None = rastro vanilla bullet_trail_deck.rules (deck HE)."""
    key = color_key(color)
    if shape == "deck" and key == "he":
        return None
    name = f"bs_trail_{shape}_{key}"
    if name in TRAILS:
        return name
    raise ValueError(f"rastro sem arquivo: {shape} / {color}")


def trail_text(name):
    shape, color, eps = TRAILS[name]
    sh = SHAPES[shape]
    if color is None:
        # Def vanilla por referencia (mesmo texto do bullet_trail_med/large.rules, caminho absoluto)
        head = "Type = Particles\nDef = &<./Data/shots/bullet_med/particles/bullet_trail_def.rules>\n"
    else:
        g = sh.get("gain", 1)
        c1, c2 = ([round(v * g, 4) for v in c[:3]] + [c[3]] for c in COLORS[color])
        d = DEF_TEXT.replace("@@BS@@", _num(sh["base_size"]))
        d = d.replace("@@C1@@", _color_lines(c1)).replace("@@C2@@", _color_lines(c2))
        head = "Type = Particles\nDef\n{\n" + d + "\n}\n"
    em = (EMITTER_TEXT.replace("@@EPS@@", str(eps)).replace("@@S0@@", _num(sh["scale"][0]))
          .replace("@@S1@@", _num(sh["scale"][1])).replace("@@LX@@", _num(sh["loc_x"])))
    return head + em + "Bucket = BulletTrailUpper\n" + TAIL_TEXT + "\n"


def all_trails():
    """(caminho relativo dentro do mod, texto) de cada rastro proprio."""
    return [(f"{DIR}/{n}.rules", trail_text(n)) for n in TRAILS]
