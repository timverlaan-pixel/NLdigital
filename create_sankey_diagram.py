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
        date = data['date'].split()[0]
        member_counts[data['date']] = data['member_count']

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


# Helper to create vertical display labels for date nodes
def display_label_for_node(n: str) -> str:
    parts = n.split('\n')
    if len(parts) >= 2 and re.match(r'^\d{4}-\d{2}-\d{2}$', parts[0]):
        date_part = parts[0]
        rest = '\n'.join(parts[1:])
        # Make date vertical (one char per line) and keep rest (counts) on bottom
        vertical_date = '\n'.join(list(date_part))
        return vertical_date + '\n\n' + rest
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

