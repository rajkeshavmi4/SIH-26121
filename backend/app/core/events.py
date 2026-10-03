import asyncio
from datetime import datetime
from typing import Callable, Dict, List, Any
from pydantic import BaseModel, Field

class DomainEvent(BaseModel):
    event_type: str
    aggregate_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    actor: str = "system"

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[DomainEvent], None]]] = {}
        self._history: List[DomainEvent] = []

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEvent):
        self._history.append(event)
        handlers = self._subscribers.get(event.event_type, []) + self._subscribers.get("*", [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event))
                else:
                    handler(event)
            except Exception:
                pass

    def get_history(self, limit: int = 50) -> List[DomainEvent]:
        return self._history[-limit:]

event_bus = EventBus()
