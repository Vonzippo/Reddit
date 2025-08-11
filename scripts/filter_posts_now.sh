#!/bin/bash

echo "🎯 Filtere Reddit POSTS für deine Subreddits"
echo "============================================"

# Variablen
INPUT_FILE="/Users/patrick/Desktop/Reddit Karma Farm/pushshift_dumps/reddit/submissions/RS_2024-12.zst"
OUTPUT_DIR="/Users/patrick/Desktop/Reddit Karma Farm/pushshift_dumps/2024_posts_filtered"
OUTPUT_FILE="$OUTPUT_DIR/RS_2024-12_filtered.jsonl"

# Erstelle Output-Verzeichnis
mkdir -p "$OUTPUT_DIR"

# Zeige Dateigröße
echo ""
echo "📊 Input-Datei: RS_2024-12.zst"
echo "   Größe: $(du -h "$INPUT_FILE" | cut -f1)"
echo ""
echo "🎯 Filtere für 20 Subreddits..."
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
            post = json.loads(line.strip())
            subreddit = post.get('subreddit', '').lower()
            
            if subreddit in target_subs:
                title = post.get('title', '')
                # Überspringe gelöschte/entfernte
                if title not in ['[deleted]', '[removed]', '']:
                    out.write(line)
                    filtered += 1
        except:
            pass
        
        if total % 10000 == 0:
            print(f'  Verarbeitet: {total:,} Posts | Gefiltert: {filtered:,}', end='\r', file=sys.stderr)
    
    print(f'\n✓ Fertig: {total:,} total, {filtered:,} gefiltert', file=sys.stderr)
"

echo ""
echo "📏 Ergebnis:"
echo "   Gefilterte Datei: $OUTPUT_FILE"
echo "   Größe: $(du -h "$OUTPUT_FILE" | cut -f1)"

echo ""
echo "✅ Posts fertig!"
echo ""
echo "🎯 Nächster Schritt: Extrahiere Top 1000"
echo "   python3 extract_top_content.py"