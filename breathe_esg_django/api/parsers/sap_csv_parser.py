"""
sap_csv_parser.py — Parses SAP flat-file CSV exports.

REALISTIC ASSUMPTIONS (preserved from C#):
- SAP exports may use German column headers (Buchungskreis, Menge, Einheit, Datum, etc.)
- Date format is inconsistent: may be ISO (2025-01-10) or German (10.02.2025)
- File may use semicolons as delimiters (German locale SAP) or commas — we auto-detect.
- Encoding is typically Windows-1252 or UTF-8 with BOM — we handle both.
- Unknown headers are preserved as-is to avoid silent data loss.
"""
import csv
import io
import json
from typing import List

from .base import ParsedRow


# Canonical field name → list of possible German/SAP header variants (case-insensitive)
HEADER_MAPPINGS = {
    'company_code':  ['Buchungskreis', 'Company Code', 'CompanyCode'],
    'plant':         ['Plant', 'Werk', 'PLT'],
    'fuel_type':     ['Fuel_Type', 'Kraftstoffart', 'FuelType', 'Material'],
    'quantity':      ['Menge', 'Quantity', 'QTY', 'Amount'],
    'unit':          ['Einheit', 'Unit', 'UOM', 'Einh'],
    'activity_date': ['Datum', 'Date', 'Belegdatum', 'Posting Date'],
    'cost_center':   ['Kostenstelle', 'CostCenter', 'Cost Center'],
    'document_no':   ['Belegnummer', 'Document', 'Doc No'],
}


def _build_canonical_map(headers: List[str]) -> dict:
    """Map raw header strings → canonical field names."""
    result = {}
    for header in headers:
        for canonical, variants in HEADER_MAPPINGS.items():
            if any(v.lower() == header.strip().lower() for v in variants):
                result[header] = canonical
                break
    return result


def _detect_encoding(raw_bytes: bytes) -> str:
    """Decode bytes, handling UTF-8 BOM and Windows-1252 fallback."""
    # Strip UTF-8 BOM
    if raw_bytes[:3] == b'\xef\xbb\xbf':
        return raw_bytes[3:].decode('utf-8', errors='replace')
    try:
        return raw_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return raw_bytes.decode('windows-1252', errors='replace')


def _detect_delimiter(text: str) -> str:
    """If semicolons outnumber commas in the first line, use semicolon."""
    first_line = text.split('\n', 1)[0]
    return ';' if first_line.count(';') > first_line.count(',') else ','


class SapCsvParser:
    """
    Parses SAP fuel CSV exports into ParsedRow objects.
    Auto-detects delimiter and encoding.
    Maps German/SAP headers to canonical names.
    """

    def parse(self, file_bytes: bytes, file_name: str) -> List[ParsedRow]:
        rows = []
        raw_text = _detect_encoding(file_bytes)
        delimiter = _detect_delimiter(raw_text)

        reader = csv.DictReader(io.StringIO(raw_text), delimiter=delimiter)

        if reader.fieldnames is None:
            rows.append(ParsedRow(row_number=1, parse_error='CSV file has no headers.'))
            return rows

        headers = list(reader.fieldnames)
        canonical_map = _build_canonical_map(headers)

        for row_number, csv_row in enumerate(reader, start=2):
            parsed = ParsedRow(row_number=row_number)
            try:
                for header in headers:
                    raw_value = csv_row.get(header, '').strip() or None
                    canonical_key = canonical_map.get(header, header)
                    parsed.raw_fields[canonical_key] = raw_value

                parsed.raw_payload = {k: v for k, v in parsed.raw_fields.items()}
            except Exception as exc:
                parsed.parse_error = f'Row {row_number}: {exc}'

            rows.append(parsed)

        return rows
