import dash_design_kit as ddk
from dash import dcc
# from .data_files_card import create_data_files_card
from portal_core.layouts.preview_card import create_preview_card
from portal_core.layouts.submission_card import create_submission_card
from portal_core.layouts.footer import create_footer
from portal_core.layouts.wizard_layout import create_wizard_layout
from portal_core.layouts.header import create_header

def get_layout(app, portal):
    """Construct and return the main application layout."""
    return ddk.App(
        show_editor=False,
        children=[
            dcc.Store(id="current-submission", data=0),
            dcc.Store(id="dashboard-user", data='{"id": -1}'),
            dcc.Store(id="file-click-store"),
            dcc.Store(id="edit-click-store"),
            dcc.Store(id="archive-click-store"),
            dcc.Store(id="metadata-store", data={}),
            *portal.app_stores(),
            # Header
            create_header(app),

            # # Upload section (buttons + upload area)
            # # * uses unpacking since this function returns a list of components
            *create_wizard_layout(portal),

            # Data files card
            # create_data_files_card(),

            # Past submission card
            create_submission_card(),

            # Footer
            create_footer(app),

            # Preview card
            create_preview_card(),
        ],
    )
