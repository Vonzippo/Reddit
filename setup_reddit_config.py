#!/usr/bin/env python3
"""
Interaktives Setup für Reddit API Verbindung
Hilft beim Erstellen der config.py
"""

import os
import sys
from pathlib import Path

print("🤖 REDDIT BOT SETUP")
print("="*50)
print("Dieses Skript hilft dir, die Reddit API Verbindung einzurichten.\n")

# Prüfe ob config.py bereits existiert
config_file = Path("config.py")
if config_file.exists():
    overwrite = input("⚠️  config.py existiert bereits. Überschreiben? (j/n): ").lower()
    if overwrite != 'j':
        print("❌ Setup abgebrochen.")
        sys.exit(0)

print("\n📝 SCHRITT 1: Reddit App erstellen")
print("-"*40)
print("1. Gehe zu: https://www.reddit.com/prefs/apps")
print("2. Klicke 'Create App' oder 'Create Another App'")
print("3. Wähle 'script' als App-Typ")
print("4. Redirect URI: http://localhost:8080")
print("\n✅ Drücke Enter wenn du die App erstellt hast...")
input()

print("\n🔑 SCHRITT 2: Credentials eingeben")
print("-"*40)
print("Kopiere die Werte von deiner Reddit App:\n")

# Client ID eingeben
print("CLIENT ID (kurze ID unter 'personal use script'):")
client_id = input("➤ ").strip()
if not client_id:
    print("❌ Client ID darf nicht leer sein!")
    sys.exit(1)

# Client Secret eingeben
print("\nCLIENT SECRET (langer String nach 'secret:'):")
client_secret = input("➤ ").strip()
if not client_secret:
    print("❌ Client Secret darf nicht leer sein!")
    sys.exit(1)

# Username eingeben
print("\nREDDIT USERNAME (ohne u/):")
username = input("➤ ").strip()
if username.startswith("u/"):
    username = username[2:]
if not username:
    print("❌ Username darf nicht leer sein!")
    sys.exit(1)

# Passwort eingeben
print("\nREDDIT PASSWORT:")
print("(Wenn du 2FA hast, nutze ein App-Passwort!)")
password = input("➤ ").strip()
if not password:
    print("❌ Passwort darf nicht leer sein!")
    sys.exit(1)

# User Agent generieren
user_agent = f"python:reddit-bot:v1.0 (by /u/{username})"

# Config erstellen
config_content = f'''# Reddit API Configuration
# WICHTIG: Diese Datei NIEMALS in Git committen!

ACTIVE_CONFIG = {{
    "client_id": "{client_id}",
    "client_secret": "{client_secret}",
    "username": "{username}",
    "password": "{password}",
    "user_agent": "{user_agent}"
}}

# Backup Config (optional)
BACKUP_CONFIG = {{
    "client_id": "",
    "client_secret": "",
    "username": "",
    "password": "",
    "user_agent": ""
}}
'''

# Speichern
print("\n💾 Speichere config.py...")
with open("config.py", "w") as f:
    f.write(config_content)

print("✅ config.py erstellt!")

# Teste Verbindung
print("\n🔌 Teste Reddit-Verbindung...")
try:
    import praw
    from config import ACTIVE_CONFIG
    
    reddit = praw.Reddit(
        client_id=ACTIVE_CONFIG["client_id"],
        client_secret=ACTIVE_CONFIG["client_secret"],
        user_agent=ACTIVE_CONFIG["user_agent"],
        username=ACTIVE_CONFIG["username"],
        password=ACTIVE_CONFIG["password"]
    )
    
    user = reddit.user.me()
    print(f"✅ Erfolgreich verbunden als: u/{user.name}")
    print(f"   Link Karma: {user.link_karma}")
    print(f"   Comment Karma: {user.comment_karma}")
    
    print("\n🎉 SETUP ERFOLGREICH!")
    print("Du kannst jetzt die Bots nutzen:")
    print("  python3 auto_post_comment_bot.py")
    print("  python3 main_other.py")
    
except ImportError:
    print("⚠️  PRAW nicht installiert!")
    print("Führe aus: pip install praw")
    
except Exception as e:
    print(f"❌ Verbindungsfehler: {e}")
    print("\n📝 Mögliche Ursachen:")
    print("  1. Client ID oder Secret falsch kopiert")
    print("  2. Username oder Passwort falsch")
    print("  3. 2FA aktiviert aber normales Passwort verwendet")
    print("  4. Reddit API temporär nicht erreichbar")
    print("\nPrüfe deine Eingaben in config.py")

# Gitignore
gitignore = Path(".gitignore")
if gitignore.exists():
    with open(".gitignore", "r") as f:
        content = f.read()
    if "config.py" not in content:
        print("\n⚠️  config.py zu .gitignore hinzufügen? (j/n): ", end="")
        if input().lower() == 'j':
            with open(".gitignore", "a") as f:
                f.write("\n# Reddit API Config\nconfig.py\n")
            print("✅ config.py zu .gitignore hinzugefügt")