import logging
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)


def get_creation_date(filename):
    """ Get the creation date of a filename using git.

    :param filename: path to the file in question. """
    logger.debug(f'Fetching creation date for {filename}')
    if not filename.is_file():
        logger.warning(f'{filename} is not a file')
        return
    command = ['git', 'log', '--format="%ci"', '--name-only', '--diff-filter=A', str(filename.absolute())]
    result = subprocess.run(command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    result = result.stdout.decode('utf-8').split('\n')
    date = None
    for line in result:
        line = line.strip('"')
        if len(line) and line[0].isdigit():
            try:
                date = datetime.strptime(line, '%Y-%m-%d %H:%M:%S %z')
                logger.debug(f'{filename} creation date: {date}')
            except:
                pass
    return date


def get_last_modification_date(filename):
    """Get the last modification date of the given file.

    :params filename: Path to the file
    """
    logger.debug(f'Fetching modification date of {filename}')
    if not filename.is_file():
        logger.warning(f'{filename} is not a file')
        return
    command = ['git', 'log', '--format="%ci"', '--name-only', '--diff-filter=M', str(filename.absolute())]

    result = subprocess.run(command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    result = result.stdout.decode('utf-8').split('\n')
    for line in result:
        line = line.strip('"')
        if len(line) and line[0].isdigit():
            date = datetime.strptime(line, '%Y-%m-%d %H:%M:%S %z')
            logger.debug(f'{filename} last modified on {date}')
            return date


def get_number_commits(filename):
    """ Get the number of edits stored on git for a given file.

    :param filename: Path to the file to check
    """
    logger.debug(f'Fetching number of commits for {filename}')
    if not filename.is_file():
        logger.warning(f'{filename} is not a file')
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
    logger.debug(f'{filename} got {edits} edits')
    return edits