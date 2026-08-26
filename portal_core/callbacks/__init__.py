"""
Dash callback for the application
"""
from portal_core.callbacks.user_callbacks import register_user_callbacks
from portal_core.callbacks.file_callbacks import register_file_callbacks
from portal_core.callbacks.grid_callbacks import register_grid_callbacks
from portal_core.callbacks.preview_callbacks import register_preview_callbacks
from portal_core.callbacks.wizard_callbacks import register_wizard_callbacks
from portal_core.callbacks.metadata_modal_callbacks import register_metadata_modal_callbacks


def register_callbacks(app, save_file, archive_file, sha256sum, portal):
    """
    Register all Dash callbacks with the app.

    Args:
        app: Dash application instance
        save_file: Function to save uploaded files
        archive_file: Function to archive deleted files
        sha256sum: Function to compute SHA256 hash
    """
    register_user_callbacks(app)
    register_wizard_callbacks(app)
    register_file_callbacks(app, save_file, archive_file)
    register_grid_callbacks(app, sha256sum, portal)
    register_preview_callbacks(app)
    register_metadata_modal_callbacks(app)
   