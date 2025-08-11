#!/usr/bin/env python3
"""
Schneller Multi-Thread Filter für Reddit .zst Dateien
Filtert Comments und Posts nach target_subreddits.txt
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
import threading
import time

class FastRedditFilter:
    def __init__(self):
        self.total_processed = 0
        self.total_filtered = 0
        self.lock = threading.Lock()
        self.start_time = None
        
        # Lade Ziel-Subreddits
        self.load_target_subreddits()
        
    def load_target_subreddits(self):
        """Lädt die Ziel-Subreddits"""
        try:
            with open("target_subreddits.txt", "r") as f:
                self.target_subs = set(line.strip().lower() for line in f if line.strip())
            print(f"📋 {len(self.target_subs)} Subreddits geladen")
        except FileNotFoundError:
            print("❌ target_subreddits.txt nicht gefunden!")
            sys.exit(1)
    
    def process_chunk(self, chunk_lines):
        """Verarbeitet einen Chunk von Zeilen"""
        local_processed = 0
        local_filtered = 0
        filtered_lines = []
        
        for line in chunk_lines:
            if not line.strip():
                continue
            
            local_processed += 1
            
            try:
                data = json.loads(line)
                subreddit = data.get('subreddit', '').lower()
                
                if subreddit in self.target_subs:
                    filtered_lines.append(line)
                    local_filtered += 1
            except:
                continue
        
        # Update globale Stats
        with self.lock:
            self.total_processed += local_processed
            self.total_filtered += local_filtered
            
            # Progress Update
            if self.total_processed % 50000 == 0:
                elapsed = time.time() - self.start_time
                rate = self.total_processed / elapsed if elapsed > 0 else 0
                print(f"\r⚡ Verarbeitet: {self.total_processed:,} | "
                      f"Gefiltert: {self.total_filtered:,} | "
                      f"Rate: {rate:,.0f}/s | "
                      f"Zeit: {elapsed:.0f}s", end='', flush=True)
        
        return filtered_lines
    
    def filter_file_parallel(self, zst_file, output_file, num_workers=None):
        """Filtert eine .zst Datei mit mehreren Threads"""
        
        if num_workers is None:
            num_workers = min(cpu_count() * 2, 16)  # Max 16 workers
        
        print(f"\n📊 Verarbeite: {zst_file.name}")
        print(f"  Größe: {zst_file.stat().st_size / (1024**3):.2f} GB")
        print(f"  Workers: {num_workers}")
        print(f"  Output: {output_file.name}")
        
        self.total_processed = 0
        self.total_filtered = 0
        self.start_time = time.time()
        
        # Chunk size für Batching
        chunk_size = 5000
        
        # Temporäre Datei für dekomprimierte Daten
        temp_file = Path(f"/tmp/{zst_file.stem}_temp.jsonl")
        
        print("  📦 Dekomprimiere...")
        decompress_cmd = f"zstd -d -c '{zst_file}' > '{temp_file}'"
        subprocess.run(decompress_cmd, shell=True, check=True)
        
        print("  🔍 Filtere mit Multithreading...")
        
        # Verarbeite mit Thread Pool
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            current_chunk = []
            
            # Lese dekomprimierte Datei
            with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    current_chunk.append(line.rstrip())
                    
                    if len(current_chunk) >= chunk_size:
                        # Submit chunk to worker
                        future = executor.submit(self.process_chunk, current_chunk)
                        futures.append(future)
                        current_chunk = []
                
                # Letzter Chunk
                if current_chunk:
                    future = executor.submit(self.process_chunk, current_chunk)
                    futures.append(future)
            
            # Schreibe gefilterte Ergebnisse
            with open(output_file, 'w', encoding='utf-8') as out:
                for future in as_completed(futures):
                    filtered_lines = future.result()
                    for line in filtered_lines:
                        out.write(line + '\n')
        
        # Cleanup temp file
        if temp_file.exists():
            temp_file.unlink()
        
        # Finale Stats
        elapsed = time.time() - self.start_time
        print(f"\n  ✅ Fertig in {elapsed:.1f}s")
        print(f"     Verarbeitet: {self.total_processed:,}")
        print(f"     Gefiltert: {self.total_filtered:,} ({self.total_filtered/self.total_processed*100:.2f}%)")
        print(f"     Rate: {self.total_processed/elapsed:,.0f} items/s")
        
        # Dateigröße
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"     Output-Größe: {size_mb:.1f} MB")
        
        return self.total_filtered

def filter_posts_and_comments():
    """Hauptfunktion zum Filtern von Posts und Comments"""
    
    print("=" * 60)
    print("⚡ FAST Reddit Filter (Multithreading)")
    print("=" * 60)
    
    # Check zstd
    result = subprocess.run(['which', 'zstd'], capture_output=True)
    if result.returncode != 0:
        print("❌ zstd nicht gefunden!")
        print("   Installiere mit: brew install zstd")
        return
    
    # Initialisiere Filter
    filter = FastRedditFilter()
    
    # Finde .zst Dateien
    dumps_dir = Path("pushshift_dumps")
    
    # Suche nach Comments (RC_*.zst) und Posts (RS_*.zst)
    comment_files = list(dumps_dir.rglob("RC_*.zst"))
    post_files = list(dumps_dir.rglob("RS_*.zst"))
    
    all_files = comment_files + post_files
    
    if not all_files:
        print("❌ Keine .zst Dateien gefunden!")
        print("\n💡 Lade zuerst Daten herunter mit:")
        print("   bash download_latest.sh")
        return
    
    print(f"\n📦 Gefundene Dateien:")
    print(f"  Comments: {len(comment_files)} Dateien")
    print(f"  Posts: {len(post_files)} Dateien")
    
    for i, f in enumerate(all_files, 1):
        size_gb = f.stat().st_size / (1024**3)
        file_type = "Comments" if f.name.startswith("RC_") else "Posts"
        print(f"  {i}. [{file_type}] {f.name} ({size_gb:.2f} GB)")
    
    # Wähle Dateien
    print("\n❓ Welche Dateien filtern?")
    print("  a = Alle")
    print("  c = Nur Comments (RC_*)")
    print("  p = Nur Posts (RS_*)")
    print("  1,2,3 = Bestimmte Nummern")
    
    choice = input("  Deine Wahl [a]: ").strip().lower() or 'a'
    
    if choice == 'a':
        selected = all_files
    elif choice == 'c':
        selected = comment_files
    elif choice == 'p':
        selected = post_files
    else:
        try:
            indices = [int(x.strip())-1 for x in choice.split(',')]
            selected = [all_files[i] for i in indices if 0 <= i < len(all_files)]
        except:
            print("❌ Ungültige Eingabe")
            return
    
    if not selected:
        print("❌ Keine Dateien ausgewählt")
        return
    
    # Worker-Anzahl
    num_cores = cpu_count()
    print(f"\n💻 CPU Cores: {num_cores}")
    print(f"  Empfohlen: {min(num_cores * 2, 16)} Workers")
    
    custom = input(f"  Worker-Anzahl [{min(num_cores * 2, 16)}]: ").strip()
    if custom.isdigit():
        num_workers = int(custom)
    else:
        num_workers = min(num_cores * 2, 16)
    
    # Zusammenfassung
    total_size_gb = sum(f.stat().st_size for f in selected) / (1024**3)
    
    print(f"\n📊 Zusammenfassung:")
    print(f"  Dateien: {len(selected)}")
    print(f"  Gesamtgröße: {total_size_gb:.2f} GB")
    print(f"  Workers: {num_workers}")
    print(f"  Geschätzte Zeit: {total_size_gb * 20:.0f}-{total_size_gb * 40:.0f} Sekunden")
    
    confirm = input("\n❓ Starten? (j/n) [j]: ").strip().lower()
    if confirm == 'n':
        print("Abgebrochen.")
        return
    
    # Verarbeite Dateien
    start_time = datetime.now()
    total_comments_filtered = 0
    total_posts_filtered = 0
    
    for zst_file in selected:
        # Bestimme Output-Verzeichnis
        if zst_file.name.startswith("RC_"):
            output_dir = Path("pushshift_dumps/2024_filtered")
        else:
            output_dir = Path("pushshift_dumps/2024_posts_filtered")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{zst_file.stem}_filtered.jsonl"
        
        # Filtere Datei
        count = filter.filter_file_parallel(zst_file, output_file, num_workers)
        
        if zst_file.name.startswith("RC_"):
            total_comments_filtered += count
        else:
            total_posts_filtered += count
    
    # Zusammenfassung
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("✅ FILTERUNG ABGESCHLOSSEN!")
    print(f"  Comments gefiltert: {total_comments_filtered:,}")
    print(f"  Posts gefiltert: {total_posts_filtered:,}")
    print(f"  Gesamtdauer: {duration:.1f} Sekunden ({duration/60:.1f} Minuten)")
    print(f"  Durchsatz: {total_size_gb / (duration/3600):.2f} GB/h")
    print("\n📁 Output-Verzeichnisse:")
    print("  Comments: pushshift_dumps/2024_filtered/")
    print("  Posts: pushshift_dumps/2024_posts_filtered/")
    
    # Optional: Cleanup
    print("\n❓ Original .zst Dateien löschen? (j/n) [n]: ")
    cleanup = input("  Deine Wahl: ").strip().lower()
    if cleanup == 'j':
        confirm = input("  ⚠️ WIRKLICH LÖSCHEN? (ja): ").strip().lower()
        if confirm == 'ja':
            for f in selected:
                f.unlink()
                print(f"  ✓ Gelöscht: {f.name}")
            print("  Originaldateien gelöscht.")

if __name__ == "__main__":
    filter_posts_and_comments()