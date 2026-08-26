"""
Callbacks related to user authentication and initalization
"""
from dash import Input, Output
from sqlalchemy.orm import Session
import json

from portal_core.constants import (
    postgres_engine,
    redis_instance,
    metadata_url,
    VISIBLE_BLOCK
)
from portal_core.models.metadata import DashboardUser
from portal_core.utils import (
    lookup_use_by_email,
    get_submissions_with_file_lists
)

def register_user_callbacks(app):
    """Register user-related callbacks."""

    @app.callback(
    [
        Output("dashboard-user", "data"),
        Output("user-welcome", "children"),
        Output("submissions", "rowData", allow_duplicate=True),
        Output("past-submissions", "style", allow_duplicate=True)
    ],
    [
        Input("header", "children"),
    ],
    prevent_initial_call="initial_duplicate",
    )
    def get_and_store_username(dontcare):
        """
        Initialize user session when app loads.
        Gets user email and stores user info in Redis
        """
        # This callback runs once at the beginning
        # DEBUG -- This is basic auth BS. We would never do this for a "real" application
        # username = request.authorization["username"]

        # Or using enterprise auth
        # email = auth.get_username()

        email = "roland.schweitzer@noaa.gov"

        # jsonify is huge overkill. It makes a response type from which you must extract the data,
        # but it does the serilization to json completely, correctly and automatically.
        dashboard_user = lookup_use_by_email(email)

        if dashboard_user is None:
            try:
                with Session(postgres_engine) as session:
                    dashboard_user = DashboardUser(email=email)
                    session.add(dashboard_user)
                    session.commit()
                    session.refresh(dashboard_user)
            except Exception:
                # If another process created the user simultaneously, 
                # the database will reject our insert. We just fetch the winner.
                dashboard_user = lookup_use_by_email(email)

        simple_user = {"id": dashboard_user.id, "email": dashboard_user.email}
        
        redis_i = redis_instance
        redis_i.hset("cache", "dashboard_user", json.dumps(simple_user))

        # Get user's submission and set visibility
        df_submissions = get_submissions_with_file_lists(
            simple_user["id"], metadata_url
        )
        df_submissions = df_submissions.sort_values(by="date_created", ascending=False) # sort newest submission first

        # Show the card if there are submissions, hide if empty
        submissions_style = VISIBLE_BLOCK if not df_submissions.empty else {"display": "none"}

        return [json.dumps(simple_user), 
        "You are currently logged in as " + str(email),
        df_submissions.to_dict("records"),
        submissions_style]