"""
Initialize all application extensions (Celery, Database, CSRF, etc.)

NOTE: CSRFPRotect is instantiated below but not wired up -- init_app() is 
commented out, so CSRF proection is NOT active. A preveious attempt stalled on
exempting Dash's _dash-update-component endpoint, which sends no token. 
"""
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import select
from sqlalchemy.orm import Session
from portal_core.constants import postgres_engine
from portal_core.models import db, MetadataRole
from portal_core.utils.logger import app_logger as log
from portal_core.db_setup import init_db


# CSRF Protection
csrf_protect = CSRFProtect()

# Global role variables (loaded after app initialization)
data_submitter_role = None
investigator_role = None

def init_extensions(server, portal):
    """
    Initialize all extensions with the Flask server.

    Args:
        server: Flask server instance
    """
    # Initialize database
    db.init_app(server)

    # Create all tables
    with server.app_context():
        init_db(portal)

  
    # Load metadata_roles()
    _load_metadata_roles()


def _load_metadata_roles():
    """
    Load the standard metadata roles from the database.
    Sets global data_submitter_role and investigator_role.
    """
    global data_submitter_role, investigator_role

    with Session(postgres_engine) as session:
        try:
            stmt = select(MetadataRole).where(MetadataRole.name == "Data Submitter")
            data_submitter_role = session.scalars(stmt).one()
            stmt2 = select(MetadataRole).where(MetadataRole.name == "Investigator")
            investigator_role = session.scalars(stmt2).one()
            # Detach these items from their session to allow reuse below
        except Exception as e:
            log.error(e)
            log.error("Exception occurred. Rolling back session.")
            session.rollback()
        finally:
            session.close()

def get_data_submitter_role():
    """Get the data submitter role"""
    return data_submitter_role

def get_investigator_role():
    """Get the investigator role."""
    return investigator_role