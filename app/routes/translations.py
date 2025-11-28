"""
Translation API routes
Serves UI translations and manages entity translations
"""
from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import uuid
from typing import Dict, Any, Optional

from app.database import get_db

router = APIRouter(prefix="/api/v1/translations", tags=["translations"])

TRANSLATIONS_DIR = Path(__file__).parent.parent / "translations"
SUPPORTED_LANGUAGES = ["en", "es", "fr", "ar"]


@router.get("/languages")
def get_supported_languages():
    """Get list of supported languages"""
    return {
        "success": True,
        "data": [
            {
                "code": "en",
                "name": "English",
                "native_name": "English",
                "rtl": False
            },
            {
                "code": "es",
                "name": "Spanish",
                "native_name": "Español",
                "rtl": False
            },
            {
                "code": "fr",
                "name": "French",
                "native_name": "Français",
                "rtl": False
            },
            {
                "code": "ar",
                "name": "Arabic",
                "native_name": "العربية",
                "rtl": True
            }
        ],
        "default_language": "en"
    }


@router.get("/{language}")
def get_translations(language: str) -> Dict[str, Any]:
    """Get all translations for a specific language"""
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language. Supported: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    
    file_path = TRANSLATIONS_DIR / f"{language}.json"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Translation file not found for language: {language}"
        )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        return {
            "success": True,
            "language": language,
            "translations": translations
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading translations: {str(e)}"
        )


# Entity Translation Management
class TranslationCreate(BaseModel):
    entity_type: str
    entity_id: str
    field_name: str
    language_code: str
    translation_value: str


@router.post("/entity")
def add_translation(
    translation: TranslationCreate,
    db: Session = Depends(get_db)
):
    """Add or update translation for any entity"""
    from app.models.translation import Translation
    
    # Check if translation exists
    existing = db.query(Translation).filter(
        Translation.entity_type == translation.entity_type,
        Translation.entity_id == translation.entity_id,
        Translation.field_name == translation.field_name,
        Translation.language_code == translation.language_code
    ).first()
    
    if existing:
        # Update
        existing.translation_value = translation.translation_value
        db.commit()
        db.refresh(existing)
        return {
            "success": True,
            "message": "Translation updated successfully",
            "data": {
                "id": existing.id,
                "entity_type": existing.entity_type,
                "entity_id": existing.entity_id,
                "field_name": existing.field_name,
                "language_code": existing.language_code,
                "translation_value": existing.translation_value
            }
        }
    else:
        # Create
        new_translation = Translation(
            id=str(uuid.uuid4()),
            **translation.dict()
        )
        db.add(new_translation)
        db.commit()
        db.refresh(new_translation)
        return {
            "success": True,
            "message": "Translation created successfully",
            "data": {
                "id": new_translation.id,
                "entity_type": new_translation.entity_type,
                "entity_id": new_translation.entity_id,
                "field_name": new_translation.field_name,
                "language_code": new_translation.language_code,
                "translation_value": new_translation.translation_value
            }
        }


@router.get("/entity/{entity_type}/{entity_id}")
def get_entity_translations(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Get all translations for an entity"""
    from app.models.translation import Translation
    
    translations = db.query(Translation).filter(
        Translation.entity_type == entity_type,
        Translation.entity_id == entity_id
    ).all()
    
    # Group by language
    result = {}
    for t in translations:
        if t.language_code not in result:
            result[t.language_code] = {}
        result[t.language_code][t.field_name] = t.translation_value
    
    return {
        "success": True,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "data": result
    }


@router.delete("/entity/{entity_type}/{entity_id}/{field_name}/{language_code}")
def delete_translation(
    entity_type: str,
    entity_id: str,
    field_name: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """Delete a specific translation"""
    from app.models.translation import Translation
    
    translation = db.query(Translation).filter(
        Translation.entity_type == entity_type,
        Translation.entity_id == entity_id,
        Translation.field_name == field_name,
        Translation.language_code == language_code
    ).first()
    
    if not translation:
        raise HTTPException(
            status_code=404,
            detail="Translation not found"
        )
    
    db.delete(translation)
    db.commit()
    
    return {
        "success": True,
        "message": "Translation deleted successfully"
    }
