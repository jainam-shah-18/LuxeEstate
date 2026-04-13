from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.dispatch import receiver


def _sync_google_profile(sociallogin):
    if not sociallogin or not getattr(sociallogin, "user", None):
        return

    user = sociallogin.user
    profile = getattr(user, "profile", None)
    if not profile:
        return

    account = sociallogin.account
    if account and account.provider == "google":
        profile.is_google_account = True
        profile.google_id = account.uid
        profile.email_verified = True
        profile.otp_code = None
        profile.save(update_fields=["is_google_account", "google_id", "email_verified", "otp_code"])


@receiver(social_account_added)
def handle_social_account_added(request, sociallogin, **kwargs):
    _sync_google_profile(sociallogin)


@receiver(social_account_updated)
def handle_social_account_updated(request, sociallogin, **kwargs):
    _sync_google_profile(sociallogin)

