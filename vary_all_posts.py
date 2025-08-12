#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Variiert ALLE Posts in data_all minimal (1-2 Wörter)
Nutzt OpenRouter API für intelligente Variationen
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
            print(f"✅ API Key geladen")
        except ImportError:
            self.api_key = ""
            print("❌ Kein API Key gefunden")
        
        self.stats = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'api_errors': 0
        }
    
    def create_minimal_variation(self, title, selftext=""):
        """Erstellt minimale Variation mit AI"""
        
        # Prompt für MINIMALE Änderungen
        prompt = f"""You are modifying Reddit posts MINIMALLY. Change ONLY 1-2 small details.

RULES:
- Change MAXIMUM 1-2 words or numbers
- NEVER change: ADHD, autism, mental health terms, subreddit names
- ONLY change: times (3am→4am), years (10→11), small numbers, or minor adjectives (big→large, nice→good)
- Keep 95% exactly the same
- If unsure, change LESS

Original Title: {title}

Return ONLY the modified title, nothing else. Make the SMALLEST possible change."""

        if selftext and len(selftext.strip()) > 10:
            prompt += f"\n\nOriginal Text (first 500 chars): {selftext[:500]}\n\nReturn modified title on first line, then modified text. Make MINIMAL changes."
        
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
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                modified = result['choices'][0]['message']['content'].strip()
                
                if selftext and len(selftext.strip()) > 10:
                    # Split in Titel und Text
                    lines = modified.split('\n', 1)
                    new_title = lines[0] if lines else title
                    new_text = lines[1] if len(lines) > 1 else selftext
                    return new_title, new_text
                else:
                    return modified, selftext
                    
            elif response.status_code == 429:
                self.stats['api_errors'] += 1
                print(f"      ⏳ Rate limit - warte länger...")
                time.sleep(5)  # Extra Pause bei Rate Limit
                return None, None
            else:
                print(f"      ❌ API Fehler: {response.status_code}")
                return None, None
                
        except Exception as e:
            print(f"      ❌ Fehler: {str(e)[:50]}")
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
            self.stats['skipped'] += 1
            return False
        
        # Skip wenn Titel zu kurz
        if len(original_title) < 10:
            self.stats['skipped'] += 1
            return False
        
        # Erstelle minimale Variation
        new_title, new_text = self.create_minimal_variation(original_title, original_text)
        
        if not new_title:
            self.stats['failed'] += 1
            return False
        
        # Speichere Original wenn noch nicht vorhanden
        if 'original_title' not in post_data:
            post_data['original_title'] = original_title
        
        post_data['title'] = new_title
        
        if original_text and new_text != original_text:
            if 'original_selftext' not in post_data:
                post_data['original_selftext'] = original_text
            post_data['selftext'] = new_text
        
        post_data['minimally_varied'] = True
        post_data['variation_date'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Speichere zurück
        with open(json_file, 'w') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        
        self.stats['success'] += 1
        
        # Zeige Fortschritt nur bei Erfolg
        if new_title != original_title:
            # Berechne Änderungen
            orig_words = original_title.split()
            new_words = new_title.split()
            changes = sum(1 for o, n in zip(orig_words, new_words) if o != n)
            if changes > 0:
                print(f"   ✅ {changes} Wort(e) geändert")
        
        return True
    
    def process_all_posts(self):
        """Verarbeitet alle Posts in data_all"""
        
        print("\n🚀 VARIIERE ALLE POSTS IN DATA_ALL")
        print("="*60)
        print("• Ändere nur 1-2 Wörter pro Post")
        print("• ADHD/Autism/Mental Health bleiben unverändert")
        print("• Zahlen und kleine Adjektive können angepasst werden")
        print()
        
        # Sammle alle Post-Ordner
        post_dirs = [d for d in self.posts_dir.iterdir() if d.is_dir()]
        total = len(post_dirs)
        
        print(f"📊 Verarbeite {total} Posts...")
        print(f"⏳ Geschätzte Zeit: {total * 2.5 / 60:.1f} Minuten")
        print()
        
        # Verarbeite Posts in Batches
        batch_size = 10
        for i in range(0, total, batch_size):
            batch = post_dirs[i:i+batch_size]
            batch_end = min(i+batch_size, total)
            
            print(f"\n📦 Batch {i//batch_size + 1}: Posts {i+1}-{batch_end}")
            print("-"*40)
            
            for post_dir in batch:
                self.stats['processed'] += 1
                
                # Zeige Fortschritt
                if self.stats['processed'] % 5 == 0:
                    print(f"   [{self.stats['processed']}/{total}] {post_dir.name[:30]}...", end="")
                
                # Verarbeite Post
                success = self.process_single_post(post_dir)
                
                # Pause zwischen API Calls
                if success:
                    time.sleep(random.uniform(2.5, 3.5))
                else:
                    time.sleep(0.5)
            
            # Status nach jedem Batch
            success_rate = (self.stats['success'] / max(self.stats['processed'], 1)) * 100
            print(f"\n   Status: {self.stats['success']} erfolgreich ({success_rate:.1f}%), "
                  f"{self.stats['skipped']} übersprungen, {self.stats['failed']} fehlgeschlagen")
            
            # Längere Pause nach jedem Batch
            if i + batch_size < total:
                print(f"   💤 Pause zwischen Batches...")
                time.sleep(5)
        
        # Finale Statistiken
        self.print_final_stats()
    
    def print_final_stats(self):
        """Zeigt finale Statistiken"""
        print("\n" + "="*60)
        print("✅ VARIATION ALLER POSTS ABGESCHLOSSEN!")
        print("="*60)
        print(f"📊 FINALE STATISTIKEN:")
        print(f"   Gesamt verarbeitet: {self.stats['processed']}")
        print(f"   ✅ Erfolgreich variiert: {self.stats['success']}")
        print(f"   ⏭️ Übersprungen: {self.stats['skipped']}")
        print(f"   ❌ Fehlgeschlagen: {self.stats['failed']}")
        
        if self.stats['api_errors'] > 0:
            print(f"   ⚠️ API Rate Limits: {self.stats['api_errors']}")
        
        success_rate = (self.stats['success'] / max(self.stats['processed'], 1)) * 100
        print(f"\n   Erfolgsrate: {success_rate:.1f}%")
        
        if self.stats['success'] > 0:
            print(f"\n✨ {self.stats['success']} Posts wurden minimal angepasst!")
            print("   Die Originale wurden gespeichert.")

def main():
    print("🔄 MINIMALE VARIATION ALLER POSTS")
    print("="*60)
    
    variator = MinimalPostVariator()
    
    if not variator.api_key:
        print("❌ Kein API Key gefunden! Abbruch.")
        return
    
    # Direkt alle Posts verarbeiten
    variator.process_all_posts()

if __name__ == "__main__":
    main()