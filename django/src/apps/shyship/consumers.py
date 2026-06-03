import asyncio
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .bot import next_bot_cell, update_bot_state
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
        ship_name = None
        ship_cells = None
        is_hit = False
        for ship in opponent_ships:
            if [row, col] in ship['cells']:
                is_hit = True
                ship_name = ship['name']
                ship_cells = ship['cells']
                break

        total_cells = sum(len(s['cells']) for s in opponent_ships)
        next_turn = 2 if self.player_num == 1 else 1
        game_over = await self.save_move(game, row, col, is_hit, next_turn, total_cells)

        ship_sunk = is_hit and await self.is_ship_sunk(ship_cells)

        await self.channel_layer.group_send(self.group_name, {
            'type': 'game_event',
            'data': {
                'type': 'move',
                'player_num': self.player_num,
                'row': row,
                'col': col,
                'is_hit': is_hit,
                'ship_name': ship_name,
                'sunk': ship_sunk,
                'next_turn': next_turn,
            },
        })

        if game_over:
            await self.channel_layer.group_send(self.group_name, {
                'type': 'game_event',
                'data': {'type': 'game_over', 'winner': self.player_num},
            })
            return

        if game.vs_bot and self.player_num == 1:
            await asyncio.sleep(0.6)
            bot_result = await self.bot_take_turn()
            if bot_result:
                b_row, b_col, b_hit, b_ship, b_sunk, b_over = bot_result
                await self.channel_layer.group_send(self.group_name, {
                    'type': 'game_event',
                    'data': {
                        'type': 'move',
                        'player_num': 2,
                        'row': b_row,
                        'col': b_col,
                        'is_hit': b_hit,
                        'ship_name': b_ship,
                        'sunk': b_sunk,
                        'next_turn': 1,
                    },
                })
                if b_over:
                    await self.channel_layer.group_send(self.group_name, {
                        'type': 'game_event',
                        'data': {'type': 'game_over', 'winner': 2},
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
    def bot_take_turn(self):
        game = ShyshipGame.objects.get(pk=self.game_id)
        fired = set(
            ShyshipMove.objects.filter(game=game, player_num=2).values_list('row', 'col')
        )
        cell = next_bot_cell(game.bot_state, fired)
        if not cell:
            return None
        row, col = cell

        ship_name = None
        ship_cells = None
        is_hit = False
        for ship in game.ships_p1:
            if [row, col] in ship['cells']:
                is_hit = True
                ship_name = ship['name']
                ship_cells = ship['cells']
                break

        ShyshipMove.objects.create(game=game, player_num=2, row=row, col=col, is_hit=is_hit)

        sunk = False
        if is_hit:
            hit_coords = set(
                ShyshipMove.objects.filter(game=game, player_num=2, is_hit=True).values_list('row', 'col')
            )
            sunk = all((r, c) in hit_coords for r, c in ship_cells)

        update_bot_state(game.bot_state, row, col, is_hit, sunk)

        total_cells = sum(len(s['cells']) for s in game.ships_p1)
        hit_count = ShyshipMove.objects.filter(game=game, player_num=2, is_hit=True).count()
        game_over = is_hit and hit_count >= total_cells

        if game_over:
            ShyshipGame.objects.filter(pk=game.pk).update(
                status=ShyshipGame.DONE, winner=2, bot_state=game.bot_state
            )
        else:
            ShyshipGame.objects.filter(pk=game.pk).update(
                current_turn=1, bot_state=game.bot_state
            )

        return row, col, is_hit, ship_name, sunk, game_over

    @database_sync_to_async
    def is_ship_sunk(self, ship_cells):
        hit_coords = set(
            ShyshipMove.objects.filter(
                game_id=self.game_id,
                player_num=self.player_num,
                is_hit=True,
            ).values_list('row', 'col')
        )
        return all((r, c) in hit_coords for r, c in ship_cells)

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
