from dash import html, dcc

def build_sidebar(portal):
    items = []
    for i, tab in enumerate(portal.metadata_tabs()):
        is_first = i == 0
        items.append(
            html.Div(
                id={'type': 'sidebar-tab', 'index': tab['id']},
                n_clicks=0,
                style={
                    'padding': '10px 16px',
                    'fontSize': '13px',
                    'color': '#e0e0e0' if is_first else '#666',
                    'cursor': 'pointer',
                    'borderLeft': '2px solid #4f8ef7' if is_first else '2px solid transparent',
                    'background': 'rgba(79,142,247,0.07)' if is_first else 'transparent',
                    'display': 'flex',
                    'alignItems': 'center',
                    'gap': '10px',
                    'userSelect': 'none'
                },
                children=[
                    html.Span(tab['icon'], style={
                        'fontSize': '14px',
                        'width': '18px',
                        'textAlign': 'center',
                        'opacity': '0.8',
                    }),
                    html.Span(tab['label']),
                    *portal.sidebar_tab_extras(tab),
                ]
            )
        )
    return items

def build_content_panels(portal):
    panels = []
    for i, tab in enumerate(portal.metadata_tabs()):
        panels.append(
            html.Div(
                id={'type': 'tab-panel', 'index': tab['id']},
                style={'display': 'block' if i == 0 else 'none'},
                children=[portal.tab_content(tab['id'])]
            )
        )
    return panels


def create_metadata_modal(portal):
    """Empty modal shell - content will be added incrementally."""
    return html.Div(
        id='metadata-modal-overlay',
        n_clicks=0,
        style={
            'display': 'none',
            'position': 'fixed',
            'top': 0, 'left': 0, 'right': 0, 'bottom': 0,
            'backgroundColor': 'rgba(0, 0, 0, 0.65)',
            'zIndex': 1000,
            'justifyContent': 'center',
            'alignItems': 'center',
        },
        children=[

            # Inner modal box — this is the centered popup
            html.Div(
                id='metadata-modal',
                style={
                    'backgroundColor': '#1e1e1e',
                    'border': '1px solid #444',
                    'borderRadius': '8px',
                    'width': '90vw', # changed from 800 px to make wider
                    'maxWidth': '95vw', # changed from 95vw
                    'height': '80vh',
                    'minHeight': '500px',
                    'display': 'flex',
                    'flexDirection': 'column',
                    'overflow': 'hidden',
                    'margin': 'auto',
                },
                children=[

                    # Header
                    html.Div(
                        style={
                            'padding': '20px 24px',
                            'borderBottom': '2px solid #333',
                            'display': 'flex',
                            'justifyContent': 'space-between',
                            'alignItems': 'center',
                            'backgroundColor': '#252525',
                        },
                        children=[
                            html.H3('Add Metadata Details', style={
                                'margin': 0,
                                'fontSize': '20px',
                                'color': '#e0e0e0',
                                'fontWeight': 'bold',
                            }),
                            html.Button(
                                '×',
                                id='btn-close-metadata-modal',
                                style={
                                    'backgroundColor': 'transparent',
                                    'border': 'none',
                                    'fontSize': '32px',
                                    'cursor': 'pointer',
                                    'padding': '0 5px',
                                    'lineHeight': '1',
                                    'color': '#888',
                                }
                            ),
                        ]
                    ),

                    *portal.modal_after_header(),

                    # Body - sidebar + content panels (WILL NEED TO INJECT PROJECT SPECIFIC HERE)
                    html.Div(
                        style={
                            'flex': 1,
                            'display': 'flex',
                            'flexDirection': 'row',
                            'overflow': 'hidden',
                            'minHeight': 0
                        },
                        children=[
                            
                            # Sidebar
                            html.Div(
                                id='metadata-sidebar',
                                style={
                                    'width': '220px',
                                    'flexShrink': 0,
                                    'backgroundColor': '#1a1a1a',
                                    'borderRight': '1px solid #2a2a2a',
                                    'paddingTop': '16px',
                                    'display': 'flex',
                                    'flexDirection': 'column',
                                    'gap': '2px',
                                    'overflowY': 'auto'
                                },
                                children=build_sidebar(portal)
                            ),

                            # Content panels
                            html.Div(
                                style={
                                    'flex': 1,
                                    'overflowY': 'auto',
                                    'padding': '24px',
                                    'backgroundColor': '#1e1e1e',
                                    'minWidth': 0,
                                },
                                children=build_content_panels(portal)
                            ),
                        ]
                    ),

                    html.Div(
                        id='metadata-save-status',
                        className='metadata-save-status',
                        style={
                            'padding': '0 24px 12px',
                            'fontSize': '13px',
                            'flexShrink': 0
                        }
                    ),

                    dcc.Store(id='metadata-save-store'),
                    dcc.Store(id='metadata-ready-store'),

                    # Footer
                    html.Div(
                        style={
                            'padding': '16px 24px',
                            'borderTop': '2px solid #333',
                            'display': 'flex',
                            'justifyContent': 'flex-end',
                            'gap': '10px',
                            'backgroundColor': '#252525',
                            'flexShrink': 0,
                        },
                        children=[
                            html.Button(
                                'Cancel',
                                id='btn-cancel-metadata-modal',
                                style={
                                    'padding': '10px 20px',
                                    'backgroundColor': '#444',
                                    'color': '#e0e0e0',
                                    'border': '1px solid #555',
                                    'borderRadius': '4px',
                                    'cursor': 'pointer',
                                    'fontSize': '14px',
                                    'fontWeight': 'bold',
                                }
                            ),
                            html.Button(
                                'Save',
                                id='btn-save-metadata',
                                style={
                                    'padding': '10px 20px',
                                    'backgroundColor': '#0066cc',
                                    'color': '#ffffff',
                                    'border': '1px solid #0052a3',
                                    'borderRadius': '4px',
                                    'cursor': 'pointer',
                                    'fontSize': '14px',
                                    'fontWeight': 'bold',
                                }
                            ),
                        ]
                    ),

                ]
            )
        ]
    )
