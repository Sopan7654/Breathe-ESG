"""
sap_strategy.py — Normalizes SAP fuel CSV rows into NormalizedRecord format.

NORMALIZATION RULES:
1. Dates: accepts ISO (YYYY-MM-DD) and German (DD.MM.YYYY) formats
2. Units: maps L/Liter/LITER → "l", KG/kg → "kg", M3 → "m3"
3. Plant + company_code → location field
4. Fuel type → category (maps German names to English)
5. All SAP fuel records → Scope 1 (direct combustion)
6. Quantity: handles both comma (1.200,50) and period (1200.50) decimal separators
"""
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from ..parsers.base import ParsedRow


UNIT_NORMALIZATION = {
    'l': 'l', 'liter': 'l', 'litre': 'l', 'ltr': 'l',
    'kg': 'kg', 'kilogram': 'kg',
    'm3': 'm3', 'cbm': 'm3', 'cubic meter': 'm3',
    't': 't', 'tonne': 't', 'ton': 't',
    'gal': 'gal', 'gallon': 'gal',
}

FUEL_TYPE_NORMALIZATION = {
    'diesel': 'Diesel', 'dieselkraftstoff': 'Diesel',
    'petrol': 'Petrol', 'benzin': 'Petrol', 'gasoline': 'Petrol',
    'natural gas': 'Natural Gas', 'erdgas': 'Natural Gas', 'cng': 'Natural Gas',
    'lpg': 'LPG', 'flüssiggas': 'LPG',
    'hfo': 'Heavy Fuel Oil', 'heizöl': 'Heavy Fuel Oil',
}

DATE_FORMATS = [
    '%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%-d.%-m.%Y',
    '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%y',
]


def _parse_quantity(raw: Optional[str]) -> Optional[Decimal]:
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    # German decimal format: 1.200,50 → 1200.50
    if ',' in raw and '.' in raw:
        raw = raw.replace('.', '').replace(',', '.')
    elif ',' in raw:
        raw = raw.replace(',', '.')
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    from datetime import datetime
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_unit(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return UNIT_NORMALIZATION.get(raw.strip().lower(), raw.strip().lower())


def _normalize_fuel_type(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return FUEL_TYPE_NORMALIZATION.get(raw.strip().lower(), raw.strip())


class SapNormalizationStrategy:
    """Port of C# SapNormalizationStrategy. Scope 1."""

    def normalize(self, row: ParsedRow) -> dict:
        """Returns a dict of field values for NormalizedRecord creation."""
        f = row.raw_fields

        raw_quantity_str = f.get('quantity')
        raw_unit = f.get('unit')
        raw_date = f.get('activity_date')
        raw_fuel_type = f.get('fuel_type')
        plant = f.get('plant')
        company_code = f.get('company_code')

        quantity = _parse_quantity(raw_quantity_str)
        normalized_unit = _normalize_unit(raw_unit)
        activity_date = _parse_date(raw_date)
        category = _normalize_fuel_type(raw_fuel_type)

        if plant and company_code:
            location = f'{company_code}/{plant}'
        else:
            location = plant or company_code or 'Unknown'

        description = f'SAP fuel consumption: {category or raw_fuel_type} at {location}'

        return {
            'source_type': 'SapFuel',
            'emission_scope': 'Scope1',
            'activity_date': activity_date,
            'activity_period_start': None,
            'activity_period_end': None,
            'quantity': quantity,
            'unit': normalized_unit,
            'original_quantity': quantity,
            'original_unit': raw_unit.strip() if raw_unit else None,
            'category': category or raw_fuel_type,
            'location': location,
            'description': description,
            'raw_payload': row.raw_payload,
        }
