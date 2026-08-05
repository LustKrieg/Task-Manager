from PyQt6.QtWidgets import QWidget, QSizePolicy, QHBoxLayout

class TaskRow(QWidget):
    def __init__(self, task, current_tab):
        super().__init__()

        self.task = task
        self.current_tab = current_tab

        self.setObjectName("taskRow")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.row_layout = QHBoxLayout(self)
        self.row_layout.setContentsMargins(0, 0, 0, 0)