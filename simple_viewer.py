#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import json
import os
import random
import time
from pathlib import Path

class SimpleLocalViewer:
    def __init__(self, data_dir="december_top_content"):
        self.data_dir = Path(data_dir)
        self.posts = []
        self.comments = []
        self._load_data()
    
    def _load_data(self):
        """Load all posts and comments from local directories"""
        # Load posts
        posts_dir = self.data_dir / "top_50_posts"
        if posts_dir.exists():
            for post_folder in posts_dir.iterdir():
                if post_folder.is_dir() and post_folder.name.startswith("post_"):
                    json_file = post_folder / "post_data.json"
                    if json_file.exists():
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                post_data = json.load(f)
                            self.posts.append(post_data)
                        except Exception as e:
                            print(f"Error loading {json_file}: {e}")
        
        # Load comments
        comments_dir = self.data_dir / "top_100_comments"
        if comments_dir.exists():
            for comment_folder in comments_dir.iterdir():
                if comment_folder.is_dir() and comment_folder.name.startswith("comment_"):
                    json_file = comment_folder / "comment_data.json"
                    if json_file.exists():
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                comment_data = json.load(f)
                            self.comments.append(comment_data)
                        except Exception as e:
                            print(f"Error loading {json_file}: {e}")
        
        print(f"✅ Loaded {len(self.posts)} posts and {len(self.comments)} comments")
    
    def show_post(self):
        """Display a random post"""
        if not self.posts:
            print("No posts available")
            return
        
        post = random.choice(self.posts)
        print("\n" + "="*80)
        print(f"📝 POST: {post.get('title', 'No title')}")
        print(f"👤 Author: {post.get('author', 'Unknown')}")
        print(f"⬆️  Score: {post.get('score', 0):,}")
        print(f"💬 Comments: {post.get('num_comments', 0):,}")
        print(f"📍 Subreddit: r/{post.get('subreddit', 'Unknown')}")
        
        if post.get('selftext'):
            print("\n📄 Content:")
            print("-" * 40)
            content = post.get('selftext', '')[:500]
            if len(post.get('selftext', '')) > 500:
                content += "..."
            print(content)
        print("="*80)
    
    def show_comment(self):
        """Display a random comment"""
        if not self.comments:
            print("No comments available")
            return
        
        comment = random.choice(self.comments)
        print("\n" + "-"*60)
        print(f"💬 COMMENT by {comment.get('author', 'Unknown')}")
        print(f"⬆️  Score: {comment.get('score', 0):,}")
        print(f"📍 Subreddit: r/{comment.get('subreddit', 'Unknown')}")
        
        if comment.get('body'):
            print("\n📝 Comment:")
            content = comment.get('body', '')[:300]
            if len(comment.get('body', '')) > 300:
                content += "..."
            print(content)
        print("-"*60)
    
    def run(self):
        """Run interactive viewer"""
        print("\n🤖 Local Content Viewer")
        print("Using data from: december_top_content/")
        print("-"*80)
        
        while True:
            print("\n📋 Options:")
            print("1. Show random post")
            print("2. Show random comment")
            print("3. Auto mode (alternating every 3 seconds)")
            print("4. Statistics")
            print("5. Exit")
            
            choice = input("\nSelect (1-5): ").strip()
            
            if choice == "1":
                self.show_post()
            elif choice == "2":
                self.show_comment()
            elif choice == "3":
                print("\n🔄 Auto mode (Ctrl+C to stop)")
                try:
                    while True:
                        if random.random() < 0.6:
                            self.show_post()
                        else:
                            self.show_comment()
                        time.sleep(3)
                except KeyboardInterrupt:
                    print("\n✋ Stopped")
            elif choice == "4":
                print(f"\n📊 Statistics:")
                print(f"  Posts: {len(self.posts)}")
                print(f"  Comments: {len(self.comments)}")
            elif choice == "5":
                print("\n👋 Goodbye!")
                break

if __name__ == "__main__":
    viewer = SimpleLocalViewer()
    viewer.run()