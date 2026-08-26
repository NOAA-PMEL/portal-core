"""
engine.py
=========

The contract between base code and a portal.

Base never imports a portal. It receives an Engine instance and calls methods
on it. Every hook returns something empty by default, so base can call any hook
unconditionally. (A hook is a placeholder that allows you to inject custom code 
into an existing program, framework, or runtime cycle without modifying its core 
source code.)

SEVEN HOOKS
---------
    metadata_tabs()             which tabs exist                    <- always explicit
    tab_content()               what's in each tab                  <- by convention
    modal_after_header()        slot below metadata modal header    <- explicit
    sidebar_tab_extras()        slot in sidebar tab item            <- explicit
    register_callbacks()        this portal's callbacks             <- by convention
    app_stores()                which stores at the app-level       <- explicit
    clone_metadata()            how to clone the metadata           <- explicit

tab_content() and register_callbacks() resolve automatically from the portal's file
layout, so a portal that follows the convention writes neither.

CONVENTIONS
-----------
For a portal package 'ocean_sites' with a tab id "data_variables", for example:

    tab_content     ->  ocean_sites/layouts/data_variables_tab.py
                        must define create_tab_content()
    callbacks       ->  every module in ocean_sites/callbacks/
                        each may define register_callbacks(app)

Adding a tab means: one dict in metadata_tabs(), one layout module, one callbacks
module. Nothing to register.

Escape hatches: define 'tab_<id>()' on the engine to override one tab, or override
'register_callbacks()' for explicit registration.

A portal subclasses PortalEngine and overrides only what it needs.

8/11/2026: SEVEN HOOKS. Do not add another hook until a portal actually needs base 
to change in a place it can't reach. The moment -- "portal 3 needs to edit a file
in base" -- is the signal, and adding a hook then is non-breaking because the 
default is already correct for every existing portal.

Conventions (things that need to be followed rather than configured):
    * Hook names. Base calls `modal_after_header`; you name your subclass method 
      that.
    * A 'tab_<id>()' method on the engine overrides the layout file for that one
      tab. Use it only for tabs build at runtime.
"""

from __future__ import annotations

from typing import Any
from pathlib import Path
import importlib
import pkgutil


class PortalEngine:
    """
    Base class of a portal engine.

    Only `name` really needs overriding. Everything else defaults to the
    behavior of a plain, unextended portal.
    """
    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------
    name: str = "base"

    # -- Convention knobs. Rarely changed here so a portal CAN differ. --
    layouts_package: str = "layouts"
    callbacks_package: str = "callbacks"
    models_package: str = "models"
    layout_tab_module_suffix: str = "_tab"
    layout_tab_function: str = "create_tab_content"
    callback_function: str = "register_callbacks"
    assets_dir_name: str = "assets"

    # -------------------------------------------------------------------------
    # Internal: locate the portal package this engine belongs to
    # -------------------------------------------------------------------------
    @classmethod
    def _portal_package(cls) -> str | None:
        """
        The package CONTAINING this engine's module, or None.

        `ocean_sites.engine`               -> `ocean_sites`
        `portals.ocean_sites.engine        -> `portals.ocean_sites`

        Taking the parent package rather than the root means this works both
        while portals live inside the base repo and after they're split into 
        their own repos -- the engine just has to sit in the same package as 
        its layouts/ and callbacks/ directories.

        Returns None when the engine is a top-level module with no package.
        That's the normal case for base's own PortalEngine during migration,
        when engine.py sits beside app.py at the repo root and nothing has
        subclassed it yet. Callers decide whether that's fatal: resolving a 
        declared tab is (there's a tab that must render), auto-registering
        callbacks isn't (a portal with no callbacks is legal.)
        """
        module = cls.__module__
        if "." not in module or module.startswith("portal_core."):
            return None
        return module.rsplit(".", 1)[0]

    # -------------------------------------------------------------------------
    # Models
    # -------------------------------------------------------------------------
    def load_models(self) -> None:
        """
        Import every module in <portal>/models/ so tables register Base.metadata.

        Base MUST import its own models before calling this: portal models
        subclass base's Base and declare FKs to oads_metadata_id.

        Replaces: the `models:` list in the config
        """
        package = self._portal_package()
        if package is None: 
            return
        package_name = f"{package}.{self.models_package}"
        try:
            pkg = importlib.import_module(package_name)
        except ModuleNotFoundError as exc:
            if exc.name != package_name:
                raise
            return
        for info in sorted(pkgutil.iter_modules(pkg.__path__), key=lambda i: i.name):
            if not info.name.startswith("_"):
                importlib.import_module(f"{package_name}.{info.name}")
 
    # -------------------------------------------------------------------------
    # Assets
    # -------------------------------------------------------------------------
    def asset_path(self) -> Path | None:
        """
        <portal>/assets/ as a filesystem path, else None if there isn't one.
        Directory of portal-owned CSS/JS/PNG/etc., served alongside base assets.

        By convention: assets/ next to the engine module. Returns None if 
        absent.
        """
        pkg = self._portal_package()
        if pkg is None:
            return None
        module = importlib.import_module(pkg)
        path = Path(list(module.__path__)[0]) / self.assets_dir_name
        return path if path.is_dir() else None

    # -------------------------------------------------------------------------
    # 1 + 2. Tabs - replaces the `tabs` block in the config.yaml file
    # -------------------------------------------------------------------------
    def metadata_tabs(self) -> list[dict[str, Any]]:
        """
        Which tabs the metadata modal shows, in order.

        Each dict is at minimum {"id": str, "label": str}; "icon" optional.

        Tab ids must be valid Python identifiers, because content is
        dispatched to a method named `<tab_id>_tab` by convention.

        After talking with Roland on 8/12/2026, decided to keep this method
        instead of moving into convention (into the tab layout files themselves), 
        because while the tab_id and label could be gathered from the associated 
        filenames, the icon can't easily be found. glob discovery makes the tab 
        list invisible, and you lose the one place to see the whole modal at a glance.
        Also adding a tab means writing a whole layout module and a callbacks module.
        A deployer can't do that from a YAML, so the tab list isnt' a deployment 
        value - it's part of the portal's code. Splitting it into config.yaml
        means one concept lives in two files that must stay in sync.
        """
        return [] 

    def tab_content(self, tab_id: str) -> Any | None:
        """
        The content panel for one tab.

        Resolution order:
            1. `tab_<tab_id>()` if defined -- runtime/dynamic escape hatch
            2. `<portal>/layouts/<tab_id>_tab.py` -> create_tab_content()

        A portal following the convention writes neither.
        """
        override = getattr(self, f"tab_{tab_id}", None)
        if callable(override):
            return override()
        
        package = self._portal_package()
        if package is None:
            raise RuntimeError(
                f"Can't resolve tab {tab_id!r}: {type(self).__name__} is a "
                f"top-level module ({type(self).__module__}.py) with no "
                f"package, so there's no layouts/ directory to look in. Put "
                f"the engine inside a package, e.g. ocean_sites/engine.py"
            )

        module_name = (
            f"{package}.{self.layouts_package}"
            f".{tab_id}{self.layout_tab_module_suffix}"
        )

        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            # Only swallow "the tab module itself is missing". A failed import
            # INSIDE the module is a real bug and must not be reported as a 
            # missing tab
            if exc.name != module_name:
                raise
            raise RuntimeError(
                f"Tab {tab_id!r} has no layout. Expected "
                f"{module_name.replace('.', '/')}.py defining "
                f"{self.layout_tab_function}(), or tab_{tab_id}() method on "
                f"{type(self).__name__}."
            ) from exc

        fn = getattr(module, self.layout_tab_function, None)
        if fn is None:
            raise RuntimeError(
                f"{module_name} exists but defines no {self.layout_tab_function}(). "
                f"Every tab layout module must define that function."
            )

        return fn()

    # -------------------------------------------------------------------------
    # 3 + 4. Slots - injection points in base's modal chrome
    #
    # These exist because Ocean Sites needed to add components to parts of the
    # modal that aren't inside any tab. Named by POSITION, not by feature, so 
    # they stay reusable: `modal_after_header`, never `changes_bar_slot`.
    #
    # Both return a LIST so base can splat with *. Empty list = render nothing.
    # Replaces: the `extension_points.modal_after_header` block in config.yaml.
    # -------------------------------------------------------------------------
    def modal_after_header(self) -> list[Any]:
        """
        Components inserted directly below the metadata modal header.

        Ocean Sites uses this for the changes bar. Arctic returns [].
        """
        return []

    def sidebar_tab_extras(self, tab: dict[str, Any]) -> list[Any]:
        """
        Components appended inside a single sidebar tab item.

        Called once per tab. `tab` is that tab's dict from metadata_tabs(),
        so output can vary per tab -- Ocean Sites uses it for the per-tab 
        change-count badge.
        """
        return []

    # -------------------------------------------------------------------------
    # 5. Callbacks.
    # 
    # Replaces: the `for tab in metadata_tabs: tab['callbacks_fn'](app)`
    # loop and the `save_callbacks(app)` call in callbacks/__init__.py
    # -------------------------------------------------------------------------
    def register_callbacks(self, app) -> None:
        """
        Register every Dash callback this portal owns.

        Default: import every module in `<portal>/callbacks/` and call its
        `register_callbacks(app)` if it defines one. Modules without that
        function are skipped, so helpers can live there safely.

        Covers tab callbacks, save callbacks and slot callbacks uniformly --
        there's no separate mechanism for callbacks that don't belong to a tab.

        This half must travel with the layout: base cannot own a callback for 
        `sidebar-tab-count   because that ID only exists when this engine's 
        sidebar_tab_extras() rendered it. 

        Base registers its shared callbacks first, then calls this.

        Order is alphabetical by module name. Dash callbacks are order-independent,
        so it shouldn't matter; override this method for explicit registration
        if a portal ever needs a specific order.

        Replaces: the `for tab in metadata_tabs: tab['callbacks_fn'](app)`
        loop and the `save_callbacks(app)` call in callbacks/__init__.py.
        """
        portal_package = self._portal_package()
        if portal_package is None:
            return None # bare PortalEngine at the repo root: nothing to load

        package_name = f"{portal_package}.{self.callbacks_package}"

        try:
            package = importlib.import_module(package_name)
        except ModuleNotFoundError as exc:
            if exc.name != package_name:
                raise
            return None # a portal with no callbacks at all is legal

        for info in sorted(
            pkgutil.iter_modules(package.__path__), key=lambda i: i.name
            ):
            if info.name.startswith("_"):
                continue
            module = importlib.import_module(f"{package_name}.{info.name}")
            fn = getattr(module, self.callback_function, None)
            if callable(fn):
                fn(app)
    
    # -------------------------------------------------------------------------
    # 6. Data
    # -------------------------------------------------------------------------
    def app_stores(self) -> list[Any]:
        """
        dcc.Store components this portal needs at app level.

        Base mounts its own shared stores first, then splats these in.

        For stat the lives outside the metadata modal -- written by upload
        callbacks, read on submission switch. Stores scoped to a single tab 
        belong inside that tab's creat_tab_content() instead.
        """
        return []

     # -------------------------------------------------------------------------
    
    # 7. Cloning
    # -------------------------------------------------------------------------
    def clone_metadata(self, session, original, clone) -> None:
        """
        Copy this portal's extension tables from one metadata record to another.

        Base has already cloned the Submission, the OadsMetadata row, and the 
        shared person links, and has flushed -- so 'clone.id' is populated.

        'original' and 'clone' are both OadsMetadata rows.

        Runs inside base's transaction, before commit. Raising here rolls the
        whole clone back, which is right: a submission cloned without its
        portal metadata is worse than a clone that failed loudly.

        A portal with no extension tables doesn't override this.
        """
        return None
    
    # -------------------------------------------------------------------------
    # Diagnostics
    # -------------------------------------------------------------------------
    def describe(self) -> dict[str, Any]:
        """
        What this engine actually resolved to. Load at startup in debug.

        Convention fails silently by nature -- a misnamed file just doesn't
        load. This makes the resolution visible, so "why isn't my callback
        firing" has an answer that doesn't involve reading base's source.
        """
        pkg = self._portal_package()
        if pkg is None:
            return {"name": self.name, "package": None, "tabs": [],
                    "callback_modules": [], "app_stores": []}

        tabs = []
        for tab in self.metadata_tabs():
            tab_id = tab["id"]
            if callable(getattr(self, f"tab_{tab_id}", None)):
                source = f"{type(self).__name__}.tab_{tab_id}()"
            else:
                source = (
                    f"{pkg.replace('.', '/')}/{self.layouts_package}/"
                    f"{tab_id}{self.layout_tab_module_suffix}.py"
                )
            tabs.append({"id": tab_id, "layout": source})

        callbacks: list[str] = []
        package_name = f"{pkg}.{self.callbacks_package}"
        try:
            package = importlib.import_module(package_name)
            for info in sorted(
                pkgutil.iter_modules(package.__path__), key=lambda i: i.name
                ):
                if info.name.startswith("_"):
                    continue
                module = importlib.import_module(f"{package_name}.{info.name}")
                if callable(getattr(module, self.callback_function, None)):
                    callbacks.append(info.name)
        except ModuleNotFoundError:
            pass

        stores = []
        for s in self.app_stores():
            sid = getattr(s, "id", None)
            stores.append(sid if sid is not None else f"<{type(s).__name__} with no id>")

        return {
            "name": self.name,
            "package": pkg,
            "tabs": tabs,
            "callback_modules": callbacks,
            "app_stores": stores
,        }

    # -------------------------------------------------------------------------
    def __repr__(self) -> str: 
        return f"<{type(self).__name__} name={self.name!r}"

