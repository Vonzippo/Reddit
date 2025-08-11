#!/bin/bash

echo "🎯 Starte Download September 2024 (RC + RS)"
echo "=========================================="

# Erstelle Verzeichnis für September
mkdir -p pushshift_dumps/reddit/september

# September 2024 Torrent URL (enthält beide: RC und RS)
echo "📥 Lade September 2024 Torrent (RC_2024-09 + RS_2024-09)..."
curl -L -o temp_september.torrent \
  "https://academictorrents.com/download/43a6e113d6ecacf38e58ecc6caa28d68892dd8af.torrent"

echo "📡 Starte Torrent-Download..."
echo "   Enthält: RC_2024-09.zst (Kommentare) + RS_2024-09.zst (Posts)"

# Check if aria2c is installed
if ! command -v aria2c &> /dev/null; then
    echo "❌ aria2c nicht installiert! Installiere mit:"
    echo "   brew install aria2"
    exit 1
fi

# Download mit aria2c (enthält beide Dateien im Torrent)
echo "⬇️  Starte Download (RC_2024-09.zst + RS_2024-09.zst)..."
aria2c --seed-time=0 \
       --max-connection-per-server=16 \
       --split=16 \
       --enable-dht=true \
       --file-allocation=none \
       --console-log-level=notice \
       --summary-interval=30 \
       --dir=pushshift_dumps/reddit/september \
       temp_september.torrent &

echo ""
echo "✅ September-Download läuft im Hintergrund!"
echo ""
echo "📊 Überwache mit:"
echo "   ps aux | grep aria2c"
echo ""
echo "📁 Dateien werden gespeichert in:"
echo "   pushshift_dumps/reddit/september/"
echo ""
echo "🎯 Sobald fertig, filtere mit:"
echo "   bash scripts/filter_september.sh"
echo ""
echo "📊 Erwartete Dateien:"
echo "   - RC_2024-09.zst (Kommentare, ~15-20 GB)"
echo "   - RS_2024-09.zst (Posts, ~2-3 GB)"