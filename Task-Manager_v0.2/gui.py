import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QScrollArea, QFrame, QSizePolicy, QTextEdit, QSpacerItem, QMenu
)
from PyQt6.QtCore import Qt, QEvent, QObject, QTimer
from PyQt6.QtGui import (QFont, QShortcut, QKeySequence, QFontMetrics,
    QTextCursor, QPainter, QColor, QPixmap, QIcon, QAction)
from database import TaskDatabase
from service import TaskService
from PyQt6 import sip

# From other files
from datetime import date
from styles import SIDEBAR_BUTTON_STYLE
from sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self, service: TaskService):
        super().__init__()
        self.current_tab = "active"
        self.service = service
        self.setWindowTitle("Task Manager")
        self.setGeometry(100, 100, 750, 500)
        self.pending_timers = {}
        self.search_text = ""

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
        content_layout.addWidget(self.title_label)

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
        self.close_current_edit(True, skip_refresh=True)

        for timer in self.pending_timers.values():
            timer.stop()
            timer.deleteLater()
        self.pending_timers.clear()

        for i in reversed(range(self.task_layout.count())):
            widget = self.task_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # --- Curcle Button ---
        if self.current_tab == "active":
            tasks = self.service.get_active_tasks()
        elif self.current_tab == "completed":
            tasks = self.service.get_completed_tasks()
        else:
            tasks = self.service.get_deleted_tasks()

        if self.search_text:
            tasks = [
                t for t in tasks
                if self.search_text in t.title.lower()
                or self.search_text in t.notes.lower()
            ]
        for task in tasks:
            row = QWidget()
            row.setObjectName("taskRow")
            row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            row_layout = QHBoxLayout()
            row.setLayout(row_layout)
            row.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            row.customContextMenuRequested.connect(lambda pos, tid=task.id: self.show_context_menu(pos, tid))
            row_layout.setContentsMargins(0, 0, 0, 0)

            # Circle color logic
            if self.current_tab == "active":
                circle_text = "○"
                circle_color = "#8E8E93"
            elif self.current_tab == "completed":
                circle_text = "◉"
                circle_color = "#E30000"
            else:
                if task.completed:
                    circle_text = "◉"
                    circle_color = "#E30000"
                else:
                    circle_text = "○"
                    circle_color = "#8E8E93"

            if not task.completed:
                hover_color = "#E30000"
            else:
                hover_color = "#8E8E93"

            circle = QPushButton(circle_text)
            circle.setFixedSize(30, 30)
            circle.setStyleSheet(f"""
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

            if self.current_tab == "active" and not task.completed:
                circle.clicked.connect(lambda checked, tid=task.id, btn=circle: self.handle_circle_click(tid, btn))

            elif self.current_tab == "completed" and task.completed:
                circle.clicked.connect(lambda checked, tid=task.id: self.undo_task(tid))

            # Left side: Title + Date (Vertical)
            left_column = QWidget()
            left_column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            left_layout = QVBoxLayout(left_column)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(2)

            # --- Title Label ---
            title_label = QLabel(task.title)
            title_label.setStyleSheet("color: black; font-size: 15px;")
            title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            title_label.setWordWrap(True)

            if self.current_tab == "active":
                def make_press_handler(lbl, tid, t):
                    def handler(event):
                        if event.button() == Qt.MouseButton.LeftButton:
                            QTimer.singleShot(0, lambda: self.start_editing(lbl, tid, t))
                    return handler
                title_label.mousePressEvent = make_press_handler(title_label, task.id, task.title)
            
            date_label = QLabel(task.created_at.strftime('%b %d, %I:%M %p'))
            date_label.setStyleSheet("color: #8E8E93; font-size: 11px;")

            # --- Notes ---
            notes_text = None
            if task.notes and task.notes.strip():
                notes_text = QLabel(task.notes)
                notes_text.setStyleSheet(''' color: #8E8E93; font-size: 12px; ''')
                notes_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                notes_text.setWordWrap(True)

                title_label._notes_text = notes_text

                if self.current_tab == "active":
                    def make_note_handler(lbl, tid, t):
                        def handler(event):
                            if event.button() == Qt.MouseButton.LeftButton:
                                QTimer.singleShot(0, lambda: self.start_editing(lbl, tid, t, focus_on="notes"))
                        return handler
                    notes_text.mousePressEvent = make_note_handler(title_label, task.id, task.title)

            left_layout.addWidget(title_label)
            if notes_text:
                left_layout.addWidget(notes_text)
            left_layout.addWidget(date_label)

            row_layout.addWidget(left_column)
            row_layout.setStretchFactor(left_column, 1)
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

    def handle_circle_click(self, task_id: int, circle_button):
        if task_id in self.pending_timers:
            timer = self.pending_timers.pop(task_id)
            timer.stop()
            timer.deleteLater()
            circle_button.setText("○")
            circle_button.setStyleSheet('''
            QPushButton {
                border: none;
                background: transparent;
                color: #8E8E93;
                font-size: 22px;
                font-weight: 300;
            }
            QPushButton:hover {color: #E30000;}
            QPushButton:pressed {color: #E30000;}
            ''')
            return

        circle_button.setText("◉")
        circle_button.setStyleSheet('''
            QPushButton {
                border: none;
                background: transparent;
                color: #E30000;
                font-size: 22px;
                font-weight: 300;
            }
            QPushButton:hover { color: #E30000; }
            QPushButton:pressed { color: #E30000; }
        ''')

        from PyQt6.QtCore import QTimer
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.complete_task(task_id))
        timer.start(1500)
        self.pending_timers[task_id] = timer

    def start_editing(self, title_label, task_id, current_title, focus_on="title"):
        self.close_current_edit(True, skip_refresh=True)

        if sip.isdeleted(title_label):
            return

        left_column = title_label.parent()
        left_layout = left_column.layout()

        left_column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        left_layout.setSpacing(0)

        # --- Title Entry ---
        edit = QTextEdit()
        edit.setPlainText(current_title)
        edit.document().setDocumentMargin(0)
        edit.setStyleSheet('''
            QTextEdit {
                border: none;
                background: white;
                color: black;
                font-size: 15px;
                padding: 0px;
            }
        ''')
        edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        edit.document().setDocumentMargin(0)

        # --- Notes entry ---
        notes_entry = QTextEdit()
        notes_entry.setPlaceholderText("Notes")
        notes_entry.setStyleSheet('''
            QTextEdit {
                border: none;
                background: white;
                color: #8E8E93;
                font-size: 12px;
                padding: 0px;
            }
        ''')
        notes_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        notes_entry.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        notes_entry.document().setDocumentMargin(0)

        fm_notes = QFontMetrics(notes_entry.font())
        notes_line_height = fm_notes.lineSpacing()

        def adjust_notes_height():
            if sip.isdeleted(notes_entry):
                return
            doc = notes_entry.document()
            doc.setTextWidth(notes_entry.viewport().width())
            doc_height = int(doc.size().height())
            notes_entry.setFixedHeight(max(notes_line_height + 4, doc_height))

        notes_entry.document().contentsChanged.connect(adjust_notes_height)
        QTimer.singleShot(0, adjust_notes_height)

        current_notes = self.service.get_notes(task_id)
        if current_notes and current_notes.strip():
            notes_entry.setPlainText(current_notes)

        # -- Height Adjustment ---
        fm = QFontMetrics(edit.font())
        line_height = fm.lineSpacing()

        def adjust_height():
            if sip.isdeleted(edit):
                return

            doc = edit.document()
            doc.setTextWidth(edit.viewport().width())
            doc_height = int(doc.size().height())
            edit.setFixedHeight(doc_height + 0)

        edit.document().contentsChanged.connect(adjust_height)
        QTimer.singleShot(0, adjust_height)

        title_label.hide()

        # Hide static notes if it exists
        if hasattr(title_label, '_notes_text'):
            notes_text = title_label._notes_text
            if notes_text and not sip.isdeleted(notes_text):
                notes_text.hide()

        left_layout.insertWidget(0, edit)
        left_layout.insertWidget(1, notes_entry)

        # --- Set focus based on clicked field ---
        if focus_on == "title":
            edit.setFocus()
            edit.moveCursor(QTextCursor.MoveOperation.End)
        else:
            notes_entry.setFocus()
            notes_entry.moveCursor(QTextCursor.MoveOperation.End)

        edit._notes_entry = notes_entry

        def finish(save=True, skip_refresh=False):
            try:
                new_title = edit.toPlainText().strip()
            except RuntimeError:
                new_title = None

            try:
                new_notes = edit._notes_entry.toPlainText().strip()
            except (RuntimeError, AttributeError):
                new_notes = None

            if save and new_title is not None:
                if new_title and new_title != current_title:
                    self.service.update_task_title(task_id, new_title)
                    if not sip.isdeleted(title_label):
                        title_label.setText(new_title)
                if new_notes is not None:
                    self.service.update_notes(task_id, new_notes)

            if not sip.isdeleted(edit):
                try:
                    edit.document().contentsChanged.disconnect(adjust_height)
                except TypeError:
                    pass
                left_layout.removeWidget(edit)
                edit.setParent(None)
                edit.deleteLater()

            if hasattr(edit, '_notes_entry') and edit._notes_entry:
                notes_entry = edit._notes_entry
                if not sip.isdeleted(notes_entry):
                    try:
                        notes_entry.document().contentsChanged.disconnect(adjust_notes_height)
                    except TypeError:
                        pass
                    left_layout.removeWidget(notes_entry)
                    notes_entry.setParent(None)
                    notes_entry.deleteLater()

            try:
                left_layout.addStretch()
                left_column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                left_layout.update()
                left_column.update()
            except RuntimeError:
                pass

            if not sip.isdeleted(title_label):
                if new_title is not None:
                    title_label.setText(new_title)
                title_label.show()

            # Restore Notes Label
            if hasattr(title_label, '_notes_text'):
                notes_text = title_label._notes_text
                if notes_text and not sip.isdeleted(notes_text):
                    if new_notes and new_notes.strip():
                        notes_text.setText(new_notes)
                        notes_text.show()
                    else:
                        notes_text.hide()

            self._current_edit_finish = None
            self.task_input.clearFocus()

            if not skip_refresh:
                self.refresh_tasks()

        self._current_edit_finish = finish

        notes_filter = NotesEnterFilter(notes_entry, finish)
        notes_entry.installEventFilter(notes_filter)
        notes_entry._entry_filter = notes_filter

        QShortcut(QKeySequence("Ctrl+Return"), edit).activated.connect(lambda: finish(True))
        QShortcut(QKeySequence("Escape"), edit).activated.connect(lambda: finish(True))

        filter_obj = EnterFilter(edit, finish)
        edit.installEventFilter(filter_obj)
        edit._enter_filter = filter_obj

    def close_current_edit(self, save=True, skip_refresh=False):
        if hasattr(self, '_current_edit_finish') and self._current_edit_finish:
            self._current_edit_finish(save, skip_refresh)

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

class EnterFilter(QObject):
    def __init__(self, edit_widget, finish_func):
        super().__init__()
        self.edit = edit_widget
        self.finish = finish_func

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return False
                self.finish(True)
                return True
        return False

class NotesEnterFilter(QObject):
    def __init__(self, notes_widget, finish_func):
        super().__init__()
        self.notes = notes_widget
        self.finish = finish_func

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return False
                self.finish(True)
                return True
        return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = TaskDatabase()
    db.create_table()
    service = TaskService(db)
    window = MainWindow(service)
    window.show()
    sys.exit(app.exec())
