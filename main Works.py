#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Content Display Bot - Zeigt archivierte Reddit-Inhalte lokal an
BILDUNGSZWECKE ONLY - Kein automatisches Posten!
"""

import json
import random
import time
from pathlib import Path

class ContentViewerBot:
    def __init__(self):
        self.base_dir = Path("/Users/patrick/Desktop/Reddit/data")
        self.posts_dir = self.base_dir / "Posts"
        self.comments_dir = self.base_dir / "Comments"
        self.posts = []
        self.comments = []
        self._load_data()
        
        # ============================================
        # HIER WÜRDE DIE REDDIT API KONFIGURATION STEHEN
        # ============================================
        import praw
        self.reddit = praw.Reddit(
            client_id="HaZ8i53jCT_u2kinupgUow",        # Von Reddit App
            client_secret="IbKUPkTXuT3efIpIHeMkpnW2X_gKTw", # Von Reddit App  
            user_agent="bot:v1.0 (by /u/username)",
            username="ReddiBoto",
            password="Passwort1234*"
        )
        # ============================================
        # WARNUNG: Automatisiertes Posten verstößt gegen Reddit ToS!
        # ============================================
    
    def _load_data(self):
        """Lädt alle Posts und Kommentare direkt aus Posts und Comments Ordnern"""
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
        
        # Kommentare laden direkt aus Comments Ordner
        if self.comments_dir.exists():
            print(f"  📁 Lade Kommentare aus: {self.comments_dir.name}")
            for comment_folder in sorted(self.comments_dir.iterdir()):
                if comment_folder.is_dir() and comment_folder.name.startswith("comment_"):
                    json_file = comment_folder / "comment_data.json"
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.comments.append(data)
        
        print(f"✅ Geladen: {len(self.posts)} Posts und {len(self.comments)} Kommentare")
    
    def get_random_post(self):
        """Gibt einen zufälligen Post zurück"""
        if self.posts:
            return random.choice(self.posts)
        return None
    
    def get_random_comment(self):
        """Gibt einen zufälligen Kommentar zurück"""
        if self.comments:
            return random.choice(self.comments)
        return None
    
    def display_content(self):
        """Zeigt zufälligen Content in der Konsole"""
        if random.random() < 0.6 and self.posts:
            post = self.get_random_post()
            print("\n" + "="*60)
            print("📝 POST:")
            print(f"Titel: {post.get('title', 'Kein Titel')[:80]}")
            print(f"Subreddit: r/{post.get('subreddit', 'unbekannt')}")
            print(f"Score: {post.get('score', 0):,} | Kommentare: {post.get('num_comments', 0)}")
            print(f"URL: {post.get('url', '')}")
            
            # ============================================
            # HIER WÜRDE DER POST-CODE STEHEN:
            # ============================================
            subreddit = self.reddit.subreddit(post['subreddit'])
            if post.get('selftext'):
                # Text-Post
                subreddit.submit(
                    title=post['title'],
                    selftext=post.get('selftext', '')
                )
            elif post.get('url'):
                # Link-Post
                subreddit.submit(
                    title=post['title'],
                    url=post.get('url')
                )
            # ============================================
            
        elif self.comments:
            comment = self.get_random_comment()
            print("\n" + "="*60)
            print("💬 KOMMENTAR:")
            print(f"Text: {comment.get('body', '')[:200]}...")
            print(f"Score: {comment.get('score', 0):,}")
            print(f"Subreddit: r/{comment.get('subreddit', 'unbekannt')}")
            
            # ============================================
            # HIER WÜRDE DER KOMMENTAR-CODE STEHEN:
            # ============================================
            submission = self.reddit.submission(url=some_post_url)
            submission.reply(comment['body'])
            # ============================================
    
    def run(self, iterations=None):
        """Hauptschleife - zeigt Content an"""
        print("\n🤖 Content Viewer Bot - NUR ANZEIGE MODUS")
        print("⚠️  Kein automatisches Posten - nur lokale Anzeige!")
        print("Drücke Ctrl+C zum Beenden\n")
        
        count = 0
        try:
            while True:
                self.display_content()
                count += 1
                
                if iterations and count >= iterations:
                    break
                    
                time.sleep(60)  # 1 minute Pause
                
        except KeyboardInterrupt:
            print("\n\n👋 Bot beendet")
    
    def show_statistics(self):
        """Zeigt Statistiken über die geladenen Daten"""
        print("\n📊 STATISTIKEN:")
        print(f"Posts gesamt: {len(self.posts)}")
        print(f"Kommentare gesamt: {len(self.comments)}")
        
        if self.posts:
            avg_score = sum(p.get('score', 0) for p in self.posts) / len(self.posts)
            print(f"Durchschnittlicher Post-Score: {avg_score:.0f}")
            
            subreddits = set(p.get('subreddit', '') for p in self.posts)
            print(f"Verschiedene Subreddits: {len(subreddits)}")
            print(f"Top Subreddits: {', '.join(list(subreddits)[:5])}")

def main():
    """Hauptfunktion"""
    bot = ContentViewerBot()
    
    print("\nWas möchtest du tun?")
    print("1. Content anzeigen (Loop)")
    print("2. Statistiken anzeigen")
    print("3. Einzelnen Post anzeigen")
    print("4. Einzelnen Kommentar anzeigen")
    
    choice = input("\nAuswahl (1-4): ").strip()
    
    if choice == "1":
        bot.run()
    elif choice == "2":
        bot.show_statistics()
    elif choice == "3":
        post = bot.get_random_post()
        if post:
            print(f"\n📝 {post.get('title', 'Kein Titel')}")
            print(f"Score: {post.get('score', 0):,}")
    elif choice == "4":
        comment = bot.get_random_comment()
        if comment:
            print(f"\n💬 {comment.get('body', '')[:200]}")
            print(f"Score: {comment.get('score', 0):,}")
    else:
        print("Ungültige Auswahl")

if __name__ == "__main__":
    main()