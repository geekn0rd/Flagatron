from sqlalchemy import text

# 1. Creates a flag without dependencies.
def test_create_flag_without_dependencies(client):
    response = client.post("/flags/", json={"name": "flag1", "dependencies": []})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "flag1"
    assert data["dependencies"] == []

# 2. Fails to create a flag if any dependency does not exist.
def test_create_flag_with_nonexistent_dependency(client):
    response = client.post("/flags/", json={"name": "flag2", "dependencies": [999]})
    assert response.status_code == 400
    assert "One or more dependencies not found" in response.text

# 3. Fails to create a flag if it introduces a circular dependency.
def test_create_flag_with_circular_dependency(client):
    # Create flagA
    flag_a_response = client.post("/flags/", json={"name": "flagA", "dependencies": []})
    flag_a_id = flag_a_response.json()["id"]
    
    # Create flagB depending on flagA
    flag_b_response = client.post("/flags/", json={"name": "flagB", "dependencies": [flag_a_id]})
    flag_b_id = flag_b_response.json()["id"]
    
    # Try to create a flag that depends on both flagB and flagA
    response = client.post("/flags/", json={"name": "flagC", "dependencies": [flag_b_id, flag_a_id]})
    assert response.status_code == 400
    assert "circular" in response.text.lower()

# 4. Enables a flag when all dependencies are active.
def test_enable_flag_with_active_dependencies(client):
    # Create dependency flag
    dep_response = client.post("/flags/", json={"name": "dep1", "dependencies": []})
    dep_id = dep_response.json()["id"]
    
    # Toggle dependency to active
    client.patch(f"/flags/toggle/{dep_id}")
    
    # Create flag that depends on dep1
    flag_response = client.post("/flags/", json={"name": "flag3", "dependencies": [dep_id]})
    flag_id = flag_response.json()["id"]
    
    # Toggle flag to active
    client.patch(f"/flags/toggle/{flag_id}")
    
    response = client.get(f"/flags/{flag_id}")
    assert response.status_code == 200
    assert response.json()["is_active"] is True

# 5. Fails to enable a flag if any dependency is inactive.
def test_enable_flag_with_inactive_dependency(client):
    # Create dependency flag (inactive by default)
    dep_response = client.post("/flags/", json={"name": "dep2", "dependencies": []})
    dep_id = dep_response.json()["id"]
    
    # Create flag that depends on dep2
    flag_response = client.post("/flags/", json={"name": "flag4", "dependencies": [dep_id]})
    flag_id = flag_response.json()["id"]
    
    # Try to toggle flag to active (should fail due to inactive dependency)
    response = client.patch(f"/flags/toggle/{flag_id}")
    assert response.status_code == 400
    assert "All dependencies must be active" in response.text

# 6. Disables a flag successfully.
def test_disable_flag(client):
    flag_response = client.post("/flags/", json={"name": "flag5", "dependencies": []})
    flag_id = flag_response.json()["id"]
    
    # Enable the flag first
    client.patch(f"/flags/toggle/{flag_id}")
    
    # Disable the flag
    response = client.patch(f"/flags/toggle/{flag_id}")
    assert response.status_code == 200
    assert response.json()["is_active"] is False

# 7. Logs an entry on flag creation.
def test_audit_log_on_flag_creation(client, db_session):
    client.post("/flags/", json={"name": "flag6", "dependencies": []})
    # Query audit log
    logs = db_session.execute(text("SELECT * FROM audit_logs WHERE operation='create' AND flag_name='flag6'")).fetchall()
    assert len(logs) == 1

# 8. Logs an entry on flag toggle (enable/disable).
def test_audit_log_on_flag_toggle(client, db_session):
    flag_response = client.post("/flags/", json={"name": "flag7", "dependencies": []})
    flag_id = flag_response.json()["id"]
    
    # Enable the flag
    client.patch(f"/flags/toggle/{flag_id}")
    
    # Disable the flag
    client.patch(f"/flags/toggle/{flag_id}")
    
    logs = db_session.execute(text("SELECT * FROM audit_logs WHERE flag_name='flag7' AND operation IN ('activate', 'deactivate')")).fetchall()
    assert len(logs) == 2

# 9. Retrieves flag status correctly.
def test_retrieve_flag_status(client):
    flag_response = client.post("/flags/", json={"name": "flag8", "dependencies": []})
    flag_id = flag_response.json()["id"]
    
    # Enable the flag
    client.patch(f"/flags/toggle/{flag_id}")
    
    response = client.get(f"/flags/{flag_id}")
    assert response.status_code == 200
    assert response.json()["is_active"] is True

# 10. Retrieves audit history correctly.
def test_retrieve_audit_history(client):
    flag_response = client.post("/flags/", json={"name": "flag9", "dependencies": []})
    flag_id = flag_response.json()["id"]
    
    # Enable the flag
    client.patch(f"/flags/toggle/{flag_id}")
    
    response = client.get("/flags/audit-logs/", params={"flag_id": flag_id})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(entry["operation"] == "create" for entry in data)
    assert any(entry["operation"] == "activate" for entry in data) 