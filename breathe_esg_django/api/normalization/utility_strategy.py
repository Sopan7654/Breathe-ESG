"""
utility_strategy.py — Normalizes utility electricity CSV rows.

NORMALIZATION RULES:
1. kWh variants → "kwh"
2. Billing period (start + end) → activity_period_start + activity_period_end
   activity_date = midpoint of billing period
3. Tariff → category (Industrial, Residential, Commercial)
4. All utility records → Scope 2 (purchased electricity)
5. Estimated vs Actual preserved in description
"""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

from ..parsers.base import ParsedRow


DATE_FORMATS = [
    '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%d-%m-%Y',
    '%d.%m.%Y', '%m-%d-%Y', '%Y/%m/%d',
]


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


def _parse_decimal(raw: Optional[str]) -> Optional[Decimal]:
    if not raw or not raw.strip():
        return None
    raw = raw.strip().replace(',', '')
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def _normalize_tariff(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    raw_lower = raw.strip().lower()
    if 'indust' in raw_lower:
        return 'Industrial'
    if 'resid' in raw_lower:
        return 'Residential'
    if 'comm' in raw_lower:
        return 'Commercial'
    return raw.strip()


class UtilityNormalizationStrategy:
    """Port of C# UtilityNormalizationStrategy. Scope 2."""

    def normalize(self, row: ParsedRow) -> dict:
        f = row.raw_fields

        meter_id = f.get('meter_id')
        billing_start = _parse_date(f.get('billing_start'))
        billing_end = _parse_date(f.get('billing_end'))
        raw_kwh = f.get('kwh')
        tariff = f.get('tariff')
        reading_type = f.get('reading_type')

        quantity = _parse_decimal(raw_kwh)

        # Activity date = midpoint of billing period
        activity_date = None
        if billing_start and billing_end:
            midpoint = billing_start + (billing_end - billing_start) / 2
            activity_date = midpoint
        else:
            activity_date = billing_start or billing_end

        category = _normalize_tariff(tariff)
        location = meter_id or 'Unknown Meter'
        is_estimated = reading_type and 'estim' in reading_type.lower()

        description = (
            f'Electricity consumption{"  (Estimated)" if is_estimated else ""}'
            f' — Meter: {location}, Tariff: {category or tariff}'
        )

        return {
            'source_type': 'UtilityElectricity',
            'emission_scope': 'Scope2',
            'activity_date': activity_date,
            'activity_period_start': billing_start,
            'activity_period_end': billing_end,
            'quantity': quantity,
            'unit': 'kwh',
            'original_quantity': quantity,
            'original_unit': 'kWh' if raw_kwh else None,
            'category': category or tariff,
            'location': location,
            'description': description,
            'raw_payload': row.raw_payload,
        }
