# **🎭 Le projet en résumé**
__________________________________________________________________
**Emoji Story Generator :** 
> une application web qui transforme une séquence d'émojis en histoire complète — texte, illustration et ambiance sonore.
___________________________



| Couche | Technologie | Rôle |
| --- | --- | --- |
| Interface | React + Nginx (:3000) | Sélection d'émojis, thème, galerie, relecture, suppression |
| API | FastAPI (:8000) | Seule à écrire en base (requêtes paramétrées), 10 routes |
| Base | PostgreSQL 16 | `emoji_db` (métier) + `n8n_db` (interne n8n) |
| Orchestration | n8n (:5678) | 3 workflows : Histoire → Image → Ambiance |
| IA | Mistral (texte + analyse d'image) · FLUX via Pollinations (image, gratuite) · ElevenLabs (son) | La chaîne générative |