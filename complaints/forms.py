
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Complaint


class CitizenSignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Full name",
    )

    email = forms.EmailField(
        required=True,
        label="Email address",
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "username",
            "email",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email


from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class StaffCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email address")
    first_name = forms.CharField(max_length=150, required=True, label="Full name")

    class Meta:
        model = User
        fields = ["first_name", "username", "email", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        user.is_staff = True
        user.is_superuser = False

        if commit:
            user.save()

        return user



class ComplaintSubmissionForm(forms.ModelForm):
    LANGUAGE_CHOICES = [
        ("English", "English"),
        ("Tamil", "Tamil"),
        ("Hindi", "Hindi"),
    ]

    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        widget=forms.Select(attrs={"class": "form-input"}),
    )

    class Meta:
        model = Complaint
        fields = [
            "title",
            "description",
            "citizen_priority",
            "language",
            "location",
            "latitude",
            "longitude",
            "evidence_image",
            "live_image",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Example: Streetlight not working",
                "maxlength": 150,
            }),
            "description": forms.Textarea(attrs={
                "class": "form-input",
                "rows": 5,
                "placeholder": "Describe the problem, its impact, and nearby landmarks.",
            }),
            "citizen_priority": forms.Select(attrs={
                "class": "form-input",
            }),
            "location": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Enter the address or nearby landmark",
                "maxlength": 255,
            }),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
            "evidence_image": forms.ClearableFileInput(attrs={
                "accept": "image/*",
            }),
            "live_image": forms.ClearableFileInput(attrs={
                "accept": "image/*",
                "capture": "environment",
            }),
        }

    def clean_evidence_image(self):
        image = self.cleaned_data.get("evidence_image")
        if image and image.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "Evidence image must be 5 MB or smaller."
            )
        return image

    def clean_live_image(self):
        image = self.cleaned_data.get("live_image")
        if image and image.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "Live photo must be 5 MB or smaller."
            )
        return image

    def clean(self):
        cleaned_data = super().clean()

        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")

        if latitude is not None and not -90 <= latitude <= 90:
            self.add_error("latitude", "Latitude must be between -90 and 90.")

        if longitude is not None and not -180 <= longitude <= 180:
            self.add_error("longitude", "Longitude must be between -180 and 180.")

        return cleaned_data
