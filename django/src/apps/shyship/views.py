from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, View

from .models import ShyshipGame, ShyshipMove, place_ships_randomly


class ShyshipLoginView(LoginView):
    template_name = 'shyship/login.html'

    def get_default_redirect_url(self):
        return '/'

GROUP_NAME = 'players.shyship'


class ShyshipAccessMixin(LoginRequiredMixin):
    login_url = '/shyship/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.groups.filter(name=GROUP_NAME).exists()):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class LobbyView(ShyshipAccessMixin, TemplateView):
    template_name = 'shyship/lobby.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['open_games'] = (
            ShyshipGame.objects
            .filter(status=ShyshipGame.WAITING)
            .exclude(player1=user)
            .select_related('player1')
        )
        ctx['my_games'] = (
            ShyshipGame.objects
            .filter(Q(player1=user) | Q(player2=user))
            .filter(status__in=[ShyshipGame.WAITING, ShyshipGame.ACTIVE])
            .select_related('player1', 'player2')
            .annotate(move_count=Count('moves'))
        )
        past_qs = (
            ShyshipGame.objects
            .filter(Q(player1=user) | Q(player2=user))
            .filter(status__in=[ShyshipGame.DONE, ShyshipGame.CANCELLED])
            .select_related('player1', 'player2')
            .prefetch_related('moves')
            .order_by('-created_at')[:10]
        )
        past_games = list(past_qs)
        for game in past_games:
            my_num = 1 if game.player1_id == user.pk else 2
            if game.status == ShyshipGame.CANCELLED:
                game.result = 'cancelled'
                game.detail = ''
            elif game.winner is None:
                game.result = 'done'
                game.detail = ''
            else:
                moves = game.moves.all()
                p1_hits = sum(1 for m in moves if m.player_num == 1 and m.is_hit)
                p2_hits = sum(1 for m in moves if m.player_num == 2 and m.is_hit)
                my_hits = p1_hits if my_num == 1 else p2_hits
                opp_hits = p2_hits if my_num == 1 else p1_hits
                winner_hits = p1_hits if game.winner == 1 else p2_hits
                forfeit = winner_hits < 17
                if game.winner == my_num:
                    game.result = 'won'
                    game.detail = 'opponent forfeited' if forfeit else f'{my_hits}–{opp_hits}'
                else:
                    game.result = 'lost'
                    game.detail = 'you forfeited' if forfeit else f'{my_hits}–{opp_hits}'
        ctx['past_games'] = past_games
        return ctx

    def post(self, request):
        action = request.POST.get('action')
        if action == 'create':
            game = ShyshipGame.objects.create(
                player1=request.user,
                ships_p1=place_ships_randomly(),
            )
            return redirect('shyship:game', game_id=game.pk)
        if action == 'join':
            game_id = request.POST.get('game_id')
            game = get_object_or_404(
                ShyshipGame, pk=game_id, status=ShyshipGame.WAITING
            )
            if game.player1 != request.user:
                game.player2 = request.user
                game.ships_p2 = place_ships_randomly()
                game.status = ShyshipGame.ACTIVE
                game.save(update_fields=['player2', 'ships_p2', 'status'])
            return redirect('shyship:game', game_id=game.pk)
        return redirect('shyship:lobby')


class GameView(ShyshipAccessMixin, TemplateView):
    template_name = 'shyship/game.html'

    def get(self, request, game_id):
        game = get_object_or_404(
            ShyshipGame.objects.select_related('player1', 'player2').annotate(move_count=Count('moves')),
            pk=game_id,
        )
        user = request.user
        if game.player1 == user:
            player_num = 1
            opponent = game.player2
        elif game.player2 == user:
            player_num = 2
            opponent = game.player1
        else:
            return redirect('shyship:lobby')

        return self.render_to_response({
            'game': game,
            'game_id': str(game_id),
            'player_num': player_num,
            'opponent': opponent,
        })


def _broadcast(game_id, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'shyship_{game_id}',
        {'type': 'game_event', 'data': data},
    )


class CancelView(ShyshipAccessMixin, View):
    def post(self, request, game_id):
        game = get_object_or_404(
            ShyshipGame,
            pk=game_id,
            player1=request.user,
            status__in=[ShyshipGame.WAITING, ShyshipGame.ACTIVE],
        )
        if ShyshipMove.objects.filter(game=game).exists():
            return redirect('shyship:lobby')
        ShyshipGame.objects.filter(pk=game_id).update(status=ShyshipGame.CANCELLED)
        _broadcast(game_id, {'type': 'game_cancelled'})
        return redirect('shyship:lobby')


class ForfeitView(ShyshipAccessMixin, View):
    def post(self, request, game_id):
        game = get_object_or_404(
            ShyshipGame.objects.select_related('player1', 'player2'),
            pk=game_id,
            status=ShyshipGame.ACTIVE,
        )
        if game.player1 == request.user:
            player_num = 1
        elif game.player2 == request.user:
            player_num = 2
        else:
            raise PermissionDenied
        ShyshipGame.objects.filter(pk=game_id).update(
            status=ShyshipGame.DONE,
            winner=3 - player_num,
        )
        _broadcast(game_id, {'type': 'game_forfeited', 'by': player_num})
        return redirect('shyship:lobby')
