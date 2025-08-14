#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Erstellt minimale Variationen für alle Posts und speichert sie in post_data.json
"""

import json
import requests
from pathlib import Path
import time
import random

class CreateVariations:
    def __init__(self):
        self.posts_dir = Path("data_all/Posts")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # OpenRouter API Key aus config.py
        try:
            from config import OPENROUTER_API_KEY
            self.api_key = OPENROUTER_API_KEY
        except ImportError:
            print("❌ Kein API Key in config.py gefunden!")
            exit(1)
        
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'already_varied': 0
        }
    
    def create_minimal_variation(self, title, selftext=""):
        """Erstellt minimale Variation mit AI"""
        
        prompt = f"""You are modifying Reddit posts MINIMALLY. Change ONLY 1-2 small details.

RULES:
- Change MAXIMUM 1-2 words or numbers
- NEVER change: ADHD, autism, mental health terms
- ONLY change: times (3am→4am), years (10→11), numbers, or minor adjectives
- Keep 95% exactly the same
- If unsure, change LESS

Original Title: {title}

Return ONLY the modified title, nothing else."""

        if selftext and len(selftext) > 50:
            prompt += f"""

Also modify the text minimally (1-2 words only):
Original Text: {selftext[:1000]}

Return format:
TITLE: [modified title]
TEXT: [modified text]"""
        
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
                    "max_tokens": 1000
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                if selftext and "TEXT:" in content:
                    # Parse title and text
                    lines = content.split('\n')
                    new_title = title  # Default
                    new_text = selftext  # Default
                    
                    for line in lines:
                        if line.startswith("TITLE:"):
                            new_title = line.replace("TITLE:", "").strip()
                        elif line.startswith("TEXT:"):
                            # Get all text after TEXT:
                            idx = content.find("TEXT:")
                            new_text = content[idx+5:].strip()
                            break
                    
                    return new_title, new_text
                else:
                    # Just title
                    return content.replace("TITLE:", "").strip(), selftext
                    
            elif response.status_code == 429:
                print(f"   ⏱️ Rate limit - warte 5 Sekunden...")
                time.sleep(5)
                return None, None
            else:
                print(f"   ❌ API Fehler: {response.status_code}")
                return None, None
                
        except Exception as e:
            print(f"   ❌ Fehler: {str(e)[:100]}")
            return None, None
    
    def process_all_posts(self):
        """Verarbeitet alle Posts"""
        print("🔄 ERSTELLE MINIMALE VARIATIONEN")
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
                self.stats['already_varied'] += 1
                continue
            
            print(f"[{i}/{total}] {post_dir.name[:40]}...")
            
            # Original Daten
            original_title = post_data.get('title', '')
            original_text = post_data.get('selftext', '')
            
            # Erstelle Variation
            varied_title, varied_text = self.create_minimal_variation(
                original_title, 
                original_text
            )
            
            if varied_title and varied_title != original_title:
                # Speichere Variationen
                post_data['varied_title'] = varied_title
                if varied_text and varied_text != original_text:
                    post_data['varied_selftext'] = varied_text
                
                # Speichere zurück
                with open(json_file, 'w') as f:
                    json.dump(post_data, f, indent=2, ensure_ascii=False)
                
                self.stats['success'] += 1
                print(f"   ✅ Variiert: '{original_title[:40]}...'")
                print(f"      → '{varied_title[:40]}...'")
            else:
                self.stats['failed'] += 1
                print(f"   ❌ Fehlgeschlagen oder keine Änderung")
            
            # Kurze Pause zwischen Requests
            if i % 10 == 0:
                print(f"\n⏸️ Pause nach {i} Posts...\n")
                time.sleep(3)
            else:
                time.sleep(random.uniform(0.5, 1.5))
        
        # Statistiken
        print("\n" + "="*60)
        print("📊 FERTIG!")
        print(f"   Total: {self.stats['total']} Posts")
        print(f"   ✅ Erfolgreich variiert: {self.stats['success']}")
        print(f"   ⏭️ Bereits variiert: {self.stats['already_varied']}")
        print(f"   ❌ Fehlgeschlagen: {self.stats['failed']}")
        print(f"   Erfolgsrate: {self.stats['success']/max(1, self.stats['total']-self.stats['already_varied'])*100:.1f}%")

if __name__ == "__main__":
    variator = CreateVariations()
    variator.process_all_posts()