from pydantic import BaseModel


class Computer(BaseModel):
    id: int
    name: str
    state: bool