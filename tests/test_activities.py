import copy
import pytest
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
import src.app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    """Ensure the in-memory `activities` dict is reset for each test (Arrange)."""
    original = copy.deepcopy(app_module.activities)
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original))
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original))


@pytest.mark.anyio
async def test_get_activities_returns_all():
    # Arrange: fixture provides a known state
    # Act
    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get("/activities")
    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


@pytest.mark.anyio
async def test_signup_for_activity_adds_participant():
    # Arrange
    activity = "Chess Club"
    email = "new_student@mergington.edu"
    assert email not in app_module.activities[activity]["participants"]
    # Act
    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert resp.status_code == 200
    assert email in app_module.activities[activity]["participants"]
    assert f"Signed up {email} for {activity}" in resp.json().get("message", "")


@pytest.mark.anyio
async def test_signup_for_nonexistent_activity_returns_404():
    # Arrange
    activity = "Nonexistent Club"
    email = "x@x.com"
    # Act
    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_unregister_removes_participant():
    # Arrange
    activity = "Chess Club"
    existing = app_module.activities[activity]["participants"][0]
    assert existing in app_module.activities[activity]["participants"]
    # Act
    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.delete(f"/activities/{activity}/signup", params={"email": existing})
    # Assert
    assert resp.status_code == 200
    assert existing not in app_module.activities[activity]["participants"]
    assert f"Removed {existing} from {activity}" in resp.json().get("message", "")


@pytest.mark.anyio
async def test_unregister_nonexistent_participant_returns_404():
    # Arrange
    activity = "Chess Club"
    email = "not_a_member@mergington.edu"
    assert email not in app_module.activities[activity]["participants"]
    # Act
    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.delete(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert resp.status_code == 404
