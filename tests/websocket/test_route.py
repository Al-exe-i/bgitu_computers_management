from fastapi.testclient import TestClient

from main import app


def test_websocket_route_delivers_matching_audience_updates() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws?audience_id=5") as websocket:
            client.portal.call(client.app.state.realtime.publish_audience_updated, 5)

            assert websocket.receive_json() == {"audience_updated": 5}
