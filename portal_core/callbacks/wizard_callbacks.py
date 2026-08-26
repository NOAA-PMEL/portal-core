import json
from dash import Input, Output, State, html, no_update
from sqlalchemy.orm import Session
from portal_core.models import Submission
from portal_core.constants import (
    _OVERLAY_HIDDEN,
     _OVERLAY_VISIBLE, 
     _PANEL_CLOSED, 
     _PANEL_OPEN, 
     metadata_url, 
     postgres_engine, 
     VISIBLE_BLOCK
)
from portal_core.config_loader import get_config

from portal_core.utils import (
    create_file_list_from_dataframe,
    create_submission_id,
    get_data_files,
    get_submissions_with_file_lists
)

def register_wizard_callbacks(app):
    """Register all wizard-related callbacks"""
    # Show/hide wizard when "New Submission" button is clicked
    @app.callback(
        [
            Output('wizard-panel', 'style'),
            Output('wizard-overlay', 'style'),
            Output('current-step', 'data'),
            Output('current-submission', 'data'),
            Output('wizard-file-list', 'children', allow_duplicate=True),
            Output('wizard-supplemental-list', 'children', allow_duplicate=True),
            Output('submissions', 'rowData', allow_duplicate=True),
            Output('past-submissions', 'style', allow_duplicate=True), 
            Output('open-metadata-store', 'data', allow_duplicate=True),
            Output('new-submission-ids', 'data', allow_duplicate=True)
        ],
        [
            Input('new-submission', 'n_clicks'),
            Input('btn-close-wizard', 'n_clicks'),
            Input('wizard-overlay', 'n_clicks'),
            Input('edit-click-store', 'data')
        ],
        [
            State('current-step', 'data'),
            State('current-submission', 'data'),
            State('dashboard-user', 'data'),
            State('submissions', 'rowData') 
        ],
        prevent_initial_call=True
    )
    def toggle_wizard(new_clicks, close_clicks, overlay_clicks, edit_row, current_step, current_submission, dashboard_user, current_submissions_row_data):
        from dash import callback_context
        ctx = callback_context

        if not ctx.triggered:
            return [_PANEL_CLOSED, _OVERLAY_HIDDEN, 0, current_submission, no_update, no_update, no_update, no_update, no_update, no_update]

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if ctx.triggered_id == 'edit-click-store':
            db_id = edit_row['db_id']
            target = edit_row.get('target', 'step-1') # default to step-1 if missing
            current_submission = db_id
            
            df_data = get_data_files(current_submission, "data")
            df_supp = get_data_files(current_submission, "supplemental")
            # Use utility function to create file lists for wizard
            data_file_list = create_file_list_from_dataframe(
                df_data,
                current_submission,
                show_delete=True,
                context='wizard',
                empty_message="No data files uploaded yet" if get_config().ALLOW_MULTIPLE_DATA_FILES else 'No data file uploaded yet'
            )

            supp_file_list = create_file_list_from_dataframe(
                df_supp,
                current_submission,
                show_delete=True,
                context='wizard',
                empty_message="No supplemental files uploaded yet"
            )
            if target == 'metadata':
                import time
                ts = time.time()
                # Open metadata modal directly - wizard panel stays closed
                return _PANEL_CLOSED, _OVERLAY_HIDDEN, 0, current_submission, data_file_list, supp_file_list, no_update, no_update, ts, no_update # triggers the metadata-model to open 
            elif target == 'step-2':
                return _PANEL_OPEN, _OVERLAY_VISIBLE, 2, current_submission, data_file_list, supp_file_list, no_update, no_update, no_update, no_update
            else:
                # step-1 or any unknown target
                return _PANEL_OPEN, _OVERLAY_VISIBLE, 1, current_submission, data_file_list, supp_file_list, no_update, no_update, no_update, no_update

        # Default messages for empty lists
        empty_data = html.Div("No data files uploaded yet" if get_config().ALLOW_MULTIPLE_DATA_FILES else 'No data file uploaded yet', style={'color': '#999', 'fontStyle': 'italic', 'padding': '10px'})
        empty_supp = html.Div("No supplemental files uploaded yet", style={'color': '#999', 'fontStyle': 'italic', 'padding': '10px'})

        # CLOSE logic
        if trigger_id in ['btn-close-wizard', 'wizard-overlay']:
            # We keep the current submission ID and step so they can "resume" later
            return _PANEL_CLOSED, _OVERLAY_HIDDEN, current_step, None, no_update, no_update, no_update, no_update, no_update, no_update

        # OPEN logic
        if trigger_id == 'new-submission':
            if new_clicks is None:
                return [no_update] * 10

            # CREATE NEW logic
            user = json.loads(dashboard_user)
            new_hash_id = create_submission_id(user["id"])
            
            # Explicitly pass the id into the model
            submission = Submission(
                id=new_hash_id,
                dashboard_user_id=user["id"]
                )
            
            with Session(postgres_engine) as session:
                session.add(submission)
                session.commit()
                # session.refresh(submission)
                new_id = submission.id

            # Refresh the gird
            df_submissions = get_submissions_with_file_lists(
                user["id"], metadata_url
            )
            df_submissions = df_submissions.sort_values(by="date_created", ascending=False)

            # Tag it as new right here
            if not df_submissions.empty:
                df_submissions['is_new'] = df_submissions['id'].astype(str) == str(new_id)

            return _PANEL_OPEN, _OVERLAY_VISIBLE, 1, new_id, empty_data, empty_supp, df_submissions.to_dict('records'), VISIBLE_BLOCK, no_update, [str(new_id)]

        return [_PANEL_CLOSED, _OVERLAY_HIDDEN, 0, current_submission, no_update, no_update, no_update, no_update, no_update, no_update]

    # Update step title
    @app.callback(
        Output('step-title', 'children'),
        Input('current-step', 'data')
    )
    def update_step_title(step):
        if step == 0:
            return ''
        return f'Step {step} of 3'

    # Toggle step visibility
    @app.callback(
        [
            Output('step-1-container', 'style'),
            Output('step-2-container', 'style'),
            Output('step-3-container', 'style')
        ],
        Input('current-step', 'data')
    )
    def toggle_step_visibility(step):
        # Default all are hidden
        hidden = {'display': 'none'}
        visible = {'display': 'block'}

        if step == 1:
            return visible, hidden, hidden
        elif step == 2:
            return hidden, visible, hidden
        elif step == 3:
            return hidden, hidden, visible

        return hidden, hidden, hidden

    # Handle Next buttons
    @app.callback(
        Output('current-step', 'data', allow_duplicate=True),
        Input('btn-wizard-next', 'n_clicks'),
        State('current-step', 'data'),
        prevent_initial_call=True
    )
    def next_step(n_clicks, current_step):
        if n_clicks is None:
            return current_step
        # Go to next step
        new_step = current_step + 1
        if new_step > 3:
            return 3 # stay on step 3 (can't go past)
        return new_step

    # Handle back button
    @app.callback(
        Output('current-step', 'data', allow_duplicate=True),
        Input('btn-wizard-back', 'n_clicks'),
        State('current-step', 'data'),
        prevent_initial_call=True
    )
    def previous_step(n_clicks, current_step):
        if n_clicks is None:
            return current_step
        # Go to next step
        new_step = current_step - 1
        if new_step < 1:
            return 1 # stay on step 1 (can't go below step 1)
        return new_step

    # Toogle Next/Start Subbision button visibility based on step
    @app.callback(
        [
            Output('btn-wizard-next', 'style'),
            Output('btn-start-submission', 'style'),
        ],
        Input('current-step', 'data')
    )
    def toggle_footer_buttons(current_step):
        next_button_base = {
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
        
        submit_button_base = {
                            'padding': '10px 20px',
                            'backgroundColor': '#0066cc',
                            'color': '#ffffff',
                            'border': '1px solid #0052a3',
                            'borderRadius': '4px',
                            'cursor': 'pointer',
                            'fontSize': '14px',
                            'fontWeight': 'bold',
                        }
        if current_step == 3:
            # On step 3, hide Next and show Done button
            return [{**next_button_base, 'display': 'none'}, submit_button_base]
        else:
            # On other steps, show Next and hide Done button
            return [next_button_base, {**submit_button_base, 'display': 'none'}]

    # Handle Done button
    @ app.callback(
        [
            Output('wizard-panel', 'style', allow_duplicate=True),
            Output('wizard-overlay', 'style', allow_duplicate=True),
            Output('current-step', 'data', allow_duplicate=True),
            Output('submissions', 'rowData', allow_duplicate=True),
            Output('past-submissions', 'style', allow_duplicate=True),
            Output('current-submission', 'data', allow_duplicate=True),
            Output('notifications', 'children', allow_duplicate=True),
        ], 
        Input('btn-start-submission', 'n_clicks'), 
        [
            State('current-submission', 'data'),
            State('dashboard-user', 'data'),
            State('new-submission-ids', 'data') 
        ],
        prevent_initial_call=True
    )
    def start_submission(n_clicks, current_submission, dashboard_user, new_ids):
        if n_clicks is None:
            return [no_update] * 7

        user = json.loads(dashboard_user)

        # Close the wizard
        panel_closed = {
            'position': 'fixed',
            'top': 0,
            'width': '600px',
            'height': '100vh',
            'backgroundColor': '#1e1e1e',  # Dark background
            'boxShadow': '-4px 0 20px rgba(0,0,0,0.3)',
            'transition': 'right 0.4s ease',
            'zIndex': 999,
            'display': 'flex',
            'flexDirection': 'column',
            'overflow': 'hidden',
            'color': '#e0e0e0', # Light text
            'right': '-600px'
        }
        overlay_hidden = {
            'position': 'fixed',
            'top': 0,
            'left': 0,
            'right': 0,
            'bottom': 0,
            'backgroundColor': 'rgba(0, 0, 0, 0.5)',
            'zIndex': 998,
            'cursor': 'pointer',
            'display': 'none'
        }
        df_submissions = get_submissions_with_file_lists(
            user["id"], metadata_url
        )
        # Sort by newest submission first
        df_submissions = df_submissions.sort_values(by="date_created", ascending=False)

        # Maintain badge persistence if the row was just created
        if not df_submissions.empty:
            df_submissions['is_new'] = df_submissions['id'].astype(str).isin([str(i) for i in (new_ids or [])])

        # Define the rule here
        # Note: We use a Javascript string for AgGrid to evaluate
        highlight_rule = {
            'highlight-row': f'params.data.id == {current_submission}'
        }

        success_notification = html.Div(
                '✅ Submission successfully updated.',
                style={
                    'backgroundColor': 'rgba(56, 217, 169, 0.1)',
                    'border': '1px solid rgba(56, 217, 169, 0.3)',
                    'borderRadius': '4px',
                    'color': '#38d9a9',
                    'padding': '10px 14px',
                    'fontSize': '13px',
                    'marginBottom': '10px'
                },
            )

        return [
            panel_closed,
            overlay_hidden,
            0, 
            df_submissions.to_dict("records"),
            constants.VISIBLE_BLOCK,
            None, # reset current submission to 0 for next time,
            success_notification
        ]





