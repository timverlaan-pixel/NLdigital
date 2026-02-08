# NLdigital Member Flow Analysis

This project analyzes member inflow and outflow for NLdigital from November 2024 to February 2026, with visualizations including Sankey diagrams and detailed company lists.

## 📊 Visualizations

### 1. Member Flow Sankey Diagram
**URL:** [https://timverlaan-pixel.github.io/NLdigital/](https://timverlaan-pixel.github.io/NLdigital/)

Interactive Sankey diagram showing:
- **Member movements** between 10 distinct time snapshots
- **Color-coded flows**: 
  - 🔵 Blue = Members who stayed
  - 🟢 Green = New members who joined  
  - 🔴 Red = Members who left

**Key Metrics:**
- Total Members Joined: **5,205**
- Total Members Left: **5,372**
- Average Retention Rate: **47.6%**

### 2. Companies That Left (Last Period)
**URL:** [companies_left.html](companies_left.html)

Detailed interactive list of all **645 companies** that left between August 4, 2025 and February 6, 2026.

**Features:**
- ✅ Searchable database
- ✅ Grid and List view modes
- ✅ Sortable by name (A-Z)
- ✅ Company rankings with departure order

---

## 📁 Project Structure

```
NLdigital/
├── index.html                          # Main Sankey diagram (GitHub Pages)
├── companies_left.html                 # Interactive list of departing companies
├── fetch_members.py                    # Script to download member data
├── analyze_member_flow.py              # Script to analyze flows
├── create_sankey_diagram.py            # Script to generate Sankey visualization
└── member_data/
    ├── members_YYYY-MM-DD_*.json       # Member snapshots (10 files)
    ├── member_flows.json               # Detailed flow analysis
    ├── sankey_data.json                # Sankey diagram data
    ├── sankey_diagram.html             # Static Sankey HTML
    └── summary.json                    # Summary statistics
```

---

## 📈 Data Overview

### Snapshot Dates
| Date | Members | Change | Source |
|------|---------|--------|--------|
| Nov 7, 2024 | 1,253 | - | Internet Archive |
| Jan 3, 2025 | 1,255 | +2 | Internet Archive |
| Feb 15, 2025 | 1,140 | -115 | Internet Archive |
| Apr 1, 2025 | 1,084 | -56 | Internet Archive |
| Apr 6, 2025 | 1,102 | +18 | Internet Archive |
| May 1, 2025 | 1,097 | -5 | Internet Archive |
| Jun 1, 2025 | 1,107 | +10 | Internet Archive |
| Jul 1, 2025 | 1,101 | -6 | Internet Archive |
| Aug 4, 2025 | 1,122 | +21 | Internet Archive |
| Feb 6, 2026 | 1,086 | -36 | Live member sitemap |

---

## 🔄 Member Flow Analysis

### Transitions Summary
Each transition shows the number of members who stayed, joined, and left:

```
Nov 2024 → Jan 2025: 617 stayed, 638 joined, 636 left
Jan 2025 → Feb 2025: 520 stayed, 620 joined, 735 left
... (7 more transitions)
Aug 2025 → Feb 2026: 477 stayed, 609 joined, 645 left ← Last batch
```

### Key Insights
- **Highest Departure:** Feb 2025 (735 companies left)
- **Highest Growth:** Jan 2025 (638 new members)
- **Most Recent Departures:** 645 companies (visible on [companies_left.html](companies_left.html))
- **Churning Pattern:** Continuous high turnover throughout the period

---

## 🛠️ How to Use

### View Visualizations (No Setup Required)
1. Open the [main Sankey diagram](https://timverlaan-pixel.github.io/NLdigital/) in your browser
2. Explore the [companies that left](companies_left.html) interactive list
3. Search, filter, and sort the data as needed

### Run Scripts Locally
```bash
# Install dependencies
pip install pandas requests beautifulsoup4 plotly lxml openpyxl

# Fetch member data from Internet Archive
python3 fetch_members.py

# Analyze member flows
python3 analyze_member_flow.py

# Generate Sankey diagram
python3 create_sankey_diagram.py
```

---

## 📊 Technologies Used
- **Python 3** - Data processing and analysis
- **Plotly** - Interactive Sankey visualization
- **Pandas** - Data manipulation
- **BeautifulSoup4** - XML/HTML parsing
- **OpenPyXL** - Excel data reading
- **Internet Archive API** - Historical member data

---

## 📝 Data Source
Data comes from:
1. **Internet Archive (Wayback Machine)** - Historical snapshots from Nov 2024 - Aug 2025
2. **Live Data** - Current member sitemap (Feb 2026)

Each snapshot captures the member sitemap from `nldigital.nl/member-sitemap1.xml`

---

## 🎯 Use Cases
This analysis can answer questions like:
- How many companies joined NLdigital during this period?
- What is the member retention rate?
- Which periods had the highest churn?
- Can I see the exact companies that left?

---

## 📄 License
This project analyzes publicly available data from the Internet Archive and NLdigital's public member directory.

---

**Last Updated:** February 8, 2026  
**Data Range:** November 7, 2024 - February 6, 2026
