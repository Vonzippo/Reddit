# Scripts Folder

This folder contains all data processing scripts for the Reddit Karma Farm project.

## Download Scripts
- `download_2024_comments.py` - Download 2024 comments
- `download_arctic_shift.py` - Download from Arctic Shift archive
- `download_arctic_torrents.py` - Download via torrents
- `download_posts.py` - Download Reddit posts
- `download_with_filter.py` - Download with filtering
- `download_latest.sh` - Download latest data
- `download_november.sh` - Download November data
- `download_posts_latest.sh` - Download latest posts

## Filter Scripts
- `filter_downloaded_data.py` - Filter downloaded data
- `filter_fast.py` - Fast filtering
- `filter_november.py` - Filter November data
- `filter_posts.py` - Filter posts
- `filter_and_cleanup.sh` - Filter and cleanup
- `filter_november.sh` - Shell script for November filtering
- `filter_posts_now.sh` - Filter posts immediately

## Extract Scripts
- `extract_november_content.py` - Extract November content
- `extract_top_content_repost.py` - Extract top content for reposting

## Monitoring
- `monitor_progress.sh` - Monitor download/processing progress

## Usage
All scripts should be run from the parent directory:
```bash
cd "/Users/patrick/Desktop/Reddit Karma Farm"
python3 scripts/script_name.py
# or
./scripts/script_name.sh
```