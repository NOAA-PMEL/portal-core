"""
Utility functions for the application.
"""
from .file_operations import sha256sum, save_file, archive_file
from .assets import portal_asset_url, PORTAL_ASSETS_SEGMENT
from .preview_utils import make_preview
from .logger import app_logger
from .submission_db_utils import (
    delete_file,
    delete_submission,
    get_data_files,
    file_exists,
    lookup_use_by_email,
    get_submissions_with_file_lists,
    get_submissions_with_counts,
    insert_file,
    insert_submission,
    get_or_create_oads_metadata_id,
    get_oads_metadata_id
)
from .file_display_utils import create_file_list_from_dataframe, _normalize_upload
from .identifer_utils import create_submission_id
from .layout_utils import _section_label
from .clone_submission import clone_submission

__all__ = [
    'sha256sum', 
    'save_file', 
    'archive_file',
    'portal_asset_url',
    'PORTAL_ASSETS_SEGMENT',
    'make_preview',
    'app_logger',
    'delete_file',
    'delete_submission',
    'get_data_files',
    'file_exists',
    'lookup_use_by_email',
    'get_submissions_with_file_lists',
    'get_submissions_with_counts',
    'insert_file',
    'insert_submission',
    'get_or_create_oads_metadata_id',
    'get_oads_metadata_id',
    'create_file_list_from_dataframe',
    'create_submission_id',
    '_section_label',
    "_normalize_upload",
    "clone_submission"
]