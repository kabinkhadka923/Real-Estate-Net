from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import User, RealEstateAgentApplication

class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Your phone number'})
    )
    address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Your address'})
    )
    # Limit choices to prevent direct registration as agent
    REGISTRATION_USER_TYPES = (
        ('broker', 'Real Estate Broker'),
        ('buyer', 'Property Buyer'),
    )
    user_type = forms.ChoiceField(
        choices=REGISTRATION_USER_TYPES,
        required=True,
        initial='buyer',
        label="Account Type (Required)",
        help_text="Select your role: Property Buyer or Real Estate Broker. To become a Real Estate Agent, you must apply separately after registration."
    )
    agree_terms = forms.BooleanField(
        required=True,
        label=mark_safe('I agree to the <a href="/legal/privacy-policy/" '
                        'target="_blank">Privacy Policy</a> and '
                        '<a href="/legal/terms-of-service/" target="_blank">'
                        'Terms of Service</a>.'),
        error_messages={
            'required': 'You must agree to the Privacy Policy and Terms '
                        'of Service to register.'
        }
    )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.agree_terms = self.cleaned_data['agree_terms']
        user.terms_accepted_date = timezone.now() if self.cleaned_data[
            'agree_terms'] else None
        user.phone_number = self.cleaned_data.get('phone_number') or ''
        user.address = self.cleaned_data.get('address') or ''
        user.user_type = self.cleaned_data.get('user_type', 'buyer')
        if commit:
            user.save()
        return user

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'password1', 'password2')  # Removed email field


class CustomAuthenticationForm(AuthenticationForm):
    pass


# Import SignupForm inside the function to avoid circular import
def create_custom_signup_form():
    from allauth.account.forms import SignupForm

    class CustomAllauthSignupForm(SignupForm):
        phone_number = forms.CharField(
            max_length=20,
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'Phone Number'})
        )
        address = forms.CharField(
            max_length=255,
            required=False,
            widget=forms.TextInput(attrs={'placeholder': 'Address'})
        )
        # Limit choices to prevent direct registration as agent
        user_type = forms.ChoiceField(
            choices=CustomUserCreationForm.REGISTRATION_USER_TYPES,
            initial='buyer',
            widget=forms.Select(),
            help_text="Select your role: Property Buyer or Real Estate Broker. To become a Real Estate Agent, you must apply separately after registration."
        )

        # Override password fields to remove allauth's built-in toggle
        password1 = forms.CharField(
            label='Password',
            widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        )
        password2 = forms.CharField(
            label='Confirm Password',
            widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        )
        agree_terms = forms.BooleanField(
            required=True,
            label=mark_safe('I agree to the <a href="/legal/privacy-policy/" '
                            'target="_blank">Privacy Policy</a> and '
                            '<a href="/legal/terms-of-service/" '
                            'target="_blank">Terms of Service</a>.'),
            error_messages={
                'required': 'You must agree to the Privacy Policy and Terms '
                            'of Service to register.'
            }
        )

        def save(self, request):
            # Save the user using allauth's save method
            user = super().save(request)

            # Update additional fields
            user.agree_terms = self.cleaned_data['agree_terms']
            user.terms_accepted_date = timezone.now() if self.cleaned_data[
                'agree_terms'] else None
            user.phone_number = self.cleaned_data.get('phone_number', '')
            user.address = self.cleaned_data.get('address', '')
            user.user_type = self.cleaned_data.get('user_type', 'buyer')

            # All new registrations are active and verified
            user.is_active = True
            user.is_verified = True
            user.verification_date = timezone.now()

            user.save()
            return user

    return CustomAllauthSignupForm


CustomAllauthSignupForm = create_custom_signup_form()


class RealEstateAgentApplicationForm(forms.ModelForm):
    """Form for real estate agent applications"""
    license_expiry = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="When does your license expire?"
    )

    class Meta:
        model = RealEstateAgentApplication
        fields = [
            'company_name', 'license_number', 'license_expiry', 'years_experience',
            'bio', 'specializations', 'contact_phone', 'contact_email',
            'license_document', 'id_document', 'business_registration'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about your experience in real estate...'}),
            'company_name': forms.TextInput(attrs={'placeholder': 'e.g., ABC Realty Company'}),
            'license_number': forms.TextInput(attrs={'placeholder': 'e.g., REL-12345-ABC'}),
            'years_experience': forms.NumberInput(attrs={'min': 0, 'placeholder': 'e.g., 5'}),
            'specializations': forms.TextInput(attrs={'placeholder': 'e.g., Residential Properties, Commercial'}),
            'contact_phone': forms.TextInput(attrs={'placeholder': 'Professional phone number'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'Professional email address'}),
        }


class AgentApplicationReviewForm(forms.ModelForm):
    """Form for admin to review and provide feedback on agent applications"""
    review_decision = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject'), ('needs_info', 'Request More Information')],
        label="Review Decision",
        widget=forms.RadioSelect()
    )

    class Meta:
        model = RealEstateAgentApplication
        fields = ['status', 'admin_feedback', 'requested_documents']
        widgets = {
            'admin_feedback': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Provide feedback, requirements, or rejection reasons...'
            }),
            'requested_documents': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'List any additional documents needed...'
            }),
        }
