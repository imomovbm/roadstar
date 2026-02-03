# your_app/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    department = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hash password
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                department=self.cleaned_data['department']
            )
        return user
