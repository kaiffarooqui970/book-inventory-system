# Bug / Issue Log

Format: date, description, root cause, fix applied, status.

---

### BUG-001 — Custom JSON 404 handler silently ignored in dev mode

- **Date:** 2026-07-03
- **Description:** While writing the integration test for the unmapped-URL
  case, a request to a nonexistent route returned Django's default HTML
  "technical 404" debug page instead of the project's JSON `handler404`
  (`inventory.views.not_found_404`).
- **Root cause:** Django only invokes a custom `handler404` when
  `DEBUG = False`. This project runs with `DEBUG = True` for local
  development, so Django's built-in debug page takes over instead.
- **Fix applied:** The affected test
  (`tests/integration/test_api.py::NotFoundHandlerTests`) wraps its request
  in `@override_settings(DEBUG=False)` so it exercises the real production
  behavior. No application code changes were needed — this is expected
  Django behavior, documented here so it isn't mistaken for a broken handler
  later. In an actual deployment, `DEBUG` must be `False`, at which point
  `handler404` fires normally and every response (including 404s) stays JSON.
- **Status:** Closed.

---

No other defects surfaced during implementation — the full suite (55 tests)
passed on its first run (see `TEST_RESULTS.md`). This log will be appended
to as new issues are found in future work on this project.
