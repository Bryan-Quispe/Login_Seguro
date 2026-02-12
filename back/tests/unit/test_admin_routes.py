import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from fastapi import HTTPException

from app.presentation.routes import admin_routes
from app.application.dto.user_dto import MessageResponse


class FakeUser:
    def __init__(self, id=1, username="user", email=None, role="user", face_registered=False, locked=False):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.face_registered = face_registered
        self.locked_until = None
        self.failed_login_attempts = 0
        self.requires_password_reset = False
        self._locked = locked

    def is_admin(self):
        return self.role == "admin"

    def is_locked(self):
        return self._locked


@pytest.mark.asyncio
async def test_list_users_returns_user_list():
    admin = SimpleNamespace(id=99, username="admin")
    u1 = FakeUser(id=1, username="alice", email="a@example.com", role="user", face_registered=True)
    u2 = FakeUser(id=2, username="bob", email=None, role="auditor", face_registered=False)

    mock_repo = Mock()
    mock_repo.find_all_users.return_value = [u1, u2]

    resp = await admin_routes.list_users(admin=admin, user_repo=mock_repo)

    assert resp.success is True
    assert resp.total == 2
    assert resp.users[0].username == "alice"


@pytest.mark.asyncio
async def test_unlock_user_user_not_found_raises_404():
    admin = SimpleNamespace(id=99, username="admin")
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = None

    with pytest.raises(HTTPException) as exc:
        await admin_routes.unlock_user(request=Mock(), user_id=123, admin=admin, user_repo=mock_repo, audit_service=AsyncMock())

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_unlock_user_admin_cannot_be_modified():
    admin = SimpleNamespace(id=99, username="admin")
    admin_user = FakeUser(id=123, username="admin", role="admin")
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = admin_user

    with pytest.raises(HTTPException) as exc:
        await admin_routes.unlock_user(request=Mock(), user_id=123, admin=admin, user_repo=mock_repo, audit_service=AsyncMock())

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_unlock_user_db_failure_raises_500():
    admin = SimpleNamespace(id=99, username="admin")
    target = FakeUser(id=5, username="johndoe", role="user")
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = target
    mock_repo.unlock_user.return_value = False

    with pytest.raises(HTTPException) as exc:
        await admin_routes.unlock_user(request=Mock(), user_id=5, admin=admin, user_repo=mock_repo, audit_service=AsyncMock())

    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_unlock_user_success_calls_audit_and_returns_message():
    admin = SimpleNamespace(id=99, username="admin")
    target = FakeUser(id=5, username="johndoe", role="user")
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = target
    mock_repo.unlock_user.return_value = True

    mock_audit = AsyncMock()
    mock_audit.log_action.return_value = 1

    resp = await admin_routes.unlock_user(request=Mock(), user_id=5, admin=admin, user_repo=mock_repo, audit_service=mock_audit)

    assert isinstance(resp, MessageResponse)
    assert resp.success is True
    assert resp.data["user_id"] == 5
    mock_repo.unlock_user.assert_called_once_with(5)
    mock_audit.log_action.assert_awaited()


@pytest.mark.asyncio
async def test_create_user_username_conflict_raises_400():
    admin = SimpleNamespace(id=99, username="admin")
    mock_repo = Mock()
    mock_repo.find_by_username.return_value = FakeUser(id=2, username="exists")

    data = SimpleNamespace(username="exists", email=None, role="user")

    with pytest.raises(HTTPException) as exc:
        await admin_routes.create_user(request=Mock(), data=data, admin=admin, user_repo=mock_repo, audit_service=AsyncMock())

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_user_email_conflict_raises_400():
    admin = SimpleNamespace(id=99, username="admin")
    mock_repo = Mock()
    mock_repo.find_by_username.return_value = None
    mock_repo.find_by_email.return_value = FakeUser(id=3, username="other")

    data = SimpleNamespace(username="newuser", email="a@b.com", role="user")

    with pytest.raises(HTTPException) as exc:
        await admin_routes.create_user(request=Mock(), data=data, admin=admin, user_repo=mock_repo, audit_service=AsyncMock())

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_user_success_calls_repo_and_audit():
    admin = SimpleNamespace(id=99, username="admin")
    mock_repo = Mock()
    mock_repo.find_by_username.return_value = None
    mock_repo.find_by_email.return_value = None

    created = FakeUser(id=77, username="newuser", role="user")
    mock_repo.create.return_value = created

    mock_audit = AsyncMock()
    resp = await admin_routes.create_user(request=Mock(), data=SimpleNamespace(username="newuser", email=None, role="user"), admin=admin, user_repo=mock_repo, audit_service=mock_audit)

    assert resp.success is True
    assert resp.data["user_id"] == 77
    mock_repo.create.assert_called_once()
    mock_audit.log_action.assert_awaited()
