#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Filtert die Top 200 Posts aus den Oktober-Daten und speichert sie im data/Posts Format
"""

import json
import os
from pathlib import Path
import shutil
from datetime import datetime

def load_october_posts(file_path):
    """Lädt alle Posts aus der gefilterten Oktober-Datei"""
    posts = []
    print(f"📂 Lade Posts aus: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i % 10000 == 0:
                print(f"  ⏳ {i:,} Posts geladen...")
            
            try:
                post = json.loads(line.strip())
                # Nur Posts mit Score behalten
                if post.get('score', 0) > 0:
                    posts.append(post)
            except json.JSONDecodeError:
                continue
    
    print(f"✅ {len(posts):,} Posts mit Score > 0 geladen")
    return posts

def get_top_posts(posts, limit=200):
    """Sortiert Posts nach Score und gibt die Top N zurück"""
    print(f"\n🏆 Sortiere nach Score und wähle Top {limit}...")
    
    # Sortiere nach Score (höchste zuerst)
    sorted_posts = sorted(posts, key=lambda x: x.get('score', 0), reverse=True)
    
    # Nimm nur die Top N
    top_posts = sorted_posts[:limit]
    
    # Zeige Score-Range
    if top_posts:
        highest_score = top_posts[0].get('score', 0)
        lowest_score = top_posts[-1].get('score', 0)
        print(f"  📊 Score-Range: {highest_score:,} - {lowest_score:,}")
        
        # Zeige Top 5
        print(f"\n  🔝 Top 5 Posts:")
        for i, post in enumerate(top_posts[:5], 1):
            print(f"    {i}. Score {post.get('score', 0):,} - r/{post.get('subreddit', 'unknown')} - {post.get('title', '')[:60]}...")
    
    return top_posts

def save_post_to_data_format(post, index, base_dir):
    """Speichert einen Post im data/Posts Format"""
    posts_dir = base_dir / "data" / "Posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    # Erstelle Ordner für den Post
    post_folder = posts_dir / f"post_{index:06d}"
    post_folder.mkdir(exist_ok=True)
    
    # Bereite Post-Daten auf
    post_data = {
        'id': post.get('id', f'october_{index}'),
        'title': post.get('title', ''),
        'subreddit': post.get('subreddit', ''),
        'author': post.get('author', '[deleted]'),
        'created_utc': post.get('created_utc', 0),
        'score': post.get('score', 0),
        'num_comments': post.get('num_comments', 0),
        'permalink': post.get('permalink', ''),
        'url': post.get('url', ''),
        'selftext': post.get('selftext', ''),
        'link_flair_text': post.get('link_flair_text', None),
        'over_18': post.get('over_18', False),
        'spoiler': post.get('spoiler', False),
        'stickied': post.get('stickied', False),
        'upvote_ratio': post.get('upvote_ratio', 0.5),
        'domain': post.get('domain', ''),
        'is_self': post.get('is_self', True),
        'is_video': post.get('is_video', False),
        'is_original_content': post.get('is_original_content', False),
        'media': post.get('media', None),
        'preview': post.get('preview', None)
    }
    
    # Speichere als JSON
    json_file = post_folder / "post_data.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(post_data, f, indent=2, ensure_ascii=False)
    
    # Erstelle Info-Datei
    info_file = post_folder / "info.txt"
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"Post ID: {post_data['id']}\n")
        f.write(f"Title: {post_data['title'][:100]}\n")
        f.write(f"Subreddit: r/{post_data['subreddit']}\n")
        f.write(f"Score: {post_data['score']:,}\n")
        f.write(f"Comments: {post_data['num_comments']:,}\n")
        f.write(f"Created: {datetime.fromtimestamp(post_data['created_utc']).strftime('%Y-%m-%d %H:%M:%S') if post_data['created_utc'] else 'Unknown'}\n")
        f.write(f"URL: https://reddit.com{post_data['permalink']}\n")
    
    return post_folder

def main():
    """Hauptfunktion"""
    print("🚀 Oktober Top 200 Posts Processor")
    print("="*60)
    
    # Pfade
    base_dir = Path("/Users/patrick/Desktop/Reddit")
    input_file = base_dir / "pushshift_dumps" / "2024_october_filtered" / "RS_2024-10_filtered.jsonl"
    
    if not input_file.exists():
        print(f"❌ Datei nicht gefunden: {input_file}")
        return
    
    # Lade alle Posts
    posts = load_october_posts(input_file)
    
    if not posts:
        print("❌ Keine Posts gefunden")
        return
    
    # Filtere Top 200
    top_posts = get_top_posts(posts, limit=200)
    
    # Speichere im data/Posts Format
    print(f"\n💾 Speichere Top {len(top_posts)} Posts im data/Posts Format...")
    
    # Finde den nächsten freien Index
    posts_dir = base_dir / "data" / "Posts"
    existing_posts = []
    if posts_dir.exists():
        existing_posts = [d for d in posts_dir.iterdir() if d.is_dir() and d.name.startswith("post_")]
    
    start_index = len(existing_posts) + 1
    print(f"  📁 Starte bei Index: {start_index}")
    
    saved_count = 0
    for i, post in enumerate(top_posts, start=start_index):
        if (i - start_index) % 20 == 0:
            print(f"  ⏳ {i - start_index}/{len(top_posts)} Posts gespeichert...")
        
        try:
            folder = save_post_to_data_format(post, i, base_dir)
            saved_count += 1
        except Exception as e:
            print(f"  ❌ Fehler bei Post {i}: {e}")
            continue
    
    print(f"\n✅ Fertig! {saved_count} Posts gespeichert")
    print(f"📁 Gespeichert in: {posts_dir}")
    
    # Zeige Statistiken
    print(f"\n📊 Statistiken:")
    print(f"  • Posts verarbeitet: {len(posts):,}")
    print(f"  • Top Posts ausgewählt: {len(top_posts)}")
    print(f"  • Erfolgreich gespeichert: {saved_count}")
    print(f"  • Neue Post-Ordner: post_{start_index:06d} bis post_{start_index + saved_count - 1:06d}")
    
    # Zeige Subreddit-Verteilung
    subreddit_counts = {}
    for post in top_posts:
        sub = post.get('subreddit', 'unknown')
        subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1
    
    print(f"\n🏷️ Top 10 Subreddits in den Top 200:")
    for sub, count in sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  • r/{sub}: {count} Posts")

if __name__ == "__main__":
    main()