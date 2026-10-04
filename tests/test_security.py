"""
Regression tests for the security fixes. None of these need a database.
"""
import base64
import io
import json
import re
import zlib

import pytest

from tests.conftest import login_as


def _decode_session_cookie(client):
    """Decode Flask's signed (not encrypted) session cookie the way an attacker would."""
    value = client.get_cookie("session").value
    compressed = value.startswith(".")
    payload = value.lstrip(".").split(".")[0]
    raw = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
    if compressed:
        raw = zlib.decompress(raw)
    return raw.decode()


# ---------------------------------------------------------------------------
# 1. Secret key
# ---------------------------------------------------------------------------

def test_no_hardcoded_secret_key_fallback(make_app):
    first = make_app()
    second = make_app()
    assert first.secret_key not in ("dev-secret", "", None)
    assert len(first.secret_key) >= 32
    # Random per process, so it cannot be guessed from the source code.
    assert first.secret_key != second.secret_key


def test_secret_key_env_names(make_app):
    assert make_app(SECRET_KEY="from-secret-key").secret_key == "from-secret-key"
    assert make_app(FLASK_SECRET_KEY="flask-key", SECRET_KEY="other").secret_key == "flask-key"


def test_session_signed_with_dev_secret_is_rejected(make_app):
    from flask import Flask
    from flask.sessions import SecureCookieSessionInterface

    app = make_app()
    forger = Flask("forger")
    forger.secret_key = "dev-secret"
    forged = SecureCookieSessionInterface().get_signing_serializer(forger).dumps(
        {"user_id": 1, "role": "admin", "name": "x"}
    )
    client = app.test_client()
    client.set_cookie("session", forged)
    response = client.get("/admin/users")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# 2. Database initialization endpoint
# ---------------------------------------------------------------------------

def _forbid_db_reset(monkeypatch):
    import backend.routes.system_routes as system_routes

    def boom(*args, **kwargs):
        raise AssertionError("database reset must not run")

    monkeypatch.setattr(system_routes, "run_schema", boom)
    monkeypatch.setattr(system_routes, "run_seed", boom)


@pytest.mark.parametrize("token", ["default-dev-token", "dev-secret", ""])
def test_init_route_disabled_without_dedicated_token(make_app, monkeypatch, token):
    _forbid_db_reset(monkeypatch)
    app = make_app(FLASK_SECRET_KEY="some-secret")
    response = app.test_client().get(f"/system/initialize-db-cloud-sync?token={token}")
    assert response.status_code == 404


def test_init_route_rejects_wrong_token_and_secret_key(make_app, monkeypatch):
    _forbid_db_reset(monkeypatch)
    app = make_app(FLASK_SECRET_KEY="flask-secret", DB_INIT_TOKEN="init-token-123")
    client = app.test_client()
    assert client.get("/system/initialize-db-cloud-sync?token=wrong").status_code == 403
    # The Flask secret key is no longer accepted as the reset token.
    assert client.get("/system/initialize-db-cloud-sync?token=flask-secret").status_code == 403


# ---------------------------------------------------------------------------
# 3. Debug endpoint listing users
# ---------------------------------------------------------------------------

def test_user_listing_debug_route_not_registered(app, client):
    assert not any("check-users" in rule.rule for rule in app.url_map.iter_rules())
    assert client.get("/test/test/auth/check-users").status_code == 404


# ---------------------------------------------------------------------------
# 4. Email verification OTP
# ---------------------------------------------------------------------------

@pytest.fixture
def signup(monkeypatch):
    """Stub DNS, DB and email for the account-request flow; capture the OTP."""
    import dns.resolver
    import backend.routes.public_routes as public_routes
    import backend.services.email_service as email_service

    sent = {}
    inserted = []

    def fake_send(to, subject, body):
        sent["otp"] = re.search(r"OTP Code: (\d{6})", body).group(1)
        return True

    monkeypatch.setattr(dns.resolver, "resolve", lambda *a, **k: True)
    monkeypatch.setattr(email_service, "send_email", fake_send)
    monkeypatch.setattr(public_routes, "fetch_one", lambda *a, **k: None)
    monkeypatch.setattr(public_routes, "ensure_account_requests_table", lambda: None)
    monkeypatch.setattr(public_routes, "execute_query", lambda q, p=None: inserted.append(p))
    public_routes._otp_failures.clear()
    return sent, inserted


def _request_account(client, email="eve@example.org"):
    return client.post("/request-account", data={"name": "Eve", "email": email, "reason": "hi"})


def test_otp_not_readable_from_session_cookie(client, signup):
    sent, inserted = signup
    assert _request_account(client).status_code == 302
    otp = sent["otp"]
    cookie = _decode_session_cookie(client)
    assert otp not in cookie
    assert "signup_otp" not in json.loads(cookie)

    # The legitimate flow still works with the emailed code.
    response = client.post("/verify-email", data={"otp": otp})
    assert response.status_code == 302 and response.headers["Location"].endswith("/login")
    assert inserted == [("Eve", "eve@example.org", "hi")]


def test_wrong_otp_rejected_and_attempts_limited(client, signup):
    sent, inserted = signup
    _request_account(client)
    for _ in range(5):
        response = client.post("/verify-email", data={"otp": "000000" if sent["otp"] != "000000" else "111111"})
        assert response.headers["Location"].endswith("/verify-email")
    # After 5 failures even the right code is refused.
    client.post("/verify-email", data={"otp": sent["otp"]})
    assert inserted == []


def test_replaying_cookie_does_not_reset_attempt_limit(client, signup):
    sent, inserted = signup
    _request_account(client)
    saved_cookie = client.get_cookie("session").value
    wrong = "000000" if sent["otp"] != "000000" else "111111"
    for _ in range(5):
        client.set_cookie("session", saved_cookie)
        client.post("/verify-email", data={"otp": wrong})
    client.set_cookie("session", saved_cookie)
    client.post("/verify-email", data={"otp": sent["otp"]})
    assert inserted == []


def test_used_otp_cannot_be_replayed(client, signup):
    sent, inserted = signup
    _request_account(client)
    saved_cookie = client.get_cookie("session").value
    client.post("/verify-email", data={"otp": sent["otp"]})
    client.set_cookie("session", saved_cookie)
    client.post("/verify-email", data={"otp": sent["otp"]})
    assert len(inserted) == 1


def test_expired_otp_rejected(client, signup, monkeypatch):
    import backend.routes.public_routes as public_routes

    sent, inserted = signup
    _request_account(client)
    real_time = public_routes.time.time
    monkeypatch.setattr(public_routes.time, "time", lambda: real_time() + public_routes.OTP_TTL_SECONDS + 1)
    client.post("/verify-email", data={"otp": sent["otp"]})
    assert inserted == []


# ---------------------------------------------------------------------------
# 5. Chat authorization and uploads
# ---------------------------------------------------------------------------

DM_CHANNEL = {"channel_id": 7, "name": "DM", "guild_id": None, "is_private": True, "created_by": None}
PUBLIC_CHANNEL = {"channel_id": 2, "name": "Lobby", "guild_id": None, "is_private": False, "created_by": None}
PRIVATE_GROUP = {"channel_id": 9, "name": "Club", "guild_id": None, "is_private": True, "created_by": 50}
GUILD_CHANNEL = {"channel_id": 11, "name": "general", "guild_id": 3, "is_private": False, "created_by": None}


def _fake_db(channels, participants=(), guild_members=()):
    """
    Minimal query router for chat tests.
    participants: {(channel_id, user_id): role}; guild_members: {(guild_id, user_id)}.
    """
    participants = dict(participants)
    guild_members = set(guild_members)

    def fetch_one(query, params=()):
        if "FROM channels" in query:
            return channels.get(params[0])
        if "FROM dm_participants" in query:
            role = participants.get((params[0], params[1]))
            return {"role": role, "ok": 1} if role else None
        if "FROM guild_members" in query:
            return {"ok": 1} if (params[0], params[1]) in guild_members else None
        raise AssertionError(f"unexpected query: {query}")

    return fetch_one


def _patch_db(monkeypatch, fetch_one, executed):
    import backend.repository.db_access as db_access
    import backend.services.channel_service as channel_service

    monkeypatch.setattr(db_access, "fetch_one", fetch_one)
    monkeypatch.setattr(channel_service, "fetch_one", fetch_one)
    monkeypatch.setattr(db_access, "execute", lambda q, p=None: executed.append((q, p)))


@pytest.mark.parametrize("user_id, role, channel, participants, guild_members, expected", [
    (5, "member", PUBLIC_CHANNEL, {}, set(), True),
    (None, "member", PUBLIC_CHANNEL, {}, set(), False),
    (5, "member", DM_CHANNEL, {}, set(), False),
    (5, "admin", DM_CHANNEL, {}, set(), False),
    (5, "member", DM_CHANNEL, {(7, 5): "member"}, set(), True),
    (5, "member", PRIVATE_GROUP, {}, set(), False),
    (5, "admin", PRIVATE_GROUP, {}, set(), True),
    (5, "member", GUILD_CHANNEL, {}, set(), False),
    (5, "member", GUILD_CHANNEL, {}, {(3, 5)}, True),
    (5, "member", None, {}, set(), False),
])
def test_can_access_channel(monkeypatch, user_id, role, channel, participants, guild_members, expected):
    import backend.services.channel_service as channel_service

    monkeypatch.setattr(channel_service, "fetch_one", _fake_db({}, participants, guild_members))
    assert channel_service.can_access_channel(user_id, channel, role) is expected


def test_rename_channel_requires_channel_admin(client, monkeypatch):
    executed = []
    channels = {9: PRIVATE_GROUP}
    _patch_db(monkeypatch, _fake_db(channels, {(9, 5): "member", (9, 6): "admin"}), executed)

    login_as(client, 5)
    response = client.patch("/chat/channels/9", json={"name": "pwned"})
    assert response.status_code == 403
    assert executed == []

    login_as(client, 6)
    response = client.patch("/chat/channels/9", json={"name": "Renamed"})
    assert response.status_code == 200
    assert executed and "UPDATE channels SET name" in executed[0][0]


def test_rename_missing_channel_is_404(client, monkeypatch):
    executed = []
    _patch_db(monkeypatch, _fake_db({}), executed)
    login_as(client, 5)
    assert client.patch("/chat/channels/404", json={"name": "x"}).status_code == 404
    assert executed == []


@pytest.mark.parametrize("filename", ["evil.html", "evil.svg", "evil.js", "noext"])
def test_channel_icon_rejects_non_images(client, monkeypatch, tmp_path, filename):
    executed = []
    _patch_db(monkeypatch, _fake_db({9: PRIVATE_GROUP}, {(9, 6): "admin"}), executed)
    client.application.static_folder = str(tmp_path)
    login_as(client, 6)
    response = client.post(
        "/chat/channels/9/settings",
        data={"icon": (io.BytesIO(b"<script>alert(1)</script>"), filename)},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert not (tmp_path / "uploads" / "channels").exists() or not any((tmp_path / "uploads" / "channels").iterdir())
    assert executed == []


def test_channel_icon_accepts_image(client, monkeypatch, tmp_path):
    executed = []
    _patch_db(monkeypatch, _fake_db({9: PRIVATE_GROUP}, {(9, 6): "admin"}), executed)
    client.application.static_folder = str(tmp_path)
    login_as(client, 6)
    response = client.post(
        "/chat/channels/9/settings",
        data={"icon": (io.BytesIO(b"\x89PNG\r\n\x1a\n"), "logo.PNG")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    saved = list((tmp_path / "uploads" / "channels").iterdir())
    assert len(saved) == 1 and saved[0].suffix == ".png"


def test_messages_route_denies_non_participant(client, monkeypatch):
    import backend.routes.chat_routes as chat_routes

    executed = []
    _patch_db(monkeypatch, _fake_db({7: DM_CHANNEL}), executed)
    monkeypatch.setattr(chat_routes, "get_channel_messages", lambda cid: [{"content": "secret"}])
    login_as(client, 5)
    response = client.get("/chat/channels/7/messages")
    assert response.status_code == 403
    assert b"secret" not in response.data


def test_messages_route_allows_participant(client, monkeypatch):
    import backend.routes.chat_routes as chat_routes

    executed = []
    _patch_db(monkeypatch, _fake_db({7: DM_CHANNEL}, {(7, 5): "member"}), executed)
    monkeypatch.setattr(chat_routes, "get_channel_messages", lambda cid: [{"content": "hello"}])
    login_as(client, 5)
    response = client.get("/chat/channels/7/messages")
    assert response.status_code == 200
    assert response.json["messages"] == [{"content": "hello"}]


def _socket_client(app, flask_client, monkeypatch, participants):
    import importlib
    from backend import socketio
    import backend.chat.socket_service as socket_service
    import backend.services.channel_service as channel_service

    # create_app() re-initialises the shared SocketIO server, which drops
    # handlers registered by an earlier app in this test process; re-import
    # the handler module so it registers on the current server.
    socket_service = importlib.reload(socket_service)

    fetch_one = _fake_db({7: DM_CHANNEL}, participants)
    monkeypatch.setattr(socket_service, "fetch_one", fetch_one)
    monkeypatch.setattr(channel_service, "fetch_one", fetch_one)
    monkeypatch.setattr(socket_service, "get_channel_messages", lambda cid: [])
    monkeypatch.setattr(socket_service, "get_or_create_anon_id", lambda uid: "anon")
    return socketio.test_client(app, flask_test_client=flask_client)


def test_socket_join_denied_for_non_participant(app, client, monkeypatch):
    login_as(client, 5)
    sio = _socket_client(app, client, monkeypatch, {})
    sio.emit("join_channel", {"channel_id": 7})
    names = [event["name"] for event in sio.get_received()]
    assert "error" in names
    assert "message_history" not in names


def test_socket_join_allowed_for_participant(app, client, monkeypatch):
    login_as(client, 5)
    sio = _socket_client(app, client, monkeypatch, {(7, 5): "member"})
    sio.emit("join_channel", {"channel_id": 7})
    names = [event["name"] for event in sio.get_received()]
    assert "message_history" in names


def test_socket_send_denied_for_non_participant(app, client, monkeypatch):
    login_as(client, 5)
    sio = _socket_client(app, client, monkeypatch, {})
    import backend.chat.socket_service as socket_service

    def boom(*args, **kwargs):
        raise AssertionError("message must not be stored")

    monkeypatch.setattr(socket_service.IngestionService, "process_message", staticmethod(boom))
    sio.emit("send_message", {"channel_id": 7, "content": "hi"})
    names = [event["name"] for event in sio.get_received()]
    assert names == ["error"]


def test_responses_disable_mime_sniffing(client):
    assert client.get("/login").headers["X-Content-Type-Options"] == "nosniff"


def _invite_db(monkeypatch, invites, executed, channels=None, participants=(), guild_owner=None):
    base = _fake_db(channels or {}, participants)

    def fetch_one(query, params=()):
        if "FROM chat_invitations" in query:
            return invites.get(params[0])
        if "JOIN guilds" in query:
            return {"owner_id": guild_owner} if guild_owner else None
        return base(query, params)

    _patch_db(monkeypatch, fetch_one, executed)


@pytest.mark.parametrize("channel_id", [7, 9])  # someone's DM, a private group the user is not in
def test_cannot_invite_self_into_foreign_channel(client, monkeypatch, channel_id):
    executed = []
    _invite_db(monkeypatch, {}, executed, channels={7: DM_CHANNEL, 9: PRIVATE_GROUP})
    login_as(client, 5)
    response = client.post("/chat/invites/send", json={"target_user_id": 5, "target_channel_id": channel_id, "type": "GROUP"})
    assert response.status_code == 403
    assert executed == []


def test_member_can_invite_into_own_group(client, monkeypatch):
    executed = []
    _invite_db(monkeypatch, {}, executed, channels={9: PRIVATE_GROUP}, participants={(9, 5): "member"})
    login_as(client, 5)
    response = client.post("/chat/invites/send", json={"target_user_id": 8, "target_channel_id": 9, "type": "GROUP"})
    assert response.status_code == 200
    assert "INSERT INTO chat_invitations" in executed[0][0]


def test_only_invitee_can_answer_invite(client, monkeypatch):
    executed = []
    invite = {"invite_id": 99, "sender_id": 1, "target_user_id": 8, "target_channel_id": 9, "type": "GROUP", "status": "pending"}
    _invite_db(monkeypatch, {99: invite}, executed, channels={9: PRIVATE_GROUP})
    login_as(client, 5)
    response = client.post("/chat/invites/handle", json={"invite_id": 99, "action": "accept"})
    assert response.status_code == 403
    assert executed == []

    login_as(client, 8)
    response = client.post("/chat/invites/handle", json={"invite_id": 99, "action": "accept"})
    assert response.status_code == 200
    assert any("INSERT IGNORE INTO dm_participants" in q for q, _ in executed)
    assert all(p is None or 5 not in p for _, p in executed)


def test_guild_owner_can_answer_group_invite(client, monkeypatch):
    executed = []
    invite = {"invite_id": 99, "sender_id": 1, "target_user_id": 8, "target_channel_id": 11, "type": "GROUP", "status": "pending"}
    _invite_db(monkeypatch, {99: invite}, executed, channels={11: GUILD_CHANNEL}, guild_owner=6)
    login_as(client, 6)
    response = client.post("/chat/invites/handle", json={"invite_id": 99, "action": "reject"})
    assert response.status_code == 200
    assert executed and "UPDATE chat_invitations" in executed[0][0]


def test_answered_invite_cannot_be_reused(client, monkeypatch):
    executed = []
    invite = {"invite_id": 99, "sender_id": 1, "target_user_id": 8, "target_channel_id": None, "type": "DM", "status": "rejected"}
    _invite_db(monkeypatch, {99: invite}, executed)
    login_as(client, 8)
    assert client.post("/chat/invites/handle", json={"invite_id": 99, "action": "accept"}).status_code == 404
    assert executed == []
