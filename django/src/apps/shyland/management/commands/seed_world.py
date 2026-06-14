from django.core.management.base import BaseCommand
from apps.shyland.models import Zone, Room


class Command(BaseCommand):
    help = 'Seed The Convergence zone with its starting rooms'

    def handle(self, *args, **options):
        zone, _ = Zone.objects.get_or_create(
            slug='the-convergence',
            defaults={
                'name': 'The Convergence',
                'genre_tone': 'All genres collide',
                'danger_level': Zone.DANGER_SANCTUARY,
                'is_pvp_zone': False,
                'is_scaled': False,
                'description': (
                    'The Convergence is the beating heart of Shyland, where dimensional rifts '
                    'have stitched fragments of wildly different realities into an uneasy peace. '
                    'No violence is permitted here. Even the air feels cautiously neutral.'
                ),
            },
        )

        center, _ = Room.objects.get_or_create(
            zone=zone,
            name='The Fracture Point',
            defaults={
                'description': (
                    'You stand at the epicentre of the Convergence. The ground beneath your feet '
                    'is a mosaic of mismatched materials — cobblestone giving way to steel grating, '
                    'then bare earth, then smooth glass. Rifts of faint light pulse at the edges of '
                    'your vision. Travellers of every description pass through here: armoured knights '
                    'brush shoulders with neon-lit street samurai; hooded mystics trade words with '
                    'grease-stained machinists. Four passages lead outward from this hub.'
                ),
                'brief_description': 'The heart of the Convergence. Passages lead in four directions.',
                'coord_x': 0, 'coord_y': 0, 'coord_z': 0,
                'flag_safe': True,
            },
        )

        north, _ = Room.objects.get_or_create(
            zone=zone,
            name='The Northern Arcade',
            defaults={
                'description': (
                    'A vaulted arcade stretches before you, its arched columns carved from pale stone '
                    'yet threaded with glowing conduit lines. Market stalls line the promenade — vendors '
                    'hawk everything from enchanted blades to cracked datachips. The chatter of dozens '
                    'of languages fills the air, some of them not quite human.'
                ),
                'brief_description': 'A busy market arcade humming with mixed-world commerce.',
                'coord_x': 0, 'coord_y': 1, 'coord_z': 0,
                'flag_safe': True,
            },
        )

        south, _ = Room.objects.get_or_create(
            zone=zone,
            name='The Southern Docks',
            defaults={
                'description': (
                    'The air carries the scent of brine and machine oil in equal measure. Makeshift '
                    'piers jut into a canal whose water shifts hues with the rift-light overhead. '
                    'Flat-bottomed barges share moorings with sleek patrol skiffs. Dockhands argue '
                    'in three different tongues about cargo manifests that defy easy categorisation.'
                ),
                'brief_description': 'Canal docks where watercraft from a dozen realities tie up.',
                'coord_x': 0, 'coord_y': -1, 'coord_z': 0,
                'flag_safe': True,
            },
        )

        east, _ = Room.objects.get_or_create(
            zone=zone,
            name='The Eastern Bazaar',
            defaults={
                'description': (
                    'Colour and noise assault you from every angle. Canopies of silk and corrugated '
                    'polymer compete overhead. Spice-sellers, relic merchants, and data brokers jostle '
                    'for the same narrow lanes. At the far end, a tea-house with lantern-lit windows '
                    'promises respite from the clamour.'
                ),
                'brief_description': 'A chaotic open-air market overflowing with goods from everywhere.',
                'coord_x': 1, 'coord_y': 0, 'coord_z': 0,
                'flag_safe': True,
            },
        )

        west, _ = Room.objects.get_or_create(
            zone=zone,
            name='The Western Gate',
            defaults={
                'description': (
                    'Two enormous doors — one ancient iron-bound oak, the other brushed titanium — '
                    'stand permanently open in opposite directions, their frames fused together by '
                    'rift energy. Beyond the threshold the air shimmers, hinting at wilder territories. '
                    'A weathered sign reads: "Beyond here, the Convergence cannot protect you."'
                ),
                'brief_description': 'The boundary gate where the sanctuary ends and the world begins.',
                'coord_x': -1, 'coord_y': 0, 'coord_z': 0,
                'flag_safe': True,
            },
        )

        # Wire exits
        center.exit_north = north
        center.exit_south = south
        center.exit_east = east
        center.exit_west = west
        center.save()

        north.exit_south = center
        north.save()

        south.exit_north = center
        south.save()

        east.exit_west = center
        east.save()

        west.exit_east = center
        west.save()

        self.stdout.write(self.style.SUCCESS(
            f'Seeded: zone "{zone.name}" with 5 rooms. Starting room PK={center.pk}.'
        ))
        self.stdout.write(f'  Set new characters\' current_room to pk={center.pk}.')
