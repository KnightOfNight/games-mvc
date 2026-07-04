from better_profanity import profanity
from django import forms

from .models import Archetype, Character, Origin


class CharacterCreationForm(forms.Form):
    origin = forms.ModelChoiceField(queryset=Origin.objects.all(), empty_label=None)
    archetype = forms.ModelChoiceField(queryset=Archetype.objects.all(), empty_label=None)
    name = forms.CharField(max_length=20)

    def __init__(self, *args, default_name='', vetted_name=None, **kwargs):
        self.default_name = default_name
        # Only a set gamer tag skips the profanity check — the username
        # fallback default has no upstream vetting and must be checked.
        self.vetted_name = vetted_name
        super().__init__(*args, **kwargs)
        self.fields['name'].initial = default_name

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Name cannot be blank.')
        if len(name) > 20:
            raise forms.ValidationError('Name must be 20 characters or fewer.')

        if Character.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError('That name is already taken.')

        if name != self.vetted_name and profanity.contains_profanity(name):
            raise forms.ValidationError('That name is not allowed.')

        return name
