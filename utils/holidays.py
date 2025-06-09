# utils/holidays.py
# Lista dni ustawowo wolnych od pracy w Polsce na 2025 + funkcja sprawdzająca

import datetime

HOLIDAYS_2025 = [
    # Nowy Rok
    datetime.date(2025, 1, 1),
    # Trzech Króli
    datetime.date(2025, 1, 6),
    # Wielkanoc
    datetime.date(2025, 4, 20),
    # Poniedziałek Wielkanocny
    datetime.date(2025, 4, 21),
    # Święto Pracy
    datetime.date(2025, 5, 1),
    # Święto Konstytucji 3 Maja
    datetime.date(2025, 5, 3),
    # Zesłanie Ducha Świętego (Zielone Świątki)
    datetime.date(2025, 6, 8),
    # Boże Ciało
    datetime.date(2025, 6, 19),
    # Wniebowzięcie NMP
    datetime.date(2025, 8, 15),
    # Wszystkich Świętych
    datetime.date(2025, 11, 1),
    # Narodowe Święto Niepodległości
    datetime.date(2025, 11, 11),
    # Boże Narodzenie
    datetime.date(2025, 12, 25),
    # Drugi dzień Świąt Bożego Narodzenia
    datetime.date(2025, 12, 26),
    # Wigilia (od 2025 r. ustawowo wolna)
    datetime.date(2025, 12, 24),
]

def is_polish_holiday(date_obj):
    """Sprawdza, czy data to dzień wolny od pracy w Polsce w 2025."""
    return date_obj in HOLIDAYS_2025