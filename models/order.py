from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .db import Base

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    order_number = Column(String, unique=True, index=True)
    order_date = Column(Date)
    delivery_date = Column(Date)
    client_id = Column(Integer, ForeignKey("clients.id"))
    notes = Column(Text)
    payment_term = Column(String)  # Dodane pole na termin płatności
    client = relationship("Client", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")