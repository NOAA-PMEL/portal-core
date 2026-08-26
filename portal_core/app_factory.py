from pathlib import Path
import json, os
import flask 
from dash import Dash, DiskcacheManager, CeleryManager
from celery import Celery

from portal_core.config_loader import init_config
from portal_core.extensions import init_extensions
from portal_core.callbacks import register_callbacks
from portal_core.layouts import get_layout
from portal_core.constants import connection_string
from portal_core.utils import (
    app_logger as log,
    sha256sum, 
    save_file, 
    archive_file,
    PORTAL_ASSETS_SEGMENT, 
    portal_asset_url
)

 # Create an instance of Celery
celery_app = Celery(
    broker=os.environ.get("REDIS_URL", "redis://127.0.0.1:6379"),
    backend=os.environ.get("REDIS_URL", "redis://127.0.0.1:6379"),
)

def create_app(portal, config_path):
    config = init_config(config_path) # BEFORE layouts/callbacks run

    # Designed to make dash app not whether it is running on local computer (for development) 
    # or on a professional server (for production)
    if os.environ.get("DASH_ENTERPRISE_ENV") == "WORKSPACE":
        # For testing...
        import diskcache
        cache = diskcache.Cache("./cache")
        background_callback_manager = DiskcacheManager(cache)
    else:
        # For production...
        background_callback_manager = CeleryManager(celery_app)

    # Create Flask server
    server = flask.Flask(__name__)

    server.config['SQLALCHEMY_DATABASE_URI'] = connection_string

    log.info("Engine: %s", portal.describe())

    # Combine portal-specific assets with base's assets
    ROUTES_PREFIX = os.getenv("DASH_ROUTES_PATHNAME_PREFIX", "/")
    extra_css, extra_js = [], []
    portal_assets = portal.asset_path()
    if portal_assets is not None:
        @server.route(f"{ROUTES_PREFIX}{PORTAL_ASSETS_SEGMENT}/<path:filename>")
        def portal_asset(filename):
            return flask.send_from_directory(str(portal_assets), filename)

        for f in sorted(p for p in portal_assets.iterdir() if p.is_file()):
            url = f"{portal_asset_url(f.name)}?m={int(f.stat().st_mtime)}"
            if f.suffix == ".css":
                extra_css.append(url)
            elif f.suffix == ".js":
                extra_js.append(url)

    app = Dash(
        __name__, 
        server=server,
        assets_folder=str(Path(__file__).parent / "assets"),
        background_callback_manager=background_callback_manager,
        suppress_callback_exceptions=True, # Tells Dash that the layout ids will exist when they are needed
        external_stylesheets=extra_css, # injects portal specific css files to be served (since will be outside of base's assets/ dir)
        external_scripts=extra_js, # injects portal specific js files to be served (since will be outside of base's assets/ dir)
    ) # when writing a callback that takes a long time, can just add background=True
    
    # get submission archives (to put in agGrid.js file)
    @server.route(os.getenv("DASH_ROUTES_PATHNAME_PREFIX", "/") + "archives-config")
    def archives_config():
        return flask.Response(
            json.dumps(config.SUBMISSION_ARCHIVES),
            mimetype="application/json"
    )

    # Initialize extensions (database, CSRF, roles, etc)
    init_extensions(server, portal)

    # Set the application layout
    app.layout = get_layout(app, portal)

    # register callbacks
    register_callbacks(app, save_file, archive_file, sha256sum, portal)
    portal.register_callbacks(app)

    log.debug('Application started...')

    return app
