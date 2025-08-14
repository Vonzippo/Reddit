#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Variiert Text-Posts aus data_text mit AI
Ändert ~20% der Wörter während Stil und Emotionen erhalten bleiben
"""

import json
import requests
from pathlib import Path
import time
import random

class TextPostVariator:
    def __init__(self):
        self.posts_dir = Path("data_text/Posts")
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
    
    def create_text_variation(self, title, text):
        """Erstellt Variation mit ~20% Wortänderungen"""
        
        prompt = f"""You are rewriting Reddit posts to avoid detection while keeping the EXACT same meaning, emotion, and writing style.

STRICT RULES:
1. Change approximately 20% of words (synonyms, rephrasing)
2. KEEP the same emotional tone (if angry, stay angry; if sad, stay sad)
3. KEEP the same writing style (casual/formal, punctuation habits)
4. KEEP the same paragraph structure
5. KEEP all specific details (numbers, names, places)
6. DO NOT add new information or remove information
7. DO NOT change the story or message
8. DO NOT make it sound more formal or AI-generated

Original Title: {title}

Original Text (first 2000 chars):
{text[:2000]}

Rewrite this naturally with ~20% word changes. Keep the EXACT same voice and emotion.

Return format:
TITLE: [varied title]
---
TEXT: [full varied text]"""

        try:
            response = requests.post(
                self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3.5-haiku-20241022",  # Besseres Modell für Text
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,  # Etwas kreativer für natürliche Variation
                    "max_tokens": 3000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Parse Antwort
                if "---" in content:
                    parts = content.split("---", 1)
                    title_part = parts[0]
                    text_part = parts[1] if len(parts) > 1 else text
                    
                    # Extrahiere Titel
                    if "TITLE:" in title_part:
                        new_title = title_part.replace("TITLE:", "").strip()
                    else:
                        new_title = title_part.strip()
                    
                    # Extrahiere Text
                    if "TEXT:" in text_part:
                        new_text = text_part.replace("TEXT:", "").strip()
                    else:
                        new_text = text_part.strip()
                    
                    return new_title, new_text
                else:
                    # Fallback parsing
                    lines = content.split('\n')
                    new_title = title
                    new_text = text
                    
                    for i, line in enumerate(lines):
                        if line.startswith("TITLE:"):
                            new_title = line.replace("TITLE:", "").strip()
                        elif line.startswith("TEXT:"):
                            new_text = '\n'.join(lines[i:]).replace("TEXT:", "").strip()
                            break
                    
                    return new_title, new_text
                    
            elif response.status_code == 429:
                print(f"   ⏱️ Rate limit - warte 10 Sekunden...")
                time.sleep(10)
                return None, None
            else:
                print(f"   ❌ API Fehler: {response.status_code}")
                if response.text:
                    print(f"   Details: {response.text[:200]}")
                return None, None
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout - überspringe...")
            return None, None
        except Exception as e:
            print(f"   ❌ Fehler: {str(e)[:100]}")
            return None, None
    
    def process_all_posts(self):
        """Verarbeitet alle Text-Posts"""
        print("🔄 VARIIERE TEXT-POSTS MIT AI")
        print("="*60)
        print("📝 Ändere ~20% der Wörter, behalte Stil & Emotionen")
        print()
        
        post_dirs = sorted(list(self.posts_dir.iterdir()))
        total = len([d for d in post_dirs if d.is_dir()])
        
        print(f"📊 Gefunden: {total} Text-Posts")
        print()
        
        for i, post_dir in enumerate(post_dirs, 1):
            if not post_dir.is_dir():
                continue
            
            self.stats['total'] += 1
            
            json_file = post_dir / "post_data.json"
            content_file = post_dir / "post_content.txt"
            
            if not json_file.exists() or not content_file.exists():
                print(f"[{i}/{total}] ⚠️ {post_dir.name[:40]} - Dateien fehlen")
                continue
            
            # Lade Post-Daten
            with open(json_file, 'r', encoding='utf-8') as f:
                post_data = json.load(f)
            
            # Skip wenn schon variiert
            if 'varied_title' in post_data:
                self.stats['already_varied'] += 1
                print(f"[{i}/{total}] ⏭️ {post_dir.name[:40]} - bereits variiert")
                continue
            
            # Lade Original-Text
            with open(content_file, 'r', encoding='utf-8') as f:
                original_text = f.read()
            
            original_title = post_data.get('title', '')
            
            print(f"[{i}/{total}] 🔄 {post_dir.name[:40]}...")
            
            # Erstelle Variation mit AI
            varied_title, varied_text = self.create_text_variation(
                original_title, 
                original_text
            )
            
            if varied_title and varied_text:
                # Speichere Variationen
                post_data['varied_title'] = varied_title
                post_data['varied_selftext'] = varied_text
                
                # Speichere JSON zurück
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(post_data, f, indent=2, ensure_ascii=False)
                
                # Speichere variierten Text auch als Datei
                varied_content_file = post_dir / "post_content_varied.txt"
                with open(varied_content_file, 'w', encoding='utf-8') as f:
                    f.write(varied_text)
                
                self.stats['success'] += 1
                
                # Zeige Beispiel der Änderung (erste 100 Zeichen)
                print(f"   ✅ Original: \"{original_title[:60]}...\"")
                print(f"      Variiert: \"{varied_title[:60]}...\"")
                
                # Zeige Textänderung (erste Zeile)
                orig_first_line = original_text.split('\n')[0][:80] if original_text else ""
                var_first_line = varied_text.split('\n')[0][:80] if varied_text else ""
                if orig_first_line and var_first_line:
                    print(f"   📝 Text: \"{orig_first_line}...\"")
                    print(f"      → \"{var_first_line}...\"")
            else:
                self.stats['failed'] += 1
                print(f"   ❌ Variation fehlgeschlagen")
            
            # Pause zwischen Requests
            if i < total:  # Nicht nach dem letzten
                wait_time = random.uniform(2, 4)
                print(f"   ⏸️ Warte {wait_time:.1f}s...")
                time.sleep(wait_time)
            
            # Längere Pause alle 10 Posts
            if i % 10 == 0 and i < total:
                print(f"\n💤 Pause nach {i} Posts (15s)...\n")
                time.sleep(15)
        
        # Statistiken
        print("\n" + "="*60)
        print("📊 FERTIG!")
        print(f"   Total: {self.stats['total']} Posts")
        print(f"   ✅ Erfolgreich variiert: {self.stats['success']}")
        print(f"   ⏭️ Bereits variiert: {self.stats['already_varied']}")
        print(f"   ❌ Fehlgeschlagen: {self.stats['failed']}")
        
        if self.stats['success'] > 0:
            print(f"\n✨ Erfolgsrate: {self.stats['success']/(self.stats['total']-self.stats['already_varied'])*100:.1f}%")
            print("\n💡 Die Texte wurden mit ~20% Wortänderungen variiert.")
            print("   Stil, Emotionen und Inhalt bleiben erhalten!")

if __name__ == "__main__":
    print("🚀 Starte Text-Post Variation mit AI...")
    print("   Model: Claude 3.5 Haiku")
    print("   Ziel: ~20% Wortänderungen, gleicher Stil")
    print()
    
    variator = TextPostVariator()
    variator.process_all_posts()