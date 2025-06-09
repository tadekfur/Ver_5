from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QGridLayout, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from .day_box import DayBox  # zakładamy, że DayBox jest w osobnym pliku widgets/day_box.py

DAY_BOX_WIDTH = 340   # Stała szerokość kontenera dnia (dopasuj do siebie)

class DashboardWidget(QWidget):
    def __init__(self, order_entry_widget_factory, main_window):
        super().__init__()
        self.order_entry_widget_factory = order_entry_widget_factory
        self.main_window = main_window

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header_layout = QHBoxLayout()
        label = QLabel("TABLICA ZLECEŃ")
        label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_layout.addWidget(label)
        header_layout.addStretch(1)
        self.show_done_checkbox = QCheckBox("Pokaż zrealizowane")
        self.show_done_checkbox.setChecked(False)
        header_layout.addWidget(self.show_done_checkbox)
        main_layout.addLayout(header_layout)

        # --- Dodajemy QScrollArea pionowo na całą siatkę dni ---
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # GridLayout: 4 rows x 5 columns (tygodnie x dni robocze)
        self.days_grid_container = QWidget()
        self.days_grid_layout = QGridLayout(self.days_grid_container)
        self.days_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.days_grid_layout.setSpacing(0)
        self.scroll_area.setWidget(self.days_grid_container)

        self.day_boxes = []
        self.cards_per_day = {}
        self.populate_days()
        self.show_done_checkbox.stateChanged.connect(self.refresh_cards)
        # Odświeżamy tablicę zawsze po powrocie okna na wierzch (np. po dodaniu/klonowaniu)
        self.installEventFilter(self)
        self.refresh_cards()

    def eventFilter(self, obj, event):
        if obj == self and event.type() == 24:  # QEvent.WindowActivate
            QTimer.singleShot(100, self.refresh_cards)
        return super().eventFilter(obj, event)

    def get_days(self):
        from datetime import datetime, timedelta
        today = datetime.today()
        weekday = today.weekday()
        monday_this_week = today - timedelta(days=weekday)
        weeks = []
        for week_offset in [-1, 0, 1, 2]:  # poprzedni, bieżący, 2 następne = 4 tygodnie
            monday = monday_this_week + timedelta(days=7 * week_offset)
            week_days = [monday + timedelta(days=i) for i in range(5)]
            weeks.append(week_days)
        return [d for week in weeks for d in week]

    def populate_days(self):
        for i in reversed(range(self.days_grid_layout.count())):
            widget = self.days_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        self.day_boxes = []
        self.cards_per_day = {}

        days = self.get_days()
        for idx, day in enumerate(days):
            row = idx // 5
            col = idx % 5
            box = DayBox(day, self)
            # TYLKO szerokość jest stała, wysokość automatyczna
            box.setFixedWidth(DAY_BOX_WIDTH)
            box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            self.day_boxes.append(box)
            self.days_grid_layout.addWidget(box, row, col)
            self.cards_per_day[day.strftime("%Y-%m-%d")] = box

        # Ustaw równomierne rozłożenie (każda kolumna ma ten sam stretch)
        for col in range(5):
            self.days_grid_layout.setColumnStretch(col, 1)
        for row in range(4):  # 4 tygodnie
            self.days_grid_layout.setRowStretch(row, 1)

    def resizeEvent(self, event):
        QTimer.singleShot(0, self.adjust_day_box_sizes)
        super().resizeEvent(event)

    def adjust_day_box_sizes(self):
        for box in self.day_boxes:
            if hasattr(box, 'orders_container'):
                box.orders_container.adjustSize()
            box.adjustSize()
        self.updateGeometry()

    def refresh_cards(self):
        from models.db import Session
        from sqlalchemy.orm import joinedload
        from models.order import Order
        from widgets.order_card import OrderCard  # import tutaj, żeby uniknąć cyklicznych importów
        from widgets.done_orders_store import done_orders_store

        show_done = self.show_done_checkbox.isChecked()
        # WYCZYŚĆ zamówienia w każdym DayBox
        for box in self.day_boxes:
            if hasattr(box, "clear_orders"):
                box.clear_orders()

        session = Session()
        # WYMUSZAJ NAJŚWIEŻSZE DANE Z BAZY
        session.expire_all()
        orders = session.query(Order).options(joinedload(Order.client)).order_by(Order.delivery_date.asc()).all()
        session.close()

        for order in orders:
            if order.delivery_date:
                day_str = order.delivery_date.strftime("%Y-%m-%d")
            else:
                continue
            is_done = done_orders_store.is_done(order.id)
            if show_done:
                if not is_done:
                    continue
            else:
                if is_done:
                    continue
            if day_str in self.cards_per_day:
                card = OrderCard(order, self)
                # Dodanie fiszki do DayBoxa
                self.cards_per_day[day_str].add_order(card)
                # Podłączanie sygnałów
                if hasattr(card, "arrow_btn"):
                    card.arrow_btn.clicked.connect(card.toggle_details)
                card.mouseDoubleClickEvent = lambda event, o=order: self.open_edit_order(o)
                card.setAcceptDrops(False)
        self.update()
        self.adjust_day_box_sizes()

    def archive_order_card(self, card):
        card.setParent(None)
        card.hide()

    def open_edit_order(self, order):
        w = self.order_entry_widget_factory(edit_order=order)
        w.show()
        # Automatycznie odśwież po zamknięciu okna edycji:
        if hasattr(w, "finished"):
            w.finished.connect(self.refresh_cards)

    def handle_drop(self, order_id, target_day):
        from models.db import Session
        from models.order import Order
        session = Session()
        order = session.query(Order).filter_by(id=order_id).one_or_none()
        if order:
            order.delivery_date = target_day
            session.commit()
        session.close()
        self.refresh_cards()