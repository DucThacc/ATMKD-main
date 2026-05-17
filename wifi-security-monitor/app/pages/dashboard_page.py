from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.utils import (
    alert_reason,
    alert_severity,
    alert_summary,
    alert_title,
    format_timestamp,
)
from app.widgets.stat_card import StatCard


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self._running = False
        self._interface = "-"
        self._scope = "All detected APs"
        self._stats: dict = {}
        self._alerts: list[dict] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("PageHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(4)
        header_layout.addWidget(self._label("Dashboard", "SectionEyebrow"))
        title = QLabel("Executive SOC Snapshot")
        title.setObjectName("PanelTitle")
        subtitle = self._label(
            "Live mission state, last incident, and core telemetry without the investigation noise.",
            "SectionText",
        )
        subtitle.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        root.addWidget(header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        self.mission_frame = QFrame()
        self.mission_frame.setObjectName("Panel")
        mission_layout = QVBoxLayout(self.mission_frame)
        mission_layout.setContentsMargins(20, 18, 20, 18)
        mission_layout.setSpacing(10)
        mission_layout.addWidget(self._label("Mission State", "SectionEyebrow"))
        self.live_value = QLabel("IDLE")
        self.live_value.setStyleSheet("font-size: 38px; font-weight: 800;")
        self.live_meta = self._label("Ready to monitor.", "SectionText")
        self.live_scope = self._label("Scope: All detected APs", "SectionText")
        self.live_runtime = self._label("Live telemetry summary will appear here.", "SectionText")
        self.live_runtime.setWordWrap(True)
        mission_layout.addWidget(self.live_value)
        mission_layout.addWidget(self.live_meta)
        mission_layout.addWidget(self.live_scope)
        mission_layout.addWidget(self.live_runtime)
        mission_layout.addStretch(1)

        self.card_beacons = StatCard("Beacon Frames", "#59b8ff")
        self.card_deauth = StatCard("Deauth Frames", "#ffb454")
        self.card_alerts = StatCard("Alerts Raised", "#ff6f86")
        self.card_rogue = StatCard("Rogue AP Alerts", "#ff935d")

        self.incident_frame = QFrame()
        self.incident_frame.setObjectName("Panel")
        incident_layout = QVBoxLayout(self.incident_frame)
        incident_layout.setContentsMargins(20, 18, 20, 18)
        incident_layout.setSpacing(8)
        incident_layout.addWidget(self._label("Last Incident", "SectionEyebrow"))
        self.last_incident_title = QLabel("No incidents captured")
        self.last_incident_title.setStyleSheet("font-size: 24px; font-weight: 800;")
        self.last_incident_meta = self._label("Waiting for the alert stream", "SectionText")
        self.last_incident_reason = self._label(
            "The most recent rogue AP or deauth incident will appear here as soon as monitoring catches it.",
            "SectionText",
        )
        self.last_incident_reason.setWordWrap(True)
        incident_layout.addWidget(self.last_incident_title)
        incident_layout.addWidget(self.last_incident_meta)
        incident_layout.addWidget(self.last_incident_reason)
        incident_layout.addStretch(1)

        self.stream_frame = QFrame()
        self.stream_frame.setObjectName("Panel")
        stream_layout = QVBoxLayout(self.stream_frame)
        stream_layout.setContentsMargins(18, 18, 18, 18)
        stream_layout.setSpacing(10)
        head = QHBoxLayout()
        head.setSpacing(10)
        head.addWidget(self._label("Signal Stream", "SectionEyebrow"))
        head.addStretch(1)
        self.stream_count = self._label("0 live entries", "SmallMeta")
        head.addWidget(self.stream_count)
        stream_layout.addLayout(head)
        self.stream_list = QListWidget()
        self.stream_list.setMinimumHeight(220)
        stream_layout.addWidget(self.stream_list)

        grid.addWidget(self.mission_frame, 0, 0, 1, 2)
        grid.addWidget(self.card_beacons, 0, 2)
        grid.addWidget(self.card_deauth, 0, 3)
        grid.addWidget(self.incident_frame, 1, 0, 1, 2)
        grid.addWidget(self.card_alerts, 1, 2)
        grid.addWidget(self.card_rogue, 1, 3)
        grid.addWidget(self.stream_frame, 2, 0, 1, 4)

        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        grid.setRowStretch(2, 1)
        root.addLayout(grid, 1)

    def set_status(self, running: bool, interface: str, stats: dict, scope: str) -> None:
        self._running = running
        self._interface = interface
        self._stats = dict(stats)
        self._scope = scope
        self._render()

    def set_alerts(self, alerts: list[dict]) -> None:
        self._alerts = list(alerts)
        self._render()

    def _render(self) -> None:
        total_beacons = int(self._stats.get("total_beacons", 0) or 0)
        total_deauths = int(self._stats.get("total_deauths", 0) or 0)
        total_alerts = int(self._stats.get("total_alerts", 0) or 0)
        rogue_alerts = sum(
            1 for alert in self._alerts if alert.get("event_type") == "rogue_ap_detected"
        )

        self.live_value.setText("LIVE" if self._running else "IDLE")
        self.live_value.setStyleSheet(
            f"font-size: 38px; font-weight: 800; color: {'#42d69d' if self._running else '#8aa0b7'};"
        )
        self.live_meta.setText(
            f"{'Monitoring active' if self._running else 'Ready to monitor'} on {self._interface}"
        )
        self.live_scope.setText(f"Scope: {self._scope}")
        self.live_runtime.setText(
            f"{total_alerts} alert(s) emitted in the active session. "
            f"{'Live collection is running now.' if self._running else 'No active monitoring session at the moment.'}"
        )

        self.card_beacons.set_value(total_beacons, "Beacon telemetry captured")
        self.card_deauth.set_value(total_deauths, "Deauth frames observed")
        self.card_alerts.set_value(total_alerts, "Alerts emitted in active session")
        self.card_rogue.set_value(rogue_alerts, "Rogue incidents held in memory")

        latest = self._alerts[0] if self._alerts else None
        if latest:
            self.last_incident_title.setText(alert_title(latest))
            self.last_incident_meta.setText(
                f"{format_timestamp(str(latest.get('timestamp', '')))} | severity {alert_severity(latest).upper()}"
            )
            self.last_incident_reason.setText(alert_reason(latest))
        else:
            self.last_incident_title.setText("No incidents captured")
            self.last_incident_meta.setText("Waiting for the alert stream")
            self.last_incident_reason.setText(
                "The most recent rogue AP or deauth incident will appear here as soon as monitoring catches it."
            )

        self.stream_list.clear()
        self.stream_count.setText(f"{len(self._alerts[:8])} live entr{'y' if len(self._alerts[:8]) == 1 else 'ies'}")
        if not self._alerts:
            self.stream_list.addItem("No live alerts yet.")
            return

        for alert in self._alerts[:8]:
            item = QListWidgetItem(
                f"{format_timestamp(str(alert.get('timestamp', '')))} | {alert_title(alert)}\n{alert_summary(alert)}"
            )
            severity = alert_severity(alert)
            item.setForeground(
                QColor(
                    "#ff6f86"
                    if severity == "critical"
                    else "#ffb454"
                    if severity in {"high", "medium"}
                    else "#6db9ff"
                )
            )
            self.stream_list.addItem(item)

    @staticmethod
    def _label(text: str, name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(name)
        return label
