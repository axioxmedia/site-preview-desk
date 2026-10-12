"""本地站点预览器 — temporary local server for ZIP + SQL website preview."""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path
from typing import Any

import http.server
import socketserver

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from axioxmedia import (
    AIO_BRAND,
    AIO_SOFTWARE_NAME_EN,
    aio_logo_png,
    aio_watermark,
    apply_hwnd_icon,
    axiox_window_title,
)
from utm_beacon import schedule_utm_beacon

APP_VERSION = "1.0.0"
PRODUCT_EN = "Site Preview Desk"
PRODUCT_ZH = "本地站点预览器"


def app_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


ROOT = app_root()
STATIC = ROOT / "static"

app = FastAPI(title=PRODUCT_ZH, version=APP_VERSION)
app.mount("/assets", StaticFiles(directory=STATIC), name="assets")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(content=aio_logo_png(), media_type="image/png")

# Runtime state
STATE: dict[str, Any] = {
    "zip_path": "",
    "sql_path": "",
    "temp_dir": "",
    "preview_proc": None,
    "preview_httpd": None,
    "preview_port": 0,
    "preview_url": "",
    "php_available": False,
    "php_version": "",
    "extensions": [],
}


def runtime_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


LOG_FILE = runtime_dir() / "site_preview.log"


def write_log(message: str) -> None:
    try:
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + message + "\n")
    except Exception:
        pass


class SelectRequest(BaseModel):
    kind: str


class PreviewOptions(BaseModel):
    php_version: str = ""
    extensions: list[str] = []
    docroot: str = ""


@app.get("/api/defaults")
def defaults() -> dict[str, Any]:
    return {
        "version": APP_VERSION,
        "product": PRODUCT_EN,
        "product_zh": PRODUCT_ZH,
        "brand": AIO_BRAND,
    }


@app.get("/brand/logo.png")
def logo() -> Response:
    return Response(content=aio_logo_png(), media_type="image/png")


def _detect_php() -> tuple[bool, str, list[str]]:
    try:
        ver = subprocess.check_output(["php", "-v"], text=True, timeout=5, stderr=subprocess.STDOUT)
        version = ver.splitlines()[0] if ver else ""
        mods = subprocess.check_output(["php", "-m"], text=True, timeout=5, stderr=subprocess.STDOUT)
        exts = [line.strip() for line in mods.splitlines() if line.strip() and not line.startswith("[")]
        return True, version, exts
    except Exception:
        return False, "", []


def _scan_project(extract_dir: Path) -> dict[str, Any]:
    php_files = list(extract_dir.rglob("*.php"))
    has_php = len(php_files) > 0
    index_candidates = ["index.php", "index.html", "index.htm", "public/index.php", "public/index.html"]
    docroot = ""
    for cand in index_candidates:
        if (extract_dir / cand).exists():
            docroot = str(Path(cand).parent) if "/" in cand else "."
            break
    common_exts = ["pdo_mysql", "mysqli", "pdo_sqlite", "gd", "mbstring", "curl", "zip", "intl", "openssl", "fileinfo"]
    php_ok, php_ver, available = _detect_php()
    suggested = [e for e in common_exts if e in available or not php_ok]
    return {
        "has_php": has_php,
        "php_available": php_ok,
        "php_version": php_ver,
        "docroot": docroot or ".",
        "suggested_extensions": suggested,
        "available_extensions": available,
        "file_count": sum(1 for _ in extract_dir.rglob("*") if _.is_file()),
    }


@app.post("/api/analyze")
def analyze() -> dict[str, Any]:
    zip_path = STATE.get("zip_path") or ""
    if not zip_path or not Path(zip_path).exists():
        raise HTTPException(400, "请先选择 ZIP 文件")
    # Quick scan without full extract for analysis
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    has_php = any(n.lower().endswith(".php") for n in names)
    php_ok, php_ver, available = _detect_php()
    common = ["pdo_mysql", "mysqli", "pdo_sqlite", "gd", "mbstring", "curl", "zip", "intl", "openssl"]
    return {
        "has_php": has_php,
        "php_available": php_ok,
        "php_version": php_ver,
        "suggested_extensions": [e for e in common if e in available or True],
        "available_extensions": available,
        "file_count": len(names),
        "sql_selected": bool(STATE.get("sql_path")),
    }


@app.post("/api/start_preview")
def start_preview(opts: PreviewOptions) -> dict[str, Any]:
    zip_path = STATE.get("zip_path")
    sql_path = STATE.get("sql_path")
    if not zip_path or not Path(zip_path).exists():
        raise HTTPException(400, "ZIP 未选择或不存在")

    # Clean previous
    stop_preview()

    tmp = Path(tempfile.mkdtemp(prefix="site_preview_"))
    STATE["temp_dir"] = str(tmp)
    write_log(f"extract to {tmp}")

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(tmp)

    # SQL import attempt
    db_info = ""
    if sql_path and Path(sql_path).exists():
        try:
            db_path = tmp / "preview.db"
            # Simple import for SQLite-compatible dumps; MySQL dumps may fail partially
            with sqlite3.connect(db_path) as conn:
                sql_text = Path(sql_path).read_text(encoding="utf-8", errors="ignore")
                # Strip MySQL-specific
                sql_text = re.sub(r"ENGINE=\w+", "", sql_text, flags=re.I)
                sql_text = re.sub(r"AUTO_INCREMENT=\d+", "", sql_text, flags=re.I)
                conn.executescript(sql_text)
            db_info = f"SQLite 已导入到 {db_path.name}"
            write_log(db_info)
        except Exception as exc:
            db_info = f"SQL 导入提示：{exc}（文件已复制到临时目录）"
            shutil.copy(sql_path, tmp / "import.sql")
            write_log(db_info)

    # Find docroot
    doc = opts.docroot or "."
    serve_root = tmp / doc if doc != "." else tmp
    if not serve_root.exists():
        serve_root = tmp

    php_ok, _, _ = _detect_php()
    port = _free_port(8800)
    url = f"http://127.0.0.1:{port}"

    proc = None
    httpd = None
    if php_ok and any(serve_root.rglob("*.php")):
        cmd = ["php", "-S", f"127.0.0.1:{port}", "-t", str(serve_root)]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        write_log(f"started php -S on {port}")
        STATE["preview_proc"] = proc
    else:
        # Pure-Python static server so a frozen EXE does not re-launch itself
        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(serve_root), **kwargs)

            def log_message(self, format, *args):
                return

        httpd = socketserver.TCPServer(("127.0.0.1", port), QuietHandler)
        httpd.allow_reuse_address = True
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        write_log(f"started pure-python static server on {port}")
        STATE["preview_httpd"] = httpd

    STATE["preview_port"] = port
    STATE["preview_url"] = url

    time.sleep(0.4)
    return {
        "ok": True,
        "url": url,
        "port": port,
        "temp_dir": str(tmp),
        "db_info": db_info,
        "php_used": bool(php_ok and proc),
    }


@app.post("/api/stop_preview")
def stop_preview() -> dict[str, Any]:
    proc = STATE.get("preview_proc")
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        write_log("preview php stopped")
    STATE["preview_proc"] = None

    httpd = STATE.get("preview_httpd")
    if httpd:
        try:
            httpd.shutdown()
            httpd.server_close()
            write_log("preview static server stopped")
        except Exception as exc:
            write_log(f"httpd stop: {exc}")
    STATE["preview_httpd"] = None

    STATE["preview_url"] = ""
    tmp = STATE.get("temp_dir")
    if tmp and Path(tmp).exists():
        try:
            shutil.rmtree(tmp, ignore_errors=True)
            write_log(f"cleaned {tmp}")
        except Exception as exc:
            write_log(f"cleanup warn: {exc}")
    STATE["temp_dir"] = ""
    return {"ok": True}


def open_system_browser(url: str) -> bool:
    """Open the OS default browser, never another webview window."""
    try:
        if os.name == "nt":
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            import webbrowser
            webbrowser.open(url)
        write_log(f"opened system browser: {url}")
        return True
    except Exception as exc:
        write_log(f"browser open failed: {exc}")
        return False


@app.get("/api/status")
def status() -> dict[str, Any]:
    proc = STATE.get("preview_proc")
    running = bool(proc and proc.poll() is None)
    return {
        "running": running,
        "url": STATE.get("preview_url") or "",
        "zip": STATE.get("zip_path") or "",
        "sql": STATE.get("sql_path") or "",
        "temp": STATE.get("temp_dir") or "",
    }


# Desktop file dialog helpers (exposed via pywebview)
def select_file(kind: str) -> str:
    try:
        import webview
        if kind == "zip":
            result = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG, file_types=("ZIP files (*.zip)", "All files (*.*)")
            )
        else:
            result = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG, file_types=("SQL files (*.sql)", "All files (*.*)")
            )
        if result and len(result) > 0:
            path = result[0]
            if kind == "zip":
                STATE["zip_path"] = path
            else:
                STATE["sql_path"] = path
            write_log(f"selected {kind}: {path}")
            return path
    except Exception as exc:
        write_log(f"dialog error: {exc}")
    return ""


# ---- bootstrap (adapted from reference) ----

def _free_port(preferred: int = 8787) -> int:
    import socket
    for port in range(preferred, preferred + 40):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return preferred


def ensure_stdio() -> None:
    if sys.stdout is None:
        sys.stdout = LOG_FILE.open("a", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = LOG_FILE.open("a", encoding="utf-8")


def run_server(host: str, port: int, reload: bool = False) -> None:
    import uvicorn

    ensure_stdio()
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
        log_config=None,
        lifespan="on",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = False
    server.run()


def wait_ready(url: str, errors: list[str], timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if errors:
            raise RuntimeError(errors[0])
        try:
            with httpx.Client(timeout=0.8, trust_env=False) as http:
                if http.get(url).status_code < 500:
                    return
        except httpx.HTTPError:
            time.sleep(0.2)
        except Exception as exc:
            write_log(f"ready check: {exc}")
            time.sleep(0.2)
    extra = f"\n服务线程错误：{errors[0]}" if errors else ""
    raise RuntimeError(f"本地服务启动超时：{url}{extra}\n日志：{LOG_FILE}")


def show_error(message: str) -> None:
    write_log(message)
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, PRODUCT_ZH, 0x10)
        except Exception:
            pass


def run_desktop() -> None:
    write_log(f"start frozen={getattr(sys, 'frozen', False)}")
    write_log(f"static={STATIC} exists={STATIC.exists()}")

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    write_log(f"bind {url}")
    server_error: list[str] = []

    def _serve() -> None:
        try:
            run_server("127.0.0.1", port, reload=False)
        except Exception:
            import traceback
            server_error.append(traceback.format_exc())
            write_log(server_error[-1])

    thread = threading.Thread(target=_serve, name="uvicorn", daemon=True)
    thread.start()
    wait_ready(f"{url}/api/defaults", server_error)
    schedule_utm_beacon(product_en=PRODUCT_EN, version=app.version, log=write_log)

    try:
        import webview

        window = webview.create_window(
            title=axiox_window_title(),
            url=url,
            width=1280,
            height=820,
            min_size=(960, 640),
            background_color="#0b0d12",
        )
        window.expose(select_file, open_system_browser)

        def paint_chrome(_=None) -> None:
            if os.name != "nt":
                return
            try:
                import ctypes
                hwnd = int(window.native.Handle.ToInt32())
                apply_hwnd_icon(hwnd)
                value = ctypes.c_int(1)
                for attr in (20, 19):
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
                    )
            except Exception as exc:
                write_log(f"dark titlebar skipped: {exc}")

        try:
            window.events.shown += paint_chrome
        except Exception:
            pass
        webview.start()
        return
    except Exception:
        import traceback
        write_log(traceback.format_exc())
        import webbrowser
        webbrowser.open(url)
        while thread.is_alive():
            thread.join(timeout=0.5)


if __name__ == "__main__":
    import multiprocessing
    import traceback

    multiprocessing.freeze_support()
    ensure_stdio()
    try:
        desktop = "--web" not in sys.argv and os.environ.get("SITE_PREVIEW_WEB") != "1"
        if desktop:
            run_desktop()
        else:
            run_server("127.0.0.1", _free_port(8787), reload=not getattr(sys, "frozen", False))
    except Exception:
        show_error("启动失败：\n\n" + traceback.format_exc() + f"\n\n日志文件：{LOG_FILE}")
        raise
