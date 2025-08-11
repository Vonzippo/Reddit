#!/bin/bash

echo "🔍 Filtere November 2024 Daten"
echo "==============================="

# Variablen für November
COMMENTS_IN="/Users/patrick/Desktop/Reddit Karma Farm/pushshift_dumps/reddit/november/RC_2024-11.zst"
POSTS_IN="/Users/patrick/Desktop/Reddit Karma Farm/pushshift_dumps/reddit/november/RS_2024-11.zst"
COMMENTS_OUT="/Users/patrick/Desktop/Reddit Karma Farm/pushshift_dumps/2024_filtered/RC_2024-11_filtered.jsonl"
POSTS_OUT="/Users/patrick/Desktop/Reddit Karma Farm/pushshift_dumps/2024_posts_filtered/RS_2024-11_filtered.jsonl"

# Prüfe ob Dateien existieren
if [ ! -f "$COMMENTS_IN" ]; then
    echo "❌ RC_2024-11.zst noch nicht heruntergeladen!"
    echo "   Warte bis Download fertig ist..."
    exit 1
fi

if [ ! -f "$POSTS_IN" ]; then
    echo "❌ RS_2024-11.zst noch nicht heruntergeladen!"
    echo "   Warte bis Download fertig ist..."
    exit 1
fi

echo "✅ Beide November-Dateien gefunden!"
echo ""

# Filtere Kommentare
echo "💬 Filtere November Kommentare..."
zstd -d -c "$COMMENTS_IN" | python3 -c "
import sys
import json

target_subs = {
    'adhd', 'adhdwomen', 'howtoadhd', 'adhdmemes', 'audhd',
    'adhduk', 'adultadhd', 'adhd_parenting', 'mentalhealth',
    'anxiety', 'depression', 'ocd', 'ptsd', 'cptsd',
    'socialanxiety', 'bipolar', 'autism', 'neurodiversity',
    'getdisciplined', 'productivity'
}

total = 0
filtered = 0

with open('$COMMENTS_OUT', 'w') as out:
    for line in sys.stdin:
        total += 1
        try:
            comment = json.loads(line.strip())
            subreddit = comment.get('subreddit', '').lower()
            
            if subreddit in target_subs:
                body = comment.get('body', '')
                if body not in ['[deleted]', '[removed]', '']:
                    out.write(line)
                    filtered += 1
        except:
            pass
        
        if total % 100000 == 0:
            print(f'Kommentare: {total:,} verarbeitet, {filtered:,} gefiltert', end='\r', file=sys.stderr)
    
    print(f'\n✓ November Kommentare: {total:,} total, {filtered:,} gefiltert', file=sys.stderr)
" &

# Filtere Posts parallel
echo "📝 Filtere November Posts..."
zstd -d -c "$POSTS_IN" | python3 -c "
import sys
import json

target_subs = {
    'adhd', 'adhdwomen', 'howtoadhd', 'adhdmemes', 'audhd',
    'adhduk', 'adultadhd', 'adhd_parenting', 'mentalhealth',
    'anxiety', 'depression', 'ocd', 'ptsd', 'cptsd',
    'socialanxiety', 'bipolar', 'autism', 'neurodiversity',
    'getdisciplined', 'productivity'
}

total = 0
filtered = 0

with open('$POSTS_OUT', 'w') as out:
    for line in sys.stdin:
        total += 1
        try:
            post = json.loads(line.strip())
            subreddit = post.get('subreddit', '').lower()
            
            if subreddit in target_subs:
                title = post.get('title', '')
                if title not in ['[deleted]', '[removed]', '']:
                    out.write(line)
                    filtered += 1
        except:
            pass
        
        if total % 10000 == 0:
            print(f'Posts: {total:,} verarbeitet, {filtered:,} gefiltert', end='\r', file=sys.stderr)
    
    print(f'\n✓ November Posts: {total:,} total, {filtered:,} gefiltert', file=sys.stderr)
" &

echo ""
echo "⏳ Beide Filterungen laufen parallel..."
echo "   Dies kann 10-20 Minuten dauern."
echo ""

# Warte auf beide Prozesse
wait

echo "✅ November-Filterung abgeschlossen!"
echo ""
echo "📊 Ergebnisse:"
ls -lh "$COMMENTS_OUT" "$POSTS_OUT" 2>/dev/null