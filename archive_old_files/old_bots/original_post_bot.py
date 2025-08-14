#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Original Post Bot - Erstellt eigene, originale Reddit Posts
Nutzt archivierte Posts nur als Inspiration
"""

import json
import random
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta

class OriginalPostBot:
    def __init__(self):
        self.base_dir = Path("/Users/patrick/Desktop/Reddit/data")
        self.posts_dir = self.base_dir / "Posts"
        self.archive_posts = []  # Archivierte Posts als Inspiration
        self._load_archive_posts()
        
        # Tägliches Post-Tracking
        self.daily_posts = {}
        self.daily_target = None
        self._load_daily_stats()
        
        # Track bereits gepostete Inhalte
        self.posted_titles = set()
        self._load_posted_history()
        
        # OpenRouter API für Content-Generierung
        from config import OPENROUTER_API_KEY
        self.openrouter_api_key = OPENROUTER_API_KEY
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Reddit API
        self._init_reddit_connection()
        
        # Target Subreddits für verschiedene Themen
        self.subreddit_themes = {
            'adhd': ['ADHD', 'ADHDmemes', 'adhdwomen', 'AdultADHD'],
            'productivity': ['GetDisciplined', 'productivity', 'selfimprovement'],
            'mental_health': ['mentalhealth', 'Anxiety', 'depression_help'],
            'life': ['CasualConversation', 'offmychest', 'TrueOffMyChest'],
            'work': ['jobs', 'WorkReform', 'careerguidance'],
            'creative': ['WritingPrompts', 'ArtTherapy', 'crafts']
        }
    
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
    
    def _load_archive_posts(self):
        """Lädt archivierte Posts als Inspiration"""
        print(f"📂 Lade Inspiration aus: {self.posts_dir}")
        
        if self.posts_dir.exists():
            for post_folder in sorted(self.posts_dir.iterdir())[:500]:  # Maximal 500 laden
                if post_folder.is_dir() and post_folder.name.startswith("post_"):
                    json_file = post_folder / "post_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Nur hochwertige Posts als Inspiration
                            if data.get('score', 0) > 100:
                                self.archive_posts.append(data)
        
        print(f"✅ {len(self.archive_posts)} Inspirations-Posts geladen")
    
    def _load_daily_stats(self):
        """Lädt tägliche Post-Statistiken"""
        stats_file = Path("/Users/patrick/Desktop/Reddit/original_post_stats.json")
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.daily_posts = json.load(f)
            except:
                self.daily_posts = {}
        else:
            self.daily_posts = {}
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today in self.daily_posts:
            self.daily_target = self.daily_posts[today].get('target', 0)
            print(f"📊 Heutiges Ziel: {self.daily_target} Posts")
        else:
            # 15% Chance für Pausentag
            if random.random() < 0.15:
                self.daily_target = 0
                self.daily_posts[today] = {'target': 0, 'count': 0, 'posts': [], 'skip_day': True}
                print(f"😴 Heute ist ein Pausentag")
            else:
                self.daily_target = random.randint(1, 4)
                self.daily_posts[today] = {'target': self.daily_target, 'count': 0, 'posts': []}
                print(f"🎯 Tagesziel: {self.daily_target} originale Posts")
            self._save_daily_stats()
    
    def _save_daily_stats(self):
        """Speichert tägliche Statistiken"""
        stats_file = Path("/Users/patrick/Desktop/Reddit/original_post_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.daily_posts, f, indent=2, ensure_ascii=False)
    
    def _load_posted_history(self):
        """Lädt Historie der geposteten Titel"""
        history_file = Path("/Users/patrick/Desktop/Reddit/original_posted.json")
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.posted_titles = set(data.get('titles', []))
            except:
                self.posted_titles = set()
    
    def _save_posted_history(self):
        """Speichert Historie"""
        history_file = Path("/Users/patrick/Desktop/Reddit/original_posted.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump({'titles': list(self.posted_titles)}, f, indent=2)
    
    def generate_original_post(self, theme='random', subreddit=None):
        """Generiert einen komplett originalen Post"""
        
        # Wähle Thema und Subreddit
        if theme == 'random':
            theme = random.choice(list(self.subreddit_themes.keys()))
        
        if not subreddit:
            subreddit = random.choice(self.subreddit_themes[theme])
        
        # Hole 3-5 Inspirations-Posts aus ähnlichen Subreddits
        inspirations = []
        for post in random.sample(self.archive_posts, min(50, len(self.archive_posts))):
            if any(sub in post.get('subreddit', '') for sub in self.subreddit_themes[theme]):
                inspirations.append(post)
                if len(inspirations) >= 5:
                    break
        
        # Generiere originalen Content basierend auf Thema
        if theme == 'adhd':
            return self.generate_adhd_post(subreddit, inspirations)
        elif theme == 'productivity':
            return self.generate_productivity_post(subreddit, inspirations)
        elif theme == 'mental_health':
            return self.generate_mental_health_post(subreddit, inspirations)
        elif theme == 'life':
            return self.generate_life_post(subreddit, inspirations)
        elif theme == 'work':
            return self.generate_work_post(subreddit, inspirations)
        elif theme == 'creative':
            return self.generate_creative_post(subreddit, inspirations)
        else:
            return self.generate_general_post(subreddit, inspirations)
    
    def generate_adhd_post(self, subreddit, inspirations):
        """Generiert ADHD-bezogenen Content"""
        
        post_types = [
            'relatable_moment',
            'tip_sharing',
            'question',
            'victory',
            'struggle'
        ]
        
        post_type = random.choice(post_types)
        
        # Erstelle Prompts basierend auf Post-Typ
        prompts = {
            'relatable_moment': """Write a relatable ADHD moment post for Reddit. Be authentic and personal.
Examples of good titles:
- "That moment when you clean the entire house to avoid one simple task"
- "Started making coffee, ended up reorganizing my bookshelf"
- "Why do I have 47 browser tabs open?"

Create a NEW, ORIGINAL title and short text (2-3 sentences) about a relatable ADHD experience.
Make it genuine, slightly humorous, and very relatable.

Format:
Title: [your title]
Text: [your text]""",

            'tip_sharing': """Share a helpful ADHD life hack or tip. Be practical and specific.
Examples of good titles:
- "Game changer: Setting timers for EVERYTHING"
- "Finally found a morning routine that works"
- "This one trick helped my executive dysfunction"

Create a NEW, ORIGINAL tip with title and explanation (3-4 sentences).

Format:
Title: [your title]
Text: [your text]""",

            'question': """Ask an engaging question to the ADHD community.
Examples:
- "What's your weirdest hyperfocus?"
- "How do you explain ADHD to people who don't have it?"
- "What's your most ADHD kitchen mishap?"

Create a NEW, ORIGINAL question with brief context (1-2 sentences).

Format:
Title: [your question]
Text: [brief context]""",

            'victory': """Share an ADHD victory or accomplishment.
Examples:
- "Finally finished a project I started 6 months ago!"
- "Remembered my appointment WITHOUT any reminders"
- "Made it through a whole movie without checking my phone"

Create a NEW, ORIGINAL victory post. Be proud but humble.

Format:
Title: [your victory]
Text: [brief story, 2-3 sentences]""",

            'struggle': """Share a current ADHD struggle (seeking support/validation).
Examples:
- "Anyone else struggling with sleep schedules?"
- "The rejection sensitivity is hitting hard today"
- "Task paralysis is real"

Create a NEW, ORIGINAL post about a struggle. Be vulnerable but not too heavy.

Format:
Title: [your struggle]
Text: [brief explanation, 2-3 sentences]"""
        }
        
        # Nutze AI zur Generierung
        try:
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3-haiku",
                    "messages": [
                        {"role": "system", "content": "You're a genuine Reddit user with ADHD sharing experiences. Be authentic, relatable, and use casual language."},
                        {"role": "user", "content": prompts[post_type]}
                    ],
                    "temperature": 0.9,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse Title und Text
                lines = content.strip().split('\n')
                title = ""
                text = ""
                
                for line in lines:
                    if line.startswith('Title:'):
                        title = line.replace('Title:', '').strip()
                    elif line.startswith('Text:'):
                        text = line.replace('Text:', '').strip()
                
                # Stelle sicher dass Titel unique ist
                if title in self.posted_titles:
                    # Modifiziere leicht
                    title = title + " (Update)"
                
                return {
                    'title': title,
                    'selftext': text,
                    'subreddit': subreddit,
                    'is_original': True,
                    'theme': 'adhd',
                    'type': post_type
                }
            
        except Exception as e:
            print(f"❌ Fehler bei Content-Generierung: {e}")
        
        # Fallback
        return None
    
    def generate_productivity_post(self, subreddit, inspirations):
        """Generiert Productivity Content"""
        
        prompts = [
            """Share a productivity win or technique that worked for you.
Be specific and actionable. Include personal experience.

Format:
Title: [specific technique or win]
Text: [how it helped you, 2-3 sentences]""",

            """Ask for productivity advice on a specific challenge.
Be clear about your situation.

Format:
Title: [your specific challenge/question]
Text: [brief context, 2-3 sentences]"""
        ]
        
        try:
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3-haiku",
                    "messages": [
                        {"role": "system", "content": "You're a Reddit user interested in productivity and self-improvement. Be genuine and helpful."},
                        {"role": "user", "content": random.choice(prompts)}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                lines = content.strip().split('\n')
                title = ""
                text = ""
                
                for line in lines:
                    if line.startswith('Title:'):
                        title = line.replace('Title:', '').strip()
                    elif line.startswith('Text:'):
                        text = line.replace('Text:', '').strip()
                
                return {
                    'title': title,
                    'selftext': text,
                    'subreddit': subreddit,
                    'is_original': True,
                    'theme': 'productivity'
                }
        
        except Exception as e:
            print(f"❌ Fehler: {e}")
        
        return None
    
    def generate_mental_health_post(self, subreddit, inspirations):
        """Generiert Mental Health Content (supportive)"""
        
        prompt = """Write a supportive mental health post. Options:
1. Share a small victory or progress
2. Offer encouragement to others
3. Share a helpful coping strategy

Be genuine, supportive, and hopeful without being preachy.

Format:
Title: [your title]
Text: [your message, 2-4 sentences]"""
        
        try:
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3-haiku",
                    "messages": [
                        {"role": "system", "content": "You're a supportive Reddit user sharing mental health experiences. Be kind, genuine, and helpful."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                lines = content.strip().split('\n')
                title = ""
                text = ""
                
                for line in lines:
                    if line.startswith('Title:'):
                        title = line.replace('Title:', '').strip()
                    elif line.startswith('Text:'):
                        text = line.replace('Text:', '').strip()
                
                return {
                    'title': title,
                    'selftext': text,
                    'subreddit': subreddit,
                    'is_original': True,
                    'theme': 'mental_health'
                }
        
        except Exception as e:
            print(f"❌ Fehler: {e}")
        
        return None
    
    def generate_life_post(self, subreddit, inspirations):
        """Generiert allgemeine Life/Casual Posts"""
        
        prompts = [
            """Share an interesting observation or shower thought about daily life.
Be relatable and slightly philosophical or funny.

Format:
Title: [your observation]
Text: [brief elaboration, 2-3 sentences]""",

            """Share a small life moment that made you smile or think.
Be genuine and relatable.

Format:
Title: [your moment]
Text: [what happened and why it mattered, 2-3 sentences]""",

            """Ask a casual, engaging question about life or daily experiences.

Format:
Title: [your question]
Text: [brief context or your thoughts, 1-2 sentences]"""
        ]
        
        try:
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3-haiku",
                    "messages": [
                        {"role": "system", "content": "You're a thoughtful Reddit user sharing life observations. Be relatable and engaging."},
                        {"role": "user", "content": random.choice(prompts)}
                    ],
                    "temperature": 0.9,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                lines = content.strip().split('\n')
                title = ""
                text = ""
                
                for line in lines:
                    if line.startswith('Title:'):
                        title = line.replace('Title:', '').strip()
                    elif line.startswith('Text:'):
                        text = line.replace('Text:', '').strip()
                
                return {
                    'title': title,
                    'selftext': text,
                    'subreddit': subreddit,
                    'is_original': True,
                    'theme': 'life'
                }
        
        except Exception as e:
            print(f"❌ Fehler: {e}")
        
        return None
    
    def generate_work_post(self, subreddit, inspirations):
        """Generiert Work/Career Posts"""
        
        prompt = """Write a work-related post. Options:
1. Share a work situation seeking advice
2. Share a work win or lesson learned
3. Ask about career development

Be professional but casual. Include relevant details.

Format:
Title: [your title]
Text: [your content, 3-4 sentences]"""
        
        try:
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3-haiku",
                    "messages": [
                        {"role": "system", "content": "You're a Reddit user discussing work and career topics. Be professional but relatable."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                lines = content.strip().split('\n')
                title = ""
                text = ""
                
                for line in lines:
                    if line.startswith('Title:'):
                        title = line.replace('Title:', '').strip()
                    elif line.startswith('Text:'):
                        text = line.replace('Text:', '').strip()
                
                return {
                    'title': title,
                    'selftext': text,
                    'subreddit': subreddit,
                    'is_original': True,
                    'theme': 'work'
                }
        
        except Exception as e:
            print(f"❌ Fehler: {e}")
        
        return None
    
    def generate_creative_post(self, subreddit, inspirations):
        """Generiert Creative Content"""
        
        if subreddit == 'WritingPrompts':
            prompt = """Create an original writing prompt that would inspire stories.
Make it intriguing and open-ended.

Format:
Title: [WP] [your prompt]
Text: [optional additional context, 1-2 sentences]"""
        else:
            prompt = """Share a creative project or idea.
Be enthusiastic and descriptive.

Format:
Title: [your project/idea]
Text: [description and what inspired you, 2-3 sentences]"""
        
        try:
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3-haiku",
                    "messages": [
                        {"role": "system", "content": "You're a creative Reddit user. Be imaginative and engaging."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                lines = content.strip().split('\n')
                title = ""
                text = ""
                
                for line in lines:
                    if line.startswith('Title:'):
                        title = line.replace('Title:', '').strip()
                    elif line.startswith('Text:'):
                        text = line.replace('Text:', '').strip()
                
                return {
                    'title': title,
                    'selftext': text if text else "",
                    'subreddit': subreddit,
                    'is_original': True,
                    'theme': 'creative'
                }
        
        except Exception as e:
            print(f"❌ Fehler: {e}")
        
        return None
    
    def generate_general_post(self, subreddit, inspirations):
        """Fallback für allgemeine Posts"""
        return self.generate_life_post(subreddit, inspirations)
    
    def create_post(self, post_data):
        """Postet auf Reddit"""
        if self.daily_target == 0:
            print("😴 Heute ist ein Pausentag")
            return False
        
        try:
            subreddit = self.reddit.subreddit(post_data['subreddit'])
            
            # Erstelle Post
            submission = subreddit.submit(
                title=post_data['title'],
                selftext=post_data.get('selftext', '')
            )
            
            print(f"✅ Original-Post erstellt!")
            print(f"   Titel: {post_data['title']}")
            print(f"   Subreddit: r/{post_data['subreddit']}")
            print(f"   URL: https://reddit.com{submission.permalink}")
            
            # Tracking
            self.posted_titles.add(post_data['title'])
            self._save_posted_history()
            
            # Speichere Post
            self.save_post(post_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            return False
    
    def save_post(self, post_data):
        """Speichert generierten Post"""
        base_dir = Path("/Users/patrick/Desktop/Reddit/original_posts")
        date_now = datetime.now()
        
        post_dir = base_dir / date_now.strftime("%Y-%m") / date_now.strftime("%d")
        post_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"post_{date_now.strftime('%H%M%S')}_{post_data.get('subreddit')}.json"
        
        post_data['created_at'] = date_now.isoformat()
        
        with open(post_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
    
    def run_loop(self):
        """Hauptloop"""
        print("\n🤖 ORIGINAL POST BOT")
        print("="*60)
        print(f"📊 Tagesziel: {self.daily_target} Posts")
        
        if self.daily_target == 0:
            print("😴 Heute ist Pausentag")
            return
        
        posted_today = 0
        themes = list(self.subreddit_themes.keys())
        
        while posted_today < self.daily_target:
            # Wähle zufälliges Thema
            theme = random.choice(themes)
            
            print(f"\n🎨 Generiere {theme} Post...")
            post = self.generate_original_post(theme)
            
            if post and post['title']:
                print(f"📝 Generiert: {post['title'][:60]}...")
                if self.create_post(post):
                    posted_today += 1
                    print(f"   Fortschritt: {posted_today}/{self.daily_target}")
                    
                    if posted_today < self.daily_target:
                        wait = random.randint(1800, 7200)  # 30min - 2h
                        print(f"⏰ Warte {wait//60} Minuten...")
                        time.sleep(wait)
            else:
                print("❌ Generierung fehlgeschlagen")
                time.sleep(60)
        
        print(f"\n✅ Tagesziel erreicht! {posted_today} originale Posts erstellt")

def main():
    bot = OriginalPostBot()
    
    print("\n🤖 ORIGINAL POST BOT")
    print("Erstellt eigene, originale Reddit Posts")
    print("\n1. Automatischer Loop")
    print("2. Einzelnen Post generieren")
    print("3. Statistiken anzeigen")
    
    choice = input("\nWahl (1-3): ").strip()
    
    if choice == "1":
        bot.run_loop()
    elif choice == "2":
        themes = list(bot.subreddit_themes.keys())
        print(f"\nVerfügbare Themen: {', '.join(themes)}")
        theme = input("Thema wählen (oder Enter für zufällig): ").strip() or 'random'
        
        post = bot.generate_original_post(theme)
        if post:
            print(f"\n📝 GENERIERTER POST:")
            print(f"Titel: {post['title']}")
            print(f"Subreddit: r/{post['subreddit']}")
            print(f"Text: {post.get('selftext', '')}")
            
            if input("\nPosten? (ja/nein): ").lower() == 'ja':
                bot.create_post(post)
    elif choice == "3":
        print(f"\n📊 STATISTIKEN:")
        print(f"Inspirations-Posts: {len(bot.archive_posts)}")
        print(f"Bereits gepostet: {len(bot.posted_titles)} Titel")
        print(f"Heutiges Ziel: {bot.daily_target} Posts")

if __name__ == "__main__":
    main()