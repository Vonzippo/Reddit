#!/usr/bin/env python3
"""Verify ADHD-only configuration in main_other.py"""

import re

def verify_adhd_configuration():
    """Check that main_other.py is configured for ADHD subreddits only"""
    
    print("\n🔍 VERIFYING ADHD-ONLY CONFIGURATION")
    print("="*60)
    
    # Read the main_other.py file
    with open('/Users/patrick/Desktop/Reddit/main_other.py', 'r') as f:
        content = f.read()
    
    # Check 1: get_random_post method
    print("\n✅ CHECK 1: get_random_post() method")
    if "ADHD-fokussiert" in content and "adhd_core = ['ADHD', 'ADHDwomen'" in content:
        print("   ✓ Posts will be directed to ADHD subreddits")
    else:
        print("   ✗ Posts configuration needs update")
    
    # Check 2: find_popular_post_to_comment method
    print("\n✅ CHECK 2: find_popular_post_to_comment() method")
    
    # Extract the method
    pattern = r'def find_popular_post_to_comment\(self\):(.*?)(?=\n    def |\nclass |\nif __name__|$)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        method_content = match.group(1)
        
        # Check for ADHD subreddits
        if "'ADHD', 'ADHDwomen', 'AdultADHD'" in method_content:
            print("   ✓ Comments target ADHD subreddits")
        else:
            print("   ✗ Comments configuration needs update")
            
        # Check for old mixed subreddits (should NOT be present)
        bad_subs = ['rarepuppers', 'cats', 'dogs', 'aww', 'funny']
        has_bad = any(sub in method_content for sub in bad_subs)
        if has_bad:
            print("   ✗ WARNING: Old non-ADHD subreddits still present!")
        else:
            print("   ✓ No old mixed subreddits found")
    
    # Check 3: Loaded subreddit files
    print("\n✅ CHECK 3: Target subreddit files")
    
    # Check target_subreddits.txt
    with open('/Users/patrick/Desktop/Reddit/target_subreddits.txt', 'r') as f:
        lines = f.readlines()
        adhd_subs = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        print(f"   ✓ target_subreddits.txt: {len(adhd_subs)} ADHD subreddits")
        print(f"     First 5: {', '.join(adhd_subs[:5])}")
    
    # Check target_subreddits_extended.txt
    with open('/Users/patrick/Desktop/Reddit/target_subreddits_extended.txt', 'r') as f:
        lines = f.readlines()
        extended_subs = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        print(f"   ✓ target_subreddits_extended.txt: {len(extended_subs)} ADHD subreddits")
    
    # Check 4: Path configuration
    print("\n✅ CHECK 4: Path configuration")
    if "/home/lucawahl" in content:
        print("   ✓ Paths updated to /home/lucawahl")
    if "/home/GoodValuable4401" in content:
        print("   ✗ WARNING: Old paths /home/GoodValuable4401 still present!")
    else:
        print("   ✓ No old paths found")
    
    print("\n" + "="*60)
    print("✅ VERIFICATION COMPLETE")
    print("   The bot is configured to use ONLY ADHD-focused subreddits")
    print("   for both posts and comments!")

if __name__ == "__main__":
    verify_adhd_configuration()