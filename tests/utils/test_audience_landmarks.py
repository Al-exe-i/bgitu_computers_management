import pytest
from pydantic import ValidationError

from utils.audience_landmarks import normalize_landmarks


def test_normalize_landmarks_strips_values_and_drops_empty_strings() -> None:
    result = normalize_landmarks(
        {
            "north": "  Доска  ",
            "south": "   ",
            "west": "\tОкна\t",
            "east": None,
        }
    )

    assert result == {
        "north": "Доска",
        "west": "Окна",
    }


def test_normalize_landmarks_rejects_unknown_keys() -> None:
    with pytest.raises(ValidationError):
        normalize_landmarks({"north": "Вход", "center": "Стол"})
