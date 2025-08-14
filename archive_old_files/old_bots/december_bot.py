#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
December Content Bot - Zeigt Posts und Kommentare aus december_top_content
Keine Reddit API erforderlich!
"""

import json
import random
import time
from pathlib import Path

class DecemberBot:
    def __init__(self):
        self.data_dir = Path("december_top_content")
        self.posts = []
        self.comments = []
        self.load_all_content()
    
    def load_all_content(self):
        """Lädt alle Posts und Kommentare aus december_top_content"""
        
        # Posts laden
        posts_dir = self.data_dir / "top_50_posts"
        if posts_dir.exists():
            for folder in sorted(posts_dir.iterdir()):
                if folder.is_dir() and folder.name.startswith("post_"):
                    json_file = folder / "post_data.json"
                    if json_file.exists():
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                post = json.load(f)
                                # Content hinzufügen wenn vorhanden
                                content_file = folder / "post_content.txt"
                                if content_file.exists():
                                    with open(content_file, 'r', encoding='utf-8') as f:
                                        post['text_content'] = f.read()
                                self.posts.append(post)
                        except Exception as e:
                            print(f"Fehler beim Laden von {json_file}: {e}")
        
        # Kommentare laden
        comments_dir = self.data_dir / "top_100_comments"
        if comments_dir.exists():
            for folder in sorted(comments_dir.iterdir()):
                if folder.is_dir() and folder.name.startswith("comment_"):
                    json_file = folder / "comment_data.json"
                    if json_file.exists():
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                comment = json.load(f)
                                # Content hinzufügen wenn vorhanden
                                content_file = folder / "comment_content.txt"
                                if content_file.exists():
                                    with open(content_file, 'r', encoding='utf-8') as f:
                                        comment['text_content'] = f.read()
                                self.comments.append(comment)
                        except Exception as e:
                            print(f"Fehler beim Laden von {json_file}: {e}")
        
        print(f"\n✅ December Content Bot gestartet!")
        print(f"📊 {len(self.posts)} Posts und {len(self.comments)} Kommentare geladen")
        print("-" * 60)
    
    def show_post(self):
        """Zeigt einen zufälligen Post"""
        if not self.posts:
            return
        
        post = random.choice(self.posts)
        print(f"\n📝 POST: {post.get('title', 'Kein Titel')[:100]}")
        print(f"   👤 r/{post.get('subreddit', '?')} | ⬆️ {post.get('score', 0):,} | 💬 {post.get('num_comments', 0):,}")
        
        # Zeige Textinhalt wenn vorhanden
        if post.get('selftext'):
            preview = post['selftext'][:150].replace('\n', ' ')
            if len(post.get('selftext', '')) > 150:
                preview += "..."
            print(f"   📄 {preview}")
    
    def show_comment(self):
        """Zeigt einen zufälligen Kommentar"""
        if not self.comments:
            return
        
        comment = random.choice(self.comments)
        body = comment.get('body', '')[:120].replace('\n', ' ')
        if len(comment.get('body', '')) > 120:
            body += "..."
        
        print(f"\n💬 COMMENT: {body}")
        print(f"   👤 r/{comment.get('subreddit', '?')} | ⬆️ {comment.get('score', 0):,}")
    
    def run_continuous(self):
        """Läuft kontinuierlich und zeigt abwechselnd Posts und Kommentare"""
        print("\n🤖 Bot läuft... (Strg+C zum Stoppen)\n")
        
        try:
            while True:
                # 60% Chance für Post, 40% für Kommentar
                if random.random() < 0.6:
                    self.show_post()
                else:
                    self.show_comment()
                
                # Warte 2-5 Sekunden
                time.sleep(random.uniform(2, 5))
                
        except KeyboardInterrupt:
            print("\n\n✋ Bot gestoppt")
            print(f"📊 Session beendet - {len(self.posts)} Posts und {len(self.comments)} Kommentare waren verfügbar")

if __name__ == "__main__":
    bot = DecemberBot()
    bot.run_continuous()