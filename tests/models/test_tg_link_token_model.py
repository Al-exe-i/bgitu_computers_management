from models.tg_link_token import TelegramLinkToken


def test_tg_link_token_datetime_columns_are_timezone_aware() -> None:
    assert TelegramLinkToken.__table__.c.created_at.type.timezone is True
    assert TelegramLinkToken.__table__.c.expires_at.type.timezone is True
    assert TelegramLinkToken.__table__.c.used_at.type.timezone is True
