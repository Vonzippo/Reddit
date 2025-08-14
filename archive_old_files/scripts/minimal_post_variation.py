#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Passt Posts MINIMAL an - nur 1-2 Wörter ändern
Nutzt AI für intelligente aber minimale Variationen
"""

import json
import requests
from pathlib import Path
import time
import random

class MinimalPostVariator:
    def __init__(self):
        self.posts_dir = Path("/Users/patrick/Desktop/Reddit/data_all/Posts")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # OpenRouter API Key aus config.py
        try:
            from config import OPENROUTER_API_KEY
            self.api_key = OPENROUTER_API_KEY
        except ImportError:
            self.api_key = ""  # Fallback
        
        self.stats = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def get_api_key(self):
        """Prüft ob API Key vorhanden"""
        if not self.api_key:
            print("❌ Kein OpenRouter API Key gefunden!")
            print("   Bitte in config.py setzen")
            return False
        return True
    
    def create_minimal_variation(self, title, selftext=""):
        """Erstellt minimale Variation mit AI"""
        
        # Prompt für MINIMALE Änderungen
        prompt = f"""You are modifying Reddit posts MINIMALLY. Change ONLY 1-2 small details.

RULES:
- Change MAXIMUM 1-2 words or numbers
- NEVER change: ADHD, autism, mental health terms, subreddit names
- ONLY change: times (3am→4am), years (10→11), small numbers, or minor adjectives
- Keep 95% exactly the same
- If unsure, change LESS

Original Title: {title}

Return ONLY the modified title, nothing else. Make the SMALLEST possible change."""

        if selftext:
            prompt += f"\n\nOriginal Text: {selftext[:500]}\n\nReturn modified title on first line, then modified text. Make MINIMAL changes."
        
        try:
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/llama-3.2-3b-instruct:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,  # Niedrig für konsistente Änderungen
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                modified = result['choices'][0]['message']['content'].strip()
                
                if selftext:
                    # Split in Titel und Text
                    lines = modified.split('\n', 1)
                    new_title = lines[0] if lines else title
                    new_text = lines[1] if len(lines) > 1 else selftext
                    return new_title, new_text
                else:
                    return modified, ""
            else:
                print(f"   ❌ API Fehler: {response.status_code}")
                return None, None
                
        except Exception as e:
            print(f"   ❌ Fehler: {str(e)[:50]}")
            return None, None
    
    def process_single_post(self, post_dir):
        """Verarbeitet einen einzelnen Post"""
        
        json_file = post_dir / "post_data.json"
        if not json_file.exists():
            return False
        
        # Lade Original
        with open(json_file, 'r') as f:
            post_data = json.load(f)
        
        original_title = post_data.get('title', '')
        original_text = post_data.get('selftext', '')
        
        # Skip wenn schon bearbeitet
        if post_data.get('minimally_varied', False):
            print(f"   ⏭️ Bereits bearbeitet")
            self.stats['skipped'] += 1
            return False
        
        print(f"\n📝 {post_dir.name}:")
        print(f"   Original: {original_title[:60]}...")
        
        # Erstelle minimale Variation
        new_title, new_text = self.create_minimal_variation(original_title, original_text)
        
        if not new_title:
            print(f"   ❌ Variation fehlgeschlagen")
            self.stats['failed'] += 1
            return False
        
        # Zeige Änderungen
        if new_title != original_title:
            print(f"   ✅ Neu: {new_title[:60]}...")
            
            # Zähle Wortänderungen
            orig_words = original_title.split()
            new_words = new_title.split()
            changes = sum(1 for o, n in zip(orig_words, new_words) if o != n)
            print(f"   📊 {changes} Wort(e) geändert")
        else:
            print(f"   ℹ️ Keine Änderung nötig")
        
        # Speichere Variationen
        post_data['original_title'] = original_title
        post_data['title'] = new_title
        
        if original_text:
            post_data['original_selftext'] = original_text
            post_data['selftext'] = new_text
        
        post_data['minimally_varied'] = True
        post_data['variation_date'] = time.strftime("%Y-%m-%d")
        
        # Speichere zurück
        with open(json_file, 'w') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        
        self.stats['success'] += 1
        return True
    
    def process_all_posts(self, limit=None):
        """Verarbeitet alle Posts"""
        
        print("🚀 MINIMALE POST-VARIATION")
        print("="*60)
        print("Ändere nur 1-2 Wörter pro Post")
        print("NICHT ändern: ADHD, wichtige Keywords")
        print()
        
        # API Key prüfen
        if not self.get_api_key():
            print("❌ Kein API Key!")
            return
        
        posts = list(self.posts_dir.iterdir())
        if limit:
            posts = posts[:limit]
        
        print(f"📊 Verarbeite {len(posts)} Posts...")
        
        for i, post_dir in enumerate(posts, 1):
            if not post_dir.is_dir():
                continue
            
            self.stats['processed'] += 1
            
            # Verarbeite Post
            self.process_single_post(post_dir)
            
            # Status Update
            if i % 10 == 0:
                print(f"\n--- Fortschritt: {i}/{len(posts)} ---")
                print(f"✅ Erfolgreich: {self.stats['success']}")
                print(f"⏭️ Übersprungen: {self.stats['skipped']}")
                print(f"❌ Fehlgeschlagen: {self.stats['failed']}")
            
            # Längere Pause für API (wegen Rate Limits)
            time.sleep(random.uniform(2, 3))
        
        # Finale Statistiken
        self.print_stats()
    
    def print_stats(self):
        """Zeigt finale Statistiken"""
        print("\n" + "="*60)
        print("✅ VARIATION ABGESCHLOSSEN!")
        print("="*60)
        print(f"📊 STATISTIKEN:")
        print(f"   Verarbeitet: {self.stats['processed']}")
        print(f"   Erfolgreich: {self.stats['success']}")
        print(f"   Übersprungen: {self.stats['skipped']}")  
        print(f"   Fehlgeschlagen: {self.stats['failed']}")

def main():
    print("🔄 MINIMALE POST-VARIATION MIT AI")
    print("="*60)
    print("⚠️ WICHTIG:")
    print("- Nur 1-2 Wörter werden geändert")
    print("- ADHD, autism etc. bleiben IMMER gleich")
    print("- Zahlen/Zeiten können leicht variiert werden")
    print()
    
    variator = MinimalPostVariator()
    
    # Erst mal nur 5 Posts zum Testen
    print("Teste mit ersten 5 Posts...")
    variator.process_all_posts(limit=5)
    
    # Wenn gut, dann alle
    if variator.stats['success'] > 0:
        cont = input("\n✅ Test erfolgreich! Alle Posts bearbeiten? (j/n): ").lower()
        if cont in ['j', 'ja', 'yes']:
            variator.stats = {'processed': 0, 'success': 0, 'failed': 0, 'skipped': 0}
            variator.process_all_posts()

if __name__ == "__main__":
    main()