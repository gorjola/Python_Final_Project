from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ProfileUpdateForm(forms.ModelForm):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'username': 'მომხმარებლის სახელი',
            'email': 'ელ-ფოსტა'
        }
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'მომხმარებელი'}),
            'email': forms.EmailInput(attrs={'placeholder': 'example@email.com'}),
        }