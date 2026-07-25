import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import TaskDatabase
from service import TaskService

class MainWindow(QMainWindow):
    def __init__(self, service: TaskService):
        super().__init__()
        self.service = service
        self.setWindowTitle("Task Manager")
        self.setGeometry(100, 100, 600, 500)

        # --- Central Widget ---
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # --- Title ---
        title = QLabel("Acitve")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # --- Add Task Row ---
        add_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("New Reminder")
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_task)
        add_layout.addWidget(self.task_input)
        add_layout.addWidget(add_btn)
        main_layout.addLayout(add_layout)

        # --- Scroll Area for Tasks ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.task_container)
        main_layout.addWidget(scroll)

        # --- Load tasks ---
        self.refresh_tasks()

    def add_task(self):
        title = self.task_input.text().strip()
        if title:
            self.service.add_task(title)
            self.task_input.clear()
            self.refresh_tasks()

    def refresh_tasks(self):
        for i in reversed(range(self.task_layout.count())):
            widget = self.task_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        tasks = self.service.get_active_tasks()

        for task in tasks:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            circle = QPushButton("○")
            circle.setFixedSize(30, 30)
            circle.setStyleSheet("border: 1px solid gray; border-radius: 15px")
            circle.clicked.connect(lambda checked, tid=task.id: self.complete_task(tid))

            title_label = QLabel(task.title)


            row_layout.addWidget(circle)
            row_layout.addWidget(title_label)
            row_layout.addStretch()

            self.task_layout.addWidget(row)

    def complete_task(self, task_id: int):
        self.service.complete_task(task_id)
        self.refresh_tasks()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = TaskDatabase()
    db.create_table()
    service = TaskService(db)
    window = MainWindow(service)
    window.show()
    sys.exit(app.exec())
