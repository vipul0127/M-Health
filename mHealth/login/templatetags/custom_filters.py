# myapp/templatetags/custom_filters.py
from django import template

register = template.Library()



@register.filter
def my_custom_filter(value):
    # Your filter logic here
    return value

# custom_filters.py
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

