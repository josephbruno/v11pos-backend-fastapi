"""
Multi-language support utilities
"""
from typing import Optional, Any, List
from fastapi import Header


# Supported languages
SUPPORTED_LANGUAGES = ["en", "ta", "hi", "fr"]
DEFAULT_LANGUAGE = "en"


def get_language_from_header(accept_language: Optional[str] = Header(None, alias="Accept-Language")) -> str:
    """
    Extract language code from Accept-Language header
    
    Args:
        accept_language: Accept-Language header value
        
    Returns:
        Language code (en, ta, hi, fr)
    """
    if not accept_language:
        return DEFAULT_LANGUAGE
    
    # Parse Accept-Language header (e.g., "ta,en;q=0.9")
    lang_code = accept_language.split(",")[0].split(";")[0].strip().lower()
    
    # Extract just the language part (e.g., "ta" from "ta-IN")
    lang_code = lang_code.split("-")[0]
    
    # Return if supported, otherwise default
    return lang_code if lang_code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def get_translated_field(entity: Any, field_name: str, language: str = DEFAULT_LANGUAGE) -> Optional[str]:
    """
    Get translated field value for an entity
    
    Args:
        entity: Database entity with translations relationship
        field_name: Field name to translate (name, description)
        language: Language code
        
    Returns:
        Translated value or default value
    """
    if not hasattr(entity, 'translations'):
        # No translations, return default field
        return getattr(entity, field_name, None)
    
    # Try to find translation for requested language
    translation = next(
        (t for t in entity.translations if t.language_code == language),
        None
    )
    
    if translation and hasattr(translation, field_name):
        return getattr(translation, field_name)
    
    # Fallback to default field
    return getattr(entity, field_name, None)


def apply_translations(entity: Any, language: str = DEFAULT_LANGUAGE) -> dict:
    """
    Apply translations to entity and return as dict
    
    Args:
        entity: Database entity with translations
        language: Language code
        
    Returns:
        Dictionary with translated fields
    """
    result = {}
    
    # Copy all non-relationship fields
    for key, value in entity.__dict__.items():
        if not key.startswith('_'):
            result[key] = value
    
    # Override with translations if available
    if hasattr(entity, 'translations'):
        translation = next(
            (t for t in entity.translations if t.language_code == language),
            None
        )
        
        if translation:
            # Override translatable fields
            if hasattr(translation, 'name'):
                result['name'] = translation.name
            if hasattr(translation, 'description'):
                result['description'] = translation.description
    
    return result


def get_translation_dict(entity: Any) -> dict:
    """
    Get all translations as a dictionary
    
    Args:
        entity: Database entity with translations
        
    Returns:
        Dictionary with language codes as keys
    """
    if not hasattr(entity, 'translations'):
        return {}
    
    translations = {}
    for trans in entity.translations:
        lang_data = {
            'language_code': trans.language_code
        }
        if hasattr(trans, 'name'):
            lang_data['name'] = trans.name
        if hasattr(trans, 'description'):
            lang_data['description'] = trans.description
        
        translations[trans.language_code] = lang_data
    
    return translations
