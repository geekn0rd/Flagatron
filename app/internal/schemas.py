from typing import List, Optional

from pydantic import BaseModel, Field


class FlagBase(BaseModel):
    name: str = Field(..., description="The name of the flag.")
    is_active: bool = False
    dependencies: List["FlagBase"] = Field(
        default_factory=list, description="List of flags this flag depends on."
    )

    class Config:
        from_attributes = True
        orm_mode = True


class FlagUpdate(FlagBase):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    dependencies: Optional[List[int]] = None


class FlagInDB(FlagBase):
    id: int = Field(..., description="The unique identifier of the flag.")
