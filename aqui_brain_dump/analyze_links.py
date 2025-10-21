"""
Analyze internal links in the digital garden.
- Identify orphaned notes (notes with no incoming links)
- Identify broken wikilinks (links to non-existing notes)
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from aqui_brain_dump import content_path
from aqui_brain_dump.note import Note

logger = logging.getLogger(__name__)


def analyze_internal_links(output_file='stats/link_analysis.json', parse_git=False):
    """
    Analyze internal links and identify issues.
    
    Args:
        output_file: Path to save analysis JSON file
        parse_git: Whether to parse git information
    
    Returns:
        dict: Analysis results
    """
    logger.info('Analyzing internal links')
    
    # Parse all notes
    import os
    f_walk = os.walk(content_path)
    for dirs in f_walk:
        if 'templates' in dirs[0]:
            continue
        cur_dir = dirs[0]
        sub_dir = Path(cur_dir).absolute()
        
        if str(sub_dir).startswith('.') or 'templates' in str(sub_dir):
            continue
        
        for file in dirs[2]:
            if not file.endswith('.md'):
                continue
            filepath = Path(cur_dir) / file
            logger.debug(f'Creating note for link analysis: {filepath}')
            Note.create_from_path(filepath, parse_git=parse_git)
    
    # Wait for all parsing to complete
    import time
    while len([f for f in Note.futures_executor if f.running()]):
        time.sleep(.01)
    Note.note_executor.shutdown(wait=True)
    
    # Build backlinks
    Note.build_backlinks()
    
    analysis = {
        'timestamp': datetime.now(tz=timezone.utc).isoformat(),
        'orphaned_notes': [],
        'broken_wikilinks': [],
        'notes_without_outgoing_links': [],
        'summary': {
            'total_notes': 0,
            'orphaned_count': 0,
            'broken_links_count': 0,
            'notes_without_outgoing_count': 0
        }
    }
    
    # Track all existing note URLs
    existing_urls = set()
    for url, note in Note.notes.items():
        if note.content is not None and note.content != '':
            existing_urls.add(url)
    
    # Analyze each note
    for url, note in Note.notes.items():
        # Skip auto-generated notes without content
        if note.content is None or note.content == '':
            continue
        
        analysis['summary']['total_notes'] += 1
        
        # Check for orphaned notes (no backlinks)
        num_backlinks = len(note.backlinks) if hasattr(note, 'backlinks') else 0
        if num_backlinks == 0:
            analysis['orphaned_notes'].append({
                'title': note.title,
                'url': note.url,
                'path': str(note.path),
                'outgoing_links': len(note.links) if hasattr(note, 'links') else 0
            })
        
        # Check for notes without outgoing links
        num_links = len(note.links) if hasattr(note, 'links') else 0
        if num_links == 0:
            analysis['notes_without_outgoing_links'].append({
                'title': note.title,
                'url': note.url,
                'path': str(note.path),
                'backlinks': num_backlinks
            })
        
        # Check for broken wikilinks
        if hasattr(note, 'links'):
            for link in note.links:
                # Normalize the link URL
                link_url = link if link.startswith('/') else f'/{link}'
                
                # Check if the linked note exists
                if link_url not in existing_urls:
                    # Check if it's in notes but has no content (broken link)
                    if link_url in Note.notes:
                        target_note = Note.notes[link_url]
                        if target_note.content is None or target_note.content == '':
                            analysis['broken_wikilinks'].append({
                                'source_title': note.title,
                                'source_url': note.url,
                                'source_path': str(note.path),
                                'target_link': link_url,
                                'target_expected_path': str(target_note.path) if hasattr(target_note, 'path') else 'unknown'
                            })
                    else:
                        # Link doesn't exist at all
                        analysis['broken_wikilinks'].append({
                            'source_title': note.title,
                            'source_url': note.url,
                            'source_path': str(note.path),
                            'target_link': link_url,
                            'target_expected_path': 'Not found in notes'
                        })
    
    # Update summary counts
    analysis['summary']['orphaned_count'] = len(analysis['orphaned_notes'])
    analysis['summary']['broken_links_count'] = len(analysis['broken_wikilinks'])
    analysis['summary']['notes_without_outgoing_count'] = len(analysis['notes_without_outgoing_links'])
    
    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    logger.info(f'Link analysis saved to {output_path}')
    
    # Also save a timestamped version
    timestamp = datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')
    historical_path = output_path.parent / f'link_analysis_{timestamp}.json'
    with open(historical_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    logger.info(f'Historical snapshot saved to {historical_path}')
    
    return analysis


def print_link_analysis_summary(analysis):
    """Print a human-readable summary of link analysis"""
    print('\n' + '='*60)
    print('INTERNAL LINK ANALYSIS')
    print('='*60)
    print(f'\nGenerated: {analysis["timestamp"]}')
    print(f'\n📊 SUMMARY')
    print(f'  Total notes analyzed: {analysis["summary"]["total_notes"]}')
    print(f'  Orphaned notes: {analysis["summary"]["orphaned_count"]}')
    print(f'  Broken wikilinks: {analysis["summary"]["broken_links_count"]}')
    print(f'  Notes without outgoing links: {analysis["summary"]["notes_without_outgoing_count"]}')
    
    # Orphaned notes
    if analysis['orphaned_notes']:
        print(f'\n🏝️  ORPHANED NOTES (No incoming links)')
        print(f'  Found {len(analysis["orphaned_notes"])} orphaned notes:')
        for i, note in enumerate(analysis['orphaned_notes'][:20], 1):  # Show first 20
            print(f'    {i}. "{note["title"]}" ({note["url"]})')
            print(f'       Path: {note["path"]}')
            print(f'       Outgoing links: {note["outgoing_links"]}')
        if len(analysis['orphaned_notes']) > 20:
            print(f'    ... and {len(analysis["orphaned_notes"]) - 20} more')
    
    # Broken wikilinks
    if analysis['broken_wikilinks']:
        print(f'\n🔗💔 BROKEN WIKILINKS (Links to non-existing notes)')
        print(f'  Found {len(analysis["broken_wikilinks"])} broken links:')
        for i, link in enumerate(analysis['broken_wikilinks'][:20], 1):  # Show first 20
            print(f'    {i}. In "{link["source_title"]}"')
            print(f'       Source: {link["source_path"]}')
            print(f'       Broken link: {link["target_link"]}')
            print(f'       Expected path: {link["target_expected_path"]}')
        if len(analysis['broken_wikilinks']) > 20:
            print(f'    ... and {len(analysis["broken_wikilinks"]) - 20} more')
    
    # Notes without outgoing links
    if analysis['notes_without_outgoing_links']:
        print(f'\n📝 NOTES WITHOUT OUTGOING LINKS')
        print(f'  Found {len(analysis["notes_without_outgoing_links"])} notes without outgoing links')
        print(f'  (First 10 shown)')
        for i, note in enumerate(analysis['notes_without_outgoing_links'][:10], 1):
            print(f'    {i}. "{note["title"]}" ({note["backlinks"]} backlinks)')
    
    print('\n' + '='*60 + '\n')


if __name__ == '__main__':
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    analysis = analyze_internal_links(parse_git=False)
    print_link_analysis_summary(analysis)

