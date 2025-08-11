#!/bin/bash
# Download latest month (December 2024) with aria2c

echo "🚀 Starte Download von Reddit Kommentaren Dezember 2024"
echo "=================================================="

# Erstelle Verzeichnisse
mkdir -p pushshift_dumps/2024_filtered
mkdir -p temp_torrents

# Download Torrent-Datei
echo "📥 Lade Torrent-Datei..."
curl -L -o temp_torrents/RC_2024-12.torrent \
  "https://academictorrents.com/download/eb2017da9f63a49460dde21a4ebe3b7c517f3ad9.torrent"

# Starte Download mit aria2c
echo "📡 Starte Torrent-Download (kann einige Zeit dauern)..."
echo "  Datei: RC_2024-12.zst (~15-20 GB)"
echo ""

aria2c --seed-time=0 \
       --max-connection-per-server=16 \
       --split=16 \
       --enable-dht=true \
       --file-allocation=none \
       --console-log-level=notice \
       --summary-interval=30 \
       --dir=pushshift_dumps \
       temp_torrents/RC_2024-12.torrent

echo "✅ Download abgeschlossen!"
echo "📁 Datei in: pushshift_dumps/"

# Prüfe ob Datei existiert
if [ -f "pushshift_dumps/RC_2024-12.zst" ]; then
    echo "✓ RC_2024-12.zst erfolgreich heruntergeladen"
    echo ""
    echo "🔍 Nächster Schritt: Filtere die Daten mit:"
    echo "   python3 filter_downloaded_data.py"
else
    echo "⚠️ Datei nicht gefunden. Prüfe pushshift_dumps/ Ordner"
fi