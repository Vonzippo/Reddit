#!/usr/bin/env python3
"""
Extrahiert die Top 100 Text-Posts (ohne Bilder) aus Pushshift-Dumps
"""

import json
import os
from pathlib import Path
import re
from datetime import datetime

def is_text_only_post(post):
    """Prüft ob ein Post nur Text ist (kein Bild/Video)"""
    # Prüfe ob selftext vorhanden (Text-Post)
    if not post.get('selftext') or post.get('selftext') in ['[removed]', '[deleted]', '']:
        return False
    
    # Prüfe URL - sollte keine Bild/Video-URL sein
    url = post.get('url', '')
    if url:
        # Bild/Video-Endungen
        media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm', '.mov']
        # Bild/Video-Domains
        media_domains = ['i.redd.it', 'imgur.com', 'i.imgur.com', 'v.redd.it', 
                        'youtube.com', 'youtu.be', 'gfycat.com', 'streamable.com']
        
        # Prüfe auf Medien
        for ext in media_extensions:
            if ext in url.lower():
                return False
        for domain in media_domains:
            if domain in url.lower():
                return False
    
    # Muss mehr als 100 Zeichen Text haben
    if len(post.get('selftext', '')) < 100:
        return False
    
    return True

def is_adhd_related(post):
    """Prüft ob Post ADHD-relevant ist"""
    adhd_keywords = ['adhd', 'add', 'executive dysfunction', 'hyperfocus', 
                     'neurodivergent', 'dopamine', 'medication', 'vyvanse', 
                     'adderall', 'ritalin', 'concerta', 'diagnosis', 'diagnosed']
    
    text = (post.get('title', '') + ' ' + post.get('selftext', '')).lower()
    subreddit = post.get('subreddit', '').lower()
    
    # Check subreddit
    adhd_subs = ['adhd', 'adhdmeme', 'adhdwomen', 'audhd', 'adhd_anxiety']
    if any(sub in subreddit for sub in adhd_subs):
        return True
    
    # Check keywords
    return any(keyword in text for keyword in adhd_keywords)

def process_posts():
    """Verarbeitet alle gefilterten Posts"""
    all_posts = []
    
    # Dateien zum Durchsuchen
    files_to_process = [
        'pushshift_dumps/2024_october_filtered/RS_2024-10_filtered.jsonl',
        'pushshift_dumps/2024_posts_filtered/RS_2024-11_filtered.jsonl',
        'pushshift_dumps/2024_posts_filtered/RS_2024-12_filtered.jsonl'
    ]
    
    print("📖 Lade Text-Posts aus Pushshift-Dumps...")
    
    for file_path in files_to_process:
        if not os.path.exists(file_path):
            print(f"   ⚠️ Datei nicht gefunden: {file_path}")
            continue
            
        print(f"   📂 Verarbeite: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    post = json.loads(line.strip())
                    
                    # Nur Text-Posts
                    if not is_text_only_post(post):
                        continue
                    
                    # Nur ADHD-relevante Posts
                    if not is_adhd_related(post):
                        continue
                    
                    # Muss mindestens 50 Score haben
                    if post.get('score', 0) < 50:
                        continue
                    
                    # Füge zur Liste hinzu
                    all_posts.append({
                        'id': post.get('id'),
                        'title': post.get('title'),
                        'selftext': post.get('selftext'),
                        'score': post.get('score', 0),
                        'num_comments': post.get('num_comments', 0),
                        'subreddit': post.get('subreddit'),
                        'author': post.get('author'),
                        'created_utc': post.get('created_utc'),
                        'url': f"https://reddit.com/r/{post.get('subreddit')}/comments/{post.get('id')}"
                    })
                    
                except Exception as e:
                    continue
    
    print(f"\n✅ Gefunden: {len(all_posts)} Text-Posts")
    
    # Sortiere nach Score
    all_posts.sort(key=lambda x: x['score'], reverse=True)
    
    # Nimm Top 100
    top_posts = all_posts[:100]
    
    return top_posts

def save_posts(posts):
    """Speichert Posts in Data_Text Struktur"""
    base_dir = Path("Data_Text/Posts")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Speichere Top {len(posts)} Text-Posts...")
    
    for i, post in enumerate(posts, 1):
        # Erstelle sauberen Ordnernamen
        title_clean = re.sub(r'[^\w\s-]', '', post['title'][:50])
        title_clean = re.sub(r'[-\s]+', '_', title_clean).lower()
        
        folder_name = f"text_{i:03d}_{title_clean}"
        post_dir = base_dir / folder_name
        post_dir.mkdir(exist_ok=True)
        
        # Speichere post_data.json
        post_data = {
            'id': post['id'],
            'title': post['title'],
            'selftext': post['selftext'],
            'score': post['score'],
            'num_comments': post['num_comments'],
            'subreddit': post['subreddit'],
            'author': post['author'],
            'created_utc': post['created_utc'],
            'url': post['url'],
            'is_text_post': True,
            'rank': i
        }
        
        with open(post_dir / 'post_data.json', 'w', encoding='utf-8') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        
        # Speichere lesbaren Text
        with open(post_dir / 'post_content.txt', 'w', encoding='utf-8') as f:
            f.write(f"RANK: #{i} (Score: {post['score']})\n")
            f.write("="*50 + "\n\n")
            f.write(f"TITLE:\n{post['title']}\n\n")
            f.write(f"SUBREDDIT: r/{post['subreddit']}\n")
            f.write(f"AUTHOR: u/{post['author']}\n")
            f.write(f"COMMENTS: {post['num_comments']}\n\n")
            f.write("TEXT:\n")
            f.write("-"*30 + "\n")
            f.write(post['selftext'])
        
        if i % 10 == 0:
            print(f"   📝 {i}/{len(posts)} gespeichert...")
    
    # Erstelle Übersicht
    with open(base_dir.parent / 'TOP_100_TEXT_POSTS.md', 'w', encoding='utf-8') as f:
        f.write("# 📝 Top 100 Text-Posts (ohne Bilder)\n\n")
        f.write("Extrahiert aus Pushshift-Dumps (Oktober-Dezember 2024)\n")
        f.write("Alle Posts sind ADHD-relevant und reine Text-Posts.\n\n")
        
        for i, post in enumerate(posts, 1):
            f.write(f"{i}. **{post['title']}**\n")
            f.write(f"   - r/{post['subreddit']} | Score: {post['score']} | {post['num_comments']} Kommentare\n")
        
        f.write(f"\n---\nErstellt: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    print(f"✅ Alle Posts gespeichert in: Data_Text/")

def main():
    print("🚀 EXTRAHIERE TOP 100 TEXT-POSTS")
    print("="*50)
    
    # Verarbeite Posts
    top_posts = process_posts()
    
    if not top_posts:
        print("❌ Keine Text-Posts gefunden!")
        return
    
    # Speichere Posts
    save_posts(top_posts)
    
    print("\n✅ FERTIG!")
    print(f"   • {len(top_posts)} Text-Posts extrahiert")
    print(f"   • Gespeichert in: Data_Text/Posts/")
    print(f"   • Übersicht: Data_Text/TOP_100_TEXT_POSTS.md")

if __name__ == "__main__":
    main()