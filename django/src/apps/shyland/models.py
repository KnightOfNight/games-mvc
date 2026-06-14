from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
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
