from sqlalchemy import Column, Integer
from .db import Base, Session
from sqlalchemy.exc import NoResultFound

ORDER_NR_START = 567   # numeracja zamówień zaczyna się od 000567

class OrderSequence(Base):
    __tablename__ = "order_sequence"
    id = Column(Integer, primary_key=True)
    last_number = Column(Integer, nullable=False, default=ORDER_NR_START - 1)

def get_next_order_number(session):
    """
    Zwraca kolejny unikalny numer zamówienia w formacie 000567/TER.
    Numer nigdy się nie powtórzy ani nie zmniejszy nawet po usunięciu zamówienia.
    """
    try:
        seq = session.query(OrderSequence).one()
    except NoResultFound:
        seq = OrderSequence(last_number=ORDER_NR_START - 1)
        session.add(seq)
        session.commit()
    seq.last_number += 1
    session.commit()
    return f"{seq.last_number:06d}/TER"

def set_last_order_number(session, order_number):
    """
    Ustawia ostatni numer zamówienia na podstawie numeru w formacie 000567/TER.
    Dzięki temu można nadpisać licznik jeżeli zamówienie było anulowane przed zapisem.
    Funkcja wyciąga liczbę z numeru (przed ukośnikiem).
    """
    try:
        num = int(order_number.split('/')[0])
    except Exception:
        return
    try:
        seq = session.query(OrderSequence).one()
    except NoResultFound:
        seq = OrderSequence(last_number=ORDER_NR_START - 1)
        session.add(seq)
        session.commit()
    if num > seq.last_number:
        seq.last_number = num
        session.commit()