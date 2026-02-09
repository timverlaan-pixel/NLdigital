#!/usr/bin/env python3
"""
Create pages listing companies that left/joined, grouped by departure batch.
"""

import json
import os
import re

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

data_dir = '/workspaces/NLdigital/member_data'

with open(os.path.join(data_dir, 'member_flows.json'), 'r') as f:
    flows = json.load(f)

# Build mapping: normalized slug -> original URL path (for correct NLdigital links)
member_files = sorted([f for f in os.listdir(data_dir) if f.startswith('members_') and f.endswith('.json')])
slug_to_original = {}
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

print(f"Built URL mapping for {len(slug_to_original)} companies")

# Build batches
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


def format_name(slug):
    return slug.replace('-', ' ').title()


def generate_batch_sections(batches, header_gradient, hover_color):
    html = ''
    for batch in batches:
        items = ''
        for idx, slug in enumerate(batch['companies']):
            original_path = slug_to_original.get(slug, slug)
            url = f'https://www.nldigital.nl/leden/{original_path}/'
            name = format_name(slug)
            items += f'''            <div class="company-item">
                <div class="company-num">{idx + 1}</div>
                <div class="company-name">{name}</div>
                <a href="{url}" target="_blank" class="company-link" style="--hover-bg: {hover_color};">Bezoeken</a>
            </div>
'''
        html += f'''
        <div class="batch-section">
            <div class="batch-header" style="background: linear-gradient(135deg, {header_gradient});">
                <div class="batch-dates">{batch['from_date']} &rarr; {batch['to_date']}</div>
                <div class="badge">{len(batch['companies'])} bedrijven</div>
            </div>
            <div class="company-list">
{items}            </div>
        </div>
'''
    return html


COMMON_CSS = '''        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            color: white; text-align: center; margin-bottom: 10px;
            font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .stats {
            color: rgba(255,255,255,0.9); text-align: center;
            margin-bottom: 30px; font-size: 1.1em;
        }
        .batch-section {
            background: white; border-radius: 12px; overflow: hidden;
            margin-bottom: 30px; box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }
        .batch-header {
            color: white; padding: 20px 25px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .batch-dates { font-size: 1.3em; font-weight: bold; }
        .badge {
            background: rgba(255,255,255,0.3); padding: 8px 16px;
            border-radius: 20px; font-weight: bold; font-size: 1.1em;
        }
        .company-list { padding: 10px 20px; }
        .company-item {
            display: flex; align-items: center; padding: 10px 5px;
            border-bottom: 1px solid #eee; transition: background 0.2s;
        }
        .company-item:last-child { border-bottom: none; }
        .company-item:hover { background: #f8f9fa; }
        .company-num {
            width: 30px; height: 30px; border-radius: 50%;
            background: #e8e8e8; display: flex; align-items: center;
            justify-content: center; font-size: 0.8em; color: #666;
            margin-right: 12px; flex-shrink: 0;
        }
        .company-name { flex: 1; font-weight: 500; color: #333; }
        .company-link {
            padding: 6px 14px; background: #f0f0f0; border-radius: 6px;
            text-decoration: none; color: #667eea; font-size: 0.85em;
            font-weight: 500; transition: all 0.3s;
        }
        .company-link:hover { background: var(--hover-bg, #667eea); color: white; }
        .back-link {
            color: white; text-align: center; margin-top: 30px; font-size: 1em;
        }
        .back-link a {
            color: white; text-decoration: underline; margin: 0 10px;
            transition: opacity 0.3s;
        }
        .back-link a:hover { opacity: 0.8; }'''

departed_sections = generate_batch_sections(departed_batches, '#d32f2f 0%, #b71c1c 100%', '#d32f2f')

departed_html = f'''<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vertrokken Bedrijven</title>
    <style>
{COMMON_CSS}
        body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Vertrokken Bedrijven</h1>
        <div class="stats">{total_departed} bedrijven hebben NLdigital verlaten</div>
{departed_sections}
        <div class="back-link">
            <a href="index.html">&larr; Terug naar Sankey</a> |
            <a href="joined_companies_logos.html">Nieuwe Bedrijven &rarr;</a>
        </div>
    </div>
</body>
</html>
'''

joined_sections = generate_batch_sections(joined_batches, '#11998e 0%, #38ef7d 100%', '#11998e')

joined_html = f'''<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nieuwe Bedrijven</title>
    <style>
{COMMON_CSS}
        body {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Nieuwe Bedrijven</h1>
        <div class="stats">{total_joined} bedrijven zijn toegetreden tot NLdigital</div>
{joined_sections}
        <div class="back-link">
            <a href="departed_companies_logos.html">&larr; Vertrokken Bedrijven</a> |
            <a href="index.html">Sankey &rarr;</a>
        </div>
    </div>
</body>
</html>
'''

output_dir = '/workspaces/NLdigital'
with open(os.path.join(output_dir, 'departed_companies_logos.html'), 'w', encoding='utf-8') as f:
    f.write(departed_html)
with open(os.path.join(output_dir, 'joined_companies_logos.html'), 'w', encoding='utf-8') as f:
    f.write(joined_html)

print(f"Generated departed_companies_logos.html ({len(departed_batches)} batches, {total_departed} companies)")
print(f"Generated joined_companies_logos.html ({len(joined_batches)} batches, {total_joined} companies)")
