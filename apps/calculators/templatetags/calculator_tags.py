from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Повертає значення з dictionary за динамічним ключем."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
