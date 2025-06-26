from database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

# Association table for self-referencing relationship
flag_dependencies_association = Table(
    "flag_dependencies",
    Base.metadata,
    Column("flag_id", Integer, ForeignKey("flags.id"), primary_key=True),
    Column("dependent_flag_id", Integer, ForeignKey("flags.id"), primary_key=True),
)


class Flag(Base):
    __tablename__ = "flags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True, nullable=False)
    is_active = Column(Boolean, default=False)

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
