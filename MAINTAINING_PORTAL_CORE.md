# Maintaining `portal-core`

The folder inside this repo called `portal_core` is a **library**. Nothing here is deployed. Portals install it and extend it.
The folder `example/` in this repo is deployed as a test ground for any updates to base/portal-core.

If you are looking for how to build a portal *on top of* this, see `README.md`. This document is for changing base itself.

---

## The one rule

**Base never imports a portal.**

Base learns about a portal only through the `PortalEngine` object it is handed at startup. If you find yourself wanting `from arctic...` anywhere in `portal_core/`, the answer is a new hook on the Engine, not an import.

That single constraint is what lets five portals share this code without becoming five forks of it.

---

## Repo layout

```
portal-core/
├── portal_core/          # the package — this is what ships
│   ├── engine.py         # the contract every portal implements
│   ├── app_factory.py    # create_app()
│   ├── config_loader.py
│   ├── assets/
│   └── ...
├── example/              # the test portal — does NOT ship
├── pyproject.toml        # dependencies and packaging (the real list)
├── requirements.txt      # two lines; points at pyproject.toml for DE
├── README.md             # for portal developers
├── MAINTAINING_PORTAL_CORE.md
└── CHANGELOG.md
```

`example/` is excluded from the built package by `include = ["portal_core*"]` in `pyproject.toml`. It exists only so base has something to run against.

---

## Prerequisites

A workspace provisions itself from `requirements.txt`, which does an editable
install of this project. After a workspace rebuild you should not need to run
`pip install` by hand -- check with:

  `cd /tmp && python -c "import portal_core; print(portal_core.__file__)"`

That should print a path inside your repo. If it fails, run
`pip install -e ".[dev]"` from the repo root.

Base needs Postgres and Redis attached. First run on a fresh database:

  `python -m example.app`   # create tables, then Ctrl + C
  `python -m portal_core.seed.ror_and_roles --ror-csv /path/to/ror-data.csv` # csv path in portal-core is in mount
  `python -m example.app`   # now clean

The first run logs an error from _load_metadata_roles() -- the two roles don't exist
yet. It's expected and goes away after seeding.

## The example portal is your only in-repo test

This is the thing to understand about maintaining base alone: **there are no real portals here to catch your mistakes.** You can break Arctic's clone flow, run everything in this repo, and see green.

So `example/` has to earn its keep. It should override **every hook on `PortalEngine`**, minimally — not because a real portal would, but because an unexercised hook is an untested hook:

| Hook | What example should do |
|---|---|
| `metadata_tabs()` | Return 2 tabs, so tab switching is exercised |
| `tab_content()` | Rely on the convention for one tab, override for the other |
| `register_callbacks()` | Rely on auto-discovery |
| `modal_after_header()` | Return one trivial component |
| `sidebar_tab_extras()` | Return one trivial component |
| `app_stores()` | Return one store |
| `clone_metadata()` | Copy one field |
| `asset_path()` | Ship one CSS file that visibly changes something |
| `load_models()` | Ship one model, discoverd by convention |

If a hook has no example coverage, assume a change to it is untested.

Run it as the first step of every change:

```bash
python -m example.app
```

Check the `describe()` log line at startup. It lists which modules the convention resolved. A tab silently missing there means the file wasn't found — usually a filename typo or a missing `create_tab_content`.

---

## The daily loop

You are running an editable install, so **editing code does not require reinstalling**.

```
1. Edit portal_core/
2. python -m example.app
3. Pre-commit checks (below)
4. Commit
```

### When you DO need to reinstall

`pyproject.toml` is only read at install time. After changing it:

```bash
pip install -e . --no-deps
```

Needed after: adding/removing a dependency, bumping `version`, changing a `[project.scripts]` entry, changing `package-data` or `packages.find`, or adding a new top-level directory under `portal_core/`.

**If you added or removed a dependency, drop `--no-deps`:**

```bash
pip install -e ".[dev]"
```

`--no-deps` skips dependency resolution, which is faster and can't disturb a 
working environment - but it also means a newly added dependency never gets
installed.

A workspace rebuild reinstalls automatically via `requirements.txt`, so this is 
mainly for changes you make mid-session.

---

## Deploying the example portal

`example/` deploys as a live reference - a URL where anyone can see what a 
minimal portal looks like, and a canary that catches breakage without a portal 
team having to report it. 

`Procfile`:

```
web: gunicorn example.app:server --workers 2
workers: celery -A portal_core.app_factory:celery_app worker --loglevel DEBUG --concurrency=2
worker-beat: celery -A portal_core.app_factory:celery_app beat
```

Deploying pushes the whole repo, so `example/` being excluded from teh built
wheel does not affect it.

This is the only thing in this repo that deploys. Base itself is a library.

---

## Before you commit

```bash
# 1. Base must not import a portal
grep -rnE "^(from|import) (example)" portal_core/

# 2. Nothing computes a path by walking OUT of its own folder
grep -rn "parents\[" portal_core/

# 3. No un-namespaced internal imports
grep -rnE "^(from|import) (config_loader|constants|db_setup|engine|extensions|models|utils|layouts|callbacks|routes|forms|sftp|seed)\b" \
  --include="*.py" portal_core/ example/
```

All three empty.

Check 2 matters more than it looks. Code that locates a file by counting directories upward from itself works when everything is in one repo and breaks the instant base is installed into someone's `site-packages`. **Paths are passed in, never computed.** This bug has already appeared twice before (`config.yaml`, the ROR CSV).

---

## Changing the Engine contract

The Engine is a published interface. Portals you cannot see depend on it.

### Adding a hook — safe

Add it to `PortalEngine` **with a working default that does nothing**:

```python
def footer_extras(self):
    """Optional. Extra components in the footer. Default: none."""
    return []
```

Every existing portal keeps working without touching a line. Base calls it unconditionally — no `hasattr`, no `if`. That is the whole discipline: every engine answers every question, some just answer "nothing."

Then: document it in the `engine.py` header, add it to `describe()`, override it in `example/`, update the README.md, and bump the **minor** version.

Add a hook as soon as one portal needs it. If a portal cannot do what it needs without editing the base - that is a sign that a new hook needs to be added (e.g. adding another header in the metadata_modal layout that won't be used by another portal, so a portal needs to be able to inject it (a slot) into the base layout code.) First check that a hook is actually required. Most portal-specific work - new metadata tabs, callbacks, models, assets - already lives entirely in the portal and needs nothing from the base. The trigger for a hook is: base's own control flow has to do something different, and there is no existing hook that expresses it. The cost of a hook is that you keep it forever, so give it a working default and the smallest signature that does the job.

### Changing or removing a hook — breaking

Changing a signature or removing a hook breaks portals silently, because duck typing means nothing checks. If you must:

1. Add the new hook alongside the old one
2. Make the old one's default delegate to the new one
3. Log a deprecation warning when a portal overrides the old one
4. Bump the **major** version
5. Remove the old one only after every known portal has migrated

### Never

- `hasattr(engine, ...)` in base — that's a hook without a default, and it rots
- Branching on `engine.name` — if base needs to know which portal it is, the design has failed
- Reading portal-specific keys out of the config

---

## Testing against a real portal

`example/` will not catch everything. Before releasing anything non-trivial, run a real portal against your unreleased base:

```bash
cd ~/arctic-portal
pip install -e ~/portal-core --no-deps   # point at your working copy
python -m arctic.app
```

Restore afterwards:

```bash
pip install -r requirements.txt
```

This needs a portal checkout and a database, so it's not part of the daily loop — but it is part of the release process. `example/` tells you base is internally consistent; only a real portal tells you the contract still holds.

Worth checking against whichever portal exercises the most hooks. Today (August 21, 2026) that's Arctic.

---

## Releasing

### 1. Test

```bash
python -m example.app
```

Then run at least one real portal against this working copy (see "Testing
against a real portal" above). `example/` proves base is internally consistent;
only a real portal proves the contract still holds.

### 2. Decide the version

- **patch** (v0.1.0 → v0.1.1) — bug fix, no contract change
- **minor** (v0.1.0 → v0.2.0) — new hook with a working default; existing
  portals unaffected
- **major** (v0.1.0 → v1.0.0) — a hook changed or was removed; portals must
  migrate before upgrading

### 3. Update `pyproject.toml` and `CHANGELOG.md`

Bump `version` in `pyproject.toml`, then add a section at the top of
`CHANGELOG.md`:

```markdown
## v0.2.0 — 2026-09-15

### Added
- `footer_extras()` hook for injecting components into the footer.

### Changed
- ...

### Removed
- ...
```

Write it for the portal developer who will read it while deciding whether to
upgrade. "Added footer_extras() hook" is useful; "various improvements" is not.

### 4. Reinstall

```bash
pip install -e . --no-deps
```

`pyproject.toml` is only read at install time, so the version bump isn't live
until you do this.

### 5. Verify what ships

```bash
python -m build --no-isolation
python -c "
import zipfile, glob
names = zipfile.ZipFile(glob.glob('dist/*.whl')[0]).namelist()
print('assets:', [n for n in names if 'assets' in n])
leaked = [n for n in names if any(x in n for x in ('example','test'))]
print('LEAKED:', leaked if leaked else 'none — good')
print('total:', len(names))
"
```

Expect 6 assets, no leaks, roughly 58 files.

### 6. Commit and push — before tagging

```bash
git add CHANGELOG.md pyproject.toml
git commit -m "Release v0.2.0"
git push
```

**This must happen first.** A tag points at a commit. Tagging before committing
the version bump produces a tag whose `pyproject.toml` still says the old
number, and pushing a tag does not push the commit underneath it.

### 7. Create the tag

**Preferred — GitHub Releases.** This creates the tag *and* publishes the notes
where portal developers can find them without cloning:

1. Repo → **Releases** → **Draft a new release**
2. **Choose a tag** → type `v0.2.0` → **Create new tag on publish**
3. Target: `main`
4. Release title: `v0.2.0`
5. Description: paste this version's section from `CHANGELOG.md`
6. **Publish release**

**Or from the terminal** (works fine in a DE workspace):

```bash
git tag v0.2.0
git push origin v0.2.0
```

Either way the result is the same tag, and `pip install ...@v0.2.0` works.

### 8. Tell the portals

Each portal upgrades on its own schedule by editing its `requirements.txt`:

portal-core @ git+https://github.com/<org>/portal-core.git@v0.2.0

then `pip install -r requirements.txt`, test, commit, deploy. The upgrade is a
commit in the *portal's* history, which is what makes it traceable later.

**Do not expect portals to upgrade together.** Arctic sitting on v0.1.0 for a
month while Ocean Sites runs v0.2.0 is the system working as designed.

### Never move a tag

If v0.2.0 has a bug, release v0.2.1. Force-pushing a tag means someone who
installed v0.2.0 last week and someone installing it today get different code,
which destroys the only guarantee a tag provides.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `No module named 'example'` | Not in the repo root. `example/` is excluded from the package, so it's only findable from there. |
| `No module named 'portal_core'` | Editable install didn't take, or wrong virtualenv. `pip show portal-core`. |
| `No module named 'app_factory'` | Ran `python example/app.py` instead of `python -m example.app`. The path form puts the wrong directory on the search path. |
| `RuntimeError: Config not initialized` | Something reached `get_config()` before `create_app()` ran — usually a config read that drifted to module level. |
| Runs but unstyled | `package-data` missing; assets didn't ship. |
| Tab missing, no error | Convention didn't resolve the file. Check the `describe()` log. |
| A portal broke after upgrading base | Compare the two tags. If a hook signature changed, that needed a major bump. |
| `_load_metadata_roles()` errors on a fresh database | seed ror_and_roles (see prerequisites above) |
| Edits to `portal-core/` have no effect | Non-editable install is active. Run `pip uninstall portal-core -y && pip install -e . --no-deps` |

---

## The one-sentence version

Base is a library that knows nothing about any specific portal; portals hand it an `Engine` and a config path at startup; every hook has a working default so adding one never breaks anyone.
