from PyQt6.QtWidgets import (QWidget, QSizePolicy, 
    QHBoxLayout, QVBoxLayout, QPushButton, QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
class TaskRow(QWidget):
    def __init__(self, task, current_tab, main_window):
        super().__init__()

        self.task = task
        self.current_tab = current_tab
        self.main_window = main_window

        self.setObjectName("taskRow")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.build_circle()
        self.build_labels()
        self.build_layout()

    def build_circle(self):
        if self.current_tab == "active":
            circle_text = "○"
            circle_color = "#8E8E93"
        elif self.current_tab == "completed":
            circle_text = "◉"
            circle_color = "#E30000"
        else:
            if self.task.completed:
                circle_text = "◉"
                circle_color = "#E30000"
            else:
                circle_text = "○"
                circle_color = "#8E8E93"

        hover_color = "#E30000" if not self.task.completed else "#8E8E93"

        self.circle = QPushButton(circle_text)
        self.circle.setFixedSize(30, 30)
        self.circle.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                color: {circle_color};
                font-size: 22px;
                font-weight: 300;
            }}
            QPushButton:hover {{
                color: {hover_color};
            }}
            QPushButton:pressed {{
                color: #E30000;
            }}
        """)

    def build_labels(self):
        self.title_label = QLabel(self.task.title)
        self.title_label.setStyleSheet("color: black; font-size: 15px;")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.title_label.setWordWrap(True)

        if self.current_tab == "active":
            self.title_label.mousePressEvent = self.open_title_edit

        self.date_label = QLabel(self.task.created_at.strftime("%b %d, %I:%M %p"))
        self.date_label.setStyleSheet("color: #8E8E93; font-size: 11px;")

        self.notes_label = None
        if self.task.notes and self.task.notes.strip():
            self.notes_label = QLabel(self.task.notes)
            self.notes_label.setStyleSheet("color: #8E8E93; font-size: 12px;")
            self.notes_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.notes_label.setWordWrap(True)

            if self.current_tab == "active":
                self.notes_label.mousePressEvent = self.open_notes_edit
                self.title_label._notes_text = self.notes_label
            else:
                self.notes_label = None

    def build_layout(self):
        self.row_layout = QHBoxLayout(self)
        self.row_layout.setContentsMargins(0, 0, 0, 0)

        self.left_column = QWidget()
        self.left_layout = QVBoxLayout(self.left_column)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(2)

        self.left_layout.addWidget(self.title_label)

        if self.notes_label:
            self.left_layout.addWidget(self.notes_label)

        self.left_layout.addWidget(self.date_label)

        self.row_layout.addWidget(self.left_column)
        self.row_layout.setStretchFactor(self.left_column, 1)
        self.row_layout.addWidget(self.circle)

    def open_title_edit(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.main_window.start_editing(
                self.title_label,
                self.task.id,
                self.task.title
            )

    def open_notes_edit(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.main_window.start_editing(
                self.title_label,
                self.task.id,
                self.task.title,
                focus_on="notes"
            )