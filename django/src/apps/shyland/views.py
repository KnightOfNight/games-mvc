from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, View

from .combat_utils import recalculate_bars
from .forms import CharacterCreationForm
from .models import Character, Room

GROUP_NAME = 'players.shyland'


class ShylandAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.groups.filter(name=GROUP_NAME).exists()):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def _gamer_tag(user):
    return getattr(getattr(user, 'profile', None), 'gamer_tag', None)


def _default_character_name(user):
    # Truncated so the pre-filled default always fits Character.name — a bare
    # username can be up to 150 chars.
    return (_gamer_tag(user) or user.username)[:20]


class GameView(ShylandAccessMixin, TemplateView):
    template_name = 'shyland/game.html'

    def get(self, request, *args, **kwargs):
        if not Character.objects.filter(user=request.user).exists():
            return redirect('shyland:create_character')
        return super().get(request, *args, **kwargs)


class CharacterCreateView(ShylandAccessMixin, View):
    template_name = 'shyland/character_create.html'

    def get(self, request):
        if Character.objects.filter(user=request.user).exists():
            return redirect('shyland:game')
        form = CharacterCreationForm(
            default_name=_default_character_name(request.user),
            vetted_name=_gamer_tag(request.user),
        )
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if Character.objects.filter(user=request.user).exists():
            return redirect('shyland:game')
        form = CharacterCreationForm(
            request.POST,
            default_name=_default_character_name(request.user),
            vetted_name=_gamer_tag(request.user),
        )
        if form.is_valid():
            origin = form.cleaned_data['origin']
            archetype = form.cleaned_data['archetype']
            name = form.cleaned_data['name']

            spawn_room = Room.objects.filter(
                zone__slug='the-convergence', coord_x=0, coord_y=0, coord_z=0,
            ).first()
            if spawn_room is None:
                form.add_error(None, 'Spawn point is not configured. Contact an admin.')
                return render(request, self.template_name, {'form': form})

            stats = {'str': 8, 'dex': 8, 'end': 8, 'int': 8, 'wis': 8, 'per': 8}
            stats[archetype.primary_stat_1] = 18
            stats[archetype.primary_stat_2] = 18

            character = Character(
                user=request.user,
                name=name,
                origin=origin,
                archetype=archetype,
                current_room=spawn_room,
                recall_room=spawn_room,
                stat_str=stats['str'], stat_dex=stats['dex'], stat_end=stats['end'],
                stat_int=stats['int'], stat_wis=stats['wis'], stat_per=stats['per'],
                acuity_current=origin.acuity_baseline,
                acuity_baseline=origin.acuity_baseline,
                acuity_band_low=origin.acuity_band_low,
                acuity_band_high=origin.acuity_band_high,
            )
            recalculate_bars(character)  # sets vitality/longevity max + current from stats
            # The form's exists() checks are only advisory — concurrent submits
            # can both pass them, so the DB constraints are the real gate.
            try:
                with transaction.atomic():
                    character.save()
            except IntegrityError:
                if Character.objects.filter(user=request.user).exists():
                    return redirect('shyland:game')
                form.add_error('name', 'That name is already taken.')
                return render(request, self.template_name, {'form': form})

            return redirect('shyland:game')
        return render(request, self.template_name, {'form': form})


class CheckNameView(ShylandAccessMixin, View):
    def get(self, request):
        name = request.GET.get('name', '').strip()
        form = CharacterCreationForm(
            {'name': name, 'origin': '', 'archetype': ''},
            default_name=_default_character_name(request.user),
            vetted_name=_gamer_tag(request.user),
        )
        form.is_valid()  # populate errors; origin/archetype errors are expected and ignored here
        name_errors = form.errors.get('name')
        return JsonResponse({
            'available': not bool(name_errors),
            'error': name_errors[0] if name_errors else None,
        })
