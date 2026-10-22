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
                self.messages,
                self.chunk_received.emit,
                should_stop=self.isInterruptionRequested
            )
            self.finished_ok.emit(full_text)
        except Exception as exc:
            self.finished_error.emit(str(exc))

class TitleWorker(QThread):
    title_generated = pyqtSignal(str)

    def __init__(self, provider, first_message, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.first_message = first_message

    def run(self):
        try:
            title = self.provider.generate_title(self.first_message)
            if title:
                self.title_generated.emit(title)
        except Exception as e:
            print(f"TitleWorker crashed: {e}")