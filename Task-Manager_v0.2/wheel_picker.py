import math
from PyQt6.QtCore import (
    Qt, pyqtSignal, pyqtProperty, QPropertyAnimation, QEasingCurve,
    QDate, QSize,
)
from PyQt6.QtGui import QPainter, QFont, QColor
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout


class WheelPicker(QWidget):
    """iOS-style 3D cylinder picker.

    Items sit on a virtual cylinder and recede into depth as they move
    away from the centre.  Wheel, click-drag, and arrow keys all work.
    """

    value_changed = pyqtSignal(int)

    # ── Visual tuning ────────────────────────────────────────────────
    VISIBLE_ITEMS = 5
    ITEM_HEIGHT   = 22
    ANGLE_STEP    = 24.0     # degrees between adjacent items
    WHEEL_RADIUS  = 60.0
    FONT_POINT    = 12.0

    COLOR_ACTIVE   = "#1C1C1E"   # centred item
    COLOR_INACTIVE = "#5A5A5F"   # off-centre items

    def __init__(self, items, parent=None, selected_index=0, width=78):
        super().__init__(parent)
        self._items = list(items)
        self._offset = float(selected_index)
        self._target = float(selected_index)
        self._last_emit = selected_index

        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setFixedSize(width, self.ITEM_HEIGHT * self.VISIBLE_ITEMS)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("background: transparent;")

        self._dragging = False
        self._drag_y = 0.0
        self._drag_offset = 0.0

    # ── Animated property ────────────────────────────────────────────
    def _get_offset(self): return self._offset

    def _set_offset(self, value):
        self._offset = value
        self.update()
        idx = int(round(self._offset))
        if idx != self._last_emit:
            self._last_emit = idx
            self.value_changed.emit(idx)

    offset = pyqtProperty(float, _get_offset, _set_offset)

    # ── Public API ───────────────────────────────────────────────────
    def current_index(self): return int(round(self._offset))

    def set_current_index(self, index, animate=False):
        index = max(0, min(len(self._items) - 1, index))
        self._target = float(index)
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._offset)
            self._anim.setEndValue(self._target)
            self._anim.start()
        else:
            self._anim.stop()
            self._set_offset(self._target)

    # ── Input ────────────────────────────────────────────────────────
    def wheelEvent(self, event):
        notches = event.angleDelta().y() / 120.0
        if notches == 0:
            return
        step = -1 if notches > 0 else 1
        self.set_current_index(self.current_index() + step, animate=True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self.set_current_index(self.current_index() - 1, animate=True)
        elif event.key() == Qt.Key.Key_Down:
            self.set_current_index(self.current_index() + 1, animate=True)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._anim.stop()
            self._dragging = True
            self._drag_y = event.position().y()
            self._drag_offset = self._offset

    def mouseMoveEvent(self, event):
        if not self._dragging:
            return
        dy = event.position().y() - self._drag_y
        self._set_offset(self._drag_offset - dy / self.ITEM_HEIGHT)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.set_current_index(self.current_index(), animate=True)

    # ── Paint ────────────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        cx = self.width() / 2.0
        cy = self.height() / 2.0
        offset = self._offset

        # Only iterate over indices near the current offset.  Items that are a
        # multiple of 360°/ANGLE_STEP indices apart share the same on-screen
        # angle, so an unbounded loop paints them on top of each other.
        span = self.VISIBLE_ITEMS
        lo = max(0, int(math.floor(offset)) - span)
        hi = min(len(self._items), int(math.ceil(offset)) + span + 1)

        for i in range(lo, hi):
            theta  = (i - offset) * math.radians(self.ANGLE_STEP)
            cos_t  = math.cos(theta)
            if cos_t <= 0.05:
                continue
            y = cy + math.sin(theta) * self.WHEEL_RADIUS
            if y < -self.ITEM_HEIGHT or y > self.height() + self.ITEM_HEIGHT:
                continue

            scale   = cos_t
            opacity = min(1.0, cos_t ** 1.5)

            font = self.font()
            font.setPointSizeF(self.FONT_POINT * scale)
            font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(font)

            painter.save()
            painter.setOpacity(opacity)

            is_center = abs(i - offset) < 0.5
            painter.setPen(QColor(self.COLOR_ACTIVE if is_center
                                else self.COLOR_INACTIVE))

            metrics = painter.fontMetrics()
            text = str(self._items[i])
            text_w = metrics.horizontalAdvance(text)
            text_h = metrics.ascent()

            painter.drawText(
                int(cx - text_w / 2),
                int(y + text_h / 2),
                text,
            )
            painter.restore()


class MonthYearSelector(QWidget):
    """Two WheelPickers side-by-side: month on the left, year on the right."""

    value_changed      = pyqtSignal(int, int)   # year, month (1-12)
    dismiss_requested  = pyqtSignal()           # user tapped outside the wheels

    MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    YEAR_RANGE   = 10

    def __init__(self, parent=None, year=None, month=None):
        super().__init__(parent)
        today = QDate.currentDate()
        year  = year  or today.year()
        month = month or today.month()

        base = today.year()
        self._years = list(range(base - self.YEAR_RANGE, base + self.YEAR_RANGE + 1))

        self.setStyleSheet("background: white;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(0)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)

        self.month_wheel = WheelPicker(self.MONTH_LABELS,
                                       selected_index=month - 1)
        self.year_wheel  = WheelPicker([str(y) for y in self._years],
                                       selected_index=self._years.index(year))
        row.addWidget(self.month_wheel)
        row.addWidget(self.year_wheel)
        outer.addLayout(row)

        self.month_wheel.value_changed.connect(self._on_change)
        self.year_wheel.value_changed.connect(self._on_change)

    def _on_change(self, _index):
        year  = self._years[self.year_wheel.current_index()]
        month = self.month_wheel.current_index() + 1
        self.value_changed.emit(year, month)

    def set_value(self, year, month):
        self.month_wheel.set_current_index(month - 1, animate=False)
        self.year_wheel.set_current_index(self._years.index(year), animate=False)

    def sizeHint(self):
        m, y = self.month_wheel, self.year_wheel
        return QSize(m.width() + y.width() + 2 + 12,
                     max(m.height(), y.height()) + 12)

    def mousePressEvent(self, event):
        # Tap on the background (not on a wheel) → ask parent to switch back
        pos = event.position().toPoint()
        on_month = self.month_wheel.geometry().contains(pos)
        on_year  = self.year_wheel.geometry().contains(pos)
        if not (on_month or on_year):
            self.dismiss_requested.emit()
        super().mousePressEvent(event)