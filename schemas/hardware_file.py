from pydantic import BaseModel, computed_field


class HardwareFileBase(BaseModel):
    file_path: str
    file_type: str
    hardware_id: int

class HardwareFileCreate(HardwareFileBase):
    pass

class HardwareFileResponse(HardwareFileBase):
    id: int

    @computed_field
    def url(self) -> str:
        return f"/hardware/files/{self.id}"