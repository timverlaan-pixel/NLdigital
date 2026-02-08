#!/usr/bin/env python3
"""
Script to fetch member data from NLdigital archives and save them
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from urllib.parse import urljoin
import time

# Load the metadata
excel_file = '/workspaces/NLDigital.xlsx'
df_metadata = pd.read_excel(excel_file, sheet_name='leden_aantal_datum')

# Create output directory
output_dir = '/workspaces/NLdigital/member_data'
os.makedirs(output_dir, exist_ok=True)

# Clean URLs (remove "view-source:" prefix)
df_metadata['url_clean'] = df_metadata['url'].str.replace('view-source:', '')

print("="*60)
print("Fetching NLdigital member data from archive URLs")
print("="*60)

all_members_data = []

for idx, row in df_metadata.iterrows():
    datum = str(row['Datum & tijd'])
    aantal = int(row['Aantal leden'])
    url = row['url_clean']
    
    print(f"\n[{idx+1}/{len(df_metadata)}] Processing {datum}")
    print(f"  Aantal leden according to sheet: {aantal}")
    print(f"  URL: {url[:100]}...")
    
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"  ✗ Failed to fetch (status {response.status_code})")
            continue
        
        # Parse the XML/HTML
        soup = BeautifulSoup(response.content, 'xml')
        
        # Look for loc tags (URLs in sitemap)
        locs = soup.find_all('loc')
        
        if not locs:
            # Try as HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            locs = soup.find_all('loc')
        
        print(f"  Found {len(locs)} member URLs in sitemap")
        
        # Extract member identifiers/paths from URLs
        members = []
        for loc in locs:
            url_text = loc.text.strip()
            members.append(url_text)
        
        # Save to file
        output_file = os.path.join(output_dir, f"members_{datum.replace(' ', '_').replace(':', '-')}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'date': str(datum),
                'member_count': len(members),
                'expected_count': int(aantal),
                'members': members
            }, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Saved {len(members)} members")
        
        # Store for later analysis
        all_members_data.append({
            'date': datum,
            'member_count': len(members),
            'expected_count': int(aantal),
            'members': set(members)  # Use set for easy comparison
        })
        
        # Rate limiting
        time.sleep(2)
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

print("\n" + "="*60)
print("Member data fetching complete!")
print(f"Saved {len(all_members_data)} snapshots to {output_dir}")
print("="*60)

# Save summary
summary_file = os.path.join(output_dir, 'summary.json')
summary_data = [{
    'date': str(item['date']),
    'member_count': item['member_count'],
    'expected_count': item['expected_count']
} for item in all_members_data]

with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary_data, f, indent=2)

print(f"Summary saved to {summary_file}")
