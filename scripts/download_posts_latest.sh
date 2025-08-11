#!/bin/bash
# Download Posts (RS = Reddit Submissions) für Dezember 2024

echo "🎯 Reddit POSTS Download (Dezember 2024)"
echo "========================================"
echo ""
echo "📌 INFO: Der Torrent enthält BEIDE Dateien:"
echo "  • RC_2024-12.zst - Kommentare (~15 GB)"
echo "  • RS_2024-12.zst - Posts (~2 GB) ← Das brauchen wir!"
echo ""

# Erstelle Verzeichnisse
mkdir -p pushshift_dumps/posts
mkdir -p temp_torrents

# Download Torrent-Datei (enthält Comments UND Posts)
echo "📥 Lade Torrent-Datei..."
curl -L -o temp_torrents/Reddit_2024-12.torrent \
  "https://academictorrents.com/download/eb2017da9f63a49460dde21a4ebe3b7c517f3ad9.torrent"

# Selektiver Download nur für RS (Posts) Datei
echo "📡 Starte Download NUR für Posts (RS_2024-12.zst)..."
echo "  ⏳ Dies kann 10-30 Minuten dauern..."

# aria2c mit Datei-Selektion
aria2c --seed-time=0 \
       --select-file=*RS_2024* \
       --max-connection-per-server=16 \
       --split=16 \
       --enable-dht=true \
       --file-allocation=none \
       --console-log-level=notice \
       --dir=pushshift_dumps/posts \
       temp_torrents/Reddit_2024-12.torrent

echo ""
echo "✅ Download abgeschlossen!"

# Prüfe Dateien
if [ -f "pushshift_dumps/posts/RS_2024-12.zst" ]; then
    SIZE=$(du -h pushshift_dumps/posts/RS_2024-12.zst | cut -f1)
    echo "✓ RS_2024-12.zst heruntergeladen ($SIZE)"
    echo ""
    echo "🎯 Nächster Schritt:"
    echo "   python3 filter_posts.py"
else
    echo "⚠️ Posts-Datei nicht gefunden"
    echo "  Prüfe pushshift_dumps/posts/ Ordner"
fi
