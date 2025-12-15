"""
Translation model for storing entity translations in database
"""
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class Translation(Base):
    """
    Generic translation table for any entity
    Stores translations for products, categories, modifiers, etc.
    """
    __tablename__ = "translations"
    
    id = Column(String(36), primary_key=True)
    restaurant_id = Column(String(36), nullable=False, index=True)  # Added for multi-tenancy
    entity_type = Column(String(50), nullable=False)  # 'product', 'category', 'modifier', etc.
    entity_id = Column(String(36), nullable=False)    # ID of the entity
    field_name = Column(String(50), nullable=False)   # 'name', 'description', etc.
    language_code = Column(String(5), nullable=False) # 'en', 'es', 'fr', 'ar'
    translation_value = Column(String(1000), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Indexes for better performance
    __table_args__ = (
        Index('idx_restaurant_entity', 'restaurant_id', 'entity_type', 'entity_id'),
        Index('idx_language', 'language_code'),
        Index('idx_unique_translation', 'restaurant_id', 'entity_type', 'entity_id', 'field_name', 'language_code', unique=True)
    )
    
    def __repr__(self):
        return f"<Translation {self.entity_type}.{self.entity_id}.{self.field_name}[{self.language_code}] restaurant_id={self.restaurant_id}>"
