# Test Results

**Last run:** 2026-07-03 19:39 UTC
**Command:** `python manage.py test tests.unit tests.integration -v 2`
**Environment:** Python 3.14.0, Django 6.0.1, SQLite (in-memory test DB)

## Summary

```
Ran 55 tests in 0.030s

OK
```

55/55 tests passed. 0 failures, 0 errors.

| Suite | File | Tests | Result |
|---|---|---|---|
| Unit — models | `tests/unit/test_models.py` | 6 | ✅ pass |
| Unit — views | `tests/unit/test_views.py` | 20 | ✅ pass |
| Integration — authors | `tests/integration/test_api.py::AuthorEndpointTests` | 4 | ✅ pass |
| Integration — book CRUD | `tests/integration/test_api.py::BookCrudEndpointTests` | 11 | ✅ pass |
| Integration — search/sort | `tests/integration/test_api.py::SearchSortEndpointTests` | 4 | ✅ pass |
| Integration — bulk ops | `tests/integration/test_api.py::BulkEndpointTests` | 9 | ✅ pass |
| Integration — 404 handler | `tests/integration/test_api.py::NotFoundHandlerTests` | 1 | ✅ pass |

## What's covered

**Unit tests** call view functions directly with `RequestFactory` (no URL
routing, no middleware), isolating each view's logic:
- Empty inventory, single add, list add, missing-field error, duplicate skip
- Retrieve/update/delete a single book by id, 404 on missing id
- Search with/without query param, no-match case
- Sort by price/title, invalid sort field
- Filter by author
- Bulk add (including an efficiency check that the query count for a 50-book
  batch stays under 10 — proving there's no per-row/N+1 querying), bulk add
  with an empty list, bulk delete by id, bulk delete with an empty body

**Integration tests** use Django's `Client` to hit real URLs end-to-end and
check status codes + JSON bodies:
- Add/list authors, duplicate author is not re-created
- Add book (auto-creates author), retrieve full inventory, filter by author
  (including unknown author → empty list, not an error)
- Update book fields, update on a missing id → 404
- Delete by id (success + 404 on missing id)
- Delete by title: unique match succeeds; **multiple matches are rejected
  with 409 and nothing is deleted** (prevents accidental multi-delete); no
  match → 404
- Adding an exact duplicate (title+author+edition) is skipped, not duplicated
- Bulk add: multiple books, empty list → 400, duplicates skipped, a 200-book
  batch to confirm it doesn't choke on larger input
- Bulk delete: by titles, empty `ids`/`titles` → 400, non-existent ids → 0
  deleted (no error)
- Unmapped URL returns a JSON 404 (not Django's default HTML page)

## How to re-run

```bash
cd src
python manage.py test tests.unit tests.integration -v 2
```

(`manage.py` adds the repo root to `sys.path` so the top-level `tests`
package — living outside `src/` — is importable; see `src/manage.py`.)
