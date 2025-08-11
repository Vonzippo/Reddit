#!/usr/bin/env python3
"""
Download Reddit POSTS (RS = Reddit Submissions) für deine Subreddits
Posts sind wichtiger als Kommentare für Content-Verständnis!
"""

import os
import subprocess
from pathlib import Path

# Arctic Shift Torrent URLs für 2024 POSTS (RS = Reddit Submissions)
POST_TORRENT_URLS = {
    # Hinweis: RS (Submissions/Posts) Dateien sind kleiner als RC (Comments)
    "2024-12": "https://academictorrents.com/download/eb2017da9f63a49460dde21a4ebe3b7c517f3ad9.torrent",
    "2024-11": "https://academictorrents.com/download/a1b490117808d9541ab9e3e67a3447e2f4f48f01.torrent", 
    "2024-10": "https://academictorrents.com/download/507dfcda29de9936dd77ed4f34c6442dc675c98f.torrent",
    "2024-09": "https://academictorrents.com/download/43a6e113d6ecacf38e58ecc6caa28d68892dd8af.torrent",
    "2024-08": "https://academictorrents.com/download/8c2d4b00ce8ff9d45e335bed106fe9046c60adb0.torrent",
    "2024-07": "https://academictorrents.com/download/6e5300446bd9b328d0b812cdb3022891e086d9ec.torrent"
}

def check_posts_in_torrent():
    """Prüfe ob Posts in den Torrent-Dateien enthalten sind"""
    print("\n📌 WICHTIG: Arctic Shift Torrents enthalten BEIDE:")
    print("  - RC_2024-XX.zst = Reddit Comments")
    print("  - RS_2024-XX.zst = Reddit Submissions (Posts)")
    print("\nBeide Dateien sind im selben Torrent!")

def download_posts_latest():
    """Download-Skript für Posts"""
    
    script_content = """#!/bin/bash
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
curl -L -o temp_torrents/Reddit_2024-12.torrent \\
  "https://academictorrents.com/download/eb2017da9f63a49460dde21a4ebe3b7c517f3ad9.torrent"

# Selektiver Download nur für RS (Posts) Datei
echo "📡 Starte Download NUR für Posts (RS_2024-12.zst)..."
echo "  ⏳ Dies kann 10-30 Minuten dauern..."

# aria2c mit Datei-Selektion
aria2c --seed-time=0 \\
       --select-file=*RS_2024* \\
       --max-connection-per-server=16 \\
       --split=16 \\
       --enable-dht=true \\
       --file-allocation=none \\
       --console-log-level=notice \\
       --dir=pushshift_dumps/posts \\
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
"""
    
    with open("download_posts_latest.sh", "w") as f:
        f.write(script_content)
    
    os.chmod("download_posts_latest.sh", 0o755)
    print("✓ Erstellt: download_posts_latest.sh")

def create_posts_filter():
    """Erstelle Filter-Skript für Posts"""
    
    filter_script = '''#!/usr/bin/env python3
"""
Filtert Reddit POSTS für deine Subreddits
Posts enthalten: Titel, Text, Score, Kommentaranzahl, etc.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

def filter_posts():
    """Filtere Posts für unsere Ziel-Subreddits"""
    
    print("=" * 60)
    print("🎯 Reddit Posts Filter")
    print("=" * 60)
    
    # Lade Ziel-Subreddits
    with open("target_subreddits.txt", "r") as f:
        target_subs = [line.strip().lower() for line in f if line.strip()]
    
    print(f"\\n📋 {len(target_subs)} Ziel-Subreddits geladen")
    
    # Finde Posts-Dateien
    posts_dir = Path("pushshift_dumps/posts")
    if not posts_dir.exists():
        posts_dir = Path("pushshift_dumps")
    
    rs_files = list(posts_dir.glob("RS_*.zst"))
    
    if not rs_files:
        print("❌ Keine RS_*.zst (Posts) Dateien gefunden!")
        print("   Führe zuerst aus: bash download_posts_latest.sh")
        return
    
    print(f"\\n📦 Gefundene Posts-Dateien:")
    for f in rs_files:
        size_gb = f.stat().st_size / (1024**3)
        print(f"  • {f.name} ({size_gb:.2f} GB)")
    
    # Verarbeite jede Datei
    output_dir = Path("pushshift_dumps/2024_posts_filtered")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for rs_file in rs_files:
        output_file = output_dir / f"{rs_file.stem}_filtered.jsonl"
        
        print(f"\\n📊 Verarbeite: {rs_file.name}")
        print(f"  Output: {output_file.name}")
        
        # Filter-Kommando
        cmd = f"""
zstd -d -c "{rs_file}" | python3 -c "
import sys
import json

target_subs = {list(target_subs)}
total = 0
filtered = 0

with open('{output_file}', 'w') as out:
    for line in sys.stdin:
        total += 1
        try:
            post = json.loads(line.strip())
            subreddit = post.get('subreddit', '').lower()
            
            # Filtere nach Subreddit
            if subreddit in target_subs:
                # Nur Posts mit Inhalt
                if post.get('title') and post['title'] not in ['[deleted]', '[removed]']:
                    out.write(line)
                    filtered += 1
        except:
            pass
        
        if total % 10000 == 0:
            print(f'  Verarbeitet: {{total:,}} Posts, {{filtered:,}} gefiltert', end='\\\\r', file=sys.stderr)

print(f'\\\\n✓ Total: {{total:,}} Posts, {{filtered:,}} gefiltert', file=sys.stderr)
"
"""
        
        # Führe Filterung aus
        subprocess.run(cmd, shell=True)
        
        # Zeige Statistiken
        if output_file.exists():
            with open(output_file, 'r') as f:
                count = sum(1 for _ in f)
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"✓ Gespeichert: {count:,} Posts ({size_mb:.1f} MB)")
    
    print(f"\\n✅ Fertig! Gefilterte Posts in: {output_dir}/")
    print("\\n🎯 Nächster Schritt:")
    print("   python3 extract_top_content.py")

if __name__ == "__main__":
    filter_posts()
'''
    
    with open("filter_posts.py", "w") as f:
        f.write(filter_script)
    
    os.chmod("filter_posts.py", 0o755)
    print("✓ Erstellt: filter_posts.py")

def main():
    print("=" * 60)
    print("🎯 Reddit POSTS Download Setup")
    print("=" * 60)
    
    print("\n📊 Warum Posts wichtig sind:")
    print("  • Posts haben Titel + Content")
    print("  • Zeigen Hauptthemen der Community")
    print("  • Haben mehr Kontext als einzelne Kommentare")
    print("  • Engagement-Metriken (Kommentaranzahl)")
    
    print("\n📦 Dateigrössen:")
    print("  • Posts (RS): ~1-2 GB pro Monat")
    print("  • Kommentare (RC): ~15-20 GB pro Monat")
    print("  • Nach Filterung: ~10-20 MB Posts, ~150 MB Kommentare")
    
    # Erstelle Download-Skripte
    download_posts_latest()
    create_posts_filter()
    
    print("\n✅ Skripte erstellt!")
    print("\n🚀 So gehts weiter:")
    print("\n1️⃣  Download Posts (Dezember 2024):")
    print("   bash download_posts_latest.sh")
    print("\n2️⃣  Filtere für deine Subreddits:")
    print("   python3 filter_posts.py")
    print("\n3️⃣  Extrahiere Top 1000 Posts & Kommentare:")
    print("   python3 extract_top_content.py")
    print("\n4️⃣  Review die besten Inhalte:")
    print("   python3 view_top_content.py")

if __name__ == "__main__":
    main()