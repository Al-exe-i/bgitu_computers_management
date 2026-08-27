from typing import Any, Protocol


class ApplicationResultWithEvents(Protocol):
    events: list[Any]


class ApplicationEventDispatcher(Protocol):
    async def dispatch(self, events: list[Any]) -> None: ...


async def dispatch_result_events[ResultT: ApplicationResultWithEvents](
    result: ResultT,
    dispatcher: ApplicationEventDispatcher,
) -> ResultT:
    await dispatcher.dispatch(result.events)
    return result
