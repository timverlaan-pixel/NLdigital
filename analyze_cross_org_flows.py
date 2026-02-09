#!/usr/bin/env python3
"""
Analyze cross-organization flows between NLdigital and NLConnect.
Identifies companies that left one organization and joined the other.
"""

import json
import os
from datetime import datetime

nldigital_dir = '/workspaces/NLdigital/member_data'
nlconnect_dir = '/workspaces/NLdigital/nlconnect_data'


def load_snapshots(data_dir):
    """Load member snapshots sorted by date."""
    files = sorted([f for f in os.listdir(data_dir) if f.startswith('members_') and f.endswith('.json')])
    snapshots = []
    for filename in files:
        with open(os.path.join(data_dir, filename), 'r') as f:
            data = json.load(f)
            snapshots.append({
                'date': data['date'],
                'members': set(data.get('members', []))
            })
    return snapshots


def load_flows(data_dir):
    with open(os.path.join(data_dir, 'member_flows.json'), 'r') as f:
        return json.load(f)


# Load data
nldigital_flows = load_flows(nldigital_dir)
nlconnect_flows = load_flows(nlconnect_dir)

# Collect all companies that ever left/joined each org
nldigital_departed = set()
nldigital_joined = set()
nlconnect_departed = set()
nlconnect_joined = set()

for flow in nldigital_flows:
    nldigital_departed.update(flow.get('left_members', []))
    nldigital_joined.update(flow.get('joined_members', []))

for flow in nlconnect_flows:
    nlconnect_departed.update(flow.get('left_members', []))
    nlconnect_joined.update(flow.get('joined_members', []))

# NLdigital uses slugified company names from URLs like /leden/company-slug
# NLConnect uses slugs from /onze-leden/company-slug
# These may not match directly, so we need fuzzy matching

# First try: exact slug match
digital_left_connect_joined = nldigital_departed & nlconnect_joined
connect_left_digital_joined = nlconnect_departed & nldigital_joined

# Also check: companies currently in both (overlapping membership)
nldigital_snaps = load_snapshots(nldigital_dir)
nlconnect_snaps = load_snapshots(nlconnect_dir)

# Get current members of each (last snapshot)
# NLdigital members are full URLs, extract slugs
import re

def slugify_nldigital(url):
    """Extract slug from NLdigital member URL."""
    if '/leden/' in url and 'logo' not in url.lower():
        parts = url.split('/leden/')
        if len(parts) > 1:
            s = parts[1].strip('/').strip().lower()
            if not s.startswith('wp-content'):
                s = re.sub(r"\bb[\.\-\s]?v\b", 'bv', s)
                s = re.sub(r'[^a-z0-9]+', '-', s)
                s = re.sub(r'-{2,}', '-', s).strip('-')
                return s
    return None

nldigital_current_slugs = set()
for url in nldigital_snaps[-1]['members']:
    slug = slugify_nldigital(url)
    if slug:
        nldigital_current_slugs.add(slug)

nlconnect_current = nlconnect_snaps[-1]['members']

# Find overlap in current membership
overlap = nldigital_current_slugs & nlconnect_current

print("=" * 70)
print("CROSS-ORGANIZATION FLOW ANALYSIS: NLdigital <-> NLConnect")
print("=" * 70)

print(f"\nNLdigital total departed: {len(nldigital_departed)}")
print(f"NLdigital total joined: {len(nldigital_joined)}")
print(f"NLConnect total departed: {len(nlconnect_departed)}")
print(f"NLConnect total joined: {len(nlconnect_joined)}")

print(f"\n--- Companies that LEFT NLdigital and JOINED NLConnect ---")
if digital_left_connect_joined:
    for c in sorted(digital_left_connect_joined):
        print(f"  {c}")
else:
    print("  None found (exact slug match)")

print(f"\n--- Companies that LEFT NLConnect and JOINED NLdigital ---")
if connect_left_digital_joined:
    for c in sorted(connect_left_digital_joined):
        print(f"  {c}")
else:
    print("  None found (exact slug match)")

print(f"\n--- Companies currently in BOTH organizations ---")
if overlap:
    for c in sorted(overlap):
        print(f"  {c}")
else:
    print("  None found (exact slug match)")

# Try fuzzy matching - normalize slugs more aggressively
def normalize_slug(s):
    """Aggressive normalization for cross-org matching."""
    s = s.lower().strip('-').strip('/')
    s = re.sub(r'\bbv\b', '', s)
    s = re.sub(r'\bnl\b', '', s)
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

# Build normalized lookup
nldigital_departed_norm = {normalize_slug(c): c for c in nldigital_departed}
nlconnect_joined_norm = {normalize_slug(c): c for c in nlconnect_joined}
nlconnect_departed_norm = {normalize_slug(c): c for c in nlconnect_departed}
nldigital_joined_norm = {normalize_slug(c): c for c in nldigital_joined}

fuzzy_d2c = set(nldigital_departed_norm.keys()) & set(nlconnect_joined_norm.keys())
fuzzy_c2d = set(nlconnect_departed_norm.keys()) & set(nldigital_joined_norm.keys())

print(f"\n--- Fuzzy match: LEFT NLdigital -> JOINED NLConnect ---")
cross_flows = []
if fuzzy_d2c:
    for norm in sorted(fuzzy_d2c):
        d_name = nldigital_departed_norm[norm]
        c_name = nlconnect_joined_norm[norm]
        print(f"  NLdigital: {d_name} -> NLConnect: {c_name}")
        cross_flows.append({
            'from_org': 'NLdigital',
            'to_org': 'NLConnect',
            'nldigital_slug': d_name,
            'nlconnect_slug': c_name,
            'direction': 'digital_to_connect'
        })
else:
    print("  None found")

print(f"\n--- Fuzzy match: LEFT NLConnect -> JOINED NLdigital ---")
if fuzzy_c2d:
    for norm in sorted(fuzzy_c2d):
        c_name = nlconnect_departed_norm[norm]
        d_name = nldigital_joined_norm[norm]
        print(f"  NLConnect: {c_name} -> NLdigital: {d_name}")
        cross_flows.append({
            'from_org': 'NLConnect',
            'to_org': 'NLdigital',
            'nlconnect_slug': c_name,
            'nldigital_slug': d_name,
            'direction': 'connect_to_digital'
        })
else:
    print("  None found")

# Fuzzy overlap in current membership
nldigital_current_norm = {normalize_slug(s): s for s in nldigital_current_slugs}
nlconnect_current_norm = {normalize_slug(s): s for s in nlconnect_current}
fuzzy_overlap = set(nldigital_current_norm.keys()) & set(nlconnect_current_norm.keys())

print(f"\n--- Fuzzy match: Currently in BOTH ---")
dual_members = []
if fuzzy_overlap:
    for norm in sorted(fuzzy_overlap):
        d = nldigital_current_norm[norm]
        c = nlconnect_current_norm[norm]
        print(f"  NLdigital: {d} | NLConnect: {c}")
        dual_members.append({'nldigital': d, 'nlconnect': c})
else:
    print("  None found")

# Save results
results = {
    'cross_flows': cross_flows,
    'dual_members': dual_members,
    'stats': {
        'nldigital_departed': len(nldigital_departed),
        'nldigital_joined': len(nldigital_joined),
        'nlconnect_departed': len(nlconnect_departed),
        'nlconnect_joined': len(nlconnect_joined),
        'digital_to_connect': len([f for f in cross_flows if f['direction'] == 'digital_to_connect']),
        'connect_to_digital': len([f for f in cross_flows if f['direction'] == 'connect_to_digital']),
        'dual_members': len(dual_members)
    }
}

output_file = '/workspaces/NLdigital/cross_org_flows.json'
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to {output_file}")
print("=" * 70)
