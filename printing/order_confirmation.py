from fpdf import FPDF
import os
import sys
import webbrowser
import datetime

def orderitem_to_pdf_dict(orderitem):
    def format_cena(cena, cena_typ):
        if not cena:
            return ""
        cena_str = str(cena)
        typ = str(cena_typ).lower()
        typ = typ.replace(".", "").replace(" ", "")
        typ = (typ.replace("ę", "e")
                  .replace("ł", "l")
                  .replace("ó", "o")
                  .replace("ą", "a")
                  .replace("ś", "s")
                  .replace("ć", "c")
                  .replace("ń", "n")
                  .replace("ź", "z")
                  .replace("ż", "z"))
        if "rol" in typ:
            return f"{cena_str} /rolka"
        elif "tys" in typ or "tyś" in typ:
            return f"{cena_str} /tyś"
        else:
            return cena_str

    if isinstance(orderitem, dict):
        cena_typ = orderitem.get("price_type") or orderitem.get("CenaTyp") or ""
        width = str(orderitem.get("Szerokość", orderitem.get("width", "")))
        height = str(orderitem.get("Wysokość", orderitem.get("height", "")))
        wymiar = f"{width} x {height}" if width and height else width or height
        cena = orderitem.get("Cena", orderitem.get("price", ""))
        miara = orderitem.get("quantity_type") or orderitem.get("Typ ilości") or ""
        return {
            "Wymiar": wymiar,
            "Rodzaj materiału": orderitem.get("Rodzaj materiału", orderitem.get("material", "")),
            "Ilość na rolce": orderitem.get("nawój/długość", orderitem.get("roll_length", "")),
            "Średnica rdzenia": orderitem.get("Średnica rdzenia", orderitem.get("core", "")),
            "Ilość": orderitem.get("zam. ilość", orderitem.get("ordered_quantity", "")),
            "Miara": miara,
            "zam. rolki": orderitem.get("zam. rolki", orderitem.get("zam_rolki", "")),
            "Cena": format_cena(cena, cena_typ)
        }
    else:
        cena_typ = getattr(orderitem, "price_type", "") or getattr(orderitem, "CenaTyp", "")
        width = str(getattr(orderitem, "Szerokość", getattr(orderitem, "width", "")))
        height = str(getattr(orderitem, "Wysokość", getattr(orderitem, "height", "")))
        wymiar = f"{width} x {height}" if width and height else width or height
        cena = getattr(orderitem, "Cena", getattr(orderitem, "price", ""))
        miara = getattr(orderitem, "quantity_type", "") or getattr(orderitem, "Typ ilości", "")
        return {
            "Wymiar": wymiar,
            "Rodzaj materiału": getattr(orderitem, "Rodzaj materiału", getattr(orderitem, "material", "")),
            "Ilość na rolce": getattr(orderitem, "nawój_długość", getattr(orderitem, "roll_length", "")),
            "Średnica rdzenia": getattr(orderitem, "Średnica rdzenia", getattr(orderitem, "core", "")),
            "Ilość": getattr(orderitem, "zam_ilość", getattr(orderitem, "ordered_quantity", "")),
            "Miara": miara,
            "zam. rolki": getattr(orderitem, "zam. rolki", getattr(orderitem, "zam_rolki", "")),
            "Cena": format_cena(cena, cena_typ)
        }

def client_to_pdf_dict(client):
    if isinstance(client, dict):
        return client
    return {
        "Firma": getattr(client, "company_name", getattr(client, "name", "")),
        "Nr klienta": getattr(client, "client_number", ""),
        "Osoba kontakt.": getattr(client, "contact_person", ""),
        "Nr telefonu": getattr(client, "phone", ""),
        "E-mail": getattr(client, "email", ""),
        "Ulica i nr": getattr(client, "street", ""),
        "Kod pocztowy": getattr(client, "postal_code", ""),
        "Miasto": getattr(client, "city", ""),
        "NIP": getattr(client, "nip", ""),
        "delivery_company": getattr(client, "delivery_company", ""),
        "delivery_street": getattr(client, "delivery_street", ""),
        "delivery_postal_code": getattr(client, "delivery_postal_code", ""),
        "delivery_city": getattr(client, "delivery_city", ""),
    }

def format_pdf_value(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime("%Y-%m-%d")
    return str(value) if value is not None else ""

class PDFGenerator:
    def __init__(self, order):
        self.order = order

    def generate_pdf(self, filename="output.pdf"):
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=5)
        left_margin = 10
        right_margin = 10
        top_margin = 10
        pdf.set_margins(left=left_margin, top=top_margin, right=right_margin)
        pdf.add_page()

        folder = os.path.dirname(__file__)
        font_regular = os.path.join(folder, "DejaVuSans.ttf")
        font_bold = os.path.join(folder, "DejaVuSans-Bold.ttf")
        pdf.add_font("DejaVu", "", font_regular, uni=True)
        pdf.add_font("DejaVu", "B", font_bold, uni=True)

        color_accent = (77, 144, 254)
        color_header_bg = (0, 0, 0)
        color_white = (255, 255, 255)
        color_grey = (245, 245, 245)
        color_border = (180, 180, 200)

        # --- Dane firmy Termedia ---
        pdf.set_xy(left_margin, 15)
        pdf.set_font("DejaVu", "B", 13.5)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, "TERMEDIA", ln=1, align="L")
        pdf.set_font("DejaVu", "", 8)
        pdf.set_x(left_margin)
        pdf.cell(0, 4, "ul. Przemysłowa 60", ln=1, align="L")
        pdf.set_x(left_margin)
        pdf.cell(0, 4, "43-110 Tychy", ln=1, align="L")
        pdf.set_x(left_margin)
        pdf.cell(0, 4, "bok@termedialabels.pl", ln=1, align="L")
        pdf.set_x(left_margin)
        pdf.cell(0, 4, "www.termedialabels.pl", ln=1, align="L")
        pdf.set_x(left_margin)
        pdf.cell(0, 4, "+48 503 179 658", ln=1, align="L")
        pdf.ln(1)

        # --- Blok "Zamówienie" i nr zamówienia ---
        blok_x = left_margin + 60
        blok_y = 15
        ramka_w = 120
        ramka_h = 11
        pdf.set_xy(blok_x, blok_y)
        pdf.set_fill_color(0, 0, 0)
        pdf.rect(blok_x, blok_y, ramka_w, ramka_h, style='F')
        pdf.set_xy(blok_x + 4, blok_y + 1.5)
        pdf.set_font("DejaVu", "B", 11)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(45, 8, "Zamówienie", ln=0, align="L")
        nr_zamowienia = format_pdf_value(self.order.get('Nr zamówienia', ''))
        pdf.set_font("DejaVu", "B", 11)
        pdf.set_xy(blok_x + 52, blok_y + 1.5)
        pdf.cell(0, 8, f"Nr zamówienia: {nr_zamowienia}", ln=0, align="L")

        przesuniecie_dol = 20

        # Daty
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_fill_color(0, 0, 0)
        pdf.set_xy(left_margin, 33 + przesuniecie_dol)
        pdf.cell(64, 8, "Data zamówienia:", ln=0, align="L", fill=True)
        pdf.set_xy(left_margin + 68, 33 + przesuniecie_dol)
        pdf.cell(64, 8, "Data wysyłki:", ln=0, align="L", fill=True)
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(left_margin, 41 + przesuniecie_dol)
        data_zamowienia = format_pdf_value(self.order.get("Data zamówienia", ""))
        pdf.cell(64, 7, data_zamowienia, ln=0, align="L")
        pdf.set_xy(left_margin + 68, 41 + przesuniecie_dol)
        data_dostawy = format_pdf_value(self.order.get("Data dostawy", ""))
        pdf.cell(64, 7, data_dostawy, ln=0, align="L")
        pdf.ln(14)

        # Dane klienta (lewo)
        klient_x = left_margin + 5
        pdf.set_xy(klient_x, 51 + przesuniecie_dol)
        pdf.set_font("DejaVu", "B", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(60, 7, "Dane klienta", ln=0, align="L")

        # Adres dostawy - PRZESUNIĘCIE BLOKU O 1,5 CM W PRAWO (czyli +15mm)
        adres_blok_x = left_margin + 90 - 20 + 30
        pdf.set_x(adres_blok_x)
        pdf.cell(0, 7, "Adres dostawy", ln=1, align="L")

        klient_info = [
            (u"Firma", self.order.get('Firma', '')),
            (u"Nr klienta", self.order.get('Nr klienta', '')),
            (u"Osoba kontakt.", self.order.get('Osoba kontakt.', self.order.get('Osoba kontaktowa', ''))),
            (u"Nr telefonu", self.order.get('Nr telefonu', '')),
            (u"E-mail", self.order.get('E-mail', '')),
            (u"Ulica i nr", self.order.get('Ulica i nr', '')),
            (u"Kod pocztowy", self.order.get('Kod pocztowy', '')),
            (u"Miasto", self.order.get('Miasto', '')),
            (u"NIP", self.order.get('NIP', '')),
        ]
        y_klient = pdf.get_y()

        # --- Automatyczne zawijanie tekstu w komórce "Firma" i przesuwanie reszty w dół ---
        firma_label = klient_info[0][0]
        firma_value = klient_info[0][1]
        pdf.set_xy(klient_x + 3, y_klient)
        pdf.set_font("DejaVu", "B", 8)
        pdf.cell(30, 6, f"{firma_label}:", border=0)
        pdf.set_font("DejaVu", "", 8)
        firma_cell_width = 60
        pdf.multi_cell(firma_cell_width, 6, format_pdf_value(firma_value), border=0, align="L")
        after_firma_y = pdf.get_y()
        for idx, (label, value) in enumerate(klient_info[1:]):
            if value:
                pdf.set_xy(klient_x + 3, after_firma_y + idx * 6)
                pdf.set_font("DejaVu", "B", 8)
                pdf.cell(30, 6, f"{label}:", border=0)
                pdf.set_font("DejaVu", "", 8)
                pdf.cell(0, 6, format_pdf_value(value), ln=0, align="L")

        # --- Adres dostawy, jeśli nie podano, to dane firmy + osoba kontaktowa i telefon ---
        adres = self.order.get("Adres dostawy", {})
        pdf.set_font("DejaVu", "B", 8)
        pdf.set_xy(adres_blok_x + 3, y_klient)
        adres_labels = [
            ("Firma", "firma"),
            ("Ulica i nr", "ulica"),
            ("Kod pocztowy", "kod_pocztowy"),
            ("Miejscowość", "miejscowość"),
            ("Osoba kont.", "osoba_kont"),
            ("tel", "telefon"),
        ]
        for idx, (lab, key) in enumerate(adres_labels):
            val = adres.get(key, "")
            if val:
                pdf.set_xy(adres_blok_x + 3, y_klient + idx * 6)
                pdf.set_font("DejaVu", "B", 8)
                pdf.cell(36, 6, f"{lab}:", border=0)
                pdf.set_font("DejaVu", "", 8)
                pdf.cell(0, 6, format_pdf_value(val), ln=0, align="L")
        
        # ZMIANA TUTAJ: Zmniejszenie odstępu przed tabelą produkcji
        pdf.ln(40) # Poprzednio było pdf.ln(74)

        # Dane produkcji
        pdf.set_x(left_margin)
        pdf.set_font("DejaVu", "B", 10.5)
        prod_title_width = pdf.get_string_width("Dane produkcji") + 10
        pdf.set_fill_color(180, 200, 245)
        pdf.set_text_color(40, 80, 160)
        pdf.cell(prod_title_width, 9, "Dane produkcji", ln=1, fill=True)
        pdf.ln(1)

        produkty = self.order.get("Dane produkcji", [])
        produkty = [
            produkt for produkt in produkty
            if (produkt.get("Wymiar", "") or produkt.get("width", "") or produkt.get("Szerokość", ""))
            and (str(produkt.get("Wymiar", "")) != "" or str(produkt.get("width", "")) != "" or str(produkt.get("Szerokość", "")) != "")
        ]
        pdf.set_x(left_margin)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("DejaVu", "B", 7.5)
        table_headers = [
            "Lp.", "Wymiar", "Materiał", "Na rolce", "Rdzeń", "Ilość", "Miara", "zam. rolki", "Cena"
        ]
        col_widths = [9, 28, 37, 22, 14, 16, 18, 18, 22]

        pdf.set_x(left_margin)
        for w, h in zip(col_widths, table_headers):
            pdf.set_fill_color(180, 200, 245)
            pdf.set_draw_color(*color_border)
            pdf.cell(w, 6.5, h, border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_font("DejaVu", "", 7.5)
        for i, produkt in enumerate(produkty, 1):
            wymiar = format_pdf_value(produkt.get("Wymiar", ""))
            material = format_pdf_value(produkt.get("Rodzaj materiału", ""))
            na_rolce = format_pdf_value(produkt.get("Ilość na rolce", ""))
            rdzen = format_pdf_value(produkt.get("Średnica rdzenia", ""))
            ilosc = format_pdf_value(produkt.get("Ilość", ""))
            miara = format_pdf_value(produkt.get("Miara", ""))
            zam_rolki = format_pdf_value(produkt.get("zam. rolki", produkt.get("zam_rolki", "")))
            cena = format_pdf_value(produkt.get("Cena", ""))
            row = [
                str(i),
                wymiar,
                material,
                na_rolce,
                rdzen,
                ilosc,
                miara,
                zam_rolki,
                cena
            ]
            pdf.set_x(left_margin)
            bg = color_grey if i % 2 == 0 else color_white
            pdf.set_fill_color(*bg)
            for w, cell_val in zip(col_widths, row):
                pdf.cell(w, 6, str(cell_val), border=1, align="C", fill=True)
            pdf.ln()

        # Uwagi pod tabelą
        pdf.ln(3)
        pdf.set_x(left_margin)
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, "Uwagi:", ln=1, align="L")
        pdf.set_font("DejaVu", "", 8)
        pdf.set_x(left_margin)
        uwagi = self.order.get("Uwagi", "")
        pdf.multi_cell(176, 6, format_pdf_value(uwagi), align="L")
        pdf.ln(6)

        # Dodany tekst 8 pkt, wycentrowany, maksymalnie w dół
        pdf.set_y(pdf.h - 18)  # 18 mm od dołu (A4 = 297 mm, więc na 279 mm)
        pdf.set_font("DejaVu", "", 8)
        pdf.set_text_color(0, 0, 0)
        pdf.set_x(left_margin)
        pdf.cell(
            190 - left_margin - right_margin, 6,
            "Podany termin wysyłki jest orientacyjny, w razie zmian poinformujemy w osobnej wiadomości.",
            align="C"
        )

        # Stopka przesunięta wyżej, aby nie kolidowała z tekstem 8 pkt
        pdf.set_font("DejaVu", "", 4)
        pdf.set_text_color(130, 130, 130)
        pdf.set_y(284)
        center_text = "Wygenerowano automatycznie przez LabelOrderManager"
        text_width = pdf.get_string_width(center_text)
        page_center = 105
        pdf.set_x(page_center - text_width / 2)
        pdf.cell(text_width, 3, center_text, align="C")

        pdf.output(filename)

        abs_path = os.path.abspath(filename)
        if sys.platform.startswith("win"):
            os.startfile(abs_path)
        elif sys.platform.startswith("darwin"):
            os.system(f'open "{abs_path}"')
        else:
            try:
                webbrowser.open(f'file://{abs_path}')
            except Exception:
                os.system(f'xdg-open "{abs_path}"')

def export_order_to_pdf(order, client, order_items, filename):
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    client_dict = client_to_pdf_dict(client) if client else {}
    order_items_dicts = [orderitem_to_pdf_dict(item) for item in (order_items or [])]
    order_data = dict(order) if isinstance(order, dict) else {}

    if "Nr zamówienia" not in order_data:
        if "order_number" in order_data:
            order_data["Nr zamówienia"] = order_data["order_number"]
        elif hasattr(order, "order_number"):
            order_data["Nr zamówienia"] = getattr(order, "order_number", "")
    if "Data zamówienia" not in order_data:
        if "order_date" in order_data:
            order_data["Data zamówienia"] = order_data["order_date"]
        elif hasattr(order, "order_date"):
            order_data["Data zamówienia"] = getattr(order, "order_date", "")
    if "Data dostawy" not in order_data:
        if "delivery_date" in order_data:
            order_data["Data dostawy"] = order_data["delivery_date"]
        elif hasattr(order, "delivery_date"):
            order_data["Data dostawy"] = getattr(order, "delivery_date", "")

    if "Uwagi" not in order_data:
        if "notes" in order_data:
            order_data["Uwagi"] = order_data["notes"]
        elif hasattr(order, "notes"):
            order_data["Uwagi"] = getattr(order, "notes", "")

    order_data.update(client_dict)
    if order_items_dicts:
        order_data['Dane produkcji'] = order_items_dicts

    # GŁÓWNA ZMIANA: sekcja adresu dostawy jak w production ticket:
    if "Adres dostawy" not in order_data or not order_data["Adres dostawy"]:
        adres_dostawy = {
            "firma": order_data.get("delivery_company", "") or order_data.get("Firma", ""),
            "ulica": order_data.get("delivery_street", "") or order_data.get("Ulica i nr", ""),
            "kod_pocztowy": order_data.get("delivery_postal_code", "") or order_data.get("Kod pocztowy", ""),
            "miejscowość": order_data.get("delivery_city", "") or order_data.get("Miasto", ""),
            "osoba_kont": order_data.get("Osoba kontakt.", "") or order_data.get("contact_person", ""),
            "telefon": order_data.get("Nr telefonu", "") or order_data.get("phone", ""),
        }
        adres_dostawy = {k: v for k, v in adres_dostawy.items() if v}
        order_data["Adres dostawy"] = adres_dostawy

    for key in ["Data zamówienia", "Data dostawy"]:
        if key in order_data and isinstance(order_data[key], (datetime.date, datetime.datetime)):
            order_data[key] = order_data[key].strftime("%Y-%m-%d")

    pdfgen = PDFGenerator(order_data)
    pdfgen.generate_pdf(filename)