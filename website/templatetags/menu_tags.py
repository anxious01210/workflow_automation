# website/templatetags/menu_tags.py
from django import template
from django.utils.safestring import mark_safe

try:
    from website.models import NavigationSettings
except Exception:
    NavigationSettings = None  # if models import fails, we still render a fallback

register = template.Library()


@register.inclusion_tag("partials/_primary_menu.html", takes_context=True)
def primary_menu(context):
    """
    Safe menu renderer. If settings or request isn't available, we return a harmless fallback
    so the page never crashes to a blank screen.
    """
    request = context.get("request")
    items = []
    settings = None

    if NavigationSettings and request:
        try:
            settings = NavigationSettings.for_request(request)
            items = list(getattr(settings, "items", []).all())
        except Exception:
            # leave settings=None, items=[]
            pass

    return {"settings": settings, "items": items, "request": request}
