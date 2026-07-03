<div align="center">

# 📚 Book Inventory System

### A JSON-only Django backend for the "Readers Haven" bookstore inventory

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)

</div>

---

## About

**Book Inventory System** is a university coursework project implementing a
JSON-only Django backend for a bookstore's book inventory. There is
**no admin interface and no HTML templates** — every feature is a plain
Django view returning JSON, reachable by a RESTful URL, so it can be
exercised directly with `curl`/Postman or the Django test client.

## Project structure

```
book-inventory-system/
├── src/
│   ├── manage.py
│   ├── bookstore/          # Django project config (settings, urls, wsgi, asgi)
│   └── inventory/          # the app: models, views, urls, migrations
├── tests/
│   ├── unit/                # view/model logic in isolation (RequestFactory)
│   ├── integration/         # full request/response cycle (Django test Client)
│   ├── TEST_RESULTS.md      # latest `manage.py test` output
│   └── BUGS.md              # bug/issue log
├── .gitignore
├── README.md
└── requirements.txt
```

## Setup

### Prerequisites
- Python 3.10+
- pip

### 1. Clone the repository
```bash
git clone https://github.com/kaiffarooqui970/book-inventory-system.git
cd book-inventory-system
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply migrations
```bash
cd src
python manage.py migrate
```

### 5. Run the development server
```bash
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/`.

## Running tests

From `src/` (or anywhere, since `manage.py` adds the repo root to
`sys.path` so the top-level `tests/` package is importable):

```bash
cd src
python manage.py test tests.unit tests.integration -v 2
```

Run just one suite:
```bash
python manage.py test tests.unit          # isolated view/model tests
python manage.py test tests.integration   # full request/response cycle
```

See `tests/TEST_RESULTS.md` for the latest recorded run and
`tests/BUGS.md` for the issue log.

---

## API Endpoints

All endpoints accept/return `application/json`. List endpoints return a
JSON array directly; write endpoints return an object describing what
happened. Errors are always `{"error": "..."}` (or a richer object for
partial-success bulk operations) with a non-2xx status code.

Book object shape:
```json
{
  "id": 1,
  "title": "1984",
  "author": "George Orwell",
  "author_id": 3,
  "price": "9.99",
  "edition": "1st"
}
```

### Authors

#### `GET /authors/` — list all authors
```bash
curl http://127.0.0.1:8000/authors/
```
```json
[{"id": 1, "name": "George Orwell"}]
```

#### `POST /authors/` — add author(s)
Accepts a single object or a list.
```bash
curl -X POST http://127.0.0.1:8000/authors/ \
  -H "Content-Type: application/json" \
  -d '{"name": "George Orwell"}'
```
```json
{"created": [{"id": 1, "name": "George Orwell"}], "duplicates_skipped": [], "errors": []}
```
Adding the same name again returns it in `duplicates_skipped` (status 200)
instead of creating a second row.

### Books — core CRUD

#### `GET /books/` — retrieve the entire inventory
```bash
curl http://127.0.0.1:8000/books/
```
```json
[{"id": 1, "title": "1984", "author": "George Orwell", "author_id": 1, "price": "9.99", "edition": "1st"}]
```

#### `POST /books/` — add book(s)
Accepts a single object or a list of objects (`title`, `author`, `price`
required; `edition` optional). Auto-creates the author if it doesn't exist
yet. Exact duplicates (same title + author + edition) are skipped, not
re-created.
```bash
curl -X POST http://127.0.0.1:8000/books/ \
  -H "Content-Type: application/json" \
  -d '{"title": "1984", "author": "George Orwell", "price": "9.99", "edition": "1st"}'
```
```json
{
  "created": [{"id": 1, "title": "1984", "author": "George Orwell", "author_id": 1, "price": "9.99", "edition": "1st"}],
  "duplicates_skipped": [],
  "errors": []
}
```

#### `GET /books/<id>/` — retrieve a single book
```bash
curl http://127.0.0.1:8000/books/1/
```
```json
{"id": 1, "title": "1984", "author": "George Orwell", "author_id": 1, "price": "9.99", "edition": "1st"}
```
Returns `404 {"error": "Book with id 1 not found"}` if it doesn't exist.

#### `PUT` / `PATCH /books/<id>/` — update a book
Send only the fields you want to change.
```bash
curl -X PATCH http://127.0.0.1:8000/books/1/ \
  -H "Content-Type: application/json" \
  -d '{"price": "11.50", "edition": "2nd"}'
```
```json
{"id": 1, "title": "1984", "author": "George Orwell", "author_id": 1, "price": "11.50", "edition": "2nd"}
```
Returns `409` if the update would collide with another existing book
(same title + author + edition).

#### `DELETE /books/<id>/` — delete a single book by id
```bash
curl -X DELETE http://127.0.0.1:8000/books/1/
```
```json
{"message": "Deleted book '1984' (id=1)"}
```

#### `DELETE /books/delete/?title=<title>` — delete by title
Deletes only when the title matches **exactly one** book. If multiple
books share that title, nothing is deleted and the response lists the
candidate ids so you can retry with `/books/<id>/` instead — this
prevents accidental multi-delete.
```bash
curl -X DELETE "http://127.0.0.1:8000/books/delete/?title=1984"
```
```json
{"message": "Deleted book '1984' (id=1)"}
```
Ambiguous match (409):
```json
{"error": "2 books match title 'Emma'; delete by id instead to avoid accidental multi-delete", "matching_ids": [4, 7]}
```

#### `GET /books/author/<name>/` — filter books by author name
```bash
curl "http://127.0.0.1:8000/books/author/George%20Orwell/"
```
```json
[{"id": 1, "title": "1984", "author": "George Orwell", "author_id": 1, "price": "9.99", "edition": "1st"}]
```

### Books — search & sort

#### `GET /books/search/?q=<text>` — search by partial/full title
```bash
curl "http://127.0.0.1:8000/books/search/?q=farm"
```
```json
[{"id": 2, "title": "Animal Farm", "author": "George Orwell", "author_id": 1, "price": "7.99", "edition": ""}]
```

#### `GET /books/sort/?by=price|title&order=asc|desc` — sort inventory
```bash
curl "http://127.0.0.1:8000/books/sort/?by=price&order=desc"
```
```json
[
  {"id": 1, "title": "1984", "author": "George Orwell", "author_id": 1, "price": "9.99", "edition": "1st"},
  {"id": 2, "title": "Animal Farm", "author": "George Orwell", "author_id": 1, "price": "7.99", "edition": ""}
]
```

### Books — bulk operations

#### `POST /books/bulk-add/` — add many books at once
Accepts a JSON list (or `{"books": [...]}`), uses `bulk_create` and
resolves/creates authors with only a couple of extra queries regardless of
batch size (no N+1). Duplicates already in the DB, or repeated within the
same batch, are skipped and reported rather than erroring the whole request.
```bash
curl -X POST http://127.0.0.1:8000/books/bulk-add/ \
  -H "Content-Type: application/json" \
  -d '[
        {"title": "Brave New World", "author": "Aldous Huxley", "price": "8.50"},
        {"title": "Fahrenheit 451", "author": "Ray Bradbury", "price": "7.25"}
      ]'
```
```json
{"created_count": 2, "duplicates_skipped": [], "errors": []}
```
Empty list returns `400 {"created_count": 0, "duplicates_skipped": [], "errors": []}`.

#### `POST /books/bulk-delete/` — delete many books at once
Accepts `{"ids": [...]}`, `{"titles": [...]}`, or both — resolved as a
single queryset `.delete()` (no per-row loop).
```bash
curl -X POST http://127.0.0.1:8000/books/bulk-delete/ \
  -H "Content-Type: application/json" \
  -d '{"titles": ["Brave New World", "Fahrenheit 451"]}'
```
```json
{"deleted_count": 2, "deleted_titles": ["Brave New World", "Fahrenheit 451"]}
```
Both lists empty/missing returns `400 {"error": "Provide a non-empty 'ids' or 'titles' list"}`.

---

## Design notes

- **No admin, no templates.** `django.contrib.admin` isn't installed and
  there's no `admin/` route — every feature is reachable only through the
  JSON API listed above.
- **Duplicate prevention.** `Book` has a DB-level `unique_together` on
  `(title, author, edition)`; add/update paths pre-empt the resulting
  `IntegrityError` and report it as a normal JSON response instead of a 500.
- **No accidental multi-delete.** Deleting by title is refused (409) unless
  exactly one book matches; deleting by id is always unambiguous.
- **Bulk-safe.** `bulk-add`/`bulk-delete` resolve authors and existing rows
  with a fixed, small number of queries and use `bulk_create` / a single
  queryset `.delete()`, so batch size doesn't turn into N+1 queries.
