from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QEasingCurve, QVariantAnimation
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


class StatCard(QFrame):
    def __init__(self, title: str, accent: str):
        super().__init__()
        self._accent = accent
        self._value = 0
        self._animation: Optional[QVariantAnimation] = None
        self.setObjectName("MetricCard")
        self.setMinimumHeight(154)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("CardEyebrow")

        self.value_label = QLabel("0")
        self.value_label.setObjectName("MetricValue")
        self.value_label.setStyleSheet(f"color: {accent};")
        self.value_label.setMinimumHeight(44)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.caption_label = QLabel("Waiting for telemetry")
        self.caption_label.setObjectName("CardCaption")
        self.caption_label.setWordWrap(True)
        self.caption_label.setMinimumHeight(34)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.caption_label)

    def set_value(
        self,
        value: int | str,
        caption: str = "",
        *,
        accent: Optional[str] = None,
        animate: bool = True,
    ) -> None:
        self.caption_label.setText(caption)
        self.value_label.setStyleSheet(f"color: {accent or self._accent};")
        if isinstance(value, int):
            if self._animation:
                self._animation.stop()
            if animate:
                self._animation = QVariantAnimation(self)
                self._animation.setStartValue(self._value)
                self._animation.setEndValue(value)
                self._animation.setDuration(320)
                self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
                self._animation.valueChanged.connect(
                    lambda current: self.value_label.setText(f"{int(current):,}")
                )
                self._animation.start()
            else:
                self.value_label.setText(f"{value:,}")
            self._value = value
            return

        if self._animation:
            self._animation.stop()
        self.value_label.setText(str(value))
