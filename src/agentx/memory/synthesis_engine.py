"""
Memory Synthesis Engine

The intelligent core of the Memory System that analyzes events and creates
structured memories (Constraints, Hot Issues, Document Chunks) as specified
in the architecture document.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

from .types import Memory, Constraint, HotIssue, DocumentChunk, MemoryType, MemoryItem
from .backend import MemoryBackend
from ..event.types import Event
# Brain import will be handled at runtime to avoid circular dependency
from ..utils.logger import get_logger

# Import Brain at runtime to avoid circular dependency
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..core.brain import Brain

logger = get_logger(__name__)


class MemorySynthesisEngine:
    """
    The logical core of the Memory System that analyzes events and creates memories.
    
    Implements the event-driven analysis logic specified in the architecture:
    - Analyzes user messages for constraints/preferences
    - Detects tool failures and creates hot issues
    - Resolves hot issues when tools succeed
    - Chunks document content for semantic search
    """
    
    def __init__(self, memory_backend: MemoryBackend, brain: Optional['Brain'] = None):
        self.backend = memory_backend
        self.brain = brain  # For LLM-powered constraint analysis
        self._constraint_patterns = self._build_constraint_patterns()
        self._quality_tools = {"run_tests", "linter", "quality_analyzer", "fact_checker"}
        
        logger.info("MemorySynthesisEngine initialized")
    
    def _build_constraint_patterns(self) -> List[str]:
        """Build regex patterns that indicate user constraints."""
        return [
            r"never\s+(?:use|create|do|mention)",
            r"always\s+(?:use|include|add|remember)",
            r"don't\s+(?:use|create|generate)",
            r"make sure\s+to\s+(?:use|include|add)",
            r"(?:prefer|use)\s+\w+\s+(?:instead of|rather than)",
            r"for\s+now,?\s+(?:don't|avoid|skip)",
            r"(?:requirement|rule|constraint|policy):",
            r"(?:citation\s+style|format|standard):\s*\w+",
        ]
    
    async def on_event(self, event: Event) -> None:
        """
        Main event handler - routes events to appropriate analysis methods.
        
        This implements the event handling logic from the architecture document.
        """
        try:
            event_data = event.data
            event_type = getattr(event_data, 'type', event_data.__class__.__name__)
            
            logger.debug(f"Processing event: {event_type}")
            
            # Route by event type as specified in architecture
            if event_type == "event_user_message" or hasattr(event_data, 'role') and event_data.role == 'user':
                await self._handle_user_message_event(event_data, event.metadata.event_id)
            
            elif event_type == "event_tool_result" or hasattr(event_data, 'tool_name'):
                await self._handle_tool_result_event(event_data, event.metadata.event_id)
            
            elif event_type == "event_artifact_created" or event_type == "artifact_created":
                await self._handle_artifact_event(event_data, event.metadata.event_id)
                
        except Exception as e:
            logger.error(f"Error processing event in synthesis engine: {e}")
    
    async def _handle_user_message_event(self, event_data: Any, event_id: str) -> None:
        """
        Analyze user messages for constraints and preferences.
        
        Implements the constraint extraction logic from the architecture document.
        """
        try:
            # Extract message text
            message_text = getattr(event_data, 'content', '') or getattr(event_data, 'text', '') or str(event_data)
            
            if not message_text or len(message_text.strip()) < 10:
                return
            
            # First, check for obvious constraint patterns
            constraint_found = await self._detect_constraint_patterns(message_text)
            
            if constraint_found:
                await self._create_constraint_memory(constraint_found, event_id)
                return
            
            # If we have a brain (LLM), use intelligent analysis
            if self.brain:
                await self._analyze_message_with_llm(message_text, event_id)
            
        except Exception as e:
            logger.error(f"Error handling user message event: {e}")
    
    async def _detect_constraint_patterns(self, message_text: str) -> Optional[str]:
        """Detect constraints using regex patterns."""
        message_lower = message_text.lower()
        
        for pattern in self._constraint_patterns:
            if re.search(pattern, message_lower):
                # Extract the constraint from context
                sentences = message_text.split('.')
                for sentence in sentences:
                    if re.search(pattern, sentence.lower()):
                        return sentence.strip()
        
        return None
    
    async def _analyze_message_with_llm(self, message_text: str, event_id: str) -> None:
        """Use LLM to analyze message for constraints."""
        try:
            prompt = f"""Does the following user message contain a persistent rule, constraint, or preference for an AI assistant? If so, state the rule clearly in a single imperative sentence. If not, respond with 'N/A'.

User Message: "{message_text}"

Rule (if any):"""

            response = await self.brain.generate_response_async(prompt)
            
            if response and response.strip().upper() != 'N/A':
                await self._create_constraint_memory(response.strip(), event_id)
                
        except Exception as e:
            logger.warning(f"LLM constraint analysis failed: {e}")
    
    async def _create_constraint_memory(self, constraint_text: str, event_id: str) -> None:
        """Create a constraint memory object."""
        try:
            constraint = Constraint(
                content=constraint_text,
                source_event_id=event_id,
                agent_name="user",
                metadata={
                    "extracted_at": datetime.now().isoformat(),
                    "extraction_method": "synthesis_engine"
                }
            )
            
            # Convert to MemoryItem for backend storage
            memory_item = MemoryItem(
                memory_id=str(constraint.id),
                content=constraint.content,
                agent_name=constraint.agent_name,
                timestamp=constraint.timestamp,
                memory_type=MemoryType.CONSTRAINT,
                metadata=constraint.metadata,
                importance=constraint.importance,
                source_event_id=event_id,
                is_active=constraint.is_active
            )
            
            await self.backend.add(
                content=memory_item.content,
                memory_type=memory_item.memory_type,
                agent_name=memory_item.agent_name,
                metadata=memory_item.metadata,
                importance=memory_item.importance
            )
            
            logger.info(f"Created constraint memory: {constraint_text[:100]}...")
            
        except Exception as e:
            logger.error(f"Error creating constraint memory: {e}")
    
    async def _handle_tool_result_event(self, event_data: Any, event_id: str) -> None:
        """
        Handle tool execution results - create/resolve hot issues.
        
        Implements the hot issue tracking logic from the architecture document.
        """
        try:
            tool_name = getattr(event_data, 'tool_name', '')
            success = getattr(event_data, 'success', True)
            result = getattr(event_data, 'result', '')
            
            if not tool_name:
                return
            
            if not success and tool_name in self._quality_tools:
                # Create hot issue for failed quality tools
                await self._create_hot_issue(tool_name, result, event_id)
            
            elif success and tool_name in self._quality_tools:
                # Resolve related hot issues
                await self._resolve_hot_issues(tool_name, event_id)
                
        except Exception as e:
            logger.error(f"Error handling tool result event: {e}")
    
    async def _create_hot_issue(self, tool_name: str, error_result: str, event_id: str) -> None:
        """Create a hot issue memory for a failed tool."""
        try:
            issue_content = f"Tool '{tool_name}' failed: {str(error_result)[:200]}"
            
            hot_issue = HotIssue(
                content=issue_content,
                source_event_id=event_id,
                agent_name="system",
                metadata={
                    "tool_name": tool_name,
                    "error_details": str(error_result),
                    "created_at": datetime.now().isoformat()
                }
            )
            
            # Convert to MemoryItem for backend storage
            memory_item = MemoryItem(
                memory_id=str(hot_issue.id),
                content=hot_issue.content,
                agent_name=hot_issue.agent_name,
                timestamp=hot_issue.timestamp,
                memory_type=MemoryType.HOT_ISSUE,
                metadata=hot_issue.metadata,
                importance=2.0,  # Hot issues are high importance
                source_event_id=event_id,
                is_active=hot_issue.is_active
            )
            
            await self.backend.add(
                content=memory_item.content,
                memory_type=memory_item.memory_type,
                agent_name=memory_item.agent_name,
                metadata=memory_item.metadata,
                importance=memory_item.importance
            )
            
            logger.warning(f"Created hot issue: {issue_content}")
            
        except Exception as e:
            logger.error(f"Error creating hot issue: {e}")
    
    async def _resolve_hot_issues(self, tool_name: str, event_id: str) -> None:
        """Resolve hot issues related to a successful tool execution."""
        try:
            # Search for active hot issues related to this tool
            from .types import MemoryQuery
            
            query = MemoryQuery(
                query=f"tool '{tool_name}' failed",
                memory_type=MemoryType.HOT_ISSUE,
                metadata_filter={"tool_name": tool_name},
                limit=10
            )
            
            results = await self.backend.search(query)
            
            for item in results.items:
                if item.is_active:
                    # Mark as resolved
                    await self.backend.update(
                        item.memory_id,
                        is_active=False,
                        resolved_by_event_id=event_id,
                        resolved_at=datetime.now().isoformat()
                    )
                    
                    logger.info(f"Resolved hot issue: {item.content[:100]}...")
                    
        except Exception as e:
            logger.error(f"Error resolving hot issues: {e}")
    
    async def _handle_artifact_event(self, event_data: Any, event_id: str) -> None:
        """
        Handle artifact creation - chunk content for semantic search.
        
        Implements the document chunking logic from the architecture document.
        """
        try:
            file_path = getattr(event_data, 'file_path', '') or getattr(event_data, 'path', '')
            content = getattr(event_data, 'content', '')
            
            if not file_path or not content:
                return
            
            # Only chunk text files
            if not self._is_text_file(file_path):
                return
            
            await self._chunk_and_store_content(content, file_path, event_id)
            
        except Exception as e:
            logger.error(f"Error handling artifact event: {e}")
    
    def _is_text_file(self, file_path: str) -> bool:
        """Check if file should be chunked for semantic search."""
        text_extensions = {'.md', '.txt', '.py', '.js', '.ts', '.yaml', '.yml', '.json', '.html', '.css'}
        return Path(file_path).suffix.lower() in text_extensions
    
    async def _chunk_and_store_content(self, content: str, file_path: str, event_id: str) -> None:
        """Chunk content and store as document chunk memories."""
        try:
            chunks = self._chunk_content(content)
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:  # Skip very small chunks
                    continue
                
                doc_chunk = DocumentChunk(
                    content=chunk,
                    source_file_path=file_path,
                    chunk_index=i,
                    source_event_id=event_id,
                    agent_name="system",
                    metadata={
                        "file_path": file_path,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk)
                    }
                )
                
                # Convert to MemoryItem for backend storage
                memory_item = MemoryItem(
                    memory_id=str(doc_chunk.id),
                    content=doc_chunk.content,
                    agent_name=doc_chunk.agent_name,
                    timestamp=doc_chunk.timestamp,
                    memory_type=MemoryType.DOCUMENT_CHUNK,
                    metadata=doc_chunk.metadata,
                    importance=1.0,
                    source_event_id=event_id,
                    is_active=doc_chunk.is_active
                )
                
                await self.backend.add(
                    content=memory_item.content,
                    memory_type=memory_item.memory_type,
                    agent_name=memory_item.agent_name,
                    metadata=memory_item.metadata,
                    importance=memory_item.importance
                )
            
            logger.debug(f"Chunked and stored {len(chunks)} pieces from {file_path}")
            
        except Exception as e:
            logger.error(f"Error chunking content: {e}")
    
    def _chunk_content(self, content: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """Split content into overlapping chunks for semantic search."""
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence endings near the chunk boundary
                for i in range(end, max(start + chunk_size - 100, start), -1):
                    if content[i] in '.!?\n':
                        end = i + 1
                        break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(content):
                break
        
        return chunks
    
    async def get_relevant_context(self, last_user_message: str, agent_name: str = None) -> str:
        """
        Get relevant context for injection into agent prompts.
        
        This implements the context retrieval logic from the architecture document.
        """
        try:
            # 1. Fetch active rules (constraints and hot issues)
            active_rules = await self._get_active_rules()
            
            # 2. Perform semantic search on document chunks
            from .types import MemoryQuery
            
            doc_query = MemoryQuery(
                query=last_user_message,
                memory_type=MemoryType.DOCUMENT_CHUNK,
                agent_name=agent_name,
                limit=5
            )
            
            doc_results = await self.backend.search(doc_query)
            
            # 3. Format for prompt injection
            return self._format_context_for_prompt(active_rules, doc_results.items)
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return ""
    
    async def _get_active_rules(self) -> List[MemoryItem]:
        """Get all active constraints and hot issues."""
        active_rules = []
        
        try:
            # Get active constraints
            from .types import MemoryQuery
            
            constraint_query = MemoryQuery(
                query="*",  # Get all
                memory_type=MemoryType.CONSTRAINT,
                limit=20
            )
            
            constraint_results = await self.backend.search(constraint_query)
            active_rules.extend([item for item in constraint_results.items if item.is_active])
            
            # Get active hot issues
            issue_query = MemoryQuery(
                query="*",  # Get all
                memory_type=MemoryType.HOT_ISSUE,
                limit=20
            )
            
            issue_results = await self.backend.search(issue_query)
            active_rules.extend([item for item in issue_results.items if item.is_active])
            
        except Exception as e:
            logger.error(f"Error getting active rules: {e}")
        
        return active_rules
    
    def _format_context_for_prompt(self, active_rules: List[MemoryItem], doc_chunks: List[MemoryItem]) -> str:
        """
        Format retrieved memories for prompt injection.
        
        Implements the context formatting from the architecture document.
        """
        if not active_rules and not doc_chunks:
            return ""
        
        context_parts = ["CONTEXT:", "---"]
        
        # Add active rules and issues
        if active_rules:
            context_parts.append("ACTIVE RULES AND ISSUES:")
            for rule in active_rules:
                rule_type = "Constraint" if rule.memory_type == MemoryType.CONSTRAINT else "Hot Issue"
                context_parts.append(f"- [{rule_type}] {rule.content}")
            context_parts.append("")
        
        # Add relevant document snippets
        if doc_chunks:
            context_parts.append("RELEVANT DOCUMENT SNIPPETS:")
            for chunk in doc_chunks:
                file_path = chunk.metadata.get('file_path', 'unknown')
                snippet = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                context_parts.append(f"- [Source: {file_path}] {snippet}")
            context_parts.append("")
        
        context_parts.append("---")
        
        return "\n".join(context_parts) 