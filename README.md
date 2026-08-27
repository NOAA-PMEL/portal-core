# portal-core

Shared base for PMEL data submission portals.

A **portal** is a Dash application where researchers upload data files and describe them with metadata. Every portal shares the same upload wizard, submission grid, file handling, cloning (partially), and user management. What differs is the metadata: Ocean Sites describes NetCDF global attributes and variables; Arctic describes temporal and spatial coverage, platforms, sensors, and parameter keywords.

`portal-core` is everything shared. Your portal is everything else.

- Building a portal on top of base → **you are in the right place**
- Changing base itself → see `MAINTAINING_PORTAL_CORE.md`

---

## The shape of a portal / Your portal's `app.py` file

Base never imports your portal. It receives a `PortalEngine` instance and a config file path, and everything else follows from those two.

```python
# arctic/app.py (your_portal/app.py) -- the entire application entry point
from pathlib import Path
from portal_core import create_app
from arctic.engine import Engine

app = create_app(Engine(), Path(__file__).parent / "config.yaml")
server = app.server

if __name__ == "__main__":
    app.run(debug=True)
```

Everything else your portal contributes is found **by convention** — base discovers files by their location and name. You almost never register anything explicitly.

---

## Getting started

### 1. Install base

```
portal-core @ git+ssh://git@github.com/<org>/portal-core.git@v0.0.3
```

in your portal's `requirements.txt`, then:

```bash
pip install -r requirements.txt --extra-index-url=https://dash-temp.pmel.noaa.gov/Docs/packages
```

The extra index is needed for `dash-design-kit`. Always pin a tag — see [Versioning](#versioning).

### 2. Create the directory structure

```
my-portal/
├── app.py                     # the 5 lines above
├── config.yaml       # branding, contact, deployment settings
├── requirements.txt
├── Procfile
├── engine.py                  # your PortalEngine subclass
├── assets/                    # your CSS/JS, served alongside base's
├── models/                    # your SQLAlchemy tables
│   └── my_portal.py           # replace with your_model.py
├── layouts/                   # one <tab_id>_tab.py per metadata tab
│   └── general_metadata_tab.py # replace with your tabs_tab.py file(s)
├── callbacks/                 # every module defining register_callbacks(app)
│   ├── general_metadata_callbacks.py # replace with your callback file(s)
│   └── save_callbacks.py      # not necessary, but each portal will have to write its own save callbacks
└── utils/                     # your own helpers
```

`example/` in the base repo is a working minimal portal. Copy it's structure.

### 3. Write the engine

```python
from portal_core.engine import PortalEngine

class Engine(PortalEngine):
    name = "my_portal"

    def metadata_tabs(self):
        return [
            {"id": "general_metadata", "label": "General", "icon": "📋"},
            {"id": "coverage",         "label": "Coverage", "icon": "🌍"},
        ]
```

That is a complete, working portal engine. Every other hook has a default that does nothing. Can optionally add these hooks. See below.

### 4. Dash Enterprise setup

Do this once, in teh Dash Enterprise UI, **before teh frist deploy**. 

#### Services

Under the app's **Services** tab, enable both:

| Service | Why |
|---|---|
| **Postgres** | Every table in [Extending the schema](#extending-the-schema). `portal_core.constants.postgres_engine` reads its connection string from teh environment at import.|
| **Redis** | Celery broker for the `workers` and `worker-beat` processes in the `Procfile`. Without it the web process starts but background work silently never runs. | 

Enabling each service injects its connection string as an environment variable
(typically `DATABASE_URL` and `REDIS_URL`). You do not set these by hand.

#### Persistent file storage

Under the **Persistent Filesystem**, enable **persistent filesystem** and note the mount path.

As of 8/27/2026 (before file uploading workflow has been implemented), uploaded data files, archives, bags, and tarballs are written to real directories on disk - `UPLOAD_DIRECTORY`, `ARCHIVE_DIRECOTRY`, `BAG_DIRECTORY`, `TAR_DIRECTORY` in `portal_core.constants`. Without a mounted volume these files won't persist and save. Pleas note after enabling persisten filesystem, you will have to create the directories in `mount/` to save to in the environment (e.g. `../mount/submission/`).

Point the four directory bariables at paths under mount.

#### Environment variables

Under the **Settings -> Environment Variables**, add everything the app reads via `os.environ.get()`. A missing variable surfaces as a startup crash or connection string, not a clear error message.

| Variable | Set by | Notes |
|---|---|---|
| `DATABASE_URL` | Dash Enterprise | Created when you enable Postgres |
| `REDIS_URL | Dash Enterprise | Created when you enable Redis |
| `UPLOAD_DIRECTORY | You | Path under the persistent mount |
| `ARCHIVE_DIRECTORY | You | Path under the persistent mount |
| `BAG_DIRECTORY | You | Path under the persistent mount |
| `TAR_DIRECTORY` | You | Path under the persistent mount |
| `NCEI_<keys> | You | **TODO** Will need to be implemented when this submission feature is implemented (see sftp folder) |

Never commit these values. Keys, passwords, paths should be saved as environment variables.

---

### 5. Database setup

Base needs Postgres and Redis attached, and persistent file storage enabled - see
[Dash Enterprise setup](#dash-enterprise-setup). Do that first; the steps below
assyne the services exist and teh environment variables are set.

#### 1. Stage the ROR reference CSV

The seed step reads a Research Organization Registry CSV and will not download it
for you. (Can get the ror-csv from the portal-core mount directory). Save it somewhere under teh persistent mount **before** running the seed
command, so the path stays valid between deploys and terminal sessions:

```bash
mkdir ~/mount/ror
cp ror-data.csv ~/mount/ror/ror-data.csv
```

#### 2. Create tables

Base's tables plus yours, via `load_models()`:

```bash
# 1. Create tables -- base's plus yours, via load_models()
python -m my_portal.app      # then Ctrl-C
```

#### 3. Seed shared reference data

```bash
portal-seed --ror-csv /path/to/ror-data.csv
```

This populates `research_organization` and the `metadata_role` rows.

#### 4. Run

```bash
python -m my_portal.app
```

The first run logs an error from `_load_metadata_roles()` because the "Data Submitter" and "Investigator" roles don't exist yet. Expected; it goes away after seeding.

---

## Conventions

Base finds your code by name. Get these right and nothing needs registering in the engine.py.

| What | Where | Must define |
|---|---|---|
| Tab layout | `<portal>/layouts/<tab_id>_tab.py` | `create_tab_content()` |
| Callbacks | `<portal>/callbacks/*.py` | `register_callbacks(app)` |
| Models | `<portal>/models/*.py` | classes subclassing `portal_core.models.base.Base` |
| Assets | `<portal>/assets/` | `.css` and `.js` are auto-injected |

Tab ids become module names, so they must be valid Python identifiers — letters, digits, underscores, not starting with a digit. `data_variables` works; `data-variables` and `data variables` do not.

**Every callback module in `callbacks/` is imported and its `register_callbacks(app)` called.** A module without that function is skipped silently. A misspelled `register_callbacks` is the most common reason a portal's callbacks never fire.

Check what base actually resolved — `describe()` is logged at startup:

```
Portal: {'name': 'arctic', 'package': 'arctic', 'tabs': {...}, 'callback_modules': [...]}
```

A tab missing from that output means the file wasn't found.

---

## The Engine

Your subclass of `PortalEngine`. Every hook has a working default, so override only what you need.

### Discovery — usually leave alone

| Hook | Default |
|---|---|
| `load_models()` | Imports every module in `<portal>/models/` so tables register |
| `asset_path()` | Returns `<portal>/assets/` if it exists |
| `describe()` | Diagnostic dict, logged at startup |

### Content

| Hook | Default | Purpose |
|---|---|---|
| `metadata_tabs()` | `[]` | List of `{"id", "label", "icon"}`. The one hook every portal overrides. |
| `tab_content(tab_id)` | convention lookup | Resolution order: `tab_<id>()` on the engine, then `<portal>/layouts/<id>_tab.py`. |
| `register_callbacks(app)` | auto-discovery | Override only if you need explicit control. |

### Slots — inject into base's layout

| Hook | Default | Renders |
|---|---|---|
| `modal_after_header()` | `[]` | Below the metadata modal header |
| `sidebar_tab_extras(tab)` | `[]` | Beside each sidebar tab. Called once per tab; `tab` is that tab's dict. |
| `app_stores()` | `[]` | Extra `dcc.Store` components mounted app-wide |

### Data

| Hook | Default | Purpose |
|---|---|---|
| `clone_metadata(session, original, clone)` | no-op | Copy your extension tables when a submission is cloned. Runs inside base's transaction, after `clone.id` is populated. |

### Escape hatch

For a tab built at runtime with no layout module, define `tab_<tab_id>()` on the engine. It takes precedence over the convention lookup.

---

## Component ids base provides

These are base's UI contract. Your callbacks read and write them, so treat them as a public API — they will not change without a major version bump.

**Namespace your own ids** with a portal prefix (`nc-` for Ocean Sites, `cov-`/`param-` for Arctic). Colliding with a base id produces duplicate-output errors that are hard to trace.

### The four you will use constantly

| Id | Property | What it is |
|---|---|---|
| `current-submission` | `data` | The open submission id. Nearly every portal callback needs this. |
| `btn-save-metadata` | `n_clicks` | Base's save button. Your save callback listens to it. |
| `notifications` | `children` | App-level banner for success/error messages. |
| `metadata-save-status` | `children` | Status line beside the save button. |

### Stores base mounts

| Id | Contains |
|---|---|
| `current-submission` | Open submission id (default `0`) |
| `dashboard-user` | JSON string of the logged-in user, e.g. `{"id": 3}` |
| `metadata-store` | Base's metadata scratch store |
| `metadata-save-store` | Save signalling between base's modal callbacks |
| `open-metadata-store` | Which submission the modal was opened for |
| `newly-uploaded-data-file` | Fires when a data file finishes uploading |
| `file-click-store` | Last file clicked in the grid |
| `edit-click-store` | Last "edit" clicked in the grid |
| `archive-click-store` | Last "archive" clicked in the grid |
| `new-submission-ids` | Ids created in this session |
| `pending-clone-ids` | Awaiting clone confirmation |
| `pending-delete-ids` | Awaiting delete confirmation |
| `selected-submissions` | Checkbox selection in the grid |
| `current-step` | Wizard step number |

### Metadata modal

| Id | Property | Use |
|---|---|---|
| `metadata-modal` | `style` | The modal itself |
| `metadata-modal-overlay` | `style` | Set `{'display': 'none'}` to close |
| `metadata-sidebar` | `children` | Tab list — base builds this from `metadata_tabs()` |
| `metadata-save-status` | `children` | Status line |
| `btn-save-metadata` | `n_clicks` | Save |
| `btn-close-metadata-modal` | `n_clicks` | Close |
| `btn-cancel-metadata-modal` | `n_clicks` | Cancel |
| `btn-open-metadata-modal` | `n_clicks` | Open |

### Upload wizard

| Id | Use |
|---|---|
| `wizard-panel` | Slide-out panel; set `_PANEL_CLOSED` / `_PANEL_OPEN` |
| `wizard-overlay` | Set `_OVERLAY_HIDDEN` / `_OVERLAY_VISIBLE` |
| `wizard-upload-data` | Data file dcc.Upload |
| `wizard-upload-supplemental` | Supplemental file dcc.Upload |
| `wizard-file-list` | Uploaded data files |
| `wizard-supplemental-list` | Uploaded supplemental files |
| `btn-wizard-next`, `btn-wizard-back`, `btn-close-wizard`, `btn-start-submission` | Navigation |
| `step-1-container`, `step-2-container`, `step-3-container` | Step panels |
| `step-title` | Current step heading |

### Grid, confirmations, chrome

| Id | Use |
|---|---|
| `submissions`, `past-submissions`, `new-submission` | Submission grids |
| `files` | File grid |
| `bulk-actions-bar`, `selection-count` | Bulk selection UI |
| `clone-confirm-modal`, `clone-confirm-btn`, `clone-cancel-btn`, `clone-modal-message` | Clone confirmation |
| `delete-confirm-modal`, `delete-confirm-btn`, `delete-cancel-btn`, `delete-modal-message` | Delete confirmation |
| `preview-card`, `preview-plots`, `preview-loader`, `done-preview` | File preview |
| `header`, `user-welcome`, `data-parse-status` | Page chrome |

### Pattern-matching ids base owns

Base uses these with `ALL` selectors. **Do not reuse these `type` values** — your components would be swept into base's callbacks and vice versa.

```python
{'type': 'sidebar-tab',        'index': <tab_id>}
{'type': 'tab-panel',          'index': <tab_id>}
{'type': 'wizard-delete-file', 'index': <file_id>}
```

### Writing a save callback

```python
from portal_core.utils import get_or_create_oads_metadata_id
@app.callback(
    Output('notifications', 'children', allow_duplicate=True),
    Output('metadata-modal-overlay', 'style', allow_duplicate=True),
    Output('wizard-panel', 'style', allow_duplicate=True),
    Output('wizard-overlay', 'style', allow_duplicate=True),
    Input('btn-save-metadata', 'n_clicks'),
    State('current-submission', 'data'),
    # ... your component States
    prevent_initial_call=True,
)
def save_metadata(n_clicks, submission_id, ...):
    ...
    # Almost every save callback will start iwth get_or_create_oads_metadata_id from portal_core.utils.
    oads_id = get_or_create_oads_metadata_id(session=session, submission_id=submission_id)

    return message, {'display': 'none'}, _PANEL_CLOSED, _OVERLAY_HIDDEN
```

Base deliberately does not own saving: the `State()` list is made of your component ids, so only your portal can declare it. Anything base also writes needs `allow_duplicate=True`.

## Helper functions

```python
from portal_core.utils import (
    get_or_create_oads_metadata_id,   # submission_id -> oads_metadata.id, creating if needed
    get_oads_metadata_id,             # lookup only
    insert_submission, insert_file,
    delete_submission, delete_file,
    get_data_files, file_exists,
    get_submissions_with_counts,
    get_submissions_with_file_lists,
    create_submission_id,
    lookup_use_by_email,
    sha256sum, save_file, archive_file,
    make_preview,
    portal_asset_url,
    app_logger,
)
```

`get_or_create_oads_metadata_id(session, submission_id)` is the one nearly every save callback starts with — your extension tables hang off `oads_metadata.id`, not `submission.id`.

### Constants

```python
from portal_core.constants import (
    postgres_engine,
    _OVERLAY_HIDDEN, _OVERLAY_VISIBLE,
    _PANEL_OPEN, _PANEL_CLOSED,
    VISIBLE_BLOCK, HIDDEN_BLOCK,
)
```

The style constants matter for consistency — use `_PANEL_CLOSED` rather than writing your own dict, or your portal's animations will drift from base's.

---

## Extending the schema

### How base's schema is shaped

Base owns 17 tables. The hub is **`oads_metadata`** — one row per submission, holding the generic descriptive fields every portal shares.

```
dashboard_user
    └── submission              (id is a String(16), not an integer)
            ├── file            (data + supplemental files)
            └── oads_metadata   (1:1 -- the hub your tables attach to)
                    ├── related_dataset
                    ├── oads_metadata_investigators   -> person
                    └── oads_metadata_data_submitter  -> person

person
    ├── contact_information -> address
    ├── person_organization -> organization
    └── person_metadata_roles -> metadata_role

research_organization      (ROR reference data, seeded)
```

`oads_metadata` already has: `title`, `abstract`, `doi`, `doi_requested`, `use_limitation`, `purpose`, `data_license`, `publication_year`, `dataset_version`, `publisher_name`, `publisher_location`, `submission_date`.

### Attach your tables to `oads_metadata.id`

```python
from typing import Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from portal_core.models.base import Base


class MyPortalCoverage(Base):
    __tablename__ = "my_portal_coverage"

    id: Mapped[int] = mapped_column(primary_key=True)
    oads_metadata_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("oads_metadata.id", ondelete="CASCADE"), index=True
    )
    start_date: Mapped[Optional[str]] = mapped_column(String(32))
```

Four things matter here:

**Subclass `portal_core.models.base.Base`.** That single `DeclarativeBase` holds the metadata registry for base and every portal. Defining your own would mean `create_all` never sees your tables.

**FK to `oads_metadata.id`, not `submission.id`.** This is the one that bites. Base's clone flow copies the Submission *and* creates a new OadsMetadata row, then calls `clone_metadata(session, original, clone)` where `original` and `clone` are OadsMetadata rows. If your table hangs off `submission.id`, your clone code has the wrong anchor and you'll be re-deriving it every time.

**`ondelete="CASCADE"`.** Deleting a submission should take your rows with it. Without this you accumulate orphans that nothing cleans up.

**Prefix your table names.** Base's tables and every portal's tables share one database. `coverage` will collide; `arctic_coverage` will not.

### Nothing imports your models file

`load_models()` walks `<portal>/models/` and imports every module, which is enough for SQLAlchemy to register the classes. Then `init_db()` calls `create_all`. Put the file in the right directory and it works.

### Never modify base tables

Adding a column to `oads_metadata` for one portal's benefit means editing base, which changes the schema for every portal. If you need a field:

1. Is it generic? Use an existing `oads_metadata` column.
2. Is it portal-specific? Put it in your own table.
3. Is it genuinely generic and missing? That's a base change — a schema migration affecting every portal, and a conversation, not a commit.

### Sessions

Two mechanisms exist and they are not interchangeable:

```python
# In callbacks and portal code -- open, use, close
from sqlalchemy.orm import Session
from portal_core.constants import postgres_engine

with Session(postgres_engine) as session:
    oads_id = get_or_create_oads_metadata_id(session, submission_id)
    ...
    session.commit()
```

Base also configures a Flask-SQLAlchemy `db` (`portal_core.models.shared`) for request-scoped work. Use the explicit `Session` form in callbacks — Dash callbacks are not always inside a Flask request context, and a module-level session shared across requests goes stale after any failed transaction.

### Cloning your tables

```python
def clone_metadata(self, session, original, clone) -> None:
    for row in session.query(MyPortalCoverage).filter_by(
        oads_metadata_id=original.id
    ):
        session.add(MyPortalCoverage(
            oads_metadata_id=clone.id,
            start_date=row.start_date,
        ))
```

Runs inside base's transaction, after base has flushed — so `clone.id` is populated. Do not commit; base does.

If your portal has several tables, clone them in FK order: parents before children, flushing between so child rows can reference new parent ids.

## config.yaml

Deployment settings only — things a person installing this portal might change without writing Python. Anything requiring code belongs on the Engine.

```yaml
branding:
  organization_name: "Pacific Marine Environmental Laboratory"
  organization_short_name: "PMEL"
  page_title: "Scientific Data Information System"
  version: "v0.0.3"
  header_logo: "my-logo.svg"        # filename in <portal>/assets/
  footer_logo: "my-logo.svg"

contact:
  email: "oar.pmel.webmaster@noaa.gov"
  footer_links:
    organization:
      text: "Pacific Marine Environmental Laboratory"
      url: "https://www.pmel.noaa.gov/"
    parent_org:
      text: "National Oceanic and Atmospheric Administration"
      url: "https://www.noaa.gov/"
    legal_links:
      - text: "NOAA"
        url: "https://www.noaa.gov/"

allow_multiple_data_files_to_submit: False

submission_archives:
  - key: ncei
    icon: '🏛️'
    label: 'NCEI'
    enabled: true
```

All keys are required except `submission_archives`. A missing key raises `KeyError` at startup.

---

## Deploying

`Procfile` at your portal's repo root:

```
web: gunicorn my_portal.app:server --workers 4
workers: celery -A portal_core.app_factory:celery_app worker --loglevel INFO --concurrency=4
worker-beat: celery -A portal_core.app_factory:celery_app beat
```

`gunicorn my_portal.app:server` needs `server = app.server` on its own line in `app.py`.

Do **not** add `--preload` without reading the note in `portal_core/constants.py` — the database connection pool is created at import, and preloading would share connections across forked workers.

---

## Versioning

Pin a tag:

```
portal-core @ git+https://git@github.com/<org>/portal-core.git@v0.0.3
```

Upgrading is a deliberate act: edit the tag, reinstall, test, commit. Portals are not expected to upgrade together — one portal sitting on an older release while another moves ahead is the system working as intended.

- **patch** — bug fix, no contract change
- **minor** — new hook with a default; your portal is unaffected
- **major** — a hook changed or was removed; read the changelog before upgrading

---

## When something goes wrong

| Symptom | Cause |
|---|---|
| `No module named 'portal_core'` | Not installed, or wrong virtualenv. `pip show portal-core`. |
| `No module named 'my_portal'` | Ran `python my_portal/app.py`. Use `python -m my_portal.app` from the repo root. |
| `RuntimeError: Config not initialized` | Something ran before `create_app()`. Config reads must be inside functions, not at module level. |
| Tab missing, no error | Convention didn't resolve. Check the `describe()` log and the filename. |
| Callbacks never fire | Module doesn't define `register_callbacks(app)`, or it's misspelled. |
| Duplicate output error | Two callbacks write the same component. Add `allow_duplicate=True`, or your id collides with a base id. |
| `KeyError` at startup | `config.yaml` is missing a required key. |
| App runs unstyled | Base installed without its assets — check the wheel was built with `package-data`. |

The `example/` portal in the base repo is a working reference for every hook. When something isn't behaving, compare against it.
