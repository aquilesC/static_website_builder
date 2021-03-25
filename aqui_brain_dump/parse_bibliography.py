import json
from pathlib import Path


def parse_bibliography(filename: Path):
    """ Parses a bibliographic record exported into json in the CSL Json format (easy to achieve with Zotero)
    """

    with open(filename.absolute(), 'r', encoding="utf-8") as f:
        data = json.load(f)
        bibliography = dict()
        for entry in data:
            bibliography[entry['id']] = entry
    return bibliography