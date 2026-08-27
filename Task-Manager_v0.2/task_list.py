from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from task_row import TaskRow

class TaskList:
    def __init__(self, main_window, task_layout):
        self.main_window = main_window
        self.task_layout = task_layout

    def create_task_row(self, task):
        row = TaskRow(task, self.main_window.current_tab, self.main_window)
        circle = row.circle
        circle._task_row = row

        if self.is_task_pending(task.id):
            circle.setText("◉")
            circle.setStyleSheet('''
            QPushButton {
            border: none;
            background: transparent;
            color: #E30000;
            font-size: 19px;
            font-weight: 300;
            }
            QPushButton: hover { color: #E30000; }
            QPushButton: pressed { color: #E30000; }
            ''')
        row.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        row.customContextMenuRequested.connect(lambda pos, tid=task.id: self.main_window.show_context_menu(pos, tid))

        # Circle button behavior
        if self.main_window.current_tab == "active" and not task.completed:
            circle.clicked.connect(lambda checked, tid=task.id, btn=circle: self.main_window.handle_circle_click(tid, btn))

        elif self.main_window.current_tab == "completed" and task.completed:
            circle.clicked.connect(lambda checked, tid=task.id: self.main_window.undo_task(tid))  
        return row

    def display_tasks(self, tasks):
        for index, task in enumerate(tasks):
            row = self.create_task_row(task)
            self.task_layout.addWidget(row)

            if index < len(tasks) - 1:
                separator = QWidget()
                separator.setFixedHeight(1)
                separator.setStyleSheet("background-color: #D1D1D6;")
                self.task_layout.addWidget(separator)

        QTimer.singleShot(0, self.update_container_height)

    def update_container_height(self):
        self.task_layout.activate()
        container = self.task_layout.parentWidget()
        if container is not None:
            content_height = max(self.task_layout.sizeHint().height(), 1)
            container.setFixedHeight(content_height)
            self.main_window.task_scroll_area.set_content_height(content_height)

    def clear_task_list(self):
        container = self.task_layout.parentWidget()
        if container is not None:
            container.setMinimumHeight(0)
            container.setMaximumHeight(16777215)

        while self.task_layout.count():
            item = self.task_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def get_visible_tasks(self):
        if self.main_window.current_tab == "active":
            tasks = self.main_window.service.get_active_tasks()
        elif self.main_window.current_tab == "completed":
            tasks = self.main_window.service.get_completed_tasks()
        else:
            tasks = self.main_window.service.get_deleted_tasks()

        if self.main_window.search_text:
            tasks = [
                t for t in tasks
                if self.main_window.search_text in t.title.lower()
                or self.main_window.search_text in t.notes.lower()
            ]
        return tasks

    def is_task_pending(self, task_id):
        return task_id in self.main_window.pending_timers
    