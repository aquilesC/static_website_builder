# Garden Tools - Quick Start Guide

## Installation

```bash
# From the static_website_builder directory
pip install -e .
```

This will install the `garden_tools` command.

## Quick Commands

### 1. Get Statistics About Your Garden

```bash
garden_tools stats
```

**What it does:**
- Counts total notes and words
- Finds longest and shortest notes
- Identifies most connected notes
- Shows tag distribution
- Lists orphaned notes

**Output:** `stats/garden_stats.json` + timestamped copy

---

### 2. Find Link Problems

```bash
garden_tools links
```

**What it does:**
- Finds orphaned notes (no incoming links)
- Identifies broken wikilinks (links to non-existing notes)
- Lists notes without outgoing links

**Output:** `stats/link_analysis.json` + timestamped copy

---

### 3. Check External Links

```bash
garden_tools external
```

**What it does:**
- Extracts all HTTP/HTTPS links from your notes
- Checks each link (fetches URL)
- Reports broken or problematic links

**Output:** `stats/external_links.json` + timestamped copy

**Note:** This can take a while depending on how many external links you have.

---

### 4. Run Everything

```bash
garden_tools all
```

Runs all three analyses in sequence.

---

## Common Use Cases

### Weekly Health Check

```bash
# Quick check for issues
garden_tools links
```

Look for:
- Orphaned notes that should be linked
- Broken wikilinks that need fixing

### Monthly Deep Dive

```bash
# Full analysis with git info
garden_tools all --git
```

This gives you accurate dates from git history (slower but more precise).

### Before Publishing

```bash
# Check external links before deploying
garden_tools external
```

Fix any broken external links before your site goes live.

### Track Growth Over Time

```bash
# Run regularly and compare historical files
garden_tools stats

# Later, compare files
ls -la stats/garden_stats_*.json
```

Each run creates a timestamped file, so you can track your garden's evolution.

---

## Interpreting Results

### Statistics

Key metrics to watch:
- **Total notes**: Is your garden growing?
- **Average words per note**: Are notes substantial?
- **Orphaned notes**: Notes that might need linking
- **Most connected notes**: Your "hub" notes

### Link Analysis

**Orphaned Notes** - Consider:
- Should this note be linked from somewhere?
- Is this note still relevant?
- Could it be merged with another note?

**Broken Wikilinks** - Action needed:
- Create the missing note, or
- Fix the link to point to the right note, or
- Remove the link if no longer relevant

### External Links

**Status 200 (OK)** ✅ - Link works fine

**Status 404 (Not Found)** ❌ - Update or remove the link

**Status 403 (Forbidden)** ⚠️ - Site blocks automated checking (might work in browser)

**Timeout/Connection Error** ❌ - Site down or slow

---

## Tips

### Faster External Link Checking

```bash
# Reduce delay between requests (be respectful!)
garden_tools external -d 0.2

# Reduce timeout for faster failure detection
garden_tools external -t 5
```

### Custom Output Location

```bash
# Save to specific location
garden_tools stats -o my_reports/stats_today.json
```

### Verbose Mode for Debugging

```bash
# See detailed logs
garden_tools stats -v
```

---

## File Locations

All results are saved in the `stats/` directory:

**Latest Results** (overwritten each run):
- `stats/garden_stats.json`
- `stats/link_analysis.json`
- `stats/external_links.json`

**Historical Archive** (timestamped, never overwritten):
- `stats/garden_stats_YYYYMMDD_HHMMSS.json`
- `stats/link_analysis_YYYYMMDD_HHMMSS.json`
- `stats/external_links_YYYYMMDD_HHMMSS.json`

**Logs**:
- `stats/garden_tools.log`

---

## Troubleshooting

### "Command not found: garden_tools"

```bash
# Reinstall the package
pip install -e .
```

### "ModuleNotFoundError: No module named 'requests'"

```bash
# Install requests
pip install requests
```

### Stats look wrong

Try with git information for accurate dates:

```bash
garden_tools stats --git
```

---

## Need More Info?

See the full documentation in `GARDEN_TOOLS_README.md`

Or get help:

```bash
garden_tools --help
garden_tools stats --help
garden_tools links --help
garden_tools external --help
```

