#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Zeigt Statistiken über generierte Kommentare
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import os

def show_stats():
    """Zeigt Statistiken über generierte Kommentare"""
    
    # Pfade
    base_dir = Path("/Users/patrick/Desktop/Reddit")
    comments_dir = base_dir / "generated_comments"
    daily_stats_file = base_dir / "daily_comment_stats.json"
    
    print("\n📊 KOMMENTAR-STATISTIKEN")
    print("="*60)
    
    # Lade tägliche Statistiken
    if daily_stats_file.exists():
        with open(daily_stats_file, 'r', encoding='utf-8') as f:
            daily_stats = json.load(f)
        
        print("\n📅 TÄGLICHE ÜBERSICHT:")
        print("-"*40)
        
        # Sortiere nach Datum
        sorted_days = sorted(daily_stats.keys(), reverse=True)[:7]  # Letzte 7 Tage
        
        total_comments = 0
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
                print(f"  {day}: {emoji} {count}/{target} Kommentare")
                total_comments += count
        
        print(f"\n📈 ZUSAMMENFASSUNG (letzte 7 Tage):")
        print(f"  • Aktive Tage: {len(sorted_days) - skip_days}")
        print(f"  • Pausentage: {skip_days}")
        print(f"  • Gesamt Kommentare: {total_comments}")
        if len(sorted_days) - skip_days > 0:
            print(f"  • Durchschnitt pro aktivem Tag: {total_comments / (len(sorted_days) - skip_days):.1f}")
    
    # Zeige Ordnerstruktur
    if comments_dir.exists():
        print("\n📁 GESPEICHERTE KOMMENTARE:")
        print("-"*40)
        
        total_files = 0
        for year_month in sorted(comments_dir.iterdir()):
            if year_month.is_dir() and not year_month.name.startswith('.'):
                month_count = 0
                for day in year_month.iterdir():
                    if day.is_dir():
                        json_files = list(day.glob("comment_*.json"))
                        month_count += len(json_files)
                        total_files += len(json_files)
                
                if month_count > 0:
                    print(f"  📅 {year_month.name}: {month_count} Kommentare")
        
        print(f"\n  💾 Gesamt gespeicherte Kommentare: {total_files}")
        
        # Zeige neueste Kommentare
        print("\n🆕 NEUESTE KOMMENTARE:")
        print("-"*40)
        
        # Finde die neuesten Kommentar-Dateien
        all_comments = []
        for year_month in comments_dir.iterdir():
            if year_month.is_dir():
                for day in year_month.iterdir():
                    if day.is_dir():
                        for comment_file in day.glob("comment_*.json"):
                            all_comments.append(comment_file)
        
        # Sortiere nach Änderungszeit
        all_comments.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Zeige die letzten 5
        for comment_file in all_comments[:5]:
            try:
                with open(comment_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                time_str = data.get('time', 'unknown')
                date_str = data.get('date', 'unknown')
                subreddit = data.get('subreddit', 'unknown')
                comment_preview = data.get('comment', '')[:50]
                
                print(f"\n  📝 {date_str} {time_str} - r/{subreddit}")
                print(f"     {comment_preview}...")
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
            
            print(f"  Ziel: {target} Kommentare")
            print(f"  Erstellt: {count}")
            print(f"  Fortschritt: [{bar}] {progress:.0f}%")
            
            if count < target:
                remaining = target - count
                print(f"  Verbleibend: {remaining} Kommentare")

if __name__ == "__main__":
    show_stats()