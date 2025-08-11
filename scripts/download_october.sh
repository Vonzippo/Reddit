#!/bin/bash

echo "🎯 Starte Download Oktober 2024 (RC + RS)"
echo "=========================================="

# Erstelle Verzeichnis für Oktober
mkdir -p pushshift_dumps/reddit/october

# Download Oktober Kommentare (RC_2024-10)
echo "📥 Lade Oktober 2024 Kommentare (RC_2024-10)..."
echo "   Quelle: Academic Torrents"

# Oktober 2024 Torrent URL (enthält beide: RC und RS)
echo "📥 Lade Oktober 2024 Torrent (RC_2024-10 + RS_2024-10)..."
curl -L -o temp_october.torrent \
  "https://academictorrents.com/download/507dfcda29de9936dd77ed4f34c6442dc675c98f.torrent"

echo "📡 Starte Torrent-Download..."
echo "   Enthält: RC_2024-10.zst (Kommentare) + RS_2024-10.zst (Posts)"

# Check if aria2c is installed
if ! command -v aria2c &> /dev/null; then
    echo "❌ aria2c nicht installiert! Installiere mit:"
    echo "   brew install aria2"
    exit 1
fi

# Download mit aria2c (enthält beide Dateien im Torrent)
echo "⬇️  Starte Download (RC_2024-10.zst + RS_2024-10.zst)..."
aria2c --seed-time=0 \
       --max-connection-per-server=16 \
       --split=16 \
       --enable-dht=true \
       --file-allocation=none \
       --console-log-level=notice \
       --summary-interval=30 \
       --dir=pushshift_dumps/reddit/october \
       temp_october.torrent &

echo ""
echo "✅ Oktober-Download läuft im Hintergrund!"
echo ""
echo "📊 Überwache mit:"
echo "   ps aux | grep aria2c"
echo ""
echo "📁 Dateien werden gespeichert in:"
echo "   pushshift_dumps/reddit/october/"
echo ""
echo "🎯 Sobald fertig, filtere mit:"
echo "   bash scripts/filter_october.sh"
echo ""
echo "📊 Erwartete Dateien:"
echo "   - RC_2024-10.zst (Kommentare, ~15-20 GB)"
echo "   - RS_2024-10.zst (Posts, ~2-3 GB)"