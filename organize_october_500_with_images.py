#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Organisiert die Top 500 Oktober Posts und lädt Bilder herunter
Erstellt die gleiche Struktur wie data_all für Oktober
"""

import json
import urllib.request
import urllib.error
from pathlib import Path
import time
import random
import re

class OctoberPostOrganizer:
    def __init__(self):
        self.base_dir = Path("/Users/patrick/Desktop/Reddit/data_october")
        self.posts_dir = self.base_dir / "Posts"
        self.posts_dir.mkdir(parents=True, exist_ok=True)
        
        self.input_file = self.base_dir / "top_500_posts_october.json"
        
        self.stats = {
            'total': 0,
            'with_images': 0,
            'without_images': 0,
            'download_success': 0,
            'download_failed': 0,
            'text_posts': 0
        }
    
    def is_image_url(self, url):
        """Prüft ob URL ein Bild ist"""
        if not url:
            return False
        
        # Direkte Bildendungen
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        url_lower = url.lower()
        
        for ext in image_extensions:
            if ext in url_lower:
                return True
        
        # Reddit/Imgur Bilder
        if any(domain in url_lower for domain in ['i.redd.it', 'i.imgur.com', 'preview.redd.it']):
            return True
        
        return False
    
    def download_image(self, url, save_path):
        """Lädt ein Bild herunter"""
        try:
            # User-Agent Header hinzufügen
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Download mit Timeout
            with urllib.request.urlopen(req, timeout=10) as response:
                img_data = response.read()
            
            # Speichere Bild
            with open(save_path, 'wb') as f:
                f.write(img_data)
            
            return True
            
        except Exception as e:
            print(f"      ❌ Download fehlgeschlagen: {str(e)[:50]}")
            return False
    
    def create_post_folder(self, post, index):
        """Erstellt einen Post-Ordner mit allen Daten"""
        # Erstelle sicheren Ordnernamen
        safe_title = re.sub(r'[^\w\s-]', '', post['title'][:50]).strip()
        safe_title = re.sub(r'[-\s]+', '_', safe_title).lower()
        
        folder_name = f"post_{index:04d}_{safe_title}"
        post_dir = self.posts_dir / folder_name
        post_dir.mkdir(exist_ok=True)
        
        # Speichere post_data.json
        json_file = post_dir / "post_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(post, f, indent=2, ensure_ascii=False)
        
        # Erstelle info.txt für bessere Lesbarkeit
        info_file = post_dir / "info.txt"
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"Titel: {post['title']}\n")
            f.write(f"Subreddit: r/{post['subreddit']}\n")
            f.write(f"Score: {post['score']:,}\n")
            f.write(f"Autor: u/{post.get('author', '[deleted]')}\n")
            f.write(f"Kommentare: {post.get('num_comments', 0):,}\n")
            f.write(f"NSFW: {'Ja' if post.get('over_18') else 'Nein'}\n")
            f.write(f"URL: {post.get('url', '')}\n")
            
            if post.get('selftext'):
                f.write(f"\nText:\n{post['selftext'][:1000]}")
                if len(post['selftext']) > 1000:
                    f.write("\n... (gekürzt)")
        
        # Versuche Bild herunterzuladen wenn vorhanden
        url = post.get('url', '')
        if self.is_image_url(url):
            # Bestimme Dateiendung
            if '.gif' in url.lower():
                ext = '.gif'
            elif '.png' in url.lower():
                ext = '.png'
            elif '.webp' in url.lower():
                ext = '.webp'
            else:
                ext = '.jpg'
            
            image_path = post_dir / f"image{ext}"
            
            print(f"      ⬇️ Lade Bild herunter...")
            if self.download_image(url, image_path):
                self.stats['download_success'] += 1
                self.stats['with_images'] += 1
                print(f"      ✅ Bild gespeichert: image{ext}")
                return True, True  # Erfolg, mit Bild
            else:
                self.stats['download_failed'] += 1
                self.stats['without_images'] += 1
                return True, False  # Erfolg, ohne Bild
        else:
            # Text-Post oder Video
            if post.get('selftext'):
                self.stats['text_posts'] += 1
            self.stats['without_images'] += 1
            return True, False  # Erfolg, ohne Bild
    
    def organize_all_posts(self):
        """Organisiert alle Top 500 Posts"""
        print("📚 ORGANISIERE TOP 500 OKTOBER POSTS")
        print("="*60)
        
        # Lade Posts
        if not self.input_file.exists():
            print(f"❌ Datei nicht gefunden: {self.input_file}")
            return
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        
        print(f"📊 {len(posts)} Posts geladen")
        print(f"📁 Zielordner: {self.posts_dir}")
        print()
        
        # Verarbeite jeden Post
        for i, post in enumerate(posts, 1):
            self.stats['total'] += 1
            
            print(f"📝 Post {i}/{len(posts)}:")
            print(f"   Titel: {post['title'][:60]}...")
            print(f"   r/{post['subreddit']} | Score: {post['score']:,}")
            
            success, has_image = self.create_post_folder(post, i)
            
            # Kleine Pause zwischen Downloads
            if has_image:
                time.sleep(random.uniform(0.5, 1.5))
            
            # Status-Update alle 50 Posts
            if i % 50 == 0:
                self.print_progress(i, len(posts))
        
        # Finale Statistiken
        self.print_final_stats()
    
    def print_progress(self, current, total):
        """Zeigt Zwischenstand"""
        print("\n" + "-"*40)
        print(f"📊 FORTSCHRITT: {current}/{total} ({current*100/total:.1f}%)")
        print(f"   Mit Bildern: {self.stats['with_images']}")
        print(f"   Text-Posts: {self.stats['text_posts']}")
        print(f"   Downloads erfolgreich: {self.stats['download_success']}")
        print("-"*40 + "\n")
    
    def print_final_stats(self):
        """Zeigt finale Statistiken"""
        print("\n" + "="*60)
        print("✅ ORGANISATION ABGESCHLOSSEN!")
        print("="*60)
        print(f"📊 STATISTIKEN:")
        print(f"   Posts gesamt: {self.stats['total']}")
        print(f"   Mit Bildern: {self.stats['with_images']}")
        print(f"   Ohne Bilder: {self.stats['without_images']}")
        print(f"   Text-Posts: {self.stats['text_posts']}")
        print(f"   Downloads erfolgreich: {self.stats['download_success']}")
        print(f"   Downloads fehlgeschlagen: {self.stats['download_failed']}")
        
        # Berechne Ordnergröße
        total_size = 0
        for file in self.posts_dir.rglob('*'):
            if file.is_file():
                total_size += file.stat().st_size
        
        size_mb = total_size / (1024 * 1024)
        print(f"\n💾 SPEICHERPLATZ:")
        print(f"   Ordnergröße: {size_mb:.1f} MB")
        
        if size_mb > 500:
            print(f"   ⚠️ Zu groß für GitHub (>500 MB)")
            print(f"   ℹ️ Verwende cleanup-Script um Größe zu reduzieren")
        else:
            print(f"   ✅ OK für GitHub (<500 MB)")

def main():
    print("🚀 OKTOBER POST ORGANIZER")
    print("="*60)
    print("Dies organisiert die Top 500 Oktober Posts")
    print("und lädt verfügbare Bilder herunter.")
    print()
    
    organizer = OctoberPostOrganizer()
    organizer.organize_all_posts()

if __name__ == "__main__":
    main()