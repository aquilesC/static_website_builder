import os
from distutils.dir_util import copy_tree
from pathlib import Path

from aqui_brain_dump import output_path
from aqui_brain_dump.note import Note


def main(content_dir='content', static_dir='static'):
    static_dir = Path.cwd() / static_dir

    out_static_dir = output_path / 'static'
    copy_tree(str(static_dir.absolute()), str(out_static_dir.absolute()))

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



if __name__ == '__main__':
    main()