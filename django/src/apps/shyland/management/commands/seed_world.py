from django.core.management.base import BaseCommand
from apps.shyland.models import (
    Area, Archetype, EffectComponent, EffectDefinition, ItemDefinition, LootTable, LootTableEntry,
    NpcDefinition, NpcEffect, NpcInstance, Origin, Room, Zone,
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

        center, _ = Room.objects.update_or_create(
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

        north, _ = Room.objects.update_or_create(
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

        south, _ = Room.objects.update_or_create(
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

        east, _ = Room.objects.update_or_create(
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

        west, _ = Room.objects.update_or_create(
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

        convergence_area, _ = Area.objects.get_or_create(
            slug='the-fracture-point-plaza',
            defaults={
                'zone': zone,
                'name': 'The Fracture Point Plaza',
                'area_description': (
                    'The air here shimmers faintly, a residual effect of The Fracture '
                    'that created this place. Travelers from a dozen different realities '
                    'pass through the plaza — a knight in plate armor haggles with a '
                    'woman in a leather duster, and somewhere nearby a generator hums '
                    'beneath the sound of a lute. This is where all roads meet.'
                ),
            }
        )

        Room.objects.filter(zone=zone).update(area=convergence_area)

        self.stdout.write(self.style.SUCCESS(
            f'Seeded: zone "{zone.name}" with 5 rooms. Starting room PK={center.pk}.'
        ))
        self.stdout.write(f'  Set new characters\' current_room to pk={center.pk}.')
        self.stdout.write(f'  Area "{convergence_area.name}" assigned to all {zone.name} rooms.')

        self._seed_unarmed_pools()
        self._seed_origins()
        self._seed_archetypes()
        self._seed_effects()
        self._seed_items()

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
            {'slug': 'highborn',    'name': 'Highborn',    'acuity_baseline': 1.0,  'acuity_band_low': 0.85, 'acuity_band_high': 1.15},
            {'slug': 'feral',       'name': 'Feral',       'acuity_baseline': 0.95, 'acuity_band_low': 0.80, 'acuity_band_high': 1.10},
            {'slug': 'streetborn',  'name': 'Streetborn',  'acuity_baseline': 1.0,  'acuity_band_low': 0.85, 'acuity_band_high': 1.15},
            {'slug': 'irradiated',  'name': 'Irradiated',  'acuity_baseline': 0.90, 'acuity_band_low': 0.75, 'acuity_band_high': 1.05},
            {'slug': 'undying',     'name': 'Undying',     'acuity_baseline': 0.80, 'acuity_band_low': 0.65, 'acuity_band_high': 1.00},
            {'slug': 'machinekind', 'name': 'Machinekind', 'acuity_baseline': 1.05, 'acuity_band_low': 0.90, 'acuity_band_high': 1.20},
            {'slug': 'voidtouched', 'name': 'Voidtouched', 'acuity_baseline': 0.70, 'acuity_band_low': 0.40, 'acuity_band_high': 1.30},
        ]
        for data in origins:
            _, created = Origin.objects.get_or_create(
                slug=data['slug'],
                defaults={
                    'name': data['name'],
                    'description': '',
                    'acuity_baseline': data['acuity_baseline'],
                    'acuity_band_low': data['acuity_band_low'],
                    'acuity_band_high': data['acuity_band_high'],
                },
            )
            self.stdout.write(f'  Origin "{data["name"]}" {"created" if created else "exists"}.')

    def _seed_archetypes(self):
        archetypes = [
            {'slug': 'blade',     'name': 'Blade',     'primary_stat_1': 'str', 'primary_stat_2': 'dex'},
            {'slug': 'bulwark',   'name': 'Bulwark',   'primary_stat_1': 'str', 'primary_stat_2': 'end'},
            {'slug': 'shade',     'name': 'Shade',     'primary_stat_1': 'dex', 'primary_stat_2': 'int'},
            {'slug': 'conduit',   'name': 'Conduit',   'primary_stat_1': 'int', 'primary_stat_2': 'wis'},
            {'slug': 'warden',    'name': 'Warden',    'primary_stat_1': 'wis', 'primary_stat_2': 'end'},
            {'slug': 'gunner',    'name': 'Gunner',    'primary_stat_1': 'dex', 'primary_stat_2': 'per'},
            {'slug': 'machinist', 'name': 'Machinist', 'primary_stat_1': 'int', 'primary_stat_2': 'dex'},
        ]
        for data in archetypes:
            _, created = Archetype.objects.get_or_create(
                slug=data['slug'],
                defaults={
                    'name': data['name'],
                    'description': '',
                    'primary_stat_1': data['primary_stat_1'],
                    'primary_stat_2': data['primary_stat_2'],
                },
            )
            self.stdout.write(f'  Archetype "{data["name"]}" {"created" if created else "exists"}.')

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

        self._seed_npcs()

    def _seed_npcs(self):
        loot_table, created = LootTable.objects.get_or_create(
            slug='goblin-drops',
            defaults={'name': 'Goblin Drops'},
        )
        self.stdout.write(f'  LootTable "Goblin Drops" {"created" if created else "exists"}.')

        iron_sword_def = ItemDefinition.objects.get(slug='iron-sword')
        healing_draught_def = ItemDefinition.objects.get(slug='healing-draught')

        _, created = LootTableEntry.objects.get_or_create(
            loot_table=loot_table,
            item_definition=iron_sword_def,
            defaults={
                'mk_tier_min': 1,
                'mk_tier_max': 3,
                'drop_chance': 0.5,
                'rarity_weights': {'common': 70, 'uncommon': 25, 'rare': 5},
            },
        )
        self.stdout.write(f'  LootTableEntry iron-sword {"created" if created else "exists"}.')

        _, created = LootTableEntry.objects.get_or_create(
            loot_table=loot_table,
            item_definition=healing_draught_def,
            defaults={
                'mk_tier_min': 1,
                'mk_tier_max': 2,
                'drop_chance': 0.8,
                'rarity_weights': {'common': 100},
            },
        )
        self.stdout.write(f'  LootTableEntry healing-draught {"created" if created else "exists"}.')

        goblin_def, created = NpcDefinition.objects.get_or_create(
            slug='goblin-scout',
            defaults={
                'name': 'a goblin scout',
                'description': (
                    'A wiry creature with darting eyes and quick hands. '
                    'It watches you with undisguised hunger.'
                ),
                'genre_tag': 'fantasy',
                'is_aggressive': True,
                'is_unique': False,
                'wanders': False,
                'base_vitality': 30,
                'base_str': 8,
                'base_dex': 12,
                'base_end': 8,
                'base_int': 6,
                'base_wis': 6,
                'base_per': 10,
                'scaling_factor': 1.0,
                'loot_table': loot_table,
                'currency_drop_min': 3,
                'currency_drop_max': 10,
                'respawn_minutes': 15,
            },
        )
        self.stdout.write(f'  NpcDefinition "a goblin scout" {"created" if created else "exists"}.')

        fracture_point = Room.objects.get(name='The Fracture Point', zone__slug='the-convergence')

        _, created = NpcInstance.objects.get_or_create(
            definition=goblin_def,
            defaults={
                'current_room': fracture_point,
                'spawn_room': fracture_point,
                'mk_tier': 1,
                'vitality_current': goblin_def.base_vitality,
                'vitality_max': goblin_def.base_vitality,
                'is_alive': True,
            },
        )
        self.stdout.write(
            f'  NpcInstance goblin-scout in The Fracture Point {"created" if created else "exists"}.'
        )

        # --- Training Dummy ---
        dummy_def, created = NpcDefinition.objects.get_or_create(
            slug='training-dummy',
            defaults={
                'name': 'Training Dummy',
                'description': 'A battered wooden dummy used for combat practice. It does not fight back.',
                'genre_tag': 'fantasy',
                'is_aggressive': False,
                'is_unique': False,
                'wanders': False,
                'base_vitality': 20,
                'base_str': 1,
                'base_dex': 1,
                'base_end': 1,
                'base_int': 1,
                'base_wis': 1,
                'base_per': 1,
                'scaling_factor': 1.0,
                'currency_drop_min': 0,
                'currency_drop_max': 0,
                'respawn_minutes': 1,
            },
        )
        self.stdout.write(f'  NpcDefinition "Training Dummy" {"created" if created else "exists"}.')

        _, created = NpcInstance.objects.get_or_create(
            definition=dummy_def,
            spawn_room=fracture_point,
            defaults={
                'current_room': fracture_point,
                'mk_tier': 1,
                'vitality_current': dummy_def.base_vitality,
                'vitality_max': dummy_def.base_vitality,
                'is_alive': True,
            },
        )
        self.stdout.write(
            f'  NpcInstance training-dummy in The Fracture Point {"created" if created else "exists"}.'
        )

        # --- Fracture Wraith ---
        eastern_bazaar = Room.objects.get(name='The Eastern Bazaar', zone__slug='the-convergence')
        wraith_poison_effect = EffectDefinition.objects.filter(slug='fracture-wraith-poison').first()

        wraith_def, created = NpcDefinition.objects.get_or_create(
            slug='fracture-wraith',
            defaults={
                'name': 'Fracture Wraith',
                'description': (
                    'A ghostly remnant of the Fracture, drawn to the residual energy of the plaza. '
                    'Its touch chills the soul.'
                ),
                'genre_tag': 'gothic',
                'is_aggressive': True,
                'is_unique': False,
                'wanders': False,
                'base_vitality': 15,
                'base_str': 4,
                'base_dex': 6,
                'base_end': 3,
                'base_int': 5,
                'base_wis': 3,
                'base_per': 4,
                'scaling_factor': 1.0,
                'currency_drop_min': 2,
                'currency_drop_max': 8,
                'respawn_minutes': 5,
            },
        )
        self.stdout.write(f'  NpcDefinition "Fracture Wraith" {"created" if created else "exists"}.')

        if wraith_poison_effect:
            _, created = NpcEffect.objects.get_or_create(
                npc_definition=wraith_def,
                effect_definition=wraith_poison_effect,
                defaults={'effect_chance': 0.30},
            )
            self.stdout.write(
                f'  NpcEffect Fracture Wraith → Fracture Wraith Poison {"created" if created else "exists"}.'
            )

        _, created = NpcInstance.objects.get_or_create(
            definition=wraith_def,
            spawn_room=eastern_bazaar,
            defaults={
                'current_room': eastern_bazaar,
                'mk_tier': 1,
                'vitality_current': wraith_def.base_vitality,
                'vitality_max': wraith_def.base_vitality,
                'is_alive': True,
            },
        )
        self.stdout.write(
            f'  NpcInstance fracture-wraith in The Eastern Bazaar {"created" if created else "exists"}.'
        )

        self.stdout.write(self.style.SUCCESS('NPC seed complete.'))
