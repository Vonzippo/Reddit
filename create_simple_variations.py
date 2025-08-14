#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Erstellt einfache regel-basierte Variationen ohne API
"""

import json
import random
from pathlib import Path

class SimpleVariator:
    def __init__(self):
        self.posts_dir = Path("data_all/Posts")
        
        # Einfache Ersetzungen
        self.number_variations = {
            '1': ['2', '3'],
            '2': ['3', '4'],
            '3': ['4', '5'],
            '4': ['5', '6'],
            '5': ['6', '7'],
            '6': ['7', '8'],
            '7': ['8', '9'],
            '8': ['9', '10'],
            '9': ['10', '11'],
            '10': ['11', '12'],
            '15': ['16', '17'],
            '20': ['21', '22'],
            '30': ['31', '32'],
            'one': ['two', 'three'],
            'two': ['three', 'four'],
            'three': ['four', 'five'],
            'first': ['second', 'initial'],
            'last': ['final', 'previous'],
        }
        
        self.time_variations = {
            'morning': ['afternoon', 'evening'],
            'afternoon': ['evening', 'morning'],
            'evening': ['night', 'afternoon'],
            'night': ['evening', 'morning'],
            'today': ['yesterday', 'recently'],
            'yesterday': ['today', 'recently'],
            'week': ['month', 'weeks'],
            'month': ['months', 'week'],
            'year': ['years', 'time'],
            'years': ['year', 'time'],
            'minutes': ['moments', 'mins'],
            'hours': ['hour', 'time'],
            'days': ['day', 'time'],
        }
        
        self.adjective_variations = {
            'amazing': ['great', 'wonderful'],
            'great': ['good', 'nice'],
            'good': ['nice', 'fine'],
            'bad': ['tough', 'hard'],
            'terrible': ['awful', 'bad'],
            'awful': ['terrible', 'bad'],
            'huge': ['big', 'large'],
            'big': ['large', 'huge'],
            'small': ['little', 'tiny'],
            'little': ['small', 'tiny'],
            'new': ['recent', 'fresh'],
            'old': ['older', 'aged'],
            'finally': ['at last', 'eventually'],
            'actually': ['really', 'truly'],
            'really': ['truly', 'actually'],
            'super': ['very', 'extremely'],
            'very': ['quite', 'really'],
            'extremely': ['very', 'super'],
        }
        
        self.stats = {
            'total': 0,
            'varied': 0,
            'skipped': 0
        }
    
    def create_variation(self, text):
        """Erstellt einfache Variation durch Ersetzung"""
        if not text:
            return text
            
        words = text.split()
        modified = False
        changes = 0
        max_changes = 2  # Maximal 2 Änderungen
        
        for i, word in enumerate(words):
            if changes >= max_changes:
                break
                
            # Bereinige Wort für Vergleich
            clean_word = word.lower().strip('.,!?;:()"')
            
            # Prüfe verschiedene Variationen
            for variations_dict in [self.number_variations, self.time_variations, self.adjective_variations]:
                if clean_word in variations_dict:
                    # Wähle zufällige Ersetzung
                    replacement = random.choice(variations_dict[clean_word])
                    
                    # Behalte Groß-/Kleinschreibung
                    if word[0].isupper():
                        replacement = replacement.capitalize()
                    
                    # Behalte Satzzeichen
                    if word != clean_word:
                        # Finde Satzzeichen
                        prefix = word[:word.lower().find(clean_word)]
                        suffix = word[word.lower().find(clean_word) + len(clean_word):]
                        replacement = prefix + replacement + suffix
                    
                    words[i] = replacement
                    modified = True
                    changes += 1
                    break
        
        if modified:
            return ' '.join(words)
        return text
    
    def process_all_posts(self):
        """Verarbeitet alle Posts"""
        print("🔄 ERSTELLE EINFACHE VARIATIONEN")
        print("="*60)
        
        post_dirs = list(self.posts_dir.iterdir())
        total = len([d for d in post_dirs if d.is_dir()])
        
        print(f"📊 Gefunden: {total} Posts")
        print()
        
        for i, post_dir in enumerate(post_dirs, 1):
            if not post_dir.is_dir():
                continue
            
            self.stats['total'] += 1
            
            json_file = post_dir / "post_data.json"
            if not json_file.exists():
                continue
            
            # Lade Post-Daten
            with open(json_file, 'r') as f:
                post_data = json.load(f)
            
            # Skip wenn schon variiert
            if 'varied_title' in post_data:
                self.stats['skipped'] += 1
                continue
            
            # Original Daten
            original_title = post_data.get('title', '')
            original_text = post_data.get('selftext', '')
            
            # Erstelle Variation
            varied_title = self.create_variation(original_title)
            
            # Nur Text variieren wenn er existiert und nicht zu lang ist
            varied_text = original_text
            if original_text and len(original_text) < 5000:
                varied_text = self.create_variation(original_text)
            
            # Speichere wenn verändert
            if varied_title != original_title or varied_text != original_text:
                post_data['varied_title'] = varied_title
                if varied_text != original_text:
                    post_data['varied_selftext'] = varied_text
                
                # Speichere zurück
                with open(json_file, 'w') as f:
                    json.dump(post_data, f, indent=2, ensure_ascii=False)
                
                self.stats['varied'] += 1
                
                if i <= 10 or i % 50 == 0:  # Zeige erste 10 und dann jeden 50.
                    print(f"[{i}/{total}] ✅ {post_dir.name[:30]}")
                    if varied_title != original_title:
                        print(f"   Original: {original_title[:60]}...")
                        print(f"   Variiert: {varied_title[:60]}...")
        
        # Statistiken
        print("\n" + "="*60)
        print("📊 FERTIG!")
        print(f"   Total: {self.stats['total']} Posts")
        print(f"   ✅ Variiert: {self.stats['varied']}")
        print(f"   ⏭️ Übersprungen: {self.stats['skipped']}")
        print(f"   Erfolgsrate: {self.stats['varied']/max(1, self.stats['total'])*100:.1f}%")

if __name__ == "__main__":
    variator = SimpleVariator()
    variator.process_all_posts()