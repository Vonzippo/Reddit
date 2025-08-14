#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Filter für Top 1000 Posts aus ALLEN November Reddit Posts
Liest die komplette RS_2024-11.zst und extrahiert die 1000 Posts mit höchstem Score
"""

import json
import zstandard as zstd
from pathlib import Path
import heapq
from datetime import datetime

def filter_top_1000_posts():
    """Filtert die Top 1000 Posts nach Score aus November 2024"""
    
    # Pfade
    input_file = Path("/Users/patrick/Desktop/Reddit/pushshift_dumps/reddit/november/reddit/submissions/RS_2024-11.zst")
    output_dir = Path("/Users/patrick/Desktop/Reddit/data_all")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "top_1000_november_posts.jsonl"
    
    if not input_file.exists():
        print(f"❌ Datei nicht gefunden: {input_file}")
        return
    
    print(f"📂 Lese Datei: {input_file}")
    print(f"📊 Dateigröße: {input_file.stat().st_size / (1024**3):.1f} GB")
    
    # Verwende Heap für effiziente Top-K Sortierung
    top_posts = []
    total_posts = 0
    processed_posts = 0
    
    start_time = datetime.now()
    
    # Öffne komprimierte Datei
    with open(input_file, 'rb') as fh:
        dctx = zstd.ZstdDecompressor(max_window_size=2147483648)
        
        with dctx.stream_reader(fh) as reader:
            text_stream = reader.read(1000000)  # Lese in 1MB Chunks
            buffer = ""
            
            while text_stream:
                # Dekodiere und füge zum Buffer hinzu
                try:
                    chunk = text_stream.decode('utf-8', errors='ignore')
                    buffer += chunk
                except:
                    text_stream = reader.read(1000000)
                    continue
                
                # Verarbeite komplette Zeilen
                lines = buffer.split('\n')
                buffer = lines[-1]  # Behalte unvollständige Zeile
                
                for line in lines[:-1]:
                    if not line.strip():
                        continue
                    
                    total_posts += 1
                    
                    # Status Update
                    if total_posts % 100000 == 0:
                        elapsed = (datetime.now() - start_time).seconds
                        print(f"⏳ Verarbeitet: {total_posts:,} Posts | Zeit: {elapsed}s | Top Score: {top_posts[0][0] if top_posts else 0}")
                    
                    try:
                        post = json.loads(line)
                        
                        # Extrahiere wichtige Felder
                        score = post.get('score', 0)
                        
                        # Skip gelöschte/entfernte Posts
                        if post.get('removed_by_category'):
                            continue
                        if post.get('selftext') in ['[removed]', '[deleted]']:
                            continue
                        if post.get('author') in ['[deleted]', 'AutoModerator']:
                            continue
                        
                        # Behalte nur Posts mit Score > 0
                        if score <= 0:
                            continue
                        
                        processed_posts += 1
                        
                        # Erstelle kompaktes Post-Objekt
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
                            'over_18': post.get('over_18', False),
                            'spoiler': post.get('spoiler', False),
                            'stickied': post.get('stickied', False),
                            'is_video': post.get('is_video', False),
                            'domain': post.get('domain'),
                            'permalink': post.get('permalink')
                        }
                        
                        # Verwende Min-Heap mit negativem Score für Top-K
                        if len(top_posts) < 1000:
                            heapq.heappush(top_posts, (score, post_data))
                        elif score > top_posts[0][0]:
                            heapq.heapreplace(top_posts, (score, post_data))
                        
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        if total_posts < 10:
                            print(f"⚠️ Fehler bei Post: {e}")
                        continue
                
                # Lese nächsten Chunk
                text_stream = reader.read(1000000)
    
    print(f"\n✅ Verarbeitung abgeschlossen!")
    print(f"📊 Posts gesamt: {total_posts:,}")
    print(f"📊 Posts verarbeitet (nicht gelöscht): {processed_posts:,}")
    print(f"📊 Top 1000 Posts gefunden: {len(top_posts)}")
    
    # Sortiere nach Score (höchster zuerst)
    top_posts_sorted = sorted(top_posts, key=lambda x: x[0], reverse=True)
    
    # Speichere Top 1000
    print(f"\n💾 Speichere Top 1000 Posts...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for score, post in top_posts_sorted:
            f.write(json.dumps(post, ensure_ascii=False) + '\n')
    
    print(f"✅ Gespeichert: {output_file}")
    print(f"📊 Dateigröße: {output_file.stat().st_size / (1024**2):.1f} MB")
    
    # Zeige Top 10
    print(f"\n🏆 Top 10 Posts nach Score:")
    for i, (score, post) in enumerate(top_posts_sorted[:10], 1):
        print(f"{i:2}. Score {score:,} | r/{post['subreddit']} | {post['title'][:60]}...")
    
    # Statistiken
    print(f"\n📊 Score-Verteilung:")
    scores = [s for s, _ in top_posts_sorted]
    print(f"   Höchster Score: {scores[0]:,}")
    print(f"   Niedrigster Score (Top 1000): {scores[-1]:,}")
    print(f"   Median Score: {scores[500]:,}")
    
    # Subreddit Verteilung
    subreddit_count = {}
    for _, post in top_posts_sorted:
        sub = post['subreddit']
        subreddit_count[sub] = subreddit_count.get(sub, 0) + 1
    
    print(f"\n📊 Top 10 Subreddits in Top 1000:")
    for sub, count in sorted(subreddit_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   r/{sub}: {count} Posts")
    
    # Erstelle auch eine readable Version
    readable_file = output_dir / "top_1000_november_readable.txt"
    with open(readable_file, 'w', encoding='utf-8') as f:
        f.write("TOP 1000 REDDIT POSTS - NOVEMBER 2024\n")
        f.write("="*80 + "\n\n")
        
        for i, (score, post) in enumerate(top_posts_sorted, 1):
            f.write(f"#{i} | Score: {score:,} | r/{post['subreddit']}\n")
            f.write(f"Titel: {post['title']}\n")
            f.write(f"Autor: u/{post['author']} | Kommentare: {post['num_comments']:,}\n")
            f.write(f"URL: {post['url']}\n")
            if post['selftext'] and len(post['selftext']) > 0:
                preview = post['selftext'][:200].replace('\n', ' ')
                f.write(f"Text: {preview}...\n")
            f.write("-"*80 + "\n\n")
    
    print(f"✅ Readable Version: {readable_file}")
    
    elapsed_total = (datetime.now() - start_time).seconds
    print(f"\n⏱️ Gesamtzeit: {elapsed_total//60} Minuten {elapsed_total%60} Sekunden")

if __name__ == "__main__":
    print("🚀 Starte Filterung der Top 1000 November Posts...")
    print("⚠️ Dies wird die komplette 15GB Datei durchsuchen!")
    print("-"*60)
    
    try:
        filter_top_1000_posts()
    except KeyboardInterrupt:
        print("\n\n❌ Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()