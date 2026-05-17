"""
webapp/app.py
-------------
FastAPI dashboard cho WiFi Security Monitor.
Chay: sudo .venv/bin/python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
"""

import json
import time
import threading
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from detector.scanner import APScanner
from detector.sniffer import WiFiSniffer

# -----------------------------------------------
# App setup
# -----------------------------------------------
app = FastAPI(title="WiFi Security Monitor")
templates = Jinja2Templates(directory="webapp/templates")

CONFIG_PATH = "config/config.yaml"
_sniffer: WiFiSniffer | None = None
_recent_alerts: list = []   # Buffer 100 alert gan nhat cho dashboard
_lock = threading.Lock()

DEFAULT_CONFIG = {
    "interface": "wlan1mon",
    "whitelist_path": "config/whitelist.json",
    "log_path": "logs/wifi_alerts.jsonl",
    "interactive_scan": True,
    "scan_seconds": 10,
    "scan_max_results": 20,
    "ssid_similarity_threshold": 0.85,
    "alert_cooldown_seconds": 30,
    "deauth_window_seconds": 10,
    "deauth_threshold": 20,
    "opensearch": {
        "enabled": False,
        "endpoint": "http://localhost:9200",
        "index": "wifi-security-logs",
        "verify_tls": False,
        "username": "admin",
        "password": "admin",
    },
    "telegram": {
        "enabled": False,
        "bot_token": "NHAP_BOT_TOKEN",
        "chat_id": "NHAP_CHAT_ID",
    },
}


# -----------------------------------------------
# Helper
# -----------------------------------------------
def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = _deep_merge(base[key], value)
        else:
            merged[key] = value
    return merged


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _coerce_int(value, field: str, minimum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid integer for {field}") from exc
    if minimum is not None and parsed < minimum:
        raise HTTPException(status_code=400, detail=f"{field} must be >= {minimum}")
    return parsed


def _coerce_float(
    value,
    field: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid number for {field}") from exc
    if minimum is not None and parsed < minimum:
        raise HTTPException(status_code=400, detail=f"{field} must be >= {minimum}")
    if maximum is not None and parsed > maximum:
        raise HTTPException(status_code=400, detail=f"{field} must be <= {maximum}")
    return parsed


def _normalize_config(cfg: dict | None) -> dict:
    merged = _deep_merge(DEFAULT_CONFIG, cfg or {})

    opensearch = merged.get("opensearch", {})
    telegram = merged.get("telegram", {})

    return {
        "interface": str(merged.get("interface", DEFAULT_CONFIG["interface"])).strip()
        or DEFAULT_CONFIG["interface"],
        "whitelist_path": str(
            merged.get("whitelist_path", DEFAULT_CONFIG["whitelist_path"])
        ).strip()
        or DEFAULT_CONFIG["whitelist_path"],
        "log_path": str(merged.get("log_path", DEFAULT_CONFIG["log_path"])).strip()
        or DEFAULT_CONFIG["log_path"],
        "interactive_scan": _coerce_bool(
            merged.get("interactive_scan", DEFAULT_CONFIG["interactive_scan"])
        ),
        "scan_seconds": _coerce_int(
            merged.get("scan_seconds", DEFAULT_CONFIG["scan_seconds"]),
            "scan_seconds",
            minimum=1,
        ),
        "scan_max_results": _coerce_int(
            merged.get("scan_max_results", DEFAULT_CONFIG["scan_max_results"]),
            "scan_max_results",
            minimum=1,
        ),
        "ssid_similarity_threshold": _coerce_float(
            merged.get(
                "ssid_similarity_threshold",
                DEFAULT_CONFIG["ssid_similarity_threshold"],
            ),
            "ssid_similarity_threshold",
            minimum=0.0,
            maximum=1.0,
        ),
        "alert_cooldown_seconds": _coerce_int(
            merged.get(
                "alert_cooldown_seconds",
                DEFAULT_CONFIG["alert_cooldown_seconds"],
            ),
            "alert_cooldown_seconds",
            minimum=0,
        ),
        "deauth_window_seconds": _coerce_int(
            merged.get(
                "deauth_window_seconds",
                DEFAULT_CONFIG["deauth_window_seconds"],
            ),
            "deauth_window_seconds",
            minimum=1,
        ),
        "deauth_threshold": _coerce_int(
            merged.get("deauth_threshold", DEFAULT_CONFIG["deauth_threshold"]),
            "deauth_threshold",
            minimum=1,
        ),
        "opensearch": {
            "enabled": _coerce_bool(
                opensearch.get("enabled", DEFAULT_CONFIG["opensearch"]["enabled"])
            ),
            "endpoint": str(
                opensearch.get("endpoint", DEFAULT_CONFIG["opensearch"]["endpoint"])
            ).strip()
            or DEFAULT_CONFIG["opensearch"]["endpoint"],
            "index": str(
                opensearch.get("index", DEFAULT_CONFIG["opensearch"]["index"])
            ).strip()
            or DEFAULT_CONFIG["opensearch"]["index"],
            "verify_tls": _coerce_bool(
                opensearch.get(
                    "verify_tls", DEFAULT_CONFIG["opensearch"]["verify_tls"]
                )
            ),
            "username": str(
                opensearch.get("username", DEFAULT_CONFIG["opensearch"]["username"])
            ).strip()
            or DEFAULT_CONFIG["opensearch"]["username"],
            "password": str(
                opensearch.get("password", DEFAULT_CONFIG["opensearch"]["password"])
            ),
        },
        "telegram": {
            "enabled": _coerce_bool(
                telegram.get("enabled", DEFAULT_CONFIG["telegram"]["enabled"])
            ),
            "bot_token": str(
                telegram.get("bot_token", DEFAULT_CONFIG["telegram"]["bot_token"])
            ),
            "chat_id": str(
                telegram.get("chat_id", DEFAULT_CONFIG["telegram"]["chat_id"])
            ),
        },
    }


def _load_config() -> dict:
    config_file = Path(CONFIG_PATH)
    if not config_file.exists():
        return _normalize_config(None)
    with open(config_file, "r", encoding="utf-8") as f:
        return _normalize_config(yaml.safe_load(f))


def _save_config(cfg: dict) -> dict:
    normalized = _normalize_config(cfg)
    config_file = Path(CONFIG_PATH)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(normalized, f, allow_unicode=True, sort_keys=False)
    return normalized


def _on_alert(alert: dict):
    """Callback duoc goi khi sniffer tao alert moi."""
    with _lock:
        _recent_alerts.insert(0, alert)
        if len(_recent_alerts) > 100:
            _recent_alerts.pop()


def _append_log_event(event: dict) -> None:
    """Ghi mot su kien he thong vao file JSONL."""
    cfg = _load_config()
    log_path = Path(cfg["log_path"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


# -----------------------------------------------
# Routes: Pages
# -----------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -----------------------------------------------
# Routes: API - Status
# -----------------------------------------------
@app.get("/api/status")
async def api_status():
    global _sniffer
    cfg = _load_config()
    return {
        "running": _sniffer.is_running() if _sniffer else False,
        "interface": cfg["interface"],
        "stats": _sniffer.stats if _sniffer else {},
    }


@app.get("/api/config")
async def api_get_config():
    return {"config": _load_config()}


@app.put("/api/config")
async def api_save_config(request: Request):
    body = await request.json()
    config = _save_config(body)
    restart_required = _sniffer.is_running() if _sniffer else False
    return {
        "status": "saved",
        "config": config,
        "restart_required": restart_required,
        "message": (
            "Config saved. Restart monitoring to apply runtime changes."
            if restart_required
            else "Config saved."
        ),
    }


# -----------------------------------------------
# Routes: API - Scan
# -----------------------------------------------
@app.post("/api/scan")
async def api_scan():
    """Quet AP trong 10 giay, tra ve danh sach."""
    cfg = _load_config()
    scanner = APScanner(interface=cfg["interface"])
    aps = scanner.scan(
        seconds=cfg.get("scan_seconds", 10),
        max_results=cfg.get("scan_max_results", 20),
    )
    scan_event = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event_type": "scan_completed",
        "severity": "info",
        "interface": cfg["interface"],
        "ap_count": len(aps),
        "scan_seconds": cfg.get("scan_seconds", 10),
        "message": (
            f"Scan completed on {cfg['interface']} with {len(aps)} access point(s) detected."
        ),
        "top_results": aps[:5],
    }
    _append_log_event(scan_event)
    return {"aps": aps, "scan_event": scan_event}


# -----------------------------------------------
# Routes: API - Monitor control
# -----------------------------------------------
@app.post("/api/monitor/start")
async def api_start(request: Request, background_tasks: BackgroundTasks):
    global _sniffer, _recent_alerts

    body = await request.json()
    target_bssids = body.get("target_bssids", None)  # None = tat ca

    cfg = _load_config()

    # Dung sniffer cu neu dang chay
    if _sniffer and _sniffer.is_running():
        _sniffer.stop()
        time.sleep(0.5)

    _recent_alerts.clear()
    _sniffer = WiFiSniffer(config=cfg)
    _sniffer.set_target(target_bssids)
    _sniffer.add_alert_callback(_on_alert)
    _sniffer.start()

    return {"status": "started", "interface": cfg["interface"]}


@app.post("/api/monitor/stop")
async def api_stop():
    global _sniffer
    if _sniffer:
        _sniffer.stop()
    return {"status": "stopped"}


# -----------------------------------------------
# Routes: API - Alerts
# -----------------------------------------------
@app.get("/api/alerts")
async def api_alerts(limit: int = 50, event_type: Optional[str] = None):
    """Lay danh sach alert gan nhat."""
    with _lock:
        data = list(_recent_alerts)

    if event_type:
        data = [a for a in data if a.get("event_type") == event_type]

    return {"alerts": data[:limit], "total": len(data)}


@app.get("/api/alerts/log")
async def api_alerts_log(limit: int = 100, event_type: Optional[str] = None):
    """Doc log file JSONL va tra ve."""
    cfg = _load_config()
    log_path = Path(cfg["log_path"])
    alerts = []

    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in reversed(lines[-limit:]):
            line = line.strip()
            if line:
                try:
                    item = json.loads(line)
                    if event_type and item.get("event_type") != event_type:
                        continue
                    alerts.append(item)
                except Exception:
                    pass

    return {"alerts": alerts, "total": len(alerts)}


@app.delete("/api/alerts/log")
async def api_clear_log():
    """Xoa log file."""
    cfg = _load_config()
    log_path = Path(cfg["log_path"])
    if log_path.exists():
        log_path.write_text("")
    with _lock:
        _recent_alerts.clear()
    return {"status": "cleared"}


# -----------------------------------------------
# Routes: API - Whitelist
# -----------------------------------------------
@app.get("/api/whitelist")
async def api_get_whitelist():
    cfg = _load_config()
    wl_path = Path(cfg["whitelist_path"])
    if not wl_path.exists():
        return {"whitelist": []}
    with open(wl_path, "r", encoding="utf-8") as f:
        return {"whitelist": json.load(f)}


@app.post("/api/whitelist")
async def api_add_whitelist(request: Request):
    """Them AP vao whitelist."""
    body = await request.json()
    required = ["ssid", "bssid"]
    for field in required:
        if not body.get(field):
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    cfg = _load_config()
    wl_path = Path(cfg["whitelist_path"])

    whitelist = []
    if wl_path.exists():
        with open(wl_path, "r", encoding="utf-8") as f:
            whitelist = json.load(f)

    # Kiem tra trung BSSID
    new_bssid = body["bssid"].upper()
    for ap in whitelist:
        if ap.get("bssid", "").upper() == new_bssid:
            raise HTTPException(status_code=409, detail="BSSID already in whitelist")

    entry = {
        "ssid": body["ssid"],
        "bssid": new_bssid,
        "channel": body.get("channel", 0),
        "encryption": body.get("encryption", "WPA2"),
        "note": body.get("note", ""),
    }
    whitelist.append(entry)

    with open(wl_path, "w", encoding="utf-8") as f:
        json.dump(whitelist, f, indent=2, ensure_ascii=False)

    # Reload detector neu dang chay
    if _sniffer:
        _sniffer.rogue_detector.reload_whitelist()

    return {"status": "added", "entry": entry}


@app.put("/api/whitelist/{bssid}")
async def api_update_whitelist(bssid: str, request: Request):
    """Cap nhat AP hop le trong whitelist theo BSSID cu."""
    body = await request.json()
    required = ["ssid", "bssid"]
    for field in required:
        if not body.get(field):
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    cfg = _load_config()
    wl_path = Path(cfg["whitelist_path"])

    if not wl_path.exists():
        raise HTTPException(status_code=404, detail="Whitelist not found")

    with open(wl_path, "r", encoding="utf-8") as f:
        whitelist = json.load(f)

    target_bssid = bssid.upper()
    new_bssid = body["bssid"].upper()
    match_index = None

    for index, ap in enumerate(whitelist):
        existing_bssid = ap.get("bssid", "").upper()
        if existing_bssid == target_bssid:
            match_index = index
        elif existing_bssid == new_bssid:
            raise HTTPException(status_code=409, detail="BSSID already in whitelist")

    if match_index is None:
        raise HTTPException(status_code=404, detail="BSSID not found")

    entry = {
        "ssid": body["ssid"],
        "bssid": new_bssid,
        "channel": body.get("channel", 0),
        "encryption": body.get("encryption", "WPA2"),
        "note": body.get("note", ""),
    }
    whitelist[match_index] = entry

    with open(wl_path, "w", encoding="utf-8") as f:
        json.dump(whitelist, f, indent=2, ensure_ascii=False)

    if _sniffer:
        _sniffer.rogue_detector.reload_whitelist()

    return {"status": "updated", "entry": entry}


@app.delete("/api/whitelist/{bssid}")
async def api_delete_whitelist(bssid: str):
    """Xoa AP khoi whitelist theo BSSID."""
    cfg = _load_config()
    wl_path = Path(cfg["whitelist_path"])

    if not wl_path.exists():
        raise HTTPException(status_code=404, detail="Whitelist not found")

    with open(wl_path, "r", encoding="utf-8") as f:
        whitelist = json.load(f)

    new_wl = [ap for ap in whitelist if ap.get("bssid", "").upper() != bssid.upper()]

    if len(new_wl) == len(whitelist):
        raise HTTPException(status_code=404, detail="BSSID not found")

    with open(wl_path, "w", encoding="utf-8") as f:
        json.dump(new_wl, f, indent=2, ensure_ascii=False)

    if _sniffer:
        _sniffer.rogue_detector.reload_whitelist()

    return {"status": "deleted", "bssid": bssid}


# -----------------------------------------------
# Routes: API - Deauth stats
# -----------------------------------------------
@app.get("/api/deauth/stats")
async def api_deauth_stats():
    if not _sniffer:
        return {"stats": {}}
    return {"stats": _sniffer.deauth_detector.get_stats()}
