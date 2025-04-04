"""
Chat Service

This module provides services for managing chat interactions with project agents.
It follows DDD principles by encapsulating chat-related business logic.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

logger = logger.bind(module=__name__)

from roboco.core.config import load_config, get_llm_config, get_workspace
from roboco.teams.planning import PlanningTeam
from roboco.core.project_manager import ProjectManager
from roboco.services.project_service import ProjectService
from roboco.core.models import (
    MessageRole,
    Message,
    MessageType
)
from roboco.core.models.chat import (
    ChatRequest, 
    ChatResponse,
    ChatStatus
)
from roboco.utils.id_generator import generate_short_id

# Define custom status models locally to avoid circular imports
class MessageStatus:
    """Status of a message thread."""
    def __init__(self, conversation_id: str, status: str, message: str, **kwargs):
        self.conversation_id = conversation_id
        self.status = status
        self.message = message
        self.project_id = kwargs.get("project_id")
        self.project_details = kwargs.get("project_details")
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
        self.progress = kwargs.get("progress", 0)
        
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary (compatible with Pydantic models)."""
        result = {
            "conversation_id": self.conversation_id,
            "status": self.status,
            "message": self.message,
            "progress": self.progress
        }
        
        if self.project_id:
            result["project_id"] = self.project_id
            
        if self.project_details:
            result["project_details"] = self.project_details
            
        if self.created_at:
            result["created_at"] = self.created_at
            
        if self.updated_at:
            result["updated_at"] = self.updated_at
            
        return result

class MessageHistory:
    """Complete history of a message thread."""
    def __init__(self, conversation_id: str, status: str, messages: List[Dict], **kwargs):
        self.conversation_id = conversation_id
        self.status = status
        self.messages = messages
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
        self.project_id = kwargs.get("project_id")
        self.title = kwargs.get("title")
        self.description = kwargs.get("description")
        self.files = kwargs.get("files", [])
        
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary (compatible with Pydantic models)."""
        result = {
            "conversation_id": self.conversation_id,
            "status": self.status,
            "messages": self.messages
        }
        
        if self.created_at:
            result["created_at"] = self.created_at
            
        if self.updated_at:
            result["updated_at"] = self.updated_at
            
        if self.project_id:
            result["project_id"] = self.project_id
            
        if self.title:
            result["title"] = self.title
            
        if self.description:
            result["description"] = self.description
            
        if self.files:
            result["files"] = self.files
            
        return result

class ChatService:
    """
    Service for managing chat interactions with project agents.
    
    This service follows the DDD principles by encapsulating chat-related
    business logic and providing a clean interface for the API layer.
    """
    
    def __init__(self):
        """
        Initialize the chat service with its dependencies.
        """
        # Store conversation history - in a real implementation, this would be persisted
        self.conversations = {}
        
        # Store conversation statuses with timestamps - in a real implementation, this would be persisted
        self.conversation_statuses = {}
        
        # Store file tracking
        self.files = {}
        
        # Load config for LLM settings
        self.config = load_config()
        self.llm_config = get_llm_config(self.config)
        
        # Set workspace directory from configuration
        self.workspace_dir = str(get_workspace(self.config))
        
        # Create services - reuse instances instead of creating new ones per request
        self.project_service = ProjectService()
    
    async def start_chat(self, chat_request: ChatRequest) -> ChatResponse:
        """Start a new chat session and process the request.
        
        Args:
            chat_request: The chat request containing the query
            
        Returns:
            Response with conversation ID and results
        """
        # Generate a new conversation ID
        conversation_id = generate_short_id()
        
        # Generate a new project ID (will be used if a project is created)
        project_id = generate_short_id()
        
        # Initialize conversation
        current_time = datetime.now().isoformat()
        conversation = {
            "messages": [],
            "created_at": current_time,
            "updated_at": current_time,
            "project_id": None,  # Will be set if a project is created
            "title": f"Conversation {conversation_id}"
        }
        self.conversations[conversation_id] = conversation
        
        # Initialize files collection for this conversation
        self.files[conversation_id] = []
        
        # Initialize status as PENDING
        await self.update_conversation_status(
            conversation_id=conversation_id,
            status=ChatStatus.PENDING,
            message=f"Processing query: {chat_request.query}"
        )
        
        # Add user message to conversation history with proper structure
        message_id = generate_short_id()
        current_time = datetime.now().isoformat()
        
        user_message = {
            "id": message_id,
            "role": MessageRole.USER,
            "content": chat_request.query,
            "timestamp": current_time,
            "type": MessageType.TEXT
        }
        
        conversation["messages"].append(user_message)
        conversation["updated_at"] = current_time
        
        # Update conversation title based on first query
        words = chat_request.query.split()
        title = " ".join(words[:5])
        if len(words) > 5:
            title += "..."
        conversation["title"] = title
        
        # Update status to PLANNING
        await self.update_conversation_status(
            conversation_id=conversation_id, 
            status=ChatStatus.PLANNING,
            message="Planning project execution..."
        )
        
        # Create and execute a project based on the query
        response = await self._create_and_execute_project(conversation_id, chat_request, message_id)
        
        return response
    
    async def _handle_follow_up_message(self, conversation_id: str, chat_request, message_id: str) -> ChatResponse:
        """Handle a follow-up message in an existing conversation."""
        conversation = self.conversations[conversation_id]
        project_id = conversation.get("project_id")
        
        # Create planner for general chat
        planning_team = PlanningTeam(project_id=project_id)
        
        # Get project status if available
        project_status = None
        response_message = ""
        
        try:
            if project_id:
                # Update status to show we're checking project status
                await self.update_conversation_status(
                    conversation_id=conversation_id, 
                    status=ChatStatus.EXECUTING,
                    message="Retrieving project status and processing query..."
                )
                
                project_status = await self.project_service.get_project_status(project_id)
                
                # Add project context to the query
                context = (
                    f"Project: {project_status['name']}\n"
                    f"Status: {project_status['status']}\n"
                    f"Progress: {project_status['progress']}% "
                    f"({project_status['completed_tasks']}/{project_status['total_tasks']} tasks completed)\n\n"
                )
                
                # Add project context to query
                contextual_query = (
                    f"The user is asking about project '{project_status['name']}' "
                    f"which is {project_status['progress']}% complete. "
                    f"Their query is: {chat_request.query}"
                )
                
                # Run chat with context
                chat_result = await planning_team.run_chat(
                    query=contextual_query,
                    teams=["planning"]  # Default to planning team
                )
                
                # Combine status and response
                response_message = context + chat_result["response"]
            else:
                # No project context, just regular chat
                await self.update_conversation_status(
                    conversation_id=conversation_id, 
                    status=ChatStatus.EXECUTING,
                    message="Processing chat query..."
                )
                    
                chat_result = await planning_team.run_chat(
                    query=chat_request.query,
                    teams=["versatile"]  # Default to versatile team
                )
                response_message = chat_result["response"]
        
            # Add response to conversation history
            conversation["messages"].append({
                    "id": message_id,
                    "role": MessageRole.ASSISTANT,
                "content": response_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update status to COMPLETED
            await self.update_conversation_status(
                conversation_id=conversation_id, 
                status=ChatStatus.COMPLETED,
                message="Query processed successfully",
                project_details=project_status
            )
        
            # Return formatted response
            return ChatResponse(
                conversation_id=conversation_id,
                message=response_message,
                project_id=project_id,
                project_details=project_status,
                status=ChatStatus.COMPLETED
                )
        except Exception as e:
            logger.error(f"Error handling follow-up message: {str(e)}")
            
            # Update status to FAILED
            await self.update_conversation_status(
                conversation_id=conversation_id, 
                status=ChatStatus.FAILED,
                message=f"Error processing query: {str(e)}"
            )
            
            # Return error response
            return ChatResponse(
                conversation_id=conversation_id,
                message=f"Error: {str(e)}",
                project_id=project_id,
                status=ChatStatus.FAILED
            )
    
    async def _create_and_execute_project(
        self,
        conversation_id: str,
        chat_request: ChatRequest,
        message_id: str
    ) -> ChatResponse:
        """Create and execute a project based on the chat request."""
        # Use the project_id that was generated in start_chat
        project_id = generate_short_id()
        
        try:
            # Update status to show we're creating a project
            await self.update_conversation_status(
                conversation_id=conversation_id, 
                status=ChatStatus.PLANNING,
                message="Creating project from query...",
                project_id=project_id
            )
        
            # Create a project
            project = await self.project_service.create_project_from_query(
                query=chat_request.query, 
                teams=["versatile"],  # Default to versatile team
                metadata={
                    "conversation_id": conversation_id,
                    "chat_request": chat_request.dict()
                },
                project_id=project_id
            )
            
            if project.project_id != project_id:
                logger.warning(f"Project ID changed from {project_id} to {project.project_id}")
                project_id = project.project_id
                    
            # Update status with correct project ID
            await self.update_conversation_status(
                conversation_id=conversation_id, 
                status=ChatStatus.PLANNING,
                message="Project created, preparing task execution...",
                project_id=project_id
            )
            
            # Store the project ID in the conversation
            conversation = self.conversations[conversation_id]
            conversation["project_id"] = project.project_id
            
            # Update status to EXECUTING
            await self.update_conversation_status(
                conversation_id=conversation_id, 
                status=ChatStatus.EXECUTING,
                message="Executing project tasks...",
                project_id=project_id
            )
        
            # Initialize TaskManager for the project
            logger.info(f"Initializing Project for execution: {project.project_id}")
            project_obj = ProjectManager.load(project.project_id)
            
            # Execute project tasks
            result = await project_obj.execute_tasks()
                
            # Get final project status
            project_details = await self.project_service.get_project_status(project.project_id)
            
            # Update status to COMPLETED
            await self.update_conversation_status(
                conversation_id=conversation_id, 
                status=ChatStatus.COMPLETED,
                message=f"Project '{project.name}' created and executed successfully",
                project_id=project.project_id,
                project_details=project_details,
                progress=project_details.get("progress", 100) if project_details else 100
            )
            
            # Add response to conversation history
            success_message = f"Project '{project.name}' created and executed successfully"
            conversation["messages"].append({
                "id": message_id,
                "role": MessageRole.ASSISTANT,
                "content": success_message,
                "timestamp": datetime.now().isoformat()
            })
        
            # Create chat response
            response = ChatResponse(
                conversation_id=conversation_id,
                project_id=project.id,
                message=success_message,
                project_details=project_details,
                status=ChatStatus.COMPLETED
            )
            
            return response
    
        except Exception as e:
            logger.error(f"Error creating/executing project: {str(e)}")
            
            # Update status to FAILED
            await self.update_conversation_status(
                conversation_id=conversation_id, 
                status=ChatStatus.FAILED,
                message=f"Error: {str(e)}",
                project_id=project_id
            )
            
            # Add error to conversation history
            conversation = self.conversations[conversation_id]
            conversation["messages"].append({
                "id": message_id,
                "role": MessageRole.ASSISTANT,
                "content": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            
            # Return error response
            return ChatResponse(
                conversation_id=conversation_id,
                project_id=project_id,
                message=f"Error: {str(e)}",
                status=ChatStatus.FAILED
            )
    
    async def get_conversation_status(self, conversation_id: str) -> Optional[MessageStatus]:
        """
        Get the current status of a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            MessageStatus object if found, None otherwise
        """
        status_data = self.conversation_statuses.get(conversation_id)
        if not status_data:
            return None
        
        # Ensure we have the required fields
        required_fields = ["conversation_id", "status", "message", "created_at", "updated_at"]
        for field in required_fields:
            if field not in status_data:
                logger.warning(f"Missing required field {field} in conversation status {conversation_id}")
                
                # Add missing required fields with defaults
                if field == "conversation_id":
                    status_data["conversation_id"] = conversation_id
                elif field == "status":
                    status_data["status"] = ChatStatus.PENDING
                elif field == "message":
                    status_data["message"] = "Conversation status"
                elif field == "created_at" or field == "updated_at":
                    status_data[field] = datetime.now().isoformat()
        
        return MessageStatus(**status_data)
    
    async def get_conversation_history(self, conversation_id: str) -> Optional[MessageHistory]:
        """
        Get the complete history of a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            MessageHistory object if found, None otherwise
        """
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return None
        
        # Get status information
        status = await self.get_conversation_status(conversation_id)
        if not status:
            logger.warning(f"No status found for conversation {conversation_id}")
            return None
        
        # Get files
        files = self.files.get(conversation_id, [])
        
        # Convert messages to Message objects
        # Ensure all messages have the required fields
        messages = []
        for msg in conversation.get("messages", []):
            # Ensure each message has all required fields
            if "id" not in msg:
                msg["id"] = generate_short_id()
            if "role" not in msg:
                msg["role"] = MessageRole.SYSTEM
            if "content" not in msg:
                msg["content"] = ""
            if "timestamp" not in msg:
                msg["timestamp"] = datetime.now().isoformat()
            
            messages.append(Message(**msg))
        
        # Create MessageHistory object
        history = MessageHistory(
            conversation_id=conversation_id,
            project_id=conversation.get("project_id"),
            created_at=conversation.get("created_at", datetime.now().isoformat()),
            updated_at=conversation.get("updated_at", datetime.now().isoformat()),
            title=conversation.get("title", f"Conversation {conversation_id}"),
            description=conversation.get("description", ""),
            status=status.status,
            messages=messages,
            files=files,
            progress=status.progress
        )
        
        return history
    
    async def update_conversation_status(
        self,
        conversation_id: str,
        status: Optional[ChatStatus] = None,
        message: Optional[str] = None,
        project_id: Optional[str] = None,
        project_details: Optional[Dict[str, Any]] = None,
        progress: Optional[float] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        files: Optional[List[Dict[str, Any]]] = None,
        active_task_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> MessageStatus:
        """
        Update the status of a conversation.
        
        Args:
            conversation_id: ID of the conversation
            status: New status
            message: Status message
            project_id: ID of the project associated with this conversation
            project_details: Additional project details
            progress: Progress percentage (0-100)
            messages: List of messages in the thread
            files: List of files created or modified in the thread
            active_task_id: ID of the currently active task
            title: Title of the message thread
            description: Description of the message thread
            labels: Labels/tags for the message thread
            
        Returns:
            Updated MessageStatus object
        """
        now = datetime.now().isoformat()
        
        # Get existing status data or create new
        status_data = self.conversation_statuses.get(conversation_id, {})
        
        # Update fields
        if not status_data:
            status_data = {
                "conversation_id": conversation_id,
                "created_at": now,
                "updated_at": now
            }
        else:
            status_data["updated_at"] = now
        
        # Update optional fields if provided
        if status is not None:
            status_data["status"] = status
        
        if message is not None:
            status_data["message"] = message
        
        if project_id is not None:
            status_data["project_id"] = project_id
        
        if project_details is not None:
            status_data["project_details"] = project_details
            
        if progress is not None:
            status_data["progress"] = progress
            
        if messages is not None:
            status_data["messages"] = messages
            
        if files is not None:
            status_data["files"] = files
            
        if active_task_id is not None:
            status_data["active_task_id"] = active_task_id
            
        if title is not None:
            status_data["title"] = title
            
        if description is not None:
            status_data["description"] = description
            
        if labels is not None:
            status_data["labels"] = labels
        
        # Ensure required fields are present
        if "status" not in status_data:
            status_data["status"] = ChatStatus.PENDING
            
        if "message" not in status_data:
            status_data["message"] = "Conversation started"
        
        # Store updated status
        self.conversation_statuses[conversation_id] = status_data
        
        # Log status update
        logger.info(f"Updated conversation status: {conversation_id} -> {status_data.get('status')}")
        
        return MessageStatus(**status_data)
    
    async def add_file(
        self,
        conversation_id: str,
        file_path: str,
        file_type: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a file to the conversation tracking.
        
        Args:
            conversation_id: ID of the conversation
            file_path: Path to the file
            file_type: Type of the file
            description: Optional description of the file
            metadata: Optional metadata
            
        Returns:
            ID of the file record
        """
        # Check if conversation exists
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Generate file ID
        file_id = generate_short_id()
        current_time = datetime.now().isoformat()
        
        # Create file record
        file_record = {
            "id": file_id,
            "path": file_path,
            "type": file_type,
            "description": description,
            "created_at": current_time,
            "updated_at": current_time,
            "metadata": metadata or {}
        }
        
        # Add file to files collection
        if conversation_id not in self.files:
            self.files[conversation_id] = []
            
        self.files[conversation_id].append(file_record)
        
        # Update conversation status with file
        await self.update_conversation_status(
            conversation_id=conversation_id,
            files=self.files[conversation_id]
        )
        
        # Create a system message about file creation
        await self.add_system_message(
            conversation_id=conversation_id,
            content=f"Added file: {file_path}",
            message_type=MessageType.TEXT,
            metadata={"file_id": file_id}
        )
        
        return file_id
    
    async def add_system_message(
        self,
        conversation_id: str,
        content: str,
        message_type: str = MessageType.TEXT,
        parent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a system message to the conversation.
        
        Args:
            conversation_id: ID of the conversation
            content: Message content
            message_type: Type of the message
            parent_id: Optional parent message ID
            task_id: Optional related task ID
            metadata: Optional metadata
            
        Returns:
            ID of the created message
        """
        # Check if conversation exists
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Generate message ID
        message_id = generate_short_id()
        current_time = datetime.now().isoformat()
        
        # Create message
        message = {
            "id": message_id,
            "role": MessageRole.SYSTEM,
            "content": content,
            "timestamp": current_time,
            "type": message_type,
            "parent_id": parent_id,
            "task_id": task_id,
            "meta": metadata or {}
        }
        
        # Add message to conversation
        self.conversations[conversation_id]["messages"].append(message)
        self.conversations[conversation_id]["updated_at"] = current_time
        
        return message_id
    
    async def add_assistant_message(
        self,
        conversation_id: str,
        content: str,
        message_type: str = MessageType.TEXT,
        parent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add an assistant message to the conversation.
        
        Args:
            conversation_id: ID of the conversation
            content: Message content
            message_type: Type of the message
            parent_id: Optional parent message ID
            task_id: Optional related task ID
            metadata: Optional metadata
            
        Returns:
            ID of the created message
        """
        # Check if conversation exists
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Generate message ID
        message_id = generate_short_id()
        current_time = datetime.now().isoformat()
        
        # Create message
        message = {
            "id": message_id,
            "role": MessageRole.ASSISTANT,
            "content": content,
            "timestamp": current_time,
            "type": message_type,
            "parent_id": parent_id,
            "task_id": task_id,
            "meta": metadata or {}
        }
        
        # Add message to conversation
        self.conversations[conversation_id]["messages"].append(message)
        self.conversations[conversation_id]["updated_at"] = current_time
        
        return message_id

    async def list_conversations(self, project_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List conversations, optionally filtered by project ID.
        
        Args:
            project_id: Optional project ID to filter by
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation summaries
        """
        conversations = []
        
        # Create a copy of the conversation list for thread safety
        conversation_ids = list(self.conversations.keys())
        
        # Process each conversation
        for conversation_id in conversation_ids:
            try:
                conversation = self.conversations.get(conversation_id)
                if not conversation:
                    continue
                
                # Skip if project_id filter is applied and doesn't match
                if project_id and conversation.get("project_id") != project_id:
                    continue
                
                # Create a summary of the conversation
                summary = {
                    "id": conversation_id,
                    "title": conversation.get("title", "Untitled Conversation"),
                    "created_at": conversation.get("created_at"),
                    "updated_at": conversation.get("updated_at"),
                    "project_id": conversation.get("project_id"),
                    "status": conversation.get("status", "pending"),
                    "message_count": len(conversation.get("messages", [])),
                    "labels": conversation.get("labels", [])
                }
                
                # Add the last message content if available
                if conversation.get("messages"):
                    last_message = conversation["messages"][-1]
                    summary["last_message"] = {
                        "role": last_message.get("role"),
                        "content": last_message.get("content"),
                        "timestamp": last_message.get("timestamp")
                    }
                
                conversations.append(summary)
            except Exception as e:
                logger.error(f"Error processing conversation {conversation_id}: {str(e)}")
        
        # Sort by updated_at (newest first)
        conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        # Limit the number of results
        return conversations[:limit]

    async def stop_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Stop a running conversation.
        
        This is a simplified implementation that just updates the status in memory.
        
        Args:
            conversation_id: ID of the conversation to stop
            
        Returns:
            Updated conversation status or None if not found
        """
        # Check if conversation exists
        if conversation_id not in self.conversations:
            return None
        
        # Update status to COMPLETED in memory
        await self.update_conversation_status(
            conversation_id=conversation_id,
            status=ChatStatus.COMPLETED,
            message="Conversation stopped by user"
        )
        
        # Get the updated status
        status = await self.get_conversation_status(conversation_id)
        if not status:
            return None
            
        # Return simplified status info
        return {
            "id": conversation_id,
            "status": status.status,
            "message": status.message,
            "project_id": status.project_id,
            "updated_at": status.updated_at
        }

    async def continue_project_chat(self, project_id: str, query: str) -> ChatResponse:
        """Continue a chat session for a specific project.
        
        Args:
            project_id: ID of the project to chat about
            query: The query to process
            
        Returns:
            Response with conversation ID and results
        """
        # Create a chat request from the query
        chat_request = ChatRequest(query=query)
        
        # Check if there's an existing conversation for this project
        conversation_id = None
        for conv_id, conv in self.conversations.items():
            if conv.get("project_id") == project_id:
                conversation_id = conv_id
                break
        
        if conversation_id:
            # Get the message ID for the user's message
            message_id = generate_short_id()
            
            # Add user message to conversation
            conversation = self.conversations[conversation_id]
            user_message = {
                "id": message_id,
                "role": MessageRole.USER,
                "content": query,
                "timestamp": datetime.now().isoformat(),
                "type": MessageType.TEXT
            }
            conversation["messages"].append(user_message)
            conversation["updated_at"] = datetime.now().isoformat()
            
            # Process the follow-up message
            return await self._handle_follow_up_message(conversation_id, chat_request, message_id)
        else:
            # If no existing conversation, create a new one and link it to the project
            response = await self.start_chat(chat_request)
            
            # Link the conversation to the project
            if response.conversation_id and response.conversation_id in self.conversations:
                self.conversations[response.conversation_id]["project_id"] = project_id
                
            return response
