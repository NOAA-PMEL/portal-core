"""
Callbacks for preview functionality.
"""
from dash import Input, Output
import dash_design_kit as ddk

from portal_core.constants import (
    VISIBLE_BLOCK,
    HIDDEN_BLOCK
)
from portal_core.utils import (
    app_logger as log,
    make_preview
)


def register_preview_callbacks(app):
    """Register preview-related callbacks."""
    @app.callback(
    [
        Output("preview-card", "style", allow_duplicate=True),
        Output("past-submissions", "style", allow_duplicate=True),
    ],
    [
        Input("done-preview", "n_clicks"),
    ],
    prevent_initial_call=True
    )
    def toggle_preivew(click):
        """Hide preview card and show submissions when done previewing."""
        return [HIDDEN_BLOCK, VISIBLE_BLOCK]

    @app.callback(
        [
            Output("preview-plots", "children"), 
            Output("preview-loader", "children")
        ],
        [
            Input("files", "value")
        ],
        prevent_initial_call=True,
        background=True,
        )
    def preview_plot(filename):
        """Generate preview plots for selected file"""
        log.debug(f'[preview_plot] Entering preview call back with {filename}')
        if filename is not None and len(filename) > 0:
            log.debug(f'Calling preview with {filename}')
            cards = make_preview(filename)
            return [cards, "done"]
        else:
            log.debug('[preview_plot] Preview plot had an empty file name.')
            return [ddk.Card(), "done"]