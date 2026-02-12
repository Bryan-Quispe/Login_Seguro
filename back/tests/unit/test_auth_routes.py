import pytest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.presentation import routes as routes_pkg
from app.presentation.routes import auth_routes


class FakeUser:
    def __init__(self, id=1, username="user", email="u@e.com", role="user", face_registered=False):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.face_registered = face_registered
        self.created_at = datetime(2020, 1, 1)
        self.updated_at = datetime(2020, 1, 2)
        self.password_hash = "oldhash"
        self.active_session_token = "tok"

    def has_backup_code(self):
        return False


@pytest.mark.asyncio
async def test_register_success(monkeypatch):
    data = SimpleNamespace(username="newuser", password="P@ssw0rd1", email=None)

    fake_user = SimpleNamespace(id=10, username="newuser")

    class DummyUseCase:
        def __init__(self, repo):
            self.repo = repo

        def execute(self, data_in):
            return True, "Usuario creado", fake_user

    monkeypatch.setattr(auth_routes, "RegisterUserUseCase", DummyUseCase)
    resp = await auth_routes.register.__wrapped__(request=Mock(), data=data, user_repo=Mock())

    assert resp.success is True
    assert resp.data["user_id"] == 10


@pytest.mark.asyncio
async def test_register_failure_raises_400(monkeypatch):
    data = SimpleNamespace(username="bad", password="weak", email=None)

    class DummyUseCase:
        def __init__(self, repo):
            pass

        def execute(self, data_in):
            return False, "Error: invalid", None

    monkeypatch.setattr(auth_routes, "RegisterUserUseCase", DummyUseCase)
    with pytest.raises(HTTPException) as exc:
        await auth_routes.register.__wrapped__(request=Mock(), data=data, user_repo=Mock())

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_login_success_returns_token(monkeypatch):
    data = SimpleNamespace(username="u", password="p")
    token_resp = SimpleNamespace(access_token="abc", token_type="bearer", expires_in=3600, user={"id":1}, requires_face_registration=False)

    class DummyUseCase:
        def __init__(self, repo):
            pass

        def execute(self, data_in):
            return True, None, token_resp, None

    monkeypatch.setattr(auth_routes, "LoginUserUseCase", DummyUseCase)
    result = await auth_routes.login.__wrapped__(request=Mock(), data=data, user_repo=Mock())
    assert result is token_resp


@pytest.mark.asyncio
async def test_login_failure_returns_401_with_additional_data(monkeypatch):
    data = SimpleNamespace(username="u", password="p")
    locked_until = datetime.now() + timedelta(minutes=30)

    class DummyUseCase:
        def __init__(self, repo):
            pass

        def execute(self, data_in):
            return False, "Invalid credentials", None, {"remaining_attempts": 1, "account_locked": True, "locked_until": locked_until, "role": "user", "active_session_exists": True}

    monkeypatch.setattr(auth_routes, "LoginUserUseCase", DummyUseCase)
    resp = await auth_routes.login.__wrapped__(request=Mock(), data=data, user_repo=Mock())
    assert resp.status_code == 401
    assert resp.json()["account_locked"] is True


@pytest.mark.asyncio
async def test_health_check():
    resp = await auth_routes.health_check()
    assert resp == {"status": "healthy", "service": "auth"}


@pytest.mark.asyncio
async def test_logout_user_not_found_raises_404():
    payload = {"sub": 1}
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = None

    with pytest.raises(HTTPException) as exc:
        await auth_routes.logout(payload=payload, user_repo=mock_repo)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_logout_success_updates_user(monkeypatch):
    payload = {"sub": 1}
    user = FakeUser(id=1, username="u")
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = user

    res = await auth_routes.logout(payload=payload, user_repo=mock_repo)
    assert res["success"] is True
    assert mock_repo.update.called


@pytest.mark.asyncio
async def test_get_profile_user_not_found_raises_404():
    payload = {"sub": 5}
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = None

    with pytest.raises(HTTPException):
        await auth_routes.get_profile(payload=payload, user_repo=mock_repo)


@pytest.mark.asyncio
async def test_get_profile_success_returns_profile():
    payload = {"sub": 7}
    user = FakeUser(id=7, username="bob", email="b@e.com", role="user", face_registered=True)
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = user

    resp = await auth_routes.get_profile(payload=payload, user_repo=mock_repo)
    assert resp.success is True
    assert resp.user["username"] == "bob"


@pytest.mark.asyncio
async def test_change_password_user_not_found_raises_404():
    payload = {"sub": 9}
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = None

    with pytest.raises(HTTPException) as exc:
           await auth_routes.change_password.__wrapped__(request=Mock(), data=SimpleNamespace(current_password="a", new_password="b"), payload=payload, user_repo=mock_repo)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_change_password_invalid_current_raises_400(monkeypatch):
    payload = {"sub": 2}
    user = FakeUser(id=2, username="u")
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = user

    # Patch bcrypt.checkpw to return False
    monkeypatch.setattr("bcrypt.checkpw", lambda a, b: False)

    with pytest.raises(HTTPException) as exc:
        await auth_routes.change_password.__wrapped__(request=Mock(), data=SimpleNamespace(current_password="x", new_password="y12345678"), payload=payload, user_repo=mock_repo)

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_change_password_same_new_raises_400(monkeypatch):
    payload = {"sub": 3}
    user = FakeUser(id=3, username="u")
    user.password_hash = "hashed"
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = user

    # make checkpw True
    monkeypatch.setattr("bcrypt.checkpw", lambda a, b: True)

    with pytest.raises(HTTPException) as exc:
        await auth_routes.change_password.__wrapped__(request=Mock(), data=SimpleNamespace(current_password="same", new_password="same"), payload=payload, user_repo=mock_repo)

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_change_password_success(monkeypatch):
    payload = {"sub": 4}
    user = FakeUser(id=4, username="u", face_registered=False)
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = user

    monkeypatch.setattr("bcrypt.checkpw", lambda a, b: True)
    monkeypatch.setattr("bcrypt.gensalt", lambda rounds=12: b"s")
    monkeypatch.setattr("bcrypt.hashpw", lambda pw, s: b"newhash")
    res = await auth_routes.change_password.__wrapped__(request=Mock(), data=SimpleNamespace(current_password="x", new_password="newpass123"), payload=payload, user_repo=mock_repo)
    assert res["success"] is True
    assert mock_repo.update.called
