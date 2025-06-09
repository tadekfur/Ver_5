from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QLabel, QHeaderView
)
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtCore import Qt
from widgets.production_sorter import get_weekly_production_summary

class ProductionSortDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zestawienie produkcji")
        self.resize(950, 700)
        self.layout = QVBoxLayout(self)

        # Tytuł dialogu
        title = QLabel("Zestawienie produkcji (grupowanie: tydzień, materiał, rozmiar)")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("color: #197a3d; margin-bottom: 16px;")
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)

        # Tabela
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #b3b3b3;
                font-size: 15px;
                background: #fcfcfc;
            }
            QTableWidget::item:selected {
                background: #eaffea;
                color: #0e5f22;
            }
            QHeaderView::section {
                background-color: #eaffea;
                color: #197a3d;
                font-weight: bold;
                font-size: 15px;
                border-bottom: 2px solid #197a3d;
                padding: 8px;
            }
        """)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.layout.addWidget(self.table)

        # Przycisk zamykania
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_close = QPushButton("Zamknij")
        self.btn_close.setMinimumWidth(130)
        self.btn_close.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                min-height: 36px;
                border-radius: 7px;
                border: 2px solid #197a3d;
                background: #eaffea;
                color: #197a3d;
                padding: 8px 30px;
                margin: 0 8px;
            }
            QPushButton:hover { background: #c5ffd7; }
        """)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        self.layout.addLayout(btn_layout)

        self.populate_table()

    def populate_table(self):
        summary = get_weekly_production_summary()
        self.table.setRowCount(len(summary))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Tydzień", "Materiał", "Szerokość [mm]", "Wysokość [mm]", "Ilość [tyś.]"
        ])

        font_bold = QFont("Segoe UI", 13, QFont.Bold)
        self.table.horizontalHeader().setFont(font_bold)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.horizontalHeader().setHighlightSections(False)

        for row, ((week, material, width, height), qty) in enumerate(summary):
            week_item = QTableWidgetItem(str(week))
            week_item.setTextAlignment(Qt.AlignCenter)
            week_item.setFont(QFont("Segoe UI", 12))

            material_item = QTableWidgetItem(str(material))
            material_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            material_item.setFont(QFont("Segoe UI", 12))

            width_item = QTableWidgetItem(str(width))
            width_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            width_item.setFont(QFont("Segoe UI", 12))

            height_item = QTableWidgetItem(str(height))
            height_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            height_item.setFont(QFont("Segoe UI", 12))

            qty_item = QTableWidgetItem(f"{qty:.2f}")
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            qty_item.setFont(QFont("Segoe UI", 12, QFont.Bold))
            qty_item.setForeground(QBrush(QColor("#197a3d")))

            self.table.setItem(row, 0, week_item)
            self.table.setItem(row, 1, material_item)
            self.table.setItem(row, 2, width_item)
            self.table.setItem(row, 3, height_item)
            self.table.setItem(row, 4, qty_item)

        # Styl nagłówków i kolumn
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(True)