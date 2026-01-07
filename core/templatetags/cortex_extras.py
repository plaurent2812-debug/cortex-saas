from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def blur_if_free(user, value):
    """
    Returns the value if user is premium, otherwise returns a blurred placeholder.
    Usage: {% blur_if_free request.user some_value %}
    """
    is_premium = getattr(user, 'is_premium', False)
    
    if is_premium:
        return value
    else:
        return mark_safe('<span class="blur-sm select-none">🔒 PREMIUM</span>')

@register.filter(name='is_premium_check')
def is_premium_check(user):
    return getattr(user, 'is_premium', False)
