from django import forms
from django.forms import modelformset_factory
from .models import Property, PropertyType, Amenity, Image

class PropertySearchForm(forms.Form):
    query = forms.CharField(max_length=255, required=False, label='Keywords')
    property_type = forms.ModelChoiceField(queryset=PropertyType.objects.all(), required=False, label='Property Type')
    min_price = forms.DecimalField(max_digits=15, decimal_places=2, required=False, label='Min Price')
    max_price = forms.DecimalField(max_digits=15, decimal_places=2, required=False, label='Max Price')
    min_sq_ft = forms.IntegerField(required=False, label='Min Square Footage')
    max_sq_ft = forms.IntegerField(required=False, label='Max Square Footage')
    amenities = forms.ModelMultipleChoiceField(queryset=Amenity.objects.all(), required=False, widget=forms.CheckboxSelectMultiple, label='Amenities')

    # Add more fields for other filters like location, year built, zoning, etc.
    city = forms.CharField(max_length=100, required=False, label='City')
    state = forms.CharField(max_length=100, required=False, label='State')
    zip_code = forms.CharField(max_length=20, required=False, label='Zip Code')
    lease_or_buy = forms.ChoiceField(choices=[('', 'Any')] + list(Property.PROPERTY_STATUS_CHOICES), required=False, label='Lease/Buy')
    cap_rate = forms.DecimalField(max_digits=5, decimal_places=2, required=False, label='Cap Rate')
    year_built = forms.IntegerField(required=False, label='Year Built')
    zoning = forms.CharField(max_length=100, required=False, label='Zoning')

class PropertyForm(forms.ModelForm):
    # Add location fields separately since they're related to the Location model
    latitude = forms.DecimalField(
        max_digits=10,
        decimal_places=8,
        required=False,
        widget=forms.HiddenInput(),
        help_text="Latitude coordinate from map"
    )
    longitude = forms.DecimalField(
        max_digits=11,
        decimal_places=8,
        required=False,
        widget=forms.HiddenInput(),
        help_text="Longitude coordinate from map"
    )

    class Meta:
        model = Property
        fields = [
            'title', 'description', 'property_type', 'address', 'city', 'state',
            'zip_code', 'country', 'price', 'square_footage', 'lot_size',
            'year_built', 'zoning', 'status', 'amenities', 'cap_rate', 'noi',
            'rent_roll', 'expense_summaries', 'broker_name', 'broker_email',
            'broker_phone', 'virtual_tour_url', 'floor_plan_image'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'rent_roll': forms.Textarea(attrs={'rows': 4}),
            'expense_summaries': forms.Textarea(attrs={'rows': 4}),
            'amenities': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Enter amenities (one per line or comma-separated):\n• Swimming Pool\n• Gym, Parking\n• Garden, Security'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for lat/lng if property has location
        if self.instance and self.instance.location:
            self.fields['latitude'].initial = self.instance.location.latitude
            self.fields['longitude'].initial = self.instance.location.longitude

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle location data
        latitude = self.cleaned_data.get('latitude')
        longitude = self.cleaned_data.get('longitude')

        if latitude and longitude:
            from .models import Location
            # Try to find existing location or create new one
            location, created = Location.objects.get_or_create(
                latitude=latitude,
                longitude=longitude,
                defaults={
                    'name': f"{latitude},{longitude}",
                    'type': 'address',
                }
            )
            instance.location = location

        if commit:
            instance.save()
        return instance

class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image', 'caption']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'accept': 'image/*'
            }),
        }

# Create formset for multiple images
ImageFormSet = modelformset_factory(
    Image,
    form=ImageForm,
    fields=['image', 'caption'],
    extra=1,  # Allow 1 blank form for single image upload
    can_delete=True,
    max_num=1  # Maximum 1 image
)
