import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import ShyshipGame, ShyshipMove


class ShyshipConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.group_name = f'shyship_{self.game_id}'

        await self.accept()

        if not user.is_authenticated or not await self.user_in_group(user):
            await self.send(text_data=json.dumps({'type': 'error', 'code': 'auth'}))
            await self.close()
            return

        game = await self.get_game()
        if game is None:
            await self.send(text_data=json.dumps({'type': 'error', 'code': 'not_found'}))
            await self.close()
            return

        self.player_num = await self.get_player_num(game, user)
        if self.player_num is None:
            await self.send(text_data=json.dumps({'type': 'error', 'code': 'not_player'}))
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        moves = await self.get_moves()
        ships_own = game.ships_p1 if self.player_num == 1 else game.ships_p2

        await self.send(text_data=json.dumps({
            'type': 'state',
            'player_num': self.player_num,
            'status': game.status,
            'winner': game.winner,
            'current_turn': game.current_turn,
            'ships_own': ships_own,
            'opponent': await self.get_opponent_name(game, self.player_num),
            'moves': moves,
        }))

        if self.player_num == 2 and game.status == ShyshipGame.ACTIVE:
            await self.channel_layer.group_send(self.group_name, {
                'type': 'game_event',
                'data': {
                    'type': 'player_joined',
                    'player': await self.get_display_name(user),
                    'status': 'active',
                },
            })

    async def disconnect(self, code):
        if hasattr(self, 'group_name') and hasattr(self, 'player_num'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        if data.get('type') != 'fire':
            return

        game = await self.get_game()
        if game is None or game.status != ShyshipGame.ACTIVE:
            return
        if game.current_turn != self.player_num:
            return

        row = data.get('row')
        col = data.get('col')
        if not (isinstance(row, int) and isinstance(col, int)):
            return
        if not (0 <= row <= 9 and 0 <= col <= 9):
            return

        if await self.cell_already_fired(row, col):
            return

        opponent_ships = game.ships_p2 if self.player_num == 1 else game.ships_p1
        is_hit = [row, col] in opponent_ships

        next_turn = 2 if self.player_num == 1 else 1
        game_over = await self.save_move(game, row, col, is_hit, next_turn, len(opponent_ships))

        await self.channel_layer.group_send(self.group_name, {
            'type': 'game_event',
            'data': {
                'type': 'move',
                'player_num': self.player_num,
                'row': row,
                'col': col,
                'is_hit': is_hit,
                'next_turn': next_turn,
            },
        })

        if game_over:
            await self.channel_layer.group_send(self.group_name, {
                'type': 'game_event',
                'data': {'type': 'game_over', 'winner': self.player_num},
            })

    async def game_event(self, event):
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_display_name(self, user):
        try:
            if user.profile.gamer_tag:
                return user.profile.gamer_tag
        except AttributeError:
            pass
        full = user.get_full_name().strip()
        return full if full else user.username

    @database_sync_to_async
    def user_in_group(self, user):
        return user.is_superuser or user.groups.filter(name='players.shyship').exists()

    @database_sync_to_async
    def get_game(self):
        try:
            return (
                ShyshipGame.objects
                .select_related('player1', 'player2')
                .get(pk=self.game_id)
            )
        except ShyshipGame.DoesNotExist:
            return None

    @database_sync_to_async
    def get_player_num(self, game, user):
        if game.player1_id == user.pk:
            return 1
        if game.player2_id == user.pk:
            return 2
        return None

    @database_sync_to_async
    def get_opponent_name(self, game, player_num):
        if player_num == 1:
            return game.player2.username if game.player2_id else None
        return game.player1.username

    @database_sync_to_async
    def get_moves(self):
        return list(
            ShyshipMove.objects
            .filter(game_id=self.game_id)
            .values('player_num', 'row', 'col', 'is_hit')
        )

    @database_sync_to_async
    def cell_already_fired(self, row, col):
        return ShyshipMove.objects.filter(
            game_id=self.game_id,
            player_num=self.player_num,
            row=row,
            col=col,
        ).exists()

    @database_sync_to_async
    def save_move(self, game, row, col, is_hit, next_turn, opponent_ship_count):
        ShyshipMove.objects.create(
            game=game,
            player_num=self.player_num,
            row=row,
            col=col,
            is_hit=is_hit,
        )
        if is_hit:
            hit_count = ShyshipMove.objects.filter(
                game=game, player_num=self.player_num, is_hit=True
            ).count()
            if hit_count >= opponent_ship_count:
                ShyshipGame.objects.filter(pk=game.pk).update(
                    status=ShyshipGame.DONE, winner=self.player_num
                )
                return True
        ShyshipGame.objects.filter(pk=game.pk).update(current_turn=next_turn)
        return False
