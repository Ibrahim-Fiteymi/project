"""End-to-end tests for /api/analyze: validation, persistence, and edge cases."""

import io


def test_analyze_success(client, upload_png):
    name, payload, ctype = upload_png
    res = client.post("/api/analyze", files={"file": (name, payload, ctype)})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"].startswith("ok")
    assert body["cell_count"] >= 0
    assert body["job_id"]
    assert body["overlay_url"].startswith("/files/")
    assert body["mask_url"].startswith("/files/")
    assert body["metadata"]["min_area"] >= 1


def test_analyze_persists_to_history(client, upload_png):
    name, payload, ctype = upload_png
    res = client.post("/api/analyze", files={"file": (name, payload, ctype)})
    job_id = res.json()["job_id"]

    history = client.get("/api/analyses").json()
    assert history["total"] >= 1
    assert any(item["job_id"] == job_id for item in history["items"])


def test_analyze_get_single(client, upload_png):
    name, payload, ctype = upload_png
    res = client.post("/api/analyze", files={"file": (name, payload, ctype)})
    job_id = res.json()["job_id"]

    item = client.get(f"/api/analyses/{job_id}").json()
    assert item["job_id"] == job_id
    assert item["status"] == "completed"


def test_analyze_delete(client, upload_png):
    name, payload, ctype = upload_png
    job_id = client.post("/api/analyze", files={"file": (name, payload, ctype)}).json()["job_id"]

    res = client.delete(f"/api/analyses/{job_id}")
    assert res.status_code == 200

    res2 = client.get(f"/api/analyses/{job_id}")
    assert res2.status_code == 404


def test_analyze_rejects_empty_upload(client):
    res = client.post("/api/analyze", files={"file": ("empty.png", b"", "image/png")})
    assert res.status_code == 400


def test_analyze_rejects_text_file(client):
    res = client.post(
        "/api/analyze",
        files={"file": ("hello.txt", b"plain text", "text/plain")},
    )
    assert res.status_code == 415


def test_analyze_rejects_bad_extension(client):
    res = client.post(
        "/api/analyze",
        files={"file": ("malicious.exe", b"\x00\x01\x02", "image/png")},
    )
    assert res.status_code == 415


def test_analyze_rejects_oversize(client):
    # Build a payload exactly 1 byte over the limit.
    from backend.config import settings

    huge = b"\x89PNG" + b"\x00" * (settings.max_upload_bytes + 1)
    res = client.post("/api/analyze", files={"file": ("huge.png", huge, "image/png")})
    assert res.status_code == 413


def test_analyze_rejects_undecodable_image(client):
    payload = b"\x89PNG\r\n\x1a\nnot-a-real-png"
    res = client.post("/api/analyze", files={"file": ("bad.png", payload, "image/png")})
    assert res.status_code == 400


def test_history_pagination_validation(client):
    assert client.get("/api/analyses?limit=0").status_code == 400
    assert client.get("/api/analyses?limit=99999").status_code == 400
    assert client.get("/api/analyses?offset=-1").status_code == 400


def test_get_nonexistent_analysis(client):
    res = client.get("/api/analyses/does-not-exist")
    assert res.status_code == 404


def test_delete_nonexistent_analysis(client):
    res = client.delete("/api/analyses/does-not-exist")
    assert res.status_code == 404


def test_file_path_traversal_blocked(client):
    res = client.get("/files/..%2Fsecrets.txt")
    # FastAPI URL-decodes path params; either way ".." is rejected.
    assert res.status_code in {400, 404}


def test_file_not_found(client):
    res = client.get("/files/zzz_nonexistent.png")
    assert res.status_code == 404


def test_file_etag_round_trip(client, upload_png):
    name, payload, ctype = upload_png
    job = client.post("/api/analyze", files={"file": (name, payload, ctype)}).json()
    overlay = job["overlay_url"]
    first = client.get(overlay)
    assert first.status_code == 200
    etag = first.headers.get("etag")
    assert etag

    second = client.get(overlay, headers={"If-None-Match": etag})
    assert second.status_code == 304


def test_concurrent_uploads_each_get_unique_id(client, upload_png):
    name, payload, ctype = upload_png
    ids = set()
    for _ in range(5):
        res = client.post("/api/analyze", files={"file": (name, payload, ctype)})
        assert res.status_code == 200
        ids.add(res.json()["job_id"])
    assert len(ids) == 5
