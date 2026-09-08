from datetime import datetime, timedelta, timezone

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import ReconRun, Role, User
from app.security import read_session_token

settings = get_settings()


class NotAuthenticated(Exception):
    pass


class Forbidden(Exception):
    def __init__(self, message: str = "You don't have permission to do that."):
        self.message = message


class RateLimited(Exception):
    def __init__(self, message: str):
        self.message = message


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    user_id = read_session_token(token, max_age=settings.session_max_age_seconds)
    if not user_id:
        return None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


def require_user(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise NotAuthenticated()
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != Role.ADMINISTRATOR:
        raise Forbidden("Administrator access is required for this page.")
    return user


def get_or_create_csrf_token(request: Request) -> str:
    from app.security import new_csrf_token

    return request.cookies.get("csrf_token") or new_csrf_token()


def verify_csrf(request: Request, form_token: str | None) -> bool:
    cookie_token = request.cookies.get("csrf_token")
    return bool(cookie_token) and bool(form_token) and secrets_compare(cookie_token, form_token)


def secrets_compare(a: str, b: str) -> bool:
    import hmac

    return hmac.compare_digest(a, b)


def check_run_rate_limit(db: Session, user: User) -> None:
    window_start = datetime.now(timezone.utc) - timedelta(hours=1)
    recent = (
        db.query(ReconRun)
        .filter(ReconRun.user_id == user.id, ReconRun.created_at >= window_start)
        .count()
    )
    if recent >= settings.runs_per_user_per_hour:
        raise RateLimited(
            f"You've reached the limit of {settings.runs_per_user_per_hour} recon runs per hour. "
            "Please try again later."
        )
