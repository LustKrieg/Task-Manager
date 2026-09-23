from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QToolButton, QHBoxLayout, QVBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont


WEEKDAY_LABELS = {
    Qt.DayOfWeek.Monday:    ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    Qt.DayOfWeek.Tuesday:   ["Tu", "We", "Th", "Fr", "Sa", "Su", "Mo"],
    Qt.DayOfWeek.Wednesday: ["We", "Th", "Fr", "Sa", "Su", "Mo", "Tu"],
    Qt.DayOfWeek.Thursday:  ["Th", "Fr", "Sa", "Su", "Mo", "Tu", "We"],
    Qt.DayOfWeek.Friday:    ["Fr", "Sa", "Su", "Mo", "Tu", "We", "Th"],
    Qt.DayOfWeek.Saturday:  ["Sa", "Su", "Mo", "Tu", "We", "Th", "Fr"],
    Qt.DayOfWeek.Sunday:    ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"],
}

# A single day cell. Handles its own hover/selected/today styling.
class DayCell(QLabel):
    clicked = pyqtSignal(QDate)

    def __init__(self, date: QDate, current_month: int,
                 today: QDate, selected: QDate, cell_size: int = 26):
        super().__init__(str(date.day()))
        self.date = date
        self._current_month = current_month
        self._today = today
        self._selected = selected
        self._hovered = False
        self._cell_size = cell_size

        self.setFixedSize(cell_size, cell_size)
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
        font.setPointSize(10)                     # was 11 → tighter
        font.setWeight(weight)
        self.setFont(font)

        radius = self._cell_size // 2             # round pill, scales with cell
        self.setStyleSheet(
            f"QLabel {{ color: {fg}; background: {bg}; border-radius: {radius}px; }}"
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
    date_selected = pyqtSignal(QDate)

    # ── Tunable sizing (all in px) ────────────────────────────────────
    CELL_SIZE         = 26
    WEEKDAY_HEIGHT    = 16
    NAV_BUTTON_SIZE   = 20
    OUTER_MARGIN_H    = 8
    OUTER_MARGIN_V    = 6
    HEADER_MARGIN_L   = 4
    DAY_FONT_SIZE     = 10
    WEEKDAY_FONT_SIZE = 10
    MONTH_FONT_SIZE   = 13

    def __init__(self, parent=None, value=None,
                 first_day: Qt.DayOfWeek = Qt.DayOfWeek.Monday):
        super().__init__(parent)
        self._first_day = first_day

        self._selected: QDate = self._coerce_to_qdate(value) or QDate.currentDate()
        self._displayed_month: QDate = QDate(
            self._selected.year(), self._selected.month(), 1
        )
        self._day_cells: list[DayCell] = []

        self.setStyleSheet("background: white;")

        # Width = 7 cells + side margins.  Height is driven by layout.
        self.setFixedWidth(
            self.CELL_SIZE * 7 + self.OUTER_MARGIN_H * 2
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(self.OUTER_MARGIN_H, self.OUTER_MARGIN_V,
                                self.OUTER_MARGIN_H, self.OUTER_MARGIN_V)
        root.setSpacing(1)

        # ── Header: "Sep 2026"  ‹  › ──────────────────────────────────
        header = QHBoxLayout()
        header.setContentsMargins(self.HEADER_MARGIN_L, 0, 0, 0)
        header.setSpacing(0)

        self.month_label = QLabel()
        self.month_label.setStyleSheet(
            f"color: #1C1C1E; font-size: {self.MONTH_FONT_SIZE}px;"
            "font-weight: 700; background: transparent;"
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

        for col, name in enumerate(WEEKDAY_LABELS[self._first_day]):
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedSize(self.CELL_SIZE, self.WEEKDAY_HEIGHT)
            lbl.setStyleSheet(
                f"color: #8E8E93; font-size: {self.WEEKDAY_FONT_SIZE}px;"
                "font-weight: 600; background: transparent;"
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

    # Switch which weekday starts the grid (rebuilds the header).
    def set_first_day(self, first_day: Qt.DayOfWeek) -> None:
        if first_day == self._first_day:
            return
        self._first_day = first_day
        # Rebuild the weekday header labels
        for col in range(7):
            item = self.grid.itemAtPosition(0, col)
            if item and item.widget():
                item.widget().setText(WEEKDAY_LABELS[self._first_day][col])
        self._rebuild()

    # ── Internal helpers ──────────────────────────────────────────────
    @staticmethod
    def _coerce_to_qdate(value) -> QDate | None:
        if value is None:
            return None
        if isinstance(value, QDate):
            return value
        date_obj = value.date() if callable(getattr(value, "date", None)) else None
        if date_obj is None:
            return None
        return QDate(date_obj.year, date_obj.month, date_obj.day)

    def _make_nav_button(self, glyph: str) -> QToolButton:
        btn = QToolButton()
        btn.setText(glyph)
        btn.setFixedSize(self.NAV_BUTTON_SIZE, self.NAV_BUTTON_SIZE)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                color: #1C1C1E;
                font-size: 14px;
                font-weight: 700;
            }
            QToolButton:hover {
                background: #F2F2F7;
                border-radius: 4px;
            }
        """)
        return btn

    def _shift_month(self, delta: int) -> None:
        self._displayed_month = self._displayed_month.addMonths(delta)
        self._rebuild()

    # How many days before `date` belong to the previous month, given the configured first day of week.
    def _first_day_offset(self, date: QDate) -> int:
        day_index = date.dayOfWeek() - 1          # Qt: Mon=1..Sun=7 → 0..6
        first_index = self._first_day.value - 1   # same conversion
        return (day_index - first_index) % 7

    def _rebuild(self) -> None:
        for cell in self._day_cells:
            self.grid.removeWidget(cell)
            cell.deleteLater()
        self._day_cells.clear()

        year = self._displayed_month.year()
        month = self._displayed_month.month()
        self.month_label.setText(self._displayed_month.toString("MMM yyyy"))

        first = QDate(year, month, 1)
        start_offset = self._first_day_offset(first)
        start = first.addDays(-start_offset)

        today = QDate.currentDate()

        for i in range(42):          # 6 rows × 7 days → stable height
            date = start.addDays(i)
            row = i // 7 + 1         # row 0 is the weekday header
            col = i % 7
            cell = DayCell(date, month, today, self._selected,
                           cell_size=self.CELL_SIZE)
            cell.clicked.connect(self._on_cell_clicked)
            self.grid.addWidget(cell, row, col)
            self._day_cells.append(cell)

    def _on_cell_clicked(self, date: QDate) -> None:
        self._selected = date
        if (date.year() != self._displayed_month.year()
                or date.month() != self._displayed_month.month()):
            self._displayed_month = QDate(date.year(), date.month(), 1)
            self._rebuild()
        else:
            for cell in self._day_cells:
                cell.set_selected(date)
        self.date_selected.emit(date)