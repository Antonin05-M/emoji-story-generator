-- ============================================
-- Emoji Story Generator - Schéma PostgreSQL
-- ============================================

-- Base dédiée à n8n (tables internes séparées des tables métier)
CREATE DATABASE n8n_db;
GRANT ALL PRIVILEGES ON DATABASE n8n_db TO emoji_user;

-- Tables métier (dans emoji_db)
CREATE TABLE IF NOT EXISTS stories (
    id VARCHAR(36) PRIMARY KEY,
    emojis TEXT[] NOT NULL,
    theme VARCHAR(255),
    story_text TEXT,
    audio_url VARCHAR(255),
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS custom_emojis (
    id SERIAL PRIMARY KEY,
    emoji VARCHAR(10) UNIQUE NOT NULL,
    category VARCHAR(50) DEFAULT 'custom',
    added_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS story_history (
    id SERIAL PRIMARY KEY,
    story_id VARCHAR(36) REFERENCES stories(id) ON DELETE CASCADE,
    event VARCHAR(50) NOT NULL,
    detail TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);
CREATE INDEX IF NOT EXISTS idx_stories_created ON stories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_history_story ON story_history(story_id);
