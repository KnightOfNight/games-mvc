from django.db import migrations


ORIGIN_DATA = [
    {'slug': 'highborn',    'name': 'Highborn',    'acuity_baseline': 1.0,  'acuity_band_low': 0.85, 'acuity_band_high': 1.15},
    {'slug': 'feral',       'name': 'Feral',       'acuity_baseline': 0.95, 'acuity_band_low': 0.80, 'acuity_band_high': 1.10},
    {'slug': 'streetborn',  'name': 'Streetborn',  'acuity_baseline': 1.0,  'acuity_band_low': 0.85, 'acuity_band_high': 1.15},
    {'slug': 'irradiated',  'name': 'Irradiated',  'acuity_baseline': 0.90, 'acuity_band_low': 0.75, 'acuity_band_high': 1.05},
    {'slug': 'undying',     'name': 'Undying',     'acuity_baseline': 0.80, 'acuity_band_low': 0.65, 'acuity_band_high': 1.00},
    {'slug': 'machinekind', 'name': 'Machinekind', 'acuity_baseline': 1.05, 'acuity_band_low': 0.90, 'acuity_band_high': 1.20},
    {'slug': 'voidtouched', 'name': 'Voidtouched', 'acuity_baseline': 0.70, 'acuity_band_low': 0.40, 'acuity_band_high': 1.30},
]

ARCHETYPE_DATA = [
    {'slug': 'blade',     'name': 'Blade',     'primary_stat_1': 'str', 'primary_stat_2': 'dex'},
    {'slug': 'bulwark',   'name': 'Bulwark',   'primary_stat_1': 'str', 'primary_stat_2': 'end'},
    {'slug': 'shade',     'name': 'Shade',     'primary_stat_1': 'dex', 'primary_stat_2': 'int'},
    {'slug': 'conduit',   'name': 'Conduit',   'primary_stat_1': 'int', 'primary_stat_2': 'wis'},
    {'slug': 'warden',    'name': 'Warden',    'primary_stat_1': 'wis', 'primary_stat_2': 'end'},
    {'slug': 'gunner',    'name': 'Gunner',    'primary_stat_1': 'dex', 'primary_stat_2': 'per'},
    {'slug': 'machinist', 'name': 'Machinist', 'primary_stat_1': 'int', 'primary_stat_2': 'dex'},
]


def seed_origins_and_archetypes(apps, schema_editor):
    Origin = apps.get_model('shyland', 'Origin')
    Archetype = apps.get_model('shyland', 'Archetype')

    for data in ORIGIN_DATA:
        Origin.objects.get_or_create(slug=data['slug'], defaults={
            'name': data['name'],
            'description': '',
            'acuity_baseline': data['acuity_baseline'],
            'acuity_band_low': data['acuity_band_low'],
            'acuity_band_high': data['acuity_band_high'],
        })

    for data in ARCHETYPE_DATA:
        Archetype.objects.get_or_create(slug=data['slug'], defaults={
            'name': data['name'],
            'description': '',
            'primary_stat_1': data['primary_stat_1'],
            'primary_stat_2': data['primary_stat_2'],
        })


def reverse_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shyland', '0013_archetype_origin_unarmedmessagepool_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_origins_and_archetypes, reverse_seed),
    ]
