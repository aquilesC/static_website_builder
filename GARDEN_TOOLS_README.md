# Digital Garden Tools

A comprehensive toolkit for analyzing and maintaining your digital garden built with `aqui_brain_dump`.

## Overview

The Garden Tools provide several utilities to help you understand and improve your digital garden:

1. **Statistics** - Track metrics about your notes over time
2. **Link Analysis** - Identify orphaned notes and broken wikilinks
3. **External Link Checker** - Verify all outbound HTTP/HTTPS links

## Installation

After installing `aqui_brain_dump`, you'll have access to the `garden_tools` command:

```bash
pip install -e .
```

Or if you've already installed the package, just run:

```bash
garden_tools --help
```

## Usage

### Generate Statistics

Get comprehensive statistics about your digital garden:

```bash
garden_tools stats
```

This will generate:
- Total number of notes
- Total word count
- Longest and shortest notes
- Most connected and most linked notes
- Tag distribution
- Orphaned notes count
- And much more!

**Output:** Results are saved to `stats/garden_stats.json` and timestamped versions for historical tracking.

**Statistics Tracked:**
- Number of notes (total and with content)
- Total words and average per note
- Total links and backlinks
- Longest note (by word count)
- Shortest note (by word count)
- Most connected note (most links + backlinks)
- Most linked note (most backlinks)
- Orphaned notes (no incoming links)
- Notes without outgoing links
- Tag distribution
- Notes by creation date

### Analyze Internal Links

Find orphaned notes and broken wikilinks:

```bash
garden_tools links
```

This will identify:
- **Orphaned notes**: Notes that have no backlinks (nothing links to them)
- **Broken wikilinks**: `[[wikilinks]]` that point to non-existing notes
- **Notes without outgoing links**: Notes that don't link to anything

**Output:** Results are saved to `stats/link_analysis.json` and timestamped versions.

### Check External Links

Verify all external HTTP/HTTPS links in your notes:

```bash
garden_tools external
```

This will:
- Extract all external links from your notes
- Attempt to fetch each unique URL
- Report status codes and errors
- Show which notes contain problematic links

**Options:**
- `--delay` / `-d`: Delay between requests in seconds (default: 0.5)
- `--timeout` / `-t`: Request timeout in seconds (default: 10)

**Output:** Results are saved to `stats/external_links.json` and timestamped versions.

**Note:** This requires the `requests` library, which is now included in the dependencies.

### Run All Analyses

Run all three analyses in sequence:

```bash
garden_tools all
```

This is equivalent to running `stats`, `links`, and `external` one after another.

## Command-Line Options

### Global Options

- `--verbose` / `-v`: Enable verbose output for debugging

### Stats Command

```bash
garden_tools stats [OPTIONS]
```

**Options:**
- `--output` / `-o`: Output file path (default: `stats/garden_stats.json`)
- `--git`: Parse git information for accurate dates (slower but more accurate)

### Links Command

```bash
garden_tools links [OPTIONS]
```

**Options:**
- `--output` / `-o`: Output file path (default: `stats/link_analysis.json`)
- `--git`: Parse git information

### External Command

```bash
garden_tools external [OPTIONS]
```

**Options:**
- `--output` / `-o`: Output file path (default: `stats/external_links.json`)
- `--git`: Parse git information
- `--delay` / `-d`: Delay between requests (default: 0.5 seconds)
- `--timeout` / `-t`: Request timeout (default: 10 seconds)

### All Command

```bash
garden_tools all [OPTIONS]
```

**Options:**
- `--git`: Parse git information
- `--delay` / `-d`: Delay between requests for external link checking
- `--timeout` / `-t`: Request timeout for external link checking

## Examples

### Basic Usage

```bash
# Generate statistics
garden_tools stats

# Analyze links
garden_tools links

# Check external links with 1 second delay
garden_tools external -d 1.0

# Run everything
garden_tools all
```

### With Git Information

For more accurate creation and modification dates, use the `--git` flag:

```bash
garden_tools stats --git
```

**Note:** This is slower as it queries git history for each file.

### Custom Output Paths

```bash
# Save to a custom location
garden_tools stats -o my_stats/today.json
```

### Verbose Mode

```bash
# See detailed logging
garden_tools stats -v
```

## Output Files

All results are saved in the `stats/` directory:

### Current Files (overwritten each run)
- `stats/garden_stats.json` - Latest statistics
- `stats/link_analysis.json` - Latest link analysis
- `stats/external_links.json` - Latest external link check

### Historical Files (timestamped, never overwritten)
- `stats/garden_stats_YYYYMMDD_HHMMSS.json`
- `stats/link_analysis_YYYYMMDD_HHMMSS.json`
- `stats/external_links_YYYYMMDD_HHMMSS.json`

This allows you to track the evolution of your garden over time!

## Understanding the Results

### Statistics Output

```
📊 OVERVIEW
  Total notes: 150
  Notes with content: 145
  Total words: 45,230
  Average words per note: 312.0

🔗 CONNECTIONS
  Total links: 523
  Total backlinks: 523
  Average links per note: 3.6

🏆 RECORDS
  Longest note: "Deep Dive into Neural Networks" (2,450 words)
  Shortest note: "Quick Note" (15 words)
  Most connected: "Index" (45 connections)
  Most linked: "Core Concepts" (28 backlinks)

🏷️ TAGS & CITATIONS
  Total tags: 42
  Total citations: 18

⚠️ POTENTIAL ISSUES
  Orphaned notes (no backlinks): 12
  Notes without outgoing links: 8
```

### Link Analysis Output

Shows three categories:
1. **Orphaned Notes**: These are notes that exist but nothing links to them. Consider linking to them from related notes or removing if outdated.
2. **Broken Wikilinks**: These are `[[links]]` in your notes that don't point to existing files. Either create the missing note or fix the link.
3. **Notes Without Outgoing Links**: These notes don't link to anything else. Consider adding relevant links to improve connectivity.

### External Link Check Output

Shows the status of all external links:
- ✅ **OK (200)**: Link is working perfectly
- ⚠️ **Warning (non-200)**: Link returned a status code other than 200 (might be a redirect, access denied, etc.)
- ❌ **Error**: Link failed to load (timeout, connection error, etc.)

## Tips

### Track Evolution Over Time

Since all results are timestamped, you can track how your garden grows:

```bash
# Run weekly statistics
garden_tools stats

# Compare historical files in stats/
ls -la stats/garden_stats_*.json
```

### Workflow Integration

Add to your workflow:

```bash
# Before committing changes, check for issues
garden_tools links
garden_tools external

# Monthly health check
garden_tools all --git > garden_report_$(date +%Y%m).txt
```

### Focus on Problematic Areas

Use the JSON output files to create custom reports:

```python
import json

with open('stats/link_analysis.json') as f:
    data = json.load(f)
    
# Get all orphaned notes
orphaned = data['orphaned_notes']
print(f"Found {len(orphaned)} orphaned notes")
```

## Troubleshooting

### "requests library not found"

Install the requests library:

```bash
pip install requests
```

Or reinstall the package which now includes it:

```bash
pip install -e .
```

### External link checking is slow

Adjust the delay and timeout:

```bash
garden_tools external -d 0.2 -t 5
```

### Git information not working

Make sure you're running from within a git repository and that git is installed.

## Module Usage

You can also import and use these tools in your own scripts:

```python
from aqui_brain_dump.stats import generate_statistics, print_statistics_summary
from aqui_brain_dump.analyze_links import analyze_internal_links
from aqui_brain_dump.check_external_links import check_external_links

# Generate statistics
stats = generate_statistics(parse_git=False)
print_statistics_summary(stats)

# Analyze links
analysis = analyze_internal_links(parse_git=False)

# Check external links
results = check_external_links(delay=0.5, timeout=10)
```

## Contributing

Feel free to extend these tools or create new analyses! The code is modular and easy to extend.

## License

Same as `aqui_brain_dump` - BSD License

