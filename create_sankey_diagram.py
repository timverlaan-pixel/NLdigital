#!/usr/bin/env python3
"""
Create interactive Sankey diagram for NLdigital member flows
"""

import json
import os
import pandas as pd
from datetime import datetime

# Install plotly if needed
try:
    import plotly.graph_objects as go
except ImportError:
    print("Installing plotly...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'plotly', '-q'])
    import plotly.graph_objects as go

# Load Sankey data
data_dir = '/workspaces/NLdigital/member_data'
sankey_file = os.path.join(data_dir, 'sankey_data.json')

with open(sankey_file, 'r', encoding='utf-8') as f:
    sankey_data = json.load(f)

print("Creating Sankey diagram...")

# Convert to dataframe for easier processing
df = pd.DataFrame(sankey_data)

# Get all unique nodes
all_sources = df['source'].unique().tolist()
all_targets = df['target'].unique().tolist()
all_nodes = sorted(list(set(all_sources + all_targets)))

print(f"Total nodes: {len(all_nodes)}")
print(f"Nodes: {all_nodes}")

# Create mapping of node names to indices
node_indices = {node: i for i, node in enumerate(all_nodes)}

# Prepare source, target, and value arrays
source_indices = [node_indices[s] for s in df['source']]
target_indices = [node_indices[t] for t in df['target']]
values = df['value'].tolist()
labels = df['label'].tolist()

# Create color mapping
colors = []
for label in labels:
    if label == 'Stayed':
        colors.append('rgba(100, 150, 200, 0.5)')  # Blue
    elif label == 'Joined':
        colors.append('rgba(100, 200, 100, 0.5)')  # Green
    elif label == 'Left':
        colors.append('rgba(200, 100, 100, 0.5)')  # Red
    else:
        colors.append('rgba(150, 150, 150, 0.5)')  # Gray

# Create Sankey diagram
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color='black', width=0.5),
        label=all_nodes,
        color=['rgba(100, 150, 200, 1)' if 'New' in n or 'Left' not in n and '-' in n else 
               'rgba(100, 200, 100, 1)' if 'New' in n else
               'rgba(200, 100, 100, 1)' if 'Left' in n else
               'rgba(150, 150, 150, 1)' for n in all_nodes]
    ),
    link=dict(
        source=source_indices,
        target=target_indices,
        value=values,
        color=colors,
        label=labels
    )
)])

fig.update_layout(
    title_text="NLdigital Member Flows (2024-2026)",
    font=dict(size=10),
    height=800,
    width=1400,
    template='plotly_white'
)

# Save HTML
output_file = os.path.join(data_dir, 'sankey_diagram.html')
fig.write_html(output_file)
print(f"✓ Sankey diagram saved to {output_file}")

# Also try to save as PNG (requires kaleido)
try:
    png_file = os.path.join(data_dir, 'sankey_diagram.png')
    fig.write_image(png_file)
    print(f"✓ PNG saved to {png_file}")
except Exception as e:
    print(f"Note: PNG export not available ({str(e)})")

# Create a summary statistics
print("\n" + "="*60)
print("Summary Statistics")
print("="*60)

# Analyze total flows
total_joined = df[df['label'] == 'Joined']['value'].sum()
total_left = df[df['label'] == 'Left']['value'].sum()
total_stayed = df[df['label'] == 'Stayed']['value'].sum()

print(f"\nTotal member movements across all periods:")
print(f"  Total joined: {total_joined}")
print(f"  Total left:   {total_left}")
print(f"  Total stayed: {total_stayed}")

print(f"\nMembership retention rate: {total_stayed / (total_stayed + total_left):.1%}")
print(f"Churn flows per transition: {(total_left / len(df[df['label'] == 'Left'])):.0f} average")

print("\n" + "="*60)
print("Sankey diagram ready for viewing!")
print("Open sankey_diagram.html in a browser to see the interactive visualization.")
print("="*60)
