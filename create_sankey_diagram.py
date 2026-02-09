#!/usr/bin/env python3
"""
Create interactive Sankey diagram for NLdigital member flows
Shows member inflow/outflow with clear labels and filtered batches
"""

import json
import os
import pandas as pd
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

def extract_company_from_url(url: str) -> str:
    u = (url or '').strip()
    if '/leden/' in u and not u.lower().endswith(('.jpg', '.png', '.jpeg', '.gif')):
        parts = u.split('/leden/')
        if len(parts) > 1:
            candidate = parts[1].strip('/').strip()
            if not candidate.startswith('wp-content'):
                return slugify(candidate)
    return None

# Install plotly if needed
try:
    import plotly.graph_objects as go
except ImportError:
    print("Installing plotly...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'plotly', '-q'])
    import plotly.graph_objects as go

# Load Sankey data and flow analysis
data_dir = '/workspaces/NLdigital/member_data'
flow_file = os.path.join(data_dir, 'member_flows.json')

with open(flow_file, 'r') as f:
    flows = json.load(f)

print("Creating enhanced Sankey diagram...")
print("\nFiltering out batches with 0 departures...")

# Filter out batches where no one left
active_flows = [f for f in flows if f['left'] > 0]
print(f"Original batches: {len(flows)}")
print(f"Active batches (with departures): {len(active_flows)}")

# Build the Sankey data
sankey_entries = []

# Load the original member snapshots for count information
member_files = sorted([f for f in os.listdir(data_dir) if f.startswith('members_') and f.endswith('.json')])
member_counts = {}
for filename in member_files:
    with open(os.path.join(data_dir, filename), 'r') as f:
        data = json.load(f)
        # compute deduplicated member slugs from snapshot URLs
        company_slugs = set()
        for url in data.get('members', []):
            slug = extract_company_from_url(url)
            if slug:
                company_slugs.add(slug)
        # store deduplicated count keyed by full datetime string (matches flows)
        member_counts[data['date']] = len(company_slugs)

# Process each active flow
for i, flow in enumerate(active_flows):
    from_date = flow['from_date'].split()[0]  # Just date part
    to_date = flow['to_date'].split()[0]

    # Ensure member counts are integers (no trailing .0)
    from_count_raw = member_counts.get(flow['from_date'], '?')
    to_count_raw = member_counts.get(flow['to_date'], '?')
    try:
        from_count = int(round(float(from_count_raw)))
    except Exception:
        from_count = from_count_raw
    try:
        to_count = int(round(float(to_count_raw)))
    except Exception:
        to_count = to_count_raw

    # Create labeled nodes - use \n for multiline
    from_node = f"{from_date}\n({from_count} leden)"
    to_node = f"{to_date}\n({to_count} leden)"

    # Create company list string for hover text (companies that left)
    left_companies = flow.get('left_members', [])
    companies_text = '<b>Companies that left:</b><br>'
    if left_companies:
        for company in left_companies[:10]:
            display_name = company.replace('-', ' ').replace('bv', 'BV')
            companies_text += f"• {display_name}<br>"
        if len(left_companies) > 10:
            companies_text += f"... and {len(left_companies) - 10} more<br>"
    else:
        companies_text += "No data"

    # Add stayed flow
    if flow.get('stayed', 0) > 0:
        stayed_val = int(round(float(flow.get('stayed', 0))))
        sankey_entries.append({
            'source': from_node,
            'target': to_node,
            'value': stayed_val,
            'label': f"Gebleven: {stayed_val}",
            'type': 'stayed'
        })

    # Add joined flow (from "New")
    if flow.get('joined', 0) > 0:
        joined_val = int(round(float(flow.get('joined', 0))))
        sankey_entries.append({
            'source': 'Nieuw / Toegetreden',
            'target': to_node,
            'value': joined_val,
            'label': f"Toegetreden: {joined_val}",
            'type': 'joined'
        })

    # Add left flow (to "Gone")
    if flow.get('left', 0) > 0:
        left_val = int(round(float(flow.get('left', 0))))
        sankey_entries.append({
            'source': from_node,
            'target': 'Vertrokken',
            'value': left_val,
            'label': f"Vertrokken: {left_val}",
            'type': 'left',
            'hover_companies': companies_text
        })

print(f"Total flow entries: {len(sankey_entries)}")

# Convert to dataframe
df = pd.DataFrame(sankey_entries)

# Get all unique nodes
all_sources = df['source'].unique().tolist()
all_targets = df['target'].unique().tolist()
all_nodes = sorted(list(set(all_sources + all_targets)))

print(f"Total nodes: {len(all_nodes)}")

# Create mapping of node names to indices
node_indices = {node: i for i, node in enumerate(all_nodes)}

# Prepare source, target, and value arrays
source_indices = [node_indices[s] for s in df['source']]
target_indices = [node_indices[t] for t in df['target']]
df['value'] = df['value'].astype(int)
values = df['value'].tolist()
labels = df['label'].astype(str).tolist()

# Prepare custom hover text with company information
hover_texts = []
for idx, row in df.iterrows():
    if 'hover_companies' in row and row['hover_companies']:
        hover_text = f"{row['label']}<br>{row['hover_companies']}"
    else:
        hover_text = row['label']
    hover_texts.append(hover_text)

# Link colors
colors = []
for label in labels:
    if 'Gebleven' in label:
        colors.append('rgba(100, 150, 200, 0.6)')
    elif 'Toegetreden' in label:
        colors.append('rgba(100, 200, 100, 0.6)')
    elif 'Vertrokken' in label:
        colors.append('rgba(200, 100, 100, 0.6)')
    else:
        colors.append('rgba(150, 150, 150, 0.5)')

# -- Manual node positioning: ALL date nodes in a single horizontal row --
date_nodes = sorted([n for n in all_nodes if re.match(r'^\d{4}-\d{2}-\d{2}', n)])
special_nodes = [n for n in all_nodes if n not in date_nodes]

# Build ordered list: Nieuw, then date nodes, then Vertrokken — all in one row
num_date = len(date_nodes)
total_cols = num_date + 2  # +2 for Nieuw and Vertrokken
node_x = []
node_y = []
node_colors = []
node_labels = []

for n in all_nodes:
    if n in date_nodes:
        idx = date_nodes.index(n)
        # Date nodes occupy columns 1..num_date (0-indexed), leaving col 0 for Nieuw, last for Vertrokken
        col = idx + 1
        x = 0.01 + (col / (total_cols - 1)) * 0.98
        node_x.append(x)
        node_y.append(0.5)
        node_colors.append('rgba(100, 150, 200, 1)')
        node_labels.append(n)
    elif 'Toegetreden' in n:
        node_x.append(0.01)
        node_y.append(0.5)  # Same row as date nodes
        node_colors.append('rgba(100, 200, 100, 1)')
        node_labels.append(n)
    elif 'Vertrokken' in n:
        node_x.append(0.99)
        node_y.append(0.5)  # Same row as date nodes
        node_colors.append('rgba(200, 100, 100, 1)')
        node_labels.append(n)
    else:
        node_x.append(0.5)
        node_y.append(0.5)
        node_colors.append('rgba(150, 150, 150, 1)')
        node_labels.append(n)

# Use arrangement='fixed' so Plotly respects our exact x/y positions
fig = go.Figure(data=[go.Sankey(
    arrangement='fixed',
    node=dict(
        pad=8,
        thickness=35,
        line=dict(color='black', width=0.5),
        label=node_labels,
        color=node_colors,
        x=node_x,
        y=node_y
    ),
    link=dict(
        source=source_indices,
        target=target_indices,
        value=values,
        color=colors,
        label=labels,
        customdata=hover_texts,
        hovertemplate='%{customdata}<br><b>Aantal:</b> %{value}<extra></extra>'
    )
)])

fig.update_layout(
    title_text="NLdigital Ledenstromen (Alleen batches met vertrekken)",
    font=dict(size=9),
    height=450,
    width=1200,
    template='plotly_white',
    hovermode='closest',
    margin=dict(l=5, r=5, t=35, b=5)
)

# Save HTML
output_file = os.path.join(data_dir, '..', 'sankey_diagram_filtered.html')
fig.write_html(output_file, config={'responsive': True})

# Post-process: inject JS to rotate node labels 90 degrees and add link numbers
CUSTOM_JS = r"""
<script>
(function() {
    function repositionNodeLabels() {
        // Plotly Sankey renders nodes as <g> with child <rect> + <text>.
        // The <text> may have <tspan> children for multi-line labels.
        var allGroups = document.querySelectorAll('g');
        allGroups.forEach(function(g) {
            var rect = g.querySelector(':scope > rect');
            var textEl = g.querySelector(':scope > text');
            if (!rect || !textEl) return;

            var rectW = parseFloat(rect.getAttribute('width'));
            var rectH = parseFloat(rect.getAttribute('height'));
            // Only Sankey node rects (skip tiny ones)
            if (!rectW || !rectH || rectW < 15 || rectH < 20) return;

            var rectX = parseFloat(rect.getAttribute('x')) || 0;
            var rectY = parseFloat(rect.getAttribute('y')) || 0;
            var centerX = rectX + rectW / 2;
            var centerY = rectY + rectH / 2;

            // Remove all tspan children and flatten to single text
            var tspans = textEl.querySelectorAll('tspan');
            var fullText = '';
            if (tspans.length > 0) {
                tspans.forEach(function(ts) {
                    if (fullText) fullText += ' ';
                    fullText += ts.textContent;
                });
                // Remove tspans
                while (textEl.firstChild) textEl.removeChild(textEl.firstChild);
                textEl.textContent = fullText;
            }

            // Position at center, rotated -90 degrees (vertical, reading bottom-to-top)
            textEl.setAttribute('x', centerX);
            textEl.setAttribute('y', centerY);
            textEl.setAttribute('text-anchor', 'middle');
            textEl.setAttribute('dominant-baseline', 'central');
            textEl.setAttribute('transform',
                'rotate(-90, ' + centerX + ', ' + centerY + ')');
            textEl.style.fontSize = '9px';
            textEl.style.fill = 'white';
            textEl.style.fontWeight = 'bold';
            textEl.style.paintOrder = 'stroke';
            textEl.style.stroke = 'rgba(0,0,0,0.4)';
            textEl.style.strokeWidth = '2.5px';
            textEl.style.strokeLinejoin = 'round';
        });
    }

    function addLinkLabels() {
        document.querySelectorAll('.custom-link-label').forEach(function(el) { el.remove(); });
        var plotDiv = document.querySelector('.plotly-graph-div');
        if (!plotDiv || !plotDiv.data || !plotDiv.data[0] || !plotDiv.data[0].link) return;
        var linkData = plotDiv.data[0].link;
        var labels = linkData.label;
        var values = linkData.value;
        var svg = plotDiv.querySelector('svg.main-svg');
        if (!svg) return;

        // Collect link paths (Plotly link paths have fill with rgba and opacity)
        var paths = svg.querySelectorAll('path');
        var linkPaths = [];
        paths.forEach(function(p) {
            var fill = p.getAttribute('style') || '';
            if (fill.indexOf('rgba') >= 0 && fill.indexOf('0.6') >= 0) {
                linkPaths.push(p);
            }
        });

        linkPaths.forEach(function(path, index) {
            if (index >= labels.length) return;
            var label = labels[index];
            var match = label.match(/:\s*(\d+)/);
            if (!match) return;
            var number = match[1];
            var value = values[index];
            if (value < 5) return;
            try {
                var len = path.getTotalLength();
                var midPoint = path.getPointAtLength(len / 2);
                var svgNS = 'http://www.w3.org/2000/svg';
                var text = document.createElementNS(svgNS, 'text');
                text.setAttribute('x', midPoint.x);
                text.setAttribute('y', midPoint.y);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('dominant-baseline', 'central');
                text.setAttribute('class', 'custom-link-label');
                var textColor = '#333';
                if (label.indexOf('Vertrokken') >= 0) textColor = '#b71c1c';
                else if (label.indexOf('Toegetreden') >= 0) textColor = '#1b5e20';
                else if (label.indexOf('Gebleven') >= 0) textColor = '#1a237e';
                text.style.fontSize = value > 50 ? '10px' : '8px';
                text.style.fontWeight = 'bold';
                text.style.fill = textColor;
                text.style.pointerEvents = 'none';
                text.style.paintOrder = 'stroke';
                text.style.stroke = 'white';
                text.style.strokeWidth = '3px';
                text.style.strokeLinejoin = 'round';
                text.textContent = number;
                path.parentNode.appendChild(text);
            } catch(e) {}
        });
    }

    function customizeSankey() {
        repositionNodeLabels();
        addLinkLabels();
    }

    // Wait for Plotly to render
    function waitAndCustomize() {
        var rects = document.querySelectorAll('g > rect');
        var found = false;
        rects.forEach(function(r) {
            var w = parseFloat(r.getAttribute('width'));
            var h = parseFloat(r.getAttribute('height'));
            if (w > 15 && h > 20) found = true;
        });
        if (found) {
            setTimeout(customizeSankey, 300);
        } else {
            setTimeout(waitAndCustomize, 200);
        }
    }
    waitAndCustomize();

    // Re-apply after Plotly re-renders (resize, etc.)
    setTimeout(function() {
        var plotDiv = document.querySelector('.plotly-graph-div');
        if (plotDiv && plotDiv.on) {
            plotDiv.on('plotly_afterplot', function() {
                setTimeout(customizeSankey, 150);
            });
        }
    }, 1000);
})();
</script>
"""

with open(output_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

html_content = html_content.replace('</body>', CUSTOM_JS + '\n</body>')

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Sankey diagram saved to {output_file}")

# Print summary
print("\n" + "="*70)
print("SAMENVATTING - GEFILTERDE BATCHES (alleen met vertrekken)")
print("="*70)
for flow in active_flows:
    from_date = flow['from_date'].split()[0]
    to_date = flow['to_date'].split()[0]
    from_count = member_counts.get(flow['from_date'], '?')
    to_count = member_counts.get(flow['to_date'], '?')

    print(f"\n{from_date} ({from_count} leden) -> {to_date} ({to_count} leden)")
    print(f"  Gebleven:    {flow['stayed']}")
    print(f"  Toegetreden: {flow['joined']}")
    print(f"  Vertrokken:  {flow['left']}")
    print(f"  Netto:       {flow['joined'] - flow['left']:+d}")

print("\n" + "="*70)
