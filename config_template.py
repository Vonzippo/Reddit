"""
Reddit Bot Konfiguration - TEMPLATE
Kopiere diese Datei zu config.py und fülle deine echten Daten ein!
"""

# Reddit API Credentials - FÜLLE DIESE AUS!
REDDIT_CONFIG = {
    "client_id": "DEINE_CLIENT_ID_HIER",        # z.B. "HaZ8i53jCT_u2k..."
    "client_secret": "DEIN_CLIENT_SECRET_HIER",  # z.B. "IbKUPkTXuT3efI..."
    "username": "DEIN_REDDIT_USERNAME",          # z.B. "ReddiBoto"
    "password": "DEIN_REDDIT_PASSWORT",          # Dein Reddit Account Passwort
    "user_agent": "bot:v1.0 (by /u/DEIN_USERNAME)"  # Ersetze DEIN_USERNAME
}

# Zweiter Account (optional - für Account-Wechsel)
REDDIT_CONFIG_ALT = {
    "client_id": "ALTERNATIVE_CLIENT_ID",
    "client_secret": "ALTERNATIVES_SECRET",
    "username": "AlternativerUsername",
    "password": "AlternativesPasswort",
    "user_agent": "bot:v1.0 (by /u/AlternativerUsername)"
}

# OpenRouter API (für AI Features)
# Bekomme deinen Key auf: https://openrouter.ai/keys
OPENROUTER_API_KEY = "sk-or-v1-DEIN_OPENROUTER_KEY_HIER"

# Bot Settings
BOT_SETTINGS = {
    "daily_post_limit": [1, 4],      # Min, Max Posts pro Tag
    "daily_comment_limit": [5, 20],   # Min, Max Kommentare pro Tag
    "pause_day_chance": 0.15,         # 15% Chance für Pausentag
    "min_post_delay": 1800,           # 30 Minuten
    "max_post_delay": 7200,           # 2 Stunden
    "min_comment_delay": 120,         # 2 Minuten
    "max_comment_delay": 420,         # 7 Minuten
}

# Target Subreddits (kannst du anpassen)
TARGET_SUBREDDITS = [
    "ADHD", "ADHDmemes", "adhdwomen", "AdultADHD",
    "GetDisciplined", "productivity", "selfimprovement",
    "mentalhealth", "Anxiety", "depression_help",
    "CasualConversation", "offmychest", "TrueOffMyChest",
    "jobs", "WorkReform", "careerguidance",
    "WritingPrompts", "ArtTherapy", "crafts"
]

# Aktiven Account wählen
import os
USE_ALT_ACCOUNT = os.environ.get('USE_ALT_ACCOUNT', 'false').lower() == 'true'
ACTIVE_CONFIG = REDDIT_CONFIG_ALT if USE_ALT_ACCOUNT else REDDIT_CONFIG

"""
ANLEITUNG:
==========

1. REDDIT API KEYS BEKOMMEN:
   - Gehe zu: https://www.reddit.com/prefs/apps
   - Klicke "Create App" 
   - Wähle "script" als App Type
   - Redirect URI: http://localhost:8080
   - Nach Erstellung kopiere Client ID und Secret

2. OPENROUTER API KEY:
   - Gehe zu: https://openrouter.ai/keys
   - Erstelle einen Account (kostenlos)
   - Generiere einen API Key
   - Kopiere den Key (beginnt mit sk-or-v1-)

3. DIESE DATEI NUTZEN:
   - Benenne diese Datei um zu: config.py
   - Fülle alle DEINE_XXX Platzhalter aus
   - Speichere die Datei

4. SICHERHEIT:
   - config.py ist in .gitignore
   - Teile diese Datei NIEMALS öffentlich!
   - Committe sie NICHT zu Git!

5. TESTEN:
   python3 -c "from config import ACTIVE_CONFIG; print('✅ Config funktioniert!')"
"""