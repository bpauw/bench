import datetime

from pydantic import BaseModel


class DiscussionEntry(BaseModel):
    """A single discussion entry parsed from the discussions directory."""

    name: str
    filename: str
    created_date: datetime.date
