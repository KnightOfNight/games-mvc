from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from apps.shyland.models import (
    Area, Archetype, Character, EffectComponent, EffectDefinition, ItemDefinition,
    LootTable, LootTableEntry, NpcDefinition, Origin, Room, RoomSpawn,
    TravelMessage, TravelNode, VendorEntry, Zone,
    UnarmedMessage, UnarmedMessagePool,
)

WEAPON_DUR = [
    {'min': 75, 'max': 100, 'penalty': 0.0},
    {'min': 50, 'max': 75,  'penalty': 0.25},
    {'min': 25, 'max': 50,  'penalty': 0.35},
    {'min': 1,  'max': 25,  'penalty': 0.50},
    {'min': 0,  'max': 0,   'penalty': 1.0},
]

RANGED_DUR = [
    {'min': 75, 'max': 100, 'penalty': 0.0},
    {'min': 50, 'max': 75,  'penalty': 0.20},
    {'min': 25, 'max': 50,  'penalty': 0.30},
    {'min': 1,  'max': 25,  'penalty': 0.45},
    {'min': 0,  'max': 0,   'penalty': 1.0},
]

ARMOR_DUR = [
    {'min': 75, 'max': 100, 'penalty': 0.0},
    {'min': 50, 'max': 75,  'penalty': 0.15},
    {'min': 25, 'max': 50,  'penalty': 0.25},
    {'min': 1,  'max': 25,  'penalty': 0.40},
    {'min': 0,  'max': 0,   'penalty': 1.0},
]

KEEP_OFF_GRASS = 'The park lawn stretches away. A small sign reads: Please keep off the grass.'

DIRECTIONS = ('north', 'south', 'east', 'west', 'up', 'down')

OPPOSITE = {
    'north': 'south', 'south': 'north',
    'east': 'west', 'west': 'east',
    'up': 'down', 'down': 'up',
}

# The ring street as a clockwise walk: each entry is (room key, direction of the
# next clockwise step). The last entry steps back to the first, closing the loop.
RING_WALK = [
    ('r01', 'east'), ('r02', 'east'), ('r03', 'east'), ('r04', 'east'),
    ('r05', 'south'), ('r33', 'south'), ('r06', 'south'), ('r07', 'south'),
    ('r08', 'south'), ('r09', 'south'), ('r10', 'south'), ('r11', 'south'),
    ('r12', 'south'), ('r34', 'west'), ('r13', 'west'), ('r14', 'west'),
    ('r15', 'west'), ('r16', 'west'), ('r17', 'west'), ('r18', 'west'),
    ('r19', 'west'), ('r20', 'west'), ('r35', 'north'), ('r21', 'north'),
    ('r22', 'north'), ('r23', 'north'), ('r24', 'north'), ('r25', 'north'),
    ('r26', 'north'), ('r27', 'north'), ('r28', 'east'), ('r29', 'east'),
    ('r30', 'east'), ('r31', 'east'), ('r32', 'east'),
]

# Park paths and the smithy, as (source key, direction, destination key).
PATH_EDGES = [
    # Wisteria Walk (north path; NW jog between WW-1 and WW-2)
    ('heart', 'north', 'ww1'), ('ww1', 'south', 'heart'),
    ('ww1', 'west', 'ww2'), ('ww2', 'east', 'ww1'),
    ('ww2', 'north', 'ww3'), ('ww3', 'south', 'ww2'),
    ('ww3', 'north', 'ww4'), ('ww4', 'south', 'ww3'),
    ('ww4', 'north', 'r01'), ('r01', 'south', 'ww4'),
    # Bamboo Run (east path)
    ('heart', 'east', 'br1'), ('br1', 'west', 'heart'),
    ('br1', 'east', 'br2'), ('br2', 'west', 'br1'),
    ('br2', 'east', 'br3'), ('br3', 'west', 'br2'),
    ('br3', 'east', 'r10'), ('r10', 'west', 'br3'),
    # Basalt Way (south path; east jog between BW-1 and BW-2)
    ('heart', 'south', 'bw1'), ('bw1', 'north', 'heart'),
    ('bw1', 'east', 'bw2'), ('bw2', 'west', 'bw1'),
    ('bw2', 'south', 'bw3'), ('bw3', 'north', 'bw2'),
    ('bw3', 'south', 'bw4'), ('bw4', 'north', 'bw3'),
    ('bw4', 'south', 'bw5'), ('bw5', 'north', 'bw4'),
    ('bw5', 'south', 'r18'), ('r18', 'north', 'bw5'),
    # Fern Boards (west path; the north jog is absorbed into a straight west walk)
    ('heart', 'west', 'fb1'), ('fb1', 'east', 'heart'),
    ('fb1', 'west', 'fb2'), ('fb2', 'east', 'fb1'),
    ('fb2', 'west', 'fb3'), ('fb3', 'east', 'fb2'),
    ('fb3', 'west', 'fb4'), ('fb4', 'east', 'fb3'),
    ('fb4', 'west', 'r24'), ('r24', 'east', 'fb4'),
    # Morra's Smithy (north across the ring street from R01)
    ('r01', 'north', 'smithy_ext'), ('smithy_ext', 'south', 'r01'),
    ('smithy_ext', 'north', 'smithy_int'), ('smithy_int', 'south', 'smithy_ext'),
]

# The Verdant Reach (v18 briefs 5 and 6), as one-way canonical edges. Each
# entry is expanded to its reverse pair at wiring time — direction pairs are
# always wired both ways.
VR_EDGES_ONE_WAY = [
    # The Verdant gate: Green Gate ring room ↔ the Tree Arch
    ('r02', 'north', 'vr-v01'),
    # Fernwater Vale spine
    ('vr-v01', 'north', 'vr-v02'), ('vr-v02', 'north', 'vr-v03'),
    ('vr-v03', 'north', 'vr-v04'), ('vr-v04', 'north', 'vr-v05'),
    ('vr-v05', 'north', 'vr-v07'), ('vr-v07', 'north', 'vr-v08'),
    ('vr-v08', 'north', 'vr-v09'), ('vr-v09', 'north', 'vr-v10'),
    ('vr-v10', 'north', 'vr-v11'), ('vr-v11', 'north', 'vr-v12'),
    ('vr-v12', 'north', 'vr-v13'), ('vr-v13', 'north', 'vr-v14'),
    ('vr-v14', 'north', 'vr-v15'), ('vr-v15', 'north', 'vr-v16'),
    # Vale offshoots
    ('vr-v04', 'east', 'vr-v06'), ('vr-v09', 'west', 'vr-v17'),
    ('vr-v10', 'east', 'vr-v18'), ('vr-v11', 'west', 'vr-rm1'),
    ('vr-v12', 'east', 'vr-v19'), ('vr-v13', 'east', 'vr-v20'),
    ('vr-v14', 'west', 'vr-v21'), ('vr-v15', 'east', 'vr-v22'),
    # Reedmere
    ('vr-rm1', 'north', 'vr-rm2'), ('vr-rm1', 'west', 'vr-rm3'),
    # Spinner's Hollow and the Silken Cleft
    ('vr-v20', 'east', 'vr-c1a'),
    ('vr-v22', 'east', 'vr-c2a'), ('vr-c2a', 'north', 'vr-c2b'),
    ('vr-c2b', 'north', 'vr-c2c'), ('vr-c2c', 'north', 'vr-c2d'),
    # The ancient stair
    ('vr-v16', 'north', 'vr-s1'), ('vr-s1', 'north', 'vr-s2'),
    ('vr-s2', 'north', 'vr-s3'), ('vr-s3', 'north', 'vr-s4'),
    ('vr-s4', 'north', 'vr-s5'), ('vr-s5', 'north', 'vr-f01'),
    # Sagewind Flats spine
    ('vr-f01', 'north', 'vr-f02'), ('vr-f02', 'north', 'vr-f03'),
    ('vr-f03', 'north', 'vr-f04'), ('vr-f04', 'north', 'vr-f05'),
    ('vr-f05', 'north', 'vr-f06'), ('vr-f06', 'north', 'vr-f07'),
    ('vr-f07', 'north', 'vr-f08'), ('vr-f08', 'north', 'vr-f09'),
    ('vr-f09', 'north', 'vr-f16'), ('vr-f16', 'north', 'vr-f18'),
    # Flats offshoots
    ('vr-f03', 'west', 'vr-f10'), ('vr-f04', 'east', 'vr-f11'),
    ('vr-f05', 'west', 'vr-w1'), ('vr-w1', 'north', 'vr-w2'),
    ('vr-f06', 'east', 'vr-f12'), ('vr-f07', 'west', 'vr-f13'),
    ('vr-f08', 'east', 'vr-f14'), ('vr-f09', 'west', 'vr-f15'),
    ('vr-f16', 'east', 'vr-f17'),
    # The Whistling Sink
    ('vr-f12', 'down', 'vr-c3a'), ('vr-c3a', 'north', 'vr-c3b'),
    ('vr-c3b', 'north', 'vr-c3c'), ('vr-c3c', 'east', 'vr-c3d'),
    ('vr-c3c', 'north', 'vr-c3e'), ('vr-c3e', 'north', 'vr-c3f'),
    # The Drone Pit
    ('vr-f14', 'down', 'vr-c4a'), ('vr-c4a', 'north', 'vr-c4b'),
    ('vr-c4b', 'north', 'vr-c4c'), ('vr-c4c', 'east', 'vr-c4d'),
    ('vr-c4c', 'north', 'vr-c4e'), ('vr-c4e', 'down', 'vr-c4f'),
    ('vr-c4e', 'north', 'vr-c4g'), ('vr-c4g', 'north', 'vr-c4h'),
    # The Viridian Ridge spine (v18 brief 6): Cragfoot to the Verdant Crown
    ('vr-f18', 'north', 'vr-c01'), ('vr-c01', 'north', 'vr-m01'),
    ('vr-m01', 'north', 'vr-m02'), ('vr-m02', 'north', 'vr-m03'),
    ('vr-m03', 'north', 'vr-m04'), ('vr-m04', 'north', 'vr-m05'),
    ('vr-m05', 'north', 'vr-m06'), ('vr-m06', 'north', 'vr-m07'),
    ('vr-m07', 'north', 'vr-m08'), ('vr-m08', 'north', 'vr-m14'),
    ('vr-m14', 'north', 'vr-m15'), ('vr-m15', 'north', 'vr-m16'),
    ('vr-m16', 'north', 'vr-m17'), ('vr-m17', 'north', 'vr-m18'),
    ('vr-m18', 'north', 'vr-m19'), ('vr-m19', 'north', 'vr-m20'),
    ('vr-m20', 'north', 'vr-m21'), ('vr-m21', 'north', 'vr-m27'),
    ('vr-m27', 'north', 'vr-m28'), ('vr-m28', 'north', 'vr-m29'),
    ('vr-m29', 'north', 'vr-m30'), ('vr-m30', 'north', 'vr-m31'),
    ('vr-m31', 'north', 'vr-m32'), ('vr-m32', 'north', 'vr-m33'),
    ('vr-m33', 'north', 'vr-m34'), ('vr-m34', 'north', 'vr-m35'),
    ('vr-m35', 'north', 'vr-m41'), ('vr-m41', 'north', 'vr-vc1'),
    # Ridge offshoots, vistas, and the four AGGRO grounds
    ('vr-m02', 'east', 'vr-m09'), ('vr-m04', 'west', 'vr-m10'),
    ('vr-m07', 'east', 'vr-m12'), ('vr-m15', 'east', 'vr-m22'),
    ('vr-m17', 'west', 'vr-m23'), ('vr-m20', 'west', 'vr-m26'),
    ('vr-m27', 'west', 'vr-m43'), ('vr-m28', 'east', 'vr-m36'),
    ('vr-m30', 'west', 'vr-m37'), ('vr-m32', 'west', 'vr-m38'),
    ('vr-m33', 'east', 'vr-m39'), ('vr-m35', 'east', 'vr-m42'),
    # Ridge villages (each with its warned-about aggro offshoot)
    ('vr-m06', 'east', 'vr-st1'), ('vr-st1', 'north', 'vr-st2'),
    ('vr-st2', 'north', 'vr-m11'),
    ('vr-m18', 'east', 'vr-hf1'), ('vr-hf1', 'north', 'vr-hf2'),
    ('vr-hf2', 'west', 'vr-m24'),
    ('vr-m31', 'east', 'vr-ll1'), ('vr-ll1', 'north', 'vr-ll2'),
    # The Undercrag
    ('vr-m08', 'east', 'vr-m13'), ('vr-m13', 'east', 'vr-c5a'),
    ('vr-c5a', 'down', 'vr-c5b'), ('vr-c5b', 'north', 'vr-c5c'),
    ('vr-c5c', 'up', 'vr-c5d'), ('vr-c5c', 'north', 'vr-c5e'),
    ('vr-c5e', 'down', 'vr-c5f'), ('vr-c5f', 'down', 'vr-c5g'),
    ('vr-c5f', 'north', 'vr-c5h'), ('vr-c5h', 'north', 'vr-c5i'),
    # Chitterdeep
    ('vr-m21', 'east', 'vr-m25'), ('vr-m25', 'east', 'vr-c6a'),
    ('vr-c6a', 'down', 'vr-c6b'), ('vr-c6b', 'down', 'vr-c6c'),
    ('vr-c6c', 'east', 'vr-c6d'), ('vr-c6c', 'north', 'vr-c6e'),
    ('vr-c6e', 'down', 'vr-c6f'), ('vr-c6e', 'north', 'vr-c6g'),
    ('vr-c6g', 'north', 'vr-c6h'), ('vr-c6h', 'up', 'vr-c6i'),
    ('vr-c6i', 'north', 'vr-c6j'),
    # Hollowcrown
    ('vr-m34', 'east', 'vr-m40'), ('vr-m40', 'east', 'vr-c7a'),
    ('vr-c7a', 'north', 'vr-c7b'), ('vr-c7b', 'up', 'vr-c7c'),
    ('vr-c7c', 'east', 'vr-c7d'), ('vr-c7c', 'north', 'vr-c7e'),
    ('vr-c7e', 'up', 'vr-c7f'), ('vr-c7f', 'east', 'vr-c7g'),
    ('vr-c7f', 'north', 'vr-c7h'), ('vr-c7h', 'up', 'vr-c7i'),
    ('vr-c7i', 'north', 'vr-c7j'), ('vr-c7j', 'north', 'vr-c7k'),
]


def vr_edges():
    edges = []
    for src, direction, dst in VR_EDGES_ONE_WAY:
        edges.append((src, direction, dst))
        edges.append((dst, OPPOSITE[direction], src))
    return edges

# These NPCs never fight — stats are placeholders.
MINIMAL_STATS = {
    'base_vitality': 999,
    'base_str': 1, 'base_dex': 1, 'base_end': 1,
    'base_int': 1, 'base_wis': 1, 'base_per': 1,
    'scaling_factor': 1.0,
}


class Command(BaseCommand):
    help = 'Seed The Convergence zone with the Infinity City starting area'

    def handle(self, *args, **options):
        self.rooms = {}
        self._cleanup_placeholders()
        zone = self._seed_zone()
        areas = self._seed_areas(zone)
        self._seed_rooms(zone, areas)
        vr_zone = self._seed_verdant_zone()
        vr_areas = self._seed_verdant_areas(vr_zone)
        self._seed_verdant_rooms_vale(vr_zone, vr_areas)
        self._seed_verdant_rooms_flats(vr_zone, vr_areas)
        self._seed_verdant_rooms_caves(vr_zone, vr_areas)
        self._seed_ridge_rooms_leg1(vr_zone, vr_areas)
        self._seed_ridge_rooms_leg2(vr_zone, vr_areas)
        self._seed_ridge_rooms_leg3(vr_zone, vr_areas)
        self._seed_undercrag_rooms(vr_zone, vr_areas)
        self._seed_chitterdeep_rooms(vr_zone, vr_areas)
        self._seed_hollowcrown_rooms(vr_zone, vr_areas)
        self._wire_exits()
        self._seed_convergence_npcs()
        self._seed_primordial_sphere()
        self._seed_travel_nodes()
        self._seed_travel_messages()
        self._set_character_rooms()

        self._seed_unarmed_pools()
        self._seed_origins()
        self._seed_archetypes()
        self._seed_effects()
        self._seed_items()

        self._seed_verdant_loot_tables()
        self._seed_verdant_npcs()
        self._seed_verdant_spawns()
        self._seed_verdant_vendors()

        self._seed_ridge_loot_tables()
        self._seed_ridge_npcs()
        self._seed_ridge_spawns()
        self._seed_ridge_vendors()

        self._verify()

    # ------------------------------------------------------------------
    # Cleanup — remove the pre-Infinity City placeholder content
    # ------------------------------------------------------------------

    def _cleanup_placeholders(self):
        placeholder_room_names = [
            'The Fracture Point',
            'The Northern Arcade',
            'The Southern Docks',
            'The Eastern Bazaar',
            'The Western Gate',
        ]
        room_deleted, _ = Room.objects.filter(
            zone__slug='the-convergence',
            name__in=placeholder_room_names,
        ).delete()

        placeholder_npc_slugs = ['goblin-scout', 'training-dummy', 'fracture-wraith']
        npc_deleted, _ = NpcDefinition.objects.filter(slug__in=placeholder_npc_slugs).delete()

        area_deleted, _ = Area.objects.filter(slug='the-fracture-point-plaza').delete()

        self.stdout.write(
            f'Cleanup: {room_deleted} placeholder room-related rows, '
            f'{npc_deleted} NPC-related rows, {area_deleted} area rows deleted.'
        )

    # ------------------------------------------------------------------
    # Zone and Areas
    # ------------------------------------------------------------------

    def _seed_zone(self):
        zone, _ = Zone.objects.update_or_create(
            slug='the-convergence',
            defaults={
                'name': 'The Convergence',
                'genre_tone': 'All genres collide — the world\'s central hub',
                'danger_level': Zone.DANGER_SANCTUARY,
                'is_pvp_zone': False,
                'is_scaled': False,
                'description': (
                    'At the exact center of a Venn diagram of colliding universes sits The Convergence — '
                    'the one point where all the forces cancel out and stillness takes hold. Here, the chaos '
                    'of genre-collision resolves into an uneasy, permanent peace. No violence is sanctioned. '
                    'Even the air feels cautiously neutral. Infinity City has grown up around this stillness '
                    'over generations, accumulating like a city always does at a crossroads — organically, '
                    'inevitably, and without a plan.'
                ),
            },
        )
        self.stdout.write(f'Zone "{zone.name}" seeded.')
        return zone

    def _seed_areas(self, zone):
        wisteria_walk, _ = Area.objects.update_or_create(
            slug='wisteria-walk',
            defaults={
                'zone': zone,
                'name': 'Wisteria Walk',
                'area_description': (
                    'Broad stones of pale grey lead northward through the park, worn smooth by the passage '
                    'of countless feet across uncounted years. Low trellises line the path on either side, '
                    'their timber frames dark with age and almost invisible beneath cascading curtains of '
                    'wisteria. The blooms hang heavy, purple-white, stirred by the faintest movement of air. '
                    'The scent is persistent without being overwhelming — sweet, clean, faintly floral. Bees '
                    'move through the blossoms with quiet purpose. The stone underfoot is cool even in warm '
                    'weather, and the path feels deliberate, unhurried, as though it was laid by someone who '
                    'believed the walk itself was worth taking.'
                ),
            },
        )

        bamboo_run, _ = Area.objects.update_or_create(
            slug='bamboo-run',
            defaults={
                'zone': zone,
                'name': 'Bamboo Run',
                'area_description': (
                    'Crushed amber gravel crunches softly underfoot as the path turns east, the small stones '
                    'warm-toned and catching light in a way that makes the path glow faintly at certain hours. '
                    'On both sides, bamboo grows in dense stands — tall, straight, their green-gold canes '
                    'clicking quietly against one another when the air moves. The sound is dry and rhythmic, '
                    'almost musical. The path is narrow here, the bamboo close enough that the fronds brush '
                    'your shoulders if you drift from center. It is the shortest way out of the park, and '
                    'somehow feels like it knows this — brisk, direct, unceremonious.'
                ),
            },
        )

        basalt_way, _ = Area.objects.update_or_create(
            slug='basalt-way',
            defaults={
                'zone': zone,
                'name': 'Basalt Way',
                'area_description': (
                    'The path south is paved in wide slabs of dark basalt, nearly black, fitted together '
                    'without mortar across their entire surface. Between every seam, and in every crack where '
                    'time has loosened the stone, flowering moss has taken hold — vivid green starred with '
                    'tiny blooms of white and pale yellow. The contrast is stark and beautiful: dark stone, '
                    'bright life. The moss does not look accidental. It looks invited. The path is wide enough '
                    'to walk two abreast and winds gently as it goes, taking its time, finding its way south '
                    'through the older and larger trees at this end of the park.'
                ),
            },
        )

        fern_boards, _ = Area.objects.update_or_create(
            slug='fern-boards',
            defaults={
                'zone': zone,
                'name': 'Fern Boards',
                'area_description': (
                    'Planks of dark aged timber, worn smooth at their centers and raised slightly above the '
                    'earth on low supports, carry the path westward through the deepest green in the park. '
                    'Enormous ferns crowd both sides — waist-high, then shoulder-high, their broad fronds '
                    'reaching across the boardwalk\'s edges so that walking the path means moving through a '
                    'corridor of living green. The wood gives slightly underfoot, a soft flex with each step, '
                    'and the sound is muffled here in a way the other paths are not. It smells of damp earth '
                    'and old growth. The city feels further away than it is.'
                ),
            },
        )

        self.stdout.write('Areas seeded: Wisteria Walk, Bamboo Run, Basalt Way, Fern Boards.')
        return {
            'wisteria_walk': wisteria_walk,
            'bamboo_run': bamboo_run,
            'basalt_way': basalt_way,
            'fern_boards': fern_boards,
        }

    # ------------------------------------------------------------------
    # Rooms
    # ------------------------------------------------------------------

    def _room(self, zone, key, x, y, name, brief, description,
              area=None, indoors=False, no_exit=None):
        msgs = no_exit or {}
        room, _ = Room.objects.update_or_create(
            zone=zone,
            coord_x=x, coord_y=y, coord_z=0,
            defaults={
                'name': name,
                'brief_description': brief,
                'description': description,
                'area': area,
                'flag_safe': True,
                'flag_indoors': indoors,
                'no_exit_north_msg': msgs.get('north', ''),
                'no_exit_south_msg': msgs.get('south', ''),
                'no_exit_east_msg': msgs.get('east', ''),
                'no_exit_west_msg': msgs.get('west', ''),
                'no_exit_up_msg': msgs.get('up', ''),
                'no_exit_down_msg': msgs.get('down', ''),
            },
        )
        self.rooms[key] = room
        return room

    def _seed_rooms(self, zone, areas):
        ww = areas['wisteria_walk']
        br = areas['bamboo_run']
        bw = areas['basalt_way']
        fb = areas['fern_boards']

        # --- Heart of the Convergence ---------------------------------------
        self._room(
            zone, 'heart', 0, 0,
            'Heart of the Convergence',
            'The heart of Infinity City, where all paths meet.',
            'At the center of everything stands the Obelisk.'
            '\n\n'
            'It rises from the earth without ceremony — no plinth, no inscription, no fence to keep '
            'you back. The stone is dark and smooth, each of its countless facets ground to a perfect '
            'plane, each one catching light at a slightly different angle so that the whole surface '
            'seems to breathe. You could count the facets. You won\'t. Some things resist counting.'
            '\n\n'
            'At the obelisk\'s heart, suspended at eye level inside the stone as though the stone grew '
            'around it, is a sphere no larger than a closed fist. It glows white. Not brilliantly — '
            'not the white of a searchlight or a spell discharged at close range — but steadily, the '
            'way a candle glows in a room that is otherwise completely still. It does not flicker. It '
            'does not pulse. It simply is.'
            '\n\n'
            'Around you, Convergence Park spreads outward in four directions, tended and unhurried. '
            'Paths of different materials wind away through trees and grass toward the streets beyond, '
            'where the sounds of Infinity City begin — voices, movement, the distant hum of things you '
            'haven\'t named yet.'
            '\n\n'
            'You have arrived. Where you go from here is entirely up to you.',
            no_exit={
                'up': 'There is nothing above you.',
                'down': 'You\'d have to dig to go that way.',
            },
        )

        # --- Wisteria Walk (north path) --------------------------------------
        self._room(
            zone, 'ww1', 0, 1,
            'First Steps on the Wisteria Walk',
            'The pale stone path begins here, leading north under cascading wisteria.',
            'The pale stones begin here, broad and worn, leading away from the obelisk into the quiet '
            'of the park. A trellis arch frames the entrance to the path, its timber dark with age, '
            'wisteria already heavy overhead — purple blooms cascading down on either side close enough '
            'to brush your arms. The scent of them follows you. Behind you, the obelisk still catches '
            'your eye. Ahead, the path bends gently west and continues into the green. You step '
            'forward, not yet knowing how far it might take you.',
            area=ww,
            no_exit={'east': KEEP_OFF_GRASS, 'west': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'ww2', -1, 2,
            'Along the Wisteria Walk',
            'The pale path curves west under a heavy canopy of wisteria blooms.',
            'The path has found its westward lean here, the pale stones curving unhurriedly through a '
            'longer stretch of trellis-work hung so thick with wisteria that the sky above is more '
            'purple than blue. Bees move through the blossoms with quiet authority, paying you no '
            'attention. The fountain is behind you now, the obelisk out of sight. The sounds of the '
            'street ahead are still faint, but present — a murmur at the edge of hearing. You feel '
            'the path drawing toward its end.',
            area=ww,
            no_exit={'north': KEEP_OFF_GRASS, 'west': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'ww3', -1, 3,
            'Deeper on the Wisteria Walk',
            'Wisteria thickens overhead as the pale path continues north.',
            'The wisteria is at its most dense here, the trellises so closely spaced that they form a '
            'near-continuous canopy of purple and grey-green. The scent is strongest in this stretch. '
            'Below your feet the pale stones are their most worn — this section of the path sees the '
            'most foot traffic, being neither too close to the obelisk nor too close to the street. '
            'Through gaps in the trellis you can glimpse the older trees of the park on either side. '
            'Something about the light here is especially still.',
            area=ww,
            no_exit={'east': KEEP_OFF_GRASS, 'west': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'ww4', -1, 4,
            'Northern Edge of the Wisteria Walk',
            'The wisteria thins as the pale path approaches the northern street.',
            'The wisteria thins here, the trellises giving way to open sky, and the pale stones broaden '
            'as they approach the street ahead. Through the last of the park trees — tall, old, their '
            'roots lifting the stone at the path\'s edges — you can see movement: people, storefronts, '
            'the ordinary business of Infinity City going about its day. The path ends just ahead. '
            'Whatever comes next is already waiting.',
            area=ww,
            no_exit={'east': KEEP_OFF_GRASS, 'west': KEEP_OFF_GRASS},
        )

        # --- Bamboo Run (east path) ------------------------------------------
        self._room(
            zone, 'br1', 1, 0,
            'Onto the Bamboo Run',
            'Amber gravel crunches underfoot as the path leads east into tall bamboo.',
            'The gravel begins here — crushed amber stone, warm-toned, crunching softly with each step '
            'as the path leads east away from the obelisk. On either side, the first bamboo canes rise '
            'close and straight, their green-gold surfaces catching the light. The fronds are already '
            'brushing the edges of the path. Ahead the corridor of bamboo thickens, and the park opens '
            'into something quieter and more enclosed. You step in, not yet knowing where it ends.',
            area=br,
            no_exit={'north': KEEP_OFF_GRASS, 'south': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'br2', 2, 0,
            'Along the Bamboo Run',
            'Bamboo crowds close on both sides of the amber gravel path.',
            'The bamboo stands tall and dense on both sides now, the canes clicking softly in the '
            'faintest air movement, fronds brushing your shoulders as you walk. The amber gravel '
            'glows warmly underfoot. Somewhere behind you the obelisk; somewhere ahead the street. '
            'The city sounds are audible here, filtering through the bamboo in fragments. You feel '
            'you are close to the path\'s end.',
            area=br,
            no_exit={'north': KEEP_OFF_GRASS, 'south': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'br3', 3, 0,
            'End of the Bamboo Run',
            'The bamboo parts ahead as the gravel path reaches the eastern street.',
            'The bamboo stands tall and dense on both sides, canes clicking softly against one another '
            'in the faint movement of air, and then ahead the path simply ends — the gravel broadening '
            'as it meets the street. You can see it clearly now: the city, people moving, the line of '
            'trees that borders the park on this side standing patient and tall between the park and the '
            'storefronts beyond. The end of the path is right there. You wonder what\'s waiting on the '
            'other side.',
            area=br,
            no_exit={'north': KEEP_OFF_GRASS, 'south': KEEP_OFF_GRASS},
        )

        # --- Basalt Way (south path) -----------------------------------------
        self._room(
            zone, 'bw1', 0, -1,
            'Onto the Basalt Way',
            'Dark basalt slabs begin here, threaded with flowering moss, heading south.',
            'The first dark slabs of basalt begin here, wide and nearly black, fitted flush with one '
            'another so the path feels continuous underfoot. Between the seams, flowering moss catches '
            'the light — vivid green, impossibly small white and yellow blooms. The contrast stops you '
            'for a moment. It is one of those things that shouldn\'t be as beautiful as it is. The path '
            'leads south from the obelisk, already curving gently eastward. You step down it not knowing '
            'how long the winding might take.',
            area=bw,
            no_exit={'east': KEEP_OFF_GRASS, 'west': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'bw2', 1, -1,
            'Along the Basalt Way',
            'The basalt path bends east through older, larger park trees.',
            'The basalt path has bent east here, following some old logic of the park\'s original design '
            '— the moss filling every seam faithfully regardless of direction, as if it made no '
            'distinction. The trees on this side of the park are older and larger, their roots lifting '
            'the edges of the stone in places, the park itself slowly reclaiming the path at its '
            'margins. It has the feeling of something tended but not controlled. You sense the path '
            'beginning to find its way back south.',
            area=bw,
            no_exit={'north': KEEP_OFF_GRASS, 'east': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'bw3', 1, -2,
            'Deeper on the Basalt Way',
            'The dark basalt straightens south, the flowering moss vivid between the slabs.',
            'The path has straightened now, heading south once more, the dark stone broader here and the '
            'moss between the slabs at its most vivid — a long stretch with no interruption, the '
            'flowering green threading through the black in a continuous line toward the street ahead. '
            'The trees thin at the park\'s southern edge and through them you can make out movement, hear '
            'voices. The end feels close. You feel yourself drawn forward.',
            area=bw,
            no_exit={'east': KEEP_OFF_GRASS, 'west': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'bw4', 1, -3,
            'Near the Southern Edge of the Basalt Way',
            'Great trees line the final stretch of dark basalt path.',
            'The great trees of the park\'s southern edge rise close on either side here, their roots '
            'threading beneath the basalt slabs in long dark lines. The moss between the stones is '
            'bright even in the shade beneath the canopy. The street is almost visible now — a strip '
            'of movement and sound framed between the trunks. You have walked almost the full length '
            'of the Basalt Way.',
            area=bw,
            no_exit={'east': KEEP_OFF_GRASS, 'west': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'bw5', 1, -4,
            'Southern Edge of the Basalt Way',
            'The basalt path ends here where the park meets the southern street.',
            'The basalt slabs end here in a clean line where the park meets the southern street, the '
            'last of the great trees standing on either side like a gate that chose not to close. Beyond '
            'them the street opens up — wide, busy, lined with storefronts and vendors whose signs and '
            'sounds carry easily across the distance. The moss runs right to the edge of the last stone, '
            'bright as ever, unbothered by the city at its doorstep. The path is behind you now. What '
            'comes next is straight ahead.',
            area=bw,
            no_exit={'east': KEEP_OFF_GRASS, 'west': KEEP_OFF_GRASS},
        )

        # --- Fern Boards (west path) -----------------------------------------
        self._room(
            zone, 'fb1', -1, 0,
            'Onto the Fern Boards',
            'A dark timber boardwalk leads west into towering ferns.',
            'The boardwalk begins here — dark aged timber, planks worn smooth at their centers, raised '
            'just slightly off the earth on low supports. The wood gives faintly underfoot, a small flex '
            'with each step, and the sound of it is different from stone: softer, more intimate. The '
            'ferns start immediately, waist-high on either side, their broad fronds already reaching '
            'toward the path\'s edges. The air smells of damp earth and old growth. You step forward '
            'into the green, not yet knowing how far west this will take you.',
            area=fb,
            no_exit={'north': KEEP_OFF_GRASS, 'south': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'fb2', -2, 1,
            'Along the Fern Boards',
            'The boardwalk drifts north through the densest ferns in the park.',
            'The boardwalk has drifted north here, following a gentle bend through the densest stretch '
            'of ferns in the park — shoulder-high now, fronds crossing overhead in places to form a '
            'broken canopy of green. The city is muffled here in a way that feels deliberate, as though '
            'the park decided this corner should stay quiet. The timber is darker with age and moisture, '
            'the grain deep and pronounced. You feel closer to the end of the path, the sound of the '
            'street beginning to find its way through the green.',
            area=fb,
            no_exit={'north': KEEP_OFF_GRASS, 'west': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'fb3', -3, 1,
            'Deeper on the Fern Boards',
            'Old timber runs through ferns that crowd the boardwalk on all sides.',
            'The ferns reach their tallest here, their fronds meeting overhead in a loose canopy that '
            'filters the light to something softer and greener than the open park. The boardwalk planks '
            'are at their darkest with age and the moisture the ferns bring. One plank has been replaced '
            'recently — lighter in color, still showing the tool marks of its fitting, flush and solid '
            'underfoot. Someone tends this path. The city sounds are returning, growing clearer to the '
            'west.',
            area=fb,
            no_exit={'north': KEEP_OFF_GRASS, 'south': KEEP_OFF_GRASS},
        )
        self._room(
            zone, 'fb4', -4, 1,
            'End of the Fern Boards',
            'The boardwalk broadens as the ferns thin toward the western street.',
            'The ferns thin as the boardwalk straightens and widens toward the western street, the planks '
            'here lighter in color where more light reaches them. The last of the great trees stands just '
            'off the path\'s edge, its roots running beneath the boards, the timber built around them '
            'rather than through them. Through the remaining green you can see the street ahead clearly '
            'now — the motion of people, the shapes of buildings, the line of trees the city planted when '
            'it grew up against the park\'s edge. The boards end just ahead. Whatever comes next is '
            'already in sight.',
            area=fb,
            no_exit={'north': KEEP_OFF_GRASS, 'south': KEEP_OFF_GRASS},
        )

        # --- Ring street (35 rooms, clockwise from the north gate) ------------
        # NOTE: the brief assigned R16 to (1, -4, 0), which collides with BW-5.
        # R16 sits at (1, -5, 0) instead, keeping it adjacent to the Iron Gate.
        self._room(
            zone, 'r01', 0, 5,
            'Northern Ring — Wisteria Gate',
            'The Wisteria Walk meets the ring street here. An old tree bears a carved sign.',
            'The ring street curves away in both directions here, broad and unhurried, lined on the park '
            'side with old trees whose roots have lifted the paving stones into gentle waves over the '
            'years. No one thought to fix it. No one ever will. The pale stones of the Wisteria Walk '
            'emerge from the park just here, the last trellis arch still heavy with purple blooms at your '
            'back. At the base of the largest tree on the park\'s edge, a hollow has been worn or made — '
            'large enough for a man, a chair, and decades of opinions. The word INFORMATION is carved '
            'above the opening in letters so old the bark has begun to grow back around them. The man '
            'inside is already watching you.',
        )
        self._room(
            zone, 'r02', 1, 5,
            'The Green Gate',
            'Two great trees lean together here, their branches interlocked above a dirt path.',
            'The ring street widens slightly here, as if the city stepped back to make room for what '
            'stands at this point on the road. Between two ancient trees whose trunks lean inward toward '
            'each other, their upper branches long since interlocked overhead, a path of dark earth '
            'begins. Not paved. Not constructed. Just worn into existence by whatever passed this way '
            'before the city grew up around it. Beyond the arch, a short path runs into green shade, '
            'and the air that drifts out of it smells of ferns and rain. A wooden '
            'sign has been nailed to the left tree at eye level. It reads: THE VERDANT REACH. Below '
            'that, in different handwriting, older: Mind the roots.',
        )
        self._room(
            zone, 'r03', 2, 5,
            'Eastern Ring — First Stretch',
            'A quiet stretch of ring street lined with closed storefronts and old trees.',
            'The ring street continues its curve here, trees lining the park side in an unbroken row, '
            'their canopy meeting overhead to dapple the paving with moving light. On the outer edge, a '
            'row of storefronts sits quiet — their shutters closed, their signs faded to illegibility, '
            'their facades wearing the particular dignity of places that were once busy and are patiently '
            'waiting to be busy again. One doorway still has a bundle of dried flowers hanging above it, '
            'brown with age. The street is clean. Someone sweeps it.',
        )
        self._room(
            zone, 'r04', 3, 5,
            'Eastern Ring — The Cold Corner',
            'The air is cooler here. An unlit lamppost stands at the corner.',
            'The air is different here. Not unpleasant — just cooler than it should be for the time of '
            'day, and still in a way that the rest of the ring street is not. The trees on the park side '
            'are the same as everywhere else, old and patient, but the ones on the outer edge of the '
            'street here are darker — their bark almost black with moisture, their lower branches '
            'trailing something pale and fibrous that might be lichen or might be something else. An old '
            'lamppost stands at the corner, unlit. Its glass is intact. There are no scorch marks in its '
            'bowl, as though it was installed and never needed. A faint smell of old stone and cold '
            'candle wax drifts from somewhere ahead.',
        )
        self._room(
            zone, 'r05', 4, 5,
            'Eastern Ring — Whisper Row',
            'A long stone wall with a sealed iron door runs the outer edge of the street.',
            'The outer edge of the street here is a continuous wall — old stone, fitted tight, no '
            'windows, no doors, no explanation. It runs the length of the room and ends as abruptly as '
            'it began. Someone has pressed flowers into the mortar at intervals, dried flat, petals long '
            'since colorless. At the wall\'s midpoint, set flush with the surface, is a small iron door '
            'with no handle. Above it, carved directly into the stone: a shape that might be an arch, '
            'might be a gateway, might be a stylized flame. The inscription below it is in a language '
            'you don\'t recognize. The door does not move when you push it. It is very cold to the touch.',
        )
        self._room(
            zone, 'r33', 4, 4,
            'Eastern Ring — Corner Approach',
            'The ring street turns here, the park trees thinning at the corner.',
            'The ring street bends at this corner, the park trees thinning briefly before resuming on '
            'the other side of the turn. The paving here is a little wider than elsewhere, as though '
            'the original builders anticipated foot traffic pooling at corners. On the outer edge, a '
            'building presents a plain facade — no windows on this side, just old stone and a downpipe '
            'stained with decades of weather. The air carries the faint smell of old stone from the '
            'north and something that hasn\'t quite resolved itself yet from the east.',
        )
        self._room(
            zone, 'r06', 5, 4,
            'The Stone Gate',
            'Two carved stone columns frame iron doors that stand permanently open.',
            'The ring street arrives at something that was not built so much as revealed. Two columns of '
            'dark stone rise from the paving on the outer edge of the street, taller than the surrounding '
            'buildings, their surfaces carved in dense interlocking patterns that reward study without '
            'resolving into anything nameable. Between them, a set of iron doors stand open — or rather, '
            'stand at rest in the open position, as though they have not been closed in a very long time '
            'and have forgotten how. Beyond them, a cobbled path descends slightly into a space where the '
            'light is amber and sourceless and the air smells of incense and age. Somewhere beyond the '
            'threshold, very faintly, something that might be an organ chord fades into silence. A sign '
            'affixed to the left column reads: ASHENVEIL CATHEDRAL. Below it, in smaller text: Visitors '
            'welcome. Mind the congregation.',
            no_exit={
                'east': 'Ashenveil Cathedral is sealed. The iron doors stand open but something on the other side is not yet ready for visitors.',
            },
        )
        self._room(
            zone, 'r07', 5, 3,
            'Southern Ring — Past the Stone Gate',
            'The ring continues south past the stone columns, stalls under construction ahead.',
            'The ring street continues here past the weight of the stone columns behind you, the air '
            'gradually warming back to normal as you move. On the outer edge, a row of stalls under '
            'construction line the street — timber frames up, canvas stretched over some of them, tools '
            'left out as though the builders stepped away an hour ago and will be back shortly. One stall '
            'has its counter installed already, a beautiful piece of dark hardwood polished to a shine, '
            'with nothing yet to sell from it. The park trees on the inner edge continue their patient '
            'row, unmoved by commerce.',
        )
        self._room(
            zone, 'r08', 5, 2,
            'Southern Ring — The Wet Stones',
            'The paving stays damp here. A blue sign above a locked door catches the light.',
            'The paving here is damp despite no recent rain — a persistent seep from somewhere beneath '
            'the street keeps the stones dark and slightly slick underfoot. On the outer edge, the '
            'buildings have a different character: older facades overlaid with newer work, stone '
            'underneath metal trim underneath what might be an early attempt at signage using materials '
            'that have no business being this far into the Convergence. One sign is made from something '
            'that catches light strangely — not glass, not metal, a deep vivid blue that shifts toward '
            'violet depending on the angle. It has no text. It is simply a color, hung above a door, as '
            'advertisement. The door is locked.',
        )
        self._room(
            zone, 'r09', 5, 1,
            'Southern Ring — Flicker Alley',
            'A mosaic wall catches the light. A faintly glowing tube reads: Coming Soon.',
            'The outer edge of the street here is dominated by a long low building whose facade has been '
            'covered, at some point in its history, in small pieces of colored glass — tesserae pressed '
            'into mortar in no particular pattern, purely for the pleasure of it. At certain angles the '
            'whole wall catches light and throws it back in fractured color across the street. Between '
            'two of the glass panels, someone has installed a length of tubing that glows faintly '
            'blue-white even in daylight, its light steady and cold and unlike anything else on the ring. '
            'Below it, a small hand-lettered card reads: Coming Soon. The card is yellowed. The tubing '
            'still glows.',
        )
        self._room(
            zone, 'r10', 5, 0,
            'Eastern Ring — Bamboo Crossing',
            'The Bamboo Run meets the ring here. Two metal docking tubes stand across the street.',
            'The amber gravel of the Bamboo Run spills out of the park here, a few stones always '
            'escaping onto the ring street paving no matter how often they are swept back. The bamboo '
            'stands tall on either side of the path\'s mouth, its canes clicking softly in the moving '
            'air. On the outer edge of the ring street, directly across from where the park path ends, '
            'two large cylindrical tubes of brushed metal stand side by side, their surfaces worn to a '
            'deep patina. The first is labeled CIVIC INFORMATION UNIT; the second, CIVIC REPAIR UNIT — '
            'VERSION 2. Both sets of doors are open. Two units stand just outside them, facing outward. '
            'Green buttons are visible on both panels. Both have been recently polished.',
        )
        self._room(
            zone, 'r11', 5, -1,
            'Southern Ring — Dry Block',
            'The air dries out here. Scorch marks above one door have never fully faded.',
            'The street changes character here — the air drier, the light harsher somehow despite the '
            'same sky overhead. The trees on the park side continue, but the ones on the outer edge have '
            'been removed at some point, their stumps ground down and the gaps left open. The buildings '
            'behind those gaps are older, their facades cracked in the particular way of stone exposed to '
            'repeated heat cycles. One building has a scorch mark above its door that no amount of '
            'weathering has fully erased. A barrel outside another storefront is filled with sand. '
            'Everything here feels like somewhere that knows what dry heat is and has made its '
            'accommodations.',
        )
        self._room(
            zone, 'r12', 5, -2,
            'Southern Ring — Ash Corner',
            'A vacant lot with a carefully maintained firepit sits at the outer edge.',
            'The outer edge of the ring here is a vacant lot — cleared, level, nothing growing. Not for '
            'lack of trying: the soil visible at the edges is grey-white, exhausted, and something about '
            'it resists the park\'s generosity. The trees that line the street stop one room short and '
            'start again one room later, leaving this gap conspicuous. In the center of the lot, someone '
            'has placed a ring of stones in the old way — a firepit, unlit, swept clean. Around it, four '
            'flat stones for sitting. The whole arrangement is carefully maintained. Someone uses this '
            'place and keeps it ready. The air smells of ash that hasn\'t been there in years and somehow '
            'still is.',
        )
        self._room(
            zone, 'r34', 5, -3,
            'Southern Ring — The Bridge Stretch',
            'The ring street passes over a narrow channel here on a low stone bridge.',
            'The paving here transitions briefly to a low stone bridge, the road passing over a narrow '
            'channel whose water is dark and moves slowly. The balustrade on the outer side is old '
            'ironwork, its surface pitted and repainted several times over in different colors — layers '
            'visible at every chip. Below, the channel smells of stone and still water. On the far bank '
            'the storefronts resume. The park trees on the inner edge line up to the bridge\'s edge and '
            'pick up again immediately on the other side, unbroken as ever.',
        )
        self._room(
            zone, 'r13', 4, -4,
            'The Ashgate',
            'A cracked concrete arch opens onto a flat grey expanse. A sign warns: there is no road.',
            'The outer edge of the ring street opens here onto a wide arch of weathered concrete, cracked '
            'and patched and cracked again — not a ruin exactly, but a structure that has survived things. '
            'Beyond the arch, a flat expanse stretches away, the ground pale grey and hardpacked, the air '
            'immediately drier and tasting of mineral dust. The sky on the other side of the arch is the '
            'same sky, but it seems bigger out there — wider, less managed. A rusted metal sign has been '
            'bolted to the arch with heavy fasteners, as though previous signs were removed by wind or '
            'worse. It reads: THE BLASTED FLATS. In smaller text below: Stay on the road. There is no road.',
            no_exit={
                'south': 'The Blasted Flats gate is sealed. The arch stands open but the expanse beyond is not yet reachable — the air from it is very dry.',
            },
        )
        self._room(
            zone, 'r14', 3, -4,
            'Western Ring — Past the Ashgate',
            'The ring resumes past the concrete arch. Workshop shutters stand open, tools laid out.',
            'The ring street curves back into its familiar pattern here, the park trees resuming on the '
            'inner edge as if the Ashgate were a thing they preferred not to acknowledge. On the outer '
            'edge, a series of workshops sit shoulder to shoulder — their facades different heights, '
            'different ages, different materials, as though each was built independently by someone who '
            'hadn\'t consulted the neighbors. One has a sign: CLOSED FOR RENOVATION — EST. REOPENING: '
            'followed by a date left blank. The workshop beside it has its shutters open, the interior '
            'visible: workbenches, tools racked neatly, everything ready, no one home. From somewhere '
            'below the street, barely audible, a low rhythmic vibration. Not unpleasant. Just present.',
        )
        self._room(
            zone, 'r15', 2, -4,
            'Western Ring — Gear Corner',
            'A relief carving of gears and pipes decorates a building facade. Warm air rises from a grate below.',
            'The paving here has been repaired at some point with a different type of stone — darker, '
            'harder, fitted with mechanical precision into the gaps where the original stones failed. '
            'The seams are exact. The work is extraordinary and completely anonymous. On the outer edge, '
            'a building facade has been decorated with a large relief carving — gears, pipes, and '
            'pressure valves rendered in loving detail, clearly the work of someone who understood these '
            'things. The carving has no label. Below the building\'s door, just visible at street level, '
            'a brass grate covers a ventilation shaft from which warm air rises steadily, smelling '
            'faintly of oil and hot metal.',
        )
        self._room(
            zone, 'r16', 1, -5,
            'Western Ring — The Deep Hum',
            'A deep vibration pulses from below. An iron access hatch is scratched with the letters I.D.',
            'The vibration is stronger here. You feel it in your feet before you hear it — a deep '
            'rhythmic pulse from somewhere far below, steady as a heartbeat, mechanical rather than '
            'natural. The outer edge buildings here are built on foundations that go down further than '
            'they should — their basements having basements, if the iron-ringed access hatches set into '
            'the pavement are any indication. One hatch is newer than the others, its ring polished from '
            'regular use. It is locked with a mechanism you don\'t immediately recognize. Beside it, '
            'scratched into the stone: an arrow pointing down, and below that, three letters: I.D.',
        )
        self._room(
            zone, 'r17', 0, -5,
            'The Iron Gate',
            'A freight elevator platform descends into warm orange light. A note reads: maintenance.',
            'The outer edge of the ring opens here onto a broad freight elevator platform — iron lattice '
            'floor, heavy counterweights, a control panel of switches and levers worn smooth by use. The '
            'elevator itself is large enough for a dozen people and whatever they might be carrying. Below '
            'the platform, a shaft descends into warm orange light and the smell of hot metal and deep '
            'earth. The mechanism is clearly functional — the counterweights are balanced, the cables taut '
            'and oiled. A brass plate on the control panel reads: IRON DEEPS — CIVIC ACCESS LIFT. Below '
            'it, a hand-written note attached with a bolt: Currently under scheduled maintenance. Access '
            'resuming soon.',
            no_exit={
                'down': 'The Iron Deeps lift is undergoing maintenance. The mechanism looks functional but something is preventing descent.',
            },
        )
        self._room(
            zone, 'r18', -1, -5,
            'Southern Ring — Basalt Crossing',
            'The Basalt Way meets the ring here. A brightly colored gazebo sits across the street.',
            'The dark basalt slabs of the Basalt Way emerge from the park here, the moss between them '
            'bright even where it meets the ring street paving. The path\'s mouth is framed by two of the '
            'park\'s oldest trees, their roots threading under both the basalt and the ring street stone '
            'without apology. On the outer edge of the street, directly across from the park path, a '
            'gazebo stands in colors that have no business being next to each other and are somehow '
            'getting along fine — deep teal posts, amber railings, a roof in gold and crimson and a '
            'particular shade of green that has no name. Flowering vines have climbed all four posts '
            'uninvited and stayed. Inside, an old woman on a painted stool is already smiling at you.',
        )
        self._room(
            zone, 'r19', -2, -5,
            'Western Ring — Past the Iron Gate',
            'The ring continues west. A tree has grown around a lamppost and both still work.',
            'The ring street resumes its quiet character here, the mechanical energy of the lift platform '
            'fading behind you. On the outer edge, a long undeveloped stretch — cleared ground, a few '
            'foundation stones laid and then abandoned, a stack of building materials under weathered '
            'canvas. The park trees on the inner edge grow particularly large here, as though the open '
            'space on the other side of the street has given their roots room to spread. One tree has '
            'grown so close to a lamppost that the trunk has incorporated the post\'s base, the metal now '
            'part of the wood. The lamppost still works. The tree does not seem to mind.',
        )
        self._room(
            zone, 'r20', -3, -5,
            'Western Ring — The Still Street',
            'Something about this stretch is quieter than it should be. The shadows fall wrong.',
            'Something about this stretch of the ring is quieter than it should be. The ambient sounds '
            'of Infinity City — voices, distant commerce, the creak of signage in the wind — are present '
            'but muffled, as though heard through water. The buildings on the outer edge are unremarkable '
            'in every particular: ordinary facades, ordinary shuttered windows, ordinary doors. And yet. '
            'The shadows they cast fall at a slightly wrong angle for the time of day. The lamppost on '
            'this block has a crack in its glass that has collected something dark — not dirt, not rust. '
            'The air has no smell at all, which in a city is more disturbing than any smell would be.',
        )
        self._room(
            zone, 'r35', -4, -4,
            'Western Ring — Southwest Corner',
            'The ring bends at this corner. The stillness from the east lingers faintly.',
            'The ring street bends here at the southwest corner of the park, the paving slightly wider '
            'to accommodate the turn. The park trees resume their line after a brief gap where the corner '
            'building\'s foundation pushed them back. On the outer edge, a plain shopfront presents '
            'closed shutters and an awning that has been carefully rolled and tied. The stillness from '
            'the eastern stretch lingers here — not quite as strong, but present. The air is a degree '
            'cooler than it was a few steps back. It normalizes again to the west.',
        )
        self._room(
            zone, 'r21', -5, -3,
            'Western Ring — Where the Light Goes Wrong',
            'The light here has no warmth. Colors feel translated. A warm bench sits empty.',
            'The light fails here in a way that has nothing to do with clouds or time of day. Not '
            'darkness — the street is perfectly visible. But the light has no warmth. Shadows are too '
            'sharp. Colors are accurate but feel somehow translated, as though you are seeing them through '
            'a description of colors rather than the colors themselves. The trees on the park side are the '
            'same trees they have always been, but standing in this room looking at them, you feel that '
            'they are very far away. An old woman was sitting on a bench on the outer edge when you '
            'arrived. She is no longer there. The bench is warm.',
        )
        self._room(
            zone, 'r22', -5, -2,
            'Western Ring — The Crystal Approach',
            'Something ahead catches light in shifting colors. The air is cooling as you walk.',
            'The air cools slightly as you continue along the ring, the wrongness of the previous stretch '
            'fading behind you. On the inner edge, the park trees are particularly old here — their trunks '
            'wide enough that two people could not link hands around them, their bark deeply grooved and '
            'covered in a fine pale-green moss quite different from the flowering kind on the Basalt Way. '
            'On the outer edge, the storefronts are quiet and maintained. Ahead, something is catching '
            'the light in shifting colors — violet, pale blue, something between green and gold. It is '
            'not a sign. It is not glass. It is getting closer.',
        )
        self._room(
            zone, 'r23', -5, -1,
            'Western Ring — Crystal Street',
            'The crystal structures are visible on both sides of the street now.',
            'The shifting light is all around you now, emanating from two structures — one on the inner '
            'edge of the ring at the park\'s boundary, one on the outer edge directly across the street. '
            'Both are formed from interlocking columns of crystal in colors that move as you move. The '
            'light they distribute travels slowly across the paving, the park trees, the fern fronds that '
            'reach out from the Fern Boards\' mouth just ahead. The air here has a texture to it, a '
            'quality of attentiveness. Both structures are aware of you. Both are content to wait.',
        )
        self._room(
            zone, 'r24', -5, 0,
            'Western Ring — Fern Crossing',
            'The Fern Boards meet the ring here. Crystal structures stand on both sides of the street.',
            'The dark timber of the Fern Boards emerges from the park here, the boardwalk ending at the '
            'ring street in a clean line where wood meets stone. The ferns crowd close on either side of '
            'the path\'s mouth, their fronds reaching out over the ring street itself as though curious '
            'about the city. On the inner edge of the ring, directly alongside the path\'s mouth, a '
            'structure of interlocking crystal columns rises — violet, pale blue, something between green '
            'and gold that shifts as you move. Directly across the street, its exact twin. The inner '
            'crystal holds a presence that is aware and unhurried. The outer crystal holds the same '
            'presence, differently purposed.',
        )
        self._room(
            zone, 'r25', -5, 1,
            'The Pale Gate',
            'A shore begins here without explanation. The sound of the water does not match its movement.',
            'The outer edge of the ring opens here onto something that resists description at the edges. '
            'There is a threshold — that much is certain. On this side: the ring street, the park trees, '
            'Infinity City going about its business. On the other side: a shore. Not a metaphorical '
            'shore. Actual pale sand, actual grey water, actual horizon. The scale is wrong in a way you '
            'cannot identify — the water seems both close and impossibly distant. The sound of it does '
            'not match its movement. The gate itself is nothing: no arch, no door, no structure. Just '
            'the point where one place ends and another begins, as if reality simply changed its mind. '
            'A sign on a post driven into the ring street paving reads: THE PALE SHORE. Below it: Do not '
            'look at the water for more than thirty seconds. This is not a warning. It is advice.',
            no_exit={
                'west': 'The Pale Shore gate is sealed. The threshold is there but something on the other side is not yet permitting passage — the sound of water carries through anyway.',
            },
        )
        self._room(
            zone, 'r26', -5, 2,
            'Northern Ring — Scorched Stretch',
            'Bleached paving and a missing building floor. The sky feels too large overhead.',
            'The character of the street changes here, past the Pale Gate. The buildings on the outer '
            'edge are lower, more exposed, their rooflines uneven. One building is missing its top floor '
            'entirely — not collapsed, removed, the cut too clean to be accident or weather. The paving '
            'is intact but the color has bleached out of it in irregular patches, as though subjected to '
            'intense heat at some point and recovered imperfectly. The trees on the park side thin here '
            'and one gap has never been filled — a stump, ground level, surrounded by the same bleached '
            'stone. The sky feels large overhead in a way it doesn\'t elsewhere on the ring. A wind comes '
            'from the direction of the gate behind you carrying nothing — no smell, no temperature. Just '
            'movement.',
        )
        self._room(
            zone, 'r27', -5, 3,
            'Northern Ring — The Open Block',
            'A vacant lot with an empty billboard and a single chair facing a horizon that should not be visible.',
            'The outer edge of the ring here is entirely open — no buildings, no stalls, no construction. '
            'Just a long flat expanse of pale packed earth behind a low stone curb. At the far end of the '
            'expanse, a billboard structure has been erected: two posts, a crossbeam, and a large panel '
            'of weathered board. Nothing has been painted on it yet. Or something was painted on it and '
            'has fully faded. It is impossible to know which. In the center of the open expanse, a single '
            'chair. Occupied by no one. Facing outward, away from the park, toward the horizon that '
            'should not be visible from inside a city but somehow, from this particular spot, is.',
        )
        self._room(
            zone, 'r28', -5, 4,
            'The Waste Gate',
            'A gap in the city opens onto flat, pale scrubland. A cairn reads: It scales. Good luck.',
            'The ring street ends its penultimate stretch here at the widest opening on the outer edge — '
            'not a gate in any constructed sense but a gap in the city so large and so permanent that the '
            'city has accepted it as a feature rather than a failure. Beyond it, the ground extends flat '
            'and pale in every direction, the scrub vegetation low and grey-green, the sky enormous and '
            'cloudless and somehow indifferent. The wind through the gap is constant and dry and carries '
            'fine grit that has settled into every crack in the ring street paving for meters in either '
            'direction. A cairn of stacked stones stands at the gap\'s right edge — not official, not '
            'labeled, built by hand over time, each stone placed by someone who passed through and felt '
            'the need to mark it. On the top stone, scratched with something sharp: It scales. Good luck.',
            no_exit={
                'west': 'The Wastelands gate is sealed. The gap in the city is real but passage is not yet possible — the grit-laden wind comes through regardless.',
            },
        )
        self._room(
            zone, 'r29', -4, 4,
            'Northern Ring — The Return',
            'The city reasserts itself. An old vendor cart waits with a note: Back in an hour.',
            'The ring street curves back toward the north here, the open exposure of the Waste Gate '
            'falling behind you, the city reasserting itself in the familiar way — buildings closing back '
            'in on the outer edge, the park trees resuming their patient row on the inner side. The '
            'paving is cleaner here, the stones better maintained, as though the city is making an effort '
            'at the seam between its wilder edges and its settled center. An old vendor cart sits against '
            'the outer building, empty, its wheels chocked with stones. A handwritten note is tucked '
            'under the brake handle. It reads: Back in an hour. The note is not recent.',
        )
        self._room(
            zone, 'r30', -3, 4,
            'Northern Ring — Quiet Block',
            'A settled stretch of ring street. Old businesses, maintained facades, the hum of normalcy.',
            'The ring street is comfortable here, settled into itself. The buildings on the outer edge '
            'have been here long enough to stop trying to announce themselves — their facades clean, '
            'their signs legible, their hours posted and kept. A tailor\'s window shows work in progress '
            'through the glass: half-assembled garments on forms, spools of thread in a dozen colors '
            'arranged by hue on a shelf. The proprietor is not visible. The work is beautiful. On the '
            'park side, the trees are old friends by now, their roots having given up fighting the '
            'paving and found their way beneath it instead.',
        )
        self._room(
            zone, 'r31', -2, 4,
            'Northern Ring — Almost Home',
            'The ring curves back toward the north. The north path intersection is just ahead.',
            'The ring street is nearly complete here, the north path intersection visible ahead where the '
            'pale stones of the Wisteria Walk catch the light. The buildings on the outer edge are the '
            'most established on the ring — older, more settled, their facades maintained with the pride '
            'of businesses that have been here long enough to stop worrying about it. A small cafe '
            'occupies the corner unit, its shutters open, a smell of something warm and unfamiliar '
            'drifting into the street. The proprietor — visible through the window, elderly, unhurried — '
            'looks up as you pass and nods with the acknowledgment of someone who has seen every kind of '
            'person come through and found them all more or less acceptable.',
        )
        self._room(
            zone, 'r32', -1, 5,
            'Northern Ring — Closing the Loop',
            'The ring street curves back to where it started. The Wisteria Walk is just ahead.',
            'The ring curves back to meet itself here, the familiar pale stone of the Wisteria Walk '
            'visible just to the east where the path emerges from the park. The paving underfoot is its '
            'most worn on this stretch — foot traffic from the north path intersection spreads in both '
            'directions and this room catches most of it. The park trees on the inner edge are the same '
            'trees they have always been: patient, unhurried, growing around whatever the city has put '
            'next to them. The ring is complete. You have walked all the way around.',
        )

        # --- Morra's Smithy ---------------------------------------------------
        self._room(
            zone, 'smithy_ext', 0, 6,
            'Morra\'s Smithy — Entrance',
            'A low stone building. Heat bleeds from the open front. The sign reads MORRA\'S.',
            'The smithy sits directly across the ring street from Aldric\'s tree — a low solid structure '
            'of dark stone and heavy timber, forge-heat bleeding from the open front even on mild days. '
            'The sign above the door reads MORRA\'S in letters punched from sheet metal, functional and '
            'permanent. Through the open front, the equipment is visible: anvil, bellows, quench tank, '
            'racks of tools arranged with the precision of someone who knows where everything is and '
            'will know immediately if anything moves. The forge glows at the back. The whole space smells '
            'of hot metal and honest work.',
        )
        self._room(
            zone, 'smithy_int', 0, 7,
            'Morra\'s Smithy',
            'A well-equipped smithy. The forge glows at the back. A woman works at the anvil.',
            'Inside, the smithy is medium-sized and entirely serious. Every surface that isn\'t equipment '
            'is storage for equipment. The anvil is positioned for maximum reach from the forge. The '
            'quench tank is clean. The tool racks are arranged not by size or type but by the order in '
            'which they are most commonly reached for — a system that took years to optimize and would '
            'mean nothing to anyone else. A woman stands at the anvil. She does not look up when you '
            'enter but her posture changes slightly — the posture of someone who is now aware of you '
            'and reserving judgment.',
            indoors=True,
        )

        self.stdout.write(f'Rooms seeded: {len(self.rooms)}.')

    # ------------------------------------------------------------------
    # Exits
    # ------------------------------------------------------------------

    def _ring_edges(self):
        keys = [key for key, _ in RING_WALK]
        edges = []
        for i, (src, direction) in enumerate(RING_WALK):
            dst = keys[(i + 1) % len(keys)]
            edges.append((src, direction, dst))
            edges.append((dst, OPPOSITE[direction], src))
        return edges

    def _wire_exits(self):
        exit_map = {key: {} for key in self.rooms}
        for src, direction, dst in PATH_EDGES + self._ring_edges() + vr_edges():
            exit_map[src][direction] = dst

        for key, room in self.rooms.items():
            for direction in DIRECTIONS:
                target_key = exit_map[key].get(direction)
                setattr(room, f'exit_{direction}',
                        self.rooms[target_key] if target_key else None)
            room.save()

        self.stdout.write('Exits wired.')

    # ------------------------------------------------------------------
    # NPCs
    # ------------------------------------------------------------------

    def _seed_convergence_npcs(self):
        npcs = [
            (
                'the-obelisk', 'The Obelisk', 'cosmic', 'heart',
                'It has been here longer than the city. Longer than the paths. Longer than memory. '
                'It does not seem to notice you noticing it.'
            ),
            (
                'aldric', 'Aldric', 'fantasy', 'r01',
                'Old. Very old. The kind of old that stopped being surprised by anything a long time '
                'ago. He\'s watching you the way people watch weather — not unfriendly, just practiced.'
            ),
            (
                'info-prime', 'Info Prime', 'cyber', 'r10',
                'A robot of considerable age. The chassis shows repair work from multiple eras — '
                'components from wildly different periods of technological history bolted or welded '
                'alongside one another with varying degrees of elegance. The eyes glow a faint amber. '
                'It is watching you with the patience of something that has been watching things for '
                'a very long time.'
            ),
            (
                'repairbot-prime', 'Repairbot Prime', 'cyber', 'r10',
                'Version 2 of a familiar chassis. The same engineering logic as Info Prime, slightly '
                'newer — components from a narrower range of eras, the repairs slightly less layered. '
                'Its eyes glow amber, same as Info Prime\'s. It watches you with the same quality of '
                'patience. When it moves, it moves with the unhurried efficiency of something that has '
                'been doing this for three centuries and sees no reason to rush.'
            ),
            (
                'pella', 'Pella', 'fantasy', 'r18',
                'Small, bright-eyed, wearing more colors than the gazebo if that\'s possible. Old in '
                'the way of someone who decided a long time ago that age was happening to them whether '
                'they liked it or not and chose to like it. She has already decided she likes you.'
            ),
            (
                'ferwick', 'Ferwick', 'fantasy', 'r18',
                'Old and cheerful in the way of someone who has never found a good reason not to be. '
                'His hat is extraordinary in its wrongness. His eyes are sharp despite everything else '
                'about him suggesting mild disorder. He gives the impression of someone who is almost '
                'certainly going to be fine, eventually.'
            ),
            (
                'seris', 'Seris', 'cosmic', 'r24',
                'Ageless in the way that suggests a specific and considerable age rather than none at '
                'all. She is watching you with an attention that feels like more than looking. '
                'Not invasive. Thorough.'
            ),
            (
                'veris', 'Veris', 'cosmic', 'r24',
                'Identical to the other crystal structure in every physical particular. The presence '
                'inside it is the same quality — quiet, attentive, deep. It is aware of you in a way '
                'that feels considered rather than automatic.'
            ),
            (
                'morra', 'Morra', 'fantasy', 'smithy_int',
                'Compact, strong-handed, apron scorched in ways that tell a story. Old in the way of '
                'someone who has spent decades doing one thing and gotten very good at it. She is '
                'currently looking at whatever you\'ve brought her the way a doctor looks at a patient '
                '— professionally, without sentiment.'
            ),
        ]

        for slug, name, genre_tag, room_key, description in npcs:
            content = {
                'name': name,
                'genre_tag': genre_tag,
                'description': description,
                'is_aggressive': False,
                'is_unique': True,
                'wanders': False,
                'combat_tier': 'normal',
                'loot_table': None,
            }
            # Stats/drops are balance data — set on create only, matching the
            # Origin/Archetype convention below.
            balance = {
                **MINIMAL_STATS,
                'currency_drop_min': 0,
                'currency_drop_max': 0,
                'respawn_minutes': 0,
            }
            npc, created = NpcDefinition.objects.update_or_create(
                slug=slug,
                defaults=content,
                create_defaults={**content, **balance},
            )
            RoomSpawn.objects.get_or_create(
                room=self.rooms[room_key],
                npc_definition=npc,
                mk_tier=1,
                defaults={'count': 1, 'is_active': True},
            )
            self.stdout.write(
                f'  NpcDefinition "{name}" {"created" if created else "updated"}; '
                f'spawn in {self.rooms[room_key].name}.'
            )

    def _seed_primordial_sphere(self):
        # The first sphere — origin of the pattern every zone-end obelisk
        # sphere follows. Unlike the placeholder NPCs above, the brief pins
        # its stats at 1 across the board.
        content = {
            'name': 'the Primordial Sphere',
            'genre_tag': 'fantasy',
            'description': (
                'A perfect sphere of soft white light, suspended at eye level inside '
                'the stone of the Obelisk as though the stone grew around it. It does '
                'not spin, pulse, or drift — it simply is, with a patience that makes '
                'the plaza feel younger than it. Looking at it for too long feels '
                'less like watching and more like being read. It has never spoken. '
                'It never will. And yet every traveler who stands here leaves with '
                'the same quiet certainty: it noticed them.'
            ),
            'is_aggressive': False,
            'is_unique': True,
            'wanders': False,
            'combat_tier': 'normal',
            'loot_table': None,
            'unarmed_message_pool': None,
        }
        balance = {
            'base_vitality': 1,
            'base_str': 1, 'base_dex': 1, 'base_end': 1,
            'base_int': 1, 'base_wis': 1, 'base_per': 1,
            'scaling_factor': 1.0,
            'currency_drop_min': 0,
            'currency_drop_max': 0,
            'respawn_minutes': 0,
        }
        sphere, created = NpcDefinition.objects.update_or_create(
            slug='the-primordial-sphere',
            defaults=content,
            create_defaults={**content, **balance},
        )
        RoomSpawn.objects.get_or_create(
            room=self.rooms['heart'],
            npc_definition=sphere,
            mk_tier=1,
            defaults={'count': 1, 'is_active': True},
        )
        self.stdout.write(
            f'  NpcDefinition "the Primordial Sphere" {"created" if created else "updated"}; '
            f'spawn in {self.rooms["heart"].name}.'
        )

    # ------------------------------------------------------------------
    # Obelisk Network
    # ------------------------------------------------------------------

    def _seed_travel_nodes(self):
        nodes = [
            ('heart', 'The Convergence', 'obelisk'),
            ('vr-v07', 'Fordwatch', 'checkpoint'),
            ('vr-f01', 'Stairhead', 'checkpoint'),
            ('vr-c01', 'Cragfoot', 'checkpoint'),
            ('vr-vc1', 'The Verdant Crown', 'obelisk'),
        ]
        for room_key, travel_name, node_type in nodes:
            node, created = TravelNode.objects.get_or_create(
                room=self.rooms[room_key],
                defaults={
                    'travel_name': travel_name,
                    'node_type': node_type,
                },
            )
            self.stdout.write(
                f'  TravelNode "{node.travel_name}" ({node.node_type}) '
                f'{"created" if created else "exists"}.'
            )

    def _seed_travel_messages(self):
        pools = {
            'traveler': [
                'The world folds. For one breathless instant you are a thought between two places — then the ground remembers you.',
                'Light swallows light. You fall upward through somewhere that has no name, and arrive as though you never left.',
                'The obelisk does not move. Everything else does. When the world stops turning, you are elsewhere.',
                'You cross a boundary that was never meant to be seen, stitched shut behind you before you can look back.',
                'For a moment you are unmade — scattered across every place you have ever stood — and then gathered, gently, here.',
                'Somewhere between one heartbeat and the next, the universe changes its mind about where you are.',
                'The green of leaves, the grey of stone, the black between stars — all of it blurs past, or you blur past it.',
                'You step through the skin of the world. It does not tear. It welcomes.',
                'Distance forgets you. When it remembers, you are already there.',
                'The stone hums a single note too low to hear, and the world rearranges itself around your stillness.',
            ],
            'departure': [
                '{name} dissolves into motes of pale light that drift upward and are gone.',
                'The air folds around {name}, and where they stood there is only a fading afterimage.',
                '{name} takes a step that never lands. They are simply no longer here.',
                'A soundless pulse washes outward, and {name} is gone between one blink and the next.',
                'Light bends briefly around {name} — then straightens, having taken them with it.',
                "{name} fades like a figure walking into fog that isn't there.",
            ],
            'arrival': [
                'Motes of pale light gather and knit themselves into {name}.',
                'The air unfolds, and {name} steps out of a place that was never a doorway.',
                '{name} arrives mid-stride, as though finishing a step begun somewhere else entirely.',
                'A soundless pulse washes over the ground, and {name} is standing where no one stood.',
                'Light bends, brightens, and lets go of {name}.',
                '{name} coalesces out of the quiet, blinking, entirely here.',
            ],
        }
        created_count = 0
        for category, texts in pools.items():
            for text in texts:
                _, created = TravelMessage.objects.get_or_create(
                    category=category, text=text,
                )
                if created:
                    created_count += 1
        total = sum(len(texts) for texts in pools.values())
        self.stdout.write(f'  TravelMessages: {created_count} created ({total} defined).')

    # ------------------------------------------------------------------
    # Character starting rooms
    # ------------------------------------------------------------------

    def _set_character_rooms(self):
        heart = self.rooms['heart']
        moved_null = Character.objects.filter(current_room__isnull=True).update(current_room=heart)
        recall_set = Character.objects.filter(recall_room__isnull=True).update(recall_room=heart)
        # Also update any characters still in old placeholder rooms — but leave
        # anyone standing in a seeded zone where they are.
        moved_outside = Character.objects.exclude(
            current_room__zone__slug__in=('the-convergence', 'the-verdant-reach'),
        ).update(current_room=heart)
        self.stdout.write(
            f'Characters: {moved_null} moved from no room, {recall_set} recall rooms set, '
            f'{moved_outside} moved from outside The Convergence.'
        )

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def _check(self, label, condition):
        if condition:
            self.stdout.write(self.style.SUCCESS(f'  PASS: {label}'))
        else:
            self.stdout.write(self.style.ERROR(f'  FAIL: {label}'))
            self._failures.append(label)

    def _walk_ok(self, start_key, steps):
        """Follow exits from start_key through (direction, expected key) steps,
        re-reading each room from the DB so the check reflects persisted state."""
        current = self.rooms[start_key]
        for direction, expected_key in steps:
            db_room = Room.objects.get(pk=current.pk)
            expected = self.rooms[expected_key]
            if getattr(db_room, f'exit_{direction}_id') != expected.pk:
                return False
            current = expected
        return True

    def _verify(self):
        self._failures = []
        self.stdout.write('Verification:')

        zone_exists = Zone.objects.filter(slug='the-convergence').exists()
        self._check('Zone the-convergence exists', zone_exists)

        area_count = Area.objects.filter(zone__slug='the-convergence').count()
        self._check(f'4 areas exist (found {area_count})', area_count == 4)

        room_count = Room.objects.filter(zone__slug='the-convergence').count()
        self._check(f'54 rooms exist (found {room_count})', room_count == 54)

        heart = Room.objects.filter(
            zone__slug='the-convergence', coord_x=0, coord_y=0, coord_z=0,
        ).first()
        self._check(
            'Heart of the Convergence at (0,0,0)',
            heart is not None and heart.name == 'Heart of the Convergence',
        )

        if heart is not None:
            self._check(
                'Heart has all four cardinal exits and no up/down',
                all(getattr(heart, f'exit_{d}_id') is not None
                    for d in ('north', 'south', 'east', 'west'))
                and heart.exit_up_id is None and heart.exit_down_id is None,
            )

        ring_keys = [key for key, _ in RING_WALK]
        ring_steps = [
            (direction, ring_keys[(i + 1) % len(ring_keys)])
            for i, (_, direction) in enumerate(RING_WALK)
        ]
        self._check(
            'Ring street is a closed 35-room clockwise loop',
            self._walk_ok('r01', ring_steps),
        )

        self._check('Wisteria Walk connects heart to R01', self._walk_ok('heart', [
            ('north', 'ww1'), ('west', 'ww2'), ('north', 'ww3'),
            ('north', 'ww4'), ('north', 'r01'),
        ]))
        self._check('Bamboo Run connects heart to R10', self._walk_ok('heart', [
            ('east', 'br1'), ('east', 'br2'), ('east', 'br3'), ('east', 'r10'),
        ]))
        self._check('Basalt Way connects heart to R18', self._walk_ok('heart', [
            ('south', 'bw1'), ('east', 'bw2'), ('south', 'bw3'),
            ('south', 'bw4'), ('south', 'bw5'), ('south', 'r18'),
        ]))
        self._check('Fern Boards connects heart to R24', self._walk_ok('heart', [
            ('west', 'fb1'), ('west', 'fb2'), ('west', 'fb3'),
            ('west', 'fb4'), ('west', 'r24'),
        ]))

        npc_count = NpcDefinition.objects.filter(slug__in=[
            'the-obelisk', 'aldric', 'info-prime', 'repairbot-prime',
            'pella', 'ferwick', 'seris', 'veris', 'morra',
            'the-primordial-sphere',
        ]).count()
        self._check(f'10 NPC definitions exist (found {npc_count})', npc_count == 10)

        spawn_count = RoomSpawn.objects.filter(room__zone__slug='the-convergence').count()
        self._check(f'10 RoomSpawns in The Convergence (found {spawn_count})', spawn_count == 10)

        sphere_spawns = RoomSpawn.objects.filter(
            npc_definition__slug='the-primordial-sphere',
        )
        self._check(
            'Primordial Sphere has exactly one spawn, at the Heart',
            sphere_spawns.count() == 1
            and heart is not None
            and sphere_spawns.first().room_id == heart.pk,
        )

        node_count = TravelNode.objects.count()
        heart_node = TravelNode.objects.filter(
            room=heart, travel_name='The Convergence', node_type='obelisk',
        ).exists() if heart is not None else False
        crown_node = TravelNode.objects.filter(
            room=self.rooms['vr-vc1'], travel_name='The Verdant Crown',
            node_type='obelisk',
        ).exists()
        checkpoint_nodes = TravelNode.objects.filter(
            node_type='checkpoint',
            travel_name__in=('Fordwatch', 'Stairhead', 'Cragfoot'),
        ).count()
        self._check(
            f'Exactly 5 TravelNodes: the Convergence and Verdant Crown '
            f'obelisks plus the Fordwatch, Stairhead, and Cragfoot '
            f'checkpoints (found {node_count})',
            node_count == 5 and heart_node and crown_node
            and checkpoint_nodes == 3,
        )

        msg_counts = {
            category: TravelMessage.objects.filter(category=category).count()
            for category in ('traveler', 'departure', 'arrival')
        }
        self._check(
            f'22 travel messages: 10 traveler, 6 departure, 6 arrival '
            f'(found {msg_counts})',
            msg_counts == {'traveler': 10, 'departure': 6, 'arrival': 6},
        )

        placeholder_count = Room.objects.filter(
            zone__slug='the-convergence', name='The Fracture Point',
        ).count()
        self._check('Placeholder rooms are gone', placeholder_count == 0)

        smithy = Room.objects.filter(
            zone__slug='the-convergence', coord_x=0, coord_y=7, coord_z=0,
        ).first()
        self._check(
            'Smithy interior is flagged indoors',
            smithy is not None and smithy.flag_indoors,
        )

        unsafe_count = Room.objects.filter(
            zone__slug='the-convergence', flag_safe=False,
        ).count()
        self._check('All Convergence rooms are flag_safe', unsafe_count == 0)

        material_count = ItemDefinition.objects.filter(
            item_type='material', slug__in=('animal-hide', 'insect-carapace'),
        ).count()
        self._check(
            f'2 material ItemDefinitions exist (found {material_count})',
            material_count == 2,
        )

        unvalued = ItemDefinition.objects.filter(base_value=1).count()
        self._check(
            f'No ItemDefinition left at default base_value (found {unvalued})',
            unvalued == 0,
        )

        self._verify_verdant()

        if self._failures:
            raise CommandError(f'{len(self._failures)} verification check(s) failed.')
        self.stdout.write(self.style.SUCCESS('All verification checks passed.'))

    def _verify_verdant(self):
        vr = 'the-verdant-reach'
        self._check('Zone the-verdant-reach exists', Zone.objects.filter(slug=vr).exists())

        vr_area_count = Area.objects.filter(zone__slug=vr).count()
        self._check(f'10 Verdant Reach areas exist (found {vr_area_count})', vr_area_count == 10)

        vr_room_count = Room.objects.filter(zone__slug=vr).count()
        self._check(f'150 Verdant Reach rooms exist (found {vr_room_count})', vr_room_count == 150)

        # Every Verdant edge is wired in both directions, per the persisted DB
        # state (vr_edges() already contains both directions of each pair).
        edges_ok = True
        for src, direction, dst in vr_edges():
            db_room = Room.objects.get(pk=self.rooms[src].pk)
            if getattr(db_room, f'exit_{direction}_id') != self.rooms[dst].pk:
                edges_ok = False
                break
        self._check('All Verdant Reach exits wired bidirectionally '
                    '(including the Verdant gate)', edges_ok)

        f18 = Room.objects.get(pk=self.rooms['vr-f18'].pk)
        self._check(
            'vr-f18 north exit wired to Cragfoot with its pending message gone',
            f18.exit_north_id == self.rooms['vr-c01'].pk
            and f18.no_exit_north_msg == '',
        )

        r02 = Room.objects.get(pk=self.rooms['r02'].pk)
        self._check(
            'Verdant gate room no longer carries the sealed message',
            r02.no_exit_north_msg == '' and r02.exit_north_id == self.rooms['vr-v01'].pk,
        )

        safe_keys = {
            key for key, room in self.rooms.items()
            if key.startswith('vr-') and Room.objects.get(pk=room.pk).flag_safe
        }
        self._check(
            'Fordwatch, Stairhead, Cragfoot, and the Verdant Crown are the '
            'only safe Verdant rooms',
            safe_keys == {'vr-v07', 'vr-f01', 'vr-c01', 'vr-vc1'},
        )

        indoor_count = Room.objects.filter(zone__slug=vr, flag_indoors=True).count()
        cave_keys = [
            k for k in self.rooms
            if k.startswith('vr-c') and k not in ('vr-c01',)
        ]
        self._check(
            f'All 49 cave rooms are flag_indoors (found {indoor_count})',
            indoor_count == 49 and len(cave_keys) == 49
            and all(Room.objects.get(pk=self.rooms[k].pk).flag_indoors for k in cave_keys),
        )

        self._check(
            'No Verdant Reach room is flag_dark',
            not Room.objects.filter(zone__slug=vr, flag_dark=True).exists(),
        )

        vr_npc_slugs = [
            'river-otter', 'black-bear', 'young-mountain-lion', 'wild-boar',
            'plains-deer', 'plains-rabbit', 'prairie-dog', 'buffalo',
            'reedmere-villager', 'reedmere-fisher', 'windhome-villager',
            'windhome-hunter', 'maro-the-mender', 'essa-the-trader',
            'tavik-the-mender', 'sona-the-trader', 'verdant-shard',
            'cave-spider', 'cave-centipede', 'cave-beetle',
            'giant-cave-spider', 'giant-cave-centipede', 'giant-cave-beetle',
            'silk-matron', 'whistler-below', 'dronemother',
            'matrons-brood', 'whistlers-young', 'dronemothers-swarm',
        ]
        ridge_passive_slugs = [
            'mountain-goat', 'mountain-squirrel', 'brown-bear', 'mountain-lion',
            'mountain-villager', 'mountain-hunter', 'old-brammel',
            'ridda-the-trader', 'the-verdant-sphere',
        ]
        ridge_aggro_slugs = [
            'prowling-mountain-lion', 'territorial-brown-bear',
            'elder-cave-spider', 'elder-cave-centipede', 'elder-cave-beetle',
            'undercrag-weaver', 'chittering-king', 'crowned-devourer',
            'weavers-brood', 'kings-skitterlings', 'devourers-drones',
        ]
        all_vr_slugs = vr_npc_slugs + ridge_passive_slugs + ridge_aggro_slugs
        vr_npc_count = NpcDefinition.objects.filter(slug__in=all_vr_slugs).count()
        self._check(
            f'49 Verdant NPC definitions exist (found {vr_npc_count})',
            vr_npc_count == 49,
        )

        aggro_ok = (
            not NpcDefinition.objects.filter(
                slug__in=vr_npc_slugs[:17] + ridge_passive_slugs,
                is_aggressive=True,
            ).exists()
            and NpcDefinition.objects.filter(
                slug__in=vr_npc_slugs[17:] + ridge_aggro_slugs,
                is_aggressive=True,
            ).count() == 23
        )
        self._check('Surface/villager NPCs passive; aggro variants, cave NPCs, '
                    'bosses, and minions aggressive', aggro_ok)

        boss_ok = (
            NpcDefinition.objects.filter(
                slug__in=('silk-matron', 'whistler-below', 'dronemother',
                          'undercrag-weaver', 'chittering-king',
                          'crowned-devourer'),
                combat_tier='boss', is_unique=False,
            ).exclude(death_message='').count() == 6
        )
        self._check('6 bosses at combat_tier boss with death messages', boss_ok)

        repairer_count = NpcDefinition.objects.filter(
            slug__in=('maro-the-mender', 'tavik-the-mender', 'old-brammel'),
            is_repairer=True,
        ).count()
        self._check('Maro, Tavik, and Old Brammel are repairers', repairer_count == 3)

        sphere = NpcDefinition.objects.filter(
            slug='the-verdant-sphere', is_unique=True,
        ).first()
        sphere_spawns = RoomSpawn.objects.filter(
            npc_definition__slug='the-verdant-sphere',
        )
        self._check(
            'The Verdant Sphere is unique with exactly one spawn, at the Crown',
            sphere is not None and sphere_spawns.count() == 1
            and sphere_spawns.first().room_id == self.rooms['vr-vc1'].pk,
        )

        vr_spawn_count = RoomSpawn.objects.filter(room__zone__slug=vr).count()
        self._check(
            f'129 RoomSpawns in the Verdant Reach (found {vr_spawn_count})',
            vr_spawn_count == 129,
        )

        gated = RoomSpawn.objects.filter(
            room__zone__slug=vr, requires_living_npc__isnull=False,
        )
        gated_ok = gated.count() == 6 and all(
            spawn.npc_definition.slug == minion
            and spawn.requires_living_npc.slug == boss
            for minion, boss, spawn in (
                (m, b, gated.get(npc_definition__slug=m))
                for m, b in (
                    ('matrons-brood', 'silk-matron'),
                    ('whistlers-young', 'whistler-below'),
                    ('dronemothers-swarm', 'dronemother'),
                    ('weavers-brood', 'undercrag-weaver'),
                    ('kings-skitterlings', 'chittering-king'),
                    ('devourers-drones', 'crowned-devourer'),
                )
            )
        )
        self._check('6 minion spawns gated on their bosses', gated_ok)

        table_entry_counts = {
            'animal-drops': 1, 'insect-drops': 1,
            'reedmere-gear': 4, 'windhome-gear': 4,
            'matron-loot': 7, 'whistler-loot': 9, 'dronemother-loot': 13,
            'ridge-gear': 4, 'ridge-hunter-gear': 5,
            'weaver-loot': 7, 'king-loot': 9, 'devourer-loot': 13,
        }
        tables_ok = all(
            LootTableEntry.objects.filter(loot_table__slug=slug).count() == n
            for slug, n in table_entry_counts.items()
        )
        self._check('12 Verdant loot tables with expected entry counts', tables_ok)

        group_counts = {
            'matron-loot': ('weapon', 6),
            'whistler-loot': ('armor', 8),
            'dronemother-loot': ('accessory', 12),
            'weaver-loot': ('weapon', 6),
            'king-loot': ('armor', 8),
            'devourer-loot': ('accessory', 12),
        }
        groups_ok = all(
            LootTableEntry.objects.filter(
                loot_table__slug=slug, guaranteed_group=group,
            ).count() == n
            for slug, (group, n) in group_counts.items()
        )
        self._check('Boss loot guaranteed groups populated', groups_ok)

        epic_ok = not LootTableEntry.objects.filter(
            loot_table__slug='devourer-loot', guaranteed_group='accessory',
        ).exclude(rarity_weights={'epic': 100}).exists()
        self._check("Devourer accessories all roll at {'epic': 100}", epic_ok)

        pool_ok = all(
            UnarmedMessage.objects.filter(pool__slug=f'{prefix}-{species}').count() == 4
            for prefix in ('vale', 'flats', 'ridge')
            for species in ('spider', 'centipede', 'beetle')
        )
        self._check('9 Verdant unarmed pools with 4 messages each', pool_ok)

        vendor_ok = (
            VendorEntry.objects.filter(npc_definition__slug='essa-the-trader').count() == 4
            and VendorEntry.objects.filter(npc_definition__slug='sona-the-trader').count() == 4
            and VendorEntry.objects.filter(npc_definition__slug='ridda-the-trader').count() == 5
        )
        self._check('Essa and Sona carry 4 vendor entries each; Ridda carries 5', vendor_ok)

    # ------------------------------------------------------------------
    # Shared platform seed data (unchanged)
    # ------------------------------------------------------------------

    def _seed_unarmed_pools(self):
        default_pool, created = UnarmedMessagePool.objects.get_or_create(
            slug='default',
            defaults={'name': 'Default'},
        )
        self.stdout.write(f'  UnarmedMessagePool "Default" {"created" if created else "exists"}.')

        UnarmedMessage.objects.filter(pool=default_pool).delete()
        messages = [
            "You punch {target}.",
            "You kick {target}.",
            "You shove {target} hard.",
            "You swing at {target}.",
            "You lunge at {target}.",
            "You jab {target}.",
            "You strike {target}.",
            "You slam into {target}.",
            "You drive your shoulder into {target}.",
            "You throw a wild hit at {target}.",
        ]
        for i, template in enumerate(messages):
            UnarmedMessage.objects.create(pool=default_pool, template=template, order=i)
        self.stdout.write(f'  Seeded {len(messages)} UnarmedMessages in "Default" pool.')

        # Verdant Reach species pools (v18 briefs 5 and 6). The flats and
        # ridge pools are the vale pools with the species noun upsized to its
        # giant/elder variant.
        vale_templates = {
            'spider': [
                'The spider blurs sideways and strikes at {target}, fangs first.',
                'The spider drops on {target} from above, all legs at once.',
                'The spider skitters in a half-circle and lunges at {target}.',
                'The spider feints left, flows right, and bites at {target}.',
            ],
            'centipede': [
                'The centipede pours across the stone and whips its body at {target}.',
                'The centipede rears its front third and rakes at {target} with hooked legs.',
                "The centipede flows over {target}'s boot and bites upward.",
                'The centipede coils and springs at {target} in one dry rush.',
            ],
            'beetle': [
                "The beetle's wings snap open and it swoops down on {target}.",
                'The beetle drops from the ceiling darkness onto {target}.',
                "The beetle buzzes past {target}'s ear and rakes back across, clawed legs first.",
                'The beetle slams into {target} like a thrown stone, wings roaring.',
            ],
        }
        vr_pools = {}
        for species, templates in vale_templates.items():
            vr_pools[f'vale-{species}'] = (
                f'Vale {species.capitalize()} Attacks', templates,
            )
            vr_pools[f'flats-{species}'] = (
                f'Flats {species.capitalize()} Attacks',
                [t.replace(f'The {species}', f'The giant {species}') for t in templates],
            )
            vr_pools[f'ridge-{species}'] = (
                f'Ridge {species.capitalize()} Attacks',
                [t.replace(f'The {species}', f'The elder {species}') for t in templates],
            )
        for slug, (name, templates) in vr_pools.items():
            pool, _ = UnarmedMessagePool.objects.get_or_create(
                slug=slug, defaults={'name': name},
            )
            for i, template in enumerate(templates):
                UnarmedMessage.objects.get_or_create(
                    pool=pool, template=template, defaults={'order': i},
                )
        self.stdout.write(f'  Seeded {len(vr_pools)} Verdant Reach unarmed pools.')

        # NPC attack fallback pool (v19 brief 3) — NPC attacks never fall
        # back to the player-perspective "default" pool.
        npc_default_templates = [
            'The {attacker} strikes {target}',
            'The {attacker} lashes out at {target}',
            'The {attacker} slams into {target}',
            'The {attacker} tears at {target}',
        ]
        # Verdant surface animal species pools (v19 brief 3), third person.
        animal_templates = {
            'sp-river-otter': (
                'River Otter Attacks',
                [
                    'The river otter darts in and rakes {target} with quick claws',
                    "The river otter twists around {target}'s legs and bites hard",
                    'The river otter snaps at {target} with surprising ferocity',
                    'The river otter slams its sleek body against {target}',
                ],
            ),
            'sp-black-bear': (
                'Black Bear Attacks',
                [
                    'The black bear rakes {target} with a heavy paw',
                    'The black bear clamps its jaws down on {target}',
                    'The black bear rears up and slams its weight into {target}',
                    'The black bear swats {target} aside with terrible strength',
                ],
            ),
            'sp-mountain-lion': (
                'Young Mountain Lion Attacks',
                [
                    'The young mountain lion rakes {target} with both sets of claws',
                    'The young mountain lion sinks its teeth into {target}',
                    'The young mountain lion pounces, driving {target} back',
                    'The young mountain lion slashes at {target} in a blur',
                ],
            ),
            'sp-wild-boar': (
                'Wild Boar Attacks',
                [
                    'The wild boar gores {target} with a slashing tusk',
                    'The wild boar charges headlong into {target}',
                    'The wild boar hooks its tusks upward into {target}',
                    'The wild boar tramples over {target} in a frenzy',
                ],
            ),
            'sp-plains-deer': (
                'Plains Deer Attacks',
                [
                    'The plains deer lashes out at {target} with sharp hooves',
                    'The plains deer rears and strikes {target} hard',
                    'The plains deer drives its antlers at {target}',
                    'The plains deer kicks {target} with startling force',
                ],
            ),
            'sp-plains-rabbit': (
                'Plains Rabbit Attacks',
                [
                    'The plains rabbit rakes {target} with powerful hind claws',
                    'The plains rabbit bites {target} and darts away',
                    'The plains rabbit thumps into {target} at full speed',
                    'The plains rabbit scratches furiously at {target}',
                ],
            ),
            'sp-prairie-dog': (
                'Prairie Dog Attacks',
                [
                    'The prairie dog nips at {target} with chisel teeth',
                    "The prairie dog darts between {target}'s feet, biting",
                    'The prairie dog scratches at {target} in a fury',
                    "The prairie dog latches onto {target} and won't let go",
                ],
            ),
            'sp-buffalo': (
                'Buffalo Attacks',
                [
                    'The buffalo drives its horns into {target}',
                    'The buffalo slams a ton of muscle into {target}',
                    'The buffalo hooks {target} and tosses them aside',
                    'The buffalo tramples {target} beneath heavy hooves',
                ],
            ),
        }
        npc_pools = {'npc-default': ('NPC Default Attacks', npc_default_templates)}
        npc_pools.update(animal_templates)
        for slug, (name, templates) in npc_pools.items():
            pool, _ = UnarmedMessagePool.objects.get_or_create(
                slug=slug, defaults={'name': name},
            )
            for i, template in enumerate(templates):
                UnarmedMessage.objects.get_or_create(
                    pool=pool, template=template, defaults={'order': i},
                )
        self.stdout.write(f'  Seeded {len(npc_pools)} NPC unarmed pools '
                          f'(npc-default + {len(animal_templates)} species).')

    def _seed_origins(self):
        origins = [
            {
                'slug': 'highborn', 'name': 'Highborn',
                'acuity_baseline': 1.0, 'acuity_band_low': 0.85, 'acuity_band_high': 1.15,
                'description': "Born into privilege and lineage in a fantasy court, carrying inherited confidence and formal training. Their minds rest at the same steady center most Origins share — no special gift, no burden, just the quiet certainty of someone raised to believe they belong.",
                'attire_material': 'fine tailored fabrics in noble colors',
            },
            {
                'slug': 'feral', 'name': 'Feral',
                'acuity_baseline': 0.95, 'acuity_band_low': 0.80, 'acuity_band_high': 1.10,
                'description': "Raised by wild lands and tribal codes, moving with an animal's economy and an instinctive read of terrain. Their minds run a touch looser than most, tuned to reflex over deliberation.",
                'attire_material': 'tanned hides, fur, and woven plant fiber',
            },
            {
                'slug': 'streetborn', 'name': 'Streetborn',
                'acuity_baseline': 1.0, 'acuity_band_low': 0.85, 'acuity_band_high': 1.15,
                'description': "Cut their teeth in a neon-lit cyberpunk sprawl, reading a crowd, a network, and a threat with equal fluency. Same steady baseline as Highborn — sharpened by constant low-grade urban vigilance instead.",
                'attire_material': 'salvaged synthetics and street-tech patchwork',
            },
            {
                'slug': 'irradiated', 'name': 'Irradiated',
                'acuity_baseline': 0.90, 'acuity_band_low': 0.75, 'acuity_band_high': 1.05,
                'description': "Survivors of a shattered, irradiated world, bodies at uneasy peace with poison. That peace costs something — minds resting slightly below center, worn by scarcity and threat.",
                'attire_material': 'patched scavenged canvas and scrap plating',
            },
            {
                'slug': 'undying', 'name': 'Undying',
                'acuity_baseline': 0.80, 'acuity_band_low': 0.65, 'acuity_band_high': 1.00,
                'description': "Touched by a gothic curse or blessing that keeps death from fully taking hold. Minds settle well below the common center — colder, quieter — and that same distance is what makes death sting less.",
                'attire_material': 'black lace and grave-worn cloth',
            },
            {
                'slug': 'machinekind', 'name': 'Machinekind',
                'acuity_baseline': 1.05, 'acuity_band_low': 0.90, 'acuity_band_high': 1.20,
                'description': "Built, not born: steam-driven constructs of gears and something that might be a soul. Runs slightly hot by design. No blood for poison to spoil, but the same mechanical nature means magic slides off too — only honest repair mends them.",
                'attire_material': 'riveted brass plating and worn leather straps',
            },
            {
                'slug': 'voidtouched', 'name': 'Voidtouched',
                'acuity_baseline': 0.70, 'acuity_band_low': 0.40, 'acuity_band_high': 1.30,
                'description': "Stared into something between the stars and lived. A permanent, unsettling distance from ordinary thought. That same distance lets them tolerate extremes of focus and scatter that would break anyone else, and channel eldritch forces others can barely touch.",
                'attire_material': 'shifting, void-dark cloth that seems to drink the light',
            },
        ]
        for data in origins:
            slug = data.pop('slug')
            name = data.pop('name')
            # Acuity values are balance data an admin may have tuned in prod —
            # set them on create only; re-runs update content fields alone.
            balance = {k: data.pop(k) for k in ('acuity_baseline', 'acuity_band_low', 'acuity_band_high')}
            content = {'name': name, **data}
            _, created = Origin.objects.update_or_create(
                slug=slug,
                defaults=content,
                create_defaults={**content, **balance},
            )
            self.stdout.write(f'  Origin "{name}" {"created" if created else "updated"}.')

    def _seed_archetypes(self):
        archetypes = [
            {
                'slug': 'blade', 'name': 'Blade', 'primary_stat_1': 'str', 'primary_stat_2': 'dex',
                'description': "Closes distance and ends fights with raw physical skill. STR and DEX in equal measure, equally at home as a disciplined duelist or a street brawler.",
                'attire_silhouette': 'a fitted tunic with wrapped forearms',
            },
            {
                'slug': 'bulwark', 'name': 'Bulwark', 'primary_stat_1': 'str', 'primary_stat_2': 'end',
                'description': "Stands between danger and everyone else. STR and END built to absorb punishment nothing lighter could survive.",
                'attire_silhouette': 'a heavy layered coat',
            },
            {
                'slug': 'shade', 'name': 'Shade', 'primary_stat_1': 'dex', 'primary_stat_2': 'int',
                'description': "Wins fights before the enemy knows one started. DEX for speed, INT for the cunning to strike where it hurts, then be somewhere else.",
                'attire_silhouette': 'a close-cut hooded wrap',
            },
            {
                'slug': 'conduit', 'name': 'Conduit', 'primary_stat_1': 'int', 'primary_stat_2': 'wis',
                'description': "Channels raw power through mind and will. INT to shape it, WIS to control it without being consumed.",
                'attire_silhouette': 'flowing, loose-sleeved robes',
            },
            {
                'slug': 'warden', 'name': 'Warden', 'primary_stat_1': 'wis', 'primary_stat_2': 'end',
                'description': "Keeps everyone else standing. WIS for healing, END to outlast the fight. Also nudges allies' Acuity back toward its band when it's drifted too far.",
                'attire_silhouette': 'simple, unadorned vestments',
            },
            {
                'slug': 'gunner', 'name': 'Gunner', 'primary_stat_1': 'dex', 'primary_stat_2': 'per',
                'description': "Deals damage from range and rarely misses. DEX for the trigger, PER for the read on distance and timing.",
                'attire_silhouette': 'a trim long coat with a cinched belt',
            },
            {
                'slug': 'machinist', 'name': 'Machinist', 'primary_stat_1': 'int', 'primary_stat_2': 'dex',
                'description': "Doesn't fight alone. INT to build and command, DEX to keep deployments fast under pressure.",
                'attire_silhouette': 'a utility vest lined with tool loops',
            },
        ]
        for data in archetypes:
            slug = data.pop('slug')
            name = data.pop('name')
            # Primary stats are balance data — set on create only, like Origin
            # acuity values above.
            balance = {k: data.pop(k) for k in ('primary_stat_1', 'primary_stat_2')}
            content = {'name': name, **data}
            _, created = Archetype.objects.update_or_create(
                slug=slug,
                defaults=content,
                create_defaults={**content, **balance},
            )
            self.stdout.write(f'  Archetype "{name}" {"created" if created else "updated"}.')

    def _seed_effects(self):
        # --- Healing Draught ---
        healing_draught, created = EffectDefinition.objects.get_or_create(
            slug='healing-draught',
            defaults={
                'name': 'Healing Draught',
                'description': 'Restores Vitality immediately.',
            },
        )
        healing_draught.components.all().delete()
        EffectComponent.objects.create(
            definition=healing_draught,
            component_type='restore_vitality',
            magnitude_base=20.0,
            magnitude_scaling=5.0,
            duration_base=0.0,
            duration_scaling=0.0,
            order=0,
        )
        self.stdout.write(f'  EffectDefinition "{healing_draught.name}" {"created" if created else "exists"}.')

        # --- Focus Tonic ---
        focus_tonic, created = EffectDefinition.objects.get_or_create(
            slug='focus-tonic',
            defaults={
                'name': 'Focus Tonic',
                'description': 'Sharpens Acuity upward over time.',
            },
        )
        focus_tonic.components.all().delete()
        EffectComponent.objects.create(
            definition=focus_tonic,
            component_type='shift_acuity_high',
            magnitude_base=0.1,
            magnitude_scaling=0.05,
            duration_base=30.0,
            duration_scaling=5.0,
            order=0,
        )
        self.stdout.write(f'  EffectDefinition "{focus_tonic.name}" {"created" if created else "exists"}.')

        # --- Fracture Wraith Poison ---
        wraith_poison, created = EffectDefinition.objects.get_or_create(
            slug='fracture-wraith-poison',
            defaults={
                'name': 'Fracture Wraith Poison',
                'description': 'Vitality damage over time from the Fracture Wraith.',
            },
        )
        wraith_poison.components.all().delete()
        EffectComponent.objects.create(
            definition=wraith_poison,
            component_type='dot_vitality',
            magnitude_base=3.0,
            magnitude_scaling=2.0,
            duration_base=15.0,
            duration_scaling=3.0,
            order=0,
        )
        self.stdout.write(f'  EffectDefinition "{wraith_poison.name}" {"created" if created else "exists"}.')

        self._effects = {
            'healing-draught': healing_draught,
            'focus-tonic': focus_tonic,
            'fracture-wraith-poison': wraith_poison,
        }

    def _seed_items(self):
        effects = self._effects

        # v18: absorb the legacy generic copper ring into the stat-suffixed set.
        ItemDefinition.objects.filter(slug='copper-ring').update(
            slug='copper-ring-of-wisdom',
            name='Copper Ring of Wisdom',
        )

        items = [
            # Weapons
            {
                'slug': 'iron-sword',
                'name': 'Iron Sword',
                'item_type': 'weapon',
                'genre_tag': 'fantasy',
                'valid_slots': ['MAIN_HAND'],
                'is_two_handed': False,
                'scaling_base': 8.0,
                'scaling_factor': 3.0,
                'damage_spread': 4.0,
                'is_ranged': False,
                'takes_durability_loss': True,
                'durability_table': WEAPON_DUR,
                'primary_stats': [{'stat': 'str', 'base': 3.0, 'factor': 1.0}],
                'secondary_stat_pool': [
                    {'stat': 'dex', 'base': 1.0, 'factor': 0.5},
                    {'stat': 'crit_chance', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'bleed_chance', 'base': 0.3, 'factor': 0.1},
                    {'stat': 'lifesteal', 'base': 0.2, 'factor': 0.1},
                ],
                'description': 'A reliable iron blade. Well-balanced and well-worn.',
            },
            {
                'slug': 'combat-knife',
                'name': 'Combat Knife',
                'item_type': 'weapon',
                'genre_tag': 'wasteland',
                'valid_slots': ['MAIN_HAND', 'OFF_HAND'],
                'is_two_handed': False,
                'scaling_base': 5.0,
                'scaling_factor': 2.0,
                'damage_spread': 2.0,
                'is_ranged': False,
                'takes_durability_loss': True,
                'durability_table': WEAPON_DUR,
                'primary_stats': [{'stat': 'dex', 'base': 3.0, 'factor': 1.0}],
                'secondary_stat_pool': [
                    {'stat': 'str', 'base': 1.0, 'factor': 0.3},
                    {'stat': 'crit_chance', 'base': 1.0, 'factor': 0.3},
                    {'stat': 'bleed_chance', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'poison_chance', 'base': 0.3, 'factor': 0.1},
                ],
                'description': 'Scratched and notched but still sharp. Does the job.',
            },
            {
                'slug': 'pulse-pistol',
                'name': 'Pulse Pistol',
                'item_type': 'weapon',
                'genre_tag': 'cyber',
                'valid_slots': ['RANGED', 'MAIN_HAND'],
                'is_two_handed': False,
                'scaling_base': 6.0,
                'scaling_factor': 2.5,
                'damage_spread': 3.0,
                'is_ranged': True,
                'takes_durability_loss': True,
                'durability_table': RANGED_DUR,
                'primary_stats': [
                    {'stat': 'dex', 'base': 2.0, 'factor': 0.8},
                    {'stat': 'per', 'base': 2.0, 'factor': 0.8},
                ],
                'secondary_stat_pool': [
                    {'stat': 'crit_chance', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'electric_damage_bonus', 'base': 0.3, 'factor': 0.1},
                    {'stat': 'per', 'base': 1.0, 'factor': 0.4},
                ],
                'description': 'A compact energy sidearm. Hums faintly when charged.',
            },
            {
                'slug': 'apprentice-staff',
                'name': 'Apprentice Staff',
                'item_type': 'weapon',
                'genre_tag': 'fantasy',
                'valid_slots': ['MAIN_HAND'],
                'is_two_handed': True,
                'scaling_base': 7.0,
                'scaling_factor': 2.5,
                'damage_spread': 5.0,
                'is_ranged': False,
                'takes_durability_loss': True,
                'durability_table': WEAPON_DUR,
                'primary_stats': [{'stat': 'int', 'base': 4.0, 'factor': 1.2}],
                'secondary_stat_pool': [
                    {'stat': 'wis', 'base': 1.0, 'factor': 0.5},
                    {'stat': 'spell_damage_bonus', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'mana_regen', 'base': 0.3, 'factor': 0.1},
                ],
                'description': 'Gnarled wood wrapped in copper wire. Crackles with unfocused energy.',
            },
            {
                'slug': 'iron-mace',
                'name': 'Iron Mace',
                'item_type': 'weapon',
                'genre_tag': 'fantasy',
                'valid_slots': ['MAIN_HAND'],
                'is_two_handed': False,
                'scaling_base': 8.0,
                'scaling_factor': 3.0,
                'damage_spread': 3.0,
                'is_ranged': False,
                'takes_durability_loss': True,
                'durability_table': WEAPON_DUR,
                'primary_stats': [{'stat': 'str', 'base': 3.0, 'factor': 1.0}],
                'secondary_stat_pool': [
                    {'stat': 'end', 'base': 1.0, 'factor': 0.4},
                    {'stat': 'stun_chance', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'physical_resist', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A heavy iron head on a short haft. Argument-ending.',
            },
            {
                'slug': 'broadsword',
                'name': 'Broadsword',
                'item_type': 'weapon',
                'genre_tag': 'fantasy',
                'valid_slots': ['MAIN_HAND'],
                'is_two_handed': True,
                'scaling_base': 12.0,
                'scaling_factor': 4.5,
                'damage_spread': 5.0,
                'is_ranged': False,
                'takes_durability_loss': True,
                'durability_table': WEAPON_DUR,
                'primary_stats': [{'stat': 'str', 'base': 4.0, 'factor': 1.2}],
                'secondary_stat_pool': [
                    {'stat': 'dex', 'base': 1.0, 'factor': 0.5},
                    {'stat': 'crit_chance', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'bleed_chance', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'lifesteal', 'base': 0.2, 'factor': 0.1},
                ],
                'description': 'A long, wide blade that wants both hands. Steady and unhurried.',
            },
            {
                'slug': 'battle-axe',
                'name': 'Battle Axe',
                'item_type': 'weapon',
                'genre_tag': 'fantasy',
                'valid_slots': ['MAIN_HAND'],
                'is_two_handed': True,
                'scaling_base': 11.0,
                'scaling_factor': 4.5,
                'damage_spread': 8.0,
                'is_ranged': False,
                'takes_durability_loss': True,
                'durability_table': WEAPON_DUR,
                'primary_stats': [{'stat': 'str', 'base': 4.0, 'factor': 1.2}],
                'secondary_stat_pool': [
                    {'stat': 'crit_chance', 'base': 1.0, 'factor': 0.3},
                    {'stat': 'bleed_chance', 'base': 0.8, 'factor': 0.3},
                    {'stat': 'end', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A broad crescent blade on a long haft. Either it lands or it does not.',
            },
            {
                'slug': 'hunting-bow',
                'name': 'Hunting Bow',
                'item_type': 'weapon',
                'genre_tag': 'fantasy',
                'valid_slots': ['RANGED'],
                'is_two_handed': True,
                'scaling_base': 7.0,
                'scaling_factor': 3.0,
                'damage_spread': 4.0,
                'is_ranged': True,
                'takes_durability_loss': True,
                'durability_table': RANGED_DUR,
                'primary_stats': [
                    {'stat': 'dex', 'base': 2.0, 'factor': 0.8},
                    {'stat': 'per', 'base': 2.0, 'factor': 0.8},
                ],
                'secondary_stat_pool': [
                    {'stat': 'crit_chance', 'base': 0.8, 'factor': 0.3},
                    {'stat': 'per', 'base': 1.0, 'factor': 0.4},
                    {'stat': 'bleed_chance', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A shortbow of laminated yew. Quiet, patient, accurate.',
            },
            # Armor
            {
                'slug': 'leather-vest',
                'name': 'Leather Vest',
                'item_type': 'armor',
                'genre_tag': 'fantasy',
                'valid_slots': ['CHEST'],
                'scaling_base': 5.0,
                'scaling_factor': 2.0,
                'takes_durability_loss': True,
                'durability_table': ARMOR_DUR,
                'primary_stats': [{'stat': 'end', 'base': 3.0, 'factor': 1.0}],
                'secondary_stat_pool': [
                    {'stat': 'str', 'base': 1.0, 'factor': 0.3},
                    {'stat': 'dex', 'base': 1.0, 'factor': 0.3},
                    {'stat': 'physical_resist', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'Cured hide stitched with gut thread. Basic but proven.',
            },
            {
                'slug': 'ballistic-jacket',
                'name': 'Ballistic Jacket',
                'item_type': 'armor',
                'genre_tag': 'wasteland',
                'valid_slots': ['CHEST'],
                'scaling_base': 6.0,
                'scaling_factor': 2.2,
                'takes_durability_loss': True,
                'durability_table': ARMOR_DUR,
                'primary_stats': [
                    {'stat': 'end', 'base': 3.0, 'factor': 1.0},
                    {'stat': 'per', 'base': 1.0, 'factor': 0.4},
                ],
                'secondary_stat_pool': [
                    {'stat': 'physical_resist', 'base': 0.8, 'factor': 0.3},
                    {'stat': 'radiation_resist', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'dex', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'Layered composite panels over a worn canvas shell. Smells like smoke.',
            },
            {
                'slug': 'leather-cap',
                'name': 'Leather Cap',
                'item_type': 'armor',
                'genre_tag': 'fantasy',
                'valid_slots': ['HEAD'],
                'scaling_base': 4.0,
                'scaling_factor': 1.6,
                'takes_durability_loss': True,
                'durability_table': ARMOR_DUR,
                'primary_stats': [{'stat': 'end', 'base': 2.0, 'factor': 0.7}],
                'secondary_stat_pool': [
                    {'stat': 'per', 'base': 1.0, 'factor': 0.4},
                    {'stat': 'physical_resist', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'int', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A simple cap of hardened leather. Keeps the rain off and the ears open.',
            },
            {
                'slug': 'leather-shoulders',
                'name': 'Leather Shoulders',
                'item_type': 'armor',
                'genre_tag': 'fantasy',
                'valid_slots': ['SHOULDERS'],
                'scaling_base': 4.5,
                'scaling_factor': 1.8,
                'takes_durability_loss': True,
                'durability_table': ARMOR_DUR,
                'primary_stats': [{'stat': 'end', 'base': 2.0, 'factor': 0.7}],
                'secondary_stat_pool': [
                    {'stat': 'str', 'base': 1.0, 'factor': 0.3},
                    {'stat': 'physical_resist', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'end', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'Layered leather pads that sit square on the shoulders. Broken in, not broken.',
            },
            {
                'slug': 'leather-gloves',
                'name': 'Leather Gloves',
                'item_type': 'armor',
                'genre_tag': 'fantasy',
                'valid_slots': ['HANDS'],
                'scaling_base': 4.0,
                'scaling_factor': 1.6,
                'takes_durability_loss': True,
                'durability_table': ARMOR_DUR,
                'primary_stats': [{'stat': 'end', 'base': 2.0, 'factor': 0.7}],
                'secondary_stat_pool': [
                    {'stat': 'dex', 'base': 1.0, 'factor': 0.4},
                    {'stat': 'crit_chance', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'str', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'Supple leather gloves, palms worn smooth with use.',
            },
            {
                'slug': 'leather-belt',
                'name': 'Leather Belt',
                'item_type': 'armor',
                'genre_tag': 'fantasy',
                'valid_slots': ['WAIST'],
                'scaling_base': 4.0,
                'scaling_factor': 1.6,
                'takes_durability_loss': True,
                'durability_table': ARMOR_DUR,
                'primary_stats': [{'stat': 'end', 'base': 2.0, 'factor': 0.7}],
                'secondary_stat_pool': [
                    {'stat': 'str', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'end', 'base': 1.0, 'factor': 0.3},
                    {'stat': 'physical_resist', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A wide leather belt with a plain iron buckle. Everything hangs from it.',
            },
            {
                'slug': 'leather-leggings',
                'name': 'Leather Leggings',
                'item_type': 'armor',
                'genre_tag': 'fantasy',
                'valid_slots': ['LEGS'],
                'scaling_base': 5.0,
                'scaling_factor': 2.0,
                'takes_durability_loss': True,
                'durability_table': ARMOR_DUR,
                'primary_stats': [{'stat': 'end', 'base': 3.0, 'factor': 1.0}],
                'secondary_stat_pool': [
                    {'stat': 'end', 'base': 1.0, 'factor': 0.4},
                    {'stat': 'physical_resist', 'base': 0.8, 'factor': 0.3},
                    {'stat': 'str', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'Sturdy leather leggings, double-stitched at the knees.',
            },
            {
                'slug': 'leather-boots',
                'name': 'Leather Boots',
                'item_type': 'armor',
                'genre_tag': 'fantasy',
                'valid_slots': ['FEET'],
                'scaling_base': 4.5,
                'scaling_factor': 1.8,
                'takes_durability_loss': True,
                'durability_table': ARMOR_DUR,
                'primary_stats': [{'stat': 'end', 'base': 2.0, 'factor': 0.7}],
                'secondary_stat_pool': [
                    {'stat': 'dex', 'base': 1.0, 'factor': 0.4},
                    {'stat': 'end', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'physical_resist', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'Broken-in leather boots with hobnailed soles. Miles left in them.',
            },
            {
                'slug': 'wooden-shield',
                'name': 'Wooden Shield',
                'item_type': 'armor',
                'genre_tag': 'fantasy',
                'valid_slots': ['OFF_HAND'],
                'scaling_base': 5.0,
                'scaling_factor': 2.0,
                'takes_durability_loss': True,
                'durability_table': ARMOR_DUR,
                'primary_stats': [{'stat': 'end', 'base': 3.0, 'factor': 1.0}],
                'secondary_stat_pool': [
                    {'stat': 'physical_resist', 'base': 1.0, 'factor': 0.4},
                    {'stat': 'str', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'magic_resist', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A round shield of banded oak. Scarred, solid, dependable.',
            },
            # Bag
            {
                'slug': 'satchel',
                'name': 'Satchel',
                'item_type': 'bag',
                'genre_tag': 'fantasy',
                'valid_slots': ['BACK'],
                'scaling_base': 0.0,
                'scaling_factor': 0.0,
                'carry_bonus': 20,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [],
                'secondary_stat_pool': [],
                'description': 'A worn canvas satchel with a single shoulder strap. Fits more than it looks.',
            },
            # Consumables
            {
                'slug': 'healing-draught',
                'name': 'Healing Draught',
                'item_type': 'consumable',
                'genre_tag': 'fantasy',
                'valid_slots': [],
                'scaling_base': 0.0,
                'scaling_factor': 0.0,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [],
                'secondary_stat_pool': [],
                'effect': effects['healing-draught'],
                'description': 'A bitter herbal infusion in a stoppered vial. Works fast.',
            },
            {
                'slug': 'focus-tonic',
                'name': 'Focus Tonic',
                'item_type': 'consumable',
                'genre_tag': 'fantasy',
                'valid_slots': [],
                'scaling_base': 0.0,
                'scaling_factor': 0.0,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [],
                'secondary_stat_pool': [],
                'effect': effects['focus-tonic'],
                'description': 'Clear liquid with a sharp chemical smell. Narrows the world to a point.',
            },
            {
                'slug': 'repair-kit',
                'name': 'Repair Kit',
                'item_type': 'consumable',
                'genre_tag': 'wasteland',
                'valid_slots': [],
                'scaling_base': 0.0,
                'scaling_factor': 0.0,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [],
                'secondary_stat_pool': [],
                'effect': None,
                'description': 'Patches, adhesive, and a small wrench. Enough to hold things together.',
            },
            # Materials (vendor-sellable, no slots, stats, or durability)
            {
                'slug': 'animal-hide',
                'name': 'Animal Hide',
                'item_type': 'material',
                'genre_tag': 'fantasy',
                'valid_slots': [],
                'base_value': 6,
                'scaling_base': 0.0,
                'scaling_factor': 0.0,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [],
                'secondary_stat_pool': [],
                'description': 'A cured animal hide, rolled and tied. Worth a little to any trader.',
            },
            {
                'slug': 'insect-carapace',
                'name': 'Insect Carapace',
                'item_type': 'material',
                'genre_tag': 'fantasy',
                'valid_slots': [],
                'base_value': 8,
                'scaling_base': 0.0,
                'scaling_factor': 0.0,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [],
                'secondary_stat_pool': [],
                'description': 'A plate of chitin, dark and glossy. Traders buy them by the stack.',
            },
        ]

        # v18 copper accessories (tier-material items — no Mk suffix shown).
        # These are seeded with update_or_create so the absorbed legacy copper
        # ring is normalized to its D.5 shape on existing databases too.
        accessories = [
            {
                'slug': 'copper-ring-of-strength',
                'name': 'Copper Ring of Strength',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['RING'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'str', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'dex', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'end', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A plain copper band, faintly warm. The hand that wears it grips harder.',
            },
            {
                'slug': 'copper-ring-of-dexterity',
                'name': 'Copper Ring of Dexterity',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['RING'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'dex', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'str', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'per', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A plain copper band, faintly warm. The fingers that wear it fumble less.',
            },
            {
                'slug': 'copper-ring-of-endurance',
                'name': 'Copper Ring of Endurance',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['RING'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'end', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'str', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'wis', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A plain copper band, faintly warm. The miles weigh less on the legs.',
            },
            {
                'slug': 'copper-ring-of-intelligence',
                'name': 'Copper Ring of Intelligence',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['RING'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'int', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'wis', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'dex', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A plain copper band, faintly warm. Thoughts line up cleaner while it is worn.',
            },
            {
                'slug': 'copper-ring-of-wisdom',
                'name': 'Copper Ring of Wisdom',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['RING'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'wis', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'int', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'end', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A plain copper band, faintly warm. Second thoughts arrive before the first mistake.',
            },
            {
                'slug': 'copper-ring-of-perception',
                'name': 'Copper Ring of Perception',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['RING'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'per', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'dex', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'int', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A plain copper band, faintly warm. Small details stop slipping past.',
            },
            {
                'slug': 'copper-amulet-of-strength',
                'name': 'Copper Amulet of Strength',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['NECK'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'str', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'dex', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'end', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A copper pendant on a leather cord, faintly warm. Heavy loads sit lighter on the shoulders.',
            },
            {
                'slug': 'copper-amulet-of-dexterity',
                'name': 'Copper Amulet of Dexterity',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['NECK'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'dex', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'str', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'per', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A copper pendant on a leather cord, faintly warm. The feet find their footing without being asked.',
            },
            {
                'slug': 'copper-amulet-of-endurance',
                'name': 'Copper Amulet of Endurance',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['NECK'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'end', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'str', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'wis', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A copper pendant on a leather cord, faintly warm. Breath comes steadier on the long road.',
            },
            {
                'slug': 'copper-amulet-of-intelligence',
                'name': 'Copper Amulet of Intelligence',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['NECK'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'int', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'wis', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'dex', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A copper pendant on a leather cord, faintly warm. Hard problems unknot a little faster.',
            },
            {
                'slug': 'copper-amulet-of-wisdom',
                'name': 'Copper Amulet of Wisdom',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['NECK'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'wis', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'int', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'end', 'base': 0.5, 'factor': 0.2},
                ],
                'description': "A copper pendant on a leather cord, faintly warm. Old lessons surface just when they're needed.",
            },
            {
                'slug': 'copper-amulet-of-perception',
                'name': 'Copper Amulet of Perception',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['NECK'],
                'suppress_mk_suffix': True,
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'per', 'base': 2.0, 'factor': 0.8}],
                'secondary_stat_pool': [
                    {'stat': 'dex', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'int', 'base': 0.5, 'factor': 0.2},
                ],
                'description': 'A copper pendant on a leather cord, faintly warm. Sounds at the edge of hearing come clear.',
            },
        ]

        count_created = 0
        for data in items:
            slug = data.pop('slug')
            _, created = ItemDefinition.objects.get_or_create(slug=slug, defaults=data)
            if created:
                count_created += 1
            self.stdout.write(
                f'  ItemDefinition "{data["name"]}" {"created" if created else "exists"}.'
            )

        for data in accessories:
            slug = data.pop('slug')
            _, created = ItemDefinition.objects.update_or_create(slug=slug, defaults=data)
            if created:
                count_created += 1
            self.stdout.write(
                f'  ItemDefinition "{data["name"]}" {"created" if created else "updated"}.'
            )

        # v18 brief 4: base_value back-fill. get_or_create never updates
        # existing rows, so authored values are forced here on every run.
        base_values = {
            'iron-sword': 60,
            'combat-knife': 35,
            'pulse-pistol': 90,
            'apprentice-staff': 55,
            'leather-vest': 50,
            'ballistic-jacket': 55,
            'iron-mace': 65,
            'broadsword': 100,
            'battle-axe': 100,
            'hunting-bow': 80,
            'wooden-shield': 55,
            'leather-cap': 35,
            'leather-shoulders': 40,
            'leather-gloves': 35,
            'leather-belt': 35,
            'leather-leggings': 45,
            'leather-boots': 40,
            'animal-hide': 6,
            'insect-carapace': 8,
        }
        for stat in ('strength', 'dexterity', 'endurance',
                     'intelligence', 'wisdom', 'perception'):
            base_values[f'copper-ring-of-{stat}'] = 30
            base_values[f'copper-amulet-of-{stat}'] = 30

        for slug, value in base_values.items():
            ItemDefinition.objects.filter(slug=slug).update(base_value=value)
        ItemDefinition.objects.filter(item_type='consumable').update(base_value=12)
        ItemDefinition.objects.filter(item_type='bag').update(base_value=50)
        ItemDefinition.objects.exclude(slug__in=base_values).exclude(
            item_type__in=('consumable', 'bag'),
        ).update(base_value=25)
        self.stdout.write('  base_value back-fill applied to all ItemDefinitions.')

        self.stdout.write(self.style.SUCCESS(
            f'Item seed complete: {count_created} new ItemDefinitions created.'
        ))

    # ------------------------------------------------------------------
    # The Verdant Reach (Z01) — v18 brief 5: Vale & Flats
    # ------------------------------------------------------------------

    def _seed_verdant_zone(self):
        zone, created = Zone.objects.get_or_create(
            slug='the-verdant-reach',
            defaults={
                'name': 'The Verdant Reach',
                'genre_tone': 'Pastoral fantasy — green wilderness beyond the city',
                'danger_level': Zone.DANGER_BEGINNER,
                'is_pvp_zone': False,
                'is_scaled': False,
                'description': (
                    'Beyond the tree arch on Infinity City\'s ring street, the forest simply '
                    'begins: a green valley folded between high stone walls, an ancient stair, '
                    'and open grassland running toward the mountains. The first zone beyond '
                    'the city, and the gentlest — which is not the same as gentle.'
                ),
            },
        )
        self.stdout.write(f'Zone "{zone.name}" {"created" if created else "exists"}.')
        return zone

    def _seed_verdant_areas(self, zone):
        area_defs = [
            ('vale', 'Fernwater Vale',
             'A green valley folded between high stone walls, its floor stitched with '
             'ferns and threaded by a cold, quick river. Mist gathers in the low places. '
             'Everything here grows.'),
            ('flats', 'The Sagewind Flats',
             'Open grassland under an enormous sky, silver-green and restless. The wind '
             'never entirely stops, combing the sage in long slow waves toward the mountains.'),
            ('hollow', "Spinner's Hollow",
             'A single pocket of dark beneath the valley wall, hung wall to wall with old silk.'),
            ('cleft', 'The Silken Cleft',
             'A crack in the valley wall that goes back further than it should, silk-strung '
             'and softly rustling.'),
            ('sink', 'The Whistling Sink',
             'A sunken cave beneath the plains where wind pours down through the mouth above '
             'and never finds its way out, whistling one thin endless note.'),
            ('pit', 'The Drone Pit',
             'A pit hive under the grass, its galleries carved smooth, the air thick with a '
             'hum felt more in the teeth than the ears.'),
            ('ridge', 'The Viridian Ridge',
             'Mountains that refuse to be grey: green climbs them almost to their crowns, '
             'pine and moss and stubborn grass on switchback bones of stone. The wind up '
             'here has edges. So does everything else.'),
            ('undercrag', 'The Undercrag',
             'A delve beneath the first shoulder of the Ridge, descending in webbed '
             'galleries where the daylight has never been introduced.'),
            ('chitterdeep', 'Chitterdeep',
             'A deep of falling passages under the high Ridge, named for the sound that '
             'never entirely stops.'),
            ('hollowcrown', 'Hollowcrown',
             'The hollow inside the summit itself, climbing in veined galleries toward a '
             'crown of impossible green.'),
        ]
        areas = {}
        for key, name, description in area_defs:
            area, _ = Area.objects.get_or_create(
                zone=zone,
                slug=slugify(name),
                defaults={'name': name, 'area_description': description},
            )
            areas[key] = area
        self.stdout.write('Verdant Reach areas seeded: ' + ', '.join(a.name for a in areas.values()) + '.')
        return areas

    def _vr_room(self, zone, key, x, y, z, name, brief, description,
                 area, safe=False, indoors=False, no_exit=None):
        msgs = no_exit or {}
        room, _ = Room.objects.update_or_create(
            zone=zone,
            coord_x=x, coord_y=y, coord_z=z,
            defaults={
                'name': name,
                'brief_description': brief,
                'description': description,
                'area': area,
                'flag_safe': safe,
                'flag_indoors': indoors,
                'no_exit_north_msg': msgs.get('north', ''),
                'no_exit_south_msg': msgs.get('south', ''),
                'no_exit_east_msg': msgs.get('east', ''),
                'no_exit_west_msg': msgs.get('west', ''),
                'no_exit_up_msg': msgs.get('up', ''),
                'no_exit_down_msg': msgs.get('down', ''),
            },
        )
        self.rooms[key] = room
        return room

    def _seed_verdant_rooms_vale(self, zone, areas):
        vale = areas['vale']

        self._vr_room(
            zone, 'vr-v01', 0, 0, 0,
            'The Tree Arch',
            'Two ancient trees grow into a living arch over a green path.',
            'Two enormous trees have grown into each other overhead, their intergrown branches '
            'forming an arch that no one built and no one could. Beyond it a short path runs north '
            'into green shade, and the air changes as you pass beneath — cooler, older, smelling of '
            'ferns and wet stone. Behind you, the city. Ahead, the forest simply begins.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v02', 0, 1, 0,
            'The Green Path',
            'A soft path runs through dense ferns and close green shade.',
            'Ferns crowd the path on both sides, brushing your arms as you pass, and the canopy '
            'knits itself together overhead until the light comes through green. Somewhere ahead '
            'there is the faint sound of moving water. The path is soft underfoot and clearly '
            'walked, though not often, and not recently.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v03', 0, 2, 0,
            'The Narrowing Way',
            'The green thins as stone shoulders through the soil.',
            'The ferns begin to give ground. Grey stone shoulders up through the soil in ribs and '
            'knuckles, and the path threads between them, narrowing as it goes. The sound of water '
            'is louder now — quick water, cold water, water in a hurry. Mist drifts through the '
            'gaps in the rock ahead.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v04', 0, 3, 0,
            'The Rocky Descent',
            'The path drops between wet boulders toward rushing water.',
            'The path tips downward and picks its way between boulders slick with spray. The mist '
            'is thicker here, beading on the stone, and the rush of water fills the gaps between '
            'your own footsteps. To the east, a game trail worn by something heavy pushes through '
            'a screen of brush.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v05', 0, 4, 0,
            'The Riverbank',
            'A cold, quick river runs through a wall of standing fog.',
            'The river runs fast and shallow here over pale stones, cold enough to ache. On the '
            'far bank a wall of fog stands like a held breath, hiding whatever lies beyond — the '
            'world simply stops at the waterline and goes white. Stepping stones cross the '
            'current, worn smooth by feet that came before yours.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v06', 1, 3, 0,
            'Bear Hollow',
            'A trampled hollow smelling of musk and torn earth.',
            'The game trail opens into a hollow of flattened grass and clawed-up earth. Half-eaten '
            'fish lie on the rocks by a backwater pool, and the musk in the air says the owners '
            'are not far. The brush hangs in ragged tears where something large has shouldered '
            'through, again and again, for years.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v07', 0, 5, 0,
            'Fordwatch',
            'A green sphere drifts above the crossing where the fog gives way.',
            'The moment you cross the river the fog lifts — all at once, like a curtain taken by '
            'the wind — and the whole of Fernwater Vale spreads out below the light: green folded '
            'on green, the river threading it, cliffs rising pale on either side. A small sphere '
            'of soft green light drifts and bobs above the crossing, circling nothing in '
            'particular, delighted by the water. Around it, a trodden clearing has grown up the '
            "way markets grow: a mender's bench, a trader's blanket, the small industry of people "
            'who noticed that travelers keep appearing here.',
            area=vale, safe=True,
        )
        self._vr_room(
            zone, 'vr-v08', 0, 6, 0,
            'The Valley Floor',
            'Open valley floor, green and generous under high pale cliffs.',
            'The valley opens its hand. Grass and fern run in every direction, broken by stands '
            'of white-barked trees, and the cliffs stand back on either side like walls of a room '
            'too large to feel enclosed. The river glitters off to the west. Otters are usually '
            'about, doing whatever otters have decided is urgent today.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v09', 0, 7, 0,
            'The Fern Meadow',
            'Ferns grow waist-high in a broad, humming meadow.',
            'Ferns rise waist-high across the whole meadow, moving in slow waves when the wind '
            'comes down the valley. Insects hum in the green. A side path, narrower and damper, '
            "bends west toward the river's edge; the main way keeps north, a parting in the ferns.",
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v10', 0, 8, 0,
            'The Cliffside Path',
            'The path runs beneath pale cliffs where lean shapes move.',
            'The path swings near the eastern cliffs, close enough to feel their stored cold. '
            'High on the rock, lean tawny shapes move from ledge to ledge with insulting ease — '
            'mountain lions, working the wall for whatever lives in it. A goat track climbs east '
            'toward their ledges, if you have opinions about lions.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v11', 0, 9, 0,
            'Reedmere Approach',
            'Woodsmoke and reed-smell drift from the west.',
            'Woodsmoke reaches you before anything else — thin, domestic, unhurried — then the '
            'smell of reeds and wet rope. Through the trees to the west, low roofs gather at the '
            "water's edge, and someone is singing badly and without shame. The main path continues "
            'north past the turnoff.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v12', 0, 10, 0,
            'The Old Orchard',
            'Feral fruit trees stand in rows nobody tends anymore.',
            'Fruit trees stand in rows that have long forgotten they were rows, branches tangled, '
            'fruit small and fierce. Windfalls rot sweetly in the grass, and the bears know it — '
            'the grass is pressed flat in patches, and claw marks score the bark shoulder-high. '
            'A gap in the eastern trees marks a well-used animal path.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v13', 0, 11, 0,
            'The Bramble Cut',
            'Brambles wall the path; eastward, something glints like thread.',
            'Brambles rise on both sides in a hedge of hooks, funneling the path. To the east, '
            'where a dry gully cuts back toward the cliff base, the morning light catches on long '
            'pale strands strung between the thorns — too regular for cobweb, too much of it to '
            'be anything good. The main path pushes north.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v14', 0, 12, 0,
            'The Riverfork',
            'The river bends close, braiding around gravel bars.',
            'The river comes back to meet the path, splitting around gravel bars into silver '
            'braids. The shallows to the west boil with fish at the right hour, and the bank is '
            'printed over and over with broad, five-clawed tracks. The bears fish here. It is '
            'worth knowing before you go down to the water.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v15', 0, 13, 0,
            'The Cleft Wall',
            'The valley wall rises sheer, seamed by one dark crack.',
            'The eastern wall stands close and sheer here, pale stone going up until your neck '
            'complains. One crack seams it from the ground to twice your height — narrow, dark, '
            'and breathing out cool air that smells faintly of dust and old silk. The path keeps '
            "north along the wall's foot.",
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v16', 0, 14, 0,
            'The Vanished Road',
            'The path dead-ends at the wall — but steps are carved in the stone.',
            'The path walks itself straight into the valley wall and stops. A dead end — until '
            'you look up. Steps are carved into the living rock, very old, worn hollow in their '
            'centers, climbing in switchbacks toward the rim far above. Below them, along the '
            'river, you can make out the ghost of an easier road: a broad shelf that once ran up '
            "the valley's end, long since eaten away by the water. The steps are the way now. The "
            'steps have been the way for a very long time.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v17', -1, 7, 0,
            'Otter Bend',
            'A slow backwater where otters conduct important business.',
            'The river slows into a backwater pool here, glass-still at the edges, and the otters '
            'have claimed it utterly. They chase, dive, surface with pebbles, drop the pebbles, '
            'and look personally betrayed. A mud slide down the far bank is polished to a shine '
            'from use. It is very hard to leave.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v18', 1, 8, 0,
            'The Talon Ledge',
            'A climbing track ends on ledges that belong to the lions.',
            'The goat track ends on a series of broad ledges partway up the cliff, littered with '
            'clean-picked bones and drifted fur. The view down the valley is glorious, and it '
            'belongs to the mountain lions, who watch your arrival with the flat patience of '
            'landlords. Nothing here is hidden. That is rather the point.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v19', 1, 10, 0,
            'Boar Wallow',
            "Churned mud and shredded bark — the boars' own ground.",
            'The animal path ends in a wallow of churned black mud ringed by trees with their '
            'bark shredded to shoulder height. The smell is rich and organic and entirely '
            'unapologetic. Wild boars use this place hard, and the deep, fresh prints say they '
            'have not gone far, and the tusked furrows in the ground say they do not startle.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v20', 1, 11, 0,
            'The Webbed Gully',
            'A dry gully strung with silk, ending at a dark hollow.',
            'The gully runs dry and quiet toward the cliff base, and the silk thickens as you go '
            "— strands, then sheets, then architecture. At the gully's end a hollow opens beneath "
            'a fallen slab, hung inside with pale drapery that stirs in air you cannot feel. '
            'Something in there is patient.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v21', -1, 12, 0,
            'The Shallows',
            'Bears fish the silver shallows, absorbed and enormous.',
            'The shallows spread wide and bright over gravel, and the bears are at work in them — '
            'enormous, absorbed, swatting fish onto the bank with a economy that took generations '
            'to learn. An otter loiters downstream of the whole operation, cleaning up. The bears '
            "ignore you with magnificent completeness, right up until they don't.",
            area=vale,
        )
        self._vr_room(
            zone, 'vr-v22', 1, 13, 0,
            'The Cleft Mouth',
            'Cool air and silk strands breathe from a crack in the wall.',
            'Up close the crack is wider than it looked — a person could walk in without turning '
            'sideways, which someone or something clearly wants. Silk strands cross the opening '
            'at intervals, snapped and rehung, snapped and rehung. The air that moves out of the '
            'dark is cool and carries a dry rustling, like paper considering something.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-rm1', -1, 9, 0,
            'Reedmere Shore',
            'A reed-fringed shore of racks, nets, and easy voices.',
            'Reedmere begins at the waterline, the way it was always going to: drying racks hung '
            'with split fish, nets draped like laundry, coracles turned turtle on the mud. The '
            'reeds stand taller than the people, and the people like it that way. Voices carry '
            'easily here and nobody minds.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-rm2', -1, 10, 0,
            'Reedmere Huts',
            'Low reed-thatched huts around a shared cookfire.',
            'The huts are low and round, thatched in reed, each with its door facing the water '
            'out of custom older than reasons. A shared cookfire smolders in the middle ground, '
            "ringed by stones and gossip. Children's toys — carved fish, mostly — lie where they "
            'were dropped, which is everywhere.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-rm3', -2, 9, 0,
            'Reedmere Jetty',
            'A crooked jetty where the fishers work and argue kindly.',
            'The jetty leans out over the water at an angle that has been about to be fixed for '
            'twenty years. Fishers work along its length, mending nets with wet fingers and '
            "arguing kindly about weather that hasn't happened yet. The planks are silver with "
            'age and slick with scales, and the whole structure creaks in a way everyone here '
            'has stopped hearing.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-s1', 0, 15, 1,
            'The First Steps',
            'Ancient carved steps begin their climb up the valley wall.',
            'The steps are broader than they looked from below, cut deep into the rock by hands '
            'that measured for feet larger than yours, or more numerous. Each tread is worn into '
            'a shallow bowl. The valley floor begins to sink away behind you, and the climb '
            'settles into your legs like a fact.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-s2', 0, 16, 1,
            'The Low Vista',
            'The steps pause at a ledge; the vale spreads out below.',
            'The steps pause at a natural ledge, and the vale rewards you for turning around: the '
            "river a bright thread, Reedmere's smoke rising straight in the still air, the whole "
            'green length of the valley laid out like something you own now, a little, by having '
            'walked it. Then you look up at how much stair remains, and the feeling complicates.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-s3', 0, 17, 2,
            'The Long Climb',
            'Switchbacks, wind, and the honest work of climbing.',
            'The steps switch back on themselves and climb without commentary. The wind finds you '
            'here, coming down off the plains above with a smell of grass and distance. The valley '
            'has become a map of itself. Your legs have opinions. The steps do not care; the steps '
            'have outlasted better legs than yours.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-s4', 0, 18, 3,
            'The High Vista',
            'A high ledge; below, the old road the river ate is plain.',
            "From this height the story of the valley's end is laid bare. The old road is "
            'unmistakable now — a broad, gentle shelf that once climbed the valley\'s head in a '
            'single easy sweep, sheared away in mid-stride where the river undercut it, '
            'generations or centuries ago. Somebody built that road. The water unbuilt it. The '
            'steps you stand on are the apology.',
            area=vale,
        )
        self._vr_room(
            zone, 'vr-s5', 0, 19, 4,
            'The Rim',
            'The last steps rise into grass and an enormous sky.',
            'The final steps rise through a notch in the rim and the world changes registers: '
            'grass at eye level, then grass to the horizon, and above it a sky suddenly twice its '
            'former size. The wind here is constant and busy. Behind and below, the whole vale '
            'you climbed out of. Ahead, the flats, silver-green and moving.',
            area=vale,
        )
        self.stdout.write('Verdant Reach: Fernwater Vale rooms seeded (30).')

    def _seed_verdant_rooms_flats(self, zone, areas):
        flats = areas['flats']

        self._vr_room(
            zone, 'vr-f01', 0, 20, 4,
            'Stairhead',
            'A green sphere rides the wind above a trodden waystation.',
            'Where the stair meets the plain, a clearing has been worn into the grass by arriving '
            'feet. A small sphere of green light rides the wind here — climbing it, dropping, '
            'wobbling upward again, entirely pleased with itself. In its orbit the usual industry '
            "has gathered: a mender's kit spread on a hide, a trader's goods weighted down against "
            'the wind, and the particular calm of a place where nothing bad has ever managed to '
            'happen.',
            area=flats, safe=True,
        )
        self._vr_room(
            zone, 'vr-f02', 0, 21, 4,
            'The Grass Sea',
            'Silver-green grass runs in waves to the horizon.',
            'The grass runs unbroken to the horizon in every direction that matters, moving in '
            'long slow swells when the wind leans on it. Deer stand in it to their shoulders, '
            'visible only as heads that lift, consider you, and return to the grass. The '
            'mountains are a blue suggestion to the north. The sky is most of the world.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f03', 0, 22, 4,
            'The Wind Rows',
            'The wind combs the sage into long parallel rows.',
            'Here the wind has been at work so long it has combed the sage into rows, all leaning '
            'the same way, silver side up. Walking across the grain feels faintly like an '
            'argument. Small bursts of movement erupt and vanish in the grass to the west — '
            'rabbits, running their endless errands.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f04', 0, 23, 4,
            'The Tall Grass Crossing',
            'Grass overhead-high, threaded by one confident path.',
            'The grass stands taller than you here, and the path through it is a green tunnel '
            'roofed in sky. Heavy bodies move somewhere off to the east — unhurried, in numbers, '
            'accompanied by the sound of enormous patient chewing. The path has clearly '
            'negotiated its route with them and won only partially.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f05', 0, 24, 4,
            'Windhome Approach',
            'Painted hide tents rise west, smoke leaning with the wind.',
            'Tents rise out of the grass to the west — tall cones of stitched hide, painted in '
            'ochre and white with patterns that repeat like a language you almost know. Their '
            'smoke leans with the wind, all in agreement. Between here and there, drying racks '
            'and a horse-less travois say the people of this place carry their world with them '
            'and set it down gently.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f06', 0, 25, 4,
            'The Whistling Rise',
            'A low rise where a thin whistle rides under the wind.',
            'The ground swells into a long low rise, and somewhere beneath the ordinary voice of '
            'the wind there is another sound — thinner, steadier, a single held note that does '
            'not stop for breath. It comes from the east, from the ground itself. The grass grows '
            'thinner in that direction, as if it too is listening.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f07', 0, 26, 4,
            'The Dust Trail',
            'A dusty stretch printed over with small, busy tracks.',
            'The grass gives way to a stretch of bare, dusty ground printed all over with small '
            'tracks — hundreds of them, coming and going with municipal purpose. To the west, '
            'the prairie dog town announces itself with a skyline of dirt mounds and a sentry\'s '
            'sharp whistle, followed by the sound of an entire civilization ducking.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f08', 0, 27, 4,
            'The Low Swale',
            'A dip in the plain where a hum rises through your boots.',
            'The land dips into a shallow swale, and in the bottom of it you feel the sound '
            'before you hear it: a low, continuous hum rising through the soles of your boots, '
            'patient as machinery. Eastward the grass fails entirely around a bare depression, '
            'and the hum is stronger there, and the air above it shivers very slightly.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f09', 0, 28, 4,
            'The Herd Path',
            'A broad trampled avenue cut by generations of buffalo.',
            'The buffalo have been using this route longer than anything else out here has been '
            'doing anything: a broad avenue trampled to hardpan, curving with the land, dunged '
            'and hoof-printed and utterly authoritative. Deer use the margins. The path north '
            'follows it because arguing with it would be absurd.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f16', 0, 29, 4,
            'The Open Sky',
            'The plain runs out its last miles; the mountains have arrived.',
            'The mountains are no longer a suggestion. They stand up out of the plain to the '
            'north in folds of green-going-grey, near enough now to have texture, weather, '
            'intent. The grass runs on toward them, thinning. Behind you, the flats; ahead, the '
            'whole vertical remainder of the world.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f18', 0, 30, 4,
            'The Boulder Field',
            "Grassy field littered with boulders — the mountains' first word.",
            'Boulders lie scattered across the grass in their hundreds — some hip-high, some the '
            'size of huts, all of them travelers, carried here and set down by whatever the '
            'mountains were doing before anyone was watching. The grass grows up around them '
            'respectfully. There is no line on the ground where the plains end and the mountains '
            'begin, but standing here, you know you have crossed it.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f10', -1, 22, 4,
            'The Rabbit Warrens',
            'Burrow-pocked ground alive with sprinting rabbits.',
            'The ground here is pocked with burrow mouths, and the grass between them is mown '
            'short by ten thousand small breakfasts. Rabbits materialize, sprint nowhere in '
            'particular at maximum sincerity, and vanish. Underfoot, the whole meadow is hollow '
            'with their city.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f11', 1, 23, 4,
            'The Grazing Grounds',
            'The buffalo herd grazes here, vast and unbothered.',
            'The herd is here — dark, hill-shaped, steam rising off their backs in the cool air. '
            'Buffalo graze the way mountains would graze, with no interest in your schedule and '
            'a mass that renders opinion irrelevant. Calves shelter in the middle of all that '
            'muscle. The grass is cropped in a wide fair circle around them.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f12', 1, 25, 4,
            'The Sink Mouth',
            'A whistling hole opens straight down into the dark.',
            'The rise ends at a hole in the world. It opens straight down — a sink of raw earth '
            'and root-ends, wide as a hut, breathing wind. The whistle lives here: air pouring '
            'down over the lip and finding, somewhere below, an instrument to play. Handholds '
            'and a slumped ramp of fallen soil make the descent possible. That is not the same '
            'as advisable.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f13', -1, 26, 4,
            'Prairie Dog Town',
            'A metropolis of dirt mounds and outraged sentries.',
            'Dozens of dirt mounds rise in loose streets, each crowned with a sentry standing '
            'bolt upright at full civic alarm. Your every movement is narrated in whistles, '
            'relayed, embellished, and denounced. The ground hums with small departures. It is, '
            'frankly, adorable, and they would bite you to the bone.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f14', 1, 27, 4,
            'The Drone Mouth',
            'A bare pit exhales a hum and a smell of wax and acid.',
            'The depression ends in a pit going down — smoother-edged than the sink, its walls '
            'worked and re-worked into something disquietingly like craft. The hum pours up out '
            'of it along with a smell of wax, earth, and faint acid. Now and then the darkness '
            'below flickers, as of wings catching what little light falls in.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f15', -1, 28, 4,
            'The Deer Run',
            'A sheltered draw where the deer gather in numbers.',
            'A shallow draw runs off the herd path, sheltered from the wind, and the deer favor '
            'it in numbers — heads down, ears up, the whole group wired into one shared nervous '
            'system. They allow your presence at a fixed radius, recalculated continuously. The '
            'grass here is good and they know the exits.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-f17', 1, 29, 4,
            'The Buffalo Wallow',
            'A dust bowl where the buffalo roll and rumble.',
            'Generations of rolling buffalo have worn a bowl of bare dust into the plain, and on '
            'most days some of them are at it — down on their backs, legs in the air, groaning '
            'with an enjoyment so total it borders on philosophy. The dust hangs golden. '
            'Approaching a buffalo mid-wallow is a decision with consequences.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-w1', -1, 24, 4,
            'Windhome Circle',
            'The fire circle at the heart of the painted tents.',
            'The tents stand in a ring around a central fire circle, and the life of Windhome '
            'moves through it all day: hides being worked soft, a haunch turning, children '
            'orbiting, someone mending, someone laughing, an elder saying something that makes '
            'the laughing worse. The painted patterns on the tents catch the light and mean '
            'things. You are seen, weighed, and — for now — welcome.',
            area=flats,
        )
        self._vr_room(
            zone, 'vr-w2', -1, 25, 4,
            'Windhome Tents',
            'Among the tents: bows being worked, arrows fletched.',
            'Between the tents the working life of the camp goes on out of the wind: bows being '
            'shaped and strung, arrows fletched with plains-bird feathers, hide scraped thin '
            'enough to glow. The hunters here move with the economy of people whose tools are '
            'also their survival. Everything is packable in an hour. Nothing looks temporary.',
            area=flats,
        )
        self.stdout.write('Verdant Reach: Sagewind Flats rooms seeded (20).')

    def _seed_verdant_rooms_caves(self, zone, areas):
        hollow = areas['hollow']
        cleft = areas['cleft']
        sink = areas['sink']
        pit = areas['pit']

        # --- Spinner's Hollow (1 room) ---------------------------------------
        self._vr_room(
            zone, 'vr-c1a', 2, 11, 0,
            "Spinner's Hollow",
            'A silk-hung pocket of dark with one patient occupant.',
            'The hollow is one small room of stone hung wall to wall in old silk, layered pale '
            'on pale, soft-walled like the inside of a cocoon. Husks of small things hang in it '
            'at various altitudes. In the middle of all that patience, a spider the size of a '
            'dog holds very still, in the way that is the opposite of stillness.',
            area=hollow, indoors=True,
        )

        # --- The Silken Cleft (4 rooms) --------------------------------------
        self._vr_room(
            zone, 'vr-c2a', 2, 13, 0,
            'The Entry Cleft',
            'A narrow stone throat strung with tripline silk.',
            'The cleft runs back into the wall as a narrow throat of stone, and the silk begins '
            'immediately — single strands at ankle and throat height, taut, deliberate. The '
            "rustling is clearer in here, coming from everywhere the light isn't. Daylight gives "
            'up a few paces in.',
            area=cleft, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c2b', 2, 14, 0,
            'The Silk Gallery',
            'A widened gallery curtained in sheets of webbing.',
            'The cleft widens into a gallery curtained floor to ceiling in sheets of webbing, '
            'some fresh and bright, some grey and sagging with dust and use. Wrapped shapes hang '
            'in the older sheets, all sizes. Things move behind the curtains — quick, '
            'many-legged, and aware of you to a fine degree of precision.',
            area=cleft, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c2c', 2, 15, 0,
            'The Choke',
            'The passage narrows to a silk-funnel choke point.',
            'The passage narrows until your shoulders brush silk on both sides, and it dawns on '
            'you that the narrowing is not geology — it is a funnel, woven on purpose, and you '
            'are walking down it in the approved direction. The air is close and smells of dust '
            'and vinegar. Something long and low flows across the floor at the edge of sight.',
            area=cleft, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c2d', 2, 16, 0,
            "The Matron's Larder",
            'A silk-vaulted chamber; above, a shape guards a wrapped bundle.',
            'The cleft ends in a vaulted chamber upholstered entirely in silk, generations deep. '
            'Wrapped bundles hang in ordered rows — a larder, kept by something with standards. '
            "In the vault's crown, half-lost in her own architecture, the Matron waits: pale, "
            'vast, and holding one bundle apart from all the others, close, the way anything '
            'hoards the thing it values most.',
            area=cleft, indoors=True,
        )

        # --- The Whistling Sink (6 rooms) ------------------------------------
        self._vr_room(
            zone, 'vr-c3a', 1, 25, 3,
            'The Fallen Light',
            'A shaft of daylight falls into a wind-scoured chamber.',
            'You come down the slumped earth ramp into a chamber lit by one shaft of falling '
            'daylight, dust turning in it like slow weather. The whistle is loud here — the '
            'mouth above catching the wind and playing it down the throat of the cave. Around '
            'the light, the dark starts immediately, and the walls glisten with moss where the '
            'light has taught it to grow.',
            area=sink, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c3b', 1, 26, 3,
            'The Whistle Throat',
            'A fluted passage where the wind plays one endless note.',
            'The passage narrows and flutes, and this is the instrument: wind forced down from '
            'above hums through the stone in one thin endless note that you now get to live '
            'inside. Long-bodied shapes pour along the walls when your light moves — too many '
            'legs, moving like spilled water. The note never breathes. You will hear it tonight, '
            'wherever you sleep.',
            area=sink, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c3c', 1, 27, 3,
            'The Wind Gallery',
            'A broad gallery scoured smooth; a bone-strewn niche east.',
            'The cave opens into a gallery scoured smooth by ages of moving air, ribbed like the '
            'roof of a mouth. Lichen maps the walls in grey continents. To the east a niche in '
            'the rock is drifted with small bones, sorted by something, or by wind, and it '
            'matters which. Overhead, wings tick against stone.',
            area=sink, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c3d', 2, 27, 3,
            'The Bone Niche',
            'A low niche drifted deep with sorted small bones.',
            'The niche is low enough to stoop in and drifted ankle-deep in small bones — rabbit, '
            'prairie dog, bird — pale and clean and unsettlingly sorted, long bones with long '
            'bones, skulls with skulls. The silk here is sparse but recent. Whatever does the '
            'sorting eats first and organizes after, and is not far.',
            area=sink, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c3e', 1, 28, 3,
            'The Deep Hum',
            'The whistle deepens; the walls carry a second, living note.',
            'Deeper in, the whistle drops in pitch and gains company — under it now there is a '
            'second sound, irregular, made of many small dry movements, and it is not the wind. '
            'The moss fails here for lack of light and the walls go bare and cold. Something big '
            'has polished a track along the floor with the underside of its body.',
            area=sink, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c3f', 1, 29, 3,
            "The Whistler's Hollow",
            "The note's source: a hollow ruled by one immense centipede.",
            'The cave ends in a rounded hollow where the note finally resolves — the wind '
            'spending itself against a wall of fluted stone, one held tone, forever. Coiled '
            "through the flutes, segment on glossy segment, is the hollow's owner: a centipede "
            'of impossible length, antennae combing the air. High on the wall, wedged where the '
            'wind cannot take it, a hide-wrapped cache hangs from a plaited grass rope, out of '
            'reach of everything but gravity, patience, or violence.',
            area=sink, indoors=True,
        )

        # --- The Drone Pit (8 rooms) ------------------------------------------
        self._vr_room(
            zone, 'vr-c4a', 3, 27, 3,
            'The Drop',
            "The pit's floor: worked walls, wax-smell, and the hum.",
            'The climb down ends on a floor of packed, level earth — level on purpose. The walls '
            'of the pit have been worked smooth in overlapping scallops, and the hum is no '
            'longer a sound so much as a medium you are now inside. The wax-and-acid smell is '
            'stronger. Passages lead north into the hive proper, and the daylight above already '
            'looks like a rumor.',
            area=pit, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c4b', 3, 28, 3,
            'The Buzzing Dark',
            'Full dark; wings stir the air from unseen angles.',
            'The last daylight fails and the hive takes over the job of describing itself: the '
            'hum, the wax-smell, and the wings — starting, stopping, moving the air against your '
            'face from angles you cannot predict. When wings pass close the hum bends around '
            'them. Your light catches carapaces the color of oiled iron before they slide from '
            'the beam.',
            area=pit, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c4c', 3, 29, 3,
            'The Honeycomb Walls',
            'Walls worked into cells, some sealed, some watching.',
            'The walls here are worked into cells — hexagonal, palm-wide, hundreds of them — '
            'some sealed with wax caps, some open and dark, and a few occupied by heads that '
            'track your light. The centipedes have moved in along the seams, using the beetle '
            'city the way rats use a human one. It is architecture. Something builds down here, '
            'and you are inside its intentions.',
            area=pit, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c4d', 4, 29, 3,
            'The Husk Pile',
            'A midden of shed carapaces heaped to the ceiling.',
            "A dead-end chamber serves as the hive's midden: shed carapaces heaped nearly to the "
            'ceiling, translucent amber ghosts of every size the builders have ever been, '
            "including — you measure it twice — sizes larger than the ones you've seen. Spiders "
            "work the pile's edges. The crunch underfoot is unavoidable and announces you "
            'generously.',
            area=pit, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c4e', 3, 30, 3,
            'The Droneway',
            'A flight corridor; wings pass close and often. A shaft drops away.',
            'The passage straightens and widens into what is unmistakably a flight corridor — '
            'the beetles use it at speed, wings snapping open with a sound like sails, passing '
            'close enough to move your hair. Staying to the wall is wisdom. Midway along, a '
            'worked shaft drops away into deeper dark, its edges polished by traffic.',
            area=pit, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c4f', 3, 30, 2,
            'The Larder Shaft',
            'A deep cell where provisions — all kinds — are stored.',
            'The shaft opens into a single deep cell, wax-capped floor to ceiling, and the smell '
            'here is complicated: honey, carrion, earth, acid. This is the larder. Some caps '
            'have been chewed open from outside — the centipedes raiding downward — and the '
            'beetles have opinions about that, expressed at volume, in the dark, often.',
            area=pit, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c4g', 3, 31, 3,
            'The Low Chamber',
            'The hum gathers weight; the ceiling presses down.',
            'The ceiling steps down until the hum has nowhere to go and simply becomes pressure. '
            'Beetles stand along the walls here in ranks, wings closed, still in a way that '
            'reads less like rest and more like posting. Beyond them the passage bends once and '
            'glows faintly with the phosphor of disturbed fungus. Whatever the hive protects, it '
            'is past this room.',
            area=pit, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c4h', 3, 32, 3,
            "The Dronemother's Vault",
            "The hive's heart: the vast Dronemother before a sealed wall.",
            'The hive ends in a vault whose walls are one continuous sweep of worked wax, and at '
            'its heart, wings folded like furled banners, stands the Dronemother — beetle beyond '
            'argument, plated in iron-dark chitin, the hum deepening around her to a register '
            'you feel in your sternum. Behind her the wall bulges with a sealed hollow, waxed '
            'over and over, generations thick, in the way of things too valuable to look at. She '
            'is between you and it. She intends to remain so.',
            area=pit, indoors=True,
        )
        self.stdout.write('Verdant Reach: cave rooms seeded (19).')

    def _seed_ridge_rooms_leg1(self, zone, areas):
        ridge = areas['ridge']

        self._vr_room(
            zone, 'vr-c01', 0, 31, 4,
            'Cragfoot',
            "A green sphere warms itself by a fire at the mountains' feet.",
            'Where the boulders give way to the first true slope, a waystation has grown up '
            "in the lee of a stone the size of a house: a fire ring, a mender's bench, trade "
            'goods under oilcloth. A small sphere of green light hangs near the flames, '
            'swaying gently, to all appearances warming itself — which should not work, and '
            'works. Above, the switchbacks begin their long argument with the mountain.',
            area=ridge, safe=True,
        )
        self._vr_room(
            zone, 'vr-m01', 0, 32, 5,
            'The First Switchback',
            'The path folds back on itself and begins to climb in earnest.',
            'The path takes the slope the only way paths can: sideways, folding back on '
            'itself, gaining height by patience. Pine and juniper crowd the bends, and the '
            'plains behind you begin their slow transformation into scenery.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m02', 0, 33, 5,
            'The Goat Trail',
            'Goat sign everywhere; a side track climbs to eastern ledges.',
            'Droppings, tufted hair on the thorn bushes, and hoofprints stamped into '
            'impossible angles of rock — the goats own this stretch and file no paperwork. '
            'A side track climbs east toward ledges where several of them stand at slopes '
            'that insult gravity.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m03', 0, 34, 5,
            'The Shale Turn',
            'Loose shale slides underfoot at a tight bend.',
            'The path turns tight across a fan of loose shale that moves underfoot with a '
            'sound like breaking crockery. Every step is a small negotiation. Below the '
            'turn, the shale runs out into empty air and takes a long time to land.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m04', 0, 35, 5,
            'The Pine Shelf',
            'A level shelf of wind-bent pines, loud with squirrels.',
            'The mountain relents into a level shelf of pines, every one of them bent the '
            "same direction by the wind's long opinion. Squirrels run the branches overhead, "
            'furious about everything, particularly you. A gap in the trees opens west.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m05', 0, 36, 6,
            'The Second Switchback',
            'The path folds again; goats watch from above with contempt.',
            'The path folds back again and gains a hard stretch of height. Goats stand on '
            'the rocks above the bend, chewing, watching your labor with the specific '
            'contempt of creatures to whom slopes are horizontal.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m06', 0, 37, 6,
            'Stonestep Approach',
            'Terraced walls and woodsmoke — a village holds the slope.',
            'Dry-stone terraces step up the slope to the east, holding soil and a village '
            "against the mountain's preference for neither. Woodsmoke and the clink of tools "
            'drift down. The people of Stonestep built where the mountain allowed and '
            'apologized nowhere.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m07', 0, 38, 6,
            'The Long Traverse',
            'A long sidelong stretch beneath a bear-clawed slope.',
            'The path runs long and sidelong beneath a slope of berry scrub, and the scrub '
            'is torn in the wide, thorough way that means bear. A brown one, by the hair on '
            'the thorns — bigger than the valley kind, and less philosophical. A vista opens '
            'from a shelf to the east.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m08', 0, 39, 6,
            'The Crag Shoulder',
            'The first great shoulder; eastward, a delve mouth gapes.',
            "The path crests the Ridge's first great shoulder and the mountain shows its "
            'teeth: eastward, under an overhang of raw crag, a mouth of absolute dark opens '
            'in the stone, breathing cold. Old silk fringes the entrance like grey banners. '
            'The main path continues north, which is one option.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m09', 1, 33, 5,
            'The Goat Ledges',
            'Ledges at absurd angles, thoroughly owned by goats.',
            'The track ends at a series of ledges stacked at angles that should require '
            'permits. The goats stand on all of them, including several that cannot be '
            'reached, watching you attempt geometry they solved at birth.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m10', -1, 35, 5,
            'The Squirrel Pines',
            'Deep pine shade, administered loudly by squirrels.',
            'The pines grow close here, roofing the light out, and the squirrels administer '
            'the dark at volume — chittering ultimatums, dropping cones with intent, holding '
            'grudges of ancient standing. The needle-floor is soft and the air smells of '
            'resin.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m11', 1, 40, 6,
            "The Lion's Backyard",
            'The high meadow the villagers warned you about.',
            'Past the last terrace the ground rises into a hanging meadow, sweet grass and '
            'sun-warmed stone — and bones, once you look, clean and scattered and plural. '
            'This is the place they warned you about, in the village whose warning you did '
            'or did not heed. The lions here do not watch and consider. They are already '
            'moving.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m12', 2, 38, 6,
            'The Crag Shelf',
            'A vista shelf: the Flats laid out golden below.',
            'A flat shelf of stone hangs over the drop, and from it the whole of the '
            'Sagewind Flats lies below in golden motion, the grass moving like weather on '
            "water. Windhome's smoke rises thin and straight. You can see the sink and the "
            'pit from here — two small dark mouths in all that gold — and know better.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m13', 1, 39, 6,
            'The Crag Mouth',
            "The Undercrag's entrance: cold breath and old silk.",
            'Up close the mouth is tall as two doors and hung with silk gone grey with '
            'grit. The cold that moves out of it is cellar-cold, mineral, patient. Somewhere '
            'inside, at the edge of hearing, something plucks a strand and lets it ring.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-st1', 1, 37, 6,
            'Stonestep Terrace',
            'A terraced village street held up by stubborn stonework.',
            "Stonestep's single street runs along a terrace edge, houses built of the "
            'mountain into the mountain, roofs weighted with slabs against the wind. The '
            'people here are civil and busy and glad of travelers, and they will tell you, '
            'unprompted and in detail, not to go up past the top terrace to the high '
            'meadow. The lions have it, they say. The lions have always had it.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-st2', 1, 38, 6,
            'Stonestep Hearths',
            'Upper terrace hearths; beyond, the path they warn about.',
            'The upper terrace holds the hearth-houses, warm-smelling and close, washing '
            "strung between them arguing with the wind. At the terrace's north end a path "
            'continues up toward a hanging meadow, and every villager who sees you look at '
            "it says the same word, kindly, and means it: don't.",
            area=ridge,
        )
        self.stdout.write('Verdant Reach: Viridian Ridge leg 1 rooms seeded (16).')

    def _seed_ridge_rooms_leg2(self, zone, areas):
        ridge = areas['ridge']

        self._vr_room(
            zone, 'vr-m14', 0, 40, 7,
            'The Wind Gap',
            'A notch where the wind crosses the Ridge at speed.',
            'The path threads a notch where the wind crosses the Ridge without slowing down '
            'for anyone. Everything here leans — the grass, the one heroic pine, briefly '
            'you. Through the gap, the higher country shows itself: greener than mountains '
            'have any right to be.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m15', 0, 41, 7,
            'The Third Switchback',
            'Another fold of the path; a goat walk branches east.',
            'The path folds and climbs. The drop below the bend has stopped being '
            'interesting and started being serious. A narrow walk branches east along a '
            'grassy rib where the goats keep their high pastures.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m16', 0, 42, 7,
            'The Grey Ridge',
            'Bare grey stone; a brown bear works the slope below.',
            'The green thins across a rib of bare grey stone, lichen-mapped and '
            'wind-polished. Below the path a brown bear works a berry slope with the total '
            'focus of the self-employed. It is very large. The berries are apparently worth '
            'it.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m17', 0, 43, 7,
            'The Windbreak',
            'A stone windbreak shelters the path; pines crowd west.',
            'Someone, sometime, stacked a long windbreak of dry stone along the path\'s '
            'exposed edge, and generations of travelers have blessed them for it. In its '
            'lee the air goes suddenly still and loud with your own footsteps. Pines crowd '
            'a hollow to the west, full of motion.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m18', 0, 44, 7,
            'Highfold Approach',
            'Goat-folds terrace the slope below a hardy village.',
            "Dry-stone goat-folds step down the slope in neat crescents, and above them "
            "Highfold's houses sit low and round-shouldered against the weather. The bells "
            'of the folds carry down the path. So does a warning, from the first villager '
            'you meet, friendly and firm: the hollow west of the top fold belongs to the '
            'bears now, and the bears are not reasonable this season.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m19', 0, 45, 8,
            'The High Traverse',
            'A long high stretch; a lion crosses at its own pace.',
            'The path runs long and level across the mountain\'s face, the world arranged '
            'below it in tiers. Partway along, a mountain lion crosses ahead of you at its '
            'own pace, gives you one flat unhurried look, and continues — on the spine of '
            'the path, so far, there is a truce.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m20', 0, 46, 8,
            'The Fourth Switchback',
            'The path folds beneath a vista shelf to the west.',
            'The fold gains height in earnest now, the air thinner and bright. A shelf to '
            'the west promises the kind of view that makes the climbing make sense, or at '
            'least argues the case.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m21', 0, 47, 8,
            'The Chitter Shoulder',
            'A dry rasping rides the wind from a gate of dark stone.',
            'The path crests the second shoulder and you hear it before you see it: a dry, '
            'layered rasping, rising and falling, riding the wind from the east — from a '
            'gate of dark stone at the base of a crag, where the mountain has opened and '
            'something inside never stops talking to itself. North, the path continues '
            'toward the last and highest country.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m22', 1, 41, 7,
            'The Goat Walk',
            'A grassy rib of high pasture, thick with goats.',
            'The rib runs out into hanging pasture, sweet and short-cropped, and the goats '
            'are here in numbers — nannies, kids, and one patriarch with horns like '
            'furniture, all watching you with rectangular skepticism.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m23', -1, 43, 7,
            'The Windbreak Pines',
            'A sheltered pine hollow, squirrel-ruled.',
            'The hollow holds the pines and the pines hold the squirrels, and the squirrels '
            'hold court — loudly, continuously, with prejudice. Out of the wind, the air is '
            'warm and resinous and full of small thrown objects.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m24', -1, 45, 7,
            "Bear's Hollow",
            'The torn-up hollow the folk of Highfold warned about.',
            'The hollow west of the top fold is torn — earth clawed up in furrows, saplings '
            'snapped at the height of a shoulder much higher than yours, a smell of musk '
            'thick enough to lean on. Highfold warned you. Highfold may already be a '
            'smoking memory behind you, but the warning was true either way: the bears here '
            'do not bluff, and they have already noticed.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m25', 1, 47, 8,
            'The Chittering Mouth',
            "Chitterdeep's gate: the rasping is louder here, and layered.",
            'The gate of Chitterdeep stands taller than it needs to, and the sound pours '
            'out of it in layers — near rasps and far rasps, over and under, a deep talking '
            'to itself in ten thousand small dry voices. The cold coming up from below '
            'smells of stone and molt.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m26', -1, 46, 8,
            'The Grey Vista',
            'The whole zone below: vale, flats, and the climb between.',
            'From the shelf the whole journey lies below you at once — the vale a green '
            'fold in the far south, the river a bright hair, the flats golden and moving, '
            'the stair invisible but known, every step of it in your legs. Higher country '
            'rises at your back, greener as it climbs, which is not how mountains are '
            'supposed to work.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-hf1', 1, 44, 7,
            'Highfold Terrace',
            'A village of goatherds among their crescent folds.',
            'Highfold lives with its goats the way Reedmere lives with its river: the folds '
            'come first, the houses fit around them. Bells, hay-smell, and hands that never '
            'stop working hide or rope. They are generous with milk-cheese and warnings, in '
            'that order — the hollow west of the hearths, they say, is the bears\' now. Do '
            'not test it.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-hf2', 1, 45, 7,
            'Highfold Hearths',
            'Round-backed hearth houses; westward, the forbidden hollow.',
            'The hearth-houses turn their round backs to the weather, doorways low and '
            'warm-breathed. A track runs west off the top fold toward a pine hollow, and it '
            'is the most warned-about stretch of ground on the mountain: every hearth has a '
            'story about it, and none of the stories end well.',
            area=ridge,
        )
        self.stdout.write('Verdant Reach: Viridian Ridge leg 2 rooms seeded (15).')

    def _seed_ridge_rooms_leg3(self, zone, areas):
        ridge = areas['ridge']

        self._vr_room(
            zone, 'vr-m27', 0, 48, 9,
            'The Thin Air',
            'High country: thin bright air and the summit finally visible.',
            'The air goes thin and glassy and the light gains an edge. Above, for the first '
            'time, the summit shows itself — and it is wrong in the loveliest way: no snow, '
            'no bare rock, but a crown of deep green, glowing like a held leaf. A quiet col '
            'opens west; the path climbs on.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m28', 0, 49, 9,
            'The Fifth Switchback',
            'The folds come faster now; goats claim a ledge east.',
            'The switchbacks come tighter and steeper, the mountain done with pretending to '
            'be gradual. Goats hold a ledge to the east — the high-country breed, shaggier, '
            'bigger, disapproving of your form.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m29', 0, 50, 9,
            'The Stone Teeth',
            'The path threads a row of standing stones like teeth.',
            'Weathered pillars stand in a row across the slope like the teeth of something '
            'the mountain grew over, and the path threads between them. In their lee, a '
            'brown bear the size of a toolshed turns over rocks with one paw, snacking on '
            'what runs out.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m30', 0, 51, 10,
            'The Stunted Rise',
            'Trees shrink to knee height; the wind means it now.',
            'The pines up here grow to the height of your knee and no higher, ancient and '
            "bonsai'd by wind that has never once relented. Squirrels live in them anyway, "
            'at reduced volume and increased fury. A twisted little wood gathers to the '
            'west.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m31', 0, 52, 10,
            'Lastlight Approach',
            "The final village's lights, warm against the height.",
            'Lastlight earns its name at dusk, they say, when its hearths are the last warm '
            'lights below the summit — but even at noon the village reads as an outpost of '
            "warmth against altitude. Its people are the high Ridge's toughest, and their "
            "welcome comes with the mountain's last and most serious warnings attached.",
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m32', 0, 53, 10,
            'The Knife Edge',
            'The path narrows over air on both sides.',
            'For a stretch the path is the top of the mountain — a knife edge with '
            'committed air on both sides and wind with opinions. Westward off the edge, a '
            'ledge track drops toward a sunning shelf the Lastlight folk speak of only to '
            'forbid.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m33', 0, 54, 10,
            'The Sixth Switchback',
            'The last true switchback; a lion owns the bend.',
            'The final switchback folds beneath a wall of green-veined stone. A mountain '
            'lion — high-country big — lies across a sun-warmed rock at the bend, and lets '
            "you pass, this time, on the path's old truce. East, a track climbs toward a "
            'throne of tumbled boulders.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m34', 0, 55, 11,
            'The Crown Shoulder',
            "The summit's last shoulder; eastward, a gate into the mountain.",
            "The last shoulder before the summit, and the mountain's final door: eastward, "
            'a gate of pale stone opens into the peak itself, exhaling air that is somehow '
            'warm, mineral-sweet, alive. The green of the summit crown hangs directly above '
            'now, close enough to make the light under your feet faintly emerald.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m35', 0, 56, 11,
            'The Green Ascent',
            'Impossible green begins: growth where nothing should grow.',
            'The stone gives way to growth. At an altitude that should permit lichen and '
            'apology, the mountain is green — moss deep as carpet, flowers with no names '
            'you know, air warm as a held breath. It should not be. It is. Every step '
            'upward, the wrongness gets more beautiful. A rail of cloud hangs level with a '
            'shelf to the east.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m36', 1, 49, 9,
            'The High Fold Ledge',
            'The highest goats on the mountain hold this ledge.',
            'The ledge belongs to the highest goats on the mountain, shag-coated and '
            'enormous, who regard your arrival with the mild interest of creatures that '
            'have watched avalanches from above.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m37', -1, 51, 10,
            'The Stunted Pines',
            "A wind-bonsai'd wood, knee-high and centuries old.",
            'The little wood is centuries old and knee-high, every trunk a fist of '
            "resistance. The squirrels here are the mountain's maddest, living at the edge "
            'of the possible and defending it like a kingdom.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m38', -1, 53, 10,
            "Lion's Watch",
            'The sunning shelf Lastlight forbids, and for good reason.',
            'The ledge track ends at a broad shelf where the sun pools all day, and the '
            "lions of the high Ridge keep it as a court. Lastlight's forbiddance was not "
            'folklore: the shapes rising from the warm stone are already committed, and up '
            'here there is nowhere to be but exactly where you are.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m39', 1, 54, 10,
            "Bear's Throne",
            "A tumble of boulders ruled by the mountain's largest bears.",
            'The boulders stack into a natural throne against the summit wall, and the '
            "mountain's largest bears hold it — visibly, deliberately, a dynasty in fur. "
            'The bones about the base are old and new and not all small. This is the '
            "hardest ground on the mountain that isn't underground, and it knows it.",
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m40', 1, 55, 11,
            'The Crown Mouth',
            "Hollowcrown's gate: warm air rising from inside the peak.",
            'The gate into the summit stands pale and veined, and the air moving out of it '
            'rises — warm, sweet with mineral and growth, wrong for a cave in every '
            'reassuring way and one alarming one: beneath the sweetness, wings. Somewhere '
            'above and inside, the hollow of the crown hums.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m41', 0, 57, 12,
            'The Last Stair',
            'Steps of living stone rise through flowers to the crown.',
            'Steps rise through the green — not carved, this time, but grown, stone risers '
            'cushioned in moss, flowers crowding the treads. The light from above is '
            'emerald and gold. The air hums faintly, warm as noon. Whatever waits at the '
            'top has been waiting a long time, and gladly.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m42', 1, 56, 11,
            'The Cloud Rail',
            'A shelf level with the clouds themselves.',
            'The shelf hangs level with a rail of cloud that streams past close enough to '
            "touch, tearing silently on the summit's green shoulder. Below the cloud, the "
            'whole zone; above it, only the crown. People would build temples for this '
            'view. Up here, the mountain simply has it.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-m43', -1, 48, 9,
            'The Silent Col',
            'A hushed saddle where the wind, for once, does not come.',
            'The col sits in a fold of the mountain that the wind, by some accident of '
            'shape, cannot enter. The silence is total and physical. Grass grows tall here, '
            "unbothered, and the air holds the day's warmth like cupped hands. Travelers "
            'who find it tend to stay an hour longer than they meant to.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-ll1', 1, 52, 10,
            'Lastlight Terrace',
            'The highest village: stone houses roped against the sky.',
            "Lastlight's houses are stone to the eaves and roped to the mountain, and its "
            'people are correspondingly weatherproof. They feed travelers as a duty and a '
            "pleasure, and they deliver the mountain's last warnings with the weight of "
            "scripture: the sunning shelf west of the Knife Edge is the lions'; the boulder "
            "throne east of the last switchback is the bears'; and past both, they say — "
            'lower, with something that is not quite fear — is the hollow in the crown, and '
            'what keeps it.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-ll2', 1, 53, 10,
            'Lastlight Hearths',
            'The last hearths below the summit, warm and watchful.',
            'The hearth-row is the warmest ground on the high mountain, and the most '
            "watchful — hunters' bows hang strung by every door. From here the green of the "
            'crown is directly overhead, casting its faint emerald light on the chimney '
            'smoke. The people of Lastlight look up at it often. They never say quite what '
            'they think of it.',
            area=ridge,
        )
        self._vr_room(
            zone, 'vr-vc1', 0, 58, 12,
            'The Verdant Crown',
            'Eden on the roof of the world, and a green sphere in an obelisk.',
            'The summit is a garden. There is no other word and no need for one: at an '
            'altitude fit for ice, the crown of the mountain is deep with green — moss and '
            'flower and slender trees, warm air, water somewhere speaking quietly to stone. '
            'In the center stands an obelisk, twin in every proportion to the one at the '
            'Heart of the Convergence, and suspended in its stone burns a sphere of pure '
            'deep green, steady as a held note. The garden grows toward it. Everything here '
            'does. You have walked the whole of the Verdant Reach to stand in this light, '
            'and the light, unmistakably, notices.',
            area=ridge, safe=True,
        )
        self.stdout.write('Verdant Reach: Viridian Ridge leg 3 rooms seeded (20).')

    def _seed_undercrag_rooms(self, zone, areas):
        undercrag = areas['undercrag']

        self._vr_room(
            zone, 'vr-c5a', 2, 39, 6,
            'The Crag Gate',
            'A cold entry hall hung with grey silk banners.',
            'The entry hall is tall and cellar-cold, hung with silk gone grey and heavy '
            'with rock dust. The floor is swept — not clean, swept, in long strokes the '
            "width of a body. A shaft descends at the hall's end, its lip polished by use.",
            area=undercrag, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c5b', 2, 39, 5,
            'The First Descent',
            'Down the shaft: silk lines run taut into the dark.',
            'The shaft lets into a sloping gallery where silk lines run taut along the '
            'walls like the rigging of a ship, thrumming faintly when anything anywhere '
            'moves. The dark ahead has depth to it, and occupants.',
            area=undercrag, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c5c', 2, 40, 5,
            'The Under Gallery',
            'A broad web-strung gallery; a chimney climbs into black.',
            'The gallery opens broad and low, webbed post to pillar, and the rustling here '
            'is constant — above, below, keeping pace. A natural chimney climbs into black '
            'overhead, its walls silk-lined all the way up, which is information.',
            area=undercrag, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c5d', 2, 40, 6,
            'The Web Chimney',
            'A silk-lined vertical pocket, thick with weavers.',
            'The chimney tops out in a pocket entirely upholstered in silk, floor '
            'indistinguishable from wall from ceiling. Everything here is at an angle and '
            'everything here is theirs. Coming up the chimney, you were felt arriving the '
            'whole way.',
            area=undercrag, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c5e', 2, 41, 5,
            'The Cold Ladder',
            'Natural stone steps descend into deeper cold.',
            'The gallery ends at a descent of natural steps, each broad as a table, '
            'dropping into cold that gains authority with every level. Beetles patrol here '
            '— the elder kind, big as carts, wing cases whispering open at your light.',
            area=undercrag, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c5f', 2, 41, 4,
            'The Black Span',
            'A stone bridge over darkness; a silk well drops below.',
            'A natural span of stone crosses a gulf whose bottom your light declines to '
            'discuss. Silk cables anchor the span to the walls in a way that suggests '
            'maintenance. Partway across, a well of woven silk drops through the span '
            'itself, down into the true dark.',
            area=undercrag, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c5g', 2, 41, 3,
            'The Silk Well',
            'The bottom of the well: a nursery of pale silk.',
            'The well bottoms out in a chamber of layered pale silk, egg-cases racked along '
            'the walls in disquieting order. The weavers here are protective in the '
            'absolute sense. The way you came in is the way out, and they know it better '
            'than you.',
            area=undercrag, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c5h', 2, 42, 4,
            'The Deep Landing',
            "The delve's deep floor; ahead, a vault of listening silk.",
            "The span lands on the delve's deep floor, and the silk here changes character "
            '— older, denser, structural. Every strand runs the same direction: inward, '
            'north, toward a vault where the dark is complete and attentive. The rustling '
            'has stopped, which is worse.',
            area=undercrag, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c5i', 2, 43, 4,
            "The Weaver's Vault",
            "The Weaver's chamber; high above, a snared strongbox hangs.",
            "The vault rises out of your light's reach, and the Weaver holds its center — "
            'a spider of architectural size, pale as the deep silk it has spent generations '
            'spinning. High above, snared in a cradle of lines, hangs an iron-strapped '
            'strongbox, taken whole from someone who needed it, kept for reasons a spider '
            'keeps things. Every line in the room runs, eventually, to her.',
            area=undercrag, indoors=True,
        )
        self.stdout.write('Verdant Reach: Undercrag rooms seeded (9).')

    def _seed_chitterdeep_rooms(self, zone, areas):
        chitterdeep = areas['chitterdeep']

        self._vr_room(
            zone, 'vr-c6a', 2, 47, 8,
            'The Chitter Gate',
            'The rasping surrounds you the moment you enter.',
            'Inside the gate the sound is no longer ahead of you; it is around you — dry, '
            'layered, continuous, the deep talking in its sleep. The passage tips '
            'immediately downward, walls polished at flank height by the passing of long '
            'bodies.',
            area=chitterdeep, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c6b', 2, 47, 7,
            'The Falling Gallery',
            'The passage falls in long polished pitches.',
            'The gallery descends in long pitches, floor polished to a shine that has '
            'nothing to do with water. Centipedes flow along the walls in both directions, '
            'unbothered by the grade, unbothered by you — so far.',
            area=chitterdeep, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c6c', 2, 47, 6,
            'The Thousand Steps',
            'Rippled stone descends like steps cut for no human gait.',
            'The floor ripples into hundreds of shallow ridges descending into the dark — '
            'steps, if steps were cut for a gait with a hundred feet. Beetles work the '
            'margins here, and a side passage east breathes a papery smell.',
            area=chitterdeep, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c6d', 3, 47, 6,
            'The Molt Chamber',
            "Shed skins stand propped like a museum of the deep's growth.",
            "The chamber is full of the deep's history: shed centipede skins, translucent "
            'and whole, propped against the walls by draft and chance like exhibits. They '
            'ascend in size toward the back, where the largest stands taller than you and '
            'is not the largest thing down here.',
            area=chitterdeep, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c6e', 2, 48, 6,
            'The Chitter Hall',
            'A long hall where the sound gains a rhythm; a vault drops below.',
            'The hall runs long and ribbed, and in it the chittering gains something '
            'terrible: rhythm. Call and response, near and far, ten thousand small voices '
            'keeping time. Spiders hunt the margins of the sound. A worked shaft drops '
            'through the floor midway, breathing warmth and the smell of eggs.',
            area=chitterdeep, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c6f', 2, 48, 5,
            'The Egg Vault',
            'A warm vault racked with translucent eggs.',
            'The vault below is warm as a body and racked wall to wall with eggs — '
            'translucent, faintly pulsing, each holding a coiled length of what the deep is '
            'made of. The guardians here do not patrol. They are simply always between you '
            'and the racks.',
            area=chitterdeep, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c6g', 2, 49, 6,
            'The Long Crawl',
            'The ceiling drops; the passage insists on humility.',
            'The ceiling steps down until the passage insists on humility, and you move at '
            'a crouch through stone dust and molt-paper while things your own length flow '
            'past in the dark with room to spare. This is their hallway. You are the wrong '
            'shape for it.',
            area=chitterdeep, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c6h', 2, 50, 6,
            'The Rising Dark',
            'The deep turns upward; the rhythm converges from above.',
            'Unexpectedly, the deep turns upward — a climbing gallery, the rhythm of the '
            'chittering converging from overhead now, all its layers braiding into one '
            'direction. The air warms as you climb. Whatever conducts this chorus is above '
            'you.',
            area=chitterdeep, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c6i', 2, 50, 7,
            "The King's Approach",
            'A polished processional gallery; the sound holds its breath.',
            'The climb lets into a gallery polished like the inside of a shell, and here — '
            'only here — the chittering stops. The silence is ceremonial. The floor is '
            "swept. The passage north has the proportions of a throne room's doors because "
            'that is what it is.',
            area=chitterdeep, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c6j', 2, 51, 7,
            'The Chittering Throne',
            'The King coiled about an ancient chest, scored by a thousand legs.',
            'The throne room rises in ribs of dark stone, and the King fills it — a '
            'centipede of dynastic size, coiled in glossy tiers about a chest of black iron '
            'and older wood, its lid scored soft by the grip of a thousand legs across '
            'uncountable years. As your light touches him the chittering resumes from every '
            'wall at once: the deep, announcing its King. He uncoils exactly as much as the '
            'occasion requires.',
            area=chitterdeep, indoors=True,
        )
        self.stdout.write('Verdant Reach: Chitterdeep rooms seeded (10).')

    def _seed_hollowcrown_rooms(self, zone, areas):
        hollowcrown = areas['hollowcrown']

        self._vr_room(
            zone, 'vr-c7a', 2, 55, 11,
            'The Crown Gate',
            'Warm mineral air and a hum: the inside of the summit.',
            'Inside the gate the mountain is warm. Veins of pale green mineral thread the '
            'walls, glowing faintly, and the hum you felt outside resolves into layers — '
            'the deep drone of wings, somewhere above, and under it something almost like '
            "the garden's warmth given a voice. The way leads north, and then, impossibly "
            'for a cave, up.',
            area=hollowcrown, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c7b', 2, 56, 11,
            'The Hollow Stair',
            'A rising gallery, green-veined and wing-swept.',
            'The passage rises in a natural stair of green-veined stone, the mineral light '
            'strengthening as you climb. Beetles command this gallery — the elder kind, '
            'vast, dropping from the dark above with a sound like tearing canvas.',
            area=hollowcrown, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c7c', 2, 56, 12,
            'The Veined Gallery',
            'Glowing mineral veins thick as rivers; a seam glitters east.',
            'The veins run thick as rivers here, casting the gallery in green half-light '
            'that needs no torch. Spiders have strung the high corners, their silk catching '
            'the glow like frost. To the east a seam in the wall glitters with something '
            'more than mineral.',
            area=hollowcrown, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c7d', 3, 56, 12,
            'The Glittering Seam',
            'A crystal-crusted pocket, jealously patrolled.',
            'The seam opens into a pocket crusted in green crystal, every facet holding a '
            'small burning copy of your light. The beetles patrol it with what can only be '
            'called jealousy. Things glint in the crystal matrix that did not grow there — '
            'carried things, hoarded things, a magpie instinct at monstrous scale.',
            area=hollowcrown, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c7e', 2, 57, 12,
            'The Upper Dark',
            'The climb continues; the hum gains mass overhead.',
            'The gallery climbs again, and the hum overhead gains mass — no longer sound, '
            'closer to weather. Centipedes hunt this stretch, drawn up from their own deeps '
            "by whatever the crown's warmth promises. The green light strengthens with "
            'every step upward.',
            area=hollowcrown, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c7f', 2, 57, 13,
            'The Wingway',
            'A flight gallery inside the peak; wings pass like weather.',
            'The passage broadens into a flight gallery where the beetles move at speed '
            'through the green glow, wings roaring open, banking around you as though you '
            'were furniture — for now. A shaft drops away east where something fell, or was '
            'dropped, long ago.',
            area=hollowcrown, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c7g', 3, 57, 13,
            'The Fallen Shaft',
            "A collapsed pocket where the crown's cast-offs gather.",
            "The shaft ends in a collapsed pocket where the hollow's cast-offs have "
            'gathered across ages — carapace, crystal shards, the dust of things carried up '
            'and found wanting. Spiders and centipedes contest the scraps here, in the dark '
            'below the light.',
            area=hollowcrown, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c7h', 2, 58, 13,
            'The Deep Turn',
            'The last broad turn; above, the hum is a single deep chord.',
            'The gallery makes one last broad turn beneath a ceiling lost in green glow, '
            'and the hum above resolves into a single sustained chord, patient and '
            'enormous. The beetles here no longer patrol. They stand posted. The hollow is '
            'done being casual about you.',
            area=hollowcrown, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c7i', 2, 58, 14,
            'The Last Dark',
            'The final climb: warm, bright-veined, and defended.',
            'The last climb rises through stone so veined with glowing green it is barely '
            'dark at all. The air is garden-warm and moving, drawn upward toward the crown. '
            "What defends this stretch defends it absolutely: the summit's own, in the "
            "summit's own light.",
            area=hollowcrown, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c7j', 2, 59, 14,
            "The Devourer's Approach",
            "A processional gallery beneath the garden's floor.",
            'You are directly beneath the garden now — rootlets finger through the ceiling '
            'seams, and water somewhere above speaks its quiet syllable to stone. The '
            "gallery runs processional and green-lit toward the hollow's heart, and the "
            'chord of wings ahead deepens to greet you, which is not the right word, and '
            'both of you know it.',
            area=hollowcrown, indoors=True,
        )
        self._vr_room(
            zone, 'vr-c7k', 2, 60, 14,
            "The Devourer's Hoard",
            "The hollow's heart: the Devourer atop a hoard, beneath the Crown.",
            "The hollow's heart is a vaulted chamber directly beneath the Verdant Crown, "
            'its ceiling a lace of glowing roots, and it is floored — floored — in hoard: '
            'coin, crystal, carried treasure of every genre the rifts ever spilled, heaped '
            'in dunes. Atop it, wings spread to the vault, stands the Crowned Devourer: a '
            'beetle at the scale of legend, chitin black-green as the deepest leaf, the '
            'chord of its wings the very hum you have climbed through all this way. Above '
            'you both, through the roots, the light of the Crown burns green and steady. '
            'The Devourer does not move to meet you. On a hoard like this, everything comes '
            'to it eventually.',
            area=hollowcrown, indoors=True,
        )
        self.stdout.write('Verdant Reach: Hollowcrown rooms seeded (11).')

    def _seed_verdant_loot_tables(self):
        boss_weapons = [
            'iron-sword', 'iron-mace', 'broadsword',
            'battle-axe', 'hunting-bow', 'combat-knife',
        ]
        boss_armor = [
            'leather-cap', 'leather-shoulders', 'leather-vest', 'leather-gloves',
            'leather-belt', 'leather-leggings', 'leather-boots', 'wooden-shield',
        ]
        boss_accessories = [
            f'copper-{kind}-of-{stat}'
            for kind in ('ring', 'amulet')
            for stat in ('strength', 'dexterity', 'endurance',
                         'intelligence', 'wisdom', 'perception')
        ]
        villager_weights = {'common': 85, 'uncommon': 15}

        # (table slug, table name, entries); each entry is
        # (item slug, drop_chance, rarity_weights, guaranteed_group).
        tables = [
            ('animal-drops', 'Animal Drops', [
                ('animal-hide', 0.35, {'common': 100}, ''),
            ]),
            ('insect-drops', 'Insect Drops', [
                ('insect-carapace', 0.35, {'common': 100}, ''),
            ]),
            ('reedmere-gear', 'Reedmere Gear', [
                ('combat-knife', 0.12, villager_weights, ''),
                ('leather-boots', 0.10, villager_weights, ''),
                ('leather-belt', 0.10, villager_weights, ''),
                ('leather-gloves', 0.10, villager_weights, ''),
            ]),
            ('windhome-gear', 'Windhome Gear', [
                ('hunting-bow', 0.10, villager_weights, ''),
                ('leather-leggings', 0.10, villager_weights, ''),
                ('leather-cap', 0.10, villager_weights, ''),
                ('leather-vest', 0.12, villager_weights, ''),
            ]),
            ('matron-loot', 'Silk Matron Loot',
             [(slug, 1.0, {'uncommon': 100}, 'weapon') for slug in boss_weapons]
             + [('insect-carapace', 0.5, {'common': 100}, '')]),
            ('whistler-loot', 'Whistler Below Loot',
             [(slug, 1.0, {'uncommon': 100}, 'armor') for slug in boss_armor]
             + [('insect-carapace', 0.5, {'common': 100}, '')]),
            ('dronemother-loot', 'Dronemother Loot',
             [(slug, 1.0, {'uncommon': 100}, 'accessory') for slug in boss_accessories]
             + [('insect-carapace', 0.5, {'common': 100}, '')]),
        ]

        for table_slug, table_name, entries in tables:
            table, _ = LootTable.objects.get_or_create(
                slug=table_slug, defaults={'name': table_name},
            )
            for item_slug, drop_chance, weights, group in entries:
                LootTableEntry.objects.get_or_create(
                    loot_table=table,
                    item_definition=ItemDefinition.objects.get(slug=item_slug),
                    defaults={
                        'mk_tier_min': 1,
                        'mk_tier_max': 1,
                        'drop_chance': drop_chance,
                        'guaranteed_group': group,
                        'rarity_weights': weights,
                    },
                )
        self.stdout.write(f'Verdant Reach: {len(tables)} loot tables seeded.')

    def _seed_verdant_npcs(self):
        # Each entry: (slug, name, combat_tier, is_aggressive,
        #              (VIT, STR, DEX, END, INT, WIS, PER), scaling_factor,
        #              pool slug, loot table slug, (copper min, max),
        #              respawn_minutes, description, extras)
        npcs = [
            # Surface creatures — passive
            ('river-otter', 'river otter', 'normal', False,
             (15, 4, 10, 5, 3, 3, 8), 1.0, 'sp-river-otter', 'animal-drops', (0, 0), 1,
             'Sleek, whiskered, and entirely certain the river was made for it. '
             'It watches you upside down, mid-float, unimpressed.', {}),
            ('black-bear', 'black bear', 'normal', False,
             (35, 10, 6, 9, 3, 3, 6), 2.0, 'sp-black-bear', 'animal-drops', (0, 0), 1,
             'A black bear, big as a haystack and about as hurried. Its attention '
             "is on the fish, until it isn't.", {}),
            ('young-mountain-lion', 'young mountain lion', 'normal', False,
             (28, 8, 11, 7, 3, 3, 9), 2.0, 'sp-mountain-lion', 'animal-drops', (0, 0), 1,
             'Lean and tawny, all shoulder and patience, moving over the rock '
             'like it weighs nothing and owes nothing.', {}),
            ('wild-boar', 'wild boar', 'elite', False,
             (55, 12, 7, 12, 2, 2, 6), 3.0, 'sp-wild-boar', 'animal-drops', (0, 0), 1,
             'Bristled, tusked, and built like a barrel full of grudges. It does '
             'not startle. It commits.', {}),
            ('plains-deer', 'plains deer', 'normal', False,
             (45, 8, 13, 10, 3, 3, 11), 4.0, 'sp-plains-deer', 'animal-drops', (0, 0), 1,
             'A plains deer, ears up, legs coiled, already halfway into the '
             'decision to be somewhere else.', {}),
            ('plains-rabbit', 'plains rabbit', 'normal', False,
             (18, 4, 15, 6, 2, 2, 12), 4.0, 'sp-plains-rabbit', 'animal-drops', (0, 0), 1,
             'A rabbit of the flats — grass-fat, absurdly quick, running errands '
             'of tremendous urgency and no discernible purpose.', {}),
            ('prairie-dog', 'prairie dog', 'normal', False,
             (16, 4, 14, 6, 3, 3, 13), 4.0, 'sp-prairie-dog', 'animal-drops', (0, 0), 1,
             'It stands bolt upright on its mound, whistling civic outrage at '
             'your existence to the entire town.', {}),
            ('buffalo', 'buffalo', 'elite', False,
             (90, 16, 6, 16, 2, 2, 8), 5.0, 'sp-buffalo', 'animal-drops', (0, 0), 1,
             'A hill that eats grass. It regards you with one enormous, '
             'incurious eye and continues chewing.', {}),
            # Villagers — passive
            ('reedmere-villager', 'Reedmere villager', 'normal', False,
             (30, 7, 7, 7, 6, 6, 6), 2.0, None, 'reedmere-gear', (2, 8), 5,
             "A villager of Reedmere, reed-cutter's hands and river-colored "
             'clothes, moving through the day\'s work without hurry.', {}),
            ('reedmere-fisher', 'Reedmere fisher', 'normal', False,
             (30, 8, 8, 7, 5, 6, 8), 2.0, None, 'reedmere-gear', (2, 8), 5,
             'Net over one shoulder, scales on both forearms, and an opinion '
             "about tomorrow's weather you didn't ask for.", {}),
            ('windhome-villager', 'Windhome villager', 'normal', False,
             (50, 9, 9, 9, 7, 8, 8), 4.0, None, 'windhome-gear', (4, 12), 5,
             'A person of Windhome, wind-weathered and easy, hands never idle — '
             'there is always hide to work, and the wind does not wait.', {}),
            ('windhome-hunter', 'Windhome hunter', 'normal', False,
             (65, 10, 13, 10, 7, 8, 13), 5.0, None, 'windhome-gear', (4, 12), 5,
             'A hunter of Windhome, bow worn to the shape of their grip, '
             'watching the grass the way others watch fire.', {}),
            # Checkpoint service NPCs — passive
            ('maro-the-mender', 'Maro the Mender', 'normal', False,
             (30, 7, 7, 7, 6, 6, 6), 2.0, None, 'reedmere-gear', (2, 8), 5,
             'A Reedmere man gone grey at the temples, tool roll spread on a '
             'bench worn smooth by work. He came up from the village for the '
             'foot traffic and stayed for the sphere, which he talks to, '
             'quietly, when he thinks no one is listening.',
             {'is_repairer': True}),
            ('essa-the-trader', 'Essa the Trader', 'normal', False,
             (30, 7, 7, 7, 6, 6, 6), 2.0, None, 'reedmere-gear', (4, 12), 5,
             'A Reedmere trader with a blanket of goods weighted at the corners '
             'and an eye that prices you, kindly, as you approach.', {}),
            ('tavik-the-mender', 'Tavik the Mender', 'normal', False,
             (50, 9, 9, 9, 7, 8, 8), 4.0, None, 'windhome-gear', (4, 12), 5,
             'A Windhome mender, cross-legged on a hide, needle and awl moving '
             'without being watched. Travelers keep appearing beside the green '
             'light, and travelers always need something sewn, hammered, or '
             'talked back into shape.',
             {'is_repairer': True}),
            ('sona-the-trader', 'Sona the Trader', 'normal', False,
             (50, 9, 9, 9, 7, 8, 8), 4.0, None, 'windhome-gear', (6, 16), 5,
             'A trader of Windhome, goods laid out in painted order against the '
             'wind. She learned three languages from the people who appear '
             'beside the sphere and is working on a fourth.', {}),
            # The Verdant Shard
            ('verdant-shard', 'a Verdant Shard', 'normal', False,
             (1, 1, 1, 1, 1, 1, 1), 1.0, None, None, (0, 0), 1,
             'A small sphere of soft green light, unattached to anything, '
             'wandering the air at head height. It circles things — the water, '
             'the wind, your face — with an attention that feels less like '
             'watching and more like delight. It is a piece of an obelisk '
             'somewhere, gone out to see the world, and gladness comes off it '
             'like warmth off a stone.', {}),
            # Cave insects — aggressive
            ('cave-spider', 'cave spider', 'normal', True,
             (25, 7, 11, 6, 2, 2, 9), 2.0, 'vale-spider', 'insect-drops', (0, 0), 1,
             'A spider the size of a dog, pale from the dark, moving in bursts '
             'of terrible fluency between long, considered stillnesses.', {}),
            ('cave-centipede', 'cave centipede', 'normal', True,
             (32, 9, 10, 8, 2, 2, 8), 3.0, 'vale-centipede', 'insect-drops', (0, 0), 1,
             'As long as your leg and faster than your eye, a river of hooked '
             'legs under a glossy segmented back.', {}),
            ('cave-beetle', 'cave beetle', 'normal', True,
             (40, 10, 8, 11, 2, 2, 7), 3.0, 'vale-beetle', 'insect-drops', (0, 0), 1,
             'A beetle broad as a shield, chitin dark as oiled iron. Its wing '
             'cases sit slightly open, ready, always ready.', {}),
            ('giant-cave-spider', 'giant cave spider', 'normal', True,
             (55, 11, 14, 9, 2, 2, 11), 4.0, 'flats-spider', 'insect-drops', (0, 0), 1,
             'Bigger than the ones in the valley stories, and the valley '
             'stories were already lies people told to feel safer.', {}),
            ('giant-cave-centipede', 'giant cave centipede', 'normal', True,
             (65, 13, 12, 11, 2, 2, 10), 5.0, 'flats-centipede', 'insect-drops', (0, 0), 1,
             'A horror of length and hunger, thick as a rolled tent, its front '
             'legs modified into things with only one purpose.', {}),
            ('giant-cave-beetle', 'giant cave beetle', 'normal', True,
             (75, 14, 10, 14, 2, 2, 9), 5.0, 'flats-beetle', 'insect-drops', (0, 0), 1,
             'The size of a cart. When the wings open, the sound arrives in '
             'your chest before your ears.', {}),
            # Bosses — aggressive
            ('silk-matron', 'the Silk Matron', 'boss', True,
             (120, 12, 14, 11, 4, 4, 12), 3.0, 'vale-spider', 'matron-loot', (50, 150), 10,
             'Pale and vast in the crown of her own silk, legs spanning more '
             'shadow than your light can argue with. She holds one wrapped '
             'bundle apart from all the rest, close, the way anything holds '
             'the thing it loves.',
             {'death_message':
              'The Silk Matron curls inward and drops from her web — and with '
              'her falls the bundle she guarded, splitting open on the stone '
              'in a spill of silk and stolen things.'}),
            ('whistler-below', 'the Whistler Below', 'boss', True,
             (260, 16, 15, 15, 4, 4, 12), 6.0, 'flats-centipede', 'whistler-loot', (50, 150), 10,
             'A centipede beyond sense, coiled through the fluted stone in '
             "glossy yards, antennae reading the wind's one endless note. This "
             'is its hollow. Everything in it, it kept.',
             {'death_message':
              'The Whistler Below collapses in a long shudder, and the wind '
              'through the sink changes pitch — somewhere above, a rope of '
              'woven grass gives way, and a hide-wrapped cache drops to the '
              'floor.'}),
            ('dronemother', 'the Dronemother', 'boss', True,
             (320, 18, 12, 18, 5, 5, 11), 6.0, 'flats-beetle', 'dronemother-loot', (50, 150), 10,
             'The hive made flesh: a beetle vast as a wagon, plated in '
             'iron-dark chitin, the hum bending deeper around her. Her wings '
             'are furled like banners before a war.',
             {'death_message':
              "The Dronemother's wings still at last. The honeycomb wall "
              'behind her cracks along its seams and sloughs away, revealing '
              'a hollow packed with the shining things she hoarded.'}),
            # Boss minions — aggressive, spawn-gated on their boss
            ('matrons-brood', "one of the Matron's brood", 'normal', True,
             (25, 7, 11, 6, 2, 2, 9), 2.0, 'vale-spider', 'insect-drops', (0, 0), 3,
             "A spider of the Matron's brood, quick and pale, never straying "
             'far from the silk she spun it in.', {}),
            ('whistlers-young', "one of the Whistler's young", 'normal', True,
             (50, 13, 12, 11, 2, 2, 10), 4.0, 'flats-centipede', 'insect-drops', (0, 0), 3,
             "Young only by the Whistler's measure — already longer than your "
             'arm, already sure of what it is.', {}),
            ('dronemothers-swarm', "one of the Dronemother's swarm", 'normal', True,
             (60, 14, 10, 14, 2, 2, 9), 4.0, 'flats-beetle', 'insect-drops', (0, 0), 3,
             'A soldier of the swarm, wings half-open, holding the line its '
             "mother's hum assigns it.", {}),
        ]

        self._upsert_npc_definitions(npcs, 'Verdant Reach')

    def _upsert_npc_definitions(self, npcs, label):
        created_count = 0
        for (slug, name, tier, aggressive, stats, sf, pool_slug, loot_slug,
             (copper_min, copper_max), respawn, description, extras) in npcs:
            vit, s, d, e, i, w, p = stats
            content = {
                'name': name,
                'genre_tag': 'fantasy',
                'description': description,
                'is_aggressive': aggressive,
                'is_unique': extras.get('is_unique', False),
                'wanders': False,
                'combat_tier': tier,
                'loot_table': LootTable.objects.get(slug=loot_slug) if loot_slug else None,
                'unarmed_message_pool': (
                    UnarmedMessagePool.objects.get(slug=pool_slug) if pool_slug else None
                ),
                'is_repairer': extras.get('is_repairer', False),
                'death_message': extras.get('death_message', ''),
            }
            balance = {
                'base_vitality': vit,
                'base_str': s, 'base_dex': d, 'base_end': e,
                'base_int': i, 'base_wis': w, 'base_per': p,
                'scaling_factor': sf,
                'currency_drop_min': copper_min,
                'currency_drop_max': copper_max,
                'respawn_minutes': respawn,
            }
            _, created = NpcDefinition.objects.update_or_create(
                slug=slug,
                defaults=content,
                create_defaults={**content, **balance},
            )
            if created:
                created_count += 1
        self.stdout.write(
            f'{label}: {len(npcs)} NPC definitions seeded '
            f'({created_count} created).'
        )

    def _seed_verdant_spawns(self):
        # (room key, npc slug, count, gating boss slug or None)
        spawns = [
            # Surface
            ('vr-v06', 'black-bear', 2, None),
            ('vr-v08', 'river-otter', 2, None),
            ('vr-v12', 'black-bear', 1, None),
            ('vr-v17', 'river-otter', 3, None),
            ('vr-v18', 'young-mountain-lion', 2, None),
            ('vr-v19', 'wild-boar', 2, None),
            ('vr-v21', 'black-bear', 2, None),
            ('vr-v21', 'river-otter', 1, None),
            ('vr-rm1', 'reedmere-villager', 2, None),
            ('vr-rm2', 'reedmere-villager', 2, None),
            ('vr-rm3', 'reedmere-fisher', 2, None),
            ('vr-v07', 'verdant-shard', 1, None),
            ('vr-v07', 'maro-the-mender', 1, None),
            ('vr-v07', 'essa-the-trader', 1, None),
            ('vr-f01', 'verdant-shard', 1, None),
            ('vr-f01', 'tavik-the-mender', 1, None),
            ('vr-f01', 'sona-the-trader', 1, None),
            ('vr-f02', 'plains-deer', 2, None),
            ('vr-f04', 'plains-deer', 2, None),
            ('vr-f07', 'plains-rabbit', 2, None),
            ('vr-f09', 'buffalo', 2, None),
            ('vr-f16', 'plains-deer', 1, None),
            ('vr-f10', 'plains-rabbit', 3, None),
            ('vr-f11', 'buffalo', 3, None),
            ('vr-f13', 'prairie-dog', 4, None),
            ('vr-f15', 'plains-deer', 3, None),
            ('vr-f17', 'buffalo', 2, None),
            ('vr-w1', 'windhome-villager', 2, None),
            ('vr-w2', 'windhome-villager', 1, None),
            ('vr-w2', 'windhome-hunter', 2, None),
            # Caves
            ('vr-c1a', 'cave-spider', 1, None),
            ('vr-c2a', 'cave-spider', 2, None),
            ('vr-c2b', 'cave-spider', 1, None),
            ('vr-c2b', 'cave-centipede', 1, None),
            ('vr-c2c', 'cave-centipede', 1, None),
            ('vr-c2c', 'cave-beetle', 1, None),
            ('vr-c2d', 'silk-matron', 1, None),
            ('vr-c2d', 'matrons-brood', 2, 'silk-matron'),
            ('vr-c3a', 'giant-cave-spider', 1, None),
            ('vr-c3b', 'giant-cave-centipede', 2, None),
            ('vr-c3c', 'giant-cave-beetle', 1, None),
            ('vr-c3d', 'giant-cave-spider', 2, None),
            ('vr-c3e', 'giant-cave-centipede', 1, None),
            ('vr-c3e', 'giant-cave-beetle', 1, None),
            ('vr-c3f', 'whistler-below', 1, None),
            ('vr-c3f', 'whistlers-young', 2, 'whistler-below'),
            ('vr-c4a', 'giant-cave-beetle', 2, None),
            ('vr-c4b', 'giant-cave-beetle', 1, None),
            ('vr-c4b', 'giant-cave-spider', 1, None),
            ('vr-c4c', 'giant-cave-centipede', 2, None),
            ('vr-c4d', 'giant-cave-spider', 2, None),
            ('vr-c4e', 'giant-cave-beetle', 2, None),
            ('vr-c4f', 'giant-cave-centipede', 1, None),
            ('vr-c4f', 'giant-cave-beetle', 1, None),
            ('vr-c4g', 'giant-cave-beetle', 2, None),
            ('vr-c4h', 'dronemother', 1, None),
            ('vr-c4h', 'dronemothers-swarm', 2, 'dronemother'),
        ]
        for room_key, npc_slug, count, gate_slug in spawns:
            RoomSpawn.objects.get_or_create(
                room=self.rooms[room_key],
                npc_definition=NpcDefinition.objects.get(slug=npc_slug),
                mk_tier=1,
                defaults={
                    'count': count,
                    'is_active': True,
                    'requires_living_npc': (
                        NpcDefinition.objects.get(slug=gate_slug)
                        if gate_slug else None
                    ),
                },
            )
        self.stdout.write(f'Verdant Reach: {len(spawns)} room spawns seeded.')

    def _seed_verdant_vendors(self):
        vendors = {
            'essa-the-trader': [
                ('healing-draught', 15),
                ('combat-knife', 40),
                ('leather-boots', 35),
                ('leather-gloves', 35),
            ],
            'sona-the-trader': [
                ('healing-draught', 15),
                ('hunting-bow', 90),
                ('leather-vest', 60),
                ('leather-leggings', 55),
            ],
        }
        entry_count = 0
        for npc_slug, wares in vendors.items():
            npc = NpcDefinition.objects.get(slug=npc_slug)
            for item_slug, price in wares:
                VendorEntry.objects.get_or_create(
                    npc_definition=npc,
                    item_definition=ItemDefinition.objects.get(slug=item_slug),
                    mk_tier=1,
                    defaults={
                        'price': price,
                        'stock_limit': None,
                        'is_active': True,
                    },
                )
                entry_count += 1
        self.stdout.write(f'Verdant Reach: {entry_count} vendor entries seeded.')

    # ------------------------------------------------------------------
    # The Viridian Ridge & delves (v18 brief 6) — loot, NPCs, spawns, vendors
    # ------------------------------------------------------------------

    def _seed_ridge_loot_tables(self):
        boss_weapons = [
            'iron-sword', 'iron-mace', 'broadsword',
            'battle-axe', 'hunting-bow', 'combat-knife',
        ]
        boss_armor = [
            'leather-cap', 'leather-shoulders', 'leather-vest', 'leather-gloves',
            'leather-belt', 'leather-leggings', 'leather-boots', 'wooden-shield',
        ]
        boss_accessories = [
            f'copper-{kind}-of-{stat}'
            for kind in ('ring', 'amulet')
            for stat in ('strength', 'dexterity', 'endurance',
                         'intelligence', 'wisdom', 'perception')
        ]
        villager_weights = {'common': 85, 'uncommon': 15}
        ridge_gear = [
            ('iron-mace', 0.10, villager_weights, ''),
            ('iron-sword', 0.10, villager_weights, ''),
            ('leather-shoulders', 0.10, villager_weights, ''),
            ('wooden-shield', 0.10, villager_weights, ''),
        ]

        # (table slug, table name, entries); each entry is
        # (item slug, drop_chance, rarity_weights, guaranteed_group).
        tables = [
            ('ridge-gear', 'Ridge Gear', list(ridge_gear)),
            ('ridge-hunter-gear', 'Ridge Hunter Gear',
             ridge_gear + [('battle-axe', 0.10, villager_weights, '')]),
            ('weaver-loot', 'Undercrag Weaver Loot',
             [(slug, 1.0, {'rare': 100}, 'weapon') for slug in boss_weapons]
             + [('insect-carapace', 0.5, {'common': 100}, '')]),
            ('king-loot', 'Chittering King Loot',
             [(slug, 1.0, {'rare': 100}, 'armor') for slug in boss_armor]
             + [('insect-carapace', 0.5, {'common': 100}, '')]),
            ('devourer-loot', 'Crowned Devourer Loot',
             [(slug, 1.0, {'epic': 100}, 'accessory') for slug in boss_accessories]
             + [('insect-carapace', 0.5, {'common': 100}, '')]),
        ]

        for table_slug, table_name, entries in tables:
            table, _ = LootTable.objects.get_or_create(
                slug=table_slug, defaults={'name': table_name},
            )
            for item_slug, drop_chance, weights, group in entries:
                LootTableEntry.objects.get_or_create(
                    loot_table=table,
                    item_definition=ItemDefinition.objects.get(slug=item_slug),
                    defaults={
                        'mk_tier_min': 1,
                        'mk_tier_max': 1,
                        'drop_chance': drop_chance,
                        'guaranteed_group': group,
                        'rarity_weights': weights,
                    },
                )
        self.stdout.write(f'Viridian Ridge: {len(tables)} loot tables seeded.')

    def _seed_ridge_npcs(self):
        # Same tuple shape as _seed_verdant_npcs; see _upsert_npc_definitions.
        npcs = [
            # Surface creatures — passive except the two territorial variants
            ('mountain-goat', 'mountain goat', 'normal', False,
             (70, 13, 12, 14, 2, 2, 10), 6.0, None, 'animal-drops', (0, 0), 1,
             'Shag-coated and slab-shouldered, standing on a slope that should '
             'be impossible, chewing, unimpressed by your entire species.', {}),
            ('mountain-squirrel', 'mountain squirrel', 'normal', False,
             (20, 5, 17, 6, 3, 3, 14), 6.0, None, 'animal-drops', (0, 0), 1,
             'Small, loud, and incandescent with territorial fury. It has '
             'already thrown something at you.', {}),
            ('brown-bear', 'brown bear', 'elite', False,
             (130, 18, 8, 17, 3, 3, 8), 7.0, None, 'animal-drops', (0, 0), 1,
             'A brown bear of the high Ridge — bigger than the valley kind, '
             'and less philosophical about company.', {}),
            ('mountain-lion', 'mountain lion', 'elite', False,
             (120, 15, 17, 13, 3, 3, 14), 8.0, None, 'animal-drops', (0, 0), 1,
             'A high-country lion, long as a bench and fluid as poured shadow. '
             'On the path, there is a truce. You are not always on the path.', {}),
            ('prowling-mountain-lion', 'prowling mountain lion', 'elite', True,
             (150, 17, 19, 14, 3, 3, 15), 9.0, None, 'animal-drops', (0, 0), 1,
             'A lion of the forbidden places, and it is not watching you — it '
             'is already closing. The villagers told you. They always tell '
             'you.', {}),
            ('territorial-brown-bear', 'territorial brown bear', 'elite', True,
             (170, 21, 9, 19, 3, 3, 9), 9.0, None, 'animal-drops', (0, 0), 1,
             'A bear at the scale where the word stops being descriptive. This '
             'ground is claimed, and you are the paperwork.', {}),
            # Villagers — passive
            ('mountain-villager', 'mountain villager', 'normal', False,
             (95, 12, 10, 13, 8, 9, 9), 7.0, None, 'ridge-gear', (8, 20), 5,
             'A villager of the high Ridge, stone-handed and weatherproof, '
             'hospitality and warnings issued in the same breath.', {}),
            ('mountain-hunter', 'mountain hunter', 'normal', False,
             (110, 13, 14, 13, 8, 9, 14), 8.0, None, 'ridge-hunter-gear', (8, 20), 5,
             'A Ridge hunter, bow strung and back never quite to the slope. '
             'They know exactly which grounds are forbidden, and why, and stay '
             'alive by it.', {}),
            # Checkpoint service NPCs — passive
            ('old-brammel', 'Old Brammel the Mender', 'normal', False,
             (95, 12, 10, 13, 8, 9, 9), 7.0, None, 'ridge-gear', (8, 20), 5,
             "Old Brammel came down from Lastlight the year the green light "
             "appeared at the crag's foot, set up a bench, and has been "
             "mending travelers' gear beside it ever since. He calls the "
             'sphere "the little lamp" and considers it excellent company.',
             {'is_repairer': True}),
            ('ridda-the-trader', 'Ridda the Trader', 'normal', False,
             (95, 12, 10, 13, 8, 9, 9), 7.0, None, 'ridge-gear', (10, 24), 5,
             "Ridda trades at the mountains' door: tools, iron, and the things "
             "climbers wish they'd bought lower down. Her prices are fair and "
             'her warnings free.', {}),
            # The Verdant Sphere — the summit sphere
            ('the-verdant-sphere', 'the Verdant Sphere', 'normal', False,
             (1, 1, 1, 1, 1, 1, 1), 1.0, None, None, (0, 0), 1,
             'A sphere of pure deep green, suspended at eye level inside the '
             'stone of the obelisk as though the stone grew around it — and '
             'here, in this garden, perhaps it did. It is the same presence '
             'as the pale one at the Heart of the Convergence, wearing this '
             "zone's color the way light wears a leaf. It does not spin, "
             'pulse, or drift. The garden grows toward it. Stand here long '
             'enough and you will understand the impulse.',
             {'is_unique': True}),
            # Cave insects — aggressive
            ('elder-cave-spider', 'elder cave spider', 'elite', True,
             (110, 15, 18, 12, 3, 3, 14), 7.0, 'ridge-spider', 'insect-drops', (0, 0), 1,
             'A spider grown old in the dark under the mountain, pale as deep '
             'silk and patient as geology.', {}),
            ('elder-cave-centipede', 'elder cave centipede', 'elite', True,
             (130, 17, 16, 14, 3, 3, 12), 8.0, 'ridge-centipede', 'insect-drops', (0, 0), 1,
             'Length beyond reason, armored in segments the size of shields, '
             'older than the villages above it.', {}),
            ('elder-cave-beetle', 'elder cave beetle', 'elite', True,
             (150, 18, 13, 18, 3, 3, 11), 9.0, 'ridge-beetle', 'insect-drops', (0, 0), 1,
             'A beetle at the scale of livestock, chitin black-green, wings '
             'that open with a sound like a door to somewhere worse.', {}),
            # Bosses — aggressive
            ('undercrag-weaver', 'the Undercrag Weaver', 'boss', True,
             (500, 20, 22, 18, 5, 5, 18), 9.0, 'ridge-spider', 'weaver-loot', (150, 400), 10,
             'A spider of architectural size, pale as the generations of silk '
             'it has spun beneath the mountain. High above it, snared in a '
             'cradle of lines, hangs an iron-strapped strongbox it took whole '
             'and keeps for reasons a spider keeps things.',
             {'death_message':
              'The Undercrag Weaver sags into its own silk. High above, the '
              'web-line holding a snared strongbox parts strand by strand — '
              'then all at once, and the box crashes down and bursts open.'}),
            ('chittering-king', 'the Chittering King', 'boss', True,
             (650, 24, 20, 22, 6, 6, 16), 10.0, 'ridge-centipede', 'king-loot', (150, 400), 10,
             'A centipede of dynastic size, coiled in glossy tiers about a '
             'chest scored soft by a thousand legs across uncountable years. '
             'The deep chitters in his name.',
             {'death_message':
              'The Chittering King unclenches, segment by segment, from '
              'around the chest it has coiled about for years. The lid, '
              'scored by a thousand legs, falls open.'}),
            ('crowned-devourer', 'the Crowned Devourer', 'boss', True,
             (850, 27, 18, 27, 7, 7, 15), 10.0, 'ridge-beetle', 'devourer-loot', (400, 1000), 10,
             'Legend, standing on legend: a beetle vast as myth atop a hoard '
             'of every genre the rifts ever spilled, wings holding one '
             'enormous patient chord beneath the light of the Crown itself.',
             {'death_message':
              'The Crowned Devourer crashes down, wings splintering, and the '
              'hoard beneath it shifts — coins and treasures sliding free of '
              'the great shape that will never guard them again.'}),
            # Boss minions — aggressive, spawn-gated on their boss
            ('weavers-brood', "one of the Weaver's brood", 'elite', True,
             (90, 15, 18, 12, 3, 3, 14), 6.0, 'ridge-spider', 'insect-drops', (0, 0), 3,
             "A spider of the Weaver's brood, pale and quick, spun into the "
             'world for exactly this purpose.', {}),
            ('kings-skitterlings', "one of the King's skitterlings", 'elite', True,
             (100, 17, 16, 14, 3, 3, 12), 8.0, 'ridge-centipede', 'insect-drops', (0, 0), 3,
             "A skitterling of the King's court, already terrible, keeping "
             'the rhythm its sovereign conducts.', {}),
            ('devourers-drones', "one of the Devourer's drones", 'elite', True,
             (120, 18, 13, 18, 3, 3, 11), 9.0, 'ridge-beetle', 'insect-drops', (0, 0), 3,
             "A drone of the Devourer's chord, wings tuned to its mother's "
             "note, holding the hoard's perimeter.", {}),
        ]
        self._upsert_npc_definitions(npcs, 'Viridian Ridge')

    def _seed_ridge_spawns(self):
        # (room key, npc slug, count, gating boss slug or None)
        spawns = [
            # Surface — Cragfoot, the ridge legs, villages, aggro grounds
            ('vr-c01', 'verdant-shard', 1, None),
            ('vr-c01', 'old-brammel', 1, None),
            ('vr-c01', 'ridda-the-trader', 1, None),
            ('vr-m02', 'mountain-goat', 1, None),
            ('vr-m04', 'mountain-squirrel', 2, None),
            ('vr-m05', 'mountain-goat', 2, None),
            ('vr-m07', 'brown-bear', 1, None),
            ('vr-m09', 'mountain-goat', 3, None),
            ('vr-m10', 'mountain-squirrel', 3, None),
            ('vr-m11', 'prowling-mountain-lion', 2, None),
            ('vr-st1', 'mountain-villager', 2, None),
            ('vr-st2', 'mountain-villager', 2, None),
            ('vr-m15', 'mountain-goat', 2, None),
            ('vr-m16', 'brown-bear', 1, None),
            ('vr-m17', 'mountain-squirrel', 2, None),
            ('vr-m19', 'mountain-lion', 1, None),
            ('vr-m22', 'mountain-goat', 3, None),
            ('vr-m23', 'mountain-squirrel', 3, None),
            ('vr-m24', 'territorial-brown-bear', 2, None),
            ('vr-hf1', 'mountain-villager', 2, None),
            ('vr-hf2', 'mountain-villager', 2, None),
            ('vr-m28', 'mountain-goat', 2, None),
            ('vr-m29', 'brown-bear', 1, None),
            ('vr-m30', 'mountain-squirrel', 2, None),
            ('vr-m33', 'mountain-lion', 1, None),
            ('vr-m36', 'mountain-goat', 3, None),
            ('vr-m37', 'mountain-squirrel', 3, None),
            ('vr-m38', 'prowling-mountain-lion', 3, None),
            ('vr-m39', 'territorial-brown-bear', 3, None),
            ('vr-ll1', 'mountain-villager', 2, None),
            ('vr-ll2', 'mountain-villager', 1, None),
            ('vr-ll2', 'mountain-hunter', 2, None),
            ('vr-vc1', 'the-verdant-sphere', 1, None),
            # The Undercrag
            ('vr-c5a', 'elder-cave-spider', 1, None),
            ('vr-c5b', 'elder-cave-spider', 2, None),
            ('vr-c5c', 'elder-cave-centipede', 2, None),
            ('vr-c5d', 'elder-cave-spider', 2, None),
            ('vr-c5e', 'elder-cave-beetle', 2, None),
            ('vr-c5f', 'elder-cave-centipede', 1, None),
            ('vr-c5f', 'elder-cave-beetle', 1, None),
            ('vr-c5g', 'elder-cave-spider', 2, None),
            ('vr-c5h', 'elder-cave-spider', 1, None),
            ('vr-c5h', 'elder-cave-centipede', 1, None),
            ('vr-c5i', 'undercrag-weaver', 1, None),
            ('vr-c5i', 'weavers-brood', 3, 'undercrag-weaver'),
            # Chitterdeep
            ('vr-c6a', 'elder-cave-centipede', 1, None),
            ('vr-c6b', 'elder-cave-centipede', 2, None),
            ('vr-c6c', 'elder-cave-beetle', 2, None),
            ('vr-c6d', 'elder-cave-centipede', 2, None),
            ('vr-c6e', 'elder-cave-spider', 2, None),
            ('vr-c6f', 'elder-cave-centipede', 2, None),
            ('vr-c6g', 'elder-cave-beetle', 1, None),
            ('vr-c6g', 'elder-cave-spider', 1, None),
            ('vr-c6h', 'elder-cave-centipede', 2, None),
            ('vr-c6i', 'elder-cave-centipede', 1, None),
            ('vr-c6i', 'elder-cave-beetle', 1, None),
            ('vr-c6j', 'chittering-king', 1, None),
            ('vr-c6j', 'kings-skitterlings', 3, 'chittering-king'),
            # Hollowcrown
            ('vr-c7a', 'elder-cave-beetle', 1, None),
            ('vr-c7b', 'elder-cave-beetle', 2, None),
            ('vr-c7c', 'elder-cave-spider', 2, None),
            ('vr-c7d', 'elder-cave-beetle', 2, None),
            ('vr-c7e', 'elder-cave-centipede', 2, None),
            ('vr-c7f', 'elder-cave-beetle', 2, None),
            ('vr-c7g', 'elder-cave-spider', 1, None),
            ('vr-c7g', 'elder-cave-centipede', 1, None),
            ('vr-c7h', 'elder-cave-beetle', 2, None),
            ('vr-c7i', 'elder-cave-centipede', 1, None),
            ('vr-c7i', 'elder-cave-beetle', 1, None),
            ('vr-c7j', 'elder-cave-beetle', 2, None),
            ('vr-c7k', 'crowned-devourer', 1, None),
            ('vr-c7k', 'devourers-drones', 3, 'crowned-devourer'),
        ]
        for room_key, npc_slug, count, gate_slug in spawns:
            RoomSpawn.objects.get_or_create(
                room=self.rooms[room_key],
                npc_definition=NpcDefinition.objects.get(slug=npc_slug),
                mk_tier=1,
                defaults={
                    'count': count,
                    'is_active': True,
                    'requires_living_npc': (
                        NpcDefinition.objects.get(slug=gate_slug)
                        if gate_slug else None
                    ),
                },
            )
        self.stdout.write(f'Viridian Ridge: {len(spawns)} room spawns seeded.')

    def _seed_ridge_vendors(self):
        vendors = {
            'ridda-the-trader': [
                ('healing-draught', 15),
                ('iron-mace', 80),
                ('wooden-shield', 70),
                ('iron-sword', 75),
                ('leather-cap', 40),
            ],
        }
        entry_count = 0
        for npc_slug, wares in vendors.items():
            npc = NpcDefinition.objects.get(slug=npc_slug)
            for item_slug, price in wares:
                VendorEntry.objects.get_or_create(
                    npc_definition=npc,
                    item_definition=ItemDefinition.objects.get(slug=item_slug),
                    mk_tier=1,
                    defaults={
                        'price': price,
                        'stock_limit': None,
                        'is_active': True,
                    },
                )
                entry_count += 1
        self.stdout.write(f'Viridian Ridge: {entry_count} vendor entries seeded.')
