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
        self.current_tab = "active"
        self.service = service
        self.setWindowTitle("Task Manager")
        self.setGeometry(100, 100, 750, 500)

        # --- Central Widget ---
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet('''
            QWidget {
            background: #F5F5F7;
            border-right: 1px solid #E5E5EA;
            }
        ''')
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setContentsMargins(8, 20, 8, 20)

        # --- Tab buttons ---
        self.active_tab = QPushButton("Active")
        self.completed_tab = QPushButton("Completed")
        self.trash_tab = QPushButton("Recently Deleted")

        # Styling Bar Tabs
        for tab in (self.active_tab, self.completed_tab, self.trash_tab):
            tab.setFlat(True)
            tab.setStyleSheet('''
                QPushButton{
                border: none;
                padding: 10px 14px;
                font-size: 14px;
                font=weight: 500;
                color: #8E8E93;
                background: transparent;
                text-align: left;
                border-radius: 8px;
                margin: 2px 0px;
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

        sidebar_layout.addWidget(self.active_tab)
        sidebar_layout.addWidget(self.completed_tab)
        sidebar_layout.addWidget(self.trash_tab)
        sidebar_layout.addStretch()

        # --- CONTENT (Right) ---
        content = QWidget()
        content.setStyleSheet("background: white;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(15)

        # --- Title ---
        self.title_label = QLabel("Active")
        self.title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        content_layout.addWidget(self.title_label)

        # --- Add Task Row ---
        add_layout = QHBoxLayout()
        add_layout.setSpacing(10)

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("New Reminder")
        self.task_input.returnPressed.connect(self.add_task)

        add_btn = QPushButton("Add")
        add_btn.setObjectName("addButton")
        add_btn.clicked.connect(self.add_task)

        add_layout.addWidget(self.task_input)
        add_layout.addWidget(add_btn)
        content_layout.addLayout(add_layout)

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

        scroll.setWidget(self.task_container)
        content_layout.addWidget(scroll)

        # --- Add sidebar and content to main layout ---
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)
        main_layout.setStretchFactor(content, 1)

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

        titles = {"active": "Active", "completed": "Completed", "trash": "Recently Deleted"}
        self.title_label.setText(titles[tab_name])
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

            circle = QPushButton("○" if not task.completed else "◉")
            circle.setFixedSize(30, 30)
            circle.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    color: #8E8E93;
                    font-size: 22px;
                    font-weight: 300;
                }
                QPushButton:hover {
                    color: #E30000;
                }
                QPushButton:pressed {
                    color: #E30000;
                }
            """)

            if self.current_tab == "active" and not task.completed:
                circle.clicked.connect(lambda checked, tid=task.id: self.complete_task(tid))

            elif self.current_tab == "completed" and task.completed:
                circle.clicked.connect(lambda checked, tid=task.id: self.undo_task(tid))

            title_label = QLabel(task.title)

            row_layout.addWidget(title_label)
            row_layout.addStretch()
            row_layout.addWidget(circle)

            self.task_layout.addWidget(row)

            separator = QWidget()
            separator.setFixedHeight(1)
            separator.setStyleSheet("background-color: #D1D1D6;")
            self.task_layout.addWidget(separator)

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
