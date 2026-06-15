from django.contrib import admin
from .currency import display as currency_display
from .models import (
    Area, Character, EffectDefinition, EffectInstance,
    ItemDefinition, ItemInstance, Room, RoomVisit, Zone,
)


class AreaInline(admin.TabularInline):
    model = Area
    extra = 0
    fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    show_change_link = True


class RoomInline(admin.TabularInline):
    model = Room
    extra = 0
    fields = ('name', 'coord_x', 'coord_y', 'coord_z', 'flag_safe')


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'danger_level', 'is_pvp_zone', 'is_scaled')
    inlines = [AreaInline, RoomInline]


class RoomInlineForArea(admin.TabularInline):
    model = Room
    extra = 0
    fields = ('name', 'coord_x', 'coord_y', 'coord_z', 'flag_safe')
    show_change_link = True


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'zone', 'slug')
    list_filter = ('zone',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [RoomInlineForArea]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'zone', 'area', 'coord_x', 'coord_y', 'coord_z', 'flag_safe')
    list_filter = ('zone', 'area', 'flag_safe', 'flag_pvp')
    raw_id_fields = ('area', 'exit_north', 'exit_south', 'exit_east', 'exit_west', 'exit_up', 'exit_down')


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


@admin.register(EffectDefinition)
class EffectDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'effect_type', 'scales_with_mk')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ItemDefinition)
class ItemDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_type', 'genre_tag', 'takes_durability_loss')
    list_filter = ('item_type', 'genre_tag')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ItemInstance)
class ItemInstanceAdmin(admin.ModelAdmin):
    list_display = ('definition', 'owner', 'mk_tier', 'rarity', 'is_equipped', 'is_broken', 'is_soulbound')
    list_filter = ('rarity', 'is_equipped', 'is_broken')
    raw_id_fields = ('owner', 'current_room', 'soulbound_to', 'active_curse')


@admin.register(EffectInstance)
class EffectInstanceAdmin(admin.ModelAdmin):
    list_display = ('definition', 'target', 'is_active', 'applied_at', 'expires_at')
    list_filter = ('is_active',)
