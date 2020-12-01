import json


def parse_bibliography(filename):
    """ Parses a bibliographic record exported into json in the CSL Json format (easy to achieve with Zotero)
    """

    with open(filename, 'r', encoding="utf-8") as f:
        data = json.load(f)
        bibliography = dict()
        for entry in data:
            bibliography[entry['id']] = entry
    return bibliography