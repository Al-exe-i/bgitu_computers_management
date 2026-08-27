import pytest
from pydantic import ValidationError

from models.hardware import HardwareType
from schemas.specifications import MAX_INSTALLED_SOFTWARE_ITEMS
from utils.hw_specs import validate_specs


def test_computer_software_inventory_is_normalized() -> None:
    specs = validate_specs(
        HardwareType.computer,
        {
            "operating_system": "  Windows 11 Pro  ",
            "os_edition": " ",
            "installed_software": [
                "  Mozilla Firefox ",
                "7-Zip",
                "mozilla firefox",
                " ",
            ],
        },
    )

    assert specs == {
        "operating_system": "windows",
        "os_edition": "Windows 11 Pro",
        "installed_software": ["Mozilla Firefox", "7-Zip"],
    }


def test_computer_software_inventory_has_bounded_size() -> None:
    software = [
        f"Application {index}"
        for index in range(MAX_INSTALLED_SOFTWARE_ITEMS + 1)
    ]

    with pytest.raises(ValidationError):
        validate_specs(
            HardwareType.computer,
            {"installed_software": software},
        )


def test_server_does_not_accept_computer_software_inventory() -> None:
    with pytest.raises(ValidationError):
        validate_specs(
            HardwareType.server,
            {"operating_system": "Ubuntu Server 24.04"},
        )


def test_computer_rejects_edition_from_another_operating_system() -> None:
    with pytest.raises(ValidationError):
        validate_specs(
            HardwareType.computer,
            {
                "operating_system": "linux",
                "os_edition": "Windows 11 Pro",
            },
        )
