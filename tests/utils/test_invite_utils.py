from utils.invite_utils import hash_invite_token, new_invite_token


def test_new_invite_token_returns_non_empty_unique_values() -> None:
    first_token = new_invite_token()
    second_token = new_invite_token()

    assert first_token
    assert second_token
    assert first_token != second_token


def test_hash_invite_token_is_deterministic() -> None:
    token = "invite-token"

    assert hash_invite_token(token) == hash_invite_token(token)
    assert hash_invite_token(token) != hash_invite_token("other-token")
