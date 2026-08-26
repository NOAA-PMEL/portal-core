import dash_design_kit as ddk
import dash_ag_grid as dag
from dash import dcc, html

_TEAL_BG = "rgba(56,217,169,0.07)"
_TEAL_BORDER = "rgba(56,217,169,0.25)"
_TEAL = "#38d9a9"
_RED_BG = "rgba(247,111,111,0.10)"
_RED_BORDER = "rgba(247,111,111,0.20)"
_RED = "#f76f6f"
_TEXT = "#e0e0e0"
_TEXT_MUTED = "#999"
_SURFACE = "#252525"
_BORDER = "1px solid #333"

def _action_btn(label, btn_id, variant="ghost"):
    """
    Reusable button. 
    variant: "teal" | "red" | "ghost"
    """
    if variant == "teal":
        style = {
            "backgroundColor": _TEAL_BG,
            "border": f"1px solid {_TEAL_BORDER}",
            "color": _TEAL
        }
    elif variant == "red":
        style = {
            "backgroundColor": _RED_BG,
            "border": f"1px solid {_RED_BORDER}",
            "color": _RED
        }
    elif variant == "ghost":
        style = {
            "backgroundColor": "transparent",
            "border": "1px solid #444",
            "color": _TEXT_MUTED
        }

    return html.Button(
        label,
        id=btn_id,
        n_clicks=0,
        style={
            **style,
            "borderRadius": "4px",
            "cursor": "pointer",
            "fontSize": "12px",
            "fontWeight": "600",
            "padding": "6px 14px",
            "letterSpacing": "0.02em"
        }
    )

def _bulk_modal(modal_id, title, message_id, cancel_id, confirm_id, confirm_label, confirm_variant="red"):
    """
    Reusable modal shell - same structure for both delete and clone.
    confirm_variant: "red" | "teal"
    """
    confirm_style = {
        "backgroundColor": _TEAL_BG if confirm_variant == "teal" else _RED_BG,
        "border": f"1px solid {_TEAL_BORDER if confirm_variant == 'teal' else _RED_BORDER}",
        "color": _TEAL if confirm_variant == "teal" else _RED,
        "borderRadius": "4px",
        "cursor": "pointer",
        "fontSize": "12px",
        "fontWeight": "600",
        "padding": "6px 14px"
    }

    return html.Div(
        id=modal_id,
        style={'display': 'none'},
        children=[
            #Dark backdrop
            html.Div(
                style={
                    "position": "fixed",
                    "inset": "0",
                    "backgroundColor": "rgba(0,0,0,0.65)",
                    "zIndex": 9998,
                }
            ),
            # Modal box
            html.Div(
                style={
                    "position": "fixed",
                    "top": "50%", "left": "50%",
                    "transform": "translate(-50%, -50%)",
                    "zIndex": 9999,
                    "backgroundColor": _SURFACE,
                    "border": "1px solid #3a3a3a",
                    "borderRadius": "6px",
                    "padding": "28px 32px",
                    "minWidth": "400px",
                    "maxWidth": "480px",
                    "boxShadow": "0 12px 40px rgba(0,0,0,0.6)",
                },
                children=[
                    html.H3(
                        title,
                        style={
                            "color": _TEXT,
                            "marginTop": 0,
                            "marginBottom": "8px",
                            "fontSize": "15px",
                            "fontWeight": "600"
                        }
                    ),
                    html.P(
                        id=message_id,
                        style={
                            "color": _TEXT_MUTED,
                            "fontSize": "13px",
                            "marginBottom": "24px",
                            "lineHeight": "1.6"
                        }
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "8px", "justifyContent": "flex-end"},
                        children=[
                            # Cancel - always ghost
                            html.Button(
                                "Cancel",
                                id=cancel_id,
                                n_clicks=0,
                                style={
                                    "backgroundColor": "transparent",
                                    "border": "1px solid #444", 
                                    "color": _TEXT_MUTED,
                                    "borderRadius": "4px",
                                    "cursor": "pointer",
                                    "fontSize": "12px",
                                    "fontWeight": "600",
                                    "padding": "6px 14px"
                                },
                            ),
                            # Confirm - teal or red
                            html.Button(
                                confirm_label,
                                id=confirm_id,
                                n_clicks=0,
                                style=confirm_style
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

def create_submission_card():
    """Create the past submissions grid card."""
    return  ddk.Card(
            id="past-submissions",
            width=100,
            children=[
                ddk.CardHeader(title="Submissions"),

                # --- Delete confirmation modal --------
                _bulk_modal(
                    modal_id="delete-confirm-modal",
                    title="Delete submissions?",
                    message_id="delete-modal-message",
                    cancel_id="delete-cancel-btn",
                    confirm_id="delete-confirm-btn",
                    confirm_label="Yes, Delete",
                    confirm_variant="red",
                ),

                # --- Clone confirmation modal --------
                _bulk_modal(
                    modal_id="clone-confirm-modal",
                    title="Clone submissions?",
                    message_id="clone-modal-message",
                    cancel_id="clone-cancel-btn",
                    confirm_id="clone-confirm-btn",
                    confirm_label="Yes, Clone",
                    confirm_variant="teal",
                ),

                # -- Stores ------------------
                dcc.Store(id="pending-delete-ids", data=[]),
                dcc.Store(id="pending-clone-ids", data=[]),
                dcc.Store(id="selected-submissions", data=[]),
                dcc.Store(id="open-metadata-store", data=None),
                dcc.Store(id="new-submission-ids", data=[]), # used to track new submissions so the new badge can be used in the grid.

                # Bulk Actions Bar - appears when items are selectd
                html.Div(
                    id="bulk-actions-bar",
                    style={"display": "none"},
                    children=[
                        html.Div(
                            style={
                                "display": "flex",
                                "alignItems": "center",
                                "gap": "12px",
                                "padding": "10px 16px",
                                "backgroundColor": _SURFACE,
                                "border": _BORDER,
                                "borderRadius": "6px",
                                "marginBottom": "12px"
                            },
                            children=[
                                html.Span(
                                    id="selection-count",
                                    style={
                                        "fontSize": "12px",
                                        "fontWeight": 600,
                                        "color": _TEXT_MUTED,
                                        "marginRight": "4px"
                                    },
                                ),
                                _action_btn("📄 Clone selected", "bulk-clone-btn", variant="teal"),
                                _action_btn("🗑️ Delete selected", "bulk-delete-btn", variant="red"),
                                _action_btn("✕ Cancel", "cancel-selection-btn", variant="ghost"),
                            ],
                        ),
                    ],
                ),

                dag.AgGrid(
                    id="submissions",
                    # className="ag-theme-quartz-dark",
                    defaultColDef={"cellRenderer": "markdown"},
                    columnSize="responsiveSizeToFit",

                    # Enable multi-row selection with checkboxes
                    dashGridOptions={
                        "rowSelection": "multiple",
                        "suppressRowClickSelection": True, #only checkboxes trigger selection
                        "masterDetail": True,
                        "detailRowAutoHeight": True,
                        "getRowId": "params.data.id",
                        "suppressRowTransform": True,
                    },
                    
                    columnDefs=[
                        {
                            "field": "checkbox",
                            "headerName": "",
                            "checkboxSelection": True,
                            "headerCheckboxSelection": True,
                            "maxWidth": 50, 
                            "pinned": "left",
                            "lockPosition": True,
                            "suppressMenu": True,
                            "suppressMovable": True,
                        },
                        {
                            "field": "id", 
                            "headerName": "Submission", 
                            "filter": True, "maxWidth": 185, 
                            "cellRenderer": "SubmissionIdRenderer",
                            "cellClass": "overflow-visible",
                            "cellStyle": {"overflow": "visible", "display": "flex", "alignItems": "center"}
                        },
                        
                        {"field": "date_created", "headerName": "Date Created", "filter": True, "maxWidth": 185},
                        # {'field': "submitted_to_ncei", "headerName": "Sumbitted to NCEI"},
                        {
                            "field": "date_submitted_to_ncei",
                            "headerName": "Date Submitted to NCEI",
                            "filter": True,
                            "maxWidth": 280
                        },
                        {"headerName": "Submitted Files", "children": [
                                # Column 1: DATA FILES -> Points to DataFileListRenderer
                                {
                                    "headerName": "Data Files", 
                                    "field": "data_files",
                                    "colId": "data_files", 
                                    "cellRenderer": "DataFileListRenderer", # <--- DISTINCT RENDERER
                                    "autoHeight": True,
                                    "flex": 1,
                                    "filter": True, 
                                },
                                # Column 2: SUPPLEMENTAL FILES -> Points to SuppFileListRenderer
                                {
                                    "headerName": "Supplemental Files", 
                                    "field": "supp_files",
                                    "colId": "supp_files",
                                    "cellRenderer": "SuppFileListRenderer", # <--- DISTINCT RENDERER
                                    "autoHeight": True,
                                    "flex": 1,
                                    "filter": True, 
                                },
                            ],
                        
                        },
                        {
                            "headerName": "Edit",
                            "field": "edit",
                            "maxWidth": 120,
                            # "pinned": "right", 
                            "suppressMenu": True,
                            "cellRenderer": "EditDropdownButton",
                            "cellClass": "overflow-visible",
                            "cellStyle": {
                                "display": "flex", 
                                "justifyContent": "center", 
                                "alignItems": "center"}
                        },
                        {
                            "field": "submit",
                            "headerName": "Submit",
                            "wrapHeaderText": True,
                            'maxWidth': 120,
                            # "pinned": "right",
                            "suppressMenu": True,
                            "cellRenderer": "SubmitDropdownButton",
                            "cellClass": "overflow-visible",
                            "cellStyle": {
                                "display": "flex", 
                                "justifyContent": "center", 
                                "alignItems": "center"}
                        },
                    ],
                    getRowId="params.data.id",
                ),
            ],
            style={"display": "none"},
        )
        