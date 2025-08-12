#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Post Bot - Verbesserte Version mit allen Features aus main_other.py
Nutzt data_all/Posts mit alternativen Subreddits
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

class PostBot:
    def __init__(self):
        # Nutze data_all statt data
        self.base_dir = Path("/Users/patrick/Desktop/Reddit/data_all")
        self.posts_dir = self.base_dir / "Posts"
        self.posts = []
        self._load_data()
        
        # Tägliches Post-Tracking
        self.daily_posts = {}
        self._load_daily_stats()
        self.daily_target = None  # Wird täglich zufällig zwischen 1-4 gesetzt
        
        # Track bereits gepostete Posts
        self.posted_posts = set()
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
            # Test der Verbindung
            user = self.reddit.user.me()
            print(f"✅ Reddit-Verbindung hergestellt als u/{user.name}")
            
            # Prüfe Account-Alter und Karma
            account_age_days = (time.time() - user.created_utc) / 86400
            account_karma = user.link_karma + user.comment_karma
            print(f"👤 Account: {account_age_days:.0f} Tage alt, {account_karma} Karma")
            
        except Exception as e:
            print(f"⚠️ Reddit-Verbindung fehlgeschlagen: {e}")
    
    def _load_data(self):
        """Lädt alle Posts aus data_all/Posts"""
        print(f"📂 Lade Daten von: {self.base_dir}")
        
        # Posts laden aus data_all/Posts
        if self.posts_dir.exists():
            print(f"  📁 Lade Posts aus: {self.posts_dir.name}")
            for post_folder in sorted(self.posts_dir.iterdir()):
                if post_folder.is_dir():
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
            # 15% Chance für einen Pausentag
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
    
    def download_image(self, url):
        """Lädt ein Bild herunter und speichert es temporär"""
        if not url:
            return None
            
        try:
            # Erstelle temp_images Ordner
            temp_dir = Path("/Users/patrick/Desktop/Reddit/temp_images")
            temp_dir.mkdir(exist_ok=True)
            
            print(f"   ⬇️ Lade Bild herunter...")
            
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
    
    def get_image_for_post(self, post_data):
        """Sucht nach lokalem Bild oder lädt es herunter"""
        post_id = post_data.get('id', '')
        
        # Suche nach lokalem Bild im Archiv
        for folder in self.posts_dir.iterdir():
            if folder.is_dir():
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
    
    def delete_posted_folder(self, post_data):
        """Löscht den Post-Ordner nach erfolgreichem Posten"""
        post_id = post_data.get('id', '')
        post_title = post_data.get('title', '')
        
        for folder in self.posts_dir.iterdir():
            if folder.is_dir():
                json_file = folder / "post_data.json"
                if json_file.exists():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if data.get('id') == post_id or data.get('title') == post_title:
                                # Lösche den Ordner
                                try:
                                    shutil.rmtree(folder)
                                    print(f"   🗑️ Post-Ordner gelöscht: {folder.name}")
                                except OSError:
                                    # Fallback: Lösche Dateien einzeln
                                    for file in folder.iterdir():
                                        if file.is_file() and not str(file.name).startswith('.nfs'):
                                            try:
                                                file.unlink()
                                            except:
                                                pass
                                    try:
                                        folder.rmdir()
                                        print(f"   🗑️ Post-Ordner gelöscht: {folder.name}")
                                    except:
                                        print(f"   ⚠️ Ordner enthält noch temporäre Dateien")
                                
                                # Entferne aus interner Liste
                                self.posts = [p for p in self.posts if p.get('id') != post_id]
                                return True
                    except Exception as e:
                        print(f"   ⚠️ Fehler: {e}")
        return False
    
    def create_post(self, post_data, dry_run=True, ignore_limit=False):
        """Erstellt einen Post auf Reddit mit allen Verbesserungen"""
        # Prüfe Tageslimit
        if not ignore_limit and self.daily_target == 0:
            print("😴 Heute ist ein Pausentag - keine Posts werden erstellt")
            return False
        
        if not ignore_limit and not self.can_post_today():
            return False
        
        if dry_run:
            print("\n⚠️ DRY RUN MODUS - Würde posten aber tut es nicht:")
            print(f"   Subreddit: r/{post_data.get('subreddit', 'unbekannt')}")
            print(f"   Titel: {post_data.get('title', '')[:80]}...")
            return False
        
        try:
            subreddit = self.reddit.subreddit(post_data['subreddit'])
            
            # Hole verfügbare Flairs
            flair_id = None
            flair_text = None
            try:
                flair_choices = list(subreddit.flair.link_templates)
                if flair_choices:
                    # Versuche Original-Flair zu finden
                    if post_data.get('link_flair_text'):
                        for flair in flair_choices:
                            if flair['text'] == post_data.get('link_flair_text'):
                                flair_id = flair['id']
                                flair_text = flair['text']
                                break
                    
                    # Falls nicht gefunden, nimm ersten verfügbaren
                    if not flair_id:
                        for flair in flair_choices:
                            if not flair.get('mod_only', False):
                                flair_id = flair['id']
                                flair_text = flair['text']
                                print(f"   🏷️ Verwende Flair: {flair_text}")
                                break
            except:
                pass
            
            # Bereinige Titel
            clean_title = self.clean_post_title(post_data['title'])
            
            # Erstelle den Post
            if post_data.get('selftext'):
                # Text-Post
                submission = subreddit.submit(
                    title=clean_title,
                    selftext=post_data.get('selftext', ''),
                    flair_id=flair_id if flair_id else None
                )
            elif post_data.get('url'):
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
                            print(f"   ✅ Bild-Post mit Upload erstellt")
                            # Lösche temporäres Bild
                            if 'temp_images' in image_path:
                                os.remove(image_path)
                        except Exception as e:
                            print(f"   ⚠️ Upload fehlgeschlagen: {e}")
                            # Fallback: URL
                            submission = subreddit.submit(
                                title=clean_title,
                                url=url,
                                flair_id=flair_id if flair_id else None
                            )
                    else:
                        # Fallback: URL
                        submission = subreddit.submit(
                            title=clean_title,
                            url=url,
                            flair_id=flair_id if flair_id else None
                        )
                else:
                    # Link-Post
                    submission = subreddit.submit(
                        title=clean_title,
                        url=url,
                        flair_id=flair_id if flair_id else None
                    )
            
            print(f"✅ Post erfolgreich erstellt!")
            print(f"   URL: https://reddit.com{submission.permalink}")
            
            # Speichere generierten Post
            self.save_generated_post(post_data)
            
            # Update Tracking
            self.posted_posts.add(post_data.get('id', ''))
            self._save_posted_history()
            
            if not ignore_limit:
                self.increment_daily_count(post_data)
            
            # Lösche Post-Ordner nach erfolgreichem Posten
            self.delete_posted_folder(post_data)
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "FLAIR_REQUIRED" in error_msg:
                print(f"❌ Flair-Fehler: Subreddit r/{post_data.get('subreddit')} erfordert Flair")
            else:
                print(f"❌ Fehler beim Posten: {e}")
            return False
    
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
    
    def get_today_count(self):
        """Gibt zurück wie viele Posts heute bereits erstellt wurden"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        return self.daily_posts.get(today, {}).get('count', 0)
    
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
    
    def save_generated_post(self, post_data):
        """Speichert generierten Post in organisiertem Ordner"""
        from datetime import datetime
        
        # Erstelle Ordnerstruktur
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
        
        return file_path
    
    def run_auto_loop(self, start_hour=10, end_hour=22):
        """Hauptschleife - erstellt Posts mit Tageslimit"""
        from datetime import datetime, timedelta
        
        print("\n🤖 POST BOT - AUTOMATISCHER LOOP")
        print("="*60)
        print(f"⏰ Aktive Zeit: {start_hour}:00 - {end_hour}:00 Uhr")
        print(f"📊 Tagesziel: {self.daily_target} Posts (1-4/Tag)")
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
                        print(f"\n😴 Heute ist ein Pausentag")
                    else:
                        print(f"\n🌅 Neuer Tag! Ziel: {self.daily_target} Posts")
                
                # Prüfe ob Pausentag
                if self.daily_target == 0:
                    print(f"\n😴 [{current_time}] Pausentag - warte bis morgen...")
                    time.sleep(7200)
                    continue
                
                # Prüfe ob Tageslimit erreicht
                if not self.can_post_today():
                    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                    wait_seconds = (tomorrow - datetime.now()).total_seconds()
                    hours_to_wait = int(wait_seconds // 3600)
                    print(f"\n✅ [{current_time}] Tagesziel erreicht! Warte {hours_to_wait}h")
                    time.sleep(3600)
                    continue
                
                # Prüfe ob in aktiver Zeit
                if current_hour < start_hour or current_hour >= end_hour:
                    print(f"\n😴 [{current_time}] Außerhalb der aktiven Zeit...")
                    time.sleep(3600)
                    continue
                
                # Mindestabstand zwischen Posts
                if last_post_time:
                    time_since_last = (datetime.now() - last_post_time).total_seconds()
                    min_wait = random.randint(1800, 7200)  # 30 Min - 2 Stunden
                    if time_since_last < min_wait:
                        wait_time = int(min_wait - time_since_last)
                        print(f"\n⏳ Warte noch {wait_time//60} Minuten bis zum nächsten Post...")
                        time.sleep(wait_time)
                        continue
                
                # Erstelle Post
                post = self.get_random_post()
                if post:
                    print(f"\n📝 POST #{session_count + 1}:")
                    print(f"Titel: {post.get('title', '')[:80]}")
                    print(f"Subreddit: r/{post.get('subreddit', 'unbekannt')}")
                    
                    if self.create_post(post, dry_run=False):
                        session_count += 1
                        last_post_time = datetime.now()
                
                # Wartezeit bis zur nächsten Prüfung
                wait_minutes = random.randint(30, 90)
                print(f"\n⏰ Warte {wait_minutes} Minuten bis zur nächsten Prüfung...")
                time.sleep(wait_minutes * 60)
                
        except KeyboardInterrupt:
            current_count = self.get_today_count()
            print(f"\n\n👋 Loop beendet")
            print(f"📊 Heute erstellt: {current_count}/{self.daily_target} Posts")
            print(f"   Sessions: {session_count}")

def main():
    """Hauptfunktion mit Menü"""
    bot = PostBot()
    
    print("\n🤖 Reddit Post Bot - Verbesserte Version")
    print("="*50)
    print("Was möchtest du tun?")
    print("1. 📮 Einzelnen Post erstellen")
    print("2. 🔄 Automatischer Loop (1-4 Posts/Tag)")
    print("3. 📊 Statistiken anzeigen")
    print("4. 🎲 Zufälligen Post anzeigen")
    
    choice = input("\nAuswahl (1-4): ").strip()
    
    if choice == "1":
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
    
    elif choice == "2":
        # Automatischer Loop
        print("\n🔄 AUTOMATISCHER LOOP")
        print(f"• Tagesziel: {bot.daily_target} Posts")
        print(f"• Heute bereits: {bot.get_today_count()} Posts")
        print("• Aktiv von 10:00 - 22:00 Uhr")
        
        confirm = input("\n⚠️ Posts werden auf Reddit erstellt! Fortfahren? (j/n): ").strip().lower()
        if confirm in ['j', 'ja', 'yes', 'y']:
            bot.run_auto_loop(start_hour=10, end_hour=22)
        else:
            print("❌ Abgebrochen")
    
    elif choice == "3":
        # Statistiken
        print(f"\n📊 STATISTIKEN:")
        print(f"Posts gesamt: {len(bot.posts)}")
        print(f"Bereits gepostet: {len(bot.posted_posts)}")
        print(f"Verfügbar: {len(bot.posts) - len(bot.posted_posts)}")
        print(f"Heutiges Ziel: {bot.daily_target} Posts")
        print(f"Heute erstellt: {bot.get_today_count()}")
    
    elif choice == "4":
        # Zufälliger Post anzeigen
        post = bot.get_random_post()
        if post:
            print(f"\n📝 ZUFÄLLIGER POST:")
            print(f"Titel: {post.get('title', 'Kein Titel')}")
            print(f"Subreddit: r/{post.get('subreddit', 'unbekannt')}")
            if post.get('alternative_subreddits'):
                print(f"Alternativen: {', '.join(['r/'+s for s in post['alternative_subreddits'][:5]])}")
            print(f"Score: {post.get('score', 0):,}")
            
            if post.get('selftext'):
                print(f"\nText-Vorschau: {post.get('selftext', '')[:300]}...")
            elif post.get('url'):
                print(f"\nURL: {post.get('url')}")

if __name__ == "__main__":
    main()