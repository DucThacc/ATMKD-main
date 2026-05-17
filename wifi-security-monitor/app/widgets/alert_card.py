from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from app.utils import (
    alert_details_html,
    alert_reason,
    alert_severity,
    alert_summary,
    alert_title,
    event_icon,
    format_timestamp,
    severity_color,
)


class AlertCard(QFrame):
    activated = Signal(dict)

    def __init__(self, alert: dict):
        super().__init__()
        self.alert = alert
        self._active = False
        self._severity = alert_severity(alert)
        self._accent = severity_color(self._severity)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("AlertTile")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)

        self.icon_label = QLabel(event_icon(str(alert.get("event_type", ""))))
        self.icon_label.setObjectName("CardEyebrow")

        self.title_label = QLabel(alert_title(alert))
        self.title_label.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {self._accent};")

        self.badge = QLabel(self._severity.upper())
        self.badge.setObjectName("StatusPill")
        self.badge.setStyleSheet(
            f"padding: 4px 10px; border-radius: 999px; "
            f"background: {self._accent}33; border: 1px solid {self._accent}; color: {self._accent};"
        )

        self.timestamp_label = QLabel(format_timestamp(str(alert.get("timestamp", ""))))
        self.timestamp_label.setObjectName("SmallMeta")

        header.addWidget(self.icon_label)
        header.addWidget(self.title_label)
        header.addWidget(self.badge)
        header.addStretch(1)
        header.addWidget(self.timestamp_label)

        self.summary_label = QLabel(alert_summary(alert))
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-weight: 600;")

        self.reason_label = QLabel(alert_reason(alert))
        self.reason_label.setWordWrap(True)
        self.reason_label.setObjectName("SectionText")

        self.details_label = QLabel(alert_details_html(alert))
        self.details_label.setWordWrap(True)
        self.details_label.setTextFormat(Qt.TextFormat.RichText)
        self.details_label.setVisible(False)
        self.details_label.setStyleSheet("color: #cfe2f5;")

        layout.addLayout(header)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.reason_label)
        layout.addWidget(self.details_label)

        self._apply_style()
        self._fade_in()

    def _fade_in(self) -> None:
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0.0)
        self.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(220)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        self._animation = animation

    def _apply_style(self) -> None:
        border = self._accent if self._active else "#243447"
        background = "#182433" if self._active else "#101922"
        self.setStyleSheet(
            f"""
            QFrame#AlertTile {{
                background: {background};
                border: 1px solid {border};
                border-left: 3px solid {self._accent};
                border-radius: 8px;
            }}
            QFrame#AlertTile:hover {{
                border-color: {self._accent};
                background: #152232;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            """
        )

    def set_active(self, active: bool) -> None:
        self._active = active
        self.details_label.setVisible(active)
        self._apply_style()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self.alert)
        super().mousePressEvent(event)
