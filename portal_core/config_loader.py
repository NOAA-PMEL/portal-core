"""
Instance-specifc settings, loaded from a portal's config.yaml file.
"""
from pathlib import Path
import yaml

class Config:
    def __init__(self, path):
        self.path = Path(path)
        with self.path.open("r") as f:
            data = yaml.safe_load(f)

        branding = data["branding"]
        self.ORGANIZATION_NAME = branding["organization_name"]
        self.ORGANIZATION_SHORT_NAME = branding["organization_short_name"]
        self.PAGE_TITLE = branding["page_title"]
        self.VERSION = branding["version"]
        self.HEADER_LOGO = branding["header_logo"]
        self.FOOTER_LOGO = branding["footer_logo"]
        
        contact = data["contact"]
        links = contact["footer_links"]
        self.CONTACT_EMAIL = contact["email"]
        self.FOOTER_ORG_NAME = links["organization"]["text"]
        self.FOOTER_ORG_URL = links["organization"]["url"]
        self.FOOTER_PARENT_ORG_NAME = links["parent_org"]["text"]
        self.FOOTER_PARENT_ORG_URL = links["parent_org"]["url"]
        self.LEGAL_LINKS = links["legal_links"]

        self.ALLOW_MULTIPLE_DATA_FILES = str(data["allow_multiple_data_files_to_submit"]).strip().lower() in ['true', '1', 'yes']

        # submissona archives
        self.SUBMISSION_ARCHIVES = data.get('submission_archives', [])

_config = None

def init_config(path):
    """Called once by create_app(), before any layout or callback runs."""
    global _config
    _config = Config(path)
    return _config

def get_config():
    if _config is None:
        raise RuntimeError(
            "Config not initialized. Base must be entered through create_app(), "
            "which calls init_config() first."
        )
    return _config
                