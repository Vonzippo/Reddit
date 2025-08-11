#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Prüft alle Bilder in data_all/Posts auf Upload-Tauglichkeit
- Größe, Format, NSFW-Content, etc.
"""

import json
from pathlib import Path
from PIL import Image
import os

class ImageChecker:
    def __init__(self):
        self.posts_dir = Path("/Users/patrick/Desktop/Reddit/data_all/Posts")
        self.stats = {
            'total_posts': 0,
            'with_images': 0,
            'without_images': 0,
            'nsfw_posts': 0,
            'safe_posts': 0,
            'large_images': 0,
            'gif_files': 0,
            'jpg_files': 0,
            'png_files': 0,
            'problematic': []
        }
        
        # NSFW Subreddits die wir vermeiden sollten
        self.nsfw_subreddits = {
            'nsfw', 'gonewild', 'realgirls', 'porn', 'hentai', 
            'boobs', 'ass', 'pussy', 'cock', 'penis', 'nude',
            'xxx', 'sex', 'fuck', 'horny', 'onlyfans',
            'gaynsfw', 'gayporn', 'transporn', 'futanari',
            'cumsluts', 'blowjobs', 'milf', 'teen', 'jailbait'
        }
        
        # Problematische Keywords in Titeln
        self.nsfw_keywords = {
            'nsfw', 'nude', 'naked', 'porn', 'sex', 'fuck',
            'cock', 'dick', 'pussy', 'tits', 'boobs', 'ass',
            'cum', 'masturbat', 'orgasm', 'erotic', '18+',
            'onlyfans', 'fansly', 'xxx', 'horny', 'fetish'
        }
    
    def check_nsfw_content(self, post_data):
        """Prüft ob Post NSFW-Content enthält"""
        # Check NSFW Flag
        if post_data.get('over_18', False):
            return True
        
        # Check Subreddit
        subreddit = post_data.get('subreddit', '').lower()
        for nsfw_sub in self.nsfw_subreddits:
            if nsfw_sub in subreddit:
                return True
        
        # Check Title
        title = post_data.get('title', '').lower()
        for keyword in self.nsfw_keywords:
            if keyword in title:
                return True
        
        return False
    
    def check_all_posts(self):
        """Prüft alle Posts"""
        print("🔍 Prüfe alle Bilder in data_all/Posts...")
        print("="*60)
        
        safe_posts = []
        nsfw_posts = []
        
        for post_dir in sorted(self.posts_dir.iterdir()):
            if not post_dir.is_dir():
                continue
            
            self.stats['total_posts'] += 1
            
            # Lade post_data.json
            json_file = post_dir / "post_data.json"
            if not json_file.exists():
                continue
            
            with open(json_file, 'r') as f:
                post_data = json.load(f)
            
            # Prüfe auf NSFW
            is_nsfw = self.check_nsfw_content(post_data)
            
            # Prüfe ob Bild existiert
            has_image = False
            image_info = {}
            
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                img_path = post_dir / f"image{ext}"
                if img_path.exists():
                    has_image = True
                    
                    # Bildinfo sammeln
                    size_mb = img_path.stat().st_size / (1024 * 1024)
                    image_info = {
                        'path': img_path,
                        'size_mb': size_mb,
                        'format': ext,
                        'dir': post_dir.name
                    }
                    
                    # Stats
                    self.stats['with_images'] += 1
                    if ext == '.gif':
                        self.stats['gif_files'] += 1
                    elif ext in ['.jpg', '.jpeg']:
                        self.stats['jpg_files'] += 1
                    elif ext == '.png':
                        self.stats['png_files'] += 1
                    
                    if size_mb > 10:
                        self.stats['large_images'] += 1
                    
                    break
            
            if not has_image:
                self.stats['without_images'] += 1
                continue
            
            # Kategorisiere
            post_info = {
                'title': post_data.get('title', ''),
                'subreddit': post_data.get('subreddit', ''),
                'score': post_data.get('score', 0),
                'url': post_data.get('url', ''),
                'image': image_info,
                'is_nsfw': is_nsfw,
                'dir': post_dir.name
            }
            
            if is_nsfw:
                nsfw_posts.append(post_info)
                self.stats['nsfw_posts'] += 1
            else:
                safe_posts.append(post_info)
                self.stats['safe_posts'] += 1
        
        # Zeige Ergebnisse
        self.print_results(safe_posts, nsfw_posts)
        
        # Speichere sichere Posts
        self.save_safe_posts(safe_posts)
        
        return safe_posts, nsfw_posts
    
    def print_results(self, safe_posts, nsfw_posts):
        """Zeigt Prüfergebnisse"""
        print("\n📊 PRÜFERGEBNISSE:")
        print("="*60)
        print(f"Posts gesamt: {self.stats['total_posts']}")
        print(f"Mit Bildern: {self.stats['with_images']}")
        print(f"Ohne Bilder: {self.stats['without_images']}")
        print()
        print(f"✅ SICHERE Posts: {self.stats['safe_posts']}")
        print(f"⚠️  NSFW Posts: {self.stats['nsfw_posts']}")
        print()
        print(f"Bildformate:")
        print(f"  JPG/JPEG: {self.stats['jpg_files']}")
        print(f"  PNG: {self.stats['png_files']}")
        print(f"  GIF: {self.stats['gif_files']}")
        print(f"  Große Bilder (>10MB): {self.stats['large_images']}")
        
        if nsfw_posts:
            print("\n⚠️ NSFW POSTS (nicht hochladen!):")
            print("-"*60)
            for post in nsfw_posts[:10]:
                print(f"  r/{post['subreddit']}: {post['title'][:50]}...")
        
        print("\n✅ TOP 20 SICHERE POSTS (OK zum Upload):")
        print("-"*60)
        for i, post in enumerate(safe_posts[:20], 1):
            size = post['image']['size_mb']
            print(f"{i:2}. Score {post['score']:,} | r/{post['subreddit']} | {size:.1f}MB")
            print(f"    {post['title'][:60]}...")
        
        # Warnung für große Bilder
        large_safe = [p for p in safe_posts if p['image']['size_mb'] > 10]
        if large_safe:
            print("\n⚠️ GROSSE BILDER (>10MB) - evtl. problematisch:")
            for post in large_safe:
                print(f"  {post['image']['size_mb']:.1f}MB - {post['title'][:40]}...")
    
    def save_safe_posts(self, safe_posts):
        """Speichert Liste sicherer Posts"""
        output_file = self.posts_dir.parent / "safe_posts_for_upload.json"
        
        # Erstelle kompakte Liste
        safe_list = []
        for post in safe_posts:
            safe_list.append({
                'dir': post['dir'],
                'title': post['title'],
                'subreddit': post['subreddit'],
                'score': post['score'],
                'image_size_mb': post['image']['size_mb'],
                'image_format': post['image']['format']
            })
        
        with open(output_file, 'w') as f:
            json.dump({
                'total_safe': len(safe_list),
                'posts': safe_list
            }, f, indent=2)
        
        print(f"\n💾 Sichere Posts gespeichert: {output_file}")
        print(f"   {len(safe_list)} Posts sind sicher zum Upload")

def main():
    print("🔍 IMAGE CHECKER FÜR REDDIT POSTS")
    print("="*60)
    
    checker = ImageChecker()
    safe_posts, nsfw_posts = checker.check_all_posts()
    
    print("\n" + "="*60)
    print("✅ EMPFEHLUNG:")
    if len(safe_posts) > 150:
        print(f"  {len(safe_posts)} sichere Posts gefunden!")
        print("  Diese können problemlos hochgeladen werden.")
    else:
        print(f"  Nur {len(safe_posts)} sichere Posts.")
        print("  Eventuell Filter anpassen.")
    
    if nsfw_posts:
        print(f"\n⚠️  {len(nsfw_posts)} NSFW Posts sollten NICHT hochgeladen werden!")

if __name__ == "__main__":
    main()