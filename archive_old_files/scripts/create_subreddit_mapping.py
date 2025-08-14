#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Erstellt ein Mapping von Original-Subreddits zu passenden Alternativen
aus target_subreddits_extended.txt
"""

import json
from pathlib import Path
from collections import defaultdict

def load_target_subreddits():
    """Lädt erlaubte Subreddits aus target_subreddits_extended.txt"""
    target_file = Path("/Users/patrick/Desktop/Reddit/target_subreddits_extended.txt")
    
    # Gesperrte Subreddits
    BLACKLIST = {
        'adhdwomen',  # Gesperrt laut User
        'adhd_women',
        'twoxadhd'  # Zeile 70, könnte auch problematisch sein
    }
    
    allowed_subs = []
    
    with open(target_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                sub = line.lower()
                if sub not in BLACKLIST:
                    allowed_subs.append(line)  # Original Schreibweise
    
    return allowed_subs

def create_mapping():
    """Erstellt Mapping von Original-Subs zu Alternativen"""
    
    allowed_subs = load_target_subreddits()
    print(f"✅ {len(allowed_subs)} erlaubte Subreddits geladen (ohne Blacklist)")
    
    # Kategorisiere Subreddits
    categories = {
        'adhd': [],
        'mental_health': [],
        'productivity': [],
        'work': [],
        'creative': [],
        'general': [],
        'support': []
    }
    
    for sub in allowed_subs:
        sub_lower = sub.lower()
        
        # ADHD-bezogen
        if 'adhd' in sub_lower or 'audhd' in sub_lower:
            categories['adhd'].append(sub)
        # Mental Health
        elif any(word in sub_lower for word in ['mental', 'anxiety', 'depression', 'therapy', 'ptsd', 'ocd']):
            categories['mental_health'].append(sub)
        # Produktivität
        elif any(word in sub_lower for word in ['productivity', 'discipline', 'organization', 'study', 'habit']):
            categories['productivity'].append(sub)
        # Arbeit
        elif any(word in sub_lower for word in ['job', 'work', 'career', 'entrepreneur', 'freelance']):
            categories['work'].append(sub)
        # Kreativ
        elif any(word in sub_lower for word in ['art', 'write', 'craft', 'diy', 'garden', 'sketch']):
            categories['creative'].append(sub)
        # Support
        elif any(word in sub_lower for word in ['help', 'support', 'kind', 'friend']):
            categories['support'].append(sub)
        else:
            categories['general'].append(sub)
    
    # Erstelle Mapping-Regeln
    mapping_rules = {
        # Original Subreddit -> Liste von Alternativen
        'adhdmeme': categories['adhd'] + ['ADHD', 'AdultADHD', 'ADHDmemes'],
        'adhd': categories['adhd'],
        'pics': ['wholesome', 'AnimalsBeingBros', 'GetMotivated'],
        'wholesome': ['AnimalsBeingBros', 'happiness', 'GetMotivated', 'KindVoice'],
        'workreform': categories['work'],
        'jobs': categories['work'] + ['careerguidance'],
        'antiwork': categories['work'],
        'houseplants': ['gardening', 'DIY', 'crafts'],
        'teachers': ['education', 'SpecialEducation', 'StudyTips'],
        'casualconversation': ['offmychest', 'TrueOffMyChest', 'vent', 'confessions'],
        
        # Default für unbekannte
        'default': categories['general'] + ['CasualConversation', 'decidingtobebetter', 'selfimprovement']
    }
    
    # Zeige Kategorien
    print("\n📊 KATEGORIEN:")
    for cat, subs in categories.items():
        if subs:
            print(f"\n{cat.upper()} ({len(subs)} Subs):")
            print(f"  {', '.join(subs[:10])}")
            if len(subs) > 10:
                print(f"  ... und {len(subs)-10} weitere")
    
    return mapping_rules, categories

def update_posts_with_alternatives():
    """Fügt alternative Subreddits zu jedem Post hinzu"""
    
    posts_dir = Path("/Users/patrick/Desktop/Reddit/data_all/Posts")
    mapping_rules, categories = create_mapping()
    
    print("\n🔄 UPDATE POSTS MIT ALTERNATIVEN:")
    print("="*60)
    
    updated = 0
    
    for post_dir in posts_dir.iterdir():
        if not post_dir.is_dir():
            continue
        
        json_file = post_dir / "post_data.json"
        if not json_file.exists():
            continue
        
        with open(json_file, 'r') as f:
            post_data = json.load(f)
        
        original_sub = post_data.get('subreddit', '').lower()
        
        # Finde passende Alternativen
        if original_sub in mapping_rules:
            alternatives = mapping_rules[original_sub]
        else:
            # Nutze Default-Alternativen
            alternatives = mapping_rules['default']
        
        # Filtere Original-Sub aus Alternativen
        alternatives = [alt for alt in alternatives if alt.lower() != original_sub]
        
        # Füge zu post_data hinzu
        post_data['alternative_subreddits'] = alternatives[:10]  # Max 10 Alternativen
        
        # Speichere zurück
        with open(json_file, 'w') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        
        updated += 1
        
        if updated <= 5:  # Zeige erste 5 als Beispiel
            print(f"\n📝 {post_dir.name}:")
            print(f"   Original: r/{post_data.get('subreddit')}")
            print(f"   Alternativen: {', '.join(['r/'+s for s in alternatives[:5]])}")
    
    print(f"\n✅ {updated} Posts mit Alternativen aktualisiert!")
    
    # Speichere Mapping als Referenz
    mapping_file = Path("/Users/patrick/Desktop/Reddit/subreddit_mapping.json")
    with open(mapping_file, 'w') as f:
        json.dump({
            'mapping_rules': mapping_rules,
            'categories': categories,
            'blacklist': ['adhdwomen', 'adhd_women', 'twoxadhd']
        }, f, indent=2)
    
    print(f"\n💾 Mapping gespeichert: {mapping_file}")

def main():
    print("🎯 SUBREDDIT MAPPING ERSTELLEN")
    print("="*60)
    print("Verwende NUR Subreddits aus target_subreddits_extended.txt")
    print("Blacklist: adhdwomen (gesperrt)")
    print()
    
    update_posts_with_alternatives()

if __name__ == "__main__":
    main()