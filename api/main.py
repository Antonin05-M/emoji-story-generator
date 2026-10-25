"""API Emoji Story Generator - FastAPI

Seul service de la stack à écrire dans PostgreSQL : toutes les requêtes
sont paramétrées (aucune concaténation SQL), ce qui rend impossible la
casse par apostrophes françaises ou l'injection SQL.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from models import (
    EmojiStoryRequest,
    EmojiAddRequest,
    ExtendStoryRequest,
    StoryUpdateRequest,
)
import psycopg2
import os
import httpx
import random
import uuid
from datetime import datetime, timezone

app = FastAPI(title="Emoji Story Generator API", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("/app/media", exist_ok=True)
app.mount("/media", StaticFiles(directory="/app/media"), name="media")

# Configuration : UNIQUEMENT via variables d'environnement
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT"),
}

# =============================================================================
# BASE D'ÉMOTICÔNES (500+ par catégories)
# =============================================================================
EMOJI_DATABASE = {
    "emotions": [
        "😀","😃","😄","😁","😆","😅","🤣","😂","🙂","🙃","😉","😊","😇","🥰",
        "😍","🤩","😘","😗","😚","😙","🥲","😋","😛","😜","🤪","😝","🤑","🤗",
        "🤭","🫢","🫣","🤫","🤔","🫡","🤐","🤨","😐","😑","😶","🫥","😏","😒",
        "🙄","😬","😮‍💨","🤥","😌","😔","😪","🤤","😴","😷","🤒","🤕","🤢","🤮",
        "🤧","🥵","🥶","🥴","😵","😵‍💫","🤯","🤠","🥳","🥸","😎","🤓","🧐","😕",
        "🫤","😟","🙁","☹️","😮","😯","😲","😳","🥺","🥹","😦","😧","😨","😰",
        "😥","😢","😭","😱","😖","😣","😞","😓","😩","😫","🥱","😤","😡","😠",
        "🤬","😈","👿","💀","☠️","💩","🤡","👹","👺","👻","👽","🤖","😺","😸",
        "😹","😻","😽","🙀","😿","😾","🙈","🙉","🙊"
    ],
    "personnes": [
        "👋","🤚","🖐️","✋","🖖","🫱","🫲","🫳","🫴","🤝","🙏","✍️","💅","🤳",
        "💪","🦾","🦿","🦵","🦶","👂","🦻","👃","🧠","🫀","🫁","🦷","🦴","👀",
        "👁️","👅","👄","👶","🧒","👦","👧","🧑","👨","👩","🧓","👴","👵","🙍",
        "🙎","🙅","🙆","💁","🙋","🧏","🙇","🤦","🤷","👮","🕵️","💂","🥷","👷",
        "🤴","👸","👑","👳","🤵","👰","🤰","🫃","🤱","👼","🎅","🤶","🦸","🦹","🧙",
        "🧚","🧛","🧜","🧝","🧞","🧟","💃","🕺","👯","🧘","🤌","🫰","🫦","🫅","🫄"
    ],
    "animaux": [
        "🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐸",
        "🐵","🐒","🐔","🐧","🐦","🐤","🐣","🐥","🦆","🦅","🦉","🦇","🐺","🐗",
        "🐴","🦄","🐝","🪱","🐛","🦋","🐌","🐞","🐜","🪰","🪲","🪳","🦂","🐢",
        "🐍","🦎","🦖","🦕","🐙","🦑","🦐","🦞","🦀","🐡","🐠","🐟","🐬","🐳",
        "🐋","🦈","🐊","🐅","🐆","🦓","🦍","🦧","🐘","🦛","🦏","🐪","🐫","🦒",
        "🦘","🐂","🐄","🐎","🐖","🐏","🐑","🦙","🐐","🦌","🐕","🐩","🦮","🐈",
        "🐈‍⬛","🐓","🦃","🦚","🦜","🦢","🕊️","🐇","🦝","🦨","🦡","🦫","🦦","🦥",
        "🐁","🐀","🐿️","🦔","🦭","🪿","🫎","🫏","🪶","🐾","🦠","🪽"
    ],
    "nature": [
        "🌵","🎄","🌲","🌳","🌴","🌱","🌿","☘️","🍀","🎍","🎋","🍃","🍂","🍁",
        "🌾","🌷","🪷","🌹","🥀","🌺","🌸","🌼","🌻","🌞","🌝","🌛","🌜","🌚",
        "🌕","🌖","🌗","🌘","🌑","🌒","🌓","🌔","🌙","🌎","🌍","🌏","🪐","💫",
        "⭐️","🌟","✨","⚡️","☄️","💥","🔥","🌪️","🌈","☀️","🌤️","⛅","🌥️","☁️",
        "🌦️","🌧️","⛈️","🌩️","🌨️","❄️","☃️","⛄️","🌬️","💨","💧","💦","🌊","🌫️",
        "🏝️","🏔️","⛰️","🌋","🗻","🏕️","🏖️","🏜️","🏞️","🪨","🌅","🌄","🌠","🌇",
        "🌆","🌃","🌌","🌉","🪸","🪻"
    ],
    "nourriture": [
        "🍇","🍈","🍉","🍊","🍋","🍌","🍍","🥭","🍑","🍒","🍓","🫐","🥝",
        "🍅","🫒","🥥","🥑","🍆","🥔","🥕","🌽","🌶️","🫑","🥒","🥬","🥦","🧄",
        "🧅","🍄","🥜","🫘","🌰","🍞","🥐","🥖","🫓","🥨","🥯","🥞","🧇","🧈",
        "🍳","🥚","🧀","🥓","🥩","🍗","🍖","🌭","🍔","🍟","🍕","🥙","🧆","🌮",
        "🌯","🫔","🥗","🥘","🫕","🥫","🍝","🍜","🍲","🍛","🍣","🍱","🥟","🦪",
        "🍤","🍙","🍚","🍘","🍥","🥠","🥮","🍢","🍡","🍧","🍨","🍦","🥧","🧁",
        "🍰","🎂","🍮","🍭","🍬","🍫","🍿","🍩","🍪","☕️","🍵","🧉","🥤","🧋",
        "🍺","🍻","🥂","🍷","🥃","🍸","🍹","🧊","🥛","🍼","🧂","🫙","🍯","🫗","🫖"
    ],
    "activites": [
        "⚽️","🏀","🏈","⚾️","🥎","🎾","🏐","🏉","🥏","🎱","🪀","🏓","🏸","🏒",
        "🥅","⛳️","🪁","🏹","🎣","🤿","🥊","🥋","🎽","🛹","🛼","🛷","⛸️","🥌",
        "🎿","⛷️","🏂","🪂","🏋️","🤼","🤸","⛹️","🤺","🤾","🏌️","🏇","🧘","🏄",
        "🏊","🤽","🚣","🧗","🚵","🚴","🏆","🥇","🥈","🥉","🎖️","🏅","🎗️","🎫",
        "🎟️","🎪","🤹","🎭","🩰","🎨","🎬","🎤","🎧","🎼","🎹","🥁","🪘","🪗",
        "🎷","🎺","🎸","🪕","🎻","🎲","♟️","🎯","🎳","🎮","🎰","🧩","🪩","🛝","🃏","🪄"
    ],
    "objets": [
        "⌚️","📱","💻","⌨️","🖥️","🖨️","🖱️","🖲️","🕹️","🗜️","💽","💾","💿","📀",
        "🧮","🎥","📷","📹","📼","🔍","🔎","🕯️","💡","🔦","🏮","🪔","📔","📕",
        "📖","📗","📘","📙","📚","📓","📒","📃","📜","📄","📰","🗞️","📑","🔖",
        "🏷️","💰","🪙","💴","💵","💶","💷","💸","💳","🧾","✉️","📧","📨","📩",
        "📤","📥","📦","📪","📫","📬","📭","📮","🗳️","✏️","✒️","🖋️","🖊️","🖌️",
        "🖍️","📝","💼","📁","📂","🗂️","📅","📆","🗒️","🗓️","📇","📈","📉","📊",
        "📋","📌","📍","📎","🖇️","📏","📐","✂️","🗃️","🗄️","🗑️","🔒","🔓","🔏",
        "🔐","🔑","🗝️","🔨","🪓","⛏️","⚒️","🛠️","🗡️","⚔️","💣","🪃","🛡️","🪚",
        "🔧","🪛","🔩","⚙️","⚖️","🔗","⛓️","🪤","🧰","🧲","🪜","🔬","🔭","📡","🩺",
        "🩹","🩼","💊","💉","🩸","🧪","🧫","🧵","🧶","🪡","🪢","🪪","🎁","🎈","🎀",
        "🛍️","🛒","💎","🔋","🔌","🪫","🧸"
    ],
    "voyages": [
        "🚗","🚕","🚙","🚌","🚎","🏎️","🚓","🚑","🚒","🚐","🛻","🚚","🚛","🚜",
        "🛴","🚲","🛵","🏍️","🛺","🚨","🚔","🚍","🚘","🚖","🚡","🚠","🚟","🚃",
        "🚋","🚞","🚝","🚄","🚅","🚈","🚂","🚆","🚇","🚊","🚉","✈️","🛫","🛬",
        "🛩️","💺","🛰️","🚀","🛸","🚁","🛶","⛵️","🚤","🛥️","🛳️","⛴️","🚢","⚓️",
        "🪝","⛽️","🚧","🚦","🚥","🗺️","🗿","🗽","🗼","🏰","🏯","🏟️","🎡","🎢",
        "🎠","⛲️","🏖️","🏝️","🏜️","🌋","⛰️","🏔️","🗻","🏕️","⛺️","🛖","🏠",
        "🏡","🏢","🏣","🏤","🏥","🏦","🏨","🏩","🏪","🏫","🏬","💒","🏛️","⛪️",
        "🕌","🕍","🛕","🕋","⛩️","🛤️","🛣️","🗾","🏞️","🎇","🎆","🛞","🚏","🏘️","🏚️","🧭"
    ],
    "symboles": [
        "❤️","🧡","💛","💚","💙","💜","🖤","🤍","🤎","🫶","💔","❣️","💕","💞",
        "💓","💗","💖","💘","💝","💟","☮️","✝️","☪️","🕉️","☸️","✡️","🔯","🕎",
        "🪯","✴️","✳️","❇️","💠","🔱","⚜️","🔰","⚠️","🚸","⛔️","🚫","🚳","🚭",
        "🚯","🚱","🚷","🔞","☢️","☣️","⬆️","↗️","➡️","↘️","⬇️","↙️","⬅️","↖️",
        "↕️","↔️","↩️","↪️","⤴️","⤵️","🔃","🔄","🔙","🔚","🔛","🔜","🔝","🛐",
        "⚛️","🔮","🔔","🔕","🎵","🎶","💹","💱","©️","®️","™️","🩷","🩵","🩶","🧿",
        "🌐","🪬","🆕","🆒","🆓","🆙","⁉️","❓","❗","‼️","❕","❔"
    ],
    "temps": [
        "🕐","🕑","🕒","🕓","🕔","🕕","🕖","🕗","🕘","🕙","🕚","🕛","🕜","🕝",
        "🕞","🕟","🕠","🕡","🕢","🕣","🕤","🕥","🕦","⏰","⏱️","⏲️","⏳️","⌛️","🕰️","🌡️"
    ],
    "vêtements": [
        "👔","👕","👖","🧥","🧦","🧤","🧣","👗","👘","🥻","🩱","🩲","👙","👚",
        "🥽","🥼","🦺","🪖","🕶️","🪭","👜","👝","🎒","👛","🩴","👟","🥾","👡",
        "👠","👢"
    ],
    "maison": [
        "🚪","🪟","🛏️","🪑","🛋️","🛗","🚽","🚿","🛁","🪞","🧻","🧼","🧽","🧹",
        "🧺","🪣","🧴","🧷","🪥","🪒","🧯","🪴"
    ],
}

# Aplatis + déduplique en préservant l'ordre
ALL_EMOJIS = []
for _cat, _list in EMOJI_DATABASE.items():
    ALL_EMOJIS.extend(_list)
ALL_EMOJIS = list(dict.fromkeys(ALL_EMOJIS))

# =============================================================================
# MOTS-CLÉS FRANÇAIS pour la barre de recherche d'émoticônes.
# Les émoticônes non listés restent visibles dans la grille, mais ne
# remontent pas dans une recherche par mot. La correspondance est
# insensible à la casse et aux accents (faite côté frontend).
# =============================================================================
EMOJI_KEYWORDS = {
    # --- Animaux ---
    "🐶": "chien", "🐱": "chat", "🐭": "souris", "🐹": "hamster",
    "🐰": "lapin", "🦊": "renard", "🐻": "ours", "🐼": "panda",
    "🐨": "koala", "🐯": "tigre", "🦁": "lion", "🐮": "vache",
    "🐷": "cochon", "🐸": "grenouille", "🐵": "singe", "🐔": "poule",
    "🐧": "pingouin manchot", "🐦": "oiseau", "🐤": "poussin",
    "🐣": "eclosion poussin", "🐥": "poussin oiseau", "🦆": "canard",
    "🦅": "aigle", "🦉": "hibou chouette", "🦇": "chauve-souris",
    "🐺": "loup", "🐗": "sanglier", "🐴": "cheval", "🦄": "licorne",
    "🐝": "abeille", "🪱": "ver", "🐛": "chenille insecte",
    "🦋": "papillon", "🐌": "escargot", "🐞": "coccinelle",
    "🐜": "fourmi", "🦂": "scorpion", "🐢": "tortue", "🐍": "serpent",
    "🦎": "lezard", "🦖": "dinosaure tyrannosaure", "🦕": "dinosaure",
    "🐙": "poulpe pieuvre", "🦑": "calamar", "🦐": "crevette",
    "🦞": "homard", "🦀": "crabe", "🐡": "poisson-globe",
    "🐠": "poisson tropical", "🐟": "poisson", "🐬": "dauphin",
    "🐳": "baleine", "🦈": "requin", "🐊": "crocodile alligator",
    "🐅": "tigre", "🐆": "leopard", "🦓": "zebre", "🦍": "gorille",
    "🦧": "orang-outan", "🐘": "elephant", "🦛": "hippopotame",
    "🦏": "rhinoceros", "🐪": "dromadaire", "🐫": "chameau",
    "🦒": "girafe", "🦘": "kangourou", "🐂": "boeuf taureau",
    "🐄": "vache", "🐎": "cheval", "🐖": "cochon", "🐏": "belier mouton",
    "🐑": "mouton", "🦙": "lama", "🐐": "chevre", "🦌": "cerf biche",
    "🐕": "chien", "🐩": "caniche chien", "🐈": "chat",
    "🐈‍⬛": "chat noir", "🐓": "coq", "🦃": "dindon",
    "🦚": "paon", "🦜": "perroquet", "🦢": "cygne",
    "🕊️": "colombe paix", "🐇": "lapin", "🦝": "raton laveur",
    "🦨": "mouffette putois", "🦡": "blaireau", "🦫": "castor",
    "🦦": "loutre", "🦥": "paresseux", "🐁": "souris", "🐀": "rat",
    "🐿️": "ecureuil", "🦔": "herisson", "🦭": "phoque", "🪿": "oie",
    "🫎": "elan orignal", "🫏": "ane", "🪶": "plume",
    "🐾": "patte empreinte", "🦠": "microbe virus", "🪽": "aile",
    # --- Nourriture ---
    "🍇": "raisin", "🍉": "pasteque", "🍊": "orange agrume",
    "🍋": "citron", "🍌": "banane", "🍍": "ananas", "🥭": "mangue",
    "🍑": "peche", "🍒": "cerise", "🍓": "fraise", "🫐": "myrtille",
    "🥝": "kiwi", "🍅": "tomate", "🫒": "olive", "🥥": "coco noix",
    "🥑": "avocat", "🍆": "aubergine", "🥔": "patate pomme de terre",
    "🥕": "carotte", "🌽": "mais", "🌶️": "piment", "🫑": "poivron",
    "🥒": "concombre", "🥬": "chou salade", "🥦": "brocoli",
    "🧄": "ail", "🧅": "oignon", "🍄": "champignon", "🥜": "cacahuete",
    "🫘": "haricot", "🌰": "chataigne", "🍞": "pain",
    "🥐": "croissant", "🥖": "baguette pain", "🫓": "galette",
    "🥨": "bretzel", "🥯": "bagel", "🥞": "crepes pancakes",
    "🧇": "gaufre", "🧈": "beurre", "🍳": "oeufs poele",
    "🥚": "oeuf", "🧀": "fromage", "🥓": "bacon lardons",
    "🥩": "viande steak", "🍗": "poulet cuisse", "🍖": "viande",
    "🌭": "hot-dog", "🍔": "hamburger burger", "🍟": "frites",
    "🍕": "pizza", "🥙": "kebab taco", "🧆": "falafel",
    "🌮": "taco", "🌯": "burrito", "🫔": "tamal", "🥗": "salade",
    "🥘": "paella poele", "🫕": "fondue", "🥫": "conserve",
    "🍝": "pates spaghettis", "🍜": "nouilles ramen soupe",
    "🍲": "ragout potage", "🍛": "curry", "🍣": "sushi",
    "🍱": "bento", "🥟": "ravioli", "🍤": "crevette",
    "🍙": "boulette riz", "🍚": "riz", "🍥": "naruto",
    "🥠": "biscuit fortune", "🥮": "gateau lune", "🍢": "brochette",
    "🍡": "dango", "🍧": "granite glace", "🍨": "glace",
    "🍦": "glace cornet", "🥧": "tarte", "🧁": "cupcake",
    "🍰": "part de gateau", "🎂": "gateau anniversaire",
    "🍮": "flan", "🍭": "sucette", "🍬": "bonbon",
    "🍫": "chocolat", "🍿": "popcorn", "🍩": "donut beignet",
    "🍪": "cookie biscuit", "☕️": "cafe", "🍵": "the",
    "🧉": "mate", "🥤": "soda boisson", "🧋": "bubble tea",
    "🍺": "biere", "🍻": "chope biere", "🥂": "champagne toast",
    "🍷": "vin", "🥃": "whisky alcool", "🍸": "cocktail",
    "🍹": "cocktail tropical", "🥛": "lait", "🍼": "biberon",
    "🧂": "sel", "🫙": "pot conserve", "🍯": "miel",
    "🫗": "versement boisson", "🫖": "theiere",
    # --- Nature ---
    "🌵": "cactus", "🎄": "sapin noel", "🌲": "pin arbre",
    "🌳": "arbre", "🌴": "palmier", "🌱": "pousse graine",
    "🌿": "herbe plante", "☘️": "trefle", "🍀": "trefle chance",
    "🍂": "feuilles mortes automne", "🍁": "erable feuille automne",
    "🌾": "ble epis", "🌷": "tulipe", "🪷": "lotus",
    "🌹": "rose", "🥀": "rose fanee fleur", "🌺": "hibiscus",
    "🌸": "fleur cerisier", "🌼": "fleur marguerite",
    "🌻": "tournesol", "🌞": "soleil visage", "🌙": "lune",
    "💫": "etincelle etoile", "⭐️": "etoile", "🌟": "etoile brillante",
    "✨": "etincelles magie", "⚡️": "eclair orage",
    "☄️": "comete", "💥": "explosion", "🔥": "feu flamme",
    "🌪️": "tornade", "🌈": "arc-en-ciel", "☀️": "soleil",
    "❄️": "flocon neige hiver", "☃️": "bonhomme de neige",
    "⛄️": "bonhomme de neige", "🌬️": "vent", "💨": "souffle vent",
    "💧": "goutte eau", "💦": "gouttes sueur", "🌊": "vague mer ocean",
    "🌫️": "brouillard", "🏝️": "ile",
    "🏔️": "montagne neige", "⛰️": "montagne", "🌋": "volcan",
    "🗻": "mont fuji", "🏕️": "camping tente", "🏖️": "plage",
    "🏜️": "desert", "🏞️": "parc paysage", "🪨": "rocher pierre",
    "🌅": "lever de soleil", "🌄": "leve soleil montagne",
    "🌠": "etoile filante", "🌇": "coucher de soleil",
    "🌌": "galaxie voie lactee", "🌉": "pont nuit",
    "🪸": "corail", "🪻": "jacinthe fleur",
    "🌡️": "temperature thermometre",
    # --- Voyages / lieux ---
    "🚗": "voiture", "🚕": "taxi", "🚌": "bus", "🏎️": "voiture course",
    "🚓": "voiture police", "🚑": "ambulance",
    "🚒": "camion pompier", "🚚": "camion", "🚜": "tracteur",
    "🚲": "velo", "🏍️": "moto", "🛴": "trottinette",
    "🛵": "scooter", "🚨": "gyrophaire alarme",
    "🚄": "train rapide", "🚂": "locomotive train", "🚇": "metro",
    "🚉": "gare", "✈️": "avion", "🚀": "fusee espace",
    "🚁": "helicoptere", "🛶": "canoe", "⛵️": "voilier bateau",
    "🚢": "paquebot bateau", "⚓️": "ancre", "🗺️": "carte",
    "🗿": "statue moai", "🗽": "statue liberte", "🗼": "tour eiffel",
    "🏰": "chateau", "🏯": "chateau japonais", "🎡": "grande roue",
    "🎢": "montagnes russes", "🎠": "carrousel manege",
    "⛲️": "fontaine", "🏠": "maison", "🏡": "maison jardin",
    "🏢": "immeuble bureau", "🏥": "hopital", "🏦": "banque",
    "🏨": "hotel", "🏪": "epicerie magasin", "🏫": "ecole",
    "🏬": "grand magasin", "⛪️": "eglise", "🕌": "mosquee",
    "🛕": "temple hindou", "🕋": "kaaba", "⛩️": "torii temple japonais",
    "🗾": "japon carte", "🎇": "feux artifice",
    "🎆": "feux artifice", "🛞": "roue", "🚏": "arret bus",
    "🏘️": "maisons quartier", "🏚️": "maison abandonnee ruine",
    "🧭": "boussole",
    # --- Objets ---
    "⌚️": "montre", "📱": "telephone portable", "💻": "ordinateur",
    "🖥️": "ordinateur bureau", "🖨️": "imprimante", "🎥": "camera cinema",
    "📷": "appareil photo", "🔍": "loupe recherche",
    "🔎": "loupe", "🕯️": "bougie", "💡": "ampoule idee",
    "🏮": "lanterne", "🪔": "lampe huile", "📖": "livre",
    "📚": "livres", "📰": "journal", "💰": "sac argent",
    "🪙": "piece monnaie", "💵": "billet argent",
    "💳": "carte bancaire", "✉️": "lettre enveloppe",
    "📧": "email courriel", "📦": "colis carton",
    "📮": "boite aux lettres", "✏️": "crayon", "🖊️": "stylo",
    "🖌️": "pinceau", "📝": "note memo", "💼": "malette travail",
    "📁": "dossier", "📅": "calendrier", "📈": "graphique croissance",
    "📊": "diagramme", "📋": "presse-papiers", "📌": "punaise",
    "📍": "epingle localisation", "✂️": "ciseaux",
    "🔒": "cadenas ferme", "🔓": "cadenas ouvert",
    "🔗": "chaine lien", "🔑": "cle", "🔨": "marteau",
    "🪓": "hache", "⛏️": "pioche", "🛠️": "outils",
    "🗡️": "epee dague", "⚔️": "epees combat", "💣": "bombe",
    "🛡️": "bouclier", "🔧": "cle a molette", "🪛": "tournevis",
    "⚙️": "engrenage", "⚖️": "balance justice", "🧲": "aimant",
    "🪜": "echelle", "🔬": "microscope", "🔭": "telescope",
    "📡": "antenne satellite", "🩺": "stethoscope",
    "🩹": "pansement", "🩼": "bequille", "💊": "medicament pilule",
    "💉": "seringue vaccin", "🩸": "sang", "🧪": "tube essai",
    "🧫": "boite de petri", "🧵": "fil couture", "🧶": "laine",
    "🪡": "aiguille coudre", "🪢": "noeud corde", "🪪": "carte identite",
    "🎁": "cadeau", "🎈": "ballon", "🎀": "ruban noeud",
    "🛍️": "sacs shopping", "🛒": "caddie courses", "💎": "diamant joyau",
    "🔋": "batterie pile", "🔌": "prise electrique",
    "🪫": "batterie faible", "🧸": "ours en peluche",
    # --- Vetements ---
    "👔": "cravate costume", "👕": "t-shirt chemise",
    "👖": "jean pantalon", "🧥": "manteau veste",
    "🧦": "chaussettes", "🧤": "gants", "🧣": "echarpe",
    "👗": "robe", "👘": "kimono", "🩱": "maillot de bain",
    "👙": "maillot bikini", "🥽": "lunettes protection",
    "🥼": "blouse blanche laboratoire", "🦺": "gilet securite",
    "🪖": "casque militaire", "🕶️": "lunettes de soleil",
    "👜": "sac a main", "👝": "sac poche", "🎒": "sac a dos",
    "👛": "portefeuille sac", "🩴": "tongs", "👟": "baskets chaussure",
    "🥾": "bottines chaussure rando", "👡": "sandale",
    "👠": "talon chaussure", "👢": "botte",
    # --- Maison ---
    "🚪": "porte", "🪟": "fenetre", "🛏️": "lit",
    "🪑": "chaise", "🛋️": "canape", "🛗": "ascenseur",
    "🚽": "toilettes wc", "🚿": "douche", "🛁": "baignoire",
    "🪞": "miroir", "🧻": "papier hygienique", "🧼": "savon",
    "🧽": "eponge", "🧹": "balai", "🧺": "panier linge",
    "🪣": "seau", "🧴": "creme flacon", "🧷": "epingle",
    "🪥": "brosse a dents", "🪒": "rasoir", "🧯": "extincteur",
    "🪴": "plante verte",
    # --- Activites ---
    "⚽️": "ballon football", "🏀": "basket", "🎾": "tennis",
    "🏐": "volley", "🏉": "rugby", "🏓": "ping-pong",
    "🏸": "badminton", "🥊": "boxe gants", "🥋": "karate judo",
    "🛹": "skate", "🛼": "rollers", "⛸️": "patins glace",
    "🎿": "ski", "🏂": "snowboard", "🏋️": "halteres musculation",
    "🤸": "gymnastique", "🏄": "surf", "🏊": "natation",
    "🚣": "aviron", "🧗": "escalade", "🚴": "cyclisme",
    "🏆": "trophee coupe", "🥇": "medaille or premier",
    "🎭": "theatre masque", "🎨": "art peinture",
    "🎬": "cinema film clap", "🎤": "micro chanson",
    "🎧": "ecouteurs casque", "🎹": "piano", "🥁": "batterie tambour",
    "🎷": "saxophone", "🎺": "trompette", "🎸": "guitare",
    "🎻": "violon", "🎲": "de jeu hasard", "♟️": "echecs pion",
    "🎯": "cible", "🎳": "bowling", "🎮": "manette jeu video",
    "🧩": "puzzle", "🎰": "machine a sous",
    "🪩": "boule a facettes disco", "🛝": "toboggan",
    "🃏": "joker carte", "🪄": "baguette magique magie",
    "🎪": "chapiteau cirque", "🎫": "billet ticket",
    # --- Personnages ---
    "👋": "salut bonjour", "🤝": "poignee de main accord",
    "🙏": "merci prier", "💪": "muscle force",
    "👀": "yeux regarder", "🧠": "cerveau reflechir",
    "👶": "bebe", "👦": "garcon enfant", "👧": "fille enfant",
    "👨": "homme", "👩": "femme", "🧓": "personne agee",
    "👴": "grand-pere", "👵": "grand-mere", "👮": "policier",
    "🕵️": "detective espion", "🥷": "ninja", "👑": "couronne roi reine",
    "🦸": "super-heros", "🦹": "super-vilain", "🧙": "magicien sorcier",
    "🧚": "fee", "🧛": "vampire", "🧜": "sirene", "🧝": "elfe",
    "🧞": "genie", "🧟": "zombie", "🎅": "pere noel",
    "🤶": "mere noel", "👼": "ange", "💃": "danse",
    "🕺": "danse homme", "🤖": "robot", "👻": "fantome",
    "👽": "extraterrestre alien", "💀": "crane mort",
    "☠️": "crane tete de mort danger",
    # --- Symboles / temps ---
    "❤️": "coeur amour", "💔": "coeur brise rupture",
    "💕": "coeurs amour", "💖": "coeur brillant amour",
    "🔔": "cloche", "🎵": "musique note", "🎶": "musique",
    "⚠️": "attention danger", "🚫": "interdit",
    "⛔️": "interdit", "☢️": "radioactif",
    "🔮": "boule de cristal magie", "🌐": "globe monde",
    "⏰": "reveil alarme", "⏳️": "sablier temps",
    "⌛️": "sablier",
}

# =============================================================================
# ROUTES
# =============================================================================
@app.get("/")
async def root():
    return {
        "message": "🎭 Emoji Story Generator API",
        "version": "3.1.0",
        "docs": "/docs",
        "total_emojis": len(ALL_EMOJIS),
    }

@app.get("/emojis")
async def get_all_emojis():
    """Tous les émoticônes par catégorie + mots-clés FR (recherche)"""
    return {
        "total": len(ALL_EMOJIS),
        "categories": EMOJI_DATABASE,
        "keywords": EMOJI_KEYWORDS,
    }

@app.get("/emojis/random")
async def get_random_emojis():
    """6 émoticônes aléatoires"""
    return {"random": random.sample(ALL_EMOJIS, 6), "total_available": len(ALL_EMOJIS)}

@app.post("/emojis")
async def add_custom_emoji(request: EmojiAddRequest):
    """Ajoute un émoticône personnalisé"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO custom_emojis (emoji) VALUES (%s)", (request.emoji,))
        conn.commit()
        ALL_EMOJIS.append(request.emoji)
        return {"message": "Émoticône ajouté", "emoji": request.emoji}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return {"message": "Émoticône déjà présent", "emoji": request.emoji}
    finally:
        cur.close()
        conn.close()

@app.post("/stories")
async def create_story(request: EmojiStoryRequest):
    """Crée une histoire et déclenche le workflow n8n"""
    story_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO stories (id, emojis, theme, status, created_at) VALUES (%s, %s, %s, %s, %s)",
            (story_id, request.emojis, request.theme, "pending", created_at),
        )
        cur.execute(
            "INSERT INTO story_history (story_id, event, detail) VALUES (%s, %s, %s)",
            (story_id, "created", f"Histoire créée avec {len(request.emojis)} émoticônes"),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

    n8n_url = os.getenv("N8N_URL")
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{n8n_url}/webhook/generate-story",
                json={"story_id": story_id, "emojis": request.emojis, "theme": request.theme},
                timeout=10.0,
            )
        except httpx.HTTPError:
            pass  # n8n pas encore configuré : l'histoire reste en pending

    return {"story_id": story_id, "status": "pending", "created_at": created_at}

@app.get("/stories/{story_id}")
async def get_story(story_id: str):
    """Récupère une histoire et ses médias"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, emojis, theme, story_text, audio_url, image_url, created_at, status "
        "FROM stories WHERE id = %s",
        (story_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Histoire non trouvée")

    return {
        "story_id": row[0],
        "emojis": row[1],
        "theme": row[2],
        "story_text": row[3],
        "audio_url": row[4],
        "image_url": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
        "status": row[7],
    }

@app.get("/stories")
async def list_stories(limit: int = 50):
    """Galerie : dernières histoires créées (extrait du texte inclus)"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, emojis, theme, story_text, audio_url, image_url, created_at, status "
        "FROM stories ORDER BY created_at DESC LIMIT %s",
        (min(limit, 100),),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    gallery = []
    for row in rows:
        text = row[3] or ""
        gallery.append({
            "story_id": row[0],
            "emojis": row[1],
            "theme": row[2],
            "excerpt": text[:180] + "…" if len(text) > 180 else text,
            "audio_url": row[4],
            "image_url": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
            "status": row[7],
        })
    return {"total": len(gallery), "stories": gallery}

@app.delete("/stories/{story_id}")
async def delete_story(story_id: str):
    """Supprime une histoire : ligne SQL, historique et fichiers média"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM story_history WHERE story_id = %s", (story_id,))
        cur.execute("DELETE FROM stories WHERE id = %s", (story_id,))
        deleted = cur.rowcount
        conn.commit()
    finally:
        cur.close()
        conn.close()

    if not deleted:
        raise HTTPException(status_code=404, detail="Histoire non trouvée")

    # Suppression des fichiers média (échec non bloquant : le fichier peut
    # ne pas exister si l'image/l'audio n'avait pas encore été généré)
    for ext in (".jpg", ".mp3"):
        try:
            os.remove(f"/app/media/{story_id}{ext}")
        except OSError:
            pass

    return {"story_id": story_id, "deleted": True}

@app.patch("/stories/{story_id}")
async def update_story(story_id: str, request: StoryUpdateRequest):
    """Mise à jour interne appelée par n8n après chaque génération IA.

    Point clé de la v2 : n8n n'écrit PLUS directement dans PostgreSQL.
    Il appelle cette route ; l'API fait des requêtes paramétrées → les
    apostrophes et guillemets du texte français ne cassent plus rien.

    Extension (v2.3.2) : si l'histoire a déjà un texte et que le
    workflow n'envoie que la suite, on conserve le début -> l'histoire
    complète reste visible dans la galerie.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        if request.story_text is not None:
            cur.execute("SELECT story_text FROM stories WHERE id = %s", (story_id,))
            existing = cur.fetchone()
            if existing and existing[0]:
                prev = (existing[0] or "").strip()
                new = (request.story_text or "").strip()
                # Si le nouveau texte commence déjà par l'ancien, le
                # workflow a envoyé le récit complet : rien à concaténer.
                if new and not new.startswith(prev[:150]):
                    request.story_text = prev + "\n\n" + new

        updates = {}
        events = []
        if request.story_text is not None:
            updates["story_text"] = request.story_text
            events.append(("story_generated", "Texte généré par Mistral"))
        if request.audio_url is not None:
            updates["audio_url"] = request.audio_url
            events.append(("audio_ready", "Audio généré par ElevenLabs"))
        if request.image_url is not None:
            updates["image_url"] = request.image_url
            events.append(("image_ready", "Illustration générée par FLUX"))
        if request.status is not None:
            updates["status"] = request.status
        if not updates:
            raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

        # Noms de colonnes issus d'une liste blanche interne (jamais de l'entrée)
        set_clause = ", ".join(f"{col} = %s" for col in updates)
        values = list(updates.values()) + [story_id]

        cur.execute(
            f"UPDATE stories SET {set_clause}, updated_at = NOW() "
            "WHERE id = %s "
            "RETURNING id, emojis, theme, story_text, audio_url, image_url, created_at, status",
            values,
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Histoire non trouvée")
        for event, detail in events:
            cur.execute(
                "INSERT INTO story_history (story_id, event, detail) VALUES (%s, %s, %s)",
                (story_id, event, detail),
            )
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return {
        "story_id": row[0],
        "emojis": row[1],
        "theme": row[2],
        "story_text": row[3],
        "audio_url": row[4],
        "image_url": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
        "status": row[7],
    }

@app.post("/stories/{story_id}/extend")
async def extend_story(story_id: str, request: ExtendStoryRequest):
    """Fait évoluer l'histoire avec de nouveaux émoticônes"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT emojis, story_text, theme FROM stories WHERE id = %s", (story_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Histoire non trouvée")

    current_emojis, current_text, current_theme = row[0], row[1] or "", row[2]
    updated_emojis = current_emojis + request.new_emojis

    cur.execute(
        "UPDATE stories SET emojis = %s, status = 'extending', updated_at = NOW() WHERE id = %s",
        (updated_emojis, story_id),
    )
    cur.execute(
        "INSERT INTO story_history (story_id, event, detail) VALUES (%s, %s, %s)",
        (story_id, "extended", f"Ajout de {len(request.new_emojis)} émoticônes"),
    )
    conn.commit()
    cur.close()
    conn.close()

    n8n_url = os.getenv("N8N_URL")
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{n8n_url}/webhook/generate-story",
                json={
                    "story_id": story_id,
                    "emojis": updated_emojis,
                    "previous_text": current_text,
                    "theme": current_theme,
                    "is_extension": True,
                },
                timeout=10.0,
            )
        except httpx.HTTPError:
            pass

    return {"story_id": story_id, "status": "extending", "total_emojis": len(updated_emojis)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
