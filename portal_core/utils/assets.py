import os

PORTAL_ASSETS_SEGMENT = "portal-assets"

def portal_asset_url(filename: str) -> str:
    """
    Browser-facing URL for a file in <portal>/assets/.
    """
    prefix = os.getenv(
        "DASH_REQUESTS_PATHNAME_PREFIX",
        os.getenv("DASH_ROUTES_PATHNAME_PREFIX", "/"),
    )
    return f"{prefix}{PORTAL_ASSETS_SEGMENT}/{filename}"