#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Post Bot - Erstellt Reddit Posts aus archivierten Daten
BILDUNGSZWECKE ONLY - Kein automatisches Posten!
"""

import json
import random
import time
from pathlib import Path
import urllib.request
import os
import mimetypes
import re
import requests

class PostBot:
    def __init__(self):
        self.base_dir = Path("data_all")  # Geändert zu data_all
        self.posts_dir = self.base_dir / "Posts"
        self.comments_dir = Path("data/Comments")  # Für Kommentare
        self.posts = []
        self.comments = []
        self._load_data()
        
        # Tägliches Post-Tracking
        self.daily_posts = {}
        self._load_daily_stats()
        self.daily_target = None  # Wird täglich zufällig zwischen 1-4 gesetzt
        self.daily_comment_target = None  # Für Kommentare
        
        # Track bereits gepostete Posts und Kommentare
        self.posted_posts = set()
        self.posted_comments = set()
        self._load_posted_history()
        
        # Reddit API Konfiguration
        self._init_reddit_connection()
    
    def _init_reddit_connection(self):
        """Initialisiert die Reddit-Verbindung"""
        try:
            from config import ACTIVE_CONFIG
            import praw
            
            self.reddit = praw.Reddit(
                client_id=ACTIVE_CONFIG["client_id"],
                client_secret=ACTIVE_CONFIG["client_secret"],
                user_agent=ACTIVE_CONFIG["user_agent"],
                username=ACTIVE_CONFIG["username"],
                password=ACTIVE_CONFIG["password"],
                ratelimit_seconds=300
            )
            print(f"✅ Reddit-Verbindung hergestellt als u/{ACTIVE_CONFIG['username']}")
        except Exception as e:
            print(f"⚠️ Reddit-Verbindung fehlgeschlagen: {e}")
    
    def _load_data(self):
        """Lädt alle Posts aus dem Posts Ordner und Kommentare aus data/Comments"""
        print(f"📂 Lade Daten von: {self.base_dir}")
        
        # Posts laden direkt aus Posts Ordner
        if self.posts_dir.exists():
            print(f"  📁 Lade Posts aus: {self.posts_dir.name}")
            for post_folder in sorted(self.posts_dir.iterdir()):
                if post_folder.is_dir():
                    json_file = post_folder / "post_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.posts.append(data)
        
        # Kommentare laden aus data/Comments
        if self.comments_dir.exists():
            print(f"  📁 Lade Kommentare aus: {self.comments_dir}")
            for comment_folder in sorted(self.comments_dir.iterdir()):
                if comment_folder.is_dir() and comment_folder.name.startswith("comment_"):
                    json_file = comment_folder / "comment_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.comments.append(data)
        
        print(f"✅ Geladen: {len(self.posts)} Posts, {len(self.comments)} Kommentare")
    
    def _load_daily_stats(self):
        """Lädt tägliche Post-Statistiken"""
        from datetime import datetime
        stats_file = Path("./daily_post_stats.json")
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.daily_posts = json.load(f)
            except:
                self.daily_posts = {}
        else:
            self.daily_posts = {}
        
        # Prüfe ob heute schon ein Target gesetzt wurde
        today = datetime.now().strftime("%Y-%m-%d")
        if today in self.daily_posts:
            self.daily_target = self.daily_posts[today].get('target')
            self.daily_comment_target = self.daily_posts[today].get('comment_target')
            # Falls target nicht gesetzt oder None, setze neues Ziel
            if self.daily_target is None:
                self.daily_target = random.randint(1, 4)
                self.daily_posts[today]['target'] = self.daily_target
                self._save_daily_stats()
                print(f"🎯 Tagesziel korrigiert: {self.daily_target} Posts")
            if self.daily_comment_target is None:
                self.daily_comment_target = random.randint(5, 20)
                self.daily_posts[today]['comment_target'] = self.daily_comment_target
                self._save_daily_stats()
            elif self.daily_target == 0:
                print(f"🚫 Heute ist ein Pausentag - keine Posts")
            else:
                print(f"📊 Heutiges Ziel: {self.daily_target} Posts, {self.daily_comment_target} Kommentare")
                print(f"   Bereits erstellt: {self.daily_posts[today].get('count', 0)} Posts, {self.daily_posts[today].get('comment_count', 0)} Kommentare")
        else:
            # 15% Chance für einen Pausentag (0 Posts) - reduziert von 30%
            if random.random() < 0.15:
                self.daily_target = 0
                self.daily_posts[today] = {
                    'target': 0,
                    'count': 0,
                    'posts': [],
                    'skip_day': True
                }
                print(f"😴 Heute ist ein Pausentag - keine Posts geplant")
            else:
                # Setze neues tägliches Ziel (1-4 Posts, 5-20 Kommentare)
                self.daily_target = random.randint(1, 4)
                self.daily_comment_target = random.randint(5, 20)
                self.daily_posts[today] = {
                    'target': self.daily_target,
                    'comment_target': self.daily_comment_target,
                    'count': 0,
                    'comment_count': 0,
                    'posts': [],
                    'comments': []
                }
                print(f"🎯 Neues Tagesziel gesetzt: {self.daily_target} Posts, {self.daily_comment_target} Kommentare")
            self._save_daily_stats()
    
    def _save_daily_stats(self):
        """Speichert tägliche Post-Statistiken"""
        stats_file = Path("./daily_post_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.daily_posts, f, indent=2, ensure_ascii=False)
    
    def _load_posted_history(self):
        """Lädt Historie der bereits geposteten Posts"""
        history_file = Path("./posted_posts.json")
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.posted_posts = set(data.get('posts', []))
                    self.posted_comments = set(data.get('comments', []))
                    print(f"📝 Historie geladen: {len(self.posted_posts)} Posts, {len(self.posted_comments)} Kommentare")
            except:
                self.posted_posts = set()
        else:
            self.posted_posts = set()
    
    def _save_posted_history(self):
        """Speichert Historie der geposteten Posts und Kommentare"""
        history_file = Path("./posted_posts.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump({
                'posts': list(self.posted_posts),
                'comments': list(self.posted_comments)
            }, f, indent=2)
    
    def get_today_post_count(self):
        """Gibt zurück wie viele Posts heute bereits erstellt wurden"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        return self.daily_posts.get(today, {}).get('count', 0)
    
    def can_post_today(self):
        """Prüft ob heute noch Posts erstellt werden können"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.daily_posts:
            self._load_daily_stats()
        
        current_count = self.daily_posts[today].get('count', 0)
        target = self.daily_posts[today].get('target', self.daily_target)
        
        if current_count >= target:
            print(f"⚠️ Tageslimit erreicht: {current_count}/{target} Posts")
            return False
        return True
    
    def increment_daily_count(self, post_info=None):
        """Erhöht den täglichen Post-Zähler"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.daily_posts:
            self.daily_posts[today] = {
                'target': self.daily_target or random.randint(1, 4),
                'count': 0,
                'posts': []
            }
        
        self.daily_posts[today]['count'] += 1
        
        if post_info:
            self.daily_posts[today]['posts'].append({
                'time': datetime.now().isoformat(),
                'title': post_info.get('title', '')[:100],
                'subreddit': post_info.get('subreddit', 'unknown'),
                'score': post_info.get('score', 0)
            })
        
        self._save_daily_stats()
        
        current = self.daily_posts[today]['count']
        target = self.daily_posts[today]['target']
        print(f"📈 Tagesfortschritt: {current}/{target} Posts")
    
    def get_random_post(self):
        """Gibt einen zufälligen Post zurück mit alternativen Subreddits"""
        # Subreddits die OC verlangen oder strenge Regeln haben
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
                # Wähle zufällig einen alternativen Subreddit
                new_sub = random.choice(post['alternative_subreddits'])
                print(f"   📋 Verwende alternativen Subreddit: r/{new_sub}")
                post['subreddit'] = new_sub
            elif post.get('subreddit', '').lower() in problematic_subs:
                # Fallback für problematische Subs
                safe_subs = ['interestingasfuck', 'Damnthatsinteresting', 'BeAmazed', 'nextfuckinglevel']
                new_sub = random.choice(safe_subs)
                print(f"   ⚠️ r/{post['subreddit']} problematisch - verwende r/{new_sub}")
                post['subreddit'] = new_sub
            
            return post
        return None
    
    def clean_post_title(self, title):
        """Bereinigt Post-Titel von problematischen Elementen"""
        # Entferne mehrfache Leerzeichen
        title = ' '.join(title.split())
        
        # Entferne verbotene Phrasen
        banned_phrases = [
            'upvote if', 'upvote this', 'please upvote',
            '[OC]', '[oc]', '(OC)', '(oc)',
            'EDIT:', 'UPDATE:'
        ]
        
        for phrase in banned_phrases:
            title = re.sub(re.escape(phrase), '', title, flags=re.IGNORECASE)
        
        # Prüfe auf ALL CAPS
        if sum(1 for c in title if c.isupper()) > len(title) * 0.5:
            title = title.title()
            print(f"   📝 Titel von CAPS zu Normal konvertiert")
        
        # Entferne übermäßige Satzzeichen
        title = re.sub(r'[!?.]{2,}$', '.', title)
        
        # Max 300 Zeichen
        if len(title) > 300:
            title = title[:297] + "..."
        
        return title.strip()
    
    def save_generated_post(self, post_data):
        """Speichert generierten Post in organisiertem Ordner"""
        from datetime import datetime
        
        # Erstelle Ordnerstruktur: generated_posts/YYYY-MM/DD/
        base_dir = Path("./generated_posts")
        date_now = datetime.now()
        year_month = date_now.strftime("%Y-%m")
        day = date_now.strftime("%d")
        
        post_dir = base_dir / year_month / day
        post_dir.mkdir(parents=True, exist_ok=True)
        
        # Erstelle eindeutigen Dateinamen
        timestamp = date_now.strftime("%H%M%S")
        subreddit = post_data.get('subreddit', 'unknown')
        filename = f"post_{timestamp}_{subreddit}.json"
        
        # Füge Zeitstempel hinzu
        post_data['created_at'] = date_now.isoformat()
        post_data['date'] = date_now.strftime("%Y-%m-%d")
        post_data['time'] = date_now.strftime("%H:%M:%S")
        
        # Speichere Post
        file_path = post_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        
        # Erstelle auch eine Textvorschau
        preview_file = post_dir / f"preview_{timestamp}_{subreddit}.txt"
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write(f"Subreddit: r/{subreddit}\n")
            f.write(f"Titel: {post_data.get('title', '')}\n")
            f.write(f"Score (Original): {post_data.get('score', 0)}\n")
            f.write(f"Zeit: {date_now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            if post_data.get('selftext'):
                f.write(f"\nText:\n{post_data.get('selftext', '')[:500]}...\n")
            else:
                f.write(f"\nURL: {post_data.get('url', '')}\n")
        
        return file_path
    
    
    def get_image_for_post(self, post_data):
        """Sucht nach lokalem Bild oder lädt es herunter"""
        # Prüfe zuerst ob lokales Bild existiert
        post_id = post_data.get('id', '')
        
        # Suche nach lokalem Bild im Archiv
        for folder in self.posts_dir.iterdir():
            if folder.is_dir():
                # Prüfe ob es der richtige Post ist
                json_file = folder / "post_data.json"
                if json_file.exists():
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('id') == post_id or data.get('title') == post_data.get('title'):
                            # Suche nach Bilddatei
                            for img_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                                img_path = folder / f"image{img_ext}"
                                if img_path.exists():
                                    print(f"   📂 Verwende lokales Bild: {img_path.name}")
                                    return str(img_path)
        
        # Kein lokales Bild gefunden, versuche Download
        return self.download_image(post_data.get('url', ''))
    
    def download_image(self, url):
        """Lädt ein Bild herunter und speichert es temporär"""
        if not url:
            return None
            
        try:
            # Erstelle temp_images Ordner
            temp_dir = Path("./temp_images")
            temp_dir.mkdir(exist_ok=True)
            
            print(f"   ⬇️ Lade Bild herunter von URL...")
            
            # Bestimme Dateiendung
            if '.gif' in url.lower():
                ext = '.gif'
            elif '.png' in url.lower():
                ext = '.png'
            else:
                ext = '.jpg'
            
            # Download mit User-Agent
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=10)
            img_data = response.read()
            
            # Speichere temporär
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = temp_dir / f"img_{timestamp}{ext}"
            
            with open(temp_path, 'wb') as f:
                f.write(img_data)
            
            print(f"   ✅ Bild heruntergeladen: {temp_path.name}")
            return str(temp_path)
            
        except Exception as e:
            print(f"   ❌ Fehler beim Bilddownload: {e}")
            return None
    
    def create_post(self, post_data, dry_run=True, ignore_limit=False):
        """Erstellt einen Post auf Reddit"""
        # Prüfe ob heute ein Pausentag ist (außer bei ignore_limit)
        if not ignore_limit and self.daily_target == 0:
            print("😴 Heute ist ein Pausentag - keine Posts werden erstellt")
            return False
        
        # Prüfe ob Tageslimit erreicht (außer bei ignore_limit)
        if not ignore_limit and not self.can_post_today():
            return False
        
        if dry_run:
            print("\n⚠️ DRY RUN MODUS - Würde posten aber tut es nicht:")
            print(f"   Subreddit: r/{post_data.get('subreddit', 'unbekannt')}")
            print(f"   Titel: {post_data.get('title', '')[:80]}...")
            return False
        
        try:
            # ============================================
            # POST-CODE:
            # ============================================
            subreddit = self.reddit.subreddit(post_data['subreddit'])
            
            # Hole verfügbare Flairs für das Subreddit
            flair_choices = []
            flair_required = False
            try:
                flair_choices = list(subreddit.flair.link_templates)
                # Prüfe ob Flair erforderlich ist
                for flair in flair_choices:
                    if flair.get('mod_only', False) == False:
                        flair_required = True
                        break
            except Exception as e:
                print(f"   ℹ️ Keine Flair-Informationen verfügbar")
            
            # Finde passenden Flair
            flair_id = None
            flair_text = None
            
            if post_data.get('link_flair_text') and flair_choices:
                # Versuche Original-Flair zu finden
                for flair in flair_choices:
                    if flair['text'] == post_data.get('link_flair_text'):
                        flair_id = flair['id']
                        flair_text = flair['text']
                        break
            
            # Falls kein Flair gefunden aber erforderlich, nimm den ersten verfügbaren
            if not flair_id and flair_choices:
                for flair in flair_choices:
                    if not flair.get('mod_only', False):
                        flair_id = flair['id']
                        flair_text = flair['text']
                        print(f"   🏷️ Verwende Flair: {flair_text}")
                        break
            
            # Verwende variierten Titel wenn vorhanden, sonst Original
            title_to_use = post_data.get('varied_title', post_data['title'])
            clean_title = self.clean_post_title(title_to_use)
            
            # Erstelle den Post mit Flair wenn möglich
            if post_data.get('selftext'):
                # Text-Post - verwende variierten Text wenn vorhanden
                text_to_use = post_data.get('varied_selftext', post_data.get('selftext', ''))
                submission = subreddit.submit(
                    title=clean_title,
                    selftext=text_to_use,
                    flair_id=flair_id if flair_id else None
                )
            elif post_data.get('url'):
                # Prüfe ob es ein Bild ist
                url = post_data.get('url', '')
                is_image = any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', 'i.redd.it', 'imgur'])
                
                if is_image:
                    # Versuche lokales Bild zu finden oder herunterzuladen
                    image_path = self.get_image_for_post(post_data)
                    if image_path:
                        try:
                            # Versuche als Bild-Post mit Datei
                            submission = subreddit.submit_image(
                                title=clean_title,
                                image_path=image_path,
                                flair_id=flair_id if flair_id else None
                            )
                            print(f"   ✅ Bild-Post mit neuem Upload erstellt")
                            # Lösche temporäres Bild (nicht lokale Archiv-Bilder)
                            if 'temp_images' in image_path:
                                os.remove(image_path)
                        except Exception as e:
                            print(f"   ⚠️ Upload fehlgeschlagen: {e}")
                            # Fallback: Verwende Original-URL
                            submission = subreddit.submit(
                                title=clean_title,
                                url=url,
                                flair_id=flair_id if flair_id else None
                            )
                            print(f"   ⚠️ Verwende Original-URL stattdessen")
                    else:
                        # Fallback wenn Download fehlschlägt
                        submission = subreddit.submit(
                            title=clean_title,
                            url=url,
                            flair_id=flair_id if flair_id else None
                        )
                        print(f"   ⚠️ Verwende Original-URL (Download fehlgeschlagen)")
                else:
                    # Normaler Link-Post (kein Bild)
                    submission = subreddit.submit(
                        title=clean_title,
                        url=url,
                        flair_id=flair_id if flair_id else None
                    )
            
            if submission and flair_text:
                print(f"   🏷️ Flair gesetzt: {flair_text}")
            
            print(f"✅ Post erfolgreich erstellt!")
            print(f"   URL: https://reddit.com{submission.permalink}")
            
            # Speichere in Ordnerstruktur
            saved_path = self.save_generated_post(post_data)
            print(f"   💾 Gespeichert: {saved_path.name}")
            
            # Update Tracking
            self.posted_posts.add(post_data.get('id', ''))
            self._save_posted_history()
            
            # Nur Daily Count erhöhen wenn nicht ignore_limit
            if not ignore_limit:
                self.increment_daily_count(post_data)
            
            return True
            # ============================================
            
        except Exception as e:
            error_msg = str(e)
            if "FLAIR_REQUIRED" in error_msg or "flair" in error_msg.lower():
                print(f"❌ Flair-Fehler: Subreddit r/{post_data.get('subreddit')} erfordert Flair")
                print("   Versuche mit anderem Post...")
            else:
                print(f"❌ Fehler beim Posten: {e}")
            return False
    
    def run_post_loop(self, start_hour=10, end_hour=22):
        """Hauptschleife - erstellt Posts mit Tageslimit"""
        from datetime import datetime, timedelta
        import time
        
        print("\n🤖 POST BOT - AUTOMATISCHER LOOP MIT TAGESLIMIT")
        print("="*60)
        print(f"⏰ Aktive Zeit: {start_hour}:00 - {end_hour}:00 Uhr")
        print(f"📊 Tägliches Ziel: {self.daily_target} Posts (Max 4/Tag)")
        print(f"⏳ Wartezeit zwischen Posts: 0.5-2 Stunden")
        print("\nDrücke Ctrl+C zum Beenden")
        print("="*60)
        
        session_count = 0
        last_post_time = None
        
        try:
            while True:
                current_hour = datetime.now().hour
                current_time = datetime.now().strftime("%H:%M:%S")
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Prüfe ob neuer Tag
                if today not in self.daily_posts:
                    self._load_daily_stats()
                    if self.daily_target == 0:
                        print(f"\n😴 Heute ist ein Pausentag - keine Posts geplant")
                    else:
                        print(f"\n🌅 Neuer Tag! Ziel: {self.daily_target} Posts")
                
                # Prüfe ob heute ein Pausentag ist
                if self.daily_target == 0:
                    print(f"\n😴 [{current_time}] Pausentag - warte bis morgen...")
                    time.sleep(7200)  # 2 Stunden
                    continue
                
                # Prüfe ob Tageslimit erreicht
                if not self.can_post_today():
                    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                    wait_seconds = (tomorrow - datetime.now()).total_seconds()
                    hours_to_wait = int(wait_seconds // 3600)
                    print(f"\n✅ [{current_time}] Tagesziel erreicht!")
                    print(f"   Warte bis morgen ({hours_to_wait}h)")
                    time.sleep(3600)  # 1 Stunde
                    continue
                
                # Prüfe ob in aktiver Zeit
                if current_hour < start_hour or current_hour >= end_hour:
                    print(f"\n😴 [{current_time}] Außerhalb der aktiven Zeit...")
                    time.sleep(3600)  # 1 Stunde
                    continue
                
                # Berechne wie viele Posts noch heute
                current_count = self.get_today_post_count()
                # Stelle sicher dass daily_target gesetzt ist
                if self.daily_target is None:
                    self._load_daily_stats()
                    if self.daily_target is None:
                        self.daily_target = random.randint(1, 4)
                
                remaining_today = self.daily_target - current_count
                active_hours_left = end_hour - current_hour
                
                if remaining_today <= 0:
                    continue
                
                # Bei nur 1-4 Posts pro Tag, mache maximal 1 Post pro Session
                posts_this_hour = 1
                
                # Mindestabstand zwischen Posts (0.5-2 Stunden)
                if last_post_time:
                    time_since_last = (datetime.now() - last_post_time).total_seconds()
                    min_wait = random.randint(1800, 7200)  # 30 Min - 2 Stunden
                    if time_since_last < min_wait:
                        wait_time = int(min_wait - time_since_last)
                        print(f"\n⏳ Warte noch {wait_time//60} Minuten ({wait_time/3600:.1f}h) bis zum nächsten Post...")
                        time.sleep(wait_time)
                        continue
                
                print(f"\n🕐 [{current_time}] Erstelle {posts_this_hour} Post(s)")
                print(f"   Tagesfortschritt: {current_count}/{self.daily_target}")
                print("-"*40)
                
                # Erstelle Posts
                for i in range(posts_this_hour):
                    post = self.get_random_post()
                    if post:
                        print(f"\n📝 POST #{session_count + 1}:")
                        print(f"Titel: {post.get('title', '')[:80]}")
                        print(f"Subreddit: r/{post.get('subreddit', 'unbekannt')}")
                        
                        if self.create_post(post, dry_run=False):
                            session_count += 1
                            last_post_time = datetime.now()
                        
                        if i < posts_this_hour - 1:
                            wait = random.randint(300, 600)  # 5-10 Min zwischen Posts
                            print(f"⏳ Warte {wait//60} Minuten...")
                            time.sleep(wait)
                
                # Wartezeit bis zur nächsten Prüfung (30-90 Minuten)
                wait_minutes = random.randint(30, 90)
                print(f"\n⏰ Warte {wait_minutes} Minuten ({wait_minutes/60:.1f}h) bis zur nächsten Prüfung...")
                time.sleep(wait_minutes * 60)
                
        except KeyboardInterrupt:
            current_count = self.get_today_post_count()
            print(f"\n\n👋 Loop beendet")
            print(f"📊 Heute erstellt: {current_count}/{self.daily_target} Posts")
            print(f"   Sessions heute: {session_count}")
    
    def find_target_posts(self):
        """Findet Posts zum Kommentieren in relevanten Subreddits"""
        try:
            # Target Subreddits für Kommentare (niedrige Anforderungen)
            target_subreddits = [
                'CasualConversation', 'self', 'NoStupidQuestions',
                'findareddit', 'Showerthoughts', 'DoesAnybodyElse',
                'offmychest', 'TrueOffMyChest', 'confession',
                'Journaling', 'productivity', 'GetMotivated'
            ]
            
            target_posts = []
            
            # Durchsuche erste 3 Subreddits
            for sub_name in random.sample(target_subreddits, min(3, len(target_subreddits))):
                try:
                    subreddit = self.reddit.subreddit(sub_name)
                    # Hole neue Posts (letzte 24h)
                    for post in subreddit.new(limit=10):
                        if post.created_utc > time.time() - 86400:  # Letzten 24h
                            if post.id not in self.posted_comments:
                                if not post.locked and not post.archived:
                                    target_posts.append(post)
                except Exception as e:
                    print(f"   ⚠️ Fehler bei r/{sub_name}: {str(e)[:50]}")
                    continue
            
            return target_posts
            
        except Exception as e:
            print(f"❌ Fehler beim Suchen von Posts: {e}")
            return []
    
    def find_best_comment_with_ai(self, post):
        """Nutzt OpenRouter API um den passendsten Kommentar aus dem Archiv zu finden"""
        if not self.comments:
            print("❌ Keine Kommentare im Archiv gefunden!")
            return None
        
        try:
            from config import OPENROUTER_API_KEY
            
            # Nimm eine Auswahl von Kommentaren (max 20 um API Kosten zu sparen)
            sample_size = min(20, len(self.comments))
            comment_sample = random.sample(self.comments, sample_size)
            
            # Bereite Kommentare für API vor
            comments_text = ""
            for i, comment in enumerate(comment_sample):
                body = comment.get('body', '')[:300]  # Max 300 Zeichen pro Kommentar
                comments_text += f"{i+1}. {body}\n\n"
            
            # API Request
            prompt = f"""You are selecting the MOST RELEVANT comment from an archive to reply to a Reddit post.

Post Title: {post.title}
Post Subreddit: r/{post.subreddit.display_name}

Available Comments:
{comments_text}

Select the NUMBER of the comment that best fits as a reply to this post. Consider:
- Relevance to the topic
- Appropriate tone for the subreddit
- Natural flow of conversation

Return ONLY the number (1-{sample_size}) of the best comment, nothing else."""

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/llama-3.2-3b-instruct:free",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                choice_text = result['choices'][0]['message']['content'].strip()
                
                # Extrahiere Nummer
                try:
                    choice_num = int(''.join(filter(str.isdigit, choice_text)))
                    if 1 <= choice_num <= sample_size:
                        selected = comment_sample[choice_num - 1]
                        print(f"   🤖 AI wählte Kommentar #{choice_num} als passendsten")
                        comment_body = selected.get('body', '')
                    else:
                        # Fallback: Zufällig
                        selected = random.choice(comment_sample)
                        print(f"   📋 AI-Auswahl ungültig, nutze zufälligen Kommentar")
                        comment_body = selected.get('body', '')
                except:
                    # Fallback: Zufällig
                    selected = random.choice(comment_sample)
                    print(f"   📋 AI-Antwort nicht parsebar, nutze zufälligen Kommentar")
                    comment_body = selected.get('body', '')
            else:
                # API Fehler - Fallback
                selected = random.choice(self.comments)
                print(f"   ⚠️ API-Fehler ({response.status_code}), nutze zufälligen Kommentar")
                comment_body = selected.get('body', '')
                
        except Exception as e:
            # Fehler - Fallback
            print(f"   ⚠️ Fehler bei AI-Auswahl: {str(e)[:50]}")
            selected = random.choice(self.comments)
            print(f"   📋 Nutze zufälligen Kommentar als Fallback")
            comment_body = selected.get('body', '')
        
        # Kürze sehr lange Kommentare
        if len(comment_body) > 500:
            sentences = comment_body[:500].split('. ')
            if len(sentences) > 1:
                comment_body = '. '.join(sentences[:-1]) + '.'
            else:
                comment_body = comment_body[:497] + '...'
        
        return comment_body
    
    def get_random_comment_from_archive(self, post=None):
        """Holt einen passenden Kommentar aus dem Archiv (mit AI wenn möglich)"""
        if not self.comments:
            print("❌ Keine Kommentare im Archiv gefunden!")
            return None
        
        # Versuche AI-basierte Auswahl wenn Post gegeben
        if post and hasattr(post, 'title'):
            return self.find_best_comment_with_ai(post)
        else:
            # Kein Post - nimm zufälligen
            selected = random.choice(self.comments)
            print(f"   📋 Zufälliger Kommentar aus Archiv")
            comment_body = selected.get('body', '')
            
            # Kürze sehr lange Kommentare
            if len(comment_body) > 500:
                sentences = comment_body[:500].split('. ')
                if len(sentences) > 1:
                    comment_body = '. '.join(sentences[:-1]) + '.'
                else:
                    comment_body = comment_body[:497] + '...'
            
            return comment_body
    
    def generate_comment(self, post):
        """Nutzt einen Kommentar aus dem Archiv"""
        return self.get_random_comment_from_archive(post)
    
    def create_comment(self, post):
        """Erstellt einen Kommentar auf einem Post"""
        try:
            comment_text = self.generate_comment(post)
            
            # Erstelle Kommentar
            comment = post.reply(comment_text)
            
            print(f"✅ Kommentar erstellt auf r/{post.subreddit.display_name}")
            print(f"   Post: {post.title[:60]}...")
            print(f"   Kommentar: {comment_text[:100]}...")
            print(f"   URL: https://reddit.com{comment.permalink}")
            
            # Update Tracking
            self.posted_comments.add(post.id)
            self._save_posted_history()
            
            # Update tägliche Statistik
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            
            if today not in self.daily_posts:
                self._load_daily_stats()
            
            if 'comment_count' not in self.daily_posts[today]:
                self.daily_posts[today]['comment_count'] = 0
                self.daily_posts[today]['comments'] = []
            
            self.daily_posts[today]['comment_count'] += 1
            self.daily_posts[today]['comments'].append({
                'time': datetime.now().isoformat(),
                'post_title': post.title[:100],
                'subreddit': post.subreddit.display_name,
                'comment': comment_text[:200],
                'permalink': comment.permalink
            })
            self._save_daily_stats()
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg:
                print(f"❌ Zugriff verweigert (403): ")
                print(f"   • Account könnte zu neu sein oder zu wenig Karma haben")
                print(f"   • r/{post.subreddit.display_name} hat möglicherweise Beschränkungen")
                print(f"   • Versuche ein anderes Subreddit")
            elif "429" in error_msg:
                print(f"❌ Rate Limit erreicht - zu viele Anfragen")
                print(f"   • Warte ein paar Minuten")
            elif "401" in error_msg:
                print(f"❌ Authentifizierung fehlgeschlagen")
                print(f"   • Überprüfe deine Reddit Credentials in config.py")
            else:
                print(f"❌ Fehler beim Kommentieren: {error_msg[:100]}")
            return False
    
    def can_comment_today(self):
        """Prüft ob heute noch Kommentare erstellt werden können"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.daily_posts:
            self._load_daily_stats()
        
        current_count = self.daily_posts[today].get('comment_count', 0)
        target = self.daily_posts[today].get('comment_target', self.daily_comment_target or 10)
        
        if current_count >= target:
            print(f"⚠️ Kommentar-Limit erreicht: {current_count}/{target} Kommentare")
            return False
        return True
    
    def create_comments_batch(self, count=5):
        """Erstellt mehrere Kommentare in einem Batch"""
        print(f"\n💬 Erstelle bis zu {count} Kommentare...")
        
        target_posts = self.find_target_posts()
        if not target_posts:
            print("❌ Keine passenden Posts zum Kommentieren gefunden")
            return 0
        
        created = 0
        for i in range(min(count, len(target_posts))):
            if not self.can_comment_today():
                break
                
            post = target_posts[i]
            print(f"\n💬 Kommentar {i+1}/{count}:")
            
            if self.create_comment(post):
                created += 1
                # Pause zwischen Kommentaren
                if i < count - 1:
                    wait = random.randint(60, 300)  # 1-5 Min
                    print(f"   ⏳ Warte {wait} Sekunden...")
                    time.sleep(wait)
        
        print(f"\n✅ {created} Kommentare erstellt")
        return created
    
    def show_statistics(self):
        """Zeigt Statistiken über die geladenen Posts"""
        print("\n📊 STATISTIKEN:")
        print(f"Posts gesamt: {len(self.posts)}")
        
        if self.posts:
            avg_score = sum(p.get('score', 0) for p in self.posts) / len(self.posts)
            print(f"Durchschnittlicher Post-Score: {avg_score:.0f}")
            
            # Top Posts nach Score
            sorted_posts = sorted(self.posts, key=lambda x: x.get('score', 0), reverse=True)
            print(f"\n🏆 Top 5 Posts nach Score:")
            for i, post in enumerate(sorted_posts[:5], 1):
                print(f"  {i}. Score {post.get('score', 0):,} - {post.get('title', '')[:60]}...")
            
            # Subreddit Statistiken
            subreddit_counts = {}
            for post in self.posts:
                sub = post.get('subreddit', 'unknown')
                subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1
            
            print(f"\n📊 Verschiedene Subreddits: {len(subreddit_counts)}")
            print(f"\n🏷️ Top 10 Subreddits nach Anzahl Posts:")
            for sub, count in sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  • r/{sub}: {count} Posts")

def main():
    """Hauptfunktion"""
    from datetime import datetime
    bot = PostBot()
    
    print("\n🤖 Post Bot - Reddit Post & Kommentar Generator")
    print("="*50)
    print("Was möchtest du tun?")
    print("1. 🔄 Automatischer Post-Loop")
    print("2. 📝 Einzelnen Post erstellen")
    print("3. 💬 Kommentare erstellen")
    print("4. 📊 Statistiken anzeigen")
    print("5. 🎲 Zufälligen Post anzeigen")
    print("6. 🔍 Posts nach Subreddit filtern")
    
    choice = input("\nAuswahl (1-6): ").strip()
    
    if choice == "1":
        # Automatischer Loop mit Tageslimit
        print("\n🔄 AUTOMATISCHER POST-LOOP MIT TAGESLIMIT")
        print("="*60)
        print(f"• Tägliches Ziel: {bot.daily_target} Posts (0-4 pro Tag)")
        print(f"• Heute bereits: {bot.get_today_post_count()} Posts")
        print("• Aktiv von 10:00 - 22:00 Uhr")
        print("• Wartezeit zwischen Posts: 0.5-2 Stunden")
        
        confirm = "j" #input("\n⚠️ WARNUNG: Posts werden auf Reddit erstellt! Fortfahren? (j/n): ").strip().lower()
        if confirm in ['j', 'ja', 'yes', 'y']:
            bot.run_post_loop(start_hour=10, end_hour=22)
        else:
            print("❌ Abgebrochen")
            
    elif choice == "2":
        # Einzelner Post
        post = bot.get_random_post()
        if post:
            print(f"\n📝 POST:")
            print(f"Titel: {post.get('title', 'Kein Titel')}")
            print(f"Subreddit: r/{post.get('subreddit', 'unbekannt')}")
            print(f"Score (Original): {post.get('score', 0):,}")
            
            if post.get('selftext'):
                print(f"\nText: {post.get('selftext', '')[:200]}...")
            elif post.get('url'):
                print(f"\nURL: {post.get('url')}")
            
            action = input("\n📮 Diesen Post erstellen? (j/n): ").strip().lower()
            if action in ['j', 'ja', 'yes', 'y']:
                bot.create_post(post, dry_run=False, ignore_limit=True)
            else:
                print("❌ Abgebrochen")
                
    elif choice == "3":
        # Kommentare erstellen
        print("\n💬 KOMMENTARE ERSTELLEN")
        print("="*60)
        
        today_comments = bot.daily_posts.get(datetime.now().strftime("%Y-%m-%d"), {}).get('comment_count', 0)
        comment_target = bot.daily_comment_target or 10
        
        print(f"Heutiges Kommentar-Ziel: {comment_target}")
        print(f"Bereits erstellt: {today_comments}")
        
        if today_comments >= comment_target:
            print("⚠️ Tageslimit für Kommentare bereits erreicht!")
        else:
            remaining = comment_target - today_comments
            print(f"Noch möglich: {remaining} Kommentare")
            
            print("\nWie viele Kommentare erstellen?")
            print(f"1. Einzelnen Kommentar")
            print(f"2. 5 Kommentare")
            print(f"3. 10 Kommentare")
            print(f"4. Alle verbleibenden ({remaining})")
            
            sub_choice = input("\nAuswahl (1-4): ").strip()
            
            if sub_choice == "1":
                count = 1
            elif sub_choice == "2":
                count = min(5, remaining)
            elif sub_choice == "3":
                count = min(10, remaining)
            elif sub_choice == "4":
                count = remaining
            else:
                count = 1
            
            confirm = input(f"\n⚠️ {count} Kommentare erstellen? (j/n): ").strip().lower()
            if confirm in ['j', 'ja', 'yes', 'y']:
                bot.create_comments_batch(count)
            else:
                print("❌ Abgebrochen")
        
    elif choice == "4":
        bot.show_statistics()
        
    elif choice == "5":
        # Zufälligen Post anzeigen
        post = bot.get_random_post()
        if post:
            print(f"\n📝 ZUFÄLLIGER POST:")
            print(f"Titel: {post.get('title', 'Kein Titel')}")
            print(f"Subreddit: r/{post.get('subreddit', 'unbekannt')}")
            print(f"Score: {post.get('score', 0):,}")
            print(f"Kommentare: {post.get('num_comments', 0):,}")
            
            if post.get('link_flair_text'):
                print(f"Flair: {post.get('link_flair_text')}")
            
            if post.get('selftext'):
                print(f"\nText-Vorschau: {post.get('selftext', '')[:300]}...")
            elif post.get('url'):
                print(f"\nURL: {post.get('url')}")
                
    elif choice == "6":
        # Posts nach Subreddit filtern
        subreddit = input("\nSubreddit eingeben (z.B. adhdmeme): ").strip()
        
        filtered_posts = [p for p in bot.posts if p.get('subreddit', '').lower() == subreddit.lower()]
        
        if filtered_posts:
            print(f"\n📊 {len(filtered_posts)} Posts in r/{subreddit} gefunden")
            print("\nTop 10 Posts:")
            sorted_posts = sorted(filtered_posts, key=lambda x: x.get('score', 0), reverse=True)
            for i, post in enumerate(sorted_posts[:10], 1):
                print(f"  {i}. Score {post.get('score', 0):,} - {post.get('title', '')[:60]}...")
        else:
            print(f"❌ Keine Posts für r/{subreddit} gefunden")
    else:
        print("Ungültige Auswahl")

if __name__ == "__main__":
    main()