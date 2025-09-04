from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0 

@register.filter
def class_name(obj):
    """Get the class name of an object"""
    return obj.__class__.__name__ 