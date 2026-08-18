import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QScrollArea,QMenu
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from database import TaskDatabase
from service import TaskService

# From other files
from sidebar import Sidebar
from task_editor import TaskEditor
from task_list import TaskList
from task_row import TaskRow


class MainWindow(QMainWindow):
    def __init__(self, service: TaskService):
        super().__init__()
        self.current_tab = "active"
        self.service = service
        self.setWindowTitle("Task Manager")
        self.setGeometry(100, 100, 750, 500)
        self.pending_timers = {}
        self.search_text = ""
        self.task_editor = TaskEditor(self)

        # --- Central Widget ---
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.search_input = self.sidebar.search_input
        self.active_tab = self.sidebar.active_tab
        self.completed_tab = self.sidebar.completed_tab
        self.trash_tab = self.sidebar.trash_tab

        self.search_input.textChanged.connect(self.on_search_changed)

        self.active_tab.clicked.connect(lambda: self.switch_tab("active"))
        self.completed_tab.clicked.connect(lambda: self.switch_tab("completed"))
        self.trash_tab.clicked.connect(lambda: self.switch_tab("trash"))


        # --- CONTENT (Right) ---
        content = QWidget()
        content.setStyleSheet("background: white;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(15)

        # --- Title ---
        self.title_label = QLabel("Active")
        self.title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
#        content_layout.addWidget(self.title_label)

        # --- Top Bar: Add "+" Button
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(10)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(30, 30)
        add_btn.setStyleSheet('''
            QPushButton {
                border: 2px solid #8E8E93;
                border-radius: 8px;
                background: transparent;
                color: #8E8E93;
                font-size: 20px;
                font-weight: 300;
            }
            QPushButton:hover {
                background: #E5E5EA;
                border-color: #3A3A3C;
                color: black;
            }
        ''')
        add_btn.clicked.connect(self.add_task_from_button)
        top_bar.addWidget(self.title_label)
        top_bar.addStretch()
        top_bar.addWidget(add_btn)

        content_layout.addLayout(top_bar)

        # --- Add Task Row ---
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("New Reminder")
        self.task_input.setStyleSheet('''
            QLineEdit {
                border: none;
                background: white;
                color: black;
                font-size: 15px;
                padding: 10px 0px;
            }
            QLineEdit:focus {
                border: none;
            }
        ''')

        self.task_input.returnPressed.connect(self.add_task)
        content_layout.addWidget(self.task_input)

        entry_separator = QWidget()
        entry_separator.setFixedHeight(1)
        entry_separator.setStyleSheet("background-color: #D1D1D6;")
        content_layout.addWidget(entry_separator)

        # --- Scroll Area for Tasks ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: white;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #C1C1C6;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8E8E93;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.task_container = QWidget()
        self.task_container.setStyleSheet("background: white;")
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.task_layout.setContentsMargins(0, 0, 0, 0)
        self.task_list = TaskList(self, self.task_layout)

        scroll.setWidget(self.task_container)
        content_layout.addWidget(scroll)

        # --- Add sidebar and content to main layout ---
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content)
        main_layout.setStretchFactor(content, 1)

        # --- Load tasks ---
        self.refresh_tasks()

        self.setFocus()

    def add_task(self):
        title = self.task_input.text().strip()
        if title:
            self.service.add_task(title)
            self.task_input.clear()
            self.refresh_tasks()

    def switch_tab(self, tab_name: str):
        for tab, name in [(self.active_tab, "active"), 
                        (self.completed_tab, "completed"), 
                        (self.trash_tab, "trash")]:
            tab.setProperty("active", name == tab_name)
            tab.style().polish(tab)
        
        self.current_tab = tab_name

        titles = {"active": "Active", "completed": "Completed", "trash": "Recently Deleted"}
        self.title_label.setText(titles[tab_name])
        self.refresh_tasks()

    def refresh_tasks(self):
        self.task_editor.close_current_edit(True, skip_refresh=True)
        self.task_list.clear_task_list()
        tasks = self.task_list.get_visible_tasks()
        self.task_list.display_tasks(tasks)

    def complete_task(self, task_id: int):
        self.service.complete_task(task_id)
        self.refresh_tasks()

    def undo_task(self, task_id: int):
        self.service.undo_task(task_id)
        self.refresh_tasks()

    def handle_circle_click(self, task_id: int, circle_button):
        if task_id in self.pending_timers:
            timer = self.pending_timers.pop(task_id)
            timer.stop()
            timer.deleteLater()
            task = self.service.get_task(task_id)

            row = circle_button._task_row
            row.set_circle_state(task.completed, pending=False)
            return
        
        task = self.service.get_task(task_id)

        if task.completed:
            circle_button.setText("○")
            pending_action = "undo"
        else:
            circle_button.setText("◉")
            pending_action = "complete"

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.finish_pending_completion(task_id, pending_action))
        timer.start(1500)
        self.pending_timers[task_id] = timer

    def finish_pending_completion(self, task_id, action):
        timer = self.pending_timers.pop(task_id, None)
        if timer:
            timer.deleteLater()

        if action == "complete":
            self.service.complete_task(task_id)

        elif action == "undo":
            self.service.undo_task(task_id)

        self.refresh_tasks()

    def start_editing(self, title_label, task_id, current_title, focus_on="title"):
        self.task_editor.start_editing(title_label, task_id, current_title, focus_on)

    def restore_task(self, task_id: int):
        self.service.restore_task(task_id)
        self.refresh_tasks()

    def restore_all_tasks(self):
        self.service.restore_all()
        self.refresh_tasks()

    def popup_delete_task(self):
        self.move_to_trash(self.selected_task_id)

    def move_to_trash(self, task_id: int):
        self.service.move_to_trash(task_id)
        self.refresh_tasks()

    def delete_forever(self, task_id: int):
        self.service.delete_forever(task_id)
        self.refresh_tasks()

    def empty_trash(self):
        self.service.empty_trash()
        self.refresh_tasks()

    def add_task_from_button(self):
        self.task_input.setFocus()
        self.task_input.selectAll()

    def on_search_changed(self, text):
        self.search_text = text.strip().lower()
        self.refresh_tasks()

    def show_context_menu(self, pos, task_id):
        menu = QMenu()
        self.selected_task_id = task_id

        if self.current_tab == "trash":
            action_restore = menu.addAction("Restore")
            action_restore.triggered.connect(lambda: self.restore_task(self.selected_task_id))

            action_delete = menu.addAction("Delete Forever")
            action_delete.triggered.connect(lambda: self.delete_forever(self.selected_task_id))

            menu.addSeparator()

            action_restore_all = menu.addAction("Restore All")
            action_restore_all.triggered.connect(self.restore_all_tasks)

            action_empty = menu.addAction("Delete All")
            action_empty.triggered.connect(self.empty_trash)
        else:
            action_delete = menu.addAction("Delete")
            action_delete.triggered.connect(self.popup_delete_task)

        menu.exec(self.sender().mapToGlobal(pos))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = TaskDatabase()
    db.create_table()
    service = TaskService(db)
    window = MainWindow(service)
    window.show()
    sys.exit(app.exec())
