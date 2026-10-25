"""Modèles de données (Pydantic) - Emoji Story Generator"""
from pydantic import BaseModel, Field
from typing import Optional


class EmojiStoryRequest(BaseModel):
    """Requête de création d'histoire : 10 émoticônes ordonnés + thème libre"""
    emojis: list[str] = Field(..., min_length=10, max_length=10)
    theme: Optional[str] = Field(None, max_length=100)


class EmojiAddRequest(BaseModel):
    """Ajout d'un émoticône personnalisé"""
    emoji: str = Field(..., min_length=1, max_length=10)


class ExtendStoryRequest(BaseModel):
    """Extension d'histoire avec de nouveaux émoticônes"""
    new_emojis: list[str] = Field(..., min_length=1, max_length=10)


class StoryUpdateRequest(BaseModel):
    """Mise à jour interne (appelée par n8n après chaque génération IA)"""
    story_text: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
