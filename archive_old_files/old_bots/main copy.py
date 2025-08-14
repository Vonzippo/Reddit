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

class PostBot:
    def __init__(self):
        self.base_dir = Path("/Users/patrick/Desktop/Reddit/data")
        self.posts_dir = self.base_dir / "Posts"
        self.posts = []
        self._load_data()
        
        # Tägliches Post-Tracking
        self.daily_posts = {}
        self._load_daily_stats()
        self.daily_target = None  # Wird täglich zufällig zwischen 5-20 gesetzt
        
        # Track bereits gepostete Posts
        self.posted_posts = set()
        self._load_posted_history()
        
        # Reddit API Konfiguration
        self._init_reddit_connection()
    
    def _init_reddit_connection(self):
        """Initialisiert die Reddit-Verbindung"""
        try:
            import praw
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
        except Exception as e:
            print(f"⚠️ Reddit-Verbindung fehlgeschlagen: {e}")
    
    def _load_data(self):
        """Lädt alle Posts aus dem Posts Ordner"""
        print(f"📂 Lade Daten von: {self.base_dir}")
        
        # Posts laden direkt aus Posts Ordner
        if self.posts_dir.exists():
            print(f"  📁 Lade Posts aus: {self.posts_dir.name}")
            for post_folder in sorted(self.posts_dir.iterdir()):
                if post_folder.is_dir() and post_folder.name.startswith("post_"):
                    json_file = post_folder / "post_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.posts.append(data)
        
        print(f"✅ Geladen: {len(self.posts)} Posts")
    
    def _load_daily_stats(self):
        """Lädt tägliche Post-Statistiken"""
        from datetime import datetime
        stats_file = Path("/Users/patrick/Desktop/Reddit/daily_post_stats.json")
        
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
            # Falls target nicht gesetzt oder None, setze neues Ziel
            if self.daily_target is None:
                self.daily_target = random.randint(1, 4)
                self.daily_posts[today]['target'] = self.daily_target
                self._save_daily_stats()
                print(f"🎯 Tagesziel korrigiert: {self.daily_target} Posts")
            elif self.daily_target == 0:
                print(f"🚫 Heute ist ein Pausentag - keine Posts")
            else:
                print(f"📊 Heutiges Ziel: {self.daily_target} Posts")
                print(f"   Bereits erstellt: {self.daily_posts[today].get('count', 0)}")
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
                # Setze neues tägliches Ziel (1-4 Posts)
                self.daily_target = random.randint(1, 4)
                self.daily_posts[today] = {
                    'target': self.daily_target,
                    'count': 0,
                    'posts': []
                }
                print(f"🎯 Neues Tagesziel gesetzt: {self.daily_target} Posts")
            self._save_daily_stats()
    
    def _save_daily_stats(self):
        """Speichert tägliche Post-Statistiken"""
        stats_file = Path("/Users/patrick/Desktop/Reddit/daily_post_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.daily_posts, f, indent=2, ensure_ascii=False)
    
    def _load_posted_history(self):
        """Lädt Historie der bereits geposteten Posts"""
        history_file = Path("/Users/patrick/Desktop/Reddit/posted_posts.json")
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.posted_posts = set(data.get('posts', []))
                    print(f"📝 Historie geladen: {len(self.posted_posts)} bereits gepostete Posts")
            except:
                self.posted_posts = set()
        else:
            self.posted_posts = set()
    
    def _save_posted_history(self):
        """Speichert Historie der geposteten Posts"""
        history_file = Path("/Users/patrick/Desktop/Reddit/posted_posts.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump({'posts': list(self.posted_posts)}, f, indent=2)
    
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
        """Gibt einen zufälligen Post zurück (bevorzugt noch nicht gepostete)"""
        if self.posts:
            # Versuche einen noch nicht geposteten Post zu finden
            unposted = [p for p in self.posts if p.get('id') not in self.posted_posts]
            if unposted:
                return random.choice(unposted)
            # Falls alle gepostet, nimm irgendeinen
            return random.choice(self.posts)
        return None
    
    def save_generated_post(self, post_data):
        """Speichert generierten Post in organisiertem Ordner"""
        from datetime import datetime
        
        # Erstelle Ordnerstruktur: generated_posts/YYYY-MM/DD/
        base_dir = Path("/Users/patrick/Desktop/Reddit/generated_posts")
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
            temp_dir = Path("/Users/patrick/Desktop/Reddit/temp_images")
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
            
            # Erstelle den Post mit Flair wenn möglich
            if post_data.get('selftext'):
                # Text-Post
                submission = subreddit.submit(
                    title=post_data['title'],
                    selftext=post_data.get('selftext', ''),
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
                                title=post_data['title'],
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
                                title=post_data['title'],
                                url=url,
                                flair_id=flair_id if flair_id else None
                            )
                            print(f"   ⚠️ Verwende Original-URL stattdessen")
                    else:
                        # Fallback wenn Download fehlschlägt
                        submission = subreddit.submit(
                            title=post_data['title'],
                            url=url,
                            flair_id=flair_id if flair_id else None
                        )
                        print(f"   ⚠️ Verwende Original-URL (Download fehlgeschlagen)")
                else:
                    # Normaler Link-Post (kein Bild)
                    submission = subreddit.submit(
                        title=post_data['title'],
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
    bot = PostBot()
    
    print("\n🤖 Post Bot - Reddit Post Generator")
    print("="*50)
    print("Was möchtest du tun?")
    print("1. 🔄 Automatischer Post-Loop")
    print("2. 📝 Einzelnen Post erstellen")
    print("3. 📊 Statistiken anzeigen")
    print("4. 🎲 Zufälligen Post anzeigen")
    print("5. 🔍 Posts nach Subreddit filtern")
    
    choice = input("\nAuswahl (1-5): ").strip()
    
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
        bot.show_statistics()
        
    elif choice == "4":
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
                
    elif choice == "5":
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