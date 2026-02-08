#!/usr/bin/env python3
"""
Create a visual gallery of company logos that left in each batch
Direct approach: pre-fetch all logo URLs and embed in HTML
"""

import json
import os
from datetime import datetime
import re

# Local slugify to match other scripts
def slugify(name: str) -> str:
    s = (name or '').strip().lower()
    s = s.strip('/')
    if s.startswith('logo-'):
        s = s[len('logo-'):]
    s = re.sub(r"\.(jpg|jpeg|png|gif)$", '', s)
    s = re.sub(r"\bb[\.\-\s]?v\b", 'bv', s)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-{2,}', '-', s)
    s = s.strip('-')
    return s

# Load member flows and snapshots
data_dir = '/workspaces/NLdigital/member_data'

with open(os.path.join(data_dir, 'member_flows.json'), 'r') as f:
    flows = json.load(f)

# Load all member snapshots to find logo URLs
member_files = sorted([f for f in os.listdir(data_dir) if f.startswith('members_') and f.endswith('.json')])

# Build a complete mapping of all member -> logo URL across all snapshots
all_logos = {}  # member_slug -> logo_url

for filename in member_files:
    with open(os.path.join(data_dir, filename), 'r') as f:
        data = json.load(f)
        logo_urls = [u for u in data['members'] if 'logo' in u.lower()]

        # Create mapping (normalize keys so they match company slugs)
        for logo_url in logo_urls:
            logo_filename = logo_url.split('/')[-1]
            key = slugify(logo_filename)
            if key not in all_logos:  # Use first occurrence (most recent)
                all_logos[key] = logo_url

print(f"✓ Found {len(all_logos)} unique company logos across all snapshots")

# Build mapping: normalized slug -> original URL path (for correct NLdigital links)
# The slugify() normalizes "b-v" to "bv", but the actual URLs use "b-v"
slug_to_original = {}  # normalized_slug -> original_url_path
for filename in member_files:
    with open(os.path.join(data_dir, filename), 'r') as f:
        data = json.load(f)
        for url in data['members']:
            if '/leden/' in url and 'logo' not in url.lower():
                parts = url.split('/leden/')
                if len(parts) > 1:
                    original_path = parts[1].strip('/').strip()
                    if not original_path.startswith('wp-content'):
                        normalized = slugify(original_path)
                        if normalized not in slug_to_original:
                            slug_to_original[normalized] = original_path

print(f"✓ Built URL mapping for {len(slug_to_original)} companies")

# Build batches: list of dicts with date range + company lists
departed_batches = []
joined_batches = []

for flow in flows:
    from_date = flow['from_date'].split()[0]
    to_date = flow['to_date'].split()[0]

    left_members = flow.get('left_members', [])
    joined_members = flow.get('joined_members', [])

    if left_members:
        departed_batches.append({
            'from_date': from_date,
            'to_date': to_date,
            'companies': sorted(left_members)
        })

    if joined_members:
        joined_batches.append({
            'from_date': from_date,
            'to_date': to_date,
            'companies': sorted(joined_members)
        })

total_departed = sum(len(b['companies']) for b in departed_batches)
total_joined = sum(len(b['companies']) for b in joined_batches)

print(f"Creating gallery for {total_departed} departed companies in {len(departed_batches)} batches...")
print(f"Creating gallery for {total_joined} joined companies in {len(joined_batches)} batches...")

# Create function to generate company HTML card with logo
def create_company_card(company_slug):
    """Generate HTML card for a company with its logo and link"""
    company_name = company_slug.replace('-', ' ').title()
    logo_url = all_logos.get(company_slug)
    # Use original URL path (with b-v etc.) instead of normalized slug
    original_path = slug_to_original.get(company_slug, company_slug)
    nldigital_url = f'https://www.nldigital.nl/leden/{original_path}/'

    # Card HTML with logo or fallback
    html = f'''    <div class="company-card">
        <a href="{nldigital_url}" title="Ga naar {company_name} op NLDigital.nl" class="company-link">
            <div class="logo-container">
'''

    if logo_url:
        html += f'                <img src="{logo_url}" alt="{company_name}" class="company-logo">\n'

    html += f'''            </div>
            <div class="company-name">{company_name}</div>
        </a>
    </div>
'''
    return html

def generate_batch_sections(batches, header_gradient):
    """Generate HTML for batch sections with company cards."""
    sections_html = ''
    for batch in batches:
        batch_cards = ''.join(create_company_card(slug) for slug in batch['companies'])
        sections_html += f'''
        <div class="batch-section">
            <div class="batch-header" style="background: linear-gradient(135deg, {header_gradient});">
                <div class="batch-dates">{batch['from_date']} &rarr; {batch['to_date']}</div>
                <div class="batch-count-badge">{len(batch['companies'])} bedrijven</div>
            </div>
            <div class="batch-gallery">
{batch_cards}            </div>
        </div>
'''
    return sections_html

# Common CSS for both pages
COMMON_CSS = '''        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                'Ubuntu', 'Cantarell', 'Droid Sans', 'Helvetica Neue', sans-serif;
            min-height: 100vh;
            padding: 40px 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        h1 {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .stats {
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.1em;
        }

        .batch-section {
            margin-bottom: 40px;
        }

        .batch-header {
            color: white;
            padding: 20px 25px;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .batch-dates {
            font-size: 1.3em;
            font-weight: bold;
        }

        .batch-count-badge {
            background: rgba(255,255,255,0.3);
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 1.1em;
        }

        .batch-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 25px;
            padding: 25px;
            background: rgba(255,255,255,0.1);
            border-radius: 0 0 12px 12px;
        }

        .company-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
        }

        .company-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
        }

        .company-link {
            text-decoration: none;
            color: inherit;
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        .logo-container {
            background: #f5f5f5;
            height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            border-bottom: 1px solid #eee;
        }

        .company-logo {
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
        }

        .company-name {
            padding: 15px;
            font-weight: 600;
            color: #333;
            text-align: center;
            flex-grow: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.95em;
            transition: color 0.3s ease;
        }

        .back-link {
            color: white;
            text-align: center;
            margin-top: 30px;
            font-size: 1em;
        }

        .back-link a {
            color: white;
            text-decoration: underline;
            transition: opacity 0.3s ease;
        }

        .back-link a:hover {
            opacity: 0.8;
        }'''

# Generate departed page
departed_batches_html = generate_batch_sections(departed_batches, '#d32f2f 0%, #b71c1c 100%')

departed_html = f'''<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vertrokken Bedrijven</title>
    <style>
{COMMON_CSS}

        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}

        .company-card:hover .company-name {{
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Vertrokken Bedrijven</h1>
        <div class="stats">{total_departed} bedrijven hebben NLdigital verlaten</div>

{departed_batches_html}

        <div class="back-link">
            <a href="index.html">&larr; Terug naar Sankey</a> |
            <a href="joined_companies_logos.html">Nieuwe Bedrijven &rarr;</a>
        </div>
    </div>
</body>
</html>
'''

# Generate joined page
joined_batches_html = generate_batch_sections(joined_batches, '#11998e 0%, #38ef7d 100%')

joined_html = f'''<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nieuwe Bedrijven</title>
    <style>
{COMMON_CSS}

        body {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}

        .company-card:hover .company-name {{
            color: #11998e;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Nieuwe Bedrijven</h1>
        <div class="stats">{total_joined} bedrijven zijn toegetreden tot NLdigital</div>

{joined_batches_html}

        <div class="back-link">
            <a href="departed_companies_logos.html">&larr; Vertrokken Bedrijven</a> |
            <a href="index.html">Sankey &rarr;</a>
        </div>
    </div>
</body>
</html>
'''

# Write HTML files
output_dir = '/workspaces/NLdigital'

with open(os.path.join(output_dir, 'departed_companies_logos.html'), 'w', encoding='utf-8') as f:
    f.write(departed_html)

with open(os.path.join(output_dir, 'joined_companies_logos.html'), 'w', encoding='utf-8') as f:
    f.write(joined_html)

print(f"✓ Generated departed_companies_logos.html ({len(departed_batches)} batches)")
print(f"✓ Generated joined_companies_logos.html ({len(joined_batches)} batches)")
for batch in departed_batches:
    print(f"  {batch['from_date']} -> {batch['to_date']}: {len(batch['companies'])} departed")
