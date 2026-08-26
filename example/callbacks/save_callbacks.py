"""
Saves this example portal's one extension table.

Exists so clone_metadata() has something to clone -- a clone test is meaningless
if no ExampleNote rows are ever written. Also the only coverage base has for a 
portal writing to its own tables from a callback.

Discovered by convention, like every other module in example/callbacks/.

Wiring notes:
    btn-save-metadata       base's save button, in the modal footer
    current-submission      base's store, holds the open submission id
    metadata-save-status    base's status line, next to the save button

The submission -> oads_metadata lookup is the piece a real portal will also
need; base does not hand it to you.
"""

from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from sqlalchemy.orm import Session

from portal_core.constants import postgres_engine
from portal_core.models.metadata import OadsMetadata
from example.models.example import ExampleNote
from portal_core.utils import get_or_create_oads_metadata_id

def register_callbacks(app):

    @app.callback(
        Output("metadata-save-status", "children", allow_duplicate=True),
        Input('btn-save-metadata', "n_clicks"),
        State("example-notes-input", "value"),
        State("current-submission", "data"),
        prevent_initial_call=True,
    )
    def save_note(n_clicks, text, submission_id):
        if not n_clicks or not submission_id:
            raise PreventUpdate

        with Session(postgres_engine) as session:
            
            oads_id = get_or_create_oads_metadata_id(session=session, submission_id=submission_id)

            note = (
                session.query(ExampleNote)
                .filter_by(oads_metadata_id=oads_id)
                .first()
            )
            if note is None:
                note = ExampleNote(oads_metadata_id=oads_id)
                session.add(note)
                note.text = text or ""
                session.commit()
        
        return "Saved."
