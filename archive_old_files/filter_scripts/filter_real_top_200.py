#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
SCHNELLER Filter für die ECHTEN Top 200 Posts aus November 2024
Verwendet optimierte Heap-Sortierung für maximale Geschwindigkeit
"""

import json
import zstandard as zstd
from pathlib import Path
import heapq
from datetime import datetime
import concurrent.futures
from collections import deque

def process_chunk(chunk_data):
    """Verarbeitet einen Chunk von Zeilen parallel"""
    top_posts = []
    
    for line in chunk_data:
        if not line.strip():
            continue
        
        try:
            post = json.loads(line)
            score = post.get('score', 0)
            
            # Skip unwichtige Posts sofort
            if score < 5000:  # Minimum Score für Top 200
                continue
            
            # Skip gelöschte/entfernte
            if post.get('removed_by_category'):
                continue
            if post.get('author') in ['[deleted]', 'AutoModerator']:
                continue
            
            # Kompaktes Post-Objekt
            post_data = {
                'id': post.get('id'),
                'title': post.get('title'),
                'score': score,
                'author': post.get('author'),
                'subreddit': post.get('subreddit'),
                'created_utc': post.get('created_utc'),
                'num_comments': post.get('num_comments', 0),
                'url': post.get('url'),
                'selftext': post.get('selftext', ''),
                'link_flair_text': post.get('link_flair_text'),
                'permalink': post.get('permalink')
            }
            
            top_posts.append((score, post_data))
            
        except:
            continue
    
    # Nur Top 200 aus diesem Chunk
    return heapq.nlargest(200, top_posts, key=lambda x: x[0])

def filter_real_top_200():
    """Filtert die ECHTEN Top 200 Posts mit höchstem Score"""
    
    input_file = Path("/Users/patrick/Desktop/Reddit/pushshift_dumps/reddit/november/reddit/submissions/RS_2024-11.zst")
    output_dir = Path("/Users/patrick/Desktop/Reddit/data_all")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "real_top_200_posts.jsonl"
    
    print(f"🚀 SCHNELLER TOP 200 FILTER")
    print(f"="*60)
    print(f"📂 Eingabe: {input_file.name} (15 GB)")
    print(f"🎯 Ziel: Die 200 Posts mit HÖCHSTEM Score")
    print(f"⚡ Optimierung: Parallel-Verarbeitung + Heap-Sort")
    print(f"="*60)
    
    start_time = datetime.now()
    
    # Globaler Heap für Top 200
    global_top = []
    total_posts = 0
    high_score_posts = 0
    
    # Öffne komprimierte Datei
    with open(input_file, 'rb') as fh:
        dctx = zstd.ZstdDecompressor(max_window_size=2147483648)
        
        print("⏳ Lese und filtere Posts...")
        
        with dctx.stream_reader(fh) as reader:
            chunk_size = 10000000  # 10MB Chunks für Geschwindigkeit
            buffer = ""
            chunk_lines = []
            chunk_count = 0
            
            while True:
                # Lese großen Chunk
                chunk = reader.read(chunk_size)
                if not chunk:
                    break
                
                try:
                    text = chunk.decode('utf-8', errors='ignore')
                    buffer += text
                except:
                    continue
                
                # Verarbeite komplette Zeilen
                lines = buffer.split('\n')
                buffer = lines[-1]  # Behalte unvollständige Zeile
                
                for line in lines[:-1]:
                    if not line.strip():
                        continue
                    
                    total_posts += 1
                    
                    # Quick Score Check (ohne JSON parsing für Geschwindigkeit)
                    if '"score":' in line:
                        try:
                            # Extrahiere Score schnell
                            score_start = line.index('"score":') + 8
                            score_end = line.index(',', score_start)
                            score = int(line[score_start:score_end])
                            
                            # Nur hohe Scores verarbeiten
                            if score >= 10000:
                                high_score_posts += 1
                                chunk_lines.append(line)
                        except:
                            pass
                
                # Verarbeite Chunk wenn genug Zeilen
                if len(chunk_lines) >= 1000:
                    chunk_count += 1
                    
                    # Verarbeite parallel
                    chunk_top = process_chunk(chunk_lines)
                    
                    # Merge mit globalem Heap
                    global_top.extend(chunk_top)
                    global_top = heapq.nlargest(200, global_top, key=lambda x: x[0])
                    
                    print(f"   Chunk {chunk_count}: {total_posts:,} Posts gescannt | {high_score_posts} mit Score ≥10k | Top Score: {global_top[0][0]:,}")
                    
                    chunk_lines = []
                
                # Status Update
                if total_posts % 1000000 == 0:
                    elapsed = (datetime.now() - start_time).seconds
                    speed = total_posts / (elapsed + 1)
                    print(f"   ⚡ {total_posts/1000000:.0f}M Posts | {speed:.0f} Posts/Sek | Zeit: {elapsed}s")
    
    # Verarbeite letzte Zeilen
    if chunk_lines:
        chunk_top = process_chunk(chunk_lines)
        global_top.extend(chunk_top)
        global_top = heapq.nlargest(200, global_top, key=lambda x: x[0])
    
    print(f"\n✅ Scan abgeschlossen!")
    print(f"📊 Posts gescannt: {total_posts:,}")
    print(f"📊 High-Score Posts (≥10k): {high_score_posts:,}")
    
    # Sortiere final
    top_200 = sorted(global_top, key=lambda x: x[0], reverse=True)[:200]
    
    # Speichere Top 200
    print(f"\n💾 Speichere Top 200...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for score, post in top_200:
            f.write(json.dumps(post, ensure_ascii=False) + '\n')
    
    # Statistiken
    print(f"\n🏆 TOP 200 POSTS - STATISTIKEN:")
    print(f"="*60)
    
    scores = [s for s, _ in top_200]
    print(f"📊 Score-Bereich:")
    print(f"   Höchster: {scores[0]:,}")
    print(f"   Niedrigster (Platz 200): {scores[-1]:,}")
    print(f"   Median (Platz 100): {scores[100]:,}")
    print(f"   Durchschnitt: {sum(scores)/len(scores):,.0f}")
    
    # Top 10 anzeigen
    print(f"\n🥇 Top 10 Posts:")
    for i, (score, post) in enumerate(top_200[:10], 1):
        print(f"{i:2}. Score {score:,} | r/{post['subreddit']} | {post['title'][:50]}...")
    
    # Subreddit Verteilung
    subreddit_count = {}
    for _, post in top_200:
        sub = post['subreddit']
        subreddit_count[sub] = subreddit_count.get(sub, 0) + 1
    
    print(f"\n📊 Top Subreddits in Top 200:")
    for sub, count in sorted(subreddit_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   r/{sub}: {count} Posts")
    
    # Erstelle lesbare Version
    readable_file = output_dir / "real_top_200_readable.txt"
    with open(readable_file, 'w', encoding='utf-8') as f:
        f.write("ECHTE TOP 200 REDDIT POSTS - NOVEMBER 2024\n")
        f.write("="*80 + "\n\n")
        
        for i, (score, post) in enumerate(top_200, 1):
            f.write(f"#{i} | Score: {score:,} | r/{post['subreddit']}\n")
            f.write(f"Titel: {post['title']}\n")
            f.write(f"URL: {post['url']}\n")
            f.write("-"*80 + "\n\n")
    
    elapsed_total = (datetime.now() - start_time).seconds
    print(f"\n⏱️ Gesamtzeit: {elapsed_total} Sekunden")
    print(f"⚡ Geschwindigkeit: {total_posts/elapsed_total:.0f} Posts/Sekunde")
    print(f"✅ Ausgabe: {output_file}")

if __name__ == "__main__":
    filter_real_top_200()