"""Rate-limiter behaviour."""

from backend.rate_limit import IPRateLimiter
from backend import main


def test_rate_limit_triggers(client, upload_png, monkeypatch):
    """Replace the limiter with a tight one and confirm 429 is emitted."""
    name, payload, ctype = upload_png
    monkeypatch.setattr(main, "upload_limiter", IPRateLimiter(max_calls=2, window_seconds=60))

    statuses = []
    for _ in range(5):
        statuses.append(
            client.post("/api/analyze", files={"file": (name, payload, ctype)}).status_code
        )
    assert 429 in statuses, f"Expected a 429 in {statuses}"
    assert statuses.count(200) == 2, f"Expected exactly 2 success codes in {statuses}"


def test_rate_limit_reset_clears_bucket():
    limiter = IPRateLimiter(max_calls=1, window_seconds=60)

    class _R:
        client = type("c", (), {"host": "1.2.3.4"})()

    limiter.check(_R())
    limiter.reset()
    # After reset the same caller is allowed again.
    limiter.check(_R())
