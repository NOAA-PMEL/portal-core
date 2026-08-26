"""
Tab content resolved by convention. example/layouts/<tab_id>_tab.py
"""
from dash import dcc, html

def create_tab_content():
    return html.Div(
        [
            html.H4("Notes"),
            dcc.Textarea(
                id="example-notes-input", 
                placeholder="Type here; the callback echoes below.",
                style={"width": "100%", "height": "120px"},
            ),
            html.Div(id="example-notes-echo", className="example-echo")
        ],
        className="example-panel",
    )