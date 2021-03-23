import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePath

from aqui_brain_dump.util import path_to_url


def get_creation_date(content_dir):
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
            filename = Path(line)
            creation_dates[filename] = date

    return creation_dates


def get_last_modification_date(content_dir):
    result = subprocess.run(['git', 'log', '--format="%ci"', '--name-only', '--diff-filter=M', str(content_dir)],
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
            filename = Path(line)
            if filename not in modification_dates or date > modification_dates[filename]:
                    modification_dates[filename] = date

    return modification_dates


def get_number_commits(content_dir):
    command = [
        'git',
        'log',
        '--name-only',
        '--pretty=format:',
        str(content_dir),
    ]
    result = subprocess.run(command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    result = [Path(r) for r in result.stdout.decode('utf-8').split('\n')]
    edits = Counter(result)
    return edits