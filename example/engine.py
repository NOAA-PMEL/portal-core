"""
The reference portal. 

This exists to exercise EVERY hook on PortalEngine, so that a change to base
fails here rather than in a portal repo much later after a change in the python
package has been released and implemented into a portal-specific repo.

It is deliberately minimal in content and maximal in coverage. Each override
does the smallest thing that proves the hook is wired up. Nothing here is a 
model of good portal design; see arctic/ or ocean_sites/ for that. 

COVERAGE MAP
------------
    load_models()           convention  ->  example/models/*.py
    asset_path()            convention  -> example/assets/
    metadata_tabs()         overridden  -> 3 tabs
    tab_content()           all three resolution paths (see metadata_tabs)
    modal_after_header()    overriden   ->  banner
    sidebar_tab_extras      overrideen  ->  per-tab marker
    register_callbacks      convention  ->  example/callbacks/*.py (notes + save)
    app_stores()            overriden   -> one store
    clone_metadata()        overrideen  -> copies ExampleNote rows  
    describe()              not overriden; read at startup

If you addd a hook to PortalEngine, add an override here in the same commit.
"""
from dash import html, dcc

from portal_core.engine import PortalEngine
from example.models.example import ExampleNote

class Engine(PortalEngine):
    name = "example"

    # -------------------------------------------------------------------------
    # Tabs
    #
    # Two tabs, one per content-resolution path. Keep all two: they are the
    # only coverage base has for tab_content()
    # -------------------------------------------------------------------------

    def metadata_tabs(self):
        return [
            # convention -> example/layouts/notes_tab.py
            {"id": "notes", "label": "Notes", "icon": "🗒️"},
            # escape hatch -> tab_runtime_info() below, no layout module
            {"id": "runtime_info", "label": "Runtime", "icon": "⏳"},
        ]

    def tab_runtime_info(self):
        """
        Exercises the `tab_<id>(ctx)` escape hatch: a tab built at runtime with 
        no layout module on disk.
        """
        return html.Div(
            [
                html.H4("Runtime"),
                html.P(f"Portal: {self.name}"),
                html.P(f"Tabs declared: {len(self.metadata_tabs())}"),
            ],
            className="example-panel"
        )

    # -------------------------------------------------------------------------
    # Slots
    # -------------------------------------------------------------------------
    def modal_after_header(self):
        """Proves base splats this in below the modal header"""
        return [
            html.Div(
                "example portal -- reference implementation",
                className="example-banner"
            )
        ]

    def sidebar_tab_extras(self, tab):
        """
        Called once per tab, so the output can vary per tab. Showing the tab id
        makes it obvious in the browser which tab a given extra belongs to.
        """
        return [html.Span(tab["id"], className="example-tab-marker")]

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------
    def app_stores(self):
        return [dcc.Store(id="example-notes-store", data={})]

    # -------------------------------------------------------------------------
    # Cloning
    # -------------------------------------------------------------------------
    def clone_metadata(self, session, original, clone) -> None:
        """
        Copy this portal's one extension table.
        
        Runs inside base's transaction, after base has cloned the Submission
        and the OadsMetadata row and flushed -- so clone.id is populated.
        """
        for note in session.query(ExampleNote).filter_by(
            oads_metadata_id=original.id
        ):
            session.add(
                ExampleNote(oads_metadata_id=clone.id, text=note.text)
            )