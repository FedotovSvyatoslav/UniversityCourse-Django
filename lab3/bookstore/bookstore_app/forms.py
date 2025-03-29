from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ["title", "author", "publisher", "cost"]


class CustomRegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('user', 'Обычный пользователь'),
        ('admin', 'Администратор'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Роль",
                             required=True)

    username = forms.CharField(max_length=150, label="Логин")
    first_name = forms.CharField(max_length=150, label="Имя")
    email = forms.EmailField(required=True, label="Электронная почта")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    password2 = forms.CharField(widget=forms.PasswordInput,
                                label="Подтверждение пароля")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email', 'password1', 'password2',
                  'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].validators = []
        self.fields['password2'].validators = []

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            role = self.cleaned_data['role']
            user.is_staff = False
            user.is_superuser = False
            if role == 'admin':
                user.is_staff = True
            user.save()
        return user
