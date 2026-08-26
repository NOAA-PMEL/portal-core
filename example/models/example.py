"""
The example portal's one extension table.

Exists so load_models() has something to discover and clone_metadata() has 
something to copy. Discovered by convention -- nothing registers it explicitly
it just lives in a folder title models/
"""
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from portal_core.models.base import Base


class ExampleNote(Base):
    """A free-text note attached to a metadata record."""
    __tablename__ = "example_note"

    id: Mapped[int] = mapped_column(primary_key=True)
    oads_metadata_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("oads_metadata.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[Optional[str]] = mapped_column(String(500))