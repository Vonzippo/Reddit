#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Kommentare Bot - Verbesserte Version mit ADHD-Fokus
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
        self.base_dir = Path("data_all")
        self.posts_dir = self.base_dir / "Posts"
        self.comments_dir = self.base_dir / "Comments"
        self.posts = []
        self.comments = []
        self._load_data()
        self._load_subreddits()
        
        # Track bereits kommentierte Posts
        self.commented_posts = set()
        self._load_commented_history()
        
        # OpenRouter API Konfiguration
        from config import OPENROUTER_API_KEY
        self.openrouter_api_key = OPENROUTER_API_KEY
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Reddit API Konfiguration mit verbesserter Fehlerbehandlung
        self._init_reddit_connection()
        
        # Lade Benutzer aus otherUser.txt
        self.users_to_process = self._load_users_from_file()
    
    def _load_users_from_file(self):
        """Lädt Benutzernamen aus otherUser.txt"""
        users = []
        user_file = Path("./otherUser.txt")
        
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
        """Initialisiert oder erneuert die Reddit-Verbindung"""
        try:
            from config import ACTIVE_CONFIG
            
            self.reddit = praw.Reddit(
                client_id=ACTIVE_CONFIG["client_id"],
                client_secret=ACTIVE_CONFIG["client_secret"],
                user_agent=ACTIVE_CONFIG["user_agent"],
                username=ACTIVE_CONFIG["username"],
                password=ACTIVE_CONFIG["password"],
                ratelimit_seconds=300  # Wartet automatisch bei Rate Limits
            )
            # Test der Verbindung
            _ = self.reddit.user.me()
            print(f"✅ Reddit-Verbindung erfolgreich hergestellt als u/{ACTIVE_CONFIG['username']}")
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
        """Lädt alle Target-Subreddits aus den Dateien und entfernt gebannte"""
        self.all_subreddits = []
        self.blacklisted_subreddits = []
        
        # Lade Blacklist zuerst
        blacklist_file = Path("./blacklist_subreddits.txt")
        if blacklist_file.exists():
            with open(blacklist_file, 'r', encoding='utf-8') as f:
                for line in f:
                    sub = line.strip()
                    if sub and not sub.startswith('#'):
                        self.blacklisted_subreddits.append(sub.lower())
            print(f"🚫 Blacklist geladen: {len(self.blacklisted_subreddits)} gesperrte Subreddits")
        
        # Lade aus target_subreddits.txt
        target_file = Path("./target_subreddits.txt")
        if target_file.exists():
            with open(target_file, 'r', encoding='utf-8') as f:
                for line in f:
                    sub = line.strip()
                    if sub and not sub.startswith('#'):
                        # Prüfe ob Subreddit auf Blacklist
                        if sub.lower() not in self.blacklisted_subreddits:
                            self.all_subreddits.append(sub)
        
        # Lade aus target_subreddits_extended.txt (ohne Duplikate)
        extended_file = Path("./target_subreddits_extended.txt")
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
        
        # FALLBACK wenn keine Subreddits geladen wurden
        if not self.all_subreddits:
            print("⚠️ Keine Subreddits aus Dateien geladen - verwende Fallback-Liste")
            self.all_subreddits = [
                'ADHD', 'ADHDUK', 'HowToADHD', 'AuDHD',
                'GetDisciplined', 'productivity', 'bulletjournal',
                'planners', 'PlannerAddicts', 'bujo', 'Journaling',
                'mentalhealth', 'anxiety', 'therapy', 'selfcare',
                'decidingtobebetter', 'selfimprovement', 'GetMotivated',
                'organization', 'declutter', 'minimalism',
                'Notion', 'ObsidianMD', 'todoist',
                'needafriend', 'CasualConversation', 'offmychest'
            ]
            # Filtere Blacklist auch aus Fallback
            self.all_subreddits = [s for s in self.all_subreddits 
                                  if s.lower() not in self.blacklisted_subreddits]
        
        print(f"📋 Geladen: {len(self.all_subreddits)} ADHD-fokussierte Subreddits (nach Blacklist-Filter)")
    
    def _load_commented_history(self):
        """Lädt Historie der bereits kommentierten Posts"""
        history_file = Path("./commented_posts.json")
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
        history_file = Path("./commented_posts.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump({'posts': list(self.commented_posts)}, f, indent=2)
    
    def check_if_already_commented(self, post_id):
        """Prüft ob der Bot bereits auf diesem Post kommentiert hat"""
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)
            
            # Prüfe ob unser Bot bereits kommentiert hat
            for comment in submission.comments.list():
                if comment.author and comment.author.name == self.reddit.user.me().name:
                    return True
            return False
        except:
            return False
    
    def check_if_banned_from_subreddit(self, subreddit_name):
        """Prüft ob der Bot aus einem Subreddit gebannt ist"""
        try:
            # Versuche auf Subreddit zuzugreifen
            subreddit = self.reddit.subreddit(subreddit_name)
            _ = subreddit.display_name
            
            # Wenn wir gebannt sind, sollte dieser Zugriff fehlschlagen
            _ = subreddit.submit_selfpost
            
            # Wenn wir hier ankommen, sind wir NICHT gebannt
            return False
            
        except Exception as e:
            error_str = str(e).lower()
            # Nur bei spezifischen Ban-Fehlern True zurückgeben
            if any(ban_indicator in error_str for ban_indicator in [
                'banned', 'suspended', 'not allowed', 'forbidden to post'
            ]):
                return True
            # Alle anderen Fehler bedeuten NICHT gebannt
            return False
    
    def add_to_blacklist(self, subreddit_name):
        """Fügt ein Subreddit zur Blacklist hinzu"""
        blacklist_file = Path("./blacklist_subreddits.txt")
        
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
    
    def find_popular_post_to_comment(self):
        """Findet einen beliebten Post zum Kommentieren - NUR in ADHD-fokussierten Subreddits"""
        try:
            # NUR ADHD-fokussierte Subreddits aus target_subreddits Dateien
            if self.all_subreddits:
                adhd_subs = self.all_subreddits
            else:
                # Fallback auf Core ADHD Subreddits (ohne Blacklist)
                adhd_subs = [
                    'ADHD', 'AdultADHD', 'ADHDUK', 'HowToADHD',
                    'GetDisciplined', 'productivity', 'bulletjournal',
                    'mentalhealth', 'anxiety', 'therapy', 'selfcare'
                ]
            
            # Mische die Subreddits für Abwechslung
            target_subs = adhd_subs.copy()
            random.shuffle(target_subs)
            
            # Versuche mehrere Subreddits
            for attempt in range(5):
                if not target_subs:
                    break
                    
                target_sub = random.choice(target_subs)
                print(f"   🔎 Prüfe r/{target_sub}...")
                
                # WARTEZEIT zwischen Subreddit-Scans (30 Sekunden)
                if attempt > 0:
                    print(f"   ⏳ Warte 30 Sekunden vor nächstem Scan...")
                    time.sleep(30)
                
                try:
                    # Prüfe zuerst ob wir gebannt sind
                    if self.check_if_banned_from_subreddit(target_sub):
                        print(f"   🚫 Gebannt in r/{target_sub} - überspringe")
                        self.add_to_blacklist(target_sub)
                        # Kurze Pause nach Ban-Check
                        time.sleep(1)
                        continue
                    
                    subreddit = self.reddit.subreddit(target_sub)
                    
                    # Kleine Pause vor dem Abrufen der Posts
                    time.sleep(0.5)
                    
                    # Hole Hot Posts
                    posts = list(subreddit.hot(limit=25))
                    
                    # Filtere geeignete Posts
                    suitable_posts = []
                    for post in posts:
                        # Skip wenn wir schon kommentiert haben
                        if post.id in self.commented_posts:
                            continue
                            
                        # ANGEPASSTE Standards für bessere Trefferquote
                        post_age_hours = (time.time() - post.created_utc) / 3600
                        if (post.score > 30 and  # Reduziert von 100
                            post.num_comments > 5 and  # Reduziert von 10
                            post_age_hours > 1 and  # Früher erlaubt
                            post_age_hours < 24 and  # Längeres Zeitfenster (24h statt 12h)
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
                    error_msg = str(e)
                    print(f"   ⚠️ Fehler bei r/{target_sub}: {error_msg[:50]}")
                    
                    # Auto-Blacklist bei bestimmten Fehlern
                    if "403" in error_msg or "Redirect" in error_msg or "not found" in error_msg.lower():
                        print(f"   🚫 r/{target_sub} wird zur Blacklist hinzugefügt")
                        self.add_to_blacklist(target_sub)
                        # Entferne aus aktiver Liste
                        if target_sub in target_subs:
                            target_subs.remove(target_sub)
                    
                    continue
            
            print("   ❌ Keine Posts nach 5 Versuchen gefunden")
                
        except Exception as e:
            print(f"❌ Fehler bei Post-Suche: {e}")
        
        return None
    
    def generate_smart_comment(self, post_title, post_body, existing_comments, subreddit=""):
        """Generiert intelligente ADHD-fokussierte Kommentare mit AI"""
        
        # Analysiere Post-Kontext für ADHD-Relevanz
        context = (post_title + " " + post_body).lower()
        
        # ADHD-spezifische Keywords
        adhd_keywords = ['adhd', 'executive dysfunction', 'hyperfocus', 'medication', 
                        'diagnosis', 'dopamine', 'focus', 'attention', 'hyperactive',
                        'time blind', 'rejection sensitive', 'rsd', 'neurodivergent']
        
        planning_keywords = ['planner', 'bullet journal', 'bujo', 'organization', 
                           'productivity', 'task', 'schedule', 'routine', 'habit']
        
        is_adhd_related = any(kw in context for kw in adhd_keywords) or 'adhd' in subreddit.lower()
        is_planning_related = any(kw in context for kw in planning_keywords)
        
        # Wähle passenden Kommentar-Typ
        if is_adhd_related:
            comment_type = random.choice(['adhd_experience', 'adhd_tip', 'adhd_support'])
        elif is_planning_related:
            comment_type = random.choice(['planning_tip', 'planning_question', 'planning_relate'])
        else:
            comment_type = random.choice(['value', 'question', 'relatable'])
        
        # Erstelle Prompt basierend auf Typ
        if comment_type == 'adhd_experience':
            prompt = f"""Generate an ADHD community comment sharing personal experience.
Post title: {post_title}
Subreddit: r/{subreddit}

Create a comment that:
- Shares a specific ADHD experience or struggle
- Shows understanding and empathy
- Uses ADHD community language naturally
- Is 1-2 sentences long
- Sounds genuine and supportive

Examples:
- "the executive dysfunction is real, sometimes i just stare at my to-do list for hours"
- "hyperfocus kicked in and suddenly its 3am and i know everything about medieval blacksmithing"
- "body doubling saved my productivity, even virtual coworking helps so much"

Write ONLY the comment text (lowercase, casual):"""
        
        elif comment_type == 'adhd_tip':
            prompt = f"""Generate an ADHD community comment with helpful advice.
Post title: {post_title}

Create a comment that:
- Shares a specific ADHD coping strategy or tip
- Is practical and actionable
- Sounds like it comes from experience
- Is 1-2 sentences

Examples:
- "timers are my best friend, i set one every 15 min to stay on track"
- "the pomodoro technique but make it 10 minutes because adhd brain"
- "i put my meds next to my toothbrush so i never forget them"

Write ONLY the comment text (lowercase):"""
        
        elif comment_type == 'adhd_support':
            prompt = f"""Generate a supportive ADHD community comment.
Post title: {post_title}

Create a comment that:
- Validates their ADHD experience
- Shows genuine understanding
- Is warm and encouraging
- Is 1-2 sentences

Examples:
- "youre not lazy, your brain just works differently and thats okay"
- "getting diagnosed changed everything, suddenly my whole life made sense"
- "this is so validating, thought i was the only one struggling with this"

Write ONLY the comment text (lowercase):"""
        
        elif comment_type == 'planning_tip':
            prompt = f"""Generate a planning/organization tip comment.
Post title: {post_title}

Create a comment that:
- Shares a specific planning technique
- Is practical for ADHD brains
- Sounds experienced
- Is 1-2 sentences

Examples:
- "color coding saved my bujo, visual cues work so well for adhd"
- "simplified my spreads to just daily tasks and it actually works now"
- "digital reminders plus physical planner is the sweet spot for me"

Write ONLY the comment text (lowercase):"""
        
        elif comment_type == 'planning_question':
            prompt = f"""Generate a curious question about planning/organization.
Post title: {post_title}

Ask a genuine question that:
- Shows interest in their system
- Is specific and thoughtful
- Encourages sharing
- Is 1 sentence

Examples:
- "how do you keep up with it consistently? i always forget after a few days"
- "do you use any apps alongside your physical planner?"
- "whats your backup plan when executive dysfunction hits?"

Write ONLY the question (lowercase):"""
        
        elif comment_type == 'value':
            prompt = f"""Generate a VALUABLE Reddit comment that adds real insight or helpful advice.
Post title: {post_title}
Subreddit: r/{subreddit}

Create a comment that:
- Shares useful personal experience or expert knowledge
- Provides practical tips or solutions
- Adds new perspective or information
- Is 2-4 sentences long
- Sounds natural and genuine

Write ONLY the comment text, nothing else."""
        
        elif comment_type == 'funny':
            prompt = f"""Generate a FUNNY Reddit comment that could go viral.
Post title: {post_title}

Create a comment that:
- Makes a clever observation or witty remark
- Uses Reddit humor style
- Is short and punchy (1-2 sentences)
- Could get lots of upvotes

Write ONLY the comment text, nothing else."""
        
        elif comment_type == 'question':
            prompt = f"""Generate a thoughtful QUESTION as a Reddit comment.
Post title: {post_title}
Subreddit: r/{subreddit}

Create a question that:
- Shows genuine curiosity
- Encourages discussion
- Is relevant and specific
- Sounds natural

Write ONLY the question, nothing else."""
        
        else:  # relatable
            prompt = f"""Generate a RELATABLE Reddit comment.
Post title: {post_title}

Create a comment that:
- Shares a similar experience
- Shows empathy or understanding
- Connects with the post emotionally
- Is 1-3 sentences

Write ONLY the comment text, nothing else."""
        
        try:
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a helpful Reddit user. Write natural, engaging comments."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 150
                }
            )
            
            if response.status_code == 200:
                comment = response.json()['choices'][0]['message']['content'].strip()
                
                # Validierung
                if len(comment) < 10:
                    return self.generate_fallback_comment(post_title)
                
                # Füge natürliche Variationen hinzu
                comment = self.add_natural_variations(comment)
                
                print(f"   💬 Typ: {comment_type.upper()}")
                return comment
            else:
                print(f"   ⚠️ API-Fehler: {response.status_code}")
                return self.generate_fallback_comment(post_title)
                
        except Exception as e:
            print(f"   ⚠️ Fehler bei Kommentar-Generierung: {e}")
            return self.generate_fallback_comment(post_title)
    
    def generate_fallback_comment(self, post_title):
        """Generiert ADHD-fokussierte Fallback-Kommentare wenn API fehlschlägt"""
        
        # Analysiere Post-Titel für Kontext
        title_lower = post_title.lower()
        
        # Kontext-spezifische ADHD-Kommentare
        if any(word in title_lower for word in ['medication', 'meds', 'diagnosed', 'diagnosis']):
            fallbacks = [
                "getting diagnosed was so validating, finally everything made sense",
                "the right meds changed my life, hope you find what works for you",
                "diagnosis explained so much about my past struggles",
                "remember meds are just one tool, therapy helps too"
            ]
        elif any(word in title_lower for word in ['focus', 'hyperfocus', 'distracted']):
            fallbacks = [
                "hyperfocus is a blessing and a curse honestly",
                "the adhd tax of losing focus mid-task is real",
                "body doubling helps me stay focused, even virtually",
                "pomodoro timers are the only way i can focus"
            ]
        elif any(word in title_lower for word in ['planner', 'bujo', 'organize', 'system']):
            fallbacks = [
                "simplified systems work best for my adhd brain",
                "i have 5 planners and use none consistently lol",
                "color coding changed the game for me",
                "digital or paper? why not both and use neither properly"
            ]
        elif any(word in title_lower for word in ['late', 'time', 'procrastinat']):
            fallbacks = [
                "time blindness is so real, 5 min feels like 5 hours",
                "i have 20 alarms and still somehow run late",
                "waiting mode is the worst, cant do anything before an appointment",
                "panic monster is my only motivator unfortunately"
            ]
        else:
            # Generelle ADHD-Community Kommentare
            fallbacks = [
                "this is so validating, thought it was just me",
                "the adhd tax is real on this one",
                "felt this in my executive dysfunction",
                "saving this to show my therapist",
                "neurotypicals will never understand this struggle",
                "this is why i love the adhd community",
                "my adhd brain: noted and immediately forgotten"
            ]
        
        comment = random.choice(fallbacks)
        
        # Füge gelegentlich Variationen hinzu
        if random.random() < 0.15:
            starters = ['honestly ', 'okay but ', 'wait ']
            comment = random.choice(starters) + comment
        
        return comment
    
    def add_natural_variations(self, text):
        """Fügt natürliche Variationen zum Text hinzu"""
        
        # IMMER Kleinschreibung am Anfang (außer "I")
        if len(text) > 0 and not text.startswith('I '):
            text = text[0].lower() + text[1:]
        
        # Casual Starter hinzufügen (30% Chance)
        if random.random() < 0.3:
            starter = random.choice(self.casual_starters)
            text = f"{starter} {text}"
        
        # Punkte oft weglassen (50% Chance)
        if random.random() < 0.5 and text.endswith('.'):
            text = text[:-1]
        
        # Casual Ending hinzufügen (25% Chance)
        if random.random() < 0.25:
            ending = random.choice(self.casual_endings)
            text = text.rstrip('.,!?') + f" {ending}"
        
        # Tippfehler (10% Chance pro Wort)
        words = text.split()
        new_words = []
        for word in words:
            if random.random() < 0.1 and word.lower() in self.typos:
                new_words.append(random.choice(self.typos[word.lower()]))
            else:
                new_words.append(word)
        text = ' '.join(new_words)
        
        return text
    
    def post_comment_to_reddit(self, parent, comment_text, dry_run=False):
        """Postet einen Kommentar auf Reddit"""
        if dry_run:
            print(f"   [DRY RUN] Würde kommentieren: {comment_text}")
            return True
        
        try:
            comment = parent.reply(comment_text)
            print(f"   ✅ Kommentar gepostet!")
            print(f"   URL: https://reddit.com{comment.permalink}")
            return True
        except praw.exceptions.RedditAPIException as e:
            for error in e.items:
                if error.error_type == "RATELIMIT":
                    wait_time = int(error.message.split("minute")[0].split()[-1]) * 60
                    print(f"   ⚠️ Rate Limit erreicht. Warte {wait_time} Sekunden...")
                    time.sleep(wait_time + 10)
                    return False
                elif error.error_type == "THREAD_LOCKED":
                    print(f"   ⚠️ Thread ist gesperrt")
                    return False
            print(f"   ❌ Reddit API Fehler: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Fehler beim Posten: {e}")
            return False
    
    def create_smart_comment(self, post_data):
        """Erstellt einen intelligenten Kommentar auf einem Post"""
        try:
            submission = post_data['submission']
            
            # Hole Top-Kommentare für Kontext
            submission.comments.replace_more(limit=0)
            top_comments = submission.comments[:5]
            
            # Finde einen guten Kommentar zum Antworten
            target_comment = None
            for comment in top_comments:
                if hasattr(comment, 'body') and len(comment.body) > 20:
                    target_comment = comment
                    break
            
            # Generiere Kommentar
            comment_text = self.generate_smart_comment(
                post_data['title'],
                "",
                [],
                post_data.get('subreddit', '')
            )
            
            print(f"\n💬 Kommentar: {comment_text}")
            
            # Poste den Kommentar
            if target_comment:
                # Antworte auf Top-Kommentar
                if not self.post_comment_to_reddit(target_comment, comment_text, dry_run=False):
                    return False
            else:
                # Antworte direkt auf Post
                if not self.post_comment_to_reddit(submission, comment_text, dry_run=False):
                    return False
                
            # Markiere als kommentiert
            self.commented_posts.add(post_data['id'])
            self._save_commented_history()
            
            # Speichere generierten Kommentar
            self.save_generated_comment({
                'post_id': post_data['id'],
                'post_title': post_data['title'],
                'post_score': post_data['score'],
                'subreddit': post_data['subreddit'],
                'comment': comment_text,
                'success': True
            })
            
            return True
                
        except Exception as e:
            print(f"❌ Fehler beim Kommentieren: {e}")
            return False
    
    def save_generated_comment(self, comment_data):
        """Speichert generierten Kommentar in organisiertem Ordner"""
        from datetime import datetime
        
        # Erstelle Ordnerstruktur
        base_dir = Path("./generated_comments")
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
        
        # Speichere Kommentar
        file_path = comment_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(comment_data, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def run_comment_loop(self, mode='auto'):
        """Hauptschleife für Kommentare - OHNE TAGESLIMIT"""
        print("\n🤖 KOMMENTAR-BOT - UNLIMITIERT")
        print("="*60)
        print("• Ziel-Subreddits: ADHD-fokussiert")
        print("• Wartezeit zwischen Kommentaren: 5-10 Minuten")
        print("• KEIN TAGESLIMIT")
        print("\nDrücke Ctrl+C zum Beenden")
        print("="*60)
        
        comments_made = 0
        
        try:
            while True:
                print(f"\n📊 Session-Fortschritt: {comments_made} Kommentare erstellt")
                
                # Finde Post zum Kommentieren
                post = self.find_popular_post_to_comment()
                
                if post:
                    print(f"\n📝 Gefunden: {post['title'][:80]}...")
                    print(f"   Subreddit: r/{post['subreddit']}")
                    print(f"   Score: {post['score']}, Kommentare: {post['num_comments']}")
                    
                    # Erstelle und poste Kommentar
                    if self.create_smart_comment(post):
                        comments_made += 1
                        
                        # Wartezeit zwischen Kommentaren (5-10 Minuten)
                        if mode == 'auto':
                            wait_time = random.randint(300, 600)
                            print(f"\n⏳ Warte {wait_time//60} Minuten bis zum nächsten Kommentar...")
                            time.sleep(wait_time)
                        else:
                            # Im Einmal-Modus beenden
                            break
                    else:
                        print("❌ Kommentar fehlgeschlagen, versuche anderen Post...")
                        time.sleep(30)
                else:
                    print("❌ Keine geeigneten Posts gefunden, warte...")
                    time.sleep(300)  # 5 Minuten
                    
        except KeyboardInterrupt:
            print(f"\n\n👋 Kommentar-Loop beendet")
            print(f"📊 Session-Total: {comments_made} Kommentare erstellt")
    
    def show_statistics(self):
        """Zeigt Statistiken über die geladenen Daten"""
        print("\n📊 STATISTIKEN:")
        print(f"Posts gesamt: {len(self.posts)}")
        print(f"Kommentare gesamt: {len(self.comments)}")
        print(f"Benutzer in otherUser.txt: {len(self.users_to_process)}")
        print(f"ADHD-Subreddits verfügbar: {len(self.all_subreddits)}")
        print(f"Bereits kommentierte Posts: {len(self.commented_posts)}")
        
        if self.posts:
            avg_score = sum(p.get('score', 0) for p in self.posts) / len(self.posts)
            print(f"Durchschnittlicher Post-Score: {avg_score:.0f}")

def main():
    """Hauptfunktion"""
    bot = KommentareBot()
    
    print("\n🤖 Kommentare Bot - ADHD Edition (UNLIMITIERT)")
    print("⚠️  NUR FÜR BILDUNGSZWECKE!")
    print("="*50)
    print("• Wartezeit zwischen Kommentaren: 5-10 Minuten")
    print("• KEIN TAGESLIMIT - läuft bis manueller Stop")
    print("• Fokus auf ADHD-Subreddits")
    print("")
    print("Modus wählen:")
    print("1. Automatischer Loop (läuft unbegrenzt)")
    print("2. Einmalige Ausführung (1 Kommentar)")
    print("3. Statistiken anzeigen")
    
    choice = input("\nWahl (1-3): ").strip()
    
    if choice == "1":
        bot.run_comment_loop(mode='auto')
    elif choice == "2":
        bot.run_comment_loop(mode='single')
    elif choice == "3":
        bot.show_statistics()
    else:
        print("Ungültige Auswahl")

if __name__ == "__main__":
    main()