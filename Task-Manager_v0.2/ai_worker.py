from PyQt6.QtCore import QThread, pyqtSignal


class AIWorker(QThread):
    chunk_received = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    finished_error = pyqtSignal(str)

    def __init__(self, provider, messages, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.messages = messages

    def run(self):
        try:
            full_text = self.provider.chat_stream(
                self.messages, self.chunk_received.emit
            )
            self.finished_ok.emit(full_text)
        except Exception as exc:
            self.finished_error.emit(str(exc))