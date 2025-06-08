from typing import Optional
from sqlmodel import SQLModel, Field


class Flag(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, index=True)
    name: str
    dependencies: list["Flag"] = []
    is_active: bool = False