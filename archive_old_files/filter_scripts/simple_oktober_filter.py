#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Einfacher Filter für Top 500 Posts aus Oktober
"""

import json
from pathlib import Path
import time

print("🚀 STARTE EINFACHEN OKTOBER FILTER")
print("="*60)

input_file = Path("/Users/patrick/Desktop/Reddit/pushshift_dumps/2024_october_filtered/RS_2024-10_filtered.jsonl")
output_dir = Path("/Users/patrick/Desktop/Reddit/data_october")
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "top_500_posts_october.json"

print(f"📂 Lese: {input_file.name}")
print(f"   Suche Posts mit Score ≥ 1000")

posts = []
total = 0
start_time = time.time()

with open(input_file, 'r') as f:
    for line in f:
        total += 1
        
        try:
            post = json.loads(line)
            score = post.get('score', 0)
            
            if score >= 1000:
                posts.append({
                    'id': post.get('id', ''),
                    'title': post.get('title', ''),
                    'score': score,
                    'subreddit': post.get('subreddit', ''),
                    'url': post.get('url', ''),
                    'selftext': post.get('selftext', ''),
                    'author': post.get('author', ''),
                    'created_utc': post.get('created_utc', 0),
                    'num_comments': post.get('num_comments', 0),
                    'over_18': post.get('over_18', False),
                    'permalink': post.get('permalink', ''),
                    'link_flair_text': post.get('link_flair_text', '')
                })
        except:
            continue
        
        if total % 50000 == 0:
            elapsed = time.time() - start_time
            print(f"   📊 {total:,} Posts gelesen | {len(posts)} gefunden | {total/elapsed:.0f}/s")

# Sortiere nach Score
posts.sort(key=lambda x: x['score'], reverse=True)

# Nimm Top 500
top_500 = posts[:500]

print(f"\n✅ FERTIG!")
print(f"   Total gelesen: {total:,}")
print(f"   Posts mit Score ≥1000: {len(posts)}")
print(f"   Top 500 extrahiert")

if top_500:
    print(f"\n🏆 TOP 10 POSTS:")
    for i, post in enumerate(top_500[:10], 1):
        print(f"{i:2}. Score {post['score']:,} | r/{post['subreddit']}")
        print(f"    {post['title'][:60]}...")

# Speichern
with open(output_file, 'w') as f:
    json.dump(top_500, f, indent=2, ensure_ascii=False)

print(f"\n💾 Gespeichert: {output_file}")
print(f"   Score-Range: {top_500[-1]['score']:,} - {top_500[0]['score']:,}")