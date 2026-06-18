from django.db import migrations

_ACUITY_DEFAULTS = {
    'highborn':    (1.0,  0.85, 1.15),
    'feral':       (0.95, 0.80, 1.10),
    'streetborn':  (1.0,  0.85, 1.15),
    'irradiated':  (0.90, 0.75, 1.05),
    'undying':     (0.80, 0.65, 1.00),
    'machinekind': (1.05, 0.90, 1.20),
    'voidtouched': (0.70, 0.40, 1.30),
}


def reset_acuity_defaults(apps, schema_editor):
    Character = apps.get_model('shyland', 'Character')
    for character in Character.objects.all():
        baseline, band_low, band_high = _ACUITY_DEFAULTS.get(
            character.origin, (1.0, 0.8, 1.2)
        )
        character.acuity_current = baseline
        character.acuity_baseline = baseline
        character.acuity_band_low = band_low
        character.acuity_band_high = band_high
        character.save(update_fields=[
            'acuity_current', 'acuity_baseline', 'acuity_band_low', 'acuity_band_high'
        ])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shyland', '0008_character_dying_since_character_is_dying_and_more'),
    ]

    operations = [
        migrations.RunPython(reset_acuity_defaults, reverse_code=noop),
    ]
