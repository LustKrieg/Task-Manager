from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPointF
from PyQt6.QtGui import QAction, QActionGroup, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QMenu, QPushButton,
    QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)
from localization import available_languages, tr


class LanguageMenuButton(QPushButton):
    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#4B4B50"))
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        center_x = self.width() - 17
        center_y = self.height() / 2 - 1
        arrow = QPainterPath()
        arrow.moveTo(QPointF(center_x - 4, center_y - 2))
        arrow.lineTo(QPointF(center_x, center_y + 2))
        arrow.lineTo(QPointF(center_x + 4, center_y - 2))
        painter.drawPath(arrow)


class SettingsView(QWidget):
    back_requested = pyqtSignal()
    language_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_language = "English"
        self.setStyleSheet("background: #FFFFFF;")

        settings_layout = QHBoxLayout(self)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(0)

        navigation = QWidget()
        navigation.setFixedWidth(205)
        navigation.setStyleSheet("background: #F5F5F7;")
        navigation_layout = QVBoxLayout(navigation)
        navigation_layout.setContentsMargins(18, 22, 18, 20)
        navigation_layout.setSpacing(10)

        back_button = QToolButton()
        back_button.setText("\u2190")
        back_button.setToolTip(tr("Back to tasks"))
        back_button.setAccessibleName(tr("Back to tasks"))
        back_button.setFixedSize(34, 34)
        back_button.setStyleSheet("""
            QToolButton {
                border: none;
                border-radius: 6px;
                background: transparent;
                color: #3A3A3C;
                font-size: 20px;
            }
            QToolButton:hover { background: #E7E7EA; }
        """)
        back_button.clicked.connect(self.back_requested)
        navigation_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.title_label = QLabel(tr("Settings"))
        self.title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #202124;")
        navigation_layout.addWidget(self.title_label)

        self.language_tab = self._make_section_button("Language")
        self.general_tab = self._make_section_button("General")
        self.back_button = back_button
        self.section_group = QButtonGroup(self)
        self.section_group.setExclusive(True)
        self.section_group.addButton(self.language_tab)
        self.section_group.addButton(self.general_tab)
        self.language_tab.setChecked(True)
        self.language_tab.clicked.connect(lambda: self.panel_stack.setCurrentIndex(0))
        self.general_tab.clicked.connect(lambda: self.panel_stack.setCurrentIndex(1))
        navigation_layout.addWidget(self.language_tab)
        navigation_layout.addWidget(self.general_tab)
        navigation_layout.addStretch()

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFixedWidth(1)
        divider.setStyleSheet("color: #D9DADD; background: #D9DADD;")

        self.panel_stack = QStackedWidget()
        self.panel_stack.setStyleSheet("background: #FFFFFF;")
        self.panel_stack.addWidget(self._create_language_page())
        self.panel_stack.addWidget(self._create_general_page())

        settings_layout.addWidget(navigation)
        settings_layout.addWidget(divider)
        settings_layout.addWidget(self.panel_stack, 1)

    def _make_section_button(self, text):
        button = QPushButton(text)
        button.setFixedHeight(38)
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 6px;
                background: transparent;
                color: #3A3A3C;
                text-align: left;
                padding: 0 12px;
            }
            QPushButton:checked {
                background: #E5E7EA;
                color: #202124;
                font-weight: 600;
            }
            QPushButton:hover:!checked { background: #ECEDEF; }
        """)
        return button

    def _create_language_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(18)

        self.language_heading = QLabel(tr("Language"))
        self.language_heading.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.language_heading.setStyleSheet("color: #202124;")
        layout.addWidget(self.language_heading)

        self.language_picker = LanguageMenuButton()
        self.language_picker.setAccessibleName(tr("Choose language"))
        self.language_picker.setToolTip(tr("Choose language"))
        self.language_picker.setFixedSize(150, 32)
        self.language_picker.setFlat(True)
        self.language_picker.setStyleSheet("""
            QPushButton {
                border: 1px solid rgba(180, 182, 190, 210);
            border-radius: 7px;
                background: rgba(238, 240, 245, 220);
                color: #202124;
                text-align: left;
            padding: 0 26px 0 9px;
            font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(228, 231, 237, 238);
                border-color: rgba(150, 153, 162, 220);
            }
            QPushButton:pressed { background: rgba(216, 220, 228, 245); }
        """)
        self.language_menu = QMenu(self.language_picker)
        self.language_menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.language_menu.setStyleSheet("""
            QMenu {
                background-color: rgba(238, 240, 245, 238);
                border: 1px solid rgba(180, 182, 190, 210);
                border-radius: 12px;
                padding: 6px 5px;
                color: #202124;
            }
            QMenu::item {
                min-width: 120px;
                padding: 5px 18px 5px 27px;
                margin: 1px 3px;
                border-radius: 6px;
                color: #202124;
                font-size: 13px;
            }
            QMenu::item:selected {
                background: #1684FC;
                color: #FFFFFF;
            }
        """)
        self.language_actions = {}
        self.language_action_group = QActionGroup(self.language_menu)
        self.language_action_group.setExclusive(True)
        for language in available_languages():
            action = QAction(language, self.language_menu)
            action.setCheckable(True)
            action.triggered.connect(
                lambda checked=False, selected=language: self.set_language(selected)
            )
            self.language_action_group.addAction(action)
            self.language_menu.addAction(action)
            self.language_actions[language] = action
        self.language_picker.clicked.connect(self._show_language_menu)
        self.set_language("English", emit=False)
        layout.addWidget(
            self.language_picker,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        layout.addStretch()
        return page

    def _create_general_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 30, 36, 30)
        self.general_heading = QLabel(tr("General"))
        self.general_heading.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.general_heading.setStyleSheet("color: #202124;")
        layout.addWidget(self.general_heading)
        layout.addStretch()
        return page

    def _show_language_menu(self):
        position = self.language_picker.mapToGlobal(
            QPoint(0, self.language_picker.height())
        )
        self.language_menu.popup(position)

    def set_language(self, language, emit=True):
        if language not in available_languages():
            return
        self.current_language = language
        self.language_actions[language].setChecked(True)
        self.language_picker.setText(language)
        if emit:
            self.language_changed.emit(language)

    def retranslate_ui(self):
        self.back_button.setToolTip(tr("Back to tasks"))
        self.back_button.setAccessibleName(tr("Back to tasks"))
        self.title_label.setText(tr("Settings"))
        self.language_tab.setText(tr("Language"))
        self.general_tab.setText(tr("General"))
        self.language_heading.setText(tr("Language"))
        self.general_heading.setText(tr("General"))
        self.language_picker.setToolTip(tr("Choose language"))