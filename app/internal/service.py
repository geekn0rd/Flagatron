from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.internal.models import Flag
from app.internal.schemas import FlagBody, FlagResponse


def has_circular_dependency(flag_id: int, dependencies: list[int], db: Session) -> bool:
    """
    Returns True if adding any of the dependencies would create a circular dependency for flag_id.
    """
    visited = set()
    stack = list(dependencies)
    while stack:
        current_id = stack.pop()
        if current_id == flag_id:
            return True
        if current_id in visited:
            continue
        visited.add(current_id)
        current_flag = db.query(Flag).filter(Flag.id == current_id).first()
        if current_flag:
            stack.extend([dep.id for dep in current_flag.dependencies])
    return False


def validate_dependencies(dependencies: list[int], db: Session) -> list[Flag]:
    """
    Validates that all dependency IDs exist and returns the Flag objects.
    Raises HTTPException if any dependency is not found.
    """
    deps = db.query(Flag).filter(Flag.id.in_(dependencies)).all()
    if len(deps) != len(dependencies):
        raise HTTPException(status_code=400, detail="One or more dependencies not found.")
    return deps


def check_dependencies_active(flag: Flag) -> None:
    """
    Checks if all dependencies of a flag are active.
    Raises HTTPException if any dependency is inactive.
    """
    if not all(dep.is_active for dep in flag.dependencies):
        raise HTTPException(status_code=400, detail="All dependencies must be active to activate this flag.")


def check_no_dependent_flags(flag_id: int, db: Session) -> None:
    """
    Checks if any other active flag depends on the given flag.
    Raises HTTPException if dependent flags exist.
    """
    dependent_flags = db.query(Flag).filter(
        Flag.dependencies.any(id=flag_id),
        Flag.is_active == True
    ).all()
    if dependent_flags:
        flag_names = [flag.name for flag in dependent_flags]
        if len(flag_names) == 1:
            detail = f"Cannot deactivate: flag '{flag_names[0]}' depends on this flag."
        else:
            names_str = "', '".join(flag_names)
            detail = f"Cannot deactivate: flags '{names_str}' depend on this flag."
        raise HTTPException(status_code=400, detail=detail)


def create_flag_service(flag_in: FlagBody, db: Session) -> Flag:
    """
    Creates a new flag with validation for duplicates and circular dependencies.
    """
    # Check for duplicate flag name
    existing = db.query(Flag).filter(Flag.name == flag_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Flag with this name already exists.")

    new_flag = Flag(name=flag_in.name)

    if flag_in.dependencies:
        # Prevent circular dependency (use temp_id since new_flag.id is not set yet)
        temp_id = -1
        if has_circular_dependency(temp_id, flag_in.dependencies, db):
            raise HTTPException(status_code=400, detail="Circular dependency detected.")
        
        # Validate dependencies exist
        deps = validate_dependencies(flag_in.dependencies, db)
        new_flag.dependencies = deps

    db.add(new_flag)
    db.commit()
    db.refresh(new_flag)
    return new_flag


def toggle_flag_service(flag_id: int, db: Session) -> Flag:
    """
    Toggles a flag's active state with dependency validation.
    """
    flag_db = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag_db:
        raise HTTPException(status_code=404, detail="Flag not found.")
    
    if flag_db.is_active == False:
        # Activating: check that all dependencies are active
        check_dependencies_active(flag_db)
        flag_db.is_active = True
    else:
        # Deactivating: check that no other active flag depends on this one
        check_no_dependent_flags(flag_id, db)
        flag_db.is_active = False

    db.commit()
    db.refresh(flag_db)
    return flag_db


def flag_to_response(flag: Flag) -> FlagResponse:
    """
    Converts a Flag model to FlagResponse schema.
    """
    return FlagResponse(
        id=flag.id,
        name=flag.name,
        is_active=flag.is_active,
        dependencies=[dep.id for dep in flag.dependencies],
    ) 