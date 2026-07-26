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

        # --- Tab Bar ---
        self.current_tab = "active"
        tab_layout = QHBoxLayout()
        self.active_tab = QPushButton("Acitve")
        self.completed_tab = QPushButton("Completed")
        self.trash_tab = QPushButton("Recently Deleted")

        # Styling Bar Tabs
        for tab in (self.active_tab, self.completed_tab, self.trash_tab):
            tab.setFlat(True)
            tab.setStyleSheet('''
                QPushButton{
                border: none;
                padding: 12px 16px;
                font-size: 14px;
                font=weight: 500;
                color: #8E8E93;
                background: transparent;
                text-align: left;
                border-radius: 8px;
                }
                QPushButton:hover {
                background: #E5E5EA;
                }
                QPushButton:pressed {
                    background: #D1D1D6;
                }
                QPushButton[active="true"] {
                    background: #D1D1D6;
                    color: black;
                    font-weight: 600;
                }
            ''')

        self.active_tab.setProperty("active", True)
        self.active_tab.style().polish(self.active_tab)
        
        self.active_tab.clicked.connect(lambda: self.switch_tab("active"))
        self.completed_tab.clicked.connect(lambda: self.switch_tab("completed"))
        self.trash_tab.clicked.connect(lambda: self.switch_tab("trash"))

        tab_layout.addWidget(self.active_tab)
        tab_layout.addWidget(self.completed_tab)
        tab_layout.addWidget(self.trash_tab)
        tab_layout.addStretch()
        main_layout.addLayout(tab_layout)
            
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

    def switch_tab(self, tab_name: str):
        for tab, name in [(self.active_tab, "active"), 
                        (self.completed_tab, "completed"), 
                        (self.trash_tab, "trash")]:
            tab.setProperty("active", name == tab_name)
            tab.style().polish(tab)
        
        self.current_tab = tab_name
        self.refresh_tasks()

    def refresh_tasks(self):
        for i in reversed(range(self.task_layout.count())):
            widget = self.task_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if self.current_tab == "active":
            tasks = self.service.get_active_tasks()
        elif self.current_tab == "completed":
            tasks = self.service.get_completed_tasks()
        else:
            tasks = self.service.get_deleted_tasks()

        for task in tasks:
            row = QWidget()
            row.setObjectName("taskRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            title_label = QLabel(task.title)
            title_label.setObjectName("tasktitle")

            circle = QPushButton("○" if not task.completed else"◉")
            circle.setFixedSize(30, 30)
            circle.setStyleSheet('''
                QPushButton {
                border: 1.5px solid #8E8E93;
                border-radius: 15px;
                background: transparent;
                color: #8E8E93;
                font-size: 18px;
                font-weight: 300;
                }
                QPushButton:hover {
                border-color: #E30000;
                color: #E30000;
                background: rgba(227, 0, 0, 0,05);
                }
                QPushButton:hover {
                border-color: #E30000;
                color: #E30000;
                background: rgba(227, 0, 0, 0,05);
                }
                QPushButton:pressed {
                border-color: #E30000;
                color: #E30000;
                background: rgba(227, 0, 0, 0,05);
                }
            ''')

            if self.current_tab == "active" and not task.completed:
                circle.clicked.connect(lambda checked, tid=task.id: self.complete_task(tid))

            elif self.current_tab == "completed" and task.completed:
                circle.clicked.connect(lambda checked, tid=task.id: self.undo_task(tid))

            title_label = QLabel(task.title)

            row_layout.addWidget(title_label)
            row_layout.addStretch()
            row_layout.addWidget(circle)

            self.task_layout.addWidget(row)

    def complete_task(self, task_id: int):
        self.service.complete_task(task_id)
        self.refresh_tasks()

    def undo_task(self, task_id: int):
        self.service.undo_task(task_id)
        self.refresh_tasks()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = TaskDatabase()
    db.create_table()
    service = TaskService(db)
    window = MainWindow(service)
    window.show()
    sys.exit(app.exec())
