from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, DateTime, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

from app.internal.database import Base

# Association table for self-referencing relationship
flag_dependencies_association = Table(
    "flag_dependencies",
    Base.metadata,
    Column("flag_id", Integer, ForeignKey("flags.id"), primary_key=True),
    Column("dependent_flag_id", Integer, ForeignKey("flags.id"), primary_key=True),
)


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(index=True, unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False)

    dependencies = relationship(
        "Flag",
        secondary=flag_dependencies_association,
        primaryjoin=id == flag_dependencies_association.c.flag_id,
        secondaryjoin=id == flag_dependencies_association.c.dependent_flag_id,
        backref="dependents",
    )

    def __repr__(self):
        # Get the names of the dependencies, or an empty list if there are none
        dependency_names = [dep.name for dep in self.dependencies]
        return f"<Flag(id={self.id}, name='{self.name}', is_active={self.is_active}, dependencies={dependency_names})>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    flag_id: Mapped[int] = mapped_column(ForeignKey("flags.id"), nullable=False, index=True)
    flag_name: Mapped[str] = mapped_column(nullable=False)
    operation: Mapped[str] = mapped_column(nullable=False)  # create, toggle, auto-disable, etc.
    previous_state: Mapped[str] = mapped_column(nullable=True)  # JSON string of previous state
    new_state: Mapped[str] = mapped_column(nullable=True)  # JSON string of new state
    reason: Mapped[str] = mapped_column(Text, nullable=True)  # Human-readable reason
    actor: Mapped[str] = mapped_column(nullable=True)  # Who performed the action
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship to flag
    flag = relationship("Flag", backref="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, flag_id={self.flag_id}, operation='{self.operation}', timestamp='{self.timestamp}')>"
