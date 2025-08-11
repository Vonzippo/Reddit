#!/usr/bin/env python3
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
    
    print(f"\n📋 {len(target_subs)} Ziel-Subreddits geladen")
    
    # Finde Posts-Dateien
    posts_dir = Path("pushshift_dumps/posts")
    if not posts_dir.exists():
        posts_dir = Path("pushshift_dumps")
    
    rs_files = list(posts_dir.glob("RS_*.zst"))
    
    if not rs_files:
        print("❌ Keine RS_*.zst (Posts) Dateien gefunden!")
        print("   Führe zuerst aus: bash download_posts_latest.sh")
        return
    
    print(f"\n📦 Gefundene Posts-Dateien:")
    for f in rs_files:
        size_gb = f.stat().st_size / (1024**3)
        print(f"  • {f.name} ({size_gb:.2f} GB)")
    
    # Verarbeite jede Datei
    output_dir = Path("pushshift_dumps/2024_posts_filtered")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for rs_file in rs_files:
        output_file = output_dir / f"{rs_file.stem}_filtered.jsonl"
        
        print(f"\n📊 Verarbeite: {rs_file.name}")
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
            print(f'  Verarbeitet: {{total:,}} Posts, {{filtered:,}} gefiltert', end='\\r', file=sys.stderr)

print(f'\\n✓ Total: {{total:,}} Posts, {{filtered:,}} gefiltert', file=sys.stderr)
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
    
    print(f"\n✅ Fertig! Gefilterte Posts in: {output_dir}/")
    print("\n🎯 Nächster Schritt:")
    print("   python3 extract_top_content.py")

if __name__ == "__main__":
    filter_posts()
