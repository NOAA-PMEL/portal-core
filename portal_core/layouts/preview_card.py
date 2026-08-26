import dash_design_kit as ddk
from dash import html, dcc

def create_preview_card():
    """Create the preview plots card."""
    return  ddk.Card(
            id="preview-card",
            width=100,
            children=[
                ddk.CardHeader(title="Preview Plots"),
                ddk.ControlCard(
                    orientation="horizontal",
                    label_position="left",
                    children=[
                        ddk.ControlItem(
                            width=50,
                            label="Select a file:",
                            children=[
                                dcc.Dropdown(id="files"),
                            ],
                        ),
                        ddk.ControlItem(
                            width=30,
                            children=[
                                dcc.Loading(
                                    html.Div(
                                        id="preview-loader",
                                        style={"visibility": "hidden"},
                                    )
                                )
                            ],
                        ),
                        ddk.ControlItem(
                            width=5,
                            children=[
                                html.Button(id="done-preview", children=["Done"]),
                            ],
                        ),
                        ddk.Block(
                            width=5,
                            children=[
                                # spacer
                            ],
                        ),
                    ],
                ),
                ddk.Block(
                    width=100,
                    children=[
                        dcc.Loading(ddk.Card(id="preview-plots")),
                    ],
                ),
            ],
            style={"display": "none"},
        )