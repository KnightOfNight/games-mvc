from django import template

register = template.Library()


@register.filter
def display_name(user):
    if user is None:
        return ''
    try:
        return user.profile.display_name()
    except AttributeError:
        pass
    full = user.get_full_name().strip()
    return full if full else user.username
