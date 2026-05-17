from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.utils import NAV_ITEMS

_NAV_CODES = {
    "dashboard": "OVR",
    "monitor": "MON",
    "alert_center": "ALR",
    "whitelist": "WHT",
    "logs": "LOG",
    "statistics": "STA",
    "settings": "CFG",
}


class Sidebar(QWidget):
    workspace_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(104)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.shell = QFrame()
        self.shell.setObjectName("DockShell")
        shell_layout = QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(12, 16, 12, 16)
        shell_layout.setSpacing(12)

        brand = QFrame()
        brand.setObjectName("DockBrand")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(10, 10, 10, 10)
        brand_layout.setSpacing(4)
        self.brand_mark = QLabel("WSM")
        self.brand_mark.setObjectName("DockCode")
        self.brand_name = QLabel("Node")
        self.brand_name.setObjectName("DockMeta")
        self.brand_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(self.brand_mark, alignment=Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(self.brand_name)
        shell_layout.addWidget(brand)

        self.status_chip = QFrame()
        self.status_chip.setObjectName("DockStatus")
        status_layout = QVBoxLayout(self.status_chip)
        status_layout.setContentsMargins(8, 8, 8, 8)
        status_layout.setSpacing(3)
        self.status_pulse = QFrame()
        self.status_pulse.setObjectName("DockPulse")
        self.status_pulse.setFixedSize(12, 12)
        self.status_label = QLabel("OFF")
        self.status_label.setObjectName("DockTiny")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_pulse, alignment=Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_label)
        shell_layout.addWidget(self.status_chip)

        self.button_group = QButtonGroup(self)
        self.buttons: list[QPushButton] = []
        for index, (key, title, summary) in enumerate(NAV_ITEMS):
            button = QPushButton(_NAV_CODES.get(key, title[:3].upper()))
            button.setProperty("role", "dock")
            button.setCheckable(True)
            button.setToolTip(f"{title}\n{summary}")
            button.clicked.connect(
                lambda checked=False, i=index: self.workspace_selected.emit(i)
            )
            self.button_group.addButton(button, index)
            self.buttons.append(button)
            shell_layout.addWidget(button)

        shell_layout.addStretch(1)

        footer = QFrame()
        footer.setObjectName("DockFooter")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(8, 8, 8, 8)
        footer_layout.setSpacing(6)

        self.scope_code = QLabel("SCP")
        self.scope_code.setObjectName("DockTiny")
        self.scope_code.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scope_value = QLabel("ALL")
        self.scope_value.setObjectName("DockMeta")
        self.scope_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.alert_code = QLabel("ALR")
        self.alert_code.setObjectName("DockTiny")
        self.alert_code.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alert_value = QLabel("00")
        self.alert_value.setObjectName("DockMeta")
        self.alert_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        footer_layout.addWidget(self.scope_code)
        footer_layout.addWidget(self.scope_value)
        footer_layout.addSpacing(4)
        footer_layout.addWidget(self.alert_code)
        footer_layout.addWidget(self.alert_value)
        shell_layout.addWidget(footer)

        layout.addWidget(self.shell, 1)
        self._interface = "-"
        self.set_connection(False)

    def set_active(self, index: int) -> None:
        for button_index, button in enumerate(self.buttons):
            button.setChecked(button_index == index)

    def set_connection(self, connected: bool) -> None:
        if connected:
            self.status_pulse.setStyleSheet(
                "background:#52d6a4; border:1px solid #7ae6bb; border-radius:6px;"
            )
            self.status_label.setText("LIVE")
            self.brand_name.setText(self._interface or "Node")
        else:
            self.status_pulse.setStyleSheet(
                "background:#ff7c92; border:1px solid #ff9db0; border-radius:6px;"
            )
            self.status_label.setText("LINK")
            self.brand_name.setText("Node")

    def set_interface(self, interface: str) -> None:
        self._interface = interface
        if self.status_label.text() == "LIVE":
            self.brand_name.setText(interface)

    def set_scope(self, scope: str) -> None:
        compact = "ALL"
        if scope and scope != "All detected APs":
            compact = scope.replace("selected APs", "SEL").replace(" ", "")
        self.scope_value.setText(compact[:8])

    def set_alert_count(self, count: int) -> None:
        self.alert_value.setText(f"{count:02d}" if count < 100 else "99+")
