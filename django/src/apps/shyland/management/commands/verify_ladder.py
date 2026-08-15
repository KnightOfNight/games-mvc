"""v24.29 (#249 Part 2): the tier-material ladder survey.

Spec verbatim from V24.28 Brief 1 §7 step 8 — the survey that shipped to
production unverified because no session had a sanctioned path to run it,
and which spawned #248:

    Count existing ItemInstance rows on a ladder definition whose
    mk_tier falls outside that definition's range. Expected: 0.

Ladder membership is ``tier_material_mk_min is not null``. A null minimum
means the definition is simply not on the ladder — the freebie kit
suppresses its Mk suffix without joining it, and must not be counted.

A null ``tier_material_mk_max`` on a ladder definition is sphaerium's
shape: the rung is unbounded above and can never mismatch upward. Null is
not zero here.
"""

from django.db.models import F, Q

from apps.shyland.models import ItemInstance
from apps.shyland.verification import VerificationCommand


class Command(VerificationCommand):
    help = 'Report ItemInstance rows whose mk_tier falls outside their ladder rung (read-only).'

    def verify(self, *args, **options):
        ladder_rows = ItemInstance.objects.filter(
            definition__tier_material_mk_min__isnull=False,
        )
        total = ladder_rows.count()

        mismatched = ladder_rows.filter(
            Q(mk_tier__lt=F('definition__tier_material_mk_min'))
            | Q(
                definition__tier_material_mk_max__isnull=False,
                mk_tier__gt=F('definition__tier_material_mk_max'),
            )
        ).select_related('definition').order_by('definition__slug', 'pk')

        count = mismatched.count()
        self.stdout.write(
            f'verify_ladder: {count} mismatched instance(s) '
            f'out of {total} ladder row(s).')

        if not count:
            return []

        findings = []
        for item in mismatched:
            defn = item.definition
            bound_max = (
                'unbounded' if defn.tier_material_mk_max is None
                else defn.tier_material_mk_max
            )
            findings.append(
                f'{defn.slug}: instance {item.pk} at Mk {item.mk_tier} '
                f'(rung {defn.tier_material_mk_min}..{bound_max})')
        return findings
