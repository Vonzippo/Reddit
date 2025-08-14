#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Korrigiert die Subreddit-Zuordnungen
Stellt sicher dass ADHD-Posts nur in passende Subreddits gehen
"""

import json
from pathlib import Path

def fix_subreddit_mappings():
    """Korrigiert alternative Subreddits für alle Posts"""
    
    posts_dir = Path("/Users/patrick/Desktop/Reddit/data_all/Posts")
    
    # Definiere thematisch passende Alternativen
    # WICHTIG: Nur Subreddits OHNE Karma-Anforderungen!
    # Diese wurden getestet und funktionieren mit niedrigem Karma
    ADHD_ALTERNATIVES = [
        'self', 'CasualConversation', 'NoStupidQuestions',
        'DoesAnybodyElse', 'rant', 'confession',
        'selfimprovement', 'DecidingToBeBetter'
    ]
    
    MENTAL_HEALTH_ALTERNATIVES = [
        'self', 'CasualConversation', 'NoStupidQuestions',
        'rant', 'confession', 'offmychest',
        'selfimprovement', 'DecidingToBeBetter'
    ]
    
    GENERAL_ALTERNATIVES = [
        'self', 'CasualConversation', 'NoStupidQuestions', 
        'DoesAnybodyElse', 'rant', 'confession',
        'offmychest', 'Showerthoughts', 'TooAfraidToAsk'
    ]
    
    # Subreddits die NIE als Alternative verwendet werden sollten
    BLACKLIST = {
        'schizophrenia', 'bipolar', 'depression', 'SuicideWatch',
        'adhdwomen', 'ADHDmemes', 'adhdmeme', 'ADHD',  # Original ADHD subs
        'autism', 'aspergers', 'BPD', 'CPTSD', 'PTSD',
        'AnorexiaNervosa', 'EDAnonymous', 'EatingDisorders',
        # Subreddits mit hohen Karma-Anforderungen oder Beschränkungen
        'motivation', 'GetMotivated', 'productivity', 'getdisciplined',
        'AskReddit', 'pics', 'funny', 'videos', 'gaming',
        'unpopularopinion', 'AmItheAsshole', 'relationship_advice',
        'TrueOffMyChest',  # Hat auch Beschränkungen für neue User
        'LifeProTips', 'YouShouldKnow'  # Oft hohe Anforderungen
    }
    
    fixed_count = 0
    checked_count = 0
    
    print("🔧 KORRIGIERE SUBREDDIT MAPPINGS")
    print("="*60)
    
    for post_dir in posts_dir.iterdir():
        if not post_dir.is_dir():
            continue
            
        json_file = post_dir / "post_data.json"
        if not json_file.exists():
            continue
        
        checked_count += 1
        
        with open(json_file, 'r') as f:
            post_data = json.load(f)
        
        original_sub = post_data.get('subreddit', '').lower()
        title_lower = post_data.get('title', '').lower()
        
        # Bestimme passende Alternativen basierend auf Original-Subreddit und Titel
        if any(word in original_sub for word in ['adhd', 'add']):
            # ADHD-bezogener Post
            alternatives = ADHD_ALTERNATIVES.copy()
        elif any(word in original_sub for word in ['mental', 'anxiety', 'depression', 'therapy']):
            # Mental Health Post
            alternatives = MENTAL_HEALTH_ALTERNATIVES.copy()
        elif any(word in title_lower for word in ['adhd', 'add', 'focus', 'attention', 'hyperactive']):
            # Titel deutet auf ADHD hin
            alternatives = ADHD_ALTERNATIVES.copy()
        else:
            # Allgemeiner Post
            alternatives = GENERAL_ALTERNATIVES.copy()
        
        # Entferne geblockte Subreddits aus Alternativen
        current_alternatives = post_data.get('alternative_subreddits', [])
        
        # Prüfe ob aktuelle Alternativen problematisch sind
        has_problematic = False
        for alt in current_alternatives:
            if alt.lower() in BLACKLIST:
                has_problematic = True
                print(f"⚠️ {post_dir.name}: Enthält problematisches Subreddit: r/{alt}")
                break
        
        if has_problematic or not current_alternatives:
            # Ersetze mit sicheren Alternativen
            safe_alternatives = [sub for sub in alternatives if sub.lower() not in BLACKLIST]
            post_data['alternative_subreddits'] = safe_alternatives[:10]  # Max 10 Alternativen
            
            # Speichere zurück
            with open(json_file, 'w') as f:
                json.dump(post_data, f, indent=2, ensure_ascii=False)
            
            fixed_count += 1
            print(f"✅ Korrigiert: {post_dir.name}")
            print(f"   Original: r/{original_sub}")
            print(f"   Neue Alternativen: {', '.join(['r/'+s for s in safe_alternatives[:3]])}...")
    
    print()
    print("="*60)
    print(f"✅ FERTIG!")
    print(f"   Überprüft: {checked_count} Posts")
    print(f"   Korrigiert: {fixed_count} Posts")
    print()
    print("🚫 Folgende Subreddits werden NIE als Alternative verwendet:")
    for sub in sorted(BLACKLIST):
        print(f"   • r/{sub}")

if __name__ == "__main__":
    fix_subreddit_mappings()