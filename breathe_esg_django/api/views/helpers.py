"""
views/helpers.py — Shared header extraction utilities.
Mirrors C# GetCompanyId() / GetAnalystName() / GetIpAddress() exactly.
"""
import uuid

DEFAULT_COMPANY_ID = '11111111-1111-1111-1111-111111111111'


def get_company_id(request) -> uuid.UUID:
    header = request.META.get('HTTP_X_COMPANY_ID', '')
    try:
        return uuid.UUID(header)
    except (ValueError, AttributeError):
        return uuid.UUID(DEFAULT_COMPANY_ID)


def get_analyst_name(request) -> str:
    return request.META.get('HTTP_X_ANALYST_NAME', 'System')


def get_ip_address(request) -> str:
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
