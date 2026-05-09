"""Health-endpoint smoke tests."""


def test_health_ok(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["mode"] in {"model", "fallback-demo", "uninitialised"}
    assert "device" in body


def test_health_includes_request_id(client):
    res = client.get("/api/health")
    assert "x-request-id" in {k.lower() for k in res.headers.keys()}
