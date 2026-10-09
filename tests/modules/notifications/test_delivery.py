import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from modules.notifications.public import AudienceChangedNotification
from modules.notifications.services.delivery import RealtimeNotificationDispatcher
from modules.notifications.services.recipients import (
    RealtimeNotificationRecipientService,
)
from modules.notifications.services.renderer import RealtimeNotificationRenderer


@pytest.fixture
def delivery():
    context = SimpleNamespace(id=10, public_id=uuid4(), number=228, office_id=1)
    audiences = SimpleNamespace(get_one_short=AsyncMock(return_value=context))
    subscriptions = SimpleNamespace(list_recipient_user_ids=AsyncMock(return_value=[7]))
    publisher = SimpleNamespace(publish_notification=AsyncMock())
    dispatcher = RealtimeNotificationDispatcher(
        recipients=RealtimeNotificationRecipientService(subscriptions, audiences),
        renderer=RealtimeNotificationRenderer(),
        publisher=publisher,
    )
    return dispatcher, audiences, publisher


def test_audience_update_uses_public_id_in_payload(delivery):
    dispatcher, audiences, publisher = delivery
    result = asyncio.run(
        dispatcher.send_audience_changed(AudienceChangedNotification(10))
    )
    assert result.sent == 1
    payload = publisher.publish_notification.call_args.kwargs["payload"]
    assert payload["audience_public_id"] == str(
        audiences.get_one_short.return_value.public_id
    )
    assert payload["event_type"] == "audience_changed"


def test_deleted_audience_is_not_published(delivery):
    dispatcher, audiences, publisher = delivery
    audiences.get_one_short.return_value = None
    result = asyncio.run(
        dispatcher.send_audience_changed(AudienceChangedNotification(10))
    )
    assert result.sent == 0
    publisher.publish_notification.assert_not_awaited()


def test_publish_failure_is_not_reported_as_success(delivery):
    dispatcher, _, publisher = delivery
    publisher.publish_notification.side_effect = RuntimeError("transport unavailable")
    with pytest.raises(RuntimeError, match="transport unavailable"):
        asyncio.run(dispatcher.send_audience_changed(AudienceChangedNotification(10)))
