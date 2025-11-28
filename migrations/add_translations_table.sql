-- Migration: Add translations table
-- Description: Creates table for storing entity translations
-- Date: 2024

-- Create translations table
CREATE TABLE IF NOT EXISTS translations (
    id VARCHAR(36) PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL COMMENT 'Type of entity: product, category, modifier, etc.',
    entity_id VARCHAR(36) NOT NULL COMMENT 'ID of the entity being translated',
    field_name VARCHAR(50) NOT NULL COMMENT 'Field being translated: name, description, etc.',
    language_code VARCHAR(5) NOT NULL COMMENT 'Language code: en, es, fr, ar',
    translation_value VARCHAR(1000) NOT NULL COMMENT 'Translated text',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_entity_lookup (entity_type, entity_id),
    INDEX idx_language (language_code),
    
    -- Ensure uniqueness: one translation per entity/field/language combination
    UNIQUE KEY idx_unique_translation (entity_type, entity_id, field_name, language_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stores translations for all entities';

-- Example: Add Spanish translation for a product
-- INSERT INTO translations (id, entity_type, entity_id, field_name, language_code, translation_value)
-- VALUES (UUID(), 'product', 'product-id-here', 'name', 'es', 'Nombre del Producto');

-- Example: Add French description for a category
-- INSERT INTO translations (id, entity_type, entity_id, field_name, language_code, translation_value)
-- VALUES (UUID(), 'category', 'category-id-here', 'description', 'fr', 'Description de la catégorie');

-- Query to see all translations for a product:
-- SELECT * FROM translations WHERE entity_type = 'product' AND entity_id = 'your-product-id';

-- Query to see all Spanish translations:
-- SELECT * FROM translations WHERE language_code = 'es';
