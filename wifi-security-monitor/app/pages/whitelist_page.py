from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from app.utils import is_valid_bssid


class WhitelistPage(QWidget):
    save_requested = Signal(dict, str)
    delete_requested = Signal(str)
    refresh_requested = Signal()

    def __init__(self):
        super().__init__()
        self._entries: list[dict] = []
        self._editing_bssid = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("PageHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(4)
        header_layout.addWidget(self._label("Whitelist", "SectionEyebrow"))
        title = QLabel("Trusted AP Policy")
        title.setObjectName("PanelTitle")
        subtitle = self._label(
            "Manage approved infrastructure on the left and edit the selected policy record on the right.",
            "SectionText",
        )
        subtitle.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        root.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_frame = QFrame()
        left_frame.setObjectName("Panel")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(10)
        head = QHBoxLayout()
        head.setSpacing(10)
        head.addWidget(self._label("Trusted AP Table", "SectionEyebrow"))
        head.addStretch(1)
        self.count_label = self._label("0 entries", "SmallMeta")
        head.addWidget(self.count_label)
        left_layout.addLayout(head)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setProperty("variant", "primary")
        self.btn_refresh.clicked.connect(lambda _checked=False: self.refresh_requested.emit())
        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.setProperty("variant", "danger")
        self.btn_delete.clicked.connect(self._delete_selected)
        self.btn_export = QPushButton("Export")
        self.btn_export.setProperty("variant", "warning")
        self.btn_export.clicked.connect(self._export_entries)
        button_row.addWidget(self.btn_refresh)
        button_row.addWidget(self.btn_delete)
        button_row.addWidget(self.btn_export)
        button_row.addStretch(1)
        left_layout.addLayout(button_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["SSID", "BSSID", "Channel", "Encryption", "Notes"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.table, 1)
        splitter.addWidget(left_frame)

        right_frame = QFrame()
        right_frame.setObjectName("Panel")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)
        right_layout.addWidget(self._label("Trusted AP Form", "SectionEyebrow"))
        self.mode_label = QLabel("Create trusted AP")
        self.mode_label.setStyleSheet("font-size: 20px; font-weight: 800;")
        self.mode_hint = self._label("Use this panel to add or edit approved infrastructure.", "SectionText")
        self.mode_hint.setWordWrap(True)
        right_layout.addWidget(self.mode_label)
        right_layout.addWidget(self.mode_hint)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.input_ssid = QLineEdit()
        self.input_bssid = QLineEdit()
        self.input_bssid.textChanged.connect(self._validate_form)
        self.input_channel = QSpinBox()
        self.input_channel.setRange(0, 196)
        self.input_encryption = QComboBox()
        self.input_encryption.addItems(["WPA2", "WPA3", "WPA", "Open"])
        self.input_note = QLineEdit()

        form.addRow("SSID", self.input_ssid)
        form.addRow("BSSID", self.input_bssid)
        form.addRow("Channel", self.input_channel)
        form.addRow("Encryption", self.input_encryption)
        form.addRow("Notes", self.input_note)
        right_layout.addLayout(form)

        self.validation_label = self._label("BSSID must use AA:BB:CC:DD:EE:FF format.", "SmallMeta")
        right_layout.addWidget(self.validation_label)

        form_buttons = QHBoxLayout()
        form_buttons.setSpacing(10)
        self.btn_save = QPushButton("Add to Whitelist")
        self.btn_save.setProperty("variant", "success")
        self.btn_save.clicked.connect(self._emit_save)
        self.btn_reset = QPushButton("Reset Form")
        self.btn_reset.setProperty("variant", "ghost")
        self.btn_reset.clicked.connect(self.reset_form)
        form_buttons.addWidget(self.btn_save)
        form_buttons.addWidget(self.btn_reset)
        form_buttons.addStretch(1)
        right_layout.addLayout(form_buttons)
        right_layout.addStretch(1)
        splitter.addWidget(right_frame)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

        self._validate_form()

    def set_entries(self, entries: list[dict]) -> None:
        self._entries = list(entries)
        self.table.setRowCount(0)
        for entry in entries:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, value in enumerate(
                [
                    str(entry.get("ssid", "")),
                    str(entry.get("bssid", "")),
                    str(entry.get("channel", "")),
                    str(entry.get("encryption", "")),
                    str(entry.get("note", "")),
                ]
            ):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, entry)
                self.table.setItem(row, column, item)
        self.count_label.setText(f"{len(entries)} trusted AP(s)")

    def prefill_from_access_point(self, ap: dict) -> None:
        self._editing_bssid = ""
        self.mode_label.setText("Create trusted AP")
        self.mode_hint.setText("Prefilled from the current monitor selection.")
        self.btn_save.setText("Add to Whitelist")
        self.input_ssid.setText(str(ap.get("ssid", "")))
        self.input_bssid.setText(str(ap.get("bssid", "")).upper())
        self.input_channel.setValue(int(ap.get("channel", 0) or 0))
        encryption = str(ap.get("encryption", "WPA2"))
        index = self.input_encryption.findText(encryption)
        self.input_encryption.setCurrentIndex(index if index >= 0 else 0)
        self.input_note.setText("Imported from monitor workspace")
        self._validate_form()

    def reset_form(self) -> None:
        self._editing_bssid = ""
        self.mode_label.setText("Create trusted AP")
        self.mode_hint.setText("Use this panel to add or edit approved infrastructure.")
        self.btn_save.setText("Add to Whitelist")
        self.input_ssid.clear()
        self.input_bssid.clear()
        self.input_channel.setValue(0)
        self.input_encryption.setCurrentIndex(0)
        self.input_note.clear()
        self._validate_form()

    def _on_selection_changed(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 1)
        entry = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not entry:
            return
        self._editing_bssid = str(entry.get("bssid", "")).upper()
        self.mode_label.setText("Edit trusted AP")
        self.mode_hint.setText("Modify the selected policy entry and save the new values.")
        self.btn_save.setText("Save Changes")
        self.input_ssid.setText(str(entry.get("ssid", "")))
        self.input_bssid.setText(str(entry.get("bssid", "")).upper())
        self.input_channel.setValue(int(entry.get("channel", 0) or 0))
        encryption = str(entry.get("encryption", "WPA2"))
        index = self.input_encryption.findText(encryption)
        self.input_encryption.setCurrentIndex(index if index >= 0 else 0)
        self.input_note.setText(str(entry.get("note", "")))
        self._validate_form()

    def _validate_form(self) -> None:
        bssid = self.input_bssid.text().strip().upper()
        if bssid and self.input_bssid.text() != bssid:
            self.input_bssid.blockSignals(True)
            self.input_bssid.setText(bssid)
            self.input_bssid.blockSignals(False)
        valid = bool(self.input_ssid.text().strip()) and is_valid_bssid(bssid)
        self.btn_save.setEnabled(valid)
        if bssid and not is_valid_bssid(bssid):
            self.input_bssid.setStyleSheet("border: 1px solid #ff6f86;")
            self.validation_label.setText("Invalid BSSID format. Expected AA:BB:CC:DD:EE:FF.")
        else:
            self.input_bssid.setStyleSheet("")
            self.validation_label.setText("BSSID must use AA:BB:CC:DD:EE:FF format.")

    def _emit_save(self) -> None:
        payload = {
            "ssid": self.input_ssid.text().strip(),
            "bssid": self.input_bssid.text().strip().upper(),
            "channel": int(self.input_channel.value()),
            "encryption": self.input_encryption.currentText(),
            "note": self.input_note.text().strip(),
        }
        self.save_requested.emit(payload, self._editing_bssid)

    def _delete_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select an entry", "Choose a trusted AP row first.")
            return
        item = self.table.item(row, 1)
        bssid = item.text() if item else ""
        confirm = QMessageBox.question(
            self,
            "Delete trusted AP",
            f"Remove {bssid} from the whitelist?",
        )
        if confirm == QMessageBox.StandardButton.Yes and bssid:
            self.delete_requested.emit(bssid)

    def _export_entries(self) -> None:
        if not self._entries:
            QMessageBox.information(self, "No data", "There are no whitelist entries to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Whitelist",
            "trusted-access-points.json",
            "JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self._entries, handle, indent=2, ensure_ascii=False)

    @staticmethod
    def _label(text: str, name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(name)
        return label
