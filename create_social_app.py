import os

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

if not client_id or not client_secret:
    raise ValueError("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your environment.")

site = Site.objects.get(id=1)
app, created = SocialApp.objects.get_or_create(
    provider="google",
    defaults={
        "name": "Google",
        "client_id": client_id,
        "secret": client_secret,
    },
)
app.sites.add(site)
print("SocialApp created:", created)