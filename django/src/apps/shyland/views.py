from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

GROUP_NAME = 'players.shyland'


class ShylandAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.groups.filter(name=GROUP_NAME).exists()):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class GameView(ShylandAccessMixin, TemplateView):
    template_name = 'shyland/game.html'
