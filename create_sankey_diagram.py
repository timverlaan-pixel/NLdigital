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
import json
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
    
    # Create labeled nodes
    from_node = f"{from_date}\n({from_count} leden)"
    to_node = f"{to_date}\n({to_count} leden)"
    
    # Create company list string for hover text (companies that left)
    left_companies = flow.get('left_members', [])
    companies_text = '<b>Companies that left:</b><br>'
    if left_companies:
        # Show first 10 companies + count of remaining
        for company in left_companies[:10]:
            # Normalize display name
            display_name = company.replace('-', ' ').replace('bv', 'BV')
            companies_text += f"• {display_name}<br>"
        if len(left_companies) > 10:
            companies_text += f"... and {len(left_companies) - 10} more<br>"
    else:
        companies_text += "No data"
    
    # Add stayed flow (use integer values)
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


# Helper to create compact display labels for nodes (repositioned by JS post-render)
def display_label_for_node(n: str) -> str:
    parts = n.split('\n')
    if len(parts) >= 2 and re.match(r'^\d{4}-\d{2}-\d{2}$', parts[0]):
        return parts[0] + ' ' + ' '.join(parts[1:])
    return n

# Create mapping of node names to indices
node_indices = {node: i for i, node in enumerate(all_nodes)}

# Prepare source, target, and value arrays
source_indices = [node_indices[s] for s in df['source']]
target_indices = [node_indices[t] for t in df['target']]
# Ensure values are integers (no .0) and labels reflect integer values
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

# Create color mapping with better visibility
colors = []
for label in labels:
    if 'Gebleven' in label:
        colors.append('rgba(100, 150, 200, 0.6)')  # Blue
    elif 'Toegetreden' in label:
        colors.append('rgba(100, 200, 100, 0.6)')  # Green
    elif 'Vertrokken' in label:
        colors.append('rgba(200, 100, 100, 0.6)')  # Red
    else:
        colors.append('rgba(150, 150, 150, 0.5)')

# Node colors
node_colors = []
for n in all_nodes:
    if 'Toegetreden' in n:
        node_colors.append('rgba(100, 200, 100, 1)')
    elif 'Vertrokken' in n:
        node_colors.append('rgba(200, 100, 100, 1)')
    else:
        node_colors.append('rgba(100, 150, 200, 1)')

# Create Sankey diagram
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=20,
        thickness=80,
        line=dict(color='black', width=0.5),
        # display vertical labels for date boxes, keep internal ids in all_nodes
        label=[display_label_for_node(n) for n in all_nodes],
        color=node_colors
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
    title_text="NLdigital Ledenstromen - Gefiltreerde Batches<br>(Alleen batches met vertrekken)",
    font=dict(size=11),
    height=900,
    width=1400,
    template='plotly_white',
    hovermode='closest'
)

# Save HTML
output_file = os.path.join(data_dir, '..', 'sankey_diagram_filtered.html')
fig.write_html(output_file)

# Post-process: inject JS to reposition node labels inside node boundaries
# and add visible numbers on link paths
CUSTOM_JS = r"""
<script>
(function() {
    function repositionNodeLabels() {
        var nodes = document.querySelectorAll('.sankey-node');
        nodes.forEach(function(node) {
            var rect = node.querySelector('rect');
            var textEl = node.querySelector('text');
            if (!rect || !textEl) return;

            var rectX = parseFloat(rect.getAttribute('x'));
            var rectY = parseFloat(rect.getAttribute('y'));
            var rectW = parseFloat(rect.getAttribute('width'));
            var rectH = parseFloat(rect.getAttribute('height'));

            var centerX = rectX + rectW / 2;
            var centerY = rectY + rectH / 2;

            // Position text at center of rectangle, rotated vertically
            textEl.setAttribute('x', centerX);
            textEl.setAttribute('y', centerY);
            textEl.setAttribute('text-anchor', 'middle');
            textEl.setAttribute('dominant-baseline', 'central');
            textEl.setAttribute('transform',
                'rotate(-90, ' + centerX + ', ' + centerY + ')');
            textEl.style.fontSize = '11px';
            textEl.style.fill = 'white';
            textEl.style.fontWeight = 'bold';
            textEl.style.paintOrder = 'stroke';
            textEl.style.stroke = 'rgba(0,0,0,0.3)';
            textEl.style.strokeWidth = '2px';
            textEl.style.strokeLinejoin = 'round';
        });
    }

    function addLinkLabels() {
        // Remove any previously added link labels
        document.querySelectorAll('.custom-link-label').forEach(function(el) {
            el.remove();
        });

        var plotDiv = document.querySelector('.plotly-graph-div');
        if (!plotDiv || !plotDiv.data || !plotDiv.data[0] || !plotDiv.data[0].link) return;
        var linkData = plotDiv.data[0].link;
        var labels = linkData.label;
        var values = linkData.value;

        var links = document.querySelectorAll('.sankey-link');
        links.forEach(function(linkGroup, index) {
            if (index >= labels.length) return;

            var path = linkGroup.querySelector('path');
            if (!path) return;

            var label = labels[index];
            var match = label.match(/:\s*(\d+)/);
            if (!match) return;
            var number = match[1];
            var value = values[index];

            // Skip very small links where text won't fit
            if (value < 5) return;

            var pathLength = path.getTotalLength();
            var midPoint = path.getPointAtLength(pathLength / 2);

            // Determine color based on link type
            var textColor = '#333';
            if (label.indexOf('Vertrokken') >= 0) textColor = '#b71c1c';
            else if (label.indexOf('Toegetreden') >= 0) textColor = '#1b5e20';
            else if (label.indexOf('Gebleven') >= 0) textColor = '#1a237e';

            var svgNS = 'http://www.w3.org/2000/svg';
            var text = document.createElementNS(svgNS, 'text');
            text.setAttribute('x', midPoint.x);
            text.setAttribute('y', midPoint.y);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'central');
            text.setAttribute('class', 'custom-link-label');
            text.style.fontSize = value > 50 ? '12px' : '9px';
            text.style.fontWeight = 'bold';
            text.style.fill = textColor;
            text.style.pointerEvents = 'none';
            text.style.paintOrder = 'stroke';
            text.style.stroke = 'white';
            text.style.strokeWidth = '3px';
            text.style.strokeLinejoin = 'round';
            text.textContent = number;

            // Add to the SVG layer above the link paths
            var svg = path.closest('svg');
            if (svg) svg.appendChild(text);
        });
    }

    function customizeSankey() {
        repositionNodeLabels();
        addLinkLabels();
    }

    // Wait for Plotly to finish rendering
    var observer = new MutationObserver(function(mutations, obs) {
        if (document.querySelectorAll('.sankey-node').length > 0) {
            obs.disconnect();
            setTimeout(customizeSankey, 200);
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Re-apply after Plotly re-renders (e.g. node drag)
    setTimeout(function() {
        var plotDiv = document.querySelector('.plotly-graph-div');
        if (plotDiv && plotDiv.on) {
            plotDiv.on('plotly_afterplot', function() {
                setTimeout(customizeSankey, 100);
            });
        }
    }, 500);
})();
</script>
"""

with open(output_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

html_content = html_content.replace('</body>', CUSTOM_JS + '\n</body>')

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✓ Sankey diagram saved to {output_file}")

# Print summary
print("\n" + "="*70)
print("SAMENVATTING - GEFILTERDE BATCHES (alleen met vertrekken)")
print("="*70)
for flow in active_flows:
    from_date = flow['from_date'].split()[0]
    to_date = flow['to_date'].split()[0]
    from_count = member_counts.get(flow['from_date'], '?')
    to_count = member_counts.get(flow['to_date'], '?')
    
    print(f"\n{from_date} ({from_count} leden) → {to_date} ({to_count} leden)")
    print(f"  Gebleven:    {flow['stayed']}")
    print(f"  Toegetreden: {flow['joined']}")
    print(f"  Vertrokken:  {flow['left']} ⚠️")
    print(f"  Netto:       {flow['joined'] - flow['left']:+d}")

print("\n" + "="*70)

