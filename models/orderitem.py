from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    width = Column(String)
    height = Column(String)
    material = Column(String)
    ordered_quantity = Column(String)
    quantity_type = Column(String)
    roll_length = Column(String)
    core = Column(String)
    price = Column(String)        # NOWE POLE
    price_type = Column(String)   # NOWE POLE
    zam_rolki = Column(String)      # NOWE POLE

    order = relationship("Order", back_populates="items")