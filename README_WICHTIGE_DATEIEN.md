# 🤖 Reddit Bot - Wichtige Dateien

## 📁 Hauptordner aufgeräumt!
Von **47** auf **9** Python-Dateien reduziert. Alle alten Dateien sind in `archive_old_files/` gesichert.

## ✅ AKTIVE BOTS (Die wichtigsten!)

### 1. **auto_post_comment_bot.py** (NEU - EMPFOHLEN!)
- Vollautomatischer Bot für Posts & Kommentare
- **Limits**: Max 2 Posts, 2-5 Kommentare pro Tag
- Läuft komplett selbstständig
- Lokale Version

### 2. **auto_post_comment_bot_pythonanywhere.py** 
- Gleicher Bot für PythonAnywhere
- Angepasste Pfade für Server

### 3. **main_other.py**
- Kombinierter Bot mit Menü
- Posts & Kommentare mit manueller Kontrolle
- Verbesserte Kommentar-Generierung (kein negatives Karma mehr!)

### 4. **kommentare_bot.py**
- Nur Kommentare (kein Posten)
- ADHD-fokussierte Kommentare
- Ohne Tageslimit

## 📋 KONFIGURATION

- **config.py** - Deine Reddit API Credentials
- **config_template.py** - Vorlage für neue Configs

## 📂 DATEN

- **data_all/** - Alle Posts zum Reposten
- **target_subreddits.txt** - ADHD-Subreddits
- **blacklist_subreddits.txt** - Gesperrte Subreddits
- **safe_active_subreddits.txt** - Sichere Subreddits

## 🗂️ ARCHIV

- **archive_old_files/** - Alle alten Dateien
  - `/filter_scripts` - Alte Filter
  - `/old_bots` - Alte Bot-Versionen
  - `/test_files` - Test-Skripte
  - `/scripts` - Utilities

## 🚀 VERWENDUNG

```bash
# Empfohlen: Vollautomatisch
python3 auto_post_comment_bot.py

# Auf PythonAnywhere
python3 auto_post_comment_bot_pythonanywhere.py

# Mit Menü (manuell)
python3 main_other.py
```

## ⚙️ EINSTELLUNGEN

Alle Bots haben jetzt:
- **Max 2 Posts pro Tag**
- **Max 2-5 Kommentare pro Tag**
- Verbesserte ADHD-fokussierte Kommentare
- Natürliche Wartezeiten

---
Stand: 14.08.2025