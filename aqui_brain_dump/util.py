from pathlib import Path


def path_to_url(filename: Path, content_dir: Path = None) -> str:
    """ Transforms a file path to an url by following some simple rules such as transforming spaces to _ and setting
    all the characters to lowercase.
    """
    if content_dir is not None:
        rel_name = filename.absolute().relative_to(content_dir.absolute())
    else:
        rel_name = filename
    base = str(rel_name.parent).strip('.')
    file = str(rel_name.stem).lower().replace(' ', '_')
    if file == 'index':
        url = base
    else:
        url = base + '/' + file

    if not url.startswith('/'):
        url = '/' + url
    if not url.endswith('/'):
        url += '/'
    return url

