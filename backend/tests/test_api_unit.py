from fastapi.testclient import TestClient
import app.main as main

class FakeSession:
    def run(self, cypher, **params):
        class Result:
            def data(self):
                return [{"playerID": "judgeaa01", "name": "Aaron Judge"}]
            def single(self):
                return None
        return Result()
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): pass

class FakeDriver:
    def session(self):
        return FakeSession()

def test_player_search_returns_results(monkeypatch):
    monkeypatch.setattr(main, "get_driver", lambda: FakeDriver())
    client = TestClient(main.app)

    r = client.get("/player/search", params={"q": "judge"})
    assert r.status_code == 200
    assert r.json()["results"][0]["name"] == "Aaron Judge"
