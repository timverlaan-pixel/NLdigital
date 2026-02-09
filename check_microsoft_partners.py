#!/usr/bin/env python3
"""
Check which current NLdigital members are Microsoft Partners.
Uses the Microsoft Partner Directory API.
"""

import json
import os
import re
import time
import requests
from urllib.parse import quote

data_dir = '/workspaces/NLdigital/member_data'
API_BASE = "https://main.prod.marketplacepartnerdirectory.azure.com/api/partners"


def slugify_url(url):
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


def slug_to_search_name(slug):
    """Convert slug to a search-friendly company name.
    E.g. 'accenture-bv' -> 'Accenture'
    """
    name = slug.replace('-', ' ')
    # Remove common suffixes that won't help with search
    name = re.sub(r'\b(bv|nv|holding|nederland|netherlands|group|international)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def search_partner(company_name, country='NL'):
    """Search Microsoft Partner Directory for a company."""
    filter_str = f"freetext={quote(company_name)}&country={country}&onlyThisCountry=true&pageSize=5&locationNotRequired=true"
    url = f"{API_BASE}?filter={quote(filter_str, safe='')}"
    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if resp.status_code == 200:
            data = resp.json()
            return data.get('matchingPartners', {})
        return None
    except Exception as e:
        print(f"  Error searching: {e}")
        return None


# Load latest NLdigital member snapshot
member_files = sorted([f for f in os.listdir(data_dir) if f.startswith('members_') and f.endswith('.json')])
with open(os.path.join(data_dir, member_files[-1]), 'r') as f:
    latest = json.load(f)

# Extract unique member slugs
members = set()
for url in latest['members']:
    slug = slugify_url(url)
    if slug:
        members.add(slug)

members = sorted(members)
print(f"Checking {len(members)} NLdigital members against Microsoft Partner Directory...")
print("=" * 70)

results = []
found_count = 0

for i, slug in enumerate(members):
    search_name = slug_to_search_name(slug)
    if len(search_name) < 3:
        continue

    result = search_partner(search_name)
    if result and result.get('totalCount', 0) > 0:
        items = result.get('items', [])
        # Check if any result is actually in Netherlands and name matches reasonably
        for item in items:
            loc = item.get('location', {}).get('address', {})
            partner_country = loc.get('country', '')
            partner_name = item.get('name', '')

            # Check if the partner name contains the search term (fuzzy match)
            search_words = search_name.lower().split()
            partner_lower = partner_name.lower()
            match_score = sum(1 for w in search_words if len(w) > 2 and w in partner_lower)

            if match_score > 0 and partner_country == 'NL':
                found_count += 1
                designations = item.get('solutionsPartnerDesignations', [])
                solutions = item.get('solutions', [])
                competencies = item.get('competencies', {})
                products = item.get('product', []) if isinstance(item.get('product'), list) else []
                endorsed = item.get('endorsedProducts', []) if isinstance(item.get('endorsedProducts'), list) else []

                entry = {
                    'nldigital_slug': slug,
                    'search_name': search_name,
                    'ms_partner_name': partner_name,
                    'ms_partner_id': item.get('partnerId', ''),
                    'city': loc.get('city', ''),
                    'designations': designations,
                    'solutions': solutions[:10],
                    'competencies': competencies,
                    'products': products,
                    'endorsed_products': endorsed
                }
                results.append(entry)

                print(f"[{i+1}/{len(members)}] {slug} -> {partner_name} ({loc.get('city', '?')})")
                if designations:
                    print(f"  Designations: {', '.join(designations)}")
                if solutions:
                    print(f"  Solutions: {', '.join(solutions[:5])}")
                break
        else:
            # No NL match found
            pass

    # Rate limit: ~2 requests per second
    if i % 10 == 0 and i > 0:
        print(f"  ... processed {i}/{len(members)} ({found_count} partners found)")
    time.sleep(0.5)

print("\n" + "=" * 70)
print(f"RESULTS: {found_count} of {len(members)} NLdigital members are Microsoft Partners in NL")
print("=" * 70)

# Save results
output_file = '/workspaces/NLdigital/microsoft_partners.json'
with open(output_file, 'w') as f:
    json.dump({
        'total_members': len(members),
        'microsoft_partners': len(results),
        'partners': results
    }, f, indent=2)

print(f"\nResults saved to {output_file}")
