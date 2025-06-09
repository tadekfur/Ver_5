import datetime
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QDateEdit, QGroupBox, QScrollArea, QMessageBox, QSizePolicy, QTextEdit, QDialog, QCalendarWidget,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QFontMetrics, QColor, QPalette, QTextCharFormat
from datetime import date
from models.db import Session
from models.order import Order
from models.client import Client
from models.orderitem import OrderItem
from models.order_sequence import get_next_order_number
from widgets.clients_db_widget import ClientsDBWidget, ClientEditDialog

HOLIDAYS_2025 = [
    datetime.date(2025, 1, 1),
    datetime.date(2025, 1, 6),
    datetime.date(2025, 4, 20),
    datetime.date(2025, 4, 21),
    datetime.date(2025, 5, 1),
    datetime.date(2025, 5, 3),
    datetime.date(2025, 6, 8),
    datetime.date(2025, 6, 19),
    datetime.date(2025, 8, 15),
    datetime.date(2025, 11, 1),
    datetime.date(2025, 11, 11),
    datetime.date(2025, 12, 24),
    datetime.date(2025, 12, 25),
    datetime.date(2025, 12, 26),
]

def is_polish_holiday(date_obj):
    if date_obj in HOLIDAYS_2025:
        return True
    if date_obj.isoweekday() in (6, 7):
        return True
    return False

BTN_GREEN = """
    QPushButton {
        font-size: 14px;
        font-weight: bold;
        min-height: 23px;
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
BTN_RED = BTN_GREEN.replace('#197a3d', '#c60000').replace('#eaffea', '#ffeaea').replace('#c5ffd7', '#ffd2d2')
BTN_ORANGE = BTN_GREEN.replace('#197a3d', '#d35400').replace('#eaffea', '#fff4e0').replace('#c5ffd7', '#ffe0b2')
BTN_VIOLET = BTN_GREEN.replace('#197a3d', '#8e44ad').replace('#eaffea', '#f5e6ff').replace('#c5ffd7', '#e0cfff')
BTN_BLUE = """
    QPushButton {
        font-size: 16px;
        font-weight: bold;
        min-height: 54px;
        border-radius: 10px;
        border: 2.5px solid #2267d4;
        background: #4D90FE;
        color: white;
        padding: 12px 28px;
        margin: 6px 12px;
    }
    QPushButton:disabled {
        background: #cbd8f7;
        color: #a0a0a0;
        border: 2px solid #cccccc;
    }
    QPushButton:pressed {
        background: #2267d4;
    }
"""

MATERIAL_OPTIONS = [
    "Termiczny", "Termotransferowy", "Termiczny TOP", "Termiczny RF20",
    "Termotransferowy RF20", "Folia PP", "Folia PP RF20",
    "PET Matt Silver", "Inny (dopisz ręcznie)"
]
RDZEN_OPTIONS = ["25", "40", "76", "inny"]

def get_max_content_width(options, font):
    metrics = QFontMetrics(font)
    return max(metrics.horizontalAdvance(opt) for opt in options) + 28

class ClientSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wybierz klienta")
        self.setModal(True)
        layout = QVBoxLayout(self)
        self.clients_widget = ClientsDBWidget()
        for btn_name in ('btn_add', 'btn_edit', 'btn_delete'):
            btn = getattr(self.clients_widget, btn_name, None)
            if btn is not None:
                btn.hide()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.clients_widget)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        self.choose_btn = QPushButton("Wybierz")
        self.choose_btn.setStyleSheet(BTN_GREEN)
        self.choose_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.setStyleSheet(BTN_RED)
        self.cancel_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        btn_row.addStretch(1)
        btn_row.addWidget(self.choose_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        self.selected_client = None

        table = self.clients_widget.table
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setStyleSheet("""
            QTableWidget::item:selected {
                background: #b3d8fd !important;
                color: #003366 !important;
            }
        """)
        table.itemDoubleClicked.connect(self._handle_choose)
        self.choose_btn.clicked.connect(self._handle_choose)
        self.cancel_btn.clicked.connect(self.reject)

        self.setMinimumWidth(1000)
        self.setMaximumWidth(2200)
        self.adjust_table_size()
        self.showEvent = self._on_show

    def _on_show(self, event):
        self.adjust_table_size()
        QDialog.showEvent(self, event)

    def adjust_table_size(self):
        table = self.clients_widget.table
        table.resizeColumnsToContents()
        width = sum([table.columnWidth(i) for i in range(table.columnCount())]) + 120
        width = min(max(width, 1000), 2200)
        visible_rows = min(table.rowCount(), 20)
        row_height = table.verticalHeader().defaultSectionSize()
        header_height = table.horizontalHeader().height()
        height = header_height + visible_rows * row_height + 240
        self.setMinimumWidth(width)
        self.setMaximumWidth(width)
        self.setMinimumHeight(height)
        self.setMaximumHeight(1500)
        self.resize(width, height)

    def _handle_choose(self, *args):
        client = self.clients_widget.get_selected_client()
        if client:
            self.selected_client = client
            self.accept()

class CustomCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setFirstDayOfWeek(Qt.Monday)
        self.setGridVisible(True)
        self.update_weekend_colors()

    def update_weekend_colors(self):
        fmt_default = QTextCharFormat()
        fmt_default.setForeground(QColor("#000000"))
        self.setDateTextFormat(QDate(), fmt_default)
        month = self.monthShown()
        year = self.yearShown()
        days_in_month = QDate(year, month, 1).daysInMonth()
        fmt_weekend = QTextCharFormat()
        fmt_weekend.setForeground(QColor("#d41c1c"))
        fmt_selected = QTextCharFormat()
        fmt_selected.setForeground(QColor("#000000"))
        selected_date = self.selectedDate()
        for day in range(1, days_in_month + 1):
            qdate = QDate(year, month, day)
            if qdate == selected_date:
                self.setDateTextFormat(qdate, fmt_selected)
            elif qdate.dayOfWeek() in (6, 7):
                self.setDateTextFormat(qdate, fmt_weekend)
            else:
                self.setDateTextFormat(qdate, fmt_default)

    def paintCell(self, painter, rect, date):
        if date == self.selectedDate():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("#000000"))
            self.setDateTextFormat(date, fmt)
        super().paintCell(painter, rect, date)

    def showNextMonth(self):
        super().showNextMonth()
        self.update_weekend_colors()
    def showPreviousMonth(self):
        super().showPreviousMonth()
        self.update_weekend_colors()
    def showNextYear(self):
        super().showNextYear()
        self.update_weekend_colors()
    def showPreviousYear(self):
        super().showPreviousYear()
        self.update_weekend_colors()
    def setCurrentPage(self, year, month):
        super().setCurrentPage(year, month)
        self.update_weekend_colors()
    def setSelectedDate(self, qdate):
        super().setSelectedDate(qdate)
        self.update_weekend_colors()

class OrderEntryWidget(QWidget):
    def __init__(self, edit_order=None, copy_order=None, new_client=None, after_save_callback=None, parent=None, main_window=None):
        super().__init__(parent)
        self.edit_order = edit_order
        self.copy_order = copy_order
        self.new_client = new_client
        self.after_save_callback = after_save_callback
        self.main_window = main_window
        self.prod_fields = []
        self.prod_blocks = []
        self.selected_client = None
        self.init_ui()
        if self.edit_order:
            self.fill_from_order(self.edit_order, as_new=False)
        elif self.copy_order:
            self.fill_from_order(self.copy_order, as_new=True)
        elif self.new_client:
            self.fill_from_client(self.new_client)

    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("WPROWADŹ DANE ZAMÓWIENIA")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; color: #147a3a; font-weight: bold;")
        layout.addWidget(title)

        form_area = QScrollArea(self)
        form_area.setWidgetResizable(True)
        self.setMinimumWidth(1200)
        self.setMaximumWidth(1800)

        form_widget = QWidget()
        self.form_layout = QVBoxLayout(form_widget)
        self.form_layout.setSpacing(18)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Nr zamówienia:"))
        self.nr_edit = QLineEdit()
        self.nr_edit.setMaximumWidth(260)
        self.nr_edit.setMinimumWidth(180)
        self.nr_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.nr_edit.setReadOnly(True)
        row1.addWidget(self.nr_edit)
        row1.addSpacing(16)

        label_datazam = QLabel("Data zamówienia:")
        font_bold = QFont("Segoe UI", 11, QFont.Bold)
        label_datazam.setFont(font_bold)
        row1.addWidget(label_datazam)
        self.data_zamowienia_edit = QDateEdit(QDate.currentDate())
        self.data_zamowienia_edit.setCalendarPopup(True)
        self.data_zamowienia_edit.setMaximumWidth(150)
        font_date = QFont("Segoe UI", 11, QFont.Bold)
        self.data_zamowienia_edit.setFont(font_date)
        self.data_zamowienia_edit.setFixedHeight(36)
        row1.addWidget(self.data_zamowienia_edit)
        row1.addSpacing(16)

        label_datadostawy = QLabel("Data wysyłki:")
        font_bold_red = QFont("Segoe UI", 11, QFont.Bold)
        label_datadostawy.setFont(font_bold_red)
        label_datadostawy.setStyleSheet("color: #222222;")
        row1.addWidget(label_datadostawy)
        self.data_dostawy_edit = QDateEdit(QDate.currentDate())
        self.data_dostawy_edit.setCalendarPopup(True)
        self.data_dostawy_edit.setMaximumWidth(150)
        font_date_red = QFont("Segoe UI", 11, QFont.Bold)
        self.data_dostawy_edit.setFont(font_date_red)
        self.data_dostawy_edit.setFixedHeight(36)
        palette = self.data_dostawy_edit.palette()
        palette.setColor(QPalette.Text, QColor("#000000"))
        self.data_dostawy_edit.setPalette(palette)
        self.custom_calendar = CustomCalendarWidget()
        self.data_dostawy_edit.setCalendarWidget(self.custom_calendar)
        row1.addWidget(self.data_dostawy_edit)
        row1.addStretch(1)
        self.form_layout.addLayout(row1)

        gb = QGroupBox("Dane zamawiającego")
        gb_layout = QGridLayout(gb)
        gb_layout.addWidget(QLabel("Nr klienta:"), 0, 0)
        nr_klienta_layout = QHBoxLayout()
        self.nr_klienta_edit = QLineEdit()
        self.nr_klienta_edit.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.nr_klienta_edit.setMaximumWidth(170)
        self.nr_klienta_edit.setMinimumWidth(120)
        self.nr_klienta_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.nr_klienta_edit.setReadOnly(True)
        nr_klienta_layout.addWidget(self.nr_klienta_edit)

        nr_klienta_layout.addSpacing(12)
        label_termin_platnosci = QLabel("Termin płatności:")
        label_termin_platnosci.setFont(QFont("Segoe UI", 10, QFont.Bold))
        nr_klienta_layout.addWidget(label_termin_platnosci)

        self.termin_platnosci_combo = QComboBox()
        self.termin_platnosci_combo.addItems(["7 dni", "14 dni", "21 dni", "30 dni", "45 dni"])
        self.termin_platnosci_combo.setMinimumWidth(110)
        self.termin_platnosci_combo.setMaximumWidth(110)
        self.termin_platnosci_combo.setFont(QFont("Segoe UI", 10))
        nr_klienta_layout.addWidget(self.termin_platnosci_combo)

        nr_klienta_layout.addSpacing(12)
        self.btn_wstaw_z_bazy = QPushButton("Wstaw z bazy")
        self.btn_dodaj_nowego = QPushButton("Dodaj nowego")
        self.btn_wstaw_z_bazy.setMinimumWidth(120)
        self.btn_wstaw_z_bazy.setMaximumWidth(170)
        self.btn_wstaw_z_bazy.setMinimumHeight(int(34 * 1.2))
        self.btn_wstaw_z_bazy.setStyleSheet(BTN_GREEN)
        self.btn_wstaw_z_bazy.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_dodaj_nowego.setMinimumWidth(120)
        self.btn_dodaj_nowego.setMaximumWidth(170)
        self.btn_dodaj_nowego.setMinimumHeight(int(34 * 1.2))
        self.btn_dodaj_nowego.setStyleSheet(BTN_ORANGE)
        self.btn_dodaj_nowego.setFont(QFont("Segoe UI", 12, QFont.Bold))
        nr_klienta_layout.addWidget(self.btn_wstaw_z_bazy)
        nr_klienta_layout.addSpacing(6)
        nr_klienta_layout.addWidget(self.btn_dodaj_nowego)
        nr_klienta_layout.addStretch(1)

        gb_layout.addLayout(nr_klienta_layout, 0, 1, 1, 2, alignment=Qt.AlignLeft)
        self.btn_wstaw_z_bazy.clicked.connect(self.handle_select_client_from_db)
        self.btn_dodaj_nowego.clicked.connect(self.handle_add_new_client)

        labels = [
            "Firma", "Nazwa skróc.", "Osoba kontaktowa", "Nr telefonu", "E-mail",
            "Ulica i nr", "Kod pocztowy", "Miasto", "NIP"
        ]
        self.zamawiajacy_fields = []
        for i, field in enumerate(labels):
            gb_layout.addWidget(QLabel(field + ":"), i+1, 0, alignment=Qt.AlignLeft)
            edit = QLineEdit()
            edit.setAlignment(Qt.AlignLeft)
            edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            edit.setMaximumWidth(240)
            gb_layout.addWidget(edit, i+1, 1, 1, 2)
            self.zamawiajacy_fields.append(edit)
        gb_layout.setColumnStretch(1, 1)
        gb_layout.setColumnStretch(2, 1)
        self.form_layout.addWidget(gb)

        self.prod_container = QGroupBox("Dane produkcji")
        self.prod_main_layout = QVBoxLayout(self.prod_container)
        self.prod_grid = QGridLayout()
        self.prod_main_layout.addLayout(self.prod_grid)
        font = self.font()
        self.material_combo_width = get_max_content_width(MATERIAL_OPTIONS, font)
        self.rdzen_combo_width = max(get_max_content_width(RDZEN_OPTIONS, font), 90) + 30
        for idx in range(2):
            self.add_prod_block(idx+1)
        self.btn_add_position = QPushButton("Dodaj pozycję")
        self.btn_add_position.setStyleSheet(BTN_GREEN)
        self.btn_add_position.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_add_position.setMinimumWidth(180)
        self.btn_add_position.setMaximumWidth(260)
        self.btn_add_position.setMinimumHeight(int(36 * 1.2))
        self.btn_add_position.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_add_position.clicked.connect(self.handle_add_position)
        self.prod_main_layout.addWidget(self.btn_add_position, alignment=Qt.AlignLeft)
        self.form_layout.addWidget(self.prod_container)

        gb_addr = QGroupBox("Adres dostawy")
        gb_addr_layout = QGridLayout(gb_addr)
        addr_labels = ["Nazwa firmy", "Ulica i nr", "Kod pocztowy", "Miejscowość"]
        self.addr_fields = []
        for i, field in enumerate(addr_labels):
            gb_addr_layout.addWidget(QLabel(field + ":"), i, 0)
            edit = QLineEdit()
            gb_addr_layout.addWidget(edit, i, 1)
            self.addr_fields.append(edit)
        gb_addr_layout.setColumnStretch(1, 1)
        self.form_layout.addWidget(gb_addr)

        gb_uwagi = QGroupBox("Uwagi")
        uwagi_layout = QVBoxLayout(gb_uwagi)
        self.uwagi_textedit = QTextEdit()
        self.uwagi_textedit.setPlaceholderText("Wpisz dodatkowe uwagi do zamówienia...")
        uwagi_layout.addWidget(self.uwagi_textedit)
        self.form_layout.addWidget(gb_uwagi)

        btn_save = QPushButton("💾 Zapisz zamówienie")
        btn_save.setStyleSheet(BTN_BLUE)
        btn_save.setFont(QFont("Segoe UI", 16, QFont.Bold))
        btn_save.setMinimumWidth(280)
        btn_save.setMinimumHeight(54)
        btn_save.clicked.connect(self.save_order)
        self.form_layout.addWidget(btn_save, alignment=Qt.AlignCenter)

        form_area.setWidget(form_widget)
        layout.addWidget(form_area)

    def add_prod_block(self, number=None):
        idx = len(self.prod_blocks)
        if number is None:
            number = idx + 1

        prod_block = QGroupBox()
        prod_block.setStyleSheet("QGroupBox { margin-top: 6px; }")
        prod_layout = QGridLayout(prod_block)

        title_layout = QHBoxLayout()
        block_title = QLabel(f"Pozycja {number}")
        block_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        block_title.setStyleSheet("color: #159800; font-weight: bold")
        title_layout.addWidget(block_title)

        btn_remove = QPushButton("Usuń")
        btn_remove.setStyleSheet(BTN_RED)
        btn_remove.setFont(QFont("Segoe UI", 13, QFont.Bold))
        btn_remove.setMaximumWidth(130)
        btn_remove.setMinimumWidth(110)
        btn_remove.setMinimumHeight(int(36 * 1.2))
        btn_remove.clicked.connect(lambda: self.remove_prod_block(prod_block))
        title_layout.addStretch(1)
        title_layout.addWidget(btn_remove)
        prod_layout.addLayout(title_layout, 0, 0, 1, 4)

        cena_label = QLabel("Cena:")
        cena_input = QLineEdit()
        cena_input.setPlaceholderText("Cena")
        cena_input.setMaximumWidth(200)
        cena_input.setMinimumWidth(110)

        cena_typ_combo = QComboBox()
        cena_typ_combo.addItems(["za 1 tyś", "za 1 rolkę"])
        cena_typ_combo.setStyleSheet("QComboBox { background: #eaffea; }")
        cena_typ_combo.setFixedWidth(110)
        cena_typ_combo.setCurrentText("za 1 tyś")

        cena_row = QHBoxLayout()
        cena_row.addWidget(cena_label)
        cena_row.addWidget(cena_input)
        cena_row.addWidget(cena_typ_combo)
        cena_row.addStretch(1)
        prod_layout.addLayout(cena_row, 1, 0, 1, 4)

        szer = QLineEdit()
        szer.setPlaceholderText("Szerokość [mm]")
        szer.setMaximumWidth(200)
        szer.setMinimumWidth(110)

        wys = QLineEdit()
        wys.setPlaceholderText("Wysokość [mm]")
        wys.setMaximumWidth(200)
        wys.setMinimumWidth(110)

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Szerokość:"))
        size_row.addWidget(szer)
        size_row.addSpacing(16)
        size_row.addWidget(QLabel("Wysokość:"))
        size_row.addWidget(wys)
        size_row.addStretch(1)
        prod_layout.addLayout(size_row, 2, 0, 1, prod_layout.columnCount())

        mat = QComboBox()
        mat.addItems(MATERIAL_OPTIONS)
        mat.setMinimumWidth(180)
        mat.setMaximumWidth(180)
        mat.setStyleSheet(
            "QComboBox { background: #eaffea; }"
            "QComboBox QAbstractItemView { background: #eaffea; }"
        )
        mat.setEditable(False)

        def handle_material_change(idx):
            text = mat.itemText(idx)
            if text == "Inny (dopisz ręcznie)":
                mat.setEditable(True)
                mat.setCurrentText("")
                mat.lineEdit().setPlaceholderText("Wpisz własny rodzaj materiału")
                mat.lineEdit().setFocus()
            else:
                mat.setEditable(False)
                mat.setCurrentText(text)
        mat.currentIndexChanged.connect(handle_material_change)

        ilosc = QLineEdit(); ilosc.setPlaceholderText("zam. ilość")

        typ_ilosci = QComboBox(); typ_ilosci.addItems(["tyś.", "rolek"])
        typ_ilosci.setStyleSheet("QComboBox { background: #eaffea; }")
        typ_ilosci.setFixedWidth(80)
        typ_ilosci.setCurrentText("rolek")

        naw_dlug = QLineEdit(); naw_dlug.setPlaceholderText("nawój/długość")

        # --- zmiana tutaj: pole "Rdzeń" z opcją "inny" i polem edycyjnym ---
        rdzen = QComboBox()
        rdzen.addItems(RDZEN_OPTIONS)
        rdzen.setStyleSheet("QComboBox { background: #eaffea; }")
        rdzen.setFixedWidth(80)
        rdzen.setEditable(False)

        rdzen_inny_edit = QLineEdit()
        rdzen_inny_edit.setPlaceholderText("Wpisz rdzeń")
        rdzen_inny_edit.setVisible(False)
        rdzen_inny_edit.setFixedWidth(80)

        def handle_rdzen_change(idx):
            if rdzen.itemText(idx) == "inny":
                rdzen_inny_edit.setVisible(True)
                rdzen_inny_edit.setFocus()
            else:
                rdzen_inny_edit.setVisible(False)
        rdzen.currentIndexChanged.connect(handle_rdzen_change)

        row_mat = QHBoxLayout()
        label_mat = QLabel("Rodzaj materiału:")
        row_mat.addWidget(label_mat)
        row_mat.addWidget(mat)
        row_mat.addStretch(1)
        prod_layout.addLayout(row_mat, 3, 0, 1, 4)

        row_ilosc = QHBoxLayout()
        label_ilosc = QLabel("zam. ilość:")
        row_ilosc.addWidget(label_ilosc)
        row_ilosc.addWidget(ilosc)
        ilosc.setFixedWidth(180)
        row_ilosc.addSpacing(8)
        row_ilosc.addWidget(typ_ilosci)
        row_ilosc.addStretch(1)
        prod_layout.addLayout(row_ilosc, 4, 0, 1, 4)

        row_nawoj = QHBoxLayout()
        label_nawoj = QLabel("nawój/długość:")
        row_nawoj.addWidget(label_nawoj)
        row_nawoj.addWidget(naw_dlug)
        naw_dlug.setFixedWidth(180)
        row_nawoj.addSpacing(8)
        label_rdzen = QLabel("Rdzeń:")
        row_nawoj.addWidget(label_rdzen)
        row_nawoj.addWidget(rdzen)
        row_nawoj.addWidget(rdzen_inny_edit)
        row_nawoj.addStretch(1)
        prod_layout.addLayout(row_nawoj, 5, 0, 1, 4)

        row_zam_rolki = QHBoxLayout()
        label_zam_rolki = QLabel("zam. rolki:")
        zam_rolki = QLineEdit()
        zam_rolki.setReadOnly(True)
        zam_rolki.setFixedWidth(180)
        row_zam_rolki.addWidget(label_zam_rolki)
        row_zam_rolki.addWidget(zam_rolki)
        row_zam_rolki.addStretch(1)
        prod_layout.addLayout(row_zam_rolki, 6, 0, 1, 4)

        def update_zam_rolki():
            try:
                val_ilosc = float(ilosc.text().replace(",", ".") or "0")
                val_nawoj = float(naw_dlug.text().replace(",", ".") or "0")
                typ = typ_ilosci.currentText().strip()
                if typ == "tyś.":
                    if val_nawoj > 0 and val_ilosc > 0:
                        dzielenie = (val_ilosc * 1000) / val_nawoj
                        wynik = math.ceil(dzielenie)
                        zam_rolki.setText(str(wynik))
                    else:
                        zam_rolki.setText("0")
                else:  # typ == "rolek"
                    zam_rolki.setText(ilosc.text())
            except Exception:
                zam_rolki.setText("0")

        ilosc.textChanged.connect(update_zam_rolki)
        naw_dlug.textChanged.connect(update_zam_rolki)
        typ_ilosci.currentIndexChanged.connect(update_zam_rolki)

        prod_dict = {
            "block_widget": prod_block,
            "Cena": cena_input,
            "CenaTyp": cena_typ_combo,
            "Szerokość": szer, "Wysokość": wys, "Rodzaj materiału": mat,
            "zam. ilość": ilosc, "Typ ilości": typ_ilosci,
            "nawój/długość": naw_dlug, "Rdzeń": rdzen,
            "Rdzeń_inny": rdzen_inny_edit,
            "zam. rolki": zam_rolki
        }
        self.prod_fields.append(prod_dict)
        self.prod_blocks.append(prod_block)

        row = idx // 2
        col = idx % 2
        self.prod_grid.addWidget(prod_block, row, col)

    def remove_prod_block(self, block_widget):
        idx_to_remove = None
        for i, d in enumerate(self.prod_fields):
            if d["block_widget"] is block_widget:
                idx_to_remove = i
                break
        if idx_to_remove is not None:
            block = self.prod_blocks.pop(idx_to_remove)
            d = self.prod_fields.pop(idx_to_remove)
            block.setParent(None)
            block.deleteLater()
            self.relayout_prod_blocks()

    def relayout_prod_blocks(self):
        for i in reversed(range(self.prod_grid.count())):
            item = self.prod_grid.itemAt(i)
            widget = item.widget()
            if widget:
                self.prod_grid.removeWidget(widget)
        for idx, block in enumerate(self.prod_blocks):
            row = idx // 2
            col = idx % 2
            self.prod_grid.addWidget(block, row, col)

    def handle_add_position(self):
        self.add_prod_block()
        self.prod_container.adjustSize()
        self.prod_container.updateGeometry()

    def fill_from_order(self, order, as_new=False):
        session = Session()
        client = session.query(Client).filter_by(id=order.client_id).first()
        items = session.query(OrderItem).filter_by(order_id=order.id).all()
        session.close()
        if as_new:
            self.nr_edit.setText("")
        else:
            self.nr_edit.setText(order.order_number)
        self.data_zamowienia_edit.setDate(QDate.fromString(order.order_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        self.data_dostawy_edit.setDate(QDate.fromString(order.delivery_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        if hasattr(order, "payment_term") and order.payment_term:
            idx = self.termin_platnosci_combo.findText(order.payment_term)
            if idx != -1:
                self.termin_platnosci_combo.setCurrentIndex(idx)
            else:
                self.termin_platnosci_combo.setCurrentIndex(0)
        else:
            self.termin_platnosci_combo.setCurrentIndex(0)
        if client:
            self.selected_client = client
            self.nr_klienta_edit.setText(str(client.client_number))
            self.zamawiajacy_fields[0].setText(client.name or "")
            self.zamawiajacy_fields[1].setText(getattr(client, "short_name", "") or "")
            self.zamawiajacy_fields[2].setText(client.contact_person or "")
            self.zamawiajacy_fields[3].setText(client.phone or "")
            self.zamawiajacy_fields[4].setText(client.email or "")
            self.zamawiajacy_fields[5].setText(client.street or "")
            self.zamawiajacy_fields[6].setText(client.postal_code or "")
            self.zamawiajacy_fields[7].setText(client.city or "")
            self.zamawiajacy_fields[8].setText(client.nip or "")
            self.addr_fields[0].setText(client.delivery_company or "")
            self.addr_fields[1].setText(client.delivery_street or "")
            self.addr_fields[2].setText(client.delivery_postal_code or "")
            self.addr_fields[3].setText(client.delivery_city or "")
        self.uwagi_textedit.setText(order.notes or "")
        for block in list(self.prod_blocks):
            self.remove_prod_block(block)
        for idx, item in enumerate(items):
            self.add_prod_block(idx+1)
            p = self.prod_fields[-1]
            p["Szerokość"].setText(str(item.width))
            p["Wysokość"].setText(str(item.height))
            if item.material in MATERIAL_OPTIONS:
                p["Rodzaj materiału"].setCurrentText(item.material)
            else:
                idx_inny = p["Rodzaj materiału"].findText("Inny (dopisz ręcznie)")
                if idx_inny >= 0:
                    p["Rodzaj materiału"].setCurrentIndex(idx_inny)
                    p["Rodzaj materiału"].setEditable(True)
                    p["Rodzaj materiału"].setCurrentText(item.material)
            p["zam. ilość"].setText(str(item.ordered_quantity))
            p["Typ ilości"].setCurrentText(item.quantity_type)
            p["nawój/długość"].setText(item.roll_length)
            # obsługa "Rdzeń"
            if item.core and item.core not in RDZEN_OPTIONS:
                idx_inny = p["Rdzeń"].findText("inny")
                if idx_inny >= 0:
                    p["Rdzeń"].setCurrentIndex(idx_inny)
                    p["Rdzeń_inny"].setVisible(True)
                    p["Rdzeń_inny"].setText(item.core)
            else:
                p["Rdzeń"].setCurrentText(item.core or "")
                p["Rdzeń_inny"].setVisible(False)
                p["Rdzeń_inny"].setText("")
            p["Cena"].setText(getattr(item, "price", "") or "")
            if hasattr(item, "price_type"):
                p["CenaTyp"].setCurrentText(item.price_type or "za 1 tyś")

    def fill_from_client(self, client):
        self.selected_client = client
        self.nr_klienta_edit.setText(str(client.client_number))
        self.zamawiajacy_fields[0].setText(client.name or "")
        self.zamawiajacy_fields[1].setText(getattr(client, "short_name", "") or "")
        self.zamawiajacy_fields[2].setText(client.contact_person or "")
        self.zamawiajacy_fields[3].setText(client.phone or "")
        self.zamawiajacy_fields[4].setText(client.email or "")
        self.zamawiajacy_fields[5].setText(client.street or "")
        self.zamawiajacy_fields[6].setText(client.postal_code or "")
        self.zamawiajacy_fields[7].setText(client.city or "")
        self.zamawiajacy_fields[8].setText(client.nip or "")
        self.addr_fields[0].setText(client.delivery_company or "")
        self.addr_fields[1].setText(client.delivery_street or "")
        self.addr_fields[2].setText(client.delivery_postal_code or "")
        self.addr_fields[3].setText(client.delivery_city or "")

    def handle_select_client_from_db(self):
        dlg = ClientSelectDialog(self)
        if dlg.exec() == QDialog.Accepted and dlg.selected_client:
            self.fill_from_client(dlg.selected_client)

    def handle_add_new_client(self):
        dlg = ClientEditDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            session = Session()
            client = Client(**data)
            session.add(client)
            session.commit()
            if self.main_window and hasattr(self.main_window, "clients_db"):
                try:
                    self.main_window.clients_db.refresh_clients()
                except Exception:
                    pass
            session.refresh(client)
            session.close()
            self.fill_from_client(client)

    def save_order(self):
        if not self.zamawiajacy_fields[0].text().strip():
            QMessageBox.warning(self, "Błąd", "Podaj nazwę firmy.")
            return
        if not self.selected_client:
            QMessageBox.warning(self, "Błąd", "Nie wybrano klienta dla zamówienia!")
            return

        delivery_date_qdate = self.data_dostawy_edit.date()
        delivery_date = datetime.date(
            delivery_date_qdate.year(),
            delivery_date_qdate.month(),
            delivery_date_qdate.day()
        )
        if is_polish_holiday(delivery_date):
            QMessageBox.information(
                self,
                "Uwaga! Dzień wolny od pracy",
                "Wybrana data wysyłki przypada na dzień ustawowo wolny od pracy w Polsce (święto lub sobota/niedziela).\n"
                "Zmień datę wysyłki lub wróć do edycji zamówienia.",
                QMessageBox.Ok
            )
            return

        confirm = QMessageBox(self)
        confirm.setWindowTitle("Potwierdzenie zapisu")
        confirm.setText("Jesteś pewny, że chcesz zapisać zamówienie?")
        confirm.setIcon(QMessageBox.Question)
        btn_yes = confirm.addButton("TAK", QMessageBox.AcceptRole)
        btn_cancel = confirm.addButton("Wróć do zamówienia", QMessageBox.RejectRole)
        confirm.exec()

        if confirm.clickedButton() != btn_yes:
            return

        order_date_qdate = self.data_zamowienia_edit.date()
        order_date = date(
            order_date_qdate.year(),
            order_date_qdate.month(),
            order_date_qdate.day()
        )

        session = Session()
        if self.edit_order:
            order = session.query(Order).get(self.edit_order.id)
            if order is None:
                QMessageBox.critical(self, "Błąd", "Nie znaleziono zamówienia w bazie.")
                session.close()
                return
            order.order_date = order_date
            order.delivery_date = delivery_date
            order.notes = self.uwagi_textedit.toPlainText().strip()
            order.client_id = self.selected_client.id
            order.payment_term = self.termin_platnosci_combo.currentText()
            session.query(OrderItem).filter_by(order_id=order.id).delete()
        else:
            order_number = get_next_order_number(session)
            self.nr_edit.setText(order_number)
            order = Order(
                order_number=order_number,
                order_date=order_date,
                delivery_date=delivery_date,
                notes=self.uwagi_textedit.toPlainText().strip(),
                client_id=self.selected_client.id,
                payment_term=self.termin_platnosci_combo.currentText()
            )
            session.add(order)
            session.flush()

        for p in self.prod_fields:
            zam_rolki_val = p["zam. rolki"].text().strip()
            try:
                zam_rolki = int(zam_rolki_val) if zam_rolki_val else None
            except Exception:
                zam_rolki = None
            if p["Rdzeń"].currentText() == "inny":
                core_value = p["Rdzeń_inny"].text().strip()
            else:
                core_value = p["Rdzeń"].currentText().strip()
            item = OrderItem(
                order_id=order.id,
                width=p["Szerokość"].text().strip(),
                height=p["Wysokość"].text().strip(),
                material=p["Rodzaj materiału"].currentText().strip(),
                ordered_quantity=p["zam. ilość"].text().strip(),
                quantity_type=p["Typ ilości"].currentText().strip(),
                roll_length=p["nawój/długość"].text().strip(),
                core=core_value,
                price=p["Cena"].text().strip(),
                price_type=p["CenaTyp"].currentText().strip(),
                zam_rolki=zam_rolki
            )
            session.add(item)
        session.commit()
        session.close()
        if self.after_save_callback:
            self.after_save_callback()