from pydantic import BaseModel


class ComputerBase(BaseModel):
    name: str
    state: bool = True


class ComputerCreate(ComputerBase):
    row_id: int


class ComputerUpdate(BaseModel):
    description: str | None = None
    state: bool | None = None


class Computer(ComputerBase):
    id: int
    row_id: int
    description: str | None = None