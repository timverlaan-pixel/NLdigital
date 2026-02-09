#!/usr/bin/env python3
"""
Create interactive Sankey diagram for NLConnect member flows.
"""

import json
import os
import pandas as pd
import re

try:
    import plotly.graph_objects as go
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'plotly', '-q'])
    import plotly.graph_objects as go

data_dir = '/workspaces/NLdigital/nlconnect_data'

with open(os.path.join(data_dir, 'member_flows.json'), 'r') as f:
    flows = json.load(f)

print("Creating NLConnect Sankey diagram...")

# Filter out batches where nothing happened
active_flows = [f for f in flows if f['left'] > 0 or f['joined'] > 0]
print(f"Active batches: {len(active_flows)} of {len(flows)}")

# Build Sankey entries
sankey_entries = []

# Member counts per snapshot
member_files = sorted([f for f in os.listdir(data_dir) if f.startswith('members_') and f.endswith('.json')])
member_counts = {}
for filename in member_files:
    with open(os.path.join(data_dir, filename), 'r') as f:
        data = json.load(f)
        member_counts[data['date']] = data['member_count']

for i, flow in enumerate(active_flows):
    from_date = flow['from_date'].split()[0]
    to_date = flow['to_date'].split()[0]

    from_count = member_counts.get(flow['from_date'], '?')
    to_count = member_counts.get(flow['to_date'], '?')

    from_node = f"{from_date}\n({from_count} leden)"
    to_node = f"{to_date}\n({to_count} leden)"

    left_companies = flow.get('left_members', [])
    companies_text = '<b>Companies that left:</b><br>'
    if left_companies:
        for company in left_companies[:10]:
            companies_text += f"• {company.replace('-', ' ').title()}<br>"
        if len(left_companies) > 10:
            companies_text += f"... and {len(left_companies) - 10} more<br>"

    if flow.get('stayed', 0) > 0:
        sankey_entries.append({
            'source': from_node, 'target': to_node,
            'value': flow['stayed'],
            'label': f"Gebleven: {flow['stayed']}", 'type': 'stayed'
        })

    if flow.get('joined', 0) > 0:
        sankey_entries.append({
            'source': 'Nieuw / Toegetreden', 'target': to_node,
            'value': flow['joined'],
            'label': f"Toegetreden: {flow['joined']}", 'type': 'joined'
        })

    if flow.get('left', 0) > 0:
        sankey_entries.append({
            'source': from_node, 'target': 'Vertrokken',
            'value': flow['left'],
            'label': f"Vertrokken: {flow['left']}", 'type': 'left',
            'hover_companies': companies_text
        })

df = pd.DataFrame(sankey_entries)
all_sources = df['source'].unique().tolist()
all_targets = df['target'].unique().tolist()
all_nodes = sorted(list(set(all_sources + all_targets)))

node_indices = {node: i for i, node in enumerate(all_nodes)}
source_indices = [node_indices[s] for s in df['source']]
target_indices = [node_indices[t] for t in df['target']]
df['value'] = df['value'].astype(int)
values = df['value'].tolist()
labels = df['label'].astype(str).tolist()

hover_texts = []
for idx, row in df.iterrows():
    if 'hover_companies' in row and row['hover_companies']:
        hover_texts.append(f"{row['label']}<br>{row['hover_companies']}")
    else:
        hover_texts.append(row['label'])

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

# Manual positioning: all nodes in one horizontal row
date_nodes = sorted([n for n in all_nodes if re.match(r'^\d{4}-\d{2}-\d{2}', n)])
num_date = len(date_nodes)
total_cols = num_date + 2

node_x, node_y, node_colors, node_labels = [], [], [], []

for n in all_nodes:
    if n in date_nodes:
        idx = date_nodes.index(n)
        col = idx + 1
        x = 0.01 + (col / (total_cols - 1)) * 0.98
        node_x.append(x)
        node_y.append(0.5)
        node_colors.append('rgba(255, 152, 0, 1)')  # Orange for NLConnect
        node_labels.append(n)
    elif 'Toegetreden' in n:
        node_x.append(0.01)
        node_y.append(0.5)
        node_colors.append('rgba(100, 200, 100, 1)')
        node_labels.append(n)
    elif 'Vertrokken' in n:
        node_x.append(0.99)
        node_y.append(0.5)
        node_colors.append('rgba(200, 100, 100, 1)')
        node_labels.append(n)
    else:
        node_x.append(0.5)
        node_y.append(0.5)
        node_colors.append('rgba(150, 150, 150, 1)')
        node_labels.append(n)

fig = go.Figure(data=[go.Sankey(
    arrangement='fixed',
    node=dict(
        pad=8, thickness=35,
        line=dict(color='black', width=0.5),
        label=node_labels, color=node_colors,
        x=node_x, y=node_y
    ),
    link=dict(
        source=source_indices, target=target_indices,
        value=values, color=colors, label=labels,
        customdata=hover_texts,
        hovertemplate='%{customdata}<br><b>Aantal:</b> %{value}<extra></extra>'
    )
)])

fig.update_layout(
    title_text="NLConnect Ledenstromen",
    font=dict(size=9),
    height=400,
    width=1200,
    template='plotly_white',
    hovermode='closest',
    margin=dict(l=5, r=5, t=35, b=5)
)

output_file = '/workspaces/NLdigital/nlconnect_sankey.html'
fig.write_html(output_file, config={'responsive': True})

# Post-process: inject JS for vertical labels and link numbers
CUSTOM_JS = r"""
<script>
(function() {
    function repositionNodeLabels() {
        var allGroups = document.querySelectorAll('g');
        allGroups.forEach(function(g) {
            var rect = g.querySelector(':scope > rect');
            var textEl = g.querySelector(':scope > text');
            if (!rect || !textEl) return;
            var rectW = parseFloat(rect.getAttribute('width'));
            var rectH = parseFloat(rect.getAttribute('height'));
            if (!rectW || !rectH || rectW < 15 || rectH < 20) return;
            var rectX = parseFloat(rect.getAttribute('x')) || 0;
            var rectY = parseFloat(rect.getAttribute('y')) || 0;
            var centerX = rectX + rectW / 2;
            var centerY = rectY + rectH / 2;
            var tspans = textEl.querySelectorAll('tspan');
            var fullText = '';
            if (tspans.length > 0) {
                tspans.forEach(function(ts) {
                    if (fullText) fullText += ' ';
                    fullText += ts.textContent;
                });
                while (textEl.firstChild) textEl.removeChild(textEl.firstChild);
                textEl.textContent = fullText;
            }
            textEl.setAttribute('x', centerX);
            textEl.setAttribute('y', centerY);
            textEl.setAttribute('text-anchor', 'middle');
            textEl.setAttribute('dominant-baseline', 'central');
            textEl.setAttribute('transform', 'rotate(-90, ' + centerX + ', ' + centerY + ')');
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
        var paths = svg.querySelectorAll('path');
        var linkPaths = [];
        paths.forEach(function(p) {
            var fill = p.getAttribute('style') || '';
            if (fill.indexOf('rgba') >= 0 && fill.indexOf('0.6') >= 0) linkPaths.push(p);
        });
        linkPaths.forEach(function(path, index) {
            if (index >= labels.length) return;
            var label = labels[index];
            var match = label.match(/:\s*(\d+)/);
            if (!match) return;
            var value = values[index];
            if (value < 2) return;
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
                text.style.fontSize = value > 20 ? '10px' : '8px';
                text.style.fontWeight = 'bold';
                text.style.fill = textColor;
                text.style.pointerEvents = 'none';
                text.style.paintOrder = 'stroke';
                text.style.stroke = 'white';
                text.style.strokeWidth = '3px';
                text.style.strokeLinejoin = 'round';
                text.textContent = match[1];
                path.parentNode.appendChild(text);
            } catch(e) {}
        });
    }
    function customizeSankey() { repositionNodeLabels(); addLinkLabels(); }
    function waitAndCustomize() {
        var rects = document.querySelectorAll('g > rect');
        var found = false;
        rects.forEach(function(r) {
            var w = parseFloat(r.getAttribute('width'));
            var h = parseFloat(r.getAttribute('height'));
            if (w > 15 && h > 20) found = true;
        });
        if (found) setTimeout(customizeSankey, 300);
        else setTimeout(waitAndCustomize, 200);
    }
    waitAndCustomize();
    setTimeout(function() {
        var plotDiv = document.querySelector('.plotly-graph-div');
        if (plotDiv && plotDiv.on) plotDiv.on('plotly_afterplot', function() { setTimeout(customizeSankey, 150); });
    }, 1000);
})();
</script>
"""

with open(output_file, 'r', encoding='utf-8') as f:
    html = f.read()
html = html.replace('</body>', CUSTOM_JS + '\n</body>')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"NLConnect Sankey saved to {output_file}")
