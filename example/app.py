from pathlib import Path
from portal_core.app_factory import create_app
from example.engine import Engine

app = create_app(Engine(), Path(__file__).parent / "config.yaml")
server = app.server

if __name__ == "__main__":
    app.run(
        debug=True,
    )