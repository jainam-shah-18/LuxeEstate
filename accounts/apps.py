from django.apps import AppConfig
from django.conf import settings
from django.core.signals import request_started


class AccountsConfig(AppConfig):
    name = 'accounts'
    _google_social_app_synced = False

    def ready(self):
        # Register auth/account signal handlers.
        from . import signals  # noqa: F401
        request_started.connect(self._sync_google_social_app, weak=False)

    def _sync_google_social_app(self, **kwargs):
        if self._google_social_app_synced:
            return

        google_client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
        google_client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '')
        if not google_client_id or not google_client_secret:
            return

        try:
            from django.contrib.sites.models import Site
            from allauth.socialaccount.models import SocialApp
            from django.db.utils import OperationalError, ProgrammingError

            site = Site.objects.get_current()
            app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': google_client_id,
                    'secret': google_client_secret,
                },
            )

            updated = False
            if app.client_id != google_client_id:
                app.client_id = google_client_id
                updated = True
            if app.secret != google_client_secret:
                app.secret = google_client_secret
                updated = True
            if site not in app.sites.all():
                app.sites.add(site)
                updated = True
            if updated:
                app.save()
            self._google_social_app_synced = True
        except (OperationalError, ProgrammingError):
            # Database is not ready yet (migrate / initial setup), so skip sync.
            pass
