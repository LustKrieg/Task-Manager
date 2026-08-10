from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from task_row import TaskRow

class TaskList:
    def __init__(self, main_window):
        self.main_window = main_window

    def display_tasks(self, tasks):
        for task in tasks:
            row = TaskRow(task, self.main_window.current_tab, self.main_window)
            circle = row.circle
            row.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            row.customContextMenuRequested.connect(lambda pos, tid=task.id: self.main_window.show_context_menu(pos, tid))

            # Circle color logic
            if self.main_window.current_tab == "active" and not task.completed:
                circle.clicked.connect(lambda checked, tid=task.id, btn=circle: self.main_window.handle_circle_click(tid, btn))

            elif self.main_window.current_tab == "completed" and task.completed:
                circle.clicked.connect(lambda checked, tid=task.id: self.main_window.undo_task(tid))

            self.main_window.task_layout.addWidget(row)

            separator = QWidget()
            separator.setFixedHeight(1)
            separator.setStyleSheet("background-color: #D1D1D6;")
            self.main_window.task_layout.addWidget(separator)