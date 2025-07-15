from django import template

register = template.Library()

@register.filter
def to_range(value, arg):
    """
    Custom template filter to generate a range from value to arg.
    """
    return range(value, arg + 1)
