# Flagatron
### 🚩 Flagatron – A fun and powerful feature flag management service built with FastAPI 🐍 and PostgreSQL 🐘.

Easily manage feature flags with dependency validation, circular dependency detection, and detailed audit logging – all behind a clean REST API.<br/><br/>
✨ Features:

- 🔗 Flag dependency validation
- ♻️ Circular dependency detection
- 📝 Audit log with actor, reason & timestamps
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
