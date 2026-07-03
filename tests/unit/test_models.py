from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from inventory.models import Author, Book


class AuthorModelTests(TestCase):
    def test_str_representation(self):
        author = Author.objects.create(name="George Orwell")
        self.assertEqual(str(author), "George Orwell")

    def test_name_is_unique(self):
        Author.objects.create(name="Jane Austen")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Author.objects.create(name="Jane Austen")


class BookModelTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name="J.R.R. Tolkien")

    def test_str_representation(self):
        book = Book.objects.create(
            title="The Hobbit", author=self.author, price=Decimal("15.99"), edition="1st"
        )
        self.assertEqual(str(book), "The Hobbit (1st) by J.R.R. Tolkien")

    def test_edition_defaults_to_empty_string(self):
        book = Book.objects.create(title="The Hobbit", author=self.author, price=Decimal("15.99"))
        self.assertEqual(book.edition, "")

    def test_duplicate_title_author_edition_is_rejected_at_db_level(self):
        Book.objects.create(
            title="The Hobbit", author=self.author, price=Decimal("15.99"), edition="1st"
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Book.objects.create(
                    title="The Hobbit", author=self.author, price=Decimal("12.00"), edition="1st"
                )

    def test_same_title_different_edition_is_allowed(self):
        Book.objects.create(
            title="The Hobbit", author=self.author, price=Decimal("15.99"), edition="1st"
        )
        second = Book.objects.create(
            title="The Hobbit", author=self.author, price=Decimal("18.99"), edition="2nd"
        )
        self.assertEqual(Book.objects.filter(title="The Hobbit").count(), 2)
        self.assertEqual(second.edition, "2nd")
