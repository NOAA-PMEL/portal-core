"""
Callback for file upload and deletion.
"""
import os
from pathlib import Path
from dash import Input, Output, State, no_update, html, ALL
import dash_design_kit as ddk
import json

from portal_core.constants import (
    metadata_url,
    UPLOAD_DIRECTORY,
    VISIBLE_BLOCK
)
from portal_core.utils import (
    app_logger as log,
    get_data_files,
    get_submissions_with_file_lists,
    file_exists,
    insert_file,
    get_submissions_with_file_lists,
    get_data_files,
    delete_file,
    create_file_list_from_dataframe,
    _normalize_upload
)
import uuid
from portal_core.config_loader import get_config
from portal_core.models.metadata import FileCategory

def register_file_callbacks(app, save_file_func, archive_file_func):
    """
    Register file-related callbacks. 

    Args:
        app: Dash app instance
        save_file_func: Function to save uploaded files
        archive_file_func: Function to archive deleted files
    """
    @app.callback(
        [
            Output("submissions", "rowData", allow_duplicate=True),
            Output("past-submissions", "style", allow_duplicate=True),
            Output("wizard-upload-data", "filename"),
            Output("wizard-upload-data", "contents"),
            Output("wizard-upload-data", "last_modified"),
            Output("notifications", "children"),
            Output("wizard-file-list", "children"),
            Output("newly-uploaded-data-file", "data") # Just tracks if a new file was added (used in Ocean Sites)
        ],
        Input("wizard-upload-data", "contents"),
        [
            State("wizard-upload-data", "filename"),
            State("current-submission", "data"),
            State("dashboard-user", "data"),
        ],
        prevent_initial_call=True
    )
    def update_data_upload_contents(data_contents, data_filenames, current_submission, current_user):
        if data_contents is None or data_filenames is None:
            return [no_update] * 8

        dashboard_user = json.loads(current_user)
        category = FileCategory.DATA.value
        contents, names = _normalize_upload(data_contents, data_filenames)

        # 2 . -- Guard against adding a subsequent file OR multiple files at once when disabled --
        if not get_config().ALLOW_MULTIPLE_DATA_FILES:
            existing_files = get_data_files(current_submission, category)
            
            # Block if a file already exists OR if the incoming batch contains more than 1 file
            if not existing_files.empty or len(names) > 1:
                n = ddk.Notification(
                        title="Multiple Files Not Allowed",
                        children=[
                            html.P("A submission only allows a single primary data file."),
                            html.P("Please delete the existing file before uploading a replacement.")
                        ],
                        user_dismiss=True,
                        type="danger",
                        timeout=5000,
                        className="makewhite",
                    )
                df_submissions = get_submissions_with_file_lists(dashboard_user['id'], metadata_url)
                df_data = get_data_files(current_submission, category)
                data_files_list = create_file_list_from_dataframe(
                    df_data, current_submission, show_delete=True,
                    context='wizard', empty_message='No data file uploaded yet'
                )
                return [
                    df_submissions.to_dict("records"),
                    VISIBLE_BLOCK,
                    None, None, None, # Explicitly resets the upload component state
                    [n],
                    data_files_list,
                    no_update
                ]

        # 3. -- Directory Setup ----
        Path(os.path.join(UPLOAD_DIRECTORY, str(current_submission))).mkdir(
            parents=True, exist_ok=True
        )

        notifcations = []

        log.debug(f"[update data upload] found some {category} files")
        
        # Absolute failsafe: slice the list to 1 file maximum if multiple files are disabled
        files_to_process = names[:1] if not get_config().ALLOW_MULTIPLE_DATA_FILES else names

        saved_any_new_file = False

        for idx, filename in enumerate(files_to_process):
            log.debug(f"['update_date_upload'] sending {category} file {idx} named {filename}")
            content_type, content_string = contents[idx].split(",")
            if not file_exists(current_submission, filename, category):
                log.debug(f'[update_data_upload] storing {category} file record')
                insert_file(current_submission, filename, content_type, category)
                log.debug(f'[update_date_upload] saving {category} file...')
                save_file_func(current_submission, contents[idx], filename)
                log.debug('[update_data_upload] file saved')
                saved_any_new_file = True
            else:
                n = ddk.Notification(
                        title="File Exists",
                        children=[
                            html.P(f"A {category} file named {filename} already exists in this submission."),
                            html.P("If you want to replace it, delete the existing file from the submission.")
                        ],
                        user_dismiss=True,
                        type="danger",
                        timeout=-1,
                        className="makewhite",
                    )
                notifcations.append(n)
        
        log.debug('[update_data_upload] getting current submission')
        df_submissions = get_submissions_with_file_lists(dashboard_user['id'], metadata_url)
        log.debug('[update_data_upload] getting file in this submission')
        df_data = get_data_files(current_submission, category)

        data_file_list = create_file_list_from_dataframe(
            df_data,
            current_submission,
            show_delete=True,
            context='wizard',
            empty_message="No data files uploaded yet" if get_config().ALLOW_MULTIPLE_DATA_FILES else "No data file uploaded yet"
        )

        newly_updated_signal = str(uuid.uuid4() if saved_any_new_file else no_update)

        return [
            df_submissions.to_dict("records"),
            VISIBLE_BLOCK,
            None, None, None,
            notifcations,
            data_file_list,
            newly_updated_signal
        ]
    
    @app.callback(
    [
        Output("submissions", "rowData", allow_duplicate=True),
        Output("past-submissions", "style", allow_duplicate=True),
        Output("wizard-upload-supplemental", "filename"),
        Output("wizard-upload-supplemental", "contents"),
        Output("wizard-upload-supplemental", "last_modified"),
        Output("notifications", "children", allow_duplicate=True),
        Output("wizard-supplemental-list", "children")
    ],
    Input("wizard-upload-supplemental", "contents"),
    [
        State("wizard-upload-supplemental", "filename"),
        State("current-submission", "data"),
        State("dashboard-user", "data"),
    ],
    prevent_initial_call=True,
    )
    def update_supplemental_upload(supp_contents, supp_names, current_submission, dashboard_user):
        if supp_contents is None:
            return [no_update] * 7


        dashboard_user = json.loads(dashboard_user)
        category = FileCategory.SUPPLEMENTAL.value
        contents, names = _normalize_upload(supp_contents, supp_names)

        Path(os.path.join(UPLOAD_DIRECTORY, str(current_submission))).mkdir(
            parents=True, exist_ok=True
        )

        notifcations = []

        log.debug(f"[update_supplemental_upload] found some {category} files")
        
        for idx, filename in enumerate(names):
            log.debug(f"['update_supplemental_upload'] sending {category} file {idx} named {filename}")
            content_type, content_string = contents[idx].split(",")
            if not file_exists(current_submission, filename, category):
                log.debug(f'[update_supplemental_upload] storing {category} file record')
                insert_file(current_submission, filename, content_type, category)
                log.debug(f'[update_supplemental_upload] saving {category} file...')
                save_file_func(current_submission, contents[idx], filename)
                log.debug('[update_supplemental_upload] file saved')
            else:
                n = ddk.Notification(
                        title="File Exists",
                        children=[
                            html.P(f"A {category} file named {filename} already exists in this submission."),
                            html.P("If you want to replace it, delete the existing file from the submission.")
                        ],
                        user_dismiss=True,
                        type="danger",
                        timeout=-1,
                        className="makewhite",
                    )
                notifcations.append(n)
        
        log.debug('[update_supplemental_upload] getting current submission')
        df_submissions = get_submissions_with_file_lists(dashboard_user['id'], metadata_url)
        log.debug('[update_supplemental_upload] getting supplemental file in this submission')
        df_supp = get_data_files(current_submission, category)

        data_file_list = create_file_list_from_dataframe(
            df_supp,
            current_submission,
            show_delete=True,
            context='wizard',
            empty_message="No supplemental files uploaded yet"
        )

        return [
            df_submissions.to_dict("records"),
            VISIBLE_BLOCK,
            None, None, None,
            notifcations,
            data_file_list
        ]

    @app.callback(
    [
        Output("submissions", "rowData", allow_duplicate=True),
        Output("wizard-file-list", "children", allow_duplicate=True),
        Output("wizard-supplemental-list", "children", allow_duplicate=True)
    ],
    [
        Input({'type': 'wizard-delete-file', 'index': ALL}, 'n_clicks'),
    ],
    [
        State("current-submission", "data"),
        State("dashboard-user", "data"),
    ],
    prevent_initial_call=True,
    )
    def delete_data_file(
        wizard_delete_clicks,
        state_current_submission, 
        state_user
    ):
        # 1. Check if any button was actually clicked
        if not wizard_delete_clicks or not any(click > 0 for click in wizard_delete_clicks if click):
            return [no_update] * 3

        from dash import callback_context
        ctx = callback_context
        if not ctx.triggered:
            return [no_update] * 3
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if 'wizard-delete-file' not in trigger_id:
            return [no_update] * 3

        import json as json_lib
        trigger_dict = json_lib.loads(trigger_id.split('.')[0])
        file_id = trigger_dict['index']

        # Get file info from database
        df_data = get_data_files(state_current_submission, "data")
        df_supp = get_data_files(state_current_submission, "supplemental")

        # Find the file in either dataframe
        filename = None
        category = None

        for _, row in df_data.iterrows():
            if row['id'] == file_id:
                filename = row['filename']
                category = FileCategory.DATA.value
                break
        
        if not filename:
            for _, row in df_supp.iterrows():
                if row['id'] == file_id:
                    filename = row['filename']
                    category = FileCategory.SUPPLEMENTAL.value
                    break
        
        if not filename:
            return [no_update] * 3

        dashboard_user = json.loads(state_user)
        
        log.debug(f"[update_output] Deleteing {category} file: {filename}")
        delete_file(file_id)
        archive_file_func(filename, dashboard_user, state_current_submission)

        # Get updated file lists
        df_data = get_data_files(state_current_submission, "data")
        df_supp = get_data_files(state_current_submission, "supplemental")

        # Use utility function to recreate wizard file lists after deletion
        data_file_list = create_file_list_from_dataframe(
            df_data,
            state_current_submission,
            show_delete=True,
            context='wizard',
            empty_message="No data files uploaded yet" if get_config().ALLOW_MULTIPLE_DATA_FILES else 'No data file uploaded yet'
        )

        supp_file_list = create_file_list_from_dataframe(
            df_supp,
            state_current_submission,
            show_delete=True,
            context='wizard',
            empty_message="No supplemental files uploaded yet"
        )

        if dashboard_user is not None:
            dfs = get_submissions_with_file_lists(
                dashboard_user["id"], metadata_url
            )
            return [dfs.to_dict("records"),
            data_file_list, #updated data file list
            supp_file_list, # updated supp file list
            ]
        else:
            return [no_update] * 3
