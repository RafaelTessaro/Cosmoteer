"""Rastros de particulas proprios dos projeteis do Bullet Strike (R1: projeteis visiveis em voo).

Copias do texto vanilla 0.30.x de shots/bullet_med/particles/bullet_trail_med.rules, bullet_trail_large.rules,
bullet_trail_def.rules e shots/bullet_deck/particles/bullet_trail_deck.rules, com SO estas mudancas:
  * Bucket = BulletTrailUpper (o do bullet_trail_deck): o rastro fica por cima dos tetos, visivel sobre o
    nosso casco e sobre o casco inimigo (BulletTrail esta nos MiddleBuckets, sob o teto);
  * EmitPerSecond menor nos rastros de canhao rapido (orcamento de particulas, ver bs_data.VIS);
  * nos coloridos (Perfurante, P.E.M., nuclear) a Def vai inteira no arquivo e muda so _color1/_color2:
    no particle_distort.shader a cor vem do material (col = lerp(_color1, _color2, tex.r)), a cor da particula
    nao tinge o rastro. Caminhos relativos da Def viram ./Data/... (os tres existem no jogo).
Nada de heranca parcial da Def ("Def : <...> { Material : ... }"): nao ha exemplo vanilla e o
bullet_deck_overclock.rules avisa que heranca parcial aninhada pode travar o jogo.
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
}

# _color1 / _color2 (X, Y, Z, W) do material. Vanilla (ambar): (1, 0.0745, 0, 1) e (1, 0.727, 0.259, 1)
COLORS = {
    "ap": ((0.35, 0.5, 1, 1), (0.85, 0.92, 1, 1)),        # branco-azulado do Perfurante
    "emp": ((0.05, 0.3, 1, 1), (0.5, 0.8, 1, 1)),          # azul do P.E.M.
    "nuclear": ((0.3, 1, 0, 1), (0.8, 1, 0.45, 1)),        # verde da Boiuna
}
# (o plasma do Curupira tem rastro proprio em bsgen/plasma_fx.py)

# (forma, cor ou None = ambar vanilla, particulas/s): um arquivo por combinacao usada pelos projeteis
TRAILS = {
    "bs_trail_med_amber": ("med", None, 150),
    "bs_trail_large_amber": ("large", None, 200),
    "bs_trail_large_ap": ("large", "ap", 200),
    "bs_trail_large_emp": ("large", "emp", 200),
    "bs_trail_deck_ap": ("deck", "ap", 300),
    "bs_trail_deck_emp": ("deck", "emp", 300),
    "bs_trail_deck_nuclear": ("deck", "nuclear", 300),
}

# rastro vanilla ja no bucket de cima (sem copia): canhoes de conves de 155/406 mm com Padrao / Perfurante-Explosiva
VANILLA_DECK = "./Data/shots/bullet_deck/particles/bullet_trail_deck.rules"
DIR = "shots/bs_trails"


def _num(v):
    return str(int(v)) if float(v) == int(v) else f"{v:g}"


def _color_lines(c):
    return "\n".join(f"\t\t\t{k} = {_num(v)}" for k, v in zip("XYZW", c))


def trail_name(shape, color):
    """Nome do arquivo do rastro de uma forma (med/large/deck) e cor (ap/emp/nuclear; outra = ambar).
    None = rastro vanilla bullet_trail_deck.rules (deck ambar)."""
    key = color if color in COLORS else "amber"
    name = f"bs_trail_{shape}_{key}"
    if name in TRAILS:
        return name
    if shape == "deck" and key == "amber":
        return None
    raise ValueError(f"rastro sem arquivo: {shape} / {color}")


def trail_text(name):
    shape, color, eps = TRAILS[name]
    sh = SHAPES[shape]
    if color is None:
        # Def vanilla por referencia (mesmo texto do bullet_trail_med/large.rules, caminho absoluto)
        head = "Type = Particles\nDef = &<./Data/shots/bullet_med/particles/bullet_trail_def.rules>\n"
    else:
        c1, c2 = COLORS[color]
        d = DEF_TEXT.replace("@@BS@@", _num(sh["base_size"]))
        d = d.replace("@@C1@@", _color_lines(c1)).replace("@@C2@@", _color_lines(c2))
        head = "Type = Particles\nDef\n{\n" + d + "\n}\n"
    em = (EMITTER_TEXT.replace("@@EPS@@", str(eps)).replace("@@S0@@", _num(sh["scale"][0]))
          .replace("@@S1@@", _num(sh["scale"][1])).replace("@@LX@@", _num(sh["loc_x"])))
    return head + em + "Bucket = BulletTrailUpper\n" + TAIL_TEXT + "\n"


def all_trails():
    """(caminho relativo dentro do mod, texto) de cada rastro proprio."""
    return [(f"{DIR}/{n}.rules", trail_text(n)) for n in TRAILS]
