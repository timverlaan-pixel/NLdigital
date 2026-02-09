#!/usr/bin/env python3
"""
Analyze member inflow and outflow for NLConnect.
"""

import json
import os

data_dir = '/workspaces/NLdigital/nlconnect_data'
member_files = sorted([f for f in os.listdir(data_dir) if f.startswith('members_') and f.endswith('.json')])

print("=" * 60)
print("Analyzing NLConnect member flows")
print("=" * 60)

snapshots = []
for filename in member_files:
    with open(os.path.join(data_dir, filename), 'r') as f:
        data = json.load(f)
        snapshots.append({
            'date': data['date'],
            'members': set(data['members']),
            'count': len(data['members'])
        })

print(f"Loaded {len(snapshots)} snapshots")
for s in snapshots:
    print(f"  {s['date']}: {s['count']} members")

# Analyze flows between consecutive snapshots
flows = []
for i in range(len(snapshots) - 1):
    current = snapshots[i]
    next_snap = snapshots[i + 1]

    stayed = current['members'] & next_snap['members']
    joined = next_snap['members'] - current['members']
    left = current['members'] - next_snap['members']

    print(f"\n{current['date']} -> {next_snap['date']}")
    print(f"  Stayed: {len(stayed)}, Joined: {len(joined)}, Left: {len(left)}")
    print(f"  Net: {len(joined) - len(left):+d}")

    flows.append({
        'from_date': current['date'],
        'to_date': next_snap['date'],
        'stayed': len(stayed),
        'joined': len(joined),
        'left': len(left),
        'stayed_members': sorted(list(stayed)),
        'joined_members': sorted(list(joined)),
        'left_members': sorted(list(left))
    })

# Save
flow_file = os.path.join(data_dir, 'member_flows.json')
with open(flow_file, 'w') as f:
    json.dump(flows, f, indent=2)

print(f"\nFlow analysis saved to {flow_file}")
