from django.core.management.base import BaseCommand, CommandError
from apps.shyland.models import (
    Area, Archetype, Character, EffectComponent, EffectDefinition, ItemDefinition,
    NpcDefinition, Origin, Room, RoomSpawn, Zone,
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
        self._wire_exits()
        self._seed_convergence_npcs()
        self._set_character_rooms()

        self._seed_unarmed_pools()
        self._seed_origins()
        self._seed_archetypes()
        self._seed_effects()
        self._seed_items()

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
            'before the city grew up around it. Beyond the tree arch, the light changes — greener, '
            'dimmer, filtered through canopy that begins immediately and thickens fast. The air coming '
            'from that direction is cooler and smells of moss and old wood and living things. A wooden '
            'sign has been nailed to the left tree at eye level. It reads: THE VERDANT REACH. Below '
            'that, in different handwriting, older: Mind the roots.',
            no_exit={
                'north': 'The Verdant Reach gate is sealed. Whatever lies beyond is not yet reachable — but the trees lean toward it as if they remember.',
            },
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
        for src, direction, dst in PATH_EDGES + self._ring_edges():
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

    # ------------------------------------------------------------------
    # Character starting rooms
    # ------------------------------------------------------------------

    def _set_character_rooms(self):
        heart = self.rooms['heart']
        moved_null = Character.objects.filter(current_room__isnull=True).update(current_room=heart)
        recall_set = Character.objects.filter(recall_room__isnull=True).update(recall_room=heart)
        # Also update any characters still in old placeholder rooms
        moved_outside = Character.objects.exclude(
            current_room__zone__slug='the-convergence'
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
        ]).count()
        self._check(f'9 NPC definitions exist (found {npc_count})', npc_count == 9)

        spawn_count = RoomSpawn.objects.filter(room__zone__slug='the-convergence').count()
        self._check(f'9 RoomSpawns in The Convergence (found {spawn_count})', spawn_count == 9)

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

        if self._failures:
            raise CommandError(f'{len(self._failures)} verification check(s) failed.')
        self.stdout.write(self.style.SUCCESS('All verification checks passed.'))

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
            # Accessory
            {
                'slug': 'copper-ring',
                'name': 'Copper Ring',
                'item_type': 'accessory',
                'genre_tag': 'fantasy',
                'valid_slots': ['RING'],
                'scaling_base': 2.0,
                'scaling_factor': 0.8,
                'takes_durability_loss': False,
                'durability_table': [],
                'primary_stats': [{'stat': 'wis', 'base': 1.0, 'factor': 0.5}],
                'secondary_stat_pool': [
                    {'stat': 'int', 'base': 0.5, 'factor': 0.2},
                    {'stat': 'magic_resist', 'base': 0.3, 'factor': 0.1},
                ],
                'description': 'A simple copper band. Faintly warm to the touch.',
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

        self.stdout.write(self.style.SUCCESS(
            f'Item seed complete: {count_created} new ItemDefinitions created.'
        ))
