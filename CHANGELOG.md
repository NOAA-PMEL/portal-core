# Changelog

All notable changes to `portal-core`.

Versions follow the contract rule: **major** means a hook changed or was removed
and portals must migrate; **minor** means a new hook with a working default, so
existing portals are unaffected; **patch** means a bug fix with no contract change.

## v0.1.0 - 2026-08-26

First release as a standard packaged. Everything before this lived in the 
combined `arctic-data-submit` repo and was not installable. 

### Added
- `create_app(portal, config_path)` as the single entry point. A portal's
`app.py` is now about five lines.
- `pyproject.toml`; base installs with `pip install portal-core`.
- `example/`, a minimal reference portal exercising every hook.
- `portal_core.seed_ror_and_roles(ror_csv)`.
- README covering the Engine contract, base's component ids, and how to extend
the schema.

### Changed
- All base code namespaced under `portal-core` (was top-level `models`,
`utils`, `layouts`, `callbacks`, `constants`, `engine`).
- Config is passed to `create_app()` instead of read from the working
direcotry. Each portal owns its `config.yaml`.
- Engine hook parameters renamed from `engine` to `portal` where they mean a 
`PortalEngine`, to distinguish them from the SQLAlchemy engine.

### Removed
- The unused `ctx` paramewter from `tab_content()`, `modal_after_header()`, and
`app_stores()`. Base alwasy passed an empty dict and not portal read it. If 
context is needed later it can be reintroduced with a default, without
breaking the existing portals.
- The legacy Flask/Jinja routes and WTForms forms, replaced by the Dash tab
system. `wtforms` and `wtforms-alchemy` are no longer dependencies.
- Dead config keys (`models`, `slots`) - models are discovered by convention.

### Known issues
- Deploy-time installation from a git URL is untested; the first portal deploy
after splitting out of the original `arctic-data-submit` repo is the real test.
- Base has no automated tests. `example/` is the only regression check. Will
add this after split.

## v0.1.1 - 2026-08-31

### Fixed
- Circular import in `portal-core/utils/clone_submission.py`, which imported
from the `portal_core.utils` package while that package's `__init__.py` was 
still executing. Now imports the sibling modules directly.
