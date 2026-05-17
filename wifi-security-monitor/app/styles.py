from __future__ import annotations

from app.utils import DEFAULT_THEME

THEMES = {
    "SOC Navy": {
        "bg": "#060b10",
        "bg_alt": "#0a1118",
        "bg_deep": "#101922",
        "panel": "#101922",
        "panel_alt": "#141f2b",
        "panel_soft": "#182533",
        "panel_hover": "#1c2c3d",
        "border": "#243447",
        "border_soft": "#33506d",
        "text": "#edf3fb",
        "muted": "#97a9bd",
        "soft": "#7290ae",
        "accent": "#59b8ff",
        "accent_soft": "rgba(89,184,255,0.15)",
        "good": "#42d69d",
        "good_soft": "rgba(66,214,157,0.14)",
        "warn": "#ffb454",
        "warn_soft": "rgba(255,180,84,0.14)",
        "bad": "#ff6f86",
        "bad_soft": "rgba(255,111,134,0.14)",
    },
    "Graphite Blue": {
        "bg": "#070c12",
        "bg_alt": "#0b1219",
        "bg_deep": "#121c27",
        "panel": "#121c27",
        "panel_alt": "#172331",
        "panel_soft": "#1b2b3c",
        "panel_hover": "#203346",
        "border": "#26394d",
        "border_soft": "#3a5776",
        "text": "#eef4fb",
        "muted": "#9bacc0",
        "soft": "#7f9bb8",
        "accent": "#71c0ff",
        "accent_soft": "rgba(113,192,255,0.15)",
        "good": "#4adca6",
        "good_soft": "rgba(74,220,166,0.14)",
        "warn": "#ffbf63",
        "warn_soft": "rgba(255,191,99,0.14)",
        "bad": "#ff7d93",
        "bad_soft": "rgba(255,125,147,0.14)",
    },
}

THEME_NAMES = tuple(THEMES.keys())


def get_stylesheet(theme_name: str = DEFAULT_THEME) -> str:
    t = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    return f"""
    * {{
        font-family: "Segoe UI", "Bahnschrift", sans-serif;
        color: {t["text"]};
        outline: none;
    }}
    QMainWindow, QWidget {{
        background: {t["bg"]};
        color: {t["text"]};
    }}
    QWidget#AppRoot {{
        background:
            qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {t["bg_deep"]},
                stop:0.45 {t["bg_alt"]},
                stop:1 {t["bg"]});
    }}
    QFrame#TopBar {{
        background: rgba(12,18,26,0.98);
        border: 1px solid {t["border"]};
        border-radius: 6px;
    }}
    QFrame#WorkspaceRibbon {{
        background: rgba(10,15,22,0.86);
        border: 1px solid {t["border"]};
        border-radius: 6px;
    }}
    QFrame#WorkspaceCanvas {{
        background: transparent;
        border: none;
    }}
    QFrame#PageHeader {{
        background: transparent;
        border: none;
    }}
    QFrame#Panel, QFrame#HeroPanel, QFrame#MetricCard, QFrame#StickyBar, QFrame#DetailCard {{
        background: rgba(15,24,34,0.97);
        border: 1px solid {t["border"]};
        border-radius: 6px;
    }}
    QFrame#HeroPanel {{
        background: rgba(18,29,41,0.98);
    }}
    QLabel {{
        background: transparent;
    }}
    QLabel#AppTitle {{
        font-size: 24px;
        font-weight: 800;
        letter-spacing: 0.2px;
    }}
    QLabel#AppSubtitle {{
        font-size: 13px;
    }}
    QLabel#AppSubtitle, QLabel#SectionText, QLabel#CardCaption,
    QLabel#EmptyState, QLabel#SmallMeta, QLabel#SidebarMeta, QLabel#DockMeta {{
        color: {t["muted"]};
    }}
    QLabel#SectionEyebrow, QLabel#CardEyebrow, QLabel#SidebarEyebrow,
    QLabel#MonoLabel, QLabel#DockCode, QLabel#DockTiny {{
        color: {t["soft"]};
        font-family: "Consolas", "Cascadia Mono", monospace;
        font-size: 11px;
        letter-spacing: 1.6px;
        text-transform: uppercase;
    }}
    QLabel#PanelTitle {{
        font-size: 21px;
        font-weight: 800;
    }}
    QLabel#MetricValue {{
        font-size: 30px;
        font-weight: 800;
    }}
    QLabel#StatusPill {{
        border-radius: 4px;
        padding: 8px 12px;
        background: {t["accent_soft"]};
        color: {t["accent"]};
        border: 1px solid {t["accent"]};
        font-family: "Consolas", "Cascadia Mono", monospace;
        font-size: 11px;
        font-weight: 700;
    }}
    QPushButton {{
        min-height: 38px;
        background: rgba(13,20,29,0.96);
        border: 1px solid {t["border"]};
        border-radius: 4px;
        padding: 0 16px;
        color: {t["text"]};
        font-weight: 700;
    }}
    QPushButton:hover {{
        background: {t["panel_hover"]};
        border-color: {t["border_soft"]};
    }}
    QPushButton:pressed {{
        background: {t["panel_soft"]};
    }}
    QPushButton[variant="primary"] {{
        background: {t["accent_soft"]};
        border-color: {t["accent"]};
        color: {t["accent"]};
    }}
    QPushButton[variant="success"] {{
        background: {t["good_soft"]};
        border-color: {t["good"]};
        color: {t["good"]};
    }}
    QPushButton[variant="warning"] {{
        background: {t["warn_soft"]};
        border-color: {t["warn"]};
        color: {t["warn"]};
    }}
    QPushButton[variant="danger"] {{
        background: {t["bad_soft"]};
        border-color: {t["bad"]};
        color: {t["bad"]};
    }}
    QPushButton[variant="ghost"] {{
        color: {t["muted"]};
    }}
    QPushButton[actionButton="true"][activeState="active"] {{
        background: {t["panel_soft"]};
        border-width: 2px;
    }}
    QPushButton[actionButton="true"][variant="warning"][activeState="active"] {{
        background: {t["warn_soft"]};
        border-color: {t["warn"]};
        color: {t["warn"]};
    }}
    QPushButton[actionButton="true"][variant="success"][activeState="active"] {{
        background: {t["good_soft"]};
        border-color: {t["good"]};
        color: {t["good"]};
    }}
    QPushButton[actionButton="true"][variant="danger"][activeState="active"] {{
        background: {t["bad_soft"]};
        border-color: {t["bad"]};
        color: {t["bad"]};
    }}
    QPushButton[actionButton="true"][variant="ghost"][activeState="active"] {{
        background: {t["accent_soft"]};
        border-color: {t["accent"]};
        color: {t["accent"]};
    }}
    QPushButton[actionButton="true"][activeState="active"]:disabled {{
        color: {t["text"]};
    }}
    QPushButton[role="workspaceTab"] {{
        min-height: 40px;
        border-radius: 4px;
        background: transparent;
        color: {t["soft"]};
        font-family: "Consolas", "Cascadia Mono", monospace;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 0 14px;
        text-align: left;
    }}
    QPushButton[role="workspaceTab"]:hover {{
        background: rgba(89,184,255,0.08);
        border-color: {t["accent"]};
        color: {t["text"]};
    }}
    QPushButton[role="workspaceTab"]:checked {{
        background: {t["panel_soft"]};
        border-color: {t["accent"]};
        color: {t["text"]};
    }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextBrowser, QListWidget, QTableWidget, QPlainTextEdit {{
        background: rgba(7,12,18,0.92);
        border: 1px solid {t["border"]};
        border-radius: 4px;
        color: {t["text"]};
    }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        min-height: 40px;
        padding: 0 12px;
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextBrowser:focus, QListWidget:focus {{
        border-color: {t["accent"]};
    }}
    QTextBrowser, QPlainTextEdit {{
        padding: 10px;
    }}
    QListWidget {{
        padding: 6px;
    }}
    QListWidget::item {{
        padding: 10px 12px;
        margin: 2px 0;
        border-radius: 6px;
    }}
    QListWidget::item:selected {{
        background: rgba(89,184,255,0.14);
        border: 1px solid {t["accent"]};
    }}
    QTableWidget {{
        gridline-color: rgba(36,52,71,0.5);
        font-family: "Consolas", "Cascadia Mono", monospace;
        font-size: 11px;
        selection-background-color: rgba(89,184,255,0.14);
    }}
    QTableWidget::item:selected {{
        background: rgba(89,184,255,0.14);
        color: {t["text"]};
    }}
    QHeaderView::section {{
        background: rgba(20,31,43,0.98);
        color: {t["soft"]};
        border: none;
        border-bottom: 1px solid {t["border"]};
        padding: 10px 8px;
        font-family: "Consolas", "Cascadia Mono", monospace;
        font-size: 10px;
        letter-spacing: 1.4px;
    }}
    QGroupBox {{
        background: rgba(15,24,34,0.97);
        border: 1px solid {t["border"]};
        border-radius: 6px;
        margin-top: 14px;
        padding-top: 14px;
        font-weight: 700;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 14px;
        padding: 0 6px;
        color: {t["accent"]};
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid {t["border_soft"]};
        background: rgba(7,12,18,0.92);
    }}
    QCheckBox::indicator:checked {{
        background: {t["accent"]};
        border-color: {t["accent"]};
    }}
    QScrollArea {{
        background: transparent;
        border: none;
    }}
    QStatusBar {{
        background: rgba(8,12,18,0.95);
        color: {t["muted"]};
        border-top: 1px solid {t["border"]};
    }}
    QStatusBar::item {{
        border: none;
    }}
    QSplitter::handle {{
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 12px;
        margin: 4px 0 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {t["border_soft"]};
        border-radius: 5px;
        min-height: 28px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
    QScrollBar:horizontal, QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: transparent;
        border: none;
        height: 0px;
        width: 0px;
    }}
    """
