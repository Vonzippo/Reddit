#!/usr/bin/env python3
"""
Optimized Reddit Data Downloader with Live Filtering
Downloads and filters data in streaming mode to save disk space
"""

import os
import sys
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime
import gzip
import io

class RedditDataDownloader:
    def __init__(self):
        self.output_dir = Path("pushshift_dumps/2024_filtered")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.target_subreddits = self.load_target_subreddits()
        self.stats = {"total_comments": 0, "filtered_comments": 0, "total_size_mb": 0}
    
    def load_target_subreddits(self):
        """Load target subreddits from file"""
        try:
            with open("target_subreddits.txt", "r") as f:
                subs = [line.strip().lower() for line in f if line.strip()]
                print(f"✓ Loaded {len(subs)} target subreddits")
                return set(subs)
        except FileNotFoundError:
            print("❌ target_subreddits.txt not found!")
            sys.exit(1)
    
    def check_tools(self):
        """Check if required tools are installed"""
        print("\n🔍 Checking required tools...")
        
        tools = {
            'curl': 'brew install curl',
            'zstd': 'brew install zstd',
            'python3': 'Already installed'
        }
        
        all_good = True
        for tool, install_cmd in tools.items():
            result = subprocess.run(['which', tool], capture_output=True)
            if result.returncode == 0:
                print(f"  ✓ {tool}")
            else:
                print(f"  ❌ {tool} - Install with: {install_cmd}")
                all_good = False
        
        return all_good
    
    def get_data_urls(self):
        """Get direct download URLs for Reddit data"""
        # Check multiple sources
        sources = {
            "Arctic Shift (Direct)": [
                ("2024-12", "https://the-eye.eu/redarcs/files/RC_2024-12.zst"),
                ("2024-11", "https://the-eye.eu/redarcs/files/RC_2024-11.zst"),
                ("2024-10", "https://the-eye.eu/redarcs/files/RC_2024-10.zst"),
            ],
            "Pushshift Archives": [
                ("2024-12", "https://files.pushshift.io/reddit/comments/RC_2024-12.zst"),
                ("2024-11", "https://files.pushshift.io/reddit/comments/RC_2024-11.zst"),
                ("2024-10", "https://files.pushshift.io/reddit/comments/RC_2024-10.zst"),
            ]
        }
        
        print("\n🔍 Checking data availability...")
        available = []
        
        for source_name, urls in sources.items():
            print(f"\n  Checking {source_name}...")
            for month, url in urls[:1]:  # Check only first to save time
                try:
                    response = requests.head(url, timeout=5, allow_redirects=True)
                    if response.status_code == 200:
                        size_gb = int(response.headers.get('Content-Length', 0)) / (1024**3)
                        print(f"    ✓ {source_name} is available")
                        available.extend(urls)
                        break
                except:
                    pass
            else:
                print(f"    ✗ {source_name} not accessible")
        
        return available
    
    def download_and_filter_stream(self, month, url):
        """Download and filter in streaming mode"""
        output_file = self.output_dir / f"RC_{month}_filtered.jsonl"
        
        print(f"\n📥 Downloading and filtering {month}...")
        print(f"  Source: {url}")
        print(f"  Output: {output_file}")
        
        # Create filter script that processes in streaming mode
        filter_script = f"""
#!/bin/bash
set -e

echo "Starting streaming download and filter..."

# Download and decompress in streaming mode, filter with Python
curl -L --progress-bar "{url}" | \\
zstd -d -c | \\
python3 -c "
import sys
import json

target_subs = {list(self.target_subreddits)}
total = 0
filtered = 0

for line in sys.stdin:
    total += 1
    try:
        comment = json.loads(line.strip())
        if comment.get('subreddit', '').lower() in target_subs:
            print(line.strip())
            filtered += 1
    except:
        pass
    
    if total % 100000 == 0:
        print(f'Processed {{total:,}} comments, kept {{filtered:,}}', file=sys.stderr)

print(f'Final: {{total:,}} total, {{filtered:,}} kept', file=sys.stderr)
" > {output_file}
"""
        
        # Save and run script
        script_path = Path("temp_filter.sh")
        with open(script_path, 'w') as f:
            f.write(filter_script)
        
        os.chmod(script_path, 0o755)
        
        # Run the streaming filter
        result = subprocess.run(['bash', str(script_path)], capture_output=False)
        
        # Clean up
        script_path.unlink()
        
        # Get stats
        if output_file.exists():
            with open(output_file, 'r') as f:
                count = sum(1 for _ in f)
            size_mb = output_file.stat().st_size / (1024 * 1024)
            
            self.stats["filtered_comments"] += count
            self.stats["total_size_mb"] += size_mb
            
            print(f"✓ Saved {count:,} comments ({size_mb:.1f} MB)")
            return True
        
        return False
    
    def run(self):
        """Main execution"""
        print("=" * 60)
        print("🚀 Reddit Data Downloader with Live Filtering")
        print("=" * 60)
        
        # Check tools
        if not self.check_tools():
            print("\n⚠️ Please install missing tools first")
            return
        
        # Get available data
        urls = self.get_data_urls()
        
        if not urls:
            print("\n❌ No data sources available")
            print("\n💡 Alternative: Download manually from:")
            print("  https://github.com/ArthurHeitmann/arctic_shift")
            return
        
        print(f"\n📅 Found {len(urls)} months available")
        for i, (month, url) in enumerate(urls[:5], 1):  # Show first 5
            print(f"  {i}. {month}")
        
        # Ask user selection
        print("\n❓ Which months to download?")
        print("  1 = Latest month only")
        print("  2 = Last 3 months")
        print("  3 = Custom selection")
        
        choice = input("  Your choice (1-3): ").strip()
        
        if choice == "1":
            selected = urls[:1]
        elif choice == "2":
            selected = urls[:3]
        elif choice == "3":
            print("\nAvailable months:")
            for i, (month, _) in enumerate(urls, 1):
                print(f"  {i}. {month}")
            indices = input("Enter numbers (e.g., 1,3,5): ").strip()
            try:
                idx_list = [int(x.strip())-1 for x in indices.split(',')]
                selected = [urls[i] for i in idx_list if 0 <= i < len(urls)]
            except:
                print("❌ Invalid selection")
                return
        else:
            print("❌ Invalid choice")
            return
        
        print(f"\n📥 Will download {len(selected)} month(s)")
        
        # Estimate
        est_size = len(selected) * 0.15  # ~150MB per month after filtering
        print(f"💾 Estimated final size: ~{est_size:.2f} GB")
        
        confirm = input("\n❓ Start download? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return
        
        # Process each month
        start_time = datetime.now()
        
        for month, url in selected:
            success = self.download_and_filter_stream(month, url)
            if not success:
                print(f"⚠️ Failed to process {month}")
        
        # Summary
        duration = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("✅ Processing Complete!")
        print(f"  Comments filtered: {self.stats['filtered_comments']:,}")
        print(f"  Total size: {self.stats['total_size_mb']:.1f} MB")
        print(f"  Time taken: {duration:.1f} seconds")
        print(f"  Output location: {self.output_dir}/")
        
        print("\n🎯 Next steps:")
        print("  1. Review the filtered data")
        print("  2. Run the bot with: python3 src/bot.py")

if __name__ == "__main__":
    downloader = RedditDataDownloader()
    downloader.run()