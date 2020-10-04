import subprocess


def get_creation_date(content_dir):
    result = subprocess.run(['git', 'log', '--format="%ci"', '--name-only', '--diff-filter=A', content_dir],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    result = result.stdout.decode('utf-8').split('\n')
    creation_dates = {}
    date = 0
    for line in result:
        if line.startswith('"'):
            date = line.strip('"')
        else:
            if line.endswith('.md'):
                if line.startswith('/'):
                    line = line[1:]
                page_url = line.strip(content_dir).strip('.md').lower()
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
        if line.startswith('"'):
            date = line.strip('"')
        else:
            if line.endswith('.md'):
                if line.startswith('/'):
                    line = line[1:]
                page_url = line.strip(content_dir).strip('.md').lower()
                page_url = page_url.replace(' ', '_')

                modification_dates[page_url] = date

    return modification_dates
