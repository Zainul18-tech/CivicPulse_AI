
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from department_portal.models import Department, DepartmentProfile



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
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="Select a department",
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "username",
            "email",
            "department",
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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        user.is_staff = True
        user.is_superuser = False

        if commit:
            user.save()
            department = self.cleaned_data["department"]
            if department:
                DepartmentProfile.objects.update_or_create(
                    user=user,
                    defaults={"department": department},
                )

        return user
