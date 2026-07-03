from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    edition = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ["title"]
        unique_together = ("title", "author", "edition")

    def __str__(self):
        return f"{self.title} ({self.edition}) by {self.author.name}"
