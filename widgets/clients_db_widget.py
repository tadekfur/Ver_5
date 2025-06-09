from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QLineEdit, QDialog, QFormLayout, QMessageBox, QScrollArea, QSizePolicy, QComboBox
)
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtCore import Qt, QSettings
from models.db import Session
from models.client import Client, CLIENT_NR_START

class ClientEditDialog(QDialog):
    def __init__(self, client=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edycja klienta" if client else "Dodaj klienta")
        self.client = client
        layout = QVBoxLayout(self)

        base_font = self.font()
        base_point_size = base_font.pointSizeF()
        if base_point_size <= 0: base_point_size = 10
        bigger_font = QFont(base_font)
        bigger_font.setPointSizeF(base_point_size * 1.2)
        self.setFont(bigger_font)

        session = Session()
        if client:
            nr = client.client_number
        else:
            last = session.query(Client).order_by(Client.client_number.desc()).first()
            if last and last.client_number and last.client_number.isdigit():
                next_nr = max(int(last.client_number) + 1, CLIENT_NR_START)
            else:
                next_nr = CLIENT_NR_START
            nr = f"{next_nr:06d}"
        session.close()

        nr_font = QFont(bigger_font)
        nr_font.setPointSizeF(bigger_font.pointSizeF() * 1.3)
        self.nr_edit = QLineEdit(nr)
        self.nr_edit.setFont(nr_font)
        self.nr_edit.setMaxLength(6)
        nr_label = QLabel("Numer klienta:")
        nr_label.setFont(nr_font)
        nr_row = QHBoxLayout()
        nr_row.addWidget(nr_label)
        nr_row.addWidget(self.nr_edit)
        layout.addLayout(nr_row)

        form = QFormLayout()
        self.name_edit = QLineEdit(client.name if client else "")
        self.short_name_edit = QLineEdit(getattr(client, "short_name", "") if client else "")
        self.contact_edit = QLineEdit(client.contact_person if client else "")
        self.phone_edit = QLineEdit(client.phone if client else "")
        self.email_edit = QLineEdit(client.email if client else "")
        self.street_edit = QLineEdit(client.street if client else "")
        self.postal_edit = QLineEdit(client.postal_code if client else "")
        self.city_edit = QLineEdit(client.city if client else "")
        self.nip_edit = QLineEdit(client.nip if client else "")
        self.delivery_company_edit = QLineEdit(client.delivery_company if client else "")
        self.delivery_street_edit = QLineEdit(client.delivery_street if client else "")
        self.delivery_postal_edit = QLineEdit(client.delivery_postal_code if client else "")
        self.delivery_city_edit = QLineEdit(client.delivery_city if client else "")

        form.addRow("Nazwa firmy:", self.name_edit)
        form.addRow("Nazwa skróc.:", self.short_name_edit)
        form.addRow("Osoba kontaktowa:", self.contact_edit)
        form.addRow("Telefon:", self.phone_edit)
        form.addRow("E-mail:", self.email_edit)
        form.addRow("Ulica i nr:", self.street_edit)
        form.addRow("Kod pocztowy:", self.postal_edit)
        form.addRow("Miasto:", self.city_edit)
        form.addRow("NIP:", self.nip_edit)
        form.addRow("Dostawa: Firma:", self.delivery_company_edit)
        form.addRow("Dostawa: Ulica i nr:", self.delivery_street_edit)
        form.addRow("Dostawa: Kod pocztowy:", self.delivery_postal_edit)
        form.addRow("Dostawa: Miejscowość:", self.delivery_city_edit)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_save = QPushButton("Zapisz")
        btn_cancel = QPushButton("Anuluj")
        btn_save.setFont(bigger_font)
        btn_cancel.setFont(bigger_font)
        btn_save.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                min-height: 36px;
                border-radius: 7px;
                border: 2px solid #197a3d;
                background: #eaffea;
                color: #197a3d;
            }
            QPushButton:pressed {
                background: #c5ffd7;
            }
        """)
        btn_cancel.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                min-height: 36px;
                border-radius: 7px;
                border: 2px solid #c60000;
                background: #ffeaea;
                color: #c60000;
            }
            QPushButton:pressed {
                background: #ffd2d2;
            }
        """)
        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

        self.setLayout(layout)
        self.resize(int(500*1.2), int(600*1.2))

    def get_data(self):
        return {
            "client_number": self.nr_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "short_name": self.short_name_edit.text().strip(),
            "contact_person": self.contact_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "street": self.street_edit.text().strip(),
            "postal_code": self.postal_edit.text().strip(),
            "city": self.city_edit.text().strip(),
            "nip": self.nip_edit.text().strip(),
            "delivery_company": self.delivery_company_edit.text().strip(),
            "delivery_street": self.delivery_street_edit.text().strip(),
            "delivery_postal_code": self.delivery_postal_edit.text().strip(),
            "delivery_city": self.delivery_city_edit.text().strip(),
        }

class ClientsDBWidget(QWidget):
    SETTINGS_ORG = "twoja_aplikacja"
    SETTINGS_APP = "clients_db_widget"
    SETTINGS_COLUMNS = "column_widths"

    SEARCH_FIELDS = [
        ("Nazwa skróc.", "short_name"),
        ("Numer klienta", "client_number"),
        ("Nazwa", "name"),
        ("NIP", "nip"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Baza klientów")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        btns_row = QHBoxLayout()

        # --- KOMÓRKA ROZWIJANA + POLE WYSZUKIWANIA + PRZYCISK ---
        self.search_combo = QComboBox()
        for label, _ in self.SEARCH_FIELDS:
            self.search_combo.addItem(label)
        self.search_combo.setMinimumWidth(140)
        self.search_combo.setMaximumWidth(180)
        self.search_combo.setFont(QFont("Segoe UI", 12))
        btns_row.addWidget(self.search_combo)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Wpisz szukaną frazę...")
        self.search_edit.setMinimumWidth(180)
        self.search_edit.setMaximumWidth(320)
        self.search_edit.setFont(QFont("Segoe UI", 12))
        btns_row.addWidget(self.search_edit)

        self.btn_search = QPushButton("Wyszukaj")
        btn_search_style = """
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                min-height: 36px;
                border-radius: 7px;
                border: 2px solid #2267d4;
                background: #e6f0ff;
                color: #2267d4;
            }
            QPushButton:disabled {
                background: #f4f4f4;
                color: #a0a0a0;
                border: 2px solid #cccccc;
            }
            QPushButton:pressed {
                background: #cbe2ff;
            }
        """
        self.btn_search.setStyleSheet(btn_search_style)
        btns_row.addWidget(self.btn_search)

        self.btn_add = QPushButton("Dodaj klienta")
        self.btn_edit = QPushButton("Edytuj")
        self.btn_delete = QPushButton("Usuń")

        btn_style = """
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                min-height: 36px;
                border-radius: 7px;
                border: 2px solid #197a3d;
                background: #eaffea;
                color: #197a3d;
            }
            QPushButton:disabled {
                background: #f4f4f4;
                color: #a0a0a0;
                border: 2px solid #cccccc;
            }
        """
        self.btn_add.setStyleSheet(btn_style)
        self.btn_edit.setStyleSheet(btn_style.replace('#197a3d', '#1566a1').replace('#eaffea', '#e0efff'))
        self.btn_delete.setStyleSheet(btn_style.replace('#197a3d', '#c60000').replace('#eaffea', '#ffeaea'))

        self.btn_edit.setEnabled(False)
        self.btn_delete.setEnabled(False)
        btns_row.addWidget(self.btn_add)
        btns_row.addWidget(self.btn_edit)
        btns_row.addWidget(self.btn_delete)
        btns_row.addStretch(1)
        layout.addLayout(btns_row)

        table_container = QScrollArea()
        table_container.setWidgetResizable(True)
        self.table = QTableWidget(0, 11)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)

        font = QFont()
        base_size = font.pointSizeF()
        if base_size <= 0:
            base_size = 10
        bigger_font = QFont(font)
        bigger_font.setPointSizeF(base_size * 1.2)
        self.table.setFont(bigger_font)
        self.table.setStyleSheet(f"""
            QTableWidget::item:selected {{
                background: #409cff;
                color: white;
            }}
            QTableWidget::item {{
                padding: 2px;
                margin: 0px;
                font-size: {bigger_font.pointSizeF()}pt;
                white-space: nowrap;
            }}
        """)
        self.table.setWordWrap(False)
        self.table.setHorizontalHeaderLabels([
            "Nr klienta", "Nazwa firmy", "Nazwa skróc.", "Osoba kontaktowa", "Telefon", "E-mail",
            "Ulica i nr", "Kod pocztowy", "Miasto", "NIP", "Adres dostawy"
        ])
        header_font = QFont(bigger_font)
        header_font.setBold(True)
        self.table.horizontalHeader().setFont(header_font)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_container.setWidget(self.table)
        layout.addWidget(table_container)

        self.table.itemSelectionChanged.connect(self.handle_selection)
        self.btn_add.clicked.connect(self.add_client)
        self.btn_edit.clicked.connect(self.edit_client)
        self.btn_delete.clicked.connect(self.delete_client)
        self.btn_search.clicked.connect(self.search_clients)
        self.search_edit.returnPressed.connect(self.search_clients)

        self.restore_column_widths()
        self.table.horizontalHeader().sectionResized.connect(self.save_column_widths)

        self._last_search_field = self.SEARCH_FIELDS[0][1]
        self._last_search_text = ""
        self.search_combo.currentIndexChanged.connect(self._on_search_combo_changed)
        self.refresh_clients()

    def _on_search_combo_changed(self, idx):
        self._last_search_field = self.SEARCH_FIELDS[idx][1]
        # Możesz wyczyścić pole wyszukiwania jeśli chcesz:
        # self.search_edit.clear()

    def save_column_widths(self):
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        widths = [self.table.columnWidth(i) for i in range(self.table.columnCount())]
        settings.setValue(self.SETTINGS_COLUMNS, widths)

    def restore_column_widths(self):
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        widths = settings.value(self.SETTINGS_COLUMNS)
        if widths and len(widths) == self.table.columnCount():
            for i, w in enumerate(widths):
                try:
                    self.table.setColumnWidth(i, int(w))
                except Exception:
                    pass

    def refresh_clients(self, search_field=None, search_text=""):
        self.table.setRowCount(0)
        session = Session()
        query = session.query(Client).order_by(Client.client_number.asc())
        if search_field and search_text:
            search = f"%{search_text.lower()}%"
            col = getattr(Client, search_field)
            query = query.filter(col.ilike(search))
        clients = query.all()
        for row, client in enumerate(clients):
            self.table.insertRow(row)
            delivery_address = " ".join(filter(None, [
                client.delivery_company,
                client.delivery_street,
                client.delivery_postal_code,
                client.delivery_city
            ]))
            for col, val in enumerate([
                client.client_number or "",
                client.name or "",
                getattr(client, "short_name", "") or "",
                client.contact_person or "",
                client.phone or "",
                client.email or "",
                client.street or "",
                client.postal_code or "",
                client.city or "",
                client.nip or "",
                delivery_address
            ]):
                item = QTableWidgetItem(val)
                font = self.table.font()
                if col == 0:
                    font_bold = QFont(font)
                    font_bold.setBold(True)
                    item.setFont(font_bold)
                else:
                    item.setFont(font)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item.setToolTip(val)
                item.setData(Qt.TextWrapAnywhere, False)
                if row % 2 == 0:
                    bg = QColor("#f2f2f2")
                else:
                    bg = QColor("#ffffff")
                item.setBackground(QBrush(bg))
                if col == 10:
                    item.setBackground(QBrush(QColor("#fffbc7")))
                self.table.setItem(row, col, item)
        session.close()
        self.btn_edit.setEnabled(False)
        self.btn_delete.setEnabled(False)
        self.table.clearSelection()
        self.table.resizeRowsToContents()
        min_row_height = 22
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, min_row_height)

    def search_clients(self):
        search_text = self.search_edit.text().strip()
        idx = self.search_combo.currentIndex()
        search_field = self.SEARCH_FIELDS[idx][1]
        self._last_search_field = search_field
        self._last_search_text = search_text
        self.refresh_clients(search_field, search_text)

    def handle_selection(self):
        selected = self.table.selectedItems()
        self.btn_edit.setEnabled(bool(selected))
        self.btn_delete.setEnabled(bool(selected))

    def get_selected_client(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        client_number = self.table.item(row, 0).text()
        session = Session()
        client = session.query(Client).filter_by(client_number=client_number).first()
        session.close()
        return client

    def add_client(self):
        dlg = ClientEditDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Błąd", "Nazwa firmy jest wymagana.")
                return
            session = Session()
            exists = session.query(Client).filter_by(client_number=data["client_number"]).first()
            if exists:
                QMessageBox.warning(self, "Błąd", f"Numer klienta {data['client_number']} już istnieje.")
                session.close()
                return
            client = Client(**data)
            session.add(client)
            session.commit()
            session.close()
            self.refresh_clients(self._last_search_field, self._last_search_text)

    def edit_client(self):
        client = self.get_selected_client()
        if not client:
            QMessageBox.information(self, "Wybierz klienta", "Zaznacz klienta do edycji.")
            return
        dlg = ClientEditDialog(client, parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            session = Session()
            dbclient = session.query(Client).filter_by(id=client.id).first()
            if dbclient.client_number != data["client_number"]:
                exists = session.query(Client).filter_by(client_number=data["client_number"]).first()
                if exists:
                    QMessageBox.warning(self, "Błąd", f"Numer klienta {data['client_number']} już istnieje.")
                    session.close()
                    return
            for k, v in data.items():
                setattr(dbclient, k, v)
            session.commit()
            session.close()
            self.refresh_clients(self._last_search_field, self._last_search_text)

    def delete_client(self):
        client = self.get_selected_client()
        if not client:
            QMessageBox.information(self, "Wybierz klienta", "Zaznacz klienta do usunięcia.")
            return
        ret = QMessageBox.question(
            self, "Potwierdź usunięcie",
            f"Jesteś pewny, że chcesz usunąć klienta '{client.client_number} - {client.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret != QMessageBox.Yes:
            return
        session = Session()
        session.delete(client)
        session.commit()
        session.close()
        self.refresh_clients(self._last_search_field, self._last_search_text)