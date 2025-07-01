from typing import Optional
from datetime import datetime
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


class NestedFlagResponse(BaseModel):
    id: int = Field(..., description="The unique identifier of the flag.")
    name: str = Field(..., description="The name of the flag.")
    is_active: bool = False
    dependencies: list['NestedFlagResponse'] = Field(
        default_factory=list,
        description="List of flags this flag depends on with their full details."
    )

    class Config:
        from_attributes = True
        orm_mode = True


# This is needed for the self-referencing model
NestedFlagResponse.model_rebuild()


class AuditLogCreate(BaseModel):
    flag_id: int = Field(..., description="The ID of the flag being audited.")
    flag_name: str = Field(..., description="The name of the flag being audited.")
    operation: str = Field(..., description="The operation performed (create, toggle, auto-disable, etc.).")
    previous_state: Optional[str] = Field(None, description="JSON string of the previous state.")
    new_state: Optional[str] = Field(None, description="JSON string of the new state.")
    reason: Optional[str] = Field(None, description="Human-readable reason for the operation.")
    actor: Optional[str] = Field(None, description="Who performed the action.")


class AuditLogResponse(BaseModel):
    id: int = Field(..., description="The unique identifier of the audit log entry.")
    flag_id: int = Field(..., description="The ID of the flag being audited.")
    flag_name: str = Field(..., description="The name of the flag being audited.")
    operation: str = Field(..., description="The operation performed.")
    previous_state: Optional[str] = Field(None, description="JSON string of the previous state.")
    new_state: Optional[str] = Field(None, description="JSON string of the new state.")
    reason: Optional[str] = Field(None, description="Human-readable reason for the operation.")
    actor: Optional[str] = Field(None, description="Who performed the action.")
    timestamp: datetime = Field(..., description="When the operation occurred.")

    class Config:
        from_attributes = True
        orm_mode = True