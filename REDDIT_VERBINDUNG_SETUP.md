# 🔌 Reddit-Verbindung initialisieren

## 📝 Schritt 1: Reddit App erstellen

1. Gehe zu: https://www.reddit.com/prefs/apps
2. Scrolle runter und klicke **"Create App"** oder **"Create Another App"**
3. Fülle aus:
   - **Name**: `MeinBot` (oder beliebig)
   - **App type**: `script` ✅ (WICHTIG!)
   - **Description**: Optional
   - **About URL**: Leer lassen
   - **Redirect URI**: `http://localhost:8080` (egal was, wird nicht genutzt)
4. Klicke **"Create app"**

## 🔑 Schritt 2: Credentials kopieren

Nach dem Erstellen siehst du:
```
personal use script
MeinBot
by u/DeinUsername

[HIER_IST_DEINE_CLIENT_ID]
secret: [HIER_IST_DEIN_CLIENT_SECRET]
```

- **CLIENT_ID**: Die kurze ID direkt unter "personal use script"
- **CLIENT_SECRET**: Der lange String nach "secret:"

## 📄 Schritt 3: config.py erstellen

Erstelle eine Datei `config.py`:

```python
# config.py
ACTIVE_CONFIG = {
    "client_id": "abc123XYZ789",  # Deine Client ID (kurz)
    "client_secret": "AbC123-geheim_key_hier",  # Dein Secret (lang)
    "username": "DeinRedditUsername",  # Dein Reddit Username (ohne u/)
    "password": "DeinRedditPasswort",  # Dein Reddit Passwort
    "user_agent": "python:mein-bot:v1.0 (by /u/DeinUsername)"
}
```

## ✅ Schritt 4: Verbindung testen

```python
# test_connection.py
import praw
from config import ACTIVE_CONFIG

# Verbindung initialisieren
reddit = praw.Reddit(
    client_id=ACTIVE_CONFIG["client_id"],
    client_secret=ACTIVE_CONFIG["client_secret"],
    user_agent=ACTIVE_CONFIG["user_agent"],
    username=ACTIVE_CONFIG["username"],
    password=ACTIVE_CONFIG["password"]
)

# Testen
try:
    user = reddit.user.me()
    print(f"✅ Verbunden als: u/{user.name}")
    print(f"   Karma: {user.link_karma + user.comment_karma}")
except Exception as e:
    print(f"❌ Fehler: {e}")
```

## 🚨 Häufige Fehler

### 1. "401 Unauthorized"
- **Client ID** oder **Secret** falsch
- Nochmal von Reddit App kopieren

### 2. "invalid_grant"
- **Username** oder **Passwort** falsch
- Ohne "u/" beim Username!

### 3. "received 403 HTTP response"
- Account gesperrt oder zu neu
- 2FA aktiviert? Dann App-Passwort nötig!

### 4. ImportError
- `pip install praw` ausführen

## 🔐 Für 2FA (Two-Factor Authentication)

Wenn du 2FA aktiviert hast:
1. Gehe zu: https://www.reddit.com/prefs/apps/
2. Erstelle ein **App-Passwort**
3. Nutze dieses statt deinem normalen Passwort

## 📱 Für PythonAnywhere

1. Upload `config.py` zu `/home/lucawahl/Reddit/`
2. Stelle sicher dass die Pfade stimmen
3. Teste mit:
```bash
cd /home/lucawahl/Reddit
python3 -c "from config import ACTIVE_CONFIG; print('✅ Config geladen')"
```

## 🎯 Beispiel funktionierende config.py

```python
ACTIVE_CONFIG = {
    "client_id": "a1B2c3D4e5F6g7",
    "client_secret": "xYz123-ABC_def456GHI789jkl",
    "username": "ReddiBoto",  # OHNE u/
    "password": "MeinSicheresPasswort123",
    "user_agent": "python:adhd-bot:v1.0 (by /u/ReddiBoto)"
}
```

## ⚠️ WICHTIG

- **NIEMALS** config.py in Git committen!
- Füge `config.py` zu `.gitignore` hinzu
- Behalte Credentials **privat**!

## 🧪 Quick Test

```bash
python3 -c "
import praw
from config import ACTIVE_CONFIG

reddit = praw.Reddit(**ACTIVE_CONFIG)
print(f'✅ Verbunden als: {reddit.user.me().name}')
"
```

Wenn das funktioniert, ist alles richtig eingerichtet!