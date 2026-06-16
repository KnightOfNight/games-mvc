from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models


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
    coord_x = models.IntegerField(default=0)
    coord_y = models.IntegerField(default=0)
    coord_z = models.IntegerField(default=0)

    exit_north = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_south')
    exit_south = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_north')
    exit_east = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_west')
    exit_west = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_east')
    exit_up = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_below')
    exit_down = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='entrance_from_above')

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


class Character(models.Model):
    ORIGIN_HIGHBORN = 'highborn'
    ORIGIN_FERAL = 'feral'
    ORIGIN_STREETBORN = 'streetborn'
    ORIGIN_IRRADIATED = 'irradiated'
    ORIGIN_UNDYING = 'undying'
    ORIGIN_MACHINEKIND = 'machinekind'
    ORIGIN_VOIDTOUCHED = 'voidtouched'
    ORIGIN_CHOICES = [
        (ORIGIN_HIGHBORN, 'Highborn'),
        (ORIGIN_FERAL, 'Feral'),
        (ORIGIN_STREETBORN, 'Streetborn'),
        (ORIGIN_IRRADIATED, 'Irradiated'),
        (ORIGIN_UNDYING, 'Undying'),
        (ORIGIN_MACHINEKIND, 'Machinekind'),
        (ORIGIN_VOIDTOUCHED, 'Voidtouched'),
    ]

    ARCHETYPE_BLADE = 'blade'
    ARCHETYPE_BULWARK = 'bulwark'
    ARCHETYPE_SHADE = 'shade'
    ARCHETYPE_CONDUIT = 'conduit'
    ARCHETYPE_WARDEN = 'warden'
    ARCHETYPE_GUNNER = 'gunner'
    ARCHETYPE_MACHINIST = 'machinist'
    ARCHETYPE_CHOICES = [
        (ARCHETYPE_BLADE, 'Blade'),
        (ARCHETYPE_BULWARK, 'Bulwark'),
        (ARCHETYPE_SHADE, 'Shade'),
        (ARCHETYPE_CONDUIT, 'Conduit'),
        (ARCHETYPE_WARDEN, 'Warden'),
        (ARCHETYPE_GUNNER, 'Gunner'),
        (ARCHETYPE_MACHINIST, 'Machinist'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shyland_character')
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES)
    archetype = models.CharField(max_length=20, choices=ARCHETYPE_CHOICES)
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
    acuity_current = models.IntegerField(default=50)
    acuity_baseline = models.IntegerField(default=50)
    acuity_band_low = models.IntegerField(default=35)
    acuity_band_high = models.IntegerField(default=65)
    longevity_current = models.IntegerField(default=100)
    longevity_max = models.IntegerField(default=100)

    copper = models.BigIntegerField(default=0)

    is_hardcore = models.BooleanField(default=False)
    is_dead = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    @property
    def name(self):
        try:
            tag = self.user.profile.gamer_tag
            if tag:
                return tag
        except ObjectDoesNotExist:
            pass
        return self.user.username

    def __str__(self):
        return self.name


class RoomVisit(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='room_visits')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='visits')
    visited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('character', 'room')


class EffectDefinition(models.Model):
    RESTORE_VITALITY = 'restore_vitality'
    RESTORE_ACUITY = 'restore_acuity'
    RESTORE_LONGEVITY = 'restore_longevity'
    DOT_VITALITY = 'dot_vitality'
    DOT_ACUITY = 'dot_acuity'
    DOT_LONGEVITY = 'dot_longevity'
    SHIFT_ACUITY_HIGH = 'shift_acuity_high'
    SHIFT_ACUITY_LOW = 'shift_acuity_low'
    STAT_BONUS = 'stat_bonus'
    STAT_PENALTY = 'stat_penalty'
    DURABILITY_RESTORE = 'durability_restore'
    CURSE_GENERIC = 'curse_generic'
    EFFECT_TYPE_CHOICES = [
        (RESTORE_VITALITY, 'Restore Vitality'),
        (RESTORE_ACUITY, 'Restore Acuity'),
        (RESTORE_LONGEVITY, 'Restore Longevity'),
        (DOT_VITALITY, 'DoT Vitality'),
        (DOT_ACUITY, 'DoT Acuity'),
        (DOT_LONGEVITY, 'DoT Longevity'),
        (SHIFT_ACUITY_HIGH, 'Shift Acuity High'),
        (SHIFT_ACUITY_LOW, 'Shift Acuity Low'),
        (STAT_BONUS, 'Stat Bonus'),
        (STAT_PENALTY, 'Stat Penalty'),
        (DURABILITY_RESTORE, 'Durability Restore'),
        (CURSE_GENERIC, 'Curse Generic'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    effect_type = models.CharField(max_length=30, choices=EFFECT_TYPE_CHOICES)
    magnitude_min = models.FloatField()
    magnitude_max = models.FloatField()
    duration_min = models.FloatField(null=True, blank=True)
    duration_max = models.FloatField(null=True, blank=True)
    scales_with_mk = models.BooleanField(default=False)
    scaling_base = models.FloatField(null=True, blank=True)
    scaling_factor = models.FloatField(null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class ItemDefinition(models.Model):
    WEAPON = 'weapon'
    ARMOR = 'armor'
    ACCESSORY = 'accessory'
    CONSUMABLE = 'consumable'
    BAG = 'bag'
    READABLE = 'readable'
    KEY = 'key'
    ITEM_TYPE_CHOICES = [
        (WEAPON, 'Weapon'),
        (ARMOR, 'Armor'),
        (ACCESSORY, 'Accessory'),
        (CONSUMABLE, 'Consumable'),
        (BAG, 'Bag'),
        (READABLE, 'Readable'),
        (KEY, 'Key'),
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
    source_item = models.ForeignKey(
        'ItemInstance',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='applied_effects',
    )
    source_ability = models.CharField(max_length=100, blank=True)
    magnitude = models.FloatField()
    duration = models.FloatField(null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    removed_by = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f'{self.definition.name} on {self.target}'


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

    is_aggressive   = models.BooleanField(default=False, help_text="Attacks players on sight.")
    is_unique       = models.BooleanField(default=False, help_text="One instance only; no respawn.")
    wanders         = models.BooleanField(default=False, help_text="Moves between rooms. Not yet implemented.")

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
    currency_drop_min   = models.IntegerField(default=0, help_text="Minimum copper drop (before Mk scaling).")
    currency_drop_max   = models.IntegerField(default=0, help_text="Maximum copper drop (before Mk scaling).")

    respawn_minutes = models.IntegerField(default=30, help_text="Ignored if is_unique=True.")

    def __str__(self):
        return self.name


class NpcInstance(models.Model):
    definition       = models.ForeignKey(NpcDefinition, on_delete=models.CASCADE, related_name='instances')
    current_room     = models.ForeignKey('Room', null=True, blank=True, on_delete=models.SET_NULL, related_name='npcs')
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
