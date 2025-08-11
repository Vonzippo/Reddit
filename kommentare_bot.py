#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Kommentare Bot - Natürliche Kommentar-Generierung
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
        self.base_dir = Path("/Users/patrick/Desktop/Reddit/data")
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
        
        # OpenRouter API Konfiguration
        from config import OPENROUTER_API_KEY
        self.openrouter_api_key = OPENROUTER_API_KEY
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Reddit API Konfiguration mit verbesserter Fehlerbehandlung
        self._init_reddit_connection()
    
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
        """Lädt alle Kommentare"""
        print(f"📂 Lade Daten von: {self.base_dir}")
        
        # Kommentare laden
        if self.comments_dir.exists():
            print(f"  📁 Lade Kommentare aus: {self.comments_dir.name}")
            for comment_folder in sorted(self.comments_dir.iterdir()):
                if comment_folder.is_dir() and comment_folder.name.startswith("comment_"):
                    json_file = comment_folder / "comment_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.comments.append(data)
        
        print(f"✅ Geladen: {len(self.comments)} Kommentare")
    
    def _load_subreddits(self):
        """Lädt alle Target-Subreddits aus den Dateien"""
        self.all_subreddits = []
        
        # Lade aus target_subreddits.txt
        target_file = Path("/Users/patrick/Desktop/Reddit/target_subreddits.txt")
        if target_file.exists():
            with open(target_file, 'r', encoding='utf-8') as f:
                for line in f:
                    sub = line.strip()
                    if sub and not sub.startswith('#'):
                        self.all_subreddits.append(sub)
        
        # Lade aus target_subreddits_extended.txt (ohne Duplikate)
        extended_file = Path("/Users/patrick/Desktop/Reddit/target_subreddits_extended.txt")
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
        history_file = Path("/Users/patrick/Desktop/Reddit/commented_posts.json")
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
        history_file = Path("/Users/patrick/Desktop/Reddit/commented_posts.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump({'posts': list(self.commented_posts)}, f, indent=2)
    
    def _load_daily_stats(self):
        """Lädt tägliche Kommentar-Statistiken"""
        from datetime import datetime
        stats_file = Path("/Users/patrick/Desktop/Reddit/daily_comment_stats.json")
        
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
        stats_file = Path("/Users/patrick/Desktop/Reddit/daily_comment_stats.json")
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
    
    def check_if_already_commented(self, post_id):
        """Prüft ob der Bot bereits auf diesem Post kommentiert hat"""
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)
            
            # Prüfe ob unser Bot bereits kommentiert hat
            for comment in submission.comments.list():
                if comment.author and comment.author.name == "ReddiBoto":
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
    
    def analyze_image_with_ai(self, image_url, post_title):
        """Analysiert ein Bild mit AI und generiert passenden Kommentar"""
        
        # Lade das Bild herunter
        image_base64 = self.download_image(image_url)
        if not image_base64:
            return None
        
        print("🖼️ Analysiere Bild mit AI...")
        
        # Liste von Vision-Modellen (mit API Key keine Rate Limits)
        vision_models = [
            "google/gemini-2.5-flash",      # Neueste Gemini Version
            "openai/gpt-4o-mini",           # Günstig und gut
            "anthropic/claude-3-haiku",     # Schnell und günstig
        ]
        
        # Wähle zufälliges Modell für Load-Balancing
        import random
        selected_model = random.choice(vision_models)
        print(f"   Verwende Modell: {selected_model.split('/')[1].split(':')[0]}")
        
        # Verschiedene Prompt-Stile für natürliche Variation
        prompt_styles = [
            f"""look at this image someone posted on reddit with title: "{post_title}"

write a casual reddit comment reacting to it. be natural, like you're just scrolling and saw this. keep it short, genuine reaction. maybe point out something specific you notice. use reddit slang if it fits naturally

comment:""",
            
            f"""reddit post: "{post_title}"
[image attached]

drop a quick comment like a real redditor would. notice details, be casual, maybe relate to it personally. 1-2 sentences max. dont be too enthusiastic

your reaction:""",
            
            f"""someone posted this pic on reddit: "{post_title}"

comment something relatable or observational. sound like you're typing quick on your phone. natural reaction, not trying too hard

you write:"""
        ]
        
        prompt = random.choice(prompt_styles)
        
        try:
            # Nutze Gemini 2.5 Flash für Bildanalyse
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Kommentare Bot"
                },
                json={
                    "model": selected_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": image_base64}}
                            ]
                        }
                    ],
                    "temperature": random.uniform(0.8, 1.0),
                    "max_tokens": 100
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                generated = result['choices'][0]['message']['content'].strip()
                
                # Entferne Anführungszeichen
                generated = generated.strip('"\'')
                
                # Füge natürliche Variationen hinzu
                return self.add_natural_variations(generated)
            else:
                print(f"❌ AI Fehler: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Bildanalyse fehlgeschlagen: {e}")
        
        return None
    
    def generate_natural_comment(self, post_title, post_body, reference_comments, image_url=None):
        """Generiert einen natürlicheren Kommentar basierend auf Referenzen"""
        
        # Wenn Bild vorhanden, analysiere es
        if image_url:
            image_comment = self.analyze_image_with_ai(image_url, post_title)
            if image_comment:
                return image_comment
        
        # Wähle 2-3 Referenzkommentare für Inspiration
        samples = random.sample(reference_comments, min(3, len(reference_comments)))
        
        # Erstelle verschiedene Prompt-Stile für lustige persönliche Kommentare
        prompt_styles = [
            # Lustige Story als Kommentar (1-4 Sätze!)
            f"""reddit post: "{post_title}"

write a funny comment (1-4 sentences MAXIMUM). include a brief personal story.

style:
- relate to OP  
- share ONE funny/embarrassing moment
- be specific (mention place/time/brand)
- lowercase, casual
- self-deprecating

example: "lol this happened to me at target yesterday. bought 5 plants instead of toilet paper. my bathroom is now a jungle but i'm using napkins."

your comment (1-4 sentences):""",
            
            # Chaotischer aber relevanter Kommentar (1-4 Sätze!)
            f"""post title: "{post_title}"

write a SHORT comment (1-4 sentences MAX) with your own funny fail.

rules:
- acknowledge OP
- share similar embarrassing moment
- mention ONE specific detail (time/place/brand)
- lowercase, casual

1-4 sentences only:""",
            
            # Empathie + Humor Kommentar (1-4 Sätze!)
            f"""someone posted: {post_title}

write a funny supportive comment (1-4 SENTENCES MAX!)

structure:
1. relate ("same" or "felt this")
2. brief embarrassing example
3. end with joke

MUST BE 1-4 SENTENCES. lowercase. one specific detail.

comment:"""
        ]
        
        prompt = random.choice(prompt_styles)
        
        try:
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Kommentare Bot"
                },
                json={
                    "model": "openai/gpt-5",  # GPT-5 für beste Stories
                    "messages": [
                        {"role": "system", "content": "You're a funny redditor. Write SHORT comments (1-4 sentences MAX). Include a brief personal story. Be self-deprecating, use lowercase, casual reddit style."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.1,  # Kreativ aber nicht zu wild
                    "max_tokens": 100,  # Weniger Tokens = kürzere Kommentare
                    "presence_penalty": 0.6,
                    "frequency_penalty": 0.5,
                    "top_p": 0.95
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                generated = result['choices'][0]['message']['content'].strip()
                
                # Entferne Anführungszeichen falls vorhanden
                generated = generated.strip('"\'')
                
                # Füge weitere natürliche Variationen hinzu
                generated = self.add_natural_variations(generated)
                
                return generated
            
        except Exception as e:
            print(f"❌ Generierung fehlgeschlagen: {e}")
        
        # Fallback: Modifiziere einen existierenden Kommentar
        base_comment = random.choice(reference_comments)
        return self.add_natural_variations(base_comment.get('body', '')[:200])
    
    def mix_comments(self, comments):
        """Mischt Teile verschiedener Kommentare für mehr Variation"""
        if len(comments) < 2:
            return comments[0].get('body', '') if comments else ""
        
        # Nimm Anfang von einem, Ende von anderem
        c1, c2 = random.sample(comments, 2)
        text1 = c1.get('body', '')
        text2 = c2.get('body', '')
        
        # Teile die Kommentare
        sentences1 = text1.split('. ')
        sentences2 = text2.split('. ')
        
        if len(sentences1) > 1 and len(sentences2) > 1:
            # Mische Sätze
            mixed = []
            mixed.append(sentences1[0])
            if len(sentences2) > 1:
                mixed.append(sentences2[-1])
            
            result = '. '.join(mixed)
            return self.add_natural_variations(result)
        
        return self.add_natural_variations(text1[:150])
    
    def find_suitable_posts(self, subreddit_name="ADHD", limit=10, sort_by="hot"):
        """Findet neue Posts in einem Subreddit, sortiert nach Score"""
        print(f"\n🔍 Suche nach Posts in r/{subreddit_name} (sortiert nach {sort_by})...")
        
        # Retry bei Verbindungsfehlern
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Kleine Pause vor API-Aufruf
                if attempt > 0:
                    wait_time = attempt * 2
                    print(f"  ⏳ Warte {wait_time} Sekunden vor Retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                
                subreddit = self.reddit.subreddit(subreddit_name)
                posts = []
                
                # Wähle Sortierung
                if sort_by == "hot":
                    submissions = subreddit.hot(limit=limit * 2)  # Hole mehr für Filterung
                elif sort_by == "top":
                    submissions = subreddit.top(time_filter="day", limit=limit * 2)
                else:
                    submissions = subreddit.new(limit=limit * 2)
                
                # Wenn hier angekommen, war Verbindung erfolgreich
                break
                
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠️ Verbindungsfehler, versuche erneut...")
                    continue
                else:
                    print(f"  ❌ Verbindung fehlgeschlagen nach {max_retries} Versuchen")
                    return []
            except Exception as e:
                print(f"❌ Fehler beim Suchen in r/{subreddit_name}: {e}")
                return []
        
        try:
            
            for submission in submissions:
                # Skip wenn bereits kommentiert
                if submission.id in self.commented_posts:
                    print(f"  ⏭️ Überspringe (bereits kommentiert): {submission.title[:40]}...")
                    continue
                
                # Skip wenn Post gesperrt oder archiviert
                if submission.locked:
                    print(f"  🔒 Überspringe (gesperrt): {submission.title[:40]}...")
                    continue
                    
                if submission.archived:
                    print(f"  📁 Überspringe (archiviert): {submission.title[:40]}...")
                    continue
                
                # Skip wenn Bot bereits kommentiert hat
                if self.check_if_already_commented(submission.id):
                    self.commented_posts.add(submission.id)
                    print(f"  ⏭️ Überspringe (Bot hat kommentiert): {submission.title[:40]}...")
                    continue
                
                # Prüfe ob Post ein Bild hat
                image_url = None
                if hasattr(submission, 'url'):
                    url_lower = submission.url.lower()
                    if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                        image_url = submission.url
                    elif 'i.redd.it' in submission.url or 'i.imgur.com' in submission.url:
                        image_url = submission.url
                
                post_info = {
                    'id': submission.id,
                    'title': submission.title,
                    'body': submission.selftext if submission.is_self else None,
                    'url': f"https://reddit.com{submission.permalink}",
                    'image_url': image_url,
                    'num_comments': submission.num_comments,
                    'score': submission.score,
                    'created': submission.created_utc,
                    'is_image': image_url is not None,
                    'upvote_ratio': submission.upvote_ratio
                }
                posts.append(post_info)
                
                if image_url:
                    print(f"  🖼️ Bild-Post (Score: {submission.score}): {submission.title[:40]}...")
                else:
                    print(f"  📝 Text-Post (Score: {submission.score}): {submission.title[:40]}...")
                
                # Stoppe wenn genug Posts gefunden
                if len(posts) >= limit:
                    break
            
            # Sortiere Posts nach Score (höchste zuerst)
            posts.sort(key=lambda x: x['score'], reverse=True)
            
            return posts
        except Exception as e:
            print(f"❌ Fehler beim Suchen in r/{subreddit_name}: {e}")
            return []
    
    def post_comment_real(self, post_id, comment_text, dry_run=True):
        """
        Postet einen Kommentar auf Reddit mit Sicherheitsvorkehrungen
        
        WARNUNG: Automatisiertes Posten verstößt gegen Reddit ToS!
        dry_run=True bedeutet es wird NUR simuliert, nicht wirklich gepostet
        """
        
        # ============================================
        # AUSKOMMENTIERTER POST-CODE - NUR FÜR BILDUNGSZWECKE
        # ============================================
        
        # SICHERHEITS-CHECK 1: Dry Run Modus (Standard)
        if dry_run:
            print("\n⚠️ DRY RUN MODUS - Würde posten aber tut es nicht:")
            print(f"   Post ID: {post_id}")
            print(f"   Kommentar: {comment_text[:100]}...")
            return False
        
        # SICHERHEITS-CHECK 2: Explizite Bestätigung erforderlich
        print("\n🚨 WARNUNG: ECHTER POST-MODUS!")
        print(f"Post ID: {post_id}")
        print(f"Kommentar: {comment_text[:200]}...")
        
        confirm = "JA ICH WILL WIRKLICH POSTEN" #input("\nTippe 'JA ICH WILL WIRKLICH POSTEN' zum Bestätigen: ").strip()
        
        if confirm != "JA ICH WILL WIRKLICH POSTEN":
            print("❌ Abgebrochen - Kommentar wurde NICHT gepostet")
            return False
        
        # SICHERHEITS-CHECK 3: Rate Limiting (10 Minuten zwischen Posts)
        if hasattr(self, 'last_post_time'):
            time_since_last = time.time() - self.last_post_time
            if time_since_last < 600:  # 10 Minuten Mindestabstand
                wait_time = 600 - time_since_last
                print(f"⏰ Rate Limit: Warte noch {wait_time:.0f} Sekunden")
                return False
        
        try:
            # ============================================
            # HIER WÜRDE DER ECHTE POST PASSIEREN:
            # ============================================
            
            # Reddit Submission (Post) finden
            submission = self.reddit.submission(id=post_id)
            
            # Prüfe ob Post gesperrt ist
            submission._fetch()
            if submission.locked:
                print(f"🔒 Post ist gesperrt - keine Kommentare erlaubt")
                return False
            
            if submission.archived:
                print(f"📁 Post ist archiviert - keine Kommentare erlaubt")
                return False
            
            # Kommentar posten
            comment = submission.reply(comment_text)
            
            # Erfolg tracking
            self.last_post_time = time.time()
            self.commented_posts.add(post_id)
            self._save_commented_history()
            
            print(f"✅ Kommentar gepostet!")
            print(f"   Comment ID: {comment.id}")
            print(f"   URL: https://reddit.com{comment.permalink}")
            
            return True
            
        except praw.exceptions.RedditAPIException as e:
            error_msg = str(e)
            if "THREAD_LOCKED" in error_msg:
                print(f"🔒 Post ist gesperrt - keine Kommentare erlaubt")
            elif "DELETED_LINK" in error_msg:
                print(f"🗑️ Post wurde gelöscht")
            elif "THREAD_ARCHIVED" in error_msg:
                print(f"📁 Post ist archiviert (älter als 6 Monate)")
            elif "RATELIMIT" in error_msg:
                print(f"⏱️ Rate Limit erreicht - warte etwas")
            else:
                print(f"❌ Reddit API Fehler: {e}")
            return False
            
        except Exception as e:
            print(f"❌ Unerwarteter Fehler: {e}")
            return False
       
        # ============================================
        # ENDE DES AUSKOMMENTIERTEN POST-CODES
        # ============================================
        
        print("\n📌 POST-FUNKTION IST DEAKTIVIERT (auskommentiert)")
        print("   Um zu aktivieren, entferne die # Zeichen im Code")
        return False
    
    def get_natural_comment(self, post_title, post_body="", image_url=None):
        """Erstellt einen natürlichen Kommentar"""
        
        # Wenn Bild vorhanden, bevorzuge Bildanalyse
        if image_url:
            image_comment = self.analyze_image_with_ai(image_url, post_title)
            if image_comment:
                return image_comment
        
        if not self.comments:
            return None
        
        # Finde relevante Kommentare als Basis
        keywords = post_title.lower().split()
        relevant_comments = []
        
        for comment in self.comments:
            comment_text = comment.get('body', '').lower()
            if any(keyword in comment_text for keyword in keywords[:5]):  # Nur erste 5 Keywords
                relevant_comments.append(comment)
        
        # Wenn keine relevanten gefunden, nimm zufällige
        if not relevant_comments:
            relevant_comments = random.sample(self.comments, min(10, len(self.comments)))
        
        # Entscheide zufällig welche Methode verwendet wird
        method = random.choice(['generate', 'mix', 'modify'])
        
        if method == 'generate':
            # Generiere neuen Kommentar basierend auf Referenzen
            return self.generate_natural_comment(post_title, post_body, relevant_comments, image_url)
        elif method == 'mix':
            # Mische existierende Kommentare
            return self.mix_comments(relevant_comments)
        else:
            # Modifiziere einen existierenden Kommentar
            base = random.choice(relevant_comments)
            return self.add_natural_variations(base.get('body', '')[:250])
    
    def scan_all_subreddits_smart(self, max_subs=10, min_score=10):
        """Durchsucht Subreddits und wählt nur den besten Post pro Subreddit"""
        print("\n🎯 INTELLIGENTER SCAN - Nur beste Posts")
        print("="*60)
        print(f"📋 {len(self.all_subreddits)} Subreddits verfügbar")
        print(f"🎯 Mindest-Score: {min_score}")
        
        best_posts = []
        scanned_count = 0
        skipped_count = 0
        
        # Shuffled für Variation
        shuffled_subs = random.sample(self.all_subreddits, len(self.all_subreddits))
        
        for sub in shuffled_subs:
            if len(best_posts) >= max_subs:
                break
                
            try:
                print(f"\n🔍 Scanne r/{sub}...")
                
                # Hole top Posts des Tages
                posts = self.find_suitable_posts(sub, limit=5, sort_by="hot")
                
                if not posts:
                    print(f"  ⚠️ Keine unkommentierten Posts gefunden")
                    skipped_count += 1
                    continue
                
                # Nimm nur den besten Post (bereits nach Score sortiert)
                best_post = posts[0]
                
                # Skip wenn Score zu niedrig
                if best_post['score'] < min_score:
                    print(f"  ⚠️ Bester Post hat nur Score {best_post['score']} (< {min_score})")
                    skipped_count += 1
                    continue
                
                best_post['subreddit'] = sub
                best_posts.append(best_post)
                
                print(f"  ✅ BESTER POST gefunden:")
                print(f"     Score: {best_post['score']} | Kommentare: {best_post['num_comments']}")
                print(f"     Titel: {best_post['title'][:60]}...")
                
                scanned_count += 1
                
                # Längere Pause zwischen Subreddits um SSL-Fehler zu vermeiden
                time.sleep(random.uniform(2.0, 4.0))
                
            except Exception as e:
                print(f"  ❌ Fehler bei r/{sub}: {str(e)[:50]}")
                continue
        
        # Sortiere finale Liste nach Score
        best_posts.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n📊 ZUSAMMENFASSUNG:")
        print(f"  • Subreddits gescannt: {scanned_count + skipped_count}")
        print(f"  • Erfolgreiche Posts: {len(best_posts)}")
        print(f"  • Übersprungen: {skipped_count}")
        
        if best_posts:
            print(f"\n🏆 TOP 5 POSTS:")
            for i, post in enumerate(best_posts[:5], 1):
                print(f"  {i}. r/{post['subreddit']} - Score: {post['score']}")
                print(f"     {post['title'][:60]}...")
        
        return best_posts
    
    def scan_all_subreddits(self, posts_per_sub=3, max_subs=10):
        """Durchsucht alle Subreddits nach neuen Posts"""
        print("\n🔍 DURCHSUCHE ALLE SUBREDDITS")
        print("="*60)
        print(f"📋 {len(self.all_subreddits)} Subreddits gefunden")
        
        all_posts = []
        scanned_count = 0
        
        # Zufällige Reihenfolge für natürlicheres Verhalten
        shuffled_subs = random.sample(self.all_subreddits, min(max_subs, len(self.all_subreddits)))
        
        for sub in shuffled_subs:
            try:
                print(f"\n🔍 Scanne r/{sub}...")
                posts = self.find_suitable_posts(sub, limit=posts_per_sub, sort_by="hot")
                
                if posts:
                    for post in posts:
                        post['subreddit'] = sub
                        all_posts.append(post)
                    print(f"  ✅ {len(posts)} Posts gefunden")
                else:
                    print(f"  ⚠️ Keine Posts gefunden")
                
                scanned_count += 1
                
                # Kleine Pause zwischen Subreddits
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                print(f"  ❌ Fehler bei r/{sub}: {e}")
                continue
        
        print(f"\n📊 Zusammenfassung:")
        print(f"  • Subreddits gescannt: {scanned_count}")
        print(f"  • Posts gefunden: {len(all_posts)}")
        
        # Zeige Bild vs Text Statistik
        image_posts = [p for p in all_posts if p.get('is_image')]
        print(f"  • Bild-Posts: {len(image_posts)}")
        print(f"  • Text-Posts: {len(all_posts) - len(image_posts)}")
        
        return all_posts
    
    def smart_mode_loop(self, min_score=50, start_hour=10, end_hour=22):
        """
        Läuft automatisch im Loop und generiert Kommentare
        Respektiert tägliches Limit (5-20 Kommentare pro Tag)
        Nur aktiv zwischen start_hour und end_hour (Standard: 10-22 Uhr)
        """
        from datetime import datetime, timedelta
        import time
        
        print("\n🤖 SMART MODE - AUTOMATISCHER LOOP MIT TAGESLIMIT")
        print("="*60)
        print(f"⏰ Aktive Zeit: {start_hour}:00 - {end_hour}:00 Uhr")
        print(f"📊 Tägliches Ziel: {self.daily_target} Kommentare")
        print(f"🎯 Mindest-Score: {min_score}")
        print("\nDrücke Ctrl+C zum Beenden")
        print("="*60)
        
        session_count = 0
        last_comment_time = None
        
        try:
            while True:
                current_hour = datetime.now().hour
                current_time = datetime.now().strftime("%H:%M:%S")
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Prüfe ob neuer Tag
                if today not in self.daily_comments:
                    self._load_daily_stats()
                    if self.daily_target == 0:
                        print(f"\n😴 Heute ist ein Pausentag - keine Kommentare geplant")
                    else:
                        print(f"\n🌅 Neuer Tag! Ziel: {self.daily_target} Kommentare")
                
                # Prüfe ob heute ein Pausentag ist
                if self.daily_target == 0:
                    print(f"\n😴 [{current_time}] Pausentag - warte bis morgen...")
                    # Warte 2 Stunden und prüfe dann ob neuer Tag
                    time.sleep(7200)
                    continue
                
                # Prüfe ob Tageslimit erreicht
                if not self.can_comment_today():
                    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                    wait_seconds = (tomorrow - datetime.now()).total_seconds()
                    hours_to_wait = int(wait_seconds // 3600)
                    minutes_to_wait = int((wait_seconds % 3600) // 60)
                    
                    print(f"\n✅ [{current_time}] Tagesziel erreicht!")
                    print(f"   Warte bis morgen ({hours_to_wait}h {minutes_to_wait}m)")
                    
                    # Warte 1 Stunde und prüfe dann erneut
                    time.sleep(3600)
                    continue
                
                # Prüfe ob in aktiver Zeit
                if current_hour < start_hour or current_hour >= end_hour:
                    print(f"\n😴 [{current_time}] Außerhalb der aktiven Zeit. Warte...")
                    minutes_to_wait = 60 - datetime.now().minute
                    time.sleep(minutes_to_wait * 60)
                    continue
                
                # Berechne wie viele Kommentare noch heute erstellt werden sollen
                current_count = self.get_today_comment_count()
                
                # Stelle sicher dass daily_target gesetzt ist
                if self.daily_target is None:
                    self._load_daily_stats()
                    if self.daily_target is None:
                        self.daily_target = random.randint(5, 20)
                
                remaining_today = self.daily_target - current_count
                active_hours_left = end_hour - current_hour
                
                if remaining_today <= 0:
                    continue
                
                # Verteile verbleibende Kommentare auf verbleibende Stunden
                if active_hours_left > 0:
                    comments_this_hour = max(1, min(3, remaining_today // active_hours_left))
                else:
                    comments_this_hour = min(3, remaining_today)
                
                # Mindestabstand zwischen Kommentaren (15-45 Minuten)
                if last_comment_time:
                    time_since_last = (datetime.now() - last_comment_time).total_seconds()
                    min_wait = random.randint(900, 2700)  # 15-45 Minuten
                    if time_since_last < min_wait:
                        wait_time = int(min_wait - time_since_last)
                        print(f"\n⏳ Warte noch {wait_time//60} Minuten bis zum nächsten Kommentar...")
                        time.sleep(wait_time)
                        continue
                
                print(f"\n🕐 [{current_time}] Erstelle {comments_this_hour} Kommentar(e)")
                print(f"   Tagesfortschritt: {current_count}/{self.daily_target}")
                print("-"*40)
                
                # Generiere Kommentare
                generated = self.generate_comments_smart(
                    max_posts=comments_this_hour,
                    min_score=min_score
                )
                
                if generated:
                    session_count += 1
                    last_comment_time = datetime.now()
                    
                    # Aktualisiere täglichen Zähler
                    for comment in generated:
                        self.increment_daily_count(comment)
                    
                    print(f"\n✅ {len(generated)} Kommentar(e) erstellt")
                    
                    # Speichere Session-Log
                    self._save_session_log(session_count, generated)
                    
                    # Wenn Tageslimit erreicht, melde es
                    if not self.can_comment_today():
                        print(f"\n🎉 Tagesziel erreicht! Bis morgen!")
                else:
                    print("\n⚠️ Keine passenden Posts gefunden")
                
                # Zufällige Wartezeit (20-60 Minuten)
                wait_minutes = random.randint(20, 60)
                print(f"\n⏰ Warte {wait_minutes} Minuten bis zur nächsten Prüfung...")
                
                # Zeige Countdown
                for i in range(wait_minutes):
                    remaining = wait_minutes - i
                    print(f"\r   ⏳ Noch {remaining} Minuten...", end="", flush=True)
                    time.sleep(60)  # 1 Minute
                
        except KeyboardInterrupt:
            current_count = self.get_today_comment_count()
            print(f"\n\n👋 Loop beendet")
            print(f"📊 Heute erstellt: {current_count}/{self.daily_target} Kommentare")
            print(f"   Sessions heute: {session_count}")
    
    def _save_session_log(self, session_num, comments):
        """Speichert Log der aktuellen Session"""
        from datetime import datetime
        
        log_file = Path("/Users/patrick/Desktop/Reddit/smart_mode_sessions.json")
        
        # Lade existierende Sessions
        sessions = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    sessions = json.load(f)
            except:
                sessions = []
        
        # Füge neue Session hinzu
        sessions.append({
            'session': session_num,
            'timestamp': datetime.now().isoformat(),
            'comments_count': len(comments),
            'comments': comments
        })
        
        # Speichere
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
    
    def save_generated_comment(self, comment_data):
        """Speichert generierten Kommentar in organisiertem Ordner"""
        from datetime import datetime
        
        # Erstelle Ordnerstruktur: generated_comments/YYYY-MM/DD/
        base_dir = Path("/Users/patrick/Desktop/Reddit/generated_comments")
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
    
    def generate_comments_smart(self, max_posts=10, min_score=10):
        """Generiert Kommentare nur für die besten Posts"""
        print("\n🤖 INTELLIGENTE KOMMENTAR-GENERIERUNG")
        print("="*60)
        
        # Prüfe ob heute ein Pausentag ist
        if self.daily_target == 0:
            print("😴 Heute ist ein Pausentag - keine Kommentare werden generiert")
            return []
        
        # Sammle beste Posts
        best_posts = self.scan_all_subreddits_smart(max_subs=max_posts, min_score=min_score)
        
        if not best_posts:
            print("❌ Keine geeigneten Posts gefunden")
            return []
        
        print(f"\n💬 Generiere Kommentare für {len(best_posts)} Top-Posts:")
        print("-"*60)
        
        generated_comments = []
        
        for i, post in enumerate(best_posts, 1):
            print(f"\n{i}. r/{post['subreddit']} (Score: {post['score']})")
            
            if post.get('is_image'):
                print(f"   🖼️ BILD: {post['title'][:60]}...")
            else:
                print(f"   📝 TEXT: {post['title'][:60]}...")
            
            # Generiere Kommentar
            comment = self.get_natural_comment(
                post['title'],
                post.get('body', ''),
                post.get('image_url')
            )
            
            print(f"   💬 Kommentar: {comment}")
            print(f"   📊 Stats: {post['num_comments']} Kommentare | {post.get('upvote_ratio', 0)*100:.0f}% upvoted")
            
            # Speichere für späteren Post
            comment_data = {
                'post_id': post['id'],
                'subreddit': post['subreddit'],
                'post_title': post['title'],
                'post_url': post.get('url', ''),
                'comment': comment,
                'post_score': post['score'],
                'is_image': post.get('is_image', False)
            }
            generated_comments.append(comment_data)
            
            # Speichere in Ordnerstruktur
            saved_path = self.save_generated_comment(comment_data)
            print(f"   💾 Gespeichert: {saved_path.name}")
            
            # Markiere als kommentiert (für Simulation)
            self.commented_posts.add(post['id'])
        
        # Speichere Historie
        self._save_commented_history()
        
        # Erstelle tägliche Zusammenfassung
        if generated_comments:
            from datetime import datetime
            summary_dir = Path("/Users/patrick/Desktop/Reddit/generated_comments/daily_summaries")
            summary_dir.mkdir(parents=True, exist_ok=True)
            
            date_str = datetime.now().strftime('%Y-%m-%d')
            summary_file = summary_dir / f"summary_{date_str}.json"
            
            # Lade existierende Summary wenn vorhanden
            existing_summary = []
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    existing_summary = json.load(f)
            
            # Füge neue Kommentare hinzu
            existing_summary.extend(generated_comments)
            
            # Speichere aktualisierte Summary
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(existing_summary, f, indent=2, ensure_ascii=False)
            
            print(f"\n📊 Tägliche Zusammenfassung aktualisiert: {summary_file.name}")
        
        # ============================================
        # OPTIONAL: Posts an Reddit senden (AUSKOMMENTIERT)
        # ============================================
        
        if generated_comments:
            print("\n" + "="*60)
            print("🚨 POST-MODUS VERFÜGBAR")
            print("="*60)
            
            post_mode = "real"

            if post_mode == "test":
                print("\n🧪 TEST-MODUS (Dry Run - nichts wird gepostet):")
                for i, item in enumerate(generated_comments[:3], 1):
                    print(f"\n{i}. Test für r/{item['subreddit']}:")
                    self.post_comment_real(
                        item['post_id'], 
                        item['comment'],
                        dry_run=True  # NUR SIMULATION
                    )
            
            elif post_mode == "real":
                print("\n⚠️ WARNUNG: ECHTER POST-MODUS!")
                print("Dies verstößt gegen Reddit Terms of Service!")
                print("Dein Account kann permanent gebannt werden!")
                
                final_confirm ="ICH VERSTEHE DIE RISIKEN"
                
                if final_confirm == "ICH VERSTEHE DIE RISIKEN":
                    #max_posts = input("Wie viele posten? (max 3): ").strip()
                    max_posts = "1"
                    max_posts = min(int(max_posts) if max_posts.isdigit() else 1, 3)
                    
                    for i, item in enumerate(generated_comments[:max_posts], 1):
                        print(f"\n📮 Poste {i}/{max_posts}...")
                        success = self.post_comment_real(
                            item['post_id'],
                            item['comment'],
                            dry_run=False  # ECHTER POST!
                        )
                        
                        if success and i < max_posts:
                            wait_time = 610  # 10+ Minuten
                            print(f"⏰ Warte {wait_time} Sekunden bis zum nächsten Post...")
                            time.sleep(wait_time)
                else:
                    print("✅ Abgebrochen - Keine Posts")
            else:
                print("✅ Übersprungen - Keine Posts")
        
        # ============================================
        # ENDE DES AUSKOMMENTIERTEN POST-CODES
        # ============================================
        
        return generated_comments
    
    def generate_comments_for_all(self, limit_subs=5, posts_per_sub=2):
        """Generiert Kommentare für Posts aus allen Subreddits"""
        print("\n🤖 GENERIERE KOMMENTARE FÜR ALLE SUBREDDITS")
        print("="*60)
        
        # Sammle Posts von verschiedenen Subreddits
        all_posts = self.scan_all_subreddits(posts_per_sub, limit_subs)
        
        if not all_posts:
            print("❌ Keine Posts gefunden")
            return
        
        # Mische Posts für Variation
        random.shuffle(all_posts)
        
        print(f"\n💬 Generiere Kommentare für {len(all_posts)} Posts:")
        print("-"*60)
        
        for i, post in enumerate(all_posts[:10], 1):  # Maximal 10 zeigen
            print(f"\n{i}. r/{post['subreddit']}")
            
            if post.get('is_image'):
                print(f"   🖼️ BILD: {post['title'][:60]}...")
            else:
                print(f"   📝 TEXT: {post['title'][:60]}...")
            
            # Generiere Kommentar
            comment = self.get_natural_comment(
                post['title'],
                post.get('body', ''),
                post.get('image_url')
            )
            
            print(f"   💬 Kommentar: {comment}")
            print(f"   📊 Post-Stats: {post['score']} Punkte, {post['num_comments']} Kommentare")
    
    def test_mode_improved(self):
        """Test-Modus mit verbesserten natürlichen Kommentaren"""
        print("\n🧪 TEST-MODUS - Verbesserte natürliche Kommentare mit Bildanalyse")
        print("="*60)
        
        # Option für alle Subreddits oder nur ausgewählte
        print("\nWas möchtest du testen?")
        print("1. Nur ADHD-Subreddits (schnell)")
        print("2. Alle Subreddits durchsuchen")
        
        choice = input("\nWahl (1-2): ").strip()
        
        if choice == "2":
            # Durchsuche alle Subreddits
            self.generate_comments_for_all(limit_subs=10, posts_per_sub=2)
        else:
            # Original: Nur ADHD Subreddits
            target_subreddits = ["ADHD", "ADHDmemes", "adhdwomen"]
            
            for sub in target_subreddits[:1]:  # Nur erstes zum Testen
                posts = self.find_suitable_posts(sub, limit=5)
                
                if posts:
                    print(f"\n📌 Beispiele für r/{sub}:")
                    for post in posts:
                        if post.get('is_image'):
                            print(f"\n  🖼️ BILD-POST: {post['title'][:80]}...")
                            print(f"     Bild-URL: {post['image_url']}")
                        else:
                            print(f"\n  📝 TEXT-POST: {post['title'][:80]}...")
                        
                        # Generiere passenden Kommentar
                        print(f"  💬 Generierter Kommentar:")
                        comment = self.get_natural_comment(
                            post['title'], 
                            post.get('body', ''),
                            post.get('image_url')
                        )
                        print(f"     {comment}")
                        print()
    
    def compare_old_vs_new(self):
        """Vergleicht alte vs neue Kommentar-Generierung"""
        print("\n🔬 VERGLEICH: Alt vs Neu (mit Bildanalyse)")
        print("="*60)
        
        # Hole Posts (bevorzuge Bilder)
        posts = self.find_suitable_posts("ADHDmemes", limit=5)
        
        # Finde einen Bild-Post wenn möglich
        image_post = None
        text_post = None
        for p in posts:
            if p.get('is_image') and not image_post:
                image_post = p
            elif not p.get('is_image') and not text_post:
                text_post = p
        
        if image_post:
            print(f"\n🖼️ BILD-POST: {image_post['title']}")
            print(f"   URL: {image_post['image_url']}")
            
            # Alter Stil: Zufälliger Kommentar
            if self.comments:
                old_comment = random.choice(self.comments)
                print(f"\n❌ ALTER STIL (zufällig aus Datenbank):")
                print(f"   {old_comment.get('body', '')[:200]}...")
            
            # Neuer Stil mit Bildanalyse
            new_comment = self.get_natural_comment(
                image_post['title'], 
                image_post.get('body', ''),
                image_post.get('image_url')
            )
            print(f"\n✅ NEUER STIL (mit Bildanalyse):")
            print(f"   {new_comment}")
        
        if text_post and self.comments:
            print(f"\n📝 TEXT-POST: {text_post['title']}")
            
            # Zeige Varianten für Text-Post
            print(f"\n🎯 Kommentar-Varianten für Text:")
            for i in range(2):
                variant = self.get_natural_comment(
                    text_post['title'], 
                    text_post.get('body', '')
                )
                print(f"   {i+1}. {variant}")

def main():
    """Hauptfunktion"""
    bot = KommentareBot()
    
    print("\n🤖 Kommentare Bot - Mit Bildanalyse & Smart Scoring")
    print("⚠️  NUR FÜR BILDUNGSZWECKE!")
    print("\nWas möchtest du tun?")
    print("1. 🎯 SMART MODE - Nur beste Posts kommentieren")
    print("2. 📊 Normale Subreddit-Durchsuchung")
    print("3. 🧪 Test-Modus (einzelne Subreddits)")
    print("4. 🔬 Vergleich: Alt vs Neu")
    print("5. 🖼️ Teste Bildanalyse")
    print("6. 📋 Zeige alle Subreddits")
    print("7. 📈 Statistiken & Historie")
    
    choice = input("\nAuswahl (1-7): ").strip()
    
    if choice == "1":
        # SMART MODE - Automatischer Loop mit Tageslimit
        print("\n🎯 SMART MODE - Automatischer Loop mit Tageslimit")
        print("="*60)
        print("Dieser Modus läuft automatisch:")
        # Stelle sicher dass daily_target gesetzt ist
        if bot.daily_target is None:
            bot.daily_target = random.randint(5, 20)
        print(f"• Tägliches Ziel: {bot.daily_target} Kommentare (zufällig 5-20)")
        print(f"• Heute bereits: {bot.get_today_comment_count()} Kommentare")
        print("• Aktiv von 10:00 - 22:00 Uhr")
        print("• Mindest-Score: 50")
        print("• Wartezeit zwischen Kommentaren: 15-45 Minuten")
        print("• Speichert alle Sessions automatisch")
        
        print("\nModus wählen:")
        print("1. Automatischer Loop (empfohlen)")
        print("2. Einmalige Ausführung (respektiert Tageslimit)")
        
        mode = input("\nWahl (1-2): ").strip()
        
        if mode == "1":
            # Automatischer Loop
            print("\n🚀 Starte automatischen Loop mit Tageslimit...")
            bot.smart_mode_loop(
                min_score=50,  # Immer 50
                start_hour=10,
                end_hour=22
            )
        else:
            # Einmalige Ausführung mit Limit-Check
            if not bot.can_comment_today():
                print("\n⚠️ Tageslimit bereits erreicht! Versuche es morgen wieder.")
            else:
                # Stelle sicher dass daily_target gesetzt ist
                if bot.daily_target is None:
                    bot.daily_target = random.randint(5, 20)
                remaining = bot.daily_target - bot.get_today_comment_count()
                comments_to_make = min(2, remaining)
                print(f"\n📝 Erstelle {comments_to_make} Kommentar(e)...")
                
                results = bot.generate_comments_smart(max_posts=comments_to_make, min_score=50)
                
                if results:
                    for comment in results:
                        bot.increment_daily_count(comment)
                    print(f"\n✅ {len(results)} Kommentar(e) generiert!")
                    print(f"   Tagesfortschritt: {bot.get_today_comment_count()}/{bot.daily_target}")
                
    elif choice == "2":
        # Normale Durchsuchung
        print("\n📊 NORMALE SUBREDDIT-DURCHSUCHUNG")
        print(f"Verfügbare Subreddits: {len(bot.all_subreddits)}")
        
        num_subs = input(f"Wie viele Subreddits? (1-{len(bot.all_subreddits)}, Enter für 20): ").strip()
        num_subs = int(num_subs) if num_subs else 20
        
        posts_per = input("Posts pro Subreddit? (Enter für 3): ").strip()
        posts_per = int(posts_per) if posts_per else 3
        
        bot.generate_comments_for_all(limit_subs=num_subs, posts_per_sub=posts_per)
        
    elif choice == "3":
        bot.compare_old_vs_new()
    elif choice == "4":
        # Teste mit spezifischem Bild
        print("\n🖼️ Test mit spezifischem Bild")
        image_url = input("Bild-URL eingeben: ").strip()
        title = input("Post-Titel eingeben: ").strip()
        
        if image_url and title:
            print("\n🤖 Analysiere Bild und generiere Kommentar...")
            comment = bot.analyze_image_with_ai(image_url, title)
            if comment:
                print(f"\n💬 Generierter Kommentar:")
                print(f"   {comment}")
            else:
                print("❌ Bildanalyse fehlgeschlagen")
        else:
            print("❌ Bild-URL und Titel erforderlich")
    elif choice == "5":
        # Zeige alle Subreddits
        print(f"\n📋 ALLE {len(bot.all_subreddits)} VERFÜGBAREN SUBREDDITS:")
        print("="*60)
        
        # Gruppiere nach Kategorien (basierend auf Keywords)
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
                    
    elif choice == "6":
        sub = input("Subreddit Name (z.B. ADHDmemes): ").strip()
        bot.find_suitable_posts(sub, limit=5)
    elif choice == "7":
        print(f"\n📊 Statistiken:")
        print(f"Kommentare geladen: {len(bot.comments)}")
        print(f"Subreddits verfügbar: {len(bot.all_subreddits)}")
        if bot.comments:
            avg_score = sum(c.get('score', 0) for c in bot.comments) / len(bot.comments)
            print(f"Durchschnittlicher Score: {avg_score:.0f}")
    else:
        print("Ungültige Auswahl")

if __name__ == "__main__":
    main()