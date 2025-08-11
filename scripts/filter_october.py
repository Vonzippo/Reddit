#!/usr/bin/env python3
"""
Filter Oktober 2024 Reddit Daten für ADHD-relevante Subreddits
"""

import json
import os
from pathlib import Path
import zstandard as zstd

# Lade Subreddit-Liste
def load_target_subreddits():
    """Lade die erweiterte Subreddit-Liste"""
    subreddits = []
    with open("target_subreddits.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                subreddits.append(line.lower())
    return set(subreddits)

def filter_october_data():
    """Filtere Oktober-Daten nach Subreddits"""
    
    target_subs = load_target_subreddits()
    print(f"📋 Filtere nach {len(target_subs)} Subreddits")
    
    # Pfade
    input_dir = Path("pushshift_dumps/reddit/october")
    output_dir = Path("pushshift_dumps/2024_filtered")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Filtere Kommentare
    comments_file = input_dir / "RC_2024-10.zst"
    if comments_file.exists():
        print(f"📝 Filtere Kommentare: {comments_file}")
        output_file = output_dir / "RC_2024-10_filtered.jsonl"
        
        with zstd.open(comments_file, 'rt', encoding='utf-8') as infile:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                count = 0
                filtered = 0
                
                for line in infile:
                    count += 1
                    if count % 100000 == 0:
                        print(f"  Verarbeitet: {count:,} | Gefiltert: {filtered:,}")
                    
                    try:
                        data = json.loads(line)
                        if data.get('subreddit', '').lower() in target_subs:
                            outfile.write(line)
                            filtered += 1
                    except:
                        continue
                
                print(f"✅ Kommentare gefiltert: {filtered:,} von {count:,}")
    
    # Filtere Posts
    posts_file = input_dir / "RS_2024-10.zst"
    if posts_file.exists():
        print(f"📝 Filtere Posts: {posts_file}")
        output_file = output_dir / "RS_2024-10_filtered.jsonl"
        
        with zstd.open(posts_file, 'rt', encoding='utf-8') as infile:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                count = 0
                filtered = 0
                
                for line in infile:
                    count += 1
                    if count % 100000 == 0:
                        print(f"  Verarbeitet: {count:,} | Gefiltert: {filtered:,}")
                    
                    try:
                        data = json.loads(line)
                        if data.get('subreddit', '').lower() in target_subs:
                            outfile.write(line)
                            filtered += 1
                    except:
                        continue
                
                print(f"✅ Posts gefiltert: {filtered:,} von {count:,}")

if __name__ == "__main__":
    print("🎯 Starte Oktober-Filterung...")
    filter_october_data()
    print("✅ Filterung abgeschlossen!")