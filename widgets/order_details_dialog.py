from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QDialogButtonBox, QSizePolicy, QHeaderView
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from models.db import Session
from models.orderitem import OrderItem

class OrderDetailsDialog(QDialog):
    def __init__(self, order, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Szczegóły produkcji")
        self.setModal(True)
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)
        font_bold = QFont("Segoe UI", 11, QFont.Bold)
        font = QFont("Segoe UI", 10)

        # --- Nagłówek: tylko klient, nr zam, data wysyłki ---
        client = order.client if hasattr(order, "client") else None
        name = client.name if client else "—"
        nr = getattr(order, "order_number", "—")
        data_wysylki = getattr(order, "delivery_date", "—")
        if hasattr(data_wysylki, "strftime"):  # datetime/date
            data_wysylki = data_wysylki.strftime("%Y-%m-%d")
        elif data_wysylki is None:
            data_wysylki = "—"
        header_row = QHBoxLayout()
        label_client = QLabel(f"{name}")
        label_client.setFont(font_bold)
        label_nr = QLabel(f"Zamówienie: {nr}")
        label_nr.setFont(font)
        label_date = QLabel(f"Wysyłka: {data_wysylki}")
        label_date.setFont(font)
        header_row.addWidget(label_client)
        header_row.addStretch(1)
        header_row.addWidget(label_nr)
        header_row.addSpacing(15)
        header_row.addWidget(label_date)
        layout.addLayout(header_row)
        layout.addSpacing(12)

        # --- Tabela pozycji produkcyjnych ---
        session = Session()
        order_items = session.query(OrderItem).filter_by(order_id=order.id).all()
        session.close()
        table_headers = ["#", "Materiał", "Wymiar", "Ilość", "Rodzaj", "Nawój", "Rdzeń"]
        prod_items = [item for item in order_items if getattr(item, "width", None) not in (None, '', 0)]
        table = QTableWidget(len(prod_items), len(table_headers))
        table.setHorizontalHeaderLabels(table_headers)
        for row_idx, item in enumerate(prod_items):
            table.setItem(row_idx, 0, QTableWidgetItem(str(row_idx+1)))
            table.setItem(row_idx, 1, QTableWidgetItem(str(getattr(item, "material", "") or "")))
            wymiar = f"{getattr(item, 'width', '') or ''} x {getattr(item, 'height', '') or ''}" if getattr(item, "height", None) not in (None, '', 0) else f"{getattr(item, 'width', '') or ''}"
            table.setItem(row_idx, 2, QTableWidgetItem(wymiar.strip()))
            table.setItem(row_idx, 3, QTableWidgetItem(str(getattr(item, "ordered_quantity", "") or "")))
            table.setItem(row_idx, 4, QTableWidgetItem(str(getattr(item, "quantity_type", "") or "")))
            table.setItem(row_idx, 5, QTableWidgetItem(str(getattr(item, "roll_length", "") or "")))
            table.setItem(row_idx, 6, QTableWidgetItem(str(getattr(item, "core", "") or "")))
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        table.setStyleSheet("""
            QTableWidget {
                background: #fff;
                border: none;
                color: #111;
            }
            QTableWidget::item {
                background: #fff;
                border: 1px solid #333;
                color: #111;
                padding: 4px 8px;
            }
            QHeaderView::section {
                background: #fff;
                border: 1px solid #333;
                font-weight: bold;
                font-size: 9.5pt;
                color: #111;
            }
        """)
        table.resizeColumnsToContents()
        for i in range(table.columnCount()):
            table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        table.setMinimumWidth(530)
        table.setFixedHeight(32 + 28 * len(prod_items))
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(table)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        # Automatyczne dopasowanie rozmiaru do zawartości:
        self.adjustSize()
        self.resize(self.sizeHint())
        self.setMinimumSize(self.sizeHint())