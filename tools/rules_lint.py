#!/usr/bin/env python3
"""rules_lint.py - static validator ("linter") for Cosmoteer .rules files.

Standard library only (Python 3.8+). Never executes anything from the data it
reads; vanilla files that are not checked out are read with `git cat-file`.

README
======

Usage
-----
    # Lint a mod (start at <mod>/mod.rules, follow every Action, then lint
    # every other .rules file under the mod folder):
    python3 tools/rules_lint.py --mod BulletStrike --vanilla /path/to/Data

    # Lint loose files (./Data/ and &/ROOT paths resolve against --vanilla):
    python3 tools/rules_lint.py --vanilla /path/to/Data some/file.rules ...

    # Self-test: lint every vanilla .rules file (also the ones that are only
    # in the git history of a sparse checkout):
    python3 tools/rules_lint.py --vanilla-selftest /path/to/Data

    Options: --no-warnings, --max-issues N, --git-ref REF (vanilla commit used
    for the file listing / not-checked-out files; default origin/main-unstable
    if it exists, else HEAD), --langs pt-br,de (languages compared with
    en.rules, default pt-br), --strict-unreachable (keep errors of mod files
    that mod.rules never reaches as errors instead of warnings),
    --show-case (also list case-only mismatches in vanilla self-test).

Exit code: 1 if any ERROR was reported, else 0.

The `--vanilla` folder is the game's Data folder (`./Data/` maps to it and
`/` is `<it>/cosmoteer.rules`). If it is a git checkout (e.g. the sparse
Rojamahorse/CosmoteerUpdates mirror), `git ls-tree -r --name-only <ref>` is
used as the list of existing vanilla files, so PNG/WAV references are checked
even though binaries are not checked out.

What is checked
---------------
1. Syntax: `//` and `/* */` comments; `Name = value`, `Name { }`,
   `Name [ ]`, `Name = { }` / `= [ ]` / `= : Base [ ]`, `Name : B1, B2 { }`
   (bases with or without `&`, `Name :/ROOT/X`, bases on following lines,
   trailing comma before the body), inherit-only nodes (`A : B`, no body),
   unnamed list elements (`{}`, `[]`, `: base {}`, `: 0 {}`), void fields
   (bare name), quoted strings with escapes, `"..."\\` + newline
   continuation, `@"verbatim"` strings. Like the game, a value runs to the end
   of the line or to `,` / `;` / `}` / `]` - parentheses do not protect
   commas (vanilla quotes such math: `"round((&X) * 2, 0)"`), and quoted and
   unquoted pieces concatenate (`db2vol( "&~/X" )`). Reports unclosed
   brackets (with an indentation-based "probable culprit" hint), unterminated
   strings/comments, stray tokens, missing separators, duplicate field names
   (WARNING: vanilla never has them).
2. References: every `&path` (whole value, list element, `(&path)` inside
   math, also inside quoted math strings) and every inheritance base must
   resolve. Supported: `<file>` / `<file>/path` (relative to the file the
   text is written in; `./Data/...` = vanilla), `~/` (root of the current
   file), `/` (root of Data/cosmoteer.rules), `^/N/` (N-th base of the
   current node), `..` (parent; inside a list the list itself is a level;
   after stepping through a reference, `..` walks from the referenced node, as
   vanilla's `&~/OVERCLOCK/BEAM/../DAMAGE` requires), `.`, numeric list
   indices, child/sibling names (looked up only in the node containing the
   field - no search of ancestors), `& path` with a space, and `:` (virtual /
   most-derived: treated as "current node", a miss is only a WARNING).
   Children of bases are visible through derived nodes (multiple inheritance,
   first base wins; list inheritance = base elements first). Resolution always
   starts where the text is physically written (an inherited node keeps its
   original file/node context, as the game does). Node-name lookups are
   case-insensitive like the game (vanilla relies on it, e.g. `&Base` vs
   `BASE`); case-only mismatches are WARNINGs. ERRORs also for a `&` in math
   that is not wrapped in parentheses and for a stray `&` operator;
   `X = <file>/Path` without `&` is a WARNING.
3. Assets: string (or unquoted word) values of `File`, `NormalsFile`,
   `Sound`, `Logo`, `Texture`, `Shader`, `Font`, entries of `AnimationFiles`,
   `NormalsAnimationFiles`, `RandomSounds`, `Sounds`, `Files`, and any quoted
   string ending in .png/.wav/.ogg/.shader/.jpg/.ttf/.mp3/.ship must exist
   (relative to the file containing the string, or `./Data/...`). Files
   tracked by git but not checked out (sparse checkouts of vanilla or of the
   mod) count as existing. File-name case mismatches are WARNINGs (fine on
   Windows only).
4. Mod mode: parses `mod.rules`; checks ID/Name/CompatibleGameVersions, Logo
   and StringsFolder; for each Action checks the target path
   (AddTo/OverrideIn/Replace/Remove/RemoveMany/AddBaseTo, relative to Data/)
   resolves in vanilla (respecting IgnoreIfNotExisting / CreateIfNotExisting)
   and has the right node kind, then *applies* the action in memory
   (Add/AddMany/Overrides/Replace/Remove/AddBase) so later actions and mod
   files can see nodes added by earlier ones (e.g. new `/MY_ALIAS` roots).
   Value fields (ToAdd/ManyToAdd/With/Overrides/BaseToAdd) are linted as part
   of mod.rules, and every mod file they reach is linted recursively; then all
   remaining .rules files under the mod folder are linted (issues there are
   downgraded to WARNINGs tagged "[unreachable]", because the game never
   loads them; --strict-unreachable keeps them as errors).
   String keys (NameKey, IconNameKey, DescriptionKey, PluralNameKey,
   TitleKey, ButtonToolTipKey, ToolTipKey/TooltipKey, LongNameKey,
   SingularKey, PluralKey) written as literal strings in mod files must exist
   in <StringsFolder>/en.rules or vanilla strings/en.rules (ERROR; nested
   groups and group inheritance are followed); keys of the mod en.rules
   missing from pt-br.rules (or --langs) are WARNINGs.
   Duplicate part IDs (`ID` of `Part` nodes in reachable mod files, and the
   effective ID of every part added to a `.../Parts` list, also against the
   vanilla Terran parts) and duplicate shot IDs (roots of files under a
   `shots/` folder, `Bullet`/`Shot` nodes, targets of `Bullet = &...`, also
   against vanilla shots) are ERRORs; a registered part/bullet that changes
   its base but inherits the base's ID is flagged too.

5. Bullet Strike 2.0 (mod mode, WP01), on the files mod.rules reaches:
   every BuffType / ReceivableBuffs / IncomingBuffTypes name is defined in
   vanilla buffs/buffs.rules or by the mod's Overrides of it; every Category
   of a PartCriteria / Criteria exists in the TypeCategories of some mod or
   vanilla part; every ViaBuffs.ComponentIDs name is a component of some mod
   (or vanilla) part (catches typos in the teleport chain); every UIToggle
   ToggleID and ToggleChoicesUnlocked toggle exists in PartToggles of the mod
   or vanilla (`{ ID = X; ToggleID = "IsRunning" }` sub-toggles excluded);
   every namespaced NetworkPort type (with a '.') is used by >= 2 mod parts.
   Integer fields also include Amount, ResourcesUsed, Crew, Quantity and
   GridDistance (never BuffAmount: vanilla uses 25 %, 0.5...).

Important semantic note
-----------------------
The game resolves references lazily: a broken reference inside a field the
game never reads does not crash (vanilla ships 4 such latent bugs, SW:ACD
dozens). The linter reports every broken reference anyway, because in new
code the same mistake usually sits in a field that *is* read.

Known limitations
-----------------
* Values are not type-checked (no knowledge of component schemas, required
  fields, enum names or math validity beyond reference extraction).
* `:` virtual (most-derived) paths are resolved as if `:` were the current
  node; if that fails it is reported as a WARNING only. Void fields that
  remove an inherited component (0.30.2+) still count as existing nodes.
* Mod actions are applied in a simplified way (Remove/RemoveMany only hide
  named children; list-index Remove/Replace are checked but not applied).
  Only mod.rules is used as manifest (mod_*.rules variants are linted as
  ordinary files). References to other mods cannot be checked.
* `./` paths that do not start with `./Data/` cannot be checked (WARNING).
* Unquoted words are asset-checked only for the asset keys above (vanilla
  particle `Filename = SmoothFalloffRamp.png` / planet `DecalFiles` names are
  resolved by the engine elsewhere).
* Vanilla files are only linted in --vanilla-selftest; in mod mode they are
  loaded for lookups only.

Vanilla self-test (0.30.5 RC4 mirror, origin/main-unstable, 2026-10-17)
-----------------------------------------------------------------------
939 .rules files (744 checked out + 195 read from git) parsed with 0 syntax
errors; references 9748/9749 resolved, inheritance bases 5802/5803, assets
15927/15928 (29 case-only mismatches, e.g. `&Base` -> `BASE`). The 4
remaining errors are genuine latent vanilla bugs in never-read fields, not
linter false positives:
  ships/terran/terran.rules:703       base `<../base_ship.rules>/Fire` (no Fire)
  shots/resonance_beam/resonance_beam.rules:184  `&^/0/Scale` (base modifier
                                      #2 has no Scale)
  shots/resonance_beam/resonance_beam.rules:482  `File = ../../fire/particles/
                                      fire_ramp.png` (lives in statuses/fire/)
  statuses/fire/fire.rules:26         `(&SCORCH_PER_SECOND) & (&TickInterval)`
                                      (`&` typed instead of `*`)
Runtime: ~6 s for vanilla, ~16 s for SW:ACD (4643 files) on one core.
"""

import argparse
import os
import posixpath
import re
import subprocess
import sys

sys.setrecursionlimit(20000)

ERROR = 'ERROR'
WARNING = 'WARNING'

ASSET_EXTS = ('.png', '.wav', '.ogg', '.shader', '.jpg', '.jpeg', '.ttf',
              '.otf', '.mp3', '.ship', '.dds', '.bmp')
ASSET_KEYS = {'file', 'normalsfile', 'sound', 'logo', 'texture', 'shader',
              'font', 'normalsmap', 'image'}
ASSET_LIST_KEYS = {'animationfiles', 'normalsanimationfiles', 'randomsounds',
                   'sounds', 'files'}
STRING_KEY_FIELDS = {'namekey', 'iconnamekey', 'descriptionkey',
                     'pluralnamekey', 'titlekey', 'buttontooltipkey',
                     'tooltipkey', 'longnamekey', 'singularkey', 'pluralkey'}
ACTION_TARGET_FIELDS = {
    'add': ('addto', 'toadd'),
    'addmany': ('addto', 'manytoadd'),
    'overrides': ('overridein', 'overrides'),
    'replace': ('replace', 'with'),
    'remove': ('remove', None),
    'removemany': ('removemany', None),
    'addbase': ('addbaseto', 'basetoadd'),
}


# Campos que o jogo le como inteiro (Int32 / ModifiableInt): um literal fracionario derruba o carregamento
# ("evaluated to 7666,667 which is not compatible with the desired type 'Int32'"). Para os ModifiableInt o valor
# pode vir num bloco { BaseValue = ... }.
INT_FIELDS = {'totaldamage', 'maxhealth', 'maxresources', 'maxstacksize', 'toquantity', 'fromquantity',
              'togglequantity', 'toggleonresources', 'toggleoffresources', 'resupplythreshold', 'commandpoints',
              'crewrequired', 'expandstartradius',
              # 2.0 (WP01): conversores, estoques, emissores, tripulacao e alcance da grade de buffs. NUNCA BuffAmount:
              # o vanilla usa 25 %, 50 %, 1 e {BaseValue ...} (J2R3-21)
              'amount', 'resourcesused', 'crew', 'quantity', 'griddistance'}
_FRACTION_RE = re.compile(r'^-?\d*\.\d*[1-9]\d*$')


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class Issue(object):
    __slots__ = ('sev', 'display', 'line', 'cat', 'msg')

    def __init__(self, sev, display, line, cat, msg):
        self.sev, self.display, self.line, self.cat, self.msg = \
            sev, display, line, cat, msg

    def format(self):
        loc = self.display
        if self.line:
            loc += ':%d' % self.line
        return '%s: %s: [%s] %s' % (self.sev, loc, self.cat, self.msg)


class Report(object):
    def __init__(self):
        self.issues = []
        self._seen = set()
        self.strict_unreachable = False

    def add(self, sev, rfile, line, cat, msg):
        display = rfile.display if rfile is not None else '<mod>'
        if rfile is not None and rfile.unreachable and not self.strict_unreachable:
            if sev == ERROR:
                sev = WARNING
            msg += ' [unreachable]'
        key = (sev, display, line, cat, msg)
        if key in self._seen:
            return
        self._seen.add(key)
        self.issues.append(Issue(sev, display, line, cat, msg))

    def count(self, sev):
        return sum(1 for i in self.issues if i.sev == sev)


# ---------------------------------------------------------------------------
# Files / virtual file system
# ---------------------------------------------------------------------------

class RFile(object):
    """A parsed .rules file. origin is 'vanilla' (path = Data-relative posix
    path) or 'fs' (path = absolute OS path)."""
    __slots__ = ('origin', 'path', 'display', 'root', 'lint', 'unreachable',
                 'linted', 'parse_ok')

    def __init__(self, origin, path, display):
        self.origin = origin
        self.path = path
        self.display = display
        self.root = None
        self.lint = False
        self.unreachable = False
        self.linted = False
        self.parse_ok = True


class Loc(object):
    """Result of resolving a file path."""
    __slots__ = ('origin', 'path', 'case_ok', 'is_dir')

    def __init__(self, origin, path, case_ok=True, is_dir=False):
        self.origin, self.path, self.case_ok, self.is_dir = \
            origin, path, case_ok, is_dir


class VFS(object):
    def __init__(self, vanilla_dir, git_ref=None):
        self.vdir = os.path.abspath(vanilla_dir) if vanilla_dir else None
        self.vfiles = {}      # lower rel -> actual rel
        self.vdirs = {}       # lower rel dir -> actual
        self.git_ref = None
        self._git = None
        self._git_cache = {}
        self._ls_cache = {}
        self.git_fs = {}      # lower abs path -> actual abs path (git-tracked, maybe not on disk)
        self.git_fs_dirs = {}
        if not self.vdir:
            return
        names = []
        if os.path.isdir(os.path.join(self.vdir, '.git')) or \
                os.path.isfile(os.path.join(self.vdir, '.git')):
            ref = git_ref
            if ref is None:
                for cand in ('origin/main-unstable', 'HEAD'):
                    if self._git_ok(['rev-parse', '--verify', '-q', cand + '^{commit}']):
                        ref = cand
                        break
            if ref:
                try:
                    out = subprocess.run(
                        ['git', '-C', self.vdir, 'ls-tree', '-r', '--name-only',
                         '-z', ref], stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, check=True).stdout
                    names = [n for n in out.decode('utf-8', 'replace').split('\0') if n]
                    self.git_ref = ref
                except (OSError, subprocess.CalledProcessError):
                    names = []
        # Files present on disk count too (non-git folder or untracked files).
        for dirpath, dirnames, filenames in os.walk(self.vdir):
            if '.git' in dirnames:
                dirnames.remove('.git')
            rel_dir = os.path.relpath(dirpath, self.vdir).replace(os.sep, '/')
            for fn in filenames:
                names.append(fn if rel_dir == '.' else rel_dir + '/' + fn)
        for n in names:
            self.vfiles.setdefault(n.lower(), n)
            parts = n.split('/')
            for i in range(1, len(parts)):
                d = '/'.join(parts[:i])
                self.vdirs.setdefault(d.lower(), d)
        self.vdirs[''] = ''

    def _git_ok(self, args):
        try:
            return subprocess.run(['git', '-C', self.vdir] + args,
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL).returncode == 0
        except OSError:
            return False

    def vanilla_lookup(self, rel):
        if self.vdir is None:
            return None
        rel = posixpath.normpath(rel) if rel else ''
        if rel == '.':
            rel = ''
        if rel.startswith('../') or rel == '..' or rel.startswith('/'):
            return None
        low = rel.lower()
        act = self.vfiles.get(low)
        if act is not None:
            return Loc('vanilla', act, act == rel)
        act = self.vdirs.get(low)
        if act is not None:
            return Loc('vanilla', act, act == rel, True)
        return None

    def vanilla_read(self, rel):
        p = os.path.join(self.vdir, rel)
        if os.path.isfile(p):
            with open(p, 'rb') as f:
                return f.read()
        if self.git_ref is None:
            return None
        if rel in self._git_cache:
            return self._git_cache[rel]
        data = self._git_cat(rel)
        self._git_cache[rel] = data
        return data

    def _git_cat(self, rel):
        try:
            if self._git is None:
                self._git = subprocess.Popen(
                    ['git', '-C', self.vdir, 'cat-file', '--batch'],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL)
            self._git.stdin.write(('%s:%s\n' % (self.git_ref, rel)).encode('utf-8'))
            self._git.stdin.flush()
            header = self._git.stdout.readline().decode('utf-8', 'replace').split()
            if len(header) < 3 or header[1] == 'missing':
                return None
            size = int(header[2])
            data = self._git.stdout.read(size)
            self._git.stdout.read(1)
            if header[1] != 'blob':
                return None
            return data
        except (OSError, ValueError):
            return None

    def close(self):
        if self._git is not None:
            try:
                self._git.stdin.close()
                self._git.wait(timeout=5)
            except Exception:
                pass
            self._git = None

    def add_git_worktree(self, d):
        """Treat files tracked by git under d (e.g. a sparse checkout without
        binaries) as existing."""
        try:
            out = subprocess.run(['git', '-C', d, 'ls-files', '-z', '--full-name'],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 check=True).stdout
            top = subprocess.run(['git', '-C', d, 'rev-parse', '--show-toplevel'],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 check=True).stdout.decode('utf-8').strip()
        except (OSError, subprocess.CalledProcessError):
            return 0
        n = 0
        for rel in out.decode('utf-8', 'replace').split('\0'):
            if not rel:
                continue
            ap = os.path.normpath(os.path.join(top, rel.replace('/', os.sep)))
            self.git_fs.setdefault(ap.lower(), ap)
            dp = os.path.dirname(ap)
            while dp and dp.lower() not in self.git_fs_dirs:
                self.git_fs_dirs[dp.lower()] = dp
                nd = os.path.dirname(dp)
                if nd == dp:
                    break
                dp = nd
            n += 1
        return n

    def _listdir_lower(self, d):
        r = self._ls_cache.get(d)
        if r is None:
            try:
                r = {}
                for n in os.listdir(d):
                    r.setdefault(n.lower(), n)
            except OSError:
                r = {}
            self._ls_cache[d] = r
        return r

    def fs_lookup(self, path):
        path = os.path.normpath(path)
        if os.path.exists(path):
            # exact-case check (os.path.exists is case-insensitive on Windows/macOS)
            return Loc('fs', path, self._fs_exact(path), os.path.isdir(path))
        # git-tracked but not checked out (sparse checkout)
        if self.git_fs:
            low = path.lower()
            act = self.git_fs.get(low)
            if act is not None:
                return Loc('fs', act, act == path, False)
            act = self.git_fs_dirs.get(low)
            if act is not None:
                return Loc('fs', act, act == path, True)
        # case-insensitive walk
        drive, rest = os.path.splitdrive(path)
        parts = [p for p in rest.split(os.sep) if p]
        cur = drive + os.sep
        for part in parts:
            m = self._listdir_lower(cur).get(part.lower())
            if m is None:
                return None
            cur = os.path.join(cur, m)
        return Loc('fs', cur, False, os.path.isdir(cur))

    def _fs_exact(self, path):
        drive, rest = os.path.splitdrive(path)
        parts = [p for p in rest.split(os.sep) if p]
        cur = drive + os.sep
        for part in parts:
            names = self._listdir_lower(cur)
            if part not in names.values():
                return part.lower() not in names
            cur = os.path.join(cur, part)
        return True


# ---------------------------------------------------------------------------
# Tokenizer / parser
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile('|'.join([
    r'(?P<nl>\n)',
    r'(?P<ws>[ \t\r\f\v﻿]+)',
    r'(?P<lc>\\[ \t\r]*\n)',
    r'(?P<lcom>//[^\n]*)',
    r'(?P<bcom>/\*[\s\S]*?\*/)',
    r'(?P<badcom>/\*[\s\S]*)',
    r'(?P<vstr>@"(?:[^"]|"")*")',
    r'(?P<str>"(?:[^"\\\n]|\\[\s\S])*")',
    r'(?P<badstr>"[^\n]*)',
    r'(?P<punct>[{}\[\]=,;])',
    r'(?P<colon>:)',
    # a word never starts with ':' (`Name :/ROOT/X` is inheritance), but
    # ':/' may appear inside a path (`&../:/v_Foo`, virtual inheritance)
    r'(?P<word>(?:<[^>\n]*>|[^\s{}\[\]=,;:"/<\\@]|/(?![/*])|\\(?![ \t\r]*\n)|<|@(?!"))'
    r'(?:<[^>\n]*>|[^\s{}\[\]=,;:"/<\\@]|/(?![/*])|:(?=/)|\\(?![ \t\r]*\n)|<|@(?!"))*)',
    r'(?P<err>[\s\S])',
]))

_ESCAPES = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', '\\': '\\', '0': '\0',
            '\n': ''}


def _unescape(s):
    if s.startswith('@'):
        return s[2:-1].replace('""', '"')
    body = s[1:-1]
    if '\\' not in body:
        return body
    out = []
    i = 0
    n = len(body)
    while i < n:
        c = body[i]
        if c == '\\' and i + 1 < n:
            nxt = body[i + 1]
            if nxt == '\r' and i + 2 < n and body[i + 2] == '\n':
                i += 3
                continue
            out.append(_ESCAPES.get(nxt, nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def tokenize(text, errors):
    """Returns list of (kind, text, line). kinds: nl str word { } [ ] = , ; : eof.
    errors: list to append (line, message)."""
    toks = []
    append = toks.append
    line = 1
    pos = 0
    n = len(text)
    match = _TOKEN_RE.match
    while pos < n:
        m = match(text, pos)
        kind = m.lastgroup
        s = m.group(kind)
        pos = m.end()
        if kind == 'ws' or kind == 'lcom':
            continue
        if kind == 'nl':
            append(('nl', s, line))
            line += 1
            continue
        if kind == 'word':
            append(('word', s, line))
            continue
        if kind == 'punct':
            append((s, s, line))
            continue
        if kind == 'str' or kind == 'vstr':
            append(('str', s, line))
            line += s.count('\n')
            continue
        if kind == 'colon':
            append((':', s, line))
            continue
        if kind == 'lc':
            line += 1
            continue
        if kind == 'bcom':
            c = s.count('\n')
            if c:
                append(('nl', '\n', line))
                line += c
            continue
        if kind == 'badcom':
            errors.append((line, 'unterminated /* block comment'))
            line += s.count('\n')
            continue
        if kind == 'badstr':
            errors.append((line, 'unterminated string literal'))
            append(('str', s + '"', line))
            continue
        errors.append((line, 'unexpected character %r' % s))
    append(('eof', '', line))
    return toks


class Node(object):
    __slots__ = ('kind', 'name', 'line', 'file', 'parent', 'children', 'index',
                 'bases', 'value', 'is_str', 'mixed', 'ov_children', 'ov_elems',
                 'ov_bases', 'removed', 'end_line')

    def __init__(self, kind, name, line, file, parent):
        self.kind = kind          # group | list | value | void | inherit
        self.name = name
        self.line = line
        self.file = file
        self.parent = parent
        self.children = []
        self.index = {}
        self.bases = ()
        self.value = None
        self.is_str = False
        self.mixed = False        # value mixes quoted and unquoted text
        self.ov_children = None
        self.ov_elems = None
        self.ov_bases = None
        self.removed = None
        self.end_line = line

    def __repr__(self):
        return '<Node %s %r %s:%d>' % (self.kind, self.name,
                                       self.file.display if self.file else '?',
                                       self.line)

    def path_str(self):
        parts = []
        n = self
        while n.parent is not None:
            if n.name is not None:
                parts.append(n.name)
            else:
                try:
                    parts.append(str(n.parent.children.index(n)))
                except ValueError:
                    parts.append('?')
            n = n.parent
        return '/'.join(reversed(parts))


_IDENT_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_.\-]*$')
_NAME_RE = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_.\-]*$')


class Parser(object):
    def __init__(self, text, rfile):
        self.errors = []      # (line, msg)
        self.warnings = []    # (line, msg)
        self.toks = tokenize(text, self.errors)
        self.i = 0
        self.file = rfile
        self.lines = text.split('\n')
        self.suspects = []    # (open_line, close_line) with mismatched indentation

    def indent(self, line):
        if 1 <= line <= len(self.lines):
            t = self.lines[line - 1].replace('\t', '    ')
            return len(t) - len(t.lstrip())
        return -1

    def check_indent(self, open_line, close_line):
        if open_line != close_line and self.indent(open_line) != self.indent(close_line):
            self.suspects.append((open_line, close_line))

    def unclosed(self, open_line, what):
        msg = "unclosed '%s' (reached end of file)" % what
        if self.suspects:
            o, c = self.suspects[0]
            msg += ("; probable culprit: the bracket opened at line %d is closed at line %d "
                    "with a different indentation" % (o, c))
        self.err(open_line, msg)

    def err(self, line, msg):
        self.errors.append((line, msg))

    def parse(self):
        root = Node('group', None, 1, self.file, None)
        self.parse_group_body(root, 'eof', 1)
        return root

    def add_child(self, parent, child):
        parent.children.append(child)
        if child.name is not None:
            key = child.name.lower()
            prev = parent.index.get(key)
            if prev is not None:
                self.warnings.append((child.line, "duplicate field '%s' (also at line %d)"
                                      % (child.name, prev.line)))
            parent.index[key] = child

    def skip_nl(self):
        toks = self.toks
        i = self.i
        while toks[i][0] == 'nl':
            i += 1
        self.i = i

    def parse_group_body(self, node, closer, open_line):
        toks = self.toks
        while True:
            k, s, ln = toks[self.i]
            if k == 'nl' or k == ',' or k == ';':
                self.i += 1
                continue
            if k == closer:
                node.end_line = ln
                if k != 'eof':
                    self.check_indent(open_line, ln)
                    self.i += 1
                return
            if k == 'eof':
                self.unclosed(open_line, '{')
                node.end_line = ln
                return
            if k == '}' or k == ']':
                if closer == 'eof':
                    self.err(ln, "unexpected '%s' (no matching opening bracket)" % k)
                    self.i += 1
                    continue
                self.err(ln, "expected '}' to close group opened at line %d, found '%s'"
                         % (open_line, k))
                self.i += 1
                return
            if k == 'word' or k == 'str':
                name = _unescape(s) if k == 'str' else s
                if k == 'word' and not _NAME_RE.match(s):
                    self.err(ln, "unexpected value %r where a field name was expected" % s)
                self.i += 1
                self.parse_entry_after_name(node, name, ln)
                continue
            if k in ('{', '[', ':'):
                self.err(ln, "unnamed element '%s' inside a {} group" % k)
                self.parse_anon_element(node)
                continue
            self.err(ln, "unexpected '%s'" % s)
            self.i += 1

    def parse_entry_after_name(self, parent, name, ln):
        toks = self.toks
        j = self.i
        while toks[j][0] == 'nl':
            j += 1
        k2 = toks[j][0]
        crossed_nl = j > self.i
        if k2 == '=' and not crossed_nl:
            self.i = j + 1
            k3 = toks[self.i][0]
            if k3 == 'nl':
                jj = self.i
                while toks[jj][0] == 'nl':
                    jj += 1
                if toks[jj][0] in ('{', '['):
                    self.i = jj
                    k3 = toks[jj][0]
            if k3 == '{' or k3 == '[':
                self.parse_body(parent, name, ln, ())
                return
            if k3 == ':':
                # `Tags = : ^/0/Tags [captured_station]` (vanilla)
                self.i += 1
                bases = self.parse_bases(ln)
                self.parse_body(parent, name, ln, bases)
                return
            node = self.parse_value(parent, name, ln)
            if node is not None:
                self.add_child(parent, node)
            return
        if k2 == ':' and not crossed_nl:
            self.i = j + 1
            bases = self.parse_bases(ln)
            self.parse_body(parent, name, ln, bases)
            return
        if k2 == '{' or k2 == '[':
            self.i = j
            self.parse_body(parent, name, ln, ())
            return
        if not crossed_nl and k2 in ('word', 'str'):
            self.err(ln, "expected '=', ':', '{' or '[' after '%s', found %r"
                     % (name, toks[j][1]))
        # void field
        node = Node('void', name, ln, self.file, parent)
        self.add_child(parent, node)

    def parse_body(self, parent, name, ln, bases):
        """At '{', '[' or something else (inherit-only node)."""
        toks = self.toks
        k, s, bl = toks[self.i]
        if k == '{':
            node = Node('group', name, ln, self.file, parent)
            node.bases = bases
            self.i += 1
            self.add_child(parent, node)
            self.parse_group_body(node, '}', bl)
        elif k == '[':
            node = Node('list', name, ln, self.file, parent)
            node.bases = bases
            self.i += 1
            self.add_child(parent, node)
            self.parse_list_body(node, bl)
        else:
            node = Node('inherit', name, ln, self.file, parent)
            node.bases = bases
            if not bases:
                node.kind = 'void'
            self.add_child(parent, node)

    def parse_bases(self, ln):
        toks = self.toks
        bases = []
        while True:
            self.skip_nl()
            k, s, bl = toks[self.i]
            if k in ('word', 'str'):
                text = _unescape(s) if k == 'str' else s
                self.i += 1
                # `^/0/ Name` (space inside the path, seen in SW:ACD)
                while toks[self.i][0] == 'word' and (text.endswith('/') or
                                                     toks[self.i][1].startswith('/')):
                    self.warnings.append((bl, "whitespace inside inheritance path '%s %s'"
                                          % (text, toks[self.i][1])))
                    text += toks[self.i][1]
                    self.i += 1
                bases.append((text, bl))
            else:
                self.err(bl, "expected an inheritance path after ':', found %r" % (s or k))
                break
            k2 = toks[self.i][0]
            if k2 == ',':
                self.i += 1
                j = self.i
                while toks[j][0] == 'nl':
                    j += 1
                if toks[j][0] in ('{', '['):
                    # trailing comma before the body (vanilla codex.rules)
                    self.i = j
                    break
                continue
            j = self.i
            while toks[j][0] == 'nl':
                j += 1
            kj, sj, lj = toks[j]
            if kj in ('{', '['):
                self.i = j
                break
            if kj == 'word' and j > self.i and sj[:1] in ('&', '<'):
                self.i = j
                continue
            if kj in ('word', 'str') and j == self.i:
                self.err(lj, "unexpected %r in inheritance list (missing ','?)" % sj)
            break
        return tuple(bases)

    def parse_list_body(self, node, open_line):
        toks = self.toks
        while True:
            k, s, ln = toks[self.i]
            if k == 'nl' or k == ',' or k == ';':
                self.i += 1
                continue
            if k == ']':
                node.end_line = ln
                self.check_indent(open_line, ln)
                self.i += 1
                return
            if k == 'eof':
                self.unclosed(open_line, '[')
                return
            if k == '}':
                self.err(ln, "expected ']' to close list opened at line %d, found '}'"
                         % open_line)
                self.i += 1
                return
            if k in ('{', '[', ':'):
                self.parse_anon_element(node)
                continue
            if k == 'word' or k == 'str':
                nk = toks[self.i + 1][0]
                if k == 'word' and nk in ('=', '{', ':') and _IDENT_RE.match(s):
                    # named entry inside a list
                    self.i += 1
                    self.parse_entry_after_name(node, s, ln)
                    continue
                v = self.parse_value(node, None, ln)
                if v is not None:
                    self.add_child(node, v)
                continue
            self.err(ln, "unexpected '%s' in list" % s)
            self.i += 1

    def parse_anon_element(self, parent):
        toks = self.toks
        k, s, ln = toks[self.i]
        if k == ':':
            self.i += 1
            bases = self.parse_bases(ln)
            self.parse_body(parent, None, ln, bases)
        else:
            self.parse_body(parent, None, ln, ())

    def parse_value(self, parent, name, ln):
        """A value runs to the end of the line or to ',' ';' '}' ']' (the
        game does not treat parentheses specially: vanilla quotes math that
        needs commas, e.g. "round((&X) * 2, 0)")."""
        toks = self.toks
        parts = []
        while True:
            k, s, l2 = toks[self.i]
            if k == 'word' or k == 'str':
                parts.append((k, s))
                self.i += 1
                continue
            if k == ':':
                parts.append(('word', ':'))
                self.i += 1
                continue
            break
        k, s, l2 = toks[self.i]
        if k in ('{', '[', '=') and parts:
            self.err(l2, "unexpected '%s' after value (missing newline, ',' or ';'?)" % k)
        node = Node('value', name, ln, self.file, parent)
        if not parts:
            node.value = ''
            node.is_str = True
            if name is not None:
                self.warnings.append((ln, "empty value for '%s'" % name))
            return node
        if all(p[0] == 'str' for p in parts):
            node.value = ''.join(_unescape(p[1]) for p in parts)
            node.is_str = True
        elif any(p[0] == 'str' for p in parts):
            # Quoted and unquoted text concatenate (vanilla en.rules has
            # "...the " military free market ", ..." and thrusters use
            # db2vol( "&~/X" )).  Keep it as an unquoted (math) value.
            node.value = ' '.join(_unescape(p[1]) if p[0] == 'str' else p[1]
                                  for p in parts)
            node.is_str = False
            node.mixed = True
        else:
            node.value = ' '.join(p[1] for p in parts)
        return node


def parse_text(text, rfile):
    p = Parser(text, rfile)
    root = p.parse()
    return root, p.errors, p.warnings


# ---------------------------------------------------------------------------
# Reference helpers
# ---------------------------------------------------------------------------

_PURE_REF_RE = re.compile(r'^&\s*(?:<[^>]*>)?[^\s()<>]*$')
_ANGLE_PATH_RE = re.compile(r'^<[^>]+>(/\S*)?$')
_UNQUOTED_ASSET_RE = re.compile(r'^[^\s&()<>"]+\.(png|wav|ogg|shader|jpg|jpeg|ttf|otf|mp3)$', re.I)
_ACTION_PATH_FIELDS = {'addto', 'overridein', 'replace', 'remove', 'addbaseto'}
_PATH_START = set('<~/.^:_') | set('abcdefghijklmnopqrstuvwxyz') | \
    set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')


def is_pure_ref(v):
    return bool(v) and v[0] == '&' and _PURE_REF_RE.match(v) is not None


def refs_in_value(raw, quoted=False):
    """Returns (paths, problems) for the & references inside a value.
    quoted=True: the value was a quoted string; only `(&path)` math
    references are taken and nothing else is reported (e.g. "&amp;")."""
    s = raw.strip()
    if not s or '&' not in s:
        return [], []
    if not quoted and s[0] == '&' and _PURE_REF_RE.match(s):
        return [s[1:].strip()], []
    paths = []
    problems = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] != '&':
            i += 1
            continue
        prev = s[:i].rstrip()
        nxt = s[i + 1] if i + 1 < n else ''
        if nxt not in _PATH_START:
            if not quoted:
                problems.append("stray '&' (not followed by a path) in value: %s" % s)
            i += 1
            continue
        if quoted and not prev.endswith('('):
            i += 1
            continue
        j = i + 1
        while j < n:
            cj = s[j]
            if cj == '<':
                e = s.find('>', j)
                j = n if e < 0 else e + 1
                continue
            if cj == ')' or cj.isspace() or cj == ',':
                break
            j += 1
        path = s[i + 1:j]
        rest = s[j:].lstrip()
        if quoted and not rest.startswith(')'):
            i = j      # e.g. "(&amp; text)" inside a display string
            continue
        if not prev.endswith('(') or not rest.startswith(')'):
            problems.append("reference '&%s' inside a math expression must be "
                            "wrapped in parentheses: %s" % (path, s))
        if path:
            paths.append(path)
        i = j
    return paths, problems


class ResolveError(Exception):
    pass


# ---------------------------------------------------------------------------
# Linter
# ---------------------------------------------------------------------------

class Linter(object):
    def __init__(self, vfs, report, mode='files'):
        self.vfs = vfs
        self.report = report
        self.mode = mode
        self.files = {}           # (origin, path) -> RFile
        self.global_root_file = None
        self._ref_cache = {}      # id(node) -> node or None
        self._bases_cache = {}    # id(node) -> list of nodes
        self._busy = set()
        self.lint_queue = []
        self._pending_parse_issues = {}   # (origin, path) -> (errors, warnings)
        self.mod_dir = None
        self.stats = {'files': 0, 'refs': 0, 'refs_ok': 0, 'bases': 0,
                      'bases_ok': 0, 'assets': 0, 'assets_ok': 0,
                      'case_notes': 0, 'virtual': 0}
        self.case_notes = []
        # mod-mode collections
        self.string_key_uses = []     # (rfile, line, key)
        self.part_id_nodes = []       # (rfile, line, id, node)
        self.shot_id_nodes = []
        self.bullet_targets = []      # (value node, target node)

    # -- files ---------------------------------------------------------------

    def display_for(self, origin, path):
        if origin == 'vanilla':
            return '<vanilla>/' + path
        if self.mod_dir and (path == self.mod_dir or path.startswith(self.mod_dir + os.sep)):
            return os.path.relpath(path, os.path.dirname(self.mod_dir))
        return path

    def get_file(self, loc):
        key = (loc.origin, loc.path)
        rf = self.files.get(key)
        if rf is not None:
            return rf
        rf = RFile(loc.origin, loc.path, self.display_for(loc.origin, loc.path))
        self.files[key] = rf
        if loc.origin == 'vanilla':
            data = self.vfs.vanilla_read(loc.path)
        else:
            try:
                with open(loc.path, 'rb') as f:
                    data = f.read()
            except OSError:
                data = None
        if data is None:
            rf.root = Node('group', None, 1, rf, None)
            rf.parse_ok = False
            return rf
        text = data.decode('utf-8', 'replace')
        root, errors, warnings = parse_text(text, rf)
        rf.root = root
        self.stats['files'] += 1
        if errors:
            rf.parse_ok = False
        self._pending_parse_issues[key] = (errors, warnings)
        # mod files reached from the mod get linted
        if self.mode == 'mod' and loc.origin == 'fs' and self.mod_dir and \
                (loc.path.startswith(self.mod_dir + os.sep)):
            if not rf.lint:
                rf.lint = True
                self.lint_queue.append(rf)
        return rf

    def emit_parse_issues(self, rf):
        key = (rf.origin, rf.path)
        errs, warns = self._pending_parse_issues.pop(key, ((), ()))
        for line, msg in errs:
            self.report.add(ERROR, rf, line, 'syntax', msg)
        for line, msg in warns:
            self.report.add(WARNING, rf, line, 'syntax', msg)

    def global_root(self):
        if self.global_root_file is None:
            loc = self.vfs.vanilla_lookup('cosmoteer.rules')
            if loc is None:
                return None
            self.global_root_file = self.get_file(loc)
        return self.global_root_file.root

    def resolve_file_path(self, p, from_file):
        """Resolve a file path string written in from_file. Returns Loc or None.
        Raises ResolveError for unsupported forms."""
        p = p.replace('\\', '/').strip()
        if not p:
            raise ResolveError('empty file path')
        if p.startswith('/') or re.match(r'^[A-Za-z]:', p):
            raise ResolveError('absolute paths are not allowed')
        if p.startswith('./'):
            rest = p[2:]
            while rest.startswith('./'):
                rest = rest[2:]
            first, _, tail = rest.partition('/')
            if first.lower() == 'data':
                loc = self.vfs.vanilla_lookup(tail)
                if loc is not None and first != 'Data':
                    loc.case_ok = False
                return loc
            raise ResolveError("'./' paths outside ./Data/ cannot be checked")
        if from_file.origin == 'vanilla':
            rel = posixpath.normpath(posixpath.join(posixpath.dirname(from_file.path), p))
            return self.vfs.vanilla_lookup(rel)
        d = os.path.dirname(from_file.path)
        return self.vfs.fs_lookup(os.path.join(d, p.replace('/', os.sep)))

    # -- core resolution -----------------------------------------------------

    def deref(self, node):
        """Follow value references until a non-reference node."""
        seen = 0
        while node is not None and node.kind == 'value' and not node.is_str \
                and is_pure_ref(node.value):
            node = self.resolve_ref_node(node)
            seen += 1
            if seen > 64:
                return None
        return node

    def resolve_ref_node(self, node):
        nid = id(node)
        if nid in self._ref_cache:
            return self._ref_cache[nid]
        if ('r', nid) in self._busy:
            return None
        self._busy.add(('r', nid))
        try:
            target = self.walk(node.value[1:], node.parent, node.file)
        except ResolveError:
            target = None
        finally:
            self._busy.discard(('r', nid))
        self._ref_cache[nid] = target
        return target

    def bases_of(self, node):
        """Resolved (dereferenced) base nodes of node, in order."""
        nid = id(node)
        r = self._bases_cache.get(nid)
        if r is not None:
            return r
        if not node.bases and not node.ov_bases:
            return ()
        if ('b', nid) in self._busy:
            return ()
        self._busy.add(('b', nid))
        out = []
        try:
            for raw, line in node.bases:
                try:
                    b = self.walk(raw, node.parent, node.file)
                except ResolveError:
                    b = None
                b = self.deref(b) if b is not None else None
                if b is not None:
                    out.append(b)
            if node.ov_bases:
                for vnode in node.ov_bases:
                    b = self.deref(vnode)
                    if b is not None:
                        out.append(b)
        finally:
            self._busy.discard(('b', nid))
        self._bases_cache[nid] = out
        return out

    def is_listlike(self, node, depth=0):
        if node.kind == 'list':
            return True
        if node.kind == 'inherit' and depth < 50:
            for b in self.bases_of(node):
                if self.is_listlike(b, depth + 1):
                    return True
        return False

    def is_grouplike(self, node, depth=0):
        if node.kind == 'group':
            return True
        if node.kind == 'inherit' and depth < 50:
            for b in self.bases_of(node):
                if self.is_grouplike(b, depth + 1):
                    return True
        return False

    def list_elements(self, node):
        node = self.deref(node)
        if node is None:
            return []
        nid = id(node)
        if ('e', nid) in self._busy:
            return []
        self._busy.add(('e', nid))
        try:
            elems = []
            for b in self.bases_of(node):
                if self.is_listlike(b):
                    elems.extend(self.list_elements(b))
            if node.kind == 'list':
                elems.extend(node.children)
            if node.ov_elems:
                elems.extend(node.ov_elems)
            return elems
        finally:
            self._busy.discard(('e', nid))

    def lookup(self, node, name, notes=None):
        """Find child `name` of node (through references and inheritance)."""
        node = self.deref(node)
        if node is None:
            return None
        key = name.lower()
        nid = id(node)
        bk = ('l', nid, key)
        if bk in self._busy:
            return None
        self._busy.add(bk)
        try:
            if node.removed and key in node.removed:
                return None
            if node.ov_children:
                c = node.ov_children.get(key)
                if c is not None:
                    return c
            c = node.index.get(key)
            if c is not None:
                if notes is not None and c.name != name:
                    notes.append("case mismatch: '%s' is written '%s' at %s:%d"
                                 % (name, c.name, c.file.display, c.line))
                return c
            if name.isdigit() and self.is_listlike(node):
                elems = self.list_elements(node)
                i = int(name)
                if i < len(elems):
                    return elems[i]
                return None
            for b in self.bases_of(node):
                c = self.lookup(b, name, notes)
                if c is not None:
                    return c
            return None
        finally:
            self._busy.discard(bk)

    def walk(self, path, start, file, notes=None):
        """Resolve a reference/inheritance path written in `file` with start
        node `start` (the node containing the field). Returns the node or
        raises ResolveError."""
        p = path.strip()
        if p.startswith('&'):
            p = p[1:].strip()
        if not p:
            raise ResolveError('empty path')
        trail = []
        if p.startswith('<'):
            j = p.find('>')
            if j < 0:
                raise ResolveError("missing '>' in file path")
            fpath = p[1:j]
            rest = p[j + 1:]
            if rest and not rest.startswith('/'):
                raise ResolveError("expected '/' after <%s>" % fpath)
            loc = self.resolve_file_path(fpath, file)
            if loc is None or loc.is_dir:
                raise ResolveError('file not found: <%s>' % fpath)
            if not fpath.lower().endswith('.rules'):
                raise ResolveError('<%s> is not a .rules file' % fpath)
            if notes is not None and not loc.case_ok:
                notes.append("file name case mismatch: <%s> is actually '%s'"
                             % (fpath, loc.path if loc.origin == 'vanilla'
                                else os.path.basename(loc.path)))
            rf = self.get_file(loc)
            if not rf.parse_ok and rf.root is not None and not rf.root.children:
                raise ResolveError('could not read/parse <%s>' % fpath)
            cur = rf.root
            rest = rest[1:]
        elif p.startswith('~'):
            cur = file.root
            rest = p[1:]
            if rest and not rest.startswith('/'):
                raise ResolveError("expected '/' after '~'")
            rest = rest[1:]
        elif p.startswith('/'):
            cur = self.global_root()
            if cur is None:
                raise ResolveError('vanilla cosmoteer.rules not available for "/" paths')
            rest = p[1:]
        else:
            cur = start
            rest = p
        segs = rest.split('/') if rest else []
        n = len(segs)
        i = 0
        virtual = False
        while i < n:
            seg = segs[i].strip()
            i += 1
            if seg == '' or seg == '.':
                continue
            if seg == '..':
                tgt = self.deref(cur)
                if tgt is None:
                    raise ResolveError("cannot resolve reference before '..'")
                if tgt is not cur:
                    trail = []
                    cur = tgt
                if trail:
                    cur = trail.pop()
                else:
                    if cur.parent is None:
                        raise ResolveError("'..' goes above the root of %s" % cur.file.display)
                    cur = cur.parent
                continue
            if seg == '^':
                if i >= n or not segs[i].strip().isdigit():
                    raise ResolveError("'^' must be followed by a base index")
                idx = int(segs[i].strip())
                i += 1
                tgt = self.deref(cur)
                if tgt is None:
                    raise ResolveError("cannot resolve node before '^'")
                bases = self.bases_of(tgt)
                nb = len(tgt.bases) + len(tgt.ov_bases or ())
                if idx >= nb:
                    raise ResolveError("'^/%d' but %s has %d base(s)"
                                       % (idx, self._node_desc(tgt), nb))
                if idx >= len(bases) or len(bases) != nb:
                    raise ResolveError("'^/%d': a base of %s does not resolve"
                                       % (idx, self._node_desc(tgt)))
                cur = bases[idx]
                trail = []
                continue
            if seg == ':':
                virtual = True
                continue
            tgt = self.deref(cur)
            if tgt is None:
                raise ResolveError("reference '%s' does not resolve" % '/'.join(segs[:i - 1]))
            if tgt is not cur:
                trail = []
            child = self.lookup(tgt, seg, notes)
            if child is None:
                done = '/'.join(segs[:i - 1])
                msg = "no '%s' in %s" % (seg, self._node_desc(tgt))
                if done:
                    msg += " (after '%s')" % done
                if virtual:
                    raise ResolveError('VIRTUAL:' + msg)
                raise ResolveError(msg)
            trail.append(tgt)
            cur = child
        return cur

    def _node_desc(self, node):
        if node.parent is None:
            return 'root of %s' % node.file.display
        return "'%s' (%s:%d)" % (node.path_str(), node.file.display, node.line)

    # -- linting -------------------------------------------------------------

    def lint_file(self, rf):
        if rf.linted:
            return
        rf.linted = True
        rf.lint = True
        self.emit_parse_issues(rf)
        stack = [rf.root]
        while stack:
            node = stack.pop()
            if node.bases:
                for raw, line in node.bases:
                    self.check_path(rf, node.parent, raw, line, 'base', node)
            if node.kind == 'value':
                self.check_value(rf, node)
            if node.children:
                stack.extend(reversed(node.children))
            if self.mode == 'mod':
                self.collect_ids(rf, node)

    def check_path(self, rf, start, raw, line, what, node=None):
        key = 'bases' if what == 'base' else 'refs'
        self.stats[key] += 1
        notes = []
        path = raw.strip()
        try:
            target = self.walk(path, start, rf, notes)
        except ResolveError as e:
            msg = str(e)
            if msg.startswith('VIRTUAL:'):
                self.stats['virtual'] += 1
                self.report.add(WARNING, rf, line, 'virtual',
                                "virtual path '%s' only resolves through an inheritor: %s"
                                % (path, msg[8:]))
                return None
            label = 'inheritance base' if what == 'base' else 'reference'
            self.report.add(ERROR, rf, line, 'unresolved',
                            "%s '%s' does not resolve: %s" % (label, path, msg))
            return None
        self.stats[key + '_ok'] += 1
        if notes:
            self.stats['case_notes'] += len(notes)
            if self.mode == 'selftest':
                self.case_notes.append((rf, line, path, notes))
            else:
                for n in notes:
                    self.report.add(WARNING, rf, line, 'case', "'%s': %s" % (path, n))
        if what == 'base':
            if node is not None:
                t = self.deref(target)
                if t is not None:
                    if node.kind == 'list' and t.kind in ('group', 'value', 'void') \
                            and not self.is_listlike(t):
                        self.report.add(WARNING, rf, line, 'kind',
                                        "list '%s' inherits from a non-list (%s)"
                                        % (node.name or '[]', self._node_desc(t)))
                    elif node.kind == 'group' and t.kind in ('list',):
                        self.report.add(WARNING, rf, line, 'kind',
                                        "group '%s' inherits from a list (%s)"
                                        % (node.name or '{}', self._node_desc(t)))
        return target

    def check_value(self, rf, node):
        v = node.value
        if v and not node.is_str and _FRACTION_RE.match(v.strip()):
            name = (node.name or '').lower()
            if name == 'basevalue' and node.parent is not None:
                name = (node.parent.name or '').lower()
            if name in INT_FIELDS:
                self.report.add(ERROR, rf, node.line, 'type',
                                "'%s' is read as an integer by the game but has the fractional value %s "
                                "(the mod fails to load)" % (node.name if node.name != 'BaseValue' else
                                                             node.parent.name, v.strip()))
        if node.is_str:
            self.check_string(rf, node)
            if v and '(&' in v:
                for p in refs_in_value(v, quoted=True)[0]:
                    self.check_path(rf, node.parent, '&' + p, node.line, 'ref')
            return
        if not v:
            return
        if '&' in v:
            paths, problems = refs_in_value(v, quoted=node.mixed)
            for pr in problems:
                self.report.add(ERROR, rf, node.line, 'syntax', pr)
            for p in paths:
                target = self.check_path(rf, node.parent, '&' + p, node.line, 'ref')
                if target is not None and self.mode == 'mod' and node.name and \
                        node.name.lower() == 'bullet':
                    self.bullet_targets.append((rf, node, target))
        elif _UNQUOTED_ASSET_RE.match(v.strip()) and _is_asset_field(node):
            # unquoted words are strings too (`File = ../x.png`)
            self.check_asset(rf, node, v.strip())
        elif _ANGLE_PATH_RE.match(v.strip()):
            if (node.name or '').lower() in _ACTION_PATH_FIELDS or (
                    node.name is None and node.parent is not None and
                    (node.parent.name or '').lower() == 'removemany'):
                return   # mod action target paths are plain strings
            self.report.add(WARNING, rf, node.line, 'syntax',
                            "value '%s' looks like a path but has no '&' (it will be "
                            "read as plain text, not as a reference)" % v.strip())

    def check_string(self, rf, node):
        s = node.value
        if not s:
            return
        name = (node.name or '').lower()
        parent = node.parent
        is_asset = False
        if name in ASSET_KEYS:
            is_asset = True
        elif node.name is None and parent is not None and parent.name and \
                parent.name.lower() in ASSET_LIST_KEYS:
            is_asset = True
        low = s.lower().strip()
        if low.endswith(ASSET_EXTS) and not low.startswith('<') and '\n' not in s \
                and len(s) < 300:
            is_asset = True
        if is_asset:
            self.check_asset(rf, node, s)
        if self.mode == 'mod' and name in STRING_KEY_FIELDS:
            self.string_key_uses.append((rf, node.line, s, node.name))

    def check_asset(self, rf, node, s):
        self.stats['assets'] += 1
        try:
            loc = self.resolve_file_path(s, rf)
        except ResolveError as e:
            self.report.add(WARNING, rf, node.line, 'asset',
                            "cannot check asset path \"%s\": %s" % (s, e))
            return
        if loc is None or loc.is_dir:
            where = ''
            if not s.startswith('./'):
                if rf.origin == 'vanilla':
                    where = ' (looked in <vanilla>/%s)' % posixpath.normpath(
                        posixpath.join(posixpath.dirname(rf.path), s))
                else:
                    where = ' (looked in %s)' % self.display_for(
                        'fs', os.path.normpath(os.path.join(os.path.dirname(rf.path), s)))
            self.report.add(ERROR, rf, node.line, 'asset',
                            "missing asset file \"%s\" for '%s'%s"
                            % (s, node.name or (node.parent.name or '') + '[]', where))
            return
        self.stats['assets_ok'] += 1
        if not loc.case_ok:
            self.stats['case_notes'] += 1
            if self.mode == 'selftest':
                self.case_notes.append((rf, node.line, s, ['file name case mismatch']))
            else:
                actual = loc.path if loc.origin == 'vanilla' else os.path.basename(loc.path)
                self.report.add(WARNING, rf, node.line, 'case',
                                "asset \"%s\" differs in case from the real file '%s' "
                                "(works on Windows only)" % (s, actual))

    # -- mod mode ------------------------------------------------------------

    def collect_ids(self, rf, node):
        if node.kind == 'value' and node.name and node.name.lower() == 'id' and \
                node.parent is not None:
            par = node.parent
            val = node.value.strip()
            if par.name and par.name.lower() == 'part':
                self.part_id_nodes.append((rf, node.line, val, par))
            elif par.name and par.name.lower() in ('bullet', 'shot'):
                self.shot_id_nodes.append((rf, node.line, val, par))
            elif par.parent is None and _in_shots_dir(rf):
                self.shot_id_nodes.append((rf, node.line, val, par))


def _is_asset_field(node):
    name = (node.name or '').lower()
    if name in ASSET_KEYS:
        return True
    par = node.parent
    return node.name is None and par is not None and par.name is not None and \
        par.name.lower() in ASSET_LIST_KEYS


def _changes_something(node):
    """True if a derived node has own children (i.e. is not a plain alias)."""
    return bool(node.children) or not node.bases


def _in_shots_dir(rf):
    parts = rf.path.replace(os.sep, '/').lower().split('/')
    return 'shots' in parts[:-1]


def _field(node, name):
    if node is None:
        return None
    return node.index.get(name.lower())


def _strip_quotes_path(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        v = v[1:-1]
    return v


class ModLinter(object):
    def __init__(self, linter, mod_dir, langs):
        self.L = linter
        self.mod_dir = os.path.abspath(mod_dir)
        self.langs = langs
        self.report = linter.report
        self.strings_roots = []
        self.vanilla_strings = None

    def target_ctx(self):
        """A pseudo file located at the Data root, used for action targets."""
        rf = RFile('vanilla', 'cosmoteer.rules', '<vanilla>/cosmoteer.rules')
        rf.root = self.L.global_root()
        return rf

    def run(self):
        L = self.L
        L.mod_dir = self.mod_dir
        manifest = os.path.join(self.mod_dir, 'mod.rules')
        loc = L.vfs.fs_lookup(manifest)
        if loc is None:
            self.report.add(ERROR, None, 0, 'mod', 'mod.rules not found in %s' % self.mod_dir)
            return
        mrf = L.get_file(loc)
        mrf.lint = True
        if L.global_root() is None:
            self.report.add(ERROR, mrf, 0, 'mod',
                            'vanilla cosmoteer.rules not found (check --vanilla)')
        L.emit_parse_issues(mrf)
        self.check_manifest(mrf)
        self.apply_actions(mrf)
        # caches may hold results computed before overlays existed
        L._ref_cache.clear()
        L._bases_cache.clear()
        mrf.linted = False
        L._pending_parse_issues[(mrf.origin, mrf.path)] = ((), ())
        L.lint_file(mrf)
        self.drain_queue()
        # every other .rules file under the mod dir
        for dirpath, dirnames, filenames in os.walk(self.mod_dir):
            dirnames[:] = sorted(d for d in dirnames if d != '.git')
            for fn in sorted(filenames):
                if not fn.lower().endswith('.rules'):
                    continue
                p = os.path.join(dirpath, fn)
                key = ('fs', p)
                rf = L.files.get(key)
                if rf is not None and rf.linted:
                    continue
                if self.is_strings_file(p):
                    continue
                rf = L.get_file(Loc('fs', p))
                if not rf.linted:
                    rf.unreachable = True
                    L.lint_queue = [x for x in L.lint_queue if x is not rf]
                    L.lint_file(rf)
                    self.drain_queue(unreachable=True)
        self.check_strings()
        self.check_ids()
        self.check_semantics()

    def drain_queue(self, unreachable=False):
        L = self.L
        while L.lint_queue:
            rf = L.lint_queue.pop(0)
            if rf.linted:
                continue
            if unreachable:
                rf.unreachable = True
            L.lint_file(rf)

    def is_strings_file(self, p):
        for d in self.strings_dirs():
            if os.path.dirname(p) == d:
                return True
        return False

    _sdirs = None

    def strings_dirs(self):
        return self._sdirs or []

    def check_manifest(self, mrf):
        root = mrf.root
        L = self.L
        for req in ('ID', 'Name'):
            if _field(root, req) is None:
                self.report.add(ERROR, mrf, 1, 'mod', "mod.rules has no '%s'" % req)
        idn = _field(root, 'ID')
        if idn is not None and idn.kind == 'value':
            v = idn.value.strip()
            if '.' not in v.strip('.'):
                self.report.add(ERROR, mrf, idn.line, 'mod',
                                "mod ID '%s' must be 'author_name.mod_name'" % v)
        if _field(root, 'CompatibleGameVersions') is None:
            self.report.add(WARNING, mrf, 1, 'mod',
                            'no CompatibleGameVersions: the game auto-disables the mod')
        sf = _field(root, 'StringsFolder')
        self._sdirs = []
        if sf is not None and sf.kind == 'value':
            loc = L.vfs.fs_lookup(os.path.join(self.mod_dir, sf.value.replace('/', os.sep)))
            if loc is None or not loc.is_dir:
                self.report.add(ERROR, mrf, sf.line, 'strings',
                                "StringsFolder \"%s\" does not exist" % sf.value)
            else:
                if not loc.case_ok:
                    self.report.add(WARNING, mrf, sf.line, 'case',
                                    "StringsFolder \"%s\" differs in case from the real "
                                    "folder '%s' (works on Windows only)"
                                    % (sf.value, os.path.basename(loc.path)))
                self._sdirs.append(loc.path)
                en = L.vfs.fs_lookup(os.path.join(loc.path, 'en.rules'))
                if en is None:
                    self.report.add(ERROR, mrf, sf.line, 'strings',
                                    'no en.rules in StringsFolder')
                else:
                    erf = L.get_file(en)
                    erf.lint = True
                    L.emit_parse_issues(erf)
                    erf.linted = True
                    self.strings_roots.append(erf)
                    self.check_langs(loc.path, erf)
        # vanilla strings
        vloc = L.vfs.vanilla_lookup('strings/en.rules')
        if vloc is not None:
            self.vanilla_strings = L.get_file(vloc)
        for key in ('Logo',):
            n = _field(root, key)
            if n is not None and n.kind == 'value' and n.is_str:
                pass  # checked as asset by lint_file

    def check_langs(self, sdir, erf):
        L = self.L
        en_keys = _flatten_keys(erf.root)
        for lang in self.langs:
            loc = L.vfs.fs_lookup(os.path.join(sdir, lang + '.rules'))
            if loc is None:
                self.report.add(WARNING, erf, 0, 'strings',
                                'no %s.rules next to en.rules' % lang)
                continue
            lrf = L.get_file(loc)
            lrf.lint = True
            L.emit_parse_issues(lrf)
            lrf.linted = True
            lkeys = _flatten_keys(lrf.root)
            missing = [k for k in en_keys if k.lower() not in lkeys]
            for k in missing:
                self.report.add(WARNING, lrf, 0, 'strings',
                                "key '%s' (en.rules:%d) missing in %s.rules"
                                % (k, en_keys[k], lang))

    def apply_actions(self, mrf):
        L = self.L
        actions = _field(mrf.root, 'Actions')
        if actions is None:
            return
        if actions.kind != 'list' and not L.is_listlike(actions):
            self.report.add(ERROR, mrf, actions.line, 'mod', "'Actions' must be a [] list")
            return
        ctx = self.target_ctx()
        for idx, act in enumerate(L.list_elements(actions)):
            a = L.deref(act)
            if a is None or not L.is_grouplike(a):
                self.report.add(ERROR, act.file, act.line, 'action',
                                'action #%d is not a {} group' % idx)
                continue
            self.apply_action(a, idx, ctx)

    def _act_field(self, a, name):
        n = self.L.lookup(a, name)
        return n

    def _flag(self, a, name):
        n = self._act_field(a, name)
        return n is not None and n.kind == 'value' and n.value.strip().lower() == 'true'

    def apply_action(self, a, idx, ctx):
        L = self.L
        rf = a.file
        tnode = self._act_field(a, 'Action')
        if tnode is None or tnode.kind != 'value':
            self.report.add(ERROR, rf, a.line, 'action', "action #%d has no 'Action ='" % idx)
            return
        atype = tnode.value.strip().lower()
        if atype not in ACTION_TARGET_FIELDS:
            self.report.add(ERROR, rf, tnode.line, 'action',
                            "action #%d: unknown Action type '%s'" % (idx, tnode.value))
            return
        tfield, vfield = ACTION_TARGET_FIELDS[atype]
        ignore = self._flag(a, 'IgnoreIfNotExisting')
        create = self._flag(a, 'CreateIfNotExisting')
        if atype == 'removemany':
            lst = self._act_field(a, 'RemoveMany')
            if lst is None:
                self.report.add(ERROR, rf, a.line, 'action',
                                "action #%d (RemoveMany) has no 'RemoveMany' list" % idx)
                return
            for el in L.list_elements(lst):
                if el.kind == 'value':
                    self.check_target(el, _strip_quotes_path(el.value), ctx, ignore, False, idx)
            return
        pnode = self._act_field(a, tfield)
        if pnode is None or pnode.kind != 'value':
            self.report.add(ERROR, rf, a.line, 'action',
                            "action #%d (%s) has no '%s' path"
                            % (idx, tnode.value.strip(), _CANON.get(tfield, tfield)))
            return
        vnode = None
        if vfield is not None:
            vnode = self._act_field(a, vfield)
            if vnode is None:
                self.report.add(ERROR, rf, a.line, 'action',
                                "action #%d (%s) has no '%s'"
                                % (idx, tnode.value.strip(), _CANON.get(vfield, vfield)))
        path = _strip_quotes_path(pnode.value)
        target = self.check_target(pnode, path, ctx, ignore, create, idx,
                                   atype=atype, vnode=vnode)
        if target is None:
            if create and atype in ('add', 'addmany', 'overrides'):
                target = self.create_target(pnode, path, ctx, atype)
            if target is None:
                return
        tgt = L.deref(target)
        if tgt is None:
            return
        # kind checks + apply
        if atype == 'addmany':
            if not L.is_listlike(tgt):
                self.report.add(ERROR, pnode.file, pnode.line, 'action',
                                "AddMany target '%s' must be a [] list (is %s)"
                                % (path, tgt.kind))
                return
            if vnode is not None:
                src = L.deref(vnode)
                if src is None:
                    return  # reported by lint
                if not L.is_listlike(src):
                    self.report.add(ERROR, vnode.file, vnode.line, 'action',
                                    'ManyToAdd must be a [] list (or a reference to one)')
                    return
                elems = L.list_elements(src)
                if tgt.ov_elems is None:
                    tgt.ov_elems = []
                tgt.ov_elems.extend(elems)
                self.note_parts_added(path, elems)
        elif atype == 'add':
            nm = self._act_field(a, 'Name')
            if L.is_listlike(tgt):
                if vnode is not None:
                    if tgt.ov_elems is None:
                        tgt.ov_elems = []
                    tgt.ov_elems.append(vnode)
                    self.note_parts_added(path, [vnode])
            elif L.is_grouplike(tgt) or tgt.parent is None:
                if nm is None or nm.kind != 'value' or not nm.value.strip():
                    self.report.add(ERROR, pnode.file, pnode.line, 'action',
                                    "Add into a {} group/file '%s' needs a 'Name'" % path)
                    return
                name = _strip_quotes_path(nm.value)
                if vnode is not None:
                    exists = L.lookup(tgt, name) is not None
                    if exists and not self._flag(a, 'OnlyIfNotExisting'):
                        self.report.add(WARNING, pnode.file, pnode.line, 'action',
                                        "Add: '%s' already exists in '%s' (the game reports "
                                        "an error unless OnlyIfNotExisting = true)"
                                        % (name, path))
                    if not exists:
                        if tgt.ov_children is None:
                            tgt.ov_children = {}
                        tgt.ov_children[name.lower()] = vnode
            else:
                self.report.add(ERROR, pnode.file, pnode.line, 'action',
                                "Add target '%s' must be a file, {} group or [] list" % path)
        elif atype == 'overrides':
            if not (L.is_grouplike(tgt) or tgt.parent is None):
                self.report.add(ERROR, pnode.file, pnode.line, 'action',
                                "Overrides target '%s' must be a {} group or file (is %s)"
                                % (path, tgt.kind))
                return
            if vnode is not None:
                src = L.deref(vnode)
                if src is None:
                    return
                if not (L.is_grouplike(src) or src.parent is None):
                    self.report.add(ERROR, vnode.file, vnode.line, 'action',
                                    'Overrides value must be a {} group or a file reference')
                    return
                if tgt.ov_children is None:
                    tgt.ov_children = {}
                for name, child in _merged_children(L, src).items():
                    tgt.ov_children[name] = child
        elif atype == 'replace':
            parent, last = self.split_parent(path, ctx)
            if parent is not None and vnode is not None and last is not None:
                pt = L.deref(parent)
                if pt is not None and not last.isdigit():
                    if pt.ov_children is None:
                        pt.ov_children = {}
                    pt.ov_children[last.lower()] = vnode
            if L.is_listlike(tgt) and vnode is not None:
                src = L.deref(vnode)
                if src is not None and not L.is_listlike(src):
                    self.report.add(ERROR, vnode.file, vnode.line, 'action',
                                    "Replace: '%s' is a [] list but 'With' is not" % path)
        elif atype == 'remove':
            if tgt.parent is None and target.kind != 'value':
                self.report.add(ERROR, pnode.file, pnode.line, 'action',
                                "Remove target '%s' is the root of a file" % path)
                return
            parent, last = self.split_parent(path, ctx)
            if parent is not None and last is not None and not last.isdigit():
                pt = L.deref(parent)
                if pt is not None:
                    if pt.removed is None:
                        pt.removed = set()
                    pt.removed.add(last.lower())
        elif atype == 'addbase':
            if vnode is not None:
                if tgt.ov_bases is None:
                    tgt.ov_bases = []
                tgt.ov_bases.append(vnode)
                L._bases_cache.pop(id(tgt), None)

    def split_parent(self, path, ctx):
        p = path.rstrip('/')
        j = p.rfind('/')
        gt = p.rfind('>')
        if j < 0 or j < gt:
            return None, None
        try:
            parent = self.L.walk(p[:j], ctx.root, ctx)
        except ResolveError:
            return None, None
        return parent, p[j + 1:]

    def check_target(self, pnode, path, ctx, ignore, create, idx, atype=None, vnode=None):
        L = self.L
        notes = []
        try:
            if not path.startswith('<'):
                raise ResolveError("action paths must start with '<file.rules>'")
            target = L.walk(path, ctx.root, ctx, notes)
        except ResolveError as e:
            if ignore:
                self.report.add(WARNING, pnode.file, pnode.line, 'action',
                                "action #%d target '%s' does not resolve (ignored because "
                                "IgnoreIfNotExisting = true): %s" % (idx, path, e))
            elif create:
                self.report.add(WARNING, pnode.file, pnode.line, 'action',
                                "action #%d target '%s' does not exist in vanilla and will be "
                                "created (CreateIfNotExisting = true): %s" % (idx, path, e))
            else:
                self.report.add(ERROR, pnode.file, pnode.line, 'action',
                                "action #%d target '%s' does not resolve in vanilla: %s"
                                % (idx, path, e))
            return None
        for n in notes:
            self.report.add(WARNING, pnode.file, pnode.line, 'case',
                            "action #%d target '%s': %s" % (idx, path, n))
        return target

    def create_target(self, pnode, path, ctx, atype):
        parent, last = self.split_parent(path, ctx)
        if parent is None or last is None:
            self.report.add(ERROR, pnode.file, pnode.line, 'action',
                            "CreateIfNotExisting: parent of '%s' does not resolve" % path)
            return None
        pt = self.L.deref(parent)
        if pt is None:
            return None
        kind = 'list' if atype in ('add', 'addmany') else 'group'
        node = Node(kind, last, pnode.line, pnode.file, pt)
        if pt.ov_children is None:
            pt.ov_children = {}
        pt.ov_children[last.lower()] = node
        return node

    def note_parts_added(self, path, elems):
        if not path.lower().rstrip('/').endswith('/parts'):
            return
        L = self.L
        for el in elems:
            part = L.deref(el)
            if part is None:
                continue
            idn = L.lookup(part, 'ID')
            if idn is None or idn.kind != 'value':
                self.report.add(ERROR, el.file, el.line, 'id',
                                "part added to '%s' has no ID" % path)
                continue
            self.added_parts.append((el, part, idn))

    added_parts = None

    # strings ---------------------------------------------------------------

    def find_string(self, key):
        L = self.L
        segs = [s for s in key.split('/') if s]
        if not segs:
            return False
        roots = [r.root for r in self.strings_roots]
        if self.vanilla_strings is not None:
            roots.append(self.vanilla_strings.root)
        for root in roots:
            cur = root
            for s in segs:
                cur = L.lookup(cur, s)
                if cur is None:
                    break
            if cur is not None:
                return True
        return False

    def check_strings(self):
        L = self.L
        seen = set()
        for rf, line, key, field in L.string_key_uses:
            if (rf.path, line, key) in seen:
                continue
            seen.add((rf.path, line, key))
            if not self.find_string(key):
                self.report.add(ERROR, rf, line, 'strings',
                                "%s \"%s\" not found in the mod strings (en.rules) nor in "
                                "vanilla strings/en.rules" % (field, key))

    # ids ---------------------------------------------------------------------

    def check_ids(self):
        L = self.L
        # literal Part IDs in mod files
        by_id = {}
        for rf, line, val, par in L.part_id_nodes:
            if rf.unreachable:
                continue
            v = _strip_quotes_path(val)
            by_id.setdefault(v.lower(), []).append((rf, line, v))
        for k, lst in sorted(by_id.items()):
            if len(lst) > 1:
                first = lst[0]
                for rf, line, v in lst[1:]:
                    self.report.add(ERROR, rf, line, 'id',
                                    "duplicate part ID '%s' (also %s:%d)"
                                    % (v, first[0].display, first[1]))
        # vanilla part IDs
        vanilla_ids = self.vanilla_part_ids()
        reg = {}
        for el, part, idn in self.added_parts:
            v = _strip_quotes_path(idn.value)
            if idn.parent is not part and _changes_something(part):
                # ID inherited from another part
                self.report.add(ERROR if idn.file.origin == 'vanilla' else WARNING,
                                el.file, el.line, 'id',
                                "part added to Parts inherits its ID '%s' from %s:%d "
                                "(give it its own ID)" % (v, idn.file.display, idn.line))
            if v.lower() in vanilla_ids and idn.file.origin != 'vanilla':
                self.report.add(ERROR, idn.file, idn.line, 'id',
                                "part ID '%s' clashes with vanilla part %s"
                                % (v, vanilla_ids[v.lower()]))
            if v.lower() in reg and reg[v.lower()][1] is not part:
                o = reg[v.lower()][0]
                self.report.add(ERROR, el.file, el.line, 'id',
                                "part ID '%s' registered twice (also %s:%d)"
                                % (v, o.file.display, o.line))
            else:
                reg[v.lower()] = (el, part)
        # shots
        shot_ids = {}
        nodes_seen = set()
        for rf, line, val, par in L.shot_id_nodes:
            if rf.unreachable:
                continue
            nodes_seen.add(id(par))
            shot_ids.setdefault(_strip_quotes_path(val).lower(), []).append(
                (rf, line, _strip_quotes_path(val), par))
        for rf, node, target in L.bullet_targets:
            t = L.deref(target)
            if rf.unreachable or t is None or id(t) in nodes_seen or \
                    t.file.origin == 'vanilla':
                continue
            nodes_seen.add(id(t))
            idn = L.lookup(t, 'ID')
            if idn is None:
                continue
            if idn.parent is not t and _changes_something(t):
                self.report.add(WARNING, rf, node.line, 'id',
                                "bullet %s changes its base but inherits the base's ID '%s' "
                                "from %s:%d (shots need unique IDs)"
                                % (L._node_desc(t), idn.value, idn.file.display, idn.line))
        vshots = self.vanilla_shot_ids()
        for k, lst in sorted(shot_ids.items()):
            seen_par = []
            uniq = []
            for item in lst:
                if any(item[3] is p for p in seen_par):
                    continue
                seen_par.append(item[3])
                uniq.append(item)
            if len(uniq) > 1:
                first = uniq[0]
                for rf, line, v, par in uniq[1:]:
                    self.report.add(ERROR, rf, line, 'id',
                                    "duplicate shot ID '%s' (also %s:%d)"
                                    % (v, first[0].display, first[1]))
            if k in vshots:
                for rf, line, v, par in uniq:
                    self.report.add(ERROR, rf, line, 'id',
                                    "shot ID '%s' clashes with vanilla %s" % (v, vshots[k]))

    # semantica 2.0 (WP01) ----------------------------------------------------

    def _mod_files(self):
        """Arquivos do mod que o jogo carrega (alcancaveis pelo mod.rules), sem os de textos."""
        return [rf for rf in self.L.files.values()
                if rf.origin == 'fs' and rf.linted and not rf.unreachable and not self.is_strings_file(rf.path)]

    @staticmethod
    def _walk(root):
        stack = [root]
        while stack:
            n = stack.pop()
            yield n
            if n.children:
                stack.extend(reversed(n.children))

    @staticmethod
    def _plain(v):
        """Nome simples (sem referencia/expressao) ou None."""
        if v is None:
            return None
        v = v.strip().strip('"')
        if not v or any(ch in v for ch in '&()<>{}[];= '):
            return None
        return v

    def _vanilla_root(self, rel):
        loc = self.L.vfs.vanilla_lookup(rel)
        return self.L.get_file(loc).root if loc is not None else None

    def _type_of(self, node):
        t = self.L.lookup(node, 'Type')
        return t.value.strip().strip('"').lower() if t is not None and t.kind == 'value' and t.value else None

    def _list_values(self, node):
        out = []
        for el in self.L.list_elements(node):
            el = self.L.deref(el) if el.kind == 'value' and not el.is_str else el
            if el is not None and el.kind == 'value':
                out.append((el, el.value))
        return out

    def _vanilla_part_nodes(self):
        L = self.L
        rf = self._vanilla_root('ships/terran/terran.rules')
        out = []
        if rf is None:
            return out
        t = L.lookup(rf, 'Terran')
        parts = L.lookup(t, 'Parts') if t is not None else None
        for el in (parts.children if parts is not None else []):
            p = L.deref(el)
            if p is not None:
                out.append(p)
        return out

    def _categories_of(self, part):
        tc = self.L.lookup(part, 'TypeCategories')
        if tc is None:
            return set()
        if tc.kind == 'value':
            v = self._plain(tc.value)
            return {v.lower()} if v else set()
        return {self._plain(v).lower() for _n, v in self._list_values(tc) if self._plain(v)}

    def check_semantics(self):
        """Checagens de sentido (WP01): BuffType definido, Category de PartCriteria/Criteria existente, ViaBuffs
        ComponentIDs existentes, ToggleID existente, tipo de NetworkPort do mod com >= 2 pecas."""
        L = self.L
        files = self._mod_files()
        if not files:
            return
        # 1) buffs definidos: vanilla buffs/buffs.rules + Overrides do mod (aplicados em ov_children)
        broot = self._vanilla_root('buffs/buffs.rules')
        buffs = set(_merged_children(L, broot).keys()) if broot is not None else None
        # 2) categorias: TypeCategories das pecas do mod (registradas) e do vanilla
        cats = set()
        for _el, part, _idn in (self.added_parts or []):
            cats |= self._categories_of(part)
        # 3) nomes de componentes: pecas do mod (grupos Components, inclusive aninhados) e do jogo (um ViaBuffs pode
        # juntar um componente vanilla, ex. EngineHeatCollectionStorage)
        comps = set()
        for part in self._vanilla_part_nodes():
            cats |= self._categories_of(part)
            cn = L.lookup(part, 'Components')
            if cn is not None:
                for nm, ch in _merged_children(L, cn).items():
                    comps.add(nm)
                    sub = L.lookup(ch, 'Components') if L.is_grouplike(ch) else None
                    if sub is not None:
                        comps.update(_merged_children(L, sub).keys())
        # 4) ToggleIDs definidos: PartToggles do vanilla e do mod
        toggles = set()
        troot = self._vanilla_root('gui/game/parts/part_toggles.rules')
        for root in ([troot] if troot is not None else []) + [rf.root for rf in files]:
            pt = L.lookup(root, 'PartToggles') if root is not None else None
            if pt is None or not L.is_listlike(pt):
                continue
            for el in L.list_elements(pt):
                e = L.deref(el)
                tid = L.lookup(e, 'ToggleID') if e is not None else None
                if tid is not None and tid.kind == 'value':
                    toggles.add(tid.value.strip().strip('"').lower())
        uses = {'buff': [], 'cat': [], 'via': [], 'toggle': []}
        ports = {}
        for rf in files:
            for n in self._walk(rf.root):
                nm = (n.name or '').lower()
                par = (n.parent.name or '').lower() if n.parent is not None else ''
                if nm == 'components' and n.kind in ('group', 'inherit'):
                    comps.update(c.name.lower() for c in n.children if c.name)
                if n.kind == 'value' and nm == 'bufftype':
                    uses['buff'].append((rf, n, n.value))
                elif nm in ('receivablebuffs', 'incomingbufftypes') and L.is_listlike(n):
                    uses['buff'] += [(rf, e, v) for e, v in self._list_values(n)]
                elif n.kind == 'value' and nm == 'category' and par in ('partcriteria', 'criteria'):
                    uses['cat'].append((rf, n, n.value))
                elif nm == 'categories' and par in ('partcriteria', 'criteria') and L.is_listlike(n):
                    uses['cat'] += [(rf, e, v) for e, v in self._list_values(n)]
                elif nm == 'componentids' and par == 'viabuffs' and L.is_listlike(n):
                    uses['via'] += [(rf, e, v) for e, v in self._list_values(n)]
                elif n.kind == 'value' and nm == 'toggleid':
                    # definicao dentro de PartToggles nao conta como uso; { ID=<componente>; ToggleID="IsRunning" } e
                    # um sub-toggle de componente (vanilla railgun_launcher.rules:267), nao uma PartToggle
                    gp = n.parent.parent if n.parent is not None else None
                    sub = n.parent is not None and 'id' in n.parent.index and 'partid' not in n.parent.index
                    if not sub and not (gp is not None and (gp.name or '').lower() == 'parttoggles'):
                        uses['toggle'].append((rf, n, n.value))
                elif par == 'togglechoicesunlocked' and n.kind == 'list' and n.children:
                    first = n.children[0]
                    if first.kind == 'value':
                        uses['toggle'].append((rf, first, first.value))
                if n.kind in ('group', 'inherit') and n.name and n.parent is not None and \
                        (n.parent.name or '').lower() == 'components' and self._type_of(n) == 'networkport':
                    ty = L.lookup(n, 'Types')
                    part = n.parent.parent
                    for _e, v in (self._list_values(ty) if ty is not None else []):
                        v = self._plain(v)
                        if v and '.' in v:
                            ports.setdefault(v, set()).add((rf.path, id(part)))
        if buffs is not None:
            for rf, n, v in uses['buff']:
                v = self._plain(v)
                if v and v.lower() not in buffs:
                    self.report.add(ERROR, rf, n.line, 'buff',
                                    "BuffType '%s' nao esta definido (buffs/buffs.rules do jogo nem Overrides do mod)" % v)
        for rf, n, v in uses['cat']:
            v = self._plain(v)
            if v and v.lower() not in cats:
                self.report.add(ERROR, rf, n.line, 'category',
                                "Category '%s' de PartCriteria/Criteria nao existe em TypeCategories de nenhuma peca "
                                "do mod nem do jogo" % v)
        for rf, n, v in uses['via']:
            v = self._plain(v)
            if v and v.lower() not in comps:
                self.report.add(ERROR, rf, n.line, 'viabuffs',
                                "ViaBuffs.ComponentIDs cita '%s', que nao e componente de nenhuma peca do mod nem do jogo" % v)
        for rf, n, v in uses['toggle']:
            v = self._plain(v)
            if v and v.lower() not in toggles:
                self.report.add(ERROR, rf, n.line, 'toggle',
                                "ToggleID '%s' nao existe em PartToggles do mod nem do jogo" % v)
        for ty, owners in sorted(ports.items()):
            if len(owners) < 2:
                self.report.add(ERROR, None, 0, 'network',
                                "tipo de NetworkPort '%s' so aparece em %d peca (a rede precisa de >= 2)"
                                % (ty, len(owners)))

    def vanilla_part_ids(self):
        L = self.L
        out = {}
        loc = L.vfs.vanilla_lookup('ships/terran/terran.rules')
        if loc is None:
            return out
        rf = L.get_file(loc)
        for shipname in ('Terran',):
            parts = L.lookup(rf.root, shipname)
            if parts is None:
                continue
            parts = L.lookup(parts, 'Parts')
            if parts is None:
                continue
            for el in parts.children:   # vanilla elements only (not mod overlays)
                p = L.deref(el)
                if p is None:
                    continue
                idn = L.lookup(p, 'ID')
                if idn is not None and idn.kind == 'value':
                    out[_strip_quotes_path(idn.value).lower()] = '%s:%d' % (
                        idn.file.display, idn.line)
        return out

    def vanilla_shot_ids(self):
        L = self.L
        out = {}
        for low, act in L.vfs.vfiles.items():
            if low.startswith('shots/') and low.endswith('.rules'):
                loc = L.vfs.vanilla_lookup(act)
                rf = L.get_file(loc)
                idn = rf.root.index.get('id')
                if idn is not None and idn.kind == 'value':
                    out[_strip_quotes_path(idn.value).lower()] = '%s:%d' % (rf.display, idn.line)
        return out


_CANON = {'addto': 'AddTo', 'toadd': 'ToAdd', 'manytoadd': 'ManyToAdd',
          'overridein': 'OverrideIn', 'overrides': 'Overrides', 'replace': 'Replace',
          'with': 'With', 'remove': 'Remove', 'removemany': 'RemoveMany',
          'addbaseto': 'AddBaseTo', 'basetoadd': 'BaseToAdd'}


def _merged_children(L, node, depth=0):
    """name(lower) -> child, own children overriding inherited ones."""
    out = {}
    if depth > 50:
        return out
    bases = L.bases_of(node)
    for b in reversed(list(bases)):
        out.update(_merged_children(L, b, depth + 1))
    for c in node.children:
        if c.name is not None:
            out[c.name.lower()] = c
    if node.ov_children:
        out.update(node.ov_children)
    return out


class _KeySet(dict):
    """dict key -> line with case-insensitive membership."""

    def __init__(self, d):
        dict.__init__(self, d)
        self._lower = set(k.lower() for k in d)

    def __contains__(self, k):
        return k.lower() in self._lower


def _flatten_keys(root):
    """Leaf string keys (Group/Key) -> line, own children only."""
    out = {}

    def rec(node, prefix):
        for c in node.children:
            if c.name is None:
                continue
            k = prefix + c.name
            if c.kind in ('group', 'inherit'):
                rec(c, k + '/')
            else:
                out[k] = c.line
    rec(root, '')
    return _KeySet(out)


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------

def run_selftest(vfs, report, only_checked_out=False):
    L = Linter(vfs, report, mode='selftest')
    names = sorted(act for low, act in vfs.vfiles.items() if low.endswith('.rules'))
    on_disk = 0
    for act in names:
        if only_checked_out and not os.path.isfile(os.path.join(vfs.vdir, act)):
            continue
        if os.path.isfile(os.path.join(vfs.vdir, act)):
            on_disk += 1
        rf = L.get_file(Loc('vanilla', act))
        if not rf.root.children and not rf.parse_ok:
            report.add(ERROR, rf, 0, 'io', 'could not read file')
            continue
        L.lint_file(rf)
    return L, len(names), on_disk


def run_files(vfs, report, paths):
    L = Linter(vfs, report, mode='files')
    for p in paths:
        loc = vfs.fs_lookup(os.path.abspath(p))
        if loc is None:
            report.add(ERROR, None, 0, 'io', 'file not found: %s' % p)
            continue
        rf = L.get_file(loc)
        L.lint_file(rf)
    return L


def run_mod(vfs, report, mod_dir, langs):
    L = Linter(vfs, report, mode='mod')
    vfs.add_git_worktree(os.path.abspath(mod_dir))
    M = ModLinter(L, mod_dir, langs)
    M.added_parts = []
    M.run()
    return L, M


def print_report(report, show_warnings, max_issues, out=None):
    out = out or sys.stdout
    errs = [i for i in report.issues if i.sev == ERROR]
    warns = [i for i in report.issues if i.sev == WARNING]

    def key(i):
        return (i.display, i.line, i.msg)
    errs.sort(key=key)
    warns.sort(key=key)
    if errs:
        out.write('ERRORS (%d)\n' % len(errs))
        for i in errs[:max_issues]:
            out.write('  ' + i.format() + '\n')
        if len(errs) > max_issues:
            out.write('  ... %d more errors\n' % (len(errs) - max_issues))
    if warns and show_warnings:
        out.write('WARNINGS (%d)\n' % len(warns))
        for i in warns[:max_issues]:
            out.write('  ' + i.format() + '\n')
        if len(warns) > max_issues:
            out.write('  ... %d more warnings\n' % (len(warns) - max_issues))
    return len(errs), len(warns)


DEFAULT_VANILLA = '/home/user/rojamahorse/cosmoteerupdates'


def main(argv=None):
    ap = argparse.ArgumentParser(description='Static validator for Cosmoteer .rules files.')
    ap.add_argument('files', nargs='*', help='.rules files to lint')
    ap.add_argument('--mod', help='mod folder (containing mod.rules)')
    ap.add_argument('--vanilla', help='game Data folder (default: %s or $COSMOTEER_DATA)'
                    % DEFAULT_VANILLA)
    ap.add_argument('--vanilla-selftest', metavar='DIR',
                    help='lint every vanilla .rules file in DIR')
    ap.add_argument('--checked-out-only', action='store_true',
                    help='self-test: skip files only present in git history')
    ap.add_argument('--git-ref', help='git ref for the vanilla file listing')
    ap.add_argument('--langs', default='pt-br',
                    help='comma-separated languages compared with en.rules (mod mode)')
    ap.add_argument('--no-warnings', action='store_true')
    ap.add_argument('--strict-unreachable', action='store_true')
    ap.add_argument('--show-case', action='store_true',
                    help='self-test: list case-only mismatches')
    ap.add_argument('--max-issues', type=int, default=500)
    args = ap.parse_args(argv)

    report = Report()
    report.strict_unreachable = args.strict_unreachable
    vdir = args.vanilla_selftest or args.vanilla or os.environ.get('COSMOTEER_DATA')
    if not vdir and os.path.isdir(DEFAULT_VANILLA):
        vdir = DEFAULT_VANILLA
    if not vdir or not os.path.isdir(vdir):
        sys.stderr.write('error: vanilla Data folder not found; pass --vanilla DIR\n')
        return 2
    vfs = VFS(vdir, args.git_ref)
    try:
        if args.vanilla_selftest:
            L, total, on_disk = run_selftest(vfs, report, args.checked_out_only)
            ne, nw = print_report(report, not args.no_warnings, args.max_issues)
            st = L.stats
            print('SELFTEST: %d .rules files listed (%d checked out), %d parsed'
                  % (total, on_disk, st['files']))
            print('  references: %d/%d resolved; inheritance bases: %d/%d resolved'
                  % (st['refs_ok'], st['refs'], st['bases_ok'], st['bases']))
            print('  assets: %d/%d found; case-only mismatches: %d; virtual paths: %d'
                  % (st['assets_ok'], st['assets'], st['case_notes'], st['virtual']))
            if args.show_case:
                for rf, line, path, notes in L.case_notes:
                    print('  CASE %s:%d %s: %s' % (rf.display, line, path, '; '.join(notes)))
            print('%d error(s), %d warning(s)' % (ne, nw))
        elif args.mod:
            if not os.path.isdir(args.mod):
                sys.stderr.write('error: mod folder not found: %s\n' % args.mod)
                return 2
            langs = [x.strip() for x in args.langs.split(',') if x.strip()]
            L, M = run_mod(vfs, report, args.mod, langs)
            linted = sum(1 for rf in L.files.values() if rf.linted and rf.origin == 'fs')
            unreach = sum(1 for rf in L.files.values() if rf.linted and rf.unreachable)
            ne, nw = print_report(report, not args.no_warnings, args.max_issues)
            st = L.stats
            print('MOD: %d mod .rules files linted (%d not reachable from mod.rules); '
                  '%d files parsed in total (incl. vanilla)'
                  % (linted, unreach, st['files']))
            print('  references: %d/%d resolved; inheritance bases: %d/%d resolved; '
                  'assets: %d/%d found'
                  % (st['refs_ok'], st['refs'], st['bases_ok'], st['bases'],
                     st['assets_ok'], st['assets']))
            print('  parts registered via actions: %d; string keys checked: %d'
                  % (len(M.added_parts), len(L.string_key_uses)))
            print('%d error(s), %d warning(s)' % (ne, nw))
        elif args.files:
            L = run_files(vfs, report, args.files)
            ne, nw = print_report(report, not args.no_warnings, args.max_issues)
            print('%d error(s), %d warning(s)' % (ne, nw))
        else:
            ap.print_help()
            return 2
    finally:
        vfs.close()
    return 1 if report.count(ERROR) else 0


if __name__ == '__main__':
    sys.exit(main())
