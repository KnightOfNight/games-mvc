from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Profile'
    fields = ['gamer_tag']


class UserWithProfileAdmin(UserAdmin):
    inlines = [UserProfileInline]

    def save_formset(self, request, form, formset, change):
        if formset.model is not UserProfile:
            return super().save_formset(request, form, formset, change)
        instances = formset.save(commit=False)
        for instance in instances:
            existing = UserProfile.objects.filter(user=instance.user).first()
            if existing:
                existing.gamer_tag = instance.gamer_tag or None
                existing.save()
            else:
                instance.save()
        formset.save_m2m()


admin.site.unregister(User)
admin.site.register(User, UserWithProfileAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'gamer_tag', 'display_name']
    search_fields = ['user__username', 'gamer_tag']
