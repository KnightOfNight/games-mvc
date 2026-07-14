from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower

COMBAT_ROUND_TICKS    = 3
DYING_DURATION_SECS   = 30
FLEE_COOLDOWN_TICKS   = 3
STALE_SESSION_SECS    = 30
XP_PENALTY_MIN_LEVEL  = 10
DEATH_DURABILITY_LOSS = 10.0
ACUITY_DRIFT_RATE     = 0.01
STAT_POINTS_PER_LEVEL = 5
VITALITY_REGEN_SECS   = 120   # seconds to regen full Vitality from zero out of combat
LONGEVITY_REGEN_SECS  = 3600  # seconds to regen full Longevity from zero out of combat

# v19 brief 9: NPC dialogue engine timing. Slower than combat's 1-tick
# cadence, kept sociable rather than interrupty.
DIALOGUE_FIRST_DELAY_TICKS = 2
DIALOGUE_STAGGER_TICKS     = 2
DIALOGUE_RECENT_EXCLUDE    = 1

class Zone(models.Model):
    DANGER_BEGINNER = 'beginner'
    DANGER_INTERMEDIATE = 'intermediate'
    DANGER_ADVANCED = 'advanced'
    DANGER_SANCTUARY = 'sanctuary'
    DANGER_ALL_LEVELS = 'all_levels'
    DANGER_CHOICES = [
        (DANGER_BEGINNER, 'Beginner'),
        (DANGER_INTERMEDIATE, 'Intermediate'),
        (DANGER_ADVANCED, 'Advanced'),
        (DANGER_SANCTUARY, 'Sanctuary'),
        (DANGER_ALL_LEVELS, 'All Levels'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    genre_tone = models.CharField(max_length=100)
    danger_level = models.CharField(max_length=20, choices=DANGER_CHOICES)
    is_pvp_zone = models.BooleanField(default=False)
    is_scaled = models.BooleanField(default=False)
    description = models.TextField()

    def __str__(self):
        return self.name


class Area(models.Model):
    """
    A named grouping of rooms within a zone, sharing a common ambient context.

    Areas sit between Zone and Room in the world hierarchy:
        Zone → Area → Room

    The area_description provides shared atmospheric text — the sounds, smells,
    and feel of the location — that applies to all rooms within the area.
    Individual rooms add their specific detail on top.

    Rooms are not required to belong to an area (area is nullable on Room).
    """

    zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        related_name='areas',
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    area_description = models.TextField(
        blank=True,
        help_text=(
            'Shared atmospheric text for all rooms in this area. '
            'Describes the general feel, sounds, smells, and environment. '
            'Shown alongside the room-specific description.'
        ),
    )

    class Meta:
        ordering = ['zone', 'name']

    def __str__(self):
        return f'{self.zone.name} / {self.name}'


class Room(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='rooms')
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rooms',
        help_text='Optional. Groups this room with others sharing a common atmosphere.',
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    brief_description = models.CharField(max_length=500)
    # v20 brief 1: coordinates are the map's positional source of truth, in
    # per-zone map-space (one room per (zone, x, y, z) cell). z is a map
    # plane index, NOT elevation. Exits remain the connectivity source of
    # truth; every unflagged intra-zone cardinal exit must land grid-adjacent
    # at the same z (north (0,+1,0), south (0,-1,0), east (+1,0,0),
    # west (-1,0,0)) — enforced by seed verification.
    coord_x = models.IntegerField(default=0)
    coord_y = models.IntegerField(default=0)
    coord_z = models.IntegerField(default=0)

    exit_north = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_south')
    exit_south = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_north')
    exit_east = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_west')
    exit_west = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_east')
    exit_up = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_below')
    exit_down = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_above')

    # v20 brief 1: MapFrag boundary flags, cardinals only (up/down exits
    # always break fragments and need no flag). An undirected edge is a
    # boundary if either side is flagged; the seeder always sets both sides
    # and verification enforces the symmetry. A flagged exit is exempt from
    # the grid-adjacency geometry invariant.
    exit_north_boundary = models.BooleanField(default=False)
    exit_south_boundary = models.BooleanField(default=False)
    exit_east_boundary = models.BooleanField(default=False)
    exit_west_boundary = models.BooleanField(default=False)

    no_exit_north_msg = models.CharField(max_length=255, blank=True, default='')
    no_exit_south_msg = models.CharField(max_length=255, blank=True, default='')
    no_exit_east_msg  = models.CharField(max_length=255, blank=True, default='')
    no_exit_west_msg  = models.CharField(max_length=255, blank=True, default='')
    no_exit_up_msg    = models.CharField(max_length=255, blank=True, default='')
    no_exit_down_msg  = models.CharField(max_length=255, blank=True, default='')

    flag_safe = models.BooleanField(default=False)
    flag_pvp = models.BooleanField(default=False)
    flag_dark = models.BooleanField(default=False)
    flag_indoors = models.BooleanField(default=False)
    flag_water = models.BooleanField(default=False)
    flag_no_recall = models.BooleanField(default=False)
    flag_radiation = models.BooleanField(default=False)
    flag_holy = models.BooleanField(default=False)
    flag_magic_dead = models.BooleanField(default=False)
    flag_scaled = models.BooleanField(default=False)

    def exits(self):
        result = {}
        for direction in ('north', 'south', 'east', 'west', 'up', 'down'):
            if getattr(self, f'exit_{direction}_id') is not None:
                result[direction] = True
        return result

    def __str__(self):
        return f'{self.name} ({self.zone.name})'


class UnarmedMessagePool(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class UnarmedMessage(models.Model):
    pool = models.ForeignKey(UnarmedMessagePool, on_delete=models.CASCADE, related_name='messages')
    template = models.TextField(
        help_text='Python format string. Use {target} for the target name. Example: "You punch {target}."'
    )
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.pool.name}: {self.template[:60]}'


class Origin(models.Model):
    name             = models.CharField(max_length=100)
    slug             = models.SlugField(unique=True)
    description      = models.TextField(blank=True)
    acuity_baseline  = models.FloatField()
    acuity_band_low  = models.FloatField()
    acuity_band_high = models.FloatField()
    attire_material  = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Archetype(models.Model):
    STAT_CHOICES = [
        ('str', 'STR'), ('dex', 'DEX'), ('end', 'END'),
        ('int', 'INT'), ('wis', 'WIS'), ('per', 'PER'),
    ]

    name                 = models.CharField(max_length=100)
    slug                 = models.SlugField(unique=True)
    description          = models.TextField(blank=True)
    primary_stat_1       = models.CharField(max_length=3, choices=STAT_CHOICES)
    primary_stat_2       = models.CharField(max_length=3, choices=STAT_CHOICES)
    attire_silhouette    = models.CharField(max_length=200, blank=True, default='')
    unarmed_message_pool = models.ForeignKey(
        UnarmedMessagePool,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='archetypes',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Character(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shyland_character')
    name = models.CharField(max_length=20)
    origin = models.ForeignKey(Origin, on_delete=models.PROTECT, related_name='characters')
    archetype = models.ForeignKey(Archetype, on_delete=models.PROTECT, related_name='characters')
    level = models.IntegerField(default=1)
    xp = models.IntegerField(default=0)
    current_room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL, related_name='characters')
    recall_room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL, related_name='recall_characters')

    stat_str = models.IntegerField(default=10)
    stat_dex = models.IntegerField(default=10)
    stat_end = models.IntegerField(default=10)
    stat_int = models.IntegerField(default=10)
    stat_wis = models.IntegerField(default=10)
    stat_per = models.IntegerField(default=10)

    vitality_current = models.IntegerField(default=100)
    vitality_max = models.IntegerField(default=100)
    acuity_current  = models.FloatField(default=1.0)
    acuity_baseline = models.FloatField(default=1.0)
    acuity_band_low = models.FloatField(default=0.8)
    acuity_band_high = models.FloatField(default=1.2)
    longevity_current = models.IntegerField(default=100)
    longevity_max = models.IntegerField(default=100)

    copper = models.BigIntegerField(default=0)
    unspent_stat_points = models.IntegerField(default=0)

    is_hardcore = models.BooleanField(default=False)
    is_dead = models.BooleanField(default=False)
    is_dying    = models.BooleanField(default=False)
    dying_since = models.DateTimeField(null=True, blank=True)
    brief_mode = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # Uniqueness must be case-insensitive: players are told a name is
            # taken regardless of casing, so the DB has to enforce the same rule
            # for every write path (creator form, admin, shell).
            models.UniqueConstraint(
                Lower('name'),
                name='shyland_character_name_ci_unique',
                violation_error_message='That name is already taken.',
            ),
        ]

    def clean(self):
        self.name = (self.name or '').strip()

    def __str__(self):
        return self.name


class RoomVisit(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='room_visits')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='visits')
    visited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('character', 'room')


class EffectDefinition(models.Model):
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


COMPONENT_TYPE_CHOICES = [
    ('restore_vitality',   'Restore Vitality'),
    ('restore_acuity',     'Restore Acuity'),
    ('restore_longevity',  'Restore Longevity'),
    ('dot_vitality',       'DoT Vitality'),
    ('dot_acuity',         'DoT Acuity'),
    ('dot_longevity',      'DoT Longevity'),
    ('hot_vitality',       'HoT Vitality'),
    ('hot_acuity',         'HoT Acuity'),
    ('hot_longevity',      'HoT Longevity'),
    ('shift_acuity_high',  'Shift Acuity High'),
    ('shift_acuity_low',   'Shift Acuity Low'),
    ('stat_bonus',         'Stat Bonus'),
    ('stat_penalty',       'Stat Penalty'),
    ('curse_generic',      'Curse Generic'),
    ('durability_restore', 'Durability Restore'),
]

STAT_TARGET_CHOICES = [
    ('str', 'STR'),
    ('dex', 'DEX'),
    ('end', 'END'),
    ('int', 'INT'),
    ('wis', 'WIS'),
    ('per', 'PER'),
]


class EffectComponent(models.Model):
    definition        = models.ForeignKey(
                            'EffectDefinition', on_delete=models.CASCADE,
                            related_name='components')
    component_type    = models.CharField(max_length=30, choices=COMPONENT_TYPE_CHOICES)
    target_stat       = models.CharField(max_length=10, blank=True,
                            choices=STAT_TARGET_CHOICES)
    magnitude_base    = models.FloatField()
    magnitude_scaling = models.FloatField(default=0.0)
    duration_base     = models.FloatField(default=0.0)
    duration_scaling  = models.FloatField(default=0.0)
    order             = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.definition.name} — {self.component_type}"

    def is_instantaneous(self):
        return self.duration_base == 0.0 and self.duration_scaling == 0.0

    def computed_magnitude(self, mk_tier):
        return self.magnitude_base + (self.magnitude_scaling * mk_tier)

    def computed_duration(self, mk_tier):
        return self.duration_base + (self.duration_scaling * mk_tier)


class ItemDefinition(models.Model):
    WEAPON = 'weapon'
    ARMOR = 'armor'
    ACCESSORY = 'accessory'
    CONSUMABLE = 'consumable'
    BAG = 'bag'
    READABLE = 'readable'
    KEY = 'key'
    MATERIAL = 'material'
    ITEM_TYPE_CHOICES = [
        (WEAPON, 'Weapon'),
        (ARMOR, 'Armor'),
        (ACCESSORY, 'Accessory'),
        (CONSUMABLE, 'Consumable'),
        (BAG, 'Bag'),
        (READABLE, 'Readable'),
        (KEY, 'Key'),
        (MATERIAL, 'Material'),
    ]

    FANTASY = 'fantasy'
    CYBER = 'cyber'
    WASTELAND = 'wasteland'
    GOTHIC = 'gothic'
    STEAM = 'steam'
    COSMIC = 'cosmic'
    GENRE_TAG_CHOICES = [
        (FANTASY, 'Fantasy'),
        (CYBER, 'Cyber'),
        (WASTELAND, 'Wasteland'),
        (GOTHIC, 'Gothic'),
        (STEAM, 'Steam'),
        (COSMIC, 'Cosmic'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    genre_tag = models.CharField(max_length=20, choices=GENRE_TAG_CHOICES)
    description = models.TextField()

    base_value = models.BigIntegerField(
        default=1,
        help_text='Authored worth in copper at Mk 1, Common. Item value = '
                  'base_value × mk_tier × rarity multiplier. Sale price is '
                  'one third of value.',
    )

    scaling_base = models.FloatField()
    scaling_factor = models.FloatField()

    damage_spread = models.FloatField(null=True, blank=True)
    is_ranged = models.BooleanField(default=False)

    valid_slots = models.JSONField(default=list)
    is_two_handed = models.BooleanField(default=False)

    takes_durability_loss = models.BooleanField(default=True)
    durability_table = models.JSONField(default=list)

    carry_bonus = models.IntegerField(default=0)

    primary_stats = models.JSONField(default=list)
    secondary_stat_pool = models.JSONField(default=list)

    effect = models.ForeignKey(
        'EffectDefinition',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='items',
    )
    is_cursed_template = models.BooleanField(default=False)

    mystery_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=(
            "Name shown to players before identification. "
            "e.g. 'an unknown sword', 'a fragment of something'. "
            "If blank, falls back to 'an unidentified <item_type>'."
        )
    )
    mystery_description = models.TextField(
        blank=True,
        help_text=(
            "Description shown on examine before identification. "
            "Can contain lore, atmosphere, or deliberate misdirection. "
            "If blank, falls back to 'You can't determine anything about this item.'"
        )
    )
    suppress_mk_suffix = models.BooleanField(
        default=False,
        help_text='If True, display names never show the "Mk N" suffix. '
                  'Used for tier-material items (copper/silver/gold/platinum) '
                  'whose material name already conveys the tier.',
    )

    def __str__(self):
        return self.name


class ItemInstance(models.Model):
    COMMON = 'common'
    UNCOMMON = 'uncommon'
    RARE = 'rare'
    EPIC = 'epic'
    LEGENDARY = 'legendary'
    ARTIFACT = 'artifact'
    RARITY_CHOICES = [
        (COMMON, 'Common'),
        (UNCOMMON, 'Uncommon'),
        (RARE, 'Rare'),
        (EPIC, 'Epic'),
        (LEGENDARY, 'Legendary'),
        (ARTIFACT, 'Artifact'),
    ]

    definition = models.ForeignKey(
        'ItemDefinition',
        on_delete=models.CASCADE,
        related_name='instances',
    )
    owner = models.ForeignKey(
        'Character',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='inventory',
    )
    current_room = models.ForeignKey(
        'Room',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='items',
    )

    mk_tier = models.IntegerField()
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES)

    rolled_primary_stats = models.JSONField(default=list)
    rolled_secondary_stats = models.JSONField(default=list)

    damage_midpoint = models.FloatField(null=True, blank=True)
    damage_spread = models.FloatField(null=True, blank=True)

    durability_current = models.FloatField(default=100.0)
    is_broken = models.BooleanField(default=False)

    is_soulbound = models.BooleanField(default=False)
    soulbound_to = models.ForeignKey(
        'Character',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='soulbound_items',
    )

    is_equipped = models.BooleanField(default=False)
    equipped_slot = models.CharField(max_length=20, blank=True)

    is_cursed = models.BooleanField(default=False)
    curse_identified = models.BooleanField(default=False)
    active_curse = models.ForeignKey(
        'EffectInstance',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='cursed_item',
    )

    is_artifact = models.BooleanField(default=False)

    is_identified = models.BooleanField(
        default=True,
        help_text=(
            "Whether this item's true nature is known to its current holder. "
            "Defaults True — set False on items that should be mysterious. "
            "Resets to False when the item is dropped."
        )
    )
    is_unidentifiable = models.BooleanField(
        default=False,
        help_text=(
            "If True, no in-game mechanism can ever identify this item. "
            "Set by super users only on specific instances. "
            "Intended for one-of-a-kind mystery Artifacts."
        )
    )

    created_at = models.DateTimeField(auto_now_add=True)

    corpse = models.ForeignKey(
        'Corpse',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='contents',
    )

    def save(self, *args, **kwargs):
        non_null = sum([
            self.owner_id is not None,
            self.current_room_id is not None,
            self.corpse_id is not None,
        ])
        if non_null > 1:
            raise ValidationError(
                "ItemInstance must be in exactly one location: owner, current_room, or corpse. "
                f"Got {non_null} non-null location fields."
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.rarity} {self.definition.name} Mk {self.mk_tier}'


class EffectInstance(models.Model):
    definition = models.ForeignKey(
        'EffectDefinition',
        on_delete=models.CASCADE,
        related_name='instances',
    )
    target = models.ForeignKey(
        'Character',
        on_delete=models.CASCADE,
        related_name='active_effects',
    )
    mk_tier    = models.IntegerField(default=1)
    is_active  = models.BooleanField(default=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    removed_by = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f'{self.definition.name} on {self.target}'


class EffectComponentInstance(models.Model):
    effect_instance = models.ForeignKey(
                          'EffectInstance', on_delete=models.CASCADE,
                          related_name='component_instances')
    component       = models.ForeignKey(
                          'EffectComponent', on_delete=models.CASCADE)
    magnitude       = models.FloatField()
    expires_at      = models.DateTimeField(null=True, blank=True)
    is_active       = models.BooleanField(default=True)
    removed_by      = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return (f"{self.effect_instance.definition.name} / "
                f"{self.component.component_type}")


class LootTable(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class LootTableEntry(models.Model):
    loot_table      = models.ForeignKey(LootTable, on_delete=models.CASCADE, related_name='entries')
    item_definition = models.ForeignKey('ItemDefinition', on_delete=models.CASCADE)
    mk_tier_min     = models.IntegerField()
    mk_tier_max     = models.IntegerField()
    drop_chance     = models.FloatField(help_text="0.0 to 1.0. Rolled independently per entry.")
    guaranteed_group = models.CharField(
        max_length=40, blank=True, default='',
        help_text='Optional group label (e.g. "weapon"). At roll time, each '
                  'distinct group in a table yields EXACTLY ONE of its entries, '
                  'chosen with drop_chance as relative weight. Grouped entries '
                  'do not make independent drop rolls. Blank = normal '
                  'independent roll.',
    )
    rarity_weights  = models.JSONField(
        default=dict,
        help_text='Dict of rarity → weight. Keys: common, uncommon, rare, epic, legendary. Must sum to 100.'
    )

    def clean(self):
        total = sum(self.rarity_weights.values())
        if total != 100:
            raise ValidationError(f'rarity_weights must sum to 100, got {total}.')

    def __str__(self):
        return f"{self.loot_table.name} — {self.item_definition.name} ({self.drop_chance*100:.0f}%)"


class NpcDefinition(models.Model):
    GENRE_TAG_CHOICES = [
        ('fantasy',   'Fantasy'),
        ('cyber',     'Cyber'),
        ('wasteland', 'Wasteland'),
        ('gothic',    'Gothic'),
        ('steam',     'Steam'),
        ('cosmic',    'Cosmic'),
    ]

    name            = models.CharField(max_length=200)
    slug            = models.SlugField(unique=True)
    description     = models.TextField(help_text="Shown when a player examines the NPC.")
    genre_tag       = models.CharField(max_length=20, choices=GENRE_TAG_CHOICES)

    COMBAT_TIER_CHOICES = [
        ('normal',     'Normal'),
        ('elite',      'Elite'),
        ('champion',   'Champion'),
        ('boss',       'Boss'),
        ('world_boss', 'World Boss'),
    ]

    is_aggressive   = models.BooleanField(default=False, help_text="Attacks players on sight.")
    is_unique       = models.BooleanField(default=False, help_text="One instance only; no respawn.")
    wanders         = models.BooleanField(default=False, help_text="Moves between rooms. Not yet implemented.")
    is_repairer     = models.BooleanField(
        default=False,
        help_text='This NPC offers repair services. The repair command routes '
                  'to a living repairer in the room.',
    )
    is_fixture      = models.BooleanField(
        default=False,
        help_text='Displayed in the room\'s "What\'s here?" section instead of '
                  '"Who\'s here?". Purely a display distinction.',
    )
    attackable      = models.BooleanField(
        default=True,
        help_text='If False, this NPC may never be targeted, engaged, or hold '
                  'aggro. Independent of room safe-flag mechanics.',
    )

    combat_tier = models.CharField(
        max_length=20,
        choices=COMBAT_TIER_CHOICES,
        default='normal',
        help_text="Combat role tier. Used for display and future AI/balance logic.",
    )

    base_vitality   = models.IntegerField()
    base_str        = models.IntegerField()
    base_dex        = models.IntegerField()
    base_end        = models.IntegerField()
    base_int        = models.IntegerField()
    base_wis        = models.IntegerField()
    base_per        = models.IntegerField()
    scaling_factor  = models.FloatField(default=1.0, help_text="Stat multiplier per Mk tier.")

    loot_table          = models.ForeignKey(
        LootTable, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Loot table rolled on death. Null = no item drops."
    )
    unarmed_message_pool = models.ForeignKey(
        'UnarmedMessagePool',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='npc_definitions',
    )
    currency_drop_min   = models.IntegerField(default=0, help_text="Minimum copper drop (before Mk scaling).")
    currency_drop_max   = models.IntegerField(default=0, help_text="Maximum copper drop (before Mk scaling).")

    respawn_minutes = models.IntegerField(default=30, help_text="Ignored if is_unique=True.")

    death_message = models.TextField(
        blank=True, default='',
        help_text='Optional. Broadcast once to the room at the moment this NPC '
                  'dies, before corpse/loot output. Used for boss narrative '
                  'reveals (e.g. a guarded chest splitting open). Blank = no '
                  'extra message.',
    )

    def __str__(self):
        return self.name


class NpcInstance(models.Model):
    definition       = models.ForeignKey(NpcDefinition, on_delete=models.CASCADE, related_name='instances')
    current_room     = models.ForeignKey('Room', null=True, blank=True, on_delete=models.SET_NULL, related_name='npcs')
    spawn_room       = models.ForeignKey(
        'Room', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='npc_spawns',
        help_text="The room this NPC spawns into. Used for respawn. Set at creation time.",
    )
    mk_tier          = models.IntegerField(default=1)
    vitality_current = models.IntegerField()
    vitality_max     = models.IntegerField()
    is_alive         = models.BooleanField(default=True)
    spawned_at       = models.DateTimeField(auto_now_add=True)
    respawn_at       = models.DateTimeField(null=True, blank=True, help_text="Set on death. Null while alive.")

    @property
    def name(self):
        return self.definition.name

    def __str__(self):
        return f"{self.definition.name} (Mk {self.mk_tier}, room {self.current_room_id})"


CORPSE_DECAY_MINUTES = 10


class Corpse(models.Model):
    npc_definition    = models.ForeignKey(
        NpcDefinition, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Source NPC definition. SET_NULL so corpse survives definition deletion."
    )
    npc_name_snapshot = models.CharField(max_length=200, help_text="NPC name captured at death. Stable reference.")
    current_room      = models.ForeignKey('Room', null=True, blank=True, on_delete=models.SET_NULL, related_name='corpses')
    killed_by         = models.ForeignKey('Character', null=True, blank=True, on_delete=models.SET_NULL, related_name='kills')
    created_at        = models.DateTimeField(auto_now_add=True)
    decay_at          = models.DateTimeField(help_text="Corpse and all contents deleted at this time. Sweep deferred to tick engine.")
    copper_drop       = models.BigIntegerField(default=0, help_text="Copper to transfer to killer on first loot. Set at death.")

    @property
    def display_name(self):
        return f"the corpse of {self.npc_name_snapshot}"

    def __str__(self):
        return f"Corpse of {self.npc_name_snapshot} (room {self.current_room_id})"


class NpcEffect(models.Model):
    npc_definition    = models.ForeignKey(NpcDefinition, on_delete=models.CASCADE, related_name='effects')
    effect_definition = models.ForeignKey(EffectDefinition, on_delete=models.CASCADE)
    effect_chance     = models.FloatField(default=1.0)

    def __str__(self):
        return f"{self.npc_definition.name} → {self.effect_definition.name} ({self.effect_chance * 100:.0f}%)"

    class Meta:
        ordering = ['npc_definition', 'effect_definition']


class RoomSpawn(models.Model):
    """
    Configuration record declaring that a room should contain a certain number
    of live instances of a given NPC definition at a given Mk tier.

    The tick engine uses this as the source of truth for NPC population.
    It compares the desired count against the current count of live + dead
    NpcInstance rows for this definition/room/mk_tier combination and creates
    new live instances to fill any gap, subject to the 2× cap.

    Cap rule: total instances (live + dead) may not exceed count × 2.
    This prevents unbounded dead-instance accumulation while still allowing
    respawn timers to run their course.
    """
    room            = models.ForeignKey(
        'Room', on_delete=models.CASCADE, related_name='spawns',
    )
    npc_definition  = models.ForeignKey(
        NpcDefinition, on_delete=models.CASCADE, related_name='room_spawns',
    )
    mk_tier         = models.IntegerField(
        default=1,
        help_text="Mk tier at which this NPC spawns in this room.",
    )
    count           = models.IntegerField(
        default=1,
        help_text="Desired number of live instances of this NPC in this room.",
    )
    is_active       = models.BooleanField(
        default=True,
        help_text="Inactive spawns are ignored by the tick engine.",
    )
    requires_living_npc = models.ForeignKey(
        'NpcDefinition', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='dependent_spawns',
        help_text='If set, this spawn only refills while a live instance of the '
                  'given definition exists in the same room. Used to gate boss '
                  'minions on their boss: minions respawn on their own timer '
                  'while the boss lives, stop when it dies, and resume when it '
                  'respawns.',
    )

    class Meta:
        unique_together = ('room', 'npc_definition', 'mk_tier')
        ordering = ['room', 'npc_definition', 'mk_tier']

    def __str__(self):
        return (
            f"{self.npc_definition.name} (Mk {self.mk_tier}) "
            f"×{self.count} in {self.room.name}"
        )


class VendorEntry(models.Model):
    """
    Declares that an NPC sells a particular item at a particular Mk tier
    for a specific copper price.

    An NpcDefinition with one or more VendorEntry rows is a vendor.
    No flag is needed on NpcDefinition itself.
    """
    npc_definition  = models.ForeignKey(
        NpcDefinition, on_delete=models.CASCADE, related_name='vendor_entries',
    )
    item_definition = models.ForeignKey(
        'ItemDefinition', on_delete=models.CASCADE, related_name='vendor_entries',
    )
    mk_tier         = models.IntegerField(
        default=1,
        help_text="Mk tier of the item being sold.",
    )
    price           = models.BigIntegerField(
        help_text="Price in copper. Always required — no auto-calculation.",
    )
    stock_limit     = models.IntegerField(
        null=True, blank=True,
        help_text=(
            "Maximum number of this item available for purchase. "
            "Null = unlimited stock."
        ),
    )
    sold_count      = models.IntegerField(
        default=0,
        help_text='Units sold so far. An entry with a finite stock_limit is '
                  'exhausted when sold_count >= stock_limit.',
    )
    is_active       = models.BooleanField(
        default=True,
        help_text="Inactive entries are hidden from players.",
    )

    class Meta:
        unique_together = ('npc_definition', 'item_definition', 'mk_tier')
        ordering = ['npc_definition', 'item_definition', 'mk_tier']

    def __str__(self):
        return (
            f"{self.npc_definition.name} sells "
            f"{self.item_definition.name} Mk {self.mk_tier} "
            f"for {self.price}cp"
        )


class TravelNode(models.Model):
    """
    A registered stop on the Obelisk Network (GDD 2.11).

    A character's available destinations are derived from RoomVisit: any node
    whose room they have seen is revealed to them, permanently. The network is
    global — no zone scoping. Travel is free and only initiates from a room
    whose node is obelisk-type; checkpoints are destinations only.
    """
    NODE_TYPE_CHOICES = [
        ('obelisk', 'Obelisk'),
        ('checkpoint', 'Checkpoint'),
    ]

    room = models.OneToOneField(
        Room, on_delete=models.CASCADE, related_name='travel_node',
        help_text='The room this node lives in. One node per room.',
    )
    travel_name = models.CharField(
        max_length=60, unique=True,
        help_text='Unique, typeable destination name shown in travel lists '
                  '(e.g. "Fordwatch", "The Verdant Crown").',
    )
    node_type = models.CharField(
        max_length=12, choices=NODE_TYPE_CHOICES,
        help_text='Obelisks are travel sources and destinations. '
                  'Checkpoints are destinations only.',
    )

    def __str__(self):
        return f'{self.travel_name} ({self.node_type})'


class TravelMessage(models.Model):
    CATEGORY_CHOICES = [
        ('traveler', 'Traveler'),           # shown to the traveling player
        ('departure', 'Departure witness'), # shown to players in the origin room
        ('arrival', 'Arrival witness'),     # shown to players in the destination room
    ]

    category = models.CharField(max_length=12, choices=CATEGORY_CHOICES)
    text = models.TextField(
        help_text='Witness messages may include {name}, replaced with the '
                  'traveling character\'s name. Traveler messages take no '
                  'placeholders.',
    )

    def __str__(self):
        return f'[{self.category}] {self.text[:60]}'


class CombatSession(models.Model):
    characters          = models.ManyToManyField('Character', related_name='combat_sessions', blank=True)
    npcs                = models.ManyToManyField('NpcInstance', related_name='combat_sessions', blank=True)
    room                = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True, related_name='combat_sessions')
    started_at          = models.DateTimeField(auto_now_add=True)
    last_tick_at        = models.DateTimeField(null=True, blank=True)
    tick_counter        = models.IntegerField(default=0)
    is_active           = models.BooleanField(default=True)
    first_attacker      = models.CharField(max_length=20, default='character')
    last_flee_attempt_at = models.DateTimeField(null=True, blank=True)
    last_flee_character  = models.ForeignKey(
        'Character', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    focus_npc = models.ForeignKey(
        'NpcInstance', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )

    def __str__(self):
        return f"CombatSession {self.pk} (room={self.room_id}, active={self.is_active})"

    class Meta:
        ordering = ['-started_at']


class CombatAction(models.Model):
    ACTION_ATTACK = 'attack'
    ACTION_USE    = 'use'
    ACTION_FLEE   = 'flee'
    ACTION_TYPE_CHOICES = [
        (ACTION_ATTACK, 'Attack'),
        (ACTION_USE,    'Use Item'),
        (ACTION_FLEE,   'Flee'),
    ]

    combat_session   = models.ForeignKey(CombatSession, on_delete=models.CASCADE, related_name='actions')
    character        = models.ForeignKey('Character', on_delete=models.CASCADE, null=True, blank=True, related_name='combat_actions')
    npc              = models.ForeignKey('NpcInstance', on_delete=models.CASCADE, null=True, blank=True, related_name='combat_actions')
    action_type      = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES, default=ACTION_ATTACK)
    target_character = models.ForeignKey('Character', on_delete=models.SET_NULL, null=True, blank=True, related_name='targeted_by_actions')
    target_npc       = models.ForeignKey('NpcInstance', on_delete=models.SET_NULL, null=True, blank=True, related_name='targeted_by_actions')
    item             = models.ForeignKey('ItemInstance', on_delete=models.SET_NULL, null=True, blank=True, related_name='combat_actions')
    queued_at        = models.DateTimeField(auto_now_add=True)
    is_processed     = models.BooleanField(default=False)

    def __str__(self):
        actor = self.character or self.npc
        return f"CombatAction {self.pk} ({self.action_type} by {actor})"

    class Meta:
        ordering = ['queued_at']


# ----------------------------------------------------------------------
# NPC dialogue engine (v19 brief 9)
# ----------------------------------------------------------------------

class DialogueEntry(models.Model):
    """A keyword→response map, greeting, or departure reaction for one NPC
    definition. Seed-owned (enforce-exact) per brief 9."""

    ENTRY_KEYWORD = 'keyword'
    ENTRY_GREETING = 'greeting'
    ENTRY_DEPARTED = 'departed'
    ENTRY_TYPE_CHOICES = [
        (ENTRY_KEYWORD, 'Keyword'),
        (ENTRY_GREETING, 'Greeting'),
        (ENTRY_DEPARTED, 'Departed'),
    ]

    npc_definition = models.ForeignKey(NpcDefinition, on_delete=models.CASCADE, related_name='dialogue_entries')
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES, default=ENTRY_KEYWORD)
    keywords = models.JSONField(
        default=list, blank=True,
        help_text='Lowercase single-word tokens. Empty for greeting/departed entries.',
    )
    note = models.CharField(
        max_length=100, blank=True,
        help_text='Authoring aid only.',
    )

    def __str__(self):
        return f'{self.npc_definition.name} [{self.entry_type}] {self.note or self.pk}'


class DialogueResponse(models.Model):
    """One line in an entry's response pool. Seed-owned (enforce-exact)."""

    entry = models.ForeignKey(DialogueEntry, on_delete=models.CASCADE, related_name='responses')
    text = models.TextField()

    def __str__(self):
        return self.text[:60]


class DialogueConnective(models.Model):
    """Position-aware connective color for the second/later speaker in a
    multi-NPC response to one utterance. Seed-owned (enforce-exact)."""

    POSITION_SECOND = 'second'
    POSITION_LATER = 'later'
    POSITION_CLASS_CHOICES = [
        (POSITION_SECOND, 'Second speaker'),
        (POSITION_LATER, 'Third-and-later speaker'),
    ]

    position_class = models.CharField(max_length=6, choices=POSITION_CLASS_CHOICES)
    template = models.TextField(help_text="Uses {name}, replaced with the responding NPC's name.")

    def __str__(self):
        return f'[{self.position_class}] {self.template[:60]}'


class PendingDialogueResponse(models.Model):
    """A scheduled NPC response awaiting tick-engine delivery. Runtime state
    — never touched by the seed sweep (brief 9, joining brief 8's
    never-touched list)."""

    utterance_id = models.UUIDField(help_text='Groups every responder to one say or greeting event.')
    npc_instance = models.ForeignKey(NpcInstance, on_delete=models.CASCADE, related_name='pending_dialogue_responses')
    entry = models.ForeignKey(DialogueEntry, on_delete=models.CASCADE, related_name='pending_responses')
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='pending_dialogue_responses',
        help_text='The character whose speech or room entry triggered this response.',
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='pending_dialogue_responses',
        help_text='Delivery room, captured at scheduling time so a departed asker cannot silence it.',
    )
    position = models.PositiveSmallIntegerField(help_text='0 = first speaker in this utterance.')
    is_final = models.BooleanField(default=False, help_text='Last speaker for this utterance.')
    fire_at = models.DateTimeField()

    class Meta:
        ordering = ['fire_at', 'position']

    def __str__(self):
        return f'PendingDialogueResponse {self.pk} (npc={self.npc_instance_id}, fire_at={self.fire_at})'


class DialogueGreetingRecord(models.Model):
    """Marks that an NPC definition has already greeted a character. Runtime
    state — never touched by the seed sweep (brief 9)."""

    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='dialogue_greeting_records')
    npc_definition = models.ForeignKey(NpcDefinition, on_delete=models.CASCADE, related_name='greeting_records')

    class Meta:
        unique_together = [('character', 'npc_definition')]

    def __str__(self):
        return f'{self.character.name} greeted by {self.npc_definition.name}'
