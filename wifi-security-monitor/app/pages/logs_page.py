from __future__ import annotations

import html
import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.utils import alert_details_html, alert_reason, alert_severity, alert_title, format_timestamp


class LogsPage(QWidget):
    refresh_requested = Signal()
    clear_requested = Signal()

    def __init__(self):
        super().__init__()
        self._alerts: list[dict] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("PageHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(4)
        header_layout.addWidget(self._label("Logs", "SectionEyebrow"))
        title = QLabel("Forensic Event History")
        title.setObjectName("PanelTitle")
        subtitle = self._label(
            "Search the raw JSONL history, filter by severity or event type, and inspect the selected entry in detail.",
            "SectionText",
        )
        subtitle.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        root.addWidget(header)

        toolbar = QFrame()
        toolbar.setObjectName("Panel")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 14, 16, 14)
        toolbar_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search raw JSON, SSID, BSSID, or message")
        self.search_input.textChanged.connect(self._render)

        self.severity_filter = QComboBox()
        self.severity_filter.addItem("All severities", "")
        self.severity_filter.addItem("Critical", "critical")
        self.severity_filter.addItem("High", "high")
        self.severity_filter.addItem("Medium", "medium")
        self.severity_filter.addItem("Info", "info")
        self.severity_filter.currentIndexChanged.connect(self._render)

        self.type_filter = QComboBox()
        self.type_filter.addItem("All events", "")
        self.type_filter.addItem("Rogue AP", "rogue_ap_detected")
        self.type_filter.addItem("Deauth Attack", "deauth_attack_detected")
        self.type_filter.addItem("Scan Sessions", "scan_completed")
        self.type_filter.currentIndexChanged.connect(self._render)

        self.auto_scroll = QCheckBox("Auto-select newest")
        self.auto_scroll.setChecked(True)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setProperty("variant", "primary")
        self.btn_refresh.clicked.connect(lambda _checked=False: self.refresh_requested.emit())
        self.btn_export = QPushButton("Export Logs")
        self.btn_export.setProperty("variant", "warning")
        self.btn_export.clicked.connect(self._export_logs)
        self.btn_clear = QPushButton("Clear Logs")
        self.btn_clear.setProperty("variant", "danger")
        self.btn_clear.clicked.connect(self._confirm_clear)
        self.count_label = self._label("0 entries", "SmallMeta")

        toolbar_layout.addWidget(self.search_input, 1)
        toolbar_layout.addWidget(self.severity_filter)
        toolbar_layout.addWidget(self.type_filter)
        toolbar_layout.addWidget(self.auto_scroll)
        toolbar_layout.addWidget(self.btn_refresh)
        toolbar_layout.addWidget(self.btn_export)
        toolbar_layout.addWidget(self.btn_clear)
        toolbar_layout.addWidget(self.count_label)
        root.addWidget(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        list_frame = QFrame()
        list_frame.setObjectName("Panel")
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(14, 14, 14, 14)
        list_layout.setSpacing(10)
        list_layout.addWidget(self._label("History Stream", "SectionEyebrow"))
        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self._show_selected)
        list_layout.addWidget(self.list_widget)
        splitter.addWidget(list_frame)

        detail_frame = QFrame()
        detail_frame.setObjectName("Panel")
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(16, 14, 16, 14)
        detail_layout.setSpacing(8)
        detail_layout.addWidget(self._label("Entry Detail", "SectionEyebrow"))
        self.detail_title = QLabel("Select a log entry")
        self.detail_title.setStyleSheet("font-size: 20px; font-weight: 800;")
        self.detail_meta = self._label("Raw JSON and derived fields will appear here.", "SectionText")
        self.detail_browser = QTextBrowser()
        detail_layout.addWidget(self.detail_title)
        detail_layout.addWidget(self.detail_meta)
        detail_layout.addWidget(self.detail_browser, 1)
        splitter.addWidget(detail_frame)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter, 1)

        self._render()

    def set_logs(self, alerts: list[dict]) -> None:
        self._alerts = list(alerts)
        self._render()

    def set_auto_scroll_enabled(self, enabled: bool) -> None:
        self.auto_scroll.setChecked(enabled)

    def filtered_logs(self) -> list[dict]:
        needle = self.search_input.text().strip().lower()
        severity = self.severity_filter.currentData() or ""
        event_type = self.type_filter.currentData() or ""
        filtered: list[dict] = []
        for alert in self._alerts:
            if severity and alert_severity(alert) != severity:
                continue
            if event_type and alert.get("event_type") != event_type:
                continue
            payload = json.dumps(alert, ensure_ascii=False).lower()
            if needle and needle not in payload:
                continue
            filtered.append(alert)
        return filtered

    def _render(self) -> None:
        alerts = self.filtered_logs()
        self.count_label.setText(f"{len(alerts)} entr{'y' if len(alerts) == 1 else 'ies'}")
        self.list_widget.clear()

        if not alerts:
            self.detail_title.setText("No log entries")
            self.detail_meta.setText("No entries match the current filters.")
            self.detail_browser.setHtml(
                "<div style='font-family:Consolas; color:#8ea8c2;'>"
                "No log entries match the current filters.<br><br>"
                "Scan sessions create <code>scan_completed</code> events, while monitor detections create "
                "rogue AP and deauth events."
                "</div>"
            )
            return

        for alert in alerts:
            item = QListWidgetItem(
                f"{format_timestamp(str(alert.get('timestamp', '')))} | "
                f"{alert_severity(alert).upper()} | {alert_title(alert)}"
            )
            item.setData(Qt.ItemDataRole.UserRole, alert)
            item.setForeground(
                QColor(
                    "#ff6f86"
                    if alert_severity(alert) == "critical"
                    else "#ffb454"
                    if alert_severity(alert) in {"high", "medium"}
                    else "#6db9ff"
                )
            )
            self.list_widget.addItem(item)

        if self.auto_scroll.isChecked() and self.list_widget.count():
            self.list_widget.setCurrentRow(0)
        else:
            self._show_selected()

    def _show_selected(self) -> None:
        current = self.list_widget.currentItem()
        alert = current.data(Qt.ItemDataRole.UserRole) if current else None
        if not alert:
            return
        self.detail_title.setText(alert_title(alert))
        self.detail_meta.setText(
            f"{format_timestamp(str(alert.get('timestamp', '')))} | severity {alert_severity(alert).upper()}"
        )
        raw = html.escape(json.dumps(alert, indent=2, ensure_ascii=False))
        self.detail_browser.setHtml(
            f"""
            <div style="font-family:'Segoe UI'; color:#e8f2fd;">
              <div style="color:#97adc4; margin-bottom:12px;">{html.escape(alert_reason(alert))}</div>
              <div style="line-height:1.6; margin-bottom:14px;">{alert_details_html(alert)}</div>
              <div style="font-size:11px; color:#7f96ad; margin-bottom:6px;">RAW JSON</div>
              <pre style="background:#08111a; border:1px solid #243447; border-radius:8px; padding:12px; color:#dce9f5;">{raw}</pre>
            </div>
            """
        )

    def _export_logs(self) -> None:
        alerts = self.filtered_logs()
        if not alerts:
            QMessageBox.information(self, "No logs", "There are no filtered log entries to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            "wifi-security-logs.jsonl",
            "JSONL Files (*.jsonl);;All Files (*)",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as handle:
            for alert in alerts:
                handle.write(json.dumps(alert, ensure_ascii=False) + "\n")

    def _confirm_clear(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Clear logs",
            "Delete the current log history from the backend log file?",
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.clear_requested.emit()

    @staticmethod
    def _label(text: str, name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(name)
        return label
