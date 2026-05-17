from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton

from app.utils import NAV_ITEMS


class WorkspaceSwitcher(QFrame):
    workspace_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("WorkspaceRibbon")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        self.buttons: list[QPushButton] = []
        for index, (_, title, _) in enumerate(NAV_ITEMS):
            button = QPushButton(title)
            button.setProperty("role", "workspaceTab")
            button.setCheckable(True)
            button.setMinimumWidth(150)
            button.clicked.connect(
                lambda checked=False, i=index: self.workspace_selected.emit(i)
            )
            self.buttons.append(button)
            layout.addWidget(button)
        layout.addStretch(1)

    def set_active(self, index: int) -> None:
        for button_index, button in enumerate(self.buttons):
            button.setChecked(button_index == index)
