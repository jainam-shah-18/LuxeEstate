"""
Comprehensive forms for the LuxeEstate application
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from accounts.models import Profile
from properties.models import Property, PropertyImage, PropertyReview
from messaging.models import Message


# ============================================
# User Registration & Authentication Forms
# ============================================

class CustomUserCreationForm(UserCreationForm):
    """Custom user registration form"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    user_type = forms.ChoiceField(
        choices=[
            ('buyer', 'I am a Buyer/Renter'),
            ('owner', 'I am a Property Owner'),
            ('agent', 'I am a Property Agent')
        ],
        widget=forms.RadioSelect()
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2', 'user_type')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email


class OTPVerificationForm(forms.Form):
    """Form for OTP verification"""
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 6-digit code',
            'class': 'form-control text-center',
            'style': 'font-size: 1.5rem; letter-spacing: 10px;'
        })
    )
    
    def clean_otp_code(self):
        otp = self.cleaned_data['otp_code'].strip()
        if not otp.isdigit():
            raise forms.ValidationError('OTP must contain only digits.')
        return otp


class ProfileForm(forms.ModelForm):
    """Form for user profile"""
    class Meta:
        model = Profile
        fields = ['phone', 'bio', 'profile_picture', 'favorite_cities', 'preferred_property_type']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your phone number'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'favorite_cities': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Comma-separated cities (e.g., Mumbai, Delhi, Bangalore)'
            }),
            'preferred_property_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Apartment, Villa, House'
            }),
        }


# ============================================
# Property Forms
# ============================================

class PropertyForm(forms.ModelForm):
    """Form for creating/editing properties"""
    
    class Meta:
        model = Property
        fields = [
            'title', 'description',
            'property_type', 'city', 'state', 'address', 'pincode',
            'latitude', 'longitude',
            'price', 'bedrooms', 'bathrooms', 'area_sqft',
            'furnishing', 'status',
            'amenities'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Property Title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Detailed property description'
            }),
            'property_type': forms.Select(attrs={
                'class': 'form-control'
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
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Latitude',
                'step': 'any'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Longitude',
                'step': 'any'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price in Rupees'
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


class PropertyImageForm(forms.ModelForm):
    """Form for property images"""
    
    class Meta:
        model = PropertyImage
        fields = ['image', 'alt_text', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Image description'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class PropertySearchForm(forms.Form):
    """Advanced property search form"""
    
    SORT_CHOICES = [
        ('-created_at', 'Newest First'),
        ('price', 'Price: Low to High'),
        ('-price', 'Price: High to Low'),
        ('-views_count', 'Most Viewed'),
        ('-rating', 'Highest Rated'),
    ]
    
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City',
        })
    )
    
    property_type = forms.MultipleChoiceField(
        required=False,
        choices=Property.PROPERTY_TYPES,
        widget=forms.CheckboxSelectMultiple(),
        help_text='Select one or more property types'
    )
    
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Price',
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Price',
        })
    )
    
    bedrooms = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bedrooms',
        })
    )
    
    bathrooms = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bathrooms',
        })
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    furnishing = forms.MultipleChoiceField(
        required=False,
        choices=Property.FURNISHING_CHOICES,
        widget=forms.CheckboxSelectMultiple()
    )


class PropertyReviewForm(forms.ModelForm):
    """Form for property reviews"""
    
    class Meta:
        model = PropertyReview
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, '★' * i) for i in range(1, 6)]),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Review Title'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your thoughts about this property'
            }),
        }


# ============================================
# Messaging Forms
# ============================================

class MessageForm(forms.ModelForm):
    """Form for sending messages"""
    
    class Meta:
        model = Message
        fields = ['message', 'image']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your message...',
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }


class ContactAgentForm(forms.Form):
    """Form for contacting property agent"""
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your message to the agent...'
        }),
        label='Message'
    )
    
    contact_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your phone number'
        }),
        label='Phone Number'
    )
    
    preferred_contact_time = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Preferred contact time (e.g., 10:00 AM - 2:00 PM)'
        }),
        label='Preferred Contact Time'
    )


# ============================================
# Utility Forms
# ============================================

class SaveSearchForm(forms.Form):
    """Form for saving property search"""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Give this search a name'
        }),
        label='Search Name'
    )
    
    notify_on_new = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Notify me when new properties match this search'
    )
