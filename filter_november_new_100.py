#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Filtert neue Top 100 Posts aus November
- Ohne bereits vorhandene Posts
- Ohne adhdwomen, ADHDmemes, adhdmeme
- Mit Bilddownload direkt zu data_all
"""

import json
import zstandard as zstd
from pathlib import Path
import time
import urllib.request
import re
import shutil

class NovemberNewPostFilter:
    def __init__(self):
        self.data_all_dir = Path("/Users/patrick/Desktop/Reddit/data_all/Posts")
        # Versuche verschiedene Pfade
        possible_paths = [
            Path("/Users/patrick/Desktop/Reddit/pushshift_dumps/reddit/november/reddit/submissions/RS_2024-11.zst"),
            Path("/Users/patrick/Desktop/Reddit/pushshift_dumps/2024_posts_filtered/RS_2024-11_filtered.jsonl"),
            Path("/Users/patrick/Desktop/Reddit/pushshift_dumps/2024_filtered/RC_2024-11_filtered.jsonl")
        ]
        
        self.november_file = None
        for path in possible_paths:
            if path.exists():
                self.november_file = path
                self.is_compressed = path.suffix == '.zst'
                break
        
        if not self.november_file:
            print("❌ Keine November-Datei gefunden!")
        
        # Blacklist Subreddits
        self.blacklist_subs = {
            'adhdwomen', 'adhd_women',
            'adhdmemes', 'adhd_memes', 
            'adhdmeme', 'adhd_meme'
        }
        
        # Sammle bereits vorhandene Post-IDs und Titel
        self.existing_posts = set()
        self.existing_titles = set()
        self._load_existing_posts()
        
        self.stats = {
            'total_processed': 0,
            'high_score': 0,
            'blacklisted': 0,
            'already_exists': 0,
            'new_posts': 0,
            'with_images': 0,
            'download_success': 0
        }
    
    def _load_existing_posts(self):
        """Lädt IDs und Titel aller bereits vorhandenen Posts"""
        print("📂 Lade vorhandene Posts aus data_all...")
        
        for post_dir in self.data_all_dir.iterdir():
            if post_dir.is_dir():
                json_file = post_dir / "post_data.json"
                if json_file.exists():
                    try:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                            # Sammle ID und Titel
                            if data.get('id'):
                                self.existing_posts.add(data['id'])
                            if data.get('title'):
                                self.existing_titles.add(data['title'])
                    except:
                        continue
        
        print(f"✅ {len(self.existing_posts)} vorhandene Posts geladen")
    
    def is_image_url(self, url):
        """Prüft ob URL ein Bild ist"""
        if not url:
            return False
        
        url_lower = url.lower()
        image_indicators = [
            '.jpg', '.jpeg', '.png', '.gif', '.webp',
            'i.redd.it', 'i.imgur.com', 'preview.redd.it'
        ]
        
        return any(indicator in url_lower for indicator in image_indicators)
    
    def download_image(self, url, save_path):
        """Lädt ein Bild herunter"""
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                img_data = response.read()
            
            with open(save_path, 'wb') as f:
                f.write(img_data)
            
            return True
        except Exception as e:
            print(f"      ❌ Download fehlgeschlagen: {str(e)[:50]}")
            return False
    
    def create_post_folder(self, post_data, index):
        """Erstellt Post-Ordner in data_all mit Bild"""
        # Erstelle sicheren Ordnernamen
        safe_title = re.sub(r'[^\w\s-]', '', post_data['title'][:50]).strip()
        safe_title = re.sub(r'[-\s]+', '_', safe_title).lower()
        
        folder_name = f"post_nov_{index:04d}_{safe_title}"
        post_dir = self.data_all_dir / folder_name
        post_dir.mkdir(exist_ok=True)
        
        # Speichere post_data.json
        json_file = post_dir / "post_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        
        # Versuche Bild herunterzuladen
        url = post_data.get('url', '')
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
            
            if self.download_image(url, image_path):
                self.stats['download_success'] += 1
                self.stats['with_images'] += 1
                print(f"      ✅ Bild gespeichert")
                return True
            else:
                # Lösche Ordner wenn kein Bild
                shutil.rmtree(post_dir)
                return False
        elif post_data.get('selftext'):
            # Text-Post ist OK
            return True
        else:
            # Kein Bild und kein Text -> löschen
            shutil.rmtree(post_dir)
            return False
    
    def filter_new_posts(self):
        """Filtert neue Top 100 Posts aus November"""
        print("\n🚀 FILTERE NEUE TOP 100 NOVEMBER POSTS")
        print("="*60)
        print(f"❌ Blacklist: {', '.join(self.blacklist_subs)}")
        print(f"📊 Überspringe {len(self.existing_posts)} bereits vorhandene Posts")
        print()
        
        if not self.november_file.exists():
            print(f"❌ November-Datei nicht gefunden: {self.november_file}")
            return
        
        # Sammle Top-Posts
        top_posts = []
        MIN_SCORE = 1000  # Hochwertige Posts (gesenkt von 10000)
        
        print(f"📂 Durchsuche November-Daten (Score ≥ {MIN_SCORE:,})...")
        print(f"   Datei: {self.november_file.name}")
        
        import io
        
        # Öffne Datei je nach Format
        if self.is_compressed:
            # Komprimierte .zst Datei
            dctx = zstd.ZstdDecompressor()
            with open(self.november_file, 'rb') as fh:
                with dctx.stream_reader(fh) as reader:
                    text_stream = io.TextIOWrapper(reader, encoding='utf-8')
                    self._process_lines(text_stream, top_posts, MIN_SCORE)
        else:
            # JSONL Datei
            with open(self.november_file, 'r', encoding='utf-8') as text_stream:
                self._process_lines(text_stream, top_posts, MIN_SCORE)
        
        # Sortiere nach Score und nimm Top 100
        top_posts.sort(key=lambda x: x['score'], reverse=True)
        top_100 = top_posts[:100]
        
        print(f"\n✅ {len(top_100)} neue Posts gefunden!")
        
        if not top_100:
            print("❌ Keine neuen Posts gefunden")
            return
        
        print(f"   Score-Range: {top_100[-1]['score']:,} - {top_100[0]['score']:,}")
        
        # Zeige Top 10
        print("\n🏆 TOP 10 NEUE POSTS:")
        print("-"*60)
        for i, post in enumerate(top_100[:10], 1):
            print(f"{i:2}. Score {post['score']:,} | r/{post['subreddit']}")
            print(f"    {post['title'][:60]}...")
        
        # Erstelle Post-Ordner mit Bildern
        print("\n📥 ERSTELLE POSTS IN DATA_ALL:")
        print("-"*60)
        
        successful = 0
        for i, post in enumerate(top_100, 1):
            print(f"\n📝 Post {i}/100: {post['title'][:50]}...")
            print(f"   r/{post['subreddit']} | Score: {post['score']:,}")
            
            if self.create_post_folder(post, i):
                successful += 1
                self.stats['new_posts'] += 1
                
                # Pause zwischen Downloads
                if self.stats['with_images'] > 0:
                    time.sleep(1)
            
            # Status alle 20 Posts
            if i % 20 == 0:
                print(f"\n--- Fortschritt: {i}/100 | Erfolgreich: {successful} ---")
        
        # Finale Statistiken
        self.print_stats(successful)
    
    def _process_lines(self, text_stream, top_posts, MIN_SCORE):
        """Verarbeitet die Zeilen der Datei"""
        MAX_LINES = 5000000  # Max 5M Zeilen
        for line_num, line in enumerate(text_stream, 1):
            self.stats['total_processed'] += 1
            
            # Stoppe nach MAX_LINES oder wenn genug Posts gefunden
            if line_num > MAX_LINES or len(top_posts) >= 500:
                print(f"   ⏹️ Stoppe nach {line_num:,} Zeilen (gefunden: {len(top_posts)})")
                break
            
            if self.stats['total_processed'] % 100000 == 0:
                print(f"   📊 {self.stats['total_processed']:,} Posts durchsucht | "
                      f"Gefunden: {len(top_posts)}")
            
            try:
                post = json.loads(line)
                score = int(post.get('score', 0))
                
                # Skip wenn Score zu niedrig
                if score < MIN_SCORE:
                    continue
                
                self.stats['high_score'] += 1
                
                # Skip wenn Blacklist-Subreddit
                subreddit = post.get('subreddit', '').lower()
                if any(black in subreddit for black in self.blacklist_subs):
                    self.stats['blacklisted'] += 1
                    continue
                
                # Skip wenn bereits vorhanden (ID oder Titel)
                post_id = post.get('id', '')
                post_title = post.get('title', '')
                
                if post_id in self.existing_posts or post_title in self.existing_titles:
                    self.stats['already_exists'] += 1
                    continue
                
                # Füge zu Top-Posts hinzu
                top_posts.append({
                    'id': post_id,
                    'title': post_title,
                    'score': score,
                    'subreddit': post.get('subreddit', ''),
                    'url': post.get('url', ''),
                    'selftext': post.get('selftext', ''),
                    'author': post.get('author', ''),
                    'created_utc': post.get('created_utc', 0),
                    'num_comments': post.get('num_comments', 0),
                    'over_18': post.get('over_18', False),
                    'permalink': post.get('permalink', ''),
                    'link_flair_text': post.get('link_flair_text', '')
                })
                
            except:
                continue
    
    def print_stats(self, successful):
        """Zeigt finale Statistiken"""
        print("\n" + "="*60)
        print("✅ FILTER ABGESCHLOSSEN!")
        print("="*60)
        print(f"📊 STATISTIKEN:")
        print(f"   Posts durchsucht: {self.stats['total_processed']:,}")
        print(f"   Mit hohem Score: {self.stats['high_score']:,}")
        print(f"   Blacklist übersprungen: {self.stats['blacklisted']}")
        print(f"   Bereits vorhanden: {self.stats['already_exists']}")
        print(f"   NEUE Posts erstellt: {successful}")
        print(f"   Mit Bildern: {self.stats['with_images']}")
        print(f"   Downloads erfolgreich: {self.stats['download_success']}")
        
        # Berechne neue Größe
        total_size = sum(f.stat().st_size for f in self.data_all_dir.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"\n💾 NEUE GRÖSSE data_all: {size_mb:.1f} MB")

def main():
    print("🔍 NOVEMBER TOP 100 NEUE POSTS FILTER")
    print("="*60)
    print("Sucht neue Posts die:")
    print("• NICHT bereits in data_all sind")
    print("• NICHT aus adhdwomen/ADHDmemes/adhdmeme sind")
    print("• Hohen Score haben (≥10k)")
    print("• Bilder haben oder Text-Posts sind")
    print()
    
    filter = NovemberNewPostFilter()
    filter.filter_new_posts()

if __name__ == "__main__":
    main()