import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path


def get_creation_date(filename):
    """ Get the creation date of a filename using git.

    :param filename: path to the file in question. """
    if not filename.is_file():
        print(filename)
        return
    command = ['git', 'log', '--format="%ci"', '--name-only', '--diff-filter=A', str(filename.absolute())]
    result = subprocess.run(command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    result = result.stdout.decode('utf-8').split('\n')
    for line in result:
        line = line.strip('"')
        if len(line) and line[0].isdigit():
            date = datetime.strptime(line, '%Y-%m-%d %H:%M:%S %z')
            return date
    return
    # raise ValueError(f'File {filename} not found on git')


def get_last_modification_date(filename):
    """Get the last modification date of the given file.

    :params filename: Path to the file
    """
    if not filename.is_file():
        print(filename)
        return
    command = ['git', 'log', '--format="%ci"', '--name-only', '--diff-filter=M', str(filename.absolute())]

    result = subprocess.run(command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    result = result.stdout.decode('utf-8').split('\n')
    date = 0
    for line in result:
        line = line.strip('"')
        if len(line) and line[0].isdigit():
            date = datetime.strptime(line, '%Y-%m-%d %H:%M:%S %z')
            return date
    # raise ValueError(f'File {filename} last modification not found on git')


def get_number_commits(filename):
    """ Get the number of edits stored on git for a given file.

    :param filename: Path to the file to check
    """
    if not filename.is_file():
        print(filename)
        return
    command = [
        'git',
        'log',
        '--name-only',
        '--pretty=format:',
        str(filename.absolute()),
    ]
    result = subprocess.run(command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    result = [Path(r).absolute() for r in result.stdout.decode('utf-8').split('\n')]
    edits = Counter(result).get(filename.absolute(), 1)
    return edits