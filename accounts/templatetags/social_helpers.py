from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.templatetags.socialaccount import provider_login_url
from django.core.exceptions import MultipleObjectsReturned
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def safe_provider_login_url(context, provider, **kwargs):
    """Return provider URL or empty string when social app config is invalid."""
    request = context.get("request")
    if request is None:
        return ""

    try:
        return provider_login_url(context, provider, **kwargs)
    except (SocialApp.DoesNotExist, MultipleObjectsReturned):
        return ""
