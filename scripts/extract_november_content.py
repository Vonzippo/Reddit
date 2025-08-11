#!/usr/bin/env python3
"""
Extrahiert Top 50 Posts und Top 100 Kommentare aus November 2024
Identisch zu Dezember-Extraktion, nur für November-Daten
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
import threading
import heapq
import time

class NovemberContentExtractor:
    def __init__(self):
        self.posts_file = Path("pushshift_dumps/2024_posts_filtered/RS_2024-11_filtered.jsonl")
        self.comments_file = Path("pushshift_dumps/2024_filtered/RC_2024-11_filtered.jsonl")
        self.output_dir = Path("november_top_content")
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_top_posts(self, limit=50):
        """Extrahiert die Top Posts mit Multithreading"""
        print(f"\n📊 Extrahiere Top {limit} Posts aus November 2024...")
        print(f"  ⚡ Nutze {cpu_count()} CPU Cores für parallele Verarbeitung")
        
        if not self.posts_file.exists():
            print(f"  ⚠️ Warte auf gefilterte Posts: {self.posts_file}")
            return []
        
        start_time = time.time()
        
        # Thread-safe heap für Top Posts
        top_heap = []
        heap_lock = threading.Lock()
        processed_count = 0
        count_lock = threading.Lock()
        
        def process_lines_batch(lines_batch):
            """Verarbeitet einen Batch von Zeilen"""
            nonlocal processed_count
            local_posts = []
            
            for line in lines_batch:
                try:
                    post = json.loads(line)
                    score = post.get('score', 0)
                    if score > 100:  # Mindest-Score
                        local_posts.append((score, post))
                except:
                    continue
            
            # Update heap thread-safe (mit ID für eindeutige Sortierung)
            with heap_lock:
                for score, post in local_posts:
                    item_id = post.get('id', str(score))
                    if len(top_heap) < limit:
                        heapq.heappush(top_heap, (score, item_id, post))
                    elif score > top_heap[0][0]:
                        heapq.heapreplace(top_heap, (score, item_id, post))
            
            with count_lock:
                processed_count += len(lines_batch)
                if processed_count % 10000 == 0:
                    print(f"  Verarbeitet: {processed_count:,} Posts...", end='\r')
        
        # Lese Datei in Batches und verarbeite parallel
        batch_size = 1000
        with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
            futures = []
            current_batch = []
            
            with open(self.posts_file, 'r', encoding='utf-8') as f:
                for line in f:
                    current_batch.append(line.strip())
                    
                    if len(current_batch) >= batch_size:
                        future = executor.submit(process_lines_batch, current_batch)
                        futures.append(future)
                        current_batch = []
                
                # Letzter Batch
                if current_batch:
                    future = executor.submit(process_lines_batch, current_batch)
                    futures.append(future)
            
            # Warte auf alle Threads
            for future in as_completed(futures):
                future.result()
        
        # Extrahiere Top Posts aus Heap (sortiert)
        top_posts = []
        while top_heap:
            score, item_id, post = heapq.heappop(top_heap)
            top_posts.append(post)
        
        # Sortiere absteigend
        top_posts.reverse()
        
        if not top_posts:
            print("\n  ❌ Keine Posts gefunden!")
            return []
        
        elapsed = time.time() - start_time
        print(f"\n  ✓ {len(top_posts)} Top Posts gefunden in {elapsed:.1f}s")
        print(f"  Score-Range: {top_posts[0]['score']:,} - {top_posts[-1]['score']:,}")
        print(f"  Verarbeitungsrate: {processed_count/elapsed:,.0f} Posts/s")
        
        # Speichere Posts parallel
        posts_dir = self.output_dir / "top_50_posts"
        posts_dir.mkdir(exist_ok=True)
        
        print(f"  💾 Speichere Posts parallel...")
        with ThreadPoolExecutor(max_workers=min(10, cpu_count())) as executor:
            futures = []
            for i, post in enumerate(top_posts, 1):
                future = executor.submit(self.save_post_for_repost, post, i, posts_dir)
                futures.append(future)
            
            # Warte auf alle Speicher-Operationen
            for future in as_completed(futures):
                future.result()
        
        # Erstelle Übersicht
        self.create_posts_overview(top_posts, posts_dir)
        
        return top_posts
    
    def extract_top_comments(self, limit=100):
        """Extrahiert die Top Kommentare mit Multithreading"""
        print(f"\n💬 Extrahiere Top {limit} Kommentare aus November 2024...")
        print(f"  ⚡ Nutze {cpu_count()} CPU Cores für parallele Verarbeitung")
        
        if not self.comments_file.exists():
            print(f"  ⚠️ Warte auf gefilterte Kommentare: {self.comments_file}")
            return []
        
        start_time = time.time()
        
        # Thread-safe heap für Top Comments
        top_heap = []
        heap_lock = threading.Lock()
        processed_count = 0
        filtered_count = 0
        count_lock = threading.Lock()
        
        def process_comment_batch(lines_batch):
            """Verarbeitet einen Batch von Kommentaren"""
            nonlocal processed_count, filtered_count
            local_comments = []
            
            for line in lines_batch:
                try:
                    comment = json.loads(line)
                    score = comment.get('score', 0)
                    body = comment.get('body', '')
                    
                    # Filter: Nur Kommentare mit gutem Score und Text
                    if score > 50 and body and body != '[deleted]':
                        local_comments.append((score, comment))
                except:
                    continue
            
            # Update heap thread-safe (mit ID für eindeutige Sortierung)
            with heap_lock:
                for score, comment in local_comments:
                    item_id = comment.get('id', str(score))
                    if len(top_heap) < limit:
                        heapq.heappush(top_heap, (score, item_id, comment))
                    elif score > top_heap[0][0]:
                        heapq.heapreplace(top_heap, (score, item_id, comment))
            
            with count_lock:
                processed_count += len(lines_batch)
                filtered_count += len(local_comments)
                if processed_count % 50000 == 0:
                    print(f"  Verarbeitet: {processed_count:,} | Gefiltert: {filtered_count:,}", end='\r')
        
        # Lese und verarbeite in Batches
        batch_size = 5000
        with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
            futures = []
            current_batch = []
            
            with open(self.comments_file, 'r', encoding='utf-8') as f:
                for line in f:
                    current_batch.append(line.strip())
                    
                    if len(current_batch) >= batch_size:
                        future = executor.submit(process_comment_batch, current_batch)
                        futures.append(future)
                        current_batch = []
                
                # Letzter Batch
                if current_batch:
                    future = executor.submit(process_comment_batch, current_batch)
                    futures.append(future)
            
            # Warte auf alle Threads
            for future in as_completed(futures):
                future.result()
        
        # Extrahiere Top Comments aus Heap
        top_comments = []
        while top_heap:
            score, item_id, comment = heapq.heappop(top_heap)
            top_comments.append(comment)
        
        # Sortiere absteigend
        top_comments.reverse()
        
        if not top_comments:
            print("\n  ❌ Keine Kommentare gefunden!")
            return []
        
        elapsed = time.time() - start_time
        print(f"\n  Gefiltert: {filtered_count:,} Kommentare mit Score > 50")
        print(f"  ✓ Top {limit} Kommentare ausgewählt in {elapsed:.1f}s")
        print(f"  Score-Range: {top_comments[0]['score']:,} - {top_comments[-1]['score']:,}")
        print(f"  Verarbeitungsrate: {processed_count/elapsed:,.0f} Kommentare/s")
        
        # Speichere Kommentare parallel
        comments_dir = self.output_dir / "top_100_comments"
        comments_dir.mkdir(exist_ok=True)
        
        print(f"  💾 Speichere Kommentare parallel...")
        with ThreadPoolExecutor(max_workers=min(10, cpu_count())) as executor:
            futures = []
            for i, comment in enumerate(top_comments, 1):
                future = executor.submit(self.save_comment_for_repost, comment, i, comments_dir)
                futures.append(future)
            
            # Warte auf alle Speicher-Operationen
            for future in as_completed(futures):
                future.result()
        
        # Erstelle Übersicht
        self.create_comments_overview(top_comments, comments_dir)
        
        return top_comments
    
    def save_post_for_repost(self, post, num, output_dir):
        """Speichert einen Post repost-fertig (gleiche Struktur wie Top 3)"""
        
        # Erstelle Ordner für diesen Post
        subreddit = post.get('subreddit', 'unknown')
        
        # Bestimme Ordnernamen basierend auf Inhalt
        title_words = post.get('title', '').lower().split()[:3]
        folder_suffix = '_'.join(title_words[:2]) if len(title_words) >= 2 else subreddit.lower()
        folder_name = f"post_{num}_{folder_suffix}"
        post_dir = output_dir / folder_name
        post_dir.mkdir(exist_ok=True)
        
        # Extrahiere Daten
        title = post.get('title', '')
        author = post.get('author', '[deleted]')
        selftext = post.get('selftext', '')
        score = post.get('score', 0)
        num_comments = post.get('num_comments', 0)
        created_utc = post.get('created_utc', 0)
        permalink = post.get('permalink', '')
        url = post.get('url', '')
        
        # Formatiere Datum (gleich wie Top 3)
        date = datetime.fromtimestamp(created_utc)
        date_str = date.strftime("%B %d, %Y at %I:%M %p")
        
        # Erstelle post_content.txt (exakt wie Top 3)
        post_content = f"""ORIGINAL POST INFORMATION
========================
Subreddit: r/{subreddit}
Author: u/{author}
Date: {date_str}
Score: {score:,} upvotes
Comments: {num_comments:,}
Original Link: https://reddit.com{permalink}

TITLE
=====
{title}

POST TEXT
=========
{selftext if selftext else "[This was an image/link post with no text]"}

REPOST TEMPLATE
===============
Title: {title}

Text:
{selftext if selftext else "[Image/Link Post]"}

[Originally posted by u/{author} in r/{subreddit}]

MEDIA/LINKS
===========
Post URL: {url}
Reddit Link: https://reddit.com{permalink}
"""
        
        # Speichere post_content.txt
        with open(post_dir / "post_content.txt", 'w', encoding='utf-8') as f:
            f.write(post_content)
        
        # Speichere post_data.json
        with open(post_dir / "post_data.json", 'w', encoding='utf-8') as f:
            json.dump(post, f, indent=2, ensure_ascii=False)
        
        # Erstelle repost_guide.txt (wie Top 3)
        repost_guide = f"""REPOST ANLEITUNG
================

1. TITEL KOPIEREN:
   {title}

2. TEXT KOPIEREN (falls Textpost):
   {selftext[:500] if selftext else "[Kein Text - Bild/Link-Post]"}

3. CREDITS HINZUFÜGEN:
   Füge am Ende hinzu: "Credit: u/{author} from r/{subreddit}"
   
4. BESTE ZEIT ZUM POSTEN:
   - Morgens: 8-10 Uhr
   - Mittags: 12-14 Uhr  
   - Abends: 19-22 Uhr

5. PASSENDE SUBREDDITS:
   - r/{subreddit} (Original)
   - Ähnliche Communities finden

6. REDDIT REGELN BEACHTEN:
   - Keine Spam/Karma-Farming
   - Quellenangabe machen
   - Community-Regeln lesen
"""
        
        with open(post_dir / "repost_guide.txt", 'w', encoding='utf-8') as f:
            f.write(repost_guide)
        
        # Download Bild falls vorhanden (mit mehreren Versuchen)
        if url and url != f"https://www.reddit.com{permalink}":
            if self.is_image_url(url):
                self.download_image(url, post_dir / "image.jpg")
            elif 'i.redd.it' in url or 'preview.redd.it' in url:
                self.download_image(url, post_dir / "image.jpg")
            elif 'imgur.com' in url:
                # Versuche direkte Bild-URL für imgur
                if not url.endswith(('.jpg', '.png', '.gif')):
                    imgur_url = url + '.jpg'
                    self.download_image(imgur_url, post_dir / "image.jpg")
    
    def save_comment_for_repost(self, comment, num, output_dir):
        """Speichert einen Kommentar repost-fertig (strukturiert wie Posts)"""
        
        # Erstelle Ordner
        subreddit = comment.get('subreddit', 'unknown')
        
        # Kurzer Ordnername mit Kontext
        body_preview = re.sub(r'[^\w\s]', '', comment.get('body', '')[:20]).strip()
        folder_suffix = body_preview[:15].replace(' ', '_').lower() if body_preview else subreddit.lower()
        folder_name = f"comment_{num}_{folder_suffix}"
        comment_dir = output_dir / folder_name
        comment_dir.mkdir(exist_ok=True)
        
        # Extrahiere Daten
        body = comment.get('body', '')
        author = comment.get('author', '[deleted]')
        score = comment.get('score', 0)
        created_utc = comment.get('created_utc', 0)
        permalink = comment.get('permalink', '')
        link_id = comment.get('link_id', '')
        parent_id = comment.get('parent_id', '')
        
        # Formatiere Datum
        date = datetime.fromtimestamp(created_utc)
        date_str = date.strftime("%B %d, %Y at %I:%M %p")
        
        # Erstelle comment_content.txt (ähnlich wie post_content.txt)
        comment_content = f"""ORIGINAL COMMENT INFORMATION
============================
Subreddit: r/{subreddit}
Author: u/{author}
Date: {date_str}
Score: {score:,} upvotes
Original Link: https://reddit.com{permalink}

COMMENT TEXT
============
{body}

CONTEXT
=======
Post ID: {link_id}
Parent: {parent_id}
Thread: https://reddit.com/comments/{link_id.replace('t3_', '') if link_id else 'unknown'}

REPOST TEMPLATE
===============
{body}

[Originally commented by u/{author} in r/{subreddit}]

USAGE GUIDE
===========
This comment can be used:
1. As a response to similar questions
2. In relevant discussions
3. As helpful advice in appropriate context

Remember to:
- Adapt to the new context
- Make it sound natural
- Wait for appropriate timing
"""
        
        # Speichere comment_content.txt
        with open(comment_dir / "comment_content.txt", 'w', encoding='utf-8') as f:
            f.write(comment_content)
        
        # Speichere comment_data.json
        with open(comment_dir / "comment_data.json", 'w', encoding='utf-8') as f:
            json.dump(comment, f, indent=2, ensure_ascii=False)
        
        # Erstelle repost_guide.txt
        repost_guide = f"""KOMMENTAR REPOST ANLEITUNG
==========================

1. KOMMENTAR TEXT:
{body[:500]}{"..." if len(body) > 500 else ""}

2. ORIGINAL KONTEXT:
   - Subreddit: r/{subreddit}
   - Score: {score:,} upvotes
   - Autor: u/{author}

3. VERWENDUNGSMÖGLICHKEITEN:
   - Als Antwort auf ähnliche Fragen
   - In Diskussionen zum gleichen Thema
   - Als hilfreicher Beitrag

4. BESTE EINSATZZEITEN:
   - Wenn jemand eine ähnliche Frage stellt
   - Bei passenden Diskussionsthemen
   - Als Ergänzung zu eigenen Posts

5. WICHTIGE TIPPS:
   - Passe den Text an den neuen Kontext an
   - Mache kleine Änderungen für Natürlichkeit
   - Vermeide 1:1 Kopien
   - Warte auf den richtigen Moment

6. WARNUNG:
   - Nicht spammen
   - Kontext muss passen
   - Community-Regeln beachten
"""
        
        with open(comment_dir / "repost_guide.txt", 'w', encoding='utf-8') as f:
            f.write(repost_guide)
    
    def create_posts_overview(self, posts, output_dir):
        """Erstellt eine Übersicht aller Posts"""
        
        overview = "TOP 50 POSTS - NOVEMBER 2024\n"
        overview += "=" * 60 + "\n\n"
        
        # Gruppiere nach Subreddit
        by_subreddit = defaultdict(list)
        for post in posts:
            by_subreddit[post.get('subreddit', 'unknown')].append(post)
        
        overview += f"SUBREDDIT VERTEILUNG:\n"
        for sub, sub_posts in sorted(by_subreddit.items(), key=lambda x: len(x[1]), reverse=True):
            overview += f"  r/{sub}: {len(sub_posts)} Posts\n"
        
        overview += "\n" + "=" * 60 + "\n"
        overview += "ALLE POSTS NACH SCORE:\n\n"
        
        for i, post in enumerate(posts, 1):
            title = post.get('title', '')[:80]
            score = post.get('score', 0)
            subreddit = post.get('subreddit', '')
            overview += f"{i:3d}. [{score:6,}] r/{subreddit:20} - {title}\n"
        
        # Speichere Übersicht
        with open(output_dir / "OVERVIEW.txt", 'w', encoding='utf-8') as f:
            f.write(overview)
    
    def create_comments_overview(self, comments, output_dir):
        """Erstellt eine Übersicht aller Kommentare"""
        
        overview = "TOP 100 KOMMENTARE - NOVEMBER 2024\n"
        overview += "=" * 60 + "\n\n"
        
        # Gruppiere nach Subreddit
        by_subreddit = defaultdict(list)
        for comment in comments:
            by_subreddit[comment.get('subreddit', 'unknown')].append(comment)
        
        overview += f"SUBREDDIT VERTEILUNG:\n"
        for sub, sub_comments in sorted(by_subreddit.items(), key=lambda x: len(x[1]), reverse=True):
            overview += f"  r/{sub}: {len(sub_comments)} Kommentare\n"
        
        overview += "\n" + "=" * 60 + "\n"
        overview += "ALLE KOMMENTARE NACH SCORE:\n\n"
        
        for i, comment in enumerate(comments, 1):
            body_preview = comment.get('body', '')[:60].replace('\n', ' ')
            score = comment.get('score', 0)
            subreddit = comment.get('subreddit', '')
            overview += f"{i:3d}. [{score:5,}] r/{subreddit:20} - {body_preview}...\n"
        
        # Speichere Übersicht
        with open(output_dir / "OVERVIEW.txt", 'w', encoding='utf-8') as f:
            f.write(overview)
    
    def is_image_url(self, url):
        """Prüft ob URL ein Bild ist"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return any(url.lower().endswith(ext) for ext in image_extensions) or 'i.redd.it' in url
    
    def download_image(self, url, filepath):
        """Lädt ein Bild herunter"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True
        except:
            pass
        return False
    
    def create_master_guide(self):
        """Erstellt eine Master-Anleitung für Reposting"""
        
        guide = """
REDDIT KARMA FARM - NOVEMBER 2024 REPOST GUIDE
===============================================

📋 INHALT:
- Top 50 Posts (november_top_content/top_50_posts/)
- Top 100 Kommentare (november_top_content/top_100_comments/)

⏰ BESTE POSTING-ZEITEN:
- Montag-Freitag: 8-10 Uhr, 12-14 Uhr, 19-22 Uhr
- Wochenende: 10-12 Uhr, 14-17 Uhr, 20-23 Uhr

📊 POSTING-STRATEGIE:
1. Maximal 2-3 Posts pro Tag
2. Verschiedene Subreddits nutzen
3. Mindestens 6 Stunden zwischen Posts
4. Kommentare natürlich einstreuen

⚠️ WICHTIGE REGELN:
- IMMER Subreddit-Regeln prüfen
- KEINE identischen Reposts
- Inhalte leicht anpassen/personalisieren
- Credits geben wenn gefordert

🎯 ERFOLGS-TIPPS:
- Engagiere in Kommentaren
- Antworte auf Replies
- Sei Teil der Community
- Qualität vor Quantität

📁 STRUKTUR:
Jeder Post/Kommentar hat:
- content.txt (Fertiger Text)
- data.json (Original-Daten)
- repost_guide.txt (Anleitung)
- image.jpg (Falls Bild-Post)

VIEL ERFOLG! 🚀
"""
        
        with open(self.output_dir / "MASTER_GUIDE.txt", 'w', encoding='utf-8') as f:
            f.write(guide)

def main():
    print("=" * 60)
    print("🚀 REDDIT TOP CONTENT EXTRACTOR - NOVEMBER 2024")
    print("   Top 50 Posts & Top 100 Kommentare")
    print("=" * 60)
    
    extractor = NovemberContentExtractor()
    
    # Check ob Filter fertig ist
    if not extractor.posts_file.exists() or not extractor.comments_file.exists():
        print("\n⏳ Warte auf Filterung der November-Daten...")
        print(f"  Comments: {extractor.comments_file}")
        print(f"  Posts: {extractor.posts_file}")
        print("\n💡 Starte dieses Skript erneut wenn die Filterung abgeschlossen ist.")
        return
    
    # Extrahiere Content
    posts = extractor.extract_top_posts(limit=50)
    comments = extractor.extract_top_comments(limit=100)
    
    if posts or comments:
        # Erstelle Master Guide
        extractor.create_master_guide()
        
        # Zusammenfassung
        print("\n" + "=" * 60)
        print("✅ NOVEMBER EXTRAKTION ABGESCHLOSSEN!")
        print(f"\n📁 Output-Verzeichnis: november_top_content/")
        print(f"   ├── top_50_posts/       ({len(posts)} Posts)")
        print(f"   ├── top_100_comments/   ({len(comments)} Kommentare)")
        print(f"   └── MASTER_GUIDE.txt")
        print("\n💡 Jeder Ordner enthält:")
        print("   - Fertigen Text zum Reposten")
        print("   - Original-Daten als JSON")
        print("   - Bilder (falls vorhanden)")
        print("\n🎯 Nächste Schritte:")
        print("   1. Öffne november_top_content/MASTER_GUIDE.txt")
        print("   2. Wähle Content zum Posten")
        print("   3. Folge den Anleitungen in jedem Ordner")

if __name__ == "__main__":
    main()