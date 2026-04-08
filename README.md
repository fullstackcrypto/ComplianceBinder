# ComplianceBinder

A minimal **digital compliance binder** you can run locally or deploy.

It’s built to stay **simple**:
- Login
- Create a binder
- Track tasks (checklists)
- Upload documents
- One-click *inspection-ready report*

## Quick start (local)

### 1) Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# IMPORTANT: edit .env and change SECRET_KEY
uvicorn app.main:app --reload
```

Open: http://localhost:8000

### 2) First use
1. Click **Register**
2. Login
3. Create a binder
4. Add tasks + upload docs
5. Open the Inspection Report

## Notes on security (MVP)
- Passwords are hashed (bcrypt)
- Auth is via JWT (Bearer token)
- Files are stored on disk in `UPLOAD_DIR`

For production:
- Set a strong `SECRET_KEY`
- Set `ALLOWED_ORIGINS` to your domain
- Put the app behind HTTPS (Caddy / Nginx)
- Store uploads in S3-compatible storage (optional)

## Repo layout
```
ComplianceBinder/
  backend/
    app/
      main.py
      models.py
      db.py
      security.py
      schemas.py
      static/     # simple frontend served by FastAPI
    requirements.txt
    .env.example
  docs/
  scripts/
```

## Roadmap (next)
- Binder templates (assisted living, contractor, etc.)
- Scheduled reminders (email)
- PDF export button
- Multi-user sharing (read-only inspectors)

## Monitoring & Self-Monitoring

ComplianceBinder includes built-in monitoring endpoints for observability:

### Health Check
```
GET /health
```
Returns service health status including database and storage connectivity.

### Metrics
```
GET /metrics
```
Returns system statistics:
- Total users, binders, tasks, and documents
- Task status breakdown (open, done, overdue)
- Storage usage in bytes

### System Status
```
GET /status
```
Returns comprehensive system information:
- Application version and Python version
- Uptime in seconds
- Database and storage status
- Storage path and usage

### Structured Logging
All operations are logged with:
- **Request ID tracking** - Each request gets a unique ID for traceability
- **Auth event logging** - Login/register events are logged for security auditing
- **CRUD audit logging** - All create/update operations are logged with user context

### Overdue Task Tracking
Tasks with past due dates are automatically flagged as overdue:
- The `/metrics` endpoint includes `tasks_overdue` count
- The frontend displays overdue tasks with visual indicators
- Overdue count shows in the binder stats dashboard

