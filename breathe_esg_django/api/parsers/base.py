"""
parsers/base.py — Base types for the parsing layer.
ParsedRow is the universal intermediate representation produced by all parsers.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ParsedRow:
    """
    A single row of data extracted from any source format, before normalization.
    raw_fields: key-value pairs exactly as they appeared in the source file,
                with headers mapped to canonical names where possible.
    raw_payload_json: the entire row serialized as a dict (stored in NormalizedRecord.raw_payload).
    row_number: 1-based index in the source file (for error reporting).
    parse_error: human-readable error if this row failed to parse.
    """
    row_number: int = 0
    raw_fields: Dict[str, Optional[str]] = field(default_factory=dict)
    raw_payload: dict = field(default_factory=dict)
    parse_error: Optional[str] = None

    @property
    def has_parse_error(self) -> bool:
        return self.parse_error is not None
