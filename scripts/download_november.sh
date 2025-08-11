#!/bin/bash

echo "🎯 Starte Download November 2024 (RC + RS)"
echo "=========================================="

# Erstelle Verzeichnis für November
mkdir -p pushshift_dumps/reddit/november

# Download November Torrent
echo "📥 Lade November 2024 Torrent..."
curl -L -o temp_november.torrent \
  "https://academictorrents.com/download/a1b490117808d9541ab9e3e67a3447e2f4f48f01.torrent"

echo "📡 Starte Torrent-Download..."
echo "   Enthält: RC_2024-11.zst (Kommentare) + RS_2024-11.zst (Posts)"

# Download mit aria2c
aria2c --seed-time=0 \
       --max-connection-per-server=16 \
       --split=16 \
       --enable-dht=true \
       --file-allocation=none \
       --console-log-level=notice \
       --summary-interval=30 \
       --dir=pushshift_dumps/reddit/november \
       temp_november.torrent &

echo ""
echo "✅ November-Download läuft im Hintergrund!"
echo ""
echo "📊 Überwache mit:"
echo "   ps aux | grep aria2c"
echo ""
echo "🎯 Sobald fertig, filtere mit:"
echo "   bash filter_november.sh"