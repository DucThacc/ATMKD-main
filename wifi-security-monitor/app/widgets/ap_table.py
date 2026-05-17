from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from app.utils import guess_vendor


class APTable(QTableWidget):
    checked_targets_changed = Signal(list)
    current_ap_changed = Signal(dict)

    def __init__(self):
        super().__init__(0, 7)
        self._aps: list[dict] = []
        self._selected_bssids: set[str] = set()
        self._suspicious_reasons: dict[str, str] = {}
        self._updating = False

        self.setHorizontalHeaderLabels(
            ["SEL", "SSID", "BSSID", "CH", "ENC", "RSSI", "VENDOR"]
        )
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(False)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in range(2, 6):
            self.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

        self.itemChanged.connect(self._on_item_changed)
        self.itemSelectionChanged.connect(self._on_selection_changed)

    def populate(
        self,
        aps: list[dict],
        selected_bssids: set[str],
        suspicious_reasons: dict[str, str],
    ) -> None:
        self._updating = True
        self._aps = aps
        self._selected_bssids = set(selected_bssids)
        self._suspicious_reasons = dict(suspicious_reasons)

        self.setSortingEnabled(False)
        self.setRowCount(0)

        for ap in aps:
            row = self.rowCount()
            self.insertRow(row)
            bssid = str(ap.get("bssid", "")).upper()
            suspicious_reason = suspicious_reasons.get(bssid, "")

            check_item = QTableWidgetItem()
            check_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            check_item.setCheckState(
                Qt.CheckState.Checked if bssid in self._selected_bssids else Qt.CheckState.Unchecked
            )
            check_item.setData(Qt.ItemDataRole.UserRole, ap)
            self.setItem(row, 0, check_item)

            values = [
                str(ap.get("ssid", "<Hidden>") or "<Hidden>"),
                bssid,
                str(ap.get("channel", "-")),
                str(ap.get("encryption", "-")),
                f"{ap.get('rssi', '-')} dBm",
                guess_vendor(bssid),
            ]
            for column, value in enumerate(values, start=1):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, ap)
                if suspicious_reason:
                    item.setToolTip(suspicious_reason)
                self.setItem(row, column, item)

            if suspicious_reason:
                for column in range(self.columnCount()):
                    item = self.item(row, column)
                    if item:
                        item.setBackground(QColor(67, 39, 20))
                        item.setForeground(QColor(255, 222, 171))
                        item.setToolTip(suspicious_reason)

        self.setSortingEnabled(True)
        self._updating = False
        self.checked_targets_changed.emit(self.selected_targets())
        self._emit_current_ap()

    def selected_targets(self) -> list[str]:
        return sorted(self._selected_bssids)

    def current_ap(self) -> Optional[dict]:
        row = self.currentRow()
        if row < 0:
            return None
        item = self.item(row, 1)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def apply_filters(self, search: str, mode: str) -> None:
        needle = search.strip().lower()
        for row in range(self.rowCount()):
            item = self.item(row, 1)
            if not item:
                continue
            ap = item.data(Qt.ItemDataRole.UserRole) or {}
            bssid = str(ap.get("bssid", "")).upper()
            haystack = " ".join(
                [
                    str(ap.get("ssid", "")),
                    bssid,
                    str(ap.get("encryption", "")),
                    guess_vendor(bssid),
                ]
            ).lower()
            visible = True
            if needle and needle not in haystack:
                visible = False
            if mode == "suspicious" and bssid not in self._suspicious_reasons:
                visible = False
            if mode == "selected" and bssid not in self._selected_bssids:
                visible = False
            self.setRowHidden(row, not visible)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating or item.column() != 0:
            return
        ap = item.data(Qt.ItemDataRole.UserRole) or {}
        bssid = str(ap.get("bssid", "")).upper()
        if not bssid:
            return
        if item.checkState() == Qt.CheckState.Checked:
            self._selected_bssids.add(bssid)
        else:
            self._selected_bssids.discard(bssid)
        self.checked_targets_changed.emit(self.selected_targets())

    def _on_selection_changed(self) -> None:
        self._emit_current_ap()

    def _emit_current_ap(self) -> None:
        ap = self.current_ap()
        if ap:
            self.current_ap_changed.emit(ap)

