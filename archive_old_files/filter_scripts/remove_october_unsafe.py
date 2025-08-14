#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Entfernt NSFW und unsichere Posts aus Oktober data_october/Posts
"""

import json
import shutil
from pathlib import Path

def remove_unsafe_october_posts():
    """Entfernt alle NSFW und unsicheren Oktober Posts"""
    
    posts_dir = Path("/Users/patrick/Desktop/Reddit/data_october/Posts")
    safe_posts_file = Path("/Users/patrick/Desktop/Reddit/data_october/safe_october_posts.json")
    
    print("🗑️ ENTFERNE NSFW OKTOBER POSTS")
    print("="*60)
    
    # Lade Liste der sicheren Posts
    if not safe_posts_file.exists():
        print("❌ safe_october_posts.json nicht gefunden!")
        return
    
    with open(safe_posts_file, 'r') as f:
        safe_data = json.load(f)
    
    safe_dirs = {post['dir'] for post in safe_data['posts']}
    print(f"✅ {len(safe_dirs)} sichere Posts identifiziert")
    
    # Gehe durch alle Post-Ordner
    removed_count = 0
    removed_posts = []
    
    for post_dir in sorted(posts_dir.iterdir()):
        if not post_dir.is_dir():
            continue
        
        # Prüfe ob dieser Post sicher ist
        if post_dir.name not in safe_dirs:
            # Lade Post-Info für Log
            json_file = post_dir / "post_data.json"
            if json_file.exists():
                with open(json_file, 'r') as f:
                    post_data = json.load(f)
                    removed_posts.append({
                        'dir': post_dir.name,
                        'title': post_data.get('title', ''),
                        'subreddit': post_data.get('subreddit', ''),
                        'score': post_data.get('score', 0)
                    })
            
            # Lösche den Ordner
            print(f"   ❌ Entferne: {post_dir.name}")
            shutil.rmtree(post_dir)
            removed_count += 1
    
    # Speichere Log der entfernten Posts
    if removed_posts:
        log_file = posts_dir.parent / "removed_october_posts_log.json"
        with open(log_file, 'w') as f:
            json.dump({
                'removed_count': removed_count,
                'posts': removed_posts
            }, f, indent=2)
        print(f"\n📝 Log gespeichert: {log_file}")
    
    # Zeige Zusammenfassung
    print("\n" + "="*60)
    print("✅ BEREINIGUNG ABGESCHLOSSEN!")
    print(f"   Entfernt: {removed_count} Posts")
    print(f"   Behalten: {len(safe_dirs)} Posts")
    
    # Zeige was entfernt wurde
    if removed_posts:
        print("\n🗑️ ENTFERNTE POSTS:")
        print("-"*60)
        for post in removed_posts:
            print(f"   r/{post['subreddit']}: {post['title'][:50]}...")
    
    # Prüfe neue Größe
    total_size = sum(f.stat().st_size for f in posts_dir.rglob('*') if f.is_file())
    size_mb = total_size / (1024 * 1024)
    print(f"\n📊 NEUE GRÖSSE: {size_mb:.1f} MB")
    
    if size_mb < 500:
        print("✅ Perfekt für GitHub (<500 MB)!")
    else:
        print("⚠️ Immer noch zu groß für GitHub!")

def main():
    remove_unsafe_october_posts()

if __name__ == "__main__":
    main()