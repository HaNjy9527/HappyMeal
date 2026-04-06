from urllib.parse import parse_qs, urlparse

import httpx

from app.core.config import get_settings
from app.db.models import User
from app.services import auth as auth_service


class MockResponse:
    def __init__(self, status_code: int, payload: dict[str, str]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, str]:
        return self._payload


def test_get_line_login_redirects_to_line_authorize_url(raw_client, monkeypatch):
    monkeypatch.setenv("LINE_CHANNEL_ID", "channel-123")
    monkeypatch.setenv("LINE_CALLBACK_URL", "https://api.example.com/auth/line/callback")
    get_settings.cache_clear()

    response = raw_client.get("/auth/line/login", follow_redirects=False)

    assert response.status_code == 302
    redirect_url = response.headers["location"]
    parsed = urlparse(redirect_url)
    query = parse_qs(parsed.query)

    assert parsed.netloc == "access.line.me"
    assert parsed.path == "/oauth2/v2.1/authorize"
    assert query["client_id"] == ["channel-123"]
    assert query["redirect_uri"] == ["https://api.example.com/auth/line/callback"]
    assert query["scope"] == ["profile openid"]
    assert query["state"]

    get_settings.cache_clear()


def test_get_line_callback_rejects_invalid_state(raw_client, monkeypatch):
    monkeypatch.setenv("LINE_CHANNEL_ID", "channel-123")
    monkeypatch.setenv("LINE_CALLBACK_URL", "https://api.example.com/auth/line/callback")
    get_settings.cache_clear()

    raw_client.get("/auth/line/login", follow_redirects=False)
    response = raw_client.get("/auth/line/callback?code=test-code&state=wrong-state", follow_redirects=False)

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid state parameter"

    get_settings.cache_clear()


def test_auth_flow_creates_session_and_logout_clears_it(raw_client, monkeypatch, db_session):
    monkeypatch.setenv("LINE_CHANNEL_ID", "channel-123")
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "secret-456")
    monkeypatch.setenv("LINE_CALLBACK_URL", "https://api.example.com/auth/line/callback")
    monkeypatch.setenv("FRONTEND_URL", "https://app.example.com")
    get_settings.cache_clear()

    def fake_post(*args, **kwargs):
        return MockResponse(200, {"access_token": "access-token-123"})

    def fake_get(*args, **kwargs):
        return MockResponse(
            200,
            {
                "userId": "line-user-001",
                "displayName": "LINE Tester",
                "pictureUrl": "https://cdn.example.com/avatar.jpg",
            },
        )

    monkeypatch.setattr("app.services.auth.httpx.post", fake_post)
    monkeypatch.setattr("app.services.auth.httpx.get", fake_get)

    login_response = raw_client.get("/auth/line/login", follow_redirects=False)
    state = parse_qs(urlparse(login_response.headers["location"]).query)["state"][0]

    callback_response = raw_client.get(
        f"/auth/line/callback?code=test-code&state={state}",
        follow_redirects=False,
    )

    # Callback now redirects to /?token=... instead of /home
    assert callback_response.status_code == 302
    redirect_location = callback_response.headers["location"]
    parsed_redirect = urlparse(redirect_location)
    redirect_params = parse_qs(parsed_redirect.query)
    assert parsed_redirect.path == "/"
    assert "token" in redirect_params
    auth_token = redirect_params["token"][0]

    # User is created in DB
    user = db_session.query(User).filter(User.line_user_id == "line-user-001").one_or_none()
    assert user is not None
    assert user.display_name == "LINE Tester"

    # Session is NOT set yet — /auth/me should return 401 before token exchange
    me_before_exchange = raw_client.get("/auth/me")
    assert me_before_exchange.status_code == 401

    # Exchange the token to establish session in the browser's context
    exchange_response = raw_client.post("/auth/exchange-token", json={"token": auth_token})
    assert exchange_response.status_code == 200
    assert exchange_response.json()["display_name"] == "LINE Tester"

    # Now /auth/me should return 200
    me_response = raw_client.get("/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["display_name"] == "LINE Tester"

    # Logout clears the session
    logout_response = raw_client.post("/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out"

    me_after_logout = raw_client.get("/auth/me")
    assert me_after_logout.status_code == 401
    assert me_after_logout.json()["detail"] == "Not authenticated"

    get_settings.cache_clear()


def test_get_line_callback_updates_existing_user(raw_client, monkeypatch, db_session):
    existing_user = User(
        line_user_id="line-user-001",
        display_name="Old Name",
        avatar_url="https://cdn.example.com/old-avatar.jpg",
    )
    db_session.add(existing_user)
    db_session.commit()

    monkeypatch.setenv("LINE_CHANNEL_ID", "channel-123")
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "secret-456")
    monkeypatch.setenv("LINE_CALLBACK_URL", "https://api.example.com/auth/line/callback")
    monkeypatch.setenv("FRONTEND_URL", "https://app.example.com")
    get_settings.cache_clear()

    def fake_post(*args, **kwargs):
        return MockResponse(200, {"access_token": "access-token-123"})

    def fake_get(*args, **kwargs):
        return MockResponse(
            200,
            {
                "userId": "line-user-001",
                "displayName": "Updated Name",
                "pictureUrl": "https://cdn.example.com/new-avatar.jpg",
            },
        )

    monkeypatch.setattr("app.services.auth.httpx.post", fake_post)
    monkeypatch.setattr("app.services.auth.httpx.get", fake_get)

    login_response = raw_client.get("/auth/line/login", follow_redirects=False)
    state = parse_qs(urlparse(login_response.headers["location"]).query)["state"][0]

    callback_response = raw_client.get(
        f"/auth/line/callback?code=test-code&state={state}",
        follow_redirects=False,
    )

    assert callback_response.status_code == 302
    redirect_params = parse_qs(urlparse(callback_response.headers["location"]).query)
    assert "token" in redirect_params

    db_session.refresh(existing_user)
    assert existing_user.display_name == "Updated Name"
    assert existing_user.avatar_url == "https://cdn.example.com/new-avatar.jpg"

    get_settings.cache_clear()


def test_exchange_token_success(raw_client, monkeypatch, db_session):
    user = User(
        line_user_id="line-user-exchange",
        display_name="Exchange User",
        avatar_url=None,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")
    get_settings.cache_clear()

    settings = get_settings()
    token = auth_service.create_auth_token(user.id, settings)

    response = raw_client.post("/auth/exchange-token", json={"token": token})
    assert response.status_code == 200
    assert response.json()["display_name"] == "Exchange User"

    # Session should now be active
    me_response = raw_client.get("/auth/me")
    assert me_response.status_code == 200

    get_settings.cache_clear()


def test_exchange_token_expired(raw_client, monkeypatch, db_session):
    user = User(
        line_user_id="line-user-expired",
        display_name="Expired User",
        avatar_url=None,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")
    get_settings.cache_clear()

    settings = get_settings()
    token = auth_service.create_auth_token(user.id, settings)

    # Force expiry by setting max age to -1 (any token age > -1 is always true)
    monkeypatch.setattr(auth_service, "AUTH_TOKEN_MAX_AGE_SECONDS", -1)

    response = raw_client.post("/auth/exchange-token", json={"token": token})
    assert response.status_code == 400
    assert response.json()["detail"] == "Auth token expired"

    get_settings.cache_clear()


def test_exchange_token_invalid(raw_client, monkeypatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")
    get_settings.cache_clear()

    response = raw_client.post("/auth/exchange-token", json={"token": "not.a.valid.token"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid auth token"

    get_settings.cache_clear()
