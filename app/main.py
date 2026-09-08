import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.background import start_workers, stop_workers
from app.database import init_db
from app.deps import Forbidden, NotAuthenticated, RateLimited
from app.routers import admin, auth, runs, search

logger = logging.getLogger("ethicalhawk.main")

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_workers()
    yield
    await stop_workers()


app = FastAPI(title="EthicalHawk Recon", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(search.router)
app.include_router(runs.router)
app.include_router(admin.router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; script-src 'self' https://unpkg.com; img-src 'self' data:;"
    )
    return response


@app.exception_handler(NotAuthenticated)
async def handle_not_authenticated(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/auth/login", status_code=303)


@app.exception_handler(Forbidden)
async def handle_forbidden(request: Request, exc: Forbidden):
    return templates.TemplateResponse(
        request, "errors/generic.html", {"status_code": 403, "message": exc.message}, status_code=403
    )


@app.exception_handler(RateLimited)
async def handle_rate_limited(request: Request, exc: RateLimited):
    return templates.TemplateResponse(
        request, "errors/generic.html", {"status_code": 429, "message": exc.message}, status_code=429
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(request: Request, exc: StarletteHTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "Something went wrong."
    context = {"status_code": exc.status_code, "message": message}
    return templates.TemplateResponse(request, "errors/generic.html", context, status_code=exc.status_code)


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return templates.TemplateResponse(
        request,
        "errors/generic.html",
        {"status_code": 500, "message": "An unexpected error occurred. No details are shown here for your safety."},
        status_code=500,
    )
