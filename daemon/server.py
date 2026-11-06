#!/usr/bin/env python3
"""Grok Bot Progress local daemon — stdlib only.

Bind 127.0.0.1:7310
  POST /v1/events          upsert one event
  GET  /v1/tasks           list all tasks
  GET  /v1/tasks/{task_id} get one task
  GET  /healthz
  static files from web/
Optional: poll inbox/*.json drops; persist data/tasks.json atomically.
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
import traceback
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
DATA_DIR = ROOT / "data"
DATA_FILE = DATA_DIR / "tasks.json"
INBOX_DIR = ROOT / "inbox"
INBOX_BAD = INBOX_DIR / "bad"
HOST = os.environ.get("GBP_HOST", "127.0.0.1")
PORT = int(os.environ.get("GBP_PORT", "7310"))
INBOX_POLL_SEC = float(os.environ.get("GBP_INBOX_POLL", "1.0"))

VALID_STATES = frozenset({"running", "blocked", "done", "failed", "idle"})
SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")

_lock = threading.RLock()
_tasks: Dict[str, Dict[str, Any]] = {}


def now_iso() -> str:
    return datetime.now(SHANGHAI).isoformat(timespec="seconds")


def atomic_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_tasks() -> None:
    global _tasks
    if not DATA_FILE.exists():
        _tasks = {}
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict) and "tasks" in raw and isinstance(raw["tasks"], dict):
            _tasks = {k: v for k, v in raw["tasks"].items() if isinstance(v, dict)}
        elif isinstance(raw, dict):
            # allow bare map task_id -> event
            _tasks = {k: v for k, v in raw.items() if isinstance(v, dict) and "task_id" in v}
        else:
            _tasks = {}
    except (OSError, json.JSONDecodeError) as e:
        print(f"[gbp] warn: failed to load {DATA_FILE}: {e}", file=sys.stderr)
        _tasks = {}


def persist_tasks() -> None:
    snapshot = {
        "updated_at": now_iso(),
        "tasks": dict(_tasks),
    }
    atomic_write_json(DATA_FILE, snapshot)


def validate_event(body: Any) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(body, dict):
        return None, "body must be a JSON object"
    required = ("task_id", "bot_id", "title", "state", "progress", "detail", "updated_at")
    for key in required:
        if key not in body:
            return None, f"missing field: {key}"
    task_id = body["task_id"]
    bot_id = body["bot_id"]
    title = body["title"]
    state = body["state"]
    progress = body["progress"]
    detail = body["detail"]
    updated_at = body["updated_at"]

    if not isinstance(task_id, str) or not task_id.strip():
        return None, "task_id must be a non-empty string"
    if not isinstance(bot_id, str) or not bot_id.strip():
        return None, "bot_id must be a non-empty string"
    if not isinstance(title, str):
        return None, "title must be a string"
    if not isinstance(state, str) or state not in VALID_STATES:
        return None, f"state must be one of {sorted(VALID_STATES)}"
    if progress is not None:
        if not isinstance(progress, (int, float)) or isinstance(progress, bool):
            return None, "progress must be number 0-100 or null"
        if progress < 0 or progress > 100:
            return None, "progress must be between 0 and 100"
        progress = float(progress)
    if detail is not None and not isinstance(detail, str):
        return None, "detail must be string or null"
    if not isinstance(updated_at, str) or not updated_at.strip():
        return None, "updated_at must be a non-empty string"

    event = {
        "task_id": task_id.strip(),
        "bot_id": bot_id.strip(),
        "title": title,
        "state": state,
        "progress": progress,
        "detail": detail,
        "updated_at": updated_at.strip(),
    }
    return event, None


def upsert_event(event: Dict[str, Any]) -> None:
    with _lock:
        _tasks[event["task_id"]] = event
        persist_tasks()


def list_tasks() -> list:
    with _lock:
        return list(_tasks.values())


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        return _tasks.get(task_id)


def process_inbox_file(path: Path) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            body = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"[gbp] inbox bad json {path.name}: {e}", file=sys.stderr)
        try:
            INBOX_BAD.mkdir(parents=True, exist_ok=True)
            dest = INBOX_BAD / path.name
            os.replace(path, dest)
        except OSError:
            pass
        return
    event, err = validate_event(body)
    if err or event is None:
        print(f"[gbp] inbox invalid {path.name}: {err}", file=sys.stderr)
        try:
            INBOX_BAD.mkdir(parents=True, exist_ok=True)
            os.replace(path, INBOX_BAD / path.name)
        except OSError:
            pass
        return
    upsert_event(event)
    try:
        path.unlink(missing_ok=True)
    except OSError as e:
        print(f"[gbp] inbox unlink failed {path.name}: {e}", file=sys.stderr)


def inbox_loop(stop: threading.Event) -> None:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    while not stop.is_set():
        try:
            for path in sorted(INBOX_DIR.glob("*.json")):
                if path.is_file():
                    process_inbox_file(path)
        except Exception:
            traceback.print_exc()
        stop.wait(INBOX_POLL_SEC)


MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "gbp-daemon/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code: int, obj: Any) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(code, data, "application/json; charset=utf-8")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = unquote(self.path.split("?", 1)[0])
        if path == "/healthz":
            self._send_json(200, {"ok": True})
            return
        if path == "/v1/tasks":
            self._send_json(200, {"tasks": list_tasks()})
            return
        m = re.fullmatch(r"/v1/tasks/([^/]+)", path)
        if m:
            task = get_task(m.group(1))
            if task is None:
                self._send_json(404, {"ok": False, "error": "not found"})
                return
            self._send_json(200, task)
            return
        # static
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        # prevent path escape
        candidate = (WEB_DIR / rel).resolve()
        try:
            candidate.relative_to(WEB_DIR.resolve())
        except ValueError:
            self._send_json(403, {"ok": False, "error": "forbidden"})
            return
        if not candidate.is_file():
            self._send_json(404, {"ok": False, "error": "not found"})
            return
        ext = candidate.suffix.lower()
        ctype = MIME.get(ext, "application/octet-stream")
        data = candidate.read_bytes()
        self._send(200, data, ctype)

    def do_POST(self) -> None:  # noqa: N802
        path = unquote(self.path.split("?", 1)[0])
        if path != "/v1/events":
            self._send_json(404, {"ok": False, "error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            self._send_json(400, {"ok": False, "error": f"invalid json: {e}"})
            return
        # fill updated_at if caller omitted? schema requires it — keep strict
        event, err = validate_event(body)
        if err or event is None:
            self._send_json(400, {"ok": False, "error": err})
            return
        upsert_event(event)
        self._send_json(200, {"ok": True, "task_id": event["task_id"]})


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    load_tasks()

    stop = threading.Event()
    t = threading.Thread(target=inbox_loop, args=(stop,), name="inbox-poll", daemon=True)
    t.start()

    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[gbp] listening on http://{HOST}:{PORT}", flush=True)
    print(f"[gbp] web={WEB_DIR} data={DATA_FILE} inbox={INBOX_DIR}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[gbp] shutting down", flush=True)
    finally:
        stop.set()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
