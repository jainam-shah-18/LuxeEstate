from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


def _style(fields):
    for field in fields.values():
        w = field.widget
        if isinstance(w, forms.CheckboxInput):
            field.widget.attrs.setdefault('class', 'form-check-input')
        else:
            field.widget.attrs.setdefault('class', 'form-control')


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields)
        self.fields['email'].widget.attrs['placeholder'] = 'you@example.com'


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, label='Enter OTP', widget=forms.TextInput(attrs={'autocomplete': 'one-time-code'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields)


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'autocomplete': 'email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields)
