import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.internal.models import Flag, AuditLog
from app.internal.schemas import FlagBody, FlagResponse, NestedFlagResponse


def log_audit_event(
    db: Session,
    flag_id: int,
    flag_name: str,
    operation: str,
    previous_state: dict = None,
    new_state: dict = None,
    reason: str = None,
    actor: str = None
) -> AuditLog:
    """
    Creates an audit log entry for a flag operation.
    """
    audit_log = AuditLog(
        flag_id=flag_id,
        flag_name=flag_name,
        operation=operation,
        previous_state=json.dumps(previous_state) if previous_state else None,
        new_state=json.dumps(new_state) if new_state else None,
        reason=reason,
        actor=actor
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def has_circular_dependency(flag_id: int, dependencies: list[int], db: Session) -> bool:
    """
    Returns True if adding any of the dependencies would create a circular dependency for flag_id.
    """
    # Check for direct self-reference
    if flag_id in dependencies:
        return True
    
    # Check for circular dependencies through the dependency chain
    visited = set()
    stack = list(dependencies)
    while stack:
        current_id = stack.pop()
        if current_id in visited:
            continue
        visited.add(current_id)
        current_flag = db.query(Flag).filter(Flag.id == current_id).first()
        if current_flag:
            # Check if any of the current flag's dependencies would create a cycle
            for dep in current_flag.dependencies:
                if dep.id == flag_id:
                    return True
                stack.append(dep.id)
    
    # Check for redundant dependencies (e.g., if flagC depends on both flagB and flagA,
    # but flagB already depends on flagA, this creates redundant paths)
    direct_deps = set(dependencies)
    indirect_deps = set()
    
    for dep_id in dependencies:
        dep_flag = db.query(Flag).filter(Flag.id == dep_id).first()
        if dep_flag:
            # Get all transitive dependencies
            stack = [dep_flag]
            visited_transitive = set()
            while stack:
                current = stack.pop()
                if current.id in visited_transitive:
                    continue
                visited_transitive.add(current.id)
                for transitive_dep in current.dependencies:
                    indirect_deps.add(transitive_dep.id)
                    stack.append(transitive_dep)
    
    # If any direct dependency is also reachable through other dependencies, it's redundant
    redundant_deps = direct_deps.intersection(indirect_deps)
    if redundant_deps:
        return True
    
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


def create_flag_service(flag_in: FlagBody, db: Session, actor: str = None) -> Flag:
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
    
    # Log the creation
    log_audit_event(
        db=db,
        flag_id=new_flag.id,
        flag_name=new_flag.name,
        operation="create",
        new_state={
            "name": new_flag.name,
            "is_active": new_flag.is_active,
            "dependencies": [dep.id for dep in new_flag.dependencies]
        },
        reason="Flag created",
        actor=actor
    )
    
    return new_flag


def toggle_flag_service(flag_id: int, db: Session, actor: str = None) -> Flag:
    """
    Toggles a flag's active state with dependency validation.
    """
    flag_db = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag_db:
        raise HTTPException(status_code=404, detail="Flag not found.")
    
    # Capture previous state for audit log
    previous_state = {
        "name": flag_db.name,
        "is_active": flag_db.is_active,
        "dependencies": [dep.id for dep in flag_db.dependencies]
    }
    
    if flag_db.is_active == False:
        # Activating: check that all dependencies are active
        check_dependencies_active(flag_db)
        flag_db.is_active = True
        operation = "activate"
        reason = "Flag manually activated"
    else:
        # Deactivating: check that no other active flag depends on this one
        check_no_dependent_flags(flag_id, db)
        flag_db.is_active = False
        operation = "deactivate"
        reason = "Flag manually deactivated"

    db.commit()
    db.refresh(flag_db)
    
    # Log the toggle operation
    new_state = {
        "name": flag_db.name,
        "is_active": flag_db.is_active,
        "dependencies": [dep.id for dep in flag_db.dependencies]
    }
    
    log_audit_event(
        db=db,
        flag_id=flag_db.id,
        flag_name=flag_db.name,
        operation=operation,
        previous_state=previous_state,
        new_state=new_state,
        reason=reason,
        actor=actor
    )
    
    return flag_db


def auto_disable_flag_service(flag_id: int, db: Session, reason: str = None) -> Flag:
    """
    Automatically disables a flag (e.g., when dependencies become inactive).
    """
    flag_db = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag_db:
        raise HTTPException(status_code=404, detail="Flag not found.")
    
    if not flag_db.is_active:
        return flag_db  # Already inactive
    
    # Capture previous state for audit log
    previous_state = {
        "name": flag_db.name,
        "is_active": flag_db.is_active,
        "dependencies": [dep.id for dep in flag_db.dependencies]
    }
    
    flag_db.is_active = False
    db.commit()
    db.refresh(flag_db)
    
    # Log the auto-disable operation
    new_state = {
        "name": flag_db.name,
        "is_active": flag_db.is_active,
        "dependencies": [dep.id for dep in flag_db.dependencies]
    }
    
    log_audit_event(
        db=db,
        flag_id=flag_db.id,
        flag_name=flag_db.name,
        operation="auto-disable",
        previous_state=previous_state,
        new_state=new_state,
        reason=reason or "Flag automatically disabled due to dependency changes",
        actor="system"
    )
    
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


def flag_to_nested_response(flag: Flag) -> NestedFlagResponse:
    """
    Converts a Flag model to NestedFlagResponse schema with full dependency details.
    """
    return NestedFlagResponse(
        id=flag.id,
        name=flag.name,
        is_active=flag.is_active,
        dependencies=[flag_to_nested_response(dep) for dep in flag.dependencies],
    )


def get_flag_by_id_service(flag_id: int, db: Session) -> Flag:
    """
    Gets a flag by ID with all dependencies loaded.
    Raises HTTPException if flag is not found.
    """
    flag = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found.")
    return flag


def get_audit_logs_service(
    db: Session,
    flag_id: int = None,
    operation: str = None,
    actor: str = None,
    limit: int = 100,
    offset: int = 0
) -> list[AuditLog]:
    """
    Retrieves audit logs with optional filtering.
    """
    query = db.query(AuditLog)
    
    if flag_id:
        query = query.filter(AuditLog.flag_id == flag_id)
    
    if operation:
        query = query.filter(AuditLog.operation == operation)
    
    if actor:
        query = query.filter(AuditLog.actor == actor)
    
    return query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all() 