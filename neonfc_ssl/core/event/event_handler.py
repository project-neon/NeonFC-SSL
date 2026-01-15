from typing import TYPE_CHECKING, Callable, Any
if TYPE_CHECKING:
    from neonfc_ssl.core.event import Event, EventType


NO_CALLBACK_REGISTERED = "No callback registered for event type: {}"


class EventHandler:
    """Handles event registration and dispatching"""
    def __init__(self):
        self._handlers: dict["EventType", Callable[["Event"], None]] = {}

    def register_from_instance(self, instance: Any):
        """Auto-discover and register methods decorated with @handles"""
        # Get the class's method resolution order to find all methods
        for cls in type(instance).__mro__:
            for name, method in cls.__dict__.items():
                # Skip private attributes (but allow _on_* methods)
                if name.startswith('__'):
                    continue

                # Check if it has the decorator marker
                if hasattr(method, '_handles_event'):
                    # Bind the method to the instance
                    bound_method = getattr(instance, name)
                    event_type = method._handles_event
                    self._handlers[event_type] = bound_method

    def subscribe(self, event_type: "EventType", handler: Callable[["Event"], None]):
        """Manually register a handler for an event type"""
        self._handlers[event_type] = handler

    def __call__(self, event: "Event"):
        """Dispatch event to registered handler"""
        handler = self._handlers.get(event.type)
        if handler:
            handler(event)

    def has_handler(self, event_type: "EventType") -> bool:
        """Check if a handler is registered for this event type"""
        return event_type in self._handlers

    def subscriptions(self) -> list["EventType"]:
        """Get current event type to handler mapping"""
        return list(self._handlers.keys())

def event_callback(event_type: "EventType"):
    """Decorator to mark methods as event handlers"""
    def decorator(func: Callable) -> Callable:
        func._handles_event = event_type
        return func
    return decorator
