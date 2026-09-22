from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QToolButton, QHBoxLayout, QVBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont


WEEKDAY_NAMES = [ "Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

class DayCell(QLabel):
    """A single day cell. Handles its own hover/selected/today styling."""

    clicked = pyqtSignal(QDate)

    def __init__(self, date: QDate, current_month: int, today: QDate, selected: QDate):
        super().__init__(str(date.day()))
        self.date = date
        self._current_month = current_month
        self._today = today
        self._selected = selected
        self._hovered = False

        self.setFixedSize(30, 30)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh()

    def set_selected(self, selected: QDate) -> None:
        self._selected = selected
        self._refresh()

    def _refresh(self) -> None:
        in_month = self.date.month() == self._current_month
        is_today = self.date == self._today
        is_selected = self.date == self._selected

        if is_selected:
            bg, fg, weight = "#E5E5EA", "#1C1C1E", QFont.Weight.DemiBold
        elif is_today:
            bg, fg, weight = "#DDEBFF", "#147EFB", QFont.Weight.DemiBold
        elif self._hovered:
            bg = "#F2F2F7"
            fg = "#1C1C1E" if in_month else "#C7C7CC"
            weight = QFont.Weight.Normal
        else:
            bg = "transparent"
            fg = "#1C1C1E" if in_month else "#C7C7CC"
            weight = QFont.Weight.Normal

        font = self.font()
        font.setPointSize(11)
        font.setWeight(weight)
        self.setFont(font)

        self.setStyleSheet(
            f"QLabel {{ color: {fg}; background: {bg}; border-radius: 15px; }}"
        )

    def enterEvent(self, event):
        self._hovered = True
        self._refresh()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._refresh()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.date)
        super().mousePressEvent(event)


class MiniCalendar(QWidget):
    """A compact, reusable month-view calendar.

    Emits `date_selected(QDate)` whenever the user picks a day.
    Accepts a QDate, a QDateTime, or a python `datetime` as initial value.
    """

    date_selected = pyqtSignal(QDate)

    def __init__(self, parent=None, value=None):
        super().__init__(parent)

        self._selected: QDate = self._coerce_to_qdate(value) or QDate.currentDate()
        self._displayed_month: QDate = QDate(
            self._selected.year(), self._selected.month(), 1
        )
        self._day_cells: list[DayCell] = []

        self.setStyleSheet("background: white;")
        self.setMinimumWidth(240)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(2)

        # ── Header: "Sep 2026"  ‹  › ──────────────────────────────────
        header = QHBoxLayout()
        header.setContentsMargins(6, 0, 2, 0)
        header.setSpacing(0)

        self.month_label = QLabel()
        self.month_label.setStyleSheet(
            "color: #1C1C1E; font-size: 14px; font-weight: 700; background: transparent;"
        )
        header.addWidget(self.month_label)
        header.addStretch()

        self.prev_btn = self._make_nav_button("‹")
        self.next_btn = self._make_nav_button("›")
        self.prev_btn.clicked.connect(lambda: self._shift_month(-1))
        self.next_btn.clicked.connect(lambda: self._shift_month(1))
        header.addWidget(self.prev_btn)
        header.addWidget(self.next_btn)
        root.addLayout(header)

        # ── Weekday header + day grid ─────────────────────────────────
        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)

        for col, name in enumerate(WEEKDAY_NAMES):
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedSize(30, 18)
            lbl.setStyleSheet(
                "color: #8E8E93; font-size: 11px; font-weight: 600; background: transparent;"
            )
            self.grid.addWidget(lbl, 0, col)

        root.addLayout(self.grid)
        self._rebuild()

    # ── Public API ────────────────────────────────────────────────────
    def selected_date(self) -> QDate:
        return self._selected

    def set_selected_date(self, value) -> None:
        qdate = self._coerce_to_qdate(value)
        if qdate is None:
            return
        self._selected = qdate
        self._displayed_month = QDate(qdate.year(), qdate.month(), 1)
        self._rebuild()

    # ── Internal helpers ──────────────────────────────────────────────
    @staticmethod
    def _coerce_to_qdate(value) -> QDate | None:
        if value is None:
            return None
        if isinstance(value, QDate):
            return value
        # QDateTime.date() -> QDate ; python datetime.date() -> date
        date_obj = value.date() if callable(getattr(value, "date", None)) else None
        if date_obj is None:
            return None
        return QDate(date_obj.year, date_obj.month, date_obj.day)

    def _make_nav_button(self, glyph: str) -> QToolButton:
        btn = QToolButton()
        btn.setText(glyph)
        btn.setFixedSize(22, 22)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                color: #1C1C1E;
                font-size: 15px;
                font-weight: 700;
            }
            QToolButton:hover {
                background: #F2F2F7;
                border-radius: 5px;
            }
        """)
        return btn

    def _shift_month(self, delta: int) -> None:
        self._displayed_month = self._displayed_month.addMonths(delta)
        self._rebuild()

    def _rebuild(self) -> None:
        # Wipe old day cells (weekday header stays in row 0)
        for cell in self._day_cells:
            self.grid.removeWidget(cell)
            cell.deleteLater()
        self._day_cells.clear()

        year = self._displayed_month.year()
        month = self._displayed_month.month()
        self.month_label.setText(self._displayed_month.toString("MMM yyyy"))

        first = QDate(year, month, 1)
        # Qt dayOfWeek: Mon=1 ... Sun=7.  Sun-first offset = dayOfWeek % 7.
        start_offset = first.dayOfWeek() % 7
        start = first.addDays(-start_offset)

        today = QDate.currentDate()

        for i in range(42):          # always 6 rows × 7 days for stable layout
            date = start.addDays(i)
            row = i // 7 + 1         # row 0 is weekday header
            col = i % 7
            cell = DayCell(date, month, today, self._selected)
            cell.clicked.connect(self._on_cell_clicked)
            self.grid.addWidget(cell, row, col)
            self._day_cells.append(cell)

    def _on_cell_clicked(self, date: QDate) -> None:
        self._selected = date
        # Clicking a trailing/leading day jumps to that month
        if (date.year() != self._displayed_month.year()
                or date.month() != self._displayed_month.month()):
            self._displayed_month = QDate(date.year(), date.month(), 1)
            self._rebuild()
        else:
            for cell in self._day_cells:
                cell.set_selected(date)
        self.date_selected.emit(date)