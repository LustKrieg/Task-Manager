from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from styles import SIDEBAR_BUTTON_STYLE


class SearchLineEdit(QLineEdit):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.clear()
            self.clearFocus()
            event.accept()
            return
        super().keyPressEvent(event)


class Sidebar(QWidget):
    def __init__(self):
        super().__init__()

        self.setFixedWidth(280)
        self.setStyleSheet("""
            QWidget {
                background: #F5F5F7;
                border-right: 1px solid #E5E5EA;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(5)

        self.search_input = SearchLineEdit()
        search_icon = QIcon.fromTheme("edit-find")
        if search_icon.isNull():
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#8E8E93"), 1.5))
            painter.drawEllipse(2, 2, 8, 8)
            painter.drawLine(9, 9, 14, 14)
            painter.end()
            search_icon = QIcon(pixmap)

        self.search_input.addAction(search_icon, QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.setPlaceholderText("Search")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                background: white;
                color: black;
                font-size: 13px;
                padding: 6px 10px;
            }

            QLineEdit:focus {
                border: 1px solid #007AFF;
            }
        """)

        layout.addWidget(self.search_input)

        self.active_tab = QPushButton("○  Active")
        self.completed_tab = QPushButton("✓  Completed")
        self.trash_tab = QPushButton("▥  Recently Deleted")
        self.trash_tab.setObjectName("trashTab")

        for button in (
            self.active_tab,
            self.completed_tab,
            self.trash_tab,
        ):
            button.setFixedSize(130, 60)
            button.setFlat(True)
            button.setStyleSheet(SIDEBAR_BUTTON_STYLE)

        self.trash_tab.setStyleSheet(SIDEBAR_BUTTON_STYLE + '''
            QPushButton#trashTab {
                font-size: 14px;
            }
        ''')

        self.active_tab.setProperty("active", True)
        self.active_tab.style().polish(self.active_tab)

        layout.addWidget(self.active_tab)
        layout.addWidget(self.completed_tab)
        layout.addWidget(self.trash_tab)

        layout.addStretch()