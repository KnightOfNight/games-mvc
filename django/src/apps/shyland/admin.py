from django.contrib import admin
from .currency import display as currency_display
from .models import Character, Room, RoomVisit, Zone


class RoomInline(admin.TabularInline):
    model = Room
    extra = 0
    fields = ('name', 'coord_x', 'coord_y', 'coord_z', 'flag_safe')


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'danger_level', 'is_pvp_zone', 'is_scaled')
    inlines = [RoomInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'zone', 'coord_x', 'coord_y', 'coord_z', 'flag_safe')
    list_filter = ('zone', 'flag_safe', 'flag_pvp')
    raw_id_fields = ('exit_north', 'exit_south', 'exit_east', 'exit_west', 'exit_up', 'exit_down')


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'level', 'origin', 'archetype', 'current_room', 'last_seen')
    list_filter = ('origin', 'archetype', 'is_hardcore', 'is_dead')
    raw_id_fields = ('current_room', 'recall_room')
    readonly_fields = ('wallet_display',)
    list_select_related = ('user__profile',)

    def wallet_display(self, obj):
        return currency_display(obj.copper)
    wallet_display.short_description = 'Wallet'


@admin.register(RoomVisit)
class RoomVisitAdmin(admin.ModelAdmin):
    list_display = ('character', 'room', 'visited_at')
