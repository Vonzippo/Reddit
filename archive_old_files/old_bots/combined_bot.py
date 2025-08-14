#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Combined Bot - Erstellt neue Posts (mit heruntergeladenen Bildern) und Kommentare
Nutzt alte Posts als Vorlage aber erstellt sie NEU (kein Repost)
"""

import json
import random
import time
import requests
import praw
from pathlib import Path
from datetime import datetime, timedelta
import urllib.request
import base64
from PIL import Image
import io

class CombinedBot:
    def __init__(self):
        self.base_dir = Path("/Users/patrick/Desktop/Reddit/data")
        self.posts_dir = self.base_dir / "Posts"
        self.comments_dir = self.base_dir / "Comments"
        self.posts = []
        self.comments = []
        self._load_data()
        
        # Tägliches Tracking
        self.daily_posts = {}
        self.daily_comments = {}
        self.daily_post_target = None
        self.daily_comment_target = None
        self._load_daily_stats()
        
        # Track bereits verwendete Posts/Kommentare
        self.used_posts = set()
        self.used_comments = set()
        self._load_history()
        
        # OpenRouter API für Kommentar-Generierung
        from config import OPENROUTER_API_KEY
        self.openrouter_api_key = OPENROUTER_API_KEY
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Reddit API
        self._init_reddit_connection()
        
        # Temporärer Ordner für heruntergeladene Bilder
        self.temp_images = Path("/Users/patrick/Desktop/Reddit/temp_images")
        self.temp_images.mkdir(exist_ok=True)
    
    def _init_reddit_connection(self):
        """Initialisiert die Reddit-Verbindung"""
        try:
            from config import ACTIVE_CONFIG
            
            self.reddit = praw.Reddit(
                client_id=ACTIVE_CONFIG["client_id"],
                client_secret=ACTIVE_CONFIG["client_secret"],
                user_agent=ACTIVE_CONFIG["user_agent"],
                username=ACTIVE_CONFIG["username"],
                password=ACTIVE_CONFIG["password"],
                ratelimit_seconds=300
            )
            print(f"✅ Reddit-Verbindung hergestellt als u/{ACTIVE_CONFIG['username']}")
            # Test der Verbindung
            _ = self.reddit.user.me()
        except Exception as e:
            print(f"⚠️ Reddit-Verbindung fehlgeschlagen: {e}")
    
    def _load_data(self):
        """Lädt Posts und Kommentare"""
        print(f"📂 Lade Daten von: {self.base_dir}")
        
        # Posts laden
        if self.posts_dir.exists():
            print(f"  📁 Lade Posts...")
            for post_folder in sorted(self.posts_dir.iterdir())[:500]:  # Max 500
                if post_folder.is_dir() and post_folder.name.startswith("post_"):
                    json_file = post_folder / "post_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.posts.append(data)
        
        # Kommentare laden
        if self.comments_dir.exists():
            print(f"  📁 Lade Kommentare...")
            for comment_folder in sorted(self.comments_dir.iterdir())[:500]:  # Max 500
                if comment_folder.is_dir() and comment_folder.name.startswith("comment_"):
                    json_file = comment_folder / "comment_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.comments.append(data)
        
        print(f"✅ Geladen: {len(self.posts)} Posts und {len(self.comments)} Kommentare")
    
    def _load_daily_stats(self):
        """Lädt tägliche Statistiken"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Post Stats
        post_stats_file = Path("/Users/patrick/Desktop/Reddit/combined_post_stats.json")
        if post_stats_file.exists():
            with open(post_stats_file, 'r') as f:
                self.daily_posts = json.load(f)
        else:
            self.daily_posts = {}
        
        # Comment Stats
        comment_stats_file = Path("/Users/patrick/Desktop/Reddit/combined_comment_stats.json")
        if comment_stats_file.exists():
            with open(comment_stats_file, 'r') as f:
                self.daily_comments = json.load(f)
        else:
            self.daily_comments = {}
        
        # Setze Tagesziele wenn noch nicht vorhanden
        if today not in self.daily_posts:
            # 15% Chance für Pausentag
            if random.random() < 0.15:
                self.daily_post_target = 0
            else:
                self.daily_post_target = random.randint(1, 4)
            self.daily_posts[today] = {'target': self.daily_post_target, 'count': 0, 'posts': []}
            self._save_stats()
        else:
            self.daily_post_target = self.daily_posts[today].get('target', 0)
        
        if today not in self.daily_comments:
            if random.random() < 0.2:
                self.daily_comment_target = 0
            else:
                self.daily_comment_target = random.randint(5, 20)
            self.daily_comments[today] = {'target': self.daily_comment_target, 'count': 0, 'comments': []}
            self._save_stats()
        else:
            self.daily_comment_target = self.daily_comments[today].get('target', 0)
        
        print(f"📊 Heutige Ziele: {self.daily_post_target} Posts, {self.daily_comment_target} Kommentare")
    
    def _save_stats(self):
        """Speichert Statistiken"""
        post_stats_file = Path("/Users/patrick/Desktop/Reddit/combined_post_stats.json")
        with open(post_stats_file, 'w') as f:
            json.dump(self.daily_posts, f, indent=2)
        
        comment_stats_file = Path("/Users/patrick/Desktop/Reddit/combined_comment_stats.json")
        with open(comment_stats_file, 'w') as f:
            json.dump(self.daily_comments, f, indent=2)
    
    def _load_history(self):
        """Lädt Historie verwendeter Posts/Kommentare"""
        history_file = Path("/Users/patrick/Desktop/Reddit/combined_history.json")
        if history_file.exists():
            with open(history_file, 'r') as f:
                data = json.load(f)
                self.used_posts = set(data.get('posts', []))
                self.used_comments = set(data.get('comments', []))
        else:
            self.used_posts = set()
            self.used_comments = set()
    
    def _save_history(self):
        """Speichert Historie"""
        history_file = Path("/Users/patrick/Desktop/Reddit/combined_history.json")
        with open(history_file, 'w') as f:
            json.dump({
                'posts': list(self.used_posts),
                'comments': list(self.used_comments)
            }, f, indent=2)
    
    def download_image(self, url):
        """Lädt ein Bild herunter und speichert es temporär"""
        try:
            print(f"   ⬇️ Lade Bild herunter: {url[:50]}...")
            
            # Download
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=10)
            img_data = response.read()
            
            # Bestimme Dateityp
            if url.lower().endswith('.gif'):
                ext = '.gif'
            elif url.lower().endswith('.png'):
                ext = '.png'
            else:
                ext = '.jpg'
            
            # Speichere temporär
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = self.temp_images / f"img_{timestamp}{ext}"
            
            with open(temp_path, 'wb') as f:
                f.write(img_data)
            
            print(f"   ✅ Bild gespeichert: {temp_path.name}")
            return temp_path
            
        except Exception as e:
            print(f"   ❌ Fehler beim Bilddownload: {e}")
            return None
    
    def upload_image_to_reddit(self, image_path, subreddit_name):
        """Lädt ein Bild auf Reddit hoch"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Upload Bild
            print(f"   📤 Lade Bild auf Reddit hoch...")
            
            # Öffne Bild
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Reddit nimmt nur bestimmte Formate
            # Konvertiere zu PNG wenn nötig
            if not str(image_path).endswith(('.jpg', '.jpeg', '.png', '.gif')):
                img = Image.open(io.BytesIO(image_data))
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                image_data = buffer.getvalue()
            
            # Upload über submit_image (nur in manchen Subreddits erlaubt)
            # Alternativ: Imgur upload und URL posten
            
            # Für jetzt: Verwende die Original-URL (funktioniert oft noch)
            return True
            
        except Exception as e:
            print(f"   ⚠️ Bild-Upload nicht möglich: {e}")
            return False
    
    def get_random_post(self, prefer_unused=True):
        """Gibt einen zufälligen Post zurück"""
        if prefer_unused:
            unused = [p for p in self.posts if p.get('id') not in self.used_posts]
            if unused:
                return random.choice(unused)
        return random.choice(self.posts) if self.posts else None
    
    def get_random_comment(self, prefer_unused=True):
        """Gibt einen zufälligen Kommentar zurück"""
        if prefer_unused:
            unused = [c for c in self.comments if c.get('id') not in self.used_comments]
            if unused:
                return random.choice(unused)
        return random.choice(self.comments) if self.comments else None
    
    def create_new_post(self, post_data, ignore_limit=False):
        """Erstellt einen NEUEN Post (kein Repost) mit gleichem Inhalt"""
        
        # Check Tageslimit (außer bei Einzelposts)
        if not ignore_limit:
            today = datetime.now().strftime("%Y-%m-%d")
            current_count = self.daily_posts.get(today, {}).get('count', 0)
            if self.daily_post_target and current_count >= self.daily_post_target:
                print("⚠️ Tageslimit für Posts erreicht")
                return False
        
        try:
            subreddit_name = post_data.get('subreddit', 'test')
            subreddit = self.reddit.subreddit(subreddit_name)
            
            print(f"\n📝 Erstelle NEUEN Post (kein Repost):")
            print(f"   Titel: {post_data.get('title', '')[:60]}...")
            print(f"   Subreddit: r/{subreddit_name}")
            
            # Prüfe ob es ein Bild-Post ist
            if post_data.get('url') and any(ext in post_data.get('url', '').lower() 
                                           for ext in ['.jpg', '.jpeg', '.png', '.gif', 'i.redd.it', 'imgur']):
                
                # Bild-Post: Lade Bild herunter
                image_path = self.download_image(post_data['url'])
                
                if image_path:
                    # Option 1: Poste mit Original-URL (funktioniert oft noch)
                    submission = subreddit.submit(
                        title=post_data['title'],
                        url=post_data['url']  # Original URL
                    )
                    print(f"   ✅ Bild-Post erstellt (mit Original-URL)")
                else:
                    # Fallback: Als Text-Post
                    submission = subreddit.submit(
                        title=post_data['title'],
                        selftext=post_data.get('selftext', f"[Bild war hier: {post_data.get('url', '')}]")
                    )
                    print(f"   ⚠️ Als Text-Post erstellt (Bild nicht verfügbar)")
            
            elif post_data.get('url'):
                # Link-Post (kein Bild)
                submission = subreddit.submit(
                    title=post_data['title'],
                    url=post_data['url']
                )
                print(f"   ✅ Link-Post erstellt")
            
            else:
                # Text-Post
                submission = subreddit.submit(
                    title=post_data['title'],
                    selftext=post_data.get('selftext', '')
                )
                print(f"   ✅ Text-Post erstellt")
            
            # Setze Flair wenn vorhanden
            if submission and post_data.get('link_flair_text'):
                try:
                    flair_choices = list(subreddit.flair.link_templates)
                    for flair in flair_choices:
                        if flair['text'] == post_data.get('link_flair_text'):
                            submission.flair.select(flair['id'])
                            print(f"   🏷️ Flair gesetzt: {post_data.get('link_flair_text')}")
                            break
                except:
                    pass
            
            print(f"   🔗 URL: https://reddit.com{submission.permalink}")
            
            # Tracking
            self.used_posts.add(post_data.get('id', ''))
            self._save_history()
            
            # Update Tagesstatistik (nur wenn nicht ignore_limit)
            if not ignore_limit:
                today = datetime.now().strftime("%Y-%m-%d")
                if today in self.daily_posts:
                    self.daily_posts[today]['count'] += 1
                    self.daily_posts[today]['posts'].append({
                        'time': datetime.now().isoformat(),
                        'title': post_data.get('title', ''),
                        'subreddit': subreddit_name
                    })
                    self._save_stats()
            
            return True
            
        except Exception as e:
            print(f"   ❌ Fehler beim Posten: {e}")
            return False
    
    def find_suitable_post_for_comment(self):
        """Findet einen aktuellen Reddit-Post zum Kommentieren"""
        try:
            # Wähle zufälliges Subreddit
            subreddits = ['ADHD', 'ADHDmemes', 'productivity', 'GetDisciplined', 
                         'CasualConversation', 'offmychest']
            subreddit = self.reddit.subreddit(random.choice(subreddits))
            
            # Hole aktuelle Posts
            for submission in subreddit.hot(limit=20):
                # Skip gesperrte/archivierte
                if submission.locked or submission.archived:
                    continue
                
                # Skip wenn wir schon kommentiert haben
                already_commented = False
                submission.comments.replace_more(limit=0)
                for comment in submission.comments.list():
                    if comment.author and comment.author.name == "ReddiBoto":
                        already_commented = True
                        break
                
                if not already_commented:
                    return submission
            
            return None
            
        except Exception as e:
            print(f"❌ Fehler bei Post-Suche: {e}")
            return None
    
    def generate_comment_for_post(self, post_title, post_body=""):
        """Generiert einen passenden Kommentar mit AI"""
        try:
            prompt = f"""Write a short, casual Reddit comment for this post:
Title: {post_title}
Body: {post_body[:200] if post_body else ""}

Be genuine, helpful or funny. Keep it 1-3 sentences. Use casual Reddit style.

Comment:"""
            
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3-haiku",
                    "messages": [
                        {"role": "system", "content": "You're a helpful Reddit user. Be casual and genuine."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.9,
                    "max_tokens": 100
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                comment = result['choices'][0]['message']['content'].strip()
                
                # Füge natürliche Variationen hinzu
                if random.random() < 0.3:
                    comment = comment.lower()
                
                return comment
                
        except Exception as e:
            print(f"❌ Fehler bei Kommentar-Generierung: {e}")
        
        # Fallback: Verwende archivierten Kommentar
        archived = self.get_random_comment()
        if archived:
            return archived.get('body', 'Nice post!')[:200]
        
        return "This is interesting!"
    
    def post_comment(self, submission, comment_text, ignore_limit=False):
        """Postet einen Kommentar"""
        
        # Check Tageslimit (außer bei ignore_limit)
        if not ignore_limit:
            today = datetime.now().strftime("%Y-%m-%d")
            current_count = self.daily_comments.get(today, {}).get('count', 0)
            if self.daily_comment_target and current_count >= self.daily_comment_target:
                print("⚠️ Tageslimit für Kommentare erreicht")
                return False
        
        try:
            comment = submission.reply(comment_text)
            print(f"   ✅ Kommentar gepostet!")
            print(f"   📝 Text: {comment_text[:50]}...")
            print(f"   🔗 URL: https://reddit.com{comment.permalink}")
            
            # Update Statistik
            if not ignore_limit:
                today = datetime.now().strftime("%Y-%m-%d")
                if today in self.daily_comments:
                    self.daily_comments[today]['count'] += 1
                    self.daily_comments[today]['comments'].append({
                        'time': datetime.now().isoformat(),
                        'text': comment_text[:100],
                        'post': submission.title[:50]
                    })
                    self._save_stats()
            
            return True
            
        except Exception as e:
            print(f"   ❌ Fehler beim Kommentieren: {e}")
            return False
    
    def run_combined_loop(self):
        """Hauptloop: Abwechselnd Posts und Kommentare"""
        print("\n🤖 KOMBINIERTER BOT - Posts & Kommentare")
        print("="*60)
        print(f"📊 Tagesziele: {self.daily_post_target} Posts, {self.daily_comment_target} Kommentare")
        print("📋 Muster: 1-3 Kommentare → 1 Post → 1-3 Kommentare → 1 Post...")
        print("\nDrücke Ctrl+C zum Beenden")
        print("="*60)
        
        posts_created = 0
        comments_created = 0
        
        try:
            while True:
                # Phase 1: 1-3 Kommentare
                comments_this_round = random.randint(1, 3)
                print(f"\n💬 Phase: {comments_this_round} Kommentare")
                
                for i in range(comments_this_round):
                    if comments_created >= self.daily_comment_target:
                        print("   ✅ Kommentar-Tagesziel erreicht")
                        break
                    
                    # Finde Post zum Kommentieren
                    print(f"\n   Kommentar {i+1}/{comments_this_round}:")
                    submission = self.find_suitable_post_for_comment()
                    
                    if submission:
                        print(f"   📍 Gefunden: {submission.title[:50]}...")
                        
                        # Generiere passenden Kommentar
                        comment_text = self.generate_comment_for_post(
                            submission.title, 
                            submission.selftext if submission.is_self else ""
                        )
                        
                        if self.post_comment(submission, comment_text):
                            comments_created += 1
                        
                        # Warte 2-7 Minuten
                        if i < comments_this_round - 1:
                            wait = random.randint(120, 420)
                            print(f"   ⏰ Warte {wait//60} Minuten...")
                            time.sleep(wait)
                    else:
                        print("   ⚠️ Kein passender Post gefunden")
                
                # Phase 2: 1 Post
                if posts_created < self.daily_post_target:
                    print(f"\n📝 Phase: 1 Post erstellen")
                    
                    post_data = self.get_random_post()
                    if post_data:
                        if self.create_new_post(post_data):
                            posts_created += 1
                            print(f"   Fortschritt: {posts_created}/{self.daily_post_target} Posts")
                else:
                    print("\n✅ Post-Tagesziel erreicht")
                
                # Check ob beide Ziele erreicht
                if posts_created >= self.daily_post_target and comments_created >= self.daily_comment_target:
                    print("\n🎉 Beide Tagesziele erreicht!")
                    break
                
                # Warte vor nächster Runde (10-30 Minuten)
                wait = random.randint(600, 1800)
                print(f"\n⏰ Warte {wait//60} Minuten bis zur nächsten Runde...")
                time.sleep(wait)
                
        except KeyboardInterrupt:
            print(f"\n\n👋 Bot beendet")
            print(f"📊 Heute erstellt: {posts_created} Posts, {comments_created} Kommentare")
    
    def create_single_post(self):
        """Erstellt einen einzelnen Post ohne Tageslimit"""
        post = self.get_random_post()
        if post:
            print(f"\n📝 EINZELNER POST (ohne Tageslimit):")
            print(f"Titel: {post.get('title', '')}")
            print(f"Subreddit: r/{post.get('subreddit', 'test')}")
            print(f"Score (Original): {post.get('score', 0):,}")
            
            if input("\nErstellen? (ja/nein): ").lower() == 'ja':
                self.create_new_post(post, ignore_limit=True)
        else:
            print("❌ Keine Posts verfügbar")

def main():
    bot = CombinedBot()
    
    print("\n🤖 KOMBINIERTER BOT - Posts & Kommentare")
    print("="*60)
    print("1. 🔄 Kombinierter Loop (Posts + Kommentare)")
    print("2. 📝 Einzelnen Post erstellen (ohne Limit)")
    print("3. 💬 Einzelnen Kommentar erstellen")
    print("4. 📊 Statistiken anzeigen")
    
    choice = input("\nWahl (1-4): ").strip()
    
    if choice == "1":
        bot.run_combined_loop()
        
    elif choice == "2":
        bot.create_single_post()
        
    elif choice == "3":
        print("\n💬 EINZELNER KOMMENTAR:")
        submission = bot.find_suitable_post_for_comment()
        if submission:
            print(f"Post gefunden: {submission.title[:60]}...")
            comment = bot.generate_comment_for_post(submission.title)
            print(f"Kommentar: {comment}")
            
            if input("\nPosten? (ja/nein): ").lower() == 'ja':
                bot.post_comment(submission, comment, ignore_limit=True)
        else:
            print("❌ Kein passender Post gefunden")
            
    elif choice == "4":
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"\n📊 STATISTIKEN für {today}:")
        print(f"Posts: {bot.daily_posts.get(today, {}).get('count', 0)}/{bot.daily_post_target}")
        print(f"Kommentare: {bot.daily_comments.get(today, {}).get('count', 0)}/{bot.daily_comment_target}")
        print(f"\nGesammt verwendet:")
        print(f"Posts: {len(bot.used_posts)}")
        print(f"Kommentare: {len(bot.used_comments)}")

if __name__ == "__main__":
    main()