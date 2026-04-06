from django import forms
from django.forms import inlineformset_factory

from .models import Property, PropertyImage, NearbyLocation, UserProfile


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title',
            'description',
            'price',
            'city',
            'address',
            'property_type',
            'latitude',
            'longitude',
            'is_featured',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'id': 'id_address'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'latitude': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control', 'id': 'id_latitude'}),
            'longitude': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control', 'id': 'id_longitude'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in self.Meta.widgets and 'class' not in field.widget.attrs:
                field.widget.attrs.setdefault('class', 'form-control')


class PropertyImageEntryForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ('image',)
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class NearbyLocationEntryForm(forms.ModelForm):
    class Meta:
        model = NearbyLocation
        fields = ('place_type', 'name', 'distance', 'place_id', 'latitude', 'longitude')
        widgets = {
            'place_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name (search with Google below)'}),
            'distance': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1.2 km'}),
            'place_id': forms.HiddenInput(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }


PropertyImageFormSet = inlineformset_factory(
    Property,
    PropertyImage,
    form=PropertyImageEntryForm,
    extra=3,
    max_num=12,
    can_delete=True,
)

NearbyLocationFormSet = inlineformset_factory(
    Property,
    NearbyLocation,
    form=NearbyLocationEntryForm,
    extra=12,
    max_num=40,
    can_delete=True,
)


class UserProfileForm(forms.ModelForm):
    preferred_cities = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'form-control',
            'placeholder': 'Enter cities separated by commas (e.g., Mumbai, Delhi, Bangalore)'
        }),
        help_text="Cities you're interested in"
    )
    preferred_property_types = forms.MultipleChoiceField(
        required=False,
        choices=Property.PROPERTY_TYPES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Select property types you prefer"
    )

    class Meta:
        model = UserProfile
        fields = ['budget_min', 'budget_max', 'preferred_cities', 'preferred_property_types']
        widgets = {
            'budget_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minimum budget (₹)',
                'step': '10000'
            }),
            'budget_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maximum budget (₹)',
                'step': '10000'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['preferred_cities'].initial = ', '.join(self.instance.preferred_cities)
            self.fields['preferred_property_types'].initial = self.instance.preferred_property_types

    def clean_preferred_cities(self):
        cities = self.cleaned_data.get('preferred_cities', '')
        if cities:
            return [city.strip() for city in cities.split(',') if city.strip()]
        return []

    def clean_preferred_property_types(self):
        types = self.cleaned_data.get('preferred_property_types', [])
        return types
