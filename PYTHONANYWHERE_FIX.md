# 🔧 FIX: Reddit-Verbindungsfehler auf PythonAnywhere

## ❌ Fehlermeldung
```
❌ Fehler beim Posten: 'AutoPostCommentBot' object has no attribute 'reddit'
```

## 🎯 Ursache
Die Reddit-Verbindung konnte nicht hergestellt werden, wahrscheinlich weil:
1. **config.py** fehlt oder ist fehlerhaft
2. Import-Fehler beim Laden der Credentials

## ✅ LÖSUNG

### 1. Prüfe config.py auf PythonAnywhere

```bash
cd /home/lucawahl/Reddit
ls -la config.py
```

Falls nicht vorhanden, erstelle sie:

```python
# config.py
ACTIVE_CONFIG = {
    "client_id": "DEIN_CLIENT_ID",
    "client_secret": "DEIN_CLIENT_SECRET",
    "username": "DEIN_USERNAME",
    "password": "DEIN_PASSWORD",
    "user_agent": "python:reddit-bot:v1.0 (by /u/DEIN_USERNAME)"
}
```

### 2. Teste die Verbindung

Führe diesen Test aus:

```bash
python3 test_reddit_connection.py
```

### 3. Update auto_post_comment_bot_pythonanywhere.py

Die neue Version hat bessere Fehlerbehandlung:
- Prüft ob Reddit-Verbindung existiert
- Stoppt Bot wenn keine Verbindung
- Zeigt klare Fehlermeldungen

### 4. Alternative: Hardcode Credentials (NUR FÜR TEST!)

Falls config.py nicht funktioniert, kannst du temporär die Credentials direkt einfügen:

```python
def _init_reddit_connection(self):
    """Initialisiert die Reddit-Verbindung"""
    try:
        self.reddit = praw.Reddit(
            client_id="DEIN_CLIENT_ID_HIER",
            client_secret="DEIN_SECRET_HIER",
            username="DEIN_USERNAME",
            password="DEIN_PASSWORD",
            user_agent="python:bot:v1.0"
        )
```

⚠️ **WICHTIG**: Nie Credentials in öffentlichen Repos!

## 📝 Checkliste

- [ ] config.py existiert in `/home/lucawahl/Reddit/`
- [ ] Alle 5 Credentials sind ausgefüllt
- [ ] Keine Tippfehler in den Credentials
- [ ] Username/Password sind korrekt
- [ ] Client ID/Secret vom Reddit App Dashboard

## 🔍 Debug-Tipp

Füge diesen Debug-Code am Anfang von `_init_reddit_connection()` ein:

```python
print("🔍 DEBUG: Versuche config.py zu laden...")
try:
    from config import ACTIVE_CONFIG
    print("✅ config.py geladen")
    print(f"   Keys gefunden: {list(ACTIVE_CONFIG.keys())}")
except Exception as e:
    print(f"❌ config.py Fehler: {e}")
    return False
```

Das zeigt genau wo das Problem liegt!