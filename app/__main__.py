from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import List

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.audio import AudioResource, first_n, group_audio_by_unit, load_audio_resources

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE_DIR / "data" / "workbook"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"


app = FastAPI(title="KET Workbook Level 0")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


if AUDIO_DIR.exists():
    logger.debug("Mounting audio directory at /audio: %s", AUDIO_DIR)
    app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")
else:
    logger.warning("Audio directory not found at startup: %s", AUDIO_DIR)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


ALL_AUDIO: List[AudioResource] = load_audio_resources(AUDIO_DIR)
AUDIO_GROUPS = group_audio_by_unit(ALL_AUDIO)


CURRENCY_OPTIONS = [
    ("USD", "US Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"),
    ("CNY", "Chinese Yuan"),
    ("AUD", "Australian Dollar"),
    ("CAD", "Canadian Dollar"),
    ("CHF", "Swiss Franc"),
    ("HKD", "Hong Kong Dollar"),
    ("SGD", "Singapore Dollar"),
]


def _template_context(request: Request, **kwargs):
    page_title = kwargs.pop("page_title", None)
    context = {
        "request": request,
        "site_title": "KET Workbook Level 0",
        "page_title": page_title,
        "audio_groups": AUDIO_GROUPS,
        "currency_options": CURRENCY_OPTIONS,
        "umami_website_id": os.getenv("UMAMI_WEBSITE_ID", "028e0e39-63ba-4265-9e17-908ba7bfdcb5"),
        "rybbit_website_id": os.getenv("RYBBIT_WEBSITE_ID", "05bc2740acb1"),
    }
    context.update(kwargs)
    return context


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    featured_audio = first_n(ALL_AUDIO, 3)
    first_audio = featured_audio[0] if featured_audio else None
    return templates.TemplateResponse(
        "home.html",
        _template_context(
            request,
            page_title="首页",
            featured_audio=featured_audio,
            first_audio=first_audio,
        ),
    )


@app.post("/payment")
async def payment(
    request: Request,
    customer_name: str = Form(default=""),
    currency: str = Form(default="USD"),
    revenue: float = Form(...),
    email: str = Form(default=""),
    notes: str = Form(default=""),
):
    logger.info(
        "Received payment intent | name=%s | email=%s | currency=%s | revenue=%.2f",
        customer_name or "(anonymous)",
        email or "(not provided)",
        currency,
        revenue,
    )
    if notes:
        logger.debug("Order notes: %s", notes)

    return RedirectResponse(url=request.url_for("list_audio"), status_code=303)


@app.get("/list", response_class=HTMLResponse, name="list_audio")
async def list_audio(request: Request):
    first_audio = ALL_AUDIO[0] if ALL_AUDIO else None
    return templates.TemplateResponse(
        "list.html",
        _template_context(
            request,
            page_title="音频资源列表",
            first_audio=first_audio,
        ),
    )


@app.get("/ping")
async def ping():
    return {"status": "ok"}


def main():
    parser = argparse.ArgumentParser(description="KET Workbook Audio Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8080, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    module_path = f"{__package__}.{__name__}:app" if __package__ else f"{__name__}:app"
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    logger.info(
        "Starting KET Workbook service on %s:%d (reload=%s)",
        args.host,
        args.port,
        args.reload,
    )

    uvicorn.run(module_path, host=args.host, port=args.port, reload=args.reload, log_level=log_level)


if __name__ == "__main__":
    main()

