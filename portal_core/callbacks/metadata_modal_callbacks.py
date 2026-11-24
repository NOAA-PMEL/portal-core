from dash import Input, Output, ALL, ctx
from dash.exceptions import PreventUpdate
    
def register_metadata_modal_callbacks(app):

    # callback to toggle metadata modal
    @app.callback(
        Output('metadata-modal-overlay', 'style'),
        Output('metadata-save-status', 'children', allow_duplicate=True),
        [
            Input('btn-open-metadata-modal', 'n_clicks'),
            Input('btn-close-metadata-modal', 'n_clicks'),
            Input('btn-cancel-metadata-modal', 'n_clicks'),
            Input('metadata-ready-store', 'data'),
        ],
        prevent_initial_call=True
    )
    def toggle_metadata_modal(open_clicks, close_clicks, cancel_clicks, metadata_ready):
        if ctx.triggered_id == 'metadata-ready-store' and metadata_ready is None:
            raise PreventUpdate
        if ctx.triggered_id in ('btn-open-metadata-modal', 'metadata-ready-store'):
            visible = {
                'display': 'flex',
                'position': 'fixed',
                'top': 0, 'left': 0, 'right': 0, 'bottom': 0,
                'backgroundColor': 'rgba(0, 0, 0, 0.65)',
                'zIndex': 1000,
                'justifyContent': 'center',
                'alignItems': 'center'
            }
            return visible, []
        return {'display': 'none'}, []

   
    # Switch tabs on metadata modal
    @app.callback(
        Output({'type': 'tab-panel', 'index': ALL}, 'style'),
        Output({'type': 'sidebar-tab', 'index': ALL}, 'style'),
        Input({'type': 'sidebar-tab', 'index': ALL}, 'n_clicks'),
        prevent_initial_call=True
    )
    def switch_metadata_tab(n_clicks):
        if not ctx.triggered_id:
            raise PreventUpdate

        active_id = ctx.triggered_id['index']

        panel_ids = [m['id']['index'] for m in ctx.outputs_list[0]]
        sidebar_ids = [m['id']['index'] for m in ctx.outputs_list[1]]

        panel_styles = [
            {'display': 'block' if tid == active_id else 'none'}
            for tid in panel_ids
        ]

        sidebar_styles = [
            {
                'padding': '10px 16px',
                'fontSize': '13px',
                'cursor': 'pointer',
                'display': 'flex',
                'alignItems': 'center',
                'gap': '10px',
                'userSelect': 'none',
                'color': '#e0e0e0' if tid == active_id else '#666',
                'borderLeft': '2px solid #4f8ef7' if tid == active_id else '2px solid transparent',
                'background': 'rgba(79,142,247,0.07)' if tid == active_id else 'transparent',
            }
            for tid in sidebar_ids
        ]

        return panel_styles, sidebar_styles