#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Korrigiert alle hardcoded Pfade auf relative Pfade
"""

import os
from pathlib import Path

def fix_paths():
    """Ändert alle absoluten Pfade auf relative Pfade"""
    
    # Liste der wichtigsten Dateien die angepasst werden müssen
    files_to_fix = [
        'main.py',
        'main_other.py', 
        'auto_post_comment_bot.py',
        'kommentare_bot.py',
        'create_simple_variations.py',
        'create_variations.py',
        'fix_subreddit_mapping.py',
        'fix_subreddit_mapping_improved.py'
    ]
    
    replacements = {
        '/Users/patrick/Desktop/Reddit/data_all': 'data_all',
        '/Users/patrick/Desktop/Reddit/data': 'data',
        '/Users/patrick/Desktop/Reddit/': './',
        'Path("/Users/patrick/Desktop/Reddit/data_all/Posts")': 'Path("data_all/Posts")',
        'Path("/Users/patrick/Desktop/Reddit/data_all")': 'Path("data_all")',
        'Path("/Users/patrick/Desktop/Reddit/data")': 'Path("data")',
        'Path("/Users/patrick/Desktop/Reddit")': 'Path(".")',
        '"/Users/patrick/Desktop/Reddit/daily_post_stats.json"': '"daily_post_stats.json"',
        '"/Users/patrick/Desktop/Reddit/history.json"': '"history.json"',
        '"/Users/patrick/Desktop/Reddit/comment_history.json"': '"comment_history.json"',
    }
    
    fixed_count = 0
    
    print("🔧 KORRIGIERE ABSOLUTE PFADE")
    print("="*60)
    
    for filename in files_to_fix:
        filepath = Path(filename)
        if not filepath.exists():
            print(f"⚠️ Datei nicht gefunden: {filename}")
            continue
            
        print(f"\n📝 Bearbeite: {filename}")
        
        # Lese Datei
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Wende alle Ersetzungen an
        modified = False
        for old_path, new_path in replacements.items():
            if old_path in content:
                content = content.replace(old_path, new_path)
                modified = True
                print(f"   ✅ Ersetzt: {old_path[:50]}... → {new_path}")
        
        # Speichere wenn geändert
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_count += 1
            print(f"   💾 Gespeichert!")
        else:
            print(f"   ℹ️ Keine Änderungen nötig")
    
    print("\n" + "="*60)
    print(f"✅ FERTIG! {fixed_count} Dateien korrigiert")
    print("\n💡 Die Scripts nutzen jetzt relative Pfade und funktionieren")
    print("   in jedem Verzeichnis wo sie ausgeführt werden.")

if __name__ == "__main__":
    fix_paths()