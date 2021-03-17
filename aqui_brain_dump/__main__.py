import os
from pathlib import Path

from aqui_brain_dump.note import Note


def main(content_dir='content'):
    content_path = Path.cwd() / content_dir
    f_walk = os.walk(content_path)
    for dirs in f_walk:
        cur_dir = dirs[0]
        sub_dir = os.path.abspath(cur_dir)
        if sub_dir == '.':
            sub_dir = ''

        if sub_dir.startswith('.'):
            continue

        for file in dirs[2]:
            if not file.endswith('.md'):
                continue
            filepath = content_path / sub_dir / file
            Note(filepath)

    Note.build_backlinks()

    for rel_path, note in Note.notes.items():
        note.render()
        print(rel_path, note.backlinks)



if __name__ == '__main__':
    main()