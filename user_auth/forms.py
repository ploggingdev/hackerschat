from django import forms
from django.core.validators import RegexValidator
from .models import UserProfile

class RegisterForm(forms.Form):
    username = forms.CharField(label='Username', max_length=20, validators=[RegexValidator(r'^[a-zA-Z0-9-_]+$', "Only letters, digits, hyphen and underscore without spaces are allowed")])
    password = forms.CharField(label='Password', max_length=100, widget=forms.PasswordInput)
    email = forms.EmailField()

class ProfileForm(forms.Form):
    email = forms.EmailField()
    about = forms.CharField(max_length=1000, widget=forms.Textarea)

class AdminUserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['user', 'about']
        widgets = {
            'about': forms.Textarea(attrs={'rows': 10}),
        }