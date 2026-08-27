from models.hardware import HardwareType
from schemas.specifications import ComputerSpecs, EmptySpecs, ServerSpecs, SwitchSpecs

SPEC_MODEL_BY_TYPE = {
    HardwareType.computer: ComputerSpecs,
    HardwareType.server: ServerSpecs,
    HardwareType.switch: SwitchSpecs,
    HardwareType.tv: EmptySpecs,
    HardwareType.projector: EmptySpecs,
    HardwareType.printer: EmptySpecs,
    HardwareType.router: EmptySpecs,
    HardwareType.other: EmptySpecs,
}

def validate_specs(hw_type: HardwareType, specs: dict | None) -> dict:
    model = SPEC_MODEL_BY_TYPE[hw_type]
    parsed = model.model_validate(specs or {})
    return parsed.model_dump(exclude_none=True)
