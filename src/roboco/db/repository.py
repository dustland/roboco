"""
Generic Repository Pattern Implementation

This module provides a generic repository pattern implementation that can be used
for any SQLModel model type. It provides basic CRUD operations and serves as a
base class for specialized repositories.
"""

from typing import List, Optional, Dict, Any, TypeVar, Generic, Type
from sqlmodel import Session, select
from datetime import datetime

# Type variable for models
T = TypeVar('T')


class GenericRepository(Generic[T]):
    """
    Generic repository for database operations on a specific model type.
    
    This class implements common database operations for any model type
    using SQLModel, and serves as a base class for specialized repositories.
    """
    
    def __init__(self, session: Session, model_class: Type[T]):
        """
        Initialize the repository with a database session and model class.
        
        Args:
            session: SQLModel session for database operations
            model_class: Class of the model this repository operates on
        """
        self.session = session
        self.model_class = model_class
    
    def get(self, entity_id: str) -> Optional[T]:
        """
        Get an entity by its ID.
        
        Args:
            entity_id: ID of the entity to retrieve
            
        Returns:
            Entity if found, None otherwise
        """
        return self.session.get(self.model_class, entity_id)
    
    def get_all(self) -> List[T]:
        """
        Get all entities of this type.
        
        Returns:
            List of all entities
        """
        statement = select(self.model_class)
        return self.session.exec(statement).all()
    
    def create(self, entity_data: Dict[str, Any]) -> T:
        """
        Create a new entity.
        
        Args:
            entity_data: Dictionary of fields to create the entity with
            
        Returns:
            Created entity
        """
        entity = self.model_class(**entity_data)
        self.session.add(entity)
        self.session.flush()
        return entity
    
    def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[T]:
        """
        Update an entity.
        
        Args:
            entity_id: ID of the entity to update
            update_data: Dictionary of fields to update
            
        Returns:
            Updated entity if found, None otherwise
        """
        entity = self.get(entity_id)
        if not entity:
            return None
            
        # Update fields
        for key, value in update_data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        # Update timestamp if the entity has one
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.utcnow()
            
        self.session.add(entity)
        self.session.flush()
        return entity
    
    def delete(self, entity_id: str) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            True if entity was deleted, False if not found
        """
        entity = self.get(entity_id)
        if not entity:
            return False
            
        self.session.delete(entity)
        self.session.flush()
        return True 