#!/usr/bin/env python3
"""
Analyze member inflow and outflow for Sankey diagram
Properly parses company names from URLs
"""

import json
import os
from datetime import datetime
import pandas as pd
import re

def extract_company_name(url):
    """Extract company name from URL - only from actual leden URLs, not logo images"""
    url = url.strip()
    # Only process actual member profile URLs, skip logo images
    if '/leden/' in url and not url.endswith('.jpg') and not url.endswith('.png'):
        parts = url.split('/leden/')
        if len(parts) > 1:
            company_slug = parts[1].strip('/').strip()
            # Make sure it's not a logo path
            if not company_slug.startswith('wp-content'):
                return slugify(company_slug)
    return None


def slugify(name: str) -> str:
    """Return a canonical slug used across scripts.

    Rules:
    - lowercase
    - normalize variants like "b v", "b-v", "b.v" -> "bv"
    - remove leading "logo-" when present
    - replace non-alphanumeric characters with single hyphen
    - trim extra hyphens
    """
    s = (name or '').strip().lower()
    # remove any leading/trailing slashes
    s = s.strip('/')
    # drop common prefix
    if s.startswith('logo-'):
        s = s[len('logo-'):]
    # remove file extensions if any
    s = re.sub(r"\.(jpg|jpeg|png|gif)$", '', s)
    # normalize b v / b-v / b.v -> bv
    s = re.sub(r"\bb[\.\-\s]?v\b", 'bv', s)
    # replace any non-alphanumeric sequences with hyphen
    s = re.sub(r'[^a-z0-9]+', '-', s)
    # collapse hyphens
    s = re.sub(r'-{2,}', '-', s)
    # strip leading/trailing hyphens
    s = s.strip('-')
    return s

# Load all member data
data_dir = '/workspaces/NLdigital/member_data'
member_files = sorted([f for f in os.listdir(data_dir) if f.startswith('members_') and f.endswith('.json')])

print("="*60)
print("Analyzing member flows for Sankey diagram")
print("="*60)

member_snapshots = []

# Load all snapshots and extract company names
for filename in member_files:
    with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Extract company names and deduplicate
        company_names = set()
        for url in data['members']:
            company_name = extract_company_name(url)
            if company_name:  # Only add if extraction was successful
                company_names.add(company_name)
        
        member_snapshots.append({
            'date': data['date'],
            'members': company_names,
            'count': len(company_names),
            'raw_urls': len(data['members']),
            'duplicates_removed': len(data['members']) - len(company_names)
        })

print(f"\nLoaded {len(member_snapshots)} snapshots")

# Show deduplication stats
print("\nDeduplication Statistics:")
print("-" * 60)
for snap in member_snapshots:
    dedup_pct = (snap['duplicates_removed'] / snap['raw_urls'] * 100) if snap['raw_urls'] > 0 else 0
    print(f"{snap['date']}: {snap['raw_urls']} URLs → {snap['count']} companies (removed {snap['duplicates_removed']} duplicates, {dedup_pct:.1f}%)")
print("-" * 60)

# Analyze flows between consecutive snapshots
sankey_data = []

for i in range(len(member_snapshots) - 1):
    current = member_snapshots[i]
    next_snap = member_snapshots[i + 1]
    
    current_date = current['date']
    next_date = next_snap['date']
    
    current_members = current['members']
    next_members = next_snap['members']
    
    # Members that stayed
    stayed = current_members & next_members
    
    # Members that joined (new in next_snap)
    joined = next_members - current_members
    
    # Members that left (in current but not in next_snap)
    left = current_members - next_members
    
    print(f"\n{current_date} → {next_date}")
    print(f"  Current members: {len(current_members)}")
    print(f"  Next members:    {len(next_members)}")
    print(f"  Stayed:  {len(stayed)}")
    print(f"  Joined:  {len(joined)}")
    print(f"  Left:    {len(left)}")
    print(f"  Net change: {len(next_members) - len(current_members):+d}")
    
    sankey_data.append({
        'from_date': current_date,
        'to_date': next_date,
        'stayed': len(stayed),
        'joined': len(joined),
        'left': len(left),
        'stayed_members': sorted(list(stayed)),
        'joined_members': sorted(list(joined)),
        'left_members': sorted(list(left))
    })

# Save flow analysis
flow_file = os.path.join(data_dir, 'member_flows.json')
with open(flow_file, 'w', encoding='utf-8') as f:
    json.dump(sankey_data, f, indent=2)

print(f"\n" + "="*60)
print(f"Flow analysis saved to {flow_file}")
print("="*60)

# Create summary for Sankey
print("\nPreparing Sankey data...")

# Group flows by quarters/months for better visualization
import re
from datetime import datetime as dt

# Create a simplified version for Sankey
sankey_simplified = []

for flow in sankey_data:
    from_date_obj = dt.strptime(flow['from_date'], '%Y-%m-%d %H:%M:%S')
    to_date_obj = dt.strptime(flow['to_date'], '%Y-%m-%d %H:%M:%S')
    
    from_date_str = from_date_obj.strftime('%Y-%m-%d')
    to_date_str = to_date_obj.strftime('%Y-%m-%d')
    
    # Add flows for stayed members (coming from the first date)
    if flow['stayed'] > 0:
        sankey_simplified.append({
            'source': f"{from_date_str}",
            'target': f"{to_date_str}",
            'value': flow['stayed'],
            'label': 'Stayed'
        })
    
    # Add flows for new members (joining)
    if flow['joined'] > 0:
        sankey_simplified.append({
            'source': f"New members",
            'target': f"{to_date_str}",
            'value': flow['joined'],
            'label': 'Joined'
        })
    
    # Add flows for leaving members
    if flow['left'] > 0:
        sankey_simplified.append({
            'source': f"{from_date_str}",
            'target': f"Left",
            'value': flow['left'],
            'label': 'Left'
        })

# Save simplified Sankey data
sankey_file = os.path.join(data_dir, 'sankey_data.json')
with open(sankey_file, 'w', encoding='utf-8') as f:
    json.dump(sankey_simplified, f, indent=2)

print(f"Sankey data saved to {sankey_file}")

# Create a CSV for easy visualization
sankey_df = pd.DataFrame(sankey_simplified)
csv_file = os.path.join(data_dir, 'sankey_data.csv')
sankey_df.to_csv(csv_file, index=False)
print(f"Sankey CSV saved to {csv_file}")

print("\n" + "="*60)
print("Analysis complete! Ready to create visualizations.")
print("="*60)
