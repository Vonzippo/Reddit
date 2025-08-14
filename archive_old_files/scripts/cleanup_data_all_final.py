#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Bereinigt data_all von allen unnötigen Dateien
Behält nur: post_data.json und Bilder
"""

import os
from pathlib import Path
import shutil

def cleanup_data_all():
    """Entfernt alle unnötigen Dateien aus data_all"""
    
    data_all_dir = Path("/Users/patrick/Desktop/Reddit/data_all")
    posts_dir = data_all_dir / "Posts"
    
    print("🧹 BEREINIGE DATA_ALL")
    print("="*60)
    
    # Dateien die behalten werden sollen
    keep_files = {
        'post_data.json',  # Post-Metadaten
        'image.jpg', 'image.jpeg', 'image.png', 'image.gif', 'image.webp'  # Bilder
    }
    
    # Dateien die gelöscht werden sollen
    delete_patterns = {
        'info.txt',  # Redundant, Info ist in JSON
        'repost_guide.txt',  # Nicht benötigt
        'post_content.txt',  # Redundant
        '.DS_Store',  # Mac System-Dateien
        'Thumbs.db',  # Windows System-Dateien
    }
    
    stats = {
        'folders_processed': 0,
        'files_deleted': 0,
        'files_kept': 0,
        'space_freed_mb': 0
    }
    
    # Lösche unnötige Dateien im Hauptordner
    for file in data_all_dir.iterdir():
        if file.is_file():
            # Behalte nur wichtige JSON-Dateien
            if file.name not in ['combined_stats.json', 'safe_posts_for_upload.json', 'safe_october_posts.json']:
                if file.suffix in ['.txt', '.log', '.jsonl']:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    stats['space_freed_mb'] += size_mb
                    file.unlink()
                    stats['files_deleted'] += 1
                    print(f"   🗑️ Gelöscht: {file.name} ({size_mb:.1f} MB)")
    
    # Bereinige Posts-Ordner
    for post_dir in posts_dir.iterdir():
        if not post_dir.is_dir():
            continue
        
        stats['folders_processed'] += 1
        
        for file in post_dir.iterdir():
            if file.is_file():
                # Prüfe ob Datei behalten werden soll
                should_keep = False
                
                # Behalte post_data.json
                if file.name == 'post_data.json':
                    should_keep = True
                
                # Behalte Bilder
                if file.name.startswith('image.') and file.suffix in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    should_keep = True
                
                if should_keep:
                    stats['files_kept'] += 1
                else:
                    # Lösche unnötige Datei
                    size_mb = file.stat().st_size / (1024 * 1024)
                    stats['space_freed_mb'] += size_mb
                    file.unlink()
                    stats['files_deleted'] += 1
                    
                    if stats['files_deleted'] <= 20:  # Zeige nur erste 20
                        print(f"   🗑️ {post_dir.name}/{file.name}")
    
    # Berechne neue Größe
    total_size = 0
    for file in posts_dir.rglob('*'):
        if file.is_file():
            total_size += file.stat().st_size
    
    new_size_mb = total_size / (1024 * 1024)
    
    print("\n" + "="*60)
    print("✅ BEREINIGUNG ABGESCHLOSSEN!")
    print("="*60)
    print(f"📊 STATISTIKEN:")
    print(f"   Ordner verarbeitet: {stats['folders_processed']}")
    print(f"   Dateien gelöscht: {stats['files_deleted']}")
    print(f"   Dateien behalten: {stats['files_kept']}")
    print(f"   Speicher freigegeben: {stats['space_freed_mb']:.1f} MB")
    print(f"\n💾 NEUE GRÖSSE: {new_size_mb:.1f} MB")
    
    if new_size_mb < 500:
        print("   ✅ Perfekt für GitHub!")
    else:
        print("   ⚠️ Immer noch zu groß für GitHub")
        print("   ℹ️ Weitere Reduzierung nötig")

def main():
    print("🚀 DATA_ALL FINAL CLEANUP")
    print("="*60)
    print("Entfernt alle unnötigen Dateien:")
    print("- info.txt")
    print("- repost_guide.txt") 
    print("- post_content.txt")
    print("- Logs und temporäre Dateien")
    print("\nBehält nur:")
    print("- post_data.json")
    print("- Bilder (image.*)")
    print()
    
    cleanup_data_all()

if __name__ == "__main__":
    main()