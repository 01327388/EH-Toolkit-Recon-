from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.audit import record_event
from app.database import get_db
from app.deps import get_or_create_csrf_token, require_admin, secrets_compare
from app.models import AuditEvent, Role, User

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


def _redirect_with_flash(url: str, message: str, kind: str = "error") -> RedirectResponse:
    return RedirectResponse(f"{url}?flash={quote(message)}&flash_type={kind}", status_code=303)


@router.get("")
def admin_home(request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.asc()).all()
    events = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(100).all()
    csrf = get_or_create_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "admin.html",
        {
            "user": admin,
            "users": users,
            "events": events,
            "csrf_token": csrf,
            "flash": request.query_params.get("flash"),
            "flash_type": request.query_params.get("flash_type", "error"),
        },
    )
    response.set_cookie("csrf_token", csrf, samesite="lax", secure=False, httponly=False)
    return response


@router.post("/users/{user_id}/role")
def change_role(
    user_id: str,
    request: Request,
    role: str = Form(...),
    csrf_token: str = Form(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if not secrets_compare(request.cookies.get("csrf_token", ""), csrf_token):
        return _redirect_with_flash("/admin", "Your form session expired. Please try again.")

    try:
        new_role = Role(role)
    except ValueError:
        return _redirect_with_flash("/admin", "Unknown role.")

    target = db.get(User, user_id)
    if target is None:
        return _redirect_with_flash("/admin", "User not found.")
    if target.id == admin.id and new_role != Role.ADMINISTRATOR:
        return _redirect_with_flash("/admin", "You cannot remove your own administrator access.")

    target.role = new_role
    db.commit()
    record_event(
        db,
        event_type="admin.role_changed",
        description=f"{target.email} role set to {new_role.value}.",
        user_id=admin.id,
        target_type="user",
        target_id=target.id,
    )
    return _redirect_with_flash("/admin", "Role updated.", kind="success")


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: str,
    request: Request,
    csrf_token: str = Form(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if not secrets_compare(request.cookies.get("csrf_token", ""), csrf_token):
        return _redirect_with_flash("/admin", "Your form session expired. Please try again.")

    target = db.get(User, user_id)
    if target is None:
        return _redirect_with_flash("/admin", "User not found.")
    if target.id == admin.id:
        return _redirect_with_flash("/admin", "You cannot deactivate your own account.")

    target.is_active = not target.is_active
    db.commit()
    record_event(
        db,
        event_type="admin.user_active_toggled",
        description=f"{target.email} active set to {target.is_active}.",
        user_id=admin.id,
        target_type="user",
        target_id=target.id,
    )
    return _redirect_with_flash("/admin", "User updated.", kind="success")
