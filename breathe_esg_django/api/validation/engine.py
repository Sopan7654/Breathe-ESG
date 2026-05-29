"""
engine.py — ValidationEngine orchestrates all rules against a normalized record dict.

Rules with ERROR severity cause the record to become FLAGGED.
Rules with WARNING severity produce flags but the record stays PENDING.

Design: Adding a new rule = instantiate it in UploadService.build_validation_engine().
No modification to this engine class needed.
"""
from dataclasses import dataclass, field
from typing import List
from .rules import IValidationRule


@dataclass
class EngineResult:
    final_status: str          # 'Pending' or 'Flagged'
    flags: List[dict] = field(default_factory=list)


class ValidationEngine:
    """
    Runs all registered validation rules against a normalized record data dict.
    Returns an EngineResult with the final status and all generated flags.
    """

    def __init__(self, rules: List[IValidationRule]):
        self._rules = rules

    def validate(self, record_data: dict) -> EngineResult:
        """
        record_data: the dict of normalized fields (source_type, quantity, unit, etc.)
        Returns EngineResult with final_status and list of flag dicts.
        """
        flags = []
        has_error = False

        source_type = record_data.get('source_type', '')

        for rule in self._rules:
            # Skip rules that don't apply to this source type
            if rule.applies_to and source_type not in rule.applies_to:
                continue

            result = rule.validate(record_data)
            if result is None:
                continue

            flags.append({
                'rule_code': result['rule_code'],
                'severity': result['severity'],
                'description': result['description'],
            })

            if result['severity'] == 'Error':
                has_error = True

        final_status = 'Flagged' if has_error else 'Pending'
        return EngineResult(final_status=final_status, flags=flags)
