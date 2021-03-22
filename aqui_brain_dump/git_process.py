import subprocess
from collections import Counter
from datetime import datetime


def myconverter(o):
    if isinstance(o, datetime):
        return o.__str__()

def get_creation_date(content_dir, base_dir='content'):
    result = subprocess.run(['git', 'log', '--format="%ci"', '--name-only', '--diff-filter=A', content_dir],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    result = result.stdout.decode('utf-8').split('\n')
    creation_dates = {}
    date = 0
    for line in result:
        line = line.strip('"')
        if len(line) and line[0].isdigit():
            date = datetime.strptime(line, '%Y-%m-%d %H:%M:%S %z')
        else:
            if line.endswith('.md'):
                if line.startswith('/'):
                    line = line[1:]
                page_url = line.strip(base_dir).strip('.md').lower()
                page_url = page_url.replace(' ', '_')
                creation_dates[page_url] = date

    return creation_dates


def get_last_modification_date(content_dir):
    result = subprocess.run(['git', 'log', '--format="%ci"', '--name-only', '--diff-filter=M', content_dir],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    result = result.stdout.decode('utf-8').split('\n')
    modification_dates = {}
    date = 0
    for line in result:
        line = line.strip('"')
        if len(line) and line[0].isdigit():
            date = datetime.strptime(line, '%Y-%m-%d %H:%M:%S %z')
        else:
            if line.endswith('.md'):
                if line.startswith('/'):
                    line = line[1:]
                page_url = line.strip(content_dir).strip('.md').lower()
                page_url = page_url.replace(' ', '_')
                if page_url not in modification_dates or date > modification_dates[page_url]:
                    modification_dates[page_url] = date

    return modification_dates


def get_number_commits(content_dir):
    command = [
        'git',
        'log',
        '--name-only',
        '--pretty=format:',
        content_dir,
    ]
    result = subprocess.run(command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    result = [r.strip(content_dir).strip('.md').lower().replace(' ', '_') for r in result.stdout.decode('utf-8').split('\n') if r.endswith('.md')]
    edits = Counter(result)
    return edits