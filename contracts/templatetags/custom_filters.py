# contracts/templatetags/custom_filters.py

from django import template
from contracts.utils import get_default_paragraph_text, num_to_uz_cyrillic_text
import re

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def max_value(lst):
    try:
        return max(lst)
    except:
        return None

@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def spaced_float(value, decimals=2):
    try:
        value = float(value)
        parts = f"{value:,.{int(decimals)}f}".split(".")
        integer_part = parts[0].replace(",", " ")  # use '\u00A0' for non-breaking space
        return f"{integer_part}.{parts[1]}" if len(parts) > 1 else integer_part
    except (ValueError, TypeError):
        return value

@register.filter
def num_to_uz_text(value):
    return num_to_uz_cyrillic_text(value)

@register.filter
def get_default_text(paragraph_number):
    return get_default_paragraph_text(paragraph_number)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def br2nl(value):
    """Convert <br>, <br/> or <br /> to newlines for textarea display."""
    if value is None:
        return ''
    # Replace different forms of <br> tags with \n
    return re.sub(r'(<br\s*/?>)', '\n', value, flags=re.IGNORECASE)