"""
Internationalization (i18n) helper functions
Provides utilities for translation and language handling
"""
from typing import Any, Dict, Optional
from fastapi import Request
from sqlalchemy.orm import Session


def extract_language_from_header(request: Request) -> str:
    """
    Extract language code from Accept-Language header
    Falls back to 'en' if not provided or invalid
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Language code (e.g., 'en', 'es', 'fr', 'ar')
    """
    accept_language = request.headers.get("Accept-Language", "en")
    
    # Parse first language from Accept-Language header
    # Format: "en-US,en;q=0.9,es;q=0.8"
    language_code = accept_language.split(",")[0].split("-")[0].strip()
    
    # Validate against supported languages
    supported_languages = ["en", "es", "fr", "ar"]
    if language_code not in supported_languages:
        language_code = "en"  # Default to English
    
    return language_code


def get_translated_field(
    db: Session,
    entity_type: str,
    entity_id: str,
    field_name: str,
    language_code: str,
    default_value: str
) -> str:
    """
    Get translated value for an entity field
    Falls back to default_value if translation not found
    
    Args:
        db: Database session
        entity_type: Type of entity (e.g., 'product', 'category', 'modifier')
        entity_id: ID of the entity
        field_name: Name of the field to translate (e.g., 'name', 'description')
        language_code: Language code (e.g., 'en', 'es')
        default_value: Value to return if translation not found
        
    Returns:
        Translated value or default_value
    """
    from app.models.translation import Translation
    
    # If requesting English, return default
    if language_code == "en":
        return default_value
    
    # Query translation
    translation = db.query(Translation).filter(
        Translation.entity_type == entity_type,
        Translation.entity_id == entity_id,
        Translation.field_name == field_name,
        Translation.language_code == language_code
    ).first()
    
    if translation:
        return translation.translation_value
    
    # Fallback to default
    return default_value


def translate_entity(
    db: Session,
    entity: Any,
    language_code: str,
    entity_type: str,
    translatable_fields: list[str]
) -> Dict[str, Any]:
    """
    Translate all specified fields of an entity
    Returns dict with original fields plus translations
    
    Args:
        db: Database session
        entity: SQLAlchemy model instance
        language_code: Language code (e.g., 'en', 'es')
        entity_type: Type of entity (e.g., 'product', 'category')
        translatable_fields: List of field names to translate
        
    Returns:
        Dictionary with translated fields
    """
    result = {
        field: getattr(entity, field)
        for field in translatable_fields
    }
    
    # If not English, get translations
    if language_code != "en":
        for field in translatable_fields:
            original_value = getattr(entity, field, "")
            translated_value = get_translated_field(
                db=db,
                entity_type=entity_type,
                entity_id=entity.id,
                field_name=field,
                language_code=language_code,
                default_value=original_value
            )
            result[field] = translated_value
    
    return result


def translate_entity_list(
    db: Session,
    entities: list[Any],
    language_code: str,
    entity_type: str,
    translatable_fields: list[str]
) -> list[Dict[str, Any]]:
    """
    Translate multiple entities at once
    More efficient than calling translate_entity in a loop
    
    Args:
        db: Database session
        entities: List of SQLAlchemy model instances
        language_code: Language code (e.g., 'en', 'es')
        entity_type: Type of entity (e.g., 'product', 'category')
        translatable_fields: List of field names to translate
        
    Returns:
        List of dictionaries with translated fields
    """
    from app.models.translation import Translation
    
    # If English, just return original values
    if language_code == "en":
        return [
            {field: getattr(entity, field) for field in translatable_fields}
            for entity in entities
        ]
    
    # Get all entity IDs
    entity_ids = [entity.id for entity in entities]
    
    # Batch fetch all translations
    translations = db.query(Translation).filter(
        Translation.entity_type == entity_type,
        Translation.entity_id.in_(entity_ids),
        Translation.field_name.in_(translatable_fields),
        Translation.language_code == language_code
    ).all()
    
    # Build translation lookup dictionary
    translation_map = {}
    for t in translations:
        key = (t.entity_id, t.field_name)
        translation_map[key] = t.translation_value
    
    # Apply translations
    result = []
    for entity in entities:
        entity_dict = {}
        for field in translatable_fields:
            original_value = getattr(entity, field, "")
            key = (entity.id, field)
            entity_dict[field] = translation_map.get(key, original_value)
        result.append(entity_dict)
    
    return result


def get_rtl_languages() -> list[str]:
    """
    Get list of right-to-left languages
    
    Returns:
        List of RTL language codes
    """
    return ["ar", "he", "fa", "ur"]


def is_rtl_language(language_code: str) -> bool:
    """
    Check if a language is right-to-left
    
    Args:
        language_code: Language code to check
        
    Returns:
        True if language is RTL, False otherwise
    """
    return language_code in get_rtl_languages()


def create_entity_translations(
    db: Session,
    entity_type: str,
    entity_id: str,
    translations: Dict[str, Dict[str, str]]
) -> None:
    """
    Create multiple translations for an entity
    Used when creating new entities with translations
    
    Args:
        db: Database session
        entity_type: Type of entity (product, category, modifier, combo)
        entity_id: ID of the entity
        translations: Dict with structure: 
                     {"es": {"name": "...", "description": "..."}, "fr": {...}}
    
    Example:
        create_entity_translations(
            db=db,
            entity_type="product",
            entity_id="product-123",
            translations={
                "es": {"name": "Hamburguesa", "description": "Deliciosa"},
                "fr": {"name": "Hamburger", "description": "Délicieux"}
            }
        )
    """
    if not translations:
        return
    
    import uuid
    from app.models.translation import Translation
    
    for language_code, fields in translations.items():
        for field_name, translation_value in fields.items():
            if translation_value:  # Only create if value is not empty
                db_translation = Translation(
                    id=str(uuid.uuid4()),
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_name=field_name,
                    language_code=language_code,
                    translation_value=translation_value
                )
                db.add(db_translation)
    
    db.commit()


def update_entity_translations(
    db: Session,
    entity_type: str,
    entity_id: str,
    translations: Dict[str, Dict[str, str]]
) -> None:
    """
    Update or create translations for an entity
    Used when updating entities - updates existing translations or creates new ones
    
    Args:
        db: Database session
        entity_type: Type of entity
        entity_id: ID of the entity
        translations: Dict with translations to update/create
    
    Example:
        update_entity_translations(
            db=db,
            entity_type="category",
            entity_id="cat-456",
            translations={
                "es": {"name": "Nuevo Nombre"}
            }
        )
    """
    if not translations:
        return
    
    import uuid
    from app.models.translation import Translation
    
    for language_code, fields in translations.items():
        for field_name, translation_value in fields.items():
            if translation_value:
                # Check if translation exists
                existing = db.query(Translation).filter(
                    Translation.entity_type == entity_type,
                    Translation.entity_id == entity_id,
                    Translation.field_name == field_name,
                    Translation.language_code == language_code
                ).first()
                
                if existing:
                    # Update existing translation
                    existing.translation_value = translation_value
                else:
                    # Create new translation
                    db_translation = Translation(
                        id=str(uuid.uuid4()),
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field_name=field_name,
                        language_code=language_code,
                        translation_value=translation_value
                    )
                    db.add(db_translation)
    
    db.commit()


def delete_entity_translations(
    db: Session,
    entity_type: str,
    entity_id: str
) -> int:
    """
    Delete all translations for an entity
    Used when deleting entities to clean up translation records
    
    Args:
        db: Database session
        entity_type: Type of entity
        entity_id: ID of the entity
        
    Returns:
        Number of translations deleted
    
    Example:
        deleted_count = delete_entity_translations(
            db=db,
            entity_type="product",
            entity_id="product-789"
        )
    """
    from app.models.translation import Translation
    
    deleted_count = db.query(Translation).filter(
        Translation.entity_type == entity_type,
        Translation.entity_id == entity_id
    ).delete()
    
    db.commit()
    return deleted_count
