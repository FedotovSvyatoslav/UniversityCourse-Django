import json
import os
from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView

from .models import Book
from .forms import BookForm, CustomRegisterForm, ProfileForm, \
    CustomPasswordChangeForm

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "../templates")
books_dir = os.path.join(templates_dir, "books")


def admin_permission_check(user):
    return user.is_authenticated and user.is_staff


def get_cart_cookie_name(request):
    if request.user.is_authenticated:
        return f'cart_{request.user.username}'
    return 'cart__'


def get_orders_cookie_name(request):
    if request.user.is_authenticated:
        return f'orders_{request.user.username}'
    return 'orders__'


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


@login_required
def profile(request):
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user,
                                                 data=request.POST)

        action = request.POST.get('action')
        role = request.POST.get('role')

        if action == 'update_profile' and profile_form.is_valid():
            profile_form.save(is_staff=(role == "admin" if role else False))
            messages.success(request, 'Ваши данные успешно обновлены!')
            return redirect('profile')
        elif action == 'change_password' and password_form.is_valid():
            password_form.save()
            messages.success(request, 'Ваш пароль успешно обновлен!')
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            return redirect('profile')
        else:
            if action == 'update_profile':
                messages.error(request, 'Ошибка при обновлении данных. '
                                        'Проверьте введённые данные.')
            elif action == 'change_password':
                messages.error(request, 'Ошибка при смене пароля.'
                                        ' Проверьте введённые данные.')
    else:
        profile_form = ProfileForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'bookstore_app/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })


def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    cart_cookie_name = get_cart_cookie_name(request)
    print(f"atc {cart_cookie_name = }")
    cart = request.COOKIES.get(cart_cookie_name, '{}')
    try:
        cart = json.loads(cart)
    except json.JSONDecodeError:
        cart = {}

    book_id_str = str(book_id)
    if book_id_str in cart:
        cart[book_id_str]['quantity'] += 1
    else:
        cart[book_id_str] = {
            'quantity': 1,
            'title': book.title,
            'author': book.author,
            'cost': str(book.cost) if book.cost else '0.00',
        }

    cart_json = json.dumps(cart)
    if len(cart_json.encode('utf-8')) > 4096:  # Ограничение 4 КБ
        messages.error(request, 'Корзина слишком большая. '
                                'Пожалуйста, удалите некоторые элементы.')
        return redirect('cart')

    response = redirect('book_list')
    response.set_cookie(cart_cookie_name, json.dumps(cart),
                        max_age=30 * 24 * 60 * 60)  # 30 дней
    messages.success(request, f'Книга "{book.title}" добавлена в корзину!')
    return response


def remove_from_cart(request, book_id):
    cart_cookie_name = get_cart_cookie_name(request)
    print(f"rfc {cart_cookie_name = }")
    cart = request.COOKIES.get(cart_cookie_name, '{}')
    try:
        cart = json.loads(cart)
    except json.JSONDecodeError:
        cart = {}

    book_id_str = str(book_id)
    if book_id_str in cart:
        book_title = cart[book_id_str]['title']
        del cart[book_id_str]
        messages.success(request, f'Книга "{book_title}" удалена из корзины!')
    else:
        messages.error(request, 'Книга не найдена в корзине.')

    response = redirect('cart')
    response.set_cookie(cart_cookie_name, json.dumps(cart),
                        max_age=30 * 24 * 60 * 60)
    return response


def cart_view(request):
    cart_cookie_name = get_cart_cookie_name(request)
    print(f"cv {cart_cookie_name = }")
    cart = request.COOKIES.get(cart_cookie_name, '{}')
    try:
        cart = json.loads(cart)
    except json.JSONDecodeError:
        cart = {}
    print(f"{cart = }")

    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        quantity = int(request.POST.get('quantity', 1))
        book_id_str = str(book_id)

        if book_id_str in cart:
            if quantity > 0:
                cart[book_id_str]['quantity'] = quantity
                messages.success(request,
                                 f'Количество для "{cart[book_id_str]["title"]}" обновлено!')
            else:
                book_title = cart[book_id_str]['title']
                del cart[book_id_str]
                messages.success(request,
                                 f'Книга "{book_title}" удалена из корзины!')
            response = redirect('cart')
            response.set_cookie('cart', json.dumps(cart),
                                max_age=30 * 24 * 60 * 60)
            return response

    cart_items = []
    total_cost = Decimal('0.00')

    for book_id, item in cart.items():
        item_cost = Decimal(item['cost']) * item['quantity']
        cart_items.append({
            'book_id': book_id,
            'title': item['title'],
            'quantity': item['quantity'],
            'cost': item['cost'],
            'total_item_cost': item_cost,
        })
        total_cost += item_cost

    return render(request, 'bookstore_app/cart.html', {
        'cart_items': cart_items,
        'total_cost': total_cost,
    })


def clear_cart(request):
    cart_cookie_name = get_cart_cookie_name(request)
    response = redirect('cart')
    response.delete_cookie(cart_cookie_name)
    messages.success(request, 'Корзина очищена!')
    return response


@login_required
def place_order(request):
    cart_cookie_name = get_cart_cookie_name(request)
    cart = request.COOKIES.get(cart_cookie_name, '{}')
    try:
        cart = json.loads(cart)
    except json.JSONDecodeError:
        cart = {}

    if not cart:
        messages.error(request, 'Ваша корзина пуста. Нельзя оформить заказ.')
        return redirect('cart')

    total_cost = Decimal('0.00')
    for book_id, item in cart.items():
        item_cost = Decimal(item['cost']) * item['quantity']
        total_cost += item_cost

    order = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'items': cart,
        'total_cost': str(total_cost),
    }

    orders_cookie_name = get_orders_cookie_name(request)
    orders = request.COOKIES.get(orders_cookie_name, '[]')
    try:
        orders = json.loads(orders)
    except json.JSONDecodeError:
        orders = []

    orders.append(order)

    orders_json = json.dumps(orders)
    if len(orders_json.encode('utf-8')) > 4096:
        messages.error(request, 'Слишком много заказов. '
                                'Пожалуйста, очистите историю заказов.')
        return redirect('cart')

    response = redirect('order_history')
    response.delete_cookie(cart_cookie_name)
    response.set_cookie(orders_cookie_name, orders_json,
                        max_age=365 * 24 * 60 * 60)  # Заказы хранятся 1 год
    messages.success(request, 'Заказ успешно оформлен!')
    return response


@login_required
def order_history(request):
    orders_cookie_name = get_orders_cookie_name(request)
    orders = request.COOKIES.get(orders_cookie_name, '[]')
    try:
        orders = json.loads(orders)
    except json.JSONDecodeError:
        orders = []

    for order in orders:
        order['total_cost'] = Decimal(order['total_cost'])
        for item in order['items'].values():
            item['cost'] = Decimal(item['cost'])

    return render(request, 'bookstore_app/order_history.html', {
        'orders': orders,
    })


@login_required
def clear_orders(request):
    orders_cookie_name = get_orders_cookie_name(request)
    response = redirect('order_history')
    response.delete_cookie(orders_cookie_name)
    messages.success(request, 'История заказов очищена!')
    return response
