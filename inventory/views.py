from django.http import JsonResponse
from .models import Book
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
def add_book(request):
    if request.method == "POST":
        data = json.loads(request.body)
        Book.objects.create(
            title=data["title"],
            author=data["author"],
            price=data["price"]
        )
        return JsonResponse({"message": "Book added successfully"})


def list_books(request):
    books = Book.objects.all()
    data = [
        {
            "title": book.title,
            "author": book.author,
            "price": str(book.price)
        }
        for book in books
    ]
    return JsonResponse(data, safe=False)


def books_by_author(request, author):
    books = Book.objects.filter(author__iexact=author)
    data = [
        {
            "title": book.title,
            "price": str(book.price)
        }
        for book in books
    ]
    return JsonResponse(data, safe=False)
