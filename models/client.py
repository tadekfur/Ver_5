from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from .db import Base, Session
from sqlalchemy.event import listens_for

CLIENT_NR_START = 567  # numeracja klientów zaczyna się od 000567

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    client_number = Column(String(6), unique=True, index=True)  # np. "000567"
    name = Column(String)
    short_name = Column(String)  # Dodane pole na "Nazwa skróc."
    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    street = Column(String)
    postal_code = Column(String)
    city = Column(String)
    nip = Column(String)
    delivery_company = Column(String)
    delivery_street = Column(String)
    delivery_postal_code = Column(String)
    delivery_city = Column(String)
    orders = relationship("Order", back_populates="client")

    __table_args__ = (
        UniqueConstraint('client_number', name='uq_client_number'),
    )

@listens_for(Client, "before_insert")
def before_insert_client(mapper, connection, target):
    # Automatyczne nadanie numeru klienta w formacie 000567, 000568, ...
    session = Session()
    try:
        last = session.query(Client).order_by(Client.client_number.desc()).first()
        if last and last.client_number and last.client_number.isdigit():
            next_nr = max(int(last.client_number) + 1, CLIENT_NR_START)
        else:
            next_nr = CLIENT_NR_START
        target.client_number = f"{next_nr:06d}"
    finally:
        session.close()