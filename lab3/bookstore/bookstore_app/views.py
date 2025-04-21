import os

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView

from .models import Book
from .forms import BookForm, CustomRegisterForm

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "../templates")
books_dir = os.path.join(templates_dir, "books")


def admin_permission_check(user):
    return user.is_authenticated and user.is_staff


def homepage_view(request):
    return HttpResponse("Hello, World!")


def books_list_view(request):
    context = {
        "books": [],
    }
    return render(request, "bookstore_app/book_list.html", context)


class BookListView(ListView):
    model = Book
    template_name = 'bookstore_app/templates/book_list.html'
    context_object_name = 'books'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        if 'admin_required' in request.GET:
            messages.error(request,
                           'У вас нет прав для выполнения этого действия.')
        return super().dispatch(request, *args, **kwargs)


@login_required
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'bookstore_app/book_form.html', {'form': form})


@login_required
@user_passes_test(admin_permission_check, login_url="book_list",
                  redirect_field_name="admin_required")
def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'bookstore_app/book_form.html', {'form': form})


@login_required
@user_passes_test(admin_permission_check, login_url="book_list",
                  redirect_field_name="admin_required")
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        return redirect('book_list')
    return render(request, 'bookstore_app/book_delete.html',
                  {'book': book})


def register(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт для {username} '
                                      f'успешно создан! Войдите в систему.')
            return redirect('login')
    else:
        form = CustomRegisterForm()
    return render(request, 'bookstore_app/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('book_list')
        messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()
    return render(request, 'bookstore_app/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('book_list')
