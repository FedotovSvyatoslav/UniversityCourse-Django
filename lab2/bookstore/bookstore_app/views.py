import os

from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView

from .models import Book
from .forms import BookForm

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "../templates")
books_dir = os.path.join(templates_dir, "books")


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


def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'bookstore_app/book_form.html', {'form': form})


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


def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        return redirect('book_list')
    return render(request, 'bookstore_app/book_delete.html',
                  {'book': book})
