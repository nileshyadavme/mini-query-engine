import csv
import os


def load_csv(filepath):
    """
    Read a CSV file and return a list of dicts.

    Type inference order:
        1. Try int
        2. Try float
        3. Keep as string

    Keys are lowercased and stripped for consistent access.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: '{filepath}'")

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"Empty or header-less CSV: '{filepath}'")

        rows = []
        for row in reader:
            typed = {}
            for key, value in row.items():
                clean_key = key.strip().lower()
                typed[clean_key] = _infer_type(value.strip() if value else "")
            rows.append(typed)

    return rows


def _infer_type(value):
    """Try int → float → str in that order."""
    if value == "" or value is None:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value
