import datetime
import pytest
from models.db import Session, create_db
from models.client import Client
from models.order import Order
from models.orderitem import OrderItem
from models.order_sequence import get_next_order_number, set_last_order_number

@pytest.fixture(scope="module")
def db_session():
    # Uwaga: To tworzy tabele, nie czyści istniejących danych!
    create_db()
    session = Session()
    yield session
    session.close()

def test_create_client(db_session):
    client = Client(
        name="Firma Testowa",
        contact_person="Jan Kowalski",
        phone="123456789",
        email="test@firma.pl",
        street="Testowa 1",
        postal_code="00-001",
        city="Warszawa",
        nip="1234567890",
        delivery_company="Kurier",
        delivery_street="Dostawcza 2",
        delivery_postal_code="00-002",
        delivery_city="Warszawa"
    )
    db_session.add(client)
    db_session.commit()
    found = db_session.query(Client).filter_by(email="test@firma.pl").first()
    assert found is not None
    assert found.name == "Firma Testowa"

def test_order_sequence(db_session):
    next_nr = get_next_order_number(db_session)
    assert next_nr.endswith("/TER")
    set_last_order_number(db_session, "000999/TER")
    newer = get_next_order_number(db_session)
    assert newer.startswith("001000")

def test_create_order_and_item(db_session):
    client = db_session.query(Client).first()
    order = Order(
        order_number="001000/TER",
        order_date=datetime.date(2025, 6, 1),
        delivery_date=datetime.date(2025, 6, 10),
        client_id=client.id,
        notes="Testowe zamówienie"
    )
    db_session.add(order)
    db_session.commit()
    item = OrderItem(
        order_id=order.id,
        width="50",
        height="100",
        material="Folia PET",
        ordered_quantity="10 000",
        quantity_type="sztuk",
        roll_length="100 m",
        core="76 mm",
        packaging="karton"
    )
    db_session.add(item)
    db_session.commit()
    found_order = db_session.query(Order).filter_by(order_number="001000/TER").first()
    assert found_order is not None
    assert len(found_order.items) > 0