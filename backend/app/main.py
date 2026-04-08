from __future__ import annotations

import os
import secrets
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from .config import settings
from .db import init_db, get_session
from .models import User, Binder, Task, Document
from .schemas import Token, UserCreate, BinderCreate, BinderOut, TaskCreate, TaskOut, DocumentOut
from .security import hash_password, verify_password, create_access_token, decode_token
from .monitoring import router as monitoring_router
from .logging_config import (
    configure_logging,
    RequestIdMiddleware,
    RequestLoggingMiddleware,
    log_auth_event,
    log_crud_event,
)


# Configure structured logging
logger = configure_logging()

app = FastAPI(title="ComplianceBinder", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origins] if settings.allowed_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware for traceability
app.add_middleware(RequestIdMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include monitoring endpoints
app.include_router(monitoring_router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@app.on_event("startup")
def _startup() -> None:
    init_db()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    logger.info("ComplianceBinder started successfully")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        if not email:
            raise ValueError("missing sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ------------------ Auth ------------------


@app.post("/auth/register", status_code=201)
def register(user_in: UserCreate, session: Session = Depends(get_session)) -> dict:
    existing = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing:
        log_auth_event("register", user_in.email, success=False, details="Email already registered")
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=user_in.email, password_hash=hash_password(user_in.password))
    session.add(user)
    session.commit()
    log_auth_event("register", user_in.email, success=True)
    return {"ok": True}


@app.post("/auth/token", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> Token:
    user = session.exec(select(User).where(User.email == form.username)).first()
    if not user or not verify_password(form.password, user.password_hash):
        log_auth_event("login", form.username, success=False, details="Bad credentials")
        raise HTTPException(status_code=401, detail="Bad credentials")
    token = create_access_token(subject=user.email)
    log_auth_event("login", user.email, success=True)
    return Token(access_token=token)


# ------------------ Binders ------------------


@app.get("/binders", response_model=list[BinderOut])
def list_binders(
    me: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[BinderOut]:
    binders = session.exec(select(Binder).where(Binder.owner_id == me.id).order_by(Binder.created_at.desc())).all()
    return [BinderOut(id=b.id, name=b.name, industry=b.industry, created_at=b.created_at) for b in binders]


@app.post("/binders", response_model=BinderOut, status_code=201)
def create_binder(
    binder_in: BinderCreate,
    me: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> BinderOut:
    binder = Binder(name=binder_in.name, industry=binder_in.industry, owner_id=me.id)
    session.add(binder)
    session.commit()
    session.refresh(binder)
    log_crud_event("create", "binder", binder.id, me.email, f"name={binder.name}")
    return BinderOut(id=binder.id, name=binder.name, industry=binder.industry, created_at=binder.created_at)


def _get_binder_or_404(binder_id: int, me: User, session: Session) -> Binder:
    binder = session.get(Binder, binder_id)
    if not binder or binder.owner_id != me.id:
        raise HTTPException(status_code=404, detail="Binder not found")
    return binder


# ------------------ Tasks ------------------


@app.get("/binders/{binder_id}/tasks", response_model=list[TaskOut])
def list_tasks(
    binder_id: int,
    me: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[TaskOut]:
    _ = _get_binder_or_404(binder_id, me, session)
    tasks = session.exec(select(Task).where(Task.binder_id == binder_id).order_by(Task.created_at.desc())).all()
    today = date.today()
    return [
        TaskOut(
            id=t.id,
            title=t.title,
            description=t.description,
            status=t.status,
            due_date=t.due_date,
            created_at=t.created_at,
            is_overdue=t.status != "done" and t.due_date is not None and t.due_date < today,
        )
        for t in tasks
    ]


@app.post("/binders/{binder_id}/tasks", response_model=TaskOut, status_code=201)
def create_task(
    binder_id: int,
    task_in: TaskCreate,
    me: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> TaskOut:
    _ = _get_binder_or_404(binder_id, me, session)
    task = Task(
        title=task_in.title,
        description=task_in.description,
        due_date=task_in.due_date,
        binder_id=binder_id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    log_crud_event("create", "task", task.id, me.email, f"title={task.title}")
    return TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        created_at=task.created_at,
    )


@app.post("/tasks/{task_id}/done")
def mark_done(
    task_id: int,
    me: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    binder = session.get(Binder, task.binder_id)
    if not binder or binder.owner_id != me.id:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "done"
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    log_crud_event("update", "task", task.id, me.email, "status=done")
    return {"ok": True}


# ------------------ Documents ------------------


@app.get("/binders/{binder_id}/documents", response_model=list[DocumentOut])
def list_documents(
    binder_id: int,
    me: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[DocumentOut]:
    _ = _get_binder_or_404(binder_id, me, session)
    docs = session.exec(select(Document).where(Document.binder_id == binder_id).order_by(Document.uploaded_at.desc())).all()
    return [
        DocumentOut(id=d.id, original_name=d.original_name, content_type=d.content_type, note=d.note, uploaded_at=d.uploaded_at)
        for d in docs
    ]


@app.post("/binders/{binder_id}/documents", status_code=201)
def upload_document(
    binder_id: int,
    file: UploadFile = File(...),
    note: str = Form(""),
    me: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    _ = _get_binder_or_404(binder_id, me, session)

    safe_name = f"{secrets.token_hex(16)}_{os.path.basename(file.filename)}"
    dest = Path(settings.upload_dir) / safe_name
    with dest.open("wb") as f:
        f.write(file.file.read())

    doc = Document(
        filename=safe_name,
        original_name=file.filename,
        content_type=file.content_type or "application/octet-stream",
        note=note,
        binder_id=binder_id,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    log_crud_event("create", "document", doc.id, me.email, f"name={file.filename}")
    return {"ok": True}


@app.get("/documents/{doc_id}/download")
def download_document(
    doc_id: int,
    me: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Doc not found")
    binder = session.get(Binder, doc.binder_id)
    if not binder or binder.owner_id != me.id:
        raise HTTPException(status_code=404, detail="Doc not found")
    from fastapi.responses import FileResponse

    path = Path(settings.upload_dir) / doc.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing on server")
    return FileResponse(path, media_type=doc.content_type, filename=doc.original_name)


# ------------------ Report (inspection-ready) ------------------


@app.get("/binders/{binder_id}/report")
def binder_report(
    binder_id: int,
    me: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    binder = _get_binder_or_404(binder_id, me, session)
    tasks = session.exec(select(Task).where(Task.binder_id == binder_id)).all()
    docs = session.exec(select(Document).where(Document.binder_id == binder_id)).all()

    open_tasks = [t for t in tasks if t.status != "done"]
    done_tasks = [t for t in tasks if t.status == "done"]

    html = [
        "<html><head><meta charset='utf-8'><title>Inspection Report</title>",
        "<style>body{font-family:Arial;margin:24px}h1{margin-bottom:0}.meta{color:#555}table{width:100%;border-collapse:collapse;margin-top:12px}td,th{border:1px solid #ddd;padding:8px}th{background:#f5f5f5}</style>",
        "</head><body>",
        f"<h1>{binder.name}</h1>",
        f"<div class='meta'>Industry: {binder.industry} • Generated: {date.today().isoformat()}</div>",
        "<h2>Open Tasks</h2>",
        "<table><tr><th>Task</th><th>Due</th><th>Description</th></tr>",
    ]
    for t in sorted(open_tasks, key=lambda x: (x.due_date or date.max)):
        html.append(f"<tr><td>{t.title}</td><td>{t.due_date or ''}</td><td>{t.description}</td></tr>")
    html.append("</table>")

    html.append("<h2>Completed Tasks</h2>")
    html.append("<table><tr><th>Task</th><th>Due</th><th>Description</th></tr>")
    for t in sorted(done_tasks, key=lambda x: (x.due_date or date.max)):
        html.append(f"<tr><td>{t.title}</td><td>{t.due_date or ''}</td><td>{t.description}</td></tr>")
    html.append("</table>")

    html.append("<h2>Documents</h2>")
    html.append("<table><tr><th>Name</th><th>Note</th><th>Uploaded</th></tr>")
    for d in sorted(docs, key=lambda x: x.uploaded_at, reverse=True):
        html.append(f"<tr><td>{d.original_name}</td><td>{d.note}</td><td>{d.uploaded_at:%Y-%m-%d}</td></tr>")
    html.append("</table>")
    html.append("</body></html>")

    from fastapi.responses import HTMLResponse

    return HTMLResponse("\n".join(html))


# ------------------ Static UI ------------------


static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
