from __future__ import annotations

import html
import os
import re
import secrets
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select

from .config import settings
from .db import get_session, init_db
from .logging_config import (
    RequestIdMiddleware,
    RequestLoggingMiddleware,
    configure_logging,
    log_auth_event,
    log_crud_event,
)
from .models import Binder, Document, Task, User
from .monitoring import router as monitoring_router
from .schemas import BinderCreate, BinderOut, DocumentOut, TaskCreate, TaskOut, Token, UserCreate
from .security import create_access_token, decode_token, hash_password, verify_password
from .templates import default_tasks_for_industry


logger = configure_logging()

app = FastAPI(title="ComplianceBinder", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(monitoring_router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class CheckoutRequest(BaseModel):
    plan: str


class CheckoutResponse(BaseModel):
    url: str


class BillingStatusResponse(BaseModel):
    plan: str
    status: str
    stripe_customer_id: str = ""
    stripe_subscription_id: str = ""


def _escape(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _safe_original_filename(filename: str | None) -> str:
    base = os.path.basename(filename or "document")
    base = re.sub(r"[^A-Za-z0-9._ -]", "_", base).strip(" .")
    return base or "document"


def _validate_upload_metadata(file: UploadFile) -> str:
    content_type = (file.content_type or "application/octet-stream").lower()
    if content_type not in settings.parsed_allowed_content_types():
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}",
        )
    return content_type


def _save_upload_with_limit(file: UploadFile, destination: Path) -> int:
    total = 0
    with destination.open("wb") as out_file:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > settings.max_upload_size_bytes:
                out_file.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Upload exceeds the configured file-size limit",
                )
            out_file.write(chunk)

    if total == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty uploads are not allowed")
    return total


def _has_paid_access(user: User) -> bool:
    return user.billing_status in {"active", "trialing"}


def _apply_billing_update(
    session: Session,
    user: User,
    plan: str,
    billing_status: str,
    stripe_customer_id: str = "",
    stripe_subscription_id: str = "",
) -> None:
    user.billing_plan = plan or user.billing_plan or "free"
    user.billing_status = billing_status or user.billing_status or "inactive"
    if stripe_customer_id:
        user.stripe_customer_id = stripe_customer_id
    if stripe_subscription_id:
        user.stripe_subscription_id = stripe_subscription_id
    user.billing_updated_at = datetime.utcnow()
    session.add(user)
    session.commit()


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


@app.get("/billing/plans")
def billing_plans() -> dict:
    return {
        "starter": {"label": "Starter", "price": "$19 / month", "mode": "subscription"},
        "pro": {"label": "Pro", "price": "$49 / month", "mode": "subscription"},
        "setup": {"label": "Done-With-You Setup", "price": "$299 one-time", "mode": "payment"},
    }


@app.get("/billing/status", response_model=BillingStatusResponse)
def billing_status(me: User = Depends(get_current_user)) -> BillingStatusResponse:
    return BillingStatusResponse(
        plan=me.billing_plan,
        status=me.billing_status,
        stripe_customer_id=me.stripe_customer_id,
        stripe_subscription_id=me.stripe_subscription_id,
    )


@app.post("/billing/checkout", response_model=CheckoutResponse)
def create_checkout_session(
    payload: CheckoutRequest,
    me: User = Depends(get_current_user),
) -> CheckoutResponse:
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    price_map = {
        "starter": (settings.stripe_price_starter, "subscription"),
        "pro": (settings.stripe_price_pro, "subscription"),
        "setup": (settings.stripe_price_setup, "payment"),
    }
    plan = payload.plan.strip().lower()
    price_id, mode = price_map.get(plan, ("", ""))
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid or unconfigured billing plan")

    import stripe

    stripe.api_key = settings.stripe_secret_key
    checkout = stripe.checkout.Session.create(
        mode=mode,
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=me.email,
        success_url=f"{settings.public_app_url.rstrip('/')}/?payment=success",
        cancel_url=f"{settings.public_app_url.rstrip('/')}/?payment=cancelled",
        metadata={"user_id": str(me.id), "email": me.email, "plan": plan},
    )
    return CheckoutResponse(url=checkout.url)


@app.post("/billing/webhook")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)) -> dict:
    if not settings.stripe_secret_key or not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook is not configured")

    import stripe

    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook payload") from exc

    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        metadata = obj.get("metadata", {}) or {}
        user_id = metadata.get("user_id")
        plan = metadata.get("plan", "starter")
        if user_id:
            user = session.get(User, int(user_id))
            if user:
                checkout_status = "active" if obj.get("payment_status") == "paid" else "trialing"
                _apply_billing_update(
                    session,
                    user,
                    plan=plan,
                    billing_status=checkout_status,
                    stripe_customer_id=obj.get("customer") or "",
                    stripe_subscription_id=obj.get("subscription") or "",
                )

    elif event_type in {"customer.subscription.updated", "customer.subscription.deleted"}:
        customer_id = obj.get("customer") or ""
        user = session.exec(select(User).where(User.stripe_customer_id == customer_id)).first() if customer_id else None
        if user:
            subscription_status = obj.get("status") or "inactive"
            plan = user.billing_plan if event_type == "customer.subscription.updated" else "free"
            _apply_billing_update(
                session,
                user,
                plan=plan,
                billing_status=subscription_status if event_type == "customer.subscription.updated" else "canceled",
                stripe_customer_id=customer_id,
                stripe_subscription_id=obj.get("id") or user.stripe_subscription_id,
            )

    return {"received": True}


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

    template_tasks = default_tasks_for_industry(binder.industry, binder.id)
    if template_tasks:
        session.add_all(template_tasks)
        session.commit()

    log_crud_event("create", "binder", binder.id, me.email, f"name={binder.name};template_tasks={len(template_tasks)}")
    return BinderOut(id=binder.id, name=binder.name, industry=binder.industry, created_at=binder.created_at)


def _get_binder_or_404(binder_id: int, me: User, session: Session) -> Binder:
    binder = session.get(Binder, binder_id)
    if not binder or binder.owner_id != me.id:
        raise HTTPException(status_code=404, detail="Binder not found")
    return binder


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
    content_type = _validate_upload_metadata(file)
    original_name = _safe_original_filename(file.filename)
    safe_name = f"{secrets.token_hex(16)}_{original_name}"
    dest = Path(settings.upload_dir) / safe_name
    bytes_written = _save_upload_with_limit(file, dest)

    doc = Document(
        filename=safe_name,
        original_name=original_name,
        content_type=content_type,
        note=note[:500],
        binder_id=binder_id,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    log_crud_event("create", "document", doc.id, me.email, f"name={original_name};bytes={bytes_written}")
    return {"ok": True, "id": doc.id, "bytes": bytes_written}


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

    path = Path(settings.upload_dir) / doc.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing on server")
    return FileResponse(path, media_type=doc.content_type, filename=doc.original_name)


def _render_binder_report_html(binder: Binder, tasks: list[Task], docs: list[Document]) -> str:
    open_tasks = [t for t in tasks if t.status != "done"]
    done_tasks = [t for t in tasks if t.status == "done"]

    report_html = [
        "<html><head><meta charset='utf-8'><title>Inspection Report</title>",
        "<style>body{font-family:Arial;margin:24px}h1{margin-bottom:0}.meta{color:#555}table{width:100%;border-collapse:collapse;margin-top:12px}td,th{border:1px solid #ddd;padding:8px}th{background:#f5f5f5}</style>",
        "</head><body>",
        f"<h1>{_escape(binder.name)}</h1>",
        f"<div class='meta'>Industry: {_escape(binder.industry)} &bull; Generated: {date.today().isoformat()}</div>",
        "<h2>Open Tasks</h2>",
        "<table><tr><th>Task</th><th>Due</th><th>Description</th></tr>",
    ]
    for task in sorted(open_tasks, key=lambda x: (x.due_date or date.max)):
        report_html.append(
            f"<tr><td>{_escape(task.title)}</td><td>{_escape(task.due_date or '')}</td><td>{_escape(task.description)}</td></tr>"
        )
    report_html.append("</table>")

    report_html.append("<h2>Completed Tasks</h2>")
    report_html.append("<table><tr><th>Task</th><th>Due</th><th>Description</th></tr>")
    for task in sorted(done_tasks, key=lambda x: (x.due_date or date.max)):
        report_html.append(
            f"<tr><td>{_escape(task.title)}</td><td>{_escape(task.due_date or '')}</td><td>{_escape(task.description)}</td></tr>"
        )
    report_html.append("</table>")

    report_html.append("<h2>Documents</h2>")
    report_html.append("<table><tr><th>Name</th><th>Note</th><th>Uploaded</th></tr>")
    for doc in sorted(docs, key=lambda x: x.uploaded_at, reverse=True):
        report_html.append(
            f"<tr><td>{_escape(doc.original_name)}</td><td>{_escape(doc.note)}</td><td>{doc.uploaded_at:%Y-%m-%d}</td></tr>"
        )
    report_html.append("</table>")
    report_html.append("</body></html>")
    return "\n".join(report_html)


def _build_report_pdf(binder: Binder, tasks: list[Task], docs: list[Document]) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    left = 0.75 * inch
    y = height - 0.75 * inch

    def line(text: str, size: int = 10, gap: int = 14) -> None:
        nonlocal y
        if y < 0.75 * inch:
            pdf.showPage()
            y = height - 0.75 * inch
        pdf.setFont("Helvetica", size)
        pdf.drawString(left, y, text[:110])
        y -= gap

    line(str(binder.name), 16, 22)
    line(f"Industry: {binder.industry} | Generated: {date.today().isoformat()}", 10, 20)

    line("Open Tasks", 13, 18)
    for task in sorted([t for t in tasks if t.status != "done"], key=lambda x: (x.due_date or date.max)):
        due = task.due_date.isoformat() if task.due_date else "No due date"
        line(f"- {task.title} ({due})", 10, 13)
        if task.description:
            line(f"  {task.description}", 9, 12)

    y -= 8
    line("Completed Tasks", 13, 18)
    for task in sorted([t for t in tasks if t.status == "done"], key=lambda x: (x.due_date or date.max)):
        due = task.due_date.isoformat() if task.due_date else "No due date"
        line(f"- {task.title} ({due})", 10, 13)

    y -= 8
    line("Documents", 13, 18)
    for doc in sorted(docs, key=lambda x: x.uploaded_at, reverse=True):
        line(f"- {doc.original_name} | Uploaded {doc.uploaded_at:%Y-%m-%d}", 10, 13)
        if doc.note:
            line(f"  Note: {doc.note}", 9, 12)

    pdf.save()
    buffer.seek(0)
    return buffer.read()


@app.get("/binders/{binder_id}/report")
def binder_report(
    binder_id: int,
    me: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    binder = _get_binder_or_404(binder_id, me, session)
    tasks = session.exec(select(Task).where(Task.binder_id == binder_id)).all()
    docs = session.exec(select(Document).where(Document.binder_id == binder_id)).all()
    return HTMLResponse(_render_binder_report_html(binder, tasks, docs))


@app.get("/binders/{binder_id}/report.pdf")
def binder_report_pdf(
    binder_id: int,
    me: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not _has_paid_access(me):
        raise HTTPException(status_code=402, detail="PDF export requires an active paid plan")

    binder = _get_binder_or_404(binder_id, me, session)
    tasks = session.exec(select(Task).where(Task.binder_id == binder_id)).all()
    docs = session.exec(select(Document).where(Document.binder_id == binder_id)).all()
    pdf_bytes = _build_report_pdf(binder, tasks, docs)
    filename = f"inspection-report-{binder_id}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
