# 1. Creates a flag without dependencies.
def test_create_flag_without_dependencies(client):
    response = client.post("/flags/", json={"name": "flag1", "dependencies": []})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "flag1"
    assert data["dependencies"] == []

# 2. Fails to create a flag if any dependency does not exist.
def test_create_flag_with_nonexistent_dependency(client):
    response = client.post("/flags/", json={"name": "flag2", "dependencies": ["nonexistent"]})
    assert response.status_code == 400
    assert "does not exist" in response.text

# 3. Fails to create a flag if it introduces a circular dependency.
def test_create_flag_with_circular_dependency(client):
    # Create flagA
    client.post("/flags/", json={"name": "flagA", "dependencies": []})
    # Create flagB depending on flagA
    client.post("/flags/", json={"name": "flagB", "dependencies": ["flagA"]})
    # Try to update flagA to depend on flagB (circular)
    response = client.post("/flags/", json={"name": "flagA", "dependencies": ["flagB"]})
    assert response.status_code == 400
    assert "circular" in response.text.lower()

# 4. Enables a flag when all dependencies are active.
def test_enable_flag_with_active_dependencies(client):
    client.post("/flags/", json={"name": "dep1", "dependencies": []})
    client.post("/flags/enable", json={"name": "dep1"})
    client.post("/flags/", json={"name": "flag3", "dependencies": ["dep1"]})
    client.post("/flags/enable", json={"name": "flag3"})
    response = client.get("/flags/flag3")
    assert response.status_code == 200
    assert response.json()["active"] is True

# 5. Fails to enable a flag if any dependency is inactive.
def test_enable_flag_with_inactive_dependency(client):
    client.post("/flags/", json={"name": "dep2", "dependencies": []})
    client.post("/flags/", json={"name": "flag4", "dependencies": ["dep2"]})
    response = client.post("/flags/enable", json={"name": "flag4"})
    assert response.status_code == 400
    assert "dependency" in response.text.lower()

# 6. Disables a flag successfully.
def test_disable_flag(client):
    client.post("/flags/", json={"name": "flag5", "dependencies": []})
    client.post("/flags/enable", json={"name": "flag5"})
    response = client.post("/flags/disable", json={"name": "flag5"})
    assert response.status_code == 200
    assert response.json()["active"] is False

# 7. Logs an entry on flag creation.
def test_audit_log_on_flag_creation(client, db_session):
    client.post("/flags/", json={"name": "flag6", "dependencies": []})
    # Query audit log
    logs = db_session.execute("SELECT * FROM audit_log WHERE action='create' AND flag_name='flag6'").fetchall()
    assert len(logs) == 1

# 8. Logs an entry on flag toggle (enable/disable).
def test_audit_log_on_flag_toggle(client, db_session):
    client.post("/flags/", json={"name": "flag7", "dependencies": []})
    client.post("/flags/enable", json={"name": "flag7"})
    client.post("/flags/disable", json={"name": "flag7"})
    logs = db_session.execute("SELECT * FROM audit_log WHERE flag_name='flag7' AND action IN ('enable', 'disable')").fetchall()
    assert len(logs) == 2

# 9. Retrieves flag status correctly.
def test_retrieve_flag_status(client):
    client.post("/flags/", json={"name": "flag8", "dependencies": []})
    client.post("/flags/enable", json={"name": "flag8"})
    response = client.get("/flags/flag8")
    assert response.status_code == 200
    assert response.json()["active"] is True

# 10. Retrieves audit history correctly.
def test_retrieve_audit_history(client):
    client.post("/flags/", json={"name": "flag9", "dependencies": []})
    client.post("/flags/enable", json={"name": "flag9"})
    response = client.get("/flags/flag9/audit")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(entry["action"] == "create" for entry in data)
    assert any(entry["action"] == "enable" for entry in data) 