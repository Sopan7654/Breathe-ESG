"""
travel_strategy.py — Normalizes Concur-style corporate travel JSON rows.

NORMALIZATION RULES:
1. tripType: flight, hotel, taxi, rail → category
2. distanceKm → quantity in "km" (may be null — flagged downstream)
3. from/to airport codes → location (IATA format: "BOM → BLR")
4. All travel records → Scope 3 (value chain emissions)
5. tripDate normalized from ISO or US date formats
6. Duplicate detection: hash of (employeeId + tripType + from + to + date)
   stored in raw_payload["_tripHash"] for downstream dedup flag rule
"""
import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from ..parsers.base import ParsedRow


TRIP_TYPE_NORMALIZATION = {
    'flight': 'Flight', 'air': 'Flight', 'airline': 'Flight',
    'hotel': 'Hotel', 'accommodation': 'Hotel', 'lodging': 'Hotel',
    'taxi': 'Taxi', 'cab': 'Taxi', 'rideshare': 'Taxi', 'uber': 'Taxi',
    'rail': 'Rail', 'train': 'Rail',
    'car rental': 'Car Rental', 'rental car': 'Car Rental',
    'bus': 'Bus',
    'ferry': 'Ferry',
}

DATE_FORMATS = [
    '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y',
    '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ',
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


def _normalize_trip_type(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return TRIP_TYPE_NORMALIZATION.get(raw.strip().lower(), raw.strip())


def _compute_trip_hash(employee_id, trip_type, from_code, to_code, date_str) -> str:
    """12-char hex hash for duplicate trip detection within an upload batch."""
    key = f'{employee_id}|{trip_type}|{from_code}|{to_code}|{date_str}'.lower()
    return hashlib.sha256(key.encode()).hexdigest()[:12]


class TravelNormalizationStrategy:
    """Port of C# TravelNormalizationStrategy. Scope 3."""

    def normalize(self, row: ParsedRow) -> dict:
        f = row.raw_fields

        employee_id = f.get('employeeId')
        raw_trip_type = f.get('tripType')
        from_code = (f.get('from') or '').upper().strip() or None
        to_code = (f.get('to') or '').upper().strip() or None
        raw_distance = f.get('distanceKm')
        raw_date = f.get('tripDate') or f.get('date') or f.get('departureDate')
        raw_cost = f.get('cost') or f.get('amount')
        currency = f.get('currency')

        quantity = _parse_decimal(raw_distance)
        activity_date = _parse_date(raw_date)
        category = _normalize_trip_type(raw_trip_type)

        # Build location
        if from_code and to_code:
            location = f'{from_code} → {to_code}'
        elif from_code:
            location = from_code
        elif to_code:
            location = to_code
        else:
            location = None

        # Build description
        parts = [f'{category or raw_trip_type or "Travel"} trip']
        if location:
            parts.append(f'route: {location}')
        if employee_id:
            parts.append(f'employee: {employee_id}')
        if raw_cost:
            cost_part = f'cost: {raw_cost}'
            if currency:
                cost_part += f' {currency}'
            parts.append(cost_part)
        description = ' | '.join(parts)

        # Trip hash for duplicate detection
        trip_hash = _compute_trip_hash(employee_id, raw_trip_type, from_code, to_code, raw_date)

        # Inject trip hash into raw_payload
        raw_payload = dict(row.raw_payload)
        raw_payload['_tripHash'] = trip_hash

        return {
            'source_type': 'CorporateTravel',
            'emission_scope': 'Scope3',
            'activity_date': activity_date,
            'activity_period_start': None,
            'activity_period_end': None,
            'quantity': quantity,
            'unit': 'km' if quantity is not None else None,
            'original_quantity': quantity,
            'original_unit': 'km' if raw_distance else None,
            'category': category or raw_trip_type,
            'location': location,
            'description': description,
            'raw_payload': raw_payload,
        }
