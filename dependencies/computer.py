from typing import Annotated
from fastapi import Depends
from db.session import session_dep
from repositories.computers_repo import ComputerRepository
from services.computers_service import ComputerService


def get_computer_service(db: session_dep):
    repo = ComputerRepository(db)
    service = ComputerService(repo)
    return service


computer_service_dep = Annotated[ComputerService, Depends(get_computer_service)]