import os
import redis
from sqlalchemy import create_engine

VISIBLE_BLOCK = {"display": ""}
HIDDEN_BLOCK = {"display": "none"}

# Deployments MUST set these to in Dash's environment variables on a persistent volume
for directory in ["UPLOAD_DIRECTORY", "ARCHIVE_DIRECTORY", "BAG_DIRECTORY", "TAR_DIRECTORY"]:
    if directory not in os.environ:
        from portal_core.utils.logger import app_logger as log
        log.error(f"{directory} not set. Must set directory in Dash's environment.")

UPLOAD_DIRECTORY = os.environ.get("UPLOAD_DIRECTORY")
ARCHIVE_DIRECTORY = os.environ.get("ARCHIVE_DIRECTORY")
BAG_DIRECTORY = os.environ.get("BAG_DIRECTORY")
TAR_DIRECTORY = os.environ.get("TAR_DIRECTORY")

submissions_table = "submission"
files_table = "file"
connection_string = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:docker@127.0.0.1:5432"
)

if os.environ.get("DASH_ENTERPRISE_ENV") == "WORKSPACE":
    route_prefix = "/workspace/view/workspace-data-submit/"
else:
    route_prefix = "/data-submit/"

metadata_url = route_prefix + "metadata?submission_id="

# NOTE: this pool is created at import time, i.e. per gunicorn worker, because
# gunicorn does not preload by default. If --preload is ever added to a portal's
# Procfile, the pool would be created in the master process and every forked 
# worker would inherit the samp TCP connections -- which is exactly the 
# "server close dthe connection unexpectedly." failure referenced below. If you
# add --preload, add a post_fork hook calling postgres_engine.dispose()
postgres_engine = create_engine(
    connection_string,
    pool_pre_ping=True,
    pool_recycle=3600,  # this line might not be needed
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

redis_instance = redis.StrictRedis.from_url(
    os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")
)

# ---------------------------------------------------------
# Moved from arctic/constants (used in ocean_sites as well)
# ---------------------------------------------------------
_OVERLAY_BASE = {
            'position': 'fixed',
            'top': 0,
            'left': 0,
            'right': 0,
            'bottom': 0,
            'backgroundColor': 'rgba(0, 0, 0, 0.5)',
            'zIndex': 998,
            'cursor': 'pointer'
        }
_OVERLAY_HIDDEN = {**_OVERLAY_BASE, 'display': 'none'}  
_OVERLAY_VISIBLE = {**_OVERLAY_BASE, 'display': 'block'}

_PANEL_BASE = {
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
    'color': '#e0e0e0'  # Light text
}
_PANEL_CLOSED = {**_PANEL_BASE, 'right': '-600px'}
_PANEL_OPEN = {**_PANEL_BASE, 'right': '0'}

_FONT_SIZE_LABEL = '11px'

_BG_INPUT = '#1e1e1e'
_BORDER_COLOR = '#3a3a3a'
_TEXT_COLOR = '#e0e0e0'
_FONT_SIZE_INPUT = '12px'
_INPUT_HEIGHT = '34px'

_input_style = {
    'width': '100%',
    'backgroundColor': _BG_INPUT,
    'border': f'1px solid {_BORDER_COLOR}',
    'borderRadius': '4px',
    'color': _TEXT_COLOR,
    'padding': '6px 10px',
    'fontSize': _FONT_SIZE_INPUT,
    'boxSizing': 'border-box',
    'height': _INPUT_HEIGHT
}

_dropdown_style = {
    'backgroundColor': _BG_INPUT,
    'color': _TEXT_COLOR,
    'fontSize': _FONT_SIZE_INPUT,
}

_label_style = {
    'color': '#999', 
    'fontSize': _FONT_SIZE_LABEL,
    'marginBottom': '4px',
    'display': 'block'
} 

_section_label_style = {
    'fontSize': '11px',
    'fontWeight': '600',
    'color': '#4f8ef7',
    'textTransform': 'uppercase',
    'letterSpacing': '0.08em',
    'marginBottom': '2px',
    'display': 'flex',
    'alignItems': 'center',
    'gap': '8px'
}

_hr_style = {
    'flex': 1,
    'border': 'none',
    'borderTop': '1px solid #2e2e2e',
    'margin': 0
}

# ---------------------------------------------------------
# Moved from arctic/constants (used in ocean_sites as well)
# ---------------------------------------------------------