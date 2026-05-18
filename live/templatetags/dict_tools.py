from django import template

register = template.Library()


@register.filter
def get_item(d, key):
    if d is None:
        return None
    return d.get(key)


@register.simple_tag
def get_pair(d, a, b):
    """
    d est un dict dont les clés sont des tuples (a,b)
    Retourne d[(a,b)] ou "" si absent.
    """
    if d is None:
        return ""
    return d.get((a, b), "")
