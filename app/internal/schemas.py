from typing import Optional

from pydantic import BaseModel, Field


class FlagBody(BaseModel):
    name: str = Field(..., description="The name of the flag.")
    dependencies: list[int] = Field(
        default_factory=list, description="List of flag ids this flag depends on."
    )


class FlagResponse(BaseModel):
    id: int = Field(..., description="The unique identifier of the flag.")
    name: str = Field(..., description="The name of the flag.")
    is_active: bool = False
    dependencies: list[int] = Field(
        default_factory=list,
        description="List of flag IDs this flag depends on."
    )

    class Config:
        from_attributes = True
        orm_mode = True


class FlagToggle(BaseModel):
    is_active: Optional[bool] = None

 