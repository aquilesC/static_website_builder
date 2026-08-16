import logging
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)


def get_all_git_info(repo_path):
    """Get creation date, last modification date, and commit counts for all files in repo_path in a single git command.

    :param repo_path: Path to the repository root
    :return: dict mapping absolute Path objects to dict with keys 'creation_date', 'last_mod', 'number_edits'
    """
    repo_path = Path(repo_path).absolute()
    logger.info(f'Fetching batched git information for {repo_path}')
    command = ['git', '-c', 'core.quotePath=false', 'log', '--name-status', '--format=COMMIT|%ci']
    try:
        result = subprocess.run(
            command,
            cwd=str(repo_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
    except Exception as e:
        logger.error(f'Error executing git log: {e}')
        return {}

    git_info = {}
    current_date = None

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('COMMIT|'):
            date_str = line[7:].strip()
            try:
                current_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %z')
            except Exception:
                current_date = None
            continue

        if current_date is None:
            continue

        parts = line.split('\t')
        if len(parts) < 2:
            continue

        rel_file_str = parts[-1].strip().strip('"\'')
        if not rel_file_str:
            continue

        file_abs = (repo_path / rel_file_str).absolute()

        if file_abs not in git_info:
            git_info[file_abs] = {
                'last_mod': current_date,
                'creation_date': current_date,
                'number_edits': 1,
            }
        else:
            git_info[file_abs]['creation_date'] = current_date
            git_info[file_abs]['number_edits'] += 1

    return git_info


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