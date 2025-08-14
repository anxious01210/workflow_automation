from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def active_class(context, url_name):
    cur = getattr(getattr(context.get("request"), "resolver_match", None), "view_name", "")
    return "bg-base-200 font-semibold" if cur == url_name else ""

# def active_class(context, url_name):
#     try:
#         current = context["request"].resolver_match.view_name
#     except Exception:
#         return ""
#     return "bg-base-200 font-semibold" if current == url_name else ""
