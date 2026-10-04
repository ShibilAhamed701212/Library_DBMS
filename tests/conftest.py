"""
Shared fixtures. Unit tests run without a database: every DB call made
during app setup/request hooks is stubbed out here, and individual tests
stub the specific queries they exercise.
"""
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def make_app(monkeypatch):
    """Factory returning a fresh app with DB-backed hooks stubbed."""
    import backend.services.settings_service as settings_service
    import backend.services.notification_service as notification_service

    monkeypatch.setattr(settings_service, "get_setting", lambda key, default=None: default)
    monkeypatch.setattr(settings_service, "get_all_settings", lambda: {})
    monkeypatch.setattr(notification_service, "get_unread_notifications", lambda user_id: [])

    def _make(**env):
        for key in ("FLASK_SECRET_KEY", "SECRET_KEY", "DB_INIT_TOKEN"):
            monkeypatch.delenv(key, raising=False)
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        from backend.app import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app

    return _make


@pytest.fixture
def app(make_app):
    return make_app(FLASK_SECRET_KEY="test-secret-key")


@pytest.fixture
def client(app):
    return app.test_client()


def login_as(client, user_id, role="member", name="Tester"):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["role"] = role
        sess["name"] = name
