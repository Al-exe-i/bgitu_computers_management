import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/v1/admin/invites"),
        ("post", "/api/v1/admin/invites/one"),
        ("post", "/api/v1/admin/invites/batch"),
        ("post", "/api/v1/admin/invites/1/revoke"),
        ("delete", "/api/v1/admin/invites/1"),
        ("post", "/api/v1/auth/invite/preview"),
        ("post", "/api/v1/auth/invite/register"),
    ],
)
def test_invitation_routes_are_removed(method, path):
    with TestClient(app) as client:
        response = client.request(method, path)
    assert response.status_code == 404


def test_openapi_keeps_manual_creation_without_invitation_routes():
    paths = app.openapi()["paths"]
    assert not any("invite" in path for path in paths)
    assert "post" in paths["/api/v1/users"]
