#!/usr/bin/env python3
"""
Fetch NLConnect member data from Wayback Machine archives and live site.
Extracts member company slugs from /onze-leden/ links on each snapshot.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
from datetime import datetime

# NLConnect Wayback URLs (oldest to newest) + live URL
URLS = [
    "https://web.archive.org/web/20230322090811/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20230609040256/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20230927043922/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20240301035232/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20240620151223/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20240912120636/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20241208212519/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20250219013027/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20250426010256/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20250811135039/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20251009131550/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20251126081753/https://www.nlconnect.org/onze-leden",
    "https://web.archive.org/web/20251213220505/https://www.nlconnect.org/onze-leden",
    "https://www.nlconnect.org/onze-leden",
]

output_dir = '/workspaces/NLdigital/nlconnect_data'
os.makedirs(output_dir, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def extract_date_from_wayback_url(url):
    """Extract date from Wayback Machine URL timestamp."""
    m = re.search(r'/web/(\d{14})/', url)
    if m:
        ts = m.group(1)
        return datetime.strptime(ts, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def extract_members_from_html(html_content):
    """Extract member slugs from NLConnect onze-leden page HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    members = set()

    # Find all links pointing to /onze-leden/<slug>
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Match both absolute and relative URLs
        m = re.search(r'/onze-leden/([a-z0-9][a-z0-9\-]*[a-z0-9])(?:/|$|\?)', href)
        if not m:
            m = re.search(r'/onze-leden/([a-z0-9][a-z0-9\-]*[a-z0-9])$', href)
        if m:
            slug = m.group(1)
            # Skip navigation/category pages
            if slug not in ('onze-leden', 'ook-lid-worden', 'over-ons'):
                members.add(slug)

    return sorted(members)


print("=" * 60)
print("Fetching NLConnect member data")
print("=" * 60)

all_snapshots = []

for i, url in enumerate(URLS):
    date_str = extract_date_from_wayback_url(url)
    is_live = 'web.archive.org' not in url

    print(f"\n[{i+1}/{len(URLS)}] {'LIVE' if is_live else date_str}")
    print(f"  URL: {url[:80]}...")

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            print(f"  Failed: HTTP {resp.status_code}")
            continue

        members = extract_members_from_html(resp.text)
        print(f"  Found {len(members)} members")

        snapshot = {
            'date': date_str,
            'url': url,
            'member_count': len(members),
            'members': members
        }

        # Save individual snapshot
        safe_date = date_str.replace(' ', '_').replace(':', '-')
        filename = f"members_{safe_date}.json"
        with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)

        all_snapshots.append(snapshot)
        print(f"  Saved to {filename}")

        time.sleep(2)

    except Exception as e:
        print(f"  Error: {e}")

print(f"\n{'=' * 60}")
print(f"Fetched {len(all_snapshots)} snapshots")
print("=" * 60)

# Save summary
summary = [{'date': s['date'], 'member_count': s['member_count']} for s in all_snapshots]
with open(os.path.join(output_dir, 'summary.json'), 'w') as f:
    json.dump(summary, f, indent=2)

print(f"Summary saved to {output_dir}/summary.json")
