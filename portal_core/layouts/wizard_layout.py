import dash_design_kit as ddk
from dash import dcc, html
from portal_core.layouts.metadata_modal import create_metadata_modal
from portal_core.config_loader import get_config

#     # ---- Main layout --------------------------
def create_wizard_layout(portal):
    """Creates the side panel wizard layout"""
    return [
        # Button container
        ddk.Block(
            width=100,
            children=[
                html.Button(
                    id="new-submission", 
                    children=["+ New Submission"],
                    style={
                        'padding': '10px 20px',
                        'fontSize': '16px',
                        'cursor': 'pointer',
                        'marginBottom': '20px'
                    }
                ),
            ],
        ),
        
        html.Div(id="notifications"),
        dcc.Store(id='current-step', data=0),
        dcc.Store(id='newly-uploaded-data-file'), # For tracking newly added data files (used in Ocean sites portal)

        # Create the metadata modal - placed outside the wizard panel so it can sit above it (zIndex: 1000)
        create_metadata_modal(portal),
        
        # Overlay
        html.Div(
            id='wizard-overlay',
            n_clicks=0,
            style={
                'display': 'none',
                'position': 'fixed',
                'top': 0, 
                'left': 0, 
                'right': 0, 
                'bottom': 0,
                'backgroundColor': 'rgba(0, 0, 0, 0.5)',
                'zIndex': 998,
                'cursor': 'pointer'
            }
        ),
    
        # Side panel - matching DDK dark theme
        html.Div(
            id='wizard-panel',
            style={
                'position': 'fixed',
                'right': '-600px',
                'top': 0,
                'width': '600px',
                'height': '100vh',
                'backgroundColor': '#1e1e1e',
                'boxShadow': '-4px 0 20px rgba(0,0,0,0.3)',
                'transition': 'right 0.4s ease',
                'zIndex': 999,
                'display': 'flex',
                'flexDirection': 'column',
                'overflow': 'hidden',
                'color': '#e0e0e0'
            },
            children=[
                # Header section
                html.Div(
                    style={
                        'padding': '20px',
                        'borderBottom': '2px solid #333',
                        'display': 'flex',
                        'justifyContent': 'space-between',
                        'alignItems': 'center',
                        'backgroundColor': '#252525',
                        'minHeight': '60px'
                    },
                    children=[
                        html.H3('Submission Wizard', style={
                            'margin': 0, 
                            'fontSize': '20px',
                            'color': '#e0e0e0',
                            'fontWeight': 'bold'
                        }),
                        html.Button(
                            '×',
                            id='btn-close-wizard',
                            style={
                                'backgroundColor': 'transparent',
                                'border': 'none',
                                'fontSize': '32px',
                                'cursor': 'pointer',
                                'padding': '0 5px',
                                'lineHeight': '1',
                                'color': '#888'
                            }
                        )
                    ]
                ),
                
                # Content area
                html.Div(
                    style={
                        'flex': 1,
                        'overflowY': 'auto',
                        'padding': '20px',
                        'backgroundColor': '#1e1e1e'
                    },
                    children=[
                        html.Div(
                            id='step-title',
                            style={
                                'marginBottom': '20px', 
                                'fontWeight': 'bold',
                                'fontSize': '16px',
                                'color': '#999'
                            }
                        ),

                        # STEP 1: DATA UPLOAD
                        html.Div(id='step-1-container', style={'display': 'none'}, children=[
                            html.H4('Upload Your Data Files' if get_config().ALLOW_MULTIPLE_DATA_FILES else 'Upload Your Data File', style={
                                'marginBottom': '10px',
                                'color': '#e0e0e0'
                            }),
                            html.P('Drag and drop your primary data files here' if get_config().ALLOW_MULTIPLE_DATA_FILES else 'Drag and drop your primary data file here', 
                                   style={'color': '#999', 'marginBottom': '15px'}),
                            dcc.Upload(
                                id='wizard-upload-data',
                                children=html.Div([
                                    'Data Files: Drag and Drop or ' if get_config().ALLOW_MULTIPLE_DATA_FILES else 'Data File: Drag and Drop or ', 
                                    html.A("Select Files" if get_config().ALLOW_MULTIPLE_DATA_FILES == True else "Select File", style={
                                        'color': 'lightblue',
                                        'cursor': 'pointer',
                                        'textDecoration': 'underline'
                                    })
                                ]),
                                style={
                                    "width": "100%", 
                                    "height": "80px", 
                                    "lineHeight": "80px",
                                    "borderWidth": "2px", 
                                    "borderStyle": "dashed",
                                    "borderRadius": "5px", 
                                    "textAlign": "center", 
                                    "margin": "10px 0",
                                    "borderColor": "#444",
                                    "backgroundColor": "#2a2a2a",
                                    "color": "#e0e0e0"
                                },
                                multiple=get_config().ALLOW_MULTIPLE_DATA_FILES
                            ),
                            html.Div(id='data-parse-status'), # Feedback for portals that parse the data into the metadata. Used in Ocean Sites
                            # File list container - populated by callback
                            html.Div(
                                id='wizard-file-list',
                                style={'marginTop': '15px'},
                                children=[
                                    html.Div("No data files uploaded yet" if get_config().ALLOW_MULTIPLE_DATA_FILES else 'No data file uploaded yet',
                                    style={'color': '#999', 'fontStyle': 'italic', 'padding': '10px'})
                                ]
                            )
                        ]),

                        # STEP 2: SUPPLEMENTAL
                        html.Div(id='step-2-container', style={'display': 'none'}, children=[
                            html.H4('Add Supplemental Files (Optional)', style={
                                'marginBottom': '10px',
                                'color': '#e0e0e0'
                            }),
                            html.P('Upload any additional documentation or supporting files', 
                                   style={'color': '#999', 'marginBottom': '15px'}),
                            dcc.Upload(
                                id='wizard-upload-supplemental',
                                children=html.Div([
                                    'Drag and Drop or ', 
                                    html.A('Select Supplemental Files', style={
                                        'color': 'lightblue',
                                        'cursor': 'pointer',
                                        'textDecoration': 'underline'
                                    })
                                ]),
                                style={
                                    "width": "100%", 
                                    "height": "80px", 
                                    "lineHeight": "80px",
                                    "borderWidth": "2px", 
                                    "borderStyle": "dashed",
                                    "borderRadius": "5px", 
                                    "textAlign": "center", 
                                    "margin": "10px 0",
                                    "borderColor": "#444",
                                    "backgroundColor": "#2a2a2a",
                                    "color": "#e0e0e0"
                                },
                                multiple=True
                            ),
                            # File list container - populated callback
                            html.Div(
                                id='wizard-supplemental-list',
                                style={'marginTop': '15px'},
                                children=[
                                    html.Div("No supplemental files uploaded yet",
                                    style={'color': '#999', 'fontStyle': 'italic', 'padding': '10px'})
                                ]
                            )
                        ]),

                        # STEP 3: METADATA
                        html.Div(id='step-3-container', style={'display': 'none'}, children=[
                            html.H4('Enter Metadata', style={
                                'marginBottom': '10px',
                                'color': '#e0e0e0'
                            }),
                            html.P('Provide information to describe your submission.', 
                                   style={'color': '#999', 'marginBottom': '15px'}),
                            

                            # Add Metadata Details Button
                            html.Button(
                                'Add Metadata Details',
                                id='btn-open-metadata-modal',
                                n_clicks=0,
                                style={
                                    'padding': '10px 20px',
                                    'backgroundColor': '#444',
                                    'color': 'lightblue',
                                    'border': '1px solid #555',
                                    'borderRadius': '4px',
                                    'cursor': 'pointer',
                                    'fontSize': '14px',
                                    'fontWeight': 'bold',
                                    'textDecoration': 'underline',
                                    'marginTop': '5px'
                                }
                            )
                        ]),
                    ]
                ),
                
                # Footer
                html.Div([
                    html.Button(
                        'Back', 
                        id='btn-wizard-back', 
                        style={
                            'marginRight': '10px',
                            'padding': '10px 20px',
                            'backgroundColor': '#444',
                            'color': '#e0e0e0',
                            'border': '1px solid #555',
                            'borderRadius': '4px',
                            'cursor': 'pointer',
                            'fontSize': '14px',
                            'fontWeight': 'bold'
                        }
                    ),
                    html.Button(
                        'Next', 
                        id='btn-wizard-next',
                        style={
                            'padding': '10px 20px',
                            'backgroundColor': '#444',
                            'color': 'lightblue',
                            'border': '1px solid #555',
                            'borderRadius': '4px',
                            'cursor': 'pointer',
                            'textDecoration': 'underline',
                            'fontSize': '14px',
                            'fontWeight': 'bold'
                        }
                    ),
                    html.Button(
                        'Done',
                        id='btn-start-submission',
                        style={
                            'padding': '10px 20px',
                            'backgroundColor': '#0066cc',
                            'color': '#ffffff',
                            'border': '1px solid #0052a3',
                            'borderRadius': '4px',
                            'cursor': 'pointer',
                            'fontSize': '14px',
                            'fontWeight': 'bold',
                            'display': 'none' # Hidden by default
                        }
                    ),
                ], style={
                    'display': 'flex', 
                    'justifyContent': 'flex-end', 
                    'padding': '20px', 
                    'borderTop': '2px solid #333',
                    'backgroundColor': '#252525',
                    'minHeight': '70px',
                    'alignItems': 'center',
                    'flexShrink': 0
                })
            ]
        )
    ]