"""
Utility functions for the application.
"""
from portal_core.utils.file_operations import sha256sum, save_file, archive_file
from portal_core.utils.assets import portal_asset_url, PORTAL_ASSETS_SEGMENT
from portal_core.utils.preview_utils import make_preview
from portal_core.utils.logger import app_logger
from portal_core.utils.submission_db_utils import (
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
from portal_core.utils.file_display_utils import create_file_list_from_dataframe, _normalize_upload
from portal_core.utils.identifer_utils import create_submission_id
from portal_core.utils.layout_utils import _section_label
from portal_core.utils.clone_submission import clone_submission

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