#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import json
import os
import random
from pathlib import Path
from logs.logger import log

class LocalDataAPI:
    def __init__(self, data_dir="/Users/patrick/Desktop/Reddit Karma Farm/december_top_content"):
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
                    content_file = post_folder / "post_content.txt"
                    if json_file.exists():
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                post_data = json.load(f)
                            
                            # Add content if exists
                            if content_file.exists():
                                with open(content_file, 'r', encoding='utf-8') as f:
                                    post_data['content'] = f.read()
                            
                            # Check for image
                            image_file = post_folder / "image.jpg"
                            if image_file.exists():
                                post_data['has_image'] = True
                                post_data['image_path'] = str(image_file)
                            
                            self.posts.append(post_data)
                        except Exception as e:
                            log.error(f"Error loading post {post_folder}: {e}")
        
        # Load comments
        comments_dir = self.data_dir / "top_100_comments"
        if comments_dir.exists():
            for comment_folder in comments_dir.iterdir():
                if comment_folder.is_dir() and comment_folder.name.startswith("comment_"):
                    json_file = comment_folder / "comment_data.json"
                    content_file = comment_folder / "comment_content.txt"
                    if json_file.exists():
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                comment_data = json.load(f)
                            
                            # Add content if exists
                            if content_file.exists():
                                with open(content_file, 'r', encoding='utf-8') as f:
                                    comment_data['content'] = f.read()
                            
                            self.comments.append(comment_data)
                        except Exception as e:
                            log.error(f"Error loading comment {comment_folder}: {e}")
        
        log.info(f"Loaded {len(self.posts)} posts and {len(self.comments)} comments from local data")
    
    def get_random_post(self):
        """Get a random post from the loaded data"""
        if self.posts:
            return random.choice(self.posts)
        return None
    
    def get_random_comment(self):
        """Get a random comment from the loaded data"""
        if self.comments:
            return random.choice(self.comments)
        return None
    
    def get_all_posts(self):
        """Get all loaded posts"""
        return self.posts
    
    def get_all_comments(self):
        """Get all loaded comments"""
        return self.comments