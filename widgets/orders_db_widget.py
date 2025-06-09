from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QSizePolicy, QDialog,
    QAbstractItemView, QFrame, QScrollArea, QGroupBox, QGridLayout
)
from PySide6.QtGui import QFont, QColor, QDesktopServices
from PySide6.QtCore import Qt, QSettings, QUrl
import os
from decimal import Decimal, InvalidOperation

from models.db import Session
from models.client import Client
from models.order import Order
from models.orderitem import OrderItem
from widgets.order_details_dialog import OrderDetailsDialog
from printing.order_confirmation import export_order_to_pdf
from printing.production_ticket import export_production_ticket

class OrdersDBWidget(QWidget):
    SETTINGS_ORG = "twoja_aplikacja"
    SETTINGS_APP = "orders_db_widget"
    SETTINGS_COLUMNS = "column_widths"

    def __init__(self, order_entry_factory, refresh_dashboard_callback=None, show_order_entry_callback=None, main_window=None, parent=None):
        super().__init__(parent)
        self.order_entry_factory = order_entry_factory
        self.refresh_dashboard_callback = refresh_dashboard_callback
        self.show_order_entry_callback = show_order_entry_callback
        self.main_window = main_window
        self.selected_order_id = None

        layout = QVBoxLayout(self)
        title = QLabel("Baza zamówień")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        buttons_row = QHBoxLayout()

        self.button_green = """
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                min-height: 28px;
                border-radius: 7px;
                border: 2px solid #197a3d;
                background: #eaffea;
                color: #197a3d;
                padding: 7px 20px;
                margin: 0 6px;
            }
            QPushButton:disabled {
                background: #f4f4f4;
                color: #a0a0a0;
                border: 2px solid #cccccc;
            }
            QPushButton:pressed {
                background: #c5ffd7;
            }
        """
        self.button_red = self.button_green.replace('#197a3d', '#c60000').replace('#eaffea', '#ffeaea').replace('#c5ffd7', '#ffd2d2')
        self.button_orange = self.button_green.replace('#197a3d', '#d35400').replace('#eaffea', '#fff4e0').replace('#c5ffd7', '#ffe0b2')
        self.button_violet = self.button_green.replace('#197a3d', '#8e44ad').replace('#eaffea', '#f5e6ff').replace('#c5ffd7', '#e0cfff')

        self.button_view = QPushButton("Zobacz zamówienie")
        self.button_view.setStyleSheet(self.button_violet)
        self.button_view.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.button_view.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.button_edit = QPushButton("Edycja zamówienia")
        self.button_edit.setStyleSheet(self.button_green)
        self.button_edit.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.button_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.button_copy = QPushButton("Wystaw jako nowe")
        self.button_copy.setStyleSheet(self.button_orange)
        self.button_copy.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.button_copy.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.button_delete = QPushButton("Usuń")
        self.button_delete.setStyleSheet(self.button_red)
        self.button_delete.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.button_delete.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.button_print = QPushButton("Drukuj wybrane zamówienie")
        self.button_print.setStyleSheet(self.button_green)
        self.button_print.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.button_print.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        for button in (self.button_view, self.button_edit, self.button_copy, self.button_delete, self.button_print):
            button.setEnabled(False)
            button.setMinimumWidth(button.sizeHint().width() + 18)
            buttons_row.addWidget(button)
        buttons_row.addStretch(1)
        layout.addLayout(buttons_row)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Nr zamówienia", "Data zamówienia", "Data wysyłki",
            "Klient", "Telefon", "Miasto", "Termin płatności", "Cena", "Dane produkcji", "Uwagi"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setFont(QFont("Segoe UI", 11))
        self.table.horizontalHeader().setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background: #409cff;
                color: white;
            }
        """)

        layout.addWidget(self.table, stretch=1)

        self.table.itemSelectionChanged.connect(self.handle_selection)
        self.button_view.clicked.connect(self.view_selected_order)
        self.button_edit.clicked.connect(self.edit_selected_order)
        self.button_copy.clicked.connect(self.copy_selected_order)
        self.button_delete.clicked.connect(self.delete_selected_order)
        self.button_print.clicked.connect(self.show_print_dialog)

        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.restore_column_widths()
        self.table.horizontalHeader().sectionResized.connect(self.save_column_widths)

        self.refresh_orders()

        self.button_styles = {
            "green": self.button_green,
            "red": self.button_red,
            "orange": self.button_orange,
            "violet": self.button_violet
        }

    def save_column_widths(self):
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        widths = [self.table.columnWidth(i) for i in range(self.table.columnCount())]
        settings.setValue(self.SETTINGS_COLUMNS, widths)

    def restore_column_widths(self):
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        widths = settings.value(self.SETTINGS_COLUMNS)
        if widths and len(widths) == self.table.columnCount():
            for i, width in enumerate(widths):
                try:
                    self.table.setColumnWidth(i, int(width))
                except Exception:
                    pass

    def format_currency(self, value):
        try:
            d = Decimal(str(value).replace(',', '.'))
        except (InvalidOperation, TypeError):
            return str(value)
        return f"{d:,.2f} zł".replace(',', ' ').replace('.', ',')

    def refresh_orders(self):
        session = Session()
        def safe_order_number(order):
            try:
                return int(order.order_number)
            except Exception:
                return order.order_number or ""
        orders = session.query(Order).all()
        orders = sorted(orders, key=safe_order_number)

        self.table.setRowCount(0)
        for row_index, order in enumerate(orders):
            row = self.table.rowCount()
            self.table.insertRow(row)
            client = session.query(Client).filter_by(id=order.client_id).first()
            items = session.query(OrderItem).filter_by(order_id=order.id).all()
            production_items = [
                (item, index) for index, item in enumerate(items)
                if item.width is not None and str(item.width).strip() != ""
            ]

            order_number_item = QTableWidgetItem(order.order_number or "")
            order_number_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row, 0, order_number_item)

            order_date_item = QTableWidgetItem(order.order_date.strftime("%Y-%m-%d") if order.order_date else "")
            order_date_item.setFont(QFont("Segoe UI", 10))
            self.table.setItem(row, 1, order_date_item)

            delivery_date_item = QTableWidgetItem(order.delivery_date.strftime("%Y-%m-%d") if order.delivery_date else "")
            delivery_date_item.setFont(QFont("Segoe UI", 10))
            self.table.setItem(row, 2, delivery_date_item)

            client_name_item = QTableWidgetItem(client.name if client else "")
            client_name_item.setFont(QFont("Segoe UI", 10))
            self.table.setItem(row, 3, client_name_item)

            client_phone_item = QTableWidgetItem(client.phone if client else "")
            client_phone_item.setFont(QFont("Segoe UI", 10))
            self.table.setItem(row, 4, client_phone_item)

            client_city_item = QTableWidgetItem(client.city if client else "")
            client_city_item.setFont(QFont("Segoe UI", 10))
            self.table.setItem(row, 5, client_city_item)

            payment_term = getattr(order, "payment_term", None)
            if not payment_term and items:
                payment_term = getattr(items[0], "payment_term", None)
            if not payment_term:
                payment_term = ""
            payment_term_item = QTableWidgetItem(payment_term)
            payment_term_item.setFont(QFont("Segoe UI", 10))
            self.table.setItem(row, 6, payment_term_item)

            # Cena - obsługa wielu pozycji, wartości walutowe
            if production_items:
                price_lines = []
                for item, _ in production_items:
                    width = str(getattr(item, "width", "") or "")
                    height = str(getattr(item, "height", "") or "")
                    price = getattr(item, "price", "")
                    price_type = getattr(item, "price_type", "")
                    if price:
                        prefix = f"{width}x{height}/"
                        formatted_price = self.format_currency(price)
                        if "rolk" in (price_type or "").lower():
                            price_line = f"{prefix}{formatted_price} /rolkę"
                        else:
                            price_line = f"{prefix}{formatted_price} /tyś."
                        price_lines.append(price_line)
                price_display = "\n".join(price_lines)
            else:
                price_display = ""
            price_item = QTableWidgetItem(price_display)
            price_item.setFont(QFont("Segoe UI", 10))
            price_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row, 7, price_item)

            def format_prod(item):
                # Zamiana zam.tyś na zam. rolki
                return (
                    f"{item.material}, {item.width}x{item.height} mm, {item.ordered_quantity} {item.quantity_type}, "
                    f"nawój: {item.roll_length}, rdzeń: {item.core}, "
                    f"cena: {item.price} {item.price_type}, "
                    f"zam. rolki: {getattr(item, 'zam_rolki', '')}"
                )
            prod_col = 8
            if len(production_items) == 0:
                production_label = QLabel("Brak pozycji")
                production_label.setFont(QFont("Segoe UI", 10))
                self.table.setCellWidget(row, prod_col, production_label)
                self.table.setRowHeight(row, 28)
            else:
                production_widget = QWidget()
                production_layout = QVBoxLayout(production_widget)
                production_layout.setContentsMargins(0, 0, 0, 0)
                production_layout.setSpacing(0)
                height_per_row = 20
                total_prod_rows = 0
                for (item, index) in production_items:
                    label = QLabel(f"{index+1}. {format_prod(item)}")
                    label.setFont(QFont("Segoe UI", 10))
                    production_layout.addWidget(label)
                    total_prod_rows += 1
                    if index < len(production_items)-1:
                        separator = QFrame()
                        separator.setFrameShape(QFrame.HLine)
                        separator.setFrameShadow(QFrame.Sunken)
                        separator.setStyleSheet("color: #e0e0e0;")
                        production_layout.addWidget(separator)
                        total_prod_rows += 1
                self.table.setCellWidget(row, prod_col, production_widget)
                self.table.setRowHeight(row, max(28, total_prod_rows * height_per_row))

            notes_item = QTableWidgetItem(order.notes or "")
            notes_item.setFont(QFont("Segoe UI", 10))
            self.table.setItem(row, 9, notes_item)

            base_background = "#ffffff" if row_index % 2 == 0 else "#f2f2f2"
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                if item:
                    item.setBackground(QColor(base_background))
            cell_widget = self.table.cellWidget(row, prod_col)
            if cell_widget:
                cell_widget.setStyleSheet(f"background: {base_background};")
        session.close()
        self.button_view.setEnabled(False)
        self.button_edit.setEnabled(False)
        self.button_copy.setEnabled(False)
        self.button_delete.setEnabled(False)
        self.button_print.setEnabled(False)
        self.selected_order_id = None
        self.table.clearSelection()
        self.highlight_selected_row()

    def handle_selection(self):
        selected = self.table.selectedItems()
        if not selected:
            self.button_view.setEnabled(False)
            self.button_edit.setEnabled(False)
            self.button_copy.setEnabled(False)
            self.button_delete.setEnabled(False)
            self.button_print.setEnabled(False)
            self.selected_order_id = None
            self.table.clearSelection()
            self.highlight_selected_row()
            return
        row = self.table.currentRow()
        order_number = self.table.item(row, 0).text()
        session = Session()
        order = session.query(Order).filter_by(order_number=order_number).first()
        self.selected_order_id = order.id if order else None
        session.close()
        if self.selected_order_id:
            self.button_view.setEnabled(True)
            self.button_edit.setEnabled(True)
            self.button_copy.setEnabled(True)
            self.button_delete.setEnabled(True)
            self.button_print.setEnabled(True)
        else:
            self.button_view.setEnabled(False)
            self.button_edit.setEnabled(False)
            self.button_copy.setEnabled(False)
            self.button_delete.setEnabled(False)
            self.button_print.setEnabled(False)
        self.highlight_selected_row()

    def highlight_selected_row(self):
        pass

    def get_selected_order(self):
        if not self.selected_order_id:
            return None
        session = Session()
        order = session.query(Order).filter_by(id=self.selected_order_id).first()
        session.close()
        return order

    def view_selected_order(self):
        order = self.get_selected_order()
        if not order:
            return
        self.show_order_dialog_v4(order)

    def edit_selected_order(self):
        order = self.get_selected_order()
        if not order:
            return
        def after_edit():
            self.refresh_orders()
            if self.refresh_dashboard_callback:
                self.refresh_dashboard_callback()
        EditDialog = self._get_edit_dialog_class()
        edit_dialog = EditDialog(self.order_entry_factory, order, after_edit, self.button_styles)
        edit_dialog.exec()

    def _get_edit_dialog_class(self):
        class EditOrderDialog(QDialog):
            def __init__(self, order_entry_factory, order, after_save_callback, button_styles):
                super().__init__()
                self.setWindowTitle("WPROWADŹ DANE ZAMÓWIENIA")
                self.setAttribute(Qt.WA_DeleteOnClose)
                layout = QVBoxLayout(self)
                layout.setContentsMargins(12, 12, 12, 12)
                layout.setSpacing(10)

                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setMinimumWidth(900)
                self.order_widget = order_entry_factory(edit_order=order, after_save_callback=after_save_callback)
                self.order_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                scroll.setWidget(self.order_widget)
                layout.addWidget(scroll, stretch=1)

                button_row = QHBoxLayout()
                button_row.setSpacing(20)
                button_row.addStretch(1)

                # Szukamy przycisku zapisz, lub tworzymy nowy jeśli nie ma
                if hasattr(self.order_widget, "form_layout"):
                    found = False
                    for i in reversed(range(self.order_widget.form_layout.count())):
                        item = self.order_widget.form_layout.itemAt(i)
                        widget = item.widget()
                        if isinstance(widget, QPushButton) and "zapisz" in widget.text().lower():
                            self.save_button = widget
                            self.save_button.setParent(None)
                            self.save_button.setStyleSheet(button_styles["green"])
                            self.save_button.setMinimumWidth(160)
                            self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                            button_row.addWidget(self.save_button)
                            self.save_button.clicked.disconnect()
                            self.save_button.clicked.connect(self.save_and_close)
                            found = True
                            break
                    if not found:
                        self.save_button = QPushButton("💾 Zapisz zamówienie")
                        self.save_button.setStyleSheet(button_styles["green"])
                        self.save_button.setMinimumWidth(160)
                        self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                        button_row.addWidget(self.save_button)
                        self.save_button.clicked.connect(self.save_and_close)
                else:
                    self.save_button = QPushButton("💾 Zapisz zamówienie")
                    self.save_button.setStyleSheet(button_styles["green"])
                    self.save_button.setMinimumWidth(160)
                    self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                    button_row.addWidget(self.save_button)
                    self.save_button.clicked.connect(self.save_and_close)

                self.cancel_button = QPushButton("Anuluj")
                self.cancel_button.setStyleSheet(button_styles["red"])
                self.cancel_button.setMinimumWidth(120)
                self.cancel_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                button_row.addWidget(self.cancel_button)
                self.cancel_button.clicked.connect(self.reject)
                layout.addLayout(button_row)

                self.setMinimumWidth(1200)
                self.resize(1300, 700)

            def save_and_close(self):
                if hasattr(self.order_widget, "save_order"):
                    self.order_widget.save_order()
                if hasattr(self.order_widget, "after_save_callback") and callable(self.order_widget.after_save_callback):
                    self.order_widget.after_save_callback()
                self.accept()
        return EditOrderDialog

    def copy_selected_order(self):
        order = self.get_selected_order()
        if not order:
            return
        if self.show_order_entry_callback:
            self.show_order_entry_callback(
                copy_order=order
            )
        else:
            order_widget = self.order_entry_factory(
                copy_order=order
            )
            order_widget.show()

    def _after_save_new_order(self):
        self.refresh_orders()
        if self.refresh_dashboard_callback:
            self.refresh_dashboard_callback()
        if self.main_window:
            self.main_window.switch_page(0, self.main_window.btn_dashboard, "dashboard")

    def delete_selected_order(self):
        order = self.get_selected_order()
        if not order:
            return
        session = Session()
        result = QMessageBox.question(self, "Potwierdź usunięcie", f"Czy na pewno usunąć zamówienie nr {order.order_number}?", QMessageBox.Yes | QMessageBox.No)
        if result != QMessageBox.Yes:
            session.close()
            return
        session.query(OrderItem).filter_by(order_id=order.id).delete()
        session.delete(order)
        session.commit()
        session.close()
        self.refresh_orders()
        if self.refresh_dashboard_callback:
            self.refresh_dashboard_callback()

    def show_order_dialog_v4(self, order):
        session = Session()
        client = session.query(Client).filter_by(id=order.client_id).first()
        items = session.query(OrderItem).filter_by(order_id=order.id).all()
        session.close()
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Podgląd zamówienia {order.order_number}")
        dialog.resize(900, 700)
        layout = QVBoxLayout(dialog)
        groupbox_ordering = QGroupBox("Dane zamawiającego")
        grid = QGridLayout(groupbox_ordering)
        labels = [
            ("Firma:", client.name if client else ""),
            ("Nr klienta:", str(client.client_number) if client else ""),
            ("Osoba kontaktowa:", client.contact_person if client else ""),
            ("Telefon:", client.phone if client else ""),
            ("E-mail:", client.email if client else ""),
            ("Ulica i nr:", client.street if client else ""),
            ("Kod pocztowy:", client.postal_code if client else ""),
            ("Miasto:", client.city if client else ""),
            ("NIP:", client.nip if client else ""),
        ]
        for i, (label, value) in enumerate(labels):
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Segoe UI", 11, QFont.Bold))
            grid.addWidget(label_widget, i, 0)
            value_widget = QLabel(value)
            value_widget.setFont(QFont("Segoe UI", 11))
            grid.addWidget(value_widget, i, 1)
        layout.addWidget(groupbox_ordering)
        groupbox_production = QGroupBox("Dane produkcji")
        production_layout = QVBoxLayout(groupbox_production)
        any_row = False
        for index, item in enumerate(items):
            if not item.width or str(item.width).strip() == "":
                continue
            # Zamiana zam.tyś na zam. rolki
            label = QLabel(
                f"{index+1}. Szer: {item.width} mm, Wys: {item.height} mm, "
                f"Materiał: {item.material}, Ilość: {item.ordered_quantity} {item.quantity_type}, "
                f"Nawój: {item.roll_length}, Rdzeń: {item.core}, "
                f"Cena: {item.price} {item.price_type}, Zam. rolki: {getattr(item, 'zam_rolki', '')}"
            )
            label.setFont(QFont("Segoe UI", 11))
            production_layout.addWidget(label)
            any_row = True
        if not any_row:
            production_layout.addWidget(QLabel("Brak pozycji z wypełnioną szerokością"))
        layout.addWidget(groupbox_production)
        groupbox_address = QGroupBox("Adres dostawy")
        grid_address = QGridLayout(groupbox_address)
        address_labels = [
            ("Nazwa firmy:", client.delivery_company if client else ""),
            ("Ulica i nr:", client.delivery_street if client else ""),
            ("Kod pocztowy:", client.delivery_postal_code if client else ""),
            ("Miejscowość:", client.delivery_city if client else "")
        ]
        for i, (label, value) in enumerate(address_labels):
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Segoe UI", 11, QFont.Bold))
            grid_address.addWidget(label_widget, i, 0)
            value_widget = QLabel(value)
            value_widget.setFont(QFont("Segoe UI", 11))
            grid_address.addWidget(value_widget, i, 1)
        layout.addWidget(groupbox_address)
        groupbox_notes = QGroupBox("Uwagi do zamówienia")
        notes_layout = QVBoxLayout(groupbox_notes)
        notes = QLabel(order.notes or "")
        notes.setFont(QFont("Segoe UI", 11))
        notes_layout.addWidget(notes)
        layout.addWidget(groupbox_notes)
        dialog.exec()

    def show_print_dialog(self):
        if not self.selected_order_id:
            QMessageBox.warning(self, "Brak zamówienia", "Nie wybrano zamówienia do wydruku.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Wybierz typ wydruku")
        dialog.resize(400, 120)
        layout = QVBoxLayout(dialog)
        info = QLabel("Wybierz rodzaj wydruku PDF:")
        info.setFont(QFont("Segoe UI", 11))
        layout.addWidget(info)
        row = QHBoxLayout()
        button_client = QPushButton("Dla klienta")
        button_production = QPushButton("Produkcja")
        button_client.setFont(QFont("Segoe UI", 12, QFont.Bold))
        button_production.setFont(QFont("Segoe UI", 12, QFont.Bold))
        button_client.setStyleSheet(self.button_green)
        button_production.setStyleSheet(self.button_orange)
        row.addWidget(button_client)
        row.addWidget(button_production)
        layout.addLayout(row)

        def print_for_client_action():
            dialog.accept()
            self.print_for_client()
        def print_for_production_action():
            dialog.accept()
            self.print_for_production()

        button_client.clicked.connect(print_for_client_action)
        button_production.clicked.connect(print_for_production_action)
        dialog.exec()

    def print_for_client(self):
        order = self.get_selected_order()
        if not order:
            QMessageBox.warning(self, "Brak zamówienia", "Nie wybrano zamówienia do wydruku.")
            return
        session = Session()
        client = session.query(Client).filter_by(id=order.client_id).first()
        items = session.query(OrderItem).filter_by(order_id=order.id).all()
        session.close()
        output_dir = r"c:\potwierdzenia dla klienta"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in client.name)
        safe_order = "".join(c for c in str(order.order_number) if c.isalnum() or c in "._-")
        filename = f"{safe_order}_{safe_name}.pdf"
        output_path = os.path.join(output_dir, filename)
        try:
            export_order_to_pdf(order, client, items, output_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(output_path))
        except Exception as e:
            QMessageBox.critical(self, "Błąd PDF", f"Wystąpił błąd podczas generowania PDF:\n{e}")

    def print_for_production(self):
        order = self.get_selected_order()
        if not order:
            QMessageBox.warning(self, "Brak zamówienia", "Nie wybrano zamówienia do wydruku.")
            return
        session = Session()
        client = session.query(Client).filter_by(id=order.client_id).first()
        items = session.query(OrderItem).filter_by(order_id=order.id).all()
        session.close()
        output_dir = r"c:\produkcja"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in client.name)
        safe_order = "".join(c for c in str(order.order_number) if c.isalnum() or c in "._-")
        filename = f"{safe_order}_{safe_name}_PRODUKCJA.pdf"
        output_path = os.path.join(output_dir, filename)
        try:
            export_production_ticket(order, client, items, output_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(output_path))
        except Exception as e:
            QMessageBox.critical(self, "Błąd PDF", f"Wystąpił błąd podczas generowania PDF:\n{e}")