from __future__ import annotations

import threading
from typing import Any, Callable, Optional

import requests
from PySide6.QtCore import QObject, Signal


class ApiClient(QObject):
    status_received = Signal(dict)
    alerts_received = Signal(dict)
    log_received = Signal(dict)
    whitelist_received = Signal(dict)
    scan_received = Signal(dict)
    config_received = Signal(dict)
    deauth_stats_received = Signal(dict)
    action_done = Signal(dict)
    error = Signal(dict)

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url.rstrip("/")

    def set_base_url(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        timeout: int = 5,
        **kwargs,
    ) -> dict:
        response = requests.request(
            method,
            f"{self.base_url}{path}",
            timeout=timeout,
            **kwargs,
        )
        if not response.ok:
            detail = ""
            try:
                payload = response.json()
                detail = payload.get("detail") or payload.get("message", "")
            except Exception:
                detail = response.text.strip()
            raise RuntimeError(detail or f"HTTP {response.status_code}")

        if not response.content:
            return {"status": "ok"}

        try:
            return response.json()
        except Exception as exc:
            raise RuntimeError("Invalid JSON response") from exc

    def _run(
        self,
        fn: Callable[[], Any],
        on_success: Signal,
        *,
        source: str,
        blocking: bool,
    ) -> None:
        def worker() -> None:
            try:
                on_success.emit(fn())
            except Exception as exc:
                self.error.emit(
                    {
                        "source": source,
                        "blocking": blocking,
                        "message": str(exc),
                    }
                )

        threading.Thread(target=worker, daemon=True).start()

    def get_status(self) -> None:
        self._run(
            lambda: self._request_json("GET", "/api/status"),
            self.status_received,
            source="status",
            blocking=False,
        )

    def get_alerts(self, limit: int = 120, event_type: str = "") -> None:
        def fetch() -> dict:
            params = {"limit": limit}
            if event_type:
                params["event_type"] = event_type
            return self._request_json("GET", "/api/alerts", params=params, timeout=5)

        self._run(fetch, self.alerts_received, source="alerts", blocking=False)

    def get_log(self, limit: int = 250, event_type: str = "") -> None:
        def fetch() -> dict:
            params = {"limit": limit}
            if event_type:
                params["event_type"] = event_type
            return self._request_json("GET", "/api/alerts/log", params=params, timeout=8)

        self._run(fetch, self.log_received, source="logs", blocking=True)

    def get_whitelist(self) -> None:
        self._run(
            lambda: self._request_json("GET", "/api/whitelist", timeout=5),
            self.whitelist_received,
            source="whitelist",
            blocking=False,
        )

    def get_config(self) -> None:
        self._run(
            lambda: self._request_json("GET", "/api/config", timeout=5),
            self.config_received,
            source="config",
            blocking=False,
        )

    def get_deauth_stats(self) -> None:
        self._run(
            lambda: self._request_json("GET", "/api/deauth/stats", timeout=5),
            self.deauth_stats_received,
            source="deauth_stats",
            blocking=False,
        )

    def scan(self) -> None:
        self._run(
            lambda: self._request_json("POST", "/api/scan", timeout=35),
            self.scan_received,
            source="scan",
            blocking=True,
        )

    def start_monitor(self, target_bssids: Optional[list[str]]) -> None:
        self._run(
            lambda: self._request_json(
                "POST",
                "/api/monitor/start",
                timeout=10,
                json={"target_bssids": target_bssids},
            ),
            self.action_done,
            source="start_monitor",
            blocking=True,
        )

    def stop_monitor(self) -> None:
        self._run(
            lambda: self._request_json("POST", "/api/monitor/stop", timeout=5),
            self.action_done,
            source="stop_monitor",
            blocking=True,
        )

    def clear_log(self) -> None:
        self._run(
            lambda: self._request_json("DELETE", "/api/alerts/log", timeout=5),
            self.action_done,
            source="clear_log",
            blocking=True,
        )

    def add_whitelist(self, payload: dict) -> None:
        self._run(
            lambda: self._request_json("POST", "/api/whitelist", timeout=5, json=payload),
            self.action_done,
            source="add_whitelist",
            blocking=True,
        )

    def update_whitelist(self, original_bssid: str, payload: dict) -> None:
        self._run(
            lambda: self._request_json(
                "PUT",
                f"/api/whitelist/{original_bssid}",
                timeout=5,
                json=payload,
            ),
            self.action_done,
            source="update_whitelist",
            blocking=True,
        )

    def delete_whitelist(self, bssid: str) -> None:
        self._run(
            lambda: self._request_json("DELETE", f"/api/whitelist/{bssid}", timeout=5),
            self.action_done,
            source="delete_whitelist",
            blocking=True,
        )

    def save_config(self, payload: dict) -> None:
        self._run(
            lambda: self._request_json("PUT", "/api/config", timeout=10, json=payload),
            self.action_done,
            source="save_config",
            blocking=True,
        )

