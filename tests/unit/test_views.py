import json
from decimal import Decimal

from django.db import connection
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext

from inventory import views
from inventory.models import Author, Book


def _json(response):
    return json.loads(response.content)


class BooksCollectionViewTests(TestCase):
    """Calls view functions directly (no URL routing) to isolate each view."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_returns_empty_list_when_no_books(self):
        request = self.factory.get("/books/")
        response = views.books_collection(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response), [])

    def test_post_creates_single_book_and_auto_creates_author(self):
        body = {"title": "Dune", "author": "Frank Herbert", "price": "12.50", "edition": "1st"}
        request = self.factory.post(
            "/books/", data=json.dumps(body), content_type="application/json"
        )
        response = views.books_collection(request)
        self.assertEqual(response.status_code, 201)
        data = _json(response)
        self.assertEqual(len(data["created"]), 1)
        self.assertEqual(data["created"][0]["title"], "Dune")
        self.assertEqual(Author.objects.filter(name="Frank Herbert").count(), 1)

    def test_post_list_creates_multiple_books(self):
        body = [
            {"title": "Dune", "author": "Frank Herbert", "price": "12.50"},
            {"title": "Dune Messiah", "author": "Frank Herbert", "price": "11.00"},
        ]
        request = self.factory.post(
            "/books/", data=json.dumps(body), content_type="application/json"
        )
        response = views.books_collection(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(_json(response)["created"]), 2)

    def test_post_missing_field_reports_error_without_crashing(self):
        body = {"title": "Dune", "price": "12.50"}  # missing author
        request = self.factory.post(
            "/books/", data=json.dumps(body), content_type="application/json"
        )
        response = views.books_collection(request)
        self.assertEqual(response.status_code, 400)
        data = _json(response)
        self.assertEqual(len(data["errors"]), 1)
        self.assertEqual(len(data["created"]), 0)

    def test_post_duplicate_book_is_skipped_not_duplicated(self):
        author = Author.objects.create(name="Frank Herbert")
        Book.objects.create(title="Dune", author=author, price=Decimal("12.50"), edition="1st")
        body = {"title": "Dune", "author": "Frank Herbert", "price": "12.50", "edition": "1st"}
        request = self.factory.post(
            "/books/", data=json.dumps(body), content_type="application/json"
        )
        response = views.books_collection(request)
        data = _json(response)
        self.assertEqual(len(data["duplicates_skipped"]), 1)
        self.assertEqual(Book.objects.filter(title="Dune").count(), 1)

    def test_invalid_json_body_returns_400(self):
        request = self.factory.post("/books/", data="not json", content_type="application/json")
        response = views.books_collection(request)
        self.assertEqual(response.status_code, 400)

    def test_disallowed_method_returns_json_405(self):
        request = self.factory.delete("/books/")
        response = views.books_collection(request)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(_json(response)["error"], "Method DELETE not allowed")


class BookDetailViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.author = Author.objects.create(name="Frank Herbert")
        self.book = Book.objects.create(
            title="Dune", author=self.author, price=Decimal("12.50"), edition="1st"
        )

    def test_get_existing_book(self):
        request = self.factory.get(f"/books/{self.book.id}/")
        response = views.book_detail(request, self.book.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["title"], "Dune")

    def test_get_missing_book_returns_404(self):
        request = self.factory.get("/books/9999/")
        response = views.book_detail(request, 9999)
        self.assertEqual(response.status_code, 404)

    def test_patch_updates_price(self):
        body = {"price": "9.99"}
        request = self.factory.patch(
            f"/books/{self.book.id}/", data=json.dumps(body), content_type="application/json"
        )
        response = views.book_detail(request, self.book.id)
        self.assertEqual(response.status_code, 200)
        self.book.refresh_from_db()
        self.assertEqual(self.book.price, Decimal("9.99"))

    def test_delete_removes_book(self):
        request = self.factory.delete(f"/books/{self.book.id}/")
        response = views.book_detail(request, self.book.id)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Book.objects.filter(id=self.book.id).exists())


class SearchSortFilterViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        author = Author.objects.create(name="Frank Herbert")
        Book.objects.create(title="Dune", author=author, price=Decimal("20.00"))
        Book.objects.create(title="Dune Messiah", author=author, price=Decimal("10.00"))

    def test_search_requires_query_param(self):
        request = self.factory.get("/books/search/")
        response = views.search_books(request)
        self.assertEqual(response.status_code, 400)

    def test_search_partial_match(self):
        request = self.factory.get("/books/search/?q=mess")
        response = views.search_books(request)
        self.assertEqual(len(_json(response)), 1)

    def test_search_no_matches_returns_empty_list(self):
        request = self.factory.get("/books/search/?q=nonexistent")
        response = views.search_books(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response), [])

    def test_sort_by_price_desc(self):
        request = self.factory.get("/books/sort/?by=price&order=desc")
        response = views.sort_books(request)
        titles = [b["title"] for b in _json(response)]
        self.assertEqual(titles, ["Dune", "Dune Messiah"])

    def test_sort_invalid_field_returns_400(self):
        request = self.factory.get("/books/sort/?by=nonsense")
        response = views.sort_books(request)
        self.assertEqual(response.status_code, 400)

    def test_filter_by_author(self):
        request = self.factory.get("/books/author/Frank Herbert/")
        response = views.books_by_author(request, "Frank Herbert")
        self.assertEqual(len(_json(response)), 2)


class BulkOperationsViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_bulk_add_empty_list_returns_400(self):
        request = self.factory.post(
            "/books/bulk-add/", data=json.dumps([]), content_type="application/json"
        )
        response = views.bulk_add_books(request)
        self.assertEqual(response.status_code, 400)

    def test_bulk_add_creates_many_books_efficiently(self):
        books = [
            {"title": f"Book {i}", "author": "Author X", "price": "5.00"} for i in range(50)
        ]
        request = self.factory.post(
            "/books/bulk-add/", data=json.dumps(books), content_type="application/json"
        )
        with CaptureQueriesContext(connection) as ctx:
            response = views.bulk_add_books(request)
        # A handful of fixed queries regardless of batch size proves there's
        # no per-row (N+1) querying for 50 books.
        self.assertLess(len(ctx.captured_queries), 10)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(_json(response)["created_count"], 50)

    def test_bulk_delete_empty_body_returns_400(self):
        request = self.factory.post(
            "/books/bulk-delete/", data=json.dumps({}), content_type="application/json"
        )
        response = views.bulk_delete_books(request)
        self.assertEqual(response.status_code, 400)

    def test_bulk_delete_by_ids(self):
        author = Author.objects.create(name="Author X")
        b1 = Book.objects.create(title="A", author=author, price=Decimal("1.00"))
        b2 = Book.objects.create(title="B", author=author, price=Decimal("2.00"))
        request = self.factory.post(
            "/books/bulk-delete/",
            data=json.dumps({"ids": [b1.id, b2.id]}),
            content_type="application/json",
        )
        response = views.bulk_delete_books(request)
        self.assertEqual(_json(response)["deleted_count"], 2)
        self.assertEqual(Book.objects.count(), 0)
