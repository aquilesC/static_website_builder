"""
Statistics generator for digital garden notes.
Collects metrics about notes and saves them to track evolution over time.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

from aqui_brain_dump import content_path
from aqui_brain_dump.note import Note

logger = logging.getLogger(__name__)


def count_words(content):
    """Count words in HTML content (rough estimate)"""
    if not content:
        return 0
    # Simple word count - strip HTML tags and count
    import re
    text = re.sub(r'<[^>]+>', '', content)
    words = text.split()
    return len(words)


def generate_statistics(output_file='stats/garden_stats.json', parse_git=True):
    """
    Generate comprehensive statistics about the digital garden.
    
    Args:
        output_file: Path to save statistics JSON file
        parse_git: Whether to parse git information for dates
    
    Returns:
        dict: Statistics dictionary
    """
    logger.info('Generating digital garden statistics')
    
    # Parse all notes
    import os
    f_walk = os.walk(content_path)
    for dirs in f_walk:
        if 'templates' in dirs[0]:
            continue
        logger.debug(f'Processing directory: {dirs[0]}')
        cur_dir = dirs[0]
        sub_dir = Path(cur_dir).absolute()
        
        if str(sub_dir).startswith('.') or 'templates' in str(sub_dir):
            continue
        
        for file in dirs[2]:
            if not file.endswith('.md'):
                continue
            filepath = Path(cur_dir) / file
            logger.debug(f'Creating note for statistics: {filepath}')
            Note.create_from_path(filepath, parse_git=parse_git)
    
    # Wait for all parsing to complete
    import time
    while len([f for f in Note.futures_executor if f.running()]):
        time.sleep(.01)
    Note.note_executor.shutdown(wait=True)
    
    # Build backlinks to get complete network data
    Note.build_backlinks()
    
    # Collect statistics
    stats = {
        'timestamp': datetime.now(tz=timezone.utc).isoformat(),
        'total_notes': 0,
        'notes_with_content': 0,
        'total_words': 0,
        'total_links': 0,
        'total_backlinks': 0,
        'total_tags': len(Note.tags_dict),
        'total_citations': len(Note.lit_notes),
        'longest_note': {'title': None, 'words': 0, 'path': None},
        'shortest_note': {'title': None, 'words': float('inf'), 'path': None},
        'most_connected_note': {'title': None, 'connections': 0, 'path': None},
        'most_linked_note': {'title': None, 'backlinks': 0, 'path': None},
        'orphaned_notes': [],
        'notes_without_links': [],
        'tag_distribution': {},
        'notes_by_date': {},
    }
    
    for url, note in Note.notes.items():
        # Skip auto-generated notes without content
        if note.content is None or note.content == '':
            stats['total_notes'] += 1
            continue
        
        stats['total_notes'] += 1
        stats['notes_with_content'] += 1
        
        # Word count
        word_count = count_words(note.content)
        stats['total_words'] += word_count
        
        # Longest note
        if word_count > stats['longest_note']['words']:
            stats['longest_note'] = {
                'title': note.title,
                'words': word_count,
                'path': str(note.path),
                'url': note.url
            }
        
        # Shortest note (only count notes with content)
        if word_count > 0 and word_count < stats['shortest_note']['words']:
            stats['shortest_note'] = {
                'title': note.title,
                'words': word_count,
                'path': str(note.path),
                'url': note.url
            }
        
        # Link statistics
        num_links = len(note.links) if hasattr(note, 'links') else 0
        num_backlinks = len(note.backlinks) if hasattr(note, 'backlinks') else 0
        stats['total_links'] += num_links
        stats['total_backlinks'] += num_backlinks
        
        total_connections = num_links + num_backlinks
        
        # Most connected note
        if total_connections > stats['most_connected_note']['connections']:
            stats['most_connected_note'] = {
                'title': note.title,
                'connections': total_connections,
                'links': num_links,
                'backlinks': num_backlinks,
                'path': str(note.path),
                'url': note.url
            }
        
        # Most linked note (most backlinks)
        if num_backlinks > stats['most_linked_note']['backlinks']:
            stats['most_linked_note'] = {
                'title': note.title,
                'backlinks': num_backlinks,
                'path': str(note.path),
                'url': note.url
            }
        
        # Orphaned notes (no backlinks)
        if num_backlinks == 0:
            stats['orphaned_notes'].append({
                'title': note.title,
                'path': str(note.path),
                'url': note.url
            })
        
        # Notes without outgoing links
        if num_links == 0:
            stats['notes_without_links'].append({
                'title': note.title,
                'path': str(note.path),
                'url': note.url
            })
        
        # Track notes by creation date
        if hasattr(note, 'creation_date') and note.creation_date:
            date_str = str(note.creation_date)[:10]  # YYYY-MM-DD
            if date_str not in stats['notes_by_date']:
                stats['notes_by_date'][date_str] = 0
            stats['notes_by_date'][date_str] += 1
    
    # Tag distribution
    for tag, notes in Note.tags_dict.items():
        stats['tag_distribution'][tag] = len(notes)
    
    # Calculate averages
    if stats['notes_with_content'] > 0:
        stats['avg_words_per_note'] = round(stats['total_words'] / stats['notes_with_content'], 2)
        stats['avg_links_per_note'] = round(stats['total_links'] / stats['notes_with_content'], 2)
        stats['avg_backlinks_per_note'] = round(stats['total_backlinks'] / stats['notes_with_content'], 2)
    else:
        stats['avg_words_per_note'] = 0
        stats['avg_links_per_note'] = 0
        stats['avg_backlinks_per_note'] = 0
    
    # Clean up shortest note if no notes were found
    if stats['shortest_note']['words'] == float('inf'):
        stats['shortest_note']['words'] = 0
    
    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    logger.info(f'Statistics saved to {output_path}')
    
    # Also save a timestamped version for historical tracking
    timestamp = datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')
    historical_path = output_path.parent / f'garden_stats_{timestamp}.json'
    with open(historical_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    logger.info(f'Historical snapshot saved to {historical_path}')
    
    return stats


def print_statistics_summary(stats):
    """Print a human-readable summary of statistics"""
    print('\n' + '='*60)
    print('DIGITAL GARDEN STATISTICS')
    print('='*60)
    print(f'\nGenerated: {stats["timestamp"]}')
    print(f'\n📊 OVERVIEW')
    print(f'  Total notes: {stats["total_notes"]}')
    print(f'  Notes with content: {stats["notes_with_content"]}')
    print(f'  Total words: {stats["total_words"]:,}')
    print(f'  Average words per note: {stats["avg_words_per_note"]}')
    
    print(f'\n🔗 CONNECTIONS')
    print(f'  Total links: {stats["total_links"]}')
    print(f'  Total backlinks: {stats["total_backlinks"]}')
    print(f'  Average links per note: {stats["avg_links_per_note"]}')
    print(f'  Average backlinks per note: {stats["avg_backlinks_per_note"]}')
    
    print(f'\n🏆 RECORDS')
    if stats['longest_note']['title']:
        print(f'  Longest note: "{stats["longest_note"]["title"]}" ({stats["longest_note"]["words"]:,} words)')
    if stats['shortest_note']['title']:
        print(f'  Shortest note: "{stats["shortest_note"]["title"]}" ({stats["shortest_note"]["words"]} words)')
    if stats['most_connected_note']['title']:
        print(f'  Most connected: "{stats["most_connected_note"]["title"]}" ({stats["most_connected_note"]["connections"]} connections)')
    if stats['most_linked_note']['title']:
        print(f'  Most linked: "{stats["most_linked_note"]["title"]}" ({stats["most_linked_note"]["backlinks"]} backlinks)')
    
    print(f'\n🏷️  TAGS & CITATIONS')
    print(f'  Total tags: {stats["total_tags"]}')
    print(f'  Total citations: {stats["total_citations"]}')
    
    print(f'\n⚠️  POTENTIAL ISSUES')
    print(f'  Orphaned notes (no backlinks): {len(stats["orphaned_notes"])}')
    print(f'  Notes without outgoing links: {len(stats["notes_without_links"])}')
    
    # Top 10 tags
    if stats['tag_distribution']:
        print(f'\n🔝 TOP 10 TAGS')
        sorted_tags = sorted(stats['tag_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]
        for tag, count in sorted_tags:
            print(f'  #{tag}: {count} notes')
    
    print('\n' + '='*60 + '\n')


if __name__ == '__main__':
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    stats = generate_statistics(parse_git=False)
    print_statistics_summary(stats)

