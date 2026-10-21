#!/usr/bin/env python3
"""Unit tests for rules_lint.py (standard library only).

    python3 tools/rules_lint_test.py            # synthetic tests
    COSMOTEER_DATA=/path/to/Data python3 tools/rules_lint_test.py   # + real vanilla self-test

The synthetic tests build a tiny fake vanilla Data folder and a tiny mod in a
temporary directory, so they do not need the game files.
"""

import contextlib
import io
import os
import shutil
import sys
import tempfile
import textwrap
import unittest

sys.dont_write_bytecode = True   # keep tools/__pycache__ clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules_lint as RL  # noqa: E402


VANILLA = {
    'cosmoteer.rules': '''
        PRIORITIES = &<ships/priorities.rules>
        BASE_SOUNDS = &<common_effects/sounds/base_sounds.rules>
        Ships [ &<ships/terran/terran.rules>/Terran ]
    ''',
    'ships/priorities.rules': 'Weapon_Supply = 5\n',
    'common_effects/sounds/base_sounds.rules': '''
        AudioExterior { Type = Audio; Volume = 1 }
    ''',
    'common_effects/sounds/boom.wav': '',
    'ships/terran/terran.rules': '''
        Terran
        {
            Parts
            [
                &<armor/armor.rules>/Part
            ]
        }
    ''',
    'ships/terran/base_part.rules': '''
        Part
        {
            ID = cosmoteer.base_part
            OVERCLOCK_OPERATIONAL = 7
            ReceivableBuffs [Overclock]
            Components
            {
                Health { Type = Health; Max = 10 }
                Graphics { Type = Sprite; File = "base.png" }
            }
        }
    ''',
    'ships/terran/base.png': '',
    'ships/terran/armor/armor.rules': '''
        Part : <../base_part.rules>/Part
        {
            ID = cosmoteer.armor
            NameKey = "Parts/Armor"
            Components : ^/0/Components
            {
                Extra { Type = X; Value = &~/Part/^/0/OVERCLOCK_OPERATIONAL }
            }
            EditorIcon { Texture { File = "icon.png" } }
        }
    ''',
    'ships/terran/armor/icon.png': '',
    'shots/bullet/bullet.rules': '''
        ID = "cosmoteer.bullet"
        Range = 100
        Components { Physics { Type = CirclePhysics } }
    ''',
    'strings/en.rules': '''
        Parts
        {
            Armor = "Armor"
        }
        Base { A = "a" }
        Derived : Base { B = "b" }
    ''',
}


def write_tree(root, files):
    for rel, text in files.items():
        p = os.path.join(root, rel.replace('/', os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(textwrap.dedent(text))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='rules_lint_test_')
        self.vdir = os.path.join(self.tmp, 'Data')
        write_tree(self.vdir, VANILLA)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_main(self, args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = RL.main(args + ['--vanilla', self.vdir, '--max-issues', '10000'])
        return code, out.getvalue()

    def lint_files(self, files):
        """Write files under <tmp>/loose and lint them; returns (code, output)."""
        d = os.path.join(self.tmp, 'loose')
        write_tree(d, files)
        paths = [os.path.join(d, k) for k in files if k.endswith('.rules')]
        return self.run_main(paths)

    def errors(self, out):
        return [l for l in out.splitlines() if l.strip().startswith('ERROR:')]

    def warnings(self, out):
        return [l for l in out.splitlines() if l.strip().startswith('WARNING:')]


class SyntaxTests(Base):
    def test_valid_constructs(self):
        code, out = self.lint_files({'a.rules': r'''
            // line comment
            /* block
               comment */
            A = 1; B = .5, C = 270d
            D = 50%
            E = 7/64
            F = "str with \"escape\""\
                " continued"
            G = @"C:\verbatim"
            H = [1, 2, 3]
            I { X = 1; Y = "y" }
            J [ { V = 1 } : 0 { V = -(&^/0/V) } ]
            K = (&A) * (&B) + ceil(&C)
            L = "round((&A) * 2, 0)"
            M = db2vol( "&A" )
            Void
            N = & ~/A
            O : I, J/0 { Z = &Y }
            P = { a = 1, b = &a }
            Q = : H [4]
            R : I
            S :
                ~/I,
                ~/O,
            {
            }
            T = &/PRIORITIES/Weapon_Supply
            U : /BASE_SOUNDS/AudioExterior { Volume = 2 }
            W :/BASE_SOUNDS/AudioExterior { }
        '''})
        self.assertEqual(self.errors(out), [], out)

    def test_unclosed_group(self):
        code, out = self.lint_files({'a.rules': 'A\n{\n  B = 1\n'})
        self.assertEqual(code, 1)
        self.assertTrue(any("a.rules:2" in e and "unclosed '{'" in e for e in self.errors(out)), out)

    def test_unterminated_string(self):
        code, out = self.lint_files({'a.rules': 'A = "abc\nB = 1\n'})
        self.assertTrue(any('a.rules:1' in e and 'unterminated string' in e
                            for e in self.errors(out)), out)

    def test_stray_closer(self):
        code, out = self.lint_files({'a.rules': 'A = 1\n}\n'})
        self.assertTrue(any("a.rules:2" in e and "unexpected '}'" in e for e in self.errors(out)), out)

    def test_math_reference_needs_parentheses(self):
        code, out = self.lint_files({'a.rules': 'A = 1\nB = &A * 2\nC = 2 * &A\n'})
        errs = self.errors(out)
        self.assertTrue(any('a.rules:2' in e and 'parentheses' in e for e in errs), out)
        self.assertTrue(any('a.rules:3' in e and 'parentheses' in e for e in errs), out)

    def test_missing_separator(self):
        code, out = self.lint_files({'a.rules': 'A { File = "x.png"  Size = 2 }\n'})
        self.assertTrue(any("after value" in e for e in self.errors(out)), out)


class ReferenceTests(Base):
    def test_sibling_parent_and_list_levels(self):
        code, out = self.lint_files({'a.rules': '''
            Part
            {
                MaxHealth = 10
                Components
                {
                    Turret { Location = [0, 0] }
                    Collider { Location = &../Turret/Location; H = &../../MaxHealth }
                    Crew { Dest [ &../../Turret/Location ] }
                    Mods { BaseValue = 1; Modifiers [ { RemapTo = [&../../../BaseValue] } ] }
                }
            }
        '''})
        self.assertEqual(self.errors(out), [], out)

    def test_list_level_off_by_one_is_reported(self):
        code, out = self.lint_files({'a.rules': '''
            Part
            {
                Components
                {
                    Turret { Location = [0, 0] }
                    Crew { Dest [ &../Turret/Location ] }
                }
            }
        '''})
        self.assertTrue(any('a.rules:7' in e and "&../Turret/Location" in e
                            for e in self.errors(out)), out)

    def test_base_access_and_inherited_children(self):
        code, out = self.lint_files({'a.rules': '''
            Part : <./Data/ships/terran/base_part.rules>/Part
            {
                Components : ^/0/Components
                {
                    Copy = &Health/Max
                    Other = &../Components/Graphics/File
                }
                OC = &~/Part/^/0/OVERCLOCK_OPERATIONAL
                ReceivableBuffs : ^/0/ReceivableBuffs [Engine]
                Bad = &~/Part/^/1/X
            }
        '''})
        errs = self.errors(out)
        self.assertEqual(len(errs), 1, out)
        self.assertIn("'^/1'", errs[0])

    def test_relative_context_is_where_written(self):
        # base.rules refers to its own ~/CONST; derived file has no CONST but
        # inherits the node: still fine (resolved in base.rules)
        code, out = self.lint_files({
            'sub/base.rules': 'CONST = 3\nNode { V = &~/CONST; Pic = "p.png" }\n',
            'sub/p.png': '',
            'derived.rules': 'X : <sub/base.rules>/Node { W = &V }\n',
        })
        self.assertEqual(self.errors(out), [], out)

    def test_dotdot_after_reference_walks_from_target(self):
        code, out = self.lint_files({
            'shot.rules': 'DAMAGE = 5\nBeam { A = 1 }\n',
            'gun.rules': 'OC { BEAM = &<shot.rules>/Beam }\nD = &~/OC/BEAM/../DAMAGE\n',
        })
        self.assertEqual(self.errors(out), [], out)

    def test_unresolved_reports_file_line_path(self):
        code, out = self.lint_files({'a.rules': 'A = 1\n\nB = &Missing/X\nC : NoSuchBase {}\n'
                                                'D = &<nofile.rules>/X\n'})
        errs = self.errors(out)
        self.assertEqual(code, 1)
        self.assertTrue(any('a.rules:3' in e and '&Missing/X' in e for e in errs), out)
        self.assertTrue(any('a.rules:4' in e and 'NoSuchBase' in e for e in errs), out)
        self.assertTrue(any('a.rules:5' in e and 'file not found' in e for e in errs), out)

    def test_list_index_through_inheritance(self):
        code, out = self.lint_files({'a.rules': '''
            L1 [ 1, 2 ]
            L2 : L1 [ 3 ]
            A = &L2/2
            B = &L2/3
        '''})
        errs = self.errors(out)
        self.assertEqual(len(errs), 1, out)
        self.assertIn('&L2/3', errs[0])

    def test_root_alias_and_vanilla_relative_copy(self):
        code, out = self.lint_files({'a.rules': '''
            P = &/PRIORITIES/Weapon_Supply
            Q = &/PRIORITIES/Nope
            Part : <../base_part.rules>/Part {}
        '''})
        errs = self.errors(out)
        self.assertTrue(any('&/PRIORITIES/Nope' in e for e in errs), out)
        self.assertTrue(any('<../base_part.rules>/Part' in e for e in errs), out)
        self.assertFalse(any('Weapon_Supply' in e for e in errs), out)

    def test_case_insensitive_with_warning(self):
        code, out = self.lint_files({'a.rules': 'BASE = 1\nX = &Base\n'})
        self.assertEqual(self.errors(out), [], out)
        self.assertTrue(any('case' in w for w in self.warnings(out)), out)


class AssetTests(Base):
    def test_assets(self):
        code, out = self.lint_files({
            'a.rules': '''
                A { File = "ok.png" }
                B { File = "missing.png" }
                C { Sound = "./Data/common_effects/sounds/boom.wav" }
                D { Sound = "./Data/common_effects/sounds/nope.wav" }
                E { AnimationFiles [ "ok.png", "gone.png" ] }
                F { RandomSounds = ["./Data/common_effects/sounds/boom.wav"] }
                G { File = ok.png }
                H { File = "OK.PNG" }
            ''',
            'ok.png': '',
        })
        errs = self.errors(out)
        self.assertEqual(len(errs), 3, out)
        self.assertTrue(any('missing.png' in e for e in errs))
        self.assertTrue(any('nope.wav' in e for e in errs))
        self.assertTrue(any('gone.png' in e for e in errs))
        self.assertTrue(any('OK.PNG' in w and 'case' in w for w in self.warnings(out)), out)


MOD = {
    'mod.rules': '''
        ID = tester.bs
        Name = "Test"
        CompatibleGameVersions = ["0.30.4"]
        Logo = "logo.png"
        StringsFolder = "strings"
        Actions
        [
            {
                Action = AddMany
                AddTo = "<ships/terran/terran.rules>/Terran/Parts"
                ManyToAdd = &<parts.rules>/Parts
            }
            {
                Action = Add
                AddTo = "<cosmoteer.rules>"
                Name = BS_ALIAS
                ToAdd = &<alias.rules>
            }
            {
                Action = Overrides
                OverrideIn = "<ships/terran/terran.rules>/Terran/NoSuchNode"
                Overrides { X = 1 }
            }
            {
                Action = Replace
                Replace = "<./Data/ships/priorities.rules>/Weapon_Supply"
                With = 6
            }
        ]
    ''',
    'logo.png': '',
    'parts.rules': '''
        Parts
        [
            &<gun/gun.rules>/Part
            &<gun/gun2.rules>/Part
            &<gun/clash.rules>/Part
        ]
    ''',
    'alias.rules': 'Value = 42\n',
    'gun/gun.rules': '''
        Part : <./Data/ships/terran/base_part.rules>/Part
        {
            ID = tester.gun
            NameKey = "Parts/BS_Gun"
            DescriptionKey = "Parts/BS_GunDesc"
            Components : ^/0/Components
            {
                Emitter { Bullet = &<../shots/shell.rules> }
                Emitter2 { Bullet = &<../shots/vanilla_clash.rules> }
                Uses = &/BS_ALIAS/Value
            }
            EditorIcon { Texture { File = "icon.png" } }
        }
    ''',
    'gun/icon.png': '',
    'gun/gun2.rules': '''
        Part : <./Data/ships/terran/base_part.rules>/Part
        {
            ID = tester.gun
            NameKey = "Parts/Armor"
            Components : ^/0/Components { Emitter { Bullet = &<../shots/shell2.rules> } }
        }
    ''',
    'gun/clash.rules': '''
        Part : <./Data/ships/terran/base_part.rules>/Part
        {
            ID = cosmoteer.armor
            NameKey = "Derived/A"
        }
    ''',
    'shots/shell.rules': 'ID = "tester.shell"\nRange = 10\n',
    'shots/shell2.rules': 'ID = "tester.shell"\nRange = 20\n',
    'shots/vanilla_clash.rules': 'ID = "cosmoteer.bullet"\n',
    'orphan.rules': 'X = &Nope\n',
    'strings/en.rules': '''
        Parts
        {
            BS_Gun = "Gun"
            BS_Only_En = "x"
        }
    ''',
    'strings/pt-br.rules': '''
        Parts
        {
            BS_Gun = "Arma"
        }
    ''',
}


class ModTests(Base):
    def setUp(self):
        Base.setUp(self)
        self.mdir = os.path.join(self.tmp, 'BulletStrike')
        write_tree(self.mdir, MOD)

    def test_mod_mode(self):
        code, out = self.run_main(['--mod', self.mdir])
        errs = self.errors(out)
        warns = self.warnings(out)
        self.assertEqual(code, 1)
        # bad action target
        self.assertTrue(any('mod.rules' in e and 'NoSuchNode' in e for e in errs), out)
        # alias added to cosmoteer.rules by an action is visible to mod files
        self.assertFalse(any('BS_ALIAS' in e for e in errs), out)
        # missing string key (DescriptionKey) but NameKey present; vanilla keys and
        # inherited vanilla string groups resolve
        self.assertTrue(any('Parts/BS_GunDesc' in e for e in errs), out)
        self.assertFalse(any('"Parts/BS_Gun"' in e for e in errs), out)
        self.assertFalse(any('Parts/Armor' in e or 'Derived/A' in e for e in errs), out)
        # duplicate part ID + clash with vanilla
        self.assertTrue(any("duplicate part ID 'tester.gun'" in e for e in errs), out)
        self.assertTrue(any("clashes with vanilla part" in e for e in errs), out)
        # duplicate shot ID + vanilla shot clash
        self.assertTrue(any("duplicate shot ID 'tester.shell'" in e for e in errs), out)
        self.assertTrue(any("shot ID 'cosmoteer.bullet' clashes" in e for e in errs), out)
        # pt-br missing key
        self.assertTrue(any('BS_Only_En' in w and 'pt-br' in w for w in warns), out)
        # unreachable file: downgraded to warning
        self.assertTrue(any('orphan.rules' in w and '[unreachable]' in w for w in warns), out)
        self.assertFalse(any('orphan.rules' in e for e in errs), out)

    def test_missing_strings_folder(self):
        shutil.rmtree(os.path.join(self.mdir, 'strings'))
        code, out = self.run_main(['--mod', self.mdir])
        self.assertTrue(any('StringsFolder' in e for e in self.errors(out)), out)


class SchemaCheckTests(unittest.TestCase):
    """schema_check.SAME_TYPE: a field proven in HitOperational is accepted in the hit groups the game
    itself aliases to it (missile_he l.125, bullet_deck l.152, ion_beam_overclock l.64), and nowhere else."""

    CORPUS = {
        'shots/msl/msl.rules': '''
            Components
            {
                Hit
                {
                    Type = SimpleHit
                    HitOperational { MediaEffectsScale = 1; MediaEffects [] }
                }
                Pen
                {
                    Type = PenetratingHit
                    HitOperational { MediaEffectsScale = 1; MediaEffects [] }
                    FinishedPenetratingOperational { ReduceEffectsByPenetration = true }
                }
                Other
                {
                    Type = Sprite
                    Inner { Size = 1 }
                }
            }
        ''',
        'shots/beam/beam.rules': '''
            HitOperational { MediaEffectsScale = 1 }
            HitNothing { MediaEffects [] }
        ''',
    }
    MOD = {
        'shots/a/a.rules': '''
            Components
            {
                Hit
                {
                    Type = SimpleHit
                    HitShield { MediaEffectsScale = 0.5 }
                    HitFriendly { MediaEffectsScale = 0.5; MediaEffectScale = 0.5 }
                }
                Pen
                {
                    Type = PenetratingHit
                    FinishedPenetratingOperational { MediaEffectsScale = 0.5; MediaEffects [] }
                }
                Other
                {
                    Type = Sprite
                    Inner { MediaEffectsScale = 0.5 }
                }
            }
        ''',
        'shots/b/b.rules': '''
            HitNothing { MediaEffectsScale = 0.5 }
            HitAttenuator { MediaEffectsScale = 0.5 }
        ''',
    }

    def test_same_type_hit_groups(self):
        import schema_check as SC
        tmp = tempfile.mkdtemp(prefix='schema_check_test_')
        try:
            write_tree(os.path.join(tmp, 'Data'), self.CORPUS)
            write_tree(os.path.join(tmp, 'mod'), self.MOD)
            out = io.StringIO()
            argv = sys.argv
            sys.argv = ['schema_check.py', '--mod', os.path.join(tmp, 'mod'), '--vanilla', os.path.join(tmp, 'Data'),
                        '--cache', os.path.join(tmp, 'cache')]
            try:
                with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
                    SC.main()
            finally:
                sys.argv = argv
            text = out.getvalue()
            lines = [l for l in text.splitlines() if ': ' in l and not l.startswith('schema_check:')]
            # aceitos pelo alias (mesmo tipo HitRules no jogo)
            self.assertFalse(any("'MediaEffectsScale'" in l and 'hitshield' in l for l in lines), text)
            self.assertFalse(any("'MediaEffectsScale'" in l and 'hitfriendly' in l for l in lines), text)
            self.assertFalse(any('finishedpenetratingoperational' in l for l in lines), text)
            self.assertFalse(any('R:hitnothing' in l for l in lines), text)
            # erros reais continuam aparecendo: erro de digitacao, contexto sem alias, grupo de outro tipo
            self.assertTrue(any("'MediaEffectScale'" in l and 'hitfriendly' in l for l in lines), text)
            self.assertTrue(any("'MediaEffectsScale'" in l and 'N:Sprite/inner' in l for l in lines), text)
            self.assertEqual(SC.known_fields({}, 'N:SimpleHit/hitshield'), None)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- 2.0 (WP01): checagens de sentido
VANILLA_20 = {
    'buffs/buffs.rules': '''
        Factory { CombineMode = Add }
        Overclock {}
    ''',
    'gui/game/parts/part_toggles.rules': '''
        PartToggles
        [
            { ToggleID = "on_off"; Style = Popout }
        ]
    ''',
}

MOD_20 = {
    'mod.rules': '''
        ID = tester.mod20
        Name = "Mod 20"
        CompatibleGameVersions = ["0.30.4"]
        StringsFolder = "strings"
        Actions
        [
            { Action = Overrides; OverrideIn = "<./Data/buffs/buffs.rules>"; Overrides = &<buffs/my_buffs.rules> }
            { Action = AddMany; AddTo = "<ships/terran/terran.rules>/Terran/Parts"; ManyToAdd [ &<parts/a.rules>/Part, &<parts/b.rules>/Part ] }
            { Action = AddMany; AddTo = "<gui/game/parts/part_toggles.rules>/PartToggles"; ManyToAdd = &<gui/toggles.rules>/PartToggles }
        ]
    ''',
    'strings/en.rules': 'Parts { A = "a" }\n',
    'strings/pt-br.rules': 'Parts { A = "a" }\n',
    'buffs/my_buffs.rules': 'MyLink { CombineMode = Max }\n',
    'gui/toggles.rules': '''
        PartToggles
        [
            { ToggleID = "my_ammo"; Style = Popout }
        ]
    ''',
    'parts/a.rules': '''
        Part
        {
            ID = tester.a
            TypeCategories = [cat_a]
            ReceivableBuffs = [MyLink, Factory, NoSuchBuff]
            Components
            {
                Estoque_he { Type = ResourceStorage; MaxResources = 10 }
                Feed { Type = ResourceConverter; FromQuantity = 1; ToQuantity = 1; Amount = 2.5 }
                Grid { Type = GridBuffProvider; BuffType = MyLink; BuffAmount = 0.5; GridDistance = 12.5 }
                Bad { Type = GridBuffProvider; BuffType = Typo_Buff; BuffAmount = 1 }
                Sel { Type = UIToggle; ToggleID = "my_ammo" }
                SelBad { Type = UIToggle; ToggleID = "bs_cell_type" }
                Sub { Type = MultiToggle; Toggles = [ { Toggle = { ID=Timer; ToggleID="IsRunning"; } } ] }
                Via
                {
                    Type = MultiResourceStorage
                    ViaBuffs { OutgoingBuffProviders = [Grid]; ComponentIDs = [Estoque_he, Estoque_hee] }
                }
                Area { Type = AreaBuffProvider; BuffType = MyLink; Criteria { Category = cat_b } }
                AreaBad { Type = AreaBuffProvider; BuffType = MyLink; Criteria { Category = cat_typo } }
                Port1 { Type = NetworkPort; Types = [ tester.solo ] }
                Port2 { Type = NetworkPort; Types = [ tester.pair ] }
            }
        }
    ''',
    'parts/b.rules': '''
        Part
        {
            ID = tester.b
            TypeCategories = [cat_b]
            Components
            {
                Port { Type = NetworkPort; Types = [ tester.pair ] }
                Prox { Type = ResourceStorageProxy; PartCriteria { Category = cat_a } }
            }
        }
    ''',
}


class Semantics20Tests(Base):
    """WP01: BuffType definido, Category existente, ViaBuffs.ComponentIDs, ToggleID, NetworkPort >= 2 pecas e
    campos inteiros novos (Amount, GridDistance; BuffAmount fica livre)."""

    def setUp(self):
        Base.setUp(self)
        write_tree(self.vdir, VANILLA_20)
        self.mdir = os.path.join(self.tmp, 'Mod20')
        write_tree(self.mdir, MOD_20)

    def test_semantic_checks(self):
        code, out = self.run_main(['--mod', self.mdir])
        errs = self.errors(out)
        self.assertEqual(code, 1, out)
        # buffs: vanilla (Factory) e Overrides do mod (MyLink) valem; os outros nao
        self.assertTrue(any("BuffType 'NoSuchBuff'" in e for e in errs), out)
        self.assertTrue(any("BuffType 'Typo_Buff'" in e for e in errs), out)
        self.assertFalse(any("'MyLink'" in e or "'Factory'" in e for e in errs), out)
        # categorias
        self.assertTrue(any("Category 'cat_typo'" in e for e in errs), out)
        self.assertFalse(any("'cat_a'" in e or "'cat_b'" in e for e in errs), out)
        # ViaBuffs: erro de digitacao no nome do componente
        self.assertTrue(any("'Estoque_hee'" in e for e in errs), out)
        self.assertFalse(any("'Estoque_he'" in e for e in errs), out)
        # ToggleID inexistente (a F3 sem bs_cell_type); sub-toggle de componente nao conta
        self.assertTrue(any("ToggleID 'bs_cell_type'" in e for e in errs), out)
        self.assertFalse(any("'my_ammo'" in e or "IsRunning" in e for e in errs), out)
        # NetworkPort: tipo do mod numa peca so
        self.assertTrue(any("'tester.solo'" in e for e in errs), out)
        self.assertFalse(any("'tester.pair'" in e for e in errs), out)
        # inteiros novos: Amount e GridDistance; BuffAmount fracionario e permitido (vanilla usa 25 %, 0.5...)
        self.assertTrue(any("'Amount'" in e and '2.5' in e for e in errs), out)
        self.assertTrue(any("'GridDistance'" in e and '12.5' in e for e in errs), out)
        self.assertFalse(any("'BuffAmount'" in e for e in errs), out)


REAL = os.environ.get('COSMOTEER_DATA') or RL.DEFAULT_VANILLA


@unittest.skipUnless(os.path.isfile(os.path.join(REAL, 'cosmoteer.rules')),
                     'real vanilla Data folder not available')
class RealVanillaTests(unittest.TestCase):
    def test_selftest_is_clean(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            RL.main(['--vanilla-selftest', REAL, '--max-issues', '100'])
        text = out.getvalue()
        errs = [l for l in text.splitlines() if l.strip().startswith('ERROR:')]
        # 4 genuine (harmless, never-read) vanilla bugs are known in 0.30.5 RC4
        self.assertLessEqual(len(errs), 4, text)
        self.assertNotIn('[syntax] unclosed', text)


if __name__ == '__main__':
    unittest.main()
