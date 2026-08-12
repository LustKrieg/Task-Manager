from PyQt6.QtWidgets import QTextEdit, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QEvent, QObject
from PyQt6.QtGui import QShortcut, QKeySequence, QFontMetrics, QTextCursor
from PyQt6 import sip

class TaskEditor:
    def __init__(self, main_window):
        self.main_window = main_window
        self._current_edit_finish = None

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

        edit.setMinimumWidth(0)
        edit.setMaximumWidth(16777215)

        edit.document().setDocumentMargin(0)
        edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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

        edit.setMinimumWidth(0)
        edit.setMaximumWidth(16777215)

        notes_entry.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        notes_entry.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        notes_entry.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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

        # --- Notes Height ---
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

        # --- Load Existing Notes ---
        current_notes = self.main_window.service.get_notes(task_id)
        if current_notes and current_notes.strip():
            notes_entry.setPlainText(current_notes)

        # --- Title Height ---
        fm = QFontMetrics(edit.font())
        line_height = fm.lineSpacing()

        def adjust_title_height():
            if sip.isdeleted(edit):
                return

            doc = edit.document()
            doc.setTextWidth(edit.viewport().width())
            doc_height = int(doc.size().height())

            edit.setFixedHeight(max(line_height + 4, doc_height))

        edit.document().contentsChanged.connect(adjust_title_height)

        title_label.hide()

        # --- Hide Static Labels ---
        if hasattr(title_label, '_notes_text'):
            notes_text = title_label._notes_text
            if notes_text and not sip.isdeleted(notes_text):
                notes_text.hide()

        # --- Add Editors ---
        left_layout.insertWidget(0, edit)
        left_layout.insertWidget(1, notes_entry)
        QTimer.singleShot(0, adjust_title_height)

        # --- Set focus based on clicked field ---
        if focus_on == "title":
            edit.setFocus()
            edit.moveCursor(QTextCursor.MoveOperation.End)
        else:
            notes_entry.setFocus()
            notes_entry.moveCursor(QTextCursor.MoveOperation.End)

        edit._notes_entry = notes_entry

        # --- SAVE / FNINISH ---
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
                    self.main_window.service.update_task_title(task_id, new_title)
                    if not sip.isdeleted(title_label):
                        title_label.setText(new_title)
                if new_notes is not None:
                    self.main_window.service.update_notes(task_id, new_notes)

            # --- Remove Title Editor ---
            if not sip.isdeleted(edit):
                try:
                    edit.document().contentsChanged.disconnect(adjust_title_height)
                except TypeError:
                    pass
                left_layout.removeWidget(edit)
                edit.setParent(None)
                edit.deleteLater()

            # --- Remove Notes Editor ---
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

            # --- Restore Title ---
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

            # --- Restore Notes ---
            if hasattr(title_label, '_notes_text'):
                notes_text = title_label._notes_text
                if notes_text and not sip.isdeleted(notes_text):
                    if new_notes and new_notes.strip():
                        notes_text.setText(new_notes)
                        notes_text.show()
                    else:
                        notes_text.hide()

            self._current_edit_finish = None
            self.main_window.task_input.clearFocus()

            if not skip_refresh:
                self.main_window.refresh_tasks()

        self._current_edit_finish = finish

        # --- Enter / Escape Handling --- 
        notes_filter = NotesEnterFilter(notes_entry, finish)
        notes_entry.installEventFilter(notes_filter)
        notes_entry._entry_filter = notes_filter

        QShortcut(QKeySequence("Ctrl+Return"), edit).activated.connect(lambda: finish(True))
        QShortcut(QKeySequence("Escape"), edit).activated.connect(lambda: finish(True))

        filter_obj = EnterFilter(edit, finish)
        edit.installEventFilter(filter_obj)
        edit._enter_filter = filter_obj

    def close_current_edit(self, save=True, skip_refresh=False):
        if self._current_edit_finish:
            self._current_edit_finish(save, skip_refresh)

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

