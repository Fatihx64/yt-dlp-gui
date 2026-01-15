"""
YT-DLP GUI - Stylesheet
Night Mode (Pure Black) and Day Mode (Pure White) themes.
"""

# Night Mode - Pure black theme with subtle gray accents
DARK_THEME = """
/* ========== GLOBAL ========== */
* {
    font-family: 'Segoe UI', 'Arial', sans-serif;
}

QWidget {
    background-color: #000000;
    color: #e0e0e0;
    font-size: 13px;
}

QMainWindow {
    background-color: #000000;
}

/* ========== GROUP BOXES ========== */
QGroupBox {
    background-color: #1a1a1a;
    border: 1px solid #333333;
    border-radius: 6px;
    margin-top: 10px;
    padding: 10px;
    padding-top: 20px;
    font-weight: bold;
    color: #e0e0e0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #e0e0e0;
}

/* ========== BUTTONS ========== */
QPushButton {
    background-color: #2a2a2a;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 10px 20px;
    color: #e0e0e0;
    font-weight: normal;
    min-height: 28px;
    min-width: 100px;
}

QPushButton:hover {
    background-color: #3a3a3a;
    border-color: #555555;
}

QPushButton:pressed {
    background-color: #1a1a1a;
}

QPushButton:disabled {
    background-color: #1a1a1a;
    color: #555555;
    border-color: #333333;
}

/* Primary Button - subtle blue */
QPushButton#primaryButton {
    background-color: #1a5fb4;
    border-color: #1a5fb4;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background-color: #2a7fd4;
}

QPushButton#primaryButton:pressed {
    background-color: #144a8f;
}

/* Secondary Button - subtle purple */
QPushButton#secondaryButton {
    background-color: #4a3a8a;
    border-color: #4a3a8a;
    color: #ffffff;
}

QPushButton#secondaryButton:hover {
    background-color: #5a4a9a;
}

/* Danger Button - subtle red */
QPushButton#dangerButton {
    background-color: #8a2a2a;
    border-color: #8a2a2a;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background-color: #aa3a3a;
}

/* ========== INPUT FIELDS ========== */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1a1a1a;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px 10px;
    color: #e0e0e0;
    selection-background-color: #1a5fb4;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #1a5fb4;
}

QLineEdit:disabled {
    background-color: #0a0a0a;
    color: #555555;
}

/* ========== COMBO BOXES ========== */
QComboBox {
    background-color: #1a1a1a;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 24px;
    color: #e0e0e0;
}

QComboBox:hover {
    border-color: #555555;
}

QComboBox:focus {
    border-color: #1a5fb4;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
    background: transparent;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #e0e0e0;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a1a;
    border: 1px solid #444444;
    selection-background-color: #1a5fb4;
    color: #e0e0e0;
    outline: none;
    padding: 4px;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    min-height: 24px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #2a2a2a;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #1a5fb4;
}

/* ========== SPIN BOXES ========== */
QSpinBox, QDoubleSpinBox {
    background-color: #1a1a1a;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px 10px;
    color: #e0e0e0;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #1a5fb4;
}

/* ========== PROGRESS BARS ========== */
QProgressBar {
    background-color: #1a1a1a;
    border: 1px solid #333333;
    border-radius: 4px;
    height: 16px;
    text-align: center;
    color: #e0e0e0;
}

QProgressBar::chunk {
    background-color: #1a5fb4;
    border-radius: 3px;
}

/* ========== TAB WIDGET ========== */
QTabWidget::pane {
    border: 1px solid #333333;
    border-radius: 4px;
    background-color: #1a1a1a;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #0a0a0a;
    border: 1px solid #333333;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
    color: #888888;
}

QTabBar::tab:selected {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border-bottom: 2px solid #1a5fb4;
}

QTabBar::tab:hover:!selected {
    background-color: #151515;
    color: #aaaaaa;
}

/* ========== SCROLL BARS ========== */
QScrollBar:vertical {
    background-color: #0a0a0a;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #333333;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #444444;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #0a0a0a;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #333333;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #444444;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ========== LIST WIDGETS ========== */
QListWidget, QTableWidget, QTreeWidget {
    background-color: #1a1a1a;
    border: 1px solid #333333;
    border-radius: 4px;
    outline: none;
    padding: 4px;
    color: #e0e0e0;
}

QListWidget::item {
    padding: 6px;
    border-radius: 3px;
}

QListWidget::item:selected {
    background-color: #1a5fb4;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #2a2a2a;
}

QHeaderView::section {
    background-color: #1a1a1a;
    color: #e0e0e0;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #333333;
}

/* ========== SPLITTER ========== */
QSplitter::handle {
    background-color: #333333;
}

QSplitter::handle:horizontal {
    width: 1px;
}

QSplitter::handle:vertical {
    height: 1px;
}

/* ========== LABELS ========== */
QLabel {
    color: #e0e0e0;
    background-color: transparent;
}

QLabel#titleLabel {
    font-size: 16px;
    font-weight: bold;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #888888;
}

/* ========== CHECKBOXES ========== */
QCheckBox {
    spacing: 6px;
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #444444;
    background-color: #1a1a1a;
}

QCheckBox::indicator:checked {
    background-color: #1a5fb4;
    border-color: #1a5fb4;
}

QCheckBox::indicator:hover {
    border-color: #555555;
}

/* ========== MENU BAR ========== */
QMenuBar {
    background-color: #0a0a0a;
    padding: 4px;
    color: #e0e0e0;
    border-bottom: 1px solid #333333;
}

QMenuBar::item {
    padding: 6px 12px;
    border-radius: 3px;
}

QMenuBar::item:selected {
    background-color: #2a2a2a;
}

QMenu {
    background-color: #1a1a1a;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 4px;
    color: #e0e0e0;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #1a5fb4;
}

QMenu::separator {
    height: 1px;
    background-color: #333333;
    margin: 4px 8px;
}

/* ========== STATUS BAR ========== */
QStatusBar {
    background-color: #0a0a0a;
    color: #e0e0e0;
    padding: 4px;
    border-top: 1px solid #333333;
}

QStatusBar::item {
    border: none;
}

/* ========== TOOLTIPS ========== */
QToolTip {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #333333;
    border-radius: 3px;
    padding: 6px;
}

/* ========== MESSAGE BOX ========== */
QMessageBox {
    background-color: #1a1a1a;
}

QMessageBox QLabel {
    color: #e0e0e0;
}

QMessageBox QPushButton {
    min-width: 80px;
}

/* ========== FRAME ========== */
QFrame {
    background-color: transparent;
}

QFrame#separator {
    background-color: #333333;
    max-height: 1px;
}
"""

# Day Mode - Pure white theme with subtle gray accents
LIGHT_THEME = """
/* ========== GLOBAL ========== */
* {
    font-family: 'Segoe UI', 'Arial', sans-serif;
}

QWidget {
    background-color: #ffffff;
    color: #1a1a1a;
    font-size: 13px;
}

QMainWindow {
    background-color: #f5f5f5;
}

/* ========== GROUP BOXES ========== */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    margin-top: 10px;
    padding: 10px;
    padding-top: 20px;
    font-weight: bold;
    color: #1a1a1a;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #1a1a1a;
}

/* ========== BUTTONS ========== */
QPushButton {
    background-color: #f0f0f0;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 10px 20px;
    color: #1a1a1a;
    font-weight: normal;
    min-height: 28px;
    min-width: 100px;
}

QPushButton:hover {
    background-color: #e0e0e0;
    border-color: #b0b0b0;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QPushButton:disabled {
    background-color: #f5f5f5;
    color: #a0a0a0;
    border-color: #d0d0d0;
}

/* Primary Button - subtle blue */
QPushButton#primaryButton {
    background-color: #1a5fb4;
    border-color: #1a5fb4;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background-color: #2a7fd4;
}

QPushButton#primaryButton:pressed {
    background-color: #144a8f;
}

/* Secondary Button - subtle purple */
QPushButton#secondaryButton {
    background-color: #6a5aaa;
    border-color: #6a5aaa;
    color: #ffffff;
}

QPushButton#secondaryButton:hover {
    background-color: #7a6aba;
}

/* Danger Button - subtle red */
QPushButton#dangerButton {
    background-color: #c04040;
    border-color: #c04040;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background-color: #d05050;
}

/* ========== INPUT FIELDS ========== */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 6px 10px;
    color: #1a1a1a;
    selection-background-color: #1a5fb4;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #1a5fb4;
}

QLineEdit:disabled {
    background-color: #f5f5f5;
    color: #a0a0a0;
}

/* ========== COMBO BOXES ========== */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 24px;
    color: #1a1a1a;
}

QComboBox:hover {
    border-color: #a0a0a0;
}

QComboBox:focus {
    border-color: #1a5fb4;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
    background: transparent;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #1a1a1a;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    selection-background-color: #1a5fb4;
    selection-color: #ffffff;
    color: #1a1a1a;
    outline: none;
    padding: 4px;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    min-height: 24px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #f0f0f0;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #1a5fb4;
    color: #ffffff;
}

/* ========== SPIN BOXES ========== */
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 6px 10px;
    color: #1a1a1a;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #1a5fb4;
}

/* ========== PROGRESS BARS ========== */
QProgressBar {
    background-color: #e0e0e0;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    height: 16px;
    text-align: center;
    color: #1a1a1a;
}

QProgressBar::chunk {
    background-color: #1a5fb4;
    border-radius: 3px;
}

/* ========== TAB WIDGET ========== */
QTabWidget::pane {
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    background-color: #ffffff;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #f5f5f5;
    border: 1px solid #d0d0d0;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
    color: #666666;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1a1a1a;
    border-bottom: 2px solid #1a5fb4;
}

QTabBar::tab:hover:!selected {
    background-color: #eeeeee;
    color: #333333;
}

/* ========== SCROLL BARS ========== */
QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #f5f5f5;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #c0c0c0;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #a0a0a0;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ========== LIST WIDGETS ========== */
QListWidget, QTableWidget, QTreeWidget {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    outline: none;
    padding: 4px;
    color: #1a1a1a;
}

QListWidget::item {
    padding: 6px;
    border-radius: 3px;
}

QListWidget::item:selected {
    background-color: #1a5fb4;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #f0f0f0;
}

QHeaderView::section {
    background-color: #f5f5f5;
    color: #1a1a1a;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #d0d0d0;
}

/* ========== SPLITTER ========== */
QSplitter::handle {
    background-color: #d0d0d0;
}

QSplitter::handle:horizontal {
    width: 1px;
}

QSplitter::handle:vertical {
    height: 1px;
}

/* ========== LABELS ========== */
QLabel {
    color: #1a1a1a;
    background-color: transparent;
}

QLabel#titleLabel {
    font-size: 16px;
    font-weight: bold;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #666666;
}

/* ========== CHECKBOXES ========== */
QCheckBox {
    spacing: 6px;
    color: #1a1a1a;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #c0c0c0;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #1a5fb4;
    border-color: #1a5fb4;
}

QCheckBox::indicator:hover {
    border-color: #a0a0a0;
}

/* ========== MENU BAR ========== */
QMenuBar {
    background-color: #f5f5f5;
    padding: 4px;
    color: #1a1a1a;
    border-bottom: 1px solid #d0d0d0;
}

QMenuBar::item {
    padding: 6px 12px;
    border-radius: 3px;
}

QMenuBar::item:selected {
    background-color: #e0e0e0;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 4px;
    color: #1a1a1a;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #1a5fb4;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #d0d0d0;
    margin: 4px 8px;
}

/* ========== STATUS BAR ========== */
QStatusBar {
    background-color: #f5f5f5;
    color: #1a1a1a;
    padding: 4px;
    border-top: 1px solid #d0d0d0;
}

QStatusBar::item {
    border: none;
}

/* ========== TOOLTIPS ========== */
QToolTip {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #c0c0c0;
    border-radius: 3px;
    padding: 6px;
}

/* ========== MESSAGE BOX ========== */
QMessageBox {
    background-color: #ffffff;
}

QMessageBox QLabel {
    color: #1a1a1a;
}

QMessageBox QPushButton {
    min-width: 80px;
}

/* ========== FRAME ========== */
QFrame {
    background-color: transparent;
}

QFrame#separator {
    background-color: #d0d0d0;
    max-height: 1px;
}
"""


def get_theme(theme_name: str = "dark") -> str:
    """Get stylesheet for the specified theme."""
    if theme_name == "light":
        return LIGHT_THEME
    return DARK_THEME
