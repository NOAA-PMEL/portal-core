"""
Callbacks discovered by convention: every module in example/callbacks/ that
defines register_callbacks(app).

Nothing imports this file. If the echo below stops working, base's callback
auto-discovery has broken.
"""
from dash import Input, Output

def register_callbacks(app):
    @app.callback(
        Output("example-notes-echo", "children"),
        Input("example-notes-input", "value"),
        prevent_initial_call=True,
    )
    def echo_note(value):
        return f"{len(value or '')} characters"