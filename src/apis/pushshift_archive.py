#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Pushshift Archive Reader
Reads and filters historical Pushshift dumps for high-scoring posts
"""

import json
import zstandard as zstd
from pathlib import Path
from logs.logger import log
from typing import Generator, Dict, Any
import os

class PushshiftArchive:
    def __init__(self, archive_path: str = None):
        """
        Initialize the Pushshift Archive reader
        
        Args:
            archive_path: Path to the directory containing Pushshift dump files
        """
        self.archive_path = Path(archive_path) if archive_path else Path("./pushshift_dumps")
        self.min_score = 5000  # Same threshold as original code
        
    def read_zst_file(self, file_path: Path) -> Generator[Dict[str, Any], None, None]:
        """
        Read a zstandard compressed NDJSON file
        
        Args:
            file_path: Path to the .zst file
            
        Yields:
            Dict containing post/comment data
        """
        log.info(f"Reading archive file: {file_path}")
        
        with open(file_path, 'rb') as fh:
            dctx = zstd.ZstdDecompressor(max_window_size=2147483648)
            with dctx.stream_reader(fh) as reader:
                text_stream = io.TextIOWrapper(reader, encoding='utf-8')
                for line_number, line in enumerate(text_stream):
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as e:
                        log.warning(f"Error parsing line {line_number} in {file_path}: {e}")
                        continue
                        
    def get_high_score_posts(self, subreddit: str = None, limit: int = 100) -> list:
        """
        Find posts with score >= 5000 from the archives
        
        Args:
            subreddit: Specific subreddit to filter (optional)
            limit: Maximum number of posts to return
            
        Returns:
            List of high-scoring posts
        """
        high_score_posts = []
        
        # Find relevant archive files
        if subreddit:
            pattern = f"*{subreddit}*submissions*.zst"
        else:
            pattern = "*submissions*.zst"
            
        archive_files = list(self.archive_path.glob(pattern))
        
        if not archive_files:
            log.warning(f"No archive files found matching pattern: {pattern}")
            return []
            
        log.info(f"Found {len(archive_files)} archive files to process")
        
        for file_path in archive_files:
            if len(high_score_posts) >= limit:
                break
                
            try:
                for post in self.read_zst_file(file_path):
                    # Filter by score
                    if post.get('score', 0) >= self.min_score:
                        # Filter out deleted posts
                        if post.get('author') not in ['[deleted]', None]:
                            if post.get('selftext') not in ['[removed]', '[deleted]', None]:
                                # Add post if it matches our criteria
                                if not subreddit or post.get('subreddit', '').lower() == subreddit.lower():
                                    high_score_posts.append({
                                        'id': post.get('id'),
                                        'title': post.get('title'),
                                        'score': post.get('score'),
                                        'subreddit': post.get('subreddit'),
                                        'author': post.get('author'),
                                        'selftext': post.get('selftext', ''),
                                        'url': post.get('url', ''),
                                        'is_self': post.get('is_self', False),
                                        'created_utc': post.get('created_utc')
                                    })
                                    
                                    if len(high_score_posts) >= limit:
                                        break
                                        
            except Exception as e:
                log.error(f"Error processing file {file_path}: {e}")
                continue
                
        log.info(f"Found {len(high_score_posts)} high-scoring posts")
        return high_score_posts
        
    def search_posts_by_year(self, year: int, subreddit: str = None) -> list:
        """
        Search for high-scoring posts from a specific year
        
        Args:
            year: Year to search (e.g., 2022)
            subreddit: Optional subreddit filter
            
        Returns:
            List of high-scoring posts from that year
        """
        import time
        from datetime import datetime
        
        # Calculate timestamp range for the year
        start_timestamp = int(datetime(year, 1, 1).timestamp())
        end_timestamp = int(datetime(year + 1, 1, 1).timestamp())
        
        high_score_posts = []
        pattern = f"*{year}*submissions*.zst" if not subreddit else f"*{subreddit}*{year}*submissions*.zst"
        
        archive_files = list(self.archive_path.glob(pattern))
        
        for file_path in archive_files:
            try:
                for post in self.read_zst_file(file_path):
                    created_utc = post.get('created_utc', 0)
                    
                    # Check if post is from the specified year
                    if start_timestamp <= created_utc < end_timestamp:
                        if post.get('score', 0) >= self.min_score:
                            if post.get('author') not in ['[deleted]', None]:
                                high_score_posts.append(post)
                                
            except Exception as e:
                log.error(f"Error processing file {file_path}: {e}")
                
        return high_score_posts


# Import io for TextIOWrapper
import io