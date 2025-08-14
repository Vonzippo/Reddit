#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Vollautomatischer Reddit Bot - Posts und Kommentare
Erstellt Posts und Kommentare automatisch mit Zeitverzögerungen
Kombiniert Funktionen von main_other und kommentarbot
"""

import json
import random
import time
from pathlib import Path
import urllib.request
import os
import mimetypes
import praw
import shutil
import re
from datetime import datetime, timedelta

class AutoPostCommentBot:
    def __init__(self):
        # Bot Settings MÜSSEN ZUERST definiert werden
        self.settings = {
            'post_delay_min': 1800,    # 30 Min
            'post_delay_max': 7200,    # 2 Stunden
            'comment_delay_min': 300,  # 5 Min
            'comment_delay_max': 1800, # 30 Min
            'active_hours': (10, 22),  # 10:00 - 22:00
            'max_posts_per_day': 2,     # MAX 2 Posts pro Tag
            'max_comments_per_day': 5,  # MAX 5 Kommentare pro Tag
            'pause_day_chance': 0.55   # 55% Chance für Pausentag (mehr Pause als Aktivität!)
        }
        
        # Nutze data_all
        self.base_dir = Path("/Users/patrick/Desktop/Reddit/data_all")
        self.posts_dir = self.base_dir / "Posts"
        self.posts = []
        self._load_data()
        
        # Tägliches Tracking
        self.daily_stats = {}
        self._load_daily_stats()
        self.daily_post_target = None
        self.daily_comment_target = None
        
        # Track bereits gepostete Posts/Kommentare
        self.posted_posts = set()
        self.posted_comments = set()
        self._load_posted_history()
        
        # Reddit API Konfiguration
        self._init_reddit_connection()
    
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
            user = self.reddit.user.me()
            print(f"✅ Reddit-Verbindung hergestellt als u/{user.name}")
            
        except Exception as e:
            print(f"⚠️ Reddit-Verbindung fehlgeschlagen: {e}")
    
    def _load_data(self):
        """Lädt alle Posts aus data_all/Posts"""
        print(f"📂 Lade Daten von: {self.base_dir}")
        
        if self.posts_dir.exists():
            for post_folder in sorted(self.posts_dir.iterdir()):
                if post_folder.is_dir():
                    json_file = post_folder / "post_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.posts.append(data)
        
        print(f"✅ Geladen: {len(self.posts)} Posts")
    
    def _load_daily_stats(self):
        """Lädt tägliche Statistiken"""
        stats_file = Path("/Users/patrick/Desktop/Reddit/auto_bot_stats.json")
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.daily_stats = json.load(f)
            except:
                self.daily_stats = {}
        else:
            self.daily_stats = {}
        
        # Prüfe/setze heutige Ziele
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.daily_stats:
            self._set_daily_targets(today)
        else:
            self.daily_post_target = self.daily_stats[today].get('post_target')
            self.daily_comment_target = self.daily_stats[today].get('comment_target')
    
    def _set_daily_targets(self, today):
        """Setzt tägliche Ziele"""
        # 55% Chance für Pausentag - Bot ist mehr inaktiv als aktiv!
        if random.random() < self.settings['pause_day_chance']:
            self.daily_post_target = 0
            self.daily_comment_target = 0
            is_pause_day = True
            print(f"😴 Heute ist ein Pausentag")
        else:
            self.daily_post_target = random.randint(1, 2)  # 1-2 Posts
            self.daily_comment_target = random.randint(2, 5)  # 2-5 Kommentare
            is_pause_day = False
            print(f"🎯 Heutige Ziele: {self.daily_post_target} Posts, {self.daily_comment_target} Kommentare")
        
        self.daily_stats[today] = {
            'post_target': self.daily_post_target,
            'comment_target': self.daily_comment_target,
            'posts_created': 0,
            'comments_created': 0,
            'posts': [],
            'comments': [],
            'is_pause_day': is_pause_day
        }
        self._save_daily_stats()
    
    def _save_daily_stats(self):
        """Speichert tägliche Statistiken"""
        stats_file = Path("/Users/patrick/Desktop/Reddit/auto_bot_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.daily_stats, f, indent=2, ensure_ascii=False)
    
    def _load_posted_history(self):
        """Lädt Historie der bereits geposteten Posts/Kommentare"""
        history_file = Path("/Users/patrick/Desktop/Reddit/auto_bot_history.json")
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.posted_posts = set(data.get('posts', []))
                    self.posted_comments = set(data.get('comments', []))
                    print(f"📝 Historie geladen: {len(self.posted_posts)} Posts, {len(self.posted_comments)} Kommentare")
            except:
                self.posted_posts = set()
                self.posted_comments = set()
        else:
            self.posted_posts = set()
            self.posted_comments = set()
    
    def _save_posted_history(self):
        """Speichert Historie"""
        history_file = Path("/Users/patrick/Desktop/Reddit/auto_bot_history.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump({
                'posts': list(self.posted_posts),
                'comments': list(self.posted_comments)
            }, f, indent=2)
    
    def get_random_post(self):
        """Gibt einen zufälligen Post mit alternativen Subreddits zurück"""
        problematic_subs = ['pics', 'photography', 'itookapicture', 'art', 'drawing']
        
        if self.posts:
            # Versuche einen noch nicht geposteten Post zu finden
            unposted = [p for p in self.posts if p.get('id') not in self.posted_posts]
            if unposted:
                post = random.choice(unposted)
            else:
                post = random.choice(self.posts)
            
            # Nutze alternative Subreddits wenn vorhanden
            if post.get('alternative_subreddits'):
                new_sub = random.choice(post['alternative_subreddits'])
                print(f"   📋 Verwende alternativen Subreddit: r/{new_sub}")
                post['subreddit'] = new_sub
            elif post.get('subreddit', '').lower() in problematic_subs:
                safe_subs = ['interestingasfuck', 'Damnthatsinteresting', 'BeAmazed', 'nextfuckinglevel']
                new_sub = random.choice(safe_subs)
                print(f"   ⚠️ r/{post['subreddit']} problematisch - verwende r/{new_sub}")
                post['subreddit'] = new_sub
            
            return post
        return None
    
    def clean_post_title(self, title):
        """Bereinigt Post-Titel"""
        title = ' '.join(title.split())
        
        banned_phrases = [
            'upvote if', 'upvote this', 'please upvote',
            '[OC]', '[oc]', '(OC)', '(oc)',
            'EDIT:', 'UPDATE:'
        ]
        
        for phrase in banned_phrases:
            title = re.sub(re.escape(phrase), '', title, flags=re.IGNORECASE)
        
        if sum(1 for c in title if c.isupper()) > len(title) * 0.5:
            title = title.title()
        
        title = re.sub(r'[!?.]{2,}$', '.', title)
        
        if len(title) > 300:
            title = title[:297] + "..."
        
        return title.strip()
    
    def download_image(self, url):
        """Lädt ein Bild herunter"""
        if not url:
            return None
            
        try:
            temp_dir = Path("/Users/patrick/Desktop/Reddit/temp_images")
            temp_dir.mkdir(exist_ok=True)
            
            if '.gif' in url.lower():
                ext = '.gif'
            elif '.png' in url.lower():
                ext = '.png'
            else:
                ext = '.jpg'
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=10)
            img_data = response.read()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = temp_dir / f"img_{timestamp}{ext}"
            
            with open(temp_path, 'wb') as f:
                f.write(img_data)
            
            return str(temp_path)
            
        except Exception as e:
            print(f"   ❌ Fehler beim Bilddownload: {e}")
            return None
    
    def get_image_for_post(self, post_data):
        """Sucht nach lokalem Bild oder lädt es herunter"""
        post_id = post_data.get('id', '')
        
        # Suche nach lokalem Bild
        for folder in self.posts_dir.iterdir():
            if folder.is_dir():
                json_file = folder / "post_data.json"
                if json_file.exists():
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('id') == post_id or data.get('title') == post_data.get('title'):
                            for img_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                                img_path = folder / f"image{img_ext}"
                                if img_path.exists():
                                    print(f"   📂 Verwende lokales Bild: {img_path.name}")
                                    return str(img_path)
        
        return self.download_image(post_data.get('url', ''))
    
    def create_post(self, post_data):
        """Erstellt einen Post auf Reddit"""
        try:
            subreddit = self.reddit.subreddit(post_data['subreddit'])
            
            # Hole Flairs
            flair_id = None
            try:
                flair_choices = list(subreddit.flair.link_templates)
                if flair_choices:
                    for flair in flair_choices:
                        if not flair.get('mod_only', False):
                            flair_id = flair['id']
                            break
            except:
                pass
            
            # Verwende variierten Titel wenn vorhanden
            title_to_use = post_data.get('varied_title', post_data['title'])
            clean_title = self.clean_post_title(title_to_use)
            
            # Erstelle Post
            if post_data.get('selftext'):
                # Verwende variierten Text wenn vorhanden
                text_to_use = post_data.get('varied_selftext', post_data.get('selftext', ''))
                submission = subreddit.submit(
                    title=clean_title,
                    selftext=text_to_use,
                    flair_id=flair_id
                )
            elif post_data.get('url'):
                url = post_data.get('url', '')
                is_image = any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', 'i.redd.it', 'imgur'])
                
                if is_image:
                    image_path = self.get_image_for_post(post_data)
                    if image_path:
                        try:
                            submission = subreddit.submit_image(
                                title=clean_title,
                                image_path=image_path,
                                flair_id=flair_id
                            )
                            if 'temp_images' in image_path:
                                os.remove(image_path)
                        except Exception as e:
                            submission = subreddit.submit(
                                title=clean_title,
                                url=url,
                                flair_id=flair_id
                            )
                    else:
                        submission = subreddit.submit(
                            title=clean_title,
                            url=url,
                            flair_id=flair_id
                        )
                else:
                    submission = subreddit.submit(
                        title=clean_title,
                        url=url,
                        flair_id=flair_id
                    )
            
            print(f"✅ Post erstellt: https://reddit.com{submission.permalink}")
            
            # Update Tracking
            self.posted_posts.add(post_data.get('id', ''))
            self._save_posted_history()
            
            # Update Stats
            today = datetime.now().strftime("%Y-%m-%d")
            self.daily_stats[today]['posts_created'] += 1
            self.daily_stats[today]['posts'].append({
                'time': datetime.now().isoformat(),
                'title': clean_title[:100],
                'subreddit': post_data.get('subreddit', 'unknown'),
                'permalink': submission.permalink
            })
            self._save_daily_stats()
            
            return submission
            
        except Exception as e:
            print(f"❌ Fehler beim Posten: {e}")
            return None
    
    def find_target_posts(self):
        """Findet Posts zum Kommentieren"""
        try:
            # Suche in verschiedenen Subreddits
            target_subreddits = [
                'ADHD', 'adhdmeme', 'adhdwomen', 'GetStudying', 'productivity',
                'Journaling', 'selfimprovement', 'mentalhealth', 'autism'
            ]
            
            target_posts = []
            
            for sub_name in target_subreddits[:3]:  # Nur ersten 3 um Zeit zu sparen
                try:
                    subreddit = self.reddit.subreddit(sub_name)
                    # Hole neue Posts (letzte 24h)
                    for post in subreddit.new(limit=20):
                        if post.created_utc > time.time() - 86400:  # Letzten 24h
                            if post.id not in self.posted_comments:
                                target_posts.append(post)
                except:
                    continue
            
            return target_posts
            
        except Exception as e:
            print(f"❌ Fehler beim Suchen von Target Posts: {e}")
            return []
    
    def generate_comment(self, post):
        """Generiert einen relevanten Kommentar"""
        # Einfache Kommentar-Templates basierend auf Keywords
        adhd_comments = [
            "I can totally relate to this! Thanks for sharing.",
            "This is so accurate, especially the part about...",
            "Have you tried any specific strategies for this?",
            "This made my day, thank you!",
            "I'm glad I'm not the only one who experiences this.",
            "Thanks for putting this into words so well.",
            "This is exactly what I needed to read today.",
            "I feel seen! This describes my experience perfectly.",
        ]
        
        general_comments = [
            "Great post, thanks for sharing!",
            "This is really helpful, appreciate it!",
            "Thanks for the insight!",
            "Interesting perspective, thanks!",
            "This resonates with me, thank you.",
            "Well said!",
            "Appreciate you sharing this.",
        ]
        
        title_lower = post.title.lower()
        
        if any(word in title_lower for word in ['adhd', 'autism', 'mental', 'brain', 'focus']):
            return random.choice(adhd_comments)
        else:
            return random.choice(general_comments)
    
    def create_comment(self, post):
        """Erstellt einen Kommentar"""
        try:
            comment_text = self.generate_comment(post)
            comment = post.reply(comment_text)
            
            print(f"✅ Kommentar erstellt auf r/{post.subreddit.display_name}")
            print(f"   Post: {post.title[:60]}...")
            print(f"   Kommentar: {comment_text}")
            
            # Update Tracking
            self.posted_comments.add(post.id)
            self._save_posted_history()
            
            # Update Stats
            today = datetime.now().strftime("%Y-%m-%d")
            self.daily_stats[today]['comments_created'] += 1
            self.daily_stats[today]['comments'].append({
                'time': datetime.now().isoformat(),
                'post_title': post.title[:100],
                'subreddit': post.subreddit.display_name,
                'comment': comment_text
            })
            self._save_daily_stats()
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Kommentieren: {e}")
            return False
    
    def can_post_today(self):
        """Prüft ob heute noch Posts erstellt werden können"""
        today = datetime.now().strftime("%Y-%m-%d")
        current_count = self.daily_stats[today]['posts_created']
        target = self.daily_stats[today]['post_target']
        return current_count < target
    
    def can_comment_today(self):
        """Prüft ob heute noch Kommentare erstellt werden können"""
        today = datetime.now().strftime("%Y-%m-%d")
        current_count = self.daily_stats[today]['comments_created']
        target = self.daily_stats[today]['comment_target']
        return current_count < target
    
    def is_active_time(self):
        """Prüft ob aktive Zeit"""
        current_hour = datetime.now().hour
        start_hour, end_hour = self.settings['active_hours']
        return start_hour <= current_hour < end_hour
    
    def run_auto_loop(self):
        """Hauptschleife - vollautomatisch"""
        print("\n🤖 VOLLAUTOMATISCHER POST & KOMMENTAR BOT")
        print("="*60)
        print(f"⏰ Aktive Zeit: {self.settings['active_hours'][0]}:00 - {self.settings['active_hours'][1]}:00 Uhr")
        
        today = datetime.now().strftime("%Y-%m-%d")
        if self.daily_stats[today].get('is_pause_day'):
            print(f"😴 Heute ist ein Pausentag")
        else:
            print(f"🎯 Heutiges Ziel: {self.daily_post_target} Posts, {self.daily_comment_target} Kommentare")
        
        print("🔄 Bot läuft vollautomatisch...")
        print("Drücke Ctrl+C zum Beenden")
        print("="*60)
        
        last_action_time = None
        
        try:
            while True:
                current_time = datetime.now()
                today = current_time.strftime("%Y-%m-%d")
                
                # Prüfe ob neuer Tag
                if today not in self.daily_stats:
                    self._set_daily_targets(today)
                
                # Prüfe ob Pausentag
                if self.daily_stats[today].get('is_pause_day'):
                    print(f"😴 [{current_time.strftime('%H:%M:%S')}] Pausentag - warte bis morgen...")
                    time.sleep(3600)
                    continue
                
                # Prüfe ob aktive Zeit
                if not self.is_active_time():
                    print(f"😴 [{current_time.strftime('%H:%M:%S')}] Außerhalb der aktiven Zeit...")
                    time.sleep(1800)  # 30 Min
                    continue
                
                # Mindestabstand zwischen Aktionen
                if last_action_time:
                    time_since_last = (current_time - last_action_time).total_seconds()
                    min_wait = 300  # 5 Min zwischen Aktionen
                    if time_since_last < min_wait:
                        wait_time = int(min_wait - time_since_last)
                        print(f"⏳ Warte noch {wait_time//60} Minuten...")
                        time.sleep(wait_time)
                        continue
                
                # Entscheide: Post oder Kommentar (70% Chance für Kommentar)
                action_type = 'comment' if random.random() < 0.7 else 'post'
                
                if action_type == 'post' and self.can_post_today():
                    # Erstelle Post
                    post_data = self.get_random_post()
                    if post_data:
                        print(f"\n📝 [{current_time.strftime('%H:%M:%S')}] Erstelle Post:")
                        print(f"   Titel: {post_data.get('title', '')[:60]}...")
                        print(f"   Subreddit: r/{post_data.get('subreddit', 'unknown')}")
                        
                        if self.create_post(post_data):
                            last_action_time = current_time
                            # Längere Pause nach Post
                            wait_time = random.randint(
                                self.settings['post_delay_min'],
                                self.settings['post_delay_max']
                            )
                            print(f"   💤 Warte {wait_time//60} Minuten...")
                            time.sleep(wait_time)
                
                elif action_type == 'comment' and self.can_comment_today():
                    # Erstelle Kommentar
                    target_posts = self.find_target_posts()
                    if target_posts:
                        target_post = random.choice(target_posts)
                        print(f"\n💬 [{current_time.strftime('%H:%M:%S')}] Erstelle Kommentar:")
                        
                        if self.create_comment(target_post):
                            last_action_time = current_time
                            # Kürzere Pause nach Kommentar
                            wait_time = random.randint(
                                self.settings['comment_delay_min'],
                                self.settings['comment_delay_max']
                            )
                            print(f"   💤 Warte {wait_time//60} Minuten...")
                            time.sleep(wait_time)
                
                # Status Check
                posts_today = self.daily_stats[today]['posts_created']
                comments_today = self.daily_stats[today]['comments_created']
                post_target = self.daily_stats[today]['post_target']
                comment_target = self.daily_stats[today]['comment_target']
                
                print(f"\n📊 Tagesstatus: {posts_today}/{post_target} Posts, {comments_today}/{comment_target} Kommentare")
                
                # Wenn beide Ziele erreicht, warte bis morgen
                if not self.can_post_today() and not self.can_comment_today():
                    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                    wait_seconds = (tomorrow - datetime.now()).total_seconds()
                    hours_to_wait = int(wait_seconds // 3600)
                    print(f"✅ Tagesziele erreicht! Warte bis morgen ({hours_to_wait}h)")
                    time.sleep(3600)
                    continue
                
                # Standard Wartezeit
                wait_time = random.randint(600, 1800)  # 10-30 Min
                print(f"⏰ Warte {wait_time//60} Minuten bis zur nächsten Prüfung...")
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            today = datetime.now().strftime("%Y-%m-%d")
            posts_today = self.daily_stats[today]['posts_created']
            comments_today = self.daily_stats[today]['comments_created']
            print(f"\n\n👋 Bot beendet")
            print(f"📊 Heute erstellt: {posts_today} Posts, {comments_today} Kommentare")

def main():
    print("🤖 VOLLAUTOMATISCHER REDDIT BOT")
    print("="*50)
    print("Erstellt automatisch Posts und Kommentare")
    print("Keine User-Inputs erforderlich")
    print()
    
    bot = AutoPostCommentBot()
    bot.run_auto_loop()

if __name__ == "__main__":
    main()