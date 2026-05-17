from __future__ import annotations

import html
import json
from typing import Optional

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.utils import alert_severity, alert_summary, alert_title, format_timestamp, guess_vendor
from app.widgets.ap_table import APTable


class MonitorPage(QWidget):
    scan_requested = Signal()
    start_requested = Signal()
    stop_requested = Signal()
    clear_requested = Signal()
    promote_to_whitelist_requested = Signal(dict)

    def __init__(self):
        super().__init__()
        self._scan_results: list[dict] = []
        self._suspicious_reasons: dict[str, str] = {}
        self._live_alerts: list[dict] = []
        self._session_notices: list[tuple[str, str]] = []
        self._pending_action = ""
        self._monitor_live = False

        self._action_flash_timer = QTimer(self)
        self._action_flash_timer.setSingleShot(True)
        self._action_flash_timer.timeout.connect(self._clear_pending_action)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("PageHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(4)
        header_layout.addWidget(self._label("Monitor", "SectionEyebrow"))
        title = QLabel("Airspace Control Console")
        title.setObjectName("PanelTitle")
        subtitle = self._label(
            "Scan nearby APs, choose scope, start monitoring, and watch the live session stream in one workspace.",
            "SectionText",
        )
        subtitle.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        root.addWidget(header)

        controls = QFrame()
        controls.setObjectName("Panel")
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(18, 16, 18, 16)
        controls_layout.setSpacing(12)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        self.btn_scan = QPushButton("Scan APs")
        self.btn_scan.setProperty("variant", "warning")
        self.btn_scan.setProperty("actionButton", True)
        self.btn_scan.clicked.connect(lambda _checked=False: self._trigger_action("scan"))
        self.btn_start = QPushButton("Start Monitor")
        self.btn_start.setProperty("variant", "success")
        self.btn_start.setProperty("actionButton", True)
        self.btn_start.clicked.connect(lambda _checked=False: self._trigger_action("start"))
        self.btn_stop = QPushButton("Stop Monitor")
        self.btn_stop.setProperty("variant", "danger")
        self.btn_stop.setProperty("actionButton", True)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(lambda _checked=False: self._trigger_action("stop"))
        self.btn_clear = QPushButton("Clear Session")
        self.btn_clear.setProperty("variant", "ghost")
        self.btn_clear.setProperty("actionButton", True)
        self.btn_clear.clicked.connect(lambda _checked=False: self._trigger_action("clear"))
        button_row.addWidget(self.btn_scan)
        button_row.addWidget(self.btn_start)
        button_row.addWidget(self.btn_stop)
        button_row.addWidget(self.btn_clear)
        button_row.addStretch(1)
        self.session_chip = self._chip("IDLE")
        self.selected_chip = self._chip("0 SELECTED")
        self.suspicious_chip = self._chip("0 FLAGGED")
        button_row.addWidget(self.session_chip)
        button_row.addWidget(self.selected_chip)
        button_row.addWidget(self.suspicious_chip)
        controls_layout.addLayout(button_row)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter APs by SSID, BSSID, encryption, or vendor")
        self.search_input.textChanged.connect(self._apply_filters)
        self.view_filter = QComboBox()
        self.view_filter.addItem("All APs", "all")
        self.view_filter.addItem("Suspicious only", "suspicious")
        self.view_filter.addItem("Selected only", "selected")
        self.view_filter.currentIndexChanged.connect(self._apply_filters)
        self.session_label = self._label("No scan session yet.", "SectionText")
        filter_row.addWidget(self.search_input, 1)
        filter_row.addWidget(self.view_filter)
        filter_row.addWidget(self.session_label, 1)
        controls_layout.addLayout(filter_row)

        root.addWidget(controls)

        body = QHBoxLayout()
        body.setSpacing(14)

        table_frame = QFrame()
        table_frame.setObjectName("Panel")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(10)
        table_head = QHBoxLayout()
        table_head.setSpacing(10)
        table_head.addWidget(self._label("Airspace Table", "SectionEyebrow"))
        table_head.addStretch(1)
        self.table_count = self._label("0", "SmallMeta")
        table_head.addWidget(self.table_count)
        table_layout.addLayout(table_head)

        self.table_stack = QStackedWidget()
        table_empty = self._empty_panel(
            "No scan results yet",
            "Run Scan APs to build the live airspace table and choose which targets to monitor.",
        )
        self.ap_table = APTable()
        self.ap_table.checked_targets_changed.connect(self._on_checked_targets_changed)
        self.ap_table.current_ap_changed.connect(self._render_current_ap)
        self.table_stack.addWidget(table_empty)
        self.table_stack.addWidget(self.ap_table)
        table_layout.addWidget(self.table_stack, 1)
        body.addWidget(table_frame, 3)

        right_column = QVBoxLayout()
        right_column.setSpacing(14)

        events_frame = QFrame()
        events_frame.setObjectName("Panel")
        events_layout = QVBoxLayout(events_frame)
        events_layout.setContentsMargins(16, 16, 16, 16)
        events_layout.setSpacing(10)
        events_head = QHBoxLayout()
        events_head.setSpacing(10)
        events_head.addWidget(self._label("Live Session Stream", "SectionEyebrow"))
        events_head.addStretch(1)
        self.live_count = self._label("0", "SmallMeta")
        events_head.addWidget(self.live_count)
        events_layout.addLayout(events_head)
        self.live_stack = QStackedWidget()
        live_empty = self._empty_panel(
            "Session stream idle",
            "Start monitor to watch local session notices and live rogue/deauth detections here.",
        )
        self.live_feed = QListWidget()
        self.live_stack.addWidget(live_empty)
        self.live_stack.addWidget(self.live_feed)
        events_layout.addWidget(self.live_stack, 1)
        right_column.addWidget(events_frame, 1)

        profile = QFrame()
        profile.setObjectName("Panel")
        profile_layout = QVBoxLayout(profile)
        profile_layout.setContentsMargins(16, 16, 16, 16)
        profile_layout.setSpacing(12)
        profile_layout.addWidget(self._label("Focused Access Point", "SectionEyebrow"))
        self.detail_stack = QStackedWidget()

        detail_empty = self._empty_panel(
            "Select an AP",
            "AP metadata, RSSI, vendor, and raw payload will appear here after you select a row from the airspace table.",
        )

        detail_view = QWidget()
        detail_view_layout = QVBoxLayout(detail_view)
        detail_view_layout.setContentsMargins(0, 8, 0, 0)
        detail_view_layout.setSpacing(8)
        self.detail_title = QLabel("Select an AP")
        self.detail_title.setStyleSheet("font-size: 20px; font-weight: 800;")
        self.detail_meta = self._label("AP metadata will appear here.", "SectionText")
        self.detail_browser = QTextBrowser()
        self.detail_browser.setMinimumHeight(220)
        detail_view_layout.addWidget(self.detail_title)
        detail_view_layout.addWidget(self.detail_meta)
        detail_view_layout.addWidget(self.detail_browser, 1)

        self.detail_stack.addWidget(detail_empty)
        self.detail_stack.addWidget(detail_view)
        profile_layout.addWidget(self.detail_stack, 1)

        profile_action_row = QHBoxLayout()
        profile_action_row.setSpacing(10)
        profile_action_row.addStretch(1)
        self.btn_trust = QPushButton("Promote to Whitelist")
        self.btn_trust.setProperty("variant", "primary")
        self.btn_trust.setEnabled(False)
        self.btn_trust.setMinimumWidth(220)
        self.btn_trust.clicked.connect(self._emit_whitelist_request)
        profile_action_row.addWidget(self.btn_trust)
        profile_layout.addLayout(profile_action_row)
        right_column.addWidget(profile, 2)

        right_shell = QWidget()
        right_shell.setLayout(right_column)
        right_shell.setMinimumWidth(480)
        body.addWidget(right_shell, 2)
        root.addLayout(body, 1)
        self._render_action_states()

    def set_running(self, running: bool) -> None:
        self._monitor_live = running
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        if running and self._pending_action == "start":
            self._pending_action = ""
        if not running and self._pending_action == "stop":
            self._pending_action = ""
        self.session_chip.setText("LIVE" if running else "READY" if self._scan_results else "IDLE")
        self._render_action_states()

    def set_session_text(self, text: str) -> None:
        self.session_label.setText(text)

    def set_scan_results(
        self,
        aps: list[dict],
        selected_bssids: set[str],
        suspicious_reasons: dict[str, str],
    ) -> None:
        self._scan_results = list(aps)
        self._suspicious_reasons = dict(suspicious_reasons)
        self.ap_table.populate(aps, selected_bssids, suspicious_reasons)
        self.table_stack.setCurrentIndex(1 if aps else 0)
        self._apply_filters()
        self.table_count.setText(str(len(aps)))
        self.suspicious_chip.setText(f"{len(suspicious_reasons)} FLAGGED")
        self.session_chip.setText("READY" if aps else "IDLE")
        self.session_label.setText(f"{len(aps)} AP(s) scanned." if aps else "No scan session yet.")
        self._update_selection_label(self.ap_table.selected_targets())

    def selected_targets(self) -> list[str]:
        return self.ap_table.selected_targets()

    def clear_session(self) -> None:
        self._scan_results.clear()
        self._suspicious_reasons.clear()
        self._live_alerts.clear()
        self._session_notices.clear()
        self._monitor_live = False
        self.ap_table.populate([], set(), {})
        self.table_stack.setCurrentIndex(0)
        self.table_count.setText("0")
        self.session_chip.setText("IDLE")
        self.selected_chip.setText("0 SELECTED")
        self.suspicious_chip.setText("0 FLAGGED")
        self.session_label.setText("Session cleared.")
        self._render_current_ap({})
        self._render_live_alerts()
        self._render_action_states()

    def set_live_alerts(self, alerts: list[dict]) -> None:
        self._live_alerts = list(alerts)
        self._render_live_alerts()

    def set_action_pending(self, action: str) -> None:
        self._pending_action = action
        self._action_flash_timer.stop()
        self._render_action_states()

    def clear_action_pending(self, action: str = "") -> None:
        if not action or self._pending_action == action:
            self._pending_action = ""
            self._action_flash_timer.stop()
            self._render_action_states()

    def flash_action(self, action: str, duration_ms: int = 900) -> None:
        self._pending_action = action
        self._render_action_states()
        self._action_flash_timer.start(duration_ms)

    def append_notice(self, message: str, level: str = "info") -> None:
        self._session_notices.insert(0, (message, level))
        self._session_notices = self._session_notices[:30]
        self._render_live_alerts()

    def _apply_filters(self) -> None:
        self.ap_table.apply_filters(
            self.search_input.text(),
            str(self.view_filter.currentData() or "all"),
        )

    def _on_checked_targets_changed(self, targets: list[str]) -> None:
        self._update_selection_label(targets)

    def _update_selection_label(self, targets: list[str]) -> None:
        self.selected_chip.setText(f"{len(targets)} SELECTED")

    def _render_current_ap(self, ap: Optional[dict]) -> None:
        self.btn_trust.setEnabled(bool(ap))
        if not ap:
            self.detail_stack.setCurrentIndex(0)
            self.detail_title.setText("Select an AP")
            self.detail_meta.setText("AP metadata will appear here.")
            self.detail_browser.setHtml(
                "<div style='color:#8ea8c2;font-family:Consolas;'>No access point selected.</div>"
            )
            return

        self.detail_stack.setCurrentIndex(1)
        bssid = str(ap.get("bssid", "")).upper()
        reason = self._suspicious_reasons.get(bssid, "No suspicion flags for this AP.")
        self.detail_title.setText(str(ap.get("ssid", "<Hidden>") or "<Hidden>"))
        self.detail_meta.setText(f"{bssid} | {guess_vendor(bssid)}")
        raw = html.escape(json.dumps(ap, indent=2, ensure_ascii=False))
        self.detail_browser.setHtml(
            f"""
            <div style="font-family:'Segoe UI'; color:#edf5ff;">
              <div style="margin-bottom:12px; line-height:1.6;">
                <b>Channel</b>: {html.escape(str(ap.get('channel', '-')))}<br>
                <b>Encryption</b>: {html.escape(str(ap.get('encryption', '-')))}<br>
                <b>RSSI</b>: {html.escape(str(ap.get('rssi', '-')))} dBm<br>
                <b>Vendor</b>: {html.escape(guess_vendor(bssid))}<br>
                <b>Assessment</b>: {html.escape(reason)}
              </div>
              <div style="font-size:11px; color:#7f96ad; margin-bottom:6px;">RAW AP PAYLOAD</div>
              <pre style="background:#08111a; border:1px solid #243447; border-radius:8px; padding:12px; color:#dce8f5;">{raw}</pre>
            </div>
            """
        )

    def _emit_whitelist_request(self) -> None:
        ap = self.ap_table.current_ap()
        if ap:
            self.promote_to_whitelist_requested.emit(ap)

    def _trigger_action(self, action: str) -> None:
        if action == "scan":
            self.set_action_pending("scan")
            self.scan_requested.emit()
        elif action == "start":
            self.set_action_pending("start")
            self.start_requested.emit()
        elif action == "stop":
            self.set_action_pending("stop")
            self.stop_requested.emit()
        elif action == "clear":
            self.flash_action("clear")
            self.clear_requested.emit()

    def _render_live_alerts(self) -> None:
        self.live_feed.clear()
        total_events = len(self._session_notices) + len(self._live_alerts)
        self.live_count.setText(str(total_events))
        if not self._live_alerts and not self._session_notices:
            self.live_stack.setCurrentIndex(0)
            self.live_feed.addItem("Monitoring stream is idle. Start monitor to watch live events here.")
            return
        self.live_stack.setCurrentIndex(1)

        for message, level in self._session_notices:
            item = QListWidgetItem(message)
            if level == "critical":
                item.setForeground(QColor("#ff6f86"))
            elif level in {"high", "warning"}:
                item.setForeground(QColor("#ffb454"))
            elif level == "success":
                item.setForeground(QColor("#42d69d"))
            else:
                item.setForeground(QColor("#6db9ff"))
            self.live_feed.addItem(item)

        for alert in self._live_alerts[:30]:
            item = QListWidgetItem(
                f"{format_timestamp(str(alert.get('timestamp', '')))} | {alert_title(alert)}\n{alert_summary(alert)}"
            )
            severity = alert_severity(alert)
            if severity == "critical":
                item.setForeground(QColor("#ff6f86"))
            elif severity in {"high", "medium"}:
                item.setForeground(QColor("#ffb454"))
            else:
                item.setForeground(QColor("#6db9ff"))
            self.live_feed.addItem(item)

    @staticmethod
    def _label(text: str, name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(name)
        return label

    def _empty_panel(self, title: str, text: str) -> QWidget:
        frame = QFrame()
        frame.setObjectName("HeroPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 18px; font-weight: 800;")
        caption = self._label(text, "SectionText")
        caption.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(caption)
        layout.addStretch(1)
        return frame

    def _clear_pending_action(self) -> None:
        self._pending_action = ""
        self._render_action_states()

    def _render_action_states(self) -> None:
        active_map = {
            "scan": self._pending_action == "scan",
            "start": self._monitor_live or self._pending_action == "start",
            "stop": self._pending_action == "stop",
            "clear": self._pending_action == "clear",
        }
        for key, button in {
            "scan": self.btn_scan,
            "start": self.btn_start,
            "stop": self.btn_stop,
            "clear": self.btn_clear,
        }.items():
            button.setProperty("activeState", "active" if active_map[key] else "idle")
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    @staticmethod
    def _chip(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("StatusPill")
        return label
