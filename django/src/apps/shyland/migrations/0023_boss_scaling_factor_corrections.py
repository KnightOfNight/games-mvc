# Generated for Shyland v19 brief 7.
#
# NPC contest stats now scale additively (npc_level = scaling_factor +
# 10 * (mk_tier - 1)); scaling_factor encodes the NPC's within-band level
# (1-10). The six Z01 bosses had inflated scaling_factor values left over
# from the old multiplicative reading, placing them far outside their
# intended level band. Correct them to their level-band placements. Minion
# scaling_factor values were inspected and found already below their boss's
# corrected value (not inflated) — no minion changes required.

from django.db import migrations

BOSS_CORRECTIONS = {
    'silk-matron': 3.0,
    'whistler-below': 6.0,
    'dronemother': 6.0,
    'undercrag-weaver': 9.0,
    'chittering-king': 10.0,
    'crowned-devourer': 10.0,
}


def correct_boss_scaling_factors(apps, schema_editor):
    NpcDefinition = apps.get_model('shyland', 'NpcDefinition')
    for slug, new_sf in BOSS_CORRECTIONS.items():
        NpcDefinition.objects.filter(slug=slug).update(scaling_factor=new_sf)


def noop_reverse(apps, schema_editor):
    # Balance data correction, not reversible to a meaningful prior state.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shyland', '0022_combatsession_focus_npc'),
    ]

    operations = [
        migrations.RunPython(correct_boss_scaling_factors, noop_reverse),
    ]
