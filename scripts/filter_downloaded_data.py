#!/usr/bin/env python3
"""
Filtert heruntergeladene .zst Dateien für die gewünschten Subreddits
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

def check_zstd():
    """Prüfe ob zstd installiert ist"""
    result = subprocess.run(['which', 'zstd'], capture_output=True)
    if result.returncode != 0:
        print("❌ zstd nicht gefunden. Installiere mit: brew install zstd")
        return False
    return True

def find_zst_files():
    """Finde alle .zst Dateien im pushshift_dumps Ordner"""
    dumps_dir = Path("pushshift_dumps")
    zst_files = list(dumps_dir.glob("*.zst"))
    
    if not zst_files:
        # Suche auch in Unterordnern
        zst_files = list(dumps_dir.rglob("*.zst"))
    
    return sorted(zst_files)

def filter_file(zst_file, target_subreddits):
    """Filtert eine einzelne .zst Datei"""
    
    output_dir = Path("pushshift_dumps/2024_filtered")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Output Dateiname
    output_file = output_dir / f"{zst_file.stem}_filtered.jsonl"
    
    print(f"\n📊 Verarbeite: {zst_file.name}")
    print(f"  Größe: {zst_file.stat().st_size / (1024**3):.2f} GB")
    print(f"  Output: {output_file.name}")
    
    # Erstelle Filter-Kommando
    filter_cmd = f"""
zstd -d -c "{zst_file}" | python3 -c "
import sys
import json

target_subs = {list(target_subreddits)}
total = 0
filtered = 0

with open('{output_file}', 'w') as out:
    for line in sys.stdin:
        total += 1
        try:
            comment = json.loads(line.strip())
            subreddit = comment.get('subreddit', '').lower()
            
            if subreddit in target_subs:
                out.write(line)
                filtered += 1
        except:
            pass
        
        if total % 100000 == 0:
            print(f'  Verarbeitet: {{total:,}} | Gefiltert: {{filtered:,}}', end='\\\\r', file=sys.stderr)

print(f'\\\\n✓ Fertig: {{total:,}} total, {{filtered:,}} gefiltert', file=sys.stderr)
print(f'{{filtered}}')
"
"""
    
    # Führe Filterung aus
    result = subprocess.run(filter_cmd, shell=True, capture_output=True, text=True)
    
    try:
        filtered_count = int(result.stdout.strip())
    except:
        filtered_count = 0
    
    # Prüfe Ausgabedatei
    if output_file.exists():
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"✓ Gespeichert: {filtered_count:,} Kommentare ({size_mb:.1f} MB)")
        return filtered_count, size_mb
    else:
        print("❌ Fehler beim Filtern")
        return 0, 0

def main():
    print("=" * 60)
    print("🔍 Reddit Daten Filter")
    print("=" * 60)
    
    # Prüfe zstd
    if not check_zstd():
        return
    
    # Lade target subreddits
    try:
        with open("target_subreddits.txt", "r") as f:
            target_subs = [line.strip().lower() for line in f if line.strip()]
        print(f"\n📋 {len(target_subs)} Ziel-Subreddits geladen:")
        print(f"  {', '.join(target_subs[:5])}...")
    except FileNotFoundError:
        print("❌ target_subreddits.txt nicht gefunden!")
        return
    
    # Finde .zst Dateien
    print("\n🔍 Suche nach .zst Dateien...")
    zst_files = find_zst_files()
    
    if not zst_files:
        print("❌ Keine .zst Dateien gefunden in pushshift_dumps/")
        print("\n💡 Tipp: Lade zuerst Daten herunter mit:")
        print("   bash download_latest.sh")
        return
    
    print(f"\n📦 Gefundene Dateien:")
    for i, f in enumerate(zst_files, 1):
        size_gb = f.stat().st_size / (1024**3)
        print(f"  {i}. {f.name} ({size_gb:.2f} GB)")
    
    # Frage welche Dateien
    if len(zst_files) == 1:
        selected = zst_files
        print(f"\n➡️ Verarbeite: {selected[0].name}")
    else:
        print("\n❓ Welche Dateien filtern?")
        print("  a = Alle")
        print("  1,2,3 = Bestimmte Nummern")
        
        choice = input("  Deine Wahl: ").strip().lower()
        
        if choice == 'a':
            selected = zst_files
        else:
            try:
                indices = [int(x.strip())-1 for x in choice.split(',')]
                selected = [zst_files[i] for i in indices if 0 <= i < len(zst_files)]
            except:
                print("❌ Ungültige Eingabe")
                return
    
    # Bestätigung
    total_size_gb = sum(f.stat().st_size for f in selected) / (1024**3)
    est_output_gb = total_size_gb * 0.001  # ~0.1% der Originalgröße
    
    print(f"\n📊 Zusammenfassung:")
    print(f"  Dateien: {len(selected)}")
    print(f"  Input-Größe: {total_size_gb:.2f} GB")
    print(f"  Geschätzte Output-Größe: {est_output_gb:.2f} GB")
    
    confirm = input("\n❓ Starten? (j/n): ")
    if confirm.lower() != 'j':
        print("Abgebrochen.")
        return
    
    # Verarbeite Dateien
    start_time = datetime.now()
    total_comments = 0
    total_size_mb = 0
    
    for zst_file in selected:
        count, size_mb = filter_file(zst_file, target_subs)
        total_comments += count
        total_size_mb += size_mb
    
    # Zusammenfassung
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("✅ Filterung abgeschlossen!")
    print(f"  Kommentare gefiltert: {total_comments:,}")
    print(f"  Gesamtgröße: {total_size_mb:.1f} MB")
    print(f"  Dauer: {duration:.1f} Sekunden")
    print(f"  Output: pushshift_dumps/2024_filtered/")
    
    # Optionale Bereinigung
    print("\n❓ Original .zst Dateien löschen um Platz zu sparen? (j/n)")
    cleanup = input("  Deine Wahl: ").strip().lower()
    if cleanup == 'j':
        for f in selected:
            f.unlink()
            print(f"  ✓ Gelöscht: {f.name}")

if __name__ == "__main__":
    main()