#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Cleanup Script für data_all Ordner
- Entfernt Posts mit gelöschten Bildern (404)
- Reduziert Größe auf unter 500 MB für GitHub
- Analysiert welche Bilder noch verfügbar sind
"""

import json
import shutil
from pathlib import Path
import urllib.request

class DataAllCleaner:
    def __init__(self):
        self.data_dir = Path("/Users/patrick/Desktop/Reddit/data_all/Posts")
        self.stats = {
            'total_posts': 0,
            'with_images': 0,
            'without_images': 0,
            'images_still_valid': 0,
            'images_deleted': 0,
            'posts_removed': 0,
            'size_before': 0,
            'size_after': 0
        }
        
    def get_folder_size(self, path):
        """Berechnet Ordnergröße in MB"""
        total = sum(f.stat().st_size for f in Path(path).rglob('*') if f.is_file())
        return total / (1024 * 1024)
    
    def check_image_url(self, url):
        """Prüft ob Bild-URL noch verfügbar ist"""
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Method': 'HEAD'  # Nur Header, kein Download
            })
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except:
            return False
    
    def analyze_posts(self):
        """Analysiert alle Posts und ihre Bilder"""
        print("📊 Analysiere Posts...")
        
        results = []
        
        for post_dir in sorted(self.data_dir.iterdir()):
            if not post_dir.is_dir():
                continue
            
            self.stats['total_posts'] += 1
            
            # Lade post_data.json
            json_file = post_dir / "post_data.json"
            if not json_file.exists():
                continue
            
            with open(json_file, 'r') as f:
                post_data = json.load(f)
            
            # Prüfe ob lokales Bild existiert
            has_local_image = False
            image_size = 0
            
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                img_path = post_dir / f"image{ext}"
                if img_path.exists():
                    has_local_image = True
                    image_size = img_path.stat().st_size / (1024 * 1024)  # MB
                    self.stats['with_images'] += 1
                    break
            
            if not has_local_image:
                self.stats['without_images'] += 1
            
            # Sammle Info
            results.append({
                'dir': post_dir,
                'title': post_data.get('title', ''),
                'score': post_data.get('score', 0),
                'subreddit': post_data.get('subreddit', ''),
                'url': post_data.get('url', ''),
                'has_image': has_local_image,
                'image_size': image_size,
                'is_text_post': bool(post_data.get('selftext', ''))
            })
            
            # Status alle 100 Posts
            if self.stats['total_posts'] % 100 == 0:
                print(f"   Analysiert: {self.stats['total_posts']} Posts...")
        
        return results
    
    def remove_posts_without_images(self, posts):
        """Entfernt Posts ohne Bilder (außer Text-Posts)"""
        removed = []
        
        for post in posts:
            # Behalte Text-Posts
            if post['is_text_post']:
                continue
            
            # Entferne Posts ohne lokale Bilder
            if not post['has_image']:
                print(f"   ❌ Entferne: {post['dir'].name} (kein Bild)")
                shutil.rmtree(post['dir'])
                removed.append(post)
                self.stats['posts_removed'] += 1
        
        return [p for p in posts if p not in removed]
    
    def optimize_for_size(self, posts, target_mb=450):
        """Optimiert auf Zielgröße"""
        # Sortiere nach Score (niedrigste zuerst)
        posts_sorted = sorted(posts, key=lambda x: x['score'])
        
        current_size = self.get_folder_size(self.data_dir.parent)
        removed = []
        
        print(f"\n📉 Reduziere Größe von {current_size:.1f} MB auf unter {target_mb} MB...")
        
        for post in posts_sorted:
            if current_size <= target_mb:
                break
            
            # Entferne Posts mit niedrigem Score
            if post['score'] < 50:  # Threshold
                print(f"   ❌ Entferne: Score {post['score']} - {post['title'][:40]}...")
                shutil.rmtree(post['dir'])
                removed.append(post)
                self.stats['posts_removed'] += 1
                
                # Schätze neue Größe
                current_size -= post['image_size']
                current_size -= 0.01  # JSON/Text files
        
        return [p for p in posts if p not in removed]
    
    def remove_large_images(self, posts, max_image_mb=10):
        """Entfernt sehr große Bilder"""
        removed = []
        
        for post in posts:
            if post['image_size'] > max_image_mb:
                print(f"   ❌ Entferne: {post['image_size']:.1f} MB Bild - {post['title'][:40]}...")
                shutil.rmtree(post['dir'])
                removed.append(post)
                self.stats['posts_removed'] += 1
        
        return [p for p in posts if p not in removed]
    
    def create_summary(self, posts):
        """Erstellt Zusammenfassung"""
        summary_file = self.data_dir.parent / "cleanup_summary.json"
        
        summary = {
            'stats': self.stats,
            'remaining_posts': len(posts),
            'top_posts': [
                {
                    'title': p['title'],
                    'score': p['score'],
                    'subreddit': p['subreddit'],
                    'has_image': p['has_image']
                }
                for p in sorted(posts, key=lambda x: x['score'], reverse=True)[:20]
            ],
            'size_mb': self.get_folder_size(self.data_dir.parent)
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
    
    def run_cleanup(self):
        """Hauptfunktion"""
        print("🧹 DATA_ALL CLEANUP")
        print("="*60)
        
        # Größe vorher
        self.stats['size_before'] = self.get_folder_size(self.data_dir.parent)
        print(f"📊 Größe vorher: {self.stats['size_before']:.1f} MB")
        
        # Analysiere Posts
        posts = self.analyze_posts()
        print(f"✅ {len(posts)} Posts analysiert")
        
        # Schritt 1: Entferne Posts ohne Bilder
        print("\n🗑️ Schritt 1: Entferne Posts ohne Bilder...")
        posts = self.remove_posts_without_images(posts)
        
        # Schritt 2: Entferne sehr große Bilder (>10MB)
        print("\n🗑️ Schritt 2: Entferne sehr große Bilder...")
        posts = self.remove_large_images(posts)
        
        # Schritt 3: Optimiere auf Zielgröße
        current_size = self.get_folder_size(self.data_dir.parent)
        if current_size > 450:
            print("\n🗑️ Schritt 3: Optimiere auf < 450 MB...")
            posts = self.optimize_for_size(posts, target_mb=450)
        
        # Größe nachher
        self.stats['size_after'] = self.get_folder_size(self.data_dir.parent)
        
        # Erstelle Zusammenfassung
        summary = self.create_summary(posts)
        
        # Zeige Ergebnisse
        print("\n" + "="*60)
        print("✅ CLEANUP ABGESCHLOSSEN!")
        print("="*60)
        print(f"📊 ERGEBNISSE:")
        print(f"   Größe vorher: {self.stats['size_before']:.1f} MB")
        print(f"   Größe nachher: {self.stats['size_after']:.1f} MB")
        print(f"   Eingespart: {self.stats['size_before'] - self.stats['size_after']:.1f} MB")
        print(f"\n   Posts vorher: {self.stats['total_posts']}")
        print(f"   Posts nachher: {len(posts)}")
        print(f"   Posts entfernt: {self.stats['posts_removed']}")
        print(f"\n   Mit Bildern: {self.stats['with_images']}")
        print(f"   Ohne Bilder: {self.stats['without_images']}")
        
        if self.stats['size_after'] > 500:
            print(f"\n⚠️ WARNUNG: Immer noch über 500 MB!")
            print(f"   Weitere Reduzierung nötig!")
        else:
            print(f"\n✅ Größe OK für GitHub (<500 MB)")

def main():
    print("🚀 Starte Cleanup für data_all...")
    cleaner = DataAllCleaner()
    cleaner.run_cleanup()

if __name__ == "__main__":
    main()