from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from localization import tr
from styles import ROUNDED_MENU_STYLE

class MessageBubble(QWidget):
    def __init__(self, text, is_user, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        bubble.setMaximumWidth(440)

        if is_user:
            bubble.setStyleSheet(
                "QLabel {"
                "background: #DDEBFF; color: #1C1C1E;"
                "border-radius: 14px; padding: 8px 12px;"
                "font-size: 13px;"
                "}"
            )
            layout.addStretch(1)
            layout.addWidget(bubble, 0)
        else:
            bubble.setStyleSheet(
                "QLabel {"
                "background: #F1F2F4; color: #1C1C1E;"
                "border-radius: 14px; padding: 8px 12px;"
                "font-size: 13px;"
                "}"
            )
            layout.addWidget(bubble, 0)
            layout.addStretch(1)

class ChatInput(QPlainTextEdit):
    send_requested = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)   # shift+enter → newline
                return
            self.send_requested.emit()          # enter → send
            event.accept()
            return
        super().keyPressEvent(event)

class AIChatView(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.current_conversation_id = None
        self.setStyleSheet("background: #FFFFFF;")

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.history_sidebar = QWidget()
        self.history_sidebar.setFixedWidth(238)
        self.history_sidebar.setStyleSheet("background: #F5F5F7;")
        sidebar_layout = QVBoxLayout(self.history_sidebar)
        sidebar_layout.setContentsMargins(16, 18, 14, 16)
        sidebar_layout.setSpacing(12)

        sidebar_header = QHBoxLayout()
        self.back_button = QToolButton()
        self.back_button.setText("\u2190")
        self.back_button.setToolTip(tr("Back to tasks"))
        self.back_button.setAccessibleName(tr("Back to tasks"))
        self.back_button.setFixedSize(34, 34)
        self.back_button.setStyleSheet("""
            QToolButton {
                border: none;
                border-radius: 6px;
                background: transparent;
                color: #3A3A3C;
                font-size: 20px;
            }
            QToolButton:hover { background: #E7E7EA; }
        """)
        self.back_button.clicked.connect(self.back_requested)
        sidebar_header.addWidget(self.back_button)
        sidebar_header.addStretch()
        sidebar_layout.addLayout(sidebar_header)

        self.history_title = QLabel(tr("Chat History"))
        self.history_title.setFont(QFont("Arial", 12, QFont.Weight.DemiBold))
        self.history_title.setStyleSheet("color: #636366; padding: 3px 2px;")
        sidebar_layout.addWidget(self.history_title)

        self.conversation_list = QListWidget()
        self.conversation_list.setSelectionMode(
            QListWidget.SelectionMode.SingleSelection
        )
        self.conversation_list.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
                outline: none;
            }
            QListWidget::item {
                color: #3A3A3C;
                border-radius: 6px;
                padding: 9px 8px;
            }
            QListWidget::item:selected { background: #E1E2E5; color: #202124; }
            QListWidget::item:hover:!selected { background: #EBECEE; }
        """)
        self.conversation_list.currentItemChanged.connect(
            self._on_conversation_selected
        )
        self.conversation_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.conversation_list.customContextMenuRequested.connect(self._on_conversation_context_menu)
        sidebar_layout.addWidget(self.conversation_list, 1)

        self.history_empty_label = QLabel(tr("Start a new chat to get going."))
        self.history_empty_label.setWordWrap(True)
        self.history_empty_label.setStyleSheet(
            "color: #8E8E93; font-size: 12px; padding: 0 4px;"
        )
        sidebar_layout.addWidget(self.history_empty_label)
        root_layout.addWidget(self.history_sidebar)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFixedWidth(1)
        divider.setStyleSheet("color: #E5E5EA; background: #E5E5EA;")
        root_layout.addWidget(divider)

        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(26, 18, 26, 18)
        chat_layout.setSpacing(14)

        heading_group = QVBoxLayout()
        heading_group.setSpacing(3)
        self.title_label = QLabel(tr("AI Chat"))
        self.title_label.setFont(QFont("Arial", 19, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #202124;")
        self.status_label = QLabel(
            tr("Messages are saved locally. AI replies aren't connected yet.")
        )
        self.status_label.setStyleSheet("color: #8E8E93; font-size: 12px;")
        heading_group.addWidget(self.title_label)
        heading_group.addWidget(self.status_label)

        chat_header = QHBoxLayout()
        chat_header.addLayout(heading_group)
        chat_header.addStretch()
        self.new_chat_button = QToolButton()
        self.new_chat_button.setText("+")
        self.new_chat_button.setToolTip(tr("New Chat"))
        self.new_chat_button.setAccessibleName(tr("New Chat"))
        self.new_chat_button.setFixedSize(34, 34)
        self.new_chat_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_chat_button.setStyleSheet("""
            QToolButton {
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                background: #FFFFFF;
                color: #202124;
                font-size: 20px;
            }
            QToolButton:hover { background: #ECEDEF; }
        """)
        self.new_chat_button.clicked.connect(self.start_new_chat)
        chat_header.addWidget(self.new_chat_button)
        chat_layout.addLayout(chat_header)

        self.message_scroll = QScrollArea()
        self.message_scroll.setWidgetResizable(True)
        self.message_scroll.setStyleSheet("""
            QScrollArea { border: none; background: #FFFFFF; }
            QScrollBar:vertical {
                background: transparent; width: 8px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #C1C1C6; border-radius: 4px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.message_container = QWidget()
        self.message_container.setStyleSheet("background: #FFFFFF;")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(4, 4, 4, 4)
        self.message_layout.setSpacing(8)
        self.message_layout.addStretch(1)

        self.message_scroll.setWidget(self.message_container)
        chat_layout.addWidget(self.message_scroll, 1)

        composer = QFrame()
        composer.setStyleSheet("""
            QFrame {
                background: #F5F5F7;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
            }
            QPlainTextEdit {
                background: transparent;
                border: none;
                color: #1C1C1E;
                padding: 8px 10px;
            }
            QPlainTextEdit QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 4px 2px 4px 0;
            }
            QPlainTextEdit QScrollBar::handle:vertical {
                background: #C1C1C6;
                border-radius: 3px;
                min-height: 12px;
            }
            QPlainTextEdit QScrollBar::handle:vertical:hover {
                background: #8E8E93;
            }
            QPlainTextEdit QScrollBar::add-line:vertical,
            QPlainTextEdit QScrollBar::sub-line:vertical {
                height: 0;
            }
            QPlainTextEdit QScrollBar::add-page:vertical,
            QPlainTextEdit QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                background: #3A3A3C;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:disabled { background: #D1D1D6; }
        """)
        composer_layout = QHBoxLayout(composer)
        composer_layout.setContentsMargins(8, 6, 8, 6)
        composer_layout.setSpacing(8)
        self.message_input = ChatInput()
        self.message_input.setPlaceholderText(tr("Message"))
        self.message_input.setFixedHeight(54)
        self.message_input.textChanged.connect(self._update_send_state)
        self.message_input.send_requested.connect(self.send_message)
        composer_layout.addWidget(self.message_input, 1)

        self.send_button = QPushButton("\u2191")
        self.send_button.setToolTip(tr("Send"))
        self.send_button.setAccessibleName(tr("Send"))
        self.send_button.setFixedSize(38, 38)
        self.send_button.clicked.connect(self.send_message)
        composer_layout.addWidget(self.send_button)
        chat_layout.addWidget(composer)
        root_layout.addWidget(chat_panel, 1)

        self._reload_conversations()
        self._update_send_state()

    def _reload_conversations(self, select_id=None):
        conversations = self.service.get_chat_conversations()
        self.conversation_list.blockSignals(True)
        self.conversation_list.clear()
        selected_item = None
        for conversation in conversations:
            item = QListWidgetItem(conversation["title"] or tr("New Chat"))
            item.setData(Qt.ItemDataRole.UserRole, conversation["id"])
            self.conversation_list.addItem(item)
            if conversation["id"] == select_id:
                selected_item = item

        if selected_item is None and conversations:
            selected_item = self.conversation_list.item(0)
        self.conversation_list.setCurrentItem(selected_item)
        self.conversation_list.blockSignals(False)
        self.history_empty_label.setVisible(not conversations)

        if selected_item is None:
            self.current_conversation_id = None
            self.message_input.clear()
            self.title_label.setText(tr("AI Chat"))
        else:
            self._load_conversation(selected_item)

    def _on_conversation_selected(self, current, _previous):
        if current is not None:
            self._load_conversation(current)

    def _on_conversation_context_menu(self, pos):
        item = self.conversation_list.itemAt(pos)
        if item is None:
            return
        conversation_id = item.data(Qt.ItemDataRole.UserRole)
        current_title = item.text()

        menu = QMenu(self.conversation_list)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        menu.setStyleSheet(ROUNDED_MENU_STYLE)
        menu.addAction(
            tr("Rename"),
            lambda: self._rename_conversation(conversation_id, current_title),
        )
        menu.addAction(
            tr("Delete Chat"),
            lambda: self._delete_conversation(conversation_id),
        )
        menu.exec(self.conversation_list.mapToGlobal(pos))

    def _rename_conversation(self, conversation_id, current_title):
        new_title, ok = QInputDialog.getText(
            self,
            tr("Rename Chat"),
            tr("Enter a new name:"),
            text=current_title,
        )
        if not ok:
            return
        new_title = new_title.strip()
        if not new_title or new_title == current_title:
            return
        self.service.update_chat_conversation_title(conversation_id, new_title)
        self._reload_conversations(select_id=conversation_id)

    def _delete_conversation(self, conversation_id):
        keep_id = self.current_conversation_id
        if keep_id == conversation_id:
            keep_id = None
        self.service.delete_chat_conversation(conversation_id)
        self._reload_conversations(select_id=keep_id)

    def _load_conversation(self, item):
        self.current_conversation_id = item.data(Qt.ItemDataRole.UserRole)
        self._clear_messages()
        for message in self.service.get_chat_messages(self.current_conversation_id):
            self._append_bubble(
                message["content"],
                is_user=(message["role"] == "user"),
            )
        self.title_label.setText(item.text())
        self._scroll_to_bottom()

    def _clear_messages(self):
        while self.message_layout.count() > 1:
            item = self.message_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _append_bubble(self, text, is_user):
        bubble = MessageBubble(text, is_user)
        self.message_layout.insertWidget(
            self.message_layout.count() - 1, bubble
        )

    def _scroll_to_bottom(self):
        QTimer.singleShot(
            0,
            lambda: self.message_scroll.verticalScrollBar().setValue(
                self.message_scroll.verticalScrollBar().maximum()
            ),
        )

    def start_new_chat(self):
        conversation_id = self.service.create_chat_conversation()
        self.message_input.clear()
        self._reload_conversations(select_id=conversation_id)
        self.message_input.setFocus()

    def send_message(self):
        content = self.message_input.toPlainText().strip()
        if not content:
            return
        if self.current_conversation_id is None:
            self.current_conversation_id = self.service.create_chat_conversation()

        conversation_id = self.current_conversation_id
        self.service.add_chat_message(conversation_id, content)
        self.message_input.clear()
        self._reload_conversations(select_id=conversation_id)
        self.message_input.setFocus()

    def _update_send_state(self):
        self.send_button.setEnabled(bool(self.message_input.toPlainText().strip()))

    def retranslate_ui(self):
        self.back_button.setToolTip(tr("Back to tasks"))
        self.back_button.setAccessibleName(tr("Back to tasks"))
        self.new_chat_button.setToolTip(tr("New Chat"))
        self.new_chat_button.setAccessibleName(tr("New Chat"))
        self.history_title.setText(tr("Chat History"))
        self.history_empty_label.setText(tr("Start a new chat to get going."))
        self.status_label.setText(
            tr("Messages are saved locally. AI replies aren't connected yet.")
        )
        self.message_input.setPlaceholderText(tr("Message"))
        self.send_button.setToolTip(tr("Send"))
        self.send_button.setAccessibleName(tr("Send"))
        for row, conversation in enumerate(self.service.get_chat_conversations()):
            item = self.conversation_list.item(row)
            if item is not None and not conversation["title"]:
                item.setText(tr("New Chat"))
