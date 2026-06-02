from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    gamer_tag = models.CharField(max_length=20, unique=True, blank=True, default='')

    def __str__(self):
        return f'{self.user.username} ({self.gamer_tag or "no tag"})'

    def display_name(self):
        if self.gamer_tag:
            return self.gamer_tag
        full = self.user.get_full_name().strip()
        return full if full else self.user.username
