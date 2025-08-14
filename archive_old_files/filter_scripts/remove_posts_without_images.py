#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Entfernt Posts ohne Bilder aus data_all
AUSNAHME: Text-Posts (mit selftext) werden behalten
"""

import json
import shutil
from pathlib import Path

def remove_posts_without_proper_images():
    """Entfernt Posts ohne Bilder (außer Text-Posts)"""
    
    posts_dir = Path("/Users/patrick/Desktop/Reddit/data_all/Posts")
    
    print("🖼️ ENTFERNE POSTS OHNE BILDER")
    print("="*60)
    print("Behalte: Text-Posts (selftext) und Posts mit Bildern")
    print("Lösche: Posts ohne Bilder die nur Links sind")
    print()
    
    stats = {
        'total': 0,
        'kept_with_image': 0,
        'kept_text_posts': 0,
        'removed_no_image': 0,
        'removed_folders': []
    }
    
    for post_dir in sorted(posts_dir.iterdir()):
        if not post_dir.is_dir():
            continue
        
        stats['total'] += 1
        
        # Lade post_data.json
        json_file = post_dir / "post_data.json"
        if not json_file.exists():
            # Kein JSON = löschen
            shutil.rmtree(post_dir)
            stats['removed_no_image'] += 1
            continue
        
        with open(json_file, 'r') as f:
            post_data = json.load(f)
        
        # Prüfe ob Bild existiert
        has_image = False
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            if (post_dir / f"image{ext}").exists():
                has_image = True
                break
        
        # Prüfe ob es ein Text-Post ist
        is_text_post = bool(post_data.get('selftext', '').strip())
        
        # Entscheidung
        if has_image:
            # Post mit Bild = behalten
            stats['kept_with_image'] += 1
            print(f"✅ Behalten (Bild): {post_dir.name[:50]}")
        elif is_text_post:
            # Text-Post = behalten
            stats['kept_text_posts'] += 1
            print(f"📝 Behalten (Text): {post_dir.name[:50]}")
        else:
            # Weder Bild noch Text = löschen
            stats['removed_no_image'] += 1
            stats['removed_folders'].append({
                'dir': post_dir.name,
                'title': post_data.get('title', '')[:60],
                'url': post_data.get('url', '')[:50]
            })
            print(f"❌ Entferne (kein Bild/Text): {post_dir.name[:40]}")
            shutil.rmtree(post_dir)
    
    # Zeige Statistiken
    print("\n" + "="*60)
    print("✅ BEREINIGUNG ABGESCHLOSSEN!")
    print("="*60)
    print(f"📊 STATISTIKEN:")
    print(f"   Posts gesamt: {stats['total']}")
    print(f"   Behalten mit Bild: {stats['kept_with_image']}")
    print(f"   Behalten als Text-Post: {stats['kept_text_posts']}")
    print(f"   Entfernt (kein Bild/Text): {stats['removed_no_image']}")
    print(f"   GESAMT BEHALTEN: {stats['kept_with_image'] + stats['kept_text_posts']}")
    
    if stats['removed_folders']:
        print(f"\n🗑️ ENTFERNTE POSTS (erste 20):")
        print("-"*60)
        for post in stats['removed_folders'][:20]:
            print(f"   {post['title']}")
            print(f"   URL: {post['url']}")
    
    # Berechne neue Größe
    total_size = sum(f.stat().st_size for f in posts_dir.rglob('*') if f.is_file())
    size_mb = total_size / (1024 * 1024)
    print(f"\n💾 NEUE GRÖSSE: {size_mb:.1f} MB")
    
    # Speichere Log
    log_file = posts_dir.parent / "cleanup_log.json"
    with open(log_file, 'w') as f:
        json.dump({
            'stats': stats,
            'removed_posts': stats['removed_folders']
        }, f, indent=2)
    print(f"📝 Log gespeichert: {log_file}")

def main():
    print("🚀 POSTS OHNE BILDER ENTFERNEN")
    print("="*60)
    remove_posts_without_proper_images()

if __name__ == "__main__":
    main()