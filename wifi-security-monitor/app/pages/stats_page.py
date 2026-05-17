from __future__ import annotations

import html
from collections import Counter, defaultdict
from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.utils import alert_severity, alert_title, format_timestamp
from app.widgets.stat_card import StatCard


class StatsPage(QWidget):
    refresh_requested = Signal()

    def __init__(self):
        super().__init__()
        self._alerts: list[dict] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("PageHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(12)
        left = QVBoxLayout()
        left.setSpacing(4)
        left.addWidget(self._label("Statistics", "SectionEyebrow"))
        title = QLabel("Operational Trend Summary")
        title.setObjectName("PanelTitle")
        subtitle = self._label(
            "Recent volume, event mix, and targeted devices rendered for a quick operational review.",
            "SectionText",
        )
        subtitle.setWordWrap(True)
        left.addWidget(title)
        left.addWidget(subtitle)
        header_layout.addLayout(left, 1)
        self.refresh_button = QPushButton("Refresh Statistics")
        self.refresh_button.setProperty("variant", "primary")
        self.refresh_button.clicked.connect(lambda _checked=False: self.refresh_requested.emit())
        header_layout.addWidget(self.refresh_button)
        root.addWidget(header)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(14)
        metrics.setVerticalSpacing(14)
        self.total_card = StatCard("Total Events", "#6db9ff")
        self.rogue_card = StatCard("Rogue Alerts", "#ff935d")
        self.deauth_card = StatCard("Deauth Alerts", "#ffb454")
        self.scan_card = StatCard("Scan Sessions", "#42d69d")
        metrics.addWidget(self.total_card, 0, 0)
        metrics.addWidget(self.rogue_card, 0, 1)
        metrics.addWidget(self.deauth_card, 0, 2)
        metrics.addWidget(self.scan_card, 0, 3)
        root.addLayout(metrics)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        self.hourly_panel = self._panel("24H Activity")
        self.breakdown_panel = self._panel("Event Breakdown")
        self.top_bssid_panel = self._panel("Top Detected BSSIDs")
        self.severity_panel = self._panel("Severity Mix")

        grid.addWidget(self.hourly_panel[0], 0, 0)
        grid.addWidget(self.breakdown_panel[0], 0, 1)
        grid.addWidget(self.top_bssid_panel[0], 1, 0)
        grid.addWidget(self.severity_panel[0], 1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        root.addLayout(grid, 1)

        self.render([])

    def render(self, alerts: list[dict]) -> None:
        self._alerts = list(alerts)
        total = len(alerts)
        rogue = sum(1 for alert in alerts if alert.get("event_type") == "rogue_ap_detected")
        deauth = sum(1 for alert in alerts if alert.get("event_type") == "deauth_attack_detected")
        scans = sum(1 for alert in alerts if alert.get("event_type") == "scan_completed")

        self.total_card.set_value(total, "Events loaded from JSONL history")
        self.rogue_card.set_value(rogue, "Rogue AP detections")
        self.deauth_card.set_value(deauth, "Deauth detections")
        self.scan_card.set_value(scans, "Completed scan sessions")

        hourly = defaultdict(Counter)
        event_counts = Counter()
        severity_counts = Counter()
        bssid_counts = Counter()

        for alert in alerts:
            event_type = str(alert.get("event_type", "unknown"))
            event_counts[event_type] += 1
            severity_counts[alert_severity(alert)] += 1

            hour_key = "Unknown"
            timestamp = str(alert.get("timestamp", ""))
            if timestamp:
                try:
                    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    hour_key = parsed.strftime("%H:00")
                except Exception:
                    hour_key = format_timestamp(timestamp)[:13]
            hourly[hour_key][event_type] += 1

            target_bssid = (
                alert.get("detected_bssid")
                or alert.get("target_bssid")
                or alert.get("legit_bssid")
                or ""
            )
            if target_bssid:
                bssid_counts[str(target_bssid).upper()] += 1

        hourly_rows = []
        for hour in sorted(hourly.keys())[-12:]:
            counts = hourly[hour]
            hourly_rows.append(
                f"<tr><td>{html.escape(hour)}</td><td>{counts.get('rogue_ap_detected', 0)}</td>"
                f"<td>{counts.get('deauth_attack_detected', 0)}</td><td>{counts.get('scan_completed', 0)}</td></tr>"
            )
        if not hourly_rows:
            hourly_rows.append("<tr><td colspan='4'>No hourly data yet.</td></tr>")
        self.hourly_panel[1].setHtml(
            "<table width='100%' style='font-family:Consolas;'>"
            "<tr><th align='left'>Hour</th><th align='left'>Rogue</th><th align='left'>Deauth</th><th align='left'>Scans</th></tr>"
            + "".join(hourly_rows)
            + "</table>"
        )

        breakdown_rows = []
        for event_type, count in event_counts.most_common():
            breakdown_rows.append(
                f"<div style='margin-bottom:10px;'><b>{html.escape(alert_title({'event_type': event_type}))}</b>"
                f"<div style='margin-top:4px; background:#08111a; border:1px solid #243447; border-radius:999px;'>"
                f"<div style='height:10px; width:{(count / max(total, 1)) * 100:.0f}%; background:#59b8ff; border-radius:999px;'></div>"
                f"</div><div style='margin-top:4px; color:#97adc4;'>{count} event(s)</div></div>"
            )
        if not breakdown_rows:
            breakdown_rows.append("<div>No event breakdown available yet.</div>")
        self.breakdown_panel[1].setHtml("".join(breakdown_rows))

        top_rows = []
        for bssid, count in bssid_counts.most_common(5):
            top_rows.append(f"<div><code>{html.escape(bssid)}</code> <b style='color:#ffb454;'>{count}</b></div>")
        if not top_rows:
            top_rows.append("<div>No targeted BSSID telemetry yet.</div>")
        self.top_bssid_panel[1].setHtml("".join(top_rows))

        severity_rows = []
        for severity, count in severity_counts.most_common():
            width = (count / max(total, 1)) * 100
            color = "#ff6f86" if severity == "critical" else "#ffb454" if severity in {"high", "medium"} else "#6db9ff"
            severity_rows.append(
                f"<div style='margin-bottom:10px;'><b>{html.escape(severity.upper())}</b>"
                f"<div style='margin-top:4px; background:#08111a; border:1px solid #243447; border-radius:999px;'>"
                f"<div style='height:10px; width:{width:.0f}%; background:{color}; border-radius:999px;'></div>"
                f"</div><div style='margin-top:4px; color:#97adc4;'>{count} event(s)</div></div>"
            )
        if not severity_rows:
            severity_rows.append("<div>No severity mix available yet.</div>")
        self.severity_panel[1].setHtml("".join(severity_rows))

    @staticmethod
    def _label(text: str, name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(name)
        return label

    @staticmethod
    def _panel(title: str) -> tuple[QFrame, QTextBrowser]:
        frame = QFrame()
        frame.setObjectName("Panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        eyebrow = QLabel(title)
        eyebrow.setObjectName("SectionEyebrow")
        browser = QTextBrowser()
        browser.setMinimumHeight(180)
        layout.addWidget(eyebrow)
        layout.addWidget(browser, 1)
        return frame, browser
