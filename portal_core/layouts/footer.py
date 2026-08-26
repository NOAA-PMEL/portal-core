import dash_design_kit as ddk
from dash import html, dcc
from portal_core.config_loader import get_config
from portal_core.utils import portal_asset_url

def create_footer(app):
    """Create the application footer with links and version info"""

    # Build legal links dynamically
    legal_elements = []
    for i, link in enumerate(get_config().LEGAL_LINKS):
        if i > 0:
            legal_elements.append(" | ")
        legal_elements.append(dcc.Link(link["text"], href=link["url"]))
    
    
    return ddk.Card(
            width=100,
            style={
                "margin-bottom": "10px", 
                "padding": "10px", 
                "display": "flex",
                "flex-direction": "row", 
                "align-items": "center",
                "position": "relative",
                },
            children=[
                ddk.Card(
                    width=15,
                    style={"padding": "5px"},
                    children=[
                        html.Img(
                            src=portal_asset_url(
                                get_config().FOOTER_LOGO
                            ),
                            style={"height": "80px", "width": "auto", "max-width": "100%"}
                        ),
                    ],
                ),
                ddk.Card(
                    width=85,
                    children=[
                        html.Div(
                            children=[
                                dcc.Link(
                                    get_config().FOOTER_PARENT_ORG_NAME,
                                    href=get_config().FOOTER_PARENT_ORG_URL,
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                dcc.Link(
                                    get_config().FOOTER_ORG_NAME,
                                    href=get_config().FOOTER_ORG_URL,
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                dcc.Link(
                                    get_config().CONTACT_EMAIL,
                                    href=f"mailto:{get_config().CONTACT_EMAIL}",
                                )
                            ]
                        ),
                        html.Div(
                            children=legal_elements
                        )
                    ],
                ),
                ddk.Card(
                    width=10,
                    children=[
                        html.Div(
                            style={"font-size": ".6em"},
                            children=["Version " + str(get_config().VERSION)],
                        )
                    ],
                    style={"position": "absolute", "bottom": "0"},
                ),
            ],
        )