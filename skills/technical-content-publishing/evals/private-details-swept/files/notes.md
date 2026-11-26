# Notes: retry helper

We built a small retry helper for flaky HTTP calls at Example Corp. Sam Example reviewed it
(ticket PROJ-1234). It runs against build-cache.internal.example.test and cut retries
from three per request to one in our test suite. Code: src/retry.py (about 80 lines),
tests in tests/test_retry.py. Never mention: Example Corp, Sam Example.
