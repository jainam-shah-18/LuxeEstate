"""
Forms for the properties app
"""
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Property, PropertyImage, PropertyReview
from messaging.models import Message


class PropertyForm(forms.ModelForm):
    """Form for creating and editing properties"""
    
    amenities = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Swimming Pool\nGym\nParking\nGarden\nSecurity'
        }),
        help_text='List each amenity on a new line'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert amenities list to newline-separated string for display in textarea
        if self.instance and self.instance.pk and self.instance.amenities:
            if isinstance(self.instance.amenities, list):
                self.fields['amenities'].initial = '\n'.join(str(a).strip() for a in self.instance.amenities if a)
            else:
                self.fields['amenities'].initial = str(self.instance.amenities)
    
    class Meta:
        model = Property
        fields = [
            'title',
            'description',
            'price',
            'city',
            'state',
            'address',
            'pincode',
            'property_type',
            'bedrooms',
            'bathrooms',
            'area_sqft',
            'furnishing',
            'status',
            'amenities',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Property Title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Detailed description of the property'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price in Rupees'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Complete Address'
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pincode'
            }),
            'property_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'bedrooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of Bedrooms'
            }),
            'bathrooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of Bathrooms'
            }),
            'area_sqft': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Area in Square Feet'
            }),
            'furnishing': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def clean_amenities(self):
        """Parse amenities string into a list"""
        amenities_text = self.cleaned_data.get('amenities', '')
        if not amenities_text:
            return []
        
        # Split by newline and comma, trim whitespace, remove empty strings
        items = []
        for line in str(amenities_text).split('\n'):
            for part in line.split(','):
                value = part.strip()
                if value:
                    items.append(value)
        return items

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError('Price must be greater than 0')
        return price

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title) < 5:
            raise forms.ValidationError('Title must be at least 5 characters long')
        return title

    def save(self, commit=True):
        """Override save to ensure amenities is saved as a list"""
        instance = super().save(commit=False)
        
        # Ensure amenities is saved as a list
        amenities = self.cleaned_data.get('amenities', [])
        if isinstance(amenities, str):
            instance.amenities = [a.strip() for a in amenities.split('\n') if a.strip()]
        else:
            instance.amenities = amenities if amenities else []
        
        if commit:
            instance.save()
        return instance


class PropertyImageForm(forms.ModelForm):
    """Form for uploading property images"""
    
    class Meta:
        model = PropertyImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }


class PropertySearchForm(forms.Form):
    """Form for searching and filtering properties"""
    
    PROPERTY_TYPE_CHOICES = [
        ('', 'All Types'),
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('plot', 'Plot'),
        ('commercial', 'Commercial'),
    ]

    keyword = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title or description...',
        })
    )

    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter city name...',
        })
    )

    property_type = forms.ChoiceField(
        choices=PROPERTY_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum price...',
            'step': '100',
        })
    )

    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Maximum price...',
            'step': '100',
        })
    )

    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('-created_at', 'Newest First'),
            ('price', 'Price: Low to High'),
            ('-price', 'Price: High to Low'),
            ('-views_count', 'Most Viewed'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
