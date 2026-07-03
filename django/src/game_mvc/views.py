from django import forms
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.views.generic import TemplateView

_GAME_GROUPS = {
    'can_play_shydle':  'players.shydle',
    'can_play_shyship': 'players.shyship',
    'can_play_shyland': 'players.shyland',
}


class StrictPasswordChangeForm(PasswordChangeForm):
    def clean(self):
        cleaned = super().clean()
        old = cleaned.get('old_password')
        new = cleaned.get('new_password1')
        if old and new and old == new:
            raise forms.ValidationError('New password must be different from your current password.')
        return cleaned


class SettingsPasswordChangeView(PasswordChangeView):
    form_class = StrictPasswordChangeForm
    template_name = 'registration/password_change_form.html'
    success_url = '/'

    def form_valid(self, form):
        messages.success(self.request, 'Password changed successfully.')
        return super().form_valid(form)


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
