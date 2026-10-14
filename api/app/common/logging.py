"""Logging JSON con request_id y duración por petición (ver observability.md)."""

from __future__ import annotations

import logging
import sys
import time
import uuid

from flask import Flask, Response, g, request
from pythonjsonlogger.json import JsonFormatter

access_log = logging.getLogger("app.access")


def init_app(app: Flask) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter(
            "{asctime}{levelname}{name}{message}",
            style="{",
            rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(app.config["LOG_LEVEL"])

    @app.before_request
    def start_request() -> None:
        g.request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
        g.request_started = time.perf_counter()

    @app.after_request
    def end_request(response: Response) -> Response:
        duration_ms = round((time.perf_counter() - g.request_started) * 1000, 1)
        response.headers["X-Request-Id"] = g.request_id
        level = logging.WARNING if duration_ms > app.config["SLOW_REQUEST_MS"] else logging.INFO
        access_log.log(
            level,
            "request.slow" if level == logging.WARNING else "request",
            extra={
                "request_id": g.request_id,
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
