#!/usr/bin/env python3
"""
Create a visual gallery of company logos that left in each batch
"""

import json
import os
from datetime import datetime
import re

# Load member flows and snapshots
data_dir = '/workspaces/NLdigital/member_data'

with open(os.path.join(data_dir, 'member_flows.json'), 'r') as f:
    flows = json.load(f)

# Load all member snapshots to find logo URLs
member_files = sorted([f for f in os.listdir(data_dir) if f.startswith('members_') and f.endswith('.json')])

snapshots_by_date = {}
for filename in member_files:
    with open(os.path.join(data_dir, filename), 'r') as f:
        data = json.load(f)
        date = data['date'].split()[0]  # Just the date part
        # Extract company name -> logo URL mapping
        logo_urls = [u for u in data['members'] if 'logo' in u.lower()]
        member_urls = [u for u in data['members'] if '/leden/' in u and 'logo' not in u.lower()]
        
        # Create mapping (normalize keys so they match company slugs)
        logos_by_company = {}
        for logo_url in logo_urls:
            # Extract company name from logo URL
            # Format: logo-company-name.jpg
            logo_filename = logo_url.split('/')[-1]  # Get filename
            # Use same slugification as other scripts
            # remove extension and leading 'logo-' inside slugify
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

            key = slugify(logo_filename)
            logos_by_company[key] = logo_url

        snapshots_by_date[data['date']] = {
            'members': data['members'],
            'logos_by_company': logos_by_company,
            'logo_urls': set(logo_urls)
        }

# Build HTML
html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NLdigital - Companies That Left (Visual)</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        h1 {
            color: #d32f2f;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 20px;
        }
        
        .batch {
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        .batch-title {
            background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%);
            color: white;
            padding: 15px;
            border-radius: 6px;
            margin: -25px -25px 20px -25px;
            font-size: 1.3em;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .batch-count {
            background: rgba(255, 255, 255, 0.3);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .logo-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 15px;
            padding: 20px 0;
        }
        
        .logo-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            transition: all 0.3s;
            border: 2px solid transparent;
            cursor: pointer;
        }
        
        .logo-item:hover {
            border-color: #d32f2f;
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(211, 47, 47, 0.2);
        }
        
        .logo-item img {
            max-width: 100%;
            height: 80px;
            object-fit: contain;
            margin-bottom: 8px;
        }
        
        .logo-item-name {
            font-size: 0.75em;
            color: #666;
            word-break: break-word;
            height: 2.5em;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .no-logos {
            color: #999;
            font-style: italic;
            padding: 20px;
            text-align: center;
            background: #f8f9fa;
            border-radius: 6px;
        }
        
        footer {
            background: white;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 0.9em;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        @media (max-width: 768px) {
            header {
                padding: 15px;
            }
            
            .batch {
                padding: 15px;
            }
            
            .batch-title {
                margin: -15px -15px 15px -15px;
                flex-direction: column;
                gap: 10px;
            }
            
            .logo-gallery {
                grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎨 NLdigital Member Departures - Visual Gallery</h1>
            <p class="subtitle">Company logos that left in each batch (Aug 2025 - Feb 2026)</p>
            <p style="color: #999; font-size: 0.9em;">Hover over logos to see details</p>
        </header>
        
        <div id="batches"></div>
        
        <footer>
            <p>Logos sourced from NLdigital member directory</p>
        </footer>
    </div>
    
    <script>
        const flows = %FLOWS_JSON%;
        const snapshots = %SNAPSHOTS_JSON%;
        
        function renderBatches() {
            const batchesContainer = document.getElementById('batches');
            
            flows.forEach((flow, index) => {
                const fromDate = flow.from_date.split(' ')[0];
                const toDate = flow.to_date.split(' ')[0];
                const leftMembers = flow.left_members;
                
                const batchDiv = document.createElement('div');
                batchDiv.className = 'batch';
                
                // Find the snapshot that has the logos
                const snapshotDate = flow.from_date;
                const snapshot = Object.values(snapshots).find(s => s.date === snapshotDate);
                
                let logoGalleryHtml = '<div class="logo-gallery">';
                
                if (leftMembers.length > 0 && snapshot) {
                    leftMembers.forEach(company => {
                        // Try to find logo URL
                        const logoUrl = snapshot.logos_by_company[company];
                        
                        if (logoUrl) {
                            // Format company name: replace hyphens with spaces, normalize "b v" to "bv"
                            let companyDisplay = company
                                .replace(/-/g, ' ')
                                .replace(/b v/g, 'BV')
                                .replace(/b-v/g, 'BV')
                                .replace(/([a-z])([A-Z])/g, '$1 $2');
                            
                            logoGalleryHtml += `
                                <div class="logo-item" title="${companyDisplay}">
                                    <img src="${logoUrl}" alt="${companyDisplay}" onerror="this.style.display='none'">
                                    <div class="logo-item-name">${companyDisplay}</div>
                                </div>
                            `;
                        }
                    });
                } else {
                    logoGalleryHtml = '<div class="no-logos">No logos available for this batch</div>';
                }
                
                logoGalleryHtml += '</div>';
                
                batchDiv.innerHTML = `
                    <div class="batch-title">
                        <span>${fromDate} → ${toDate}</span>
                        <span class="batch-count">${leftMembers.length} companies left</span>
                    </div>
                    ${logoGalleryHtml}
                `;
                
                batchesContainer.appendChild(batchDiv);
            });
        }
        
        renderBatches();
    </script>
</body>
</html>
'''

# Create snapshot lookup for the template
snapshots_data = {}
for date, snapshot_info in snapshots_by_date.items():
    logos_mapping = {}
    for company, logo_url in snapshot_info['logos_by_company'].items():
        logos_mapping[company] = logo_url
    
    snapshots_data[date] = {
        'date': date,
        'logos_by_company': logos_mapping
    }

# Replace placeholders
html_final = html_content.replace(
    '%FLOWS_JSON%',
    json.dumps(flows)
).replace(
    '%SNAPSHOTS_JSON%',
    json.dumps(snapshots_data)
)

# Write output
# Write departed companies page
output_file_departed = os.path.join(data_dir, '..', 'departed_companies_logos.html')
with open(output_file_departed, 'w', encoding='utf-8') as f:
    f.write(html_final)

print(f"✓ Departed logo gallery created: {output_file_departed}")
print(f"\nBatch Summary (departures):")
for i, flow in enumerate(flows, 1):
    print(f"{i}. {flow['from_date'].split()[0]} → {flow['to_date'].split()[0]}: {flow['left']} companies left")

# Create joined companies page by adapting the template JS to use joined_members
html_joined = html_content.replace('%FLOWS_JSON%', json.dumps(flows)).replace('%SNAPSHOTS_JSON%', json.dumps(snapshots_data))
html_joined = html_joined.replace("const flows = %FLOWS_JSON%;", "const flows = %FLOWS_JSON%;\n        const mode = 'joined';")
# Replace rendering logic: use joined_members and snapshot for to_date
html_joined = html_joined.replace("const snapshotDate = flow.from_date;", "const snapshotDate = flow.to_date;")
html_joined = html_joined.replace("const leftMembers = flow.left_members;", "const leftMembers = flow.joined_members;")
html_joined = html_joined.replace("${leftMembers.length} companies left", "${leftMembers.length} companies joined")

output_file_joined = os.path.join(data_dir, '..', 'joined_companies_logos.html')
with open(output_file_joined, 'w', encoding='utf-8') as f:
    f.write(html_joined)

print(f"✓ Joined logo gallery created: {output_file_joined}")
