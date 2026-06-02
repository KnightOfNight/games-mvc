from django.contrib import admin

from .models import ShyshipGame, ShyshipMove


@admin.register(ShyshipGame)
class ShyshipGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player1', 'player2', 'status', 'current_turn', 'created_at']
    list_filter = ['status']
    readonly_fields = ['id', 'created_at']


@admin.register(ShyshipMove)
class ShyshipMoveAdmin(admin.ModelAdmin):
    list_display = ['game', 'player_num', 'row', 'col', 'is_hit', 'created_at']
    list_filter = ['is_hit', 'player_num']
    readonly_fields = ['created_at']
