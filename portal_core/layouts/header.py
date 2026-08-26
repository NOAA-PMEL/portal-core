import dash_design_kit as ddk
from dash import html
from portal_core.config_loader import get_config
from portal_core.utils import portal_asset_url

def create_header(app):
    """Create the application header with logo and user info."""
    return ddk.Header(
            id="header",
            children=[
                ddk.Logo(
                    portal_asset_url(
                        get_config().HEADER_LOGO
                    ),
                    style={"padding": 15},
                ),
                ddk.Title(get_config().PAGE_TITLE),
                html.Div(id="user-welcome", children="You are not logged in..."),
                html.Div(
                    # auth.create_logout_button(),
                    html.Button(
                        "LOGOUT",
                        style={"margin-right": "30px", "float": "right"},
                    )
                ),
            ],
            style={"height": "140px"},
            border_width="3",
        )