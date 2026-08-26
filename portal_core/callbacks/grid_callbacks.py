"""
Callback for grid interactions (cell clicks, submissions grid).
"""
import os
import shutil 
from datetime import datetime
from pathlib import Path
from dash import Input, Output, State, no_update, exceptions, html
import dash_design_kit as ddk
from distutils.dir_util import copy_tree
import json
import bagit
from sqlalchemy.orm import Session
from pydantic import TypeAdapter
from pydantic.json import pydantic_encoder
import pandas as pd

from portal_core.constants import (
    UPLOAD_DIRECTORY,
    ARCHIVE_DIRECTORY,
    metadata_url,
    VISIBLE_BLOCK,
    HIDDEN_BLOCK,
    postgres_engine,
    BAG_DIRECTORY,
    TAR_DIRECTORY
)
import portal_core.sftp.local_sftp as lsftp
from portal_core.models.metadata import Submission, SubmissionSchema
from portal_core.utils import (
    app_logger as log,
    clone_submission,
    delete_submission,
    get_submissions_with_file_lists,
    get_data_files
)


def register_grid_callbacks(app, sha256sum_func, portal):
    """
    Register grid interaction callbacks.
    
    Args:
        app: Dash app instance
        sha256sum_func: Function to compute SHA256 hash
    """
    # Handle selection changes to show/hide bulk actions bar
    @app.callback(
        [
            Output("bulk-actions-bar", "style"),
            Output("selection-count", "children"),
            Output("selected-submissions", "data")
        ],
        [
            Input("submissions", "selectedRows"),
        ],
        prevent_initial_call=True
    )
    def handle_selection_change(selected_rows):
        """Update bulk actions bar when row selection changes."""
        if not selected_rows or len(selected_rows) ==0:
            return(
               { "display": "none"},
               "",
               []
            )
        
        # Show bulk actions bar with selection count
        count = len(selected_rows)
        selected_ids = [row.get("id") for row in selected_rows if "id" in row]

        return(
            {
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
                "padding": "12px 20px",
                "background": "#1e1e1e",
                "borderRadius": "4px",
                "marginBottom": "12px",
                "border": "1px solid #555"
            },
            f"{count} submission{'s' if count != 1 else ''} selected",
            selected_ids
        )

    # Show the modal when delete selected is clicked
    @app.callback(
        [
            Output("delete-confirm-modal", "style"),
            Output("delete-modal-message", "children"),
            Output("pending-delete-ids", "data"),
        ],
        [
            Input("bulk-delete-btn", "n_clicks")
        ],
        [
            State("selected-submissions", "data")
        ],
        prevent_initial_call=True
    )
    def show_delete_modal(n_clicks, selected_ids):
        if not n_clicks or not selected_ids:
            raise exceptions.PreventUpdate

        count = len(selected_ids)
        noun = "submission" if count == 1 else "submissions"
        message = f"Are you sure you want to delete {count} {noun}?"

        return (
            {"display": "block"},
            message, 
            selected_ids # saves what we are about to delete in the store
        )

    # Show the modal when clone selected is clicked
    @app.callback(
        [
            Output("clone-confirm-modal", "style"),
            Output("clone-modal-message", "children"),
            Output("pending-clone-ids", "data"),
        ],
        [
            Input("bulk-clone-btn", "n_clicks")
        ],
        [
            State("selected-submissions", "data")
        ],
        prevent_initial_call=True
    )
    def show_clone_modal(n_clicks, selected_ids):
        if not n_clicks or not selected_ids:
            raise exceptions.PreventUpdate

        count = len(selected_ids)
        noun = "submission" if count == 1 else "submissions"
        message = f"Full copies of {count} {noun} will be created - including all metadata. DOIs will NOT be carried over. Clones will open as new drafts."

        return (
            {"display": "block"},
            message, 
            selected_ids # saves what we are about to delete in the store
        )

    @app.callback(
        [
            Output("clone-confirm-modal", "style", allow_duplicate=True),
            Output("pending-clone-ids", "data", allow_duplicate=True),
        ],
        [
            Input("clone-cancel-btn", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def hide_clone_modal(n_clicks):
        if not n_clicks:
            raise exceptions.PreventUpdate
        return {"display": "none"}, []

    # Cancel button in delete modal will hide modeal and clear pending
    @app.callback(
        [
            Output("delete-confirm-modal", "style", allow_duplicate=True),
            Output("pending-delete-ids", "data", allow_duplicate=True),
        ],
        [
            Input("delete-cancel-btn", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def hide_delete_modal(n_clicks):
        if not n_clicks:
            raise exceptions.PreventUpdate
        return {"display": "none"}, []

    # Confirm deleted in modal and actually delete
    @app.callback(
        [
            Output("submissions", "rowData", allow_duplicate=True),
            Output("past-submissions", "style", allow_duplicate=True),
            Output("submissions", "selectedRows", allow_duplicate=True),
            Output("notifications", "children", allow_duplicate=True),
            Output("delete-confirm-modal", "style", allow_duplicate=True),
            Output("current-submission", "data", allow_duplicate=True)
        ],
        [
            Input("delete-confirm-btn", "n_clicks")
        ],
        [
            State("pending-delete-ids", "data"),
            State("dashboard-user", "data")
        ],
        prevent_initial_call=True
     )
    def handle_confirmed_delete(n_clicks, selected_ids, state_user):
        print(f"DEBUG handle_confirmed_delete: selected_ids: {selected_ids}")
        if not n_clicks or not selected_ids:
            raise exceptions.PreventUpdate
        
        dashboard_user = json.loads(state_user)

        deleted_count = 0
        for submission_id in selected_ids:
            try:
                delete_submission(submission_id, dashboard_user["id"])
                # Archive the entire submission directory all at once
                to_move = os.path.join(UPLOAD_DIRECTORY, str(submission_id))
                destination = os.path.join(
                    ARCHIVE_DIRECTORY,
                    str(submission_id) + "." + datetime.now().isoformat(),
                )
                if os.path.isdir(to_move):
                    shutil.move(to_move, destination)
                deleted_count += 1
            except Exception as e:
                log.error("Error deleted submission {submission_id}: {e}")

        # Show success notification
        n = html.Div(
                f"✅ Successfully deleted {deleted_count} submission{'s' if deleted_count != 1 else ''}",
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

        # Refresh submission grid
        df = get_submissions_with_file_lists(
            dashboard_user["id"], metadata_url
        )
        df = df.sort_values(by="date_created", ascending=False) # sort by most recent
        
        submissions_visibility = VISIBLE_BLOCK
        if df.empty:
            submissions_visibility = HIDDEN_BLOCK

        return (
            df.to_dict("records"),
            submissions_visibility,
            [],
            [n],
            {"display": "none"}, # hide the modal
            None # reset current-submission
        )

    # Handle cancel selection button
    @app.callback(
        [
            Output("submissions", "selectedRows", allow_duplicate=True)
        ], 
        [
            Input("cancel-selection-btn", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def handle_cancel_selection(n_clicks):
        """Clear all row selections."""
        if not n_clicks:
            raise exceptions.PreventUpdate
        return[[]] # Empty list clears all selections


    @app.callback(
        [
            Output("past-submissions", "style", allow_duplicate=True),
            Output("files", "options", allow_duplicate=True),
            Output("files", "value", allow_duplicate=True),
            Output("preview-card", "style", allow_duplicate=True),
        ],
        [
            Input("file-click-store", "data"),
        ],
        [
            State("dashboard-user", "data"),
            State("submissions", "rowData"),
        ],
        prevent_initial_call=True
    )
    def handel_data_file_click(in_file_clicked, state_user, state_row_data):
        log.debug('[handel_data_file_click] entering callback')
        if not in_file_clicked:
            return [no_update] * 4
        
        filename = in_file_clicked.get("filename")
        db_id = in_file_clicked.get("db_id")
        
        log.debug(f'filename={filename}, db_id={db_id}')
        dashboard_user = json.loads(state_user)
        notifications = []
        submission_id = db_id

        file_value = None
        files = get_data_files(submission_id, 'data')
        if len(files) > 0:
            file_options = []
            for file in files["filename"]:
                file_path = f"{UPLOAD_DIRECTORY}/{submission_id}/{file}"
                file_options.append({"label": file, "value": file_path})
                if filename == file:
                    file_value = file_path
            if not file_value:       
                file_value = file_options[0]["value"]
            
            return [
                HIDDEN_BLOCK,  # past-submissions style
                file_options,            # files options
                file_value,              # files value
                VISIBLE_BLOCK, # preview-card style
            ]
        return [no_update] * 4



    @app.callback(
        [
            Output("submissions", "rowData", allow_duplicate=True),
            Output("notifications", "children", allow_duplicate=True),
        ],
        [
            Input("archive-click-store", "data"),
        ],
        [
            State("dashboard-user", "data"),
            State("submissions", "rowData"),
        ],
        prevent_initial_call=True
    )
    def handle_archive_click(in_clicked_row, state_user, state_row_data):
        log.debug('[handel_archive_click] entering callback')
        if not in_clicked_row:
            return [no_update, no_update]
        
        submission_id = in_clicked_row.get("db_id")
        
        log.debug(f'[handle_archive_click] submission_id={submission_id}')
        dashboard_user = json.loads(state_user)
        notifications = []

        file_value = None
        files = get_data_files(submission_id, 'data')


        # --- 3. SUBMIT TO NCEI LOGIC ---

        du = dashboard_user["email"].replace("@", "_at_")
        
        with Session(postgres_engine) as session:
            try:
                submission = session.query(Submission).filter(Submission.id == submission_id).one()
                
                if submission.submitted_to_ncei:
                    # n = ddk.Notification(title="Already Submitted", type="danger", timeout=5000)
                    n = html.Div(
                        "⚠️ Already Submitted",  # Added an optional warning emoji to fit the theme
                        style={
                            'backgroundColor': 'rgba(252, 211, 77, 0.15)', # Soft yellow/amber tint (slightly higher opacity for visibility)
                            'border': '1px solid rgba(252, 211, 77, 0.4)',  # Subtle yellow/amber border
                            'borderRadius': '4px',
                            'color': '#d97706',                             # High-contrast amber text for easy reading
                            'padding': '10px 14px',
                            'fontSize': '13px',
                            'marginBottom': '10px',
                            'fontWeight': '500'
                        }
                    )
                    return [no_update, [n]]

                submission.date_submitted_to_ncei = datetime.now()
                submission.submitted_to_ncei = True
                session.add(submission)
                
                adapter = TypeAdapter(SubmissionSchema)
                if submission.oads_metadata is not None:
                    submission_schema = adapter.validate_python(submission)
                else:
                    # n = ddk.Notification(title="Metadata record required", type="danger")
                    n = html.Div(
                        "⚠️ Metadata record required",  # Added an optional warning emoji to fit the theme
                        style={
                            'backgroundColor': 'rgba(252, 211, 77, 0.15)', # Soft yellow/amber tint (slightly higher opacity for visibility)
                            'border': '1px solid rgba(252, 211, 77, 0.4)',  # Subtle yellow/amber border
                            'borderRadius': '4px',
                            'color': '#d97706',                             # High-contrast amber text for easy reading
                            'padding': '10px 14px',
                            'fontSize': '13px',
                            'marginBottom': '10px',
                            'fontWeight': '500'
                        }
                    )
                    
                    return [no_update, [n]]

                # Generate JSON and Bag
                submission_json = os.path.join(UPLOAD_DIRECTORY, str(submission.id), "submission.json")
                with open(submission_json, "w") as f:
                    f.write(json.dumps(submission_schema, default=pydantic_encoder, indent=4))
                
                contact = f"{submission.oads_metadata.data_submitter[0].first_name} {submission.oads_metadata.data_submitter[0].last_name}"
                ds = submission.oads_metadata.data_submitter[0].contact_information.email.replace("@", "_at_")
                
                bag_dir = os.path.join(BAG_DIRECTORY, f"bag_{submission.id}")
                tar_dir = os.path.join(TAR_DIRECTORY, f"bag_{submission.id}")
                submission_dir = os.path.join(UPLOAD_DIRECTORY, str(submission.id))

                if os.path.exists(bag_dir): shutil.rmtree(bag_dir)
                if os.path.exists(tar_dir): shutil.rmtree(tar_dir)
                Path(bag_dir).mkdir(parents=True, exist_ok=True)
                Path(tar_dir).mkdir(parents=True, exist_ok=True)
                
                copy_tree(submission_dir, bag_dir)
                bagit.make_bag(bag_dir, {"Contact-Name": contact})
                
                bag_tar = os.path.join(tar_dir, "bag")
                shutil.make_archive(bag_tar, "tar", bag_dir)
                
                hash_val = sha256sum_func(bag_tar + ".tar")
                with open(bag_tar + ".sha", "w") as s: s.write(hash_val)

                # SFTP Transfer
                lsftp.send_bag(bag_tar + ".sha", du, ds, submission.id)
                lsftp.send_bag(bag_tar + ".tar", du, ds, submission.id)
                
                session.commit()
                df = get_submissions_with_file_lists(dashboard_user["id"], metadata_url)
                n = html.Div(
                        f"✅ Submission Successful",
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
                # n = ddk.Notification(title="Submission Successful", type="info", timeout=5000)
                
                return [
                    df.to_dict("records"),
                    [n]
                ]

            except Exception as e:
                session.rollback()
                n = ddk.Notification(title="Error", children=[html.P(str(e))], type="danger")
                return [no_update, 
                [n]]
            finally:
                session.close()

    @app.callback(
        [
            Output("submissions", "rowData", allow_duplicate=True),
            Output("past-submissions", "style", allow_duplicate=True),
            Output("submissions", "selectedRows", allow_duplicate=True),
            Output("notifications", "children", allow_duplicate=True),
            Output("clone-confirm-modal", "style", allow_duplicate=True),
            Output("pending-clone-ids", "data", allow_duplicate=True),
            Output("new-submission-ids", "data", allow_duplicate=True)
        ],
        [
            Input("clone-confirm-btn", "n_clicks")
        ],
        [
            State("pending-clone-ids", "data"),
            State("dashboard-user", "data")
        ],
        prevent_initial_call=True  
    )
    def handle_confirmed_clone(n_clicks, pending_ids, state_user):
        if not n_clicks or not pending_ids:
            raise exceptions.PreventUpdate

        dashboard_user = json.loads(state_user)
        cloned_count = 0
        errors = []

        actual_new_ids = []

        for submission_id in pending_ids:
            try:
                created_id = clone_submission(submission_id, dashboard_user["id"], portal)
                actual_new_ids.append(str(created_id))
                cloned_count += 1
            except Exception as e:
                log.error(f"Error cloning submission {submission_id}: {e}")
                errors.append(submission_id)

        # Build notification
        if errors:
            n = html.Div(
                f"❌ Failed to clone: {', '.join(errors)}",
                style={
                    'backgroundColor': 'rgba(255, 107, 107, 0.1)',  # Soft red tint
                    'border': '1px solid rgba(255, 107, 107, 0.3)', # Subtle red border
                    'borderRadius': '4px',
                    'color': '#ff6b6b',                             # Bright error red/coral
                    'padding': '10px 14px',
                    'fontSize': '13px',
                    'marginBottom': '10px',
                    'fontWeight': '500'                             # Optional: added slight weight for readability
                }
            )
        else:
            n = html.Div(
                f"✅ Successfully cloned {cloned_count} submission{'s' if cloned_count != 1 else ''}. Clone(s) have been created as new submissions.",
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
           
        # Refresh the grid
        df = get_submissions_with_file_lists(
            dashboard_user["id"], metadata_url
        )

        df = df.sort_values(by="date_created", ascending=False)
        # Force cloned rows to the top regardless of timestamp
        if actual_new_ids:
            new_rows = df[df['id'].astype(str).isin(actual_new_ids)]
            old_rows = df[~df['id'].astype(str).isin(actual_new_ids)]
            df = pd.concat([new_rows, old_rows], ignore_index=True)
        
        # Inject the is_new flag straight into the DataFrame data
        if not df.empty:
            df['is_new'] = df['id'].astype(str).isin(actual_new_ids)
        else:
            df['is_new'] = False

        submissions_visibility = VISIBLE_BLOCK
        if df.empty:
            submissions_visibility = HIDDEN_BLOCK

        return (
            df.to_dict("records"),
            submissions_visibility,
            [], # clear selected rows
            [n],
            {"display": "none"}, # hide bulk check modal
            [], # clear pending store
            actual_new_ids # all cloned IDs get added to new submission store (For the new badge on the grid.)
        )