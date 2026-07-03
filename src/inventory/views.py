import json
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Author, Book

SORT_FIELDS = {"price": "price", "title": "title"}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def require_json_methods(methods):
    """Like require_http_methods, but the 405 body is JSON instead of HTML."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.method not in methods:
                return JsonResponse(
                    {"error": f"Method {request.method} not allowed"}, status=405
                )
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def _parse_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
        return None


def _book_to_dict(book):
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author.name,
        "author_id": book.author_id,
        "price": str(book.price),
        "edition": book.edition,
    }


def _author_to_dict(author):
    return {"id": author.id, "name": author.name}


def _extract_book_fields(item):
    """Returns (title, author_name, price, edition) or raises ValueError."""
    try:
        title = str(item["title"]).strip()
        author_name = str(item["author"]).strip()
        price = Decimal(str(item["price"]))
        edition = str(item.get("edition", "")).strip()
    except (KeyError, InvalidOperation, AttributeError, TypeError) as exc:
        raise ValueError(f"Invalid book data: {exc}") from exc
    if not title:
        raise ValueError("title cannot be empty")
    if not author_name:
        raise ValueError("author cannot be empty")
    return title, author_name, price, edition


def not_found_404(request, exception=None):
    return JsonResponse({"error": "Not found"}, status=404)


# ---------------------------------------------------------------------------
# books: collection (/books/) — GET list, POST add (single object or list)
# ---------------------------------------------------------------------------

@csrf_exempt
@require_json_methods(["GET", "POST"])
def books_collection(request):
    if request.method == "GET":
        return _list_books(request)
    return _add_book(request)


def _list_books(request):
    books = Book.objects.select_related("author").all()
    return JsonResponse([_book_to_dict(b) for b in books], safe=False)


def _add_book(request):
    payload = _parse_body(request)
    if payload is None:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)
    items = payload if isinstance(payload, list) else [payload]
    if not items:
        return JsonResponse({"error": "No book data provided"}, status=400)

    created, duplicates, errors = [], [], []
    for idx, item in enumerate(items):
        try:
            title, author_name, price, edition = _extract_book_fields(item)
        except ValueError as exc:
            errors.append({"index": idx, "error": str(exc)})
            continue

        author, _ = Author.objects.get_or_create(name=author_name)
        try:
            with transaction.atomic():
                book = Book.objects.create(
                    title=title, author=author, price=price, edition=edition
                )
        except IntegrityError:
            duplicates.append({"index": idx, "title": title, "author": author_name})
            continue
        created.append(_book_to_dict(book))

    if created:
        status = 201
    elif errors:
        status = 400
    else:
        status = 200
    return JsonResponse(
        {"created": created, "duplicates_skipped": duplicates, "errors": errors},
        status=status,
    )


# ---------------------------------------------------------------------------
# books: detail (/books/<id>/) — GET retrieve, PUT/PATCH update, DELETE by id
# ---------------------------------------------------------------------------

@csrf_exempt
@require_json_methods(["GET", "PUT", "PATCH", "DELETE"])
def book_detail(request, book_id):
    try:
        book = Book.objects.select_related("author").get(id=book_id)
    except Book.DoesNotExist:
        return JsonResponse({"error": f"Book with id {book_id} not found"}, status=404)

    if request.method == "GET":
        return JsonResponse(_book_to_dict(book))
    if request.method == "DELETE":
        title = book.title
        book.delete()
        return JsonResponse({"message": f"Deleted book '{title}' (id={book_id})"})
    return _update_book(request, book)


def _update_book(request, book):
    payload = _parse_body(request)
    if payload is None or not isinstance(payload, dict):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    if "title" in payload:
        title = str(payload["title"]).strip()
        if not title:
            return JsonResponse({"error": "title cannot be empty"}, status=400)
        book.title = title
    if "edition" in payload:
        book.edition = str(payload["edition"]).strip()
    if "price" in payload:
        try:
            book.price = Decimal(str(payload["price"]))
        except InvalidOperation:
            return JsonResponse({"error": "Invalid price"}, status=400)
    if "author" in payload:
        author_name = str(payload["author"]).strip()
        if not author_name:
            return JsonResponse({"error": "author cannot be empty"}, status=400)
        author, _ = Author.objects.get_or_create(name=author_name)
        book.author = author

    try:
        with transaction.atomic():
            book.save()
    except IntegrityError:
        return JsonResponse(
            {"error": "Update would create a duplicate book entry"}, status=409
        )
    return JsonResponse(_book_to_dict(book))


# ---------------------------------------------------------------------------
# books: delete by title (/books/delete/?title=) — refuses ambiguous matches
# ---------------------------------------------------------------------------

@csrf_exempt
@require_json_methods(["DELETE"])
def delete_book_by_title(request):
    title = request.GET.get("title", "").strip()
    if not title:
        return JsonResponse({"error": "Query parameter 'title' is required"}, status=400)

    matches = Book.objects.filter(title__iexact=title)
    count = matches.count()
    if count == 0:
        return JsonResponse({"error": f"No book found with title '{title}'"}, status=404)
    if count > 1:
        return JsonResponse(
            {
                "error": (
                    f"{count} books match title '{title}'; delete by id instead "
                    "to avoid accidental multi-delete"
                ),
                "matching_ids": list(matches.values_list("id", flat=True)),
            },
            status=409,
        )

    book = matches.first()
    book_id = book.id
    book.delete()
    return JsonResponse({"message": f"Deleted book '{title}' (id={book_id})"})


# ---------------------------------------------------------------------------
# books: search / sort / filter by author
# ---------------------------------------------------------------------------

@require_json_methods(["GET"])
def search_books(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"error": "Query parameter 'q' is required"}, status=400)
    books = Book.objects.select_related("author").filter(title__icontains=query)
    return JsonResponse([_book_to_dict(b) for b in books], safe=False)


@require_json_methods(["GET"])
def sort_books(request):
    by = request.GET.get("by", "title")
    order = request.GET.get("order", "asc")
    if by not in SORT_FIELDS:
        return JsonResponse(
            {"error": f"Cannot sort by '{by}'. Use 'price' or 'title'."}, status=400
        )
    if order not in ("asc", "desc"):
        return JsonResponse({"error": "order must be 'asc' or 'desc'"}, status=400)

    field = SORT_FIELDS[by]
    if order == "desc":
        field = f"-{field}"
    books = Book.objects.select_related("author").order_by(field)
    return JsonResponse([_book_to_dict(b) for b in books], safe=False)


@require_json_methods(["GET"])
def books_by_author(request, author_name):
    books = Book.objects.select_related("author").filter(author__name__iexact=author_name)
    return JsonResponse([_book_to_dict(b) for b in books], safe=False)


# ---------------------------------------------------------------------------
# books: bulk add / bulk delete
# ---------------------------------------------------------------------------

@csrf_exempt
@require_json_methods(["POST"])
def bulk_add_books(request):
    payload = _parse_body(request)
    if payload is None:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)
    items = payload.get("books") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return JsonResponse(
            {"error": "Expected a list of books (or {'books': [...]})"}, status=400
        )
    if not items:
        return JsonResponse(
            {"created_count": 0, "duplicates_skipped": [], "errors": []}, status=400
        )

    valid_rows = []
    errors = []
    seen_in_batch = set()
    for idx, item in enumerate(items):
        try:
            title, author_name, price, edition = _extract_book_fields(item)
        except ValueError as exc:
            errors.append({"index": idx, "error": str(exc)})
            continue

        key = (title.lower(), author_name.lower(), edition.lower())
        if key in seen_in_batch:
            errors.append({"index": idx, "error": "Duplicate within submitted batch"})
            continue
        seen_in_batch.add(key)
        valid_rows.append((title, author_name, price, edition))

    if not valid_rows:
        return JsonResponse(
            {"created_count": 0, "duplicates_skipped": [], "errors": errors}, status=400
        )

    # Resolve/create authors in bulk (2 queries total, not one per row).
    author_names = {row[1] for row in valid_rows}
    existing_authors = Author.objects.filter(name__in=author_names)
    existing_author_names = {a.name for a in existing_authors}
    new_author_names = author_names - existing_author_names
    if new_author_names:
        Author.objects.bulk_create(
            [Author(name=n) for n in new_author_names], ignore_conflicts=True
        )
    authors_by_name = {a.name: a for a in Author.objects.filter(name__in=author_names)}

    # Single query to find pre-existing books that would collide with the batch.
    existing_books = set(
        Book.objects.filter(title__in=[r[0] for r in valid_rows]).values_list(
            "title", "author__name", "edition"
        )
    )

    to_create = []
    duplicates = []
    for title, author_name, price, edition in valid_rows:
        if (title, author_name, edition) in existing_books:
            duplicates.append({"title": title, "author": author_name, "edition": edition})
            continue
        to_create.append(
            Book(title=title, author=authors_by_name[author_name], price=price, edition=edition)
        )

    try:
        created_books = Book.objects.bulk_create(to_create)
    except IntegrityError:
        return JsonResponse(
            {"error": "Bulk insert failed due to duplicate entries"}, status=409
        )

    status = 201 if created_books else 200
    return JsonResponse(
        {
            "created_count": len(created_books),
            "duplicates_skipped": duplicates,
            "errors": errors,
        },
        status=status,
    )


@csrf_exempt
@require_json_methods(["POST"])
def bulk_delete_books(request):
    payload = _parse_body(request)
    if payload is None or not isinstance(payload, dict):
        return JsonResponse(
            {"error": "Expected a JSON object with 'ids' and/or 'titles'"}, status=400
        )

    ids = payload.get("ids") or []
    titles = payload.get("titles") or []
    if not isinstance(ids, list) or not isinstance(titles, list):
        return JsonResponse({"error": "'ids' and 'titles' must be lists"}, status=400)
    if not ids and not titles:
        return JsonResponse({"error": "Provide a non-empty 'ids' or 'titles' list"}, status=400)

    qs = Book.objects.none()
    if ids:
        qs = qs | Book.objects.filter(id__in=ids)
    if titles:
        qs = qs | Book.objects.filter(title__in=titles)

    deleted_titles = list(qs.values_list("title", flat=True))
    deleted_count, _ = qs.delete()
    return JsonResponse({"deleted_count": deleted_count, "deleted_titles": deleted_titles})


# ---------------------------------------------------------------------------
# authors
# ---------------------------------------------------------------------------

@csrf_exempt
@require_json_methods(["GET", "POST"])
def authors_collection(request):
    if request.method == "GET":
        authors = Author.objects.all()
        return JsonResponse([_author_to_dict(a) for a in authors], safe=False)
    return _add_author(request)


def _add_author(request):
    payload = _parse_body(request)
    if payload is None:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)
    items = payload if isinstance(payload, list) else [payload]
    if not items:
        return JsonResponse({"error": "No author data provided"}, status=400)

    created, duplicates, errors = [], [], []
    for idx, item in enumerate(items):
        try:
            name = str(item["name"]).strip()
        except (KeyError, AttributeError, TypeError) as exc:
            errors.append({"index": idx, "error": f"Invalid author data: {exc}"})
            continue
        if not name:
            errors.append({"index": idx, "error": "name cannot be empty"})
            continue

        author, was_created = Author.objects.get_or_create(name=name)
        if was_created:
            created.append(_author_to_dict(author))
        else:
            duplicates.append(_author_to_dict(author))

    if created:
        status = 201
    elif errors:
        status = 400
    else:
        status = 200
    return JsonResponse(
        {"created": created, "duplicates_skipped": duplicates, "errors": errors},
        status=status,
    )
