"""Read the CSV files in data/ into plain Python dicts.

No third-party dependencies -- stdlib csv only, so the repo runs on a
bare Python 3 install.
"""
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

PROJECTS_CSV = DATA_DIR / "projects.csv"
UNITS_CSV = DATA_DIR / "unit_inventory.csv"
TRANSACTIONS_CSV = DATA_DIR / "sales_transactions.csv"

SOLD_STATUSES = ("firm", "closed")


def _read(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def _to_int(row, *fields):
    for field in fields:
        row[field] = int(row[field])
    return row


def load_projects():
    """Return the project list, keyed order preserved from the CSV."""
    return [_to_int(r, "storeys", "total_units") for r in _read(PROJECTS_CSV)]


def load_units():
    """Return every tracked unit in the inventory."""
    return [
        _to_int(r, "floor", "beds", "baths", "interior_sqft",
                "balcony_sqft", "list_price")
        for r in _read(UNITS_CSV)
    ]


def load_transactions():
    """Return every recorded sale."""
    return [_to_int(r, "list_price", "sold_price") for r in _read(TRANSACTIONS_CSV)]


def projects_by_id():
    return {p["project_id"]: p for p in load_projects()}


def units_by_id():
    return {u["unit_id"]: u for u in load_units()}
