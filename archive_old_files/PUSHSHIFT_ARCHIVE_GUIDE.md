# Pushshift Archive Integration Guide

## Übersicht
Da die Pushshift API seit 2023 nicht mehr verfügbar ist, nutzt dieses System jetzt historische Pushshift-Dumps um hochbewertete Reddit-Posts zu finden.

## Setup

### 1. Pushshift Dumps herunterladen

Download von Academic Torrents:

- **Komplettarchiv (2005-2023)**: 
  https://academictorrents.com/details/9c263fc85366c1ef8f5bb9da0203f4c8c8db75f4
  
- **Top 40.000 Subreddits**: 
  https://academictorrents.com/details/7c0645c94321311bb05bd879ddee4d0eba08aaee

### 2. Verzeichnisstruktur

Erstelle einen `pushshift_dumps` Ordner im Projekt:

```bash
mkdir pushshift_dumps
```

Platziere die heruntergeladenen `.zst` Dateien dort:

```
Reddit Karma Farm/
├── pushshift_dumps/
│   ├── reddit_submissions_2022-01.zst
│   ├── reddit_submissions_2022-02.zst
│   └── ...
└── src/
```

### 3. Abhängigkeiten installieren

```bash
pipenv install zstandard
```

## Verwendung

Das System sucht automatisch in den Archive-Dumps nach Posts mit Score ≥ 5000:

1. **Automatisch**: Der Bot verwendet jetzt die Archive statt der API
2. **Manuell**: Du kannst auch direkt mit der Archive-Klasse arbeiten:

```python
from apis.pushshift_archive import PushshiftArchive

archive = PushshiftArchive('./pushshift_dumps')
high_score_posts = archive.get_high_score_posts(subreddit='funny', limit=100)
```

## Features

- Filtert automatisch Posts mit Score ≥ 5000
- Ignoriert gelöschte Posts und Autoren
- Unterstützt Subreddit-spezifische Suche
- Kann nach Jahr filtern

## Tipps

- Du musst nicht alle Dumps herunterladen - nur die Subreddits die dich interessieren
- Die Dateien sind groß (mehrere GB) - stelle sicher, dass du genug Speicherplatz hast
- Das erste Laden kann etwas dauern, da die komprimierten Dateien gelesen werden müssen

## Konfiguration

Um den Archive-Pfad zu ändern, bearbeite `pushshift_archive.py`:

```python
self.archive_path = Path("/dein/pfad/zu/dumps")
```