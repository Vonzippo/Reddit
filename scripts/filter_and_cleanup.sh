#!/bin/bash

echo "🚀 Filtere Reddit Kommentare für deine Subreddits"
echo "=================================================="

# Variablen
INPUT_FILE="/Users/patrick/Desktop/Reddit Karma Farm/pushshift_dumps/reddit/comments/RC_2024-12.zst"
OUTPUT_DIR="/Users/patrick/Desktop/Reddit Karma Farm/pushshift_dumps/2024_filtered"
OUTPUT_FILE="$OUTPUT_DIR/RC_2024-12_filtered.jsonl"

# Erstelle Output-Verzeichnis
mkdir -p "$OUTPUT_DIR"

# Zeige Dateigröße
echo ""
echo "📊 Input-Datei: RC_2024-12.zst"
echo "   Größe: $(du -h "$INPUT_FILE" | cut -f1)"
echo ""
echo "🎯 Filtere für 20 Subreddits..."
echo "   Dies kann 10-30 Minuten dauern..."
echo ""

# Filtere mit Python während Dekompression
zstd -d -c "$INPUT_FILE" | python3 -c "
import sys
import json

# Target Subreddits (kleingeschrieben)
target_subs = {
    'adhd', 'adhdwomen', 'howtoadhd', 'adhdmemes', 'audhd',
    'adhduk', 'adultadhd', 'adhd_parenting', 'mentalhealth',
    'anxiety', 'depression', 'ocd', 'ptsd', 'cptsd',
    'socialanxiety', 'bipolar', 'autism', 'neurodiversity',
    'getdisciplined', 'productivity'
}

total = 0
filtered = 0

with open('$OUTPUT_FILE', 'w') as out:
    for line in sys.stdin:
        total += 1
        try:
            comment = json.loads(line.strip())
            subreddit = comment.get('subreddit', '').lower()
            
            if subreddit in target_subs:
                body = comment.get('body', '')
                # Überspringe gelöschte/entfernte
                if body not in ['[deleted]', '[removed]', '']:
                    out.write(line)
                    filtered += 1
        except:
            pass
        
        if total % 100000 == 0:
            print(f'  Verarbeitet: {total:,} | Gefiltert: {filtered:,}', end='\r', file=sys.stderr)
    
    print(f'\n✓ Fertig: {total:,} total, {filtered:,} gefiltert', file=sys.stderr)
"

echo ""
echo "📏 Ergebnis:"
echo "   Gefilterte Datei: $OUTPUT_FILE"
echo "   Größe: $(du -h "$OUTPUT_FILE" | cut -f1)"

echo ""
echo "🗑️ Lösche große Original-Datei um Platz zu sparen..."
read -p "   Wirklich löschen? (j/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Jj]$ ]]; then
    rm -f "$INPUT_FILE"
    echo "   ✓ Original gelöscht, $(du -h "$INPUT_FILE" 2>/dev/null | cut -f1 || echo '32 GB') gespart!"
else
    echo "   ℹ️ Original behalten"
fi

echo ""
echo "✅ Kommentare fertig!"
echo ""
echo "🎯 Nächster Schritt: Filtere die Posts"
echo "   bash filter_posts_now.sh"