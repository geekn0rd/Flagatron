# Flagatron
### 🚩 Flagatron – A fun and powerful feature flag management service built with FastAPI 🐍 and PostgreSQL 🐘.

Easily manage feature flags with dependency validation, circular dependency detection, and detailed audit logging – all behind a clean REST API.<br/><br/>
✨ Features:

- 🔗 Flag dependency validation
- ♻️ Circular dependency detection
- 📝 Comprehensive audit logging with timestamps, reasons, and actor information
- 🧰 REST API for flag control & status
- 🐳 Fully Dockerized with docker-compose
- 🧪 One-command test suite inside Docker

## 🚀 Getting Started

### Prerequisites
- Docker installed on your system

### Setup Instructions

1. **Create a `.env` file** in the root directory with the following environment variables:
   ```env
   POSTGRES_DB=flagatron
   POSTGRES_TEST_DB=test_db
   POSTGRES_USER=flagatron_user
   POSTGRES_PASSWORD=your_secure_password_here
   ```

2. **Run the application with Docker**:
   ```bash
   docker compose up -d --build --remove-orphans
   ```

3. **Access the application**:
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs

4. **Stop the application**:
   ```bash
   docker compose down
   ```

The application will automatically set up the PostgreSQL database and run database migrations on startup.

## 📝 Audit Logging

The service includes comprehensive audit logging that tracks all flag operations:

### Audit Log Fields
- **flag_id**: The ID of the flag being operated on
- **flag_name**: The name of the flag for easy identification
- **operation**: The type of operation (create, activate, deactivate, auto-disable)
- **previous_state**: JSON representation of the flag's state before the operation
- **new_state**: JSON representation of the flag's state after the operation
- **reason**: Human-readable reason for the operation
- **actor**: Who performed the action (user ID, system, etc.)
- **timestamp**: When the operation occurred

## 🚩 API Endpoints

### Flag Management

#### Get All Flags
```bash
GET /flags/
```
Returns a list of all flags with their basic information.

#### Get Flag by ID
```bash
GET /flags/{flag_id}
```
Returns detailed information about a specific flag, including nested dependency information.

#### Create Flag
```bash
POST /flags/
```
Creates a new feature flag.

**Request Body:**
```json
{
  "name": "new-feature",
  "dependencies": [1, 2]
}
```

**Query Parameters:**
- `actor` (optional): Who is performing the operation (for audit logging)

#### Toggle Flag
```bash
PATCH /flags/toggle/{flag_id}
```
Toggles the active state of a flag (activates if inactive, deactivates if active).

**Query Parameters:**
- `actor` (optional): Who is performing the operation (for audit logging)

### Audit Logging

#### Get All Audit Logs
```bash
GET /flags/audit-logs/
```

**Query Parameters:**
- `flag_id` (optional): Filter by specific flag ID
- `operation` (optional): Filter by operation type
- `actor` (optional): Filter by actor
- `limit` (default: 100, max: 1000): Maximum number of logs to return
- `offset` (default: 0): Number of logs to skip

### Adding Actor Information

When creating or toggling flags, you can include actor information for audit logging:

```bash
# Create flag with actor
POST /flags/?actor=user123
{
  "name": "new-feature",
  "dependencies": [1, 2]
}

# Toggle flag with actor
PATCH /flags/toggle/1?actor=admin
```

### Automatic Logging

The system automatically logs:
- Flag creation
- Manual flag activation/deactivation
- Automatic flag disabling (when dependencies become inactive)

## Running Tests

To run all unit tests inside the Docker environment:

```sh
docker compose run --rm test
```
