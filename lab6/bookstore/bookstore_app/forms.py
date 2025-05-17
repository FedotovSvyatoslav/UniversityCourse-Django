from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
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

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username or not username.isalnum() or '_' not in username and \
                not username.isalnum():
            raise forms.ValidationError(
                "Имя пользователя может содержать только "
                "буквы, цифры и подчёркивание.")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        if password1 and len(password1) < 8:
            raise forms.ValidationError(
                "Пароль должен содержать не менее 8 символов.")
        return password2

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


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'email']

    def save(self, commit=True, is_staff=False):
        user = super().save(commit=False)
        user.is_staff = is_staff
        user.is_superuser = False
        if commit:
            user.save()
        return user


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем валидаторы пароля, чтобы не требовать сложный пароль
        self.fields['new_password1'].validators = []
        self.fields['new_password2'].validators = []