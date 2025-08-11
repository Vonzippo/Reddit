#!/usr/bin/env python3
"""
Arctic Shift Torrent Downloader mit automatischer Filterung
Downloads 2024 Reddit Kommentare und filtert sie für deine Subreddits
"""

import os
import subprocess
from pathlib import Path

# Arctic Shift Torrent URLs für 2024
TORRENT_URLS = {
    "2024-01": "https://academictorrents.com/download/ac88546145ca3227e2b90e51ab477c4527dd8b90.torrent",
    "2024-02": "https://academictorrents.com/download/5969ae3e21bb481fea63bf649ec933c222c1f824.torrent",
    "2024-03": "https://academictorrents.com/download/deef710de36929e0aa77200fddda73c86142372c.torrent",
    "2024-04": "https://academictorrents.com/download/ad4617a3e9c1f52405197fc088b28a8018e12a7a.torrent",
    "2024-05": "https://academictorrents.com/download/4f60634d96d35158842cd58b495dc3b444d78b0d.torrent",
    "2024-06": "https://academictorrents.com/download/dcdecc93ca9a9d758c045345112771cef5b4989a.torrent",
    "2024-07": "https://academictorrents.com/download/6e5300446bd9b328d0b812cdb3022891e086d9ec.torrent",
    "2024-08": "https://academictorrents.com/download/8c2d4b00ce8ff9d45e335bed106fe9046c60adb0.torrent",
    "2024-09": "https://academictorrents.com/download/43a6e113d6ecacf38e58ecc6caa28d68892dd8af.torrent",
    "2024-10": "https://academictorrents.com/download/507dfcda29de9936dd77ed4f34c6442dc675c98f.torrent",
    "2024-11": "https://academictorrents.com/download/a1b490117808d9541ab9e3e67a3447e2f4f48f01.torrent",
    "2024-12": "https://academictorrents.com/download/eb2017da9f63a49460dde21a4ebe3b7c517f3ad9.torrent"
}

def check_tools():
    """Prüfe ob benötigte Tools installiert sind"""
    print("🔍 Prüfe benötigte Tools...")
    
    tools = {
        'aria2c': 'brew install aria2',
        'zstd': 'brew install zstd',
        'curl': 'Bereits installiert'
    }
    
    all_good = True
    for tool, install_cmd in tools.items():
        result = subprocess.run(['which', tool], capture_output=True)
        if result.returncode == 0:
            print(f"  ✓ {tool}")
        else:
            print(f"  ❌ {tool} - Installiere mit: {install_cmd}")
            all_good = False
    
    return all_good

def download_torrent_file(month, url):
    """Lade .torrent Datei herunter"""
    torrent_file = f"RC_{month}.torrent"
    
    print(f"📥 Lade Torrent-Datei für {month}...")
    cmd = f"curl -L -o {torrent_file} '{url}'"
    subprocess.run(cmd, shell=True)
    
    if Path(torrent_file).exists():
        print(f"  ✓ {torrent_file} heruntergeladen")
        return torrent_file
    else:
        print(f"  ❌ Fehler beim Download")
        return None

def download_and_filter_with_aria2(month, torrent_file):
    """Download mit aria2c und direkte Filterung"""
    
    output_dir = Path("pushshift_dumps/2024_filtered")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Lade target subreddits
    with open("target_subreddits.txt", "r") as f:
        target_subs = [line.strip().lower() for line in f if line.strip()]
    
    print(f"\n🚀 Starte Download und Filterung für {month}...")
    print(f"  Ziel-Subreddits: {len(target_subs)}")
    
    # Erstelle Filter-Skript
    filter_script = f"""#!/bin/bash
set -e

# Download mit aria2c
echo "📡 Starte Torrent-Download..."
aria2c --seed-time=0 \\
       --max-connection-per-server=16 \\
       --split=16 \\
       --enable-dht=true \\
       --file-allocation=none \\
       --console-log-level=error \\
       --summary-interval=30 \\
       --download-result=hide \\
       {torrent_file}

# Finde heruntergeladene Datei
ZST_FILE=$(find . -name "RC_{month}*.zst" -type f | head -1)

if [ -z "$ZST_FILE" ]; then
    echo "❌ Keine .zst Datei gefunden"
    exit 1
fi

echo "📊 Filtere Kommentare..."
echo "  Datei: $ZST_FILE"

# Filtere mit Python während der Dekompression
zstd -d -c "$ZST_FILE" | python3 -c "
import sys
import json

target_subs = {target_subs}
total = 0
filtered = 0

output_file = open('{output_dir}/RC_{month}_filtered.jsonl', 'w')

for line in sys.stdin:
    total += 1
    try:
        comment = json.loads(line.strip())
        subreddit = comment.get('subreddit', '').lower()
        
        if subreddit in target_subs:
            output_file.write(line)
            filtered += 1
    except:
        pass
    
    if total % 100000 == 0:
        print(f'  Verarbeitet: {{total:,}} | Gefiltert: {{filtered:,}}', end='\\r')

output_file.close()
print(f'\\n✓ Fertig: {{total:,}} total, {{filtered:,}} gefiltert')
"

# Lösche Original .zst Datei um Platz zu sparen
echo "🗑️ Lösche Original-Datei..."
rm -f "$ZST_FILE"

echo "✅ {month} erfolgreich verarbeitet!"
"""
    
    script_path = Path(f"filter_{month}.sh")
    with open(script_path, 'w') as f:
        f.write(filter_script)
    
    os.chmod(script_path, 0o755)
    
    # Führe Skript aus
    subprocess.run(['bash', str(script_path)])
    
    # Aufräumen
    script_path.unlink()
    Path(torrent_file).unlink(missing_ok=True)

def main():
    print("=" * 60)
    print("🎯 Arctic Shift 2024 Torrent Downloader & Filter")
    print("=" * 60)
    
    # Prüfe Tools
    if not check_tools():
        print("\n⚠️ Bitte installiere fehlende Tools zuerst")
        return
    
    # Zeige verfügbare Monate
    print("\n📅 Verfügbare 2024 Monate:")
    months = sorted(TORRENT_URLS.keys(), reverse=True)
    for i, month in enumerate(months, 1):
        print(f"  {i:2d}. {month}")
    
    print("\n❓ Welche Monate möchtest du herunterladen?")
    print("  1 = Neuester Monat")
    print("  2 = Letzte 3 Monate")  
    print("  3 = Bestimmte Monate auswählen")
    print("  4 = Alle 2024 Monate")
    
    choice = input("\n  Deine Wahl (1-4): ").strip()
    
    if choice == "1":
        selected = [months[0]]
    elif choice == "2":
        selected = months[:3]
    elif choice == "3":
        indices = input("  Gib Nummern ein (z.B. 1,3,5): ").strip()
        try:
            idx_list = [int(x.strip())-1 for x in indices.split(',')]
            selected = [months[i] for i in idx_list if 0 <= i < len(months)]
        except:
            print("❌ Ungültige Eingabe")
            return
    elif choice == "4":
        selected = months
    else:
        print("❌ Ungültige Wahl")
        return
    
    print(f"\n📥 Werde herunterladen: {', '.join(selected)}")
    
    # Schätze Größe
    est_size_gb = len(selected) * 0.15  # ~150MB pro Monat nach Filterung
    print(f"💾 Geschätzte finale Größe: ~{est_size_gb:.2f} GB")
    print(f"⚠️  Download-Größe: ~{len(selected) * 15} GB (wird während Filterung gelöscht)")
    
    confirm = input("\n❓ Fortfahren? (j/n): ")
    if confirm.lower() != 'j':
        print("Abgebrochen.")
        return
    
    # Verarbeite jeden Monat
    for month in selected:
        print(f"\n{'='*50}")
        print(f"📅 Verarbeite {month}")
        print('='*50)
        
        # Lade Torrent-Datei
        torrent_file = download_torrent_file(month, TORRENT_URLS[month])
        
        if torrent_file:
            # Download und Filter
            download_and_filter_with_aria2(month, torrent_file)
    
    print("\n" + "=" * 60)
    print("✅ Alle Downloads abgeschlossen!")
    print(f"📁 Gefilterte Daten in: pushshift_dumps/2024_filtered/")

if __name__ == "__main__":
    main()