#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Combined Bot - PythonAnywhere Version mit hardcoded Credentials
Posts und Kommentare kombiniert
BILDUNGSZWECKE ONLY - Kein automatisches Posten!
"""

import json
import random
import time
from pathlib import Path
import urllib.request
import os
import mimetypes
import praw
import requests
import base64
import re

class CombinedBot:
    def __init__(self, use_config_file=False):
        self.base_dir = Path("/home/lucawahl/Reddit/data_all")
        self.posts_dir = self.base_dir / "Posts"
        self.comments_dir = self.base_dir / "Comments"
        self.posts = []
        self.comments = []
        
        # Lade oder erstelle Konfiguration
        self.config_file = Path("/home/lucawahl/Reddit/bot_config.json")
        self.config = self._load_or_create_config(use_config_file)
        
        self._load_data()
        self._load_subreddits()
        
        # Tägliches Post-Tracking
        self.daily_posts = {}
        self._load_daily_stats()
        self.daily_post_target = None  # Wird täglich zufällig zwischen 1-4 gesetzt
        
        # Tägliches Kommentar-Tracking
        self.daily_comments = {}
        self.daily_comment_target = None  # Wird täglich zufällig zwischen 5-20 gesetzt
        self._load_comment_daily_stats()
        
        # Track bereits gepostete Posts und Kommentare
        self.posted_posts = set()
        self._load_posted_history()
        self.commented_posts = set()
        self._load_commented_history()
        
        # OpenRouter API für Kommentare
        self.openrouter_api_key = self.config.get("openrouter_api_key", "")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Reddit API Konfiguration
        self._init_reddit_connection()
        
        # Lade Benutzer aus otherUser.txt
        self.users_to_process = self._load_users_from_file()
        
        # Viral Post Tracking für gestern gepostete Beiträge
        self.viral_posts_file = Path("/home/lucawahl/Reddit/viral_posts_tracking.json")
        self.viral_posts = self._load_viral_tracking()
        
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
    
    def _load_or_create_config(self, use_config_file):
        """Lädt Konfiguration aus Datei oder nutzt Hardcoded-Werte"""
        if use_config_file and self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print("✅ Konfiguration aus bot_config.json geladen")
                    return config
            except Exception as e:
                print(f"⚠️ Fehler beim Laden der Konfiguration: {e}")
        
        # Hardcoded Defaults
        return {
            "client_id": "YOUR_CLIENT_ID_HERE",
            "client_secret": "YOUR_CLIENT_SECRET_HERE",
            "username": "GoodValuable4401",
            "password": "UPS2021*",
            "user_agent": "CombinedBot/1.0 by GoodValuable4401",
            "openrouter_api_key": ""
        }
    
    def save_config(self):
        """Speichert die aktuelle Konfiguration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            print(f"✅ Konfiguration gespeichert in: {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Speichern der Konfiguration: {e}")
            return False
    
    def update_credentials(self):
        """Interaktive Eingabe der API-Credentials"""
        print("\n🔑 API CREDENTIALS EINGEBEN")
        print("="*60)
        print("Gib die Daten ein (Enter überspringt den Wert):\n")
        
        # Reddit API
        print("📱 REDDIT API:")
        current_id = self.config.get('client_id', '')
        if current_id and current_id != 'YOUR_CLIENT_ID_HERE':
            display_id = f"{current_id[:10]}..." if len(current_id) > 10 else current_id
        else:
            display_id = "nicht gesetzt"
        client_id = input(f"Client ID [{display_id}]: ").strip()
        if client_id:
            self.config['client_id'] = client_id
        
        current_secret = self.config.get('client_secret', '')
        if current_secret and current_secret != 'YOUR_CLIENT_SECRET_HERE':
            display_secret = '*' * 10
        else:
            display_secret = "nicht gesetzt"
        client_secret = input(f"Client Secret [{display_secret}]: ").strip()
        if client_secret:
            self.config['client_secret'] = client_secret
        
        username = input(f"Username [{self.config.get('username', 'nicht gesetzt')}]: ").strip()
        if username:
            self.config['username'] = username
        
        current_pw = self.config.get('password', '')
        if current_pw:
            display_pw = '*' * min(len(current_pw), 10)
        else:
            display_pw = "nicht gesetzt"
        password = input(f"Password [{display_pw}]: ").strip()
        if password:
            self.config['password'] = password
        
        user_agent = input(f"User Agent [{self.config.get('user_agent', '')}]: ").strip()
        if user_agent:
            self.config['user_agent'] = user_agent
        
        # OpenRouter API (optional)
        print("\n🤖 OPENROUTER API (Optional für KI-Kommentare):")
        print("   ℹ️ Hinweis: Für intelligente Kommentare benötigt. Kostenlos auf openrouter.ai")
        print("   Enter drücken zum Überspringen")
        openrouter_key = input(f"OpenRouter API Key [{'*' * 10 if self.config.get('openrouter_api_key') else 'nicht gesetzt'}]: ").strip()
        if openrouter_key:
            self.config['openrouter_api_key'] = openrouter_key
            self.openrouter_api_key = openrouter_key
        else:
            print("   ⚠️ Ohne OpenRouter Key werden nur einfache Kommentare generiert")
        
        # Speichern?
        save = input("\n💾 Konfiguration speichern? (j/n): ").strip().lower()
        if save in ['j', 'ja', 'yes', 'y']:
            if self.save_config():
                print("✅ Konfiguration erfolgreich gespeichert!")
                
                # Reddit-Verbindung neu initialisieren
                print("\n🔄 Teste Reddit-Verbindung mit neuen Daten...")
                self._init_reddit_connection()
            else:
                print("❌ Speichern fehlgeschlagen")
        else:
            print("ℹ️ Konfiguration nur für diese Session aktiv")
    
    def _load_users_from_file(self):
        """Lädt Benutzernamen aus otherUser.txt"""
        users = []
        user_file = Path("/home/lucawahl/Reddit/otherUser.txt")
        
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
            # Erstelle Beispieldatei
            try:
                with open(user_file, 'w', encoding='utf-8') as f:
                    f.write("# Benutzernamen - einer pro Zeile\n")
                    f.write("# Zeilen mit # werden ignoriert\n")
                    f.write("beispiel_user1\n")
                    f.write("beispiel_user2\n")
                print(f"📝 Beispiel otherUser.txt erstellt bei: {user_file}")
            except:
                pass
        
        return users
    
    def _init_reddit_connection(self):
        """Initialisiert die Reddit-Verbindung mit Credentials aus Config"""
        try:
            # Verwende Credentials aus Config
            self.reddit = praw.Reddit(
                client_id=self.config.get("client_id"),
                client_secret=self.config.get("client_secret"),
                user_agent=self.config.get("user_agent", "CombinedBot/1.0"),
                username=self.config.get("username"),
                password=self.config.get("password"),
                ratelimit_seconds=300
            )
            # Test der Verbindung
            user = self.reddit.user.me()
            print(f"✅ Reddit-Verbindung hergestellt als u/{user.name}")
        except Exception as e:
            print(f"⚠️ Reddit-Verbindung fehlgeschlagen: {e}")
            print("   Tipp: Nutze Option 9 im Hauptmenü um API-Daten einzugeben")
    
    def _load_data(self):
        """Lädt alle Posts und Kommentare aus dem data_all Ordner"""
        print(f"📂 Lade Daten von: {self.base_dir}")
        
        # Posts laden direkt aus Posts Ordner (data_all Struktur)
        if self.posts_dir.exists():
            print(f"  📁 Lade Posts aus: {self.posts_dir.name}")
            for post_folder in sorted(self.posts_dir.iterdir()):
                if post_folder.is_dir():  # Alle Ordner laden
                    json_file = post_folder / "post_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.posts.append(data)
        
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
        
        print(f"✅ Geladen: {len(self.posts)} Posts, {len(self.comments)} Kommentare")
    
    def _load_subreddits(self):
        """Lädt alle Target-Subreddits aus den Dateien und entfernt gebannte"""
        self.all_subreddits = []
        self.blacklisted_subreddits = []
        
        # Lade Blacklist zuerst
        blacklist_file = Path("/home/lucawahl/Reddit/blacklist_subreddits.txt")
        if blacklist_file.exists():
            with open(blacklist_file, 'r', encoding='utf-8') as f:
                for line in f:
                    sub = line.strip()
                    if sub and not sub.startswith('#'):
                        self.blacklisted_subreddits.append(sub.lower())
            print(f"🚫 Blacklist geladen: {len(self.blacklisted_subreddits)} gesperrte Subreddits")
        
        # Lade aus target_subreddits.txt
        target_file = Path("/home/lucawahl/Reddit/target_subreddits.txt")
        if target_file.exists():
            with open(target_file, 'r', encoding='utf-8') as f:
                for line in f:
                    sub = line.strip()
                    if sub and not sub.startswith('#'):
                        # Prüfe ob Subreddit auf Blacklist
                        if sub.lower() not in self.blacklisted_subreddits:
                            self.all_subreddits.append(sub)
        
        # Lade aus target_subreddits_extended.txt (ohne Duplikate)
        extended_file = Path("/home/lucawahl/Reddit/target_subreddits_extended.txt")
        if extended_file.exists():
            with open(extended_file, 'r', encoding='utf-8') as f:
                for line in f:
                    sub = line.strip()
                    if sub and not sub.startswith('#') and sub not in self.all_subreddits:
                        # Prüfe ob Subreddit auf Blacklist
                        if sub.lower() not in self.blacklisted_subreddits:
                            self.all_subreddits.append(sub)
        
        # Entferne Duplikate und sortiere
        self.all_subreddits = sorted(list(set(self.all_subreddits)))
        print(f"📋 Geladen: {len(self.all_subreddits)} Subreddits (nach Blacklist-Filter)")
    
    def _load_daily_stats(self):
        """Lädt tägliche Post-Statistiken"""
        from datetime import datetime
        stats_file = Path("/home/lucawahl/Reddit/daily_post_stats.json")
        
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
            self.daily_post_target = self.daily_posts[today].get('target')
            # Falls target nicht gesetzt oder None, setze neues Ziel
            if self.daily_post_target is None:
                self.daily_post_target = random.randint(1, 4)
                self.daily_posts[today]['target'] = self.daily_post_target
                self._save_daily_stats()
                print(f"🎯 Post-Tagesziel korrigiert: {self.daily_post_target} Posts")
            elif self.daily_post_target == 0:
                print(f"🚫 Heute ist ein Pausentag - keine Posts")
            else:
                print(f"📊 Heutiges Post-Ziel: {self.daily_post_target} Posts")
                print(f"   Bereits erstellt: {self.daily_posts[today].get('count', 0)}")
        else:
            # 15% Chance für einen Pausentag (0 Posts)
            if random.random() < 0.15:
                self.daily_post_target = 0
                self.daily_posts[today] = {
                    'target': 0,
                    'count': 0,
                    'posts': [],
                    'skip_day': True
                }
                print(f"😴 Heute ist ein Pausentag - keine Posts geplant")
            else:
                # Setze neues tägliches Ziel (1-4 Posts)
                self.daily_post_target = random.randint(1, 4)
                self.daily_posts[today] = {
                    'target': self.daily_post_target,
                    'count': 0,
                    'posts': []
                }
                print(f"🎯 Neues Post-Tagesziel gesetzt: {self.daily_post_target} Posts")
            self._save_daily_stats()
    
    def _save_daily_stats(self):
        """Speichert tägliche Post-Statistiken"""
        stats_file = Path("/home/lucawahl/Reddit/daily_post_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.daily_posts, f, indent=2, ensure_ascii=False)
    
    def _load_comment_daily_stats(self):
        """Lädt tägliche Kommentar-Statistiken"""
        from datetime import datetime
        stats_file = Path("/home/lucawahl/Reddit/daily_comment_stats.json")
        
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
            self.daily_comment_target = self.daily_comments[today].get('target')
            # Falls target nicht gesetzt oder None, setze neues Ziel
            if self.daily_comment_target is None:
                self.daily_comment_target = random.randint(3, 7)
                self.daily_comments[today]['target'] = self.daily_comment_target
                self._save_comment_daily_stats()
                print(f"🎯 Kommentar-Tagesziel korrigiert: {self.daily_comment_target} Kommentare")
            elif self.daily_comment_target == 0:
                # Falls irgendwie 0, setze neues Ziel
                self.daily_comment_target = random.randint(3, 7)
                self.daily_comments[today]['target'] = self.daily_comment_target
                self._save_comment_daily_stats()
                print(f"🎯 Kommentar-Tagesziel korrigiert: {self.daily_comment_target} Kommentare")
            else:
                print(f"📊 Heutiges Kommentar-Ziel: {self.daily_comment_target} Kommentare")
                print(f"   Bereits erstellt: {self.daily_comments[today].get('count', 0)}")
        else:
            # Setze IMMER ein tägliches Ziel (5-20 Kommentare, keine Pausentage)
            self.daily_comment_target = random.randint(3, 7)
            self.daily_comments[today] = {
                'target': self.daily_comment_target,
                'count': 0,
                'comments': []
            }
            print(f"🎯 Neues Kommentar-Tagesziel gesetzt: {self.daily_comment_target} Kommentare")
            self._save_comment_daily_stats()
        
        # Finale Sicherheitsprüfung
        if self.daily_comment_target is None or self.daily_comment_target == 0:
            self.daily_comment_target = random.randint(3, 7)
            print(f"🎯 Standard-Kommentar-Tagesziel gesetzt: {self.daily_comment_target} Kommentare")
    
    def _save_comment_daily_stats(self):
        """Speichert tägliche Kommentar-Statistiken"""
        stats_file = Path("/home/lucawahl/Reddit/daily_comment_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.daily_comments, f, indent=2, ensure_ascii=False)
    
    def _load_posted_history(self):
        """Lädt Historie der bereits geposteten Posts"""
        history_file = Path("/home/lucawahl/Reddit/posted_posts.json")
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
        history_file = Path("/home/lucawahl/Reddit/posted_posts.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump({'posts': list(self.posted_posts)}, f, indent=2)
    
    def _load_commented_history(self):
        """Lädt Historie der bereits kommentierten Posts"""
        history_file = Path("/home/lucawahl/Reddit/commented_posts.json")
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.commented_posts = set(data.get('posts', []))
                    print(f"📝 Kommentar-Historie geladen: {len(self.commented_posts)} bereits kommentierte Posts")
            except:
                self.commented_posts = set()
        else:
            self.commented_posts = set()
    
    def _save_commented_history(self):
        """Speichert Historie der kommentierten Posts"""
        history_file = Path("/home/lucawahl/Reddit/commented_posts.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump({'posts': list(self.commented_posts)}, f, indent=2)
    
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
        target = self.daily_posts[today].get('target', self.daily_post_target)
        
        if current_count >= target:
            print(f"⚠️ Post-Tageslimit erreicht: {current_count}/{target} Posts")
            return False
        return True
    
    def increment_daily_count(self, post_info=None):
        """Erhöht den täglichen Post-Zähler"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.daily_posts:
            self.daily_posts[today] = {
                'target': self.daily_post_target or random.randint(1, 4),
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
        print(f"📈 Post-Tagesfortschritt: {current}/{target} Posts")
    
    def increment_comment_daily_count(self, comment_info=None):
        """Erhöht den täglichen Kommentar-Zähler"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.daily_comments:
            self.daily_comments[today] = {
                'target': self.daily_comment_target or random.randint(3, 7),
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
        
        self._save_comment_daily_stats()
        
        current = self.daily_comments[today]['count']
        target = self.daily_comments[today]['target']
        print(f"📈 Kommentar-Tagesfortschritt: {current}/{target} Kommentare")
    
    def get_random_post(self):
        """Gibt einen zufälligen Post zurück und wählt ein ADHD-Subreddit als Ziel"""
        if self.posts:
            # Versuche einen noch nicht geposteten Post zu finden
            unposted = [p for p in self.posts if p.get('id') not in self.posted_posts]
            if unposted:
                post = random.choice(unposted)
            else:
                # Falls alle gepostet, nimm irgendeinen
                post = random.choice(self.posts)
            
            # IMMER ein ADHD-Subreddit als Ziel verwenden
            # Wähle basierend auf Post-Typ ein passendes ADHD-Subreddit
            title_lower = post.get('title', '').lower()
            
            # Kategorisiere ADHD-Subreddits für bessere Zuordnung (ohne gebannte)
            blacklist = getattr(self, 'blacklisted_subreddits', ['adhdwomen'])
            
            # Filtere gebannte Subreddits aus den Listen
            adhd_core = [s for s in ['ADHD', 'AdultADHD', 'ADHDUK', 'ADHDmemes', 'HowToADHD'] 
                        if s.lower() not in blacklist]
            adhd_productivity = [s for s in ['GetDisciplined', 'productivity', 'stopprocrastinating', 'bulletjournal', 'organization']
                               if s.lower() not in blacklist]
            adhd_mental = [s for s in ['mentalhealth', 'Anxiety', 'depression', 'therapy', 'selfcare']
                          if s.lower() not in blacklist]
            adhd_creative = [s for s in ['WritingPrompts', 'crafts', 'DIY', 'gardening', 'ArtTherapy']
                            if s.lower() not in blacklist]
            adhd_support = [s for s in ['KindVoice', 'needafriend', 'offmychest', 'CasualConversation']
                           if s.lower() not in blacklist]
            adhd_career = [s for s in ['ADHD_Programmers', 'ADHD_Entrepreneurs', 'adhd_college', 'careerguidance']
                          if s.lower() not in blacklist]
            
            # Wähle passende Kategorie basierend auf Keywords
            if any(word in title_lower for word in ['work', 'job', 'career', 'office', 'boss', 'colleague']):
                target_sub = random.choice(adhd_career)
            elif any(word in title_lower for word in ['sad', 'anxious', 'depressed', 'therapy', 'mental']):
                target_sub = random.choice(adhd_mental)
            elif any(word in title_lower for word in ['organize', 'plan', 'productive', 'focus', 'task']):
                target_sub = random.choice(adhd_productivity)
            elif any(word in title_lower for word in ['art', 'creative', 'made', 'built', 'drew']):
                target_sub = random.choice(adhd_creative)
            elif any(word in title_lower for word in ['help', 'support', 'need', 'advice', 'question']):
                target_sub = random.choice(adhd_support)
            else:
                # Default: Core ADHD subreddits
                target_sub = random.choice(adhd_core)
            
            print(f"   🎯 Post wird in r/{target_sub} gepostet (ADHD-fokussiert)")
            post['subreddit'] = target_sub
            
            return post
        return None
    
    def save_generated_post(self, post_data):
        """Speichert generierten Post in organisiertem Ordner"""
        from datetime import datetime
        
        # Erstelle Ordnerstruktur: generated_posts/YYYY-MM/DD/
        base_dir = Path("/home/lucawahl/Reddit/generated_posts")
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
            self.daily_comment_target = random.randint(3, 7)
            self.daily_comments[today] = {
                'target': self.daily_comment_target,
                'count': 0,
                'comments': []
            }
            self._save_comment_daily_stats()
        
        current_count = self.daily_comments[today].get('count', 0)
        target = self.daily_comments[today].get('target', self.daily_comment_target)
        
        if current_count >= target:
            print(f"⚠️ Kommentar-Tageslimit erreicht: {current_count}/{target} Kommentare")
            return False
        return True
    
    def add_natural_variations(self, text):
        """Fügt natürliche Variationen zum Text hinzu für Kommentare"""
        
        # Prüfe ob Text zu kurz ist
        if not text or len(text.strip()) < 5:
            # Generiere einen sicheren Fallback
            fallbacks = [
                "this is actually really interesting",
                "i never thought about it this way",
                "thanks for sharing this perspective",
                "this makes so much sense now",
                "wow i learned something new today"
            ]
            text = random.choice(fallbacks)
        
        # IMMER Kleinschreibung am Anfang (außer "I")
        if len(text) > 0 and not text.startswith('I '):
            text = text[0].lower() + text[1:]
        
        # Casual Starter hinzufügen (40% Chance)
        if random.random() < 0.4:
            starter = random.choice(self.casual_starters)
            text = f"{starter} {text}"
        
        # Entferne zu viele Satzzeichen am Ende (aber nur wenn Text lang genug)
        if len(text) > 1:
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
    
    def _load_viral_tracking(self):
        """Lädt Viral Post Tracking Daten"""
        if self.viral_posts_file.exists():
            try:
                with open(self.viral_posts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_viral_tracking(self):
        """Speichert Viral Post Tracking"""
        with open(self.viral_posts_file, 'w', encoding='utf-8') as f:
            json.dump(self.viral_posts, f, indent=2, ensure_ascii=False)
    
    def check_yesterdays_viral_posts(self):
        """Prüft Posts vom Vortag auf virale Aktivität"""
        from datetime import datetime, timedelta
        
        print("\n🔥 PRÜFE VIRALE POSTS VOM VORTAG")
        print("="*60)
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Hole Posts die gestern erstellt wurden
        if yesterday not in self.daily_posts:
            print("❌ Keine Posts vom Vortag gefunden")
            return []
        
        yesterdays_posts = self.daily_posts[yesterday].get('posts', [])
        viral_candidates = []
        
        print(f"📊 Prüfe {len(yesterdays_posts)} Posts vom {yesterday}...")
        
        for post_info in yesterdays_posts:
            try:
                # Hole aktuellen Post-Status von Reddit
                post_id = post_info.get('post_id')
                if not post_id:
                    continue
                
                # LÄNGERE Pause vor API-Aufruf beim Suchen (Rate Limit Schutz)
                time.sleep(random.uniform(10, 20))
                
                submission = self.reddit.submission(id=post_id)
                submission._fetch()
                
                # Prüfe ob Post viral gegangen ist (>1000 upvotes oder >100 Kommentare)
                if submission.score > 1000 or submission.num_comments > 100:
                    print(f"\n🚀 VIRALER POST GEFUNDEN!")
                    print(f"   Titel: {submission.title[:60]}...")
                    print(f"   Score: {submission.score} | Kommentare: {submission.num_comments}")
                    
                    viral_candidates.append({
                        'id': post_id,
                        'title': submission.title,
                        'score': submission.score,
                        'num_comments': submission.num_comments,
                        'url': f"https://reddit.com{submission.permalink}",
                        'subreddit': submission.subreddit.display_name
                    })
                    
            except Exception as e:
                print(f"❌ Fehler beim Prüfen von Post {post_id}: {e}")
                continue
        
        if viral_candidates:
            # Speichere virale Posts
            self.viral_posts[yesterday] = viral_candidates
            self._save_viral_tracking()
            
        return viral_candidates
    
    def find_top_comment_thread(self, post_id):
        """Findet den Top-Kommentar mit den meisten Antworten"""
        try:
            # LÄNGERE Pause vor API-Aufruf beim Suchen (Rate Limit Schutz)
            time.sleep(random.uniform(5, 10))
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)
            
            top_thread = None
            max_replies = 0
            
            for comment in submission.comments:
                if hasattr(comment, 'replies'):
                    reply_count = len(comment.replies)
                    if reply_count > max_replies:
                        max_replies = reply_count
                        top_thread = comment
            
            if top_thread:
                return {
                    'comment': top_thread,
                    'body': top_thread.body,
                    'score': top_thread.score,
                    'replies': top_thread.replies,
                    'reply_count': max_replies
                }
            
        except Exception as e:
            print(f"❌ Fehler beim Finden des Top-Kommentars: {e}")
        
        return None
    
    def generate_funny_contextual_comment(self, post_title, parent_comment, other_replies=[], subreddit_name=""):
        """Generiert einen kontextbezogenen Kommentar mit AI - optimiert für virale Reichweite"""
        
        if not self.openrouter_api_key:
            print("⚠️ OpenRouter API Key nicht gesetzt - verwende Fallback")
            return self.generate_viral_fallback_comment(subreddit_name)
        
        # Sammle Kontext von anderen Replies für bessere Anpassung
        reply_context = "\n".join([f"- {r.body[:100]}" for r in other_replies[:3]])
        
        # Erkenne Nischen-Hobbys und spezielle Subreddits
        niche_hobbies = ['bonsai', 'aquarium', 'pottery', 'woodworking', 'leathercraft', 
                        'fermentation', 'mushroom', 'orchid', 'blacksmith', 'knitting',
                        'vintage', 'coin', 'stamp', 'model', 'terrarium']
        
        help_subs = ['askdocs', 'fixit', 'askelectronics', 'diy', 'homeimprovement',
                    'learnprogramming', 'nostupidquestions', 'explainlikeimfive']
        
        is_niche = any(hobby in subreddit_name.lower() for hobby in niche_hobbies)
        is_help_sub = any(sub in subreddit_name.lower() for sub in help_subs)
        
        # Wähle Kommentar-Stil basierend auf Subreddit
        if is_niche:
            # Für Nischen-Hobbys: Stelle ehrliche Anfängerfragen
            prompt = f"""You're a curious beginner in r/{subreddit_name} asking genuine questions.

POST: "{post_title}"
COMMENT: "{parent_comment[:200]}"

Write a SHORT (1-2 sentences) beginner question or observation that:
- Shows genuine interest in learning
- Asks about technique, materials, or process
- Is humble and respectful
- Sounds like a real person discovering this hobby

Examples:
- "wow this is beautiful! how long did it take you to learn this technique?"
- "i'm just starting out with this hobby, what tools would you recommend for a beginner?"
- "this might be a dumb question but how do you keep it from [specific problem]?"
- "your work is inspiring! did you learn from youtube or take classes?"

VIRAL TIPS: Be relatable, show genuine excitement, add personal touch
Your genuine question (lowercase, casual):"""
        
        elif is_help_sub or "help" in parent_comment.lower() or "how" in parent_comment.lower():
            # Für Hilfe-Anfragen: Biete Unterstützung oder teile Erfahrung
            prompt = f"""You're helpfully responding in r/{subreddit_name}.

POST: "{post_title}"
COMMENT: "{parent_comment[:200]}"

Write a SHORT (1-2 sentences) helpful response that:
- Offers a specific tip or solution
- Shares personal experience with the issue
- Is supportive and encouraging
- Sounds genuine and knowledgeable

Examples:
- "i had this exact problem last week! try checking the [specific thing], that fixed it for me"
- "this happened to me too, what worked was [specific solution]"
- "hey just wanted to add that [specific tip] really helps with this"
- "if that doesn't work, you might also want to try [alternative solution]"

Your helpful response (lowercase, casual):"""
        
        else:
            # Standard: Mix mit 40% WERTVOLLE Kommentare
            weights = [0.2, 0.2, 0.2, 0.4]  # funny, question, relate, VALUE
            comment_types = random.choices(['funny', 'question', 'relate', 'value'], weights=weights)[0]
            
            if comment_types == 'question':
                prompt = f"""You're asking a follow-up question on Reddit.

POST: "{post_title}"
COMMENT: "{parent_comment[:200]}"

Write a SHORT (1-2 sentences) curious question that:
- Asks for more details or clarification
- Shows you're interested in the topic
- Sounds casual and conversational

Examples:
- "wait how did you even figure that out?"
- "did this actually work or are you just lucky?"
- "ok but seriously, how much did this cost you?"
- "genuine question - is this common or super rare?"

Your question (lowercase, casual):"""
            
            elif comment_types == 'relate':
                prompt = f"""You're relating to a Reddit comment.

POST: "{post_title}"
COMMENT: "{parent_comment[:200]}"

Write a SHORT (1-2 sentences) relatable response that:
- Shares a similar experience
- Agrees and adds to the point
- Sounds genuine and conversational

Examples:
- "literally same thing happened to me last month"
- "this is exactly why i stopped doing [thing]"
- "can confirm, my [person] does this all the time"
- "yep learned this the hard way too"

Your relatable response (lowercase, casual):"""
            
            elif comment_types == 'value':
                # WERTVOLLER KOMMENTAR mit echtem Mehrwert
                prompt = f"""You're adding VALUE to a Reddit discussion.

POST: "{post_title}"
COMMENT: "{parent_comment[:200]}"

Write a SHORT (2-3 sentences) comment that ADDS REAL VALUE:
- Share specific tips, resources, or solutions
- Add important context or corrections
- Provide helpful links or references
- Give actionable advice based on experience
- Point out something others missed

HIGH-VALUE Examples:
- "pro tip: if you're dealing with this, try [specific solution] - saved me hours of frustration"
- "for anyone interested, there's a free tool called [name] that does exactly this"
- "important context: this only works if you [specific condition], learned that the hard way"
- "adding to this - the documentation mentions [specific detail] that most people miss"
- "quick heads up: this changed in the latest update, you now need to [specific action]"
- "if you're struggling with this, r/[specific sub] has a great guide in their wiki"

Your VALUE-ADDING response (be specific and helpful):"""
            
            else:  # funny
                prompt = f"""You're making a witty Reddit comment.

POST: "{post_title}"
COMMENT: "{parent_comment[:200]}"

Write a SHORT (1-2 sentences) VIRAL funny response that:
- Makes a clever, unexpected observation
- Uses peak reddit humor
- Is highly relatable or absurd
- Could get thousands of upvotes

VIRAL Examples:
- "i also choose this guys dead wife"
- "sir this is a wendys"
- "task failed successfully"
- "instructions unclear, dick stuck in ceiling fan"
- "this is the way"
- "thanks i hate it"

Make it MEMORABLE and QUOTABLE (lowercase, casual):"""

        try:
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-5-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.9,
                    "max_tokens": 60
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                comment = result['choices'][0]['message']['content'].strip()
                # Stelle sicher dass Kommentar nicht zu kurz ist
                if len(comment) < 10:
                    print(f"   ⚠️ Kommentar zu kurz ({len(comment)} Zeichen), verwende Fallback")
                    return self.generate_viral_fallback_comment(subreddit_name)
                # Mache es noch natürlicher
                return self.add_natural_variations(comment)
            
        except Exception as e:
            print(f"❌ AI-Generierung fehlgeschlagen: {e}")
        
        return self.generate_fallback_comment(subreddit_name)
    
    def generate_viral_fallback_comment(self, subreddit_name=""):
        """Generiert virale Kommentare basierend auf erfolgreichen Reddit-Mustern"""
        
        # VIRALE KOMMENTAR-MUSTER (aus Analyse von Top-Comments)
        viral_patterns = {
            'relatable_struggle': [
                "i feel personally attacked by this accuracy",
                "why would you expose me like this on a friday",
                "this hit way too close to home and now i need therapy",
                "sir how did you get access to my life story",
                "i came here to have a good time and honestly im feeling so attacked right now",
                "delete this before my wife sees it and realizes im not unique"
            ],
            
            'unexpected_twist': [
                "plot twist: the real treasure was the anxiety we developed along the way",
                "instructions unclear, accidentally became successful",
                "task failed successfully",
                "this went from 0 to 100 real quick",
                "they had us in the first half not gonna lie",
                "well that escalated quickly"
            ],
            
            'wholesome_support': [
                "you dropped this 👑",
                "this is the kind of content i signed up for",
                "protect this human at all costs",
                "faith in humanity restored",
                "we dont deserve you but we need you",
                "youre doing amazing sweetie"
            ],
            
            'clever_observation': [
                "the fact that we all collectively agreed on this without discussion is peak humanity",
                "this is either genius or insane and honestly both work",
                "tell me youre [thing] without telling me youre [thing]",
                "this has the same energy as [relatable thing] and i love it",
                "why is nobody talking about the real issue here",
                "ok but can we appreciate the fact that [specific detail]"
            ],
            
            'self_deprecating': [
                "bold of you to assume i have my life together enough for this",
                "cries in poor",
                "laughs nervously in millennial",
                "my therapist would like a word with you",
                "i didnt come here to be called out but here we are",
                "this is the most expensive free advice ive ever received"
            ],
            
            'reddit_meta': [
                "reddit moment",
                "this guy reddits",
                "username checks out",
                "this is why i love reddit",
                "peak reddit right here",
                "the real LPT is always in the comments"
            ]
        }
        
        # Wähle Muster basierend auf Subreddit
        if any(word in subreddit_name.lower() for word in ['wholesome', 'made', 'smile', 'aww', 'happy']):
            pattern_type = 'wholesome_support'
        elif any(word in subreddit_name.lower() for word in ['funny', 'meme', 'joke']):
            pattern_type = random.choice(['relatable_struggle', 'unexpected_twist', 'self_deprecating'])
        elif any(word in subreddit_name.lower() for word in ['ask', 'question']):
            pattern_type = 'clever_observation'
        else:
            # Zufällige Auswahl für maximale Viralität
            pattern_type = random.choice(list(viral_patterns.keys()))
        
        comment = random.choice(viral_patterns[pattern_type])
        
        # Füge manchmal Edit hinzu (10% Chance) - das macht es authentischer
        if random.random() < 0.1:
            edits = [
                "\n\nedit: wow this blew up",
                "\n\nedit: thanks for the gold kind stranger!",
                "\n\nedit: rip my inbox",
                "\n\nedit: my highest rated comment is about this... thanks reddit"
            ]
            comment += random.choice(edits)
        
        return comment
    
    def generate_fallback_comment(self, subreddit_name=""):
        """Fallback für Kommentare ohne AI - angepasst an Subreddit"""
        
        # Erkenne Typ des Subreddits
        if any(hobby in subreddit_name.lower() for hobby in ['bonsai', 'aquarium', 'woodworking', 'pottery']):
            # Nischen-Hobby Fragen
            templates = [
                "wow this looks amazing! how long have you been doing this?",
                "this is so cool! what got you started with this hobby?",
                "beautiful work! is this difficult for beginners?",
                "this is inspiring! any tips for someone wanting to start?",
                "incredible detail! how long did this take you?",
                "this looks professional! did you teach yourself?"
            ]
        elif any(help in subreddit_name.lower() for help in ['ask', 'help', 'fix', 'learn']):
            # Hilfreiche Kommentare
            templates = [
                "i had this same issue, what helped me was checking the basics first",
                "this might help - have you tried the simpler solution?",
                "just wanted to add that this is more common than you think",
                "don't give up, we all started somewhere!",
                "great question, following this thread for answers too"
            ]
        else:
            # Standard lustige Kommentare
            templates = [
            "this is the way",
            "i felt that in my soul ngl",
            "why is this so accurate tho",
            "okay but why did you have to call me out like that",
            "instructions unclear, ended up here somehow",
            "this comment section is pure gold lmao",
            "reddit moment fr fr",
            "cant believe i had to scroll this far for this",
            "take my upvote and leave",
            "this is peak comedy and nobody can convince me otherwise"
            ]
        
        return random.choice(templates)
    
    def engage_with_viral_post(self, post_data):
        """Interagiert intelligent mit einem viralen Post"""
        print(f"\n💬 Interagiere mit viralem Post: {post_data['title'][:50]}...")
        
        # Finde Top-Kommentar-Thread
        top_thread = self.find_top_comment_thread(post_data['id'])
        
        if not top_thread:
            print("❌ Kein geeigneter Kommentar-Thread gefunden")
            return False
        
        print(f"📝 Top-Kommentar gefunden:")
        print(f"   Score: {top_thread['score']} | Antworten: {top_thread['reply_count']}")
        print(f"   Text: {top_thread['body'][:100]}...")
        
        comments_made = []
        
        # 1. Kommentiere auf Top-Kommentar
        main_comment = self.generate_funny_contextual_comment(
            post_data['title'],
            top_thread['body'],
            list(top_thread['replies'])[:5],
            post_data.get('subreddit', '')
        )
        
        print(f"\n🎯 Hauptkommentar: {main_comment}")
        
        if self.post_comment_to_reddit(top_thread['comment'], main_comment):
            comments_made.append({
                'type': 'main',
                'text': main_comment,
                'parent': 'top_comment'
            })
        
        # 2. Kommentiere auf 2-3 Sub-Kommentare für mehr Engagement
        sub_replies = list(top_thread['replies'])[:5]
        selected_replies = random.sample(sub_replies, min(2, len(sub_replies)))
        
        for reply in selected_replies:
            if hasattr(reply, 'body'):
                sub_comment = self.generate_funny_contextual_comment(
                    post_data['title'],
                    reply.body,
                    []
                )
                
                print(f"   💭 Sub-Kommentar: {sub_comment}")
                
                if self.post_comment_to_reddit(reply, sub_comment):
                    comments_made.append({
                        'type': 'sub',
                        'text': sub_comment,
                        'parent': reply.body[:50]
                    })
                
                # LÄNGERE WARTEZEIT zwischen Kommentaren (2-4 Minuten)
                wait_time = random.randint(120, 240)
                print(f"   ⏳ Warte {wait_time} Sekunden ({wait_time//60} Min) bis zum nächsten Kommentar...")
                time.sleep(wait_time)
        
        return comments_made
    
    def check_if_banned_from_subreddit(self, subreddit_name):
        """Prüft ob der Bot aus einem Subreddit gebannt ist"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            # Versuche auf banned status zuzugreifen
            banned = subreddit.banned(redditor=self.reddit.user.me())
            for ban in banned:
                # Wenn wir in der Liste sind, sind wir gebannt
                return True
            return False
        except Exception as e:
            # Bei 403 Forbidden sind wir wahrscheinlich gebannt
            if "403" in str(e) or "Forbidden" in str(e):
                return True
            return False
    
    def add_to_blacklist(self, subreddit_name):
        """Fügt ein Subreddit zur Blacklist hinzu"""
        blacklist_file = Path("/home/lucawahl/Reddit/blacklist_subreddits.txt")
        
        # Lese existierende Blacklist
        existing = []
        if blacklist_file.exists():
            with open(blacklist_file, 'r', encoding='utf-8') as f:
                existing = [line.strip() for line in f.readlines()]
        
        # Füge neues Subreddit hinzu wenn noch nicht vorhanden
        if subreddit_name not in existing and not subreddit_name.startswith('#'):
            with open(blacklist_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{subreddit_name}")
            print(f"   🚫 r/{subreddit_name} zur Blacklist hinzugefügt")
            
            # Update die in-memory Blacklist
            if hasattr(self, 'blacklisted_subreddits'):
                self.blacklisted_subreddits.append(subreddit_name.lower())
    
    def post_comment_to_reddit(self, parent, comment_text, dry_run=False):
        """Postet einen Kommentar auf Reddit"""
        if dry_run:
            print(f"   [DRY RUN] Würde kommentieren: {comment_text}")
            return True
        
        # Prüfe ob Kommentar leer ist
        if not comment_text or comment_text.strip() == "":
            print(f"   ❌ Kommentar ist leer - generiere Fallback")
            comment_text = "this is really interesting, thanks for sharing!"
        
        try:
            # Poste den Kommentar (mit keyword argument für PRAW 8)
            comment = parent.reply(body=comment_text)
            print(f"   ✅ Kommentar erfolgreich gepostet!")
            
            # Speichere Kommentar-Info
            self.save_generated_comment({
                'post_id': parent.submission.id if hasattr(parent, 'submission') else 'unknown',
                'parent_id': parent.id,
                'comment': comment_text,
                'subreddit': parent.subreddit.display_name if hasattr(parent, 'subreddit') else 'unknown',
                'timestamp': time.time()
            })
            
            return True
        except Exception as e:
            error_msg = str(e)
            if 'THREAD_LOCKED' in error_msg:
                print(f"   ❌ Thread ist gesperrt")
            elif 'DELETED_COMMENT' in error_msg:
                print(f"   ❌ Kommentar wurde gelöscht")
            elif 'ratelimit' in error_msg.lower() or 'RATELIMIT' in error_msg:
                print(f"   ⏰ Rate Limit erreicht - warte 10 Minuten...")
                time.sleep(600)  # 10 Minuten warten bei Rate Limit
                print(f"   🔄 Versuche erneut nach Wartezeit")
            else:
                print(f"   ❌ Fehler beim Posten: {error_msg[:100]}")
            return False
    
    def save_generated_comment(self, comment_data):
        """Speichert generierten Kommentar"""
        from datetime import datetime
        
        # Erstelle Ordnerstruktur
        base_dir = Path("/home/lucawahl/Reddit/generated_comments")
        date_now = datetime.now()
        year_month = date_now.strftime("%Y-%m")
        day = date_now.strftime("%d")
        
        comment_dir = base_dir / year_month / day
        comment_dir.mkdir(parents=True, exist_ok=True)
        
        # Speichere Kommentar
        timestamp = date_now.strftime("%H%M%S")
        filename = f"comment_{timestamp}.json"
        
        file_path = comment_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(comment_data, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def viral_engagement_loop(self):
        """Hauptloop für virale Post-Interaktion"""
        print("\n🔥 VIRAL ENGAGEMENT MODUS")
        print("="*60)
        
        # Prüfe gestrige Posts
        viral_posts = self.check_yesterdays_viral_posts()
        
        if not viral_posts:
            print("😴 Keine viralen Posts vom Vortag gefunden")
            return
        
        print(f"\n🎯 {len(viral_posts)} virale Posts gefunden!")
        
        for post in viral_posts:
            print(f"\n{'='*40}")
            print(f"📌 Bearbeite: {post['title'][:60]}...")
            print(f"   r/{post['subreddit']} | Score: {post['score']}")
            
            # Interagiere mit dem Post
            comments = self.engage_with_viral_post(post)
            
            if comments:
                print(f"   ✅ {len(comments)} Kommentare erstellt")
            
            # LÄNGERE Pause zwischen Posts (10-20 Minuten)
            wait_time = random.randint(600, 1200)
            print(f"   ⏳ Warte {wait_time//60} Minuten bis zum nächsten Post...")
            time.sleep(wait_time)
        
        print("\n✅ Viral Engagement abgeschlossen!")
    
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
    
    def clean_post_title(self, title):
        """Bereinigt Post-Titel von problematischen Elementen"""
        import re
        
        # Entferne mehrfache Leerzeichen
        title = ' '.join(title.split())
        
        # Entferne Emojis (optional - manche Subs erlauben sie)
        # title = re.sub(r'[^\x00-\x7F]+', '', title)
        
        # Entferne verbotene Phrasen
        banned_phrases = [
            'upvote if', 'upvote this', 'please upvote',
            'don\'t let this die', 'to the front page',
            'karma please', 'give me karma',
            '[OC]', '[oc]', '(OC)', '(oc)',  # Entferne OC tags wenn nicht eigener Content
            'EDIT:', 'UPDATE:'
        ]
        
        title_lower = title.lower()
        for phrase in banned_phrases:
            if phrase.lower() in title_lower:
                # Entferne die Phrase case-insensitive
                title = re.sub(re.escape(phrase), '', title, flags=re.IGNORECASE)
        
        # Prüfe auf ALL CAPS (mehr als 50% Großbuchstaben)
        if sum(1 for c in title if c.isupper()) > len(title) * 0.5:
            # Konvertiere zu normaler Schreibweise
            title = title.title()
            print(f"   📝 Titel von CAPS zu Normal konvertiert")
        
        # Entferne übermäßige Satzzeichen am Ende
        title = re.sub(r'[!?.]{2,}$', '.', title)
        
        # Stelle sicher dass Titel nicht zu lang ist (max 300 Zeichen)
        if len(title) > 300:
            title = title[:297] + "..."
            print(f"   ✂️ Titel gekürzt auf 300 Zeichen")
        
        # Entferne führende/nachfolgende Leerzeichen
        title = title.strip()
        
        return title
    
    def delete_posted_folder(self, post_data):
        """Löscht den Post-Ordner aus data_all/Posts nach erfolgreichem Posten"""
        import shutil
        import glob
        
        post_id = post_data.get('id', '')
        post_title = post_data.get('title', '')
        
        # Suche nach dem entsprechenden Ordner
        for folder in self.posts_dir.iterdir():
            if folder.is_dir():
                # Prüfe ob es der richtige Post ist
                json_file = folder / "post_data.json"
                if json_file.exists():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Prüfe ob es der gleiche Post ist (ID oder Titel)
                            if data.get('id') == post_id or data.get('title') == post_title:
                                # Lösche den gesamten Ordner mit mehreren Versuchen
                                deleted = False
                                
                                # Versuch 1: Normal mit shutil
                                try:
                                    shutil.rmtree(folder)
                                    deleted = True
                                    print(f"   🗑️ Post-Ordner gelöscht: {folder.name}")
                                except:
                                    pass
                                
                                # Versuch 2: Lösche nur normale Dateien, ignoriere .nfs Dateien
                                if not deleted:
                                    try:
                                        print(f"   🔧 Lösche Dateien einzeln (ignoriere .nfs)...")
                                        for file in folder.iterdir():
                                            if file.is_file() and not str(file.name).startswith('.nfs'):
                                                try:
                                                    file.unlink()
                                                except:
                                                    pass
                                        
                                        # Versuche Ordner zu löschen (schlägt fehl wenn .nfs noch da)
                                        try:
                                            folder.rmdir()
                                            deleted = True
                                            print(f"   🗑️ Post-Ordner gelöscht: {folder.name}")
                                        except:
                                            # Ordner hat noch .nfs Dateien, aber normale Dateien sind weg
                                            print(f"   ⚠️ Ordner enthält noch temporäre .nfs Dateien (werden automatisch gelöscht)")
                                            deleted = True  # Betrachte als erfolgreich
                                    except Exception as e:
                                        print(f"   ⚠️ Teilweise gelöscht: {str(e)[:50]}")
                                
                                # Entferne aus der internen Liste auch wenn Löschen teilweise fehlschlug
                                self.posts = [p for p in self.posts if p.get('id') != post_id]
                                return True
                                
                    except Exception as e:
                        print(f"   ⚠️ Fehler beim Verarbeiten: {e}")
        
        return False
    
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
            temp_dir = Path("/home/lucawahl/Reddit/temp_images")
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
        if not ignore_limit and self.daily_post_target == 0:
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
            
            # Prüfe Account-Alter und Karma
            try:
                account = self.reddit.user.me()
                account_age_days = (time.time() - account.created_utc) / 86400
                account_karma = account.link_karma + account.comment_karma
                
                print(f"   👤 Account: {account_age_days:.0f} Tage alt, {account_karma} Karma")
                
                # Warne bei jungem Account
                if account_age_days < 30:
                    print(f"   ⚠️ Account ist nur {account_age_days:.0f} Tage alt - manche Subs verlangen 30+ Tage")
                if account_karma < 100:
                    print(f"   ⚠️ Niedriges Karma ({account_karma}) - manche Subs verlangen 100+")
            except:
                pass
            
            # Liste problematischer Subreddits mit strengen Regeln
            problematic_subs = {
                'pics': ['interestingasfuck', 'Damnthatsinteresting', 'BeAmazed', 'nextfuckinglevel'],
                'photography': ['nocontextpics', 'pic', 'images'],
                'itookapicture': ['nocontextpics', 'pic', 'images'],
                'art': ['somethingimade', 'crafts', 'DIY'],
                'drawing': ['doodles', 'sketches'],
                'painting': ['somethingimade', 'crafts'],
                'earthporn': ['natureisfuckinglit', 'NatureIsFuckingLit', 'BeAmazed'],
                'foodporn': ['food', 'FoodPorn', 'shittyfoodporn'],
                'mildlyinteresting': ['interestingasfuck', 'Damnthatsinteresting'],
                'oldschoolcool': ['TheWayWeWere', 'nostalgia']
            }
            
            # Prüfe ob Subreddit problematisch ist
            sub_name = subreddit.display_name.lower()
            if sub_name in problematic_subs:
                print(f"   ⚠️ r/{sub_name} hat strenge OC/Regeln")
                print("   Verwende alternativen Subreddit...")
                
                # Wähle alternativen Subreddit
                alternatives = problematic_subs.get(sub_name, ['interestingasfuck', 'Damnthatsinteresting', 'BeAmazed'])
                
                for alt in alternatives:
                    try:
                        subreddit = self.reddit.subreddit(alt)
                        # Prüfe ob Subreddit existiert und zugänglich ist
                        _ = subreddit.display_name
                        print(f"   ✅ Verwende r/{alt} stattdessen")
                        post_data['subreddit'] = alt
                        break
                    except Exception as e:
                        print(f"   ❌ r/{alt} nicht verfügbar: {str(e)[:50]}")
                        continue
            
            # Bereinige Titel von problematischen Elementen
            clean_title = self.clean_post_title(post_data['title'])
            
            # Erstelle den Post mit Flair wenn möglich
            if post_data.get('selftext'):
                # Text-Post
                submission = subreddit.submit(
                    title=clean_title,
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
            
            # LÖSCHE den Post-Ordner aus data_all/Posts nach erfolgreichem Posten
            self.delete_posted_folder(post_data)
            
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
        
        print("\n🤖 COMBINED BOT - AUTOMATISCHER LOOP MIT TAGESLIMIT")
        print("="*60)
        print(f"⏰ Aktive Zeit: {start_hour}:00 - {end_hour}:00 Uhr")
        print(f"📊 Post-Ziel: {self.daily_post_target} Posts (Max 4/Tag)")
        print(f"📊 Kommentar-Ziel: {self.daily_comment_target} Kommentare (3-7/Tag)")
        print(f"⏳ Wartezeit zwischen Posts: 0.5-2 Stunden")
        print(f"👥 Benutzer aus otherUser.txt: {len(self.users_to_process)}")
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
                    if self.daily_post_target == 0:
                        print(f"\n😴 Heute ist ein Pausentag - keine Posts geplant")
                    else:
                        print(f"\n🌅 Neuer Tag! Post-Ziel: {self.daily_post_target} Posts")
                
                # Prüfe ob heute ein Pausentag ist
                if self.daily_post_target == 0:
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
                # Stelle sicher dass daily_post_target gesetzt ist
                if self.daily_post_target is None:
                    self._load_daily_stats()
                    if self.daily_post_target is None:
                        self.daily_post_target = random.randint(1, 4)
                
                remaining_today = self.daily_post_target - current_count
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
                print(f"   Tagesfortschritt: {current_count}/{self.daily_post_target}")
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
            comment_count = self.get_today_comment_count()
            print(f"\n\n👋 Loop beendet")
            print(f"📊 Heute erstellt:")
            print(f"   Posts: {current_count}/{self.daily_post_target}")
            print(f"   Kommentare: {comment_count}/{self.daily_comment_target}")
            print(f"   Sessions heute: {session_count}")
    
    def run_comment_loop(self):
        """Hauptloop für automatische Kommentare"""
        from datetime import datetime, timedelta
        
        print("\n💬 AUTOMATISCHER KOMMENTAR-LOOP")
        print("="*60)
        print(f"📊 Kommentar-Ziel heute: {self.daily_comment_target} Kommentare")
        print(f"📊 Bereits erstellt: {self.get_today_comment_count()}")
        print("\nDrücke Ctrl+C zum Beenden")
        print("="*60)
        
        try:
            while True:
                # Prüfe ob heute noch Kommentare erlaubt
                if not self.can_comment_today():
                    print(f"\n✅ Tagesziel erreicht! Warte bis morgen...")
                    time.sleep(3600)  # 1 Stunde warten
                    continue
                
                # Finde beliebte Posts zum Kommentieren
                print(f"\n🔍 Suche nach Posts zum Kommentieren...")
                target_post = self.find_popular_post_to_comment()
                
                if target_post:
                    print(f"\n📝 Gefunden: {target_post['title'][:60]}...")
                    print(f"   Subreddit: r/{target_post['subreddit']}")
                    print(f"   Score: {target_post['score']} | Kommentare: {target_post['num_comments']}")
                    
                    # Generiere und poste Kommentar
                    success = self.create_smart_comment(target_post)
                    
                    if success:
                        # Update Statistiken
                        self.increment_comment_daily_count({
                            'post_id': target_post['id'],
                            'subreddit': target_post['subreddit'],
                            'comment': 'Kommentar erstellt'
                        })
                        
                        # LÄNGERE Wartezeit: 5-10 Minuten zwischen Kommentaren
                        wait_time = random.randint(300, 600)
                        print(f"\n⏳ Warte {wait_time//60} Minuten bis zum nächsten Kommentar...")
                        time.sleep(wait_time)
                    else:
                        print("❌ Kommentar fehlgeschlagen, versuche anderen Post...")
                        time.sleep(30)
                else:
                    print("❌ Keine geeigneten Posts gefunden, warte...")
                    time.sleep(300)  # 5 Minuten
                    
        except KeyboardInterrupt:
            print(f"\n\n👋 Kommentar-Loop beendet")
            print(f"📊 Heute erstellt: {self.get_today_comment_count()}/{self.daily_comment_target} Kommentare")
    
    def find_popular_post_to_comment(self):
        """Findet einen beliebten Post zum Kommentieren - NUR in ADHD-fokussierten Subreddits"""
        try:
            # NUR ADHD-fokussierte Subreddits aus target_subreddits Dateien
            # Diese sind bereits in self.all_subreddits geladen
            if self.all_subreddits:
                # Verwende NUR die geladenen ADHD-Subreddits
                adhd_subs = self.all_subreddits
            else:
                # Fallback auf Core ADHD Subreddits
                adhd_subs = [
                    'ADHD', 'ADHDwomen', 'AdultADHD', 'ADHDUK', 'ADHDmemes',
                    'ADHD_Parenting', 'HowToADHD', 'AuDHD', 'adhdmeme', 'adhd_anxiety',
                    'GetDisciplined', 'productivity', 'bulletjournal', 'organization',
                    'mentalhealth', 'anxiety', 'therapy', 'selfcare', 'meditation',
                    'decidingtobebetter', 'selfimprovement', 'GetMotivated'
                ]
            
            # Verwende die ADHD-fokussierten Subreddits
            target_subs = adhd_subs
            
            # Versuche mehrere Subreddits
            for attempt in range(3):
                if not target_subs:
                    break
                    
                target_sub = random.choice(target_subs)
                print(f"   🔎 Prüfe r/{target_sub}...")
                
                try:
                    # Prüfe zuerst ob wir gebannt sind
                    if self.check_if_banned_from_subreddit(target_sub):
                        print(f"   🚫 Gebannt in r/{target_sub} - überspringe")
                        self.add_to_blacklist(target_sub)
                        continue
                    
                    subreddit = self.reddit.subreddit(target_sub)
                    # Hole Hot Posts
                    posts = list(subreddit.hot(limit=25))
                    
                    # Filtere geeignete Posts
                    suitable_posts = []
                    for post in posts:
                        # Skip wenn wir schon kommentiert haben
                        if post.id in self.commented_posts:
                            continue
                            
                        # HÖHERE Standards: 100+ Score, 10+ Kommentare, 2-12h alt (perfektes Timing)
                        post_age_hours = (time.time() - post.created_utc) / 3600
                        if (post.score > 100 and 
                            post.num_comments > 10 and 
                            post_age_hours > 2 and  # Nicht zu früh
                            post_age_hours < 12 and  # Noch im Aufwärtstrend
                            not post.locked and
                            not post.archived):
                            
                            suitable_posts.append({
                                'id': post.id,
                                'title': post.title,
                                'subreddit': post.subreddit.display_name,
                                'score': post.score,
                                'num_comments': post.num_comments,
                                'submission': post
                            })
                    
                    if suitable_posts:
                        print(f"   ✅ {len(suitable_posts)} geeignete Posts gefunden")
                        return random.choice(suitable_posts)
                        
                except Exception as e:
                    print(f"   ⚠️ Fehler bei r/{target_sub}: {str(e)[:50]}")
                    continue
            
            print("   ❌ Keine Posts nach 3 Versuchen gefunden")
                
        except Exception as e:
            print(f"❌ Fehler bei Post-Suche: {e}")
        
        return None
    
    def create_smart_comment(self, post_data):
        """Erstellt einen intelligenten Kommentar auf einem Post mit perfektem Timing"""
        try:
            submission = post_data['submission']
            
            # Prüfe auf Event-bezogene Keywords für perfektes Timing
            title_lower = post_data['title'].lower()
            event_keywords = {
                'update': "thanks for the update! ",
                'follow up': "glad you followed up on this! ",
                'happened': "wow, hope you're okay now! ",
                'just': "perfect timing seeing this! ",
                'today': "what a coincidence, ",
                'yesterday': "i saw something similar yesterday! ",
                'breaking': "this is huge if true! ",
                'finally': "about time! been waiting for this ",
                'announced': "this changes everything! ",
                'released': "can't wait to try this! "
            }
            
            # Füge Event-Kontext hinzu wenn relevant
            event_prefix = ""
            for keyword, prefix in event_keywords.items():
                if keyword in title_lower:
                    event_prefix = prefix
                    break
            
            # Hole Top-Kommentare für Kontext
            submission.comments.replace_more(limit=0)
            top_comments = submission.comments[:5]
            
            # Finde einen guten Kommentar zum Antworten
            target_comment = None
            for comment in top_comments:
                if hasattr(comment, 'body') and len(comment.body) > 20:
                    target_comment = comment
                    break
            
            if target_comment:
                # Generiere kontextbezogenen Kommentar
                comment_text = self.generate_funny_contextual_comment(
                    post_data['title'],
                    target_comment.body,
                    [],
                    post_data.get('subreddit', '')
                )
                
                # Füge Event-Prefix hinzu wenn vorhanden
                if event_prefix and random.random() < 0.5:  # 50% Chance für Event-Bezug
                    comment_text = event_prefix + comment_text
                
                print(f"\n💬 Kommentar: {comment_text}")
                
                # Poste den Kommentar
                if not self.post_comment_to_reddit(target_comment, comment_text, dry_run=False):
                    return False
                    
                # Markiere als kommentiert
                self.commented_posts.add(post_data['id'])
                self._save_commented_history()
                
                return True
            else:
                print("❌ Kein geeigneter Kommentar zum Antworten gefunden")
                return False
                
        except Exception as e:
            print(f"❌ Fehler beim Kommentieren: {e}")
            return False
    
    def test_comment_generation(self):
        """Testet die Kommentar-Generierung ohne zu posten"""
        print("\n🧪 TESTE KOMMENTAR-GENERIERUNG")
        print("="*60)
        
        # Beispiel-Daten
        test_posts = [
            "My cat learned how to open doors and now I have no privacy",
            "Just finished my first marathon at 45 years old",
            "Found this weird bug in my code after 3 hours of debugging"
        ]
        
        test_comments = [
            "This is literally the best thing I've seen all day",
            "Same thing happened to me last week",
            "You should definitely post this on the other subreddit too"
        ]
        
        for i in range(3):
            post = random.choice(test_posts)
            comment = random.choice(test_comments)
            
            print(f"\n📝 Post: {post}")
            print(f"💭 Top-Kommentar: {comment}")
            
            generated = self.generate_funny_contextual_comment(post, comment, [])
            print(f"🤖 Generiert: {generated}")
            print("-"*40)
    
    def show_statistics(self):
        """Zeigt Statistiken über die geladenen Posts"""
        print("\n📊 STATISTIKEN:")
        print(f"Posts gesamt: {len(self.posts)}")
        print(f"Benutzer in otherUser.txt: {len(self.users_to_process)}")
        
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
    
    # Prüfe ob Config-Datei existiert
    config_file = Path("/home/lucawahl/Reddit/bot_config.json")
    use_config = config_file.exists()
    
    if not use_config:
        print("\n⚠️ Keine Konfigurationsdatei gefunden!")
        print("Möchtest du jetzt API-Daten eingeben?")
        setup = input("(j/n): ").strip().lower()
        if setup in ['j', 'ja', 'yes', 'y']:
            bot = CombinedBot(use_config_file=False)
            bot.update_credentials()
            use_config = True
        else:
            print("ℹ️ Verwende Hardcoded-Defaults (müssen im Code angepasst werden)")
            bot = CombinedBot(use_config_file=False)
    else:
        bot = CombinedBot(use_config_file=True)
    
    # AUTOMATISCH: Prüfe virale Posts vom Vortag beim Start
    print("\n🔍 Prüfe automatisch virale Posts vom Vortag...")
    viral_posts = bot.check_yesterdays_viral_posts()
    if viral_posts:
        print(f"\n🔥 {len(viral_posts)} VIRALE POSTS GEFUNDEN!")
        engage = input("Möchtest du diese jetzt bearbeiten? (j/n): ").strip().lower()
        if engage in ['j', 'ja', 'yes', 'y']:
            bot.viral_engagement_loop()
    
    print("\n🤖 Combined Bot - Posts & Kommentare (PythonAnywhere Edition)")
    print("="*50)
    print("Was möchtest du tun?")
    print("1. 🔄 Automatischer Post-Loop")
    print("2. 📝 Einzelnen Post erstellen")
    print("3. 💬 Kommentar-Modus")
    print("4. 🔥 Viral Engagement (gestrige Posts)")
    print("5. 📊 Statistiken anzeigen")
    print("6. 🎲 Zufälligen Post anzeigen")
    print("7. 🔍 Posts nach Subreddit filtern")
    print("8. 👥 Benutzer aus otherUser.txt verarbeiten")
    print("9. 📋 Zeige alle Subreddits")
    print("10. 🔑 API-Daten eingeben/ändern")
    
    choice = input("\nAuswahl (1-10): ").strip()
    
    if choice == "1":
        # Automatischer Loop mit Tageslimit
        print("\n🔄 AUTOMATISCHER POST-LOOP MIT TAGESLIMIT")
        print("="*60)
        print(f"• Post-Ziel: {bot.daily_post_target} Posts (0-4 pro Tag)")
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
        # Kommentar-Modus
        print("\n💬 KOMMENTAR-MODUS")
        print("="*60)
        print(f"• Kommentar-Ziel: {bot.daily_comment_target} Kommentare (5-20 pro Tag)")
        print(f"• Heute bereits: {bot.get_today_comment_count()} Kommentare")
        
        print("\nOptionen:")
        print("1. Automatischer Kommentar-Loop")
        print("2. Einzelne Kommentare generieren (Simulation)")
        
        comment_choice = input("\nWahl (1-2): ").strip()
        
        if comment_choice == "1":
            print("\n🚀 Starte automatischen Kommentar-Loop...")
            confirm = input("\n⚠️ WARNUNG: Kommentare werden auf Reddit erstellt! Fortfahren? (j/n): ").strip().lower()
            if confirm in ['j', 'ja', 'yes', 'y']:
                bot.run_comment_loop()
            else:
                print("❌ Abgebrochen")
        else:
            print("\n📝 Teste Kommentar-Generierung...")
            bot.test_comment_generation()
    
    elif choice == "4":
        # Viral Engagement Modus
        print("\n🔥 VIRAL ENGAGEMENT MODUS")
        print("="*60)
        print("Prüfe Posts vom Vortag auf virale Aktivität...")
        bot.viral_engagement_loop()
        
    elif choice == "5":
        bot.show_statistics()
        
    elif choice == "6":
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
                
    elif choice == "7":
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
    
    elif choice == "8":
        # Benutzer verarbeiten
        bot.process_users()
    
    elif choice == "9":
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
    
    elif choice == "10":
        # API-Daten eingeben/ändern
        bot.update_credentials()
        
        # Zeige aktuelle Konfiguration (ohne Passwörter)
        print("\n📋 Aktuelle Konfiguration:")
        print(f"   Client ID: {bot.config.get('client_id', '')[:15]}...")
        print(f"   Username: {bot.config.get('username', '')}")
        print(f"   Config-Datei: {bot.config_file}")
    
    else:
        print("Ungültige Auswahl")

if __name__ == "__main__":
    main()