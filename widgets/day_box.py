from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QWidget, QLabel, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QByteArray, QDataStream
from PySide6.QtGui import QFont

class DayBox(QGroupBox):
    def __init__(self, day, dashboard):
        super().__init__()
        self.day = day
        self.dashboard = dashboard
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        weekday_idx = day.weekday()
        WEEKDAYS_PL = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]
        dayname = WEEKDAYS_PL[weekday_idx]
        date_str = day.strftime("%d.%m.%Y")

        # Windows 11 pastel-like header colors
        week_colors = [
            {"bg": "#e6f0fa", "fg": "#235d9f"},
            {"bg": "#eafaea", "fg": "#2d7c31"},
            {"bg": "#fff9e1", "fg": "#a6842e"},
            {"bg": "#e6f0fa", "fg": "#235d9f"},
        ]
        week_idx = 0
        if hasattr(dashboard, "get_days"):
            days_all = dashboard.get_days()
            try:
                idx_in_all = [d.strftime("%Y-%m-%d") for d in days_all].index(day.strftime("%Y-%m-%d"))
                week_idx = idx_in_all // 5
            except Exception:
                week_idx = 0
        color = week_colors[week_idx % len(week_colors)]

        self._header_color = color['bg']
        self._header_fg = color['fg']

        self.setStyleSheet("""
            QGroupBox {
                border: 2px solid #e3e5ec;
                border-radius: 12px;
                background: #fff;
                margin-top: 8px;
            }
        """)

        self.header = QWidget(self)
        self.header_layout = QVBoxLayout(self.header)
        self.header_layout.setContentsMargins(4, 4, 4, 4)

        self.header_label = QLabel(dayname, self.header)
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet(f"background-color: {self._header_color}; color: {self._header_fg}; padding: 4px 0; border-radius: 6px;")
        self.header_label.setFont(QFont("Segoe UI Variable", 13, QFont.Bold))

        self.date_label = QLabel(date_str, self.header)
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setFont(QFont("Segoe UI Variable", 12, QFont.Bold))
        self.date_label.setStyleSheet(f"background-color: {self._header_color}; color: {self._header_fg}; padding-bottom:2px; border-radius: 6px;")

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.header)
        self.header_layout.addWidget(self.header_label)
        self.header_layout.addWidget(self.date_label)

        self.orders = []
        self.max_orders = 20

        self.orders_container = QWidget(self)
        self.orders_layout = QVBoxLayout(self.orders_container)
        self.orders_layout.setSpacing(10)
        self.orders_layout.setContentsMargins(2, 2, 2, 2)
        self.orders_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.orders_container)
        layout.addStretch(1)

    def set_header_color(self, color):
        """Pozwala dashboardowi ustawić kolor nagłówka w stylu Win11."""
        self._header_color = color
        self.header_label.setStyleSheet(f"background-color: {self._header_color}; color: {self._header_fg}; padding: 4px 0; border-radius: 6px;")
        self.date_label.setStyleSheet(f"background-color: {self._header_color}; color: {self._header_fg}; padding-bottom:2px; border-radius: 6px;")

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-order-id"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-order-id"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        data = event.mimeData().data("application/x-order-id")
        stream = QDataStream(data)
        order_id = stream.readInt32()
        if len(self.orders) >= self.max_orders:
            reply = QMessageBox.question(self, "Potwierdź",
                f"W tym dniu jest już {self.max_orders} zamówień. Czy dodać kolejne?",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return
        self.dashboard.handle_drop(order_id, self.day)
        event.acceptProposedAction()

    def add_order(self, card):
        self.orders.append(card)
        self.orders_layout.addWidget(card)
        self.orders_container.adjustSize()
        self.adjustSize()
        parent = self.parent()
        if parent:
            parent.adjustSize()

    def clear_orders(self):
        for card in self.orders:
            card.setParent(None)
            card.deleteLater()
        self.orders = []
        self.orders_container.adjustSize()
        self.adjustSize()
        parent = self.parent()
        if parent:
            parent.adjustSize()