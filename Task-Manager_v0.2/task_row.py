from PyQt6.QtWidgets import QWidget, QSizePolicy, QHBoxLayout, QPushButton

class TaskRow(QWidget):
    def __init__(self, task, current_tab):
        super().__init__()

        self.task = task
        self.current_tab = current_tab

        self.setObjectName("taskRow")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.build_circle()

        self.row_layout = QHBoxLayout(self)
        self.row_layout.setContentsMargins(0, 0, 0, 0)
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