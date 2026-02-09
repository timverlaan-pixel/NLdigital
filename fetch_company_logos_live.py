#!/usr/bin/env python3
"""
Fetch company logos directly from NLDigital member profiles
"""

import json
import os
import re
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import time

# Load member flows
data_dir = '/workspaces/NLdigital/member_data'
with open(os.path.join(data_dir, 'member_flows.json'), 'r') as f:
    flows = json.load(f)

# Collect all unique members
all_members = set()
for flow in flows:
    all_members.update(flow.get('stayed_members', []))
    all_members.update(flow.get('joined_members', []))
    all_members.update(flow.get('left_members', []))

print(f"Total unique members: {len(all_members)}")

# Fetch logos from NLDigital
logos = {}
failed = []

def fetch_logo_from_profile(member_slug: str) -> str:
    """Fetch logo URL from NLDigital member profile page"""
    url = f"https://nldigital.nl/leden/{member_slug}/"
    
    try:
        # Use a User-Agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = Request(url, headers=headers)
        
        with urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Try to find logo URL via Open Graph image meta tag
            og_match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html)
            if og_match:
                return og_match.group(1)
            
            # Also try to find in <img> tags with 'logo' in class/src
            img_matches = re.findall(r'<img[^>]*src=["\']([^"\']*logo[^"\']*)["\']', html, re.IGNORECASE)
            if img_matches:
                # Return first logo image found
                logo_url = img_matches[0]
                # Ensure absolute URL
                if logo_url.startswith('/'):
                    return f"https://nldigital.nl{logo_url}"
                elif not logo_url.startswith('http'):
                    return f"https://nldigital.nl/{logo_url}"
                return logo_url
            
            # Try common img src patterns
            img_matches = re.findall(r'<img[^>]*src=["\']([^"\']+\.(?:jpg|png|gif|svg))["\'][^>]*(?:alt|title)=["\']([^"\']*)["\']', html, re.IGNORECASE)
            for src, alt in img_matches:
                if 'logo' in src.lower() or 'logo' in alt.lower():
                    if src.startswith('/'):
                        return f"https://nldigital.nl{src}"
                    elif not src.startswith('http'):
                        return f"https://nldigital.nl/{src}"
                    return src
            
        return None
    except (HTTPError, URLError, Exception) as e:
        print(f"  ⚠️ Failed to fetch {member_slug}: {type(e).__name__}")
        return None

print("\nFetching logos from NLDigital profiles...")
success_count = 0

for i, member in enumerate(sorted(all_members), 1):
    if i % 50 == 0:
        print(f"  Progress: {i}/{len(all_members)}")
        time.sleep(1)  # Rate limiting
    
    logo_url = fetch_logo_from_profile(member)
    if logo_url:
        logos[member] = logo_url
        success_count += 1
    else:
        failed.append(member)

print(f"\n✓ Successfully fetched: {success_count}/{len(all_members)}")
print(f"✗ Failed: {len(failed)}")

if failed and len(failed) <= 20:
    print(f"\nFailed members: {failed}")

# Save logos to a JSON file for use in gallery
output_file = os.path.join(data_dir, 'logos_fetched.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(logos, f, indent=2)

print(f"\n✓ Logos saved to: {output_file}")
