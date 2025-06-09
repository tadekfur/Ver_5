import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QFrame, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication, QIcon
from widgets.order_entry_widget import OrderEntryWidget
from models.db import create_db
from widgets.orders_db_widget import OrdersDBWidget
from widgets.clients_db_widget import ClientsDBWidget
from widgets.dashboard_widget import DashboardWidget
from widgets.production_sort_dialog import ProductionSortDialog

DONE_ORDERS_FILE = "done_orders_store.json"

BTN_SIDEBAR = {
    "dashboard": """
        QPushButton {
            font-size: 15px;
            font-weight: bold;
            min-height: 38px;
            border-radius: 8px;
            border: 2px solid #197a3d;
            background: #eaffea;
            color: #197a3d;
            margin: 4px 0;
        }
        QPushButton:hover {
            background: #c5ffd7;
        }
        QPushButton[selected="true"] {
            background: #e53935;
            color: #fff;
            border: 2px solid #b71c1c;
        }
    """,
    "order": """
        QPushButton {
            font-size: 15px;
            font-weight: bold;
            min-height: 38px;
            border-radius: 8px;
            border: 2px solid #2267d4;
            background: #e7f1ff;
            color: #2267d4;
            margin: 4px 0;
        }
        QPushButton:hover {
            background: #b8d5fe;
        }
        QPushButton[selected="true"] {
            background: #e53935;
            color: #fff;
            border: 2px solid #b71c1c;
        }
    """,
    "clients": """
        QPushButton {
            font-size: 15px;
            font-weight: bold;
            min-height: 38px;
            border-radius: 8px;
            border: 2px solid #d35400;
            background: #fff4e0;
            color: #d35400;
            margin: 4px 0;
        }
        QPushButton:hover {
            background: #ffe0b2;
        }
        QPushButton[selected="true"] {
            background: #e53935;
            color: #fff;
            border: 2px solid #b71c1c;
        }
    """,
    "orders": """
        QPushButton {
            font-size: 15px;
            font-weight: bold;
            min-height: 38px;
            border-radius: 8px;
            border: 2px solid #8e44ad;
            background: #f5e6ff;
            color: #8e44ad;
            margin: 4px 0;
        }
        QPushButton:hover {
            background: #e0cfff;
        }
        QPushButton[selected="true"] {
            background: #e53935;
            color: #fff;
            border: 2px solid #b71c1c;
        }
    """,
}

def create_color_legend():
    legend_widget = QWidget()
    legend_layout = QVBoxLayout(legend_widget)
    legend_layout.setContentsMargins(0, 0, 0, 0)
    legend_layout.setSpacing(5)

    header = QLabel("dni do wysyłki")
    header.setFont(QFont("Segoe UI", 10, QFont.Bold))
    header.setAlignment(Qt.AlignLeft)
    legend_layout.addWidget(header)

    # (color, opis)
    legend_data = [
        ("#ff6666", "po terminie"),
        ("#ffe600", "dzień wysyłki"),
        ("#ffc966", "1 dzień"),
        ("#b2d7ff", "2 dni"),
        ("#b5e7b2", "3 dni"),
        ("#cccccc", "4 dni"),
    ]

    for color, text in legend_data:
        row = QHBoxLayout()
        row.setSpacing(6)
        # Kwadrat z kolorem
        color_box = QLabel()
        color_box.setFixedSize(20, 20)
        # Minimalne zaokrąglenie rogów i tło
        color_box.setStyleSheet(f"background:{color}; border-radius:4px; border:1px solid #aaa;")
        row.addWidget(color_box)
        # Opis
        txt = QLabel(text)
        txt.setFont(QFont("Segoe UI", 9))
        row.addWidget(txt)
        row.addStretch(1)
        legend_layout.addLayout(row)

    legend_layout.addStretch(1)
    return legend_widget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zarządzanie zleceniami")
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "clipboard-list-check.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            self.setWindowIcon(QIcon.fromTheme("applications-office"))
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.btn_dashboard = QPushButton("TABLICA ZLECEŃ")
        self.btn_order = QPushButton("Wystaw zamówienie")
        self.btn_clients = QPushButton("Baza klientów")
        self.btn_orders = QPushButton("Baza zamówień")
        self.btn_production_sort = QPushButton("Zestawienie\nprodukcji")
        self.btn_production_sort.setMinimumHeight(52)
        self.btn_production_sort.setMaximumHeight(70)
        self.btn_production_sort.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                font-weight: bold;
                min-height: 52px;
                max-height: 70px;
                border-radius: 8px;
                border: 2px solid #197a3d;
                background: #eaffea;
                color: #197a3d;
                margin: 4px 0;
                padding: 4px;
                white-space: normal;
            }
            QPushButton:hover { background: #b3d8fd; }
        """)

        self.btn_dashboard.setStyleSheet(BTN_SIDEBAR["dashboard"])
        self.btn_order.setStyleSheet(BTN_SIDEBAR["order"])
        self.btn_clients.setStyleSheet(BTN_SIDEBAR["clients"])
        self.btn_orders.setStyleSheet(BTN_SIDEBAR["orders"])

        sidebar = QFrame()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet("""
            QFrame {
                background: #f2f2f2;
                border-right: 1.5px solid #d1d5db;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 24, 12, 12)
        sidebar_layout.setSpacing(16)
        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_order)
        sidebar_layout.addWidget(self.btn_clients)
        sidebar_layout.addWidget(self.btn_orders)
        sidebar_layout.addWidget(self.btn_production_sort)
        sidebar_layout.addStretch(1)

        # DODAJ LEGENDĘ KOLORÓW NA DOLE, LEWA STRONA
        legend = create_color_legend()
        sidebar_layout.addWidget(legend, alignment=Qt.AlignLeft | Qt.AlignBottom)

        self.pages = QStackedWidget()
        self.dashboard = DashboardWidget(
            lambda **kwargs: self.create_order_entry_widget(**kwargs), self
        )
        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(QWidget())
        self.clients_db = ClientsDBWidget()
        self.pages.addWidget(self.clients_db)
        self.orders_db = OrdersDBWidget(
            order_entry_factory=lambda **kwargs: self.create_order_entry_widget(**kwargs),
            refresh_dashboard_callback=self.dashboard.refresh_cards,
            show_order_entry_callback=self.show_order_entry
        )
        self.pages.addWidget(self.orders_db)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)

        self.sidebar_buttons = [
            (self.btn_dashboard, "dashboard"),
            (self.btn_order, "order"),
            (self.btn_clients, "clients"),
            (self.btn_orders, "orders")
        ]

        for btn, _ in self.sidebar_buttons:
            btn.setProperty("selected", False)
            btn.setCheckable(False)

        self.btn_dashboard.clicked.connect(lambda: self.switch_page(0, self.btn_dashboard, "dashboard"))
        self.btn_order.clicked.connect(lambda: self.show_order_entry())
        self.btn_clients.clicked.connect(lambda: self.switch_page(2, self.btn_clients, "clients"))
        self.btn_orders.clicked.connect(lambda: self.switch_page(3, self.btn_orders, "orders"))
        self.btn_production_sort.clicked.connect(self.show_production_sort_dialog)

        self.switch_page(0, self.btn_dashboard, "dashboard")

    def set_sidebar_active(self, active_btn, active_name):
        for btn, name in self.sidebar_buttons:
            if btn is active_btn:
                btn.setProperty("selected", True)
                btn.setStyleSheet(BTN_SIDEBAR[name])
                btn.style().unpolish(btn)
                btn.style().polish(btn)
            else:
                btn.setProperty("selected", False)
                btn.setStyleSheet(BTN_SIDEBAR[name])
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    def switch_page(self, idx, active_button, active_name):
        self.pages.setCurrentIndex(idx)
        self.set_sidebar_active(active_button, active_name)
        if idx == 3 and hasattr(self, "orders_db"):
            self.orders_db.refresh_orders()
        if idx == 0:
            old_widget = self.pages.widget(1)
            if old_widget is not None and old_widget.__class__.__name__ != "QWidget":
                self.pages.removeWidget(old_widget)
                old_widget.deleteLater()
                self.pages.insertWidget(1, QWidget())

    def show_order_entry(self, edit_order=None, copy_order=None, after_save_callback=None, new_client=None):
        from PySide6.QtCore import QTimer
        def after_save():
            self.dashboard.refresh_cards()
            QTimer.singleShot(0, lambda: self.switch_page(0, self.btn_dashboard, "dashboard"))
        widget = self.create_order_entry_widget(
            edit_order=edit_order,
            copy_order=copy_order,
            after_save_callback=after_save_callback or after_save,
            new_client=new_client
        )
        old_widget = self.pages.widget(1)
        self.pages.removeWidget(old_widget)
        old_widget.deleteLater()
        self.pages.insertWidget(1, widget)
        self.pages.setCurrentIndex(1)
        self.set_sidebar_active(self.btn_order, "order")

    def create_order_entry_widget(self, edit_order=None, copy_order=None, after_save_callback=None, new_client=None):
        return OrderEntryWidget(
            edit_order=edit_order,
            copy_order=copy_order,
            after_save_callback=after_save_callback,
            main_window=self,
            new_client=new_client
        )

    def show_production_sort_dialog(self):
        dlg = ProductionSortDialog(self)
        dlg.exec()

def main():
    create_db()
    app = QApplication(sys.argv)
    main_window = MainWindow()
    screen = QGuiApplication.primaryScreen()
    if screen:
        available_geometry = screen.availableGeometry()
        main_window.setGeometry(available_geometry)
        main_window.showMaximized()
    else:
        main_window.showMaximized()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()