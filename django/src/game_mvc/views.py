from django.views.generic import TemplateView

_GAME_GROUPS = {
    'can_play_shydle':  'players.shydle',
    'can_play_shyship': 'players.shyship',
    'can_play_shyland': 'players.shyland',
}


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated and user.is_superuser:
            ctx.update({key: True for key in _GAME_GROUPS})
        elif user.is_authenticated:
            user_groups = set(user.groups.values_list('name', flat=True))
            ctx.update({key: grp in user_groups for key, grp in _GAME_GROUPS.items()})
        else:
            ctx.update({key: False for key in _GAME_GROUPS})
        return ctx
