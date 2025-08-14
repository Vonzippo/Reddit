#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Zeigt Statistiken über generierte Posts
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

def show_stats():
    """Zeigt Statistiken über generierte Posts"""
    
    # Pfade
    base_dir = Path("/Users/patrick/Desktop/Reddit")
    posts_dir = base_dir / "generated_posts"
    daily_stats_file = base_dir / "daily_post_stats.json"
    posted_history_file = base_dir / "posted_posts.json"
    
    print("\n📊 POST-STATISTIKEN")
    print("="*60)
    
    # Lade tägliche Statistiken
    if daily_stats_file.exists():
        with open(daily_stats_file, 'r', encoding='utf-8') as f:
            daily_stats = json.load(f)
        
        print("\n📅 TÄGLICHE ÜBERSICHT:")
        print("-"*40)
        
        # Sortiere nach Datum
        sorted_days = sorted(daily_stats.keys(), reverse=True)[:7]  # Letzte 7 Tage
        
        total_posts = 0
        skip_days = 0
        
        for day in sorted_days:
            stats = daily_stats[day]
            target = stats.get('target', 0)
            count = stats.get('count', 0)
            
            if stats.get('skip_day', False) or target == 0:
                print(f"  {day}: 😴 Pausentag")
                skip_days += 1
            else:
                emoji = "✅" if count >= target else "⏳"
                print(f"  {day}: {emoji} {count}/{target} Posts")
                total_posts += count
        
        print(f"\n📈 ZUSAMMENFASSUNG (letzte 7 Tage):")
        print(f"  • Aktive Tage: {len(sorted_days) - skip_days}")
        print(f"  • Pausentage: {skip_days}")
        print(f"  • Gesamt Posts: {total_posts}")
        if len(sorted_days) - skip_days > 0:
            print(f"  • Durchschnitt pro aktivem Tag: {total_posts / (len(sorted_days) - skip_days):.1f}")
    
    # Zeige gepostete Historie
    if posted_history_file.exists():
        with open(posted_history_file, 'r', encoding='utf-8') as f:
            posted_data = json.load(f)
            posted_posts = posted_data.get('posts', [])
        
        print(f"\n📝 GEPOSTETE POSTS:")
        print(f"  • Insgesamt gepostet: {len(posted_posts)}")
    
    # Zeige Ordnerstruktur
    if posts_dir.exists():
        print("\n📁 GESPEICHERTE POSTS:")
        print("-"*40)
        
        total_files = 0
        for year_month in sorted(posts_dir.iterdir()):
            if year_month.is_dir() and not year_month.name.startswith('.'):
                month_count = 0
                for day in year_month.iterdir():
                    if day.is_dir():
                        json_files = list(day.glob("post_*.json"))
                        month_count += len(json_files)
                        total_files += len(json_files)
                
                if month_count > 0:
                    print(f"  📅 {year_month.name}: {month_count} Posts")
        
        print(f"\n  💾 Gesamt gespeicherte Posts: {total_files}")
        
        # Zeige neueste Posts
        print("\n🆕 NEUESTE POSTS:")
        print("-"*40)
        
        # Finde die neuesten Post-Dateien
        all_posts = []
        for year_month in posts_dir.iterdir():
            if year_month.is_dir():
                for day in year_month.iterdir():
                    if day.is_dir():
                        for post_file in day.glob("post_*.json"):
                            all_posts.append(post_file)
        
        # Sortiere nach Änderungszeit
        all_posts.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Zeige die letzten 5
        for post_file in all_posts[:5]:
            try:
                with open(post_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                time_str = data.get('time', 'unknown')
                date_str = data.get('date', 'unknown')
                subreddit = data.get('subreddit', 'unknown')
                title = data.get('title', '')[:60]
                score = data.get('score', 0)
                
                print(f"\n  📝 {date_str} {time_str} - r/{subreddit}")
                print(f"     Titel: {title}...")
                print(f"     Score (Original): {score:,}")
            except:
                continue
    
    # Heute Status
    today = datetime.now().strftime("%Y-%m-%d")
    if daily_stats_file.exists() and today in daily_stats:
        today_stats = daily_stats[today]
        target = today_stats.get('target', 0)
        count = today_stats.get('count', 0)
        
        print("\n🎯 HEUTIGER STATUS:")
        print("-"*40)
        
        if today_stats.get('skip_day', False) or target == 0:
            print("  😴 Heute ist ein Pausentag")
        else:
            progress = (count / target * 100) if target > 0 else 0
            bar_length = 20
            filled = int(bar_length * progress / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f"  Ziel: {target} Posts")
            print(f"  Erstellt: {count}")
            print(f"  Fortschritt: [{bar}] {progress:.0f}%")
            
            if count < target:
                remaining = target - count
                print(f"  Verbleibend: {remaining} Posts")
            
            # Zeige heutige Posts
            if 'posts' in today_stats and today_stats['posts']:
                print(f"\n  📋 Heutige Posts:")
                for post in today_stats['posts'][-5:]:  # Letzte 5
                    time_str = post.get('time', '')
                    if 'T' in time_str:
                        time_str = time_str.split('T')[1].split('.')[0]
                    title = post.get('title', '')[:50]
                    subreddit = post.get('subreddit', 'unknown')
                    print(f"    • {time_str} - r/{subreddit}: {title}...")

def show_combined_stats():
    """Zeigt kombinierte Statistiken für Posts und Kommentare"""
    print("\n📊 KOMBINIERTE BOT-STATISTIKEN")
    print("="*60)
    
    base_dir = Path("/Users/patrick/Desktop/Reddit")
    
    # Lade beide Statistiken
    post_stats_file = base_dir / "daily_post_stats.json"
    comment_stats_file = base_dir / "daily_comment_stats.json"
    
    post_stats = {}
    comment_stats = {}
    
    if post_stats_file.exists():
        with open(post_stats_file, 'r') as f:
            post_stats = json.load(f)
    
    if comment_stats_file.exists():
        with open(comment_stats_file, 'r') as f:
            comment_stats = json.load(f)
    
    # Kombiniere alle Tage
    all_days = set(list(post_stats.keys()) + list(comment_stats.keys()))
    sorted_days = sorted(all_days, reverse=True)[:7]
    
    print("\n📅 LETZTE 7 TAGE AKTIVITÄT:")
    print("-"*40)
    
    for day in sorted_days:
        posts = post_stats.get(day, {})
        comments = comment_stats.get(day, {})
        
        post_count = posts.get('count', 0)
        post_target = posts.get('target', 0)
        comment_count = comments.get('count', 0)
        comment_target = comments.get('target', 0)
        
        if posts.get('skip_day') and comments.get('skip_day'):
            print(f"  {day}: 😴 Komplett-Pausentag")
        else:
            activities = []
            if post_target > 0:
                activities.append(f"📝 {post_count}/{post_target} Posts")
            elif posts.get('skip_day'):
                activities.append("📝 Pause")
            
            if comment_target > 0:
                activities.append(f"💬 {comment_count}/{comment_target} Kommentare")
            elif comments.get('skip_day'):
                activities.append("💬 Pause")
            
            print(f"  {day}: {' | '.join(activities)}")
    
    print("\n📊 GESAMTAKTIVITÄT:")
    total_posts = sum(post_stats.get(d, {}).get('count', 0) for d in sorted_days)
    total_comments = sum(comment_stats.get(d, {}).get('count', 0) for d in sorted_days)
    print(f"  • Posts (7 Tage): {total_posts}")
    print(f"  • Kommentare (7 Tage): {total_comments}")
    print(f"  • Gesamt Aktivitäten: {total_posts + total_comments}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--combined":
        show_combined_stats()
    else:
        show_stats()
        print("\n💡 Tipp: Nutze '--combined' für kombinierte Post+Kommentar Statistiken")