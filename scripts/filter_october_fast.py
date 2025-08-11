#!/usr/bin/env python3
"""
⚡ Schneller Multi-Thread Filter für Oktober 2024 Reddit Daten
Optimiert für 99 Subreddits aus target_subreddits.txt
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
import zstandard as zstd

class OctoberFilterMultithread:
    def __init__(self):
        self.total_processed = 0
        self.total_filtered = 0
        self.lock = threading.Lock()
        self.start_time = None
        self.progress_interval = 100000  # Update alle 100k Zeilen
        
        # Lade alle 99 Ziel-Subreddits
        self.load_target_subreddits()
        
    def load_target_subreddits(self):
        """Lädt die 99 Ziel-Subreddits"""
        try:
            with open("target_subreddits.txt", "r") as f:
                self.target_subs = set(line.strip().lower() for line in f 
                                     if line.strip() and not line.startswith("#"))
            print(f"📋 {len(self.target_subs)} Subreddits geladen aus target_subreddits.txt")
            
            # Zeige erste 5 als Beispiel
            sample = list(self.target_subs)[:5]
            print(f"   Beispiele: {', '.join(sample)}...")
            
        except FileNotFoundError:
            print("❌ target_subreddits.txt nicht gefunden!")
            sys.exit(1)
    
    def process_chunk(self, chunk_data):
        """Verarbeitet einen Chunk von Zeilen (Worker-Funktion)"""
        chunk_lines, chunk_id = chunk_data
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
                
                # Check ob Subreddit in unseren 99 Target-Subs ist
                if subreddit in self.target_subs:
                    filtered_lines.append(line)
                    local_filtered += 1
            except json.JSONDecodeError:
                continue
            except Exception:
                continue
        
        # Update globale Stats thread-safe
        with self.lock:
            self.total_processed += local_processed
            self.total_filtered += local_filtered
            
            # Progress Update
            if self.total_processed % self.progress_interval == 0:
                elapsed = time.time() - self.start_time
                rate = self.total_processed / elapsed if elapsed > 0 else 0
                percentage = (self.total_filtered / self.total_processed * 100) if self.total_processed > 0 else 0
                
                print(f"\r⚡ Verarbeitet: {self.total_processed:,} | "
                      f"Gefiltert: {self.total_filtered:,} ({percentage:.2f}%) | "
                      f"Rate: {rate:,.0f}/s | "
                      f"Zeit: {elapsed:.0f}s", end='', flush=True)
        
        return filtered_lines
    
    def filter_file_parallel(self, zst_file, output_file, num_workers=None):
        """Filtert eine .zst Datei mit mehreren Threads"""
        
        if num_workers is None:
            num_workers = min(cpu_count() * 2, 24)  # Max 24 workers für Oktober-Daten
        
        print(f"\n📊 Verarbeite: {zst_file.name}")
        print(f"  📁 Größe: {zst_file.stat().st_size / (1024**3):.2f} GB")
        print(f"  🔧 Workers: {num_workers}")
        print(f"  💾 Output: {output_file.name}")
        
        self.total_processed = 0
        self.total_filtered = 0
        self.start_time = time.time()
        
        # Chunk size optimiert für große Dateien
        chunk_size = 10000  # Größere Chunks für bessere Performance
        
        print("  🔍 Filtere mit Multithreading...")
        
        # Direkte Verarbeitung ohne temporäre Datei
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            chunk_id = 0
            
            # Verwende zstandard library für streaming
            with open(zst_file, 'rb') as fh:
                dctx = zstd.ZstdDecompressor()
                reader = dctx.stream_reader(fh)
                text_reader = reader.read1
                
                current_chunk = []
                buffer = b''
                
                while True:
                    # Lese in Chunks
                    chunk = reader.read1(65536)  # 64KB chunks
                    if not chunk:
                        break
                    
                    buffer += chunk
                    lines = buffer.split(b'\n')
                    
                    # Behalte letzten unvollständigen Teil
                    buffer = lines[-1]
                    
                    for line in lines[:-1]:
                        try:
                            line_str = line.decode('utf-8', errors='ignore')
                            if line_str.strip():
                                current_chunk.append(line_str)
                                
                                if len(current_chunk) >= chunk_size:
                                    # Submit chunk to worker
                                    chunk_id += 1
                                    future = executor.submit(self.process_chunk, 
                                                          (current_chunk.copy(), chunk_id))
                                    futures.append(future)
                                    current_chunk = []
                        except:
                            continue
                
                # Verarbeite restlichen Buffer
                if buffer:
                    try:
                        line_str = buffer.decode('utf-8', errors='ignore')
                        if line_str.strip():
                            current_chunk.append(line_str)
                    except:
                        pass
                
                # Letzter Chunk
                if current_chunk:
                    chunk_id += 1
                    future = executor.submit(self.process_chunk, 
                                          (current_chunk, chunk_id))
                    futures.append(future)
            
            print(f"\n  📝 Schreibe gefilterte Daten...")
            
            # Schreibe gefilterte Ergebnisse
            written = 0
            with open(output_file, 'w', encoding='utf-8') as out:
                for future in as_completed(futures):
                    try:
                        filtered_lines = future.result()
                        for line in filtered_lines:
                            out.write(line)
                            if not line.endswith('\n'):
                                out.write('\n')
                            written += 1
                            
                            if written % 10000 == 0:
                                print(f"\r  📝 Geschrieben: {written:,} Zeilen", end='', flush=True)
                    except Exception as e:
                        print(f"\n  ⚠️ Fehler in Worker: {e}")
        
        # Finale Stats
        elapsed = time.time() - self.start_time
        print(f"\n  ✅ Fertig in {elapsed:.1f}s ({elapsed/60:.1f} Minuten)")
        print(f"     Verarbeitet: {self.total_processed:,}")
        print(f"     Gefiltert: {self.total_filtered:,} ({self.total_filtered/self.total_processed*100:.2f}%)")
        print(f"     Rate: {self.total_processed/elapsed:,.0f} items/s")
        
        # Dateigröße
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            size_gb = size_mb / 1024
            if size_gb >= 1:
                print(f"     Output-Größe: {size_gb:.2f} GB")
            else:
                print(f"     Output-Größe: {size_mb:.1f} MB")
        
        return self.total_filtered

def main():
    """Hauptfunktion zum Filtern der Oktober-Daten"""
    
    print("=" * 70)
    print("⚡ OKTOBER 2024 FAST FILTER - Multithreading Edition")
    print("=" * 70)
    
    # Initialisiere Filter
    filter_engine = OctoberFilterMultithread()
    
    # Oktober-Dateien
    october_dir = Path("pushshift_dumps/reddit/october/reddit")
    
    # Finde Oktober-Dateien
    rc_file = october_dir / "comments" / "RC_2024-10.zst"
    rs_file = october_dir / "submissions" / "RS_2024-10.zst"
    
    files_to_process = []
    
    if rc_file.exists():
        files_to_process.append(("comments", rc_file))
        print(f"✅ Gefunden: {rc_file.name} ({rc_file.stat().st_size / (1024**3):.2f} GB)")
    else:
        print(f"❌ Nicht gefunden: {rc_file}")
    
    if rs_file.exists():
        files_to_process.append(("posts", rs_file))
        print(f"✅ Gefunden: {rs_file.name} ({rs_file.stat().st_size / (1024**3):.2f} GB)")
    else:
        print(f"❌ Nicht gefunden: {rs_file}")
    
    if not files_to_process:
        print("\n❌ Keine Oktober-Dateien gefunden!")
        print("   Lade erst mit: bash scripts/download_october.sh")
        return
    
    # Worker-Anzahl
    num_cores = cpu_count()
    recommended = min(num_cores * 2, 24)
    print(f"\n💻 System:")
    print(f"  CPU Cores: {num_cores}")
    print(f"  Empfohlene Workers: {recommended}")
    
    custom = input(f"  Worker-Anzahl [{recommended}]: ").strip()
    if custom.isdigit():
        num_workers = int(custom)
    else:
        num_workers = recommended
    
    # Zusammenfassung
    total_size_gb = sum(f[1].stat().st_size for f in files_to_process) / (1024**3)
    
    print(f"\n📊 Zusammenfassung:")
    print(f"  🎯 Target Subreddits: {len(filter_engine.target_subs)}")
    print(f"  📁 Dateien: {len(files_to_process)}")
    print(f"  💾 Gesamtgröße: {total_size_gb:.2f} GB")
    print(f"  🔧 Workers: {num_workers}")
    print(f"  ⏱️  Geschätzte Zeit: {total_size_gb * 15:.0f}-{total_size_gb * 30:.0f} Sekunden")
    
    confirm = input("\n▶️  Starten? (j/n) [j]: ").strip().lower()
    if confirm == 'n':
        print("Abgebrochen.")
        return
    
    # Verarbeite Dateien
    start_time = datetime.now()
    
    # Output-Verzeichnis für Oktober
    output_base = Path("pushshift_dumps/2024_october_filtered")
    output_base.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for file_type, zst_file in files_to_process:
        if file_type == "comments":
            output_file = output_base / "RC_2024-10_filtered.jsonl"
        else:
            output_file = output_base / "RS_2024-10_filtered.jsonl"
        
        # Filtere Datei
        count = filter_engine.filter_file_parallel(zst_file, output_file, num_workers)
        results[file_type] = count
    
    # Zusammenfassung
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 70)
    print("🎉 OKTOBER-FILTERUNG ABGESCHLOSSEN!")
    print("=" * 70)
    
    if "comments" in results:
        print(f"  💬 Comments gefiltert: {results['comments']:,}")
    if "posts" in results:
        print(f"  📝 Posts gefiltert: {results['posts']:,}")
    
    total_filtered = sum(results.values())
    print(f"  📊 Gesamt gefiltert: {total_filtered:,}")
    print(f"  ⏱️  Gesamtdauer: {duration:.1f} Sekunden ({duration/60:.1f} Minuten)")
    
    if duration > 0:
        print(f"  🚀 Durchsatz: {total_size_gb / (duration/3600):.2f} GB/h")
        print(f"  ⚡ Items/s: {total_filtered/duration:,.0f}")
    
    print(f"\n📁 Output-Verzeichnis: {output_base}/")
    print("  - RC_2024-10_filtered.jsonl (Kommentare)")
    print("  - RS_2024-10_filtered.jsonl (Posts)")
    
    print("\n✨ Nächster Schritt:")
    print("   python3 scripts/extract_october_top_content.py")

if __name__ == "__main__":
    # Check dependencies
    try:
        import zstandard
    except ImportError:
        print("❌ zstandard library nicht installiert!")
        print("   Installiere mit: pip install zstandard")
        sys.exit(1)
    
    main()