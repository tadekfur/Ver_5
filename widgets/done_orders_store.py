import os
import json

DONE_ORDERS_FILE = "done_orders_store.json"

class DoneOrdersStore:
    def __init__(self, filename=DONE_ORDERS_FILE):
        self.filename = filename
        self.done_ids = set()
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.done_ids = set(data)
            except Exception:
                self.done_ids = set()
        else:
            self.done_ids = set()

    def save(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(list(self.done_ids), f)
        except Exception:
            pass

    def is_done(self, order_id):
        return order_id in self.done_ids

    def mark_done(self, order_id):
        self.done_ids.add(order_id)
        self.save()

    def clear_all(self):
        self.done_ids.clear()
        self.save()

    def remove(self, order_id):
        if order_id in self.done_ids:
            self.done_ids.remove(order_id)
            self.save()

done_orders_store = DoneOrdersStore()