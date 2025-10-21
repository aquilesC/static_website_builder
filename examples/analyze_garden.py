#!/usr/bin/env python3
"""
Example script showing how to use the garden tools programmatically.

This demonstrates how to:
1. Generate statistics
2. Analyze links
3. Create custom reports
4. Compare historical data
"""

import json
from pathlib import Path
from datetime import datetime

from aqui_brain_dump.stats import generate_statistics, print_statistics_summary
from aqui_brain_dump.analyze_links import analyze_internal_links, print_link_analysis_summary
from aqui_brain_dump.check_external_links import check_external_links, print_external_links_summary


def main():
    """Run a complete garden analysis"""
    
    print("=" * 60)
    print("DIGITAL GARDEN ANALYSIS")
    print("=" * 60)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Generate statistics
    print("\n1. Generating statistics...")
    stats = generate_statistics(parse_git=False)
    print_statistics_summary(stats)
    
    # 2. Analyze links
    print("\n2. Analyzing internal links...")
    link_analysis = analyze_internal_links(parse_git=False)
    print_link_analysis_summary(link_analysis)
    
    # 3. Create a custom summary report
    print("\n3. Creating custom summary report...")
    create_summary_report(stats, link_analysis)
    
    # 4. Check external links (optional - can be slow)
    # Uncomment if you want to check external links
    # print("\n4. Checking external links...")
    # external_results = check_external_links(parse_git=False, delay=0.5)
    # print_external_links_summary(external_results)
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def create_summary_report(stats, link_analysis):
    """Create a custom summary report combining stats and link analysis"""
    
    report = {
        'date': datetime.now().isoformat(),
        'summary': {
            'total_notes': stats['total_notes'],
            'total_words': stats['total_words'],
            'avg_words': stats['avg_words_per_note'],
            'total_tags': stats['total_tags'],
            'health_score': calculate_health_score(stats, link_analysis)
        },
        'top_notes': {
            'longest': stats['longest_note']['title'],
            'most_connected': stats['most_connected_note']['title'],
            'most_linked': stats['most_linked_note']['title']
        },
        'issues': {
            'orphaned_notes': len(link_analysis['orphaned_notes']),
            'broken_links': len(link_analysis['broken_wikilinks']),
            'notes_without_links': len(link_analysis['notes_without_outgoing_links'])
        },
        'top_tags': get_top_tags(stats, n=10)
    }
    
    # Save the summary report
    output_path = Path('stats/summary_report.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*60}")
    print("CUSTOM SUMMARY REPORT")
    print(f"{'='*60}")
    print(f"\n📊 Overview:")
    print(f"  Total Notes: {report['summary']['total_notes']}")
    print(f"  Total Words: {report['summary']['total_words']:,}")
    print(f"  Average Words: {report['summary']['avg_words']}")
    print(f"  Total Tags: {report['summary']['total_tags']}")
    print(f"  Garden Health Score: {report['summary']['health_score']}/100")
    
    print(f"\n🏆 Top Notes:")
    print(f"  Longest: {report['top_notes']['longest']}")
    print(f"  Most Connected: {report['top_notes']['most_connected']}")
    print(f"  Most Linked: {report['top_notes']['most_linked']}")
    
    print(f"\n⚠️  Issues:")
    print(f"  Orphaned Notes: {report['issues']['orphaned_notes']}")
    print(f"  Broken Links: {report['issues']['broken_links']}")
    print(f"  Notes Without Links: {report['issues']['notes_without_links']}")
    
    print(f"\n🏷️  Top 10 Tags:")
    for tag, count in report['top_tags']:
        print(f"  #{tag}: {count} notes")
    
    print(f"\n💾 Report saved to: {output_path}")
    print(f"{'='*60}\n")


def calculate_health_score(stats, link_analysis):
    """
    Calculate a health score for the garden (0-100).
    
    Higher scores indicate:
    - Good interconnectedness
    - Few orphaned notes
    - Few broken links
    - Substantial content
    """
    if stats['notes_with_content'] == 0:
        return 0
    
    score = 100
    
    # Penalize orphaned notes (max -30 points)
    orphan_ratio = len(link_analysis['orphaned_notes']) / stats['notes_with_content']
    score -= min(30, orphan_ratio * 100)
    
    # Penalize broken links (max -30 points)
    broken_link_ratio = len(link_analysis['broken_wikilinks']) / max(stats['total_links'], 1)
    score -= min(30, broken_link_ratio * 100)
    
    # Penalize notes without links (max -20 points)
    no_links_ratio = len(link_analysis['notes_without_outgoing_links']) / stats['notes_with_content']
    score -= min(20, no_links_ratio * 50)
    
    # Reward good average connectivity (bonus up to +20 points)
    if stats['avg_links_per_note'] > 3:
        score += min(20, (stats['avg_links_per_note'] - 3) * 5)
    
    # Ensure score is between 0 and 100
    return max(0, min(100, round(score)))


def get_top_tags(stats, n=10):
    """Get top N tags by count"""
    sorted_tags = sorted(
        stats['tag_distribution'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    return sorted_tags[:n]


def compare_historical_stats():
    """
    Example function to compare current stats with historical data.
    This shows how you can track growth over time.
    """
    stats_dir = Path('stats')
    
    # Get all historical stats files
    historical_files = sorted(stats_dir.glob('garden_stats_*.json'))
    
    if len(historical_files) < 2:
        print("Not enough historical data to compare")
        return
    
    # Compare first and last
    with open(historical_files[0]) as f:
        old_stats = json.load(f)
    
    with open(historical_files[-1]) as f:
        new_stats = json.load(f)
    
    print(f"\n{'='*60}")
    print("GROWTH COMPARISON")
    print(f"{'='*60}")
    print(f"\nFrom: {old_stats['timestamp']}")
    print(f"To:   {new_stats['timestamp']}")
    
    # Calculate changes
    notes_change = new_stats['total_notes'] - old_stats['total_notes']
    words_change = new_stats['total_words'] - old_stats['total_words']
    
    print(f"\n📈 Changes:")
    print(f"  Notes: {old_stats['total_notes']} → {new_stats['total_notes']} ({notes_change:+d})")
    print(f"  Words: {old_stats['total_words']:,} → {new_stats['total_words']:,} ({words_change:+,})")
    print(f"  Tags:  {old_stats['total_tags']} → {new_stats['total_tags']} ({new_stats['total_tags'] - old_stats['total_tags']:+d})")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
    
    # Optionally compare historical data
    # compare_historical_stats()

