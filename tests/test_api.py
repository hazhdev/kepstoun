def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "version" in r.json()


def test_create_and_list(client):
    r = client.post("/messages", json={"author": "Аня", "text": "Привет!"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["author"] == "Аня"

    r = client.get("/messages")
    assert r.status_code == 200
    assert [m["text"] for m in r.json()] == ["Привет!"]


def test_validation(client):
    r = client.post("/messages", json={"author": "", "text": "x"})
    assert r.status_code == 422
