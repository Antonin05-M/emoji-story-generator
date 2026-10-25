<div align="center">

# 🎭 Emoji Story Generator

**Une histoire illustrée et sonorisée, à partir de quelques émojis.**

React · FastAPI · PostgreSQL · n8n · Mistral · FLUX · ElevenLabs

*Version 3.1 — projet personnel de lab-anto ([lab-anto.com](https://lab-anto.com))*

</div>

---

## 📖 Le concept

Tu tires 6 émoticônes au hasard, tu en ajoutes 4 parmi **1 036 disponibles**
(12 catégories), tu les ordonnes par glisser-déposé… et l'application fait le reste :

- 🇫🇷 **Mistral** écrit une histoire qui suit ta séquence d'émojis ;
- 🎨 **FLUX** (via Pollinations) illustre la scène ;
- 🔊 **Pixtral** analyse l'illustration + le récit et écrit un prompt de sound design,
  puis **ElevenLabs Sound Effects** génère une ambiance sonore (~20 s).

Tout est orchestré par **n8n**, stocké dans **PostgreSQL**, et consultable dans une
galerie. Une histoire peut ensuite être **prolongée** avec de nouveaux émojis.

## ✨ Fonctionnalités (v3.1)

| Fonctionnalité | Détail |
|---|---|
| 🎲 Sélection d'émojis | 6 aléatoires + 4 au choix parmi **1 036 émoticônes** (12 catégories : émotions, personnes, animaux, nature, nourriture, activités, objets, voyages, symboles, temps, vêtements, maison) |
| 🔍 Recherche d'émoji | Barre de filtre avec **mots-clés français** (~340 émoticônes indexés : « chat », « château », « fusée »…), insensible à la casse et aux accents |
| 🏷️ Pastilles de sélection | Les émojis choisis s'affichent en pastilles cliquables (clic = retirer) |
| 📖 Thème libre optionnel | Aventure, policier, poétique… transmis au prompt texte **et** au prompt image **et** au sound design |
| 📜 Histoire rédigée | Par Mistral (`mistral-large-latest`), affichage avec **gras/italique Markdown interprétés** |
| 🎨 Illustration | FLUX via **Pollinations** (gratuit, sans clé) — 1024×768, JPEG |
| 🔊 Ambiance sonore | Pixtral (`mistral-medium-latest`) analyse image + récit → prompt sound design → ElevenLabs Sound Effects (~20 s). **Pas une lecture du texte** |
| ➕ Évolution d'histoire | Prolonge une histoire avec de nouveaux émojis — le début est **conservé**, la suite s'y ajoute ; sélection parmi **toute** la base avec recherche |
| 📚 Galerie | Toutes les histoires (extrait, thème, date **locale**), relecture en un clic, **suppression définitive** (texte + image + audio) via le bouton ✕ |
| 🖥️ Jouable en réseau | URLs relatives via proxy Nginx : l'interface fonctionne depuis n'importe quelle machine du réseau |

## 🏗️ Architecture

    Utilisateur (navigateur)
    │  http://<IP-VM>:3000
    ▼
    frontend (React + Nginx :80)  ──proxy /api et /media──►  api (FastAPI :8000)
    │                                                          ▲
    │  POST /stories ──webhook──► n8n (:5678) ──PATCH /stories/{id}──┘
    │                              │
    │                              ├──► Mistral API          → histoire (texte)
    │                              ├──► Pollinations (FLUX) → illustration (.jpg)
    │                              └──► Pixtral + ElevenLabs → ambiance (.mp3)
    ▼
    db (PostgreSQL 16, non exposée) — emoji_db (métier) + n8n_db (interne n8n)

**Volumes Docker** : `postgres_data`, `media` (partagé entre `api` et `n8n`),
`n8n_data`. Les conteneurs se joignent par nom de service sur `emoji-network`.

**Point clé : seul l'API écrit en base.** n8n déclenche les générations puis met à
jour l'histoire via `PATCH http://api:8000/stories/{id}` — requêtes paramétrées
côté Python, donc les apostrophes et guillemets du texte français ne cassent rien,
et aucune injection SQL n'est possible.

### La chaîne de génération pas à pas

| Étape | Workflow n8n | Ce qui se passe | Statut de l'histoire |
|---|---|---|---|
| 1 | Generate Story (Mistral) | Mistral rédige l'histoire (thème + séquence d'émojis) → PATCH texte | `story_generated` |
| 2 | Generate Image (Pollinations) | FLUX illustre (thème + émojis + extrait du récit) → PATCH image | — |
| 3 | Generate Ambience (Pixtral + ElevenLabs) | Pixtral analyse l'image + le récit → prompt sound design → ElevenLabs → PATCH audio | `completed` |

⏳ **Durée** : quelques secondes pour le texte, 1 à 8 minutes pour l'image
(file d'attente gratuite de Pollinations, timeout n8n réglé sur 600 s), puis
quelques secondes pour l'audio. L'interface affiche les étapes au fur et à mesure.

## 📁 Arborescence

    emoji-story-generator/
    ├── docker-compose.yml       # 4 services : db, api, n8n, frontend
    ├── .env.example             # modèle de configuration (copier en .env)
    ├── .gitignore
    ├── README.md
    ├── db/
    │   └── init.sql             # schéma PostgreSQL (stories, custom_emojis, story_history)
    ├── api/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── models.py            # modèles Pydantic
    │   └── main.py              # API FastAPI : émojis, histoires, galerie, suppression
    ├── n8n/
    │   ├── Dockerfile
    │   └── workflows/
    │       ├── generate_story.json
    │       ├── generate_image.json
    │       └── generate_audio.json
    ├── frontend/
    │   ├── Dockerfile
    │   ├── package.json
    │   ├── nginx.conf           # proxy /api et /media
    │   ├── public/
    │   │   ├── index.html
    │   │   └── lab-anto.png     # logo (à fournir — non inclus)
    │   └── src/
    │       ├── index.js
    │       ├── App.jsx          # écrans, galerie, évolution
    │       ├── styles.css
    │       └── components/
    │           ├── EmojiPicker.jsx    # grille + barre de recherche
    │           └── StoryDisplay.jsx   # récit + médias (Markdown interprété)
    └── media/                   # illustrations .jpg + ambiances .mp3 (volume partagé)

> **Note** : le logo `frontend/public/lab-anto.png` est un fichier personnel
> volontairement absent du dépôt. Mets-le en place, ou retire le bloc
> `.logo-link` de `App.jsx` si tu n'en veux pas.

## 📋 Prérequis

- Une machine Linux (testé sur Debian 12) avec **Docker Engine ≥ 24** et
  **Docker Compose v2**
- Une clé API **Mistral** — [console.mistral.ai](https://console.mistral.ai)
- Une clé API **ElevenLabs** — [elevenlabs.io](https://elevenlabs.io)
  (chaque ambiance ~20 s consomme des crédits ; le plan gratuit offre un quota
  mensuel — la plateforme « Creative » est la plus adaptée aux Sound Effects)
- **Pas besoin de token Hugging Face** : l'illustration passe par Pollinations
  (gratuit, sans clé)
- Ports libres : 3000 (interface), 8000 (API), 5678 (n8n)

## 🚀 Installation pas à pas

### 1. Récupérer le projet et configurer

    git clone <url-du-repo> && cd emoji-story-generator
    cp .env.example .env
    nano .env   # renseigne MISTRAL_API_KEY et ELEVENLABS_API_KEY

### 2. Lancer la stack

    docker compose up -d --build
    docker compose ps        # les 4 services doivent être "healthy"/"running"

### 3. Initialiser n8n

Ouvre `http://<IP-VM>:5678` et crée le compte propriétaire (email + mot de
passe). Ignore l'écran d'onboarding qui propose des intégrations.

### 4. Créer les 2 credentials (noms EXACTS)

n8n → Credentials → Add Credential → **Header Auth** :

| Nom exact | Header | Valeur |
|---|---|---|
| `Mistral API Header` | `Authorization` | `Bearer <clé Mistral>` (espace après « Bearer ») |
| `ElevenLabs API Header` | `xi-api-key` | `<clé ElevenLabs>` |

### 5. Importer et activer les 3 workflows

Workflows → **Import from File** → les 3 fichiers de `n8n/workflows/`,
puis pour chaque workflow :

1. **Attache le credential** dans chaque nœud d'appel API (Mistral ×2,
   ElevenLabs ×1) — l'import ne peut pas les lier tout seul ;
2. Vérifie les **menus Method** des nœuds HTTP : POST pour les appels IA,
   PATCH pour les mises à jour, GET pour Pollinations ;
3. Sur les 2 nœuds **Read/Write Files from Disk**, re-sélectionne
   l'opération (« Write File to Disk » sur *Save Image File* et
   *Save Audio File*, « Read File(s) from Disk » sur *Read Image File*)
   puis vérifie dans **Options** du nœud de lecture que
   *Put Output File in Field* = `image` ;
4. Vérifie que **Always Output Data** est bien coché sur les 2 nœuds
   d'écriture de fichier (déjà dans le JSON, mais à contrôler) ;
5. **Publish** (ou Save) puis bascule le workflow sur **Active**.

### 6. Tester en ligne de commande

    # Création d'une histoire via l'API (chemin réel utilisé par le frontend)
    curl -X POST http://localhost:8000/stories \
      -H "Content-Type: application/json" \
      -d '{"emojis":["🐉","🏰","🔥","👑","🌙","✨","🚀","🌊","💥","🌟"]}'
    
    # Suivi du statut : pending -> story_generated -> completed
    curl http://localhost:8000/stories/<story_id>
    
    # L'interface n8n (onglet Executions) montre chaque étape en cas de souci

### 7. Jouer

    http://<IP-VM>:3000

## 📡 API (documentation interactive : `http://<IP-VM>:8000/docs`)

| Méthode | Route | Description |
|---|---|---|
| GET | `/emojis` | Les 1 036 émoticônes par catégorie + `keywords` (mots-clés FR pour la recherche) |
| GET | `/emojis/random` | 6 émoticônes aléatoires |
| POST | `/emojis` | Ajouter un émoticône personnalisé |
| POST | `/stories` | Créer une histoire (10 émoticônes + thème optionnel) → déclenche n8n |
| GET | `/stories` | Galerie : dernières histoires (extrait du texte inclus) |
| GET | `/stories/{id}` | Statut + texte + médias d'une histoire |
| PATCH | `/stories/{id}` | Mise à jour interne — appelée par n8n (conserve le début en cas d'extension) |
| DELETE | `/stories/{id}` | **Supprimer** une histoire : lignes SQL + fichiers média |
| POST | `/stories/{id}/extend` | Faire évoluer l'histoire avec de nouveaux émoticônes |

## ⚠️ Pièges connus & dépannage

| Problème | Cause / Solution |
|---|---|
| Webhook 404 | Le workflow n'est pas **activé** dans n8n |
| 401 Mistral / ElevenLabs | Vérifie le credential (espace après « Bearer » pour Mistral ; header `xi-api-key` pour ElevenLabs) et le rattachement du credential au nœud |
| Image très lente (1-8 min) | Normal : file d'attente gratuite de Pollinations (1 req/15 s). Le timeout n8n est réglé sur 600 s |
| « Access to the file is not allowed » | Déjà corrigé par `N8N_RESTRICT_FILE_ACCESS_TO=/home/node/media` dans le docker-compose |
| « Cannot decode file 'filesystem-v2' » | Déjà corrigé par `N8N_DEFAULT_BINARY_DATA_MODE=default` dans le docker-compose |
| Chaîne qui s'arrête après l'écriture d'un fichier | **Always Output Data** doit être coché sur les nœuds writeFile (ils ne renvoient rien par conception) |
| Modèle invalide (Pixtral) | Le modèle vision est `mistral-medium-latest` (Pixtral Large est déprécié) ; liste à jour sur console.mistral.ai |
| Erreur ElevenLabs 401/422 | Clé ou crédits épuisés (chaque ambiance consomme des crédits) |
| Histoire bloquée en `pending`/`story_generated` | Onglet **Executions** de n8n : l'erreur exacte y est visible |
| n8n inaccessible depuis une autre machine | `N8N_SECURE_COOKIE=false` est déjà configuré ; sinon vérifie le pare-feu (`ss -tulpn`) |
| Conteneur en boucle de redémarrage | `docker compose logs -f <service>` |
| Tout réinitialiser | `docker compose down -v` (supprime données et médias) puis `docker compose up -d --build` |

## 🔒 Sécurité

- **Aucun secret dans le code source** : tout vient du `.env` (exclu de Git
  via le `.gitignore`).
- PostgreSQL n'est pas exposée sur l'hôte (réseau interne Docker uniquement).
- `PATCH`/`DELETE /stories/{id}` sont internes au réseau Docker : si un jour
  l'API est exposée sur Internet, ajoute un token d'authentification sur ces
  routes.
- `N8N_SECURE_COOKIE=false` : acceptable sur un réseau local de confiance ;
  repasse à `true` (avec HTTPS) si n8n est exposé publiquement.

## 🧰 Commandes utiles

    docker compose ps              # état des services
    docker compose logs -f api     # logs de l'API
    docker compose logs -f n8n     # logs n8n
    docker compose up -d --build api frontend   # reconstruire après une modif code
    docker compose down            # arrêter (données conservées)
    docker compose down -v         # tout supprimer (données incluses)

## 📜 Historique des versions

| Version | Contenu |
|---|---|
| v1 | Prototype initial (orchestration directe n8n → PostgreSQL) |
| v2 | Refonte : seul l'API écrit en base (requêtes paramétrées), proxy Nginx, ambiance sonore **générée** (Pixtral + ElevenLabs) au lieu d'une lecture du texte |
| v2.1 | Thème libre optionnel (texte + image) et galerie des histoires |
| v2.2.x | Fixes de déploiement en conditions réelles (ajv, PostgreSQL 16, entrypoint n8n, méthodes HTTP, nœuds fichiers, accès fichiers, mode binaire) ; image migrée vers Pollinations gratuit ; chaîne complète validée |
| v2.3.0 | Horodatage local, logo cliquable, émojis noir et blanc corrigés (VS16), prompts enrichis (récit dans le prompt image, pas d'émoji dans le texte) |
| v2.3.1 | **1 036 émoticônes** (+ vêtements, maison), **recherche** par mots-clés FR, **suppression** d'histoires dans la galerie |
| v2.3.2 | Pastilles de sélection, évolution d'histoire sur **toute** la base avec recherche, le début d'une histoire est **conservé** lors d'une extension |
| v2.3.3 | Affichage **Markdown interprété** (titres en gras) |
| **v3.1** | Consolidation : README complet, structure Git, versions internes alignées |

## 🔮 Évolutions possibles

- Token d'authentification sur les routes PATCH/DELETE internes
- Durée d'ambiance paramétrable depuis l'interface (`duration_seconds`)
- Musique générée en plus du soundscape (MusicGen, Stable Audio)
- Partage d'histoires par lien, export PDF
- Plusieurs illustrations par histoire
- Élargir les mots-clés de recherche à davantage d'émojis

## 🙏 Crédits & mentions

- [Mistral AI](https://mistral.ai) — rédaction (`mistral-large-latest`) et analyse d'image (`mistral-medium-latest`)
- [Pollinations](https://pollinations.ai) — illustration FLUX, gratuite
- [ElevenLabs](https://elevenlabs.io) — ambiances sonores (Sound Effects)
- [n8n](https://n8n.io), [FastAPI](https://fastapi.tiangolo.com), [PostgreSQL](https://www.postgresql.org), [React](https://react.dev)

Projet réalisé par Antonin Moisan — [lab-anto.com](https://lab-anto.com)
