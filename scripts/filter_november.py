#!/usr/bin/env python3
"""
Schneller Filter speziell für November 2024 Daten
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filter_fast import FastRedditFilter
from pathlib import Path
from datetime import datetime

def filter_november():
    print("=" * 60)
    print("⚡ NOVEMBER 2024 FILTER (Multithreading)")
    print("=" * 60)
    
    # Initialisiere Filter
    filter = FastRedditFilter()
    
    # November-Dateien
    november_comments = Path("pushshift_dumps/reddit/november/reddit/comments/RC_2024-11.zst")
    november_posts = Path("pushshift_dumps/reddit/november/reddit/submissions/RS_2024-11.zst")
    
    if not november_comments.exists() or not november_posts.exists():
        print("❌ November-Dateien nicht gefunden!")
        return
    
    print(f"\n📦 November-Dateien gefunden:")
    print(f"  Comments: {november_comments.stat().st_size / (1024**3):.2f} GB")
    print(f"  Posts: {november_posts.stat().st_size / (1024**3):.2f} GB")
    
    # Output-Verzeichnisse
    comments_output_dir = Path("pushshift_dumps/2024_filtered")
    posts_output_dir = Path("pushshift_dumps/2024_posts_filtered")
    comments_output_dir.mkdir(parents=True, exist_ok=True)
    posts_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Filtere Comments
    print("\n📊 Filtere November Comments...")
    comments_output = comments_output_dir / "RC_2024-11_filtered.jsonl"
    comments_count = filter.filter_file_parallel(november_comments, comments_output, num_workers=16)
    
    # Filtere Posts
    print("\n📊 Filtere November Posts...")
    posts_output = posts_output_dir / "RS_2024-11_filtered.jsonl"
    posts_count = filter.filter_file_parallel(november_posts, posts_output, num_workers=16)
    
    print("\n" + "=" * 60)
    print("✅ NOVEMBER FILTERUNG ABGESCHLOSSEN!")
    print(f"  Comments gefiltert: {comments_count:,}")
    print(f"  Posts gefiltert: {posts_count:,}")
    print("\n📁 Output:")
    print(f"  Comments: {comments_output}")
    print(f"  Posts: {posts_output}")

if __name__ == "__main__":
    filter_november()