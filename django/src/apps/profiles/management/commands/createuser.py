import getpass

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from apps.profiles.models import UserProfile

PLAYER_GROUPS = [
    'players.shyship',
    'players.shydle',
    'players.shyland',
]


class Command(BaseCommand):
    help = 'Create or update a player account and assign game group memberships'

    def handle(self, *args, **options):
        username = input('Username: ').strip()
        if not username:
            self.stderr.write('Username cannot be blank.')
            return

        user = User.objects.filter(username=username).first()
        updating = user is not None

        if updating:
            self.stdout.write(f'\nUpdating existing user "{username}"\n' + '-' * 40)
            profile = user.profile
        else:
            self.stdout.write(f'\nCreating new user "{username}"\n' + '-' * 40)
            profile = None

        def prompt(label, current=None):
            hint = f' [{current}]' if current else ''
            value = input(f'{label}{hint}: ').strip()
            return value if value else current

        email      = prompt('Email (optional)',      user.email if updating else None)
        first_name = prompt('First name (optional)', user.first_name if updating else None)
        last_name  = prompt('Last name (optional)',  user.last_name if updating else None)

        if updating:
            self.stdout.write('Password (leave both blank to keep current):')
        while True:
            password = getpass.getpass('Password: ')
            confirm  = getpass.getpass('Confirm password: ')
            if password == confirm:
                break
            self.stdout.write('Passwords do not match, try again.')

        current_tag = profile.gamer_tag if profile else None
        gamer_tag_raw = prompt('Gamer tag (optional, max 20 chars)', current_tag)
        gamer_tag = gamer_tag_raw[:20] if gamer_tag_raw else None
        if gamer_tag and gamer_tag != current_tag:
            if UserProfile.objects.filter(gamer_tag=gamer_tag).exists():
                self.stderr.write(f'Gamer tag "{gamer_tag}" is already taken.')
                return

        current_groups = set(user.groups.values_list('name', flat=True)) if updating else set()
        self.stdout.write('\nAvailable groups:')
        for i, name in enumerate(PLAYER_GROUPS, 1):
            marker = '*' if name in current_groups else ' '
            self.stdout.write(f'  [{i}]{marker} {name}')
        if updating:
            self.stdout.write('  (* = currently assigned)')

        if updating:
            group_prompt = '\nEnter group numbers (comma-separated, blank to keep current): '
        else:
            group_prompt = '\nEnter group numbers (comma-separated, or blank for none): '
        raw = input(group_prompt).strip()
        selected_groups = []
        if raw:
            for part in raw.split(','):
                try:
                    idx = int(part.strip()) - 1
                    if 0 <= idx < len(PLAYER_GROUPS):
                        selected_groups.append(PLAYER_GROUPS[idx])
                except ValueError:
                    pass
        elif updating:
            selected_groups = [g for g in current_groups if g in PLAYER_GROUPS]

        if updating:
            user.email      = email
            user.first_name = first_name
            user.last_name  = last_name
            if password:
                user.set_password(password)
            user.save()
            UserProfile.objects.filter(user=user).update(gamer_tag=gamer_tag)
            player_groups = [g for g in PLAYER_GROUPS]
            keep    = [g for g in selected_groups]
            remove  = [g for g in player_groups if g not in keep]
            for name in keep:
                group, _ = Group.objects.get_or_create(name=name)
                user.groups.add(group)
            for name in remove:
                try:
                    user.groups.remove(Group.objects.get(name=name))
                except Group.DoesNotExist:
                    pass
            verb = 'Updated'
        else:
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name,
            )
            UserProfile.objects.filter(user=user).update(gamer_tag=gamer_tag)
            for name in selected_groups:
                group, _ = Group.objects.get_or_create(name=name)
                user.groups.add(group)
            verb = 'Created'

        self.stdout.write(self.style.SUCCESS(
            f'\n{verb} user "{username}"'
            + (f' with groups: {", ".join(selected_groups)}' if selected_groups else ' (no groups)')
        ))
