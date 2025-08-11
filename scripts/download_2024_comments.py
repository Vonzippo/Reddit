#!/usr/bin/env python3
import os
import json
import zstandard as zstd
import requests
from datetime import datetime
from tqdm import tqdm
import time

PUSHSHIFT_BASE_URL = "https://the-eye.eu/redarcs/files/"
TARGET_SUBREDDITS_FILE = "target_subreddits.txt"
OUTPUT_DIR = "pushshift_dumps/2024_filtered"

def load_target_subreddits():
    """Load target subreddits from file"""
    with open(TARGET_SUBREDDITS_FILE, 'r') as f:
        return [line.strip().lower() for line in f if line.strip()]

def get_2024_comment_files():
    """Get list of 2024 comment dump files and their sizes"""
    files_info = []
    
    print("Checking available 2024 comment dumps...")
    
    # 2024 monthly dumps (RC = Reddit Comments)
    months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    
    for month in months:
        filename = f"RC_2024-{month}.zst"
        url = f"{PUSHSHIFT_BASE_URL}{filename}"
        
        try:
            # HEAD request to get file size
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                size = int(response.headers.get('Content-Length', 0))
                size_gb = size / (1024**3)
                files_info.append({
                    'filename': filename,
                    'url': url,
                    'size': size,
                    'size_gb': size_gb
                })
                print(f"  ✓ {filename}: {size_gb:.2f} GB")
            else:
                print(f"  ✗ {filename}: Not available")
        except Exception as e:
            print(f"  ✗ {filename}: Error checking - {e}")
    
    return files_info

def estimate_filtered_size(total_size, target_subreddits_count=20, total_subreddits=150000):
    """Estimate size after filtering (rough approximation)"""
    # Assuming our subreddits are average to above-average in activity
    ratio = (target_subreddits_count * 5) / total_subreddits  # multiply by 5 for popular subs
    return total_size * ratio

def download_and_filter_comments(file_info, target_subreddits):
    """Download and filter comments from a single file"""
    filename = file_info['filename']
    url = file_info['url']
    
    print(f"\nProcessing {filename}...")
    print(f"Size: {file_info['size_gb']:.2f} GB")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, filename.replace('.zst', '_filtered.jsonl'))
    
    # Stream download with filtering
    response = requests.get(url, stream=True)
    dctx = zstd.ZstdDecompressor(max_window_size=2147483648)
    
    matched_count = 0
    total_count = 0
    
    with open(output_file, 'w') as outfile:
        with dctx.stream_reader(response.raw) as reader:
            text_stream = io.TextIOWrapper(reader, encoding='utf-8')
            
            for line in tqdm(text_stream, desc=f"Filtering {filename}"):
                total_count += 1
                try:
                    comment = json.loads(line)
                    subreddit = comment.get('subreddit', '').lower()
                    
                    if subreddit in target_subreddits:
                        outfile.write(line)
                        matched_count += 1
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    continue
    
    print(f"Filtered {matched_count:,} comments from {total_count:,} total")
    return matched_count, total_count

def main():
    print("Reddit 2024 Comments Downloader & Filter")
    print("=" * 50)
    
    # Load target subreddits
    target_subreddits = load_target_subreddits()
    print(f"\nTarget subreddits loaded: {len(target_subreddits)}")
    print(f"Subreddits: {', '.join(target_subreddits[:5])}...")
    
    # Get available files
    files_info = get_2024_comment_files()
    
    if not files_info:
        print("\nNo 2024 comment files available!")
        return
    
    # Calculate total size
    total_size = sum(f['size'] for f in files_info)
    total_size_gb = total_size / (1024**3)
    
    estimated_filtered_gb = estimate_filtered_size(total_size_gb, len(target_subreddits))
    
    print(f"\n📊 Size Information:")
    print(f"  Total uncompressed size: ~{total_size_gb:.2f} GB")
    print(f"  Estimated filtered size: ~{estimated_filtered_gb:.2f} GB")
    print(f"  Available files: {len(files_info)}")
    
    print("\nNOTE: The actual Pushshift dumps for 2024 might not be available yet.")
    print("The most recent dumps are usually from the Pushshift Archive:")
    print("https://github.com/ArthurHeitmann/arctic_shift")
    
    # Ask user to confirm
    response = input("\nDo you want to proceed with checking Arctic Shift for 2024 data? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    print("\n🔍 Alternative: Arctic Shift provides more recent data.")
    print("Visit: https://github.com/ArthurHeitmann/arctic_shift")
    print("\nThey provide torrent files for recent Reddit data including 2024.")

if __name__ == "__main__":
    # Check if we need to install dependencies
    try:
        import zstandard
        import tqdm
    except ImportError:
        print("Installing required packages...")
        os.system("pip3 install zstandard tqdm requests")
    
    import io
    main()