#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from apis.local_data import LocalDataAPI
from logs.logger import log
import time
import random
import json

class LocalContentBot:
    def __init__(self):
        self.api = LocalDataAPI()
        self.posts_shown = []
        self.comments_shown = []
        
    def display_post(self):
        """Display a random post from local data"""
        post = self.api.get_random_post()
        if post:
            print("\n" + "="*80)
            print(f"📝 POST: {post.get('title', 'No title')}")
            print(f"👤 Author: {post.get('author', 'Unknown')}")
            print(f"⬆️  Score: {post.get('score', 0)}")
            print(f"💬 Comments: {post.get('num_comments', 0)}")
            print(f"📍 Subreddit: {post.get('subreddit', 'Unknown')}")
            
            if post.get('selftext'):
                print("\n📄 Content:")
                print("-" * 40)
                # Show first 500 characters
                content = post.get('selftext', '')[:500]
                if len(post.get('selftext', '')) > 500:
                    content += "..."
                print(content)
            
            if post.get('has_image'):
                print(f"\n🖼️  Image available: {post.get('image_path', '')}")
            
            print("="*80)
            self.posts_shown.append(post.get('id', 'unknown'))
            return True
        return False
    
    def display_comment(self):
        """Display a random comment from local data"""
        comment = self.api.get_random_comment()
        if comment:
            print("\n" + "-"*60)
            print(f"💬 COMMENT")
            print(f"👤 Author: {comment.get('author', 'Unknown')}")
            print(f"⬆️  Score: {comment.get('score', 0)}")
            print(f"📍 Subreddit: {comment.get('subreddit', 'Unknown')}")
            
            if comment.get('body'):
                print("\n📝 Comment:")
                print("-" * 30)
                # Show first 300 characters
                content = comment.get('body', '')[:300]
                if len(comment.get('body', '')) > 300:
                    content += "..."
                print(content)
            
            print("-"*60)
            self.comments_shown.append(comment.get('id', 'unknown'))
            return True
        return False
    
    def show_statistics(self):
        """Show statistics about the loaded content"""
        print("\n" + "="*80)
        print("📊 CONTENT STATISTICS")
        print("-"*40)
        print(f"Total posts loaded: {len(self.api.get_all_posts())}")
        print(f"Total comments loaded: {len(self.api.get_all_comments())}")
        print(f"Posts shown in this session: {len(self.posts_shown)}")
        print(f"Comments shown in this session: {len(self.comments_shown)}")
        print("="*80)
    
    def run_interactive(self):
        """Run an interactive session"""
        print("\n🤖 Local Content Viewer Bot")
        print("Using local data from december_top_content")
        print("-"*80)
        
        self.show_statistics()
        
        while True:
            print("\n📋 Options:")
            print("1. Show random post")
            print("2. Show random comment")
            print("3. Show statistics")
            print("4. Auto mode (show content every 5 seconds)")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                self.display_post()
            elif choice == "2":
                self.display_comment()
            elif choice == "3":
                self.show_statistics()
            elif choice == "4":
                print("\n🔄 Auto mode started (Press Ctrl+C to stop)")
                try:
                    while True:
                        if random.random() < 0.6:
                            self.display_post()
                        else:
                            self.display_comment()
                        time.sleep(5)
                except KeyboardInterrupt:
                    print("\n✋ Auto mode stopped")
            elif choice == "5":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid option, please try again")

if __name__ == "__main__":
    bot = LocalContentBot()
    bot.run_interactive()