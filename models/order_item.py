from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float # Dodano Float
from sqlalchemy.orm import relationship
from .db import Base # Zakładam, że Base jest w models/db.py

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)

    # Pola odpowiadające temu, co jest zapisywane w OrderEntryWidget
    width = Column(String)              # np. "100"
    height = Column(String)             # np. "50"
    material = Column(String)           # np. "Termotransferowy"
    ordered_quantity = Column(String)   # np. "1000"
    quantity_type = Column(String)      # np. "tyś." lub "rolek"
    roll_length = Column(String)        # np. "250" (może być też metraż, np. "100m")
    core = Column(String)               # np. "40" lub "inny"
    price = Column(String)              # Cena jako string, np. "12.34"
    price_type = Column(String)         # np. "za 1 tyś" lub "za 1 rolkę"
    zam_rolki = Column(Integer, nullable=True) # Wyliczona liczba rolek

    # Relacja zwrotna do zamówienia
    order = relationship("Order", back_populates="items")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, material='{self.material}')>"
