from django.contrib import admin
from .currency import display as currency_display
from .models import (
    Area, Character, CombatAction, CombatSession, Corpse,
    EffectComponent, EffectComponentInstance, EffectDefinition, EffectInstance,
    ItemDefinition, ItemInstance, LootTable, LootTableEntry,
    NpcDefinition, NpcEffect, NpcInstance, Room, RoomVisit, Zone,
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
    list_display = ('name', 'user', 'level', 'unspent_stat_points', 'origin', 'archetype', 'current_room', 'last_seen')
    list_filter = ('origin', 'archetype', 'is_hardcore', 'is_dead')
    raw_id_fields = ('current_room', 'recall_room')
    readonly_fields = ('wallet_display',)
    list_select_related = ('user__profile',)
    fieldsets = (
        (None, {'fields': ('user', 'origin', 'archetype', 'current_room', 'recall_room')}),
        ('Progression', {'fields': ('level', 'xp', 'unspent_stat_points')}),
        ('Primary Stats', {'fields': ('stat_str', 'stat_dex', 'stat_end', 'stat_int', 'stat_wis', 'stat_per')}),
        ('Bars', {'fields': ('vitality_current', 'vitality_max', 'longevity_current', 'longevity_max',
                             'acuity_current', 'acuity_baseline', 'acuity_band_low', 'acuity_band_high')}),
        ('Economy', {'fields': ('copper', 'wallet_display')}),
        ('Flags', {'fields': ('is_hardcore', 'is_dead', 'is_dying', 'dying_since')}),
    )

    def wallet_display(self, obj):
        return currency_display(obj.copper)
    wallet_display.short_description = 'Wallet'


@admin.register(RoomVisit)
class RoomVisitAdmin(admin.ModelAdmin):
    list_display = ('character', 'room', 'visited_at')


class EffectComponentInline(admin.TabularInline):
    model = EffectComponent
    extra = 1
    fields = ['component_type', 'target_stat', 'magnitude_base', 'magnitude_scaling',
              'duration_base', 'duration_scaling', 'order']


@admin.register(EffectDefinition)
class EffectDefinitionAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [EffectComponentInline]


@admin.register(EffectComponent)
class EffectComponentAdmin(admin.ModelAdmin):
    list_display  = ['definition', 'component_type', 'target_stat',
                     'magnitude_base', 'magnitude_scaling',
                     'duration_base', 'duration_scaling', 'order']
    list_filter   = ['component_type']


@admin.register(ItemDefinition)
class ItemDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_type', 'genre_tag', 'takes_durability_loss')
    list_filter = ('item_type', 'genre_tag')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'item_type', 'genre_tag', 'description')}),
        ('Identification', {'fields': ('mystery_name', 'mystery_description')}),
        ('Scaling', {'fields': ('scaling_base', 'scaling_factor')}),
        ('Weapon', {'fields': ('damage_spread', 'is_ranged')}),
        ('Equipment', {'fields': ('valid_slots', 'is_two_handed')}),
        ('Durability', {'fields': ('takes_durability_loss', 'durability_table')}),
        ('Carry', {'fields': ('carry_bonus',)}),
        ('Stats', {'fields': ('primary_stats', 'secondary_stat_pool')}),
        ('Effect / Curse', {'fields': ('effect', 'is_cursed_template')}),
    )


@admin.register(ItemInstance)
class ItemInstanceAdmin(admin.ModelAdmin):
    list_display = (
        'definition', 'owner', 'mk_tier', 'rarity',
        'is_equipped', 'is_broken', 'is_soulbound',
        'is_identified', 'is_unidentifiable',
    )
    list_filter = ('rarity', 'is_equipped', 'is_broken', 'is_unidentifiable')
    raw_id_fields = ('owner', 'current_room', 'soulbound_to', 'active_curse')
    fieldsets = (
        (None, {'fields': ('definition', 'owner', 'current_room', 'mk_tier', 'rarity')}),
        ('Stats', {'fields': ('rolled_primary_stats', 'rolled_secondary_stats')}),
        ('Combat', {'fields': ('damage_midpoint', 'damage_spread')}),
        ('Durability', {'fields': ('durability_current', 'is_broken')}),
        ('Equipment', {'fields': ('is_equipped', 'equipped_slot')}),
        ('Soulbind', {'fields': ('is_soulbound', 'soulbound_to')}),
        ('Identification', {'fields': ('is_identified', 'is_unidentifiable')}),
        ('Curse', {'fields': ('is_cursed', 'curse_identified', 'active_curse')}),
        ('Flags', {'fields': ('is_artifact',)}),
    )


class EffectComponentInstanceInline(admin.TabularInline):
    model = EffectComponentInstance
    extra = 0
    readonly_fields = ['component', 'magnitude', 'expires_at', 'is_active', 'removed_by']
    can_delete = False


@admin.register(EffectInstance)
class EffectInstanceAdmin(admin.ModelAdmin):
    list_display  = ['definition', 'target', 'mk_tier', 'is_active', 'applied_at']
    list_filter   = ['is_active']
    readonly_fields = ['applied_at']
    inlines = [EffectComponentInstanceInline]


@admin.register(EffectComponentInstance)
class EffectComponentInstanceAdmin(admin.ModelAdmin):
    list_display  = ['effect_instance', 'component', 'magnitude',
                     'expires_at', 'is_active', 'removed_by']
    list_filter   = ['is_active']
    readonly_fields = ['effect_instance', 'component', 'magnitude',
                       'expires_at', 'is_active', 'removed_by']


class LootTableEntryInline(admin.TabularInline):
    model = LootTableEntry
    extra = 1
    fields = ('item_definition', 'mk_tier_min', 'mk_tier_max', 'drop_chance', 'rarity_weights')


@admin.register(LootTable)
class LootTableAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [LootTableEntryInline]


class NpcEffectInline(admin.TabularInline):
    model = NpcEffect
    extra = 1
    fields = ['effect_definition', 'effect_chance']
    autocomplete_fields = ['effect_definition']


@admin.register(NpcDefinition)
class NpcDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'genre_tag', 'is_aggressive', 'is_unique', 'respawn_minutes')
    list_filter = ('genre_tag', 'is_aggressive', 'is_unique')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('loot_table',)
    inlines = [NpcEffectInline]


@admin.register(NpcInstance)
class NpcInstanceAdmin(admin.ModelAdmin):
    list_display = ('definition', 'mk_tier', 'current_room', 'spawn_room', 'is_alive', 'vitality_current', 'vitality_max', 'spawned_at')
    list_filter = ('is_alive', 'mk_tier')
    raw_id_fields = ('current_room', 'spawn_room')


@admin.register(Corpse)
class CorpseAdmin(admin.ModelAdmin):
    list_display = ('npc_name_snapshot', 'current_room', 'killed_by', 'copper_drop', 'created_at', 'decay_at')
    list_filter = ('current_room',)
    raw_id_fields = ('npc_definition', 'current_room', 'killed_by')


@admin.register(NpcEffect)
class NpcEffectAdmin(admin.ModelAdmin):
    list_display  = ['npc_definition', 'effect_definition', 'effect_chance']
    list_filter   = ['npc_definition']
    raw_id_fields = ['npc_definition', 'effect_definition']


@admin.register(CombatSession)
class CombatSessionAdmin(admin.ModelAdmin):
    list_display    = ['pk', 'room', 'is_active', 'first_attacker', 'started_at', 'last_tick_at', 'tick_counter']
    list_filter     = ['is_active', 'first_attacker']
    readonly_fields = ['started_at', 'last_tick_at', 'tick_counter', 'characters', 'npcs']
    raw_id_fields   = ['room']
    ordering        = ['-started_at']


@admin.register(CombatAction)
class CombatActionAdmin(admin.ModelAdmin):
    list_display    = ['pk', 'combat_session', 'action_type', 'character', 'npc', 'is_processed', 'queued_at']
    list_filter     = ['action_type', 'is_processed']
    readonly_fields = ['queued_at']
    raw_id_fields   = ['combat_session', 'character', 'npc', 'target_character', 'target_npc', 'item']
    ordering        = ['-queued_at']
