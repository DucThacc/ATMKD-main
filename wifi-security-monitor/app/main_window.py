from __future__ import annotations

import sys
from difflib import SequenceMatcher

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.api import ApiClient
from app.pages.alert_center_page import AlertCenterPage
from app.pages.dashboard_page import DashboardPage
from app.pages.logs_page import LogsPage
from app.pages.monitor_page import MonitorPage
from app.pages.settings_page import SettingsPage
from app.pages.stats_page import StatsPage
from app.pages.whitelist_page import WhitelistPage
from app.styles import get_stylesheet
from app.utils import DEFAULT_BASE_URL, DEFAULT_THEME, NAV_ITEMS, coerce_bool, guess_vendor
from app.widgets.workspace_switcher import WorkspaceSwitcher


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_store = QSettings("WiFiSecurityMonitor", "DesktopShell")
        self.theme_name = str(self.settings_store.value("theme_name", DEFAULT_THEME) or DEFAULT_THEME)
        self.base_url = str(self.settings_store.value("base_url", DEFAULT_BASE_URL) or DEFAULT_BASE_URL)
        self.status_refresh_seconds = int(self.settings_store.value("status_refresh_seconds", 3) or 3)
        self.alert_refresh_seconds = int(self.settings_store.value("alert_refresh_seconds", 3) or 3)
        self.log_limit = int(self.settings_store.value("log_limit", 250) or 250)
        self.logs_auto_scroll = coerce_bool(self.settings_store.value("logs_auto_scroll", True))

        self._connection_ok = False
        self._status_loaded = False
        self._current_scope = "All detected APs"
        self._latest_alerts: list[dict] = []
        self._log_alerts: list[dict] = []
        self._scan_results: list[dict] = []
        self._whitelist_entries: list[dict] = []
        self._config_cache: dict = {}
        self._selected_monitor_bssids: set[str] = set()

        self.setWindowTitle("WiFi Security Monitor")
        self.resize(1560, 980)
        self.setMinimumSize(1260, 820)

        self.api = ApiClient(self.base_url)
        self.api.status_received.connect(self.on_status)
        self.api.alerts_received.connect(self.on_alerts)
        self.api.log_received.connect(self.on_log)
        self.api.whitelist_received.connect(self.on_whitelist)
        self.api.scan_received.connect(self.on_scan)
        self.api.config_received.connect(self.on_config)
        self.api.action_done.connect(self.on_action_done)
        self.api.error.connect(self.on_error)

        self._build_ui()
        self._apply_styles()
        self._apply_saved_preferences_to_settings_page()
        self._set_connection_state(False, "Connecting to remote API")

        self.status_timer = QTimer(self)
        self.status_timer.setInterval(max(1, self.status_refresh_seconds) * 1000)
        self.status_timer.timeout.connect(self.api.get_status)
        self.status_timer.start()

        self.alert_timer = QTimer(self)
        self.alert_timer.setInterval(max(1, self.alert_refresh_seconds) * 1000)
        self.alert_timer.timeout.connect(lambda: self.api.get_alerts(limit=120))
        self.alert_timer.start()

        self._refresh_all()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("AppRoot")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(12)

        root_layout.addWidget(self._build_topbar())
        self.workspace_switcher = WorkspaceSwitcher()
        self.workspace_switcher.workspace_selected.connect(self._switch_workspace)
        root_layout.addWidget(self.workspace_switcher)

        canvas = QFrame()
        canvas.setObjectName("WorkspaceCanvas")
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.currentChanged.connect(self._on_workspace_changed)

        self.dashboard_page = DashboardPage()
        self.monitor_page = MonitorPage()
        self.alert_center_page = AlertCenterPage()
        self.whitelist_page = WhitelistPage()
        self.logs_page = LogsPage()
        self.stats_page = StatsPage()
        self.settings_page = SettingsPage()

        self.monitor_page.scan_requested.connect(self._run_scan)
        self.monitor_page.start_requested.connect(self._start_monitor)
        self.monitor_page.stop_requested.connect(self._stop_monitor)
        self.monitor_page.clear_requested.connect(self._clear_monitor_session)
        self.monitor_page.promote_to_whitelist_requested.connect(self._prefill_whitelist_from_monitor)

        self.whitelist_page.refresh_requested.connect(self.api.get_whitelist)
        self.whitelist_page.save_requested.connect(self._submit_whitelist)
        self.whitelist_page.delete_requested.connect(self.api.delete_whitelist)

        self.logs_page.refresh_requested.connect(self._load_logs)
        self.logs_page.clear_requested.connect(self.api.clear_log)

        self.stats_page.refresh_requested.connect(self._load_logs)

        self.settings_page.save_remote_requested.connect(self._save_remote_config)
        self.settings_page.apply_local_requested.connect(self._apply_local_preferences_from_settings)
        self.settings_page.reload_requested.connect(self.api.get_config)
        self.settings_page.test_connection_requested.connect(self._test_connection)

        for page in [
            self.dashboard_page,
            self.monitor_page,
            self.alert_center_page,
            self.whitelist_page,
            self.logs_page,
            self.stats_page,
            self.settings_page,
        ]:
            self.stack.addWidget(page)

        canvas_layout.addWidget(self.stack)
        root_layout.addWidget(canvas, 1)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")
        self._switch_workspace(0)

    def _build_topbar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("TopBar")
        frame.setMaximumHeight(104)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        left = QVBoxLayout()
        left.setSpacing(1)
        eyebrow = QLabel("WIRELESS THREAT CONSOLE")
        eyebrow.setObjectName("SectionEyebrow")
        title = QLabel("WiFi Security Monitor")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Live airspace monitoring, triage, and policy control")
        subtitle.setObjectName("AppSubtitle")
        self.remote_target_label = QLabel(f"API TARGET  {self.base_url}")
        self.remote_target_label.setObjectName("SmallMeta")
        left.addWidget(eyebrow)
        left.addWidget(title)
        left.addWidget(subtitle)
        left.addWidget(self.remote_target_label)

        right = QHBoxLayout()
        right.setSpacing(10)
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.connection_badge = QLabel("OFFLINE")
        self.connection_badge.setObjectName("StatusPill")
        self.interface_badge = QLabel("IFACE: -")
        self.interface_badge.setObjectName("StatusPill")
        self.sync_badge = QLabel("SYNC: waiting")
        self.sync_badge.setObjectName("StatusPill")
        self.refresh_button = QPushButton("Refresh Now")
        self.refresh_button.setProperty("variant", "primary")
        self.refresh_button.clicked.connect(self._quick_refresh)

        right.addWidget(self.connection_badge)
        right.addWidget(self.interface_badge)
        right.addWidget(self.sync_badge)
        right.addWidget(self.refresh_button)

        layout.addLayout(left, 1)
        layout.addLayout(right)
        return frame

    def _apply_styles(self) -> None:
        QApplication.instance().setStyleSheet(get_stylesheet(self.theme_name))
        self._update_connection_badges()

    def _apply_saved_preferences_to_settings_page(self) -> None:
        self.settings_page.set_local_preferences(
            base_url=self.base_url,
            theme_name=self.theme_name,
            status_refresh_seconds=self.status_refresh_seconds,
            alert_refresh_seconds=self.alert_refresh_seconds,
            log_limit=self.log_limit,
            logs_auto_scroll=self.logs_auto_scroll,
        )
        self.logs_page.set_auto_scroll_enabled(self.logs_auto_scroll)

    def _update_connection_badges(self) -> None:
        if self._connection_ok:
            self.connection_badge.setText("CONNECTED")
            self.connection_badge.setStyleSheet(
                "padding: 8px 12px; border-radius: 6px; "
                "background: rgba(78,216,157,0.16); border: 1px solid #4ed89d; color: #4ed89d; "
                "font-family: Consolas; font-size: 11px; font-weight: 700;"
            )
        else:
            self.connection_badge.setText("OFFLINE")
            self.connection_badge.setStyleSheet(
                "padding: 8px 12px; border-radius: 6px; "
                "background: rgba(255,111,134,0.16); border: 1px solid #ff6f86; color: #ff6f86; "
                "font-family: Consolas; font-size: 11px; font-weight: 700;"
            )
    def _set_connection_state(self, connected: bool, detail: str) -> None:
        self._connection_ok = connected
        self._update_connection_badges()
        self.statusBar().showMessage(detail, 5000)

    def _set_sync_label(self, label: str) -> None:
        self.sync_badge.setText(f"SYNC: {label}")

    def _switch_workspace(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.workspace_switcher.set_active(index)
        self._update_workspace_header(index)

    def _on_workspace_changed(self, index: int) -> None:
        self.workspace_switcher.set_active(index)
        self._update_workspace_header(index)
        key = NAV_ITEMS[index][0]
        if key in {"logs", "statistics"}:
            self._load_logs()
        elif key == "settings":
            self.api.get_config()
        elif key == "whitelist":
            self.api.get_whitelist()
        elif key == "alert_center":
            self.alert_center_page.set_alerts(self._latest_alerts)

    def _refresh_all(self) -> None:
        self.api.get_status()
        self.api.get_alerts(limit=120)
        self.api.get_whitelist()
        self.api.get_config()
        self._load_logs()

    def _quick_refresh(self) -> None:
        self.api.get_status()
        self.api.get_alerts(limit=120)
        current_key = NAV_ITEMS[self.stack.currentIndex()][0]
        if current_key in {"logs", "statistics"}:
            self._load_logs()
        elif current_key == "whitelist":
            self.api.get_whitelist()
        elif current_key == "settings":
            self.api.get_config()
        self.statusBar().showMessage("Refreshing active workspace...", 3000)

    def _load_logs(self) -> None:
        self.api.get_log(limit=self.log_limit)

    def _run_scan(self) -> None:
        self.monitor_page.set_action_pending("scan")
        self.monitor_page.set_session_text("Scanning nearby APs...")
        self.monitor_page.append_notice("Scan started. Probing nearby access points...", "info")
        self.statusBar().showMessage("Scanning access points...", 4000)
        self.api.scan()

    def _start_monitor(self) -> None:
        targets = self.monitor_page.selected_targets()
        self._current_scope = f"{len(targets)} selected APs" if targets else "All detected APs"
        self.monitor_page.set_action_pending("start")
        self.dashboard_page.set_status(
            self._status_loaded and self.monitor_page.btn_stop.isEnabled(),
            self.interface_badge.text().replace("IFACE: ", ""),
            self._status_stats(),
            self._current_scope,
        )
        self.monitor_page.set_session_text(f"Starting monitor for {self._current_scope.lower()}...")
        self.monitor_page.append_notice(
            f"Monitor requested for {self._current_scope.lower()}. Waiting for backend confirmation...",
            "info",
        )
        self.api.start_monitor(targets or None)

    def _stop_monitor(self) -> None:
        self.monitor_page.set_action_pending("stop")
        self.monitor_page.append_notice("Stop requested. Waiting for backend confirmation...", "warning")
        self.api.stop_monitor()

    def _clear_monitor_session(self) -> None:
        self.monitor_page.flash_action("clear")
        self._scan_results.clear()
        self._selected_monitor_bssids.clear()
        self._current_scope = "All detected APs"
        self.monitor_page.clear_session()
        self.dashboard_page.set_status(
            False,
            self.interface_badge.text().replace("IFACE: ", ""),
            self._status_stats(),
            self._current_scope,
        )

    def _prefill_whitelist_from_monitor(self, ap: dict) -> None:
        self._switch_workspace(3)
        self.whitelist_page.prefill_from_access_point(ap)

    def _submit_whitelist(self, payload: dict, original_bssid: str) -> None:
        if original_bssid:
            self.api.update_whitelist(original_bssid, payload)
        else:
            self.api.add_whitelist(payload)

    def _save_remote_config(self) -> None:
        payload = self.settings_page.collect_remote_payload()
        self.api.save_config(payload)

    def _apply_local_preferences_from_settings(self) -> None:
        prefs = self.settings_page.collect_local_preferences()
        self.base_url = prefs["base_url"] or DEFAULT_BASE_URL
        self.theme_name = prefs["theme_name"] or DEFAULT_THEME
        self.status_refresh_seconds = prefs["status_refresh_seconds"]
        self.alert_refresh_seconds = prefs["alert_refresh_seconds"]
        self.log_limit = prefs["log_limit"]
        self.logs_auto_scroll = prefs["logs_auto_scroll"]

        self.api.set_base_url(self.base_url)
        self.settings_store.setValue("base_url", self.base_url)
        self.settings_store.setValue("theme_name", self.theme_name)
        self.settings_store.setValue("status_refresh_seconds", self.status_refresh_seconds)
        self.settings_store.setValue("alert_refresh_seconds", self.alert_refresh_seconds)
        self.settings_store.setValue("log_limit", self.log_limit)
        self.settings_store.setValue("logs_auto_scroll", self.logs_auto_scroll)

        self.remote_target_label.setText(f"API TARGET  {self.base_url}")
        self.status_timer.setInterval(max(1, self.status_refresh_seconds) * 1000)
        self.alert_timer.setInterval(max(1, self.alert_refresh_seconds) * 1000)
        self.logs_page.set_auto_scroll_enabled(self.logs_auto_scroll)
        self._apply_styles()
        self.settings_page.mark_local_applied("Local UI settings applied.")
        self._set_connection_state(False, f"Reconnecting to {self.base_url}")
        self.api.get_status()
        self.api.get_alerts(limit=120)

    def _test_connection(self) -> None:
        self._set_connection_state(False, "Testing remote API")
        self.api.get_status()

    def _status_stats(self) -> dict:
        return self._config_cache.get("_last_status_stats", {})

    def _monitor_similarity_threshold(self) -> float:
        return float(self._config_cache.get("ssid_similarity_threshold", 0.85) or 0.85)

    def _scan_suspicious_reasons(self) -> dict[str, str]:
        threshold = self._monitor_similarity_threshold()
        reasons: dict[str, str] = {}
        for ap in self._scan_results:
            ssid = str(ap.get("ssid", "")).strip()
            bssid = str(ap.get("bssid", "")).upper()
            if not ssid or ssid == "<Hidden>":
                continue
            for trusted in self._whitelist_entries:
                trusted_ssid = str(trusted.get("ssid", "")).strip()
                trusted_bssid = str(trusted.get("bssid", "")).upper()
                similarity = SequenceMatcher(None, ssid.lower(), trusted_ssid.lower()).ratio()
                if similarity >= threshold and bssid != trusted_bssid:
                    reasons[bssid] = (
                        f"SSID resembles trusted AP '{trusted_ssid}' ({trusted_bssid}) "
                        f"with similarity {similarity:.2f}."
                    )
                    break
        return reasons

    def _refresh_monitor_table(self) -> None:
        suspicious = self._scan_suspicious_reasons()
        self.monitor_page.set_scan_results(self._scan_results, self._selected_monitor_bssids, suspicious)

    def on_status(self, data: dict) -> None:
        running = bool(data.get("running", False))
        interface = str(data.get("interface", "-"))
        stats = data.get("stats", {}) or {}
        self._config_cache["_last_status_stats"] = stats
        self._status_loaded = True
        self._set_connection_state(True, f"Connected to {self.base_url}")
        self._set_sync_label("status updated")
        self.interface_badge.setText(f"IFACE: {interface}")
        self.remote_target_label.setText(f"API TARGET  {self.base_url}")
        self.monitor_page.set_running(running)
        if self._scan_results:
            self.monitor_page.set_session_text(
                f"{len(self._scan_results)} AP(s) scanned | monitor {'live' if running else 'idle'} on {interface}"
            )
        self.dashboard_page.set_status(running, interface, stats, self._current_scope)
        self._update_workspace_header(self.stack.currentIndex())

    def on_alerts(self, data: dict) -> None:
        self._latest_alerts = data.get("alerts", []) or []
        self.dashboard_page.set_alerts(self._latest_alerts)
        self.alert_center_page.set_alerts(self._latest_alerts)
        self.monitor_page.set_live_alerts(self._latest_alerts)
        self._update_workspace_header(self.stack.currentIndex())

    def on_log(self, data: dict) -> None:
        self._log_alerts = data.get("alerts", []) or []
        self.logs_page.set_logs(self._log_alerts)
        self.stats_page.render(self._log_alerts)
        self._set_connection_state(True, f"Connected to {self.base_url}")

    def on_whitelist(self, data: dict) -> None:
        self._whitelist_entries = data.get("whitelist", []) or []
        self.whitelist_page.set_entries(self._whitelist_entries)
        if self._scan_results:
            self._refresh_monitor_table()

    def on_scan(self, data: dict) -> None:
        self.monitor_page.clear_action_pending("scan")
        self._scan_results = data.get("aps", []) or []
        self._selected_monitor_bssids.clear()
        self._refresh_monitor_table()
        if self._scan_results:
            first = self._scan_results[0]
            self.monitor_page.set_session_text(
                f"Scan completed: {len(self._scan_results)} AP(s) found. Strongest AP: "
                f"{first.get('ssid', '<Hidden>')} ({guess_vendor(str(first.get('bssid', '')))})"
            )
            self.monitor_page.append_notice(
                f"Scan completed. {len(self._scan_results)} AP(s) found. Strongest: "
                f"{first.get('ssid', '<Hidden>')} on channel {first.get('channel', '-')}.",
                "success",
            )
        else:
            self.monitor_page.set_session_text("Scan completed with no AP results.")
            self.monitor_page.append_notice("Scan completed with no AP results.", "warning")
        scan_event = data.get("scan_event")
        if scan_event and NAV_ITEMS[self.stack.currentIndex()][0] in {"logs", "statistics"}:
            self._load_logs()
        self.statusBar().showMessage(f"Scan complete: {len(self._scan_results)} AP(s) found.", 5000)
        self._update_workspace_header(self.stack.currentIndex())

    def on_config(self, data: dict) -> None:
        config = data.get("config", {}) or {}
        last_status = self._config_cache.get("_last_status_stats", {})
        self._config_cache = dict(config)
        if last_status:
            self._config_cache["_last_status_stats"] = last_status
        self.settings_page.set_remote_config(config)
        self.settings_page.set_status_message("Remote config loaded.")
        if self._scan_results:
            self._refresh_monitor_table()

    def on_action_done(self, data: dict) -> None:
        status = data.get("status", "done")
        messages = {
            "started": "Monitoring started.",
            "stopped": "Monitoring stopped.",
            "cleared": "Log cleared.",
            "added": "Whitelist entry added.",
            "updated": "Whitelist entry updated.",
            "deleted": "Whitelist entry deleted.",
            "saved": data.get("message", "Config saved."),
        }
        self.statusBar().showMessage(messages.get(status, "Action completed."), 5000)
        self._set_connection_state(True, f"Connected to {self.base_url}")

        if status == "started":
            self.monitor_page.clear_action_pending("start")
            self.monitor_page.append_notice("Monitoring started successfully.", "success")
            self.api.get_status()
            self.api.get_alerts(limit=120)
        elif status == "stopped":
            self.monitor_page.clear_action_pending("stop")
            self.monitor_page.append_notice("Monitoring stopped.", "warning")
            self.api.get_status()
        elif status == "cleared":
            self.monitor_page.append_notice("Remote log history cleared.", "warning")
            self._log_alerts.clear()
            self.logs_page.set_logs([])
            self.stats_page.render([])
            self.api.get_status()
        elif status in {"added", "updated", "deleted"}:
            self.api.get_whitelist()
        elif status == "saved":
            self.settings_page.mark_remote_saved(data.get("message", "Config saved."))
            self.api.get_config()

    def on_error(self, error: dict) -> None:
        source = error.get("source", "request")
        message = error.get("message", "Unknown error")
        blocking = bool(error.get("blocking", False))

        # Only the status probe should control the global online/offline badge.
        # Other workspace requests can fail independently while the backend is still reachable.
        if source == "status":
            self._set_connection_state(False, f"{source} failed")
        else:
            self.statusBar().showMessage(f"{source}: {message}", 6000)

        if source == "scan":
            self.monitor_page.clear_action_pending("scan")
        elif source == "start_monitor":
            self.monitor_page.clear_action_pending("start")
        elif source == "stop_monitor":
            self.monitor_page.clear_action_pending("stop")

        if blocking:
            QMessageBox.warning(self, "Request failed", message)

    def _update_workspace_header(self, index: int) -> None:
        key, title, subtitle = NAV_ITEMS[index]
        self.setWindowTitle(f"WiFi Security Monitor - {title}")
        self.statusBar().showMessage(subtitle, 2500)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(get_stylesheet(DEFAULT_THEME))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
