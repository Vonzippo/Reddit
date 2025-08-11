#!/bin/bash

echo "📊 FILTERUNG LÄUFT..."
echo "===================="
echo ""

while true; do
    clear
    echo "📊 REDDIT DATEN FILTERUNG - LIVE STATUS"
    echo "========================================"
    echo ""
    
    # Kommentar-Status
    if [ -f filter_comments.log ]; then
        COMMENT_STATUS=$(tail -1 filter_comments.log)
        echo "💬 KOMMENTARE (RC_2024-12.zst):"
        echo "   $COMMENT_STATUS"
    else
        echo "💬 KOMMENTARE: Warte auf Start..."
    fi
    
    echo ""
    
    # Posts-Status
    if [ -f filter_posts.log ]; then
        POST_STATUS=$(tail -1 filter_posts.log)
        echo "📝 POSTS (RS_2024-12.zst):"
        echo "   $POST_STATUS"
    else
        echo "📝 POSTS: Warte auf Start..."
    fi
    
    echo ""
    echo "📁 OUTPUT DATEIEN:"
    
    # Prüfe Output-Dateien
    if [ -f pushshift_dumps/2024_filtered/RC_2024-12_filtered.jsonl ]; then
        COMMENT_SIZE=$(du -h pushshift_dumps/2024_filtered/RC_2024-12_filtered.jsonl | cut -f1)
        echo "   • Kommentare: $COMMENT_SIZE"
    fi
    
    if [ -f pushshift_dumps/2024_posts_filtered/RS_2024-12_filtered.jsonl ]; then
        POST_SIZE=$(du -h pushshift_dumps/2024_posts_filtered/RS_2024-12_filtered.jsonl | cut -f1)
        echo "   • Posts: $POST_SIZE"
    fi
    
    echo ""
    echo "⏱️  Aktualisiert: $(date '+%H:%M:%S')"
    echo ""
    echo "Drücke Ctrl+C zum Beenden"
    
    # Prüfe ob fertig
    if grep -q "FERTIG:" filter_comments.log 2>/dev/null && grep -q "FERTIG:" filter_posts.log 2>/dev/null; then
        echo ""
        echo "✅ BEIDE FILTERUNGEN ABGESCHLOSSEN!"
        break
    fi
    
    sleep 5
done