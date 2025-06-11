from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, AsyncGenerator
from collections import defaultdict

# Assuming Message is in core.models, adjust if it's elsewhere or needs a more specific import
from roboco.core.models import Message

class ContextStore(ABC):
    """
    Abstract base class for context stores.
    Defines the interface for managing agent context, including messages,
    scratchpad data, and potentially other forms of state.
    """

    @abstractmethod
    async def add_message(self, conversation_id: str, message: Message) -> None:
        """
        Add a message to a specific conversation's context.

        Args:
            conversation_id: The unique identifier for the conversation or context.
            message: The Message object to add.
        """
        pass

    @abstractmethod
    async def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        before_message_id: Optional[str] = None,
        after_message_id: Optional[str] = None,
    ) -> List[Message]:
        """
        Retrieve messages from a specific conversation's context.

        Args:
            conversation_id: The unique identifier for the conversation.
            limit: Maximum number of messages to retrieve.
            before_message_id: Retrieve messages before this message ID (exclusive).
            after_message_id: Retrieve messages after this message ID (exclusive).

        Returns:
            A list of Message objects.
        """
        pass

    @abstractmethod
    async def stream_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        before_message_id: Optional[str] = None,
        after_message_id: Optional[str] = None,
    ) -> AsyncGenerator[Message, None]:
        """
        Stream messages from a specific conversation's context.

        Args:
            conversation_id: The unique identifier for the conversation.
            limit: Maximum number of messages to retrieve.
            before_message_id: Retrieve messages before this message ID (exclusive).
            after_message_id: Retrieve messages after this message ID (exclusive).

        Yields:
            Message objects as they are retrieved.
        """
        # Ensure the generator is properly defined
        if False: # pragma: no cover
            yield


    @abstractmethod
    async def update_message(self, conversation_id: str, message_id: str, updates: Dict[str, Any]) -> Optional[Message]:
        """
        Update an existing message in the context.
        Note: This might be complex if messages are immutable.
              Alternatively, one might add a new version or an annotation.

        Args:
            conversation_id: The unique identifier for the conversation.
            message_id: The ID of the message to update.
            updates: A dictionary of fields to update.

        Returns:
            The updated Message object, or None if not found.
        """
        pass

    @abstractmethod
    async def delete_message(self, conversation_id: str, message_id: str) -> bool:
        """
        Delete a message from the context.

        Args:
            conversation_id: The unique identifier for the conversation.
            message_id: The ID of the message to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        pass

    @abstractmethod
    async def get_scratchpad(self, context_id: str, key: str) -> Optional[Any]:
        """
        Retrieve a value from the scratchpad associated with a context.

        Args:
            context_id: The unique identifier for the context (e.g., agent_id, session_id).
            key: The key of the data to retrieve.

        Returns:
            The retrieved data, or None if the key doesn't exist.
        """
        pass

    @abstractmethod
    async def set_scratchpad(self, context_id: str, key: str, value: Any) -> None:
        """
        Set a value in the scratchpad associated with a context.

        Args:
            context_id: The unique identifier for the context.
            key: The key of the data to set.
            value: The data to store.
        """
        pass

    @abstractmethod
    async def delete_scratchpad(self, context_id: str, key: str) -> bool:
        """
        Delete a key-value pair from the scratchpad.

        Args:
            context_id: The unique identifier for the context.
            key: The key to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        pass

    @abstractmethod
    async def clear_conversation_context(self, conversation_id: str) -> None:
        """
        Clear all messages and associated data for a specific conversation.

        Args:
            conversation_id: The unique identifier for the conversation.
        """
        pass

    @abstractmethod
    async def clear_scratchpad_context(self, context_id: str) -> None:
        """
        Clear all scratchpad data for a specific context_id.

        Args:
            context_id: The unique identifier for the context.
        """
        pass


class InMemoryContextStore(ContextStore):
    """
    An in-memory implementation of the ContextStore.
    Useful for development, testing, or single-session applications.
    Data is not persisted across application restarts.
    """
    def __init__(self):
        self._conversations: Dict[str, List[Message]] = defaultdict(list)
        self._scratchpads: Dict[str, Dict[str, Any]] = defaultdict(dict)

    async def add_message(self, conversation_id: str, message: Message) -> None:
        self._conversations[conversation_id].append(message)

    async def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        before_message_id: Optional[str] = None, # Not fully implemented for simplicity
        after_message_id: Optional[str] = None,  # Not fully implemented for simplicity
    ) -> List[Message]:
        messages = self._conversations.get(conversation_id, [])
        # Basic filtering for before/after (can be made more robust)
        if after_message_id:
            # Find index of after_message_id, then slice
            try:
                idx = next(i for i, msg in enumerate(messages) if msg.message_id == after_message_id)
                messages = messages[idx+1:]
            except StopIteration:
                messages = [] # after_message_id not found, so no messages after it
        
        if before_message_id:
            # Find index of before_message_id, then slice
            try:
                idx = next(i for i, msg in enumerate(messages) if msg.message_id == before_message_id)
                messages = messages[:idx]
            except StopIteration:
                pass # before_message_id not found, so all current messages are before it (no change needed)

        if limit is not None:
            return messages[-limit:] # Get the last 'limit' messages from the potentially filtered list
        return messages

    async def stream_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        before_message_id: Optional[str] = None,
        after_message_id: Optional[str] = None,
    ) -> AsyncGenerator[Message, None]:
        messages_to_stream = await self.get_messages(
            conversation_id, limit, before_message_id, after_message_id
        )
        for message in messages_to_stream:
            yield message

    async def update_message(self, conversation_id: str, message_id: str, updates: Dict[str, Any]) -> Optional[Message]:
        if conversation_id in self._conversations:
            for i, msg in enumerate(self._conversations[conversation_id]):
                if msg.message_id == message_id:
                    try:
                        updated_msg = msg.model_copy(update=updates)
                        self._conversations[conversation_id][i] = updated_msg
                        return updated_msg
                    except Exception: 
                        return None 
        return None

    async def delete_message(self, conversation_id: str, message_id: str) -> bool:
        if conversation_id in self._conversations:
            original_len = len(self._conversations[conversation_id])
            self._conversations[conversation_id] = [
                msg for msg in self._conversations[conversation_id] if msg.message_id != message_id
            ]
            return len(self._conversations[conversation_id]) < original_len
        return False

    async def get_scratchpad(self, context_id: str, key: str) -> Optional[Any]:
        return self._scratchpads.get(context_id, {}).get(key)

    async def set_scratchpad(self, context_id: str, key: str, value: Any) -> None:
        self._scratchpads[context_id][key] = value

    async def delete_scratchpad(self, context_id: str, key: str) -> bool:
        if context_id in self._scratchpads and key in self._scratchpads[context_id]:
            del self._scratchpads[context_id][key]
            return True
        return False

    async def clear_conversation_context(self, conversation_id: str) -> None:
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]

    async def clear_scratchpad_context(self, context_id: str) -> None:
        if context_id in self._scratchpads:
            del self._scratchpads[context_id]
