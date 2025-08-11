#!/usr/bin/env python3
"""
Arctic Shift Reddit Data Downloader with Filtering
Downloads and filters Reddit comments for specific subreddits
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

def check_dependencies():
    """Check if required tools are installed"""
    dependencies = {
        'aria2c': 'brew install aria2',
        'zstd': 'brew install zstd',
        'jq': 'brew install jq'
    }
    
    missing = []
    for cmd, install in dependencies.items():
        result = subprocess.run(['which', cmd], capture_output=True)
        if result.returncode != 0:
            missing.append((cmd, install))
    
    if missing:
        print("❌ Missing dependencies:")
        for cmd, install in missing:
            print(f"  - {cmd}: Install with '{install}'")
        return False
    return True

def get_arctic_shift_torrents():
    """Get torrent URLs for Arctic Shift data"""
    # These are example URLs - actual URLs from Arctic Shift GitHub
    torrents = {
        "2024-12": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-12.torrent",
        "2024-11": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-11.torrent",
        "2024-10": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-10.torrent",
        "2024-09": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-09.torrent",
        "2024-08": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-08.torrent",
        "2024-07": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-07.torrent",
        "2024-06": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-06.torrent",
        "2024-05": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-05.torrent",
        "2024-04": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-04.torrent",
        "2024-03": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-03.torrent",
        "2024-02": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-02.torrent",
        "2024-01": "https://github.com/ArthurHeitmann/arctic_shift/releases/download/v2/RC_2024-01.torrent"
    }
    return torrents

def download_and_filter(month, torrent_url, target_subreddits):
    """Download and filter a single month of data"""
    
    filename = f"RC_{month}.zst"
    output_dir = Path("pushshift_dumps/2024_filtered")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"RC_{month}_filtered.jsonl"
    temp_dir = Path("temp_download")
    temp_dir.mkdir(exist_ok=True)
    
    print(f"\n📥 Processing {month}...")
    print(f"  Output: {output_file}")
    
    # Create filter script
    filter_script = temp_dir / "filter.sh"
    
    # Create subreddit filter pattern
    subs_pattern = "|".join(target_subreddits)
    
    filter_content = f'''#!/bin/bash
# Filter Reddit comments for specific subreddits

echo "🔍 Filtering comments for target subreddits..."

# Download with aria2c and pipe directly to filtering
aria2c --allow-overwrite=true \\
       --max-connection-per-server=16 \\
       --min-split-size=1M \\
       --split=16 \\
       --enable-dht=true \\
       --seed-time=0 \\
       --follow-torrent=mem \\
       --console-log-level=error \\
       --summary-interval=10 \\
       -d {temp_dir} \\
       "{torrent_url}" 2>/dev/null | \\
while IFS= read -r line; do
    if [[ "$line" == *"Download complete"* ]]; then
        echo "✓ Download complete, starting filter..."
        
        # Stream decompress and filter
        zstd -d -c {temp_dir}/{filename} | \\
        jq -c --arg subs "({subs_pattern})" \\
           'select(.subreddit | test($subs; "i"))' > {output_file}
        
        # Clean up
        rm -f {temp_dir}/{filename}
        echo "✓ Filtering complete!"
    fi
done
'''
    
    with open(filter_script, 'w') as f:
        f.write(filter_content)
    
    os.chmod(filter_script, 0o755)
    
    # Run the filter script
    subprocess.run(['bash', str(filter_script)])
    
    # Count results
    if output_file.exists():
        with open(output_file, 'r') as f:
            count = sum(1 for _ in f)
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"✓ Saved {count:,} comments ({size_mb:.1f} MB)")
        return count, size_mb
    
    return 0, 0

def main():
    print("🚀 Arctic Shift Reddit Data Downloader")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n⚠️ Please install missing dependencies first")
        return
    
    # Load target subreddits
    try:
        with open("target_subreddits.txt", "r") as f:
            target_subreddits = [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ target_subreddits.txt not found!")
        return
    
    print(f"\n📋 Loaded {len(target_subreddits)} target subreddits")
    
    # Get available torrents
    torrents = get_arctic_shift_torrents()
    
    print("\n📅 Available months:")
    for i, month in enumerate(sorted(torrents.keys(), reverse=True), 1):
        print(f"  {i}. {month}")
    
    # Ask user which months to download
    print("\n❓ Which months do you want to download?")
    print("  Enter month numbers separated by commas (e.g., 1,2,3)")
    print("  Or 'all' for all months, or 'latest' for most recent")
    
    choice = input("  Your choice: ").strip()
    
    if choice.lower() == 'all':
        selected_months = list(torrents.keys())
    elif choice.lower() == 'latest':
        selected_months = [sorted(torrents.keys(), reverse=True)[0]]
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            month_list = sorted(torrents.keys(), reverse=True)
            selected_months = [month_list[i] for i in indices if 0 <= i < len(month_list)]
        except:
            print("❌ Invalid selection")
            return
    
    print(f"\n📥 Will download: {', '.join(selected_months)}")
    
    # Estimate size
    estimated_size_gb = len(selected_months) * 0.15  # ~150MB per month after filtering
    print(f"💾 Estimated final size: ~{estimated_size_gb:.2f} GB")
    
    confirm = input("\n❓ Continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return
    
    # Process each month
    total_comments = 0
    total_size_mb = 0
    
    for month in selected_months:
        count, size_mb = download_and_filter(month, torrents[month], target_subreddits)
        total_comments += count
        total_size_mb += size_mb
    
    # Summary
    print("\n" + "=" * 50)
    print("✅ Download Complete!")
    print(f"  Total comments: {total_comments:,}")
    print(f"  Total size: {total_size_mb:.1f} MB")
    print(f"  Data location: pushshift_dumps/2024_filtered/")

if __name__ == "__main__":
    main()