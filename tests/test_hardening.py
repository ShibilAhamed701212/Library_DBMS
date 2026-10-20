"""
Regression tests for the second audit pass: CSRF origin check, forced
password change, support-ticket ownership. No database needed.
"""
import pytest

from tests.conftest import login_as


# ---------------------------------------------------------------------------
# CSRF: state-changing requests from another origin are rejected
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("headers", [
    {"Origin": "https://evil.example"},
    {"Referer": "https://evil.example/attack.html"},
    {"Origin": "null"},
])
def test_cross_origin_post_rejected(client, headers):
    login_as(client, 5)
    response = client.post("/chat/anonymous", json={"is_anon": True}, headers=headers)
    assert response.status_code == 403
    with client.session_transaction() as sess:
        assert "is_anon" not in sess


@pytest.mark.parametrize("headers", [
    {"Origin": "http://localhost"},
    {"Referer": "http://localhost/member/community"},
    {},  # non-browser client without Origin/Referer
])
def test_same_origin_post_allowed(client, headers):
    login_as(client, 5)
    response = client.post("/chat/anonymous", json={"is_anon": True}, headers=headers)
    assert response.status_code == 200


def test_trusted_origin_allowed(make_app):
    app = make_app(FLASK_SECRET_KEY="k", CSRF_TRUSTED_ORIGINS="library.example.org")
    client = app.test_client()
    login_as(client, 5)
    response = client.post("/chat/anonymous", json={"is_anon": True},
                           headers={"Origin": "https://library.example.org"})
    assert response.status_code == 200


def test_cross_origin_get_not_blocked(client):
    assert client.get("/login", headers={"Origin": "https://evil.example"}).status_code == 200


def test_session_cookie_samesite_lax(app):
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True


# ---------------------------------------------------------------------------
# Forced password change can no longer be skipped
# ---------------------------------------------------------------------------

def test_login_with_temporary_password_sets_flag(client, monkeypatch):
    import backend.routes.auth_routes as auth_routes

    monkeypatch.setattr(auth_routes, "authenticate_user", lambda e, p: {
        "user_id": 5, "role": "member", "name": "M", "must_change_password": True,
    })
    response = client.post("/login", data={"email": "m@x.org", "password": "temp"})
    assert response.headers["Location"].endswith("/change-password")
    # Navigating elsewhere is redirected back until the password is changed.
    response = client.get("/member/dashboard")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/change-password")
    assert client.get("/change-password").status_code == 200


def test_changing_password_clears_flag(client, monkeypatch):
    import backend.routes.auth_routes as auth_routes

    updates = []
    monkeypatch.setattr(auth_routes, "execute", lambda q, p=None: updates.append(p))
    monkeypatch.setattr(auth_routes, "hash_password", lambda pw: "hashed")
    login_as(client, 5)
    with client.session_transaction() as sess:
        sess["must_change_password"] = True
    response = client.post("/change-password", data={"password": "N3w-password!", "confirm_password": "N3w-password!"})
    assert response.headers["Location"].endswith("/member/dashboard")
    assert updates == [("hashed", 5)]
    with client.session_transaction() as sess:
        assert "must_change_password" not in sess


# ---------------------------------------------------------------------------
# Support tickets
# ---------------------------------------------------------------------------

@pytest.fixture
def tickets(monkeypatch):
    import backend.routes.member_routes as member_routes
    import backend.services.support_service as support_service

    replies = []
    owners = {1: 6}
    monkeypatch.setattr(
        member_routes, "fetch_one",
        lambda q, p=(): {"user_id": owners[p[0]]} if "FROM tickets" in q and p[0] in owners else None,
    )
    monkeypatch.setattr(support_service, "add_reply", lambda tid, uid, msg: replies.append((tid, uid)) or "ok")
    monkeypatch.setattr(support_service, "get_ticket_details", lambda tid: {
        "ticket": {"ticket_id": tid, "user_id": owners.get(tid), "subject": "s", "status": "open", "user_name": "u", "created_at": None},
        "replies": [],
    } if tid in owners else None)
    return replies


def test_member_cannot_read_or_reply_to_others_ticket(client, tickets):
    login_as(client, 5)
    response = client.get("/member/support/1")
    assert response.status_code == 302 and response.headers["Location"].endswith("/member/support")
    client.post("/member/support/1", data={"message": "hijack"})
    assert tickets == []


def test_member_can_reply_to_own_ticket(client, tickets):
    login_as(client, 6)
    client.post("/member/support/1", data={"message": "hello"})
    assert tickets == [(1, 6)]


def test_admin_unknown_ticket_is_404(client, monkeypatch):
    import backend.services.support_service as support_service

    monkeypatch.setattr(support_service, "get_ticket_details", lambda tid: None)
    login_as(client, 1, role="admin")
    assert client.get("/admin/support/999").status_code == 404
