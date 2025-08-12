#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Filtert Top Posts aus Planner/Organisation Subreddits
aus November Daten und fügt sie zu data_all hinzu
"""

import json
import zstandard as zstd
from pathlib import Path
import time
import urllib.request
import re
import shutil

class PlannerSubredditFilter:
    def __init__(self):
        self.data_all_dir = Path("/Users/patrick/Desktop/Reddit/data_all/Posts")
        
        # Versuche verschiedene Pfade für November Daten
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
        
        # Target Planner/Organisation Subreddits
        self.target_subreddits = {
            # Planner Communities
            'planners', 'planneraddicts', 'bujo', 'basicbulletjournals',
            
            # Digital Planning
            'notion', 'notiontemplates', 'digitalplanning', 'digitalplanner',
            
            # Study Planning
            'studyplanner', 'studytips', 'getstudying',
            
            # Life Management
            'lifeplanning', 'thexeffect', 'nonzeroday',
            
            # Productivity
            'timemanagement', 'getorganized', 'gtd',
            
            # Journaling
            'journaling', 'notebooks', 'weeklyplanning', 'dailyplanning'
        }
        
        # Lade bereits vorhandene Posts
        self.existing_posts = set()
        self.existing_titles = set()
        self._load_existing_posts()
        
        # Stats
        self.stats = {
            'total_processed': 0,
            'target_subs_found': 0,
            'high_score': 0,
            'already_exists': 0,
            'new_posts': 0,
            'with_images': 0,
            'download_success': 0
        }
        
        # Zähle Posts pro Subreddit
        self.subreddit_counts = {sub: 0 for sub in self.target_subreddits}
    
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
        
        folder_name = f"planner_{index:04d}_{safe_title}"
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
    
    def filter_planner_posts(self):
        """Filtert Top Posts aus Planner/Organisation Subreddits"""
        print("\n🗓️ FILTERE PLANNER/ORGANISATION SUBREDDIT POSTS")
        print("="*60)
        print(f"📋 Target Subreddits ({len(self.target_subreddits)}): ")
        print(f"   {', '.join(sorted(self.target_subreddits)[:10])}...")
        print(f"📊 Überspringe {len(self.existing_posts)} bereits vorhandene Posts")
        print()
        
        if not self.november_file or not self.november_file.exists():
            print(f"❌ November-Datei nicht gefunden")
            return
        
        # Sammle Top-Posts aus Target Subreddits
        planner_posts = []
        MIN_SCORE = 100  # Niedrigerer Score für Nischen-Subreddits
        
        print(f"📂 Durchsuche November-Daten nach Planner Posts (Score ≥ {MIN_SCORE})...")
        print(f"   Datei: {self.november_file.name}")
        
        import io
        
        # Öffne Datei je nach Format
        if self.is_compressed:
            # Komprimierte .zst Datei
            dctx = zstd.ZstdDecompressor()
            with open(self.november_file, 'rb') as fh:
                with dctx.stream_reader(fh) as reader:
                    text_stream = io.TextIOWrapper(reader, encoding='utf-8')
                    self._process_lines(text_stream, planner_posts, MIN_SCORE)
        else:
            # JSONL Datei
            with open(self.november_file, 'r', encoding='utf-8') as text_stream:
                self._process_lines(text_stream, planner_posts, MIN_SCORE)
        
        # Sortiere nach Score und nimm Top Posts
        planner_posts.sort(key=lambda x: x['score'], reverse=True)
        
        # Nimm maximal 50 Posts (oder weniger wenn nicht genug gefunden)
        top_posts = planner_posts[:50]
        
        print(f"\n✅ {len(top_posts)} Planner Posts gefunden!")
        
        if not top_posts:
            print("❌ Keine Posts aus Target Subreddits gefunden")
            return
        
        print(f"   Score-Range: {top_posts[-1]['score']:,} - {top_posts[0]['score']:,}")
        
        # Zeige Top 10
        print("\n🏆 TOP 10 PLANNER/ORGANISATION POSTS:")
        print("-"*60)
        for i, post in enumerate(top_posts[:10], 1):
            print(f"{i:2}. Score {post['score']:,} | r/{post['subreddit']}")
            print(f"    {post['title'][:60]}...")
        
        # Zeige Subreddit Verteilung
        print("\n📊 POSTS PRO SUBREDDIT:")
        for sub in sorted(self.target_subreddits):
            count = sum(1 for p in top_posts if p['subreddit'].lower() == sub)
            if count > 0:
                print(f"   r/{sub}: {count} Posts")
        
        # Erstelle Post-Ordner mit Bildern
        print("\n📥 ERSTELLE POSTS IN DATA_ALL:")
        print("-"*60)
        
        successful = 0
        for i, post in enumerate(top_posts, 1):
            print(f"\n📝 Post {i}/{len(top_posts)}: {post['title'][:50]}...")
            print(f"   r/{post['subreddit']} | Score: {post['score']:,}")
            
            if self.create_post_folder(post, i):
                successful += 1
                self.stats['new_posts'] += 1
                
                # Pause zwischen Downloads
                if self.stats['with_images'] > 0:
                    time.sleep(1)
            
            # Status alle 10 Posts
            if i % 10 == 0:
                print(f"\n--- Fortschritt: {i}/{len(top_posts)} | Erfolgreich: {successful} ---")
        
        # Finale Statistiken
        self.print_stats(successful)
    
    def _process_lines(self, text_stream, planner_posts, MIN_SCORE):
        """Verarbeitet die Zeilen der Datei"""
        MAX_LINES = 5000000  # Max 5M Zeilen
        
        for line_num, line in enumerate(text_stream, 1):
            self.stats['total_processed'] += 1
            
            # Stoppe nach MAX_LINES oder wenn genug Posts gefunden
            if line_num > MAX_LINES or len(planner_posts) >= 200:
                print(f"   ⏹️ Stoppe nach {line_num:,} Zeilen (gefunden: {len(planner_posts)} Planner Posts)")
                break
            
            if self.stats['total_processed'] % 100000 == 0:
                print(f"   📊 {self.stats['total_processed']:,} Posts durchsucht | "
                      f"Planner Posts: {len(planner_posts)}")
            
            try:
                post = json.loads(line)
                
                # Prüfe ob aus Target Subreddit
                subreddit = post.get('subreddit', '').lower()
                if subreddit not in self.target_subreddits:
                    continue
                
                self.stats['target_subs_found'] += 1
                
                score = int(post.get('score', 0))
                
                # Skip wenn Score zu niedrig
                if score < MIN_SCORE:
                    continue
                
                self.stats['high_score'] += 1
                
                # Skip wenn bereits vorhanden (ID oder Titel)
                post_id = post.get('id', '')
                post_title = post.get('title', '')
                
                if post_id in self.existing_posts or post_title in self.existing_titles:
                    self.stats['already_exists'] += 1
                    continue
                
                # Füge zu Planner Posts hinzu
                planner_posts.append({
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
                
                self.subreddit_counts[subreddit] += 1
                
            except:
                continue
    
    def print_stats(self, successful):
        """Zeigt finale Statistiken"""
        print("\n" + "="*60)
        print("✅ FILTER ABGESCHLOSSEN!")
        print("="*60)
        print(f"📊 STATISTIKEN:")
        print(f"   Posts durchsucht: {self.stats['total_processed']:,}")
        print(f"   Aus Target Subreddits: {self.stats['target_subs_found']:,}")
        print(f"   Mit hohem Score: {self.stats['high_score']:,}")
        print(f"   Bereits vorhanden: {self.stats['already_exists']}")
        print(f"   NEUE Posts erstellt: {successful}")
        print(f"   Mit Bildern: {self.stats['with_images']}")
        print(f"   Downloads erfolgreich: {self.stats['download_success']}")
        
        # Berechne neue Größe
        total_size = sum(f.stat().st_size for f in self.data_all_dir.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"\n💾 NEUE GRÖSSE data_all: {size_mb:.1f} MB")

def main():
    print("🗓️ PLANNER/ORGANISATION SUBREDDIT FILTER")
    print("="*60)
    print("Sucht Posts aus:")
    print("• Planner Communities (planners, bujo, etc.)")
    print("• Digital Planning (Notion, etc.)")
    print("• Study Planning")
    print("• Life Management")
    print("• Productivity & Journaling")
    print()
    
    filter = PlannerSubredditFilter()
    filter.filter_planner_posts()

if __name__ == "__main__":
    main()