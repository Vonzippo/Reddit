#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Organisiert die Top 1000 Posts mit Bildern in der gleichen Struktur wie data/Posts
Lädt Bilder herunter und erstellt die komplette Ordnerstruktur
"""

import json
import urllib.request
import time
import random
from pathlib import Path
from datetime import datetime
import hashlib
import re

class Top1000Organizer:
    def __init__(self):
        self.input_file = Path("/Users/patrick/Desktop/Reddit/data_all/real_top_200_posts.jsonl")
        self.output_dir = Path("/Users/patrick/Desktop/Reddit/data_all/Posts")
        self.output_dir.mkdir(exist_ok=True)
        
        # Statistiken
        self.stats = {
            'total': 0,
            'with_images': 0,
            'images_downloaded': 0,
            'images_failed': 0,
            'text_posts': 0,
            'link_posts': 0
        }
    
    def sanitize_filename(self, text, max_length=50):
        """Erstellt einen sicheren Dateinamen aus Text"""
        # Entferne/ersetze problematische Zeichen
        text = re.sub(r'[^\w\s-]', '', text.lower())
        text = re.sub(r'[-\s]+', '_', text)
        
        # Kürze auf max_length
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip('_')
    
    def download_image(self, url, save_path):
        """Lädt ein Bild herunter und speichert es"""
        try:
            # Verschiedene Image-Hosting Services handhaben
            if 'i.redd.it' in url:
                # Reddit hosted images
                pass
            elif 'imgur.com' in url and not url.endswith(('.jpg', '.png', '.gif', '.jpeg')):
                # Imgur links ohne Endung
                if '/a/' not in url and '/gallery/' not in url:
                    # Direkter Imgur Link - füge .jpg hinzu
                    url = url + '.jpg'
            elif 'v.redd.it' in url:
                # Reddit Videos - überspringe
                print(f"      ⚠️ Video-Post, überspringe: {url[:50]}...")
                return False
            elif 'reddit.com/gallery' in url:
                # Reddit Gallery - komplexer, überspringe erstmal
                print(f"      ⚠️ Gallery-Post, überspringe: {url[:50]}...")
                return False
            
            # User-Agent setzen (wichtig für viele Seiten)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            # Download mit Timeout
            with urllib.request.urlopen(req, timeout=10) as response:
                # Prüfe Content-Type
                content_type = response.headers.get('Content-Type', '')
                
                if 'image' not in content_type and 'video' not in content_type:
                    print(f"      ⚠️ Kein Bild-Content: {content_type}")
                    return False
                
                # Lese Bild-Daten
                img_data = response.read()
                
                # Bestimme Dateiendung basierend auf Content-Type
                if 'gif' in content_type:
                    ext = '.gif'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'
                
                # Speichere Bild
                image_path = save_path / f"image{ext}"
                with open(image_path, 'wb') as f:
                    f.write(img_data)
                
                # Größe prüfen
                size_mb = len(img_data) / (1024 * 1024)
                print(f"      ✅ Bild gespeichert: {ext} ({size_mb:.1f} MB)")
                return True
                
        except urllib.error.HTTPError as e:
            print(f"      ❌ HTTP Error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            print(f"      ❌ URL Error: {e.reason}")
        except Exception as e:
            print(f"      ❌ Download-Fehler: {str(e)[:100]}")
        
        return False
    
    def process_posts(self):
        """Verarbeitet alle Top 1000 Posts"""
        if not self.input_file.exists():
            print(f"❌ Datei nicht gefunden: {self.input_file}")
            return
        
        print(f"📂 Lese Top 200 Posts aus: {self.input_file}")
        
        # Lade alle Posts
        posts = []
        with open(self.input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    posts.append(json.loads(line))
        
        print(f"✅ {len(posts)} Posts geladen")
        print("="*60)
        
        # Verarbeite jeden Post
        for idx, post in enumerate(posts, 1):
            self.stats['total'] += 1
            
            # Erstelle Ordnername
            title_clean = self.sanitize_filename(post.get('title', 'untitled'))
            folder_name = f"post_{idx:04d}_{title_clean}"
            post_dir = self.output_dir / folder_name
            post_dir.mkdir(exist_ok=True)
            
            print(f"\n📝 Post #{idx}/200: r/{post.get('subreddit', 'unknown')}")
            print(f"   Titel: {post.get('title', '')[:60]}...")
            print(f"   Score: {post.get('score', 0):,}")
            
            # Prüfe ob es ein Bild-Post ist
            url = post.get('url', '')
            is_image = False
            
            if url:
                # Prüfe URL auf Bild-Endungen oder bekannte Image-Hosts
                image_indicators = [
                    '.jpg', '.jpeg', '.png', '.gif', '.webp',
                    'i.redd.it', 'imgur.com', 'i.imgur.com'
                ]
                is_image = any(indicator in url.lower() for indicator in image_indicators)
            
            # Lade Bild wenn vorhanden
            if is_image:
                print(f"   🖼️ Bild-URL gefunden: {url[:50]}...")
                if self.download_image(url, post_dir):
                    self.stats['with_images'] += 1
                    self.stats['images_downloaded'] += 1
                else:
                    self.stats['images_failed'] += 1
            elif post.get('selftext'):
                print(f"   📄 Text-Post (kein Bild)")
                self.stats['text_posts'] += 1
            else:
                print(f"   🔗 Link-Post: {url[:50]}...")
                self.stats['link_posts'] += 1
            
            # Speichere post_data.json
            post_data_file = post_dir / "post_data.json"
            with open(post_data_file, 'w', encoding='utf-8') as f:
                json.dump(post, f, indent=2, ensure_ascii=False)
            
            # Erstelle info.txt
            info_file = post_dir / "info.txt"
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(f"Post #{idx}\n")
                f.write(f"="*50 + "\n")
                f.write(f"Titel: {post.get('title', 'N/A')}\n")
                f.write(f"Subreddit: r/{post.get('subreddit', 'N/A')}\n")
                f.write(f"Autor: u/{post.get('author', '[deleted]')}\n")
                f.write(f"Score: {post.get('score', 0):,}\n")
                f.write(f"Kommentare: {post.get('num_comments', 0):,}\n")
                f.write(f"Erstellt: {post.get('created_utc', 'N/A')}\n")
                f.write(f"URL: {post.get('url', 'N/A')}\n")
                
                if post.get('selftext'):
                    f.write(f"\nText:\n{post.get('selftext')[:500]}...\n")
                
                if post.get('link_flair_text'):
                    f.write(f"\nFlair: {post.get('link_flair_text')}\n")
            
            # Kleine Pause zwischen Downloads (höflich zu Servern)
            if is_image and idx < len(posts):
                delay = random.uniform(0.5, 1.5)
                time.sleep(delay)
            
            # Status-Update alle 50 Posts
            if idx % 50 == 0:
                self.print_progress(idx, len(posts))
        
        # Finale Statistiken
        self.print_final_stats()
    
    def print_progress(self, current, total):
        """Zeigt Fortschritt an"""
        percent = (current / total) * 100
        print("\n" + "="*60)
        print(f"⏳ FORTSCHRITT: {current}/{total} ({percent:.1f}%)")
        print(f"   Mit Bildern: {self.stats['with_images']}")
        print(f"   Downloads erfolgreich: {self.stats['images_downloaded']}")
        print(f"   Downloads fehlgeschlagen: {self.stats['images_failed']}")
        print("="*60)
    
    def print_final_stats(self):
        """Zeigt finale Statistiken"""
        print("\n" + "="*60)
        print("✅ VERARBEITUNG ABGESCHLOSSEN!")
        print("="*60)
        print(f"📊 STATISTIKEN:")
        print(f"   Posts gesamt: {self.stats['total']}")
        print(f"   Mit Bildern: {self.stats['with_images']}")
        print(f"   Bilder heruntergeladen: {self.stats['images_downloaded']}")
        print(f"   Bilder fehlgeschlagen: {self.stats['images_failed']}")
        print(f"   Text-Posts: {self.stats['text_posts']}")
        print(f"   Link-Posts: {self.stats['link_posts']}")
        
        success_rate = 0
        if self.stats['with_images'] > 0:
            success_rate = (self.stats['images_downloaded'] / self.stats['with_images']) * 100
        
        print(f"\n   Download-Erfolgsrate: {success_rate:.1f}%")
        print(f"   Ausgabe-Ordner: {self.output_dir}")
        
        # Zeige Ordner-Größe
        total_size = sum(f.stat().st_size for f in self.output_dir.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"   Gesamtgröße: {size_mb:.1f} MB")

def main():
    print("🚀 TOP 1000 POSTS ORGANIZER")
    print("="*60)
    print("Organisiert die Top 1000 Posts mit Bildern")
    print("Struktur: data_all/Posts/post_XXXX/")
    print("="*60)
    
    organizer = Top1000Organizer()
    
    # Sicherheitsabfrage
    print("\n⚠️ WARNUNG:")
    print("   - Lädt bis zu 200 Bilder herunter")
    print("   - Kann mehrere Minuten dauern")
    print("   - Benötigt ~100-500 MB Speicherplatz")
    
    # Auto-confirm für automatische Ausführung
    auto_run = True
    
    if auto_run or input("\nFortfahren? (ja/nein): ").strip().lower() in ['ja', 'j', 'yes', 'y']:
        print("\n🔄 Starte Verarbeitung...")
        try:
            organizer.process_posts()
        except KeyboardInterrupt:
            print("\n\n❌ Abgebrochen durch Benutzer")
        except Exception as e:
            print(f"\n❌ Fehler: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Abgebrochen")

if __name__ == "__main__":
    main()