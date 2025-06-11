from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Optional, Type, TypeVar, Union, Dict, List
import asyncio
from collections import defaultdict
import inspect # For checking if a handler is async

from .events import Event # Assuming events.py is in the same package

# Type variable for specific event types in subscriptions
E = TypeVar('E', bound=Event)

# Define a type for an event handler (callback)
# It can be a regular function or an async function
EventHandler = Callable[[E], Union[None, Awaitable[None]]]

class EventBus(ABC):
    """
    Abstract base class for an event bus.
    Defines the interface for publishing events and managing subscriptions.
    """

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """
        Publish an event to the bus.
        The bus will then distribute it to all relevant subscribers.

        Args:
            event: The Event object to publish.
        """
        pass

    @abstractmethod
    def subscribe(
        self,
        event_type: Union[Type[E], str], # Can subscribe to a specific Event class or by event_type string
        handler: EventHandler[E]
    ) -> None:
        """
        Subscribe a handler to a specific event type.

        Args:
            event_type: The type of event to subscribe to (e.g., MessageSentEvent or "agent.message.sent").
                        If a class is provided, it will subscribe to that class and its subclasses.
                        If a string is provided, it will subscribe to events with that exact event_type.
            handler: The callable (sync or async) that will be invoked when the event occurs.
                     It will receive the event instance as its only argument.
        """
        pass

    @abstractmethod
    def unsubscribe(
        self,
        event_type: Union[Type[E], str],
        handler: EventHandler[E]
    ) -> None:
        """
        Unsubscribe a handler from a specific event type.

        Args:
            event_type: The type of event to unsubscribe from.
            handler: The handler function to remove.
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """
        Start the event bus, if it requires an explicit start (e.g., for background processing).
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the event bus and clean up resources.
        """
        pass

    # Optional: Methods for more advanced subscription patterns
    # def subscribe_all(self, handler: EventHandler[Event]) -> None:
    #     """Subscribe a handler to all events."""
    #     pass

    # def unsubscribe_all(self, handler: EventHandler[Event]) -> None:
    #     """Unsubscribe a handler from all events."""
    #     pass


class InMemoryEventBus(EventBus):
    """
    An in-memory implementation of the EventBus.
    Handles event publishing and subscription within a single process.
    Supports both synchronous and asynchronous event handlers.
    """
    def __init__(self):
        # Stores subscriptions.
        # Key: Event type (str or class)
        # Value: List of event handlers
        self._subscriptions: Dict[Union[Type[Event], str], List[EventHandler]] = defaultdict(list)
        self._running = False

    async def publish(self, event: Event) -> None:
        if not self._running:
            # Or raise an error, or queue events if desired
            print(f"Warning: EventBus is not running. Event {event.event_type} not published.")
            return

        handlers_to_call: List[EventHandler] = []

        # Check for handlers subscribed to the specific event class
        event_class = type(event)
        if event_class in self._subscriptions:
            handlers_to_call.extend(self._subscriptions[event_class])

        # Check for handlers subscribed to the event_type string
        # Avoid double-adding if class and string subscriptions point to same handler list
        if event.event_type != event_class and event.event_type in self._subscriptions:
            for handler in self._subscriptions[event.event_type]:
                if handler not in handlers_to_call: # Ensure handler uniqueness for this event
                    handlers_to_call.append(handler)
        
        # Check for handlers subscribed to parent classes (polymorphism)
        # Iterate through all subscribed types that are classes
        for subscribed_type in list(self._subscriptions.keys()): # list() to avoid issues if dict changes during iteration
            if inspect.isclass(subscribed_type) and issubclass(event_class, subscribed_type) and subscribed_type != event_class:
                for handler in self._subscriptions[subscribed_type]:
                    if handler not in handlers_to_call:
                        handlers_to_call.append(handler)
        
        for handler in handlers_to_call:
            try:
                # Check if the handler is an async function or a coroutine
                if inspect.iscoroutinefunction(handler) or inspect.isawaitable(handler(event)):
                    await handler(event) # type: ignore[misc]
                else:
                    handler(event) # type: ignore[call-arg]
            except Exception as e:
                # Log the error, but don't let one handler break others
                print(f"Error executing event handler {getattr(handler, '__name__', str(handler))} for event {event.event_type}: {e}")
                # Optionally, publish an ErrorOccurredEvent

    def subscribe(self, event_type: Union[Type[E], str], handler: EventHandler[E]) -> None:
        if handler not in self._subscriptions[event_type]:
            self._subscriptions[event_type].append(handler)

    def unsubscribe(self, event_type: Union[Type[E], str], handler: EventHandler[E]) -> None:
        if event_type in self._subscriptions:
            try:
                self._subscriptions[event_type].remove(handler)
                if not self._subscriptions[event_type]: # Clean up empty list
                    del self._subscriptions[event_type]
            except ValueError:
                # Handler not found, ignore silently or log
                pass

    async def start(self) -> None:
        self._running = True
        # In a more complex bus, this might start background tasks, connect to brokers, etc.
        print("InMemoryEventBus started.")

    async def stop(self) -> None:
        self._running = False
        # Clean up resources, ensure pending tasks are handled, etc.
        print("InMemoryEventBus stopped.")
