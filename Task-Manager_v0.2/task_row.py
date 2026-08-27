from PyQt6.QtWidgets import (QWidget, QSizePolicy, 
    QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QToolButton, QTextEdit,
    QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextOption

class CircleButton(QPushButton):
    pressed_state = pyqtSignal()
    released_state = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressed_state.emit()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.released_state.emit()

        super().mouseReleaseEvent(event)


class NewTaskInput(QLineEdit):
    escape_pressed = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.escape_pressed.emit()
            return
        super().keyPressEvent(event)


class NewTaskRow(QWidget):
    def __init__(self, save_task, cancel_task):
        super().__init__()
        self.setObjectName("newTaskRow")

        circle = QLabel("○")
        circle.setFixedSize(26, 26)
        circle.setStyleSheet("color: #8E8E93; font-size: 19px;")

        self.title_input = NewTaskInput()
        self.title_input.setPlaceholderText("New Reminder")
        self.title_input.setStyleSheet('''
            QLineEdit {
                border: none;
                background: white;
                color: black;
                font-size: 15px;
                padding: 0px;
            }
        ''')
        self.title_input.returnPressed.connect(save_task)
        self.title_input.escape_pressed.connect(cancel_task)

        self.notes_input = NewTaskInput()
        self.notes_input.setPlaceholderText("Notes")
        self.notes_input.setStyleSheet('''
            QLineEdit {
                border: none;
                background: white;
                color: #8E8E93;
                font-size: 12px;
                padding: 0px;
            }
        ''')
        self.notes_input.returnPressed.connect(save_task)
        self.notes_input.escape_pressed.connect(cancel_task)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(circle, alignment=Qt.AlignmentFlag.AlignTop)
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.addWidget(self.title_input)
        text_layout.addWidget(self.notes_input)
        layout.addLayout(text_layout)

class TaskRow(QWidget):
    def __init__(self, task, current_tab, main_window):
        super().__init__()

        self.task = task
        self.current_tab = current_tab
        self.main_window = main_window

        self.setObjectName("taskRow")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
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

        self.circle = CircleButton(circle_text)
        self.circle.setFixedSize(26, 26)
        self.circle.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                color: {circle_color};
                font-size: 19px;
                font-weight: 300;
            }}
            QPushButton:hover {{
                color: {hover_color};
            }}
            QPushButton:pressed {{
                color: #8E8E93;
            }}
        """)
        if self.current_tab == "trash":
            self.circle.setEnabled(False)

        self.circle.pressed_state.connect(self.circle_mouse_pressed)
        self.circle.released_state.connect(self.circle_mouse_released)

    def set_circle_state(self, completed, pending=False):
        if completed:
            circle_text = "◉"
            circle_color = "#E30000" if not pending else "#8E8E93"
            hover_color = "#E30000"
        else:
            circle_text = "○"
            circle_color = "#8E8E93"
            hover_color = "#E30000"
        self.circle.setText(circle_text)

        self.circle.setStyleSheet(f'''
            QPushButton {{
            border: none;
            background: transparent;
            color: {circle_color};
            font-size: 19px;
            font-weight: 300;
            }}
            QPushButton:hover {{
            color: {hover_color};
            }}
            QPushButton:pressed {{
            color: #8E8E93;
            }}
        ''')

    def circle_mouse_pressed(self):
        if self.task.completed:
            self.circle.setText("○")
            self.circle.setStyleSheet('''
                QPushButton {
                border: none;
                background: transparent;
                color: #8E8E93;
                font-size: 19px;
                font-weight: 300;
                }
            ''')
        else:
            self.circle.setText("◉")
            self.circle.setStyleSheet('''
                QPushButton {
                border: none;
                background: transparent;
                color: #8E8E93;
                font-size: 19px;
                font-weight: 300;
                }
            ''')

    def circle_mouse_released(self):
        if self.task.completed:
            self.circle.setText("○")
            self.circle.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    color: #8E8E93;
                    font-size: 19px;
                    font-weight: 300;
                }
            """)
        else:
            self.circle.setText("◉")
            self.circle.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    color: #E30000;
                    font-size: 19px;
                    font-weight: 300;
                }
            """)


    def build_labels(self):
        self.title_label = QLabel(self.task.title)
        self.title_label.setStyleSheet("color: black; font-size: 15px;")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.title_label.setMinimumWidth(0)
        self.title_label.setWordWrap(True)

        if self.current_tab == "active":
            self.title_label.mousePressEvent = self.open_title_edit

        self.date_label = QLabel(self.task.created_at.strftime("%b %d, %I:%M %p"))
        self.date_label.setStyleSheet("color: #8E8E93; font-size: 11px;")

        # Always create notes label
        self.notes_label = QLabel(self.task.notes or "")
        self.notes_label.setStyleSheet("color: #8E8E93; font-size: 12px;")
        self.notes_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.notes_label.setMinimumWidth(0)
        self.notes_label.setWordWrap(True)

        if self.current_tab == "active":
            self.notes_label.mousePressEvent = self.open_notes_edit

        self.title_label._notes_text = self.notes_label

        if not self.task.notes or not self.task.notes.strip():
            self.notes_label.hide()

        self.info_button = QToolButton(self)
        self.info_button.setText("ⓘ")
        self.info_button.setFixedSize(26, 26)
        self.info_button.setStyleSheet('''
            QToolButton {
                border: none;
                background: transparent;
                color: #8E8E93;
                font-size: 17px;
            }
            QToolButton:hover {
                color: #3A3A3C;
            }
        ''')
        self.info_button.hide()

    def build_layout(self):
        self.row_layout = QHBoxLayout(self)
        self.row_layout.setContentsMargins(0, 0, 0, 0)
        self.row_layout.setSpacing(8)

        self.left_column = QWidget()
        self.left_column.setMinimumWidth(0)
        self.left_column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.left_layout = QVBoxLayout(self.left_column)
        self.left_layout.setContentsMargins(0, 0, 34, 0)
        self.left_layout.setSpacing(2)

        self.left_layout.addWidget(self.title_label)
        self.left_layout.addWidget(self.notes_label)
        self.left_layout.addWidget(self.date_label)

        self.row_layout.addWidget(self.circle,alignment=Qt.AlignmentFlag.AlignTop)
        self.row_layout.addWidget(self.left_column, 1)
        self.info_button.raise_()

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

    def enterEvent(self, event):
        self.info_button.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.info_button.hide()
        super().leaveEvent(event)

    # Position ⓘ at top-right of the row, vertically centered with first line
    def resizeEvent(self, event):
        super().resizeEvent(event)
        btn_w = self.info_button.width()
        btn_h = self.info_button.height()
        x = self.width() - btn_w - 2
        y = (self.circle.height() - btn_h) // 2 # align with circle = first line
        self.info_button.move(x, y)