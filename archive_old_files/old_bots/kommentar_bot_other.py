#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Kommentare Bot - PythonAnywhere Version mit hardcoded Credentials
WARNUNG: Automatisiertes Posten verstößt gegen Reddit ToS!
"""

import json
import random
import time
import requests
from pathlib import Path
import praw
import re
import base64
from io import BytesIO
from PIL import Image
import urllib.request

class KommentareBot:
    def __init__(self):
        self.base_dir = Path("/home/GoodValuable4401/Reddit/data_all")
        self.posts_dir = self.base_dir / "Posts"
        self.comments_dir = self.base_dir / "Comments"
        self.posts = []
        self.comments = []
        self._load_data()
        self._load_subreddits()
        
        # Track bereits kommentierte Posts
        self.commented_posts = set()
        self._load_commented_history()
        
        # Tägliches Kommentar-Tracking
        self.daily_comments = {}
        self.daily_target = None  # Wird täglich zufällig zwischen 5-20 gesetzt
        self._load_daily_stats()
        
        # OpenRouter API Konfiguration - HARDCODED
        self.openrouter_api_key = "YOUR_OPENROUTER_API_KEY_HERE"  # Hier deinen OpenRouter API Key eintragen
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Reddit API Konfiguration - HARDCODED
        self._init_reddit_connection()
        
        # Lade Benutzer aus otherUser.txt
        self.users_to_process = self._load_users_from_file()
    
    def _load_users_from_file(self):
        """Lädt Benutzernamen aus otherUser.txt"""
        users = []
        user_file = Path("/home/GoodValuable4401/Reddit/otherUser.txt")
        
        if user_file.exists():
            try:
                with open(user_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):  # Ignoriere leere Zeilen und Kommentare
                            users.append(line)
                print(f"✅ {len(users)} Benutzer aus otherUser.txt geladen")
            except Exception as e:
                print(f"⚠️ Fehler beim Laden der Benutzer: {e}")
        else:
            print(f"⚠️ otherUser.txt nicht gefunden bei: {user_file}")
        
        return users
    
    def _init_reddit_connection(self):
        """Initialisiert die Reddit-Verbindung mit hardcoded Credentials"""
        try:
            # HARDCODED CREDENTIALS für PythonAnywhere
            self.reddit = praw.Reddit(
                client_id="YOUR_CLIENT_ID_HERE",  # Hier deine Client ID eintragen
                client_secret="YOUR_CLIENT_SECRET_HERE",  # Hier deinen Client Secret eintragen
                user_agent="KommentareBot/1.0 by GoodValuable4401",
                username="GoodValuable4401",
                password="UPS2021*",
                ratelimit_seconds=300  # Wartet automatisch bei Rate Limits
            )
            # Test der Verbindung
            _ = self.reddit.user.me()
            print(f"✅ Reddit-Verbindung erfolgreich hergestellt als u/GoodValuable4401")
        except Exception as e:
            print(f"⚠️ Reddit-Verbindung fehlgeschlagen: {e}")
            print("   Versuche es später erneut...")
        
        # Natürliche Variationen für Kommentare
        self.casual_starters = [
            "oh man,", "honestly", "tbh", "ngl", "wait", "okay so",
            "bruh", "yo", "damn", "holy shit", "lol", "lmao",
            "literally", "actually", "fr fr", "no cap", "lowkey"
        ]
        
        self.casual_endings = [
            "tho", "though", "lol", "lmao", "haha", "fr",
            "ngl", "imo", "tbh", "idk", "rn", "atm"
        ]
        
        self.typos = {
            "the": ["teh", "th", "hte"],
            "and": ["adn", "nad", "an"],
            "you": ["u", "yuo", "yu"],
            "your": ["ur", "yuor", "yor"],
            "because": ["bc", "cuz", "cause", "becuase"],
            "definitely": ["definately", "defiantly", "def"],
            "probably": ["prolly", "probs", "probly"],
            "really": ["rly", "realy", "rlly"],
            "though": ["tho", "tough", "thou"],
            "with": ["w/", "wit", "wth"],
            "what": ["wat", "wut", "waht"],
            "that": ["taht", "tht", "dat"],
            "their": ["thier", "there"],
            "they're": ["theyre", "there", "their"],
            "it's": ["its"],
            "you're": ["your", "ur"]
        }
    
    def _load_data(self):
        """Lädt alle Kommentare aus data_all Struktur"""
        print(f"📂 Lade Daten von: {self.base_dir}")
        
        # Kommentare laden (falls vorhanden)
        if self.comments_dir.exists():
            print(f"  📁 Lade Kommentare aus: {self.comments_dir.name}")
            for comment_folder in sorted(self.comments_dir.iterdir()):
                if comment_folder.is_dir():
                    json_file = comment_folder / "comment_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.comments.append(data)
        
        # Posts laden aus data_all Struktur
        if self.posts_dir.exists():
            print(f"  📁 Lade Posts aus: {self.posts_dir.name}")
            for post_folder in sorted(self.posts_dir.iterdir()):
                if post_folder.is_dir():  # Alle Ordner laden
                    json_file = post_folder / "post_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.posts.append(data)
        
        print(f"✅ Geladen: {len(self.comments)} Kommentare, {len(self.posts)} Posts")
        print(f"👥 Benutzer in otherUser.txt: {len(getattr(self, 'users_to_process', []))}")
    
    def _load_subreddits(self):
        """Lädt alle Target-Subreddits aus den Dateien"""
        self.all_subreddits = []
        
        # Lade aus target_subreddits.txt
        target_file = Path("/home/GoodValuable4401/Reddit/target_subreddits.txt")
        if target_file.exists():
            with open(target_file, 'r', encoding='utf-8') as f:
                for line in f:
                    sub = line.strip()
                    if sub and not sub.startswith('#'):
                        self.all_subreddits.append(sub)
        
        # Lade aus target_subreddits_extended.txt (ohne Duplikate)
        extended_file = Path("/home/GoodValuable4401/Reddit/target_subreddits_extended.txt")
        if extended_file.exists():
            with open(extended_file, 'r', encoding='utf-8') as f:
                for line in f:
                    sub = line.strip()
                    if sub and not sub.startswith('#') and sub not in self.all_subreddits:
                        self.all_subreddits.append(sub)
        
        # Entferne Duplikate und sortiere
        self.all_subreddits = sorted(list(set(self.all_subreddits)))
        print(f"📋 Geladen: {len(self.all_subreddits)} Subreddits")
    
    def _load_commented_history(self):
        """Lädt Historie der bereits kommentierten Posts"""
        history_file = Path("/home/GoodValuable4401/Reddit/commented_posts.json")
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.commented_posts = set(data.get('posts', []))
                    print(f"📝 Historie geladen: {len(self.commented_posts)} bereits kommentierte Posts")
            except:
                self.commented_posts = set()
        else:
            self.commented_posts = set()
    
    def _save_commented_history(self):
        """Speichert Historie der kommentierten Posts"""
        history_file = Path("/home/GoodValuable4401/Reddit/commented_posts.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump({'posts': list(self.commented_posts)}, f, indent=2)
    
    def _load_daily_stats(self):
        """Lädt tägliche Kommentar-Statistiken"""
        from datetime import datetime
        stats_file = Path("/home/GoodValuable4401/Reddit/daily_comment_stats.json")
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.daily_comments = json.load(f)
            except:
                self.daily_comments = {}
        else:
            self.daily_comments = {}
        
        # Prüfe ob heute schon ein Target gesetzt wurde
        today = datetime.now().strftime("%Y-%m-%d")
        if today in self.daily_comments:
            self.daily_target = self.daily_comments[today].get('target')
            # Falls target nicht gesetzt oder None, setze neues Ziel
            if self.daily_target is None:
                self.daily_target = random.randint(5, 20)
                self.daily_comments[today]['target'] = self.daily_target
                self._save_daily_stats()
                print(f"🎯 Tagesziel korrigiert: {self.daily_target} Kommentare")
            elif self.daily_target == 0:
                print(f"🚫 Heute ist ein Pausentag - keine Kommentare")
            else:
                print(f"📊 Heutiges Ziel: {self.daily_target} Kommentare")
                print(f"   Bereits erstellt: {self.daily_comments[today].get('count', 0)}")
        else:
            # 20% Chance für einen Pausentag (Tag überspringen)
            if random.random() < 0.2:
                self.daily_target = 0
                self.daily_comments[today] = {
                    'target': 0,
                    'count': 0,
                    'comments': [],
                    'skip_day': True
                }
                print(f"😴 Heute ist ein Pausentag - keine Kommentare geplant")
            else:
                # Setze neues tägliches Ziel
                self.daily_target = random.randint(5, 20)
                self.daily_comments[today] = {
                    'target': self.daily_target,
                    'count': 0,
                    'comments': []
                }
                print(f"🎯 Neues Tagesziel gesetzt: {self.daily_target} Kommentare")
            self._save_daily_stats()
        
        # Finale Sicherheitsprüfung
        if self.daily_target is None:
            self.daily_target = random.randint(5, 20)
            print(f"🎯 Standard-Tagesziel gesetzt: {self.daily_target} Kommentare")
    
    def _save_daily_stats(self):
        """Speichert tägliche Kommentar-Statistiken"""
        stats_file = Path("/home/GoodValuable4401/Reddit/daily_comment_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.daily_comments, f, indent=2, ensure_ascii=False)
    
    def get_today_comment_count(self):
        """Gibt zurück wie viele Kommentare heute bereits erstellt wurden"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        return self.daily_comments.get(today, {}).get('count', 0)
    
    def can_comment_today(self):
        """Prüft ob heute noch Kommentare erstellt werden können"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Stelle sicher dass heute ein Eintrag existiert
        if today not in self.daily_comments:
            self.daily_target = random.randint(5, 20)
            self.daily_comments[today] = {
                'target': self.daily_target,
                'count': 0,
                'comments': []
            }
            self._save_daily_stats()
        
        current_count = self.daily_comments[today].get('count', 0)
        target = self.daily_comments[today].get('target', self.daily_target)
        
        if current_count >= target:
            print(f"⚠️ Tageslimit erreicht: {current_count}/{target} Kommentare")
            return False
        return True
    
    def increment_daily_count(self, comment_info=None):
        """Erhöht den täglichen Kommentar-Zähler"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.daily_comments:
            self.daily_comments[today] = {
                'target': self.daily_target or random.randint(5, 20),
                'count': 0,
                'comments': []
            }
        
        self.daily_comments[today]['count'] += 1
        
        if comment_info:
            self.daily_comments[today]['comments'].append({
                'time': datetime.now().isoformat(),
                'post_id': comment_info.get('post_id'),
                'subreddit': comment_info.get('subreddit'),
                'comment_preview': comment_info.get('comment', '')[:100]
            })
        
        self._save_daily_stats()
        
        current = self.daily_comments[today]['count']
        target = self.daily_comments[today]['target']
        print(f"📈 Tagesfortschritt: {current}/{target} Kommentare")
    
    def process_users(self):
        """Verarbeitet die Benutzer aus otherUser.txt"""
        if not self.users_to_process:
            print("⚠️ Keine Benutzer zum Verarbeiten gefunden")
            return
        
        print(f"\n👥 Verarbeite {len(self.users_to_process)} Benutzer:")
        for user in self.users_to_process:
            print(f"  • {user}")
        
        # Hier kannst du die Logik für die Benutzerverarbeitung hinzufügen
        # z.B. Posts von diesen Benutzern laden, analysieren, etc.
    
    def check_if_already_commented(self, post_id):
        """Prüft ob der Bot bereits auf diesem Post kommentiert hat"""
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)
            
            # Prüfe ob unser Bot bereits kommentiert hat
            for comment in submission.comments.list():
                if comment.author and comment.author.name == "GoodValuable4401":
                    return True
            return False
        except:
            return False
    
    def verify_post_exists(self, post_id):
        """Prüft ob ein Post wirklich auf Reddit existiert"""
        try:
            submission = self.reddit.submission(id=post_id)
            # Versuche auf Post-Daten zuzugreifen
            _ = submission.title
            
            # Prüfe ob Post entfernt wurde
            if submission.removed_by_category:
                print(f"  ⚠️ Post wurde entfernt: {submission.removed_by_category}")
                return False
            
            # Prüfe ob Author gelöscht
            if submission.author is None:
                print(f"  ⚠️ Post-Author wurde gelöscht")
                return False
            
            return True
        except Exception as e:
            print(f"  ❌ Post existiert nicht oder ist nicht zugänglich: {str(e)[:50]}")
            return False
    
    def add_natural_variations(self, text):
        """Fügt natürliche Variationen zum Text hinzu"""
        
        # IMMER Kleinschreibung am Anfang (außer "I")
        if len(text) > 0 and not text.startswith('I '):
            text = text[0].lower() + text[1:]
        
        # Casual Starter hinzufügen (40% Chance)
        if random.random() < 0.4:
            starter = random.choice(self.casual_starters)
            text = f"{starter} {text}"
        
        # Entferne zu viele Satzzeichen am Ende
        text = text.rstrip('.,!?') + text[-1] if text and text[-1] in '.,!?' else text
        
        # Punkte oft weglassen oder durch ... ersetzen (60% Chance)
        if random.random() < 0.6:
            if text.endswith('.'):
                text = text[:-1]  # Punkt weglassen
            elif random.random() < 0.5:
                text = text.replace('. ', '... ')
        
        # Ausrufezeichen komplett entfernen (meist)
        if '!' in text and random.random() < 0.8:
            text = text.replace('!', '')
        
        # Casual Ending hinzufügen (35% Chance)
        if random.random() < 0.35:
            ending = random.choice(self.casual_endings)
            # Kein Punkt vor casual endings
            text = text.rstrip('.,!?') + f" {ending}"
        
        # Mehr Tippfehler (15% Chance pro Wort)
        words = text.split()
        new_words = []
        for word in words:
            if random.random() < 0.15 and word.lower() in self.typos:
                new_words.append(random.choice(self.typos[word.lower()]))
            else:
                new_words.append(word)
        text = ' '.join(new_words)
        
        # Manchmal keine Großschreibung nach Punkt
        text = text.replace('. I', '. i') if random.random() < 0.7 else text
        text = text.replace('. The', '. the') if random.random() < 0.7 else text
        
        # Apostrophe oft weglassen
        if random.random() < 0.5:
            text = text.replace("don't", "dont")
            text = text.replace("can't", "cant")
            text = text.replace("won't", "wont")
            text = text.replace("I'm", "im")
        
        return text
    
    def download_image(self, url):
        """Lädt ein Bild von einer URL herunter und konvertiert es zu base64"""
        try:
            # Download image
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req)
            img_data = response.read()
            
            # Convert to base64
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # Detect image type
            if url.lower().endswith('.png'):
                mime_type = "image/png"
            elif url.lower().endswith('.gif'):
                mime_type = "image/gif"
            else:
                mime_type = "image/jpeg"
            
            return f"data:{mime_type};base64,{img_base64}"
        except Exception as e:
            print(f"❌ Fehler beim Bilddownload: {e}")
            return None
    
    def save_generated_comment(self, comment_data):
        """Speichert generierten Kommentar in organisiertem Ordner"""
        from datetime import datetime
        
        # Erstelle Ordnerstruktur: generated_comments/YYYY-MM/DD/
        base_dir = Path("/home/GoodValuable4401/Reddit/generated_comments")
        date_now = datetime.now()
        year_month = date_now.strftime("%Y-%m")
        day = date_now.strftime("%d")
        
        comment_dir = base_dir / year_month / day
        comment_dir.mkdir(parents=True, exist_ok=True)
        
        # Erstelle eindeutigen Dateinamen
        timestamp = date_now.strftime("%H%M%S")
        subreddit = comment_data.get('subreddit', 'unknown')
        filename = f"comment_{timestamp}_{subreddit}.json"
        
        # Füge Zeitstempel hinzu
        comment_data['created_at'] = date_now.isoformat()
        comment_data['date'] = date_now.strftime("%Y-%m-%d")
        comment_data['time'] = date_now.strftime("%H:%M:%S")
        
        # Speichere Kommentar
        file_path = comment_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(comment_data, f, indent=2, ensure_ascii=False)
        
        # Erstelle auch eine Textvorschau
        preview_file = comment_dir / f"preview_{timestamp}_{subreddit}.txt"
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write(f"Subreddit: r/{subreddit}\n")
            f.write(f"Post: {comment_data.get('post_title', '')[:100]}...\n")
            f.write(f"Score: {comment_data.get('post_score', 0)}\n")
            f.write(f"Zeit: {date_now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"\nKommentar:\n")
            f.write(comment_data.get('comment', ''))
        
        return file_path
    
    def show_statistics(self):
        """Zeigt Statistiken über die geladenen Daten"""
        print("\n📊 STATISTIKEN:")
        print(f"Posts gesamt: {len(self.posts)}")
        print(f"Kommentare gesamt: {len(self.comments)}")
        print(f"Benutzer in otherUser.txt: {len(self.users_to_process)}")
        print(f"Subreddits verfügbar: {len(self.all_subreddits)}")
        
        if self.posts:
            avg_score = sum(p.get('score', 0) for p in self.posts) / len(self.posts)
            print(f"Durchschnittlicher Post-Score: {avg_score:.0f}")
            
            # Top Posts nach Score
            sorted_posts = sorted(self.posts, key=lambda x: x.get('score', 0), reverse=True)
            print(f"\n🏆 Top 5 Posts nach Score:")
            for i, post in enumerate(sorted_posts[:5], 1):
                print(f"  {i}. Score {post.get('score', 0):,} - {post.get('title', '')[:60]}...")
        
        if self.comments:
            avg_comment_score = sum(c.get('score', 0) for c in self.comments) / len(self.comments)
            print(f"\nDurchschnittlicher Kommentar-Score: {avg_comment_score:.0f}")

def main():
    """Hauptfunktion"""
    bot = KommentareBot()
    
    print("\n🤖 Kommentare Bot - PythonAnywhere Edition")
    print("⚠️  NUR FÜR BILDUNGSZWECKE!")
    print("="*50)
    print("Was möchtest du tun?")
    print("1. 📊 Statistiken anzeigen")
    print("2. 👥 Benutzer aus otherUser.txt verarbeiten")
    print("3. 📋 Zeige alle Subreddits")
    print("4. 📈 Tagesstatistiken anzeigen")
    
    choice = input("\nAuswahl (1-4): ").strip()
    
    if choice == "1":
        bot.show_statistics()
        
    elif choice == "2":
        bot.process_users()
        
    elif choice == "3":
        # Zeige alle Subreddits
        print(f"\n📋 ALLE {len(bot.all_subreddits)} VERFÜGBAREN SUBREDDITS:")
        print("="*60)
        
        # Gruppiere nach Kategorien
        categories = {
            'ADHD': [],
            'Mental Health': [],
            'Productivity': [],
            'Support': [],
            'Creative': [],
            'Career': [],
            'Tools': [],
            'Other': []
        }
        
        for sub in bot.all_subreddits:
            sub_lower = sub.lower()
            if 'adhd' in sub_lower or 'add' in sub_lower:
                categories['ADHD'].append(sub)
            elif any(word in sub_lower for word in ['mental', 'anxiety', 'depression', 'therapy', 'bipolar', 'ocd', 'ptsd']):
                categories['Mental Health'].append(sub)
            elif any(word in sub_lower for word in ['productivity', 'discipline', 'organized', 'habit']):
                categories['Productivity'].append(sub)
            elif any(word in sub_lower for word in ['support', 'help', 'kind', 'friend']):
                categories['Support'].append(sub)
            elif any(word in sub_lower for word in ['art', 'write', 'creative', 'craft', 'sketch']):
                categories['Creative'].append(sub)
            elif any(word in sub_lower for word in ['job', 'career', 'work', 'entrepreneur']):
                categories['Career'].append(sub)
            elif any(word in sub_lower for word in ['notion', 'todoist', 'obsidian', 'app']):
                categories['Tools'].append(sub)
            else:
                categories['Other'].append(sub)
        
        for category, subs in categories.items():
            if subs:
                print(f"\n🏷️ {category} ({len(subs)}):")
                for sub in sorted(subs):
                    print(f"  • r/{sub}")
                    
    elif choice == "4":
        # Zeige Tagesstatistiken
        print(f"\n📈 TAGESSTATISTIKEN:")
        print(f"Heutiges Ziel: {bot.daily_target} Kommentare")
        print(f"Bereits erstellt: {bot.get_today_comment_count()}")
        
        if bot.daily_target == 0:
            print("\n😴 Heute ist ein Pausentag")
        elif bot.can_comment_today():
            remaining = bot.daily_target - bot.get_today_comment_count()
            print(f"Noch zu erstellen: {remaining}")
        else:
            print("\n✅ Tagesziel erreicht!")
    
    else:
        print("Ungültige Auswahl")

if __name__ == "__main__":
    main()