from __future__ import annotations

import html
import json
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.utils import (
    alert_details_html,
    alert_key,
    alert_reason,
    alert_severity,
    alert_title,
    format_timestamp,
)
from app.widgets.alert_card import AlertCard


class AlertCenterPage(QWidget):
    def __init__(self):
        super().__init__()
        self._alerts: list[dict] = []
        self._selected_key: Optional[str] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("PageHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(4)
        header_layout.addWidget(self._label("Alert Center", "SectionEyebrow"))
        title = QLabel("Incident Investigation Board")
        title.setObjectName("PanelTitle")
        subtitle = self._label(
            "Filter live detections, drill into a selected incident, and inspect the raw payload beside its timeline.",
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
        self.search_input.setPlaceholderText("Search by SSID, BSSID, source MAC, or raw JSON")
        self.search_input.textChanged.connect(self._render)

        self.severity_filter = QComboBox()
        self.severity_filter.addItem("All severities", "")
        self.severity_filter.addItem("Critical", "critical")
        self.severity_filter.addItem("High", "high")
        self.severity_filter.addItem("Medium", "medium")
        self.severity_filter.addItem("Info", "info")
        self.severity_filter.currentIndexChanged.connect(self._render)

        self.type_filter = QComboBox()
        self.type_filter.addItem("All event types", "")
        self.type_filter.addItem("Rogue AP", "rogue_ap_detected")
        self.type_filter.addItem("Deauth Attack", "deauth_attack_detected")
        self.type_filter.addItem("Scan Sessions", "scan_completed")
        self.type_filter.currentIndexChanged.connect(self._render)

        self.total_chip = self._chip("0 INCIDENTS")
        self.rogue_chip = self._chip("0 ROGUE")
        self.deauth_chip = self._chip("0 DEAUTH")

        toolbar_layout.addWidget(self.search_input, 1)
        toolbar_layout.addWidget(self.severity_filter)
        toolbar_layout.addWidget(self.type_filter)
        toolbar_layout.addWidget(self.total_chip)
        toolbar_layout.addWidget(self.rogue_chip)
        toolbar_layout.addWidget(self.deauth_chip)
        root.addWidget(toolbar)

        body = QSplitter(Qt.Orientation.Horizontal)

        queue_frame = QFrame()
        queue_frame.setObjectName("Panel")
        queue_layout = QVBoxLayout(queue_frame)
        queue_layout.setContentsMargins(16, 16, 16, 16)
        queue_layout.setSpacing(10)
        queue_layout.addWidget(self._label("Incident Queue", "SectionEyebrow"))

        self.feed_scroll = QScrollArea()
        self.feed_scroll.setWidgetResizable(True)
        self.feed_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.feed_container = QWidget()
        self.feed_content = QVBoxLayout(self.feed_container)
        self.feed_content.setContentsMargins(0, 0, 0, 0)
        self.feed_content.setSpacing(8)
        self.feed_scroll.setWidget(self.feed_container)
        queue_layout.addWidget(self.feed_scroll, 1)
        body.addWidget(queue_frame)

        detail_split = QSplitter(Qt.Orientation.Vertical)

        detail_frame = QFrame()
        detail_frame.setObjectName("Panel")
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(10)
        detail_layout.addWidget(self._label("Selected Incident", "SectionEyebrow"))
        self.detail_title = QLabel("Select an alert")
        self.detail_title.setStyleSheet("font-size: 28px; font-weight: 800;")
        self.detail_meta = self._label("Detailed telemetry will appear here.", "SectionText")
        self.detail_reason = self._label("", "SectionText")
        self.detail_reason.setWordWrap(True)
        self.detail_browser = QTextBrowser()
        detail_layout.addWidget(self.detail_title)
        detail_layout.addWidget(self.detail_meta)
        detail_layout.addWidget(self.detail_reason)
        detail_layout.addWidget(self.detail_browser, 1)
        detail_split.addWidget(detail_frame)

        lower = QSplitter(Qt.Orientation.Horizontal)

        timeline_frame = QFrame()
        timeline_frame.setObjectName("Panel")
        timeline_layout = QVBoxLayout(timeline_frame)
        timeline_layout.setContentsMargins(14, 14, 14, 14)
        timeline_layout.setSpacing(10)
        timeline_layout.addWidget(self._label("Timeline", "SectionEyebrow"))
        self.timeline_list = QListWidget()
        self.timeline_list.itemSelectionChanged.connect(self._on_timeline_selected)
        timeline_layout.addWidget(self.timeline_list)
        lower.addWidget(timeline_frame)

        raw_frame = QFrame()
        raw_frame.setObjectName("Panel")
        raw_layout = QVBoxLayout(raw_frame)
        raw_layout.setContentsMargins(14, 14, 14, 14)
        raw_layout.setSpacing(10)
        raw_layout.addWidget(self._label("Technical Payload", "SectionEyebrow"))
        self.raw_browser = QTextBrowser()
        raw_layout.addWidget(self.raw_browser)
        lower.addWidget(raw_frame)

        lower.setStretchFactor(0, 1)
        lower.setStretchFactor(1, 2)
        detail_split.addWidget(lower)
        detail_split.setStretchFactor(0, 3)
        detail_split.setStretchFactor(1, 2)
        body.addWidget(detail_split)

        body.setStretchFactor(0, 2)
        body.setStretchFactor(1, 3)
        root.addWidget(body, 1)

        self._render()

    def set_alerts(self, alerts: list[dict]) -> None:
        self._alerts = list(alerts)
        self._render()

    def _filtered_alerts(self) -> list[dict]:
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
        alerts = self._filtered_alerts()
        self.total_chip.setText(f"{len(alerts)} INCIDENTS")
        self.rogue_chip.setText(
            f"{sum(1 for alert in alerts if alert.get('event_type') == 'rogue_ap_detected')} ROGUE"
        )
        self.deauth_chip.setText(
            f"{sum(1 for alert in alerts if alert.get('event_type') == 'deauth_attack_detected')} DEAUTH"
        )

        while self.feed_content.count():
            item = self.feed_content.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not alerts:
            empty = self._label("No incidents match the current filters.", "EmptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumHeight(220)
            self.feed_content.addWidget(empty)
            self.feed_content.addStretch(1)
            self.timeline_list.clear()
            self._show_alert(None)
            return

        for alert in alerts:
            card = AlertCard(alert)
            card.set_active(alert_key(alert) == self._selected_key)
            card.activated.connect(self._show_alert)
            self.feed_content.addWidget(card)
        self.feed_content.addStretch(1)

        self.timeline_list.blockSignals(True)
        self.timeline_list.clear()
        for alert in alerts:
            item = QListWidgetItem(
                f"{format_timestamp(str(alert.get('timestamp', '')))} | "
                f"{alert_severity(alert).upper()} | {alert_title(alert)}"
            )
            item.setData(Qt.ItemDataRole.UserRole, alert)
            self.timeline_list.addItem(item)
            if alert_key(alert) == self._selected_key:
                item.setSelected(True)
        self.timeline_list.blockSignals(False)

        target = None
        if self._selected_key:
            target = next((alert for alert in alerts if alert_key(alert) == self._selected_key), None)
        if target is None:
            target = alerts[0]
        self._show_alert(target)

    def _show_alert(self, alert: Optional[dict]) -> None:
        self._selected_key = alert_key(alert) if alert else None
        if alert is None:
            self.detail_title.setText("Select an alert")
            self.detail_meta.setText("Detailed telemetry will appear here.")
            self.detail_reason.setText("")
            self.detail_browser.setHtml(
                "<div style='color:#8ea8c2;font-family:Consolas;'>No alert selected.</div>"
            )
            self.raw_browser.setHtml(
                "<div style='color:#8ea8c2;font-family:Consolas;'>No raw payload selected.</div>"
            )
            return

        self.detail_title.setText(alert_title(alert))
        self.detail_meta.setText(
            f"{format_timestamp(str(alert.get('timestamp', '')))} | severity {alert_severity(alert).upper()}"
        )
        self.detail_reason.setText(alert_reason(alert))
        raw = html.escape(json.dumps(alert, indent=2, ensure_ascii=False))
        self.detail_browser.setHtml(
            f"<div style=\"font-family:'Segoe UI'; color:#edf5ff; line-height:1.65;\">{alert_details_html(alert)}</div>"
        )
        self.raw_browser.setHtml(
            f"""
            <div style="font-size:11px; color:#edf5ff; font-family:Consolas, monospace;">
              <pre style="background:#08111a; border:1px solid #243447; border-radius:8px; padding:12px; color:#dce8f5;">{raw}</pre>
            </div>
            """
        )
        self._render_selection_state()

    def _render_selection_state(self) -> None:
        for index in range(self.timeline_list.count()):
            item = self.timeline_list.item(index)
            alert = item.data(Qt.ItemDataRole.UserRole)
            item.setSelected(alert_key(alert) == self._selected_key)
        for i in range(self.feed_content.count()):
            widget = self.feed_content.itemAt(i).widget()
            if isinstance(widget, AlertCard):
                widget.set_active(alert_key(widget.alert) == self._selected_key)

    def _on_timeline_selected(self) -> None:
        selected = self.timeline_list.selectedItems()
        if not selected:
            return
        alert = selected[0].data(Qt.ItemDataRole.UserRole)
        self._show_alert(alert)

    @staticmethod
    def _label(text: str, name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(name)
        return label

    @staticmethod
    def _chip(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("StatusPill")
        return label
