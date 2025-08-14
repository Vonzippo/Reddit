# Reddit 2024 Daten Download Guide

## Übersicht
Dieses Projekt benötigt Reddit-Kommentardaten aus 2024 für die gewählten Subreddits. Die Daten werden gefiltert, sodass nur die relevanten Kommentare gespeichert werden.

## Deine Ziel-Subreddits (20 Stück)
- ADHD, ADHDwomen, HowToADHD, ADHDmemes, AuDHD, ADHDUK, AdultADHD, ADHD_Parenting
- mentalhealth, Anxiety, depression, OCD, PTSD, CPTSD, SocialAnxiety, bipolar
- autism, neurodiversity, GetDisciplined, productivity

## Dateigrössen
- **Unkomprimiert pro Monat**: ~15-20 GB
- **Nach Filterung für deine Subreddits**: ~100-150 MB pro Monat
- **Ganzes Jahr gefiltert**: ~1.5-2 GB

## Option 1: Automatischer Download mit Filterung (Empfohlen)

### Schritt 1: Tools installieren
```bash
# Installiere benötigte Tools
brew install curl zstd
```

### Schritt 2: Download-Skript ausführen
```bash
# Führe das optimierte Download-Skript aus
python3 download_with_filter.py
```

Das Skript:
- Lädt Daten direkt herunter
- Filtert während des Downloads (spart Speicherplatz)
- Speichert nur Kommentare aus deinen Subreddits
- Zeigt Fortschritt und Statistiken

## Option 2: Torrent Download (für grössere Datenmengen)

### Schritt 1: Torrent Client installieren
```bash
# Option A: qBittorrent (GUI)
brew install --cask qbittorrent

# Option B: aria2 (Command Line)
brew install aria2
```

### Schritt 2: Arctic Shift Torrents
1. Gehe zu: https://github.com/ArthurHeitmann/arctic_shift
2. Scrolle zum "Torrents" Abschnitt
3. Lade die .torrent Dateien für gewünschte Monate (z.B. RC_2024-10.torrent)

### Schritt 3: Mit aria2 herunterladen und filtern
```bash
# Download mit aria2 und direkter Filterung
aria2c --seed-time=0 RC_2024-10.torrent

# Während des Downloads in anderem Terminal filtern:
zstd -d -c RC_2024-10.zst | \
  grep -E '"subreddit":"(ADHD|ADHDwomen|anxiety|depression)"' > \
  filtered_october.jsonl
```

## Option 3: Direkte Downloads (falls verfügbar)

### Mögliche Quellen:
1. **The Eye Archive**: https://the-eye.eu/redarcs/
2. **Academic Torrents**: https://academictorrents.com/
3. **Arctic Shift Direct**: Check GitHub releases

### Download mit curl:
```bash
# Beispiel für Oktober 2024
curl -L https://the-eye.eu/redarcs/files/RC_2024-10.zst | \
  zstd -d -c | \
  python3 -c "
import sys, json
subs = ['adhd','adhdwomen','anxiety','depression']
for line in sys:
    try:
        c = json.loads(line)
        if c.get('subreddit','').lower() in subs:
            print(line.strip())
    except: pass
" > october_filtered.jsonl
```

## Speicherplatz-Tipps

### Streaming-Filterung (empfohlen)
- Lädt und filtert gleichzeitig
- Benötigt nur Platz für gefilterte Daten
- ~150 MB statt 20 GB pro Monat

### Batch-Processing
- Lade einen Monat
- Filtere die Daten
- Lösche Original
- Fahre mit nächstem Monat fort

## Verarbeitung der Daten

Nach dem Download:
```bash
# Prüfe heruntergeladene Daten
ls -lh pushshift_dumps/2024_filtered/

# Zähle Kommentare
wc -l pushshift_dumps/2024_filtered/*.jsonl

# Teste mit dem Bot
python3 src/bot.py
```

## Fehlerbehebung

### "Datei nicht gefunden"
- Arctic Shift aktualisiert URLs regelmässig
- Prüfe GitHub für aktuelle Links

### "Nicht genug Speicherplatz"
- Nutze Streaming-Filterung
- Lade nur einzelne Monate

### "Download zu langsam"
- Versuche andere Quelle
- Lade ausserhalb Stosszeiten
- Nutze Torrents mit mehreren Peers

## Wichtige Hinweise
- Respektiere die Nutzungsbedingungen
- Lösche Originaldaten nach Filterung
- Sichere gefilterte Daten regelmässig