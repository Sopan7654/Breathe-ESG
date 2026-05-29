"""
utility_csv_parser.py — Parses utility electricity CSV exports.

REALISTIC ASSUMPTIONS:
- Always comma-delimited, UTF-8
- Headers vary by portal (Meter ID vs MeterId vs meter_id)
- Billing periods may span multiple months (non-calendar aligned)
- May include Estimated vs Actual reading flags
"""
import csv
import io
from typing import List

from .base import ParsedRow


HEADER_MAPPINGS = {
    'meter_id':       ['Meter ID', 'MeterID', 'Meter_ID', 'Account No', 'AccountNo'],
    'billing_start':  ['Billing Start', 'BillingStart', 'From', 'Period Start', 'Start Date'],
    'billing_end':    ['Billing End', 'BillingEnd', 'To', 'Period End', 'End Date'],
    'kwh':            ['kWh', 'KWH', 'Units', 'Consumption', 'Energy kWh', 'Usage'],
    'tariff':         ['Tariff', 'Rate Category', 'TariffCode', 'Category'],
    'reading_type':   ['Reading Type', 'ReadingType', 'Actual/Estimated', 'Type'],
    'account_name':   ['Account Name', 'AccountName', 'Consumer Name'],
    'invoice_number': ['Invoice', 'Invoice No', 'Bill No', 'InvoiceNumber'],
}


def _build_canonical_map(headers: List[str]) -> dict:
    result = {}
    for header in headers:
        for canonical, variants in HEADER_MAPPINGS.items():
            if any(v.lower() == header.strip().lower() for v in variants):
                result[header] = canonical
                break
    return result


class UtilityCsvParser:
    """
    Parses utility electricity CSV exports into ParsedRow objects.
    Flexible header mapping supports various utility portal formats.
    """

    def parse(self, file_bytes: bytes, file_name: str) -> List[ParsedRow]:
        rows = []
        text = file_bytes.decode('utf-8-sig', errors='replace')   # handles BOM

        reader = csv.DictReader(io.StringIO(text))

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

                parsed.raw_payload = dict(parsed.raw_fields)
            except Exception as exc:
                parsed.parse_error = f'Row {row_number}: {exc}'

            rows.append(parsed)

        return rows
