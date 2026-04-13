from django import forms
from .models import Payment, Subscription, PaymentPackage


class PaymentForm(forms.ModelForm):
    """Form for payment creation"""
    class Meta:
        model = Payment
        fields = ['package', 'notes']
        widgets = {
            'package': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add any notes (optional)'
            }),
        }


class SubscriptionForm(forms.ModelForm):
    """Form for subscription management"""
    class Meta:
        model = Subscription
        fields = ['package', 'auto_renew']
        widgets = {
            'package': forms.Select(attrs={'class': 'form-control'}),
            'auto_renew': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PackageSelectionForm(forms.Form):
    """Form for package selection"""
    package = forms.ModelChoiceField(
        queryset=PaymentPackage.objects.filter(is_active=True),
        widget=forms.RadioSelect(),
        empty_label=None
    )
