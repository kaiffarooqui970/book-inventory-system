import json
from decimal import Decimal

from django.test import Client, TestCase, override_settings

from inventory.models import Author, Book


def _json(response):
    return json.loads(response.content)


class AuthorEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_add_single_author(self):
        response = self.client.post(
            "/authors/", data=json.dumps({"name": "Agatha Christie"}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Author.objects.count(), 1)

    def test_add_duplicate_author_is_not_duplicated(self):
        Author.objects.create(name="Agatha Christie")
        response = self.client.post(
            "/authors/", data=json.dumps({"name": "Agatha Christie"}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(_json(response)["duplicates_skipped"]), 1)
        self.assertEqual(Author.objects.count(), 1)

    def test_add_multiple_authors(self):
        payload = [{"name": "Author A"}, {"name": "Author B"}]
        response = self.client.post("/authors/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Author.objects.count(), 2)

    def test_list_authors(self):
        Author.objects.create(name="Author A")
        response = self.client.get("/authors/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(_json(response)), 1)


class BookCrudEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_add_book_creates_book_and_author(self):
        payload = {"title": "1984", "author": "George Orwell", "price": "9.99", "edition": "1st"}
        response = self.client.post("/books/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(Author.objects.count(), 1)

    def test_retrieve_entire_inventory(self):
        author = Author.objects.create(name="George Orwell")
        Book.objects.create(title="1984", author=author, price=Decimal("9.99"))
        Book.objects.create(title="Animal Farm", author=author, price=Decimal("7.99"))
        response = self.client.get("/books/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(_json(response)), 2)

    def test_filter_books_by_author_name(self):
        orwell = Author.objects.create(name="George Orwell")
        austen = Author.objects.create(name="Jane Austen")
        Book.objects.create(title="1984", author=orwell, price=Decimal("9.99"))
        Book.objects.create(title="Emma", author=austen, price=Decimal("6.99"))
        response = self.client.get("/books/author/George Orwell/")
        data = _json(response)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "1984")

    def test_filter_by_unknown_author_returns_empty_list(self):
        response = self.client.get("/books/author/Nobody/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response), [])

    def test_update_book_price_and_edition(self):
        author = Author.objects.create(name="George Orwell")
        book = Book.objects.create(title="1984", author=author, price=Decimal("9.99"), edition="1st")
        response = self.client.patch(
            f"/books/{book.id}/",
            data=json.dumps({"price": "11.50", "edition": "2nd"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        book.refresh_from_db()
        self.assertEqual(book.price, Decimal("11.50"))
        self.assertEqual(book.edition, "2nd")

    def test_update_missing_book_returns_404(self):
        response = self.client.patch(
            "/books/9999/", data=json.dumps({"price": "1.00"}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_book_by_id(self):
        author = Author.objects.create(name="George Orwell")
        book = Book.objects.create(title="1984", author=author, price=Decimal("9.99"))
        response = self.client.delete(f"/books/{book.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Book.objects.filter(id=book.id).exists())

    def test_delete_nonexistent_book_by_id_returns_404(self):
        response = self.client.delete("/books/9999/")
        self.assertEqual(response.status_code, 404)

    def test_delete_book_by_unique_title(self):
        author = Author.objects.create(name="George Orwell")
        Book.objects.create(title="1984", author=author, price=Decimal("9.99"))
        response = self.client.delete("/books/delete/?title=1984")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Book.objects.count(), 0)

    def test_delete_by_title_with_multiple_matches_is_rejected(self):
        orwell = Author.objects.create(name="George Orwell")
        other = Author.objects.create(name="Someone Else")
        Book.objects.create(title="Same Title", author=orwell, price=Decimal("9.99"), edition="1st")
        Book.objects.create(title="Same Title", author=other, price=Decimal("5.00"), edition="2nd")
        response = self.client.delete("/books/delete/?title=Same Title")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Book.objects.count(), 2)  # nothing deleted — no accidental multi-delete

    def test_delete_by_title_not_found(self):
        response = self.client.delete("/books/delete/?title=Nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_adding_exact_duplicate_book_is_rejected(self):
        author = Author.objects.create(name="George Orwell")
        Book.objects.create(title="1984", author=author, price=Decimal("9.99"), edition="1st")
        response = self.client.post(
            "/books/",
            data=json.dumps({"title": "1984", "author": "George Orwell", "price": "9.99", "edition": "1st"}),
            content_type="application/json",
        )
        data = _json(response)
        self.assertEqual(len(data["duplicates_skipped"]), 1)
        self.assertEqual(Book.objects.filter(title="1984").count(), 1)


class SearchSortEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()
        author = Author.objects.create(name="George Orwell")
        Book.objects.create(title="1984", author=author, price=Decimal("20.00"))
        Book.objects.create(title="Animal Farm", author=author, price=Decimal("8.00"))

    def test_search_partial_title_match(self):
        response = self.client.get("/books/search/?q=animal")
        data = _json(response)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Animal Farm")

    def test_search_with_no_matches_returns_empty_list_not_error(self):
        response = self.client.get("/books/search/?q=zzzznomatch")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response), [])

    def test_sort_by_price_ascending(self):
        response = self.client.get("/books/sort/?by=price&order=asc")
        titles = [b["title"] for b in _json(response)]
        self.assertEqual(titles, ["Animal Farm", "1984"])

    def test_sort_by_title_alphabetical(self):
        response = self.client.get("/books/sort/?by=title&order=asc")
        titles = [b["title"] for b in _json(response)]
        self.assertEqual(titles, ["1984", "Animal Farm"])


class BulkEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_bulk_add_multiple_books(self):
        payload = [
            {"title": "Book A", "author": "Author X", "price": "5.00"},
            {"title": "Book B", "author": "Author X", "price": "6.00"},
        ]
        response = self.client.post(
            "/books/bulk-add/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(_json(response)["created_count"], 2)
        self.assertEqual(Book.objects.count(), 2)

    def test_bulk_add_with_empty_list_returns_400(self):
        response = self.client.post(
            "/books/bulk-add/", data=json.dumps([]), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_bulk_add_skips_existing_duplicates(self):
        author = Author.objects.create(name="Author X")
        Book.objects.create(title="Book A", author=author, price=Decimal("5.00"))
        payload = [{"title": "Book A", "author": "Author X", "price": "5.00"}]
        response = self.client.post(
            "/books/bulk-add/", data=json.dumps(payload), content_type="application/json"
        )
        data = _json(response)
        self.assertEqual(data["created_count"], 0)
        self.assertEqual(len(data["duplicates_skipped"]), 1)

    def test_bulk_add_large_batch_succeeds(self):
        payload = [{"title": f"Book {i}", "author": "Author X", "price": "1.00"} for i in range(200)]
        response = self.client.post(
            "/books/bulk-add/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Book.objects.count(), 200)

    def test_bulk_delete_by_titles(self):
        author = Author.objects.create(name="Author X")
        Book.objects.create(title="Book A", author=author, price=Decimal("1.00"))
        Book.objects.create(title="Book B", author=author, price=Decimal("2.00"))
        response = self.client.post(
            "/books/bulk-delete/",
            data=json.dumps({"titles": ["Book A", "Book B"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["deleted_count"], 2)
        self.assertEqual(Book.objects.count(), 0)

    def test_bulk_delete_with_empty_lists_returns_400(self):
        response = self.client.post(
            "/books/bulk-delete/",
            data=json.dumps({"ids": [], "titles": []}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_bulk_delete_nonexistent_ids_returns_zero_deleted(self):
        response = self.client.post(
            "/books/bulk-delete/",
            data=json.dumps({"ids": [9999, 8888]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["deleted_count"], 0)


class NotFoundHandlerTests(TestCase):
    @override_settings(DEBUG=False)
    def test_unknown_url_returns_json_404(self):
        # handler404 only kicks in with DEBUG=False; with DEBUG=True Django
        # shows its own debug page instead, so this test forces DEBUG off.
        response = self.client.get("/this-route-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")
