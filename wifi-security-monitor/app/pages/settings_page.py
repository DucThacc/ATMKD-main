from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.styles import THEME_NAMES


class SettingsPage(QWidget):
    save_remote_requested = Signal()
    apply_local_requested = Signal()
    reload_requested = Signal()
    test_connection_requested = Signal()

    def __init__(self):
        super().__init__()
        self._loading = False
        self._dirty_remote = False
        self._dirty_local = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("PageHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(4)
        header_layout.addWidget(self._label("Settings", "SectionEyebrow"))
        title = QLabel("Configuration Workspace")
        title.setObjectName("PanelTitle")
        subtitle = self._label(
            "Remote detector configuration and local desktop preferences live here, separate from the operational tabs.",
            "SectionText",
        )
        subtitle.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        root.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_layout = QGridLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setHorizontalSpacing(14)
        content_layout.setVerticalSpacing(14)

        self.group_local = QGroupBox("Local Shell Preferences")
        local_form = QFormLayout(self.group_local)
        local_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        local_form.setHorizontalSpacing(12)
        local_form.setVerticalSpacing(10)
        self.base_url_input = QLineEdit()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(THEME_NAMES)
        self.status_refresh_spin = QSpinBox()
        self.status_refresh_spin.setRange(1, 60)
        self.alert_refresh_spin = QSpinBox()
        self.alert_refresh_spin.setRange(1, 60)
        self.log_limit_spin = QSpinBox()
        self.log_limit_spin.setRange(50, 2000)
        self.logs_auto_scroll = QCheckBox("Auto-select newest log entry")
        local_form.addRow("API URL", self.base_url_input)
        local_form.addRow("Theme", self.theme_combo)
        local_form.addRow("Status refresh (s)", self.status_refresh_spin)
        local_form.addRow("Alert refresh (s)", self.alert_refresh_spin)
        local_form.addRow("Log fetch limit", self.log_limit_spin)
        local_form.addRow("", self.logs_auto_scroll)

        self.group_general = QGroupBox("Interface and Paths")
        general_form = QFormLayout(self.group_general)
        general_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        general_form.setHorizontalSpacing(12)
        general_form.setVerticalSpacing(10)
        self.interface_input = QLineEdit()
        self.whitelist_path_input = QLineEdit()
        self.log_path_input = QLineEdit()
        general_form.addRow("Interface", self.interface_input)
        general_form.addRow("Whitelist path", self.whitelist_path_input)
        general_form.addRow("Log path", self.log_path_input)

        self.group_scan = QGroupBox("Scan Settings")
        scan_form = QFormLayout(self.group_scan)
        scan_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        scan_form.setHorizontalSpacing(12)
        scan_form.setVerticalSpacing(10)
        self.interactive_scan_check = QCheckBox("Prompt before monitor target selection")
        self.scan_seconds_spin = QSpinBox()
        self.scan_seconds_spin.setRange(1, 120)
        self.scan_max_results_spin = QSpinBox()
        self.scan_max_results_spin.setRange(1, 500)
        scan_form.addRow("", self.interactive_scan_check)
        scan_form.addRow("Scan seconds", self.scan_seconds_spin)
        scan_form.addRow("Max AP results", self.scan_max_results_spin)

        self.group_thresholds = QGroupBox("Detection Thresholds")
        threshold_form = QFormLayout(self.group_thresholds)
        threshold_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        threshold_form.setHorizontalSpacing(12)
        threshold_form.setVerticalSpacing(10)
        self.ssid_similarity_spin = QDoubleSpinBox()
        self.ssid_similarity_spin.setRange(0.0, 1.0)
        self.ssid_similarity_spin.setDecimals(2)
        self.ssid_similarity_spin.setSingleStep(0.01)
        self.alert_cooldown_spin = QSpinBox()
        self.alert_cooldown_spin.setRange(0, 3600)
        self.deauth_window_spin = QSpinBox()
        self.deauth_window_spin.setRange(1, 300)
        self.deauth_threshold_spin = QSpinBox()
        self.deauth_threshold_spin.setRange(1, 10000)
        threshold_form.addRow("SSID similarity", self.ssid_similarity_spin)
        threshold_form.addRow("Alert cooldown (s)", self.alert_cooldown_spin)
        threshold_form.addRow("Deauth window (s)", self.deauth_window_spin)
        threshold_form.addRow("Deauth threshold", self.deauth_threshold_spin)

        self.group_opensearch = QGroupBox("OpenSearch")
        os_form = QFormLayout(self.group_opensearch)
        os_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        os_form.setHorizontalSpacing(12)
        os_form.setVerticalSpacing(10)
        self.os_enabled_check = QCheckBox("Enable OpenSearch sink")
        self.os_endpoint_input = QLineEdit()
        self.os_index_input = QLineEdit()
        self.os_verify_tls_check = QCheckBox("Verify TLS")
        self.os_username_input = QLineEdit()
        self.os_password_input = QLineEdit()
        self.os_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        os_form.addRow("", self.os_enabled_check)
        os_form.addRow("Endpoint", self.os_endpoint_input)
        os_form.addRow("Index", self.os_index_input)
        os_form.addRow("", self.os_verify_tls_check)
        os_form.addRow("Username", self.os_username_input)
        os_form.addRow("Password", self.os_password_input)

        self.group_telegram = QGroupBox("Telegram")
        tg_form = QFormLayout(self.group_telegram)
        tg_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        tg_form.setHorizontalSpacing(12)
        tg_form.setVerticalSpacing(10)
        self.tg_enabled_check = QCheckBox("Enable Telegram notifications")
        self.tg_bot_token_input = QLineEdit()
        self.tg_bot_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.tg_chat_id_input = QLineEdit()
        tg_form.addRow("", self.tg_enabled_check)
        tg_form.addRow("Bot token", self.tg_bot_token_input)
        tg_form.addRow("Chat ID", self.tg_chat_id_input)

        content_layout.addWidget(self.group_local, 0, 0)
        content_layout.addWidget(self.group_general, 0, 1)
        content_layout.addWidget(self.group_scan, 1, 0)
        content_layout.addWidget(self.group_thresholds, 1, 1)
        content_layout.addWidget(self.group_opensearch, 2, 0)
        content_layout.addWidget(self.group_telegram, 2, 1)
        content_layout.setColumnStretch(0, 1)
        content_layout.setColumnStretch(1, 1)

        self.scroll.setWidget(content)
        root.addWidget(self.scroll, 1)

        sticky = QFrame()
        sticky.setObjectName("StickyBar")
        sticky_layout = QHBoxLayout(sticky)
        sticky_layout.setContentsMargins(16, 12, 16, 12)
        sticky_layout.setSpacing(10)
        self.status_label = self._label("All changes saved.", "SmallMeta")
        self.reload_button = QPushButton("Reload Remote Config")
        self.reload_button.setProperty("variant", "ghost")
        self.reload_button.clicked.connect(lambda _checked=False: self.reload_requested.emit())
        self.test_button = QPushButton("Test API Connection")
        self.test_button.setProperty("variant", "warning")
        self.test_button.clicked.connect(lambda _checked=False: self.test_connection_requested.emit())
        self.apply_local_button = QPushButton("Apply Local UI")
        self.apply_local_button.setProperty("variant", "primary")
        self.apply_local_button.clicked.connect(lambda _checked=False: self.apply_local_requested.emit())
        self.save_remote_button = QPushButton("Save Remote Config")
        self.save_remote_button.setProperty("variant", "success")
        self.save_remote_button.clicked.connect(lambda _checked=False: self.save_remote_requested.emit())
        sticky_layout.addWidget(self.status_label, 1)
        sticky_layout.addWidget(self.reload_button)
        sticky_layout.addWidget(self.test_button)
        sticky_layout.addWidget(self.apply_local_button)
        sticky_layout.addWidget(self.save_remote_button)
        root.addWidget(sticky)

        self._watch_local(
            [
                self.base_url_input,
                self.theme_combo,
                self.status_refresh_spin,
                self.alert_refresh_spin,
                self.log_limit_spin,
                self.logs_auto_scroll,
            ]
        )
        self._watch_remote(
            [
                self.interface_input,
                self.whitelist_path_input,
                self.log_path_input,
                self.interactive_scan_check,
                self.scan_seconds_spin,
                self.scan_max_results_spin,
                self.ssid_similarity_spin,
                self.alert_cooldown_spin,
                self.deauth_window_spin,
                self.deauth_threshold_spin,
                self.os_enabled_check,
                self.os_endpoint_input,
                self.os_index_input,
                self.os_verify_tls_check,
                self.os_username_input,
                self.os_password_input,
                self.tg_enabled_check,
                self.tg_bot_token_input,
                self.tg_chat_id_input,
            ]
        )

    def set_remote_config(self, config: dict) -> None:
        self._loading = True
        opensearch = config.get("opensearch", {})
        telegram = config.get("telegram", {})
        self.interface_input.setText(str(config.get("interface", "")))
        self.whitelist_path_input.setText(str(config.get("whitelist_path", "")))
        self.log_path_input.setText(str(config.get("log_path", "")))
        self.interactive_scan_check.setChecked(bool(config.get("interactive_scan", False)))
        self.scan_seconds_spin.setValue(int(config.get("scan_seconds", 10) or 10))
        self.scan_max_results_spin.setValue(int(config.get("scan_max_results", 20) or 20))
        self.ssid_similarity_spin.setValue(float(config.get("ssid_similarity_threshold", 0.85) or 0.85))
        self.alert_cooldown_spin.setValue(int(config.get("alert_cooldown_seconds", 30) or 30))
        self.deauth_window_spin.setValue(int(config.get("deauth_window_seconds", 10) or 10))
        self.deauth_threshold_spin.setValue(int(config.get("deauth_threshold", 20) or 20))

        self.os_enabled_check.setChecked(bool(opensearch.get("enabled", False)))
        self.os_endpoint_input.setText(str(opensearch.get("endpoint", "")))
        self.os_index_input.setText(str(opensearch.get("index", "")))
        self.os_verify_tls_check.setChecked(bool(opensearch.get("verify_tls", False)))
        self.os_username_input.setText(str(opensearch.get("username", "")))
        self.os_password_input.setText(str(opensearch.get("password", "")))

        self.tg_enabled_check.setChecked(bool(telegram.get("enabled", False)))
        self.tg_bot_token_input.setText(str(telegram.get("bot_token", "")))
        self.tg_chat_id_input.setText(str(telegram.get("chat_id", "")))

        self._loading = False
        self._dirty_remote = False
        self._update_status()

    def set_local_preferences(
        self,
        *,
        base_url: str,
        theme_name: str,
        status_refresh_seconds: int,
        alert_refresh_seconds: int,
        log_limit: int,
        logs_auto_scroll: bool,
    ) -> None:
        self._loading = True
        self.base_url_input.setText(base_url)
        self.theme_combo.setCurrentText(theme_name)
        self.status_refresh_spin.setValue(status_refresh_seconds)
        self.alert_refresh_spin.setValue(alert_refresh_seconds)
        self.log_limit_spin.setValue(log_limit)
        self.logs_auto_scroll.setChecked(logs_auto_scroll)
        self._loading = False
        self._dirty_local = False
        self._update_status()

    def collect_remote_payload(self) -> dict:
        return {
            "interface": self.interface_input.text().strip(),
            "whitelist_path": self.whitelist_path_input.text().strip(),
            "log_path": self.log_path_input.text().strip(),
            "interactive_scan": self.interactive_scan_check.isChecked(),
            "scan_seconds": int(self.scan_seconds_spin.value()),
            "scan_max_results": int(self.scan_max_results_spin.value()),
            "ssid_similarity_threshold": float(self.ssid_similarity_spin.value()),
            "alert_cooldown_seconds": int(self.alert_cooldown_spin.value()),
            "deauth_window_seconds": int(self.deauth_window_spin.value()),
            "deauth_threshold": int(self.deauth_threshold_spin.value()),
            "opensearch": {
                "enabled": self.os_enabled_check.isChecked(),
                "endpoint": self.os_endpoint_input.text().strip(),
                "index": self.os_index_input.text().strip(),
                "verify_tls": self.os_verify_tls_check.isChecked(),
                "username": self.os_username_input.text().strip(),
                "password": self.os_password_input.text(),
            },
            "telegram": {
                "enabled": self.tg_enabled_check.isChecked(),
                "bot_token": self.tg_bot_token_input.text(),
                "chat_id": self.tg_chat_id_input.text().strip(),
            },
        }

    def collect_local_preferences(self) -> dict:
        return {
            "base_url": self.base_url_input.text().strip(),
            "theme_name": self.theme_combo.currentText(),
            "status_refresh_seconds": int(self.status_refresh_spin.value()),
            "alert_refresh_seconds": int(self.alert_refresh_spin.value()),
            "log_limit": int(self.log_limit_spin.value()),
            "logs_auto_scroll": self.logs_auto_scroll.isChecked(),
        }

    def mark_remote_saved(self, message: str) -> None:
        self._dirty_remote = False
        self.status_label.setText(message)
        self._update_status()

    def mark_local_applied(self, message: str) -> None:
        self._dirty_local = False
        self.status_label.setText(message)
        self._update_status()

    def set_status_message(self, message: str) -> None:
        self.status_label.setText(message)

    def _watch_local(self, widgets: Iterable[QWidget]) -> None:
        for widget in widgets:
            self._connect_changed(widget, self._mark_local_dirty)

    def _watch_remote(self, widgets: Iterable[QWidget]) -> None:
        for widget in widgets:
            self._connect_changed(widget, self._mark_remote_dirty)

    def _connect_changed(self, widget: QWidget, callback) -> None:
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(callback)
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(callback)
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(callback)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(callback)

    def _mark_local_dirty(self, *args) -> None:
        if self._loading:
            return
        self._dirty_local = True
        self._update_status()

    def _mark_remote_dirty(self, *args) -> None:
        if self._loading:
            return
        self._dirty_remote = True
        self._update_status()

    def _update_status(self) -> None:
        if self._dirty_remote and self._dirty_local:
            self.status_label.setText("Remote config and local UI settings have unsaved changes.")
        elif self._dirty_remote:
            self.status_label.setText("Remote detector config has unsaved changes.")
        elif self._dirty_local:
            self.status_label.setText("Local UI preferences have unsaved changes.")
        elif self.status_label.text() == "":
            self.status_label.setText("All changes saved.")

    @staticmethod
    def _label(text: str, name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(name)
        return label
