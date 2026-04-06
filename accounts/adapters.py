from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if hasattr(user, 'is_verified'):
            user.is_verified = True
            user.save(update_fields=['is_verified'])
        return user
