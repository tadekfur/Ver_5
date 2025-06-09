from fpdf import FPDF
import os
import sys
import webbrowser
import datetime
import re

def format_pdf_value(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime("%Y-%m-%d")
    return str(value) if value is not None else ""

def format_cena(cena, cena_typ):
    if not cena:
        return ""
    cena_str = str(cena)
    typ = str(cena_typ).lower().replace(".", "").replace(" ", "")
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

def orderitem_to_pdf_row(orderitem):
    width = str(getattr(orderitem, "width", getattr(orderitem, "Szerokość", "")))
    height = str(getattr(orderitem, "height", getattr(orderitem, "Wysokość", "")))
    wymiar = f"{width}x{height}" if width and height else width or height
    material = getattr(orderitem, "material", getattr(orderitem, "Rodzaj materiału", ""))
    roll_length = getattr(orderitem, "roll_length", getattr(orderitem, "nawój/długość", ""))
    core = getattr(orderitem, "core", getattr(orderitem, "Średnica rdzenia", ""))
    ordered_quantity = getattr(orderitem, "ordered_quantity", getattr(orderitem, "zam. ilość", ""))
    miara = getattr(orderitem, "quantity_type", getattr(orderitem, "Typ ilości", ""))
    zam_rolki = getattr(orderitem, "zam. rolki", getattr(orderitem, "zam_rolki", ""))
    cena = getattr(orderitem, "Cena", getattr(orderitem, "price", ""))
    cena_typ = getattr(orderitem, "price_type", getattr(orderitem, "CenaTyp", ""))
    cena_sufix = format_cena(cena, cena_typ)
    return [
        wymiar, material, roll_length, core, ordered_quantity, miara, zam_rolki, cena_sufix
    ]

class ProductionTicketPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A5')
        self.set_auto_page_break(False)
        self.margin_left = 6
        self.margin_top = 6
        self.page_width = 148
        self.page_height = 210
        self.ticket_height = 90
        self.ticket_spacing = 6

        folder = os.path.dirname(__file__)
        font_regular = os.path.join(folder, "DejaVuSans.ttf")
        font_bold = os.path.join(folder, "DejaVuSans-Bold.ttf")
        self.add_font("DejaVu", "", font_regular, uni=True)
        self.add_font("DejaVu", "B", font_bold, uni=True)
        self.add_font("DejaVu", "I", font_regular, uni=True)  # fallback for italic if needed

    def draw_cut_mark(self):
        y_cut = self.page_height / 2
        x1 = self.margin_left
        x2 = self.page_width - self.margin_left
        self.set_draw_color(180, 180, 180)
        self.set_line_width(0.6)
        self.line(x1, y_cut, x2, y_cut)
        self.set_text_color(120, 120, 120)
        self.set_font("DejaVu", "", 8)
        self.set_xy(x2 - 20, y_cut - 4)
        self.cell(20, 5, "--- cięcie ---", border=0, align="R")
        self.set_text_color(0, 0, 0)

    def fit_font_size(self, text, width, max_fontsize=7, min_fontsize=5):
        """Dopasuj wielkość fontu do pojedynczej linii żeby tekst się zmieścił."""
        font_size = max_fontsize
        while font_size >= min_fontsize:
            self.set_font("DejaVu", "", font_size)
            if self.get_string_width(text) <= width:
                return font_size
            font_size -= 0.2
        return min_fontsize

    def multi_cell_row(self, col_widths, row, align='C', max_font=7, min_font=5):
        """Rysuje wiersz tabeli z automatycznym zawijaniem i dopasowaniem fontu."""
        n = len(row)
        # Sprawdź ile linii potrzeba dla każdej komórki
        font_sizes = []
        lines = []
        for i in range(n):
            cell_val = str(row[i])
            font_size = self.fit_font_size(cell_val, col_widths[i], max_font, min_font)
            self.set_font("DejaVu", "", font_size)
            # policz ile linii zajmuje tekst przy tej szerokości
            line_count = len(self.multi_cell_preview(col_widths[i], 5, cell_val))
            lines.append(line_count)
            font_sizes.append(font_size)
        max_lines = max(lines)
        y_start = self.get_y()
        x_start = self.get_x()
        # Rysuj każdą komórkę
        for i in range(n):
            self.set_font("DejaVu", "", font_sizes[i])
            self.set_xy(x_start + sum(col_widths[:i]), y_start)
            self.multi_cell(col_widths[i], 5, str(row[i]), border=1, align=align, fill=True)
            self.set_xy(x_start + sum(col_widths[:i+1]), y_start)
        self.set_y(y_start + max_lines * 5)

    def multi_cell_preview(self, w, h, txt):
        # Helper: podziel tekst na linie jak zrobiłoby to MultiCell (do ustalenia wysokości)
        # FPDF nie udostępnia takiej funkcji, więc używamy prostego podziału.
        result = []
        words = txt.split()
        line = ""
        for word in words:
            test_line = (line + " " + word).strip()
            if self.get_string_width(test_line) <= w:
                line = test_line
            else:
                result.append(line)
                line = word
        if line:
            result.append(line)
        return result

    def ticket(self, order, client, order_items, y_offset, table_full_width=False):
        x = self.margin_left
        if y_offset > 0:
            y = self.margin_top + y_offset + 10
        else:
            y = self.margin_top + y_offset

        box_h = 8
        black = (0, 0, 0)
        color_border = (180, 180, 200)
        color_grey = (245, 245, 245)
        color_white = (255, 255, 255)

        # --- Górny czarny pasek i bloki dat ---
        self.set_xy(x, y)
        self.set_fill_color(*black)
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVu", "B", 9)
        self.cell(56, box_h, f"Nr zamówienia: {format_pdf_value(getattr(order, 'order_number', getattr(order, 'Nr zamówienia', '')))}", border=0, align="L", fill=True)

        self.set_font("DejaVu", "B", 8)
        date_order_label = "Data zamówienia:"
        date_order_label_w = self.get_string_width(date_order_label) + 6
        date_order_x = x + 58
        date_order_y = y
        self.set_fill_color(*black)
        self.set_line_width(0.2)
        self.rect(date_order_x, date_order_y, date_order_label_w, box_h, style='F')
        self.set_line_width(0.2)
        self.set_xy(date_order_x, date_order_y)
        self.set_text_color(255, 255, 255)
        self.cell(date_order_label_w, box_h, date_order_label, border=0, align="L")

        wysylka_label = "Data wysyłki:"
        wysylka_label_w = self.get_string_width(wysylka_label) + 6
        wysylka_x = date_order_x + date_order_label_w + 15
        wysylka_y = y
        self.set_fill_color(*black)
        self.set_line_width(0.2)
        self.rect(wysylka_x, wysylka_y, wysylka_label_w, box_h, style='F')
        self.set_line_width(0.2)
        self.set_xy(wysylka_x, wysylka_y)
        self.set_text_color(255, 255, 255)
        self.cell(wysylka_label_w, box_h, wysylka_label, border=0, align="L")

        # Daty
        self.set_text_color(0, 0, 0)
        self.set_font("DejaVu", "", 8)
        self.set_xy(date_order_x, y + box_h)
        self.cell(date_order_label_w, 5, format_pdf_value(getattr(order, "order_date", getattr(order, "Data zamówienia", ""))), border=0, align="L")
        self.set_xy(wysylka_x, y + box_h)
        self.cell(wysylka_label_w, 5, format_pdf_value(getattr(order, "delivery_date", getattr(order, "Data dostawy", ""))), border=0, align="L")

        y += box_h + 5

        self.set_font("DejaVu", "B", 8)
        self.set_text_color(0, 0, 0)
        self.set_xy(x, y)
        self.cell(40, 4, "Dane klienta", ln=0, align="L")
        self.set_x(x + 60)
        self.cell(0, 4, "Adres dostawy", ln=1, align="L")

        self.set_font("DejaVu", "B", 7)
        y_klient = self.get_y()
        nazwa_skrocona = getattr(client, 'short_name', getattr(client, 'Nazwa skrócona', ''))
        klient_info = [
            ("Firma", nazwa_skrocona if nazwa_skrocona else getattr(client, 'name', getattr(client, 'Firma', ''))),
            ("Nr klienta", getattr(client, 'client_number', getattr(client, 'Nr klienta', ''))),
            ("Ulica i nr", getattr(client, 'street', getattr(client, 'Ulica i nr', ''))),
            ("Kod poczt.", getattr(client, 'postal_code', getattr(client, 'Kod pocztowy', ''))),
            ("Miasto", getattr(client, 'city', getattr(client, 'Miasto', '')))
        ]
        for idx, (label, value) in enumerate(klient_info):
            if value:
                self.set_xy(x, y_klient + idx * 4)
                self.set_font("DejaVu", "B", 7)
                self.cell(18, 4, f"{label}:", border=0)
                self.set_font("DejaVu", "", 7)
                self.cell(20, 4, format_pdf_value(value), border=0)

        # --- Adres dostawy (zawsze uzupełnij danymi firmy jeżeli brak adresu dostawy) ---
        self.set_font("DejaVu", "B", 7)
        self.set_xy(x + 60, y_klient)
        delivery_company = getattr(client, "delivery_company", "") or getattr(client, "name", "")
        delivery_street = getattr(client, "delivery_street", "") or getattr(client, "street", "")
        delivery_postal_code = getattr(client, "delivery_postal_code", "") or getattr(client, "postal_code", "")
        delivery_city = getattr(client, "delivery_city", "") or getattr(client, "city", "")
        contact_person = getattr(client, "contact_person", None)
        contact_phone = getattr(client, "phone", None)

        address_labels = [
            ("Firma", delivery_company),
            ("Ulica i nr", delivery_street),
            ("Kod poczt.", delivery_postal_code),
            ("Miasto", delivery_city),
        ]
        any_adres = any(val for (_, val) in address_labels)

        for idx, (lab, val) in enumerate(address_labels):
            if val:
                self.set_xy(x + 60, y_klient + idx * 4)
                self.set_font("DejaVu", "B", 7)
                self.cell(18, 4, f"{lab}:", border=0)
                self.set_font("DejaVu", "", 7)
                self.cell(34, 4, format_pdf_value(val), ln=1, border=0)

        offset = len(address_labels)
        # Dodaj osobę kontaktową w adresie dostawy (etkieta "Osoba kont.")
        if contact_person:
            self.set_xy(x + 60, y_klient + offset * 4)
            self.set_font("DejaVu", "B", 7)
            self.cell(18, 4, "Osoba kont.:", border=0)
            self.set_font("DejaVu", "", 7)
            self.cell(34, 4, format_pdf_value(contact_person), ln=1, border=0)
            offset += 1
        # Dodaj telefon osoby kontaktowej (etkieta "tel")
        if contact_phone:
            self.set_xy(x + 60, y_klient + offset * 4)
            self.set_font("DejaVu", "B", 7)
            self.cell(18, 4, "tel:", border=0)
            self.set_font("DejaVu", "", 7)
            self.cell(34, 4, format_pdf_value(contact_phone), ln=1, border=0)
            offset += 1

        if not any_adres and not contact_person and not contact_phone:
            self.set_xy(x + 60, y_klient)
            self.set_font("DejaVu", "I", 7)
            self.cell(0, 4, "brak danych", ln=1, align="L")

        y_table = y_klient + 22 + (4 * (offset - len(address_labels)) if (contact_person or contact_phone) else 0)

        filtered_items = [item for item in order_items if str(getattr(item, "width", getattr(item, "Szerokość", ""))).strip() != ""]
        if filtered_items:
            col_headers = ["Lp.", "Wymiar", "Materiał", "Na rolce", "Rdzeń", "Ilość", "Miara", "zam. rolki", "Cena"]
            rows = []
            for i, produkt in enumerate(filtered_items, 1):
                row = orderitem_to_pdf_row(produkt)
                row_new = [str(i)] + row
                rows.append(row_new)
            total_width = self.page_width - 2 * self.margin_left
            self.set_font("DejaVu", "B", 7)
            col_widths = self.get_dynamic_col_widths(col_headers, rows, total_width, min_width=10, max_width=70, padding=1)

            table_x = x
            table_y = y_table + 5

            self.set_xy(table_x, y_table)
            self.set_fill_color(180, 200, 245)
            self.set_text_color(40, 80, 160)
            self.set_font("DejaVu", "B", 8)
            self.cell(sum(col_widths), 6, "Dane produkcji", ln=1, fill=True)

            self.set_xy(table_x, table_y)
            self.set_font("DejaVu", "B", 7)
            self.set_text_color(0, 0, 0)
            for w, h in zip(col_widths, col_headers):
                self.set_fill_color(180, 200, 245)
                self.set_draw_color(*color_border)
                self.set_line_width(0.2)
                self.cell(w, 5, h, border=1, align="C", fill=True)
            self.ln()

            # Wiersze z automatycznym zawijaniem i dopasowaniem fontu:
            self.set_font("DejaVu", "", 7)
            for i, row in enumerate(rows):
                self.set_x(table_x)
                bg = color_grey if i % 2 == 1 else color_white
                self.set_fill_color(*bg)
                self.multi_cell_row(col_widths, row, align='C', max_font=7, min_font=5)
            y_uwagi = self.get_y() + 1
        else:
            y_uwagi = y_table

        self.set_x(x)
        self.set_font("DejaVu", "B", 7)
        self.cell(0, 4, "Uwagi:", ln=1, align="L")
        self.set_font("DejaVu", "", 6)
        self.set_x(x)
        self.multi_cell(110, 4, format_pdf_value(getattr(order, "notes", getattr(order, "Uwagi", ""))), align="L")

    def get_dynamic_col_widths(self, headers, rows, total_width, min_width=10, max_width=70, padding=1):
        n = len(headers)
        col_widths = [min_width] * n
        for i, header in enumerate(headers):
            w = self.get_string_width(str(header)) + 2 * padding
            col_widths[i] = max(col_widths[i], min(w, max_width))
        for row in rows:
            for i, val in enumerate(row):
                w = self.get_string_width(str(val)) + 2 * padding
                col_widths[i] = max(col_widths[i], min(w, max_width))
        sum_width = sum(col_widths)
        if sum_width != total_width:
            scale = total_width / sum_width if sum_width > 0 else 1
            col_widths = [w * scale for w in col_widths]
            diff = total_width - sum(col_widths)
            if col_widths:
                col_widths[-1] += diff
        return col_widths

def clean_filename(name):
    import re
    return re.sub(r'[^a-zA-Z0-9._-]', '_', name)

def export_production_ticket(order, client, order_items, filename=None):
    output_dir = r"c:\\produkcja"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    safe_order = clean_filename(str(getattr(order, "order_number", getattr(order, "Nr zamówienia", "zamowienie"))))
    safe_name = clean_filename(str(getattr(client, "name", getattr(client, "Firma", "klient"))))
    if not filename:
        filename = f"{safe_order}_{safe_name}_PRODUKCJA.pdf"
    output_path = os.path.join(output_dir, filename)

    pdf = ProductionTicketPDF()
    pdf.add_page()
    pdf.ticket(order, client, order_items, y_offset=0)
    pdf.draw_cut_mark()
    pdf.ticket(order, client, order_items, y_offset=pdf.ticket_height + pdf.ticket_spacing, table_full_width=True)

    pdf.output(output_path)

    abs_path = os.path.abspath(output_path)
    if sys.platform.startswith("win"):
        os.startfile(abs_path)
    elif sys.platform.startswith("darwin"):
        os.system(f'open "{abs_path}"')
    else:
        try:
            webbrowser.open(f'file://{abs_path}')
        except Exception:
            os.system(f'xdg-open "{abs_path}"')