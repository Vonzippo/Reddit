#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Filter für die ECHTEN Top 500 Posts aus Oktober Reddit-Daten
Nutzt Heap-Sortierung für effiziente Verarbeitung
"""

import json
import zstandard as zstd
import heapq
from pathlib import Path
import time
from datetime import datetime
import multiprocessing as mp
from functools import partial

def process_chunk(chunk_data):
    """Verarbeitet einen Chunk von Zeilen"""
    chunk_lines, min_score = chunk_data
    chunk_posts = []
    
    for line in chunk_lines:
        try:
            post = json.loads(line)
            score = int(post.get('score', 0))
            
            # Nur Posts mit hohem Score behalten
            if score >= min_score:
                # Vereinfachte Daten für Heap
                chunk_posts.append((
                    -score,  # Negativ für Max-Heap
                    {
                        'id': post.get('id', ''),
                        'title': post.get('title', ''),
                        'score': score,
                        'subreddit': post.get('subreddit', ''),
                        'url': post.get('url', ''),
                        'selftext': post.get('selftext', ''),
                        'author': post.get('author', ''),
                        'created_utc': post.get('created_utc', 0),
                        'num_comments': post.get('num_comments', 0),
                        'over_18': post.get('over_18', False),
                        'is_video': post.get('is_video', False),
                        'permalink': post.get('permalink', '')
                    }
                ))
        except:
            continue
    
    return chunk_posts

def filter_top_500_october():
    """Filtert die Top 500 Posts aus Oktober-Daten"""
    
    # Pfade - Oktober-Dateien (bereits gefiltert!)
    input_files = [
        Path("/Users/patrick/Desktop/Reddit/pushshift_dumps/2024_october_filtered/RS_2024-10_filtered.jsonl")
    ]
    
    output_dir = Path("/Users/patrick/Desktop/Reddit/data_october")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "top_500_posts_october.json"
    
    print("🚀 STARTE OKTOBER TOP 500 FILTER (ECHTE HIGH-SCORE POSTS)")
    print("="*60)
    
    # Statistiken
    total_posts = 0
    high_score_posts = 0
    start_time = time.time()
    
    # Min-Score für erste Filterung (nur hohe Scores)
    MIN_SCORE_THRESHOLD = 10000  # Nur Posts mit 10k+ Score
    
    # Heap für Top 500 (verwende negatives Score für Max-Heap)
    top_posts_heap = []
    HEAP_SIZE = 500
    
    print(f"⚙️ Einstellungen:")
    print(f"   - Suche Top 500 Posts")
    print(f"   - Nur Posts mit Score ≥ {MIN_SCORE_THRESHOLD:,}")
    print(f"   - Nutze {mp.cpu_count()} CPU-Kerne")
    print()
    
    for input_file in input_files:
        if not input_file.exists():
            print(f"❌ Datei nicht gefunden: {input_file}")
            continue
        
        print(f"📂 Verarbeite: {input_file.name}")
        file_size = input_file.stat().st_size / (1024**3)
        print(f"   Größe: {file_size:.2f} GB")
        
        # Öffne JSONL Datei (nicht komprimiert)
        with open(input_file, 'r', encoding='utf-8') as text_stream:
            
            # Verarbeite in Chunks für Parallelisierung
            chunk_lines = []
            CHUNK_SIZE = 10000
            
            with mp.Pool(processes=mp.cpu_count()) as pool:
                for line_num, line in enumerate(text_stream, 1):
                    total_posts += 1
                    
                    # Schnell-Check für Score
                    if '"score":' in line:
                        try:
                            # Extrahiere Score schnell
                            score_start = line.index('"score":') + 8
                            score_end = line.index(',', score_start)
                            score = int(line[score_start:score_end])
                            
                            # Nur hohe Scores verarbeiten
                            if score >= MIN_SCORE_THRESHOLD:
                                high_score_posts += 1
                                chunk_lines.append(line)
                        except:
                            continue
                    
                    # Verarbeite Chunk wenn voll
                    if len(chunk_lines) >= CHUNK_SIZE:
                        # Parallel verarbeiten
                        results = pool.map(
                            partial(process_chunk, min_score=MIN_SCORE_THRESHOLD),
                            [(chunk_lines, MIN_SCORE_THRESHOLD)]
                        )[0]
                        
                        # Füge zu Heap hinzu
                        for post_tuple in results:
                            if len(top_posts_heap) < HEAP_SIZE:
                                heapq.heappush(top_posts_heap, post_tuple)
                            else:
                                # Ersetze kleinsten wenn neuer größer
                                if post_tuple[0] < top_posts_heap[0][0]:
                                    heapq.heapreplace(top_posts_heap, post_tuple)
                        
                        chunk_lines = []
                        
                        # Status Update
                        if total_posts % 50000 == 0:
                            elapsed = time.time() - start_time
                            speed = total_posts / elapsed
                            current_min = -top_posts_heap[0][0] if top_posts_heap else 0
                            
                            print(f"   📊 {total_posts:,} Posts | "
                                  f"High-Score: {high_score_posts:,} | "
                                  f"Speed: {speed:.0f}/s | "
                                  f"Min in Top 500: {current_min:,}")
                
                # Letzter Chunk
                if chunk_lines:
                    results = pool.map(
                        partial(process_chunk, min_score=MIN_SCORE_THRESHOLD),
                        [(chunk_lines, MIN_SCORE_THRESHOLD)]
                    )[0]
                    
                    for post_tuple in results:
                        if len(top_posts_heap) < HEAP_SIZE:
                            heapq.heappush(top_posts_heap, post_tuple)
                        else:
                            if post_tuple[0] < top_posts_heap[0][0]:
                                heapq.heapreplace(top_posts_heap, post_tuple)
    
    # Extrahiere und sortiere Top 500
    print("\n📝 Extrahiere Top 500...")
    top_500 = []
    while top_posts_heap:
        score, post = heapq.heappop(top_posts_heap)
        top_500.append(post)
    
    # Sortiere nach Score (höchste zuerst)
    top_500.sort(key=lambda x: x['score'], reverse=True)
    
    # Speichere Ergebnisse
    print(f"\n💾 Speichere {len(top_500)} Posts...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(top_500, f, indent=2, ensure_ascii=False)
    
    # Zeige Top 20
    print("\n🏆 TOP 20 POSTS (OKTOBER):")
    print("-"*60)
    for i, post in enumerate(top_500[:20], 1):
        print(f"{i:2}. Score: {post['score']:,} | r/{post['subreddit']}")
        print(f"    {post['title'][:60]}...")
    
    # Statistiken
    elapsed_time = time.time() - start_time
    print("\n" + "="*60)
    print("✅ FERTIG!")
    print(f"   Verarbeitete Posts: {total_posts:,}")
    print(f"   High-Score Posts (≥10k): {high_score_posts:,}")
    print(f"   Top 500 gefunden: {len(top_500)}")
    print(f"   Score-Range: {top_500[-1]['score']:,} - {top_500[0]['score']:,}")
    print(f"   Zeit: {elapsed_time:.1f} Sekunden")
    print(f"   Geschwindigkeit: {total_posts/elapsed_time:.0f} Posts/Sekunde")
    print(f"\n📁 Gespeichert in: {output_file}")

import io

if __name__ == "__main__":
    filter_top_500_october()