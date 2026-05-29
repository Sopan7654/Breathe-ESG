"""
0002_seed_initial_data.py — Inserts the same seed companies + data sources as C# EF Core.

Uses the same UUIDs so the existing frontend (X-Company-Id: 11111111-...) works unchanged.
This migration is idempotent — if the rows already exist it does nothing.
"""
from django.db import migrations


SEED_COMPANIES = [
    {
        'id': '11111111-1111-1111-1111-111111111111',
        'name': 'ABC Manufacturing Ltd.',
        'slug': 'abc',
    },
    {
        'id': '22222222-2222-2222-2222-222222222222',
        'name': 'GreenCorp Manufacturing',
        'slug': 'greencorp',
    },
]

SEED_DATA_SOURCES = [
    {
        'id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        'company_id': '11111111-1111-1111-1111-111111111111',
        'name': 'SAP ERP - Plant Operations',
        'source_type': 'SapFuel',
        'is_active': True,
    },
    {
        'id': 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
        'company_id': '11111111-1111-1111-1111-111111111111',
        'name': 'DESCO Utility Portal',
        'source_type': 'UtilityElectricity',
        'is_active': True,
    },
    {
        'id': 'cccccccc-cccc-cccc-cccc-cccccccccccc',
        'company_id': '11111111-1111-1111-1111-111111111111',
        'name': 'SAP Concur - Corporate Travel',
        'source_type': 'CorporateTravel',
        'is_active': True,
    },
]


def seed_data(apps, schema_editor):
    Company = apps.get_model('api', 'Company')
    DataSource = apps.get_model('api', 'DataSource')

    for data in SEED_COMPANIES:
        Company.objects.get_or_create(id=data['id'], defaults=data)

    for data in SEED_DATA_SOURCES:
        DataSource.objects.get_or_create(id=data['id'], defaults=data)


def unseed_data(apps, schema_editor):
    Company = apps.get_model('api', 'Company')
    DataSource = apps.get_model('api', 'DataSource')

    for data in SEED_DATA_SOURCES:
        DataSource.objects.filter(id=data['id']).delete()
    for data in SEED_COMPANIES:
        Company.objects.filter(id=data['id']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_data, reverse_code=unseed_data),
    ]
