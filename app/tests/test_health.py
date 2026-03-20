from fastapi.testclient import TestClient

from app.bootstrap.app import create_app


async def _fake_startup_diagnostics(app, **_: object) -> dict:
    app.state.startup_diagnostics = {
        "status": "ok",
        "database": {"connected": True},
        "redis": {"connected": True},
        "tables": {"count": 31},
        "routes": {"count": 84},
    }
    return app.state.startup_diagnostics


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setattr("app.bootstrap.lifespan.run_startup_diagnostics", _fake_startup_diagnostics)
    return TestClient(create_app())


def test_healthz(monkeypatch) -> None:
    with _build_client(monkeypatch) as client:
        response = client.get('/healthz')
    assert response.status_code == 200
    assert response.json()['code'] == 0


def test_readyz(monkeypatch) -> None:
    with _build_client(monkeypatch) as client:
        response = client.get('/readyz')
    assert response.status_code == 200
    assert response.json()['code'] == 0
    assert response.json()['data'] == {
        "status": "ok",
        "database": {"connected": True},
        "redis": {"connected": True},
        "tables": {"count": 31},
        "routes": {"count": 84},
    }
