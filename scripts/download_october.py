#!/usr/bin/env python3
"""
Download Oktober 2024 Reddit Daten
Lädt RC_2024-10 (Kommentare) und RS_2024-10 (Posts)
"""

import os
import sys
import requests
from pathlib import Path
import subprocess
import time

# Arctic Shift URLs für Oktober 2024
OCTOBER_URLS = {
    "comments": {
        "name": "RC_2024-10.zst",
        "url": "https://academictorrents.com/download/YOUR_HASH_HERE.torrent",
        "size_estimate": "~15-20 GB komprimiert"
    },
    "posts": {
        "name": "RS_2024-10.zst", 
        "url": "https://academictorrents.com/download/YOUR_HASH_HERE.torrent",
        "size_estimate": "~2-3 GB komprimiert"
    }
}

def check_dependencies():
    """Prüfe ob notwendige Tools installiert sind"""
    tools = ["aria2c", "zstd"]
    missing = []
    
    for tool in tools:
        result = subprocess.run(["which", tool], capture_output=True, text=True)
        if result.returncode != 0:
            missing.append(tool)
    
    if missing:
        print(f"❌ Fehlende Tools: {', '.join(missing)}")
        print("Installiere mit:")
        for tool in missing:
            print(f"  brew install {tool.replace('aria2c', 'aria2')}")
        return False
    return True

def create_directories():
    """Erstelle notwendige Verzeichnisse"""
    base_dir = Path("pushshift_dumps/reddit/october")
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def download_torrent_file(url, filename):
    """Lade Torrent-Datei herunter"""
    print(f"📥 Lade Torrent: {filename}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ Torrent gespeichert: {filename}")
        return True
    except Exception as e:
        print(f"❌ Fehler beim Download: {e}")
        return False

def start_torrent_download(torrent_file, output_dir):
    """Starte Torrent-Download mit aria2c"""
    cmd = [
        "aria2c",
        "--seed-time=0",
        "--max-connection-per-server=16",
        "--split=16",
        "--enable-dht=true",
        "--file-allocation=none",
        "--console-log-level=notice",
        "--summary-interval=30",
        f"--dir={output_dir}",
        torrent_file
    ]
    
    print(f"🚀 Starte Download: {torrent_file}")
    process = subprocess.Popen(cmd)
    return process

def main():
    print("="*60)
    print("🎯 Oktober 2024 Reddit Daten Download")
    print("="*60)
    
    # Prüfe Dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Erstelle Verzeichnisse
    output_dir = create_directories()
    print(f"📁 Output-Verzeichnis: {output_dir}")
    
    print("\n⚠️  WICHTIG: Die Torrent-URLs müssen noch aktualisiert werden!")
    print("Besuche: https://academictorrents.com/browse.php?search=reddit+2024-10")
    print("Oder: https://the-eye.eu/redarcs/")
    
    # Alternative: Direkter Download von the-eye.eu
    print("\n📡 Alternative Quellen:")
    print("1. The Eye Archive: https://the-eye.eu/redarcs/")
    print("2. Arctic Shift: https://arctic-shift.photon-reddit.com/")
    print("3. Pushshift Archive: https://academictorrents.com/")
    
    print("\n📊 Geschätzte Dateigrößen:")
    print("  - RC_2024-10.zst (Kommentare): ~15-20 GB")
    print("  - RS_2024-10.zst (Posts): ~2-3 GB")
    
    print("\n🎯 Nach dem Download:")
    print("1. Entpacke mit: zstd -d RC_2024-10.zst")
    print("2. Filtere mit: python scripts/filter_october.py")
    print("3. Extrahiere Top-Content mit: python scripts/extract_october_content.py")

if __name__ == "__main__":
    main()