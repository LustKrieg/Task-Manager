from datetime import datetime, timedelta
from PyQt6.QtWidgets import QWidget, QSizePolicy, QLabel
from PyQt6.QtCore import Qt, QTimer
from task_row import NewTaskRow, TaskRow


def format_due_for_search(value):
    if value is None:
        return ""
    try:
        return value.strftime("%b %-d %Y %-I:%M %p")
    except ValueError:
        return value.strftime("%b %d %Y %I:%M %p")


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
        if self.main_window.current_tab == "active":
            for title, section_tasks in self._group_active_tasks(tasks):
                heading = QLabel(title)
                heading.setFixedHeight(24)
                heading.setStyleSheet(
                    "color: #3A3A3C; font-size: 13px; font-weight: 600;"
                    "padding: 4px 0px 0px 0px; background: white;"
                )
                heading.setProperty("sticky_section", True)
                self.task_layout.addWidget(heading)
                for task in section_tasks:
                    self._add_task_row(task)
        else:
            for task in tasks:
                self._add_task_row(task)

        QTimer.singleShot(0, self.update_container_height)

    def _add_task_row(self, task):
        row = self.create_task_row(task)
        self.task_layout.addWidget(row)

        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #D1D1D6;")
        self.task_layout.addWidget(separator)

    @staticmethod
    def _group_active_tasks(tasks):
        now = datetime.now()
        now_timestamp = now.timestamp()
        today = now.date()
        week_end = today + timedelta(days=6 - today.weekday())
        dated_tasks = sorted(
            (task for task in tasks if task.due_at is not None),
            key=lambda task: task.due_at.timestamp(),
        )
        undated_tasks = [task for task in tasks if task.due_at is None]
        sections = []

        def add_section(title, matching_tasks):
            if matching_tasks:
                sections.append((title, matching_tasks))

        overdue = [task for task in dated_tasks if task.due_at.timestamp() < now_timestamp]
        add_section("Overdue", overdue)

        remaining = [task for task in dated_tasks if task.due_at.timestamp() >= now_timestamp]
        add_section("Today", [task for task in remaining if task.due_at.date() == today])

        tomorrow = today + timedelta(days=1)
        add_section("Tomorrow", [task for task in remaining if task.due_at.date() == tomorrow])

        next_weekdays = today + timedelta(days=2)
        while next_weekdays <= week_end:
            add_section(
                next_weekdays.strftime("%a %b %-d"),
                [task for task in remaining if task.due_at.date() == next_weekdays],
            )
            next_weekdays += timedelta(days=1)

        rest_of_month = [
            task for task in remaining
            if task.due_at.date().month == today.month
            and task.due_at.date().year == today.year
            and task.due_at.date() > week_end
        ]
        add_section(f"Rest of {now.strftime('%B')}", rest_of_month)

        later_months = sorted({
            (task.due_at.year, task.due_at.month)
            for task in remaining
            if (task.due_at.year, task.due_at.month) != (today.year, today.month)
            and task.due_at.date() > week_end
        })
        for year, month in later_months:
            month_tasks = [
                task for task in remaining
                if (task.due_at.year, task.due_at.month) == (year, month)
            ]
            title = datetime(year, month, 1).strftime("%B")
            if year != today.year:
                title += f", {year}"
            add_section(title, month_tasks)

        add_section("No Due Date", undated_tasks)
        return sections

    def add_new_task_row(self):
        if hasattr(self.main_window, "new_task_row"):
            self.main_window.new_task_row.title_input.setFocus()
            self.main_window.new_task_row.title_input.selectAll()
            return

        container = self.task_layout.parentWidget()
        previous_height = container.height() if container is not None else 0
        if container is not None:
            container.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Minimum,
            )
            container.setMinimumHeight(0)
            container.setMaximumHeight(16777215)

        new_task_row = NewTaskRow(
            self.main_window.save_new_task,
            self.main_window.cancel_new_task,
        )
        self.main_window.new_task_row = new_task_row
        self.task_layout.insertWidget(0, new_task_row)
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #D1D1D6;")
        self.main_window.new_task_separator = separator
        self.task_layout.insertWidget(1, separator)
        if container is not None:
            container.setMinimumHeight(
                previous_height
                + new_task_row.sizeHint().height()
                + separator.height()
                + (self.task_layout.spacing() * 2)
            )
        QTimer.singleShot(0, self.main_window.focus_new_task_row)
        QTimer.singleShot(0, self.update_container_height)

    def update_container_height(self):
        self.task_layout.activate()
        container = self.task_layout.parentWidget()
        if container is not None:
            container.setMinimumHeight(0)
            container.setMaximumHeight(16777215)
            container.setMinimumHeight(max(self.task_layout.sizeHint().height(), 1))

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
                or (
                    t.due_at is not None
                    and self.main_window.search_text in format_due_for_search(t.due_at).lower()
                )
            ]
        return tasks

    def is_task_pending(self, task_id):
        return task_id in self.main_window.pending_timers
    