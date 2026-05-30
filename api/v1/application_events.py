from typing import Any, Protocol, TypeVar


class ApplicationResultWithEvents(Protocol):
    events: list[Any]


class ApplicationEventDispatcher(Protocol):
    async def dispatch(self, events: list[Any]) -> None: ...


ResultT = TypeVar("ResultT", bound=ApplicationResultWithEvents)


async def dispatch_result_events(
    result: ResultT,
    dispatcher: ApplicationEventDispatcher,
) -> ResultT:
    await dispatcher.dispatch(result.events)
    return result
