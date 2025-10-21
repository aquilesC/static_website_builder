"""
Check external HTTP/HTTPS links in the digital garden.
Attempts to fetch each external link and reports any errors.
"""
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import time

from aqui_brain_dump import content_path
from aqui_brain_dump.note import Note

logger = logging.getLogger(__name__)


def extract_external_links(content):
    """
    Extract external HTTP/HTTPS links from HTML content.
    
    Args:
        content: HTML content string
    
    Returns:
        set: Set of external URLs
    """
    if not content:
        return set()
    
    # Pattern to match href="http..." or href='http...'
    pattern = r'href=["\']?(https?://[^"\'>\s]+)["\']?'
    matches = re.findall(pattern, content, re.IGNORECASE)
    
    # Also check for markdown-style links that might remain
    md_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    md_matches = re.findall(md_pattern, content, re.IGNORECASE)
    md_urls = [url for _, url in md_matches]
    
    return set(matches + md_urls)


def check_url(url, timeout=10):
    """
    Check if a URL is accessible.
    
    Args:
        url: URL to check
        timeout: Request timeout in seconds
    
    Returns:
        dict: Result with status code, error, etc.
    """
    try:
        import requests
        response = requests.head(url, timeout=timeout, allow_redirects=True, 
                                headers={'User-Agent': 'Mozilla/5.0 (Digital Garden Link Checker)'})
        
        # If HEAD request fails, try GET
        if response.status_code >= 400:
            response = requests.get(url, timeout=timeout, allow_redirects=True,
                                  headers={'User-Agent': 'Mozilla/5.0 (Digital Garden Link Checker)'})
        
        return {
            'status': 'ok' if response.status_code == 200 else 'warning',
            'status_code': response.status_code,
            'final_url': response.url,
            'error': None
        }
    except requests.exceptions.Timeout:
        return {
            'status': 'error',
            'status_code': None,
            'final_url': None,
            'error': 'Timeout'
        }
    except requests.exceptions.ConnectionError:
        return {
            'status': 'error',
            'status_code': None,
            'final_url': None,
            'error': 'Connection Error'
        }
    except requests.exceptions.TooManyRedirects:
        return {
            'status': 'error',
            'status_code': None,
            'final_url': None,
            'error': 'Too Many Redirects'
        }
    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'status_code': None,
            'final_url': None,
            'error': str(e)
        }
    except Exception as e:
        return {
            'status': 'error',
            'status_code': None,
            'final_url': None,
            'error': f'Unexpected error: {str(e)}'
        }


def check_external_links(output_file='stats/external_links.json', parse_git=False, 
                        delay=0.5, timeout=10):
    """
    Check all external links in the digital garden.
    
    Args:
        output_file: Path to save results JSON file
        parse_git: Whether to parse git information
        delay: Delay between requests in seconds (to be polite)
        timeout: Request timeout in seconds
    
    Returns:
        dict: Check results
    """
    logger.info('Checking external links')
    
    # Check if requests library is available
    try:
        import requests
    except ImportError:
        logger.error('requests library not found. Install it with: pip install requests')
        return {
            'error': 'requests library not installed',
            'message': 'Please install requests: pip install requests'
        }
    
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
            logger.debug(f'Creating note for external link check: {filepath}')
            Note.create_from_path(filepath, parse_git=parse_git)
    
    # Wait for all parsing to complete
    while len([f for f in Note.futures_executor if f.running()]):
        time.sleep(.01)
    Note.note_executor.shutdown(wait=True)
    
    results = {
        'timestamp': datetime.now(tz=timezone.utc).isoformat(),
        'links_checked': [],
        'summary': {
            'total_notes': 0,
            'total_external_links': 0,
            'unique_external_links': 0,
            'ok_links': 0,
            'warning_links': 0,
            'error_links': 0
        }
    }
    
    # Collect all external links
    all_external_links = {}  # url -> list of notes that reference it
    
    for url, note in Note.notes.items():
        # Skip auto-generated notes without content
        if note.content is None or note.content == '':
            continue
        
        results['summary']['total_notes'] += 1
        
        # Extract external links from content
        external_links = extract_external_links(note.content)
        
        for link in external_links:
            if link not in all_external_links:
                all_external_links[link] = []
            all_external_links[link].append({
                'title': note.title,
                'url': note.url,
                'path': str(note.path)
            })
    
    results['summary']['unique_external_links'] = len(all_external_links)
    results['summary']['total_external_links'] = sum(len(notes) for notes in all_external_links.values())
    
    logger.info(f'Found {results["summary"]["unique_external_links"]} unique external links')
    logger.info(f'Checking links (this may take a while)...')
    
    # Check each unique link
    for i, (link, source_notes) in enumerate(all_external_links.items(), 1):
        logger.info(f'Checking link {i}/{len(all_external_links)}: {link}')
        
        check_result = check_url(link, timeout=timeout)
        
        link_result = {
            'url': link,
            'status': check_result['status'],
            'status_code': check_result['status_code'],
            'final_url': check_result['final_url'],
            'error': check_result['error'],
            'found_in_notes': source_notes
        }
        
        results['links_checked'].append(link_result)
        
        # Update summary
        if check_result['status'] == 'ok':
            results['summary']['ok_links'] += 1
        elif check_result['status'] == 'warning':
            results['summary']['warning_links'] += 1
        else:
            results['summary']['error_links'] += 1
        
        # Be polite and wait between requests
        if delay > 0 and i < len(all_external_links):
            time.sleep(delay)
    
    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f'External link check results saved to {output_path}')
    
    # Also save a timestamped version
    timestamp = datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')
    historical_path = output_path.parent / f'external_links_{timestamp}.json'
    with open(historical_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f'Historical snapshot saved to {historical_path}')
    
    return results


def print_external_links_summary(results):
    """Print a human-readable summary of external link check"""
    if 'error' in results:
        print(f'\n❌ ERROR: {results["message"]}')
        return
    
    print('\n' + '='*60)
    print('EXTERNAL LINK CHECK')
    print('='*60)
    print(f'\nGenerated: {results["timestamp"]}')
    print(f'\n📊 SUMMARY')
    print(f'  Total notes: {results["summary"]["total_notes"]}')
    print(f'  Total external links: {results["summary"]["total_external_links"]}')
    print(f'  Unique external links: {results["summary"]["unique_external_links"]}')
    print(f'  ✅ OK (200): {results["summary"]["ok_links"]}')
    print(f'  ⚠️  Warning (non-200): {results["summary"]["warning_links"]}')
    print(f'  ❌ Error: {results["summary"]["error_links"]}')
    
    # Show problematic links
    problematic = [link for link in results['links_checked'] 
                   if link['status'] in ['warning', 'error']]
    
    if problematic:
        print(f'\n⚠️  PROBLEMATIC LINKS ({len(problematic)} found)')
        for i, link in enumerate(problematic[:30], 1):  # Show first 30
            status_icon = '⚠️' if link['status'] == 'warning' else '❌'
            print(f'\n  {i}. {status_icon} {link["url"]}')
            if link['status_code']:
                print(f'     Status: {link["status_code"]}')
            if link['error']:
                print(f'     Error: {link["error"]}')
            if link['final_url'] and link['final_url'] != link['url']:
                print(f'     Redirected to: {link["final_url"]}')
            print(f'     Found in {len(link["found_in_notes"])} note(s):')
            for note in link["found_in_notes"][:3]:  # Show first 3 notes
                print(f'       - "{note["title"]}" ({note["url"]})')
            if len(link["found_in_notes"]) > 3:
                print(f'       - ... and {len(link["found_in_notes"]) - 3} more')
        
        if len(problematic) > 30:
            print(f'\n  ... and {len(problematic) - 30} more problematic links')
    else:
        print(f'\n✅ All external links are accessible!')
    
    print('\n' + '='*60 + '\n')


if __name__ == '__main__':
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    results = check_external_links(parse_git=False, delay=0.5)
    print_external_links_summary(results)

