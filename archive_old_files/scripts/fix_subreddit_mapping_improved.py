#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Verbesserte Subreddit-Zuordnung basierend auf Themen
"""

import json
from pathlib import Path
import random

def fix_subreddit_mappings():
    """Korrigiert alternative Subreddits mit besserem Themen-Matching"""
    
    posts_dir = Path("/Users/patrick/Desktop/Reddit/data_all/Posts")
    
    # Thematische Zuordnungen - nur sichere Subreddits ohne Karma-Anforderungen
    THEME_MAPPINGS = {
        # ADHD/Mental Health Posts -> Selbstverbesserung & Support
        'adhdwomen': ['self', 'selfimprovement', 'DecidingToBeBetter', 'offmychest', 'rant'],
        'ADHDmemes': ['self', 'DoesAnybodyElse', 'CasualConversation', 'rant'],
        'adhdmeme': ['self', 'DoesAnybodyElse', 'CasualConversation', 'rant'],
        'ADHD': ['self', 'selfimprovement', 'DecidingToBeBetter', 'NoStupidQuestions'],
        
        # Autism/Neurodiversity -> Allgemeine Diskussion
        'autism': ['self', 'CasualConversation', 'NoStupidQuestions', 'DoesAnybodyElse'],
        'neurodiversity': ['self', 'CasualConversation', 'NoStupidQuestions', 'DoesAnybodyElse'],
        
        # Mental Health -> Support Communities
        'CPTSD': ['self', 'offmychest', 'rant', 'confession'],
        
        # Produktivität/Lernen -> Selbstverbesserung
        'productivity': ['selfimprovement', 'DecidingToBeBetter', 'self'],
        'getdisciplined': ['selfimprovement', 'DecidingToBeBetter', 'self'],
        'GetStudying': ['selfimprovement', 'DecidingToBeBetter', 'self', 'NoStupidQuestions'],
        'studytips': ['selfimprovement', 'DecidingToBeBetter', 'self', 'NoStupidQuestions'],
        
        # Journaling/Notebooks -> Kreative Communities
        'Journaling': ['self', 'CasualConversation', 'selfimprovement'],
        'notebooks': ['self', 'CasualConversation', 'selfimprovement'],
        'Notion': ['selfimprovement', 'DecidingToBeBetter', 'self'],
        'BasicBulletJournals': ['selfimprovement', 'self', 'CasualConversation'],
        'planners': ['selfimprovement', 'DecidingToBeBetter', 'self'],
        
        # Personal/Confession -> Offene Diskussion
        'TrueOffMyChest': ['self', 'offmychest', 'rant', 'confession', 'CasualConversation'],
        'relationship_advice': ['self', 'offmychest', 'rant', 'confession'],
        
        # Hobbies/Interests -> Casual Communities
        'gardening': ['self', 'CasualConversation', 'DoesAnybodyElse'],
        'houseplants': ['self', 'CasualConversation', 'DoesAnybodyElse'],
        'crafts': ['self', 'CasualConversation', 'DoesAnybodyElse'],
        'DIY': ['self', 'CasualConversation', 'DoesAnybodyElse'],
        
        # Work/Career -> Diskussion
        'Teachers': ['self', 'offmychest', 'rant', 'CasualConversation'],
        'jobs': ['self', 'offmychest', 'rant', 'CasualConversation'],
        
        # Entertainment/Memes -> Casual
        'memes': ['CasualConversation', 'DoesAnybodyElse', 'self'],
        'dankmemes': ['CasualConversation', 'DoesAnybodyElse', 'self'],
        'meirl': ['DoesAnybodyElse', 'CasualConversation', 'self'],
        'me_irl': ['DoesAnybodyElse', 'CasualConversation', 'self'],
        '2meirl4meirl': ['self', 'DoesAnybodyElse', 'rant'],
        'shitposting': ['CasualConversation', 'self'],
        'FunnyandSad': ['self', 'DoesAnybodyElse', 'CasualConversation'],
        
        # Specific fandoms/games -> General discussion
        'StardewValley': ['CasualConversation', 'self'],
        'Sims4': ['CasualConversation', 'self'],
        'thesims': ['CasualConversation', 'self'],
        'titanfall': ['CasualConversation', 'self'],
        'Helldivers': ['CasualConversation', 'self'],
        'batman': ['CasualConversation', 'self'],
        'OnePiece': ['CasualConversation', 'self'],
        'HunterXHunter': ['CasualConversation', 'self'],
        'attackontitan': ['CasualConversation', 'self'],
        'anime_irl': ['CasualConversation', 'self'],
        'Animemes': ['CasualConversation', 'self'],
        'Hololive': ['CasualConversation', 'self'],
        
        # General/Misc -> Breite Alternativen
        'CasualConversation': ['self', 'NoStupidQuestions', 'DoesAnybodyElse', 'offmychest'],
        'mildlyinfuriating': ['rant', 'offmychest', 'self', 'DoesAnybodyElse'],
        'mildlyinteresting': ['CasualConversation', 'self', 'DoesAnybodyElse'],
        'funny': ['CasualConversation', 'self'],
        'wholesome': ['CasualConversation', 'self'],
        'Eyebleach': ['CasualConversation', 'self'],
        'notinteresting': ['CasualConversation', 'self', 'DoesAnybodyElse'],
        
        # Specific communities -> General
        'Millennials': ['CasualConversation', 'self', 'DoesAnybodyElse'],
        'BlackPeopleTwitter': ['CasualConversation', 'self'],
        'WitchesVsPatriarchy': ['self', 'CasualConversation'],
        'BravoRealHousewives': ['CasualConversation', 'self'],
    }
    
    # Fallback für nicht gemappte Subreddits
    DEFAULT_ALTERNATIVES = ['self', 'CasualConversation', 'NoStupidQuestions', 'DoesAnybodyElse']
    
    fixed_count = 0
    checked_count = 0
    
    print("🔧 VERBESSERTE SUBREDDIT ZUORDNUNG")
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
        
        original_sub = post_data.get('subreddit', '')
        title = post_data.get('title', '')
        
        # Finde passende Alternativen basierend auf Original-Subreddit
        if original_sub in THEME_MAPPINGS:
            alternatives = THEME_MAPPINGS[original_sub].copy()
        else:
            # Fallback für unbekannte Subreddits
            alternatives = DEFAULT_ALTERNATIVES.copy()
            
        # Füge zusätzliche Alternativen hinzu basierend auf Titel-Keywords
        title_lower = title.lower()
        
        # ADHD Keywords
        if any(word in title_lower for word in ['adhd', 'focus', 'attention', 'executive', 'dysfunction']):
            extra = ['selfimprovement', 'DecidingToBeBetter', 'DoesAnybodyElse']
            alternatives = list(dict.fromkeys(extra + alternatives))  # Duplikate entfernen
            
        # Frage-Posts
        if any(word in title_lower for word in ['?', 'anyone', 'anybody', 'someone', 'does', 'how', 'why', 'what']):
            extra = ['NoStupidQuestions', 'DoesAnybodyElse']
            alternatives = list(dict.fromkeys(extra + alternatives))
            
        # Erfolgs-Posts
        if any(word in title_lower for word in ['finally', 'success', 'managed', 'proud', 'achieved', 'did it']):
            extra = ['self', 'DecidingToBeBetter', 'selfimprovement']
            alternatives = list(dict.fromkeys(extra + alternatives))
            
        # Rant/Beschwerde Posts
        if any(word in title_lower for word in ['hate', 'annoying', 'frustrated', 'sick of', 'tired of']):
            extra = ['rant', 'offmychest', 'confession']
            alternatives = list(dict.fromkeys(extra + alternatives))
        
        # Begrenzen auf max 8 Alternativen
        alternatives = alternatives[:8]
        
        # Nur updaten wenn sich was geändert hat
        current_alts = post_data.get('alternative_subreddits', [])
        if current_alts != alternatives:
            post_data['alternative_subreddits'] = alternatives
            
            with open(json_file, 'w') as f:
                json.dump(post_data, f, indent=2, ensure_ascii=False)
            
            fixed_count += 1
            if fixed_count <= 10:  # Zeige nur erste 10 Beispiele
                print(f"✅ {post_dir.name[:30]}")
                print(f"   Original: r/{original_sub}")
                print(f"   Neue Alts: {', '.join(['r/'+s for s in alternatives[:3]])}...")
    
    print()
    print("="*60)
    print(f"✅ FERTIG!")
    print(f"   Überprüft: {checked_count} Posts")
    print(f"   Verbessert: {fixed_count} Posts")
    print()
    print("📝 Mapping-Strategie:")
    print("   • ADHD-Posts → self, selfimprovement, DecidingToBeBetter")
    print("   • Fragen → NoStupidQuestions, DoesAnybodyElse")
    print("   • Persönliches → offmychest, rant, confession")
    print("   • Hobbies → CasualConversation, self")
    print("   • Erfolge → self, DecidingToBeBetter")

if __name__ == "__main__":
    fix_subreddit_mappings()