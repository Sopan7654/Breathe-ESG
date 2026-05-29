"""
travel_json_parser.py — Parses Concur-style corporate travel JSON exports.

REALISTIC ASSUMPTIONS:
- SAP Concur exports are JSON arrays of trip/expense line items
- Each entry: flight, hotel, taxi, or rail leg
- May be wrapped: {"trips": [...]} or bare array [...]
- distanceKm is often null for hotel entries
- Airport codes can be invalid/misspelled
- Same trip may appear twice (expense re-submission)
- Dates: ISO or US format (M/D/YYYY)
"""
import json
from typing import List

from .base import ParsedRow


class TravelJsonParser:
    """
    Parses Concur-style corporate travel JSON exports into ParsedRow objects.
    Handles both bare JSON arrays and wrapped {"trips": [...]} format.
    """

    def parse(self, file_bytes: bytes, file_name: str) -> List[ParsedRow]:
        rows = []

        try:
            data = json.loads(file_bytes.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            rows.append(ParsedRow(row_number=1, parse_error=f'Invalid JSON: {exc}'))
            return rows

        # Unwrap if the root is an object containing an array
        if isinstance(data, dict):
            # Find first array value
            entries = next(
                (v for v in data.values() if isinstance(v, list)),
                []
            )
        elif isinstance(data, list):
            entries = data
        else:
            rows.append(ParsedRow(row_number=1, parse_error='JSON root must be an array or an object containing an array.'))
            return rows

        for row_number, entry in enumerate(entries, start=1):
            parsed = ParsedRow(row_number=row_number)
            try:
                if not isinstance(entry, dict):
                    parsed.parse_error = f'Entry {row_number}: expected object, got {type(entry).__name__}'
                    rows.append(parsed)
                    continue

                for key, value in entry.items():
                    parsed.raw_fields[key] = str(value) if value is not None else None

                parsed.raw_payload = dict(entry)  # Preserve original types for JSON storage
            except Exception as exc:
                parsed.parse_error = f'Entry {row_number}: {exc}'

            rows.append(parsed)

        return rows
