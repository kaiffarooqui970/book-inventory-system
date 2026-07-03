from django.urls import path

from . import views

urlpatterns = [
    path("books/", views.books_collection, name="books-collection"),
    path("books/<int:book_id>/", views.book_detail, name="book-detail"),
    path("books/search/", views.search_books, name="books-search"),
    path("books/sort/", views.sort_books, name="books-sort"),
    path("books/author/<str:author_name>/", views.books_by_author, name="books-by-author"),
    path("books/delete/", views.delete_book_by_title, name="book-delete-by-title"),
    path("books/bulk-add/", views.bulk_add_books, name="books-bulk-add"),
    path("books/bulk-delete/", views.bulk_delete_books, name="books-bulk-delete"),
    path("authors/", views.authors_collection, name="authors-collection"),
]
