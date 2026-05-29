"""
rules.py — All 10 validation rules ported exactly from C# ValidationRules.cs.

Each rule is a class with:
  - applies_to: list of SourceType strings it applies to (empty = all)
  - validate(record_data: dict) -> Optional[dict]: returns flag dict or None
"""
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import List, Optional


# ---------------------------------------------------------------------------
# Base interface
# ---------------------------------------------------------------------------
class IValidationRule(ABC):
    applies_to: List[str] = []   # SourceType strings; empty = applies to all

    @abstractmethod
    def validate(self, record: dict) -> Optional[dict]:
        """Return a flag dict {rule_code, severity, description} or None."""
        ...

    @staticmethod
    def _flag(rule_code: str, severity: str, description: str) -> dict:
        return {'rule_code': rule_code, 'severity': severity, 'description': description}


# ---------------------------------------------------------------------------
# 1. NegativeValueRule — applies to all source types
# ---------------------------------------------------------------------------
class NegativeValueRule(IValidationRule):
    """
    Flags records where quantity is negative.
    A negative fuel or electricity value is always a data error —
    may indicate a credit note or export from SAP incorrectly included.
    """
    applies_to = []

    def validate(self, record: dict) -> Optional[dict]:
        quantity = record.get('quantity')
        if quantity is not None and Decimal(str(quantity)) < 0:
            return self._flag(
                'NEGATIVE_VALUE', 'Error',
                f'Quantity is negative ({quantity}). Negative consumption values are not valid. '
                'Check if this is a credit note or data export issue.'
            )
        return None


# ---------------------------------------------------------------------------
# 2. FutureDateRule — applies to all source types
# ---------------------------------------------------------------------------
class FutureDateRule(IValidationRule):
    """
    Flags records with activity dates in the future.
    Future dates can occur due to billing estimates or system clock misconfigurations.
    WARNING (not ERROR) because some utility billing extends slightly into the future.
    """
    applies_to = []

    def validate(self, record: dict) -> Optional[dict]:
        today = date.today()
        date_to_check = record.get('activity_date') or record.get('activity_period_end')
        if date_to_check and date_to_check > today:
            return self._flag(
                'FUTURE_DATE', 'Warning',
                f'Activity date {date_to_check} is in the future. '
                'Verify this is intentional (e.g., estimated billing).'
            )
        return None


# ---------------------------------------------------------------------------
# 3. MissingActivityDateRule — applies to all source types
# ---------------------------------------------------------------------------
class MissingActivityDateRule(IValidationRule):
    """
    Flags records where no activity date could be parsed.
    Date is mandatory for time-series analysis and GHG period reporting.
    """
    applies_to = []

    def validate(self, record: dict) -> Optional[dict]:
        if not record.get('activity_date') and not record.get('activity_period_start'):
            return self._flag(
                'MISSING_ACTIVITY_DATE', 'Error',
                'No activity date could be parsed from this record. '
                'Date is required for GHG period reporting.'
            )
        return None


# ---------------------------------------------------------------------------
# 4. MissingUnitRule — SAP + Utility only
# ---------------------------------------------------------------------------
class MissingUnitRule(IValidationRule):
    """
    Flags records with missing unit when quantity is present.
    A quantity without a unit makes the record useless for emissions calculation.
    """
    applies_to = ['SapFuel', 'UtilityElectricity']

    def validate(self, record: dict) -> Optional[dict]:
        quantity = record.get('quantity')
        unit = record.get('unit')
        if quantity is not None and not unit:
            return self._flag(
                'MISSING_UNIT', 'Error',
                'Quantity is present but unit of measurement is missing. '
                'Unit is required for normalization and emissions calculation.'
            )
        return None


# ---------------------------------------------------------------------------
# 5. UnrealisticFuelQuantityRule — SAP only
# ---------------------------------------------------------------------------
class UnrealisticFuelQuantityRule(IValidationRule):
    """
    Flags SAP fuel rows with unrealistically large quantities (> 50,000 L).
    This threshold would need to be configurable per company/plant in production.
    """
    MAX_REASONABLE_LITERS = Decimal('50000')
    applies_to = ['SapFuel']

    def validate(self, record: dict) -> Optional[dict]:
        unit = record.get('unit')
        quantity = record.get('quantity')
        if unit == 'l' and quantity is not None and Decimal(str(quantity)) > self.MAX_REASONABLE_LITERS:
            return self._flag(
                'UNREALISTIC_FUEL_QUANTITY', 'Warning',
                f'Fuel quantity {quantity:,} L exceeds the review threshold of {self.MAX_REASONABLE_LITERS:,} L. '
                'Verify this is a bulk tanker delivery, not a data entry error.'
            )
        return None


# ---------------------------------------------------------------------------
# 6. MissingMeterIdRule — Utility only
# ---------------------------------------------------------------------------
class MissingMeterIdRule(IValidationRule):
    """
    Flags utility records with missing meter ID.
    Without a meter ID, the reading cannot be attributed to a specific facility.
    """
    applies_to = ['UtilityElectricity']

    def validate(self, record: dict) -> Optional[dict]:
        location = record.get('location')
        if not location or location == 'Unknown Meter':
            return self._flag(
                'MISSING_METER_ID', 'Error',
                'No meter ID found in this record. '
                'Meter ID is required to attribute electricity consumption to a specific facility.'
            )
        return None


# ---------------------------------------------------------------------------
# 7. MissingBillingPeriodRule — Utility only
# ---------------------------------------------------------------------------
class MissingBillingPeriodRule(IValidationRule):
    """
    Flags utility records with missing billing period.
    Without start and end dates, consumption cannot be period-allocated for GHG reporting.
    """
    applies_to = ['UtilityElectricity']

    def validate(self, record: dict) -> Optional[dict]:
        if not record.get('activity_period_start') or not record.get('activity_period_end'):
            return self._flag(
                'MISSING_BILLING_PERIOD', 'Error',
                'Billing period start or end date is missing. '
                'Both dates are required to accurately allocate electricity consumption across months.'
            )
        return None


# ---------------------------------------------------------------------------
# 8. MissingDistanceRule — Corporate Travel only
# ---------------------------------------------------------------------------
class MissingDistanceRule(IValidationRule):
    """
    Flags travel records with missing distance.
    Hotels are exempt — distance doesn't apply to them.
    """
    applies_to = ['CorporateTravel']

    def validate(self, record: dict) -> Optional[dict]:
        if record.get('category') == 'Hotel':
            return None   # Hotels have no distance dimension
        quantity = record.get('quantity')
        if quantity is None or Decimal(str(quantity)) == 0:
            return self._flag(
                'MISSING_DISTANCE', 'Warning',
                f'Travel distance is missing for {record.get("category") or "trip"} record. '
                'Distance is required for GHG Scope 3 Category 6 calculation.'
            )
        return None


# ---------------------------------------------------------------------------
# 9. InvalidAirportCodeRule — Corporate Travel only
# ---------------------------------------------------------------------------
KNOWN_IATA_CODES = {
    'BOM', 'DEL', 'BLR', 'MAA', 'HYD', 'CCU', 'GOI', 'AMD', 'PNQ', 'COK',
    'LHR', 'LGW', 'MAN', 'CDG', 'AMS', 'FRA', 'DXB', 'SIN', 'HKG', 'NRT',
    'JFK', 'LAX', 'ORD', 'ATL', 'SFO', 'DFW', 'MIA', 'SEA', 'BOS', 'DEN',
    'SYD', 'MEL', 'AKL', 'DUB', 'ZRH', 'MUC', 'BCN', 'MAD', 'FCO', 'IST',
    'DOH', 'AUH', 'RUH', 'KUL', 'BKK', 'ICN', 'PVG', 'CAN', 'CTU', 'SHA',
}


class InvalidAirportCodeRule(IValidationRule):
    """
    Flags travel records with invalid IATA airport codes.
    Codes must be exactly 3 uppercase alpha characters and in the known set.
    """
    applies_to = ['CorporateTravel']

    def validate(self, record: dict) -> Optional[dict]:
        if record.get('category') != 'Flight':
            return None
        location = record.get('location')
        if not location:
            return None

        parts = [p.strip() for p in location.split('→')]
        invalid_codes = [
            code for code in parts
            if len(code) != 3 or not code.isalpha() or code.upper() not in KNOWN_IATA_CODES
        ]

        if invalid_codes:
            return self._flag(
                'INVALID_AIRPORT_CODE', 'Warning',
                f'Unrecognized airport code(s): {", ".join(invalid_codes)}. '
                'Verify these are valid IATA codes.'
            )
        return None


# ---------------------------------------------------------------------------
# 10. DuplicateTripRule — Corporate Travel only (STATEFUL — new instance per upload)
# ---------------------------------------------------------------------------
class DuplicateTripRule(IValidationRule):
    """
    Flags travel records that appear to be duplicates based on trip hash.
    The hash (employee + tripType + from + to + date) is injected by TravelNormalizationStrategy.
    Duplicates frequently occur when employees re-submit amended expense reports.
    IMPORTANT: This rule is stateful — instantiate a new instance per upload batch.
    """
    applies_to = ['CorporateTravel']

    def __init__(self):
        self._seen_hashes: set = set()

    def validate(self, record: dict) -> Optional[dict]:
        raw_payload = record.get('raw_payload', {})
        trip_hash = raw_payload.get('_tripHash') if isinstance(raw_payload, dict) else None

        if not trip_hash:
            return None

        if trip_hash in self._seen_hashes:
            return self._flag(
                'DUPLICATE_TRIP', 'Warning',
                'This trip appears to be a duplicate within this upload batch '
                '(same employee, route, and date). Possible expense re-submission.'
            )

        self._seen_hashes.add(trip_hash)
        return None
