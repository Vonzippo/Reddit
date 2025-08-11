#!/bin/bash

echo "📊 Oktober Download Monitor"
echo "================================"

while true; do
    clear
    echo "📊 Oktober 2024 Download Status"
    echo "================================"
    echo ""
    
    # Zeige aria2c Prozesse
    echo "🔄 Download-Prozesse:"
    ps aux | grep aria2c | grep -v grep || echo "   Keine aktiven Downloads"
    echo ""
    
    # Zeige Dateigrößen
    echo "📁 Heruntergeladene Dateien:"
    if [ -d "pushshift_dumps/reddit/october" ]; then
        ls -lh pushshift_dumps/reddit/october/reddit/comments/ 2>/dev/null | grep -E "RC_2024-10" || echo "   RC_2024-10.zst noch nicht vorhanden"
        ls -lh pushshift_dumps/reddit/october/reddit/submissions/ 2>/dev/null | grep -E "RS_2024-10" || echo "   RS_2024-10.zst noch nicht vorhanden"
    else
        echo "   Verzeichnis noch nicht erstellt"
    fi
    echo ""
    
    # Zeige Speicherplatz
    echo "💾 Speicherplatz:"
    df -h . | tail -1
    echo ""
    
    echo "⏱️  Aktualisierung alle 10 Sekunden (Strg+C zum Beenden)"
    sleep 10
done